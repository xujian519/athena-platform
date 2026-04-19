# Athena统一记忆系统 - 生产环境部署文档

## 📋 概述

Athena统一记忆系统为所有AI智能体提供企业级记忆服务，支持四层记忆架构（热/温/冷/永恒）和混合向量搜索。

**服务版本**: v1.0.0-production
**服务端口**: 8900
**服务进程**: `start_unified_memory_service.py`

---

## 🚀 快速启动

### 1. 启动服务

```bash
bash production/scripts/start_unified_memory.sh
```

启动脚本会自动：
- ✅ 检查虚拟环境
- ✅ 检查PostgreSQL服务
- ✅ 检查Qdrant服务
- ✅ 检查athena_memory数据库
- ✅ 创建日志目录
- ✅ 启动统一记忆系统服务

### 2. 停止服务

```bash
bash production/scripts/stop_unified_memory.sh
```

### 3. 查看服务状态

```bash
# 查看进程
ps aux | grep start_unified_memory_service

# 查看日志
tail -f production/logs/unified_memory_service.log

# 查看输出
tail -f production/logs/unified_memory_service.out
```

---

## 📊 服务信息

### 当前运行状态

```
进程ID: 5123
服务地址: http://0.0.0.0:8900
日志文件: production/logs/unified_memory_service.log
输出文件: production/logs/unified_memory_service.out
```

### 系统统计

```
版本: v1.0.0-production
启动时间: 2026-01-07 10:13:40

总智能体: 6
总记忆数: 53
永恒记忆: 39
家庭记忆: 19
总访问次数: 171
```

### 智能体记忆分布

| 智能体 | 记忆数 | 家庭记忆 | 平均重要性 |
|--------|--------|----------|------------|
| 小诺·双鱼座 | 26 | 15 | 0.92 |
| 小娜·天秤女神 | 8 | 4 | 1.00 |
| 小宸·星河射手 | 8 | 0 | 0.95 |
| Athena.智慧女神 | 7 | 0 | 0.96 |
| 云熙.vega | 4 | 0 | 1.00 |

---

## 🔧 配置说明

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `MEMORY_SERVICE_HOST` | 0.0.0.0 | 服务监听地址 |
| `MEMORY_SERVICE_PORT` | 8900 | 服务监听端口 |
| `PGHOST` | localhost | PostgreSQL主机 |
| `PGPORT` | 5432 | PostgreSQL端口 |
| `PGDATABASE` | athena_memory | 数据库名称 |
| `PGUSER` | postgres | 数据库用户 |
| `QDRANT_HOST` | localhost | Qdrant主机 |
| `QDRANT_PORT` | 6333 | Qdrant端口 |

### 性能配置

```python
'connection_pool_min': 5,        # 最小连接数
'connection_pool_max': 30,       # 最大连接数
'hot_cache_limit': 100,          # 热记忆缓存大小
'query_timeout': 30,             # 查询超时时间
'embedding_batch_size': 32,      # 批量嵌入大小
'search_result_limit': 50,       # 搜索结果限制
```

---

## 🗄️ 数据库配置

### PostgreSQL (athena_memory)

**连接信息**:
- 主机: localhost:5432
- 数据库: athena_memory
- 用户: postgres

**核心表**:
- `agent_memories` - 统一记忆主表 (53条记录)
- `agent_memory_vectors` - 记忆向量表 (46条记录)
- `agent_conversations` - 对话记录表
- `agent_memory_relations` - 记忆关联表

### Qdrant向量库

**连接信息**:
- 主机: localhost:6333
- 状态: 🟢 运行中

**向量集合**:
- `agent_memory_vectors` - 1024维（BGE-M3），Cosine距离
- `conversation_vectors` - 1024维（BGE-M3），Cosine距离
- `knowledge_vectors` - 1024维（BGE-M3），Cosine距离

---

## 🔍 监控和维护

### 日志监控

