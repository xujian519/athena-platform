# 法律知识图谱系统运维手册

## 📋 系统概述

法律知识图谱系统是基于向量搜索的智能法律条款检索平台，支持1024维BGE向量相似度搜索，提供高性能的法律条款查询和智能分类功能。

### 核心组件
- **PostgreSQL**: 主数据库，存储法律条款元数据
- **Qdrant**: 向量数据库，存储1024维法律向量
- **Redis**: 缓存系统，提供L1+L2智能缓存
- **API服务**: RESTful API，提供搜索和查询接口
- **监控系统**: 实时监控服务健康状态和性能指标

---

## 🚀 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    法律系统架构图                              │
├─────────────────────────────────────────────────────────────┤
│  客户端应用                                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │   Web UI    │  │ Mobile App  │  │   API       │           │
│  └─────────────┘  └─────────────┘  └─────────────┘           │
├─────────────────────────────────────────────────────────────┤
│  API网关层 (端口: 8001)                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ • 健康检查    • 搜索接口    • 向量生成                    │   │
│  │ • 性能监控    • 限流控制    • 认证授权                    │   │
│  └─────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  业务逻辑层                                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │ 搜索引擎     │  │ 缓存管理     │  │ 向量计算     │           │
│  └─────────────┘  └─────────────┘  └─────────────┘           │
├─────────────────────────────────────────────────────────────┤
│  数据存储层                                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │ PostgreSQL  │  │   Qdrant    │  │   Redis     │           │
│  │ (端口: 5433)│  │ (端口: 6333)│  │ (端口: 6380)│           │
│  └─────────────┘  └─────────────┘  └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 服务端点

### 核心API接口
- **API地址**: `http://localhost:8001`
- **健康检查**: `GET /health`
- **法律搜索**: `POST /search`
- **集合信息**: `GET /collections`
- **系统统计**: `GET /stats`
- **向量生成**: `POST /embeddings`
- **性能测试**: `POST /benchmark`

### 数据库连接
- **PostgreSQL**: `localhost:5433`
- **Qdrant**: `localhost:6333`
- **Redis**: `localhost:6380`

---

## 📊 监控指标

### 系统健康指标
| 指标类别 | 监控项目 | 正常阈值 | 告警阈值 |
|---------|---------|---------|---------|
| 系统资源 | CPU使用率 | < 80% | > 80% (警告) / > 95% (严重) |
| 系统资源 | 内存使用率 | < 85% | > 85% (警告) / > 95% (严重) |
| 系统资源 | 磁盘使用率 | < 90% | > 90% (警告) / > 98% (严重) |
| 服务状态 | PostgreSQL | 健康 | 不健康 |
| 服务状态 | Qdrant | 健康 | 不健康 |
| 服务状态 | Redis | 健康 | 不健康 |
| 性能指标 | 响应时间 | < 2000ms | > 2000ms (警告) / > 5000ms (严重) |
| 性能指标 | 错误率 | < 5% | > 5% (警告) / > 15% (严重) |

### 业务指标
- **搜索请求量**: 每分钟搜索请求数
- **平均搜索时间**: 搜索响应时间平均值
- **缓存命中率**: L1+L2缓存整体命中率
- **向量索引大小**: 各集合向量数量
- **并发用户数**: 同时在线用户数

---

## 🛠️ 部署流程

### 1. 环境准备
```bash
# 检查系统要求
python3 --version    # Python 3.8+
docker --version      # Docker 20.10+

# 确保端口可用
netstat -tlnp | grep -E ":5433|:6333|:6380|:8001"
```

### 2. 启动服务
```bash
# 启动Docker容器
cd /Users/xujian/Athena工作平台
docker-compose -f infrastructure/docker/compose/legal-simple.yml up -d

# 等待服务就绪
sleep 15

# 检查服务状态
docker ps | grep legal

# 启动监控系统
python3 dev/scripts/legal_system_monitor.py &

# 启动API服务
python3 dev/scripts/simple_legal_api.py &
```

### 3. 验证部署
```bash
# 健康检查
curl http://localhost:8001/health

# 搜索测试
curl -X POST http://localhost:8001/search \
  -H "Content-Type: application/json" \
  -d '{"query": "合同违约", "type": "hybrid", "limit": 5}'
```

---

## 🚨 应急预案

### 1. 服务故障处理

#### PostgreSQL故障
**症状**: 数据库连接失败或响应超时
**影响**: 无法查询法律条款元数据

**处理步骤**:
```bash
# 检查容器状态
docker ps | grep postgresql

# 查看容器日志
docker logs athena_postgres_legal --tail 50

# 重启容器
docker restart athena_postgres_legal

# 验证连接
docker exec athena_postgres_legal psql -U legal_user -d legal_db -c "SELECT 1;"
```

**预防措施**:
- 定期备份数据库
- 监控连接池状态
- 设置连接超时和重试机制

#### Qdrant故障
**症状**: 向量搜索失败或响应缓慢
**影响**: 无法进行向量相似度搜索

**处理步骤**:
```bash
# 检查容器状态
docker ps | grep qdrant

# 查看服务状态
curl http://localhost:6333/

# 重启容器
docker restart athena_qdrant_legal

# 验证集合
curl http://localhost:6333/collections
```

**预防措施**:
- 监控内存使用情况
- 定期检查向量索引完整性
- 设置资源限制和自动重启

#### Redis故障
**症状**: 缓存失效或响应缓慢
**影响**: 搜索性能下降

