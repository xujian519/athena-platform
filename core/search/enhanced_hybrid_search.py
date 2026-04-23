#!/usr/bin/env python3
from __future__ import annotations
"""
增强混合检索算法
结合向量搜索、知识图谱推理和关键词检索的智能搜索系统
"""

import asyncio
import logging
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import networkx as nx

# 导入数据库连接池(替代直接使用psycopg2)
# 始终导入psycopg2作为回退
import psycopg2
from psycopg2.extras import RealDictCursor
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue
from sentence_transformers import SentenceTransformer

# 尝试使用连接池
try:
    from sqlalchemy import text


    USE_CONNECTION_POOL = True
except ImportError:
    USE_CONNECTION_POOL = False
    logging.warning("⚠️ 数据库连接池不可用,使用直接连接")

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent.parent))

# 导入配置
from core.config.search_config import UnifiedSearchConfig, get_search_config

# 配置日志
logger = logging.getLogger(__name__)
try:
    from core.interfaces.knowledge_base import KnowledgeBaseService
from config.dependency_injection import DIContainer
except ImportError:
    LegalOntology = None
    logger.warning("⚠️ LegalOntology模块未找到,使用简化模式")


@dataclass
class SearchResult:
    """搜索结果"""

    id: str
    content: str
    score: float
    source: str  # vector, graph, keyword
    metadata: dict[str, Any]
    relevance_explanation: str


@dataclass
class SearchRequest:
    """搜索请求"""

    query: str
    filters: Optional[dict[str, Any]] = None
    limit: int = 10
    vector_weight: float = 0.4
    graph_weight: float = 0.4
    keyword_weight: float = 0.2
    similarity_threshold: float = 0.3
    enable_reranking: bool = True


