#!/usr/bin/env python3
"""
Athena平台LlamaIndex混合架构集成
Athena Platform LlamaIndex Hybrid Architecture Integration

保持Athena核心优势 + 选择性引入LlamaIndex工具
"""

from __future__ import annotations
import asyncio
import logging
import sys
import time
from dataclasses import dataclass
from typing import Any

import numpy as np

from core.logging_config import setup_logging

# 添加Athena平台路径
sys.path.append("/Users/xujian/Athena工作平台")

# Athena核心组件
from qdrant_client import QdrantClient

from core.nlp.bge_embedding_service import get_bge_service
from core.vector_db.vector_db_manager import VectorDBManager

# LlamaIndex组件
try:
    from llama_index.core import (
        Document,
        Node,
        NodeWithScore,
        QueryBundle,
        SimpleDirectoryReader,
        StorageContext,
        VectorStoreIndex,
    )
    from llama_index.core.evaluation import (
        BatchEvalRunner,
        FaithfulnessEvaluator,
        RelevancyEvaluator,
    )
    from llama_index.core.extractors import (
        QuestionsAnsweredExtractor,
        SummaryExtractor,
        TitleExtractor,
    )
    from llama_index.core.node_parser import (
        SemanticSplitterNodeParser,
        SentenceSplitter,
    )
    from llama_index.core.postprocessor import (
        KeywordRelevancyPostprocessor,
        SimilarityPostprocessor,
        SimilarityScorer,
    )

    LLAMAINDEX_AVAILABLE = True
except ImportError as e:
    LLAMAINDEX_AVAILABLE = False
    logging.warning(f"LlamaIndex不可用: {e}")

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


@dataclass
class AthenaDocument:
    """Athena文档数据结构"""

    content: str
    metadata: dict[str, Any]
    doc_id: str
    source: str
    doc_type: str
    embedding: list[float] | None = None


