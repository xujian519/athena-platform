# patent_analysis工具快速使用指南

## 概述

**patent_analysis** 是Athena平台的专利内容分析和创造性评估工具，提供4种分析类型：

- **basic**: 基础技术特征提取
- **creativity**: 创造性评估（0-1评分）
- **novelty**: 新颖性判断（0-1评分）
- **comprehensive**: 综合分析（整合所有维度）

---

## 快速开始

### 1. 导入工具

```python
from core.tools.unified_registry import get_unified_registry

registry = get_unified_registry()
patent_analysis = registry.get('patent_analysis')
```

### 2. 基础分析

```python
result = patent_analysis(
    patent_id='CN123456789A',
    title='一种基于深度学习的图像识别方法',
    abstract='本发明公开了一种基于深度学习的图像识别方法，包括：获取待识别图像；对图像进行预处理；将预处理后的图像输入到深度卷积神经网络模型中；通过模型输出图像识别结果。',
    analysis_type='basic'
)

print(result['results']['analysis_summary'])
# 输出: 从专利文本中提取了 3 个技术特征
```

### 3. 创造性评估

```python
result = patent_analysis(
    patent_id='CN123456789A',
    title='一种基于深度学习的图像识别方法',
    abstract='本发明公开了一种基于深度学习的图像识别方法...',
    claims=['权利要求1...', '权利要求2...'],
    analysis_type='creativity'
)

print(f"创造性评分: {result['results']['creativity_score']:.2f}")
print(f"技术强度: {result['results']['technical_strength']}")
```

### 4. 新颖性判断

```python
result = patent_analysis(
    patent_id='CN123456789A',
    title='一种基于深度学习的图像识别方法',
    abstract='本发明公开了一种基于深度学习的图像识别方法...',
    analysis_type='novelty'
)

print(f"新颖性评分: {result['results']['novelty_score']:.2f}")
print(f"相似专利数量: {result['results']['similar_patents_count']}")
```

### 5. 综合分析（推荐）

```python
result = patent_analysis(
    patent_id='CN123456789A',
    title='一种基于深度学习的图像识别方法',
    abstract='本发明公开了一种基于深度学习的图像识别方法，包括：获取待识别图像；对图像进行预处理；将预处理后的图像输入到深度卷积神经网络模型中；通过模型输出图像识别结果。该方法能够提高图像识别的准确率和效率。',
    claims=[
        '一种基于深度学习的图像识别方法，其特征在于，包括：获取待识别图像；对图像进行预处理；将预处理后的图像输入到深度卷积神经网络模型中；通过模型输出图像识别结果。'
    ],
    analysis_type='comprehensive'
)

# 查看专利性评分
score = result['results']['patentability_score']
print(f"专利性评分: {score:.2f}/1.0")

# 查看建议
print("\n建议:")
for rec in result['results']['recommendations']:
    print(f"  {rec}")
```

**输出示例**:
```
专利性评分: 0.87/1.0

建议:
  ✅ 专利性评分优秀，建议申请专利
  ✅ 创造性和新颖性表现良好
  建议：尽快完善申请文件并提交
```

---

## 参数说明

### 必需参数

| 参数 | 类型 | 说明 | 示例 |
|-----|------|------|------|
| `patent_id` | str | 专利号/申请号 | `'CN123456789A'` |
| `title` | str | 专利标题 | `'一种基于深度学习的图像识别方法'` |
| `abstract` | str | 专利摘要 | `'本发明公开了...'` |

### 可选参数

| 参数 | 类型 | 说明 | 默认值 |
|-----|------|------|-------|
| `claims` | list[str] | 权利要求列表 | `None` |
| `description` | str | 说明书全文 | `None` |
| `analysis_type` | str | 分析类型 | `'comprehensive'` |

**analysis_type可选值**:
- `"basic"`: 基础分析（技术特征提取）
- `"creativity"`: 创造性评估
- `"novelty"`: 新颖性判断
- `"comprehensive"`: 综合分析（默认）

---

## 返回结果格式

### 成功响应

```python
{
    'success': True,
    'patent_id': 'CN123456789A',
    'analysis_type': 'comprehensive',
    'execution_time': 0.05,  # 执行时间（秒）
    'results': {
        'patentability_score': 0.87,
        'analysis_summary': '综合专利性评分: 0.87/1.0',
        'recommendations': [
            '✅ 专利性评分优秀，建议申请专利',
            '✅ 创造性和新颖性表现良好',
            '建议：尽快完善申请文件并提交'
        ],
        # ... 其他分析结果
    }
}
```