class EnhancedHybridSearch:
    """增强混合搜索引擎"""

    def __init__(self, config: UnifiedSearchConfig | None = None):
        """初始化混合搜索引擎

        Args:
            config: 搜索配置,如果不提供则从环境变量加载
        """
        logger.info("🔍 初始化增强混合搜索引擎...")

        # 加载配置
        self.config = config or get_search_config()

        # 数据库配置
        self.db_config = self.config.database.to_dict()

        # Qdrant配置
        self.qdrant_client = QdrantClient(
            host=self.config.qdrant.host,
            port=self.config.qdrant.port,
            timeout=self.config.qdrant.timeout,
            check_compatibility=self.config.qdrant.check_compatibility,
        )

        # 集合配置
        self.vector_collections = self.config.search.vector_collections

        # 初始化组件
        self._init_search_components()

    def _init_search_components(self) -> Any:
        """初始化搜索组件"""
        try:
            # 语义模型
            logger.info("📥 加载语义搜索模型...")
            self.semantic_model = SentenceTransformer(
                "paraphrase-multilingual-MiniLM-L12-v2", device="cpu"
            )
            logger.info("✅ 语义模型加载成功")

            # 法律本体
            logger.info("🏗️ 初始化法律本体...")
            if LegalOntology:
                self.ontology = LegalOntology()
                logger.info("✅ 法律本体初始化完成")
            else:
                self.ontology = None
                logger.warning("⚠️ 法律本体未初始化,跳过相关功能")

            # 知识图谱
            logger.info("🕸️ 构建知识图谱...")
            self.knowledge_graph = self._build_knowledge_graph()
            logger.info("✅ 知识图谱构建完成")

        except Exception as e:
            logger.error(f"❌ 搜索组件初始化失败: {e}")
            self.semantic_model = None
            self.ontology = None
            self.knowledge_graph = None

    def _build_knowledge_graph(self) -> nx.DiGraph:
        """构建知识图谱"""
        G = nx.DiGraph()

        try:
            with psycopg2.connect(**self.db_config) as conn, conn.cursor() as cursor:
                # 加载实体
                cursor.execute("SELECT * FROM legal_entities LIMIT 5000")
                for row in cursor.fetchall():
                    entity_id, entity_text, entity_type, _start_pos, doc_id = row
                    G.add_node(
                        entity_id,
                        **{"text": entity_text, "type": entity_type, "document_id": doc_id},
                    )

                # 加载关系
                cursor.execute("SELECT * FROM legal_relations LIMIT 10000")
                for row in cursor.fetchall():
                    subj_entity, obj_entity, rel_type, confidence, doc_id = row
                    # 查找对应的实体ID
                    cursor.execute(
                        """
                            SELECT id FROM legal_entities WHERE entity_text = %s
                        """,
                        (subj_entity,),
                    )
                    subj_result = cursor.fetchone()

                    cursor.execute(
                        """
                            SELECT id FROM legal_entities WHERE entity_text = %s
                        """,
                        (obj_entity,),
                    )
                    obj_result = cursor.fetchone()

                    if subj_result and obj_result:
                        G.add_edge(
                            subj_result[0],
                            obj_result[0],
                            relation_type=rel_type,
                            confidence=confidence,
                            document_id=doc_id,
                        )

        except Exception as e:
            logger.warning(f"⚠️ 知识图谱构建部分失败: {e}")

        return G

    async def search(self, request: SearchRequest) -> dict[str, Any]:
        """执行混合搜索"""
        logger.info(f"🔍 执行混合搜索: {request.query[:50]}...")

        try:
            # 1. 预处理查询
            processed_query = self._preprocess_query(request.query)

            # 2. 并行执行多种搜索
            search_tasks = [
                self._vector_search(processed_query, request),
                self._graph_search(processed_query, request),
                self._keyword_search(processed_query, request),
            ]

            vector_results, graph_results, keyword_results = await asyncio.gather(*search_tasks)

            # 3. 结果融合和重排序
            merged_results = await self._merge_search_results(
                vector_results, graph_results, keyword_results, request
            )

            # 4. 多样化处理
            diversified_results = await self._diversify_results(merged_results, request)

            # 5. 生成搜索报告
            search_report = await self._generate_search_report(
                processed_query,
                vector_results,
                graph_results,
                keyword_results,
                diversified_results,
                request,
            )

            return {
                "query": request.query,
                "processed_query": processed_query,
                "reports/reports/results": diversified_results[: request.limit],
                "total_found": len(diversified_results),
                "search_report": search_report,
                "search_time": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"❌ 搜索执行失败: {e}")
            return {
                "error": str(e),
                "query": request.query,
                "reports/reports/results": [],
                "total_found": 0,
            }

    def _preprocess_query(self, query: str) -> dict[str, Any]:
        """预处理查询"""
        # 清洗文本
        cleaned_query = re.sub(r"[^\w\s\u4e00-\u9fff]", "", query).strip()

        # 提取关键词
        keywords = self._extract_keywords(cleaned_query)

        # 实体识别
        entities = self._extract_entities(cleaned_query)

        # 意图分析
        intent = self._analyze_query_intent(cleaned_query)

        # 查询扩展
        expanded_terms = self._expand_query_terms(cleaned_query)

        return {
            "original": query,
            "cleaned": cleaned_query,
            "keywords": keywords,
            "entities": entities,
            "intent": intent,
            "expanded_terms": expanded_terms,
            "vector": (
                self.semantic_model.encode([cleaned_query])[0].tolist()
                if self.semantic_model
                else None
            ),
        }

    def _extract_keywords(self, text: str) -> list[str]:
        """提取关键词"""
        # 法律关键词词典
        legal_keywords = {
            "侵权",
            "违约",
            "合同",
            "权利",
            "义务",
            "责任",
            "赔偿",
            "损失",
            "法条",
            "规定",
            "条例",
            "司法解释",
            "案例",
            "判决",
            "裁定",
            "原告",
            "被告",
            "上诉",
            "撤诉",
            "和解",
            "调解",
            "仲裁",
            "专利",
            "商标",
            "著作权",
            "商业秘密",
            "知识产权",
            "刑法",
            "民法",
            "行政法",
            "程序法",
        }

        keywords = []
        words = text.split()
        for word in words:
            if word in legal_keywords or len(word) >= 2:
                keywords.append(word)

        return list(set(keywords))

    def _extract_entities(self, text: str) -> list[dict[str, str]]:
        """提取实体"""
        entities = []

        # 法律条文
        article_pattern = re.compile(r"第([一二三四五六七八九十百千万零0-9]+)条")
        articles = article_pattern.findall(text)
        entities.extend([{"type": "article", "value": f"第{article}条"} for article in articles])

        # 法律名称
        law_pattern = re.compile(r"《([^》]+(?:法|条例|规定|办法|细则))》")
        laws = law_pattern.findall(text)
        entities.extend([{"type": "law", "value": law} for law in laws])

        # 金额
        amount_pattern = re.compile(r"(\d+(?:,\d{3})*(?:\.\d+)?(?:元|万元|千元|美元))")
        amounts = amount_pattern.findall(text)
        entities.extend([{"type": "amount", "value": amount} for amount in amounts])

        return entities

    def _analyze_query_intent(self, text: str) -> str:
        """分析查询意图"""
        intent_patterns = {
            "case_search": ["案例", "判决", "裁定", "先例"],
            "law_search": ["法条", "规定", "条例", "法律"],
            "contract_analysis": ["合同", "协议", "约定", "违约"],
            "patent_search": ["专利", "发明", "实用新型", "外观设计"],
            "damage_calculation": ["赔偿", "损失", "费用", "金额"],
            "responsibility_analysis": ["责任", "义务", "承担", "追究"],
        }

        text_lower = text.lower()
        intent_scores = {}

        for intent, keywords in intent_patterns.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                intent_scores[intent] = score

        return max(intent_scores, key=intent_scores.get) if intent_scores else "general_search"

    def _expand_query_terms(self, text: str) -> list[str]:
        """查询词扩展"""
        expanded_terms = [text]

        # 同义词扩展
        synonyms = {
            "侵权": ["侵害", "侵犯", "侵犯权益"],
            "违约": ["违反合同", "违约责任", "违背约定"],
            "赔偿": ["补偿", "损失赔偿", "经济补偿"],
            "合同": ["协议", "约定", "契约"],
        }

        for term, syns in synonyms.items():
            if term in text:
                expanded_terms.extend(syns)

        # 本体推理扩展
        if self.ontology:
            try:
                concepts = self.ontology.search_concepts(text, limit=3)
                for concept in concepts:
                    expanded_terms.append(concept["concept"]["name"])
            except KeyError as e:
                logger.warning(f"缺少必要的数据字段: {e}")
            except Exception as e:
                logger.error(f"处理数据时发生错误: {e}")

        return list(set(expanded_terms))

    async def _vector_search(
        self, processed_query: dict[str, Any], request: SearchRequest
    ) -> list[SearchResult]:
        """向量搜索"""
        if not self.semantic_model or not processed_query["vector"]:
            return []

        logger.info("🔍 执行向量搜索...")
        results = []

        try:
            query_vector = processed_query["vector"]

            # 并行搜索多个集合
            search_tasks = []
            for collection_name in self.vector_collections:
                if self._collection_exists(collection_name):
                    search_tasks.append(
                        self._search_collection(collection_name, query_vector, request)
                    )

            collection_results = await asyncio.gather(*search_tasks, return_exceptions=True)

            # 合并结果
            for collection_result in collection_results:
                if isinstance(collection_result, list):
                    results.extend(collection_result)

            logger.info(f"📊 向量搜索找到 {len(results)} 个结果")
            return results[: self.config.search.max_results_per_source]

        except Exception as e:
            logger.error(f"❌ 向量搜索失败: {e}")
            return []

    def _collection_exists(self, collection_name: str) -> bool:
        """检查集合是否存在"""
        try:
            return self.qdrant_client.collection_exists(collection_name)
        except Exception as e:
            logger.warning(f"检查集合 {collection_name} 是否存在时出错: {e}")
            return False

    async def _search_collection(
        self, collection_name: str, query_vector: list[float], request: SearchRequest
    ) -> list[SearchResult]:
        """搜索单个集合"""
        try:
            # 构建过滤器
            search_filter = self._build_filter(request.filters)

            # 执行搜索
            search_result = self.qdrant_client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                query_filter=search_filter,
                limit=self.config.search.max_results_per_source,
                score_threshold=request.similarity_threshold,
                with_payload=True,
                with_vectors=False,
            )

            results = []
            for hit in search_result:
                result = SearchResult(
                    id=hit.id,
                    content=hit.payload.get("content", ""),
                    score=hit.score,
                    source="vector",
                    metadata={
                        "collection": collection_name,
                        "document_id": hit.payload.get("document_id"),
                        "chunk_index": hit.payload.get("chunk_index"),
                        "payload": hit.payload,
                    },
                    relevance_explanation=f"向量相似度: {hit.score:.4f}",
                )
                results.append(result)

            return results

        except Exception as e:
            logger.warning(f"⚠️ 集合 {collection_name} 搜索失败: {e}")
            return []

    def _build_filter(self, filters: dict[str, Any]) -> Filter | None:
        """构建搜索过滤器"""
        if not filters:
            return None

        conditions = []
        for field, value in filters.items():
            if isinstance(value, str):
                conditions.append(
                    FieldCondition(key=f"metadata.{field}", match=MatchValue(value=value))
                )
            elif isinstance(value, list):
                conditions.append(
                    FieldCondition(key=f"metadata.{field}", match=MatchValue(any=value))
                )

        return Filter(must=conditions) if conditions else None

    async def _graph_search(
        self, processed_query: dict[str, Any], request: SearchRequest
    ) -> list[SearchResult]:
        """知识图谱搜索"""
        if not self.knowledge_graph:
            return []

        logger.info("🔍 执行知识图谱搜索...")
        results = []

        try:
            # 基于实体搜索
            entity_results = await self._search_by_entities(processed_query, request)

            # 基于关系搜索
            relation_results = await self._search_by_relations(processed_query, request)

            # 基于路径搜索
            path_results = await self._search_by_paths(processed_query, request)

            results = entity_results + relation_results + path_results

            logger.info(f"📊 知识图谱搜索找到 {len(results)} 个结果")
            return results[: self.config.search.max_results_per_source]

        except Exception as e:
            logger.error(f"❌ 知识图谱搜索失败: {e}")
            return []

    async def _search_by_entities(
        self, processed_query: dict[str, Any], request: SearchRequest
    ) -> list[SearchResult]:
        """基于实体搜索"""
        results = []
        entities = processed_query["entities"]

        for entity in entities:
            # 在知识图谱中查找匹配的节点
            matching_nodes = [
                node
                for node, data in self.knowledge_graph.nodes(data=True)
                if entity["value"].lower() in data.get("text", "").lower()
            ]

            for node_id in matching_nodes[:10]:  # 限制每个实体的结果数
                node_data = self.knowledge_graph.nodes[node_id]
                score = 0.8  # 实体匹配的基础分数

                # 计算中心性分数
                try:
                    centrality = nx.degree_centrality(self.knowledge_graph)
                    score += centrality.get(node_id, 0) * 0.2
                except (TypeError, ZeroDivisionError) as e:
                    logger.warning(f"计算中心性时发生错误: {e}")
                except Exception as e:
                    logger.error(f"未预期的错误: {e}")

                result = SearchResult(
                    id=f"graph_entity_{node_id}",
                    content=node_data.get("text", ""),
                    score=min(score, 1.0),
                    source="graph_entity",
                    metadata={
                        "entity_type": entity["type"],
                        "node_id": node_id,
                        "document_id": node_data.get("document_id"),
                    },
                    relevance_explanation=f"实体匹配: {entity['value']}",
                )
                results.append(result)

        return results

    async def _search_by_relations(
        self, processed_query: dict[str, Any], request: SearchRequest
    ) -> list[SearchResult]:
        """基于关系搜索"""
        results = []

        # 使用本体推理
        if self.ontology and processed_query["keywords"]:
            for keyword in processed_query["keywords"][:5]:  # 限制关键词数量
                try:
                    # 推断相关概念
                    related_concepts = self.ontology.search_concepts(keyword, limit=3)

                    for concept in related_concepts:
                        if concept["score"] > 0.7:
                            result = SearchResult(
                                id=f"ontology_{concept['concept']['id']}",
                                content=concept["concept"]["name"],
                                score=concept["score"] * 0.7,
                                source="ontology",
                                metadata={
                                    "concept_id": concept["concept"]["id"],
                                    "category": concept["concept"].get("category", ""),
                                    "definition": concept["concept"].get("definition", ""),
                                },
                                relevance_explanation=f"本体关联: {keyword}",
                            )
                            results.append(result)

                except Exception as e:
                    logger.warning(f"⚠️ 本体推理失败: {e}")

        return results

    async def _search_by_paths(
        self, processed_query: dict[str, Any], request: SearchRequest
    ) -> list[SearchResult]:
        """基于路径搜索"""
        results = []

        if not self.knowledge_graph:
            return results

        try:
            # 查找相关节点
            start_nodes = []
            for entity in processed_query["entities"]:
                matching_nodes = [
                    node
                    for node, data in self.knowledge_graph.nodes(data=True)
                    if entity["value"].lower() in data.get("text", "").lower()
                ]
                start_nodes.extend(matching_nodes)

            # 从每个相关节点进行路径搜索
            for start_node in start_nodes[:5]:  # 限制起始节点数
                try:
                    # 使用BFS搜索
                    paths = list(
                        nx.single_source_shortest_path_length(
                            self.knowledge_graph,
                            start_node,
                            cutoff=self.config.search.graph_depth_limit,
                        ).items()
                    )

                    # 按距离排序
                    paths.sort(key=lambda x: x[1])

                    for target_node, distance in paths[:10]:  # 每个起始节点10个结果
                        if target_node != start_node and distance > 0:
                            node_data = self.knowledge_graph.nodes[target_node]

                            # 计算路径分数
                            score = max(0.1, 1.0 - (distance * 0.2))

                            # 获取路径上的关系
                            try:
                                path = nx.shortest_path(
                                    self.knowledge_graph, start_node, target_node
                                )
                                relations = []
                                for i in range(len(path) - 1):
                                    edge_data = self.knowledge_graph[path[i]][path[i + 1]]
                                    relations.append(edge_data.get("relation_type", "related"))

                                relation_str = " → ".join(relations)
                            except Exception:
                                relation_str = "related"

                            result = SearchResult(
                                id=f"graph_path_{start_node}_{target_node}",
                                content=node_data.get("text", ""),
                                score=score,
                                source="graph_path",
                                metadata={
                                    "start_node": start_node,
                                    "target_node": target_node,
                                    "distance": distance,
                                    "relations": relations,
                                    "document_id": node_data.get("document_id"),
                                },
                                relevance_explanation=f"图谱路径: {relation_str} (距离: {distance})",
                            )
                            results.append(result)

                except Exception as e:
                    logger.warning(f"⚠️ 路径搜索失败: {e}")

        except Exception as e:
            logger.error(f"❌ 图路径搜索失败: {e}")

        return results

    async def _keyword_search(
        self, processed_query: dict[str, Any], request: SearchRequest
    ) -> list[SearchResult]:
        """关键词搜索"""
        logger.info("🔍 执行关键词搜索...")
        results = []

        try:
            keywords = processed_query["keywords"]
            if not keywords:
                return results

            # 安全检查:限制关键词数量和长度
            keywords = [k for k in keywords if k and len(k) <= 100][:10]

            if not keywords:
                return results

            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # 构建SQL查询(使用参数化查询防止SQL注入)
                    # 使用unnest和ANY进行更安全的模式匹配
                    sql_query = """
                        SELECT DISTINCT
                            document_id,
                            content,
                            ts_rank_cd(to_tsvector('chinese', content),
                                    plainto_tsquery('chinese', %s)) as rank,
                            file_path
                        FROM legal_documents
                        WHERE content ILIKE ANY(%s)
                        ORDER BY rank DESC
                        LIMIT %s
                    """

                    # 构建安全的参数
                    # 1. 查询字符串:清理特殊字符
                    safe_keywords = []
                    for keyword in keywords:
                        # 移除可能有害的字符,保留中文、字母、数字、空格
                        cleaned = re.sub(r"[^\w\s\u4e00-\u9fff]", "", keyword)
                        if cleaned:
                            safe_keywords.append(cleaned)

                    if not safe_keywords:
                        return results

                    # 2. 模式匹配参数
                    pattern_params = [f"%{kw}%" for kw in safe_keywords]

                    # 3. 全文搜索查询字符串
                    query_string = " & ".join(safe_keywords)

                    # 执行参数化查询
                    cursor.execute(
                        sql_query,
                        (query_string, pattern_params, self.config.search.max_results_per_source),
                    )

                    for row in cursor.fetchall():
                        # 计算关键词匹配分数
                        content_lower = row["content"].lower()
                        keyword_matches = sum(
                            1 for keyword in keywords if keyword.lower() in content_lower
                        )
                        score = min(keyword_matches / len(keywords), 1.0)

                        result = SearchResult(
                            id=f"keyword_{row['document_id']}",
                            content=row["content"][:500],  # 限制内容长度
                            score=score * row["rank"],  # 结合PostgreSQL的rank分数
                            source="keyword",
                            metadata={
                                "document_id": str(row["document_id"]),
                                "file_path": row.get("file_path", ""),
                                "keyword_matches": keyword_matches,
                            },
                            relevance_explanation=f"关键词匹配: {keyword_matches}/{len(keywords)}",
                        )
                        results.append(result)

            logger.info(f"📊 关键词搜索找到 {len(results)} 个结果")
            return results

        except Exception as e:
            logger.error(f"❌ 关键词搜索失败: {e}")
            return []

    async def _merge_search_results(
        self,
        vector_results: list[SearchResult],
        graph_results: list[SearchResult],
        keyword_results: list[SearchResult],
        request: SearchRequest,
    ) -> list[SearchResult]:
        """融合搜索结果"""
        logger.info("🔗 融合搜索结果...")

        # 权重配置
        weights = {
            "vector": request.vector_weight,
            "graph_entity": request.graph_weight * 0.6,
            "ontology": request.graph_weight * 0.3,
            "graph_path": request.graph_weight * 0.1,
            "keyword": request.keyword_weight,
        }

        # 合并所有结果
        all_results = []

        for result in vector_results:
            result.score = result.score * weights.get(result.source, 1.0)
            all_results.append(result)

        for result in graph_results:
            result.score = result.score * weights.get(result.source, 1.0)
            all_results.append(result)

        for result in keyword_results:
            result.score = result.score * weights.get(result.source, 1.0)
            all_results.append(result)

        # 按ID分组(同一文档的不同来源)
        doc_groups = defaultdict(list)
        for result in all_results:
            doc_id = result.metadata.get("document_id", result.id)
            doc_groups[doc_id].append(result)

        # 合并同一文档的多源结果
        merged_results = []
        for doc_id, doc_results in doc_groups.items():
            # 计算综合分数
            final_score = 0.0
            sources = set()
            explanations = []
            combined_content = ""

            for result in doc_results:
                final_score += result.score
                sources.add(result.source)
                explanations.append(result.relevance_explanation)
                if not combined_content or len(result.content) > len(combined_content):
                    combined_content = result.content

            # 归一化分数
            final_score = min(final_score, 1.0)

            merged_result = SearchResult(
                id=doc_id,
                content=combined_content,
                score=final_score,
                source=f"merged({','.join(sources)})",
                metadata=doc_results[0].metadata,
                relevance_explanation=f"多源融合: {'; '.join(explanations[:3])}",
            )
            merged_results.append(merged_result)

        # 按分数排序
        merged_results.sort(key=lambda x: x.score, reverse=True)

        logger.info(f"📊 融合后保留 {len(merged_results)} 个结果")
        return merged_results

    async def _diversify_results(
        self, results: list[SearchResult], request: SearchRequest
    ) -> list[SearchResult]:
        """结果多样化处理"""
        if not request.enable_reranking:
            return results

        logger.info("🎯 执行结果多样化...")

        # 使用Maximal Marginal Relevance (MMR)算法
        diversified = []
        remaining = results.copy()

        while remaining and len(diversified) < request.limit * 2:  # 保留更多候选结果
            if not diversified:
                # 选择分数最高的结果
                best = max(remaining, key=lambda x: x.score)
                diversified.append(best)
                remaining.remove(best)
            else:
                # 计算MMR分数
                best_mmr_score = -1
                best_result = None

                for candidate in remaining:
                    # 与已选结果的最大相似度
                    max_similarity = 0.0
                    for selected in diversified:
                        similarity = self._calculate_content_similarity(
                            candidate.content, selected.content
                        )
                        max_similarity = max(max_similarity, similarity)

                    # MMR分数 = 相关性 - λ * 相似度
                    mmr_score = (
                        candidate.score - self.config.search.diversification_factor * max_similarity
                    )

                    if mmr_score > best_mmr_score:
                        best_mmr_score = mmr_score
                        best_result = candidate

                if best_result:
                    diversified.append(best_result)
                    remaining.remove(best_result)

        # 重新按最终分数排序
        diversified.sort(key=lambda x: x.score, reverse=True)

        logger.info(f"📊 多样化后保留 {len(diversified)} 个结果")
        return diversified

    def _calculate_content_similarity(self, content1: str, content2: str) -> float:
        """计算内容相似度"""
        if not content1 or not content2:
            return 0.0

        # 简单的Jaccard相似度
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        if not union:
            return 0.0

        return len(intersection) / len(union)

    async def _generate_search_report(
        self,
        processed_query: dict[str, Any],        vector_results: list[SearchResult],
        graph_results: list[SearchResult],
        keyword_results: list[SearchResult],
        final_results: list[SearchResult],
        request: SearchRequest,
    ) -> dict[str, Any]:
        """生成搜索报告"""
        return {
            "query_analysis": {
                "original_query": processed_query["original"],
                "cleaned_query": processed_query["cleaned"],
                "keywords": processed_query["keywords"],
                "entities": processed_query["entities"],
                "intent": processed_query["intent"],
                "expanded_terms": processed_query["expanded_terms"],
            },
            "source_statistics": {
                "vector_results": len(vector_results),
                "graph_results": len(graph_results),
                "keyword_results": len(keyword_results),
                "final_results": len(final_results),
            },
            "search_parameters": {
                "vector_weight": request.vector_weight,
                "graph_weight": request.graph_weight,
                "keyword_weight": request.keyword_weight,
                "similarity_threshold": request.similarity_threshold,
                "enable_reranking": request.enable_reranking,
            },
            "quality_metrics": {
                "avg_score": (
                    sum(r.score for r in final_results) / len(final_results) if final_results else 0
                ),
                "source_diversity": len({r.source for r in final_results}) if final_results else 0,
                "content_diversity": (
                    len({r.metadata.get("document_id") for r in final_results})
                    if final_results
                    else 0
                ),
            },
        }


