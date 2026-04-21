#!/usr/bin/env python3
from __future__ import annotations
"""
负熵优化的专利检索系统
Negentropy-Optimized Patent Retrieval System

基于薛定谔"生命以负熵为食"思想构建的专利检索系统:
- 从混乱的检索结果中建立有序的排名
- 负熵 = 信息熵减 = 检索质量提升
- 综合相关性、技术相似度、法律状态等多维排序
- 智能去重和结果优化

作者: 小诺·双鱼公主
创建时间: 2025-12-24
版本: v0.1.2 "晨星初现"
"""

import json
import logging

# 导入负熵优化器
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.biology.negentropy_optimizer import get_negentropy_optimizer
from patents.core.ipc_vector_database import IPCMatchResult, get_ipc_vector_db

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class RetrievalMethod(Enum):
    """检索方法"""

    KEYWORD = "keyword"  # 关键词检索
    SEMANTIC = "semantic"  # 语义检索
    HYBRID = "hybrid"  # 混合检索


class LegalStatus(Enum):
    """法律状态"""

    GRANTED = "granted"  # 已授权
    PENDING = "pending"  # 审查中
    REJECTED = "rejected"  # 驳回
    EXPIRED = "expired"  # 过期
    WITHDRAWN = "withdrawn"  # 撤回


@dataclass
class PatentDocument:
    """专利文档"""

    patent_id: str  # 专利号
    title: str  # 标题
    abstract: str  # 摘要
    claims: list[str]  # 权利要求
    description: str  # 说明书

    # 元数据
    technical_field: str  # 技术领域
    legal_status: LegalStatus  # 法律状态
    application_date: str  # 申请日期
    publication_date: str  # 公开日期

    # 检索相关
    relevance_score: float = 0.0  # 相关性得分
    technical_similarity: float = 0.0  # 技术相似度
    legal_value: float = 0.5  # 法律价值

    # 负熵相关
    information_entropy: float = 0.0  # 信息熵
    negentropy_score: float = 0.0  # 负熵分数


@dataclass
class RetrievalQuery:
    """检索查询"""

    query_text: str  # 查询文本
    technical_field: str  # 技术领域
    keywords: list[str]  # 关键词
    retrieval_method: RetrievalMethod = RetrievalMethod.HYBRID

    # 约束条件
    legal_status_filter: list[LegalStatus] = field(default_factory=list)
    date_range: tuple[str, str] | None = None  # (start_date, end_date)

    # 权重配置
    weight_relevance: float = 0.4
    weight_similarity: float = 0.3
    weight_legal: float = 0.2
    weight_negentropy: float = 0.1


@dataclass
class RetrievalResult:
    """检索结果"""

    query: RetrievalQuery
    results: list[PatentDocument]
    total_count: int
    retrieval_time: float

    # 负熵指标
    input_entropy: float  # 输入熵
    output_entropy: float  # 输出熵(排序后)
    negentropy: float  # 负熵增益
    ordering_quality: float  # 排序质量

    # 统计信息
    avg_relevance: float
    avg_similarity: float
    legal_status_dist: dict[str, int]

    # IPC分类信息(新增)
    ipc_matches: list[IPCMatchResult] = field(default_factory=list)  # IPC匹配结果
    primary_ipc: str = ""  # 主IPC分类
    suggested_domains: list[str] = field(default_factory=list)  # 建议技术领域


