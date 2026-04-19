#!/bin/bash
# Athena知识图谱系统 - Phase 3 服务状态检查脚本

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
NC='\033[0m'

echo -e "${PURPLE}🧠 Athena知识图谱系统 - Phase 3 服务状态检查${NC}"
echo -e "${BLUE}检查时间: $(date)${NC}"
echo ""

# 切换到项目根目录
cd "$(dirname "$0")/../.."

# 检查进程状态
echo -e "${BLUE}🔍 服务进程状态:${NC}"
services=(
    "production/logs/expert_rule_engine.pid:ExpertRuleEngine:专家级规则推理引擎"
    "production/logs/patent_rule_chain.pid:PatentRuleChainEngine:专利规则链引擎"
    "production/logs/prior_art_analyzer.pid:PriorArtAnalyzer:现有技术分析器"
    "production/logs/llm_enhanced_judgment.pid:LLMEnhancedJudgment:LLM增强判断系统"
    "production/logs/monitoring.pid:Monitor:系统监控服务"
)

running_count=0
total_count=${#services[@]}

for service in "${services[@]}"; do
    pid_file=$(echo $service | cut -d: -f1)
    name=$(echo $service | cut -d: -f2)
    desc=$(echo $service | cut -d: -f3)

    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            # 获取进程详细信息
            cpu=$(ps -p $pid -o %cpu --no-headers 2>/dev/null | tr -d ' ')
            memory=$(ps -p $pid -o %mem --no-headers 2>/dev/null | tr -d ' ')
            start_time=$(ps -p $pid -o lstart --no-headers 2>/dev/null)

            echo -e "${GREEN}✅ $name${NC} - ${desc}"
            echo -e "   PID: $pid | CPU: ${cpu}% | 内存: ${memory}% | 启动: $start_time"
            running_count=$((running_count + 1))
        else
            echo -e "${RED}❌ $name${NC} - ${desc} (进程已停止)"
            echo -e "   PID文件存在但进程不存在: $pid"
        fi
    else
        echo -e "${YELLOW}⚠️  $name${NC} - ${desc} (PID文件不存在)"
    fi
    echo ""
done

# 计算服务状态
running_percentage=$((running_count * 100 / total_count))
if [ $running_percentage -eq 100 ]; then
    status_color=$GREEN
    status_text="全部正常"
elif [ $running_percentage -ge 80 ]; then
    status_color=$YELLOW
    status_text="基本正常"
else
    status_color=$RED
    status_text="需要关注"
fi

echo -e "${BLUE}📊 服务概览: ${status_color}$running_count/$total_count 个服务运行中 ($running_percentage%) - $status_text${NC}"
echo ""

# 检查系统资源
echo -e "${BLUE}💻 系统资源状态:${NC}"

# CPU使用率
cpu_usage=$(top -l 1 | grep "CPU usage" | awk '{print $3}' | sed 's/%//')
if (( $(echo "$cpu_usage > 80" | bc -l) )); then
    cpu_color=$RED
elif (( $(echo "$cpu_usage > 60" | bc -l) )); then
    cpu_color=$YELLOW
else
    cpu_color=$GREEN
fi

# 内存使用率
memory_info=$(vm_stat | grep "Pages free")
free_pages=$(echo $memory_info | awk '{print $3}' | sed 's/\.//')
total_pages=$(vm_stat | grep "Pages free" | awk '{print $1}' | sed 's/\.//')
inactive_pages=$(vm_stat | grep "Pages inactive" | awk '{print $3}' | sed 's/\.//')
active_pages=$(vm_stat | grep "Pages active" | awk '{print $3}' | sed 's/\.//')

# 计算内存使用（简化计算）
page_size=4096
total_memory=$((($free_pages + $inactive_pages + $active_pages) * $page_size))
used_memory=$((($active_pages + $inactive_pages) * $page_size))
memory_usage=$(echo "scale=2; $used_memory / $total_memory * 100" | bc)

if (( $(echo "$memory_usage > 80" | bc -l) )); then
    memory_color=$RED
elif (( $(echo "$memory_usage > 60" | bc -l) )); then
    memory_color=$YELLOW
else
    memory_color=$GREEN
fi

# 磁盘使用率
disk_usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $disk_usage -gt 80 ]; then
    disk_color=$RED
elif [ $disk_usage -gt 60 ]; then
    disk_color=$YELLOW
else
    disk_color=$GREEN
fi

echo -e "   CPU使用率: ${cpu_color}${cpu_usage}%${NC}"
echo -e "   内存使用率: ${memory_color}${memory_usage}%${NC}"
echo -e "   磁盘使用率: ${disk_color}${disk_usage}%${NC}"
echo ""

# 检查依赖服务
echo -e "${BLUE}🔗 依赖服务状态:${NC}"

# PostgreSQL
if pg_isready -q; then
    echo -e "${GREEN}✅ PostgreSQL${NC} - 数据库服务正常"
    pg_connections=$(psql -U athena_admin -d athena_patent_production -t -c "SELECT count(*) FROM pg_stat_activity;" 2>/dev/null | tr -d ' ')
    echo -e "   当前连接数: $pg_connections"
else
    echo -e "${RED}❌ PostgreSQL${NC} - 数据库服务异常"
fi

