"""
Language Tool Python Stub

This is a stub module that provides compatibility when language-tool-python is not installed.

To use the real implementation:
    pip install language-tool-python
"""

__version__ = "0.0.0-stub"


class LanguageTool:
    """Stub LanguageTool"""
    
    def __init__(self, language='en-US'):
        self.language = language
    
    def check(self, text):
        """Stub check method - returns empty list (no errors)"""
        return []
    
    def correct(self, text):
        """Stub correct method - returns text unchanged"""
        return text
    
    def close(self):
        """Stub close method"""
        pass


__all__ = [
    'LanguageTool',
]
