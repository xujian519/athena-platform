#!/bin/bash
# ============================================================================
# Athena服务启动脚本
# 启动所有Phase 1和Phase 2优化后的服务
#
# 作者: Athena平台团队
# 创建时间: 2025-12-29
# 版本: v1.0.0
# ============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 项目根目录
PROJECT_ROOT="/Users/xujian/Athena工作平台"
cd "$PROJECT_ROOT"

# 日志函数
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_section() { echo -e "\n${CYAN}========== $1 ==========${NC}\n"; }

# PID文件目录
PID_DIR="$PROJECT_ROOT/production/pids"
mkdir -p "$PID_DIR"

# 日志目录
LOG_DIR="$PROJECT_ROOT/production/logs"
mkdir -p "$LOG_DIR"

# ============================================================================
# 服务管理函数
# ============================================================================

# 检查服务是否运行
is_running() {
    local service_name=$1
    local pid_file="$PID_DIR/${service_name}.pid"

    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$pid_file"
        fi
    fi
    return 1
}

# 启动服务
start_service() {
    local service_name=$1
    local start_command=$2
    local pid_file="$PID_DIR/${service_name}.pid"
    local log_file="$LOG_DIR/${service_name}.log"

    if is_running "$service_name"; then
        log_warning "$service_name 已在运行中"
        return 0
    fi

    log_info "启动 $service_name..."

    # 启动服务并记录PID
    nohup bash -c "$start_command" > "$log_file" 2>&1 &
    local pid=$!
    echo $pid > "$pid_file"

    # 等待服务启动
    sleep 2

    # 验证服务是否启动成功
    if ps -p "$pid" > /dev/null 2>&1; then
        log_success "✓ $service_name 已启动 (PID: $pid)"
        return 0
    else
        log_error "✗ $service_name 启动失败"
        rm -f "$pid_file"
        return 1
    fi
}

# 停止服务
stop_service() {
    local service_name=$1
    local pid_file="$PID_DIR/${service_name}.pid"

    if [ ! -f "$pid_file" ]; then
        log_warning "$service_name 未运行"
        return 0
    fi

    local pid=$(cat "$pid_file")

    log_info "停止 $service_name (PID: $pid)..."

    # 优雅停止
    kill "$pid" 2>/dev/null || true

    # 等待进程结束
    local count=0
    while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt 30 ]; do
        sleep 1
        count=$((count + 1))
    done

    # 如果还没停止，强制杀死
    if ps -p "$pid" > /dev/null 2>&1; then
        kill -9 "$pid" 2>/dev/null || true
    fi

    rm -f "$pid_file"
    log_success "✓ $service_name 已停止"
}

# ============================================================================
# 服务启动函数
# ============================================================================