class NegentropyRetrievalSystem:
    """
    负熵优化的专利检索系统

    核心思想:
    1. 初始检索结果 = 高熵(混乱)
    2. 负熵优化排序 = 低熵(有序)
    3. 负熵增益 = 信息熵减 = 检索质量提升
    """

    def __init__(self):
        """初始化检索系统"""
        self.name = "负熵优化的专利检索系统"
        self.version = "v0.1.2"

        # 负熵优化器
        self.negentropy_optimizer = get_negentropy_optimizer()

        # IPC向量数据库
        self.ipc_db = get_ipc_vector_db()

        # 专利数据库(模拟)
        self.patent_db: dict[str, PatentDocument] = {}

        # 检索历史
        self.retrieval_history: list[RetrievalResult] = []

        logger.info(f"🔍 {self.name} ({self.version}) 初始化完成")

    def add_patent(self, patent: PatentDocument) -> None:
        """添加专利到数据库"""
        self.patent_db[patent.patent_id] = patent
        logger.debug(f"添加专利: {patent.patent_id} - {patent.title}")

    def retrieve(self, query: RetrievalQuery) -> RetrievalResult:
        """
        执行检索

        Args:
            query: 检索查询

        Returns:
            检索结果
        """
        start_time = datetime.now()

        # 第1步:初始检索(高熵状态)
        raw_results = self._initial_retrieve(query)

        # 计算输入熵
        input_scores = [r.relevance_score for r in raw_results]
        input_entropy = self.negentropy_optimizer.calculate_information_entropy(
            input_scores, normalize=False
        )

        # 第2步:负熵优化排序
        optimized_results = self._negentropy_optimize(raw_results, query)

        # 计算输出熵
        output_scores = [r.relevance_score for r in optimized_results]
        output_entropy = self.negentropy_optimizer.calculate_information_entropy(
            output_scores, normalize=False
        )

        # 计算负熵增益
        negentropy = max(0, input_entropy - output_entropy)

        # 计算排序质量
        ordering_quality = self._calculate_ordering_quality(optimized_results, query)

        retrieval_time = (datetime.now() - start_time).total_seconds()

        # 统计信息
        avg_relevance = (
            sum(r.relevance_score for r in optimized_results) / len(optimized_results)
            if optimized_results
            else 0
        )
        avg_similarity = (
            sum(r.technical_similarity for r in optimized_results) / len(optimized_results)
            if optimized_results
            else 0
        )
        legal_status_dist = Counter(r.legal_status.value for r in optimized_results)

        result = RetrievalResult(
            query=query,
            results=optimized_results,
            total_count=len(raw_results),
            retrieval_time=retrieval_time,
            input_entropy=input_entropy,
            output_entropy=output_entropy,
            negentropy=negentropy,
            ordering_quality=ordering_quality,
            avg_relevance=avg_relevance,
            avg_similarity=avg_similarity,
            legal_status_dist=dict(legal_status_dist),
        )

        # 记录历史
        self.retrieval_history.append(result)

        logger.info(
            f"🔍 检索完成: {len(result.results)} 条结果 "
            f"(负熵增益: {negentropy:.3f}, 质量评分: {ordering_quality:.2f})"
        )

        return result

    def _initial_retrieve(self, query: RetrievalQuery) -> list[PatentDocument]:
        """初始检索(模拟)"""
        results = []

        # 简化的检索逻辑
        for patent in self.patent_db.values():
            # 技术领域筛选
            if query.technical_field and patent.technical_field != query.technical_field:
                continue

            # 法律状态筛选
            if query.legal_status_filter:
                if patent.legal_status not in query.legal_status_filter:
                    continue

            # 计算初始相关性
            relevance = self._calculate_relevance(query, patent)

            if relevance > 0.1:  # 阈值
                # 计算技术相似度
                similarity = self._calculate_technical_similarity(query, patent)

                # 计算法律价值
                legal_value = self._calculate_legal_value(patent)

                # 计算信息熵
                entropy = self._calculate_patent_entropy(patent)

                patent.relevance_score = relevance
                patent.technical_similarity = similarity
                patent.legal_value = legal_value
                patent.information_entropy = entropy

                results.append(patent)

        # 初始按相关性排序
        results.sort(key=lambda p: p.relevance_score, reverse=True)

        return results

    def _calculate_relevance(self, query: RetrievalQuery, patent: PatentDocument) -> float:
        """计算相关性得分"""
        score = 0.0

        query_lower = query.query_text.lower()
        title_lower = patent.title.lower()
        abstract_lower = patent.abstract.lower()

        # 标题匹配(权重: 40%)
        if query_lower in title_lower:
            score += 0.4
        for kw in query.keywords:
            if kw.lower() in title_lower:
                score += 0.1

        # 摘要匹配(权重: 30%)
        if query_lower in abstract_lower:
            score += 0.3
        for kw in query.keywords:
            if kw.lower() in abstract_lower:
                score += 0.05

        # 关键词匹配(权重: 30%)
        matches = sum(1 for kw in query.keywords if kw.lower() in abstract_lower)
        if matches > 0:
            score += min(0.3, matches * 0.1)

        return min(1.0, score)

    def _calculate_technical_similarity(
        self, query: RetrievalQuery, patent: PatentDocument
    ) -> float:
        """计算技术相似度"""
        # 简化实现:基于技术领域和关键词重叠
        base_similarity = 0.7 if patent.technical_field == query.technical_field else 0.3

        # 关键词重叠
        patent_words = set((patent.title + " " + patent.abstract).lower().split())
        query_words = {kw.lower() for kw in query.keywords}

        if patent_words and query_words:
            overlap = len(patent_words & query_words)
            union = len(patent_words | query_words)
            jaccard = overlap / union if union > 0 else 0
            base_similarity += jaccard * 0.3

        return min(1.0, base_similarity)

    def _calculate_legal_value(self, patent: PatentDocument) -> float:
        """计算法律价值"""
        values = {
            LegalStatus.GRANTED: 1.0,
            LegalStatus.PENDING: 0.7,
            LegalStatus.REJECTED: 0.1,
            LegalStatus.EXPIRED: 0.3,
            LegalStatus.WITHDRAWN: 0.2,
        }
        return values.get(patent.legal_status, 0.5)

    def _calculate_patent_entropy(self, patent: PatentDocument) -> float:
        """计算单个专利的信息熵"""
        # 基于权利要求计算熵
        if not patent.claims:
            return 0.0

        # 简化:使用权利要求长度分布
        claim_lengths = [len(claim.split()) for claim in patent.claims]

        return self.negentropy_optimizer.calculate_information_entropy(
            claim_lengths, normalize=True
        )

    def _negentropy_optimize(
        self, raw_results: list[PatentDocument], query: RetrievalQuery
    ) -> list[PatentDocument]:
        """负熵优化排序"""
        for patent in raw_results:
            # 计算综合得分
            patent.negentropy_score = (
                patent.relevance_score * query.weight_relevance
                + patent.technical_similarity * query.weight_similarity
                + patent.legal_value * query.weight_legal
                + (1 - patent.information_entropy) * query.weight_negentropy
            )

        # 按综合得分排序(有序 = 低熵)
        optimized = sorted(raw_results, key=lambda p: p.negentropy_score, reverse=True)

        # 去重(基于相似度)
        deduplicated = self._deduplicate(optimized)

        return deduplicated

    def _deduplicate(
        self, patents: list[PatentDocument], similarity_threshold: float = 0.9
    ) -> list[PatentDocument]:
        """去重"""
        if not patents:
            return []

        unique = [patents[0]]

        for patent in patents[1:]:
            # 检查是否与已有专利过于相似
            is_duplicate = False
            for existing in unique:
                if patent.technical_similarity > similarity_threshold:
                    # 保留得分更高的
                    if patent.negentropy_score > existing.negentropy_score:
                        unique.remove(existing)
                        unique.append(patent)
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique.append(patent)

        return unique

    def _calculate_ordering_quality(
        self, results: list[PatentDocument], query: RetrievalQuery
    ) -> float:
        """计算排序质量"""
        if not results:
            return 0.0

        # 质量指标:高分结果集中在前面
        weights = []
        for i, patent in enumerate(results):
            # 位置权重:前面权重更高
            position_weight = 1.0 / (1 + i * 0.1)
            weights.append(patent.negentropy_score * position_weight)

        # 归一化
        max_weight = len(results)
        quality = sum(weights) / max_weight if max_weight > 0 else 0

        return quality

    # ========== IPC增强检索方法 ==========

    def retrieve_with_ipc(self, query: RetrievalQuery) -> RetrievalResult:
        """
        IPC增强检索:结合IPC分类的智能检索

        Args:
            query: 检索查询

        Returns:
            增强检索结果(包含IPC分类信息)
        """
        # 1. 执行常规检索
        result = self.retrieve(query)

        # 2. IPC分类分析
        query_text = f"{query.query_text} {' '.join(query.keywords)}"
        ipc_matches = self.ipc_db.search_by_text(query_text, top_n=5, section_filter=None)

        # 3. 提取主IPC和建议领域
        if ipc_matches:
            result.primary_ipc = ipc_matches[0].ipc_entry.ipc_code

            # 获取领域建议
            classification = self.ipc_db.classify_patent(query_text)
            result.suggested_domains = classification.domain_suggestions

        result.ipc_matches = ipc_matches

        return result

    def classify_patent_domain(self, patent_text: str) -> dict[str, Any]:
        """
        对专利文本进行技术领域分类

        Args:
            patent_text: 专利文本

        Returns:
            分类结果
        """
        classification = self.ipc_db.classify_patent(patent_text)

        return {
            "primary_ipc": classification.primary_classification,
            "secondary_ipcs": classification.secondary_classifications,
            "suggested_domains": classification.domain_suggestions,
            "confidence": classification.confidence,
            "negentropy_score": classification.negentropy_score,
            "matched_ipcs": [
                {
                    "ipc_code": m.ipc_entry.ipc_code,
                    "ipc_name": m.ipc_entry.ipc_name,
                    "similarity": m.similarity_score,
                }
                for m in classification.matched_ipcs[:5]
            ],
        }

    def get_ipc_by_patent_text(self, patent_text: str, top_n: int = 3) -> list[dict[str, Any]]:
        """
        根据专利文本获取IPC分类推荐

        Args:
            patent_text: 专利文本
            top_n: 返回前N个

        Returns:
            IPC推荐列表
        """
        matches = self.ipc_db.search_by_text(patent_text, top_n=top_n)

        return [
            {
                "ipc_code": m.ipc_entry.ipc_code,
                "ipc_name": m.ipc_entry.ipc_name,
                "ipc_description": m.ipc_entry.ipc_description,
                "similarity": m.similarity_score,
                "confidence": m.confidence,
                "keywords": m.suggested_keywords,
            }
            for m in matches
        ]

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "total_patents": len(self.patent_db),
            "total_retrievals": len(self.retrieval_history),
            "avg_negentropy_gain": (
                sum(r.negentropy for r in self.retrieval_history) / len(self.retrieval_history)
                if self.retrieval_history
                else 0
            ),
            "avg_ordering_quality": (
                sum(r.ordering_quality for r in self.retrieval_history)
                / len(self.retrieval_history)
                if self.retrieval_history
                else 0
            ),
        }


