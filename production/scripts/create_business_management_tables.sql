-- 创建业务管理系统数据库表结构
-- Create Business Management System Database Tables
-- 作者: 小诺·双鱼公主
-- 创建时间: 2025-12-22
-- 版本: v1.0.0 "业务管理系统"

-- 使用 phoenix_prod 数据库
\c phoenix_prod;

-- 创建客户表
CREATE TABLE IF NOT EXISTS customers (
    customer_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(100),
    address TEXT,
    postal_code VARCHAR(10),
    profession VARCHAR(100),
    specialization VARCHAR(200),
    contact_person VARCHAR(100),
    contact_phone VARCHAR(20),
    wechat_id VARCHAR(50),
    region VARCHAR(50),
    customer_type VARCHAR(20) DEFAULT 'individual',
    organization_name VARCHAR(200),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    metadata JSONB
);

-- 创建专利申请表
CREATE TABLE IF NOT EXISTS patent_applications (
    application_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(customer_id),
    application_number VARCHAR(50),
    patent_name VARCHAR(300) NOT NULL,
    patent_type VARCHAR(20) NOT NULL, -- '发明', '实用新型', '外观设计'
    technical_field VARCHAR(200),
    application_status VARCHAR(30) DEFAULT '准备中',
    priority_date DATE,
    filing_date DATE,
    grant_date DATE,
    expiry_date DATE,
    inventors JSONB, -- 发明人列表
    applicants JSONB, -- 申请人列表
    technical_description TEXT,
    claims_text TEXT,
    abstract_text TEXT,
    drawings_count INTEGER DEFAULT 0,
    ipc_classification VARCHAR(100),
    cpc_classification VARCHAR(100),
    application_goal VARCHAR(200), -- 申请目标：职称评定、技术保护等
    blue_ocean_potential BOOLEAN DEFAULT FALSE,
    competition_analysis JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- 创建财务记录表
CREATE TABLE IF NOT EXISTS financial_records (
    record_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(customer_id),
    application_id UUID REFERENCES patent_applications(application_id),
    record_type VARCHAR(20) NOT NULL, -- '代理费', '官方费用', '其他费用'
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'CNY',
    payment_status VARCHAR(20) DEFAULT '未支付', -- '已支付', '部分支付', '未支付'
    payment_date DATE,
    invoice_number VARCHAR(50),
    fee_details JSONB, -- 费用明细
    discount_amount DECIMAL(10,2) DEFAULT 0,
    discount_reason VARCHAR(200),
    total_amount DECIMAL(10,2),
    payment_method VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建任务管理表
CREATE TABLE IF NOT EXISTS task_management (
    task_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(customer_id),
    application_id UUID REFERENCES patent_applications(application_id),
    task_number VARCHAR(50) UNIQUE NOT NULL,
    task_title VARCHAR(300) NOT NULL,
    task_type VARCHAR(50), -- '专利名称确定', '技术交底', '申请准备', '费用催缴'等
    task_status VARCHAR(20) DEFAULT '待处理', -- '待处理', '进行中', '已完成', '已取消'
    priority VARCHAR(10) DEFAULT 'medium', -- 'high', 'medium', 'low'
    description TEXT,
    assigned_to VARCHAR(100),
    deadline DATE,
    completion_date DATE,
    progress INTEGER DEFAULT 0, -- 进度百分比
    task_details JSONB, -- 任务详细内容
    communication_records JSONB, -- 沟通记录
    attachments JSONB, -- 附件列表
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- 创建文档管理表
CREATE TABLE IF NOT EXISTS document_management (
    document_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(customer_id),
    application_id UUID REFERENCES patent_applications(application_id),
    task_id UUID REFERENCES task_management(task_id),
    document_type VARCHAR(50) NOT NULL, -- '专利申请确认书', '技术交底书', '说明书', '权利要求书'等
    document_name VARCHAR(300) NOT NULL,
    file_path TEXT,
    file_size BIGINT,
    file_format VARCHAR(20),
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_status VARCHAR(20) DEFAULT '待处理', -- '待处理', '处理中', '已完成', '处理失败'
    extraction_confidence DECIMAL(3,2),
    extracted_data JSONB,
    ocr_status VARCHAR(20),
    notes TEXT,
    metadata JSONB
);

-- 创建沟通记录表
CREATE TABLE IF NOT EXISTS communication_records (
    record_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(customer_id),
    application_id UUID REFERENCES patent_applications(application_id),
    communication_type VARCHAR(20), -- '电话', '微信', '邮件', '面谈', '其他'
    contact_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    contact_person VARCHAR(100),
    contact_method VARCHAR(50),
    subject VARCHAR(300),
    content TEXT,
    outcome VARCHAR(500),
    follow_up_required BOOLEAN DEFAULT FALSE,
    follow_up_date DATE,
    next_action VARCHAR(300),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- 创建项目里程碑表
CREATE TABLE IF NOT EXISTS project_milestones (
    milestone_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(customer_id),
    application_id UUID REFERENCES patent_applications(application_id),
    milestone_name VARCHAR(200) NOT NULL,
    milestone_type VARCHAR(50), -- '申请准备', '提交申请', '审查答复', '授权办证'等
    planned_date DATE,
    actual_date DATE,
    status VARCHAR(20) DEFAULT '未开始', -- '未开始', '进行中', '已完成', '延迟'
    description TEXT,
    deliverables JSONB,
    dependencies JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建专利检索记录表
CREATE TABLE IF NOT EXISTS patent_search_records (
    search_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(customer_id),
    application_id UUID REFERENCES patent_applications(application_id),
    search_type VARCHAR(50), -- '新颖性检索', '侵权检索', '技术调研'等
    search_keywords TEXT,
    search_strategy JSONB,
    database_used VARCHAR(100),
    search_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    results_count INTEGER,
    relevant_patents JSONB, -- 相关专利列表
    analysis_report JSONB, -- 分析报告
    blue_ocean_opportunities JSONB, -- 蓝海机会
    competition_analysis JSONB, -- 竞争分析
    recommendation JSONB, -- 建议
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_customers_name ON customers(customer_name);
CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone);
CREATE INDEX IF NOT EXISTS idx_customers_status ON customers(status);
CREATE INDEX IF NOT EXISTS idx_patent_applications_customer ON patent_applications(customer_id);
CREATE INDEX IF NOT EXISTS idx_patent_applications_status ON patent_applications(application_status);
CREATE INDEX IF NOT EXISTS idx_patent_applications_type ON patent_applications(patent_type);
CREATE INDEX IF NOT EXISTS idx_financial_records_customer ON financial_records(customer_id);
CREATE INDEX IF NOT EXISTS idx_financial_records_application ON financial_records(application_id);
CREATE INDEX IF NOT EXISTS idx_financial_records_status ON financial_records(payment_status);
CREATE INDEX IF NOT EXISTS idx_task_management_customer ON task_management(customer_id);
CREATE INDEX IF NOT EXISTS idx_task_management_status ON task_management(task_status);
CREATE INDEX IF NOT EXISTS idx_task_management_deadline ON task_management(deadline);
CREATE INDEX IF NOT EXISTS idx_document_management_customer ON document_management(customer_id);
CREATE INDEX IF NOT EXISTS idx_document_management_application ON document_management(application_id);
CREATE INDEX IF NOT EXISTS idx_communication_records_customer ON communication_records(customer_id);
CREATE INDEX IF NOT EXISTS idx_communication_records_date ON communication_records(contact_date);

-- 创建更新时间触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为所有表添加更新时间触发器
CREATE TRIGGER update_customers_updated_at BEFORE UPDATE ON customers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_patent_applications_updated_at BEFORE UPDATE ON patent_applications FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_financial_records_updated_at BEFORE UPDATE ON financial_records FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_task_management_updated_at BEFORE UPDATE ON task_management FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_document_management_updated_at BEFORE UPDATE ON document_management FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_communication_records_updated_at BEFORE UPDATE ON communication_records FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_project_milestones_updated_at BEFORE UPDATE ON project_milestones FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 插入系统信息
INSERT INTO system_info (key, value) VALUES
    ('business_management_version', 'v1.0.0'),
    ('tables_created_date', CURRENT_DATE),
    ('created_by', '小诺·双鱼公主'),
    ('description', '业务管理系统 - 客户和专利申请管理')
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;

COMMENT ON TABLE customers IS '客户信息表';
COMMENT ON TABLE patent_applications IS '专利申请表';
COMMENT ON TABLE financial_records IS '财务记录表';
COMMENT ON TABLE task_management IS '任务管理表';
COMMENT ON TABLE document_management IS '文档管理表';
COMMENT ON TABLE communication_records IS '沟通记录表';
COMMENT ON TABLE project_milestones IS '项目里程碑表';
COMMENT ON TABLE patent_search_records IS '专利检索记录表';

COMMIT;