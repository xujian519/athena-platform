# 生产环境健康检查脚本
#!/bin/bash

# Athena平台生产环境健康检查
# 检查API服务、数据库连接、内存系统状态

set -euo pipefail

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 健康检查端点
HEALTH_URL="http://localhost:8005/health"
API_URL="http://localhost:8005/api/v1/status"

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

# 检查网络连接
check_network() {
    log_info "检查网络连接..."
    
    if curl -s --connect-timeout 5 "$HEALTH_URL" > /dev/null; then
        log_info "网络连接正常"
        return 0
    else
        log_error "网络连接失败"
        return 1
    fi
}

# 检查API健康状态
check_api_health() {
    log_info "检查API健康状态..."
    
    local response=$(curl -s --connect-timeout 10 "$HEALTH_URL" || echo "")
    
    if [[ $response == *"healthy"* ]] || [[ $response == *"ok"* ]]; then
        log_info "API健康状态正常"
        return 0
    else
        log_error "API健康状态异常: $response"
        return 1
    fi
}

# 检查API详细状态
check_api_status() {
    log_info "检查API详细状态..."
    
    local response=$(curl -s --connect-timeout 10 "$API_URL" || echo "")
    
    if [[ -n "$response" ]]; then
        log_info "API状态响应正常"
        
        # 尝试解析JSON状态
        if echo "$response" | python3 -c "import sys, json; json.load(sys.stdin)" 2>/dev/null; then
            local status=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('status', 'unknown'))")
            log_info "API状态: $status"
        fi
        return 0
    else
        log_error "API状态响应失败"
        return 1
    fi
}

# 检查进程状态
check_processes() {
    log_info "检查关键进程..."
    
    # 检查Python进程
    if pgrep -f "xiaonuo_unified_startup.py" > /dev/null; then
        log_info "小诺启动进程运行正常"
    else
        log_warn "小诺启动进程未运行"
    fi
    
    # 检查FastAPI进程
    if pgrep -f "uvicorn\|gunicorn" > /dev/null; then
        log_info "FastAPI服务进程运行正常"
    else
        log_warn "FastAPI服务进程未运行"
    fi
}

# 检查内存使用
check_memory() {
    log_info "检查内存使用情况..."
    
    local available_mem=$(free -m | awk 'NR==2{printf "%.1f", $7/1024}')
    local total_mem=$(free -m | awk 'NR==2{printf "%.1f", $2/1024}')
    local usage_percent=$(free -m | awk 'NR==2{printf "%.1f", ($3/$2)*100}')
    
    log_info "内存状态: ${usage_percent}% (${available_mem}GB可用 / ${total_mem}GB总量)"
    
    # 内存使用警告阈值
    if (( $(echo "$usage_percent > 80" | bc -l) )); then
        log_warn "内存使用率过高: ${usage_percent}%"
        return 1
    fi
    
    return 0
}

# 检查磁盘空间
check_disk_space() {
    log_info "检查磁盘空间..."
    
    local disk_usage=$(df /app 2>/dev/null | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [[ -n "$disk_usage" ]]; then
        log_info "磁盘使用率: ${disk_usage}%"
        
        if (( disk_usage > 85 )); then
            log_warn "磁盘使用率过高: ${disk_usage}%"
            return 1
        fi
    else
        log_warn "无法获取磁盘使用信息"
    fi
    
    return 0
}

# 检查日志文件
check_logs() {
    log_info "检查日志文件..."
    
    local log_file="/app/logs/athena.log"
    local error_count=0
    
    if [[ -f "$log_file" ]]; then
        # 检查最近1小时的错误日志
        error_count=$(tail -n 100 "$log_file" | grep -c "ERROR\|CRITICAL" || echo "0")
        
        if (( error_count > 5 )); then
            log_warn "最近发现 $error_count 个错误日志"
            return 1
        else
            log_info "日志状态正常 (错误数: $error_count)"
        fi
    else
        log_warn "日志文件不存在: $log_file"
    fi
    
    return 0
}

# 主健康检查函数
main() {
    log_info "开始Athena平台健康检查..."
    echo "=================================="
    
    local exit_code=0
    
    # 执行各项检查
    check_network || exit_code=1
    check_api_health || exit_code=1
    check_api_status || exit_code=1
    check_processes || exit_code=1
    check_memory || exit_code=1
    check_disk_space || exit_code=1
    check_logs || exit_code=1
    
    echo "=================================="
    
    if [[ $exit_code -eq 0 ]]; then
        log_info "健康检查通过 - 系统运行正常"
    else
        log_error "健康检查失败 - 发现问题需要关注"
    fi
    
    echo "$(date): Health check completed with exit code $exit_code" >> /app/logs/health-check.log
    
    return $exit_code
}

# 执行主函数
main "$@"