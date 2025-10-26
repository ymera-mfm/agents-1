"""
Comprehensive Test Suite for Editing Agent v2.0
Tests all functionality including grammar checking, content analysis, and collaborative editing
"""

import pytest
import asyncio
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from editing_agent import (
    EditingAgent,
    EditingSession,
    EditSuggestion,
    ContentType,
    EditingMode,
    EditType
)
from base_agent import AgentConfig, TaskRequest, Priority, AgentState


@pytest.fixture
def editing_agent_config():
    """Create test configuration for editing agent"""
    return AgentConfig(
        agent_id="test-editing-001",
        name="test_editing_agent",
        agent_type="editing",
        version="2.0.0",
        nats_url="nats://localhost:4222",
        postgres_url="postgresql://user:pass@localhost:5432/testdb",
        redis_url="redis://localhost:6379",
        max_concurrent_tasks=10,
        status_publish_interval_seconds=0,  # Disable for tests
        heartbeat_interval_seconds=0  # Disable for tests
    )


@pytest.fixture
async def mock_connections(monkeypatch):
    """Mock all external connections"""
    # Mock NATS
    mock_nc = AsyncMock()
    mock_nc.publish = AsyncMock()
    mock_nc.subscribe = AsyncMock()
    mock_nc.request = AsyncMock()
    mock_nc.close = AsyncMock()
    mock_nc.drain = AsyncMock()
    
    mock_nats_connect = AsyncMock(return_value=mock_nc)
    monkeypatch.setattr("nats.connect", mock_nats_connect)
    
    # Mock PostgreSQL
    mock_pool = AsyncMock()
    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock()
    mock_conn.fetch = AsyncMock(return_value=[])
    mock_conn.fetchrow = AsyncMock(return_value=None)
    mock_conn.fetchval = AsyncMock(return_value=1)
    mock_pool.acquire = AsyncMock()
    mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_pool.acquire.return_value.__aexit__ = AsyncMock()
    mock_pool.close = AsyncMock()
    
    mock_create_pool = AsyncMock(return_value=mock_pool)
    monkeypatch.setattr("asyncpg.create_pool", mock_create_pool)
    
    # Mock Redis
    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock()
    mock_redis.close = AsyncMock()
    mock_from_url = AsyncMock(return_value=mock_redis)
    monkeypatch.setattr("redis.asyncio.from_url", mock_from_url)
    
    return {
        "nats": mock_nc,
        "postgres": mock_pool,
        "redis": mock_redis
    }


@pytest.fixture
async def editing_agent(editing_agent_config, mock_connections):
    """Create and start editing agent for testing"""
    agent = EditingAgent(editing_agent_config)
    await agent.start()
    
    # Wait for initialization
    await asyncio.sleep(0.1)
    
    yield agent
    
    await agent.stop()


class TestEditingAgentLifecycle:
    """Test agent lifecycle management"""
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, editing_agent_config, mock_connections):
        """Test agent initializes correctly"""
        agent = EditingAgent(editing_agent_config)
        
        assert agent.config.name == "test_editing_agent"
        assert agent.config.agent_type == "editing"
        assert len(agent.active_sessions) == 0
        assert agent.editing_metrics["total_sessions"] == 0
        
        await agent.start()
        assert agent.state == AgentState.RUNNING
        
        await agent.stop()
        assert agent.state == AgentState.STOPPED
    
    @pytest.mark.asyncio
    async def test_graceful_shutdown(self, editing_agent):
        """Test graceful shutdown with active sessions"""
        # Create a test session
        session = EditingSession(
            session_id="test-001",
            document_id="doc-001",
            user_id="user-001",
            content_type=ContentType.ARTICLE,
            editing_mode=EditingMode.MODERATE,
            original_content="Test content",
            current_content="Test content"
        )
        editing_agent.active_sessions["test-001"] = session
        
        # Shutdown should archive the session
        await editing_agent.stop()
        
        assert editing_agent.state == AgentState.STOPPED
        assert len(editing_agent.active_sessions) == 0


