"""
Logging configuration with colored output.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colored output"""
    
    # ANSI color codes
    COLORS = {
        'ERROR': '\033[1;31m',  # Bold Red
        'WARNING': '\033[1;33m',  # Bold Yellow
        'INFO': '\033[0m',  # Default
        'DEBUG': '\033[1;34m',  # Bold Blue
        'RESET': '\033[0m'  # Reset
    }
    
    def format(self, record):
        # Add color if it's an error or warning
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
            if record.levelno >= logging.ERROR:
                record.msg = f"{self.COLORS['ERROR']}{record.msg}{self.COLORS['RESET']}"
        return super().format(record)

def setup_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Set up a logger with colored output.
    
    Args:
        name: Logger name
        level: Optional logging level (DEBUG, INFO, WARNING, ERROR)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Set level from parameter or environment, default to INFO
    logger.setLevel(level or logging.INFO)
    
    # Create console handler if not already added
    if not logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(console_handler)
    
    try:
        # File handler
        file_handler = RotatingFileHandler(
            'logs/app.log',
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(file_handler)
    except FileNotFoundError:
        logger.warning("Logs directory not found. Creating logs directory.")
        import os
        os.makedirs('logs', exist_ok=True)
        file_handler = RotatingFileHandler(
            'logs/app.log',
            maxBytes=10485760,
            backupCount=5
        )
        file_handler.setFormatter(ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(file_handler)
    
    return logger 