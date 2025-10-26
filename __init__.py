"""
Agent Manager Module
Manages workflow, monitoring, and lifecycle of all agents in the platform
"""

__all__ = ["__version__"]
# Conditional imports to avoid breaking tests
try:
    from .agent import AgentManager
    __all__ = ['AgentManager']
except ImportError:
    __all__ = []

__version__ = '2.0.0'
