-- 同步张国艳客户数据到业务管理系统
-- Sync Zhang Guoyan Customer Data to Business Management System
-- 作者: 小诺·双鱼公主
-- 创建时间: 2025-12-22

\c phoenix_prod;

-- 插入张国艳客户信息
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
    '张国艳',
    NULL,
    NULL,
    '农业技术推广员、农作物种植专家',
    '农业技术推广、农作物种植',
    '张国艳',
    NULL,
    '中国',
    'individual',
    'active',
    '农业技术推广专家，已制定4项实用新型专利命名方案，包含1个蓝海专利（农作物种植用标准化间距调节器，0竞争）',
    '{"plan_status": "已完成", "patent_count": 4, "blue_ocean_count": 1, "plan_date": "2025-12-18"}'
) ON CONFLICT (customer_id) DO UPDATE SET
    specialization = EXCLUDED.specialization,
    updated_at = CURRENT_TIMESTAMP;

-- 获取客户ID并创建专利申请记录
DO $$
DECLARE
    v_customer_id UUID;
BEGIN
    SELECT customer_id INTO v_customer_id FROM customers WHERE customer_name = '张国艳';

    IF v_customer_id IS NOT NULL THEN
        -- 创建第1个专利申请：农技推广用便携式多媒体展示装置
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
            '农技推广用便携式多媒体展示装置',
            '实用新型',
            '农技推广设备',
            '方案已制定',
            '职称晋升、技术推广',
            '[{"sequence": 1, "name": "张国艳", "contribution": "多媒体展示装置技术方案设计"}]',
            '[{"name": "张国艳"}]',
            '一体化多媒体展示+便携式设计+农村适用，解决基层农技推广展示需求',
            false,
            '{"patent_order": 1, "competition_analysis": "类似专利17个，竞争较少", "authorization_prospects": "⭐⭐⭐⭐ 高", "naming_advantages": ["明确体现农技推广应用场景", "突出便携性和多媒体特色", "符合农村基层推广需求", "技术特征清晰明确"]}'
        );

        -- 创建第2个专利申请：智能化农技推广信息推送终端
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
            '智能化农技推广信息推送终端',
            '实用新型',
            '农业信息化设备',
            '方案已制定',
            '职称晋升、技术推广',
            '[{"sequence": 1, "name": "张国艳", "contribution": "信息推送终端技术方案设计"}]',
            '[{"name": "张国艳"}]',
            '智能推送+精准匹配+农技推广专用，提高农业技术推广效率',
            false,
            '{"patent_order": 2, "competition_analysis": "相关专利8个，竞争低", "authorization_prospects": "⭐⭐⭐⭐⭐ 极高", "naming_advantages": ["突出智能化技术特征", "明确信息推送功能", "精准定位农技推广场景", "体现技术创新性"]}'
        );

        -- 创建第3个专利申请：农作物种植用标准化间距调节器（蓝海专利）
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
            '农作物种植用标准化间距调节器',
            '实用新型',
            '农作物种植机械',
            '方案已制定',
            '职称晋升、技术推广',
            '[{"sequence": 1, "name": "张国艳", "contribution": "间距调节器技术方案设计"}]',
            '[{"name": "张国艳"}]',
            '标准化种植+间距可调+多作物适用，解决标准化种植痛点',
            true,
            '{"patent_order": 3, "competition_analysis": "0个直接相关专利，完全蓝海", "authorization_prospects": "⭐⭐⭐⭐⭐ 极高", "naming_advantages": ["零竞争蓝海专利", "解决标准化种植痛点", "多作物适用性强", "体现技术创新价值"], "blue_ocean_opportunity": true}'
        );

        -- 创建第4个专利申请：多功能农作物幼苗培育保护装置
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
            '多功能农作物幼苗培育保护装置',
            '实用新型',
            '农业培育设备',
            '方案已制定',
            '职称晋升、技术推广',
            '[{"sequence": 1, "name": "张国艳", "contribution": "培育保护装置技术方案设计"}]',
            '[{"name": "张国艳"}]',
            '多功能集成+幼苗保护+智能环境调节，提高培育成活率',
            false,
            '{"patent_order": 4, "competition_analysis": "类似专利12个，竞争较少", "authorization_prospects": "⭐⭐⭐⭐ 高", "naming_advantages": ["突出多功能集成特色", "明确幼苗保护功能", "体现智能化特点", "技术实用性强"]}'
        );

        -- 创建任务管理记录：专利方案确认
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
            'TASK20251218002',
            '张国艳客户专利命名方案确认',
            '方案确认',
            '待客户确认',
            'high',
            '张国艳客户4项实用新型专利命名方案已制定完成，包含1个蓝海专利，等待客户最终确认',
            '2025-12-20',
            '{"patent_count": 4, "blue_ocean_count": 1, "recommended_combination": "方案A", "patent_names": ["农技推广用便携式多媒体展示装置", "智能化农技推广信息推送终端", "农作物种植用标准化间距调节器", "多功能农作物幼苗培育保护装置"], "key_advantages": ["覆盖全面", "技术先进", "地域特色", "授权概率高", "职称评定适配"], "cost_budget": {"utility_patents": 3, "unit_price": 2500, "total_cost": 7500}}',
            '2025-12-18 10:00:00'
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
            '专利命名方案完成',
            '方案制定',
            '2025-12-18',
            '已完成',
            '已完成4项实用新型专利命名方案，包含1个蓝海专利，等待客户确认',
            '{"patent_count": 4, "blue_ocean_discovery": "农作物种植用标准化间距调节器（0竞争）", "方案质量": "高质量，基于2800万专利数据分析", "authorization_probability": "高"}'
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
            '客户确认专利方案',
            '申请准备',
            '2025-12-20',
            '待开始',
            '联系客户确认专利命名方案，特别是蓝海专利的技术方案',
            '{"next_actions": ["联系客户确认", "解释蓝海专利价值", "确认技术细节", "准备申请材料"], "key_focus": "蓝海专利的价值说明"}'
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
            '方案制定完成',
            '2025-12-18',
            '小娜专业版',
            '专利命名方案制定完成',
            '基于2800万专利数据分析，为张国艳客户制定了4项实用新型专利命名方案，包含1个蓝海专利（农作物种植用标准化间距调节器，0竞争）',
            '方案制定完成，质量高，包含蓝海机会，需要联系客户确认',
            true,
            '尽快联系客户确认专利方案，重点说明蓝海专利价值',
            '{"patent_count": 4, "blue_ocean_count": 1, "data_driven": true, "database_size": "2800万+", "analysis_method": "关键词组合+IPC分类+时间范围"}'
        );

        RAISE NOTICE '张国艳客户数据同步完成，客户ID: %', v_customer_id;
    ELSE
        RAISE NOTICE '未找到张国艳客户记录';
    END IF;
END $$;

COMMIT;