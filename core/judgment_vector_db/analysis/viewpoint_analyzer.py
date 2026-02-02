#!/usr/bin/env python3
"""
观点聚合分析器
Viewpoint Aggregation Analyzer for Patent Judgments

功能:
- 聚合相似观点
- 提取裁判规则
- 分析时间演变趋势
- 生成观点分布报告
"""

import logging
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class ViewpointCluster:
    """观点聚类"""

    cluster_id: str  # 聚类ID
    main_topic: str  # 主要话题
    viewpoints: list[dict[str, Any]]  # 观点列表
    case_count: int  # 涉及案例数
    confidence: float  # 聚类置信度
    summary: str  # 观点摘要
    key_arguments: list[str]  # 关键论点


@dataclass
class JudgmentRule:
    """裁判规则"""

    rule_id: str  # 规则ID
    name: str  # 规则名称
    description: str  # 规则描述
    legal_articles: list[str]  # 适用法条
    applicability: float  # 适用率
    typical_cases: list[str]  # 典型案例
    evolution: list[dict[str, Any]]  # 演变历史


@dataclass
class TemporalTrend:
    """时间趋势"""

    topic: str  # 话题
    timeline: list[tuple[int, int]]  # 时间线 [(年份, 数量), ...]
    trend_direction: str  # 趋势方向 (上升/下降/稳定)
    key_shifts: list[dict[str, Any]]  # 关键转折点


