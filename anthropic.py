"""
Anthropic SDK Stub

This is a stub module that provides compatibility when anthropic SDK is not installed.

To use the real implementation:
    pip install anthropic
"""

__version__ = "0.0.0-stub"


class AsyncAnthropic:
    """Stub AsyncAnthropic client"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.messages = Messages()


class Anthropic:
    """Stub Anthropic client"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.messages = Messages()


class Messages:
    """Stub Messages API"""
    
    async def create(self, **kwargs):
        """Stub create method"""
        class StubResponse:
            content = [{"text": "This is a stub response. Install anthropic SDK for real responses."}]
            model = kwargs.get("model", "claude-3-opus-20240229")
            role = "assistant"
        
        return StubResponse()


__all__ = [
    'Anthropic',
    'AsyncAnthropic',
    'Messages',
]
