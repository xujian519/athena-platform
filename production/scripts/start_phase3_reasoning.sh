#!/bin/bash
# Athena知识图谱系统 - Phase 3 专家级推理引擎生产环境启动脚本

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
NC='\033[0m'

# 版本信息
PHASE3_VERSION="v3.0.0"
ATHENA_VERSION="2.0.1"

echo -e "${PURPLE}🧠 Athena知识图谱系统 - Phase 3 专家级推理引擎${NC}"
echo -e "${BLUE}版本: ${PHASE3_VERSION}${NC}"
echo -e "${BLUE}Athena基础版本: ${ATHENA_VERSION}${NC}"
echo -e "${BLUE}启动时间: $(date)${NC}"
echo -e "${BLUE}部署环境: 生产环境${NC}"
echo ""

# 切换到项目根目录
cd "$(dirname "$0")/../.."

# 设置环境变量
export ATHENA_ENV=production
export PHASE3_VERSION=${PHASE3_VERSION}
export PYTHONPATH=$(pwd)
export PATH=$PATH:$(pwd)/production/scripts

echo -e "${YELLOW}🔧 环境配置...${NC}"

# 创建必要目录
mkdir -p production/logs
mkdir -p production/data
mkdir -p production/cache
mkdir -p production/backups
mkdir -p production/tmp

echo -e "${GREEN}✅ 目录结构创建完成${NC}"

# 检查Python版本
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo -e "${RED}❌ Python版本过低，需要 >= ${required_version}，当前版本: ${python_version}${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python版本检查通过: ${python_version}${NC}"

# 检查依赖服务
echo -e "${YELLOW}🔍 检查依赖服务...${NC}"

# 检查PostgreSQL
if pg_isready -q; then
    echo -e "${GREEN}✅ PostgreSQL服务正常${NC}"
else
    echo -e "${RED}❌ PostgreSQL服务未运行${NC}"
    echo -e "${BLUE}请启动PostgreSQL服务: brew services start postgresql@17${NC}"
    exit 1
fi

# 检查Redis
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis服务正常${NC}"
else
    echo -e "${YELLOW}⚠️ Redis服务未运行，尝试启动...${NC}"
    redis-server --daemonize yes --port 6379
    sleep 2
    if redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Redis服务启动成功${NC}"
    else
        echo -e "${RED}❌ Redis服务启动失败${NC}"
        exit 1
    fi
fi

# 检查Elasticsearch
if curl -s http://localhost:9200/_cluster/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Elasticsearch服务正常${NC}"
else
    echo -e "${YELLOW}⚠️ Elasticsearch服务未运行，将启动简化模式${NC}"
fi

# 检查Qdrant
if curl -s http://localhost:6333/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Qdrant服务正常${NC}"
else
    echo -e "${YELLOW}⚠️ Qdrant服务未运行，将启动简化模式${NC}"
fi

echo ""
echo -e "${PURPLE}🚀 启动Phase 3专家级推理引擎...${NC}"

# 启动Phase 3配置验证
echo -e "${BLUE}[1/6] 验证生产环境配置...${NC}"
python3 production/phase3_config.py --env production --save > production/logs/config_validation.log 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 配置验证成功${NC}"
else
    echo -e "${RED}❌ 配置验证失败，请检查日志${NC}"
    exit 1
fi

# 启动专家规则推理引擎
echo -e "${BLUE}[2/6] 启动专家规则推理引擎...${NC}"
python3 -c "
import asyncio
import sys
sys.path.insert(0, '.')
from core.reasoning.expert_rule_engine import get_expert_rule_engine

async def start_engine():
    try:
        engine = await get_expert_rule_engine()
        await engine.initialize()
        print('✅ ExpertRuleEngine启动成功')

        # 保持服务运行
        while True:
            await asyncio.sleep(60)
            stats = engine.get_statistics()
            print(f'📊 Engine统计: {stats}')
    except Exception as e:
        print(f'❌ ExpertRuleEngine启动失败: {e}')
        sys.exit(1)

asyncio.run(start_engine())
" > production/logs/expert_rule_engine.log 2>&1 &

EXPERT_ENGINE_PID=$!
echo $EXPERT_ENGINE_PID > production/logs/expert_rule_engine.pid
echo -e "${GREEN}✅ ExpertRuleEngine启动 (PID: $EXPERT_ENGINE_PID)${NC}"

