# Editing Agent v2.0 - Production Setup Guide

## Overview

The Enhanced Editing Agent is a production-ready service that provides:
- Grammar and spelling correction
- Style improvement and readability optimization
- Content analysis with detailed metrics
- Real-time collaborative editing
- Version control and history tracking
- Multi-language support (extensible)

## Quick Start

### 1. Dependencies

```bash
# Install Python dependencies
pip install -r requirements_editing.txt
```

**requirements_editing.txt:**
```txt
# Core dependencies (from base requirements)
nats-py>=2.6.0
asyncpg>=0.29.0
redis>=5.0.0
aioredis>=2.0.1
pydantic>=2.0.0

# Language processing
spacy>=3.5.0
nltk>=3.8.0
textstat>=0.7.3
language-tool-python>=2.7.1

# Download spaCy model
# python -m spacy download en_core_web_sm

# Optional but recommended
opentelemetry-api>=1.20.0
opentelemetry-sdk>=1.20.0
prometheus-client>=0.19.0
```

### 2. Database Setup

Run the following SQL to create required tables:

```sql
-- Editing sessions table
CREATE TABLE IF NOT EXISTS editing_sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    document_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    content_type VARCHAR(50) NOT NULL,
    editing_mode VARCHAR(50) NOT NULL,
    original_content TEXT NOT NULL,
    current_content TEXT NOT NULL,
    version_count INTEGER DEFAULT 0,
    suggestions_count INTEGER DEFAULT 0,
    applied_edits_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_document_id (document_id),
    INDEX idx_user_id (user_id),
    INDEX idx_updated_at (updated_at)
);

-- Archived sessions table
CREATE TABLE IF NOT EXISTS editing_sessions_archive (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    document_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    content_type VARCHAR(50) NOT NULL,
    editing_mode VARCHAR(50) NOT NULL,
    original_content TEXT NOT NULL,
    final_content TEXT NOT NULL,
    suggestions_generated INTEGER DEFAULT 0,
    suggestions_accepted INTEGER DEFAULT 0,
    version_count INTEGER DEFAULT 0,
    created_at TIMESTAMP NOT NULL,
    closed_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_session_id (session_id),
    INDEX idx_document_id (document_id),
    INDEX idx_closed_at (closed_at)
);

-- Editing suggestions table (optional, for detailed tracking)
CREATE TABLE IF NOT EXISTS editing_suggestions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    suggestion_id VARCHAR(255) NOT NULL,
    edit_type VARCHAR(50) NOT NULL,
    original_text TEXT,
    suggested_text TEXT,
    reason TEXT,
    confidence FLOAT,
    position_start INTEGER,
    position_end INTEGER,
    applied BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    
    FOREIGN KEY (session_id) REFERENCES editing_sessions(session_id),
    INDEX idx_session_id (session_id),
    INDEX idx_applied (applied)
);

-- Content analysis results (optional)
CREATE TABLE IF NOT EXISTS content_analysis (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255),
    content_hash VARCHAR(64) NOT NULL,
    readability_score FLOAT,
    grade_level FLOAT,
    sentiment_score FLOAT,
    word_count INTEGER,
    sentence_count INTEGER,
    paragraph_count INTEGER,
    total_issues INTEGER,
    analysis_data JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_session_id (session_id),
    INDEX idx_content_hash (content_hash),
    INDEX idx_created_at (created_at)
);
```

### 3. Environment Configuration

Create a `.env` file:

```env
# Agent Configuration
AGENT_ID=editing-001
AGENT_NAME=editing_agent
AGENT_TYPE=editing
AGENT_VERSION=2.0.0

# Connection URLs
NATS_URL=nats://localhost:4222
POSTGRES_URL=postgresql://user:password@localhost:5432/agentdb
REDIS_URL=redis://localhost:6379

# Performance Settings
MAX_CONCURRENT_TASKS=100
REQUEST_TIMEOUT_SECONDS=30
SHUTDOWN_TIMEOUT_SECONDS=30

# Monitoring
STATUS_PUBLISH_INTERVAL=30
HEARTBEAT_INTERVAL=10
LOG_LEVEL=INFO

# Editing-specific settings
SESSION_TIMEOUT_HOURS=24
ANALYSIS_INTERVAL_SECONDS=60
MAX_CONTENT_LENGTH=100000
```

### 4. Running the Agent

```bash
# Direct execution
python editing_agent.py

# With Docker
docker build -t editing-agent:2.0 .
docker run -d --name editing-agent \
  --env-file .env \
  editing-agent:2.0

# With docker-compose
docker-compose up -d editing-agent
```

## API Usage Examples

### Starting an Editing Session

