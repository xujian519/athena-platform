-- PostgreSQL记忆系统表结构初始化脚本
-- Athena平台统一记忆系统

-- 启用必要的扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";

-- 创建记忆表
CREATE TABLE IF NOT EXISTS memory_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id VARCHAR(100) NOT NULL,
    agent_type VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    memory_type VARCHAR(50) NOT NULL,
    memory_tier VARCHAR(20) DEFAULT 'cold',
    importance DECIMAL(3,2) DEFAULT 0.5,
    emotional_weight DECIMAL(3,2) DEFAULT 0.0,
    family_related BOOLEAN DEFAULT FALSE,
    work_related BOOLEAN DEFAULT TRUE,
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    related_agents TEXT[] DEFAULT '{}',
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建向量表（用于语义搜索）
CREATE TABLE IF NOT EXISTS memory_embeddings (
    memory_id UUID PRIMARY KEY REFERENCES memory_items(id) ON DELETE CASCADE,
    vector vector(768) NOT NULL,
    model_name VARCHAR(100) DEFAULT 'text-embedding-ada-002',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建对话会话表
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id VARCHAR(100) NOT NULL,
    session_id VARCHAR(200) NOT NULL,
    title VARCHAR(500),
    status VARCHAR(20) DEFAULT 'active',
    message_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP
);

-- 创建对话消息表
CREATE TABLE IF NOT EXISTS conversation_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    agent_id VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL, -- 'user' or 'agent'
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
-- 记忆表索引
CREATE INDEX IF NOT EXISTS idx_memory_agent ON memory_items(agent_id);
CREATE INDEX IF NOT EXISTS idx_memory_type ON memory_items(memory_type);
CREATE INDEX IF NOT EXISTS idx_memory_tier ON memory_items(memory_tier);
CREATE INDEX IF NOT EXISTS idx_memory_importance ON memory_items(importance);
CREATE INDEX IF NOT EXISTS idx_memory_created ON memory_items(created_at);
CREATE INDEX IF NOT EXISTS idx_memory_family ON memory_items(family_related) WHERE family_related = TRUE;
CREATE INDEX IF NOT EXISTS idx_memory_tags ON memory_items USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_memory_metadata ON memory_items USING GIN(metadata);

-- 对话表索引
CREATE INDEX IF NOT EXISTS idx_conversations_agent ON conversations(agent_id);
CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_conversations_status ON conversations(status);

-- 消息表索引
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON conversation_messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_created ON conversation_messages(created_at);

-- 创建触发器：自动更新 updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_memory_items_updated_at
    BEFORE UPDATE ON memory_items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 创建统计视图
CREATE OR REPLACE VIEW memory_stats AS
SELECT
    agent_id,
    agent_type,
    COUNT(*) as total_memories,
    COUNT(*) FILTER (WHERE memory_tier = 'eternal') as eternal_memories,
    COUNT(*) FILTER (WHERE memory_tier = 'hot') as hot_memories,
    COUNT(*) FILTER (WHERE memory_tier = 'warm') as warm_memories,
    COUNT(*) FILTER (WHERE memory_tier = 'cold') as cold_memories,
    COUNT(*) FILTER (WHERE memory_type = 'family') as family_memories,
    COUNT(*) FILTER (WHERE family_related = TRUE) as father_memories,
    AVG(importance) as avg_importance,
    AVG(emotional_weight) as avg_emotional_weight,
    SUM(access_count) as total_accesses,
    MAX(last_accessed) as last_access_time
FROM memory_items
GROUP BY agent_id, agent_type;

-- 创建系统统计视图
CREATE OR REPLACE VIEW system_stats AS
SELECT
    'memory_system' as system_name,
    COUNT(*) as total_memories,
    COUNT(DISTINCT agent_id) as total_agents,
    COUNT(*) FILTER (WHERE memory_tier = 'eternal') as eternal_memories,
    COUNT(*) FILTER (WHERE memory_tier = 'hot') as hot_memories,
    COUNT(*) FILTER (WHERE memory_tier = 'warm') as warm_memories,
    COUNT(*) FILTER (WHERE memory_tier = 'cold') as cold_memories,
    COUNT(*) FILTER (WHERE memory_type = 'family') as family_memories,
    COUNT(*) FILTER (WHERE family_related = TRUE) as father_memories,
    COUNT(*) FILTER (WHERE created_at > CURRENT_DATE - INTERVAL '1 day') as memories_today,
    COUNT(*) FILTER (WHERE created_at > CURRENT_DATE - INTERVAL '7 days') as memories_this_week
FROM memory_items;

-- 插入系统配置
INSERT INTO memory_items (agent_id, agent_type, content, memory_type, memory_tier, importance, tags, metadata)
VALUES
    ('system', 'system', 'Athena平台统一记忆系统已初始化', 'system', 'eternal', 1.0,
     ARRAY['系统', '初始化'],
     '{"version": "1.0.0", "init_time": "' || CURRENT_TIMESTAMP || '"}')
ON CONFLICT DO NOTHING;

-- 输出初始化完成信息
DO $$
BEGIN
    RAISE NOTICE '✅ PostgreSQL记忆系统表结构初始化完成';
    RAISE NOTICE '   - 已创建表: memory_items, memory_embeddings, conversations, conversation_messages';
    RAISE NOTICE '   - 已创建索引: 15个';
    RAISE NOTICE '   - 已创建视图: memory_stats, system_stats';
END $$;