#!/usr/bin/env python3
"""
证据整理器

整理诉讼证据，构建证据链，评估证据效力。
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EvidenceType(Enum):
    """证据类型"""
    DOCUMENT = "document"  # 书证
    MATERIAL = "material"  # 物证
    ELECTRONIC = "electronic"  # 电子证据
    WITNESS = "witness"  # 证人证言
    EXPERT_OPINION = "expert_opinion"  # 专家意见
    INSPECTION = "inspection"  # 勘验笔录


class EvidenceCategory(Enum):
    """证据分类"""
    PATENT_VALIDITY = "patent_validity"  # 专利有效性证据
    INFRINGEMENT = "infringement"  # 侵权证据
    DAMAGES = "damages"  # 损害赔偿证据
    PRIOR_ART = "prior_art"  # 现有技术证据
    CONTRACT = "contract"  # 合同证据
    OTHER = "other"  # 其他证据


class EvidenceReliability(Enum):
    """证据可靠性"""
    HIGH = "high"  # 高可靠性
    MEDIUM = "medium"  # 中等可靠性
    LOW = "low"  # 低可靠性


@dataclass
class Evidence:
    """证据项"""
    id: str
    name: str
    evidence_type: EvidenceType
    category: EvidenceCategory
    description: str
    source: str
    date: str | None = None
    reliability: EvidenceReliability = EvidenceReliability.MEDIUM
    relevance: float = 0.5  # 相关性 (0-1)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "evidence_type": self.evidence_type.value,
            "category": self.category.value,
            "description": self.description,
            "source": self.source,
            "date": self.date,
            "reliability": self.reliability.value,
            "relevance": self.relevance,
            "notes": self.notes
        }


@dataclass
class EvidenceChain:
    """证据链"""
    chain_id: str
    title: str
    description: str
    evidence_ids: list[str]  # 证据ID列表
    logical_flow: str  # 逻辑关系
    strength: float  # 证据链强度 (0-1)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "chain_id": self.chain_id,
            "title": self.title,
            "description": self.description,
            "evidence_ids": self.evidence_ids,
            "logical_flow": self.logical_flow,
            "strength": self.strength
        }


@dataclass
class EvidenceOrganizationResult:
    """证据整理结果"""
    patent_id: str
    evidences: list[Evidence]
    evidence_chains: list[EvidenceChain]
    category_summary: dict[str, list[str]  # 按分类汇总证据ID
    reliability_distribution: dict[str, int]  # 可靠性分布
    recommendations: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "patent_id": self.patent_id,
            "evidences": [e.to_dict() for e in self.evidences],
            "evidence_chains": [c.to_dict() for c in self.evidence_chains],
            "category_summary": self.category_summary,
            "reliability_distribution": self.reliability_distribution,
            "recommendations": self.recommendations,
            "metadata": self.metadata
        }


class EvidenceOrganizer:
    """证据整理器"""

    def __init__(self):
        """初始化整理器"""
        self.evidence_templates = self._load_evidence_templates()
        logger.info("✅ 证据整理器初始化成功")

    def _load_evidence_templates(self) -> dict[str, Any]:
        """加载证据模板"""
        return {
            "patent_validity": {
                "common_evidences": [
                    "专利证书",
                    "专利登记簿副本",
                    "专利授权公告文本",
                    "年费缴纳证明",
                    "专利检索报告"
                ]
            },
            "infringement": {
                "common_evidences": [
                    "侵权产品实物或照片",
                    "销售记录",
                    "宣传材料",
                    "产品说明书",
                    "公证购买记录"
                ]
            },
            "damages": {
                "common_evidences": [
                    "财务报表",
                    "销售合同",
                    "许可协议",
                    "损失计算说明",
                    "审计报告"
                ]
            },
            "prior_art": {
                "common_evidences": [
                    "对比文件全文",
                    "公开日证明",
                    "技术对比分析",
                    "专家意见书",
                    "检索报告"
                ]
            }
        }

    def organize_evidences(
        self,
        patent_id: str,
        litigation_type: str,
        raw_evidences: list[dict[str, Any],
        options: dict[str, Any] | None = None
    ) -> EvidenceOrganizationResult:
        """
        整理证据

        Args:
            patent_id: 专利号
            litigation_type: 诉讼类型
            raw_evidences: 原始证据列表
            options: 可选配置

        Returns:
            EvidenceOrganizationResult对象
        """
        logger.info(f"📁 开始整理证据: {patent_id}, 诉讼类型={litigation_type}")

        # 步骤1: 解析和规范化证据
        evidences = self._parse_evidences(raw_evidences, litigation_type)

        # 步骤2: 评估证据可靠性和相关性
        evidences = self._assess_evidences(evidences)

        # 步骤3: 构建证据链
        evidence_chains = self._build_evidence_chains(evidences, litigation_type)

        # 步骤4: 按分类汇总
        category_summary = self._summarize_by_category(evidences)

        # 步骤5: 统计可靠性分布
        reliability_distribution = self._analyze_reliability(evidences)

        # 步骤6: 生成建议
        recommendations = self._generate_recommendations(
            evidences,
            evidence_chains,
            litigation_type
        )

        return EvidenceOrganizationResult(
            patent_id=patent_id,
            evidences=evidences,
            evidence_chains=evidence_chains,
            category_summary=category_summary,
            reliability_distribution=reliability_distribution,
            recommendations=recommendations,
            metadata={
                "organization_date": datetime.now().strftime("%Y-%m-%d"),
                "total_evidences": len(evidences),
                "total_chains": len(evidence_chains),
                "litigation_type": litigation_type
            }
        )

    def _parse_evidences(
        self,
        raw_evidences: list[dict[str, Any],
        litigation_type: str
    ) -> list[Evidence]:
        """解析和规范化证据"""
        evidences = []

        for idx, raw in enumerate(raw_evidences):
            # 确定证据类型
            evidence_type = self._determine_evidence_type(raw)
            category = self._determine_category(raw, litigation_type)

            evidence = Evidence(
                id=f"EVI_{idx+1:03d}",
                name=raw.get("name", f"证据{idx+1}"),
                evidence_type=evidence_type,
                category=category,
                description=raw.get("description", ""),
                source=raw.get("source", ""),
                date=raw.get("date"),
                reliability=self._determine_reliability(raw),
                relevance=raw.get("relevance", 0.5),
                notes=raw.get("notes", "")
            )
            evidences.append(evidence)

        return evidences

    def _determine_evidence_type(self, raw_evidence: dict[str, Any]) -> EvidenceType:
        """确定证据类型"""
        type_hint = raw_evidence.get("evidence_type", "")
        if isinstance(type_hint, str):
            type_hint = type_hint.lower()
            if "document" in type_hint or "书证" in type_hint:
                return EvidenceType.DOCUMENT
            elif "material" in type_hint or "物证" in type_hint:
                return EvidenceType.MATERIAL
            elif "electronic" in type_hint or "电子" in type_hint:
                return EvidenceType.ELECTRONIC
            elif "witness" in type_hint or "证人" in type_hint:
                return EvidenceType.WITNESS
            elif "expert" in type_hint or "专家" in type_hint:
                return EvidenceType.EXPERT_OPINION
            elif "inspection" in type_hint or "勘验" in type_hint:
                return EvidenceType.INSPECTION

        # 默认为书证
        return EvidenceType.DOCUMENT

    def _determine_category(
        self,
        raw_evidence: dict[str, Any],
        litigation_type: str
    ) -> EvidenceCategory:
        """确定证据分类"""
        category_hint = raw_evidence.get("category", "")

        # 如果有明确分类
        if isinstance(category_hint, str):
            for cat in EvidenceCategory:
                if cat.value in category_hint.lower():
                    return cat

        # 根据诉讼类型和描述推断
        description = raw_evidence.get("description", "").lower()
        name = raw_evidence.get("name", "").lower()

        if "专利" in name or "专利" in description:
            return EvidenceCategory.PATENT_VALIDITY
        elif "侵权" in name or "产品" in description:
            return EvidenceCategory.INFRINGEMENT
        elif "损失" in name or "赔偿" in description or "合同" in name:
            return EvidenceCategory.DAMAGES
        elif "对比" in name or "现有技术" in description:
            return EvidenceCategory.PRIOR_ART

        return EvidenceCategory.OTHER

    def _determine_reliability(self, raw_evidence: dict[str, Any]) -> EvidenceReliability:
        """确定证据可靠性"""
        reliability_hint = raw_evidence.get("reliability", "")

        if isinstance(reliability_hint, str):
            if "high" in reliability_hint.lower() or "高" in reliability_hint:
                return EvidenceReliability.HIGH
            elif "low" in reliability_hint.lower() or "低" in reliability_hint:
                return EvidenceReliability.LOW

        # 根据来源推断
        source = raw_evidence.get("source", "").lower()
        if "公证" in source or "官方" in source:
            return EvidenceReliability.HIGH
        elif "单方" in source or "自制" in source:
            return EvidenceReliability.LOW

        return EvidenceReliability.MEDIUM

    def _assess_evidences(self, evidences: list[Evidence]) -> list[Evidence]:
        """评估证据可靠性和相关性"""
        # 这里可以添加更复杂的评估逻辑
        # 目前保持简单，实际应用中可能需要AI辅助评估
        return evidences

    def _build_evidence_chains(
        self,
        evidences: list[Evidence],
        litigation_type: str
    ) -> list[EvidenceChain]:
        """构建证据链"""
        chains = []

        # 按分类分组证据
        category_groups: dict[EvidenceCategory, list[Evidence] = {}
        for evi in evidences:
            if evi.category not in category_groups:
                category_groups[evi.category] = []
            category_groups[evi.category].append(evi)

        # 为每个分类构建证据链
        for category, evi_list in category_groups.items():
            if len(evi_list) >= 2:  # 至少2个证据才构成链
                chain_id = f"CHAIN_{category.value.upper()}_001"
                title = f"{category.value}证据链"

                # 计算证据链强度
                avg_relevance = sum(e.relevance for e in evi_list) / len(evi_list)
                high_reliability_count = sum(
                    1 for e in evi_list
                    if e.reliability == EvidenceReliability.HIGH
                )
                strength = (avg_relevance + high_reliability_count * 0.1) / len(evi_list)
                strength = min(1.0, strength)

                chain = EvidenceChain(
                    chain_id=chain_id,
                    title=title,
                    description=f"{len(evi_list)}个{category.value}相关证据",
                    evidence_ids=[e.id for e in evi_list],
                    logical_flow=" -> ".join([e.name for e in evi_list[:3]),
                    strength=strength
                )
                chains.append(chain)

        return chains

    def _summarize_by_category(self, evidences: list[Evidence]) -> dict[str, list[str]:
        """按分类汇总证据"""
        summary: dict[str, list[str] = {}

        for evi in evidences:
            category = evi.category.value
            if category not in summary:
                summary[category] = []
            summary[category].append(evi.id)

        return summary

    def _analyze_reliability(self, evidences: list[Evidence]) -> dict[str, int]:
        """分析可靠性分布"""
        distribution = {
            "high": 0,
            "medium": 0,
            "low": 0
        }

        for evi in evidences:
            distribution[evi.reliability.value] += 1

        return distribution

    def _generate_recommendations(
        self,
        evidences: list[Evidence],
        chains: list[EvidenceChain],
        litigation_type: str
    ) -> list[str]:
        """生成建议"""
        recommendations = []

        # 评估证据充分性
        if len(evidences) < 5:
            recommendations.append("建议补充更多证据以增强案件说服力")

        # 评估高可靠性证据比例
        high_reliability_ratio = sum(
            1 for e in evidences
            if e.reliability == EvidenceReliability.HIGH
        ) / len(evidences) if evidences else 0

        if high_reliability_ratio < 0.3:
            recommendations.append("建议提高高可靠性证据比例（如公证、官方文件）")

        # 评估证据链
        if len(chains) == 0:
            recommendations.append("建议构建完整的证据链以增强逻辑性")
        else:
            weak_chains = [c for c in chains if c.strength < 0.5]
            if weak_chains:
                recommendations.append(f"有{len(weak_chains)}条证据链强度较弱，建议补充相关证据")

        # 根据诉讼类型给出建议
        if litigation_type == "infringement":
            infringement_evidences = [
                e for e in evidences
                if e.category == EvidenceCategory.INFRINGEMENT
            ]
            if len(infringement_evidences) < 3:
                recommendations.append("侵权诉讼建议至少准备3项侵权证据")

        return recommendations


async def test_evidence_organizer():
    """测试证据整理器"""
    organizer = EvidenceOrganizer()

    print("\n" + "="*80)
    print("📁 证据整理器测试")
    print("="*80)

    # 测试数据
    raw_evidences = [
        {
            "name": "专利证书",
            "description": "发明专利证书原件",
            "source": "国家知识产权局",
            "evidence_type": "document",
            "category": "patent_validity",
            "reliability": "high",
            "relevance": 0.9
        },
        {
            "name": "侵权产品实物",
            "description": "公证购买的侵权产品",
            "source": "公证处",
            "evidence_type": "material",
            "category": "infringement",
            "reliability": "high",
            "relevance": 0.95
        },
        {
            "name": "销售合同",
            "description": "被诉侵权产品的销售合同",
            "source": "企业内部",
            "evidence_type": "document",
            "category": "damages",
            "reliability": "medium",
            "relevance": 0.7
        },
        {
            "name": "对比文件D1",
            "description": "现有技术对比文件",
            "source": "专利数据库",
            "evidence_type": "document",
            "category": "prior_art",
            "reliability": "high",
            "relevance": 0.85
        },
        {
            "name": "专家意见书",
            "description": "技术专家出具的意见书",
            "source": "第三方专家",
            "evidence_type": "expert_opinion",
            "category": "infringement",
            "reliability": "medium",
            "relevance": 0.75
        }
    ]

    # 整理证据
    result = organizer.organize_evidences(
        patent_id="CN123456789A",
        litigation_type="infringement",
        raw_evidences=raw_evidences
    )

    print("\n📊 证据整理结果:")
    print(f"   专利号: {result.patent_id}")
    print(f"   证据总数: {result.metadata['total_evidences']}")
    print(f"   证据链数: {result.metadata['total_chains']}")

    print("\n   证据分类汇总:")
    for category, evi_ids in result.category_summary.items():
        print(f"      {category}: {len(evi_ids)}项")

    print("\n   可靠性分布:")
    for reliability, count in result.reliability_distribution.items():
        print(f"      {reliability}: {count}项")

    print("\n   证据链:")
    for chain in result.evidence_chains[:3]:
        print(f"      - {chain.title} (强度: {chain.strength:.2f})")
        print(f"        {chain.logical_flow[:50]}...")

    print("\n   建议:")
    for rec in result.recommendations[:3]:
        print(f"      - {rec}")

    print("\n" + "="*80)
    print("✅ 测试完成")
    print("="*80)


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_evidence_organizer())