```python
import asyncio
import nats
import json

async def start_editing():
    nc = await nats.connect("nats://localhost:4222")
    
    request = {
        "task_id": "edit-001",
        "task_type": "start_editing_session",
        "payload": {
            "document_id": "doc-123",
            "user_id": "user-456",
            "content": "This is a test document with some errrors.",
            "content_type": "article",
            "editing_mode": "moderate"
        },
        "priority": "medium"
    }
    
    response = await nc.request(
        "agent.editing_agent.task",
        json.dumps(request).encode(),
        timeout=10
    )
    
    result = json.loads(response.data.decode())
    print("Session created:", result["result"]["session_id"])
    print("Analysis:", result["result"]["content_analysis"])
    print("Suggestions:", len(result["result"]["initial_suggestions"]))
    
    await nc.close()

asyncio.run(start_editing())
```

### Analyzing Content

```python
async def analyze_content():
    nc = await nats.connect("nats://localhost:4222")
    
    request = {
        "task_id": "analyze-001",
        "task_type": "analyze_content",
        "payload": {
            "content": "Your content here...",
            "content_type": "marketing"
        },
        "priority": "high"
    }
    
    response = await nc.request(
        "agent.editing_agent.task",
        json.dumps(request).encode(),
        timeout=10
    )
    
    result = json.loads(response.data.decode())
    analysis = result["result"]["analysis"]
    
    print(f"Readability Score: {analysis['readability']['score']}")
    print(f"Grade Level: {analysis['readability']['grade_level']}")
    print(f"Issues Found: {analysis['issues']['total_issues']}")
    print(f"Sentiment: {analysis['sentiment']['overall_score']}")
    
    await nc.close()

asyncio.run(analyze_content())
```

### Applying Edits

```python
async def apply_edits():
    nc = await nats.connect("nats://localhost:4222")
    
    request = {
        "task_id": "apply-001",
        "task_type": "apply_edits",
        "payload": {
            "session_id": "edit_sess_abc123",
            "edit_ids": [
                "suggestion-id-1",
                "suggestion-id-2",
                "suggestion-id-3"
            ]
        },
        "priority": "high"
    }
    
    response = await nc.request(
        "agent.editing_agent.task",
        json.dumps(request).encode(),
        timeout=10
    )
    
    result = json.loads(response.data.decode())
    print(f"Applied {result['result']['applied_count']} edits")
    print(f"New content preview: {result['result']['new_content'][:200]}")
    
    await nc.close()

asyncio.run(apply_edits())
```

### Grammar Check Only

```python
async def check_grammar():
    nc = await nats.connect("nats://localhost:4222")
    
    request = {
        "task_id": "grammar-001",
        "task_type": "check_grammar",
        "payload": {
            "content": "Their are some mistakes in this sentance."
        },
        "priority": "medium"
    }
    
    response = await nc.request(
        "agent.editing_agent.task",
        json.dumps(request).encode(),
        timeout=10
    )
    
    result = json.loads(response.data.decode())
    issues = result["result"]["issues"]
    
    for issue in issues:
        print(f"\nIssue: {issue['message']}")
        print(f"Suggestions: {', '.join(issue['replacements'][:3])}")
        print(f"Category: {issue['category']}")
    
    await nc.close()

asyncio.run(check_grammar())
```

## Task Types Reference

| Task Type | Description | Required Payload |
|-----------|-------------|------------------|
| `start_editing_session` | Create new editing session | `content`, `content_type`, `editing_mode` |
| `analyze_content` | Analyze content metrics | `content` |
| `generate_suggestions` | Generate edit suggestions | `session_id` or `content` |
| `apply_edits` | Apply selected suggestions | `session_id`, `edit_ids` |
| `check_grammar` | Grammar and spelling check | `content` |
| `improve_style` | Style improvement | `content`, `style_guide` |
| `optimize_readability` | Readability optimization | `content`, `target_grade_level` |
| `collaborative_edit` | Real-time collaborative edit | `session_id`, `change_type`, `text` |
| `version_control` | Manage versions | `session_id`, `operation` |
| `get_session_status` | Get session info | `session_id` |
| `close_session` | Close and archive session | `session_id` |

## Content Types

- `article` - Blog posts, articles
- `email` - Email messages
- `proposal` - Business proposals
- `report` - Reports and documents
- `creative` - Creative writing
- `technical` - Technical documentation
- `marketing` - Marketing copy
- `academic` - Academic papers

## Editing Modes

- `light` - Minor corrections (grammar, spelling only)
- `moderate` - Grammar + clarity improvements
- `heavy` - Significant restructuring and rewriting
- `collaborative` - Track changes mode for team editing