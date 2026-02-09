# OpenClaw插件系统与memory-core插件实现深度解析

> **分析日期**: 2026-02-04
> **承接**: 配置系统与集成指南
> **分析维度**: 插件架构、memory-core实现、Athena插件化方案

---

## 📊 执行摘要

OpenClaw采用**Slot-based插件系统**，通过排他性槽(Exclusive Slot)机制实现同类插件的互斥运行，memory-core作为默认记忆插件通过简洁的接口注册工具和CLI命令。本文档深度剖析插件系统架构和memory-core实现，为Athena提供可复制的插件化方案。

### 核心发现

| 特征 | OpenClaw实现 | Athena建议 |
|------|-------------|-----------|
| **插件发现** | `openclaw.plugin.json`清单 | 统一插件清单格式 |
| **槽机制** | 排他性Slot(同类互斥) | 借鉴互斥机制 |
| **插件API** | 10种注册方式 | 简化为核心注册 |
| **插件类型** | memory/channel/provider等 | 定义Athena插件类型 |

---

## 🏗️ 插件系统架构

### 1. 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                    OpenClaw Plugin System                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              Plugin Loader                                 │ │
│  │  - 扫描 extensions/ 目录                                   │ │
│  │  - 解析 openclaw.plugin.json                              │ │
│  │  - 加载插件模块                                            │ │
│  └────────────────────────────────────────────────────────────┘ │
│                           │                                     │
│                           ▼                                     │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              Plugin Registry                               │ │
│  │  - plugins: PluginRecord[]                                │ │
│  │  - tools: PluginToolRegistration[]                        │ │
│  │  - hooks: PluginHookRegistration[]                        │ │
│  │  - channels: PluginChannelRegistration[]                  │ │
│  └────────────────────────────────────────────────────────────┘ │
│                           │                                     │
│                           ▼                                     │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              Slot System                                   │ │
│  │  memory: "memory-core"  # 默认记忆插件                     │ │
│  │  - 排他性: 同类插件只能有一个激活                          │ │
│  │  - 自动禁用: 切换时自动禁用其他                            │ │
│  └────────────────────────────────────────────────────────────┘ │
│                           │                                     │
│                           ▼                                     │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              Plugin API                                    │ │
│  │  registerTool()    # 注册Agent工具                        │ │
│  │  registerHook()    # 注册生命周期钩子                      │ │
│  │  registerCli()     # 注册CLI命令                           │ │
│  │  registerChannel() # 注册消息频道                          │ │
│  │  registerService() # 注册后台服务                          │ │
│  │  registerCommand() # 注册快捷命令                          │ │
│  │  registerProvider() # 注册模型提供商                       │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2. 插件清单文件

```json
// extensions/memory-core/openclaw.plugin.json
{
  "id": "memory-core",
  "kind": "memory",
  "configSchema": {
    "type": "object",
    "additionalProperties": false,
    "properties": {}
  }
}

// extensions/slack/openclaw.plugin.json
{
  "id": "slack",
  "channels": ["slack"],
  "configSchema": {
    "type": "object",
    "additionalProperties": false,
    "properties": {}
  }
}
```

**清单字段说明**:
- `id`: 插件唯一标识符
- `kind`: 插件类型（memory/channel/provider等）
- `channels`: 支持的频道列表（channel插件）
- `configSchema`: 插件配置的JSON Schema

### 3. 插件类型系统

```typescript
// src/plugins/types.ts:36

export type PluginKind = "memory" | "channel" | "provider";

// 当前OpenClaw主要使用memory类型
// channel和provider用于不同功能扩展
```

---

## 🔌 Slot系统机制

### 1. Slot定义与映射

```typescript
// src/plugins/slots.ts:12-28

// 插件类型到Slot的映射
const SLOT_BY_KIND: Record<PluginKind, PluginSlotKey> = {
  memory: "memory",  // 记忆插件槽
};

// 每个Slot的默认插件
const DEFAULT_SLOT_BY_KEY: Record<PluginSlotKey, string> = {
  memory: "memory-core",  // 默认使用memory-core
};
```

