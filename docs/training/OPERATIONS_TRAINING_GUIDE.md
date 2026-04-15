# Athena平台运维培训指南

**版本**: v5.0.0  
**更新时间**: 2025-12-14  
**培训时长**: 2.5小时  
**目标读者**: 运维人员、系统管理员

---

## 📚 培训大纲

1. [监控系统使用](#监控系统使用) (60分钟)
2. [部署和扩容](#部署和扩容) (45分钟)
3. [备份和恢复](#备份和恢复) (45分钟)
4. [故障排查实战](#故障排查实战) (30分钟)

---

## 📊 监控系统使用

### 1.1 监控架构概览

```
┌──────────────────────────────────────────────────────────┐
│                  Athena监控体系                            │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐           │
│  │Prometheus│    │ Grafana  │    │  Jaeger  │           │
│  │  :9090   │    │  :3000   │    │  :16686  │           │
│  │          │    │          │    │          │           │
│  │ 指标采集  │←───│ 可视化   │←───│ 分布式追踪│           │
│  │ 告警规则  │    │ 仪表板   │    │ 调用链   │           │
│  └──────────┘    └──────────┘    └──────────┘           │
│        │                │                │               │
│        └────────────────┴────────────────┘               │
│                         │                                 │
│                   所有Athena服务                          │
│                   (自动暴露指标)                           │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

### 1.2 Prometheus监控

#### 访问地址
- **Prometheus UI**: http://localhost:9090
- **默认刷新**: 15秒
- **数据保留**: 30天

#### 常用查询示例

**1. 专利分析QPS（每秒查询率）**
```promql
# 最近5分钟的QPS
rate(patent_analysis_total[5m])

# 按分析类型分组
rate(patent_analysis_total[5m]) by (type)

# 只计算成功的分析
rate(patent_analysis_total{status="completed"}[5m])
```

**2. 专利分析延迟**
```promql
# P50延迟（中位数）
histogram_quantile(0.50, patent_analysis_duration_seconds_bucket)

# P95延迟
histogram_quantile(0.95, patent_analysis_duration_seconds_bucket)

# P99延迟
histogram_quantile(0.99, patent_analysis_duration_seconds_bucket)

# 平均延迟
rate(patent_analysis_duration_seconds_sum[5m]) 
  / rate(patent_analysis_duration_seconds_count[5m])
```

**3. 缓存性能**
```promql
# 缓存命中率
sum(rate(cache_hits_total[5m])) / 
  (sum(rate(cache_hits_total[5m])) + sum(rate(cache_misses_total[5m])))

# 按缓存类型分组
sum(rate(cache_hits_total[5m])) by (cache_type) / 
  (sum(rate(cache_hits_total[5m])) by (cache_type) + 
   sum(rate(cache_misses_total[5m])) by (cache_type))
```

**4. LLM调用监控**
```promql
# LLM调用量趋势
sum(rate(llm_requests_total[5m])) by (model)

# LLM平均响应时间
rate(llm_response_time_seconds_sum[5m]) by (model) 
  / rate(llm_response_time_seconds_count[5m]) by (model)

# LLM成本趋势
sum(llm_cost_yuan) by (model)
```

**5. 服务健康状态**
```promql
# 服务可用性
up{job="patent-execution-service"}

# CPU使用率
rate(process_cpu_seconds_total[5m]) by (instance) * 100

# 内存使用
process_resident_memory_bytes / 1024 / 1024  # MB
```

### 1.3 Grafana仪表板

#### 访问地址
- **Grafana UI**: http://localhost:3000
- **默认账号**: admin / athena123
- **首次登录**: 需要修改密码

#### 仪表板列表

**1. Athena平台总览**
- 位置: Home → Athena平台总览
- 刷新频率: 30秒
- 面板数量: 20个

**关键面板**:
```
┌─────────────────────────────────────────────┐
│  服务健康状态                │  5个服务在线 │
├─────────────────────────────────────────────┤
│  总请求量（24小时）          │  125,432     │
├─────────────────────────────────────────────┤
│  错误率                      │  1.2%        │
├─────────────────────────────────────────────┤
│  P95延迟                    │  3.6s        │
├─────────────────────────────────────────────┤
│  CPU使用率                  │  45%         │
├─────────────────────────────────────────────┤
│  内存使用率                  │  68%         │
└─────────────────────────────────────────────┘
```

**2. 专利执行专项**
- 位置: Home → 专利执行专项
- 刷新频率: 30秒
- 面板数量: 22个

**关键面板**:
```
┌─────────────────────────────────────────────┐
│  今日处理专利数              │  3,245       │
├─────────────────────────────────────────────┤
│  专利分析成功率              │  96.5%       │
├─────────────────────────────────────────────┤
│  平均分析时间                │  4.2s        │
├─────────────────────────────────────────────┤
│  LLM调用量（24小时）         │  12,543      │
├─────────────────────────────────────────────┤
│  缓存命中率                  │  42.3%       │
├─────────────────────────────────────────────┤
│  今日分析成本                │  ¥34,065     │
└─────────────────────────────────────────────┘
```

#### 仪表板操作

**1. 导入仪表板**
```
步骤:
1. 登录Grafana
2. 点击 "+" → "Import"
3. 选择 "Upload JSON file"
4. 选择仪表板JSON文件
   - platform_overview.json
   - patent_execution.json
5. 点击 "Import"
```

**2. 自定义时间范围**
```
快捷选项:
- Last 5 minutes
- Last 1 hour
- Last 3 hours
- Last 12 hours
- Last 24 hours
- Last 7 days
- Custom: 自定义时间范围
```

**3. 添加变量（模板化）**
```
场景: 按服务名动态过滤

1. 编辑仪表板
2. Settings → Variables → Add variable
3. 配置:
   - Name: service_name
   - Type: Query
   - Query: label_values(up, job)
4. 保存
5. 在面板查询中使用: $service_name
```

### 1.4 Jaeger分布式追踪

#### 访问地址
- **Jaeger UI**: http://localhost:16686
- **数据保留**: 7天

#### 使用场景

**场景1: 查找特定Trace**
```
步骤:
1. 选择服务: patent-service
2. 选择操作: analyze_patent
3. 设置时间范围: Lookback 1h
4. 点击 "Find Traces"
5. 查看Trace列表
```

**场景2: 分析性能瓶颈**
```
步骤:
1. 点击Trace ID
2. 查看调用链瀑布图
3. 找到耗时最长的Span（红色高亮）
4. 点击Span查看详情:
   - Tags: 参数和属性
   - Logs: 事件日志
   - Errors: 异常信息
```

**场景3: 跨服务调用追踪**
```
场景: 用户请求经过多个服务

Trace调用链:
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   API网关    │────▶│ 专利服务     │────▶│  LLM服务     │
│  100ms       │     │  3500ms      │     │  3200ms      │
└──────────────┘     └──────────────┘     └──────────────┘
      ↑                     ↑                     ↑
      └─────────────────────┴─────────────────────┘
                    同一个Trace ID
```

---

## 🚀 部署和扩容

### 2.1 一键部署

#### 启动监控栈

```bash
# 进入监控配置目录
cd shared/observability/monitoring

# 启动所有监控服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 预期输出:
# NAME                STATUS          PORTS
# prometheus          Up              0.0.0.0:9090->9090/tcp
# grafana             Up              0.0.0.0:3000->3000/tcp
# jaeger              Up              0.0.0.0:16686->16686/tcp
```

#### 启动应用服务

```bash
# 回到项目根目录
cd /Users/xujian/Athena工作平台

# 启动应用服务
docker-compose up -d

# 查看日志
docker-compose logs -f patent-service
```

### 2.2 配置文件管理

#### 环境变量配置

```bash
# .env文件示例
cat > .env << 'ENV'
# 应用配置
APP_NAME=athena-patent-platform
APP_VERSION=5.0.0
DEBUG=false

# 数据库配置
DATABASE_URL=postgresql://athena:secure_password@db:5432/athena_patents
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis配置
REDIS_URL=redis://:redis_password@redis:6379/0
REDIS_CACHE_TTL=3600
REDIS_MAX_CONNECTIONS=50

# LLM配置
LLM_SERVICE_URL=http://llm-service:8002
LLM_TIMEOUT=30
LLM_MAX_RETRIES=3

# 可观测性配置
TELEMETRY_ENABLED=true
TELEMETRY_EXPORTER=jaeger
JAEGER_ENDPOINT=http://jaeger:14250/api/traces
PROMETHEUS_PORT=9090
ENV
```

### 2.3 服务扩容

#### 水平扩容（增加实例数）

```bash
# 扩容patent-service到3个实例
docker-compose up -d --scale patent-service=3

# 验证扩容
docker-compose ps patent-service
# 应该看到3个容器在运行

# 查看负载均衡
curl http://localhost:8000/health
# 多次请求会轮询到不同实例
```

#### 垂直扩容（增加资源）

```yaml
# 编辑docker-compose.yml
services:
  patent-service:
    deploy:
      resources:
        limits:
          cpus: '2'      # CPU限制
          memory: 4G     # 内存限制
        reservations:
          cpus: '1'      # CPU预留
          memory: 2G     # 内存预留
```

```bash
# 应用配置
docker-compose up -d

# 验证资源限制
docker stats patent-service
```

### 2.4 滚动更新

```bash
# 拉取新镜像
docker-compose pull

# 滚动更新（零停机）
docker-compose up -d --no-deps --build patent-service

# 监控更新进度
docker-compose logs -f patent-service

# 回滚（如果需要）
docker-compose down
git checkout <previous_commit>
docker-compose up -d
```

---

## 💾 备份和恢复

### 3.1 备份策略

#### 数据分类和保留策略

| 数据类型 | 备份频率 | 保留时间 | 存储位置 |
|---------|---------|---------|----------|
| PostgreSQL | 每天 | 30天 | /backup/postgres |
| Redis | 每天 | 7天 | /backup/redis |
| 配置文件 | 每周 | 90天 | /backup/configs |
| 监控数据 | N/A | 30天 | Prometheus内置 |

### 3.2 自动备份脚本

#### PostgreSQL备份

```bash
#!/bin/bash
# scripts/backup_postgres.sh

set -e

BACKUP_DIR="/backup/postgres"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="athena_patents_${DATE}.sql.gz"

# 创建备份目录
mkdir -p ${BACKUP_DIR}

# 执行备份
echo "开始备份PostgreSQL..."
docker exec athena-postgres pg_dump -U athena athena_patents | gzip > ${BACKUP_DIR}/${BACKUP_FILE}

# 验证备份
if [ -f "${BACKUP_DIR}/${BACKUP_FILE}" ]; then
    SIZE=$(du -h ${BACKUP_DIR}/${BACKUP_FILE} | cut -f1)
    echo "备份成功: ${BACKUP_FILE} (${SIZE})"
else
    echo "备份失败!"
    exit 1
fi

# 删除30天前的备份
find ${BACKUP_DIR} -name "*.sql.gz" -mtime +30 -delete

# 记录日志
echo "$(date '+%Y-%m-%d %H:%M:%S') - PostgreSQL备份完成: ${BACKUP_FILE} (${SIZE})" >> /var/log/athena_backup.log
```

#### Redis备份

```bash
#!/bin/bash
# scripts/backup_redis.sh

set -e

BACKUP_DIR="/backup/redis"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="redis_backup_${DATE}.rdb"

# 创建备份目录
mkdir -p ${BACKUP_DIR}

# 触发Redis保存
echo "触发Redis保存..."
docker exec athena-redis redis-cli BGSAVE

# 等待保存完成
sleep 10

# 验证保存完成
while docker exec athena-redis redis-cli LASTSAVE | grep -q $(date +%s); do
    echo "等待Redis保存完成..."
    sleep 1
done

# 复制RDB文件
docker cp athena-redis:/data/dump.rdb ${BACKUP_DIR}/${BACKUP_FILE}

# 验证备份
if [ -f "${BACKUP_DIR}/${BACKUP_FILE}" ]; then
    SIZE=$(du -h ${BACKUP_DIR}/${BACKUP_FILE} | cut -f1)
    echo "备份成功: ${BACKUP_FILE} (${SIZE})"
else
    echo "备份失败!"
    exit 1
fi

# 删除7天前的备份
find ${BACKUP_DIR} -name "*.rdb" -mtime +7 -delete

# 记录日志
echo "$(date '+%Y-%m-%d %H:%M:%S') - Redis备份完成: ${BACKUP_FILE} (${SIZE})" >> /var/log/athena_backup.log
```

### 3.3 定时备份配置

```bash
# 编辑crontab
crontab -e

# 添加以下任务
# 每天凌晨2点备份PostgreSQL
0 2 * * * /path/to/scripts/backup_postgres.sh

# 每天凌晨3点备份Redis
0 3 * * * /path/to/scripts/backup_redis.sh

# 每周日凌晨4点备份配置文件
0 4 * * 0 /path/to/scripts/backup_configs.sh

# 每月1号凌晨5点备份监控数据
0 5 1 * * /path/to/scripts/backup_monitoring.sh
```

### 3.4 数据恢复

#### PostgreSQL恢复

```bash
# 1. 停止应用服务
docker-compose stop patent-service

# 2. 选择备份文件
ls -lh /backup/postgres/
# 输出: athena_patents_20251214_020000.sql.gz

# 3. 恢复数据库
gunzip < /backup/postgres/athena_patents_20251214_020000.sql.gz | \
  docker exec -i athena-postgres psql -U athena athena_patents

# 4. 验证恢复
docker exec athena-postgres psql -U athena athena_patents -c "\dt"

# 5. 重启应用服务
docker-compose start patent-service

# 6. 验证服务
curl http://localhost:8000/health
```

#### Redis恢复

```bash
# 1. 停止Redis
docker-compose stop redis

# 2. 备份当前数据（如果需要）
mv /var/lib/redis/dump.rdb /var/lib/redis/dump.rdb.old

# 3. 复制备份文件
cp /backup/redis/redis_backup_20251214_030000.rdb /var/lib/redis/dump.rdb

# 4. 修复权限
chown redis:redis /var/lib/redis/dump.rdb
chmod 640 /var/lib/redis/dump.rdb

# 5. 启动Redis
docker-compose start redis

# 6. 验证恢复
docker exec athena-redis redis-cli DBSIZE
# 应该显示恢复后的键数量
```

---

## 🆘 故障排查实战

### 4.1 常见故障处理流程

```
故障告警 → 确认影响 → 查找原因 → 执行修复 → 验证恢复 → 总结复盘
```

### 4.2 故障场景1: 服务无响应

**症状**: API请求超时，健康检查失败

**诊断步骤**:

```bash
# 1. 检查服务状态
docker-compose ps
# 查看patent-service状态是否为"Up"

# 2. 查看服务日志
docker-compose logs --tail=100 patent-service
# 查找错误信息、异常堆栈

# 3. 检查资源使用
docker stats patent-service
# 查看CPU、内存是否超限

# 4. 进入容器检查
docker exec -it patent-service bash
# 检查进程、端口、文件系统
```

**解决方案**:

```bash
# 场景A: 服务卡死
docker-compose restart patent-service

# 场景B: 内存不足
# 增加内存限制或重启服务
docker-compose up -d --force-recreate patent-service

# 场景C: 数据库连接失败
# 检查数据库服务
docker-compose ps postgres
docker-compose logs postgres
```

### 4.3 故障场景2: 数据库连接失败

**症状**: 日志显示"Error connecting to database"

**诊断步骤**:

```bash
# 1. 检查数据库服务
docker-compose ps postgres

# 2. 测试数据库连接
docker exec -it athena-postgres psql -U athena -d athena_patents

# 3. 检查连接池
docker exec patent-service env | grep DATABASE_POOL

# 4. 查看数据库连接数
docker exec athena-postgres psql -U athena -d athena_patents -c "
  SELECT count(*) FROM pg_stat_activity;
"
```

**解决方案**:

```bash
# 场景A: 数据库未启动
docker-compose up -d postgres

# 场景B: 连接池耗尽
# 增加连接池大小
# 编辑.env: DATABASE_POOL_SIZE=50
docker-compose restart patent-service

# 场景C: 数据库锁定
docker exec athena-postgres psql -U athena -d athena_patents -c "
  SELECT pg_terminate_backend(pid) 
  FROM pg_stat_activity 
  WHERE datname = 'athena_patents' 
  AND pid <> pg_backend_pid();
"
```

### 4.4 故障场景3: 缓存失效

**症状**: 响应时间激增，缓存命中率下降

**诊断步骤**:

```bash
# 1. 检查Redis服务
docker-compose ps redis

# 2. 查看缓存指标
# 在Prometheus中查询:
# cache_hit_rate
# cache_misses_total

# 3. 检查Redis内存
docker exec athena-redis redis-cli INFO memory

# 4. 查看缓存键数量
docker exec athena-redis redis-cli DBSIZE
```

**解决方案**:

```bash
# 场景A: Redis服务未启动
docker-compose up -d redis

# 场景B: Redis内存满
# 清理过期键
docker exec athena-redis redis-cli --scan --pattern "patent:*" | \
  xargs docker exec athena-redis redis-cli DEL

# 场景C: 缓存策略问题
# 调整TTL或预热缓存
```

### 4.5 故障场景4: 监控数据丢失

**症状**: Grafana仪表板显示"No Data"

**诊断步骤**:

```bash
# 1. 检查Prometheus服务
docker-compose ps prometheus

# 2. 检查Prometheus日志
docker-compose logs prometheus

# 3. 检查服务是否暴露/metrics端点
curl http://localhost:8000/metrics

# 4. 查看Prometheus配置
docker exec prometheus cat /etc/prometheus/prometheus.yml
```

**解决方案**:

```bash
# 场景A: Prometheus未启动
docker-compose up -d prometheus

# 场景B: 服务未暴露metrics
# 确保环境变量TELEMETRY_ENABLED=true
docker-compose restart patent-service

# 场景C: Prometheus配置错误
# 检查scrape_configs配置
# 重新加载配置
docker-compose restart prometheus
```

---

## 📋 运维检查清单

### 日常检查（每天，15分钟）

- [ ] 检查所有服务健康状态
  ```bash
  docker-compose ps
  curl http://localhost:8000/health
  ```

- [ ] 查看Grafana仪表板
  - 服务可用性
  - 错误率
  - P95延迟

- [ ] 检查告警通知
  - 查看邮箱/企业微信/钉钉
  - 处理P0/P1告警

- [ ] 查看日志错误
  ```bash
  docker-compose logs --since=1h | grep ERROR
  ```

### 周检查（每周，30分钟）

- [ ] 分析性能趋势
  - 对比上周指标
  - 识别性能下降

- [ ] 检查磁盘使用
  ```bash
  df -h
  docker system df
  ```

- [ ] 清理旧日志
  ```bash
  docker system prune -a --volumes
  ```

- [ ] 审查安全日志
  - 登录失败
  - 异常访问

### 月检查（每月，1小时）

- [ ] 性能基线评估
  - 更新性能基准
  - 调整告警阈值

- [ ] 成本分析
  - LLM调用成本
  - 资源使用成本

- [ ] 容量规划
  - 预测增长需求
  - 规划扩容时间

- [ ] 灾难恢复演练
  - 执行一次恢复测试
  - 更新恢复文档

---

## 📞 技术支持

**文档**: https://docs.athena-platform.com  
**GitHub**: https://github.com/athena-platform/patent-platform  
**邮件**: athena-support@example.com

---

**培训版本**: v5.0.0  
**最后更新**: 2025-12-14  
**维护团队**: Athena AI系统
