
"""
智能模型路由系统 - 任务复杂度分析与自动降级

基于 Hermes Agent 的设计理念，实现智能的模型路由策略：
- 任务复杂度分析：基于消息长度、关键词、任务类型等评估
- 自动降级：简单任务自动路由到低成本模型
- 成本监控：实时跟踪成本节省情况

核心特性:
1. 复杂度评分 (0.0-1.0)
2. 三层模型架构 (经济层/平衡层/高级层)
3. 专利法律场景的复杂度规则
4. 成本节省统计

作者: Athena平台团队
创建时间: 2026-03-19
版本: v1.0.0
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from core.ai.llm.base import LLMRequest

logger = logging.getLogger(__name__)


@dataclass
class ComplexityScore:
    """
    复杂度评分结果

    详细记录各维度的评分情况。
    """

    total: float  # 总分 (0.0-1.0)
    length_score: float  # 长度评分 (0-0.2)
    keyword_score: float  # 关键词评分 (0-0.3)
    task_type_score: float  # 任务类型评分 (0-0.3)
    context_score: float  # 上下文评分 (0-0.2)

    # 详细信息
    matched_keywords: list[str] = field(default_factory=list)
    matched_rules: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        return (
            f"ComplexityScore(total={self.total:.2f}, "
            f"length={self.length_score:.2f}, "
            f"keyword={self.keyword_score:.2f}, "
            f"task={self.task_type_score:.2f}, "
            f"context={self.context_score:.2f})"
        )


@dataclass
class RoutingDecision:
    """
    路由决策结果

    记录路由决策的详细信息。
    """

    selected_layer: str  # 选择的模型层 (economy/balanced/premium)
    selected_model: str  # 选择的模型
    complexity_score: float  # 复杂度分数
    estimated_cost: float  # 预估成本 (元/1K tokens)
    cost_saved: float  # 相比高级模型节省的成本
    reason: str  # 路由原因
    timestamp: datetime = field(default_factory=datetime.now)


class TaskComplexityAnalyzer:
    """
    任务复杂度分析器

    基于多维度评估任务复杂度，为模型路由提供决策依据。
    """

    # ========================================
    # 专利法律场景的复杂度规则
    # ========================================
    LEGAL_COMPLEXITY_RULES: dict[str, float] = {
        # 简单任务 (complexity < 0.3) - 可降级到经济模型
        "simple_qa": 0.1,  # 简单问答
        "format_conversion": 0.15,  # 格式转换
        "basic_search": 0.2,  # 基础检索
        "simple_summary": 0.2,  # 简单摘要
        "text_cleaning": 0.15,  # 文本清理
        "grammar_check": 0.2,  # 语法检查
        # 中等任务 (0.3 <= complexity < 0.7) - 使用平衡模型
        "patent_search": 0.4,  # 专利检索
        "document_summary": 0.5,  # 文档摘要
        "claim_analysis": 0.55,  # 权利要求分析
        "tech_comparison": 0.6,  # 技术对比
        "legal_research": 0.5,  # 法律研究
        # 复杂任务 (complexity >= 0.7) - 必须使用高级模型
        "novelty_analysis": 0.8,  # 新颖性分析
        "creativity_analysis": 0.85,  # 创造性分析
        "oa_response": 0.9,  # 审查意见答复
        "invalidation_analysis": 0.95,  # 无效宣告分析
        "infringement_analysis": 0.85,  # 侵权分析
        "legal_opinion": 0.9,  # 法律意见书
        "complex_reasoning": 0.85,  # 复杂推理
    }

    # 专利法律关键词复杂度权重
    KEYWORD_COMPLEXITY: dict[str, dict[str, list[str]]] = {
        "high": {
            # 高复杂度关键词 (每个 0.05 分)
            "legal": [
                "三步法",
                "区别特征",
                "技术启示",
                "显而易见",
                "创造性高度",
                "等同原则",
                "全面覆盖",
                "禁止反悔",
                "权利要求解释",
                "技术方案分解",
            ],
            "patent": [
                "新颖性",
                "创造性",
                "实用性",
                "专利性",
                "审查意见",
                "意见陈述",
                "权利要求修改",
            ],
        },
        "medium": {
            # 中等复杂度关键词 (每个 0.02 分)
            "legal": [
                "专利",
                "发明",
                "实用新型",
                "外观设计",
                "申请",
                "授权",
                "无效",
                "侵权",
            ],
            "patent": [
                "技术特征",
                "实施例",
                "技术方案",
                "对比文件",
                "现有技术",
                "检索",
                "分析",
            ],
        },
        "low": {
            # 低复杂度关键词 (每个 0.01 分)
            "general": [
                "什么",
                "如何",
                "怎样",
                "为什么",
                "介绍",
                "说明",
                "解释",
                "定义",
            ],
        },
    }

    def __init__(self):
        """初始化复杂度分析器"""
        self.analysis_history: list[ComplexityScore] = []

    def analyze(self, request: LLMRequest) -> ComplexityScore:
        """
        分析任务复杂度

        Args:
            request: LLM 请求

        Returns:
            ComplexityScore 复杂度评分
        """
        message = request.message if isinstance(request.message, str) else str(request.message)
        context = request.context or {}

        # 1. 长度评分 (0-0.2)
        length_score = self._score_length(message)

        # 2. 关键词评分 (0-0.3)
        keyword_score, matched_keywords = self._score_keywords(message)

        # 3. 任务类型评分 (0-0.3)
        task_type_score, matched_rules = self._score_task_type(request.task_type)

        # 4. 上下文评分 (0-0.2)
        context_score = self._score_context(context)

        # 计算总分
        total = min(1.0, length_score + keyword_score + task_type_score + context_score)

        score = ComplexityScore(
            total=total,
            length_score=length_score,
            keyword_score=keyword_score,
            task_type_score=task_type_score,
            context_score=context_score,
            matched_keywords=matched_keywords,
            matched_rules=matched_rules,
        )

        # 记录历史
        self.analysis_history.append(score)

        logger.debug(f"📊 复杂度分析: {score}")
        return score

    def _score_length(self, message: str) -> float:
        """
        消息长度评分

        Args:
            message: 消息内容

        Returns:
            长度评分 (0-0.2)
        """
        length = len(message)

        if length > 2000:
            return 0.2
        elif length > 1000:
            return 0.15
        elif length > 500:
            return 0.1
        elif length > 200:
            return 0.05
        return 0.02

    def _score_keywords(self, message: str) -> tuple[float, list[str]]:
        """
        关键词复杂度评分

        Args:
            message: 消息内容

        Returns:
            (评分, 匹配的关键词列表)
        """
        score = 0.0
        matched_keywords = []

        # 高复杂度关键词
        for _, keywords in self.KEYWORD_COMPLEXITY["high"].items():
            for kw in keywords:
                if kw in message:
                    score += 0.05
                    matched_keywords.append(kw)

        # 中等复杂度关键词
        for _, keywords in self.KEYWORD_COMPLEXITY["medium"].items():
            for kw in keywords:
                if kw in message:
                    score += 0.02
                    matched_keywords.append(kw)

        # 低复杂度关键词
        for _, keywords in self.KEYWORD_COMPLEXITY["low"].items():
            for kw in keywords:
                if kw in message:
                    score += 0.01
                    matched_keywords.append(kw)

        # 限制最大分数
        score = min(0.3, score)

        return score, matched_keywords

    def _score_task_type(self, task_type: Optional[str]) -> tuple[float, list[str]]:
        """
        任务类型评分

        Args:
            task_type: 任务类型

        Returns:
            (评分, 匹配的规则列表)
        """
        if not task_type:
            return 0.15, []  # 默认中等复杂度

        # 精确匹配
        if task_type in self.LEGAL_COMPLEXITY_RULES:
            return self.LEGAL_COMPLEXITY_RULES[task_type], [task_type]

        # 模糊匹配
        matched_rules = []
        max_score = 0.0

        for rule_type, rule_score in self.LEGAL_COMPLEXITY_RULES.items():
            # 检查任务类型是否包含规则关键词
            if rule_type in task_type or task_type in rule_type:
                if rule_score > max_score:
                    max_score = rule_score
                    matched_rules = [rule_type]

        if matched_rules:
            return max_score, matched_rules

        # 默认中等复杂度
        return 0.3, ["default_medium"]

    def _score_context(self, context: dict[str, Any]) -> float:
        """
        上下文复杂度评分

        Args:
            context: 上下文信息

        Returns:
            上下文评分 (0-0.2)
        """
        if not context:
            return 0.0

        score = 0.0

        # 上下文键数量
        context_size = len(context)
        if context_size > 10:
            score += 0.15
        elif context_size > 5:
            score += 0.1
        elif context_size > 2:
            score += 0.05

        # 特殊上下文标记
        if "patent_id" in context:
            score += 0.02
        if "claim_text" in context:
            score += 0.03
        if "comparison_documents" in context:
            score += 0.05

        return min(0.2, score)


class SmartModelRouter:
    """
    智能模型路由器

    基于任务复杂度自动选择最优模型，实现成本优化。
    """

    # ========================================
    # 模型分层定义
    # ========================================

    # 经济层 (低成本、快速)
    ECONOMY_MODELS: list[dict[str, Any]] = [
        {
            "model_id": "glm-4-flash",
            "cost_per_1k": 0.001,
            "quality_score": 0.75,
            "avg_latency_ms": 200,
        },
        {
            "model_id": "deepseek-chat",
            "cost_per_1k": 0.001,
            "quality_score": 0.80,
            "avg_latency_ms": 300,
        },
        {
            "model_id": "qwen2.5-7b",
            "cost_per_1k": 0.0,  # 本地模型
            "quality_score": 0.70,
            "avg_latency_ms": 500,
            "is_local": True,
        },
    ]

    # 平衡层 (性价比)
    BALANCED_MODELS: list[dict[str, Any]] = [
        {
            "model_id": "glm-4-plus",
            "cost_per_1k": 0.05,
            "quality_score": 0.90,
            "avg_latency_ms": 500,
        },
        {
            "model_id": "deepseek-reasoner",
            "cost_per_1k": 0.055,
            "quality_score": 0.92,
            "avg_latency_ms": 800,
            "supports_thinking": True,
        },
    ]

    # 高级层 (高质量)
    PREMIUM_MODELS: list[dict[str, Any]] = [
        {
            "model_id": "claude-3-5-sonnet",
            "cost_per_1k": 0.15,
            "quality_score": 0.95,
            "avg_latency_ms": 1000,
        },
        {
            "model_id": "glm-4-plus",
            "cost_per_1k": 0.05,
            "quality_score": 0.90,
            "avg_latency_ms": 500,
        },
    ]

    # 复杂度阈值
    ECONOMY_THRESHOLD = 0.3  # 低于此值使用经济模型
    BALANCED_THRESHOLD = 0.7  # 低于此值使用平衡模型

    def __init__(self, available_models: Optional[list[str]] = None):
        """
        初始化智能模型路由器

        Args:
            available_models: 可用模型列表 (None 表示全部可用)
        """
        self.complexity_analyzer = TaskComplexityAnalyzer()
        self.available_models = set(available_models) if available_models else None

        # 路由统计
        self.routing_history: list[RoutingDecision] = []
        self.total_cost_saved: float = 0.0

        logger.info("🚀 SmartModelRouter 初始化完成")

    async def route_request(
        self,
        request: LLMRequest,
        available_adapters: Optional[dict[str, Any]] = None,
    ) -> RoutingDecision:
        """
        智能路由请求到最适合的模型

        Args:
            request: LLM 请求
            available_adapters: 可用的模型适配器

        Returns:
            RoutingDecision 路由决策
        """
        # 1. 分析复杂度
        complexity = self.complexity_analyzer.analyze(request)

        logger.info(
            f"📊 任务复杂度: {complexity.total:.2f} "
            f"(长度:{complexity.length_score:.2f}, "
            f"关键词:{complexity.keyword_score:.2f}, "
            f"任务:{complexity.task_type_score:.2f}, "
            f"上下文:{complexity.context_score:.2f})"
        )

        # 2. 根据复杂度选择模型层
        if complexity.total < self.ECONOMY_THRESHOLD:
            layer, model, cost = self._select_economy_model(available_adapters)
            reason = f"简单任务 (复杂度 {complexity.total:.2f} < {self.ECONOMY_THRESHOLD})"
        elif complexity.total < self.BALANCED_THRESHOLD:
            layer, model, cost = self._select_balanced_model(complexity.total, available_adapters)
            reason = f"中等任务 ({self.ECONOMY_THRESHOLD} <= 复杂度 {complexity.total:.2f} < {self.BALANCED_THRESHOLD})"
        else:
            layer, model, cost = self._select_premium_model(available_adapters)
            reason = f"复杂任务 (复杂度 {complexity.total:.2f} >= {self.BALANCED_THRESHOLD})"

        # 3. 计算成本节省
        premium_cost = self.PREMIUM_MODELS[0]["cost_per_1k"]
        cost_saved = premium_cost - cost

        # 4. 创建路由决策
        decision = RoutingDecision(
            selected_layer=layer,
            selected_model=model,
            complexity_score=complexity.total,
            estimated_cost=cost,
            cost_saved=cost_saved,
            reason=reason,
        )

        # 5. 更新统计
        self.routing_history.append(decision)
        self.total_cost_saved += cost_saved

        logger.info(
            f"🎯 模型路由: {model} ({layer}层) "
            f"- 预估成本 {cost:.4f}元/1K tokens "
            f"(节省 {cost_saved:.4f}元)"
        )

        return decision

    def _select_economy_model(
        self,
        available_adapters: Optional[dict[str, Any]],
    ) -> Optional[Tuple[str, str]]:
        """
        选择经济模型

        Returns:
            (层名, 模型ID, 成本)
        """
        candidates = self._filter_available_models(self.ECONOMY_MODELS, available_adapters)

        if not candidates:
            logger.warning("⚠️ 无可用经济模型，回退到平衡模型")
            return self._select_balanced_model(0.25, available_adapters)

        # 优先选择本地模型（免费）
        local_models = [m for m in candidates if m.get("is_local")]
        if local_models:
            model = local_models[0]
            return "economy", model["model_id"], model["cost_per_1k"]

        # 否则选择成本最低的
        model = min(candidates, key=lambda m: m["cost_per_1k"])
        return "economy", model["model_id"], model["cost_per_1k"]

    def _select_balanced_model(
        self,
        complexity: float,
        available_adapters: Optional[dict[str, Any]],
    ) -> tuple[str, str, float]:
        """
        选择平衡模型

        Args:
            complexity: 复杂度分数

        Returns:
            (层名, 模型ID, 成本)
        """
        candidates = self._filter_available_models(self.BALANCED_MODELS, available_adapters)

        if not candidates:
            logger.warning("⚠️ 无可用平衡模型，回退到高级模型")
            return self._select_premium_model(available_adapters)

        # 根据复杂度微调选择
        if complexity > 0.5:
            # 偏向质量
            model = max(candidates, key=lambda m: m["quality_score"])
        else:
            # 偏向成本
            model = min(candidates, key=lambda m: m["cost_per_1k"])

        return "balanced", model["model_id"], model["cost_per_1k"]

    def _select_premium_model(
        self,
        available_adapters: Optional[dict[str, Any]],
    ) -> tuple[str, str, float]:
        """
        选择高级模型

        Returns:
            (层名, 模型ID, 成本)
        """
        candidates = self._filter_available_models(self.PREMIUM_MODELS, available_adapters)

        if not candidates:
            logger.warning("⚠️ 无可用高级模型，使用平衡模型")
            return self._select_balanced_model(0.75, available_adapters)

        # 选择质量最高的
        model = max(candidates, key=lambda m: m["quality_score"])
        return "premium", model["model_id"], model["cost_per_1k"]

    def _filter_available_models(
        self,
        model_list: List[Dict[str, Any]],
        available_adapters: Optional[Dict[str, Any]],
    ) -> Optional[List[Dict[str, Any]]]:
        """
        过滤出可用的模型

        Args:
            model_list: 模型列表
            available_adapters: 可用的适配器

        Returns:
            可用模型列表
        """
        if available_adapters is None:
            return model_list

        return [model for model in model_list if model["model_id"] in available_adapters]

    def get_statistics(self) -> dict[str, Any]:
        """
        获取路由统计信息

        Returns:
            统计信息字典
        """
        if not self.routing_history:
            return {
                "total_requests": 0,
                "total_cost_saved": 0.0,
                "layer_distribution": {},
            }

        # 层分布
        layer_counts: dict[str, int] = {}
        for decision in self.routing_history:
            layer_counts[decision.selected_layer] = layer_counts.get(decision.selected_layer, 0) + 1

        # 平均复杂度
        avg_complexity = sum(d.complexity_score for d in self.routing_history) / len(
            self.routing_history
        )

        return {
            "total_requests": len(self.routing_history),
            "total_cost_saved": round(self.total_cost_saved, 4),
            "avg_complexity": round(avg_complexity, 3),
            "layer_distribution": layer_counts,
            "recent_decisions": [
                {
                    "model": d.selected_model,
                    "layer": d.selected_layer,
                    "complexity": round(d.complexity_score, 2),
                    "cost_saved": round(d.cost_saved, 4),
                }
                for d in self.routing_history[-10:]
            ],
        }


# ========================================
# 全局智能路由器实例
# ========================================
_global_router: Optional[SmartModelRouter] = None


def get_smart_model_router() -> SmartModelRouter:
    """获取全局智能模型路由器"""
    global _global_router
    if _global_router is None:
        _global_router = SmartModelRouter()
    return _global_router


__all__ = [
    "TaskComplexityAnalyzer",
    "SmartModelRouter",
    "ComplexityScore",
    "RoutingDecision",
    "get_smart_model_router",
]

