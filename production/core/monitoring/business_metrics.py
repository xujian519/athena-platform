#!/usr/bin/env python3
"""
认知与决策模块业务指标扩展
Business Metrics Extension for Cognitive & Decision Module

添加更多业务相关的监控指标：
- 专利分析指标
- 意图识别准确率
- 用户满意度
- 响应质量评分
- 任务完成率

作者: Athena Platform Team
版本: v1.0
"""

from __future__ import annotations
import time
from functools import wraps
from typing import Any

from prometheus_client import Counter, Gauge, Histogram

# ============== 专利分析业务指标 ==============

# 专利分析请求
patent_analysis_requests = Counter(
    'patent_analysis_requests_total',
    'Total patent analysis requests',
    ['analysis_type', 'success']
)

# 专利分析延迟
patent_analysis_duration = Histogram(
    'patent_analysis_duration_seconds',
    'Patent analysis processing duration',
    ['analysis_type'],
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0]
)

# 专利分析质量评分
patent_analysis_quality_score = Gauge(
    'patent_analysis_quality_score',
    'Patent analysis quality score (0-100)',
    ['analysis_type']
)

# 专利检索命中率
patent_retrieval_hit_rate = Gauge(
    'patent_retrieval_hit_rate',
    'Patent retrieval hit rate',
    ['search_type']
)

# ============== 意图识别业务指标 ==============

# 意图识别请求
intent_recognition_requests = Counter(
    'intent_recognition_requests_total',
    'Total intent recognition requests',
    ['intent_type', 'confidence_level']
)

# 意图识别准确率
intent_accuracy = Gauge(
    'intent_accuracy_percent',
    'Intent recognition accuracy percentage',
    ['intent_type']
)

# 意图识别延迟
intent_recognition_duration = Histogram(
    'intent_recognition_duration_seconds',
    'Intent recognition processing duration',
    ['model_type'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0]
)

# 意图分布
intent_distribution = Gauge(
    'intent_distribution_count',
    'Distribution of detected intents',
    ['intent_type']
)

# ============== 用户交互业务指标 ==============

# 用户会话数
user_sessions = Counter(
    'user_sessions_total',
    'Total user sessions',
    ['session_type']
)

