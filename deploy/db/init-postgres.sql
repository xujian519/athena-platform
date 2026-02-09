-- PostgreSQL 初始化脚本
-- 为测试环境启用pgvector扩展并创建必要的表

-- 启用pgvector扩展
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- 用于全文搜索

-- 创建测试表
CREATE TABLE IF NOT EXISTS test_patents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    abstract TEXT,
    applicant VARCHAR(255),
    inventor VARCHAR(255),
    application_date DATE,
    publication_date DATE,
    ipc_code VARCHAR(50),
    status VARCHAR(50) DEFAULT 'pending',
    embedding vector(768),  -- 768维向量 (BGE-M3)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建测试用户表
CREATE TABLE IF NOT EXISTS test_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建测试会话表
CREATE TABLE IF NOT EXISTS test_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES test_users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建测试日志表
CREATE TABLE IF NOT EXISTS test_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    level VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    context JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建测试缓存表
CREATE TABLE IF NOT EXISTS test_cache (
    key VARCHAR(255) PRIMARY KEY,
    value JSONB NOT NULL,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建测试任务表
CREATE TABLE IF NOT EXISTS test_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    result JSONB,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_test_patents_title ON test_patents USING gin(title gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_test_patents_applicant ON test_patents(applicant);
CREATE INDEX IF NOT EXISTS idx_test_patents_ipc_code ON test_patents(ipc_code);
CREATE INDEX IF NOT EXISTS idx_test_patents_application_date ON test_patents(application_date DESC);
CREATE INDEX IF NOT EXISTS idx_test_patents_embedding ON test_patents USING ivfflat(embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_test_sessions_token ON test_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_test_sessions_expires_at ON test_sessions(expires_at);

CREATE INDEX IF NOT EXISTS idx_test_logs_level ON test_logs(level);
CREATE INDEX IF NOT EXISTS idx_test_logs_created_at ON test_logs(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_test_cache_expires_at ON test_cache(expires_at);

CREATE INDEX IF NOT EXISTS idx_test_tasks_status ON test_tasks(status);
CREATE INDEX IF NOT EXISTS idx_test_tasks_created_at ON test_tasks(created_at DESC);

-- 插入测试数据
INSERT INTO test_users (username, email, password_hash, role) VALUES
    ('test_user', 'test@example.com', 'hashed_password_here', 'user'),
    ('test_admin', 'admin@example.com', 'hashed_password_here', 'admin')
ON CONFLICT (username) DO NOTHING;

-- 创建测试用的存储过程
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为需要的表添加updated_at自动更新触发器
CREATE TRIGGER update_test_patents_updated_at BEFORE UPDATE ON test_patents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_test_users_updated_at BEFORE UPDATE ON test_users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_test_cache_updated_at BEFORE UPDATE ON test_cache
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_test_tasks_updated_at BEFORE UPDATE ON test_tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 授予测试用户权限
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO athena_test;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO athena_test;

-- 输出初始化完成信息
DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'PostgreSQL测试数据库初始化完成！';
    RAISE NOTICE '========================================';
    RAISE NOTICE '已创建的表:';
    RAISE NOTICE '  - test_patents (测试专利数据)';
    RAISE NOTICE '  - test_users (测试用户)';
    RAISE NOTICE '  - test_sessions (测试会话)';
    RAISE NOTICE '  - test_logs (测试日志)';
    RAISE NOTICE '  - test_cache (测试缓存)';
    RAISE NOTICE '  - test_tasks (测试任务)';
    RAISE NOTICE '========================================';
    RAISE NOTICE '已启用的扩展:';
    RAISE NOTICE '  - vector (pgvector向量支持)';
    RAISE NOTICE '  - uuid-ossp (UUID生成)';
    RAISE NOTICE '  - pg_trgm (全文搜索)';
    RAISE NOTICE '========================================';
    RAISE NOTICE '已插入测试用户:';
    RAISE NOTICE '  - test_user / test@example.com';
    RAISE NOTICE '  - test_admin / admin@example.com';
    RAISE NOTICE '========================================';
END $$;
