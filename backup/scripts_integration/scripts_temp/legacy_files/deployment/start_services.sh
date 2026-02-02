#!/bin/bash

# 启动Athena专利搜索系统所需的所有服务

echo "🚀 启动Athena专利搜索系统服务..."

# 1. 启动PostgreSQL
echo ""
echo "1. 启动PostgreSQL..."
if pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
    echo "✅ PostgreSQL 已运行"
else
    echo "⚠️  PostgreSQL 未运行，尝试启动..."
    # 检查是否有多个PostgreSQL版本
    if brew services list | grep -q "postgresql@17"; then
        brew services start postgresql@17
    elif brew services list | grep -q "postgresql@14"; then
        brew services start postgresql@14
    else
        echo "❌ 未找到PostgreSQL，请先安装: brew install postgresql"
    fi
fi

# 2. 启动Redis
echo ""
echo "2. 启动Redis..."
if redis-cli ping >/dev/null 2>&1; then
    echo "✅ Redis 已运行"
else
    echo "⚠️  Redis 未运行，启动中..."
    brew services start redis
fi

# 3. 启动Elasticsearch
echo ""
echo "3. 启动Elasticsearch..."
if curl -s http://localhost:9200/_cluster/health >/dev/null 2>&1; then
    echo "✅ Elasticsearch 已运行"
else
    echo "⚠️  Elasticsearch 未运行，尝试启动..."
    # 检查Elasticsearch是否已安装
    if [ -d "/usr/local/var/homebrew/linked/elasticsearch" ] || [ -d "/opt/homebrew/var/homebrew/linked/elasticsearch" ]; then
        brew services start elasticsearch
    else
        echo "❌ 未找到Elasticsearch，请先安装:"
        echo "   brew tap elastic/tap"
        echo "   brew install elastic/tap/elasticsearch-full"
    fi
fi

# 4. 等待服务启动
echo ""
echo "4. 等待服务启动..."
sleep 5

# 5. 验证服务状态
echo ""
echo "5. 验证服务状态..."
ALL_SERVICES_OK=true

# 检查PostgreSQL
if pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
    echo "✅ PostgreSQL: 运行正常"
else
    echo "❌ PostgreSQL: 未运行"
    ALL_SERVICES_OK=false
fi

# 检查Redis
if redis-cli ping >/dev/null 2>&1; then
    echo "✅ Redis: 运行正常"
else
    echo "❌ Redis: 未运行"
    ALL_SERVICES_OK=false
fi

# 检查Elasticsearch
if curl -s http://localhost:9200/_cluster/health >/dev/null 2>&1; then
    echo "✅ Elasticsearch: 运行正常"
else
    echo "❌ Elasticsearch: 未运行"
    ALL_SERVICES_OK=false
fi

# 6. 创建数据库（如果不存在）
echo ""
echo "6. 检查/创建数据库..."
if createdb -h localhost -p 5432 -U postgres athena_patents 2>/dev/null; then
    echo "✅ 数据库 athena_patents 创建成功"
else
    echo "✅ 数据库 athena_patents 已存在"
fi

# 7. 总结
echo ""
echo "=========================================="
if [ "$ALL_SERVICES_OK" = true ]; then
    echo "✅ 所有服务启动成功！"
    echo ""
    echo "🎯 下一步操作："
    echo "1. 运行专利数据导入（如果需要）"
    echo "2. 启动Athena搜索API服务:"
    echo "   ./scripts/start_athena_iterative_search.sh"
    echo ""
    echo "📖 访问地址："
    echo "   API文档: http://localhost:5002/docs"
    echo "   健康检查: http://localhost:5002/health"
else
    echo "⚠️  部分服务未启动成功"
    echo ""
    echo "🔧 故障排除："
    echo "1. 检查服务是否安装：brew list"
    echo "2. 手动启动服务："
    echo "   - brew services start postgresql"
    echo "   - brew services start redis"
    echo "   - brew services start elasticsearch"
    echo "3. 查看服务日志：brew services list"
fi
echo "=========================================="