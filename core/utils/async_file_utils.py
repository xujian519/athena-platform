#!/usr/bin/env python3
from __future__ import annotations
"""
异步文件操作工具 - Athena平台工具集
Async File Utilities - Athena Platform Toolkit

提供高性能异步文件操作功能

作者: Athena平台团队
创建时间: 2026-01-16
版本: 1.0.0
"""

import asyncio
import hashlib
import logging
from pathlib import Path

import aiofiles

logger = logging.getLogger(__name__)


class AsyncFileOperations:
    """异步文件操作工具类"""

    @staticmethod
    async def read_file(
        file_path: str | Path, mode: str = "rb", encoding: str = "utf-8"
    ) -> bytes | str:
        """
        异步读取文件

        Args:
            file_path: 文件路径
            mode: 读取模式 ('rb' 或 'r')
            encoding: 文本编码(仅当mode='r'时使用)

        Returns:
            文件内容(bytes或str)
        """
        path = Path(file_path) if isinstance(file_path, str) else file_path

        if "b" in mode:
            async with aiofiles.open(path, mode) as f:
                return await f.read()
        else:
            async with aiofiles.open(path, mode, encoding=encoding) as f:
                return await f.read()

    @staticmethod
    async def write_file(
        file_path: str | Path,
        content: bytes | str,
        mode: str = "wb",
        encoding: str = "utf-8",
    ) -> int:
        """
        异步写入文件

        Args:
            file_path: 文件路径
            content: 要写入的内容
            mode: 写入模式 ('wb' 或 'w')
            encoding: 文本编码(仅当mode='w'时使用)

        Returns:
            写入的字节数
        """
        path = Path(file_path) if isinstance(file_path, str) else file_path

        # 确保父目录存在
        path.parent.mkdir(parents=True, exist_ok=True)

        if "b" in mode:
            async with aiofiles.open(path, mode) as f:
                await f.write(content)
                return len(content)
        else:
            async with aiofiles.open(path, mode, encoding=encoding) as f:
                await f.write(content)
                return len(content.encode(encoding))

    @staticmethod
    async def read_chunks(file_path: str | Path, chunk_size: int = 8192) -> bytes:
        """
        分块异步读取文件

        Args:
            file_path: 文件路径
            chunk_size: 块大小

        Returns:
            完整文件内容
        """
        path = Path(file_path) if isinstance(file_path, str) else file_path

        chunks = []
        async with aiofiles.open(path, "rb") as f:
            while True:
                chunk = await f.read(chunk_size)
                if not chunk:
                    break
                chunks.append(chunk)

        return b"".join(chunks)

    @staticmethod
    async def write_chunks(file_path: str | Path, chunks: list[bytes]) -> int:
        """
        分块异步写入文件

        Args:
            file_path: 文件路径
            chunks: 数据块列表

        Returns:
            写入的总字节数
        """
        path = Path(file_path) if isinstance(file_path, str) else file_path

        path.parent.mkdir(parents=True, exist_ok=True)

        total_size = 0
        async with aiofiles.open(path, "wb") as f:
            for chunk in chunks:
                await f.write(chunk)
                total_size += len(chunk)

        return total_size

    @staticmethod
    async def append_file(
        file_path: str | Path, content: bytes | str, encoding: str = "utf-8"
    ) -> int:
        """
        异步追加到文件

        Args:
            file_path: 文件路径
            content: 要追加的内容
            encoding: 文本编码

        Returns:
            追加的字节数
        """
        path = Path(file_path) if isinstance(file_path, str) else file_path

        path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(content, str):
            async with aiofiles.open(path, "a", encoding=encoding) as f:
                await f.write(content)
                return len(content.encode(encoding))
        else:
            async with aiofiles.open(path, "ab") as f:
                await f.write(content)
                return len(content)

    @staticmethod
    async def copy_file(
        source: str | Path, destination: str | Path, chunk_size: int = 65536
    ) -> int:
        """
        异步复制文件

        Args:
            source: 源文件路径
            destination: 目标文件路径
            chunk_size: 复制块大小

        Returns:
            复制的字节数
        """
        src = Path(source) if isinstance(source, str) else source
        dst = Path(destination) if isinstance(destination, str) else destination

        dst.parent.mkdir(parents=True, exist_ok=True)

        total_size = 0
        async with aiofiles.open(src, "rb") as fsrc, aiofiles.open(dst, "wb") as fdst:
            while True:
                chunk = await fsrc.read(chunk_size)
                if not chunk:
                    break
                await fdst.write(chunk)
                total_size += len(chunk)

        return total_size

    @staticmethod
    async def move_file(source: str | Path, destination: str | Path) -> bool:
        """
        异步移动文件

        Args:
            source: 源文件路径
            destination: 目标文件路径

        Returns:
            是否成功移动
        """
        src = Path(source) if isinstance(source, str) else source
        dst = Path(destination) if isinstance(destination, str) else destination

        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            # 使用异步方式执行移动操作
            await asyncio.to_thread(src.rename, dst)
            return True
        except OSError as e:
            logger.error(f"移动文件失败: {e}")
            return False

    @staticmethod
    async def delete_file(file_path: str | Path) -> bool:
        """
        异步删除文件

        Args:
            file_path: 文件路径

        Returns:
            是否成功删除
        """
        path = Path(file_path) if isinstance(file_path, str) else file_path

        try:
            if path.exists():
                await asyncio.to_thread(path.unlink)
                return True
            return False
        except OSError as e:
            logger.error(f"删除文件失败: {e}")
            return False

    @staticmethod
    async def file_exists(file_path: str | Path) -> bool:
        """
        异步检查文件是否存在

        Args:
            file_path: 文件路径

        Returns:
            文件是否存在
        """
        path = Path(file_path) if isinstance(file_path, str) else file_path
        return await asyncio.to_thread(path.exists)

    @staticmethod
    async def get_file_size(file_path: str | Path) -> int:
        """
        异步获取文件大小

        Args:
            file_path: 文件路径

        Returns:
            文件大小(字节)
        """
        path = Path(file_path) if isinstance(file_path, str) else file_path

        if await asyncio.to_thread(path.exists):
            stat = await asyncio.to_thread(path.stat)
            return stat.st_size
        return 0

    @staticmethod
    async def calculate_hash(
        file_path: str | Path, algorithm: str = "md5", chunk_size: int = 8192
    ) -> str:
        """
        异步计算文件哈希值

        Args:
            file_path: 文件路径
            algorithm: 哈希算法 ('md5', 'sha1', 'sha256')
            chunk_size: 读取块大小

        Returns:
            十六进制哈希值
        """
        path = Path(file_path) if isinstance(file_path, str) else file_path

        hash_obj = hashlib.new(algorithm)

        async with aiofiles.open(path, "rb") as f:
            while True:
                chunk = await f.read(chunk_size)
                if not chunk:
                    break
                hash_obj.update(chunk)

        return hash_obj.hexdigest()

    @staticmethod
    async def list_files(
        directory: str | Path, pattern: str = "*", recursive: bool = False
    ) -> list[Path]:
        """
        异步列出目录中的文件

        Args:
            directory: 目录路径
            pattern: 文件匹配模式
            recursive: 是否递归搜索

        Returns:
            文件路径列表
        """
        dir_path = Path(directory) if isinstance(directory, str) else directory

        glob_method = dir_path.rglob if recursive else dir_path.glob

        # 在线程池中执行glob操作
        files = await asyncio.to_thread(list, glob_method(pattern))

        # 过滤出文件(不包括目录)
        return [f for f in files if await asyncio.to_thread(f.is_file)]

    @staticmethod
    async def create_directory(directory: str | Path) -> bool:
        """
        异步创建目录

        Args:
            directory: 目录路径

        Returns:
            是否成功创建
        """
        dir_path = Path(directory) if isinstance(directory, str) else directory

        try:
            await asyncio.to_thread(dir_path.mkdir, parents=True, exist_ok=True)
            return True
        except OSError as e:
            logger.error(f"创建目录失败: {e}")
            return False

    @staticmethod
    async def batch_read(
        file_paths: list[str | Path], concurrency: int = 10
    ) -> list[tuple[Path, bytes | str]]:
        """
        批量异步读取文件

        Args:
            file_paths: 文件路径列表
            concurrency: 并发数

        Returns:
            (文件路径, 内容)元组列表
        """
        semaphore = asyncio.Semaphore(concurrency)

        async def read_with_semaphore(file_path: str | Path) -> Optional[tuple[Path, bytes | str]]:
            async with semaphore:
                try:
                    path = Path(file_path) if isinstance(file_path, str) else file_path
                    content = await AsyncFileOperations.read_file(path)
                    return (path, content)
                except OSError as e:
                    logger.error(f"读取文件失败 {file_path}: {e}")
                    path = Path(file_path) if isinstance(file_path, str) else file_path
                    return (path, None)

        tasks = [read_with_semaphore(fp) for fp in file_paths]
        return await asyncio.gather(*tasks)

    @staticmethod
    async def batch_write(
        file_data: list[tuple[str | Path, bytes | str]], concurrency: int = 10
    ) -> list[tuple[Path, bool]]:
        """
        批量异步写入文件

        Args:
            file_data: (文件路径, 内容)元组列表
            concurrency: 并发数

        Returns:
            (文件路径, 是否成功)元组列表
        """
        semaphore = asyncio.Semaphore(concurrency)

        async def write_with_semaphore(
            file_path: str | Path, content: bytes | str
        ) -> tuple[Path, bool]:
            async with semaphore:
                try:
                    await AsyncFileOperations.write_file(file_path, content)
                    path = Path(file_path) if isinstance(file_path, str) else file_path
                    return (path, True)
                except OSError as e:
                    logger.error(f"写入文件失败 {file_path}: {e}")
                    path = Path(file_path) if isinstance(file_path, str) else file_path
                    return (path, False)

        tasks = [write_with_semaphore(fp, content) for fp, content in file_data]
        return await asyncio.gather(*tasks)


