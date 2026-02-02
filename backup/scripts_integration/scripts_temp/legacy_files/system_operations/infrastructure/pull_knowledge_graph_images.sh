#!/bin/bash
# Athena平台知识图谱相关Docker镜像拉取脚本
# 包含TuGraph和其他知识图谱技术栈

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }

echo "🕸️ Athena平台 - 知识图谱Docker镜像拉取"
echo "====================================="
echo ""

# 检查Docker是否运行
if ! docker info >/dev/null 2>&1; then
    log_warning "Docker未运行，请先启动Docker Desktop"
    exit 1
fi

# 知识图谱相关镜像定义
declare -A KG_IMAGES=(
    # TuGraph (主要知识图谱数据库)
    ["tugraph/tugraph-runtime-centos7:4.5.1"]="TuGraph图数据库"
    ["tugraph/tugraph-runtime-ubuntu:4.5.1"]="TuGraph Ubuntu版本"

    # Neo4j (备选图数据库)
    ["neo4j:5.15-community"]="Neo4j图数据库社区版"
    ["neo4j:4.4-enterprise"]="Neo4j企业版"

    # ArangoDB (多模型数据库，支持图)
    ["arangodb/arangodb:3.11"]="ArangoDB多模型数据库"

    # JanusGraph (分布式图数据库)
    ["janusgraph/janusgraph:1.0"]="JanusGraph分布式图数据库"

    # 相关工具和服务
    ["redis:7-alpine"]="Redis缓存服务"
    ["elasticsearch:8.11.0"]="Elasticsearch搜索引擎"
    ["kibana:8.11.0"]="Kibana数据可视化"
    ["jupyter/scipy-notebook:latest"]="Jupyter数据分析环境"

    # 图可视化和分析工具
    ["neo4jlabs/neuler:2.0"]="Neo4j图算法库"
    ["neo4j/apoc:5.15-all"]="Neo4j插件库"

    # 开发工具
    ["python:3.11-slim"]="Python运行环境"
    ["node:18-alpine"]="Node.js环境"
    ["postgres:15-alpine"]="PostgreSQL数据库"

    # 图计算框架
    ["apache/tinkerpop-gremlin-server:3.7"]="Gremlin图计算服务器"
    ["apache/spark:3.5-py3"]="Spark大数据处理"
)

# 统计信息
total_images=${#KG_IMAGES[@]}
pulled_count=0
failed_count=0

log_info "准备拉取 ${total_images} 个知识图谱相关镜像..."
echo ""

# 重点拉取TuGraph相关镜像
log_info "🎯 重点拉取TuGraph镜像 (项目主要图数据库)"
echo ""

# 优先拉取核心的TuGraph镜像
core_kg_images=(
    "tugraph/tugraph-runtime-centos7:4.5.1"
    "redis:7-alpine"
    "elasticsearch:8.11.0"
    "postgres:15-alpine"
    "python:3.11-slim"
)

for image in "${core_kg_images[@]}"; do
    if [[ -n "${KG_IMAGES[$image]}" ]]; then
        description="${KG_IMAGES[$image]}"
        log_info "🚀 拉取核心镜像: ${image} (${description})"

        if docker pull "${image}" >/dev/null 2>&1; then
            log_success "✓ ${image} 拉取成功"
            ((pulled_count++))
        else
            log_warning "✗ ${image} 拉取失败，可能是网络问题或镜像不存在"
            ((failed_count++))
        fi
        echo ""
    fi
done

# 拉取其他可选的知识图谱镜像
log_info "📚 拉取可选知识图谱镜像"
echo ""

for image in "${!KG_IMAGES[@]}"; do
    # 跳过已拉取的核心镜像
    skip=false
    for core in "${core_kg_images[@]}"; do
        if [[ "$image" == "$core" ]]; then
            skip=true
            break
        fi
    done

    if [[ "$skip" == false ]]; then
        description="${KG_IMAGES[$image]}"
        log_info "📦 拉取可选镜像: ${image} (${description})"

        if docker pull "${image}" >/dev/null 2>&1; then
            log_success "✓ ${image} 拉取成功"
            ((pulled_count++))
        else
            log_warning "✗ ${image} 拉取失败，跳过"
            ((failed_count++))
        fi
        echo ""
    fi
done

# 显示最终结果
echo "===================================="
log_info "知识图谱镜像拉取完成！"
echo ""

echo "📊 拉取统计:"
echo "   总镜像数: ${total_images}"
echo "   成功拉取: ${pulled_count}"
echo "   拉取失败: ${failed_count}"
echo ""

# 显示已拉取的知识图谱相关镜像
echo "🕸️ 知识图谱相关镜像列表:"
docker images --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}" | grep -E "(tugraph|neo4j|arangodb|janusgraph|gremlin)"

echo ""
echo "🚀 TuGraph知识图谱启动命令:"
echo "   docker run -d \\"
echo "     --name tugraph-db \\"
echo "     -p 9090:9090 \\"
echo "     -p 7687:7687 \\"
echo "     -v \$(pwd)/data/tugraph:/var/lib/tugraph \\"
echo "     tugraph/tugraph-runtime-centos7:4.5.1"
echo ""

echo "🔗 配套服务启动命令:"
echo "   docker-compose up -d redis elasticsearch"
echo "   docker-compose up -d postgres"
echo ""

echo "📖 TuGraph管理界面:"
echo "   Web UI: http://localhost:9090"
echo "   Bolt协议: bolt://localhost:7687"
echo ""

if [ $pulled_count -gt 0 ]; then
    log_success "🎉 知识图谱Docker镜像环境准备完成！"
    echo ""
    echo "📋 下一步操作建议:"
    echo "1. 启动TuGraph数据库: docker run -d --name tugraph-db tugraph/tugraph-runtime-centos7:4.5.1"
    echo "2. 配置知识图谱服务: 修改项目中的配置文件"
    echo "3. 启动知识图谱API: python scripts/knowledge_retrieval_service.py"
    echo "4. 测试图数据导入: 使用现有的迁移脚本"
else
    log_warning "⚠️ 未成功拉取任何镜像，请检查网络连接"
fi

echo ""
log_success "脚本执行完成！"