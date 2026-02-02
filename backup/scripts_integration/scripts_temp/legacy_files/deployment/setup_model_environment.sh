#!/bin/bash
# 设置本地模型环境变量
# Setup local model environment variables

# 导入环境变量文件
if [ -f "/Users/xujian/Athena工作平台/.env_models" ]; then
    export $(grep -v '^#' /Users/xujian/Athena工作平台/.env_models | xargs)
    echo "✅ 模型环境变量已加载"
else
    echo "❌ 找不到.env_models文件"
fi

# 创建模型缓存目录
mkdir -p /Users/xujian/Athena工作平台/models/.cache
mkdir -p /Users/xujian/Athena工作平台/models/hub

# 设置Python环境变量
export PYTHONPATH="/Users/xujian/Athena工作平台:$PYTHONPATH"

# 显示配置信息
echo ""
echo "📋 当前模型环境配置："
echo "----------------------------------------"
echo "SENTENCE_TRANSFORMERS_HOME: $SENTENCE_TRANSFORMERS_HOME"
echo "HF_HOME: $HF_HOME"
echo "HUGGINGFACE_HUB_CACHE: $HUGGINGFACE_HUB_CACHE"
echo "TRANSFORMERS_CACHE: $TRANSFORMERS_CACHE"
echo "BGE_LARGE_ZH_PATH: $BGE_LARGE_ZH_PATH"
echo "BGE_BASE_ZH_PATH: $BGE_BASE_ZH_PATH"
echo "FLAG_EMBEDDING_CACHE: $FLAG_EMBEDDING_CACHE"
echo "----------------------------------------"