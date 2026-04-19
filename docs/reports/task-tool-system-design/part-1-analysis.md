# Athena平台Task Tool系统设计方案

**文档版本**: v1.0.0
**创建日期**: 2026-04-05
**作者**: Athena平台团队
**状态**: 设计阶段

---

## 📋 执行摘要

### 目标
将Kode Agent的Task Tool和后台任务管理系统移植到Athena平台，实现：
1. 子代理委托机制
2. 并行任务执行
3. 非阻塞长时运行任务
4. 与Athena四层记忆系统的无缝集成
5. 专利领域特定代理类型支持

### 关键成果
- ✅ 完成Kode Agent源代码深度分析 (TaskTool.tsx: 839行)
- ✅ 识别出核心功能模块：输入验证、模型映射、后台任务管理、Fork上下文、进度跟踪
- ✅ 分析Athena现有架构的兼容性 (BaseAgent、ToolManager、四层记忆系统)
- ✅ 设计Python实现方案

---

## 1. Kode Agent Task Tool 系统深度分析

### 1.1 核心架构

```
TaskTool.tsx (839行)
├── 输入验证层 (validateInput)
│   ├── description/prompt 必填验证
│   ├── subagent_type 有效性检查
│   └── resume 任务恢复验证
├── 模型映射层
│   ├── haiku → quick
│   ├── sonnet → task
│   └── opus → main
├── 后台任务管理层
│   ├── upsertBackgroundAgentTask()
│   ├── taskOutputStore (读写任务输出)
│   └── AbortController (任务取消)
├── 执行层 (call)
│   ├── 同步执行模式
│   └── 异步后台执行模式
└── 输出渲染层
    ├── renderToolUseMessage
    ├── renderToolResultMessage
    └── renderResultForAssistant
```

### 1.2 关键技术特性

| 特性 | 实现方式 | 价值 |
|------|---------|------|
| **输入验证** | TypeScript schema + validateInput函数 | 确保任务参数有效性 |
| **模型选择** | 三级映射 + 环境变量KODE_SUBAGENT_MODEL | 灵活模型路由 |
| **工具过滤** | allowedTools + disallowedTools | 安全控制子代理权限 |
| **Fork上下文** | buildForkContextForAgent() | 子代理隔离 |
| **进度跟踪** | 工具使用计数 + 节流(200ms) | 实时进度反馈 |
| **后台任务** | Promise + AbortController | 非阻塞长时任务 |
| **任务持久化** | taskOutputStore.ts | 任务状态恢复 |

### 1.3 执行流程

**同步执行模式**:
```
1. 验证输入参数
2. 选择模型 (input.model → 映射 → 环境变量 → 默认)
3. 过滤可用工具 (allowedTools/disallowedTools)
4. 构建Fork上下文
5. 执行查询循环 (for await of queryFn)
6. 跟踪进度 (每200ms节流)
7. 保存agent transcript
8. 返回结果 (status: completed)
```

**异步后台执行模式**:
```
1. 验证输入参数
2. 创建AbortController
3. 创建taskRecord (status: running)
4. 启动后台Promise
5. 立即返回 (status: async_launched)
6. 后台Promise执行查询循环
7. 更新taskRecord.messages
8. 完成后更新taskRecord状态 (completed/failed)
9. 持久化任务输出到taskOutputStore
```

### 1.4 数据结构

**Input Schema**:
```TypeScript
{
  description: string        // 任务描述 (必填)
  prompt: string             // 任务提示词 (必填)
  subagent_type: string      // 子代理类型
  model?: string             // 模型选择 (haiku/sonnet/opus)
  resume?: string            // 恢复任务ID
  command?: string           // 指令
  run_in_background?: boolean // 后台运行模式
}
```

**Output Schema**:
```TypeScript
{
  status: 'completed' | 'async_launched'
  agentId: string
  prompt: string
  content?: TextBlock[]       // 同步模式才有
  totalToolUseCount?: number  // 同步模式才有
  totalDurationMs?: number    // 同步模式才有
  totalTokens?: number        // 同步模式才有
  usage?: any                 // 同步模式才有
}
```

**TaskRecord (后台任务)**:
```TypeScript
{
  type: 'async_agent'
  agentId: string
  description: string
  prompt: string
  status: 'running' | 'completed' | 'failed'
  startedAt: number
  completedAt?: number
  messages: MessageType[]
  abortController: AbortController
  done: Promise<void>
  resultText?: string
  error?: string
}
```

### 1.5 关键源码片段分析

**模型映射逻辑 (lines 473-486)**:
```typescript
const normalizedAgentModel = normalizeAgentModelName(agentConfig.model)
const defaultSubagentModel = 'task'
const envSubagentModel = process.env.KODE_SUBAGENT_MODEL ?? process.env.CLAUDE_CODE_SUBAGENT_MODEL
const modelToUse: string =
  (typeof envSubagentModel === 'string' && envSubagentModel.trim()
    ? envSubagentModel.trim()
    : undefined) ||
  modelEnumToPointer(input.model) ||
  (normalizedAgentModel === 'inherit'
    ? parentModel || defaultSubagentModel
    : normalizedAgentModel) ||
  defaultSubagentModel
```

