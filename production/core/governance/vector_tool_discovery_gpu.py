#!/usr/bin/env python3
from __future__ import annotations
"""
GPU加速向量嵌入工具发现模块
GPU-Accelerated Vector Embedding Tool Discovery Module

提供基于GPU加速的语义相似度工具发现功能,包括:
- mac_os MPS (Metal Performance Shaders) 加速
- PyTorch CUDA加速
- 自动GPU检测和回退
- 性能监控和对比

使用方法:
    from core.governance.vector_tool_discovery_gpu import GPUVectorToolDiscovery

    discovery = GPUVectorToolDiscovery(tool_metadata, use_gpu=True)
    results = await discovery.discover_tools("搜索专利相关文档", limit=10)
"""

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

# 🆕 导入M4 Pro优化组件
try:
    from modules.nlp.xiaonuo_nlp_deployment.apple_silicon_optimizer_fixed import (
        get_apple_silicon_optimizer_fixed,
    )

    from core.acceleration.dynamic_batch_optimizer import get_batch_optimizer
    from core.memory.layered_model_loader import ModelTier, get_model_loader
    from core.memory.m4_unified_memory_pool import get_memory_pool

    M4_OPTIMIZATION_AVAILABLE = True
    logger.info("✅ M4 Pro优化组件已导入")
except ImportError as e:
    M4_OPTIMIZATION_AVAILABLE = False
    logger.warning(f"⚠️ M4 Pro优化组件不可用: {e}")


# ================================
# GPU设备检测器
# ================================


class GPUDetector:
    """GPU设备检测器"""

    @staticmethod
    def detect_available_device() -> dict[str, Any]:
        """
        检测可用的GPU设备

        Returns:
            设备信息字典
        """
        device_info = {
            "device_type": "cpu",  # cpu, mps, cuda
            "device_name": "CPU",
            "available": False,
            "device": None,
        }

        try:
            import torch

            # 检查MPS (mac_os Metal Performance Shaders)
            if torch.backends.mps.is_available() and torch.backends.mps.is_built():
                device_info.update(
                    {
                        "device_type": "mps",
                        "device_name": "Apple Metal (MPS)",
                        "available": True,
                        "device": torch.device("mps"),
                    }
                )
                logger.info("✅ 检测到Apple Metal GPU加速 (MPS)")
                return device_info

            # 检查CUDA (NVIDIA GPU)
            if torch.cuda.is_available():
                device_name = torch.cuda.get_device_name(0)
                device_info.update(
                    {
                        "device_type": "cuda",
                        "device_name": f"NVIDIA CUDA ({device_name})",
                        "available": True,
                        "device": torch.device("cuda:0"),
                    }
                )
                logger.info(f"✅ 检测到NVIDIA CUDA GPU: {device_name}")
                return device_info

            # 无GPU可用
            logger.info("⚠️ 未检测到GPU,使用CPU")
            device_info["device"] = torch.device("cpu")
            return device_info

        except ImportError:
            logger.warning("⚠️ PyTorch未安装,无法使用GPU加速")
            return device_info
        except Exception as e:
            logger.error(f"❌ GPU检测失败: {e}")
            return device_info


# ================================
# GPU加速向量嵌入器
# ================================


