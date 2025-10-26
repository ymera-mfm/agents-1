-- Production Database Schema for Agent Engines
-- Complete implementation with all tables, indexes, and functions

-- ============================================================================
-- CORE AGENTS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS agents (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) UNIQUE NOT NULL,
    agent_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'healthy' CHECK (status IN ('healthy', 'degraded', 'unhealthy', 'inactive')),
    capabilities JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    version VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP,
    heartbeat_count INTEGER DEFAULT 0
);

CREATE INDEX idx_agents_status ON agents(status);
CREATE INDEX idx_agents_type ON agents(agent_type);
CREATE INDEX idx_agents_last_seen ON agents(last_seen DESC);
CREATE UNIQUE INDEX idx_agents_agent_id ON agents(agent_id);

-- ============================================================================
-- TASK MANAGEMENT TABLES
-- ============================================================================

CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(255) UNIQUE NOT NULL,
    task_type VARCHAR(100) NOT NULL,
    priority INTEGER DEFAULT 1 CHECK (priority >= 0 AND priority <= 3),
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'timeout')),
    payload JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_type ON tasks(task_type);
CREATE INDEX idx_tasks_priority ON tasks(priority DESC);
CREATE INDEX idx_tasks_created ON tasks(created_at DESC);
CREATE UNIQUE INDEX idx_tasks_task_id ON tasks(task_id);

CREATE TABLE IF NOT EXISTS task_results (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(255) UNIQUE NOT NULL,
    agent_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL CHECK (status IN ('success', 'failed', 'timeout', 'error')),
    result JSONB,
    error TEXT,
    error_traceback TEXT,
    execution_time_ms FLOAT NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    retry_count INTEGER DEFAULT 0,
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id) ON DELETE CASCADE
);

CREATE INDEX idx_task_results_agent ON task_results(agent_id);
CREATE INDEX idx_task_results_status ON task_results(status);
CREATE INDEX idx_task_results_created ON task_results(created_at DESC);
CREATE INDEX idx_task_results_agent_time ON task_results(agent_id, created_at DESC);
CREATE UNIQUE INDEX idx_task_results_task_id ON task_results(task_id);

-- ============================================================================
-- VALIDATION ENGINE TABLES
-- ============================================================================

CREATE TABLE IF NOT EXISTS validation_rules (
    id SERIAL PRIMARY KEY,
    rule_id VARCHAR(255) UNIQUE NOT NULL,
    field VARCHAR(255) NOT NULL,
    rule_type VARCHAR(50) NOT NULL,
    condition TEXT NOT NULL,
    error_message TEXT NOT NULL,
    severity VARCHAR(20) DEFAULT 'error' CHECK (severity IN ('error', 'warning')),
    enabled BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_validation_rules_field ON validation_rules(field);
CREATE INDEX idx_validation_rules_enabled ON validation_rules(enabled);
CREATE UNIQUE INDEX idx_validation_rules_rule_id ON validation_rules(rule_id);

CREATE TABLE IF NOT EXISTS validation_results (
    id SERIAL PRIMARY KEY,
    validation_id VARCHAR(255) UNIQUE NOT NULL,
    agent_id VARCHAR(255) NOT NULL,
    valid BOOLEAN NOT NULL,
    passed_checks INTEGER NOT NULL,
    failed_checks INTEGER NOT NULL,
    execution_time_ms FLOAT NOT NULL,
    errors JSONB DEFAULT '[]',
    warnings JSONB DEFAULT '[]',
    payload_size_bytes INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id) ON DELETE CASCADE
);

CREATE INDEX idx_validation_results_agent ON validation_results(agent_id);
CREATE INDEX idx_validation_results_valid ON validation_results(valid);
CREATE INDEX idx_validation_results_created ON validation_results(created_at DESC);
CREATE UNIQUE INDEX idx_validation_results_validation_id ON validation_results(validation_id);

CREATE TABLE IF NOT EXISTS validation_metrics (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(255) NOT NULL,
    total_validations INTEGER NOT NULL,
    passed INTEGER NOT NULL,
    failed INTEGER NOT NULL,
    avg_execution_time_ms FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id) ON DELETE CASCADE
);

CREATE INDEX idx_validation_metrics_agent ON validation_metrics(agent_id);
CREATE INDEX idx_validation_metrics_created ON validation_metrics(created_at DESC);

-- ============================================================================
-- TRANSFORMATION ENGINE TABLES
-- ============================================================================

