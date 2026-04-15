#!/bin/bash
# IP智能体MCP测试脚本

echo "========================================"
echo "  IP智能体 MCP Server 测试脚本"
echo "========================================"
echo ""

# 检查服务状态
echo "📋 检查依赖服务..."
echo ""

# 检查MLX LLM服务
if curl -s http://127.0.0.1:8765/v1/models > /dev/null 2>&1; then
    echo "✅ MLX LLM服务 运行中"
else
    echo "❌ MLX LLM服务 未运行，请检查 127.0.0.1:8765"
fi

# 检查Qdrant
if curl -s http://localhost:6333/collections > /dev/null 2>&1; then
    echo "✅ Qdrant 运行中"
else
    echo "❌ Qdrant 未运行，请执行: docker run -p 6333:6333 qdrant/qdrant"
fi

# 检查Neo4j
if curl -s http://localhost:7474 > /dev/null 2>&1; then
    echo "✅ Neo4j 运行中"
else
    echo "❌ Neo4j 未运行，请执行: docker run -p 7474:7474 -p 7687:7687 neo4j:latest"
fi

echo ""
echo "========================================"
echo "  MCP Server 配置信息"
echo "========================================"
echo "路径: /Users/xujian/Athena工作平台/services/ip-mcp-server"
echo "模型: qwen3.5:latest"
echo ""

echo "========================================"
echo "  在OpenCode中使用"
echo "========================================"
echo "1. 在OpenCode中输入以下内容测试:"
echo ""
echo '请帮我理解这份技术交底书：'
echo '发明名称：智能心率监测手表'
echo '技术领域：可穿戴健康设备'  
echo '背景：现有设备心率监测不准、续航短'
echo '发明内容：采用PPG光学传感器检测心率，'
echo '内置BLE低功耗蓝牙芯片，续航30天。'
echo ""
echo "2. OpenCode会自动调用MCP工具处理"
echo ""
echo "========================================"
echo "  直接测试MCP Server"
echo "========================================"
echo "执行以下命令测试:"
echo ""
echo 'cd /Users/xujian/Athena工作平台/services/ip-mcp-server'
echo 'echo \x27{"jsonrpc":"2.0","id":1,"method":"tools/list"}\x27 | node dist/index.js'
echo ""
