#!/usr/bin/env python3
"""
专利规则构建系统 - Qdrant向量库（含rerank优化）
Patent Rules Builder - Qdrant Vector Database with Rerank Optimization

基于Qdrant的高性能向量存储和检索系统，支持混合搜索和rerank优化

作者: Athena平台团队
创建时间: 2025-12-20
版本: v1.0.0
"""

from __future__ import annotations
import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np

# Qdrant客户端
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

# 使用安全哈希函数替代不安全的MD5/SHA1
from production.utils.security_helpers import short_hash

# 本地NLP系统
try:
    import sys
    sys.path.append("/Users/xujian/Athena工作平台/production/dev/scripts")
    from nlp_adapter_professional import NLPAdapter
    NLP_AVAILABLE = True
except ImportError:
    NLP_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentType(Enum):
    """文档类型"""
    PATENT_LAW = "专利法"
    GUIDELINE = "审查指南"
    IMPLEMENTATION_RULES = "实施细则"
    JUDICIAL_INTERPRETATION = "司法解释"
    CASE_NOTE = "案例笔记"
    TECHNICAL_STANDARD = "技术标准"
    MODIFICATION_2025 = "2025年修改"

class SearchMode(Enum):
    """搜索模式"""
    SEMANTIC = "semantic"           # 纯语义搜索
    HYBRID = "hybrid"              # 混合搜索（语义+关键词）
    GRAPH = "graph"                # 图增强搜索
    RERANK = "rerank"              # 重排序搜索
    MULTI_MODAL = "multi_modal"    # 多模态搜索

@dataclass
class VectorDocument:
    """向量文档"""
    doc_id: str
    content: str
    doc_type: DocumentType
    metadata: dict[str, Any]
    embedding: list[float] | None = None
    chunk_id: str | None = None
    chunk_index: int | None = None
    modified_2025: dict[str, Any] | None = None

@dataclass
class SearchResult:
    """搜索结果"""
    doc_id: str
    content: str
    score: float
    doc_type: DocumentType
    metadata: dict[str, Any]
    chunk_info: dict[str, Any] | None = None
    rerank_score: float | None = None
    explanation: str | None = None

@dataclass
class RerankConfig:
    """重排序配置"""
    model_name: str = "cross_encoder"
    top_k: int = 20
    apply_filters: bool = True
    boost_2025: float = 1.2
    boost_legal: float = 1.1
    boost_guideline: float = 1.0

