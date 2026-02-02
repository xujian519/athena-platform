#!/bin/bash

# 后台任务清理脚本
# Background Tasks Cleanup Script

# 设置严格模式
set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示当前后台任务
show_background_tasks() {
    log_info "当前运行的后台任务："
    echo ""
    
    # 1. Athena相关进程
    echo "🔧 Athena相关进程："
    pgrep -f "athena|Athena" | while read pid; do
        if [[ -n "$pid" ]]; then
            ps -p "$pid" -o pid,ppid,time,command | tail -n +2
        fi
    done
    echo ""
    
    # 2. 优化工具进程
    echo "📊 优化工具进程："
    pgrep -f "memory_optimizer|performance_dashboard|optimize_system" | while read pid; do
        if [[ -n "$pid" ]]; then
            ps -p "$pid" -o pid,ppid,time,command | tail -n +2
        fi
    done
    echo ""
    
    # 3. 数据服务进程
    echo "💾 数据服务进程："
    echo "Neo4j进程："
    pgrep -f "neo4j" | while read pid; do
        if [[ -n "$pid" ]]; then
            ps -p "$pid" -o pid,ppid,time,%cpu,%mem,command | tail -n +2
        fi
    done
    
    echo "Redis进程："
    pgrep -f "redis-server" | while read pid; do
        if [[ -n "$pid" ]]; then
            ps -p "$pid" -o pid,ppid,time,%cpu,%mem,command | tail -n +2
        fi
    done
    
    echo "Ollama进程："
    pgrep -f "ollama" | while read pid; do
        if [[ -n "$pid" ]]; then
            ps -p "$pid" -o pid,ppid,time,%cpu,%mem,command | tail -n +2
        fi
    done
    echo ""
    
    # 4. MCP服务器进程
    echo "🔌 MCP服务器进程："
    pgrep -f "mcp-server" | while read pid; do
        if [[ -n "$pid" ]]; then
            ps -p "$pid" -o pid,ppid,time,command | tail -n +2
        fi
    done
    echo ""
    
    # 5. 其他Python后台任务
    echo "🐍 Python后台任务："
    pgrep -f "nohup.*python" | while read pid; do
        if [[ -n "$pid" ]]; then
            ps -p "$pid" -o pid,ppid,time,command | tail -n +2
        fi
    done
    echo ""
}

# 清理特定类型的任务
cleanup_athena_tasks() {
    log_info "清理Athena相关任务..."
    
    # 停止内存优化器
    if [[ -f "logs/memory_monitor.pid" ]]; then
        PID=$(cat logs/memory_monitor.pid)
        if kill -0 "$PID" 2>/dev/null; then
            kill "$PID"
            log_info "已停止内存优化器 (PID: $PID)"
        fi
        rm -f logs/memory_monitor.pid
    fi
    
    # 停止性能监控
    if [[ -f "logs/performance_monitor.pid" ]]; then
        PID=$(cat logs/performance_monitor.pid)
        if kill -0 "$PID" 2>/dev/null; then
            kill "$PID"
            log_info "已停止性能监控 (PID: $PID)"
        fi
        rm -f logs/performance_monitor.pid
    fi
    
    # 停止健康检查
    if [[ -f "logs/health_monitor.pid" ]]; then
        PID=$(cat logs/health_monitor.pid)
        if kill -0 "$PID" 2>/dev/null; then
            kill "$PID"
            log_info "已停止健康检查 (PID: $PID)"
        fi
        rm -f logs/health_monitor.pid
    fi
    
    # 停止其他Athena相关进程
    pkill -f "memory_optimizer.py" 2>/dev/null || true
    pkill -f "performance_dashboard.py" 2>/dev/null || true
    pkill -f "optimize_system_performance.py" 2>/dev/null || true
    
    log_info "Athena任务清理完成"
}

cleanup_data_services() {
    log_info "清理数据服务..."
    
    # 停止Neo4j
    pgrep -f "neo4j" | while read pid; do
        if [[ -n "$pid" ]]; then
            kill "$pid" 2>/dev/null || true
            log_info "已停止Neo4j (PID: $pid)"
        fi
    done
    
    # 停止Redis
    pgrep -f "redis-server" | while read pid; do
        if [[ -n "$pid" ]]; then
            kill "$pid" 2>/dev/null || true
            log_info "已停止Redis (PID: $pid)"
        fi
    done
    
    # 停止Ollama
    pgrep -f "ollama serve" | while read pid; do
        if [[ -n "$pid" ]]; then
            kill "$pid" 2>/dev/null || true
            log_info "已停止Ollama (PID: $pid)"
        fi
    done
    
    # 停止Qdrant（如果运行）
    pgrep -f "qdrant" | while read pid; do
        if [[ -n "$pid" ]]; then
            kill "$pid" 2>/dev/null || true
            log_info "已停止Qdrant (PID: $pid)"
        fi
    done
    
    log_info "数据服务清理完成"
}

