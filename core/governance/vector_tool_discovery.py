#!/usr/bin/env python3
from __future__ import annotations
"""
向量嵌入工具发现模块
Vector Embedding Tool Discovery Module

提供基于语义相似度的智能工具发现功能,包括:
- sentence-transformers向量嵌入
- 语义相似度搜索
- 中英文混合查询支持
- 多语言向量索引

使用方法:
    from core.governance.vector_tool_discovery import VectorToolDiscovery

    discovery = VectorToolDiscovery(tool_metadata)
    results = await discovery.discover_tools("搜索专利相关文档", limit=10)
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


# ================================
# 向量嵌入器接口
# ================================


class VectorEmbedder:
    """向量嵌入器抽象类"""

    def __init__(
        self,
        model_name: str = "paraphrase-multilingual-MiniLM-L12-v2",
        model_path: str | None = None,
    ):
        """
        初始化向量嵌入器

        Args:
            model_name: 模型名称
            model_path: 本地模型路径(如果为None,使用默认平台路径)
        """
        self.model_name = model_name
        self.model = None

        # 本地模型路径
        if model_path is None:
            # 使用平台内的模型路径
            self.model_path = "/Users/xujian/Athena工作平台/models/converted/paraphrase-multilingual-MiniLM-L12-v2"
        else:
            self.model_path = model_path

        self._initialize_model()

    def _initialize_model(self) -> Any:
        """初始化模型(延迟加载,仅使用本地模型)"""
        try:
            import os

            from sentence_transformers import SentenceTransformer

            logger.info(f"🔄 正在加载向量嵌入模型: {self.model_name}")
            logger.info(f"📂 模型路径: {self.model_path}")

            # 检查本地模型是否存在
            if not os.path.exists(self.model_path):
                raise OSError(f"本地模型不存在: {self.model_path}")

            # 加载本地模型
            self.model = SentenceTransformer(self.model_path)
            logger.info("✅ 向量嵌入模型加载成功")
        except ImportError:
            logger.warning("⚠️ sentence-transformers未安装,向量搜索功能不可用")
            logger.info("💡 安装命令: pip install sentence-transformers")
        except OSError as e:
            logger.error(f"❌ 模型加载失败: {e}")
            logger.info(f"💡 请检查模型路径: {self.model_path}")
        except Exception as e:
            logger.error(f"❌ 向量嵌入模型加载失败: {e}")

    def encode(self, texts: list[str]) -> np.ndarray | None:
        """
        将文本编码为向量

        Args:
            texts: 文本列表

        Returns:
            向量数组 (n x dim) 或 None(如果模型未加载)
        """
        if self.model is None:
            return None

        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
            return embeddings
        except Exception as e:
            logger.error(f"❌ 向量编码失败: {e}")
            return None

    def is_available(self) -> bool:
        """检查向量嵌入器是否可用"""
        return self.model is not None


# ================================
# 向量工具发现器
# ================================


class VectorToolDiscovery:
    """向量工具发现器"""

    def __init__(
        self,
        tool_metadata: dict[str, Any],        model_name: str = "paraphrase-multilingual-MiniLM-L12-v2",
        cache_dir: str | None = None,
    ):
        """
        初始化向量工具发现器

        Args:
            tool_metadata: 工具元数据字典 {tool_id: ToolMetadata}
            model_name: sentence-transformers模型名称
            cache_dir: 向量缓存目录
        """
        self.tool_metadata = tool_metadata
        self.cache_dir = Path(cache_dir) if cache_dir else Path(".cache/vector_discovery")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 初始化向量嵌入器
        self.embedder = VectorEmbedder(model_name)

        # 向量索引
        self.tool_embeddings = None
        self.tool_ids = []

        # 缓存文件路径
        self.cache_file = self.cache_dir / "tool_embeddings.npz"

        # 构建索引
        self._build_index()

    def _build_index(self) -> Any:
        """构建向量索引"""
        if not self.embedder.is_available():
            logger.warning("⚠️ 向量嵌入器不可用,跳过向量索引构建")
            return

        # 尝试从缓存加载
        if self._load_from_cache():
            logger.info("✅ 从缓存加载向量索引")
            return

        # 构建新的向量索引
        logger.info("🔄 正在构建向量索引...")
        start_time = datetime.now()

        try:
            # 准备文本
            texts = []
            self.tool_ids = []

            for tool_id, metadata in self.tool_metadata.items():
                # 组合多个文本字段以提高语义表示
                combined_text = self._prepare_tool_text(metadata)
                texts.append(combined_text)
                self.tool_ids.append(tool_id)

            # 生成向量
            embeddings = self.embedder.encode(texts)

            if embeddings is not None:
                self.tool_embeddings = embeddings
                logger.info(f"✅ 向量索引构建完成: {len(embeddings)} 个工具")

                # 保存到缓存
                self._save_to_cache()

                elapsed = (datetime.now() - start_time).total_seconds()
                logger.info(f"⏱️ 构建耗时: {elapsed:.2f}秒")

        except Exception as e:
            logger.error(f"❌ 向量索引构建失败: {e}")

    def _prepare_tool_text(self, metadata) -> str:
        """
        准备工具的文本表示

        Args:
            metadata: 工具元数据

        Returns:
            组合后的文本
        """
        parts = []

        # 1. 工具名称(权重最高)
        if metadata.name:
            parts.append(f"名称: {metadata.name}")

        # 2. 工具描述
        if metadata.description:
            parts.append(f"描述: {metadata.description}")

        # 3. 能力列表
        if metadata.capabilities:
            capabilities_text = "功能: " + "; ".join(metadata.capabilities)
            parts.append(capabilities_text)

        # 4. 类别
        if metadata.category:
            parts.append(f"类别: {metadata.category.value}")

        # 用空格连接
        return " ".join(parts)

    def _load_from_cache(self) -> bool:
        """从缓存加载向量索引"""
        if not self.cache_file.exists():
            return False

        try:
            data = np.load(self.cache_file, allow_pickle=True)
            self.tool_embeddings = data["embeddings"]
            self.tool_ids = data["tool_ids"].tolist()
            return True
        except Exception as e:
            logger.warning(f"⚠️ 缓存加载失败: {e}")
            return False

    def _save_to_cache(self) -> Any:
        """保存向量索引到缓存"""
        try:
            np.savez_compressed(
                self.cache_file, embeddings=self.tool_embeddings, tool_ids=np.array(self.tool_ids)
            )
            logger.info(f"✅ 向量索引已缓存: {self.cache_file}")
        except Exception as e:
            logger.warning(f"⚠️ 缓存保存失败: {e}")

    async def discover_tools(
        self, query: str, limit: int = 10, category: str | None = None, threshold: float = 0.3
    ) -> list[dict[str, Any]]:
        """
        基于语义相似度发现工具

        Args:
            query: 查询描述(支持中英文混合)
            limit: 返回数量限制
            category: 工具类别过滤
            threshold: 相似度阈值(0-1),低于此值的结果将被过滤

        Returns:
            匹配的工具列表,按相似度排序
        """
        if self.tool_embeddings is None:
            logger.warning("⚠️ 向量索引不可用,返回空结果")
            return []

        try:
            # 1. 编码查询
            query_embedding = self.embedder.encode([query])

            if query_embedding is None:
                return []

            # 2. 计算相似度(余弦相似度)
            similarities = self._cosine_similarity(query_embedding[0], self.tool_embeddings)

            # 3. 过滤和排序
            results = []
            for idx, tool_id in enumerate(self.tool_ids):
                similarity = similarities[idx]

                # 状态过滤
                metadata = self.tool_metadata[tool_id]
                if metadata.status.value != "available":
                    continue

                # 类别过滤
                if category and metadata.category.value != category:
                    continue

                # 阈值过滤
                if similarity < threshold:
                    continue

                results.append(
                    {
                        "tool_id": tool_id,
                        "name": metadata.name,
                        "description": metadata.description,
                        "category": metadata.category.value,
                        "score": float(similarity),  # 语义相似度分数
                        "success_rate": metadata.success_rate,
                    }
                )

            # 4. 按相似度排序
            results.sort(key=lambda x: x["score"], reverse=True)

            logger.info(f"✅ 向量搜索发现 {len(results)} 个相关工具(查询: {query})")

            return results[:limit]

        except Exception as e:
            logger.error(f"❌ 向量搜索失败: {e}")
            return []

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> np.ndarray:
        """
        计算余弦相似度

        Args:
            vec1: 向量1 (dim,)
            vec2: 向量矩阵 (n, dim)

        Returns:
            相似度数组 (n,)
        """
        # 归一化
        vec1_norm = vec1 / (np.linalg.norm(vec1) + 1e-8)
        vec2_norm = vec2 / (np.linalg.norm(vec2, axis=1, keepdims=True) + 1e-8)

        # 点积
        similarities = np.dot(vec2_norm, vec1_norm)

        return similarities

    async def hybrid_discover(
        self,
        query: str,
        limit: int = 10,
        category: str | None = None,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3,
    ) -> list[dict[str, Any]]:
        """
        混合搜索:向量搜索 + 关键词搜索

        Args:
            query: 查询描述
            limit: 返回数量限制
            category: 工具类别过滤
            vector_weight: 向量搜索权重
            keyword_weight: 关键词搜索权重

        Returns:
            匹配的工具列表
        """
        # 向量搜索
        vector_results = await self.discover_tools(query, limit=limit * 2, category=category)

        # 关键词搜索(导入增强工具发现模块)
        try:
            from core.governance.enhanced_tool_discovery import EnhancedToolDiscovery

            keyword_discovery = EnhancedToolDiscovery(self.tool_metadata)
            keyword_results = await keyword_discovery.discover_tools(
                query, limit=limit * 2, category=category
            )
        except Exception as e:
            logger.warning(f"⚠️ 关键词搜索失败,仅使用向量搜索: {e}")
            keyword_results = []

        # 合并结果
        combined_scores = {}

        # 向量搜索分数
        for result in vector_results:
            tool_id = result["tool_id"]
            combined_scores[tool_id] = {
                "tool_id": tool_id,
                "name": result["name"],
                "description": result["description"],
                "category": result["category"],
                "score": result["score"] * vector_weight,
                "success_rate": result["success_rate"],
                "vector_score": result["score"],
                "keyword_score": 0.0,
            }

        # 关键词搜索分数
        for result in keyword_results:
            tool_id = result["tool_id"]
            if tool_id in combined_scores:
                combined_scores[tool_id]["keyword_score"] = result["score"]
                combined_scores[tool_id]["score"] += result["score"] * keyword_weight
            else:
                combined_scores[tool_id] = {
                    "tool_id": tool_id,
                    "name": result["name"],
                    "description": result["description"],
                    "category": result["category"],
                    "score": result["score"] * keyword_weight,
                    "success_rate": result["success_rate"],
                    "vector_score": 0.0,
                    "keyword_score": result["score"],
                }

        # 排序并返回
        results = sorted(combined_scores.values(), key=lambda x: x["score"], reverse=True)

        logger.info(f"✅ 混合搜索发现 {len(results)} 个相关工具")

        return results[:limit]

    def get_statistics(self) -> dict[str, Any]:
        """
        获取向量发现器统计信息

        Returns:
            统计信息字典
        """
        stats = {
            "total_tools": len(self.tool_metadata),
            "indexed_tools": len(self.tool_ids),
            "model_name": self.embedder.model_name,
            "model_available": self.embedder.is_available(),
            "vector_dimension": (
                self.tool_embeddings.shape[1] if self.tool_embeddings is not None else 0
            ),
            "cache_file": str(self.cache_file) if self.cache_file.exists() else "Not cached",
        }

        return stats


# ================================
# 便捷函数
# ================================


async def discover_tools_vector(
    tool_metadata: dict[str, Any], query: str, limit: int = 10, use_hybrid: bool = True, **kwargs
) -> list[dict[str, Any]]:
    """
    向量工具发现的便捷函数

    Args:
        tool_metadata: 工具元数据字典
        query: 查询描述
        limit: 返回数量限制
        use_hybrid: 是否使用混合搜索
        **kwargs: 其他参数

    Returns:
        匹配的工具列表
    """
    discovery = VectorToolDiscovery(tool_metadata)

    if use_hybrid:
        return await discovery.hybrid_discover(query, limit, **kwargs)
    else:
        return await discovery.discover_tools(query, limit, **kwargs)
