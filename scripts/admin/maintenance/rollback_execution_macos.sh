#!/bin/bash
###############################################################################
# 执行模块回滚脚本 (macOS版本)
# Execution Module Rollback Script for macOS
#
# 用途: 将执行模块回滚到指定版本（适用于macOS开发环境）
# 使用: ./rollback_execution_macos.sh <version> [--force] [--dry-run]
#
# 作者: Athena AI系统
# 版本: 2.0.0
# 创建时间: 2026-01-27
###############################################################################

set -e  # 遇到错误立即退出

###############################################################################
# 配置变量
###############################################################################

# 默认配置
ATHENA_HOME=${ATHENA_HOME:-"$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"}
CONFIG_DIR=${CONFIG_DIR:-"$ATHENA_HOME/config"}
BACKUP_DIR=${BACKUP_DIR:-"$ATHENA_HOME/backup"}
CORE_DIR=${CORE_DIR:-"$ATHENA_HOME/core"}
VERSIONS_DIR=${VERSIONS_DIR:-"$ATHENA_HOME/versions"}
LOG_DIR=${LOG_DIR:-"$ATHENA_HOME/logs/execution")

# 服务配置（macOS不使用systemd）
PROCESS_NAME=${PROCESS_NAME:-"athena-execution"}
PROMETHEUS_METRICS_URL=${METRICS_URL:-"http://localhost:9091/metrics"}
HEALTH_CHECK_URL=${HEALTH_CHECK_URL:-"http://localhost:8081/health"}

# 超时配置
STOP_TIMEOUT=10
START_TIMEOUT=30
HEALTH_CHECK_TIMEOUT=10

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

###############################################################################
# 辅助函数
###############################################################################

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $*"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $*"
}

# 创建备份目录
create_backup_dir() {
    local timestamp
    timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_path="$BACKUP_DIR/rollback_$timestamp"
    mkdir -p "$backup_path"
    echo "$backup_path"
}

# 检查进程是否运行
check_process_running() {
    pgrep -f "$PROCESS_NAME" > /dev/null 2>&1
}

# 停止进程（macOS）
stop_process() {
    log_step "停止进程..."
    
    if check_process_running; then
        pkill -TERM -f "$PROCESS_NAME" || true
        
        # 等待进程停止
        local elapsed=0
        while check_process_running; do
            if [ $elapsed -ge $STOP_TIMEOUT ]; then
                log_warn "进程未在${STOP_TIMEOUT}秒内停止，强制终止..."
                pkill -KILL -f "$PROCESS_NAME" || true
                sleep 1
                break
            fi
            sleep 1
            elapsed=$((elapsed + 1))
            echo -n "."
        done
        
        echo ""
        log_info "进程已停止"
    else
        log_info "进程未运行"
    fi
}

# 启动进程（macOS）
start_process() {
    # 这里只是示例，实际启动方式取决于你的应用
    log_info "进程启动方式取决于你的应用架构"
    log_info "请手动启动你的Athena执行模块"
}

# 备份当前状态
backup_current_state() {
    local backup_path=$1
    
    log_step "备份当前状态到: $backup_path"
    
    # 备份配置
    if [ -f "$CONFIG_DIR/local.yaml" ]; then
        cp "$CONFIG_DIR/local.yaml" "$backup_path/"
        log_info "配置文件已备份"
    fi
    
    if [ -f "$CONFIG_DIR/production.yaml" ]; then
        cp "$CONFIG_DIR/production.yaml" "$backup_path/"
        log_info "生产配置已备份"
    fi
    
    # 备份当前执行模块（如果是符号链接）
    if [ -L "$CORE_DIR/execution" ]; then
        # 保存链接信息
        ls -l "$CORE_DIR/execution" > "$backup_path/symlink_info.txt"
        
        # 尝试复制文件（macOS使用 -L 跟随链接）
        cp -R "$CORE_DIR/execution" "$backup_path/execution_backup" 2>/dev/null || true
        log_info "执行模块链接已记录"
    fi
    
    # 保存当前指标（如果Prometheus运行中）
    if command -v curl &> /dev/null; then
        curl -s "$PROMETHEUS_METRICS_URL" > "$backup_path/metrics.txt" 2>/dev/null || true
        log_info "监控指标已保存"
    fi
    
    # 保存错误日志
    if [ -f "$LOG_DIR/errors.log" ]; then
        tail -100 "$LOG_DIR/errors.log" > "$backup_path/error_tail.log" 2>/dev/null || true
        log_info "错误日志已保存"
    fi
    
    # 保存系统状态
    {
        echo "=== 系统状态 ==="
        date
        echo ""
        echo "=== 磁盘使用 ==="
        df -h
        echo ""
        echo "=== 内存信息 ==="
        vm_stat
        echo ""
        echo "=== CPU信息 ==="
        sysctl -n machdep.cpu.brand_string
        echo ""
        echo "=== 进程信息 ==="
        ps aux | grep "$PROCESS_NAME" | grep -v grep || true
    } > "$backup_path/system_state.txt"
    
    log_info "系统状态已保存"
}

