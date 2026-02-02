#!/bin/bash
# Athena工作平台健康检查脚本

echo "🔍 Athena工作平台服务状态检查"
echo "================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查函数
check_service() {
    local service_name=$1
    local port=$2
    local url=${3:-"http://localhost:$port/health"}

    if curl -s --max-time 3 "$url" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ $service_name (端口$port): 运行中${NC}"
        return 0
    else
        echo -e "${RED}❌ $service_name (端口$port): 未运行${NC}"
        return 1
    fi
}

# 检查基础服务
echo -e "${BLUE}📊 基础服务状态:${NC}"
check_service "PostgreSQL" "5432" "" || pg_isready -h localhost -p 5432 >/dev/null 2>&1 && echo -e "${GREEN}✅ PostgreSQL: 运行中${NC}"
check_service "Redis" "6379" "" || redis-cli ping >/dev/null 2>&1 && echo -e "${GREEN}✅ Redis: 运行中${NC}"
check_service "Ollama" "11434" "http://localhost:11434/api/tags"

echo ""
echo -e "${BLUE}🚀 核心服务状态:${NC}"

# 检查各个服务
check_service "AI模型服务" "8082"
check_service "YunPat Web" "8020" "http://localhost:8020/docs"
check_service "YunPat API" "8087" "http://localhost:8087/api/v2/health"
check_service "Athena搜索" "8088"

echo ""
echo -e "${BLUE}📋 运行中的进程:${NC}"
ps aux | grep -E "(python.*main\.py|yunpat|athena)" | grep -v grep | awk '{print $11 " " $12 " " $13 " (PID: " $2 ")"}' | head -n 10

echo ""
echo -e "${BLUE}📝 PID文件状态:${NC}"
ls -la .pids/ 2>/dev/null | grep -v "^total" || echo "没有PID文件"

echo ""
echo -e "${BLUE}💡 快速操作:${NC}"
echo "  查看日志: tail -f logs/<service>.log"
echo "  停止所有: kill \$(cat .pids/*.pid 2>/dev/null) 2>/dev/null || true"
echo "  重启平台: bash scripts/start_athena_platform_fixed.sh"