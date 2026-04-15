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

def list_directory(path):
    try:
        items = os.listdir(path)
        return "\n".join(items)
    except Exception as e:
        return str(e)

def read_file(path):
    try:
        with open(path, 'r') as f:
            return f.read(4096)
    except Exception as e:
        return str(e)

def write_file(path, content):
    try:
        with open(path, 'w') as f:
            f.write(content)
        return "File written successfully."
    except Exception as e:
        return str(e)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "shell_execute",
            "description": "Execute a command in the fish shell. The command will be executed in the user's active shell session.",
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
            "name": "read_file",
            "description": "Read the content of a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "The path to the file."}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List the files in a directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "The path to the directory."}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "The path to the file."},
                    "content": {"type": "string", "description": "The content to write."}
                },
                "required": ["path", "content"]
            }
        }
    }
]

SYSTEM_PROMPT = """
You are an autonomous shell assistant working inside a fish shell.
Your goal is to achieve the user's request by using the provided tools.

MANDATORY AUDIT RULES:
1. ALWAYS provide a concise 'Thought' explaining YOUR CURRENT PLAN before calling any tool.
2. Use `shell_execute` for all shell commands. They will run in the user's ACTIVE session.
3. Use `read_file`, `list_directory`, and `write_file` for direct file system access.
4. When the goal is met, summarize your work and end with "DONE".
"""

def compress_history(messages):
    from fish_ai.engine import get_chat_response
    
    # We only compress if we have a substantial history (e.g., > 10 messages excluding system/initial context)
    if len(messages) <= 10:
        return messages

    # Identify parts to keep: System prompt, initial goal/context, and last 4 messages
    system_msg = messages[0]
    initial_context = messages[1:3] if len(messages) > 3 else []
    recent_msgs = messages[-4:]
    to_summarize = messages[3:-4] if len(messages) > 7 else []

    if not to_summarize:
        return messages

    sys.stdout.write("STATUS: Compressing long conversation history...\n")
    sys.stdout.flush()

    summary_prompt = [
        {'role': 'system', 'content': 'You are a technical editor. Summarize the following sequence of shell actions, tool outputs, and findings into a concise list of "Achievements so far". Keep path names and key findings intact but remove verbose output.'},
        {'role': 'user', 'content': json.dumps(to_summarize)}
    ]
    
    try:
        response = get_chat_response(summary_prompt)
        summary_text = response.get('content', 'Conversation history was compressed.')
        
        compressed_msg = {
            'role': 'user',
            'content': f"--- SESSION COMPRESSED ---\nSummary of previous steps:\n{summary_text}\n--- END SUMMARY ---"
        }
        ack_msg = {
            'role': 'assistant',
            'content': "Understood. I have the summary of our progress so far and am ready to continue."
        }
        
        new_messages = [system_msg] + initial_context + [compressed_msg, ack_msg] + recent_msgs
        return new_messages
    except Exception as e:
        debug_log(f"Compression failed: {e}")
        return messages

def main():
    try:
        from fish_ai.engine import get_chat_response, get_os, get_logger
        
        parser = argparse.ArgumentParser()
        parser.add_argument('--state', required=True, help='Path to the state JSON file')
        parser.add_argument('--action-file', required=True, help='Path to the action output file')
        parser.add_argument('--goal', help='The initial goal')
        parser.add_argument('--external-history', help='Recent shell commands executed outside the agent')
        parser.add_argument('--cwd', help='Current working directory of the shell')
        parser.add_argument('--last-output', help='Output from the last executed command/tool')
        parser.add_argument('--last-status', type=int, help='Exit status from the last command')
        parser.add_argument('--rejected', action='store_true', help='Set if the last proposed command was rejected')
        parser.add_argument('--compress', action='store_true', help='Force compression of history')

        args = parser.parse_args()
        
        full_system_prompt = SYSTEM_PROMPT + "\nOperating System: {os}\n".format(os=get_os())

        messages = []
        if os.path.exists(args.state) and os.path.getsize(args.state) > 0:
            with open(args.state, 'r') as f:
                try: messages = json.load(f)
                except: messages = []
        
        if not messages:
            messages = [{'role': 'system', 'content': full_system_prompt}]
            context_msg = "Context:\n"
            if args.cwd: context_msg += f"- Current directory: {args.cwd}\n"
            if args.external_history: context_msg += f"- Recent shell history:\n{args.external_history}\n"
            
            if args.cwd or args.external_history:
                messages.append({'role': 'user', 'content': context_msg})
                messages.append({'role': 'assistant', 'content': "Understood. I am aware of the current directory and recent shell history."})
        
        if args.goal:
            messages.append({'role': 'user', 'content': args.goal})
        elif not messages or len(messages) <= 1:
            messages.append({'role': 'user', 'content': 'Hello, how can I help you today?'})

        if args.rejected:
            messages.append({'role': 'user', 'content': 'I rejected that command. Please try a different way.'})
        elif args.last_output is not None:
            content = args.last_output
            if args.last_status is not None:
                content = f"Exit status: {args.last_status}\n\nOutput:\n{content}"
            
            last_tool_call_id = None
            for msg in reversed(messages):
                if msg.get('role') == 'assistant' and msg.get('tool_calls'):
                    last_tool_call_id = msg['tool_calls'][0]['id']
                    break
            
            if last_tool_call_id:
                messages.append({'role': 'tool', 'tool_call_id': last_tool_call_id, 'content': content})
            else:
                messages.append({'role': 'user', 'content': content})

        # Automatic or manual compression
        if args.compress or len(messages) > 20:
            messages = compress_history(messages)
            with open(args.state, 'w') as f:
                json.dump(messages, f)

        response = get_chat_response(messages, tools=TOOLS)
        if not response: raise Exception("AI returned empty response.")

        messages.append(response)
        with open(args.state, 'w') as f:
            json.dump(messages, f)

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

        if thought:
            sys.stdout.write(f"THOUGHT\n{thought}\nEND_THOUGHT\n")

        if response.get('tool_calls'):
            tool_call = response['tool_calls'][0]
            func_name = tool_call['function']['name'].split(':')[-1]
            func_args = json.loads(tool_call['function']['arguments'])

            if func_name == 'shell_execute':
                with open(args.action_file, 'w') as f:
                    f.write(func_args['command'])
                sys.stdout.write("EXECUTE\n")
            else:
                args_str = ", ".join([f"{k}={v}" for k, v in func_args.items()])
                sys.stdout.write(f"TOOL_CALL: {func_name}({args_str})\n")
                
                result = ""
                if func_name == 'read_file': result = read_file(func_args['path'])
                elif func_name == 'list_directory': result = list_directory(func_args['path'])
                elif func_name == 'write_file': result = write_file(func_args['path'], func_args['content'])
                else: result = f"Unknown tool: {func_name}"
                
                sys.stdout.write(f"TOOL_RESULT\n{result}\nEND_RESULT\n")
                
                messages.append({'role': 'tool', 'tool_call_id': tool_call['id'], 'content': result})
                with open(args.state, 'w') as f:
                    json.dump(messages, f)
                sys.stdout.write("CONTINUE\n")
        else:
            if not remaining_content and thought:
                remaining_content = thought
            with open(args.action_file, 'w') as f:
                f.write(remaining_content)
            sys.stdout.write("DONE\n" if "DONE" in full_content.upper() else "CHAT\n")
        
        sys.stdout.flush()
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
