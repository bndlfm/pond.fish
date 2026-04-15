# -*- coding: utf-8 -*-

import logging
from logging.handlers import SysLogHandler, RotatingFileHandler
from os.path import isfile, exists, expanduser, expandvars
from platform import system, mac_ver
from time import time_ns
import textwrap
from os import access, R_OK, environ
from re import match
from binaryornot.check import is_binary
from subprocess import run, PIPE, DEVNULL, Popen
from itertools import islice
from sys import argv

import json
from fish_ai.redact import redact
from fish_ai.config import get_config

logger = logging.getLogger()

if exists('/dev/log'):
    # Syslog on Linux
    handler = SysLogHandler(address='/dev/log')
    logger.addHandler(handler)
elif exists('/var/run/syslog'):
    # Syslog on macOS
    handler = SysLogHandler(address='/var/run/syslog')
    logger.addHandler(handler)

if get_config('log'):
    handler = RotatingFileHandler(expanduser(get_config('log')),
                                  backupCount=0,
                                  maxBytes=1024*1024)
    logger.addHandler(handler)

if get_config('debug') == 'True':
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.WARNING)


def get_logger():
    return logger


def get_args():
    return list.copy(argv[1:])


def get_os():
    if system() == 'Linux':
        if isfile('/etc/os-release'):
            with open('/etc/os-release') as f:
                for line in f:
                    if line.startswith('PRETTY_NAME='):
                        return line.split('=')[1].strip('"')
        return 'Linux'
    if system() == 'Darwin':
        return 'macOS ' + mac_ver()[0]
    return 'Unknown'


def get_manpage(command):
    try:
        get_logger().debug('Retrieving manpage for command "{}"'
                           .format(command))
        helppage = run(
            ['fish', '-c', command + ' --help'],
            stdout=PIPE,
            stderr=DEVNULL)
        if helppage.returncode == 0:
            output = helppage.stdout.decode('utf-8')
            if len(output) > 2000:
                return output[:2000] + ' [...]'
            else:
                return output
        return 'No manpage available.'
    except Exception as e:
        get_logger().debug(
            'Failed to retrieve manpage for command "{}". Reason: {}'.format(
                command, str(e)))
        return 'No manpage available.'


def get_file_info(words):
    """
    If the user is mentioning a file, return the filename and its file
    contents.
    """
    for word in words.split():
        filename = word.rstrip(',.!').strip('"\'')
        if not match(r'[A-Za-z0-9_\-]+\.[a-z]+', filename.split('/')[-1]):
            continue
        if not isfile(filename):
            continue
        if not access(filename, R_OK):
            continue
        if is_binary(filename):
            continue
        with open(filename, 'r') as file:
            get_logger().debug('Loading file: ' + filename)
            return filename, file.read(3072)
    return None, None


def get_commandline_history(commandline, cursor_position):
    history_size = int(get_config('history_size') or 0)
    if history_size == 0:
        get_logger().debug('Commandline history disabled.')
        return 'No commandline history available.'

    def yield_history():
        command = commandline.split(' ')[0]
        before_cursor = commandline[:cursor_position]
        after_cursor = commandline[cursor_position:]

        proc = Popen(
            ['fish', '-c', 'history search --prefix "{}"'.format(command)],
            stdout=PIPE,
            stderr=DEVNULL)
        while True:
            line = proc.stdout.readline()
            if not line:
                break
            item = line.decode('utf-8').strip()
            if item.startswith(before_cursor) and item.endswith(after_cursor):
                yield item

    history = list(islice(yield_history(), history_size))

    if len(history) == 0:
        return 'No commandline history available.'
    return '\n'.join(history)


def get_system_prompt():
    return {
        'role': 'system',
        'content': textwrap.dedent('''\
        You are a shell scripting assistant working inside a fish shell.
        The operating system is {os}. Your output must to be shell runnable.
        You may consult Stack Overflow and the official Fish shell
        documentation for answers.
        ''').format(os=get_os())
    }


def get_custom_headers():
    """
    Parse custom headers from config.

    The headers config option should be in the format:
    headers = Header-Name: value, Another-Header: value

    This is useful for authentication headers like Cloudflare Access.
    """
    headers_config = get_config('headers')
    if not headers_config:
        return None

    headers = {}
    for header in headers_config.split(','):
        header = header.strip()
        if ':' in header:
            key, value = header.split(':', 1)
            headers[key.strip()] = value.strip()
    return headers if headers else None


