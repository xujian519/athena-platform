#!/bin/bash

# Athena法律AI服务启动脚本
# Legal AI Services Startup Script for Athena Platform

echo "🚀 启动Athena法律AI服务"
echo "=================================="

# 设置环境变量
export PYTHONPATH="/Users/xujian/Athena工作平台:$PYTHONPATH"
export LEGAL_AI_HOME="/Users/xujian/Athena工作平台/domains/legal-ai"

# 检查法律AI模块是否存在
if [ ! -d "$LEGAL_AI_HOME" ]; then
    echo "❌ 法律AI模块不存在: $LEGAL_AI_HOME"
    exit 1
fi

# 检查端口占用
check_port() {
    local port=$1
    local service=$2
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        echo "⚠️  端口 $port 已被占用，$service 可能已在运行"
        return 1
    fi
    return 0
}

# 清理现有服务
cleanup_services() {
    echo "🛑 清理现有法律AI服务..."
    pkill -f "knowledge_graph_api.py" 2>/dev/null || true
    pkill -f "unified_intelligent_search.py" 2>/dev/null || true
    pkill -f "legal_vector_search.py" 2>/dev/null || true
    pkill -f "unified_knowledge_manager.py" 2>/dev/null || true
    sleep 2
}

# 服务配置
declare -A SERVICES=(
    ["知识图谱API"]="9030"
    ["统一智能搜索"]="9040"
    ["法律向量搜索"]="9050"
    ["统一知识管理"]="9060"
)

echo "📋 法律AI服务启动计划:"
for service in "${!SERVICES[@]}"; do
    echo "├── 🎯 $service (端口 ${SERVICES[$service]})"
done
echo "└── 📊 所有服务将在后台运行"
echo ""

# 清理现有服务
cleanup_services

# 创建日志目录
LOG_DIR="/Users/xujian/Athena工作平台/logs/legal-ai"
mkdir -p "$LOG_DIR"

# 启动服务
echo "🚀 启动法律AI服务..."

# 1. 知识图谱API
echo "🎯 启动知识图谱API (端口9030)..."
cd "$LEGAL_AI_HOME/apis"
nohup python3 knowledge_graph_api.py > "$LOG_DIR/knowledge_graph_api.log" 2>&1 &
KG_PID=$!
echo "   PID: $KG_PID"

# 2. 统一智能搜索
echo "🔍 启动统一智能搜索 (端口9040)..."
nohup python3 unified_intelligent_search.py > "$LOG_DIR/unified_intelligent_search.log" 2>&1 &
SEARCH_PID=$!
echo "   PID: $SEARCH_PID"

# 3. 法律向量搜索
echo "📚 启动法律向量搜索 (端口9050)..."
cd "$LEGAL_AI_HOME/services"
nohup python3 legal_vector_search.py > "$LOG_DIR/legal_vector_search.log" 2>&1 &
VECTOR_PID=$!
echo "   PID: $VECTOR_PID"

# 4. 统一知识管理
echo "🗂️  启动统一知识管理 (端口9060)..."
cd "$LEGAL_AI_HOME/apis"
nohup python3 unified_knowledge_manager.py > "$LOG_DIR/unified_knowledge_manager.log" 2>&1 &
MANAGER_PID=$!
echo "   PID: $MANAGER_PID"

# 等待服务启动
echo ""
echo "⏳ 等待服务启动..."
sleep 5

# 检查服务状态
echo "📊 服务状态检查:"
echo ""

# 检查知识图谱API
if curl -s http://localhost:9030/health >/dev/null; then
    echo "✅ 知识图谱API (9030): 运行正常"
else
    echo "❌ 知识图谱API (9030): 启动失败"
fi

# 检查统一智能搜索
if curl -s http://localhost:9040/health >/dev/null; then
    echo "✅ 统一智能搜索 (9040): 运行正常"
else
    echo "❌ 统一智能搜索 (9040): 启动失败"
fi

# 检查统一知识管理
if curl -s http://localhost:9060/health >/dev/null; then
    echo "✅ 统一知识管理 (9060): 运行正常"
else
    echo "❌ 统一知识管理 (9060): 启动失败"
fi

# 输出访问地址
echo ""
echo "🌐 法律AI服务访问地址:"
echo "├── 🎯 知识图谱API: http://localhost:9030"
echo "├── 📚 API文档: http://localhost:9030/docs"
echo "├── 🔍 统一智能搜索: http://localhost:9040"
echo "├── 📖 搜索文档: http://localhost:9040/docs"
echo "├── 🗂️ 统一知识管理: http://localhost:9060"
echo "└── 📊 管理文档: http://localhost:9060/docs"
echo ""

# 保存PID到文件
echo "$KG_PID" > /tmp/legal_ai_kg_api.pid
echo "$SEARCH_PID" > /tmp/legal_ai_search.pid
echo "$VECTOR_PID" > /tmp/legal_ai_vector.pid
echo "$MANAGER_PID" > /tmp/legal_ai_manager.pid

echo "💾 进程ID已保存到 /tmp/legal_ai_*.pid"
echo ""

# 创建停止脚本
cat > /tmp/stop_legal_ai_services.sh << 'EOF'
#!/bin/bash
echo "🛑 停止Athena法律AI服务"
pkill -f "knowledge_graph_api.py" || true
pkill -f "unified_intelligent_search.py" || true
pkill -f "legal_vector_search.py" || true
pkill -f "unified_knowledge_manager.py" || true
echo "✅ 所有法律AI服务已停止"
EOF
chmod +x /tmp/stop_legal_ai_services.sh

echo "💡 停止服务: bash /tmp/stop_legal_ai_services.sh"
echo ""

echo "🎉 Athena法律AI服务启动完成!"
echo "💖 法律智能分析与检索系统已就绪"