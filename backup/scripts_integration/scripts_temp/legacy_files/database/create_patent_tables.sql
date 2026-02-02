-- Athena专利数据库表结构
-- 专门针对中国专利数据优化
-- 作者: 徐健
-- 创建日期: 2025-12-13

-- =============================================================================
-- 创建扩展
-- =============================================================================
-- 注意：这些扩展需要在数据库初始化时安装
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
-- CREATE EXTENSION IF NOT EXISTS pg_trgm;
-- CREATE EXTENSION IF NOT EXISTS pgcrypto;
-- CREATE EXTENSION IF NOT EXISTS btree_gin;
-- CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;

-- =============================================================================
-- 核心专利信息表
-- =============================================================================

-- 专利基础信息表
CREATE TABLE patents (
    id BIGSERIAL PRIMARY KEY,
    -- 基础识别信息
    patent_number VARCHAR(50) UNIQUE NOT NULL,  -- 专利号
    application_number VARCHAR(50) UNIQUE,     -- 申请号
    publication_number VARCHAR(50),            -- 公开号
    grant_number VARCHAR(50),                  -- 授权号

    -- 专利类型
    patent_type VARCHAR(20) NOT NULL,           -- 发明专利/实用新型/外观设计
    patent_subtype VARCHAR(20),                -- 子类型

    -- 申请信息
    application_date DATE NOT NULL,             -- 申请日期
    publication_date DATE,                     -- 公开日期
    grant_date DATE,                           -- 授权日期
    priority_date DATE,                        -- 优先权日期

    -- 有效期信息
    expiry_date DATE,                          -- 失效日期
    is_active BOOLEAN DEFAULT TRUE,            -- 是否有效
    status VARCHAR(20) DEFAULT 'pending',      -- 状态

    -- IPC/CPC分类
    main_ipc VARCHAR(20),                      -- 主IPC分类号
    ipc_versions TEXT[],                       -- IPC版本历史
    cpc_classifications TEXT[],                -- CPC分类

    -- 发明人信息
    inventors TEXT[],                          -- 发明人列表
    applicants TEXT[],                         -- 申请人列表
    assignees TEXT[],                          -- 权利人列表

    -- 代理信息
    agents TEXT[],                             -- 代理人
    agency VARCHAR(200),                      -- 代理机构

    -- 标题和摘要
    title_zh TEXT NOT NULL,                    -- 中文标题
    title_en TEXT,                             -- 英文标题
    abstract_zh TEXT,                          -- 中文摘要
    abstract_en TEXT,                          -- 英文摘要
    claims TEXT,                               -- 权利要求

    -- 全文搜索向量
    title_vector tsvector,                     -- 标题搜索向量
    abstract_vector tsvector,                  -- 摘要搜索向量
    content_vector tsvector,                   -- 内容搜索向量

    -- 技术领域和关键词
    technical_field TEXT,                      -- 技术领域
    keywords TEXT[],                           -- 关键词
    innovation_keywords TEXT[],                -- 创新关键词

    -- 法律状态
    legal_status VARCHAR(50),                 -- 法律状态
    license_status VARCHAR(50),               -- 许可状态
    licensing_parties TEXT[],                 -- 许可方

    -- 引用信息
    citations JSONB,                          -- 引用关系
    backward_citations TEXT[],                -- 后向引用
    forward_citations TEXT[],                 -- 前向引用

    -- 同族专利
    family_id VARCHAR(50),                    -- 专利族ID
    family_members TEXT[],                    -- 族成员

    -- 审查信息
    examiner VARCHAR(100),                    -- 审查员
    examination_report TEXT,                  -- 审查报告
    appeals TEXT,                             -- 复审信息

    -- 价值评估
    patent_value_score DECIMAL(5,2),          -- 专利价值评分
    market_potential DECIMAL(5,2),            -- 市场潜力
    technical_score DECIMAL(5,2),             -- 技术评分

    -- 元数据
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100),
    data_source VARCHAR(50) DEFAULT 'manual', -- 数据来源
    last_verified DATE,                       -- 最后验证日期

    -- 索引和约束
    CONSTRAINT patents_type_check CHECK (patent_type IN ('发明专利', '实用新型', '外观设计')),
    CONSTRAINT patents_status_check CHECK (status IN ('pending', 'published', 'granted', 'expired', 'rejected', 'withdrawn'))
);

