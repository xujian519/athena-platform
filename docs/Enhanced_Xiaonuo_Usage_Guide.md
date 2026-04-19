# Enhanced Xiaonuo 使用指南

**版本**: v2.0.0_enhanced
**状态**: ✅ 完全可用
**最后更新**: 2026-04-18

---

## 🚀 快速开始

### 1. 导入和创建实例

```python
from core.agents.xiaonuo.enhanced_xiaonuo import EnhancedXiaonuo

# 创建实例
agent = EnhancedXiaonuo()

# 查看可用能力
print(agent.enhanced_capabilities)
# 输出: ['记忆整合', '元学习优化', '自适应改进', '因果推理', '自我反思循环']
```

### 2. 基本使用

```python
# 处理用户输入
response = await agent.process_input("你好，请介绍一下你自己")
print(response)
# 输出: 我是XiaonuoAgent统一智能体,整合了媒体运营、情感关怀和平台协调的全面能力。💖
```

### 3. 带反思的完整处理

```python
# 启用反思和学习
response = await agent.process_input(
    "请分析这个专利的创造性",
    enable_reflection=True,   # 启用反思
    enable_learning=True,     # 启用学习
    include_performance=True  # 包含性能信息
)
```

---

## 📖 核心功能

### 1. 反思引擎 (ReflectionEngineV5)

**功能**: 自我反思和改进

```python
from core.intelligence.reflection_engine_v5 import ReflectionType, ThoughtStep
from datetime import datetime

# 创建思维链
thought_chain = [
    ThoughtStep(
        step_id="perception",
        timestamp=datetime.now(),
        content="感知用户输入",
        reasoning_type="perception",
        confidence=0.95,
    ),
    ThoughtStep(
        step_id="analysis",
        timestamp=datetime.now(),
        content="分析内容",
        reasoning_type="analysis",
        confidence=0.88,
    ),
]

# 执行反思
loop = await agent.reflection_engine_v5.reflect_with_loop(
    original_input="分析专利权利要求",
    output="该专利的权利要求涉及...",
    context={"patent_id": "CN123456789A"},
    thought_chain=thought_chain,
    reflection_types=[ReflectionType.OUTPUT, ReflectionType.PROCESS, ReflectionType.CAUSAL],
)

# 查看结果
print(f"循环ID: {loop.loop_id}")
print(f"因果因子数: {len(loop.causal_factors)}")
print(f"行动项数: {len(loop.action_items)}")
```

**输出示例**:
```
循环ID: loop_20260418_110903_cdf0d133
因果因子数: 4
行动项数: 4

行动项:
  - 改进relevance: 当前分数0.60 (优先级: high)
  - 解决因果问题: 推理步骤跳跃 (优先级: high)
  - 改进accuracy: 当前分数0.75 (优先级: medium)
```

### 2. 记忆整合 (MemoryConsolidationSystem)

**功能**: 将短期记忆转化为长期知识

```python
# 执行多次交互以产生记忆
await agent.process_input("什么是专利?")
await agent.process_input("如何申请专利?")
await agent.process_input("专利的保护期限是多久?")

# 执行记忆整合
report = await agent.memory_consolidation.consolidate_memories(force=True)

print(f"状态: {report.get('status')}")
print(f"整合数量: {report.get('consolidated_count', 0)}")
print(f"发现模式: {report.get('patterns_discovered', 0)}")
```

### 3. 元学习 (EnhancedMetaLearningEngine)

**功能**: 自动优化学习策略

```python
# 元学习会自动在每次交互后执行
response = await agent.process_input(
    "用户问题",
    enable_learning=True  # 启用学习
)

# 查看学习统计
print(f"学习周期: {agent.performance_tracker['learning_cycles']}")
```

### 4. 统计信息

**智能体统计**:
```python
print(f"版本: {agent.version}")
print(f"代理ID: {agent.agent_id}")
print(f"交互次数: {agent.performance_tracker['interactions']}")
print(f"反思次数: {agent.performance_tracker['reflections_performed']}")
print(f"学习周期: {agent.performance_tracker['learning_cycles']}")
```

**反思引擎统计**:
```python
stats = await agent.reflection_engine_v5.get_statistics()
print(f"总反思数: {stats['stats']['total_reflections']}")
print(f"因果分析数: {stats['stats']['causal_analyses']}")
print(f"行动项创建: {stats['stats']['action_items_created']}")
print(f"行动项完成: {stats['stats']['action_items_completed']}")
```

---

## 🎯 实际应用场景

### 场景1: 专利分析

