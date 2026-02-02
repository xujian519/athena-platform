#!/bin/bash

# Athena迭代式搜索系统启动脚本

echo "🚀 启动Athena迭代式搜索系统..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，请先安装Python3"
    exit 1
fi

# 检查必要的Python包
echo "📦 检查依赖包..."
REQUIRED_PACKAGES=("fastapi" "uvicorn" "elasticsearch" "psycopg2-binary" "pydantic")

for package in "${REQUIRED_PACKAGES[@]}"; do
    if ! python3 -c "import $package" 2>/dev/null; then
        echo "⚠️  $package 未安装，正在安装..."
        pip3 install $package
    fi
done

# 设置Python路径
export PYTHONPATH="/Users/xujian/Athena工作平台:$PYTHONPATH"

# 检查Elasticsearch是否运行
if ! curl -s http://localhost:9200/_cluster/health >/dev/null 2>&1; then
    echo "⚠️  Elasticsearch 未运行，请先启动Elasticsearch服务"
    echo "   可以运行: python3 services/patent_services/es_patent_search_api.py"
fi

# 切换到API服务目录
cd /Users/xujian/Athena工作平台/services/athena_iterative_search

# 创建日志目录
mkdir -p logs

echo "🌐 启动API服务..."
echo "   API地址: http://localhost:5002"
echo "   API文档: http://localhost:5002/docs"
echo "   健康检查: http://localhost:5002/health"

# 启动API服务
python3 api.py