#!/usr/bin/env python3
from __future__ import annotations
"""
RAG管理器 - 统一检索增强生成架构
RAG Manager - Unified Retrieval Augmented Generation Architecture

功能:
1. 统一管理向量检索、知识图谱查询、数据库查询
2. 根据任务类型自动选择检索策略
3. 构建增强上下文并注入LLM
4. 返回数据来源标注

作者: Claude Code
版本: 1.0.0
日期: 2026-01-23
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """检索结果"""

    content: str  # 检索到的内容
    source: str  # 数据来源
    score: float = 0.0  # 相似度/置信度
    metadata: dict[str, Any] = field(default_factory=dict)  # 元数据

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "content": self.content,
            "source": self.source,
            "score": self.score,
            "metadata": self.metadata,
        }


@dataclass
class RAGContext:
    """RAG上下文"""

    query: str  # 原始查询
    task_type: str  # 任务类型
    retrieval_results: list[RetrievalResult] = field(default_factory=list)
    enhanced_context: str = ""  # 增强后的上下文
    data_sources_used: list[str] = field(default_factory=list)
    processing_time: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def add_result(self, result: RetrievalResult):
        """添加检索结果"""
        self.retrieval_results.append(result)
        if result.source not in self.data_sources_used:
            self.data_sources_used.append(result.source)

    def has_results(self) -> bool:
        """是否有检索结果"""
        return len(self.retrieval_results) > 0

    def get_top_results(self, n: int = 5) -> list[RetrievalResult]:
        """获取前N个结果"""
        return sorted(self.retrieval_results, key=lambda x: x.score, reverse=True)[:n]

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "query": self.query,
            "task_type": self.task_type,
            "results_count": len(self.retrieval_results),
            "data_sources": self.data_sources_used,
            "processing_time": self.processing_time,
            "timestamp": self.timestamp,
        }


class RAGManager:
    """
    RAG管理器

    统一管理检索增强生成流程:
    1. 检索策略选择
    2. 多源数据检索
    3. 结果整合排序
    4. 上下文构建
    """

    def __init__(self, qdrant_client=None, bge_classifier=None):
        """
        初始化RAG管理器

        Args:
            qdrant_client: Qdrant客户端
            bge_classifier: BGE分类器(用于向量编码)
        """
        self.qdrant_client = qdrant_client
        self.bge_classifier = bge_classifier

        # 检索策略配置
        self.retrieval_strategies = self._init_strategies()

        logger.info("✅ RAG管理器初始化完成")

    def _init_strategies(self) -> dict[str, dict[str, Any]]:
        """
        初始化检索策略配置

        使用实际存在的Qdrant集合:
        - patents_data_1024: 专利数据
        - patent_rules_1024: 专利规则/指南
        - case_data_1024: 案例数据
        - patent_legal: 专利法律文档
        - patent_judgments: 专利判决书
        - legal_main: 法律主库
        - technical_terms_1024: 技术术语

        Returns:
            策略配置字典
        """
        return {
            # 创造性分析检索策略 - 使用专利规则和案例
            "creativity_analysis": {
                "collections": ["patent_rules_1024", "case_data_1024", "patent_judgments"],
                "limit": 5,
                "threshold": 0.35,
                "use_vector": True,
                "use_kg": True,
                "priority": "guidelines",  # 优先使用审查指南
            },
            # 新颖性分析检索策略 - 使用专利数据和现有技术
            "novelty_analysis": {
                "collections": ["patents_data_1024", "patent_legal"],
                "limit": 10,
                "threshold": 0.30,
                "use_vector": True,
                "use_kg": False,
                "priority": "prior_art",  # 优先使用现有技术
            },
            # 技术方案分析检索策略 - 使用技术术语和专利规则
            "tech_analysis": {
                "collections": ["patent_rules_1024", "technical_terms_1024", "legal_main"],
                "limit": 5,
                "threshold": 0.35,
                "use_vector": True,
                "use_kg": True,
                "priority": "technical",  # 优先使用技术方案
            },
            # 专利检索策略 - 使用专利数据和规则
            "patent_search": {
                "collections": ["patents_data_1024", "patent_rules_1024"],
                "limit": 10,
                "threshold": 0.30,
                "use_vector": True,
                "use_kg": False,
                "priority": "patents",  # 优先使用专利数据
            },
            # OA答复检索策略 - 使用规则、案例和法律文档
            "oa_response": {
                "collections": ["patent_rules_1024", "case_data_1024", "patent_legal"],
                "limit": 8,
                "threshold": 0.35,
                "use_vector": True,
                "use_kg": True,
                "priority": "guidelines",  # 优先使用指南和案例
            },
            # 默认策略 - 使用专利规则
            "default": {
                "collections": ["patent_rules_1024"],
                "limit": 3,
                "threshold": 0.40,
                "use_vector": True,
                "use_kg": False,
                "priority": "relevance",
            },
        }

    async def retrieve(
        self, query: str, task_type: str, context: dict[str, Any] | None = None
    ) -> RAGContext:
        """
        执行检索增强生成

        Args:
            query: 查询文本
            task_type: 任务类型
            context: 额外上下文

        Returns:
            RAGContext: RAG上下文对象
        """
        start_time = datetime.now()

        # 创建RAG上下文
        rag_context = RAGContext(query=query, task_type=task_type)

        # 获取检索策略
        strategy = self.retrieval_strategies.get(task_type, self.retrieval_strategies["default"])

        logger.info(f"🔍 RAG检索: {task_type}, 策略: {strategy.get('priority', 'default')}")

        # 1. 向量检索
        if strategy.get("use_vector", False):
            vector_results = await self._vector_search(
                query,
                strategy["collections"],
                limit=strategy.get("limit", 5),
                threshold=strategy.get("threshold", 0.3),
            )
            for result in vector_results:
                rag_context.add_result(result)

        # 2. 知识图谱查询(如果启用)
        if strategy.get("use_kg", False) and self.qdrant_client:
            # TODO: 集成Neo4j知识图谱查询
            pass

        # 3. 构建增强上下文
        if rag_context.has_results():
            rag_context.enhanced_context = self._build_enhanced_context(rag_context, strategy)

        # 记录处理时间
        rag_context.processing_time = (datetime.now() - start_time).total_seconds()

        logger.info(
            f"✅ RAG检索完成: {len(rag_context.retrieval_results)}条结果, "
            f"数据源: {rag_context.data_sources_used}, "
            f"耗时: {rag_context.processing_time:.2f}秒"
        )

        return rag_context

    async def _vector_search(
        self, query: str, collections: list[str], limit: int = 5, threshold: float = 0.3
    ) -> list[RetrievalResult]:
        """
        向量检索

        Args:
            query: 查询文本
            collections: 要检索的集合列表
            limit: 每个集合返回的结果数
            threshold: 相似度阈值

        Returns:
            检索结果列表
        """
        results = []

        # 检查BGE编码器是否可用
        if not self.bge_classifier or not self.bge_classifier.encoder:
            logger.warning("⚠️ BGE编码器不可用,跳过向量检索")
            return results

        # 编码查询向量
        try:
            import asyncio

            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(None, self.bge_classifier.encode_texts, [query])
            query_vector = embeddings[0].tolist() if len(embeddings) > 0 else []

            if not query_vector:
                logger.warning("⚠️ 查询向量编码失败")
                return results

            logger.info(f"✅ 查询向量维度: {len(query_vector)}")

        except Exception as e:
            logger.error(f"❌ 向量编码失败: {e}")
            return results

        # 检索每个集合
        for collection in collections:
            try:
                collection_results = await self._search_qdrant_collection(
                    collection, query_vector, limit=limit, threshold=threshold
                )
                results.extend(collection_results)

            except Exception as e:
                logger.warning(f"⚠️ 检索集合 {collection} 失败: {e}")

        return results

    async def _search_qdrant_collection(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int = 5,
        threshold: float = 0.3,
    ) -> list[RetrievalResult]:
        """
        检索Qdrant集合

        Args:
            collection_name: 集合名称
            query_vector: 查询向量
            limit: 返回结果数
            threshold: 相似度阈值

        Returns:
            检索结果列表
        """
        results = []

        if not self.qdrant_client:
            logger.warning(f"⚠️ Qdrant客户端不可用,跳过集合 {collection_name}")
            return results

        try:
            # 执行检索 - 使用query_points API
            # query参数直接接受list[float],不需要包装类
            search_results = self.qdrant_client.query_points(
                collection_name=collection_name,
                query=query_vector,
                limit=limit,
                score_threshold=threshold,
            )

            # 转换为RetrievalResult - 结果在points属性中
            for point in search_results.points:
                results.append(
                    RetrievalResult(
                        content=point.payload.get("text", point.payload.get("title", "")),
                        source=f"qdrant:{collection_name}",
                        score=point.score,
                        metadata={"id": point.id, "payload": point.payload},
                    )
                )

            logger.info(f"  📊 {collection_name}: {len(results)}条结果")

        except Exception as e:
            logger.warning(f"⚠️ Qdrant检索 {collection_name} 失败: {e}")

        return results

    def _build_enhanced_context(self, rag_context: RAGContext, strategy: dict[str, Any]) -> str:
        """
        构建增强上下文

        Args:
            rag_context: RAG上下文
            strategy: 检索策略

        Returns:
            增强后的上下文字符串
        """
        # 获取Top结果
        top_results = rag_context.get_top_results(strategy.get("limit", 5))

        if not top_results:
            return ""

        # 构建上下文
        context_parts = [
            "## 📚 相关资料检索结果",
            "",
            f"基于查询「{rag_context.query}」检索到以下相关资料:",
            "",
        ]

        for i, result in enumerate(top_results, 1):
            score_pct = result.score * 100
            context_parts.extend(
                [
                    f"### {i}. {result.source} (相关度: {score_pct:.1f}%)",
                    "",
                    f"{result.content}",
                    "",
                ]
            )

        # 添加数据来源说明
        if rag_context.data_sources_used:
            context_parts.extend(
                ["---", f"📊 数据来源: {', '.join(rag_context.data_sources_used)}", ""]
            )

        return "\n".join(context_parts)

    def format_context_for_llm(self, rag_context: RAGContext, user_query: str) -> str:
        """
        格式化上下文供LLM使用

        Args:
            rag_context: RAG上下文
            user_query: 用户查询

        Returns:
            格式化后的完整提示词
        """
        parts = []

        # 如果有检索结果,添加增强上下文
        if rag_context.enhanced_context:
            parts.extend(
                [
                    rag_context.enhanced_context,
                    "",
                    "## 🤔 请基于以上资料回答问题:",
                    "",
                    user_query,
                    "",
                ]
            )
        else:
            # 没有检索结果,直接使用用户查询
            parts.append(user_query)

        return "\n".join(parts)


# 单例
_rag_manager: RAGManager | None = None
_bge_classifier_instance = None


def _get_or_create_bge_classifier():
    """
    获取或创建BGE分类器单例

    Returns:
        BGE分类器实例
    """
    global _bge_classifier_instance

    if _bge_classifier_instance is None:
        try:
            from core.intent.bge_m3_intent_classifier import BGE_M3_IntentClassifier

            _bge_classifier_instance = BGE_M3_IntentClassifier()
            logger.info("✅ BGE分类器自动初始化成功")
        except Exception as e:
            logger.warning(f"⚠️ BGE分类器初始化失败: {e}")
            _bge_classifier_instance = None

    return _bge_classifier_instance


def get_rag_manager(qdrant_client=None, bge_classifier=None) -> RAGManager:
    """
    获取RAG管理器单例

    Args:
        qdrant_client: Qdrant客户端
        bge_classifier: BGE分类器(可选,未提供时自动创建)

    Returns:
        RAG管理器实例
    """
    global _rag_manager

    if _rag_manager is None:
        # 如果没有提供BGE分类器,尝试自动创建
        if bge_classifier is None:
            bge_classifier = _get_or_create_bge_classifier()

        _rag_manager = RAGManager(qdrant_client, bge_classifier)

    return _rag_manager
