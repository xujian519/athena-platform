-- 创建锦州医科大学审查意见答复任务
-- Create Jinzhou Medical University Examination Opinion Reply Task
-- 作者: 小诺·双鱼公主
-- 创建时间: 2025-12-22
-- 专利申请号：202411792145.X

\c phoenix_prod;

-- 1. 创建客户信息（锦州医科大学）
INSERT INTO customers (
    customer_id,
    customer_name,
    phone,
    email,
    address,
    postal_code,
    profession,
    specialization,
    contact_person,
    contact_phone,
    region,
    customer_type,
    organization_name,
    status,
    notes,
    metadata
) VALUES (
    gen_random_uuid(),
    '锦州医科大学',
    NULL,
    NULL,
    '辽宁省锦州市凌河区松坡路三段40号',
    '121000',
    '高等院校',
    '医学教育、科研创新、药物研发',
    '科研处',
    NULL,
    '辽宁省',
    'organization',
    '锦州医科大学',
    'active',
    '高等院校客户，涉及天麻苷元与对乙酰氨基酚孪药专利申请，收到第二次审查意见需要答复',
    '{"organization_type": "高等院校", "patent_focus": "药物研发", "province": "辽宁省", "city": "锦州市", "research_strength": "医药研发"}'
) ON CONFLICT (customer_id) DO UPDATE SET
    updated_at = CURRENT_TIMESTAMP;

-- 获取客户ID并创建专利申请记录
DO $$
DECLARE
    v_customer_id UUID;
    v_application_id UUID;
    v_reply_task_id UUID;
    current_date DATE := CURRENT_DATE;
    friday_date DATE;