class QdrantVectorStore:
    """Qdrant向量存储管理器"""

    def __init__(self,
                 collection_name: str = "patent_rules",
                 vector_size: int = 1024,
                 host: str = "localhost",
                 port: int = 6333):
        self.collection_name = collection_name
        self.vector_size = vector_size
        self.host = host
        self.port = port

        # 初始化客户端
        self.client = None
        self.nlp_adapter = None

        # 初始化组件
        self._initialize_client()
        self._initialize_nlp()

        # Rerank配置
        self.rerank_config = RerankConfig()

        # 统计信息
        self.stats = {
            "documents_indexed": 0,
            "search_queries": 0,
            "total_search_time": 0,
            "cache_hits": 0,
            "rerank_queries": 0
        }

        # 缓存
        self._embedding_cache = {}
        self._search_cache = {}

    def _initialize_client(self) -> Any:
        """初始化Qdrant客户端"""
        try:
            self.client = QdrantClient(
                host=self.host,
                port=self.port,
                timeout=30
            )
            logger.info("✅ Qdrant客户端初始化成功")
        except Exception as e:
            logger.warning(f"⚠️ Qdrant服务不可用: {e}")
            self.client = None

    def _initialize_nlp(self) -> Any:
        """初始化NLP适配器"""
        if not NLP_AVAILABLE:
            logger.warning("⚠️ 本地NLP系统不可用")
            return

        try:
            self.nlp_adapter = NLPAdapter()
            logger.info("✅ NLP适配器初始化成功")
        except Exception as e:
            logger.error(f"❌ NLP适配器初始化失败: {e}")
            self.nlp_adapter = None

    async def create_collection(self) -> bool:
        """创建集合"""
        if not self.client:
            logger.warning("⚠️ Qdrant客户端未初始化，使用文件模拟")
            return await self._create_file_collection()

        try:
            # 检查集合是否存在
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)

            if exists:
                logger.info(f"✅ 集合 {self.collection_name} 已存在")
                # 获取集合信息
                info = self.client.get_collection(self.collection_name)
                logger.info(f"   向量维度: {info.config.params.vectors.size}")
                logger.info(f"   文档数量: {info.points_count}")
                return True

            # 创建新集合
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE
                )
            )

            logger.info(f"✅ 创建集合成功: {self.collection_name}")
            logger.info(f"   向量维度: {self.vector_size}")
            logger.info("   距离度量: 余弦相似度")

            return True

        except Exception as e:
            logger.error(f"❌ 创建集合失败: {e}")
            return await self._create_file_collection()

    async def _create_file_collection(self) -> bool:
        """创建文件模拟集合"""
        try:
            # 创建数据目录
            data_dir = Path("/Users/xujian/Athena工作平台/production/data/patent_rules/qdrant_store")
            data_dir.mkdir(parents=True, exist_ok=True)

            # 创建集合配置文件
            config_file = data_dir / f"{self.collection_name}_config.json"
            config = {
                "collection_name": self.collection_name,
                "vector_size": self.vector_size,
                "distance": "COSINE",
                "created_at": datetime.now().isoformat(),
                "points_count": 0
            }

            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            # 创建数据文件
            data_file = data_dir / f"{self.collection_name}_data.json"
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)

            logger.info(f"✅ 创建文件模拟集合: {self.collection_name}")
            return True

        except Exception as e:
            logger.error(f"❌ 创建文件模拟集合失败: {e}")
            return False

    async def generate_embedding(self, text: str, doc_type: str = "") -> list[float]:
        """生成向量嵌入"""
        # 检查缓存
        cache_key = short_hash(f"{text}_{doc_type}".encode())
        if cache_key in self._embedding_cache:
            self.stats["cache_hits"] += 1
            return self._embedding_cache[cache_key]

        # 使用NLP适配器
        if self.nlp_adapter:
            try:
                embedding = await self.nlp_adapter.encode_text(text, "patent_bert")
                if embedding and len(embedding) > 0:
                    # 标准化维度
                    if len(embedding) != self.vector_size:
                        if len(embedding) > self.vector_size:
                            embedding = embedding[:self.vector_size]
                        else:
                            # 填充
                            embedding.extend([0.0] * (self.vector_size - len(embedding)))

                    # 归一化
                    norm = np.linalg.norm(embedding)
                    if norm > 0:
                        embedding = (np.array(embedding) / norm).tolist()

                    # 缓存结果
                    self._embedding_cache[cache_key] = embedding
                    return embedding
            except Exception as e:
                logger.error(f"NLP嵌入生成失败: {e}")

        # 回退到简单哈希向量
        embedding = self._generate_hash_embedding(text, doc_type)
        self._embedding_cache[cache_key] = embedding
        return embedding

    def _generate_hash_embedding(self, text: str, doc_type: str) -> list[float]:
        """生成哈希向量（回退方案）"""

        # 基于文本和类型生成特征向量
        features = []

        # 1. 文本长度特征
        features.append(min(len(text) / 1000, 1.0))

        # 2. 文档类型特征
        type_features = {
            "专利法": [1, 0, 0, 0, 0],
            "审查指南": [0, 1, 0, 0, 0],
            "实施细则": [0, 0, 1, 0, 0],
            "司法解释": [0, 0, 0, 1, 0],
            "2025年修改": [0, 0, 0, 0, 1]
        }
        features.extend(type_features.get(doc_type, [0, 0, 0, 0, 0]))

        # 3. 关键词特征
        keywords = [
            "专利", "发明", "实用新型", "外观设计", "审查", "申请",
            "权利要求", "说明书", "新颖性", "创造性", "实用性",
            "AI", "人工智能", "算法", "模型", "数据", "2025"
        ]

        for keyword in keywords:
            features.append(min(text.count(keyword) / 10, 1.0))

        # 4. 哈希特征
        hash_bytes = hashlib.sha256(text.encode()).digest()[:100]

        # 将字节转换为浮点数
        hash_features = [b / 255.0 for b in hash_bytes[:100]]

        # 合并所有特征
        all_features = features + hash_features

        # 扩展到指定维度
        if len(all_features) < self.vector_size:
            all_features.extend([0.0] * (self.vector_size - len(all_features)))
        elif len(all_features) > self.vector_size:
            all_features = all_features[:self.vector_size]

        return all_features

    async def index_document(self, document: VectorDocument) -> bool:
        """索引单个文档"""
        try:
            # 生成嵌入
            if not document.embedding:
                document.embedding = await self.generate_embedding(
                    document.content,
                    document.doc_type.value
                )

            # 构建点结构
            point = PointStruct(
                id=document.doc_id,
                vector=document.embedding,
                payload={
                    "content": document.content,
                    "doc_type": document.doc_type.value,
                    "metadata": document.metadata,
                    "chunk_id": document.chunk_id,
                    "chunk_index": document.chunk_index,
                    "modified_2025": document.modified_2025,
                    "indexed_at": datetime.now().isoformat()
                }
            )

            # 索引到Qdrant
            if self.client:
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=[point]
                )
            else:
                # 文件模拟
                await self._save_point_to_file(point)

            self.stats["documents_indexed"] += 1
            return True

        except Exception as e:
            logger.error(f"❌ 索引文档失败: {e}")
            return False

    async def _save_point_to_file(self, point: PointStruct):
        """保存点到文件"""
        try:
            data_dir = Path("/Users/xujian/Athena工作平台/production/data/patent_rules/qdrant_store")
            data_file = data_dir / f"{self.collection_name}_data.json"

            # 读取现有数据
            if data_file.exists():
                with open(data_file, encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = []

            # 转换PointStruct为字典
            point_dict = {
                "id": point.id,
                "vector": point.vector,
                "payload": point.payload
            }

            # 检查是否已存在
            existing_idx = next((i for i, p in enumerate(data) if p["id"] == point.id), None)
            if existing_idx is not None:
                data[existing_idx] = point_dict
            else:
                data.append(point_dict)

            # 保存数据
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"❌ 保存点到文件失败: {e}")

    async def search(self,
                    query: str,
                    top_k: int = 10,
                    search_mode: SearchMode = SearchMode.SEMANTIC,
                    filters: dict[str, Any] | None = None) -> list[SearchResult]:
        """搜索文档"""
        start_time = time.time()

        try:
            # 生成查询向量
            query_embedding = await self.generate_embedding(query)

            # 执行基础搜索
            results = await self._base_search(query_embedding, top_k * 2, filters)

            # 根据模式处理结果
            if search_mode == SearchMode.RERANK:
                results = await self._rerank_results(query, results, top_k)
            elif search_mode == SearchMode.HYBRID:
                results = await self._hybrid_search(query, results, top_k)
            elif search_mode == SearchMode.GRAPH:
                results = await self._graph_enhanced_search(query, results, top_k)
            elif search_mode == SearchMode.MULTI_MODAL:
                results = await self._multi_modal_search(query, results, top_k)
            else:
                # 纯语义搜索，截取top_k
                results = results[:top_k]

            # 更新统计
            search_time = time.time() - start_time
            self.stats["search_queries"] += 1
            self.stats["total_search_time"] += search_time

            logger.info(f"搜索完成: {len(results)} 个结果, 耗时 {search_time:.3f}s")
            return results

        except Exception as e:
            logger.error(f"❌ 搜索失败: {e}")
            return []

    async def _base_search(self,
                          query_embedding: list[float],
                          top_k: int,
                          filters: dict[str, Any] | None = None) -> list[SearchResult]:
        """基础向量搜索"""
        if self.client:
            # Qdrant搜索
            search_filter = None
            if filters:
                conditions = []
                for key, value in filters.items():
                    conditions.append(
                        FieldCondition(
                            key=key,
                            match=MatchValue(value=value)
                        )
                    )
                search_filter = Filter(must=conditions)

            hits = self.client.search(
                collection_name=self.collection_name,
                query_vector=(self.collection_name, query_embedding),
                query_filter=search_filter,
                limit=top_k,
                with_payload=True
            )

            results = []
            for hit in hits:
                payload = hit.payload
                result = SearchResult(
                    doc_id=hit.id,
                    content=payload.get("content", ""),
                    score=hit.score,
                    doc_type=DocumentType(payload.get("doc_type", "")),
                    metadata=payload.get("metadata", {}),
                    chunk_info={
                        "chunk_id": payload.get("chunk_id"),
                        "chunk_index": payload.get("chunk_index")
                    }
                )
                results.append(result)

            return results
        else:
            # 文件搜索
            return await self._file_search(query_embedding, top_k, filters)

    async def _file_search(self,
                          query_embedding: list[float],
                          top_k: int,
                          filters: dict[str, Any] | None = None) -> list[SearchResult]:
        """文件模拟搜索"""
        try:
            data_dir = Path("/Users/xujian/Athena工作平台/production/data/patent_rules/qdrant_store")
            data_file = data_dir / f"{self.collection_name}_data.json"

            if not data_file.exists():
                return []

            with open(data_file, encoding='utf-8') as f:
                points = json.load(f)

            # 计算余弦相似度
            results = []
            query_vec = np.array(query_embedding)

            for point in points:
                # 应用过滤
                if filters:
                    payload = point.get("payload", {})
                    match = True
                    for key, value in filters.items():
                        if payload.get(key) != value:
                            match = False
                            break
                    if not match:
                        continue

                # 计算相似度
                doc_vec = np.array(point["vector"])
                similarity = np.dot(query_vec, doc_vec) / (
                    np.linalg.norm(query_vec) * np.linalg.norm(doc_vec)
                )

                payload = point.get("payload", {})
                result = SearchResult(
                    doc_id=point["id"],
                    content=payload.get("content", ""),
                    score=float(similarity),
                    doc_type=DocumentType(payload.get("doc_type", "")),
                    metadata=payload.get("metadata", {}),
                    chunk_info={
                        "chunk_id": payload.get("chunk_id"),
                        "chunk_index": payload.get("chunk_index")
                    }
                )
                results.append(result)

            # 排序并返回top_k
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:top_k]

        except Exception as e:
            logger.error(f"❌ 文件搜索失败: {e}")
            return []

    async def _rerank_results(self,
                             query: str,
                             results: list[SearchResult],
                             top_k: int) -> list[SearchResult]:
        """重排序结果"""
        self.stats["rerank_queries"] += 1

        try:
            # 1. 基于文档类型加权
            for result in results:
                boost = 1.0

                if result.doc_type == DocumentType.MODIFICATION_2025:
                    boost = self.rerank_config.boost_2025
                elif result.doc_type in [DocumentType.PATENT_LAW, DocumentType.JUDICIAL_INTERPRETATION]:
                    boost = self.rerank_config.boost_legal
                elif result.doc_type == DocumentType.GUIDELINE:
                    boost = self.rerank_config.boost_guideline

                # 2025年修改内容额外加权
                if result.metadata.get("has_2025_modification"):
                    boost *= 1.3

                # 应用加权
                result.rerank_score = result.score * boost

            # 2. 基于查询相关性重排序
            query_terms = set(query.lower().split())

            for result in results:
                content_lower = result.content.lower()

                # 计算词重叠度
                overlap = len(query_terms & set(content_lower.split()))
                overlap_ratio = overlap / max(len(query_terms), 1)

                # 更新重排序分数
                semantic_weight = 0.7
                lexical_weight = 0.3

                result.rerank_score = (
                    semantic_weight * (result.rerank_score or result.score) +
                    lexical_weight * overlap_ratio
                )

                # 生成解释
                highlights = []
                for term in query_terms:
                    if term in content_lower:
                        highlights.append(term)

                if highlights:
                    result.explanation = f"关键词匹配: {', '.join(highlights[:3])}"

            # 3. 排序并返回top_k
            results.sort(key=lambda x: x.rerank_score or x.score, reverse=True)
            return results[:top_k]

        except Exception as e:
            logger.error(f"❌ 重排序失败: {e}")
            return results[:top_k]

    async def _hybrid_search(self,
                            query: str,
                            results: list[SearchResult],
                            top_k: int) -> list[SearchResult]:
        """混合搜索（语义+关键词）"""
        try:
            # 提取查询关键词
            query_terms = query.lower().split()

            # 计算每个结果的混合分数
            for result in results:
                content_lower = result.content.lower()

                # 语义分数（已有）
                semantic_score = result.score

                # 关键词分数
                keyword_matches = sum(1 for term in query_terms if term in content_lower)
                keyword_score = keyword_matches / len(query_terms) if query_terms else 0

                # 混合分数
                hybrid_score = 0.6 * semantic_score + 0.4 * keyword_score

                # 更新分数
                result.score = hybrid_score
                result.explanation = f"语义: {semantic_score:.3f}, 关键词: {keyword_score:.3f}"

            # 排序并返回
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:top_k]

        except Exception as e:
            logger.error(f"❌ 混合搜索失败: {e}")
            return results[:top_k]

    async def _graph_enhanced_search(self,
                                    query: str,
                                    results: list[SearchResult],
                                    top_k: int) -> list[SearchResult]:
        """图增强搜索"""
        try:
            # 检查是否有知识图谱信息
            graph_dir = Path("/Users/xujian/Athena工作平台/production/data/patent_rules/knowledge_graph")
            if not graph_dir.exists():
                return results[:top_k]

            # 加载图数据
            vertices_file = graph_dir / "vertices.json"
            edges_file = graph_dir / "edges.json"

            if not vertices_file.exists() or not edges_file.exists():
                return results[:top_k]

            with open(vertices_file, encoding='utf-8') as f:
                vertices = json.load(f)

            with open(edges_file, encoding='utf-8') as f:
                edges = json.load(f)

            # 构建邻接关系
            adjacents = {}
            for edge in edges:
                src = edge.get("src")
                dst = edge.get("dst")

                if src not in adjacents:
                    adjacents[src] = []
                if dst not in adjacents:
                    adjacents[dst] = []

                adjacents[src].append(dst)
                adjacents[dst].append(src)

            # 增强结果分数
            for result in results:
                doc_id = result.doc_id

                # 计算图连通度
                connectivity = len(adjacents.get(doc_id, []))
                connectivity_score = min(connectivity / 10, 1.0)

                # 检查是否连接到重要节点
                important_neighbors = 0
                for neighbor in adjacents.get(doc_id, []):
                    neighbor_type = None
                    for vertex in vertices:
                        if vertex.get("vertex_id") == neighbor:
                            neighbor_type = vertex.get("type")
                            break

                    if neighbor_type in ["Document", "Modification2025"]:
                        important_neighbors += 1

                importance_score = min(important_neighbors / 5, 1.0)

                # 更新分数
                graph_boost = 0.2 * connectivity_score + 0.1 * importance_score
                result.score = result.score * (1 + graph_boost)
                result.explanation = f"图增强: {graph_boost:.3f}"

            # 排序并返回
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:top_k]

        except Exception as e:
            logger.error(f"❌ 图增强搜索失败: {e}")
            return results[:top_k]

    async def _multi_modal_search(self,
                                 query: str,
                                 results: list[SearchResult],
                                 top_k: int) -> list[SearchResult]:
        """多模态搜索"""
        try:
            # 检查是否有多模态数据
            multimodal_dir = Path("/Users/xujian/Athena工作平台/production/data/patent_rules/multimodal")
            if not multimodal_dir.exists():
                return results[:top_k]

            # 增强有多模态信息的结果
            for result in results:
                metadata = result.metadata

                # 检查是否有图像、表格等
                has_images = metadata.get("image_count", 0) > 0
                has_tables = metadata.get("table_count", 0) > 0
                has_ocr = metadata.get("ocr_text", "") != ""

                # 计算多模态分数
                multimodal_score = 0
                if has_images:
                    multimodal_score += 0.1
                if has_tables:
                    multimodal_score += 0.1
                if has_ocr:
                    multimodal_score += 0.05

                # 更新分数
                result.score = result.score * (1 + multimodal_score)

                # 记录多模态信息
                modalities = []
                if has_images:
                    modalities.append("图像")
                if has_tables:
                    modalities.append("表格")
                if has_ocr:
                    modalities.append("OCR")

                if modalities:
                    result.explanation = f"多模态: {', '.join(modalities)}"

            # 排序并返回
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:top_k]

        except Exception as e:
            logger.error(f"❌ 多模态搜索失败: {e}")
            return results[:top_k]

    async def batch_index(self, documents: list[VectorDocument]) -> dict[str, int]:
        """批量索引文档"""
        success_count = 0
        error_count = 0

        # 分批处理
        batch_size = 10
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]

            for doc in batch:
                if await self.index_document(doc):
                    success_count += 1
                else:
                    error_count += 1

            # 短暂休息避免过载
            await asyncio.sleep(0.1)

        logger.info(f"批量索引完成: 成功 {success_count}, 失败 {error_count}")

        return {
            "success": success_count,
            "error": error_count,
            "total": len(documents)
        }

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        stats = {
            **self.stats,
            "cache_size": len(self._embedding_cache),
            "search_cache_size": len(self._search_cache),
            "average_search_time": (
                self.stats["total_search_time"] / self.stats["search_queries"]
                if self.stats["search_queries"] > 0 else 0
            )
        }

        # 获取集合信息
        if self.client:
            try:
                info = self.client.get_collection(self.collection_name)
                stats["collection_info"] = {
                    "points_count": info.points_count,
                    "vector_size": info.config.params.vectors.size,
                    "distance": str(info.config.params.vectors.distance)
                }
            except Exception as e:
                logger.debug(f"空except块已触发: {e}")
                pass
        else:
            # 文件模拟统计
            try:
                data_dir = Path("/Users/xujian/Athena工作平台/production/data/patent_rules/qdrant_store")
                config_file = data_dir / f"{self.collection_name}_config.json"
                if config_file.exists():
                    with open(config_file, encoding='utf-8') as f:
                        config = json.load(f)
            except Exception as e:
                logger.debug(f"空except块已触发: {e}")

        return stats

    def clear_cache(self) -> None:
        """清理缓存"""
        self._embedding_cache.clear()
        self._search_cache.clear()
        logger.info("✅ 缓存已清理")

# 使用示例
async def main():
    """主函数示例"""
    store = QdrantVectorStore()

    # 创建集合
    await store.create_collection()

    # 示例文档
    doc = VectorDocument(
        doc_id="example_doc",
        content="专利法第一条为了保护专利权人的合法权益，鼓励发明创造...",
        doc_type=DocumentType.PATENT_LAW,
        metadata={"title": "中华人民共和国专利法", "version": "2023"}
    )

    # 索引文档
    await store.index_document(doc)

    # 搜索
    results = await store.search(
        query="专利权的保护",
        top_k=5,
        search_mode=SearchMode.RERANK
    )

    print(f"找到 {len(results)} 个结果")
    for result in results:
        print(f"  - {result.doc_id}: {result.score:.3f}")

if __name__ == "__main__":
    asyncio.run(main())
