-- 更新李艳客户付款状态
-- Update Li Yan Customer Payment Status
-- 作者: 小诺·双鱼座 💖
-- 创建时间: 2025-12-29

\c phoenix_prod;

-- 更新客户状态为正式客户并标记已付款
UPDATE customers
SET status = 'formal',
    notes = CONCAT(COALESCE(notes, ''), ' [已付款6495元 - 2025-12-29]'),
    updated_at = CURRENT_TIMESTAMP
WHERE customer_name = '李艳' AND phone = '13105432567';

-- 创建或更新付款记录
DO $$
DECLARE
    v_customer_id UUID;
    v_payment_id UUID;
BEGIN
    SELECT customer_id INTO v_customer_id FROM customers WHERE customer_name = '李艳' AND phone = '13105432567';

    IF v_customer_id IS NOT NULL THEN
        -- 检查是否已有付款记录
        SELECT payment_id INTO v_payment_id
        FROM payment_records
        WHERE customer_id = v_customer_id AND payment_type = '专利申请费'
        LIMIT 1;

        IF v_payment_id IS NOT NULL THEN
            -- 更新现有付款记录
            UPDATE payment_records
            SET amount = 6495,
                status = 'paid',
                payment_date = '2025-12-29',
                payment_details = '{
                    "patent_count": 3,
                    "fee_breakdown": {
                        "agency_fee": {"unit": 2000, "total": 6000},
                        "official_fee": {"unit": 165, "total": 495}
                    },
                    "total": 6495,
                    "payment_status": "已付清",
                    "payment_date": "2025-12-29",
                    "patents": [
                        "滴灌带防堵塞自清洁装置",
                        "中药材种植用起垄器",
                        "山地林果采摘辅助工具"
                    ]
                }',
                updated_at = CURRENT_TIMESTAMP
            WHERE payment_id = v_payment_id;

            RAISE NOTICE '已更新李艳付款记录，付款ID: %', v_payment_id;
        ELSE
            -- 创建新的付款记录
            INSERT INTO payment_records (
                payment_id,
                customer_id,
                payment_type,
                amount,
                status,
                payment_date,
                due_date,
                payment_details,
                metadata,
                created_at
            ) VALUES (
                gen_random_uuid(),
                v_customer_id,
                '专利申请费',
                6495,
                'paid',
                '2025-12-29',
                NULL,
                '{
                    "patent_count": 3,
                    "fee_breakdown": {
                        "agency_fee": {"unit": 2000, "total": 6000},
                        "official_fee": {"unit": 165, "total": 495}
                    },
                    "total": 6495,
                    "payment_status": "已付清",
                    "payment_date": "2025-12-29",
                    "patents": [
                        "滴灌带防堵塞自清洁装置",
                        "中药材种植用起垄器",
                        "山地林果采摘辅助工具"
                    ]
                }',
                '{
                    "customer_name": "李艳",
                    "payment_confirmed": true,
                    "invoice_required": true
                }',
                '2025-12-29 10:00:00'
            );

            RAISE NOTICE '已创建李艳付款记录';
        END IF;

        -- 更新项目里程碑
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
            '付款完成',
            '财务',
            '2025-12-29',
            '已完成',
            '客户已支付专利申请费用6495元（3件专利），正式进入服务流程',
            '{"payment_amount": 6495, "patent_count": 3, "payment_method": "已确认"}'
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
            '付款确认',
            '2025-12-29',
            '徐健',
            '付款确认及专利申请启动',
            '客户已确认选择3个专利并支付费用6495元：1）滴灌带防堵塞自清洁装置 2）中药材种植用起垄器 3）山地林果采摘辅助工具',
            '付款已确认，准备进入专利申请材料准备阶段',
            true,
            '开始准备3个专利的申请材料和技术方案',
            '{"payment_confirmed": true, "amount": 6495, "patents_confirmed": 3}'
        );

        -- 创建下一阶段任务
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
            '李艳专利申请材料准备',
            '材料准备',
            '待处理',
            'high',
            '为李艳客户准备3个专利的申请材料，包括技术方案、附图、权利要求书等',
            '2025-01-15',
            '{
                "patents": [
                    {
                        "name": "滴灌带防堵塞自清洁装置",
                        "tasks": ["技术方案完善", "附图绘制", "权利要求撰写"]
                    },
                    {
                        "name": "中药材种植用起垄器",
                        "tasks": ["技术方案完善", "附图绘制", "权利要求撰写"]
                    },
                    {
                        "name": "山地林果采摘辅助工具",
                        "tasks": ["技术方案完善", "附图绘制", "权利要求撰写"]
                    }
                ],
                "next_steps": [
                    "联系客户确认技术细节",
                    "准备专利附图",
                    "撰写技术交底书",
                    "准备申请文件"
                ]
            }',
            '2025-12-29 10:00:00'
        );

        RAISE NOTICE '李艳客户付款状态更新完成，客户ID: %', v_customer_id;

    ELSE
        RAISE NOTICE '未找到李艳客户记录';
    END IF;
END $$;

-- 查询验证
SELECT
    c.customer_name,
    c.status as customer_status,
    c.phone,
    pr.amount,
    pr.status as payment_status,
    pr.payment_date,
    pr.payment_details->>'payment_status' as payment_note
FROM customers c
LEFT JOIN payment_records pr ON c.customer_id = pr.customer_id
WHERE c.customer_name = '李艳' AND c.phone = '13105432567';

COMMIT;
