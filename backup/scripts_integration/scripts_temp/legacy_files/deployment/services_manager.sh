#!/bin/bash
# Athena工作平台服务管理脚本
# 支持Docker服务和本地服务（Neo4j）的统一管理

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目配置
PROJECT_ROOT="/Users/xujian/Athena工作平台"
DOCKER_DIR="$PROJECT_ROOT/docker/compose"
COMPOSE_FILE="base-updated.yml"

# 检查服务状态
check_service_status() {
    echo -e "${BLUE}📊 检查服务状态...${NC}\n"
    
    # 检查本地Neo4j
    echo -e "${YELLOW}Neo4j (本地安装):${NC}"
    if pgrep -x "neo4j" > /dev/null; then
        echo -e "  ${GREEN}✅ 运行中${NC}"
        echo -e "  - HTTP: http://localhost:7474"
        echo -e "  - Bolt: bolt://localhost:7687"
    else
        echo -e "  ${RED}❌ 未运行${NC}"
    fi
    
    echo ""
    
    # 检查Docker服务
    if docker ps >/dev/null 2>&1; then
        cd "$DOCKER_DIR"
        echo -e "${YELLOW}Docker服务:${NC}"
        docker-compose -f $COMPOSE_FILE ps
    else
        echo -e "${RED}Docker未运行${NC}"
    fi
}

# 启动所有服务
start_all() {
    echo -e "${BLUE}🚀 启动所有服务...${NC}\n"
    
    # 启动本地Neo4j
    echo -e "${YELLOW}启动Neo4j...${NC}"
    if ! pgrep -x "neo4j" > /dev/null; then
        neo4j start
        echo -e "${GREEN}✅ Neo4j已启动${NC}"
    else
        echo -e "${YELLOW}Neo4j已在运行${NC}"
    fi
    
    echo ""
    
    # 启动Docker服务
    echo -e "${YELLOW}启动Docker服务...${NC}"
    cd "$DOCKER_DIR"
    
    # 创建环境变量文件（如果不存在）
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
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

# Elasticsearch配置（可选）
ELASTICSEARCH_PORT=9200

# MinIO配置（可选）
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
MINIO_API_PORT=9000
MINIO_CONSOLE_PORT=9001

# 本地Neo4j配置
NEO4J_HTTP_PORT=7474
NEO4J_BOLT_PORT=7687
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4j
EOF
        echo -e "${GREEN}✅ 环境变量文件已创建${NC}"
    fi
    
    # 创建网络（如果不存在）
    docker network create athena_network 2>/dev/null || true
    
    # 启动服务
    docker-compose -f $COMPOSE_FILE up -d
    
    # 等待服务启动
    echo -e "\n${YELLOW}⏳ 等待服务启动...${NC}"
    sleep 5
    
    echo -e "\n${GREEN}✅ 所有服务启动完成！${NC}"
    echo -e "\n${BLUE}📝 服务访问地址:${NC}"
    echo -e "  - PostgreSQL: localhost:5432"
    echo -e "  - Redis: localhost:6379"
    echo -e "  - Qdrant: http://localhost:6333"
    echo -e "  - Qdrant UI: http://localhost:6334"
    echo -e "  - Neo4j: http://localhost:7474"
    echo -e "  - Neo4j Browser: http://localhost:7474/browser"
}

# 停止所有服务
stop_all() {
    echo -e "${BLUE}🛑 停止所有服务...${NC}\n"
    
    # 停止Docker服务
    echo -e "${YELLOW}停止Docker服务...${NC}"
    cd "$DOCKER_DIR"
    docker-compose -f $COMPOSE_FILE down
    
    # 询问是否停止Neo4j
    echo -e "\n${YELLOW}是否停止本地Neo4j? (y/N):${NC}"
    read -p "" -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        neo4j stop
        echo -e "${GREEN}✅ Neo4j已停止${NC}"
    else
        echo -e "${YELLOW}Neo4j保持运行${NC}"
    fi
    
    echo -e "\n${GREEN}✅ 服务停止完成${NC}"
}

