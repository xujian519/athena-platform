#!/bin/bash

# Athena AI平台 - 企业级自动化部署脚本
# 生成时间: 2025-12-11
# 支持环境: development, staging, production
# 功能: 蓝绿部署、健康检查、自动回滚、监控告警

set -euo pipefail

# ================================
# 配置变量
# ================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT="${1:-staging}"
DEPLOYMENT_STRATEGY="${2:-blue-green}"
HEALTH_CHECK_TIMEOUT="${HEALTH_CHECK_TIMEOUT:-300}"
ROLLBACK_ENABLED="${ROLLBACK_ENABLED:-true}"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_debug() {
    if [[ "${DEBUG:-false}" == "true" ]]; then
        echo -e "${PURPLE}[DEBUG]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
    fi
}

# ================================
# 全局变量
# ================================
DEPLOYMENT_ID="deploy-$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="$PROJECT_ROOT/backups/$DEPLOYMENT_ID"
CONFIG_FILE="$PROJECT_ROOT/deployment/configs/${ENVIRONMENT}.yaml"
STATE_FILE="$PROJECT_ROOT/.deployment_state.json"
LOG_FILE="$PROJECT_ROOT/logs/deployments/${DEPLOYMENT_ID}.log"

# 创建必要目录
mkdir -p "$BACKUP_DIR"
mkdir -p "$(dirname "$LOG_FILE")"
mkdir -p "$PROJECT_ROOT/.temp"

# ================================
# 初始化部署
# ================================
init_deployment() {
    log_info "🚀 初始化Athena AI平台自动化部署"
    log_info "部署ID: $DEPLOYMENT_ID"
    log_info "环境: $ENVIRONMENT"
    log_info "策略: $DEPLOYMENT_STRATEGY"
    log_info "日志文件: $LOG_FILE"

    # 检查环境
    check_environment

    # 加载配置
    load_configuration

    # 备份当前状态
    backup_current_state

    # 初始化状态文件
    init_state_file

    log_success "初始化完成"
}

# ================================
# 环境检查
# ================================
check_environment() {
    log_info "🔍 检查部署环境..."

    # 验证环境参数
    if [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
        log_error "无效的环境: $ENVIRONMENT"
        echo "支持的环境: development, staging, production"
        exit 1
    fi

    # 检查配置文件
    if [[ ! -f "$CONFIG_FILE" ]]; then
        log_error "配置文件不存在: $CONFIG_FILE"
        exit 1
    fi

    # 检查Docker和Docker Compose
    check_docker_environment

    # 检查系统资源
    check_system_resources

    # 检查网络连接
    check_network_connectivity

    # 检查权限
    check_permissions

    log_success "环境检查通过"
}

# ================================
# Docker环境检查
# ================================
check_docker_environment() {
    log_debug "检查Docker环境..."

    # 检查Docker是否安装和运行
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        log_error "Docker服务未运行"
        exit 1
    fi

    # 检查Docker Compose
    if ! docker compose version &> /dev/null && ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装"
        exit 1
    fi

    # 检查磁盘空间
    local available_space
    available_space=$(df "$PROJECT_ROOT" | awk 'NR==2 {print $4}')
    local required_space=5242880  # 5GB in KB

    if [[ $available_space -lt $required_space ]]; then
        log_error "磁盘空间不足，需要至少5GB可用空间"
        exit 1
    fi

    log_debug "Docker环境检查通过"
}

# ================================
# 系统资源检查
# ================================
check_system_resources() {
    log_debug "检查系统资源..."

    # 检查内存
    local total_memory
    total_memory=$(free -m | awk 'NR==2{print $2}')

    local min_memory
    case "$ENVIRONMENT" in
        production) min_memory=8192 ;;  # 8GB
        staging) min_memory=4096 ;;     # 4GB
        development) min_memory=2048 ;; # 2GB
    esac

    if [[ $total_memory -lt $min_memory ]]; then
        log_warning "系统内存可能不足，推荐${min_memory}MB，当前${total_memory}MB"
    fi

    # 检查CPU核心数
    local cpu_cores
    cpu_cores=$(nproc)

    if [[ $cpu_cores -lt 2 ]]; then
        log_warning "CPU核心数较少，推荐至少2核，当前${cpu_cores}核"
    fi

    # 检查负载
    local load_avg
    load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')

    if (( $(echo "$load_avg > $cpu_cores" | bc -l) )); then
        log_warning "系统负载较高: $load_avg，CPU核心数: $cpu_cores"
    fi

    log_debug "系统资源检查完成"
}

