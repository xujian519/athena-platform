#!/bin/bash
# -*- coding: utf-8 -*-
# Nginx爬虫负载均衡器管理脚本
# Nginx Crawler Load Balancer Management Script - Controlled by Athena & 小诺

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# 平台信息
PLATFORM_NAME="Athena工作平台"
PLATFORM_OWNER="Athena & 小诺"

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 配置文件
NGINX_CONF="$PROJECT_ROOT/nginx/nginx_crawler.conf"
NGINX_DIR="$PROJECT_ROOT/nginx"
NGINX_PID_DIR="$PROJECT_ROOT/tmp/nginx"
NGINX_LOG_DIR="$PROJECT_ROOT/logs/nginx"

# Nginx可执行文件
NGINX_BIN="/usr/local/bin/nginx"
if [[ ! -f "$NGINX_BIN" ]]; then
    NGINX_BIN="/usr/sbin/nginx"
fi
if [[ ! -f "$NGINX_BIN" ]]; then
    NGINX_BIN="nginx"
fi

# 创建必要目录
create_directories() {
    local dirs=("$NGINX_PID_DIR" "$NGINX_LOG_DIR")
    for dir in "${dirs[@]}"; do
        mkdir -p "$dir"
    done
}

# 打印平台标识
print_banner() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    ${PLATFORM_NAME}                       ║"
    echo "║              Nginx爬虫负载均衡器管理脚本                      ║"
    echo "║                 控制者: ${PLATFORM_OWNER}                      ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# 打印彩色信息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_platform() {
    echo -e "${PURPLE}[PLATFORM]${NC} $1"
}

# 检查依赖
check_dependencies() {
    print_info "检查Nginx依赖..."

    # 检查Nginx是否安装
    if ! command -v $NGINX_BIN &> /dev/null; then
        print_error "Nginx未安装，请先安装Nginx"
        print_info "macOS: brew install nginx"
        print_info "Ubuntu: sudo apt-get install nginx"
        exit 1
    fi

    # 检查配置文件
    if [[ ! -f "$NGINX_CONF" ]]; then
        print_error "Nginx配置文件不存在: $NGINX_CONF"
        exit 1
    fi

    # 检查SSL证书
    local ssl_cert="$PROJECT_ROOT/ssl/crawler.crt"
    local ssl_key="$PROJECT_ROOT/ssl/crawler.key"

    if [[ ! -f "$ssl_cert" || ! -f "$ssl_key" ]]; then
        print_warning "SSL证书不存在，将生成自签名证书"
        if [[ -f "$PROJECT_ROOT/ssl/generate_certificates.sh" ]]; then
            "$PROJECT_ROOT/ssl/generate_certificates.sh"
        else
            print_error "SSL证书生成脚本不存在"
            exit 1
        fi
    fi

    print_success "依赖检查通过"
}

# 测试配置文件
test_config() {
    print_info "测试Nginx配置..."

    if $NGINX_BIN -t -c "$NGINX_CONF"; then
        print_success "配置文件测试通过"
        return 0
    else
        print_error "配置文件测试失败"
        return 1
    fi
}

# 获取Nginx进程ID
get_nginx_pid() {
    if [[ -f "$NGINX_PID_DIR/nginx.pid" ]]; then
        local pid=$(cat "$NGINX_PID_DIR/nginx.pid")
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "$pid"
            return 0
        else
            rm -f "$NGINX_PID_DIR/nginx.pid"
            return 1
        fi
    fi
    return 1
}

# 检查Nginx状态
check_status() {
    local pid=$(get_nginx_pid)
    if [[ -n "$pid" ]]; then
        echo "running"
        return 0
    else
        echo "stopped"
        return 1
    fi
}