# 收集诊断信息
collect_diagnostics() {
    local backup_path=$1
    
    log_step "收集诊断信息..."
    
    mkdir -p "$backup_path/diagnostics"
    
    # 系统信息
    {
        uname -a
        uptime
        sw_vers  # macOS版本信息
    } > "$backup_path/diagnostics/system_info.txt"
    
    # Python信息（如果使用Python）
    if command -v python3 &> /dev/null; then
        {
            python3 --version
            pip3 list 2>/dev/null | grep -E "(prometheus|grafana)" || true
        } > "$backup_path/diagnostics/python_info.txt"
    fi
    
    log_info "诊断信息已收集"
}

# 发送通知（可选）
send_notification() {
    local status=$1
    local message=$2
    
    local webhook_url=${WEBHOOK_URL:-""}
    
    if [ -n "$webhook_url" ]; then
        local color="info"
        if [ "$status" = "success" ]; then
            color="#00ff00"
        elif [ "$status" = "error" ]; then
            color="#ff0000"
        fi
        
        # 简单的curl通知（可以自定义）
        log_info "通知已发送（模拟）"
    fi
}

###############################################################################
# 主函数
###############################################################################

rollback_execution() {
    local target_version=$1
    local force=${2:-false}
    local dry_run=${3:-false}
    
    local backup_path
    local current_link
    local current_version
    
    log_info "开始执行模块回滚流程"
    log_info "目标版本: $target_version"
    log_info "平台: macOS"
    
    if [ "$dry_run" = true ]; then
        log_warn "DRY RUN 模式：将只显示步骤，不实际执行"
    fi
    
    # 1. 验证目标版本
    log_step "验证目标版本..."
    local version_path="$VERSIONS_DIR/$target_version"
    
    if [ ! -d "$version_path" ]; then
        log_error "目标版本目录不存在: $version_path"
        log_error "请确保版本已安装在 versions/$target_version/"
        exit 1
    fi
    
    if [ ! -f "$version_path/core/execution/__init__.py" ]; then
        log_error "目标版本不包含有效的执行模块: $version_path"
        exit 1
    fi
    
    log_info "目标版本验证通过: $version_path"
    
    # 2. 创建备份
    backup_path=$(create_backup_dir)
    log_info "备份目录: $backup_path"
    
    if [ "$dry_run" = false ]; then
        backup_current_state "$backup_path"
        collect_diagnostics "$backup_path"
    else
        log_info "[DRY RUN] 将备份当前状态到: $backup_path"
    fi
    
    # 3. 获取当前版本
    if [ -L "$CORE_DIR/execution" ]; then
        current_link=$(readlink "$CORE_DIR/execution")
        current_version=$(basename "$(dirname "$current_link")")
        log_info "当前版本: $current_version"
    else
        log_warn "无法确定当前版本（可能是直接安装）"
        current_version="unknown"
    fi
    
    # 4. 确认回滚
    if [ "$force" != true ] && [ "$dry_run" = false ]; then
        echo ""
        echo -e "${YELLOW}========================================${NC}"
        echo -e "${YELLOW}回滚确认${NC}"
        echo -e "${YELLOW}========================================${NC}"
        echo "当前版本: $current_version"
        echo "目标版本: $target_version"
        echo "备份目录: $backup_path"
        echo ""
        read -p "确认执行回滚? (yes/no): " confirm
        
        if [ "$confirm" != "yes" ]; then
            log_info "回滚已取消"
            exit 0
        fi
    fi
    
    # 5. 发送回滚开始通知
    if [ "$dry_run" = false ]; then
        send_notification "开始" "正在从 $current_version 回滚到 $target_version"
    fi
    
    # 6. 停止服务
    if [ "$dry_run" = false ]; then
        stop_process
    else
        log_info "[DRY RUN] 将停止进程: $PROCESS_NAME"
    fi
    
    # 7. 切换版本
    if [ "$dry_run" = false ]; then
        log_step "切换到目标版本..."
        
        # 备份当前链接
        if [ -L "$CORE_DIR/execution" ]; then
            mv "$CORE_DIR/execution" "$backup_path/execution_link_backup"
        fi
        
        # 创建新链接
        ln -s "$version_path/core/execution" "$CORE_DIR/execution"
        
        # 验证链接
        if [ -L "$CORE_DIR/execution" ]; then
            log_info "版本切换成功"
        else
            log_error "版本切换失败"
            exit 1
        fi
    else
        log_info "[DRY RUN] 将执行版本切换"
        log_info "[DRY RUN] 当前: $CORE_DIR/execution"
        log_info "[DRY RUN] 目标: $CORE_DIR/execution -> $version_path/core/execution"
    fi
    
    # 8. 完成回滚
    if [ "$dry_run" = false ]; then
        log_info "回滚完成！"
        log_info "从版本: $current_version"
        log_info "到版本: $target_version"
        log_info "备份位置: $backup_path"
        
        send_notification "完成" "成功从 $current_version 回滚到 $target_version"
    else
        log_info "DRY RUN 完成"
    fi
    
    # 9. 后续建议
    echo ""
    log_info "后续建议:"
    echo "  1. 重启你的Athena执行模块应用"
    echo "  2. 验证应用正常运行"
    echo "  3. 检查日志: tail -f $LOG_DIR/execution.log"
    echo "  4. 验证健康检查: curl $HEALTH_CHECK_URL"
    echo "  5. 如有问题，可从备份恢复: $backup_path"
    echo ""
    echo "恢复命令（如果需要）:"
    echo "  rm $CORE_DIR/execution"
    if [ -n "$current_version" ]; then
        echo "  ln -s $VERSIONS_DIR/$current_version/core/execution $CORE_DIR/execution"
    fi
}