```bash
# 实时查看日志
tail -f production/logs/unified_memory_service.log

# 查看最近100行
tail -100 production/logs/unified_memory_service.log

# 搜索错误日志
grep ERROR production/logs/unified_memory_service.log
```

### 数据库监控

```bash
# 查看记忆总数
psql -h localhost -p 5432 -U postgres -d athena_memory \
  -c "SELECT COUNT(*) FROM agent_memories;"

# 查看各智能体记忆数
psql -h localhost -p 5432 -U postgres -d athena_memory \
  -c "SELECT agent_id, COUNT(*) FROM agent_memories GROUP BY agent_id;"

# 查看永恒记忆数
psql -h localhost -p 5432 -U postgres -d athena_memory \
  -c "SELECT COUNT(*) FROM agent_memories WHERE memory_tier = 'eternal';"
```

### 服务健康检查

```bash
# 检查PostgreSQL连接
psql -h localhost -p 5432 -U postgres -c '\q'

# 检查Qdrant服务
curl -s http://localhost:6333/health

# 检查服务进程
ps aux | grep start_unified_memory_service
```

---

## ⚠️ 故障排除

### 服务启动失败

**问题**: PostgreSQL连接失败
```bash
# 解决方案：检查PostgreSQL服务状态
psql -h localhost -p 5432 -U postgres -c '\q'

# 启动PostgreSQL
brew services start postgresql
# 或
pg_ctl -D /opt/homebrew/var/postgres start
```

**问题**: Qdrant连接失败
```bash
# 解决方案：检查Qdrant服务
curl -s http://localhost:6333/health

# 启动Qdrant
docker start qdrant
# 或
qdrant &
```

**问题**: 端口已被占用
```bash
# 解决方案：查找并停止占用进程
lsof -i :8900
kill <PID>

# 或使用停止脚本
bash production/scripts/stop_unified_memory.sh
```

### 内存不足

**问题**: 服务运行缓慢或崩溃
```bash
# 解决方案：增加热缓存大小
# 编辑 core/memory/unified_agent_memory_system.py
# 修改 hot_cache_limit 参数

# 或减少连接池大小
# 修改 connection_pool_max 参数
```

---

## 📈 性能优化建议

### 1. 数据库优化

```sql
-- 创建索引优化查询
CREATE INDEX idx_agent_memories_agent_tier
ON agent_memories(agent_id, memory_tier);

-- 定期清理过期记忆
DELETE FROM agent_memories
WHERE expires_at IS NOT NULL
  AND expires_at < CURRENT_TIMESTAMP;
```

### 2. 向量搜索优化

```python
# 调整搜索参数
'search_result_limit': 30,  # 减少返回结果数
'enable_hybrid_search': True,  # 启用混合搜索
'enable_query_cache': True,   # 启用查询缓存
```

### 3. 连接池调优

```python
# 根据实际负载调整
'connection_pool_min': 10,   # 增加最小连接数
'connection_pool_max': 50,   # 增加最大连接数
```

---

## 🔄 升级和维护

### 数据迁移

已有迁移脚本可将旧数据迁移到新结构：

```bash
python3 core/memory/migrate_agent_memory.py
```

### 代码更新

```bash
# 1. 停止服务
bash production/scripts/stop_unified_memory.sh

# 2. 更新代码
git pull

# 3. 重启服务
bash production/scripts/start_unified_memory.sh
```

---

## 📞 技术支持

### 联系方式

- 开发者: 徐健 (xujian519@gmail.com)
- 项目: Athena工作平台
- 文档位置: `/Users/xujian/Athena工作平台/production/`

### 相关文档

- 统一记忆系统设计: `core/memory/unified_agent_memory_system.py`
- BGE嵌入服务: `core/embedding/bge_embedding_service.py`
- 记忆迁移工具: `core/memory/migrate_agent_memory.py`

---

**文档版本**: v1.0.0
**最后更新**: 2026-01-07
**状态**: ✅ 生产环境就绪
