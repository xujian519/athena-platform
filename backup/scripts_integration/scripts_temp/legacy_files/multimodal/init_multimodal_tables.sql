-- 多模态文件系统表结构
-- 集成到Athena业务数据库

-- 创建多模态文件主表
CREATE TABLE IF NOT EXISTS multimodal_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100),
    storage_path VARCHAR(500) NOT NULL,
    file_hash VARCHAR(64) UNIQUE,  -- SHA256 hash for deduplication
    uploaded_by VARCHAR(100) DEFAULT 'system',
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 处理状态
    processed BOOLEAN DEFAULT FALSE,
    processing_status VARCHAR(50) DEFAULT 'pending',
    processing_error TEXT,

    -- 元数据
    metadata JSONB DEFAULT '{}',
    extracted_text TEXT,
    thumbnail_path VARCHAR(500),

    -- 标签和分类
    tags TEXT[] DEFAULT '{}',
    category VARCHAR(100),

    -- 向量存储
    vector_id UUID,

    -- 访问统计
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP,

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建文件处理任务表
CREATE TABLE IF NOT EXISTS file_processing_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID NOT NULL REFERENCES multimodal_files(id) ON DELETE CASCADE,
    task_type VARCHAR(50) NOT NULL,  -- extract_text, generate_thumbnail, analyze_content
    status VARCHAR(50) DEFAULT 'pending',  -- pending, running, completed, failed
    progress INTEGER DEFAULT 0,  -- 0-100
    result JSONB DEFAULT '{}',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- 创建文件访问日志表
CREATE TABLE IF NOT EXISTS file_access_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID NOT NULL REFERENCES multimodal_files(id) ON DELETE CASCADE,
    access_type VARCHAR(50),  -- view, download, edit
    accessed_by VARCHAR(100),
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_multimodal_files_type ON multimodal_files(file_type);
CREATE INDEX IF NOT EXISTS idx_multimodal_files_upload_time ON multimodal_files(upload_time);
CREATE INDEX IF NOT EXISTS idx_multimodal_files_processed ON multimodal_files(processed);
CREATE INDEX IF NOT EXISTS idx_multimodal_files_tags ON multimodal_files USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_multimodal_files_category ON multimodal_files(category);
CREATE INDEX IF NOT EXISTS idx_multimodal_files_hash ON multimodal_files(file_hash);
CREATE INDEX IF NOT EXISTS idx_multimodal_files_uploaded_by ON multimodal_files(uploaded_by);

-- 创建任务索引
CREATE INDEX IF NOT EXISTS idx_processing_tasks_file_id ON file_processing_tasks(file_id);
CREATE INDEX IF NOT EXISTS idx_processing_tasks_status ON file_processing_tasks(status);
CREATE INDEX IF NOT EXISTS idx_processing_tasks_type ON file_processing_tasks(task_type);

-- 创建访问日志索引
CREATE INDEX IF NOT EXISTS idx_access_logs_file_id ON file_access_logs(file_id);
CREATE INDEX IF NOT EXISTS idx_access_logs_created_at ON file_access_logs(created_at);

-- 创建触发器：自动更新updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_multimodal_files_updated_at
    BEFORE UPDATE ON multimodal_files
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 插入一些示例数据（可选）
INSERT INTO multimodal_files (filename, original_filename, file_type, file_size, mime_type, storage_path, processed) VALUES
('example.png', '示例图片.png', 'image', 1024, 'image/png', '/storage/images/example.png', FALSE)
ON CONFLICT DO NOTHING;

-- 创建视图：文件统计
CREATE OR REPLACE VIEW multimodal_file_stats AS
SELECT
    file_type,
    COUNT(*) as total_files,
    SUM(file_size) as total_size,
    COUNT(CASE WHEN processed = TRUE THEN 1 END) as processed_files,
    COUNT(CASE WHEN processed = FALSE THEN 1 END) as pending_files,
    MAX(upload_time) as last_upload
FROM multimodal_files
GROUP BY file_type;

-- 创建视图：处理任务统计
CREATE OR REPLACE VIEW processing_task_stats AS
SELECT
    task_type,
    status,
    COUNT(*) as task_count,
    AVG(progress) as avg_progress,
    MAX(created_at) as last_task
FROM file_processing_tasks
GROUP BY task_type, status;

-- 创建存储过程：清理临时文件
CREATE OR REPLACE FUNCTION cleanup_temp_files(days_old INTEGER DEFAULT 7)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM file_access_logs
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '1 day' * days_old;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;