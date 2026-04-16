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
            return f.read()
    except Exception as e:
        return str(e)

def write_file(path, content):
    try:
        with open(path, 'w') as f:
            f.write(content)
        return "File written successfully."
    except Exception as e:
        return str(e)

def edit_file(path, old_text, new_text):
    try:
        with open(path, 'r') as f:
            content = f.read()
        if old_text not in content:
            return f"Error: Could not find exact match for 'old_text' in {path}."
        if content.count(old_text) > 1:
            return f"Error: Multiple occurrences of 'old_text' found in {path}. Please be more specific."
        new_content = content.replace(old_text, new_text)
        with open(path, 'w') as f:
            f.write(new_content)
        return "File edited successfully."
    except Exception as e:
        return str(e)

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
            "name": "read_file",
            "description": "Read the entire content of a file.",
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
            "name": "edit_file",
            "description": "Make a surgical edit to a file by replacing old_text with new_text. old_text must match exactly one occurrence.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "The path to the file."},
                    "old_text": {"type": "string", "description": "The exact text to be replaced."},
                    "new_text": {"type": "string", "description": "The new text to insert."}
                },
                "required": ["path", "old_text", "new_text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create a new file or overwrite an existing one.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "The path to the file."},
                    "content": {"type": "string", "description": "The content to write."}
                },
                "required": ["path", "content"]
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
    }
]

SYSTEM_PROMPT = """
You are an expert coding assistant. You help users with tasks by reading files, executing commands, editing code, and writing files.

Available tools:
- read_file: Read file contents
- shell_execute: Execute shell commands
- edit_file: Make surgical edits (old_text must match exactly)
- write_file: Create or overwrite files
- list_directory: Explore file structure

Guidelines:
- Use shell_execute for operations like ls, grep, find.
- Use read_file to examine files before editing.
- Use edit_file for precise changes.
- Use write_file only for new files or complete rewrites.
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
            full_prompt = SYSTEM_PROMPT + "\nOS: {os}\n".format(os=get_os())
            messages = [{'role': 'system', 'content': full_prompt}]
            context = "Context:\n"
            if args.cwd: context += f"- CWD: {args.cwd}\n"
            if args.external_history: context += f"- Recent history:\n{args.external_history}\n"
            if args.cwd or args.external_history:
                messages.append({'role': 'user', 'content': context})
                messages.append({'role': 'assistant', 'content': "Context received."})
        
        if args.goal:
            messages.append({'role': 'user', 'content': args.goal})
        elif not messages or len(messages) <= 1:
            messages.append({'role': 'user', 'content': 'Ready.'})

        if args.rejected:
            messages.append({'role': 'user', 'content': 'Command rejected.'})
        elif args.last_output is not None:
            content = args.last_output
            if args.last_status is not None: content = f"Status: {args.last_status}\nOutput:\n{content}"
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
                if func_name == 'read_file': result = read_file(func_args['path'])
                elif func_name == 'list_directory': result = list_directory(func_args['path'])
                elif func_name == 'write_file': result = write_file(func_args['path'], func_args['content'])
                elif func_name == 'edit_file': result = edit_file(func_args['path'], func_args['old_text'], func_args['new_text'])
                else: result = f"Unknown tool: {func_name}"
                
                sys.stdout.write(f"TOOL_RESULT\n{result}\nEND_RESULT\n")
                messages.append({'role': 'tool', 'tool_call_id': tool_call['id'], 'content': result})
                with open(args.state, 'w') as f: json.dump(messages, f)
                sys.stdout.write("CONTINUE\n")
        else:
            if not remaining_content and thought: remaining_content = thought
            with open(args.action_file, 'w') as f: f.write(remaining_content)
            sys.stdout.write("DONE\n" if "DONE" in full_content.upper() else "CHAT\n")
        
        # Report usage if available
        if 'usage' in response:
            u = response['usage']
            sys.stdout.write(f"USAGE: prompt={u.get('prompt_tokens', 0)} completion={u.get('completion_tokens', 0)} total={u.get('total_tokens', 0)}\n")

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