-- 创建索引
CREATE INDEX idx_patents_number ON patents(patent_number);
CREATE INDEX idx_patents_application ON patents(application_number);
CREATE INDEX idx_patents_date ON patents(application_date);
CREATE INDEX idx_patents_type ON patents(patent_type);
CREATE INDEX idx_patents_ipc ON patents(main_ipc);
CREATE INDEX idx_patents_status ON patents(status);
CREATE INDEX idx_patents_active ON patents(is_active);
CREATE INDEX idx_patents_title_vector ON patents USING GIN(title_vector);
CREATE INDEX idx_patents_abstract_vector ON patents USING GIN(abstract_vector);
CREATE INDEX idx_patents_keywords ON patents USING GIN(keywords);
CREATE INDEX idx_patents_inventors ON patents USING GIN(inventors);
CREATE INDEX idx_patents_applicants ON patents USING GIN(applicants);
CREATE INDEX idx_patents_cpc ON patents USING GIN(cpc_classifications);

-- =============================================================================
-- 专利法律状态历史表
-- =============================================================================
CREATE TABLE patent_legal_history (
    id BIGSERIAL PRIMARY KEY,
    patent_id BIGINT NOT NULL REFERENCES patents(id) ON DELETE CASCADE,

    event_date DATE NOT NULL,                  -- 事件日期
    event_type VARCHAR(50) NOT NULL,           -- 事件类型
    event_description TEXT,                    -- 事件描述

    -- 费用信息
    fee_type VARCHAR(50),                      -- 费用类型
    fee_amount DECIMAL(10,2),                 -- 费用金额
    fee_paid_date DATE,                       -- 缴费日期

    -- 变更信息
    changed_field VARCHAR(100),               -- 变更字段
    old_value TEXT,                            -- 原值
    new_value TEXT,                            -- 新值

    -- 官方文档
    document_number VARCHAR(50),              -- 官方文档号
    document_date DATE,                        -- 文档日期

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_patent_legal_history_patent_id ON patent_legal_history(patent_id);
CREATE INDEX idx_patent_legal_history_date ON patent_legal_history(event_date);
CREATE INDEX idx_patent_legal_history_type ON patent_legal_history(event_type);

-- =============================================================================
-- 专利分类映射表
-- =============================================================================
CREATE TABLE ipc_cpc_mapping (
    id SERIAL PRIMARY KEY,
    ipc_code VARCHAR(20) NOT NULL,             -- IPC分类号
    cpc_code VARCHAR(20) NOT NULL,            -- CPC分类号
    description TEXT,                          -- 分类描述
    version VARCHAR(10),                       -- 版本
    effective_date DATE,                       -- 生效日期

    UNIQUE(ipc_code, cpc_code, version)
);

CREATE INDEX idx_ipc_cpc_ipc ON ipc_cpc_mapping(ipc_code);
CREATE INDEX idx_ipc_cpc_cpc ON ipc_cpc_mapping(cpc_code);

-- =============================================================================
-- 专利申请人/发明人信息表
-- =============================================================================
CREATE TABLE patent_participants (
    id BIGSERIAL PRIMARY KEY,
    patent_id BIGINT NOT NULL REFERENCES patents(id) ON DELETE CASCADE,

    participant_type VARCHAR(20) NOT NULL,     -- 类型: inventor/applicant/assignee
    participant_name TEXT NOT NULL,            -- 姓名/名称
    participant_name_en TEXT,                  -- 英文姓名
    participant_type_detail VARCHAR(50),       -- 详细类型: individual/company/university

    -- 联系信息
    country VARCHAR(2),                        -- 国家代码
    province VARCHAR(50),                      -- 省/州
    city VARCHAR(50),                          -- 城市
    address TEXT,                              -- 地址

    -- 公司信息（如果是公司）
    company_type VARCHAR(50),                 -- 公司类型
    industry_code VARCHAR(20),                 -- 行业代码

    -- 排序和权重
    sequence_number INTEGER DEFAULT 1,        -- 排序号
    is_primary BOOLEAN DEFAULT FALSE,          -- 是否主要

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT participants_type_check CHECK (participant_type IN ('inventor', 'applicant', 'assignee'))
);

CREATE INDEX idx_participants_patent_id ON patent_participants(patent_id);
CREATE INDEX idx_participants_name ON patent_participants(participant_name);
CREATE INDEX idx_participants_type ON patent_participants(participant_type);
CREATE INDEX idx_participants_country ON patent_participants(country);

-- =============================================================================
-- 专利代理人信息表
-- =============================================================================
CREATE TABLE patent_agents (
    id BIGSERIAL PRIMARY KEY,
    patent_id BIGINT NOT NULL REFERENCES patents(id) ON DELETE CASCADE,

    agent_name TEXT NOT NULL,                  -- 代理人姓名
    agency_name TEXT,                          -- 代理机构名称
    license_number VARCHAR(50),                -- 执业证号

    -- 联系方式
    phone VARCHAR(20),
    email VARCHAR(100),
    address TEXT,

    -- 专业领域
    specialization TEXT[],                      -- 专业领域

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_agents_patent_id ON patent_agents(patent_id);
CREATE INDEX idx_agents_name ON patent_agents(agent_name);
CREATE INDEX idx_agents_agency ON patent_agents(agency_name);

-- =============================================================================
-- 专利引用关系表
-- =============================================================================
CREATE TABLE patent_citations (
    id BIGSERIAL PRIMARY KEY,
    citing_patent_id BIGINT NOT NULL REFERENCES patents(id) ON DELETE CASCADE,
    cited_patent_id BIGINT NOT NULL REFERENCES patents(id) ON DELETE CASCADE,

    citation_type VARCHAR(20) NOT NULL,       -- 引用类型: forward/backward
    citation_context TEXT,                     -- 引用上下文

    -- 引用详情
    citation_date DATE,                        -- 引用日期
    citation_source VARCHAR(100),              -- 引用来源

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(citing_patent_id, cited_patent_id, citation_type),
    CONSTRAINT citations_type_check CHECK (citation_type IN ('forward', 'backward'))
);

CREATE INDEX idx_citations_citing ON patent_citations(citing_patent_id);
CREATE INDEX idx_citations_cited ON patent_citations(cited_patent_id);
CREATE INDEX idx_citations_type ON patent_citations(citation_type);

-- =============================================================================
-- 专利族表
-- =============================================================================
CREATE TABLE patent_families (
    id SERIAL PRIMARY KEY,
    family_id VARCHAR(50) UNIQUE NOT NULL,    -- 专利族ID
    family_type VARCHAR(20),                   -- 族类型

    -- 族信息
    earliest_filing_date DATE,                -- 最早申请日
    priority_country VARCHAR(2),              -- 优先权国家
    priority_number VARCHAR(50),              -- 优先权号

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_families_id ON patent_families(family_id);
CREATE INDEX idx_families_date ON patent_families(earliest_filing_date);

-- 专利族成员表
CREATE TABLE patent_family_members (
    id BIGSERIAL PRIMARY KEY,
    family_id VARCHAR(50) NOT NULL REFERENCES patent_families(family_id),
    patent_id BIGINT NOT NULL REFERENCES patents(id) ON DELETE CASCADE,

    member_type VARCHAR(20),                   -- 成员类型
    relationship TEXT,                         -- 关系描述

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(family_id, patent_id)
);

CREATE INDEX idx_family_members_family ON patent_family_members(family_id);
CREATE INDEX idx_family_members_patent ON patent_family_members(patent_id);

-- =============================================================================
-- 专利诉讼和异议表
-- =============================================================================
CREATE TABLE patent_litigations (
    id BIGSERIAL PRIMARY KEY,
    patent_id BIGINT NOT NULL REFERENCES patents(id) ON DELETE CASCADE,

    case_number VARCHAR(50) UNIQUE,           -- 案件编号
    case_type VARCHAR(50) NOT NULL,            -- 案件类型: 无效宣告/侵权诉讼/异议

    -- 当事人信息
    plaintiff TEXT,                            -- 原告
    defendant TEXT,                            -- 被告

    -- 案件信息
    case_date DATE,                            -- 立案日期
    court VARCHAR(200),                        -- 审理法院
    judge VARCHAR(100),                        -- 审判长

    -- 结果信息
    outcome VARCHAR(100),                      -- 判决结果
    decision_date DATE,                        -- 判决日期
    compensation DECIMAL(15,2),                -- 赔偿金额

    -- 文档信息
    judgment_text TEXT,                        -- 判决书摘要
    related_laws TEXT[],                       -- 相关法条

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_litigations_patent_id ON patent_litigations(patent_id);
CREATE INDEX idx_litigations_case_number ON patent_litigations(case_number);
CREATE INDEX idx_litigations_type ON patent_litigations(case_type);

-- =============================================================================
-- 专利许可交易表
-- =============================================================================
CREATE TABLE patent_licenses (
    id BIGSERIAL PRIMARY KEY,
    patent_id BIGINT NOT NULL REFERENCES patents(id) ON DELETE CASCADE,

    -- 许可信息
    license_type VARCHAR(50) NOT NULL,         -- 许可类型: 独占/排他/普通
    license_status VARCHAR(20) DEFAULT 'active', -- 许可状态

    -- 当事人
    licensor TEXT NOT NULL,                    -- 许可方
    licensee TEXT NOT NULL,                    -- 被许可方

    -- 许可范围
    territory TEXT,                            -- 许可地域
    field_of_use TEXT,                        -- 使用领域

    -- 财务信息
    license_fee DECIMAL(15,2),                -- 许可费
    royalty_rate DECIMAL(5,2),                -- 提成比例
    minimum_royalty DECIMAL(15,2),            -- 最低提成

    -- 期限信息
    start_date DATE NOT NULL,                 -- 起始日期
    end_date DATE,                             -- 终止日期

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_licenses_patent_id ON patent_licenses(patent_id);
CREATE INDEX idx_licenses_status ON patent_licenses(license_status);
CREATE INDEX idx_licenses_type ON patent_licenses(license_type);

-- =============================================================================
-- 专利评估和分析表
-- =============================================================================
CREATE TABLE patent_analytics (
    id BIGSERIAL PRIMARY KEY,
    patent_id BIGINT NOT NULL REFERENCES patents(id) ON DELETE CASCADE,

    -- 分析信息
    analysis_date DATE NOT NULL,               -- 分析日期
    analysis_type VARCHAR(50) NOT NULL,       -- 分析类型

    -- 技术评估
    novelty_score DECIMAL(,2),                -- 新颖性评分
    inventive_step_score DECIMAL(5,2),       -- 创造性评分
    industrial_applicability DECIMAL(5,2),   -- 实用性评分

    -- 市场评估
    market_size DECIMAL(15,2),                -- 市场规模
    market_growth_rate DECIMAL(5,2),          -- 市场增长率
    competitor_count INTEGER,                  -- 竞争者数量

    -- 法律评估
    claim_strength DECIMAL(5,2),              -- 权利要求强度
    infringement_risk DECIMAL(5,2),           -- 侵权风险
    validity_risk DECIMAL(5,2),               -- 无效风险

    -- 综合评分
    overall_score DECIMAL(5,2),               -- 综合评分
    recommendation VARCHAR(200),               -- 建议

    -- 分析师信息
    analyst_id VARCHAR(50),                   -- 分析师ID
    analysis_method TEXT,                      -- 分析方法

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_analytics_patent_id ON patent_analytics(patent_id);
CREATE INDEX idx_analytics_date ON patent_analytics(analysis_date);
CREATE INDEX idx_analytics_type ON patent_analytics(analysis_type);

-- =============================================================================
-- 更新触发器
-- =============================================================================

-- 创建更新时间触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为patents表创建触发器
CREATE TRIGGER update_patents_updated_at
    BEFORE UPDATE ON patents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 创建全文搜索向量更新触发器
CREATE OR REPLACE FUNCTION update_patent_search_vectors()
RETURNS TRIGGER AS $$
BEGIN
    -- 更新标题向量
    NEW.title_vector := to_tsvector('chinese', COALESCE(NEW.title_zh, '') || ' ' || COALESCE(NEW.title_en, ''));

    -- 更新摘要向量
    NEW.abstract_vector := to_tsvector('chinese', COALESCE(NEW.abstract_zh, '') || ' ' || COALESCE(NEW.abstract_en, ''));

    -- 更新内容向量（标题+摘要+关键词）
    NEW.content_vector := setweight(to_tsvector('chinese', COALESCE(NEW.title_zh, '')), 'A') ||
                         setweight(to_tsvector('chinese', COALESCE(NEW.abstract_zh, '')), 'B') ||
                         setweight(to_tsvector('chinese', array_to_string(NEW.keywords, ' ')), 'C');

    RETURN NEW;
END;
$$ language 'plpgsql';

-- 创建触发器
CREATE TRIGGER update_patent_vectors
    BEFORE INSERT OR UPDATE ON patents
    FOR EACH ROW EXECUTE FUNCTION update_patent_search_vectors();

-- =============================================================================
-- 创建视图
-- =============================================================================

-- 专利概览视图
CREATE VIEW patent_overview AS
SELECT
    p.id,
    p.patent_number,
    p.patent_type,
    p.title_zh,
    p.application_date,
    p.grant_date,
    p.status,
    p.main_ipc,
    array_to_string(p.inventors, '; ') as inventors_str,
    array_to_string(p.applicants, '; ') as applicants_str,
    p.patent_value_score,
    p.created_at
FROM patents p;

-- 活跃专利视图
CREATE VIEW active_patents AS
SELECT *
FROM patents
WHERE is_active = true
  AND status IN ('granted', 'published')
  AND (expiry_date IS NULL OR expiry_date > CURRENT_DATE);

-- 专利统计视图
CREATE VIEW patent_statistics AS
SELECT
    patent_type,
    status,
    COUNT(*) as count,
    AVG(patent_value_score) as avg_value_score,
    MIN(application_date) as earliest_date,
    MAX(application_date) as latest_date
FROM patents
GROUP BY patent_type, status;

-- =============================================================================
-- 创建分区表（如果需要处理大量数据）
-- =============================================================================

-- 示例：按年份分区专利表（需要根据实际需求调整）
/*
CREATE TABLE patents_partitioned (
    LIKE patents INCLUDING ALL
) PARTITION BY RANGE (application_date);

-- 创建年度分区
CREATE TABLE patents_2020 PARTITION OF patents_partitioned
    FOR VALUES FROM ('2020-01-01') TO ('2021-01-01');

CREATE TABLE patents_2021 PARTITION OF patents_partitioned
    FOR VALUES FROM ('2021-01-01') TO ('2022-01-01');

CREATE TABLE patents_2022 PARTITION OF patents_partitioned
    FOR VALUES FROM ('2022-01-01') TO ('2023-01-01');

CREATE TABLE patents_2023 PARTITION OF patents_partitioned
    FOR VALUES FROM ('2023-01-01') TO ('2024-01-01');

CREATE TABLE patents_2024 PARTITION OF patents_partitioned
    FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
*/

-- =============================================================================
-- 授权和权限设置
-- =============================================================================

-- 授予专利分析师只读权限
GRANT SELECT ON patent_overview TO patent_analyst;
GRANT SELECT ON active_patents TO patent_analyst;
GRANT SELECT ON patent_statistics TO patent_analyst;

-- 授予备份用户必要的权限
GRANT SELECT ON ALL TABLES IN SCHEMA public TO patent_backup;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO patent_backup;

-- =============================================================================
-- 完成提示
-- =============================================================================

-- 输出创建完成信息
DO $$
BEGIN
    RAISE NOTICE '=====================================';
    RAISE NOTICE '专利数据库表结构创建完成！';
    RAISE NOTICE '=====================================';
    RAISE NOTICE '已创建表：';
    RAISE NOTICE '1. patents - 专利基础信息';
    RAISE NOTICE '2. patent_legal_history - 法律状态历史';
    RAISE NOTICE '3. patent_participants - 参与者信息';
    RAISE NOTICE '4. patent_citations - 引用关系';
    RAISE NOTICE '5. patent_litigations - 诉讼信息';
    RAISE NOTICE '6. patent_licenses - 许可信息';
    RAISE NOTICE '7. patent_analytics - 分析评估';
    RAISE NOTICE '';
    RAISE NOTICE '建议后续操作：';
    RAISE NOTICE '1. 导入历史专利数据';
    RAISE NOTICE '2. 配置定期数据同步';
    RAISE NOTICE '3. 设置全文搜索配置';
    RAISE NOTICE '4. 创建物化视图优化查询';
    RAISE NOTICE '=====================================';
END $$;