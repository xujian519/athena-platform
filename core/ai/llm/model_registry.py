
"""
统一LLM层 - 模型能力注册表
管理所有模型的元数据和能力定义

作者: Claude Code
日期: 2026-01-23
"""

import json
import logging
import os
import threading
from datetime import datetime
from typing import Optional
from pathlib import Path

from core.ai.llm.base import DeploymentType, ModelCapability, ModelType

logger = logging.getLogger(__name__)


class ModelCapabilityRegistry:
    """
    模型能力注册表

    管理所有模型的元数据和能力定义,提供模型查询和注册功能
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化注册表

        Args:
            config_path: 模型配置文件路径
        """
        self.capabilities: dict[str, ModelCapability] = {}

        # 优先级:参数 > 环境变量 > 相对路径默认值
        if config_path:
            self.config_path = config_path
        else:
            # 尝试从环境变量获取配置路径
            env_config_path = os.getenv("LLM_MODEL_REGISTRY_PATH")
            if env_config_path:
                self.config_path = env_config_path
                logger.info(f"📦 使用环境变量配置路径: {env_config_path}")
            else:
                # 使用相对于当前工作目录的默认路径
                # 支持从任何位置运行代码
                default_config_name = "llm_model_registry.json"
                possible_paths = [
                    # 当前目录的config子目录
                    os.path.join("config", default_config_name),
                    # 上级目录的config子目录(支持从子目录运行)
                    os.path.join("..", "config", default_config_name),
                    # 绝对路径 fallback(保持向后兼容)
                    os.path.join(os.getcwd(), "config", default_config_name),
                ]

                # 找到第一个存在的路径
                for path in possible_paths:
                    if os.path.exists(path):
                        self.config_path = os.path.abspath(path)
                        logger.info(f"📦 使用默认配置路径: {self.config_path}")
                        break
                else:
                    # 如果都不存在,使用第一个作为默认值(会触发fallback到默认配置)
                    self.config_path = os.path.abspath(possible_paths[0])
                    logger.debug(f"📦 使用配置路径(文件不存在): {self.config_path}")

        self._load_capabilities()

    def _load_capabilities(self):
        """加载模型能力配置"""
        config_file = Path(self.config_path)
        if config_file.exists():
            try:
                with open(config_file, encoding="utf-8") as f:
                    data = json.load(f)
                    for model_data in data.get("models", []):
                        capability = self._parse_capability(model_data)
                        self.capabilities[capability.model_id] = capability
                logger.info(f"✅ 加载了 {len(self.capabilities)} 个模型能力定义")
            except (FileNotFoundError, json.JSONDecodeError, KeyError, ValueError) as e:
                logger.error(f"❌ 加载模型配置失败: {e}", exc_info=True)
                logger.info("📦 使用默认模型配置")
                self._load_default_capabilities()
        else:
            logger.warning(f"⚠️ 模型配置文件不存在: {self.config_path}")
            logger.info("📦 使用默认模型配置")
            self._load_default_capabilities()

    def _parse_capability(self, data: dict) -> ModelCapability:
        """从字典解析模型能力"""
        return ModelCapability(
            model_id=data["model_id"],
            model_type=ModelType(data["model_type"]),
            deployment=DeploymentType(data["deployment"]),
            max_context=data["max_context"],
            supports_streaming=data.get("supports_streaming", False),
            supports_function_call=data.get("supports_function_call", False),
            supports_vision=data.get("supports_vision", False),
            supports_thinking=data.get("supports_thinking", False),
            avg_latency_ms=data.get("avg_latency_ms", 1000),
            throughput_tps=data.get("throughput_tps", 50),
            cost_per_1k_tokens=data.get("cost_per_1k_tokens", 0.01),
            quality_score=data.get("quality_score", 0.8),
            suitable_tasks=data.get("suitable_tasks", []),
            unsuitable_tasks=data.get("unsuitable_tasks", []),
        )

    def _load_default_capabilities(self):
        """加载默认模型能力配置"""
        # GLM-4.7-Plus (云端推理模型)
        self.capabilities["glm-4-plus"] = ModelCapability(
            model_id="glm-4-plus",
            model_type=ModelType.REASONING,
            deployment=DeploymentType.CLOUD,
            max_context=128000,
            supports_streaming=True,
            supports_function_call=True,
            supports_vision=False,
            supports_thinking=True,
            avg_latency_ms=1500,
            throughput_tps=80,
            cost_per_1k_tokens=0.05,
            quality_score=0.95,
            suitable_tasks=[
                "novelty_analysis",
                "creativity_analysis",
                "invalidation_analysis",
                "oa_response",
                "reasoning",
                "complex_analysis",
            ],
            unsuitable_tasks=["simple_chat"],
        )

        # GLM-4-Flash (高性能模型)
        self.capabilities["glm-4-flash"] = ModelCapability(
            model_id="glm-4-flash",
            model_type=ModelType.REASONING,
            deployment=DeploymentType.CLOUD,
            max_context=200000,
            supports_streaming=True,
            supports_function_call=True,
            supports_vision=False,
            supports_thinking=False,
            avg_latency_ms=800,
            throughput_tps=120,
            cost_per_1k_tokens=0.01,
            quality_score=0.90,
            suitable_tasks=["reasoning", "tech_analysis", "patent_search", "general_analysis"],
            unsuitable_tasks=[],
        )

        # DeepSeek-Chat (云端对话模型)
        self.capabilities["deepseek-chat"] = ModelCapability(
            model_id="deepseek-chat",
            model_type=ModelType.CHAT,
            deployment=DeploymentType.CLOUD,
            max_context=64000,
            supports_streaming=True,
            supports_function_call=False,
            supports_vision=False,
            supports_thinking=False,
            avg_latency_ms=1200,
            throughput_tps=60,
            cost_per_1k_tokens=0.014,
            quality_score=0.85,
            suitable_tasks=["general_chat", "conversation", "qa"],
            unsuitable_tasks=["complex_reasoning"],
        )

        # DeepSeek-Reasoner (云端推理模型)
        self.capabilities["deepseek-reasoner"] = ModelCapability(
            model_id="deepseek-reasoner",
            model_type=ModelType.REASONING,
            deployment=DeploymentType.CLOUD,
            max_context=64000,
            supports_streaming=True,
            supports_function_call=False,
            supports_vision=False,
            supports_thinking=True,
            avg_latency_ms=2000,
            throughput_tps=40,
            cost_per_1k_tokens=0.055,
            quality_score=0.92,
            suitable_tasks=[
                "novelty_analysis",
                "creativity_analysis",
                "math_reasoning",
                "complex_reasoning",
            ],
            unsuitable_tasks=["simple_chat"],
        )

        # ==================== 本地模型 (Ollama) ====================

        # Qwen3.5 (本地Ollama - 默认推理/对话/多模态模型)
        # 2026-03-22 更新: 提升为默认推理模型，复杂推理任务仍用云端
        self.capabilities["qwen3.5"] = ModelCapability(
            model_id="qwen3.5",
            model_type=ModelType.MULTIMODAL,  # 多模态类型，但支持推理和对话
            deployment=DeploymentType.LOCAL,
            max_context=262144,  # 256K 上下文
            supports_streaming=True,
            supports_function_call=True,
            supports_vision=True,
            supports_thinking=True,  # 支持思考模式
            avg_latency_ms=1000,
            throughput_tps=40,
            cost_per_1k_tokens=0.0,  # 本地免费
            quality_score=0.88,  # 7B模型，推理能力略低于云端大模型
            suitable_tasks=[
                # 多模态任务
                "image_analysis",
                "multimodal",
                "chart_analysis",
                "document_analysis",
                "ocr",
                "visual_reasoning",
                # 对话任务
                "general_chat",
                "conversation",
                "simple_chat",
                "qa",
                "simple_qa",
                # 日常推理任务 (非高复杂度)
                "reasoning",
                "tech_analysis",
                "patent_search",
                "fast_analysis",
                "step_by_step_reasoning",
                # 其他
                "chinese",
                "code_generation",
                "code_explanation",
            ],
            unsuitable_tasks=[
                # 高复杂度推理任务建议使用云端模型
                "novelty_analysis",       # 新颖性分析
                "creativity_analysis",    # 创造性判断
                "invalidation_analysis",  # 无效宣告
                "oa_response",            # 审查意见答复
                "complex_reasoning",      # 复杂推理
                "math_reasoning",         # 数学推理
            ],
        )

        # Qwen-VL-Max (通义千问视觉模型 - 云端备选)
        self.capabilities["qwen-vl-max"] = ModelCapability(
            model_id="qwen-vl-max",
            model_type=ModelType.MULTIMODAL,
            deployment=DeploymentType.CLOUD,
            max_context=30000,
            supports_streaming=True,
            supports_function_call=False,
            supports_vision=True,
            supports_thinking=False,
            avg_latency_ms=2000,
            throughput_tps=60,
            cost_per_1k_tokens=0.02,
            quality_score=0.94,
            suitable_tasks=[
                "image_analysis",
                "multimodal",
                "chart_analysis",
                "document_analysis",
                "ocr",
                "visual_reasoning",
            ],
            unsuitable_tasks=[],
        )

        # Qwen-VL-Plus
        self.capabilities["qwen-vl-plus"] = ModelCapability(
            model_id="qwen-vl-plus",
            model_type=ModelType.MULTIMODAL,
            deployment=DeploymentType.CLOUD,
            max_context=30000,
            supports_streaming=True,
            supports_function_call=False,
            supports_vision=True,
            supports_thinking=False,
            avg_latency_ms=1200,
            throughput_tps=90,
            cost_per_1k_tokens=0.008,
            quality_score=0.90,
            suitable_tasks=["image_analysis", "multimodal", "simple_visual_qa"],
            unsuitable_tasks=[],
        )

        # ==================== 编程模型 (国内) ====================

        # DeepSeek-Coder-V2
        self.capabilities["deepseek-coder-v2"] = ModelCapability(
            model_id="deepseek-coder-v2",
            model_type=ModelType.SPECIALIZED,
            deployment=DeploymentType.CLOUD,
            max_context=128000,
            supports_streaming=True,
            supports_function_call=True,
            supports_vision=False,
            supports_thinking=False,
            avg_latency_ms=1000,
            throughput_tps=100,
            cost_per_1k_tokens=0.014,
            quality_score=0.92,
            suitable_tasks=["code_generation", "code_review", "debugging"],
            unsuitable_tasks=[],
        )

        logger.info(f"✅ 加载了 {len(self.capabilities)} 个默认模型能力(仅云端模型)")

    def get_capability(self, model_id: str) -> Optional[ModelCapability]:
        """
        获取模型能力

        Args:
            model_id: 模型ID

        Returns:
            ModelCapability: 模型能力,如果不存在返回None
        """
        return self.capabilities.get(model_id)

    def get_models_by_type(self, model_type: ModelType) -> list[str]:
        """
        根据类型获取模型列表

        Args:
            model_type: 模型类型

        Returns:
            list[str]: 模型ID列表
        """
        return [
            model_id for model_id, cap in self.capabilities.items() if cap.model_type == model_type
        ]

    def get_models_by_deployment(self, deployment: DeploymentType) -> list[str]:
        """
        根据部署类型获取模型列表

        Args:
            deployment: 部署类型

        Returns:
            list[str]: 模型ID列表
        """
        return [
            model_id for model_id, cap in self.capabilities.items() if cap.deployment == deployment
        ]

    def get_suitable_models(self, task_type: str) -> list[str]:
        """
        获取适合指定任务的所有模型

        Args:
            task_type: 任务类型

        Returns:
            list[str]: 模型ID列表
        """
        suitable = []
        for model_id, cap in self.capabilities.items():
            if cap.is_suitable_for(task_type):
                suitable.append(model_id)
        return suitable

    def register_model(self, capability: ModelCapability):
        """
        注册新模型

        Args:
            capability: 模型能力定义
        """
        self.capabilities[capability.model_id] = capability
        logger.info(f"✅ 注册新模型: {capability.model_id}")

    def unregister_model(self, model_id: str):
        """
        注销模型

        Args:
            model_id: 模型ID
        """
        if model_id in self.capabilities:
            del self.capabilities[model_id]
            logger.info(f"✅ 注销模型: {model_id}")

    def list_all_models(self) -> list[str]:
        """
        列出所有模型

        Returns:
            list[str]: 所有模型ID
        """
        return list(self.capabilities.keys())

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "version": "1.0.0",
            "last_updated": datetime.now().isoformat(),
            "total_models": len(self.capabilities),
            "models": [cap.to_dict() for cap in self.capabilities.values()],
        }

    def save_to_file(self, path: Optional[str] = None):
        """
        保存到文件

        Args:
            path: 保存路径,默认使用初始化时的路径
        """
        save_path = path or self.config_path
        save_file = Path(save_path)
        save_file.parent.mkdir(parents=True, exist_ok=True)

        with open(save_file, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        logger.info(f"✅ 模型配置已保存到: {save_path}")

    def reload(self):
        """重新加载配置"""
        self.capabilities.clear()
        self._load_capabilities()


# 单例
_registry_instance: Optional[ModelCapabilityRegistry] = None
_registry_lock = threading.Lock()


def get_model_registry(config_path: Optional[str] = None) -> ModelCapabilityRegistry:
    """
    获取模型能力注册表单例(线程安全)

    Args:
        config_path: 配置文件路径

    Returns:
        ModelCapabilityRegistry: 注册表实例
    """
    global _registry_instance
    if _registry_instance is None:
        with _registry_lock:
            # 双重检查锁定
            if _registry_instance is None:
                _registry_instance = ModelCapabilityRegistry(config_path)
    return _registry_instance


def reset_model_registry():
    """重置单例(用于测试,线程安全)"""
    global _registry_instance
    with _registry_lock:
        _registry_instance = None

