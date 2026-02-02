#!/usr/bin/env python3
"""
状态模块基类
State Module Base Class

提供自动状态持久化能力:
1. 自动注册StateModule类型的属性
2. 支持手动注册普通属性
3. 提供state_dict()和load_state_dict()方法

作者: Athena平台团队
创建时间: 2026-01-20
版本: v1.0.0 "Phase 1"
"""

import json
import logging
from abc import ABC
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class StateModule(ABC):
    """
    状态模块基类

    提供自动状态持久化能力,支持:
    - 自动注册子StateModule属性
    - 手动注册普通状态属性
    - 递归状态保存和恢复
    - JSON格式持久化

    使用示例:
        class MyAgent(StateModule):
            def __init__(self):
                super().__init__()
                self.memory = WorkingMemory()  # 自动注册
                self.step_count = 0  # 需要手动注册
                self.register_state("step_count")
    """

    def __init__(self):
        """初始化状态模块"""
        # 使用object.__setattr__避免触发__setattr__
        object.__setattr__(self, "_state_attrs", set())
        object.__setattr__(self, "_registered_attrs", set())
        object.__setattr__(self, "_state_module_initialized", True)

        logger.debug(f"🔧 StateModule初始化: {self.__class__.__name__}")

    def __setattr__(self, name: str, value: Any) -> None:
        """
        拦截属性设置,自动注册StateModule类型的属性

        Args:
            name: 属性名称
            value: 属性值
        """
        # 跳过内部属性
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return

        # 检查是否已初始化(避免在__init__中触发)
        if getattr(self, "_state_module_initialized", False):
            # 自动注册StateModule类型的属性
            if isinstance(value, StateModule):
                self._state_attrs.add(name)  # type: ignore
                logger.debug(f"   🔧 自动注册子模块: {name}")

        object.__setattr__(self, name, value)

    def register_state(self, attr_name: str) -> None:
        """
        手动注册状态属性

        用于注册非StateModule类型的属性。

        Args:
            attr_name: 属性名称

        Example:
            self.register_state("step_count")
            self.register_state("last_result")
        """
        self._registered_attrs.add(attr_name)  # type: ignore
        logger.debug(f"   🔧 手动注册状态: {attr_name}")

    def register_states(self, attr_names: set[str]) -> None:
        """
        批量注册状态属性

        Args:
            attr_names: 属性名称集合
        """
        self._registered_attrs.update(attr_names)  # type: ignore
        logger.debug(f"   🔧 批量注册状态: {attr_names}")

    def unregister_state(self, attr_name: str) -> None:
        """
        取消注册状态属性

        Args:
            attr_name: 属性名称
        """
        self._registered_attrs.discard(attr_name)  # type: ignore
        logger.debug(f"   🔧 取消注册状态: {attr_name}")

    def state_dict(self) -> dict[str, Any]:
        """
        获取状态字典

        递归收集所有状态属性,包括嵌套的StateModule。

        Returns:
            包含所有状态属性的字典
        """
        state = {}

        # 自动注册的StateModule属性(递归)
        for attr in self._state_attrs:  # type: ignore
            if hasattr(self, attr):
                value = getattr(self, attr)
                if isinstance(value, StateModule):
                    state[attr] = value.state_dict()
                else:
                    # 处理非StateModule但被自动跟踪的属性
                    state[attr] = self._serialize_value(value)

        # 手动注册的属性
        for attr in self._registered_attrs:  # type: ignore
            if hasattr(self, attr):
                state[attr] = self._serialize_value(getattr(self, attr))

        logger.debug(f"📦 生成状态字典: {self.__class__.__name__} " f"({len(state)} 个属性)")

        return state

    def _serialize_value(self, value: Any) -> Any:
        """
        序列化值

        处理特殊类型,确保可JSON序列化。

        Args:
            value: 要序列化的值

        Returns:
            序列化后的值
        """
        # 处理特殊类型
        if hasattr(value, "__dict__"):
            # 自定义对象
            return {
                "_type": value.__class__.__name__,
                "_module": value.__class__.__module__,
                "data": value.__dict__,
            }
        elif isinstance(value, (set, frozenset)):
            # 集合类型
            return list(value)
        elif hasattr(value, "to_dict"):
            # 有to_dict方法的对象
            return value.to_dict()
        else:
            # 基本类型直接返回
            return value

    def load_state_dict(self, state_dict: dict[str, Any]) -> None:
        """
        加载状态字典

        递归恢复所有状态属性。

        Args:
            state_dict: 状态字典
        """
        logger.debug(f"📂 加载状态字典: {self.__class__.__name__} " f"({len(state_dict)} 个属性)")

        for attr, value in state_dict.items():
            # 检查是否是嵌套的StateModule
            if attr in self._state_attrs and hasattr(self, attr):  # type: ignore
                child_module = getattr(self, attr)
                if isinstance(child_module, StateModule) and isinstance(value, dict):
                    # 递归加载子模块状态
                    child_module.load_state_dict(value)
                else:
                    # 直接设置
                    setattr(self, attr, value)
            else:
                # 检查是否是序列化的对象
                if isinstance(value, dict) and "_type" in value:
                    # 反序列化自定义对象
                    setattr(self, attr, self._deserialize_value(value))
                else:
                    # 直接设置普通属性
                    try:
                        setattr(self, attr, value)
                    except AttributeError as e:
                        logger.warning(f"⚠️ 无法设置属性 {attr}: {e}")

    def _deserialize_value(self, value: dict[str, Any]) -> Any:
        """
        反序列化值

        Args:
            value: 序列化的值

        Returns:
            反序列化后的值
        """
        # 简单实现:返回原始数据
        # 实际使用时可以根据类型进行更复杂的反序列化
        return value.get("data", value)

    async def save_state(self, file_path: str) -> None:
        """
        保存状态到文件

        Args:
            file_path: 文件路径
        """
        state = self.state_dict()

        # 确保目录存在
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        # 保存为JSON
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2, default=str)

        logger.info(f"💾 状态已保存: {file_path}")

    async def load_state(self, file_path: str) -> None:
        """
        从文件加载状态

        Args:
            file_path: 文件路径
        """
        with open(file_path, encoding="utf-8") as f:
            state_dict = json.load(f)

        self.load_state_dict(state_dict)

        logger.info(f"📂 状态已加载: {file_path}")

    def get_state_summary(self) -> dict[str, Any]:
        """
        获取状态摘要

        Returns:
            状态摘要信息
        """
        auto_registered = len(self._state_attrs)  # type: ignore
        manually_registered = len(self._registered_attrs)  # type: ignore

        return {
            "class_name": self.__class__.__name__,
            "auto_registered_attrs": auto_registered,
            "manually_registered_attrs": manually_registered,
            "total_state_attrs": auto_registered + manually_registered,
            "auto_attrs": list(self._state_attrs),  # type: ignore
            "manual_attrs": list(self._registered_attrs),  # type: ignore
        }


__all__ = ["StateModule"]
