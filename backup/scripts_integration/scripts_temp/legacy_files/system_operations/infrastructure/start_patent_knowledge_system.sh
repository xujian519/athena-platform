#!/bin/bash
# 专利知识图谱系统启动脚本
# 作者：小娜
# 日期：2025-12-07

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

# 检查依赖
check_dependencies() {
    log "检查系统依赖..."

    # 检查Python
    if ! command -v python3 &> /dev/null; then
        error "Python3 未安装"
        exit 1
    fi

    # 检查Neo4j
    if ! command -v neo4j &> /dev/null; then
        warn "Neo4j 命令未在PATH中，请确保已安装"
    fi

    # 检查必要的Python包
    python3 -c "import fastapi, uvicorn, neo4j, requests" 2>/dev/null || {
        error "缺少必要的Python包，正在安装..."
        pip3 install fastapi uvicorn neo4j requests schedule
    }

    log "依赖检查完成"
}

# 启动Neo4j
start_neo4j() {
    log "启动Neo4j数据库..."

    if pgrep -f "neo4j" > /dev/null; then
        warn "Neo4j 已经在运行"
    else
        neo4j start
        log "Neo4j 启动成功"
    fi

    # 等待Neo4j就绪
    log "等待Neo4j服务就绪..."
    for i in {1..30}; do
        if curl -s http://localhost:7474 > /dev/null; then
            log "Neo4j 服务已就绪"
            break
        fi
        sleep 2
    done
}

# 创建必要的目录
create_directories() {
    log "创建必要的目录..."
    mkdir -p logs
    mkdir -p data/knowledge_graph/patents
    mkdir -p data/monitoring_reports
    log "目录创建完成"
}

# 启动知识图谱查询API
start_query_api() {
    log "启动知识图谱查询API..."
    cd /Users/xujian/Athena工作平台

    # 检查端口是否被占用
    if lsof -i:8088 > /dev/null; then
        warn "端口8088已被占用，尝试停止现有服务..."
        pkill -f "knowledge_graph_query_api" || true
        sleep 2
    fi

    # 后台启动API服务
    nohup python3 services/knowledge_graph_query_api.py > documentation/logs/query_api.log 2>&1 &
    echo $! > documentation/logs/query_api.pid

    log "知识图谱查询API已启动 (PID: $!)"
}

# 启动监控系统
start_monitor() {
    log "启动知识图谱监控系统..."
    cd /Users/xujian/Athena工作平台

    # 后台启动监控系统
    nohup python3 services/knowledge_graph_monitor.py > documentation/logs/monitor.log 2>&1 &
    echo $! > documentation/logs/monitor.pid

    log "监控系统已启动 (PID: $!)"
}

# 启动专利知识图谱构建
start_patent_builder() {
    log "启动专利知识图谱构建..."
    cd /Users/xujian/Athena工作平台

    # 前台运行构建过程
    python3 services/patent_knowledge_graph_builder.py
}

# 显示服务状态
show_status() {
    log "服务状态检查..."

    # Neo4j状态
    if pgrep -f "neo4j" > /dev/null; then
        log "✓ Neo4j: 运行中"
    else
        error "✗ Neo4j: 未运行"
    fi

    # API服务状态
    if lsof -i:8088 > /dev/null; then
        log "✓ 查询API: 运行中 (端口8088)"
    else
        error "✗ 查询API: 未运行"
    fi

    # 监控服务状态
    if [ -f documentation/logs/monitor.pid ]; then
        PID=$(cat documentation/logs/monitor.pid)
        if ps -p $PID > /dev/null; then
            log "✓ 监控系统: 运行中 (PID: $PID)"
        else
            error "✗ 监控系统: 未运行"
        fi
    else
        error "✗ 监控系统: 未启动"
    fi
}

# 停止所有服务
stop_services() {
    log "停止所有服务..."

    # 停止查询API
    if [ -f documentation/logs/query_api.pid ]; then
        PID=$(cat documentation/logs/query_api.pid)
        kill $PID 2>/dev/null || true
        rm -f documentation/logs/query_api.pid
        log "查询API已停止"
    fi

    # 停止监控系统
    if [ -f documentation/logs/monitor.pid ]; then
        PID=$(cat documentation/logs/monitor.pid)
        kill $PID 2>/dev/null || true
        rm -f documentation/logs/monitor.pid
        log "监控系统已停止"
    fi

    # 停止Neo4j（可选）
    read -p "是否停止Neo4j? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        neo4j stop
        log "Neo4j已停止"
    fi
}

# 主函数
main() {
    echo "========================================"
    echo "    专利知识图谱系统管理脚本"
    echo "========================================"
    echo

    case "${1:-start}" in
        start)
            log "启动专利知识图谱系统..."
            check_dependencies
            create_directories
            start_neo4j
            start_query_api
            start_monitor
            sleep 3
            show_status
            echo
            log "系统启动完成！"
            echo "查询API地址: http://localhost:8088"
            echo "监控日志: tail -f documentation/logs/monitor.log"
            echo
            read -p "是否立即开始构建专利知识图谱? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                start_patent_builder
            fi
            ;;

        stop)
            stop_services
            ;;

        status)
            show_status
            ;;

        restart)
            stop_services
            sleep 2
            main start
            ;;

        build)
            log "仅构建专利知识图谱..."
            start_patent_builder
            ;;

        *)
            echo "用法: $0 {start|stop|status|restart|build}"
            echo "  start  - 启动所有服务"
            echo "  stop   - 停止所有服务"
            echo "  status - 显示服务状态"
            echo "  restart- 重启所有服务"
            echo "  build  - 仅构建专利知识图谱"
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"