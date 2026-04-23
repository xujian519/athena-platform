#!/usr/bin/env python3

"""
Athena平台统一向量管理系统
Unified Vector Management System for Athena Platform

创建时间: 2025-12-29
功能: 统一管理向量存储、检索、语义路由和Qdrant适配
"""

import asyncio
import json
import logging
import re
import sys
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import numpy as np

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

try:
    from qdrant_client import QdrantClient, models

    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

# 导入本地BGE嵌入服务
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

try:
    from core.ai.embedding.bge_embedding_service import BGEEmbeddingService, 

    BGE_AVAILABLE = True
except ImportError:
    BGE_AVAILABLE = False

# 配置日志
logger = logging.getLogger(__name__)


class VectorDomain(str, Enum):
    """向量领域"""

    LEGAL = "legal"
    PATENT = "patent"
    MIXED = "mixed"
    TECHNICAL = "technical"
    MEMORY = "memory"


class UnifiedVectorManager:
    """
    统一向量管理器

    整合了:
    - IntelligentVectorManager (智能向量管理)
    - SemanticRouter (语义路由)
    - QdrantVectorAdapter (Qdrant适配)
    """

    def __init__(self, config: Optional[dict] = None):
        """
        初始化统一向量管理器

        Args:
            config: 配置字典
        """
        self.config = config or self._load_default_config()

        # Qdrant客户端
        self.qdrant_host = self.config.get("qdrant_host", "localhost")
        self.qdrant_port = self.config.get("qdrant_port", 6333)
        self.qdrant_client: Optional[QdrantClient] = None
        self._initialized = False

        # 嵌入模型配置 - 支持本地MPS优化模型
        self.embedding_model_name = self.config.get("embedding_model", "bge-m3")
        self.embedding_device = self._select_device()

        # BGE嵌入服务(优先使用本地MPS模型)
        self.bge_service: Optional[BGEEmbeddingService] = None

        # 向量集合配置
        self.collections_config = self._load_collections_config()

        # 语义路由配置
        self.routing_rules = self._load_routing_rules()
        self.route_cache: dict[str, tuple[VectorDomain, float]] = {}
        self.cache_ttl = 3600

        # 性能统计
        self.performance_stats = {
            "total_queries": 0,
            "cache_hits": 0,
            "average_response_time": 0,
            "last_optimization": None,
        }

        # 初始化
        self._init_components()

    def _select_device(self) -> str:
        """
        选择最优计算设备(优先MPS,其次CUDA,最后CPU)

        Returns:
            设备字符串 ("mps", "cuda", 或 "cpu")
        """
        try:
            import torch

            if torch.backends.mps.is_available():
                logger.info("🍎 检测到Apple MPS支持,将使用GPU加速")
                return "mps"
            elif torch.cuda.is_available():
                logger.info("🎮 检测到CUDA支持,将使用NVIDIA GPU")
                return "cuda"
            else:
                logger.info("💻 将使用CPU进行计算")
                return "cpu"
        except ImportError:
            logger.warning("⚠️ PyTorch未安装,将使用CPU")
            return "cpu"

    def _load_default_config(self) -> dict:
        """加载默认配置"""
        return {
            "qdrant_host": "localhost",
            "qdrant_port": 6333,
            "embedding_model": "bge-m3",  # 本地模型名称
            "embedding_device": "auto",  # auto检测设备
            "cache_enabled": True,
            "cache_size_limit": 1000,
        }

    def _load_collections_config(self) -> dict:
        """加载向量集合配置"""
        config_path = Path(__file__).parent / "config" / "vector_collections_config.json"

        default_config = {
            "legal_collections": {
                "legal_main": {
                    "size": 1536,
                    "description": "法律主向量库",
                    "priority": "high",
                    "update_strategy": "incremental",
                },
                "legal_contracts": {
                    "size": 1024,
                    "description": "法律合同条款向量库",
                    "priority": "high",
                    "update_strategy": "batch",
                },
                "legal_clauses_1024": {
                    "size": 1024,
                    "description": "法律条款向量库",
                    "priority": "high",
                    "update_strategy": "real_time",
                },
                "legal_concepts_1024": {
                    "size": 1024,
                    "description": "法律概念",
                    "priority": "medium",
                    "update_strategy": "batch",
                },
                "case_data_1024": {
                    "size": 1024,
                    "description": "案例数据",
                    "priority": "medium",
                    "update_strategy": "batch",
                },
            },
            "patent_collections": {
                "patent_rules_1024": {
                    "size": 1024,
                    "description": "专利规则向量库",
                    "priority": "high",
                    "update_strategy": "real_time",
                },
                "patents_invalid_1024": {
                    "size": 1024,
                    "description": "专利无效向量库",
                    "priority": "high",
                    "update_strategy": "batch",
                },
                "patents_data_1024": {
                    "size": 1024,
                    "description": "专利实体数据",
                    "priority": "medium",
                    "update_strategy": "batch",
                },
                "patent_applications": {
                    "size": 1536,
                    "description": "专利申请向量库",
                    "priority": "medium",
                    "update_strategy": "batch",
                },
            },
            "technical_collections": {
                "technical_terms_1024": {
                    "size": 1024,
                    "description": "技术术语向量库",
                    "priority": "high",
                    "update_strategy": "real_time",
                }
            },
            "memory_collections": {
                "athena_memory": {
                    "size": 768,
                    "description": "Athena记忆向量库",
                    "priority": "medium",
                    "update_strategy": "real_time",
                },
                "xiaonuo_memory": {
                    "size": 768,
                    "description": "小诺记忆向量库",
                    "priority": "medium",
                    "update_strategy": "real_time",
                },
            },
        }

        if config_path.exists():
            try:
                with open(config_path, encoding="utf-8") as f:
                    loaded_config = json.load(f)
                    # 合并配置
                    for category in default_config:
                        if category in loaded_config:
                            default_config[category].update(loaded_config[category])
            except Exception as e:
                logger.warning(f"加载向量配置失败: {e},使用默认配置")

        return default_config

    def _load_routing_rules(self) -> dict:
        """加载语义路由规则"""
        return {
            "legal_domain": {
                "keywords": [
                    "法律",
                    "法条",
                    "法规",
                    "诉讼",
                    "法院",
                    "法官",
                    "律师",
                    "合同",
                    "侵权",
                    "赔偿",
                    "刑事责任",
                    "民事诉讼",
                    "司法",
                    "判决",
                    "裁定",
                    "执行",
                    "仲裁",
                    "调解",
                    "法律援助",
                    "民法典",
                    "刑法",
                    "民事诉讼法",
                    "行政诉讼法",
                ],
                "patterns": [
                    r".*法.*",
                    r".*诉讼.*",
                    r".*合同.*",
                    r".*侵权.*",
                    r".*赔偿.*",
                    r".*犯罪.*",
                    r".*判决.*",
                ],
                "collections": [
                    "legal_main",
                    "legal_contracts",
                    "legal_clauses_1024",
                    "legal_concepts_1024",
                    "case_data_1024",
                ],
                "weight": 0.8,
            },
            "patent_domain": {
                "keywords": [
                    "专利",
                    "发明",
                    "实用新型",
                    "外观设计",
                    "创造性",
                    "新颖性",
                    "专利申请",
                    "专利权",
                    "专利侵权",
                    "专利检索",
                    "专利分析",
                    "知识产权",
                    "专利法",
                    "专利审查",
                    "专利授权",
                    "专利无效",
                    "技术方案",
                    "技术特征",
                    "背景技术",
                    "现有技术",
                ],
                "patterns": [
                    r".*专利.*",
                    r".*发明.*",
                    r".*实用新型.*",
                    r".*外观设计.*",
                    r".*申请.*",
                    r".*授权.*",
                    r".*侵权.*",
                ],
                "collections": [
                    "patent_rules_1024",
                    "patents_invalid_1024",
                    "patents_data_1024",
                    "patent_applications",
                ],
                "weight": 0.8,
            },
            "technical_domain": {
                "keywords": [
                    "技术",
                    "工艺",
                    "方法",
                    "系统",
                    "装置",
                    "设备",
                    "算法",
                    "模型",
                    "架构",
                    "协议",
                    "标准",
                    "规范",
                ],
                "patterns": [r".*技术.*", r".*工艺.*", r".*方法.*", r".*系统.*"],
                "collections": ["technical_terms_1024"],
                "weight": 0.6,
            },
            "mixed_domain": {
                "keywords": [
                    "专利诉讼",
                    "专利侵权",
                    "知识产权保护",
                    "商业秘密",
                    "不正当竞争",
                    "技术转让",
                    "许可合同",
                    "专利许可",
                    "知识产权纠纷",
                    "专利纠纷",
                    "商标侵权",
                    "版权保护",
                ],
                "patterns": [
                    r".*专利.*诉讼.*",
                    r".*知识产权.*",
                    r".*专利.*侵权.*",
                    r".*技术.*合同.*",
                ],
                "collections": [
                    "legal_main",
                    "legal_contracts",
                    "patent_rules_1024",
                    "patents_data_1024",
                    "case_data_1024",
                ],
                "weight": 0.9,
            },
        }

    def _init_components(self) -> Any:
        """初始化组件"""
        try:
            # 初始化Qdrant客户端
            self.qdrant_client = QdrantClient(host=self.qdrant_host, port=self.qdrant_port)

            # 测试连接
            collections = self.qdrant_client.get_collections()
            logger.info(f"✅ Qdrant连接成功,现有集合数: {len(collections.collections)}")

            # 初始化嵌入模型
            self._init_embedding_model()

            self._initialized = True
            logger.info("✅ 统一向量管理器初始化完成")

        except Exception as e:
            logger.error(f"❌ 统一向量管理器初始化失败: {e}")
            self._initialized = False

    def _init_embedding_model(self) -> Any:
        """
        初始化嵌入模型 - 使用本地MPS优化的BGE模型

        支持的本地模型:
        - 'bge-m3' (1024维,高精度)
        - 'bge-m3' (1024维(BGE-M3),平衡性能)
        - 'bge-m3' (512维,轻量快速)
        """
        if not BGE_AVAILABLE:
            logger.warning("⚠️ BGE嵌入服务不可用,请检查core/embedding/bge_embedding_service.py")
            return

        try:
            logger.info(f"🔧 初始化本地BGE嵌入模型: {self.embedding_model_name}")
            logger.info(f"🖥️ 计算设备: {self.embedding_device}")

            # 使用本地BGE服务(优先从本地converted目录加载)
            self.bge_service = BGEEmbeddingService(
                model_name=self.embedding_model_name,
                device=self.embedding_device,
                batch_size=32,
                cache_size=1000,
            )

            logger.info("✅ 本地BGE模型加载完成")
            logger.info(f"   模型: {self.embedding_model_name}")
            logger.info(f"   向量维度: {self.bge_service.dimension}")
            logger.info(f"   设备: {self.embedding_device}")

        except Exception as e:
            logger.error(f"❌ 本地BGE模型加载失败: {e}")
            logger.warning("⚠️ 将尝试使用远程模型作为备选")
            self.bge_service = None

    async def initialize(self) -> bool:
        """
        异步初始化

        Returns:
            初始化是否成功
        """
        if not self._initialized:
            self._init_components()

        # 确保必要的集合存在
        await self._ensure_collections()

        return self._initialized

    async def _ensure_collections(self):
        """确保必要的向量集合存在"""
        if not self.qdrant_client:
            return

        try:
            # 收集所有需要的集合
            required_collections = set()
            for category in self.collections_config.values():
                required_collections.update(category.keys())

            # 获取现有集合
            existing_collections = [
                col.name for col in self.qdrant_client.get_collections().collections
            ]

            # 创建缺失的集合
            for collection_name in required_collections:
                if collection_name not in existing_collections:
                    # 获取向量维度
                    vector_size = 1024  # 默认维度
                    for category in self.collections_config.values():
                        if collection_name in category:
                            vector_size = category[collection_name].get("size", 1024)
                            break

                    # 创建集合
                    self.qdrant_client.create_collection(
                        collection_name=collection_name,
                        vectors_config=models.VectorParams(
                            size=vector_size, distance=models.Distance.COSINE
                        ),
                    )
                    logger.info(f"✅ 创建向量集合: {collection_name}")
                else:
                    logger.debug(f"ℹ️ 集合已存在: {collection_name}")

        except Exception as e:
            logger.warning(f"⚠️ 集合创建警告: {e}")

    def route_query(self, query: str) -> tuple[VectorDomain, list[str]]:
        """
        路由查询到适当的向量集合

        Args:
            query: 查询文本

        Returns:
            (领域, 推荐集合列表)
        """
        # 检查缓存
        cache_key = f"route:{query}"
        if cache_key in self.route_cache:
            self.performance_stats["cache_hits"] += 1
            return self.route_cache[cache_key]

        # 分析查询
        domain_scores = {}

        for domain_name, rules in self.routing_rules.items():
            score = 0.0

            # 关键词匹配
            query_lower = query.lower()
            for keyword in rules["keywords"]:
                if keyword in query_lower:
                    score += rules["weight"]

            # 模式匹配
            for pattern in rules["patterns"]:
                if re.search(pattern, query):
                    score += rules["weight"] * 0.5

            if score > 0:
                domain = VectorDomain(domain_name.split("_")[0])
                domain_scores[domain] = score

        # 选择最高分领域
        if domain_scores:
            best_domain = max(domain_scores, key=domain_scores.get)
            collections = self.routing_rules[f"{best_domain.value}_domain"]["collections"]
        else:
            # 默认使用混合域
            best_domain = VectorDomain.MIXED
            collections = self.routing_rules["mixed_domain"]["collections"]

        # 缓存结果
        result = (best_domain, collections)
        self.route_cache[cache_key] = result

        return result

    def encode_text(self, text: str) -> np.Optional[ndarray]:
        """
        编码文本为向量 - 使用本地MPS优化的BGE模型

        Args:
            text: 输入文本

        Returns:
            向量数组,失败返回None
        """
        if not self.bge_service:
            logger.warning("BGE嵌入服务未初始化")
            return None

        try:
            # 使用BGE服务进行编码
            vector = self.bge_service.encode(text, normalize=True)
            return vector
        except Exception as e:
            logger.error(f"文本编码失败: {e}")
            return None

    async def search(
        self, query: str, domain: str = "mixed", limit: int = 10, threshold: float = 0.3
    ) -> dict[str, Any]:
        """
        统一搜索接口

        Args:
            query: 查询文本
            domain: 领域 (legal, patent, mixed)
            limit: 返回数量
            threshold: 相似度阈值

        Returns:
            搜索结果
        """
        start_time = datetime.now()

        # 路由查询
        vector_domain, collections = self.route_query(query)

        # 编码查询
        query_vector = self.encode_text(query)
        if query_vector is None:
            return {"success": False, "error": "encoding_failed", "message": "查询向量编码失败"}

        # 搜索结果聚合
        all_results = []
        collections_searched = []

        if self.qdrant_client:
            for collection_name in collections:
                try:
                    results = self.qdrant_client.search(
                        collection_name=collection_name,
                        query_vector=query_vector.tolist(),
                        limit=limit,
                        score_threshold=threshold,
                        with_payload=True,
                    )

                    collections_searched.append(collection_name)

                    for point in results:
                        all_results.append(
                            {
                                "id": point.id,
                                "score": point.score,
                                "payload": point.payload,
                                "collection": collection_name,
                            }
                        )

                except Exception as e:
                    logger.warning(f"搜索集合 {collection_name} 失败: {e}")

        # 按分数排序
        all_results.sort(key=lambda x: x["score"], reverse=True)
        all_results = all_results[:limit]

        # 更新统计
        self.performance_stats["total_queries"] += 1
        response_time = (datetime.now() - start_time).total_seconds()
        self.performance_stats["average_response_time"] = (
            self.performance_stats["average_response_time"]
            * (self.performance_stats["total_queries"] - 1)
            + response_time
        ) / self.performance_stats["total_queries"]

        return {
            "success": True,
            "query": query,
            "domain": vector_domain.value,
            "results": all_results,
            "total": len(all_results),
            "collections_searched": collections_searched,
            "response_time": response_time,
        }

    async def hybrid_search(
        self, query: str, domain: str = "mixed", limit: int = 10
    ) -> dict[str, Any]:
        """
        混合搜索(向量+关键词)

        Args:
            query: 查询文本
            domain: 领域
            limit: 返回数量

        Returns:
            搜索结果
        """
        # 向量搜索
        vector_results = await self.search(query, domain, limit)

        # TODO: 添加关键词搜索

        return vector_results

    async def add_vectors(self, collection_name: str, vectors: list[dict[str, Any]) -> bool]:
        """
        添加向量

        Args:
            collection_name: 集合名称
            vectors: 向量列表 [{"id": ..., "vector": ..., "payload": ...}]

        Returns:
            是否成功
        """
        if not self.qdrant_client:
            logger.error("Qdrant客户端未初始化")
            return False

        try:
            points = [
                models.PointStruct(
                    id=item["id"], vector=item["vector"], payload=item.get("payload", {})
                )
                for item in vectors
            ]

            self.qdrant_client.upsert(collection_name=collection_name, points=points)

            logger.info(f"✅ 添加 {len(points)} 个向量到 {collection_name}")
            return True

        except Exception as e:
            logger.error(f"添加向量失败: {e}")
            return False

    def get_stats(self) -> dict[str, Any]:
        """获取性能统计和模型信息"""
        stats = {
            "performance": self.performance_stats,
            "cache_size": len(self.route_cache),
            "collections": self.collections_config,
            "routing_rules": list(self.routing_rules.keys()),
            "initialized": self._initialized,
            "model": {
                "name": self.embedding_model_name,
                "device": self.embedding_device,
                "available": self.bge_service is not None,
            },
        }

        # 添加BGE服务统计
        if self.bge_service:
            stats["embedding_cache"] = self.bge_service.get_cache_stats()
            stats["model"]["dimension"] = self.bge_service.dimension

        return stats

    async def close(self):
        """关闭连接"""
        if self.qdrant_client:
            self.qdrant_client = None
        self._initialized = False
        logger.info("✅ 统一向量管理器已关闭")


