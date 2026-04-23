"""
file_operator工具包装器

包装tool_implementations.py中的file_operator_handler，提供符合统一工具接口的封装。
"""

import logging
from typing import Any

from core.tools.tool_implementations import file_operator_handler

logger = logging.getLogger(__name__)


class FileOperatorWrapper:
    """
    文件操作工具包装器

    提供统一的文件操作接口，包括：
    - 读取文件
    - 写入文件
    - 列出目录
    - 搜索文件
    """

    def __init__(self):
        """初始化文件操作包装器"""
        self.handler = file_operator_handler

    async def read_file(self, path: str) -> dict[str, Any]:
        """
        读取文件内容

        Args:
            path: 文件路径

        Returns:
            操作结果字典:
            {
                "success": bool,  # 是否成功
                "message": str,   # 消息
                "data": {
                    "content": str,  # 文件内容
                    "size": int,     # 文件大小
                    "lines": int     # 行数
                }
            }
        """
        params = {"action": "read", "path": path}
        return await self.handler(params, {})

    async def write_file(self, path: str, content: str) -> dict[str, Any]:
        """
        写入文件内容

        Args:
            path: 文件路径
            content: 文件内容

        Returns:
            操作结果字典:
            {
                "success": bool,  # 是否成功
                "message": str,   # 消息
                "data": {
                    "size": int  # 写入大小
                }
            }
        """
        params = {"action": "write", "path": path, "content": content}
        return await self.handler(params, {})

    async def list_directory(self, path: str) -> dict[str, Any]:
        """
        列出目录内容

        Args:
            path: 目录路径

        Returns:
            操作结果字典:
            {
                "success": bool,  # 是否成功
                "message": str,   # 消息
                "items": [        # 项目列表
                    {
                        "name": str,   # 名称
                        "type": str,   # 类型 (file/directory)
                        "size": int    # 大小
                    }
                ]
            }
        """
        params = {"action": "list", "path": path}
        return await self.handler(params, {})

    async def search_files(self, path: str, pattern: str) -> dict[str, Any]:
        """
        搜索文件

        Args:
            path: 搜索路径
            pattern: 搜索模式 (支持通配符，如 *.txt)

        Returns:
            操作结果字典:
            {
                "success": bool,  # 是否成功
                "message": str,   # 消息
                "data": {
                    "matches": list[str],  # 匹配的文件列表
                    "count": int           # 匹配数量
                }
            }
        """
        params = {"action": "search", "path": path, "pattern": pattern}
        return await self.handler(params, {})

    async def execute(self, action: str, **kwargs) -> dict[str, Any]:
        """
        通用执行方法

        Args:
            action: 操作类型 (read/write/list/search)
            **kwargs: 其他参数

        Returns:
            操作结果字典
        """
        params = {"action": action, **kwargs}
        return await self.handler(params, {})

    def get_metadata(self) -> dict[str, Any]:
        """
        获取工具元数据

        Returns:
            工具元数据字典
        """
        return {
            "name": "file_operator",
            "version": "1.0.0",
            "description": "文件操作工具 - 读取、写入、列出目录、搜索文件",
            "category": "filesystem",
            "author": "Athena Platform",
            "actions": {
                "read": "读取文件内容",
                "write": "写入文件内容",
                "list": "列出目录内容",
                "search": "搜索文件",
            },
            "capabilities": [
                "读取文本文件",
                "写入文本文件",
                "列出目录内容",
                "搜索文件（支持通配符）",
                "自动创建父目录",
                "UTF-8编码支持",
            ],
            "limitations": [
                "仅支持文本文件",
                "固定UTF-8编码",
                "搜索结果限制20条",
            ],
        }


# 创建全局实例
_file_operator_instance = None


def get_file_operator() -> FileOperatorWrapper:
    """
    获取文件操作包装器实例（单例模式）

    Returns:
        FileOperatorWrapper实例
    """
    global _file_operator_instance
    if _file_operator_instance is None:
        _file_operator_instance = FileOperatorWrapper()
    return _file_operator_instance


# 导出便捷函数
async def read_file(path: str) -> dict[str, Any]:
    """便捷函数：读取文件"""
    return await get_file_operator().read_file(path)


async def write_file(path: str, content: str) -> dict[str, Any]:
    """便捷函数：写入文件"""
    return await get_file_operator().write_file(path, content)


async def list_directory(path: str) -> dict[str, Any]:
    """便捷函数：列出目录"""
    return await get_file_operator().list_directory(path)


async def search_files(path: str, pattern: str) -> dict[str, Any]:
    """便捷函数：搜索文件"""
    return await get_file_operator().search_files(path, pattern)