cleanup_mcp_servers() {
    log_info "清理MCP服务器..."
    
    # 停止所有MCP服务器
    pgrep -f "mcp-server" | while read pid; do
        if [[ -n "$pid" ]]; then
            kill "$pid" 2>/dev/null || true
            log_info "已停止MCP服务器 (PID: $pid)"
        fi
    done
    
    # 停止npm exec进程
    pgrep -f "npm exec.*mcp" | while read pid; do
        if [[ -n "$pid" ]]; then
            kill "$pid" 2>/dev/null || true
            log_info "已停止npm MCP进程 (PID: $pid)"
        fi
    done
    
    log_info "MCP服务器清理完成"
}

cleanup_python_tasks() {
    log_info "清理Python后台任务..."
    
    # 停止nohup python进程
    pgrep -f "nohup.*python" | while read pid; do
        if [[ -n "$pid" ]]; then
            # 确保不是系统重要进程
            cmd=$(ps -p "$pid" -o command= 2>/dev/null || echo "")
            if [[ "$cmd" == *"nohup"* ]] && [[ "$cmd" == *"/Users/xujian/Athena"* ]]; then
                kill "$pid" 2>/dev/null || true
                log_info "已停止Python后台任务 (PID: $pid)"
            fi
        fi
    done
    
    log_info "Python任务清理完成"
}

# 强制清理所有相关进程
force_cleanup() {
    log_warn "强制清理所有相关进程..."
    
    # 强制终止相关进程
    pkill -9 -f "memory_optimizer.py" 2>/dev/null || true
    pkill -9 -f "performance_dashboard.py" 2>/dev/null || true
    pkill -9 -f "optimize_system_performance.py" 2>/dev/null || true
    pkill -9 -f "mcp-server" 2>/dev/null || true
    pkill -9 -f "npm exec.*@modelcontextprotocol" 2>/dev/null || true
    
    log_warn "强制清理完成"
}

# 显示内存使用情况
show_memory_usage() {
    log_info "当前内存使用情况："
    echo ""
    
    # 总体内存
    echo "📊 系统内存："
    vm_stat | awk '
        /Pages free/ {free_pages=$3}
        /Pages active/ {active_pages=$3}
        /Pages inactive/ {inactive_pages=$3}
        /Pages wired/ {wired_pages=$3}
        END {
            page_size=4096
            free=free_pages*page_size/1024/1024
            active=active_pages*page_size/1024/1024
            inactive=inactive_pages*page_size/1024/1024
            wired=wired_pages*page_size/1024/1024
            total=free+active+inactive+wired
            printf "  总计: %.1f GB\n", total/1024
            printf "  已用: %.1f GB (%.1f%%)\n", (active+inactive+wired)/1024, ((active+inactive+wired)/total)*100
            printf "  空闲: %.1f GB (%.1f%%)\n", free/1024, (free/total)*100
        }'
    
    echo ""
    echo "🔋 内存占用最高的进程："
    ps aux | sort -rk 4,4 | head -10 | awk 'NR>1 {printf "  %-10s %5.1f%%  %s\n", $1, $4, $11}'
    
    echo ""
}

# 清理临时文件
cleanup_temp_files() {
    log_info "清理临时文件..."
    
    # 清理PID文件
    find logs -name "*.pid" -type f -delete 2>/dev/null || true
    
    # 清理临时日志
    find logs -name "*.tmp" -type f -delete 2>/dev/null || true
    
    # 清理Python缓存
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    
    log_info "临时文件清理完成"
}

# 主函数
main() {
    echo "🧹 Athena后台任务清理工具"
    echo "=========================="
    echo ""
    
    # 显示当前状态
    show_background_tasks
    show_memory_usage
    
    echo "🛠️ 清理选项："
    echo "1) 仅清理Athena优化任务"
    echo "2) 仅清理数据服务（Neo4j, Redis, Ollama）"
    echo "3) 仅清理MCP服务器"
    echo "4) 仅清理Python后台任务"
    echo "5) 清理所有相关任务"
    echo "6) 强制清理所有相关进程"
    echo "7) 仅显示状态，不清理"
    echo ""
    
    read -p "请选择清理选项 (1-7): " choice
    
    case $choice in
        1)
            cleanup_athena_tasks
            cleanup_temp_files
            ;;
        2)
            cleanup_data_services
            ;;
        3)
            cleanup_mcp_servers
            ;;
        4)
            cleanup_python_tasks
            ;;
        5)
            cleanup_athena_tasks
            cleanup_data_services
            cleanup_mcp_servers
            cleanup_python_tasks
            cleanup_temp_files
            ;;
        6)
            force_cleanup
            cleanup_temp_files
            ;;
        7)
            log_info "仅显示状态，不执行清理"
            ;;
        *)
            log_error "无效选项"
            exit 1
            ;;
    esac
    
    echo ""
    log_info "清理操作完成！"
    
    # 显示清理后的状态
    echo ""
    show_memory_usage
}

# 错误处理
trap 'log_error "清理过程中发生错误"; exit 1' ERR

# 运行主函数
main "$@"