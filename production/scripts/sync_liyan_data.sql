-- 同步李艳客户数据到业务管理系统
-- Sync Li Yan Customer Data to Business Management System
-- 作者: 小诺·双鱼公主
-- 创建时间: 2025-12-22

\c phoenix_prod;

-- 插入李艳客户信息
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
    '李艳',
    '13105432567',
    NULL,
    '农业技术专家',
    '农业种植技术、节水灌溉、中药材种植、农业环保',
    '李艳',
    '13105432567',
    '中国',
    'individual',
    'active',
    '农业技术专家，已确认选择3项专利申请：1）滴灌带铺设辅助装置 2）中草药种植用土壤改良装置 4）农业废弃物高效好氧堆肥装置',
    '{"confirmed_patents": ["滴灌带铺设辅助装置", "中草药种植用土壤改良装置", "农业废弃物高效好氧堆肥装置"], "selection_date": "2025-12-22", "total_patents": 3}'
) ON CONFLICT (customer_id) DO UPDATE SET
    phone = EXCLUDED.phone,
    specialization = EXCLUDED.specialization,
    updated_at = CURRENT_TIMESTAMP;

-- 获取客户ID并创建专利申请记录
DO $$
DECLARE
    v_customer_id UUID;
    v_patent_application_id UUID;
BEGIN
    SELECT customer_id INTO v_customer_id FROM customers WHERE customer_name = '李艳' AND phone = '13105432567';

    IF v_customer_id IS NOT NULL THEN
        -- 创建第1个专利申请：滴灌带铺设辅助装置
        INSERT INTO patent_applications (
            application_id,
            customer_id,
            patent_name,
            patent_type,
            technical_field,
            application_status,
            application_goal,
            inventors,
            applicants,
            technical_description,
            blue_ocean_potential,
            metadata
        ) VALUES (
            gen_random_uuid(),
            v_customer_id,
            '滴灌带铺设辅助装置',
            '实用新型',
            '农业节水灌溉技术',
            '待技术确认',
            '技术成果保护',
            '[{"sequence": 1, "name": "李艳", "contribution": "滴灌带铺设技术方案设计"}]',
            '[{"name": "李艳"}]',
            '用于辅助滴灌带铺设的装置，提高铺设效率和准确性，减少人工操作难度',
            false,
            '{"patent_number": 1, "selection_status": "客户已确认", "selection_date": "2025-12-22"}'
        );

        -- 创建第2个专利申请：中草药种植用土壤改良装置
        INSERT INTO patent_applications (
            application_id,
            customer_id,
            patent_name,
            patent_type,
            technical_field,
            application_status,
            application_goal,
            inventors,
            applicants,
            technical_description,
            blue_ocean_potential,
            metadata
        ) VALUES (
            gen_random_uuid(),
            v_customer_id,
            '中草药种植用土壤改良装置',
            '实用新型',
            '中药材种植技术',
            '待技术确认',
            '技术成果保护',
            '[{"sequence": 1, "name": "李艳", "contribution": "土壤改良技术方案设计"}]',
            '[{"name": "李艳"}]',
            '专用于中草药种植的土壤改良装置，改善土壤结构，提高中药材质量和产量',
            false,
            '{"patent_number": 2, "selection_status": "客户已确认", "selection_date": "2025-12-22"}'
        );

        -- 创建第3个专利申请：农业废弃物高效好氧堆肥装置（对应原第4项）
        INSERT INTO patent_applications (
            application_id,
            customer_id,
            patent_name,
            patent_type,
            technical_field,
            application_status,
            application_goal,
            inventors,
            applicants,
            technical_description,
            blue_ocean_potential,
            metadata
        ) VALUES (
            gen_random_uuid(),
            v_customer_id,
            '农业废弃物高效好氧堆肥装置',
            '实用新型',
            '农业环保技术',
            '待技术确认',
            '技术成果保护',
            '[{"sequence": 1, "name": "李艳", "contribution": "堆肥装置技术方案设计"}]',
            '[{"name": "李艳"}]',
            '用于农业废弃物处理的高效好氧堆肥装置，提高堆肥效率，减少环境污染',
            false,
            '{"patent_number": 4, "selection_status": "客户已确认", "selection_date": "2025-12-22", "original_position": 4}'
        );

        -- 创建任务管理记录：技术方案确认
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
            'TASK20251222001',
            '李艳客户专利技术方案确认',
            '技术确认',
            '待处理',
            'high',
            '与李艳客户确认3项专利的具体技术方案和创新点',
            '2025-12-25',
            '{"confirmed_patents": ["滴灌带铺设辅助装置", "中草药种植用土壤改良装置", "农业废弃物高效好氧堆肥装置"], "next_steps": ["技术细节确认", "创新点分析", "实施例准备", "技术交底书撰写"], "customer_contact": "13105432567"}',
            '2025-12-22 10:00:00'
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
            '专利选择确认',
            '申请准备',
            '2025-12-22',
            '已完成',
            '客户已确认选择3项专利申请，准备技术方案确认',
            '{"confirmed_patents": 3, "selection_date": "2025-12-22", "patent_list": ["滴灌带铺设辅助装置", "中草药种植用土壤改良装置", "农业废弃物高效好氧堆肥装置"]}'
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
            '技术方案完成',
            '申请准备',
            '2025-12-25',
            '待开始',
            '完成3项专利的技术方案确认和技术交底书准备',
            '{"deliverables": ["3份技术交底书", "技术附图", "创新点说明", "实施例"]}'
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
            '微信/电话',
            '2025-12-22',
            '徐健',
            '专利选择确认',
            '李艳客户确认选择3项专利申请：1）滴灌带铺设辅助装置 2）中草药种植用土壤改良装置 4）农业废弃物高效好氧堆肥装置',
            '客户已明确选择，准备进入技术方案确认阶段',
            true,
            '联系客户确认3项专利的具体技术细节和创新点',
            '{"total_patents": 3, "contact_phone": "13105432567", "selection_completion": true}'
        );

        RAISE NOTICE '李艳客户数据同步完成，客户ID: %', v_customer_id;
    ELSE
        RAISE NOTICE '未找到李艳客户记录';
    END IF;
END $$;

COMMIT;