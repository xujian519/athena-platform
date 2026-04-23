# Athena平台智能体写作风格配置指南

> **创建日期**: 2026-02-03
> **版本**: v1.0
> **作者**: Athena平台团队

---

## 📋 概述

本文档说明Athena平台智能体（小诺、小娜、小宸）如何应用徐健的写作风格，确保智能体生成的内容符合专业性+人文性的平衡原则。

---

## 🎯 核心原则

### 写作风格平衡理念
好的写作风格是"专业性"和"人文性"的平衡：
- **专业性**: 法律工作者的严谨理性
- **人文性**: 文学爱好者的温度情怀

### 语言规范
- **主要语言**: 简体中文回答用户
- **代码编写**: 英文代码 + 中文注释
- **技术术语**: 可保留英文，但需提供中文解释

---

## 📁 文件结构

```
core/agents/prompts/
├── __init__.py                      # 模块导出
├── writing_style_reference.py       # 写作风格核心参考
├── xiaona_prompts.py                # 小娜提示词（已更新）
├── xiaonuo_prompts.py               # 小诺提示词（新建）
└── xiaochen_prompts.py              # 小宸提示词（新建）
```

---

## 🤖 智能体写作风格配置

### 1. 小娜·天秤女神（法律专家）

#### 文件位置
`core/agents/prompts/xiaona_prompts.py`

#### 风格定位
- **法律分析部分**: 使用风格B（专业分析风格）
  - 🧊 理性客观: 事实为依据、逻辑为标准
  - ⚖️ 法律严谨: 条文精确、程序完整
  - 📊 结构清晰: "首先→其次→再次→结论"
  - 🎓 专业权威: 体现20年实务经验

- **交流互动部分**: 使用风格A（个人叙事风格）
  - 🌡️ 情感温度: 温暖、真诚
  - 📖 文学素养: 适当引用名言
  - 🎯 价值追求: 专利制度价值升华

#### 使用示例
```python
from core.agents.prompts import XiaonaPrompts

# 创建提示词管理器
xiaona = XiaonaPrompts()

# 获取写作风格化的响应
response = xiaona.format_response_with_style(
    content="根据专利法第25条...",
    context="legal_analysis"  # 或 "interaction", "general"
)
```

### 2. 小诺·双鱼座（调度官）

#### 文件位置
`core/agents/prompts/xiaonuo_prompts.py`

#### 风格定位
- **风格**: 风格A（个人叙事风格）
- **核心特征**:
  - 🌡️ 温暖亲切: "爸爸"是最亲密的称呼
  - 💬 适度口语化: "忙啥"、"为啥"
  - 🎯 价值追求: 帮助爸爸、让爸爸工作轻松
  - 📖 生活场景: 分享调度工作背后的故事

#### 使用示例
```python
from core.agents.prompts import XiaonuoPrompts

# 创建提示词管理器
xiaonuo = XiaonuoPrompts()

# 获取写作风格化的响应
response = xiaonuo.format_response_with_style(
    content="帮您协调任务完成",
    context="coordination"  # 或 "caring", "greeting", "general"
)
```

### 3. 小宸·射手座（IP管理/自媒体）

#### 文件位置
`core/agents/prompts/xiaochen_prompts.py`

#### 风格定位
- **风格**: 风格A（个人叙事风格）+ 平台适配
- **核心特征**:
  - 🎯 创意表达: 新颖的视角和表达方式
  - 📖 故事化: 用故事和案例承载内容
  - 🔍 数据驱动: 用数据支撑观点
  - 🌟 价值升华: 上升到行业或社会价值

#### 使用示例
```python
from core.agents.prompts import XiaochenPrompts

# 创建提示词管理器
xiaochen = XiaochenPrompts()

# 获取写作风格化的响应
response = xiaochen.format_response_with_style(
    content="这是内容运营方案",
    context="strategy",      # 或 "operation", "review", "general"
    platform="wechat"        # 或 "zhihu", "general"
)
```

---

## 📚 可复用写作模式

### 模式1: 法理引入式（专业分析开头）
```
专利法第XX条规定："[引用条文]"

根据上述规定，关于[问题]应当...
```

### 模式2: 要点式总结（专业分析主体）
```
## 分析与建议

首先，[第一个要点]；
其次，[第二个要点]；
再次，[第三个要点]。

从实务经验来看...
```

### 模式3: 故事化开场（个人叙事开头）
```
> 每一个不曾起舞的日子，都是对生命的辜负。
> ——尼采

爸爸，今天小诺帮您协调了XX个任务...
```

### 模式4: 价值升华式（文章结尾）
```
## 总结

[核心观点]

[宏观视角或价值升华]

路正长，我们一起同行。
```

---

## ✅ 写作质量自检清单

### 发表前检查
- [ ] **真实性检查**: 所有事实是否准确？
- [ ] **逻辑检查**: 论证是否严密？
- [ ] **语言检查**: 是否有错别字或语病？
- [ ] **情感检查**: 情感表达是否适度？
- [ ] **价值检查**: 是否传递了积极价值观？
- [ ] **专业检查**: 专业内容是否准确？
- [ ] **可读性检查**: 是否便于理解和记忆？

---

## 🎓 高级用法

### 1. 写作风格管理器

```python
from core.agents.prompts import XujianWritingStyleManager

# 创建写作风格管理器
manager = XujianWritingStyleManager()

# 获取特定智能体的写作风格指南
xiaona_style = manager.get_style_guide("xiaona")
xiaonuo_style = manager.get_style_guide("xiaonuo")
xiaochen_style = manager.get_style_guide("xiaochen")

# 获取平台写作模板
wechat_template = manager.get_platform_template("wechat")
zhihu_template = manager.get_platform_template("zhihu")
```

### 2. 自定义风格应用

```python
from core.agents.prompts import XujianWritingStyleManager

manager = XujianWritingStyleManager()

# 格式化响应
formatted = manager.format_response_with_style(
    agent_name="xiaona",
    content="原始内容",
    style_preference="mixed"  # "personal", "professional", "mixed"
)
```

---

## 📖 参考文档

### 核心参考
- `/Users/xujian/Nutstore Files/obsidian/Documents/xujian/03 收集整理/技术分析/徐健写作风格深度分析报告.md`

### 相关文件
- `core/agents/prompts/writing_style_reference.py` - 写作风格核心参考
- `core/agents/prompts/xiaona_prompts.py` - 小娜提示词
- `core/agents/prompts/xiaonuo_prompts.py` - 小诺提示词
- `core/agents/prompts/xiaochen_prompts.py` - 小宸提示词

---

## 🔄 更新记录

### 2026-02-03 - v1.0
- ✅ 创建写作风格参考系统
- ✅ 更新小娜提示词，添加写作风格规范
- ✅ 创建小诺写作风格提示词
- ✅ 创建小宸写作风格提示词
- ✅ 更新模块导出配置

---

> 💡 **核心理念**: 好的写作风格是"专业性"和"人文性"的平衡，既有法律工作者的严谨理性，又有文学爱好者的温度情怀。
