-- Database Initialization Script for Editing Agent v2.0
-- This script should be placed in ./init-db/ directory

-- ============================================
-- Agent Status and Monitoring Tables
-- ============================================

-- Agent status tracking table
CREATE TABLE IF NOT EXISTS agent_status (
    agent_id VARCHAR(255) PRIMARY KEY,
    agent_name VARCHAR(255) NOT NULL,
    agent_type VARCHAR(100) NOT NULL,
    state VARCHAR(50) NOT NULL,
    last_heartbeat TIMESTAMP NOT NULL DEFAULT NOW(),
    uptime_seconds FLOAT DEFAULT 0,
    metrics JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_status_type ON agent_status(agent_type);
CREATE INDEX IF NOT EXISTS idx_agent_status_heartbeat ON agent_status(last_heartbeat);

-- Agent metrics history table
CREATE TABLE IF NOT EXISTS agent_metrics_history (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(255) NOT NULL,
    messages_processed INTEGER DEFAULT 0,
    messages_failed INTEGER DEFAULT 0,
    tasks_completed INTEGER DEFAULT 0,
    tasks_failed INTEGER DEFAULT 0,
    avg_processing_time_ms FLOAT DEFAULT 0,
    recorded_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_metrics_agent_time ON agent_metrics_history(agent_id, recorded_at);

-- Agent connection states table
CREATE TABLE IF NOT EXISTS agent_connections (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(255) NOT NULL,
    service_name VARCHAR(100) NOT NULL,
    connection_state VARCHAR(50) NOT NULL,
    last_connected TIMESTAMP,
    last_disconnected TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_agent_connection ON agent_connections(agent_id, service_name);

-- ============================================
-- Editing Agent Specific Tables
-- ============================================

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
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_editing_sessions_document ON editing_sessions(document_id);
CREATE INDEX IF NOT EXISTS idx_editing_sessions_user ON editing_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_editing_sessions_updated ON editing_sessions(updated_at);

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
    closed_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_archived_sessions_id ON editing_sessions_archive(session_id);
CREATE INDEX IF NOT EXISTS idx_archived_sessions_document ON editing_sessions_archive(document_id);
CREATE INDEX IF NOT EXISTS idx_archived_sessions_closed ON editing_sessions_archive(closed_at);

-- Editing suggestions table
CREATE TABLE IF NOT EXISTS editing_suggestions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    suggestion_id VARCHAR(255) NOT NULL UNIQUE,
    edit_type VARCHAR(50) NOT NULL,
    original_text TEXT,
    suggested_text TEXT,
    reason TEXT,
    confidence FLOAT,
    position_start INTEGER,
    position_end INTEGER,
    applied BOOLEAN DEFAULT FALSE,
    applied_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_suggestions_session ON editing_suggestions(session_id);
CREATE INDEX IF NOT EXISTS idx_suggestions_applied ON editing_suggestions(applied);
CREATE INDEX IF NOT EXISTS idx_suggestions_created ON editing_suggestions(created_at);

-- Content analysis results table
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
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_analysis_session ON content_analysis(session_id);
CREATE INDEX IF NOT EXISTS idx_analysis_hash ON content_analysis(content_hash);
CREATE INDEX IF NOT EXISTS idx_analysis_created ON content_analysis(created_at);

-- Version history table
CREATE TABLE IF NOT EXISTS editing_versions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    version_id VARCHAR(255) NOT NULL UNIQUE,
    version_number INTEGER NOT NULL,
    content TEXT NOT NULL,
    user_id VARCHAR(255),
    change_description TEXT,
    applied_edits JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_versions_session ON editing_versions(session_id);
CREATE INDEX IF NOT EXISTS idx_versions_created ON editing_versions(created_at);

-- Collaborative editing events table
CREATE TABLE IF NOT EXISTS collaborative_events (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    position_start INTEGER,
    position_end INTEGER,
    text_content TEXT,
    event_data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_collab_session ON collaborative_events(session_id);
CREATE INDEX IF NOT EXISTS idx_collab_user ON collaborative_events(user_id);
CREATE INDEX IF NOT EXISTS idx_collab_created ON collaborative_events(created_at);

-- ============================================
-- Performance Optimization
-- ============================================

-- Partitioning for large tables (PostgreSQL 10+)
-- Partition archived sessions by month
CREATE TABLE IF NOT EXISTS editing_sessions_archive_partitioned (
    LIKE editing_sessions_archive INCLUDING ALL
) PARTITION BY RANGE (closed_at);

-- Create partitions for current and next 12 months
DO $$
DECLARE
    start_date DATE := DATE_TRUNC('month', CURRENT_DATE);
    end_date DATE;
    partition_name TEXT;
BEGIN
    FOR i IN 0..12 LOOP
        end_date := start_date + INTERVAL '1 month';
        partition_name := 'editing_sessions_archive_' || TO_CHAR(start_date, 'YYYY_MM');
        
        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS %I PARTITION OF editing_sessions_archive_partitioned
             FOR VALUES FROM (%L) TO (%L)',
            partition_name, start_date, end_date
        );
        
        start_date := end_date;
    END LOOP;
END $$;

-- ============================================
-- Functions and Triggers
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for editing_sessions
CREATE TRIGGER update_editing_sessions_updated_at
    BEFORE UPDATE ON editing_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for agent_status
CREATE TRIGGER update_agent_status_updated_at
    BEFORE UPDATE ON agent_status
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to archive old sessions
CREATE OR REPLACE FUNCTION archive_old_sessions(days_old INTEGER DEFAULT 7)
RETURNS INTEGER AS $$
DECLARE
    archived_count INTEGER;
BEGIN
    -- Move old sessions to archive
    INSERT INTO editing_sessions_archive (
        session_id, document_id, user_id, content_type, editing_mode,
        original_content, final_content, suggestions_generated,
        suggestions_accepted, version_count, created_at, closed_at
    )
    SELECT 
        session_id, document_id, user_id, content_type, editing_mode,
        original_content, current_content, suggestions_count,
        applied_edits_count, version_count, created_at, NOW()
    FROM editing_sessions
    WHERE updated_at < NOW() - (days_old || ' days')::INTERVAL;
    
    GET DIAGNOSTICS archived_count = ROW_COUNT;
    
    -- Delete from active sessions
    DELETE FROM editing_sessions
    WHERE updated_at < NOW() - (days_old || ' days')::INTERVAL;
    
    RETURN archived_count;
END;
$$ LANGUAGE plpgsql;

-- Function to clean old metrics
CREATE OR REPLACE FUNCTION clean_old_metrics(days_old INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM agent_metrics_history
    WHERE recorded_at < NOW() - (days_old || ' days')::INTERVAL;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to get session statistics
CREATE OR REPLACE FUNCTION get_session_stats(
    start_date TIMESTAMP DEFAULT NOW() - INTERVAL '30 days',
    end_date TIMESTAMP DEFAULT NOW()
)
RETURNS TABLE(
    total_sessions BIGINT,
    avg_suggestions INTEGER,
    avg_accepted INTEGER,
    acceptance_rate NUMERIC,
    by_content_type JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT as total_sessions,
        AVG(suggestions_generated)::INTEGER as avg_suggestions,
        AVG(suggestions_accepted)::INTEGER as avg_accepted,
        CASE 
            WHEN SUM(suggestions_generated) > 0 
            THEN ROUND((SUM(suggestions_accepted)::NUMERIC / SUM(suggestions_generated)) * 100, 2)
            ELSE 0
        END as acceptance_rate,
        jsonb_object_agg(
            content_type, 
            count
        ) as by_content_type
    FROM (
        SELECT 
            content_type,
            COUNT(*) as count,
            suggestions_generated,
            suggestions_accepted
        FROM editing_sessions_archive
        WHERE closed_at BETWEEN start_date AND end_date
        GROUP BY content_type, suggestions_generated, suggestions_accepted
    ) subq
    GROUP BY content_type;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- Views for Monitoring
-- ============================================

-- Active sessions view
CREATE OR REPLACE VIEW v_active_sessions AS
SELECT 
    s.session_id,
    s.document_id,
    s.user_id,
    s.content_type,
    s.editing_mode,
    s.suggestions_count,
    s.applied_edits_count,
    s.version_count,
    EXTRACT(EPOCH FROM (NOW() - s.updated_at)) as idle_seconds,
    s.created_at,
    s.updated_at
FROM editing_sessions s
ORDER BY s.updated_at DESC;

-- Session performance view
CREATE OR REPLACE VIEW v_session_performance AS
SELECT 
    DATE_TRUNC('day', closed_at) as date,
    content_type,
    editing_mode,
    COUNT(*) as session_count,
    AVG(suggestions_generated) as avg_suggestions,
    AVG(suggestions_accepted) as avg_accepted,
    CASE 
        WHEN SUM(suggestions_generated) > 0 
        THEN ROUND((SUM(suggestions_accepted)::NUMERIC / SUM(suggestions_generated)) * 100, 2)
        ELSE 0
    END as acceptance_rate,
    AVG(EXTRACT(EPOCH FROM (closed_at - created_at))) as avg_duration_seconds
FROM editing_sessions_archive
GROUP BY DATE_TRUNC('day', closed_at), content_type, editing_mode
ORDER BY date DESC;

-- Agent health view
CREATE OR REPLACE VIEW v_agent_health AS
SELECT 
    a.agent_id,
    a.agent_name,
    a.agent_type,
    a.state,
    EXTRACT(EPOCH FROM (NOW() - a.last_heartbeat)) as seconds_since_heartbeat,
    a.uptime_seconds,
    ac.nats_state,
    ac.postgres_state,
    ac.redis_state
FROM agent_status a
LEFT JOIN (
    SELECT 
        agent_id,
        MAX(CASE WHEN service_name = 'nats' THEN connection_state END) as nats_state,
        MAX(CASE WHEN service_name = 'postgres' THEN connection_state END) as postgres_state,
        MAX(CASE WHEN service_name = 'redis' THEN connection_state END) as redis_state
    FROM agent_connections
    GROUP BY agent_id
) ac ON a.agent_id = ac.agent_id;

-- ============================================
-- Initial Data
-- ============================================

-- Insert default configuration if needed
-- (Add any default data here)

-- ============================================
-- Grants and Permissions
-- ============================================

-- Grant necessary permissions to agent user
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO agent;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO agent;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO agent;

-- ============================================
-- Maintenance
-- ============================================

-- Schedule regular maintenance (use pg_cron or external scheduler)
-- Example: Archive sessions older than 7 days daily
-- SELECT cron.schedule('archive-sessions', '0 2 * * *', 'SELECT archive_old_sessions(7)');

-- Example: Clean old metrics older than 90 days weekly
-- SELECT cron.schedule('clean-metrics', '0 3 * * 0', 'SELECT clean_old_metrics(90)');

COMMENT ON TABLE editing_sessions IS 'Active editing sessions';
COMMENT ON TABLE editing_sessions_archive IS 'Archived editing sessions for historical analysis';
COMMENT ON TABLE editing_suggestions IS 'Individual edit suggestions generated during sessions';
COMMENT ON TABLE content_analysis IS 'Content analysis results and metrics';
COMMENT ON TABLE editing_versions IS 'Version history for editing sessions';
COMMENT ON TABLE collaborative_events IS 'Real-time collaborative editing events';

-- End of initialization script