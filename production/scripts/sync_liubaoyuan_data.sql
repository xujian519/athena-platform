-- 同步刘宝元客户数据到业务管理系统
-- Sync Liu Baoyuan Customer Data to Business Management System
-- 作者: 小诺·双鱼座 💖
-- 创建时间: 2025-12-29

\c phoenix_prod;

-- 插入刘宝元客户信息
INSERT INTO customers (
    customer_id,
    customer_name,
    phone,
    email,
    profession,
    specialization,
    contact_person,
    contact_phone,
    region,
    customer_type,
    status,
    notes,
    metadata
) VALUES (
    gen_random_uuid(),
    '刘宝元',
    '待补充',
    NULL,
    '基层农业推广人员',
    '农业种植技术推广、种业推广、农作物培育',
    '刘宝元',
    '待补充',
    '山东省滨州市沾化区',
    'individual',
    'active',
    '基层农业推广人员，希望设计3-4个软件协助日常工作。已提供四个软件方案：1）农技推广智能助手App 2）农业技术知识库查询工具 3）农技推广活动管理工具 4）农户需求反馈收集平台。与范文新、孙俊霞同属滨州沾化地区。',
    '{"software_proposals": ["农技推广智能助手App", "农业技术知识库查询工具", "农技推广活动管理工具", "农户需求反馈收集平台"], "proposal_date": "2025-12-29", "related_customers": ["范文新", "孙俊霞"], "region": "滨州沾化"}'
) ON CONFLICT (customer_id) DO UPDATE SET
    specialization = EXCLUDED.specialization,
    region = EXCLUDED.region,
    notes = EXCLUDED.notes,
    updated_at = CURRENT_TIMESTAMP;

-- 获取客户ID并创建相关记录
DO $$
DECLARE
    v_customer_id UUID;
BEGIN
    SELECT customer_id INTO v_customer_id FROM customers WHERE customer_name = '刘宝元' AND region = '山东省滨州市沾化区';

    IF v_customer_id IS NOT NULL THEN
        -- 创建任务管理记录：确认软件方案需求
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
            task_details,
            created_at
        ) VALUES (
            gen_random_uuid(),
            v_customer_id,
            'TASK20251229001',
            '刘宝元软件方案需求确认',
            '需求确认',
            '待处理',
            'high',
            '与刘宝元客户确认四个软件方案是否符合实际工作需求，了解专利申请意向',
            '2026-01-05',
            '{"software_proposals": 4, "next_steps": ["电话沟通确认需求", "了解专利申请意向", "协商服务费用", "确定开发或专利申请方向"], "contact_required": true}',
            '2025-12-29 10:00:00'
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
            '软件方案提案',
            '需求分析',
            '2025-12-29',
            '已完成',
            '已提供4个软件方案供客户选择，等待客户确认',
            '{"proposals": 4, "software_list": ["农技推广智能助手App", "农业技术知识库查询工具", "农技推广活动管理工具", "农户需求反馈收集平台"]}'
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
            '需求确认完成',
            '需求分析',
            '2026-01-05',
            '待开始',
            '完成与客户的需求确认沟通，确定最终服务方向',
            '{"deliverables": ["需求确认记录", "服务方向确定", "费用协商", "合同准备"]}'
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
            '文档/分析',
            '2025-12-29',
            '徐健',
            '软件方案提案',
            '根据客户基层农业推广工作特点，提供4个实用软件方案，并记录工作进度',
            '客户已收到方案，待后续沟通确认',
            true,
            '电话联系客户确认方案是否符合实际需求',
            '{"total_proposals": 4, "software_focus": "基层农业推广工具", "related_region": "滨州沾化"}'
        );

        -- 创建财务记录（待付款状态）
        INSERT INTO payment_records (
            payment_id,
            customer_id,
            payment_type,
            amount,
            status,
            due_date,
            payment_details,
            metadata
        ) VALUES (
            gen_random_uuid(),
            v_customer_id,
            '服务费',
            0,
            'pending',
            NULL,
            '{"note": "费用待协商，取决于客户选择的服务类型（软件开发或专利申请）"}',
            '{"customer_status": "正式客户", "payment_status": "未到账"}'
        );

        RAISE NOTICE '刘宝元客户数据同步完成，客户ID: %', v_customer_id;
    ELSE
        RAISE NOTICE '未找到刘宝元客户记录';
    END IF;
END $$;

COMMIT;
