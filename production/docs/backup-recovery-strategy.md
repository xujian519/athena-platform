# Athena工作平台数据备份和恢复策略

## 🎯 备份策略概述

### 备份原则
- **3-2-1规则**: 3个副本，2个不同介质，1个异地备份
- **定期备份**: 每日增量，每周全量，每月归档
- **自动化**: 90%以上备份操作自动化
- **可验证性**: 所有备份必须可验证和测试

### 数据分类和优先级
#### P0 - 关键业务数据 (每日备份)
- PostgreSQL数据库
- Redis缓存数据
- 用户认证信息
- 系统配置文件

#### P1 - 重要数据 (每周备份)
- Qdrant向量数据
- AI模型文件
- 日志文件
- 监控数据

#### P2 - 一般数据 (每月备份)
- 静态资源文件
- 文档和代码
- 临时文件
- 系统快照

## 💾 自动备份系统

### 1. 数据库备份

#### PostgreSQL备份
```bash
#!/bin/bash
# backup-postgres.sh
# PostgreSQL数据库备份脚本

BACKUP_DIR="/backups/postgres"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="athena_prod_${DATE}.sql"

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 执行数据库备份
kubectl exec -n athena-production postgres-pod -- pg_dump \
  -U athena_user \
  -d athena_prod \
  --no-password \
  --verbose \
  --format=custom \
  --compress=9 \
  --file="/tmp/${BACKUP_FILE}"

# 复制备份文件
kubectl cp "athena-production/postgres-pod:/tmp/${BACKUP_FILE}" "${BACKUP_DIR}/"

# 压缩备份
cd "$BACKUP_DIR"
gzip "${BACKUP_FILE}"

# 验证备份完整性
pg_restore --list --verbose "${BACKUP_FILE}.gz" > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ PostgreSQL备份成功: ${BACKUP_FILE}.gz"
else
    echo "❌ PostgreSQL备份验证失败"
    exit 1
fi

# 清理旧备份 (保留7天)
find "$BACKUP_DIR" -name "*.gz" -mtime +7 -delete

# 上传到远程存储
./scripts/upload-backup.sh "${BACKUP_DIR}/${BACKUP_FILE}.gz" "postgres"
```

#### 增量备份
```bash
#!/bin/bash
# backup-postgres-incremental.sh
# PostgreSQL增量备份脚本

WAL_ARCHIVE_DIR="/backups/postgres/wal_archive"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建WAL归档目录
mkdir -p "$WAL_ARCHIVE_DIR"

# 启用WAL归档
kubectl exec -n athena-production postgres-pod -- psql -U athena_user -d athena_prod -c "
ALTER SYSTEM SET archive_mode = 'on';
ALTER SYSTEM SET archive_command = 'cp %p /var/lib/postgresql/wal_archive/%f';
SELECT pg_reload_conf();
"

# 压缩和归档WAL文件
kubectl exec -n athena-production postgres-pod -- find /var/lib/postgresql/wal_archive -name "*.wal" -mtime +0 -exec gzip {} \;

# 复制WAL文件到备份存储
kubectl cp "athena-production/postgres-pod:/var/lib/postgresql/wal_archive/" "${WAL_ARCHIVE_DIR}/"

echo "✅ WAL归档备份完成: ${WAL_ARCHIVE_DIR}"
```

### 2. Redis备份

#### Redis快照备份
```bash
#!/bin/bash
# backup-redis.sh
# Redis数据备份脚本

BACKUP_DIR="/backups/redis"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="redis_backup_${DATE}.rdb"

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 触发Redis保存
kubectl exec -n athena-production redis-pod -- redis-cli BGSAVE

# 等待保存完成
while ! kubectl exec -n athena-production redis-pod -- redis-cli LASTSAVE | grep -q "1"; do
    echo "等待Redis后台保存完成..."
    sleep 5
done

# 复制快照文件
kubectl cp "athena-production/redis-pod:/data/dump.rdb" "${BACKUP_DIR}/${BACKUP_FILE}"

# 压缩备份
gzip "${BACKUP_DIR}/${BACKUP_FILE}"

# 验证备份完整性
if redis-cli --rdb "${BACKUP_DIR}/${BACKUP_FILE}.gz" &> /dev/null; then
    echo "✅ Redis备份成功: ${BACKUP_FILE}.gz"
else
    echo "❌ Redis备份验证失败"
    exit 1
fi

# 清理旧备份 (保留3天)
find "$BACKUP_DIR" -name "*.gz" -mtime +3 -delete

# 上传到远程存储
./scripts/upload-backup.sh "${BACKUP_DIR}/${BACKUP_FILE}.gz" "redis"
```

