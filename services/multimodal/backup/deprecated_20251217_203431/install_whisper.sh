#!/bin/bash
# -*- coding: utf-8 -*-
"""
安装Whisper语音识别
Install Whisper Speech Recognition
"""

echo "🎤 安装Whisper语音识别系统"
echo "============================"

cd "/Users/xujian/Athena工作平台"

# 激活虚拟环境
if [ -f "venv/bin/activate" ]; then
    echo "📦 激活Python虚拟环境..."
    source venv/bin/activate
else
    echo "❌ 未找到虚拟环境"
    exit 1
fi

# 1. 安装Whisper
echo ""
echo "1. 安装OpenAI Whisper..."
pip install openai-whisper

# 2. 安装音频处理依赖
echo ""
echo "2. 安装音频处理依赖..."
pip install librosa soundfile

# 3. 安装ffmpeg（系统依赖）
echo ""
echo "3. 检查ffmpeg..."
if command -v ffmpeg &> /dev/null; then
    echo "✅ ffmpeg已安装"
else
    echo "⚠️  ffmpeg未安装，正在安装..."
    if command -v brew &> /dev/null; then
        brew install ffmpeg
    else
        echo "请手动安装ffmpeg:"
        echo "  macOS: brew install ffmpeg"
        echo "  Ubuntu: sudo apt-get install ffmpeg"
        echo "  Windows: 下载ffmpeg并添加到PATH"
    fi
fi

# 4. 测试Whisper安装
echo ""
echo "4. 测试Whisper安装..."
python3 -c "
import whisper
import os

# 列出可用模型
models = ['tiny', 'base', 'small', 'medium', 'large']
print('可用的Whisper模型:')
for model in models:
    size = os.path.getsize(os.path.expanduser(f'~/.cache/whisper/{model}.pt')) if os.path.exists(os.path.expanduser(f'~/.cache/whisper/{model}.pt')) else '未下载'
    print(f'  - {model}: {size}')

# 测试加载base模型
print('\\n正在测试base模型加载...')
try:
    model = whisper.load_model('base')
    print('✅ Whisper安装成功！')
    print(f'模型尺寸: {model.dims.n_mel} x {model.dims.n_audio_ctx}')
except Exception as e:
    print(f'❌ Whisper测试失败: {e}')
"

echo ""
echo "✅ Whisper安装完成！"
echo ""
echo "使用方法:"
echo "  python services/multimodal/ai/audio_processor_enhanced.py <音频文件>"
echo ""
echo "支持的音频格式:"
echo "  - WAV (.wav)"
echo "  - MP3 (.mp3)"
echo "  - FLAC (.flac)"
echo "  - M4A (.m4a)"
echo "  - OGG (.ogg)"
echo "  - AMR (.amr)"
echo "  - AAC (.aac)"