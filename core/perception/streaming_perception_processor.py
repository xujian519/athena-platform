"""
流式感知处理器
支持实时流式数据处理,优化M4芯片性能
"""

import asyncio
import logging
import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# Apple Silicon优化
try:
    import torch

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

logger = logging.getLogger(__name__)


class StreamType(Enum):
    """流类型"""

    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    MULTIMODAL = "multimodal"


class ProcessingMode(Enum):
    """处理模式"""

    REALTIME = "realtime"  # 实时处理
    BATCH = "batch"  # 批处理
    ADAPTIVE = "adaptive"  # 自适应
    PIPELINE = "pipeline"  # 流水线


@dataclass
class StreamConfig:
    """流配置"""

    chunk_size: int = 1024
    buffer_size: int = 8192
    processing_mode: ProcessingMode = ProcessingMode.ADAPTIVE
    overlap_ratio: float = 0.1  # 重叠比例
    enable_gpu_acceleration: bool = True
    batch_timeout: float = 0.1  # 批处理超时
    max_queue_size: int = 100
    enable_backpressure: bool = True


@dataclass
class StreamChunk:
    """流数据块"""

    chunk_id: str
    data: Any
    timestamp: float
    metadata: dict[str, Any] = field(default_factory=dict)
    sequence_number: int = 0
    is_final: bool = False


@dataclass
class ProcessingResult:
    """处理结果"""

    chunk_id: str
    result: Any
    confidence: float = 0.0
    processing_time: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class StreamingBuffer:
    """流缓冲区"""

    def __init__(self, max_size: int = 8192):
        self.buffer = deque(maxlen=max_size)
        self.metadata = {}
        self.total_size = 0

    def put(self, chunk: StreamChunk) -> bool:
        """添加数据块"""
        if len(self.buffer) >= self.buffer.maxlen:
            return False

        self.buffer.append(chunk)
        self.total_size += len(str(chunk.data)) if hasattr(chunk.data, "__len__") else 1
        return True

    def get_batch(self, batch_size: int | None = None) -> list[StreamChunk]:
        """获取批次数据"""
        if batch_size is None:
            batch_size = len(self.buffer)

        batch = []
        for _ in range(min(batch_size, len(self.buffer))):
            if self.buffer:
                batch.append(self.buffer.popleft())

        return batch

    def size(self) -> int:
        """获取缓冲区大小"""
        return len(self.buffer)


class StreamProcessor:
    """流处理器基类"""

    def __init__(self, name: str, config: StreamConfig):
        self.name = name
        self.config = config
        self.is_running = False
        self.stats = {
            "processed_chunks": 0,
            "total_processing_time": 0.0,
            "avg_processing_time": 0.0,
            "buffer_overflows": 0,
        }

    async def initialize(self):
        """初始化处理器"""
        logger.info(f"初始化流处理器: {self.name}")
        self.is_running = True

    async def process_chunk(self, chunk: StreamChunk) -> ProcessingResult:
        """处理单个数据块"""
        start_time = time.time()

        # 子类实现具体处理逻辑
        result_data = await self._process_impl(chunk)

        processing_time = time.time() - start_time
        self._update_stats(processing_time)

        return ProcessingResult(
            chunk_id=chunk.chunk_id, result=result_data, processing_time=processing_time
        )

    async def _process_impl(self, chunk: StreamChunk) -> Any:
        """处理实现(子类重写)"""
        raise NotImplementedError

    def _update_stats(self, processing_time: float) -> Any:
        """更新统计信息"""
        self.stats["processed_chunks"] += 1
        self.stats["total_processing_time"] += processing_time

        total = self.stats["processed_chunks"]
        if total > 0:
            self.stats["avg_processing_time"] = self.stats["total_processing_time"] / total

    async def cleanup(self):
        """清理资源"""
        logger.info(f"清理流处理器: {self.name}")
        self.is_running = False


class TextStreamProcessor(StreamProcessor):
    """文本流处理器"""

    def __init__(self, config: StreamConfig):
        super().__init__("text_stream", config)
        self.text_buffer = ""
        self.sentence_boundary = [". ", "! ", "? ", "\n"]

    async def _process_impl(self, chunk: StreamChunk) -> dict[str, Any]:
        """处理文本流"""
        text_data = chunk.data
        self.text_buffer += text_data

        # 查找完整句子
        sentences = []
        last_pos = 0

        for boundary in self.sentence_boundary:
            pos = self.text_buffer.rfind(boundary)
            if pos > last_pos:
                sentence = self.text_buffer[: pos + 1]
                sentences.append(sentence.strip())
                self.text_buffer = self.text_buffer[pos + 1 :]
                break

        return {
            "sentences": sentences,
            "remaining_text": self.text_buffer,
            "char_count": len(text_data),
        }


