# 小诺评估反馈系统 API 文档

## 概述

`XiaonuoFeedbackSystem` 是小诺系统的质量评估和反馈收集组件，支持明确反馈收集、隐式反馈推断、服务质量评估和改进计划生成。

## 核心组件

### 1. XiaonuoFeedbackSystem - 反馈系统主类

#### 功能
- 收集和管理用户反馈
- 评估服务质量
- 生成改进计划
- 数据持久化

#### 初始化

```python
from core.evaluation.xiaonuo_feedback_system import XiaonuoFeedbackSystem

# 创建反馈系统实例
feedback_system = XiaonuoFeedbackSystem()

# 系统会自动加载历史反馈数据
```

---

## API 方法

### 明确反馈收集

#### `collect_explicit_feedback(satisfaction: int, content: str, context: dict | None = None) -> str`

收集用户的明确反馈。

**参数:**
- `satisfaction`: 满意度评分 (1-5)
  - 5 = 非常满意
  - 4 = 满意
  - 3 = 中立
  - 2 = 不满意
  - 1 = 非常不满意
- `content`: 反馈内容
- `context`: 可选的上下文信息

**返回:** 反馈ID

**示例:**

```python
feedback_id = feedback_system.collect_explicit_feedback(
    satisfaction=5,
    content="回答非常准确，解决了我的问题",
    context={
        "task": "专利检索",
        "response_time": 2.5,
        "query": "如何提高专利检索准确度",
    }
)

print(f"反馈已记录: {feedback_id}")
```

---

### 隐式反馈推断

#### `infer_implicit_feedback(user_response: str, interaction_context: dict) -> str | None`

从用户的自然语言响应中推断隐式反馈。

**参数:**
- `user_response`: 用户响应文本
- `interaction_context`: 交互上下文

**返回:** 反馈ID（如果推断出明确情绪），否则返回 None

**工作原理:**
- 分析用户响应中的情感关键词
- 正面关键词: 好、棒、满意、可以、赞、厉害、优秀、完美
- 负面关键词: 不好、差、不行、糟糕、失望、烦、错、问题

**示例:**

```python
# 正面隐式反馈
feedback_id = feedback_system.infer_implicit_feedback(
    user_response="这个方案很棒，完全解决了我的问题！",
    interaction_context={"task": "方案建议"}
)
# 返回反馈ID，满意度 >= 4

# 中性响应
feedback_id = feedback_system.infer_implicit_feedback(
    user_response="我知道了，收到",
    interaction_context={"task": "信息查询"}
)
# 返回 None（中性反馈不记录）
```

---

### 服务质量评估

#### `evaluate_service_quality(response: str, response_time: float, context: dict | None = None) -> ServiceMetrics`

评估系统的服务质量。

**参数:**
- `response`: 系统响应内容
- `response_time`: 响应时间（秒）
- `context`: 可选的评估上下文

**返回:** ServiceMetrics 对象，包含：
- `response_time`: 响应时间
- `accuracy`: 准确性分数 (0-1)
- `helpfulness`: 有用性分数 (0-1)
- `clarity`: 清晰度分数 (0-1)
- `completeness`: 完整性分数 (0-1)
- `overall_score`: 总体分数 (0-1)

**评分标准:**

响应时间评分:
```
分数 = max(0, 1 - 响应时间 / 30)
30秒内为满分，超过30秒开始扣分
```

准确性评估:
- 检查是否回答了问题
- 包含问题关键词加分

有用性评估:
- 包含建议、方案、解决等词汇加分
- 每个有用性指示词 +0.1

清晰度评估:
- 长度在50-500字符为最优
- 包含标点符号加分

完整性评估:
- 包含示例加分
- 包含因果解释加分

**示例:**

```python
metrics = feedback_system.evaluate_service_quality(
    response="针对您的专利检索问题，建议使用以下方案：1. 使用布尔查询 2. 添加同义词扩展。例如，查询'人工智能'时可以同时搜索'AI'。",
    response_time=3.5,
    context={
        "question": "如何提高专利检索准确度",
        "task": "专利检索",
    }
)

print(f"总体分数: {metrics.overall_score:.2%}")
print(f"准确性: {metrics.accuracy:.2%}")
print(f"有用性: {metrics.helpfulness:.2%}")
print(f"清晰度: {metrics.clarity:.2%}")
print(f"完整性: {metrics.completeness:.2%}")
```