BEGIN
    -- 计算本周五的日期
    SELECT current_date + (5 - EXTRACT(DOW FROM current_date)::integer)::int
    INTO friday_date;

    SELECT customer_id INTO v_customer_id FROM customers WHERE customer_name = '锦州医科大学';

    IF v_customer_id IS NOT NULL THEN
        -- 2. 创建专利申请记录
        INSERT INTO patent_applications (
            application_id,
            customer_id,
            application_number,
            patent_name,
            patent_type,
            technical_field,
            application_status,
            inventors,
            applicants,
            technical_description,
            blue_ocean_potential,
            metadata
        ) VALUES (
            gen_random_uuid(),
            v_customer_id,
            '202411792145.X',
            '天麻苷元与对乙酰氨基酚孪药设计及应用',
            '发明',
            '药物化学、制药技术',
            '审查意见答复中',
            '[{"sequence": 1, "name": "锦州医科大学", "organization": "锦州医科大学"}]',
            '[{"name": "锦州医科大学", "organization": "锦州医科大学"}]',
            '涉及天麻苷元与对乙酰氨基酚的孪药设计及应用技术，属于医药研发领域',
            false,
            '{"filing_date": "2024-11-22", "examination_round": 2, "opinion_date": "2025-12-17", "drug_type": "孪药", "active_compounds": ["天麻苷元", "对乙酰氨基酚"]}'
        ) RETURNING application_id INTO v_application_id;

        -- 3. 创建审查意见答复任务
        INSERT INTO task_management (
            task_id,
            customer_id,
            application_id,
            task_number,
            task_title,
            task_type,
            task_status,
            priority,
            description,
            deadline,
            assigned_to,
            progress,
            task_details,
            created_at
        ) VALUES (
            gen_random_uuid(),
            v_customer_id,
            v_application_id,
            'TASK20251222001',
            '答复202411792145.X专利第二次审查意见',
            '审查意见答复',
            '待处理',
            'high',
            '需要针对锦州医科大学天麻苷元与对乙酰氨基酚孪药专利的第二次审查意见进行专业答复，确保权利要求和技术方案的充分说明',
            friday_date,
            '徐健',
            0,
            '{"examination_round": "第二次", "application_number": "202411792145.X", "opinion_date": "2025-12-17", "patent_title": "天麻苷元与对乙酰氨基酚孪药设计及应用", "reply_deadline": "' || friday_date || '", "priority_factors": ["审查意见涉及权利要求", "技术方案需要澄清", "答复期限紧迫"], "required_documents": ["审查意见答复书", "修改后的权利要求书", "修改后的说明书"], "technical_focus": "孪药设计原理、药物组合物、制备方法、应用领域"}',
            '2025-12-22 12:20:00'
        ) RETURNING task_id INTO v_reply_task_id;

        -- 4. 创建文档管理记录（审查意见文件）
        INSERT INTO document_management (
            document_id,
            customer_id,
            application_id,
            task_id,
            document_type,
            document_name,
            file_path,
            file_size,
            file_format,
            processing_status,
            notes,
            metadata
        ) VALUES (
            gen_random_uuid(),
            v_customer_id,
            v_application_id,
            v_reply_task_id,
            '审查意见通知',
            '202411792145.X-第二次审查意见-锦州医科大学-2025.12.17.pdf',
            '/Users/xujian/工作/04_审查意见/01_待答复/202411792145.X-第二次审查意见-锦州医科大学-2025.12.17/202411792145.X-第二次审查意见-锦州医科大学-2025.12.17.pdf',
            301819,
            'PDF',
            '待处理',
            '第二次审查意见通知，需要仔细分析审查意见内容并准备答复',
            '{"upload_date": "2025-12-22", "examination_round": 2, "opinion_date": "2025-12-17", "file_size_kb": 301, "processing_priority": "high"}'
        );

        INSERT INTO document_management (
            document_id,
            customer_id,
            application_id,
            task_id,
            document_type,
            document_name,
            file_path,
            file_size,
            file_format,
            processing_status,
            notes,
            metadata
        ) VALUES (
            gen_random_uuid(),
            v_customer_id,
            v_application_id,
            v_reply_task_id,
            '专利申请文件',
            '202411792145X.docx',
            '/Users/xujian/工作/04_审查意见/01_待答复/202411792145.X-第二次审查意见-锦州医科大学-2025.12.17/202411792145X.docx',
            11675,
            'DOCX',
            '待处理',
            '原始专利申请文件，需要对比审查意见进行修改',
            '{"upload_date": "2025-12-09", "document_type": "申请文件", "file_size_kb": 11, "current_version": true}'
        );

        INSERT INTO document_management (
            document_id,
            customer_id,
            application_id,
            task_id,
            document_type,
            document_name,
            file_path,
            file_size,
            file_format,
            processing_status,
            notes,
            metadata
        ) VALUES (
            gen_random_uuid(),
            v_customer_id,
            v_application_id,
            v_reply_task_id,
            '技术文档',
            '天麻苷元与对乙酰氨基酚孪药设计及应用（初稿）.docx',
            '/Users/xujian/工作/04_审查意见/01_待答复/202411792145.X-第二次审查意见-锦州医科大学-2025.12.17/天麻苷元与对乙酰氨基酚孪药设计及应用（初稿）.docx',
            462214,
            'DOCX',
            '待处理',
            '技术方案初稿，包含天麻苷元与对乙酰氨基酚孪药的详细设计说明',
            '{"upload_date": "2025-12-12", "document_type": "技术方案", "file_size_kb": 452, "technical_depth": "详细", "contains_experimental_data": true}'
        );

        -- 5. 创建项目里程碑
        INSERT INTO project_milestones (
            milestone_id,
            customer_id,
            application_id,
            milestone_name,
            milestone_type,
            planned_date,
            status,
            description,
            deliverables
        ) VALUES (
            gen_random_uuid(),
            v_customer_id,
            v_application_id,
            '审查意见分析',
            '审查答复',
            current_date + 1,
            '未开始',
            '分析第二次审查意见的具体内容，理解审查员的关注点和质疑',
            '{"deliverables": ["审查意见分析报告", "质疑点清单", "答复策略"]}'
        );

        INSERT INTO project_milestones (
            milestone_id,
            customer_id,
            application_id,
            milestone_name,
            milestone_type,
            planned_date,
            status,
            description,
            deliverables
        ) VALUES (
            gen_random_uuid(),
            v_customer_id,
            v_application_id,
            '答复文件撰写',
            '审查答复',
            friday_date - 2,
            '未开始',
            '撰写审查意见答复书，修改权利要求书和说明书',
            '{"deliverables": ["审查意见答复书", "修改后的权利要求书", "修改后的说明书", "修改说明"]}'
        );

        INSERT INTO project_milestones (
            milestone_id,
            customer_id,
            application_id,
            milestone_name,
            milestone_type,
            planned_date,
            status,
            description,
            deliverables
        ) VALUES (
            gen_random_uuid(),
            v_customer_id,
            v_application_id,
            '答复提交',
            '审查答复',
            friday_date,
            '未开始',
            '提交完整的审查意见答复文件',
            '{"deliverables": ["正式提交的答复文件", "提交确认"]}'
        );

        -- 6. 创建沟通记录
        INSERT INTO communication_records (
            record_id,
            customer_id,
            application_id,
            communication_type,
            contact_date,
            contact_person,
            subject,
            content,
            outcome,
            follow_up_required,
            next_action,
            metadata
        ) VALUES (
            gen_random_uuid(),
            v_customer_id,
            v_application_id,
            '任务创建',
            '2025-12-22',
            '小娜系统',
            '审查意见答复任务创建',
            '为锦州医科大学202411792145.X专利第二次审查意见创建答复任务，截止日期为本周五',
            true,
            '分析审查意见内容，准备专业答复',
            '{"task_number": "TASK20251222001", "deadline": "' || friday_date || '", "priority": "high", "examination_round": 2}'
        );

        -- 7. 创建专利检索记录（可选，用于支持答复）
        INSERT INTO patent_search_records (
            search_id,
            customer_id,
            application_id,
            search_type,
            search_keywords,
            search_strategy,
            database_used,
            search_date,
            results_count,
            analysis_report,
            recommendation,
            metadata
        ) VALUES (
            gen_random_uuid(),
            v_customer_id,
            v_application_id,
            '技术对比',
            '天麻苷元、对乙酰氨基酚、孪药、药物组合物',
            '{"keywords": ["天麻苷元", "对乙酰氨基酚", "孪药", "药物组合物", "镇痛药物"], "classification": ["A61K", "C07D"]}',
            '专利数据库',
            '2025-12-22',
            0,
            '{"search_status": "计划执行", "purpose": "支持审查意见答复", "focus_areas": "现有技术对比"}',
            '建议检索相关技术对比专利，支持答复时的技术论证',
            '{"support_type": "审查答复", "search_depth": "详细"}'
        );

        RAISE NOTICE '锦州医科大学审查意见答复任务创建完成，客户ID: %', v_customer_id;
        RAISE NOTICE '任务截止日期: %', friday_date;
        RAISE NOTICE '任务ID: TASK20251222001';

    ELSE
        RAISE NOTICE '未找到锦州医科大学客户记录';
    END IF;