**处理步骤**:
```bash
# 检查容器状态
docker ps | grep redis

# 测试连接
docker exec athena_redis_legal redis-cli ping

# 重启容器
docker restart athena_redis_legal

# 清理缓存
docker exec athena_redis_legal redis-cli FLUSHDB
```

**预防措施**:
- 监控内存使用率
- 设置合理的TTL策略
- 实施主从复制

#### API服务故障
**症状**: API接口无响应
**影响**: 无法提供搜索服务

**处理步骤**:
```bash
# 检查进程
ps aux | grep simple_legal_api

# 重启服务
pkill -f simple_legal_api
python3 dev/scripts/simple_legal_api.py &

# 验证服务
curl http://localhost:8001/health
```

### 2. 性能问题处理

#### 搜索响应缓慢
**可能原因**:
- 向量索引未建立
- 数据库查询优化不足
- 缓存未命中

**解决方案**:
```bash
# 检查向量索引
python3 -c "
from scripts.legal_vector_search_optimizer import LegalVectorSearchOptimizer
engine = LegalVectorSearchOptimizer()
stats = engine.get_search_statistics()
print(stats)
"

# 清理并重建缓存
docker exec athena_redis_legal redis-cli FLUSHALL

# 重启API服务
pkill -f simple_legal_api
python3 dev/scripts/simple_legal_api.py &
```

#### 内存使用过高
**可能原因**:
- 向量数据加载过多
- 内存泄漏
- 并发请求过多

**解决方案**:
```bash
# 检查内存使用
docker stats

# 重启相关容器
docker restart athena_qdrant_legal
docker restart athena_redis_legal

# 调整容器内存限制
docker-compose -f infrastructure/docker/compose/legal-simple.yml up -d --force-recreate
```

### 3. 数据问题处理

#### 数据完整性检查
```bash
# 检查SQLite数据
sqlite3 data/legal_migrated.db "
SELECT COUNT(*) FROM legal_clauses;
SELECT COUNT(*) FROM vector_embeddings_1024 WHERE is_real_embedding = 1;
"

# 检查向量维度
python3 -c "
import sqlite3, numpy as np
conn = sqlite3.connect('data/legal_migrated.db')
cursor = conn.cursor()
cursor.execute('SELECT vector_data FROM vector_embeddings_1024 LIMIT 1')
row = cursor.fetchone()
if row:
    vector = np.frombuffer(row[0], dtype=np.float32)
    print(f'向量维度: {len(vector)}')
conn.close()
"
```

#### 数据恢复
```bash
# 从备份恢复
cp backups/legal_migrated_backup.db data/legal_migrated.db

# 重新索引向量
python3 dev/scripts/vector_migration_new.py
```

---

## 📈 性能优化

### 1. 搜索性能优化
- **向量索引**: 使用FAISS加速向量搜索
- **缓存策略**: L1内存缓存 + L2Redis缓存
- **批量处理**: 批量向量化处理
- **并行搜索**: 多集合并行搜索

### 2. 数据库优化
- **索引优化**: 关键字段建立索引
- **查询优化**: SQL查询语句优化
- **连接池**: 数据库连接池管理
- **分区表**: 大表分区处理

### 3. 缓存优化
- **智能预热**: 热点数据预加载
- **LRU淘汰**: 最近最少使用算法
- **数据压缩**: 大数据压缩存储
- **分布式缓存**: Redis集群部署

---

## 🔧 维护操作

### 日常维护
```bash
# 每日检查脚本
#!/bin/bash
echo "=== 系统健康检查 $(date) ==="

# 检查容器状态
echo "1. 容器状态:"
docker ps | grep legal

# 检查API健康
echo "2. API健康状态:"
curl -s http://localhost:8001/health | jq .

# 检查磁盘使用
echo "3. 磁盘使用:"
df -h

# 检查内存使用
echo "4. 内存使用:"
free -h

echo "=== 检查完成 ==="
```

### 定期维护
```bash
# 每周维护脚本
#!/bin/bash

# 清理旧日志
find logs/ -name "*.log" -mtime +7 -delete

# 数据库优化
docker exec athena_postgres_legal psql -U legal_user -d legal_db -c "VACUUM ANALYZE;"

# 清理Redis过期数据
docker exec athena_redis_legal redis-cli --scan --pattern "temp:*" | xargs redis-cli del

# 重启服务（可选）
# docker-compose -f infrastructure/docker/compose/legal-simple.yml restart
```

### 备份策略
```bash
# 数据备份脚本
#!/bin/bash
BACKUP_DIR="/Users/xujian/Athena工作平台/backups/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# 备份SQLite数据库
cp data/legal_migrated.db $BACKUP_DIR/

# 备份配置文件
cp -r infrastructure/docker/ $BACKUP_DIR/
cp -r dev/scripts/ $BACKUP_DIR/
cp .env.legal $BACKUP_DIR/

echo "备份完成: $BACKUP_DIR"
```

---

## 📞 支持联系

### 技术支持
- **系统架构师**: 负责系统架构优化和重大问题处理
- **运维工程师**: 负责日常运维和故障处理
- **开发团队**: 负责功能开发和bug修复

### 应急联系
- **紧急故障**: 立即联系系统架构师
- **性能问题**: 联系运维工程师
- **功能问题**: 联系开发团队

### 文档更新
- 本手册每月更新一次
- 重大变更后及时更新
- 版本变更记录在文档末尾

---

## 📝 版本历史

| 版本 | 日期 | 更新内容 | 作者 |
|------|------|----------|------|
| 1.0.0 | 2025-12-20 | 初始版本，包含完整运维手册 | Athena AI |

---

*本文档最后更新时间: 2025-12-20*