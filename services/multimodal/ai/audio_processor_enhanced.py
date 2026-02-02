#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版音频处理器
Enhanced Audio Processor

集成Whisper语音识别
"""

import os
from core.async_main import async_main
import asyncio
import logging
from typing import Dict, List, Any, Optional
import numpy as np
import tempfile

# 尝试导入Whisper
try:
    import whisper
    WHISPER_AVAILABLE = True
    print("✅ Whisper已安装")
except ImportError:
    WHISPER_AVAILABLE = False
    print("⚠️ Whisper未安装，使用模拟转录")

# 导入音频处理库
try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    print("⚠️ librosa未安装")

logger = logging.getLogger(__name__)

class WhisperAudioProcessor:
    """Whisper音频处理器"""

    def __init__(self):
        """初始化处理器"""
        self.model = None
        self.model_name = "base"  # 可选: tiny, base, small, medium, large
        self.supported_formats = ['.wav', '.mp3', '.flac', '.m4a', '.ogg', '.amr', '.aac']

        # 初始化Whisper模型
        if WHISPER_AVAILABLE:
            self._load_whisper_model()

    def _load_whisper_model(self) -> Any:
        """加载Whisper模型"""
        try:
            print(f"正在加载Whisper模型: {self.model_name}")
            self.model = whisper.load_model(self.model_name)
            print(f"✅ Whisper模型加载成功: {self.model_name}")
        except Exception as e:
            print(f"❌ Whisper模型加载失败: {e}")
            self.model = None

    async def transcribe_audio(self, audio_path: str, language: str = "zh") -> Dict[str, Any]:
        """转录音频文件"""
        try:
            print(f"开始转录音频: {audio_path}")

            if WHISPER_AVAILABLE and self.model:
                # 使用Whisper进行转录
                result = await self._transcribe_with_whisper(audio_path, language)
            else:
                # 使用模拟转录
                result = await self._simulate_transcription(audio_path)

            return result

        except Exception as e:
            logger.error(f"音频转录失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "language": language
            }

    async def _transcribe_with_whisper(self, audio_path: str, language: str) -> Dict[str, Any]:
        """使用Whisper转录"""
        try:
            # 异步执行Whisper转录
            loop = asyncio.get_event_loop()

            def run_whisper() -> Any:
                result = self.model.transcribe(
                    audio_path,
                    language=language,
                    task="transcribe",
                    verbose=False
                )
                return result

            # 在线程池中运行Whisper（避免阻塞）
            result = await loop.run_in_executor(None, run_whisper)

            # 提取分段信息
            segments = []
            for segment in result.get("segments", []):
                segments.append({
                    "start": segment["start"],
                    "end": segment["end"],
                    "text": segment["text"].strip(),
                    "confidence": segment.get("avg_logprob", 0.0)
                })

            return {
                "success": True,
                "text": result["text"],
                "language": result["language"],
                "segments": segments,
                "model": self.model_name,
                "duration": result.get("duration", 0)
            }

        except Exception as e:
            logger.error(f"Whisper转录失败: {e}")
            raise

    async def _simulate_transcription(self, audio_path: str) -> Dict[str, Any]:
        """模拟转录（当Whisper不可用时）"""
        try:
            # 使用librosa获取音频信息
            if LIBROSA_AVAILABLE:
                audio_data, sample_rate = librosa.load(audio_path)
                duration = len(audio_data) / sample_rate
            else:
                duration = 0

            # 生成模拟转录文本
            filename = os.path.basename(audio_path)
            simulated_text = f"[模拟转录] 这是从{filename}中识别出的语音内容。音频时长约{duration:.1f}秒。"

            return {
                "success": True,
                "text": simulated_text,
                "language": "zh",
                "segments": [{
                    "start": 0,
                    "end": duration,
                    "text": simulated_text,
                    "confidence": 0.5
                }],
                "model": "simulation",
                "duration": duration
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "language": "unknown"
            }

    async def transcribe_with_timestamps(self, audio_path: str, language: str = "zh") -> Dict[str, Any]:
        """带时间戳的转录"""
        result = await self.transcribe_audio(audio_path, language)

        if result["success"] and "segments" in result:
            # 添加格式化的时间戳
            formatted_segments = []
            for segment in result["segments"]:
                start_time = self._format_timestamp(segment["start"])
                end_time = self._format_timestamp(segment["end"])
                formatted_segments.append({
                    "start": start_time,
                    "end": end_time,
                    "text": segment["text"]
                })

            result["formatted_segments"] = formatted_segments

        return result

    def _format_timestamp(self, seconds: float) -> str:
        """格式化时间戳"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)

        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"

    def change_model(self, model_name: str) -> Any:
        """更换Whisper模型"""
        if model_name not in ["tiny", "base", "small", "medium", "large"]:
            raise ValueError(f"不支持的模型: {model_name}")

        self.model_name = model_name
        if WHISPER_AVAILABLE:
            self._load_whisper_model()
            return True
        return False

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "whisper_available": WHISPER_AVAILABLE,
            "current_model": self.model_name if self.model else None,
            "librosa_available": LIBROSA_AVAILABLE,
            "supported_formats": self.supported_formats
        }

# 全局实例
audio_processor = None

def get_audio_processor() -> WhisperAudioProcessor:
    """获取音频处理器实例"""
    global audio_processor
    if audio_processor is None:
        audio_processor = WhisperAudioProcessor()
    return audio_processor

# 测试函数
async def test_audio_transcription(audio_file_path: str):
    """测试音频转录"""
    processor = get_audio_processor()

    print("=== 音频转录测试 ===")
    print(f"音频文件: {audio_file_path}")
    print()

    # 显示模型信息
    model_info = processor.get_model_info()
    print("模型信息:")
    for key, value in model_info.items():
        print(f"  {key}: {value}")
    print()

    # 执行转录
    result = await processor.transcribe_with_timestamps(audio_file_path, "zh")

    print("转录结果:")
    if result["success"]:
        print(f"✅ 转录成功")
        print(f"模型: {result.get('model', 'unknown')}")
        print(f"语言: {result.get('language', 'unknown')}")
        print(f"时长: {result.get('duration', 0):.2f}秒")
        print()
        print("完整文本:")
        print(result["text"])
        print()
        print("带时间戳分段:")
        for segment in result.get("formatted_segments", []):
            print(f"[{segment['start']} --> {segment['end']}] {segment['text']}")
    else:
        print(f"❌ 转录失败: {result.get('error', 'unknown error')}")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        audio_file = sys.argv[1]
        if os.path.exists(audio_file):
            asyncio.run(test_audio_transcription(audio_file))
        else:
            print(f"错误: 文件不存在 - {audio_file}")
    else:
        print("用法: python audio_processor_enhanced.py <音频文件路径>")
        print("支持格式: " + ", ".join(get_audio_processor().supported_formats))