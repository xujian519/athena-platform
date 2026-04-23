# ApplicationReviewerProxy LLM集成 - 快速使用指南

> **更新时间**: 2026-04-21
> **状态**: ✅ 生产就绪

---

## 概述

`ApplicationReviewerProxy`（申请文件审查智能体）现已支持**LLM智能分析**，同时保留**规则-based降级**。当LLM可用时，使用LLM进行更智能的分析；当LLM不可用时，自动降级到规则-based分析。

---

## 快速开始

### 1. 基本使用

```python
import asyncio
from core.agents.xiaona.application_reviewer_proxy import ApplicationDocumentReviewerProxy

async def main():
    # 创建审查智能体
    reviewer = ApplicationDocumentReviewerProxy(
        agent_id="application_reviewer_001",
        config={
            "llm_config": {
                "model": "claude-3-5-sonnet-20241022",
                "temperature": 0.7,
                "max_tokens": 4096
            }
        }
    )

    # 准备申请文件数据
    application_data = {
        "application_id": "CN202310000000.0",
        "applicant": "张三",
        "documents": ["请求书", "说明书", "权利要求书", "摘要"],
        "applicant_data": {
            "name": "张三",
            "address": "北京市海淀区",
            "nationality": "中国"
        },
        "technical_field": "本发明涉及人工智能技术领域...",
        "background_art": "现有技术中...",
        "technical_problem": "本发明要解决的技术问题是...",
        "technical_solution": "本发明提供一种...",
        "beneficial_effects": "本发明的有益效果是...",
        "claims": "1. 一种方法，其特征在于...",
        "specification": "技术领域\n本发明涉及...",
        "embodiments": ["实施例1：...", "实施例2：..."],
        "drawings": ["图1", "图2"]
    }

    # 执行完整审查
    result = await reviewer.review_application(application_data)

    # 查看结果
    print(f"综合评分: {result['overall_score']:.2f}")
    print(f"质量等级: {result['overall_quality']}")
    print(f"改进建议: {result['recommendations']}")

asyncio.run(main())
```

### 2. 单独审查

```python
# 只审查格式
format_result = await reviewer.review_format(application_data)
print(f"格式检查: {format_result['format_check']}")
print(f"完整性比例: {format_result['completeness_ratio']:.2f}")

# 只审查技术披露
disclosure_result = await reviewer.review_disclosure(application_data)
print(f"披露充分性: {disclosure_result['disclosure_adequacy']}")
print(f"完整性评分: {disclosure_result['completeness_score']:.2f}")

# 只审查权利要求
claims_result = await reviewer.review_claims(application_data)
print(f"权利要求数量: {claims_result['total_claims']}")
print(f"独立权利要求: {claims_result['independent_claims']}")

# 只审查说明书
specification_result = await reviewer.review_specification(application_data)
print(f"实施方式数量: {specification_result['total_embodiments']}")
print(f"附图数量: {specification_result['total_drawings']}")
```

---

## 输入数据格式

### 必需字段

```python
{
    # 基本信息
    "application_id": str,      # 申请号
    "applicant": str,            # 申请人
    "documents": List[str],      # 文件列表

    # 申请人信息
    "applicant_data": {
        "name": str,             # 姓名
        "address": str,          # 地址
        "nationality": str       # 国籍
    },

    # 技术信息
    "technical_field": str,     # 技术领域
    "background_art": str,      # 背景技术
    "technical_problem": str,   # 技术问题
    "technical_solution": str,  # 技术方案
    "beneficial_effects": str,  # 有益效果

    # 权利要求
    "claims": str,              # 权利要求书文本

    # 说明书
    "specification": str,       # 说明书文本

    # 实施方式和附图（可选）
    "embodiments": List[str],   # 实施方式列表
    "drawings": List[str]       # 附图列表
}
```

---

## 输出数据格式

### 完整审查输出

```python
{
    # 基本信息
    "application_id": str,
    "applicant": str,
    "review_scope": str,        # comprehensive/quick

    # 各项审查结果
    "format_review": {
        "format_check": str,    # passed/failed
        "completeness_ratio": float,
        "missing_documents": List[str],
        ...
    },
    "disclosure_review": {
        "disclosure_adequacy": str,  # sufficient/insufficient
        "completeness_score": float,
        ...
    },
    "claims_review": {
        "total_claims": int,
        "independent_claims": int,
        "dependent_claims": int,
        ...
    },
    "specification_review": {
        "total_embodiments": int,
        "total_drawings": int,
        ...
    },

    # 综合评估
    "overall_score": float,     # 0.0-1.0
    "overall_quality": str,     # 优秀/良好/合格/待改进
    "recommendations": List[str],
    "reviewed_at": str          # ISO时间戳
}
```

---

## LLM vs 规则-based对比

### LLM分析优势

