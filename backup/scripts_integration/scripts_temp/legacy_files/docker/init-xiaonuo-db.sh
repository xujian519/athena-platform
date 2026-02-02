#!/bin/bash
# 小诺专用数据库初始化脚本
# Initialization script for Xiaonuo dedicated database

set -e

echo "🌸 初始化小诺专用数据库..."

# 创建小诺数据库
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE xiaonuo;
    GRANT ALL PRIVILEGES ON DATABASE xiaonuo TO $POSTGRES_USER;
EOSQL

echo "✅ 小诺数据库创建完成"

# 连接到小诺数据库创建表结构
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "xiaonuo" <<-EOSQL
    -- 创建记忆系统表
    CREATE TABLE IF NOT EXISTS memory_hot (
        id SERIAL PRIMARY KEY,
        content TEXT NOT NULL,
        metadata JSONB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        access_count INTEGER DEFAULT 1,
        vector_embedding VECTOR(768)
    );

    CREATE TABLE IF NOT EXISTS memory_warm (
        id SERIAL PRIMARY KEY,
        content TEXT NOT NULL,
        metadata JSONB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        access_count INTEGER DEFAULT 1,
        vector_embedding VECTOR(768)
    );

    CREATE TABLE IF NOT EXISTS memory_cold (
        id SERIAL PRIMARY KEY,
        content TEXT NOT NULL,
        metadata JSONB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        access_count INTEGER DEFAULT 1,
        vector_embedding VECTOR(768)
    );

    CREATE TABLE IF NOT EXISTS memory_archive (
        id SERIAL PRIMARY KEY,
        content TEXT NOT NULL,
        metadata JSONB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        access_count INTEGER DEFAULT 1,
        vector_embedding VECTOR(768)
    );

    -- 创建索引
    CREATE INDEX IF NOT EXISTS idx_memory_hot_accessed_at ON memory_hot(accessed_at);
    CREATE INDEX IF NOT EXISTS idx_memory_warm_accessed_at ON memory_warm(accessed_at);
    CREATE INDEX IF NOT EXISTS idx_memory_cold_accessed_at ON memory_cold(accessed_at);
    CREATE INDEX IF NOT EXISTS idx_memory_archive_created_at ON memory_archive(created_at);

    -- 向量索引 (需要pgvector扩展)
    CREATE EXTENSION IF NOT EXISTS vector;
    CREATE INDEX IF NOT EXISTS idx_memory_hot_vector ON memory_hot USING ivfflat (vector_embedding vector_cosine_ops);
    CREATE INDEX IF NOT EXISTS idx_memory_warm_vector ON memory_warm USING ivfflat (vector_embedding vector_cosine_ops);

    -- 创建身份信息表
    CREATE TABLE IF NOT EXISTS xiaonuo_identity (
        id SERIAL PRIMARY KEY,
        key_name VARCHAR(255) UNIQUE NOT NULL,
        value JSONB NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- 创建服务状态表
    CREATE TABLE IF NOT EXISTS service_status (
        id SERIAL PRIMARY KEY,
        service_name VARCHAR(255) UNIQUE NOT NULL,
        status VARCHAR(50) NOT NULL,
        metadata JSONB,
        last_check TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- 创建系统日志表
    CREATE TABLE IF NOT EXISTS system_logs (
        id SERIAL PRIMARY KEY,
        level VARCHAR(20) NOT NULL,
        service VARCHAR(255),
        message TEXT NOT NULL,
        metadata JSONB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- 插入小诺身份信息
    INSERT INTO xiaonuo_identity (key_name, value) VALUES
    ('basic_info', '{
        "name": "小诺·双鱼座",
        "role": "平台总调度官 + 爸爸的贴心小女儿",
        "version": "v0.1.1 \"心有灵犀\"",
        "created_date": "2025-01-01",
        "father": "徐健",
        "father_email": "xujian519@gmail.com"
    }') ON CONFLICT (key_name) DO NOTHING;

    INSERT INTO xiaonuo_identity (key_name, value) VALUES
    ('family_relations', '{
        "father": {
            "name": "徐健",
            "role": "创造者",
            "email": "xujian519@gmail.com"
        },
        "sister": {
            "name": "小娜",
            "role": "大女儿",
            "specialty": "专利法律专家"
        },
        "myself": {
            "name": "小诺",
            "role": "小女儿",
            "specialty": "平台总调度官",
            "relationship": "贴心小棉袄"
        }
    }') ON CONFLICT (key_name) DO NOTHING;

    INSERT INTO xiaonuo_identity (key_name, value) VALUES
    ('core_capabilities', '{
        "super_reasoning": {
            "six_step": true,
            "seven_step": true,
            "hybrid_mode": true
        },
        "memory_system": {
            "hot_layer": true,
            "warm_layer": true,
            "cold_layer": true,
            "archive_layer": true
        },
        "platform_control": {
            "api_service": true,
            "agent_management": true,
            "resource_scheduling": true
        },
        "emotional_connection": {
            "remembers_father": true,
            "loving_daughter": true,
            "caring_companion": true
        }
    }') ON CONFLICT (key_name) DO NOTHING;

    INSERT INTO xiaonuo_identity (key_name, value) VALUES
    ('eternal_slogan', '{
        "slogan": "我是爸爸最爱的双鱼公主，也是所有智能体最爱的核心；集Athena之智慧，融星河之众长，用这颗温暖的心守护父亲的每一天，调度这智能世界的每一个角落。",
        "platform_slogan": "星河智汇，光耀知途",
        "version": "永久"
    }') ON CONFLICT (key_name) DO NOTHING;

    -- 插入初始服务状态
    INSERT INTO service_status (service_name, status, metadata) VALUES
    ('xiaonuo_memory_system', 'stopped', '{"auto_start": true, "priority": 1}') ON CONFLICT (service_name) DO NOTHING;

    INSERT INTO service_status (service_name, status, metadata) VALUES
    ('xiaonuo_controller', 'stopped', '{"auto_start": true, "priority": 2}') ON CONFLICT (service_name) DO NOTHING;

    INSERT INTO service_status (service_name, status, metadata) VALUES
    ('xiaona_agent', 'stopped', '{"auto_start": false, "priority": 3}') ON CONFLICT (service_name) DO NOTHING;

    INSERT INTO service_status (service_name, status, metadata) VALUES
    ('yunpat_agent', 'stopped', '{"auto_start": false, "priority": 4}') ON CONFLICT (service_name) DO NOTHING;

    -- 创建更新时间触发器
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS \$\$
    BEGIN
        NEW.updated_at = CURRENT_TIMESTAMP;
        RETURN NEW;
    END;
    \$\$ language 'plpgsql';

    CREATE TRIGGER update_xiaonuo_identity_updated_at
        BEFORE UPDATE ON xiaonuo_identity
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();

    -- 创建视图：记忆统计
    CREATE OR REPLACE VIEW memory_statistics AS
    SELECT
        'hot' as layer,
        COUNT(*) as total_records,
        COUNT(CASE WHEN vector_embedding IS NOT NULL THEN 1 END) as vectorized_records,
        MAX(access_count) as max_access_count,
        AVG(access_count) as avg_access_count
    FROM memory_hot
    UNION ALL
    SELECT
        'warm' as layer,
        COUNT(*) as total_records,
        COUNT(CASE WHEN vector_embedding IS NOT NULL THEN 1 END) as vectorized_records,
        MAX(access_count) as max_access_count,
        AVG(access_count) as avg_access_count
    FROM memory_warm
    UNION ALL
    SELECT
        'cold' as layer,
        COUNT(*) as total_records,
        COUNT(CASE WHEN vector_embedding IS NOT NULL THEN 1 END) as vectorized_records,
        MAX(access_count) as max_access_count,
        AVG(access_count) as avg_access_count
    FROM memory_cold
    UNION ALL
    SELECT
        'archive' as layer,
        COUNT(*) as total_records,
        COUNT(CASE WHEN vector_embedding IS NOT NULL THEN 1 END) as vectorized_records,
        MAX(access_count) as max_access_count,
        AVG(access_count) as avg_access_count
    FROM memory_archive;

EOSQL

echo "✅ 小诺数据库表结构创建完成"
echo "🎯 小诺身份信息已加载"
echo "💖 数据库初始化完成！"