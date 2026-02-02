#!/bin/bash
# Athena工作平台完整服务启动脚本

set -e

echo "🚀 启动Athena工作平台完整服务..."
echo "================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 工作目录
ATHENA_DIR="/Users/xujian/Athena工作平台"
cd "$ATHENA_DIR"

# 日志目录
LOG_DIR="$ATHENA_DIR/logs"
mkdir -p "$LOG_DIR"

# PID文件目录
PID_DIR="$ATHENA_DIR/.pids"
mkdir -p "$PID_DIR"

# 清理之前的PID
rm -f "$PID_DIR"/*.pid

# 停止已存在的服务
echo -e "${YELLOW}🔄 停止已存在的服务...${NC}"
pkill -f "python.*main.py" 2>/dev/null || true
pkill -f "yunpat" 2>/dev/null || true
pkill -f "athena" 2>/dev/null || true
sleep 2

# 1. AI模型服务 (端口8082)
echo -e "${YELLOW}🤖 启动AI模型服务 (端口8082)...${NC}"
cd "$ATHENA_DIR/services/ai-models"
PYTHONPATH=$ATHENA_DIR/services/ai-models python3 main.py > "$LOG_DIR/ai-models.log" 2>&1 &
AI_PID=$!
echo $AI_PID > "$PID_DIR/ai-models.pid"
sleep 2

# 2. Athena迭代搜索服务 (端口8088)
echo -e "${YELLOW}🔍 启动Athena迭代搜索服务 (端口8088)...${NC}"
cd "$ATHENA_DIR/services/athena_iterative_search"
# 使用更安全的PYTHONPATH
export PYTHONPATH=$ATHENA_DIR/services/athena_iterative_search
/usr/bin/python3 -c "import sys; sys.path.insert(0, '.'); import main; main.main()" > "$LOG_DIR/athena-search.log" 2>&1 &
ATHENA_PID=$!
echo $ATHENA_PID > "$PID_DIR/athena-search.pid"
sleep 2

# 3. YunPat Agent服务 (端口8087)
echo -e "${YELLOW}💖 启动YunPat Agent服务 (端口8087)...${NC}"
cd "$ATHENA_DIR/services/yunpat-agent"
if [ -f "app/main.py" ]; then
    # 直接启动API服务
    python3 app/main.py > "$LOG_DIR/yunpat-agent.log" 2>&1 &
    YUNPAT_PID=$!
    echo $YUNPAT_PID > "$PID_DIR/yunpat-agent.pid"
    sleep 2
fi

# 4. 检查服务状态
echo -e "${BLUE}📊 检查服务状态...${NC}"
sleep 3

# 检查函数
check_service() {
    local service_name=$1
    local port=$2
    local pid=$3

    if ps -p $pid > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $service_name: 进程运行中 (PID: $pid)${NC}"
    else
        echo -e "${RED}❌ $service_name: 进程未运行${NC}"
        return 1
    fi

    if curl -s --max-time 2 "http://localhost:$port/" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ $service_name: 端口$port响应正常${NC}"
    else
        echo -e "${YELLOW}⚠️ $service_name: 端口$port未响应${NC}"
    fi
}

# 检查各服务
check_service "AI模型服务" 8082 $AI_PID
check_service "Athena搜索" 8088 $ATHENA_PID
check_service "YunPat Agent" 8087 $YUNPAT_PID

echo ""
echo -e "${BLUE}📋 服务概览:${NC}"
echo "  - AI模型服务:    http://localhost:8082/docs"
echo "  - Athena搜索:     http://localhost:8088"
echo "  - YunPat Web:     http://localhost:8020"
echo "  - YunPat API:     http://localhost:8087"
echo ""
echo -e "${BLUE}📝 日志位置:${NC}"
echo "  - AI模型服务:    logs/ai-models.log"
echo "  - Athena搜索:     logs/athena-search.log"
echo "  - YunPat Agent:   logs/yunpat-agent.log"
echo ""
echo -e "${GREEN}🎉 启动完成！${NC}"