CREATE TABLE IF NOT EXISTS transformation_pipelines (
    id SERIAL PRIMARY KEY,
    pipeline_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    steps JSONB NOT NULL,
    enabled BOOLEAN DEFAULT true,
    version INTEGER DEFAULT 1,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_transformation_pipelines_enabled ON transformation_pipelines(enabled);
CREATE UNIQUE INDEX idx_transformation_pipelines_pipeline_id ON transformation_pipelines(pipeline_id);

CREATE TABLE IF NOT EXISTS transformation_results (
    id SERIAL PRIMARY KEY,
    transform_id VARCHAR(255) UNIQUE NOT NULL,
    agent_id VARCHAR(255) NOT NULL,
    pipeline_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL CHECK (status IN ('success', 'error')),
    record_count INTEGER,
    execution_time_ms FLOAT NOT NULL,
    steps_completed INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id) ON DELETE CASCADE,
    FOREIGN KEY (pipeline_id) REFERENCES transformation_pipelines(pipeline_id) ON DELETE CASCADE
);

CREATE INDEX idx_transformation_results_agent ON transformation_results(agent_id);
CREATE INDEX idx_transformation_results_pipeline ON transformation_results(pipeline_id);
CREATE INDEX idx_transformation_results_created ON transformation_results(created_at DESC);
CREATE UNIQUE INDEX idx_transformation_results_transform_id ON transformation_results(transform_id);

-- ============================================================================
-- ROUTING & DECISION TABLES
-- ============================================================================

CREATE TABLE IF NOT EXISTS decision_history (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(255) UNIQUE NOT NULL,
    task_type VARCHAR(100) NOT NULL,
    selected_agent VARCHAR(255),
    confidence FLOAT NOT NULL,
    reasoning TEXT,
    context_data JSONB DEFAULT '{}',
    system_state JSONB DEFAULT '{}',
    execution_time_ms FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (selected_agent) REFERENCES agents(agent_id) ON DELETE SET NULL
);

CREATE INDEX idx_decision_history_task_type ON decision_history(task_type);
CREATE INDEX idx_decision_history_agent ON decision_history(selected_agent);
CREATE INDEX idx_decision_history_created ON decision_history(created_at DESC);
CREATE UNIQUE INDEX idx_decision_history_request_id ON decision_history(request_id);

-- ============================================================================
-- PERFORMANCE METRICS TABLES
-- ============================================================================

CREATE TABLE IF NOT EXISTS performance_metrics (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    cpu_percent FLOAT,
    memory_percent FLOAT,
    memory_available_gb FLOAT,
    disk_usage_percent FLOAT,
    disk_free_gb FLOAT,
    process_memory_mb FLOAT,
    response_time_ms FLOAT,
    queue_size INTEGER,
    active_tasks INTEGER,
    error_rate FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id) ON DELETE CASCADE
);

CREATE INDEX idx_performance_metrics_agent ON performance_metrics(agent_id);
CREATE INDEX idx_performance_metrics_timestamp ON performance_metrics(timestamp DESC);
CREATE INDEX idx_performance_metrics_created ON performance_metrics(created_at DESC);
CREATE INDEX idx_performance_metrics_agent_time ON performance_metrics(agent_id, timestamp DESC);

CREATE TABLE IF NOT EXISTS performance_alerts (
    id SERIAL PRIMARY KEY,
    alert_id VARCHAR(255) UNIQUE NOT NULL,
    agent_id VARCHAR(255) NOT NULL,
    metric VARCHAR(100) NOT NULL,
    severity VARCHAR(50) NOT NULL CHECK (severity IN ('critical', 'high', 'warning', 'info')),
    current_value FLOAT NOT NULL,
    threshold_value FLOAT NOT NULL,
    message TEXT NOT NULL,
    resolved BOOLEAN DEFAULT false,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id) ON DELETE CASCADE
);

CREATE INDEX idx_performance_alerts_agent ON performance_alerts(agent_id);
CREATE INDEX idx_performance_alerts_severity ON performance_alerts(severity);
CREATE INDEX idx_performance_alerts_resolved ON performance_alerts(resolved);
CREATE INDEX idx_performance_alerts_created ON performance_alerts(created_at DESC);
CREATE UNIQUE INDEX idx_performance_alerts_alert_id ON performance_alerts(alert_id);

-- ============================================================================
-- OPTIMIZATION & MONITORING TABLES
-- ============================================================================

CREATE TABLE IF NOT EXISTS optimizations (
    id SERIAL PRIMARY KEY,
    optimization_id VARCHAR(255) UNIQUE NOT NULL,
    agent_id VARCHAR(255) NOT NULL,
    target VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL CHECK (status IN ('success', 'error', 'pending')),
    details JSONB DEFAULT '{}',
    before_metrics JSONB,
    after_metrics JSONB,
    improvement_percent FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id) ON DELETE CASCADE
);

CREATE INDEX idx_optimizations_agent ON optimizations(agent_id);
CREATE INDEX idx_optimizations_status ON optimizations(status);
CREATE INDEX idx_optimizations_created ON optimizations(created_at DESC);
CREATE UNIQUE INDEX idx_optimizations_optimization_id ON optimizations(optimization_id);

