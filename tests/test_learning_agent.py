"""Unit tests for Learning Agent"""

import pytest
from agents.learning_agent.agent import LearningAgent, KnowledgeExtractor


class TestKnowledgeExtractor:
    """Test knowledge extraction"""
    
    @pytest.fixture
    def extractor(self):
        return KnowledgeExtractor()
    
    @pytest.mark.asyncio
    async def test_extract_from_code(self, extractor, sample_code, sample_metadata):
        """Test knowledge extraction from code"""
        knowledge = await extractor.extract_from_code(sample_code, sample_metadata)
        
        assert isinstance(knowledge, dict)
        assert 'patterns' in knowledge
        assert 'libraries' in knowledge
        assert 'techniques' in knowledge
    
    @pytest.mark.asyncio
    async def test_extract_async_pattern(self, extractor):
        """Test detection of async pattern"""
        async_code = "async def test(): pass"
        knowledge = await extractor.extract_from_code(async_code, {})
        
        assert 'async_programming' in knowledge.get('patterns', [])


class TestLearningAgent:
    """Test Learning Agent functionality"""
    
    @pytest.mark.asyncio
    async def test_receive_knowledge(self, db_manager, test_settings):
        """Test receiving knowledge"""
        # Placeholder for actual test with proper initialization
        pass
