# -*- coding: utf-8 -*-

import sys
import json
import argparse
from fish_ai import engine

SYSTEM_PROMPT = """
You are a concise technical assistant. 
Respond directly to the user's request. 
If input is provided via stdin, treat it as the context for the task.
Do not use markdown formatting unless specifically asked for.
"""

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('prompt', nargs='*', help='The query prompt')
    parser.add_argument('--json', action='store_true', help='Output raw JSON response')
    args = parser.parse_args()

    prompt = ' '.join(args.prompt)
    stdin_data = ''

    if not sys.stdin.isatty():
        stdin_data = sys.stdin.read().strip()

    if not prompt and not stdin_data:
        print("Usage: pond ai <prompt> OR <command> | pond ai <prompt>")
        sys.exit(1)

    user_content = ''
    if stdin_data:
        user_content = f"Context:\n{stdin_data}\n\nTask: {prompt or 'process this input'}"
    else:
        user_content = prompt

    messages = [
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'user', 'content': user_content}
    ]

    try:
        response = engine.get_chat_response(messages)
        
        if args.json:
            print(json.dumps(response, indent=2))
            sys.exit(0)

        content = response.get('content', '').strip()
        if content:
            print(content)
    except Exception as e:
        sys.stderr.write(f"Error: {str(e)}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