def get_openai_client():
    custom_headers = get_custom_headers()

    if (get_config('provider') == 'azure'):
        from openai import AzureOpenAI
        return AzureOpenAI(
            azure_endpoint=get_config('server'),
            api_version='2023-07-01-preview',
            api_key=get_config('api_key'),
            azure_deployment=get_config('azure_deployment'),
            default_headers=custom_headers,
        )
    elif (get_config('provider') == 'self-hosted'):
        from openai import OpenAI
        return OpenAI(
            base_url=get_config('server'),
            api_key=get_config('api_key') or 'dummy',
            default_headers=custom_headers,
        )
    elif (get_config('provider') == 'openai'):
        from openai import OpenAI
        return OpenAI(
            api_key=get_config('api_key'),
            organization=get_config('organization'),
            default_headers=custom_headers,
        )
    elif (get_config('provider') == 'deepseek'):
        # DeepSeek is compatible with OpenAI Python SDK
        from openai import OpenAI
        return OpenAI(
            api_key=get_config('api_key'),
            base_url='https://api.deepseek.com',
            default_headers=custom_headers,
        )
    elif (get_config('provider') == 'bedrock'):
        from openai import OpenAI
        aws_region = get_config('aws_region') or 'us-east-1'
        api_key = get_config('api_key')
        if not api_key:
            from aws_bedrock_token_generator import provide_token
            api_key = provide_token(region=aws_region)
        return OpenAI(
            base_url='https://bedrock-mantle.{}.api.aws/v1'.format(aws_region),
            api_key=api_key,
            default_headers=custom_headers,
        )
    elif (get_config('provider') == 'groq'):
        from groq import Groq
        return Groq(
            api_key=get_config('api_key'),
            default_headers=custom_headers,
        )
    elif (get_config('provider') == 'cohere'):
        # https://docs.cohere.com/docs/compatibility-api
        from openai import OpenAI
        return OpenAI(
            api_key=get_config('api_key'),
            base_url='https://api.cohere.ai/compatibility/v1',
            default_headers=custom_headers,
        )
    else:
        raise Exception('Unknown provider "{}".'
                        .format(get_config('provider')))


def get_messages_for_anthropic(messages):
    user_messages = []
    system_messages = []
    for message in messages:
        role = message.get('role')
        content = message.get('content')
        if role == 'system':
            system_messages.append(content)
        elif role == 'tool':
            user_messages.append({
                'role': 'user',
                'content': [
                    {
                        'type': 'tool_result',
                        'tool_use_id': message.get('tool_call_id'),
                        'content': content
                    }
                ]
            })
        elif role == 'assistant' and message.get('tool_calls'):
            anthropic_content = []
            if content:
                anthropic_content.append({'type': 'text', 'text': content})
            for tc in message.get('tool_calls'):
                anthropic_content.append({
                    'type': 'tool_use',
                    'id': tc['id'],
                    'name': tc['function']['name'],
                    'input': json.loads(tc['function']['arguments'])
                })
            user_messages.append({
                'role': 'assistant',
                'content': anthropic_content
            })
        else:
            user_messages.append(message)
    return system_messages, user_messages


