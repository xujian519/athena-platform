#!/bin/bash
# Athena多模态文件系统 - 快速部署脚本
# Quick Deployment Script for Athena Multimodal File System

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 配置
PROJECT_ROOT="/Users/xujian/Athena工作平台"
DOMAIN="athena.multimodal.ai"

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

log_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

# 显示部署横幅
show_banner() {
    echo -e "${CYAN}"
    echo "========================================================"
    echo "    🚀 Athena多模态文件系统快速部署"
    echo "========================================================"
    echo -e "${NC}"
    echo -e "${BLUE}部署信息:${NC}"
    echo -e "  📅 开始时间: $(date)"
    echo -e "  🌍 环境: ${YELLOW}production${NC}"
    echo -e "  🌐 域名: ${YELLOW}${DOMAIN}${NC}"
    echo ""
}

# 检查Docker环境
check_docker() {
    log_step "检查Docker环境..."

    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi

    if ! docker info >/dev/null 2>&1; then
        log_error "Docker守护进程未运行，请启动Docker"
        exit 1
    fi

    log_success "Docker环境检查通过"
}

# 创建必要目录
create_directories() {
    log_step "创建部署目录..."

    # 创建数据目录
    mkdir -p "${PROJECT_ROOT}/data/{postgres,redis,qdrant,uploads}"
    mkdir -p "${PROJECT_ROOT}/logs/{deployment,monitoring,backup}"
    mkdir -p "${PROJECT_ROOT}/config/{nginx,ssl}"

    log_success "目录创建完成"
}

# 创建简化的Docker Compose配置
create_docker_compose() {
    log_step "创建Docker Compose配置..."

    cat > "${PROJECT_ROOT}/docker-compose.quick.yml" << 'EOF'
version: '3.8'

services:
  # API网关
  api-gateway:
    image: nginx:alpine
    container_name: athena-api-gateway
    ports:
      - "8020:80"
    volumes:
      - ./config/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - xiao-nuo-control
      - athena-platform
    networks:
      - athena-network
    restart: unless-stopped

  # 小诺控制中心
  xiao-nuo-control:
    build:
      context: ./services/xiao-nuo-control
      dockerfile: Dockerfile
    container_name: athena-xiao-nuo-control
    ports:
      - "9001:8000"
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=postgresql://athena_user:athena_password@postgres:5432/athena_db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    networks:
      - athena-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Athena平台管理
  athena-platform:
    build:
      context: ./services/athena-platform
      dockerfile: Dockerfile
    container_name: athena-platform-manager
    ports:
      - "9000:8000"
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=postgresql://athena_user:athena_password@postgres:5432/athena_db
      - REDIS_URL=redis://redis:6379/1
    depends_on:
      - postgres
      - redis
    networks:
      - athena-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # PostgreSQL数据库
  postgres:
    image: postgres:14-alpine
    container_name: athena-postgres
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_DB=athena_db
      - POSTGRES_USER=athena_user
      - POSTGRES_PASSWORD=athena_password
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
    networks:
      - athena-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U athena_user -d athena_db"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Redis缓存
  redis:
    image: redis:7-alpine
    container_name: athena-redis
    ports:
      - "6379:6379"
    volumes:
      - ./data/redis:/data
    networks:
      - athena-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  # 监控服务
  platform-monitor:
    build:
      context: ./services/platform-monitor
      dockerfile: Dockerfile
    container_name: athena-platform-monitor
    ports:
      - "9090:8000"
    environment:
      - ENVIRONMENT=production
    networks:
      - athena-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  athena-network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
EOF

    log_success "Docker Compose配置创建完成"
}

