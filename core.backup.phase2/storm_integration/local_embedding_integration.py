#!/usr/bin/env python3
from __future__ import annotations
"""
本地 Embedding 模型集成

使用 Athena 平台已有的本地模型:
- BAAI/bge-m3 (converted/)
- "BAAI/bge-m3" (converted/)
- 支持 MPS (Apple Silicon GPU) 优化

作者: Athena 平台团队
创建时间: 2026-01-02
"""

import asyncio
from pathlib import Path
from typing import Any

import torch

from core.logging_config import setup_logging

logger = setup_logging()


class LocalEmbeddingModel:
    """
    本地 Embedding 模型

    使用 Athena 平台已有的本地模型,支持 MPS 加速
    """

    # 可用的本地模型
    AVAILABLE_MODELS = {
        "bge-large-zh": {
            "path": Path("http://127.0.0.1:8766/v1/embeddings"),
            "dim": 1024,
            "max_seq_length": 512,
        },
        "bge-base-zh": {
            "path": Path("http://127.0.0.1:8766/v1/embeddings"),
            "dim": 768,
            "max_seq_length": 512,
        },
        "bge-reranker-large": {
            "path": Path("/Users/xujian/Athena工作平台/models/converted/bge-reranker-large"),
            "dim": 1024,
            "max_seq_length": 512,
        },
    }

    def __init__(self, model_name: str = "bge-large-zh", device: str | None = None):
        """
        初始化本地 Embedding 模型

        Args:
            model_name: 模型名称 (bge-large-zh, bge-base-zh)
            device: 设备 (auto, cpu, mps, cuda)
        """
        self.model_name = model_name
        self.model_path = self.AVAILABLE_MODELS[model_name]["path"]
        self.embedding_dim = self.AVAILABLE_MODELS[model_name]["dim"]

        # 自动选择设备
        if device is None:
            if torch.backends.mps.is_available():
                device = "mps"
                logger.info("✅ 检测到 Apple Silicon GPU,使用 MPS 加速")
            elif torch.cuda.is_available():
                device = "cuda"
                logger.info("✅ 检测到 NVIDIA GPU,使用 CUDA 加速")
            else:
                device = "cpu"
                logger.info("使用 CPU 运行")

        self.device = torch.device(device)
        self._model = None
        self._tokenizer = None
        self._loaded = False

        logger.info(f"初始化本地 Embedding 模型: {model_name}")
        logger.info(f"模型路径: {self.model_path}")
        logger.info(f"设备: {self.device}")

    def load(self) -> Any:
        """加载模型"""
        if self._loaded:
            return

        try:
            from transformers import AutoModel, AutoTokenizer

            logger.info("正在加载模型...")

            # 加载 tokenizer
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_path, trust_remote_code=True)

            # 加载模型
            self._model = AutoModel.from_pretrained(self.model_path, trust_remote_code=True)

            # 移动到指定设备
            self._model = self._model.to(self.device)

            # 设置为评估模式
            self._model.eval()

            self._loaded = True

            logger.info("✅ 模型加载成功!")
            logger.info(f"   向量维度: {self.embedding_dim}")
            logger.info(f"   设备: {self.device}")

        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            self._loaded = False

    def encode(self, texts: list[str], normalize: bool = True) -> list[list[float]]:
        """
        生成文本向量

        Args:
            texts: 文本列表
            normalize: 是否归一化

        Returns:
            向量列表
        """
        if not self._loaded:
            logger.warning("模型未加载,返回零向量")
            return [[0.0] * self.embedding_dim for _ in texts]

        try:
            import torch

            # Tokenize
            inputs = self._tokenizer(
                texts, padding=True, truncation=True, max_length=512, return_tensors="pt"
            )

            # 移动到相同设备
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # 生成向量
            with torch.no_grad():
                outputs = self._model(**inputs)
                # 使用 [CLS] token 或 mean pooling
                embeddings = outputs.last_hidden_state[:, 0, :].cpu()

                if normalize:
                    # L2 归一化
                    embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)

            return embeddings.tolist()

        except Exception as e:
            logger.error(f"生成向量失败: {e}")
            return [[0.0] * self.embedding_dim for _ in texts]

    def encode_single(self, text: str, normalize: bool = True) -> list[float]:
        """生成单个文本的向量"""
        return self.encode([text], normalize)[0]

    @property
    def dimension(self) -> int:
        """获取向量维度"""
        return self.embedding_dim


