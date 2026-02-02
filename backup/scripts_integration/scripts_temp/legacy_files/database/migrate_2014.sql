-- 迁移2014年数据从简化表到完整表

INSERT INTO patents (
    patent_name, patent_type, application_number, application_date,
    publication_number, publication_date, authorization_number,
    authorization_date, applicant, applicant_type, applicant_address,
    applicant_region, applicant_city, applicant_district,
    current_assignee, current_assignee_address, assignee_type,
    credit_code, inventor, ipc_code, ipc_main_class,
    ipc_classification, abstract, claims_content, claims,
    citation_count, cited_count, self_citation_count,
    other_citation_count, cited_by_self_count, cited_by_others_count,
    family_citation_count, family_cited_count,
    source_year, source_file, file_hash
)
SELECT
    ps.patent_name,
    ps.patent_type,
    ps.application_number,
    ps.application_date,
    NULL as publication_number,
    NULL as publication_date,
    NULL as authorization_number,
    NULL as authorization_date,
    ps.applicant,
    NULL as applicant_type,
    NULL as applicant_address,
    NULL as applicant_region,
    NULL as applicant_city,
    NULL as applicant_district,
    NULL as current_assignee,
    NULL as current_assignee_address,
    NULL as assignee_type,
    NULL as credit_code,
    ps.inventor,
    ps.ipc_code,
    CASE
        WHEN ps.ipc_code IS NOT NULL AND LENGTH(ps.ipc_code) >= 4
        THEN SUBSTRING(ps.ipc_code, 1, 4)
        ELSE NULL
    END as ipc_main_class,
    ps.ipc_code as ipc_classification,
    ps.abstract,
    NULL as claims_content,
    NULL as claims,
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
WHERE ps.source_year = 2014
ON CONFLICT (application_number) DO NOTHING;