-- ============================================================================
-- Athena记忆模块 - PostgreSQL数据库初始化脚本
-- ============================================================================
-- 此脚本创建记忆系统所需的所有数据库表、索引和扩展
--
-- 执行时机: PostgreSQL容器首次启动时自动执行
-- ============================================================================

-- 启用必要的扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";

-- ============================================================================
-- 记忆主表
-- ============================================================================
-- 存储所有记忆的核心数据

CREATE TABLE IF NOT EXISTS memories (
    -- 主键
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- 智能体信息
    agent_id VARCHAR(255) NOT NULL,
    agent_type VARCHAR(50) NOT NULL,

    -- 记忆内容
    content TEXT NOT NULL,
    memory_type VARCHAR(50) NOT NULL,
    memory_tier VARCHAR(50) NOT NULL DEFAULT 'cold',

    -- 重要性评分
    importance FLOAT DEFAULT 0.5,
    emotional_weight FLOAT DEFAULT 0.0,

    -- 标签和元数据
    tags TEXT[],
    metadata JSONB DEFAULT '{}',

    -- 共享设置
    shared_with TEXT[],
    is_shared BOOLEAN DEFAULT FALSE,

    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,

    -- 访问统计
    access_count INTEGER DEFAULT 0,

    -- 状态
    is_archived BOOLEAN DEFAULT FALSE,
    is_deleted BOOLEAN DEFAULT FALSE
);

-- ============================================================================
-- 索引创建
-- ============================================================================

-- 智能体ID索引
CREATE INDEX IF NOT EXISTS idx_memories_agent_id
    ON memories(agent_id);

-- 智能体类型索引
CREATE INDEX IF NOT EXISTS idx_memories_agent_type
    ON memories(agent_type);

-- 记忆类型索引
CREATE INDEX IF NOT EXISTS idx_memories_memory_type
    ON memories(memory_type);

-- 记忆层级索引
CREATE INDEX IF NOT EXISTS idx_memories_memory_tier
    ON memories(memory_tier);

-- 重要性索引
CREATE INDEX IF NOT EXISTS idx_memories_importance
    ON memories(importance DESC);

-- 创建时间索引
CREATE INDEX IF NOT EXISTS idx_memories_created_at
    ON memories(created_at DESC);

-- 最后访问时间索引
CREATE INDEX IF NOT EXISTS idx_memories_last_accessed
    ON memories(last_accessed DESC);

-- 组合索引：智能体+重要性
CREATE INDEX IF NOT EXISTS idx_memories_agent_importance
    ON memories(agent_id, importance DESC);

-- 组合索引：智能体+类型
CREATE INDEX IF NOT EXISTS idx_memories_agent_type_tier
    ON memories(agent_id, memory_type, memory_tier);

-- 过滤索引：未删除的记忆
CREATE INDEX IF NOT EXISTS idx_memories_active
    ON memories(agent_id, created_at DESC)
    WHERE is_deleted = FALSE AND is_archived = FALSE;

-- GIN索引：标签搜索
CREATE INDEX IF NOT EXISTS idx_memories_tags
    ON memories USING GIN(tags);

-- GIN索引：元数据搜索
CREATE INDEX IF NOT EXISTS idx_memories_metadata
    ON memories USING GIN(metadata);

-- ============================================================================
-- 向量搜索支持 (可选 - 如果使用pgvector)
-- ============================================================================

-- 向量列 (1024维，与BGE-M3模型一致)
ALTER TABLE memories
    ADD COLUMN IF NOT EXISTS embedding vector(1024);

-- 向量相似度索引 (IVFFlat)
-- 注意：需要至少1000条记录才能创建IVFFlat索引
CREATE INDEX IF NOT EXISTS idx_memories_embedding_ivfflat
    ON memories
    USING IVFFlat(embedding vector_cosine_ops)
    WITH (lists = 100);

-- ============================================================================
-- 触发器：自动更新 updated_at
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_memories_updated_at
    BEFORE UPDATE ON memories
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 触发器：自动更新访问计数
-- ============================================================================