```python
# 分析专利
response = await agent.process_input(
    "请分析专利CN123456789A的创造性",
    enable_reflection=True,
)

# 执行深度反思
loop = await agent.reflection_engine_v5.reflect_with_loop(
    original_input="分析专利创造性",
    output=response,
    context={"patent_id": "CN123456789A", "domain": "patent_law"},
    reflection_types=[ReflectionType.OUTPUT, ReflectionType.CAUSAL],
)

# 查看改进建议
for action in loop.action_items:
    print(f"- {action.description}")
```

### 场景2: 持续改进

```python
# 第一轮处理
loop1 = await agent.reflection_engine_v5.reflect_with_loop(
    original_input="任务",
    output="初步输出",
    context={"iteration": 1},
)

# 应用改进后，测量效果
improvement = await agent.reflection_engine_v5.measure_improvement(
    loop_id=loop1.loop_id,
    new_output="改进后的输出",
    new_context={"iteration": 2},
)

print(f"改进分数: {improvement:.3f}")
```

### 场景3: 知识整合

```python
# 收集多次交互的知识
for question in [
    "什么是专利?",
    "专利的类型有哪些?",
    "如何申请专利?",
]:
    await agent.process_input(question)

# 执行记忆整合
report = await agent.memory_consolidation.consolidate_memories(force=True)

# 整合后的知识可用于未来查询
response = await agent.process_input("总结一下关于专利的知识")
```

---

## ⚙️ 配置选项

```python
# 查看当前配置
print(agent.config)

# 修改配置
agent.config.update({
    "enable_reflection": True,      # 启用反思
    "enable_learning": True,        # 启用学习
    "enable_consolidation": True,   # 启用记忆整合
    "consolidation_interval_hours": 6,  # 整合间隔（小时）
    "reflection_threshold": 0.8,    # 反思阈值
    "learning_sample_size": 5,      # 学习样本大小
})
```

---

## 📊 性能监控

```python
# 包含性能信息的响应
response = await agent.process_input(
    "问题",
    include_performance=True,
)

# 响应会包含处理时间，例如:
# "回答内容...\n\n⏱️ 处理时间: 0.05s"
```

---

## 🔄 反思类型

| 反思类型 | 说明 | 使用场景 |
|---------|------|---------|
| `ReflectionType.OUTPUT` | 输出反思 | 评估输出质量 |
| `ReflectionType.PROCESS` | 过程反思 | 分析思维过程 |
| `ReflectionType.CAUSAL` | 因果反思 | 识别问题根因 |
| `ReflectionType.STRATEGIC` | 战略反思 | 长期策略规划 |

**使用示例**:
```python
# 组合多种反思类型
loop = await agent.reflection_engine_v5.reflect_with_loop(
    original_input="...",
    output="...",
    context={},
    reflection_types=[
        ReflectionType.OUTPUT,
        ReflectionType.PROCESS,
        ReflectionType.CAUSAL,
    ],
)
```

---

## ⚠️ 注意事项

### 可选依赖

某些功能可能不可用，这取决于依赖模块是否安装：

```python
# 检查功能是否可用
if agent.memory_consolidation is not None:
    # 记忆整合可用
    await agent.memory_consolidation.consolidate_memories()
else:
    print("记忆整合不可用")

if agent.meta_learning is not None:
    # 元学习可用
    await agent.meta_learning.learn_from_few_shots(task)
else:
    print("元学习不可用")
```

### 性能考虑

- **反思**: 会增加处理时间，建议在需要时启用
- **学习**: 需要累积足够样本后才有效果
- **记忆整合**: 建议定期执行，而非每次交互后执行

### 错误处理

```python
try:
    response = await agent.process_input("问题")
except Exception as e:
    logger.error(f"处理失败: {e}")
    # 使用备用方案或返回错误信息
```

---

## 🧪 测试和验证

运行演示脚本:
```bash
python3 examples/enhanced_xiaonuo_demo.py
```

运行验证脚本:
```bash
python3 tests/test_manual_fix_verification.py
```

---

## 📚 相关文档

- **修复报告**: `reports/manual_fix_completion_report.md`
- **验证报告**: `reports/evaluation_reflection_verification_report_20260418.md`
- **解决方案**: `docs/solutions/known_limitations_solution.md`
- **快速指南**: `docs/solutions/QUICK_FIX_GUIDE.md`

---

## 🎉 总结

Enhanced Xiaonuo v2.0 现已完全可用，具有以下核心能力：

- ✅ **记忆整合** - 短期记忆转化为长期知识
- ✅ **元学习优化** - 自动优化学习策略
- ✅ **因果推理** - 识别问题根本原因
- ✅ **自我反思循环** - 持续自我改进
- ✅ **自适应改进** - 自动应用反思建议

**所有功能已验证可用！** 🚀

---

**创建时间**: 2026-04-18
**维护者**: Athena AI System
