-- 执行所有客户数据同步脚本
-- Execute All Customer Data Sync Scripts
-- 作者: 小诺·双鱼公主
-- 创建时间: 2025-12-22
-- 版本: v1.0.0 "完整数据同步"

-- 设置数据库连接
\c phoenix_prod;

-- 显示同步开始信息
SELECT '=== 开始执行客户确认申请项目数据同步 ===' as sync_status;
SELECT CURRENT_TIMESTAMP as sync_start_time;

-- 显示当前数据库中的客户数量（同步前）
SELECT '同步前' as phase, COUNT(*) as customer_count FROM customers;
SELECT '同步前' as phase, COUNT(*) as application_count FROM patent_applications;
SELECT '同步前' as phase, COUNT(*) as task_count FROM task_management;

-- 执行李艳客户数据同步
\echo '同步李艳客户数据...'
\i /Users/xujian/Athena工作平台/production/scripts/sync_liyan_data.sql

-- 执行张国艳客户数据同步
\echo '同步张国艳客户数据...'
\i /Users/xujian/Athena工作平台/production/scripts/sync_zhangguoyan_data.sql

-- 执行范文新客户数据同步
\echo '同步范文新客户数据...'
\i /Users/xujian/Athena工作平台/production/scripts/sync_fanwenxin_data.sql

-- 显示同步完成信息
SELECT '=== 客户数据同步完成 ===' as sync_status;
SELECT CURRENT_TIMESTAMP as sync_end_time;

-- 显示同步后的数据统计
SELECT '同步后' as phase, COUNT(*) as customer_count FROM customers;
SELECT '同步后' as phase, COUNT(*) as application_count FROM patent_applications;
SELECT '同步后' as phase, COUNT(*) as task_count FROM task_management;

-- 详细客户列表
SELECT
    customer_name,
    phone,
    profession,
    specialization,
    status,
    created_at
FROM customers
WHERE customer_name IN ('孙俊霞', '李艳', '张国艳', '范文新')
ORDER BY created_at;

-- 专利申请统计
SELECT
    c.customer_name,
    COUNT(pa.application_id) as patent_count,
    STRING_AGG(pa.patent_name, ', ' ORDER BY pa.created_at) as patent_names
FROM customers c
LEFT JOIN patent_applications pa ON c.customer_id = pa.customer_id
WHERE c.customer_name IN ('孙俊霞', '李艳', '张国艳', '范文新')
GROUP BY c.customer_name, c.customer_id
ORDER BY c.customer_name;

-- 任务管理统计
SELECT
    c.customer_name,
    COUNT(tm.task_id) as task_count,
    STRING_AGG(tm.task_title, '; ' ORDER BY tm.created_at) as task_list
FROM customers c
LEFT JOIN task_management tm ON c.customer_id = tm.customer_id
WHERE c.customer_name IN ('孙俊霞', '李艳', '张国艳', '范文新')
GROUP BY c.customer_name, c.customer_id
ORDER BY c.customer_name;

-- 财务记录统计
SELECT
    c.customer_name,
    COUNT(fr.record_id) as financial_record_count,
    COALESCE(SUM(fr.amount), 0) as total_amount,
    STRING_AGG(fr.record_type, ', ' ORDER BY fr.created_at) as record_types
FROM customers c
LEFT JOIN patent_applications pa ON c.customer_id = pa.customer_id
LEFT JOIN financial_records fr ON pa.application_id = fr.application_id
WHERE c.customer_name IN ('孙俊霞', '李艳', '张国艳', '范文新')
GROUP BY c.customer_name, c.customer_id
ORDER BY c.customer_name;

-- 项目里程碑统计
SELECT
    c.customer_name,
    COUNT(pm.milestone_id) as milestone_count,
    STRING_AGG(pm.milestone_name, '; ' ORDER BY pm.created_at) as milestones
FROM customers c
LEFT JOIN patent_applications pa ON c.customer_id = pa.customer_id
LEFT JOIN project_milestones pm ON pa.application_id = pm.application_id
WHERE c.customer_name IN ('孙俊霞', '李艳', '张国艳', '范文新')
GROUP BY c.customer_name, c.customer_id
ORDER BY c.customer_name;

-- 沟通记录统计
SELECT
    c.customer_name,
    COUNT(cr.record_id) as communication_count,
    STRING_AGG(cr.communication_type, ', ' ORDER BY cr.contact_date) as communication_types
