#!/bin/bash

# Athena迭代式搜索系统环境配置脚本

echo "🔧 配置Athena迭代式搜索系统环境..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，请先安装Python3"
    exit 1
fi

# 创建环境变量文件
ENV_FILE="/Users/xujian/Athena工作平台/services/athena_iterative_search/.env"

echo "📝 创建环境配置文件..."

cat > "$ENV_FILE" << EOF
# Athena迭代式搜索系统环境配置

# 环境设置
ATHENA_ENV=development

# 数据库配置
DB_HOST=localhost
DB_PORT=5432
DB_NAME=athena_patents
DB_USER=postgres
DB_PASSWORD=

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Elasticsearch配置
ES_HOST=localhost
ES_PORT=9200

# Qwen LLM配置
QWEN_API_KEY=
DASHSCOPE_API_KEY=

# 外部搜索引擎API密钥（可选）
BAIDU_API_KEY=
BAIDU_API_SECRET=

BING_API_KEY=

SOGOU_API_KEY=

# 性能配置
ENABLE_PERFORMANCE_MONITORING=true
MAX_CONCURRENT_SEARCHES=10
CACHE_TTL=3600
EOF

echo "✅ 环境配置文件已创建: $ENV_FILE"

# 安装Python依赖
echo "📦 安装Python依赖..."

REQUIRED_PACKAGES=(
    "fastapi>=0.104.0"
    "uvicorn>=0.24.0"
    "elasticsearch>=8.0.0"
    "psycopg2-binary>=2.9.0"
    "pydantic>=2.0.0"
    "sentence-transformers>=2.2.0"
    "faiss-cpu>=1.7.0"
    "redis>=4.5.0"
    "aioredis>=2.0.0"
    "aiohttp>=3.8.0"
    "jieba>=0.42.0"
    "numpy>=1.24.0"
    "openai>=1.0.0"
    "beautifulsoup4>=4.12.0"
    "psutil>=5.9.0"
)

for package in "${REQUIRED_PACKAGES[@]}"; do
    package_name=$(echo "$package" | cut -d'>' -f1 | cut -d'=' -f1)
    if ! python3 -c "import $package_name" 2>/dev/null; then
        echo "   安装 $package..."
        pip3 install "$package"
    else
        echo "   ✓ $package_name 已安装"
    fi
done

# 检查服务状态
echo ""
echo "🔍 检查依赖服务状态..."

# 检查PostgreSQL
if pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
    echo "   ✅ PostgreSQL 运行正常"
else
    echo "   ⚠️  PostgreSQL 未运行或连接失败"
    echo "      请确保PostgreSQL已启动并创建athena_patents数据库"
fi

# 检查Redis
if redis-cli ping >/dev/null 2>&1; then
    echo "   ✅ Redis 运行正常"
else
    echo "   ⚠️  Redis 未运行"
    echo "      请启动Redis服务: brew services start redis"
fi

# 检查Elasticsearch
if curl -s http://localhost:9200/_cluster/health >/dev/null 2>&1; then
    echo "   ✅ Elasticsearch 运行正常"
else
    echo "   ⚠️  Elasticsearch 未运行"
    echo "      请启动Elasticsearch服务"
fi

# 设置Python路径
echo ""
echo "🐍 设置Python路径..."
export PYTHONPATH="/Users/xujian/Athena工作平台:$PYTHONPATH"
echo 'export PYTHONPATH="/Users/xujian/Athena工作平台:$PYTHONPATH"' >> ~/.zshrc

# 创建必要目录
echo ""
echo "📁 创建必要目录..."
mkdir -p /Users/xujian/Athena工作平台/services/athena_iterative_search/logs
mkdir -p /Users/xujian/Athena工作平台/services/athena_iterative_search/cache
mkdir -p /Users/xujian/Athena工作平台/services/athena_iterative_search/data

# 初始化向量索引
echo ""
echo "🔮 初始化向量搜索索引..."
cat > "/Users/xujian/Athena工作平台/services/athena_iterative_search/init_vector_index.py" << 'EOF'
#!/usr/bin/env python3
"""
初始化向量搜索索引
"""

import asyncio
import sys
import os
sys.path.append('/Users/xujian/Athena工作平台')

from services.athena_iterative_search.enhanced_vector_search import EnhancedVectorSearch
from services.athena_iterative_search.config_enhanced import VectorSearchConfig

async def main():
    print("初始化向量搜索索引...")

    config = VectorSearchConfig()
    db_config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "database": os.getenv("DB_NAME", "athena_patents"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", ""),
        "redis_host": os.getenv("REDIS_HOST", "localhost"),
        "redis_port": int(os.getenv("REDIS_PORT", "6379")),
        "redis_db": int(os.getenv("REDIS_DB", "0"))
    }

    vector_search = EnhancedVectorSearch(config, db_config)

    try:
        # 构建索引（这可能需要一些时间）
        await vector_search.build_index_from_database(batch_size=500)
        print("✅ 向量索引构建完成")

        # 显示统计信息
        stats = vector_search.get_statistics()
        print(f"索引大小: {stats['index_size']}")
        print(f"向量维度: {stats['embedding_dimension']}")

    except Exception as e:
        print(f"❌ 向量索引构建失败: {e}")
        print("   这可能是由于数据库连接问题或缺少专利数据")
    finally:
        await vector_search.close()

if __name__ == "__main__":
    asyncio.run(main())
EOF

chmod +x "/Users/xujian/Athena工作平台/services/athena_iterative_search/init_vector_index.py"

echo ""
echo "🎉 环境配置完成！"
echo ""
echo "📋 下一步操作："
echo "1. 配置API密钥（如需要）:"
echo "   编辑 $ENV_FILE 文件，添加您的Qwen API密钥"
echo ""
echo "2. 初始化向量索引（可选，提高搜索性能）:"
echo "   python3 /Users/xujian/Athena工作平台/services/athena_iterative_search/init_vector_index.py"
echo ""
echo "3. 启动API服务:"
echo "   ./scripts/start_enhanced_athena_iterative_search.sh"
echo ""
echo "4. 访问API文档:"
echo "   http://localhost:5002/docs"
echo ""
echo "🔍 系统特性："
echo "   ✅ 多引擎混合搜索（Elasticsearch + 向量 + 外部）"
echo "   ✅ Qwen LLM智能分析和查询生成"
echo "   ✅ 迭代式深度搜索"
echo "   ✅ 高性能缓存和并发优化"
echo "   ✅ 支持百度、Bing、Google专利搜索"