#!/bin/bash
# Athena多模态文件系统平台级部署脚本
# Platform Deployment Script for Athena Multimodal File System

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 配置
CONFIG_FILE="/Users/xujian/Athena工作平台/deploy/multimodal_platform_config.yaml"
LOG_DIR="/Users/xujian/Athena工作平台/logs/deployment"
PID_DIR="/tmp/athena_platform_pids"

# 创建必要目录
mkdir -p "$LOG_DIR"
mkdir -p "$PID_DIR"

# 日志文件
DEPLOYMENT_LOG="$LOG_DIR/deployment_$(date +%Y%m%d_%H%M%S).log"

echo -e "${PURPLE}🚀 Athena多模态文件系统平台级部署${NC}"
echo "========================================"
echo -e "${CYAN}部署开始时间: $(date)${NC}"
echo -e "${CYAN}日志文件: $DEPLOYMENT_LOG${NC}"
echo ""

# 函数定义
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$DEPLOYMENT_LOG"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$DEPLOYMENT_LOG"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$DEPLOYMENT_LOG"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$DEPLOYMENT_LOG"
}

check_system_requirements() {
    log_info "检查系统要求..."

    # 检查Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        log_success "Python版本: $PYTHON_VERSION"
    else
        log_error "Python3未安装"
        exit 1
    fi

    # 检查系统资源
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS系统
        MEMORY_GB=$(sysctl -n hw.memsize | awk '{print int($1/1024/1024/1024)}')
        CPU_CORES=$(sysctl -n hw.ncpu)
    else
        # Linux系统
        MEMORY_GB=$(free -g | awk '/^Mem:/{print $2}')
        CPU_CORES=$(nproc)
    fi

    log_info "系统资源: ${MEMORY_GB}GB内存, ${CPU_CORES}个CPU核心"

    if [ "$MEMORY_GB" -lt 8 ]; then
        log_warning "建议至少8GB内存，当前: ${MEMORY_GB}GB"
    fi

    if [ "$CPU_CORES" -lt 4 ]; then
        log_warning "建议至少4个CPU核心，当前: ${CPU_CORES}个"
    fi
}

install_dependencies() {
    log_info "安装系统依赖..."

    # 安装Python包
    log_info "安装Python依赖包..."

    packages=(
        "fastapi"
        "uvicorn"
        "pydantic"
        "aiofiles"
        "requests"
        "PyYAML"
        "psutil"
        "numpy"
        "pandas"
        "pillow"
        "opencv-python"
        "layoutparser"
        "paddleocr"
        "pdfplumber"
        "PyMuPDF"
        "python-docx"
        "doc2docx"
        "python-doc"
        "olefile"
        "jwt"
        "cryptography"
        "psycopg2-binary"
        "prometheus-client"
    )

    for package in "${packages[@]}"; do
        log_info "安装 $package..."
        pip3 install "$package" >> "$DEPLOYMENT_LOG" 2>&1 || {
            log_error "安装 $package 失败"
            return 1
        }
    done

    log_success "所有依赖包安装完成"
}

setup_database() {
    log_info "设置数据库..."

    # 检查PostgreSQL
    if command -v psql &> /dev/null; then
        log_success "PostgreSQL已安装"

        # 创建数据库（如果不存在）
        if ! sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw athena_multimodal; then
            log_info "创建数据库 athena_multimodal..."
            sudo -u postgres createdb athena_multimodal || {
                log_warning "数据库创建失败，使用内存存储"
            }
        else
            log_success "数据库 athena_multimodal 已存在"
        fi
    else
        log_warning "PostgreSQL未安装，将使用内存存储"
    fi
}

setup_storage() {
    log_info "设置存储目录..."

    # 创建存储目录
    storage_dirs=(
        "/data/athena/multimodal"
        "/data/athena/uploads"
        "/data/athena/processed"
        "/data/athena/cache"
        "/data/athena/backup"
        "/etc/athena"
        "/var/log/athena"
    )

    for dir in "${storage_dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            sudo mkdir -p "$dir"
            sudo chown $(whoami):$(whoami) "$dir"
            log_info "创建目录: $dir"
        fi
    done

    log_success "存储目录设置完成"
}

generate_ssl_certificates() {
    log_info "生成SSL证书..."

    SSL_DIR="/etc/ssl/certs"

    if [ ! -f "$SSL_DIR/athena.crt" ]; then
        log_info "生成自签名SSL证书..."
        sudo mkdir -p "$SSL_DIR"

        # 生成私钥
        sudo openssl genrsa -out "$SSL_DIR/athena.key" 2048

        # 生成证书
        sudo openssl req -new -x509 -key "$SSL_DIR/athena.key" -out "$SSL_DIR/athena.crt" -days 365 \
            -subj "/C=CN/ST=State/L=City/O=Athena/OU=Multimodal/CN=localhost"

        log_success "SSL证书生成完成"
    else
        log_success "SSL证书已存在"
    fi
}

