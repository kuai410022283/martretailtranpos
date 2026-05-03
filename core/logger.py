import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

class Logger:
    _instance = None
    _logger = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._logger is None:
            self._logger = logging.getLogger('MRTPOS')
            self._logger.setLevel(logging.DEBUG)
            self._logger.propagate = False
    
    def setup(self, config=None):
        if config is None:
            config = {
                'level': 'INFO',
                'file': 'logs/mrtpos.log',
                'max_size': 10,
                'backup_count': 5
            }
        
        log_level = getattr(logging, config.get('level', 'INFO'), logging.INFO)
        log_file = config.get('file', 'logs/mrtpos.log')
        max_size = config.get('max_size', 10) * 1024 * 1024
        backup_count = config.get('backup_count', 5)
        
        self._logger.setLevel(log_level)
        
        for handler in self._logger.handlers[:]:
            self._logger.removeHandler(handler)
            handler.close()
        
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self._logger.addHandler(file_handler)
        
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self._logger.addHandler(console_handler)
    
    def debug(self, message):
        self._logger.debug(message)
    
    def info(self, message):
        self._logger.info(message)
    
    def warning(self, message):
        self._logger.warning(message)
    
    def error(self, message, exc_info=False):
        self._logger.error(message, exc_info=exc_info)
    
    def critical(self, message, exc_info=False):
        self._logger.critical(message, exc_info=exc_info)

logger = Logger()

def get_logger():
    return logger
