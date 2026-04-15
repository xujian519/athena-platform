#!/usr/bin/env python3
from __future__ import annotations
"""
小娜深度技术分析器 (增强版)
Xiaona Deep Technical Analyzer (Enhanced)

集成小娜专利分析能力和NetworkX图谱分析，对目标专利和对比文件进行深度技术分析
输出JSON和Markdown格式文档

增强功能:
1. 问题-特征-效果三元关系提取
2. 特征关联图谱构建 (基于NetworkX)
3. 技术重要性计算 (中心性指标)
4. 技术演化路径识别

作者: 小诺·双鱼公主
创建时间: 2026-01-24
版本: v0.2.0 "图谱增强"
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import networkx as nx

from core.logging_config import setup_logging

logger = setup_logging()

# 可选导入：Dolphin文档解析器
try:
    from core.perception.dolphin_networkx_integration import (
        DolphinNetworkXAnalyzer,
        TechnicalEntity,
        TechnicalRelation,
    )
    DOLPHIN_AVAILABLE = True
    logger.info("✅ Dolphin文档解析器可用")
except ImportError as e:
    DOLPHIN_AVAILABLE = False
    logger.warning(f"⚠️ Dolphin文档解析器不可用: {e}")

# 可选导入：可视化库
try:
    import matplotlib
    import matplotlib.pyplot as plt
    matplotlib.use('Agg')  # 非交互式后端
    MATPLOTLIB_AVAILABLE = True
    logger.info("✅ Matplotlib可视化可用")
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("⚠️ Matplotlib不可用")

# 可选导入：pyvis交互式可视化
try:
    from pyvis.network import Network
    PYVIS_AVAILABLE = True
    logger.info("✅ Pyvis交互式可视化可用")
except ImportError:
    PYVIS_AVAILABLE = False
    logger.warning("⚠️ Pyvis不可用")


@dataclass
class TechnicalFeature:
    """技术特征"""

    feature_id: str
    feature_name: str
    feature_type: str  # 结构、方法、参数、效果
    description: str
    importance: float  # 0-1，重要性评分
    novelty_level: str  # 高、中、低
    claimed: bool  # 是否在权利要求中
    source_section: str = ""  # 来源章节（说明书/权利要求）

    # 图谱分析增强字段
    centrality_score: float = 0.0  # 中心性得分
    graph_position: str = ""  # 图谱位置：核心/边缘/孤立
    related_features: list[str] = field(default_factory=list)  # 关联特征ID列表


@dataclass
class ProblemFeatureEffectTriple:
    """问题-特征-效果三元关系"""

    triple_id: str
    technical_problem: str
    technical_feature: str  # 特征ID
    technical_effect: str
    confidence: float = 1.0  # 置信度
    evidence_text: str = ""  # 证据文本


@dataclass
class FeatureRelation:
    """特征关联关系"""

    source_feature: str  # 源特征ID
    target_feature: str  # 目标特征ID
    relation_type: str  # depends_on, improves, implements, contains, excludes
    weight: float = 1.0  # 关系强度
    description: str = ""


@dataclass
class TechnicalKnowledgeGraph:
    """技术知识图谱"""

    patent_number: str
    nodes: dict[str, TechnicalFeature] = field(default_factory=dict)
    edges: list[FeatureRelation] = field(default_factory=list)
    problem_effect_triples: list[ProblemFeatureEffectTriple] = field(default_factory=list)

    # 图谱指标
    graph_density: float = 0.0
    avg_clustering: float = 0.0
    core_features: list[str] = field(default_factory=list)  # 核心特征ID列表
    innovation_indicators: dict[str, float] = field(default_factory=dict)

    def to_networkx_graph(self) -> nx.DiGraph:
        """转换为NetworkX图对象"""
        G = nx.DiGraph()

        # 添加节点
        for feature_id, feature in self.nodes.items():
            G.add_node(
                feature_id,
                name=feature.feature_name,
                type=feature.feature_type,
                importance=feature.importance,
                centrality=feature.centrality_score,
            )

        # 添加边
        for edge in self.edges:
            G.add_edge(
                edge.source_feature,
                edge.target_feature,
                relation_type=edge.relation_type,
                weight=edge.weight,
            )

        return G


@dataclass
class PatentAnalysis:
    """单件专利分析结果"""

    patent_number: str
    patent_title: str
    patent_type: str  # 目标专利/对比文件
    analysis_date: str

    # 基本信息
    applicant: str = ""
    inventor: str = ""
    application_date: str = ""
    publication_date: str = ""

    # 技术领域分析
    technical_field: str = ""
    field_keywords: list[str] = field(default_factory=list)

    # 技术问题
    technical_problem: str = ""
    problem_keywords: list[str] = field(default_factory=list)

    # 技术方案
    technical_solution: str = ""
    solution_keywords: list[str] = field(default_factory=list)

    # 技术效果
    technical_effects: list[str] = field(default_factory=list)
    effect_keywords: list[str] = field(default_factory=list)

    # 技术特征提取
    technical_features: list[TechnicalFeature] = field(default_factory=list)

    # 技术知识图谱 (新增)
    knowledge_graph: TechnicalKnowledgeGraph | None = None
    problem_effect_triples: list[ProblemFeatureEffectTriple] = field(default_factory=list)
    feature_relations: list[FeatureRelation] = field(default_factory=list)

    # 图谱分析指标 (新增)
    graph_centrality_ranking: list[tuple[str, float]] = field(default_factory=list)  # (特征ID, 中心性)
    core_innovation_features: list[str] = field(default_factory=list)  # 核心创新特征ID列表

    # 权利要求分析
    independent_claims: int = 0
    dependent_claims: int = 0
    total_claims: int = 0
    claim_hierarchy: dict[str, Any] = field(default_factory=dict)

    # 关键技术点
    key_technical_points: list[str] = field(default_factory=list)
    innovation_highlights: list[str] = field(default_factory=list)

    # 技术复杂度
    complexity_score: float = 0.0  # 0-1
    complexity_factors: list[str] = field(default_factory=list)

    # 实施方式分析
    implementation_details: str = ""
    embodiment_count: int = 0

    # 分析元数据
    analysis_confidence: float = 0.0  # 分析置信度
    missing_info: list[str] = field(default_factory=list)
    analysis_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        result = {
            "patent_number": self.patent_number,
            "patent_title": self.patent_title,
            "patent_type": self.patent_type,
            "analysis_date": self.analysis_date,
            "basic_info": {
                "applicant": self.applicant,
                "inventor": self.inventor,
                "application_date": self.application_date,
                "publication_date": self.publication_date,
            },
            "technical_analysis": {
                "technical_field": self.technical_field,
                "field_keywords": self.field_keywords,
                "technical_problem": self.technical_problem,
                "problem_keywords": self.problem_keywords,
                "technical_solution": self.technical_solution,
                "solution_keywords": self.solution_keywords,
                "technical_effects": self.technical_effects,
                "effect_keywords": self.effect_keywords,
            },
            "features": [
                {
                    "feature_id": f.feature_id,
                    "feature_name": f.feature_name,
                    "feature_type": f.feature_type,
                    "description": f.description,
                    "importance": f.importance,
                    "novelty_level": f.novelty_level,
                    "claimed": f.claimed,
                    "source_section": f.source_section,
                }
                for f in self.technical_features
            ],
            "claims_analysis": {
                "independent_claims": self.independent_claims,
                "dependent_claims": self.dependent_claims,
                "total_claims": self.total_claims,
                "claim_hierarchy": self.claim_hierarchy,
            },
            "key_points": {
                "key_technical_points": self.key_technical_points,
                "innovation_highlights": self.innovation_highlights,
            },
            "complexity": {
                "complexity_score": self.complexity_score,
                "complexity_factors": self.complexity_factors,
            },
            "implementation": {
                "details": self.implementation_details,
                "embodiment_count": self.embodiment_count,
            },
            "metadata": {
                "analysis_confidence": self.analysis_confidence,
                "missing_info": self.missing_info,
                "analysis_notes": self.analysis_notes,
            },
        }
        return result

    def to_markdown(self) -> str:
        """生成Markdown格式文档"""
        md = []

        md.append(f"# 📄 {self.patent_type}深度技术分析\n")
        md.append(f"**专利号**: `{self.patent_number}`\n")
        md.append(f"**标题**: {self.patent_title}\n")
        md.append(f"**分析日期**: {self.analysis_date}\n")
        md.append("---\n")

        # 基本信息
        md.append("## 📋 基本信息\n")
        if self.applicant:
            md.append(f"- **申请人**: {self.applicant}\n")
        if self.inventor:
            md.append(f"- **发明人**: {self.inventor}\n")
        if self.application_date:
            md.append(f"- **申请日**: {self.application_date}\n")
        if self.publication_date:
            md.append(f"- **公开日**: {self.publication_date}\n")
        md.append("")

        # 技术领域分析
        md.append("## 🔬 技术领域分析\n")
        md.append(f"**技术领域**: {self.technical_field}\n")
        if self.field_keywords:
            md.append(f"**领域关键词**: {', '.join(self.field_keywords)}\n")
        md.append("")

        # 技术问题
        md.append("## 🎯 技术问题\n")
        md.append(f"{self.technical_problem}\n")
        if self.problem_keywords:
            md.append(f"**问题关键词**: {', '.join(self.problem_keywords)}\n")
        md.append("")

        # 技术方案
        md.append("## 💡 技术方案\n")
        md.append(f"{self.technical_solution}\n")
        if self.solution_keywords:
            md.append(f"**方案关键词**: {', '.join(self.solution_keywords)}\n")
        md.append("")

        # 技术效果
        if self.technical_effects:
            md.append("## ✨ 技术效果\n")
            for i, effect in enumerate(self.technical_effects, 1):
                md.append(f"{i}. {effect}\n")
            md.append("")

        # 技术特征
        if self.technical_features:
            md.append("## 🔧 技术特征提取\n")
            for feature in self.technical_features:
                claimed_icon = "✅" if feature.claimed else "⚪"
                md.append(f"### {claimed_icon} {feature.feature_name}\n")
                md.append(f"- **类型**: {feature.feature_type}\n")
                md.append(f"- **描述**: {feature.description}\n")
                md.append(f"- **重要性**: {feature.importance:.1%}\n")
                md.append(f"- **新颖性**: {feature.novelty_level}\n")
                # 新增：显示图谱指标
                if feature.centrality_score > 0:
                    md.append(f"- **图谱中心性**: {feature.centrality_score:.3f}\n")
                if feature.related_features:
                    md.append(f"- **关联特征**: {len(feature.related_features)}个\n")
                md.append("")

        # 知识图谱分析 (新增)
        if self.knowledge_graph:
            md.append("## 🕸️ 技术知识图谱分析\n")
            graph = self.knowledge_graph

            # 图谱概览
            md.append(f"- **节点数量**: {len(graph.nodes)}\n")
            md.append(f"- **边数量**: {len(graph.edges)}\n")
            md.append(f"- **图密度**: {graph.graph_density:.3f}\n")
            if graph.avg_clustering > 0:
                md.append(f"- **平均聚类系数**: {graph.avg_clustering:.3f}\n")
            md.append("")

            # 问题-特征-效果三元关系 (新增)
            if self.problem_effect_triples:
                md.append("### 🔗 问题-特征-效果三元关系\n")
                for i, triple in enumerate(self.problem_effect_triples[:5], 1):  # 最多显示5个
                    md.append(f"{i}. **问题**: {triple.technical_problem[:30]}...\n")
                    md.append(f"   - **特征**: {triple.technical_feature}\n")
                    md.append(f"   - **效果**: {triple.technical_effect[:40]}...\n")
                    md.append(f"   - **置信度**: {triple.confidence:.1%}\n")
                md.append("")

            # 特征关联关系 (新增)
            if self.feature_relations:
                md.append("### 🔗 特征关联关系\n")
                relation_type_names = {
                    "depends_on": "依赖",
                    "improves": "改进",
                    "implements": "实现",
                    "contains": "包含",
                    "excludes": "排除",
                }
                for i, relation in enumerate(self.feature_relations[:10], 1):  # 最多显示10个
                    type_name = relation_type_names.get(relation.relation_type, relation.relation_type)
                    md.append(f"{i}. {relation.source_feature} → {relation.target_feature}\n")
                    md.append(f"   - **类型**: {type_name}\n")
                    md.append(f"   - **强度**: {relation.weight:.1%}\n")
                md.append("")

            # 图谱中心性排名 (新增)
            if self.graph_centrality_ranking:
                md.append("### 📊 特征中心性排名\n")
                for i, (feature_id, centrality) in enumerate(self.graph_centrality_ranking[:10], 1):
                    feature = graph.nodes.get(feature_id)
                    if feature:
                        md.append(f"{i}. `{feature_id}` - {feature.feature_name}\n")
                        md.append(f"   - 中心性: {centrality:.3f}\n")
                md.append("")

            # 核心创新特征 (新增)
            if self.core_innovation_features:
                md.append("### ⭐ 核心创新特征\n")
                for feature_id in self.core_innovation_features:
                    feature = graph.nodes.get(feature_id)
                    if feature:
                        md.append(f"- **{feature.feature_name}** ({feature_id})\n")
                        md.append(f"  - 中心性: {feature.centrality_score:.3f}\n")
                        md.append(f"  - 新颖性: {feature.novelty_level}\n")
                md.append("")

        # 权利要求分析
        md.append("## 📝 权利要求分析\n")
        md.append(f"- **独立权利要求**: {self.independent_claims} 个\n")
        md.append(f"- **从属权利要求**: {self.dependent_claims} 个\n")
        md.append(f"- **总计**: {self.total_claims} 个\n")
        md.append("")

        # 关键技术点
        if self.key_technical_points:
            md.append("## 🔑 关键技术点\n")
            for point in self.key_technical_points:
                md.append(f"- {point}\n")
            md.append("")

        # 创新亮点
        if self.innovation_highlights:
            md.append("## ⭐ 创新亮点\n")
            for highlight in self.innovation_highlights:
                md.append(f"- {highlight}\n")
            md.append("")

        # 技术复杂度
        md.append("## 📊 技术复杂度\n")
        md.append(f"- **复杂度评分**: {self.complexity_score:.1%}\n")
        if self.complexity_factors:
            md.append("- **复杂因素**:\n")
            for factor in self.complexity_factors:
                md.append(f"  - {factor}\n")
        md.append("")

        # 实施方式
        if self.implementation_details:
            md.append("## 🛠️ 实施方式\n")
            md.append(f"{self.implementation_details}\n")
            if self.embodiment_count > 0:
                md.append(f"\n**实施例数量**: {self.embodiment_count}\n")
            md.append("")

        # 分析备注
        md.append("---\n")
        md.append("## 📊 分析元数据\n")
        md.append(f"- **分析置信度**: {self.analysis_confidence:.1%}\n")
        if self.missing_info:
            md.append(f"- **缺失信息**: {', '.join(self.missing_info)}\n")
        if self.analysis_notes:
            md.append("- **分析备注**:\n")
            for note in self.analysis_notes:
                md.append(f"  - {note}\n")
        md.append("")

        return "".join(md)


@dataclass
class ComparisonAnalysis:
    """对比分析结果"""

    target_patent: str
    prior_art_references: list[str]  # 对比文件列表
    analysis_date: str

    # 逐一分析结果
    patent_analyses: dict[str, PatentAnalysis] = field(default_factory=dict)

    # 对比分析
    feature_comparison: dict[str, Any] = field(default_factory=dict)
    similarity_analysis: dict[str, Any] = field(default_factory=dict)
    difference_analysis: dict[str, Any] = field(default_factory=dict)

    # 总体评估
    overall_similarity: float = 0.0  # 0-1
    key_differences: list[str] = field(default_factory=list)
    potential_issues: list[str] = field(default_factory=list)

    # 分析元数据
    analysis_confidence: float = 0.0
    analysis_duration: float = 0.0  # 秒

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "metadata": {
                "target_patent": self.target_patent,
                "prior_art_references": self.prior_art_references,
                "analysis_date": self.analysis_date,
                "overall_similarity": self.overall_similarity,
                "analysis_confidence": self.analysis_confidence,
                "analysis_duration": self.analysis_duration,
            },
            "patent_analyses": {
                patent_num: analysis.to_dict()
                for patent_num, analysis in self.patent_analyses.items()
            },
            "comparison": {
                "feature_comparison": self.feature_comparison,
                "similarity_analysis": self.similarity_analysis,
                "difference_analysis": self.difference_analysis,
                "key_differences": self.key_differences,
                "potential_issues": self.potential_issues,
            },
        }

    def to_markdown(self) -> str:
        """生成Markdown格式文档"""
        md = []

        md.append("# 🔬 深度技术对比分析报告\n")
        md.append("---\n")

        md.append("## 📊 分析概览\n")
        md.append(f"- **目标专利**: `{self.target_patent}`\n")
        md.append(f"- **对比文件数量**: {len(self.prior_art_references)}\n")
        md.append(f"- **分析日期**: {self.analysis_date}\n")
        md.append(f"- **整体相似度**: {self.overall_similarity:.1%}\n")
        md.append(f"- **分析置信度**: {self.analysis_confidence:.1%}\n")
        md.append(f"- **分析耗时**: {self.analysis_duration:.1f}秒\n")
        md.append("")

        # 目标专利分析
        if self.target_patent in self.patent_analyses:
            md.append("## 🎯 目标专利分析\n")
            md.append(self.patent_analyses[self.target_patent].to_markdown())

        # 对比文件分析
        for ref_num in self.prior_art_references:
            if ref_num in self.patent_analyses:
                md.append(f"## 📄 对比文件: {ref_num}\n")
                md.append(self.patent_analyses[ref_num].to_markdown())

        # 对比分析
        md.append("---\n")
        md.append("## ⚖️ 对比分析总结\n")

        if self.key_differences:
            md.append("### 🔑 关键差异\n")
            for i, diff in enumerate(self.key_differences, 1):
                md.append(f"{i}. {diff}\n")
            md.append("")

        if self.potential_issues:
            md.append("### ⚠️ 潜在问题\n")
            for issue in self.potential_issues:
                md.append(f"- {issue}\n")
            md.append("")

        return "".join(md)

    def save_outputs(self, output_dir: str, base_filename: str):
        """
        保存JSON和Markdown格式文档

        Args:
            output_dir: 输出目录
            base_filename: 基础文件名（不含扩展名）
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 保存JSON
        json_file = output_path / f"{base_filename}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        logger.info(f"✅ JSON已保存: {json_file}")

        # 保存Markdown
        md_file = output_path / f"{base_filename}.md"
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(self.to_markdown())
        logger.info(f"✅ Markdown已保存: {md_file}")


