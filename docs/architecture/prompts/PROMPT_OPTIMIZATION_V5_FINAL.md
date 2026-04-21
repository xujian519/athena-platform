# 提示词工程优化方案 v5.0 Final

> **版本**: 5.0 Final
> **创建日期**: 2026-04-21
> **核心理念**: 极致压缩 + 原小娜/Athena优点整合

---

## 📋 问题陈述

用户提出的两个核心问题：

1. **提示词占用过多上下文空间**
   - 当前设计：完整提示词可能超过20K tokens
   - 目标：压缩到5K-10K tokens（初始加载）
   - 策略：渐进式加载、模板化、参数化

2. **吸收原小娜、Athena的优点**
   - 原小娜v4.0的优点：静态/动态分离、约束重复、whenToUse、并行调用、Scratchpad
   - 需要整合到Athena团队的多智能体架构中

---

## 🎯 优化目标

| 指标 | 当前 | 目标 | 优化策略 |
|------|------|------|---------|
| 初始加载 | ~20K tokens | **~5K tokens** | 渐进式加载 |
| 完整加载 | ~20K tokens | **~10K tokens** | 模板化+参数化 |
| 缓存命中率 | ~60% | **>90%** | 静态/动态分离 |
| 加载速度 | ~2s | **<500ms** | 缓存+预加载 |

---

## 🏗️ 优化架构设计

### 1. 三层分离架构

```
┌─────────────────────────────────────────────────────────────┐
│  静态层（STATIC - 可缓存，永久）                             │
│  - 基础身份定义（压缩版，500 tokens）                        │
│  - 系统关键规则（约束重复，300 tokens）                      │
│  - 能力模板（参数化，2K tokens）                             │
├─────────────────────────────────────────────────────────────┤
│  场景层（SCENARIO - 按需加载，LRU缓存）                      │
│  - 场景特定知识（3K tokens，按需）                          │
│  - 场景特定能力（2K tokens，按需）                          │
├─────────────────────────────────────────────────────────────┤
│  会话层（SESSION - 动态生成，不缓存）                        │
│  - 会话上下文（500 tokens）                                  │
│  - 用户输入（变量）                                          │
│  - 实时数据（变量）                                          │
└─────────────────────────────────────────────────────────────┘
```

---

### 2. 渐进式加载策略

#### 阶段1：核心加载（~5K tokens）

**触发时机**: 智能体启动时

**加载内容**:
```python
CORE_PROMPT = """
# {agent_name} v5.0

## 身份（压缩版）
{compressed_identity}

## 关键规则（约束重复）
{critical_rules_start}

## 核心能力模板
{capability_templates}

## 关键规则（重复）
{critical_rules_end}
"""
```

**内容示例**（检索者）:
```markdown
# 检索者(RetrieverAgent) v5.0

## 身份
专利检索专家，多源检索、去重排序

## 核心原则
1. 全面性（不遗漏）
2. 多源原则（交叉验证）
3. 效率优先

## 能力模板
- 理解技术方案
- 构建检索策略
- 执行多源检索
- 结果去重排序

## 输出
双格式：JSON + Markdown

---
REMINDER: 全面性、多源原则、双格式输出
"""
```

**Token统计**: ~800 tokens

---

#### 阶段2：场景加载（+3K tokens）

**触发时机**: 场景识别后

**加载内容**:
```python
SCENARIO_PROMPT = """
## 当前场景：{scenario}

### 场景知识（压缩版）
{compressed_knowledge}

### 场景能力（参数化）
- 能力1: {capability_1} <whenToUse="{trigger_1}">
- 能力2: {capability_2} <whenToUse="{trigger_2}">

### 输出格式
{output_format_template}
"""
```

**Token统计**: +3K tokens

---

#### 阶段3：完整加载（+2K tokens）

**触发时机**: 执行复杂任务时

**加载内容**:
```python
FULL_PROMPT = """
### 详细流程
{detailed_workflow}

### 质量标准
{quality_standards}

### 案例参考
{case_references}
"""
```

**Token统计**: +2K tokens

---

### 3. 模板化+参数化设计

#### 3.1 能力模板

**原设计**（每个能力500 tokens）:
```markdown
## 能力1: 理解技术方案

<whenToUse>
用户请求包含：技术交底书、技术方案描述、发明点说明
</whenToUse>

**功能**: 从技术文档中提取关键技术特征、技术领域、技术问题、技术效果

**输出格式**:
```json
{
  "structured_data": {
    "technical_field": "技术领域",
    "technical_problem": "技术问题",
    ...
  },
  "markdown_text": "# 技术方案理解\n..."
}
```
```