# 用户交互延迟
user_interaction_duration = Histogram(
    'user_interaction_duration_seconds',
    'User interaction response duration',
    ['interaction_type'],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

# 用户满意度
user_satisfaction_score = Gauge(
    'user_satisfaction_score',
    'User satisfaction score (0-10)',
    ['interaction_type']
)

# 用户反馈数
user_feedback = Counter(
    'user_feedback_total',
    'Total user feedback',
    ['feedback_type', 'sentiment']
)

# ============== 推理质量业务指标 ==============

# 推理步骤数
reasoning_steps_total = Gauge(
    'reasoning_steps_total',
    'Total reasoning steps executed',
    ['reasoning_mode']
)

# 推理质量评分
reasoning_quality_score = Gauge(
    'reasoning_quality_score',
    'Reasoning quality score (0-100)',
    ['reasoning_mode']
)

# 推理结果采纳率
reasoning_adoption_rate = Gauge(
    'reasoning_adoption_rate',
    'Rate at which reasoning results are adopted',
    ['reasoning_mode']
)

# ============== 决策质量业务指标 ==============

# 决策准确率
decision_accuracy = Gauge(
    'decision_accuracy_percent',
    'Decision accuracy percentage',
    ['decision_type']
)

# 决策响应时间
decision_response_time = Histogram(
    'decision_response_time_seconds',
    'Decision response time',
    ['decision_type', 'priority'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# 决策影响评分
decision_impact_score = Gauge(
    'decision_impact_score',
    'Decision impact score (0-100)',
    ['decision_type']
)

# 决策采纳率
decision_adoption_rate = Gauge(
    'decision_adoption_rate',
    'Rate at which decisions are adopted',
    ['decision_type']
)

# ============== 学习系统业务指标 ==============

# 学习样本数
learning_samples_total = Counter(
    'learning_samples_total',
    'Total learning samples processed',
    ['sample_type']
)

# 模型准确率
model_accuracy = Gauge(
    'model_accuracy_percent',
    'Model accuracy percentage',
    ['model_name', 'metric_type']
)

# 模型损失
model_loss = Gauge(
    'model_loss_value',
    'Model loss value',
    ['model_name', 'loss_type']
)

# 学习收敛速度
learning_convergence_rate = Gauge(
    'learning_convergence_rate',
    'Learning convergence rate',
    ['algorithm']
)

# ============== 知识图谱业务指标 ==============

# 知识图谱查询数
kg_queries_total = Counter(
    'knowledge_graph_queries_total',
    'Total knowledge graph queries',
    ['query_type', 'success']
)

# 知识图谱延迟
kg_query_duration = Histogram(
    'knowledge_graph_query_duration_seconds',
    'Knowledge graph query duration',
    ['query_type'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
)

# 知识图谱节点数
kg_nodes_total = Gauge(
    'knowledge_graph_nodes_total',
    'Total nodes in knowledge graph',
    ['graph_type']
)

# 知识图谱边数
kg_edges_total = Gauge(
    'knowledge_graph_edges_total',
    'Total edges in knowledge graph',
    ['graph_type']
)

# ============== 装饰器函数 ==============

def track_patent_analysis(analysis_type: str = 'general'):
    """追踪专利分析业务指标"""
    def decorator(func):
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            quality_score = 0

            try:
                result = func(*args, **kwargs)

                # 从结果中提取质量评分（如果有）
                if isinstance(result, dict) and 'quality_score' in result:
                    quality_score = result['quality_score']

                # 记录成功指标
                duration = time.time() - start_time
                patent_analysis_requests.labels(
                    analysis_type=analysis_type,
                    success='true'
                ).inc()
                patent_analysis_duration.labels(
                    analysis_type=analysis_type
                ).observe(duration)

                if quality_score > 0:
                    patent_analysis_quality_score.labels(
                        analysis_type=analysis_type
                    ).set(quality_score)

                return result

            except Exception:
                # 记录失败指标
                duration = time.time() - start_time
                patent_analysis_requests.labels(
                    analysis_type=analysis_type,
                    success='false'
                ).inc()
                patent_analysis_duration.labels(
                    analysis_type=analysis_type
                ).observe(duration)
                raise

        return sync_wrapper
    return decorator


def track_intent_recognition(model_type: str = 'default'):
    """追踪意图识别业务指标"""
    def decorator(func):
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            intent_type = 'unknown'
            confidence = 0.0

            try:
                result = func(*args, **kwargs)

                # 从结果中提取意图和置信度
                if isinstance(result, dict):
                    intent_type = result.get('intent', 'unknown')
                    confidence = result.get('confidence', 0.0)

                # 记录延迟
                duration = time.time() - start_time
                intent_recognition_duration.labels(
                    model_type=model_type
                ).observe(duration)

                # 记录意图分布
                intent_distribution.labels(intent_type=intent_type).inc()

                # 记录置信度级别
                confidence_level = 'low' if confidence < 0.5 else 'medium' if confidence < 0.8 else 'high'
                intent_recognition_requests.labels(
                    intent_type=intent_type,
                    confidence_level=confidence_level
                ).inc()

                return result

            except Exception:
                # 记录失败
                duration = time.time() - start_time
                intent_recognition_duration.labels(
                    model_type=model_type
                ).observe(duration)
                raise

        return sync_wrapper
    return decorator


def track_user_interaction(interaction_type: str = 'general'):
    """追踪用户交互业务指标"""
    def decorator(func):
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = func(*args, **kwargs)

                # 记录成功交互
                duration = time.time() - start_time
                user_interaction_duration.labels(
                    interaction_type=interaction_type
                ).observe(duration)

                # 如果结果中包含满意度评分
                if isinstance(result, dict) and 'satisfaction' in result:
                    user_satisfaction_score.labels(
                        interaction_type=interaction_type
                    ).set(result['satisfaction'])

                return result

            except Exception:
                # 记录失败交互
                duration = time.time() - start_time
                user_interaction_duration.labels(
                    interaction_type=interaction_type
                ).observe(duration)
                raise

        return sync_wrapper
    return decorator


def track_reasoning_quality(reasoning_mode: str = 'basic'):
    """追踪推理质量业务指标"""
    def decorator(func):
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            time.time()
            steps = 0

            try:
                result = func(*args, **kwargs)

                # 从结果中提取推理步骤数和质量评分
                if isinstance(result, dict):
                    steps = result.get('steps', 0)
                    quality_score = result.get('quality_score', 0)

                    # 记录推理步骤
                    reasoning_steps_total.labels(
                        reasoning_mode=reasoning_mode
                    ).set(steps)

                    # 记录质量评分
                    if quality_score > 0:
                        reasoning_quality_score.labels(
                            reasoning_mode=reasoning_mode
                        ).set(quality_score)

                    # 记录采纳率
                    adoption_rate = result.get('adoption_rate', 0)
                    if adoption_rate > 0:
                        reasoning_adoption_rate.labels(
                            reasoning_mode=reasoning_mode
                        ).set(adoption_rate)

                return result

            except Exception:
                raise

        return sync_wrapper
    return decorator


# ============== 业务指标收集器类 ==============

class BusinessMetricsCollector:
    """业务指标收集器"""

    @staticmethod
    def record_patent_retrieval(search_type: str, total: int, found: int):
        """记录专利检索命中率"""
        hit_rate = found / total if total > 0 else 0
        patent_retrieval_hit_rate.labels(search_type=search_type).set(hit_rate)

    @staticmethod
    def record_intent_accuracy(intent_type: str, accuracy: float):
        """记录意图识别准确率"""
        intent_accuracy.labels(intent_type=intent_type).set(accuracy)

    @staticmethod
    def record_user_feedback(feedback_type: str, sentiment: str):
        """记录用户反馈"""
        user_feedback.labels(
            feedback_type=feedback_type,
            sentiment=sentiment
        ).inc()

    @staticmethod
    def record_decision_metrics(decision_type: str, accuracy: float, impact_score: float, adoption_rate: float):
        """记录决策质量指标"""
        decision_accuracy.labels(decision_type=decision_type).set(accuracy)
        decision_impact_score.labels(decision_type=decision_type).set(impact_score)
        decision_adoption_rate.labels(decision_type=decision_type).set(adoption_rate)

    @staticmethod
    def record_model_metrics(model_name: str, accuracy: float, loss: float, loss_type: str = 'cross_entropy'):
        """记录模型指标"""
        model_accuracy.labels(model_name=model_name, metric_type='accuracy').set(accuracy)
        model_loss.labels(model_name=model_name, loss_type=loss_type).set(loss)

    @staticmethod
    def record_kg_stats(graph_type: str, nodes: int, edges: int):
        """记录知识图谱统计"""
        kg_nodes_total.labels(graph_type=graph_type).set(nodes)
        kg_edges_total.labels(graph_type=graph_type).set(edges)

    @staticmethod
    def record_kg_query(query_type: str, success: bool, duration: float):
        """记录知识图谱查询"""
        kg_queries_total.labels(query_type=query_type, success=str(success).lower()).inc()
        kg_query_duration.labels(query_type=query_type).observe(duration)

    @staticmethod
    def record_learning_progress(sample_type: str, samples: int, convergence_rate: float):
        """记录学习进度"""
        learning_samples_total.labels(sample_type=sample_type).inc(samples)
        learning_convergence_rate.labels(algorithm='general').set(convergence_rate)


# 全局业务指标收集器实例
business_metrics = BusinessMetricsCollector()


# 便捷函数
def update_business_metrics(metrics_data: dict[str, Any]):
    """更新业务指标"""
    # 专利分析指标
    if 'patent_analysis' in metrics_data:
        data = metrics_data['patent_analysis']
        business_metrics.record_patent_retrieval(
            data.get('search_type', 'general'),
            data.get('total', 0),
            data.get('found', 0)
        )

    # 意图识别指标
    if 'intent_recognition' in metrics_data:
        data = metrics_data['intent_recognition']
        business_metrics.record_intent_accuracy(
            data.get('intent_type', 'unknown'),
            data.get('accuracy', 0.0)
        )

    # 决策质量指标
    if 'decision_quality' in metrics_data:
        data = metrics_data['decision_quality']
        business_metrics.record_decision_metrics(
            data.get('decision_type', 'general'),
            data.get('accuracy', 0.0),
            data.get('impact_score', 0.0),
            data.get('adoption_rate', 0.0)
        )

    # 模型指标
    if 'model_metrics' in metrics_data:
        data = metrics_data['model_metrics']
        business_metrics.record_model_metrics(
            data.get('model_name', 'unknown'),
            data.get('accuracy', 0.0),
            data.get('loss', 0.0),
            data.get('loss_type', 'cross_entropy')
        )

    # 知识图谱指标
    if 'kg_stats' in metrics_data:
        data = metrics_data['kg_stats']
        business_metrics.record_kg_stats(
            data.get('graph_type', 'general'),
            data.get('nodes', 0),
            data.get('edges', 0)
        )


if __name__ == "__main__":
    # 测试业务指标
    print("📊 测试业务指标导出...")

    # 模拟一些业务指标
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

    print("✅ 业务指标已更新")
    print("📊 访问 http://localhost:9100/metrics 查看指标")
