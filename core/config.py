import configparser
import os

def load_config(config_file=None):
    if config_file is None:
        config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.ini')
    
    config = configparser.ConfigParser()
    
    default_config = {
        'database': {
            'type': 'sqlite',
            'path': 'data/mrtpos.db',
            'host': 'localhost',
            'port': '5432',
            'database': 'mrtpos',
            'username': '',
            'password': ''
        },
        'system': {
            'app_name': 'MartRetailTranPOS',
            'version': '1.0.0',
            'language': 'zh_CN'
        },
        'printer': {
            'enabled': 'true',
            'type': 'escpos',
            'port': 'USB',
            'ip': '192.168.1.100'
        },
        'logging': {
            'level': 'INFO',
            'file': 'logs/mrtpos.log',
            'max_size': '10',
            'backup_count': '5'
        }
    }
    
    for section, options in default_config.items():
        if not config.has_section(section):
            config.add_section(section)
        for key, value in options.items():
            if not config.has_option(section, key):
                config.set(section, key, value)
    
    if os.path.exists(config_file):
        config.read(config_file, encoding='utf-8')
    else:
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        with open(config_file, 'w', encoding='utf-8') as f:
            config.write(f)
    
    return {
        'database': {
            'database_type': config.get('database', 'type'),
            'database_path': config.get('database', 'path'),
            'host': config.get('database', 'host'),
            'port': config.getint('database', 'port'),
            'database': config.get('database', 'database'),
            'username': config.get('database', 'username'),
            'password': config.get('database', 'password')
        },
        'system': {
            'app_name': config.get('system', 'app_name'),
            'version': config.get('system', 'version'),
            'language': config.get('system', 'language')
        },
        'printer': {
            'enabled': config.getboolean('printer', 'enabled'),
            'type': config.get('printer', 'type'),
            'port': config.get('printer', 'port'),
            'ip': config.get('printer', 'ip')
        },
        'logging': {
            'level': config.get('logging', 'level'),
            'file': config.get('logging', 'file'),
            'max_size': config.getint('logging', 'max_size'),
            'backup_count': config.getint('logging', 'backup_count')
        }
    }
