#!/usr/bin/env python3
"""
Athena平台智能模型选择器
根据任务复杂度、成本预算、性能要求自动选择最适合的GLM模型
"""

import asyncio
import statistics
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from core.logging_config import setup_logging

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

class GLMModelType(Enum):
    """GLM模型类型枚举"""
    GLM_4_FLASH = 'glm-4-flash'
    GLM_4_AIR = 'glm-4-air'
    GLM_4_PLUS = 'glm-4-plus'
    CHATGLM3_6B = 'chatglm3-6b'

    @classmethod
    def get_all_models(cls) -> list[str]:
        return [model.value for model in cls]

class TaskComplexity(Enum):
    """任务复杂度枚举"""
    SIMPLE = 'simple'        # 简单任务：文本分类、关键词提取
    MEDIUM = 'medium'        # 中等任务：摘要生成、基础问答
    COMPLEX = 'complex'      # 复杂任务：深度分析、创意写作
    EXPERT = 'expert'        # 专家级任务：多步推理、专业分析

class PerformanceTier(Enum):
    """性能等级枚举"""
    LOW = 'low'            # 低性能要求：可以接受较慢响应
    MEDIUM = 'medium'       # 中等性能要求：一般业务需求
    HIGH = 'high'          # 高性能要求：实时交互
    EXTREME = 'extreme'    # 极高性能要求：高频调用

@dataclass
class TaskRequirement:
    """任务需求定义"""
    task_id: str
    task_type: str
    complexity: TaskComplexity
    performance_tier: PerformanceTier
    cost_budget: float | None = None
    accuracy_requirement: float = 0.8
    latency_requirement: float | None = None  # 毫秒
    concurrency_requirement: int = 1
    priority: int = 1
    context_window: int | None = None
    special_features: list[str] = field(default_factory=list)

@dataclass
class ModelCapability:
    """模型能力评估"""
    model_type: GLMModelType
    accuracy_score: float
    speed_score: float
    cost_efficiency: float
    complexity_handling: TaskComplexity
    max_tokens: int
    concurrency_support: int
    special_features: list[str] = field(default_factory=list)

