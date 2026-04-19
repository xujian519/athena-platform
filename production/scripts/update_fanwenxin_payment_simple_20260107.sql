-- 范文新客户付款记录更新脚本（简化版）
-- 更新时间: 2026-01-07
-- 付款金额: 8000元（微信支付）

\c phoenix_prod;

-- 更新客户财务状态
UPDATE customers
SET
    payment_status = 'partial_paid',
    total_paid = 8000.00,
    remaining_balance = 5500.00,
    payment_progress = 59.3,
    last_payment_date = '2026-01-07',
    notes = '首期付款8000元(微信)，总费用13500元，剩余5500元待付。包含4件专利：3件实用新型(2500元/件)+1件发明专利(6000元)',
    updated_at = NOW()
WHERE name = '范文新' AND phone = '15966352598';

-- 显示更新结果
SELECT
    '✅ 数据库更新成功' AS "状态",
    name AS "客户姓名",
    phone AS "联系电话",
    total_paid AS "已付金额(元)",
    remaining_balance AS "待付金额(元)",
    ROUND(payment_progress, 1) AS "付款进度(%)",
    TO_CHAR(last_payment_date, 'YYYY-MM-DD') AS "付款日期",
    payment_status AS "付款状态"
FROM customers
WHERE name = '范文新' AND phone = '15966352598';

-- 添加注释
COMMENT ON customers IS '范文新付款记录已更新：2026-01-07收到8000元微信付款';
