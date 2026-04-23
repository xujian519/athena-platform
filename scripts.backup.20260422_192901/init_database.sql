-- Athena工作平台 - 数据库初始化脚本
-- Database Initialization Script for Athena Platform
-- PostgreSQL 17.7
--
-- 用途: 初始化执行模块所需的数据库表和函数
-- 使用: psql -h localhost -U athena -d athena_production -f scripts/init_database.sql

-- ==========================================
-- 1. 创建扩展
-- ==========================================

-- 启用UUID生成
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 启用JSONB索引优化
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- 启用全文搜索（zhparser需要单独安装，这里是可选的）
-- CREATE EXTENSION IF NOT EXISTS "zhparser";

-- ==========================================
-- 2. 创建执行模块表
-- ==========================================

-- 任务队列表
CREATE TABLE IF NOT EXISTS execution_tasks (
    task_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_name VARCHAR(255) NOT NULL,
    task_type VARCHAR(100) NOT NULL,
    priority INTEGER NOT NULL DEFAULT 3,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    payload JSONB NOT NULL,
    result JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    retry_count INTEGER NOT NULL DEFAULT 0,
    max_retries INTEGER NOT NULL DEFAULT 3,
    timeout_seconds INTEGER,
    worker_id VARCHAR(100),
    dependencies TEXT[],
    metadata JSONB DEFAULT '{}'::jsonb
);

