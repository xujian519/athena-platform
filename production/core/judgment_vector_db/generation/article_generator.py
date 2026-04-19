#!/usr/bin/env python3
from __future__ import annotations
"""
文章生成引擎
Article Generation Engine for Patent Judgment Analysis

功能:
- 基于检索结果生成分析文章
- 支持多种文章类型(研究综述、案例分析、规则解读)
- 质量检查机制
- 多格式导出
"""

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ArticleType(Enum):
    """文章类型枚举"""

    REVIEW = "review"  # 研究综述
    CASE_ANALYSIS = "case_analysis"  # 案例分析
    RULE_INTERPRETATION = "rule_interpretation"  # 规则解读
    COMPARATIVE_STUDY = "comparative_study"  # 比较研究
    TREND_REPORT = "trend_report"  # 趋势报告


class ArticleQuality(Enum):
    """文章质量等级"""

    EXCELLENT = "excellent"  # 优秀
    GOOD = "good"  # 良好
    ACCEPTABLE = "acceptable"  # 可接受
    NEEDS_IMPROVEMENT = "needs_improvement"  # 需改进


@dataclass
class ArticleSection:
    """文章段落"""

    section_id: str  # 段落ID
    title: str  # 标题
    content: str  # 内容
    subsections: list["ArticleSection"]  # 子段落
    metadata: dict[str, Any]  # 元数据


@dataclass
class GeneratedArticle:
    """生成的文章"""

    article_id: str  # 文章ID
    title: str  # 标题
    article_type: ArticleType  # 文章类型
    sections: list[ArticleSection]  # 段落列表
    metadata: dict[str, Any]  # 元数据
    quality_score: float  # 质量分数
    quality_level: ArticleQuality  # 质量等级
    sources: list[str]  # 来源列表
    generated_at: str  # 生成时间


@dataclass
class QualityCheckResult:
    """质量检查结果"""

    overall_score: float  # 总体分数
    quality_level: ArticleQuality  # 质量等级
    dimension_scores: dict[str, float]  # 各维度分数
    issues: list[str]  # 问题列表
    suggestions: list[str]  # 改进建议