✅ **更智能的理解**：能理解上下文和语义
✅ **更灵活的判断**：不局限于固定规则
✅ **更详细的建议**：能提供针对性建议
✅ **更准确的评分**：综合多个维度评估

### 规则-based优势

✅ **更快速度**：10-50ms vs 1-5秒
✅ **100%可靠**：不依赖外部服务
✅ **成本为零**：无LLM调用费用
✅ **结果一致**：相同输入总是相同输出

### 自动降级

系统会自动在LLM和规则-based之间切换：

```
LLM可用 → 使用LLM分析
LLM失败 → 自动降级到规则-based
```

---

## 配置选项

### LLM配置

```python
config = {
    "llm_config": {
        "model": "claude-3-5-sonnet-20241022",  # 模型选择
        "temperature": 0.7,                      # 创造性（0.0-1.0）
        "max_tokens": 4096,                      # 最大输出长度
        "timeout": 30.0                          # 超时时间（秒）
    }
}
```

### 任务类型配置

系统自动为不同任务选择合适的参数：

```python
# 格式审查 - 简单任务
task_type = "format_review"

# 披露审查 - 中等任务
task_type = "disclosure_review"

# 权利要求审查 - 复杂任务
task_type = "claims_review"

# 说明书审查 - 复杂任务
task_type = "specification_review"
```

---

## 错误处理

### LLM调用失败

```python
try:
    result = await reviewer.review_format(application_data)
except Exception as e:
    # LLM调用失败会自动降级到规则-based
    # 通常不会抛出异常
    print(f"审查完成（可能使用了规则-based分析）")
```

### 日志查看

```python
import logging

# 启用DEBUG日志查看LLM调用详情
logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger("core.agents.xiaona.application_reviewer_proxy")
```

---

## 性能优化

### 并发执行

```python
# 并发执行多个审查（如果LLM支持）
import asyncio

async def parallel_review(application_data):
    tasks = [
        reviewer.review_format(application_data),
        reviewer.review_disclosure(application_data),
        reviewer.review_claims(application_data),
        reviewer.review_specification(application_data),
    ]

    results = await asyncio.gather(*tasks)
    return results
```

### 缓存结果

```python
# 缓存审查结果避免重复计算
from functools import lru_cache

@lru_cache(maxsize=128)
def cached_review(application_id: str):
    return await reviewer.review_application(application_data)
```

---

## 最佳实践

### 1. 数据准备

```python
# ✅ 好的做法：提供完整的数据
application_data = {
    "technical_field": "详细的技术领域描述（至少100字）",
    "background_art": "详细的背景技术描述（至少200字）",
    "claims": "完整的权利要求书文本",
    ...
}

# ❌ 不好的做法：提供过于简略的数据
application_data = {
    "technical_field": "AI",
    "background_art": "现有技术不足",
    ...
}
```

### 2. 结果解读

```python
# 综合评分解读
if result['overall_score'] >= 0.9:
    print("优秀 - 申请文件质量很高")
elif result['overall_score'] >= 0.75:
    print("良好 - 有少量改进空间")
elif result['overall_score'] >= 0.6:
    print("合格 - 建议改进后再提交")
else:
    print("待改进 - 需要大幅修改")
```

### 3. 建议处理

```python
# 按优先级处理建议
priority_recommendations = [
    rec for rec in result['recommendations']
    if "必须" in rec or "缺少" in rec
]

print("优先处理：")
for rec in priority_recommendations:
    print(f"- {rec}")
```

---

## 常见问题

### Q1: LLM分析失败怎么办？

**A**: 系统会自动降级到规则-based分析，确保始终有结果返回。你可以通过日志查看是否使用了降级：

```python
logger.warning("LLM格式审查失败: xxx，使用规则-based审查")
```

### Q2: 如何判断使用了LLM还是规则？

**A**: 检查日志输出，或通过响应质量判断：

- **LLM分析**：建议更详细、评分更准确
- **规则分析**：建议较简单、评分基于固定规则

### Q3: 可以强制使用规则-based吗？

**A**: 可以通过禁用LLM管理器：

```python
reviewer._llm_manager = None
# 现在会直接使用规则-based分析
```

### Q4: 支持哪些LLM模型？

**A**: 支持UnifiedLLMManager中的所有模型：

- Claude 3.5 Sonnet
- GPT-4
- DeepSeek
- GLM
- Qwen
- Ollama（本地模型）

---

## 相关文档

- **实施报告**: `docs/reports/XIAONA_LLM_INTEGRATION_PHASE2_APPLICATION_REVIEWER_20260421.md`
- **测试代码**: `tests/agents/xiaona/test_application_reviewer_llm_integration.py`
- **源代码**: `core/agents/xiaona/application_reviewer_proxy.py`

---

**维护者**: 徐健 (xujian519@gmail.com)
**最后更新**: 2026-04-21