### 失败响应

```python
{
    'success': False,
    'patent_id': 'CN123456789A',
    'analysis_type': 'comprehensive',
    'execution_time': 0.02,
    'error': '专利分析失败: 详细错误信息',
    'results': None
}
```

---

## 在Agent中使用

### XiaonaAgent集成

```python
from core.agents.xiaona_agent import XiaonaAgent

agent = XiaonaAgent()

# 自然语言调用
response = agent.process(
    "帮我分析专利CN123456789A的创造性"
)

# Agent会自动调用patent_analysis工具
print(response)
```

### 小诺任务调度

```python
from core.agents.xiaonuo_agent import XiaonuoAgent

agent = XiaonuoAgent()

# 创建专利分析任务
task = {
    'type': 'patent_analysis',
    'patent_id': 'CN123456789A',
    'analysis_type': 'comprehensive'
}

result = agent.execute_task(task)
```

---

## 最佳实践

### 1. 选择合适的分析类型

| 场景 | 推荐分析类型 | 原因 |
|-----|------------|------|
| 快速技术特征提取 | `basic` | 速度快，结果简洁 |
| 专利申请前评估 | `creativity` | 重点关注创造性 |
| 审查意见答复 | `novelty` | 重点关注新颖性 |
| 全面评估 | `comprehensive` | 整合所有维度 |

### 2. 提供完整的输入信息

```python
# ✅ 推荐：提供完整信息
result = patent_analysis(
    patent_id='CN123456789A',
    title='...',
    abstract='...',
    claims=['权利要求1', '权利要求2', ...],  # 提供权利要求
    description='说明书全文...',  # 提供说明书
    analysis_type='comprehensive'
)

# ⚠️ 不推荐：信息不完整
result = patent_analysis(
    patent_id='CN123456789A',
    title='...',
    abstract='...',
    # 缺少claims和description
    analysis_type='comprehensive'
)
```

### 3. 处理分析结果

```python
result = patent_analysis(...)

if result['success']:
    # 分析成功
    score = result['results']['patentability_score']

    if score >= 0.8:
        print("✅ 专利性评分优秀，建议申请")
    elif score >= 0.6:
        print("⚠️ 专利性评分良好，需要补充材料")
    else:
        print("❌ 专利性评分较低，不建议申请")
else:
    # 分析失败
    print(f"❌ 分析失败: {result['error']}")
```

---

## 常见问题

### Q1: 为什么创造性评分显示"简化"？

**A**: 知识图谱分析器不可用（缺少依赖），工具自动降级到简化评估算法。这不影响核心功能，但评分精度可能降低。

**解决方法**:
```bash
pip install matplotlib
```

### Q2: 为什么新颖性判断没有返回相似专利？

**A**: 向量检索服务可能不可用，工具自动降级到基于关键词的简化判断。

**解决方法**: 检查向量搜索工具是否正常：
```python
from core.tools.unified_registry import get_unified_registry
registry = get_unified_registry()
vs = registry.get('vector_search')
print(vs)  # 应该返回函数，而不是None
```

### Q3: 如何批量分析多个专利？

**A**: 使用循环或异步处理：

```python
patents = [
    {'patent_id': 'CN001', 'title': '...', 'abstract': '...'},
    {'patent_id': 'CN002', 'title': '...', 'abstract': '...'},
    {'patent_id': 'CN003', 'title': '...', 'abstract': '...'},
]

results = []
for patent in patents:
    result = patent_analysis(
        patent_id=patent['patent_id'],
        title=patent['title'],
        abstract=patent['abstract'],
        analysis_type='comprehensive'
    )
    results.append(result)

# 按专利性评分排序
results.sort(key=lambda x: x['results']['patentability_score'], reverse=True)
```

---

## 性能指标

| 分析类型 | 平均响应时间 | 内存占用 |
|---------|------------|---------|
| basic | ~0.01秒 | <10MB |
| creativity | ~0.02秒 | <20MB |
| novelty | ~0.01秒 | <15MB |
| comprehensive | ~0.05秒 | <50MB |

---

## 相关文档

- [验证报告](../reports/PATENT_ANALYSIS_TOOL_VERIFICATION_REPORT_20260419.md)
- [工具系统API](../api/UNIFIED_TOOL_REGISTRY_API.md)
- [专利分析最佳实践](../guides/PATENT_ANALYSIS_BEST_PRACTICES.md)

---

**更新日期**: 2026-04-19
**作者**: Athena平台团队
**版本**: v1.0