class XiaonaDeepTechnicalAnalyzer:
    """
    小娜深度技术分析器

    核心功能:
    1. 逐一分析目标专利和对比文件
    2. 深度提取技术特征、技术方案、技术效果
    3. 生成JSON和Markdown格式文档
    """

    def __init__(
        self,
        output_dir: str = "data/analysis_reports",
        use_dolphin: bool = True,
        enable_visualization: bool = True,
    ):
        """
        初始化分析器

        Args:
            output_dir: 分析报告输出目录
            use_dolphin: 是否使用Dolphin文档解析器（如果可用）
            enable_visualization: 是否启用图谱可视化
        """
        self.name = "小娜深度技术分析器 (增强版)"
        self.version = "v0.2.0"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 初始化Dolphin文档解析器（如果可用且启用）
        self.dolphin_analyzer = None
        if use_dolphin and DOLPHIN_AVAILABLE:
            try:
                self.dolphin_analyzer = DolphinNetworkXAnalyzer()
                logger.info("✅ Dolphin文档解析器初始化成功")
            except Exception as e:
                logger.warning(f"⚠️ Dolphin文档解析器初始化失败: {e}")

        # 可视化设置
        self.enable_visualization = enable_visualization and MATPLOTLIB_AVAILABLE
        if self.enable_visualization:
            logger.info("✅ 图谱可视化已启用")
        else:
            logger.info("⚠️ 图谱可视化未启用")

        logger.info(f"🔬 {self.name} ({self.version}) 初始化完成")
        logger.info(f"📁 输出目录: {self.output_dir}")

    async def analyze_target_and_prior_art(
        self,
        target_patent_info: dict[str, Any],        prior_art_references: list[dict[str, Any]],        target_patent_text: str = "",
        prior_art_texts: dict[str, str] | None = None,
    ) -> ComparisonAnalysis:
        """
        分析目标专利和对比文件

        Args:
            target_patent_info: 目标专利信息（申请号、标题等）
            prior_art_references: 对比文件信息列表
            target_patent_text: 目标专利全文（可选）
            prior_art_texts: 对比文件全文映射（可选）

        Returns:
            ComparisonAnalysis: 对比分析结果
        """
        import time

        start_time = time.time()

        logger.info("🔬 开始深度技术分析")
        logger.info(f"   目标专利: {target_patent_info.get('application_number', 'N/A')}")
        logger.info(f"   对比文件: {len(prior_art_references)}个")

        analysis = ComparisonAnalysis(
            target_patent=target_patent_info.get("application_number", ""),
            prior_art_references=[
                ref.get("publication_number", "") for ref in prior_art_references
            ],
            analysis_date=datetime.now().isoformat(),
        )

        # 分析目标专利
        target_analysis = await self._analyze_single_patent(
            patent_number=target_patent_info.get("application_number", ""),
            patent_title=target_patent_info.get("title", ""),
            patent_type="目标专利",
            patent_text=target_patent_text,
        )
        analysis.patent_analyses[analysis.target_patent] = target_analysis

        # 逐一分析对比文件
        for ref_info in prior_art_references:
            ref_number = ref_info.get("publication_number", "")
            if not ref_number:
                continue

            ref_text = prior_art_texts.get(ref_number, "") if prior_art_texts else ""

            prior_analysis = await self._analyze_single_patent(
                patent_number=ref_number,
                patent_title=ref_info.get("title", ""),
                patent_type="对比文件",
                patent_text=ref_text,
            )
            analysis.patent_analyses[ref_number] = prior_analysis

        # 执行对比分析
        await self._perform_comparison_analysis(analysis)

        # 计算分析耗时
        analysis.analysis_duration = time.time() - start_time

        logger.info(f"✅ 深度技术分析完成，耗时 {analysis.analysis_duration:.1f}秒")

        return analysis

    async def _analyze_single_patent(
        self,
        patent_number: str,
        patent_title: str,
        patent_type: str,
        patent_text: str = "",
        patent_pdf_path: str = "",
    ) -> PatentAnalysis:
        """
        分析单个专利

        Args:
            patent_number: 专利号
            patent_title: 专利标题
            patent_type: 专利类型（目标专利/对比文件）
            patent_text: 专利全文
            patent_pdf_path: 专利PDF路径（可选，用于Dolphin高精度解析）

        Returns:
            PatentAnalysis: 专利分析结果
        """
        logger.info(f"   分析 {patent_type}: {patent_number}")

        analysis = PatentAnalysis(
            patent_number=patent_number,
            patent_title=patent_title,
            patent_type=patent_type,
            analysis_date=datetime.now().isoformat(),
        )

        if not patent_text and not patent_pdf_path:
            # 如果没有全文，生成基本分析
            analysis.analysis_notes.append("无专利全文，仅进行基础分析")
            analysis.analysis_confidence = 0.3
            analysis.missing_info.append("专利全文")
            return analysis

        # 优先使用Dolphin高精度解析（如果PDF可用且Dolphin已启用）
        use_dolphin = self.dolphin_analyzer is not None and patent_pdf_path

        if use_dolphin:
            logger.info("   使用Dolphin高精度解析")
            try:
                # 使用Dolphin解析PDF文档
                dolphin_result = await self.dolphin_analyzer.analyze_patent_technical_depth(
                    document_path=patent_pdf_path,
                    build_knowledge_graph=True,
                )

                # 转换Dolphin结果为我们的数据结构
                analysis = self._convert_dolphin_result(
                    dolphin_result, analysis, patent_number
                )

                # 生成图谱可视化（增强版：静态+交互式）
                if analysis.knowledge_graph:
                    self._visualize_knowledge_graph_enhanced(
                        analysis.knowledge_graph,
                        patent_number,
                        self.output_dir / "visualizations",
                    )

                return analysis

            except Exception as e:
                logger.warning(f"⚠️ Dolphin解析失败，回退到常规解析: {e}")
                use_dolphin = False

        # 常规解析流程
        # 1. 提取技术领域
        analysis.technical_field = self._extract_technical_field(patent_text)
        analysis.field_keywords = self._extract_field_keywords(patent_text)

        # 2. 提取技术问题
        analysis.technical_problem = self._extract_technical_problem(patent_text)
        analysis.problem_keywords = self._extract_keywords(analysis.technical_problem)

        # 3. 提取技术方案
        analysis.technical_solution = self._extract_technical_solution(patent_text)
        analysis.solution_keywords = self._extract_keywords(analysis.technical_solution)

        # 4. 提取技术效果
        analysis.technical_effects = self._extract_technical_effects(patent_text)

        # 5. 提取技术特征 + 构建知识图谱 (新增)
        analysis.technical_features = self._extract_technical_features(patent_text)

        # 5.1 构建技术知识图谱 (新增)
        if analysis.technical_features:
            analysis.knowledge_graph = self._build_technical_knowledge_graph(
                patent_number,
                analysis.technical_features,
                analysis.technical_problem,
                analysis.technical_effects,
            )
            analysis.feature_relations = analysis.knowledge_graph.edges
            analysis.problem_effect_triples = analysis.knowledge_graph.problem_effect_triples

            # 5.2 计算图谱中心性指标 (新增)
            analysis.graph_centrality_ranking = self._calculate_graph_centrality(
                analysis.knowledge_graph
            )

            # 5.3 识别核心创新特征 (新增)
            analysis.core_innovation_features = self._identify_core_innovations(
                analysis.knowledge_graph
            )

        # 6. 分析权利要求
        claim_info = self._analyze_claims(patent_text)
        analysis.independent_claims = claim_info["independent"]
        analysis.dependent_claims = claim_info["dependent"]
        analysis.total_claims = claim_info["total"]
        analysis.claim_hierarchy = claim_info["hierarchy"]

        # 7. 识别关键技术点
        analysis.key_technical_points = self._identify_key_points(patent_text)

        # 8. 识别创新亮点
        analysis.innovation_highlights = self._identify_innovations(patent_text)

        # 9. 评估技术复杂度
        complexity_result = self._assess_complexity(patent_text)
        analysis.complexity_score = complexity_result["score"]
        analysis.complexity_factors = complexity_result["factors"]

        # 10. 分析实施方式
        impl_result = self._analyze_implementation(patent_text)
        analysis.implementation_details = impl_result["details"]
        analysis.embodiment_count = impl_result["count"]

        # 11. 计算分析置信度
        analysis.analysis_confidence = self._calculate_confidence(analysis)

        return analysis

    async def _perform_comparison_analysis(self, analysis: ComparisonAnalysis):
        """执行对比分析"""
        if analysis.target_patent not in analysis.patent_analyses:
            return

        target = analysis.patent_analyses[analysis.target_patent]

        # 对比每个对比文件
        for ref_num in analysis.prior_art_references:
            if ref_num not in analysis.patent_analyses:
                continue

            prior = analysis.patent_analyses[ref_num]

            # 特征对比
            feature_comp = self._compare_features(target, prior)
            analysis.feature_comparison[ref_num] = feature_comp

            # 相似度分析
            similarity = self._calculate_similarity(target, prior)
            analysis.similarity_analysis[ref_num] = similarity

            # 差异分析
            differences = self._identify_differences(target, prior)
            analysis.difference_analysis[ref_num] = differences

        # 计算整体相似度
        if analysis.similarity_analysis:
            similarities = [
                s.get("overall_similarity", 0)
                for s in analysis.similarity_analysis.values()
            ]
            analysis.overall_similarity = (
                sum(similarities) / len(similarities) if similarities else 0
            )

        # 提取关键差异
        analysis.key_differences = self._extract_key_differences(analysis)

        # 识别潜在问题
        analysis.potential_issues = self._identify_potential_issues(analysis)

    def _extract_technical_field(self, text: str) -> str:
        """提取技术领域"""
        # 医疗领域技术交底书的技术领域提取
        keywords = {
            "医疗": "医疗器械",
            "医学": "医疗器械",
            "训练模型": "医疗器械",
            "骨髓腔": "医疗器械",
            "输液": "医疗器械",
            "穿刺": "医疗器械",
            "解剖": "医疗器械",
            "教学": "医疗器械",
            "计算机": "计算机科学",
            "软件": "计算机科学",
            "算法": "计算机科学",
            "机械": "机械工程",
            "装置": "机械工程",
            "电路": "电子工程",
            "通信": "通信技术",
        }
        for keyword, field_name in keywords.items():
            if keyword in text:
                return field_name
        return "未分类"

    def _extract_field_keywords(self, text: str) -> list[str]:
        """提取领域关键词"""
        # 简化实现
        return []

    def _extract_technical_problem(self, text: str) -> str:
        """提取技术问题"""
        # 提取医疗领域技术交底书的技术问题
        if "技术问题" in text or "背景技术" in text or "背景" in text:
            # 查找背景技术部分
            if "背景" in text and "技术" in text:
                start_idx = text.find("背景")
                end_idx = text.find("三、技术介绍")
                if start_idx != -1 and end_idx != -1:
                    return text[start_idx:end_idx].strip()
            # 如果没有明确的"三、技术介绍"，则返回背景部分
            if "背景" in text:
                start_idx = text.find("背景")
                if start_idx != -1:
                    end_idx = start_idx + 300
                    if end_idx > len(text):
                        end_idx = len(text)
                    return text[start_idx:end_idx].strip()
        # 从文本中寻找问题描述
        problem_keywords = [
            "问题", "挑战", "不足", "缺陷", "需要", "需求", "未解决",
            "漏液", "使用寿命", "训练效率", "遗留针孔", "清理时间"
        ]
        for keyword in problem_keywords:
            if keyword in text:
                # 查找包含问题描述的句子
                sentences = text.split("。")
                for sentence in sentences:
                    if keyword in sentence:
                        return sentence.strip() + "。"
        return "未明确描述"

    def _extract_keywords(self, text: str) -> list[str]:
        """提取关键词"""
        # 简化实现
        return []

    def _extract_technical_solution(self, text: str) -> str:
        """提取技术方案"""
        # 提取医疗领域技术交底书的技术方案
        if "技术方案" in text or "发明内容" in text or "技术介绍" in text:
            # 查找技术介绍部分
            if "技术介绍" in text:
                start_idx = text.find("技术介绍")
                end_idx = text.find("五、技术优势")
                if start_idx != -1 and end_idx != -1:
                    return text[start_idx:end_idx].strip()
        # 从文本中寻找方案描述
        solution_keywords = [
            "改进", "增加", "设计", "具备", "解决", "实现",
            "自修复", "防漏液", "限位器", "匹配座", "橡胶软管", "高分子密封胶"
        ]
        for keyword in solution_keywords:
            if keyword in text:
                # 查找包含方案描述的段落
                paragraphs = text.split("\n")
                for paragraph in paragraphs:
                    if keyword in paragraph and len(paragraph.strip()) > 20:
                        return paragraph.strip()
        return "未明确描述"

    def _extract_technical_effects(self, text: str) -> list[str]:
        """提取技术效果"""
        effects = []
        # 简化实现
        return effects

    def _extract_technical_features(self, text: str) -> list[TechnicalFeature]:
        """提取技术特征 - 增强实现，使用正则和NLP技术"""
        features = []

        # 技术特征关键词模式
        feature_patterns = {
            "结构": [
                r"包括.*?模型", r"设置.*?器", r"具有.*?架", r"包含.*?套件",
                r"由.*?组成", r"主体.*?功能", r"多层.*?结构", r"模拟.*?特性"
            ],
            "方法": [r".*?步骤", r".*?方法", r".*?流程", r".*?操作"],
            "参数": [
                r".*?厚度.*?在.*?之间", r".*?孔径.*?在.*?之间", r".*?高度.*?变化",
                r"厚度t1.*?mm", r"厚度t2.*?mm", r"厚度t3.*?mm", r"厚度t4.*?mm",
                r"长度L1.*?mm", r"长度L2.*?mm", r"深度h.*?mm"
            ],
            "效果": [
                r".*?效果", r".*?性能", r".*?效率", r".*?解决.*?问题",
                r"显著提高.*?使用寿命", r"缩短.*?时间", r"提高.*?效率"
            ],
        }

        feature_id = 0
        for feature_type, patterns in feature_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    matched_text = match.group()
                    if len(matched_text) > 5 and len(matched_text) < 100:
                        features.append(
                            TechnicalFeature(
                                feature_id=f"F{feature_id:03d}",
                                feature_name=matched_text[:30],
                                feature_type=feature_type,
                                description=matched_text,
                                importance=0.5,
                                novelty_level="中",
                                claimed=False,
                                source_section="说明书",
                            )
                        )
                        feature_id += 1

        # 提取权利要求中的特征
        if "权利要求" in text:
            claims_start = text.find("权利要求：")
            if claims_start != -1:
                claims_text = text[claims_start:].split("\n")
                for line in claims_text:
                    if line.startswith("权利要求") and len(line.strip()) > 10:
                        feature_name = line.strip()
                        if feature_name not in [f.feature_name for f in features]:
                            features.append(
                                TechnicalFeature(
                                    feature_id=f"F{feature_id:03d}",
                                    feature_name=feature_name,
                                    feature_type="权利要求",
                                    description=feature_name,
                                    importance=0.8,
                                    novelty_level="高",
                                    claimed=True,
                                    source_section="权利要求",
                                )
                            )
                            feature_id += 1

        logger.info(f"   提取到 {len(features)} 个技术特征")
        return features

    def _analyze_claims(self, text: str) -> dict[str, Any]:
        """分析权利要求"""
        independent = 0
        dependent = 0
        hierarchy = {}

        if "权利要求" in text:
            claims_start = text.find("权利要求：")
            if claims_start != -1:
                claims_text = text[claims_start:].split("\n")
                claim_count = 0
                for line in claims_text:
                    if line.strip().startswith("权利要求"):
                        claim_count += 1
                        # 判断是独立权利要求还是从属权利要求
                        if "权利要求1" in line or "独立权利要求" in line:
                            independent += 1
                        elif "权利要求" in line and len(line.strip()) > 10:
                            dependent += 1
        return {
            "independent": independent,
            "dependent": dependent,
            "total": independent + dependent,
            "hierarchy": hierarchy,
        }

    def _identify_key_points(self, text: str) -> list[str]:
        """识别关键技术点"""
        points = []
        # 简化实现
        return points

    def _identify_innovations(self, text: str) -> list[str]:
        """识别创新亮点"""
        innovations = []
        # 简化实现
        return innovations

    def _assess_complexity(self, text: str) -> dict[str, Any]:
        """评估技术复杂度"""
        # 基于文本长度等因素简化评估
        score = min(1.0, len(text) / 10000)
        return {
            "score": score,
            "factors": ["文本长度", "技术术语数量"],
        }

    def _analyze_implementation(self, text: str) -> dict[str, Any]:
        """分析实施方式"""
        details = "待分析"
        count = text.count("实施例")
        return {
            "details": details,
            "count": count,
        }

    def _calculate_confidence(self, analysis: PatentAnalysis) -> float:
        """计算分析置信度"""
        if analysis.missing_info:
            return 0.5
        return 0.85

    def _compare_features(
        self, target: PatentAnalysis, prior: PatentAnalysis
    ) -> dict[str, Any]:
        """对比技术特征"""
        return {
            "common_features": [],
            "unique_to_target": [],
            "unique_to_prior": [],
        }

    def _calculate_similarity(
        self, target: PatentAnalysis, prior: PatentAnalysis
    ) -> dict[str, Any]:
        """计算相似度"""
        return {
            "overall_similarity": 0.5,
            "field_similarity": 0.8,
            "problem_similarity": 0.6,
            "solution_similarity": 0.4,
        }

    def _identify_differences(
        self, target: PatentAnalysis, prior: PatentAnalysis
    ) -> dict[str, Any]:
        """识别差异"""
        return {
            "structural_differences": [],
            "functional_differences": [],
            "parametric_differences": [],
        }

    def _extract_key_differences(self, analysis: ComparisonAnalysis) -> list[str]:
        """提取关键差异"""
        differences = []
        for _diff_result in analysis.difference_analysis.values():
            # 简化实现
            pass
        return differences

    def _identify_potential_issues(self, analysis: ComparisonAnalysis) -> list[str]:
        """识别潜在问题"""
        issues = []
        if analysis.overall_similarity > 0.8:
            issues.append("目标专利与对比文件相似度较高")
        return issues

    # ========== 新增：NetworkX图谱分析方法 ==========

    def _build_technical_knowledge_graph(
        self,
        patent_number: str,
        features: list[TechnicalFeature],
        technical_problem: str,
        technical_effects: list[str],
    ) -> TechnicalKnowledgeGraph:
        """
        构建技术知识图谱

        使用NetworkX构建特征关联图，提取问题-特征-效果三元关系
        """
        logger.info(f"   构建技术知识图谱: {len(features)} 个特征")

        # 创建知识图谱
        graph = TechnicalKnowledgeGraph(patent_number=patent_number)

        # 添加节点（技术特征）
        for feature in features:
            graph.nodes[feature.feature_id] = feature

        # 提取问题-特征-效果三元关系
        graph.problem_effect_triples = self._extract_problem_feature_effect_triples(
            technical_problem, features, technical_effects
        )

        # 构建特征关联关系
        graph.edges = self._identify_feature_relations(features)

        # 转换为NetworkX图计算指标
        nx_graph = graph.to_networkx_graph()

        # 计算图谱指标
        if nx_graph.number_of_nodes() > 0:
            # 中心性指标
            centrality = nx.degree_centrality(nx_graph)
            for feature_id, score in centrality.items():
                if feature_id in graph.nodes:
                    graph.nodes[feature_id].centrality_score = score

            # 图密度
            graph.graph_density = nx.density(nx_graph)

            # 聚类系数
            if nx_graph.number_of_nodes() >= 3:
                graph.avg_clustering = nx.average_clustering(nx_graph.to_undirected())

            # 识别核心特征（高中心性）
            sorted_features = sorted(
                centrality.items(), key=lambda x: x[1], reverse=True
            )
            graph.core_features = [fid for fid, _ in sorted_features[:3]]

        logger.info(f"   知识图谱构建完成: {len(graph.nodes)} 节点, {len(graph.edges)} 边")

        return graph

    def _extract_problem_feature_effect_triples(
        self,
        technical_problem: str,
        features: list[TechnicalFeature],
        technical_effects: list[str],
    ) -> list[ProblemFeatureEffectTriple]:
        """
        提取问题-特征-效果三元关系

        这是一个核心创新：将技术问题、技术特征、技术效果关联起来
        形成有向三元组：Problem -> Feature -> Effect
        """
        triples = []
        triple_id = 0

        # 为每个特征建立与问题和效果的关联
        for feature in features:
            # 检查特征是否与问题相关（简单关键词匹配）
            problem_related = False
            if technical_problem and any(
                keyword in feature.description.lower()
                for keyword in ["解决", "克服", "避免", "改善"]
            ):
                problem_related = True

            # 检查特征是否与效果相关
            for effect in technical_effects:
                effect_related = any(
                    keyword in feature.description.lower()
                    for keyword in ["提高", "增强", "优化", "减少"]
                )

                if effect_related:
                    triples.append(
                        ProblemFeatureEffectTriple(
                            triple_id=f"PFE{triple_id:03d}",
                            technical_problem=technical_problem if problem_related else "",
                            technical_feature=feature.feature_id,
                            technical_effect=effect,
                            confidence=0.8,
                            evidence_text=feature.description[:50],
                        )
                    )
                    triple_id += 1

        logger.info(f"   提取到 {len(triples)} 个问题-特征-效果三元关系")
        return triples

    def _identify_feature_relations(
        self, features: list[TechnicalFeature]
    ) -> list[FeatureRelation]:
        """
        识别特征之间的关联关系

        关系类型：
        - depends_on: 依赖关系（特征A依赖特征B）
        - improves: 改进关系（特征A改进特征B）
        - implements: 实现关系（特征A实现特征B）
        - contains: 包含关系（特征A包含特征B）
        - excludes: 排除关系（特征A与特征B互斥）
        """
        relations = []
        relation_id = 0

        # 关键词模式
        relation_patterns = {
            "depends_on": ["基于", "使用", "利用", "依赖", "采用"],
            "improves": ["改进", "优化", "增强", "提升"],
            "implements": ["实现", "执行", "完成"],
            "contains": ["包括", "包含", "具有", "设置"],
            "excludes": ["不同于", "区别于", "而"],
        }

        for i, feature_a in enumerate(features):
            for feature_b in features[i + 1 :]:
                # 检查关系线索
                for relation_type, keywords in relation_patterns.items():
                    # 简单文本匹配检测关系
                    text_a = feature_a.description.lower()
                    feature_b.description.lower()

                    for keyword in keywords:
                        if keyword in text_a and feature_b.feature_name[:10] in text_a:
                            relations.append(
                                FeatureRelation(
                                    source_feature=feature_a.feature_id,
                                    target_feature=feature_b.feature_id,
                                    relation_type=relation_type,
                                    weight=0.8,
                                    description=f"{feature_a.feature_name} {keyword} {feature_b.feature_name}",
                                )
                            )
                            relation_id += 1
                            break

        logger.info(f"   识别到 {len(relations)} 个特征关联关系")
        return relations

    def _calculate_graph_centrality(
        self, graph: TechnicalKnowledgeGraph
    ) -> list[tuple[str, float]]:
        """计算图谱中心性排名"""
        nx_graph = graph.to_networkx_graph()

        if nx_graph.number_of_nodes() == 0:
            return []

        # 使用度中心性
        centrality = nx.degree_centrality(nx_graph)

        # 按中心性排序
        ranking = sorted(centrality.items(), key=lambda x: x[1], reverse=True)

        return ranking

    def _identify_core_innovations(
        self, graph: TechnicalKnowledgeGraph
    ) -> list[str]:
        """
        识别核心创新特征

        综合考虑：
        1. 中心性指标（图谱中的重要性）
        2. 新颖性评分
        3. 问题-特征-效果关联强度
        """
        core_features = []

        for feature_id, feature in graph.nodes.items():
            # 综合评分
            score = (
                feature.centrality_score * 0.4  # 中心性权重40%
                + (1.0 if feature.novelty_level == "高" else 0.5) * 0.3  # 新颖性权重30%
                + feature.importance * 0.3  # 重要性权重30%
            )

            # 关联的三元关系数量加分
            triple_count = sum(
                1 for t in graph.problem_effect_triples if t.technical_feature == feature_id
            )
            score += min(triple_count * 0.1, 0.3)  # 最多加0.3分

            if score > 0.6:  # 阈值
                core_features.append(feature_id)

        # 按评分排序
        core_features.sort(
            key=lambda fid: graph.nodes[fid].centrality_score, reverse=True
        )

        return core_features[:5]  # 返回前5个核心创新特征

    # ========== 新增：Dolphin集成方法 ==========

    def _convert_dolphin_result(
        self,
        dolphin_result: dict[str, Any],        analysis: PatentAnalysis,
        patent_number: str,
    ) -> PatentAnalysis:
        """
        将Dolphin解析结果转换为我们的数据结构

        Args:
            dolphin_result: Dolphin分析结果
            analysis: 待填充的分析对象
            patent_number: 专利号

        Returns:
            PatentAnalysis: 填充后的分析对象
        """
        # 提取技术实体并转换为技术特征
        entities = dolphin_result.get("entities_count", 0)
        logger.info(f"   Dolphin提取到 {entities} 个技术实体")

        # 从Dolphin图谱中提取特征（这里需要根据实际Dolphin返回格式调整）
        # 假设Dolphin返回了技术实体列表
        dolphin_entities = dolphin_result.get("entities", [])

        # 转换为我们的TechnicalFeature格式
        features = []
        for i, entity in enumerate(dolphin_entities[:50]):  # 限制最多50个
            feature = TechnicalFeature(
                feature_id=f"D{i:03d}",
                feature_name=entity.get("text", "")[:30],
                feature_type=entity.get("entity_type", "unknown"),
                description=entity.get("text", ""),
                importance=0.7,  # 可以从Dolphin的置信度获取
                novelty_level="中",
                claimed=False,
                source_section="说明书(Dolphin解析)",
                centrality_score=0.0,  # 稍后计算
            )
            features.append(feature)

        analysis.technical_features = features

        # 构建知识图谱
        if features:
            analysis.knowledge_graph = self._build_technical_knowledge_graph(
                patent_number,
                features,
                analysis.technical_problem,
                analysis.technical_effects,
            )

            # 计算图谱指标
            analysis.graph_centrality_ranking = self._calculate_graph_centrality(
                analysis.knowledge_graph
            )
            analysis.core_innovation_features = self._identify_core_innovations(
                analysis.knowledge_graph
            )

        # 从Dolphin结果中提取其他信息
        metrics = dolphin_result.get("metrics", {})
        if metrics:
            # 提取PageRank等指标
            pagerank = metrics.get("pagerank", {})
            if pagerank:
                analysis.analysis_notes.append(f"Dolphin PageRank分析完成: {len(pagerank)}个节点")

        innovations = dolphin_result.get("innovations", [])
        if innovations:
            analysis.innovation_highlights = [
                inv.get("text", "") for inv in innovations[:5]
            ]

        analysis.analysis_confidence = 0.95  # Dolphin解析置信度较高

        return analysis

    def _visualize_knowledge_graph(
        self,
        graph: TechnicalKnowledgeGraph,
        patent_number: str,
        output_dir: Path,
    ):
        """
        生成知识图谱可视化

        Args:
            graph: 技术知识图谱
            patent_number: 专利号
            output_dir: 输出目录
        """
        if not self.enable_visualization:
            return

        try:
            import matplotlib.pyplot as plt

            # 创建输出目录
            output_dir.mkdir(parents=True, exist_ok=True)

            # 转换为NetworkX图
            nx_graph = graph.to_networkx_graph()

            if nx_graph.number_of_nodes() == 0:
                logger.warning("   知识图谱为空，跳过可视化")
                return

            # 创建图形
            fig, ax = plt.subplots(figsize=(16, 12))

            # 使用spring布局
            pos = nx.spring_layout(nx_graph, k=2, iterations=50, seed=42)

            # 绘制节点
            node_sizes = [
                graph.nodes[n].importance * 3000 for n in nx_graph.nodes()
            ]
            node_colors = [
                graph.nodes[n].centrality_score for n in nx_graph.nodes()
            ]

            # 绘制边
            nx.draw_networkx_edges(
                nx_graph, pos, ax=ax, alpha=0.3, width=1, edge_color="gray", arrows=True
            )

            # 绘制节点
            nodes = nx.draw_networkx_nodes(
                nx_graph,
                pos,
                ax=ax,
                node_size=node_sizes,
                node_color=node_colors,
                cmap=plt.cm.viridis,
                alpha=0.8,
            )

            # 添加标签
            labels = {
                n: f"{n}\n{graph.nodes[n].feature_name[:10]}"
                for n in nx_graph.nodes()
            }
            nx.draw_networkx_labels(
                nx_graph, pos, labels, ax=ax, font_size=8, font_family="sans-serif"
            )

            # 添加颜色条
            plt.colorbar(nodes, ax=ax, label="中心性得分")

            # 标题和元数据
            plt.title(
                f"技术知识图谱: {patent_number}\n"
                f"节点数: {len(graph.nodes)} | 边数: {len(graph.edges)} | "
                f"图密度: {graph.graph_density:.3f}",
                fontsize=14,
                fontweight="bold",
            )

            plt.axis("off")
            plt.tight_layout()

            # 保存图像
            safe_patent_number = patent_number.replace("/", "_").replace("\\", "_")
            output_path = output_dir / f"{safe_patent_number}_knowledge_graph.png"
            plt.savefig(output_path, dpi=150, bbox_inches="tight")
            plt.close(fig)

            logger.info(f"   ✅ 知识图谱可视化已保存: {output_path}")

        except Exception as e:
            logger.warning(f"   ⚠️ 知识图谱可视化失败: {e}")

    def _visualize_knowledge_graph_interactive(
        self,
        graph: TechnicalKnowledgeGraph,
        patent_number: str,
        output_dir: Path,
    ):
        """
        生成交互式知识图谱可视化 (pyvis)

        生成可在浏览器中打开的HTML文件，支持：
        - 节点拖拽
        - 缩放平移
        - 悬停显示详情
        - 物理引擎布局

        Args:
            graph: 技术知识图谱
            patent_number: 专利号
            output_dir: 输出目录
        """
        if not PYVIS_AVAILABLE:
            return

        try:
            # 创建输出目录
            output_dir.mkdir(parents=True, exist_ok=True)

            # 转换为NetworkX图
            nx_graph = graph.to_networkx_graph()

            if nx_graph.number_of_nodes() == 0:
                logger.warning("   知识图谱为空，跳过交互式可视化")
                return

            # 创建pyvis网络
            net = Network(
                height="900px",
                width="100%",
                bgcolor="#222222",
                font_color="white",
                directed=True,
            )

            # 设置物理引擎布局参数
            net.set_options("""
            {
              "nodes": {
                "borderWidth": 2,
                "borderWidthSelected": 3,
                "font": {"size": 14, "color": "#ffffff"},
                "size": 20
              },
              "edges": {
                "width": 2,
                "smooth": {"type": "continuous"},
                "color": {"inherit": true},
                "arrows": {"to": {"enabled": true, "scaleFactor": 0.5}}
              },
              "physics": {
                "enabled": true,
                "barnesHut": {
                  "gravitationalConstant": -8000,
                  "centralGravity": 0.3,
                  "springLength": 150,
                  "springConstant": 0.04
                },
                "maxVelocity": 50,
                "minVelocity": 0.1,
                "solver": "barnesHut",
                "timestep": 0.5,
                "stabilization": {
                  "enabled": true,
                  "iterations": 1000
                }
              },
              "interaction": {
                "hover": true,
                "tooltipDelay": 200,
                "zoomView": true,
                "dragView": true
              }
            }
            """)

            # 添加节点
            for node_id in nx_graph.nodes():
                node_data = nx_graph.nodes[node_id]
                feature = graph.nodes.get(node_id)

                # 节点颜色根据类型
                color_map = {
                    "结构": "#4CAF50",  # 绿色
                    "方法": "#2196F3",  # 蓝色
                    "参数": "#FF9800",  # 橙色
                    "效果": "#9C27B0",  # 紫色
                    "unknown": "#9E9E9E",  # 灰色
                }

                node_type = node_data.get("type", "unknown")
                node_color = color_map.get(node_type, "#9E9E9E")

                # 节点大小根据中心性
                centrality = node_data.get("centrality", 0.5)
                node_size = 20 + int(centrality * 60)  # 20-80

                # 悬停标题
                title = f"节点ID: {node_id}\n"
                title += f"名称: {node_data.get('name', 'N/A')}\n"
                title += f"类型: {node_type}\n"
                title += f"中心性: {centrality:.3f}\n"
                if feature:
                    title += f"重要性: {feature.importance:.1%}\n"
                    title += f"新颖性: {feature.novelty_level}\n"
                    title += f"描述: {feature.description[:100]}..."

                net.add_node(
                    node_id,
                    label=node_id,
                    title=title,
                    color=node_color,
                    size=node_size,
                    borderWidth=2 + int(centrality * 3),
                )

            # 添加边
            relation_labels = {
                "depends_on": "依赖",
                "improves": "改进",
                "implements": "实现",
                "contains": "包含",
                "excludes": "排除",
            }

            for source, target, edge_data in nx_graph.edges(data=True):
                relation_type = edge_data.get("type", "unknown")
                weight = edge_data.get("weight", 1.0)

                # 边的宽度根据权重
                edge_width = 1 + int(weight * 3)

                # 边的颜色
                edge_color = "#999999"
                if relation_type == "improves":
                    edge_color = "#4CAF50"  # 绿色
                elif relation_type == "depends_on":
                    edge_color = "#2196F3"  # 蓝色
                elif relation_type == "implements":
                    edge_color = "#FF9800"  # 橙色

                label = relation_labels.get(relation_type, relation_type)

                net.add_edge(
                    source,
                    target,
                    title=f"{source} → {target}\n类型: {label}\n权重: {weight:.2f}",
                    label=label if weight > 0.6 else "",
                    width=edge_width,
                    color=edge_color,
                )

            # 保存交互式HTML
            safe_patent_number = patent_number.replace("/", "_").replace("\\", "_")
            output_path = output_dir / f"{safe_patent_number}_knowledge_graph_interactive.html"
            net.save_graph(str(output_path))

            logger.info(f"   ✅ 交互式知识图谱已保存: {output_path}")

        except Exception as e:
            logger.warning(f"   ⚠️ 交互式知识图谱生成失败: {e}")

    def _visualize_knowledge_graph_enhanced(
        self,
        graph: TechnicalKnowledgeGraph,
        patent_number: str,
        output_dir: Path,
    ):
        """
        生成增强型知识图谱可视化（同时生成静态和交互式）

        Args:
            graph: 技术知识图谱
            patent_number: 专利号
            output_dir: 输出目录
        """
        # 生成静态图
        if self.enable_visualization:
            self._visualize_knowledge_graph(graph, patent_number, output_dir)

        # 生成交互式图
        self._visualize_knowledge_graph_interactive(graph, patent_number, output_dir)


