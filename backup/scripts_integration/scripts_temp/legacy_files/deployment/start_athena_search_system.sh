#!/bin/bash

# Athena迭代式搜索系统一键启动脚本

echo "🚀 启动Athena迭代式搜索系统..."
echo "=========================================="

# 1. 启动基础服务
echo ""
echo "1️⃣ 启动基础服务 (PostgreSQL, Redis, Elasticsearch)..."
if [ -f "/Users/xujian/Athena工作平台/scripts/start_services.sh" ]; then
    bash /Users/xujian/Athena工作平台/scripts/start_services.sh
else
    echo "⚠️ 基础服务启动脚本不存在，请手动启动服务"
fi

# 等待服务启动
echo ""
echo "⏳ 等待服务启动完成..."
sleep 5

# 2. 启动API服务
echo ""
echo "2️⃣ 启动Athena迭代式搜索API服务..."
cd /Users/xujian/Athena工作平台/services/athena_iterative_search

# 检查端口是否被占用
if lsof -i :5002 > /dev/null 2>&1; then
    echo "⚠️ 端口5002已被占用，正在停止现有服务..."
    pkill -f "athena_iterative_search"
    sleep 2
fi

# 启动API服务
echo "🔄 启动API服务 (端口: 5002)..."
PYTHONPATH=/Users/xujian/Athena工作平台 nohup python3 -m uvicorn api_service:app --host 0.0.0.0 --port 5002 --reload > api_service.log 2>&1 &

API_PID=$!
echo "✅ API服务已启动 (PID: $API_PID)"

# 3. 验证服务状态
echo ""
echo "3️⃣ 验证服务状态..."
sleep 3

# 检查API健康状态
for i in {1..10}; do
    if curl -s http://localhost:5002/health > /dev/null 2>&1; then
        echo "✅ API服务运行正常"
        HEALTH_STATUS=$(curl -s http://localhost:5002/health | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])")
        echo "🏥 健康状态: $HEALTH_STATUS"
        break
    else
        echo "⏳ 等待API服务启动... ($i/10)"
        sleep 2
    fi
done

# 4. 显示访问信息
echo ""
echo "=========================================="
echo "🎉 Athena迭代式搜索系统启动完成！"
echo "=========================================="
echo ""
echo "📍 服务地址:"
echo "   • API文档: http://localhost:5002/docs"
echo "   • 健康检查: http://localhost:5002/health"
echo "   • 基础接口: http://localhost:5002/"
echo ""
echo "🛠️ 使用方式:"
echo "   • 通用搜索工具:"
echo "     python3 scripts/athena_universal_search.py --help"
echo ""
echo "   • 技术搜索演示:"
echo "     python3 services/athena_iterative_search/technology_search_example.py"
echo ""
echo "   • 命令行快速搜索:"
echo "     python3 scripts/athena_universal_search.py --search \"人工智能\" --results 10"
echo ""
echo "📚 文档位置:"
echo "   • 使用指南: documentation/Athena迭代式搜索系统使用指南.md"
echo "   • API文档: http://localhost:5002/docs"
echo ""
echo "📊 系统状态:"
echo "   • API服务: 运行中 (PID: $API_PID)"
echo "   • 基础数据库: PostgreSQL, Redis, Elasticsearch"
echo "   • LLM服务: Qwen (已配置)"
echo ""
echo "🛑 停止服务:"
echo "   pkill -f 'athena_iterative_search'"
echo "   pkill -f 'uvicorn api_service:app'"
echo ""

# 5. 提供快速测试选项
echo "🔍 是否要进行快速测试？(y/n)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    echo ""
    echo "🧪 执行快速搜索测试..."
    python3 services/athena_iterative_search/technology_search_example.py
fi

echo ""
echo "🎯 系统已就绪，开始您的智能搜索之旅吧！"