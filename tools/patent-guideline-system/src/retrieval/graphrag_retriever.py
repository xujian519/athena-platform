#!/usr/bin/env python3
"""
GraphRAG检索器
GraphRAG Retriever

结合向量搜索和知识图谱的混合检索
"""

import logging
import os

# 导入安全配置
import sys
from pathlib import Path
from typing import Any

import jieba
import numpy as np
from neo4j import GraphDatabase
from qdrant_client import QdrantClient
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

sys.path.append(str(Path(__file__).parent.parent / "core"))

# 配置日志
logger = logging.getLogger(__name__)

class GraphRAGRetriever:
    """GraphRAG检索器"""

    def __init__(
        self,
        neo4j_uri='bolt://localhost:7687',
        neo4j_user='neo4j',
        neo4j_password=os.getenv("DB_PASSWORD", "password"),
        qdrant_host='localhost',
        qdrant_port=6333,
        embedding_model='BAAI/bge-large-zh-v1.5'
    ):
        """初始化检索器

        Args:
            neo4j_uri: Neo4j URI
            neo4j_user: Neo4j用户名
            neo4j_password: Neo4j密码
            qdrant_host: Qdrant主机
            qdrant_port: Qdrant端口
            embedding_model: 向量化模型
        """
        # Neo4j连接
        self.neo4j_driver = GraphDatabase.driver(
            neo4j_uri,
            auth=(neo4j_user, neo4j_password)
        )

        # Qdrant客户端
        self.qdrant_client = QdrantClient(
            host=qdrant_host,
            port=qdrant_port
        )

        # 向量化模型
        self.embedding_model = SentenceTransformer(embedding_model)
        self.embedding_dim = 1024

        # BM25索引
        self.bm25_corpus = []
        self.bm25_index = None

        # 初始化
        self._initialize()

    def _initialize(self):
        """初始化系统"""
        logger.info('初始化GraphRAG检索系统...')

        # 确保Qdrant集合存在
        collection_name = 'patent_guidelines'
        if not self.qdrant_client.collection_exists(collection_name):
            self.qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config={
                    'size': self.embedding_dim,
                    'distance': 'Cosine'
                }
            )
            logger.info(f"创建Qdrant集合: {collection_name}")

        # 加载BM25语料库
        self._load_bm25_corpus()

        logger.info('GraphRAG检索系统初始化完成')

    def search(
        self,
        query: str,
        top_k: int = 5,
        use_vector: bool = True,
        use_graph: bool = True,
        use_bm25: bool = True,
        alpha: float = 0.5
    ) -> dict[str, Any]:
        """执行GraphRAG检索

        Args:
            query: 查询文本
            top_k: 返回结果数量
            use_vector: 是否使用向量搜索
            use_graph: 是否使用图搜索
            use_bm25: 是否使用BM25搜索
            alpha: 向量和图搜索的融合权重

        Returns:
            检索结果
        """
        logger.info(f"执行GraphRAG检索: {query}")

        results = {
            'query': query,
            'vector_results': [],
            'graph_results': [],
            'bm25_results': [],
            'combined_results': [],
            'explanations': []
        }

        # 1. 向量搜索
        if use_vector:
            vector_results = self._vector_search(query, top_k)
            results['vector_results'] = vector_results
            results['explanations'].append(f"向量搜索找到 {len(vector_results)} 个相关段落")

        # 2. 图搜索
        if use_graph:
            graph_results = self._graph_search(query, top_k)
            results['graph_results'] = graph_results
            results['explanations'].append(f"图搜索找到 {len(graph_results)} 个相关节点")

        # 3. BM25搜索
        if use_bm25 and self.bm25_index:
            bm25_results = self._bm25_search(query, top_k)
            results['bm25_results'] = bm25_results
            results['explanations'].append(f"BM25搜索找到 {len(bm25_results)} 个匹配项")

        # 4. 融合结果
        combined = self._combine_results(
            results['vector_results'],
            results['graph_results'],
            results['bm25_results'],
            alpha
        )
        results['combined_results'] = combined[:top_k]

        return results

    def _vector_search(self, query: str, top_k: int) -> list[dict]:
        """执行向量搜索

        Args:
            query: 查询文本
            top_k: 返回数量

        Returns:
            向量搜索结果
        """
        # 编码查询
        query_vector = self.embedding_model.encode(query, normalize_embeddings=True)

        # 搜索Qdrant
        search_result = self.qdrant_client.search(
            collection_name='patent_guidelines',
            query_vector=query_vector,
            limit=top_k,
            with_payload=True,
            with_score=True
        )

        # 转换结果格式
        results = []
        for hit in search_result:
            results.append({
                'id': hit.id,
                'score': hit.score,
                'payload': hit.payload,
                'type': 'vector'
            })

        return results

    def _graph_search(self, query: str, top_k: int) -> list[dict]:
        """执行图搜索

        Args:
            query: 查询文本
            top_k: 返回数量

        Returns:
            图搜索结果
        """
        # 提取查询中的关键词
        keywords = self._extract_keywords(query)

        results = []

        with self.neo4j_driver.session() as session:
            # 1. 搜索概念节点
            for keyword in keywords:
                concept_results = session.run(
                    """
                    MATCH (c:Concept)
                    WHERE c.name CONTAINS $keyword OR $keyword IN c.synonyms
                    OPTIONAL MATCH (c)<-[r:DEFINES]-(s:Section)
                    RETURN c, r, s
                    LIMIT 5
                    """,
                    keyword=keyword
                )

                for record in concept_results:
                    concept = record['c']
                    section = record['s']
                    record['r']

                    if concept:
                        results.append({
                            'id': concept['name'],
                            'type': 'concept',
                            'label': concept['name'],
                            'properties': dict(concept),
                            'related_section': dict(section) if section else None,
                            'score': 1.0  # Neo4j不支持相似度评分，使用默认值
                        })

            # 2. 搜索章节内容
            content_results = session.run(
                """
                MATCH (s:Section)
                WHERE s.title CONTAINS $query OR s.content CONTAINS $query
                RETURN s
                LIMIT $limit
                """,
                query=query,
                limit=top_k
            )

            for record in content_results:
                section = record['s']
                results.append({
                    'id': section['id'],
                    'type': 'section',
                    'label': section['title'],
                    'properties': dict(section),
                    'score': 0.8
                })

        # 去重
        seen_ids = set()
        unique_results = []
        for result in results:
            if result['id'] not in seen_ids:
                seen_ids.add(result['id'])
                unique_results.append(result)

        return unique_results[:top_k]

    def _bm25_search(self, query: str, top_k: int) -> list[dict]:
        """执行BM25搜索

        Args:
            query: 查询文本
            top_k: 返回数量

        Returns:
            BM25搜索结果
        """
        if not self.bm25_index:
            return []

        # 分词查询
        tokenized_query = list(jieba.cut(query))

        # 执行搜索
        scores = self.bm25_index.get_scores(tokenized_query)

        # 获取top-k结果
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            if scores[idx] > 0:  # 只返回有分数的结果
                results.append({
                    'id': idx,
                    'type': 'bm25',
                    'score': float(scores[idx]),
                    'content': self.bm25_corpus[idx]
                })

        return results

    def _combine_results(
        self,
        vector_results: list[dict],
        graph_results: list[dict],
        bm25_results: list[dict],
        alpha: float
    ) -> list[dict]:
        """融合多种搜索结果

        Args:
            vector_results: 向量搜索结果
            graph_results: 图搜索结果
            bm25_results: BM25搜索结果
            alpha: 融合权重

        Returns:
            融合后的结果
        """
        # 收集所有结果

        # 归一化分数
        def normalize_scores(results, max_score=1.0):
            if not results:
                return []
            scores = [r['score'] for r in results]
            min_score = min(scores)
            max_score = max(scores)
            if max_score == min_score:
                return [dict(r, score=1.0) for r in results]
            for r in results:
                r['normalized_score'] = (r['score'] - min_score) / (max_score - min_score)
            return results

        # 归一化各类结果分数
        vector_results = normalize_scores(vector_results)
        graph_results = normalize_scores(graph_results)
        bm25_results = normalize_scores(bm25_results)

        # 合并结果
        combined = {}

        # 处理向量结果
        for result in vector_results:
            result_id = result.get('payload', {}).get('section_id', result['id'])
            if result_id not in combined:
                combined[result_id] = {
                    'id': result_id,
                    'type': 'combined',
                    'vector_score': 0,
                    'graph_score': 0,
                    'bm25_score': 0,
                    'final_score': 0,
                    'content': '',
                    'metadata': {}
                }
            combined[result_id]['vector_score'] = result.get('normalized_score', 0)
            combined[result_id]['content'] = result.get('payload', {}).get('text', '')
            combined[result_id]['metadata'] = result.get('payload', {}).get('metadata', {})

        # 处理图结果
        for result in graph_results:
            result_id = result['id']
            if result_id not in combined:
                combined[result_id] = {
                    'id': result_id,
                    'type': 'combined',
                    'vector_score': 0,
                    'graph_score': 0,
                    'bm25_score': 0,
                    'final_score': 0,
                    'content': '',
                    'metadata': {}
                }
            combined[result_id]['graph_score'] = result.get('normalized_score', 0)
            if result['type'] == 'section':
                combined[result_id]['content'] = result['properties'].get('content', '')
                combined[result_id]['metadata'] = {
                    'title': result['properties'].get('title', ''),
                    'level': result['properties'].get('level', 0)
                }

        # 处理BM25结果
        for result in bm25_results:
            result_id = f"bm25_{result['id']}"
            if result_id not in combined:
                combined[result_id] = {
                    'id': result_id,
                    'type': 'combined',
                    'vector_score': 0,
                    'graph_score': 0,
                    'bm25_score': 0,
                    'final_score': 0,
                    'content': result['content'],
                    'metadata': {}
                }
            combined[result_id]['bm25_score'] = result.get('normalized_score', 0)

        # 计算最终分数
        for result_id, result in combined.items():
            # 加权融合
            result['final_score'] = (
                alpha * result['vector_score'] +
                alpha * result['graph_score'] +
                (1 - alpha) * result['bm25_score']
            )

        # 排序并返回
        final_results = sorted(combined.values(), key=lambda x: x['final_score'], reverse=True)

        return final_results

    def _extract_keywords(self, text: str) -> list[str]:
        """提取关键词

        Args:
            text: 输入文本

        Returns:
            关键词列表
        """
        # 使用jieba分词
        words = jieba.cut(text)

        # 过滤停用词和短词
        stop_words = {'的', '是', '在', '有', '和', '与', '或', '但', '而', '了', '着', '过', '等'}
        keywords = []

        for word in words:
            word = word.strip()
            if len(word) >= 2 and word not in stop_words:
                keywords.append(word)

        return keywords[:10]  # 最多返回10个关键词

    def _load_bm25_corpus(self):
        """加载BM25语料库"""
        # 从Neo4j加载所有章节内容
        with self.neo4j_driver.session() as session:
            result = session.run(
                """
                MATCH (s:Section)
                WHERE s.content IS NOT NULL
                RETURN s.content
                """
            )

            self.bm25_corpus = []
            for record in result:
                content = record['s.content']
                if content:
                    self.bm25_corpus.append(content)

        # 创建BM25索引
        if self.bm25_corpus:
            tokenized_corpus = [list(jieba.cut(doc)) for doc in self.bm25_corpus]
            self.bm25_index = BM25Okapi(tokenized_corpus)
            logger.info(f"BM25语料库加载完成，共 {len(self.bm25_corpus)} 个文档")

    def get_explanation(self, query: str, result: dict) -> str:
        """获取检索结果解释

        Args:
            query: 查询文本
            result: 检索结果

        Returns:
            解释文本
        """
        explanation_parts = []

        # 向量相似度解释
        if result.get('vector_score', 0) > 0.5:
            explanation_parts.append(f"语义相似度高({result['vector_score']:.2f})")

        # 图关系解释
        if result.get('graph_score', 0) > 0.5:
            explanation_parts.append('知识图谱相关')

        # BM25匹配解释
        if result.get('bm25_score', 0) > 0.5:
            explanation_parts.append('关键词匹配度高')

        # 综合解释
        if explanation_parts:
            return f"检索原因：{'; '.join(explanation_parts)}"
        else:
            return '检索原因：综合匹配度较高'

    def close(self):
        """关闭连接"""
        self.neo4j_driver.close()
        self.qdrant_client.close()