**优化设计**（模板化，100 tokens）:
```markdown
## 能力1: 理解技术方案 <whenToUse="{triggers}">

{template:capability_understanding}

**输出**: 双格式（JSON + Markdown）
```

**模板定义**（可复用）:
```python
CAPABILITY_TEMPLATES = {
    "capability_understanding": """
功能：{description}
提取：{extract_fields}
输出：双格式（JSON + Markdown）
""",
    
    "capability_analysis": """
功能：{description}
分析维度：{dimensions}
输出：双格式（JSON + Markdown）
""",
}
```

**Token节省**: 500 tokens → 100 tokens（80%压缩）

---

#### 3.2 输出格式模板

**原设计**（每次200 tokens）:
```json
{
  "structured_data": {
    "technical_field": "技术领域",
    "technical_problem": "技术问题",
    "key_features": ["关键特征1", "关键特征2"],
    "technical_effects": ["技术效果1", "技术效果2"],
    "keywords": ["关键词1", "关键词2", "同义词1"]
  },
  "markdown_text": "# 技术方案理解\n## 技术领域\n...\n## 关键特征\n..."
}
```

**优化设计**（模板化，50 tokens）:
```python
OUTPUT_TEMPLATES = {
    "understanding": {
        "json": {
            "field": str,
            "problem": str,
            "features": List[str],
            "effects": List[str],
            "keywords": List[str]
        },
        "markdown": "# 技术方案理解\n## {field}\n...\n"
    }
}
```

**使用时**:
```markdown
**输出格式**: {template:output_understanding}
```

**Token节省**: 200 tokens → 50 tokens（75%压缩）

---

### 4. 知识压缩策略

#### 4.1 知识摘要

**原设计**（完整知识，5K tokens）:
```markdown
# 专利检索知识库

## 当前检索场景：CREATIVITY_ANALYSIS

## 关键知识内容

### 三步法审查指南

**第一步：确定最接近的现有技术**
选择标准：
1. 技术领域相同或相近
2. 技术问题相同或相似
3. 技术效果相似
4. 公开技术特征最多

**第二步：确定区别特征**
...
（完整内容，5K tokens）
```

**优化设计**（摘要版，500 tokens）:
```markdown
# 创造性分析知识（摘要）

## 三步法（5W1H）
- Who: 本申请 vs D1
- What: 区别特征DF1, DF2
- Why: 技术效果E1, E2
- How: 结合启示判断
- When: 预料不到的效果
- Where: 证据位置

## 关键规则
1. 单独对比原则
2. 区别特征必须明确
3. 技术效果必须有证据
4. 结合启示必须合理

## 快速参考
- 创造性判断流程：F1 → DF → E → Disclosure
- 常见陷阱：忽略反教导、忽视结合障碍
- 关键证据：实验数据、对比文件

**详细知识**: 按需加载（5K tokens）
```

**Token节省**: 5K tokens → 500 tokens（90%压缩）

---

#### 4.2 知识索引

**设计思路**: 只加载索引，详细内容按需加载

```python
KNOWLEDGE_INDEX = {
    "creativity_analysis": {
        "summary": "三步法判断创造性（Who/What/Why/How/When/Where）",
        "key_rules": ["单独对比", "区别特征明确", "技术效果证据", "结合启示合理"],
        "quick_reference": "F1 → DF → E → Disclosure",
        "detailed_files": [
            "三步法审查指南.md",
            "创造性判断案例.md",
            "公知常识库.md"
        ]
    }
}
```

---

### 5. 静态/动态分离（继承v4.0优点）

#### 5.1 静态部分（可缓存）

**内容**:
- 基础身份定义（压缩版）
- 系统关键规则（约束重复）
- 能力模板（参数化）
- 输出格式模板

**缓存策略**: 永久缓存，启动时加载

**Token统计**: ~2K tokens

---

#### 5.2 动态部分（会话特定）

**内容**:
- 会话上下文（500 tokens）
- 场景知识（按需，3K tokens）
- 场景能力（按需，2K tokens）
- 用户输入（变量）
- 实时数据（变量）

**缓存策略**: 不缓存，每次动态生成

**Token统计**: 500 tokens + 按需加载

---

