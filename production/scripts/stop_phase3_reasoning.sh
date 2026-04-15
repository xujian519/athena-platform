#!/bin/bash
# Athena知识图谱系统 - Phase 3 服务停止脚本

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
NC='\033[0m'

echo -e "${PURPLE}🛑 Athena知识图谱系统 - Phase 3 服务停止${NC}"
echo -e "${BLUE}停止时间: $(date)${NC}"
echo ""

# 切换到项目根目录
cd "$(dirname "$0")/../.."

# 定义要停止的服务
services=(
    "expert_rule_engine.pid:ExpertRuleEngine:专家级规则推理引擎"
    "patent_rule_chain.pid:PatentRuleChainEngine:专利规则链引擎"
    "prior_art_analyzer.pid:PriorArtAnalyzer:现有技术分析器"
    "llm_enhanced_judgment.pid:LLMEnhancedJudgment:LLM增强判断系统"
    "monitoring.pid:Monitor:系统监控服务"
)

stopped_count=0
total_count=${#services[@]}

echo -e "${BLUE}🔄 正在停止Phase 3推理引擎服务...${NC}"

for service in "${services[@]}"; do
    pid_file=$(echo $service | cut -d: -f1)
    name=$(echo $service | cut -d: -f2)
    desc=$(echo $service | cut -d: -f3)

    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")

        if ps -p $pid > /dev/null 2>&1; then
            echo -e "${YELLOW}⏹️  正在停止 $name ($pid)...${NC}"

            # 尝试优雅停止
            kill -TERM $pid 2>/dev/null || true

            # 等待进程停止
            timeout=10
            while [ $timeout -gt 0 ] && ps -p $pid > /dev/null 2>&1; do
                sleep 1
                timeout=$((timeout - 1))
            done

            # 如果进程仍在运行，强制停止
            if ps -p $pid > /dev/null 2>&1; then
                echo -e "${RED}⚡ 强制停止 $name ($pid)...${NC}"
                kill -KILL $pid 2>/dev/null || true
                sleep 1
            fi

            # 验证是否成功停止
            if ps -p $pid > /dev/null 2>&1; then
                echo -e "${RED}❌ $name 停止失败${NC}"
            else
                echo -e "${GREEN}✅ $name 已成功停止${NC}"
                stopped_count=$((stopped_count + 1))
                # 清理PID文件
                rm -f "$pid_file"
            fi
        else
            echo -e "${YELLOW}⚠️  $name 进程不存在，清理PID文件${NC}"
            rm -f "$pid_file"
            stopped_count=$((stopped_count + 1))
        fi
    else
        echo -e "${YELLOW}⚠️  $name PID文件不存在，可能已经停止${NC}"
        stopped_count=$((stopped_count + 1))
    fi

    echo ""
done

# 停止时间
echo -e "${BLUE}🕐 停止完成时间: $(date)${NC}"

# 统计结果
if [ $stopped_count -eq $total_count ]; then
    echo -e "${GREEN}🎉 所有Phase 3推理引擎服务已成功停止${NC}"
else
    echo -e "${YELLOW}⚠️  $stopped_count/$total_count 个服务已停止${NC}"
fi

echo ""
echo -e "${BLUE}📊 停止摘要:${NC}"
echo -e "   • 成功停止: $stopped_count/$total_count 个服务"
echo -e "   • 停止成功率: $((stopped_count * 100 / total_count))%"

# 检查是否还有残留进程
echo ""
echo -e "${BLUE}🔍 检查残留进程...${NC}"

remaining_processes=$(ps aux | grep -E "expert_rule_engine|patent_rule_chain|prior_art_analyzer|llm_enhanced_judgment" | grep -v grep | wc -l)

if [ $remaining_processes -gt 0 ]; then
    echo -e "${YELLOW}⚠️  发现 $remaining_processes 个残留进程，正在清理...${NC}"

    # 查找并清理残留进程
    remaining_pids=$(ps aux | grep -E "expert_rule_engine|patent_rule_chain|prior_art_analyzer|llm_enhanced_judgment" | grep -v grep | awk '{print $2}')

    for pid in $remaining_pids; do
        process_name=$(ps -p $pid -o command --no-headers 2>/dev/null | head -1)
        echo -e "${RED}🗑️  清理残留进程: $pid ($process_name)${NC}"
        kill -KILL $pid 2>/dev/null || true
    done

    sleep 1

    # 再次检查
    final_remaining=$(ps aux | grep -E "expert_rule_engine|patent_rule_chain|prior_art_analyzer|llm_enhanced_judgment" | grep -v grep | wc -l)
    if [ $final_remaining -eq 0 ]; then
        echo -e "${GREEN}✅ 所有残留进程已清理${NC}"
    else
        echo -e "${YELLOW}⚠️  仍有 $final_remaining 个残留进程${NC}"
    fi
else
    echo -e "${GREEN}✅ 无残留进程${NC}"
fi

# 保存停止记录
echo ""
echo -e "${BLUE}📝 保存停止记录...${NC}"

stop_record={
    "stop_time": "$(date -Iseconds)",
    "services_stopped": $stopped_count,
    "total_services": $total_count,
    "success_rate": $((stopped_count * 100 / total_count))
}

echo "$stop_record" > production/logs/stop_record_$(date +%Y%m%d_%H%M%S).json

# 系统状态检查
echo ""
echo -e "${BLUE}📈 当前系统状态:${NC}"

# CPU和内存使用率
cpu_usage=$(top -l 1 | grep "CPU usage" | awk '{print $3}' | sed 's/%//')
memory_info=$(vm_stat | grep "Pages free")
free_pages=$(echo $memory_info | awk '{print $3}' | sed 's/\.//')
inactive_pages=$(vm_stat | grep "Pages inactive" | awk '{print $3}' | sed 's/\.//')
active_pages=$(vm_stat | grep "Pages active" | awk '{print $3}' | sed 's/\.//')
page_size=4096
total_memory=$((($free_pages + $inactive_pages + $active_pages) * $page_size))
used_memory=$((($active_pages + $inactive_pages) * $page_size))
memory_usage=$(echo "scale=2; $used_memory / $total_memory * 100" | bc)

echo -e "   • CPU使用率: ${cpu_usage}%"
echo -e "   • 内存使用率: ${memory_usage}%"

# 提供重启建议
echo ""
echo -e "${BLUE}💡 后续操作建议:${NC}"
echo -e "   🔄 重新启动: ./production/dev/scripts/start_phase3_reasoning.sh"
echo -e "   🔍 检查状态: ./production/dev/scripts/check_phase3_status.sh"
echo -e "   📊 查看日志: ls -la production/logs/"
echo -e "   🧹 清理数据: ./production/dev/scripts/cleanup_phase3_data.sh"

if [ $stopped_count -eq $total_count ]; then
    echo ""
    echo -e "${GREEN}🎯 Phase 3推理引擎已完全停止，系统资源已释放${NC}"
    echo -e "${PURPLE}🧠 Athena知识图谱系统进入待机状态${NC}"
else
    echo ""
    echo -e "${YELLOW}⚠️  部分服务停止异常，建议手动检查并处理${NC}"
fi

echo ""
echo -e "${PURPLE}🛑 Phase 3服务停止完成${NC}"