# -*- coding: utf-8 -*-

import sys
from fish_ai import engine

SYSTEM_PROMPT = """
You are a concise technical assistant. 
Respond directly to the user's request. 
If input is provided via stdin, treat it as the context for the task.
Do not use markdown formatting unless specifically asked for.
"""

def main():
    prompt = ' '.join(sys.argv[1:])
    stdin_data = ''

    if not sys.stdin.isatty():
        stdin_data = sys.stdin.read().strip()

    if not prompt and not stdin_data:
        print("Usage: ai <prompt> OR <command> | ai <prompt>")
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
        content = response.get('content', '').strip()
        if content:
            print(content)
    except Exception as e:
        sys.stderr.write(f"Error: {str(e)}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
