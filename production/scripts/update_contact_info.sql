-- 更新锦州医科大学联系人信息
-- Update Contact Information for Jinzhou Medical University
-- 作者: 小诺·双鱼公主
-- 更新时间: 2025-12-22
-- 联系人：冯展波，微信号：fzb200488

\c phoenix_prod;

-- 更新客户联系人信息
UPDATE customers
SET
    contact_person = '冯展波',
    phone = NULL,  -- 如有电话号码可以添加
    wechat_id = 'fzb200488',
    notes = '高等院校客户，涉及天麻苷元与对乙酰氨基酚孪药专利申请，收到第二次审查意见需要答复。联系人：冯展波，微信号：fzb200488',
    updated_at = CURRENT_TIMESTAMP,
    metadata = jsonb_set(
        COALESCE(metadata, '{}')::jsonb,
        '{contact_info}',
        '{"contact_person": "冯展波", "wechat_id": "fzb200488", "last_updated": "2025-12-22"}'::jsonb
    )
WHERE customer_name = '锦州医科大学';

-- 添加沟通记录
DO $$
DECLARE
    v_customer_id UUID;
    v_application_id UUID;
BEGIN
    SELECT customer_id INTO v_customer_id FROM customers WHERE customer_name = '锦州医科大学';
    SELECT application_id INTO v_application_id FROM patent_applications WHERE customer_id = v_customer_id AND application_number = '202411792145.X' LIMIT 1;

    IF v_customer_id IS NOT NULL AND v_application_id IS NOT NULL THEN
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
            '联系人更新',
            '2025-12-22',
            '徐健',
            '更新客户联系人信息',
            '已将锦州医科大学客户联系人更新为冯展波，微信号：fzb200488，便于后续审查意见答复的沟通协调',
            true,
            '在审查意见答复过程中与冯展波保持沟通',
            '{"contact_person": "冯展波", "wechat_id": "fzb200488", "update_reason": "审查意见答复工作需要"}'
        );

        RAISE NOTICE '联系人信息更新成功：冯展波，微信号：fzb200488';
    END IF;
END $$;

-- 验证更新结果
SELECT '✅ 联系人信息更新成功' as update_status;
SELECT
    customer_name,
    contact_person,
    phone,
    wechat_id,
    updated_at
FROM customers
WHERE customer_name = '锦州医科大学';

COMMIT;