### 2. 排他性Slot选择

```typescript
// src/plugins/slots.ts:37-108

export function applyExclusiveSlotSelection(params: {
  config: OpenClawConfig;
  selectedId: string;        // 新选择的插件ID
  selectedKind?: PluginKind;  // 插件类型
  registry?: { plugins: SlotPluginRecord[] };
}): SlotSelectionResult {
  // 1. 确定Slot键
  const slotKey = slotKeyForPluginKind(params.selectedKind);
  if (!slotKey) {
    return { config: params.config, warnings: [], changed: false };
  }

  // 2. 更新Slot配置
  const slots = {
    ...pluginsConfig.slots,
    [slotKey]: params.selectedId,  // 设置新插件
  };

  // 3. 禁用同类型其他插件
  const disabledIds: string[] = [];
  for (const plugin of registry.plugins) {
    if (plugin.id === params.selectedId) continue;
    if (plugin.kind !== params.selectedKind) continue;

    // 禁用同类其他插件
    entries[plugin.id] = { enabled: false };
    disabledIds.push(plugin.id);
  }

  return {
    config: { ...params.config, plugins: { slots, entries } },
    warnings: [
      `Slot "${slotKey}" switched from "${prevSlot}" to "${selectedId}"`,
      `Disabled other "${slotKey}" slot plugins: ${disabledIds.join(", ")}`
    ],
    changed: true
  };
}
```

**工作流程**:
```
用户切换 memory: "memory-core" → "memory-custom"
    ↓
Slot系统检测到同类型切换
    ↓
1. 更新配置: slots.memory = "memory-custom"
2. 禁用旧插件: memory-core.enabled = false
3. 启用新插件: memory-custom.enabled = true
    ↓
生成警告日志，提醒用户插件已切换
```

---

## 🧩 memory-core插件实现

### 1. 插件结构

```
extensions/memory-core/
├── openclaw.plugin.json    # 插件清单
├── index.ts                # 插件主入口
└── package.json            # NPM包配置
```

### 2. 插件主入口

```typescript
// extensions/memory-core/index.ts:1-39

import type { OpenClawPluginApi } from "openclaw/plugin-sdk";

const memoryCorePlugin = {
  id: "memory-core",
  name: "Memory (Core)",
  description: "File-backed memory search tools and CLI",
  kind: "memory",
  configSchema: emptyPluginConfigSchema(),

  register(api: OpenClawPluginApi) {
    // 注册工具: memory_search 和 memory_get
    api.registerTool(
      (ctx) => {
        const memorySearchTool = api.runtime.tools.createMemorySearchTool({
          config: ctx.config,
          agentSessionKey: ctx.sessionKey,
        });
        const memoryGetTool = api.runtime.tools.createMemoryGetTool({
          config: ctx.config,
          agentSessionKey: ctx.sessionKey,
        });
        if (!memorySearchTool || !memoryGetTool) {
          return null;
        }
        return [memorySearchTool, memoryGetTool];
      },
      { names: ["memory_search", "memory_get"] },
    );

    // 注册CLI命令: openclaw memory
    api.registerCli(
      ({ program }) => {
        api.runtime.tools.registerMemoryCli(program);
      },
      { commands: ["memory"] },
    );
  },
};

export default memoryCorePlugin;
```

### 3. 工具创建流程

```typescript
// 工具工厂函数调用链
registerTool(factory, options)
    ↓
PluginRegistry.addToolRegistration({
  pluginId: "memory-core",
  factory: (ctx) => [memorySearchTool, memoryGetTool],
  names: ["memory_search", "memory_get"],
  optional: false
})
    ↓
Agent启动时调用工厂函数
    ↓
runtime.tools.createMemorySearchTool({ config, agentSessionKey })
    ↓
返回 AnyAgentTool 实例
```

### 4. 工具上下文

