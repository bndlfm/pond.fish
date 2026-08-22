# -*- coding: utf-8 -*-

from unittest.mock import patch

from pond.codify import codify


@patch('pond.engine.get_args', lambda: ['# hello'])
@patch('pond.engine.get_response', lambda messages: 'echo hello')
def test_successful_codify(capsys):
    codify()
    assert capsys.readouterr().out == 'echo hello'
    assert capsys.readouterr().err == ''


@patch('pond.engine.get_args', lambda: ['# hello'])
@patch('pond.engine.get_response',
       side_effect=Exception('crystal ball failed'))
def test_unsuccessful_codify(_, caplog):
    codify()
    assert 'crystal ball failed' in caplog.text
