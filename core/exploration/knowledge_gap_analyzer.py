#!/usr/bin/env python3
"""
知识图谱空白分析器
Knowledge Graph Gap Analyzer

分析知识图谱的完整性,识别需要补充的知识点

作者: 小诺·双鱼座
版本: v1.0.0
创建时间: 2025-01-05
"""

import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class GapType(Enum):
    """空白类型"""

    MISSING_ENTITY = "missing_entity"  # 缺失实体
    MISSING_RELATION = "missing_relation"  # 缺失关系
    INCOMPLETE_ATTRIBUTE = "incomplete_attribute"  # 不完整属性
    LOW_CONFIDENCE = "low_confidence"  # 低置信度
    OUTDATED_INFO = "outdated_info"  # 过时信息


@dataclass
class GraphAnalysisResult:
    """图谱分析结果"""

    domain: str
    total_entities: int = 0
    covered_entities: int = 0
    total_relations: int = 0
    covered_relations: int = 0
    coverage_rate: float = 0.0
    gaps: list[dict[str, Any]] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


class KnowledgeGapAnalyzer:
    """知识图谱空白分析器"""

    def __init__(self):
        """初始化分析器"""
        self.name = "知识图谱空白分析器"
        self.version = "1.0.0"

        # 日志配置
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(self.name)

        # 分析缓存
        self.analysis_cache: dict[str, GraphAnalysisResult] = {}

        print(f"📊 {self.name} v{self.version} 初始化完成")

    async def analyze_domain_gaps(
        self, domain: str, knowledge_graph: dict[str, Any] | None = None
    ) -> GraphAnalysisResult:
        """
        分析领域知识空白

        Args:
            domain: 领域名称
            knowledge_graph: 知识图谱数据(可选)

        Returns:
            GraphAnalysisResult: 分析结果
        """
        self.logger.info(f"📊 分析领域知识空白: {domain}")

        try:
            # 1. 获取或使用提供的知识图谱
            kg = knowledge_graph or await self._get_knowledge_graph(domain)

            # 2. 分析实体覆盖度
            entity_analysis = await self._analyze_entity_coverage(kg)

            # 3. 分析关系覆盖度
            relation_analysis = await self._analyze_relation_coverage(kg)

            # 4. 识别空白点
            gaps = await self._identify_gaps(kg, entity_analysis, relation_analysis)

            # 5. 生成推荐
            recommendations = await self._generate_recommendations(gaps)

            # 6. 构建结果
            result = GraphAnalysisResult(
                domain=domain,
                total_entities=entity_analysis["total"],
                covered_entities=entity_analysis["covered"],
                total_relations=relation_analysis["total"],
                covered_relations=relation_analysis["covered"],
                coverage_rate=self._calculate_coverage_rate(entity_analysis, relation_analysis),
                gaps=gaps,
                recommendations=recommendations,
            )

            # 缓存结果
            self.analysis_cache[domain] = result

            self.logger.info(
                f"✅ 分析完成: 覆盖率 {result.coverage_rate:.1%}, " f"发现 {len(gaps)} 个空白点"
            )

            return result

        except Exception as e:
            self.logger.error(f"❌ 分析失败: {e}")
            return GraphAnalysisResult(domain=domain)

    async def _get_knowledge_graph(self, domain: str) -> dict[str, Any]:
        """获取知识图谱"""
        # 模拟实现 - 实际中会从图数据库获取
        return {
            "entities": [
                {"id": "e1", "type": "技术", "name": "人工智能"},
                {"id": "e2", "type": "领域", "name": "医疗"},
                {"id": "e3", "type": "应用", "name": "诊断"},
            ],
            "relations": [
                {"source": "e1", "target": "e2", "type": "应用于"},
                {"source": "e1", "target": "e3", "type": "支持"},
            ],
        }

    async def _analyze_entity_coverage(self, kg: dict[str, Any]) -> dict[str, Any]:
        """分析实体覆盖度"""
        entities = kg.get("entities", [])

        # 统计实体类型
        entity_types = {}
        for entity in entities:
            etype = entity.get("type", "unknown")
            entity_types[etype] = entity_types.get(etype, 0) + 1

        return {"total": len(entities), "covered": len(entities), "by_type": entity_types}

    async def _analyze_relation_coverage(self, kg: dict[str, Any]) -> dict[str, Any]:
        """分析关系覆盖度"""
        relations = kg.get("relations", [])

        # 统计关系类型
        relation_types = {}
        for relation in relations:
            rtype = relation.get("type", "unknown")
            relation_types[rtype] = relation_types.get(rtype, 0) + 1

        return {"total": len(relations), "covered": len(relations), "by_type": relation_types}

    async def _identify_gaps(
        self, kg: dict[str, Any], entity_analysis: dict[str, Any], relation_analysis: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """识别空白点"""
        gaps = []

        # 1. 识别缺失的实体关系
        entities = kg.get("entities", [])
        for i, entity1 in enumerate(entities):
            for entity2 in entities[i + 1 :]:
                # 检查是否存在关系
                has_relation = await self._check_relation_exists(kg, entity1["id"], entity2["id"])

                if not has_relation:
                    gaps.append(
                        {
                            "type": GapType.MISSING_RELATION.value,
                            "entity1": entity1,
                            "entity2": entity2,
                            "importance": await self._assess_gap_importance(entity1, entity2),
                            "suggested_relation": await self._suggest_relation_type(
                                entity1, entity2
                            ),
                        }
                    )

        # 2. 识别属性不完整的实体
        for entity in entities:
            completeness = await self._check_entity_completeness(entity)
            if completeness < 0.7:
                gaps.append(
                    {
                        "type": GapType.INCOMPLETE_ATTRIBUTE.value,
                        "entity": entity,
                        "completeness": completeness,
                        "missing_attributes": await self._get_missing_attributes(entity),
                    }
                )

        # 按重要性排序
        gaps.sort(key=lambda x: x.get("importance", 0.5), reverse=True)

        return gaps[:20]  # 返回前20个最重要的空白

    async def _check_relation_exists(
        self, kg: dict[str, Any], entity1_id: str, entity2_id: str
    ) -> bool:
        """检查关系是否存在"""
        relations = kg.get("relations", [])
        for rel in relations:
            if (rel.get("source") == entity1_id and rel.get("target") == entity2_id) or (
                rel.get("source") == entity2_id and rel.get("target") == entity1_id
            ):
                return True
        return False

    async def _assess_gap_importance(
        self, entity1: dict[str, Any], entity2: dict[str, Any]
    ) -> float:
        """评估空白重要性"""
        # 简单实现:基于实体类型
        type_importance = {"技术": 0.9, "领域": 0.8, "应用": 0.7, "unknown": 0.5}

        imp1 = type_importance.get(entity1.get("type", "unknown"), 0.5)
        imp2 = type_importance.get(entity2.get("type", "unknown"), 0.5)

        return (imp1 + imp2) / 2

    async def _suggest_relation_type(self, entity1: dict[str, Any], entity2: dict[str, Any]) -> str:
        """建议关系类型"""
        type1 = entity1.get("type", "")
        type2 = entity2.get("type", "")

        # 简单规则
        if type1 == "技术" and type2 == "领域":
            return "应用于"
        elif type1 == "技术" and type2 == "应用":
            return "支持"
        else:
            return "相关"

    async def _check_entity_completeness(self, entity: dict[str, Any]) -> float:
        """检查实体完整性"""
        required_fields = ["name", "type", "description"]
        present_fields = sum(1 for field in required_fields if field in entity)

        # 额外字段加分
        extra_fields = ["aliases", "attributes", "metadata"]
        extra_present = sum(1 for field in extra_fields if field in entity)

        return (present_fields + extra_present * 0.1) / (
            len(required_fields) + len(extra_fields) * 0.1
        )

    async def _get_missing_attributes(self, entity: dict[str, Any]) -> list[str]:
        """获取缺失属性"""
        all_possible_attributes = [
            "description",
            "aliases",
            "attributes",
            "created_at",
            "updated_at",
            "source",
            "confidence",
            "metadata",
        ]

        return [attr for attr in all_possible_attributes if attr not in entity]

    async def _generate_recommendations(self, gaps: list[dict[str, Any]]) -> list[str]:
        """生成推荐"""
        recommendations = []

        # 统计空白类型
        gap_types = {}
        for gap in gaps:
            gap_type = gap.get("type", "unknown")
            gap_types[gap_type] = gap_types.get(gap_type, 0) + 1

        # 基于空白类型生成推荐
        if GapType.MISSING_RELATION.value in gap_types:
            count = gap_types[GapType.MISSING_RELATION.value]
            recommendations.append(f"发现 {count} 个缺失的实体关系,建议进行关系补全")

        if GapType.INCOMPLETE_ATTRIBUTE.value in gap_types:
            count = gap_types[GapType.INCOMPLETE_ATTRIBUTE.value]
            recommendations.append(f"发现 {count} 个属性不完整的实体,建议进行属性完善")

        # 添加优先级建议
        if gaps:
            top_gap = gaps[0]
            recommendations.append(f"优先处理重要性最高的空白: {top_gap.get('type', 'unknown')}")

        return recommendations

    def _calculate_coverage_rate(
        self, entity_analysis: dict[str, Any], relation_analysis: dict[str, Any]
    ) -> float:
        """计算覆盖率"""
        entity_rate = (
            entity_analysis["covered"] / entity_analysis["total"]
            if entity_analysis["total"] > 0
            else 0
        )
        relation_rate = (
            relation_analysis["covered"] / relation_analysis["total"]
            if relation_analysis["total"] > 0
            else 0
        )

        # 加权平均:实体60%,关系40%
        return entity_rate * 0.6 + relation_rate * 0.4

    async def batch_analyze_domains(self, domains: list[str]) -> dict[str, GraphAnalysisResult]:
        """批量分析多个领域"""
        results = {}
        for domain in domains:
            result = await self.analyze_domain_gaps(domain)
            results[domain] = result
        return results

    def get_analysis_summary(self) -> dict[str, Any]:
        """获取分析摘要"""
        return {
            "cached_domains": list(self.analysis_cache.keys()),
            "total_analyses": len(self.analysis_cache),
            "average_coverage": (
                sum(r.coverage_rate for r in self.analysis_cache.values())
                / len(self.analysis_cache)
                if self.analysis_cache
                else 0.0
            ),
        }


# ==================== 全局实例 ====================

_gap_analyzer: KnowledgeGapAnalyzer | None = None


def get_knowledge_gap_analyzer() -> KnowledgeGapAnalyzer:
    """获取分析器单例"""
    global _gap_analyzer
    if _gap_analyzer is None:
        _gap_analyzer = KnowledgeGapAnalyzer()
    return _gap_analyzer


# ==================== 导出 ====================

__all__ = ["GapType", "GraphAnalysisResult", "KnowledgeGapAnalyzer", "get_knowledge_gap_analyzer"]
