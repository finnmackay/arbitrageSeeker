"""
Logging Configuration
Centralized logging setup for the arbitrage bot
"""
import logging
import sys
from pathlib import Path
import config


def setup_logger(name: str = None, log_file: str = None, log_level: str = None):
    """
    Set up and configure logger

    Args:
        name: Logger name (defaults to 'arbitrage_bot')
        log_file: Log file path (defaults to config.LOG_FILE)
        log_level: Log level (defaults to config.LOG_LEVEL)

    Returns:
        logging.Logger: Configured logger instance
    """
    logger_name = name or 'arbitrage_bot'
    logger = logging.getLogger(logger_name)

    # Only configure if not already configured
    if logger.handlers:
        return logger

    # Set log level
    level = getattr(logging, (log_level or config.LOG_LEVEL).upper(), logging.INFO)
    logger.setLevel(level)

    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    simple_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )

    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)

    # File handler (if log file specified)
    file_path = log_file or config.LOG_FILE
    if file_path:
        try:
            # Create logs directory if it doesn't exist
            log_path = Path(file_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(file_path)
            file_handler.setLevel(level)
            file_handler.setFormatter(detailed_formatter)
            logger.addHandler(file_handler)

            logger.info(f"Logging to file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to set up file logging: {e}")

    return logger


def get_logger(name: str = None):
    """
    Get a logger instance

    Args:
        name: Logger name (defaults to 'arbitrage_bot')

    Returns:
        logging.Logger: Logger instance
    """
    logger_name = name or 'arbitrage_bot'
    logger = logging.getLogger(logger_name)

    # Set up logger if not already configured
    if not logger.handlers:
        return setup_logger(logger_name)

    return logger