@dataclass
class SelectionResult:
    """模型选择结果"""
    selected_model: GLMModelType
    confidence: float
    reasoning: list[str]
    expected_cost: float
    expected_latency: float
    expected_accuracy: float
    alternatives: list[tuple[GLMModelType, float] = field(default_factory=list)

class ModelPerformanceTracker:
    """模型性能跟踪器"""

    def __init__(self):
        self.performance_history = {}
        self.load_performance_data()

    def load_performance_data(self) -> Any | None:
        """加载历史性能数据"""
        # 这里可以从文件或数据库加载，现在使用模拟数据
        for model in GLMModelType:
            self.performance_history[model.value] = {
                'total_calls': 0,
                'successful_calls': 0,
                'total_latency': 0.0,
                'total_cost': 0.0,
                'accuracy_scores': [],
                'last_update': datetime.now()
            }

    def record_performance(self, model: GLMModelType, latency: float,
                          cost: float, success: bool, accuracy: float = None):
        """记录模型性能"""
        history = self.performance_history[model.value]
        history['total_calls'] += 1
        history['total_latency'] += latency
        history['total_cost'] += cost

        if success:
            history['successful_calls'] += 1
            if accuracy:
                history['accuracy_scores'].append(accuracy)

        history['last_update'] = datetime.now()

    def get_performance_stats(self, model: GLMModelType) -> dict[str, Any]:
        """获取模型性能统计"""
        history = self.performance_history.get(model.value, {})

        if history['total_calls'] == 0:
            return {
                'avg_latency': 0,
                'avg_cost': 0,
                'success_rate': 0,
                'avg_accuracy': 0
            }

        avg_latency = history['total_latency'] / history['total_calls']
        avg_cost = history['total_cost'] / history['total_calls']
        success_rate = history['successful_calls'] / history['total_calls']

        avg_accuracy = 0
        if history['accuracy_scores']:
            avg_accuracy = statistics.mean(history['accuracy_scores'])

        return {
            'avg_latency': avg_latency,
            'avg_cost': avg_cost,
            'success_rate': success_rate,
            'avg_accuracy': avg_accuracy
        }

class IntelligentModelSelector:
    """智能模型选择器"""

    def __init__(self):
        """初始化智能选择器"""
        self.model_capabilities = self._initialize_model_capabilities()
        self.performance_tracker = ModelPerformanceTracker()
        self.selection_rules = self._initialize_selection_rules()
        self.learning_weights = {
            'performance': 0.4,
            'cost': 0.3,
            'accuracy': 0.2,
            'stability': 0.1
        }
        self.adaptation_history = []

    def _initialize_model_capabilities(self) -> dict[GLMModelType, ModelCapability]:
        """初始化模型能力评估"""
        return {
            GLMModelType.GLM_4_FLASH: ModelCapability(
                model_type=GLMModelType.GLM_4_FLASH,
                accuracy_score=0.75,
                speed_score=0.95,
                cost_efficiency=0.90,
                complexity_handling=TaskComplexity.SIMPLE,
                max_tokens=128000,
                concurrency_support=100,
                special_features=['快速响应', '高并发', '成本低']
            ),

            GLMModelType.GLM_4_AIR: ModelCapability(
                model_type=GLMModelType.GLM_4_AIR,
                accuracy_score=0.82,
                speed_score=0.85,
                cost_efficiency=0.75,
                complexity_handling=TaskComplexity.MEDIUM,
                max_tokens=128000,
                concurrency_support=50,
                special_features=['均衡性能', '中文优化']
            ),

            GLMModelType.GLM_4_PLUS: ModelCapability(
                model_type=GLMModelType.GLM_4_PLUS,
                accuracy_score=0.92,
                speed_score=0.70,
                cost_efficiency=0.60,
                complexity_handling=TaskComplexity.COMPLEX,
                max_tokens=128000,
                concurrency_support=20,
                special_features=['高精度', '深度理解', '专业领域']
            ),

            GLMModelType.CHATGLM3_6B: ModelCapability(
                model_type=GLMModelType.CHATGLM3_6B,
                accuracy_score=0.70,
                speed_score=0.60,
                cost_efficiency=0.95,
                complexity_handling=TaskComplexity.MEDIUM,
                max_tokens=8192,
                concurrency_support=10,
                special_features=['本地部署', '数据安全', '可定制']
            )
        }

    def _initialize_selection_rules(self) -> dict[str, dict]:
        """初始化选择规则"""
        return {
            TaskComplexity.SIMPLE.value: {
                'primary_models': [GLMModelType.GLM_4_FLASH],
                'fallback_models': [GLMModelType.CHATGLM3_6B],
                'weights': {
                    'speed': 0.5,
                    'cost': 0.3,
                    'accuracy': 0.2
                }
            },
            TaskComplexity.MEDIUM.value: {
                'primary_models': [GLMModelType.GLM_4_AIR],
                'fallback_models': [GLMModelType.GLM_4_FLASH, GLMModelType.CHATGLM3_6B],
                'weights': {
                    'accuracy': 0.4,
                    'speed': 0.3,
                    'cost': 0.3
                }
            },
            TaskComplexity.COMPLEX.value: {
                'primary_models': [GLMModelType.GLM_4_PLUS],
                'fallback_models': [GLMModelType.GLM_4_AIR],
                'weights': {
                    'accuracy': 0.6,
                    'speed': 0.2,
                    'cost': 0.2
                }
            },
            TaskComplexity.EXPERT.value: {
                'primary_models': [GLMModelType.GLM_4_PLUS],
                'fallback_models': [GLMModelType.GLM_4_AIR],
                'weights': {
                    'accuracy': 0.7,
                    'speed': 0.15,
                    'cost': 0.15
                }
            }
        }

    async def select_optimal_model(self, requirement: TaskRequirement) -> SelectionResult:
        """选择最优模型"""
        logger.info(f"开始为任务 {requirement.task_id} 选择最优模型")

        # 1. 过滤满足基本要求的模型
        candidate_models = self._filter_candidates(requirement)

        if not candidate_models:
            # 如果没有满足要求的模型，放宽条件
            candidate_models = self._relax_requirements(requirement)

        # 2. 计算每个模型的匹配分数
        model_scores = []
        for model in candidate_models:
            score = self._calculate_model_score(model, requirement)
            model_scores.append((model, score))

        # 3. 排序并选择最佳模型
        model_scores.sort(key=lambda x: x[1], reverse=True)

        selected_model = model_scores[0][0]
        confidence = self._calculate_confidence(model_scores, requirement)

        # 4. 生成选择理由
        reasoning = self._generate_reasoning(selected_model, requirement, model_scores)

        # 5. 预估性能指标
        expected_cost, expected_latency, expected_accuracy = self._estimate_performance(
            selected_model, requirement
        )

        # 6. 准备备选方案
        alternatives = [(model, score) for model, score in model_scores[1:3] if len(model_scores) > 1 else []

        result = SelectionResult(
            selected_model=selected_model,
            confidence=confidence,
            reasoning=reasoning,
            expected_cost=expected_cost,
            expected_latency=expected_latency,
            expected_accuracy=expected_accuracy,
            alternatives=alternatives
        )

        # 7. 记录选择历史
        self._record_selection(requirement, result)

        logger.info(f"选择模型 {selected_model.value}，置信度 {confidence:.2f}")
        return result

    def _filter_candidates(self, requirement: TaskRequirement) -> list[GLMModelType]:
        """过滤满足基本要求的候选模型"""
        candidates = []

        for model, capability in self.model_capabilities.items():
            # 检查复杂度处理能力
            if self._complexity_match(requirement.complexity, capability.complexity_handling):
                # 检查并发要求
                if capability.concurrency_support >= requirement.concurrency_requirement:
                    # 检查上下文窗口要求
                    if requirement.context_window is None or capability.max_tokens >= requirement.context_window:
                        # 检查特殊功能要求
                        if self._check_special_features(requirement.special_features, capability.special_features):
                            candidates.append(model)

        return candidates

    def _relax_requirements(self, requirement: TaskRequirement) -> list[GLMModelType]:
        """放宽要求以获得候选模型"""
        candidates = []

        for model, capability in self.model_capabilities.items():
            # 仅检查最基本的要求
            if capability.concurrency_support >= max(1, requirement.concurrency_requirement // 2):
                if requirement.context_window is None or capability.max_tokens >= requirement.context_window // 2:
                    candidates.append(model)

        return candidates if candidates else list(GLMModelType)

    def _complexity_match(self, required: TaskComplexity, capable: TaskComplexity) -> bool:
        """检查复杂度匹配"""
        complexity_levels = {
            TaskComplexity.SIMPLE: 1,
            TaskComplexity.MEDIUM: 2,
            TaskComplexity.COMPLEX: 3,
            TaskComplexity.EXPERT: 4
        }
        return complexity_levels[capable] >= complexity_levels[required]

    def _check_special_features(self, required: list[str], available: list[str]) -> bool:
        """检查特殊功能要求"""
        if not required:
            return True

        for feature in required:
            if feature not in available:
                return False

        return True

    def _calculate_model_score(self, model: GLMModelType, requirement: TaskRequirement) -> float:
        """计算模型匹配分数"""
        capability = self.model_capabilities[model]
        rule = self.selection_rules[requirement.complexity.value]
        weights = rule['weights']

        # 获取历史性能数据
        perf_stats = self.performance_tracker.get_performance_stats(model)

        # 计算各项得分
        accuracy_score = self._normalize_score(
            capability.accuracy_score, 0, 1, weights.get('accuracy', 0.2)
        )

        speed_score = self._normalize_score(
            capability.speed_score, 0, 1, weights.get('speed', 0.2)
        )

        cost_score = self._normalize_score(
            capability.cost_efficiency, 0, 1, weights.get('cost', 0.2)
        )

        # 考虑历史性能稳定性
        stability_score = 0
        if perf_stats['success_rate'] > 0:
            stability_score = perf_stats['success_rate'] * self.learning_weights['stability']

        # 预算约束
        budget_penalty = 0
        if requirement.cost_budget:
            estimated_cost = self._estimate_model_cost(model, requirement)
            if estimated_cost > requirement.cost_budget:
                budget_penalty = (estimated_cost - requirement.cost_budget) / requirement.cost_budget
                budget_penalty = min(budget_penalty, 0.5)  # 最大惩罚0.5

        # 延迟约束
        latency_penalty = 0
        if requirement.latency_requirement:
            estimated_latency = self._estimate_model_latency(model, requirement)
            if estimated_latency > requirement.latency_requirement:
                latency_penalty = (estimated_latency - requirement.latency_requirement) / requirement.latency_requirement
                latency_penalty = min(latency_penalty, 0.5)

        # 综合得分
        total_score = (accuracy_score + speed_score + cost_score + stability_score) - budget_penalty - latency_penalty

        return max(0, total_score)

    def _normalize_score(self, value: float, min_val: float, max_val: float, weight: float) -> float:
        """标准化分数"""
        normalized = (value - min_val) / (max_val - min_val)
        return normalized * weight

    def _estimate_model_cost(self, model: GLMModelType, requirement: TaskRequirement) -> float:
        """估算模型使用成本"""
        # 简化的成本估算
        base_costs = {
            GLMModelType.GLM_4_FLASH: 0.01,
            GLMModelType.GLM_4_AIR: 0.02,
            GLMModelType.GLM_4_PLUS: 0.05,
            GLMModelType.CHATGLM3_6B: 0.001  # 本地部署成本更低
        }

        complexity_multiplier = {
            TaskComplexity.SIMPLE: 1.0,
            TaskComplexity.MEDIUM: 1.5,
            TaskComplexity.COMPLEX: 2.5,
            TaskComplexity.EXPERT: 4.0
        }

        base_cost = base_costs[model]
        multiplier = complexity_multiplier[requirement.complexity]

        return base_cost * multiplier

    def _estimate_model_latency(self, model: GLMModelType, requirement: TaskRequirement) -> float:
        """估算模型延迟"""
        base_latencies = {
            GLMModelType.GLM_4_FLASH: 200,   # 毫秒
            GLMModelType.GLM_4_AIR: 400,
            GLMModelType.GLM_4_PLUS: 800,
            GLMModelType.CHATGLM3_6B: 1200
        }

        complexity_multiplier = {
            TaskComplexity.SIMPLE: 1.0,
            TaskComplexity.MEDIUM: 1.8,
            TaskComplexity.COMPLEX: 3.0,
            TaskComplexity.EXPERT: 5.0
        }

        base_latency = base_latencies[model]
        multiplier = complexity_multiplier[requirement.complexity]

        # 考虑并发影响
        concurrency_impact = 1 + (requirement.concurrency_requirement - 1) * 0.1

        return base_latency * multiplier * concurrency_impact

    def _calculate_confidence(self, model_scores: list[tuple[GLMModelType, float],
                            requirement: TaskRequirement) -> float:
        """计算选择置信度"""
        if len(model_scores) < 2:
            return 0.5

        # 计算最佳模型与次佳模型的分数差距
        top_score = model_scores[0][1]
        second_score = model_scores[1][1]

        if second_score == 0:
            return 1.0

        score_diff = (top_score - second_score) / second_score
        confidence = min(0.9, 0.5 + score_diff * 0.2)

        # 考虑历史成功率
        top_model = model_scores[0][0]
        perf_stats = self.performance_tracker.get_performance_stats(top_model)

        if perf_stats['success_rate'] > 0:
            confidence = confidence * 0.7 + perf_stats['success_rate'] * 0.3

        return confidence

    def _generate_reasoning(self, selected_model: GLMModelType, requirement: TaskRequirement,
                          model_scores: list[tuple[GLMModelType, float]) -> list[str]:
        """生成选择理由"""
        capability = self.model_capabilities[selected_model]
        reasoning = []

        # 基本匹配理由
        reasoning.append(f"模型 {selected_model.value} 能处理 {requirement.complexity.value} 复杂度任务")

        # 性能优势
        if capability.speed_score > 0.8:
            reasoning.append('该模型响应速度快，满足性能要求')

        if capability.accuracy_score > 0.85:
            reasoning.append('该模型准确性高，满足质量要求')

        if capability.cost_efficiency > 0.8:
            reasoning.append('该模型成本效益好，符合经济性要求')

        # 特殊功能匹配
        matched_features = set(requirement.special_features) & set(capability.special_features)
        if matched_features:
            reasoning.append(f"模型支持需要的特殊功能: {', '.join(matched_features)}")

        # 并发能力
        if capability.concurrency_support >= requirement.concurrency_requirement:
            reasoning.append(f"模型支持 {capability.concurrency_support} 并发，满足并发需求")

        # 预算考虑
        if requirement.cost_budget:
            estimated_cost = self._estimate_model_cost(selected_model, requirement)
            if estimated_cost <= requirement.cost_budget:
                reasoning.append(f"预估成本 {estimated_cost:.4f} 在预算范围内")

        # 对比优势
        if len(model_scores) > 1:
            top_score = model_scores[0][1]
            second_score = model_scores[1][1]
            if top_score > second_score * 1.2:
                reasoning.append('综合评分显著优于其他候选模型')

        return reasoning

    def _estimate_performance(self, model: GLMModelType, requirement: TaskRequirement) -> tuple[float, float, float]:
        """估算性能指标"""
        capability = self.model_capabilities[model]

        # 基础性能指标
        base_cost = self._estimate_model_cost(model, requirement)
        base_latency = self._estimate_model_latency(model, requirement)
        base_accuracy = capability.accuracy_score

        # 根据复杂度调整
        complexity_factor = {
            TaskComplexity.SIMPLE: 1.0,
            TaskComplexity.MEDIUM: 0.95,
            TaskComplexity.COMPLEX: 0.90,
            TaskComplexity.EXPERT: 0.85
        }

        adjusted_accuracy = base_accuracy * complexity_factor[requirement.complexity]

        return base_cost, base_latency, adjusted_accuracy

    def _record_selection(self, requirement: TaskRequirement, result: SelectionResult) -> Any:
        """记录选择历史"""
        record = {
            'timestamp': datetime.now().isoformat(),
            'task_id': requirement.task_id,
            'task_type': requirement.task_type,
            'complexity': requirement.complexity.value,
            'selected_model': result.selected_model.value,
            'confidence': result.confidence,
            'expected_cost': result.expected_cost,
            'expected_latency': result.expected_latency
        }

        self.adaptation_history.append(record)

        # 限制历史记录数量
        if len(self.adaptation_history) > 1000:
            self.adaptation_history = self.adaptation_history[-500:]

    def update_model_feedback(self, task_id: str, model: GLMModelType,
                            actual_cost: float, actual_latency: float,
                            success: bool, accuracy: float = None):
        """更新模型反馈"""
        self.performance_tracker.record_performance(
            model, actual_latency, actual_cost, success, accuracy
        )

        # 记录到选择历史
        for record in reversed(self.adaptation_history):
            if record.get('task_id') == task_id and record.get('selected_model') == model.value:
                record['actual_cost'] = actual_cost
                record['actual_latency'] = actual_latency
                record['success'] = success
                record['accuracy'] = accuracy
                break

    def get_model_recommendations(self, task_type: str, count: int = 3) -> list[dict[str, Any]:
        """获取模型推荐"""
        recommendations = []

        # 统计该任务类型的历史选择
        task_history = [r for r in self.adaptation_history if r.get('task_type') == task_type]

        if not task_history:
            # 没有历史记录，返回默认推荐
            default_models = [GLMModelType.GLM_4_AIR, GLMModelType.GLM_4_FLASH, GLMModelType.GLM_4_PLUS]
            for model in default_models:
                capability = self.model_capabilities[model]
                recommendations.append({
                    'model': model.value,
                    'reason': '通用推荐模型',
                    'expected_accuracy': capability.accuracy_score,
                    'expected_speed': capability.speed_score
                })
        else:
            # 基于历史表现推荐
            model_performance = {}

            for record in task_history:
                model_name = record.get('selected_model')
                if model_name not in model_performance:
                    model_performance[model_name] = {
                        'count': 0,
                        'success_count': 0,
                        'total_cost': 0,
                        'total_latency': 0
                    }

                stats = model_performance[model_name]
                stats['count'] += 1

                if record.get('success', True):
                    stats['success_count'] += 1

                stats['total_cost'] += record.get('actual_cost', record.get('expected_cost', 0))
                stats['total_latency'] += record.get('actual_latency', record.get('expected_latency', 0))

            # 计算综合评分并排序
            model_scores = []
            for model_name, stats in model_performance.items():
                if stats['count'] == 0:
                    continue

                success_rate = stats['success_count'] / stats['count']
                avg_cost = stats['total_cost'] / stats['count']
                avg_latency = stats['total_latency'] / stats['count']

                # 综合评分
                score = (success_rate * 0.5 +
                        (1 - min(avg_cost, 0.1) / 0.1) * 0.3 +
                        (1 - min(avg_latency, 1000) / 1000) * 0.2)

                model_scores.append((model_name, score, {
                    'success_rate': success_rate,
                    'avg_cost': avg_cost,
                    'avg_latency': avg_latency
                }))

            model_scores.sort(key=lambda x: x[1], reverse=True)

            # 生成推荐
            for model_name, score, stats in model_scores[:count]:
                model_type = GLMModelType(model_name)
                capability = self.model_capabilities[model_type]
                recommendations.append({
                    'model': model_name,
                    'reason': f"基于历史{stats['success_rate']:.1%}成功率推荐",
                    'expected_accuracy': capability.accuracy_score,
                    'expected_speed': capability.speed_score,
                    'historical_stats': stats
                })

        return recommendations

    def get_performance_report(self) -> dict[str, Any]:
        """获取性能报告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_selections': len(self.adaptation_history),
            'model_performance': {},
            'selection_trends': {},
            'recommendations': []
        }

        # 模型性能统计
        for model in GLMModelType:
            stats = self.performance_tracker.get_performance_stats(model)
            report['model_performance'][model.value] = stats

        # 选择趋势（最近100次）
        recent_selections = self.adaptation_history[-100:]
        model_counts = {}

        for record in recent_selections:
            model_name = record.get('selected_model')
            model_counts[model_name] = model_counts.get(model_name, 0) + 1

        total_recent = len(recent_selections)
        report['selection_trends'] = {
            model_name: {
                'count': count,
                'percentage': count / total_recent if total_recent > 0 else 0
            }
            for model_name, count in model_counts.items()
        }

        # 优化建议
        report['recommendations'] = self._generate_optimization_recommendations()

        return report

    def _generate_optimization_recommendations(self) -> list[str]:
        """生成优化建议"""
        recommendations = []

        # 分析最近的性能数据
        recent_history = self.adaptation_history[-50:]

        if len(recent_history) < 10:
            return ['数据不足，需要更多选择历史来生成建议']

        # 成功率分析
        successful_tasks = sum(1 for r in recent_history if r.get('success', True))
        success_rate = successful_tasks / len(recent_history)

        if success_rate < 0.8:
            recommendations.append('整体成功率偏低，建议调整选择算法或考虑更稳定的模型')

        # 成本分析
        total_cost = sum(r.get('actual_cost', r.get('expected_cost', 0)) for r in recent_history)
        avg_cost = total_cost / len(recent_history)

        if avg_cost > 0.05:
            recommendations.append('平均使用成本偏高，建议增加成本权重或使用更经济的模型')

        # 模型使用分布
        model_usage = {}
        for record in recent_history:
            model = record.get('selected_model')
            model_usage[model] = model_usage.get(model, 0) + 1

        if len(model_usage) == 1:
            recommendations.append('模型选择过于集中，建议增加多样性以降低风险')

        return recommendations

# 全局选择器实例
_intelligent_selector = None

def get_intelligent_model_selector() -> IntelligentModelSelector:
    """获取智能模型选择器实例"""
    global _intelligent_selector
    if _intelligent_selector is None:
        _intelligent_selector = IntelligentModelSelector()
    return _intelligent_selector

# 工具函数
def create_task_requirement(task_id: str, task_type: str, complexity: str,
                          performance_tier: str = 'medium', **kwargs) -> TaskRequirement:
    """创建任务需求对象"""
    return TaskRequirement(
        task_id=task_id,
        task_type=task_type,
        complexity=TaskComplexity(complexity),
        performance_tier=PerformanceTier(performance_tier),
        **kwargs
    )

async def quick_model_selection(task_id: str, task_type: str, description: str) -> SelectionResult:
    """快速模型选择"""
    selector = get_intelligent_model_selector()

    # 根据描述自动推断复杂度
    complexity = TaskComplexity.MEDIUM
    if any(word in description.lower() for word in ['简单', '快速', '基础']):
        complexity = TaskComplexity.SIMPLE
    elif any(word in description.lower() for word in ['复杂', '深度', '专家', '专业']):
        complexity = TaskComplexity.COMPLEX

    requirement = TaskRequirement(
        task_id=task_id,
        task_type=task_type,
        complexity=complexity,
        performance_tier=PerformanceTier.MEDIUM
    )

    return await selector.select_optimal_model(requirement)

if __name__ == '__main__':
    async def test_model_selector():
        """测试模型选择器"""
        selector = get_intelligent_model_selector()

        # 测试不同类型的任务
        test_tasks = [
            TaskRequirement(
                task_id='test_1',
                task_type='文本分类',
                complexity=TaskComplexity.SIMPLE,
                performance_tier=PerformanceTier.HIGH,
                cost_budget=0.02
            ),
            TaskRequirement(
                task_id='test_2',
                task_type='专利分析',
                complexity=TaskComplexity.COMPLEX,
                performance_tier=PerformanceTier.MEDIUM,
                accuracy_requirement=0.9
            ),
            TaskRequirement(
                task_id='test_3',
                task_type='摘要生成',
                complexity=TaskComplexity.MEDIUM,
                performance_tier=PerformanceTier.MEDIUM
            )
        ]

        for task in test_tasks:
            result = await selector.select_optimal_model(task)
            logger.info(f"\n任务 {task.task_id}:")
            logger.info(f"  选择模型: {result.selected_model.value}")
            logger.info(f"  置信度: {result.confidence:.2f}")
            logger.info(f"  理由: {'; '.join(result.reasoning)}")
            logger.info(f"  预期成本: {result.expected_cost:.4f}")
            logger.info(f"  预期延迟: {result.expected_latency:.0f}ms")
            logger.info(f"  预期准确率: {result.expected_accuracy:.2f}")

        # 获取性能报告
        report = selector.get_performance_report()
        logger.info("\n性能报告:")
        logger.info(f"  总选择次数: {report['total_selections']}")
        logger.info(f"  模型性能: {report['model_performance']}")

    asyncio.run(test_model_selector())
