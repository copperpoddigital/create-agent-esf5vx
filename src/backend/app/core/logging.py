"""
Core logging module that configures and provides logging functionality for the Document Management and AI Chatbot System.

This module sets up structured logging with appropriate formatters, handlers, and log levels
based on the application environment. It provides:
- Configurable log levels based on environment
- Console and file logging
- JSON-formatted structured logs
- Request ID correlation for request tracing
- Helpers for logging HTTP requests and responses
"""

import logging
import sys
import os
import json
from logging.handlers import RotatingFileHandler
from datetime import datetime
import uuid

from .config import settings

# Default log level if not specified
DEFAULT_LOG_LEVEL = logging.INFO

# Log format strings
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
JSON_LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"

# Log levels by environment
LOG_LEVELS = {
    "development": logging.DEBUG,
    "testing": logging.INFO,
    "production": logging.WARNING
}

# Log file configuration
LOG_DIR = "logs"
MAX_LOG_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5


class JsonFormatter(logging.Formatter):
    """Custom log formatter that outputs logs in JSON format for structured logging."""
    
    def __init__(self):
        """Initializes the JSON formatter."""
        super().__init__()
        
    def format(self, record):
        """
        Formats the log record as a JSON string.
        
        Args:
            record (logging.LogRecord): The log record to format
            
        Returns:
            str: JSON formatted log entry
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if available
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            
        # Add request_id if available
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
            
        # Add any extra attributes
        for key, value in record.__dict__.items():
            if key not in ["args", "asctime", "created", "exc_info", "exc_text", 
                          "filename", "funcName", "id", "levelname", "levelno", 
                          "lineno", "module", "msecs", "message", "msg", "name", 
                          "pathname", "process", "processName", "relativeCreated", 
                          "stack_info", "thread", "threadName", "request_id"]:
                log_data[key] = value
                
        return json.dumps(log_data)


class RequestIdFilter(logging.Filter):
    """Log filter that adds request ID to log records for request correlation."""
    
    def __init__(self):
        """Initializes the request ID filter."""
        super().__init__()
        
    def filter(self, record):
        """
        Adds request ID to the log record if available.
        
        Args:
            record (logging.LogRecord): The log record
            
        Returns:
            bool: True to include the record in the log output
        """
        # Use existing request_id if already set, otherwise generate a new one
        if not hasattr(record, "request_id"):
            record.request_id = get_request_id()
        
        return True


def get_request_id():
    """
    Generates or retrieves a request ID for correlation.
    
    Returns:
        str: Request ID for correlation
    """
    # In a real application, this might retrieve from a context variable
    # For now, we'll generate a new UUID each time
    return str(uuid.uuid4())


def setup_logging(log_level=None):
    """
    Configures the logging system for the application.
    
    Args:
        log_level (str, optional): Explicit log level to use. If not provided,
                                  uses level from settings or environment.
    """
    # Determine log level
    if log_level:
        level = getattr(logging, log_level.upper(), DEFAULT_LOG_LEVEL)
    else:
        # Use from settings or environment
        env = settings.ENV.lower()
        level = LOG_LEVELS.get(env, DEFAULT_LOG_LEVEL)
        
        # Override with explicit setting if provided
        if settings.LOG_LEVEL:
            level = getattr(logging, settings.LOG_LEVEL.upper(), level)
    
    # Create logs directory if it doesn't exist
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicate logs
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        
    # Create console handler with standard formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(LOG_FORMAT)
    console_handler.setFormatter(console_formatter)
    
    # Create file handler for general logs with JSON formatter
    general_log_file = os.path.join(LOG_DIR, f"{settings.APP_NAME.lower().replace(' ', '_')}.log")
    file_handler = RotatingFileHandler(
        general_log_file,
        maxBytes=MAX_LOG_FILE_SIZE,
        backupCount=BACKUP_COUNT
    )
    file_handler.setLevel(level)
    json_formatter = JsonFormatter()
    file_handler.setFormatter(json_formatter)
    
    # Create file handler for error logs
    error_log_file = os.path.join(LOG_DIR, f"{settings.APP_NAME.lower().replace(' ', '_')}_error.log")
    error_file_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=MAX_LOG_FILE_SIZE,
        backupCount=BACKUP_COUNT
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(json_formatter)
    
    # Add request ID filter to all handlers
    request_id_filter = RequestIdFilter()
    console_handler.addFilter(request_id_filter)
    file_handler.addFilter(request_id_filter)
    error_file_handler.addFilter(request_id_filter)
    
    # Add handlers to root logger
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_file_handler)
    
    # Configure specific loggers for third-party libraries
    # Set higher log levels for noisy libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    
    # Get logger for this module and log configuration complete
    logger = get_logger(__name__)
    logger.info(f"Logging configured. Level: {logging.getLevelName(level)}, Environment: {settings.ENV}")


def get_logger(name):
    """
    Returns a configured logger for the specified module.
    
    Args:
        name (str): Module name for the logger
        
    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)


def log_request(request_info):
    """
    Logs details of an incoming HTTP request.
    
    Args:
        request_info (dict): Dictionary containing request information
    """
    logger = get_logger("request")
    # Sanitize sensitive data before logging
    if "headers" in request_info and "authorization" in request_info["headers"]:
        request_info["headers"]["authorization"] = "[REDACTED]"
        
    logger.info(f"Request: {json.dumps(request_info)}")


def log_response(response_info):
    """
    Logs details of an outgoing HTTP response.
    
    Args:
        response_info (dict): Dictionary containing response information
    """
    logger = get_logger("response")
    logger.info(f"Response: {json.dumps(response_info)}")