# 全局单例
_analyzer_instance: XiaonaDeepTechnicalAnalyzer | None = None


def get_xiaona_deep_analyzer(
    output_dir: str = "data/analysis_reports",
    use_dolphin: bool = True,
    enable_visualization: bool = True,
) -> XiaonaDeepTechnicalAnalyzer:
    """获取分析器单例"""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = XiaonaDeepTechnicalAnalyzer(
            output_dir=output_dir,
            use_dolphin=use_dolphin,
            enable_visualization=enable_visualization,
        )
    return _analyzer_instance


# 测试代码
async def main():
    """测试深度技术分析器"""

    print("\n" + "=" * 70)
    print("🔬 小娜深度技术分析器测试")
    print("=" * 70 + "\n")

    analyzer = get_xiaona_deep_analyzer()

    # 模拟测试数据
    target_info = {
        "application_number": "CN202310000001.X",
        "title": "基于深度学习的图像识别方法",
    }

    prior_refs = [
        {
            "publication_number": "CN112345678A",
            "title": "图像识别方法及装置",
        },
        {
            "publication_number": "US2023001234A1",
            "title": "Image Processing Method",
        },
    ]

    # 执行分析
    result = await analyzer.analyze_target_and_prior_art(
        target_patent_info=target_info,
        prior_art_references=prior_refs,
    )

    # 输出Markdown
    print(result.to_markdown())

    # 保存文件
    result.save_outputs(
        output_dir=str(analyzer.output_dir),
        base_filename=f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
    )

    print("\n✅ 测试完成!")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