### 6. whenToUse触发机制（继承v4.0优点）

#### 6.1 触发器定义

```python
WHEN_TO_USE_TRIGGERS = {
    "retrieval": {
        "triggers": ["检索", "搜索", "查找", "prior art"],
        "priority": 1,
        "auto_load": ["capability_retrieval", "knowledge_search"]
    },
    
    "creativity_analysis": {
        "triggers": ["创造性", "分析专利", "非显而易见", "inventive step"],
        "priority": 2,
        "auto_load": ["capability_creativity", "knowledge_creativity"]
    },
    
    "novelty_analysis": {
        "triggers": ["新颖性", "判断新颖性", "novelty"],
        "priority": 6,  # ⚠️ 仅在明确指示时
        "auto_load": ["capability_novelty", "knowledge_novelty"],
        "require_confirmation": True
    }
}
```

---

#### 6.2 触发逻辑

```python
async def trigger_capabilities(user_input: str) -> List[str]:
    """
    根据用户输入触发能力加载
    """
    triggered = []
    
    for capability, config in WHEN_TO_USE_TRIGGERS.items():
        # 检查触发词
        if any(trigger in user_input for trigger in config["triggers"]):
            # 检查优先级
            if config.get("require_confirmation"):
                # 需要用户确认
                if not await request_confirmation(
                    f"检测到{capability}，是否继续？"
                ):
                    continue
            
            # 自动加载
            for module in config["auto_load"]:
                await load_module(module)
            
            triggered.append(capability)
    
    return triggered
```

---

### 7. 并行工具调用（继承v4.0优点）

#### 7.1 Turn-based并行

**设计**: 将任务分解为多个Turn，每个Turn内并行执行

**示例**（审查意见分析）:
```markdown
### Turn 1: 并行读取
parallel([
    read_oa_document(),
    read_patent_application(),
    read_prior_art()
])
→ 等待所有完成

### Turn 2: 并行分析
parallel([
    analyze_novelty(),
    analyze_creativity(),
    analyze_clarity()
])
→ 等待所有完成

### Turn 3: 综合判断
synthesize([
    novelty_result,
    creativity_result,
    clarity_result
])
```

**性能提升**: 75%（串行12分钟 → 并行3分钟）

---

#### 7.2 并行指令模板

```markdown
### 并行执行指令

**当前Turn**: {turn_number}

**并行任务**:
```python
parallel([
    task_1({params_1}),
    task_2({params_2}),
    task_3({params_3})
])
```

**等待条件**: 所有任务完成

**下一步**: {next_step}
```

---

### 8. Scratchpad推理（继承v4.0优点）

#### 8.1 推理模板

```markdown
## Scratchpad推理（私下）

### 推理过程
{private_reasoning}

### 推理摘要（给用户）
{reasoning_summary}

---

## 用户可见内容

{user_visible_content}
```

**使用示例**:
```markdown
## Scratchpad: 创造性分析推理

### 私下推理
1. 分析最接近现有技术：
   - D1: CN123456789A，公开了特征F1, F2, F3
   - 未公开：F4, F5
   - 选择理由：技术领域相同，公开90%特征

2. 分析区别特征：
   - DF1: F4（自适应控制算法）
   - DF2: F5（多模态融合）

3. 分析技术效果：
   - 预期效果：性能提升20%
   - 实际效果：性能提升50%
   - 预料不到：是（超出预期30%）

4. 判断技术启示：
   - D1未给出DF1的启示
   - D1教导避免使用复杂算法
   - 结论：不存在结合启示

5. 综合判断：
   - 具备创造性
   - 关键：预料不到的效果 + 反教导

### 推理摘要（给用户）
通过三步法分析，本申请具备创造性。关键在于：
1. 区别特征DF1带来了预料不到的技术效果（性能提升50%，超出预期30%）
2. D1教导避免使用复杂算法，不构成结合启示

---

## 创造性分析报告

### 三步法分析

**第一步：最接近现有技术**
- D1: CN123456789A
...
```

**Token节省**: 推理过程不占用输出Token，只展示摘要

---

## 📊 优化效果对比

### Token使用对比

| 阶段 | 原设计 | 优化设计 | 节省 |
|------|--------|---------|------|
| 核心加载 | 20K tokens | 5K tokens | **75%** |
| 场景加载 | 20K tokens | 8K tokens | **60%** |
| 完整加载 | 20K tokens | 10K tokens | **50%** |

