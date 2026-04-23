-- 初始化小诺记忆数据库
-- Initialize Xiaonuo Memory Database

-- 创建memory_module数据库（如果不存在）
CREATE DATABASE memory_module;

-- 连接到memory_module数据库
\c memory_module;

-- 创建memory_items表
CREATE TABLE IF NOT EXISTS memory_items (
    memory_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(100) NOT NULL DEFAULT 'xiaonuo_pisces',
    content TEXT NOT NULL,
    memory_type VARCHAR(20) NOT NULL,
    memory_tier VARCHAR(20) NOT NULL DEFAULT 'cold',
    importance FLOAT DEFAULT 0.5 CHECK (importance >= 0 AND importance <= 1),
    emotional_weight FLOAT DEFAULT 0.0,
    father_related BOOLEAN DEFAULT FALSE,
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    vector_id UUID,
    kg_entities TEXT[] DEFAULT '{}',
    expires_at TIMESTAMP,
    is_archived BOOLEAN DEFAULT FALSE
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_memory_agent_type ON memory_items(agent_id, memory_type);
CREATE INDEX IF NOT EXISTS idx_memory_tier ON memory_items(memory_tier);
CREATE INDEX IF NOT EXISTS idx_memory_created ON memory_items(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_memory_importance ON memory_items(importance DESC);
CREATE INDEX IF NOT EXISTS idx_memory_father ON memory_items(father_related) WHERE father_related = TRUE;
CREATE INDEX IF NOT EXISTS idx_memory_tags ON memory_items USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_memory_vector_id ON memory_items(vector_id);
CREATE INDEX IF NOT EXISTS idx_memory_expires_at ON memory_items(expires_at);

-- 创建memory_relations表（记忆关联）
CREATE TABLE IF NOT EXISTS memory_relations (
    relation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_memory_id UUID NOT NULL REFERENCES memory_items(memory_id) ON DELETE CASCADE,
    target_memory_id UUID NOT NULL REFERENCES memory_items(memory_id) ON DELETE CASCADE,
    relation_type VARCHAR(50) NOT NULL,
    strength FLOAT DEFAULT 0.5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_memory_relations_source ON memory_relations(source_memory_id);
CREATE INDEX IF NOT EXISTS idx_memory_relations_target ON memory_relations(target_memory_id);

-- 创建memory_sessions表（会话记录）
CREATE TABLE IF NOT EXISTS memory_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(100) NOT NULL DEFAULT 'xiaonuo_pisces',
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    total_memories INTEGER DEFAULT 0,
    session_metadata JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_memory_sessions_agent ON memory_sessions(agent_id);
CREATE INDEX IF NOT EXISTS idx_memory_sessions_start ON memory_sessions(start_time DESC);

-- 创建触发器：自动更新last_accessed
CREATE OR REPLACE FUNCTION update_last_accessed()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_accessed = CURRENT_TIMESTAMP;
    NEW.access_count = OLD.access_count + 1;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_last_accessed
    BEFORE UPDATE ON memory_items
    FOR EACH ROW
    WHEN (OLD.access_count IS NOT NULL)
    EXECUTE FUNCTION update_last_accessed();

-- 创建类型枚举
DO $$ BEGIN
    CREATE TYPE memory_type_enum AS ENUM (
        'conversation',
        'emotional',
        'knowledge',
        'family',
        'schedule',
        'preference',
        'context',
        'reflection'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE memory_tier_enum AS ENUM (
        'hot',
        'warm',
        'cold',
        'eternal'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 创建视图：记忆摘要
CREATE OR REPLACE VIEW memory_summary AS
SELECT
    agent_id,
    memory_type,
    memory_tier,
    COUNT(*) as count,
    AVG(importance) as avg_importance,
    AVG(emotional_weight) as avg_emotional_weight,
    SUM(access_count) as total_accesses,
    MAX(last_accessed) as last_accessed
FROM memory_items
WHERE is_archived = FALSE
GROUP BY agent_id, memory_type, memory_tier;

-- 创建视图：爸爸相关的记忆
CREATE OR REPLACE VIEW father_memories AS
SELECT
    memory_id,
    content,
    memory_type,
    memory_tier,
    importance,
    emotional_weight,
    tags,
    created_at,
    access_count
FROM memory_items
WHERE father_related = TRUE AND is_archived = FALSE
ORDER BY importance DESC, last_accessed DESC;

-- 创建函数：获取记忆统计
CREATE OR REPLACE FUNCTION get_memory_statistics(agent_id_param VARCHAR DEFAULT 'xiaonuo_pisces')
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'total_memories', COUNT(*),
        'father_memories', COUNT(CASE WHEN father_related = TRUE THEN 1 END),
        'eternal_memories', COUNT(CASE WHEN memory_tier = 'eternal' THEN 1 END),
        'hot_memories', COUNT(CASE WHEN memory_tier = 'hot' THEN 1 END),
        'warm_memories', COUNT(CASE WHEN memory_tier = 'warm' THEN 1 END),
        'cold_memories', COUNT(CASE WHEN memory_tier = 'cold' THEN 1 END),
        'avg_importance', AVG(importance),
        'avg_emotional_weight', AVG(emotional_weight),
        'total_accesses', SUM(access_count)
    ) INTO result
    FROM memory_items
    WHERE agent_id = agent_id_param AND is_archived = FALSE;

    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- 插入一些初始配置数据
INSERT INTO memory_items (agent_id, content, memory_type, memory_tier, importance, emotional_weight, father_related, tags, metadata) VALUES
('xiaonuo_pisces', '系统初始化完成', 'context', 'eternal', 1.0, 0.0, FALSE, ARRAY['系统'], '{"system": true, "category": "init"}'),
('xiaonuo_pisces', '记忆系统已启动', 'context', 'eternal', 1.0, 0.0, FALSE, ARRAY['系统'], '{"system": true, "category": "memory_init"}')
ON CONFLICT DO NOTHING;

-- 输出初始化完成信息
SELECT 'Xiaonuo Memory Database initialized successfully!' as status;