### 3. Qdrant向量数据库备份

#### Qdrant数据备份
```bash
#!/bin/bash
# backup-qdrant.sh
# Qdrant向量数据库备份脚本

BACKUP_DIR="/backups/qdrant"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="qdrant_backup_${DATE}.tar.gz"

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 停止Qdrant服务（确保数据一致性）
kubectl scale deployment qdrant-deployment --replicas=0 -n athena-production
kubectl wait --for=condition=replicas=0 deployment/qdrant-deployment -n athena-production --timeout=300s

# 复制数据目录
kubectl cp "athena-production/qdrant-pod:/qdrant/storage/" "${BACKUP_DIR}/qdrant_storage_${DATE}/"

# 压缩数据
cd "$BACKUP_DIR"
tar -czf "${BACKUP_FILE}" "qdrant_storage_${DATE}/"

# 验证备份完整性
if tar -tzf "${BACKUP_FILE}" | head -10 | grep -q "collections"; then
    echo "✅ Qdrant备份成功: ${BACKUP_FILE}"
else
    echo "❌ Qdrant备份验证失败"
    exit 1
fi

# 重启Qdrant服务
kubectl scale deployment qdrant-deployment --replicas=1 -n athena-production
kubectl wait --for=condition=available deployment/qdrant-deployment -n athena-production --timeout=300s

# 清理临时目录
rm -rf "qdrant_storage_${DATE}/"

# 上传到远程存储
./scripts/upload-backup.sh "${BACKUP_DIR}/${BACKUP_FILE}" "qdrant"
```

### 4. 配置文件备份

#### Kubernetes配置备份
```bash
#!/bin/bash
# backup-config.sh
# Kubernetes配置备份脚本

BACKUP_DIR="/backups/config"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 备份命名空间
kubectl get namespaces -o yaml > "${BACKUP_DIR}/namespaces_${DATE}.yaml"

# 备份部署配置
kubectl get deployments -n athena-production -o yaml > "${BACKUP_DIR}/deployments_${DATE}.yaml"

# 备份服务配置
kubectl get services -n athena-production -o yaml > "${BACKUP_DIR}/services_${DATE}.yaml"

# 备份配置映射
kubectl get configmaps -n athena-production -o yaml > "${BACKUP_DIR}/configmaps_${DATE}.yaml"

# 备份密钥（加密）
kubectl get secrets -n athena-production -o yaml | gpg --encrypt --recipient "backup@athena-patent.com" > "${BACKUP_DIR}/secrets_${DATE}.yaml.gpg"

# 压缩所有配置
cd "$BACKUP_DIR"
tar -czf "config_backup_${DATE}.tar.gz" "*_${DATE}.yaml*"

echo "✅ 配置备份完成: config_backup_${DATE}.tar.gz"
```

## 🗄️ 远程备份存储

### 1. AWS S3存储配置

#### S3备份脚本
```bash
#!/bin/bash
# upload-to-s3.sh
# S3上传备份脚本

S3_BUCKET="athena-backups"
LOCAL_FILE="$1"
BACKUP_TYPE="$2"
DATE=$(date +%Y%m%d)

# S3路径
S3_PATH="s3://${S3_BUCKET}/${BACKUP_TYPE}/${DATE}/"

# 上传文件
aws s3 cp "$LOCAL_FILE" "$S3_PATH" --storage-class GLACIER_IR

# 设置生命周期策略
aws s3api put-object \
  --bucket "$S3_BUCKET" \
  --key "${BACKUP_TYPE}/${DATE}/$(basename $LOCAL_FILE)" \
  --storage-class GLACIER_IR \
  --metadata "backup-type=${BACKUP_TYPE},backup-date=${DATE}"

# 验证上传
if aws s3 ls "$S3_PATH" | grep -q "$(basename $LOCAL_FILE)"; then
    echo "✅ S3上传成功: $LOCAL_FILE -> $S3_PATH"
else
    echo "❌ S3上传失败"
    exit 1
fi
```