class AthenaLlamaIndexProcessor:
    """Athena平台LlamaIndex集成处理器"""

    def __init__(self):
        """初始化处理器"""
        self.name = "Athena-LlamaIndex集成处理器"
        self.version = "1.0.0"

        # 初始化Athena核心服务
        logger.info("🔄 初始化Athena核心服务...")
        self.bge_service = None  # 将在异步初始化中设置
        self.vector_manager = VectorDBManager()
        self.qdrant_client = QdrantClient(host="localhost", port=6333)

        # LlamaIndex组件状态
        self.llamaindex_available = LLAMAINDEX_AVAILABLE

        # 配置
        self.config = {
            "chunk_size": 512,
            "chunk_overlap": 50,
            "vector_dimension": 1024,
            "collection_name": "athena_llamaindex_hybrid",
            "top_k": 10,
            "similarity_threshold": 0.7,
        }

        logger.info(f"✅ {self.name} 初始化完成")
        logger.info(f"   - LlamaIndex可用: {self.llamaindex_available}")
        logger.info(f"   - 向量维度: {self.config['vector_dimension']}")

    async def _ensure_bge_service(self):
        """确保BGE服务已初始化"""
        if self.bge_service is None:
            self.bge_service = await get_bge_service()

    async def process_documents_with_llamaindex(
        self, documents: list[dict[str, Any]], doc_type: str = "default"
    ) -> list[AthenaDocument]:
        """使用LlamaIndex处理文档"""
        logger.info(f"🔄 使用LlamaIndex处理 {len(documents)} 个文档...")

        # 确保BGE服务已初始化
        await self._ensure_bge_service()

        if not self.llamaindex_available:
            # 回退到Athena原生处理
            return await self._process_documents_athena(documents, doc_type)

        try:
            # 转换为LlamaIndex Document格式
            llama_docs = []
            for doc in documents:
                content = doc.get("content", doc.get("text", ""))
                if content:
                    llama_doc = Document(
                        text=content,
                        metadata={
                            **doc.get("metadata", {}),
                            "doc_type": doc_type,
                            "source": doc.get("source", "unknown"),
                            "processed_by": "llamaindex",
                            "processed_time": time.time(),
                        },
                    )
                    llama_docs.append(llama_doc)

            # 使用LlamaIndex进行节点解析
            node_parser = SemanticSplitterNodeParser.from_defaults(
                embed_model=self._get_embedding_model(),
                chunk_size=self.config["chunk_size"],
                chunk_overlap=self.config["chunk_overlap"],
            )

            nodes = node_parser.get_nodes_from_documents(llama_docs)
            logger.info(f"📝 LlamaIndex分块生成 {len(nodes)} 个节点")

            # 转换回Athena格式
            athena_docs = []
            for i, node in enumerate(nodes):
                athena_doc = AthenaDocument(
                    content=node.text,
                    metadata={
                        **node.metadata,
                        "node_id": node.id_,
                        "chunk_index": i,
                        "processed_by": "llamaindex",
                    },
                    doc_id=node.id_,
                    source=node.metadata.get("source", "unknown"),
                    doc_type=doc_type,
                )
                athena_docs.append(athena_doc)

            return athena_docs

        except Exception as e:
            logger.error(f"❌ LlamaIndex处理失败,回退到Athena处理: {e}")
            return await self._process_documents_athena(documents, doc_type)

    async def _process_documents_athena(
        self, documents: list[dict[str, Any]], doc_type: str
    ) -> list[AthenaDocument]:
        """Athena原生文档处理(回退方案)"""
        logger.info("🔄 使用Athena原生文档处理...")

        athena_docs = []
        for i, doc in enumerate(documents):
            content = doc.get("content", doc.get("text", ""))
            if content:
                # 简单分块策略
                chunks = self._simple_chunk(content)

                for j, chunk in enumerate(chunks):
                    athena_doc = AthenaDocument(
                        content=chunk,
                        metadata={
                            **doc.get("metadata", {}),
                            "chunk_index": j,
                            "processed_by": "athena_native",
                        },
                        doc_id=f"athena_{i}_{j}",
                        source=doc.get("source", "unknown"),
                        doc_type=doc_type,
                    )
                    athena_docs.append(athena_doc)

        return athena_docs

    def _simple_chunk(self, text: str, chunk_size: int = 512) -> list[str]:
        """简单文本分块"""
        chunks = []
        current_chunk = ""

        sentences = text.split("。")
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            if len(current_chunk + sentence) < chunk_size:
                current_chunk += sentence + "。"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + "。"

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _get_embedding_model(self) -> Any:
        """获取嵌入模型(适配LlamaIndex)"""

        class AthenaEmbeddingModel:
            def __init__(self, bge_service):
                self.bge_service = bge_service
                self.embed_dim = 1024

            def get_query_embedding(self, query: str) -> list[float]:
                # 同步调用(实际应该是异步的)

                loop = asyncio.new_event_loop()
                try:
                    result = loop.run_until_complete(self.bge_service.encode(query))
                    return result.embeddings[0]
                finally:
                    loop.close()

            def get_text_embedding_batch(self, texts: list[str]) -> list[list[float]]:
                # 同步调用(实际应该是异步的)

                loop = asyncio.new_event_loop()
                try:
                    result = loop.run_until_complete(self.bge_service.encode(texts))
                    return result.embeddings
                finally:
                    loop.close()

            def similarity(
                self, query_embedding: list[float], text_embedding: list[float]
            ) -> float:

                query_np = np.array(query_embedding)
                text_np = np.array(text_embedding)
                return np.dot(query_np, text_np) / (
                    np.linalg.norm(query_np) * np.linalg.norm(text_np)
                )

        return AthenaEmbeddingModel(self.bge_service)


async def main():
    """测试Athena-LlamaIndex集成"""
    print("🚀 Athena-LlamaIndex混合架构集成测试")
    print("=" * 60)

    processor = AthenaLlamaIndexProcessor()

    # 测试文档
    test_documents = [
        {
            "content": "专利法是保护发明创造的重要法律制度。发明专利的保护期为二十年,实用新型专利的保护期为十年。",
            "metadata": {"category": "法律条文", "source": "专利法"},
            "source": "patent_law.md",
        },
        {
            "content": "权利要求书应当清楚、简要地限定要求专利保护的范围。权利要求书应当以说明书为依据。",
            "metadata": {"category": "法律条文", "source": "专利实施细则"},
            "source": "patent_rules.md",
        },
    ]

    # 处理文档
    processed_docs = await processor.process_documents_with_llamaindex(
        test_documents, "专利法律法规"
    )

    print("\n📊 处理结果:")
    print(f"   - 处理文档数: {len(processed_docs)}")
    print(
        f"   - 处理方式: {processed_docs[0].metadata.get('processed_by', 'unknown') if processed_docs else 'N/A'}"
    )

    # 显示处理结果
    for i, doc in enumerate(processed_docs[:3]):  # 只显示前3个
        print(f"\n📄 文档 {i+1}:")
        print(f"   - ID: {doc.doc_id}")
        print(f"   - 类型: {doc.doc_type}")
        print(f"   - 长度: {len(doc.content)} 字符")
        print(f"   - 来源: {doc.source}")
        print(f"   - 处理器: {doc.metadata.get('processed_by', 'unknown')}")
        print(f"   - 内容预览: {doc.content[:100]}...")


# 入口点: @async_main装饰器已添加到main函数
