#!/bin/bash
# 高可用性和故障转移配置脚本
# High Availability and Failover Configuration for Athena Production

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
CLUSTER_NAME="athena-prod"
NODES=(
    "master:172.20.0.10:MASTER"
    "node1:172.20.0.11:BACKUP"
    "node2:172.20.0.12:BACKUP"
)
VIRTUAL_IP="172.20.0.100"
INTERFACES=("eth0" "eth0" "eth0")
SERVICES=("api-gateway:8020" "dolphin-parser:8013" "glm-vision:8091" "multimodal-processor:8012" "xiao-nuo-control:9001" "athena-platform:9000" "platform-monitor:9090")

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查系统要求
check_requirements() {
    log_info "检查系统要求..."

    # 检查keepalived
    if ! command -v keepalived &> /dev/null; then
        log_error "Keepalived未安装，请先安装"
        echo "Ubuntu/Debian: sudo apt-get install keepalived"
        echo "CentOS/RHEL: sudo yum install keepalived"
        exit 1
    fi

    # 检查ipvsadm
    if ! command -v ipvsadm &> /dev/null; then
        log_warning "IPVS管理工具未安装，部分功能可能受限"
    fi

    # 检查网络接口
    for interface in "${INTERFACES[@]}"; do
        if ! ip link show "$interface" &> /dev/null; then
            log_warning "网络接口 $interface 不存在，请检查配置"
        fi
    done

    log_success "系统要求检查完成"
}

# 创建Keepalived配置
create_keepalived_configs() {
    log_info "创建Keepalived高可用配置..."

    for i in "${!NODES[@]}"; do
        node_info=(${NODES[i]//:/ })
        node_name=${node_info[0]}
        node_ip=${node_info[1]}
        node_role=${node_info[2]}
        interface=${INTERFACES[i]}

        config_file="/etc/keepalived/keepalived_${node_name}.conf"

        case $node_role in
            "MASTER")
                priority=150
                state="MASTER"
                ;;
            "BACKUP")
                priority=$((100 - i * 10))
                state="BACKUP"
                ;;
        esac

        cat > "$config_file" << EOF
# Keepalived配置 - ${node_name} (${state})
# Athena多模态文件系统生产环境

global_defs {
    router_id ${node_name}
    script_user root
    enable_script_security
    vrrp_skip_check_adv_addr
    vrrp_strict
    vrrp_garp_interval 0
    vrrp_gna_interval 0
}

# 健康检查脚本
vrrp_script chk_nginx {
    script "/usr/local/bin/check_nginx.sh"
    interval 2
    weight -20
    fall 3
    rise 2
    timeout 2
}

vrrp_script chk_services {
    script "/usr/local/bin/check_services.sh"
    interval 5
    weight -10
    fall 2
    rise 1
    timeout 3
}

# 虚拟路由器实例
vrrp_instance VI_1 {
    state ${state}
    interface ${interface}
    virtual_router_id 51
    priority ${priority}
    advert_int 1

    authentication {
        auth_type PASS
        auth_pass athena2024
    }

    virtual_ipaddress {
        ${VIRTUAL_IP}/24 dev ${interface}
    }

    track_script {
        chk_nginx
        chk_services
    }

    # 状态切换通知
    notify_master "/etc/keepalived/notify.sh ${node_name} master"
    notify_backup "/etc/keepalived/notify.sh ${node_name} backup"
    notify_fault "/etc/keepalived/notify.sh ${node_name} fault"

    # 预占模式
    preempt_delay 30
}

# API服务虚拟路由器
vrrp_instance VI_API {
    state ${state}
    interface ${interface}
    virtual_router_id 52
    priority ${priority}
    advert_int 1

    authentication {
        auth_type PASS
        auth_pass athena_api_2024
    }

    virtual_ipaddress {
        172.20.0.200/24 dev ${interface}
    }

    track_script {
        chk_nginx
        chk_services
    }

    notify_master "/etc/keepalived/notify.sh ${node_name} master_api"
    notify_backup "/etc/keepalived/notify.sh ${node_name} backup_api"
}
EOF

        log_success "创建 $config_file 完成"
    done
}

