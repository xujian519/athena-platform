---
name: "skill_name"
display_name: "技能显示名称"
description: "技能的详细描述，说明它的功能和用途"

version: "1.0.0"
author: "Your Name"
license: "MIT"

category: "custom"  # 可选: patent_analysis, legal_research, document_generation, data_visualization, web_search, custom

tags:
  - "tag1"
  - "tag2"

dependencies: []  # 依赖的其他技能名称列表

parameters:
  required:
    - "param1"    # 必需参数名称
  optional:
    - "param2"    # 可选参数名称
  types:
    param1: "str"     # 参数类型
    param2: "int"
  defaults:
    param2: 10        # 默认值

examples:
  - description: "示例1描述"
    input:
      param1: "value1"
    output:
      result: "expected output"

enabled: true
---

# 技能名称

## 功能描述

详细描述这个技能的功能和用途。

## 使用方法

说明如何使用这个技能，包括参数说明和返回值格式。

## 参数说明

### param1 (必需)
- 类型: string
- 描述: 参数1的描述

### param2 (可选)
- 类型: integer
- 描述: 参数2的描述
- 默认值: 10

## 返回值

描述技能执行后的返回值格式和含义。

## 示例

```python
# 使用示例
result = await skill.execute(
    param1="value1",
    param2=20
)
```

## 注意事项

任何需要注意的事项或限制。

## 实现说明

如果这个技能有 Python 实现，在这里说明实现细节。

## 更新日志

### 1.0.0 (2024-01-01)
- 初始版本