# 启动监控系统
start_monitoring_system() {
    log_section "启动监控系统"

    start_service "athena-monitoring" "
        export PYTHONPATH=$PROJECT_ROOT
        export ATHENA_ENV=production

        python3.11 -c '
import sys
sys.path.insert(0, \"$PROJECT_ROOT\")

from core.monitoring.full_link_monitoring_system import get_monitoring_system
from core.monitoring.enhanced_alerting_system import get_alerting_system
import time
import signal
import logging

logging.basicConfig(
    level=logging.INFO,
    format=\"%(asctime)s - %(name)s - %(levelname)s - %(message)s\"
)

logger = logging.getLogger(__name__)

running = True

def signal_handler(signum, frame):
    global running
    logger.info(\"收到停止信号，正在关闭...\")
    running = False

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

try:
    # 初始化系统
    monitor = get_monitoring_system()
    alerting = get_alerting_system()

    logger.info(\"✅ 监控系统已启动\")

    # 持续运行
    while running:
        time.sleep(1)

except Exception as e:
    logger.error(f\"监控系统错误: {e}\")
    sys.exit(1)
finally:
    logger.info(\"监控系统已关闭\")
'
    "
}

# 启动NLP服务
start_nlp_service() {
    log_section "启动NLP服务"

    start_service "athena-nlp" "
        export PYTHONPATH=$PROJECT_ROOT
        export ATHENA_ENV=production

        python3.11 -c '
import sys
sys.path.insert(0, \"$PROJECT_ROOT\")

from core.nlp.xiaonuo_enhanced_ner import XiaonuoEnhancedNER
from core.nlp.bert_semantic_intent_classifier import BERTSemanticIntentClassifier
from core.performance.batch_processor import BatchProcessor
from sentence_transformers import SentenceTransformer
import time
import signal
import logging

logging.basicConfig(
    level=logging.INFO,
    format=\"%(asctime)s - %(name)s - %(levelname)s - %(message)s\"
)

logger = logging.getLogger(__name__)

running = True

def signal_handler(signum, frame):
    global running
    logger.info(\"收到停止信号，正在关闭...\")
    running = False

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

try:
    # 加载NER模型
    logger.info(\"加载NER模型...\")
    ner = XiaonuoEnhancedNER()

    # 加载意图分类器
    logger.info(\"加载意图分类器...\")
    intent_classifier = BERTSemanticIntentClassifier()

    # 加载批处理器
    logger.info(\"初始化批处理器...\")
    model = SentenceTransformer(\"/Users/xujian/Athena工作平台/models/converted/BAAI/bge-m3\")
    batch_processor = BatchProcessor(model=model, batch_size=16, device=\"mps\")

    logger.info(\"✅ NLP服务已启动\")

    # 持续运行
    while running:
        time.sleep(1)

except Exception as e:
    logger.error(f\"NLP服务错误: {e}\")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    logger.info(\"NLP服务已关闭\")
'
    "
}

# 启动缓存服务
start_cache_service() {
    log_section "启动缓存服务"

    start_service "athena-cache" "
        export PYTHONPATH=$PROJECT_ROOT
        export ATHENA_ENV=production

        python3.11 -c '
import sys
sys.path.insert(0, \"$PROJECT_ROOT\")

from core.performance.three_tier_cache import get_cache
from core.cache_manager import AthenaCacheManager
import time
import signal
import logging

logging.basicConfig(
    level=logging.INFO,
    format=\"%(asctime)s - %(name)s - %(levelname)s - %(message)s\"
)

logger = logging.getLogger(__name__)

running = True

def signal_handler(signum, frame):
    global running
    logger.info(\"收到停止信号，正在关闭...\")
    running = False

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

try:
    # 初始化三级缓存
    logger.info(\"初始化三级缓存...\")
    cache = get_cache()

    # 初始化Redis缓存
    logger.info(\"初始化Redis缓存...\")
    redis_cache = AthenaCacheManager()

    logger.info(\"✅ 缓存服务已启动\")

    # 持续运行
    while running:
        time.sleep(1)

except Exception as e:
    logger.error(f\"缓存服务错误: {e}\")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    logger.info(\"缓存服务已关闭\")
'
    "
}

# 启动智能体服务
start_agent_service() {
    log_section "启动智能体服务"

    start_service "athena-agent" "
        export PYTHONPATH=$PROJECT_ROOT
        export ATHENA_ENV=production

        # 加载环境配置
        if [ -f \"$PROJECT_ROOT/production/config/production/.env\" ]; then
            export \$(grep -v '^#' \"$PROJECT_ROOT/production/config/production/.env\" | xargs)
        fi

        python3.11 -c '
import sys
sys.path.insert(0, \"'$PROJECT_ROOT'\")

from core.agent import AthenaAgent, AgentProfile, AgentType
from core.monitoring.full_link_monitoring_system import get_monitoring_system
import time
import signal
import logging

logging.basicConfig(
    level=logging.INFO,
    format=\"%(asctime)s - %(name)s - %(levelname)s - %(message)s\"
)

logger = logging.getLogger(__name__)

running = True

def signal_handler(signum, frame):
    global running
    logger.info(\"收到停止信号，正在关闭...\")
    running = False

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

try:
    # 初始化监控系统
    monitor = get_monitoring_system()

    # 创建智能体配置
    logger.info(\"创建智能体配置...\")
    from datetime import datetime
    profile = AgentProfile(
        agent_id=\"athena-agent-001\",
        agent_type=AgentType.ATHENA,
        name=\"Athena智能体\",
        description=\"Athena工作平台的智慧女神，负责系统协调和任务编排\",
        personality={
            \"role\": \"orchestration\",
            \"style\": \"wise_strategic\"
        },
        capabilities=[
            \"search\",
            \"analysis\",
            \"execution\",
            \"orchestration\",
            \"collaboration\"
        ],
        preferences={
            \"max_concurrent_tasks\": 5,
            \"timeout\": 300,
            \"enable_monitoring\": True
        },
        created_at=datetime.now()
    )

    # 创建智能体
    logger.info(\"初始化Athena智能体...\")
    agent = AthenaAgent(config={\"profile\": profile})

    logger.info(\"✅ 智能体服务已启动\")

    # 持续运行
    while running:
        time.sleep(1)

except Exception as e:
    logger.error(f\"智能体服务错误: {e}\")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    logger.info(\"智能体服务已关闭\")
'
    "
}

# ============================================================================
# 主流程
# ============================================================================

show_usage() {
    cat << EOF
Athena服务启动脚本

用法:
    $0 [command]

命令:
    start       启动所有服务
    stop        停止所有服务
    restart     重启所有服务
    status      查看服务状态
    help        显示帮助信息

服务列表:
    - athena-monitoring    监控系统
    - athena-nlp          NLP服务
    - athena-cache        缓存服务
    - athena-agent        智能体服务
EOF
}

# 启动所有服务
start_all() {
    log_section "启动Athena服务"
    log_info "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"

    start_monitoring_system
    start_nlp_service
    start_cache_service
    start_agent_service

    log_section "服务启动完成"
    log_success "🎉 所有Athena服务已启动!"
    log_info "查看日志: tail -f $LOG_DIR/<service>.log"
    log_info "查看状态: $0 status"
}

# 停止所有服务
stop_all() {
    log_section "停止Athena服务"

    stop_service "athena-agent"
    stop_service "athena-cache"
    stop_service "athena-nlp"
    stop_service "athena-monitoring"

    log_success "✓ 所有Athena服务已停止"
}

# 重启所有服务
restart_all() {
    log_info "重启所有服务..."
    stop_all
    sleep 2
    start_all
}

# 查看服务状态
show_status() {
    log_section "Athena服务状态"

    services=("athena-monitoring" "athena-nlp" "athena-cache" "athena-agent")

    for service in "${services[@]}"; do
        if is_running "$service"; then
            local pid=$(cat "$PID_DIR/${service}.pid")
            log_success "✓ $service: 运行中 (PID: $pid)"
        else
            log_error "✗ $service: 未运行"
        fi
    done

    echo ""
    log_info "日志文件位置: $LOG_DIR/"
    log_info "PID文件位置: $PID_DIR/"
}

# ============================================================================
# 命令处理
# ============================================================================

case "${1:-start}" in
    start)
        start_all
        ;;
    stop)
        stop_all
        ;;
    restart)
        restart_all
        ;;
    status)
        show_status
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        log_error "未知命令: $1"
        show_usage
        exit 1
        ;;
esac
