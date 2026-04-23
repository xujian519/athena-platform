#!/bin/bash
# =============================================================================
# 小诺生产环境一键部署脚本
# Xiaonuo Production One-Click Deployment Script
# =============================================================================
#
# 此脚本将：
# 1. 创建必要的用户和目录
# 2. 部署配置文件
# 3. 创建Python虚拟环境
# 4. 安装依赖
# 5. 配置systemd服务
# 6. 启动服务
#
# =============================================================================

set -e

# -----------------------------------------------------------------------------
# 配置
# -----------------------------------------------------------------------------

PROJECT_ROOT="/Users/xujian/Athena工作平台"
PRODUCTION_ROOT="${PROJECT_ROOT}/production"

# 用户配置（本地开发环境使用当前用户）
XIAONUO_USER="${USER}"
XIAONUO_GROUP="$(id -gn)"

# 目录配置
DATA_DIR="${PROJECT_ROOT}/data/xiaonuo"
LOG_DIR="${PROJECT_ROOT}/logs/xiaonuo"
PID_DIR="${PROJECT_ROOT}/pids/xiaonuo"
BACKUP_DIR="${PROJECT_ROOT}/backups/xiaonuo"

# Python配置
VENV_DIR="${PROJECT_ROOT}/athena_env_py311"
PYTHON="${VENV_DIR}/bin/python"
PIP="${VENV_DIR}/bin/pip"

# 服务配置
SERVICE_NAME="xiaonuo"
SERVICE_PORT=8005

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# -----------------------------------------------------------------------------
# 辅助函数
# -----------------------------------------------------------------------------

print_header() {
    echo -e "\n${BLUE}============================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================================${NC}\n"
}

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "\n${BLUE}>>> $1${NC}"
}

# -----------------------------------------------------------------------------
# 部署步骤
# -----------------------------------------------------------------------------

# 步骤1: 创建目录结构
setup_directories() {
    print_step "步骤1/7: 创建目录结构"

    mkdir -p "$DATA_DIR"
    mkdir -p "$LOG_DIR"
    mkdir -p "$PID_DIR"
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$DATA_DIR/memory"
    mkdir -p "$DATA_DIR/eternal_memory"

    print_info "目录创建完成"
    print_info "  数据目录: $DATA_DIR"
    print_info "  日志目录: $LOG_DIR"
    print_info "  PID目录: $PID_DIR"
    print_info "  备份目录: $BACKUP_DIR"
}

# 步骤2: 部署配置文件
deploy_configurations() {
    print_step "步骤2/7: 部署配置文件"

    # 创建生产配置目录
    mkdir -p "${PROJECT_ROOT}/config/production"

    # 检查配置文件
    if [ -f "${PROJECT_ROOT}/config/production/xiaonuo_production.yaml" ]; then
        print_info "生产配置文件已存在"
    else
        print_warn "生产配置文件不存在，使用默认配置"
    fi

    # 创建环境变量文件（从模板复制）
    if [ ! -f "${PROJECT_ROOT}/.env.production" ]; then
        if [ -f "${PROJECT_ROOT}/.env.production.xiaonuo" ]; then
            cp "${PROJECT_ROOT}/.env.production.xiaonuo" "${PROJECT_ROOT}/.env.production"
            print_info "环境变量文件已创建"
        fi
    fi

    # 导出环境变量
    export XIAONUO_DATA_DIR="$DATA_DIR"
    export XIAONUO_LOG_DIR="$LOG_DIR"
    export XIAONUO_PID_FILE="$PID_DIR/xiaonuo.pid"
}

# 步骤3: 检查Python虚拟环境
setup_python_env() {
    print_step "步骤3/7: 检查Python虚拟环境"

    if [ -f "$PYTHON" ]; then
        print_info "Python虚拟环境已存在"
        "$PYTHON" --version
    else
        print_warn "Python虚拟环境不存在，创建中..."
        python3 -m venv "$VENV_DIR"
        print_info "Python虚拟环境创建完成"
    fi

    # 检查关键依赖
    print_info "检查关键依赖..."

    # 检查FastAPI
    if "$PYTHON" -c "import fastapi" 2>/dev/null; then
        print_info "  ✓ FastAPI已安装"
    else
        print_warn "  ⚠ FastAPI未安装"
    fi

    # 检查Prometheus客户端
    if "$PYTHON" -c "import prometheus_client" 2>/dev/null; then
        print_info "  ✓ prometheus_client已安装"
    else
        print_warn "  ⚠ prometheus_client未安装，安装中..."
        "$PIP" install prometheus-client
    fi
}

