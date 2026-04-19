#!/usr/bin/env python3
"""
Athena生产环境模型服务
统一的模型加载、批处理、缓存管理

作者: Athena AI
创建时间: 2025-12-29
版本: v1.0.0
"""

from __future__ import annotations
import asyncio
import logging

# 导入核心工具
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.models.athena_model_loader import get_device, load_model
from core.performance.batch_processor import BatchProcessor
from core.performance.model_cache import get_cache_manager

logger = logging.getLogger(__name__)


@dataclass
class ModelServiceConfig:
    """模型服务配置"""

    # 环境配置
    environment: str = "production"

    # 设备配置
    device_auto_detect: bool = True
    device_priority: list[str] | None = None

    # 批处理配置
    batch_processing_enabled: bool = True
    batch_size: int = 32
    batch_timeout_ms: int = 50

    # 缓存配置
    cache_enabled: bool = True
    l1_cache_size_mb: int = 500
    l2_redis_enabled: bool = True
    l3_disk_enabled: bool = True

    # 监控配置
    monitoring_enabled: bool = True
    sample_interval_sec: int = 5

    # 分层加载配置
    tiered_loading_enabled: bool = True
    hot_memory_limit_mb: int = 2048

    def __post_init__(self):
        if self.device_priority is None:
            self.device_priority = ["mps", "cuda", "cpu"]