# 创建Nginx配置
create_nginx_config() {
    log_step "创建Nginx配置..."

    cat > "${PROJECT_ROOT}/config/nginx/nginx.conf" << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream api_backend {
        server xiao-nuo-control:8000;
        server athena-platform:8000;
    }

    server {
        listen 80;
        server_name localhost;

        location / {
            proxy_pass http://api_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
EOF

    log_success "Nginx配置创建完成"
}

# 创建简单的健康检查服务
create_health_services() {
    log_step "创建健康检查服务..."

    # 创建小诺控制中心Dockerfile
    mkdir -p "${PROJECT_ROOT}/services/xiao-nuo-control"
    cat > "${PROJECT_ROOT}/services/xiao-nuo-control/Dockerfile" << 'EOF'
FROM python:3.9-slim

WORKDIR /app

RUN pip install fastapi uvicorn

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

    cat > "${PROJECT_ROOT}/services/xiao-nuo-control/main.py" << 'EOF'
from fastapi import FastAPI

app = FastAPI(title="小诺控制中心", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "小诺控制中心运行正常", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "xiao-nuo-control"}
EOF

    # 创建Athena平台管理Dockerfile
    mkdir -p "${PROJECT_ROOT}/services/athena-platform"
    cat > "${PROJECT_ROOT}/services/athena-platform/Dockerfile" << 'EOF'
FROM python:3.9-slim

WORKDIR /app

RUN pip install fastapi uvicorn

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

    cat > "${PROJECT_ROOT}/services/athena-platform/main.py" << 'EOF'
from fastapi import FastAPI

app = FastAPI(title="Athena平台管理", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "Athena平台管理运行正常", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "athena-platform"}
EOF

    # 创建平台监控服务Dockerfile
    mkdir -p "${PROJECT_ROOT}/services/platform-monitor"
    cat > "${PROJECT_ROOT}/services/platform-monitor/Dockerfile" << 'EOF'
FROM python:3.9-slim

WORKDIR /app

RUN pip install fastapi uvicorn

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

    cat > "${PROJECT_ROOT}/services/platform-monitor/main.py" << 'EOF'
from fastapi import FastAPI

app = FastAPI(title="平台监控", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "平台监控服务运行正常", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "platform-monitor"}
EOF

    log_success "健康检查服务创建完成"
}

# 构建和启动服务
deploy_services() {
    log_step "构建和启动服务..."

    cd "${PROJECT_ROOT}"

    # 停止现有服务
    docker-compose -f docker-compose.quick.yml down 2>/dev/null || true

    # 构建并启动服务
    docker-compose -f docker-compose.quick.yml up -d --build

    log_success "服务部署完成"
}

# 等待服务启动
wait_for_services() {
    log_step "等待服务启动..."

    sleep 30

    log_success "服务启动等待完成"
}

# 健康检查
health_check() {
    log_step "执行健康检查..."

    local services=("8020" "9001" "9000" "9090")
    local healthy=0

    for port in "${services[@]}"; do
        if curl -f "http://localhost:$port/health" >/dev/null 2>&1; then
            log_success "端口 $port 服务健康"
            healthy=$((healthy + 1))
        else
            log_warning "端口 $port 服务未就绪"
        fi
    done

    log_info "健康服务数量: $healthy/${#services[@]}"
}

# 显示部署结果
show_results() {
    echo ""
    echo -e "${GREEN}🎉 部署完成！${NC}"
    echo ""
    echo -e "${CYAN}📋 访问地址:${NC}"
    echo -e "  🌐 主站: ${YELLOW}http://localhost:8020${NC}"
    echo -e "  🤖 小诺控制: ${YELLOW}http://localhost:9001${NC}"
    echo -e "  🛡️ 平台管理: ${YELLOW}http://localhost:9000${NC}"
    echo -e "  📊 监控服务: ${YELLOW}http://localhost:9090${NC}"
    echo ""
    echo -e "${CYAN}🔧 管理命令:${NC}"
    echo -e "  📊 查看状态: ${YELLOW}cd ${PROJECT_ROOT} && docker-compose -f docker-compose.quick.yml ps${NC}"
    echo -e "  📋 查看日志: ${YELLOW}cd ${PROJECT_ROOT} && docker-compose -f docker-compose.quick.yml logs -f${NC}"
    echo -e "  🔄 重启服务: ${YELLOW}cd ${PROJECT_ROOT} && docker-compose -f docker-compose.quick.yml restart${NC}"
    echo -e "  🛑 停止服务: ${YELLOW}cd ${PROJECT_ROOT} && docker-compose -f docker-compose.quick.yml down${NC}"
    echo ""
}

# 主函数
main() {
    show_banner

    check_docker
    create_directories
    create_docker_compose
    create_nginx_config
    create_health_services
    deploy_services
    wait_for_services
    health_check
    show_results

    log_success "Athena多模态文件系统快速部署完成！"
}

# 错误处理
trap 'log_error "部署过程中发生错误"; exit 1' ERR

# 执行主函数
main "$@"