class ImageStreamProcessor(StreamProcessor):
    """图像流处理器"""

    def __init__(self, config: StreamConfig):
        super().__init__("image_stream", config)
        self.frame_buffer = deque(maxlen=config.buffer_size)
        self.preprocessing_pipeline = self._create_pipeline()

    def _create_pipeline(self) -> list[Callable]:
        """创建预处理管道"""
        pipeline = []

        if TORCH_AVAILABLE and self.config.enable_gpu_acceleration:
            # 添加GPU加速的图像处理
            pipeline.append(self._gpu_preprocess)
        else:
            pipeline.append(self._cpu_preprocess)

        return pipeline

    async def _gpu_preprocess(self, image_data) -> Any:
        """GPU图像预处理"""
        # 实现GPU加速的图像处理
        if hasattr(image_data, "shape"):
            return torch.from_numpy(image_data).to("mps")
        return image_data

    async def _cpu_preprocess(self, image_data) -> Any:
        """CPU图像预处理"""
        # 实现CPU图像处理
        return image_data

    async def _process_impl(self, chunk: StreamChunk) -> dict[str, Any]:
        """处理图像流"""
        frame = chunk.data

        # 预处理
        for processor in self.preprocessing_pipeline:
            frame = await processor(frame)

        # 添加到缓冲区
        self.frame_buffer.append(frame)

        return {
            "frame_processed": True,
            "frame_id": chunk.chunk_id,
            "buffer_size": len(self.frame_buffer),
        }


class MultimodalStreamProcessor(StreamProcessor):
    """多模态流处理器"""

    def __init__(self, config: StreamConfig):
        super().__init__("multimodal_stream", config)
        self.processors = {}
        self.sync_buffer = {}

    async def initialize(self):
        """初始化多模态处理器"""
        await super().initialize()

        # 初始化子处理器
        self.processors[StreamType.TEXT] = TextStreamProcessor(self.config)
        self.processors[StreamType.IMAGE] = ImageStreamProcessor(self.config)

        for processor in self.processors.values():
            await processor.initialize()

    async def _process_impl(self, chunk: StreamChunk) -> dict[str, Any]:
        """处理多模态流"""
        stream_type = chunk.metadata.get("stream_type", "text")

        if stream_type not in self.processors:
            logger.warning(f"不支持的流类型: {stream_type}")
            return {"error": f"Unsupported stream type: {stream_type}"}

        processor = self.processors[stream_type]
        result = await processor.process_chunk(chunk)

        return {"stream_type": stream_type, "processed_result": result, "timestamp": time.time()}

    async def cleanup(self):
        """清理多模态处理器"""
        for processor in self.processors.values():
            await processor.cleanup()
        await super().cleanup()


