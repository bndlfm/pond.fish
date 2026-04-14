# -*- coding: utf-8 -*-

import json
import sys
import argparse
import os
from fish_ai.engine import get_chat_response, get_logger, get_os

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

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--state', required=True, help='Path to the state JSON file')
    parser.add_argument('--action-file', required=True, help='Path to the action output file')
    parser.add_argument('--goal', help='The initial goal (only provided on the first call)')
    parser.add_argument('--last-output', help='Output from the last executed command/tool')
    parser.add_argument('--last-status', type=int, help='Exit status from the last command')
    parser.add_argument('--rejected', action='store_true', help='Set if the last proposed command was rejected by the user')

    args = parser.parse_args()

    messages = []
    if os.path.exists(args.state) and os.path.getsize(args.state) > 0:
        with open(args.state, 'r') as f:
            try:
                messages = json.load(f)
            except json.JSONDecodeError:
                messages = []
    
    if not messages:
        messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]
        if args.goal:
            messages.append({'role': 'user', 'content': args.goal})

    if args.rejected:
        messages.append({'role': 'user', 'content': 'I have rejected the proposed command. Please try a different approach or ask for clarification.'})
    elif args.last_output is not None:
        content = args.last_output
        if args.last_status is not None:
            content = f"Command exited with status {args.last_status}\n\nOutput:\n{content}"
        
        # In a real tool-calling loop, the previous message from assistant had tool_calls.
        # We need to append the tool result message.
        # However, for simplicity in the first version, we'll handle tool results as user messages
        # if the engine doesn't fully support structured tool history yet.
        # But let's try to do it properly.
        
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
    try:
        get_logger().debug('Agent calling engine with {} messages'.format(len(messages)))
        response = get_chat_response(messages, tools=TOOLS)
        get_logger().debug('Agent received response: {}'.format(response))
    except Exception as e:
        get_logger().error('Agent engine error: {}'.format(str(e)))
        with open(args.action_file, 'w') as f:
            f.write(str(e))
        print("ERROR")
        sys.exit(1)

    if not response or (not response.get('content') and not response.get('tool_calls')):
        error_msg = "The AI returned an empty response. Check your configuration/API key."
        get_logger().error(error_msg)
        with open(args.action_file, 'w') as f:
            f.write(error_msg)
        print("ERROR")
        sys.exit(1)

    messages.append(response)

    # Save state
    with open(args.state, 'w') as f:
        json.dump(messages, f)

    # Process response
    if response.get('tool_calls'):
        # For now, we process one tool call at a time to keep the shell interaction simple.
        # But we must ensure shell_execute is prioritized or handled distinctly.
        tool_call = response['tool_calls'][0]
        func_name = tool_call['function']['name']
        func_args = json.loads(tool_call['function']['arguments'])

        if func_name == 'shell_execute':
            # Signal the shell wrapper to ask for confirmation
            with open(args.action_file, 'w') as f:
                f.write(func_args['command'])
            print("EXECUTE")
        else:
            # Execute internal tools immediately
            result = ""
            try:
                if func_name == 'read_file':
                    result = read_file(func_args['path'])
                elif func_name == 'list_directory':
                    result = list_directory(func_args['path'])
                elif func_name == 'write_file':
                    result = write_file(func_args['path'], func_args['content'])
                else:
                    result = f"Unknown tool: {func_name}"
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
            
            # Print CONTINUE so the shell wrapper calls us again immediately
            print("CONTINUE")
    else:
        content = response.get('content', '')
        with open(args.action_file, 'w') as f:
            f.write(content)
        if "DONE" in content.upper():
            print("DONE")
        else:
            print("CHAT")

if __name__ == "__main__":
    main()
