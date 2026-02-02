#!/usr/bin/env python3
"""
异步文件操作工具
Async File Operations Utility

提供高效的异步文件读写操作,替代同步文件IO

作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class AsyncFileManager:
    """
    异步文件管理器

    提供异步文件读写、JSON操作等功能
    """

    def __init__(self, encoding: str = "utf-8"):
        """
        初始化文件管理器

        Args:
            encoding: 文件编码,默认utf-8
        """
        self.encoding = encoding

    async def read_text(self, file_path: str | Path) -> str:
        """
        异步读取文本文件

        Args:
            file_path: 文件路径

        Returns:
            文件内容字符串
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: Path(file_path).read_text(encoding=self.encoding)
        )

    async def write_text(self, file_path: str | Path, content: str, mkdir: bool = False) -> None:
        """
        异步写入文本文件

        Args:
            file_path: 文件路径
            content: 文件内容
            mkdir: 是否自动创建目录
        """

        async def _write():
            path = Path(file_path)
            if mkdir:
                path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding=self.encoding)

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _write)

    async def read_json(self, file_path: str | Path) -> dict[str, Any]:
        """
        异步读取JSON文件

        Args:
            file_path: 文件路径

        Returns:
            解析后的字典
        """
        content = await self.read_text(file_path)
        return json.loads(content)

    async def write_json(
        self,
        file_path: str | Path,
        data: dict[str, Any] | list[Any],
        indent: int = 2,
        ensure_ascii: bool = False,
        mkdir: bool = True,
        default: Any = str,
    ) -> None:
        """
        异步写入JSON文件

        Args:
            file_path: 文件路径
            data: 要写入的数据
            indent: JSON缩进
            ensure_ascii: 是否确保ASCII
            mkdir: 是否自动创建目录
            default: 默认序列化函数
        """
        content = json.dumps(data, indent=indent, ensure_ascii=ensure_ascii, default=default)
        await self.write_text(file_path, content, mkdir=mkdir)

    async def append_text(self, file_path: str | Path, content: str, mkdir: bool = False) -> None:
        """
        异步追加文本到文件

        Args:
            file_path: 文件路径
            content: 要追加的内容
            mkdir: 是否自动创建目录
        """

        async def _append():
            path = Path(file_path)
            if mkdir:
                path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "a", encoding=self.encoding) as f:
                f.write(content)

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _append)

    async def file_exists(self, file_path: str | Path) -> bool:
        """
        检查文件是否存在

        Args:
            file_path: 文件路径

        Returns:
            文件是否存在
        """
        path = Path(file_path)
        return path.exists()

    async def delete_file(self, file_path: str | Path) -> bool:
        """
        删除文件

        Args:
            file_path: 文件路径

        Returns:
            是否成功删除
        """
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                return True
            return False
        except Exception as e:
            return False

    async def list_files(self, directory: str | Path, pattern: str = "*") -> list[Path]:
        """
        列出目录中的文件

        Args:
            directory: 目录路径
            pattern: 文件匹配模式

        Returns:
            文件路径列表
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            return []
        return list(dir_path.glob(pattern))


# 全局单例
_file_manager: AsyncFileManager | None = None


def get_async_file_manager() -> AsyncFileManager:
    """获取全局文件管理器单例"""
    global _file_manager
    if _file_manager is None:
        _file_manager = AsyncFileManager()
    return _file_manager


# 便捷函数
async def async_read_json(file_path: str | Path) -> dict[str, Any]:
    """快捷函数:异步读取JSON文件"""
    manager = get_async_file_manager()
    return await manager.read_json(file_path)


async def async_write_json(
    file_path: str | Path, data: dict[str, Any] | list[Any], indent: int = 2
) -> None:
    """快捷函数:异步写入JSON文件"""
    manager = get_async_file_manager()
    await manager.write_json(file_path, data, indent=indent)