class ArticleGenerator:
    """文章生成引擎"""

    def __init__(
        self, viewpoint_analyzer, hybrid_retriever, config: dict[str, Any] | None = None
    ):
        """
        初始化生成引擎

        Args:
            viewpoint_analyzer: 观点分析器
            hybrid_retriever: 混合检索引擎
            config: 配置字典
        """
        self.analyzer = viewpoint_analyzer
        self.retriever = hybrid_retriever
        self.config = config or {}

        # 生成参数
        self.min_sources = self.config.get("min_sources", 5)
        self.quality_threshold = self.config.get("quality_threshold", 0.7)

    def generate_article(
        self,
        topic: str,
        article_type: ArticleType = ArticleType.REVIEW,
        analysis_report: dict[str, Any] | None = None,
        requirements: dict[str, Any] | None = None,
    ) -> GeneratedArticle:
        """
        生成文章

        Args:
            topic: 文章主题
            article_type: 文章类型
            analysis_report: 分析报告(可选,如无则自行分析)
            requirements: 特殊要求

        Returns:
            GeneratedArticle对象
        """
        logger.info(f"🔄 生成文章: {topic} ({article_type.value})")

        # 1. 如果没有提供分析报告,先生成
        if not analysis_report:
            analysis_report = self.analyzer.generate_analysis_report(
                query=topic, analysis_types=["viewpoints", "rules", "trends"]
            )

        # 2. 根据文章类型生成结构
        sections = self._generate_sections(
            topic=topic,
            article_type=article_type,
            analysis_report=analysis_report,
            requirements=requirements or {},
        )

        # 3. 提取来源
        sources = self._extract_sources(analysis_report)

        # 4. 质量检查
        quality_result = self._check_quality(
            article=GeneratedArticle(
                article_id=f"article_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                title=self._generate_title(topic, article_type),
                article_type=article_type,
                sections=sections,
                metadata=analysis_report,
                quality_score=0.0,
                quality_level=ArticleQuality.NEEDS_IMPROVEMENT,
                sources=sources,
                generated_at=datetime.now().isoformat(),
            )
        )

        # 5. 构建最终文章
        article = GeneratedArticle(
            article_id=f"article_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            title=self._generate_title(topic, article_type),
            article_type=article_type,
            sections=sections,
            metadata=analysis_report,
            quality_score=quality_result.overall_score,
            quality_level=quality_result.quality_level,
            sources=sources,
            generated_at=datetime.now().isoformat(),
        )

        logger.info(f"✅ 文章生成完成: 质量={quality_result.quality_level.value}")
        return article

    def _generate_sections(
        self,
        topic: str,
        article_type: ArticleType,
        analysis_report: dict[str, Any]
    ) -> list[ArticleSection]:
        """生成文章段落"""
        if article_type == ArticleType.REVIEW:
            return self._generate_review_sections(topic, analysis_report)
        elif article_type == ArticleType.CASE_ANALYSIS:
            return self._generate_case_analysis_sections(topic, analysis_report)
        elif article_type == ArticleType.RULE_INTERPRETATION:
            return self._generate_rule_interpretation_sections(topic, analysis_report)
        elif article_type == ArticleType.COMPARATIVE_STUDY:
            return self._generate_comparative_study_sections(topic, analysis_report)
        elif article_type == ArticleType.TREND_REPORT:
            return self._generate_trend_report_sections(topic, analysis_report)
        else:
            return self._generate_review_sections(topic, analysis_report)

    def _generate_review_sections(
        self, topic: str, analysis_report: dict[str, Any]
    ) -> list[ArticleSection]:
        """生成研究综述段落"""
        sections = []

        # 1. 引言
        sections.append(
            ArticleSection(
                section_id="intro",
                title="引言",
                content=self._generate_intro_content(topic, analysis_report),
                subsections=[],
                metadata={"type": "introduction"},
            )
        )

        # 2. 主要观点聚类
        vp_data = analysis_report.get("sections", {}).get("viewpoint_aggregation", {})
        clusters = vp_data.get("clusters", [])

        if clusters:
            sections.append(
                ArticleSection(
                    section_id="viewpoints",
                    title="主要观点分析",
                    content=self._generate_viewpoints_content(clusters),
                    subsections=[
                        ArticleSection(
                            section_id=f"viewpoint_{i}",
                            title=c["topic"],
                            content=c["summary"],
                            subsections=[],
                            metadata={"cluster_id": c["id"], "case_count": c["case_count"]},
                        )
                        for i, c in enumerate(clusters)
                    ],
                    metadata={"type": "viewpoint_analysis"},
                )
            )

        # 3. 裁判规则
        jr_data = analysis_report.get("sections", {}).get("judgment_rules", {})
        rules = jr_data.get("rules", [])

        if rules:
            sections.append(
                ArticleSection(
                    section_id="rules",
                    title="裁判规则总结",
                    content=self._generate_rules_content(rules),
                    subsections=[
                        ArticleSection(
                            section_id=f"rule_{i}",
                            title=r["name"],
                            content=r["description"],
                            subsections=[],
                            metadata={"rule_id": r["id"], "applicability": r["applicability"]},
                        )
                        for i, r in enumerate(rules[:5])  # 最多5条规则
                    ],
                    metadata={"type": "rules_summary"},
                )
            )

        # 4. 时间演变
        te_data = analysis_report.get("sections", {}).get("temporal_evolution", {})
        trends = te_data.get("trends", [])

        if trends:
            sections.append(
                ArticleSection(
                    section_id="trends",
                    title="时间演变趋势",
                    content=self._generate_trends_content(trends),
                    subsections=[
                        ArticleSection(
                            section_id=f"trend_{i}",
                            title=t["topic"],
                            content=f"趋势方向:{t['direction']}",
                            subsections=[],
                            metadata={"timeline": t["timeline"]},
                        )
                        for i, t in enumerate(trends)
                    ],
                    metadata={"type": "temporal_analysis"},
                )
            )

        # 5. 结论
        sections.append(
            ArticleSection(
                section_id="conclusion",
                title="结论",
                content=self._generate_conclusion_content(topic, analysis_report),
                subsections=[],
                metadata={"type": "conclusion"},
            )
        )

        return sections

    def _generate_case_analysis_sections(
        self, topic: str, analysis_report: dict[str, Any]
    ) -> list[ArticleSection]:
        """生成案例分析段落"""
        # 简化实现
        return [
            ArticleSection(
                section_id="case_overview",
                title="案例概述",
                content=f"关于{topic}的案例分析",
                subsections=[],
                metadata={},
            )
        ]

    def _generate_rule_interpretation_sections(
        self, topic: str, analysis_report: dict[str, Any]
    ) -> list[ArticleSection]:
        """生成规则解读段落"""
        # 简化实现
        return [
            ArticleSection(
                section_id="rule_overview",
                title="规则概述",
                content=f"关于{topic}的规则解读",
                subsections=[],
                metadata={},
            )
        ]

    def _generate_comparative_study_sections(
        self, topic: str, analysis_report: dict[str, Any]
    ) -> list[ArticleSection]:
        """生成比较研究段落"""
        # 简化实现
        return [
            ArticleSection(
                section_id="comparison_intro",
                title="比较研究引言",
                content=f"关于{topic}的比较研究",
                subsections=[],
                metadata={},
            )
        ]

    def _generate_trend_report_sections(
        self, topic: str, analysis_report: dict[str, Any]
    ) -> list[ArticleSection]:
        """生成趋势报告段落"""
        # 简化实现
        return [
            ArticleSection(
                section_id="trend_overview",
                title="趋势概述",
                content=f"关于{topic}的趋势报告",
                subsections=[],
                metadata={},
            )
        ]

    def _generate_intro_content(self, topic: str, analysis_report: dict[str, Any]) -> str:
        """生成引言内容"""
        summary = analysis_report.get("summary", "")

        intro = f"""# 引言

{topic}是专利法律实践中的重要议题。{summary}

本文基于权威判决文档的深度分析,系统梳理了相关裁判观点、适用规则和发展趋势,为专利代理人和研究人员提供参考。

"""
        return intro

    def _generate_viewpoints_content(self, clusters: list[dict]) -> str:
        """生成观点分析内容"""
        content = f"""# 主要观点分析

通过聚类分析,共识别出{len(clusters)}个主要观点聚类,涵盖了不同法院和时期的裁判思路。

"""
        return content

    def _generate_rules_content(self, rules: list[dict]) -> str:
        """生成规则总结内容"""
        content = f"""# 裁判规则总结

基于案例的深度分析,提取出{len(rules)}条核心裁判规则,反映了司法实践中的标准和做法。

"""
        return content

    def _generate_trends_content(self, trends: list[dict]) -> str:
        """生成趋势分析内容"""
        content = f"""# 时间演变趋势

分析了{len(trends)}个主要议题的发展趋势,揭示了司法实践的演变轨迹。

"""
        return content

    def _generate_conclusion_content(self, topic: str, analysis_report: dict[str, Any]) -> str:
        """生成结论内容"""
        summary = analysis_report.get("summary", "")

        conclusion = f"""# 结论

综上所述,{summary}

这些分析结果有助于深入理解{topic}的法律适用,为专利实务工作提供指导。

"""
        return conclusion

    def _generate_title(self, topic: str, article_type: ArticleType) -> str:
        """生成文章标题"""
        type_suffix = {
            ArticleType.REVIEW: "研究综述",
            ArticleType.CASE_ANALYSIS: "案例分析",
            ArticleType.RULE_INTERPRETATION: "规则解读",
            ArticleType.COMPARATIVE_STUDY: "比较研究",
            ArticleType.TREND_REPORT: "趋势报告",
        }

        suffix = type_suffix.get(article_type, "分析报告")
        return f"{topic}{suffix}"

    def _extract_sources(self, analysis_report: dict[str, Any]) -> list[str]:
        """提取来源列表"""
        sources = []

        # 从各部分提取案例ID
        sections = analysis_report.get("sections", {})

        # 观点聚类中的案例
        vp_data = sections.get("viewpoint_aggregation", {})
        for _cluster in vp_data.get("clusters", []):
            # 这里应该从聚类中提取具体案例
            pass  # 简化

        # 裁判规则中的案例
        jr_data = sections.get("judgment_rules", {})
        for _rule in jr_data.get("rules", []):
            pass  # 简化

        return list(set(sources))

    def _check_quality(self, article: GeneratedArticle) -> QualityCheckResult:
        """检查文章质量"""
        dimension_scores = {}
        issues = []
        suggestions = []

        # 1. 结构完整性检查
        structure_score = self._check_structure(article)
        dimension_scores["structure"] = structure_score
        if structure_score < 0.7:
            issues.append("文章结构不完整")
            suggestions.append("补充缺失的段落")

        # 2. 内容充实度检查
        content_score = self._check_content(article)
        dimension_scores["content"] = content_score
        if content_score < 0.7:
            issues.append("内容不够充实")
            suggestions.append("增加更多细节和例证")

        # 3. 逻辑连贯性检查
        logic_score = self._check_logic(article)
        dimension_scores["logic"] = logic_score
        if logic_score < 0.7:
            issues.append("逻辑不够连贯")
            suggestions.append("加强段落间的逻辑衔接")

        # 4. 来源充分性检查
        source_score = self._check_sources(article)
        dimension_scores["sources"] = source_score
        if source_score < 0.7:
            issues.append("引用来源不足")
            suggestions.append("增加更多权威案例引用")

        # 5. 语言表达检查
        language_score = self._check_language(article)
        dimension_scores["language"] = language_score
        if language_score < 0.7:
            issues.append("语言表达有待改进")
            suggestions.append("优化文字表述")

        # 计算总体分数
        overall_score = sum(dimension_scores.values()) / len(dimension_scores)

        # 确定质量等级
        if overall_score >= 0.9:
            quality_level = ArticleQuality.EXCELLENT
        elif overall_score >= 0.75:
            quality_level = ArticleQuality.GOOD
        elif overall_score >= 0.6:
            quality_level = ArticleQuality.ACCEPTABLE
        else:
            quality_level = ArticleQuality.NEEDS_IMPROVEMENT

        return QualityCheckResult(
            overall_score=overall_score,
            quality_level=quality_level,
            dimension_scores=dimension_scores,
            issues=issues,
            suggestions=suggestions,
        )

    def _check_structure(self, article: GeneratedArticle) -> float:
        """检查结构完整性"""
        required_sections = ["intro", "conclusion"]
        section_ids = [s.section_id for s in article.sections]

        score = 1.0
        for req in required_sections:
            if req not in section_ids:
                score -= 0.3

        return max(score, 0.0)

    def _check_content(self, article: GeneratedArticle) -> float:
        """检查内容充实度"""
        total_chars = sum(len(s.content) for s in article.sections)

        if total_chars >= 5000:
            return 1.0
        elif total_chars >= 3000:
            return 0.8
        elif total_chars >= 1000:
            return 0.6
        else:
            return 0.4

    def _check_logic(self, article: GeneratedArticle) -> float:
        """检查逻辑连贯性"""
        # 简化:检查是否有逻辑连接词
        all_content = " ".join([s.content for s in article.sections])

        logic_words = ["因此", "所以", "综上", "然而", "但是", "此外", "同时"]
        count = sum(1 for word in logic_words if word in all_content)

        if count >= 10:
            return 1.0
        elif count >= 5:
            return 0.7
        else:
            return 0.5

    def _check_sources(self, article: GeneratedArticle) -> float:
        """检查来源充分性"""
        source_count = len(article.sources)

        if source_count >= 20:
            return 1.0
        elif source_count >= 10:
            return 0.8
        elif source_count >= 5:
            return 0.6
        else:
            return 0.4

    def _check_language(self, article: GeneratedArticle) -> float:
        """检查语言表达"""
        # 简化:检查句子长度
        all_content = " ".join([s.content for s in article.sections])
        sentences = re.split(r"[。!?]", all_content)

        avg_length = sum(len(s) for s in sentences) / len(sentences) if sentences else 0

        if 20 <= avg_length <= 100:
            return 1.0
        elif avg_length < 20:
            return 0.6  # 句子太短
        else:
            return 0.8  # 句子较长但可接受

    def export_markdown(self, article: GeneratedArticle) -> str:
        """导出为Markdown格式"""
        lines = []

        lines.append(f"# {article.title}\n")
        lines.append(f"**生成时间**: {article.generated_at}\n")
        lines.append(f"**质量等级**: {article.quality_level.value}\n")
        lines.append(f"**质量分数**: {article.quality_score:.2f}\n")
        lines.append("\n---\n")

        for section in article.sections:
            lines.append(f"## {section.title}\n")
            lines.append(f"{section.content}\n")

            for subsection in section.subsections:
                lines.append(f"### {subsection.title}\n")
                lines.append(f"{subsection.content}\n")

        return "\n".join(lines)

    def export_html(self, article: GeneratedArticle) -> str:
        """导出为HTML格式"""
        # 简化实现
        markdown = self.export_markdown(article)
        return f"<!DOCTYPE html><html><body><pre>{markdown}</pre></body></html>"

    def export_json(self, article: GeneratedArticle) -> dict[str, Any]:
        """导出为JSON格式"""
        return {
            "article_id": article.article_id,
            "title": article.title,
            "article_type": article.article_type.value,
            "sections": [
                {
                    "section_id": s.section_id,
                    "title": s.title,
                    "content": s.content,
                    "subsections": [
                        {"section_id": ss.section_id, "title": ss.title, "content": ss.content}
                        for ss in s.subsections
                    ],
                }
                for s in article.sections
            ],
            "metadata": article.metadata,
            "quality_score": article.quality_score,
            "quality_level": article.quality_level.value,
            "sources": article.sources,
            "generated_at": article.generated_at,
        }


# 便捷函数
def create_article_generator(
    viewpoint_analyzer = None,
    hybrid_retriever = None,
    config: dict[str, Any] | None = None
) -> ArticleGenerator:
    """
    创建文章生成器

    Args:
        viewpoint_analyzer: 观点分析器
        hybrid_retriever: 混合检索引擎
        config: 配置字典

    Returns:
        ArticleGenerator实例
    """
    return ArticleGenerator(
        viewpoint_analyzer=viewpoint_analyzer, hybrid_retriever=hybrid_retriever, config=config
    )
