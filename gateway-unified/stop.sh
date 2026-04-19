#!/bin/bash
# Athena Gateway 停止脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="${SCRIPT_DIR}/gateway.pid"

# 检查PID文件
if [ ! -f "${PID_FILE}" ]; then
    echo -e "${YELLOW}网关未运行（无PID文件）${NC}"
    exit 0
fi

# 读取PID
PID=$(cat "${PID_FILE}")

# 检查进程是否存在
if ! ps -p "${PID}" > /dev/null 2>&1; then
    echo -e "${YELLOW}进程 ${PID} 不存在，清理PID文件${NC}"
    rm -f "${PID_FILE}"
    exit 0
fi

# 优雅关闭
echo -e "${YELLOW}🛑 正在停止 Athena Gateway (PID: ${PID})...${NC}"

# 发送TERM信号
kill -TERM "${PID}" 2>/dev/null || true

# 等待进程退出（最多30秒）
TIMEOUT=30
ELAPSED=0
while ps -p "${PID}" > /dev/null 2>&1 && [ ${ELAPSED} -lt ${TIMEOUT} ]; do
    sleep 1
    ELAPSED=$((ELAPSED + 1))
    echo -n "."
done
echo ""

# 检查是否已停止
if ps -p "${PID}" > /dev/null 2>&1; then
    echo -e "${RED}⚠️  优雅关闭超时，强制终止...${NC}"
    kill -9 "${PID}" 2>/dev/null || true
    sleep 1
fi

# 验证并清理
if ps -p "${PID}" > /dev/null 2>&1; then
    echo -e "${RED}❌ 停止失败${NC}"
    exit 1
else
    echo -e "${GREEN}✅ Athena Gateway 已停止${NC}"
    rm -f "${PID_FILE}"
fi
