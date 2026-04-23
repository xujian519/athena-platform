#!/bin/bash
################################################################################
# Athena平台 - 统一PID文件管理脚本
# Unified PID File Management Script
#
# 功能：
#   1. 统一管理所有服务的PID文件
#   2. 提供PID文件的创建、删除、查询功能
#   3. 自动清理过期的PID文件
#   4. 支持服务健康检查
#
# 使用方法：
#   ./scripts/pid_manager.sh [service] [action]
#
# 示例：
#   ./scripts/pid_manager.sh xiaonuo start     # 启动并记录PID
#   ./scripts/pid_manager.sh xiaonuo stop      # 停止并清理PID
#   ./scripts/pid_manager.sh xiaonuo status    # 查看状态
#   ./scripts/pid_manager.sh cleanup           # 清理所有过期PID
#
# 作者: 徐健 (xujian519@gmail.com)
# 创建: 2026-04-22
################################################################################

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="/Users/xujian/Athena工作平台"

# 统一PID目录
PID_DIR="$PROJECT_ROOT/logs/pid"
mkdir -p "$PID_DIR"

# 服务配置（使用函数而非关联数组，提高兼容性）
get_service_command() {
    case "$1" in
        xiaonuo)
            echo "python3 scripts/xiaonuo_unified_startup.py"
            ;;
        gateway)
            echo "cd gateway-unified && sudo bash quick-deploy-macos.sh"
            ;;
        nlp_service)
            echo "python3 -m core.services.nlp_service"
            ;;
        orchestrator)
            echo "python3 -m core.orchestration.orchestrator"
            ;;
        patent_api)
            echo "python3 apps/patent-platform/workspace/src/api/patent_analysis_api.py"
            ;;
        multimodal_api)
            echo "python3 api/multimodal_api.py"
            ;;
        image_api)
            echo "python3 api/patent_image_api.py"
            ;;
        *)
            echo ""
            ;;
    esac
}

# 获取所有服务列表
get_all_services() {
    echo "xiaonuo gateway nlp_service orchestrator patent_api multimodal_api image_api"
}

# 日志函数
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

# 获取PID文件路径
get_pid_file() {
    local service=$1
    echo "$PID_DIR/${service}.pid"
}