# 启动专利规则链引擎
echo -e "${BLUE}[3/6] 启动专利规则链引擎...${NC}"
python3 -c "
import asyncio
import sys
sys.path.insert(0, '.')
from core.reasoning.patent_rule_chain import get_patent_rule_chain_engine

async def start_engine():
    try:
        engine = await get_patent_rule_chain_engine()
        await engine.initialize()
        print('✅ PatentRuleChainEngine启动成功')

        # 保持服务运行
        while True:
            await asyncio.sleep(60)
            stats = engine.get_statistics()
            print(f'📊 RuleChain统计: {stats}')
    except Exception as e:
        print(f'❌ PatentRuleChainEngine启动失败: {e}')
        sys.exit(1)

asyncio.run(start_engine())
" > production/logs/patent_rule_chain.log 2>&1 &

PATENT_RULE_ENGINE_PID=$!
echo $PATENT_RULE_ENGINE_PID > production/logs/patent_rule_chain.pid
echo -e "${GREEN}✅ PatentRuleChainEngine启动 (PID: $PATENT_RULE_ENGINE_PID)${NC}"

# 启动现有技术分析器
echo -e "${BLUE}[4/6] 启动现有技术分析器...${NC}"
python3 -c "
import asyncio
import sys
sys.path.insert(0, '.')
from core.reasoning.prior_art_analyzer import get_prior_art_analyzer

async def start_analyzer():
    try:
        analyzer = await get_prior_art_analyzer()
        await analyzer.initialize()
        print('✅ PriorArtAnalyzer启动成功')

        # 保持服务运行
        while True:
            await asyncio.sleep(120)
            stats = analyzer.get_statistics()
            print(f'📊 Analyzer统计: {stats}')
    except Exception as e:
        print(f'❌ PriorArtAnalyzer启动失败: {e}')
        sys.exit(1)

asyncio.run(start_analyzer())
" > production/logs/prior_art_analyzer.log 2>&1 &

PRIOR_ART_PID=$!
echo $PRIOR_ART_PID > production/logs/prior_art_analyzer.pid
echo -e "${GREEN}✅ PriorArtAnalyzer启动 (PID: $PRIOR_ART_PID)${NC}"

# 启动LLM增强判断系统
echo -e "${BLUE}[5/6] 启动LLM增强判断系统...${NC}"
python3 -c "
import asyncio
import sys
sys.path.insert(0, '.')
from core.reasoning.llm_enhanced_judgment import get_llm_judgment_engine

async def start_judgment():
    try:
        engine = await get_llm_judgment_engine()
        await engine.initialize()
        print('✅ LLMEnhancedJudgment启动成功')

        # 保持服务运行
        while True:
            await asyncio.sleep(90)
            stats = engine.get_statistics()
            print(f'📊 Judgment统计: {stats}')
    except Exception as e:
        print(f'❌ LLMEnhancedJudgment启动失败: {e}')
        sys.exit(1)

asyncio.run(start_judgment())
" > production/logs/llm_enhanced_judgment.log 2>&1 &

LLM_JUDGMENT_PID=$!
echo $LLM_JUDGMENT_PID > production/logs/llm_enhanced_judgment.pid
echo -e "${GREEN}✅ LLMEnhancedJudgment启动 (PID: $LLM_JUDGMENT_PID)${NC}"

# 启动系统监控
echo -e "${BLUE}[6/6] 启动系统监控...${NC}"
python3 -c "
import time
import psutil
import json
from datetime import datetime
import sys
import os

sys.path.insert(0, '.')