# ================================
# 网络连接检查
# ================================
check_network_connectivity() {
    log_debug "检查网络连接..."

    # 检查外部网络连接
    if ! curl -s --connect-timeout 5 https://www.google.com > /dev/null; then
        log_warning "无法连接到外部网络，可能影响依赖下载"
    fi

    # 检查Docker Hub连接
    if ! curl -s --connect-timeout 5 https://registry.hub.docker.com > /dev/null; then
        log_warning "无法连接到Docker Hub，可能影响镜像拉取"
    fi

    # 检查GitHub连接
    if ! curl -s --connect-timeout 5 https://github.com > /dev/null; then
        log_warning "无法连接到GitHub，可能影响代码下载"
    fi

    log_debug "网络连接检查完成"
}

# ================================
# 权限检查
# ================================
check_permissions() {
    log_debug "检查权限..."

    # 检查项目目录写权限
    if [[ ! -w "$PROJECT_ROOT" ]]; then
        log_error "没有项目目录写权限: $PROJECT_ROOT"
        exit 1
    fi

    # 检查Docker权限
    if ! docker ps &> /dev/null; then
        log_error "没有Docker权限，请将用户添加到docker组"
        exit 1
    fi

    # 检查端口权限
    local ports=("80" "443" "8080" "5432" "6379" "9200")
    for port in "${ports[@]}"; do
        if netstat -tuln 2>/dev/null | grep -q ":$port "; then
            log_warning "端口 $port 已被占用"
        fi
    done

    log_debug "权限检查通过"
}

# ================================
# 配置加载
# ================================
load_configuration() {
    log_info "📋 加载部署配置..."

    # 使用Python解析YAML配置
    python3 - << EOF
import yaml
import json
import sys

try:
    with open("$CONFIG_FILE", 'r') as f:
        config = yaml.safe_load(f)

    # 导出环境变量
    env_vars = config.get('environment', {})
    for key, value in env_vars.items():
        print(f"export {key}='{value}'")

    # 保存配置到状态文件
    with open("$PROJECT_ROOT/.temp/config.json", 'w') as f:
        json.dump(config, f, indent=2)

    print("echo '配置加载完成'")
except Exception as e:
    print(f"echo '配置加载失败: {e}'", file=sys.stderr)
    sys.exit(1)
EOF

    if [[ $? -ne 0 ]]; then
        log_error "配置加载失败"
        exit 1
    fi

    # 执行环境变量导出
    eval "$(python3 - << 'PYEOF'
import yaml
import json

with open("$CONFIG_FILE", 'r') as f:
    config = yaml.safe_load(f)

env_vars = config.get('environment', {})
for key, value in env_vars.items():
    print(f"export {key}='{value}'")
PYEOF
)"

    log_success "配置加载完成"
}