---

### 缓存命中率对比

| 内容类型 | 原设计 | 优化设计 | 提升 |
|---------|--------|---------|------|
| 静态层 | 60% | **95%** | +58% |
| 场景层 | 40% | **85%** | +113% |
| 综合命中率 | 50% | **90%** | +80% |

---

### 性能对比

| 指标 | 原设计 | 优化设计 | 提升 |
|------|--------|---------|------|
| 初始加载时间 | 2s | **<500ms** | **4x** |
| 场景切换时间 | 1.5s | **<300ms** | **5x** |
| 内存占用 | 50MB | **20MB** | **60%** |

---

## 🚀 实施方案

### 阶段1：核心优化（1周）

**任务**:
1. 实现三层分离架构
2. 实现渐进式加载策略
3. 实现模板化+参数化

**目标**:
- 初始加载从20K tokens降至5K tokens
- 缓存命中率达到80%

---

### 阶段2：知识压缩（1周）

**任务**:
1. 压缩所有知识库内容
2. 建立知识索引
3. 实现按需加载

**目标**:
- 知识加载从5K tokens降至500 tokens
- 按需加载延迟<100ms

---

### 阶段3：v4.0优点整合（1周）

**任务**:
1. 整合whenToUse触发机制
2. 整合并行工具调用
3. 整合Scratchpad推理

**目标**:
- 性能提升75%
- 推理质量提升

---

## 📁 文件结构

```
prompts_v5/
├── static/                              # [STATIC - 可缓存]
│   ├── identity/                        # 身份定义（压缩版）
│   │   ├── retriever_identity_v5.md     # 检索者身份（500 tokens）
│   │   ├── analyzer_identity_v5.md      # 分析者身份（500 tokens）
│   │   └── ...
│   │
│   ├── rules/                           # 系统规则（约束重复）
│   │   ├── critical_rules_start.md      # 关键规则开头（300 tokens）
│   │   └── critical_rules_end.md        # 关键规则结尾（300 tokens）
│   │
│   ├── templates/                       # 能力模板（参数化）
│   │   ├── capability_templates.json    # 能力模板定义
│   │   ├── output_templates.json        # 输出格式模板
│   │   └── knowledge_templates.json     # 知识模板定义
│   │
│   └── triggers/                        # whenToUse触发器
│       ├── capability_triggers.json     # 能力触发器
│       └── scenario_triggers.json       # 场景触发器
│
├── scenario/                            # [SCENARIO - 按需加载，LRU缓存]
│   ├── creativity_analysis/             # 创造性分析场景
│   │   ├── knowledge_summary.md         # 知识摘要（500 tokens）
│   │   ├── knowledge_index.json         # 知识索引
│   │   ├── capabilities.json            # 场景能力
│   │   └── workflow.md                  # 详细流程
│   │
│   ├── novelty_analysis/                # 新颖性分析场景
│   └── ...
│
├── dynamic/                             # [DYNAMIC - 会话特定，不缓存]
│   ├── session_context.md               # 会话上下文模板
│   ├── user_input.md                    # 用户输入模板
│   └── real_time_data.md                # 实时数据模板
│
└── scratchpads/                         # [SCRATCHPAD - 私下推理]
    ├── reasoning_template.md            # 推理模板
    └── summary_template.md              # 摘要模板
```

---

## 🎯 最终效果

### Token使用

| 场景 | 初始加载 | 完整加载 | 缓存命中 |
|------|---------|---------|---------|
| 检索 | 5K tokens | 8K tokens | 95% |
| 技术分析 | 5K tokens | 8K tokens | 90% |
| 创造性分析 | 5K tokens | 10K tokens | 85% |
| 新颖性分析 | 5K tokens | 10K tokens | 80% |
| 侵权分析 | 5K tokens | 10K tokens | 85% |

### 性能指标

| 指标 | 目标 | 预期 |
|------|------|------|
| 初始加载时间 | <500ms | ~300ms |
| 场景切换时间 | <300ms | ~200ms |
| 缓存命中率 | >90% | ~90% |
| 内存占用 | <30MB | ~20MB |

---

## 下一步工作

1. ✅ 优化方案设计（本文档）
2. ⏳ 实现三层分离架构
3. ⏳ 压缩所有提示词内容
4. ⏳ 实现渐进式加载器
5. ⏳ 整合v4.0优点
6. ⏳ 性能测试和优化

---

**End of Document**
