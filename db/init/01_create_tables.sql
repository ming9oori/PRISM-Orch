-- PostgreSQL initialization script for PRISM Orchestration Database
-- This script creates all necessary tables and indexes for the orchestration system

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create Task Management table
CREATE TABLE orch_task_manage (
    task_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL CHECK (status IN ('ACTIVE', 'COMPLETED', 'FAILED', 'CANCELLED')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    total_duration FLOAT,
    priority VARCHAR(20) NOT NULL DEFAULT 'NORMAL' CHECK (priority IN ('HIGH', 'NORMAL', 'LOW')),
    error_message TEXT
);

-- Create User Query table
CREATE TABLE orch_user_query (
    query_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES orch_task_manage(task_id) ON DELETE CASCADE,
    query_text TEXT NOT NULL,
    query_type VARCHAR(50) NOT NULL CHECK (query_type IN ('MONITORING', 'PREDICTION', 'CONTROL')),
    parsed_intent JSONB,
    user_constraints TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    response_time FLOAT
);

-- Create Execution Plan table
CREATE TABLE orch_execution_plan (
    plan_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES orch_task_manage(task_id) ON DELETE CASCADE,
    query_id UUID NOT NULL REFERENCES orch_user_query(query_id) ON DELETE CASCADE,
    task_graph JSONB NOT NULL,
    risk_assessment VARCHAR(20) CHECK (risk_assessment IN ('LOW', 'MEDIUM', 'HIGH')),
    constraint_check JSONB,
    plan_status VARCHAR(50) NOT NULL DEFAULT 'PENDING' 
        CHECK (plan_status IN ('PENDING', 'EXECUTING', 'COMPLETED', 'FAILED')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Create Agent SubTask table
CREATE TABLE orch_agent_subtask (
    subtask_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plan_id UUID NOT NULL REFERENCES orch_execution_plan(plan_id) ON DELETE CASCADE,
    agent_id VARCHAR(255) NOT NULL,
    agent_type VARCHAR(50) NOT NULL 
        CHECK (agent_type IN ('MONITORING', 'PREDICTION', 'CONTROL', 'ANALYSIS')),
    sequence_order INTEGER NOT NULL,
    input_data JSONB,
    output_data JSONB,
    subtask_status VARCHAR(50) NOT NULL DEFAULT 'QUEUED'
        CHECK (subtask_status IN ('QUEUED', 'RUNNING', 'SUCCESS', 'FAILED', 'SKIPPED')),
    error_message TEXT,
    actual_duration FLOAT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    retry_count INTEGER NOT NULL DEFAULT 0
);

-- Create Constraint Violation table
CREATE TABLE orch_constraint_violation (
    violation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plan_id UUID NOT NULL REFERENCES orch_execution_plan(plan_id) ON DELETE CASCADE,
    subtask_id UUID REFERENCES orch_agent_subtask(subtask_id) ON DELETE SET NULL,
    constraint_type VARCHAR(50) NOT NULL 
        CHECK (constraint_type IN ('RESOURCE', 'TIME', 'SAFETY', 'POLICY')),
    constraint_name VARCHAR(255) NOT NULL,
    expected_value TEXT,
    actual_value TEXT,
    severity_level VARCHAR(20) NOT NULL 
        CHECK (severity_level IN ('INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    is_blocking BOOLEAN NOT NULL DEFAULT FALSE,
    resolution_action TEXT,
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE
);

-- Create User Feedback table
CREATE TABLE orch_user_feedback (
    feedback_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES orch_task_manage(task_id) ON DELETE CASCADE,
    plan_id UUID REFERENCES orch_execution_plan(plan_id) ON DELETE SET NULL,
    feedback_type VARCHAR(50) NOT NULL 
        CHECK (feedback_type IN ('MODIFICATION', 'CANCELLATION', 'APPROVAL', 'COMPLAINT')),
    feedback_content TEXT,
    action_taken VARCHAR(50) NOT NULL 
        CHECK (action_taken IN ('APPLIED', 'IGNORED', 'DEFERRED')),
    system_response TEXT,
    impact_scope VARCHAR(50) 
        CHECK (impact_scope IN ('CURRENT_TASK', 'FUTURE_TASKS', 'GLOBAL_SETTINGS')),
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    satisfaction_score INTEGER CHECK (satisfaction_score BETWEEN 1 AND 5)
);

-- Create External Knowledge Metadata table
CREATE TABLE orch_knowledge_metadata (
    knowledge_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_title VARCHAR(500) NOT NULL,
    document_type VARCHAR(50) NOT NULL 
        CHECK (document_type IN ('RESEARCH_PAPER', 'MANUAL', 'GUIDELINE', 'FAQ')),
    content_summary TEXT,
    metadata JSONB,
    access_count INTEGER NOT NULL DEFAULT 0,
    last_accessed TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    embedder_info VARCHAR(255) NOT NULL,
    version VARCHAR(50),
    weaviate_object_id VARCHAR(255) UNIQUE  -- Reference to Weaviate object ID
);

-- Create indexes for performance optimization

-- Task table indexes
CREATE INDEX idx_task_user_status ON orch_task_manage (user_id, status);
CREATE INDEX idx_task_created_at ON orch_task_manage (created_at);
CREATE INDEX idx_task_priority_status ON orch_task_manage (priority, status);

-- User Query table indexes
CREATE INDEX idx_query_task_id ON orch_user_query (task_id);
CREATE INDEX idx_query_type ON orch_user_query (query_type);
CREATE INDEX idx_query_created_at ON orch_user_query (created_at);
CREATE INDEX idx_query_parsed_intent ON orch_user_query USING GIN (parsed_intent);

-- Execution Plan table indexes
CREATE INDEX idx_plan_task_query ON orch_execution_plan (task_id, query_id);
CREATE INDEX idx_plan_status_created ON orch_execution_plan (plan_status, created_at);
CREATE INDEX idx_plan_task_graph ON orch_execution_plan USING GIN (task_graph);
CREATE INDEX idx_plan_constraint_check ON orch_execution_plan USING GIN (constraint_check);

-- Agent SubTask table indexes
CREATE INDEX idx_subtask_plan_sequence ON orch_agent_subtask (plan_id, sequence_order);
CREATE INDEX idx_subtask_agent_status ON orch_agent_subtask (agent_id, subtask_status);
CREATE INDEX idx_subtask_status_created ON orch_agent_subtask (subtask_status, started_at);
CREATE UNIQUE INDEX idx_subtask_plan_sequence_unique ON orch_agent_subtask (plan_id, sequence_order);

-- Constraint Violation table indexes
CREATE INDEX idx_violation_plan_severity ON orch_constraint_violation (plan_id, severity_level);
CREATE INDEX idx_violation_type_detected ON orch_constraint_violation (constraint_type, detected_at);
CREATE INDEX idx_violation_blocking_unresolved ON orch_constraint_violation (is_blocking, resolved_at);

-- User Feedback table indexes
CREATE INDEX idx_feedback_task_type ON orch_user_feedback (task_id, feedback_type);
CREATE INDEX idx_feedback_submitted_processed ON orch_user_feedback (submitted_at, processed_at);
CREATE INDEX idx_feedback_satisfaction_score ON orch_user_feedback (satisfaction_score);

-- Knowledge Metadata table indexes
CREATE INDEX idx_knowledge_doc_type ON orch_knowledge_metadata (document_type);
CREATE INDEX idx_knowledge_access_count ON orch_knowledge_metadata (access_count DESC);
CREATE INDEX idx_knowledge_last_accessed ON orch_knowledge_metadata (last_accessed);
CREATE INDEX idx_knowledge_metadata ON orch_knowledge_metadata USING GIN (metadata);
CREATE INDEX idx_knowledge_weaviate_ref ON orch_knowledge_metadata (weaviate_object_id);