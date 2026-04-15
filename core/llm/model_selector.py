from __future__ import annotations
"""
统一LLM层 - 智能模型选择器
基于任务类型、成本、性能等因素自动选择最合适的模型

作者: Claude Code
日期: 2026-01-23
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from core.llm.base import DeploymentType, LLMRequest, ModelType, SelectionStrategy

logger = logging.getLogger(__name__)


@dataclass
class SelectionCriteria:
    """
    模型选择标准

    定义选择模型时的偏好和约束条件
    """

    task_type: str  # 任务类型
    strategy: SelectionStrategy = SelectionStrategy.BALANCED  # 选择策略

    # 约束条件
    max_cost: float | None = None  # 最大成本
    max_latency: float | None = None  # 最大延迟(秒)
    min_quality: float | None = None  # 最小质量分数

    # 偏好
    prefer_local: bool = False  # 是否偏好本地模型
    prefer_streaming: bool = False  # 是否偏好流式输出
    require_thinking: bool = False  # 是否要求思考模式


class IntelligentModelSelector:
    """
    智能模型选择器

    根据任务类型、策略、约束条件自动选择最合适的模型
    """

    def __init__(self, capability_registry):
        """
        初始化选择器

        Args:
            capability_registry: 模型能力注册表
        """
        self.registry = capability_registry
        self.selection_history: list[dict[str, Any]] = []

        # 任务类型到模型类型的映射
        # 2026-03-22 更新: 本地 qwen3.5 作为默认模型，支持多种任务类型
        self.task_to_model_type = {
            # 推理类任务 (日常推理用本地，复杂推理走 complex_reasoning_models)
            "novelty_analysis": ModelType.REASONING,
            "creativity_analysis": ModelType.REASONING,
            "invalidation_analysis": ModelType.REASONING,
            "oa_response": ModelType.REASONING,
            "reasoning": ModelType.REASONING,
            "complex_reasoning": ModelType.REASONING,
            "tech_analysis": ModelType.REASONING,
            "step_by_step_reasoning": ModelType.REASONING,
            # 对话类任务 (优先使用本地多模态模型 qwen3.5)
            "general_chat": ModelType.MULTIMODAL,  # 改为 MULTIMODAL 以支持 qwen3.5
            "conversation": ModelType.MULTIMODAL,
            "qa": ModelType.MULTIMODAL,
            "simple_chat": ModelType.MULTIMODAL,
            "simple_qa": ModelType.MULTIMODAL,
            "fast_analysis": ModelType.MULTIMODAL,
            # 专用任务
            "patent_search": ModelType.SPECIALIZED,
            "math_reasoning": ModelType.SPECIALIZED,
            "complex_analysis": ModelType.SPECIALIZED,
            # 编程任务
            "code_generation": ModelType.SPECIALIZED,
            "code_review": ModelType.SPECIALIZED,
            "code_refactoring": ModelType.SPECIALIZED,
            "debugging": ModelType.SPECIALIZED,
            "code_explanation": ModelType.SPECIALIZED,
            "test_generation": ModelType.SPECIALIZED,
            "code_completion": ModelType.SPECIALIZED,
            # 多模态任务
            "image_analysis": ModelType.MULTIMODAL,
            "multimodal": ModelType.MULTIMODAL,
            "chart_analysis": ModelType.MULTIMODAL,
            "document_analysis": ModelType.MULTIMODAL,
            "diagram_analysis": ModelType.MULTIMODAL,
            "visual_reasoning": ModelType.MULTIMODAL,
            "simple_visual_qa": ModelType.MULTIMODAL,
            "ocr": ModelType.MULTIMODAL,
        }

        # 默认模型映射 (任务类型 -> 默认模型ID)
        # 2026-03-22 更新: 本地优先策略，复杂推理使用 DeepSeek
        self.default_models = {
            # 多模态任务默认使用本地 qwen3.5
            ModelType.MULTIMODAL: "qwen3.5",
            # 推理任务默认使用本地 qwen3.5 (日常推理)
            ModelType.REASONING: "qwen3.5",
            # 对话任务默认使用本地 qwen3.5
            ModelType.CHAT: "qwen3.5",
        }

        # 高复杂度推理任务专用映射 (强制使用云端高质量模型)
        # 这些任务需要深度法律推理，本地7B模型不够准确
        self.complex_reasoning_models = {
            "novelty_analysis": "deepseek-reasoner",       # 新颖性分析
            "creativity_analysis": "deepseek-reasoner",    # 创造性判断
            "invalidation_analysis": "deepseek-reasoner",  # 无效宣告
            "oa_response": "deepseek-reasoner",            # 审查意见答复
            "complex_reasoning": "deepseek-reasoner",      # 复杂推理
            "math_reasoning": "deepseek-reasoner",         # 数学推理
        }

        # 策略权重配置
        self.strategy_weights = {
            SelectionStrategy.COST_OPTIMIZED: {"cost": 0.40, "quality": 0.30, "performance": 0.30},
            SelectionStrategy.PERFORMANCE_OPTIMIZED: {
                "cost": 0.20,
                "quality": 0.30,
                "performance": 0.50,
            },
            SelectionStrategy.QUALITY_OPTIMIZED: {
                "cost": 0.15,
                "quality": 0.60,
                "performance": 0.25,
            },
            SelectionStrategy.BALANCED: {"cost": 0.30, "quality": 0.35, "performance": 0.35},
            SelectionStrategy.LOCAL_FIRST: {
                "cost": 0.20,
                "quality": 0.30,
                "performance": 0.20,
                "local_bonus": 0.30,  # 本地模型额外加成
            },
        }

    async def select_model(
        self, request: LLMRequest, criteria: SelectionCriteria | None = None
    ) -> str | None:
        """
        智能选择最合适的模型

        选择流程:
        1. 根据任务类型筛选候选模型
        2. 根据策略对候选模型评分
        3. 应用约束条件过滤
        4. 返回最优模型

        Args:
            request: LLM请求
            criteria: 选择标准(可选)

        Returns:
            Optional[str]: 选中的模型ID,如果没有合适的模型返回None
        """
        # 1. 确定选择标准
        if criteria is None:
            criteria = SelectionCriteria(
                task_type=request.task_type,
                strategy=self._get_default_strategy(request.task_type),
                prefer_local=request.prefer_local,
                require_thinking=request.enable_thinking,
            )

        # 2. 获取候选模型
        candidates = await self._get_candidates(criteria.task_type, request)
        if not candidates:
            logger.warning(f"没有找到适合任务 {criteria.task_type} 的模型")
            return None

        # 3. 评分和排序
        scored_candidates = []
        for model_id in candidates:
            score = await self._score_model(model_id, request, criteria)
            scored_candidates.append((model_id, score))

        # 4. 排序(分数降序)
        scored_candidates.sort(key=lambda x: x[1], reverse=True)

        # 5. 应用约束条件
        for model_id, score in scored_candidates:
            if await self._check_constraints(model_id, request, criteria):
                logger.info(f"✅ 选择模型: {model_id} (评分: {score:.2f})")

                # 记录选择历史
                self.selection_history.append(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "task_type": criteria.task_type,
                        "model_id": model_id,
                        "score": score,
                        "strategy": criteria.strategy.value,
                    }
                )

                return model_id

        # 如果没有模型满足所有约束,返回评分最高的
        logger.warning("没有模型满足所有约束条件,返回评分最高的模型")
        return scored_candidates[0][0] if scored_candidates else None

    async def _get_candidates(self, task_type: str, request: LLMRequest) -> list[str]:
        """
        获取候选模型列表

        Args:
            task_type: 任务类型
            request: LLM请求

        Returns:
            list[str]: 候选模型ID列表
        """
        # 评估请求复杂度
        complexity = self._assess_complexity(request)
        logger.debug(f"📊 请求复杂度评估: {complexity:.2f} (任务: {task_type})")

        # 🎯 优先检查: 高复杂度推理任务专用模型
        if task_type in self.complex_reasoning_models:
            dedicated_model = self.complex_reasoning_models[task_type]
            logger.info(f"🎯 高复杂度推理任务 [{task_type}] → 强制使用 {dedicated_model}")
            return [dedicated_model]

        # 根据任务类型确定模型类型
        model_type = self.task_to_model_type.get(task_type, ModelType.CHAT)  # 默认使用对话模型

        # 获取该类型的所有模型
        candidates = self.registry.get_models_by_type(model_type)

        # 进一步筛选适合该任务的模型
        suitable_candidates = []
        for model_id in candidates:
            capability = self.registry.get_capability(model_id)
            if capability and capability.is_suitable_for(task_type):
                suitable_candidates.append(model_id)

        # 如果用户指定了偏好模型,优先考虑
        if request.preferred_model and request.preferred_model in suitable_candidates:
            suitable_candidates.remove(request.preferred_model)
            suitable_candidates.insert(0, request.preferred_model)
        else:
            # 将默认模型排在首位（如果存在）
            default_model = self.default_models.get(model_type)
            if default_model and default_model in suitable_candidates:
                suitable_candidates.remove(default_model)
                suitable_candidates.insert(0, default_model)
                logger.debug(f"🎯 使用默认模型: {default_model} (任务类型: {model_type.value})")

        # 基于复杂度进行智能排序
        suitable_candidates = self._sort_by_complexity(suitable_candidates, complexity, task_type)

        return suitable_candidates

    def _assess_complexity(self, request: LLMRequest) -> float:
        """
        评估请求复杂度

        Args:
            request: LLM请求

        Returns:
            float: 复杂度分数 (0.0-1.0)
        """
        complexity = 0.0

        # 1. 消息长度 (0-0.3分)
        message_len = len(request.message)
        if message_len > 2000:
            complexity += 0.3
        elif message_len > 1000:
            complexity += 0.2
        elif message_len > 500:
            complexity += 0.1

        # 2. 上下文复杂度 (0-0.2分)
        context_size = len(request.context) if request.context else 0
        if context_size > 10:
            complexity += 0.2
        elif context_size > 5:
            complexity += 0.1

        # 3. 任务类型固有复杂度 (0-0.3分)
        task_complexity = {
            "novelty_analysis": 0.3,
            "creativity_analysis": 0.3,
            "invalidation_analysis": 0.3,
            "oa_response": 0.25,
            "tech_analysis": 0.2,
            "complex_analysis": 0.2,
            "patent_search": 0.15,
            "code_generation": 0.2,
            "code_review": 0.15,
            "code_refactoring": 0.25,
            "debugging": 0.2,
            "image_analysis": 0.15,
            "general_chat": 0.05,
            "simple_chat": 0.0,
        }
        complexity += task_complexity.get(request.task_type, 0.1)

        # 4. 关键词检测 (0-0.2分)
        complex_keywords = [
            "分析",
            "评估",
            "推理",
            "判断",
            "对比",
            "综合",
            "三步法",
            "创造性",
            "新颖性",
            "审查意见",
            "技术方案",
            "区别特征",
            "现有技术",
        ]
        keyword_count = sum(1 for kw in complex_keywords if kw in request.message)
        complexity += min(0.2, keyword_count * 0.03)

        # 5. 思考模式要求 (+0.1分)
        if request.enable_thinking:
            complexity += 0.1

        # 6. Token要求 (0-0.1分)
        if request.max_tokens > 3000:
            complexity += 0.1
        elif request.max_tokens > 2000:
            complexity += 0.05

        return min(1.0, complexity)

    def _sort_by_complexity(
        self, candidates: list[str], complexity: float, task_type: str
    ) -> list[str]:
        """
        基于复杂度对候选模型排序

        Args:
            candidates: 候选模型列表
            complexity: 复杂度分数
            task_type: 任务类型

        Returns:
            list[str]: 排序后的候选模型列表
        """
        # 定义高复杂度偏好模型(高质量推理模型 - 云端)
        # 注意: 复杂推理任务已在 _get_candidates 中通过 complex_reasoning_models 强制路由
        high_complex_models = [
            "deepseek-reasoner",  # DeepSeek 推理模型 (首选)
            "glm-4-plus",         # 智谱高级推理
            "qwen-vl-max",        # 高级多模态
        ]
        # 定义中等复杂度偏好模型(平衡模型)
        medium_complex_models = [
            "qwen3.5",            # 本地多模态/推理 (本地首选)
            "glm-4-flash",        # 智谱快速推理
            "deepseek-coder-v2",  # 代码专用
            "qwen-vl-plus",       # 云端多模态
        ]
        # 定义低复杂度偏好模型(快速/成本优化模型)
        low_complex_models = [
            "qwen3.5",            # 本地首选 (免费)
            "deepseek-chat",      # 云端低成本
            "qwen2.5-7b-instruct-gguf",
        ]

        # 根据复杂度调整候选顺序
        if complexity >= 0.7:  # 高复杂度
            preferred = high_complex_models
        elif complexity >= 0.4:  # 中等复杂度
            preferred = medium_complex_models
        else:  # 低复杂度
            preferred = low_complex_models

        # 重新排序:优先选择匹配复杂度的模型
        sorted_candidates = []
        remaining = list(candidates)

        # 先添加首选模型
        for model_id in preferred:
            if model_id in remaining:
                sorted_candidates.append(model_id)
                remaining.remove(model_id)

        # 再添加其他模型
        sorted_candidates.extend(remaining)

        return sorted_candidates

    async def _score_model(
        self, model_id: str, request: LLMRequest, criteria: SelectionCriteria
    ) -> float:
        """
        对模型进行评分

        Args:
            model_id: 模型ID
            request: LLM请求
            criteria: 选择标准

        Returns:
            float: 评分(0-1)
        """
        capability = self.registry.get_capability(model_id)
        if not capability:
            return 0.0

        # 获取策略权重
        weights = self.strategy_weights.get(
            criteria.strategy, self.strategy_weights[SelectionStrategy.BALANCED]
        )

        # 计算各项得分
        cost_score = self._normalize_cost(capability.cost_per_1k_tokens)
        quality_score = capability.quality_score
        performance_score = self._normalize_latency(capability.avg_latency_ms)

        # 根据策略计算总分
        score = (
            cost_score * weights.get("cost", 0.33)
            + quality_score * weights.get("quality", 0.33)
            + performance_score * weights.get("performance", 0.33)
        )

        # 本地优先加成
        if criteria.prefer_local and capability.deployment == DeploymentType.LOCAL:
            bonus = weights.get("local_bonus", 0.2)
            score *= 1.0 + bonus

        return max(0.0, min(1.0, score))

    def _normalize_cost(self, cost: float) -> float:
        """
        成本归一化(成本越低分数越高)

        Args:
            cost: 每1K tokens成本

        Returns:
            float: 归一化后的成本分数(0-1)
        """
        max_cost = 0.1  # 假设最高成本为0.1元/1K tokens
        return max(0.0, 1.0 - (cost / max_cost))

    def _normalize_latency(self, latency_ms: float) -> float:
        """
        延迟归一化(延迟越低分数越高)

        Args:
            latency_ms: 平均延迟(毫秒)

        Returns:
            float: 归一化后的延迟分数(0-1)
        """
        max_latency = 5000  # 假设最大可接受延迟为5秒
        return max(0.0, 1.0 - (latency_ms / max_latency))

    async def _check_constraints(
        self, model_id: str, request: LLMRequest, criteria: SelectionCriteria
    ) -> bool:
        """
        检查约束条件

        Args:
            model_id: 模型ID
            request: LLM请求
            criteria: 选择标准

        Returns:
            bool: 是否满足所有约束条件
        """
        capability = self.registry.get_capability(model_id)
        if not capability:
            return False

        # 成本约束
        if criteria.max_cost:
            estimated_cost = capability.estimate_cost(request.max_tokens)
            if estimated_cost > criteria.max_cost:
                return False

        # 延迟约束
        if criteria.max_latency and capability.avg_latency_ms > criteria.max_latency * 1000:
            return False

        # 质量约束
        if criteria.min_quality and capability.quality_score < criteria.min_quality:
            return False

        # 功能需求
        if criteria.require_thinking and not capability.supports_thinking:
            return False

        return not (criteria.prefer_streaming and not capability.supports_streaming)

    def _get_default_strategy(self, task_type: str) -> SelectionStrategy:
        """
        根据任务类型获取默认策略

        Args:
            task_type: 任务类型

        Returns:
            SelectionStrategy: 默认策略
        """
        # 推理类任务默认使用质量优化
        if task_type in [
            "novelty_analysis",
            "creativity_analysis",
            "invalidation_analysis",
            "oa_response",
            "reflection",  # 反思任务需要高质量评估
            "quality_evaluation",  # 质量评估任务
        ]:
            return SelectionStrategy.QUALITY_OPTIMIZED

        # 日常对话默认使用成本优化
        if task_type in ["general_chat", "simple_chat", "conversation"]:
            return SelectionStrategy.COST_OPTIMIZED

        # 其他任务使用平衡策略
        return SelectionStrategy.BALANCED

    def get_selection_history(self) -> list[dict[str, Any]]:
        """
        获取选择历史记录

        Returns:
            list[Dict]: 选择历史记录
        """
        return self.selection_history.copy()

    def clear_selection_history(self):
        """清空选择历史记录"""
        self.selection_history.clear()
