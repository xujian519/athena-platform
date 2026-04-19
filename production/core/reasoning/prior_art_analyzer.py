#!/usr/bin/env python3
from __future__ import annotations
"""
现有技术图谱分析引擎
Prior Art Knowledge Graph Analyzer

基于引用关系和相似性关系的现有技术图谱分析,自动生成技术路线图
作者: 小诺·双鱼座
创建时间: 2025-12-21
版本: v1.0.0 "技术图谱分析"
"""

import logging
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import networkx as nx

from ..knowledge.patent_analysis.enhanced_knowledge_graph import EnhancedPatentKnowledgeGraph

logger = logging.getLogger(__name__)


class RelationType(Enum):
    """关系类型"""

    CITES = "cites"  # 引用
    CITED_BY = "cited_by"  # 被引用
    SIMILAR_TO = "similar_to"  # 相似
    RELATED_TO = "related_to"  # 相关
    IMPROVES_UPON = "improves_upon"  # 改进
    ALTERNATIVE_TO = "alternative_to"  # 替代
    DERIVED_FROM = "derived_from"  # 派生


class AnalysisType(Enum):
    """分析类型"""

    TECHNICAL_EVOLUTION = "technical_evolution"  # 技术演进
    INNOVATION_TREND = "innovation_trend"  # 创新趋势
    COMPETITIVE_LANDSCAPE = "competitive_landscape"  # 竞争格局
    TECHNOLOGY_ROADMAP = "technology_roadmap"  # 技术路线图
    PRIOR_ART_MAPPING = "prior_art_mapping"  # 现有技术映射


class NodeType(Enum):
    """节点类型"""

    PATENT = "patent"
    COMPANY = "company"
    INVENTOR = "inventor"
    TECHNOLOGY = "technology"
    INDUSTRY = "industry"


@dataclass
class TechNode:
    """技术节点"""

    node_id: str
    node_type: NodeType
    title: str
    abstract: str
    publication_date: datetime
    assignee: str | None = None
    inventors: list[str] = field(default_factory=list)
    technology_field: str = ""
    claims: int = 0
    citations: int = 0
    features: dict[str, Any] = field(default_factory=dict)


@dataclass
class TechRelation:
    """技术关系"""

    source_id: str
    target_id: str
    relation_type: RelationType
    strength: float  # 关系强度 0-1
    evidence: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TechnologyCluster:
    """技术集群"""

    cluster_id: str
    cluster_name: str
    core_patents: list[str]
    supporting_patents: list[str]
    key_technologies: list[str]
    innovation_score: float
    market_potential: float
    time_span: tuple[datetime, datetime]
    description: str


@dataclass
class TechEvolution:
    """技术演进"""

    evolution_id: str
    technology_name: str
    evolution_path: list[TechNode]
    key_innovations: list[TechNode]
    evolution_rate: float  # 演进速度
    future_trends: list[str]
    analysis_timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class TechnologyRoadmap:
    """技术路线图"""

    roadmap_id: str
    focus_technology: str
    time_horizon: tuple[datetime, datetime]
    development_phases: list[dict[str, Any]]
    key_milestones: list[TechNode]
    competing_technologies: list[str]
    market_opportunities: list[str]
    risk_factors: list[str]