```typescript
// src/plugins/types.ts:56-65

export type OpenClawPluginToolContext = {
  config?: OpenClawConfig;        // 完整配置
  workspaceDir?: string;          // 工作目录
  agentDir?: string;              // Agent目录
  agentId?: string;               // Agent ID
  sessionKey?: string;            // 会话键
  messageChannel?: string;        // 消息频道
  agentAccountId?: string;        # Agent账户ID
  sandboxed?: boolean;            # 沙盒模式
};
```

---

## 🔌 Plugin API详解

### 1. 完整API列表

```typescript
// src/plugins/types.ts:233-272

export type OpenClawPluginApi = {
  // 插件元信息
  id: string;
  name: string;
  version?: string;
  description?: string;
  source: string;

  // 配置访问
  config: OpenClawConfig;
  pluginConfig?: Record<string, unknown>;

  // 运行时环境
  runtime: PluginRuntime;
  logger: PluginLogger;

  // 注册方法（10种）
  registerTool: (tool, opts?) => void;
  registerHook: (events, handler, opts?) => void;
  registerHttpHandler: (handler) => void;
  registerHttpRoute: (params) => void;
  registerChannel: (registration) => void;
  registerGatewayMethod: (method, handler) => void;
  registerCli: (registrar, opts?) => void;
  registerService: (service) => void;
  registerProvider: (provider) => void;
  registerCommand: (command) => void;

  // 工具方法
  resolvePath: (input) => string;
  on: (hookName, handler, opts?) => void;
};
```

### 2. 注册方式详解

#### registerTool - 工具注册

```typescript
// 注册Agent工具
api.registerTool(
  // 工具工厂函数
  (ctx: OpenClawPluginToolContext) => {
    return {
      name: "my_tool",
      description: "工具描述",
      execute: async (params) => { /* ... */ }
    };
  },
  // 选项
  {
    name: "my_tool",        // 工具名称
    names: ["tool1", "tool2"], // 或多个工具
    optional: true          // 是否可选
  }
);
```

#### registerHook - 钩子注册

```typescript
// 注册生命周期钩子
api.registerHook(
  "message_received",  // 事件名
  async (event, ctx) => {
    console.log("收到消息:", event.content);
  },
  { entry: "my-plugin.message_received" }
);

// 可用钩子事件
type PluginHookName =
  | "before_agent_start"
  | "agent_end"
  | "message_received"
  | "message_sending"
  | "message_sent"
  | "before_tool_call"
  | "after_tool_call"
  | "session_start"
  | "session_end"
  | "gateway_start"
  | "gateway_stop";
```

#### registerCli - CLI命令注册

```typescript
// 注册CLI命令
api.registerCli(
  ({ program, config, logger }) => {
    program
      .command("my-cmd")
      .description("我的命令")
      .action(async (options) => {
        logger.info("执行命令");
      });
  },
  { commands: ["my-cmd"] }
);
```

#### registerService - 后台服务注册

```typescript
// 注册后台服务
api.registerService({
  id: "my-service",
  start: async ({ config, stateDir, logger }) => {
    logger.info("服务启动");
    // 启动逻辑
  },
  stop: async ({ config, stateDir, logger }) => {
    logger.info("服务停止");
    // 停止逻辑
  }
});
```

#### registerCommand - 快捷命令注册

```typescript
// 注册快捷命令（绕过LLM）
api.registerCommand({
  name: "status",
  description: "查看状态",
  requireAuth: true,
  handler: async (ctx) => {
    return {
      text: `状态: 运行中`,
      messageType: "text"
    };
  }
});
```

---

## 📋 Plugin Registry

### 1. 注册表结构

