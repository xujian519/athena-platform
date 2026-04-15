---
name: "hello_world"
display_name: "Hello World"
description: "一个简单的示例技能，向世界问好"

version: "1.0.0"
author: "Athena Team"
license: "MIT"

category: "custom"

tags:
  - "demo"
  - "example"
  - "hello"

dependencies: []

parameters:
  required:
    - "name"
  optional:
    - "greeting"
  types:
    name: "str"
    greeting: "str"
  defaults:
    greeting: "Hello"

examples:
  - description: "基本问候"
    input:
      name: "World"
    output:
      message: "Hello, World!"
  - description: "自定义问候"
    input:
      name: "Athena"
      greeting: "Welcome"
    output:
      message: "Welcome, Athena!"

enabled: true
---

# Hello World 技能

这是一个简单的示例技能，用于演示 Athena 技能系统的使用方法。

## 功能

向指定目标发送问候消息。

## 参数说明

### name (必需)
- 类型: string
- 描述: 要问候的对象名称

### greeting (可选)
- 类型: string
- 描述: 问候语
- 默认值: "Hello"

## 返回值

包含问候消息的字典：
```python
{
    "message": "问候内容",
    "greeting": "使用的问候语",
    "name": "问候的对象"
}
```

## 使用示例

```python
from core.skills import SkillManager, SkillExecutor

# 创建管理器和执行器
manager = SkillManager()
executor = SkillExecutor(registry=manager.registry)

# 加载技能
await manager.load_all()

# 执行技能
result = await executor.execute(
    "hello_world",
    name="World"
)

print(result.data)  # {'message': 'Hello, World!', ...}
```
