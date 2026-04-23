-- 专利数据库表创建脚本
-- 用于支持本地PostgreSQL专利检索功能
--
-- 使用方法:
--   docker exec -i athena-postgres psql -U athena -d athena < scripts/create_patent_tables.sql
--
-- 或在psql中:
--   \i scripts/create_patent_tables.sql

-- ============================================
-- 1. 创建专利数据库
-- ============================================

SELECT 'CREATE DATABASE patent_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'patent_db')\gexec

\c patent_db

-- ============================================
-- 2. 创建专利主表
-- ============================================

CREATE TABLE IF NOT EXISTS patents (
    -- 主键
    id SERIAL PRIMARY KEY,

    -- 专利基本信息
    patent_id VARCHAR(100) UNIQUE NOT NULL,           -- 专利号（如：US20230012345A1）
    title TEXT,                                       -- 标题
    abstract TEXT,                                    -- 摘要
    publication_date DATE,                            -- 公开日期
    filing_date DATE,                                 -- 申请日期
    priority_date DATE,                               -- 优先权日期

    -- 申请人信息
    applicant VARCHAR(500),                           -- 申请人
    inventor VARCHAR(1000),                           -- 发明人（多个用分号分隔）
    assignee VARCHAR(500),                            -- 受让人

    -- 专利内容
    claims TEXT,                                      -- 权利要求书
    description TEXT,                                 -- 说明书
    full_text TEXT,                                   -- 全文

    -- 分类和状态
    classification VARCHAR(100),                      -- 专利分类号（IPC/CPC）
    legal_status VARCHAR(50),                         -- 法律状态

    -- 同族和引文
    family_id VARCHAR(100),                           -- 同族ID
    family_members TEXT,                              -- 同族成员（JSON格式）
    citations TEXT,                                   -- 引用文献（JSON格式）

    -- 元数据
    source VARCHAR(100),                              -- 数据来源（google_patents, local_import等）
    url TEXT,                                         -- 原始URL
    relevance_score FLOAT,                            -- 相关性评分（用于排序）
    search_query TEXT,                                -- 检索查询（用于审计）

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP   -- 上次索引更新时间
);

-- 添加注释
COMMENT ON TABLE patents IS '专利主表 - 存储所有专利的基本信息和内容';
COMMENT ON COLUMN patents.patent_id IS '专利号，唯一标识符';
COMMENT ON COLUMN patents.family_members IS '同族成员列表，JSON格式: [{"patent_id": "CNxxx", "country": "CN"}]';
COMMENT ON COLUMN patents.citations IS '引用文献列表，JSON格式: [{"patent_id": "USxxx", "type": "forward"}]';

-- ============================================
-- 3. 创建全文检索索引
-- ============================================

-- 中文全文检索配置
CREATE TEXT SEARCH CONFIGURATION IF NOT EXISTS chinese (COPY = simple);

-- 标题全文索引
CREATE INDEX IF NOT EXISTS idx_patents_title_gin
ON patents USING gin(to_tsvector('chinese', title));

-- 摘要全文索引
CREATE INDEX IF NOT EXISTS idx_patents_abstract_gin
ON patents USING gin(to_tsvector('chinese', abstract));

-- 说明书全文索引
CREATE INDEX IF NOT EXISTS idx_patents_description_gin
ON patents USING gin(to_tsvector('chinese', description));

-- 权利要求书全文索引
CREATE INDEX IF NOT EXISTS idx_patents_claims_gin
ON patents USING gin(to_tsvector('chinese', claims));

-- ============================================
-- 4. 创建常用查询索引
-- ============================================

-- 专利号索引（用于精确查找）
CREATE INDEX IF NOT EXISTS idx_patents_patent_id
ON patents(patent_id);

-- 申请日期索引（用于时间范围查询）
CREATE INDEX IF NOT EXISTS idx_patents_filing_date
ON patents(filing_date);

-- 公开日期索引（用于时间范围查询）
CREATE INDEX IF NOT EXISTS idx_patents_publication_date
ON patents(publication_date);

-- 申请人索引（用于申请人查询）
CREATE INDEX IF NOT EXISTS idx_patents_applicant
ON patents(applicant);

-- 分类号索引（用于分类查询）
CREATE INDEX IF NOT EXISTS idx_patents_classification
ON patents(classification);

-- 来源索引（用于数据来源过滤）
CREATE INDEX IF NOT EXISTS idx_patents_source
ON patents(source);

-- 相关性评分索引（用于排序）
CREATE INDEX IF NOT EXISTS idx_patents_relevance_score
ON patents(relevance_score DESC);

-- 复合索引：申请人 + 申请日期（常用组合查询）
CREATE INDEX IF NOT EXISTS idx_patents_applicant_filing_date
ON patents(applicant, filing_date DESC);

