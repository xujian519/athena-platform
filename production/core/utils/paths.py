#!/usr/bin/env python3
"""
Athena平台路径工具模块
Platform Path Utilities

统一管理项目路径,避免硬编码路径,提高代码可移植性。

功能:
1. 自动检测项目根目录
2. 提供常用路径的访问方法
3. 确保项目路径在sys.path中
4. 支持环境变量配置

作者: Athena平台团队
创建时间: 2026-01-01
版本: v1.0.0
"""

from __future__ import annotations
import os
import sys
from pathlib import Path


class AthenaPaths:
    """Athena平台路径管理器"""

    def __init__(self, project_root: Path | None = None):
        """
        初始化路径管理器

        Args:
            project_root: 项目根目录,如果不指定则自动检测
        """
        self._project_root = self._detect_project_root(project_root)
        self._ensure_project_root_in_path()

    @staticmethod
    def _detect_project_root(override_path: Path | None = None) -> Path:
        """
        检测项目根目录

        检测策略(按优先级):
        1. 使用传入的覆盖路径
        2. 环境变量 ATHENA_HOME
        3. 从当前文件向上查找包含特定标记的目录

        Args:
            override_path: 覆盖路径

        Returns:
            Path: 项目根目录
        """
        # 1. 使用覆盖路径
        if override_path is not None:
            return Path(override_path).resolve()

        # 2. 环境变量
        env_home = os.environ.get("ATHENA_HOME")
        if env_home:
            return Path(env_home).resolve()

        # 3. 自动检测
        # 从当前文件向上查找
        current_file = Path(__file__).resolve()
        current_dir = current_file.parent

        # 查找标记:包含这些目录/文件的即为项目根目录
        markers = [
            "core",
            "services",
            "modules",
            "production",
            "config",
            "CLAUDE.md",
            "README.md",
            "athena_services.sh",
        ]

        # 向上最多查找5级
        search_path = current_dir
        for _ in range(6):
            # 检查是否有足够的标记
            marker_count = sum(1 for marker in markers if (search_path / marker).exists())

            if marker_count >= 3:  # 至少包含3个标记
                return search_path

            parent = search_path.parent
            if parent == search_path:  # 已到达根目录
                break
            search_path = parent

        # 如果找不到,使用当前工作目录
        return Path.cwd()

    def _ensure_project_root_in_path(self) -> None:
        """确保项目根目录在sys.path中"""
        root_str = str(self._project_root)
        if root_str not in sys.path:
            sys.path.insert(0, root_str)

    @property
    def project_root(self) -> Path:
        """获取项目根目录"""
        return self._project_root

    @property
    def core_dir(self) -> Path:
        """获取core目录"""
        return self._project_root / "core"

    @property
    def services_dir(self) -> Path:
        """获取services目录"""
        return self._project_root / "services"

    @property
    def modules_dir(self) -> Path:
        """获取modules目录"""
        return self._project_root / "modules"

    @property
    def config_dir(self) -> Path:
        """获取config目录"""
        return self._project_root / "config"

    @property
    def production_dir(self) -> Path:
        """获取production目录"""
        return self._project_root / "production"

    @property
    def data_dir(self) -> Path:
        """获取data目录"""
        return self._project_root / "data"

    @property
    def logs_dir(self) -> Path:
        """获取logs目录"""
        return self._project_root / "production" / "logs"

    @property
    def cache_dir(self) -> Path:
        """获取cache目录"""
        return self._project_root / "production" / "cache"

    @property
    def models_dir(self) -> Path:
        """获取models目录"""
        return self._project_root / "models"

    @property
    def scripts_dir(self) -> Path:
        """获取scripts目录"""
        return self._project_root / "production" / "scripts"

    @property
    def tests_dir(self) -> Path:
        """获取tests目录"""
        return self._project_root / "tests"

    @property
    def apps_dir(self) -> Path:
        """获取apps目录"""
        return self._project_root / "apps"

    def get_relative_path(self, target_path: Path) -> Path:
        """
        获取相对于项目根目录的路径

        Args:
            target_path: 目标路径

        Returns:
            Path: 相对路径
        """
        try:
            return target_path.relative_to(self._project_root)
        except ValueError:
            # 如果不在项目内,返回绝对路径
            return target_path

    def resolve_path(self, path_str: str) -> Path:
        """
        解析路径字符串
        支持绝对路径、相对路径和~开头的路径

        Args:
            path_str: 路径字符串

        Returns:
            Path: 解析后的路径
        """
        path = Path(path_str)
        if path.is_absolute():
            return path

        # 相对路径相对于项目根目录
        return self._project_root / path

    def ensure_dir(self, directory: Path) -> Path:
        """
        确保目录存在,不存在则创建

        Args:
            directory: 目录路径

        Returns:
            Path: 目录路径
        """
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def __repr__(self) -> str:
        return f"AthenaPaths(project_root={self._project_root})"


# 全局单例实例
_global_paths: AthenaPaths | None = None


def get_paths(project_root: Path | None = None) -> AthenaPaths:
    """
    获取全局路径管理器实例

    Args:
        project_root: 项目根目录(仅首次调用有效)

    Returns:
        AthenaPaths: 路径管理器实例
    """
    global _global_paths
    if _global_paths is None:
        _global_paths = AthenaPaths(project_root)
    return _global_paths


def ensure_project_root_in_path(project_root: Path | None = None) -> str:
    """
    确保项目根目录在sys.path中(便捷函数)

    Args:
        project_root: 项目根目录

    Returns:
        str: 项目根目录字符串
    """
    paths = get_paths(project_root)
    return str(paths.project_root)


def get_project_root(project_root: Path | None = None) -> Path:
    """
    获取项目根目录(便捷函数)

    Args:
        project_root: 项目根目录

    Returns:
        Path: 项目根目录
    """
    paths = get_paths(project_root)
    return paths.project_root


# 导出
__all__ = [
    "AthenaPaths",
    "ensure_project_root_in_path",
    "get_paths",
    "get_project_root",
]
