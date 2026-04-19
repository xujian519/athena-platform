#!/usr/bin/env python3
"""
专利指南智能检索系统
Patent Guideline Intelligent Retrieval System

基于GraphRAG的专利审查指南智能检索

作者: Athena平台团队
创建时间: 2025-12-20
"""

from __future__ import annotations
import asyncio
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# 添加项目路径
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

# 导入安全配置
try:
    from production.config import get_nebula_config
except ImportError:
    def get_nebula_config() -> Any | None:
        return {
            'host': '127.0.0.1',
            'port': 9669,
            'user': 'root',
            "password": config.get("NEBULA_PASSWORD", required=True),
            'space': 'patent_guideline'
        }

# 导入Qdrant客户端
from nebula3.Config import Config

# 导入NebulaGraph客户端
from nebula3.gclient.net import ConnectionPool
from qdrant_client import QdrantClient
from qdrant_client.models import (
    FieldCondition,
    Filter,
    MatchValue,
)

from core.config.secure_config import get_config

config = get_config()


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RetrievalResult:
    """检索结果"""
    content: str
    source: str  # vector或graph
    score: float
    metadata: dict
    section_id: str
    title: str
    full_path: str
    context: list[dict] = None

@dataclass
class GraphPath:
    """图路径"""
    nodes: list[dict]
    edges: list[dict]
    score: float
    path_type: str

