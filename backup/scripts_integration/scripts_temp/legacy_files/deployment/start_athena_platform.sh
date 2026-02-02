#!/bin/bash
# Athena工作平台启动脚本
# Athena Platform Startup Script

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

# 1. 专利搜索服务
echo -e "${YELLOW}启动专利搜索服务 (端口8080)...${NC}"
cd "$ATHENA_DIR/services/patent-search"
if [ -f "main.py" ]; then
    nohup python3 main.py > "$LOG_DIR/patent-search.log" 2>&1 &
    echo $! > "$PID_DIR/patent-search.pid"
    sleep 2
    echo -e "${GREEN}✅ 专利搜索服务已启动${NC}"
else
    echo -e "${YELLOW}⚠️ 专利搜索服务文件不存在${NC}"
fi

# 2. 向量服务
echo -e "${YELLOW}启动向量服务 (端口8082)...${NC}"
cd "$ATHENA_DIR/services/ai-models/pqai-integration"
if [ -f "main.py" ]; then
    nohup python3 main.py > "$LOG_DIR/vector-service.log" 2>&1 &
    echo $! > "$PID_DIR/vector-service.pid"
    sleep 2
    echo -e "${GREEN}✅ 向量服务已启动${NC}"
else
    echo -e "${YELLOW}⚠️ 向量服务文件不存在${NC}"
fi

# 3. 专利分析服务
echo -e "${YELLOW}启动专利分析服务 (端口8081)...${NC}"
if [ -d "$ATHENA_DIR/services/patent-analysis" ]; then
    cd "$ATHENA_DIR/services/patent-analysis"
    if [ -f "main.py" ]; then
        nohup python3 main.py > "$LOG_DIR/patent-analysis.log" 2>&1 &
        echo $! > "$PID_DIR/patent-analysis.pid"
        sleep 2
        echo -e "${GREEN}✅ 专利分析服务已启动${NC}"
    else
        echo -e "${YELLOW}⚠️ 专利分析服务文件不存在${NC}"
    fi
fi

# 返回工作目录
cd "$ATHENA_DIR"

# 启动后台任务
echo -e "${BLUE}📋 启动后台任务...${NC}"

# 数据库监控任务
nohup python3 scripts/database_monitor.py > "$LOG_DIR/database-monitor.log" 2>&1 &
echo $! > "$PID_DIR/database-monitor.pid"

# 缓存预热任务
nohup python3 scripts/cache_warmer.py > "$LOG_DIR/cache-warmer.log" 2>&1 &
echo $! > "$PID_DIR/cache-warmer.pid"

# 服务状态检查
echo -e "${BLUE}🔍 检查服务状态...${NC}"
sleep 3

# 检查端口占用
services=(
    "专利搜索服务:8080"
    "专利分析服务:8081"
    "向量服务:8082"
    "Ollama:11434"
    "PostgreSQL:5432"
    "Redis:6379"
)

for service in "${services[@]}"; do
    name=$(echo $service | cut -d: -f1)
    port=$(echo $service | cut -d: -f2)

    if lsof -i :$port >/dev/null 2>&1; then
        echo -e "${GREEN}✅ $name (端口$port) 运行中${NC}"
    else
        echo -e "${RED}❌ $name (端口$port) 未运行${NC}"
    fi
done

# 显示平台访问信息
echo -e "${BLUE}🌐 平台访问地址:${NC}"
echo "  - 专利搜索服务: http://localhost:8080"
echo "  - 专利分析服务: http://localhost:8081"
echo "  - 向量服务: http://localhost:8082"
echo "  - Ollama API: http://localhost:11434"

# 显示日志位置
echo -e "${BLUE}📁 日志文件位置:${NC}"
echo "  - 服务日志: $LOG_DIR/"
echo "  - PID文件: $PID_DIR/"

# 显示常用命令
echo -e "${BLUE}🛠️ 常用管理命令:${NC}"
echo "  - 停止服务: ./scripts/stop_athena_platform.sh"
echo "  - 重启服务: ./scripts/restart_athena_platform.sh"
echo "  - 查看日志: tail -f logs/patent-search.log"
echo "  - 服务状态: ./scripts/athena_consistency_checker.py"

echo -e "${GREEN}🎉 Athena工作平台启动完成！${NC}"