# Athena平台数据库备份与恢复策略

## 1. 备份策略概述

### 1.1 备份目标
- **数据零丢失**: RPO (Recovery Point Objective) = 0
- **快速恢复**: RTO (Recovery Time Objective) < 1小时
- **多地域保护**: 本地+异地备份
- **长期保存**: 满足法规要求的保存期限

### 1.2 备份分类
```
备份类型:
├── 全量备份 (Full Backup)
│   ├── 频率: 每周一次
│   ├── 时间: 周日凌晨 2:00
│   └── 保留: 3个月
├── 增量备份 (Incremental Backup)
│   ├── 频率: 每天一次
│   ├── 时间: 每天凌晨 3:00
│   └── 保留: 1个月
├── WAL归档 (WAL Archive)
│   ├── 频率: 实时
│   ├── 保留: 1年
│   └── 压缩: 是
└── 快照备份 (Snapshot Backup)
    ├── 频率: 每小时
    ├── 保留: 7天
    └── 目标: 关键表
```

## 2. 本地备份实施方案

### 2.1 目录结构
```
/backup/postgresql/
├── full/                # 全量备份
│   ├── 2024/
│   │   ├── week_01/
│   │   ├── week_02/
│   │   └── ...
├── incremental/         # 增量备份
│   ├── 2024-12/
│   │   ├── day_01/
│   │   ├── day_02/
│   │   └── ...
├── wal/                 # WAL归档
│   ├── 2024/
│   │   ├── 12/
│   │   │   ├── 13/
│   │   │   ├── 14/
│   │   │   └── ...
├── snapshots/           # 快照备份
│   ├── hourly/
│   └── daily/
├── dev/scripts/             # 备份脚本
│   ├── backup_full.sh
│   ├── backup_incremental.sh
│   ├── backup_wal.sh
│   └── restore.sh
└── logs/                # 备份日志
    └── backup.log
```

### 2.2 备份脚本实现

#### 全量备份脚本
```bash
#!/bin/bash
# backup_full.sh - 全量备份脚本

# 配置
DB_NAME="athena_patent"
DB_USER="athena_admin"
BACKUP_DIR="/backup/postgresql/full"
DATE=$(date +%Y-%m-%d)
BACKUP_FILE="$BACKUP_DIR/$DATE/athena_patent_full.dump"

# 创建备份目录
mkdir -p "$(dirname "$BACKUP_FILE")"

# 执行备份
pg_dump -h localhost -U "$DB_USER" \
    -d "$DB_NAME" \
    -Fc \
    -Z 9 \
    -f "$BACKUP_FILE"

# 验证备份
if pg_restore --list "$BACKUP_FILE" > /dev/null; then
    echo "全量备份成功: $BACKUP_FILE"
else
    echo "全量备份失败!"
    exit 1
fi

# 压缩备份（如果使用自定义格式）
# pg_dump -Fc已经内置压缩

# 清理旧备份（保留3个月）
find "$BACKUP_DIR" -type d -mtime +90 -exec rm -rf {} \;
```

#### 增量备份脚本
```bash
#!/bin/bash
# backup_incremental.sh - 增量备份脚本

# 配置
DB_NAME="athena_patent"
DB_USER="athena_admin"
BACKUP_DIR="/backup/postgresql/incremental"
DATE=$(date +%Y-%m-%d)
BACKUP_FILE="$BACKUP_DIR/$DATE/athena_patent_incremental.dump"

# 创建备份目录
mkdir -p "$(dirname "$BACKUP_FILE")"

# 使用pg_basebackup进行物理备份（实际上更像是快照）
pg_basebackup -h localhost -D "$BACKUP_DIR/$DATE" \
    -U "$DB_USER" \
    -Ft \
    -z \
    -P \
    -v

# 或者使用逻辑备份作为增量
# 这里简化为逻辑备份
pg_dump -h localhost -U "$DB_USER" \
    -d "$DB_NAME" \
    -Fc \
    -Z 9 \
    --file="$BACKUP_FILE"

echo "增量备份完成: $BACKUP_DIR/$DATE"
```

### 2.3 WAL归档配置

