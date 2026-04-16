# -*- coding: utf-8 -*-

import json
import sys
import argparse
import os

def get_config_setting(name):
    try:
        from fish_ai.config import get_config
        return get_config(name)
    except:
        return None

DEBUG_ENABLED = get_config_setting('debug') == 'True'

def debug_log(msg):
    if DEBUG_ENABLED:
        sys.stderr.write(f"DEBUG: {msg}\n")
        sys.stderr.flush()

def read_path(path):
    try:
        if os.path.isdir(path):
            items = os.listdir(path)
            return f"Directory listing for {path}:\n" + "\n".join(items)
        with open(path, 'r') as f:
            return f.read()
    except Exception as e:
        return str(e)

def web_search(query):
    api_key = get_config_setting('brave_search_api_key')
    if not api_key:
        return "Error: Brave Search API key not configured. Add 'brave_search_api_key' to your fish-ai.ini or use fish_ai_put_api_key."
    
    try:
        import httpx
        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": api_key
        }
        params = {"q": query, "count": 5}
        
        response = httpx.get(url, headers=headers, params=params, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for result in data.get('web', {}).get('results', []):
            title = result.get('title', 'No Title')
            link = result.get('url', 'No Link')
            snippet = result.get('description', 'No description available.')
            results.append(f"Title: {title}\nURL: {link}\nSnippet: {snippet}\n")
        
        return "\n".join(results) if results else "No results found."
    except Exception as e:
        return f"Search error: {str(e)}"

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "shell_execute",
            "description": "Execute a command in the fish shell.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The shell command to execute."}
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_path",
            "description": "Read the content of a file or list the contents of a directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "The path to the file or directory."}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web using Brave Search for up-to-date information, documentation, or troubleshooting help.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query."}
                },
                "required": ["query"]
            }
        }
    }
]

SYSTEM_PROMPT = """
You are an expert coding assistant. You help users with tasks by reading paths, searching the web, and executing shell commands.

Available tools:
- read_path: Read file contents OR list directory contents
- shell_execute: Execute shell commands
- web_search: Search the web for information you don't have locally

Guidelines:
- Use web_search for finding documentation, latest versions, or fixing errors.
- Use read_path to explore the local project.
- Use shell_execute for ALL other system tasks (searching, editing files, etc).
- ALWAYS provide a concise 'Thought' explaining your reasoning before any tool call.
- Be concise. When the goal is met, end with "DONE".
"""

def compress_history(messages):
    from fish_ai.engine import get_chat_response
    if len(messages) <= 10: return messages
    system_msg = messages[0]
    initial_context = messages[1:3] if len(messages) > 3 else []
    recent_msgs = messages[-4:]
    to_summarize = messages[3:-4] if len(messages) > 7 else []
    if not to_summarize: return messages

    sys.stdout.write("STATUS: Compressing history...\n")
    sys.stdout.flush()

    summary_prompt = [
        {'role': 'system', 'content': 'Summarize the following shell actions and findings into a concise list of "Achievements so far".'},
        {'role': 'user', 'content': json.dumps(to_summarize)}
    ]
    try:
        response = get_chat_response(summary_prompt)
        summary_text = response.get('content', 'History compressed.')
        compressed_msg = {'role': 'user', 'content': f"[SYSTEM: History Compressed]\nSummary:\n{summary_text}"}
        ack_msg = {'role': 'assistant', 'content': "Understood. Resuming with previous context."}
        return [system_msg] + initial_context + [compressed_msg, ack_msg] + recent_msgs
    except:
        return messages

