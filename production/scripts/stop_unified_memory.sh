#!/bin/bash
# Athena统一记忆系统 - 停止服务脚本
# Unified Agent Memory System - Stop Service

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🛑 Athena统一记忆系统 - 停止服务${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# 查找服务进程
PIDS=$(pgrep -f "start_unified_memory_service.py" || true)

if [ -z "$PIDS" ]; then
    echo -e "${YELLOW}⚠️  未找到运行中的统一记忆系统服务${NC}"
    exit 0
fi

echo -e "${GREEN}📋 找到服务进程:${NC}"
echo "$PIDS"
echo ""

# 停止服务
echo -e "${YELLOW}🛑 正在停止服务...${NC}"
for PID in $PIDS; do
    kill "$PID" 2>/dev/null || echo -e "${YELLOW}⚠️  进程 $PID 已停止${NC}"
done

# 等待进程结束
echo -e "${GREEN}⏳ 等待服务优雅关闭...${NC}"
sleep 3

# 检查是否成功停止
REMAINING=$(pgrep -f "start_unified_memory_service.py" || true)
if [ -n "$REMAINING" ]; then
    echo -e "${YELLOW}⚠️  服务仍在运行，强制停止...${NC}"
    pkill -9 -f "start_unified_memory_service.py" || true
    sleep 1
fi

# 最终确认
FINAL_CHECK=$(pgrep -f "start_unified_memory_service.py" || true)
if [ -z "$FINAL_CHECK" ]; then
    echo -e "${GREEN}✅ 服务已成功停止${NC}"
else
    echo -e "${RED}❌ 服务停止失败，请手动检查${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 统一记忆系统服务已停止${NC}"