class PriorArtAnalyzer:
    """现有技术图谱分析引擎"""

    def __init__(self):
        self.name = "现有技术图谱分析引擎"
        self.version = "1.0.0"
        self._initialized = False
        self.logger = logging.getLogger(self.name)

        # 知识图谱集成
        self.knowledge_graph: EnhancedPatentKnowledgeGraph | None = None

        # 技术图谱
        self.tech_graph = nx.DiGraph()
        self.patents: dict[str, TechNode] = {}
        self.relations: list[TechRelation] = []

        # 分析缓存
        self.analysis_cache: dict[str, Any] = {}
        self.cluster_cache: dict[str, TechnologyCluster] = {}

        # 配置参数
        self.config = {
            "max_analyze_depth": 5,
            "similarity_threshold": 0.7,
            "citation_weight": 0.6,
            "temporal_weight": 0.4,
            "min_cluster_size": 3,
            "cache_ttl": 3600,
            "enable_temporal_analysis": True,
            "enable_competitive_analysis": True,
        }

        # 统计信息
        self.stats = {
            "patents_analyzed": 0,
            "relations_extracted": 0,
            "clusters_identified": 0,
            "roadmaps_generated": 0,
            "analysis_count": 0,
        }

    async def initialize(self):
        """初始化现有技术分析引擎"""
        try:
            # 初始化知识图谱
            self.knowledge_graph = await EnhancedPatentKnowledgeGraph.initialize()

            # 构建技术图谱
            await self._build_technology_graph()

            self._initialized = True
            self.logger.info("✅ PriorArtAnalyzer 初始化完成")
            return True

        except Exception:
            return False

    async def _build_technology_graph(self):
        """构建技术图谱"""
        try:
            # 从知识图谱加载专利数据
            await self._load_patent_data()

            # 提取技术关系
            await self._extract_technology_relations()

            # 构建网络结构
            await self._construct_network_structure()

            self.logger.info(
                f"✅ 技术图谱构建完成: {len(self.patents)} 个节点, {len(self.relations)} 条关系"
            )

        except Exception as e:
            self.logger.error(f"技术图谱构建失败: {e}")

    async def _load_patent_data(self):
        """加载专利数据"""
        try:
            # 搜索所有专利节点
            search_results = await self.knowledge_graph.search_hybrid(
                query="patent invention", node_types=["patent"]
            )

            for result in search_results:
                patent_node = TechNode(
                    node_id=result.node_id,
                    node_type=NodeType.PATENT,
                    title=result.title,
                    abstract=result.content,
                    publication_date=datetime.now(),  # 实际应该从数据中解析
                    technology_field=result.context.get("technology_field", ""),
                    features=result.context,
                )

                self.patents[result.node_id] = patent_node
                self.tech_graph.add_node(result.node_id, **asdict(patent_node))

            self.stats["patents_analyzed"] = len(self.patents)

        except Exception as e:
            self.logger.error(f"专利数据加载失败: {e}")

    async def _extract_technology_relations(self):
        """提取技术关系"""
        try:
            for patent_id, _patent_node in self.patents.items():
                # 获取相关节点
                related_nodes = await self.knowledge_graph.get_node_with_context(
                    patent_id, max_hops=2
                )

                if related_nodes and "connected_nodes" in related_nodes["context"]:
                    for connected in related_nodes["context"]["connected_nodes"]:
                        relation = await self._analyze_relation(
                            patent_id, connected["node_id"], connected["relation_type"]
                        )
                        if relation:
                            self.relations.append(relation)
                            self.tech_graph.add_edge(
                                relation.source_id,
                                relation.target_id,
                                relation_type=relation.relation_type.value,
                                strength=relation.strength,
                            )

            self.stats["relations_extracted"] = len(self.relations)

        except Exception as e:
            self.logger.error(f"技术关系提取失败: {e}")

    async def _analyze_relation(
        self, source_id: str, target_id: str, relation_type: str
    ) -> TechRelation | None:
        """分析技术关系"""
        try:
            # 映射关系类型
            relation_mapping = {
                "cites": RelationType.CITES,
                "similar_to": RelationType.SIMILAR_TO,
                "related_to": RelationType.RELATED_TO,
                "improves": RelationType.IMPROVES_UPON,
            }

            mapped_type = relation_mapping.get(relation_type, RelationType.RELATED_TO)

            # 计算关系强度
            strength = await self._calculate_relation_strength(source_id, target_id, mapped_type)

            if strength < self.config.get("similarity_threshold"):
                return None

            # 获取证据
            evidence = await self._gather_relation_evidence(source_id, target_id, mapped_type)

            return TechRelation(
                source_id=source_id,
                target_id=target_id,
                relation_type=mapped_type,
                strength=strength,
                evidence=evidence,
            )

        except Exception:
            return None

    async def _calculate_relation_strength(
        self, source_id: str, target_id: str, relation_type: RelationType
    ) -> float:
        """计算关系强度"""
        try:
            base_strength = 0.5

            # 基于关系类型的强度调整
            type_weights = {
                RelationType.CITES: 0.8,
                RelationType.SIMILAR_TO: 0.7,
                RelationType.RELATED_TO: 0.6,
                RelationType.IMPROVES_UPON: 0.9,
                RelationType.ALTERNATIVE_TO: 0.5,
                RelationType.DERIVED_FROM: 0.7,
            }

            base_strength *= type_weights.get(relation_type, 0.5)

            # 基于时间关系的调整
            if (
                self.config.get("enable_temporal_analysis")
                and source_id in self.patents
                and target_id in self.patents
            ):
                source_node = self.patents[source_id]
                target_node = self.patents[target_id]

                time_diff = abs((source_node.publication_date - target_node.publication_date).days)
                temporal_factor = max(0.1, 1.0 - time_diff / 3650)  # 10年内的技术相关性

                base_strength *= temporal_factor

            return min(1.0, base_strength)

        except Exception:
            return 0.5

    async def _gather_relation_evidence(
        self, source_id: str, target_id: str, relation_type: RelationType
    ) -> list[str]:
        """收集关系证据"""
        evidence = []

        try:
            if source_id in self.patents:
                source_patent = self.patents[source_id]
                evidence.append(f"源专利: {source_patent.title}")

            if target_id in self.patents:
                target_patent = self.patents[target_id]
                evidence.append(f"目标专利: {target_patent.title}")

            evidence.append(f"关系类型: {relation_type.value}")

            # 基于技术领域相似性
            if source_id in self.patents and target_id in self.patents:
                source_field = self.patents[source_id].technology_field
                target_field = self.patents[target_id].technology_field

                if source_field == target_field:
                    evidence.append(f"同一技术领域: {source_field}")

        except Exception as e:
            self.logger.warning(f"证据生成失败: {e}")

        return evidence

    async def _construct_network_structure(self):
        """构建网络结构"""
        try:
            # 计算网络指标
            self._calculate_network_metrics()

            # 识别关键节点
            self._identify_key_nodes()

        except Exception as e:
            self.logger.error(f"网络结构构建失败: {e}")

    def _calculate_network_metrics(self) -> Any:
        """计算网络指标"""
        try:
            # 计算度中心性
            degree_centrality = nx.degree_centrality(self.tech_graph)

            # 计算介数中心性
            betweenness_centrality = nx.betweenness_centrality(self.tech_graph)

            # 计算接近中心性
            closeness_centrality = nx.closeness_centrality(self.tech_graph)

            # 更新节点指标
            for node_id in self.tech_graph.nodes():
                if node_id in self.patents:
                    patent_node = self.patents[node_id]
                    patent_node.features.update(
                        {
                            "degree_centrality": degree_centrality.get(node_id, 0),
                            "betweenness_centrality": betweenness_centrality.get(node_id, 0),
                            "closeness_centrality": closeness_centrality.get(node_id, 0),
                        }
                    )

        except Exception as e:
            self.logger.warning(f"网络指标计算失败: {e}")

    def _identify_key_nodes(self) -> Any:
        """识别关键节点"""
        try:
            # 基于多种指标识别重要专利
            importance_scores = {}

            for node_id, patent_node in self.patents.items():
                score = 0

                # 基于中心性
                score += patent_node.features.get("degree_centrality", 0) * 0.3
                score += patent_node.features.get("betweenness_centrality", 0) * 0.2

                # 基于被引次数
                score += min(1.0, patent_node.citations / 100) * 0.3

                # 基于权利要求数量
                score += min(1.0, patent_node.claims / 20) * 0.2

                importance_scores[node_id] = score

            # 标记重要专利
            sorted_patents = sorted(importance_scores.items(), key=lambda x: x[1], reverse=True)
            top_10_percent = int(len(sorted_patents) * 0.1)

            for node_id, score in sorted_patents[:top_10_percent]:
                self.patents[node_id].features["key_patent"] = True
                self.patents[node_id].features["importance_score"] = score

        except Exception as e:
            self.logger.warning(f"关键节点识别失败: {e}")

    async def analyze_technology_evolution(
        self, technology_field: str, time_range: tuple[datetime, datetime] | None = None
    ) -> TechEvolution:
        """
        分析技术演进

        Args:
            technology_field: 技术领域
            time_range: 时间范围

        Returns:
            TechEvolution: 技术演进分析结果
        """
        if not self._initialized:
            raise RuntimeError("PriorArtAnalyzer未初始化")

        self.stats["analysis_count"] += 1

        try:
            # 筛选相关专利
            relevant_patents = await self._filter_patents_by_field(technology_field, time_range)

            if not relevant_patents:
                raise ValueError(f"未找到技术领域 '{technology_field}' 的相关专利")

            # 构建演进路径
            evolution_path = await self._build_evolution_path(relevant_patents)

            # 识别关键创新
            key_innovations = await self._identify_key_innovations(evolution_path)

            # 计算演进速度
            evolution_rate = self._calculate_evolution_rate(evolution_path)

            # 预测未来趋势
            future_trends = await self._predict_future_trends(evolution_path, key_innovations)

            evolution = TechEvolution(
                evolution_id=f"evolution_{technology_field}_{datetime.now().strftime('%Y%m%d')}",
                technology_name=technology_field,
                evolution_path=evolution_path,
                key_innovations=key_innovations,
                evolution_rate=evolution_rate,
                future_trends=future_trends,
            )

            self.logger.info(f"✅ 技术演进分析完成: {technology_field}")
            return evolution

        except Exception:
            raise

    async def _filter_patents_by_field(
        self, technology_field: str, time_range: tuple[datetime, datetime]) -> list[TechNode]:
        """按技术领域筛选专利"""
        relevant_patents = []

        for patent in self.patents.values():
            # 技术领域匹配
            if technology_field.lower() in patent.technology_field.lower():
                # 时间范围筛选
                if time_range:
                    start_date, end_date = time_range
                    if start_date <= patent.publication_date <= end_date:
                        relevant_patents.append(patent)
                else:
                    relevant_patents.append(patent)

        # 按时间排序
        relevant_patents.sort(key=lambda p: p.publication_date)
        return relevant_patents

    async def _build_evolution_path(self, patents: list[TechNode]) -> list[TechNode]:
        """构建技术演进路径"""
        evolution_path = []

        # 基于时间和技术相似性构建路径
        for i, patent in enumerate(patents):
            evolution_path.append(patent)

            # 寻找直接的技术演进关系
            for j in range(i + 1, min(i + 5, len(patents))):  # 检查后续4个专利
                next_patent = patents[j]

                # 检查是否存在改进关系
                has_improvement = await self._check_improvement_relation(patent, next_patent)
                if has_improvement:
                    # 在图中添加演进边
                    if not self.tech_graph.has_edge(patent.node_id, next_patent.node_id):
                        self.tech_graph.add_edge(
                            patent.node_id,
                            next_patent.node_id,
                            relation_type=RelationType.IMPROVES_UPON.value,
                            strength=0.8,
                        )

        return evolution_path

    async def _check_improvement_relation(
        self, earlier_patent: TechNode, later_patent: TechNode
    ) -> bool:
        """检查改进关系"""
        # 简化的改进关系判断逻辑
        # 实际应用中需要更复杂的语义分析

        # 检查时间顺序
        if later_patent.publication_date <= earlier_patent.publication_date:
            return False

        # 检查技术领域相似性
        if earlier_patent.technology_field != later_patent.technology_field:
            return False

        # 基于标题和摘要的相似性
        similarity = self._calculate_text_similarity(
            earlier_patent.title + " " + earlier_patent.abstract,
            later_patent.title + " " + later_patent.abstract,
        )

        return similarity > 0.3  # 相似度阈值

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        try:
            # 简化的文本相似度计算
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())

            intersection = words1.intersection(words2)
            union = words1.union(words2)

            return len(intersection) / len(union) if union else 0.0

        except Exception:
            return 0.0

    async def _identify_key_innovations(self, evolution_path: list[TechNode]) -> list[TechNode]:
        """识别关键创新"""
        key_innovations = []

        # 基于多种指标识别关键创新
        for patent in evolution_path:
            innovation_score = 0

            # 重要性分数
            importance_score = patent.features.get("importance_score", 0)
            innovation_score += importance_score * 0.4

            # 权利要求数量
            claim_score = min(1.0, patent.claims / 15)
            innovation_score += claim_score * 0.3

            # 被引次数
            citation_score = min(1.0, patent.citations / 50)
            innovation_score += citation_score * 0.3

            # 如果分数超过阈值,认为是关键创新
            if innovation_score > 0.6:
                patent.features["innovation_score"] = innovation_score
                key_innovations.append(patent)

        # 按创新分数排序
        key_innovations.sort(key=lambda p: p.features.get("innovation_score", 0), reverse=True)

        return key_innovations

    def _calculate_evolution_rate(self, evolution_path: list[TechNode]) -> float:
        """计算技术演进速度"""
        if len(evolution_path) < 2:
            return 0.0

        # 计算时间跨度
        start_time = evolution_path[0].publication_date
        end_time = evolution_path[-1].publication_date
        time_span = (end_time - start_time).days

        if time_span == 0:
            return 0.0

        # 计算演进速度(专利数量/年)
        patents_per_year = len(evolution_path) * 365.25 / time_span

        # 归一化到0-1范围
        return min(1.0, patents_per_year / 100)  # 100个专利/年为最大速度

    async def _predict_future_trends(
        self, evolution_path: list[TechNode], key_innovations: list[TechNode]
    ) -> list[str]:
        """预测未来趋势"""
        trends = []

        try:
            # 基于近期专利分析趋势
            if len(evolution_path) >= 3:
                recent_patents = evolution_path[-3:]

                # 提取关键技术词汇
                tech_keywords = self._extract_technology_keywords(recent_patents)

                # 基于关键词生成趋势预测
                trends.extend([f"向{keyword}方向发展" for keyword in tech_keywords[:3]])

            # 基于关键创新预测
            for innovation in key_innovations[:2]:
                trends.append(f"基于{innovation.title}的技术优化")

            # 添加通用趋势
            trends.extend(["技术集成与融合", "智能化和自动化", "成本降低和效率提升"])

        except Exception as e:
            self.logger.warning(f"趋势预测失败: {e}")

        return list(set(trends))  # 去重

    def _extract_technology_keywords(self, patents: list[TechNode]) -> list[str]:
        """提取技术关键词"""
        all_text = " ".join([p.title + " " + p.abstract for p in patents])

        # 简化的关键词提取
        # 实际应用中应该使用TF-IDF或TextRank等算法
        common_words = {
            "method",
            "system",
            "device",
            "apparatus",
            "process",
            "based",
            "using",
            "for",
            "with",
        }
        words = [
            word.lower()
            for word in all_text.split()
            if word.isalpha() and len(word) > 3 and word.lower() not in common_words
        ]

        # 统计词频
        word_freq = defaultdict(int)
        for word in words:
            word_freq[word] += 1

        # 返回最高频的词汇
        return [
            word for word, _ in sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        ]

    async def generate_technology_roadmap(
        self, focus_technology: str, time_horizon_years: int = 5
    ) -> TechnologyRoadmap:
        """
        生成技术路线图

        Args:
            focus_technology: 重点关注的技术
            time_horizon_years: 时间跨度(年)

        Returns:
            TechnologyRoadmap: 技术路线图
        """
        self.stats["roadmaps_generated"] += 1

        try:
            # 分析技术演进
            evolution = await self.analyze_technology_evolution(focus_technology)

            # 确定时间范围
            current_time = datetime.now()
            end_time = current_time + timedelta(days=time_horizon_years * 365)

            # 识别开发阶段
            development_phases = await self._identify_development_phases(evolution)

            # 确定关键里程碑
            key_milestones = await self._identify_key_milestones(evolution, development_phases)

            # 分析竞争技术
            competing_technologies = await self._analyze_competing_technologies(focus_technology)

            # 识别市场机会
            market_opportunities = await self._identify_market_opportunities(evolution)

            # 识别风险因素
            risk_factors = await self._identify_risk_factors(evolution)

            roadmap = TechnologyRoadmap(
                roadmap_id=f"roadmap_{focus_technology}_{datetime.now().strftime('%Y%m%d')}",
                focus_technology=focus_technology,
                time_horizon=(current_time, end_time),
                development_phases=development_phases,
                key_milestones=key_milestones,
                competing_technologies=competing_technologies,
                market_opportunities=market_opportunities,
                risk_factors=risk_factors,
            )

            self.logger.info(f"✅ 技术路线图生成完成: {focus_technology}")
            return roadmap

        except Exception:
            raise

    async def _identify_development_phases(self, evolution: TechEvolution) -> list[dict[str, Any]]:
        """识别开发阶段"""
        phases = []

        if not evolution.evolution_path:
            return phases

        # 基于时间分布划分阶段
        total_patents = len(evolution.evolution_path)
        patents_per_phase = max(1, total_patents // 4)  # 分为4个阶段

        phase_names = ["基础研究", "技术开发", "应用优化", "产业化"]

        for i, phase_name in enumerate(phase_names):
            start_idx = i * patents_per_phase
            end_idx = min((i + 1) * patents_per_phase, total_patents)

            if start_idx < total_patents:
                phase_patents = evolution.evolution_path[start_idx:end_idx]

                phase = {
                    "phase_name": phase_name,
                    "patent_count": len(phase_patents),
                    "time_span": (
                        phase_patents[0].publication_date,
                        phase_patents[-1].publication_date,
                    ),
                    "key_technologies": [patent.technology_field for patent in phase_patents[:3]],
                    "development_focus": self._get_phase_focus(phase_name),
                }

                phases.append(phase)

        return phases

    def _get_phase_focus(self, phase_name: str) -> str:
        """获取阶段重点"""
        focus_map = {
            "基础研究": "理论探索和概念验证",
            "技术开发": "原型开发和功能实现",
            "应用优化": "性能优化和应用测试",
            "产业化": "规模化生产和市场推广",
        }
        return focus_map.get(phase_name, "持续改进")

    async def _identify_key_milestones(
        self, evolution: TechEvolution, development_phases: list[dict[str, Any]]) -> list[TechNode]:
        """识别关键里程碑"""
        milestones = []

        # 将关键创新作为里程碑
        milestones.extend(evolution.key_innovations[:5])

        # 添加阶段转换点
        for phase in development_phases:
            if phase["patent_count"] > 0:
                # 选择每个阶段的代表性专利
                phase_patents = [
                    p
                    for p in evolution.evolution_path
                    if phase["time_span"][0] <= p.publication_date <= phase["time_span"][1]
                ]

                if phase_patents:
                    # 选择最重要的专利
                    best_patent = max(
                        phase_patents, key=lambda p: p.features.get("importance_score", 0)
                    )
                    if best_patent not in milestones:
                        milestones.append(best_patent)

        # 按时间排序
        milestones.sort(key=lambda p: p.publication_date)

        return milestones

    async def _analyze_competing_technologies(self, focus_technology: str) -> list[str]:
        """分析竞争技术"""
        competing_techs = []

        try:
            # 基于技术领域寻找相似技术
            related_fields = []
            for patent in self.patents.values():
                if focus_technology.lower() in patent.technology_field.lower():
                    # 提取相关技术领域
                    related_fields.append(patent.technology_field)

            # 统计相关领域
            field_counts = defaultdict(int)
            for field in related_fields:
                field_counts[field] += 1

            # 排除主要技术领域,返回竞争技术
            for field, _count in sorted(field_counts.items(), key=lambda x: x[1], reverse=True):
                if field != focus_technology and len(competing_techs) < 5:
                    competing_techs.append(field)

        except Exception as e:
            self.logger.warning(f"竞争技术识别失败: {e}")

        return competing_techs

    async def _identify_market_opportunities(self, evolution: TechEvolution) -> list[str]:
        """识别市场机会"""
        opportunities = []

        try:
            # 基于技术演进识别机会
            opportunities.extend(
                ["技术标准化带来的市场机会", "跨行业应用扩展", "新兴市场渗透", "技术集成服务"]
            )

            # 基于未来趋势识别机会
            for trend in evolution.future_trends:
                opportunities.append(f"{trend}相关市场机会")

            # 去重
            opportunities = list(set(opportunities))

        except Exception as e:
            self.logger.warning(f"机会识别失败: {e}")

        return opportunities[:8]  # 限制数量

    async def _identify_risk_factors(self, evolution: TechEvolution) -> list[str]:
        """识别风险因素"""
        risks = []

        try:
            # 技术风险
            risks.extend(["技术成熟度不足", "替代技术威胁", "研发周期延长", "成本控制挑战"])

            # 市场风险
            risks.extend(["市场需求变化", "竞争加剧", "监管政策变化", "知识产权风险"])

            # 实施风险
            risks.extend(["人才短缺", "资金压力", "技术集成难度", "用户接受度"])

        except Exception as e:
            self.logger.warning(f"风险识别失败: {e}")

        return risks[:10]  # 限制数量

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()

    async def close(self):
        """关闭现有技术分析引擎"""
        self.analysis_cache.clear()
        self.cluster_cache.clear()
        self._initialized = False
        self.logger.info("✅ PriorArtAnalyzer 已关闭")


# 便捷函数
async def get_prior_art_analyzer() -> PriorArtAnalyzer:
    """获取现有技术分析引擎实例"""
    analyzer = PriorArtAnalyzer()
    await analyzer.initialize()
    return analyzer


async def analyze_technology_landscape(technology_field: str, years: int = 10) -> TechEvolution:
    """便捷函数:分析技术图谱"""
    analyzer = await get_prior_art_analyzer()

    end_time = datetime.now()
    start_time = end_time - timedelta(days=years * 365)

    return await analyzer.analyze_technology_evolution(technology_field, (start_time, end_time))


if __name__ == "__main__":
    print("现有技术图谱分析引擎模块已加载")