# 测试函数
def test_graphrag():
    """测试GraphRAG检索器"""
    logger.info('=== 测试GraphRAG检索器 ===')

    retriever = GraphRAGRetriever()

    # 测试查询
    test_queries = [
        '什么是创造性？',
        '新颖性的判断标准',
        '专利申请的要求',
        '驳回的情形'
    ]

    for query in test_queries:
        logger.info(f"\n查询: {query}")
        logger.info(str('-' * 50))

        results = retriever.search(query, top_k=3)

        logger.info(f"找到 {len(results['combined_results'])} 个结果")

        for i, result in enumerate(results['combined_results'][:3], 1):
            logger.info(f"\n{i}. 相关度: {result['final_score']:.3f}")
            logger.info(f"   向量分数: {result['vector_score']:.3f}")
            logger.info(f"   图分数: {result['graph_score']:.3f}")
            logger.info(f"   BM25分数: {result['bm25_score']:.3f}")

            metadata = result.get('metadata', {})
            if metadata.get('title'):
                logger.info(f"   标题: {metadata['title']}")

            content = result.get('content', '')
            if content:
                preview = content[:100]
                logger.info(f"   预览: {preview}...")

            # 获取解释
            explanation = retriever.get_explanation(query, result)
            logger.info(f"   {explanation}")

    retriever.close()
    logger.info("\n✅ 测试完成！")

if __name__ == '__main__':
    test_graphrag()