```typescript
// src/plugins/registry.ts:124-138

export type PluginRegistry = {
  plugins: PluginRecord[];              // 插件列表
  tools: PluginToolRegistration[];      // 工具注册
  hooks: PluginHookRegistration[];      // 钩子注册
  typedHooks: TypedPluginHookRegistration[];
  channels: PluginChannelRegistration[]; // 频道注册
  providers: PluginProviderRegistration[];
  gatewayHandlers: GatewayRequestHandlers;
  httpHandlers: PluginHttpRegistration[];
  httpRoutes: PluginHttpRouteRegistration[];
  cliRegistrars: PluginCliRegistration[];
  services: PluginServiceRegistration[];  // 服务注册
  commands: PluginCommandRegistration[];
  diagnostics: PluginDiagnostic[];        // 诊断信息
};
```

### 2. 插件记录

```typescript
// src/plugins/registry.ts:97-122

export type PluginRecord = {
  id: string;              // 插件ID
  name: string;            // 插件名称
  version?: string;        // 版本号
  description?: string;    // 描述
  kind?: PluginKind;       // 插件类型
  source: string;          // 来源路径
  origin: PluginOrigin;    // 来源类型
  enabled: boolean;        // 是否启用
  status: "loaded" | "disabled" | "error";
  error?: string;          // 错误信息

  // 注册内容统计
  toolNames: string[];
  hookNames: string[];
  channelIds: string[];
  providerIds: string[];
  gatewayMethods: string[];
  cliCommands: string[];
  services: string[];
  commands: string[];
  httpHandlers: number;
  hookCount: number;

  // 配置相关
  configSchema: boolean;
  configUiHints?: Record<string, PluginConfigUiHint>;
  configJsonSchema?: Record<string, unknown>;
};
```

### 3. 全局注册表状态

```typescript
// src/plugins/runtime.ts:19-37

const REGISTRY_STATE = Symbol.for("openclaw.pluginRegistryState");

type RegistryState = {
  registry: PluginRegistry | null;
  key: string | null;
};

// 全局单例注册表
const state: RegistryState = {
  registry: createEmptyRegistry(),
  key: null,
};

export function setActivePluginRegistry(registry: PluginRegistry, cacheKey?: string) {
  state.registry = registry;
  state.key = cacheKey ?? null;
}

export function getActivePluginRegistry(): PluginRegistry | null {
  return state.registry;
}
```

---

## 💡 Athena插件化方案

### 1. 插件系统设计

#### 核心概念

```python
# core/plugins/types.py

from enum import Enum
from typing import Protocol, Optional, Dict, Any, List
from dataclasses import dataclass

class PluginKind(Enum):
    """插件类型"""
    MEMORY = "memory"        # 记忆插件
    CHANNEL = "channel"      # 频道插件
    PROVIDER = "provider"    # 模型提供商
    TOOL = "tool"           # 工具插件
    SERVICE = "service"     # 服务插件

@dataclass
class PluginManifest:
    """插件清单"""
    id: str                          # 插件ID
    name: str                        # 插件名称
    version: str                     # 版本号
    description: str                 # 描述
    kind: PluginKind                 # 插件类型
    author: Optional[str] = None     # 作者
    config_schema: Optional[Dict] = None  # 配置Schema

@dataclass
class PluginRecord:
    """插件记录"""
    manifest: PluginManifest
    source_path: str                 # 源路径
    enabled: bool = True             # 是否启用
    status: str = "loaded"           # 状态
    error: Optional[str] = None      # 错误信息

class PluginAPI(Protocol):
    """插件API协议"""

    @property
    def id(self) -> str: ...
    @property
    def config(self) -> Dict[str, Any]: ...
    @property
    def logger(self) -> Any: ...

    def register_tool(self, tool: Any, **opts) -> None: ...
    def register_hook(self, event: str, handler: callable) -> None: ...
    def register_cli(self, command: callable) -> None: ...
    def register_service(self, service: Any) -> None: ...
```

#### 插件管理器

