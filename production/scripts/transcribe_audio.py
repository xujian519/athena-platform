#!/usr/bin/env python3
"""
音频转录脚本
使用OpenAI Whisper进行语音识别
作者: 小诺·双鱼公主
创建时间: 2025-01-07
"""

from __future__ import annotations
import datetime
import sys
from pathlib import Path

import whisper


def transcribe_audio(audio_path: str, model_size: str = "base") -> dict:
    """
    转录音频文件

    Args:
        audio_path: 音频文件路径
        model_size: 模型大小 (tiny, base, small, medium, large)

    Returns:
        包含转录文本和元数据的字典
    """

    print(f"🎵 开始转录音频: {audio_path}")
    print(f"📦 使用模型: {model_size}")
    print(f"⏰ 开始时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # 加载Whisper模型
        print("📥 正在加载Whisper模型...")
        model = whisper.load_model(model_size)

        # 转录音频
        print("🎧 正在转录音频...")
        result = model.transcribe(
            audio_path,
            language="zh",  # 中文
            task="transcribe",
            verbose=True
        )

        # 提取结果
        transcription = {
            "text": result["text"],
            "segments": result["segments"],
            "language": result["language"],
            "duration": result.get("duration", 0),
            "audio_path": audio_path,
            "model_size": model_size,
            "timestamp": datetime.datetime.now().isoformat()
        }

        print("✅ 转录完成！")
        print(f"📝 文本长度: {len(transcription['text'])} 字符")
        print(f"⏱️  音频时长: {transcription['duration']:.2f} 秒")
        print(f"🌍 识别语言: {transcription['language']}")

        return transcription

    except Exception as e:
        print(f"❌ 转录失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def save_transcription(transcription: dict, output_path: str) -> None:
    """
    保存转录结果

    Args:
        transcription: 转录结果字典
        output_path: 输出文件路径
    """
    try:
        # 保存纯文本
        txt_path = output_path.with_suffix(".txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(transcription["text"])
        print(f"💾 文本已保存: {txt_path}")

        # 保存详细JSON
        import json
        json_path = output_path.with_suffix(".json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(transcription, f, ensure_ascii=False, indent=2)
        print(f"💾 详细记录已保存: {json_path}")

        # 保存分段文本（带时间戳）
        segments_path = output_path.with_suffix(".segments.txt")
        with open(segments_path, "w", encoding="utf-8") as f:
            for segment in transcription["segments"]:
                start_time = segment["start"]
                end_time = segment["end"]
                text = segment["text"]
                f.write(f"[{start_time:.2f}s - {end_time:.2f}s] {text}\n")
        print(f"💾 分段文本已保存: {segments_path}")

    except Exception as e:
        print(f"❌ 保存失败: {str(e)}")


def main() -> None:
    """主函数"""
    # 音频文件路径
    audio_path = "/Users/xujian/工作/09_临时文件/刘晓燕/新录音 11.m4a"

    # 输出目录
    output_dir = Path("/Users/xujian/工作/09_临时文件/刘晓燕")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 生成输出文件名
    audio_name = Path(audio_path).stem
    output_path = output_dir / f"{audio_name}_转录"

    print("=" * 60)
    print("🎙️  刘晓燕录音转录工具")
    print("=" * 60)
    print()

    # 转录音频
    transcription = transcribe_audio(audio_path, model_size="base")

    if transcription:
        # 保存结果
        save_transcription(transcription, output_path)

        print()
        print("=" * 60)
        print("🎉 转录完成！")
        print("=" * 60)
        print()
        print("📄 转录文本预览:")
        print("-" * 60)
        print(transcription["text"][:500] + "..." if len(transcription["text"]) > 500 else transcription["text"])
        print("-" * 60)

        return 0
    else:
        print("❌ 转录失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