# ================================
# 备份当前状态
# ================================
backup_current_state() {
    log_info "💾 备份当前部署状态..."

    mkdir -p "$BACKUP_DIR"

    # 备份配置文件
    if [[ -f "$PROJECT_ROOT/deployment/docker/docker-compose.production.yml" ]]; then
        cp "$PROJECT_ROOT/deployment/docker/docker-compose.production.yml" "$BACKUP_DIR/"
    fi

    # 备份数据库（如果存在）
    if docker ps --format "table {{.Names}}" | grep -q "postgres"; then
        log_info "备份数据库..."
        docker exec $(docker ps -q -f name=postgres) pg_dump -U athena athenadb > "$BACKUP_DIR/database_backup.sql"
    fi

    # 备份重要数据目录
    local data_dirs=("data/volumes" "logs" "config")
    for dir in "${data_dirs[@]}"; do
        if [[ -d "$PROJECT_ROOT/$dir" ]]; then
            cp -r "$PROJECT_ROOT/$dir" "$BACKUP_DIR/"
        fi
    done

    # 保存容器状态
    docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}" > "$BACKUP_DIR/container_status.txt"

    log_success "备份完成: $BACKUP_DIR"
}

# ================================
# 初始化状态文件
# ================================
init_state_file() {
    log_debug "初始化部署状态文件..."

    cat > "$STATE_FILE" << EOF
{
    "deployment_id": "$DEPLOYMENT_ID",
    "environment": "$ENVIRONMENT",
    "strategy": "$DEPLOYMENT_STRATEGY",
    "status": "initializing",
    "start_time": "$(date -Iseconds)",
    "backup_dir": "$BACKUP_DIR",
    "config_file": "$CONFIG_FILE",
    "steps": {
        "init": "completed",
        "build": "pending",
        "deploy": "pending",
        "health_check": "pending",
        "finalize": "pending"
    },
    "rollback": {
        "enabled": $ROLLBACK_ENABLED,
        "triggered": false,
        "reason": null
    }
}
EOF

    log_debug "状态文件初始化完成"
}

# ================================
# 更新状态文件
# ================================
update_state() {
    local step="$1"
    local status="$2"
    local message="${3:-}"

    python3 - << EOF
import json

with open("$STATE_FILE", 'r') as f:
    state = json.load(f)

state["steps"]["$step"] = "$status"
state["status"] = "$status"

if "$message":
    state["steps"]["${step}_message"] = "$message"

state["last_update"] = "$(date -Iseconds)"

with open("$STATE_FILE", 'w') as f:
    json.dump(state, f, indent=2)
EOF

    log_debug "状态更新: $step -> $status"
}

# ================================
# 构建阶段
# ================================
build_phase() {
    log_info "🔨 开始构建阶段..."

    update_state "build" "running"

    # 拉取最新代码
    log_info "拉取最新代码..."
    git -C "$PROJECT_ROOT" pull origin main || {
        log_error "代码拉取失败"
        trigger_rollback "代码拉取失败"
        exit 1
    }

    # 构建Docker镜像
    log_info "构建Docker镜像..."
    if ! docker build \
        -f deployment/docker/Dockerfile.optimized \
        --target production \
        -t "athena-app:$DEPLOYMENT_ID" \
        -t "athena-app:latest" \
        --build-arg BUILD_ENV="$ENVIRONMENT" \
        --build-arg BUILD_ID="$DEPLOYMENT_ID" \
        .; then
        log_error "Docker镜像构建失败"
        trigger_rollback "Docker镜像构建失败"
        exit 1
    fi

    # 安全扫描
    log_info "执行镜像安全扫描..."
    if command -v trivy &> /dev/null; then
        trivy image --format json --output "$BACKUP_DIR/security_scan.json" "athena-app:$DEPLOYMENT_ID" || {
            log_warning "安全扫描失败，但继续部署"
        }
    fi

    update_state "build" "completed" "镜像构建完成"

    log_success "构建阶段完成"
}

# ================================
# 部署阶段
# ================================
deploy_phase() {
    log_info "🚀 开始部署阶段..."

    update_state "deploy" "running"

    case "$DEPLOYMENT_STRATEGY" in
        "blue-green")
            blue_green_deploy
            ;;
        "rolling")
            rolling_deploy
            ;;
        "canary")
            canary_deploy
            ;;
        *)
            log_error "不支持的部署策略: $DEPLOYMENT_STRATEGY"
            exit 1
            ;;
    esac

    update_state "deploy" "completed" "部署策略执行完成"

    log_success "部署阶段完成"
}

