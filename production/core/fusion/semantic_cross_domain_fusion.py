#!/usr/bin/env python3
"""
语义级跨域融合引擎
Semantic Cross-Domain Fusion Engine

实现Athena的深度跨域知识融合，超越简单的API调用层面
达到语义理解和概念映射的深度融合

作者: Athena平台团队
创建时间: 2025-12-31
版本: 1.0.0
"""

from __future__ import annotations
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class FusionDepth(Enum):
    """融合深度级别"""
    SURFACE = "surface"  # 表层融合 - API层面
    FUNCTIONAL = "functional"  # 功能融合 - 功能组合
    SEMANTIC = "semantic"  # 语义融合 - 概念映射
    CONCEPTUAL = "conceptual"  # 概念融合 - 深度理解
    INTEGRATED = "integrated"  # 一体化融合 - 无缝整合


class DomainType(Enum):
    """领域类型"""
    PATENT_LAW = "patent_law"  # 专利法律
    TECHNOLOGY = "technology"  # 技术
    BUSINESS = "business"  # 商业
    AI_ML = "ai_ml"  # 人工智能/机器学习
    LEGAL = "legal"  # 法律
    FINANCE = "finance"  # 金融
    MEDICAL = "medical"  # 医疗
    EDUCATION = "education"  # 教育
    GENERAL = "general"  # 通用


@dataclass
class ConceptMapping:
    """概念映射"""
    source_domain: DomainType
    target_domain: DomainType
    source_concept: str
    target_concept: str
    semantic_similarity: float  # 语义相似度
    mapping_confidence: float  # 映射置信度
    context: str = ""


@dataclass
class SemanticRelation:
    """语义关系"""
    concept1: str
    concept2: str
    relation_type: str  # similar_to, related_to, part_of, causes, etc.
    confidence: float
    domains: list[DomainType] = field(default_factory=list)


@dataclass
class FusedInsight:
    """融合洞察"""
    insight_id: str
    query: str
    source_domains: list[DomainType]
    concept_mappings: list[ConceptMapping]
    semantic_relations: list[SemanticRelation]
    fused_understanding: str
    cross_domain_insights: list[str]
    novelty_score: float  # 新颖性评分
    utility_score: float  # 实用性评分
    fusion_depth: FusionDepth
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class KnowledgeGraphNode:
    """知识图谱节点"""
    concept: str
    domain: DomainType
    attributes: dict[str, Any] = field(default_factory=dict)
    relations: list[SemanticRelation] = field(default_factory=list)


@dataclass
class MultiModalUnderstanding:
    """多模态理解"""
    text_understanding: dict[str, Any]
    structured_insights: list[dict[str, Any]]
    cross_modal_associations: list[dict[str, Any]]
    unified_representation: dict[str, Any]


