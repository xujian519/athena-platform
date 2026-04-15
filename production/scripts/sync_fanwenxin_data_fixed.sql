-- 修复版：同步范文新客户数据到业务管理系统
-- Fixed: Sync Fan Wenxin Customer Data to Business Management System
-- 作者: 小诺·双鱼公主
-- 创建时间: 2025-12-22

\c phoenix_prod;

-- 插入范文新客户信息
INSERT INTO customers (
    customer_id,
    customer_name,
    phone,
    email,
    address,
    profession,
    specialization,
    contact_person,
    contact_phone,
    wechat_id,
    region,
    customer_type,
    status,
    notes,
    metadata
) VALUES (
    gen_random_uuid(),
    '范文新',
    '15966352598',
    NULL,
    '滨州沾化',
    '农业种植、种业推广',
    '农业种植、种业推广、农作物培育',
    '范文新',
    '15966352598',
    '茉莉',
    '山东省滨州市沾化区',
    'individual',
    'active',
    '农业种植、种业推广专家，与孙俊霞、刘宝元同属滨州沾化地区，计划申请3件实用新型专利用于职称评定',
    '{"professional_background": "农业种植、种业推广专家", "application_goal": "职称评定、技术成果保护", "planned_patents": 3, "region": "滨州沾化", "related_customers": ["孙俊霞", "刘宝元"]}'
) ON CONFLICT (customer_id) DO UPDATE SET
    phone = EXCLUDED.phone,
    address = EXCLUDED.address,
    wechat_id = EXCLUDED.wechat_id,
    updated_at = CURRENT_TIMESTAMP;

-- 获取客户ID并创建任务记录
DO $$
DECLARE
    v_customer_id UUID;
    v_task_id UUID;
BEGIN
    SELECT customer_id INTO v_customer_id FROM customers WHERE customer_name = '范文新' AND phone = '15966352598';

    IF v_customer_id IS NOT NULL THEN
        -- 创建任务管理记录：专利名称确定任务
        INSERT INTO task_management (
            task_id,
            customer_id,
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
            'TASK20251217001',
            '为范文新客户确定3件实用新型专利名称',
            '专利名称确定',
            '待执行',
            'high',
            '范文新客户计划申请3件实用新型专利，需要根据其农业种植、种业推广的专业背景，确定具体、准确、有价值的专利名称',
            '2025-12-18',
            '徐健',
            0,
            '{"emergency_level": "中等", "importance_level": "高", "execution_time": "2025-12-18 上午", "patent_requirements": {"patent_type": "实用新型", "application_count": 3}}',
            '2025-12-17 15:47:00'
        ) RETURNING task_id INTO v_task_id;

        -- 创建文档管理记录
        INSERT INTO document_management (
            document_id,
            customer_id,
            task_id,
            document_type,
            document_name,
            file_path,
            processing_status,
            notes,
            metadata
        ) VALUES (
            gen_random_uuid(),
            v_customer_id,
            v_task_id,
            '客户档案',
            '客户档案_范文新_20251217.json',
            '/Users/xujian/Athena工作平台/_BACKUP_TO_EXTERNAL_DRIVE/expired_reports_and_data/客户档案_范文新_20251217.json',
            '已完成',
            '客户基本信息和专利需求规划档案',
            '{"upload_date": "2025-12-17", "status": "已完成"}'
        );

        INSERT INTO document_management (
            document_id,
            customer_id,
            task_id,
            document_type,
            document_name,
            file_path,
            processing_status,
            notes,
            metadata
        ) VALUES (
            gen_random_uuid(),
            v_customer_id,
            v_task_id,
            '专利候选名单',
            '范文新专利候选名单_20251218.md',
            '/Users/xujian/Athena工作平台/docs/technical/范文新专利候选名单_20251218.md',
            '已完成',
            '包含6个实用新型专利候选名称和1个发明专利方向，推荐方案A',
            '{"creation_date": "2025-12-18", "status": "已完成", "recommendation": "方案A"}'
        );

        -- 创建项目里程碑
        INSERT INTO project_milestones (
            milestone_id,
            customer_id,
            milestone_name,
            milestone_type,
            planned_date,
            status,
            description,
            deliverables
        ) VALUES (
            gen_random_uuid(),
            v_customer_id,
            '任务创建完成',
            '任务管理',
            '2025-12-17',
            '已完成',
            '已创建范文新客户专利名称确定任务，任务编号TASK20251217001',
            '{"task_number": "TASK20251217001", "creation_time": "2025-12-17 15:47:00", "creator": "徐健"}'
        );

        INSERT INTO project_milestones (
            milestone_id,
            customer_id,
            milestone_name,
            milestone_type,
            planned_date,
            status,
            description,
            deliverables
        ) VALUES (
            gen_random_uuid(),
            v_customer_id,
            '专利名称确定',
            '申请准备',
            '2025-12-18',
            '进行中',
            '按计划在12月18日上午确定3件实用新型专利名称，推荐方案A',
            '{"planned_time": "2025-12-18 上午", "recommended_plan": "方案A"}'
        );

        -- 创建沟通记录
        INSERT INTO communication_records (
            record_id,
            customer_id,
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
            '任务创建',
            '2025-12-17',
            '徐健',
            '创建专利名称确定任务',
            '为范文新客户创建专利名称确定任务TASK20251217001，计划在12月18日上午确定3件实用新型专利名称',
            '任务创建成功，制定了详细的执行计划',
            true,
            '按计划于2025-12-18上午9:00联系客户确认技术方案',
            '{"task_priority": "high", "execution_deadline": "2025-12-18 12:00", "wechat_id": "茉莉"}'
        );

        RAISE NOTICE '范文新客户数据同步完成，客户ID: %', v_customer_id;
    ELSE
        RAISE NOTICE '未找到范文新客户记录';
    END IF;
END $$;

COMMIT;