#!/bin/bash
# 启动智能数据服务
# Start Intelligent Data Services

echo "🚀 启动智能数据服务..."
echo "================================"

# 1. 检查并启动Qdrant
echo "📦 检查Qdrant向量数据库..."
if docker ps | grep -q qdrant; then
    echo "✅ Qdrant已运行"
else
    echo "🔧 启动Qdrant..."
    docker start qdrant
    sleep 5
fi

# 2. 检查Neo4j
echo "🔍 检查Neo4j知识图谱..."
if neo4j status | grep -q "running"; then
    echo "✅ Neo4j已运行"
else
    echo "🔧 启动Neo4j..."
    neo4j start
    sleep 5
fi

# 3. 启动SQLite统一服务
echo "📄 启动SQLite统一服务..."
python3 services/sqlite_unified_service.py &
SQLITE_PID=$!
echo "✅ SQLite服务已启动 (PID: $SQLITE_PID)"

# 4. 启动统一专利智能服务
echo "🧠 启动统一专利智能服务..."
python3 services/unified_patent_intelligence_service.py &
INTELLIGENCE_PID=$!
echo "✅ 专利智能服务已启动 (PID: $INTELLIGENCE_PID)"

# 5. 等待服务就绪
echo ""
echo "⏳ 等待服务就绪..."
sleep 10

# 6. 检查服务状态
echo ""
echo "📊 服务状态检查:"
echo "================"

# 检查Qdrant
echo -n "Qdrant (端口6333): "
if curl -s http://localhost:6333/collections > /dev/null 2>&1; then
    echo "✅ 运行中"
else
    echo "❌ 未响应"
fi

# 检查Neo4j
echo -n "Neo4j (端口7474): "
if curl -s http://localhost:7474 > /dev/null 2>&1; then
    echo "✅ 运行中"
else
    echo "❌ 未响应"
fi

# 检查SQLite服务
echo -n "SQLite服务 (端口8011): "
if curl -s http://localhost:8011/ > /dev/null 2>&1; then
    echo "✅ 运行中"
else
    echo "❌ 未响应"
fi

# 检查专利智能服务
echo -n "专利智能服务 (端口8010): "
if curl -s http://localhost:8010/ > /dev/null 2>&1; then
    echo "✅ 运行中"
else
    echo "❌ 未响应"
fi

# 7. 显示访问地址
echo ""
echo "🌐 服务访问地址:"
echo "================"
echo "Qdrant Web UI:     http://localhost:6334/dashboard"
echo "Neo4j Web UI:      http://localhost:7474"
echo "SQLite API:        http://localhost:8011/docs"
echo "专利智能服务API:    http://localhost:8010/docs"
echo ""

# 8. 保存PID以便停止服务
echo $SQLITE_PID > /tmp/sqlite_service.pid
echo $INTELLIGENCE_PID > /tmp/intelligence_service.pid

# 9. 创建停止脚本
cat > /tmp/stop_intelligent_services.sh << 'EOF'
#!/bin/bash
echo "🛑 停止智能数据服务..."

# 停止Python服务
if [ -f /tmp/sqlite_service.pid ]; then
    SQLITE_PID=$(cat /tmp/sqlite_service.pid)
    kill $SQLITE_PID 2>/dev/null
    echo "✅ SQLite服务已停止"
fi

if [ -f /tmp/intelligence_service.pid ]; then
    INTELLIGENCE_PID=$(cat /tmp/intelligence_service.pid)
    kill $INTELLIGENCE_PID 2>/dev/null
    echo "✅ 专利智能服务已停止"
fi

# 停止Docker容器（可选）
# docker stop qdrant

# 停止Neo4j（可选）
# neo4j stop

echo "📌 所有服务已停止"
EOF

chmod +x /tmp/stop_intelligent_services.sh

echo "✅ 所有智能数据服务启动完成！"
echo "💡 使用 /tmp/stop_intelligent_services.sh 停止所有服务"
echo ""