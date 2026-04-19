#!/bin/bash
# 小娜生产环境启动脚本

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
PINK='\033[0;95m'
NC='\033[0m'

echo -e "${PINK}🚀 启动小娜生产环境 v2.1...${NC}"
echo -e "${BLUE}时间: $(date)${NC}"

# 切换目录
cd "$(dirname "$0")/../services"

# 加载环境变量
if [ -f "/Users/xujian/Athena工作平台/.env.production.unified" ]; then
    export $(grep -E '^(GLM|DEEPSEEK|QDRANT|NEBULA|DB)' /Users/xujian/Athena工作平台/.env.production.unified | xargs)
    echo -e "${GREEN}✅ 环境变量已加载${NC}"
else
    echo -e "${PINK}⚠️  警告: .env.production.unified 未找到${NC}"
fi

# 创建日志目录
mkdir -p /Users/xujian/Athena工作平台/logs/xiaona

# 启动小娜代理
echo -e "${PINK}🌸 启动小娜代理...${NC}"
python3 xiaona_agent_v2.py

echo -e "${GREEN}✅ 小娜已启动${NC}"