class GPUVectorEmbedder:
    """GPU加速向量嵌入器"""

    def __init__(
        self,
        model_name: str = "paraphrase-multilingual-MiniLM-L12-v2",
        use_gpu: bool = True,
        device: Any | None = None,
        model_path: str | None = None,
    ):
        """
        初始化GPU加速向量嵌入器(M4 Pro优化版)

        Args:
            model_name: sentence-transformers模型名称
            use_gpu: 是否尝试使用GPU
            device: 指定设备(自动检测如果为None)
            model_path: 本地模型路径(如果为None,使用默认平台路径)
        """
        self.model_name = model_name
        self.use_gpu = use_gpu
        self.model = None
        self.device = device
        self.device_info = {}

        # 本地模型路径
        if model_path is None:
            # 使用平台内的模型路径
            self.model_path = "/Users/xujian/Athena工作平台/models/converted/paraphrase-multilingual-MiniLM-L12-v2"
        else:
            self.model_path = model_path

        # 性能统计
        self.encode_times = []

        # 🆕 M4 Pro优化组件初始化
        self.m4_optimization_enabled = False
        if M4_OPTIMIZATION_AVAILABLE:
            try:
                self.mps_optimizer = get_apple_silicon_optimizer_fixed()
                self.batch_optimizer = get_batch_optimizer()
                self.memory_pool = get_memory_pool()
                self.model_loader = get_model_loader()

                # 🆕 注册模型到内存池(HOT层,常驻GPU)
                self.memory_pool.register_model(
                    name=self.model_name,
                    path=self.model_path,
                    tier=ModelTier.HOT,
                    size_mb=400,  # paraphrase-multilingual-MiniLM-L12-v2大小
                )

                self.m4_optimization_enabled = True
                logger.info("⚡ M4 Pro优化已启用")
            except Exception as e:
                logger.warning(f"⚠️ M4 Pro优化初始化失败: {e}")

        self._initialize_model()

    def _initialize_model(self) -> Any:
        """初始化模型(GPU加速,仅使用本地模型)"""
        try:
            import os

            import torch
            from sentence_transformers import SentenceTransformer

            # 设置环境变量,禁止下载模型
            os.environ["HF_HUB_OFFLINE"] = "1"
            os.environ["TRANSFORMERS_OFFLINE"] = "1"

            # 检测GPU
            if self.use_gpu and self.device is None:
                self.device_info = GPUDetector.detect_available_device()
                self.device = self.device_info.get("device")
            elif self.device:
                self.device_info = {
                    "device_type": self.device.type,
                    "device_name": str(self.device),
                    "available": True,
                }

            # 加载模型(仅使用本地缓存)
            logger.info(f"🔄 正在加载向量嵌入模型: {self.model_name}")
            logger.info(f"📍 设备: {self.device_info.get('device_name', 'CPU')}")
            logger.info(f"📂 模型路径: {self.model_path}")

            # 检查本地模型是否存在
            if not os.path.exists(self.model_path):
                raise OSError(f"本地模型不存在: {self.model_path}")

            # 加载本地模型
            self.model = SentenceTransformer(self.model_path)

            # 移动模型到GPU
            if self.device and self.device.type != "cpu":
                try:
                    self.model = self.model.to(self.device)
                    logger.info(f"✅ 模型已移动到 {self.device_info.get('device_name')}")
                except Exception as e:
                    logger.warning(f"⚠️ 无法移动模型到GPU: {e},使用CPU")
                    self.device = torch.device("cpu")
                    self.device_info["device_type"] = "cpu"
                    self.device_info["device_name"] = "CPU"

            logger.info("✅ 向量嵌入模型加载成功")

        except ImportError:
            logger.warning("⚠️ sentence-transformers未安装")
            logger.info("💡 安装命令: pip install sentence-transformers")
        except OSError as e:
            if "offline" in str(e).lower() or "download" in str(e).lower():
                logger.error(f"❌ 本地未找到模型: {self.model_name}")
                logger.info("💡 请确保模型已下载到本地缓存目录")
            else:
                logger.error(f"❌ 向量嵌入模型加载失败: {e}")
        except Exception as e:
            logger.error(f"❌ 向量嵌入模型加载失败: {e}")

    def encode(self, texts: list[str], batch_size: int | None = None) -> np.ndarray | None:
        """
        将文本编码为向量(GPU加速 + M4 Pro动态批处理优化)

        Args:
            texts: 文本列表
            batch_size: 批处理大小(None表示自动优化,M4 Pro模式)

        Returns:
            向量数组 (n x dim) 或 None
        """
        if self.model is None:
            return None

        start_time = time.time()

        try:

            # 🆕 M4 Pro动态批处理优化
            if self.m4_optimization_enabled and batch_size is None:
                # 根据GPU内存和文本数量自动计算最优batch_size
                batch_size = self.batch_optimizer.get_optimal_batch_size(
                    num_inputs=len(texts), model_type="embedding"
                )
                logger.debug(f"🔄 M4 Pro动态批处理大小: {batch_size}")
            elif self.device and self.device.type != "cpu" and batch_size is None:
                # GPU加速:使用更大的batch_size(兼容模式)
                batch_size = min(32 * 4, 128)
            elif batch_size is None:
                # 默认batch_size
                batch_size = 32

            # 编码
            embeddings = self.model.encode(
                texts,
                convert_to_numpy=True,
                show_progress_bar=False,
                batch_size=batch_size,
                device=self.device,
            )

            # 记录性能
            elapsed = time.time() - start_time
            self.encode_times.append(elapsed)

            if len(self.encode_times) % 10 == 0:
                avg_time = np.mean(self.encode_times[-10:])
                logger.debug(
                    f"⚡ 平均编码时间: {avg_time:.3f}秒 ({len(texts)}个文本, batch={batch_size})"
                )

            return embeddings

        except Exception as e:
            logger.error(f"❌ 向量编码失败: {e}")
            return None

    def is_available(self) -> bool:
        """检查向量嵌入器是否可用"""
        return self.model is not None

    def is_using_gpu(self) -> bool:
        """检查是否正在使用GPU"""
        return self.device and self.device.type != "cpu"

    def get_performance_stats(self) -> dict[str, Any]:
        """获取性能统计"""
        if not self.encode_times:
            return {}

        return {
            "total_encodes": len(self.encode_times),
            "avg_time": float(np.mean(self.encode_times)),
            "min_time": float(np.min(self.encode_times)),
            "max_time": float(np.max(self.encode_times)),
            "device_type": self.device_info.get("device_type", "cpu"),
            "device_name": self.device_info.get("device_name", "CPU"),
        }


