"""
Shared utility functions for all agents.
"""

import os
import json
from typing import Any, Dict, Optional, Tuple, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from JSON file."""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config from {config_path}: {e}")
        return {}


def save_config(config: Dict[str, Any], config_path: str):
    """Save configuration to JSON file."""
    try:
        Path(config_path).parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save config to {config_path}: {e}")


def get_env_var(key: str, default: Any = None) -> Any:
    """Get environment variable with default."""
    return os.getenv(key, default)


def validate_payload(
    payload: Dict[str, Any],
    required_keys: List[str]
) -> Tuple[bool, Optional[str]]:
    """
    Validate payload has required keys.
    
    Args:
        payload: Payload dictionary to validate
        required_keys: List of required keys
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    missing_keys = [key for key in required_keys if key not in payload]
    
    if missing_keys:
        return False, f"Missing required keys: {', '.join(missing_keys)}"
    
    return True, None


def format_error(error: Exception) -> Dict[str, Any]:
    """
    Format exception as dictionary.
    
    Args:
        error: Exception to format
    
    Returns:
        Dictionary with error details
    """
    return {
        'type': type(error).__name__,
        'message': str(error),
        'details': getattr(error, 'args', [])
    }


def sanitize_string(value: Any, max_length: int = 1000) -> str:
    """
    Sanitize string input.
    
    Args:
        value: String to sanitize
        max_length: Maximum allowed length
    
    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        value = str(value)
    
    # Truncate if too long
    if len(value) > max_length:
        value = value[:max_length] + "..."
    
    # Remove null bytes
    value = value.replace('\x00', '')
    
    return value


def merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two dictionaries, with override taking precedence.
    
    Args:
        base: Base dictionary
        override: Override dictionary
    
    Returns:
        Merged dictionary
    """
    result = base.copy()
    result.update(override)
    return result


__all__ = [
    'load_config',
    'save_config',
    'get_env_var',
    'validate_payload',
    'format_error',
    'sanitize_string',
    'merge_dicts'
]