class ViewpointAnalyzer:
    """观点聚合分析器"""

    def __init__(self, postgres_client, hybrid_retriever, config: dict[str, Any] | None = None):
        """
        初始化分析器

        Args:
            postgres_client: PostgreSQL客户端
            hybrid_retriever: 混合检索引擎
            config: 配置字典
        """
        self.postgres_client = postgres_client
        self.retriever = hybrid_retriever
        self.config = config or {}

        # 分析参数
        self.min_cluster_size = self.config.get("min_cluster_size", 3)
        self.similarity_threshold = self.config.get("similarity_threshold", 0.7)

    def aggregate_viewpoints(
        self, query: str, layer: str = "L3", limit: int = 50
    ) -> list[ViewpointCluster]:
        """
        聚合观点

        Args:
            query: 查询主题
            layer: 分析层级
            limit: 检索数量

        Returns:
            观点聚类列表
        """
        logger.info(f"🔄 聚合观点: {query}")

        # 1. 检索相关论点
        from core.judgment_vector_db.retrieval.hybrid_retriever import RetrievalStrategy

        result = self.retriever.retrieve(
            query=query, strategy=RetrievalStrategy.AGGREGATION_MODE, layer=layer, limit=limit
        )

        # 2. 按争议焦点分组
        focus_groups = self._group_by_dispute_focus(result.results)

        # 3. 为每个焦点组创建聚类
        clusters = []
        for focus, arguments in focus_groups.items():
            if len(arguments) >= self.min_cluster_size:
                cluster = self._create_viewpoint_cluster(focus, arguments)
                clusters.append(cluster)

        logger.info(f"✅ 聚合完成: {len(clusters)}个观点聚类")
        return clusters

    def extract_judgment_rules(self, legal_article: str, limit: int = 100) -> list[JudgmentRule]:
        """
        提取裁判规则

        Args:
            legal_article: 法律条文
            limit: 检索数量

        Returns:
            裁判规则列表
        """
        logger.info(f"🔄 提取裁判规则: {legal_article}")

        # 1. 检索相关案例
        from core.judgment_vector_db.retrieval.hybrid_retriever import RetrievalStrategy

        result = self.retriever.retrieve(
            query=f"{legal_article}的适用规则",
            strategy=RetrievalStrategy.GRAPH_FIRST,
            layer="L3",
            limit=limit,
        )

        # 2. 按法条适用模式分组
        rule_groups = self._group_by_application_pattern(result.results, legal_article)

        # 3. 提取规则
        rules = []
        for pattern, cases in rule_groups.items():
            rule = self._extract_rule(pattern, cases, legal_article)
            if rule:
                rules.append(rule)

        logger.info(f"✅ 规则提取完成: {len(rules)}条规则")
        return rules

    def analyze_temporal_evolution(
        self, topic: str, start_year: int = 2010, end_year: int = 2025
    ) -> list[TemporalTrend]:
        """
        分析时间演变

        Args:
            topic: 分析主题
            start_year: 起始年份
            end_year: 结束年份

        Returns:
            时间趋势列表
        """
        logger.info(f"🔄 分析时间演变: {topic} ({start_year}-{end_year})")

        # 1. 检索相关案例
        from core.judgment_vector_db.retrieval.hybrid_retriever import RetrievalStrategy

        result = self.retriever.retrieve(
            query=topic, strategy=RetrievalStrategy.AGGREGATION_MODE, layer="L3", limit=200
        )

        # 2. 按年份统计
        timeline = self._build_timeline(result.results, start_year, end_year)

        # 3. 分析趋势
        trends = []
        for subtopic, year_counts in timeline.items():
            trend = self._analyze_trend(subtopic, year_counts)
            trends.append(trend)

        logger.info(f"✅ 趋势分析完成: {len(trends)}个趋势")
        return trends

    def generate_analysis_report(
        self, query: str, analysis_types: list["key"] = None
    ) -> dict[str, Any]:
        """
        生成综合分析报告

        Args:
            query: 分析主题
            analysis_types: 分析类型列表

        Returns:
            分析报告字典
        """
        if analysis_types is None:
            analysis_types = ["viewpoints", "rules", "trends"]

        logger.info(f"🔄 生成分析报告: {query}")

        report = {"topic": query, "generated_at": datetime.now().isoformat(), "sections": {}}

        # 1. 观点聚合
        if "viewpoints" in analysis_types:
            viewpoints = self.aggregate_viewpoints(query)
            report["sections"]["viewpoint_aggregation"] = {
                "clusters": [
                    {
                        "id": c.cluster_id,
                        "topic": c.main_topic,
                        "case_count": c.case_count,
                        "summary": c.summary,
                    }
                    for c in viewpoints
                ],
                "total_clusters": len(viewpoints),
            }

        # 2. 裁判规则提取
        if "rules" in analysis_types:
            # 从查询中提取法条
            legal_articles = self._extract_legal_articles_from_query(query)
            rules = []
            for article in legal_articles:
                article_rules = self.extract_judgment_rules(article)
                rules.extend(article_rules)

            report["sections"]["judgment_rules"] = {
                "rules": [
                    {
                        "id": r.rule_id,
                        "name": r.name,
                        "description": r.description,
                        "applicability": r.applicability,
                    }
                    for r in rules
                ],
                "total_rules": len(rules),
            }

        # 3. 时间演变分析
        if "trends" in analysis_types:
            trends = self.analyze_temporal_evolution(query)
            report["sections"]["temporal_evolution"] = {
                "trends": [
                    {"topic": t.topic, "direction": t.trend_direction, "timeline": t.timeline}
                    for t in trends
                ],
                "total_trends": len(trends),
            }

        # 4. 统计摘要
        report["summary"] = self._generate_summary(report)

        logger.info("✅ 分析报告生成完成")
        return report

    def _group_by_dispute_focus(self, results: list) -> dict[str, list]:
        """按争议焦点分组"""
        groups = defaultdict(list)

        for result in results:
            focus = result.metadata.get("dispute_focus", "未分类")
            groups[focus].append(result)

        return groups

    def _create_viewpoint_cluster(self, focus: str, arguments: list) -> ViewpointCluster:
        """创建观点聚类"""
        # 提取案例
        cases = [arg.metadata.get("case_id") for arg in arguments]
        unique_cases = list(set(cases))

        # 提取关键论点
        key_args = []
        for arg in arguments[:5]:  # 取前5个
            content = arg.content
            if content:
                key_args.append(content[:200])

        # 生成摘要
        summary = self._generate_cluster_summary(focus, arguments)

        return ViewpointCluster(
            cluster_id=f"cluster_{hash(focus) % 10000:04d}",
            main_topic=focus,
            viewpoints=[
                {
                    "id": arg.id,
                    "case_id": arg.metadata.get("case_id"),
                    "content": arg.content,
                    "score": arg.score,
                }
                for arg in arguments
            ],
            case_count=len(unique_cases),
            confidence=sum(arg.score for arg in arguments) / len(arguments),
            summary=summary,
            key_arguments=key_args,
        )

    def _generate_cluster_summary(self, focus: str, arguments: list) -> str:
        """生成聚类摘要"""
        # 统计关键词
        all_text = " ".join([arg.content for arg in arguments])
        words = re.findall(r"[\u4e00-\u9fa5]{2,}", all_text)
        word_freq = Counter(words)

        # 取高频词
        top_words = [w for w, c in word_freq.most_common(10)]

        return f"关于「{focus}」的讨论,主要涉及{', '.join(top_words[:5])}等方面,共{len(arguments)}个论点。"

    def _group_by_application_pattern(self, results: list, legal_article: str) -> dict[str, list]:
        """按法条适用模式分组"""
        groups = defaultdict(list)

        for result in results:
            # 提取适用模式
            logic = result.metadata.get("argument_logic", {})
            premise = logic.get("premise", "")

            # 简化:使用前提作为模式标识
            # 实际应该使用更复杂的模式提取
            pattern_key = premise[:50] if premise else "未分类"
            groups[pattern_key].append(result)

        return groups

    def _extract_rule(
        self, pattern: str, cases: list, legal_article: str
    ) -> JudgmentRule | None:
        """提取单条规则"""
        if len(cases) < 2:
            return None

        # 提取案例
        case_ids = [c.metadata.get("case_id") for c in cases]

        # 计算适用率
        applicability = len(cases) / 100.0  # 简化

        # 生成规则描述
        description = f"在{legal_article}适用中,{pattern[:100]}..."

        return JudgmentRule(
            rule_id=f"rule_{hash(pattern) % 10000:04d}",
            name=f"{legal_article}适用规则",
            description=description,
            legal_articles=[legal_article],
            applicability=min(applicability, 1.0),
            typical_cases=case_ids[:5],
            evolution=[],
        )

    def _build_timeline(
        self, results: list, start_year: int, end_year: int
    ) -> dict[str, list[tuple[int, int]:
        """构建时间线"""
        timelines = defaultdict(lambda: defaultdict(int))

        for result in results:
            # 提取年份
            case_id = result.metadata.get("case_id", "")
            year_match = re.search(r"[(\(](\d{4})[)\)]", case_id)

            if year_match:
                year = int(year_match.group(1))
                if start_year <= year <= end_year:
                    # 按话题分组
                    focus = result.metadata.get("dispute_focus", "其他")
                    timelines[focus][year] += 1

        # 转换为列表
        timeline_dict = {}
        for topic, year_counts in timelines.items():
            timeline_dict[topic] = sorted(year_counts.items())

        return timeline_dict

    def _analyze_trend(self, topic: str, year_counts: list[tuple[int, int]) -> TemporalTrend:
        """分析单个趋势"""
        if len(year_counts) < 2:
            return TemporalTrend(
                topic=topic, timeline=year_counts, trend_direction="数据不足", key_shifts=[]
            )

        # 计算趋势方向
        first_half = sum(c for _, c in year_counts[: len(year_counts) // 2])
        second_half = sum(c for _, c in year_counts[len(year_counts) // 2 :])

        if second_half > first_half * 1.2:
            direction = "上升"
        elif second_half < first_half * 0.8:
            direction = "下降"
        else:
            direction = "稳定"

        # 识别关键转折点(简化)
        key_shifts = []
        for i in range(1, len(year_counts)):
            _prev_year, prev_count = year_counts[i - 1]
            curr_year, curr_count = year_counts[i]

            if curr_count > prev_count * 2 or curr_count < prev_count * 0.5:
                key_shifts.append(
                    {
                        "year": curr_year,
                        "type": "骤增" if curr_count > prev_count else "骤降",
                        "change": curr_count - prev_count,
                    }
                )

        return TemporalTrend(
            topic=topic, timeline=year_counts, trend_direction=direction, key_shifts=key_shifts
        )

    def _extract_legal_articles_from_query(self, query: str) -> list[str]:
        """从查询中提取法条"""
        patterns = [
            r"专利法第?[\d]+[条款项号]*",
            r"专利法实施细则第?[\d]+[条款项号]*",
        ]

        articles = []
        for pattern in patterns:
            matches = re.findall(pattern, query)
            articles.extend(matches)

        return list(set(articles))

    def _generate_summary(self, report: dict[str, Any]) -> str:
        """生成报告摘要"""
        summary_parts = []

        sections = report.get("sections", {})

        # 观点聚合摘要
        if "viewpoint_aggregation" in sections:
            vp_data = sections["viewpoint_aggregation"]
            summary_parts.append(f"识别出{vp_data['total_clusters']}个主要观点聚类")

        # 裁判规则摘要
        if "judgment_rules" in sections:
            jr_data = sections["judgment_rules"]
            summary_parts.append(f"提取了{jr_data['total_rules']}条裁判规则")

        # 时间趋势摘要
        if "temporal_evolution" in sections:
            te_data = sections["temporal_evolution"]
            summary_parts.append(f"分析了{te_data['total_trends']}个趋势")

        return ";".join(summary_parts) + "。"


# 便捷函数
def create_viewpoint_analyzer(
    Optional[postgres_client, hybrid_retriever, config: dict[str, Any] | None = None
) -> ViewpointAnalyzer:
    """
    创建观点分析器

    Args:
        postgres_client: PostgreSQL客户端
        hybrid_retriever: 混合检索引擎
        config: 配置字典

    Returns:
        ViewpointAnalyzer实例
    """
    return ViewpointAnalyzer(
        postgres_client=postgres_client, hybrid_retriever=hybrid_retriever, config=config
    )
