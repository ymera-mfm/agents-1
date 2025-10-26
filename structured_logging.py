"""
Structured Logging Module
Implements structured logging pattern with context
"""

import logging
import json
import sys
from typing import Any, Dict, Optional
from datetime import datetime
from pathlib import Path

from core.config import settings
from core.integration_config import integration_settings


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter for structured logging
    Outputs logs in JSON format
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        
        # Base log data
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": integration_settings.service_name,
            "version": integration_settings.service_version,
            "environment": settings.environment,
        }
        
        # Add extra fields
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "trace_id"):
            log_data["trace_id"] = record.trace_id
        if hasattr(record, "span_id"):
            log_data["span_id"] = record.span_id
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "agent_id"):
            log_data["agent_id"] = record.agent_id
        if hasattr(record, "task_id"):
            log_data["task_id"] = record.task_id
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add any other extra fields
        for key, value in record.__dict__.items():
            if key not in [
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "message", "pathname", "process", "processName",
                "relativeCreated", "thread", "threadName", "exc_info",
                "exc_text", "stack_info", "request_id", "trace_id",
                "span_id", "user_id", "agent_id", "task_id"
            ]:
                if not key.startswith("_"):
                    log_data[key] = value
        
        return json.dumps(log_data)


class TextFormatter(logging.Formatter):
    """
    Custom formatter for human-readable text logging
    Used in development
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as text"""
        
        # Base message
        message = f"{record.levelname:<8} [{record.name}] {record.getMessage()}"
        
        # Add context
        context_parts = []
        if hasattr(record, "request_id"):
            context_parts.append(f"request_id={record.request_id}")
        if hasattr(record, "user_id"):
            context_parts.append(f"user_id={record.user_id}")
        if hasattr(record, "agent_id"):
            context_parts.append(f"agent_id={record.agent_id}")
        if hasattr(record, "task_id"):
            context_parts.append(f"task_id={record.task_id}")
        
        if context_parts:
            message += f" [{', '.join(context_parts)}]"
        
        # Add exception if present
        if record.exc_info:
            message += f"\n{self.formatException(record.exc_info)}"
        
        return message


def setup_logging() -> None:
    """
    Configure structured logging for the application
    """
    
    # Determine log level
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # Create logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Choose formatter based on log format setting
    if settings.log_format.lower() == "json":
        console_handler.setFormatter(StructuredFormatter())
    else:
        console_handler.setFormatter(TextFormatter())
    
    root_logger.addHandler(console_handler)
    
    # File handler (if log file is configured)
    if settings.log_file:
        log_path = Path(settings.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(settings.log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(file_handler)
    
    # Log startup message
    root_logger.info(
        "Logging configured",
        extra={
            "log_level": settings.log_level,
            "log_format": settings.log_format,
            "log_file": settings.log_file,
        }
    )


class StructuredLogger:
    """
    Wrapper for structured logging with context
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def _log(
        self,
        level: int,
        message: str,
        request_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        task_id: Optional[str] = None,
        **kwargs
    ) -> None:
        """Log with structured context"""
        
        extra = {}
        if request_id:
            extra["request_id"] = request_id
        if trace_id:
            extra["trace_id"] = trace_id
        if span_id:
            extra["span_id"] = span_id
        if user_id:
            extra["user_id"] = user_id
        if agent_id:
            extra["agent_id"] = agent_id
        if task_id:
            extra["task_id"] = task_id
        
        # Add any additional context
        extra.update(kwargs)
        
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message"""
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message"""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message"""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log error message"""
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """Log critical message"""
        self._log(logging.CRITICAL, message, **kwargs)


def get_logger(name: str) -> StructuredLogger:
    """
    Get a structured logger instance
    
    Args:
        name: Logger name
        
    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(name)
