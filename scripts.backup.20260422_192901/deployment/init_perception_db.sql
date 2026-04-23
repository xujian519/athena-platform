-- Athena 感知模块 PostgreSQL 初始化脚本
-- 用于本地PostgreSQL 17.7
-- 最后更新: 2026-01-26

-- ========================================
-- 1. 创建感知模块专用用户
-- ========================================
DO
$$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'athena_perception') THEN
        CREATE ROLE athena_perception WITH
            LOGIN
            NOSUPERUSER
            NOCREATEDB
            NOCREATEROLE
            INHERIT
            NOREPLICATION
            CONNECTION LIMIT 200
            PASSWORD 'athena_perception_secure_2024';
    END IF;
END
$$;

-- ========================================
-- 2. 创建感知模块专用数据库
-- ========================================
SELECT 'CREATE DATABASE athena_perception'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'athena_perception')\gexec

-- ========================================
-- 3. 连接到感知模块数据库
-- ========================================
\c athena_perception

-- ========================================
-- 4. 启用必要的扩展
-- ========================================
-- 向量扩展（用于向量搜索）
CREATE EXTENSION IF NOT EXISTS vector;

-- UUID扩展（用于生成唯一ID）
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- pg_trgm扩展（用于文本模糊搜索）
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ========================================
-- 5. 授予权限
-- ========================================
-- 授予athena_perception用户对数据库的所有权限
GRANT ALL PRIVILEGES ON DATABASE athena_perception TO athena_perception;
GRANT ALL PRIVILEGES ON SCHEMA public TO athena_perception;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO athena_perception;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO athena_perception;

-- ========================================
-- 6. 创建核心数据表
-- ========================================

-- 感知任务表
CREATE TABLE IF NOT EXISTS perception_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id VARCHAR(100) NOT NULL,  -- 智能体ID（athena, xiaonuo, etc.）
    task_type VARCHAR(50) NOT NULL,  -- 任务类型（image, ocr, audio, video, multimodal）
    input_data JSONB NOT NULL,       -- 输入数据
    status VARCHAR(20) DEFAULT 'pending',  -- pending, processing, completed, failed
    result JSONB,                    -- 结果数据
    error_message TEXT,              -- 错误信息
    metadata JSONB,                  -- 元数据
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- 创建索引
CREATE INDEX idx_perception_tasks_agent_id ON perception_tasks(agent_id);
CREATE INDEX idx_perception_tasks_status ON perception_tasks(status);
CREATE INDEX idx_perception_tasks_task_type ON perception_tasks(task_type);
CREATE INDEX idx_perception_tasks_created_at ON perception_tasks(created_at DESC);

-- 添加注释
COMMENT ON TABLE perception_tasks IS '感知任务记录表，支持多智能体访问';
COMMENT ON COLUMN perception_tasks.agent_id IS '智能体标识：athena, xiaonuo, xiaona等';
COMMENT ON COLUMN perception_tasks.task_type IS '任务类型：image, ocr, audio, video, multimodal';

-- 感知缓存表
CREATE TABLE IF NOT EXISTS perception_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cache_key VARCHAR(512) UNIQUE NOT NULL,
    cache_value JSONB NOT NULL,
    vector_embedding vector(768),  -- 向量嵌入
    metadata JSONB,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    accessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建索引
CREATE INDEX idx_perception_cache_key ON perception_cache(cache_key);
CREATE INDEX idx_perception_cache_expires_at ON perception_cache(expires_at);
CREATE INDEX idx_perception_cache_vector_embedding ON perception_cache USING ivfflat (vector_embedding vector_cosine_ops);

-- 添加注释
COMMENT ON TABLE perception_cache IS '感知结果缓存表，支持向量相似度搜索';

-- 感知性能监控表
CREATE TABLE IF NOT EXISTS perception_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id VARCHAR(100) NOT NULL,
    task_type VARCHAR(50) NOT NULL,
    processing_time FLOAT NOT NULL,  -- 处理时间（秒）
    success BOOLEAN DEFAULT true,
    error_type VARCHAR(100),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建索引
CREATE INDEX idx_perception_metrics_agent_id ON perception_metrics(agent_id);
CREATE INDEX idx_perception_metrics_task_type ON perception_metrics(task_type);
CREATE INDEX idx_perception_metrics_created_at ON perception_metrics(created_at DESC);
CREATE INDEX idx_perception_metrics_processing_time ON perception_metrics(processing_time);

-- 添加注释
COMMENT ON TABLE perception_metrics IS '感知性能监控表，用于性能分析和优化';

-- ========================================
-- 7. 创建视图
-- ========================================

-- 智能体任务统计视图
CREATE OR REPLACE VIEW v_agent_task_stats AS
SELECT
    agent_id,
    task_type,
    status,
    COUNT(*) as task_count,
    AVG(EXTRACT(EPOCH FROM (COALESCE(completed_at, updated_at) - created_at))) as avg_processing_time,
    MIN(created_at) as first_task,
    MAX(created_at) as last_task
FROM perception_tasks
GROUP BY agent_id, task_type, status;

COMMENT ON VIEW v_agent_task_stats IS '智能体任务统计视图';

-- 感知模块健康检查视图
CREATE OR REPLACE VIEW v_perception_health AS
SELECT
    'pending' as status,
    COUNT(*) FILTER (WHERE status = 'pending') as count
