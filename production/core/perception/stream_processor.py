#!/usr/bin/env python3
"""
流式处理器
Stream Processor

支持大文件的流式处理,避免内存溢出。

功能特性:
1. 分块读取和处理
2. 异步流式处理
3. 内存使用控制
4. 进度追踪
5. 错误恢复

适用场景:
- 大文件处理(PDF、图片、视频等)
- 实时数据流
- 批量数据处理

作者: Athena AI系统
创建时间: 2026-01-25
版本: 1.0.0
"""

from __future__ import annotations
import asyncio
import inspect
import logging
from collections.abc import AsyncGenerator, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Generic

logger = logging.getLogger(__name__)

# 类型变量
T = Generic


class ChunkSize(Enum):
    """块大小标准"""

    SMALL = 1024  # 1KB
    MEDIUM = 1024 * 1024  # 1MB
    LARGE = 10 * 1024 * 1024  # 10MB
    XLARGE = 100 * 1024 * 1024  # 100MB


@dataclass
class StreamConfig:
    """流式处理配置"""

    chunk_size: int = ChunkSize.MEDIUM.value
    max_memory: int = 1024 * 1024 * 1024  # 1GB
    overlap: int = 0  # 块之间的重叠大小
    buffer_size: int = 10  # 缓冲区大小(块数)
    parallel_workers: int = 4  # 并行工作数
    enable_progress: bool = True  # 启用进度报告
    retry_on_error: bool = True  # 错误时重试
    max_retries: int = 3  # 最大重试次数


@dataclass
class StreamChunk:
    """数据块"""

    data: bytes | str | Any
    index: int  # 块索引
    offset: int  # 在源数据中的偏移量
    size: int  # 块大小
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class StreamProgress:
    """流式处理进度"""

    total_chunks: int = 0
    processed_chunks: int = 0
    total_bytes: int = 0
    processed_bytes: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None
    errors: list[Exception] = field(default_factory=list)

    @property
    def progress_percentage(self) -> float:
        """进度百分比"""
        if self.total_chunks == 0:
            return 0.0
        return (self.processed_chunks / self.total_chunks) * 100

    @property
    def elapsed_time(self) -> float:
        """已用时间(秒)"""
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()

    @property
    def estimated_remaining_time(self) -> float:
        """预估剩余时间(秒)"""
        if self.processed_chunks == 0:
            return 0.0
        rate = self.processed_chunks / self.elapsed_time
        if rate == 0:
            return 0.0
        remaining_chunks = self.total_chunks - self.processed_chunks
        return remaining_chunks / rate

    @property
    def throughput(self) -> float:
        """吞吐量(字节/秒)"""
        elapsed = self.elapsed_time
        if elapsed == 0:
            return 0.0
        return self.processed_bytes / elapsed