async def main():
    """主函数"""
    print("🔍 增强混合检索系统")
    print("=" * 50)

    search_engine = EnhancedHybridSearch()

    # 测试搜索
    test_queries = ["专利侵权纠纷", "合同违约责任", "民事损害赔偿", "知识产权保护", "法条引用关系"]

    for query in test_queries:
        print(f"\n🔍 搜索: {query}")
        print("-" * 40)

        request = SearchRequest(
            query=query,
            limit=5,
            vector_weight=0.4,
            graph_weight=0.4,
            keyword_weight=0.2,
            enable_reranking=True,
        )

        result = await search_engine.search(request)

        if "error" not in result:
            print(f"📊 找到 {result['total_found']} 个结果")

            for i, search_result in enumerate(result["reports/reports/results"][:3], 1):
                print(f"\n{i}. [{search_result.source}]分数: {search_result.score:.4f}")
                print(f"   内容: {search_result.content[:100]}...")
                print(f"   解释: {search_result.relevance_explanation}")

            # 显示搜索报告摘要
            if "search_report" in result:
                report = result["search_report"]
                print("\n📋 搜索分析:")
                print(f"   • 查询意图: {report['query_analysis']['intent']}")
                print(f"   • 识别实体: {len(report['query_analysis']['entities'])} 个")
                print(f"   • 关键词: {report['query_analysis']['keywords']}")
                print(
                    f"   • 多源结果: 向量({report['source_statistics']['vector_results']}) "
                    f"+ 图谱({report['source_statistics']['graph_results']}) "
                    f"+ 关键词({report['source_statistics']['keyword_results']})"
                )
        else:
            print(f"❌ 搜索失败: {result['error']}")

        print("\n" + "=" * 50)


# 入口点: @async_main装饰器已添加到main函数