class PatentGuidelineRetriever:
    """专利指南检索器"""

    def __init__(self):
        # 从配置获取连接参数
        nebula_config = get_nebula_config()
        host = nebula_config.get('host', '127.0.0.1')
        port = nebula_config.get('port', 9669)

        # 配置信息
        self.qdrant_url = "http://localhost:6333"
        self.qdrant_collection = "patent_guideline_sections"
        self.nebula_hosts = f"{host}:{port}"
        self.nebula_space = nebula_config.get('space', 'patent_guideline')
        self.nebula_user = nebula_config.get('user', 'root')
        self.nebula_password = nebula_config.get("password", config.get("NEBULA_PASSWORD", required=True))

        # 初始化客户端
        self.qdrant_client = None
        self.nebula_pool = None

        # 检索参数
        self.vector_weight = 0.5  # 向量检索权重
        self.graph_weight = 0.5   # 图谱检索权重
        self.rerank_threshold = 0.5  # 重排序阈值
        self.max_context_depth = 3  # 最大上下文深度

    async def initialize(self):
        """初始化连接"""
        # 初始化Qdrant客户端
        self.qdrant_client = QdrantClient(self.qdrant_url)

        # 检查集合是否存在
        if not self.qdrant_client.collection_exists(self.qdrant_collection):
            logger.warning(f"Qdrant集合不存在: {self.qdrant_collection}")

        # 初始化NebulaGraph连接池
        config = Config()
        config.max_connection_pool_size = 10
        self.nebula_pool = ConnectionPool()

        try:
            await self.nebula_pool.init([(self.nebula_hosts, config)])
            logger.info("✅ NebulaGraph连接池初始化成功")
        except Exception as e:
            logger.error(f"❌ NebulaGraph连接失败: {e}")
            self.nebula_pool = None

    async def search(self, query: str, top_k: int = 5,
                     include_context: bool = True,
                     filters: dict = None) -> list[RetrievalResult]:
        """执行检索"""
        if not self.qdrant_client:
            raise RuntimeError("Qdrant客户端未初始化")

        logger.info(f"开始检索: {query[:50]}...")

        # 1. 向量检索
        vector_results = await self._vector_search(query, top_k * 2, filters)

        # 2. 图谱检索
        graph_results = []
        if self.nebula_pool:
            graph_results = await self._graph_search(query, top_k)

        # 3. 结果融合
        fused_results = await self._fuse_results(
            vector_results, graph_results, query
        )

        # 4. 上下文扩展
        if include_context:
            fused_results = await self._expand_context(fused_results)

        # 5. 返回top_k结果
        results = fused_results[:top_k]

        logger.info(f"✅ 检索完成: 返回 {len(results)} 个结果")
        return results

    async def _vector_search(self, query: str, top_k: int,
                            filters: dict = None) -> list[RetrievalResult]:
        """向量检索"""
        try:
            # 获取查询向量（这里简化处理）
            query_vector = await self._get_query_vector(query)

            # 构建过滤器
            search_filter = None
            if filters:
                filter_conditions = []
                for key, value in filters.items():
                    filter_conditions.append(
                        FieldCondition(key=key, match=MatchValue(value=value))
                    )
                if filter_conditions:
                    search_filter = Filter(must=filter_conditions)

            # 执行搜索
            search_result = self.qdrant_client.search(
                collection_name=self.qdrant_collection,
                query_vector=query_vector,
                query_filter=search_filter,
                limit=top_k,
                with_payload=True,
                with_vectors=False
            )

            # 转换结果
            results = []
            for scored_point in search_result:
                payload = scored_point.payload
                result = RetrievalResult(
                    content=payload.get('content', ''),
                    source='vector',
                    score=scored_point.score,
                    metadata=payload.get('metadata', {}),
                    section_id=payload.get('section_id', ''),
                    title=payload.get('title', ''),
                    full_path=payload.get('full_path', '')
                )
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"向量检索失败: {e}")
            return []

    async def _graph_search(self, query: str, top_k: int) -> list[RetrievalResult]:
        """图谱检索"""
        if not self.nebula_pool:
            return []

        try:
            # 1. 提取查询中的实体
            entities = await self._extract_query_entities(query)

            # 2. 构建Cypher查询
            query_results = []
            for entity in entities[:3]:  # 限制实体数量
                paths = await self._find_entity_paths(entity)
                query_results.extend(paths)

            # 3. 转换路径为检索结果
            results = []
            for path in query_results:
                # 提取节点内容
                for node in path.nodes:
                    if node.get('tag_name') == 'Section':
                        result = RetrievalResult(
                            content=node.get('content', ''),
                            source='graph',
                            score=path.score,
                            metadata={
                                'path_type': path.path_type,
                                'path_length': len(path.nodes)
                            },
                            section_id=node.get('section_id', ''),
                            title=node.get('title', ''),
                            full_path=node.get('full_path', '')
                        )
                        results.append(result)

            # 去重并排序
            unique_results = {}
            for result in results:
                key = result.section_id
                if key not in unique_results or result.score > unique_results[key].score:
                    unique_results[key] = result

            return sorted(unique_results.values(), key=lambda x: x.score, reverse=True)[:top_k]

        except Exception as e:
            logger.error(f"图谱检索失败: {e}")
            return []

    async def _fuse_results(self, vector_results: list[RetrievalResult],
                           graph_results: list[RetrievalResult],
                           query: str) -> list[RetrievalResult]:
        """融合检索结果"""
        # 合并结果
        all_results = vector_results + graph_results

        # 按section_id分组
        results_by_section = {}
        for result in all_results:
            if result.section_id not in results_by_section:
                results_by_section[result.section_id] = {
                    'vector_score': 0,
                    'graph_score': 0,
                    'result': result
                }

            # 更新分数
            if result.source == 'vector':
                results_by_section[result.section_id]['vector_score'] = result.score
            else:
                results_by_section[result.section_id]['graph_score'] = result.score

        # 计算融合分数
        fused_results = []
        for section_data in results_by_section.values():
            vector_score = section_data['vector_score']
            graph_score = section_data['graph_score']

            # 归一化分数
            max_vector = max(r['vector_score'] for r in results_by_section.values()) or 1
            max_graph = max(r['graph_score'] for r in results_by_section.values()) or 1

            norm_vector = vector_score / max_vector if max_vector > 0 else 0
            norm_graph = graph_score / max_graph if max_graph > 0 else 0

            # 加权融合
            fused_score = (self.vector_weight * norm_vector +
                          self.graph_weight * norm_graph)

            result = section_data['result']
            result.score = fused_score
            fused_results.append(result)

        # 排序
        fused_results.sort(key=lambda x: x.score, reverse=True)

        return fused_results

    async def _expand_context(self, results: list[RetrievalResult]) -> list[RetrievalResult]:
        """扩展上下文"""
        if not self.nebula_pool:
            return results

        expanded_results = []

        for result in results:
            context_nodes = await self._get_related_sections(
                result.section_id, max_depth=self.max_context_depth
            )

            # 添加上下文信息
            context = []
            for node in context_nodes:
                context.append({
                    'section_id': node.get('section_id'),
                    'title': node.get('title'),
                    'relation': node.get('relation'),
                    'level': node.get('level', 0)
                })

            result.context = context
            expanded_results.append(result)

        return expanded_results

    async def _get_query_vector(self, query: str) -> list[float]:
        """获取查询向量"""
        # 这里简化处理，实际应该使用嵌入模型
        import hashlib

        # 生成查询向量
        query_hash = hashlib.sha256(query.encode('utf-8')).hexdigest()
        vector = []
        for i in range(0, len(query_hash), 2):
            hex_pair = query_hash[i:i+2]
            val = int(hex_pair, 16) / 255.0
            vector.append(val)

        # 扩展到1024维
        while len(vector) < 1024:
            vector.extend(vector[:1024 - len(vector)])

        return vector[:1024]

    async def _extract_query_entities(self, query: str) -> list[str]:
        """提取查询中的实体"""
        # 简化处理：提取关键词
        keywords = []

        # 法律相关
        if "专利法" in query:
            keywords.append("专利法")
        if "创造性" in query:
            keywords.append("创造性")
        if "新颖性" in query:
            keywords.append("新颖性")
        if "实用性" in query:
            keywords.append("实用性")

        # 审查相关
        if "审查" in query:
            keywords.append("审查")
        if "驳回" in query:
            keywords.append("驳回")
        if "授权" in query:
            keywords.append("授权")

        # 提取数字引用
        import re
        number_refs = re.findall(r'第([一二三四五六七八九十\d]+)[部分章节条]', query)
        keywords.extend(number_refs)

        return keywords

    async def _find_entity_paths(self, entity: str) -> list[GraphPath]:
        """查找实体路径"""
        # 这里简化处理，返回模拟路径
        # 实际应该执行NebulaGraph查询
        paths = []

        # 模拟路径1: 定义路径
        if entity == "创造性":
            paths.append(GraphPath(
                nodes=[
                    {"tag_name": "Section", "title": "创造性的概念", "content": "创造性是指..."},
                    {"tag_name": "Section", "title": "创造性的判断原则", "content": "判断创造性应考虑..."},
                    {"tag_name": "Example", "title": "例1", "content": "本案涉及..."}
                ],
                edges=[
                    {"type": "DEFINES", "relation": "定义"},
                    {"type": "ILLUSTRATES", "relation": "举例说明"}
                ],
                score=0.9,
                path_type="definition"
            ))

        return paths

    async def _get_related_sections(self, section_id: str,
                                   max_depth: int = 3) -> list[dict]:
        """获取相关章节"""
        # 这里简化处理
        related = []

        # 模拟相关章节
        related.append({
            'section_id': f"{section_id}_parent",
            'title': "父章节",
            'relation': "BELONGS_TO",
            'level': max_depth - 1
        })

        related.append({
            'section_id': f"{section_id}_child",
            'title': "子章节",
            'relation': "CONTAINS",
            'level': max_depth + 1
        })

        return related

    async def recommend_sections(self, section_id: str,
                                 top_k: int = 5) -> list[RetrievalResult]:
        """推荐相关章节"""
        if not self.nebula_pool or not self.qdrant_client:
            return []

        # 获取当前章节信息
        current_section = await self._get_section_info(section_id)
        if not current_section:
            return []

        # 基于内容推荐
        content = current_section.get('content', '')
        if content:
            # 使用内容进行相似度搜索
            similar_results = await self._vector_search(content, top_k + 1)

            # 排除自身
            recommendations = [
                r for r in similar_results
                if r.section_id != section_id
            ][:top_k]

            # 添加推荐标签
            for rec in recommendations:
                rec.metadata['recommendation_type'] = 'content_similarity'

        # 基于图谱推荐
        graph_recommendations = await self._get_graph_recommendations(section_id, top_k)
        for rec in graph_recommendations:
            rec.metadata['recommendation_type'] = 'graph_relation'

        # 合并推荐
        all_recommendations = recommendations + graph_recommendations

        # 去重并排序
        unique_recommendations = {}
        for rec in all_recommendations:
            if rec.section_id not in unique_recommendations:
                unique_recommendations[rec.section_id] = rec

        return sorted(
            unique_recommendations.values(),
            key=lambda x: x.score,
            reverse=True
        )[:top_k]

    async def _get_section_info(self, section_id: str) -> dict | None:
        """获取章节信息"""
        try:
            # 从Qdrant获取章节信息
            search_result = self.qdrant_client.scroll(
                collection_name=self.qdrant_collection,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(key="section_id", match=MatchValue(value=section_id))
                    ]
                ),
                limit=1,
                with_payload=True
            )

            if search_result[0]:  # points
                point = search_result[0][0]
                return {
                    'section_id': point.payload.get('section_id'),
                    'title': point.payload.get('title'),
                    'content': point.payload.get('content'),
                    'full_path': point.payload.get('full_path')
                }

        except Exception as e:
            logger.error(f"获取章节信息失败: {e}")

        return None

    async def _get_graph_recommendations(self, section_id: str,
                                         top_k: int) -> list[RetrievalResult]:
        """基于图谱推荐"""
        # 查找引用当前章节的其他章节
        # 查找被当前章节引用的其他章节
        # 查找同级章节
        # 这里返回模拟结果
        return []

    async def answer_question(self, question: str, context: list[dict] = None) -> dict:
        """回答问题"""
        logger.info(f"回答问题: {question[:50]}...")

        # 检索相关内容
        search_results = await self.search(question, top_k=5, include_context=True)

        if not search_results:
            return {
                "answer": "抱歉，没有找到相关的审查指南内容。",
                "sources": [],
                "confidence": 0.0
            }

        # 构建上下文
        context_text = ""
        sources = []

        for i, result in enumerate(search_results):
            context_text += f"\n{i+1}. {result.title}\n"
            context_text += f"{result.content}\n\n"
            sources.append({
                "title": result.title,
                "section_id": result.section_id,
                "score": result.score,
                "full_path": result.full_path
            })

        # 这里可以集成LLM生成答案
        # 简化处理：返回检索到的内容
        answer = f"根据专利审查指南，相关内容如下：\n\n{context_text}"
        confidence = sum(r.score for r in search_results) / len(search_results)

        return {
            "answer": answer,
            "sources": sources,
            "confidence": confidence,
            "related_sections": [
                {
                    "section_id": r.section_id,
                    "title": r.title,
                    "score": r.score
                }
                for r in search_results
            ]
        }

    async def close(self):
        """关闭连接"""
        if self.nebula_pool:
            await self.nebula_pool.close()
            logger.info("NebulaGraph连接池已关闭")

# 使用示例
async def main():
    """主函数示例"""
    retriever = PatentGuidelineRetriever()
    await retriever.initialize()

    try:
        # 示例查询
        query = "如何判断发明的创造性？"
        results = await retriever.search(query, top_k=3)

        print(f"\n查询: {query}")
        print("\n检索结果:")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result.title}")
            print(f"   相关性: {result.score:.3f}")
            print(f"   来源: {result.source}")
            print(f"   内容: {result.content[:100]}...")

        # 示例问答
        answer = await retriever.answer_question(query)
        print("\n问题回答:")
        print(f"{answer['answer'][:500]}...")

    finally:
        await retriever.close()

if __name__ == "__main__":
    asyncio.run(main())
