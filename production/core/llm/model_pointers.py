"""
模型指针系统

参考 kode-agent 的 Model Pointers 设计，实现配置驱动的模型路由。
通过语义化的指针名称（main/task/reasoning/quick）映射到具体的模型ID，
替代硬编码的模型选择逻辑。

使用方式：
    pointers = get_model_pointers()
    model_id = pointers.resolve('task')  # → 'deepseek-chat'
    model_id = pointers.resolve('reasoning')  # → 'deepseek-reasoner'

配置文件：config/model_pointers.json

Author: Athena Team
"""

from __future__ import annotations

import json
import logging
import os
import threading
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


# 指针名称常量
POINTER_MAIN = 'main'          # 主对话模型 - 处理用户的主要交互
POINTER_TASK = 'task'          # 任务执行模型 - 子代理和并行任务
POINTER_REASONING = 'reasoning'  # 深度推理模型 - 复杂分析和逻辑推理
POINTER_QUICK = 'quick'        # 快速响应模型 - 简单NLP任务（标题生成、分类等）

# 所有合法指针名称
VALID_POINTERS = {POINTER_MAIN, POINTER_TASK, POINTER_REASONING, POINTER_QUICK}


@dataclass
class ModelPointers:
    """
    模型指针配置

    将语义化的指针名称映射到具体的模型ID。
    支持从配置文件加载、运行时修改和动态回退。

    Example:
        pointers = ModelPointers(
            main='deepseek-chat',
            task='deepseek-chat',
            reasoning='deepseek-reasoner',
            quick='glm-4-flash',
        )

        # 解析指针
        model_id = pointers.resolve('task')  # → 'deepseek-chat'

        # 运行时切换
        pointers.set('task', 'glm-4-flash')
    """

    # 四个核心指针
    main: str = 'deepseek-chat'
    task: str = 'deepseek-chat'
    reasoning: str = 'deepseek-reasoner'
    quick: str = 'glm-4-flash'

    # 自定义指针（扩展用）
    custom: dict[str, str] = field(default_factory=dict)

    # 回退配置（当指定模型不可用时的备选）
    fallback: dict[str, str] = field(default_factory=lambda: {
        'main': 'glm-4-flash',
        'task': 'glm-4-flash',
        'reasoning': 'deepseek-chat',
        'quick': 'qwen3.5',
    })

    def resolve(self, pointer: str, fallback_available: list[str] | None = None) -> str:
        """
        解析指针到具体模型ID

        Args:
            pointer: 指针名称（main/task/reasoning/quick 或自定义名称）
            fallback_available: 当前可用的模型ID列表（用于智能回退）

        Returns:
            str: 模型ID
        """
        # 1. 尝试从核心指针获取
        model_id = getattr(self, pointer, None)

        # 2. 尝试从自定义指针获取
        if model_id is None:
            model_id = self.custom.get(pointer)

        # 3. 未知指针，回退到 main
        if model_id is None:
            logger.warning(f"未知指针 '{pointer}'，回退到 'main'")
            model_id = self.main

        # 4. 如果提供了可用模型列表，检查模型是否可用
        if fallback_available is not None:
            if model_id not in fallback_available:
                # 尝试回退配置
                fallback_model = self.fallback.get(pointer)
                if fallback_model and fallback_model in fallback_available:
                    logger.info(
                        f"模型 '{model_id}' 不可用，使用回退模型 '{fallback_model}' "
                        f"(指针: {pointer})"
                    )
                    return fallback_model

                # 从可用列表中选择第一个
                if fallback_available:
                    selected = fallback_available[0]
                    logger.warning(
                        f"模型 '{model_id}' 不可用且无回退，使用 '{selected}' "
                        f"(指针: {pointer})"
                    )
                    return selected

                # 完全没有可用模型
                logger.error(f"没有可用的模型 (指针: {pointer})")
                return model_id  # 返回原始值

        return model_id

    def set(self, pointer: str, model_id: str) -> None:
        """
        设置指针映射

        Args:
            pointer: 指针名称
            model_id: 模型ID
        """
        if pointer in VALID_POINTERS:
            setattr(self, pointer, model_id)
        else:
            self.custom[pointer] = model_id
        logger.info(f"模型指针更新: {pointer} → {model_id}")

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        result: dict[str, Any] = {}
        result['main'] = self.main
        result['task'] = self.task
        result['reasoning'] = self.reasoning
        result['quick'] = self.quick
        if self.custom:
            result['custom'] = dict(self.custom)
        result['fallback'] = dict(self.fallback)
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ModelPointers:
        """从字典创建"""
        return cls(
            main=data.get('main', 'deepseek-chat'),
            task=data.get('task', 'deepseek-chat'),
            reasoning=data.get('reasoning', 'deepseek-reasoner'),
            quick=data.get('quick', 'glm-4-flash'),
            custom=data.get('custom', {}),
            fallback=data.get('fallback', {
                'main': 'glm-4-flash',
                'task': 'glm-4-flash',
                'reasoning': 'deepseek-chat',
                'quick': 'qwen3.5',
            }),
        )

    @classmethod
    def from_config_file(cls, config_path: str) -> ModelPointers:
        """从配置文件加载"""
        try:
            with open(config_path, encoding='utf-8') as f:
                data = json.load(f)
            pointers = cls.from_dict(data)
            logger.info(f"从配置文件加载模型指针: {config_path}")
            return pointers
        except FileNotFoundError:
            logger.warning(f"模型指针配置文件不存在: {config_path}，使用默认值")
            return cls()
        except json.JSONDecodeError as e:
            logger.error(f"模型指针配置文件格式错误: {config_path}: {e}")
            return cls()
        except Exception as e:
            logger.error(f"加载模型指针配置失败: {e}")
            return cls()


def _get_default_config_path() -> str:
    """获取默认配置文件路径"""
    # 优先级: 环境变量 → config/ 目录
    env_path = os.getenv('MODEL_POINTERS_CONFIG')
    if env_path:
        return env_path

    # 查找项目根目录下的 config 目录
    cwd = os.getcwd()
    candidates = [
        os.path.join(cwd, 'config', 'model_pointers.json'),
        os.path.join(cwd, '..', 'config', 'model_pointers.json'),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path

    # 返回默认路径（即使不存在）
    return candidates[0]


# ============================================================
# 单例管理
# ============================================================

_pointers_instance: ModelPointers | None = None
_pointers_lock = threading.Lock()


def get_model_pointers(config_path: str | None = None) -> ModelPointers:
    """
    获取模型指针单例（线程安全）

    Args:
        config_path: 配置文件路径（可选，默认自动查找）

    Returns:
        ModelPointers: 模型指针实例
    """
    global _pointers_instance
    if _pointers_instance is None:
        with _pointers_lock:
            if _pointers_instance is None:
                path = config_path or _get_default_config_path()
                _pointers_instance = ModelPointers.from_config_file(path)
    return _pointers_instance


def reset_model_pointers() -> None:
    """重置单例（用于测试或重新加载配置）"""
    global _pointers_instance
    with _pointers_lock:
        _pointers_instance = None


def reload_model_pointers(config_path: str | None = None) -> ModelPointers:
    """重新加载模型指针配置"""
    reset_model_pointers()
    return get_model_pointers(config_path)
