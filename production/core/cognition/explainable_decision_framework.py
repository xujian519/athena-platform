# pyright: ignore
"""
可解释决策框架
实现AI决策过程的可解释性和透明度
"""
from __future__ import annotations
import hashlib
import json
import logging
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class ExplanationType(Enum):
    """解释类型"""

    FEATURE_IMPORTANCE = "feature_importance"
    DECISION_PATH = "decision_path"
    COUNTERFACTUAL = "counterfactual"
    SIMILAR_CASES = "similar_cases"
    RULE_BASED = "rule_based"
    CONFIDENCE_BREAKDOWN = "confidence_breakdown"


@dataclass
class DecisionNode:
    """决策节点"""

    node_id: str
    node_type: str
    description: str
    condition: str | None = None
    value: Any = None
    confidence: float = 0.0
    children: list["DecisionNode"] = field(default_factory=list)
    parent: Optional["DecisionNode"] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Explanation:
    """解释结果"""

    explanation_id: str
    decision_id: str
    explanation_type: ExplanationType
    title: str
    summary: str
    details: dict[str, Any]
    evidence: list[dict[str, Any]]
    confidence_score: float
    created_at: datetime = field(default_factory=datetime.now)
    visualization_data: dict[str, Any] | None = None


class ExplainableDecisionEngine:
    """可解释决策引擎"""

    def __init__(self):
        self.decision_history = []
        self.explanation_cache = {}
        self.feature_extractors = {}
        self.explanation_generators = {}

    def register_feature_extractor(self, name: str, extractor: Callable) -> Any:  # type: ignore
        """注册特征提取器"""
        self.feature_extractors[name] = extractor
        logger.info(f"注册特征提取器: {name}")

    def register_explanation_generator(
        self, explanation_type: ExplanationType, generator: Callable  # type: ignore
    ):
        """注册解释生成器"""
        self.explanation_generators[explanation_type] = generator
        logger.info(f"注册解释生成器: {explanation_type.value}")

    async def explain_decision(
        self, decision_data: dict[str, Any], explanation_types: list[ExplanationType] | None = None
    ) -> list[Explanation]:
        """解释决策过程"""
        if explanation_types is None:
            explanation_types = [
                ExplanationType.FEATURE_IMPORTANCE,
                ExplanationType.DECISION_PATH,
                ExplanationType.CONFIDENCE_BREAKDOWN,
            ]

        decision_id = self._generate_decision_id(decision_data)
        explanations = []

        for exp_type in explanation_types:
            try:
                if exp_type in self.explanation_generators:
                    explanation = await self.explanation_generators[exp_type](
                        decision_data, decision_id
                    )
                    explanations.append(explanation)
                else:
                    # 使用默认解释生成器
                    explanation = await self._generate_default_explanation(
                        decision_data, decision_id, exp_type
                    )
                    explanations.append(explanation)
            except Exception as e:
                logger.error(f"生成解释失败 {exp_type.value}: {e}")
                # 生成回退解释
                fallback = self._create_fallback_explanation(decision_id, exp_type)
                explanations.append(fallback)

        # 存储决策
        self.decision_history.append(
            {
                "decision_id": decision_id,
                "data": decision_data,
                "explanations": [asdict(exp) for exp in explanations],
                "timestamp": datetime.now().isoformat(),
            }
        )

        return explanations

    def _generate_decision_id(self, decision_data: dict[str, Any]) -> str:
        """生成决策ID"""
        content = json.dumps(decision_data, sort_keys=True)
        return hashlib.md5(content.encode(), usedforsecurity=False).hexdigest()

    async def _generate_default_explanation(
        self, decision_data: dict[str, Any], decision_id: str, explanation_type: ExplanationType
    ) -> Explanation:
        """生成默认解释"""
        if explanation_type == ExplanationType.FEATURE_IMPORTANCE:
            return await self._generate_feature_importance_explanation(decision_data, decision_id)
        elif explanation_type == ExplanationType.DECISION_PATH:
            return await self._generate_decision_path_explanation(decision_data, decision_id)
        elif explanation_type == ExplanationType.CONFIDENCE_BREAKDOWN:
            return await self._generate_confidence_breakdown_explanation(decision_data, decision_id)
        elif explanation_type == ExplanationType.SIMILAR_CASES:
            return await self._generate_similar_cases_explanation(decision_data, decision_id)
        else:
            return Explanation(
                explanation_id=f"{decision_id}_{explanation_type.value}",
                decision_id=decision_id,
                explanation_type=explanation_type,
                title=f"{explanation_type.value} 解释",
                summary="默认解释",
                details={},
                evidence=[],
                confidence_score=0.5,
            )

    async def _generate_feature_importance_explanation(
        self, decision_data: dict[str, Any], decision_id: str
    ) -> Explanation:
        """生成特征重要性解释"""
        try:
            # 提取特征
            features = await self._extract_features(decision_data)

            # 计算重要性
            importance_scores = {}
            for feature_name, feature_value in features.items():
                importance = await self._calculate_feature_importance(
                    feature_name, feature_value, decision_data
                )
                importance_scores[feature_name] = importance

            # 排序
            sorted_features = sorted(importance_scores.items(), key=lambda x: x[1], reverse=True)  # type: ignore

            # 创建可视化数据
            visualization_data = {
                "chart_type": "bar",
                "features": [item[0] for item in sorted_features],
                "importance": [item[1] for item in sorted_features],
            }

            # 生成证据
            evidence = []
            for feature, importance in sorted_features[:10]:  # Top 10
                evidence.append(
                    {
                        "feature": feature,
                        "importance": importance,
                        "description": f"特征 '{feature}' 对决策的重要性为 {importance:.3f}",
                    }
                )

            return Explanation(
                explanation_id=f"{decision_id}_feature_importance",
                decision_id=decision_id,
                explanation_type=ExplanationType.FEATURE_IMPORTANCE,
                title="特征重要性分析",
                summary=f"共有 {len(features)} 个特征参与决策",
                details={
                    "total_features": len(features),
                    "top_features": sorted_features[:5],
                    "importance_distribution": importance_scores,
                },
                evidence=evidence,
                confidence_score=0.85,
                visualization_data=visualization_data,
            )

        except Exception:
            return self._create_fallback_explanation(
                decision_id, ExplanationType.FEATURE_IMPORTANCE
            )

    async def _generate_decision_path_explanation(
        self, decision_data: dict[str, Any], decision_id: str
    ) -> Explanation:
        """生成决策路径解释"""
        try:
            # 构建决策树
            decision_tree = await self._build_decision_tree(decision_data)

            # 提取路径
            path_nodes = self._extract_decision_path(decision_tree)

            # 生成路径描述
            self._describe_decision_path(path_nodes)

            return Explanation(
                explanation_id=f"{decision_id}_decision_path",
                decision_id=decision_id,
                explanation_type=ExplanationType.DECISION_PATH,
                title="决策路径分析",
                summary=f"决策过程包含 {len(path_nodes)} 个关键节点",
                details={
                    "tree_depth": self._calculate_tree_depth(decision_tree),
                    "path_nodes": [asdict(node) for node in path_nodes],
                    "total_nodes": self._count_nodes(decision_tree),
                },
                evidence=[
                    {
                        "step": i + 1,
                        "node": node.node_type,
                        "description": node.description,
                        "confidence": node.confidence,
                    }
                    for i, node in enumerate(path_nodes)
                ],
                confidence_score=0.9,
            )

        except Exception:
            return self._create_fallback_explanation(decision_id, ExplanationType.DECISION_PATH)

    async def _generate_confidence_breakdown_explanation(
        self, decision_data: dict[str, Any], decision_id: str
    ) -> Explanation:
        """生成置信度分解解释"""
        try:
            # 分解置信度来源
            confidence_sources = await self._analyze_confidence_sources(decision_data)

            return Explanation(
                explanation_id=f"{decision_id}_confidence",
                decision_id=decision_id,
                explanation_type=ExplanationType.CONFIDENCE_BREAKDOWN,
                title="置信度分解分析",
                summary=f"决策置信度由 {len(confidence_sources)} 个因素组成",
                details={
                    "overall_confidence": confidence_sources.get("overall", 0.0),
                    "sources": confidence_sources,
                },
                evidence=[
                    {
                        "source": source,
                        "contribution": contribution,
                        "description": f"{source} 贡献了 {contribution:.3f} 的置信度",
                    }
                    for source, contribution in confidence_sources.items()
                    if source != "overall"
                ],
                confidence_score=confidence_sources.get("overall", 0.0),
            )

        except Exception:
            return self._create_fallback_explanation(
                decision_id, ExplanationType.CONFIDENCE_BREAKDOWN
            )

    async def _generate_similar_cases_explanation(
        self, decision_data: dict[str, Any], decision_id: str
    ) -> Explanation:
        """生成相似案例解释"""
        try:
            # 查找相似案例
            similar_cases = await self._find_similar_cases(decision_data)

            return Explanation(
                explanation_id=f"{decision_id}_similar_cases",
                decision_id=decision_id,
                explanation_type=ExplanationType.SIMILAR_CASES,
                title="相似案例参考",
                summary=f"找到 {len(similar_cases)} 个相似的历史决策",
                details={"similarity_threshold": 0.8, "search_criteria": "feature_similarity"},
                evidence=[
                    {
                        "case_id": case["case_id"],
                        "similarity": case["similarity"],
                        "outcome": case["outcome"],
                        "description": f"相似度 {case['similarity']:.3f} 的案例,结果是 {case['outcome']}",
                    }
                    for case in similar_cases[:5]
                ],
                confidence_score=0.75,
            )

        except Exception:
            return self._create_fallback_explanation(decision_id, ExplanationType.SIMILAR_CASES)

    def _create_fallback_explanation(
        self, decision_id: str, explanation_type: ExplanationType
    ) -> Explanation:
        """创建回退解释"""
        return Explanation(
            explanation_id=f"{decision_id}_{explanation_type.value}_fallback",
            decision_id=decision_id,
            explanation_type=explanation_type,
            title=f"{explanation_type.value} 解释",
            summary="解释生成失败,使用默认解释",
            details={},
            evidence=[],
            confidence_score=0.3,
        )

    async def _extract_features(self, decision_data: dict[str, Any]) -> dict[str, Any]:
        """提取特征"""
        features = {}

        # 基础特征
        features.update(
            {
                "task_type": decision_data.get("task_type", ""),
                "priority": decision_data.get("priority", 1),
                "complexity": decision_data.get("complexity", 0.5),
                "timestamp": decision_data.get("timestamp", ""),
            }
        )

        # 使用注册的特征提取器
        for _name, extractor in self.feature_extractors.items():
            try:
                extracted_features = await extractor(decision_data)
                features.update(extracted_features)
            except Exception as e:
                # 决策解释失败，记录错误
                logger.error(f'决策解释失败: {e}', exc_info=True)

        return features

    async def _calculate_feature_importance(
        self, feature_name: str, feature_value: Any, decision_data: dict[str, Any]
    ) -> float:
        """计算特征重要性"""
        # 基础重要性计算
        base_importance = 0.1

        # 根据特征类型调整
        if feature_name == "priority":
            return min(feature_value / 5.0, 1.0)  # 优先级归一化
        elif feature_name == "complexity":
            return min(feature_value, 1.0)
        elif feature_name in ["confidence", "reliability"]:
            return feature_value if isinstance(feature_value, (int, float)) else 0.5

        # 如果是数值型特征,使用归一化值
        if isinstance(feature_value, (int, float)) and feature_value != 0:
            return min(abs(feature_value) / 10.0, 1.0)

        return base_importance

    async def _build_decision_tree(self, decision_data: dict[str, Any]) -> DecisionNode:
        """构建决策树"""
        root = DecisionNode(
            node_id="root", node_type="root", description="决策根节点", confidence=0.0
        )

        # 根据决策数据构建树结构
        if "reasoning_steps" in decision_data:
            for step in decision_data.get("reasoning_steps"):  # type: ignore
                node = DecisionNode(
                    node_id=step.get("step_id", ""),
                    node_type=step.get("type", "processing"),
                    description=step.get("description", ""),
                    condition=step.get("condition"),
                    value=step.get("value"),
                    confidence=step.get("confidence", 0.0),
                )
                root.children.append(node)

        return root

    def _extract_decision_path(self, tree: DecisionNode) -> list[DecisionNode]:
        """提取决策路径"""
        path = []
        self._traverse_tree(tree, path, max_depth=10)
        return path

    def _traverse_tree(self, node: DecisionNode, path: list[DecisionNode], max_depth: int) -> Any:
        """遍历决策树"""
        path.append(node)

        if len(path) >= max_depth:
            return

        for child in node.children:
            self._traverse_tree(child, path, max_depth)

    def _describe_decision_path(self, nodes: list[DecisionNode]) -> str:
        """描述决策路径"""
        descriptions = [node.description for node in nodes]
        return " -> ".join(descriptions)

    def _calculate_tree_depth(self, tree: DecisionNode) -> int:
        """计算树的深度"""
        if not tree.children:
            return 1
        return 1 + max(self._calculate_tree_depth(child) for child in tree.children)

    def _count_nodes(self, tree: DecisionNode) -> int:
        """计算节点总数"""
        return 1 + sum(self._count_nodes(child) for child in tree.children)

    async def _analyze_confidence_sources(self, data: dict[str, Any]) -> dict[str, float]:
        """分析置信度来源"""
        sources = {}

        # 数据质量置信度
        if "data_quality" in data:
            sources["data_quality"] = data.get("data_quality")

        # 模型置信度
        if "model_confidence" in data:
            sources["model_confidence"] = data.get("model_confidence")

        # 特征覆盖度
        if "feature_coverage" in data:
            sources["feature_coverage"] = data.get("feature_coverage")

        # 历史一致性
        if "historical_consistency" in data:
            sources["historical_consistency"] = data.get("historical_consistency")

        # 计算总体置信度
        if sources:
            overall = np.mean(list(sources.values()))
            sources["overall"] = overall
        else:
            sources["overall"] = 0.5

        return sources

    async def _find_similar_cases(self, decision_data: dict[str, Any]) -> list[dict[str, Any]]:
        """查找相似案例"""
        # 这里应该从历史决策中查找相似案例
        # 简化实现,返回模拟数据
        return [
            {
                "case_id": f"case_{i}",
                "similarity": 0.9 - i * 0.05,
                "outcome": "positive" if i % 2 == 0 else "negative",
                "timestamp": "2025-01-01",
            }
            for i in range(5)
        ]

    def get_decision_history(self) -> list[dict[str, Any]]:
        """获取决策历史"""
        return self.decision_history

    def get_explanation_cache_stats(self) -> dict[str, Any]:
        """获取解释缓存统计"""
        return {
            "total_explanations": len(self.explanation_cache),
            "cache_size": len(self.explanation_cache),
            "cached_types": list(self.explanation_cache.keys()),
        }


# 全局可解释决策引擎实例
explainable_decision_engine = ExplainableDecisionEngine()


# 便捷函数
async def explain_decision_with_defaults(decision_data: dict[str, Any]) -> list[Explanation]:
    """使用默认配置解释决策"""
    return await explainable_decision_engine.explain_decision(decision_data)


def register_explanation_generator(explanation_type: ExplanationType, generator: Callable):  # type: ignore
    """注册解释生成器"""
    explainable_decision_engine.register_explanation_generator(explanation_type, generator)
