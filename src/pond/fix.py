# -*- coding: utf-8 -*-

from pond import engine
import textwrap


def get_instructions(command, error_message):
    return [
        {
            'role': 'system',
            'content': textwrap.dedent('''\
            Provide a fixed shell command given an error message from stdout.
            ''')
        },
        {
            'role': 'user',
            'content': textwrap.dedent('''\
            Command:

            ./foo.sh

            Error message:

            fish: Unknown command. './foo.sh' exists but is not executable.''')
        },
        {
            'role': 'assistant',
            'content': 'sh ./foo.sh'
        },
        {
            'role': 'user',
            'content': textwrap.dedent('''\
            Command:

            tree -d 1 .

            Error message:

            Command 'tree' not found, but can be installed with:
            sudo apt install tree''')
        },
        {
            'role': 'assistant',
            'content': 'sudo apt install tree'
        },
        {
            'role': 'user',
            'content': textwrap.dedent('''\
            Command:

            {}

            Error message:

            {}

            Output only the shell command that fixes the problem.
            Do not explain your solution.''').format(command, error_message)
        }
    ]


def get_messages(command, error_message):
    return [engine.get_system_prompt()] + get_instructions(
        command, error_message)


def get_error_message(previous_command):
    """Do not replay arbitrary shell history merely to reconstruct stderr."""
    return "Command output was not captured; do not rerun the command automatically."


def fix():
    engine.get_logger().info('----- BEGIN SESSION -----')

    previous_command = engine.get_args()[0]
    error_message = get_error_message(previous_command)

    try:
        engine.get_logger().debug('Fixing command: ' + previous_command)
        engine.get_logger().debug('Command output: ' + str(error_message))
        response = engine.get_response(
            messages=get_messages(previous_command, error_message))
        print(response, end='')
    except Exception as e:
        engine.get_logger().exception(e)
        print('# An error occurred when running fish-ai. More info: ' +
              str(e.args), end='')
    finally:
        engine.get_logger().info('----- END SESSION -----')