-- ============================================
-- 5. 创建更新触发器
-- ============================================

-- 自动更新 updated_at 字段的函数
CREATE OR REPLACE FUNCTION update_patents_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 创建触发器
DROP TRIGGER IF EXISTS trigger_update_patents_updated_at ON patents;
CREATE TRIGGER trigger_update_patents_updated_at
BEFORE UPDATE ON patents
FOR EACH ROW
EXECUTE FUNCTION update_patents_updated_at();

-- 自动更新 indexed_at 字段的函数
CREATE OR REPLACE FUNCTION update_patents_indexed_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.indexed_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 创建触发器（在内容字段更新时）
DROP TRIGGER IF EXISTS trigger_update_patents_indexed_at ON patents;
CREATE TRIGGER trigger_update_patents_indexed_at
BEFORE UPDATE OF title, abstract, description, claims ON patents
FOR EACH ROW
EXECUTE FUNCTION update_patents_indexed_at();

-- ============================================
-- 6. 创建辅助视图
-- ============================================

-- 专利摘要视图（用于快速浏览）
CREATE OR REPLACE VIEW patent_summary AS
SELECT
    id,
    patent_id,
    title,
    abstract,
    publication_date,
    applicant,
    classification,
    source,
    relevance_score,
    created_at
FROM patents
ORDER BY publication_date DESC;

COMMENT ON VIEW patent_summary IS '专利摘要视图 - 用于快速浏览和列表展示';

-- 专利统计视图（用于数据分析）
CREATE OR REPLACE VIEW patent_statistics AS
SELECT
    DATE_TRUNC('month', publication_date) AS month,
    COUNT(*) AS count,
    COUNT(DISTINCT applicant) AS unique_applicants,
    AVG(relevance_score) AS avg_relevance
FROM patents
WHERE publication_date IS NOT NULL
GROUP BY DATE_TRUNC('month', publication_date)
ORDER BY month DESC;

COMMENT ON VIEW patent_statistics IS '专利统计视图 - 按月统计专利数量和申请人';

-- ============================================
-- 7. 插入测试数据（可选）
-- ============================================

-- 检查是否为空表，如果为空则插入测试数据
DO $$
DECLARE
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count FROM patents;

    IF table_count = 0 THEN
        INSERT INTO patents (
            patent_id, title, abstract, publication_date,
            applicant, inventor, classification, source, url
        ) VALUES
        (
            'US20230012345A1',
            'Example Patent Title',
            'This is an example patent abstract for testing purposes.',
            '2023-01-01',
            'Example Applicant Inc.',
            'John Doe; Jane Smith',
            'G06N 3/00',
            'test_data',
            'https://patents.google.com/patent/US20230012345A1'
        );

        RAISE NOTICE '✅ 测试数据已插入';
    ELSE
        RAISE NOTICE 'ℹ️  表中已有数据，跳过测试数据插入';
    END IF;
END $$;

-- ============================================
-- 8. 授予权限（根据实际用户调整）
-- ============================================

-- 授予athena用户所有权限
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO athena;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO athena;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO athena;

-- ============================================
-- 9. 显示创建结果
-- ============================================

-- 显示表信息
SELECT
    'patent_db' AS database_name,
    'patents' AS table_name,
    COUNT(*) AS row_count,
    pg_size_pretty(pg_total_relation_size('patents')) AS table_size
FROM patents;

-- 显示索引信息
SELECT
    indexname AS index_name,
    indexdef AS index_definition
FROM pg_indexes
WHERE tablename = 'patents'
ORDER BY indexname;

-- ============================================
-- 完成
-- ============================================

DO $$
BEGIN
    RAISE NOTICE '═══════════════════════════════════════════════';
    RAISE NOTICE '✅ 专利数据库表创建完成';
    RAISE NOTICE '═══════════════════════════════════════════════';
    RAISE NOTICE '📊 数据库: patent_db';
    RAISE NOTICE '📋 主表: patents';
    RAISE NOTICE '🔍 索引: 9个全文索引 + 7个常规索引';
    RAISE NOTICE '👁️  视图: patent_summary, patent_statistics';
    RAISE NOTICE '🔧 触发器: 自动更新时间戳';
    RAISE NOTICE '';
    RAISE NOTICE '🚀 下一步:';
    RAISE NOTICE '  1. 导入专利数据到patents表';
    RAISE NOTICE '  2. 使用统一接口进行检索';
    RAISE NOTICE '     from core.tools.patent_retrieval import search_local_patents';
    RAISE NOTICE '     results = await search_local_patents("深度学习")';
    RAISE NOTICE '═══════════════════════════════════════════════';
END $$;