class StreamingPerceptionEngine:
    """流式感知引擎"""

    def __init__(self, config: StreamConfig | None = None):
        self.config = config or StreamConfig()
        self.processors = {}
        self.buffers = {}
        self.task_queue = asyncio.Queue(maxsize=self.config.max_queue_size)
        self.result_queue = asyncio.Queue()
        self.is_running = False
        self.backpressure_enabled = self.config.enable_backpressure
        self.performance_stats = defaultdict(list)
        self.stats: dict[str, int] = {}  # 流ID到序列号的映射

    async def initialize(self):
        """初始化流式感知引擎"""
        logger.info("🚀 初始化流式感知引擎")

        # 创建处理器
        self.processors[StreamType.TEXT] = TextStreamProcessor(self.config)
        self.processors[StreamType.IMAGE] = ImageStreamProcessor(self.config)
        self.processors[StreamType.MULTIMODAL] = MultimodalStreamProcessor(self.config)

        # 初始化所有处理器
        for processor in self.processors.values():
            await processor.initialize()

        self.is_running = True
        logger.info("✅ 流式感知引擎初始化完成")

    async def start_streaming(self, stream_id: str, stream_type: StreamType) -> str:
        """启动数据流"""
        _stream_info = {
            "stream_id": stream_id,
            "stream_type": stream_type,
            "started_at": time.time(),
            "chunk_count": 0,
        }

        # 创建流专用缓冲区
        self.buffers[stream_id] = StreamingBuffer(max_size=self.config.buffer_size)

        logger.info(f"启动流: {stream_id} ({stream_type.value})")
        return stream_id

    async def put_chunk(
        self, stream_id: str, data: Any, metadata: dict[str, Any] | None = None
    ) -> bool:
        """添加数据块到流"""
        if not self.is_running:
            return False

        # 检查背压
        if self.backpressure_enabled and self.task_queue.qsize() >= self.task_queue.maxsize:
            logger.warning(f"队列已满,丢弃数据块: {stream_id}")
            return False

        # 创建数据块
        chunk = StreamChunk(
            chunk_id=f"{stream_id}_{time.time()}",
            data=data,
            timestamp=time.time(),
            metadata=metadata or {},
            sequence_number=self._get_next_sequence(stream_id),
        )

        # 添加到缓冲区
        buffer = self.buffers.get(stream_id)
        if buffer and not buffer.put(chunk):
            logger.warning(f"缓冲区溢出: {stream_id}")
            return False

        # 添加到任务队列
        await self.task_queue.put((stream_id, chunk))
        return True

    async def end_stream(self, stream_id: str):
        """结束数据流"""
        # 添加结束标记
        end_chunk = StreamChunk(
            chunk_id=f"{stream_id}_end", data=None, timestamp=time.time(), is_final=True
        )

        await self.task_queue.put((stream_id, end_chunk))
        logger.info(f"结束流: {stream_id}")

    async def processing_worker(self):
        """处理工作线程"""
        logger.info("启动流处理工作线程")

        while self.is_running:
            try:
                # 获取任务(带超时)
                stream_id, chunk = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)

                # 选择处理器
                processor = self._get_processor(chunk, stream_id)
                if not processor:
                    continue

                # 处理数据块
                result = await processor.process_chunk(chunk)

                # 添加结果
                await self.result_queue.put((stream_id, result))

                # 记录性能
                self._record_performance(stream_id, result.processing_time)

            except TimeoutError:
                continue
            except Exception as e:
                logger.error(f"处理错误: {e}")

    def _get_processor(self, chunk: StreamChunk, stream_id: str) -> StreamProcessor | None:
        """获取处理器"""
        stream_type = chunk.metadata.get("stream_type")
        if stream_type:
            return self.processors.get(stream_type)
        return self.processors.get(StreamType.MULTIMODAL)

    def _get_next_sequence(self, stream_id: str) -> int:
        """获取下一个序列号"""
        if stream_id not in self.stats:
            self.stats[stream_id] = 0
        self.stats[stream_id] += 1
        return self.stats[stream_id]

    def _record_performance(self, stream_id: str, processing_time: float) -> Any:
        """记录性能数据"""
        self.performance_stats[stream_id].append(
            {"timestamp": time.time(), "processing_time": processing_time}
        )

        # 保留最近100个数据点
        if len(self.performance_stats[stream_id]) > 100:
            self.performance_stats[stream_id] = self.performance_stats[stream_id][-100:]

    async def get_results(self, timeout: float | None = None) -> list[tuple[str, ProcessingResult]]:
        """获取处理结果"""
        results = []

        try:
            while True:
                stream_id, result = await asyncio.wait_for(
                    self.result_queue.get(), timeout=timeout or 0.1
                )
                results.append((stream_id, result))
        except TimeoutError:
            logger.warning(f"连接或超时错误: {e}")

        return results

    def get_stream_stats(self, stream_id: str | None = None) -> dict[str, Any]:
        """获取流统计信息"""
        if stream_id:
            buffer = self.buffers.get(stream_id)
            return {
                "stream_id": stream_id,
                "buffer_size": buffer.size() if buffer else 0,
                "performance_data": self.performance_stats.get(stream_id, []),
            }
        else:
            return {
                "total_streams": len(self.buffers),
                "queue_size": self.task_queue.qsize(),
                "is_running": self.is_running,
                "processor_stats": {
                    name: processor.stats for name, processor in self.processors.items()
                },
            }

    async def cleanup(self):
        """清理资源"""
        logger.info("清理流式感知引擎")

        self.is_running = False

        # 清理处理器
        for processor in self.processors.values():
            await processor.cleanup()

        # 清空队列
        while not self.task_queue.empty():
            self.task_queue.get_nowait()

        while not self.result_queue.empty():
            self.result_queue.get_nowait()

        logger.info("✅ 流式感知引擎已清理")


# 全局流式感知引擎实例
streaming_perception_engine = StreamingPerceptionEngine()


# 便捷函数
async def initialize_streaming_perception():
    """初始化流式感知"""
    await streaming_perception_engine.initialize()


async def start_text_stream(stream_id: str):
    """启动文本流"""
    return await streaming_perception_engine.start_streaming(stream_id, StreamType.TEXT)


async def start_image_stream(stream_id: str):
    """启动图像流"""
    return await streaming_perception_engine.start_streaming(stream_id, StreamType.IMAGE)


async def stream_text_data(stream_id: str, text: str):
    """流式添加文本数据"""
    return await streaming_perception_engine.put_chunk(stream_id, text, {"stream_type": "text"})


async def get_stream_results(timeout: float = 1.0):
    """获取流处理结果"""
    return await streaming_perception_engine.get_results(timeout)
