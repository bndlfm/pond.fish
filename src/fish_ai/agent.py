# -*- coding: utf-8 -*-

import json
import sys
import argparse
import os

def get_config_setting(name):
    # Quick fallback to check for debug mode without full engine overhead
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

def main():
    try:
        debug_log("Agent script starting...")
        
        # Delayed import of engine
        from fish_ai.engine import get_chat_response, get_os, get_logger
        
        parser = argparse.ArgumentParser()
        parser.add_argument('--state', required=True, help='Path to the state JSON file')
        parser.add_argument('--action-file', required=True, help='Path to the action output file')
        parser.add_argument('--goal', help='The initial goal (only provided on the first call)')
        parser.add_argument('--last-output', help='Output from the last executed command/tool')
        parser.add_argument('--last-status', type=int, help='Exit status from the last command')
        parser.add_argument('--rejected', action='store_true', help='Set if the last proposed command was rejected by the user')

        args = parser.parse_args()
        
        TOOLS = [
            {
                "type": "function",
                "function": {
                    "name": "shell_execute",
                    "description": "Execute a command in the fish shell. Use this to run any shell commands, including those that modify the shell state (e.g., cd, export). The command will be executed in the user's active shell session.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "The shell command to execute."
                            }
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
                            "path": {
                                "type": "string",
                                "description": "The path to the file."
                            }
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
                            "path": {
                                "type": "string",
                                "description": "The path to the directory."
                            }
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
                            "path": {
                                "type": "string",
                                "description": "The path to the file."
                            },
                            "content": {
                                "type": "string",
                                "description": "The content to write."
                            }
                        },
                        "required": ["path", "content"]
                    }
                }
            }
        ]

        SYSTEM_PROMPT = """
        You are an autonomous shell assistant working inside a fish shell.
        Your goal is to help the user achieve their request by executing commands and using tools.

        Rules:
        1. Use `shell_execute` to run any shell commands.
        2. Use `read_file`, `list_directory`, and `write_file` for file operations.
        3. If a command modifies the shell state (e.g., `cd`, `set -x`), it will be preserved for subsequent commands in this session.
        4. After executing a command or tool, you will receive the output. Use this output to decide your next step.
        5. When the goal is achieved, provide a concise summary of what was done and end with "DONE".
        6. If you are stuck or need clarification, ask the user.

        Operating System: {os}
        """.format(os=get_os())

        messages = []
        if os.path.exists(args.state) and os.path.getsize(args.state) > 0:
            debug_log(f"Loading state from {args.state}")
            with open(args.state, 'r') as f:
                try:
                    messages = json.load(f)
                except json.JSONDecodeError as e:
                    debug_log(f"JSON decode error: {e}")
                    messages = []
        
        if not messages:
            debug_log("Initializing new conversation")
            messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]
            if args.goal:
                messages.append({'role': 'user', 'content': args.goal})
            else:
                messages.append({'role': 'user', 'content': 'Hello, how can I help you today?'})

        if args.rejected:
            messages.append({'role': 'user', 'content': 'I have rejected the proposed command. Please try a different approach or ask for clarification.'})
        elif args.last_output is not None:
            content = args.last_output
            if args.last_status is not None:
                content = f"Command exited with status {args.last_status}\n\nOutput:\n{content}"
            
            # Find the last tool call ID if it exists
            last_tool_call_id = None
            for msg in reversed(messages):
                if msg.get('role') == 'assistant' and msg.get('tool_calls'):
                    last_tool_call_id = msg['tool_calls'][0]['id']
                    break
            
            if last_tool_call_id:
                messages.append({
                    'role': 'tool',
                    'tool_call_id': last_tool_call_id,
                    'content': content
                })
            else:
                messages.append({'role': 'user', 'content': content})

        # Call the engine
        debug_log(f"Calling engine with {len(messages)} messages...")
        response = get_chat_response(messages, tools=TOOLS)
        debug_log(f"Engine response received.")

        if not response or (not response.get('content') and not response.get('tool_calls')):
            raise Exception("The AI returned an empty response. Check your configuration/API key.")

        messages.append(response)

        # Save state
        debug_log(f"Saving state to {args.state}")
        with open(args.state, 'w') as f:
            json.dump(messages, f)

        # Process response
        if response.get('content'):
            content = response['content']
            # Extract and report thoughts
            if '<think>' in content:
                import re
                m = re.search(r'<think>(.*?)</think>(.*)', content, re.DOTALL)
                if m:
                    thought = m.group(1).strip()
                    if thought:
                        sys.stdout.write(f"THOUGHT\n{thought}\nEND_THOUGHT\n")
                    content = m.group(2).strip()
            
            # If there's remaining content that isn't just a tool call, report it as CHAT
            if content and not response.get('tool_calls'):
                with open(args.action_file, 'w') as f:
                    f.write(content)
                if "DONE" in content.upper():
                    sys.stdout.write("DONE\n")
                else:
                    sys.stdout.write("CHAT\n")

        if response.get('tool_calls'):
            tool_call = response['tool_calls'][0]
            func_name = tool_call['function']['name']
            base_func_name = func_name.split(':')[-1]
            func_args = json.loads(tool_call['function']['arguments'])

            if base_func_name == 'shell_execute':
                debug_log(f"Action: EXECUTE {func_args['command']}")
                with open(args.action_file, 'w') as f:
                    f.write(func_args['command'])
                sys.stdout.write("EXECUTE\n")
            else:
                # Execute internal tools immediately
                debug_log(f"Executing internal tool: {base_func_name}")
                
                # Report the tool call to the user
                args_str = ", ".join([f"{k}={v}" for k, v in func_args.items()])
                sys.stdout.write(f"TOOL_CALL: {base_func_name}({args_str})\n")
                
                result = ""
                try:
                    if base_func_name == 'read_file':
                        result = read_file(func_args['path'])
                    elif base_func_name == 'list_directory':
                        result = list_directory(func_args['path'])
                    elif base_func_name == 'write_file':
                        result = write_file(func_args['path'], func_args['content'])
                    else:
                        result = f"Unknown tool: {base_func_name}"
                except Exception as e:
                    result = str(e)
                
                messages.append({
                    'role': 'tool',
                    'tool_call_id': tool_call['id'],
                    'content': result
                })
                # Update state with tool result
                with open(args.state, 'w') as f:
                    json.dump(messages, f)
                
                debug_log("Action: CONTINUE")
                sys.stdout.write("CONTINUE\n")
        
        sys.stdout.flush()
    except Exception as e:
        debug_log(f"CRITICAL ERROR: {e}")
        import traceback
        debug_log(traceback.format_exc())
        with open(args.action_file, 'w') as f:
            f.write(str(e))
        sys.stdout.write("ERROR\n")
        sys.stdout.flush()
        sys.exit(1)

def render_markdown():
    try:
        from rich.console import Console
        from rich.markdown import Markdown
        console = Console()
        content = sys.stdin.read()
        if not content.strip():
            return
        console.print(Markdown(content))
    except Exception as e:
        # Fallback to plain text if rich is not available or fails
        sys.stdout.write(sys.stdin.read())

if __name__ == "__main__":
    main()
