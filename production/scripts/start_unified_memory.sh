#!/bin/bash
# Athena统一记忆系统 - 生产环境启动脚本
# Unified Agent Memory System - Production Launcher

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目路径
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🏛️  Athena统一记忆系统 - 生产环境启动脚本${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# 检查虚拟环境
VENV_PATH="$PROJECT_ROOT/athena_env"
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${RED}❌ 虚拟环境不存在: $VENV_PATH${NC}"
    echo -e "${YELLOW}💡 请先创建虚拟环境: python3 -m venv $VENV_PATH${NC}"
    exit 1
fi

# 激活虚拟环境
echo -e "${GREEN}🔌 激活虚拟环境...${NC}"
source "$VENV_PATH/bin/activate"

# 检查必要的依赖
echo -e "${GREEN}📦 检查依赖...${NC}"
python3 -c "import asyncpg" 2>/dev/null || {
    echo -e "${YELLOW}⚠️  安装缺失的依赖...${NC}"
    pip install asyncpg aiohttp sentence-transformers
}

# 检查PostgreSQL
echo -e "${GREEN}🔍 检查PostgreSQL服务...${NC}"
if ! psql -h localhost -p 5432 -U postgres -c '\q' 2>/dev/null; then
    echo -e "${RED}❌ PostgreSQL服务未运行或连接失败${NC}"
    echo -e "${YELLOW}💡 请启动PostgreSQL服务${NC}"
    exit 1
fi
echo -e "${GREEN}✅ PostgreSQL服务正常${NC}"

# 检查Qdrant
echo -e "${GREEN}🔍 检查Qdrant服务...${NC}"
if ! curl -s http://localhost:6333/health > /dev/null; then
    echo -e "${YELLOW}⚠️  Qdrant服务未运行，尝试启动...${NC}"
    # 尝试启动Qdrant（如果有docker）
    if command -v docker &> /dev/null; then
        docker start qdrant 2>/dev/null || echo -e "${YELLOW}💡 请手动启动Qdrant服务${NC}"
    else
        echo -e "${YELLOW}💡 请手动启动Qdrant服务${NC}"
    fi
    sleep 2
fi

if curl -s http://localhost:6333/health > /dev/null; then
    echo -e "${GREEN}✅ Qdrant服务正常${NC}"
else
    echo -e "${RED}❌ Qdrant服务启动失败${NC}"
fi

# 检查数据库
echo -e "${GREEN}🔍 检查athena_memory数据库...${NC}"
DB_EXISTS=$(psql -h localhost -p 5432 -U postgres -lqt | cut -d \| -f 1 | grep -w athena_memory | wc -l)
if [ "$DB_EXISTS" -eq 0 ]; then
    echo -e "${YELLOW}⚠️  athena_memory数据库不存在，创建中...${NC}"
    psql -h localhost -p 5432 -U postgres -c "CREATE DATABASE athena_memory;"
    echo -e "${GREEN}✅ 数据库创建成功${NC}"
else
    echo -e "${GREEN}✅ 数据库已存在${NC}"
fi

# 创建日志目录
LOG_DIR="$PROJECT_ROOT/production/logs"
mkdir -p "$LOG_DIR"
echo -e "${GREEN}📁 日志目录: $LOG_DIR${NC}"

# 检查端口占用
PORT=8900
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  端口 $PORT 已被占用${NC}"
    echo -e "${YELLOW}💡 如需重启，请先停止现有服务:${NC}"
    echo -e "${YELLOW}   pkill -f start_unified_memory_service${NC}"
    read -p "是否强制停止现有服务并重启? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pkill -f start_unified_memory_service || true
        sleep 2
    else
        echo -e "${RED}❌ 取消启动${NC}"
        exit 1
    fi
fi

# 启动服务
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🚀 启动Athena统一记忆系统服务${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# 设置环境变量（可选）
export MEMORY_SERVICE_HOST="0.0.0.0"
export MEMORY_SERVICE_PORT="8900"
export PGHOST="localhost"
export PGPORT="5432"
export PGDATABASE="athena_memory"
export PGUSER="postgres"
export QDRANT_HOST="localhost"
export QDRANT_PORT="6333"

# 启动Python服务
cd "$PROJECT_ROOT"
nohup python3 production/scripts/start_unified_memory_service.py > "$LOG_DIR/unified_memory_service.out" 2>&1 &
SERVICE_PID=$!

# 等待服务启动
echo -e "${GREEN}⏳ 等待服务启动...${NC}"
sleep 5

# 检查服务状态
if ps -p $SERVICE_PID > /dev/null; then
    echo -e "${GREEN}✅ 服务启动成功！${NC}"
    echo ""
    echo -e "${BLUE}📋 服务信息:${NC}"
    echo -e "   进程ID: $SERVICE_PID"
    echo -e "   服务地址: http://localhost:$PORT"
    echo -e "   日志文件: $LOG_DIR/unified_memory_service.log"
    echo -e "   输出文件: $LOG_DIR/unified_memory_service.out"
    echo ""
    echo -e "${YELLOW}💡 常用命令:${NC}"
    echo -e "   查看日志: tail -f $LOG_DIR/unified_memory_service.log"
    echo -e "   停止服务: kill $SERVICE_PID"
    echo -e "   重启服务: $0"
    echo ""

    # 显示初始日志
    echo -e "${BLUE}📄 最近的服务日志:${NC}"
    tail -20 "$LOG_DIR/unified_memory_service.log"
else
    echo -e "${RED}❌ 服务启动失败${NC}"
    echo -e "${YELLOW}💡 查看错误日志: cat $LOG_DIR/unified_memory_service.out${NC}"
    exit 1
fi

echo -e "${GREEN}🎉 统一记忆系统生产环境部署完成！${NC}"