# 重启所有服务
restart_all() {
    echo -e "${BLUE}🔄 重启所有服务...${NC}\n"
    stop_all
    sleep 2
    start_all
}

# 清理数据
clean_data() {
    echo -e "${RED}⚠️ 警告：这将删除所有Docker数据！${NC}"
    echo -e "${YELLOW}Neo4j数据不会被影响（本地管理）${NC}\n"
    read -p "确定要继续吗？(y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd "$DOCKER_DIR"
        docker-compose -f $COMPOSE_FILE down -v
        docker volume prune -f
        echo -e "\n${GREEN}✅ Docker数据清理完成${NC}"
    else
        echo -e "${YELLOW}取消操作${NC}"
    fi
}

# 查看日志
view_logs() {
    service=$1
    cd "$DOCKER_DIR"
    
    if [ -z "$service" ]; then
        echo -e "${BLUE}📋 可用服务：${NC}"
        docker-compose -f $COMPOSE_FILE config --services
        echo -e "\n${BLUE}使用方法：${NC}"
        echo -e "  $0 logs [服务名]"
        echo -e "\n${BLUE}本地服务：${NC}"
        echo -e "  Neo4j: neo4j logs"
    else
        if [ "$service" = "neo4j" ]; then
            neo4j logs --tail=100
        else
            docker-compose -f $COMPOSE_FILE logs -f "$service"
        fi
    fi
}

# 数据库管理
manage_databases() {
    echo -e "\n${BLUE}🗄️ 数据库管理${NC}"
    echo -e "1. PostgreSQL - 连接: psql -h localhost -U postgres -d patent_db"
    echo -e "2. Neo4j - 浏览器: http://localhost:7474/browser"
    echo -e "3. Redis - CLI: redis-cli"
    echo -e "4. Qdrant - REST: http://localhost:6333"
    
    # 提供快速连接选项
    echo -e "\n${YELLOW}快速连接选项：${NC}"
    echo -e "a) 连接PostgreSQL"
    echo -e "b) 打开Neo4j浏览器"
    echo -e "c) 连接Redis"
    echo -e "d) 查看Qdrant集合"
    echo -e "q) 返回"
    
    read -p "选择: " choice
    
    case $choice in
        a)
            PGPASSWORD=postgres123 psql -h localhost -U postgres -d patent_db
            ;;
        b)
            open http://localhost:7474/browser
            ;;
        c)
            redis-cli
            ;;
        d)
            curl -X GET "http://localhost:6333/collections" | python3 -m json.tool
            ;;
        q)
            ;;
    esac
}

# 显示帮助信息
show_help() {
    echo -e "\n${GREEN}Athena工作平台服务管理脚本${NC}\n"
    echo -e "用法: $0 [命令]\n"
    echo -e "命令:"
    echo -e "  ${YELLOW}status${NC}       查看所有服务状态"
    echo -e "  ${YELLOW}start${NC}        启动所有服务"
    echo -e "  ${YELLOW}stop${NC}         停止所有服务"
    echo -e "  ${YELLOW}restart${NC}      重启所有服务"
    echo -e "  ${YELLOW}clean${NC}        清理Docker数据"
    echo -e "  ${YELLOW}logs${NC}         [服务名] 查看日志"
    echo -e "  ${YELLOW}db${NC}           数据库管理"
    echo -e "  ${YELLOW}help${NC}         显示帮助信息\n"
    
    echo -e "${BLUE}本地服务：${NC}"
    echo -e "  - Neo4j: 使用brew安装，通过neo4j命令管理"
    echo -e "\n${BLUE}Docker服务：${NC}"
    echo -e "  - PostgreSQL, Redis, Qdrant等"
}

# 主函数
main() {
    case "${1:-help}" in
        status)
            check_service_status
            ;;
        start)
            start_all
            ;;
        stop)
            stop_all
            ;;
        restart)
            restart_all
            ;;
        clean)
            clean_data
            ;;
        logs)
            view_logs "$2"
            ;;
        db)
            manage_databases
            ;;
        help|*)
            show_help
            ;;
    esac
}

# 执行主函数
main "$@"