# ================================
# GPU加速相似度计算
# ================================


class GPUSimilarityCalculator:
    """GPU加速相似度计算器"""

    def __init__(self, device: Any | None = None):
        """
        初始化GPU相似度计算器

        Args:
            device: 计算设备
        """
        self.device = device
        self.use_gpu = device and device.type != "cpu"

    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> np.ndarray:
        """
        计算余弦相似度(GPU加速)

        Args:
            vec1: 向量1 (dim,)
            vec2: 向量矩阵 (n, dim)

        Returns:
            相似度数组 (n,)
        """
        if not self.use_gpu:
            # CPU回退
            return self._cosine_similarity_cpu(vec1, vec2)

        try:
            import torch

            # 转换为GPU张量
            vec1_gpu = torch.from_numpy(vec1).float().to(self.device)
            vec2_gpu = torch.from_numpy(vec2).float().to(self.device)

            # 归一化
            vec1_norm = vec1_gpu / (torch.norm(vec1_gpu) + 1e-8)
            vec2_norm = vec2_gpu / (torch.norm(vec2_gpu, dim=1, keepdim=True) + 1e-8)

            # 点积
            similarities = torch.matmul(vec2_norm, vec1_norm)

            # 转回CPU
            return similarities.cpu().numpy()

        except Exception as e:
            logger.warning(f"⚠️ GPU计算失败,回退到CPU: {e}")
            return self._cosine_similarity_cpu(vec1, vec2)

    def _cosine_similarity_cpu(self, vec1: np.ndarray, vec2: np.ndarray) -> np.ndarray:
        """CPU余弦相似度计算"""
        vec1_norm = vec1 / (np.linalg.norm(vec1) + 1e-8)
        vec2_norm = vec2 / (np.linalg.norm(vec2, axis=1, keepdims=True) + 1e-8)
        return np.dot(vec2_norm, vec1_norm)


# ================================
# GPU加速向量工具发现器
# ================================