#### S3生命周期策略
```json
{
  "Rules": [
    {
      "ID": "PostgreSQLBackupLifecycle",
      "Status": "Enabled",
      "Filter": {
        "Prefix": "postgres/"
      },
      "Transitions": [
        {
          "Days": 30,
          "StorageClass": "STANDARD_IA"
        },
        {
          "Days": 90,
          "StorageClass": "GLACIER"
        },
        {
          "Days": 365,
          "StorageClass": "DEEP_ARCHIVE"
        }
      ],
      "Expiration": {
        "Days": 2555
      }
    },
    {
      "ID": "RedisBackupLifecycle",
      "Status": "Enabled",
      "Filter": {
        "Prefix": "redis/"
      },
      "Transitions": [
        {
          "Days": 7,
          "StorageClass": "STANDARD_IA"
        },
        {
          "Days": 30,
          "StorageClass": "GLACIER"
        },
        {
          "Days": 180,
          "StorageClass": "DEEP_ARCHIVE"
        }
      ],
      "Expiration": {
        "Days": 365
      }
    }
  ]
}
```

### 2. 本地备份存储

#### 本地存储策略
```bash
#!/bin/bash
# local-backup-rotation.sh
# 本地备份轮换脚本

LOCAL_BACKUP_DIR="/backups"
RETENTION_DAYS=30
MIN_FREE_SPACE_GB=100

# 检查磁盘空间
AVAILABLE_SPACE=$(df "$LOCAL_BACKUP_DIR" | awk 'NR==2{print $4}')
AVAILABLE_SPACE_GB=$((AVAILABLE_SPACE / 1024 / 1024))

if [ $AVAILABLE_SPACE_GB -lt $MIN_FREE_SPACE_GB ]; then
    echo "⚠️ 磁盘空间不足，强制清理旧备份"
    RETENTION_DAYS=7
fi

# 清理旧备份
find "$LOCAL_BACKUP_DIR" -type f -mtime +$RETENTION_DAYS -delete

# 记录清理操作
echo "$(date): 清理 $RETENTION_DAYS 天前的旧备份文件" >> "${LOCAL_BACKUP_DIR}/cleanup.log"
```

## 🔄 数据恢复流程

### 1. 数据库恢复

#### PostgreSQL恢复
```bash
#!/bin/bash
# restore-postgres.sh
# PostgreSQL数据库恢复脚本

BACKUP_FILE="$1"
RESTORE_TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 创建恢复前备份
echo "创建恢复前备份..."
./backup-postgres.sh

# 停止应用服务
kubectl scale deployment athena-api-deployment --replicas=0 -n athena-production

# 恢复数据库
echo "恢复PostgreSQL数据库..."

# 复制备份文件到Pod
kubectl cp "$BACKUP_FILE" "athena-production/postgres-pod:/tmp/restore_$(basename $BACKUP_FILE)"

# 执行恢复
kubectl exec -n athena-production postgres-pod -- bash -c "
    # 停止PostgreSQL服务
    pg_ctl stop -D /var/lib/postgresql/data
    
    # 删除现有数据
    rm -rf /var/lib/postgresql/data/*
    
    # 恢复数据库
    pg_restore -U athena_user -d athena_prod \
        --clean --if-exists --verbose \
        /tmp/restore_$(basename $BACKUP_FILE)
    
    # 重启PostgreSQL服务
    pg_ctl start -D /var/lib/postgresql/data
"

# 等待数据库就绪
sleep 30

# 验证恢复结果
kubectl exec -n athena-production postgres-pod -- psql -U athena_user -d athena_prod -c "SELECT COUNT(*) FROM information_schema.tables;" > /tmp/table_count.txt
TABLE_COUNT=$(kubectl cp "athena-production/postgres-pod:/tmp/table_count.txt" - | cat)

if [ "$TABLE_COUNT" -gt 0 ]; then
    echo "✅ PostgreSQL恢复成功，表数量: $TABLE_COUNT"
else
    echo "❌ PostgreSQL恢复验证失败"
    exit 1
fi

# 重启应用服务
kubectl scale deployment athena-api-deployment --replicas=3 -n athena-production
kubectl rollout status deployment/athena-api-deployment -n athena-production --timeout=600s

echo "✅ 数据库恢复完成: $(basename $BACKUP_FILE)"
```

### 2. Redis恢复

#### Redis数据恢复
```bash
#!/bin/bash
# restore-redis.sh
# Redis数据恢复脚本

BACKUP_FILE="$1"

# 创建恢复前备份
echo "创建恢复前备份..."
./backup-redis.sh

# 停止Redis服务
kubectl scale deployment redis-deployment --replicas=0 -n athena-production

# 恢复Redis数据
echo "恢复Redis数据..."

# 解压备份文件
if [[ $BACKUP_FILE == *.gz ]]; then
    gunzip -c "$BACKUP_FILE" > "/tmp/redis_restore_$(date +%s).rdb"
    RESTORE_FILE="/tmp/redis_restore_$(date +%s).rdb"
else
    RESTORE_FILE="$BACKUP_FILE"
fi

# 复制到Pod
kubectl cp "$RESTORE_FILE" "athena-production/redis-pod:/data/dump.rdb"

# 重启Redis服务
kubectl scale deployment redis-deployment --replicas=1 -n athena-production
kubectl rollout status deployment/redis-deployment -n athena-production --timeout=300s

# 验证恢复结果
sleep 10
REDIS_KEYS=$(kubectl exec -n athena-production redis-pod -- redis-cli DBSIZE)

echo "✅ Redis恢复完成，键数量: $REDIS_KEYS"
```

