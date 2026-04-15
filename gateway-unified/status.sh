#!/bin/bash
# Athena Gateway 状态检查脚本

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="${SCRIPT_DIR}/gateway.pid"
LOG_FILE="${SCRIPT_DIR}/logs/gateway.log"

# 检查PID文件
if [ ! -f "${PID_FILE}" ]; then
    echo -e "${RED}状态: 未运行${NC}"
    exit 0
fi

# 读取PID
PID=$(cat "${PID_FILE}")

# 检查进程是否存在
if ! ps -p "${PID}" > /dev/null 2>&1; then
    echo -e "${RED}状态: 进程已退出（PID文件存在但进程不存在）${NC}"
    echo -e "${YELLOW}建议: rm ${PID_FILE}${NC}"
    exit 0
fi

# 进程运行中
echo -e "${GREEN}状态: 运行中${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "进程信息:"
echo "  PID:      ${PID}"
echo "  运行时间: $(ps -p "${PID}" -o etime= 2>/dev/null | xargs)"
echo "  CPU:      $(ps -p "${PID}" -o %cpu= 2>/dev/null | xargs)%"
echo "  内存:     $(ps -p "${PID}" -o %mem= 2>/dev/null | xargs)%"
echo ""
echo "端口监听:"
if command -v netstat &> /dev/null; then
    netstat -an 2>/dev/null | grep LISTEN | grep ":8005\|:8888\|:9000" || echo "  (无法获取端口信息)"
elif command -v lsof &> /dev/null; then
    lsof -i -P -n 2>/dev/null | grep LISTEN | grep "${PID}" || echo "  (无法获取端口信息)"
fi
echo ""
echo "最近日志 (最后10行):"
if [ -f "${LOG_FILE}" ]; then
    tail -10 "${LOG_FILE}"
else
    echo -e "${YELLOW}日志文件不存在: ${LOG_FILE}${NC}"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
