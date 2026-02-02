#!/bin/bash
"""
Elasticsearch专利搜索系统快速启动脚本
"""

echo "🚀 启动Elasticsearch专利搜索系统"
echo "=================================="

# 检查Docker是否可用
if command -v docker &> /dev/null; then
    echo "✅ Docker可用，使用Docker启动Elasticsearch"

    # 停止可能存在的容器
    docker stop elasticsearch-patent 2>/dev/null || true
    docker rm elasticsearch-patent 2>/dev/null || true

    # 启动Elasticsearch容器
    echo "🔧 启动Elasticsearch容器..."
    docker run -d \
        --name elasticsearch-patent \
        -p 9200:9200 \
        -p 9300:9300 \
        -e "discovery.type=single-node" \
        -e "xpack.security.enabled=false" \
        -e "ES_JAVA_OPTS=-Xms512m -Xmx512m" \
        docker.elastic.co/elasticsearch/elasticsearch:8.11.1

    echo "⏱️ 等待Elasticsearch启动..."
    sleep 30

    # 检查ES是否启动成功
    if curl -s http://localhost:9200 >/dev/null; then
        echo "✅ Elasticsearch启动成功！"
    else
        echo "❌ Elasticsearch启动失败，尝试使用Homebrew版本"
        # 尝试启动Homebrew版本
        if command -v elasticsearch &> /dev/null; then
            elasticsearch --daemonize
            sleep 10
        else
            echo "⚠️ 请手动安装并启动Elasticsearch"
        fi
    fi
else
    echo "⚠️ Docker不可用，检查Homebrew安装的Elasticsearch"
    if command -v elasticsearch &> /dev/null; then
        echo "🔧 启动Homebrew版本的Elasticsearch..."
        elasticsearch --daemonize
        sleep 10
    else
        echo "❌ 未找到Elasticsearch，请先安装"
        echo "安装命令: brew install elastic/tap/elasticsearch-full"
        exit 1
    fi
fi

# 检查ES连接
echo "🔍 检查Elasticsearch连接..."
if curl -s http://localhost:9200 >/dev/null; then
    echo "✅ Elasticsearch连接正常"
else
    echo "❌ Elasticsearch连接失败，请检查配置"
    exit 1
fi

# 安装Python依赖
echo "📦 安装Python依赖..."
pip3 install -q elasticsearch psycopg2-binary jieba

# 创建专利索引
echo "🗂️ 创建专利索引..."
cd /Users/xujian/Athena工作平台
python3 services/patent_services/setup_elasticsearch_patent_index.py --action create

# 索引测试数据（前10000条）
echo "📊 索引测试数据..."
python3 services/patent_services/setup_elasticsearch_patent_index.py --action index --limit 10000

# 运行性能对比测试
echo "⚡ 运行性能对比测试..."
python3 services/patent_services/performance_comparison.py

echo ""
echo "🎉 Elasticsearch专利搜索系统启动完成！"
echo ""
echo "📋 可用服务:"
echo "  - Elasticsearch: http://localhost:9200"
echo "  - 专利搜索API: 见 services/patent_services/"
echo "  - 性能测试报告: 见生成的markdown文件"
echo ""
echo "🔧 使用方法:"
echo "  python3 services/patent_services/elasticsearch_patent_search.py"
echo ""
echo "📊 监控命令:"
echo "  curl http://localhost:9200/_cluster/health"
echo "  curl http://localhost:9200/patents/_stats"