def monitor_system():
    print('📊 Phase 3系统监控启动')

    while True:
        try:
            # 收集系统指标
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # 读取进程状态
            processes = []
            pid_files = [
                'production/logs/expert_rule_engine.pid',
                'production/logs/patent_rule_chain.pid',
                'production/logs/prior_art_analyzer.pid',
                'production/logs/llm_enhanced_judgment.pid'
            ]

            for pid_file in pid_files:
                if os.path.exists(pid_file):
                    try:
                        with open(pid_file, 'r') as f:
                            pid = int(f.read().strip())
                        if psutil.pid_exists(pid):
                            proc = psutil.Process(pid)
                            processes.append({
                                'name': pid_file.split('/')[-1].replace('.pid', ''),
                                'pid': pid,
                                'status': 'running',
                                'cpu': proc.cpu_percent(),
                                'modules/modules/modules/memory/memory/modules/memory/memory/modules/modules/memory/memory/memory': proc.memory_info().rss / 1024 / 1024  # MB
                            })
                        else:
                            processes.append({
                                'name': pid_file.split('/')[-1].replace('.pid', ''),
                                'pid': pid,
                                'status': 'stopped',
                                'cpu': 0,
                                'modules/modules/modules/memory/memory/modules/memory/memory/modules/modules/memory/memory/memory': 0
                            })
                    except:
                        processes.append({
                            'name': pid_file.split('/')[-1].replace('.pid', ''),
                            'pid': 'unknown',
                            'status': 'error',
                            'cpu': 0,
                            'modules/modules/modules/memory/memory/modules/memory/memory/modules/modules/memory/memory/memory': 0
                        })

            # 记录监控数据
            monitoring_data = {
                'timestamp': datetime.now().isoformat(),
                'system': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_used_gb': memory.used / 1024 / 1024 / 1024,
                    'disk_percent': disk.percent,
                    'disk_used_gb': disk.used / 1024 / 1024 / 1024
                },
                'processes': processes
            }

            with open('production/logs/monitoring.json', 'a') as f:
                json.dump(monitoring_data, f)
                f.write('\n')

            print(f'📈 系统监控 - CPU: {cpu_percent:.1f}%, 内存: {memory.percent:.1f}%, 进程: {len([p for p in processes if p[\"status\"] == \"running\"])}/4')

            time.sleep(30)  # 每30秒监控一次

        except KeyboardInterrupt:
            print('🛑 监控服务停止')
            break
        except Exception as e:
            print(f'❌ 监控错误: {e}')
            time.sleep(5)

monitor_system()
" > production/logs/monitoring.log 2>&1 &

MONITOR_PID=$!
echo $MONITOR_PID > production/logs/monitoring.pid
echo -e "${GREEN}✅ 系统监控启动 (PID: $MONITOR_PID)${NC}"

# 等待服务启动
echo ""
echo -e "${YELLOW}⏳ 等待服务启动完成...${NC}"
sleep 10

# 验证服务状态
echo -e "${BLUE}🔍 验证服务状态...${NC}"

services=(
    "$EXPERT_ENGINE_PID:ExpertRuleEngine"
    "$PATENT_RULE_ENGINE_PID:PatentRuleChainEngine"
    "$PRIOR_ART_PID:PriorArtAnalyzer"
    "$LLM_JUDGMENT_PID:LLMEnhancedJudgment"
    "$MONITOR_PID:Monitor"
)

all_running=true
for service in "${services[@]}"; do
    pid=$(echo $service | cut -d: -f1)
    name=$(echo $service | cut -d: -f2)

    if ps -p $pid > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $name 运行中 (PID: $pid)${NC}"
    else
        echo -e "${RED}❌ $name 启动失败 (PID: $pid)${NC}"
        all_running=false
    fi
done

echo ""
if $all_running; then
    echo -e "${GREEN}🎉 Phase 3专家级推理引擎启动成功！${NC}"
    echo -e "${PURPLE}🧠 Athena知识图谱系统已具备专家级AI推理能力${NC}"
    echo ""
    echo -e "${BLUE}📋 服务信息:${NC}"
    echo -e "   • ExpertRuleEngine: 专家级规则推理 (PID: $EXPERT_ENGINE_PID)"
    echo -e "   • PatentRuleChainEngine: 专利规则链推理 (PID: $PATENT_RULE_ENGINE_PID)"
    echo -e "   • PriorArtAnalyzer: 现有技术分析 (PID: $PRIOR_ART_PID)"
    echo -e "   • LLMEnhancedJudgment: LLM增强判断 (PID: $LLM_JUDGMENT_PID)"
    echo -e "   • 系统监控: 性能监控 (PID: $MONITOR_PID)"
    echo ""
    echo -e "${BLUE}📊 管理命令:${NC}"
    echo -e "   • 查看状态: ./production/dev/scripts/check_phase3_status.sh"
    echo -e "   • 查看日志: tail -f production/logs/expert_rule_engine.log"
    echo -e "   • 停止服务: ./production/dev/scripts/stop_phase3_reasoning.sh"
    echo -e "   • 重启服务: ./production/dev/scripts/restart_phase3_reasoning.sh"
    echo ""
    echo -e "${GREEN}🚀 系统已就绪，可以开始使用专家级推理功能！${NC}"
else
    echo -e "${RED}❌ 部分服务启动失败，请检查日志文件${NC}"
    echo -e "${BLUE}📋 日志目录: production/logs/${NC}"
    exit 1
fi