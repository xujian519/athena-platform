#!/usr/bin/env python3
"""
Athena平台模型注册和管理系统
Model Registry and Management System

管理本地大语言模型的注册、加载、卸载和监控
作者: 小诺·双鱼公主 v4.0
创建时间: 2025-01-09
"""

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from core.logging_config import setup_logging

logger = setup_logging()


class ModelType(Enum):
    """模型类型"""

    GGUF = "gguf"  # llama.cpp量化格式
    PYTORCH = "pytorch"  # PyTorch原生格式
    TRANSFORMERS = "transformers"  # HuggingFace transformers
    ONNX = "onnx"  # ONNX格式


class ModelStatus(Enum):
    """模型状态"""

    UNLOADED = "unloaded"  # 未加载
    LOADING = "loading"  # 加载中
    LOADED = "loaded"  # 已加载
    UNLOADING = "unloading"  # 卸载中
    ERROR = "error"  # 错误状态


class InferenceBackend(Enum):
    """推理后端"""

    LLAMA_CPP = "llama_cpp"  # llama.cpp (CPU/GPU/Metal)
    TRANSFORMERS = "transformers"  # HuggingFace Transformers
    VLLM = "vllm"  # v_llm (PagedAttention)
    TRTLLM = "trt_llm"  # TensorRT-LLM


@dataclass
class ModelConfig:
    """模型配置"""

    # 基本信息
    model_id: str  # 模型唯一标识
    model_name: str  # 模型名称
    model_type: ModelType  # 模型类型
    model_path: str  # 模型文件路径

    # 模型规格
    parameters: int  # 参数量(单位:亿)
    context_length: int  # 上下文长度
    quantization: str  # 量化方式(如Q4_K_M)

    # 推理配置
    backend: InferenceBackend  # 推理后端
    gpu_layers: int = -1  # GPU层数(-1表示全部)
    n_ctx: int = 8192  # 上下文窗口大小
    n_batch: int = 512  # 批处理大小
    n_threads: int = 8  # CPU线程数
    use_mmap: bool = True  # 使用内存映射
    use_mlock: bool = False  # 使用内存锁定(仅Linux)

    # 生成参数
    temperature: float = 0.7  # 温度参数
    top_p: float = 0.9  # top-p采样
    top_k: int = 40  # top-k采样
    repeat_penalty: float = 1.1  # 重复惩罚

    # 元数据
    description: str = ""  # 模型描述
    tags: list[str] | None = None  # 标签
    created_at: str = None  # 创建时间

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


