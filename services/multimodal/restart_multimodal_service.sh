#!/bin/bash

# 多模态文件系统API服务重启脚本
# Multimodal File System API Service Restart Script

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔄 多模态文件系统服务重启器${NC}"
echo -e "${BLUE}================================${NC}"

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 停止服务
echo -e "${BLUE}🛑 停止现有服务...${NC}"
"$SCRIPT_DIR/stop_multimodal_service.sh"

# 等待一秒
sleep 1

# 启动服务
echo -e "${BLUE}🚀 启动新服务...${NC}"
"$SCRIPT_DIR/start_multimodal_service.sh"