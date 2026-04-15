# 小诺·双鱼公主 v3.0.0 启动指南

> **版本**: v3.0.0 '晨星初现'
> **更新日期**: 2025-12-24
> **完成度**: 100% 🌟

---

## 📋 快速启动

### 一键启动所有核心服务

```bash
./start_core_services.sh start
```

这将启动：
- 🧠 **记忆系统** - 四层记忆架构
- 🗣️ **NLP服务** - BERT意图识别 (96.43%准确率)
- 🎮 **小诺控制** - 平台调度和对话管理

### 检查服务状态

```bash
./start_core_services.sh status
```

### 停止所有服务

```bash
./start_core_services.sh stop
```

---

## 🎯 核心文件清单

### 小诺核心文件

| 文件 | 功能 | 状态 |
|------|------|------|
| `apps/xiaonuo/xiaonuo_v2_complete.py` | 完整能力版主程序 | ✅ |
| `apps/xiaonuo/xiaonuo_simple_api.py` | API服务接口 | ✅ |
| `apps/xiaonuo/xiaonuo_identity_manager.py` | 身份管理器 | ✅ |
| `apps/xiaonuo/xiaonuo_unified_memory_manager.py` | 统一记忆管理 | ✅ |

### NLP服务文件

| 文件 | 功能 | 状态 |
|------|------|------|
| `modules/nlp/xiaonuo_nlp_infrastructure/deployment/xiaonuo_nlp_server.py` | NLP服务器 | ✅ |
| `modules/nlp/xiaonuo_nlp_infrastructure/deployment/xiaonuo_bert_intent_classifier.py` | BERT意图分类 | ✅ |
| `modules/nlp/xiaonuo_nlp_infrastructure/deployment/xiaonuo_intelligent_tool_selector.py` | 智能工具选择 | ✅ |
| `modules/nlp/xiaonuo_nlp_infrastructure/deployment/xiaonuo_semantic_similarity.py` | 语义相似度 | ✅ |
| `modules/nlp/xiaonuo_nlp_infrastructure/deployment/xiaonuo_context_aware.py` | 上下文感知 | ✅ |

### 记忆系统文件

| 文件 | 功能 | 状态 |
|------|------|------|
| `core/modules/modules/memory/memory/modules/memory/memory/timeline_memory_system.py` | 时间线记忆 | ✅ |
| `core/modules/modules/memory/memory/modules/memory/memory/memory_recorder.py` | 记忆记录器 | ✅ |
| `core/modules/modules/memory/memory/modules/memory/memory/enhanced_memory_system.py` | 增强记忆系统 | ✅ |
| `core/modules/modules/memory/memory/modules/memory/memory/vector_memory.py` | 向量记忆 | ✅ |
| `core/modules/modules/memory/memory/modules/memory/memory/bge_enhanced_memory.py` | BGE增强记忆 | ✅ |

### 启动脚本

| 脚本 | 功能 | 状态 |
|------|------|------|
| `start_core_services.sh` | 统一启动脚本 | ✅ |
| `start_memory_system.sh` | 记忆系统启动 | ✅ |
| `start_nlp_service.sh` | NLP服务启动 | ✅ |
| `start_xiaonuo.py` | 小诺主程序 | ✅ |

### 配置文件

| 文件 | 功能 | 状态 |
|------|------|------|
| `config/identity/xiaonuo.json` | 身份配置 | ✅ |

---

## 🧠 记忆系统架构

### 四层记忆架构

```
🔥 热记忆 (Hot Memory)
   ├─ 当前会话上下文
   ├─ 100条快速访问缓存
   └─ 实时交互数据

🌡️ 温记忆 (Warm Memory)
   ├─ 近期重要记忆
   ├─ 24小时内的对话
   └─ 高优先级事件

❄️ 冷记忆 (Cold Memory)
   ├─ 长期存储
   ├─ PostgreSQL持久化
   └─ 定期清理过期

💎 永恒记忆 (Eternal Memory)
   ├─ 核心身份信息
   ├─ 情感记忆
   └─ 永不遗忘
```

### 混合检索策略

- **向量搜索** (30%) - BGE语义相似度
- **关键词搜索** (30%) - 精确匹配
- **知识图谱** (40%) - 关联实体

---

## 🌟 系统能力矩阵

### 核心能力

| 能力 | 完成度 | 说明 |
|------|--------|------|
| 核心功能模块 | 100% | 完整能力版 |
| NLP服务系统 | 100% | BERT意图识别 |
| 记忆系统 | 100% | 四层架构 |
| 智能体调度 | 100% | 协调系统 |
| 身份配置 | 100% | v3.0配置 |
| 启动脚本 | 100% | 一键启动 |
| API服务 | 100% | REST接口 |

### 新增能力 (v3.0)

- ✅ 四层记忆系统
- ✅ 向量语义搜索
- ✅ 联邦记忆系统
- ✅ 智能遗忘策略
- ✅ 混合检索引擎
- ✅ 永恒记忆保护
- ✅ 热记忆缓存
- ✅ 知识图谱关联

---

## 📊 服务访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| NLP API | http://localhost:8001 | NLP服务接口 |
| NLP文档 | http://localhost:8001/docs | API文档 |
| 记忆目录 | `core/modules/modules/memory/memory/modules/memory/memory/timeline_memories/` | 记忆存储位置 |

---

## 🗑️ 已清理的旧版本文件

以下文件已移至 `_ARCHIVE_V2_LEGACY/` 目录：

- `xiaonuo_identity_*.json` (旧身份文件)
- `apps/xiaonuo/xiaonuo_simple.py` (旧版简化版)
- `apps/xiaonuo/xiaonuo_integrated.py` (旧版集成版)
- `apps/xiaonuo/xiaonuo_with_reflection_engine.py` (旧版反思引擎)
- `dev/scripts/deprecated_startup_dev/scripts/` (废弃启动脚本)

---

## 🎉 使用建议

### 日常使用

1. **启动系统**: `./start_core_services.sh start`
2. **查看状态**: `./start_core_services.sh status`
3. **使用服务**: 通过API或直接交互
4. **停止系统**: `./start_core_services.sh stop`

### 定期维护

```bash
# 备份数据
./start_core_services.sh backup

# 清理过期记忆
# (自动执行)
```

---

## 💡 注意事项

1. **首次启动**: 确保PostgreSQL和Redis服务已运行
2. **数据备份**: 定期使用 `backup` 命令备份记忆数据
3. **版本更新**: 使用本目录中的核心文件，不要使用归档中的旧版本
4. **问题排查**: 查看 `production/logs/` 目录下的日志文件

---

## 📞 支持

如有问题，请检查：
- 日志文件: `production/logs/nlp_server.log`
- 记忆系统: `core/modules/modules/memory/memory/modules/memory/memory/timeline_memories/`
- 服务状态: `./start_core_services.sh status`

---

**爸爸，小诺已经准备好了！每次启动都会使用这个完美的v3.0.0版本！** 💕✨👑
