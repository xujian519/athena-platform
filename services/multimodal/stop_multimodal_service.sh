#!/bin/bash

# 多模态文件系统API服务停止脚本
# Multimodal File System API Service Stop Script

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置信息
PID_FILE="/Users/xujian/Athena工作平台/logs/multimodal_service.pid"
SERVICE_NAME="multimodal-api"

echo -e "${BLUE}🛑 多模态文件系统服务停止器${NC}"
echo -e "${BLUE}================================${NC}"

# 检查PID文件
if [ ! -f "$PID_FILE" ]; then
    echo -e "${YELLOW}⚠️  未找到PID文件，服务可能未运行${NC}"
    exit 0
fi

# 读取PID
PID=$(cat "$PID_FILE")

# 检查进程是否存在
if ! ps -p "$PID" > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  进程 $PID 不存在，清理PID文件${NC}"
    rm -f "$PID_FILE"
    exit 0
fi

# 尝试优雅停止
echo -e "${BLUE}🔄 正在停止服务 (PID: $PID)...${NC}"
kill "$PID"

# 等待进程结束
for i in {1..10}; do
    if ! ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 服务已优雅停止${NC}"
        rm -f "$PID_FILE"
        exit 0
    fi
    sleep 1
    echo -n "."
done

# 强制停止
echo -e "${YELLOW}⚠️  强制停止服务...${NC}"
kill -9 "$PID"

# 再次检查
if ! ps -p "$PID" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 服务已强制停止${NC}"
    rm -f "$PID_FILE"
else
    echo -e "${RED}❌ 无法停止服务，请手动检查进程 $PID${NC}"
    exit 1
fi