class ModelRegistry:
    """模型注册中心"""

    def __init__(self, registry_path: str | None = None):
        """
        初始化模型注册中心

        Args:
            registry_path: 注册表文件路径
        """
        if registry_path is None:
            registry_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "..",
                "config",
                "models",
                "model_registry.json",
            )

        self.registry_path = registry_path
        self.models: dict[str, ModelConfig] = {}
        self.model_status: dict[str, ModelStatus] = {}
        self.model_instances: dict[str, Any] = {}

        # 确保目录存在
        os.makedirs(os.path.dirname(registry_path), exist_ok=True)

        # 加载已有注册表
        self._load_registry()

        logger.info(f"✅ 模型注册中心初始化完成: {len(self.models)}个已注册模型")

    def _load_registry(self) -> Any:
        """加载模型注册表"""
        if os.path.exists(self.registry_path):
            try:
                with open(self.registry_path, encoding="utf-8") as f:
                    data = json.load(f)

                for model_data in data.get("models", []):
                    config = ModelConfig(
                        model_id=model_data["model_id"],
                        model_name=model_data["model_name"],
                        model_type=ModelType(model_data["model_type"]),
                        model_path=model_data["model_path"],
                        parameters=model_data["parameters"],
                        context_length=model_data["context_length"],
                        quantization=model_data["quantization"],
                        backend=InferenceBackend(model_data["backend"]),
                        gpu_layers=model_data.get("gpu_layers", -1),
                        n_ctx=model_data.get("n_ctx", 8192),
                        n_batch=model_data.get("n_batch", 512),
                        n_threads=model_data.get("n_threads", 8),
                        use_mmap=model_data.get("use_mmap", True),
                        use_mlock=model_data.get("use_mlock", False),
                        temperature=model_data.get("temperature", 0.7),
                        top_p=model_data.get("top_p", 0.9),
                        top_k=model_data.get("top_k", 40),
                        repeat_penalty=model_data.get("repeat_penalty", 1.1),
                        description=model_data.get("description", ""),
                        tags=model_data.get("tags", []),
                        created_at=model_data.get("created_at"),
                    )
                    self.models[config.model_id] = config
                    self.model_status[config.model_id] = ModelStatus.UNLOADED

                logger.info(f"📋 加载了 {len(self.models)} 个已注册模型")

            except Exception as e:
                logger.error(f"❌ 加载模型注册表失败: {e}")
                self.models = {}
                self.model_status = {}

    def _save_registry(self) -> Any:
        """保存模型注册表"""
        try:
            data = {
                "version": "1.0.0",
                "last_updated": datetime.now().isoformat(),
                "models": [
                    {
                        **{
                            k: v.value if isinstance(v, (ModelType, InferenceBackend)) else v
                            for k, v in asdict(model).items()
                        },
                        "model_type": model.model_type.value,
                        "backend": model.backend.value,
                    }
                    for model in self.models.values()
                ],
            }

            with open(self.registry_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.debug("💾 模型注册表已保存")

        except Exception as e:
            logger.error(f"❌ 保存模型注册表失败: {e}")

    def register_model(self, config: ModelConfig) -> bool:
        """
        注册模型

        Args:
            config: 模型配置

        Returns:
            是否注册成功
        """
        try:
            # 验证模型文件存在
            if not os.path.exists(config.model_path):
                logger.error(f"❌ 模型文件不存在: {config.model_path}")
                return False

            # 注册模型
            self.models[config.model_id] = config
            self.model_status[config.model_id] = ModelStatus.UNLOADED

            # 保存注册表
            self._save_registry()

            logger.info(f"✅ 模型已注册: {config.model_name} ({config.model_id})")
            return True

        except Exception as e:
            logger.error(f"❌ 注册模型失败: {e}")
            return False

    def unregister_model(self, model_id: str) -> bool:
        """
        注销模型

        Args:
            model_id: 模型ID

        Returns:
            是否注销成功
        """
        if model_id not in self.models:
            logger.warning(f"⚠️ 模型未注册: {model_id}")
            return False

        # 如果模型已加载,先卸载
        if self.model_status.get(model_id) == ModelStatus.LOADED:
            logger.warning(f"⚠️ 模型已加载,请先卸载: {model_id}")
            return False

        # 注销模型
        del self.models[model_id]
        del self.model_status[model_id]

        # 保存注册表
        self._save_registry()

        logger.info(f"✅ 模型已注销: {model_id}")
        return True

    def get_model_config(self, model_id: str) -> ModelConfig | None:
        """
        获取模型配置

        Args:
            model_id: 模型ID

        Returns:
            模型配置,不存在返回None
        """
        return self.models.get(model_id)

    def list_models(
        self, model_type: ModelType = None, status: ModelStatus = None
    ) -> list[ModelConfig]:
        """
        列出模型

        Args:
            model_type: 过滤模型类型
            status: 过滤模型状态

        Returns:
            模型配置列表
        """
        models = list(self.models.values())

        if model_type:
            models = [m for m in models if m.model_type == model_type]

        if status:
            models = [m for m in models if self.model_status.get(m.model_id) == status]

        return models

    def get_model_status(self, model_id: str) -> ModelStatus | None:
        """
        获取模型状态

        Args:
            model_id: 模型ID

        Returns:
            模型状态
        """
        return self.model_status.get(model_id)

    def update_model_status(self, model_id: str, status: ModelStatus) -> None:
        """
        更新模型状态

        Args:
            model_id: 模型ID
            status: 新状态
        """
        if model_id in self.model_status:
            self.model_status[model_id] = status
            logger.debug(f"📊 模型状态更新: {model_id} -> {status.value}")

    def set_model_instance(self, model_id: str, instance: Any) -> None:
        """
        设置模型实例

        Args:
            model_id: 模型ID
            instance: 模型实例
        """
        self.model_instances[model_id] = instance
        logger.debug(f"🔧 模型实例已设置: {model_id}")

    def get_model_instance(self, model_id: str) -> Any | None:
        """
        获取模型实例

        Args:
            model_id: 模型ID

        Returns:
            模型实例
        """
        return self.model_instances.get(model_id)

    def remove_model_instance(self, model_id: str) -> None:
        """
        移除模型实例

        Args:
            model_id: 模型ID
        """
        if model_id in self.model_instances:
            del self.model_instances[model_id]
            logger.debug(f"🗑️ 模型实例已移除: {model_id}")

    def get_registry_stats(self) -> dict[str, Any]:
        """
        获取注册表统计信息

        Returns:
            统计信息字典
        """
        stats = {
            "total_models": len(self.models),
            "by_type": {},
            "by_status": {},
            "by_backend": {},
            "total_parameters": 0,
        }

        for model in self.models.values():
            # 按类型统计
            mtype = model.model_type.value
            stats["by_type"][mtype] = stats["by_type"].get(mtype, 0) + 1

            # 按状态统计
            status = self.model_status.get(model.model_id, ModelStatus.UNLOADED).value
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1

            # 按后端统计
            backend = model.backend.value
            stats["by_backend"][backend] = stats["by_backend"].get(backend, 0) + 1

            # 总参数量
            stats["total_parameters"] += model.parameters

        return stats


# 全局单例
_registry: ModelRegistry | None = None


def get_model_registry() -> ModelRegistry:
    """获取模型注册中心单例"""
    global _registry
    if _registry is None:
        _registry = ModelRegistry()
    return _registry


# 预配置的模型
def register_preset_models() -> Any:
    """注册预配置的模型"""
    registry = get_model_registry()

    # Qwen2.5-14B-Instruct-GGUF
    qwen_config = ModelConfig(
        model_id="qwen2.5-14b-instruct-q4_k_m",
        model_name="Qwen2.5-14B-Instruct-Q4_K_M",
        model_type=ModelType.GGUF,
        model_path="/Users/xujian/Athena工作平台/models/local/qwen2.5-14b-instruct-gguf/Qwen2.5-14B-Instruct-Q4_K_M.gguf",
        parameters=14,  # 140亿
        context_length=131072,  # Qwen2.5支持128K上下文
        quantization="Q4_K_M",
        backend=InferenceBackend.LLAMA_CPP,
        gpu_layers=-1,  # 全部GPU层
        n_ctx=32768,  # 默认32K上下文
        n_batch=512,
        n_threads=8,
        use_mmap=True,
        use_mlock=False,
        temperature=0.7,
        top_p=0.9,
        top_k=40,
        repeat_penalty=1.1,
        description="通义千问2.5-14B指令微调模型,Q4_K_M量化,支持长上下文",
        tags=["qwen", "chinese", "instruct", "gguf", "quantized"],
    )

    registry.register_model(qwen_config)

    logger.info(f"✅ 预配置模型已注册: {len(registry.models)}个")


if __name__ == "__main__":
    # 测试模型注册中心
    # setup_logging()  # 日志配置已移至模块导入

    # 注册预配置模型
    register_preset_models()

    # 获取注册中心
    registry = get_model_registry()

    # 列出所有模型
    print("\n📋 已注册模型列表:")
    print("=" * 80)
    for model in registry.list_models():
        print(f"\n模型ID: {model.model_id}")
        print(f"名称: {model.model_name}")
        print(f"类型: {model.model_type.value}")
        print(f"后端: {model.backend.value}")
        print(f"参数: {model.parameters}B")
        print(f"上下文: {model.context_length:,} tokens")
        print(f"量化: {model.quantization}")
        print(f"状态: {registry.get_model_status(model.model_id).value}")
        print(f"路径: {model.model_path}")

    # 统计信息
    stats = registry.get_registry_stats()
    print("\n📊 注册表统计:")
    print("=" * 80)
    print(f"总模型数: {stats['total_models']}")
    print(f"按类型: {stats['by_type']}")
    print(f"按状态: {stats['by_status']}")
    print(f"按后端: {stats['by_backend']}")
    print(f"总参数量: {stats['total_parameters']}B")
