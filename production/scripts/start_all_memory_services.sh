#!/bin/bash
# ===================================================================
# 快速启动所有记忆服务
# Fast Startup Script for All Memory Services
# ===================================================================
# 基于启动分析报告优化的快速启动脚本
# 目标启动时间: < 5分钟
# ===================================================================

set -e

PROJECT_ROOT="/Users/xujian/Athena工作平台"
LOG_DIR="${PROJECT_ROOT}/logs"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

# 计时
START_TIME=$(date +%s)

# ===================================================================
# 步骤1: 预检查 (30秒内完成)
# ===================================================================
pre_check() {
    log_step "步骤1: 预检查 (目标: 30秒)"

    # 1.1 检查Python语法
    log_info "检查Python 3.12语法..."
    if ! python3.11 -m compileall "$PROJECT_ROOT/core/api/rate_limiter.py" >/dev/null 2>&1; then
        log_warn "发现语法错误，尝试自动修复..."
        python3.11 "$PROJECT_ROOT/tools/fix_type_annotations.py" || true
    fi

    # 1.2 检查端口占用
    log_info "检查端口占用..."
    PORTS_IN_USE=""
    for port in 8008 8083 8002; do
        if lsof -i :$port > /dev/null 2>&1; then
            PORTS_IN_USE="$PORTS_IN_USE $port"
            log_warn "端口 $port 已被占用"
        fi
    done

    if [ -n "$PORTS_IN_USE" ]; then
        log_error "以下端口被占用:$PORTS_IN_USE"
        echo "是否停止占用这些端口的进程? (y/n)"
        read -r response
        if [ "$response" = "y" ]; then
            for port in $PORTS_IN_USE; do
                log_info "停止端口 $port 的进程..."
                lsof -ti :$port | xargs kill -9 2>/dev/null || true
                sleep 1
            done
        else
            log_error "无法启动服务，端口被占用"
            exit 1
        fi
    fi

    # 1.3 检查依赖服务
    log_info "检查依赖服务..."
    if ! ps aux | grep -E "xiaonuo.*agent" | grep -v grep > /dev/null 2>&1; then
        log_warn "小诺智能体未运行，小诺记忆服务可能无法正常工作"
    fi

    log_info "✅ 预检查完成"
}

# ===================================================================
# 步骤2: 启动服务 (1分钟内完成)
# ===================================================================
start_services() {
    log_step "步骤2: 启动服务 (目标: 1分钟)"

    # 2.1 启动Athena记忆服务
    log_info "启动Athena记忆服务 (8008)..."
    bash "$PROJECT_ROOT/production/scripts/start_athena_memory.sh" &
    ATHENA_PID=$!

    # 2.2 启动小诺记忆服务
    log_info "启动小诺记忆服务 (8083)..."
    bash "$PROJECT_ROOT/production/scripts/start_xiaonuo_memory.sh" &
    XIAONUO_PID=$!

    # 2.3 启动提示词系统API
    log_info "启动提示词系统API (8002)..."
    cd "$PROJECT_ROOT/core/api"
    export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
    export API_PORT=8002
    nohup python3.11 main.py > "$LOG_DIR/prompt-system-api.log" 2>&1 &
    PROMPT_PID=$!
    echo "$PROMPT_PID" > "$LOG_DIR/prompt-system-api.pid"

    # 等待所有服务启动
    log_info "等待服务启动..."
    sleep 5

    log_info "✅ 所有服务启动命令已执行"
}

# ===================================================================
# 步骤3: 快速验证 (30秒内完成)
# ===================================================================
verify_services() {
    log_step "步骤3: 快速验证 (目标: 30秒)"

    local all_ok=true

    # 3.1 检查Athena记忆服务
    log_info "检查Athena记忆服务..."
    if curl -s http://localhost:8008/health > /dev/null 2>&1; then
        STATUS=$(curl -s http://localhost:8008/health | grep -o '"status":"[^"]*"')
        log_info "✅ Athena记忆服务: $STATUS"
    else
        log_error "❌ Athena记忆服务未响应"
        all_ok=false
    fi

    # 3.2 检查小诺记忆服务
    log_info "检查小诺记忆服务..."
    if curl -s http://localhost:8083/health > /dev/null 2>&1; then
        STATUS=$(curl -s http://localhost:8083/health | grep -o '"status":"[^"]*"')
        log_info "✅ 小诺记忆服务: $STATUS"
    else
        log_error "❌ 小诺记忆服务未响应"
        all_ok=false
    fi

    # 3.3 检查提示词系统API
    log_info "检查提示词系统API..."
    if curl -s http://localhost:8002/health > /dev/null 2>&1; then
        STATUS=$(curl -s http://localhost:8002/health | grep -o '"status":"[^"]*"')
        log_info "✅ 提示词系统API: $STATUS"
    else
        log_error "❌ 提示词系统API未响应"
        all_ok=false
    fi

    if [ "$all_ok" = true ]; then
        log_info "✅ 所有服务验证通过"
        return 0
    else
        log_error "⚠️ 部分服务验证失败"
        return 1
    fi
}

# ===================================================================
# 显示启动报告
# ===================================================================
show_report() {
    END_TIME=$(date +%s)
    ELAPSED=$((END_TIME - START_TIME))

    echo ""
    echo "============================================================"
    echo "  启动完成报告"
    echo "============================================================"
    echo ""
    echo "⏱️  总用时: ${ELAPSED}秒"
    echo ""
    echo "📊 服务状态:"
    echo "  ┌─────────────────┬──────┬────────┬──────────┐"
    echo "  │ 服务            │ 端口 │ 状态  │ 健康检查 │"
    echo "  ├─────────────────┼──────┼────────┼──────────┤"
    echo "  │ Athena记忆      │ 8008 │ 运行中│ http://localhost:8008/health │"
    echo "  │ 小诺记忆        │ 8083 │ 运行中│ http://localhost:8083/health │"
    echo "  │ 提示词系统API   │ 8002 │ 运行中│ http://localhost:8002/health │"
    echo "  └─────────────────┴──────┴────────┴──────────┘"
    echo ""
    echo "📖 详细分析: docs/service-startup-analysis-20260131.md"
    echo ""
    echo "============================================================"
    echo ""
}

# ===================================================================
# 主程序
# ===================================================================
main() {
    echo ""
    echo "============================================================"
    echo "  快速启动所有记忆服务"
    echo "============================================================"
    echo ""

    pre_check
    start_services
    sleep 3
    verify_services
    show_report

    if [ $? -eq 0 ]; then
        log_info "🎉 所有服务启动成功！"
    else
        log_warn "⚠️ 部分服务可能需要手动检查"
    fi
}

# 执行主程序
main "$@"
