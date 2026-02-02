# RAG智能问答服务 - 部署和使用指南

**服务版本**: v4.0.0 缓存增强版
**部署日期**: 2026-01-20

---

## 📋 目录

1. [系统要求](#系统要求)
2. [安装步骤](#安装步骤)
3. [配置说明](#配置说明)
4. [服务启动](#服务启动)
5. [使用指南](#使用指南)
6. [监控维护](#监控维护)
7. [故障排查](#故障排查)

---

## 🔧 系统要求

### 硬件要求

| 组件 | 最低配置 | 推荐配置 |
|-----|---------|---------|
| CPU | 4核心 | 8核心+ |
| 内存 | 8GB | 16GB+ |
| 存储 | 50GB SSD | 100GB+ NVMe |
| GPU | - | Apple Silicon (MPS) |

### 软件要求

| 软件 | 版本要求 |
|-----|---------|
| Python | 3.14+ |
| PostgreSQL | 15+ (含pgvector扩展) |
| Redis | 7.0+ |
| NebulaGraph | 3.x |

---

## 📦 安装步骤

### 1. 安装Python依赖

```bash
# 创建虚拟环境（可选）
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install fastapi uvicorn psycopg2-binary sentence-transformers zhipuai nebula3 redis
```

### 2. 配置PostgreSQL

```bash
# 确保pgvector扩展已安装
psql -U postgres -d athena -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 验证向量列存在
psql -U postgres -d athena -c "SELECT column_name FROM information_schema.columns WHERE table_name = 'patent_invalidation_decisions' AND data_type = 'vector';"
```

### 3. 配置Redis

```bash
# 启动Redis服务
redis-server

# 验证Redis运行
redis-cli ping
# 预期输出: PONG
```

### 4. 配置NebulaGraph

```bash
# 确保NebulaGraph服务运行
# 验证连接
nebula-console -addr 127.0.0.1 -port 9669 -u root -p nebula
> USE legal_kg_v2;
> SHOW SPACES;
```

---

## ⚙️ 配置说明

### 环境变量配置

创建 `.env` 文件：

```bash
# 数据库配置
DB_HOST=localhost
DB_PORT=5432
DB_NAME=athena
DB_USER=xujian
DB_PASSWORD=your_password
DB_TIMEOUT=30

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# GLM-4.7配置
ZHIPUAI_API_KEY=your_api_key_here

# CORS配置
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8011
```

### 加载环境变量

```bash
# 方式1: 直接加载
export $(cat .env | xargs)

# 方式2: 使用python-dotenv
pip install python-dotenv
```

---

## 🚀 服务启动

### 开发模式启动

```bash
cd /Users/xujian/Athena工作平台/services/rag-qa-service
python3 patent_qa_glm_v4.py
```

### 生产模式启动

```bash
# 使用uvicorn
uvicorn patent_qa_glm_v4:app \
  --host 0.0.0.0 \
  --port 8012 \
  --workers 4 \
  --log-level info \
  --access-log
```

### 后台服务启动

```bash
# 使用nohup
nohup python3 patent_qa_glm_v4.py > /var/log/patent_qa_v4.log 2>&1 &

# 使用systemd（推荐）
sudo vi /etc/systemd/system/patent-qa.service
```

**systemd服务配置**:

```ini
[Unit]
Description=Patent Q&A Service V4.0
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=xujian
WorkingDirectory=/Users/xujian/Athena工作平台/services/rag-qa-service
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/bin/python3 patent_qa_glm_v4.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 启用并启动服务
sudo systemctl daemon-reload
sudo systemctl enable patent-qa
sudo systemctl start patent-qa

# 查看状态
sudo systemctl status patent-qa
```

---

## 📖 使用指南

### 基础问答

```bash
curl -X POST http://localhost:8012/api/qa \
  -H 'Content-Type: application/json' \
  -d '{
    "question": "专利创造性如何判断？",
    "top_k": 5,
    "use_llm": true
  }'
```

### 快速问答（不使用LLM）

```bash
curl -X POST http://localhost:8012/api/qa \
  -H 'Content-Type: application/json' \
  -d '{
    "question": "什么是专利创造性？",
    "use_llm": false,
    "use_cache": true
  }'
```

### 查询性能指标

```bash
curl http://localhost:8012/metrics
```

### 清除缓存

```bash
# 清除所有缓存
curl -X POST http://localhost:8012/api/cache/clear \
  -H 'Content-Type: application/json' \
  -d '{"pattern": ""}'

# 清除向量搜索缓存
curl -X POST http://localhost:8012/api/cache/clear \
  -H 'Content-Type: application/json' \
  -d '{"pattern": "vector"}'
```

---

## 📊 监控维护

### 性能监控

**关键指标**:

| 指标 | 健康阈值 | 说明 |
|-----|---------|------|
| cache_hit_rate | >80% | 缓存命中率 |
| avg_response_time | <200ms | 平均响应时间 |
| total_requests | - | 总请求数 |
| database | connected | 数据库连接状态 |
| redis | connected | Redis连接状态 |

**监控脚本**:

```bash
#!/bin/bash
# monitor.sh

while true; do
    response=$(curl -s http://localhost:8012/health)
    status=$(echo $response | jq -r '.status')

    if [ "$status" != "healthy" ]; then
        echo "[$(date)] 服务异常: $response"
        # 发送告警通知
    fi

    sleep 60
done
```

### 日志管理

```bash
# 查看实时日志
tail -f /tmp/patent_qa_v4.log

# 查看错误日志
grep -i "error\|exception" /tmp/patent_qa_v4.log

# 日志轮转配置
sudo vi /etc/logrotate.d/patent-qa
```

**logrotate配置**:

```
/tmp/patent_qa_v4.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
    create 644 xujian xujian
}
```

### 备份策略

```bash
# 数据库备份
pg_dump -U xujian athena > backup_athena_$(date +%Y%m%d).sql

# Redis备份
redis-cli BGSAVE

# 代码备份
git push backup main
```

---

## 🔍 故障排查

### 常见问题

#### 1. 服务启动失败

**症状**: 启动时报错 "Address already in use"

**解决**:
```bash
# 查找占用端口的进程
lsof -ti:8012

# 杀掉进程
kill -9 $(lsof -ti:8012)

# 或使用其他端口
uvicorn patent_qa_glm_v4:app --port 8013
```

#### 2. 数据库连接失败

**症状**: "could not connect to server"

**检查**:
```bash
# 检查PostgreSQL状态
sudo systemctl status postgresql

# 检查连接配置
psql -h localhost -U xujian -d athena -c "SELECT 1;"
```

#### 3. Redis连接失败

**症状**: "Redis connection failed"

**解决**:
```bash
# 启动Redis
redis-server

# 验证连接
redis-cli ping
```

#### 4. 模型加载失败

**症状**: "Failed to load embedding model"

**检查**:
```bash
# 验证模型路径
ls -la /Users/xujian/Athena工作平台/models/converted/BAAI/bge-m3

# 检查磁盘空间
df -h
```

#### 5. 缓存命中率低

**症状**: cache_hit_rate < 50%

**解决**:
```bash
# 增加缓存TTL
# 修改配置文件中的:
CACHE_TTL_QUERY = 7200  # 2小时

# 检查Redis内存
redis-cli INFO memory
```

---

## 📈 性能优化建议

### 1. 数据库优化

```sql
-- 创建索引
CREATE INDEX idx_embedding_gin ON patent_invalidation_decisions USING gin(embedding);
CREATE INDEX idx_decision_number ON patent_invalidation_decisions(decision_number);

-- 调整连接池大小
minconn=4, maxconn=20
```

### 2. Redis优化

```bash
# 设置最大内存
redis-cli CONFIG SET maxmemory 2gb

# 设置淘汰策略
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

### 3. 应用层优化

- 启用缓存 (`use_cache: true`)
- 调整 `top_k` 值 (3-10)
- 禁用LLM用于简单查询 (`use_llm: false`)

---

## 🔄 版本升级

### 从V3.0升级到V4.0

```bash
# 1. 备份当前版本
cp patent_qa_glm.py patent_qa_glm_v3_backup.py

# 2. 停止服务
sudo systemctl stop patent-qa

# 3. 替换代码
cp patent_qa_glm_v4.py patent_qa_glm.py

# 4. 更新systemd配置（如果需要）
sudo systemctl daemon-reload

# 5. 启动服务
sudo systemctl start patent-qa

# 6. 验证
curl http://localhost:8012/health
```

---

## 📞 技术支持

**文档**: API_REFERENCE_V4.md
**日志**: /tmp/patent_qa_v4.log
**问题反馈**: xujian519@gmail.com

**检查清单**:

- [ ] Python 3.14+ 已安装
- [ ] PostgreSQL + pgvector 已配置
- [ ] Redis 服务运行中
- [ ] NebulaGraph 服务运行中
- [ ] 环境变量已配置
- [ ] BGE-M3模型路径正确
- [ ] GLM API密钥已设置
- [ ] 防火墙端口已开放
- [ ] systemd服务已配置