# 全局单例
_negentropy_retrieval_instance = None


def get_negentropy_retrieval_system() -> NegentropyRetrievalSystem:
    """获取负熵检索系统单例"""
    global _negentropy_retrieval_instance
    if _negentropy_retrieval_instance is None:
        _negentropy_retrieval_instance = NegentropyRetrievalSystem()
    return _negentropy_retrieval_instance


# 测试代码
async def main():
    """测试负熵检索系统"""

    print("\n" + "=" * 60)
    print("🔍 负熵优化的专利检索系统测试")
    print("=" * 60 + "\n")

    # 初始化系统
    system = get_negentropy_retrieval_system()

    # 添加测试数据
    print("📝 测试1: 添加专利数据")

    test_patents = [
        PatentDocument(
            patent_id="CN202310000001",
            title="基于深度学习的图像识别方法",
            abstract="本发明公开了一种基于深度学习的图像识别方法...",
            claims=["1. 一种图像识别方法,其特征在于..."],
            description="本发明涉及图像处理领域...",
            technical_field="计算机视觉",
            legal_status=LegalStatus.GRANTED,
            application_date="2023-01-01",
            publication_date="2023-07-01",
        ),
        PatentDocument(
            patent_id="CN202310000002",
            title="图像识别中的特征提取方法",
            abstract="本发明公开了一种图像特征提取方法...",
            claims=["1. 一种特征提取方法,其特征在于..."],
            description="本发明涉及计算机视觉领域...",
            technical_field="计算机视觉",
            legal_status=LegalStatus.PENDING,
            application_date="2023-02-01",
            publication_date="2023-08-01",
        ),
        PatentDocument(
            patent_id="CN202310000003",
            title="基于卷积神经网络的图像分类",
            abstract="本发明公开了一种基于CNN的图像分类方法...",
            claims=["1. 一种图像分类方法,其特征在于..."],
            description="本发明涉及深度学习领域...",
            technical_field="深度学习",
            legal_status=LegalStatus.GRANTED,
            application_date="2023-03-01",
            publication_date="2023-09-01",
        ),
    ]

    for patent in test_patents:
        system.add_patent(patent)

    print(f"✅ 已添加 {len(test_patents)} 条专利\n")

    # 执行检索
    print("📝 测试2: 执行检索")

    query = RetrievalQuery(
        query_text="深度学习图像识别",
        technical_field="计算机视觉",
        keywords=["深度学习", "图像识别", "特征提取"],
        retrieval_method=RetrievalMethod.HYBRID,
    )

    result = system.retrieve(query)

    print(f"检索到 {result.total_count} 条结果,优化后 {len(result.results)} 条")
    print(f"检索时间: {result.retrieval_time:.3f}秒")
    print(f"输入熵: {result.input_entropy:.3f}")
    print(f"输出熵: {result.output_entropy:.3f}")
    print(f"负熵增益: {result.negentropy:.3f}")
    print(f"排序质量: {result.ordering_quality:.2f}\n")

    # 显示结果
    print("📝 检索结果:")
    for i, patent in enumerate(result.results, 1):
        print(f"{i}. {patent.title} [{patent.legal_status.value}]")
        print(
            f"   相关性: {patent.relevance_score:.2f}, "
            f"相似度: {patent.technical_similarity:.2f}, "
            f"综合得分: {patent.negentropy_score:.2f}"
        )
    print()

    # 统计信息
    print("📝 测试3: 统计信息")

    stats = system.get_statistics()
    print(json.dumps(stats, ensure_ascii=False, indent=2))

    print("\n✅ 测试完成!")


# 入口点: @async_main装饰器已添加到main函数
