#!/bin/bash

# 多模态文件系统API服务自动启动脚本
# Multimodal File System API Service Auto-Start Script

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置信息
SERVICE_NAME="multimodal-api"
SERVICE_PORT=8000
SERVICE_DIR="/Users/xujian/Athena工作平台/services/multimodal"
LOG_FILE="/Users/xujian/Athena工作平台/logs/multimodal_service.log"
PID_FILE="/Users/xujian/Athena工作平台/logs/multimodal_service.pid"

echo -e "${BLUE}🚀 多模态文件系统服务启动器${NC}"
echo -e "${BLUE}================================${NC}"

# 创建日志目录
mkdir -p "$(dirname "$LOG_FILE")"

# 检查是否已在运行
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  服务已在运行 (PID: $PID)${NC}"
        echo -e "${YELLOW}端口: $SERVICE_PORT${NC}"
        exit 0
    else
        echo -e "${YELLOW}🗑️  清理过期的PID文件${NC}"
        rm -f "$PID_FILE"
    fi
fi

# 检查端口是否被占用
if lsof -Pi :$SERVICE_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${RED}❌ 端口 $SERVICE_PORT 已被占用${NC}"
    echo -e "${RED}请检查是否有其他服务在使用该端口${NC}"
    exit 1
fi

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 未安装或不在PATH中${NC}"
    exit 1
fi

# 进入服务目录
cd "$SERVICE_DIR"

# 检查必要文件
if [ ! -f "multimodal_api_server.py" ]; then
    echo -e "${RED}❌ 找不到 multimodal_api_server.py${NC}"
    exit 1
fi

# 检查依赖
echo -e "${BLUE}🔍 检查依赖包...${NC}"
python3 -c "
import sys
required_packages = ['fastapi', 'uvicorn', 'aiofiles', 'pillow', 'jieba']
missing_packages = []

for package in required_packages:
    try:
        __import__(package)
    except ImportError:
        missing_packages.append(package)

if missing_packages:
    print(f'缺少依赖包: {missing_packages}')
    print('请运行: pip3 install ' + ' '.join(missing_packages))
    sys.exit(1)

print('✅ 所有依赖包已安装')
" || {
    echo -e "${RED}❌ 依赖检查失败${NC}"
    exit 1
}

# 启动服务
echo -e "${BLUE}🚀 启动多模态API服务...${NC}"

# 启动服务并记录PID
nohup python3 multimodal_api_server.py > "$LOG_FILE" 2>&1 &
SERVICE_PID=$!

# 保存PID
echo $SERVICE_PID > "$PID_FILE"

# 等待服务启动
echo -e "${BLUE}⏳ 等待服务启动...${NC}"
for i in {1..30}; do
    if ps -p "$SERVICE_PID" > /dev/null 2>&1; then
        # 检查服务是否响应
        if curl -s "http://localhost:$SERVICE_PORT/health" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ 服务启动成功！${NC}"
            echo -e "${GREEN}📍 端口: $SERVICE_PORT${NC}"
            echo -e "${GREEN}🆔 PID: $SERVICE_PID${NC}"
            echo -e "${GREEN}📋 日志: $LOG_FILE${NC}"
            echo -e "${GREEN}🌐 API文档: http://localhost:$SERVICE_PORT/docs${NC}"
            echo ""
            echo -e "${BLUE}常用命令:${NC}"
            echo -e "  查看日志: tail -f $LOG_FILE"
            echo -e "  停止服务: ./stop_multimodal_service.sh"
            echo -e "  重启服务: ./restart_multimodal_service.sh"
            echo ""
            exit 0
        fi
    else
        echo -e "${RED}❌ 服务启动失败${NC}"
        rm -f "$PID_FILE"
        cat "$LOG_FILE"
        exit 1
    fi

    sleep 1
    echo -n "."
done

echo -e "${RED}❌ 服务启动超时${NC}"
echo -e "${RED}请检查日志: $LOG_FILE${NC}"
rm -f "$PID_FILE"
exit 1