#### PostgreSQL配置
```sql
-- postgresql.conf中的WAL归档配置
archive_mode = on
archive_command = 'test ! -f /backup/postgresql/wal_archive/%f && cp %p /backup/postgresql/wal_archive/%f'
archive_timeout = 300
wal_level = replica
```

#### WAL归档脚本
```bash
#!/bin/bash
# backup_wal.sh - WAL归档脚本

# 配置
WAL_SOURCE_DIR="/var/lib/postgresql/15/main/pg_wal"
WAL_ARCHIVE_DIR="/backup/postgresql/wal_archive"
RETENTION_DAYS=365

# 创建归档目录
mkdir -p "$WAL_ARCHIVE_DIR"

# 移动并压缩WAL文件
for wal_file in "$WAL_SOURCE_DIR"/*; do
    if [[ -f "$wal_file" ]] && [[ "$(basename "$wal_file")" =~ ^[0-9A-F]{24}$ ]]; then
        # 压缩WAL文件
        gzip -c "$wal_file" > "$WAL_ARCHIVE_DIR/$(basename "$wal_file").gz"
        # 删除原文件
        rm "$wal_file"
    fi
done

# 清理旧WAL文件
find "$WAL_ARCHIVE_DIR" -name "*.gz" -mtime +$RETENTION_DAYS -delete

echo "WAL归档完成"
```

### 2.4 自动化备份配置

#### Cron任务配置
```bash
# 编辑crontab: crontab -e

# 每周日凌晨2:00执行全量备份
0 2 * * 0 /usr/local/bin/backup_full.sh

# 每天凌晨3:00执行增量备份
0 3 * * 1-6 /usr/local/bin/backup_incremental.sh

# 每小时执行WAL归档检查
0 * * * * /usr/local/bin/backup_wal.sh

# 每天凌晨4:00清理旧备份
0 4 * * * /usr/local/bin/cleanup_old_backups.sh

# 每周日凌晨5:00验证备份
0 5 * * 0 /usr/local/bin/verify_backups.sh
```

## 3. 异地备份策略

### 3.1 异地备份方案

#### 云存储备份
```bash
#!/bin/bash
# backup_to_cloud.sh - 异地备份到云存储

# 配置
LOCAL_BACKUP_DIR="/backup/postgresql"
CLOUD_BUCKET="athena-backups-2024"
CLOUD_PROVIDER="aws"  # 可选: aws, gcp, azure

# AWS S3配置
if [ "$CLOUD_PROVIDER" = "aws" ]; then
    # 上传全量备份
    aws s3 sync "$LOCAL_BACKUP_DIR/full/" "s3://$CLOUD_BUCKET/full/" \
        --delete --storage-class GLACIER

    # 上传增量备份
    aws s3 sync "$LOCAL_BACKUP_DIR/incremental/" "s3://$CLOUD_BUCKET/incremental/" \
        --delete --storage-class STANDARD_IA

    # 上传WAL归档
    aws s3 sync "$LOCAL_BACKUP_DIR/wal_archive/" "s3://$CLOUD_BUCKET/wal/" \
        --delete --storage-class STANDARD
fi

# 记录传输日志
echo "$(date): 异地备份完成" >> /var/log/cloud_backup.log
```

#### 同步到异地服务器
```bash
#!/bin/bash
# sync_to_remote.sh - 同步到异地服务器

# 配置
LOCAL_BACKUP_DIR="/backup/postgresql"
REMOTE_SERVER="backup.athena-platform.com"
REMOTE_USER="backup"
REMOTE_DIR="/backup/athena/postgresql"

# 使用rsync同步（增量同步）
rsync -avz --delete \
    -e "ssh -i /home/backup/.ssh/backup_key" \
    "$LOCAL_BACKUP_DIR/" \
    "$REMOTE_USER@$REMOTE_SERVER:$REMOTE_DIR"

# 传输完成验证
if [ $? -eq 0 ]; then
    echo "$(date): 异地同步成功" >> /var/log/remote_sync.log
else
    echo "$(date): 异地同步失败" >> /var/log/remote_sync.log
    # 发送告警
    echo "异地备份同步失败" | mail -s "备份告警" admin@athena-platform.com
fi
```