CREATE TABLE IF NOT EXISTS circuit_breakers (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(255) NOT NULL,
    failure_count INTEGER DEFAULT 0,
    state VARCHAR(50) DEFAULT 'closed' CHECK (state IN ('closed', 'open', 'half_open')),
    last_failure TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(agent_id),
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id) ON DELETE CASCADE
);

CREATE INDEX idx_circuit_breakers_state ON circuit_breakers(state);

-- ============================================================================
-- AUDIT & LOGGING TABLES
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(255),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    details JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id) ON DELETE SET NULL
);

CREATE INDEX idx_audit_log_agent ON audit_log(agent_id);
CREATE INDEX idx_audit_log_action ON audit_log(action);
CREATE INDEX idx_audit_log_resource ON audit_log(resource_type, resource_id);
CREATE INDEX idx_audit_log_created ON audit_log(created_at DESC);

-- ============================================================================
-- FUNCTIONS & PROCEDURES
-- ============================================================================

-- Calculate agent health score
CREATE OR REPLACE FUNCTION calculate_agent_health(p_agent_id VARCHAR(255))
RETURNS FLOAT AS $$
DECLARE
    v_success_rate FLOAT;
    v_avg_response_time FLOAT;
    v_error_rate FLOAT;
    v_health_score FLOAT;
BEGIN
    SELECT 
        COALESCE(SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END)::FLOAT / 
                 NULLIF(COUNT(*), 0), 1.0),
        COALESCE(AVG(execution_time_ms), 0),
        COALESCE(SUM(CASE WHEN status != 'success' THEN 1 ELSE 0 END)::FLOAT / 
                 NULLIF(COUNT(*), 0), 0)
    INTO v_success_rate, v_avg_response_time, v_error_rate
    FROM task_results
    WHERE agent_id = p_agent_id
    AND created_at > NOW() - INTERVAL '1 hour';
    
    v_health_score := (v_success_rate * 0.5) + 
                      ((1 - MIN(v_avg_response_time / 1000.0, 1.0)) * 0.3) +
                      ((1 - v_error_rate) * 0.2);
    
    RETURN GREATEST(0.0, LEAST(1.0, v_health_score));
END;
$$ LANGUAGE plpgsql;

-- Get system statistics
CREATE OR REPLACE FUNCTION get_system_stats()
RETURNS TABLE (
    total_agents INTEGER,
    healthy_agents INTEGER,
    total_tasks_completed BIGINT,
    total_tasks_failed BIGINT,
    avg_response_time_ms FLOAT,
    system_health_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(DISTINCT agents.agent_id)::INTEGER,
        COUNT(DISTINCT CASE WHEN agents.status = 'healthy' THEN agents.agent_id END)::INTEGER,
        COUNT(CASE WHEN task_results.status = 'success' THEN 1 END),
        COUNT(CASE WHEN task_results.status = 'failed' THEN 1 END),
        AVG(task_results.execution_time_ms),
        AVG(calculate_agent_health(agents.agent_id))
    FROM agents
    LEFT JOIN task_results ON agents.agent_id = task_results.agent_id
    WHERE agents.created_at > NOW() - INTERVAL '24 hours';
END;
$$ LANGUAGE plpgsql;

-- Cleanup old data
CREATE OR REPLACE FUNCTION cleanup_old_data(p_days INTEGER DEFAULT 30)
RETURNS TABLE (
    table_name VARCHAR,
    deleted_rows INTEGER
) AS $$
BEGIN
    DELETE FROM validation_results WHERE created_at < NOW() - INTERVAL '1 day' * p_days;
    RETURN QUERY SELECT 'validation_results'::VARCHAR, ROW_COUNT()::INTEGER;
    
    DELETE FROM transformation_results WHERE created_at < NOW() - INTERVAL '1 day' * p_days;
    RETURN QUERY SELECT 'transformation_results'::VARCHAR, ROW_COUNT()::INTEGER;
    
    DELETE FROM task_results WHERE created_at < NOW() - INTERVAL '1 day' * p_days;
    RETURN QUERY SELECT 'task_results'::VARCHAR, ROW_COUNT()::INTEGER;
    
    DELETE FROM performance_metrics WHERE created_at < NOW() - INTERVAL '1 day' * p_days;
    RETURN QUERY SELECT 'performance_metrics'::VARCHAR, ROW_COUNT()::INTEGER;
    
    DELETE FROM audit_log WHERE created_at < NOW() - INTERVAL '1 day' * p_days;
    RETURN QUERY SELECT 'audit_log'::VARCHAR, ROW_COUNT()::INTEGER;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- GRANTS & PERMISSIONS
-- ============================================================================

GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO agents;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO agents;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO agents;