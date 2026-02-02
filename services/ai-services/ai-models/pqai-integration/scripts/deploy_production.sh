#!/bin/bash
# PQAI专利检索服务生产环境部署脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 服务配置
PQAI_SERVICE_PORT=8030
PQAI_SERVICE_NAME="pqai-patent-search"
PQAI_WORK_DIR="/Users/xujian/Athena工作平台/services/ai-models/pqai-integration"

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

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 检查服务是否运行
check_service_running() {
    local port=$1
    if lsof -i :$port >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# 停止指定端口的服务
stop_service_on_port() {
    local port=$1
    log_step "检查端口 $port 上运行的服务..."

    if check_service_running $port; then
        log_warn "端口 $port 已被占用，正在停止相关服务..."
        local pid=$(lsof -ti:$port)
        kill -TERM $pid

        # 等待服务停止
        local count=0
        while check_service_running $port && [ $count -lt 10 ]; do
            sleep 1
            count=$((count + 1))
        done

        # 如果服务仍在运行，强制杀死
        if check_service_running $port; then
            log_warn "强制停止端口 $port 上的服务..."
            kill -KILL $pid
            sleep 2
        fi

        if ! check_service_running $port; then
            log_info "成功停止端口 $port 上的服务"
        else
            log_error "无法停止端口 $port 上的服务"
            exit 1
        fi
    else
        log_info "端口 $port 当前未被占用"
    fi
}

# 安装依赖
install_dependencies() {
    log_step "安装PQAI服务依赖..."
    cd $PQAI_WORK_DIR

    # 检查requirements.txt是否存在
    if [ -f "requirements.txt" ]; then
        log_info "发现requirements.txt，正在安装依赖..."
        pip3 install -r requirements.txt
    else
        log_warn "requirements.txt不存在，跳过依赖安装"
    fi
}

# 启动PQAI服务
start_pqai_service() {
    log_step "启动PQAI专利检索服务..."
    cd $PQAI_WORK_DIR

    # 检查API服务文件是否存在
    if [ ! -f "api/pqai_service.py" ]; then
        log_error "PQAI API服务文件不存在: api/pqai_service.py"
        exit 1
    fi

    # 创建日志目录
    mkdir -p logs

    # 启动服务
    log_info "在后台启动PQAI服务..."
    nohup python3 api/pqai_service.py > documentation/logs/pqai_service.log 2>&1 &
    local service_pid=$!

    # 保存PID
    echo $service_pid > documentation/logs/pqai_service.pid

    # 等待服务启动
    log_info "等待服务启动..."
    sleep 5

    # 验证服务是否启动成功
    if check_service_running $PQAI_SERVICE_PORT; then
        log_info "✅ PQAI服务启动成功！"
        log_info "服务地址: http://localhost:$PQAI_SERVICE_PORT"
        log_info "服务PID: $service_pid"
        log_info "日志文件: $PQAI_WORK_DIR/documentation/logs/pqai_service.log"
    else
        log_error "❌ PQAI服务启动失败"
        log_error "请检查日志文件: $PQAI_WORK_DIR/documentation/logs/pqai_service.log"
        exit 1
    fi
}

# 验证服务健康状态
verify_service_health() {
    log_step "验证服务健康状态..."

    # 等待服务完全启动
    sleep 3

    # 检查健康状态
    if curl -s http://localhost:$PQAI_SERVICE_PORT/health >/dev/null; then
        log_info "✅ 服务健康检查通过"

        # 显示服务状态
        echo ""
        log_info "🎯 PQAI专利检索服务状态信息:"
        curl -s http://localhost:$PQAI_SERVICE_PORT/health | python3 -m json.tool
        echo ""

        log_info "📊 服务详细状态:"
        curl -s http://localhost:$PQAI_SERVICE_PORT/status | python3 -m json.tool || log_warn "状态接口调用失败"

    else
        log_error "❌ 服务健康检查失败"
        exit 1
    fi
}

# 配置API网关路由
configure_api_gateway() {
    log_step "准备配置API网关路由..."
    log_info "PQAI服务已启动，可通过以下路径访问:"
    echo "  - 专利检索: http://localhost:$PQAI_SERVICE_PORT/search"
    echo "  - 相似专利: http://localhost:$PQAI_SERVICE_PORT/search/similar/{patent_id}"
    echo "  - 服务健康: http://localhost:$PQAI_SERVICE_PORT/health"
    echo "  - 服务状态: http://localhost:$PQAI_SERVICE_PORT/status"
    echo ""
    log_info "📝 下一步: 将这些路由配置到Athena API网关 (端口8000)"
}

# 显示部署摘要
show_deployment_summary() {
    echo ""
    log_info "🎉 PQAI专利检索服务部署完成！"
    echo ""
    echo "📋 服务摘要:"
    echo "  服务名称: $PQAI_SERVICE_NAME"
    echo "  服务端口: $PQAI_SERVICE_PORT"
    echo "  工作目录: $PQAI_WORK_DIR"
    echo "  日志文件: $PQAI_WORK_DIR/documentation/logs/pqai_service.log"
    echo "  PID文件: $PQAI_WORK_DIR/documentation/logs/pqai_service.pid"
    echo ""
    echo "🔗 API端点:"
    echo "  健康检查: GET  http://localhost:$PQAI_SERVICE_PORT/health"
    echo "  服务状态: GET  http://localhost:$PQAI_SERVICE_PORT/status"
    echo "  专利检索: POST http://localhost:$PQAI_SERVICE_PORT/search"
    echo "  相似专利: GET  http://localhost:$PQAI_SERVICE_PORT/search/similar/{patent_id}"
    echo "  构建索引: POST http://localhost:$PQAI_SERVICE_PORT/index/build"
    echo "  分析统计: GET  http://localhost:$PQAI_SERVICE_PORT/analytics/statistics"
    echo ""
    echo "📖 使用说明:"
    echo "  1. 首先调用 /index/build 构建专利索引"
    echo "  2. 然后使用 /search 进行专利检索"
    echo "  3. 查看日志: tail -f $PQAI_WORK_DIR/documentation/logs/pqai_service.log"
    echo ""
    echo "⚠️  注意事项:"
    echo "  - 服务已集成到Athena平台架构中"
    echo "  - 需要配置API网关路由以实现统一访问"
    echo "  - 建议配置负载均衡和监控告警"
}

# 主函数
main() {
    echo "🚀 开始部署PQAI专利检索服务到生产环境..."
    echo ""

    # 步骤1: 停止现有服务
    stop_service_on_port $PQAI_SERVICE_PORT

    # 步骤2: 安装依赖
    install_dependencies

    # 步骤3: 启动PQAI服务
    start_pqai_service

    # 步骤4: 验证服务健康状态
    verify_service_health

    # 步骤5: 配置API网关
    configure_api_gateway

    # 步骤6: 显示摘要
    show_deployment_summary

    echo ""
    log_info "✅ PQAI专利检索服务生产部署完成！"
}

# 错误处理
trap 'log_error "部署过程中发生错误，请检查日志"; exit 1' ERR

# 执行主函数
main "$@"