class TestEditingSession:
    """Test editing session management"""
    
    @pytest.mark.asyncio
    async def test_start_editing_session(self, editing_agent):
        """Test starting a new editing session"""
        payload = {
            "document_id": "doc-123",
            "user_id": "user-456",
            "content": "This is a test document with some errors.",
            "content_type": "article",
            "editing_mode": "moderate"
        }
        
        result = await editing_agent._start_editing_session(payload)
        
        assert "session_id" in result
        assert result["session_created"] is True
        assert "content_analysis" in result
        assert "initial_suggestions" in result
        
        session_id = result["session_id"]
        assert session_id in editing_agent.active_sessions
        
        session = editing_agent.active_sessions[session_id]
        assert session.document_id == "doc-123"
        assert session.user_id == "user-456"
        assert session.content_type == ContentType.ARTICLE
        assert session.editing_mode == EditingMode.MODERATE
    
    @pytest.mark.asyncio
    async def test_get_session_status(self, editing_agent):
        """Test getting session status"""
        # Create a session
        session = EditingSession(
            session_id="test-002",
            document_id="doc-002",
            user_id="user-002",
            content_type=ContentType.EMAIL,
            editing_mode=EditingMode.LIGHT,
            original_content="Test email",
            current_content="Test email"
        )
        editing_agent.active_sessions["test-002"] = session
        
        result = await editing_agent._get_session_status({
            "session_id": "test-002"
        })
        
        assert "session" in result
        assert result["session"]["session_id"] == "test-002"
        assert "pending_suggestions" in result
        assert "applied_edits" in result
    
    @pytest.mark.asyncio
    async def test_close_session(self, editing_agent):
        """Test closing a session"""
        # Create a session
        session = EditingSession(
            session_id="test-003",
            document_id="doc-003",
            user_id="user-003",
            content_type=ContentType.REPORT,
            editing_mode=EditingMode.HEAVY,
            original_content="Test report",
            current_content="Test report improved"
        )
        editing_agent.active_sessions["test-003"] = session
        
        result = await editing_agent._close_session({
            "session_id": "test-003"
        })
        
        assert result["status"] == "session_closed"
        assert result["session_id"] == "test-003"
        assert "test-003" not in editing_agent.active_sessions


class TestContentAnalysis:
    """Test content analysis functionality"""
    
    @pytest.mark.asyncio
    async def test_analyze_content_basic(self, editing_agent):
        """Test basic content analysis"""
        payload = {
            "content": "This is a test. It has multiple sentences. And paragraphs too.",
            "content_type": "article"
        }
        
        result = await editing_agent._analyze_content(payload)
        
        assert "analysis" in result
        analysis = result["analysis"]
        
        assert "readability" in analysis
        assert "sentiment" in analysis
        assert "structure" in analysis
        assert "issues" in analysis
        
        # Check structure metrics
        structure = analysis["structure"]
        assert structure["word_count"] > 0
        assert structure["sentence_count"] > 0
        assert structure["paragraph_count"] > 0
    
    @pytest.mark.asyncio
    async def test_analyze_empty_content(self, editing_agent):
        """Test analyzing empty content"""
        result = await editing_agent._analyze_content({
            "content": "",
            "content_type": "article"
        })
        
        assert "error" in result["analysis"]
    
    @pytest.mark.asyncio
    async def test_tone_analysis(self, editing_agent):
        """Test tone analysis"""
        formal_text = "Dear Sir, I hereby submit this proposal. Therefore, we recommend proceeding."
        tone = await editing_agent._analyze_tone(formal_text)
        
        assert "formal" in tone
        assert "professional" in tone
        assert tone["formal"] > 0
        
        casual_text = "Hey there! LOL, this is so cool. BTW, wanna grab coffee?"
        tone = await editing_agent._analyze_tone(casual_text)
        
        assert tone["casual"] > 0
        assert tone["friendly"] > 0
    
    @pytest.mark.asyncio
    async def test_content_specific_analysis(self, editing_agent):
        """Test content-type specific analysis"""
        # Marketing content
        marketing_result = await editing_agent._analyze_content_specific(
            "Buy now! Sign up today and get started immediately!",
            "marketing"
        )
        assert "call_to_actions_found" in marketing_result
        assert marketing_result["call_to_actions_found"] > 0
        
        # Technical content
        technical_result = await editing_agent._analyze_content_specific(
            "```python\nprint('hello')\n```",
            "technical"
        )
        assert "code_block_count" in technical_result
        
        # Email content
        email_result = await editing_agent._analyze_content_specific(
            "Dear John,\n\nThank you for your email.\n\nBest regards,\nJane",
            "email"
        )
        assert "has_greeting" in email_result
        assert "has_closing" in email_result


class TestSuggestions:
    """Test suggestion generation and application"""
    
    @pytest.mark.asyncio
    async def test_generate_suggestions(self, editing_agent):
        """Test generating edit suggestions"""
        # Create a session first
        session = EditingSession(
            session_id="test-004",
            document_id="doc-004",
            user_id="user-004",
            content_type=ContentType.ARTICLE,
            editing_mode=EditingMode.MODERATE,
            original_content="This is a very very very long sentence that should probably be split into multiple shorter sentences for better readability and clarity.",
            current_content="This is a very very very long sentence that should probably be split into multiple shorter sentences for better readability and clarity."
        )
        editing_agent.active_sessions["test-004"] = session
        
        result = await editing_agent._generate_suggestions({
            "session_id": "test-004",
            "content": session.current_content,
            "editing_mode": "moderate",
            "content_type": "article"
        })
        
        assert "suggestions" in result
        assert "suggestion_count" in result
        assert isinstance(result["suggestions"], list)
    
    @pytest.mark.asyncio
    async def test_apply_edits(self, editing_agent):
        """Test applying edit suggestions"""
        # Create a session with suggestions
        suggestion = EditSuggestion(
            id="sugg-001",
            edit_type=EditType.GRAMMAR,
            original_text="teh",
            suggested_text="the",
            reason="Spelling error",
            confidence=0.95,
            position=(0, 3)
        )
        
        session = EditingSession(
            session_id="test-005",
            document_id="doc-005",
            user_id="user-005",
            content_type=ContentType.ARTICLE,
            editing_mode=EditingMode.MODERATE,
            original_content="teh quick brown fox",
            current_content="teh quick brown fox"
        )
        session.suggestions.append(suggestion)
        editing_agent.active_sessions["test-005"] = session
        
        result = await editing_agent._apply_edits({
            "session_id": "test-005",
            "edit_ids": ["sugg-001"]
        })
        
        assert result["applied_count"] == 1
        assert "the quick brown fox" in result["new_content"]
        assert len(session.applied_edits) == 1
        assert len(session.suggestions) == 0


class TestGrammarCheck:
    """Test grammar checking functionality"""
    
    @pytest.mark.asyncio
    async def test_check_grammar_basic(self, editing_agent):
        """Test basic grammar checking"""
        # Mock grammar tool if not initialized
        if not editing_agent.grammar_tool:
            mock_tool = MagicMock()
            mock_match = MagicMock()
            mock_match.message = "Test error"
            mock_match.replacements = ["correction"]
            mock_match.offset = 0
            mock_match.errorLength = 5
            mock_match.context = "context"
            mock_match.ruleId = "TEST_RULE"
            mock_match.category = "Grammar"
            mock_tool.check.return_value = [mock_match]
            editing_agent.grammar_tool = mock_tool
        
        result = await editing_agent._check_grammar({
            "content": "This is a test sentance."
        })
        
        assert "issues" in result
        assert "issue_count" in result
    
    @pytest.mark.asyncio
    async def test_grammar_check_no_tool(self, editing_agent):
        """Test grammar check when tool not initialized"""
        editing_agent.grammar_tool = None
        
        result = await editing_agent._check_grammar({
            "content": "Test content"
        })
        
        assert "error" in result or "issues" in result