class AsyncFileProcessor:
    """异步文件处理器"""

    def __init__(self, chunk_size: int = 8192):
        """
        初始化文件处理器

        Args:
            chunk_size: 处理块大小
        """
        self.chunk_size = chunk_size

    async def process_file(
        self, file_path: str | Path, processor: callable, output_path: str | Path | None = None
    ) -> bytes | Optional[str]:
        """
        处理文件

        Args:
            file_path: 输入文件路径
            processor: 处理函数,接收内容返回处理后内容
            output_path: 输出文件路径(可选)

        Returns:
            处理后的内容
        """
        # 读取文件
        content = await AsyncFileOperations.read_file(file_path)

        # 处理内容
        processed = processor(content)

        # 写入输出文件(如果指定)
        if output_path:
            await AsyncFileOperations.write_file(output_path, processed)

        return processed

    async def batch_process(
        self,
        file_paths: list[str | Path],
        processor: callable,
        output_dir: str | Path | None = None,
        concurrency: int = 5,
    ) -> list[tuple[Path, bool]]:
        """
        批量处理文件

        Args:
            file_paths: 文件路径列表
            processor: 处理函数
            output_dir: 输出目录
            concurrency: 并发数

        Returns:
            (文件路径, 是否成功)元组列表
        """
        semaphore = asyncio.Semaphore(concurrency)

        async def process_with_semaphore(file_path: str | Path) -> tuple[Path, bool]:
            async with semaphore:
                try:
                    path = Path(file_path) if isinstance(file_path, str) else file_path

                    # 确定输出路径
                    output_path = None
                    if output_dir:
                        out_dir = Path(output_dir) if isinstance(output_dir, str) else output_dir
                        output_path = out_dir / path.name

                    # 处理文件
                    await self.process_file(path, processor, output_path)

                    return (path, True)

                except OSError as e:
                    logger.error(f"处理文件失败 {file_path}: {e}")
                    path = Path(file_path) if isinstance(file_path, str) else file_path
                    return (path, False)

        tasks = [process_with_semaphore(fp) for fp in file_paths]
        return await asyncio.gather(*tasks)


# 导出便捷函数
async def read_file(file_path: str | Path, mode: str = "rb") -> bytes | str:
    """便捷函数:异步读取文件"""
    return await AsyncFileOperations.read_file(file_path, mode)


async def write_file(file_path: str | Path, content: bytes | str) -> int:
    """便捷函数:异步写入文件"""
    return await AsyncFileOperations.write_file(file_path, content)


async def copy_file(source: str | Path, destination: str | Path) -> int:
    """便捷函数:异步复制文件"""
    return await AsyncFileOperations.copy_file(source, destination)


async def delete_file(file_path: str | Path) -> bool:
    """便捷函数:异步删除文件"""
    return await AsyncFileOperations.delete_file(file_path)


async def calculate_hash(file_path: str | Path, algorithm: str = "md5") -> str:
    """便捷函数:计算文件哈希"""
    return await AsyncFileOperations.calculate_hash(file_path, algorithm)