## 4. 恢复策略

### 4.1 恢复场景

#### 场景1: 数据损坏恢复
```bash
#!/bin/bash
# restore_from_backup.sh - 从备份恢复数据

# 配置
DB_NAME="athena_patent"
DB_USER="athena_admin"
BACKUP_FILE="$1"  # 备份文件路径

# 停止应用服务
systemctl stop athena-platform

# 删除损坏的数据库
sudo -u postgres dropdb "$DB_NAME" --if-exists

# 创建新数据库
sudo -u postgres createdb "$DB_NAME" -O "$DB_NAME"

# 恢复数据
pg_restore -h localhost -U "$DB_USER" \
    -d "$DB_NAME" \
    -v \
    --clean --if-exists \
    --exit-on-error \
    "$BACKUP_FILE"

# 验证恢复结果
if [ $? -eq 0 ]; then
    echo "数据恢复成功"

    # 更新统计信息
    psql -h localhost -U "$DB_USER" -d "$DB_NAME" -c "ANALYZE;"

    # 重启应用服务
    systemctl start athena-platform
else
    echo "数据恢复失败!"
    exit 1
fi
```

#### 场景2: 时间点恢复（PITR）
```bash
#!/bin/bash
# point_in_time_recovery.sh - 时间点恢复

# 配置
TARGET_TIME="$1"  # 目标时间，格式: "2024-12-13 15:30:00"
RECOVERY_DIR="/tmp/recovery"
DB_NAME="athena_patent"

# 创建恢复目录
mkdir -p "$RECOVERY_DIR"

# 准备基础备份
BASE_BACKUP="/backup/postgresql/full/2024-12-01/athena_patent_full.dump"
pg_restore -h localhost -U postgres -C "$DB_NAME" "$BASE_BACKUP"

# 恢复WAL到指定时间
export PGDATA="/var/lib/postgresql/15/main"
sudo -u postgres pg_ctl start -D "$PGDATA"

# 创建恢复命令
cat > "$RECOVERY_DIR/recovery.conf" << EOF
restore_command = 'cp /backup/postgresql/wal_archive/%f %p'
recovery_target_time = '$TARGET_TIME'
recovery_target_action = 'promote'
EOF

# 执行恢复
sudo -u postgres cp "$RECOVERY_DIR/recovery.conf" "$PGDATA/"
sudo -u postgres pg_ctl restart -D "$PGDATA"

echo "时间点恢复完成: $TARGET_TIME"
```

### 4.2 灾难恢复计划

#### RTO/RPO矩阵
| 灾难类型 | RPO | RTO | 恢复方案 |
|----------|-----|-----|----------|
| 单表损坏 | 0 | 5分钟 | 表级恢复 |
| 数据库损坏 | 1小时 | 30分钟 | 全量恢复 |
| 服务器故障 | 4小时 | 1小时 | 服务器切换 |
| 机房故障 | 24小时 | 4小时 | 异地恢复 |
| 地域灾难 | 24小时 | 8小时 | 云恢复 |

