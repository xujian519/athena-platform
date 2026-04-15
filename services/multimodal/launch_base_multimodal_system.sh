#!/bin/bash

# Athena多模态文件系统基础设置启动脚本
# Base Multimodal File System Launch Script

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Athena多模态文件系统基础设置启动器${NC}"
echo -e "${BLUE}=======================================${NC}"

# 配置信息
SERVICE_DIR="/Users/xujian/Athena工作平台/services/multimodal"
PYTHON_ENV="$SERVICE_DIR/venv"
LOG_DIR="/Users/xujian/Athena工作平台/logs/multimodal"

# 创建日志目录
mkdir -p "$LOG_DIR"

echo -e "${PURPLE}📋 启动清单检查${NC}"

# 1. 检查Python环境
echo -e "${BLUE}[1/7] 检查Python环境...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    echo -e "${GREEN}✅ Python版本: $PYTHON_VERSION${NC}"
else
    echo -e "${RED}❌ Python3未安装${NC}"
    exit 1
fi

# 2. 检查虚拟环境
echo -e "${BLUE}[2/7] 检查虚拟环境...${NC}"
if [ -d "$PYTHON_ENV" ]; then
    echo -e "${GREEN}✅ 虚拟环境存在${NC}"
    source "$PYTHON_ENV/bin/activate"

    # 检查依赖
    echo -e "${BLUE}   检查依赖包...${NC}"
    python -c "
required_packages = ['fastapi', 'uvicorn', 'aiofiles', 'pillow', 'jieba']
missing = []
for pkg in required_packages:
    try:
        __import__(pkg)
    except ImportError:
        missing.append(pkg)
if missing:
    print(f'缺少依赖: {missing}')
    exit(1)
print('✅ 依赖包完整')
" || {
        echo -e "${YELLOW}⚠️  依赖检查有问题，继续安装...${NC}"
        pip install fastapi uvicorn aiofiles pillow jieba
    }
else
    echo -e "${YELLOW}⚠️  创建虚拟环境...${NC}"
    python3 -m venv "$PYTHON_ENV"
    source "$PYTHON_ENV/bin/activate"
    pip install fastapi uvicorn aiofiles pillow jieba
fi

# 3. 初始化基础设置
echo -e "${BLUE}[3/7] 初始化基础设置...${NC}"
cd "$SERVICE_DIR"

python3 -c "
from base_settings_manager import get_settings_manager
manager = get_settings_manager()

# 检查服务状态
status = manager.get_service_status()
print('基础设置状态:')
for key, value in status.items():
    print(f'  {key}: {value}')

# 确保存储目录存在
import os
storage_path = manager.get_setting('storage.base_path')
if storage_path and not os.path.exists(storage_path):
    os.makedirs(storage_path, exist_ok=True)
    print(f'创建存储目录: {storage_path}')
else:
    print('存储目录已存在')
" || {
    echo -e "${RED}❌ 基础设置初始化失败${NC}"
    exit 1
}

echo -e "${GREEN}✅ 基础设置初始化完成${NC}"

# 4. 检查缓存系统
echo -e "${BLUE}[4/7] 检查缓存系统...${NC}"
python3 -c "
from cache_manager import cache_manager
stats = cache_manager.get_stats()
print('缓存系统状态:')
for key, value in stats.items():
    print(f'  {key}: {value}')
" || {
    echo -e "${YELLOW}⚠️  缓存系统检查失败，将使用本地缓存${NC}"
}

echo -e "${GREEN}✅ 缓存系统检查完成${NC}"

# 5. 检查存储目录
echo -e "${BLUE}[5/7] 检查存储目录...${NC}"
STORAGE_PATH=$(python3 -c "
from base_settings_manager import get_settings_manager
manager = get_settings_manager()
print(manager.get_setting('storage.base_path'))
")

if [ -d "$STORAGE_PATH" ]; then
    echo -e "${GREEN}✅ 存储目录存在: $STORAGE_PATH${NC}"

    # 检查存储空间
    DISK_USAGE=$(df -h "$STORAGE_PATH" | awk 'NR==2{print $5}')
    echo -e "${BLUE}   可用空间: $DISK_USAGE${NC}"
else
    echo -e "${YELLOW}⚠️  创建存储目录...${NC}"
    mkdir -p "$STORAGE_PATH"
    echo -e "${GREEN}✅ 存储目录已创建: $STORAGE_PATH${NC}"
fi

# 6. 停止旧服务（如果运行中）
echo -e "${BLUE}[6/7] 清理旧进程...${NC}"
if [ -f "/tmp/multimodal_service.pid" ]; then
    OLD_PID=$(cat /tmp/multimodal_service.pid)
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}   停止旧服务 (PID: $OLD_PID)...${NC}"
        kill "$OLD_PID"
        sleep 2
    fi
    rm -f /tmp/multimodal_service.pid
fi

# 7. 启动新服务
echo -e "${BLUE}[7/7] 启动多模态服务...${NC}"
echo -e "${PURPLE}🌟 启动参数:${NC}"
echo -e "${PURPLE}   主机: 0.0.0.0${NC}"
echo -e "${PURPLE}   端口: $(python3 -c \"from base_settings_manager import get_settings_manager; manager = get_settings_manager(); print(manager.get_setting('api.port', 8000))\")${NC}"
echo -e "${PURPLE}   工作进程: $(python3 -c \"from base_settings_manager import get_settings_manager; manager = get_settings_manager(); print(manager.get_setting('api.workers', 1))\")${NC}"

# 启动服务
LOG_FILE="$LOG_DIR/base_multimodal_$(date +%Y%m%d_%H%M%S).log"

nohup python enhanced_multimodal_api.py > "$LOG_FILE" 2>&1 &
SERVICE_PID=$!

# 保存PID
echo "$SERVICE_PID" > /tmp/multimodal_service.pid

# 等待服务启动
echo -e "${BLUE}⏳ 等待服务启动...${NC}"
sleep 3

# 检查服务状态
if ps -p "$SERVICE_PID" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 服务启动成功！${NC}"
    echo ""
    echo -e "${PURPLE}🎯 服务信息:${NC}"
    echo -e "${GREEN}📍 端口: 8000${NC}"
    echo -e "${GREEN}🆔 PID: $SERVICE_PID${NC}"
    echo -e "${GREEN}📋 日志: $LOG_FILE${NC}"
    echo -e "${GREEN}🌐 API文档: http://localhost:8000/docs${NC}"
    echo -e "${GREEN}🔍 健康检查: http://localhost:8000/health${NC}"
    echo ""
    echo -e "${PURPLE}📊 管理命令:${NC}"
    echo -e "${BLUE}   查看日志: tail -f $LOG_FILE${NC}"
    echo -e "${BLUE}   停止服务: kill $SERVICE_PID${NC}"
    echo -e "${BLUE}   查看状态: curl http://localhost:8000/health${NC}"
    echo ""
    echo -e "${GREEN}🎉 Athena多模态文件系统已启动！${NC}"
else
    echo -e "${RED}❌ 服务启动失败${NC}"
    echo -e "${YELLOW}   查看日志: tail -f $LOG_FILE${NC}"
    rm -f /tmp/multimodal_service.pid
    exit 1
fi