---

### 改进计划生成

#### `generate_improvement_plan() -> dict[str, Any]`

基于收集的反馈生成系统改进计划。

**返回:** 改进计划字典，包含:
- `current_status`: 当前状态
  - `avg_satisfaction`: 平均满意度
  - `total_feedback`: 反馈总数
  - `service_metrics`: 服务指标
- `problem_areas`: 问题领域分析
- `improvement_actions`: 改进建议列表
- `target_goals`: 目标指标
- `timeline`: 预期时间线

**问题领域识别:**
- `response_speed`: 响应速度问题
- `accuracy`: 准确性问题
- `helpfulness`: 有用性问题
- `clarity`: 清晰度问题
- `completeness`: 完整性问题

**示例:**

```python
plan = feedback_system.generate_improvement_plan()

if "message" not in plan:  # 有足够的反馈数据
    print("当前状态:")
    print(f"  平均满意度: {plan['current_status']['avg_satisfaction']:.1f}/5")
    print(f"  反馈总数: {plan['current_status']['total_feedback']}")

    print("\n问题领域:")
    for area, score in plan['problem_areas'].items():
        if score > 0:
            print(f"  {area}: {score:.1%}")

    print("\n改进建议:")
    for action in plan['improvement_actions']:
        print(f"  - {action}")

    print("\n目标指标:")
    for goal, value in plan['target_goals'].items():
        print(f"  {goal}: {value}")

    print(f"\n时间线: {plan['timeline']}")
```

---

### 反馈摘要

#### `get_feedback_summary() -> dict[str, Any]`

获取反馈数据的统计摘要。

**返回:** 反馈摘要字典，包含:
- `total_feedback`: 总反馈数
- `recent_feedback_30d`: 近30天反馈数
- `satisfaction_distribution`: 满意度分布
- `average_satisfaction`: 平均满意度
- `feedback_type_distribution`: 反馈类型分布
- `service_metrics`: 当前服务指标
- `quality_metrics`: 质量指标
- `trend`: 趋势 (improving/stable)

**示例:**

```python
summary = feedback_system.get_feedback_summary()

print("反馈摘要:")
print(f"  总反馈数: {summary['total_feedback']}")
print(f"  近30天: {summary['recent_feedback_30d']}")
print(f"  平均满意度: {summary['average_satisfaction']:.1f}/5")
print(f"  趋势: {summary['trend']}")

print("\n满意度分布:")
for level, count in summary['satisfaction_distribution'].items():
    print(f"  {level}: {count}")
```

---

## 数据模型

### FeedbackItem - 反馈项

```python
@dataclass
class FeedbackItem:
    id: str                              # 反馈ID
    timestamp: datetime                   # 时间戳
    feedback_type: FeedbackType          # 反馈类型
    satisfaction_level: SatisfactionLevel # 满意度等级
    content: str                         # 反馈内容
    context: dict[str, Any]              # 上下文信息
    tags: list[str]                      # 标签
    action_taken: str | None             # 采取的行动
    impact_score: float                  # 影响分数
```

### ServiceMetrics - 服务指标

```python
@dataclass
class ServiceMetrics:
    response_time: float                  # 响应时间(秒)
    accuracy: float                       # 准确性(0-1)
    helpfulness: float                    # 有用性(0-1)
    clarity: float                        # 清晰度(0-1)
    completeness: float                   # 完整性(0-1)
    overall_score: float                  # 总体分数
```

### QualityMetrics - 质量指标

```python
@dataclass
class QualityMetrics:
    consistency_score: float              # 一致性分数
    improvement_rate: float               # 改进率
    error_rate: float                     # 错误率
    recovery_time: float                  # 恢复时间
    user_retention: float                 # 用户留存率
```

---

## 枚举类型

### FeedbackType - 反馈类型

```python
class FeedbackType(Enum):
    EXPLICIT = "explicit"              # 明确反馈
    IMPLICIT = "implicit"              # 隐式反馈
    BEHAVIORAL = "behavioral"          # 行为反馈
    PERFORMANCE = "performance"        # 性能反馈
```

### SatisfactionLevel - 满意度等级