# 检查进程是否运行
is_process_running() {
    local pid=$1
    if [[ -z "$pid" ]]; then
        return 1
    fi

    # 检查进程是否存在
    if ps -p "$pid" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# 创建PID文件
create_pid_file() {
    local service=$1
    local pid=$2
    local pid_file=$(get_pid_file "$service")

    echo "$pid" > "$pid_file"
    log_success "PID文件已创建: $pid_file (PID: $pid)"
}

# 删除PID文件
remove_pid_file() {
    local service=$1
    local pid_file=$(get_pid_file "$service")

    if [[ -f "$pid_file" ]]; then
        rm -f "$pid_file"
        log_success "PID文件已删除: $pid_file"
    else
        log_warning "PID文件不存在: $pid_file"
    fi
}

# 读取PID文件
read_pid_file() {
    local service=$1
    local pid_file=$(get_pid_file "$service")

    if [[ -f "$pid_file" ]]; then
        cat "$pid_file"
    else
        echo ""
    fi
}

# 启动服务
start_service() {
    local service=$1
    local start_cmd=$(get_service_command "$service")

    if [[ -z "$start_cmd" ]]; then
        log_error "未知的服务: $service"
        log_info "可用服务: $(get_all_services)"
        exit 1
    fi

    # 检查是否已运行
    local existing_pid=$(read_pid_file "$service")
    if [[ -n "$existing_pid" ]] && is_process_running "$existing_pid"; then
        log_warning "服务 $service 已在运行 (PID: $existing_pid)"
        return 0
    fi

    log_info "正在启动服务: $service"

    cd "$PROJECT_ROOT"

    # 启动服务并获取PID
    if [[ "$service" == "gateway" ]]; then
        # Gateway需要sudo，特殊处理
        eval "$start_cmd" > /dev/null 2>&1 &
        sleep 2  # 等待启动
        # Gateway的PID需要通过其他方式获取
        log_info "Gateway服务启动中..."
    else
        # 普通Python服务
        eval "$start_cmd" > "$PROJECT_ROOT/logs/${service}.log" 2>&1 &
        local new_pid=$!
        create_pid_file "$service" "$new_pid"
        log_success "服务 $service 已启动 (PID: $new_pid)"
    fi
}

# 停止服务
stop_service() {
    local service=$1
    local pid=$(read_pid_file "$service")

    if [[ -z "$pid" ]]; then
        log_warning "未找到服务 $service 的PID文件"
        return 0
    fi

    if ! is_process_running "$pid"; then
        log_warning "服务 $service 未运行 (PID: $pid)"
        remove_pid_file "$service"
        return 0
    fi

    log_info "正在停止服务: $service (PID: $pid)"

    # 发送TERM信号
    kill "$pid" 2>/dev/null || true

    # 等待进程结束（最多5秒）
    local count=0
    while is_process_running "$pid" && [[ $count -lt 5 ]]; do
        sleep 1
        count=$((count + 1))
    done

    # 如果进程仍在运行，强制杀死
    if is_process_running "$pid"; then
        log_warning "强制终止服务: $service"
        kill -9 "$pid" 2>/dev/null || true
        sleep 1
    fi

    # 清理PID文件
    remove_pid_file "$service"
    log_success "服务 $service 已停止"
}

# 查看服务状态
show_status() {
    local service=$1

    if [[ "$service" == "all" ]]; then
        echo "=== 所有服务状态 ==="
        echo ""
        for svc in $(get_all_services); do
            show_single_status "$svc"
        done
    else
        show_single_status "$service"
    fi
}

# 显示单个服务状态
show_single_status() {
    local service=$1
    local pid=$(read_pid_file "$service")

    echo -n "[$service] "

    if [[ -z "$pid" ]]; then
        echo -e "${YELLOW}未启动${NC} (无PID文件)"
        return
    fi

    if is_process_running "$pid"; then
        echo -e "${GREEN}运行中${NC} (PID: $pid)"

        # 显示进程信息
        local cmd=$(ps -p "$pid" -o command= 2>/dev/null | head -c 80)
        if [[ -n "$cmd" ]]; then
            echo "  命令: $cmd..."
        fi
    else
        echo -e "${RED}已停止${NC} (PID文件存在但进程不存在)"
    fi
}

# 清理过期PID文件
cleanup_pid_files() {
    log_info "正在清理过期的PID文件..."

    local cleaned=0
    for pid_file in "$PID_DIR"/*.pid; do
        if [[ -f "$pid_file" ]]; then
            local pid=$(cat "$pid_file")
            if ! is_process_running "$pid"; then
                log_info "删除过期PID文件: $(basename "$pid_file")"
                rm -f "$pid_file"
                cleaned=$((cleaned + 1))
            fi
        fi
    done

    log_success "清理完成，删除了 $cleaned 个过期PID文件"
}

# 迁移旧的PID文件
migrate_old_pid_files() {
    log_info "正在迁移旧的PID文件..."

    local migrated=0

    # 从apps/xiaonuo迁移
    for old_pid in "$PROJECT_ROOT/apps/xiaonuo"/*.pid; do
        if [[ -f "$old_pid" ]]; then
            local basename=$(basename "$old_pid" .pid)
            local new_pid="$PID_DIR/${basename}.pid"
            if [[ ! -f "$new_pid" ]]; then
                mv "$old_pid" "$new_pid"
                log_info "迁移: $old_pid -> $new_pid"
                migrated=$((migrated + 1))
            fi
        fi
    done

    # 从data/迁移
    for old_pid in "$PROJECT_ROOT/data"/*.pid; do
        if [[ -f "$old_pid" ]]; then
            local basename=$(basename "$old_pid" .pid)
            local new_pid="$PID_DIR/${basename}.pid"
            if [[ ! -f "$new_pid" ]]; then
                mv "$old_pid" "$new_pid"
                log_info "迁移: $old_pid -> $new_pid"
                migrated=$((migrated + 1))
            fi
        fi
    done

    # 从logs/迁移（保留服务PID，删除其他）
    for old_pid in "$PROJECT_ROOT/logs"/*.pid; do
        if [[ -f "$old_pid" ]]; then
            local basename=$(basename "$old_pid" .pid)
            # 只迁移特定服务
            if [[ "$basename" =~ ^(xiaonuo|xiaona|gateway|agents)$ ]]; then
                local new_pid="$PID_DIR/${basename}.pid"
                if [[ ! -f "$new_pid" ]]; then
                    cp "$old_pid" "$new_pid"
                    log_info "复制: $old_pid -> $new_pid"
                    migrated=$((migrated + 1))
                fi
            fi
        fi
    done

    log_success "迁移完成，处理了 $migrated 个PID文件"
}

# 显示帮助信息
show_help() {
    cat << EOF
Athena平台 - 统一PID文件管理脚本

用法:
    $0 [service] [action]
    $0 [action]

服务列表:
    all              - 所有服务
    xiaonuo          - 小诺统一智能体（包含小娜能力）
    gateway          - Gateway网关
    nlp_service      - NLP服务
    orchestrator     - 编排器
    patent_api       - 专利分析API
    multimodal_api   - 多模态API
    image_api        - 图像分析API

操作:
    start            - 启动服务
    stop             - 停止服务
    restart          - 重启服务
    status           - 查看状态
    cleanup          - 清理过期PID文件
    migrate          - 迁移旧PID文件
    help             - 显示帮助信息

示例:
    $0 xiaonuo start          # 启动小诺统一服务（包含小娜能力）
    $0 xiaonuo status         # 查看小诺状态
    $0 all status             # 查看所有服务状态
    $0 cleanup                # 清理过期PID文件
    $0 migrate                # 迁移旧PID文件

注意:
    - 小娜的专业代理（申请审查、侵权分析等）已整合到小诺统一架构
    - 通过小诺的ReAct循环自动调用，无需单独启动
    - 详见: core/agents/xiaona/DEPRECATED.md

PID文件位置:
    $PID_DIR

EOF
}

# 主函数
main() {
    # 如果没有参数，显示帮助
    if [[ $# -eq 0 ]]; then
        show_help
        exit 0
    fi

    local service=$1
    local action=$2

    # 检查是否是全局操作（不需要服务名）
    if [[ "$service" =~ ^(cleanup|migrate|help|--help|-h)$ ]]; then
        case "$service" in
            cleanup)
                cleanup_pid_files
                ;;
            migrate)
                migrate_old_pid_files
                ;;
            help|--help|-h)
                show_help
                ;;
        esac
        exit 0
    fi

    # 检查服务是否存在
    local valid_service=false
    if [[ "$service" == "all" ]]; then
        valid_service=true
    else
        for svc in $(get_all_services); do
            if [[ "$svc" == "$service" ]]; then
                valid_service=true
                break
            fi
        done
    fi

    if [[ "$valid_service" == "false" ]]; then
        log_error "未知的服务: $service"
        log_info "可用服务: $(get_all_services)"
        exit 1
    fi

    # 执行操作
    case "$action" in
        start)
            if [[ "$service" == "all" ]]; then
                for svc in $(get_all_services); do
                    start_service "$svc"
                done
            else
                start_service "$service"
            fi
            ;;
        stop)
            if [[ "$service" == "all" ]]; then
                for svc in $(get_all_services); do
                    stop_service "$svc"
                done
            else
                stop_service "$service"
            fi
            ;;
        restart)
            if [[ "$service" == "all" ]]; then
                for svc in $(get_all_services); do
                    stop_service "$svc"
                done
                sleep 2
                for svc in $(get_all_services); do
                    start_service "$svc"
                done
            else
                stop_service "$service"
                sleep 2
                start_service "$service"
            fi
            ;;
        status)
            show_status "$service"
            ;;
        "")
            log_error "请指定操作: start|stop|restart|status"
            show_help
            exit 1
            ;;
        *)
            log_error "未知操作: $action"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
