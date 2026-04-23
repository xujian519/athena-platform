#!/usr/bin/env python3
"""
PQAI专利检索算法集成模块
基于PQAI项目核心算法，为Athena平台提供增强的专利检索能力
"""

import logging
from dataclasses import dataclass
from typing import Any

import faiss
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import normalize

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """检索结果数据结构"""
    patent_id: str
    title: str
    abstract: str
    score: float
    similarity_type: str
    highlight_spans: list[str] = None
    explanation: str = ''

class PQAIEnhancedPatentSearcher:
        # 中文专利专用语义模型
        # 专门针对中文专利文本优化，提升检索准确性
        # 模型特点：
        # - 向量维度: 768 (更丰富的语义表示)
        # - 专门优化中文文本理解
        # - 适合专利、法律等专业领域
        # - 在中文相似度计算任务上表现优异

    """
    PQAI增强专利检索器

    集成PQAI项目的核心专利检索算法，包括：
    1. 多向量表示学习
    2. 混合检索策略
    3. 智能重排序
    4. 语义高亮
    """

    def __init__(self, model_name: str = 'shibing624/text2vec-base-chinese'):
        """
        初始化PQAI专利检索器

        Args:
            model_name: 预训练模型名称
        """
        self.model_name = model_name
        self.model = None
        self.index = None
        self.patent_data = []
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'

        # PQAI核心参数
        self.retrieval_top_k = 100  # 初始检索数量
        self.reranking_top_k = 20   # 重排序后数量
        self.similarity_threshold = 0.7  # 相似度阈值

        logger.info(f"PQAI专利检索器初始化完成，使用设备: {self.device}")

    def load_model(self) -> Any | None:
        """加载预训练模型"""
        try:
            self.model = SentenceTransformer(self.model_name)
            self.model.to(self.device)
            logger.info(f"成功加载模型: {self.model_name}")
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            raise

    def build_index(self, patent_texts: list[dict[str, Any]) -> Any:
        """
        构建专利检索索引

        Args:
            patent_texts: 专利数据列表，每项包含id, title, abstract等
        """
        if self.model is None:
            self.load_model()

        self.patent_data = patent_texts

        # 多向量表示（标题 + 摘要）
        title_texts = [p.get('title', '') for p in patent_texts]
        abstract_texts = [p.get('abstract', '') for p in patent_texts]
        combined_texts = [f"{title} {abstract}" for title, abstract in zip(title_texts, abstract_texts, strict=False)]

        logger.info(f"开始构建索引，专利数量: {len(patent_texts)}")

        # 编码向量
        with torch.no_grad():
            title_embeddings = self.model.encode(title_texts, convert_to_numpy=True)
            abstract_embeddings = self.model.encode(abstract_texts, convert_to_numpy=True)
            combined_embeddings = self.model.encode(combined_texts, convert_to_numpy=True)

        # 归一化向量
        title_embeddings = normalize(title_embeddings)
        abstract_embeddings = normalize(abstract_embeddings)
        combined_embeddings = normalize(combined_embeddings)

        # 构建FAISS索引
        dimension = combined_embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(combined_embeddings)

        # 存储所有嵌入
        self.title_embeddings = title_embeddings
        self.abstract_embeddings = abstract_embeddings
        self.combined_embeddings = combined_embeddings

        logger.info(f"索引构建完成，维度: {dimension}")

    def search(self, query: str, top_k: int = 20, search_type: str = 'hybrid') -> list[SearchResult]:
        """
        执行专利检索

        Args:
            query: 检索查询
            top_k: 返回结果数量
            search_type: 检索类型 (hybrid, semantic, keyword)

        Returns:
            检索结果列表
        """
        if self.index is None:
            raise ValueError('索引未构建，请先调用build_index方法')

        logger.info(f"开始检索，查询: '{query}', 检索类型: {search_type}")

        # 编码查询
        with torch.no_grad():
            query_embedding = self.model.encode([query], convert_to_numpy=True)
        query_embedding = normalize(query_embedding)

        if search_type == 'semantic':
            results = self._semantic_search(query_embedding, top_k)
        elif search_type == 'keyword':
            results = self._keyword_search(query, top_k)
        else:  # hybrid
            results = self._hybrid_search(query, query_embedding, top_k)

        # 重排序
        results = self._rerank_results(query, results)

        # 生成高亮和解释
        results = self._enhance_results(query, results)

        logger.info(f"检索完成，返回{len(results)}个结果")
        return results

    def _semantic_search(self, query_embedding: np.ndarray, top_k: int) -> list[SearchResult]:
        """语义检索"""
        scores, indices = self.index.search(query_embedding, min(self.retrieval_top_k, len(self.combined_embeddings)))

        results = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0], strict=False)):
            if i >= top_k or score < self.similarity_threshold:
                break

            patent = self.patent_data[idx]
            result = SearchResult(
                patent_id=patent.get('id', ''),
                title=patent.get('title', ''),
                abstract=patent.get('abstract', ''),
                score=float(score),
                similarity_type='semantic'
            )
            results.append(result)

        return results

    def _keyword_search(self, query: str, top_k: int) -> list[SearchResult]:
        """关键词检索（简化版）"""
        query_terms = query.lower().split()
        results = []

        for patent in self.patent_data:
            title = patent.get('title', '').lower()
            abstract = patent.get('abstract', '').lower()

            # 计算关键词匹配分数
            score = 0
            for term in query_terms:
                if term in title:
                    score += 2  # 标题匹配权重更高
                if term in abstract:
                    score += 1

            if score > 0:
                normalized_score = min(score / len(query_terms), 1.0)
                if normalized_score >= self.similarity_threshold:
                    result = SearchResult(
                        patent_id=patent.get('id', ''),
                        title=patent.get('title', ''),
                        abstract=patent.get('abstract', ''),
                        score=normalized_score,
                        similarity_type='keyword'
                    )
                    results.append(result)

        # 按分数排序
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    def _hybrid_search(self, query: str, query_embedding: np.ndarray, top_k: int) -> list[SearchResult]:
        """混合检索：语义 + 关键词"""
        # 获取语义检索结果
        semantic_results = self._semantic_search(query_embedding, self.retrieval_top_k)

        # 获取关键词检索结果
        keyword_results = self._keyword_search(query, self.retrieval_top_k)

        # 合并结果
        merged_results = {}

        # 添加语义结果
        for result in semantic_results:
            merged_results[result.patent_id] = result

        # 添加或更新关键词结果
        for result in keyword_results:
            if result.patent_id in merged_results:
                # 加权平均分数
                existing = merged_results[result.patent_id]
                existing.score = 0.7 * existing.score + 0.3 * result.score
                existing.similarity_type = 'hybrid'
            else:
                merged_results[result.patent_id] = result
                result.similarity_type = 'hybrid'

        # 排序并返回
        results = list(merged_results.values())
        results.sort(key=lambda x: x.score, reverse=True)

        return results[:top_k]

    def _rerank_results(self, query: str, results: list[SearchResult]) -> list[SearchResult]:
        """
        重排序检索结果

        使用更复杂的相似度计算方法重新排序
        """
        if len(results) <= self.reranking_top_k:
            return results

        # 计算更精细的相似度分数
        reranked_scores = []
        query_embedding = self.model.encode([query], convert_to_numpy=True)
        query_embedding = normalize(query_embedding)

        for result in results[:self.reranking_top_k]:
            # 多维度相似度计算
            patent_idx = next(i for i, p in enumerate(self.patent_data) if p.get('id') == result.patent_id)

            # 标题相似度
            title_sim = np.dot(query_embedding[0], self.title_embeddings[patent_idx])

            # 摘要相似度
            abstract_sim = np.dot(query_embedding[0], self.abstract_embeddings[patent_idx])

            # 综合相似度（标题权重更高）
            final_score = 0.6 * title_sim + 0.4 * abstract_sim

            reranked_scores.append((result, final_score))

        # 重新排序
        reranked_scores.sort(key=lambda x: x[1], reverse=True)

        final_results = []
        for result, new_score in reranked_scores:
            result.score = float(new_score)
            result.similarity_type = 'reranked'
            final_results.append(result)

        return final_results

    def _enhance_results(self, query: str, results: list[SearchResult]) -> list[SearchResult]:
        """
        增强检索结果：生成高亮和解释
        """
        for result in results:
            # 生成高亮片段
            result.highlight_spans = self._extract_highlights(query, result.abstract)

            # 生成解释
            result.explanation = self._generate_explanation(query, result)

        return results

    def _extract_highlights(self, query: str, text: str, max_spans: int = 3) -> list[str]:
        """提取高亮片段"""
        if not text:
            return []

        query_terms = query.lower().split()
        text_lower = text.lower()

        spans = []
        for term in query_terms:
            start = text_lower.find(term)
            if start != -1:
                end = start + len(term)
                context_start = max(0, start - 50)
                context_end = min(len(text), end + 50)
                span = text[context_start:context_end]
                if span not in spans:
                    spans.append(span)
                if len(spans) >= max_spans:
                    break

        return spans

    def _generate_explanation(self, query: str, result: SearchResult) -> str:
        """生成检索结果解释"""
        explanation_parts = []

        # 相似度分数解释
        if result.score >= 0.9:
            explanation_parts.append('高度相关 - 专利与查询内容高度匹配')
        elif result.score >= 0.7:
            explanation_parts.append('相关 - 专利内容与查询相关')
        else:
            explanation_parts.append('部分相关 - 专利内容与查询部分匹配')

        # 相似度类型解释
        if result.similarity_type == 'semantic':
            explanation_parts.append('基于语义相似度匹配')
        elif result.similarity_type == 'keyword':
            explanation_parts.append('基于关键词匹配')
        elif result.similarity_type == 'hybrid':
            explanation_parts.append('语义和关键词混合匹配')
        elif result.similarity_type == 'reranked':
            explanation_parts.append('经过智能重排序优化')

        return ' | '.join(explanation_parts)

    def get_statistics(self) -> dict[str, Any]:
        """获取检索器统计信息"""
        stats = {
            'total_patents': len(self.patent_data),
            'index_dimension': self.combined_embeddings.shape[1] if hasattr(self, 'combined_embeddings') else 0,
            'model_name': self.model_name,
            'device': self.device,
            'similarity_threshold': self.similarity_threshold,
            'retrieval_top_k': self.retrieval_top_k,
            'reranking_top_k': self.reranking_top_k
        }
        return stats
