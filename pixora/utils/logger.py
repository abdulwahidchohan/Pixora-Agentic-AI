"""
Logging configuration for Pixora system.

Provides structured logging with both console and file output,
configurable log levels, and JSON formatting for production use.
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import structlog
from rich.console import Console
from rich.logging import RichHandler

from .config import config


def setup_logging(
    log_level: Optional[str] = None,
    log_to_file: bool = True,
    log_file_path: Optional[str] = None
) -> None:
    """
    Set up logging configuration for Pixora.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to log to file
        log_file_path: Path to log file
    """
    # Use configuration values if not provided
    log_level = log_level or config.log_level
    log_to_file = log_to_file if log_to_file is not None else config.log_to_file
    log_file_path = log_file_path or config.log_file_path
    
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler with rich formatting
    console_handler = RichHandler(
        console=Console(),
        show_time=True,
        show_path=True,
        markup=True
    )
    console_handler.setLevel(numeric_level)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler for structured logging
    if log_to_file:
        try:
            log_file = Path(log_file_path)
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file_path)
            file_handler.setLevel(numeric_level)
            
            # JSON formatter for file output
            json_formatter = logging.Formatter(
                '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
                '"logger": "%(name)s", "message": "%(message)s"}'
            )
            file_handler.setFormatter(json_formatter)
            root_logger.addHandler(file_handler)
            
        except Exception as e:
            # Fallback to console only if file logging fails
            console_handler.setFormatter(logging.Formatter(
                f"WARNING: Failed to set up file logging ({e}). Console only."
            ))
    
    # Set specific logger levels
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.INFO)
    
    # Log startup message
    logger = get_logger(__name__)
    logger.info(
        "Logging configured",
        log_level=log_level,
        log_to_file=log_to_file,
        log_file_path=log_file_path if log_to_file else None
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured structured logger
    """
    return structlog.get_logger(name)


def log_function_call(func_name: str, **kwargs) -> None:
    """
    Log a function call with parameters.
    
    Args:
        func_name: Name of the function being called
        **kwargs: Function parameters to log
    """
    logger = get_logger(__name__)
    logger.info(
        "Function call",
        function=func_name,
        parameters=kwargs
    )


def log_function_result(func_name: str, result: Any, duration_ms: float) -> None:
    """
    Log a function result and execution time.
    
    Args:
        func_name: Name of the function that completed
        result: Function result (will be truncated if too long)
        duration_ms: Execution time in milliseconds
    """
    logger = get_logger(__name__)
    
    # Truncate long results for logging
    result_str = str(result)
    if len(result_str) > 500:
        result_str = result_str[:500] + "... [truncated]"
    
    logger.info(
        "Function completed",
        function=func_name,
        result=result_str,
        duration_ms=round(duration_ms, 2)
    )


def log_error(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None
) -> None:
    """
    Log an error with context information.
    
    Args:
        error: The exception that occurred
        context: Additional context information
        user_id: ID of the user affected
        session_id: ID of the session affected
    """
    logger = get_logger(__name__)
    
    log_data = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "error_traceback": getattr(error, "__traceback__", None)
    }
    
    if context:
        log_data["context"] = context
    if user_id:
        log_data["user_id"] = user_id
    if session_id:
        log_data["session_id"] = session_id
    
    logger.error(
        "Error occurred",
        **log_data
    )


def log_user_action(
    action: str,
    user_id: str,
    session_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a user action for audit purposes.
    
    Args:
        action: Description of the action
        user_id: ID of the user performing the action
        session_id: ID of the session
        details: Additional details about the action
    """
    logger = get_logger(__name__)
    
    log_data = {
        "action": action,
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if session_id:
        log_data["session_id"] = session_id
    if details:
        log_data["details"] = details
    
    logger.info(
        "User action",
        **log_data
    )


def log_performance_metric(
    metric_name: str,
    value: float,
    unit: str,
    tags: Optional[Dict[str, str]] = None
) -> None:
    """
    Log a performance metric.
    
    Args:
        metric_name: Name of the metric
        value: Metric value
        unit: Unit of measurement
        tags: Additional tags for categorization
    """
    logger = get_logger(__name__)
    
    log_data = {
        "metric_name": metric_name,
        "value": value,
        "unit": unit,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if tags:
        log_data["tags"] = tags
    
    logger.info(
        "Performance metric",
        **log_data
    )


# Initialize logging when module is imported
if not logging.getLogger().handlers:
    setup_logging()