class GPUVectorToolDiscovery:
    """GPU加速向量工具发现器"""

    def __init__(
        self,
        tool_metadata: dict[str, Any],        model_name: str = "paraphrase-multilingual-MiniLM-L12-v2",
        cache_dir: str | None = None,
        use_gpu: bool = True,
    ):
        """
        初始化GPU加速向量发现器

        Args:
            tool_metadata: 工具元数据字典
            model_name: sentence-transformers模型名称
            cache_dir: 向量缓存目录
            use_gpu: 是否使用GPU加速
        """
        self.tool_metadata = tool_metadata
        self.cache_dir = Path(cache_dir) if cache_dir else Path(".cache/vector_discovery")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # GPU检测
        gpu_info = GPUDetector.detect_available_device()
        self.device = gpu_info.get("device") if use_gpu else None
        self.use_gpu = self.device is not None and gpu_info.get("available", False)

        logger.info(f"🎮 GPU加速: {'启用' if self.use_gpu else '禁用'}")
        if self.use_gpu:
            logger.info(f"📍 设备: {gpu_info.get('device_name')}")

        # 初始化嵌入器
        self.embedder = GPUVectorEmbedder(
            model_name=model_name, use_gpu=use_gpu, device=self.device
        )

        # 相似度计算器
        self.similarity_calc = GPUSimilarityCalculator(self.device)

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
                combined_text = self._prepare_tool_text(metadata)
                texts.append(combined_text)
                self.tool_ids.append(tool_id)

            # 生成向量(GPU加速)
            logger.info("⚡ 使用GPU加速生成向量...")
            embeddings = self.embedder.encode(texts, batch_size=64)

            if embeddings is not None:
                self.tool_embeddings = embeddings
                logger.info(f"✅ 向量索引构建完成: {len(embeddings)} 个工具")

                # 性能统计
                stats = self.embedder.get_performance_stats()
                if stats:
                    logger.info(f"📊 编码性能: {stats.get('avg_time', 0):.3f}秒/批次")

                # 保存到缓存
                self._save_to_cache()

                elapsed = (datetime.now() - start_time).total_seconds()
                logger.info(f"⏱️ 构建耗时: {elapsed:.2f}秒")

        except Exception as e:
            logger.error(f"❌ 向量索引构建失败: {e}")

    def _prepare_tool_text(self, metadata) -> str:
        """准备工具的文本表示"""
        parts = []

        if metadata.name:
            parts.append(f"名称: {metadata.name}")
        if metadata.description:
            parts.append(f"描述: {metadata.description}")
        if metadata.capabilities:
            capabilities_text = "功能: " + "; ".join(metadata.capabilities)
            parts.append(capabilities_text)
        if metadata.category:
            parts.append(f"类别: {metadata.category.value}")

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
        基于语义相似度发现工具(GPU加速)

        Args:
            query: 查询描述
            limit: 返回数量限制
            category: 工具类别过滤
            threshold: 相似度阈值

        Returns:
            匹配的工具列表
        """
        if self.tool_embeddings is None:
            logger.warning("⚠️ 向量索引不可用,返回空结果")
            return []

        try:
            # 编码查询(GPU加速)
            query_embedding = self.embedder.encode([query])

            if query_embedding is None:
                return []

            # 计算相似度(GPU加速)
            similarities = self.similarity_calc.cosine_similarity(
                query_embedding[0], self.tool_embeddings
            )

            # 过滤和排序
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
                        "score": float(similarity),
                        "success_rate": metadata.success_rate,
                    }
                )

            # 按相似度排序
            results.sort(key=lambda x: x["score"], reverse=True)

            logger.info(f"✅ 向量搜索发现 {len(results)} 个相关工具(查询: {query})")

            return results[:limit]

        except Exception as e:
            logger.error(f"❌ 向量搜索失败: {e}")
            return []

    async def hybrid_discover(
        self,
        query: str,
        limit: int = 10,
        category: str | None = None,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3,
    ) -> list[dict[str, Any]]:
        """混合搜索:向量搜索 + 关键词搜索"""
        # 向量搜索(GPU加速)
        vector_results = await self.discover_tools(query, limit=limit * 2, category=category)

        # 关键词搜索
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

        results = sorted(combined_scores.values(), key=lambda x: x["score"], reverse=True)

        logger.info(f"✅ 混合搜索发现 {len(results)} 个相关工具")

        return results[:limit]

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        stats = {
            "total_tools": len(self.tool_metadata),
            "indexed_tools": len(self.tool_ids),
            "model_name": self.embedder.model_name,
            "model_available": self.embedder.is_available(),
            "vector_dimension": (
                self.tool_embeddings.shape[1] if self.tool_embeddings is not None else 0
            ),
            "cache_file": str(self.cache_file) if self.cache_file.exists() else "Not cached",
            "gpu_enabled": self.use_gpu,
            "device_type": self.embedder.device_info.get("device_type", "cpu"),
            "device_name": self.embedder.device_info.get("device_name", "CPU"),
        }

        # 添加性能统计
        perf_stats = self.embedder.get_performance_stats()
        if perf_stats:
            stats["performance"] = perf_stats

        return stats


# ================================
# 便捷函数
# ================================


async def discover_tools_gpu(
    tool_metadata: dict[str, Any],    query: str,
    limit: int = 10,
    use_gpu: bool = True,
    use_hybrid: bool = True,
    **kwargs,
) -> list[dict[str, Any]]:
    """
    GPU加速向量工具发现的便捷函数

    Args:
        tool_metadata: 工具元数据字典
        query: 查询描述
        limit: 返回数量限制
        use_gpu: 是否使用GPU加速
        use_hybrid: 是否使用混合搜索
        **kwargs: 其他参数

    Returns:
        匹配的工具列表
    """
    discovery = GPUVectorToolDiscovery(tool_metadata, use_gpu=use_gpu)

    if use_hybrid:
        return await discovery.hybrid_discover(query, limit, **kwargs)
    else:
        return await discovery.discover_tools(query, limit, **kwargs)
