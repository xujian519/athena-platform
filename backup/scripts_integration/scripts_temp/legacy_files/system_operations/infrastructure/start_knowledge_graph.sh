#!/bin/bash
# Athena知识图谱服务快速启动脚本

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

echo "🕸️ Athena知识图谱服务启动"
echo "======================="
echo ""

# 检查Docker镜像
log_info "检查知识图谱相关Docker镜像..."
REQUIRED_IMAGES=(
    "tugraph/tugraph-runtime-centos7:4.5.1"
    "elasticsearch:8.11.0"
    "kibana:8.11.0"
    "postgres:15-alpine"
    "redis:7-alpine"
    "python:3.11-slim"
)

missing_images=()
for image in "${REQUIRED_IMAGES[@]}"; do
    if ! docker image inspect "$image" >/dev/null 2>&1; then
        missing_images+=("$image")
    fi
done

if [ ${#missing_images[@]} -gt 0 ]; then
    log_warning "缺少以下Docker镜像:"
    for image in "${missing_images[@]}"; do
        echo "   - $image"
    done
    echo ""
    log_info "正在拉取缺失镜像..."
    for image in "${missing_images[@]}"; do
        log_info "拉取: $image"
        docker pull "$image"
    done
    log_success "镜像拉取完成"
else
    log_success "所有必需镜像已就绪"
fi

echo ""

# 创建必要的目录
log_info "创建知识图谱数据目录..."
mkdir -p deployment/knowledge_graph/{config,data,logs,notebooks,init/postgres-kg,monitoring}
mkdir -p data/{tugraph,elasticsearch,postgres_knowledge,redis_cache}

# 创建TuGraph配置文件
cat > deployment/knowledge_graph/config/tugraph/tugraph.json << 'EOF'
{
  "server": {
    "host": "0.0.0.0",
    "rest_port": 9090,
    "rpc_port": 9091,
    "bolt_port": 7687,
    "enable_tls": false,
    "enable_auth": false
  },
  "audit_log": {
    "enable": true,
    "log_path": "/var/log/tugraph/audit.log"
  },
  "graph": {
    "default_graph": "athena_kg",
    "max_vertex_num": 10000000,
    "max_edge_num": 100000000
  }
}
EOF

# 创建Prometheus配置
cat > deployment/knowledge_graph/monitoring/prometheus-kg.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'knowledge-graph-api'
    static_configs:
      - targets: ['knowledge-graph-api:9030']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'tugraph-db'
    static_configs:
      - targets: ['tugraph-db:9090']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'elasticsearch'
    static_configs:
      - targets: ['elasticsearch:9200']
    metrics_path: '/_prometheus/metrics'
    scrape_interval: 30s
EOF

log_success "配置文件创建完成"

# 切换到知识图谱部署目录
cd deployment/knowledge_graph

# 启动服务
echo ""
log_info "启动知识图谱服务栈..."

# 分阶段启动服务
log_info "1. 启动基础数据服务..."
docker-compose up -d tugraph-db elasticsearch redis-kg postgres-kg

# 等待基础服务启动
log_info "等待基础服务启动完成..."
sleep 30

# 检查基础服务状态
log_info "检查基础服务状态..."
for service in tugraph-db elasticsearch redis-kg postgres-kg; do
    if docker-compose ps "$service" | grep -q "Up"; then
        log_success "✓ $service 启动成功"
    else
        log_warning "✗ $service 启动失败"
    fi
done

echo ""
log_info "2. 启动应用服务..."
docker-compose up -d kibana knowledge-graph-api prometheus-kg grafana-kg jupyter-kg

# 等待应用服务启动
sleep 20

# 检查所有服务状态
echo ""
log_info "检查所有服务状态..."
docker-compose ps

echo ""
echo "========================================"
log_success "知识图谱服务启动完成！"
echo ""

echo "🔗 服务访问地址:"
echo "   TuGraph图数据库:     http://localhost:9090"
echo "   Bolt协议:           bolt://localhost:7687"
echo "   Elasticsearch:      http://localhost:9200"
echo "   Kibana可视化:       http://localhost:5601"
echo "   知识图谱API:        http://localhost:9030"
echo "   Jupyter Notebook:   http://localhost:8889"
echo "   Prometheus监控:     http://localhost:9091"
echo "   Grafana仪表板:      http://localhost:3001 (admin/admin123)"
echo "   PostgreSQL:         localhost:5433"
echo "   Redis缓存:          localhost:6380"
echo ""

echo "📖 API测试命令:"
echo "   curl http://localhost:9030/health"
echo "   curl http://localhost:9030/api/v1/graphs"
echo ""

echo "🛠️ 管理命令:"
echo "   查看日志: docker-compose logs -f [service_name]"
echo "   停止服务: docker-compose down"
echo "   重启服务: docker-compose restart [service_name]"
echo ""

log_success "Athena知识图谱环境已就绪！"