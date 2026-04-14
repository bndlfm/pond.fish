# -*- coding: utf-8 -*-

from fish_ai.agent import TOOLS, SYSTEM_PROMPT
import json

def test_tools_definition():
    assert len(TOOLS) == 4
    tool_names = [t['function']['name'] for t in TOOLS]
    assert 'shell_execute' in tool_names
    assert 'read_file' in tool_names
    assert 'list_directory' in tool_names
    assert 'write_file' in tool_names

def test_system_prompt():
    assert "autonomous shell assistant" in SYSTEM_PROMPT
    assert "fish shell" in SYSTEM_PROMPT

def test_message_formatting():
    # Simple verification that tool calls can be added to history
    messages = [
        {'role': 'system', 'content': 'System message'},
        {'role': 'user', 'content': 'User goal'}
    ]
    
    # Simulate assistant response with tool call
    assistant_msg = {
        'role': 'assistant',
        'content': '',
        'tool_calls': [
            {
                'id': 'tc-1',
                'type': 'function',
                'function': {
                    'name': 'list_directory',
                    'arguments': json.dumps({'path': '.'})
                }
            }
        ]
    }
    messages.append(assistant_msg)
    
    # Simulate tool result
    tool_msg = {
        'role': 'tool',
        'tool_call_id': 'tc-1',
        'content': 'file1.txt\nfile2.txt'
    }
    messages.append(tool_msg)
    
    assert len(messages) == 4
    assert messages[2]['tool_calls'][0]['function']['name'] == 'list_directory'
    assert messages[3]['role'] == 'tool'
