-- 多模态文件系统数据库初始化脚本
-- Multimodal File System Database Initialization Script

-- 创建数据库（如果不存在）
-- CREATE DATABASE athena_business;

-- 使用数据库
-- \c athena_business;

-- 创建多模态文件表
CREATE TABLE IF NOT EXISTS multimodal_files (
    id SERIAL PRIMARY KEY,
    original_filename VARCHAR(500) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100),
    storage_path VARCHAR(1000) NOT NULL,
    processing_status VARCHAR(20) DEFAULT 'pending',
    processing_method VARCHAR(20),
    processing_result JSONB,
    error_message TEXT,
    metadata JSONB,
    vector_id INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_multimodal_files_status ON multimodal_files(processing_status);
CREATE INDEX IF NOT EXISTS idx_multimodal_files_type ON multimodal_files(file_type);
CREATE INDEX IF NOT EXISTS idx_multimodal_files_created ON multimodal_files(created_at);
CREATE INDEX IF NOT EXISTS idx_multimodal_files_vector ON multimodal_files(vector_id);
CREATE INDEX IF NOT EXISTS idx_multimodal_files_filename ON multimodal_files(original_filename);

-- 创建处理任务日志表
CREATE TABLE IF NOT EXISTS processing_logs (
    id SERIAL PRIMARY KEY,
    file_id INTEGER REFERENCES multimodal_files(id) ON DELETE CASCADE,
    processing_method VARCHAR(20) NOT NULL,
    processing_status VARCHAR(20) NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP WITH TIME ZONE,
    processing_result JSONB,
    error_message TEXT,
    processing_time_ms INTEGER
);

-- 创建日志表索引
CREATE INDEX IF NOT EXISTS idx_logs_file_id ON processing_logs(file_id);
CREATE INDEX IF NOT EXISTS idx_logs_status ON processing_logs(processing_status);
CREATE INDEX IF NOT EXISTS idx_logs_start_time ON processing_logs(start_time);

-- 创建文件标签表（用于分类和搜索）
CREATE TABLE IF NOT EXISTS file_tags (
    id SERIAL PRIMARY KEY,
    file_id INTEGER REFERENCES multimodal_files(id) ON DELETE CASCADE,
    tag_name VARCHAR(100) NOT NULL,
    tag_value TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(file_id, tag_name)
);

-- 创建标签索引
CREATE INDEX IF NOT EXISTS idx_tags_file_id ON file_tags(file_id);
CREATE INDEX IF NOT EXISTS idx_tags_name ON file_tags(tag_name);
CREATE INDEX IF NOT EXISTS idx_tags_value ON file_tags(tag_value);

-- 创建文件分享表（用于权限控制）
CREATE TABLE IF NOT EXISTS file_shares (
    id SERIAL PRIMARY KEY,
    file_id INTEGER REFERENCES multimodal_files(id) ON DELETE CASCADE,
    share_token VARCHAR(255) UNIQUE NOT NULL,
    share_type VARCHAR(20) NOT NULL, -- 'public', 'private', 'password'
    share_password VARCHAR(255),
    expires_at TIMESTAMP WITH TIME ZONE,
    created_by VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    max_access INTEGER DEFAULT -1 -- -1 means unlimited
);

-- 创建分享表索引
CREATE INDEX IF NOT EXISTS idx_shares_file_id ON file_shares(file_id);
CREATE INDEX IF NOT EXISTS idx_shares_token ON file_shares(share_token);
CREATE INDEX IF NOT EXISTS idx_shares_expires ON file_shares(expires_at);

-- 插入示例数据（可选）
INSERT INTO multimodal_files (
    original_filename,
    file_type,
    file_size,
    mime_type,
    storage_path,
    processing_status,
    metadata
) VALUES (
    'example.jpg',
    'image',
    1024576,
    'image/jpeg',
    '/Users/xujian/Athena工作平台/storage/multimodal/images/2024/12/17/example.jpg',
    'completed',
    '{"width": 1920, "height": 1080, "format": "JPEG", "color_space": "RGB"}'
) ON CONFLICT DO NOTHING;

-- 更新时间戳触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_multimodal_files_updated_at
    BEFORE UPDATE ON multimodal_files
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 创建视图：文件处理统计
CREATE OR REPLACE VIEW file_processing_stats AS
SELECT
    file_type,
    processing_status,
    COUNT(*) as count,
    AVG(file_size) as avg_size,
    SUM(file_size) as total_size,
    DATE(created_at) as date
FROM multimodal_files
GROUP BY file_type, processing_status, DATE(created_at)
ORDER BY date DESC, file_type, processing_status;

-- 创建视图：每日处理量统计
CREATE OR REPLACE VIEW daily_processing_stats AS
SELECT
    DATE(created_at) as date,
    COUNT(*) as total_files,
    COUNT(CASE WHEN processing_status = 'completed' THEN 1 END) as completed_files,
    COUNT(CASE WHEN processing_status = 'failed' THEN 1 END) as failed_files,
    COUNT(CASE WHEN processing_status = 'processing' THEN 1 END) as processing_files,
    ROUND(
        COUNT(CASE WHEN processing_status = 'completed' THEN 1 END) * 100.0 /
        NULLIF(COUNT(*), 0),
        2
    ) as success_rate
FROM multimodal_files
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- 授权（如果需要）
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO athena_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO athena_user;

-- 输出完成信息
SELECT 'Multimodal file system database initialization completed!' as message;