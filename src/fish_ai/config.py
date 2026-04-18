# -*- coding: utf-8 -*-

from os import path
import sys
from configparser import ConfigParser
import os


def get_config_path():
    if 'XDG_CONFIG_HOME' in os.environ:
        config_dir = path.expandvars('$XDG_CONFIG_HOME/fish-ai')
    else:
        config_dir = path.expanduser('~/.config/fish-ai')
    
    if not path.exists(config_dir):
        try: os.makedirs(config_dir, exist_ok=True)
        except: pass
        
    return path.join(config_dir, 'config.ini')


def lookup_setting():
    value = get_config(sys.argv[1] or '')
    if value is not None:
        print(value)
    elif len(sys.argv) > 2:
        print(sys.argv[2])
    else:
        print('')


def put_setting():
    config.set(section=sys.argv[1], option=sys.argv[2], value=sys.argv[3])
    with open(get_config_path(), 'w') as f:
        config.write(f)


def get_config(key):
    if not config.has_section('fish-ai'):
        return None

    try:
        active_section = config.get(section='fish-ai', option='configuration')
    except:
        return None

    if config.has_section(active_section) and config.has_option(section=active_section, option=key):
        return path.expandvars(config.get(section=active_section, option=key))

    if config.has_option(section='fish-ai', option=key):
        return path.expandvars(config.get(section='fish-ai', option=key))

    if key == 'api_key' and active_section:
        # If not specified in the configuration, try to load from keyring
        try:
            import keyring
            return keyring.get_password('fish-ai', active_section)
        except:
            return None

    return None


config = ConfigParser()
config.read(get_config_path())