# 启动Nginx
start_nginx() {
    print_platform "启动Nginx负载均衡器..."

    # 检查是否已运行
    if [[ "$(check_status)" == "running" ]]; then
        print_warning "Nginx已在运行中"
        return 0
    fi

    # 创建目录
    create_directories

    # 测试配置
    if ! test_config; then
        print_error "配置文件有误，启动失败"
        return 1
    fi

    # 启动Nginx
    print_info "正在启动Nginx..."
    $NGINX_BIN -c "$NGINX_CONF" -g "pid $NGINX_PID_DIR/nginx.pid;"

    # 等待启动
    sleep 2

    # 检查状态
    if [[ "$(check_status)" == "running" ]]; then
        local pid=$(get_nginx_pid)
        print_success "Nginx启动成功！"
        print_info "进程ID: $pid"
        print_info "HTTPS访问: https://crawler.localhost"
        print_info "管理后台: https://admin.crawler.localhost:8443"
        return 0
    else
        print_error "Nginx启动失败"
        print_info "查看日志: tail -f $NGINX_LOG_DIR/error.log"
        return 1
    fi
}

# 停止Nginx
stop_nginx() {
    print_platform "停止Nginx负载均衡器..."

    local pid=$(get_nginx_pid)
    if [[ -z "$pid" ]]; then
        print_warning "Nginx未运行"
        return 0
    fi

    print_info "正在停止Nginx (PID: $pid)..."

    # 优雅停止
    $NGINX_BIN -s stop -c "$NGINX_CONF"

    # 等待进程结束
    local count=0
    while ps -p "$pid" > /dev/null 2>&1 && [[ $count -lt 10 ]]; do
        sleep 1
        ((count++))
    done

    # 强制停止
    if ps -p "$pid" > /dev/null 2>&1; then
        print_warning "Nginx未正常停止，强制终止..."
        kill -9 "$pid"
    fi

    # 清理PID文件
    rm -f "$NGINX_PID_DIR/nginx.pid"

    print_success "Nginx已停止"
}

# 重启Nginx
restart_nginx() {
    print_platform "重启Nginx负载均衡器..."
    stop_nginx
    sleep 2
    start_nginx
}

# 重新加载配置
reload_nginx() {
    print_platform "重新加载Nginx配置..."

    if [[ "$(check_status)" != "running" ]]; then
        print_warning "Nginx未运行，将直接启动"
        start_nginx
        return 0
    fi

    # 测试配置
    if ! test_config; then
        print_error "配置文件有误，重新加载失败"
        return 1
    fi

    # 重新加载
    $NGINX_BIN -s reload -c "$NGINX_CONF"

    print_success "配置重新加载成功"
}

# 显示状态
show_status() {
    print_platform "Nginx负载均衡器状态"
    echo "================================"

    local status=$(check_status)
    local pid=$(get_nginx_pid)

    echo -e "状态: $([ "$status" == "running" ] && echo -e "${GREEN}运行中${NC}" || echo -e "${RED}已停止${NC}")"
    [[ -n "$pid" ]] && echo "进程ID: $pid"

    # 显示监听端口
    echo ""
    echo "监听端口:"
    if command -v lsof &> /dev/null; then
        echo "  HTTP: 80 (重定向到HTTPS)"
        echo "  HTTPS: 443"
        echo "  管理后台: 8443"
    fi

    # 显示配置信息
    echo ""
    echo "配置信息:"
    echo "  配置文件: $NGINX_CONF"
    echo "  SSL证书: $PROJECT_ROOT/ssl/crawler.crt"
    echo "  日志目录: $NGINX_LOG_DIR"
    echo "  PID目录: $NGINX_PID_DIR"

    # 显示后端状态
    echo ""
    echo "后端状态:"
    if command -v curl &> /dev/null; then
        if curl -s http://localhost:8002/health &> /dev/null; then
            echo "  爬虫服务: ${GREEN}运行中${NC}"
        else
            echo "  爬虫服务: ${RED}未运行${NC}"
        fi
    fi
}

# 测试访问
test_access() {
    print_platform "测试Nginx访问..."

    local endpoints=(
        "http://crawler.localhost"
        "https://crawler.localhost"
        "http://crawler.localhost/health"
        "https://crawler.localhost/health"
        "https://crawler.localhost/docs"
    )

    for endpoint in "${endpoints[@]}"; do
        echo -n "测试 $endpoint ... "
        if curl -s -k -m 5 "$endpoint" > /dev/null; then
            echo -e "${GREEN}✅ 可访问${NC}"
        else
            echo -e "${RED}❌ 不可访问${NC}"
        fi
    done
}