#### 恢复演练脚本
```bash
#!/bin/bash
# disaster_recovery_drill.sh - 灾难恢复演练

# 配置
DRILL_DATE=$(date +%Y%m%d_%H%M%S)
DRILL_REPORT_DIR="/tmp/disaster_drill/$DRILL_DATE"
DB_NAME="athena_patent_drill"

# 创建演练目录
mkdir -p "$DRILL_REPORT_DIR"

echo "开始灾难恢复演练: $DRILL_DATE" | tee "$DRILL_REPORT_DIR/drill.log"

# 1. 备份当前状态
echo "1. 备份当前数据库状态..." >> "$DRILL_REPORT_DIR/drill.log"
sudo -u postgres pg_dumpall > "$DRILL_REPORT_DIR/before_drill.sql"

# 2. 模拟灾难（停止数据库）
echo "2. 模拟灾难..." >> "$DRILL_REPORT_DIR/drill.log"
systemctl stop postgresql

# 3. 恢复数据库
echo "3. 开始恢复..." >> "$DRILL_REPORT_DIR/drill.log"
RECOVERY_START=$(date +%s)

# 使用最近的全量备份恢复
LATEST_BACKUP=$(ls -t /backup/postgresql/full/*/athena_patent_full.dump | head -1)
sudo -u postgres dropdb "$DB_NAME" --if-exists
sudo -u postgres createdb "$DB_NAME"

pg_restore -h localhost -U postgres -d "$DB_NAME" -v "$LATEST_BACKUP" >> "$DRILL_REPORT_DIR/restore.log" 2>&1

# 恢复增量备份
for inc_backup in $(ls -t /backup/postgresql/incremental/*/athena_patent_incremental.dump | head -3); do
    echo "恢复增量备份: $inc_backup" >> "$DRILL_REPORT_DIR/drill.log"
    pg_restore -h localhost -U postgres -d "$DB_NAME" -v "$inc_backup" >> "$DRILL_REPORT_DIR/restore.log" 2>&1
done

# 4. 验证数据完整性
echo "4. 验证数据完整性..." >> "$DRILL_REPORT_DIR/drill.log"
patent_count=$(psql -h localhost -U postgres -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM patents;" | tr -d ' ')

# 5. 记录恢复时间
RECOVERY_END=$(date +%s)
RTO=$((RECOVERY_END - RECOVERY_START))

# 6. 生成演练报告
cat > "$DRILL_REPORT_DIR/drill_report.txt" << EOF
灾难恢复演练报告
===================
演练时间: $DRILL_DATE
恢复耗时: $RTO 秒
数据完整性: $patent_count 条专利记录
备份文件: $LATEST_BACKUP
恢复日志: $DRILL_REPORT_DIR/restore.log

恢复成功率: $([ $RTO -lt 3600 ] && echo "通过" || echo "失败")
EOF

echo "演练完成，报告保存在: $DRILL_REPORT_DIR" >> "$DRILL_REPORT_DIR/drill.log"
```

## 5. 监控和告警

### 5.1 备份监控脚本
```bash
#!/bin/bash
# monitor_backups.sh - 备份监控脚本

# 配置
ALERT_EMAIL="admin@athena-platform.com"
BACKUP_DIR="/backup/postgresql"
LOG_FILE="/var/log/backup_monitor.log"

# 检查最近的备份
LATEST_FULL=$(ls -lt "$BACKUP_DIR/full"/*/athena_patent_full.dump 2>/dev/null | head -1)
LATEST_INCREMENTAL=$(ls -lt "$BACKUP_DIR/incremental"/*/athena_patent_incremental.dump 2>/dev/null | head -1)

# 获取备份时间
FULL_DATE=$(echo "$LATEST_FULL" | awk '{print $6, $7, $8}')
INC_DATE=$(echo "$LATEST_INCREMENTAL" | awk '{print $6, $7, $8}')

# 检查备份时效性
FULL_AGE=$(find "$BACKUP_DIR/full" -name "*.dump" -mtime +7 | wc -l)
INC_AGE=$(find "$BACKUP_DIR/incremental" -name "*.dump" -mtime +2 | wc -l)

# 检查备份大小
FULL_SIZE=$(du -sh "$BACKUP_DIR/full" 2>/dev/null | tail -1 | cut -f1)
INC_SIZE=$(du -sh "$BACKUP_DIR/incremental" 2>/dev/null | tail -1 | cut -f1)

# 生成监控报告
cat > "/tmp/backup_status_$(date +%Y%m%d).txt" << EOF
备份状态报告
=============
检查时间: $(date)
最新全量备份: $FULL_DATE
最新增量备份: $INC_DATE
全量备份大小: $FULL_SIZE
增量备份大小: $INC_SIZE
过期全量备份数: $FULL_AGE
过期增量备份数: $INC_AGE
EOF

# 告警条件
if [ "$FULL_AGE" -gt 0 ] || [ "$INC_AGE" -gt 0 ]; then
    echo "备份告警: 发现过期备份文件" | mail -s "备份监控告警" "$ALERT_EMAIL"
fi

# 记录日志
echo "$(date): 备份监控完成" >> "$LOG_FILE"
```

