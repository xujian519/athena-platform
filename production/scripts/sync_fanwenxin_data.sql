-- 同步范文新客户数据到业务管理系统
-- Sync Fan Wenxin Customer Data to Business Management System
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
            '{"emergency_level": "中等", "importance_level": "高", "execution_time": "2025-12-18 上午", "deadline": "2025-12-18 12:00", "patent_requirements": {"patent_type": "实用新型", "application_count": 3, "technical_field": "农业种植、种业推广、农作物培育", "application_goal": "职称评定、技术成果保护"}, "key_directions": ["农作物种植装置改进", "种子处理装置", "农业培育装置"], "execution_plan": {"步骤1": "联系范文新确认技术方案细节", "时间": "2025-12-18 上午9:00-9:30", "方式": "电话沟通或微信联系"}, "步骤2": "分析技术方案并进行专利检索", "时间": "2025-12-18 上午9:30-10:30"}, "步骤3": "制定专利名称方案", "时间": "2025-12-18 上午10:30-11:30"}, "步骤4": "与客户确认专利名称", "时间": "2025-12-18 上午11:30-12:00"}}',
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
            '{"upload_date": "2025-12-17", "status": "已完成", "contains": ["客户基本信息", "专利需求规划", "联系方式"]}'
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
            '包含6个实用新型专利候选名称和1个发明专利方向，推荐方案A：智能播种装置、包衣催芽一体化装置、可调节培育盘、盐碱地改良方法',
            '{"creation_date": "2025-12-18", "status": "已完成", "recommendation": "方案A", "utility_patents": 3, "invention_patents": 1, "total_cost": 13500}'
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
            '{"task_number": "TASK20251217001", "creation_time": "2025-12-17 15:47:00", "creator": "徐健", "patent_count": 3}'
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
            '{"planned_time": "2025-12-18 上午", "recommended_plan": "方案A", "patent_names": ["智能播种装置", "包衣催芽一体化装置", "可调节培育盘"], "backup_options": 6}'
        );

        -- 创建沟通记录
        INSERT INTO communication_records (
            record_id,
            customer_id,
            task_id,
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
            v_task_id,
            '任务创建',
            '2025-12-17',
            '徐健',
            '创建专利名称确定任务',
            '为范文新客户创建专利名称确定任务TASK20251217001，计划在12月18日上午确定3件实用新型专利名称',
            '任务创建成功，制定了详细的执行计划和备选方案',
            true,
            '按计划于2025-12-18上午9:00联系客户确认技术方案',
            '{"task_priority": "high", "execution_deadline": "2025-12-18 12:00", "communication_method": "电话或微信", "wechat_id": "茉莉"}'
        );

        -- 创建专利检索记录
        INSERT INTO patent_search_records (
            search_id,
            customer_id,
            task_id,
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
            v_task_id,
            '技术调研',
            '农业种植装置、种子处理、农作物培育',
            '{"keywords": ["农业种植", "种业推广", "农作物培育", "智能播种", "种子处理", "育苗装置"], "ipc_classifications": ["A01C", "A01G"], "time_range": "最近10年"}',
            '2800万+专利数据库',
            '2025-12-18',
            0,
            '{"search_status": "计划执行", "expected_competitors": "中等", "blue_ocean_potential": "高", "focus_areas": ["结构创新", "功能集成", "智能化"]}',
            '推荐重点关注农作物种植用标准化间距调节器等0竞争领域',
            '{"data_source": "2800万专利数据库", "analysis_method": "关键词组合+IPC分类", "expected_outcome": "3-5个高质量专利名称"}'
        );

        RAISE NOTICE '范文新客户数据同步完成，客户ID: %', v_customer_id;
    ELSE
        RAISE NOTICE '未找到范文新客户记录';
    END IF;
END $$;

COMMIT;