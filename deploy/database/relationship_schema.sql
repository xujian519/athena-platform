-- =====================================================
-- YunPat 数据库关联架构设计
-- 客户表与任务、案卷、文档、状态等表的关联关系
-- 创建时间: 2025-12-17
-- =====================================================

-- =====================================================
-- 1. 核心客户表 (已存在，需要添加字段)
-- =====================================================
ALTER TABLE customers ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS customer_type VARCHAR(20) DEFAULT 'formal';
ALTER TABLE customers ADD COLUMN IF NOT EXISTS business_stage VARCHAR(50) DEFAULT 'initial';
ALTER TABLE customers ADD COLUMN IF NOT EXISTS total_cases INTEGER DEFAULT 0;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS total_tasks INTEGER DEFAULT 0;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS total_documents INTEGER DEFAULT 0;

-- 添加客户索引
CREATE INDEX IF NOT EXISTS idx_customers_type ON customers(customer_type);
CREATE INDEX IF NOT EXISTS idx_customers_stage ON customers(business_stage);
CREATE INDEX IF NOT EXISTS idx_customers_created ON customers(created_at);

-- =====================================================
-- 2. 客户案卷表 (cases)
-- =====================================================
CREATE TABLE IF NOT EXISTS cases (
    case_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    case_number VARCHAR(50) UNIQUE NOT NULL,
    case_type VARCHAR(50) NOT NULL, -- 'patent_application', 'trademark', 'copyright', 'certificate'
    case_title VARCHAR(500) NOT NULL,
    case_description TEXT,

    -- 案卷状态
    case_status VARCHAR(50) DEFAULT 'created', -- 'created', 'in_progress', 'review', 'approved', 'rejected', 'completed'
    priority VARCHAR(20) DEFAULT 'normal', -- 'low', 'normal', 'high', 'urgent'

    -- 时间信息
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deadline DATE,
    completed_at TIMESTAMP,

    -- 财务信息
    total_fee DECIMAL(12, 2),
    paid_fee DECIMAL(12, 2) DEFAULT 0,
    payment_status VARCHAR(20) DEFAULT 'unpaid', -- 'unpaid', 'partial', 'paid', 'refunded'

    -- 服务内容
    services JSONB, -- ["专利申请准备", "技术文件整理", "专利文件撰写"]
    patent_info JSONB, -- 专利相关信息

    -- 元数据
    tags TEXT[],
    notes TEXT,
    assigned_to VARCHAR(100),
    reviewed_by VARCHAR(100),

    -- 系统字段
    created_by VARCHAR(100),
    updated_by VARCHAR(100)
);

-- 案卷表索引
CREATE INDEX IF NOT EXISTS idx_cases_customer_id ON cases(customer_id);
CREATE INDEX IF NOT EXISTS idx_cases_status ON cases(case_status);
CREATE INDEX IF NOT EXISTS idx_cases_type ON cases(case_type);
CREATE INDEX IF NOT EXISTS idx_cases_priority ON cases(priority);
CREATE INDEX IF NOT EXISTS idx_cases_created_at ON cases(created_at);
CREATE INDEX IF NOT EXISTS idx_cases_deadline ON cases(deadline);
CREATE INDEX IF NOT EXISTS idx_cases_payment_status ON cases(payment_status);