class TestCollaborativeEditing:
    """Test collaborative editing features"""
    
    @pytest.mark.asyncio
    async def test_collaborative_edit_insert(self, editing_agent):
        """Test inserting text in collaborative mode"""
        session = EditingSession(
            session_id="test-006",
            document_id="doc-006",
            user_id="user-006",
            content_type=ContentType.ARTICLE,
            editing_mode=EditingMode.COLLABORATIVE,
            original_content="Hello world",
            current_content="Hello world"
        )
        editing_agent.active_sessions["test-006"] = session
        
        result = await editing_agent._collaborative_edit({
            "session_id": "test-006",
            "user_id": "user-007",
            "change_type": "insert",
            "position": 6,
            "text": "beautiful "
        })
        
        assert result["status"] == "change_applied"
        assert "beautiful" in session.current_content
        assert session.current_content == "Hello beautiful world"
    
    @pytest.mark.asyncio
    async def test_collaborative_edit_delete(self, editing_agent):
        """Test deleting text in collaborative mode"""
        session = EditingSession(
            session_id="test-007",
            document_id="doc-007",
            user_id="user-007",
            content_type=ContentType.ARTICLE,
            editing_mode=EditingMode.COLLABORATIVE,
            original_content="Hello wonderful world",
            current_content="Hello wonderful world"
        )
        editing_agent.active_sessions["test-007"] = session
        
        result = await editing_agent._collaborative_edit({
            "session_id": "test-007",
            "user_id": "user-008",
            "change_type": "delete",
            "position": (6, 16),  # Delete "wonderful "
            "text": ""
        })
        
        assert result["status"] == "change_applied"
        assert "wonderful" not in session.current_content
    
    @pytest.mark.asyncio
    async def test_collaborative_edit_replace(self, editing_agent):
        """Test replacing text in collaborative mode"""
        session = EditingSession(
            session_id="test-008",
            document_id="doc-008",
            user_id="user-008",
            content_type=ContentType.ARTICLE,
            editing_mode=EditingMode.COLLABORATIVE,
            original_content="Hello world",
            current_content="Hello world"
        )
        editing_agent.active_sessions["test-008"] = session
        
        result = await editing_agent._collaborative_edit({
            "session_id": "test-008",
            "user_id": "user-009",
            "change_type": "replace",
            "position": (0, 5),
            "text": "Greetings"
        })
        
        assert result["status"] == "change_applied"
        assert session.current_content == "Greetings world"


class TestVersionControl:
    """Test version control features"""
    
    @pytest.mark.asyncio
    async def test_save_version(self, editing_agent):
        """Test saving a version"""
        session = EditingSession(
            session_id="test-009",
            document_id="doc-009",
            user_id="user-009",
            content_type=ContentType.REPORT,
            editing_mode=EditingMode.MODERATE,
            original_content="Version 1",
            current_content="Version 1 updated"
        )
        editing_agent.active_sessions["test-009"] = session
        
        result = await editing_agent._version_control({
            "session_id": "test-009",
            "operation": "save_version",
            "message": "First update"
        })
        
        assert result["status"] == "version_saved"
        assert "version_id" in result
        assert len(session.version_history) == 1
    
    @pytest.mark.asyncio
    async def test_get_version_history(self, editing_agent):
        """Test getting version history"""
        session = EditingSession(
            session_id="test-010",
            document_id="doc-010",
            user_id="user-010",
            content_type=ContentType.PROPOSAL,
            editing_mode=EditingMode.HEAVY,
            original_content="Original",
            current_content="Current"
        )
        session.version_history = [
            {"version_id": "v1", "timestamp": 1000, "content": "Version 1"},
            {"version_id": "v2", "timestamp": 2000, "content": "Version 2"}
        ]
        editing_agent.active_sessions["test-010"] = session
        
        result = await editing_agent._version_control({
            "session_id": "test-010",
            "operation": "get_history"
        })
        
        assert "version_history" in result
        assert len(result["version_history"]) == 2
    
    @pytest.mark.asyncio
    async def test_revert_version(self, editing_agent):
        """Test reverting to a previous version"""
        session = EditingSession(
            session_id="test-011",
            document_id="doc-011",
            user_id="user-011",
            content_type=ContentType.ARTICLE,
            editing_mode=EditingMode.MODERATE,
            original_content="Original",
            current_content="Current version"
        )
        session.version_history = [
            {"version_id": "v1", "timestamp": 1000, "content": "Previous version"}
        ]
        editing_agent.active_sessions["test-011"] = session
        
        result = await editing_agent._version_control({
            "session_id": "test-011",
            "operation": "revert",
            "version_id": "v1"
        })
        
        assert result["status"] == "reverted"
        assert session.current_content == "Previous version"