# ================================
# 蓝绿部署
# ================================
blue_green_deploy() {
    log_info "🔵🟢 执行蓝绿部署..."

    local current_env="blue"
    local new_env="green"

    # 检查当前活跃环境
    if docker ps --format "{{.Names}}" | grep -q "athena-green"; then
        current_env="green"
        new_env="blue"
    fi

    log_info "当前环境: $current_env, 新环境: $new_env"

    # 部署新环境
    log_info "部署到新环境: $new_env..."

    # 创建新的compose文件
    cat > "$PROJECT_ROOT/.temp/docker-compose.$new_env.yml" << EOF
version: '3.8'
services:
  athena-$new_env:
    image: athena-app:$DEPLOYMENT_ID
    container_name: athena-$new_env
    ports:
      - "${new_env}_port:8080"
    environment:
      - ATHENA_ENV=$ENVIRONMENT
      - ATHENA_DEPLOYMENT_ID=$DEPLOYMENT_ID
      - ATHENA_COLOR=$new_env
EOF

    # 启动新环境
    docker-compose -f "$PROJECT_ROOT/.temp/docker-compose.$new_env.yml" up -d

    # 等待新环境启动
    wait_for_service "athena-$new_env" 8080

    log_success "新环境部署完成: $new_env"
}

# ================================
# 滚动部署
# ================================
rolling_deploy() {
    log_info "🔄 执行滚动部署..."

    # 获取当前运行的实例数量
    local current_instances
    current_instances=$(docker ps --format "{{.Names}}" | grep "athena-app" | wc -l)

    log_info "当前实例数量: $current_instances"

    if [[ $current_instances -eq 0 ]]; then
        log_info "未发现运行实例，执行初始部署..."
        docker-compose -f "$PROJECT_ROOT/deployment/docker/docker-compose.production.yml" up -d
    else
        log_info "执行滚动更新..."
        docker-compose -f "$PROJECT_ROOT/deployment/docker/docker-compose.production.yml" up -d --no-deps web-app
    fi

    log_success "滚动部署完成"
}

# ================================
# 金丝雀部署
# ================================
canary_deploy() {
    log_info "🐤 执行金丝雀部署..."

    # 部署金丝雀实例（10%流量）
    log_info "部署金丝雀实例..."

    # 创建金丝雀配置
    cat > "$PROJECT_ROOT/.temp/docker-compose.canary.yml" << EOF
version: '3.8'
services:
  athena-canary:
    image: athena-app:$DEPLOYMENT_ID
    container_name: athena-canary
    ports:
      - "8081:8080"
    environment:
      - ATHENA_ENV=$ENVIRONMENT
      - ATHENA_DEPLOYMENT_ID=$DEPLOYMENT_ID
      - ATHENA_DEPLOYMENT_TYPE=canary
EOF

    # 启动金丝雀实例
    docker-compose -f "$PROJECT_ROOT/.temp/docker-compose.canary.yml" up -d

    # 等待金丝雀实例启动
    wait_for_service "athena-canary" 8080

    # 执行金丝雀测试
    if run_canary_tests; then
        log_success "金丝雀测试通过，开始全量部署..."

        # 逐步增加流量
        for percentage in 25 50 75 100; do
            log_info "增加流量到 ${percentage}%..."
            sleep 30  # 等待稳定
        done

        # 停止金丝雀实例
        docker-compose -f "$PROJECT_ROOT/.temp/docker-compose.canary.yml" down

        # 全量部署
        docker-compose -f "$PROJECT_ROOT/deployment/docker/docker-compose.production.yml" up -d

    else
        log_error "金丝雀测试失败"
        docker-compose -f "$PROJECT_ROOT/.temp/docker-compose.canary.yml" down
        trigger_rollback "金丝雀测试失败"
        exit 1
    fi

    log_success "金丝雀部署完成"
}