END $$;

-- 8. 更新系统信息
INSERT INTO system_info (key, value) VALUES
    ('last_task_created', json_build_object(
        'task_date', CURRENT_DATE,
        'customer_name', '锦州医科大学',
        'application_number', '202411792145.X',
        'task_type', '审查意见答复',
        'deadline', to_char(CURRENT_DATE + (5 - EXTRACT(DOW FROM CURRENT_DATE)::integer)::int, 'YYYY-MM-DD'),
        'created_by', '小娜系统'
    )::text)
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;

COMMIT;

-- 显示创建的任务信息
SELECT '🎯 审查意见答复任务创建成功 🎯' as task_status;
SELECT json_build_object(
    '客户名称', '锦州医科大学',
    '专利申请号', '202411792145.X',
    '专利名称', '天麻苷元与对乙酰氨基酚孪药设计及应用',
    '审查轮次', '第二次',
    '任务编号', 'TASK20251222001',
    '任务类型', '审查意见答复',
    '截止日期', to_char(CURRENT_DATE + (5 - EXTRACT(DOW FROM CURRENT_DATE)::integer)::int, 'YYYY-MM-DD'),
    '剩余天数', (5 - EXTRACT(DOW FROM CURRENT_DATE)::integer)::int,
    '优先级', '高',
    '关联文档数量', 3
) as task_summary;