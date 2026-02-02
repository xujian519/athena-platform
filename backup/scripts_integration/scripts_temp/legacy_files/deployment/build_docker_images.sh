#!/bin/bash
# Docker镜像构建脚本
# Docker Image Build Script for Athena Production

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
REGISTRY="registry.cn-hangzhou.aliyuncs.com/athena"
NAMESPACE="athena-prod"
VERSION="2.0-prod"
BUILD_DATE=$(date +"%Y%m%d_%H%M%S")
GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

# 服务列表
SERVICES=(
    "multimodal-api"
    "dolphin-parser"
    "glm-vision"
    "multimodal-processor"
    "xiao-nuo-control"
    "platform-manager"
    "platform-monitor"
)

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
    log_info "检查Docker环境..."

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

    # 检查Docker守护进程
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker守护进程未运行，请启动Docker"
        exit 1
    fi

    log_success "Docker环境检查完成"
}

# 创建Dockerfile
create_dockerfiles() {
    log_info "创建Dockerfile..."

    # API网关Dockerfile
    cat > "Dockerfile.api-gateway" << EOF
FROM python:3.11-slim

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1 \\
    PYTHONPATH=/app \\
    DEBIAN_FRONTEND=noninteractive

# 安装系统依赖
RUN apt-get update && apt-get install -y \\
    curl \\
    build-essential \\
    libpq-dev \\
    libffi-dev \\
    libssl-dev \\
    && rm -rf /var/lib/apt/lists/*

# 创建应用用户
RUN useradd --create-home --shell /bin/bash athena

# 设置工作目录
WORKDIR /app

# 复制requirements文件
COPY services/requirements.txt requirements.txt

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY services/unified_multimodal_api.py ./
COPY services/multimodal_system_config.yaml ./
COPY services/enhanced_file_format_support.py ./

# 创建必要的目录
RUN mkdir -p logs uploads processed cache && \\
    chown -R athena:athena /app

# 切换到应用用户
USER athena

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \\
    CMD curl -f http://localhost:8020/health || exit 1

# 暴露端口
EXPOSE 8020

# 启动命令
CMD ["gunicorn", "--bind", "0.0.0.0:8020", "--workers", "4", "--timeout", "60", "--keep-alive", "2", "--max-requests", "1000", "--max-requests-jitter", "100", "unified_multimodal_api:app"]
EOF

    # Dolphin解析器Dockerfile
    cat > "Dockerfile.dolphin-parser" << EOF
FROM python:3.11-slim

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1 \\
    PYTHONPATH=/app \\
    DEBIAN_FRONTEND=noninteractive

# 安装系统依赖
RUN apt-get update && apt-get install -y \\
    curl \\
    build-essential \\
    libpq-dev \\
    libffi-dev \\
    libssl-dev \\
    libgl1-mesa-glx \\
    libglib2.0-0 \\
    libsm6 \\
    libxext6 \\
    libxrender-dev \\
    libgomp1 \\
    && rm -rf /var/lib/apt/lists/*

# 创建应用用户
RUN useradd --create-home --shell /bin/bash athena

# 设置工作目录
WORKDIR /app

# 复制requirements文件
COPY services/requirements.txt requirements.txt

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY services/dolphin_config.yaml ./
COPY services/enhanced_file_format_support.py ./

# 创建启动脚本
COPY <<'EOF' /app/startup.sh
#!/bin/bash
echo "启动Dolphin解析服务..."
exec python3 -c "
import os
import subprocess
import sys
from services.enhanced_file_format_support import DolphinDocumentParser

# 启动FastAPI应用
parser = DolphinDocumentParser()
parser.start_service()
"
EOF
    RUN chmod +x /app/startup.sh

# 创建必要的目录
RUN mkdir -p logs cache && \\
    chown -R athena:athena /app

# 切换到应用用户
USER athena

# 健康检查
HEALTHCHECK --interval=20s --timeout=10s --start-period=40s --retries=3 \\
    CMD curl -f http://localhost:8013/health || exit 1

# 暴露端口
EXPOSE 8013

# 启动命令
CMD ["/app/startup.sh"]
EOF

    # GLM视觉服务Dockerfile
    cat > "Dockerfile.glm-vision" << EOF
FROM python:3.11-slim

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1 \\
    PYTHONPATH=/app \\
    DEBIAN_FRONTEND=noninteractive

# 安装系统依赖
RUN apt-get update && apt-get install -y \\
    curl \\
    build-essential \\
    libpq-dev \\
    libffi-dev \\
    libssl-dev \\
    libgl1-mesa-glx \\
    libglib2.0-0 \\
    libsm6 \\
    libxext6 \\
    libxrender-dev \\
    libgomp1 \\
    wget \\
    && rm -rf /var/lib/apt/lists/*

# 创建应用用户
RUN useradd --create-home --shell /bin/bash athena

# 设置工作目录
WORKDIR /app

# 复制requirements文件
COPY services/requirements.txt requirements.txt

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY services/ai-models/glm-full-suite/ ./

# 创建启动脚本
COPY <<'EOF' /app/startup.sh
#!/bin/bash
echo "启动GLM视觉服务..."
exec python3 athena_glm_full_suite_server.py
EOF
    RUN chmod +x /app/startup.sh

# 创建必要的目录
RUN mkdir -p logs models && \\
    chown -R athena:athena /app

# 切换到应用用户
USER athena

# 健康检查
HEALTHCHECK --interval=20s --timeout=10s --start-period=60s --retries=3 \\
    CMD curl -f http://localhost:8091/health || exit 1

# 暴露端口
EXPOSE 8091

# 启动命令
CMD ["/app/startup.sh"]
EOF

    # 多模态处理器Dockerfile
    cat > "Dockerfile.multimodal-processor" << EOF
FROM python:3.11-slim

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1 \\
    PYTHONPATH=/app \\
    DEBIAN_FRONTEND=noninteractive

# 安装系统依赖
RUN apt-get update && apt-get install -y \\
    curl \\
    build-essential \\
    libpq-dev \\
    libffi-dev \\
    libssl-dev \\
    && rm -rf /var/lib/apt/lists/*

# 创建应用用户
RUN useradd --create-home --shell /bin/bash athena

# 设置工作目录
WORKDIR /app

# 复制requirements文件
COPY services/requirements.txt requirements.txt

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY services/multimodal_processing_service.py ./

# 创建启动脚本
COPY <<'EOF' /app/startup.sh
#!/bin/bash
echo "启动多模态处理服务..."
exec python3 multimodal_processing_service.py
EOF
    RUN chmod +x /app/startup.sh

# 创建必要的目录
RUN mkdir -p logs vectors && \\
    chown -R athena:athena /app

# 切换到应用用户
USER athena

# 健康检查
HEALTHCHECK --interval=20s --timeout=10s --start-period=30s --retries=3 \\
    CMD curl -f http://localhost:8012/ || exit 1

# 暴露端口
EXPOSE 8012

# 启动命令
CMD ["/app/startup.sh"]
EOF

    # 小诺控制中心Dockerfile
    cat > "Dockerfile.xiao-nuo-control" << EOF
FROM python:3.11-slim

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1 \\
    PYTHONPATH=/app \\
    DEBIAN_FRONTEND=noninteractive

# 安装系统依赖
RUN apt-get update && apt-get install -y \\
    curl \\
    build-essential \\
    libpq-dev \\
    libffi-dev \\
    libssl-dev \\
    && rm -rf /var/lib/apt/lists/*

# 创建应用用户
RUN useradd --create-home --shell /bin/bash athena

# 设置工作目录
WORKDIR /app

# 复制requirements文件
COPY services/requirements.txt requirements.txt

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY services/xiao_nuo_control.py ./

# 创建启动脚本
COPY <<'EOF' /app/startup.sh
#!/bin/bash
echo "启动小诺控制中心..."
exec python3 xiao_nuo_control.py
EOF
    RUN chmod +x /app/startup.sh

# 创建必要的目录
RUN mkdir -p logs config && \\
    chown -R athena:athena /app

# 切换到应用用户
USER athena

# 健康检查
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \\
    CMD curl -f http://localhost:9001/health || exit 1

# 暴露端口
EXPOSE 9001

# 启动命令
CMD ["/app/startup.sh"]
EOF

    # Athena平台管理器Dockerfile
    cat > "Dockerfile.athena-platform" << EOF
FROM python:3.11-slim

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1 \\
    PYTHONPATH=/app \\
    DEBIAN_FRONTEND=noninteractive

# 安装系统依赖
RUN apt-get update && apt-get install -y \\
    curl \\
    build-essential \\
    libpq-dev \\
    libffi-dev \\
    libssl-dev \\
    && rm -rf /var/lib/apt/lists/*

# 创建应用用户
RUN useradd --create-home --shell /bin/bash athena

# 设置工作目录
WORKDIR /app

# 复制requirements文件
COPY services/requirements.txt requirements.txt

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY services/athena_platform_manager.py ./

# 创建启动脚本
COPY <<'EOF' /app/startup.sh
#!/bin/bash
echo "启动Athena平台管理器..."
exec python3 athena_platform_manager.py
EOF
    RUN chmod +x /app/startup.sh

# 创建必要的目录
RUN mkdir -p logs config && \\
    chown -R athena:athena /app

# 切换到应用用户
USER athena

# 健康检查
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \\
    CMD curl -f http://localhost:9000/health || exit 1

# 暴露端口
EXPOSE 9000

# 启动命令
CMD ["/app/startup.sh"]
EOF

    # 平台监控Dockerfile
    cat > "Dockerfile.platform-monitor" << EOF
FROM python:3.11-slim

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1 \\
    PYTHONPATH=/app \\
    DEBIAN_FRONTEND=noninteractive

# 安装系统依赖
RUN apt-get update && apt-get install -y \\
    curl \\
    build-essential \\
    libpq-dev \\
    libffi-dev \\
    libssl-dev \\
    && rm -rf /var/lib/apt/lists/*

# 创建应用用户
RUN useradd --create-home --shell /bin/bash athena

# 设置工作目录
WORKDIR /app

# 复制requirements文件
COPY services/requirements.txt requirements.txt

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY services/platform_monitor.py ./

# 创建启动脚本
COPY <<'EOF' /app/startup.sh
#!/bin/bash
echo "启动平台监控服务..."
exec python3 platform_monitor.py
EOF
    RUN chmod +x /app/startup.sh

# 创建必要的目录
RUN mkdir -p logs config && \\
    chown -R athena:athena /app

# 切换到应用用户
USER athena

# 健康检查
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \\
    CMD curl -f http://localhost:9090/health || exit 1

# 暴露端口
EXPOSE 9090

# 启动命令
CMD ["/app/startup.sh"]
EOF

    log_success "Dockerfile创建完成"
}

# 构建镜像
build_images() {
    log_info "开始构建Docker镜像..."

    # 构建每个服务的镜像
    for service in "${SERVICES[@]}"; do
        log_info "构建 $service 镜像..."

        case $service in
            "multimodal-api")
                dockerfile="Dockerfile.api-gateway"
                ;;
            "dolphin-parser")
                dockerfile="Dockerfile.dolphin-parser"
                ;;
            "glm-vision")
                dockerfile="Dockerfile.glm-vision"
                ;;
            "multimodal-processor")
                dockerfile="Dockerfile.multimodal-processor"
                ;;
            "xiao-nuo-control")
                dockerfile="Dockerfile.xiao-nuo-control"
                ;;
            "platform-manager")
                dockerfile="Dockerfile.athena-platform"
                ;;
            "platform-monitor")
                dockerfile="Dockerfile.platform-monitor"
                ;;
            *)
                log_error "未知服务: $service"
                continue
                ;;
        esac

        # 构建镜像
        docker build \\
            -f "$dockerfile" \\
            -t "${REGISTRY}/${service}:${VERSION}" \\
            -t "${REGISTRY}/${service}:latest" \\
            --label "com.athena.version=${VERSION}" \\
            --label "com.athena.build-date=${BUILD_DATE}" \\
            --label "com.athena.git-commit=${GIT_COMMIT}" \\
            .

        if [ $? -eq 0 ]; then
            log_success "$service 镜像构建成功"
        else
            log_error "$service 镜像构建失败"
            return 1
        fi
    done

    log_success "所有Docker镜像构建完成"
}

# 推送镜像到仓库
push_images() {
    log_info "推送镜像到仓库..."

    # 检查是否已登录
    if ! docker info | grep -q "Username"; then
        log_error "请先登录Docker仓库: docker login $REGISTRY"
        return 1
    fi

    # 推送每个服务的镜像
    for service in "${SERVICES[@]}"; do
        log_info "推送 $service 镜像..."

        # 推送版本标签
        docker push "${REGISTRY}/${service}:${VERSION}"

        # 推送latest标签
        docker push "${REGISTRY}/${service}:latest"

        if [ $? -eq 0 ]; then
            log_success "$service 镜像推送成功"
        else
            log_error "$service 镜像推送失败"
            return 1
        fi
    done

    log_success "所有镜像推送完成"
}

# 清理旧镜像
cleanup_old_images() {
    log_info "清理旧镜像..."

    # 删除未标记的镜像
    docker image prune -f

    # 删除旧的构建缓存
    docker builder prune -f

    log_success "清理完成"
}

# 生成镜像清单
generate_manifest() {
    log_info "生成镜像清单..."

    manifest_file="docker-manifest-${BUILD_DATE}.json"

    cat > "$manifest_file" << EOF
{
    "build_info": {
        "timestamp": "$(date -Iseconds)",
        "version": "${VERSION}",
        "git_commit": "${GIT_COMMIT}",
        "registry": "${REGISTRY}",
        "namespace": "${NAMESPACE}"
    },
    "services": [
EOF

    # 为每个服务生成清单条目
    for i in "${!SERVICES[@]}"; do
        service="${SERVICES[i]}"
        comma=""
        if [ $i -ne $((${#SERVICES[@]} - 1)) ]; then
            comma=","
        fi

        image_info=$(docker inspect "${REGISTRY}/${service}:${VERSION}" 2>/dev/null | jq '.[0]' 2>/dev/null || echo '{}')
        size=$(echo "$image_info" | jq -r '.Size // "unknown"')

        cat >> "$manifest_file" << EOF
        {
            "name": "${service}",
            "image": "${REGISTRY}/${service}:${VERSION}",
            "size": "${size}"
        }${comma}
EOF
    done

    cat >> "$manifest_file" << EOF
    ]
}
EOF

    log_success "镜像清单生成完成: $manifest_file"
}

# 验证镜像
verify_images() {
    log_info "验证Docker镜像..."

    failed_services=()

    for service in "${SERVICES[@]}"; do
        image="${REGISTRY}/${service}:${VERSION}"

        # 检查镜像是否存在
        if ! docker image inspect "$image" >/dev/null 2>&1; then
            log_error "镜像不存在: $image"
            failed_services+=("$service")
            continue
        fi

        # 检查镜像大小
        size=$(docker image inspect "$image" | jq -r '.[0].Size')
        if [ "$size" = "null" ] || [ "$size" -eq 0 ]; then
            log_warning "镜像大小异常: $image"
            failed_services+=("$service")
            continue
        fi

        log_success "$service 镜像验证通过"
    done

    if [ ${#failed_services[@]} -gt 0 ]; then
        log_error "以下镜像验证失败: ${failed_services[*]}"
        return 1
    fi

    log_success "所有镜像验证通过"
}

# 主函数
main() {
    echo -e "${BLUE}🐳 Athena多模态文件系统Docker镜像构建${NC}"
    echo "============================================"
    echo -e "${CYAN}开始时间: $(date)${NC}"
    echo ""

    # 解析命令行参数
    SKIP_BUILD=false
    SKIP_PUSH=false
    CLEANUP=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-build)
                SKIP_BUILD=true
                shift
                ;;
            --skip-push)
                SKIP_PUSH=true
                shift
                ;;
            --cleanup)
                CLEANUP=true
                shift
                ;;
            --version)
                VERSION="$2"
                shift 2
                ;;
            *)
                echo "未知参数: $1"
                echo "用法: $0 [--skip-build] [--skip-push] [--cleanup] [--version VERSION]"
                exit 1
                ;;
        esac
    done

    echo -e "${BLUE}构建配置:${NC}"
    echo -e "  📦 仓库: ${YELLOW}$REGISTRY${NC}"
    echo -e "  🏷️  版本: ${YELLOW}$VERSION${NC}"
    echo -e "  📅 构建时间: ${YELLOW}$BUILD_DATE${NC}"
    echo -e "  🔗 Git提交: ${YELLOW}$GIT_COMMIT${NC}"
    echo ""

    # 检查依赖
    check_dependencies

    # 创建Dockerfile
    create_dockerfiles

    # 构建镜像
    if [ "$SKIP_BUILD" = false ]; then
        if build_images; then
            log_success "镜像构建完成"
        else
            log_error "镜像构建失败"
            exit 1
        fi
    else
        log_info "跳过镜像构建"
    fi

    # 验证镜像
    if verify_images; then
        log_success "镜像验证完成"
    else
        log_error "镜像验证失败"
        exit 1
    fi

    # 推送镜像
    if [ "$SKIP_PUSH" = false ]; then
        if push_images; then
            log_success "镜像推送完成"
        else
            log_error "镜像推送失败"
            exit 1
        fi
    else
        log_info "跳过镜像推送"
    fi

    # 生成清单
    generate_manifest

    # 清理
    if [ "$CLEANUP" = true ]; then
        cleanup_old_images
    fi

    echo ""
    echo -e "${GREEN}✅ Docker镜像构建完成！${NC}"
    echo ""
    echo -e "${BLUE}📋 构建结果:${NC}"
    for service in "${SERVICES[@]}"; do
        echo -e "  📦 ${service}: ${YELLOW}${REGISTRY}/${service}:${VERSION}${NC}"
    done
    echo ""
    echo -e "${BLUE}📋 生成的文件:${NC}"
    echo -e "  📄 镜像清单: ${YELLOW}docker-manifest-${BUILD_DATE}.json${NC}"
    echo ""
    echo -e "${PURPLE}✨ Docker镜像已准备就绪！${NC}"
}

# 执行主函数
main "$@"