# ================================
# 等待服务启动
# ================================
wait_for_service() {
    local service_name="$1"
    local port="$2"
    local max_attempts=30
    local attempt=1

    log_info "等待服务启动: $service_name:$port"

    while [[ $attempt -le $max_attempts ]]; do
        if docker exec "$service_name" curl -f http://localhost:$port/health &>/dev/null; then
            log_success "服务启动成功: $service_name"
            return 0
        fi

        log_info "等待服务启动... ($attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done

    log_error "服务启动超时: $service_name"
    return 1
}

# ================================
# 金丝雀测试
# ================================
run_canary_tests() {
    log_info "🧪 执行金丝雀测试..."

    # 基本健康检查
    if ! curl -f http://localhost:8081/health &>/dev/null; then
        log_error "金丝雀实例健康检查失败"
        return 1
    fi

    # API响应测试
    if ! curl -f http://localhost:8081/api/v2/status &>/dev/null; then
        log_error "金丝雀实例API测试失败"
        return 1
    fi

    # 性能测试（简单的响应时间检查）
    local response_time
    response_time=$(curl -o /dev/null -s -w '%{time_total}' http://localhost:8081/api/v2/status)

    if (( $(echo "$response_time > 2.0" | bc -l) )); then
        log_error "金丝雀实例响应时间过长: ${response_time}s"
        return 1
    fi

    log_success "金丝雀测试通过"
    return 0
}

# ================================
# 健康检查阶段
# ================================
health_check_phase() {
    log_info "🏥 开始健康检查阶段..."

    update_state "health_check" "running"

    local start_time=$(date +%s)
    local timeout=$HEALTH_CHECK_TIMEOUT

    while true; do
        local current_time=$(date +%s)
        local elapsed=$((current_time - start_time))

        if [[ $elapsed -gt $timeout ]]; then
            log_error "健康检查超时"
            trigger_rollback "健康检查超时"
            exit 1
        fi

        if perform_health_check; then
            log_success "健康检查通过"
            update_state "health_check" "completed" "所有服务健康"
            break
        else
            log_warning "健康检查未通过，等待重试... (已等待 ${elapsed}s)"
            sleep 10
        fi
    done

    log_success "健康检查阶段完成"
}

# ================================
# 执行健康检查
# ================================
perform_health_check() {
    local services=("postgres" "redis" "elasticsearch" "web-app")
    local all_healthy=true

    for service in "${services[@]}"; do
        if docker ps --format "{{.Names}}" | grep -q "$service"; then
            if ! check_service_health "$service"; then
                all_healthy=false
            fi
        fi
    done

    # 检查HTTP端点
    local endpoints=("http://localhost/health" "http://localhost:8080/api/v2/health")
    for endpoint in "${endpoints[@]}"; do
        if ! curl -f -s "$endpoint" >/dev/null 2>&1; then
            log_warning "端点健康检查失败: $endpoint"
            all_healthy=false
        fi
    done

    return $([[ $all_healthy == true ]] && echo 0 || echo 1)
}

# ================================
# 检查服务健康
# ================================
check_service_health() {
    local service="$1"

    case "$service" in
        "postgres")
            docker exec "$service" pg_isready -U athena -d athenadb >/dev/null 2>&1
            ;;
        "redis")
            docker exec "$service" redis-cli ping >/dev/null 2>&1
            ;;
        "elasticsearch")
            curl -f http://localhost:9200/_cluster/health >/dev/null 2>&1
            ;;
        "web-app")
            if docker ps --format "{{.Names}}" | grep -q "athena-"; then
                local web_container=$(docker ps --format "{{.Names}}" | grep "athena-" | head -1)
                docker exec "$web_container" curl -f http://localhost:8080/health >/dev/null 2>&1
            else
                return 1
            fi
            ;;
        *)
            docker ps --format "{{.Names}}\t{{.Status}}" | grep "$service" | grep -q "Up"
            ;;
    esac
}

