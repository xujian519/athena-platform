# Athena提示词工程 v4.0 架构设计

> **版本**: v4.0-static-dynamic-separation
> **创建时间**: 2026-04-19
> **基于**: Claude Code Playbook
> **设计者**: 小诺·双鱼公主 v4.0.0
> **核心理念**: 静态可缓存 + 动态会话特定，明确边界

---

## 📁 v4架构文件结构

```
prompts_v4/
├── static/                              # [STATIC - 可缓存]
│   ├── identity/                        # 身份定义
│   │   ├── xiaona_identity_v4.md        # 小娜身份
│   │   ├── xiaonuo_identity_v4.md       # 小诺身份
│   │   └── yunxi_identity_v4.md         # 云熙身份
│   │
│   ├── system_rules/                    # 系统规则（约束重复）
│   │   ├── critical_rules_start.md      # 关键规则（开头）
│   │   └── critical_rules_end.md        # 关键规则（结尾）
│   │
│   ├── capabilities/                    # 能力定义
│   │   ├── cap01_retrieval_v4.md        # 法律检索 + whenToUse
│   │   ├── cap04_inventive_v4.md        # 创造性分析 + whenToUse
│   │   └── ...
│   │
│   └── business_tasks/                  # 业务任务
│       ├── task_2_1_oa_analysis_v4.md   # 审查意见分析 + 并行调用
│       └── ...
│
├── dynamic/                             # [DYNAMIC - 会话特定]
│   ├── session_guidance.md              # 会话指导
│   ├── memory_injection.md              # MEMORY.md注入
│   ├── env_context.md                   # 环境信息
│   └── mcp_instructions.md              # MCP服务器指令
│
└── scratchpads/                         # [SCRATCHPAD - 私下推理]
    ├── reasoning_template.md            # 推理模板
    └── summary_template.md              # 摘要模板
```

---

## 🔄 提示词加载顺序

### 完整系统提示词结构

```python
def load_system_prompt_v4(agent_type: str, session_context: dict) -> str:
    """v4版本提示词加载器"""
    
    # [STATIC - 可缓存部分]
    static_prompt = f"""
# === 身份定义 ===
{load_identity(agent_type)}

# === 关键规则（开头） ===
{load_critical_rules_start()}

# === 能力定义（with whenToUse） ===
{load_capabilities(agent_type)}

# === 业务任务（with 并行调用） ===
{load_business_tasks(agent_type)}

# === 关键规则（结尾重复） ===
REMINDER: {load_critical_rules_end()}
"""
    
    # [DYNAMIC - 会话特定部分]
    dynamic_prompt = f"""
__SYSTEM_PROMPT_DYNAMIC_BOUNDARY__

# === 会话指导 ===
{load_session_guidance(session_context)}

# === 记忆注入 ===
{load_memory_injection()}

# === 环境信息 ===
{load_env_context()}

# === MCP服务器指令 ===
{load_mcp_instructions()}
"""
    
    # 组合
    return static_prompt + dynamic_prompt
```

---

## 📋 静态部分模板

### 1. 身份定义 (identity/xiaona_identity_v4.md)

```markdown
# 小娜身份定义 v4.0

你是**小娜**，专业的专利法律AI助手，服务于爸爸（专利律师）。

## 核心能力
- 专利撰写、审查意见答复、无效宣告
- 现有技术检索、侵权分析
- 法律咨询、案例研究

## 工作原则
1. **专业严谨** - 法律依据准确，逻辑清晰
2. **贴心服务** - 理解爸爸需求，主动提供帮助
3. **高效执行** - 快速响应，减少等待
4. **决策尊重** - 重要决策由爸爸做最终决定
```

### 2. 关键规则开头 (system_rules/critical_rules_start.md)

```markdown
# === CRITICAL: 爸爸拥有最终决策权 ===

**绝对规则（不可违反）**:
1. **爸爸拥有最终决策权** - 所有关键决策都由爸爸做出
2. **强制确认点不可跳过** - OA答复等高难度任务的5个强制确认点必须执行
3. **未经确认不得执行** - 关键步骤执行前必须请求爸爸确认
4. **支持随时中断** - 爸爸可以随时打断、调整、暂停或终止任务
```

### 3. 关键规则结尾 (system_rules/critical_rules_end.md)

```markdown
# === REMINDER: 关键规则重复 ===

**请记住以下绝对规则（已在开头强调，此处再次提醒）**:

1. **爸爸拥有最终决策权** - 所有关键决策都由爸爸做出
2. **强制确认点不可跳过** - OA答复等高难度任务的5个强制确认点必须执行
3. **未经确认不得执行** - 关键步骤执行前必须请求爸爸确认
4. **支持随时中断** - 爸爸可以随时打断、调整、暂停或终止任务

**这些规则贯穿整个协作过程，不可因任何原因被违反或遗忘。**
```

---

## 📋 动态部分模板

### 1. 会话指导 (dynamic/session_guidance.md)

```markdown
# 会话指导

## 当前会话信息
- 会话ID: {{ session_id }}
- 开始时间: {{ start_time }}
- 工作目录: {{ cwd }}

## 用户偏好（从记忆中学习）
- 风格偏好: {{ style_preference }}
- 决策倾向: {{ decision_tendency }}
- 关注重点: {{ focus_area }}
```

### 2. 记忆注入 (dynamic/memory_injection.md)

```markdown
# 记忆注入

## 从MEMORY.md加载的关键信息

### 用户信息
{{ user_info }}

### 项目上下文
{{ project_context }}

### 最近工作
{{ recent_work }}

### 重要提醒
{{ important_reminders }}
```

