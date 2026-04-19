#!/bin/bash
# 启动小诺NLP服务脚本

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
PINK='\033[0;95m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

# 项目路径
PROJECT_ROOT=$(cd $(dirname "$0")/../.. && pwd)
NLP_DIR="${PROJECT_ROOT}/modules/nlp/xiaonuo_nlp_deployment"
# 使用平台统一虚拟环境 athena_env
VENV_DIR="${PROJECT_ROOT}/athena_env"

echo -e "${PINK}🧠 启动小诺NLP智能服务...${NC}"
echo -e "${BLUE}时间: $(date)${NC}"

# 检查NLP目录
if [ ! -d "$NLP_DIR" ]; then
    echo -e "${RED}❌ NLP目录不存在: $NLP_DIR${NC}"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}⚠️ 虚拟环境不存在，使用系统Python${NC}"
    PYTHON_CMD="python3"
else
    echo -e "${GREEN}✅ 使用虚拟环境: $VENV_DIR${NC}"
    source "$VENV_DIR/bin/activate"
    PYTHON_CMD="python3"
fi

# 进入NLP目录
cd "$NLP_DIR"

# 检查配置文件
if [ ! -f "deploy_config.json" ]; then
    echo -e "${RED}❌ 配置文件不存在${NC}"
    exit 1
fi

# 检查服务文件
if [ ! -f "xiaonuo_nlp_server.py" ]; then
    echo -e "${RED}❌ NLP服务器文件不存在${NC}"
    exit 1
fi

# 创建日志目录
LOG_DIR="${PROJECT_ROOT}/production/logs"
mkdir -p "$LOG_DIR"

echo -e "${PINK}🚀 启动NLP服务...${NC}"

# 启动服务（后台运行）
nohup $PYTHON_CMD xiaonuo_nlp_server.py > "$LOG_DIR/nlp_server.log" 2>&1 &
NLP_PID=$!

# 保存PID
echo $NLP_PID > "$LOG_DIR/nlp_service.pid"

echo -e "${BLUE}📋 NLP服务进程ID: $NLP_PID${NC}"

# 等待启动
sleep 3

# 检查进程
if ps -p $NLP_PID > /dev/null; then
    echo -e "${GREEN}✅ NLP服务启动成功！${NC}"
    echo -e "${PINK}💖 爸爸，NLP智能服务已经为您准备好了！${NC}"
    echo -e "${BLUE}📝 查看日志: tail -f $LOG_DIR/nlp_server.log${NC}"
    echo -e "${BLUE}🔍 停止服务: kill \$(cat $LOG_DIR/nlp_service.pid)${NC}"
else
    echo -e "${RED}❌ NLP服务启动失败${NC}"
    echo -e "${BLUE}📋 请查看日志: $LOG_DIR/nlp_server.log${NC}"
    exit 1
fi

echo -e "${GREEN}🎯 NLP服务启动完成${NC}"