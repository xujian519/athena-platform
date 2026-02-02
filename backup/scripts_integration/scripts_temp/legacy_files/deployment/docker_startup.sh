#!/bin/bash
# Athena工作平台 Docker 快速启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="/Users/xujian/Athena工作平台"
DOCKER_DIR="$PROJECT_ROOT/docker/compose"

# 检查Docker是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker 未安装，请先安装 Docker${NC}"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo -e "${RED}❌ Docker Compose 未安装，请先安装 Docker Compose${NC}"
        exit 1
    fi
}

# 创建网络
create_network() {
    echo -e "${YELLOW}🔧 创建 Docker 网络...${NC}"
    docker network create athena_network 2>/dev/null || true
    docker network inspect athena_network >/dev/null 2>&1 || {
        echo -e "${RED}❌ 创建网络失败${NC}"
        exit 1
    }
}

# 启动基础服务
start_base() {
    echo -e "${YELLOW}🚀 启动基础服务...${NC}"
    cd "$DOCKER_DIR"
    
    # 检查环境变量文件
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        echo -e "${YELLOW}📝 创建环境变量文件...${NC}"
        cat > "$PROJECT_ROOT/.env" << EOF
# 数据库配置
POSTGRES_DB=patent_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123
POSTGRES_PORT=5432

# Redis配置
REDIS_PASSWORD=redis123
REDIS_PORT=6379

# Qdrant配置
QDRANT_PORT=6333

# Neo4j配置
NEO4J_PASSWORD=neo4j123
NEO4J_HTTP_PORT=7474
NEO4J_BOLT_PORT=7687

# Elasticsearch配置
ELASTICSEARCH_PORT=9200
ELASTIC_PASSWORD=elastic123

# 应用配置
ATHENA_PORT=8000
API_GATEWAY_PORT=8080
CRAWLER_PORT=8300
EOF
    fi
    
    # 启动服务
    docker-compose -f base.yml up -d
    
    # 等待服务就绪
    echo -e "${YELLOW}⏳ 等待服务启动...${NC}"
    sleep 10
    
    # 检查服务状态
    docker-compose -f base.yml ps
}

# 启动开发环境
start_dev() {
    echo -e "${YELLOW}🛠️ 启动开发环境...${NC}"
    cd "$DOCKER_DIR"
    
    # 先启动基础服务
    start_base
    
    # 启动开发服务
    docker-compose -f base.yml -f development.yml up -d
    
    echo -e "\n${GREEN}✅ 开发环境启动完成！${NC}"
    echo -e "${GREEN}📝 服务访问地址:${NC}"
    echo -e "  - Athena应用: http://localhost:8000"
    echo -e "  - API网关: http://localhost:8080"
    echo -e "  - 爬虫服务: http://localhost:8300"
    echo -e "  - Jupyter: http://localhost:8888 (token: athena)"
    echo -e "  - pgAdmin: http://localhost:5050"
    echo -e "  - Redis Commander: http://localhost:8081"
}

# 启动生产环境
start_prod() {
    echo -e "${YELLOW}🚀 启动生产环境...${NC}"
    cd "$DOCKER_DIR"
    
    # 先启动基础服务
    start_base
    
    # 启动生产服务
    docker-compose -f base.yml -f production.yml --profile prod up -d
    
    echo -e "\n${GREEN}✅ 生产环境启动完成！${NC}"
    echo -e "${GREEN}📝 服务访问地址:${NC}"
    echo -e "  - API网关: http://localhost"
    echo -e "  - HTTPS: https://localhost"
    echo -e "  - Prometheus: http://localhost:9090"
    echo -e "  - Grafana: http://localhost:3000"
}

# 启动监控服务
start_monitoring() {
    echo -e "${YELLOW}📊 启动监控服务...${NC}"
    cd "$DOCKER_DIR"
    
    docker-compose -f production.yml --profile monitoring up -d
    
    echo -e "\n${GREEN}✅ 监控服务启动完成！${NC}"
    echo -e "  - Prometheus: http://localhost:9090"
    echo -e "  - Grafana: http://localhost:3000"
}

# 停止所有服务
stop_all() {
    echo -e "${YELLOW}🛑 停止所有服务...${NC}"
    cd "$DOCKER_DIR"
    
    # 停止并移除所有容器
    docker-compose -f base.yml -f development.yml -f production.yml down --remove-orphans
    
    echo -e "${GREEN}✅ 所有服务已停止${NC}"
}

# 清理数据
clean_data() {
    echo -e "${RED}⚠️ 警告：这将删除所有数据！${NC}"
    read -p "确定要继续吗？(y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd "$DOCKER_DIR"
        
        # 停止服务
        docker-compose -f base.yml -f development.yml -f production.yml down -v
        
        # 删除卷
        docker volume prune -f
        
        echo -e "${GREEN}✅ 数据清理完成${NC}"
    else
        echo -e "${YELLOW}取消操作${NC}"
    fi
}

# 查看日志
view_logs() {
    service=$1
    cd "$DOCKER_DIR"
    
    if [ -z "$service" ]; then
        docker-compose -f base.yml logs -f
    else
        docker-compose -f base.yml logs -f "$service"
    fi
}

# 显示帮助信息
show_help() {
    echo -e "\n${GREEN}Athena工作平台 Docker 管理脚本${NC}\n"
    echo -e "用法: $0 [命令]\n"
    echo -e "命令:"
    echo -e "  ${YELLOW}base${NC}       启动基础服务"
    echo -e "  ${YELLOW}dev${NC}        启动开发环境"
    echo -e "  ${YELLOW}prod${NC}       启动生产环境"
    echo -e "  ${YELLOW}monitoring${NC} 启动监控服务"
    echo -e "  ${YELLOW}stop${NC}       停止所有服务"
    echo -e "  ${YELLOW}clean${NC}      清理所有数据"
    echo -e "  ${YELLOW}logs${NC}       [服务名] 查看日志"
    echo -e "  ${YELLOW}help${NC}       显示帮助信息\n"
}

# 主函数
main() {
    check_docker
    create_network
    
    case "${1:-help}" in
        base)
            start_base
            ;;
        dev)
            start_dev
            ;;
        prod)
            start_prod
            ;;
        monitoring)
            start_monitoring
            ;;
        stop)
            stop_all
            ;;
        clean)
            clean_data
            ;;
        logs)
            view_logs "$2"
            ;;
        help|*)
            show_help
            ;;
    esac
}

# 执行主函数
main "$@"