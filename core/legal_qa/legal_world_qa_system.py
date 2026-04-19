#!/usr/bin/env python3
from __future__ import annotations
"""
法律世界模型 - 智能问答系统
Legal World Model - Intelligent Q&A System

基于三层架构的法律智能问答系统:
- Layer 1: 基础法律层(法律法规、司法解释)
- Layer 2: 专利专业层(审查指南、复审决定、无效决定)
- Layer 3: 司法案例层(判决文书)

特性:
1. 跨层语义检索(BGE-M3向量化)
2. 知识图谱关系推理(Neo4j)
3. 向量-图谱融合查询
4. 多跳法律推理
5. 智能证据链生成

版本: 1.0.0
创建时间: 2026-01-23
"""

import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

# 数据库连接管理
from core.database import SyncDatabaseConnectionManager, get_sync_db_manager

# 使用项目现有的BGE-M3嵌入器
from core.embedding.bge_m3_embedder import BGE_M3_Embedder
from core.logging_config import setup_logging


# 定义查询类型枚举(本地定义,避免依赖不兼容的FusionQueryEngine)
class QueryType(Enum):
    """查询类型"""

    PURE_VECTOR = "pure_vector"
    PURE_GRAPH = "pure_graph"
    VECTOR_GUIDED = "vector_guided"
    GRAPH_PRUNED = "graph_pruned"
    FUSION_BOTH = "fusion_both"


# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


# ============ 数据模型 ============


class QuestionType(Enum):
    """问题类型枚举"""

    CONCEPT = "concept"  # 概念解释
    PROVISION = "provision"  # 法条查询
    CASE_QUERY = "case_query"  # 案例查询
    COMPARISON = "comparison"  # 对比分析
    LIABILITY = "liability"  # 责任认定
    PROCEDURE = "procedure"  # 程序问题
    CREATIVITY = "creativity"  # 创造性判断
    NOVELTY = "novelty"  # 新颖性判断
    OTHER = "other"  # 其他


class LayerType(Enum):
    """层级类型枚举"""

    LAYER1_FOUNDATION = "layer1"  # 基础法律层
    LAYER2_PROFESSIONAL = "layer2"  # 专利专业层
    LAYER3_JUDICIAL = "layer3"  # 司法案例层


@dataclass
class QueryIntent:
    """查询意图"""

    question_type: QuestionType
    confidence: float
    entities: dict[str, Any] = field(default_factory=dict)
    keywords: list[str] = field(default_factory=list)
    target_layers: list[LayerType] = field(default_factory=list)


@dataclass
class Evidence:
    """证据"""

    content: str
    source: str
    source_type: LayerType
    relevance_score: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "source": self.source,
            "source_type": self.source_type.value,
            "relevance_score": self.relevance_score,
            "metadata": self.metadata,
        }


@dataclass
class ReasoningStep:
    """推理步骤"""

    step_number: int
    description: str
    evidence: list[Evidence] = field(default_factory=list)
    conclusion: str = ""
    confidence: float = 0.0


@dataclass
class QAAnswer:
    """问答答案"""

    answer_id: str
    question: str
    answer: str
    confidence: float
    query_intent: QueryIntent
    reasoning_chain: list[ReasoningStep] = field(default_factory=list)
    references: list[Evidence] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "answer_id": self.answer_id,
            "question": self.question,
            "answer": self.answer,
            "confidence": self.confidence,
            "query_intent": {
                "question_type": self.query_intent.question_type.value,
                "confidence": self.query_intent.confidence,
                "entities": self.query_intent.entities,
                "keywords": self.query_intent.keywords,
                "target_layers": [l.value for l in self.query_intent.target_layers],
            },
            "reasoning_chain": [
                {
                    "step_number": step.step_number,
                    "description": step.description,
                    "evidence": [e.to_dict() for e in step.evidence],
                    "conclusion": step.conclusion,
                    "confidence": step.confidence,
                }
                for step in self.reasoning_chain
            ],
            "references": [r.to_dict() for r in self.references],
            "suggestions": self.suggestions,
            "timestamp": self.timestamp,
        }


# ============ 核心类 ============


