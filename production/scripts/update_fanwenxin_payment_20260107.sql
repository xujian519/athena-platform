-- 范文新客户付款记录更新脚本
-- 更新时间: 2026-01-07
-- 付款金额: 8000元（微信支付）

\c phoenix_prod;

-- 1. 更新客户财务状态
UPDATE customers
SET
    payment_status = 'partial_paid',
    total_paid = 8000.00,
    remaining_balance = 5500.00,
    payment_progress = 59.3,
    last_payment_date = '2026-01-07',
    updated_at = NOW()
WHERE name = '范文新' AND phone = '15966352598';

-- 2. 插入付款记录
INSERT INTO payments (
    customer_id,
    payment_date,
    payment_method,
    amount,
    payment_type,
    status,
    notes,
    operator,
    created_at
)
SELECT
    id,
    '2026-01-07',
    '微信',
    8000.00,
    '专利代理费',
    'paid',
    '首期付款，用于4件专利申请（3件实用新型+1件发明专利）',
    '徐健',
    NOW()
FROM customers
WHERE name = '范文新' AND phone = '15966352598';

-- 3. 更新专利项目财务状态
UPDATE patent_projects
SET
    budget_status = 'partially_funded',
    allocated_budget = 8000.00,
    remaining_budget = 5500.00,
    updated_at = NOW()
WHERE customer_id = (SELECT id FROM customers WHERE name = '范文新' AND phone = '15966352598');

-- 4. 记录工作日志
INSERT INTO work_logs (
    customer_id,
    log_date,
    log_type,
    content,
    operator,
    created_at
)
SELECT
    id,
    '2026-01-07',
    'payment_received',
    '收到范文新客户首期付款8000元，通过微信支付。总费用13500元，剩余5500元待付。付款进度59.3%。',
    '徐健',
    NOW()
FROM customers
WHERE name = '范文新' AND phone = '15966352598';

-- 5. 验证更新结果
DO $$
DECLARE
    v_customer_name VARCHAR(50);
    v_total_paid NUMERIC;
    v_remaining_balance NUMERIC;
    v_payment_progress NUMERIC;
BEGIN
    SELECT name, total_paid, remaining_balance, payment_progress
    INTO v_customer_name, v_total_paid, v_remaining_balance, v_payment_progress
    FROM customers
    WHERE name = '范文新' AND phone = '15966352598';

    RAISE NOTICE '✅ 客户: %', v_customer_name;
    RAISE NOTICE '✅ 已付金额: % 元', v_total_paid;
    RAISE NOTICE '✅ 待付金额: % 元', v_remaining_balance;
    RAISE NOTICE '✅ 付款进度: % %%', v_payment_progress;
    RAISE NOTICE '========================================';
    RAISE NOTICE '范文新付款记录已成功更新到数据库！';
END $$;

-- 查询更新后的客户信息
SELECT
    name AS "客户姓名",
    phone AS "联系电话",
    total_paid AS "已付金额",
    remaining_balance AS "待付金额",
    payment_progress AS "付款进度(%)",
    last_payment_date AS "最后付款日期",
    payment_status AS "付款状态"
FROM customers
WHERE name = '范文新' AND phone = '15966352598';

-- 查询付款明细
SELECT
    p.payment_date AS "付款日期",
    p.payment_method AS "付款方式",
    p.amount AS "付款金额",
    p.status AS "状态",
    p.notes AS "备注"
FROM payments p
JOIN customers c ON p.customer_id = c.id
WHERE c.name = '范文新' AND c.phone = '15966352598'
ORDER BY p.payment_date DESC;
