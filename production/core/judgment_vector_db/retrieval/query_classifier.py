#!/usr/bin/env python3
"""
查询分类器
Query Classifier for Patent Judgment Retrieval

功能:
- 识别查询意图类型
- 提取查询关键实体
- 判断查询粒度层级
- 推荐检索策略
"""

from __future__ import annotations
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from core.logging_config import setup_logging

logger = setup_logging()


class QueryType(Enum):
    """查询类型枚举"""

    LEGAL_ARTICLE = "legal_article"  # 法条查询
    DISPUTE_FOCUS = "dispute_focus"  # 争议焦点查询
    ARGUMENT_LOGIC = "argument_logic"  # 论证逻辑查询
    CASE_SEARCH = "case_search"  # 案例检索
    COMPARATIVE_ANALYSIS = "comparative_analysis"  # 对比分析
    VIEWPOINT_AGGREGATION = "viewpoint_aggregation"  # 观点聚合


class Granularity(Enum):
    """查询粒度枚举"""

    L1 = "L1"  # 法条层
    L2 = "L2"  # 争议焦点层
    L3 = "L3"  # 论点层
    MULTI = "MULTI"  # 多粒度


@dataclass
class QueryAnalysis:
    """查询分析结果"""

    original_query: str  # 原始查询
    query_type: QueryType  # 查询类型
    granularity: Granularity  # 查询粒度
    key_entities: list[str]  # 关键实体
    legal_articles: list[str]  # 涉及法条
    dispute_keywords: list[str]  # 争议关键词
    confidence: float  # 分类置信度
    suggested_strategy: str  # 建议的检索策略
    normalized_query: str  # 标准化查询


