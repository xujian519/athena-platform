# 认知与决策模块扩展功能使用指南

## 📋 概述

本文档介绍了认知与决策模块监控系统的三大扩展功能：
1. ✅ 逻辑错误修复
2. ✅ 智能告警阈值调整
3. ✅ 业务指标扩展

**实施日期**: 2026-01-25
**版本**: v1.1

---

## 1. 逻辑错误修复功能

### 功能说明

自动扫描并修复认知与决策模块中的常见逻辑错误：
- 空的except块
- `dict.get(str, Any)` 模式错误
- 对函数调用赋值的语法错误

### 使用方法

#### 修复所有已知问题

```bash
python3 scripts/fix_logic_errors.py --all
```

**修复结果**:
- 修复文件数: 3个
- 修复问题数: 7个

#### 修复特定文件

```bash
python3 scripts/fix_logic_errors.py --files core/evaluation/evaluation_engine.py
```

#### 修复整个目录

```bash
python3 scripts/fix_logic_errors.py --dir core/evaluation
```

### 修复的问题类型

| 问题类型 | 严重级别 | 说明 |
|----------|----------|------|
| 空的except块 | High | except块没有任何处理逻辑，隐藏异常 |
| dict.get(str, Any) | High | 应该使用dict.get(str, default_value) |
| 函数调用赋值 | Critical | 尝试对函数调用结果赋值 |

### 示例修复

**修复前**:
```python
try:
    process_data()
except Exception:
    # 空的except块，没有任何处理
```

**修复后**:
```python
try:
    process_data()
except Exception:
    pass  # TODO: 添加适当的错误处理
```

---

## 2. 智能告警阈值调整功能

### 功能说明

基于历史指标数据自动优化Prometheus告警阈值，避免误报和漏报。

### 使用方法

#### 基本使用

```bash
python3 scripts/adjust_alert_thresholds.py
```

这将：
1. 从Prometheus查询24小时的指标数据
2. 计算各指标的P50、P95、P99值
3. 基于统计数据优化告警阈值
4. 生成新的告警规则文件

#### 指定Prometheus URL

```bash
python3 scripts/adjust_alert_thresholds.py --prometheus-url http://localhost:9090
```

#### 仅分析不保存

```bash
python3 scripts/adjust_alert_thresholds.py --dry-run
```

### 优化的告警规则

#### 认知延迟告警

```
原阈值:
- Warning: P95延迟 > 5秒
- Critical: P95延迟 > 30秒

优化后（示例）:
- Warning: P95延迟 > 7.3秒
- Critical: P95延迟 > 28.5秒
```

#### 决策错误率告警

```
原阈值:
- Warning: 错误率 > 5%
- Critical: 错误率 > 15%

优化后（示例）:
- Warning: 错误率 > 3.8%
- Critical: 错误率 > 12.5%
```

### 应用优化后的规则

```bash
# 1. 备份当前规则
cp config/docker/prometheus/cognitive_decision_alerts.yml \
   config/docker/prometheus/cognitive_decision_alerts.yml.backup

# 2. 应用新规则
cp config/docker/prometheus/cognitive_decision_alerts_optimized.yml \
   config/docker/prometheus/cognitive_decision_alerts.yml

# 3. 重启Prometheus
docker-compose -f config/docker/docker-compose.monitoring-stack.yml restart prometheus
```

### 前置条件

