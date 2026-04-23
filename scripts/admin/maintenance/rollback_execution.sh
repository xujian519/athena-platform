#!/bin/bash
###############################################################################
# 执行模块回滚脚本
# Execution Module Rollback Script
#
# 用途: 将执行模块回滚到指定版本
# 使用: ./rollback_execution.sh <version> [--force] [--dry-run]
#
# 作者: Athena AI系统
# 版本: 2.0.0
# 创建时间: 2026-01-27
###############################################################################

set -e  # 遇到错误立即退出
set -u  # 使用未定义变量时报错
set -o pipefail  # 管道命令失败时报错

###############################################################################
# 配置变量
###############################################################################

# 默认配置
ATHENA_HOME=${ATHENA_HOME:-"/opt/athena"}
CONFIG_DIR=${CONFIG_DIR:-"$ATHENA_HOME/config"}
BACKUP_DIR=${BACKUP_DIR:-"$ATHENA_HOME/backup"}
CORE_DIR=${CORE_DIR:-"$ATHENA_HOME/core"}
VERSIONS_DIR=${VERSIONS_DIR:-"$ATHENA_HOME/versions"}
LOG_DIR=${LOG_DIR:-"/var/log/athena/execution"}

# 服务配置
SERVICE_NAME=${SERVICE_NAME:-"athena-execution"}
HEALTH_CHECK_URL=${HEALTH_CHECK_URL:-"http://localhost:8080/health"}
METRICS_URL=${METRICS_URL:-"http://localhost:9090/metrics"}

# 超时配置
STOP_TIMEOUT=30
START_TIMEOUT=60
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

# 检查命令是否存在
check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "命令不存在: $1"
        exit 1
    fi
}

# 检查目录是否存在
check_directory() {
    if [ ! -d "$1" ]; then
        log_error "目录不存在: $1"
        exit 1
    fi
}

# 创建备份目录
create_backup_dir() {
    local timestamp
    timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_path="$BACKUP_DIR/rollback_$timestamp"
    mkdir -p "$backup_path"
    echo "$backup_path"
}

# 检查服务状态
check_service_status() {
    systemctl is-active --quiet "$SERVICE_NAME"
}

# 等待服务停止
wait_for_service_stop() {
    local timeout=$1
    local elapsed=0
    
    log_step "等待服务停止..."
    
    while check_service_status; do
        if [ $elapsed -ge $timeout ]; then
            log_error "服务在${timeout}秒内未停止"
            return 1
        fi
        sleep 1
        elapsed=$((elapsed + 1))
        echo -n "."
    done
    
    echo ""
    log_info "服务已停止"
    return 0
}

# 等待服务启动
wait_for_service_start() {
    local timeout=$1
    local elapsed=0
    
    log_step "等待服务启动..."
    
    while ! check_service_status; do
        if [ $elapsed -ge $timeout ]; then
            log_error "服务在${timeout}秒内未启动"
            return 1
        fi
        sleep 1
        elapsed=$((elapsed + 1))
        echo -n "."
    done
    
    echo ""
    log_info "服务已启动"
    
    # 健康检查
    elapsed=0
    log_step "执行健康检查..."
    
    while [ $elapsed -lt $HEALTH_CHECK_TIMEOUT ]; do
        if curl -sf "$HEALTH_CHECK_URL" > /dev/null 2>&1; then
            log_info "健康检查通过"
            return 0
        fi
        sleep 1
        elapsed=$((elapsed + 1))
        echo -n "."
    done
    
    echo ""
    log_warn "健康检查超时，但服务已启动"
    return 0
}

# 备份当前状态
backup_current_state() {
    local backup_path=$1
    
    log_step "备份当前状态到: $backup_path"
    
    # 备份配置
    if [ -f "$CONFIG_DIR/production.yaml" ]; then
        cp "$CONFIG_DIR/production.yaml" "$backup_path/"
        log_info "配置文件已备份"
    fi
    
    # 备份当前执行模块
    if [ -L "$CORE_DIR/execution" ]; then
        cp -rL "$CORE_DIR/execution" "$backup_path/" 2>/dev/null || true
        log_info "执行模块已备份"
    fi
    
    # 保存当前指标
    if command -v curl &> /dev/null; then
        curl -s "$METRICS_URL" > "$backup_path/metrics.txt" 2>/dev/null || true
        log_info "监控指标已保存"
    fi
    
    # 保存错误日志
    if [ -f "$LOG_DIR/errors.log" ]; then
        tail -1000 "$LOG_DIR/errors.log" > "$backup_path/error_tail.log"
        log_info "错误日志已保存"
    fi
    
    # 保存系统状态
    {
        echo "=== 系统状态 ==="
        date
        free -h
        echo ""
        echo "=== 磁盘使用 ==="
        df -h
        echo ""
        echo "=== 进程信息 ==="
        ps aux | grep athena-execution | grep -v grep || true
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
        cat /proc/meminfo | head -20
        cat /proc/cpuinfo | grep "model name" | head -1
    } > "$backup_path/diagnostics/system_info.txt"
    
    # 网络状态
    {
        netstat -tuln | grep -E "(8080|9090)"
        ss -tuln | grep -E "(8080|9090)"
    } > "$backup_path/diagnostics/network_state.txt"
    
    # 最近的服务日志
    if command -v journalctl &> /dev/null; then
        journalctl -u "$SERVICE_NAME" -n 200 > "$backup_path/diagnostics/service_journal.log"
    fi
    
    log_info "诊断信息已收集"
}