-- =====================================================
-- 3. 客户任务表 (tasks)
-- =====================================================
CREATE TABLE IF NOT EXISTS tasks (
    task_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(customer_id) ON DELETE CASCADE,
    case_id UUID REFERENCES cases(case_id) ON DELETE SET NULL,

    -- 任务基本信息
    task_title VARCHAR(500) NOT NULL,
    task_description TEXT,
    task_type VARCHAR(50) NOT NULL, -- 'contact', 'payment_collection', 'document_preparation', 'filing', 'follow_up', 'review'
    task_category VARCHAR(50), -- 'business', 'financial', 'administrative', 'legal'

    -- 任务状态
    task_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'in_progress', 'completed', 'cancelled', 'paused'
    priority VARCHAR(20) DEFAULT 'normal', -- 'low', 'normal', 'high', 'urgent'

    -- 时间信息
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    scheduled_at TIMESTAMP,
    due_at TIMESTAMP,
    completed_at TIMESTAMP,

    -- 执行信息
    assigned_to VARCHAR(100) NOT NULL,
    assigned_team VARCHAR(50),
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'archived', 'deleted'

    -- 任务详情
    details JSONB, -- 任务详细配置
    contact_info JSONB, -- 联系相关信息
    expected_outcome TEXT,
    actual_outcome TEXT,

    -- 提醒设置
    reminder_enabled BOOLEAN DEFAULT true,
    reminder_times TIMESTAMP[], -- 多个提醒时间
    last_reminder_sent TIMESTAMP,

    -- 关联信息
    depends_on UUID[], -- 依赖的其他任务ID
    blocks UUID[], -- 被此任务阻塞的任务ID

    -- 元数据
    tags TEXT[],
    notes TEXT,
    estimated_hours DECIMAL(5, 2),
    actual_hours DECIMAL(5, 2),

    -- 系统字段
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    -- 完成度
    completion_percentage INTEGER DEFAULT 0 CHECK (completion_percentage >= 0 AND completion_percentage <= 100)
);

-- 任务表索引
CREATE INDEX IF NOT EXISTS idx_tasks_customer_id ON tasks(customer_id);
CREATE INDEX IF NOT EXISTS idx_tasks_case_id ON tasks(case_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(task_status);
CREATE INDEX IF NOT EXISTS idx_tasks_type ON tasks(task_type);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned_to ON tasks(assigned_to);
CREATE INDEX IF NOT EXISTS idx_tasks_due_at ON tasks(due_at);
CREATE INDEX IF NOT EXISTS idx_tasks_scheduled_at ON tasks(scheduled_at);

-- =====================================================
-- 4. 客户文档表 (documents)
-- =====================================================
CREATE TABLE IF NOT EXISTS documents (
    document_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    case_id UUID REFERENCES cases(case_id) ON DELETE SET NULL,
    task_id UUID REFERENCES tasks(task_id) ON DELETE SET NULL,

    -- 文档基本信息
    document_name VARCHAR(500) NOT NULL,
    document_type VARCHAR(50) NOT NULL, -- 'contract', 'patent_application', 'technical_file', 'identity_document', 'payment_receipt', 'certificate'
    document_category VARCHAR(50), -- 'legal', 'technical', 'financial', 'administrative'

    -- 文档状态
    document_status VARCHAR(50) DEFAULT 'draft', -- 'draft', 'review', 'approved', 'rejected', 'signed', 'archived'
    version INTEGER DEFAULT 1,

    -- 存储信息
    file_path VARCHAR(1000),
    file_name VARCHAR(500),
    file_size BIGINT,
    file_format VARCHAR(20), -- 'pdf', 'doc', 'docx', 'jpg', 'png', 'zip'
    mime_type VARCHAR(100),

    -- 内容信息
    description TEXT,
    content_summary TEXT,
    keywords TEXT[],

    -- 时间信息
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    signed_at TIMESTAMP,
    archived_at TIMESTAMP,

    -- 权限信息
    access_level VARCHAR(20) DEFAULT 'internal', -- 'public', 'internal', 'confidential', 'secret'
    view_permissions TEXT[],
    edit_permissions TEXT[],

    -- 关联信息
    related_documents UUID[], -- 关联的其他文档
    replaces_document UUID, -- 替换的文档

    -- 元数据
    tags TEXT[],
    notes TEXT,
    uploaded_by VARCHAR(100),
    approved_by VARCHAR(100),

    -- 系统字段
    checksum VARCHAR(64), -- 文件校验和
    storage_backend VARCHAR(50), -- 'local', 's3', 'aliyun_oss'

    CONSTRAINT valid_document_status CHECK (document_status IN ('draft', 'review', 'approved', 'rejected', 'signed', 'archived'))
);

-- 文档表索引
CREATE INDEX IF NOT EXISTS idx_documents_customer_id ON documents(customer_id);
CREATE INDEX IF NOT EXISTS idx_documents_case_id ON documents(case_id);
CREATE INDEX IF NOT EXISTS idx_documents_task_id ON documents(task_id);
CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(document_type);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(document_status);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at);
CREATE INDEX IF NOT EXISTS idx_documents_access_level ON documents(access_level);

