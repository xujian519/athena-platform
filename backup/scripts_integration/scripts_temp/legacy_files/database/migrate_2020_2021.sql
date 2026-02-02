-- 迁移2020年和2021年数据从简化表到完整表
-- 修正版：只使用patents_simple表中实际存在的字段

-- 迁移2020年数据
INSERT INTO patents (
    patent_name,
    patent_type,
    application_number,
    application_date,
    publication_number,
    publication_date,
    authorization_number,
    authorization_date,
    applicant,
    applicant_type,
    applicant_address,
    applicant_region,
    applicant_city,
    applicant_district,
    current_assignee,
    current_assignee_address,
    assignee_type,
    credit_code,
    inventor,
    ipc_code,
    ipc_main_class,
    ipc_classification,
    abstract,
    claims_content,
    claims,
    citation_count,
    cited_count,
    self_citation_count,
    other_citation_count,
    cited_by_self_count,
    cited_by_others_count,
    family_citation_count,
    family_cited_count,
    source_year,
    source_file,
    file_hash
)
SELECT
    ps.patent_name,
    ps.patent_type,
    ps.application_number,
    ps.application_date,
    NULL as publication_number,  -- 简化表中没有此字段
    NULL as publication_date,  -- 简化表中没有此字段
    NULL as authorization_number,  -- 简化表中没有此字段
    NULL as authorization_date,  -- 简化表中没有此字段
    ps.applicant,
    NULL as applicant_type,  -- 简化表中没有此字段
    NULL as applicant_address,  -- 简化表中没有此字段
    NULL as applicant_region,  -- 简化表中没有此字段
    NULL as applicant_city,  -- 简化表中没有此字段
    NULL as applicant_district,  -- 简化表中没有此字段
    NULL as current_assignee,  -- 简化表中没有此字段
    NULL as current_assignee_address,  -- 简化表中没有此字段
    NULL as assignee_type,  -- 简化表中没有此字段
    NULL as credit_code,  -- 简化表中没有此字段
    ps.inventor,
    ps.ipc_code,
    CASE
        WHEN ps.ipc_code IS NOT NULL AND LENGTH(ps.ipc_code) >= 4
        THEN SUBSTRING(ps.ipc_code, 1, 4)
        ELSE NULL
    END as ipc_main_class,
    ps.ipc_code as ipc_classification,
    ps.abstract,
    NULL as claims_content,  -- 简化表中没有此字段
    NULL as claims,  -- 简化表中没有此字段
    0 as citation_count,
    0 as cited_count,
    0 as self_citation_count,
    0 as other_citation_count,
    0 as cited_by_self_count,
    0 as cited_by_others_count,
    0 as family_citation_count,
    0 as family_cited_count,
    ps.source_year,
    '中国专利数据库' || ps.source_year || '年.csv' as source_file,
    NULL as file_hash
FROM patents_simple ps
WHERE ps.source_year = 2020
ON CONFLICT (application_number) DO NOTHING;

-- 输出2020年迁移数量
DO $$
DECLARE
    count_val integer;
BEGIN
    SELECT COUNT(*) INTO count_val FROM patents WHERE source_year = 2020;
    RAISE NOTICE '✅ 2020年数据迁移完成，共迁移 % 条记录', count_val;
END $$;

-- 迁移2021年数据
INSERT INTO patents (
    patent_name,
    patent_type,
    application_number,
    application_date,
    publication_number,
    publication_date,
    authorization_number,
    authorization_date,
    applicant,
    applicant_type,
    applicant_address,
    applicant_region,
    applicant_city,
    applicant_district,
    current_assignee,
    current_assignee_address,
    assignee_type,
    credit_code,
    inventor,
    ipc_code,
    ipc_main_class,
    ipc_classification,
    abstract,
    claims_content,
    claims,
    citation_count,
    cited_count,
    self_citation_count,
    other_citation_count,
    cited_by_self_count,
    cited_by_others_count,
    family_citation_count,
    family_cited_count,
    source_year,
    source_file,
    file_hash
)
SELECT
    ps.patent_name,
    ps.patent_type,
    ps.application_number,
    ps.application_date,
    NULL as publication_number,  -- 简化表中没有此字段
    NULL as publication_date,  -- 简化表中没有此字段
    NULL as authorization_number,  -- 简化表中没有此字段
    NULL as authorization_date,  -- 简化表中没有此字段
    ps.applicant,
    NULL as applicant_type,  -- 简化表中没有此字段
    NULL as applicant_address,  -- 简化表中没有此字段
    NULL as applicant_region,  -- 简化表中没有此字段
    NULL as applicant_city,  -- 简化表中没有此字段
    NULL as applicant_district,  -- 简化表中没有此字段
    NULL as current_assignee,  -- 简化表中没有此字段
    NULL as current_assignee_address,  -- 简化表中没有此字段
    NULL as assignee_type,  -- 简化表中没有此字段
    NULL as credit_code,  -- 简化表中没有此字段
    ps.inventor,
    ps.ipc_code,
    CASE
        WHEN ps.ipc_code IS NOT NULL AND LENGTH(ps.ipc_code) >= 4
        THEN SUBSTRING(ps.ipc_code, 1, 4)
        ELSE NULL
    END as ipc_main_class,
    ps.ipc_code as ipc_classification,
    ps.abstract,
    NULL as claims_content,  -- 简化表中没有此字段
    NULL as claims,  -- 简化表中没有此字段
    0 as citation_count,
    0 as cited_count,
    0 as self_citation_count,
    0 as other_citation_count,
    0 as cited_by_self_count,
    0 as cited_by_others_count,
    0 as family_citation_count,
    0 as family_cited_count,
    ps.source_year,
    '中国专利数据库' || ps.source_year || '年.csv' as source_file,
    NULL as file_hash
FROM patents_simple ps
WHERE ps.source_year = 2021
ON CONFLICT (application_number) DO NOTHING;

-- 输出2021年迁移数量
DO $$
DECLARE
    count_val integer;
BEGIN
    SELECT COUNT(*) INTO count_val FROM patents WHERE source_year = 2021;
    RAISE NOTICE '✅ 2021年数据迁移完成，共迁移 % 条记录', count_val;
END $$;

-- 输出总计
DO $$
DECLARE
    count_2020 integer;
    count_2021 integer;
BEGIN
    SELECT COUNT(*) INTO count_2020 FROM patents WHERE source_year = 2020;
    SELECT COUNT(*) INTO count_2021 FROM patents WHERE source_year = 2021;
    RAISE NOTICE '📊 迁移总计：2020年 % 条，2021年 % 条', count_2020, count_2021;
END $$;