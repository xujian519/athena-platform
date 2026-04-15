#!/bin/bash
# 启动小娜 NLP增强版
# Xiaona with NLP Integration Startup Script

# 设置基础目录
BASE_DIR="/Users/xujian/Athena工作平台"
cd "$BASE_DIR" || exit 1

# 加载环境变量
export ENV_FILE="$BASE_DIR/.env.production.unified"
if [ -f "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE"
    set +a
    echo "✅ 环境变量已加载: $ENV_FILE"
else
    echo "⚠️  环境变量文件未找到: $ENV_FILE"
fi

# 检查NLP服务
echo ""
echo "📡 检查NLP服务状态..."
NLP_STATUS=$(curl -s http://localhost:8001/health | jq -r '.status' 2>/dev/null)
if [ "$NLP_STATUS" = "healthy" ]; then
    echo "✅ NLP服务运行正常"
    NLP_ENABLED=true
else
    echo "⚠️  NLP服务未运行，将使用降级模式"
    NLP_ENABLED=false
fi

# 启动小娜
echo ""
echo "🚀 启动小娜 NLP增强版..."
echo "   NLP集成: $([ "$NLP_ENABLED" = true ] && echo '✅ 已启用' || echo '❌ 未启用')"
echo "   工作目录: $BASE_DIR/production/services"
echo ""

cd "$BASE_DIR/production/services" || exit 1

# 启动增强版小娜
python3 xiaona_agent_v2_enhanced.py

echo ""
echo "👋 小娜已关闭"