class TestTaskHandling:
    """Test task routing and handling"""
    
    @pytest.mark.asyncio
    async def test_handle_task_routing(self, editing_agent):
        """Test that tasks are routed correctly"""
        task = TaskRequest(
            task_id="task-001",
            task_type="analyze_content",
            payload={"content": "Test content", "content_type": "article"},
            priority=Priority.MEDIUM
        )
        
        result = await editing_agent._handle_task(task)
        
        assert result["status"] == "success"
        assert result["task_id"] == "task-001"
        assert "result" in result
    
    @pytest.mark.asyncio
    async def test_handle_invalid_task(self, editing_agent):
        """Test handling of invalid task types"""
        task = TaskRequest(
            task_id="task-002",
            task_type="invalid_task_type",
            payload={},
            priority=Priority.LOW
        )
        
        result = await editing_agent._handle_task(task)
        
        # Should fall back to parent handler or return error
        assert "status" in result


class TestMetrics:
    """Test metrics collection and reporting"""
    
    @pytest.mark.asyncio
    async def test_metrics_collection(self, editing_agent):
        """Test that metrics are collected correctly"""
        initial_sessions = editing_agent.editing_metrics["total_sessions"]
        
        # Create a session
        await editing_agent._start_editing_session({
            "content": "Test",
            "content_type": "article",
            "editing_mode": "moderate"
        })
        
        assert editing_agent.editing_metrics["total_sessions"] == initial_sessions + 1
    
    @pytest.mark.asyncio
    async def test_get_agent_metrics(self, editing_agent):
        """Test getting agent metrics"""
        metrics = editing_agent._get_agent_metrics()
        
        assert "editing_metrics" in metrics
        assert "tools_status" in metrics
        assert "total_sessions" in metrics["editing_metrics"]
        assert "active_sessions" in metrics["editing_metrics"]


# Integration tests
class TestIntegration:
    """Integration tests for complete workflows"""
    
    @pytest.mark.asyncio
    async def test_complete_editing_workflow(self, editing_agent):
        """Test a complete editing workflow from start to finish"""
        # 1. Start session
        start_result = await editing_agent._start_editing_session({
            "document_id": "doc-integration",
            "user_id": "user-integration",
            "content": "This is a test document. It has some errrors.",
            "content_type": "article",
            "editing_mode": "moderate"
        })
        
        session_id = start_result["session_id"]
        assert session_id in editing_agent.active_sessions
        
        # 2. Generate suggestions (already done in start)
        suggestions = start_result["initial_suggestions"]
        assert len(suggestions) >= 0
        
        # 3. Apply some edits if suggestions exist
        if suggestions:
            edit_ids = [suggestions[0]["id"]]
            apply_result = await editing_agent._apply_edits({
                "session_id": session_id,
                "edit_ids": edit_ids
            })
            assert apply_result["applied_count"] > 0
        
        # 4. Save version
        version_result = await editing_agent._version_control({
            "session_id": session_id,
            "operation": "save_version",
            "message": "First draft"
        })
        assert version_result["status"] == "version_saved"
        
        # 5. Get session status
        status_result = await editing_agent._get_session_status({
            "session_id": session_id
        })
        assert "session" in status_result
        
        # 6. Close session
        close_result = await editing_agent._close_session({
            "session_id": session_id
        })
        assert close_result["status"] == "session_closed"
        assert session_id not in editing_agent.active_sessions


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])