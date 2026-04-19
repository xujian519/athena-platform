#!/bin/bash
# 小娜生产环境启动脚本
# Xiaona Production Service Startup Script
#
# 功能：启动小娜FastAPI服务（非交互式）
# 端口：8001
# 日期：2026-01-21

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="/Users/xujian/Athena工作平台"
cd "$PROJECT_ROOT/production/services"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                              ║${NC}"
echo -e "${BLUE}║  🌟 小娜 - 专利法律AI助手 🌟                                  ║${NC}"
echo -e "${BLUE}║  Production API Service                                      ║${NC}"
echo -e "${BLUE}║                                                              ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 未找到Python3${NC}"
    exit 1
fi

# 检查必要文件
if [ ! -f "xiaona_api.py" ]; then
    echo -e "${RED}❌ 未找到 xiaona_api.py${NC}"
    exit 1
fi

# 检查端口占用
if lsof -Pi :8001 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  端口 8001 已被占用${NC}"
    echo -e "${YELLOW}正在尝试停止现有服务...${NC}"

    # 尝试找到并停止进程
    PID=$(lsof -ti :8001)
    if [ -n "$PID" ]; then
        kill $PID 2>/dev/null || true
        sleep 2
    fi

    # 再次检查
    if lsof -Pi :8001 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${RED}❌ 无法释放端口 8001${NC}"
        exit 1
    fi
fi

# 创建日志目录
LOG_DIR="$PROJECT_ROOT/data/logs"
mkdir -p "$LOG_DIR"

# 检查依赖
echo -e "${GREEN}✓ 检查依赖...${NC}"
python3 -c "import fastapi, uvicorn" 2>/dev/null || {
    echo -e "${RED}❌ 缺少必要依赖${NC}"
    echo -e "${YELLOW}正在安装依赖...${NC}"
    pip3 install fastapi uvicorn pydantic -q
}

# 启动服务（后台运行）
echo -e "${GREEN}🚀 启动小娜API服务...${NC}"
echo ""

# 使用nohup后台启动
nohup python3 xiaona_api.py > "$LOG_DIR/xiaona_api.log" 2>&1 &
API_PID=$!

# 保存PID
echo $API_PID > "$PROJECT_ROOT/data/pids/xiaona.pid"

# 等待服务启动
echo -e "${YELLOW}等待服务启动...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 小娜API服务启动成功！${NC}"
        echo ""
        echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}服务信息:${NC}"
        echo -e "  📍 地址: http://localhost:8001"
        echo -e "  📚 文档: http://localhost:8001/docs"
        echo -e "  💚 健康: http://localhost:8001/health"
        echo -e "  📝 日志: $LOG_DIR/xiaona_api.log"
        echo -e "  🔢 PID:  $API_PID"
        echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
        echo ""

        # 显示服务状态
        echo -e "${GREEN}服务状态:${NC}"
        curl -s http://localhost:8001/health | python3 -m json.tool 2>/dev/null || echo "服务正在初始化..."

        echo ""
        echo -e "${GREEN}✅ 小娜已就绪！${NC}"
        exit 0
    fi
    sleep 1
done

# 如果超时
echo -e "${RED}❌ 服务启动超时${NC}"
echo -e "${YELLOW}请查看日志: $LOG_DIR/xiaona_api.log${NC}"
exit 1
