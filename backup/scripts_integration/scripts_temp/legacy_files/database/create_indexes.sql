-- 专利数据库索引优化脚本
-- 针对中国专利数据的查询特点优化
-- 作者: 徐健
-- 创建日期: 2025-12-13

-- =============================================================================
-- 性能优化提示
-- =============================================================================
-- 运行前请确保：
-- 1. 数据库配置已优化（参考postgresql_local.conf）
-- 2. 已加载必要的扩展（pg_trgm, btree_gin等）
-- 3. 数据量较大时，建议在低峰期执行
-- 4. 考虑使用CONCURRENTLY选项避免锁表

-- =============================================================================
-- 基础索引优化（已经在建表时创建的索引补充）
-- =============================================================================

-- 专利表复合索引
-- 用于常见的查询组合
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patents_type_status ON patents(patent_type, status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patents_date_active ON patents(application_date DESC, is_active) WHERE is_active = true;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patents_ipc_type ON patents(main_ipc, patent_type);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patents_value_date ON patents(patent_value_score DESC, application_date DESC);

-- 专利参与人表索引优化
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_participants_patent_type ON patent_participants(patent_id, participant_type);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_participants_name_type ON patent_participants(participant_name, participant_type);

-- 引用关系索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_citations_composite ON patent_citations(citing_patent_id, citation_type, patent_citations.cited_patent_id);

-- =============================================================================
-- 全文搜索索引优化
-- =============================================================================

-- 为中文全文搜索创建特殊索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patents_title_zh_gin ON patents USING GIN(to_tsvector('chinese', title_zh));
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patents_abstract_zh_gin ON patents USING GIN(to_tsvector('chinese', abstract_zh));

-- 三元组索引（用于模糊搜索）
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patents_title_trgm ON patents USING GIN(title_zh gin_trgm_ops);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patents_abstract_trgm ON patents USING GIN(abstract_zh gin_trgm_ops);

-- 关键词数组索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patents_keywords_gin ON patents USING GIN(keywords);

-- 发明人和申请人数组索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patents_inventors_gin ON patents USING GIN(inventors);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patents_applicants_gin ON patents USING GIN(applicants);

-- =============================================================================
-- 分类索引优化
-- =============================================================================

-- IPC分类层次索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patents_ipc_path ON patents USING GIN(string_to_array(main_ipc, '/') text[]);

-- CPC分类数组索引（GIN索引支持数组搜索）
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patents_cpc_gin ON patents USING GIN(cpc_classifications);

-- 技术领域全文搜索索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patents_field_gin ON patents USING GIN(to_tsvector('chinese', technical_field));

-- =============================================================================
-- 时间相关索引优化
-- =============================================================================

-- 专利生命周期时间轴索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patents_timeline ON patents(application_date, publication_date, grant_date);

-- 最近申请的专利（热数据）
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patents_recent ON patents(application_date DESC) WHERE application_date > (CURRENT_DATE - INTERVAL '2 years');

-- 即将到期的专利
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patents_expiring_soon ON patents(expiry_date)
WHERE expiry_date IS NOT NULL AND expiry_date BETWEEN CURRENT_DATE AND (CURRENT_DATE + INTERVAL '1 year');

-- =============================================================================
-- 统计和分析索引
-- =============================================================================

-- 专利价值分析索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patents_value_composite ON patents(patent_type, patent_value_score DESC);

-- 活跃专利统计索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patents_active_stats ON patents(patent_type, status)
WHERE is_active = true AND status = 'granted';

-- 法律状态历史时间线索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_legal_history_timeline ON patent_legal_history(patent_id, event_date DESC);

-- 诉讼案件时间索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_litigations_date ON patent_litigations(case_date DESC, case_type);

-- 许可交易时间索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_licenses_date_range ON patent_licenses(start_date, end_date);

-- =============================================================================
-- 分区表索引（如果使用了分区表）
-- =============================================================================

/*
-- 示例：为分区表创建局部索引
CREATE INDEX idx_patents_2020_type ON patents_2020(patent_type);
CREATE INDEX idx_patents_2021_type ON patents_2021(patent_type);
CREATE INDEX idx_patents_2022_type ON patents_2022(patent_type);
CREATE INDEX idx_patents_2023_type ON patents_2023(patent_type);
CREATE INDEX idx_patents_2024_type ON patents_2024(patent_type);

-- 跨分区全局索引（PostgreSQL 10+）
CREATE INDEX idx_patents_global_number ON ALL PARTITIONS(patent_number);
CREATE INDEX idx_patents_global_date ON ALL PARTITIONS(application_date DESC);
*/

-- =============================================================================
-- 部分索引（针对特定查询场景优化）
-- =============================================================================

-- 只索引活跃专利（减少索引大小）
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patents_active_number ON patents(patent_number)
WHERE is_active = true;

-- 只索引已授权专利
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patents_granted_ipc ON patents(main_ipc, grant_date DESC)
WHERE status = 'granted' AND grant_date IS NOT NULL;

-- 只索引有价值专利（top 20%）
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patents_high_value ON patents(patent_number, patent_value_score)
WHERE patent_value_score >= 8.0;

-- 只索引专利族主专利
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patents_family_primary ON patents(patent_number, family_id)
WHERE family_id IS NOT NULL;

-- =============================================================================
-- 表达式索引（针对特定计算字段）
-- =============================================================================

-- 专利有效期剩余天数索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patents_days_left ON patents(((expiry_date - CURRENT_DATE)))
WHERE expiry_date IS NOT NULL;

-- 专利年龄索引（申请后的年数）
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patents_age ON patents(((CURRENT_DATE - application_date) / 365));

-- 发明人数量索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patents_inventor_count ON patents((array_length(inventors, 1)));

-- 引用次数索引（需要统计视图）
-- 首先创建引用次数视图
CREATE OR REPLACE VIEW patent_citation_stats AS
SELECT
    cited_patent_id,
    COUNT(*) as citation_count,
    MAX(event_date) as last_citation_date
FROM patent_citations
WHERE citation_type = 'backward'
GROUP BY cited_patent_id;

-- 然后创建物化视图以提高性能
CREATE MATERIALIZED VIEW mv_patent_citation_stats AS
SELECT * FROM patent_citation_stats;

-- 为物化视图创建索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_mv_citation_stats_count ON mv_patent_citation_stats(citation_count DESC);
CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS idx_mv_citation_stats_patent ON mv_patent_citation_stats(cited_patent_id);

-- =============================================================================
-- JSONB字段索引（针对引用等复杂字段）
-- =============================================================================

-- 专利引用详情索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patents_citations_gin ON patents USING GIN(citations);

-- 特定JSON路径索引（PostgreSQL 12+）
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patents_backward_citations ON patents
USING GIN((citations->'backward'));

-- =============================================================================
-- 覆盖索引（包含查询所需的所有列）
-- =============================================================================

-- 专利列表查询覆盖索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patents_covering_list ON patents(patent_type, status)
INCLUDE (patent_number, title_zh, application_date, grant_date, patent_value_score);

-- 专利详情查询覆盖索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patents_covering_detail ON patents(patent_number)
INCLUDE (patent_type, status, title_zh, abstract_zh, application_date, grant_date, inventors, applicants);

-- =============================================================================
-- 自定义索引类型
-- =============================================================================

-- 专利相似度搜索索引（使用pg_trgm）
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 为标题和摘要创建相似度索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patents_title_similarity ON patents USING GIN(title_zh gin_trgm_ops);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patents_abstract_similarity ON patents USING GIN(abstract_zh gin_trgm_ops);

-- 范围索引优化（PostgreSQL 9.2+）
ALTER INDEX idx_patents_value_date ALTER COLUMN patent_value_score SET STATISTICS 1000;

-- =============================================================================
-- 并行创建索引配置
-- =============================================================================

-- 设置并行度（根据CPU核心数调整）
-- 注意：这会影响整个会话，谨慎使用
-- SET maintenance_work_mem = '1GB';
-- SET max_parallel_maintenance_workers = 4;

-- =============================================================================
-- 索引维护任务
-- =============================================================================

-- 创建索引重建函数
CREATE OR REPLACE FUNCTION rebuild_indexes()
RETURNS void AS $$
DECLARE
    idx_record RECORD;
BEGIN
    -- 重建所有需要维护的索引
    FOR idx_record IN
        SELECT schemaname, tablename, indexname
        FROM pg_indexes
        WHERE schemaname = 'public'
          AND (indexname LIKE '%_trgm' OR indexname LIKE '%_gin%')
    LOOP
        RAISE NOTICE '重建索引: %', idx_record.indexname;
        EXECUTE 'REINDEX INDEX CONCURRENTLY ' || idx_record.indexname;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- 创建索引统计信息更新函数
CREATE OR REPLACE FUNCTION update_index_stats()
RETURNS void AS $$
BEGIN
    -- 更新表统计信息
    ANALYZE patents;
    ANALYZE patent_citations;
    ANALYZE patent_legal_history;
    ANALYZE patent_participants;
    ANALYZE patent_litigations;
    ANALYZE patent_licenses;

    -- 更新物化视图
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_patent_citation_stats;

    RAISE NOTICE '索引统计信息更新完成';
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 性能监控查询
-- =============================================================================

-- 创建索引使用情况监控视图
CREATE OR REPLACE VIEW index_usage_stats AS
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- 创建表大小监控视图
CREATE OR REPLACE VIEW table_size_stats AS
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY size_bytes DESC;

-- =============================================================================
-- 完成提示
-- =============================================================================

-- 输出索引创建完成信息
DO $$
BEGIN
    RAISE NOTICE '=====================================';
    RAISE NOTICE '专利数据库索引优化完成！';
    RAISE NOTICE '=====================================';
    RAISE NOTICE '已创建的索引类型：';
    RAISE NOTICE '1. 基础索引 - 单列和复合索引';
    RAISE NOTICE '2. 全文搜索索引 - 中文搜索优化';
    RAISE NOTICE '3. 数组索引 - GIN索引优化';
    RAISE NOTICE '4. 部分索引 - 条件索引优化';
    RAISE NOTICE '5. 表达式索引 - 计算字段索引';
    RAISE NOTICE '6. 覆盖索引 - 查询性能优化';
    RAISE NOTICE '7. 物化视图 - 统计查询优化';
    RAISE NOTICE '';
    RAISE NOTICE '性能建议：';
    RAISE NOTICE '1. 定期执行 ANALYZE 更新统计信息';
    RAISE NOTICE '2. 监控索引使用情况，删除无用索引';
    RAISE NOTICE '3. 定期重建频繁更新的索引';
    RAISE NOTICE '4. 调整maintenance_work_mem优化索引创建';
    RAISE NOTICE '5. 考虑使用分区表处理大量历史数据';
    RAISE NOTICE '';
    RAISE NOTICE '可用函数：';
    RAISE NOTICE '- rebuild_indexes() - 重建索引';
    RAISE NOTICE '- update_index_stats() - 更新统计信息';
    RAISE NOTICE '=====================================';
END $$;