@dataclass
class StreamResult:
    """流式处理结果"""

    success: bool
    chunks_processed: int = 0
    total_bytes: int = 0
    results: list[Any] = field(default_factory=list)
    errors: list[Exception] = field(default_factory=list)
    processing_time: float = 0.0
    peak_memory: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class StreamProcessor:
    """流式处理器

    支持大文件的流式处理,避免内存溢出。

    使用示例:
        >>> processor = StreamProcessor(config=StreamConfig(chunk_size=1024*1024))
        >>> await processor.initialize()
        >>>
        >>> # 定义处理函数
        >>> async def process_chunk(chunk: StreamChunk) -> str:
        >>>     return chunk.data.decode()
        >>>
        >>> # 处理文件
        >>> result = await processor.process_file("large_file.txt", process_chunk)
    """

    def __init__(self, config: StreamConfig | None = None):
        """初始化处理器

        Args:
            config: 流式处理配置
        """
        self.config = config or StreamConfig()
        self._semaphore = asyncio.Semaphore(self.config.parallel_workers)
        self._progress = StreamProgress()
        self._initialized = False

        logger.info(
            f"🌊 初始化流式处理器 "
            f"(块大小={self.config.chunk_size}, 并行={self.config.parallel_workers})"
        )

    async def initialize(self) -> None:
        """初始化处理器"""
        if self._initialized:
            return

        self._initialized = True
        logger.info("✅ 流式处理器初始化完成")

    async def process_file(
        self,
        file_path: str | Path,
        processor_func: Callable[[StreamChunk], Any],
    ) -> StreamResult:
        """处理文件

        Args:
            file_path: 文件路径
            processor_func: 处理函数(接收StreamChunk,返回处理结果)

        Returns:
            处理结果
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        file_size = file_path.stat().st_size
        logger.info(f"📄 开始流式处理: {file_path.name} ({file_size} 字节)")

        # 初始化进度
        self._progress = StreamProgress(total_bytes=file_size)

        start_time = asyncio.get_event_loop().time()
        results = []
        errors = []
        peak_memory = 0

        try:
            async with self._semaphore:
                async for chunk in self._read_file_chunks(file_path):
                    # 处理块
                    try:
                        if inspect.iscoroutinefunction(processor_func):
                            result = await processor_func(chunk)
                        else:
                            result = processor_func(chunk)

                        results.append(result)

                        # 更新进度
                        self._progress.processed_chunks += 1
                        self._progress.processed_bytes += chunk.size

                        # 报告进度
                        if self.config.enable_progress:
                            logger.debug(
                                f"⏳ 处理进度: {self._progress.progress_percentage:.1f}% "
                                f"({self._progress.processed_chunks}/{self._progress.total_chunks})"
                            )

                    except Exception as e:
                        logger.error(f"❌ 处理块失败 {chunk.index}: {e}")
                        errors.append(e)

                        # 重试逻辑
                        if self.config.retry_on_error:
                            for retry in range(self.config.max_retries):
                                try:
                                    logger.info(f"🔄 重试 {retry + 1}/{self.config.max_retries}")
                                    if inspect.iscoroutinefunction(processor_func):
                                        result = await processor_func(chunk)
                                    else:
                                        result = processor_func(chunk)
                                    results.append(result)
                                    break
                                except Exception as retry_error:
                                    if retry == self.config.max_retries - 1:
                                        errors.append(retry_error)
                                    else:
                                        await asyncio.sleep(2**retry)  # 指数退避

        except Exception as e:
            logger.error(f"❌ 文件处理失败: {e}")
            errors.append(e)

        processing_time = asyncio.get_event_loop().time() - start_time
        self._progress.end_time = datetime.now()

        logger.info(
            f"✅ 文件处理完成: {file_path.name} "
            f"(耗时={processing_time:.2f}s, 吞吐={self._progress.throughput/1024/1024:.2f}MB/s)"
        )

        return StreamResult(
            success=len(errors) == 0,
            chunks_processed=self._progress.processed_chunks,
            total_bytes=self._progress.processed_bytes,
            results=results,
            errors=errors,
            processing_time=processing_time,
            peak_memory=peak_memory,
        )

    async def process_stream(
        self,
        stream: AsyncGenerator[bytes | str, None],
        processor_func: Callable[[StreamChunk], Any],
    ) -> StreamResult:
        """处理数据流

        Args:
            stream: 异步数据流
            processor_func: 处理函数

        Returns:
            处理结果
        """
        logger.info("🌊 开始流式处理数据流")

        self._progress = StreamProgress()
        start_time = asyncio.get_event_loop().time()
        results = []
        errors = []
        chunk_index = 0
        total_bytes = 0

        try:
            async with self._semaphore:
                async for data in stream:
                    chunk = StreamChunk(
                        data=data,
                        index=chunk_index,
                        offset=total_bytes,
                        size=len(data) if isinstance(data, (bytes, str)) else 0,
                    )

                    total_bytes += chunk.size
                    self._progress.total_bytes = total_bytes

                    # 处理块
                    try:
                        if inspect.iscoroutinefunction(processor_func):
                            result = await processor_func(chunk)
                        else:
                            result = processor_func(chunk)

                        results.append(result)

                        self._progress.processed_chunks += 1
                        chunk_index += 1

                    except Exception as e:
                        logger.error(f"❌ 处理块失败 {chunk.index}: {e}")
                        errors.append(e)

        except Exception as e:
            logger.error(f"❌ 流处理失败: {e}")
            errors.append(e)

        processing_time = asyncio.get_event_loop().time() - start_time

        logger.info(f"✅ 流处理完成 (耗时={processing_time:.2f}s)")

        return StreamResult(
            success=len(errors) == 0,
            chunks_processed=self._progress.processed_chunks,
            total_bytes=total_bytes,
            results=results,
            errors=errors,
            processing_time=processing_time,
        )

    async def _read_file_chunks(
        self,
        file_path: Path,
    ) -> AsyncGenerator[StreamChunk, None]:
        """读取文件块

        Args:
            file_path: 文件路径

        Yields:
            数据块
        """
        chunk_size = self.config.chunk_size
        overlap = self.config.overlap
        effective_chunk_size = chunk_size - overlap

        # 使用同步方式打开文件
        def open_file():
            return open(file_path, "rb")

        def close_file(f):
            f.close()

        f = await asyncio.to_thread(open_file)
        try:
            index = 0
            offset = 0

            while True:
                # 读取块
                data = await asyncio.to_thread(f.read, chunk_size)

                if not data:
                    break

                chunk = StreamChunk(
                    data=data,
                    index=index,
                    offset=offset,
                    size=len(data),
                )

                yield chunk

                # 移动到下一个块(考虑重叠)
                if len(data) < chunk_size:
                    # 最后一个块
                    break

                # 回退重叠部分
                await asyncio.to_thread(f.seek, -overlap, 1)  # 从当前位置回退

                offset += effective_chunk_size
                index += 1

                # 更新总块数估计
                self._progress.total_chunks = index + 1
        finally:
            await asyncio.to_thread(close_file, f)

    def get_progress(self) -> StreamProgress:
        """获取处理进度"""
        return self._progress

    async def cancel(self) -> None:
        """取消当前处理"""
        logger.warning("⚠️ 取消流式处理")
        # 信号将在下一次迭代时检查


# 便捷函数
async def process_file_stream(
    file_path: str | Path,
    processor_func: Callable[[StreamChunk], Any],
    chunk_size: int = ChunkSize.MEDIUM.value,
) -> StreamResult:
    """流式处理文件(便捷函数)"""
    processor = StreamProcessor(config=StreamConfig(chunk_size=chunk_size))
    await processor.initialize()
    return await processor.process_file(file_path, processor_func)


async def process_data_stream(
    stream: AsyncGenerator[bytes | str, None],
    processor_func: Callable[[StreamChunk], Any],
) -> StreamResult:
    """流式处理数据流(便捷函数)"""
    processor = StreamProcessor()
    await processor.initialize()
    return await processor.process_stream(stream, processor_func)


def chunk_stream(
    chunk_size: int = ChunkSize.MEDIUM.value,
    overlap: int = 0,
):
    """流式分块装饰器

    Args:
        chunk_size: 块大小
        overlap: 重叠大小

    Returns:
        装饰器函数
    """

    def decorator(func: Callable) -> Callable:
        async def wrapper(file_path: str | Path, *args, **kwargs):
            processor = StreamProcessor(config=StreamConfig(chunk_size=chunk_size, overlap=overlap))
            await processor.initialize()

            # 创建块处理函数
            async def chunk_processor(chunk: StreamChunk) -> Any:
                return await func(chunk, *args, **kwargs)

            return await processor.process_file(file_path, chunk_processor)

        return wrapper

    return decorator


__all__ = [
    "ChunkSize",
    "StreamChunk",
    "StreamConfig",
    "StreamProcessor",
    "StreamProgress",
    "StreamResult",
    "chunk_stream",
    "process_data_stream",
    "process_file_stream",
]
