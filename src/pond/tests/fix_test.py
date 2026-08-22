# -*- coding: utf-8 -*-

from unittest.mock import patch

from pond.fix import fix, get_error_message


@patch('pond.engine.get_args', lambda: ['foo'])
@patch('pond.engine.get_response')
def test_fix_does_not_replay_the_previous_command(mock_get_response, capsys):
    mock_get_response.return_value = 'sudo foo'
    fix()
    assert 'output was not captured' in mock_get_response \
        .call_args.kwargs['messages'][-1]['content']
    assert capsys.readouterr().out == 'sudo foo'
    assert capsys.readouterr().err == ''


def test_get_error_message_does_not_reexecute_failed_command(tmp_path):
    marker = tmp_path / 'unexpected-second-execution'

    get_error_message(f"sh -c 'touch {marker}; exit 1'")

    assert not marker.exists()
