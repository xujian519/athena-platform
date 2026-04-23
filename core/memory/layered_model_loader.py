#!/usr/bin/env python3
from __future__ import annotations
"""
分层模型加载器 - 方案A(保守型)
实现模型的分层加载和动态管理,优先保证办公流畅度

作者: 小诺·双鱼公主 🌊✨
创建时间: 2025-12-27
版本: v1.0.0
"""

import logging
import threading
import time
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ModelTier(Enum):
    """模型层级"""

    HOT = "hot"  # 2GB - 常用模型,常驻GPU
    WARM = "warm"  # 4GB - 频繁使用,快速加载
    COLD = "cold"  # 8GB - 按需加载
    ARCHIVE = "archive"  # 稀少使用,从磁盘加载


class LayeredModelLoader:
    """分层模型加载器"""

    # 预定义的模型层级
    MODEL_TIERS = {
        # HOT层 - 常用模型(2GB)
        "hot": [
            "BAAI/bge-m3",  # 中文语义嵌入
            "paraphrase-multilingual-MiniLM-L12-v2",  # 多语言重排序
        ],
        # WARM层 - 频繁使用(4GB)
        "warm": [
            "BAAI/bge-m3",  # 大型中文模型(统一使用,已替代法律模型)
            # chinese-legal-electra (已删除,使用BGE-M3替代)
        ],
        # COLD层 - 按需加载(8GB)
        "cold": [
            "multimodal-generator",  # 多模态生成
            "t5-small",  # 文本生成
            "sentence-transformers-all-MiniLM-L6-v2",  # 全向嵌入
        ],
        # ARCHIVE层 - 稀少使用(不占用内存)
        "archive": [
            "xlm-roberta-large",  # 大型翻译模型
            "gpt2",  # 文本生成
        ],
    }

    def __init__(self, models_path: Optional[str] = None):
        """
        初始化分层模型加载器

        Args:
            models_path: 模型存储路径,默认 /Users/xujian/Athena工作平台/models/converted/
        """
        self.models_path = models_path or "/Users/xujian/Athena工作平台/models/converted/"
        self.loaded_models: dict[str, Any] = {}
        self.model_locks = threading.Lock()

        # 内存限制(MB)
        self.tier_limits = {
            ModelTier.HOT: 2048,  # 2GB
            ModelTier.WARM: 4096,  # 4GB
            ModelTier.COLD: 8192,  # 8GB
            ModelTier.ARCHIVE: 0,  # 不占用内存
        }

        # 当前使用情况
        self.tier_usage = {
            ModelTier.HOT: 0.0,
            ModelTier.WARM: 0.0,
            ModelTier.COLD: 0.0,
            ModelTier.ARCHIVE: 0.0,
        }

        logger.info("🔄 分层模型加载器初始化完成")
        logger.info(f"📁 模型路径: {self.models_path}")
        logger.info("💾 HOT层限制: 2GB")
        logger.info("💾 WARM层限制: 4GB")
        logger.info("💾 COLD层限制: 8GB")

    def get_model_tier(self, model_name: str) -> ModelTier:
        """获取模型层级"""
        for tier, models in self.MODEL_TIERS.items():
            if model_name in models:
                return ModelTier(tier)
        return ModelTier.COLD  # 默认为COLD层

    def can_load_model(self, model_name: str, model_size_mb: float) -> bool:
        """检查是否可以加载模型"""
        tier = self.get_model_tier(model_name)
        tier_limit = self.tier_limits[tier]
        current_usage = self.tier_usage[tier]

        # 检查该层级是否有足够空间
        if current_usage + model_size_mb <= tier_limit:
            return True

        # 如果当前层级满了,尝试清理
        logger.info(f"🔄 {tier.value}层已满,尝试清理...")
        self._cleanup_tier(tier, model_size_mb)

        return (self.tier_usage[tier] + model_size_mb) <= tier_limit

    def _cleanup_tier(self, tier: ModelTier, required_mb: float) -> Any:
        """清理层级中的模型"""
        if tier == ModelTier.HOT:
            # HOT层不自动清理
            logger.warning("⚠️ HOT层不自动清理,需要手动释放")
            return

        # 找出该层级的所有模型
        models_to_remove = []
        for name, _model in self.loaded_models.items():
            if self.get_model_tier(name) == tier:
                models_to_remove.append(name)

        # 按最后使用时间排序
        models_to_remove.sort(key=lambda x: getattr(self.loaded_models[x], "_last_used", 0))

        # 释放模型直到有足够空间
        freed_mb = 0.0
        for name in models_to_remove:
            if freed_mb >= required_mb:
                break

            model_size = getattr(self.loaded_models[name], "_size_mb", 0)
            self.unload_model(name)
            freed_mb += model_size
            logger.info(f"🗑️ 清理模型: {name} ({model_size}MB)")

    def load_model(self, model_name: str) -> Any | None:
        """
        加载模型(模拟)

        Args:
            model_name: 模型名称

        Returns:
            模型对象(模拟)
        """
        tier = self.get_model_tier(model_name)

        # 检查是否已加载
        if model_name in self.loaded_models:
            logger.info(f"✅ 模型已加载: {model_name}")
            return self.loaded_models[model_name]

        # 检查是否可以加载
        model_size_mb = self._estimate_model_size(model_name)
        if not self.can_load_model(model_name, model_size_mb):
            logger.error(f"❌ 无法加载模型: {model_name} (内存不足)")
            return None

        # 模拟加载模型
        logger.info(f"🔄 加载模型: {model_name} ({tier.value}层, {model_size_mb}MB)")

        self.loaded_models[model_name] = {
            "_tier": tier,
            "_size_mb": model_size_mb,
            "_last_used": time.time(),
            "_load_count": 1,
        }

        # 更新使用统计
        self.tier_usage[tier] += model_size_mb

        return self.loaded_models[model_name]

    def unload_model(self, model_name: str) -> Any:
        """卸载模型"""
        if model_name not in self.loaded_models:
            logger.warning(f"⚠️ 模型未加载: {model_name}")
            return

        model = self.loaded_models[model_name]
        tier = model["_tier"]
        size_mb = model["_size_mb"]

        # 释放内存
        del self.loaded_models[model_name]
        self.tier_usage[tier] -= size_mb

        logger.info(f"🗑️ 模型已卸载: {model_name} ({size_mb}MB)")

    def _estimate_model_size(self, model_name: str) -> float:
        """估算模型大小(MB)"""
        # 预定义模型大小
        model_sizes = {
            # HOT层模型
            "BAAI/bge-m3": 400,
            "paraphrase-multilingual-MiniLM-L12-v2": 400,
            # WARM层模型 (使用相同的键但覆盖值表示不同层的大小)
            "BAAI/bge-m3-warm": 1200,  # WARM层使用更大的模型
            # chinese-legal-electra: 400,  # 已删除,使用BGE-M3替代
            # COLD层模型
            "multimodal-generator": 2000,
            "t5-small": 200,
            "sentence-transformers-all-MiniLM-L6-v2": 400,
        }

        # 如果请求的是bge-m3且没有指定层,返回默认大小
        if model_name == "BAAI/bge-m3":
            return 400
        return model_sizes.get(model_name, 500)  # 默认500MB

    def get_status(self) -> dict[str, Any]:
        """获取加载器状态"""
        return {
            "loaded_models": {
                name: {
                    "tier": model["_tier"].value,
                    "size_mb": model["_size_mb"],
                    "last_used": model["_last_used"],
                    "load_count": model["_load_count"],
                }
                for name, model in self.loaded_models.items()
            },
            "tier_usage": {
                tier.value: {
                    "used_mb": self.tier_usage[tier],
                    "limit_mb": self.tier_limits[tier],
                    "usage_percent": (
                        (self.tier_usage[tier] / self.tier_limits[tier] * 100)
                        if self.tier_limits[tier] > 0
                        else 0.0
                    ),
                }
                for tier in ModelTier
            },
            "total_used_mb": sum(self.tier_usage.values()),
            "total_limit_mb": sum(self.tier_limits.values()),
        }


# 全局单例
_loader: LayeredModelLoader | None = None
_loader_lock = threading.Lock()


def get_model_loader() -> LayeredModelLoader:
    """获取全局模型加载器实例"""
    global _loader
    if _loader is None:
        with _loader_lock:
            if _loader is None:
                _loader = LayeredModelLoader()
    return _loader
