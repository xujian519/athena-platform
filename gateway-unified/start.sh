#!/bin/bash
# Athena Gateway 启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GATEWAY_BIN="${SCRIPT_DIR}/bin/gateway"
PID_FILE="${SCRIPT_DIR}/gateway.pid"
LOG_DIR="${SCRIPT_DIR}/logs"
LOG_FILE="${LOG_DIR}/gateway.log"

# 创建日志目录
mkdir -p "${LOG_DIR}"

# 检查二进制文件
if [ ! -f "${GATEWAY_BIN}" ]; then
    echo -e "${RED}错误: 网关二进制文件不存在: ${GATEWAY_BIN}${NC}"
    echo "请先运行: go build -o bin/gateway ./cmd/gateway"
    exit 1
fi

# 检查是否已运行
if [ -f "${PID_FILE}" ]; then
    PID=$(cat "${PID_FILE}")
    if ps -p "${PID}" > /dev/null 2>&1; then
        echo -e "${YELLOW}网关已在运行中 (PID: ${PID})${NC}"
        echo "如需重启，请先运行: ./stop.sh"
        exit 1
    else
        echo -e "${YELLOW}发现旧的PID文件，清理中...${NC}"
        rm -f "${PID_FILE}"
    fi
fi

# 加载环境变量
if [ -f "${SCRIPT_DIR}/.env" ]; then
    echo "加载环境变量: .env"
    export $(grep -v '^#' "${SCRIPT_DIR}/.env" | xargs)
fi

# 启动网关
echo -e "${GREEN}🚀 启动 Athena Gateway...${NC}"
echo "日志文件: ${LOG_FILE}"

# 使用nohup后台启动
nohup "${GATEWAY_BIN}" >> "${LOG_FILE}" 2>&1 &
GATEWAY_PID=$!

# 保存PID
echo "${GATEWAY_PID}" > "${PID_FILE}"

# 等待启动
sleep 2

# 验证启动状态
if ps -p "${GATEWAY_PID}" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Athena Gateway 启动成功!${NC}"
    echo "PID: ${GATEWAY_PID}"
    echo ""
    echo "查看日志: tail -f ${LOG_FILE}"
    echo "查看状态: ./status.sh"
    echo "停止服务: ./stop.sh"
else
    echo -e "${RED}❌ 启动失败，请检查日志: ${LOG_FILE}${NC}"
    rm -f "${PID_FILE}"
    exit 1
fi