**工具过滤逻辑 (lines 488-512)**:
```typescript
const toolFilter = agentConfig.tools
let tools = await getTaskTools(safeMode)
if (toolFilter) {
  const isAllArray = Array.isArray(toolFilter) && toolFilter.length === 1 && toolFilter[0] === '*'
  if (toolFilter === '*' || isAllArray) {
  } else if (Array.isArray(toolFilter)) {
    const allowedToolNames = new Set(toolFilter.map(getToolNameFromSpec).filter(Boolean))
    tools = tools.filter(t => allowedToolNames.has(t.name))
  }
}

const disallowedTools = Array.isArray(agentConfig.disallowedTools) ? agentConfig.disallowedTools : []
if (disallowedTools.length > 0) {
  const disallowedToolNames = new Set(disallowedTools.map(getToolNameFromSpec).filter(Boolean))
  tools = tools.filter(t => !disallowedToolNames.has(t.name))
}
```

**后台任务创建 (lines 573-647)**:
```typescript
if (input.run_in_background) {
  const bgAbortController = new AbortController()

  const taskRecord: any = {
    type: 'async_agent',
    agentId,
    description: input.description,
    prompt: effectivePrompt,
    status: 'running',
    startedAt: Date.now(),
    messages: [...transcriptMessages],
    abortController: bgAbortController,
    done: Promise.resolve(),
  }

  taskRecord.done = (async () => {
    try {
      // 执行查询循环
      for await (const msg of queryFn(...)) {
        bgMessages.push(msg)
        bgTranscriptMessages.push(msg)
        taskRecord.messages = [...bgTranscriptMessages]
        upsertBackgroundAgentTask(taskRecord)
      }

      taskRecord.status = 'completed'
      taskRecord.completedAt = Date.now()
      taskRecord.resultText = (content || []).map(b => b.text).join('\n')
      taskRecord.messages = [...bgTranscriptMessages]
      upsertBackgroundAgentTask(taskRecord)
      saveAgentTranscript(agentId, bgTranscriptMessages)
    } catch (e) {
      taskRecord.status = 'failed'
      taskRecord.completedAt = Date.now()
      taskRecord.error = e instanceof Error ? e.message : String(e)
      upsertBackgroundAgentTask(taskRecord)
    }
  })()

  upsertBackgroundAgentTask(taskRecord)

  const output: Output = {
    status: 'async_launched',
    agentId,
    description: input.description,
    prompt: effectivePrompt,
  }
  yield {
    type: 'result',
    data: output,
    resultForAssistant: asyncLaunchMessage(agentId),
  }
  return
}
```

---

## 2. Athena平台现有架构分析

### 2.1 BaseAgent架构

**位置**: `/Users/xujian/Athena工作平台/core/agents/base_agent.py` (307行)

**核心能力**:
```python
class BaseAgent(ABC):
    def __init__(self, name, role, model, temperature, max_tokens, **kwargs)
    def process(self, input_text, **kwargs) -> str  # 抽象方法

    # 对话管理
    def add_to_history(self, role, content)
    def clear_history(self)
    def get_history(self)

    # 记忆管理
    def remember(self(, key, value)
    def recall(self, key)
    def forget(self, key)

    # 能力管理
    def add_capability(self, capability)
    def has_capability(self, capability)

    # 验证
    def validate_input(self, input_text)
    def validate_config(self)
```

**需要扩展的能力**:
- ❌ 缺少子代理委托机制
- ❌ 缺少后台任务管理
- ❌ 缺少模型映射和选择
- ❌ 缺少工具过滤机制
- ❌ 缺少进度跟踪回调

### 2.2 Tool管理架构

**位置**:
- `/Users/xujian/Athena工作平台/core/tools/tool_manager.py` (377行)
- `/Users/xujian/Athena工作平台/core/tools/tool_call_manager.py` (507行)

**核心功能**:
```python
class ToolManager:
    def register_group(self, definition: ToolGroupDef)
    def activate_group(self, group_name, deactivate_others)
    def get_active_tools(self) -> list[ToolDefinition]

class ToolCallManager:
    async def execute_tool_call(self, request: ToolCallRequest)
    def get_call_history(self, limit: int)
    def monitor_performance(self, tool_name: str)
```

**与Kode的兼容性**:
- ✅ 已有工具注册和发现机制
- ✅ 已有工具调用管理
- ✅ 需要扩展支持子代理工具类型
- ✅ 需要集成后台任务调度

### 2.3 四层记忆系统

**位置**: `/Users/xujian/Athena工作平台/core/memory/`

**架构**:
```
HOT  (memory)   → 100MB  → Python dict
WARM (Redis)    → 500MB  → Redis
COLD (SQLite)   → 10GB   → SQLite
ARCHIVE         → 无限   → 文件系统
```

**集成方案**:
- Task状态 → HOT层 (快速访问)
- Agent transcript → WARM层 (会话保持)
- 历史任务记录 → COLD层 (持久化)
- 长期归档 → ARCHIVE层 (审计)

### 2.4 协作模式系统

**位置**: `/Users/xujian/Athena工作平台/core/collaboration/`

**现有模式**:
- Sequential (顺序)
- Parallel (并行)
- Hierarchical (层级)
- Consensus (共识)

**需要扩展**:
- 子代理委托模式 (SubagentDelegation)
- Fork上下文隔离模式 (ForkContextIsolation)
- 后台任务协调模式 (BackgroundTaskCoordination)
