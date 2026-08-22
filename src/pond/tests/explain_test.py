# -*- coding: utf-8 -*-

from unittest.mock import patch

from pond.explain import explain


@patch('pond.engine.get_args', lambda: ['echo hello'])
@patch('pond.engine.get_response', lambda messages: 'print hello')
def test_successful_explain(capsys):
    explain()
    assert capsys.readouterr().out == '# print hello \
Example command: echo hello'
    assert capsys.readouterr().err == ''


@patch('pond.engine.get_args', lambda: ['echo hello'])
@patch('pond.engine.get_response',
       side_effect=Exception('crystal ball failed'))
def test_unsuccessful_explain(_, caplog):
    explain()
    assert 'crystal ball failed' in caplog.text