CREATE OR REPLACE FUNCTION increment_access_count()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_accessed = NOW();
    NEW.access_count = OLD.access_count + 1;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 注意：这个触发器需要在应用层控制，避免每次SELECT都更新
-- CREATE TRIGGER update_memories_access
--     BEFORE UPDATE ON memories
--     FOR EACH ROW
--     EXECUTE FUNCTION increment_access_count();

-- ============================================================================
-- 统计信息表 (可选)
-- ============================================================================

CREATE TABLE IF NOT EXISTS memory_stats (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(255) NOT NULL UNIQUE,
    total_memories INTEGER DEFAULT 0,
    family_memories INTEGER DEFAULT 0,
    episodic_memories INTEGER DEFAULT 0,
    semantic_memories INTEGER DEFAULT 0,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_memory_stats_agent_id
    ON memory_stats(agent_id);

-- ============================================================================
-- 清理过期记忆的函数
-- ============================================================================

CREATE OR REPLACE FUNCTION cleanup_expired_memories()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM memories
    WHERE expires_at IS NOT NULL
      AND expires_at < NOW()
      AND is_deleted = FALSE;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 数据统计函数
-- ============================================================================

CREATE OR REPLACE FUNCTION get_agent_memory_stats(p_agent_id VARCHAR)
RETURNS TABLE(
    total_memories BIGINT,
    family_memories BIGINT,
    episodic_memories BIGINT,
    semantic_memories BIGINT,
    hot_memories BIGINT,
    warm_memories BIGINT,
    cold_memories BIGINT,
    eternal_memories BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*) FILTER (WHERE is_deleted = FALSE) AS total_memories,
        COUNT(*) FILTER (WHERE is_deleted = FALSE AND family_related = TRUE) AS family_memories,
        COUNT(*) FILTER (WHERE is_deleted = FALSE AND memory_type = 'episodic') AS episodic_memories,
        COUNT(*) FILTER (WHERE is_deleted = FALSE AND memory_type = 'semantic') AS semantic_memories,
        COUNT(*) FILTER (WHERE is_deleted = FALSE AND memory_tier = 'hot') AS hot_memories,
        COUNT(*) FILTER (WHERE is_deleted = FALSE AND memory_tier = 'warm') AS warm_memories,
        COUNT(*) FILTER (WHERE is_deleted = FALSE AND memory_tier = 'cold') AS cold_memories,
        COUNT(*) FILTER (WHERE is_deleted = FALSE AND memory_tier = 'eternal') AS eternal_memories
    FROM memories
    WHERE agent_id = p_agent_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 授权 (如果需要创建只读用户)
-- ============================================================================

-- CREATE ROLE athena_memory_readonly WITH LOGIN PASSWORD 'readonly_password';
-- GRANT CONNECT ON DATABASE athena_memory TO athena_memory_readonly;
-- GRANT USAGE ON SCHEMA public TO athena_memory_readonly;
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO athena_memory_readonly;

-- ============================================================================
-- 初始化完成标记
-- ============================================================================

-- 插入初始化记录
INSERT INTO memories (agent_id, agent_type, content, memory_type, memory_tier, importance)
VALUES ('system', 'system', 'Athena记忆系统初始化完成', 'system', 'eternal', 1.0)
ON CONFLICT DO NOTHING;

-- 输出完成信息
DO $$
BEGIN
    RAISE NOTICE '===========================================';
    RAISE NOTICE 'Athena记忆模块数据库初始化完成！';
    RAISE NOTICE '===========================================';
    RAISE NOTICE '数据库: %', current_database();
    RAISE NOTICE 'Schema: public';
    RAISE NOTICE '扩展: uuid-ossp, pgvector';
    RAISE NOTICE '主表: memories';
    RAISE NOTICE '向量维度: 1024 (BGE-M3)';
    RAISE NOTICE '===========================================';
END $$;