### 5.2 恢复能力测试
```bash
#!/bin/bash
# test_recovery_capability.sh - 恢复能力测试

# 配置
TEST_DB="athena_patent_test"
BACKUP_FILE="/backup/postgresql/full/$(date +%Y-%m-%d)/athena_patent_full.dump"
TEST_REPORT="/var/log/recovery_test.log"

echo "开始恢复能力测试: $(date)" >> "$TEST_REPORT"

# 1. 创建测试数据库
sudo -u postgres dropdb "$TEST_DB" --if-exists
sudo -u postgres createdb "$TEST_DB"

# 2. 恢复备份
TEST_START=$(date +%s)
pg_restore -h localhost -U postgres -d "$TEST_DB" -v "$BACKUP_FILE" > /tmp/test_restore.log 2>&1
TEST_END=$(date +%s)

# 3. 验证恢复
if [ $? -eq 0 ]; then
    # 检查数据完整性
    TABLE_COUNT=$(psql -h localhost -U postgres -d "$TEST_DB" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | tr -d ' ')
    RECORD_COUNT=$(psql -h localhost -U postgres -d "$TEST_DB" -t -c "SELECT COUNT(*) FROM patents;" | tr -d ' ')

    DURATION=$((TEST_END - TEST_START))

    echo "恢复测试通过" >> "$TEST_REPORT"
    echo "恢复耗时: $DURATION 秒" >> "$TEST_REPORT"
    echo "表数量: $TABLE_COUNT" >> "$TEST_REPORT"
    echo "专利记录数: $RECORD_COUNT" >> "$TEST_REPORT"
else
    echo "恢复测试失败!" >> "$TEST_REPORT"
    echo "错误详情: $(cat /tmp/test_restore.log)" >> "$TEST_REPORT"
fi

# 4. 清理测试数据库
sudo -u postgres dropdb "$TEST_DB"

echo "恢复能力测试完成: $(date)" >> "$TEST_REPORT"
```

## 6. 最佳实践建议

### 6.1 备份优化
1. **压缩策略**
   - 使用PostgreSQL的压缩格式(-Fc)
   - 压缩级别平衡性能和存储
   - 定期清理过期备份

2. **并行备份**
   - 使用多个并行连接
   - 调整maintenance_work_mem
   - 利用多核CPU加速

3. **网络优化**
   - 使用增量传输
   - 断点续传支持
   - 带宽限制避免拥塞

### 6.2 恢复优化
1. **快速恢复**
   - 预先准备恢复环境
   - 使用部分恢复
   - 并行恢复处理

2. **数据验证**
   - 自动化验证脚本
   - 关键数据检查
   - 业务逻辑验证

3. **回滚机制**
   - 恢复前备份
   - 快速回滚方案
   - 最小化影响

## 7. 应急响应流程

### 7.1 数据丢失响应
```
发现数据丢失 → 评估影响 → 选择恢复点 → 执行恢复 → 验证数据 → 恢复服务
     ↓            ↓           ↓           ↓          ↓         ↓
   1分钟        5分钟       10分钟      30分钟     35分钟   40分钟
```

### 7.2 联系人清单
- **数据库管理员**: DBA团队
- **系统管理员**: 运维团队
- **应用负责人**: 开发团队
- **业务负责人**: 产品团队
- **管理层**: CTO/CIO

### 7.3 通信模板
```
邮件主题: [紧急] 数据库故障通知

致相关同事：

事件描述: [简要描述]
影响范围: [受影响的功能]
预计恢复时间: [RTO]
当前进展: [处理状态]
联系人: [负责人联系方式]

请做好相应的业务调整准备。

谢谢！
```

## 8. 文档维护

### 8.1 文档更新
- 每月审查备份策略
- 每季度更新恢复流程
- 每年进行灾难恢复演练
- 及时更新联系人信息

### 8.2 知识转移
- 备份操作手册
- 恢复操作指南
- 故障排查文档
- 最佳实践总结

---

**实施建议**:
1. 立即部署自动化备份系统
2. 配置监控和告警机制
3. 定期进行恢复测试
4. 建立异地备份机制
5. 制定详细的应急响应计划