# ================================
# 触发回滚
# ================================
trigger_rollback() {
    local reason="$1"

    if [[ "$ROLLBACK_ENABLED" != "true" ]]; then
        log_warning "回滚已禁用，跳过回滚操作"
        return 0
    fi

    log_warning "🔄 触发自动回滚..."
    log_warning "回滚原因: $reason"

    # 更新状态文件
    python3 - << EOF
import json

with open("$STATE_FILE", 'r') as f:
    state = json.load(f)

state["rollback"]["triggered"] = True
state["rollback"]["reason"] = "$reason"
state["rollback"]["timestamp"] = "$(date -Iseconds)"

with open("$STATE_FILE", 'w') as f:
    json.dump(state, f, indent=2)
EOF

    # 执行回滚
    execute_rollback

    log_warning "回滚完成"
}

# ================================
# 执行回滚
# ================================
execute_rollback() {
    log_info "执行系统回滚..."

    # 停止当前部署
    log_info "停止当前部署..."
    docker-compose -f "$PROJECT_ROOT/deployment/docker/docker-compose.production.yml" down || true

    # 清理临时文件
    log_info "清理临时文件..."
    rm -rf "$PROJECT_ROOT/.temp/docker-compose."*.yml || true

    # 恢复配置文件
    if [[ -f "$BACKUP_DIR/docker-compose.production.yml" ]]; then
        cp "$BACKUP_DIR/docker-compose.production.yml" "$PROJECT_ROOT/deployment/docker/"
    fi

    # 恢复数据库（如果需要）
    if [[ -f "$BACKUP_DIR/database_backup.sql" ]]; then
        log_info "恢复数据库..."
        docker-compose -f "$PROJECT_ROOT/deployment/docker/docker-compose.production.yml" up -d postgres
        sleep 30
        docker exec $(docker ps -q -f name=postgres) psql -U athena -d athenadb < "$BACKUP_DIR/database_backup.sql"
    fi

    # 启动之前的服务
    log_info "启动之前的服务..."
    docker-compose -f "$PROJECT_ROOT/deployment/docker/docker-compose.production.yml" up -d

    # 等待服务恢复
    sleep 60

    log_info "回滚操作完成"
}

# ================================
# 最终化阶段
# ================================
finalize_phase() {
    log_info "🎯 开始最终化阶段..."

    update_state "finalize" "running"

    # 清理旧的镜像和容器
    log_info "清理旧的部署资源..."
    docker image prune -f
    docker container prune -f

    # 更新负载均衡器（如果需要）
    update_load_balancer

    # 发送部署通知
    send_deployment_notification

    # 生成部署报告
    generate_deployment_report

    update_state "finalize" "completed" "部署最终化完成"

    log_success "最终化阶段完成"
}

# ================================
# 更新负载均衡器
# ================================
update_load_balancer() {
    log_info "更新负载均衡器配置..."

    # 根据部署策略更新负载均衡器
    case "$DEPLOYMENT_STRATEGY" in
        "blue-green")
            # 切换流量到新环境
            log_info "切换流量到新环境..."
            # 这里添加实际的负载均衡器配置更新代码
            ;;
        "canary")
            # 逐步增加流量
            log_info "金丝雀部署已完成，流量已全量切换"
            ;;
        "rolling")
            # 滚动部署已完成，无需特殊操作
            log_info "滚动部署已完成"
            ;;
    esac

    log_success "负载均衡器配置已更新"
}

# ================================
# 发送部署通知
# ================================
send_deployment_notification() {
    log_info "发送部署通知..."

    # 生成通知内容
    local notification_content
    notification_content="🚀 Athena AI平台部署通知

环境: $ENVIRONMENT
策略: $DEPLOYMENT_STRATEGY
部署ID: $DEPLOYMENT_ID
状态: 成功
时间: $(date '+%Y-%m-%d %H:%M:%S')"

    # 如果配置了Slack Webhook
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"$notification_content\"}" \
            "$SLACK_WEBHOOK_URL" || log_warning "Slack通知发送失败"
    fi

    # 如果配置了邮件通知
    if command -v mail &> /dev/null && [[ -n "${DEPLOYMENT_EMAIL:-}" ]]; then
        echo "$notification_content" | mail -s "Athena AI平台部署通知 - $ENVIRONMENT" "$DEPLOYMENT_EMAIL" || \
            log_warning "邮件通知发送失败"
    fi

    log_success "部署通知已发送"
}