deploy_services() {
    log_info "部署多模态文件系统服务..."

    # 1. 启动Dolphin文档解析服务
    log_info "启动Dolphin文档解析服务..."
    bash "/Users/xujian/Athena工作平台/scripts/startup/start_dolphin_service.sh" >> "$DEPLOYMENT_LOG" 2>&1 &
    DOLPHIN_PID=$!
    echo $DOLPHIN_PID > "$PID_DIR/dolphin_parser.pid"

    # 2. 启动GLM视觉服务
    log_info "启动GLM视觉服务..."
    cd "/Users/xujian/Athena工作平台/services/ai-models/glm-full-suite"
    nohup python3 athena_glm_full_suite_server.py > "$LOG_DIR/glm_vision.log" 2>&1 &
    GLM_PID=$!
    echo $GLM_PID > "$PID_DIR/glm_vision.pid"

    # 3. 启动多模态处理器
    log_info "启动多模态处理器..."
    cd "/Users/xujian/Athena工作平台/services"
    nohup python3 multimodal_processing_service.py > "$LOG_DIR/multimodal_processor.log" 2>&1 &
    MULTIMODAL_PID=$!
    echo $MULTIMODAL_PID > "$PID_DIR/multimodal_processor.pid"

    # 4. 启动统一API网关
    log_info "启动统一API网关..."
    cd "/Users/xujian/Athena工作平台/services"
    nohup python3 unified_multimodal_api.py > "$LOG_DIR/unified_multimodal_api.log" 2>&1 &
    API_GATEWAY_PID=$!
    echo $API_GATEWAY_PID > "$PID_DIR/api_gateway.pid"

    log_success "所有服务启动完成"
}

deploy_control_systems() {
    log_info "部署控制系统..."

    # 1. 启动小诺智能控制中心
    log_info "启动小诺智能控制中心..."
    cd "/Users/xujian/Athena工作平台/services"
    nohup python3 xiao_nuo_control.py > "$LOG_DIR/xiao_nuo_control.log" 2>&1 &
    XIAO_NUO_PID=$!
    echo $XIAO_NUO_PID > "$PID_DIR/xiao_nuo_control.pid"

    # 2. 启动Athena平台管理中心
    log_info "启动Athena平台管理中心..."
    cd "/Users/xujian/Athena工作平台/services"
    nohup python3 athena_platform_manager.py > "$LOG_DIR/athena_platform_manager.log" 2>&1 &
    ATHENA_PLATFORM_PID=$!
    echo $ATHENA_PLATFORM_PID > "$PID_DIR/athena_platform_manager.pid"

    log_success "控制系统部署完成"
}

setup_monitoring() {
    log_info "设置监控系统..."

    # 创建监控脚本
    cat > "/Users/xujian/Athena工作平台/scripts/monitor_platform.sh" << 'EOF'
#!/bin/bash
# Athena平台监控脚本

SERVICES=(
    "dolphin_parser:8013"
    "glm_vision:8091"
    "multimodal_processor:8012"
    "api_gateway:8020"
    "xiao_nuo_control:9001"
    "athena_platform_manager:9000"
)

for service in "${SERVICES[@]}"; do
    name=$(echo $service | cut -d: -f1)
    port=$(echo $service | cut -d: -f2)

    if curl -s "http://localhost:$port/health" > /dev/null; then
        echo "$(date): $name (端口$port) - 运行正常"
    else
        echo "$(date): $name (端口$port) - 服务异常"
    fi
done
EOF

    chmod +x "/Users/xujian/Athena工作平台/scripts/monitor_platform.sh"

    log_success "监控系统设置完成"
}

