# PatentDraftingPrompts 使用指南

> **版本**: v2.0
> **最后更新**: 2026-04-23

---

## 快速开始

### 基本使用

```python
from core.agents.xiaona.patent_drafting_prompts import PatentDraftingPrompts

# 1. 获取系统提示词
prompt_config = PatentDraftingPrompts.get_prompt("disclosure_analysis")
system_prompt = prompt_config["system_prompt"]

# 2. 格式化用户提示词
user_prompt = PatentDraftingPrompts.format_user_prompt(
    "disclosure_analysis",
    disclosure_data='{"title": "测试发明"}'
)

# 3. 调用LLM
response = await call_llm(system_prompt, user_prompt)
```

### 与PatentDraftingProxy集成

```python
from core.agents.xiaona.patent_drafting_proxy import PatentDraftingProxy

# 自动使用优化后的提示词
agent = PatentDraftingProxy()
result = await agent.analyze_disclosure(disclosure_data)
```

---

## 可用任务

| 任务名称 | 任务描述 | 输入 | 输出 |
|---------|---------|------|------|
| `disclosure_analysis` | 技术交底书分析 | 技术交底书 | 分析报告(JSON) |
| `patentability_assessment` | 可专利性评估 | 交底书+现有技术 | 评估报告(JSON) |
| `specification_draft` | 说明书撰写 | 交底书+可专利性 | 说明书文本 |
| `claims_draft` | 权利要求撰写 | 交底书+说明书 | 权利要求书文本 |
| `optimize_protection_scope` | 保护范围优化 | 权利要求+现有技术 | 优化建议(JSON) |
| `adequacy_review` | 充分公开审查 | 说明书+权利要求 | 审查报告(JSON) |
| `error_detection` | 常见错误检测 | 说明书+权利要求 | 错误报告(JSON) |

---

## Prompt优化特性

### ✅ Few-Shot示例

每个prompt包含2-3个精心设计的示例:
- 正面示例: 展示正确做法
- 反面示例: 展示常见错误
- 对比示例: 不同场景差异

### ✅ CoT推理步骤

每个prompt包含4-5步推理:
1. 理解输入
2. 分析结构
3. 执行任务
4. 验证输出

### ✅ 明确的JSON Schema

每个prompt都有详细的输出格式定义:
```json
{
    "disclosure_id": "交底书ID",
    "quality_score": 0.75,
    "quality_level": "良好"
}
```

### ✅ 详细注意事项

每个prompt都包含:
- 格式要求
- 质量标准
- 常见错误
- 最佳实践

---

## 示例输出

### 技术交底书分析

```json
{
    "disclosure_id": "EXAMPLE_001",
    "title": "一种可调节高度的物流传送装置",
    "completeness": {
        "title": {"exists": true, "quality": "high"},
        "technical_solution": {"exists": true, "quality": "medium"}
    },
    "missing_fields": [],
    "weak_fields": ["background_art"],
    "core_innovations": [
        "创新点1:丝杆螺母传动机构实现高度调节",
        "创新点2:电机驱动实现自动化控制"
    ],
    "quality_score": 0.86,
    "quality_level": "良好"
}
```

### 可专利性评估

```json
{
    "disclosure_id": "EXAMPLE_003",
    "novelty_assessment": {
        "score": 0.85,
        "level": "高",
        "conclusion": "具有新颖性"
    },
    "inventiveness_assessment": {
        "score": 0.78,
        "level": "中",
        "conclusion": "具有创造性"
    },
    "practicality_assessment": {
        "score": 0.95,
        "level": "高",
        "conclusion": "具有实用性"
    },
    "overall_assessment": {
        "score": 0.86,
        "patentability": "可专利",
        "success_probability": 0.82
    }
}
```

---

## 优化对比

| 指标 | v1.0 | v2.0 | 提升 |
|-----|------|------|------|
| Prompt长度 | ~150词 | ~1200词 | +700% |
| Few-shot示例 | 0个 | 2-3个 | ∞ |
| CoT推理步骤 | 无 | 4-5步 | 新增 |
| JSON输出稳定性 | ~60% | ~90% | +50% |
| 任务准确性 | ~70% | ~85% | +21% |

---

## API参考

### `get_prompt(task_name: str) -> Dict`

获取指定任务的提示词配置。

**参数**:
- `task_name`: 任务名称

**返回**:
```python
{
    "task_name": "任务名称",
    "version": "v2.0",
    "description": "任务描述",
    "system_prompt": "系统提示词",
    "user_template": "用户提示词模板"
}
```

### `format_user_prompt(task_name: str, **kwargs) -> str`

格式化用户提示词。

**参数**:
- `task_name`: 任务名称
- `**kwargs`: 模板变量
    - `disclosure_data`: 技术交底书数据(JSON字符串)
    - `prior_art`: 现有技术(JSON字符串)
    - `specification`: 说明书(文本)
    - `claims`: 权利要求书(文本)

**返回**: 格式化后的提示词字符串

### `list_tasks() -> List[str]`

列出所有可用任务。

**返回**: 任务名称列表

---

## 最佳实践

### 1. 输入数据质量

确保输入数据完整和准确:
```python
# ✅ 好的输入
disclosure_data = {
    "title": "一种智能水杯",
    "technical_field": "智能家居设备",
    "technical_solution": "包括温度传感器和显示屏...",
    "technical_problem": "解决水温显示问题",
    "beneficial_effects": "提高使用便利性"
}

# ❌ 差的输入
disclosure_data = {
    "title": "智能水杯"
    # 缺少其他必要信息
}
```

### 2. JSON格式化

确保JSON正确格式化:
```python
import json

# ✅ 正确
disclosure_data = json.dumps(disclosure_data, ensure_ascii=False, indent=2)

# ❌ 错误
disclosure_data = str(disclosure_data)  # 不是有效的JSON
```

### 3. 输出解析

使用try-except处理JSON解析:
```python
try:
    result = json.parse(response)
except json.JSONDecodeError as e:
    logger.error(f"JSON解析失败: {e}")
    # 使用降级方案
```

---

## 故障排除

### 问题1: JSON解析失败

**原因**: LLM输出包含额外文字

**解决方案**:
```python
# 提取JSON
import re
json_match = re.search(r'```json\s*([\s\S]*?)```', response)
if json_match:
    json_str = json_match.group(1).strip()
else:
    json_str = response.strip()

result = json.loads(json_str)
```

### 问题2: Prompt过长超出token限制

**解决方案**:
1. 减少Few-shot示例数量
2. 简化CoT推理步骤
3. 缩短输入数据长度

### 问题3: 输出质量不稳定

**解决方案**:
1. 增加temperature参数(0.1-0.3)
2. 使用更好的模型(GPT-4, Claude-3)
3. 添加更多的Few-shot示例

---

## 更多资源

- [优化报告](../reports/PATENT_DRAFTING_PROMPTS_V2_REPORT.md) - 详细的优化报告
- [PatentDraftingProxy代码](../../core/agents/xiaona/patent_drafting_proxy.py) - 代理实现
- [PatentDraftingPrompts代码](../../core/agents/xiaona/patent_drafting_prompts.py) - 提示词实现

---

**维护者**: 徐健 (xujian519@gmail.com)
**最后更新**: 2026-04-23