-- =====================================================
-- 5. 客户状态跟踪表 (customer_status_history)
-- =====================================================
CREATE TABLE IF NOT EXISTS customer_status_history (
    status_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,

    -- 状态信息
    status_type VARCHAR(50) NOT NULL, -- 'business', 'financial', 'contact', 'service'
    old_status VARCHAR(50),
    new_status VARCHAR(50) NOT NULL,

    -- 变更原因
    reason VARCHAR(500),
    reason_code VARCHAR(50),
    details JSONB,

    -- 时间信息
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 变更来源
    changed_by VARCHAR(100),
    change_source VARCHAR(50), -- 'manual', 'system', 'automation', 'api'
    related_task_id UUID REFERENCES tasks(task_id),
    related_case_id UUID REFERENCES cases(case_id),

    -- 影响评估
    impact_level VARCHAR(20) DEFAULT 'low', -- 'low', 'medium', 'high', 'critical'
    affected_areas TEXT[], -- ['billing', 'service', 'timeline', 'documentation']

    -- 元数据
    notes TEXT,
    tags TEXT[]
);

-- 状态历史表索引
CREATE INDEX IF NOT EXISTS idx_status_history_customer_id ON customer_status_history(customer_id);
CREATE INDEX IF NOT EXISTS idx_status_history_type ON customer_status_history(status_type);
CREATE INDEX IF NOT EXISTS idx_status_history_changed_at ON customer_status_history(changed_at);
CREATE INDEX IF NOT EXISTS idx_status_history_changed_by ON customer_status_history(changed_by);

-- =====================================================
-- 6. 客户联系记录表 (customer_contacts)
-- =====================================================
CREATE TABLE IF NOT EXISTS customer_contacts (
    contact_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,

    -- 联系信息
    contact_type VARCHAR(50) NOT NULL, -- 'phone', 'email', 'meeting', 'wechat', 'other'
    contact_direction VARCHAR(20) NOT NULL, -- 'inbound', 'outbound'

    -- 联系人信息
    contact_person VARCHAR(100), -- 客户方联系人
    our_contact_person VARCHAR(100) NOT NULL, -- 我方联系人

    -- 时间信息
    contact_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration_minutes INTEGER,

    -- 联系内容
    subject VARCHAR(500),
    content TEXT,
    summary TEXT,
    outcome VARCHAR(50), -- 'successful', 'failed', 'pending', 'callback_required'

    -- 关联信息
    related_case_id UUID REFERENCES cases(case_id),
    related_task_id UUID REFERENCES tasks(task_id),
    related_document_id UUID REFERENCES documents(document_id),

    -- 后续行动
    next_action TEXT,
    next_action_date TIMESTAMP,
    follow_up_required BOOLEAN DEFAULT false,

    -- 元数据
    tags TEXT[],
    notes TEXT,
    recording_file_path VARCHAR(1000), -- 通话录音文件路径
    attachments TEXT[], -- 附件列表

    -- 系统字段
    created_by VARCHAR(100),
    updated_by VARCHAR(100)
);

-- 联系记录表索引
CREATE INDEX IF NOT EXISTS idx_contacts_customer_id ON customer_contacts(customer_id);
CREATE INDEX IF NOT EXISTS idx_contacts_type ON customer_contacts(contact_type);
CREATE INDEX IF NOT EXISTS idx_contacts_time ON customer_contacts(contact_time);
CREATE INDEX IF NOT EXISTS idx_contacts_outcome ON customer_contacts(outcome);
CREATE INDEX IF NOT EXISTS idx_contacts_our_person ON customer_contacts(our_contact_person);

