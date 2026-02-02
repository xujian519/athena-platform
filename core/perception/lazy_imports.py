#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重型依赖懒加载管理器
Heavy Dependencies Lazy Loader

优化numpy、opencv、torch等重型库的加载，实现按需加载

作者: Athena AI系统
创建时间: 2026-01-26
版本: 1.0.0
"""

import importlib
import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


class LazyLoader:
    """
    懒加载器

    延迟加载重型依赖库，只在真正需要时才导入
    """

    def __init__(self, module_name: str, import_path: str | None = None):
        """
        初始化懒加载器

        Args:
            module_name: 模块名称（用于日志）
            import_path: 导入路径（如 'numpy' 或 'numpy as np'）
        """
        self.module_name = module_name
        self.import_path = import_path or module_name
        self._module = None

    def __getattr__(self, name: str) -> Any:
        """
        动态加载模块属性

        当访问模块属性时才真正导入模块
        """
        if self._module is None:
            logger.info(f"懒加载模块: {self.module_name}")
            try:
                self._module = importlib.import_module(self.import_path.split()[0])
            except ImportError as e:
                logger.error(f"无法导入模块 {self.module_name}: {e}")
                raise ImportError(
                    f"模块 {self.module_name} 未安装。"
                    f"请运行: pip install {self.module_name}"
                ) from e

        return getattr(self._module, name)

    def is_loaded(self) -> bool:
        """检查模块是否已加载"""
        return self._module is not None


def lazy_import(module_name: str, import_path: str | None = None) -> LazyLoader:
    """
    创建懒加载器的便捷函数

    Args:
        module_name: 模块名称
        import_path: 导入路径

    Returns:
        LazyLoader实例

    示例:
        >>> np = lazy_import('numpy', 'numpy')
        >>> # 此时numpy还未加载
        >>> # 第一次使用时才加载
        >>> arr = np.array([1, 2, 3])
    """
    return LazyLoader(module_name, import_path)


# 预定义的懒加载模块
# 这些模块将在第一次使用时才加载

numpy = lazy_import("numpy", "numpy")
cv2 = lazy_import("opencv-python", "cv2")
torch = lazy_import("torch", "torch")
torchvision = lazy_import("torchvision", "torchvision")
PIL = lazy_import("pillow", "PIL")

# 更复杂的导入（需要特殊处理）
class CV2Loader:
    """
    OpenCV懒加载器

    提供更智能的cv2模块加载
    """

    def __init__(self):
        self._cv2 = None

    def __getattr__(self, name: str) -> Any:
        if self._cv2 is None:
            logger.info("懒加载OpenCV模块")
            try:
                import cv2 as cv2_module
                self._cv2 = cv2_module
            except ImportError:
                logger.error("OpenCV未安装")
                raise ImportError(
                    "OpenCV未安装。请运行: pip install opencv-python"
                )
        return getattr(self._cv2, name)

    def imread(self, path: str, flags: int = 1):
        """读取图像（常用方法的便捷封装）"""
        if self._cv2 is None:
            # 触发加载
            _ = self.version
        return self._cv2.imread(path, flags)


cv2_extended = CV2Loader()


# 导出
__all__ = [
    "LazyLoader",
    "lazy_import",
    # 预定义的懒加载模块
    "numpy",
    "cv2",
    "torch",
    "torchvision",
    "PIL",
    "cv2_extended",
]