# Redis
if redis-cli ping > /dev/null 2>&1; then
    redis_memory=$(redis-cli info memory 2>/dev/null | grep "used_memory_human" | cut -d: -f2 | tr -d '\r')
    echo -e "${GREEN}✅ Redis${NC} - 缓存服务正常 (内存使用: $redis_memory)"
else
    echo -e "${RED}❌ Redis${NC} - 缓存服务异常"
fi

# Elasticsearch
if curl -s http://localhost:9200/_cluster/health > /dev/null 2>&1; then
    es_status=$(curl -s http://localhost:9200/_cluster/health | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    if [ "$es_status" = "green" ]; then
        es_color=$GREEN
    elif [ "$es_status" = "yellow" ]; then
        es_color=$YELLOW
    else
        es_color=$RED
    fi
    echo -e "${es_color}✅ Elasticsearch${NC} - 搜索服务状态: $es_status"
else
    echo -e "${YELLOW}⚠️  Elasticsearch${NC} - 搜索服务未运行"
fi

# Qdrant
if curl -s http://localhost:6333/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Qdrant${NC} - 向量数据库服务正常"
else
    echo -e "${YELLOW}⚠️  Qdrant${NC} - 向量数据库服务未运行"
fi

echo ""

# 检查最近的日志
echo -e "${BLUE}📝 最近日志摘要:${NC}"

log_files=(
    "production/logs/expert_rule_engine.log:ExpertRuleEngine"
    "production/logs/patent_rule_chain.log:PatentRuleChainEngine"
    "production/logs/prior_art_analyzer.log:PriorArtAnalyzer"
    "production/logs/llm_enhanced_judgment.log:LLMEnhancedJudgment"
    "production/logs/monitoring.log:Monitor"
)

for log_file in "${log_files[@]}"; do
    file=$(echo $log_file | cut -d: -f1)
    name=$(echo $log_file | cut -d: -f2)

    if [ -f "$file" ]; then
        last_lines=$(tail -5 "$file" 2>/dev/null)
        if [ $? -eq 0 ]; then
            error_count=$(echo "$last_lines" | grep -i "error\|exception\|failed" | wc -l)
            success_count=$(echo "$last_lines" | grep -i "✅\|success\|完成" | wc -l)

            if [ $error_count -gt 0 ]; then
                log_color=$RED
                log_status="有错误"
            elif [ $success_count -gt 0 ]; then
                log_color=$GREEN
                log_status="正常"
            else
                log_color=$YELLOW
                log_status="需检查"
            fi

            echo -e "   ${log_color}$name:${NC} $log_status"
        else
            echo -e "   ${YELLOW}$name:${NC} 日志读取异常"
        fi
    else
        echo -e "   ${YELLOW}$name:${NC} 日志文件不存在"
    fi
done

echo ""

# 检查配置文件
echo -e "${BLUE}⚙️  配置文件状态:${NC}"
config_files=(
    "production/phase3_config.py:Phase 3配置"
    "production/config/phase3_production_config.json:生产环境配置"
)

for config_file in "${config_files[@]}"; do
    file=$(echo $config_file | cut -d: -f1)
    name=$(echo $config_file | cut -d: -f2)

    if [ -f "$file" ]; then
        file_age=$(find "$file" -mtime +7 -print 2>/dev/null)
        if [ -n "$file_age" ]; then
            config_color=$YELLOW
            config_status="较旧"
        else
            config_color=$GREEN
            config_status="最新"
        fi
        echo -e "   ${config_color}$name:${NC} $config_status"
    else
        echo -e "   ${RED}$name:${NC} 文件缺失"
    fi
done

echo ""

# 生成状态摘要
echo -e "${BLUE}📈 状态摘要:${NC}"

# 计算总体健康度
health_score=$((($running_count * 20) + ($running_percentage / 5))) # 满分100

if [ $health_score -ge 90 ]; then
    health_color=$GREEN
    health_status="优秀"
    health_emoji="🟢"
elif [ $health_score -ge 70 ]; then
    health_color=$YELLOW
    health_status="良好"
    health_emoji="🟡"
else
    health_color=$RED
    health_status="需要关注"
    health_emoji="🔴"
fi

echo -e "   服务运行: ${running_count}/${total_count} (${running_percentage}%)"
echo -e "   系统健康度: ${health_color}${health_score}/100 - $health_status $health_emoji${NC}"

# 提供操作建议
echo ""
echo -e "${BLUE}💡 操作建议:${NC}"

if [ $running_count -eq $total_count ]; then
    echo -e "   🎉 系统运行完美，可以正常使用所有推理功能"
elif [ $running_count -ge $((total_count - 1)) ]; then
    echo -e "   ⚠️  系统基本正常，建议检查失败的服务"
else
    echo -e "   🔴 多个服务异常，建议立即检查并重启服务"
    echo -e "   📋 重启命令: ./production/dev/scripts/restart_phase3_reasoning.sh"
fi

if (( $(echo "$cpu_usage > 80" | bc -l) )); then
    echo -e "   🔥 CPU使用率过高，建议检查推理任务负载"
fi

if (( $(echo "$memory_usage > 80" | bc -l) )); then
    echo -e "   💾 内存使用率过高，建议优化内存配置"
fi

if [ $disk_usage -gt 80 ]; then
    echo -e "   💿 磁盘空间不足，建议清理日志和临时文件"
fi

echo ""
echo -e "${PURPLE}🧠 Athena Phase 3 专家级推理引擎状态检查完成${NC}"