verify_deployment() {
    log_info "验证部署..."

    # 等待服务启动
    log_info "等待服务启动完成..."
    sleep 10

    # 检查各服务健康状态
    services=(
        "Dolphin解析服务:http://localhost:8013/health"
        "GLM视觉服务:http://localhost:8091/health"
        "多模态处理器:http://localhost:8012/"
        "统一API网关:http://localhost:8020/health"
        "小诺控制中心:http://localhost:9001/health"
        "Athena管理中心:http://localhost:9000/health"
    )

    failed_services=()

    for service in "${services[@]}"; do
        name=$(echo $service | cut -d: -f1)
        url=$(echo $service | cut -d: -f2-)

        if curl -s "$url" > /dev/null; then
            log_success "$name - 运行正常"
        else
            log_error "$name - 启动失败"
            failed_services+=("$name")
        fi
    done

    if [ ${#failed_services[@]} -eq 0 ]; then
        log_success "所有服务验证通过"
        return 0
    else
        log_error "以下服务启动失败: ${failed_services[*]}"
        return 1
    fi
}

create_management_scripts() {
    log_info "创建管理脚本..."

    # 创建停止脚本
    cat > "/Users/xujian/Athena工作平台/scripts/stop_platform.sh" << 'EOF'
#!/bin/bash
# 停止Athena多模态文件系统平台

echo "停止Athena多模态文件系统平台..."

PID_DIR="/tmp/athena_platform_pids"
LOG_DIR="/Users/xujian/Athena工作平台/logs/deployment"

# 停止所有服务
services=(
    "api_gateway"
    "multimodal_processor"
    "glm_vision"
    "dolphin_parser"
    "xiao_nuo_control"
    "athena_platform_manager"
)

for service in "${services[@]}"; do
    pid_file="$PID_DIR/$service.pid"
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo "停止 $service (PID: $pid)..."
            kill "$pid"
            sleep 2
        fi
        rm -f "$pid_file"
    fi
done

echo "Athena多模态文件系统平台已停止"
EOF

    # 创建重启脚本
    cat > "/Users/xujian/Athena工作平台/scripts/restart_platform.sh" << 'EOF'
#!/bin/bash
# 重启Athena多模态文件系统平台

echo "重启Athena多模态文件系统平台..."

# 先停止
bash "/Users/xujian/Athena工作平台/scripts/stop_platform.sh"

# 等待
sleep 3

# 再启动
bash "/Users/xujian/Athena工作平台/scripts/deploy_multimodal_platform.sh"

echo "Athena多模态文件系统平台重启完成"
EOF

    # 创建状态检查脚本
    cat > "/Users/xujian/Athena工作平台/scripts/status_platform.sh" << 'EOF'
#!/bin/bash
# 检查Athena多模态文件系统平台状态

echo "Athena多模态文件系统平台状态检查"
echo "=================================="

# 检查服务状态
services=(
    "api_gateway:8020"
    "multimodal_processor:8012"
    "glm_vision:8091"
    "dolphin_parser:8013"
    "xiao_nuo_control:9001"
    "athena_platform_manager:9000"
)

all_running=true

for service in "${services[@]}"; do
    name=$(echo $service | cut -d: -f1)
    port=$(echo $service | cut -d: -f2)

    if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
        status="运行中"
        color="\033[0;32m"
    else
        status="停止"
        color="\033[0;31m"
        all_running=false
    fi

    echo -e "${color} $name (端口$port): $status${NC}"
done

echo "=================================="

if $all_running; then
    echo -e "\033[0;32m所有服务运行正常\033[0m"
else
    echo -e "\033[0;31m部分服务异常，请检查日志\033[0m"
fi
EOF

    chmod +x "/Users/xujian/Athena工作平台/scripts/stop_platform.sh"
    chmod +x "/Users/xujian/Athena工作平台/scripts/restart_platform.sh"
    chmod +x "/Users/xujian/Athena工作平台/scripts/status_platform.sh"

    log_success "管理脚本创建完成"
}

generate_deployment_info() {
    log_info "生成部署信息..."

    cat > "/Users/xujian/Athena工作平台/deployment_info.json" << EOF
{
    "deployment": {
        "timestamp": "$(date -Iseconds)",
        "platform": "Athena多模态文件系统",
        "version": "2.0.0",
        "environment": "production"
    },
    "services": {
        "dolphin_parser": {
            "name": "Dolphin文档解析服务",
            "port": 8013,
            "url": "http://localhost:8013",
            "health": "http://localhost:8013/health"
        },
        "glm_vision": {
            "name": "GLM视觉服务",
            "port": 8091,
            "url": "http://localhost:8091",
            "health": "http://localhost:8091/health"
        },
        "multimodal_processor": {
            "name": "多模态处理器",
            "port": 8012,
            "url": "http://localhost:8012",
            "health": "http://localhost:8012/"
        },
        "api_gateway": {
            "name": "统一API网关",
            "port": 8020,
            "url": "http://localhost:8020",
            "health": "http://localhost:8020/health",
            "docs": "http://localhost:8020/docs"
        },
        "xiao_nuo_control": {
            "name": "小诺智能控制中心",
            "port": 9001,
            "url": "http://localhost:9001",
            "health": "http://localhost:9001/health",
            "websocket": "ws://localhost:9001/ws"
        },
        "athena_platform_manager": {
            "name": "Athena平台管理中心",
            "port": 9000,
            "url": "http://localhost:9000",
            "health": "http://localhost:9000/health"
        }
    },
    "access_points": {
        "main_api": "http://localhost:8020",
        "control_center": "http://localhost:9001",
        "platform_management": "http://localhost:9000",
        "api_documentation": "http://localhost:8020/docs"
    },
    "supported_formats": [
        ".pdf", ".doc", ".docx", ".jpg", ".jpeg", ".png", ".tiff", ".bmp"
    ],
    "features": {
        "document_parsing": true,
        "image_analysis": true,
        "chemical_analysis": true,
        "multimodal_search": true,
        "intelligent_control": true,
        "user_management": true,
        "api_authentication": true
    },
    "management_scripts": {
        "stop": "/Users/xujian/Athena工作平台/scripts/stop_platform.sh",
        "restart": "/Users/xujian/Athena工作平台/scripts/restart_platform.sh",
        "status": "/Users/xujian/Athena工作平台/scripts/status_platform.sh",
        "monitor": "/Users/xujian/Athena工作平台/scripts/monitor_platform.sh"
    },
    "logs_directory": "/Users/xujian/Athena工作平台/logs",
    "configuration_file": "/Users/xujian/Athena工作平台/deploy/multimodal_platform_config.yaml"
}
EOF

    log_success "部署信息生成完成"
}

main() {
    # 解析命令行参数
    case "${1:-deploy}" in
        "check")
            check_system_requirements
            ;;
        "deps")
            install_dependencies
            ;;
        "services")
            deploy_services
            ;;
        "control")
            deploy_control_systems
            ;;
        "monitor")
            setup_monitoring
            ;;
        "verify")
            verify_deployment
            ;;
        "full")
            check_system_requirements
            install_dependencies
            setup_database
            setup_storage
            generate_ssl_certificates
            deploy_services
            deploy_control_systems
            setup_monitoring
            create_management_scripts

            echo ""
            log_info "验证部署..."
            if verify_deployment; then
                generate_deployment_info
                echo ""
                echo -e "${GREEN}🎉 Athena多模态文件系统平台部署完成！${NC}"
                echo "========================================"
                echo -e "${BLUE}🔗 主要访问地址:${NC}"
                echo -e "  📡 统一API: ${GREEN}http://localhost:8020${NC}"
                echo -e "  🤖 小诺控制中心: ${GREEN}http://localhost:9001${NC}"
                echo -e "  🛡️  Athena管理中心: ${GREEN}http://localhost:9000${NC}"
                echo -e "  📚 API文档: ${GREEN}http://localhost:8020/docs${NC}"
                echo ""
                echo -e "${BLUE}🔧 管理命令:${NC}"
                echo -e "  📊 查看状态: ${YELLOW}bash /Users/xujian/Athena工作平台/scripts/status_platform.sh${NC}"
                echo -e "  🛑 停止平台: ${YELLOW}bash /Users/xujian/Athena工作平台/scripts/stop_platform.sh${NC}"
                echo -e "  🔄 重启平台: ${YELLOW}bash /Users/xujian/Athena工作平台/scripts/restart_platform.sh${NC}"
                echo -e "  📈 监控系统: ${YELLOW}bash /Users/xujian/Athena工作平台/scripts/monitor_platform.sh${NC}"
                echo ""
                echo -e "${BLUE}📋 部署信息:${NC}"
                echo -e "  📄 配置文件: ${YELLOW}/Users/xujian/Athena工作平台/deploy/multimodal_platform_config.yaml${NC}"
                echo -e "  📊 部署信息: ${YELLOW}/Users/xujian/Athena工作平台/deployment_info.json${NC}"
                echo -e "  📝 日志目录: ${YELLOW}/Users/xujian/Athena工作平台/logs${NC}"
                echo ""
                echo -e "${PURPLE}✨ 现在您可以通过小诺和Athena全量控制多模态文件系统！${NC}"
            else
                echo ""
                log_error "部署验证失败，请检查日志: $DEPLOYMENT_LOG"
                exit 1
            fi
            ;;
        *)
            echo "用法: $0 [command]"
            echo ""
            echo "命令:"
            echo "  check    - 检查系统要求"
            echo "  deps     - 安装依赖"
            echo "  services - 部署服务"
            echo "  control  - 部署控制系统"
            echo "  monitor  - 设置监控"
            echo "  verify   - 验证部署"
            echo "  full     - 完整部署"
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"