#!/bin/bash
# -*- coding: utf-8 -*-
"""
启动增强感知服务
"""

set -e

# 配置
HOST="0.0.0.0"
PORT="8009"
SERVICE_NAME="enhanced-perception"
PYTHON="/Users/xujian/Athena工作平台"
SERVICE_PATH="/Users/xujian/Athena工作平台/services/enhanced_perception_service.py"

echo "🧠 启动Athena增强感知服务"
echo "=================================="

# 检查端口是否被占用
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  端口 $PORT 已被占用，正在停止现有服务..."
    pkill -f "enhanced_perception_service.py" || true
    sleep 2
fi

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

# 检查服务文件
if [ ! -f "$SERVICE_PATH" ]; then
    echo "❌ 感知服务文件不存在: $SERVICE_PATH"
    exit 1
fi

echo "📊 服务配置:"
echo "├── 🌐 服务地址: http://$HOST:$PORT"
echo "├── 📚 API文档: http://$HOST:$PORT/docs"
echo "├── 🧠 感知引擎: 增强多模态处理器"
echo "├── ⚡ 性能优化: 智能缓存 + 批量处理"
echo "├── 🛡️  错误处理: 重试机制 + 降级策略"
echo "└── 📊 监控系统: 实时性能监控"

echo ""
echo "🚀 启动服务..."

# 启动服务
cd "$PYTHON"
PYTHONPATH=/Users/xujian/Athena工作平台 python3 "$SERVICE_PATH" &
SERVICE_PID=$!

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 5

# 检查服务状态
if ps -p $SERVICE_PID > /dev/null; then
    echo "✅ 增强感知服务启动成功 (PID: $SERVICE_PID)"
    echo ""
    echo "🌐 服务访问地址:"
    echo "├── 🧠 感知服务: http://$HOST:$PORT"
    echo "├── 🏥 健康检查: http://$HOST:$PORT/health"
    echo "├── 📊 服务状态: http://$HOST:$PORT/status"
    echo "├── 🔧 处理器列表: http://$HOST:$PORT/processors"
    echo "└── 📚 API文档: http://$HOST:$PORT/docs"
    echo ""
    echo "🧠 感知服务功能:"
    echo "├── 📝 文本处理: /process/text"
    echo "├── 🎭 多模态处理: /process/multimodal"
    echo "├── 📦 批量处理: /process/batch"
    echo "├── 📊 性能仪表板: /performance/dashboard"
    echo "└── 📈 性能报告: /performance/report"
    echo ""
    echo "🛑 停止服务: kill $SERVICE_PID"
    echo ""
    echo "💡 服务特性:"
    echo "├── ✅ 智能缓存机制"
    echo "├── ✅ 批量并发处理"
    echo "├── ✅ 错误重试与降级"
    echo "├── ✅ 实时性能监控"
    echo "├── ✅ 多模态融合处理"
    echo "└── ✅ 跨模态推理分析"
else
    echo "❌ 增强感知服务启动失败"
    exit 1
fi

# 保存PID到文件
echo $SERVICE_PID > /tmp/${SERVICE_NAME}.pid

echo ""
echo "🎉 Athena增强感知服务已启动!"
echo "🏛️ 智能感知平台已激活，准备为您提供企业级感知处理服务"