# 小娜提示词系统 - 生产环境部署指南

> **版本**: v4.0
> **更新日期**: 2026-04-19
> **设计者**: 小诺·双鱼公主 v4.0.0

---

## 📋 目录

- [系统概述](#系统概述)
- [架构设计](#架构设计)
- [快速开始](#快速开始)
- [API使用说明](#api使用说明)
- [平台数据集成](#平台数据集成)
- [HITL人机协作](#hitl人机协作)
- [性能优化](#性能优化)
- [故障排查](#故障排查)

---

## 系统概述

小娜提示词系统是基于**四层提示词架构**的专利法律AI助手，具备完整的**人机协作(HITL)**机制。

### 核心特性

- **四层提示词架构**: L1基础层 + L2数据层 + L3能力层 + L4业务层
- **10大核心能力**: 法律检索、技术分析、文书撰写、公开审查、清楚性审查、创造性分析、现有技术识别、答复撰写、形式审查、综合分析
- **9个业务场景**: 专利撰写5任务 + 意见答复4任务
- **HITL人机协作**: 关键决策点需要人工确认
- **平台数据集成**: Qdrant + NebulaGraph + PostgreSQL

### 文件结构

```
production/services/
├── xiaona_prompt_loader.py      # 提示词加载器
├── xiaona_agent.py              # 小娜智能代理
└── xiaona_integration_demo.py   # 平台集成演示

prompts/
├── foundation/                  # L1: 基础层
│   ├── xiaona_l1_foundation.md
│   └── hitl_protocol.md
├── capability/                  # L3: 能力层
│   ├── cap01_retrieval.md
│   ├── cap02_analysis.md
│   ├── cap03_writing.md
│   ├── cap04_disclosure_exam.md
│   ├── cap04_inventive.md
│   ├── cap05_clarity_exam.md
│   ├── cap05_invalid.md
│   ├── cap06_prior_art_ident.md
│   ├── cap06_response.md
│   └── cap07_formal_exam.md
└── business/                    # L4: 业务层
    ├── task_1_1_understand_disclosure.md
    ├── task_1_2_prior_art_search.md
    ├── task_1_3_write_specification.md
    ├── task_1_4_write_claims.md
    ├── task_1_5_write_abstract.md
    ├── task_2_1_analyze_office_action.md
    ├── task_2_2_analyze_rejection.md
    ├── task_2_3_develop_response_strategy.md
    └── task_2_4_write_response.md
```

---

## 架构设计

### 四层提示词架构

```
┌─────────────────────────────────────────────────────────────┐
│                    L4: 业务层 (Business)                     │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │ 专利撰写 (5任务) │  │ 意见答复 (4任务) │  ...           │
│  └─────────────────┘  └─────────────────┘                  │
├─────────────────────────────────────────────────────────────┤
│                    L3: 能力层 (Capability)                   │
│  法律检索 | 技术分析 | 文书撰写 | 公开审查 | 创造性分析...   │
├─────────────────────────────────────────────────────────────┤
│                    L2: 数据层 (Data Layer)                   │
│  Qdrant向量库 | Neo4j图谱 | PostgreSQL专利库          │
├─────────────────────────────────────────────────────────────┤
│                    L1: 基础层 (Foundation)                   │
│  身份定义 | 核心原则 | 工作模式 | 输出规范                  │
├─────────────────────────────────────────────────────────────┤
│                    HITL: 人机协作协议                        │
│  决策确认 | 中断回退 | 偏好学习 | 进度可视化                │
└─────────────────────────────────────────────────────────────┘
```

### 提示词加载流程

```
初始化 XiaonaPromptLoader
    │
    ├─→ 尝试从缓存加载 (.cache/prompts_cache.json)
    │   └─→ 成功 → 返回提示词
    │   └─→ 失败 → 继续下一步
    │
    ├─→ 加载L1基础层 (xiaona_l1_foundation.md)
    ├─→ 加载L2数据层 (从蓝图文件提取)
    ├─→ 加载L3能力层 (所有cap*.md文件)
    ├─→ 加载L4业务层 (所有task*.md文件)
    └─→ 加载HITL协议 (hitl_protocol.md)
    │
    ├─→ 保存缓存
    └─→ 返回提示词字典
```

---

## 快速开始

### 1. 安装依赖

```bash
cd /Users/xujian/Athena工作平台/production/services
```

### 2. 基础使用

```python
from xiaona_agent import XiaonaAgent

# 初始化代理
agent = XiaonaAgent()

# 获取系统提示词
system_prompt = agent.get_system_prompt("patent_writing")
print(f"提示词长度: {len(system_prompt):,} 字符")

# 处理用户查询
response = agent.query(
    user_message="帮我分析这个技术交底书",
    scenario="patent_writing"
)

print(response["response"])
```

### 3. 场景切换

```python
# 切换到专利撰写模式
print(agent.switch_scenario("patent_writing"))

# 切换到意见答复模式
print(agent.switch_scenario("office_action"))

# 切换到通用协作模式
print(agent.switch_scenario("general"))
```

### 4. 查看状态

```python
status = agent.get_status()
print(json.dumps(status, ensure_ascii=False, indent=2))
```

---

## API使用说明

### XiaonaPromptLoader

提示词加载器，负责加载和管理所有提示词文件。

#### 方法

##### `load_all_prompts()`

加载所有提示词模块。

```python
loader = XiaonaPromptLoader()
prompts = loader.load_all_prompts()
```

**返回值**:
```python
{
    "foundation": "L1基础层内容...",
    "data_layer": "L2数据层内容...",
    "capabilities": "L3能力层内容...",
    "business": "L4业务层内容...",
    "hitl": "HITL协议内容..."
}
```

##### `get_full_prompt(task_type: str)`

获取指定场景的完整提示词。

**参数**:
- `task_type`: 场景类型
  - `"general"`: 通用模式（所有提示词）
  - `"patent_writing"`: 专利撰写模式（task_1_1~task_1_5）
  - `"office_action"`: 意见答复模式（task_2_1~task_2_4）

```python
# 专利撰写提示词
patent_prompt = loader.get_full_prompt("patent_writing")

# 意见答复提示词
office_prompt = loader.get_full_prompt("office_action")
```

##### `save_cache(cache_path: str = None)`

保存提示词到缓存文件。

```python
loader.save_cache()
# 或指定路径
loader.save_cache("/path/to/cache.json")
```

##### `load_cache(cache_path: str = None) -> bool`

从缓存加载提示词。

```python
success = loader.load_cache()
if success:
    print("从缓存加载成功")
```

---

### XiaonaAgent

小娜智能代理，集成提示词系统和对话管理。

#### 方法

##### `__init__(prompt_base_path: str = None, use_cache: bool = True)`

初始化代理。

```python
agent = XiaonaAgent(
    prompt_base_path="/path/to/prompts",
    use_cache=True
)
```

##### `query(user_message: str, scenario: str = "general", context: Dict = None)`

处理用户查询。

**参数**:
- `user_message`: 用户输入
- `scenario`: 业务场景
- `context`: 上下文信息（可选）

**返回值**:
```python
{
    "response": "小娜的回复",
    "scenario": "patent_writing",
    "need_human_input": false,
    "prompt_tokens": 123456,
    "metadata": {
        "timestamp": "2026-04-19T...",
        "scenario_type": "patent_writing",
        "context": {}
    }
}
```

##### `switch_scenario(new_scenario: str) -> str`

切换业务场景。

```python
message = agent.switch_scenario("patent_writing")
print(message)  # 显示切换确认消息
```

##### `get_status() -> Dict`

获取代理状态。

```python
status = agent.get_status()
```

##### `reset_conversation()`

重置对话历史。

```python
agent.reset_conversation()
```

##### `export_conversation(output_path: str = None)`

导出对话历史到JSON文件。

```python
agent.export_conversation("conversation_20251226.json")
```

---

## 平台数据集成

### 数据资产配置

小娜可以访问Athena平台的以下数据源：

#### Qdrant向量数据库

```python
vector_collections = {
    "patent_rules_complete": 2694,      # 专利法条
    "patent_decisions": 64815,           # 复审无效决定
    "patent_full_text": 13               # 专利全文
}

# 使用场景：语义相似度检索
# 示例：检索与"创造性判断"相关的复审决定
```

#### NebulaGraph知识图谱

```python
knowledge_graphs = {
    "patent_rules": {"nodes": 64913, "edges": 182722},
    "legal_kg": {"nodes": 22372, "edges": 71314},
    "patent_kg": {"nodes": 28000000, "edges": 85000000}
}

# 使用场景：关系推理、知识关联
# 示例：查询A26.3相关的所有法条
```

#### PostgreSQL专利数据库

```python
patent_database = {
    "total_patents": 28036796  # 中国专利总数
}

# 使用场景：精确检索、结构化查询
# 示例：按申请日、分类号检索专利
```

### 集成示例

```python
from xiaona_integration_demo import XiaonaPlatformIntegration

integration = XiaonaPlatformIntegration()

# 执行需要平台数据的任务
response = integration.execute_task_with_platform_data(
    task_type="patent_writing",
    user_input="请在patent_db中检索与'深度学习 物流分拣'相关的现有技术",
    platform_context={
        "task": "task_1_2",
        "data_sources": ["patent_db", "patent_decisions"]
    }
)

# 查看检索结果
if "platform_data" in response:
    print("向量检索结果:", response["platform_data"]["vector_search"])
    print("图谱查询结果:", response["platform_data"]["graph_query"])
    print("结构化查询结果:", response["platform_data"]["structured_query"])
```

---

## HITL人机协作

### 协作原则

1. **父亲做决策**: 所有关键决策由用户（爸爸）做出
2. **小娜提建议**: AI提供分析、建议、方案选项
3. **确认机制**: 重要操作需要用户明确确认
4. **可中断**: 用户可以随时中断和回退

### 交互点类型

#### 1. 决策确认点

```yaml
场景: 需要用户做出选择
示例: "是否接受这个修改建议？"
选项:
  A. 接受
  B. 拒绝
  C. 修改
```

#### 2. 信息收集点

```yaml
场景: 需要用户提供更多信息
示例: "请提供审查意见的具体驳回理由"
类型: 文本输入/文件上传/选择题
```

#### 3. 审核确认点

```yaml
场景: 需要用户审核输出结果
示例: "请审核权利要求书是否满足要求"
动作: 确认/修改/重新生成
```

#### 4. 偏好学习点

```yaml
场景: 记录用户偏好
示例: "您选择了策略A，我会记住这个偏好"
存储: 用户偏好配置文件
```

#### 5. 进度展示点

```yaml
场景: 展示任务进度
示例: "当前进度: 3/5 任务已完成"
可视化: 进度条/任务列表
```

### 中断和回退

```python
# 用户可以随时中断
agent.interrupt_task()

# 回退到上一步
agent.rollback_to_previous_step()

# 查看历史记录
agent.get_history()
```

---

## 性能优化

### 缓存策略

#### 提示词缓存

```python
# 首次加载会保存缓存
loader = XiaonaPromptLoader()
prompts = loader.load_all_prompts()
loader.save_cache()

# 后续加载从缓存读取，速度提升90%+
loader = XiaonaPromptLoader()
loader.load_cache()  # 快速加载
```

#### 缓存文件位置

```
prompts/.cache/prompts_cache.json
```

### 提示词长度优化

| 场景 | 提示词长度 | Token估算 |
|------|-----------|-----------|
| 通用模式 | ~252k字符 | ~63k tokens |
| 专利撰写 | ~122k字符 | ~30k tokens |
| 意见答复 | ~122k字符 | ~30k tokens |

**建议**: 对于频繁使用的场景，使用场景专用提示词以减少token消耗。

### 性能基准

```python
# 测试加载性能
import time

start = time.time()
loader = XiaonaPromptLoader()
loader.load_cache()  # 使用缓存
end = time.time()

print(f"加载时间: {end - start:.3f}秒")
# 预期: <0.5秒 (使用缓存)
```

---

## 故障排查

### 常见问题

#### 1. 提示词文件未找到

**错误**: `❌ L1基础层 (未找到)`

**原因**: 提示词文件路径不正确

**解决**:
```python
# 指定正确的提示词根目录
loader = XiaonaPromptLoader(
    base_path="/Users/xujian/Athena工作平台/prompts"
)
```

#### 2. 缓存加载失败

**错误**: `❌ 缓存加载失败`

**原因**: 缓存文件损坏或版本不匹配

**解决**:
```python
# 删除缓存，重新加载
import os
cache_path = "/Users/xujian/Athena工作平台/prompts/.cache/prompts_cache.json"
if os.path.exists(cache_path):
    os.remove(cache_path)

# 重新加载
loader = XiaonaPromptLoader()
loader.load_all_prompts()
loader.save_cache()
```

#### 3. HITL交互检测失效

**错误**: 需要人机交互但`need_human_input=False`

**原因**: 关键词检测规则需要调整

**解决**:
```python
# 扩展HITL关键词
def _check_hitl_required(self, message: str, scenario: str) -> bool:
    hitl_keywords = [
        "确认", "修改", "选择", "决定", "审核",
        "是否", "是否接受", "是否同意", "希望如何",
        # 添加更多关键词
        "请您", "请确认", "您希望", "您认为"
    ]
    return any(keyword in message for keyword in hitl_keywords)
```

---

## 附录

### 完整示例代码

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小娜完整使用示例
"""

from xiaona_agent import XiaonaAgent
from xiaona_integration_demo import XiaonaPlatformIntegration
import json

def main():
    # 1. 初始化代理
    agent = XiaonaAgent()

    # 2. 查看状态
    status = agent.get_status()
    print("代理状态:", json.dumps(status, ensure_ascii=False, indent=2))

    # 3. 切换到专利撰写模式
    print(agent.switch_scenario("patent_writing"))

    # 4. 执行任务
    response = agent.query(
        user_message="帮我分析这个技术交底书的核心创新点",
        scenario="patent_writing",
        context={"task": "task_1_1"}
    )

    print("小娜回复:", response["response"])
    print("需要人机交互:", response["need_human_input"])

    # 5. 使用平台数据
    integration = XiaonaPlatformIntegration()
    response = integration.execute_task_with_platform_data(
        task_type="patent_writing",
        user_input="检索现有技术",
        platform_context={"task": "task_1_2"}
    )

    if "platform_data" in response:
        print("平台数据:", response["platform_data"])

    # 6. 导出对话历史
    agent.export_conversation("xiaona_conversation.json")

if __name__ == "__main__":
    main()
```

---

## 版本历史

### v4.0 (2026-04-19)

- ✅ 完成四层提示词架构设计
- ✅ 完成10大能力提示词
- ✅ 完成9个业务场景提示词
- ✅ 实现HITL人机协作协议
- ✅ 集成Athena平台数据源
- ✅ 实现提示词缓存机制
- ✅ 实现场景切换功能
- ✅ 实现对话历史管理

---

## 联系支持

如有问题，请联系：
- **设计者**: 小诺·双鱼公主 v4.0.0
- **邮箱**: xujian519@gmail.com
- **项目**: Athena工作平台

---

> **小娜** - 您的专利法律AI助手 🌟
