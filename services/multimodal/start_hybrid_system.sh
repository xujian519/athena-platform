#!/bin/bash
# -*- coding: utf-8 -*-
"""
启动混合多模态系统
Start Hybrid Multimodal System
"""

echo "🚀 启动Athena智能混合多模态系统"
echo "================================"

cd "/Users/xujian/Athena工作平台"

# 激活虚拟环境
if [ -f "venv/bin/activate" ]; then
    echo "📦 激活Python虚拟环境..."
    source venv/bin/activate
else
    echo "❌ 未找到虚拟环境"
    exit 1
fi

# 设置环境变量
export PYTHONPATH="/Users/xujian/Athena工作平台:$PYTHONPATH"

# 1. 检查服务状态
echo ""
echo "1. 检查服务状态..."

# 检查基础多模态API（端口8089）
if curl -s http://localhost:8089/health > /dev/null; then
    echo "  ✅ 基础多模态API (8089) 运行中"
else
    echo "  ⚠️  基础多模态API未运行，正在启动..."
    cd services/multimodal
    python multimodal_api_enhanced.py &
    API_PID=$!
    cd ../..
    echo "  📡 基础API已启动 (PID: $API_PID)"
    sleep 3
fi

# 检查MCP工具
echo ""
echo "2. 检查MCP工具状态..."
echo "  🔗 MCP工具通过API调用，无需单独启动"

# 2. 启动混合API网关
echo ""
echo "3. 启动智能混合API网关..."

# 检查端口8090是否被占用
if lsof -Pi :8090 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "  ⚠️  端口8090已被占用"
    read -p "  是否停止现有服务并重新启动? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pkill -f "hybrid_api_gateway.py" 2>/dev/null || true
        sleep 2
    else
        echo "  退出启动"
        exit 1
    fi
fi

# 启动混合API网关
echo "  🌐 启动混合API网关 (端口8090)..."
cd services/multimodal
python hybrid_api_gateway.py &
GATEWAY_PID=$!
cd ../..

# 等待服务启动
sleep 5

# 3. 验证服务
echo ""
echo "4. 验证服务启动..."

if curl -s http://localhost:8090/health > /dev/null; then
    echo "  ✅ 混合API网关启动成功！"
else
    echo "  ❌ 混合API网关启动失败"
    exit 1
fi

# 4. 显示服务信息
echo ""
echo "✅ 混合多模态系统启动完成！"
echo ""
echo "📍 服务地址："
echo "  🌐 混合API网关: http://localhost:8090"
echo "  🔧 基础多模态API: http://localhost:8089"
echo ""
echo "📊 管理接口："
echo "  📈 统计信息: http://localhost:8090/api/statistics"
echo "  💰 成本分析: http://localhost:8090/api/cost-analysis"
echo "  ❤️  健康检查: http://localhost:8090/api/health"
echo ""
echo "🎯 API使用示例："
echo ""
echo "1. 智能处理单文件："
echo "curl -X POST http://localhost:8090/api/process \\"
echo "  -F \"file=@example.jpg\" \\"
echo "  -F \"priority=high\" \\"
echo "  -F \"sensitivity=public\" \\"
echo "  -F \"high_quality=true\""
echo ""
echo "2. 批量处理文件："
echo "curl -X POST http://localhost:8090/api/batch-process \\"
echo "  -F \"files=@file1.jpg\" -F \"files=@file2.pdf\" \\"
echo "  -F \"priority=normal\" \\"
echo "  -F \"max_concurrent=3\""
echo ""
echo "3. 查看统计信息："
echo "curl http://localhost:8090/api/statistics | python3 -m json.tool"
echo ""
echo "💡 智能路由策略："
echo "  - 🔒 机密数据 → 本地Whisper处理"
echo "  - ⚡ 紧急任务 → Claude MCP处理"
echo "  - 📦 大批量(>100) → 本地系统"
echo "  - 🎯 高质量要求 → Claude MCP处理"
echo ""
echo "📝 进程信息："
echo "  - 混合API网关 PID: $GATEWAY_PID"
echo "  - 基础多模态API PID: $API_PID"
echo ""
echo "🛑 停止服务："
echo "  kill $GATEWAY_PID $API_PID"
echo ""

# 保持脚本运行或退出
read -p "按回车键退出（服务将继续在后台运行）..." -r
echo ""
echo "服务正在后台运行..."
echo "使用 'ps aux | grep hybrid_api_gateway' 查看进程"