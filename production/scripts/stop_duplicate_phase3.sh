#!/bin/bash
# 停止重复的Phase 3推理引擎服务

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}🔄 检测并停止重复的Phase 3推理引擎服务...${NC}"
echo -e "${BLUE}时间: $(date)${NC}"

# 停止旧的Phase 3服务 (49137-49140)
OLD_PIDS=(49137 49138 49139 49140)
SERVICE_NAMES=("专家规则推理引擎" "专利规则链引擎" "现有技术分析器" "LLM增强判断系统")

echo ""
echo -e "${YELLOW}🔍 检查旧的Phase 3服务进程...${NC}"

for i in "${!OLD_PIDS[@]}"; do
    PID=${OLD_PIDS[$i]}
    NAME=${SERVICE_NAMES[$i]}

    if ps -p $PID > /dev/null 2>&1; then
        echo -e "${YELLOW}⏹️  停止 $NAME (PID: $PID)...${NC}"
        kill $PID

        # 等待进程结束
        sleep 2

        if ps -p $PID > /dev/null 2>&1; then
            echo -e "${RED}⚠️  强制停止 $NAME...${NC}"
            kill -9 $PID
        fi

        echo -e "${GREEN}✅ $NAME 已停止${NC}"
    else
        echo -e "${BLUE}ℹ️  $NAME (PID: $PID) 未运行${NC}"
    fi
done

# 清理旧的PID文件
echo ""
echo -e "${YELLOW}🗑️  清理旧的PID文件...${NC}"

OLD_PID_FILES=(
    "production/logs/expert_rule_engine.pid"
    "production/logs/patent_rule_chain.pid"
    "production/logs/prior_art_analyzer.pid"
    "production/logs/llm_enhanced_judgment.pid"
)

for pid_file in "${OLD_PID_FILES[@]}"; do
    if [ -f "$pid_file" ]; then
        # 检查PID文件内容是否为旧的PID
        pid_content=$(cat "$pid_file" 2>/dev/null)
        if [[ " ${OLD_PIDS[@]} " =~ " ${pid_content} " ]]; then
            rm -f "$pid_file"
            echo -e "${GREEN}✅ 已删除旧的PID文件: $pid_file${NC}"
        fi
    fi
done

# 检查当前运行的Phase 3服务
echo ""
echo -e "${BLUE}🔍 当前运行的Phase 3服务:${NC}"

# 使用ps命令查找所有相关的python进程
CURRENT_SERVICES=$(ps aux | grep -E "(5583[4-7])" | grep -v grep | wc -l)
if [ $CURRENT_SERVICES -gt 0 ]; then
    echo -e "${GREEN}✅ 发现 $CURRENT_SERVICES 个Phase 3服务正在运行${NC}"
    ps aux | grep -E "(5583[4-7])" | grep -v grep | while read line; do
        pid=$(echo $line | awk '{print $2}')
        cmd=$(echo $line | awk '{for(i=11;i<=NF;i++) printf "%s ", $i; print ""}')
        echo -e "${BLUE}   PID $pid: ${cmd:0:50}...${NC}"
    done
else
    echo -e "${YELLOW}⚠️  未发现Phase 3服务运行${NC}"
fi

echo ""
echo -e "${GREEN}🎯 Phase 3推理引擎整合完成${NC}"
echo -e "${BLUE}💡 建议: 使用 ./production/dev/scripts/start_phase3_reasoning.sh 启动统一服务${NC}"