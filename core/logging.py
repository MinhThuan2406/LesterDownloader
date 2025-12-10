"""
Centralized logging configuration for the Discord bot
"""

import logging
import sys
from pathlib import Path
from typing import Optional

def setup_logging(
    log_file: str = "bot.log",
    log_level: str = "INFO",
    enable_console: bool = True,
    enable_file: bool = True
) -> logging.Logger:
    """
    Setup logging configuration
    
    Args:
        log_file: Path to log file
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_console: Whether to log to console
        enable_file: Whether to log to file
        
    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(exist_ok=True)
    
    # Configure logging format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Set up handlers
    handlers = []
    
    if enable_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(log_format, date_format))
        handlers.append(file_handler)
    
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(log_format, date_format))
        handlers.append(console_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        datefmt=date_format,
        handlers=handlers,
        force=True
    )
    
    # Fix Unicode encoding issues on Windows
    if sys.platform == 'win32':
        try:
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8')
                sys.stderr.reconfigure(encoding='utf-8')
        except Exception:
            pass  # Ignore if reconfigure is not available
    
    # Create and return logger
    logger = logging.getLogger('LesterBot')
    logger.info(f"Logging initialized - Level: {log_level}, File: {log_file}")
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

def log_function_call(logger: logging.Logger, func_name: str, **kwargs):
    """
    Log function call with parameters
    
    Args:
        logger: Logger instance
        func_name: Name of the function being called
        **kwargs: Function parameters to log
    """
    params = ', '.join([f"{k}={v}" for k, v in kwargs.items()])
    logger.debug(f"Calling {func_name}({params})")

def log_function_result(logger: logging.Logger, func_name: str, result=None, error=None):
    """
    Log function result or error
    
    Args:
        logger: Logger instance
        func_name: Name of the function
        result: Function result (optional)
        error: Error that occurred (optional)
    """
    if error:
        logger.error(f"{func_name} failed: {error}")
    else:
        logger.debug(f"{func_name} completed successfully")
        if result is not None:
            logger.debug(f"{func_name} returned: {result}")