FROM perception_tasks
UNION ALL
SELECT
    'processing' as status,
    COUNT(*) FILTER (WHERE status = 'processing') as count
FROM perception_tasks
UNION ALL
SELECT
    'completed' as status,
    COUNT(*) FILTER (WHERE status = 'completed') as count
FROM perception_tasks
UNION ALL
SELECT
    'failed' as status,
    COUNT(*) FILTER (WHERE status = 'failed') as count
FROM perception_tasks;

COMMENT ON VIEW v_perception_health IS '感知模块健康检查视图';

-- ========================================
-- 8. 创建函数
-- ========================================

-- 自动更新updated_at字段的函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 为perception_tasks表创建触发器
CREATE TRIGGER update_perception_tasks_updated_at
    BEFORE UPDATE ON perception_tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 缓存访问更新函数
CREATE OR REPLACE FUNCTION update_cache_accessed_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.accessed_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 为perception_cache表创建触发器
CREATE TRIGGER update_perception_cache_accessed_at
    BEFORE UPDATE ON perception_cache
    FOR EACH ROW
    EXECUTE FUNCTION update_cache_accessed_at();

-- 清理过期缓存函数
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM perception_cache
    WHERE expires_at < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_expired_cache() IS '清理过期缓存，返回删除的行数';

-- ========================================
-- 9. 插入示例数据（可选）
-- ========================================

-- 示例：Athena智能体的图像处理任务
INSERT INTO perception_tasks (agent_id, task_type, input_data, status, metadata)
VALUES
    ('athena', 'image', '{"image_path": "/data/patents/images/001.png", "operation": "extract_text"}', 'completed',
     '{"priority": "high", "source": "patent_analysis"}'),
    ('athena', 'ocr', '{"image_path": "/data/documents/002.png", "language": "chinese"}', 'completed',
     '{"confidence": 0.95, "source": "document_processing"}')
ON CONFLICT DO NOTHING;

-- 示例：小诺智能体的图像识别任务
INSERT INTO perception_tasks (agent_id, task_type, input_data, status, metadata)
VALUES
    ('xiaonuo', 'image', '{"image_path": "/data/life/photo_001.jpg", "operation": "scene_recognition"}', 'completed',
     '{"category": "indoor", "confidence": 0.88}')
ON CONFLICT DO NOTHING;

-- ========================================
-- 10. 授予其他智能体用户访问权限（如果存在）
-- ========================================

-- Athena智能体
DO
$$
BEGIN
    IF EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'athena') THEN
        GRANT SELECT, INSERT, UPDATE, DELETE ON perception_tasks TO athena;
        GRANT SELECT, INSERT, UPDATE, DELETE ON perception_cache TO athena;
        GRANT SELECT, INSERT ON perception_metrics TO athena;
        GRANT USAGE ON SCHEMA public TO athena;
    END IF;
END
$$;

-- 小诺智能体
DO
$$
BEGIN
    IF EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'xiaonuo') THEN
        GRANT SELECT, INSERT, UPDATE, DELETE ON perception_tasks TO xiaonuo;
        GRANT SELECT, INSERT, UPDATE, DELETE ON perception_cache TO xiaonuo;
        GRANT SELECT, INSERT ON perception_metrics TO xiaonuo;
        GRANT USAGE ON SCHEMA public TO xiaonuo;
    END IF;
END
$$;

-- 小娜智能体
DO
$$
BEGIN
    IF EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'xiaona') THEN
        GRANT SELECT, INSERT, UPDATE, DELETE ON perception_tasks TO xiaona;
        GRANT SELECT, INSERT, UPDATE, DELETE ON perception_cache TO xiaona;
        GRANT SELECT, INSERT ON perception_metrics TO xiaona;
        GRANT USAGE ON SCHEMA public TO xiaona;
    END IF;
END
$$;

-- ========================================
-- 11. 验证安装
-- ========================================

-- 显示创建的表
\dt 'perception_*'

-- 显示创建的视图
\dv v_*

-- 显示创建的函数
\df update_*
\df cleanup_*

-- 显示数据库信息
SELECT
    current_database() as database_name,
    current_user as current_user,
    version() as postgresql_version;

-- 显示权限信息
SELECT
    grantor,
    grantee,
    table_schema,
    table_name,
    privilege_type
FROM information_schema.role_table_grants
WHERE table_name LIKE 'perception_%'
ORDER BY table_name, grantee;

-- ========================================
-- 完成
-- ========================================

\echo '========================================'
\echo 'Athena 感知模块数据库初始化完成！'
\echo '========================================'
\echo '数据库名称: athena_perception'
\echo '用户名称: athena_perception'
\echo '端口: 5432'
\echo '主机: localhost'
\echo ''
\echo '已创建的表:'
\echo '  - perception_tasks (感知任务表)'
\echo '  - perception_cache (感知缓存表)'
\echo '  - perception_metrics (性能监控表)'
\echo ''
\echo '已创建的视图:'
\echo '  - v_agent_task_stats (智能体任务统计)'
\echo '  - v_perception_health (健康检查)'
\echo ''
\echo '已创建的函数:'
\echo '  - update_updated_at_column()'
\echo '  - update_cache_accessed_at()'
\echo '  - cleanup_expired_cache()'
\echo ''
\echo '支持的智能体:'
\echo '  - athena (专利分析)'
\echo '  - xiaonuo (生活助理)'
\echo '  - xiaona (法律顾问)'
\echo '========================================'