```python
# core/plugins/manager.py

import json
from pathlib import Path
from typing import Dict, List, Optional
import importlib.util

class PluginManager:
    """Athena插件管理器"""

    def __init__(self, extensions_dir: str):
        self.extensions_dir = Path(extensions_dir)
        self._plugins: Dict[str, PluginRecord] = {}
        self._registry: PluginRegistry = PluginRegistry()
        self._slots: Dict[PluginKind, str] = {}

    def discover_plugins(self) -> List[PluginManifest]:
        """发现插件"""
        manifests = []

        for plugin_dir in self.extensions_dir.iterdir():
            manifest_file = plugin_dir / "athena.plugin.json"
            if not manifest_file.exists():
                continue

            with open(manifest_file) as f:
                data = json.load(f)

            manifest = PluginManifest(
                id=data["id"],
                name=data["name"],
                version=data.get("version", "0.0.0"),
                description=data.get("description", ""),
                kind=PluginKind(data["kind"]),
                author=data.get("author"),
                config_schema=data.get("configSchema")
            )
            manifests.append(manifest)

        return manifests

    def load_plugin(self, manifest: PluginManifest) -> bool:
        """加载插件"""
        plugin_dir = self.extensions_dir / manifest.id
        index_file = plugin_dir / "index.py"

        if not index_file.exists():
            return False

        # 动态加载插件模块
        spec = importlib.util.spec_from_file_location(
            manifest.id,
            index_file
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # 创建插件API
        api = AthenaPluginAPI(
            id=manifest.id,
            config=self._config,
            logger=self._logger,
            registry=self._registry
        )

        # 调用插件注册函数
        if hasattr(module, 'register'):
            module.register(api)

        # 记录插件
        self._plugins[manifest.id] = PluginRecord(
            manifest=manifest,
            source_path=str(plugin_dir),
            enabled=True
        )

        return True

    def activate_slot(self, kind: PluginKind, plugin_id: str) -> bool:
        """激活Slot（排他性）"""
        # 禁用同类其他插件
        for pid, record in self._plugins.items():
            if record.manifest.kind == kind and pid != plugin_id:
                record.enabled = False

        # 启用目标插件
        if plugin_id in self._plugins:
            self._plugins[plugin_id].enabled = True
            self._slots[kind] = plugin_id
            return True

        return False
```

### 2. memory-core插件实现

#### 插件清单

```json
// extensions/memory-core/athena.plugin.json
{
  "id": "memory-core",
  "name": "Memory (Core)",
  "version": "1.0.0",
  "description": "Vector-based memory search with hybrid semantic and keyword search",
  "kind": "memory",
  "author": "Athena Team",
  "configSchema": {
    "type": "object",
    "properties": {
      "enabled": { "type": "boolean", "default": true },
      "sources": {
        "type": "array",
        "items": { "type": "string" },
        "default": ["memory", "sessions"]
      }
    }
  }
}
```

#### 插件实现

```python
# extensions/memory-core/index.py

from typing import List, Optional
from athena.plugins import PluginAPI, Tool

class MemorySearchTool(Tool):
    """记忆搜索工具"""

    name = "memory_search"
    description = "语义搜索记忆库和会话历史"

    def __init__(self, memory_manager):
        self.memory_manager = memory_manager

    async def execute(
        self,
        query: str,
        max_results: int = 6,
        min_score: float = 0.35,
        session_key: Optional[str] = None
    ) -> List[dict]:
        """执行记忆搜索"""
        # 预热会话
        if session_key:
            await self.memory_manager.warm_session(session_key)

        # 执行搜索
        results = await self.memory_manager.search(
            query=query,
            max_results=max_results,
            min_score=min_score
        )

        return [
            {
                "path": r.path,
                "start_line": r.start_line,
                "end_line": r.end_line,
                "score": r.score,
                "snippet": r.snippet,
                "source": r.source
            }
            for r in results
        ]

class MemoryGetTool(Tool):
    """记忆读取工具"""

    name = "memory_get"
    description = "从记忆文件中读取片段"

    def __init__(self, memory_manager):
        self.memory_manager = memory_manager

    async def execute(
        self,
        path: str,
        from_line: Optional[int] = None,
        lines: Optional[int] = None
    ) -> dict:
        """读取记忆文件"""
        result = await self.memory_manager.read_file(
            rel_path=path,
            from_line=from_line,
            lines=lines
        )
        return {
            "path": result.path,
            "text": result.text
        }

# 插件注册函数
def register(api: PluginAPI):
    """注册memory-core插件"""

    # 获取记忆管理器
    from athena.memory import get_memory_manager
    memory_manager = get_memory_manager(api.config)

    # 注册工具
    api.register_tool(MemorySearchTool(memory_manager))
    api.register_tool(MemoryGetTool(memory_manager))

    # 注册CLI命令
    @api.cli_command()
    def memory_search(query: str, max_results: int = 6):
        """CLI: 搜索记忆"""
        import asyncio
        results = asyncio.run(memory_manager.search(
            query=query,
            max_results=max_results
        ))
        for r in results:
            print(f"[{r.score:.2f}] {r.path}:{r.start_line}")
            print(f"  {r.snippet[:100]}...")
```