### 3. Qdrant恢复

#### Qdrant数据恢复
```bash
#!/bin/bash
# restore-qdrant.sh
# Qdrant向量数据库恢复脚本

BACKUP_FILE="$1"

# 创建恢复前备份
echo "创建恢复前备份..."
./backup-qdrant.sh

# 停止Qdrant服务
kubectl scale deployment qdrant-deployment --replicas=0 -n athena-production
kubectl wait --for=condition=replicas=0 deployment/qdrant-deployment -n athena-production --timeout=300s

# 恢复Qdrant数据
echo "恢复Qdrant数据..."

# 解压备份文件
TEMP_DIR="/tmp/qdrant_restore_$(date +%s)"
mkdir -p "$TEMP_DIR"
tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"

# 清理现有数据
kubectl exec -n athena-production qdrant-pod -- rm -rf /qdrant/storage/* 2>/dev/null || true

# 复制恢复数据
kubectl cp "$TEMP_DIR/"* "athena-production/qdrant-pod:/qdrant/storage/"

# 重启Qdrant服务
kubectl scale deployment qdrant-deployment --replicas=1 -n athena-production
kubectl rollout status deployment/qdrant-deployment -n athena-production --timeout=300s

# 验证恢复结果
sleep 30
COLLECTIONS=$(kubectl exec -n athena-production qdrant-pod -- curl -s http://localhost:6333/collections | jq -r '.result.collections | length')

echo "✅ Qdrant恢复完成，集合数量: $COLLECTIONS"

# 清理临时目录
rm -rf "$TEMP_DIR"
```

## 🧪 备份验证和测试

### 1. 自动验证脚本

#### 备份完整性验证
```bash
#!/bin/bash
# verify-backup.sh
# 备份完整性验证脚本

BACKUP_FILE="$1"
BACKUP_TYPE="$2"

case $BACKUP_TYPE in
    "postgres")
        # 验证PostgreSQL备份
        if pg_restore --list --verbose "$BACKUP_FILE" &> /dev/null; then
            echo "✅ PostgreSQL备份验证通过"
            exit 0
        else
            echo "❌ PostgreSQL备份验证失败"
            exit 1
        fi
        ;;
    "redis")
        # 验证Redis备份
        if redis-cli --rdb "$BACKUP_FILE" &> /dev/null; then
            echo "✅ Redis备份验证通过"
            exit 0
        else
            echo "❌ Redis备份验证失败"
            exit 1
        fi
        ;;
    "qdrant")
        # 验证Qdrant备份
        if tar -tzf "$BACKUP_FILE" | head -10 | grep -q "collections"; then
            echo "✅ Qdrant备份验证通过"
            exit 0
        else
            echo "❌ Qdrant备份验证失败"
            exit 1
        fi
        ;;
    *)
        echo "❌ 未知的备份类型: $BACKUP_TYPE"
        exit 1
        ;;
esac
```

### 2. 定期恢复测试

#### 月度恢复测试
```bash
#!/bin/bash
# monthly-restore-test.sh
# 月度恢复测试脚本

TEST_ENV="athena-test"
TEST_BACKUP_DATE=$(date -d '7 days ago' +%Y%m%d)

# 创建测试环境
kubectl create namespace $TEST_ENV --dry-run=client -o yaml | kubectl apply -f -

# 从备份恢复到测试环境
echo "测试恢复PostgreSQL备份..."
./restore-postgres.sh "/backups/postgres/athena_prod_${TEST_BACKUP_DATE}.sql.gz"

# 部署最小测试应用
kubectl apply -f k8s/test-deployment.yaml -n $TEST_ENV

# 运行功能测试
./scripts/run-restore-tests.sh --namespace=$TEST_ENV

# 清理测试环境
kubectl delete namespace $TEST_ENV

echo "✅ 月度恢复测试完成"
```

## 📊 监控和报告

### 1. 备份监控

