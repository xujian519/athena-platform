# 动态提示词系统 & 场景规划器 - Gateway接入报告

## 📋 概述

本报告说明了动态提示词系统和场景规划器的Gateway接入情况。

## ✅ 已接入服务

### 1. 动态提示词系统API

**服务信息:**
- 服务名称: `prompt-system-api`
- 服务地址: `http://localhost:8002`
- Gateway路径前缀: `/api/prompt-system/*`

**主要端点:**

| Gateway路径 | 后端路径 | 方法 | 描述 |
|------------|---------|------|------|
| `/api/prompt-system/health` | `/api/v1/prompt-system/health` | GET | 健康检查 |
| `/api/prompt-system/scenario/identify` | `/api/v1/prompt-system/scenario/identify` | POST | 场景识别 |
| `/api/prompt-system/rules/retrieve` | `/api/v1/prompt-system/rules/retrieve` | POST | 规则检索 |
| `/api/prompt-system/capabilities/invoke` | `/api/v1/prompt-system/capabilities/invoke` | POST | 能力调用 |
| `/api/prompt-system/prompt/generate` | `/api/v1/prompt-system/prompt/generate` | POST | 提示词生成 |
| `/api/prompt-system/capabilities/list` | `/api/v1/prompt-system/capabilities/list` | GET | 能力列表 |
| `/api/prompt-system/cache/stats` | `/api/v1/prompt-system/cache/stats` | GET | 缓存统计 |
| `/api/prompt-system/cache/clear` | `/api/v1/prompt-system/cache/clear` | POST | 缓存清理 |
| `/api/prompt-system/monitoring/metrics` | `/api/v1/prompt-system/monitoring/metrics` | GET/POST | 监控指标 |
| `/api/prompt-system/monitoring/performance` | `/api/v1/prompt-system/monitoring/performance` | GET | 性能监控 |
| `/api/prompt-system/config/status` | `/api/v1/prompt-system/config/status` | GET | 配置状态 |
| `/api/prompt-system/config/reload` | `/api/v1/prompt-system/config/reload` | POST | 配置重载 |
| `/api/prompt-system/health/extended` | `/api/v1/prompt-system/health/extended` | GET | 扩展健康检查 |

**配置文件:** `gateway-unified/configs/prompt-system-service.yaml`

**启动命令:**
```bash
# 启动服务
/Users/xujian/Athena工作平台/production/scripts/start_prompt_system_api.sh

# 注册到Gateway
cd gateway-unified
python3 scripts/register_prompt_system.py
```

## 📊 场景规划器说明

### 场景规划器不是独立服务

**重要说明:** 场景规划器（Scenario Planner）**不是独立的HTTP服务**，而是一个内部Python模块，被动态提示词系统内部使用。

**模块位置:**
- `core/cognition/agentic_task_planner.py` - 智能体任务规划器
- `core/planning/adaptive_meta_planner.py` - 自适应元规划器
- `core/planning/explicit_planner.py` - 显式规划器

**访问方式:**

场景规划功能通过动态提示词系统的以下端点访问：

1. **场景识别** (`POST /api/prompt-system/scenario/identify`)
   - 识别用户输入的业务场景
   - 返回领域、任务类型、阶段等信息

2. **规则检索** (`POST /api/prompt-system/rules/retrieve`)
   - 从Neo4j检索场景规则
   - 返回处理规则和工作流步骤

3. **提示词生成** (`POST /api/prompt-system/prompt/generate`)
   - 根据场景和规则生成优化的动态提示词
   - 内部使用场景规划器进行任务分解

**工作流程:**
```
用户输入
  ↓
场景识别 (scenario/identify)
  ↓
规则检索 (rules/retrieve)
  ↓
场景规划器 (内部模块)
  ↓
提示词生成 (prompt/generate)
```

## 🏗️ 架构总结

```
┌─────────────────────────────────────────────────────────┐
│              Athena Gateway (8005)                      │
│  ┌──────────────────────────────────────────────────┐  │
│  │   统一入口 + 服务发现 + 负载均衡                   │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
         │                              │
    ┌────┴────┐                    ┌──┴──────────┐
    │         │                    │              │
┌───▼────┐ ┌─▼──────────┐    ┌────▼──────┐ ┌──▼─────────────┐
│法律世界模型│ │动态提示词系统 │    │ 主API服务  │ │  其他服务...   │
│  8020  │ │   8002    │    │   8000   │ │              │
└────────┘ └────────────┘    └───────────┘ └───────────────┘
    │             │                  │
    │             │                  │
  场景          场景规划器(内部)     智能体路由
  规则         (agentic_task     (intent_routes)
               _planner.py)
```

## 📝 使用示例

### 通过Gateway访问场景识别

```bash
curl -X POST http://localhost:8005/api/prompt-system/scenario/identify \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "我需要分析一个专利的创造性",
    "additional_context": {}
  }'
```

### 通过Gateway访问规则检索

```bash
curl -X POST http://localhost:8005/api/prompt-system/rules/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "patent",
    "task_type": "analysis",
    "phase": "invalidity"
  }'
```

### 通过Gateway生成提示词

```bash
curl -X POST http://localhost:8005/api/prompt-system/prompt/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "我需要分析一个专利的创造性",
    "context": {}
  }'
```

## ✅ 接入状态

| 服务 | Gateway接入 | 状态 | 备注 |
|------|------------|------|------|
| 法律世界模型 | ✅ | 运行中 | 端口 8020 |
| 动态提示词系统 | ✅ | 运行中 | 端口 8002 |
| 场景规划器 | N/A | 内部模块 | 通过动态提示词系统访问 |

## 📖 相关文档

- Gateway统一网关: `gateway-unified/README.md`
- 法律世界模型: `services/legal-world-model-service/README.md`
- 动态提示词系统: `core/api/prompt_system_routes.py`
- 场景规划器: `core/cognition/agentic_task_planner.py`
