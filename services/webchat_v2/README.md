# WebChat V2 Gateway

基于Moltbot/Clawdbot Gateway架构的WebChat服务。

## 架构概述

```
┌─────────────────────────────────────────────────────────────────┐
│                    用户界面层 (React前端)                       │
└─────────────────────────────────────────────────────────────────┘
                            │ WebSocket
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Gateway Server (FastAPI)                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              WebSocket Gateway (协议化消息帧)              │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ 小诺意图路由器 │ │   会话管理     │ │ 平台模块注册  │
└───────────────┘ └───────────────┘ └───────────────┘
        │
        ▼ 调用
┌─────────────────────────────────────────────────────────────────┐
│                   Athena平台能力层                                │
│  专利搜索 | 专利分析 | 知识图谱 | 向量检索 | 工具能力             │
└─────────────────────────────────────────────────────────────────┘
```

## 目录结构

```
services/webchat_v2/
├── __init__.py              # 包初始化
├── gateway/                 # Gateway模块
│   ├── __init__.py
│   ├── protocol.py          # 协议定义 (Request/Response/Event)
│   ├── session.py           # 会话管理
│   └── server.py            # Gateway服务器
├── identity/                # 身份管理模块
│   ├── __init__.py
│   └── manager.py           # 小诺身份管理器
├── modules/                 # 平台模块
│   ├── __init__.py
│   ├── registry.py          # 模块注册表
│   ├── invoker.py           # 模块调用器
│   └── router.py            # 意图路由器
├── api/                     # FastAPI应用
│   └── app.py               # 应用入口
├── config/                  # 配置
│   └── settings.py          # 配置管理
├── .env.example             # 环境变量示例
├── start.sh                 # 启动脚本
└── README.md                # 本文件
```

## 快速开始

### 1. 安装依赖

```bash
cd services/webchat_v2
pip install fastapi uvicorn[standard] websockets pydantic-settings
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件配置相关参数
```

### 3. 启动服务

```bash
./start.sh
```

或直接使用Python：

```bash
cd api
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 访问服务

- **WebSocket端点**: `ws://localhost:8000/gateway/ws?user_id=xujian`
- **健康检查**: `http://localhost:8000/gateway/health`
- **模块列表**: `http://localhost:8000/gateway/modules`

## Gateway协议

### 消息帧格式

#### 请求帧 (Request)

```json
{
  "type": "request",
  "id": "uuid",
  "method": "send",
  "params": {
    "message": "搜索关于AI的专利"
  },
  "timestamp": "2025-01-31T00:00:00"
}
```

#### 响应帧 (Response)

```json
{
  "type": "response",
  "id": "uuid",
  "result": {
    "success": true
  },
  "timestamp": "2025-01-31T00:00:00"
}
```

#### 事件帧 (Event)

```json
{
  "type": "event",
  "event": "chat.message",
  "data": {
    "role": "assistant",
    "content": "好的爸爸！找到了..."
  },
  "timestamp": "2025-01-31T00:00:00"
}
```

### 支持的方法

| 方法 | 说明 | 参数 |
|------|------|------|
| `send` | 发送消息 | `{message: string}` |
| `platform_modules` | 获取可用模块 | - |
| `platform_invoke` | 调用平台模块 | `{module, action, params}` |
| `sessions_list` | 列出会话 | - |
| `sessions_patch` | 更新会话配置 | `{updates}` |
| `config_get` | 获取配置 | `{key?}` |
| `config_set` | 设置配置 | `{key, value}` |

## 身份管理

小诺根据用户关系使用不同的称呼和语气：

| 关系类型 | 称呼示例 | 语气风格 |
|---------|---------|---------|
| FATHER (父亲) | "爸爸" | 亲切、频繁使用表情 |
| MOTHER (母亲) | "妈妈" | 亲切 |
| FAMILY (家人) | "家人" | 温暖 |
| FRIEND (朋友) | "朋友" | 友好 |
| COLLEAGUE (同事) | "同事" | 正式 |
| GUEST (访客) | "访客" | 专业 |

## 平台模块

### 可用模块

| 模块 | 说明 | 操作 |
|------|------|------|
| `patent.search` | 专利搜索 | search, advanced_search, batch_search |
| `patent.analyze` | 专利分析 | analyze, compare, assess_value |
| `knowledge.graph` | 知识图谱 | query, explore, find_path |
| `knowledge.vector` | 向量搜索 | search, similarity, hybrid |
| `knowledge.sql` | 数据查询 | query, aggregate, join |
| `tool.webchat` | 对话导出 | export_session, export_all |
| `tool.report` | 报告生成 | generate, preview, schedule |
| `tool.export` | 数据导出 | export, bulk_export |

## 意图路由

小诺自动识别用户意图并路由到相应模块：

| 用户消息示例 | 识别意图 | 调用模块 |
|-------------|---------|---------|
| "搜索AI相关的专利" | patent_search | patent.search |
| "分析这个专利的价值" | patent_analyze | patent.analyze |
| "查询相关技术资料" | knowledge_query | knowledge.vector |
| "导出对话记录" | data_export | tool.export |

## 开发

### 添加新模块

```python
# 在 modules/registry.py 的 _initialize_builtin_modules 中添加
self.register(ModuleDefinition(
    name="your.module",
    display_name="您的模块",
    description="模块描述",
    category="your_category",
    actions=["action1", "action2"],
))
```

### 添加新意图

```python
# 在 modules/router.py 的 INTENT_PATTERNS 中添加
"your_intent": {
    "keywords": ["关键词1", "关键词2"],
    "module": "your.module",
    "action": "action1",
},
```

## 测试

使用WebSocket客户端测试：

```python
import asyncio
import websockets
import json

async def test():
    uri = "ws://localhost:8000/gateway/ws?user_id=xujian"
    async with websockets.connect(uri) as ws:
        # 发送消息
        request = {
            "type": "request",
            "id": "test-1",
            "method": "send",
            "params": {"message": "搜索AI专利"},
            "timestamp": "2025-01-31T00:00:00"
        }
        await ws.send(json.dumps(request))

        # 接收响应
        while True:
            response = await ws.recv()
            print(json.loads(response))

asyncio.run(test())
```

## License

MIT License
