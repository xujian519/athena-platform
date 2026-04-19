#!/usr/bin/env python3
from __future__ import annotations
"""
BM25稀疏检索模块
BM25 Sparse Retriever Module

实现BM25算法用于稀疏文本检索,与向量检索结合形成混合检索策略。
BM25是一种基于词频和文档频率的概率检索函数,在信息检索领域广泛使用。

算法公式:
score(D,Q) = Σ IDF(qi) * (f(qi,D) * (k1 + 1)) / (f(qi,D) + k1 * (1 - b + b * |D| / avgdl))

其中:
- qi: 查询中的词项
- D: 文档
- f(qi,D): 词项qi在文档D中的词频
- |D|: 文档长度(词数)
- avgdl: 平均文档长度
- k1: 词频饱和参数(通常1.2-2.0)
- b: 长度归一化参数(通常0.75)

作者: Athena AI系统
创建时间: 2026-01-25
版本: 1.0.0
"""

import logging
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class BM25Config:
    """BM25配置参数"""

    k1: float = 1.5  # 词频饱和参数,控制词频的影响
    b: float = 0.75  # 长度归一化参数,控制文档长度的影响
    epsilon: float = 0.25  # IDF下界,防止罕见词IDF过大
    max_doc_length: int = 10000  # 最大文档长度(超过会被截断)

    # 文本预处理配置
    lowercase: bool = True
    remove_punctuation: bool = True
    min_word_length: int = 2
    max_word_length: int = 30

    # 停用词配置
    use_stopwords: bool = True
    custom_stopwords: set[str] = field(default_factory=set)

    # 语言配置
    language: str = "chinese"  # chinese, english, mixed

    def validate(self) -> bool:
        """验证配置"""
        if self.k1 < 0:
            raise ValueError(f"k1必须 >= 0,当前值: {self.k1}")
        if not (0 <= self.b <= 1):
            raise ValueError(f"b必须在[0,1]范围内,当前值: {self.b}")
        if self.epsilon < 0:
            raise ValueError(f"epsilon必须 >= 0,当前值: {self.epsilon}")
        return True


