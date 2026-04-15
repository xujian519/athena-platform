#!/bin/bash
# -*- coding: utf-8 -*-
"""
启动Athena多模态系统（精简版）
Start Athena Multimodal System (Simplified)
"""

echo "🚀 启动Athena智能多模态系统（精简版）"
echo "=================================="

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

# 1. 检查混合API网关（集成版）
echo ""
echo "1. 检查服务状态..."

if curl -s http://localhost:8090/api/health > /dev/null; then
    echo "  ✅ 混合API网关 (8090) 已运行"
else
    echo "  🌐 启动混合API网关（集成版）..."
    cd services/multimodal
    python hybrid_api_gateway_integrated.py &
    GATEWAY_PID=$!
    cd ../..
    echo "  ✅ 混合API网关已启动 (PID: $GATEWAY_PID)"
    sleep 5
fi

# 2. 显示服务信息
echo ""
echo "✅ 多模态系统启动完成！"
echo ""
echo "📍 服务地址："
echo "  🌐 智能混合API网关: http://localhost:8090"
echo "  🤖 小诺GUI控制器: http://localhost:8001"
echo ""
echo "📊 API接口："
echo "  智能处理: POST http://localhost:8090/api/process"
echo "  批量处理: POST http://localhost:8090/api/batch-process"
echo "  文件查询: GET http://localhost:8090/api/file/{file_id}"
echo "  向量搜索: GET http://localhost:8090/api/search/vector"
echo "  统计信息: GET http://localhost:8090/api/statistics"
echo "  健康检查: GET http://localhost:8090/api/health"
echo ""
echo "🎯 智能路由策略："
echo "  - 🔒 机密数据 → 本地Whisper处理"
echo "  - ⚡ 紧急任务 → Claude MCP处理"
echo "  - 📦 大批量(>100) → 本地系统"
echo "  - 🎯 高质量要求 → Claude MCP处理"
echo ""
echo "💡 使用示例："
echo ""
echo "处理单个文件："
echo "curl -X POST http://localhost:8090/api/process \\"
echo "  -F \"file=@example.jpg\" \\"
echo "  -F \"priority=high\" \\"
echo "  -F \"high_quality=true\""
echo ""
echo "查询文件信息："
echo "curl http://localhost:8090/api/file/123 | python3 -m json.tool"
echo ""
echo "向量搜索："
echo "curl \"http://localhost:8090/api/search/vector?query=测试图片&limit=5\""
echo ""
echo "查看统计："
echo "curl http://localhost:8090/api/statistics | python3 -m json.tool"
echo ""
echo "停止服务："
echo "  kill $GATEWAY_PID"
echo ""

# 显示进程信息
echo "📝 运行中的进程："
ps aux | grep -E "(hybrid_api_gateway|xiaonuo_gui_controller)" | grep -v grep | awk '{
    pid=$2;
    cmd=$11;
    for(i=12;i<=NF;i++) cmd=cmd" "$i;
    if(cmd ~ "hybrid_api_gateway") {
        port="(8090)";
    } else if(cmd ~ "xiaonuo_gui_controller") {
        port="(8001)";
    } else {
        port="";
    }
    printf "  PID %-6s %s\n", pid, port;
}'