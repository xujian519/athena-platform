#!/bin/bash

# 专利智能检索API生产部署脚本
# Patent Retrieval API Production Deployment Script

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查依赖
check_dependencies() {
    log_info "检查系统依赖..."

    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi

    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi

    # 检查Docker服务状态
    if ! docker info &> /dev/null; then
        log_error "Docker服务未运行，请启动Docker服务"
        exit 1
    fi

    log_success "系统依赖检查通过"
}

# 环境准备
prepare_environment() {
    log_info "准备生产环境..."

    # 创建必要的目录
    mkdir -p logs
    mkdir -p config
    mkdir -p monitoring
    mkdir -p infrastructure/nginx/ssl

    # 设置权限
    chmod 755 logs config monitoring
    chmod +x dev/scripts/*.sh

    # 创建监控配置
    cat > infrastructure/monitoring/prometheus.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'patent-api'
    static_configs:
      - targets: ['patent-api:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'infrastructure/infrastructure/nginx'
    static_configs:
      - targets: ['nginx:80']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'qdrant'
    static_configs:
      - targets: ['qdrant:6333']
    metrics_path: '/metrics'
    scrape_interval: 10s
EOF

    log_success "环境准备完成"
}

# 构建镜像
build_images() {
    log_info "构建Docker镜像..."

    cd /Users/xujian/Athena工作平台

    # 构建API镜像
    docker build -f production/Dockerfile -t athena-patent-api:latest .

    log_success "Docker镜像构建完成"
}

# 数据备份
backup_data() {
    log_info "备份现有数据..."

    # 创建备份目录
    BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"

    # 备份Qdrant数据
    if docker ps | grep -q athena_qdrant; then
        docker exec athena_qdrant tar -czf /tmp/qdrant_backup.tar.gz -C /qdrant storage
        docker cp athena_qdrant:/tmp/qdrant_backup.tar.gz "$BACKUP_DIR/"
        log_success "Qdrant数据备份完成"
    fi

    # 备份配置文件
    cp -r production "$BACKUP_DIR/"
    log_success "配置文件备份完成"
}

# 启动服务
start_services() {
    log_info "启动生产服务..."

    cd /Users/xujian/Athena工作平台/production

    # 停止现有服务
    docker-compose down

    # 启动新服务
    docker-compose up -d

    log_success "生产服务启动完成"
}

# 健康检查
health_check() {
    log_info "执行健康检查..."

    # 等待服务启动
    sleep 30

    # 检查API服务
    API_URL="http://localhost:8000"
    if curl -f "$API_URL/health" &> /dev/null; then
        log_success "API服务健康检查通过"
    else
        log_error "API服务健康检查失败"
        return 1
    fi

    # 检查Qdrant服务
    if curl -f "http://localhost:6333/collections" &> /dev/null; then
        log_success "Qdrant服务健康检查通过"
    else
        log_warning "Qdrant服务健康检查失败"
    fi

    # 检查Nginx服务
    if curl -f "http://localhost/health" &> /dev/null; then
        log_success "Nginx服务健康检查通过"
    else
        log_warning "Nginx服务健康检查失败"
    fi
}

# 性能测试
performance_test() {
    log_info "执行性能测试..."

    # 简单的并发测试
    API_URL="http://localhost/api/v1/search"

    # 测试数据
    TEST_DATA='{
        "query": "发明专利的创造性判断标准",
        "top_k": 5,
        "search_type": "hybrid"
    }'

    # 执行10个并发请求
    for i in {1..10}; do
        curl -s -X POST "$API_URL" \
             -H "Content-Type: application/json" \
             -d "$TEST_DATA" \
             -o "/tmp/test_$i.json" &
    done

    wait

    # 检查结果
    SUCCESS_COUNT=0
    for i in {1..10}; do
        if [ -f "/tmp/test_$i.json" ] && grep -q '"total_results"' "/tmp/test_$i.json"; then
            ((SUCCESS_COUNT++))
        fi
        rm -f "/tmp/test_$i.json"
    done

    if [ $SUCCESS_COUNT -eq 10 ]; then
        log_success "性能测试通过 ($SUCCESS_COUNT/10 请求成功)"
    else
        log_warning "性能测试部分通过 ($SUCCESS_COUNT/10 请求成功)"
    fi
}

# 生成部署报告
generate_report() {
    log_info "生成部署报告..."

    REPORT_FILE="production/deployment_report_$(date +%Y%m%d_%H%M%S).md"

    cat > "$REPORT_FILE" << EOF
# 专利智能检索API生产部署报告

## 部署信息
- **部署时间**: $(date)
- **部署环境**: 生产环境
- **版本**: 1.0.0

## 服务状态
- **API服务**: http://localhost:8000
- **Nginx代理**: http://localhost
- **Qdrant向量库**: http://localhost:6333
- **Prometheus监控**: http://localhost:9090
- **Grafana仪表板**: http://localhost:3000 (admin/admin123)

## 数据统计
- **向量集合**: $(curl -s http://localhost:6333/collections | python3 -c "import json,sys; data=json.load(sys.stdin); print(len(data['result']['collections']))" 2>/dev/null || echo "N/A")
- **专利相关集合**: $(curl -s http://localhost:6333/collections | python3 -c "import json,sys; data=json.load(sys.stdin); patent_cols=[c for c in data['result']['collections'] if 'patent' in c['name'].lower()]; print(len(patent_cols))" 2>/dev/null || echo "N/A")

## 监控指标
- **系统健康**: $(curl -s http://localhost:8000/health | python3 -c "import json,sys; data=json.load(sys.stdin); print(data.get('status', 'unknown'))" 2>/dev/null || echo "N/A")
- **API响应时间**: 通过Grafana查看详细指标

## 访问方式
### API端点
- 专利检索: POST /api/v1/search
- 语义分析: POST /api/v1/semantic-analysis
- 案例推荐: POST /api/v1/case-recommendation
- 系统统计: GET /api/v1/stats
- 健康检查: GET /health

### 文档
- API文档: http://localhost/docs
- ReDoc文档: http://localhost/redoc

## 注意事项
1. 定期检查服务状态
2. 监控系统资源使用情况
3. 定期备份重要数据
4. 及时更新安全补丁

## 故障排除
- 查看日志: docker-compose logs -f patent-api
- 重启服务: docker-compose restart patent-api
- 检查状态: docker-compose ps
EOF

    log_success "部署报告生成完成: $REPORT_FILE"
}

# 主函数
main() {
    log_info "开始专利智能检索API生产部署"
    log_info "====================================="

    # 执行部署步骤
    check_dependencies
    prepare_environment
    backup_data
    build_images
    start_services

    # 等待服务完全启动
    log_info "等待服务启动..."
    sleep 60

    health_check
    performance_test
    generate_report

    log_info "====================================="
    log_success "生产部署完成！"
    log_info "API服务: http://localhost:8000"
    log_info "API文档: http://localhost/docs"
    log_info "监控面板: http://localhost:3000"
    log_warning "请查看部署报告了解详细信息"
}

# 错误处理
trap 'log_error "部署过程中发生错误，请检查日志"; exit 1' ERR

# 执行主函数
main "$@"