-- =====================================================
-- 7. 客户财务记录表 (customer_financial_records)
-- =====================================================
CREATE TABLE IF NOT EXISTS customer_financial_records (
    record_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    case_id UUID REFERENCES cases(case_id) ON DELETE SET NULL,

    -- 财务记录基本信息
    record_type VARCHAR(50) NOT NULL, -- 'payment', 'refund', 'adjustment', 'fee', 'discount'
    transaction_type VARCHAR(20) NOT NULL, -- 'income', 'expense'

    -- 金额信息
    amount DECIMAL(12, 2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'CNY',
    exchange_rate DECIMAL(10, 6) DEFAULT 1.0,

    -- 关联信息
    related_case_id UUID REFERENCES cases(case_id),
    related_task_id UUID REFERENCES tasks(task_id),
    invoice_number VARCHAR(100),
    receipt_number VARCHAR(100),

    -- 时间信息
    transaction_date DATE NOT NULL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confirmed_at TIMESTAMP,

    -- 状态信息
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'confirmed', 'cancelled', 'disputed'
    payment_method VARCHAR(50), -- 'cash', 'bank_transfer', 'alipay', 'wechat', 'credit_card'

    -- 描述信息
    description TEXT NOT NULL,
    category VARCHAR(100), -- 'service_fee', 'government_fee', 'consultation', 'other'

    -- 对账信息
    reconciled BOOLEAN DEFAULT false,
    reconciled_at TIMESTAMP,
    reconciled_by VARCHAR(100),

    -- 元数据
    notes TEXT,
    tags TEXT[],
    created_by VARCHAR(100),
    updated_by VARCHAR(100)
);

-- 财务记录表索引
CREATE INDEX IF NOT EXISTS idx_financial_customer_id ON customer_financial_records(customer_id);
CREATE INDEX IF NOT EXISTS idx_financial_case_id ON customer_financial_records(case_id);
CREATE INDEX IF NOT EXISTS idx_financial_type ON customer_financial_records(record_type);
CREATE INDEX IF NOT EXISTS idx_financial_status ON customer_financial_records(status);
CREATE INDEX IF NOT EXISTS idx_financial_transaction_date ON customer_financial_records(transaction_date);

-- =====================================================
-- 8. 创建触发器函数，自动更新时间戳
-- =====================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为所有需要的表创建更新时间戳触发器
CREATE TRIGGER update_customers_updated_at BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cases_updated_at BEFORE UPDATE ON cases
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- 9. 创建视图，方便查询客户全景信息
-- =====================================================

-- 客户概览视图
CREATE OR REPLACE VIEW customer_overview AS
SELECT
    c.customer_id,
    c.name,
    c.phone,
    c.email,
    c.address,
    c.customer_type,
    c.business_type,
    c.business_stage,
    c.total_cases,
    c.total_tasks,
    c.total_documents,

    -- 案卷统计
    COALESCE(case_stats.total_cases, 0) as actual_case_count,
    COALESCE(case_stats.active_cases, 0) as active_case_count,
    COALESCE(case_stats.completed_cases, 0) as completed_case_count,

    -- 任务统计
    COALESCE(task_stats.total_tasks, 0) as actual_task_count,
    COALESCE(task_stats.pending_tasks, 0) as pending_task_count,
    COALESCE(task_stats.overdue_tasks, 0) as overdue_task_count,

    -- 文档统计
    COALESCE(doc_stats.total_docs, 0) as actual_doc_count,
    COALESCE(doc_stats.recent_docs, 0) as recent_doc_count,

    -- 财务统计
    COALESCE(fin_stats.total_paid, 0) as total_paid_amount,
    COALESCE(fin_stats.total_unpaid, 0) as total_unpaid_amount,
    COALESCE(fin_stats.payment_rate, 0) as payment_rate,

    -- 最近活动
    recent_status.last_status_change,
    recent_contact.last_contact_time,
    recent_contact.last_contact_person,

    c.created_at,
    c.updated_at

FROM customers c
LEFT JOIN (
    SELECT
        customer_id,
        COUNT(*) as total_cases,
        COUNT(CASE WHEN case_status IN ('created', 'in_progress', 'review') THEN 1 END) as active_cases,
        COUNT(CASE WHEN case_status = 'completed' THEN 1 END) as completed_cases
    FROM cases
    GROUP BY customer_id
) case_stats ON c.customer_id = case_stats.customer_id
LEFT JOIN (
    SELECT
        customer_id,
        COUNT(*) as total_tasks,
        COUNT(CASE WHEN task_status = 'pending' THEN 1 END) as pending_tasks,
        COUNT(CASE WHEN task_status = 'pending' AND due_at < CURRENT_TIMESTAMP THEN 1 END) as overdue_tasks
    FROM tasks
    GROUP BY customer_id
) task_stats ON c.customer_id = task_stats.customer_id
LEFT JOIN (
    SELECT
        customer_id,
        COUNT(*) as total_docs,
        COUNT(CASE WHEN created_at >= CURRENT_TIMESTAMP - INTERVAL '30 days' THEN 1 END) as recent_docs
    FROM documents
    GROUP BY customer_id
) doc_stats ON c.customer_id = doc_stats.customer_id
LEFT JOIN (
    SELECT
        customer_id,
        SUM(CASE WHEN status = 'confirmed' AND transaction_type = 'income' THEN amount ELSE 0 END) as total_paid,
        SUM(CASE WHEN status IN ('pending', 'confirmed') AND record_type = 'payment' AND transaction_type = 'income' THEN amount ELSE 0 END) as total_unpaid,
        CASE
            WHEN SUM(CASE WHEN record_type = 'payment' AND transaction_type = 'income' THEN amount ELSE 0 END) > 0
            THEN ROUND(
                SUM(CASE WHEN status = 'confirmed' AND transaction_type = 'income' THEN amount ELSE 0 END) /
                SUM(CASE WHEN record_type = 'payment' AND transaction_type = 'income' THEN amount ELSE 0 END) * 100, 2
            )
            ELSE 0
        END as payment_rate
    FROM customer_financial_records
    GROUP BY customer_id
) fin_stats ON c.customer_id = fin_stats.customer_id
LEFT JOIN (
    SELECT DISTINCT ON (customer_id)
        customer_id,
        new_status as last_status_change,
        changed_at
    FROM customer_status_history
    ORDER BY customer_id, changed_at DESC
) recent_status ON c.customer_id = recent_status.customer_id
LEFT JOIN (
    SELECT DISTINCT ON (customer_id)
        customer_id,
        contact_time as last_contact_time,
        our_contact_person as last_contact_person
    FROM customer_contacts
    ORDER BY customer_id, contact_time DESC
) recent_contact ON c.customer_id = recent_contact.customer_id;

-- =====================================================
-- 10. 插入示例数据和初始化
-- =====================================================

-- 为现有客户创建示例案卷记录（如果需要）
-- 注意：这里只是示例，实际使用时应该根据具体业务需求插入真实数据

-- =====================================================
-- 11. 创建常用查询函数
-- =====================================================

-- 获取客户完整信息的函数
CREATE OR REPLACE FUNCTION get_customer_complete_info(customer_uuid UUID)
RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    SELECT jsonb_build_object(
        'customer', row_to_json(c.*),
        'cases', (
            SELECT jsonb_agg(jsonb_build_object(
                'case_id', case_id,
                'case_number', case_number,
                'case_type', case_type,
                'case_title', case_title,
                'case_status', case_status,
                'priority', priority,
                'total_fee', total_fee,
                'paid_fee', paid_fee,
                'payment_status', payment_status,
                'created_at', created_at,
                'deadline', deadline
            ))
            FROM cases WHERE customer_id = customer_uuid
        ),
        'tasks', (
            SELECT jsonb_agg(jsonb_build_object(
                'task_id', task_id,
                'task_title', task_title,
                'task_type', task_type,
                'task_status', task_status,
                'priority', priority,
                'assigned_to', assigned_to,
                'scheduled_at', scheduled_at,
                'due_at', due_at,
                'created_at', created_at
            ))
            FROM tasks WHERE customer_id = customer_uuid
        ),
        'documents', (
            SELECT jsonb_agg(jsonb_build_object(
                'document_id', document_id,
                'document_name', document_name,
                'document_type', document_type,
                'document_status', document_status,
                'file_size', file_size,
                'created_at', created_at
            ))
            FROM documents WHERE customer_id = customer_uuid
        ),
        'financial_summary', (
            SELECT jsonb_build_object(
                'total_paid', COALESCE(SUM(CASE WHEN status = 'confirmed' AND transaction_type = 'income' THEN amount ELSE 0 END), 0),
                'total_unpaid', COALESCE(SUM(CASE WHEN record_type = 'payment' AND status IN ('pending', 'confirmed') AND transaction_type = 'income' THEN amount ELSE 0 END), 0),
                'transaction_count', COUNT(*)
            )
            FROM customer_financial_records WHERE customer_id = customer_uuid
        ),
        'recent_activities', (
            SELECT jsonb_agg(
                jsonb_build_object(
                    'activity_type', 'status_change',
                    'description', reason,
                    'changed_at', changed_at,
                    'changed_by', changed_by
                )
            )
            FROM (
                SELECT reason, changed_at, changed_by
                FROM customer_status_history
                WHERE customer_id = customer_uuid
                ORDER BY changed_at DESC
                LIMIT 5
            ) recent_changes
        )
    ) INTO result
    FROM customers c
    WHERE c.customer_id = customer_uuid;

    RETURN COALESCE(result, '{}'::jsonb);
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 12. 数据完整性约束和清理函数
-- =====================================================

-- 清理孤立数据的函数
CREATE OR REPLACE FUNCTION cleanup_orphaned_data()
RETURNS TEXT AS $$
DECLARE
    cleanup_count INTEGER := 0;
BEGIN
    -- 清理没有客户的案卷
    DELETE FROM cases WHERE customer_id NOT IN (SELECT customer_id FROM customers);
    GET DIAGNOSTICS cleanup_count = ROW_COUNT;
    RAISE NOTICE '清理孤立案卷: % 条', cleanup_count;

    -- 清理没有客户的任务
    DELETE FROM tasks WHERE customer_id NOT IN (SELECT customer_id FROM customers);
    GET DIAGNOSTICS cleanup_count = ROW_COUNT;
    RAISE NOTICE '清理孤立任务: % 条', cleanup_count;

    -- 清理没有客户的文档
    DELETE FROM documents WHERE customer_id NOT IN (SELECT customer_id FROM customers);
    GET DIAGNOSTICS cleanup_count = ROW_COUNT;
    RAISE NOTICE '清理孤立文档: % 条', cleanup_count;

    RETURN '数据清理完成';
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 说明和注释
-- =====================================================

/*
数据库关联架构说明：

1. 核心设计原则：
   - 以客户表为中心，所有业务数据都与客户关联
   - 使用UUID作为主键，确保数据安全和分布友好
   - 支持软删除和数据审计
   - 完整的时间戳跟踪

2. 关联关系：
   - customers (1) -> (n) cases (一个客户可以有多个案卷)
   - customers (1) -> (n) tasks (一个客户可以有多个任务)
   - customers (1) -> (n) documents (一个客户可以有多个文档)
   - customers (1) -> (n) customer_status_history (客户状态变更历史)
   - customers (1) -> (n) customer_contacts (客户联系记录)
   - customers (1) -> (n) customer_financial_records (客户财务记录)

3. 次要关联：
   - cases (1) -> (n) tasks (一个案卷可以有多个任务)
   - cases (1) -> (n) documents (一个案卷可以有多个文档)
   - tasks (1) -> (n) documents (一个任务可以有多个文档)

4. 特性：
   - 支持JSONB字段存储灵活的配置和元数据
   - 完整的索引策略，优化查询性能
   - 触发器自动维护更新时间
   - 视图简化常用查询
   - 函数封装复杂业务逻辑

5. 使用建议：
   - 使用customer_overview视图获取客户全景信息
   - 使用get_customer_complete_info函数获取客户完整数据
   - 定期运行cleanup_orphaned_data()清理孤立数据
   - 根据业务需要调整索引策略

6. 扩展性：
   - 可以轻松添加新的关联表
   - JSONB字段支持灵活的业务需求变化
   - 分区表支持大数据量场景
*/