-- 任务执行历史表
CREATE TABLE IF NOT EXISTS execution_history (
    history_id BIGSERIAL PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES execution_tasks(task_id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB DEFAULT '{}'::jsonb,
    event_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    worker_id VARCHAR(100)
);

-- 工作流表
CREATE TABLE IF NOT EXISTS execution_workflows (
    workflow_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_name VARCHAR(255) NOT NULL,
    workflow_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'created',
    config JSONB NOT NULL,
    tasks JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_by VARCHAR(100),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- 工作流执行记录表
CREATE TABLE IF NOT EXISTS workflow_executions (
    execution_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id UUID NOT NULL REFERENCES execution_workflows(workflow_id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'running',
    input_data JSONB DEFAULT '{}'::jsonb,
    output_data JSONB,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER
);

-- ==========================================
-- 3. 创建索引
-- ==========================================

-- 任务表索引
CREATE INDEX IF NOT EXISTS idx_tasks_status ON execution_tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON execution_tasks(priority);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON execution_tasks(created_at);
CREATE INDEX IF NOT EXISTS idx_tasks_worker_id ON execution_tasks(worker_id);
CREATE INDEX IF NOT EXISTS idx_tasks_type_status ON execution_tasks(task_type, status);

-- JSONB字段索引
CREATE INDEX IF NOT EXISTS idx_tasks_payload_gin ON execution_tasks USING gin(payload);
CREATE INDEX IF NOT EXISTS idx_tasks_result_gin ON execution_tasks USING gin(result);
CREATE INDEX IF NOT EXISTS idx_tasks_metadata_gin ON execution_tasks USING gin(metadata);

-- 工作流表索引
CREATE INDEX IF NOT EXISTS idx_workflows_status ON execution_workflows(status);
CREATE INDEX IF NOT EXISTS idx_workflows_created_at ON execution_workflows(created_at);
CREATE INDEX IF NOT EXISTS idx_workflows_updated_at ON execution_workflows(updated_at);

-- ==========================================
-- 4. 创建视图
-- ==========================================

-- 任务统计视图
CREATE OR REPLACE VIEW v_task_stats AS
SELECT
    task_type,
    status,
    COUNT(*) as count,
    AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_duration_seconds,
    MIN(created_at) as earliest_created,
    MAX(created_at) as latest_created
FROM execution_tasks
WHERE completed_at IS NOT NULL
GROUP BY task_type, status;

-- 工作流统计视图
CREATE OR REPLACE VIEW v_workflow_stats AS
SELECT
    workflow_type,
    status,
    COUNT(*) as count,
    AVG(duration_seconds) as avg_duration_seconds,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_count,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count
FROM workflow_executions
GROUP BY workflow_type, status;

-- ==========================================
-- 5. 创建函数
-- ==========================================

-- 获取待执行的任务
CREATE OR REPLACE FUNCTION get_pending_tasks(
    p_worker_id VARCHAR,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    task_id UUID,
    task_name VARCHAR,
    task_type VARCHAR,
    priority INTEGER,
    payload JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        t.task_id,
        t.task_name,
        t.task_type,
        t.priority,
        t.payload
    FROM execution_tasks t
    WHERE t.status = 'pending'
    AND (t.dependencies IS NULL OR array_length(t.dependencies, 1) IS NULL OR NOT EXISTS (
        SELECT 1 FROM execution_tasks t2
        WHERE t2.task_id = ANY(t.dependencies)
        AND t2.status NOT IN ('completed', 'cancelled')
    ))
    ORDER BY t.priority ASC, t.created_at ASC
    LIMIT p_limit
    FOR UPDATE SKIP LOCKED;

    -- 更新任务状态为已分配
    UPDATE execution_tasks
    SET status = 'assigned',
        worker_id = p_worker_id,
        started_at = NOW()
    WHERE task_id IN (SELECT task_id FROM get_pending_tasks(p_worker_id, p_limit));

END;
$$ LANGUAGE plpgsql;

-- 更新任务状态
CREATE OR REPLACE FUNCTION update_task_status(
    p_task_id UUID,
    p_status VARCHAR,
    p_result JSONB DEFAULT NULL,
    p_error_message TEXT DEFAULT NULL
)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE execution_tasks
    SET
        status = p_status,
        result = p_result,
        error_message = p_error_message,
        completed_at = CASE WHEN p_status IN ('completed', 'failed', 'cancelled') THEN NOW() ELSE NULL END
    WHERE task_id = p_task_id;

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- 清理旧任务
CREATE OR REPLACE FUNCTION cleanup_old_tasks(
    p_days INTEGER DEFAULT 30
)
RETURNS INTEGER AS $$
DECLARE
    v_deleted_count INTEGER;
BEGIN
    DELETE FROM execution_tasks
    WHERE status IN ('completed', 'failed', 'cancelled')
    AND completed_at < NOW() - INTERVAL '1 day' * p_days;

    GET DIAGNOSTICS v_deleted_count = ROW_COUNT;
    RETURN v_deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- 6. 创建触发器
-- ==========================================

-- 更新工作流updated_at字段
CREATE OR REPLACE FUNCTION update_workflow_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_workflow_updated_at
    BEFORE UPDATE ON execution_workflows
    FOR EACH ROW
    EXECUTE FUNCTION update_workflow_updated_at();

-- ==========================================
-- 7. 插入初始数据
-- ==========================================

-- 插入示例任务类型配置
INSERT INTO execution_workflows (workflow_name, workflow_type, status, config)
VALUES
    ('默认任务处理流程', 'default_task', 'active', '{"max_concurrent": 20, "timeout": 300}'),
    ('批量任务处理流程', 'batch_task', 'active', '{"max_concurrent": 50, "timeout": 600}'),
    ('高优先级任务流程', 'high_priority_task', 'active', '{"max_concurrent": 5, "timeout": 120}')
ON CONFLICT DO NOTHING;

-- ==========================================
-- 8. 授予权限
-- ==========================================

-- 授予应用用户权限
GRANT SELECT, INSERT, UPDATE, DELETE ON execution_tasks TO athena;
GRANT SELECT, INSERT, UPDATE, DELETE ON execution_history TO athena;
GRANT SELECT, INSERT, UPDATE, DELETE ON execution_workflows TO athena;
GRANT SELECT, INSERT, UPDATE, DELETE ON workflow_executions TO athena;

-- 授予视图权限
GRANT SELECT ON v_task_stats TO athena;
GRANT SELECT ON v_workflow_stats TO athena;

-- 授予函数权限
GRANT EXECUTE ON FUNCTION get_pending_tasks(VARCHAR, INTEGER) TO athena;
GRANT EXECUTE ON FUNCTION update_task_status(UUID, VARCHAR, JSONB, TEXT) TO athena;
GRANT EXECUTE ON FUNCTION cleanup_old_tasks(INTEGER) TO athena;

-- ==========================================
-- 9. 启用自动清理
-- ==========================================

-- 配置自动清理
ALTER TABLE execution_tasks SET (autovacuum_analyze_scale_factor = 0.05);
ALTER TABLE execution_history SET (autovacuum_analyze_scale_factor = 0.1);
ALTER TABLE execution_workflows SET (autovacuum_analyze_scale_factor = 0.05);
ALTER TABLE workflow_executions SET (autovacuum_analyze_scale_factor = 0.1);

-- ==========================================
-- 10. 验证安装
-- ==========================================

-- 显示安装摘要
DO $$
BEGIN
    RAISE NOTICE '============================================';
    RAISE NOTICE 'Athena执行模块数据库初始化完成';
    RAISE NOTICE '============================================';
    RAISE NOTICE 'PostgreSQL版本: %', version();
    RAISE NOTICE '当前数据库: %', current_database();
    RAISE NOTICE '当前用户: %', current_user;
    RAISE NOTICE '当前时间: %', NOW();
    RAISE NOTICE '============================================';
END $$;

-- 查询表信息
SELECT
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE t.table_schema = 'public'
AND t.table_name IN ('execution_tasks', 'execution_history', 'execution_workflows', 'workflow_executions')
ORDER BY t.table_name;