```python
class SatisfactionLevel(Enum):
    VERY_SATISFIED = 5                # 非常满意
    SATISFIED = 4                     # 满意
    NEUTRAL = 3                       # 中立
    DISSATISFIED = 2                  # 不满意
    VERY_DISSATISFIED = 1             # 非常不满意
```

---

## 使用场景

### 场景1: 专利检索后收集反馈

```python
# 执行专利检索
results = await search_patents("人工智能")

# 评估服务质量
metrics = feedback_system.evaluate_service_quality(
    response=f"找到 {len(results)} 条相关专利",
    response_time=2.3,
    context={"query": "人工智能", "results_count": len(results)}
)

# 收集用户明确反馈
feedback_id = feedback_system.collect_explicit_feedback(
    satisfaction=4,
    content="检索结果很准确，但希望能看到更多相似专利",
    context={"search_query": "人工智能", "results_count": len(results)}
)
```

### 场景2: 从对话中推断隐式反馈

```python
# 用户响应
user_response = "这个分析很有帮助，谢谢！"

# 自动推断反馈
feedback_id = feedback_system.infer_implicit_feedback(
    user_response=user_response,
    interaction_context={
        "task": "专利分析",
        "patent_id": "CN123456789A",
    }
)

if feedback_id:
    print("检测到正面反馈，已自动记录")
```

### 场景3: 定期生成改进报告

```python
# 每周生成改进计划
import schedule

def weekly_improvement_report():
    plan = feedback_system.generate_improvement_plan()

    # 发送报告
    send_report_to_team(plan)

    # 根据建议实施改进
    for action in plan['improvement_actions']:
        implement_improvement(action)

# 每周一早上9点执行
schedule.every().monday.at("09:00").do(weekly_improvement_report)
```

### 场景4: A/B测试评估

```python
# 测试两种响应方案
for variant in ["A", "B"]:
    # 使用变体生成响应
    response = generate_response_variant(query, variant)

    # 评估质量
    metrics = feedback_system.evaluate_service_quality(
        response=response,
        response_time=measure_time(),
        context={"variant": variant, "query": query}
    )

    print(f"变体{variant}总体分数: {metrics.overall_score:.2%}")
```

---

## 最佳实践

### 1. 及时收集反馈

```python
# 任务完成后立即收集反馈
async def complete_task(task_id: str):
    result = await process_task(task_id)

    # 立即收集反馈
    feedback_system.collect_explicit_feedback(
        satisfaction=ask_user_satisfaction(),
        content="任务完成",
        context={"task_id": task_id}
    )
```

### 2. 结合隐式反馈

```python
# 不要仅依赖明确反馈，也要利用隐式反馈
user_response = get_user_response()
feedback_id = feedback_system.infer_implicit_feedback(
    user_response,
    interaction_context
)

# 如果推断出明确情绪，自动记录
if feedback_id:
    logger.info(f"自动记录隐式反馈: {feedback_id}")
```

### 3. 定期分析

```python
# 每周分析反馈趋势
def weekly_analysis():
    summary = feedback_system.get_feedback_summary()

    if summary['average_satisfaction'] < 3.5:
        alert_team("满意度低于阈值，需要关注")

    if summary['trend'] != 'improving':
        review_processes()
```

### 4. 持续改进

```python
# 基于反馈持续优化系统
def continuous_improvement():
    plan = feedback_system.generate_improvement_plan()

    for action in plan['improvement_actions']:
        # 实施改进
        implement(action)

        # 追踪效果
        track_improvement_impact(action)
```

---

## 性能考虑

### 缓存服务指标

```python
# 服务指标会自动更新和缓存
# 无需手动管理
metrics = feedback_system.service_metrics
```

### 异步保存

```python
# 反馈数据会异步保存到磁盘
# 不会阻塞主流程
feedback_system.collect_explicit_feedback(5, "很好")
# 数据在后台保存，立即返回
```

### 批量处理

```python
# 批量收集反馈
for item in batch_items:
    feedback_system.collect_explicit_feedback(
        item.satisfaction,
        item.content
    )

# 批量保存
feedback_system._save_feedback_data()
```

---

## 相关文档

- [服务质量评估标准](../standards/service_quality.md)
- [反馈分析方法](../analysis/feedback_analysis.md)
- [持续改进流程](../guides/continuous_improvement.md)
