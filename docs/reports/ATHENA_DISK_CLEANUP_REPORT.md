# Athena 工作平台磁盘清理报告

> **生成时间**: 2026-02-07
> **项目总大小**: 22GB
> **预期节省空间**: 8-10GB (约 35-45%)

---

## 📊 空间占用分析

### 总体分布

| 类别 | 大小 | 占比 |
|------|------|------|
| 模型文件 | ~13GB | 59% |
| 虚拟环境 | ~1.4GB | 6% |
| 数据库 | ~3.5GB | 16% |
| 日志文件 | ~800MB | 4% |
| 代码与配置 | ~3GB | 14% |
| 其他 | ~300MB | 1% |

---

## 🔴 高优先级清理项

### 1. 虚拟环境目录 (1.4GB)

**问题**: 项目中包含 13 个虚拟环境，占用大量空间且应该被 .gitignore 忽略

| 虚拟环境 | 大小 | 建议 |
|---------|------|------|
| `athena_env` | 737MB | **移出项目** - 主虚拟环境 |
| `storage-system/venv` | 141MB | **删除** - 重复虚拟环境 |
| `storage-system/athena_env` | 107MB | **删除** - 重复虚拟环境 |
| `yunpat_agent/venv` | 77MB | **删除** - 可用主虚拟环境 |
| `gaode-mcp-server/venv` | 74MB | **保留** - MCP服务独立环境 |
| `multimodal/venv` | 65MB | **删除** - 可用主虚拟环境 |
| `knowledge-graph-service/venv` | 50MB | **删除** - 可用主虚拟环境 |
| `athena_env_py311` | 45MB | **评估后删除** - Python 3.11环境 |
| `patent_downloader/.venv` | 44MB | **保留** - MCP服务独立环境 |
| `xiaonuo-calendar-assistant/venv` | 42MB | **保留** - MCP服务独立环境 |
| `dev/scripts/venv` | 29MB | **删除** - 脚本临时环境 |
| `xiaonuo/venv` | 18MB | **删除** - 可用主虚拟环境 |
| `deploy/venv` | 10MB | **删除** - 脚本临时环境 |

**操作建议**:
```bash
# 1. 将主虚拟环境移到项目外
mv athena_env ~/athena_venv

# 2. 删除可删除的虚拟环境
rm -rf modules/storage/storage-system/venv
rm -rf modules/storage/storage-system/athena_env
rm -rf services/yunpat_agent/venv
rm -rf services/multimodal/venv
rm -rf services/knowledge-graph-service/venv
rm -rf dev/scripts/venv
rm -rf apps/xiaonuo/venv
rm -rf infrastructure/deploy/venv

# 3. 更新 .gitignore
echo "athena_env/" >> .gitignore
echo "athena_env_py311/" >> .gitignore
echo "**/venv/" >> .gitignore
echo "**/.venv/" >> .gitignore
```

**预期节省**: ~800MB

---

### 2. 重复模型文件 (约 2-3GB)

#### 2.1 转换模型目录 (5.9GB)

| 模型 | 大小 | 用途 | 建议 |
|------|------|------|------|
| `BAAI/bge-m3/` | 2.1GB | 向量嵌入 | **保留** - 核心模型 |
| `hfl/chinese-roberta-wwm-ext-large/` | 1.2GB | 中文NLP | **评估** - 如不常用可删除 |
| `DeepSeek-R1/` | ~2.6GB | 大语言模型 | **删除** - 临时转换文件 |

**操作建议**:
```bash
# 删除 DeepSeek 临时转换文件
rm -rf models/converted/DeepSeek-R1/._____temp

# 评估 chinese-roberta 是否还在使用
# 如果不再使用，删除以节省 1.2GB
# rm -rf models/converted/hfl
```

#### 2.2 意图分类器模型重复 (约 500MB)

在多个位置存在相同的模型文件：
- `core/agent/models/enhanced_intent_classifier/`
- `core/nlp/models/enhanced_intent_classifier/`
- `production/core/agent/models/enhanced_intent_classifier/`
- `production/core/nlp/models/enhanced_intent_classifier/`

**操作建议**:
```bash
# 保留最新版本，删除旧版本
# 在每个目录中，保留 latest_enhanced_model.pkl
# 删除带时间戳的旧版本
find core -name "*enhanced_intent_classifier*.pkl" ! -name "latest_*.pkl" -delete
find production -name "*enhanced_intent_classifier*.pkl" ! -name "latest_*.pkl" -delete
```

---

### 3. 日志文件清理 (~800MB)

#### 大型日志文件

| 日志文件 | 大小 | 建议 |
|---------|------|------|
| `logs/xiaonuo_gateway.log` | 497MB | **归档并清理** |
| `logs/prompt-system-api.stderr.log` | 56MB | **归档** |
| `production/logs/unified_memory.stderr.log` | 54MB | **归档** |
| `production/logs/unified_memory_service.log` | 46MB | **归档** |

**操作建议**:
```bash
# 1. 创建日志归档目录
mkdir -p logs/archive/2026-01
mkdir -p production/logs/archive/2026-01

# 2. 移动旧日志到归档
mv logs/xiaonuo_gateway.log logs/archive/2026-01/
mv logs/prompt-system-api.stderr.log logs/archive/2026-01/
mv production/logs/unified_memory*.log production/logs/archive/2026-01/

# 3. 配置日志轮转 (在项目中添加)
# 见下方 "日志轮转配置"
```

**预期节省**: 400-500MB (归档后可压缩)

---

## 🟡 中优先级清理项

### 4. Python 缓存文件 (~23MB)

项目中有 186 个 `__pycache__` 目录，总计约 23MB