class ModelService:
    """
    Athena生产环境模型服务

    统一管理:
    - 模型加载 (自动检测MPS/CUDA/CPU)
    - 批处理 (自适应批大小)
    - 三级缓存 (L1/L2/L3)
    - 监控告警
    - 健康检查
    """

    def __init__(self, config_path: str | None = None):
        """
        初始化模型服务

        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.device = get_device()

        # 核心组件
        self.models: dict[str, Any] = {}
        self.batch_processors: dict[str, BatchProcessor] = {}
        self.cache_manager = None

        # 统计信息
        self.stats = {
            "total_requests": 0,
            "total_embeddings": 0,
            "cache_hits": 0,
            "batch_processes": 0
        }

        logger.info("🚀 Athena模型服务初始化完成")
        logger.info(f"   环境: {self.config.environment}")
        logger.info(f"   设备: {self.device}")

    def _load_config(self, config_path: str | None) -> ModelServiceConfig:
        """加载配置"""
        if config_path is None:
            config_path = "/Users/xujian/Athena工作平台/config/environments/production/model_config.yaml"

        config_file = Path(config_path)
        if config_file.exists():
            with open(config_file, encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            logger.info(f"✅ 配置加载成功: {config_path}")
            return ModelServiceConfig(**config_data)
        else:
            logger.warning(f"⚠️ 配置文件不存在，使用默认配置: {config_path}")
            return ModelServiceConfig()

    async def initialize(self):
        """异步初始化"""
        logger.info("="*60)
        logger.info("🔄 初始化Athena模型服务")
        logger.info("="*60)

        # 1. 初始化缓存
        if self.config.cache_enabled:
            await self._initialize_cache()

        # 2. 加载HOT层模型
        if self.config.tiered_loading_enabled:
            await self._load_hot_models()

        # 3. 初始化批处理器
        if self.config.batch_processing_enabled:
            await self._initialize_batch_processors()

        logger.info("="*60)
        logger.info("✅ 模型服务初始化完成")
        logger.info("="*60)

    async def _initialize_cache(self):
        """初始化缓存"""
        logger.info("📦 初始化三级缓存...")

        self.cache_manager = get_cache_manager(
            l1_max_size_mb=self.config.l1_cache_size_mb,
            enable_l2=self.config.l2_redis_enabled,
            enable_l3=self.config.l3_disk_enabled
        )

        logger.info("✅ 缓存初始化完成")

    async def _load_hot_models(self):
        """加载HOT层模型"""
        logger.info("🔥 加载HOT层模型...")

        # 定义HOT层模型
        hot_models = ["BAAI/bge-m3", "lightweight_intent_classifier"]

        for model_name in hot_models:
            try:
                logger.info(f"  加载 {model_name}...")
                model = load_model(model_name)
                self.models[model_name] = model
                logger.info(f"  ✅ {model_name} 加载成功")
            except Exception as e:
                logger.error(f"  ❌ {model_name} 加载失败: {e}")

        logger.info("✅ HOT层模型加载完成")

    async def _initialize_batch_processors(self):
        """初始化批处理器"""
        logger.info("🔄 初始化批处理器...")

        # 为常用模型创建批处理器
        for model_name in ["BAAI/bge-m3"]:
            if model_name in self.models:
                try:
                    processor = BatchProcessor(
                        model=self.models[model_name],
                        batch_size=self.config.batch_size,
                        timeout_ms=self.config.batch_timeout_ms,
                        device=self.device
                    )
                    await processor.start()
                    self.batch_processors[model_name] = processor
                    logger.info(f"  ✅ {model_name} 批处理器创建成功")
                except Exception as e:
                    logger.error(f"  ❌ {model_name} 批处理器创建失败: {e}")

        logger.info("✅ 批处理器初始化完成")

    async def encode(
        self,
        texts: list[str],
        model_name: str = "BAAI/bge-m3",
        use_cache: bool = True,
        use_batch: bool = True,
        priority: int = 2
    ) -> list[Any]:
        """
        生成文本嵌入

        Args:
            texts: 文本列表
            model_name: 模型名称
            use_cache: 是否使用缓存
            use_batch: 是否使用批处理
            priority: 优先级 (1=high, 2=medium, 3=low)

        Returns:
            嵌入向量列表
        """
        self.stats["total_requests"] += 1

        # 获取或加载模型
        if model_name not in self.models:
            logger.info(f"🔄 加载模型: {model_name}")
            self.models[model_name] = load_model(model_name)

        model = self.models[model_name]

        # 使用批处理
        if use_batch and model_name in self.batch_processors:
            self.stats["batch_processes"] += 1

            processor = self.batch_processors[model_name]
            results = []

            # 批量处理
            for text in texts:
                result = await processor.process(text, priority=priority)
                results.append(result)

            self.stats["total_embeddings"] += len(texts)
            return results

        # 不使用批处理
        embeddings = []

        for text in texts:
            # 尝试从缓存获取
            if use_cache and self.cache_manager:
                cached = self.cache_manager.get(model_name, text)
                if cached is not None:
                    self.stats["cache_hits"] += 1
                    embeddings.append(cached)
                    continue

            # 生成嵌入
            embedding = model.encode([text], show_progress_bar=False)[0]

            # 写入缓存
            if use_cache and self.cache_manager:
                self.cache_manager.set(model_name, text, embedding)

            embeddings.append(embedding)

        self.stats["total_embeddings"] += len(texts)
        return embeddings

    async def get_stats(self) -> dict:
        """获取统计信息"""
        stats = self.stats.copy()

        # 添加批处理器统计
        for name, processor in self.batch_processors.items():
            stats[f"batch_processor_{name}"] = processor.get_stats()

        # 添加缓存统计
        if self.cache_manager:
            stats["cache"] = self.cache_manager.get_stats()

        # 添加模型列表
        stats["loaded_models"] = list(self.models.keys())

        return stats

    async def health_check(self) -> dict[str, Any]:
        """健康检查"""
        health = {
            "status": "healthy",
            "device": self.device,
            "models": {},
            "cache": {},
            "batch_processors": {}
        }

        # 检查模型
        for name, model in self.models.items():
            try:
                # 快速测试
                test_emb = model.encode(["测试"], show_progress_bar=False)
                health["models"][name] = {
                    "status": "ok",
                    "dimension": len(test_emb[0])
                }
            except Exception as e:
                health["models"][name] = {
                    "status": "error",
                    "error": str(e)
                }
                health["status"] = "degraded"

        # 检查缓存
        if self.cache_manager:
            try:
                cache_stats = self.cache_manager.get_stats()
                health["cache"] = {
                    "status": "ok",
                    "hit_rate": cache_stats.get("overall_hit_rate", 0)
                }
            except Exception as e:
                health["cache"] = {
                    "status": "error",
                    "error": str(e)
                }
                health["status"] = "degraded"

        # 检查批处理器
        for name, processor in self.batch_processors.items():
            stats = processor.get_stats()
            health["batch_processors"][name] = {
                "status": "ok" if stats["running"] else "stopped",
                "running": stats["running"]
            }

        return health

    async def shutdown(self):
        """关闭服务"""
        logger.info("⏹️ 关闭模型服务...")

        # 停止批处理器
        for processor in self.batch_processors.values():
            await processor.stop()

        # 清空缓存
        if self.cache_manager:
            self.cache_manager.clear()

        # 卸载模型
        self.models.clear()

        logger.info("✅ 模型服务已关闭")


# 全局单例
_model_service: ModelService | None = None


async def get_model_service() -> ModelService:
    """获取模型服务单例"""
    global _model_service

    if _model_service is None:
        _model_service = ModelService()
        await _model_service.initialize()

    return _model_service


# 便捷函数
async def encode_texts(
    texts: list[str],
    model_name: str = "BAAI/bge-m3"
) -> list[Any]:
    """
    便捷的文本编码函数

    Args:
        texts: 文本列表
        model_name: 模型名称

    Returns:
        嵌入向量列表
    """
    service = await get_model_service()
    return await service.encode(texts, model_name)


if __name__ == "__main__":
    import asyncio
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    async def test():
        """测试模型服务"""
        print("="*60)
        print("🧪 测试Athena模型服务")
        print("="*60)

        # 创建服务
        service = ModelService()
        await service.initialize()

        # 测试编码
        print("\n🔄 测试文本编码...")
        texts = ["测试文本1", "测试文本2", "测试文本3"]
        embeddings = await service.encode(texts)

        print("✅ 编码成功!")
        print(f"   文本数: {len(texts)}")
        print(f"   向量维度: {len(embeddings[0])}")

        # 获取统计
        stats = await service.get_stats()
        print("\n📊 统计信息:")
        print(f"   总请求数: {stats['total_requests']}")
        print(f"   总嵌入数: {stats['total_embeddings']}")
        print(f"   缓存命中: {stats['cache_hits']}")

        # 健康检查
        health = await service.health_check()
        print(f"\n💚 健康状态: {health['status']}")

        # 关闭服务
        await service.shutdown()

        print("\n✅ 测试完成!")

    asyncio.run(test())