def get_messages_for_gemini(messages):
    outputs = []
    for message in messages:
        role = message.get('role')
        content = message.get('content')
        if role == 'system':
            continue
        elif role == 'user':
            outputs.append({'role': 'user', 'parts': [{'text': content}]})
        elif role == 'assistant':
            parts = []
            content_to_parse = content
            if content_to_parse.startswith('<think>'):
                import re
                m = re.search(r'<think>(.*?)</think>(.*)', content_to_parse, re.DOTALL)
                if m:
                    parts.append({'thought': m.group(1).strip()})
                    content_to_parse = m.group(2).strip()
            
            if content_to_parse:
                parts.append({'text': content_to_parse})
            
            if message.get('tool_calls'):
                for tc in message.get('tool_calls'):
                    f_call = {
                        'name': tc['function']['name'],
                        'args': json.loads(tc['function']['arguments'])
                    }
                    part = {'functionCall': f_call}
                    # Gemini 3 MANDATES a thoughtSignature. 
                    part['thoughtSignature'] = tc['function'].get('thought_signature') or "skip_thought_signature_validator"
                    parts.append(part)
            outputs.append({'role': 'model', 'parts': parts})
        elif role == 'tool':
            # Gemini requires the tool response to match the name of the function called
            func_name = 'unknown'
            if message.get('tool_call_id'):
                if message['tool_call_id'].startswith('google-'):
                    func_name = message['tool_call_id'].replace('google-', '', 1)
            
            # If we still don't know the name, look back in history for the last tool call
            if func_name == 'unknown':
                for msg in reversed(outputs):
                    if msg['role'] == 'model':
                        for part in msg['parts']:
                            if 'functionCall' in part:
                                func_name = part['functionCall']['name']
                                break
                        if func_name != 'unknown':
                            break
            
            outputs.append({
                'role': 'user',
                'parts': [{
                    'functionResponse': {
                        'name': func_name,
                        'response': {'result': content}
                    }
                }]
            })
    return outputs


def create_system_prompt(messages):
    return '\n\n'.join(
        list(
            map(lambda message: message.get('content'),
                list(
                    filter(
                        lambda message: message.get('role') == 'system',
                        messages)))))


def get_response(messages):
    return get_chat_response(messages).get('content')