**操作建议**:
```bash
# 开发环境保留（加速加载）
# 生产环境可以删除
find production -type d -name "__pycache__" -exec rm -rf {} +
```

---

### 5. 重复数据库文件 (~100MB)

| 数据库 | 位置 | 建议 |
|--------|------|------|
| `yunpat.db` | `services/yunpat_agent/yunpat.db` | **保留** |
| `yunpat.db` | `services/yunpat_agent/data/yunpat.db` | **删除** (重复) |
| `grafana.db` | 多个位置 | **保留主版本，删除备份** |

**操作建议**:
```bash
# 删除重复的 yunpat.db
rm services/yunpat_agent/data/yunpat.db

# 删除备份目录中的 grafana.db
rm -rf backups/deployments/*/config/docker/data/grafana/
```

---

### 6. 备份目录 (~25MB)

| 目录 | 大小 | 建议 |
|------|------|------|
| `backups/` | 17MB | **压缩归档后删除** |
| `backup/` | 6.6MB | **压缩归档后删除** |
| `deploy/db` | 8KB | **保留** |

**操作建议**:
```bash
# 压缩备份目录
tar -czf backups_$(date +%Y%m%d).tar.gz backups/ backup/

# 验证压缩包完整性后删除原始目录
# rm -rf backups/ backup/
```

---

## 🟢 低优先级清理项

### 7. 临时文件

```bash
# 删除临时文件
find . -name "*.tmp" -delete
find . -name ".DS_Store" -delete
find . -name "*.pyc" -delete
find . -name "*.pyo" -delete
```

---

## 🛠️ 日志轮转配置

为防止日志文件无限增长，建议配置 logrotate：

```bash
# 创建 /usr/local/etc/logrotate/athena.conf
/Users/xujian/Athena工作平台/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 xujian staff
    postrotate
        # 发送信号让应用重新打开日志文件
        kill -USR1 $(cat /var/run/xiaonuo_gateway.pid 2>/dev/null) 2>/dev/null || true
    endscript
}

/Users/xujian/Athena工作平台/production/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 xujian staff
}
```

---

## 📋 清理执行清单

### ✅ 第一步：备份重要数据
```bash
# 在执行清理前，确保备份以下重要数据
# 1. 数据库文件
tar -czf db_backup_$(date +%Y%m%d).tar.gz data/

# 2. 配置文件
tar -czf config_backup_$(date +%Y%m%d).tar.gz config/
```

### ✅ 第二步：执行清理（按顺序）

```bash
# 1. 虚拟环境清理
mv athena_env ~/athena_venv
rm -rf modules/storage/storage-system/venv
rm -rf modules/storage/storage-system/athena_env
rm -rf services/yunpat_agent/venv
rm -rf services/multimodal/venv
rm -rf services/knowledge-graph-service/venv
rm -rf dev/scripts/venv
rm -rf apps/xiaonuo/venv
rm -rf infrastructure/deploy/venv

# 2. 日志归档
mkdir -p logs/archive/2026-01 production/logs/archive/2026-01
mv logs/xiaonuo_gateway.log logs/archive/2026-01/
mv logs/prompt-system-api.stderr.log logs/archive/2026-01/
mv production/logs/unified_memory*.log production/logs/archive/2026-01/

# 3. 旧模型版本清理
find core -name "*enhanced_intent_classifier*.pkl" ! -name "latest_*.pkl" -delete
find production -name "*enhanced_intent_classifier*.pkl" ! -name "latest_*.pkl" -delete

# 4. 临时转换文件清理
rm -rf models/converted/DeepSeek-R1/._____temp

# 5. Python缓存清理（生产环境）
find production -type d -name "__pycache__" -exec rm -rf {} +

# 6. 重复数据库清理
rm services/yunpat_agent/data/yunpat.db

# 7. 临时文件清理
find . -name "*.tmp" -delete
find . -name ".DS_Store" -delete
```

### ✅ 第三步：验证清理结果

```bash
# 检查项目大小
du -sh /Users/xujian/Athena工作平台

# 检查核心功能是否正常
pytest tests/ -v
```

---

## 📊 预期清理效果

| 清理项 | 节省空间 | 风险等级 |
|--------|---------|---------|
| 虚拟环境清理 | ~800MB | 低 |
| 日志归档 | ~500MB | 低 |
| 旧模型版本 | ~300MB | 中 |
| 临时转换文件 | ~2GB | 低 |
| Python缓存 | ~23MB | 低 |
| 重复数据库 | ~100MB | 中 |
| **总计** | **~3.7GB** | - |

---

## ⚠️ 注意事项

1. **不要删除的文件**:
   - `data/neo4j/` - Neo4j 数据库 (2.4GB)
   - `data/qdrant/` - Qdrant 向量数据库 (682MB)
   - `models/deepseek-ocr-2/` - OCR 模型 (6.3GB)
   - `models/converted/BAAI/bge-m3/` - 向量嵌入模型 (2.1GB)

2. **Git 仓库大小** (73MB):
   - 考虑使用 `git gc` 压缩仓库
   - 如果有大文件被误提交，使用 BFG Repo-Cleaner 清理

3. **长期维护建议**:
   - 设置定期日志轮转
   - 建立模型版本管理策略
   - 定期执行磁盘空间检查

---

## 🔄 定期维护计划

| 任务 | 频率 | 负责人 |
|------|------|--------|
| 日志归档 | 每月 | 运维 |
| 模型版本清理 | 每季度 | 开发 |
| 磁盘空间检查 | 每周 | 运维 |
| 临时文件清理 | 每月 | 开发 |

---

**报告生成**: Claude AI
**下次审查**: 2026-03-07
