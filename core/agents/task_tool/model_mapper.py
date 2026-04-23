from __future__ import annotations
"""
ModelMapper - 模型映射器

支持Kode模型到Athena模型的映射，并提供模型配置管理。
"""

import os
from typing import Any

from core.agents.task_tool.models import ModelChoice


class ModelMapper:
    """模型映射器类

    负责将Kode模型名称映射到Athena平台使用的模型名称。
    映射规则：
    - haiku → quick (快速模型)
    - sonnet → task (任务模型)
    - opus → main (主模型)
    """

    # 模型映射规则
    MODEL_MAPPING: dict[str, str] = {
        "haiku": "quick",
        "sonnet": "task",
        "opus": "main",
    }

    # 模型配置
    MODEL_CONFIGS: dict[str, dict[str, Any]] = {
        "quick": {
            "name": "quick",
            "temperature": 0.7,
            "max_tokens": 4096,
            "description": "快速模型，适合简单任务",
        },
        "task": {
            "name": "task",
            "temperature": 0.5,
            "max_tokens": 8192,
            "description": "任务模型，适合复杂任务",
        },
        "main": {
            "name": "main",
            "temperature": 0.3,
            "max_tokens": 16384,
            "description": "主模型，适合深度分析",
        },
    }

    def __init__(self):
        """初始化ModelMapper"""
        self._environment_model: Optional[str] = os.getenv("ATHENA_SUBAGENT_MODEL")
        if self._environment_model:
            self._environment_model = self.normalize_model_name(self._environment_model)

    def map(self, model: str | ModelChoice) -> str:
        """将模型名称映射到Athena模型名称

        Args:
            model: 模型名称或ModelChoice枚举

        Returns:
            Athena模型名称

        Raises:
            ValueError: 如果模型名称未知

        Examples:
            >>> mapper = ModelMapper()
            >>> mapper.map("haiku")
            'quick'
            >>> mapper.map(ModelChoice.SONNET)
            'task'
        """
        # 规范化模型名称
        normalized = self.normalize_model_name(model)

        # 检查模型是否在映射表中
        if normalized not in self.MODEL_MAPPING:
            raise ValueError(
                f"Unknown model: {model}. Available models: {', '.join(self.MODEL_MAPPING.keys())}"
            )

        # 返回映射的模型名称
        return self.MODEL_MAPPING[normalized]

    def get_model_config(self, model: str | ModelChoice) -> dict[str, Any]:
        """获取模型配置

        Args:
            model: 模型名称或ModelChoice枚举

        Returns:
            模型配置字典

        Raises:
            ValueError: 如果模型名称未知
        """
        # 映射到Athena模型名称
        athena_model = self.map(model)

        # 返回模型配置
        return self.MODEL_CONFIGS[athena_model]

    def normalize_model_name(self, model: str | ModelChoice) -> str:
        """规范化模型名称

        将模型名称转换为小写形式。
        如果是ModelChoice枚举，提取其值。

        Args:
            model: 模型名称或ModelChoice枚举

        Returns:
            规范化后的模型名称（小写）

        Examples:
            >>> mapper = ModelMapper()
            >>> mapper.normalize_model_name("HAIKU")
            'haiku'
            >>> mapper.normalize_model_name(ModelChoice.SONNET)
            'sonnet'
        """
        # 如果是枚举，获取其值
        if isinstance(model, ModelChoice):
            return model.value

        # 如果是字符串，转换为小写并去除空格
        if isinstance(model, str):
            return model.strip().lower()

        # 其他类型抛出错误
        raise TypeError(f"model must be str or ModelChoice, got {type(model).__name__}")

    def get_available_models(self) -> list[str]:
        """获取可用的模型列表

        Returns:
            可用模型名称列表
        """
        return list(self.MODEL_MAPPING.keys())

    def get_environment_model(self) -> Optional[str]:
        """获取环境变量中指定的模型

        Returns:
            环境变量ATHENA_SUBAGENT_MODEL指定的模型名称，如果未设置则返回None
        """
        return self._environment_model
