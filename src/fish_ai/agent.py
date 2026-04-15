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
            if args.cwd:
                context_msg += f"- Current directory: {args.cwd}\n"
            if args.external_history:
                context_msg += f"- Recent shell history:\n{args.external_history}\n"
            
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

        response = get_chat_response(messages, tools=TOOLS)
        if not response: raise Exception("AI returned empty response.")

        messages.append(response)
        with open(args.state, 'w') as f:
            json.dump(messages, f)

        full_content = response.get('content', '')
        remaining_content = full_content
        thought = ""
        
        # Extract thought if present
        if '<think>' in full_content:
            import re
            m = re.search(r'<think>(.*?)</think>(.*)', full_content, re.DOTALL)
            if m:
                thought = m.group(1).strip()
                remaining_content = m.group(2).strip()
        else:
            # If no explicit think tag, the entire content might be a thought if there's a tool call
            if response.get('tool_calls'):
                thought = full_content.strip()
                remaining_content = ""

        # If there's a thought, report it
        if thought:
            sys.stdout.write(f"THOUGHT\n{thought}\nEND_THOUGHT\n")
        
        # Process Actions
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
            # Final message (CHAT or DONE)
            # If everything was a thought and no tool calls, treat it as message
            if not remaining_content and thought:
                remaining_content = thought
            
            with open(args.action_file, 'w') as f:
                f.write(remaining_content)
            
            if "DONE" in full_content.upper():
                sys.stdout.write("DONE\n")
            else:
                sys.stdout.write("CHAT\n")
        
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
