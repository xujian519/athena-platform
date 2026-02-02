#!/bin/bash
# Athena工作平台启动脚本（修复版）
# Athena Platform Startup Script (Fixed Version)

set -e

echo "🚀 启动Athena工作平台..."
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

# 检查必要服务
echo -e "${BLUE}🔍 检查基础服务状态...${NC}"

# 检查PostgreSQL
if ! pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
    echo -e "${RED}❌ PostgreSQL未运行${NC}"
    echo "请先启动PostgreSQL: brew services start postgresql"
    exit 1
else
    echo -e "${GREEN}✅ PostgreSQL运行中${NC}"
fi

# 检查Redis
if ! redis-cli ping >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️ Redis未运行，正在启动...${NC}"
    brew services start redis || {
        echo -e "${RED}❌ Redis启动失败${NC}"
        exit 1
    }
    echo -e "${GREEN}✅ Redis已启动${NC}"
else
    echo -e "${GREEN}✅ Redis运行中${NC}"
fi

# 检查Ollama
if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️ Ollama未运行，正在启动...${NC}"
    ollama serve &
    sleep 3
    if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        echo -e "${RED}❌ Ollama启动失败${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Ollama已启动${NC}"
else
    echo -e "${GREEN}✅ Ollama运行中${NC}"
fi

# 启动核心服务
echo -e "${BLUE}🚀 启动核心服务...${NC}"

# 1. AI模型服务 (端口8082)
echo -e "${YELLOW}启动AI模型服务 (端口8082)...${NC}"
cd "$ATHENA_DIR/services/ai-models"
if [ -f "main.py" ]; then
    nohup python3 main.py > "$LOG_DIR/ai-models.log" 2>&1 &
    echo $! > "$PID_DIR/ai-models.pid"
    sleep 3
    echo -e "${GREEN}✅ AI模型服务已启动${NC}"
else
    echo -e "${RED}❌ AI模型服务文件不存在${NC}"
fi

# 2. YunPat Agent (端口8087)
echo -e "${YELLOW}启动YunPat Agent服务 (端口8087)...${NC}"
cd "$ATHENA_DIR/services/yunpat-agent"
if [ -f "start.sh" ]; then
    nohup bash start.sh > "$LOG_DIR/yunpat-agent.log" 2>&1 &
    echo $! > "$PID_DIR/yunpat-agent.pid"
    sleep 3
    echo -e "${GREEN}✅ YunPat Agent服务已启动${NC}"
else
    echo -e "${YELLOW}⚠️ YunPat Agent启动脚本不存在${NC}"
fi

# 3. Athena迭代搜索服务 (端口8088)
echo -e "${YELLOW}启动Athena迭代搜索服务 (端口8088)...${NC}"
cd "$ATHENA_DIR/services/athena_iterative_search"
if [ -f "main.py" ]; then
    nohup python3 main.py > "$LOG_DIR/athena-search.log" 2>&1 &
    echo $! > "$PID_DIR/athena-search.pid"
    sleep 3
    echo -e "${GREEN}✅ Athena迭代搜索服务已启动${NC}"
else
    echo -e "${YELLOW}⚠️ Athena迭代搜索服务文件不存在${NC}"
fi

# 4. 平台集成服务 (端口8089)
echo -e "${YELLOW}启动平台集成服务 (端口8089)...${NC}"
cd "$ATHENA_DIR/services/platform-integration-service"
if [ -f "main.py" ]; then
    nohup python3 main.py > "$LOG_DIR/platform-integration.log" 2>&1 &
    echo $! > "$PID_DIR/platform-integration.pid"
    sleep 3
    echo -e "${GREEN}✅ 平台集成服务已启动${NC}"
else
    echo -e "${YELLOW}⚠️ 平台集成服务文件不存在${NC}"
fi

# 5. 启动Web界面（如果存在）
if [ -f "$ATHENA_DIR/start.sh" ]; then
    echo -e "${YELLOW}启动Web界面...${NC}"
    cd "$ATHENA_DIR"
    nohup bash start.sh > "$LOG_DIR/web-interface.log" 2>&1 &
    echo $! > "$PID_DIR/web-interface.pid"
    sleep 3
    echo -e "${GREEN}✅ Web界面已启动${NC}"
fi

echo -e "${BLUE}================================${NC}"
echo -e "${GREEN}🎉 Athena工作平台启动完成！${NC}"
echo ""
echo "📊 服务状态："
echo "  - AI模型服务:    http://localhost:8082"
echo "  - YunPat Agent:   http://localhost:8087"
echo "  - Athena搜索:     http://localhost:8088"
echo "  - 平台集成:       http://localhost:8089"
echo ""
echo "📋 管理命令："
echo "  查看日志: tail -f logs/<service>.log"
echo "  停止服务: bash scripts/stop_athena_platform.sh"
echo "  重启服务: bash scripts/restart_athena_platform.sh"
echo ""
echo -e "${GREEN}祝您使用愉快！ 💖${NC}"