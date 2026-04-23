#!/usr/bin/env python3

"""
向量集合配置优化
Vector Collection Configuration Optimization

根据优化计划重构集合映射,实现数据分离和专业化存储
作者: 小诺·双鱼座
创建时间: 2025-12-21
版本: v1.0.0 "集合重构"
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class CollectionType(Enum):
    """集合类型枚举"""

    PATENT_RULES = "patent_rules_1024"  # 专利法规文本(审查指南、专利法等)
    LEGAL_CLAUSES = "legal_clauses_1024"  # 通用法律条款、判例
    PATENTS_DATA = "patents_data_1024"  # 专利实体数据(摘要、权利要求书)
    TECHNICAL_TERMS = "technical_terms_1024"  # 技术术语
    LEGAL_CONCEPTS = "legal_concepts_1024"  # 法律概念
    CASE_DATA = "case_data_1024"  # 案例数据


@dataclass
class CollectionConfig:
    """集合配置"""

    collection_type: CollectionType
    description: str
    vector_size: int = 1024
    distance_metric: str = "Cosine"
    content_types: Optional[list[str]] = None
    node_types: Optional[list[str]] = None
    priority: int = 1  # 检索优先级


class OptimizedCollectionMapper:
    """优化的集合映射器"""

    def __init__(self):
        self.collection_configs = {
            CollectionType.PATENT_RULES: CollectionConfig(
                collection_type=CollectionType.PATENT_RULES,
                description="专利法规文本存储(审查指南、专利法、实施细则)",
                content_types=["法规条文", "审查指南", "实施细则"],
                node_types=["ARTICLE", "CONCEPT"],
                priority=3,  # 高优先级,法规优先检索
            ),
            CollectionType.LEGAL_CLAUSES: CollectionConfig(
                collection_type=CollectionType.LEGAL_CLAUSES,
                description="通用法律条款和判例存储",
                content_types=["法律条款", "判例", "司法解释"],
                node_types=["LEGAL_CASE", "CONCEPT"],
                priority=2,
            ),
            CollectionType.PATENTS_DATA: CollectionConfig(
                collection_type=CollectionType.PATENTS_DATA,
                description="专利实体数据存储(摘要、权利要求书、说明书)",
                content_types=["专利摘要", "权利要求", "说明书"],
                node_types=["PATENT", "PRIOR_ART"],
                priority=1,  # 专利数据基础检索
            ),
            CollectionType.TECHNICAL_TERMS: CollectionConfig(
                collection_type=CollectionType.TECHNICAL_TERMS,
                description="技术术语和概念存储",
                content_types=["技术术语", "技术概念"],
                node_types=["TECHNOLOGY", "CONCEPT"],
                priority=2,
            ),
            CollectionType.LEGAL_CONCEPTS: CollectionConfig(
                collection_type=CollectionType.LEGAL_CONCEPTS,
                description="法律概念和定义存储",
                content_types=["法律定义", "法律概念"],
                node_types=["CONCEPT"],
                priority=3,
            ),
            CollectionType.CASE_DATA: CollectionConfig(
                collection_type=CollectionType.CASE_DATA,
                description="案例数据详细存储",
                content_types=["案例全文", "判决书"],
                node_types=["LEGAL_CASE"],
                priority=2,
            ),
        }

        # 节点类型到集合的映射
        self.node_type_mapping = {
            "PATENT": CollectionType.PATENTS_DATA,
            "PRIOR_ART": CollectionType.PATENTS_DATA,
            "ARTICLE": CollectionType.PATENT_RULES,
            "CONCEPT": CollectionType.LEGAL_CONCEPTS,  # 默认法律概念
            "LEGAL_CASE": CollectionType.LEGAL_CLAUSES,
            "TECHNOLOGY": CollectionType.TECHNICAL_TERMS,
            "COMPANY": CollectionType.TECHNICAL_TERMS,  # 公司数据存储在技术集合
            "INVENTOR": CollectionType.TECHNICAL_TERMS,  # 发明人数据
            "CATEGORY": CollectionType.TECHNICAL_TERMS,  # 分类信息
            "KEYWORD": CollectionType.TECHNICAL_TERMS,  # 关键词
        }

        # 基于内容关键词的动态映射
        self.content_keyword_mapping = {
            CollectionType.PATENT_RULES: [
                "专利法",
                "审查指南",
                "实施细则",
                "专利条例",
                "保护条例",
                "外观设计",
                "发明专利",
                "实用新型",
            ],
            CollectionType.LEGAL_CLAUSES: [
                "民法典",
                "合同法",
                "侵权责任",
                "司法解释",
                "判例",
                "案例",
                "判决",
                "裁定",
            ],
            CollectionType.PATENTS_DATA: [
                "权利要求",
                "说明书",
                "摘要",
                "技术方案",
                "实施例",
                "背景技术",
                "发明内容",
            ],
        }

    def map_node_to_collection(
        self, node_type: str, content: Optional[str] = None, title: Optional[str] = None
    ) -> CollectionType:
        """
        将节点映射到最适合的集合

        Args:
            node_type: 节点类型
            content: 节点内容(可选,用于动态判断)
            title: 节点标题(可选,用于动态判断)

        Returns:
            CollectionType: 目标集合类型
        """
        # 1. 首先基于节点类型直接映射
        if node_type in self.node_type_mapping:
            return self.node_type_mapping[node_type]

        # 2. 如果没有直接映射,基于内容关键词动态判断
        if content or title:
            text_to_analyze = (content or "") + " " + (title or "")

            for collection_type, keywords in self.content_keyword_mapping.items():
                if any(keyword in text_to_analyze for keyword in keywords):
                    return collection_type

        # 3. 默认映射到技术术语集合
        return CollectionType.TECHNICAL_TERMS

    def get_search_strategy(self, query_type: Optional[str] = None) -> list[CollectionType]:
        """
        根据查询类型获取最优的检索策略

        Args:
            query_type: 查询类型 ("patent_analysis", "legal_compliance", "technical_search")

        Returns:
            list[CollectionType]: 按优先级排序的集合列表
        """
        if query_type == "patent_analysis":
            # 专利分析:专利数据 -> 法规 -> 法律条款
            return [
                CollectionType.PATENTS_DATA,
                CollectionType.PATENT_RULES,
                CollectionType.LEGAL_CLAUSES,
            ]
        elif query_type == "legal_compliance":
            # 法律合规:法规 -> 法律条款 -> 案例数据
            return [
                CollectionType.PATENT_RULES,
                CollectionType.LEGAL_CLAUSES,
                CollectionType.CASE_DATA,
            ]
        elif query_type == "technical_search":
            # 技术搜索:技术术语 -> 专利数据
            return [CollectionType.TECHNICAL_TERMS, CollectionType.PATENTS_DATA]
        else:
            # 默认策略:按优先级排序
            return sorted(
                self.collection_configs.keys(),
                key=lambda x: self.collection_configs[x].priority,
                reverse=True,
            )

    def get_collection_info(self, collection_type: CollectionType) -> CollectionConfig:
        """获取集合配置信息"""
        return self.collection_configs.get(collection_type)

    def get_all_collections(self) -> dict[CollectionType, CollectionConfig]:
        """获取所有集合配置"""
        return self.collection_configs


# 全局单例
_collection_mapper = None


def get_collection_mapper() -> OptimizedCollectionMapper:
    """获取集合映射器单例"""
    global _collection_mapper
    if _collection_mapper is None:
        _collection_mapper = OptimizedCollectionMapper()
    return _collection_mapper


# 向后兼容的集合名称映射
LEGACY_COLLECTION_MAPPING = {
    "patent_rules_1024": CollectionType.PATENT_RULES,
    "legal_clauses_1024": CollectionType.LEGAL_CLAUSES,
    "technical_terms_1024": CollectionType.TECHNICAL_TERMS,
    "patents_data_1024": CollectionType.PATENTS_DATA,
    "legal_concepts_1024": CollectionType.LEGAL_CONCEPTS,
    "case_data_1024": CollectionType.CASE_DATA,
}


def migrate_legacy_collection_name(legacy_name: str) -> CollectionType:
    """迁移旧的集合名称到新的类型"""
    return LEGACY_COLLECTION_MAPPING.get(legacy_name, CollectionType.TECHNICAL_TERMS)