@dataclass
class Document:
    """文档表示"""

    doc_id: str
    content: str
    tokens: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SearchResult:
    """检索结果"""

    doc_id: str
    score: float
    document: Document | None = None
    matched_terms: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class BM25Retriever:
    """BM25检索器

    实现BM25算法进行稀疏文本检索。

    使用示例:
        >>> retriever = BM25Retriever()
        >>> documents = [
        ...     Document("doc1", "这是一个关于人工智能的专利"),
        ...     Document("doc2", "深度学习在计算机视觉中的应用"),
        ... ]
        >>> retriever.add_documents(documents)
        >>> results = retriever.search("人工智能 深度学习", top_k=5)
        >>> for result in results:
        ...     print(f"{result.doc_id}: {result.score:.4f}")
    """

    def __init__(self, config: BM25Config | None = None):
        """初始化BM25检索器

        Args:
            config: BM25配置参数
        """
        self.config = config or BM25Config()
        self.config.validate()

        # 文档存储
        self.documents: dict[str, Document] = {}

        # 索引结构
        self.doc_freqs: dict[str, int] = {}  # 词项 -> 包含该词项的文档数
        self.doc_lengths: dict[str, int] = {}  # doc_id -> 文档长度
        self.avg_doc_length: float = 0.0  # 平均文档长度

        # 预处理后的停用词
        self.stopwords = self._get_stopwords()

        logger.info(f"✅ BM25检索器初始化完成 (k1={self.config.k1}, b={self.config.b})")

    def _get_stopwords(self) -> set[str]:
        """获取停用词表"""
        if not self.config.use_stopwords:
            return set()

        # 基础停用词
        stopwords = {
            # 中文停用词
            "的",
            "了",
            "在",
            "是",
            "我",
            "有",
            "和",
            "就",
            "不",
            "人",
            "都",
            "一",
            "一个",
            "上",
            "也",
            "很",
            "到",
            "说",
            "要",
            "去",
            "你",
            "会",
            "着",
            "没有",
            "看",
            "好",
            "自己",
            "这",
            # 英文停用词
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
        }

        # 添加自定义停用词
        stopwords.update(self.config.custom_stopwords)

        return stopwords

    def _preprocess_text(self, text: str) -> list[str]:
        """预处理文本

        Args:
            text: 原始文本

        Returns:
            分词后的token列表
        """
        # 转小写
        if self.config.lowercase:
            text = text.lower()

        # 移除标点符号
        if self.config.remove_punctuation:
            text = re.sub(r"[^\w\s]", " ", text)

        # 分词
        if self.config.language == "chinese":
            # 简单的中文分词(按字符)
            tokens = [c for c in text if c.strip()]
        elif self.config.language == "english":
            # 英文按空格分词
            tokens = text.split()
        else:  # mixed
            # 混合模式:先按空格分,再对每个词进一步切分
            tokens = []
            for word in text.split():
                if re.search(r"[\u4e00-\u9fff]", word):
                    # 包含中文,按字符切分
                    tokens.extend([c for c in word if c.strip()])
                else:
                    tokens.append(word)

        # 过滤停用词
        if self.stopwords:
            tokens = [t for t in tokens if t not in self.stopwords]

        # 长度过滤
        tokens = [
            t
            for t in tokens
            if self.config.min_word_length <= len(t) <= self.config.max_word_length
        ]

        return tokens

    def add_documents(self, documents: list[Document]) -> None:
        """添加文档到索引

        Args:
            documents: 文档列表
        """
        if not documents:
            return

        total_length = 0

        for doc in documents:
            # 预处理
            if not doc.tokens:
                doc.tokens = self._preprocess_text(doc.content)

            # 截断过长文档
            if len(doc.tokens) > self.config.max_doc_length:
                doc.tokens = doc.tokens[: self.config.max_doc_length]

            # 存储文档
            self.documents[doc.doc_id] = doc

            # 记录文档长度
            doc_length = len(doc.tokens)
            self.doc_lengths[doc.doc_id] = doc_length
            total_length += doc_length

            # 更新词项文档频率
            unique_tokens = set(doc.tokens)
            for token in unique_tokens:
                self.doc_freqs[token] = self.doc_freqs.get(token, 0) + 1

        # 更新平均文档长度
        if self.documents:
            self.avg_doc_length = total_length / len(self.documents)

        logger.info(f"✅ 添加了 {len(documents)} 个文档,总计 {len(self.documents)} 个文档")

    def _calculate_idf(self, token: str) -> float:
        """计算逆文档频率(IDF)

        Args:
            token: 词项

        Returns:
            IDF值
        """
        n = len(self.documents)
        df = self.doc_freqs.get(token, 0)

        # 避免除零
        if df == 0:
            df = 1

        # 使用平滑IDF
        idf = math.log((n - df + 0.5) / (df + 0.5) + 1)

        # 应用IDF下界
        return max(idf, math.log(self.config.epsilon + 1))

    def _calculate_score(self, query_tokens: list[str], doc_id: str) -> tuple[float, list[str]]:
        """计算BM25分数

        Args:
            query_tokens: 查询词项列表
            doc_id: 文档ID

        Returns:
            (BM25分数, 匹配的词项列表)
        """
        if doc_id not in self.documents:
            return 0.0, []

        document = self.documents[doc_id]
        doc_length = self.doc_lengths[doc_id]

        # 计算词频
        token_freqs = Counter(document.tokens)

        score = 0.0
        matched_terms = []

        for token in query_tokens:
            if token not in token_freqs:
                continue

            # 词频
            freq = token_freqs[token]

            # IDF
            idf = self._calculate_idf(token)

            # BM25公式
            numerator = freq * (self.config.k1 + 1)
            denominator = freq + self.config.k1 * (
                1 - self.config.b + self.config.b * doc_length / self.avg_doc_length
            )

            score += idf * (numerator / denominator)
            matched_terms.append(token)

        return score, matched_terms

    def search(
        self,
        query: str,
        top_k: int = 10,
        min_score: float = 0.0,
    ) -> list[SearchResult]:
        """搜索文档

        Args:
            query: 查询文本
            top_k: 返回前k个结果
            min_score: 最小分数阈值

        Returns:
            检索结果列表,按分数降序排列
        """
        if not self.documents:
            logger.warning("⚠️ 没有文档可供搜索")
            return []

        # 预处理查询
        query_tokens = self._preprocess_text(query)

        if not query_tokens:
            logger.warning("⚠️ 查询为空或被停用词过滤")
            return []

        logger.debug(f"🔍 搜索查询: {query_tokens}")

        # 计算所有文档的分数
        results = []
        for doc_id in self.documents:
            score, matched_terms = self._calculate_score(query_tokens, doc_id)

            if score >= min_score:
                results.append(
                    SearchResult(
                        doc_id=doc_id,
                        score=score,
                        document=self.documents[doc_id],
                        matched_terms=matched_terms,
                    )
                )

        # 按分数排序
        results.sort(key=lambda r: r.score, reverse=True)

        # 返回top_k结果
        return results[:top_k]

    def batch_search(
        self,
        queries: list[str],
        top_k: int = 10,
        min_score: float = 0.0,
    ) -> list[list[SearchResult]]:
        """批量搜索

        Args:
            queries: 查询列表
            top_k: 每个查询返回前k个结果
            min_score: 最小分数阈值

        Returns:
            检索结果列表(每个查询对应一个结果列表)
        """
        return [self.search(query, top_k, min_score) for query in queries]

    def get_document(self, doc_id: str) -> Document | None:
        """获取文档

        Args:
            doc_id: 文档ID

        Returns:
            文档对象,如果不存在返回None
        """
        return self.documents.get(doc_id)

    def delete_document(self, doc_id: str) -> bool:
        """删除文档

        Args:
            doc_id: 文档ID

        Returns:
            是否删除成功
        """
        if doc_id not in self.documents:
            return False

        document = self.documents[doc_id]

        # 更新词项文档频率
        unique_tokens = set(document.tokens)
        for token in unique_tokens:
            if token in self.doc_freqs:
                self.doc_freqs[token] -= 1
                if self.doc_freqs[token] == 0:
                    del self.doc_freqs[token]

        # 删除文档
        del self.documents[doc_id]
        del self.doc_lengths[doc_id]

        # 重新计算平均文档长度
        if self.documents:
            total_length = sum(self.doc_lengths.values())
            self.avg_doc_length = total_length / len(self.documents)
        else:
            self.avg_doc_length = 0.0

        logger.info(f"🗑️ 删除文档: {doc_id}")
        return True

    def clear(self) -> None:
        """清空所有文档"""
        self.documents.clear()
        self.doc_freqs.clear()
        self.doc_lengths.clear()
        self.avg_doc_length = 0.0
        logger.info("🧹 已清空所有文档")

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息

        Returns:
            统计信息字典
        """
        return {
            "total_documents": len(self.documents),
            "total_unique_tokens": len(self.doc_freqs),
            "avg_doc_length": self.avg_doc_length,
            "avg_doc_length_words": f"{self.avg_doc_length:.2f}",
            "min_doc_length": min(self.doc_lengths.values()) if self.doc_lengths else 0,
            "max_doc_length": max(self.doc_lengths.values()) if self.doc_lengths else 0,
            "config": {
                "k1": self.config.k1,
                "b": self.config.b,
                "language": self.config.language,
            },
        }


class HybridRetriever:
    """混合检索器(BM25 + 向量检索)

    结合稀疏检索(BM25)和密集检索(向量检索)的优势,
    通过加权融合提供更好的检索效果。

    公式:
    final_score = α * dense_score + β * sparse_score

    其中:
    - dense_score: 向量检索的余弦相似度
    - sparse_score: BM25分数(归一化后)
    - α, β: 权重参数(α + β = 1)
    """

    def __init__(
        self,
        bm25_retriever: BM25Retriever,
        alpha: float = 0.5,  # 密集检索权重
        beta: float = 0.5,  # 稀疏检索权重
    ):
        """初始化混合检索器

        Args:
            bm25_retriever: BM25检索器
            alpha: 密集检索权重
            beta: 稀疏检索权重
        """
        if abs(alpha + beta - 1.0) > 0.01:
            raise ValueError(f"alpha + beta应该等于1,当前值: {alpha + beta}")

        self.bm25_retriever = bm25_retriever
        self.alpha = alpha
        self.beta = beta

        logger.info(f"✅ 混合检索器初始化完成 (α={alpha}, β={beta})")

    def search(
        self,
        query: str,
        dense_results: list[tuple[str, float]],  # (doc_id, score) 列表
        top_k: int = 10,
    ) -> list[tuple[str, float]]:
        """混合搜索

        Args:
            query: 查询文本
            dense_results: 密集检索结果 [(doc_id, score), ...]
            top_k: 返回前k个结果

        Returns:
            混合检索结果 [(doc_id, final_score), ...]
        """
        # BM25检索
        sparse_results = self.bm25_retriever.search(query, top_k=top_k * 2)

        # 归一化BM25分数
        if sparse_results:
            max_sparse_score = max(r.score for r in sparse_results)
            sparse_scores = {
                r.doc_id: (r.score / max_sparse_score if max_sparse_score > 0 else 0)
                for r in sparse_results
            }
        else:
            sparse_scores = {}

        # 归一化密集检索分数(假设是余弦相似度,已经在[0,1]范围)
        dense_scores = dict(dense_results)

        # 融合分数
        all_doc_ids = set(dense_scores.keys()) | set(sparse_scores.keys())
        final_scores = []

        for doc_id in all_doc_ids:
            dense_score = dense_scores.get(doc_id, 0.0)
            sparse_score = sparse_scores.get(doc_id, 0.0)

            final_score = self.alpha * dense_score + self.beta * sparse_score
            final_scores.append((doc_id, final_score))

        # 排序并返回top_k
        final_scores.sort(key=lambda x: x[1], reverse=True)
        return final_scores[:top_k]


# 便捷函数
def create_bm25_retriever(config: BM25Config | None = None) -> BM25Retriever:
    """创建BM25检索器"""
    return BM25Retriever(config)


def create_hybrid_retriever(
    bm25_config: BM25Config | None = None,
    alpha: float = 0.5,
    beta: float = 0.5,
) -> HybridRetriever:
    """创建混合检索器"""
    bm25_retriever = BM25Retriever(bm25_config)
    return HybridRetriever(bm25_retriever, alpha, beta)


__all__ = [
    "BM25Config",
    "BM25Retriever",
    "Document",
    "HybridRetriever",
    "SearchResult",
    "create_bm25_retriever",
    "create_hybrid_retriever",
]