###############################################################################
# 脚本入口
###############################################################################

usage() {
    echo "用法: $0 <version> [选项]"
    echo ""
    echo "参数:"
    echo "  version          目标版本号 (例如: v1.0.0)"
    echo ""
    echo "选项:"
    echo "  --force          跳过确认提示"
    echo "  --dry-run        仅显示将要执行的操作，不实际执行"
    echo "  -h, --help       显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 v1.0.0                    # 回滚到v1.0.0"
    echo "  $0 v1.0.0 --force           # 强制回滚，不确认"
    echo "  $0 v1.0.0 --dry-run         # 预览回滚操作"
    echo ""
    echo "说明:"
    echo "  此脚本适用于macOS开发环境"
    echo "  生产Linux环境请使用 rollback_execution.sh"
    echo ""
    echo "环境变量:"
    echo "  ATHENA_HOME          Athena安装目录"
    echo "  WEBHOOK_URL          通知Webhook URL"
    echo "  PROCESS_NAME         进程名称"
}

main() {
    local version=""
    local force=false
    local dry_run=false
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                usage
                exit 0
                ;;
            --force)
                force=true
                shift
                ;;
            --dry-run)
                dry_run=true
                shift
                ;;
            -*)
                log_error "未知选项: $1"
                usage
                exit 1
                ;;
            *)
                version=$1
                shift
                ;;
        esac
    done
    
    # 检查版本参数
    if [ -z "$version" ]; then
        log_error "必须指定目标版本"
        usage
        exit 1
    fi
    
    # 执行回滚
    rollback_execution "$version" "$force" "$dry_run"
}

# 捕获中断信号
trap 'log_error "回滚被中断"; exit 1' INT TERM

# 执行主函数
main "$@"
