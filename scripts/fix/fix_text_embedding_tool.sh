#!/bin/bash
# Text Embedding工具快速修复脚本
# 用于安装依赖和启动BGE-M3服务

set -e  # 遇到错误立即退出

echo "=========================================="
echo "  Text Embedding工具修复脚本"
echo "=========================================="
echo ""

# 1. 安装FlagEmbedding
echo "📦 步骤1: 安装FlagEmbedding..."
pip3 install FlagEmbedding

echo ""
echo "✅ FlagEmbedding安装完成"
echo ""

# 2. 检查BGE-M3服务状态
echo "🔍 步骤2: 检查BGE-M3服务状态..."
if curl -s http://localhost:8766/health > /dev/null 2>&1; then
    echo "✅ BGE-M3服务正在运行"
    curl -s http://localhost:8766/health | python3 -m json.tool
else
    echo "❌ BGE-M3服务未运行"
    echo ""
    echo "🚀 正在启动BGE-M3服务..."

    # 检查服务脚本
    if [ -f "production/scripts/start_bge_embedding_service.py" ]; then
        python3 production/scripts/start_bge_embedding_service.py &
        echo "⏳ 服务启动中，请等待10秒..."
        sleep 10
    else
        echo "⚠️  未找到服务启动脚本，请手动启动"
    fi
fi

echo ""
echo "🧪 步骤3: 运行验证测试..."
python3 scripts/verify_text_embedding_tool.py

echo ""
echo "=========================================="
echo "  修复完成！"
echo "=========================================="
echo ""
echo "💡 下一步:"
echo "  1. 检查验证报告: docs/reports/TEXT_EMBEDDING_TOOL_VERIFICATION_REPORT_20260420.md"
echo "  2. 如果BGE-M3未启动，运行: python3 production/scripts/start_bge_embedding_service.py"
echo "  3. 测试工具: python3 -c 'from core.tools.production_tool_implementations import text_embedding_handler; import asyncio; print(asyncio.run(text_embedding_handler(params={\"text\":\"测试\"}, context={})))'"
echo ""
