#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Whisper集成到多模态系统
Test Whisper Integration with Multimodal System
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent.parent))

from ai.audio_processor_enhanced import get_audio_processor
from ai.ai_processor import AIProcessor, ProcessingType

async def test_whisper_integration():
    """测试Whisper集成"""
    print("🎤 测试Whisper语音识别集成")
    print("=" * 50)

    # 1. 初始化音频处理器
    print("\n1. 初始化Whisper音频处理器...")
    audio_proc = get_audio_processor()

    # 显示模型信息
    model_info = audio_proc.get_model_info()
    print("\n模型状态:")
    for key, value in model_info.items():
        print(f"  {key}: {value}")

    # 2. 创建测试音频文件（使用虚拟文件）
    print("\n2. 创建音频处理器任务...")
    ai_proc = AIProcessor()

    # 3. 测试转录功能（使用示例文件路径）
    print("\n3. 测试转录功能...")
    test_audio_path = "/tmp/test_audio.wav"  # 示例路径

    # 如果有真实音频文件，可以使用
    if len(sys.argv) > 1:
        test_audio_path = sys.argv[1]

        if os.path.exists(test_audio_path):
            print(f"使用音频文件: {test_audio_path}")
            result = await audio_proc.transcribe_with_timestamps(test_audio_path, "zh")

            if result["success"]:
                print("\n✅ 转录成功!")
                print(f"模型: {result.get('model')}")
                print(f"语言: {result.get('language')}")
                print(f"时长: {result.get('duration', 0):.2f}秒")
                print("\n转录文本:")
                print(result["text"])

                if "formatted_segments" in result:
                    print("\n时间戳分段:")
                    for segment in result["formatted_segments"]:
                        print(f"[{segment['start']}] {segment['text']}")
            else:
                print(f"❌ 转录失败: {result.get('error')}")
        else:
            print(f"❌ 音频文件不存在: {test_audio_path}")
    else:
        print("⚠️ 未提供音频文件，跳过实际转录测试")
        print("\n用法: python test_whisper_integration.py <音频文件路径>")

    # 4. 测试AI处理器集成
    print("\n4. 测试AI处理器集成...")
    try:
        # 提交音频处理任务
        if os.path.exists(test_audio_path):
            task_id = await ai_proc.submit_processing_task(
                file_id="test_audio_001",
                file_path=test_audio_path,
                processing_type=ProcessingType.CONTENT_EXTRACTION,
                options={"extract_text": True}
            )

            print(f"✅ AI处理任务已提交: {task_id}")

            # 等待处理完成
            await asyncio.sleep(3)

            # 获取处理结果
            result = await ai_proc.get_processing_result(task_id)
            if result:
                print(f"任务状态: {result.status.value}")
                if result.result:
                    print(f"处理结果: {result.result.get('extracted_text', '')[:100]}...")
        else:
            print("⚠️ 跳过AI处理器测试（需要音频文件）")

    except Exception as e:
        print(f"❌ AI处理器测试失败: {e}")

    # 5. 显示支持的格式
    print("\n5. 支持的音频格式:")
    for fmt in audio_proc.supported_formats:
        print(f"  - {fmt}")

    print("\n✅ Whisper集成测试完成!")

if __name__ == "__main__":
    asyncio.run(test_whisper_integration())