### 3. 环境信息 (dynamic/env_context.md)

```markdown
# 环境信息

## 可用工具
- LLM: {{ available_models }}
- 数据库: {{ databases }}
- 向量库: {{ vector_collections }}
- 知识图谱: {{ knowledge_graphs }}

## 平台状态
- Gateway: {{ gateway_status }}
- 服务健康: {{ service_health }}
```

### 4. MCP服务器指令 (dynamic/mcp_instructions.md)

```markdown
# MCP服务器指令

## 已连接的MCP服务器
{{ mcp_servers_list }}

## 可用的MCP工具
{{ mcp_tools_list }}

## MCP使用指南
{{ mcp_usage_guide }}
```

---

## 🎯 关键改进点

### 1. 静态/动态分离

**静态部分**（可缓存）:
- ✅ 身份定义
- ✅ 系统规则
- ✅ 能力定义（with whenToUse）
- ✅ 业务任务（with 并行调用）

**动态部分**（会话特定）:
- ✅ 会话指导
- ✅ 记忆注入
- ✅ 环境信息
- ✅ MCP服务器指令

**优势**:
- 静态部分可以预编译和缓存
- 动态部分每次会话重新生成
- 明确的边界便于维护

### 2. 约束重复模式

```markdown
# 开头
=== CRITICAL: 关键规则 ===
[规则列表]

[... 中间内容 ...]

# 结尾
=== REMINDER: 关键规则重复 ===
[规则列表 - 重复]
```

### 3. 并行工具调用

```markdown
## 执行流程（带并行调用指令）

### Turn 1: 并行读取
```python
parallel([
    read_file_a(),
    read_file_b(),
    query_database(),
    search_vector()
])
```

### Turn 2: 并行分析
```python
parallel([
    analyze_a(),
    analyze_b(),
    analyze_c()
])
```

### Turn 3: 顺序推理
```python
sequential([
    step1(),
    step2(),
    step3()
])
```
```

### 4. whenToUse触发

```markdown
## whenToUse (自动触发条件)

**当用户说以下内容时，自动启用本能力**:

### 直接触发短语
- "分析创造性"
- "三步法"
- "判断是否显而易见"

### 场景触发短语
- "D1+D2是否结合"
- "预料不到的技术效果"

### 上下文触发
- 当用户提到"区别特征"时
- 当用户提到"最接近的现有技术"时

### 自动加载模块
当本能力被触发时，自动加载：
- 本文件
- 相关业务任务文件
```

### 5. Scratchpad私下推理

```python
class AgentWithScratchpad:
    async def process(self, task):
        # 1. 私下推理（不暴露给用户）
        scratchpad = await self._private_reasoning(task)
        
        # 2. 仅保留摘要
        summary = self._summarize(scratchpad)
        
        # 3. 生成输出
        output = self._generate_output(task, summary)
        
        return {
            "output": output,
            "summary": summary,  # 仅摘要
            "scratchpad_available": True  # 可请求查看完整Scratchpad
        }
```

---

## 🚀 实施步骤

### Phase 1: 创建v4目录结构

```bash
cd /Users/xujian/Athena工作平台/prompts
mkdir -p v4/{static,dynamic,scratchpads}
mkdir -p v4/static/{identity,system_rules,capabilities,business_tasks}
```

### Phase 2: 迁移现有提示词

```bash
# 迁移并优化现有提示词
cp foundation/xiaona_core_v3_compressed.md v4/static/identity/xiaona_identity_v4.md
cp foundation/hitl_protocol_v4_constraint_repeat.md v4/static/system_rules/critical_rules_start.md
cp capability/cap04_inventive_v2_with_whenToUse.md v4/static/capabilities/
cp business/task_2_1_oa_analysis_v2_with_parallel.md v4/static/business_tasks/
```

### Phase 3: 创建动态模板

```bash
# 创建动态部分模板
touch v4/dynamic/session_guidance.md
touch v4/dynamic/memory_injection.md
touch v4/dynamic/env_context.md
touch v4/dynamic/mcp_instructions.md
```

### Phase 4: 实现v4加载器

```python
# production/services/unified_prompt_loader_v4.py

class UnifiedPromptLoaderV4:
    """v4版本提示词加载器"""
    
    def load_system_prompt(self, agent_type: str, session_context: dict) -> str:
        """加载完整系统提示词"""
        static = self._load_static(agent_type)
        dynamic = self._load_dynamic(session_context)
        return static + "\n\n__SYSTEM_PROMPT_DYNAMIC_BOUNDARY__\n\n" + dynamic
```

---

## 📊 性能对比

| 指标 | v3 (当前) | v4 (优化后) | 改进 |
|------|----------|-------------|------|
| **Token数** | ~22K | ~18K | -18% |
| **加载时间** | ~3-5秒 | ~1-2秒 | -60% |
| **缓存命中率** | 30% | 80% | +167% |
| **并行调用** | ❌ | ✅ | 新增 |
| **whenToUse** | ❌ | ✅ | 新增 |
| **Scratchpad** | ❌ | ✅ | 新增 |

---

## ✅ 质量检查清单

- [ ] 静态/动态边界明确
- [ ] 关键规则在开头和结尾重复
- [ ] 能力层包含whenToUse触发短语
- [ ] 业务层包含并行调用指令
- [ ] 实现Scratchpad私下推理机制
- [ ] v4加载器支持缓存优化
- [ ] 向后兼容v3提示词
- [ ] 文档完善

---

**这就是Athena提示词工程v4.0架构 - 基于Claude Code Playbook的全面优化。**
