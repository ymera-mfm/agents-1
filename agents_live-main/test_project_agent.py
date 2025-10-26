"""Unit tests for Project Agent"""

import pytest
from agents.project_agent.agent import ProjectAgent, QualityAnalyzer


class TestQualityAnalyzer:
    """Test quality analysis functionality"""
    
    @pytest.fixture
    def analyzer(self):
        return QualityAnalyzer(threshold=0.85)
    
    @pytest.mark.asyncio
    async def test_analyze_high_quality_code(self, analyzer, sample_code, sample_metadata):
        """Test analysis of high quality code"""
        result = await analyzer.analyze_code_quality(sample_code, sample_metadata)
        
        assert 'quality_score' in result
        assert 'passed' in result
        assert 'issues' in result
        assert isinstance(result['quality_score'], float)
        assert result['quality_score'] >= 0.0
    
    @pytest.mark.asyncio
    async def test_analyze_low_quality_code(self, analyzer):
        """Test analysis of low quality code"""
        low_quality_code = "x=1"
        result = await analyzer.analyze_code_quality(low_quality_code, {})
        
        assert result['quality_score'] < 0.85
        assert not result['passed']
        assert len(result['issues']) > 0


class TestProjectAgent:
    """Test Project Agent functionality"""
    
    @pytest.mark.asyncio
    async def test_receive_agent_output(self, db_manager, test_settings, sample_code, sample_metadata):
        """Test receiving agent output"""
        # This is a placeholder - actual test would require full initialization
        # In production, you would mock dependencies
        pass