# 显示日志
show_logs() {
    local follow=false
    local lines=50
    local log_type="access"

    while [[ $# -gt 0 ]]; do
        case $1 in
            -f|--follow)
                follow=true
                shift
                ;;
            -n|--lines)
                lines="$2"
                shift 2
                ;;
            -e|--error)
                log_type="error"
                shift
                ;;
            *)
                print_error "未知参数: $1"
                exit 1
                ;;
        esac
    done

    local log_file="$NGINX_LOG_DIR/${log_type}.log"

    if [[ ! -f "$log_file" ]]; then
        print_error "日志文件不存在: $log_file"
        return 1
    fi

    print_info "显示Nginx $log_type 日志..."

    if [[ "$follow" == "true" ]]; then
        tail -f "$log_file"
    else
        tail -n "$lines" "$log_file"
    fi
}

# 显示访问统计
show_stats() {
    print_platform "Nginx访问统计"

    if [[ "$(check_status)" != "running" ]]; then
        print_error "Nginx未运行"
        return 1
    fi

    # 使用awk分析访问日志
    if [[ -f "$NGINX_LOG_DIR/access.log" ]]; then
        echo "最近访问统计:"
        echo "================================"

        # 总请求数
        local total_requests=$(wc -l < "$NGINX_LOG_DIR/access.log")
        echo "总请求数: $total_requests"

        # 状态码统计
        echo ""
        echo "状态码分布:"
        awk '{print $9}' "$NGINX_LOG_DIR/access.log" | sort | uniq -c | sort -nr | head -10

        # Top IP
        echo ""
        echo "Top 10 访问IP:"
        awk '{print $1}' "$NGINX_LOG_DIR/access.log" | sort | uniq -c | sort -nr | head -10

        # Top 请求
        echo ""
        echo "Top 10 请求路径:"
        awk '{print $7}' "$NGINX_LOG_DIR/access.log" | sort | uniq -c | sort -nr | head -10

    else
        print_warning "访问日志文件不存在"
    fi
}

# 显示帮助信息
show_help() {
    print_banner
    echo -e "${CYAN}用法:${NC} $0 [命令] [选项]"
    echo ""
    echo -e "${CYAN}命令:${NC}"
    echo "  start              启动Nginx负载均衡器"
    echo "  stop               停止Nginx负载均衡器"
    echo "  restart            重启Nginx负载均衡器"
    echo "  reload             重新加载配置"
    echo "  status             显示运行状态"
    echo "  test               测试访问"
    echo "  logs               显示日志"
    echo "  stats              显示访问统计"
    echo "  config             测试配置文件"
    echo ""
    echo -e "${CYAN}选项:${NC}"
    echo "  -f, --follow       跟踪日志输出"
    echo "  -n, --lines NUM    显示最后N行日志"
    echo "  -e, --error        显示错误日志"
    echo "  -h, --help         显示帮助信息"
    echo ""
    echo -e "${CYAN}示例:${NC}"
    echo "  $0 start           # 启动Nginx"
    echo "  $0 logs -f         # 跟踪访问日志"
    echo "  $0 reload          # 重新加载配置"
    echo ""
    echo -e "${PURPLE}控制者: $PLATFORM_OWNER${NC}"
}

# 主函数
main() {
    # 检查参数
    if [[ $# -eq 0 ]]; then
        show_help
        exit 1
    fi

    # 显示平台标识
    print_banner

    # 检查依赖
    check_dependencies

    # 解析命令
    case "$1" in
        start)
            start_nginx
            ;;
        stop)
            stop_nginx
            ;;
        restart)
            restart_nginx
            ;;
        reload)
            reload_nginx
            ;;
        status)
            show_status
            ;;
        test)
            test_access
            ;;
        logs)
            shift
            show_logs "$@"
            ;;
        stats)
            show_stats
            ;;
        config)
            test_config
            ;;
        -h|--help)
            show_help
            ;;
        *)
            print_error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"