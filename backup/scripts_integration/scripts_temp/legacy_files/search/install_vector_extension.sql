-- PostgreSQL向量扩展安装脚本
-- Patent Database Vector Extension Setup

-- 检查pgvector是否已安装
SELECT name, default_version, installed_version
FROM pg_available_extensions
WHERE name = 'vector';

-- 如果未安装，执行安装（需要superuser权限）
-- CREATE EXTENSION IF NOT EXISTS vector;

-- 安装后验证
SELECT 'pgvector extension installed successfully' as status;

-- 查看扩展信息
\dx vector

-- 创建向量字段（768维，适合BERT模型）
ALTER TABLE patents
ADD COLUMN IF NOT EXISTS embedding_title VECTOR(768),
ADD COLUMN IF NOT EXISTS embedding_abstract VECTOR(768),
ADD COLUMN IF NOT EXISTS embedding_claims VECTOR(768),
ADD COLUMN IF NOT EXISTS embedding_combined VECTOR(768);

-- 添加向量字段注释
COMMENT ON COLUMN patents.embedding_title IS '标题向量，用于语义检索';
COMMENT ON COLUMN patents.embedding_abstract IS '摘要向量，用于语义检索';
COMMENT ON COLUMN patents.embedding_claims IS '权利要求向量，用于语义检索';
COMMENT ON COLUMN patents.embedding_combined IS '组合向量，用于综合检索';

-- 创建向量索引（使用HNSW算法，适合大规模数据）
-- 注意：索引创建需要较长时间，建议分批进行

-- 1. 标题向量索引（优先级最高）
CREATE INDEX CONCURRENTLY idx_patents_embedding_title_hnsw
ON patents USING hnsw (embedding_title vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- 2. 摘要向量索引（重要度最高）
CREATE INDEX CONCURRENTLY idx_patents_embedding_abstract_hnsw
ON patents USING hnsw (embedding_abstract vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- 3. 权利要求向量索引
CREATE INDEX CONCURRENTLY idx_patents_embedding_claims_hnsw
ON patents USING hnsw (embedding_claims vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- 4. 组合向量索引
CREATE INDEX CONCURRENTLY idx_patents_embedding_combined_hnsw
ON patents USING hnsw (embedding_combined vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- 创建向量检索辅助函数
CREATE OR REPLACE FUNCTION vector_cosine_similarity(a VECTOR, b VECTOR)
RETURNS FLOAT AS $$
BEGIN
    RETURN 1 - (a <=> b);
END;
$$ LANGUAGE plpgsql;

-- 创建向量搜索视图（仅包含已向量化的记录）
CREATE OR REPLACE VIEW patents_vectorized AS
SELECT
    id,
    patent_name,
    abstract,
    claims_content,
    applicant,
    ipc_main_class,
    patent_type,
    source_year,
    embedding_title,
    embedding_abstract,
    embedding_claims,
    embedding_combined
FROM patents
WHERE embedding_abstract IS NOT NULL;

-- 设置向量搜索参数（优化性能）
SET hnsw.ef_search = 64;
SET max_parallel_workers_per_gather = 4;

-- 创建向量搜索结果表
CREATE TABLE IF NOT EXISTS patent_search_logs (
    id SERIAL PRIMARY KEY,
    query TEXT NOT NULL,
    query_vector VECTOR(768),
    search_type VARCHAR(50),
    results_count INTEGER,
    execution_time_ms FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建搜索日志索引
CREATE INDEX IF NOT EXISTS idx_patent_search_logs_created_at
ON patent_search_logs (created_at DESC);

-- 显示安装完成信息
SELECT
    'Vector Extension Setup Complete' as status,
    'Ready for Patent Vector Search' as message,
    (SELECT COUNT(*) FROM patents WHERE abstract IS NOT NULL) as records_ready_for_vectorization;