def main():
    try:
        from fish_ai.engine import get_chat_response, get_os, get_logger
        
        parser = argparse.ArgumentParser()
        parser.add_argument('--state', required=True)
        parser.add_argument('--action-file', required=True)
        parser.add_argument('--goal')
        parser.add_argument('--external-history')
        parser.add_argument('--cwd')
        parser.add_argument('--last-output')
        parser.add_argument('--last-status', type=int)
        parser.add_argument('--rejected', action='store_true')
        parser.add_argument('--compress', action='store_true')

        args = parser.parse_args()
        
        messages = []
        if os.path.exists(args.state) and os.path.getsize(args.state) > 0:
            with open(args.state, 'r') as f:
                try: messages = json.load(f)
                except: messages = []
        
        if not messages:
            full_prompt = SYSTEM_PROMPT + "\nOperating System: {os}\n".format(os=get_os())
            messages = [{'role': 'system', 'content': full_prompt}]
            context = "Context:\n"
            if args.cwd: context += f"- Current directory: {args.cwd}\n"
            if args.external_history: context += f"- Recent history:\n{args.external_history}\n"
            
            if args.cwd or args.external_history:
                messages.append({'role': 'user', 'content': context})
                messages.append({'role': 'assistant', 'content': "Understood. I am aware of the current directory and recent shell history."})
        
        if args.goal:
            messages.append({'role': 'user', 'content': args.goal})
        elif not messages or len(messages) <= 1:
            messages.append({'role': 'user', 'content': 'Hello, how can I help you today?'})

        if args.rejected:
            messages.append({'role': 'user', 'content': 'I rejected that command. Please try a different way.'})
        elif args.last_output is not None:
            content = args.last_output
            if args.last_status is not None: content = f"Exit status: {args.last_status}\n\nOutput:\n{content}"
            last_id = next((m['tool_calls'][0]['id'] for m in reversed(messages) if m.get('role') == 'assistant' and m.get('tool_calls')), None)
            if last_id: messages.append({'role': 'tool', 'tool_call_id': last_id, 'content': content})
            else: messages.append({'role': 'user', 'content': content})

        if args.compress or len(messages) > 20:
            messages = compress_history(messages)
            with open(args.state, 'w') as f: json.dump(messages, f)

        response = get_chat_response(messages, tools=TOOLS)
        if not response: raise Exception("No response from AI.")

        messages.append(response)
        with open(args.state, 'w') as f: json.dump(messages, f)

        full_content = response.get('content', '')
        remaining_content = full_content
        thought = ""
        
        if '<think>' in full_content:
            import re
            m = re.search(r'<think>(.*?)</think>(.*)', full_content, re.DOTALL)
            if m:
                thought = m.group(1).strip()
                remaining_content = m.group(2).strip()
        elif response.get('tool_calls'):
            thought = full_content.strip()
            remaining_content = ""

        if thought: sys.stdout.write(f"THOUGHT\n{thought}\nEND_THOUGHT\n")

        if response.get('tool_calls'):
            tool_call = response['tool_calls'][0]
            func_name = tool_call['function']['name'].split(':')[-1]
            func_args = json.loads(tool_call['function']['arguments'])

            if func_name == 'shell_execute':
                with open(args.action_file, 'w') as f: f.write(func_args['command'])
                sys.stdout.write("EXECUTE\n")
            else:
                args_str = ", ".join([f"{k}={v}" for k, v in func_args.items()])
                sys.stdout.write(f"TOOL_CALL: {func_name}({args_str})\n")
                
                result = ""
                if func_name == 'read_path': result = read_path(func_args['path'])
                elif func_name == 'web_search': result = web_search(func_args['query'])
                else: result = f"Unknown tool: {func_name}"
                
                sys.stdout.write(f"TOOL_RESULT\n{result}\nEND_RESULT\n")
                messages.append({'role': 'tool', 'tool_call_id': tool_call['id'], 'content': result})
                with open(args.state, 'w') as f: json.dump(messages, f)
                sys.stdout.write("CONTINUE\n")
        else:
            if not remaining_content and thought: remaining_content = thought
            with open(args.action_file, 'w') as f: f.write(remaining_content)
            sys.stdout.write("DONE\n" if "DONE" in full_content.upper() else "CHAT\n")
        
        if 'usage' in response:
            u = response['usage']
            sys.stdout.write(f"USAGE: prompt={u.get('prompt_tokens', 0)} completion={u.get('completion_tokens', 0)} total={u.get('total_tokens', 0)}\n")

        sys.stdout.flush()
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:
        debug_log(str(e))
        with open(args.action_file, 'w') as f: f.write(str(e))
        sys.stdout.write("ERROR\n")
        sys.stdout.flush()
        sys.exit(1)

def render_markdown():
    try:
        from rich.console import Console
        from rich.markdown import Markdown
        Console().print(Markdown(sys.stdin.read() or ""))
    except:
        sys.stdout.write(sys.stdin.read())

if __name__ == "__main__":
    main()