### 3. 插件加载流程

```
Athena启动
    ↓
PluginManager.discover_plugins()
    ↓
扫描 extensions/ 目录
    ↓
读取每个插件目录的 athena.plugin.json
    ↓
验证插件清单
    ↓
PluginManager.load_plugin(manifest)
    ↓
动态加载 index.py 模块
    ↓
创建 PluginAPI 实例
    ↓
调用插件的 register(api) 函数
    ↓
插件注册工具/钩子/服务
    ↓
插件就绪
```

### 4. 配置集成

```yaml
# config/plugins.yaml
plugins:
  # 插件目录
  extensions_dir: "./extensions"

  # 插件槽配置
  slots:
    memory: "memory-core"    # 默认记忆插件
    # memory: "memory-custom"  # 可切换到自定义插件

  # 插件条目配置
  entries:
    memory-core:
      enabled: true
      config:
        sources: ["memory", "sessions"]
        max_results: 6

    memory-custom:
      enabled: false
      config:
        custom_setting: "value"
```

---

## 🎯 实施建议

### Phase 1: 基础插件系统 (Week 1-2)

**任务**:
- [ ] 创建 `PluginManager` 类
- [ ] 定义插件清单格式 `athena.plugin.json`
- [ ] 实现插件发现和加载机制
- [ ] 编写插件单元测试

### Phase 2: Plugin API (Week 3-4)

**任务**:
- [ ] 实现 `PluginAPI` 协议
- [ ] 支持工具注册 `register_tool()`
- [ ] 支持钩子注册 `register_hook()`
- [ ] 支持CLI注册 `register_cli()`

### Phase 3: memory-core插件 (Week 5-6)

**任务**:
- [ ] 创建 `extensions/memory-core/` 目录
- [ ] 实现 `MemorySearchTool` 和 `MemoryGetTool`
- [ ] 编写插件清单文件
- [ ] 集成测试

### Phase 4: 生产部署 (Week 7-8)

**任务**:
- [ ] 插件热加载支持
- [ ] 插件版本管理
- [ ] 插件市场（可选）
- [ ] 文档完善

---

## 📚 核心代码索引

| 文件路径 | 功能描述 |
|----------|----------|
| `/src/plugins/types.ts` | 插件类型定义（527行） |
| `/src/plugins/slots.ts` | Slot系统实现（109行） |
| `/src/plugins/registry.ts` | 插件注册表（核心） |
| `/src/plugins/runtime.ts` | 运行时状态管理 |
| `/extensions/memory-core/index.ts` | memory-core实现（39行） |
| `/extensions/memory-core/openclaw.plugin.json` | 插件清单 |

---

## 🚀 下一步行动

1. **创建插件原型**: 实现基础的 `PluginManager` 和插件加载
2. **定义API协议**: 设计Athena的 `PluginAPI` 接口
3. **实现memory插件**: 参考memory-core创建Athena版本
4. **测试验证**: 编写完整的插件系统测试套件

---

**报告生成时间**: 2026-02-04
**分析深度**: 插件系统级 + 代码实现级
**可信度**: ⭐⭐⭐⭐⭐ (源码级验证)
