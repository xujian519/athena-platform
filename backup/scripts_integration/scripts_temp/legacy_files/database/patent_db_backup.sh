#!/bin/bash
# 专利数据库备份脚本
# Patent Database Backup Script

set -e

# 配置
DB_NAME="patent_db"
DB_USER="postgres"
DB_HOST="localhost"
DB_PORT="5432"
BACKUP_DIR="/Users/xujian/Athena工作平台/backups/database"
RETENTION_DAYS=30
COMPRESS=true
PARALLEL_JOBS=4

# 创建备份目录
mkdir -p "$BACKUP_DIR"
mkdir -p "$BACKUP_DIR/daily"
mkdir -p "$BACKUP_DIR/weekly"
mkdir -p "$BACKUP_DIR/monthly"

# 日志文件
LOG_FILE="$BACKUP_DIR/backup.log"
echo "========================================" >> "$LOG_FILE"
echo "Backup started at: $(date)" >> "$LOG_FILE"

# 函数：执行备份
perform_backup() {
    local backup_type=$1
    local backup_dir=$2
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_file="$backup_dir/patent_db_${backup_type}_${timestamp}.sql"

    echo "Starting $backup_type backup..." | tee -a "$LOG_FILE"

    if [ "$COMPRESS" = true ]; then
        # 使用pg_dump并行备份并压缩
        pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" \
            -d "$DB_NAME" \
            --format=custom \
            --parallel="$PARALLEL_JOBS" \
            --compress=9 \
            --file="$backup_file.dump"

        echo "$backup_type backup completed: $(du -h "$backup_file.dump" | cut -f1)" | tee -a "$LOG_FILE"
    else
        # 标准SQL备份
        pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" \
            -d "$DB_NAME" \
            --format=plain \
            --file="$backup_file"

        echo "$backup_type backup completed: $(du -h "$backup_file" | cut -f1)" | tee -a "$LOG_FILE"
    fi

    # 验证备份文件
    if [ -f "$backup_file.dump" ]; then
        echo "Backup file verified successfully" >> "$LOG_FILE"
    else
        echo "ERROR: Backup file not found!" >> "$LOG_FILE"
        exit 1
    fi
}

# 函数：清理旧备份
cleanup_old_backups() {
    echo "Cleaning up old backups..." | tee -a "$LOG_FILE"

    # 删除超过保留期的每日备份
    find "$BACKUP_DIR/daily" -name "*.dump" -mtime +$RETENTION_DAYS -delete

    # 删除超过4周的每周备份
    find "$BACKUP_DIR/weekly" -name "*.dump" -mtime +28 -delete

    # 删除超过12个月的每月备份
    find "$BACKUP_DIR/monthly" -name "*.dump" -mtime +365 -delete

    echo "Cleanup completed" | tee -a "$LOG_FILE"
}

# 函数：数据库统计信息备份
backup_database_stats() {
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local stats_file="$BACKUP_DIR/patent_db_stats_${timestamp}.json"

    echo "Backing up database statistics..." | tee -a "$LOG_FILE"

    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" << EOF > "$stats_file"
-- 数据库统计信息
SELECT
    'database_size' as metric,
    pg_size_pretty(pg_database_size('$DB_NAME')) as value
UNION ALL
SELECT
    'table_size' as metric,
    pg_size_pretty(pg_total_relation_size('patents')) as value
UNION ALL
SELECT
    'index_size' as metric,
    pg_size_pretty(pg_total_relation_size('patents') - pg_relation_size('patents')) as value
UNION ALL
SELECT
    'total_records' as metric,
    COUNT(*)::text as value
FROM patents
UNION ALL
SELECT
    'unique_applicants' as metric,
    COUNT(DISTINCT applicant)::text as value
FROM patents
WHERE applicant IS NOT NULL;
EOF

    echo "Database statistics backed up to: $stats_file" | tee -a "$LOG_FILE"
}

# 函数：检查数据库健康状态
check_database_health() {
    echo "Checking database health..." | tee -a "$LOG_FILE"

    # 检查连接
    if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -q; then
        echo "ERROR: Database is not ready!" >> "$LOG_FILE"
        exit 1
    fi

    # 检查表大小
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
        SELECT
            'Table Size Check: ' || pg_size_pretty(pg_total_relation_size('patents')) as result;
    " >> "$LOG_FILE"

    # 检查死元组比例
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
        SELECT
            'Dead Tuple Ratio: ' ||
            ROUND((n_dead_tup::float / (n_live_tup + n_dead_tup) * 100), 2) || '%' as result
        FROM pg_stat_user_tables
        WHERE tablename = 'patents';
    " >> "$LOG_FILE"

    echo "Database health check completed" | tee -a "$LOG_FILE"
}

# 主备份逻辑
case "${1:-daily}" in
    "daily")
        echo "Performing daily backup..." | tee -a "$LOG_FILE"
        check_database_health
        perform_backup "daily" "$BACKUP_DIR/daily"
        backup_database_stats
        ;;
    "weekly")
        echo "Performing weekly backup..." | tee -a "$LOG_FILE"
        check_database_health
        perform_backup "weekly" "$BACKUP_DIR/weekly"
        backup_database_stats
        ;;
    "monthly")
        echo "Performing monthly backup..." | tee -a "$LOG_FILE"
        check_database_health
        perform_backup "monthly" "$BACKUP_DIR/monthly"
        backup_database_stats
        ;;
    "full")
        echo "Performing full backup..." | tee -a "$LOG_FILE"
        check_database_health
        perform_backup "daily" "$BACKUP_DIR/daily"
        backup_database_stats
        ;;
    "cleanup")
        cleanup_old_backups
        ;;
    "restore")
        if [ -z "$2" ]; then
            echo "Usage: $0 restore <backup_file>" | tee -a "$LOG_FILE"
            exit 1
        fi
        echo "Restoring from backup: $2" | tee -a "$LOG_FILE"

        # 创建恢复脚本
        cat > /tmp/restore_patents.sql << 'EOF'
-- 停止所有连接
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'patent_db';

-- 删除现有表
DROP TABLE IF EXISTS patents CASCADE;

EOF

        psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "postgres" -f /tmp/restore_patents.sql

        # 恢复数据
        pg_restore -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
            --verbose --clean --if-exists --jobs="$PARALLEL_JOBS" "$2"

        echo "Restore completed" | tee -a "$LOG_FILE"
        ;;
    *)
        echo "Usage: $0 {daily|weekly|monthly|full|cleanup|restore <backup_file>}" | tee -a "$LOG_FILE"
        echo "  daily   - Daily incremental backup" | tee -a "$LOG_FILE"
        echo "  weekly  - Weekly full backup" | tee -a "$LOG_FILE"
        echo "  monthly - Monthly full backup" | tee -a "$LOG_FILE"
        echo "  full    - Full backup with stats" | tee -a "$LOG_FILE"
        echo "  cleanup - Remove old backups" | tee -a "$LOG_FILE"
        echo "  restore - Restore from backup file" | tee -a "$LOG_FILE"
        exit 1
        ;;
esac

# 清理旧备份
if [ "${1:-daily}" != "restore" ]; then
    cleanup_old_backups
fi

echo "Backup completed at: $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# 发送通知（如果需要）
if command -v terminal-notifier &> /dev/null; then
    terminal-notifier -title "Patent DB Backup" -message "Backup completed successfully" -sound default
fi