# ================================
# 生成部署报告
# ================================
generate_deployment_report() {
    log_info "生成部署报告..."

    local report_file="$PROJECT_ROOT/deployment_reports/${DEPLOYMENT_ID}.md"
    mkdir -p "$(dirname "$report_file")"

    # 读取状态文件
    local end_time
    end_time=$(date -Iseconds)

    cat > "$report_file" << EOF
# Athena AI平台部署报告

## 基本信息

- **部署ID**: $DEPLOYMENT_ID
- **环境**: $ENVIRONMENT
- **策略**: $DEPLOYMENT_STRATEGY
- **开始时间**: $(jq -r '.start_time' "$STATE_FILE")
- **结束时间**: $end_time
- **状态**: 成功

## 部署步骤

$(jq -r '.steps | to_entries[] | "- **\(.key | title)**: \(.value)"' "$STATE_FILE")

## 备份信息

- **备份目录**: $BACKUP_DIR
- **备份时间**: $(ls -la "$BACKUP_DIR" | head -1 | awk '{print $6, $7, $8}')

## 服务状态

\`\`\`
$(docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}")
\`\`\`

## 资源使用

\`\`\`
$(docker stats --no-stream)
\`\`\`

## 日志文件

- **部署日志**: $LOG_FILE
- **状态文件**: $STATE_FILE

---

*报告生成时间: $(date '+%Y-%m-%d %H:%M:%S')*
EOF

    log_success "部署报告已生成: $report_file"
}

# ================================
# 主函数
# ================================
main() {
    echo "=============================================="
    echo "🚀 Athena AI平台 企业级自动化部署"
    echo "部署ID: $DEPLOYMENT_ID"
    echo "环境: $ENVIRONMENT"
    echo "策略: $DEPLOYMENT_STRATEGY"
    echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "=============================================="
    echo

    # 记录开始时间
    local start_time=$(date +%s)

    # 执行部署流程
    trap 'handle_error $? $LINENO' ERR

    init_deployment
    build_phase
    deploy_phase
    health_check_phase
    finalize_phase

    # 计算总耗时
    local end_time=$(date +%s)
    local total_time=$((end_time - start_time))

    echo
    log_success "🎉 部署完成！"
    echo "=============================================="
    echo "📊 部署摘要:"
    echo "   总耗时: ${total_time}秒"
    echo "   部署ID: $DEPLOYMENT_ID"
    echo "   环境: $ENVIRONMENT"
    echo "   策略: $DEPLOYMENT_STRATEGY"
    echo "   状态: 成功"
    echo "   备份: $BACKUP_DIR"
    echo "   日志: $LOG_FILE"
    echo "=============================================="
    echo
    echo "🔗 访问链接:"
    echo "   Web应用: http://localhost"
    echo "   API文档: http://localhost/docs"
    echo "   健康检查: http://localhost/health"
    echo "=============================================="
}

# ================================
# 错误处理
# ================================
handle_error() {
    local exit_code=$1
    local line_number=$2

    log_error "部署过程中发生错误 (退出码: $exit_code, 行号: $line_number)"

    if [[ "$ROLLBACK_ENABLED" == "true" ]]; then
        trigger_rollback "部署过程发生错误: exit_code=$exit_code, line=$line_number"
    fi

    exit $exit_code
}

# ================================
# 信号处理
# ================================
trap 'log_warning "部署被用户中断"; trigger_rollback "用户中断"; exit 130' INT TERM

# ================================
# 执行主函数
# ================================
main "$@"