class LegalWorldQAEngine:
    """法律世界模型问答引擎"""

    # ============ 常量定义 ============
    # 内容长度限制常量(消除魔法数字)
    CONTENT_MAX_LENGTH = 1000
    CONTENT_PREVIEW_LENGTH = 300
    ANSWER_MAX_LENGTH = 500
    SUMMARY_MAX_LENGTH = 400
    EVIDENCE_MAX_LENGTH = 300

    # 查询限制常量
    DEFAULT_TOP_K = 5
    MAX_TOP_K = 20
    MIN_TOP_K = 1

    # 数据库表名常量
    TABLE_LAYER1 = "law_documents"
    TABLE_LAYER2 = "patent_law_documents"
    TABLE_LAYER3 = "patent_judgments"

    # 问题类型关键词映射
    QUESTION_TYPE_KEYWORDS = {
        QuestionType.CONCEPT: ["什么是", "定义", "概念", "含义", "解释"],
        QuestionType.PROVISION: ["法条", "法律", "规定", "依据", "条款"],
        QuestionType.CASE_QUERY: ["案例", "判例", "判决", "类似"],
        QuestionType.COMPARISON: ["区别", "差异", "对比", "不同"],
        QuestionType.LIABILITY: ["责任", "赔偿", "后果", "处罚"],
        QuestionType.PROCEDURE: ["流程", "程序", "步骤", "如何", "怎么"],
        QuestionType.CREATIVITY: ["创造性", "技术启示", "显而易见", "三步法"],
        QuestionType.NOVELTY: ["新颖性", "现有技术", "公开"],
    }

    def __init__(
        self, db_manager: SyncDatabaseConnectionManager | None = None, device: str = "auto"
    ):
        """
        初始化问答引擎

        Args:
            db_manager: 数据库管理器
            device: 设备类型 ('auto', 'mps', 'cpu')
        """
        self.db_manager = db_manager or get_sync_db_manager()
        self.device = device

        # 初始化BGE-M3嵌入器
        self.bge_embedder: BGE_M3_Embedder | None = None

        # 统计信息
        self.stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "avg_response_time": 0.0,
            "by_question_type": {},
            "by_layer": {},
        }

        logger.info("✅ 法律世界模型问答引擎初始化成功")

    async def initialize(self):
        """异步初始化组件"""
        logger.info("🔄 初始化问答引擎组件...")

        # 初始化BGE-M3嵌入器
        if self.bge_embedder is None:
            logger.info("🔄 初始化BGE-M3嵌入器...")
            self.bge_embedder = BGE_M3_Embedder(device=self.device)
            await self.bge_embedder.initialize()
            logger.info("✅ BGE-M3嵌入器初始化成功")

        logger.info("✅ 问答引擎组件初始化完成")

    def analyze_query_intent(self, question: str) -> QueryIntent:
        """
        分析查询意图

        Args:
            question: 用户问题

        Returns:
            查询意图
        """
        question_lower = question.lower().strip()

        # 提取关键词
        keywords = self._extract_keywords(question_lower)

        # 识别问题类型
        question_type, confidence = self._classify_question_type(question_lower, keywords)

        # 提取实体
        entities = self._extract_entities(question_lower)

        # 确定目标层级
        target_layers = self._determine_target_layers(question_type, entities)

        return QueryIntent(
            question_type=question_type,
            confidence=confidence,
            entities=entities,
            keywords=keywords,
            target_layers=target_layers,
        )

    def _extract_keywords(self, question: str) -> list[str]:
        """提取问题关键词"""
        # 法律关键词
        legal_keywords = [
            "专利",
            "发明",
            "实用新型",
            "外观设计",
            "创造性",
            "新颖性",
            "实用性",
            "侵权",
            "无效",
            "复审",
            "审查指南",
            "专利法",
            "实施细则",
            "权利要求",
            "说明书",
            "技术方案",
            "现有技术",
            "区别技术特征",
            "合同",
            "违约",
            "赔偿",
            "责任",
            "义务",
            "权利",
            "时效",
            "期限",
            "起诉",
            "诉讼",
            "仲裁",
            "执行",
            "判决",
            "裁定",
            "调解",
        ]

        extracted = []
        for keyword in legal_keywords:
            if keyword in question:
                extracted.append(keyword)

        return extracted

    def _classify_question_type(
        self, question: str, keywords: list[str]
    ) -> tuple[QuestionType, float]:
        """分类问题类型"""
        max_score = 0
        best_type = QuestionType.OTHER

        for qtype, type_keywords in self.QUESTION_TYPE_KEYWORDS.items():
            score = 0
            for keyword in type_keywords:
                if keyword in question:
                    score += 1

            # 关键词匹配加权
            for kw in keywords:
                if any(tk in kw for tk in type_keywords):
                    score += 0.5

            if score > max_score:
                max_score = score
                best_type = qtype

        # 计算置信度
        confidence = min(0.5 + max_score * 0.1, 1.0)

        return best_type, confidence

    def _extract_entities(self, question: str) -> dict[str, Any]:
        """提取问题实体"""
        entities = {}

        # 简单的实体提取(实际应用中可使用更复杂的NER)
        # 专利类型
        if "发明专利" in question or "发明" in question:
            entities["patent_type"] = "发明"
        elif "实用新型" in question:
            entities["patent_type"] = "实用新型"
        elif "外观设计" in question:
            entities["patent_type"] = "外观设计"

        # 争议类型
        if "创造性" in question:
            entities["issue_type"] = "创造性"
        elif "新颖性" in question:
            entities["issue_type"] = "新颖性"
        elif "实用性" in question:
            entities["issue_type"] = "实用性"
        elif "侵权" in question:
            entities["issue_type"] = "侵权"

        # 技术领域(简单提取)
        tech_fields = ["机械", "电子", "化学", "医药", "生物", "软件", "通信"]
        for field_name in tech_fields:
            if field_name in question:
                entities["technology_field"] = field_name
                break

        return entities

    def _determine_target_layers(
        self, question_type: QuestionType, entities: dict[str, Any]
    ) -> list[LayerType]:
        """确定查询目标层级"""
        # 默认查询所有层级
        target_layers = [
            LayerType.LAYER1_FOUNDATION,
            LayerType.LAYER2_PROFESSIONAL,
            LayerType.LAYER3_JUDICIAL,
        ]

        # 根据问题类型调整
        if question_type == QuestionType.CONCEPT:
            # 概念问题主要在Layer 1和Layer 2
            target_layers = [LayerType.LAYER1_FOUNDATION, LayerType.LAYER2_PROFESSIONAL]
        elif question_type == QuestionType.PROVISION:
            # 法条查询主要在Layer 1
            target_layers = [LayerType.LAYER1_FOUNDATION]
        elif question_type == QuestionType.CASE_QUERY:
            # 案例查询主要在Layer 3
            target_layers = [LayerType.LAYER3_JUDICIAL]
        elif question_type in [QuestionType.CREATIVITY, QuestionType.NOVELTY]:
            # 创造性/新颖性需要跨层查询
            target_layers = [
                LayerType.LAYER1_FOUNDATION,
                LayerType.LAYER2_PROFESSIONAL,
                LayerType.LAYER3_JUDICIAL,
            ]

        return target_layers

    async def query(
        self, question: str, top_k: int = 5, query_type: QueryType = QueryType.FUSION_BOTH
    ) -> QAAnswer:
        """
        执行查询

        Args:
            question: 用户问题
            top_k: 返回结果数量
            query_strategy: 查询策略

        Returns:
            问答答案
        """
        start_time = datetime.now()
        answer_id = str(uuid.uuid4())

        logger.info(f"📝 收到查询: {question}")

        try:
            # 确保已初始化
            if self.bge_embedder is None:
                await self.initialize()

            # 分析查询意图
            query_intent = self.analyze_query_intent(question)
            logger.info(
                f"🎯 查询意图: {query_intent.question_type.value}, 置信度: {query_intent.confidence:.2f}"
            )

            # 生成查询向量
            query_embedding = await self.bge_embedder.embed_batch([question])
            if not query_embedding or len(query_embedding) == 0:
                raise ValueError("向量生成失败:返回空结果")
            query_vector = query_embedding[0]

            # 执行融合查询
            search_results = await self._fusion_search(
                question=question,
                query_vector=query_vector,
                query_intent=query_intent,
                top_k=top_k,
                query_type=query_type,
            )

            # 构建推理链
            reasoning_chain = await self._build_reasoning_chain(
                question=question, query_intent=query_intent, search_results=search_results
            )

            # 生成答案
            answer_text = self._generate_answer(
                question=question,
                query_intent=query_intent,
                reasoning_chain=reasoning_chain,
                search_results=search_results,
            )

            # 提取参考文献
            references = self._extract_references(search_results)

            # 生成建议
            suggestions = self._generate_suggestions(query_intent, search_results)

            # 计算响应时间
            response_time = (datetime.now() - start_time).total_seconds()

            # 创建答案对象
            answer = QAAnswer(
                answer_id=answer_id,
                question=question,
                answer=answer_text,
                confidence=query_intent.confidence,
                query_intent=query_intent,
                reasoning_chain=reasoning_chain,
                references=references,
                suggestions=suggestions,
            )

            # 更新统计信息
            self.stats["total_queries"] += 1
            self.stats["successful_queries"] += 1
            self.stats["avg_response_time"] = (
                self.stats["avg_response_time"] * (self.stats["successful_queries"] - 1)
                + response_time
            ) / self.stats["successful_queries"]

            qtype = query_intent.question_type.value
            self.stats["by_question_type"][qtype] = self.stats["by_question_type"].get(qtype, 0) + 1

            for layer in query_intent.target_layers:
                layer_key = layer.value
                self.stats["by_layer"][layer_key] = self.stats["by_layer"].get(layer_key, 0) + 1

            logger.info(f"✅ 查询完成,耗时: {response_time:.2f}秒")

            return answer

        except Exception as e:
            logger.error(f"❌ 查询失败: {e}")
            self.stats["total_queries"] += 1
            self.stats["failed_queries"] += 1

            # 返回错误答案
            return QAAnswer(
                answer_id=answer_id,
                question=question,
                answer=f"抱歉,处理您的问题时出错:{e!s}",
                confidence=0.0,
                query_intent=QueryIntent(question_type=QuestionType.OTHER, confidence=0.0),
                suggestions=["请尝试重新表述您的问题", "如果问题持续,请联系系统管理员"],
            )

    async def _fusion_search(
        self,
        question: str,
        query_vector: list[float],
        query_intent: QueryIntent,
        top_k: int,
        query_type: QueryType,
    ) -> dict[str, Any]:
        """
        执行融合搜索

        Args:
            question: 问题文本
            query_vector: 查询向量
            query_intent: 查询意图
            top_k: 返回数量
            query_type: 查询类型

        Returns:
            搜索结果
        """
        results = {
            "layer1": [],  # 基础法律层
            "layer2": [],  # 专利专业层
            "layer3": [],  # 司法案例层
            "graph": [],  # 图谱关系
        }

        # 使用向量搜索进行检索
        results = await self._vector_search_fallback(query_vector, query_intent, top_k)

        # 添加图谱搜索(如果查询类型需要)
        if query_type in [QueryType.PURE_GRAPH, QueryType.VECTOR_GUIDED, QueryType.FUSION_BOTH]:
            try:
                graph_results = await self._graph_search(question, query_intent, top_k)
                results["graph"] = graph_results
                logger.info(f"✅ 图谱搜索完成,找到 {len(graph_results)} 条关系")
            except Exception as e:
                logger.warning(f"⚠️ 图谱搜索失败: {e}")

        return results

    async def _search_layer(
        self, cursor, table_name: str, query_vector: list[float], top_k: int, layer_type: LayerType
    ) -> list[dict[str, Any]]:
        """
        统一的层检索方法

        Args:
            cursor: 数据库游标
            table_name: 表名
            query_vector: 查询向量
            top_k: 返回数量
            layer_type: 层级类型

        Returns:
            list[dict[str, Any]: 检索结果列表
        """
        results = []

        try:
            # 根据层级类型构建SQL查询
            if layer_type == LayerType.LAYER1_FOUNDATION:
                # Layer 1: 基础法律层(只有content字段)
                cursor.execute(
                    """
                    SELECT
                        id,
                        title,
                        content,
                        1 - (embedding <=> %s::vector) as similarity
                    FROM law_documents
                    WHERE embedding IS NOT NULL
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """,
                    (query_vector, query_vector, top_k),
                )

                for row in cursor.fetchall():
                    results.append(
                        {
                            "id": row[0],
                            "title": row[1],
                            "content": row[2][: self.CONTENT_MAX_LENGTH] if row[2] else "",
                            "similarity": float(row[3]),
                        }
                    )

            elif layer_type == LayerType.LAYER2_PROFESSIONAL:
                # Layer 2: 专利专业层(有document_type字段)
                cursor.execute(
                    """
                    SELECT
                        id,
                        title,
                        content,
                        document_type,
                        1 - (embedding <=> %s::vector) as similarity
                    FROM patent_law_documents
                    WHERE embedding IS NOT NULL
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """,
                    (query_vector, query_vector, top_k),
                )

                for row in cursor.fetchall():
                    results.append(
                        {
                            "id": row[0],
                            "title": row[1],
                            "content": row[2][: self.CONTENT_MAX_LENGTH] if row[2] else "",
                            "document_type": row[3],
                            "similarity": float(row[4]),
                        }
                    )

            elif layer_type == LayerType.LAYER3_JUDICIAL:
                # Layer 3: 司法案例层(有reasoning和conclusion字段)
                cursor.execute(
                    """
                    SELECT
                        id,
                        title,
                        reasoning,
                        conclusion,
                        1 - (embedding <=> %s::vector) as similarity
                    FROM patent_judgments
                    WHERE embedding IS NOT NULL
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """,
                    (query_vector, query_vector, top_k),
                )

                for row in cursor.fetchall():
                    results.append(
                        {
                            "id": row[0],
                            "title": row[1],
                            "reasoning": row[2][: self.CONTENT_MAX_LENGTH] if row[2] else "",
                            "conclusion": row[3][: self.ANSWER_MAX_LENGTH] if row[3] else "",
                            "similarity": float(row[4]),
                        }
                    )

        except Exception as e:
            logger.warning(f"{layer_type.value}搜索失败: {e}")

        return results

    async def _vector_search_fallback(
        self, query_vector: list[float], query_intent: QueryIntent, top_k: int
    ) -> dict[str, Any]:
        """
        向量搜索回退方案

        Args:
            query_vector: 查询向量
            query_intent: 查询意图
            top_k: 返回数量

        Returns:
            搜索结果
        """
        results = {"layer1": [], "layer2": [], "layer3": []}

        # 从PostgreSQL + pgvector搜索
        with self.db_manager.postgresql_cursor() as cursor:
            # 使用统一的_search_layer方法搜索各层
            if LayerType.LAYER1_FOUNDATION in query_intent.target_layers:
                results["layer1"] = await self._search_layer(
                    cursor, self.TABLE_LAYER1, query_vector, top_k, LayerType.LAYER1_FOUNDATION
                )

            if LayerType.LAYER2_PROFESSIONAL in query_intent.target_layers:
                results["layer2"] = await self._search_layer(
                    cursor, self.TABLE_LAYER2, query_vector, top_k, LayerType.LAYER2_PROFESSIONAL
                )

            if LayerType.LAYER3_JUDICIAL in query_intent.target_layers:
                results["layer3"] = await self._search_layer(
                    cursor, self.TABLE_LAYER3, query_vector, top_k, LayerType.LAYER3_JUDICIAL
                )

        return results

    async def _graph_search(
        self, question: str, query_intent: QueryIntent, top_k: int
    ) -> list[dict[str, Any]]:
        """
        执行图谱搜索(Neo4j)

        根据问题类型执行不同的Cypher查询:
        - 概念问题:查找相关法律概念及其定义
        - 法条查询:查找法条及其引用关系
        - 案例查询:查找相关案例及其法律依据
        - 创造性/新颖性:查找相关审查指南和案例

        Args:
            question: 用户问题
            query_intent: 查询意图
            top_k: 返回结果数量

        Returns:
            list[dict[str, Any]: 图谱查询结果列表
        """
        results = []

        try:
            with self.db_manager.neo4j_session() as session:
                question_type = query_intent.question_type
                keywords = query_intent.keywords

                # 根据问题类型选择不同的查询策略
                if question_type == QuestionType.CONCEPT:
                    # 概念查询:查找法律概念
                    results = await self._graph_search_concept(session, keywords, top_k)

                elif question_type == QuestionType.PROVISION:
                    # 法条查询:查找法条和引用关系
                    results = await self._graph_search_provision(session, keywords, top_k)

                elif question_type == QuestionType.CASE_QUERY:
                    # 案例查询:查找案例及其法律依据
                    results = await self._graph_search_case(session, query_intent.entities, top_k)

                elif question_type in [QuestionType.CREATIVITY, QuestionType.NOVELTY]:
                    # 创造性/新颖性:查找审查指南和案例
                    results = await self._graph_search_patent_analysis(session, keywords, top_k)

                else:
                    # 通用查询:跨层关系搜索
                    results = await self._graph_search_general(session, keywords, top_k)

        except Exception as e:
            logger.error(f"❌ 图谱搜索失败: {e}")
            logger.debug(f"错误详情: {type(e).__name__}", exc_info=True)

        return results

    async def _graph_search_concept(
        self, session, keywords: list[str], top_k: int
    ) -> list[dict[str, Any]]:
        """
        搜索法律概念

        查找相关的法律概念及其在法律条文中的定义
        """
        results = []

        try:
            # 构建查询条件
            keyword_filter = ""
            if keywords:
                keyword = keywords[0].replace("'", "\\'")
                keyword_filter = f"WHERE c.concept_name CONTAINS '{keyword}'"

            # 查询法律概念
            cypher = f"""
                MATCH (c:LegalConcept)
                {keyword_filter}
                RETURN c.concept_name AS concept,
                       coalesce(substring(c.definition, 0, 500), '无定义') AS definition,
                       coalesce(c.concept_type, '未知') AS concept_type
                LIMIT {top_k}
            """

            query_result = session.run(cypher)
            for record in query_result:
                results.append(
                    {
                        "type": "concept",
                        "concept": record["concept"] or "未命名概念",
                        "definition": (record["definition"] or "无定义")[:500],
                        "concept_type": record["concept_type"] or "未知",
                    }
                )
        except Exception as e:
            logger.warning(f"概念查询失败: {e}")

        return results

    async def _graph_search_provision(
        self, session, keywords: list[str], top_k: int
    ) -> list[dict[str, Any]]:
        """
        搜索法条及其引用关系

        查找相关的法律条文及其被其他文档引用的情况
        """
        results = []

        try:
            # 构建查询条件
            keyword_filter = ""
            if keywords:
                keyword = keywords[0].replace("'", "\\'")
                keyword_filter = f"WHERE law.content CONTAINS '{keyword}'"

            # 查询法条及其引用关系
            cypher = f"""
                MATCH (law:LawDocument)
                {keyword_filter}
                OPTIONAL MATCH (law)-[r:CITED_IN_JUDGMENT|CITED_IN_GUIDE]->(citing)
                RETURN law.node_id AS law_id,
                       coalesce(law.title, substring(law.content, 0, 100)) AS title,
                       law.document_type AS doc_type,
                       count(DISTINCT citing) AS citation_count
                LIMIT {top_k}
            """

            query_result = session.run(cypher)
            for record in query_result:
                results.append(
                    {
                        "type": "provision",
                        "law_id": record["law_id"],
                        "title": (record["title"] or "未命名法条")[:200],
                        "doc_type": record["doc_type"] or "未知",
                        "citation_count": record["citation_count"],
                    }
                )
        except Exception as e:
            logger.warning(f"法条查询失败: {e}")

        return results

    async def _graph_search_case(
        self, session, entities: dict[str, Any], top_k: int
    ) -> list[dict[str, Any]]:
        """
        搜索司法案例

        查找相关的司法案例及其法律依据
        """
        results = []

        try:
            # 构建查询条件
            case_type_filter = ""
            issue_type = entities.get("issue_type", "")

            if issue_type:
                safe_type = issue_type.replace("'", "\\'")
                case_type_filter = f"WHERE j.case_type CONTAINS '{safe_type}'"

            # 查询案例及其法律依据
            cypher = f"""
                MATCH (j:JudgmentDocument)
                {case_type_filter}
                OPTIONAL MATCH (j)-[:CITED_IN_JUDGMENT]-(law:LawDocument)
                RETURN coalesce(j.case_number, j.judgment_id) AS case_number,
                       coalesce(j.court_name, '未知法院') AS court,
                       coalesce(j.case_type, '未知') AS case_type,
                       coalesce(substring(j.judgment_result, 0, 200), '无结果信息') AS result_preview,
                       count(DISTINCT law) AS law_count
                LIMIT {top_k}
            """

            query_result = session.run(cypher)
            for record in query_result:
                results.append(
                    {
                        "type": "case",
                        "case_number": record["case_number"] or "未知案号",
                        "court": record["court"],
                        "case_type": record["case_type"],
                        "result": (record["result_preview"] or "无结果信息")[:200],
                        "law_count": record["law_count"],
                    }
                )
        except Exception as e:
            logger.warning(f"案例查询失败: {e}")

        return results

    async def _graph_search_patent_analysis(
        self, session, keywords: list[str], top_k: int
    ) -> list[dict[str, Any]]:
        """
        搜索专利分析相关信息

        查找专利审查指南、复审决定和案例的关联信息
        """
        results = []

        try:
            keyword_filter = ""
            if keywords:
                keyword = keywords[0].replace("'", "\\'")
                keyword_filter = f"WHERE guide.content CONTAINS '{keyword}'"

            # 跨层查询:审查指南 -> 引用的法律 -> 被哪些案例引用
            cypher = f"""
                MATCH (guide:PatentLawDocument)
                {keyword_filter}
                OPTIONAL MATCH (guide)-[:CITES]->(law:LawDocument)
                RETURN coalesce(guide.node_id, guide.title) AS guide_id,
                       coalesce(guide.title, substring(guide.content, 0, 100)) AS guide_title,
                       count(DISTINCT law) AS law_count
                LIMIT {top_k}
            """

            query_result = session.run(cypher)
            for record in query_result:
                results.append(
                    {
                        "type": "patent_analysis",
                        "guide_id": record["guide_id"] or "未知ID",
                        "title": (record["guide_title"] or "未命名文档")[:200],
                        "law_count": record["law_count"],
                    }
                )
        except Exception as e:
            logger.warning(f"专利分析查询失败: {e}")

        return results

    async def _graph_search_general(
        self, session, keywords: list[str], top_k: int
    ) -> list[dict[str, Any]]:
        """
        通用图谱搜索

        执行跨层关系搜索,查找相关文档之间的关联
        """
        results = []

        try:
            # 如果没有关键词,返回所有关系
            if not keywords:
                cypher = """
                    MATCH (a:LawDocument)-[r:LEGAL_BASIS_FOR|CITED_IN_GUIDE|CITED_IN_JUDGMENT]->(b)
                    RETURN a.node_id AS from_id,
                           coalesce(a.title, substring(a.content, 0, 100)) AS from_title,
                           type(r) AS relation_type,
                           b.node_id AS to_id,
                           coalesce(b.title, substring(b.content, 0, 100)) AS to_title,
                           labels(b)[0] AS to_type
                    LIMIT 10
                """
            else:
                # 有关键词时,在内容中搜索
                keyword = keywords[0].replace("'", "\\'")  # 转义单引号
                cypher = f"""
                    MATCH (a:LawDocument)
                    WHERE a.content CONTAINS '{keyword}'
                    MATCH (a)-[r:LEGAL_BASIS_FOR|CITED_IN_GUIDE|CITED_IN_JUDGMENT]->(b)
                    RETURN a.node_id AS from_id,
                           coalesce(a.title, substring(a.content, 0, 100)) AS from_title,
                           type(r) AS relation_type,
                           b.node_id AS to_id,
                           coalesce(b.title, substring(b.content, 0, 100)) AS to_title,
                           labels(b)[0] AS to_type
                    LIMIT {top_k}
                """

            query_result = session.run(cypher)
            for record in query_result:
                from_title = record["from_title"] or "未命名文档"
                to_title = record["to_title"] or "未命名文档"

                results.append(
                    {
                        "type": "general_relation",
                        "from": {"id": record["from_id"], "title": from_title[:100]},  # 限制长度
                        "relation": record["relation_type"],
                        "to": {
                            "id": record["to_id"],
                            "title": to_title[:100],
                            "type": record["to_type"],
                        },
                    }
                )
        except Exception as e:
            logger.warning(f"通用查询失败: {e}")

        return results

    async def _build_reasoning_chain(
        self, question: str, query_intent: QueryIntent, search_results: dict[str, Any]
    ) -> list[ReasoningStep]:
        """
        构建推理链

        Args:
            question: 问题
            query_intent: 查询意图
            search_results: 搜索结果

        Returns:
            推理链
        """
        reasoning_chain = []
        step_number = 1

        # 步骤1:识别问题核心
        reasoning_chain.append(
            ReasoningStep(
                step_number=step_number,
                description=f"识别问题类型:{query_intent.question_type.value}",
                evidence=[],
                conclusion=f"这是一个关于{query_intent.question_type.value}的问题",
                confidence=query_intent.confidence,
            )
        )
        step_number += 1

        # 步骤2:检索基础法律(Layer 1)
        if search_results.get("layer1"):
            layer1_results = search_results["layer1"][:3]
            evidence = [
                Evidence(
                    content=r["content"][: self.EVIDENCE_MAX_LENGTH],
                    source=r["title"],
                    source_type=LayerType.LAYER1_FOUNDATION,
                    relevance_score=r["similarity"],
                    metadata={"id": r["id"]},
                )
                for r in layer1_results
            ]

            reasoning_chain.append(
                ReasoningStep(
                    step_number=step_number,
                    description="检索相关法律法规(Layer 1)",
                    evidence=evidence,
                    conclusion=f"找到{len(layer1_results)}条相关法律依据",
                    confidence=(
                        sum(r["similarity"] for r in layer1_results) / len(layer1_results)
                        if layer1_results
                        else 0.0
                    ),
                )
            )
            step_number += 1

        # 步骤3:检索专业文档(Layer 2)
        if search_results.get("layer2"):
            layer2_results = search_results["layer2"][:3]
            evidence = [
                Evidence(
                    content=r["content"][: self.EVIDENCE_MAX_LENGTH],
                    source=r["title"],
                    source_type=LayerType.LAYER2_PROFESSIONAL,
                    relevance_score=r["similarity"],
                    metadata={"id": r["id"], "document_type": r["document_type"]},
                )
                for r in layer2_results
            ]

            reasoning_chain.append(
                ReasoningStep(
                    step_number=step_number,
                    description="检索专利专业文档(Layer 2)",
                    evidence=evidence,
                    conclusion=f"找到{len(layer2_results)}条专业文档",
                    confidence=(
                        sum(r["similarity"] for r in layer2_results) / len(layer2_results)
                        if layer2_results
                        else 0.0
                    ),
                )
            )
            step_number += 1

        # 步骤4:检索司法案例(Layer 3)
        if search_results.get("layer3"):
            layer3_results = search_results["layer3"][:3]
            evidence = [
                Evidence(
                    content=r.get("reasoning", r.get("conclusion", ""))[: self.EVIDENCE_MAX_LENGTH],
                    source=r["title"],
                    source_type=LayerType.LAYER3_JUDICIAL,
                    relevance_score=r["similarity"],
                    metadata={"id": r["id"]},
                )
                for r in layer3_results
            ]

            reasoning_chain.append(
                ReasoningStep(
                    step_number=step_number,
                    description="检索相关司法案例(Layer 3)",
                    evidence=evidence,
                    conclusion=f"找到{len(layer3_results)}个相关案例",
                    confidence=(
                        sum(r["similarity"] for r in layer3_results) / len(layer3_results)
                        if layer3_results
                        else 0.0
                    ),
                )
            )
            step_number += 1

        # 步骤5:检索图谱关系(Neo4j)
        if search_results.get("graph"):
            graph_results = search_results["graph"][:3]
            evidence = []
            for r in graph_results:
                # 根据图谱结果类型构建不同的证据
                if r.get("type") == "general_relation":
                    content = f"{r['from']['title']} -{r['relation']}-> {r['to']['title']}"
                elif r.get("type") == "provision":
                    content = f"{r['title']} (被引用{r.get('citation_count', 0)}次)"
                elif r.get("type") == "case":
                    content = f"{r['case_number']} - {r['court']}"
                else:
                    content = str(r.get("title", r.get("concept", str(r))))

                evidence.append(
                    Evidence(
                        content=content[: self.EVIDENCE_MAX_LENGTH],
                        source="知识图谱",
                        source_type=LayerType.LAYER1_FOUNDATION,  # 图谱跨层
                        relevance_score=0.8,  # 图谱关系的默认相关度
                        metadata={"graph_data": r},
                    )
                )

            reasoning_chain.append(
                ReasoningStep(
                    step_number=step_number,
                    description="检索知识图谱关系(Neo4j)",
                    evidence=evidence,
                    conclusion=f"找到{len(graph_results)}条图谱关系",
                    confidence=0.8,
                )
            )
            step_number += 1

        # 步骤6:综合推理
        reasoning_chain.append(
            ReasoningStep(
                step_number=step_number,
                description="综合三层架构和图谱关系进行推理",
                evidence=[],
                conclusion="基于基础法律、专业文档、司法案例和图谱关系的综合分析",
                confidence=query_intent.confidence,
            )
        )

        return reasoning_chain

    def _generate_answer(
        self,
        question: str,
        query_intent: QueryIntent,
        reasoning_chain: list[ReasoningStep],
        search_results: dict[str, Any],    ) -> str:
        """
        生成答案

        Args:
            question: 问题
            query_intent: 查询意图
            reasoning_chain: 推理链
            search_results: 搜索结果

        Returns:
            答案文本
        """
        # 根据问题类型生成不同格式的答案
        if query_intent.question_type == QuestionType.CONCEPT:
            return self._generate_concept_answer(question, search_results)
        elif query_intent.question_type == QuestionType.PROVISION:
            return self._generate_provision_answer(question, search_results)
        elif query_intent.question_type == QuestionType.CASE_QUERY:
            return self._generate_case_answer(question, search_results)
        elif query_intent.question_type in [QuestionType.CREATIVITY, QuestionType.NOVELTY]:
            return self._generate_patent_analysis_answer(question, query_intent, search_results)
        else:
            return self._generate_general_answer(question, search_results)

    def _generate_concept_answer(self, question: str, search_results: dict[str, Any]) -> str:
        """
        生成概念解释答案

        Args:
            question: 用户问题
            search_results: 搜索结果

        Returns:
            str: 生成的答案文本
        """
        answer_parts = [f"关于'{question}'的解释:\n"]

        # Layer 1基础法律
        if search_results.get("layer1"):
            top_result = search_results["layer1"][0]
            answer_parts.append(
                f"\n[法律定义]\n{top_result['content'][:self.CONTENT_PREVIEW_LENGTH]}...\n来源:{top_result['title']}"
            )

        # Layer 2专业文档
        if search_results.get("layer2"):
            top_result = search_results["layer2"][0]
            answer_parts.append(
                f"\n[专业解释]\n{top_result['content'][:self.CONTENT_PREVIEW_LENGTH]}...\n来源:{top_result['title']}"
            )

        return "\n".join(answer_parts)

    def _generate_provision_answer(self, question: str, search_results: dict[str, Any]) -> str:
        """
        生成法条查询答案

        Args:
            question: 用户问题
            search_results: 搜索结果

        Returns:
            str: 生成的答案文本
        """
        answer_parts = [f"关于'{question}'的法律规定:\n"]

        if search_results.get("layer1"):
            for i, result in enumerate(search_results["layer1"][:3], 1):
                answer_parts.append(
                    f"\n{i}. {result['title']}\n{result['content'][:self.SUMMARY_MAX_LENGTH]}"
                )

        return "\n".join(answer_parts)

    def _generate_case_answer(self, question: str, search_results: dict[str, Any]) -> str:
        """
        生成案例查询答案

        Args:
            question: 用户问题
            search_results: 搜索结果

        Returns:
            str: 生成的答案文本
        """
        answer_parts = [f"关于'{question}'的相关案例:\n"]

        if search_results.get("layer3"):
            for i, result in enumerate(search_results["layer3"][:3], 1):
                answer_parts.append(f"\n案例{i}:{result['title']}")
                answer_parts.append(
                    f"裁判理由:{result.get('reasoning', '')[:self.CONTENT_PREVIEW_LENGTH]}..."
                )
                answer_parts.append(
                    f"裁判结果:{result.get('conclusion', '')[:self.ANSWER_MAX_LENGTH]}..."
                )
                answer_parts.append(f"相似度:{result['similarity']:.2%}")

        return "\n".join(answer_parts)

    def _generate_patent_analysis_answer(
        self, question: str, query_intent: QueryIntent, search_results: dict[str, Any]
    ) -> str:
        """
        生成专利分析答案(创造性/新颖性)

        Args:
            question: 用户问题
            query_intent: 查询意图
            search_results: 搜索结果

        Returns:
            str: 生成的答案文本
        """
        issue_type = query_intent.entities.get("issue_type", query_intent.question_type.value)

        answer_parts = [f"关于专利{issue_type}的分析:\n"]

        # 法律依据(Layer 1)
        if search_results.get("layer1"):
            answer_parts.append("\n[法律依据]")
            top_result = search_results["layer1"][0]
            answer_parts.append(f"{top_result['content'][:self.CONTENT_PREVIEW_LENGTH]}...")
            answer_parts.append(f"来源:{top_result['title']}")

        # 审查指南(Layer 2)
        if search_results.get("layer2"):
            answer_parts.append("\n[审查指南]")
            relevant_docs = [r for r in search_results["layer2"] if "指南" in r.get("title", "")]
            if relevant_docs:
                top_result = relevant_docs[0]
                answer_parts.append(f"{top_result['content'][:self.CONTENT_PREVIEW_LENGTH]}...")
                answer_parts.append(f"来源:{top_result['title']}")

        # 相关案例(Layer 3)
        if search_results.get("layer3"):
            answer_parts.append("\n[相关案例]")
            for i, result in enumerate(search_results["layer3"][:2], 1):
                answer_parts.append(f"\n案例{i}:{result['title']}")
                answer_parts.append(f"{result.get('reasoning', '')[:self.ANSWER_MAX_LENGTH]}...")

        return "\n".join(answer_parts)

    def _generate_general_answer(self, question: str, search_results: dict[str, Any]) -> str:
        """
        生成通用答案

        Args:
            question: 用户问题
            search_results: 搜索结果

        Returns:
            str: 生成的答案文本
        """
        answer_parts = [f"关于'{question}'的回答:\n"]

        # 按层级组织答案
        for layer_key, layer_label in [
            ("layer1", "基础法律"),
            ("layer2", "专业文档"),
            ("layer3", "司法案例"),
        ]:
            if search_results.get(layer_key):
                answer_parts.append(f"\n[{layer_label}]")
                top_result = search_results[layer_key][0]
                answer_parts.append(
                    f"{top_result.get('content', top_result.get('reasoning', top_result.get('conclusion', '')))[:self.SUMMARY_MAX_LENGTH]}..."
                )
                answer_parts.append(
                    f"来源:{top_result['title']}(相关度:{top_result['similarity']:.2%})"
                )

        return "\n".join(answer_parts)

    def _extract_references(self, search_results: dict[str, Any]) -> list[Evidence]:
        """
        提取参考文献

        Args:
            search_results: 搜索结果

        Returns:
            list[Evidence]: 证据列表
        """
        references = []

        for layer_key, layer_type in [
            ("layer1", LayerType.LAYER1_FOUNDATION),
            ("layer2", LayerType.LAYER2_PROFESSIONAL),
            ("layer3", LayerType.LAYER3_JUDICIAL),
        ]:
            if search_results.get(layer_key):
                for result in search_results[layer_key][:3]:
                    content = result.get(
                        "content", result.get("reasoning", result.get("conclusion", ""))
                    )
                    references.append(
                        Evidence(
                            content=content[: self.ANSWER_MAX_LENGTH],
                            source=result["title"],
                            source_type=layer_type,
                            relevance_score=result["similarity"],
                            metadata={"id": result["id"]},
                        )
                    )

        # 按相关度排序
        references.sort(key=lambda x: x.relevance_score, reverse=True)
        return references[:5]

    def _generate_suggestions(
        self, query_intent: QueryIntent, search_results: dict[str, Any]
    ) -> list[str]:
        """
        生成建议

        Args:
            query_intent: 查询意图
            search_results: 搜索结果

        Returns:
            list[str]: 建议列表
        """
        suggestions = []

        # 通用建议
        suggestions.append("如需更详细的法律分析,建议咨询专业专利律师")

        # 基于问题类型的建议
        if query_intent.question_type == QuestionType.CREATIVITY:
            suggestions.append(
                "创造性判断通常采用'三步法':确定区别技术特征 → 确定实际解决的技术问题 → 判断现有技术是否给出技术启示"
            )
        elif query_intent.question_type == QuestionType.NOVELTY:
            suggestions.append("新颖性判断需要对比权利要求与现有技术,检查是否完全公开")
        elif query_intent.question_type == QuestionType.CASE_QUERY:
            suggestions.append("案例仅供参考,具体案件需要根据具体情况分析")

        # 基于搜索结果的建议
        total_results = sum(len(results) for results in search_results.values())
        if total_results == 0:
            suggestions.append("未找到相关结果,建议尝试使用不同的关键词")
        elif total_results < 3:
            suggestions.append("相关结果较少,可以尝试更具体的查询")

        return suggestions

    def get_statistics(self) -> dict[str, Any]:
        """
        获取统计信息

        Returns:
            dict[str, Any]: 统计信息字典,包含:
                - total_queries: 总查询数
                - successful_queries: 成功查询数
                - failed_queries: 失败查询数
                - avg_response_time: 平均响应时间
                - success_rate: 成功率
                - by_question_type: 按问题类型分组的统计
                - by_layer: 按层级分组的统计
        """
        return {
            **self.stats,
            "success_rate": (
                self.stats["successful_queries"] / self.stats["total_queries"]
                if self.stats["total_queries"] > 0
                else 0
            ),
        }


