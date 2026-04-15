# 🚀 Athena记忆模块 - 生产环境部署指南

## 📋 目录

1. [概述](#概述)
2. [模拟数据识别](#模拟数据识别)
3. [快速开始](#快速开始)
4. [详细配置](#详细配置)
5. [部署步骤](#部署步骤)
6. [验证部署](#验证部署)
7. [监控与维护](#监控与维护)
8. [故障排查](#故障排查)

---

## 概述

Athena记忆模块默认使用以下**模拟/降级行为**：

| 组件 | 默认行为 | 生产环境要求 |
|------|----------|--------------|
| **嵌入模型** | MD5哈希模拟向量 | 本地BGE-M3模型或OpenAI API |
| **数据库** | localhost硬编码 | 真实PostgreSQL实例 |
| **缓存** | 降级运行（无缓存） | Redis实例 |
| **向量搜索** | 禁用 | Qdrant实例 |

本指南将帮助你将记忆模块连接到真实的基础设施。

---

## 模拟数据识别

### 1. MD5模拟向量

**位置**: `core/memory/unified_agent_memory_system.py:1200-1230`

```python
# 当前降级行为
async def _generate_md5_embedding(self, text: str) -> List[float]:
    """MD5哈希嵌入 (fallback方案,1024维)"""
    # 使用MD5生成伪向量，不是真实的语义向量
```

**解决方案**: 安装真实嵌入模型
```bash
pip install sentence-transformers torch
```

### 2. 硬编码配置

**位置**: `core/memory/unified_agent_memory_system.py:393-428`

```python
# 当前硬编码配置
self.db_config = {
    'postgresql': {
        'host': 'localhost',  # 硬编码
        'port': 5432,
        # ...
    }
}
```

**解决方案**: 使用环境变量或配置文件

### 3. 降级运行

**位置**: `core/memory/unified_agent_memory_system.py:594-595`

```python
# Redis连接失败时降级
except Exception as e:
    logger.warning(f"⚠️ Redis连接失败: {e}，系统将降级运行不使用缓存")
    self.redis_client = None
```

---

## 快速开始

### 方法1: 使用Docker Compose（推荐）

```bash
# 1. 复制配置文件
cp config/memory/production.env .env

# 2. 编辑配置，填写真实的数据库密码
vim .env

# 3. 启动所有基础设施
docker-compose -f config/docker/docker-compose.memory.yml up -d

# 4. 等待服务启动
docker-compose -f config/docker/docker-compose.memory.yml ps

# 5. 初始化记忆系统
python scripts/memory/init_production.py --config .env
```

### 方法2: 使用现有数据库

```bash
# 1. 设置环境变量
export MEMORY_DB_HOST=your-db-host
export MEMORY_DB_PASSWORD=your-password
# ... (其他配置)

# 2. 运行初始化脚本
python scripts/memory/init_production.py
```

---

## 详细配置

### 必需配置

#### PostgreSQL配置

```bash
# 数据库连接
export MEMORY_DB_HOST=localhost          # 数据库主机
export MEMORY_DB_PORT=5432               # 数据库端口
export MEMORY_DB_NAME=athena_memory      # 数据库名称
export MEMORY_DB_USER=athena_admin       # 数据库用户
export MEMORY_DB_PASSWORD=your_password  # 数据库密码（必需）

# 连接池配置
export MEMORY_DB_POOL_MIN=5              # 最小连接数
export MEMORY_DB_POOL_MAX=20             # 最大连接数
export MEMORY_DB_TIMEOUT=60              # 查询超时（秒）
```

**数据库准备**:
```sql
-- 创建数据库
CREATE DATABASE athena_memory;

-- 创建用户
CREATE USER athena_admin WITH PASSWORD 'your_password';

-- 授权
GRANT ALL PRIVILEGES ON DATABASE athena_memory TO athena_admin;

-- 连接到数据库
\c athena_memory

-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";

-- 初始化表结构（将自动执行）
-- \i infrastructure/database/init/001-init-schema.sql
```

### 推荐配置

#### Redis缓存

```bash
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_DB=0
export REDIS_PASSWORD=your_redis_password  # 可选但强烈推荐

# 缓存TTL（秒）
export REDIS_TTL_AGENT_STATS=300      # 智能体统计: 5分钟
export REDIS_TTL_SEARCH_RESULTS=60    # 搜索结果: 1分钟
export REDIS_TTL_MEMORY_DATA=180      # 记忆数据: 3分钟
export REDIS_TTL_HOT_MEMORY=600       # 热记忆: 10分钟
```

#### Qdrant向量数据库

```bash
export QDRANT_HOST=localhost
export QDRANT_PORT=6333
export QDRANT_API_KEY=your_api_key    # 如果需要认证

# 集合配置
export QDRANT_COLLECTION_MAIN=athena_memories
```

### 可选配置

#### 嵌入模型

```bash
# 启用真实嵌入模型（推荐）
export ENABLE_REAL_EMBEDDINGS=true

# 本地BGE-M3模型（推荐，免费）
# 自动下载，或指定本地路径
export BGE_M3_MODEL_PATH=/opt/models/BAAI/bge-m3

# 或使用OpenAI API（需要付费）
export OPENAI_API_KEY=your_openai_api_key
export OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

**安装本地模型**:
```bash
pip install sentence-transformers torch

# 首次运行会自动下载模型（约2GB）
# 或预先下载到指定路径
```

---

## 部署步骤

### 步骤1: 准备配置文件

```bash
# 复制模板
cp config/memory/production.env .env.production

# 编辑配置
vim .env.production
```

**必须修改的配置**:
```bash
# 数据库密码（必需）
MEMORY_DB_PASSWORD=your_secure_password_here

# Redis密码（推荐）
REDIS_PASSWORD=your_redis_password_here

# OpenAI API密钥（如果使用）
OPENAI_API_KEY=your_openai_api_key_here
```

### 步骤2: 启动基础设施

**使用Docker Compose**:
```bash
# 启动所有服务
docker-compose -f config/docker/docker-compose.memory.yml up -d

# 查看状态
docker-compose -f config/docker/docker-compose.memory.yml ps

# 查看日志
docker-compose -f config/docker/docker-compose.memory.yml logs -f
```

**使用现有服务**:
- 确保PostgreSQL、Redis、Qdrant已运行
- 跳过此步骤

### 步骤3: 加载配置

```bash
# 加载环境变量
source .env.production

# 验证配置
python -c "from core.memory.config import load_production_config; config = load_production_config(); config.print_summary()"
```

### 步骤4: 初始化记忆系统

```bash
# 完整初始化（验证配置 + 初始化系统 + 测试）
python scripts/memory/init_production.py --config .env.production

# 仅验证配置
python scripts/memory/init_production.py --config .env.production --validate-only
```

### 步骤5: 在应用中使用

```python
from core.memory.config import load_production_config
from core.memory.unified_agent_memory_system import UnifiedAgentMemorySystem
import asyncio

async def main():
    # 加载生产配置
    config = load_production_config('.env.production')

    # 创建记忆系统
    system = UnifiedAgentMemorySystem()
    system.db_config = config.to_db_config()

    # 初始化
    await system.initialize()

    # 使用记忆系统
    memory_id = await system.store_memory(
        agent_id="athena_wisdom",
        agent_type=AgentType.ATHENA,
        content="用户询问了关于记忆模块部署的问题",
        memory_type=MemoryType.CONVERSATION,
        importance=0.8
    )

    print(f"记忆已存储: {memory_id}")

    # 清理
    await system.close()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 验证部署

### 1. 检查服务状态

```bash
# PostgreSQL
docker exec athena_memory_postgres pg_isready -U athena_admin

# Redis
docker exec athena_memory_redis redis-cli ping

# Qdrant
curl http://localhost:6333/health
```

### 2. 检查数据库表

```bash
# 连接到PostgreSQL
docker exec -it athena_memory_postgres psql -U athena_admin -d athena_memory

# 检查表
\dt

# 检查扩展
\dx

# 检查记录
SELECT COUNT(*) FROM memories;
```

### 3. 运行测试

```bash
# 运行记忆模块测试
pytest tests/core/memory/test_unified_memory_system.py -v

# 运行长期记忆测试
pytest tests/core/memory/test_long_term_memory.py -v
```

---

## 监控与维护

### 日志

```bash
# 查看应用日志
tail -f init_production.log

# 查看Docker日志
docker-compose -f config/docker/docker-compose.memory.yml logs -f postgres
docker-compose -f config/docker/docker-compose.memory.yml logs -f redis
docker-compose -f config/docker/docker-compose.memory.yml logs -f qdrant
```

### 备份

#### PostgreSQL备份

```bash
# 创建备份
docker exec athena_memory_postgres pg_dump \
    -U athena_admin \
    -d athena_memory \
    > backup_$(date +%Y%m%d_%H%M%S).sql

# 恢复备份
docker exec -i athena_memory_postgres psql \
    -U athena_admin \
    -d athena_memory \
    < backup_20240124_120000.sql
```

#### Redis备份

```bash
# 触发RDB快照
docker exec athena_memory_redis redis-cli BGSAVE

# 复制RDB文件
docker cp athena_memory_redis:/data/dump.rdb ./backup/
```

### 清理过期记忆

```python
# 定期清理任务
from core.memory.unified_agent_memory_system import UnifiedAgentMemorySystem

async def cleanup_expired():
    system = UnifiedAgentMemorySystem()
    await system.initialize()

    # 清理过期记忆
    deleted = await system.cleanup_expired_memories()
    print(f"已清理 {deleted} 条过期记忆")

    await system.close()
```

---

## 故障排查

### 问题1: PostgreSQL连接失败

**症状**: `connection refused` 或 `password authentication failed`

**解决方案**:
```bash
# 1. 检查PostgreSQL是否运行
docker ps | grep postgres

# 2. 检查密码
docker exec athena_memory_postgres psql -U athena_admin -d postgres -c "ALTER USER athena_admin WITH PASSWORD 'new_password';"

# 3. 检查网络
docker network inspect athena_memory_network

# 4. 检查防火墙
sudo ufw allow 5432
```

### 问题2: Redis连接失败

**症状**: `Redis连接失败: ...`

**解决方案**:
```bash
# 1. 检查Redis是否运行
docker ps | grep redis

# 2. 检查密码
docker exec athena_memory_redis redis-cli -a your_password ping

# 3. 系统会降级运行，不是致命错误
```

### 问题3: 嵌入模型未加载

**症状**: `使用MD5临时方案`

**解决方案**:
```bash
# 1. 安装依赖
pip install sentence-transformers torch

# 2. 设置环境变量
export ENABLE_REAL_EMBEDDINGS=true

# 3. 预下载模型（可选）
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-m3')"
```

### 问题4: Qdrant连接失败

**症状**: `Qdrant客户端未初始化`

**解决方案**:
```bash
# 1. 检查Qdrant是否运行
docker ps | grep qdrant

# 2. 检查健康状态
curl http://localhost:6333/health

# 3. 向量搜索功能将不可用，但不影响基本功能
```

---

## 生产环境最佳实践

### 1. 安全性

```bash
# 使用强密码
export MEMORY_DB_PASSWORD="$(openssl rand -base64 32)"

# 限制网络访问
# 在docker-compose.yml中删除不必要的端口映射

# 使用TLS/SSL
# 在生产环境中配置PostgreSQL和Redis的TLS
```

### 2. 性能优化

```bash
# 调整连接池大小
export MEMORY_DB_POOL_MAX=50  # 根据负载调整

# 启用Redis持久化
# 在docker-compose.yml中配置appendonly yes

# 使用CDN加速模型下载
# 预先下载BGE-M3模型到本地
```

### 3. 高可用性

```bash
# PostgreSQL主从复制
# Redis哨兵模式
# Qdrant集群模式

# 配置健康检查
docker-compose -f config/docker/docker-compose.memory.yml \
    -f config/docker/docker-compose.memory.ha.yml \
    up -d
```

### 4. 监控告警

```python
# 集成Prometheus
from prometheus_client import Counter, Histogram

memory_operations = Counter('memory_operations_total', 'Total memory operations')
memory_errors = Counter('memory_errors_total', 'Total memory errors')
memory_latency = Histogram('memory_latency_seconds', 'Memory operation latency')
```

---

## 总结

通过本指南，你应该能够：

✅ 识别并移除所有模拟数据和降级行为
✅ 连接到真实的PostgreSQL、Redis、Qdrant实例
✅ 使用真实的BGE-M3嵌入模型
✅ 部署一个完全可用的生产级记忆系统
✅ 监控和维护记忆系统

**下一步**:
1. 配置定期备份
2. 设置监控告警
3. 编写运维文档
4. 制定灾难恢复计划

---

**文档版本**: 1.0.0
**更新日期**: 2026-01-24
**作者**: Athena平台团队
