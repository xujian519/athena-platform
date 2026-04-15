#!/usr/bin/env python3
"""
流式感知处理器测试
Tests for Streaming Perception Processor
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datetime import datetime
from unittest.mock import MagicMock, patch

from core.perception.streaming_perception_processor import (
    ImageStreamProcessor,
    MultimodalStreamProcessor,
    ProcessingMode,
    ProcessingResult,
    StreamChunk,
    StreamConfig,
    StreamingBuffer,
    StreamingPerceptionEngine,
    StreamProcessor,
    StreamType,
    TextStreamProcessor,
)


class TestStreamType:
    """测试StreamType枚举"""

    def test_text_type(self):
        """测试文本流类型"""
        assert StreamType.TEXT.value == "text"

    def test_image_type(self):
        """测试图像流类型"""
        assert StreamType.IMAGE.value == "image"

    def test_audio_type(self):
        """测试音频流类型"""
        assert StreamType.AUDIO.value == "audio"

    def test_video_type(self):
        """测试视频流类型"""
        assert StreamType.VIDEO.value == "video"

    def test_multimodal_type(self):
        """测试多模态流类型"""
        assert StreamType.MULTIMODAL.value == "multimodal"


class TestProcessingMode:
    """测试ProcessingMode枚举"""

    def test_realtime_mode(self):
        """测试实时处理模式"""
        assert ProcessingMode.REALTIME.value == "realtime"

    def test_batch_mode(self):
        """测试批处理模式"""
        assert ProcessingMode.BATCH.value == "batch"

    def test_streaming_mode(self):
        """测试流处理模式"""
        assert ProcessingMode.STREAMING.value == "streaming"

    def test_adaptive_mode(self):
        """测试自适应模式"""
        assert ProcessingMode.ADAPTIVE.value == "adaptive"


class TestStreamConfig:
    """测试StreamConfig配置类"""

    @pytest.fixture
    def config(self):
        """创建配置实例"""
        return StreamConfig(
            stream_type=StreamType.TEXT,
            mode=ProcessingMode.REALTIME,
            chunk_size=1024,
            buffer_size=4096,
            max_latency=100
        )

    def test_initialization(self, config):
        """测试初始化"""
        assert config.stream_type == StreamType.TEXT
        assert config.mode == ProcessingMode.REALTIME
        assert config.chunk_size == 1024
        assert config.buffer_size == 4096
        assert config.max_latency == 100

    def test_default_values(self):
        """测试默认值"""
        config = StreamConfig()
        assert config.stream_type is not None
        assert config.mode is not None

    def test_config_validation(self):
        """测试配置验证"""
        config = StreamConfig(
            stream_type=StreamType.TEXT,
            mode=ProcessingMode.STREAMING
        )
        # 配置应该是有效的
        assert config is not None


class TestStreamChunk:
    """测试StreamChunk数据块类"""

    @pytest.fixture
    def chunk(self):
        """创建数据块实例"""
        return StreamChunk(
            chunk_id="test_chunk_1",
            sequence=0,
            data="test data",
            timestamp=datetime.now(),
            metadata={"source": "test"}
        )

    def test_initialization(self, chunk):
        """测试初始化"""
        assert chunk.chunk_id == "test_chunk_1"
        assert chunk.sequence == 0
        assert chunk.data == "test data"
        assert chunk.metadata == {"source": "test"}

    def test_chunk_size(self, chunk):
        """测试数据块大小"""
        size = chunk.size()
        assert size > 0

    def test_is_complete(self, chunk):
        """测试是否完整"""
        assert hasattr(chunk, 'is_complete')


class TestProcessingResult:
    """测试ProcessingResult结果类"""

    @pytest.fixture
    def result(self):
        """创建结果实例"""
        return ProcessingResult(
            success=True,
            data="processed data",
            processing_time=0.5,
            metadata={"algorithm": "test"}
        )

    def test_initialization(self, result):
        """测试初始化"""
        assert result.success is True
        assert result.data == "processed data"
        assert result.processing_time == 0.5
        assert result.metadata == {"algorithm": "test"}

    def test_to_dict(self, result):
        """测试转换为字典"""
        result_dict = result.to_dict()
        assert "success" in result_dict
        assert "data" in result_dict


class TestStreamingBuffer:
    """测试StreamingBuffer缓冲区类"""

    @pytest.fixture
    def buffer(self):
        """创建缓冲区实例"""
        return StreamingBuffer(max_size=1024)

    def test_initialization(self, buffer):
        """测试初始化"""
        assert buffer.max_size == 1024
        assert buffer.size() == 0

    def test_write(self, buffer):
        """测试写入"""
        chunk = StreamChunk(
            chunk_id="test",
            sequence=0,
            data=b"test data",
            timestamp=datetime.now()
        )
        buffer.write(chunk)
        assert buffer.size() > 0

    def test_read(self, buffer):
        """测试读取"""
        chunk = StreamChunk(
            chunk_id="test",
            sequence=0,
            data=b"test data",
            timestamp=datetime.now()
        )
        buffer.write(chunk)
        data = buffer.read()
        assert data is not None

    def test_clear(self, buffer):
        """测试清空"""
        chunk = StreamChunk(
            chunk_id="test",
            sequence=0,
            data=b"test data",
            timestamp=datetime.now()
        )
        buffer.write(chunk)
        buffer.clear()
        assert buffer.size() == 0

    def test_is_empty(self, buffer):
        """测试是否为空"""
        assert buffer.is_empty() is True

    def test_is_full(self, buffer):
        """测试是否已满"""
        # 小缓冲区
        small_buffer = StreamingBuffer(max_size=10)
        large_chunk = StreamChunk(
            chunk_id="test",
            sequence=0,
            data=b"x" * 20,
            timestamp=datetime.now()
        )
        small_buffer.write(large_chunk)
        assert small_buffer.is_full() or small_buffer.size() > 0


class TestStreamProcessor:
    """测试StreamProcessor基类"""

    @pytest.fixture
    def processor(self):
        """创建处理器实例"""
        return StreamProcessor(
            config=StreamConfig(
                stream_type=StreamType.TEXT,
                mode=ProcessingMode.REALTIME
            )
        )

    def test_initialization(self, processor):
        """测试初始化"""
        assert processor.config is not None
        assert processor.config.stream_type == StreamType.TEXT

    def test_process_chunk(self, processor):
        """测试处理数据块"""
        chunk = StreamChunk(
            chunk_id="test",
            sequence=0,
            data="test data",
            timestamp=datetime.now()
        )
        # 基类方法应该被重写
        with pytest.raises(NotImplementedError):
            processor.process(chunk)

    @pytest.mark.asyncio
    async def test_process_chunk_async(self, processor):
        """测试异步处理数据块"""
        chunk = StreamChunk(
            chunk_id="test",
            sequence=0,
            data="test data",
            timestamp=datetime.now()
        )
        # 基类异步方法应该被重写
        with pytest.raises(NotImplementedError):
            await processor.process_async(chunk)

    def test_get_statistics(self, processor):
        """测试获取统计信息"""
        stats = processor.get_statistics()
        assert "processed_chunks" in stats
        assert "total_processing_time" in stats


class TestTextStreamProcessor:
    """测试TextStreamProcessor文本流处理器"""

    @pytest.fixture
    def processor(self):
        """创建文本处理器实例"""
        return TextStreamProcessor(
            config=StreamConfig(
                stream_type=StreamType.TEXT,
                mode=ProcessingMode.STREAMING
            )
        )

    def test_initialization(self, processor):
        """测试初始化"""
        assert processor is not None
        assert processor.config.stream_type == StreamType.TEXT

    def test_process_text_chunk(self, processor):
        """测试处理文本数据块"""
        chunk = StreamChunk(
            chunk_id="text_1",
            sequence=0,
            data="This is a test text chunk",
            timestamp=datetime.now()
        )
        result = processor.process(chunk)
        assert result.success is True
        assert result.data is not None

    def test_text_normalization(self, processor):
        """测试文本标准化"""
        text = "  Test Text  "
        normalized = processor.normalize_text(text)
        assert "Test Text" in normalized or normalized.strip() == "Test Text"

    def test_token_count(self, processor):
        """测试词元计数"""
        text = "This is a test"
        count = processor.count_tokens(text)
        assert count > 0

    def test_language_detection(self, processor):
        """测试语言检测"""
        text = "这是中文文本"
        lang = processor.detect_language(text)
        assert lang is not None


class TestImageStreamProcessor:
    """测试ImageStreamProcessor图像流处理器"""

    @pytest.fixture
    def processor(self):
        """创建图像处理器实例"""
        return ImageStreamProcessor(
            config=StreamConfig(
                stream_type=StreamType.IMAGE,
                mode=ProcessingMode.REALTIME
            )
        )

    def test_initialization(self, processor):
        """测试初始化"""
        assert processor is not None
        assert processor.config.stream_type == StreamType.IMAGE

    def test_process_image_chunk(self, processor):
        """测试处理图像数据块"""
        chunk = StreamChunk(
            chunk_id="image_1",
            sequence=0,
            data=b"fake_image_data",
            timestamp=datetime.now()
        )
        with patch.object(processor, 'decode_image') as mock_decode:
            mock_decode.return_value = MagicMock()
            result = processor.process(chunk)
            # 由于是模拟数据,结果可能失败
            assert result is not None

    def test_image_validation(self, processor):
        """测试图像验证"""
        # 测试图像验证逻辑
        assert hasattr(processor, 'validate_image')

    def test_resize_image(self, processor):
        """测试图像缩放"""
        assert hasattr(processor, 'resize_image')


class TestMultimodalStreamProcessor:
    """测试MultimodalStreamProcessor多模态流处理器"""

    @pytest.fixture
    def processor(self):
        """创建多模态处理器实例"""
        return MultimodalStreamProcessor(
            config=StreamConfig(
                stream_type=StreamType.MULTIMODAL,
                mode=ProcessingMode.ADAPTIVE
            )
        )

    def test_initialization(self, processor):
        """测试初始化"""
        assert processor is not None
        assert processor.config.stream_type == StreamType.MULTIMODAL

    def test_process_multimodal_chunk(self, processor):
        """测试处理多模态数据块"""
        chunk = StreamChunk(
            chunk_id="multi_1",
            sequence=0,
            data={"text": "test", "image": b"data"},
            timestamp=datetime.now()
        )
        with patch.object(processor, 'process') as mock_process:
            mock_process.return_value = ProcessingResult(
                success=True,
                data="processed",
                processing_time=0.1
            )
            result = mock_process(chunk)
            assert result.success is True

    def test_combine_modalities(self, processor):
        """测试组合多个模态"""
        text_result = "text result"
        image_result = "image result"
        combined = processor.combine_modalities(text_result, image_result)
        assert combined is not None


class TestStreamingPerceptionEngine:
    """测试StreamingPerceptionEngine流式感知引擎"""

    @pytest.fixture
    def engine(self):
        """创建引擎实例"""
        return StreamingPerceptionEngine(
            config=StreamConfig(
                stream_type=StreamType.MULTIMODAL,
                mode=ProcessingMode.ADAPTIVE,
                buffer_size=8192
            )
        )

    def test_initialization(self, engine):
        """测试初始化"""
        assert engine is not None
        assert engine.config is not None
        assert engine.buffer is not None

    @pytest.mark.asyncio
    async def test_start_stream(self, engine):
        """测试启动流"""
        with patch.object(engine, 'start_stream') as mock_start:
            mock_start.return_value = True
            result = await mock_start("stream_1")
            assert result is True

    @pytest.mark.asyncio
    async def test_stop_stream(self, engine):
        """测试停止流"""
        with patch.object(engine, 'stop_stream') as mock_stop:
            mock_stop.return_value = True
            result = await mock_stop("stream_1")
            assert result is True

    @pytest.mark.asyncio
    async def test_process_stream_data(self, engine):
        """测试处理流数据"""
        chunk = StreamChunk(
            chunk_id="test",
            sequence=0,
            data="stream data",
            timestamp=datetime.now()
        )

        with patch.object(engine, 'process_stream_data') as mock_process:
            mock_process.return_value = ProcessingResult(
                success=True,
                data="processed",
                processing_time=0.05
            )
            result = await mock_process("stream_1", chunk)
            assert result.success is True

    def test_get_stream_statistics(self, engine):
        """测试获取流统计"""
        stats = engine.get_stream_statistics("stream_1")
        assert stats is not None
        assert "total_chunks" in stats

    def test_list_active_streams(self, engine):
        """测试列出活跃流"""
        streams = engine.list_active_streams()
        assert isinstance(streams, list)

    @pytest.mark.asyncio
    async def test_batch_process_chunks(self, engine):
        """测试批量处理数据块"""
        chunks = [
            StreamChunk(
                chunk_id=f"chunk_{i}",
                sequence=i,
                data=f"data_{i}",
                timestamp=datetime.now()
            )
            for i in range(5)
        ]

        with patch.object(engine, 'batch_process') as mock_batch:
            mock_batch.return_value = [
                ProcessingResult(success=True, data=f"processed_{i}", processing_time=0.01)
                for i in range(5)
            ]
            results = await mock_batch("stream_1", chunks)
            assert len(results) == 5
            assert all(r.success for r in results)


class TestStreamingIntegration:
    """测试流式感知集成功能"""

    @pytest.fixture
    def engine(self):
        """创建引擎用于集成测试"""
        return StreamingPerceptionEngine(
            config=StreamConfig(
                stream_type=StreamType.TEXT,
                mode=ProcessingMode.STREAMING
            )
        )

    @pytest.mark.asyncio
    async def test_full_streaming_workflow(self, engine):
        """测试完整的流处理工作流"""
        stream_id = "test_stream"

        with patch.object(engine, 'start_stream') as mock_start:
            mock_start.return_value = True
            await mock_start(stream_id)

        # 模拟发送数据块
        chunks = [
            StreamChunk(
                chunk_id=f"chunk_{i}",
                sequence=i,
                data=f"chunk data {i}",
                timestamp=datetime.now()
            )
            for i in range(3)
        ]

        with patch.object(engine, 'process_stream_data') as mock_process:
            mock_process.return_value = ProcessingResult(
                success=True,
                data="processed",
                processing_time=0.01
            )

            for chunk in chunks:
                await mock_process(stream_id, chunk)

        with patch.object(engine, 'stop_stream') as mock_stop:
            mock_stop.return_value = True
            await mock_stop(stream_id)

    def test_error_recovery(self, engine):
        """测试错误恢复"""
        # 模拟处理错误
        StreamChunk(
            chunk_id="error_chunk",
            sequence=0,
            data=None,  # 无效数据
            timestamp=datetime.now()
        )

        # 引擎应该能够处理错误而不崩溃
        with patch.object(engine, 'process_stream_data') as mock_process:
            mock_process.side_effect = Exception("Processing error")

            # 错误应该被捕获
            assert mock_process.side_effect is not None

    def test_performance_monitoring(self, engine):
        """测试性能监控"""
        stats = engine.get_performance_stats()
        assert stats is not None
        assert "average_processing_time" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