# 全局单例
_unified_vector_manager: Optional[UnifiedVectorManager] = None


def get_vector_manager() -> UnifiedVectorManager:
    """
    获取统一向量管理器单例

    Returns:
        统一向量管理器实例
    """
    global _unified_vector_manager

    if _unified_vector_manager is None:
        _unified_vector_manager = UnifiedVectorManager()
        # 异步初始化需要在事件循环中调用
        # await _unified_vector_manager.initialize()

    return _unified_vector_manager


# 向后兼容的别名
IntelligentVectorManager = UnifiedVectorManager
SemanticRouter = UnifiedVectorManager
QdrantVectorAdapter = UnifiedVectorManager


if __name__ == "__main__":
    import asyncio

    async def test():
        # 测试统一向量管理器
        manager = UnifiedVectorManager()
        success = await manager.initialize()

        if success:
            print("✅ 统一向量管理器初始化成功")

            # 测试路由
            domain, collections = manager.route_query("专利侵权如何判定?")
            print(f"路由结果: {domain}, 集合: {collections}")

            # 测试编码
            vector = manager.encode_text("测试文本")
            print(f"向量维度: {vector.shape if vector is not None else 'None'}")

            # 获取统计
            stats = manager.get_stats()
            print(f"统计信息: {stats}")
        else:
            print("❌ 初始化失败")

    asyncio.run(test())