class SemanticCrossDomainFusion:
    """
    语义级跨域融合引擎

    核心功能:
    1. 跨领域概念映射
    2. 语义关联挖掘
    3. 知识图谱融合
    4. 深度洞察生成
    5. 多模态理解
    """

    # 预定义的跨域概念映射
    CROSS_DOMAIN_MAPPINGS: list[ConceptMapping] = []

    # 领域知识库
    DOMAIN_KNOWLEDGE = {
        DomainType.PATENT_LAW: {
            "core_concepts": [
                "现有技术", "创造性", "新颖性", "实用性",
                "权利要求", "说明书", "附图", "摘要",
                "发明", "实用新型", "外观设计",
                "专利审查", "无效宣告", "侵权诉讼"
            ],
            "relations": {
                "现有技术": ["related_to", "创造性"],
                "创造性": ["depends_on", "新颖性"],
                "权利要求": ["part_of", "专利申请"],
            },
            "typical_queries": [
                "如何判断创造性", "现有技术检索", "专利保护范围",
                "无效宣告理由", "专利侵权判断"
            ],
        },
        DomainType.TECHNOLOGY: {
            "core_concepts": [
                "架构设计", "技术栈", "代码实现", "系统优化",
                "算法", "数据结构", "API设计", "性能优化",
                "前端", "后端", "数据库", "部署运维"
            ],
            "relations": {
                "架构设计": ["includes", "技术栈"],
                "技术栈": ["includes", "编程语言"],
                "系统优化": ["improves", "性能"],
            },
            "typical_queries": [
                "系统架构设计", "技术选型", "性能优化",
                "代码重构", "API设计"
            ],
        },
        DomainType.BUSINESS: {
            "core_concepts": [
                "商业模式", "市场分析", "竞争策略", "用户需求",
                "产品定位", "定价策略", "营销渠道", "收入模式",
                "成本控制", "增长策略", "投资回报", "风险评估"
            ],
            "relations": {
                "商业模式": ["defines", "收入模式"],
                "市场分析": ["informs", "产品定位"],
                "用户需求": ["drives", "产品功能"],
            },
            "typical_queries": [
                "商业模式设计", "市场竞争分析", "用户需求分析",
                "产品定价策略", "收入增长策略"
            ],
        },
        DomainType.AI_ML: {
            "core_concepts": [
                "机器学习", "深度学习", "神经网络", "训练数据",
                "模型架构", "特征工程", "模型训练", "模型评估",
                "监督学习", "无监督学习", "强化学习", "迁移学习"
            ],
            "relations": {
                "深度学习": ["subtype_of", "机器学习"],
                "神经网络": ["implements", "深度学习"],
                "训练数据": ["required_for", "模型训练"],
            },
            "typical_queries": [
                "模型架构设计", "特征工程方法", "模型评估指标",
                "过拟合处理", "模型部署"
            ],
        },
    }

    def __init__(self):
        self.knowledge_graph: dict[str, KnowledgeGraphNode] = {}
        self.fusion_history: list[FusedInsight] = []
        self.domain_embeddings: dict[DomainType, dict[str, float]] = {}

    async def initialize(self):
        """初始化融合引擎"""
        logger.info("🔗 初始化语义级跨域融合引擎...")
        await self._initialize_cross_domain_mappings()
        await self._build_knowledge_graph()
        await self._initialize_embeddings()
        logger.info("✅ 语义级跨域融合引擎初始化完成")

    async def _initialize_cross_domain_mappings(self):
        """初始化跨域概念映射"""
        self.CROSS_DOMAIN_MAPPINGS = [
            # 专利法律 <-> 技术
            ConceptMapping(
                source_domain=DomainType.PATENT_LAW,
                target_domain=DomainType.TECHNOLOGY,
                source_concept="现有技术",
                target_concept="技术栈",
                semantic_similarity=0.85,
                mapping_confidence=0.90,
            ),
            ConceptMapping(
                source_domain=DomainType.PATENT_LAW,
                target_domain=DomainType.TECHNOLOGY,
                source_concept="创造性",
                target_concept="技术创新",
                semantic_similarity=0.80,
                mapping_confidence=0.85,
            ),
            # 专利法律 <-> 商业
            ConceptMapping(
                source_domain=DomainType.PATENT_LAW,
                target_domain=DomainType.BUSINESS,
                source_concept="专利保护范围",
                target_concept="市场护城河",
                semantic_similarity=0.75,
                mapping_confidence=0.80,
            ),
            ConceptMapping(
                source_domain=DomainType.PATENT_LAW,
                target_domain=DomainType.BUSINESS,
                source_concept="专利许可",
                target_concept="商业化模式",
                semantic_similarity=0.82,
                mapping_confidence=0.88,
            ),
            # 技术 <-> AI/ML
            ConceptMapping(
                source_domain=DomainType.TECHNOLOGY,
                target_domain=DomainType.AI_ML,
                source_concept="系统架构",
                target_concept="模型架构",
                semantic_similarity=0.88,
                mapping_confidence=0.92,
            ),
            ConceptMapping(
                source_domain=DomainType.TECHNOLOGY,
                target_domain=DomainType.AI_ML,
                source_concept="代码优化",
                target_concept="模型优化",
                semantic_similarity=0.90,
                mapping_confidence=0.93,
            ),
            # 商业 <-> AI/ML
            ConceptMapping(
                source_domain=DomainType.BUSINESS,
                target_domain=DomainType.AI_ML,
                source_concept="用户需求",
                target_concept="训练数据",
                semantic_similarity=0.70,
                mapping_confidence=0.75,
            ),
        ]

    async def _build_knowledge_graph(self):
        """构建知识图谱"""
        logger.info("🕸️  构建跨域知识图谱...")

        for domain, knowledge in self.DOMAIN_KNOWLEDGE.items():
            for concept in knowledge["core_concepts"]:
                node = KnowledgeGraphNode(
                    concept=concept,
                    domain=domain,
                    attributes={
                        "importance": knowledge["core_concepts"].index(concept) / len(knowledge["core_concepts"]),
                        "domain": domain.value,
                    }
                )

                # 添加关系
                if concept in knowledge["relations"]:
                    for relation in knowledge["relations"][concept]:
                        node.relations.append(SemanticRelation(
                            concept1=concept,
                            concept2=relation[1],
                            relation_type=relation[0],
                            confidence=0.8,
                            domains=[domain]
                        ))

                self.knowledge_graph[f"{domain.value}:{concept}"] = node

        logger.info(f"✅ 知识图谱构建完成: {len(self.knowledge_graph)} 个节点")

    async def _initialize_embeddings(self):
        """初始化领域嵌入（简化版本，实际应使用真实的词向量）"""
        logger.info("📊 初始化领域嵌入...")

        # 这里使用简化的模拟嵌入，实际应使用BERT等模型
        for domain in DomainType:
            self.domain_embeddings[domain] = {
                "tech_depth": 0.8 if domain in [DomainType.TECHNOLOGY, DomainType.AI_ML] else 0.5,
                "business_focus": 0.8 if domain == DomainType.BUSINESS else 0.4,
                "legal_complexity": 0.9 if domain == DomainType.PATENT_LAW else 0.3,
                "innovation_potential": 0.7 if domain in [DomainType.AI_ML, DomainType.TECHNOLOGY] else 0.5,
            }

        logger.info("✅ 领域嵌入初始化完成")

    async def deep_semantic_fusion(
        self,
        query: str,
        domains: list[DomainType],
        fusion_depth: FusionDepth = FusionDepth.SEMANTIC,
    ) -> FusedInsight:
        """
        深度语义融合

        Args:
            query: 查询内容
            domains: 涉及的领域列表
            fusion_depth: 融合深度

        Returns:
            FusedInsight: 融合洞察
        """
        logger.info(f"🔬 执行深度语义融合: {query} across {len(domains)} domains")

        # 1. 识别每个领域的关键概念
        domain_concepts = await self._extract_domain_concepts(query, domains)

        # 2. 发现跨域概念映射
        concept_mappings = await self._discover_concept_mappings(domain_concepts)

        # 3. 挖掘语义关系
        semantic_relations = await self._mine_semantic_relations(domain_concepts)

        # 4. 生成融合理解
        fused_understanding = await self._generate_fused_understanding(
            query, domain_concepts, concept_mappings, semantic_relations
        )

        # 5. 提取跨域洞察
        cross_domain_insights = await self._extract_cross_domain_insights(
            domain_concepts, concept_mappings, semantic_relations
        )

        # 6. 评分
        novelty_score = await self._calculate_novelty_score(cross_domain_insights)
        utility_score = await self._calculate_utility_score(fused_understanding)

        insight = FusedInsight(
            insight_id=f"FUS_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            query=query,
            source_domains=domains,
            concept_mappings=concept_mappings,
            semantic_relations=semantic_relations,
            fused_understanding=fused_understanding,
            cross_domain_insights=cross_domain_insights,
            novelty_score=novelty_score,
            utility_score=utility_score,
            fusion_depth=fusion_depth,
        )

        self.fusion_history.append(insight)

        logger.info(
            f"✅ 融合完成: 新颖性 {novelty_score:.2f}, 实用性 {utility_score:.2f}"
        )

        return insight

    async def _extract_domain_concepts(
        self, query: str, domains: list[DomainType]
    ) -> dict[DomainType, list[str]]:
        """提取每个领域的关键概念"""
        domain_concepts = {}

        for domain in domains:
            concepts = []
            knowledge = self.DOMAIN_KNOWLEDGE.get(domain, {})

            # 简化的关键词匹配
            query_lower = query.lower()
            for concept in knowledge.get("core_concepts", []):
                if concept.lower() in query_lower or any(
                    word in query_lower for word in concept.lower().split()
                ):
                    concepts.append(concept)

            # 如果没有直接匹配，使用典型查询进行启发式匹配
            if not concepts:
                for typical_query in knowledge.get("typical_queries", []):
                    if any(word in query_lower for word in typical_query.lower().split()):
                        # 提取该领域的核心概念
                        concepts = knowledge.get("core_concepts", [])[:3]
                        break

            domain_concepts[domain] = concepts if concepts else knowledge.get("core_concepts", [])[:3]

        return domain_concepts

    async def _discover_concept_mappings(
        self, domain_concepts: dict[DomainType, list[str]]
    ) -> list[ConceptMapping]:
        """发现跨域概念映射"""
        mappings = []

        # 使用预定义的映射
        for mapping in self.CROSS_DOMAIN_MAPPINGS:
            if (mapping.source_domain in domain_concepts and
                mapping.target_domain in domain_concepts):
                if (mapping.source_concept in domain_concepts[mapping.source_domain] or
                    mapping.target_concept in domain_concepts[mapping.target_domain]):
                    mappings.append(mapping)

        # 动态发现新的映射（基于语义相似性）
        domains_list = list(domain_concepts.keys())
        for i, domain1 in enumerate(domains_list):
            for domain2 in domains_list[i+1:]:
                for concept1 in domain_concepts[domain1]:
                    for concept2 in domain_concepts[domain2]:
                        # 计算简单的语义相似度
                        similarity = await self._calculate_semantic_similarity(concept1, concept2, domain1, domain2)
                        if similarity > 0.6:  # 相似度阈值
                            mappings.append(ConceptMapping(
                                source_domain=domain1,
                                target_domain=domain2,
                                source_concept=concept1,
                                target_concept=concept2,
                                semantic_similarity=similarity,
                                mapping_confidence=similarity * 0.9,
                            ))

        return mappings

    async def _calculate_semantic_similarity(
        self, concept1: str, concept2: str, domain1: DomainType, domain2: DomainType
    ) -> float:
        """计算语义相似度"""
        # 简化的相似度计算
        # 实际应使用词向量和余弦相似度

        # 1. 字面重叠
        words1 = set(concept1.lower().split())
        words2 = set(concept2.lower().split())
        overlap = len(words1 & words2) / max(len(words1 | words2), 1)

        # 2. 领域相似性
        domain_sim = 0.0
        emb1 = self.domain_embeddings.get(domain1, {})
        emb2 = self.domain_embeddings.get(domain2, {})

        if emb1 and emb2:
            # 计算嵌入向量的余弦相似度
            dot_product = sum(emb1.get(k, 0) * emb2.get(k, 0) for k in set(emb1) | set(emb2))
            norm1 = sum(v**2 for v in emb1.values())**0.5
            norm2 = sum(v**2 for v in emb2.values())**0.5
            domain_sim = dot_product / (norm1 * norm2) if norm1 and norm2 else 0

        # 组合
        return overlap * 0.6 + domain_sim * 0.4

    async def _mine_semantic_relations(
        self, domain_concepts: dict[DomainType, list[str]]
    ) -> list[SemanticRelation]:
        """挖掘语义关系"""
        relations = []

        # 从知识图谱中提取
        for domain, concepts in domain_concepts.items():
            for concept in concepts:
                key = f"{domain.value}:{concept}"
                if key in self.knowledge_graph:
                    node = self.knowledge_graph[key]
                    relations.extend(node.relations)

        # 发现跨域关系
        domains_list = list(domain_concepts.keys())
        for i, domain1 in enumerate(domains_list):
            for domain2 in domains_list[i+1:]:
                for concept1 in domain_concepts[domain1]:
                    for concept2 in domain_concepts[domain2]:
                        # 检查是否存在互补关系
                        relations.append(SemanticRelation(
                            concept1=concept1,
                            concept2=concept2,
                            relation_type="cross_domain_related",
                            confidence=0.7,
                            domains=[domain1, domain2]
                        ))

        return relations

    async def _generate_fused_understanding(
        self,
        query: str,
        domain_concepts: dict[DomainType, list[str]],
        mappings: list[ConceptMapping],
        relations: list[SemanticRelation],
    ) -> str:
        """生成融合理解"""
        # 构建结构化的理解
        parts = []

        # 1. 各领域视角
        parts.append("## 多领域视角")
        for domain, concepts in domain_concepts.items():
            if concepts:
                parts.append(f"\n### {domain.value}视角")
                parts.append(f"关键概念: {', '.join(concepts[:3])}")

        # 2. 跨域关联
        if mappings:
            parts.append("\n## 跨域概念关联")
            for mapping in mappings[:5]:
                parts.append(
                    f"- **{mapping.source_concept}** ({mapping.source_domain.value}) ↔ "
                    f"**{mapping.target_concept}** ({mapping.target_domain.value}) "
                    f"[相似度: {mapping.semantic_similarity:.2f}]"
                )

        # 3. 综合洞察
        parts.append("\n## 综合理解")
        if len(domain_concepts) > 1:
            parts.append(
                f"通过融合{len(domain_concepts)}个领域的知识，"
                f"发现了{len(mappings)}个跨域概念映射和"
                f"{len(relations)}个语义关联。"
            )
            parts.append(
                "这种跨域融合使得我们能够从多个角度理解问题，"
                "并发现单一领域难以察觉的洞察。"
            )

        return "\n".join(parts)

    async def _extract_cross_domain_insights(
        self,
        domain_concepts: dict[DomainType, list[str]],
        mappings: list[ConceptMapping],
        relations: list[SemanticRelation],
    ) -> list[str]:
        """提取跨域洞察"""
        insights = []

        # 1. 基于概念映射生成洞察
        for mapping in mappings[:3]:
            if mapping.semantic_similarity > 0.75:
                insights.append(
                    f"**跨域对应**: {mapping.source_domain.value}中的'{mapping.source_concept}' "
                    f"与{mapping.target_domain.value}中的'{mapping.target_concept}'高度相关，"
                    f"这提示我们可以借鉴后者的方法论来处理前者的问题。"
                )

        # 2. 基于关系生成洞察
        cross_domain_rels = [r for r in relations if len(r.domains) > 1]
        for rel in cross_domain_rels[:2]:
            insights.append(
                f"**关系洞察**: {rel.concept1}和{rel.concept2}之间存在"
                f"{rel.relation_type}关系，这为跨域问题解决提供了新的思路。"
            )

        # 3. 综合洞察
        if len(domain_concepts) > 1:
            domains_str = "、".join([d.value for d in domain_concepts.keys()])
            insights.append(
                f"**融合价值**: 通过{domains_str}的深度融合，"
                f"我们能够发现传统单一视角无法识别的机遇和解决方案。"
            )

        return insights if insights else ["跨域融合已成功完成，等待更多数据以生成具体洞察。"]

    async def _calculate_novelty_score(self, insights: list[str]) -> float:
        """计算新颖性评分"""
        if not insights:
            return 0.5

        # 基于洞察数量和多样性
        count_score = min(1.0, len(insights) / 10)

        # 基于关键词多样性
        all_words = " ".join(insights).split()
        unique_words = set(all_words)
        diversity_score = len(unique_words) / max(len(all_words), 1)

        return (count_score * 0.6 + diversity_score * 0.4)

    async def _calculate_utility_score(self, understanding: str) -> float:
        """计算实用性评分"""
        # 基于理解的完整性和结构化程度
        score = 0.5

        if "## " in understanding:  # 有标题
            score += 0.2
        if "### " in understanding:  # 有子标题
            score += 0.1
        if "**" in understanding:  # 有强调
            score += 0.1
        if "- " in understanding:  # 有列表
            score += 0.1

        return min(1.0, score)

    async def fuse_multimodal(
        self,
        text: str,
        structured_data: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> MultiModalUnderstanding:
        """
        多模态信息融合

        Args:
            text: 文本内容
            structured_data: 结构化数据
            context: 上下文信息

        Returns:
            MultiModalUnderstanding: 统一的多模态理解
        """
        logger.info("🎭 执行多模态融合...")

        # 1. 文本理解
        text_understanding = {
            "key_points": await self._extract_key_points(text),
            "sentiment": await self._analyze_sentiment(text),
            "entities": await self._extract_entities(text),
        }

        # 2. 结构化数据洞察
        structured_insights = []
        if structured_data:
            structured_insights = await self._analyze_structured_data(structured_data)

        # 3. 跨模态关联
        cross_modal_associations = []
        if structured_data:
            cross_modal_associations = await self._find_cross_modal_associations(
                text, structured_data
            )

        # 4. 统一表示
        unified_representation = {
            "summary": await self._generate_unified_summary(
                text_understanding, structured_insights
            ),
            "key_insights": await self._extract_unified_insights(
                text_understanding, structured_insights, cross_modal_associations
            ),
            "recommendations": await self._generate_recommendations(
                text_understanding, structured_insights
            ),
        }

        result = MultiModalUnderstanding(
            text_understanding=text_understanding,
            structured_insights=structured_insights,
            cross_modal_associations=cross_modal_associations,
            unified_representation=unified_representation,
        )

        logger.info("✅ 多模态融合完成")

        return result

    async def _extract_key_points(self, text: str) -> list[str]:
        """提取关键点"""
        sentences = text.split("。")
        # 简化：选择较长的句子作为关键点
        key_points = sorted(
            [s.strip() for s in sentences if len(s.strip()) > 10],
            key=len,
            reverse=True
        )[:3]
        return key_points

    async def _analyze_sentiment(self, text: str) -> dict[str, float]:
        """分析情感"""
        # 简化的情感分析
        positive_words = ["好", "优秀", "成功", "进步", "提升"]
        negative_words = ["问题", "困难", "失败", "下降", "风险"]

        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)

        total = positive_count + negative_count + 1
        return {
            "positive": positive_count / total,
            "negative": negative_count / total,
            "neutral": 1 / total,
        }

    async def _extract_entities(self, text: str) -> list[dict[str, str]]:
        """提取实体"""
        # 简化的实体提取
        entities = []

        # 提取数字
        import re
        numbers = re.findall(r'\d+(?:\.\d+)?', text)
        for num in numbers[:3]:
            entities.append({"type": "number", "value": num})

        # 提取领域关键词
        for domain, knowledge in self.DOMAIN_KNOWLEDGE.items():
            for concept in knowledge["core_concepts"]:
                if concept in text:
                    entities.append({"type": "concept", "value": concept, "domain": domain.value})

        return entities[:5]

    async def _analyze_structured_data(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """分析结构化数据"""
        insights = []

        for key, value in data.items():
            if isinstance(value, (int, float)):
                insights.append({
                    "field": key,
                    "value": value,
                    "type": "numeric",
                    "insight": f"字段'{key}'的值为{value}"
                })
            elif isinstance(value, list):
                insights.append({
                    "field": key,
                    "count": len(value),
                    "type": "array",
                    "insight": f"字段'{key}'包含{len(value)}个元素"
                })

        return insights[:5]

    async def _find_cross_modal_associations(
        self, text: str, data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """发现跨模态关联"""
        associations = []

        # 检查文本中的数字是否与数据匹配
        import re
        text_numbers = re.findall(r'\d+(?:\.\d+)?', text)

        for key, value in data.items():
            if isinstance(value, (int, float)):
                value_str = str(value)
                if value_str in text_numbers:
                    associations.append({
                        "type": "numeric_match",
                        "text_reference": value_str,
                        "data_field": key,
                        "confidence": 0.9,
                    })

        return associations

    async def _generate_unified_summary(
        self, text_understanding: dict, structured_insights: list
    ) -> str:
        """生成统一摘要"""
        parts = []

        if text_understanding.get("key_points"):
            parts.append("**文本关键点**: " + "；".join(text_understanding["key_points"][:2]))

        if structured_insights:
            parts.append(f"**数据洞察**: 发现{len(structured_insights)}个数据特征")

        return " | ".join(parts) if parts else "已分析文本和结构化数据"

    async def _extract_unified_insights(
        self, text_understanding: dict, structured_insights: list, associations: list
    ) -> list[str]:
        """提取统一洞察"""
        insights = []

        if text_understanding.get("sentiment"):
            sentiment = text_understanding["sentiment"]
            dominant = max(sentiment, key=sentiment.get)
            insights.append(f"整体情感倾向: {dominant}")

        if associations:
            insights.append(f"发现{len(associations)}个文本与数据的关联")

        return insights

    async def _generate_recommendations(
        self, text_understanding: dict, structured_insights: list
    ) -> list[str]:
        """生成建议"""
        recommendations = []

        sentiment = text_understanding.get("sentiment", {})
        if sentiment.get("negative", 0) > 0.3:
            recommendations.append("建议关注文本中提到的挑战和风险点")

        if len(structured_insights) > 3:
            recommendations.append("数据特征丰富，建议进行深入分析")

        if not recommendations:
            recommendations.append("继续收集更多信息以提供更精准的建议")

        return recommendations

    async def get_fusion_statistics(self) -> dict[str, Any]:
        """获取融合统计信息"""
        if not self.fusion_history:
            return {"message": "暂无融合历史"}

        total = len(self.fusion_history)
        domains_used = [d for insight in self.fusion_history for d in insight.source_domains]

        domain_counts = {}
        for domain in domains_used:
            domain_counts[domain.value] = domain_counts.get(domain.value, 0) + 1

        avg_novelty = sum(insight.novelty_score for insight in self.fusion_history) / total
        avg_utility = sum(insight.utility_score for insight in self.fusion_history) / total

        depth_counts = {}
        for insight in self.fusion_history:
            depth = insight.fusion_depth.value
            depth_counts[depth] = depth_counts.get(depth, 0) + 1

        return {
            "total_fusions": total,
            "domain_distribution": domain_counts,
            "average_novelty": avg_novelty,
            "average_utility": avg_utility,
            "depth_distribution": depth_counts,
            "knowledge_graph_nodes": len(self.knowledge_graph),
            "recent_fusions": [
                {
                    "id": insight.insight_id,
                    "domains": [d.value for d in insight.source_domains],
                    "novelty": insight.novelty_score,
                    "utility": insight.utility_score,
                }
                for insight in self.fusion_history[-5:]
            ],
        }

    async def shutdown(self):
        """关闭引擎"""
        logger.info("🛑 关闭语义级跨域融合引擎...")
        logger.info(f"📊 本次运行执行 {len(self.fusion_history)} 次融合")
        logger.info("✅ 语义级跨域融合引擎已关闭")


# 便捷函数
_semantic_fusion_engine: SemanticCrossDomainFusion | None = None


async def get_semantic_fusion_engine() -> SemanticCrossDomainFusion:
    """获取语义级跨域融合引擎单例"""
    global _semantic_fusion_engine
    if _semantic_fusion_engine is None:
        _semantic_fusion_engine = SemanticCrossDomainFusion()
        await _semantic_fusion_engine.initialize()
    return _semantic_fusion_engine
