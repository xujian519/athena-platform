#!/usr/bin/env python3
from __future__ import annotations
"""
系统管理器 - 模块加载器
System Manager - Module Loader

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-27
版本: 2.0.0
"""

import ast
import logging
import os
from pathlib import Path

from .types import DependencyType, ModuleMetadata

logger = logging.getLogger(__name__)


class ModuleLoader:
    """模块加载器

    负责扫描、加载和动态管理Python模块。
    """

    def __init__(self):
        """初始化模块加载器"""
        self.module_paths: list[Path] = []
        self.module_metadata: dict[str, ModuleMetadata] = {}
        self.file_timestamps: dict[str, float] = {}
        self.logger = logging.getLogger(__name__)

    def add_module_path(self, path: str | Path):
        """添加模块搜索路径

        Args:
            path: 模块路径
        """
        module_path = Path(path)
        if module_path.exists() and module_path not in self.module_paths:
            self.module_paths.append(module_path)
            self.logger.debug(f"模块路径已添加: {module_path}")

    def scan_modules(self, directory: Path | None = None) -> list[ModuleMetadata]:
        """扫描目录下的模块

        Args:
            directory: 扫描目录

        Returns:
            模块元数据列表
        """
        scan_dirs = [directory] if directory else self.module_paths
        modules: list[ModuleMetadata] = []

        for scan_dir in scan_dirs:
            if not scan_dir or not scan_dir.exists():
                continue

            for file_path in scan_dir.rglob("*.py"):
                # 跳过__init__和测试文件
                if file_path.name.startswith("__") or file_path.name.startswith("test_"):
                    continue

                try:
                    metadata = self._extract_metadata(file_path)
                    if metadata:
                        modules.append(metadata)
                        self.module_metadata[metadata.module_id] = metadata

                except Exception as e:
                    self.logger.warning(f"扫描模块失败 {file_path}: {e}")

        self.logger.info(f"扫描到 {len(modules)} 个模块")
        return modules

    def _extract_metadata(self, file_path: Path) -> ModuleMetadata | None:
        """从Python文件中提取模块元数据

        Args:
            file_path: 文件路径

        Returns:
            模块元数据
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source)

            # 提取元数据
            module_id = file_path.stem
            name = module_id.replace("_", " ").title()
            version = "1.0.0"
            description = ""
            class_name = "BaseModule"
            dependencies: dict[str, DependencyType] = {}
            provides: list[str] = []
            requires: list[str] = []

            # 扫描AST获取信息
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_name = node.name

                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            if target.id == "__version__":
                                if isinstance(node.value, ast.Constant):
                                    version = node.value.value
                            elif target.id == "__description__":
                                if isinstance(node.value, ast.Constant):
                                    description = node.value.value

                # 提取装饰器中的依赖信息
                if isinstance(node, ast.FunctionDef):
                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Call):
                            if hasattr(decorator.func, "id"):
                                if decorator.func.id == "requires":
                                    for arg in decorator.args:
                                        if isinstance(arg, ast.Constant):
                                            requires.append(arg.value)
                                elif decorator.func.id == "provides":
                                    for arg in decorator.args:
                                        if isinstance(arg, ast.Constant):
                                            provides.append(arg.value)

            # 记录文件时间戳
            self.file_timestamps[str(file_path)] = os.path.getmtime(file_path)

            return ModuleMetadata(
                module_id=module_id,
                name=name,
                version=version,
                description=description,
                file_path=str(file_path),
                class_name=class_name,
                dependencies=dependencies,
                provides=provides,
                requires=requires,
            )

        except Exception as e:
            self.logger.error(f"提取元数据失败 {file_path}: {e}")
            return None

    def check_file_changes(self, file_path: str | Path) -> bool:
        """检查文件是否已更改

        Args:
            file_path: 文件路径

        Returns:
            文件是否已更改
        """
        file_path_str = str(file_path)

        if not Path(file_path).exists():
            return False

        current_mtime = os.path.getmtime(file_path)
        last_mtime = self.file_timestamps.get(file_path_str, 0)

        if current_mtime > last_mtime:
            self.file_timestamps[file_path_str] = current_mtime
            return True

        return False

    def get_metadata(self, module_id: str) -> ModuleMetadata | None:
        """获取模块元数据

        Args:
            module_id: 模块ID

        Returns:
            模块元数据
        """
        return self.module_metadata.get(module_id)

    def list_modules(self) -> list[str]:
        """列出所有已扫描的模块

        Returns:
            模块ID列表
        """
        return list(self.module_metadata.keys())


__all__ = ["ModuleLoader"]