# 创建健康检查脚本
create_health_check_scripts() {
    log_info "创建健康检查脚本..."

    # Nginx检查脚本
    cat > "/usr/local/bin/check_nginx.sh" << 'EOF'
#!/bin/bash
# Nginx服务健康检查

# 检查nginx进程
if ! pgrep nginx > /dev/null; then
    echo "ERROR: Nginx进程未运行"
    exit 1
fi

# 检查nginx端口
if ! nc -z localhost 80; then
    echo "ERROR: Nginx HTTP端口未监听"
    exit 1
fi

if ! nc -z localhost 443; then
    echo "ERROR: Nginx HTTPS端口未监听"
    exit 1
fi

# 检查nginx响应
if ! curl -f http://localhost/health >/dev/null 2>&1; then
    echo "ERROR: Nginx健康检查失败"
    exit 1
fi

echo "OK: Nginx服务正常"
exit 0
EOF

    # 服务检查脚本
    cat > "/usr/local/bin/check_services.sh" << 'EOF'
#!/bin/bash
# 核心服务健康检查

SERVICES=("8020" "8013" "8091" "8012" "9001" "9000" "9090")
FAILED_COUNT=0

for port in "${SERVICES[@]}"; do
    if ! nc -z localhost $port; then
        echo "WARNING: 端口 $port 服务未运行"
        FAILED_COUNT=$((FAILED_COUNT + 1))
    fi
done

# 允许最多2个服务失败
if [ $FAILED_COUNT -gt 2 ]; then
    echo "ERROR: 过多服务失败 ($FAILED_COUNT)"
    exit 1
fi

echo "OK: 服务检查通过 (失败: $FAILED_COUNT)"
exit 0
EOF

    # 数据库连接检查脚本
    cat > "/usr/local/bin/check_database.sh" << 'EOF'
#!/bin/bash
# 数据库连接检查

DB_HOST="localhost"
DB_PORT="5432"
DB_USER="athena_user"
DB_NAME="athena_production"

# 检查数据库连接
if ! pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER; then
    echo "ERROR: 数据库连接失败"
    exit 1
fi

# 检查数据库响应
if ! PGPASSWORD="" psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT 1;" >/dev/null 2>&1; then
    echo "ERROR: 数据库查询失败"
    exit 1
fi

echo "OK: 数据库连接正常"
exit 0
EOF

    # Redis连接检查脚本
    cat > "/usr/local/bin/check_redis.sh" << 'EOF'
#!/bin/bash
# Redis连接检查

REDIS_HOST="localhost"
REDIS_PORT="6379"

# 检查Redis连接
if ! redis-cli -h $REDIS_HOST -p $REDIS_PORT ping | grep -q PONG; then
    echo "ERROR: Redis连接失败"
    exit 1
fi

echo "OK: Redis连接正常"
exit 0
EOF

    # 设置执行权限
    chmod +x /usr/local/bin/check_*.sh

    log_success "健康检查脚本创建完成"
}

# 创建状态通知脚本
create_notification_scripts() {
    log_info "创建状态通知脚本..."

    cat > "/etc/keepalived/notify.sh" << 'EOF'
#!/bin/bash
# Keepalived状态通知脚本

NODE_NAME=$1
TYPE=$2

LOG_FILE="/var/log/keepalived.log"
ALERT_URL="http://localhost:9090/alerts"

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$NODE_NAME] $1" >> $LOG_FILE
}

send_alert() {
    local level=$1
    local message=$2

    curl -X POST -H "Content-Type: application/json" \
        -d "{\"level\": \"$level\", \"message\": \"$message\", \"node\": \"$NODE_NAME\", \"timestamp\": \"$(date -Iseconds)\"}" \
        $ALERT_URL 2>/dev/null || true
}

case $TYPE in
    master)
        log_message "切换到MASTER状态"
        send_alert "INFO" "节点切换到MASTER状态"

        # 启动所有服务
        systemctl start nginx
        systemctl start keepalived

        # 通知其他系统
        curl -X POST http://localhost:9001/api/vip/change \
            -d "{\"vip\": \"172.20.0.100\", \"state\": \"master\", \"node\": \"$NODE_NAME\"}" \
            -H "Content-Type: application/json" 2>/dev/null || true
        ;;

    backup)
        log_message "切换到BACKUP状态"
        send_alert "WARNING" "节点切换到BACKUP状态"

        # 可选：在backup状态下也保持服务运行
        # systemctl start nginx
        ;;

    fault)
        log_message "切换到FAULT状态"
        send_alert "CRITICAL" "节点切换到FAULT状态"

        # 停止服务
        systemctl stop nginx
        ;;

    master_api)
        log_message "API VIP切换到MASTER状态"
        send_alert "INFO" "API VIP切换到MASTER状态"
        ;;

    backup_api)
        log_message "API VIP切换到BACKUP状态"
        send_alert "WARNING" "API VIP切换到BACKUP状态"
        ;;

    *)
        log_message "未知状态: $TYPE"
        send_alert "WARNING" "Keepalived未知状态: $TYPE"
        ;;
esac
EOF

    chmod +x /etc/keepalived/notify.sh

    log_success "状态通知脚本创建完成"
}

# 创建故障转移配置
create_failover_config() {
    log_info "创建故障转移配置..."

    cat > "/etc/keepalived/failover.conf" << 'EOF'
# 故障转移配置

# 自动故障转移脚本
vrrp_script auto_failover {
    script "/usr/local/bin/auto_failover.sh"
    interval 10
    weight 0
    timeout 5
}

# 故障转移规则
vrrp_instance VI_FAILOVER {
    state BACKUP
    interface eth0
    virtual_router_id 53
    priority 100
    advert_int 1

    authentication {
        auth_type PASS
        auth_pass failover2024
    }

    track_script {
        auto_failover
    }

    notify_master "/etc/keepalived/failover.sh master"
    notify_backup "/etc/keepalived/failover.sh backup"
}
EOF

    # 自动故障转移脚本
    cat > "/usr/local/bin/auto_failover.sh" << 'EOF'
#!/bin/bash
# 自动故障转移脚本

ALERT_THRESHOLD=3
FAILURE_COUNT_FILE="/tmp/failover_count"
CURRENT_FAILURES=0

# 读取当前失败次数
if [ -f "$FAILURE_COUNT_FILE" ]; then
    CURRENT_FAILURES=$(cat "$FAILURE_COUNT_FILE")
fi

# 检查关键服务
critical_services=("nginx" "postgresql" "redis")
failed_services=0

for service in "${critical_services[@]}"; do
    if ! systemctl is-active --quiet $service; then
        echo "服务 $service 未运行"
        failed_services=$((failed_services + 1))
    fi
done

# 检查网络连接
if ! ping -c 1 8.8.8.8 >/dev/null 2>&1; then
    echo "网络连接失败"
    failed_services=$((failed_services + 1))
fi

# 更新失败计数
if [ $failed_services -gt 0 ]; then
    CURRENT_FAILURES=$((CURRENT_FAILURES + 1))
    echo $CURRENT_FAILURES > "$FAILURE_COUNT_FILE"
else
    CURRENT_FAILURES=0
    echo $CURRENT_FAILURES > "$FAILURE_COUNT_FILE"
fi

# 判断是否需要故障转移
if [ $CURRENT_FAILURES -ge $ALERT_THRESHOLD ]; then
    echo "需要故障转移 (失败次数: $CURRENT_FAILURES)"
    exit 1
else
    echo "服务正常 (失败次数: $CURRENT_FAILURES)"
    exit 0
fi
EOF

    chmod +x /usr/local/bin/auto_failover.sh

    log_success "故障转移配置创建完成"
}

# 创建监控和日志配置
create_monitoring_config() {
    log_info "创建监控和日志配置..."

    # 创建日志轮转配置
    cat > "/etc/logrotate.d/keepalived" << 'EOF'
/var/log/keepalived.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        systemctl reload keepalived >/dev/null 2>&1 || true
    endscript
}
EOF

    # 创建systemd服务监控
    cat > "/etc/systemd/system/keepalived-monitor.service" << 'EOF'
[Unit]
Description=Keepalived Monitoring Service
After=network.target keepalived.service
Requires=keepalived.service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/monitor_keepalived.sh
User=root
Group=root

[Install]
WantedBy=multi-user.target
EOF

    # 监控脚本
    cat > "/usr/local/bin/monitor_keepalived.sh" << 'EOF'
#!/bin/bash
# Keepalived监控脚本

LOG_FILE="/var/log/keepalived_monitor.log"

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" >> $LOG_FILE
}

# 检查Keepalived状态
if ! systemctl is-active --quiet keepalived; then
    log_message "ERROR: Keepalived服务未运行"
    systemctl start keepalived
    log_message "INFO: 已尝试启动Keepalived服务"
fi

# 检查虚拟IP
if ! ip addr show | grep -q "172.20.0.100"; then
    log_message "WARNING: 虚拟IP未绑定"
else
    log_message "INFO: 虚拟IP绑定正常"
fi

# 发送监控指标到Prometheus
curl -X POST -H "Content-Type: text/plain" \
    --data-binary "# HELP keepalived_status Keepalived service status (1=active, 0=inactive)\n# TYPE keepalived_status gauge\nkeepalived_status $(systemctl is-active --quiet keepalived && echo 1 || echo 0)\n" \
    http://localhost:9090/metrics/job/keepalived 2>/dev/null || true

exit 0
EOF

    chmod +x /usr/local/bin/monitor_keepalived.sh

    # 启用监控服务
    systemctl enable keepalived-monitor
    systemctl daemon-reload

    log_success "监控配置创建完成"
}

# 创建应急恢复脚本
create_recovery_scripts() {
    log_info "创建应急恢复脚本..."

    # 主恢复脚本
    cat > "/Users/xujian/Athena工作平台/scripts/emergency_recovery.sh" << 'EOF'
#!/bin/bash
# 应急恢复脚本

log_info() {
    echo -e "\033[0;34m[INFO]\033[0m $1"
}

log_error() {
    echo -e "\033[0;31m[ERROR]\033[0m $1"
}

log_success() {
    echo -e "\033[0;32m[SUCCESS]\033[0m $1"
}

# 恢复Nginx
recover_nginx() {
    log_info "恢复Nginx服务..."

    # 停止现有进程
    pkill -f nginx || true
    sleep 2

    # 检查配置
    if nginx -t; then
        systemctl start nginx
        if systemctl is-active --quiet nginx; then
            log_success "Nginx恢复成功"
            return 0
        else
            log_error "Nginx启动失败"
            return 1
        fi
    else
        log_error "Nginx配置验证失败"
        return 1
    fi
}

# 恢复Keepalived
recover_keepalived() {
    log_info "恢复Keepalived服务..."

    # 停止现有进程
    pkill -f keepalived || true
    sleep 2

    # 启动服务
    systemctl start keepalived
    if systemctl is-active --quiet keepalived; then
        log_success "Keepalived恢复成功"
        return 0
    else
        log_error "Keepalived启动失败"
        return 1
    fi
}

# 恢复虚拟IP
recover_vip() {
    log_info "恢复虚拟IP绑定..."

    VIP="172.20.0.100"
    INTERFACE="eth0"

    if ! ip addr show dev "$INTERFACE" | grep -q "$VIP"; then
        ip addr add "$VIP/24" dev "$INTERFACE"
        log_success "虚拟IP绑定成功"
        return 0
    else
        log_info "虚拟IP已绑定"
        return 0
    fi
}

# 恢复核心服务
recover_services() {
    log_info "恢复核心服务..."

    services=("nginx" "keepalived")
    recovered=0

    for service in "${services[@]}"; do
        if systemctl is-active --quiet $service; then
            log_info "$service 服务已运行"
        else
            log_info "启动 $service 服务..."
            systemctl start $service
            if systemctl is-active --quiet $service; then
                recovered=$((recovered + 1))
                log_success "$service 服务恢复成功"
            else
                log_error "$service 服务恢复失败"
            fi
        fi
    done

    return $recovered
}

# 主恢复流程
main() {
    echo "============================================"
    echo "     Athena应急恢复脚本"
    echo "     执行时间: $(date)"
    echo "============================================"
    echo ""

    # 检查权限
    if [ "$EUID" -ne 0 ]; then
        log_error "请使用root权限执行此脚本"
        exit 1
    fi

    # 恢复服务
    recover_nginx
    recover_keepalived
    recover_vip
    recover_services

    echo ""
    echo "============================================"
    log_success "应急恢复执行完成"
    echo "============================================"

    # 生成恢复报告
    echo "恢复报告: $(date)" > /tmp/recovery_report.txt
    echo "Nginx状态: $(systemctl is-active nginx)" >> /tmp/recovery_report.txt
    echo "Keepalived状态: $(systemctl is-active keepalived)" >> /tmp/recovery_report.txt
    echo "虚拟IP状态: $(ip addr show | grep '172.20.0.100' || echo '未绑定')" >> /tmp/recovery_report.txt
}

main "$@"
EOF

    chmod +x "/Users/xujian/Athena工作平台/scripts/emergency_recovery.sh"

    # 创建服务检查脚本
    cat > "/Users/xujian/Athena工作平台/scripts/check_high_availability.sh" << 'EOF'
#!/bin/bash
# 高可用性状态检查脚本

echo "============================================"
echo "     Athena高可用性状态检查"
echo "     检查时间: $(date)"
echo "============================================"
echo ""

# 检查Keepalived状态
echo "1. Keepalived服务状态:"
systemctl status keepalived --no-pager -l | head -20
echo ""

# 检查虚拟IP
echo "2. 虚拟IP状态:"
ip addr show | grep -E "172.20.0.100|172.20.0.200" || echo "虚拟IP未绑定"
echo ""

# 检查健康检查脚本
echo "3. 健康检查脚本状态:"
for script in check_nginx.sh check_services.sh check_database.sh check_redis.sh; do
    if [ -x "/usr/local/bin/$script" ]; then
        echo "✓ $script 可执行"
        /usr/local/bin/$script
    else
        echo "✗ $script 不存在或不可执行"
    fi
    echo ""
done

# 检查通知脚本
echo "4. 通知脚本状态:"
if [ -x "/etc/keepalived/notify.sh" ]; then
    echo "✓ notify.sh 可执行"
else
    echo "✗ notify.sh 不存在或不可执行"
fi
echo ""

# 检查日志文件
echo "5. 日志文件状态:"
if [ -f "/var/log/keepalived.log" ]; then
    echo "✓ keepalived.log 存在"
    echo "最近10条日志:"
    tail -10 /var/log/keepalived.log
else
    echo "✗ keepalived.log 不存在"
fi
echo ""

# 检查配置文件
echo "6. Keepalived配置文件:"
ls -la /etc/keepalived/*.conf 2>/dev/null || echo "没有找到配置文件"
echo ""

# 检查网络连接
echo "7. 网络连接状态:"
netstat -tlnp | grep -E ":(80|443|8080|8090)" || echo "关键端口未监听"
echo ""

# 检查进程状态
echo "8. 进程状态:"
pgrep -a keepalived || echo "Keepalived进程未运行"
pgrep -a nginx || echo "Nginx进程未运行"
echo ""

echo "============================================"
echo "高可用性状态检查完成"
echo "============================================"
EOF

    chmod +x "/Users/xujian/Athena工作平台/scripts/check_high_availability.sh"

    log_success "应急恢复脚本创建完成"
}

# 配置防火墙规则
configure_firewall() {
    log_info "配置防火墙规则..."

    # 如果使用ufw
    if command -v ufw &> /dev/null; then
        # 允许VRRP协议
        ufw allow to any port 112 proto vrrp

        # 允许监控端口
        ufw allow 8080/tcp comment "Health Check"
        ufw allow 8090/tcp comment "Nginx Status"

        # 允许管理端口
        ufw allow 8081/tcp comment "Maintenance"
        ufw allow 8082/tcp comment "Admin"

        log_info "UFW防火墙规则配置完成"
    fi

    # 如果使用firewalld
    if command -v firewall-cmd &> /dev/null; then
        # 允许VRRP协议
        firewall-cmd --permanent --add-protocol=vrrp

        # 允许监控端口
        firewall-cmd --permanent --add-port=8080/tcp
        firewall-cmd --permanent --add-port=8090/tcp
        firewall-cmd --permanent --add-port=8081/tcp
        firewall-cmd --permanent --add-port=8082/tcp

        # 重载防火墙
        firewall-cmd --reload

        log_info "Firewalld防火墙规则配置完成"
    fi

    log_success "防火墙配置完成"
}

# 启动高可用服务
start_ha_services() {
    log_info "启动高可用服务..."

    # 创建systemd服务文件
    cat > "/etc/systemd/system/keepalived@.service" << EOF
[Unit]
Description=Keepalived for node %I
After=network-online.target
Wants=network-online.target

[Service]
Type=forking
ExecStart=/usr/sbin/keepalived -f /etc/keepalived/keepalived_%i.conf -D
ExecReload=/bin/kill -HUP \$MAINPID
PIDFile=/var/run/keepalived_%i.pid
KillMode=process
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

    # 重新加载systemd
    systemctl daemon-reload

    # 启动keepalived服务
    systemctl enable keepalived@master
    systemctl start keepalived@master

    log_success "高可用服务启动完成"
}

# 验证高可用配置
verify_ha_configuration() {
    log_info "验证高可用配置..."

    # 检查keepalived配置语法
    for config in /etc/keepalived/*.conf; do
        if [ -f "$config" ]; then
            if keepalived -t -f "$config"; then
                log_success "配置文件 $config 语法正确"
            else
                log_error "配置文件 $config 语法错误"
                return 1
            fi
        fi
    done

    # 检查服务状态
    if systemctl is-active --quiet keepalived; then
        log_success "Keepalived服务运行正常"
    else
        log_error "Keepalived服务未运行"
    fi

    # 检查健康检查脚本
    for script in check_nginx.sh check_services.sh; do
        if [ -x "/usr/local/bin/$script" ]; then
            if "/usr/local/bin/$script" >/dev/null 2>&1; then
                log_success "健康检查脚本 $script 工作正常"
            else
                log_warning "健康检查脚本 $script 检查失败"
            fi
        fi
    done

    return 0
}

# 主函数
main() {
    echo -e "${BLUE}🛡️ Athena多模态文件系统高可用性配置${NC}"
    echo "============================================"
    echo -e "${CYAN}开始时间: $(date)${NC}"

    # 检查要求
    check_requirements

    # 创建配置
    create_keepalived_configs
    create_health_check_scripts
    create_notification_scripts
    create_failover_config
    create_monitoring_config
    create_recovery_scripts

    # 配置防火墙
    configure_firewall

    # 启动服务
    start_ha_services

    # 验证配置
    if verify_ha_configuration; then
        echo ""
        echo -e "${GREEN}✅ 高可用性配置完成！${NC}"
        echo ""
        echo -e "${BLUE}📋 配置信息:${NC}"
        echo -e "  🌐 虚拟IP: ${YELLOW}$VIRTUAL_IP${NC}"
        echo -e "  🔧 节点数量: ${YELLOW}${#NODES[@]}${NC}"
        echo -e "  📊 配置目录: ${YELLOW}/etc/keepalived${NC}"
        echo -e "  📝 日志文件: ${YELLOW}/var/log/keepalived.log${NC}"
        echo ""
        echo -e "${BLUE}🔧 管理命令:${NC}"
        echo -e "  🔄 应急恢复: ${YELLOW}/Users/xujian/Athena工作平台/scripts/emergency_recovery.sh${NC}"
        echo -e "  🔍 状态检查: ${YELLOW}/Users/xujian/Athena工作平台/scripts/check_high_availability.sh${NC}"
        echo -e "  📈 服务监控: ${YELLOW}systemctl status keepalived${NC}"
        echo ""
        echo -e "${PURPLE}✨ 高可用性系统已就绪！${NC}"
        echo ""
        echo -e "${YELLOW}📌 重要提示:${NC}"
        echo -e "  1. 确保所有节点时间同步 (NTP)"
        echo -e "  2. 定期测试故障转移"
        echo -e "  3. 监控日志文件大小"
        echo -e "  4. 备份配置文件"
    else
        echo -e "${RED}❌ 高可用性配置验证失败${NC}"
        exit 1
    fi
}

# 执行主函数
main "$@"