# 步骤4: 创建服务启动脚本
create_service_script() {
    print_step "步骤4/7: 创建服务启动脚本"

    cat > "${PROJECT_ROOT}/scripts/start_xiaonuo_service.sh" << 'EOF'
#!/bin/bash
# 小诺服务启动脚本

export PYTHONPATH="/Users/xujian/Athena工作平台"
export XIAONUO_DATA_DIR="/Users/xujian/Athena工作平台/data/xiaonuo"
export XIAONUO_LOG_DIR="/Users/xujian/Athena工作平台/logs/xiaonuo"

# 启动健康检查服务
cd /Users/xujian/Athena工作平台
python3 production/services/health_check.py &
echo $! > /Users/xujian/Athena工作平台/pids/xiaonuo/health_check.pid

echo "小诺健康检查服务已启动"
echo "监听地址: http://127.0.0.1:8099"
echo "健康检查: http://127.0.0.1:8099/health"
EOF

    chmod +x "${PROJECT_ROOT}/scripts/start_xiaonuo_service.sh"

    print_info "服务启动脚本已创建"
}

# 步骤5: 创建服务停止脚本
create_stop_script() {
    print_step "步骤5/7: 创建服务停止脚本"

    cat > "${PROJECT_ROOT}/scripts/stop_xiaonuo_service.sh" << 'EOF'
#!/bin/bash
# 小诺服务停止脚本

echo "停止小诺服务..."

# 读取PID文件并终止进程
PID_FILE="/Users/xujian/Athena工作平台/pids/xiaonuo/health_check.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "终止进程 $PID..."
        kill -TERM "$PID"
        sleep 2
        if kill -0 "$PID" 2>/dev/null; then
            echo "强制终止进程 $PID..."
            kill -KILL "$PID"
        fi
    fi
    rm -f "$PID_FILE"
    echo "服务已停止"
else
    echo "服务未运行"
fi
EOF

    chmod +x "${PROJECT_ROOT}/scripts/stop_xiaonuo_service.sh"

    print_info "服务停止脚本已创建"
}

# 步骤6: 启动服务
start_service() {
    print_step "步骤6/7: 启动服务"

    # 检查服务是否已运行
    if [ -f "$PID_DIR/health_check.pid" ]; then
        PID=$(cat "$PID_DIR/health_check.pid")
        if kill -0 "$PID" 2>/dev/null; then
            print_warn "服务已在运行 (PID: $PID)"
            return
        fi
    fi

    # 启动服务
    "${PROJECT_ROOT}/scripts/start_xiaonuo_service.sh"

    # 等待服务启动
    sleep 2

    # 验证服务
    if [ -f "$PID_DIR/health_check.pid" ]; then
        PID=$(cat "$PID_DIR/health_check.pid")
        if kill -0 "$PID" 2>/dev/null; then
            print_info "服务启动成功 (PID: $PID)"
        else
            print_error "服务启动失败"
            return 1
        fi
    fi
}

# 步骤7: 验证服务
verify_service() {
    print_step "步骤7/7: 验证服务"

    # 检查健康检查端点
    sleep 1

    if curl -s http://127.0.0.1:8099/health > /dev/null; then
        print_info "✓ 健康检查端点响应正常"
        curl -s http://127.0.0.1:8099/health | python3 -m json.tool 2>/dev/null || echo "健康检查响应："
        echo ""
    else
        print_warn "⚠ 健康检查端点无响应"
    fi

    # 检查日志
    if [ -f "$LOG_DIR/xiaonuo.log" ]; then
        print_info "日志文件: $LOG_DIR/xiaonuo.log"
        echo "最近的日志:"
        tail -5 "$LOG_DIR/xiaonuo.log" 2>/dev/null || echo "日志文件为空"
    fi
}

# -----------------------------------------------------------------------------
# 主程序
# -----------------------------------------------------------------------------

main() {
    print_header "小诺生产环境一键部署"

    print_info "项目根目录: $PROJECT_ROOT"
    print_info "Python版本: $(python3 --version)"
    print_info "当前用户: $XIAONUO_USER"

    # 执行部署步骤
    setup_directories
    deploy_configurations
    setup_python_env
    create_service_script
    create_stop_script
    start_service
    verify_service

    print_header "部署完成"

    echo -e "${GREEN}✅ 小诺生产环境部署完成！${NC}\n"
    echo "服务信息:"
    echo "  - 健康检查: http://127.0.0.1:8099/health"
    echo "  - 就绪检查: http://127.0.0.1:8099/health/ready"
    echo "  - 存活检查: http://127.0.0.1:8099/health/live"
    echo ""
    echo "管理命令:"
    echo "  - 启动服务: ./scripts/start_xiaonuo_service.sh"
    echo "  - 停止服务: ./scripts/stop_xiaonuo_service.sh"
    echo "  - 查看日志: tail -f $LOG_DIR/xiaonuo.log"
    echo ""
}

# 运行主程序
main "$@"
