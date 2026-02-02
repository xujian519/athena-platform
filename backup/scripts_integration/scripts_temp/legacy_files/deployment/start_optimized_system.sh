#!/bin/bash

# Athena优化系统启动脚本
# Optimized Athena System Startup Script

# 设置严格模式
set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# 日志文件
LOG_FILE="logs/system_startup.log"
mkdir -p logs

# 日志函数
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log_info() {
    echo -e "${GREEN}[INFO]${NC} $(log "$1")"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(log "$1")"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(log "$1")"
}

# 检查系统要求
check_requirements() {
    log_info "检查系统要求..."
    
    # 检查Python版本
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装"
        exit 1
    fi
    
    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    log_info "Python版本: $python_version"
    
    # 检查内存
    total_memory=$(free -g | awk '/^Mem:/{print $2}' 2>/dev/null || echo "N/A")
    if [[ "$total_memory" != "N/A" ]] && [[ $total_memory -lt 16 ]]; then
        log_warn "系统内存少于16GB，可能影响性能"
    fi
    
    # 检查磁盘空间
    available_space=$(df -BG . | awk 'NR==2{print $4}' | sed 's/G//')
    if [[ $available_space -lt 10 ]]; then
        log_error "磁盘空间不足10GB"
        exit 1
    fi
    
    log_info "系统要求检查通过"
}

# 优化系统环境
optimize_environment() {
    log_info "优化系统环境..."
    
    # 1. 清理Python缓存
    log_info "清理Python缓存..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    
    # 2. 优化文件描述符限制
    if [[ -f /etc/security/limits.conf ]]; then
        echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf >/dev/null 2>&1 || true
        echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf >/dev/null 2>&1 || true
    fi
    
    # 3. 优化内核参数
    if [[ "$EUID" -eq 0 ]]; then
        echo "vm.swappiness=10" >> /etc/sysctl.conf
        echo "fs.file-max=2097152" >> /etc/sysctl.conf
        sysctl -p >/dev/null 2>&1 || true
    fi
    
    # 4. 启动内存监控
    log_info "启动内存监控..."
    nohup python3 scripts/memory_optimizer.py --monitor --interval 300 > logs/memory_monitor.log 2>&1 &
    MEMORY_PID=$!
    echo "$MEMORY_PID" > logs/memory_monitor.pid
    
    log_info "环境优化完成"
}

# 启动核心服务
start_core_services() {
    log_info "启动核心服务..."
    
    # 1. 启动Redis（如果需要）
    if command -v redis-server &> /dev/null; then
        if ! pgrep redis-server > /dev/null; then
            redis-server --daemonize yes --port 6379
            log_info "Redis服务已启动"
        fi
    fi
    
    # 2. 启动数据库（如果需要）
    if command -v postgres &> /dev/null; then
        if ! pgrep postgres > /dev/null; then
            # PostgreSQL通常由系统服务管理
            brew services start postgresql 2>/dev/null || true
            log_info "PostgreSQL服务启动尝试完成"
        fi
    fi
    
    # 3. 启动向量数据库（如果需要）
    if [[ -f "scripts/start_qdrant.sh" ]]; then
        bash scripts/start_qdrant.sh >/dev/null 2>&1 &
        log_info "Qdrant服务启动尝试完成"
    fi
    
    log_info "核心服务启动完成"
}

# 初始化AI模块
initialize_ai_modules() {
    log_info "初始化AI模块..."
    
    # 1. 设置Python路径
    export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
    
    # 2. 检查GPU支持
    if command -v nvidia-smi &> /dev/null; then
        export CUDA_VISIBLE_DEVICES=0
        log_info "GPU支持已启用"
    else
        log_info "使用CPU模式"
    fi
    
    # 3. 预热模型
    if [[ -f "scripts/warmup_models.py" ]]; then
        python3 scripts/warmup_models.py >/dev/null 2>&1 &
        log_info "模型预热已启动"
    fi
    
    log_info "AI模块初始化完成"
}

# 启动监控系统
start_monitoring() {
    log_info "启动监控系统..."
    
    # 1. 启动性能监控
    nohup python3 scripts/performance_dashboard.py --watch --interval 30 --save > logs/performance_monitor.log 2>&1 &
    PERF_PID=$!
    echo "$PERF_PID" > logs/performance_monitor.pid
    
    # 2. 启动应用监控
    if [[ -f "scripts/health_check.sh" ]]; then
        nohup bash scripts/health_check.sh --daemon > logs/health_monitor.log 2>&1 &
        HEALTH_PID=$!
        echo "$HEALTH_PID" > logs/health_monitor.pid
    fi
    
    log_info "监控系统已启动"
}

