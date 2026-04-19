#!/bin/bash
# Athena Gateway 重启脚本

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${YELLOW}🔄 重启 Athena Gateway...${NC}"
echo ""

# 停止
"${SCRIPT_DIR}/stop.sh"

# 等待一秒
sleep 1

# 启动
"${SCRIPT_DIR}/start.sh"
