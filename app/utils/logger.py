import logging
import sys
from logging.handlers import RotatingFileHandler

def setup_logger(name, config=None):
    """
    Set up logger with file and console handlers.
    
    Args:
        name (str): Logger name
        config: Configuration object with LOG_LEVEL attribute
        
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Set log level from config or default to INFO
    log_level = getattr(config, 'LOG_LEVEL', 'INFO')
    logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    # Create formatters and handlers
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    try:
        # File handler
        file_handler = RotatingFileHandler(
            'logs/app.log',
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
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
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger 