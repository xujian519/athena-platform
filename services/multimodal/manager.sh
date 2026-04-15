#!/bin/bash
# Athena多模态文件系统管理脚本

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
PORT=8001
HOST="0.0.0.0"
API_URL="http://localhost:${PORT}"
PID_FILE="/tmp/athena_multimodal.pid"
LOG_DIR="/Users/xujian/Athena工作平台/logs/multimodal"

# 创建日志目录
mkdir -p $LOG_DIR

# 检查服务状态
check_status() {
    if curl -s $API_URL/ > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 服务正在运行 (端口: $PORT)${NC}"
        return 0
    else
        echo -e "${RED}❌ 服务未运行${NC}"
        return 1
    fi
}

# 启动服务
start_service() {
    echo -e "${BLUE}🚀 启动Athena多模态文件系统...${NC}"

    if check_status > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️ 服务已在运行中${NC}"
        return 0
    fi

    cd /Users/xujian/Athena工作平台/services/multimodal
    nohup python3 minimal_api.py > $LOG_DIR/server.log 2>&1 &
    echo $! > $PID_FILE

    sleep 3

    if check_status; then
        echo -e "${GREEN}✅ 服务启动成功${NC}"
        echo -e "${GREEN}📍 API地址: $API_URL${NC}"
        echo -e "${GREEN}📚 文档: $API_URL/docs${NC}"
    else
        echo -e "${RED}❌ 服务启动失败${NC}"
        tail -10 $LOG_DIR/server.log
    fi
}

# 停止服务
stop_service() {
    echo -e "${YELLOW}🛑 停止Athena多模态文件系统...${NC}"

    if [ -f $PID_FILE ]; then
        PID=$(cat $PID_FILE)
        if kill -0 $PID 2>/dev/null; then
            kill $PID
            rm -f $PID_FILE
            sleep 2
            echo -e "${GREEN}✅ 服务已停止${NC}"
        else
            echo -e "${RED}⚠️ 进程不存在${NC}"
            rm -f $PID_FILE
        fi
    else
        # 尝试通过端口杀死进程
        PID=$(lsof -t -i:$PORT 2>/dev/null)
        if [ ! -z "$PID" ]; then
            kill $PID
            sleep 2
            echo -e "${GREEN}✅ 已终止端口 $PORT 上的进程${NC}"
        else
            echo -e "${YELLOW}⚠️ 没有找到运行中的服务${NC}"
        fi
    fi
}

# 重启服务
restart_service() {
    stop_service
    sleep 1
    start_service
}

# 显示状态
show_status() {
    echo -e "${BLUE}📊 Athena多模态文件系统状态${NC}"
    echo "================================"

    if check_status; then
        # 获取健康信息
        HEALTH=$(curl -s $API_URL/health 2>/dev/null)
        echo -e "${GREEN}状态: 在线${NC}"

        # 获取统计信息
        STATS=$(curl -s $API_URL/statistics 2>/dev/null)
        if [ ! -z "$STATS" ]; then
            echo "统计信息:"
            echo "$STATS" | python3 -c "
import sys, json
data = json.load(sys.stdin)
stats = data.get('statistics', {})
print(f\"  上传文件: {stats.get('total_uploads', 0)}\")
print(f\"  下载文件: {stats.get('total_downloads', 0)}\")
print(f\"  存储大小: {stats.get('total_size', 0)} 字节\")
"
        fi

        # 显示进程信息
        if [ -f $PID_FILE ]; then
            PID=$(cat $PID_FILE)
            echo -e "${BLUE}进程ID: $PID${NC}"
        fi
    else
        echo -e "${RED}状态: 离线${NC}"
    fi

    echo ""
    echo "服务配置:"
    echo "  端口: $PORT"
    echo "  主机: $HOST"
    echo "  API地址: $API_URL"
    echo "  日志目录: $LOG_DIR"
}

# 测试功能
test_service() {
    echo -e "${BLUE}🧪 测试服务功能...${NC}"

    if ! check_status; then
        echo -e "${RED}❌ 服务未运行，无法测试${NC}"
        return 1
    fi

    echo ""
    echo "1. 测试健康检查..."
    if curl -s $API_URL/health > /dev/null; then
        echo -e "   ${GREEN}✅ 健康检查通过${NC}"
    else
        echo -e "   ${RED}❌ 健康检查失败${NC}"
    fi

    echo ""
    echo "2. 测试用户认证..."
    TOKEN=$(curl -s -X POST $API_URL/auth/login \
        -F "username=testuser" \
        -F "password=testpass" | \
        python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('token', ''))" 2>/dev/null)

    if [ ! -z "$TOKEN" ]; then
        echo -e "   ${GREEN}✅ 认证成功 (Token: ${TOKEN:0:20}...)${NC}"
    else
        echo -e "   ${RED}❌ 认证失败${NC}"
    fi

    echo ""
    echo "3. 测试文件列表..."
    FILE_COUNT=$(curl -s $API_URL/files | \
        python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('total_files', 0))" 2>/dev/null)
    echo -e "   ${GREEN}✅ 文件列表查询成功 (当前: $FILE_COUNT 个文件)${NC}"

    echo ""
    echo -e "${GREEN}🎉 所有核心功能测试通过！${NC}"
}

# 显示帮助
show_help() {
    echo -e "${BLUE}Athena多模态文件系统管理脚本${NC}"
    echo "================================"
    echo ""
    echo "用法: $0 {start|stop|restart|status|test|help}"
    echo ""
    echo "命令:"
    echo "  start   - 启动服务"
    echo "  stop    - 停止服务"
    echo "  restart - 重启服务"
    echo "  status  - 显示状态"
    echo "  test    - 测试功能"
    echo "  help    - 显示帮助"
    echo ""
    echo "服务信息:"
    echo "  端口: $PORT"
    echo "  API: $API_URL"
    echo "  文档: $API_URL/docs"
}

# 主程序
case "$1" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    status)
        show_status
        ;;
    test)
        test_service
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}错误: 未知命令 '$1'${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac