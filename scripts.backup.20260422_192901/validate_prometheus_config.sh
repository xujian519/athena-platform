#!/bin/bash
###############################################################################
# Prometheus配置验证脚本
# Prometheus Configuration Validation Script
#
# 用途: 验证Prometheus配置和告警规则
# 使用: ./validate_prometheus_config.sh
#
# 作者: Athena AI系统
# 版本: 2.0.0
# 创建时间: 2026-01-27
###############################################################################

set -e

# 配置变量
ATHENA_HOME=${ATHENA_HOME:-"$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"}
CONFIG_DIR="$ATHENA_HOME/config/monitoring"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 统计变量
total_checks=0
passed_checks=0
failed_checks=0

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_pass() {
    echo -e "${GREEN}[PASS]${NC} $*"
    ((passed_checks++))
    ((total_checks++))
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $*"
    ((failed_checks++))
    ((total_checks++))
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

# 检查命令是否存在
check_command() {
    if command -v "$1" &> /dev/null; then
        log_pass "命令存在: $1"
        return 0
    else
        log_fail "命令不存在: $1"
        return 1
    fi
}

# 检查文件是否存在
check_file() {
    local file=$1
    local description=$2
    
    if [ -f "$file" ]; then
        log_pass "$description 存在: $file"
        return 0
    else
        log_fail "$description 不存在: $file"
        return 1
    fi
}

# 验证Prometheus配置
validate_prometheus_config() {
    log_info "验证Prometheus配置文件..."
    
    local config_file="$CONFIG_DIR/prometheus.yml"
    
    if [ ! -f "$config_file" ]; then
        log_fail "配置文件不存在: $config_file"
        return 1
    fi
    
    if promtool check config "$config_file" 2>&1; then
        log_pass "Prometheus配置验证通过"
        return 0
    else
        log_fail "Prometheus配置验证失败"
        return 1
    fi
}

# 验证告警规则
validate_alert_rules() {
    log_info "验证告警规则文件..."
    
    local rules_file="$CONFIG_DIR/prometheus_alerts.yml"
    
    if [ ! -f "$rules_file" ]; then
        log_fail "告警规则文件不存在: $rules_file"
        return 1
    fi
    
    if promtool check rules "$rules_file" 2>&1; then
        log_pass "告警规则验证通过"
        
        # 显示规则统计
        log_info "告警规则统计:"
        echo "  规则组数: $(grep -c "^  - name:" "$rules_file" || echo 0)"
        echo "  告警规则数: $(grep -c "^    - alert:" "$rules_file" || echo 0)"
        
        return 0
    else
        log_fail "告警规则验证失败"
        return 1
    fi
}

# 检查端口可用性
check_ports() {
    log_info "检查端口可用性..."
    
    local prometheus_port=9090
    local metrics_port=9091
    local health_port=8081
    
    if lsof -i :$prometheus_port &> /dev/null; then
        log_warn "Prometheus端口 $prometheus_port 已被占用"
    else
        log_pass "Prometheus端口 $prometheus_port 可用"
    fi
    
    if lsof -i :$metrics_port &> /dev/null; then
        log_warn "Metrics端口 $metrics_port 已被占用"
    else
        log_pass "Metrics端口 $metrics_port 可用"
    fi
    
    if lsof -i :$health_port &> /dev/null; then
        log_warn "Health check端口 $health_port 已被占用"
    else
        log_pass "Health check端口 $health_port 可用"
    fi
}

# 显示配置摘要
show_config_summary() {
    log_info "配置摘要:"
    echo ""
    echo "配置目录: $CONFIG_DIR"
    echo ""
    echo "配置文件:"
    echo "  - prometheus.yml          (Prometheus主配置)"
    echo "  - prometheus_alerts.yml   (告警规则)"
    echo ""
    echo "Grafana仪表板:"
    echo "  - grafana_dashboard.json  (Grafana仪表板配置)"
    echo ""
    echo "数据目录: $ATHENA_HOME/data/prometheus"
    echo ""
}

# 显示下一步操作
show_next_steps() {
    log_info "下一步操作:"
    echo ""
    echo "1. 启动Prometheus（如果需要）:"
    echo "   ./scripts/start_prometheus.sh"
    echo ""
    echo "2. 访问Prometheus Web UI:"
    echo "   http://localhost:9090"
    echo ""
    echo "3. 查看告警规则:"
    echo "   http://localhost:9090/rules"
    echo ""
    echo "4. 查看当前告警:"
    echo "   http://localhost:9090/alerts"
    echo ""
    echo "5. 查看监控目标:"
    echo "   http://localhost:9090/targets"
    echo ""
}

# 主函数
main() {
    echo "========================================"
    echo " Prometheus配置验证"
    echo "========================================"
    echo ""
    
    # 检查promtool命令
    if ! check_command promtool; then
        log_warn "未安装promtool，跳过配置验证"
        log_warn "请安装Prometheus: brew install prometheus"
        return 1
    fi
    
    # 检查配置文件
    check_file "$CONFIG_DIR/prometheus.yml" "Prometheus配置文件" || true
    check_file "$CONFIG_DIR/prometheus_alerts.yml" "告警规则文件" || true
    check_file "$CONFIG_DIR/grafana_dashboard.json" "Grafana仪表板" || true
    
    echo ""
    
    # 验证配置
    validate_prometheus_config
    validate_alert_rules
    
    echo ""
    
    # 检查端口
    check_ports
    
    echo ""
    
    # 显示配置摘要
    show_config_summary
    
    echo ""
    echo "========================================"
    echo " 验证结果汇总"
    echo "========================================"
    echo ""
    echo "总检查数: $total_checks"
    echo "通过: $passed_checks"
    echo "失败: $failed_checks"
    echo ""
    
    if [ $failed_checks -eq 0 ]; then
        echo -e "${GREEN}所有检查通过！${NC}"
        echo ""
        show_next_steps
        return 0
    else
        echo -e "${RED}部分检查失败，请修复上述问题${NC}"
        return 1
    fi
}

# 执行主函数
main "$@"
