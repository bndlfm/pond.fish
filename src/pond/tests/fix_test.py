# -*- coding: utf-8 -*-

from unittest.mock import patch

import pytest

from pond.fix import fix, get_error_message
from subprocess import CalledProcessError


@patch('pond.engine.get_args', lambda: ['foo'])
@patch('subprocess.check_output',
       side_effect=CalledProcessError(
           output=b'permission denied',
           returncode=1,
           cmd=['foo']))
@patch('pond.engine.get_response')
def test_successful_fix(mock_get_response, _, capsys):
    mock_get_response.return_value = 'sudo foo'
    fix()
    assert 'permission denied' in mock_get_response \
        .call_args.kwargs['messages'][-1]['content']
    assert capsys.readouterr().out == 'sudo foo'
    assert capsys.readouterr().err == ''


@pytest.mark.xfail(
    strict=True,
    reason='Pond 2.x reruns the previous command to recover its output',
)
def test_get_error_message_does_not_reexecute_failed_command(tmp_path):
    marker = tmp_path / 'unexpected-second-execution'

    get_error_message(f"sh -c 'touch {marker}; exit 1'")

    assert not marker.exists()
