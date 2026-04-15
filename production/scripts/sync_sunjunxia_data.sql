-- 同步孙俊霞客户数据到业务管理系统
-- Sync Sun Junxia Customer Data to Business Management System
-- 作者: 小诺·双鱼公主
-- 创建时间: 2025-12-22

\c phoenix_prod;

-- 1. 插入客户信息
INSERT INTO customers (
    customer_id,
    customer_name,
    phone,
    address,
    postal_code,
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
    '2a043af8-b99a-4fec-a313-457a3d52d646',
    '孙俊霞',
    '15206872916',
    '山东省滨州市沾化区富国街道富桥路175号',
    '256800',
    '基层农业技术推广专家',
    '农作物技术、幼苗培育',
    '孙俊霞',
    '15206872916',
    '山东省滨州市沾化区',
    'individual',
    'active',
    '基层农业技术推广专家，专注于农作物技术和幼苗培育，申请专利用于职称晋升',
    '{"application_goal": "职称晋升", "experience_level": "专业经验丰富，基层推广能力强", "customer_id_original": "sunjunxia_20251216"}'
) ON CONFLICT (customer_id) DO UPDATE SET
    phone = EXCLUDED.phone,
    address = EXCLUDED.address,
    postal_code = EXCLUDED.postal_code,
    updated_at = CURRENT_TIMESTAMP;

-- 获取客户ID和专利申请ID
DO $$
DECLARE
    v_customer_id UUID;
    v_application_id UUID;
BEGIN
    SELECT customer_id INTO v_customer_id FROM customers WHERE customer_name = '孙俊霞' AND phone = '15206872916';

    IF v_customer_id IS NOT NULL THEN
        -- 2. 插入专利申请信息
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
            '农作物幼苗培育保护罩',
            '实用新型',
            '农业种植技术 - 农作物保护技术',
            '准备中',
            '职称晋升',
            '[{"sequence": 1, "name": "孙俊霞", "education": "待补充", "professional_title": "基层农业技术推广专家", "workplace": "待补充", "contribution": "主要负责幼苗保护技术方案设计和基层应用验证"}]',
            '[{"name": "孙俊霞", "id_type": "身份证", "id_number": "待从确认书提取"}]',
            '农作物幼苗培育保护罩技术方案，专注于解决幼苗在培育过程中的保护问题，提高成活率和培育质量',
            false,
            '{"priority_field": "农业种植技术", "customer_background": {"profession": "基层农业技术推广专家", "specialization": "农作物技术", "application_goal": "职称晋升", "experience_level": "专业经验丰富，基层推广能力强"}, "application_number_original": "PA20251217A1B2C3D4"}'
        )
        RETURNING application_id INTO v_application_id;

        -- 3. 插入财务记录
        INSERT INTO financial_records (
            record_id,
            customer_id,
            application_id,
            record_type,
            amount,
            payment_status,
            payment_date,
            invoice_number,
            total_amount,
            fee_details,
            discount_amount,
            discount_reason,
            notes
        ) VALUES (
            gen_random_uuid(),
            v_customer_id,
            v_application_id,
            '代理费',
            2100.00,
            '已支付',
            '2025-12-17',
            'YL20251217001',
            2100.00,
            '{"original_amount": 3000.00, "actual_amount": 2100.00, "adjustment_reason": "实际收费调整"}',
            900.00,
            '实际收费调整',
            '代理费已支付，发票号：YL20251217001'
        );

        INSERT INTO financial_records (
            record_id,
            customer_id,
            application_id,
            record_type,
            amount,
            payment_status,
            payment_date,
            total_amount,
            fee_details,
            notes
        ) VALUES (
            gen_random_uuid(),
            v_customer_id,
            v_application_id,
            '官方费用',
            165.00,
            '已支付',
            '2025-12-17',
            165.00,
            '{"申请费": 75.00, "印刷费": 50.00, "证书费": 40.00}',
            '官方费用已支付，享受费减政策，节省585元'
        );

        -- 4. 插入任务管理记录
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
            task_details,
            created_at
        ) VALUES (
            gen_random_uuid(),
            v_customer_id,
            v_application_id,
            'TASK20251218001',
            '完善技术交底书',
            '技术交底',
            '待处理',
            'high',
            '基于技术方案完善技术交底书和说明书，准备完整的申请材料',
            '2025-12-20',
            '{"next_steps": ["技术方案完善", "说明书撰写", "权利要求书准备", "附图绘制"], "progress_items": ["技术交底书模板准备", "技术细节确认", "创新点描述", "实施例完善"]}',
            '2025-12-22 10:00:00'
        );

        -- 5. 插入文档管理记录
        INSERT INTO document_management (
            document_id,
            customer_id,
            application_id,
            document_type,
            document_name,
            file_path,
            processing_status,
            notes,
            metadata
        ) VALUES (
            gen_random_uuid(),
            v_customer_id,
            v_application_id,
            '专利申请确认书',
            '专利申请确认表(2).doc',
            '/Users/xujian/Nutstore Files/工作/孙俊霞1件/专利申请确认表(2).doc',
            '需要手动录入关键信息',
            '需要从确认书提取申请人身份证号码、申请地址和邮编、联系电话、具体费用明细、代理机构信息',
            '{"upload_date": "2025-12-17", "processed_by": "小娜系统", "manual_input_required": true, "missing_fields": ["申请人身份证号码", "申请地址和邮编", "联系电话", "具体费用明细", "代理机构信息"]}'
        );

        INSERT INTO document_management (
            document_id,
            customer_id,
            application_id,
            document_type,
            document_name,
            file_path,
            processing_status,
            upload_date,
            metadata
        ) VALUES (
            gen_random_uuid(),
            v_customer_id,
            v_application_id,
            '技术方案',
            '孙俊霞-幼苗培育保护罩技术方案.md',
            '/Users/xujian/Athena工作平台/docs/孙俊霞-幼苗培育保护罩技术方案.md',
            '已完成',
            '2025-12-17',
            '{"status": "已完成", "completion_date": "2025-12-17"}'
        );

        -- 6. 插入项目里程碑
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
            '费用支付完成',
            '财务阶段',
            '2025-12-17',
            '已完成',
            '客户已完成所有费用支付，包括代理费2100元和官方费用165元',
            '{"payment_confirmation": true, "total_paid": 2265.00, "savings": 1485.00}'
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
            '技术交底书完成',
            '申请准备',
            '2025-12-20',
            '进行中',
            '完成技术交底书和说明书撰写，准备完整的申请材料',
            '{"deliverables": ["技术交底书", "说明书", "权利要求书初稿", "技术附图"], "current_status": "进行中"}'
        );

        -- 7. 插入沟通记录
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
            '面谈',
            '2025-12-17',
            '徐健',
            '费用确认和支付',
            '与孙俊霞确认费用明细，客户完成支付：代理费2100元 + 官方费用165元，总计2265元',
            '费用已全部付清，项目可按计划全力推进',
            false,
            '准备技术交底书模板，联系客户确认技术细节',
            '{"total_amount": 2265.00, "payment_method": "现场支付", "savings": 1485.00}'
        );

        RAISE NOTICE '孙俊霞客户数据同步完成，客户ID: %', v_customer_id;
    ELSE
        RAISE NOTICE '未找到孙俊霞客户记录';
    END IF;
END $$;

COMMIT;