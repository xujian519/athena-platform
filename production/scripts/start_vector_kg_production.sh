#!/bin/bash
# Athena平台 - 向量库+知识图谱统一启动脚本
set -e

echo "========================================================================"
echo "🚀 Athena平台 - 向量库+知识图谱生产环境启动"
echo "========================================================================"
echo "启动时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 创建目录
mkdir -p production/pids production/logs production/backups

# 检查Qdrant
echo "📊 检查Qdrant..."
if ! curl -s http://localhost:6333/collections > /dev/null 2>&1; then
    echo "❌ Qdrant未运行"
    exit 1
fi
echo "✅ Qdrant正常"

# 检查PostgreSQL
echo "🗄️  检查PostgreSQL..."
if ! /opt/homebrew/opt/postgresql@17/bin/psql -U xujian -d patent_legal_db -c "SELECT 1" > /dev/null 2>&1; then
    echo "❌ PostgreSQL未运行"
    exit 1
fi
echo "✅ PostgreSQL正常"

# 启动法律服务
echo ""
echo "📚 启动法律向量库+知识图谱服务..."
production/scripts/start_legal_vector_kg_production.sh
sleep 3

# 启动专利服务
echo ""
echo "📄 启动专利规则向量库+知识图谱服务..."
production/scripts/start_patent_vector_kg_production.sh
sleep 3

echo ""
echo "========================================================================"
echo "🎉 所有服务启动完成！"
echo "========================================================================"
echo ""
echo "📊 服务端口:"
echo "  • 法律向量库搜索:     http://localhost:8010"
echo "  • 专利向量库搜索:     http://localhost:8011"
echo "  • 法律知识图谱:       http://localhost:8012"
echo "  • 专利知识图谱:       http://localhost:8013"
echo ""
echo "✅ 生产环境部署完成！"
echo "========================================================================"