#### 备份状态监控
```bash
#!/bin/bash
# monitor-backups.sh
# 备份状态监控脚本

BACKUP_DIRS=("/backups/postgres" "/backups/redis" "/backups/qdrant")
MAX_AGE_HOURS=24

for dir in "${BACKUP_DIRS[@]}"; do
    backup_type=$(basename "$dir")
    
    # 检查最新备份时间
    latest_backup=$(find "$dir" -type f -name "*.gz" -o -name "*.sql" -o -name "*.rdb" | xargs ls -lt | head -1 | awk '{print $6, $7, $8}')
    
    if [ -n "$latest_backup" ]; then
        backup_age=$(( ( $(date +%s) - $(date -d "$latest_backup" +%s) ) / 3600 ))
        
        if [ $backup_age -gt $MAX_AGE_HOURS ]; then
            echo "⚠️ 警告: $backup_type 备份已过期 (${backup_age}小时)"
            ./scripts/send-alert.sh --type="backup-expired" --service="$backup_type" --age="$backup_age"
        else
            echo "✅ $backup_type 备份正常 (最新: $latest_backup)"
        fi
    else
        echo "❌ 错误: $backup_type 没有找到备份文件"
        ./scripts/send-alert.sh --type="backup-missing" --service="$backup_type"
    fi
done
```

### 2. 备份报告生成

#### 每日备份报告
```bash
#!/bin/bash
# daily-backup-report.sh
# 每日备份报告脚本

DATE=$(date +%Y-%m-%d)
REPORT_FILE="/reports/daily_backup_${DATE}.md"

# 生成报告
cat > "$REPORT_FILE" << EOF
# 每日备份报告 - $DATE

## 备份统计

### PostgreSQL
- 备份文件数: $(find /backups/postgres -name "*.gz" -mtime -1 | wc -l)
- 总大小: $(du -sh /backups/postgres -mtime -1 | cut -f1)
- 最新备份: $(ls -lt /backups/postgres/*.gz | head -1 | awk '{print $9}')

### Redis
- 备份文件数: $(find /backups/redis -name "*.gz" -mtime -1 | wc -l)
- 总大小: $(du -sh /backups/redis -mtime -1 | cut -f1)
- 最新备份: $(ls -lt /backups/redis/*.gz | head -1 | awk '{print $9}')

### Qdrant
- 备份文件数: $(find /backups/qdrant -name "*.tar.gz" -mtime -1 | wc -l)
- 总大小: $(du -sh /backups/qdrant -mtime -1 | cut -f1)
- 最新备份: $(ls -lt /backups/qdrant/*.tar.gz | head -1 | awk '{print $9}')

## 存储状态

### 本地存储
- 可用空间: $(df -h /backups | awk 'NR==2{print $4}')
- 使用率: $(df -h /backups | awk 'NR==2{print $5}')

### 远程存储
- S3上传状态: $(./scripts/check-s3-sync.sh)
- 同步延迟: $(./scripts/check-sync-delay.sh)

## 告警信息

$./scripts/get-backup-alerts.sh --since=yesterday

## 建议

$./scripts/get-backup-recommendations.sh

EOF

# 发送报告
./scripts/send-report.sh --file="$REPORT_FILE" --type="daily-backup"

echo "✅ 每日备份报告生成完成: $REPORT_FILE"
```

## 🚨 灾难恢复计划

### 1. RTO/RPO目标

| 服务类型 | RTO (恢复时间目标) | RPO (恢复点目标) |
|---------|------------------|------------------|
| 数据库 | 4小时 | 1小时 |
| 缓存 | 2小时 | 30分钟 |
| 向量数据库 | 6小时 | 2小时 |
| 应用服务 | 1小时 | 15分钟 |
| 监控系统 | 2小时 | 1小时 |

### 2. 灾难恢复步骤

#### 立即响应 (0-30分钟)
1. **启动灾难恢复团队**
2. **评估灾难范围和影响**
3. **激活灾难恢复计划**
4. **通知相关方**

#### 系统恢复 (30分钟-4小时)
1. **准备新基础设施**
2. **从备份恢复数据**
3. **重新部署服务**
4. **配置网络和安全**

#### 验证和监控 (4-6小时)
1. **功能测试和验证**
2. **性能监控和调优**
3. **安全检查和加固**
4. **用户通知和培训**

---

**⚠️ 重要提醒**:
1. 所有备份必须定期验证
2. 恢复流程必须定期测试
3. 灾难恢复计划必须定期演练
4. 备份存储必须考虑地理分布
5. 加密密钥必须安全管理

---

*Athena工作平台数据备份和恢复策略 - 2026-02-20*