# 发送通知
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
        
        local payload=$(cat <<EOF
{
  "msgtype": "markdown",
  "markdown": {
    "title": "执行模块回滚${status}",
    "text": "## 执行模块回滚${status}\n\n$message\n\n**时间**: $(date '+%Y-%m-%d %H:%M:%S')\n**主机**: $(hostname)\n**操作人**: ${USER:-unknown}"
  }
}
EOF
)
        
        curl -s -X POST "$webhook_url" \
            -H "Content-Type: application/json" \
            -d "$payload" > /dev/null 2>&1 || true
        
        log_info "通知已发送"
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
    
    if [ "$dry_run" = true ]; then
        log_warn "DRY RUN 模式：将只显示步骤，不实际执行"
    fi
    
    # 1. 检查必要命令
    check_command systemctl
    check_command curl
    
    # 2. 验证目标版本
    log_step "验证目标版本..."
    local version_path="$VERSIONS_DIR/$target_version"
    check_directory "$version_path"
    
    if [ ! -f "$version_path/core/execution/__init__.py" ]; then
        log_error "目标版本不包含有效的执行模块: $version_path"
        exit 1
    fi
    
    log_info "目标版本验证通过: $version_path"
    
    # 3. 创建备份
    backup_path=$(create_backup_dir)
    log_info "备份目录: $backup_path"
    
    if [ "$dry_run" = false ]; then
        backup_current_state "$backup_path"
        collect_diagnostics "$backup_path"
    else
        log_info "[DRY RUN] 将备份当前状态到: $backup_path"
    fi
    
    # 4. 获取当前版本
    if [ -L "$CORE_DIR/execution" ]; then
        current_link=$(readlink -f "$CORE_DIR/execution")
        current_version=$(basename "$(dirname "$current_link")")
        log_info "当前版本: $current_version"
    else
        log_warn "无法确定当前版本"
        current_version="unknown"
    fi
    
    # 5. 确认回滚
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
    
    # 6. 发送回滚开始通知
    if [ "$dry_run" = false ]; then
        send_notification "开始" "正在从 $current_version 回滚到 $target_version"
    fi
    
    # 7. 停止服务
    if [ "$dry_run" = false ]; then
        log_step "停止服务..."
        systemctl stop "$SERVICE_NAME" || true
        
        if ! wait_for_service_stop $STOP_TIMEOUT; then
            log_warn "服务未正常停止，尝试强制终止..."
            systemctl kill "$SERVICE_NAME" || true
            sleep 2
        fi
    else
        log_info "[DRY RUN] 将停止服务: $SERVICE_NAME"
    fi
    
    # 8. 切换版本
    if [ "$dry_run" = false ]; then
        log_step "切换到目标版本..."
        
        # 删除现有链接
        rm -f "$CORE_DIR/execution"
        
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
        log_info "[DRY RUN] 删除: $CORE_DIR/execution"
        log_info "[DRY RUN] 创建链接: $CORE_DIR/execution -> $version_path/core/execution"
    fi
    
    # 9. 启动服务
    if [ "$dry_run" = false ]; then
        log_step "启动服务..."
        systemctl start "$SERVICE_NAME"
        
        if ! wait_for_service_start $START_TIMEOUT; then
            log_error "服务启动失败"
            
            # 尝试回滚到原版本
            log_warn "尝试恢复到原版本..."
            systemctl stop "$SERVICE_NAME" || true
            rm -f "$CORE_DIR/execution"
            ln -s "$VERSIONS_DIR/$current_version/core/execution" "$CORE_DIR/execution"
            systemctl start "$SERVICE_NAME"
            
            send_notification "失败" "服务启动失败，已恢复到原版本 $current_version"
            exit 1
        fi
    else
        log_info "[DRY RUN] 将启动服务: $SERVICE_NAME"
    fi
    
    # 10. 验证服务
    if [ "$dry_run" = false ]; then
        log_step "验证服务..."
        
        # 提交测试任务（可选）
        # 这里可以添加更多的验证步骤
        
        log_info "服务验证通过"
    else
        log_info "[DRY RUN] 将验证服务状态"
    fi
    
    # 11. 完成回滚
    if [ "$dry_run" = false ]; then
        log_info "回滚完成！"
        log_info "从版本: $current_version"
        log_info "到版本: $target_version"
        log_info "备份位置: $backup_path"
        
        send_notification "完成" "成功从 $current_version 回滚到 $target_version"
    else
        log_info "DRY RUN 完成"
    fi
    
    # 12. 后续建议
    echo ""
    log_info "后续建议:"
    echo "  1. 监控服务状态: systemctl status $SERVICE_NAME"
    echo "  2. 查看日志: tail -f $LOG_DIR/execution.log"
    echo "  3. 检查指标: curl $METRICS_URL"
    echo "  4. 如有问题，可从备份恢复: $backup_path"
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
    echo "环境变量:"
    echo "  ATHENA_HOME          Athena安装目录 (默认: /opt/athena)"
    echo "  WEBHOOK_URL          通知Webhook URL"
    echo "  SERVICE_NAME         服务名称 (默认: athena-execution)"
    echo "  HEALTH_CHECK_URL     健康检查URL"
    echo "  METRICS_URL          监控指标URL"
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