def get_chat_response(messages, tools=None):
    if get_config('redact') != 'False':
        messages = redact(messages)

    start_time = time_ns()

    custom_headers = get_custom_headers()
    response_message = {'role': 'assistant', 'content': ''}

    if get_config('provider') == 'mistral':
        from mistralai import Mistral

        mistral_kwargs = {
            'api_key': get_config('api_key'),
            'server_url': get_config('server') or 'https://api.mistral.ai',
        }
        if custom_headers:
            from httpx import Client
            mistral_kwargs['http_client'] = Client(headers=custom_headers)
        client = Mistral(**mistral_kwargs)
        params = {
            'model': get_config('model') or 'mistral-large-latest',
            'messages': messages,
        }
        if tools:
            params['tools'] = tools
        completions = client.chat.complete(**params)
        msg = completions.choices[0].message
        response_message['content'] = msg.content
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            response_message['tool_calls'] = []
            for tc in msg.tool_calls:
                response_message['tool_calls'].append({
                    'id': tc.id,
                    'type': 'function',
                    'function': {
                        'name': tc.function.name,
                        'arguments': tc.function.arguments
                    }
                })
    elif get_config('provider') == 'anthropic':
        from anthropic import Anthropic

        client = Anthropic(
            api_key=get_config('api_key'),
            default_headers=custom_headers,
        )
        system_messages, user_messages = get_messages_for_anthropic(messages)
        params = {
            'model': get_config('model') or 'claude-sonnet-4-6',
            'system': '\n'.join(system_messages),
            'messages': user_messages,
            'max_tokens': 4096
        }
        if tools:
            anthropic_tools = []
            for t in tools:
                anthropic_tools.append({
                    'name': t['function']['name'],
                    'description': t['function']['description'],
                    'input_schema': t['function']['parameters']
                })
            params['tools'] = anthropic_tools
        completions = client.messages.create(**params)
        
        for item in completions.content:
            if item.type == 'text':
                response_message['content'] += item.text
            elif item.type == 'tool_use':
                if 'tool_calls' not in response_message:
                    response_message['tool_calls'] = []
                response_message['tool_calls'].append({
                    'id': item.id,
                    'type': 'function',
                    'function': {
                        'name': item.name,
                        'arguments': json.dumps(item.input)
                    }
                })
    elif get_config('provider') == 'google':
        from google import genai
        from google.genai import types
        google_kwargs = {'api_key': get_config('api_key')}
        if custom_headers:
            from google.genai.types import HttpOptions
            google_kwargs['http_options'] = HttpOptions(headers=custom_headers)
        client = genai.Client(**google_kwargs)
        model = get_config('model') or 'gemini-3.1-pro-preview'

        # We must use the internal _api_client to bypass strict Pydantic
        # validation that forbids 'thought_signature' in functionCall.
        generation_config = {}
        model_info = client.models.get(model=model)
        if getattr(model_info, 'thinking', False):
            if 'gemini-2.5' in model:
                generation_config['thinkingConfig'] = {'thinkingBudget': 1024}
            elif 'gemini-3' in model:
                generation_config['thinkingConfig'] = {'includeThoughts': True}
        
        tools_payload = []
        if tools:
            declarations = []
            for t in tools:
                declarations.append({
                    'name': t['function']['name'],
                    'description': t['function']['description'],
                    'parameters': t['function']['parameters']
                })
            tools_payload = [{'function_declarations': declarations}]

        system_instruction = None
        for msg in messages:
            if msg.get('role') == 'system':
                system_instruction = {'parts': [{'text': msg.get('content')}]}
                break

        # Prepare raw request body
        request_body = {
            'contents': get_messages_for_gemini(messages),
        }
        if system_instruction:
            request_body['systemInstruction'] = system_instruction
        if generation_config:
            request_body['generationConfig'] = generation_config
        if tools_payload:
            request_body['tools'] = tools_payload

        # Use the SDK's request method directly to benefit from auth/transport
        # but avoid the strict top-level model validation.
        path = f'models/{model}:generateContent'
        http_response = client._api_client.request('post', path, request_body, None)
        result = http_response.to_json_dict()
        
        # If the response is wrapped (contains headers/body), extract the body
        if 'body' in result and isinstance(result['body'], str):
            result = json.loads(result['body'])
        
        if 'error' in result:
            raise Exception(f"Gemini API error: {result['error'].get('message', 'Unknown error')}")

        # Result is a dictionary mirroring the REST API response
        if 'candidates' not in result:
            raise Exception(f"Gemini API returned no candidates. Response: {result}")

        candidate = result['candidates'][0]
        if 'content' in candidate and 'parts' in candidate['content']:
            for part in candidate['content']['parts']:
                part_text = part.get('text', '')
                if part.get('thought') is True:
                    # This is a thought part with text content
                    if 'thought' not in response_message:
                        response_message['thought'] = True
                    response_message['content'] = f"<think>{part_text}</think>{response_message['content']}"
                elif 'text' in part:
                    response_message['content'] += part_text
                
                if 'functionCall' in part:
                    if 'tool_calls' not in response_message:
                        response_message['tool_calls'] = []
                    fc = part['functionCall']
                    response_message['tool_calls'].append({
                        'id': 'google-' + fc['name'],
                        'type': 'function',
                        'function': {
                            'name': fc['name'],
                            'arguments': json.dumps(fc.get('args', {})),
                            'thought_signature': part.get('thoughtSignature')
                        }
                    })
    else:
        params = {
            'model': get_config('model') or 'gpt-4o',
            'messages': messages,
            'stream': False,
            'n': 1,
        }
        if tools:
            params['tools'] = tools
        if get_config('extra_body'):
            params['extra_body'] = json.loads(get_config('extra_body'))
        completions = get_openai_client().chat.completions.create(**params)
        msg = completions.choices[0].message
        response_message['content'] = msg.content or ''
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            response_message['tool_calls'] = []
            for tc in msg.tool_calls:
                response_message['tool_calls'].append({
                    'id': tc.id,
                    'type': 'function',
                    'function': {
                        'name': tc.function.name,
                        'arguments': tc.function.arguments
                    }
                })

    end_time = time_ns()
    get_logger().debug('Response received from backend: ' + repr(response_message))
    get_logger().debug('Processing time: ' +
                       str(round((end_time - start_time) / 1000000)) + ' ms.')
    
    response_message['content'] = remove_thinking_tokens(response_message['content'])
    return response_message



def remove_thinking_tokens(response):
    """
    Removes thinking tokens which may be present in the beginning of the
    response.

    Example with thinking tokens:

      <think>bar</think>foo -> foo

    :param response: The response from the backend.
    :return: The output without any thinking tokens.
    """
    if not response.strip().startswith('<think>'):
        return response.strip()

    import re
    match = re.search(r'<think>(.*?)</think>(.*)', response, re.DOTALL)
    if match:
        return match.group(2).strip()
    else:
        return response.strip()


def get_install_dir():
    if 'XDG_DATA_HOME' in environ:
        return expandvars('$XDG_DATA_HOME/fish-ai')
    else:
        return expanduser('~/.local/share/fish-ai')