# 配置负载均衡器
configure_load_balancer() {
    log_info "配置负载均衡器..."
    
    # 创建负载均衡配置
    cat > config/load_balancer.json << EOF
{
    "algorithm": "round_robin",
    "health_check": {
        "interval": 30,
        "timeout": 5,
        "retries": 3
    },
    "servers": [
        {
            "host": "127.0.0.1",
            "port": 8080,
            "weight": 1
        }
    ],
    "limits": {
        "max_connections": 1000,
        "request_timeout": 30
    }
}
EOF
    
    log_info "负载均衡器配置完成"
}

# 显示启动状态
show_startup_status() {
    log_info "系统启动状态..."
    
    echo ""
    echo "=================================="
    echo "🚀 Athena优化系统已启动"
    echo "=================================="
    echo ""
    echo "📊 系统信息:"
    echo "   - 项目路径: $PROJECT_ROOT"
    echo "   - 启动时间: $(date)"
    echo "   - 日志文件: $LOG_FILE"
    echo ""
    echo "🔧 服务状态:"
    
    # 检查各个服务状态
    if [[ -f "logs/memory_monitor.pid" ]]; then
        if kill -0 $(cat logs/memory_monitor.pid) 2>/dev/null; then
            echo "   ✅ 内存监控: 运行中 (PID: $(cat logs/memory_monitor.pid))"
        else
            echo "   ❌ 内存监控: 未运行"
        fi
    fi
    
    if [[ -f "logs/performance_monitor.pid" ]]; then
        if kill -0 $(cat logs/performance_monitor.pid) 2>/dev/null; then
            echo "   ✅ 性能监控: 运行中 (PID: $(cat logs/performance_monitor.pid))"
        else
            echo "   ❌ 性能监控: 未运行"
        fi
    fi
    
    if pgrep redis-server > /dev/null; then
        echo "   ✅ Redis: 运行中"
    else
        echo "   ⚠️ Redis: 未运行"
    fi
    
    echo ""
    echo "📈 性能监控:"
    echo "   - 内存监控: 每5分钟检查一次"
    echo "   - 性能仪表板: 每30秒更新一次"
    echo ""
    echo "🛠️ 管理命令:"
    echo "   - 查看性能: python3 scripts/performance_dashboard.py"
    echo "   - 内存优化: python3 scripts/memory_optimizer.py --optimize"
    echo "   - 停止系统: bash scripts/stop_optimized_system.sh"
    echo ""
    echo "📝 日志位置:"
    echo "   - 系统日志: $LOG_FILE"
    echo "   - 内存监控: logs/memory_monitor.log"
    echo "   - 性能监控: logs/performance_monitor.log"
    echo ""
}

# 创建停止脚本
create_stop_script() {
    cat > scripts/stop_optimized_system.sh << 'EOF'
#!/bin/bash

# Athena优化系统停止脚本

echo "🛑 停止Athena优化系统..."

# 停止内存监控
if [[ -f "logs/memory_monitor.pid" ]]; then
    PID=$(cat logs/memory_monitor.pid)
    if kill -0 "$PID" 2>/dev/null; then
        kill "$PID"
        echo "✅ 内存监控已停止"
    fi
    rm -f logs/memory_monitor.pid
fi

# 停止性能监控
if [[ -f "logs/performance_monitor.pid" ]]; then
    PID=$(cat logs/performance_monitor.pid)
    if kill -0 "$PID" 2>/dev/null; then
        kill "$PID"
        echo "✅ 性能监控已停止"
    fi
    rm -f logs/performance_monitor.pid
fi

# 停止健康检查
if [[ -f "logs/health_monitor.pid" ]]; then
    PID=$(cat logs/health_monitor.pid)
    if kill -0 "$PID" 2>/dev/null; then
        kill "$PID"
        echo "✅ 健康检查已停止"
    fi
    rm -f logs/health_monitor.pid
fi

echo "🏁 系统已完全停止"
EOF
    
    chmod +x scripts/stop_optimized_system.sh
}

# 主函数
main() {
    echo ""
    echo "🚀 启动Athena优化系统..."
    echo "================================"
    
    # 创建必要的目录
    mkdir -p logs metrics config
    
    # 创建停止脚本
    create_stop_script
    
    # 执行启动步骤
    check_requirements
    optimize_environment
    start_core_services
    initialize_ai_modules
    start_monitoring
    configure_load_balancer
    show_startup_status
    
    log_info "Athena优化系统启动完成"
}

# 错误处理
trap 'log_error "启动过程中发生错误"; exit 1' ERR

# 运行主函数
main "$@"