class OptimizedQdrantRetriever:
    """
    优化的 Qdrant 检索器

    使用本地 Embedding 模型 + Qdrant 向量检索
    """

    def __init__(
        self,
        collection_name: str = "legal_knowledge",
        embedding_model: LocalEmbeddingModel | None = None,
    ):
        """初始化"""
        self.collection_name = collection_name
        self.embedding_model = embedding_model or LocalEmbeddingModel()
        self._client = None
        self._connected = False

        logger.info("初始化优化的 Qdrant 检索器")

    async def connect(self):
        """连接 Qdrant"""
        try:
            from qdrant_client import QdrantClient

            self._client = QdrantClient(url="http://localhost:6333", timeout=30)
            self._connected = True

            collections = self._client.get_collections()
            collection_names = [c.name for c in collections.collections]

            logger.info("✅ Qdrant 连接成功")
            logger.info(f"📊 可用集合: {collection_names}")

            # 检查集合
            if self.collection_name in collection_names:
                info = self._client.get_collection(self.collection_name)
                logger.info(f"📊 集合 {self.collection_name}: {info.points_count} 个向量")

                # 获取向量维度
                if info.config and info.config.params:
                    vector_size = info.config.params.vectors.size
                    logger.info(f"📊 向量维度: {vector_size}")

        except Exception as e:
            logger.error(f"Qdrant 连接失败: {e}")
            self._connected = False

    async def search_with_local_embedding(self, query: str, limit: int = 10) -> list[dict]:
        """
        使用本地 Embedding 进行向量检索

        Args:
            query: 查询文本
            limit: 返回数量

        Returns:
            检索结果
        """
        if not self._connected:
            logger.warning("Qdrant 未连接")
            return []

        try:
            # 加载本地模型
            self.embedding_model.load()

            # 生成查询向量
            logger.info(f"生成查询向量: {query[:50]}...")
            query_vector = self.embedding_model.encode_single(query)
            logger.info(f"✅ 向量生成成功,维度: {len(query_vector)}")

            # 执行检索 - 使用 query_points API
            logger.info("执行向量检索...")
            search_result = self._client.query_points(
                collection_name=self.collection_name,
                query=query_vector,  # 直接传入向量列表
                limit=limit,
                with_payload=True,
                score_threshold=None,  # 不设置阈值,返回所有结果
            )

            results = []
            # query_points 返回的是 QueryResponse 对象,需要访问 .points 属性
            for hit in search_result.points:
                results.append(
                    {
                        "id": hit.id,
                        "score": hit.score,
                        "payload": hit.payload,
                        "relevance_score": hit.score,
                    }
                )

            logger.info(f"✅ 检索到 {len(results)} 条结果")

            return results

        except Exception as e:
            logger.error(f"向量检索失败: {e}")
            import traceback

            traceback.print_exc()
            return []

    async def close(self):
        """关闭连接"""
        if self._client:
            self._client.close()


async def test_local_embedding():
    """测试本地 Embedding 和 Qdrant"""
    # setup_logging()  # 日志配置已移至模块导入

    logger.info("=" * 70)
    logger.info("测试本地 Embedding 模型 + Qdrant")
    logger.info("=" * 70)

    # 创建检索器
    retriever = OptimizedQdrantRetriever(
        collection_name="legal_knowledge",
        embedding_model=LocalEmbeddingModel(model_name="bge-large-zh"),
    )

    # 连接
    await retriever.connect()

    if retriever._connected:
        # 测试检索
        query = "专利创造性判断的标准和依据"
        logger.info(f"\n测试查询: {query}\n")

        results = await retriever.search_with_local_embedding(query, limit=5)

        logger.info(f"\n{'='*70}")
        logger.info(f"检索结果: {len(results)} 条")
        logger.info(f"{'='*70}\n")

        for i, result in enumerate(results, 1):
            logger.info(f"{i}. [ID: {result['id']}] 相关性: {result['relevance_score']:.4f}")
            payload = result.get("payload", {})
            if "text" in payload:
                logger.info(f"   内容: {payload['text'][:100]}...")
            elif "content" in payload:
                logger.info(f"   内容: {payload['content'][:100]}...")
            if "metadata" in payload:
                logger.info(f"   元数据: {payload['metadata']}")
            logger.info("")

    await retriever.close()

    logger.info(f"\n{'='*70}")
    logger.info("测试完成!")
    logger.info(f"{'='*70}")


if __name__ == "__main__":
    asyncio.run(test_local_embedding())