FROM customers c
LEFT JOIN patent_applications pa ON c.customer_id = pa.customer_id
LEFT JOIN communication_records cr ON pa.application_id = cr.application_id
WHERE c.customer_name IN ('孙俊霞', '李艳', '张国艳', '范文新')
GROUP BY c.customer_name, c.customer_id
ORDER BY c.customer_name;

-- 文档管理统计
SELECT
    c.customer_name,
    COUNT(dm.document_id) as document_count,
    STRING_AGG(dm.document_type, ', ' ORDER BY dm.upload_date) as document_types
FROM customers c
LEFT JOIN patent_applications pa ON c.customer_id = pa.customer_id
LEFT JOIN document_management dm ON pa.application_id = dm.application_id
WHERE c.customer_name IN ('孙俊霞', '李艳', '张国艳', '范文新')
GROUP BY c.customer_name, c.customer_id
ORDER BY c.customer_name;

-- 显示蓝海专利统计
SELECT
    c.customer_name,
    COUNT(pa.application_id) as blue_ocean_patents,
    STRING_AGG(pa.patent_name, '; ' ORDER BY pa.created_at) as blue_ocean_patent_names
FROM customers c
LEFT JOIN patent_applications pa ON c.customer_id = pa.customer_id
WHERE c.customer_name IN ('孙俊霞', '李艳', '张国艳', '范文新')
  AND pa.blue_ocean_potential = true
GROUP BY c.customer_name, c.customer_id
ORDER BY c.customer_name;

-- 显示系统信息更新
UPDATE system_info
SET value = CURRENT_TIMESTAMP
WHERE key = 'last_sync_time';

INSERT INTO system_info (key, value) VALUES
    ('sync_summary', json_build_object(
        'sync_date', CURRENT_DATE,
        'customers_synced', 4,
        'patent_applications_synced', (SELECT COUNT(*) FROM patent_applications pa JOIN customers c ON pa.customer_id = c.customer_id WHERE c.customer_name IN ('孙俊霞', '李艳', '张国艳', '范文新')),
        'tasks_synced', (SELECT COUNT(*) FROM task_management tm JOIN customers c ON tm.customer_id = c.customer_id WHERE c.customer_name IN ('孙俊霞', '李艳', '张国艳', '范文新')),
        'total_confirmed_patents', 11,
        'blue_ocean_discoveries', 1,
        'sync_status', 'completed'
    )::text)
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;

-- 显示最终同步状态报告
SELECT '🎉 数据同步完成报告 🎉' as report_title;
SELECT json_build_object(
    '同步客户数量', (SELECT COUNT(*) FROM customers WHERE customer_name IN ('孙俊霞', '李艳', '张国艳', '范文新')),
    '专利申请总数', (SELECT COUNT(*) FROM patent_applications pa JOIN customers c ON pa.customer_id = c.customer_id WHERE c.customer_name IN ('孙俊霞', '李艳', '张国艳', '范文新')),
    '蓝海专利发现', (SELECT COUNT(*) FROM patent_applications pa JOIN customers c ON pa.customer_id = c.customer_id WHERE c.customer_name IN ('孙俊霞', '李艳', '张国艳', '范文新') AND pa.blue_ocean_potential = true),
    '任务创建数量', (SELECT COUNT(*) FROM task_management tm JOIN customers c ON tm.customer_id = c.customer_id WHERE c.customer_name IN ('孙俊霞', '李艳', '张国艳', '范文新')),
    '财务记录数量', (SELECT COUNT(*) FROM financial_records fr JOIN patent_applications pa ON fr.application_id = pa.application_id JOIN customers c ON pa.customer_id = c.customer_id WHERE c.customer_name IN ('孙俊霞', '李艳', '张国艳', '范文新')),
    '沟通记录数量', (SELECT COUNT(*) FROM communication_records cr JOIN patent_applications pa ON cr.application_id = pa.application_id JOIN customers c ON pa.customer_id = c.customer_id WHERE c.customer_name IN ('孙俊霞', '李艳', '张国艳', '范文新')),
    '项目里程碑数量', (SELECT COUNT(*) FROM project_milestones pm JOIN patent_applications pa ON pm.application_id = pa.application_id JOIN customers c ON pa.customer_id = c.customer_id WHERE c.customer_name IN ('孙俊霞', '李艳', '张国艳', '范文新')),
    '文档管理数量', (SELECT COUNT(*) FROM document_management dm JOIN patent_applications pa ON dm.application_id = pa.application_id JOIN customers c ON pa.customer_id = c.customer_id WHERE c.customer_name IN ('孙俊霞', '李艳', '张国艳', '范文新'))
) as sync_summary;

COMMIT;