class QueryClassifier:
    """查询分类器"""

    # 法条识别模式
    LEGAL_ARTICLE_PATTERNS = [
        r"专利法第?[\d]+[条款项号]*",
        r"专利法实施细则第?[\d]+[条款项号]*",
        r"审查指南第?[\w]*[部分章节条款]*",
        r"最高人民法院[关于]*[^,。]+",
    ]

    # 争议焦点关键词
    DISPUTE_KEYWORDS = [
        "创造性",
        "新颖性",
        "实用性",
        "充分公开",
        "等同侵权",
        "全面覆盖",
        "现有技术",
        "区别技术特征",
        "技术启示",
        "显著进步",
        "显而易见",
        "突破性",
        "实质性特点",
    ]

    # 论证逻辑标识词
    LOGIC_INDICATORS = [
        "因此",
        "故",
        "所以",
        "据此",
        "综上",
        "鉴于",
        "根据",
        "依据",
        "认定",
        "判决",
    ]

    # 对比分析标识
    COMPARISON_INDICATORS = [
        "对比",
        "差异",
        "区别",
        "相同",
        "不同",
        "变化",
        "演进",
        "趋势",
        "一致性",
    ]

    def __init__(self, config: dict[str, Any] | None = None):
        """
        初始化查询分类器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.stats = {
            "total_queries": 0,
            "type_distribution:": {},
        }

    def classify(self, query: str) -> QueryAnalysis:
        """
        分类查询

        Args:
            query: 用户查询文本

        Returns:
            QueryAnalysis对象
        """
        if not query or not query.strip():
            return self._create_default_analysis(query)

        # 标准化查询
        normalized_query = self._normalize_query(query)

        # 提取关键实体
        legal_articles = self._extract_legal_articles(normalized_query)
        dispute_keywords = self._extract_dispute_keywords(normalized_query)
        key_entities = self._extract_key_entities(normalized_query)

        # 判断查询类型
        query_type, type_confidence = self._classify_query_type(
            normalized_query, legal_articles, dispute_keywords
        )

        # 判断查询粒度
        granularity = self._determine_granularity(
            normalized_query, legal_articles, dispute_keywords
        )

        # 推荐检索策略
        suggested_strategy = self._suggest_strategy(
            query_type, granularity, legal_articles, dispute_keywords
        )

        # 构建分析结果
        analysis = QueryAnalysis(
            original_query=query,
            query_type=query_type,
            granularity=granularity,
            key_entities=key_entities,
            legal_articles=legal_articles,
            dispute_keywords=dispute_keywords,
            confidence=type_confidence,
            suggested_strategy=suggested_strategy,
            normalized_query=normalized_query,
        )

        # 更新统计
        self.stats["total_queries"] += 1
        type_name = query_type.value
        if "type_distribution" not in self.stats:
            self.stats["type_distribution"] = {}
        self.stats["type_distribution"][type_name] = (
            self.stats["type_distribution"].get(type_name, 0) + 1
        )

        return analysis

    def _normalize_query(self, query: str) -> str:
        """标准化查询"""
        # 去除多余空格
        query = re.sub(r"\s+", " ", query)
        # 去除特殊字符(保留中文、英文、数字)
        query = re.sub(r'[^\u4e00-\u9fa5a-z_a-Z0-9,。、?!;:""' r"()]", " ", query)
        return query.strip()

    def _extract_legal_articles(self, query: str) -> list[str]:
        """提取法条引用"""
        articles = []
        for pattern in self.LEGAL_ARTICLE_PATTERNS:
            matches = re.findall(pattern, query)
            articles.extend(matches)
        return list(set(articles))

    def _extract_dispute_keywords(self, query: str) -> list[str]:
        """提取争议关键词"""
        keywords = []
        for keyword in self.DISPUTE_KEYWORDS:
            if keyword in query:
                keywords.append(keyword)
        return keywords

    def _extract_key_entities(self, query: str) -> list[str]:
        """提取关键实体"""
        entities = []

        # 提取案号
        case_pattern = r"[(\(]\d{4}[)\)][^,。]+?号"
        cases = re.findall(case_pattern, query)
        entities.extend(cases)

        # 提取法院名称
        court_pattern = r"(最高人民法院|高级人民法院|中级人民法院|基层人民法院|知识产权法庭)"
        courts = re.findall(court_pattern, query)
        entities.extend(courts)

        # 提取技术领域
        tech_keywords = ["通信", "软件", "硬件", "医药", "化学", "机械", "电子"]
        for keyword in tech_keywords:
            if keyword in query:
                entities.append(keyword)

        return list(set(entities))

    def _classify_query_type(
        self, query: str, legal_articles: list[str], dispute_keywords: list[str]
    ) -> tuple[QueryType, float]:
        """
        分类查询类型

        Returns:
            (查询类型, 置信度)
        """
        scores = {
            QueryType.LEGAL_ARTICLE: 0.0,
            QueryType.DISPUTE_FOCUS: 0.0,
            QueryType.ARGUMENT_LOGIC: 0.0,
            QueryType.CASE_SEARCH: 0.0,
            QueryType.COMPARATIVE_ANALYSIS: 0.0,
            QueryType.VIEWPOINT_AGGREGATION: 0.0,
        }

        # 1. 法条查询特征
        if legal_articles:
            scores[QueryType.LEGAL_ARTICLE] += 0.6
            if "如何适用" in query or "怎么用" in query:
                scores[QueryType.LEGAL_ARTICLE] += 0.3

        # 2. 争议焦点查询特征
        if dispute_keywords:
            scores[QueryType.DISPUTE_FOCUS] += 0.5
            if len(dispute_keywords) >= 2:
                scores[QueryType.DISPUTE_FOCUS] += 0.2

        # 3. 论证逻辑查询特征
        logic_count = sum(1 for indicator in self.LOGIC_INDICATORS if indicator in query)
        if logic_count >= 2:
            scores[QueryType.ARGUMENT_LOGIC] += 0.4
            if "推理" in query or "论证" in query or "逻辑" in query:
                scores[QueryType.ARGUMENT_LOGIC] += 0.3

        # 4. 案例检索特征
        if "案号" in query or re.search(r"[(\(]\d{4}[)\)]", query):
            scores[QueryType.CASE_SEARCH] += 0.7
        if "检索" in query or "搜索" in query or "查找" in query:
            scores[QueryType.CASE_SEARCH] += 0.3

        # 5. 对比分析特征
        comparison_count = sum(1 for indicator in self.COMPARISON_INDICATORS if indicator in query)
        if comparison_count >= 2:
            scores[QueryType.COMPARATIVE_ANALYSIS] += 0.6

        # 6. 观点聚合特征
        if "汇总" in query or "总结" in query or "整体" in query:
            scores[QueryType.VIEWPOINT_AGGREGATION] += 0.5
        if "观点" in query or "态度" in query or "趋势" in query:
            scores[QueryType.VIEWPOINT_AGGREGATION] += 0.3

        # 找出最高分的类型
        max_type = max(scores, key=scores.get)
        max_score = scores[max_type]

        # 如果最高分太低,默认为案例检索
        if max_score < 0.3:
            max_type = QueryType.CASE_SEARCH
            max_score = 0.5

        return max_type, min(max_score, 1.0)

    def _determine_granularity(
        self, query: str, legal_articles: list[str], dispute_keywords: list[str]
    ) -> Granularity:
        """判断查询粒度"""
        # L1层:法条查询
        if legal_articles and not dispute_keywords:
            return Granularity.L1

        # L3层:论证逻辑查询
        if any(indicator in query for indicator in self.LOGIC_INDICATORS):
            return Granularity.L3

        # L2层:争议焦点查询
        if dispute_keywords:
            return Granularity.L2

        # 多粒度:综合查询
        if legal_articles and dispute_keywords:
            return Granularity.MULTI

        # 默认L3层
        return Granularity.L3

    def _suggest_strategy(
        self,
        query_type: QueryType,
        granularity: Granularity,
        legal_articles: list[str],
        dispute_keywords: list[str],
    ) -> str:
        """推荐检索策略"""
        strategies = {
            QueryType.LEGAL_ARTICLE: "knowledge_graph_first",
            QueryType.DISPUTE_FOCUS: "vector_primary",
            QueryType.ARGUMENT_LOGIC: "hybrid_deep",
            QueryType.CASE_SEARCH: "fulltext_primary",
            QueryType.COMPARATIVE_ANALYSIS: "multi_source",
            QueryType.VIEWPOINT_AGGREGATION: "aggregation_mode",
        }

        base_strategy = strategies.get(query_type, "hybrid_standard")

        # 根据粒度调整
        if granularity == Granularity.L1:
            return f"{base_strategy}_L1"
        elif granularity == Granularity.L2:
            return f"{base_strategy}_L2"
        elif granularity == Granularity.MULTI:
            return f"{base_strategy}_multi"

        return base_strategy

    def _create_default_analysis(self, query: str) -> QueryAnalysis:
        """创建默认分析结果"""
        return QueryAnalysis(
            original_query=query,
            query_type=QueryType.CASE_SEARCH,
            granularity=Granularity.L3,
            key_entities=[],
            legal_articles=[],
            dispute_keywords=[],
            confidence=0.5,
            suggested_strategy="hybrid_standard",
            normalized_query=query or "",
        )


# 便捷函数
def classify_query(query: str | None = None, config: dict[str, Any] | None = None) -> QueryAnalysis:
    """
    分类查询

    Args:
        query: 用户查询文本
        config: 配置字典

    Returns:
        QueryAnalysis对象
    """
    classifier = QueryClassifier(config)
    return classifier.classify(query)


if __name__ == "__main__":
    # 测试代码
    # setup_logging()  # 日志配置已移至模块导入

    # 测试查询
    test_queries = [
        "专利法第22条第3款的创造性如何判断?",
        "查找关于等同侵权的典型案例",
        "(2020)最高法知行终197号案件的论证逻辑是什么?",
        "总结近几年关于充分公开的裁判观点",
        "对比分析北京和上海法院在技术启示认定上的差异",
    ]

    classifier = QueryClassifier()

    print("\n" + "=" * 60)
    print("🔍 查询分类测试")
    print("=" * 60)

    for query in test_queries:
        analysis = classifier.classify(query)

        print(f"\n查询: {query}")
        print(f"类型: {analysis.query_type.value}")
        print(f"粒度: {analysis.granularity.value}")
        print(f"置信度: {analysis.confidence:.2f}")
        print(f"策略: {analysis.suggested_strategy}")
        if analysis.legal_articles:
            print(f"法条: {', '.join(analysis.legal_articles)}")
        if analysis.dispute_keywords:
            print(f"关键词: {', '.join(analysis.dispute_keywords)}")

    print("\n" + "=" * 60)
