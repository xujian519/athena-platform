#!/bin/bash

# 启动优化版Athena工作平台
# 包含所有优化功能的完整部署

echo "🚀 启动优化版Athena工作平台"
echo "========================="

# 设置工作目录
cd "$(dirname "$0")/.."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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
    echo -e "\n${BLUE}[STEP]${NC} $1"
}

# 检查依赖
check_dependencies() {
    log_step "检查系统依赖"

    # 检查Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3未安装"
        exit 1
    fi

    # 检查Redis
    if ! command -v redis-server &> /dev/null; then
        log_warn "Redis未安装，将使用内存缓存"
        USE_MEMORY_CACHE=true
    else
        USE_MEMORY_CACHE=false
    fi

    # 检查Prometheus
    if ! command -v prometheus &> /dev/null; then
        log_warn "Prometheus未安装，监控功能将受限"
    fi

    # 安装Python依赖
    log_info "安装Python依赖..."
    pip3 install -q \
        fastapi uvicorn websockets \
        httpx aioredis \
        prometheus-client \
        cryptography \
        cachetools \
        orjson \
        msgpack \
        psutil \
        bcrypt \
        pyjwt \
        pydantic \
        numpy \
        aiosmtplib

    log_info "依赖检查完成"
}

# 生成SSL证书
generate_ssl_certificates() {
    log_step "生成SSL证书"

    if [ ! -f "certs/server.crt" ]; then
        bash scripts/generate_ssl_cert.sh
        if [ $? -eq 0 ]; then
            log_info "SSL证书生成成功"
        else
            log_error "SSL证书生成失败"
            exit 1
        fi
    else
        log_info "SSL证书已存在，跳过生成"
    fi
}

# 启动基础服务
start_base_services() {
    log_step "启动基础服务"

    # 启动Redis（如果可用）
    if [ "$USE_MEMORY_CACHE" = false ]; then
        log_info "启动Redis服务..."
        redis-server --daemonize yes --port 6379
        sleep 2
        if redis-cli ping > /dev/null 2>&1; then
            log_info "Redis启动成功"
        else
            log_warn "Redis启动失败，使用内存缓存"
            USE_MEMORY_CACHE=true
        fi
    fi

    # 创建日志目录
    mkdir -p logs/{services,monitoring,auth,ai,https}
}

# 启动优化后的服务
start_optimized_services() {
    log_step "启动优化服务"

    # 1. 统一身份服务（带认证）
    log_info "启动统一身份服务..."
    nohup python3 -c "
import asyncio
from core.auth.authentication import initialize_auth
from services.unified_identity.api_server import app
import uvicorn

async def main():
    await initialize_auth()
    config = uvicorn.Config(
        app=app,
        host='0.0.0.0',
        port=8090,
        log_level='info'
    )
    server = uvicorn.Server(config)
    await server.serve()

asyncio.run(main())
" > logs/services/unified-identity.log 2>&1 &
    echo $! > logs/services/unified-identity.pid

    # 2. 协作中枢（带缓存）
    log_info "启动协作中枢..."
    nohup python3 -c "
import asyncio
from core.cache.cache_manager import cache_manager
from services.intelligent_collaboration.api_server import app
import uvicorn

async def main():
    await cache_manager.initialize()
    config = uvicorn.Config(
        app=app,
        host='0.0.0.0',
        port=8091,
        log_level='info'
    )
    server = uvicorn.Server(config)
    await server.serve()

asyncio.run(main())
" > logs/services/intelligent-collaboration.log 2>&1 &
    echo $! > logs/services/intelligent-collaboration.pid

    # 3. WebSocket通信服务
    log_info "启动WebSocket通信服务..."
    nohup python3 services/communication-hub/websocket_server.py > logs/services/websocket-server.log 2>&1 &
    echo $! > logs/services/websocket-server.pid

    # 4. 增强版API网关（带连接池）
    log_info "启动增强版API网关..."
    nohup python3 -c "
import asyncio
from core.connection_pool.connection_manager import start_cleanup_task
from services.api_gateway.src.main_enhanced import app
import uvicorn

async def main():
    asyncio.create_task(start_cleanup_task())
    config = uvicorn.Config(
        app=app,
        host='0.0.0.0',
        port=8080,
        log_level='info'
    )
    server = uvicorn.Server(config)
    await server.serve()

asyncio.run(main())
" > logs/services/api-gateway-enhanced.log 2>&1 &
    echo $! > logs/services/api-gateway-enhanced.pid

    # 5. Prometheus监控服务
    log_info "启动Prometheus监控..."
    if command -v prometheus &> /dev/null; then
        prometheus \
            --config.file=monitoring/prometheus.yml \
            --storage.tsdb.path=monitoring/data \
            --web.console.libraries=monitoring/console_libraries \
            --web.console.templates=monitoring/consoles \
            --storage.tsdb.retention.time=30d \
            --web.enable-admin-api \
            > logs/monitoring/prometheus.log 2>&1 &
        echo $! > logs/monitoring/prometheus.pid
    else
        log_warn "Prometheus未安装，跳过启动"
    fi

    # 6. 告警系统服务
    log_info "启动告警系统..."
    nohup python3 -c "
import asyncio
from core.monitoring.alerting_system import initialize_alerting
from core.monitoring.prometheus_metrics import start_metrics_collection, start_prometheus_server
import uvicorn
from fastapi import FastAPI

app = FastAPI()

@app.get('/health')
async def health():
    return {'status': 'healthy'}

async def main():
    await initialize_alerting()
    asyncio.create_task(start_metrics_collection())
    start_prometheus_server(8001)
    config = uvicorn.Config(
        app=app,
        host='0.0.0.0',
        port=8093,
        log_level='info'
    )
    server = uvicorn.Server(config)
    await server.serve()

asyncio.run(main())
" > logs/monitoring/alerting.log 2>&1 &
    echo $! > logs/monitoring/alerting.pid

    # 7. HTTPS服务（可选）
    log_info "启动HTTPS服务..."
    if [ -f "certs/server.crt" ]; then
        nohup python3 -c "
import asyncio
from core.https.https_server import create_https_app, SecurityConfig
import uvicorn
import datetime

async def main():
    config = SecurityConfig()
    config.trusted_hosts = ['localhost', '127.0.0.1']
    app = create_https_app('Athena优化平台', config)

    http_config = uvicorn.Config(app, host='0.0.0.0', port=8000)
    https_config = uvicorn.Config(
        app=app,
        host='0.0.0.0',
        port=8443,
        ssl_config=uvicorn.SSLConfig(
            certfile='certs/server.crt',
            keyfile='certs/server.key'
        )
    )

    http_server = uvicorn.Server(http_config)
    https_server = uvicorn.Server(https_config)

    await asyncio.gather(
        http_server.serve(),
        https_server.serve()
    )

asyncio.run(main())
" > logs/https/https-server.log 2>&1 &
    echo $! > logs/https/https-server.pid
    else
        log_warn "SSL证书不存在，跳过HTTPS服务"
    fi

    # 8. 自定义AI服务
    log_info "启动自定义AI服务..."
    nohup python3 -c "
import asyncio
from core.ai.custom_ai_manager import custom_ai_manager
from core.ai.learning_system import start_learning_system
from fastapi import FastAPI
import uvicorn

app = FastAPI()

# 注册路由
from core.ai.custom_ai_manager import setup_custom_ai_routes
setup_custom_ai_routes(app)

@app.get('/health')
async def health():
    return {'status': 'healthy'}

async def main():
    await start_learning_system()
    config = uvicorn.Config(
        app=app,
        host='0.0.0.0',
        port=8094,
        log_level='info'
    )
    server = uvicorn.Server(config)
    await server.serve()

asyncio.run(main())
" > logs/ai/custom-ai.log 2>&1 &
    echo $! > logs/ai/custom-ai.pid
}

# 等待服务启动
wait_for_services() {
    log_step "等待服务启动"

    services=(
        "8080:API网关"
        "8090:统一身份服务"
        "8091:协作中枢"
        "8092:WebSocket服务"
        "8093:告警服务"
        "8094:自定义AI服务"
    )

    for service_info in "${services[@]}"; do
        port=${service_info%:*}
        name=${service_info#*:}

        echo -n "等待 $name (端口 $port)..."
        retries=0
        max_retries=30

        while [ $retries -lt $max_retries ]; do
            if curl -s http://localhost:$port/health >/dev/null 2>&1; then
                echo " ✅"
                break
            fi
            echo -n "."
            sleep 1
            ((retries++))
        done

        if [ $retries -eq $max_retries ]; then
            echo " ❌"
            log_warn "$name 启动超时"
        fi
    done
}

# 验证服务
verify_services() {
    log_step "验证服务状态"

    echo -e "\n${BLUE}服务状态检查${NC}"
    echo "================"

    # 检查各服务健康状态
    declare -A service_urls=(
        ["API网关"]="http://localhost:8080/health"
        ["统一身份服务"]="http://localhost:8090/api/v1/health"
        ["协作中枢"]="http://localhost:8091/api/v1/health"
        ["WebSocket服务"]="http://localhost:8092/health"
        ["告警服务"]="http://localhost:8093/health"
        ["自定义AI服务"]="http://localhost:8094/health"
        ["HTTPS服务"]="https://localhost:8443/health"
    )

    for service_name in "${!service_urls[@]}"; do
        url=${service_urls[$service_name]}
        if curl -s -k "$url" >/dev/null 2>&1; then
            echo -e "${GREEN}✅${NC} $service_name - 运行正常"
        else
            echo -e "${RED}❌${NC} $service_name - 无法访问"
        fi
    done
}

# 显示服务信息
show_service_info() {
    echo -e "\n${BLUE}优化功能展示${NC}"
    echo "=============="

    echo -e "\n📍 服务端点:"
    echo "  • HTTP服务: http://localhost:8000"
    echo "  • HTTPS服务: https://localhost:8443"
    echo "  • API网关: http://localhost:8080"
    echo -e "\n🤖 AI服务:"
    echo "  • 统一身份: http://localhost:8090"
    echo "  • 协作中枢: http://localhost:8091"
    echo "  • 自定义AI: http://localhost:8094"
    echo -e "\n📊 监控服务:"
    echo "  • Prometheus: http://localhost:9090"
    echo "  • 告警服务: http://localhost:8093"
    echo "  • 指标端点: http://localhost:8001/metrics"
    echo -e "\n🔌 WebSocket:"
    echo "  • 通信服务: ws://localhost:8092"
    echo -e "\n📚 API文档:"
    echo "  • API网关: http://localhost:8080/docs"
    echo "  • 身份服务: http://localhost:8090/docs"
    echo "  • 协作中枢: http://localhost:8091/docs"
    echo -  " • 自定义AI: http://localhost:8094/docs"
    echo -e "\n🔒 认证信息:"
    echo "  • 管理员: admin / admin123"
    echo "  • Athena: athena / athena123"
    echo "  • 小诺: xiaonuo / xiaonuo123"

    echo -e "\n${BLUE}优化特性${NC}"
    echo "============"
    echo "✅ 连接池管理 - 提升并发性能"
    echo "✅ 响应缓存 - 加速数据访问"
    echo "✅ 消息序列化优化 - 降低传输开销"
    echo "✅ Prometheus监控 - 全面的性能监控"
    echo "✅ 智能告警 - 及时发现问题"
    echo "✅ API认证 - 保障系统安全"
    echo "✅ HTTPS支持 - 加密数据传输"
    echo "✅ 自定义AI角色 - 灵活扩展能力"
    echo "✅ 学习系统 - 持续优化性能"
}

# 主函数
main() {
    echo -e "${BLUE}Athena工作平台优化版启动脚本${NC}"
    echo "==============================="
    echo

    # 执行启动流程
    check_dependencies
    echo
    generate_ssl_certificates
    echo
    start_base_services
    echo
    start_optimized_services
    echo
    wait_for_services
    echo
    verify_services
    echo
    show_service_info

    echo -e "\n${GREEN}🎉 优化版Athena平台启动完成！${NC}"
    echo -e "\n${YELLOW}提示：${NC}"
    echo "1. 使用 'bash scripts/stop_optimized_platform.sh' 停止所有服务"
    echo "2. 查看 'logs/' 目录下的日志文件"
    echo "3. 访问 http://localhost:8080/docs 测试API"
    echo "4. 访问 https://localhost:8443/docs 使用HTTPS"
    echo "5. 访问 http://localhost:9090 查看Prometheus监控"
}

# 错误处理
set -e
trap 'log_error "脚本执行失败，正在清理..."; cleanup; exit 1' ERR

# 清理函数
cleanup() {
    log_info "清理临时资源..."
    # 这里可以添加清理逻辑
}

# 执行主函数
main "$@"