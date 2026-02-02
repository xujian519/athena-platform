#!/usr/bin/env python3
"""
增强专利检索器 - 兼容性包装
Enhanced Patent Retriever - Compatibility Wrapper

为优化后的系统提供增强专利检索功能的兼容性接口
作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

import logging
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)


class EnhancedPatentRetriever:
    """增强专利检索器"""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.patent_adapter = None
        self.search_cache = {}
        self.initialized = False

    async def initialize(self):
        """初始化检索器"""
        if self.initialized:
            return

        try:
            # 导入专利搜索适配器
            from services.patent_services.athena_patent_search_adapter import (
                AthenaPatentSearchAdapter,
            )

            self.patent_adapter = AthenaPatentSearchAdapter(self.config)
            await self.patent_adapter.initialize()

            self.initialized = True
            logger.info("✅ 增强专利检索器初始化完成")

        except Exception as e:
            logger.error(f"❌ 增强专利检索器初始化失败: {e}")
            raise

    async def search_patents(self, query: str, **kwargs) -> dict[str, Any]:
        """
        智能专利搜索

        Args:
            query: 搜索查询
            **kwargs: 其他搜索参数

        Returns:
            搜索结果字典
        """
        if not self.initialized:
            await self.initialize()

        try:
            # 检查缓存
            cache_key = f"{query}_{hash(str(sorted(kwargs.items())))}"
            if cache_key in self.search_cache:
                logger.debug(f"从缓存返回结果: {query}")
                return self.search_cache[cache_key]

            # 执行搜索
            result = await self.patent_adapter.search_patents(query, **kwargs)

            # 增强结果
            enhanced_result = await self._enhance_search_result(result, query)

            # 缓存结果
            self.search_cache[cache_key] = enhanced_result

            logger.info(
                f"专利搜索完成: {query} -> {len(enhanced_result.get('patents', []))} 个结果"
            )
            return enhanced_result

        except Exception as e:
            logger.error(f"专利搜索失败: {query} - {e}")
            return {"success": False, "error": str(e), "patents": [], "query": query}

    async def _enhance_search_result(self, result: dict[str, Any], query: str) -> dict[str, Any]:
        """增强搜索结果"""
        enhanced = result.copy()

        # 添加元数据
        enhanced.update(
            {
                "search_time": datetime.now().isoformat(),
                "query": query,
                "enhanced": True,
                "confidence_score": self._calculate_confidence(result),
                "relevance_indicators": self._analyze_relevance(result, query),
            }
        )

        # 增强专利信息
        patents = enhanced.get("patents", [])
        for patent in patents:
            patent["enhanced_metadata"] = {
                "relevance_score": self._calculate_patent_relevance(patent, query),
                "innovation_level": self._assess_innovation_level(patent),
                "market_potential": self._assess_market_potential(patent),
            }

        return enhanced

    def _calculate_confidence(self, result: dict[str, Any]) -> float:
        """计算搜索置信度"""
        patents = result.get("patents", [])
        if not patents:
            return 0.0

        # 基于结果数量和质量计算置信度
        base_score = min(len(patents) / 10.0, 1.0)  # 基于数量
        quality_score = sum(1 for p in patents if p.get("abstract")) / len(patents)  # 基于质量

        return (base_score + quality_score) / 2

    def _analyze_relevance(self, result: dict[str, Any], query: str) -> list[str]:
        """分析相关性指标"""
        indicators = []

        patents = result.get("patents", [])
        query_terms = query.lower().split()

        # 分析关键词匹配
        for patent in patents[:5]:  # 只分析前5个结果
            title = patent.get("title", "").lower()
            abstract = patent.get("abstract", "").lower()

            title_matches = sum(1 for term in query_terms if term in title)
            abstract_matches = sum(1 for term in query_terms if term in abstract)

            if title_matches >= 2:
                indicators.append("strong_title_match")
            if abstract_matches >= 3:
                indicators.append("strong_content_match")

        return list(set(indicators))

    def _calculate_patent_relevance(self, patent: dict[str, Any], query: str) -> float:
        """计算专利相关性分数"""
        query_terms = query.lower().split()

        title = patent.get("title", "").lower()
        abstract = patent.get("abstract", "").lower()

        # 标题匹配权重更高
        title_score = sum(1 for term in query_terms if term in title) / len(query_terms)
        abstract_score = (
            sum(1 for term in query_terms if term in abstract) / len(query_terms) if abstract else 0
        )

        return title_score * 0.7 + abstract_score * 0.3

    def _assess_innovation_level(self, patent: dict[str, Any]) -> str:
        """评估创新级别"""
        # 简化的创新级别评估
        patent.get("claims", "")
        citations = patent.get("citations", [])

        if len(citations) > 10:
            return "high"
        elif len(citations) > 3:
            return "medium"
        else:
            return "low"

    def _assess_market_potential(self, patent: dict[str, Any]) -> str:
        """评估市场潜力"""
        # 简化的市场潜力评估
        classifications = patent.get("classifications", [])

        # 高价值领域
        high_value_fields = ["G06F", "H04L", "A61B", "C07D"]

        for classification in classifications:
            for field in high_value_fields:
                if classification.startswith(field):
                    return "high"

        return "medium"

    async def get_patent_details(self, patent_id: str) -> dict[str, Any]:
        """获取专利详细信息"""
        try:
            # 这里应该调用实际的专利详情API
            # 目前返回模拟数据
            return {
                "patent_id": patent_id,
                "title": f"Patent {patent_id}",
                "abstract": "Patent abstract...",
                "claims": ["Claim 1", "Claim 2"],
                "classifications": ["G06F 17/00"],
                "status": "active",
            }
        except Exception as e:
            logger.error(f"获取专利详情失败: {patent_id} - {e}")
            return {}

    async def clear_cache(self):
        """清空搜索缓存"""
        self.search_cache.clear()
        logger.info("搜索缓存已清空")


# 兼容性函数
def create_enhanced_patent_retriever(config: dict[str, Any] | None = None) -> EnhancedPatentRetriever:
    """创建增强专利检索器实例"""
    return EnhancedPatentRetriever(config)


# 向后兼容的别名
PatentRetriever = EnhancedPatentRetriever