# ============ API接口(FastAPI集成)============

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# 创建速率限制器
limiter = Limiter(key_func=get_remote_address)


# 请求/响应模型
class QuestionRequest(BaseModel):
    """问题请求"""

    question: str = Field(..., description="用户问题", min_length=1)
    top_k: int = Field(5, description="返回结果数量", ge=1, le=20)
    query_strategy: str = Field("fusion_both", description="查询策略")


class QuestionResponse(BaseModel):
    """问题响应"""

    answer_id: str
    question: str
    answer: str
    confidence: float
    reasoning_chain: list[dict[str, Any]] = []
    references: list[dict[str, Any]] = []
    suggestions: list[str] = []
    timestamp: str


# 全局问答引擎实例(使用依赖注入管理)
_qa_engine_instance: LegalWorldQAEngine | None = None


async def get_qa_engine() -> AsyncGenerator[LegalWorldQAEngine, None]:
    """
    获取问答引擎实例(依赖注入)

    Yields:
        LegalWorldQAEngine: 问答引擎实例
    """
    global _qa_engine_instance

    if _qa_engine_instance is None:
        _qa_engine_instance = LegalWorldQAEngine()
        await _qa_engine_instance.initialize()

    try:
        yield _qa_engine_instance
    finally:
        # 可以在这里添加清理逻辑
        pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理

    Args:
        app: FastAPI应用实例
    """
    # 启动时
    global _qa_engine_instance
    _qa_engine_instance = LegalWorldQAEngine()
    await _qa_engine_instance.initialize()
    logger.info("✅ 法律问答API服务启动成功")

    yield

    # 关闭时
    logger.info("✅ 法律问答API服务关闭")


def create_qa_app() -> FastAPI:
    """
    创建FastAPI应用

    Returns:
        FastAPI: 应用实例
    """
    app = FastAPI(
        title="法律世界模型智能问答API",
        description="基于三层架构的法律智能问答系统",
        version="1.0.0",
        lifespan=lifespan,
    )

    # 配置速率限制器
    app.state.limiter = limiter

    # 添加速率限制异常处理器
    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
        """速率限制异常处理"""
        return JSONResponse(
            status_code=429,
            content={
                "error": "速率限制",
                "message": f"请求过于频繁,请稍后再试。限制: {exc.detail}",
                "retry_after": 60,
            },
            headers={"Retry-After": "60"},
        )

    @app.get("/")
    async def root():
        """根路径"""
        return {
            "service": "法律世界模型智能问答API",
            "version": "1.0.0",
            "status": "running",
            "data_assets": {
                "layer1_foundation_law": "基础法律层(法律法规、司法解释)",
                "layer2_patent_professional": "专利专业层(审查指南、复审决定、无效决定)",
                "layer3_judicial_cases": "司法案例层(判决文书)",
            },
            "endpoints": {"qa": "/api/v1/qa/ask", "stats": "/api/v1/qa/stats", "health": "/health"},
        }

    @app.get("/health")
    @limiter.limit("60/minute")  # 每分钟60次请求
    async def health_check(request: Request, engine: LegalWorldQAEngine = Depends(get_qa_engine)):
        """
        健康检查

        Args:
            request: HTTP请求对象(用于速率限制)
            engine: 问答引擎实例(依赖注入)

        Returns:
            dict[str, Any]: 健康状态信息
        """
        stats = engine.get_statistics()
        return {
            "status": "healthy",
            "total_queries": stats["total_queries"],
            "success_rate": f"{stats['success_rate']:.2%}",
            "avg_response_time": f"{stats['avg_response_time']:.3f}s",
            "timestamp": datetime.now().isoformat(),
        }

    @app.post("/api/v1/qa/ask", response_model=QuestionResponse)
    @limiter.limit("10/minute")  # 每分钟10次请求(核心接口限制更严格)
    async def ask_question(
        request: Request,
        question_request: QuestionRequest,
        engine: LegalWorldQAEngine = Depends(get_qa_engine),
    ):
        """
        智能问答接口

        支持的问题类型:
        - 概念解释: "什么是专利的创造性?"
        - 法条查询: "专利法对创造性的规定是什么?"
        - 案例查询: "查找机械结构类创造性判断案例"
        - 专利分析: "分析这个技术方案的创造性"

        Args:
            request: 问题请求
            engine: 问答引擎实例(依赖注入)

        Returns:
            QuestionResponse: 问题响应
        """
        try:
            # 转换查询类型
            type_map = {
                "pure_vector": QueryType.PURE_VECTOR,
                "pure_graph": QueryType.PURE_GRAPH,
                "vector_guided": QueryType.VECTOR_GUIDED,
                "graph_pruned": QueryType.GRAPH_PRUNED,
                "fusion_both": QueryType.FUSION_BOTH,
            }
            query_type = type_map.get(question_request.query_strategy, QueryType.FUSION_BOTH)

            # 执行查询
            answer = await engine.query(
                question=question_request.question,
                top_k=question_request.top_k,
                query_type=query_type,
            )

            return QuestionResponse(
                answer_id=answer.answer_id,
                question=answer.question,
                answer=answer.answer,
                confidence=answer.confidence,
                reasoning_chain=[
                    {
                        "step_number": step.step_number,
                        "description": step.description,
                        "conclusion": step.conclusion,
                        "confidence": step.confidence,
                    }
                    for step in answer.reasoning_chain
                ],
                references=[r.to_dict() for r in answer.references],
                suggestions=answer.suggestions,
                timestamp=answer.timestamp,
            )

        except Exception as e:
            logger.error(f"问答处理失败: {e}")
            raise HTTPException(status_code=500, detail=str(e)) from e

    @app.get("/api/v1/qa/stats")
    @limiter.limit("30/minute")  # 每分钟30次请求
    async def get_stats(request: Request, engine: LegalWorldQAEngine = Depends(get_qa_engine)):
        """
        获取统计信息

        Args:
            request: HTTP请求对象(用于速率限制)
            engine: 问答引擎实例(依赖注入)

        Returns:
            dict[str, Any]: 统计信息
        """
        return engine.get_statistics()

    return app


# ============ 主函数 ============


def main():
    """主函数"""
    import uvicorn

    print("""
╔═══════════════════════════════════════════════════════════╗
║     法律世界模型 - 智能问答系统                             ║
║     Legal World Model - Intelligent Q&A System            ║
╠═══════════════════════════════════════════════════════════╣
║  三层架构:                                                ║
║    Layer 1: 基础法律层(法律法规、司法解释)               ║
║    Layer 2: 专利专业层(审查指南、复审决定、无效决定)      ║
║    Layer 3: 司法案例层(判决文书)                         ║
╠═══════════════════════════════════════════════════════════╣
║  API端点:                                                 ║
║    - GET  /                         服务信息              ║
║    - GET  /health                   健康检查              ║
║    - POST /api/v1/qa/ask            智能问答              ║
║    - GET  /api/v1/qa/stats          统计信息              ║
╚═══════════════════════════════════════════════════════════╝
    """)

    app = create_qa_app()
    uvicorn.run(app, host="0.0.0.0", port=8015)


if __name__ == "__main__":
    main()