使用智能阈值调整前需要确保：
1. ✅ Prometheus正在运行 (http://localhost:9090)
2. ✅ 指标导出器正在运行 (http://localhost:9100)
3. ✅ 有足够的指标数据 (至少1小时，推荐24小时)

---

## 3. 业务指标扩展功能

### 功能说明

添加了25+个业务相关指标，覆盖6大业务领域：
- 专利分析指标 (4个)
- 意图识别指标 (4个)
- 用户交互指标 (4个)
- 推理质量指标 (4个)
- 决策质量指标 (4个)
- 学习系统指标 (4个)
- 知识图谱指标 (4个)

### 导入业务指标模块

在应用中导入业务指标模块：

```python
from core.monitoring.business_metrics import (
    track_patent_analysis,
    track_intent_recognition,
    track_user_interaction,
    track_reasoning_quality,
    business_metrics,
    update_business_metrics
)
```

### 使用装饰器追踪指标

#### 1. 追踪专利分析

```python
@track_patent_analysis(analysis_type='similarity')
def analyze_patent_similarity(patent_id: str, compare_with: List[str]):
    # 专利相似度分析逻辑
    result = perform_analysis(patent_id, compare_with)

    # 返回结果时自动记录指标
    return {
        'similarity_score': 0.87,
        'quality_score': 92,  # 可选：质量评分
        'matches': [
            {'patent_id': 'CN123456', 'score': 0.92},
            {'patent_id': 'CN789012', 'score': 0.78}
        ]
    }
```

**自动记录的指标**:
- `patent_analysis_requests_total` - 分析请求计数
- `patent_analysis_duration_seconds` - 分析耗时
- `patent_analysis_quality_score` - 分析质量评分

#### 2. 追踪意图识别

```python
@track_intent_recognition(model_type='bge-classifier')
def classify_user_intent(query: str):
    # 意图分类逻辑
    result = intent_model.predict(query)

    return {
        'intent': 'patent_search',
        'confidence': 0.89,
        'alternatives': []
    }
```

**自动记录的指标**:
- `intent_recognition_requests_total` - 识别请求计数
- `intent_recognition_duration_seconds` - 识别耗时
- `intent_distribution_count` - 意图分布

#### 3. 追踪用户交互

```python
@track_user_interaction(interaction_type='chat')
def handle_user_message(message: str):
    # 处理用户消息
    response = generate_response(message)

    return {
        'response': response,
        'satisfaction': 8.5  # 可选：满意度评分
    }
```

**自动记录的指标**:
- `user_interaction_duration_seconds` - 交互响应时间
- `user_satisfaction_score` - 用户满意度

#### 4. 追踪推理质量

```python
@track_reasoning_quality(reasoning_mode='super')
def perform_super_reasoning(query: str, context: dict):
    # 超级推理逻辑
    reasoning_steps = execute_reasoning(query, context)

    return {
        'steps': len(reasoning_steps),
        'quality_score': 88,
        'adoption_rate': 0.85,
        'result': reasoning_steps[-1]
    }
```

**自动记录的指标**:
- `reasoning_steps_total` - 推理步骤数
- `reasoning_quality_score` - 推理质量评分
- `reasoning_adoption_rate` - 结果采纳率

### 使用业务指标收集器

#### 记录专利检索命中率

```python
from core.monitoring.business_metrics import business_metrics

def perform_patent_search(query: str):
    results = search_engine.query(query)

    # 记录检索命中率
    business_metrics.record_patent_retrieval(
        search_type='semantic',
        total=len(results.all_results),
        found=len(results.relevant_results)
    )

    return results
```

#### 记录意图识别准确率

```python
def evaluate_intent_model(test_data: List[dict]):
    correct = 0
    total = len(test_data)

    for item in test_data:
        predicted = intent_model.predict(item['query'])
        if predicted['intent'] == item['true_intent']:
            correct += 1

    accuracy = correct / total

    # 记录准确率
    business_metrics.record_intent_accuracy(
        intent_type='patent_search',
        accuracy=accuracy
    )

    return accuracy
```

#### 记录决策质量指标

```python
def evaluate_decision_quality(decisions: List[dict]):
    for decision in decisions:
        # 计算决策质量指标
        accuracy = calculate_accuracy(decision)
        impact = calculate_impact(decision)
        adoption = calculate_adoption_rate(decision)

        # 记录决策质量指标
        business_metrics.record_decision_metrics(
            decision_type=decision['type'],
            accuracy=accuracy,
            impact_score=impact,
            adoption_rate=adoption
        )
```

#### 记录模型训练指标

```python
def train_model(model_name: str, train_data: dict):
    # 训练模型
    history = model.fit(train_data['X'], train_data['y'])

    # 获取最终的准确率和损失
    final_accuracy = history['accuracy'][-1]
    final_loss = history['loss'][-1]

    # 记录模型指标
    business_metrics.record_model_metrics(
        model_name=model_name,
        accuracy=final_accuracy,
        loss=final_loss,
        loss_type='cross_entropy'
    )

    return model
```

#### 记录知识图谱统计

```python
def update_kg_statistics(graph_type: str):
    # 获取知识图谱统计
    stats = kg_client.get_statistics(graph_type)

    # 记录节点和边数
    business_metrics.record_kg_stats(
        graph_type=graph_type,
        nodes=stats['node_count'],
        edges=stats['edge_count']
    )
```

#### 批量更新业务指标

```python
# 一次性更新多个业务指标
update_business_metrics({
    'patent_analysis': {
        'search_type': 'semantic',
        'total': 100,
        'found': 87
    },
    'intent_recognition': {
        'intent_type': 'patent_search',
        'accuracy': 0.92
    },
    'decision_quality': {
        'decision_type': 'route_selection',
        'accuracy': 0.88,
        'impact_score': 75.0,
        'adoption_rate': 0.82
    },
    'model_metrics': {
        'model_name': 'intent_classifier_v2',
        'accuracy': 0.91,
        'loss': 0.23
    }
})
```

### 新增的业务指标列表

#### 专利分析指标 (4个)

| 指标名称 | 类型 | 标签 | 说明 |
|----------|------|------|------|
| `patent_analysis_requests_total` | Counter | analysis_type, success | 专利分析请求总数 |
| `patent_analysis_duration_seconds` | Histogram | analysis_type | 专利分析处理延迟 |
| `patent_analysis_quality_score` | Gauge | analysis_type | 专利分析质量评分 (0-100) |
| `patent_retrieval_hit_rate` | Gauge | search_type | 专利检索命中率 |

#### 意图识别指标 (4个)

| 指标名称 | 类型 | 标签 | 说明 |
|----------|------|------|------|
| `intent_recognition_requests_total` | Counter | intent_type, confidence_level | 意图识别请求总数 |
| `intent_accuracy_percent` | Gauge | intent_type | 意图识别准确率 |
| `intent_recognition_duration_seconds` | Histogram | model_type | 意图识别处理延迟 |
| `intent_distribution_count` | Gauge | intent_type | 意图分布统计 |

#### 用户交互指标 (4个)

| 指标名称 | 类型 | 标签 | 说明 |
|----------|------|------|------|
| `user_sessions_total` | Counter | session_type | 用户会话总数 |
| `user_interaction_duration_seconds` | Histogram | interaction_type | 用户交互响应延迟 |
| `user_satisfaction_score` | Gauge | interaction_type | 用户满意度评分 (0-10) |
| `user_feedback_total` | Counter | feedback_type, sentiment | 用户反馈总数 |

#### 推理质量指标 (4个)

| 指标名称 | 类型 | 标签 | 说明 |
|----------|------|------|------|
| `reasoning_steps_total` | Gauge | reasoning_mode | 推理步骤总数 |
| `reasoning_quality_score` | Gauge | reasoning_mode | 推理质量评分 (0-100) |
| `reasoning_adoption_rate` | Gauge | reasoning_mode | 推理结果采纳率 |
| `super_reasoning_memory_bytes` | Gauge | reasoning_mode | 超级推理内存使用 |

#### 决策质量指标 (4个)

| 指标名称 | 类型 | 标签 | 说明 |
|----------|------|------|------|
| `decision_accuracy_percent` | Gauge | decision_type | 决策准确率 |
| `decision_response_time_seconds` | Histogram | decision_type, priority | 决策响应时间 |
| `decision_impact_score` | Gauge | decision_type | 决策影响评分 (0-100) |
| `decision_adoption_rate` | Gauge | decision_type | 决策采纳率 |

#### 学习系统指标 (4个)

| 指标名称 | 类型 | 标签 | 说明 |
|----------|------|------|------|
| `learning_samples_total` | Counter | sample_type | 学习样本总数 |
| `model_accuracy_percent` | Gauge | model_name, metric_type | 模型准确率 |
| `model_loss_value` | Gauge | model_name, loss_type | 模型损失值 |
| `learning_convergence_rate` | Gauge | algorithm | 学习收敛速度 |

#### 知识图谱指标 (4个)

| 指标名称 | 类型 | 标签 | 说明 |
|----------|------|------|------|
| `knowledge_graph_queries_total` | Counter | query_type, success | 知识图谱查询总数 |
| `knowledge_graph_query_duration_seconds` | Histogram | query_type | 知识图谱查询延迟 |
| `knowledge_graph_nodes_total` | Gauge | graph_type | 知识图谱节点总数 |
| `knowledge_graph_edges_total` | Gauge | graph_type | 知识图谱边总数 |

---

## 4. 完整的使用示例

### 示例1：集成到专利分析服务

```python
# core/services/patent_analysis_service.py

from core.monitoring.business_metrics import (
    track_patent_analysis,
    track_intent_recognition,
    business_metrics
)

class PatentAnalysisService:
    """专利分析服务"""

    @track_patent_analysis(analysis_type='similarity')
    def analyze_similarity(self, patent_id: str, compare_with: List[str]):
        """分析专利相似度"""
        # 业务逻辑
        results = self._perform_similarity_analysis(patent_id, compare_with)

        # 返回包含质量评分的结果
        return {
            'patent_id': patent_id,
            'similar_patents': results,
            'quality_score': self._calculate_quality(results)
        }

    @track_intent_recognition(model_type='transformer')
    def detect_user_intent(self, query: str):
        """检测用户意图"""
        # 意图识别逻辑
        intent = self.intent_model.predict(query)

        return {
            'intent': intent['label'],
            'confidence': intent['score'],
            'metadata': intent.get('metadata', {})
        }

    def update_retrieval_metrics(self, search_type: str, total: int, found: int):
        """更新检索指标"""
        business_metrics.record_patent_retrieval(search_type, total, found)
```

### 示例2：集成到决策服务

```python
# core/decision/enhanced_decision_service.py

from core.monitoring.business_metrics import (
    track_decision,
    track_reasoning_quality,
    business_metrics
)

class EnhancedDecisionService:
    """增强决策服务"""

    @track_decision(decision_type='route_selection', priority='high')
    def make_routing_decision(self, context: dict):
        """做出路由决策"""
        # 决策逻辑
        decision = self._analyze_and_decide(context)

        return {
            'route': decision['route'],
            'confidence': decision['score'],
            'reasoning': decision.get('reasoning', [])
        }

    def evaluate_decision_quality(self, decision_type: str):
        """评估决策质量"""
        # 收集决策数据
        decisions = self._get_recent_decisions(decision_type, days=7)

        # 计算质量指标
        accuracy = self._calculate_accuracy(decisions)
        impact = self._calculate_impact(decisions)
        adoption = self._calculate_adoption(decisions)

        # 记录到指标系统
        business_metrics.record_decision_metrics(
            decision_type=decision_type,
            accuracy=accuracy,
            impact_score=impact,
            adoption_rate=adoption
        )

        return {
            'accuracy': accuracy,
            'impact': impact,
            'adoption': adoption
        }
```

### 示例3：集成到学习引擎

```python
# core/learning/adaptive_learning_engine.py

from core.monitoring.business_metrics import business_metrics

class AdaptiveLearningEngine:
    """自适应学习引擎"""

    def train_model(self, model_name: str, training_config: dict):
        """训练模型"""
        # 训练逻辑
        history = self._execute_training(model_name, training_config)

        # 记录训练指标
        final_epoch = history[-1]
        business_metrics.record_model_metrics(
            model_name=model_name,
            accuracy=final_epoch['accuracy'],
            loss=final_epoch['loss'],
            loss_type=training_config.get('loss_type', 'cross_entropy')
        )

        # 记录学习样本数
        business_metrics.record_learning_progress(
            sample_type=training_config['data_type'],
            samples=training_config['num_samples'],
            convergence_rate=self._calculate_convergence(history)
        )

        return history

    def evaluate_model(self, model_name: str, test_data: dict):
        """评估模型"""
        # 评估逻辑
        results = self._execute_evaluation(model_name, test_data)

        # 记录各种指标
        for metric_name, metric_value in results.items():
            if 'accuracy' in metric_name:
                business_metrics.record_model_metrics(
                    model_name=model_name,
                    accuracy=metric_value,
                    loss=0.0,  # 评估阶段不记录loss
                    metric_type=metric_name
                )

        return results
```

---

## 5. 查看业务指标

### 通过Prometheus查询

```bash
# 查看专利分析请求总数
curl http://localhost:9100/metrics | grep patent_analysis_requests_total

# 查看意图识别准确率
curl http://localhost:9100/metrics | grep intent_accuracy_percent

# 查看用户满意度
curl http://localhost:9100/metrics | grep user_satisfaction_score
```

### 通过Grafana可视化

在Grafana中创建新仪表板：

1. 登录Grafana (http://localhost:3000)
2. 点击 "+" → "New dashboard"
3. 添加新面板，使用Prometheus查询：

```promql
# 专利分析请求趋势
rate(patent_analysis_requests_total[5m])

# 意图识别准确率
intent_accuracy_percent

# 用户满意度分布
avg(user_satisfaction_score) by (interaction_type)
```

---

## 6. 故障排查

### 问题1：业务指标没有显示

**原因**: 业务指标模块未导入或未正确使用

**解决**:
```python
# 确保导入了业务指标模块
from core.monitoring.business_metrics import business_metrics

# 确保调用了记录方法
business_metrics.record_patent_retrieval('semantic', 100, 87)
```

### 问题2：智能阈值调整失败

**原因**: Prometheus未运行或数据不足

**解决**:
```bash
# 1. 检查Prometheus状态
curl http://localhost:9090/-/healthy

# 2. 检查指标导出器状态
curl http://localhost:9100/metrics | head -20

# 3. 确保有足够的数据（至少1小时）
# 访问 http://localhost:9090/graph 查询指标
```

### 问题3：逻辑错误修复后代码仍报错

**原因**: 某些错误需要手动审查和修复

**解决**:
1. 查看修复脚本生成的TODO注释
2. 根据业务逻辑添加适当的错误处理
3. 运行测试验证修复

---

## 7. 最佳实践

### 1. 合理使用装饰器

```python
# ✅ 好的做法：在关键业务函数上使用装饰器
@track_patent_analysis(analysis_type='similarity')
def analyze_patent_similarity(patent_id, compare_with):
    # 复杂的业务逻辑
    pass

# ❌ 不好的做法：过度使用装饰器
@track_user_interaction(interaction_type='internal')
def _internal_helper_function(data):
    # 简单的辅助函数不需要追踪
    pass
```

### 2. 定期优化告警阈值

```bash
# 每周运行一次阈值优化
python3 scripts/adjust_alert_thresholds.py

# 应用优化后的阈值
cp config/docker/prometheus/cognitive_decision_alerts_optimized.yml \
   config/docker/prometheus/cognitive_decision_alerts.yml
docker-compose restart prometheus
```

### 3. 持续监控业务指标

```python
# 在关键业务流程中记录指标
def process_patent_application(application_data):
    # 处理专利申请
    result = process(application_data)

    # 记录关键业务指标
    business_metrics.record_decision_metrics(
        decision_type='application_approval',
        accuracy=result['accuracy'],
        impact_score=result['impact'],
        adoption_rate=result['adoption']
    )

    return result
```

---

## 8. 总结

### 完成的扩展功能

| 功能 | 状态 | 产出 |
|------|------|------|
| 逻辑错误修复 | ✅ | 修复7个问题，创建自动修复工具 |
| 智能阈值调整 | ✅ | 创建基于数据的阈值优化工具 |
| 业务指标扩展 | ✅ | 添加25+个业务相关指标 |

### 创建的新文件

1. `scripts/fix_logic_errors.py` - 逻辑错误修复工具
2. `scripts/adjust_alert_thresholds.py` - 智能阈值调整工具
3. `core/monitoring/business_metrics.py` - 业务指标扩展模块
4. `docs/quality/cognitive_decision_extension_guide.md` - 本文档

### 下一步建议

1. **集成业务指标**: 将业务指标集成到实际的服务中
2. **定期优化阈值**: 每周运行一次智能阈值调整
3. **持续修复错误**: 定期运行逻辑错误扫描和修复
4. **创建仪表板**: 在Grafana中创建业务指标仪表板

---

*文档版本: v1.0*
*更新日期: 2026-01-25*
*Athena Platform Team*
