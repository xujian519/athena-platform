#!/bin/bash
# PostgreSQL自动清理脚本
# PostgreSQL Auto Cleanup Script

echo "🧹 PostgreSQL数据库自动清理"
echo "================================"
echo "时间: $(date)"
echo ""

# 设置环境变量
export PGPASSWORD=""

# 1. 创建备份目录
BACKUP_DIR="/tmp/postgres_backups/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR
echo "✅ 备份目录: $BACKUP_DIR"

# 2. 连接PostgreSQL并执行清理
echo ""
echo "开始执行清理操作..."

# 备份patents_2010表（如果存在）
echo "1. 检查并备份patents_2010表..."
psql -h localhost -U postgres -d patent_db -c "\COPY (SELECT '备份开始时间: $(date)', COUNT(*) FROM patents_2010) TO STDOUT;" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "   发现patents_2010表，开始备份..."
    psql -h localhost -U postgres -d patent_db -c "\COPY patents_2010 TO '$BACKUP_DIR/patents_2010_backup.csv' WITH CSV HEADER;" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "   ✅ 备份完成"

        # 获取备份文件大小
        BACKUP_SIZE=$(du -sh $BACKUP_DIR/patents_2010_backup.csv | cut -f1)
        echo "   备份大小: $BACKUP_SIZE"
    else
        echo "   ❌ 备份失败"
    fi
fi

# 3. 执行VACUUM清理
echo ""
echo "2. 执行VACUUM清理主表..."
psql -h localhost -U postgres -d patent_db -c "VACUUM (VERBOSE, ANALYZE) patents;" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "   ✅ VACUUM完成"
else
    echo "   ⚠️  VACUUM执行失败，继续其他操作"
fi

# 4. 更新表统计信息
echo ""
echo "3. 更新表统计信息..."
psql -h localhost -U postgres -d patent_db -c "ANALYZE;" 2>/dev/null
echo "   ✅ 统计信息已更新"

# 5. 查看清理结果
echo ""
echo "=== 清理后状态 ==="
psql -h localhost -U postgres -d patent_db -c "
SELECT
    'patents' as table_name,
    pg_size_pretty(pg_total_relation_size('public.patents')) as total_size,
    pg_size_pretty(pg_relation_size('public.patents')) as data_size,
    pg_size_pretty(pg_indexes_size('public.patents')) as index_size
UNION ALL
SELECT
    'patents_2010' as table_name,
    pg_size_pretty(pg_total_relation_size('public.patents_2010')) as total_size,
    pg_size_pretty(pg_relation_size('public.patents_2010')) as data_size,
    pg_size_pretty(pg_indexes_size('public.patents_2010')) as index_size
;" 2>/dev/null

# 6. 查看数据库总大小
echo ""
echo "=== 数据库总大小 ==="
psql -h localhost -U postgres -d postgres -c "
SELECT
    datname,
    pg_size_pretty(pg_database_size(datname)) as size
FROM pg_database
WHERE datistemplate = false
ORDER BY pg_database_size(datname) DESC
LIMIT 5
;" 2>/dev/null

# 7. 可选：删除patents_2010表（取消注释以执行）
# echo ""
# echo "4. 删除patents_2010表（已备份）..."
# read -p "确认删除patents_2010表？(y/N): " -n response
# if [[ $response =~ ^[Yy]$ ]]; then
#     psql -h localhost -U postgres -d patent_db -c "DROP TABLE IF EXISTS patents_2010;" 2>/dev/null
#     if [ $? -eq 0 ]; then
#         echo "   ✅ patents_2010表已删除"
#     else
#         echo "   ❌ 删除失败"
#     fi
# fi

# 8. 清理旧的备份文件（保留最近3天）
echo ""
echo "5. 清理旧的备份文件（保留最近3天）..."
find /tmp/postgres_backups -type d -mtime +3 -exec rm -rf {} \; 2>/dev/null
echo "   ✅ 旧备份文件已清理"

echo ""
echo "✅ 自动清理完成！"
echo "备份文件位置: $BACKUP_DIR"