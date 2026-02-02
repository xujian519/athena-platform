#!/bin/bash

# Redis安全配置脚本
# 作者: 徐健
# 创建日期: 2025-12-13

set -e

# 配置变量
REDIS_CONF=${REDIS_CONF:-"/etc/redis/redis.conf"}
REDIS_PASSWORD=${REDIS_PASSWORD:-"Ath3n@2024#RedisSecure"}
REDIS_PORT=${REDIS_PORT:-6379}

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# 检查是否以root运行
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要以root权限运行"
        exit 1
    fi
}

# 备份原配置文件
backup_config() {
    log_info "备份原配置文件..."
    if [ -f "$REDIS_CONF" ]; then
        cp "$REDIS_CONF" "${REDIS_CONF}.backup.$(date +%Y%m%d_%H%M%S)"
        log_success "配置文件已备份"
    fi
}

# 配置Redis安全
configure_redis_security() {
    log_info "配置Redis安全设置..."

    # 创建安全配置文件
    cat > /etc/redis/redis-security.conf << EOF
# Redis安全配置文件
# 生成时间: $(date)

# 网络安全
bind 127.0.0.1
port $REDIS_PORT
timeout 300
tcp-keepalive 60

# 通用配置
daemonize yes
supervised systemd
pidfile /var/run/redis/redis-server.pid
loglevel notice
logfile /var/log/redis/redis-server.log

# 数据库配置
databases 16
save 900 1
save 300 10
save 60 10000

# 内存配置
maxmemory 2gb
maxmemory-policy allkeys-lru

# 持久化配置
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir /var/lib/redis

# AOF配置
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb

# 安全配置
requirepass $REDIS_PASSWORD

# 禁用危险命令
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command KEYS ""
rename-command CONFIG "CONFIG_b835d3a8f8c0e7b6"
rename-command SHUTDOWN "SHUTDOWN_b835d3a8f8c0e7b6"
rename-command DEBUG ""
rename-command EVAL ""

# 客户端配置
maxclients 10000
tcp-backlog 511

# 内存优化
hash-max-ziplist-entries 512
hash-max-ziplist-value 64
list-max-ziplist-size -2
list-compress-depth 0
set-max-intset-entries 512
zset-max-ziplist-entries 128
zset-max-ziplist-value 64

# 延迟监控
latency-monitor-threshold 100

# 事件通知
notify-keyspace-events "Ex"

# 慢查询日志
slowlog-log-slower-than 10000
slowlog-max-len 128

# 客户端输出缓冲区限制
client-output-buffer-limit normal 0 0 0
client-output-buffer-limit replica 256mb 64mb 60
client-output-buffer-limit pubsub 32mb 8mb 60

# 内存使用率
memory-usage-stats yes

# 其他安全设置
protected-mode yes
tcp-backlog 511
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
supervised systemd

# ACL配置（Redis 6.0+）
acllog-max-len 128

# TLS配置（如果需要）
# tls-port 6380
# tls-cert-file /etc/redis/tls/redis.crt
# tls-key-file /etc/redis/tls/redis.key
# tls-ca-cert-file /etc/redis/tls/ca.crt
EOF

    log_success "Redis安全配置已创建"
}

# 配置Redis用户
configure_redis_users() {
    log_info "配置Redis用户..."

    # 检查Redis是否支持ACL
    if redis-cli ACL HELP > /dev/null 2>&1; then
        # 创建默认用户
        redis-cli ACL SETUSER default > /dev/null 2>&1 || true

        # 创建应用用户
        redis-cli ACL SETUSER athena_app on >$(echo -n $REDIS_PASSWORD | sha256sum | cut -d' ' -f1) > \
            +@read +@write +@admin ~* &* > /dev/null || true

        # 创建只读用户
        redis-cli ACL SETUSER athena_readonly on >$(echo -n "${REDIS_PASSWORD}_readonly" | sha256sum | cut -d' ' -f1) > \
            +@read ~* &* > /dev/null || true

        log_success "Redis用户已配置"
    else
        log_warning "当前Redis版本不支持ACL，使用传统认证"
    fi
}

# 设置文件权限
set_permissions() {
    log_info "设置文件权限..."

    # Redis配置文件权限
    chmod 640 /etc/redis/redis-security.conf
    chown root:redis /etc/redis/redis-security.conf

    # Redis数据目录权限
    mkdir -p /var/lib/redis
    chmod 750 /var/lib/redis
    chown redis:redis /var/lib/redis

    # Redis日志目录权限
    mkdir -p /var/log/redis
    chmod 750 /var/log/redis
    chown redis:redis /var/log/redis

    log_success "文件权限已设置"
}

# 创建systemd服务文件
create_systemd_service() {
    log_info "创建systemd服务文件..."

    cat > /etc/systemd/system/redis-secure.service << EOF
[Unit]
Description=Redis Secure In-Memory Data Store
After=network.target

[Service]
User=redis
Group=redis
ExecStart=/usr/local/bin/redis-server /etc/redis/redis-security.conf
ExecStop=/usr/local/bin/redis-cli shutdown
Restart=always
RestartSec=10

# 安全设置
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=/var/lib/redis /var/log/redis
ProtectHome=true
NoNewPrivileges=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    log_success "systemd服务文件已创建"
}

# 配置防火墙规则
configure_firewall() {
    log_info "配置防火墙规则..."

    # 如果使用ufw
    if command -v ufw > /dev/null 2>&1; then
        ufw allow from 127.0.0.1 to any port $REDIS_PORT
        ufw deny $REDIS_PORT
        log_success "ufw防火墙规则已配置"
    fi

    # 如果使用iptables
    if command -v iptables > /dev/null 2>&1; then
        iptables -A INPUT -p tcp -s 127.0.0.1 --dport $REDIS_PORT -j ACCEPT
        iptables -A INPUT -p tcp --dport $REDIS_PORT -j DROP
        # 保存规则
        if command -v iptables-save > /dev/null 2>&1; then
            iptables-save > /etc/iptables/rules.v4 2>/dev/null || true
        fi
        log_success "iptables防火墙规则已配置"
    fi
}

# 创建监控脚本
create_monitoring_script() {
    log_info "创建监控脚本..."

    cat > /usr/local/bin/redis-monitor.sh << 'EOF'
#!/bin/bash

REDIS_HOST=${REDIS_HOST:-127.0.0.1}
REDIS_PORT=${REDIS_PORT:-6379}
REDIS_PASSWORD=${REDIS_PASSWORD}
ALERT_EMAIL=${ALERT_EMAIL:-""}

# 检查Redis连接
check_redis_connection() {
    redis-cli -h $REDIS_HOST -p $REDIS_PORT -a $REDIS_PASSWORD ping > /dev/null 2>&1
}

# 检查Redis内存使用
check_redis_memory() {
    local memory_usage=$(redis-cli -h $REDIS_HOST -p $REDIS_PORT -a $REDIS_PASSWORD info memory | \
        grep used_memory_human | awk -F: '{print $2}' | tr -d '\r')
    echo $memory_usage
}

# 检查Redis连接数
check_redis_connections() {
    local connections=$(redis-cli -h $REDIS_HOST -p $REDIS_PORT -a $REDIS_PASSWORD info clients | \
        grep connected_clients | awk -F: '{print $2}' | tr -d '\r')
    echo $connections
}

# 发送告警
send_alert() {
    local message="$1"
    echo "$(date): $message" >> /var/log/redis/redis-monitor.log

    if [ -n "$ALERT_EMAIL" ]; then
        echo "$message" | mail -s "Redis Alert" $ALERT_EMAIL
    fi
}

# 主监控逻辑
if ! check_redis_connection; then
    send_alert "Redis连接失败！"
    exit 1
fi

memory_usage=$(check_redis_memory)
connections=$(check_redis_connections)

# 检查内存使用率（假设最大内存为2GB）
memory_bytes=$(echo $memory_usage | sed 's/[^0-9.]//g')
memory_mb=$(echo "$memory_bytes / 1048576" | bc -l 2>/dev/null || echo "0")

if (( $(echo "$memory_mb > 1800" | bc -l 2>/dev/null || echo "0") )); then
    send_alert "Redis内存使用过高: ${memory_usage}"
fi

if [ "$connections" -gt 800 ]; then
    send_alert "Redis连接数过高: ${connections}"
fi
EOF

    chmod +x /usr/local/bin/redis-monitor.sh

    # 创建监控定时任务
    cat > /etc/cron.d/redis-monitor << EOF
# Redis监控任务
*/5 * * * * root /usr/local/bin/redis-monitor.sh
EOF

    log_success "监控脚本已创建"
}

# 创建备份脚本
create_backup_script() {
    log_info "创建备份脚本..."

    cat > /usr/local/bin/redis-backup.sh << 'EOF'
#!/bin/bash

REDIS_HOST=${REDIS_HOST:-127.0.0.1}
REDIS_PORT=${REDIS_PORT:-6379}
REDIS_PASSWORD=${REDIS_PASSWORD}
BACKUP_DIR=${BACKUP_DIR:-/var/backups/redis}
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR

# 执行备份
redis-cli -h $REDIS_HOST -p $REDIS_PORT -a $REDIS_PASSWORD \
    --rdb $BACKUP_DIR/dump_$DATE.rdb

# 压缩备份文件
gzip $BACKUP_DIR/dump_$DATE.rdb

# 删除7天前的备份
find $BACKUP_DIR -name "dump_*.rdb.gz" -mtime +7 -delete

echo "Redis备份完成: $BACKUP_DIR/dump_$DATE.rdb.gz"
EOF

    chmod +x /usr/local/bin/redis-backup.sh

    # 创建备份定时任务
    cat > /etc/cron.d/redis-backup << EOF
# Redis备份任务
0 2 * * * root /usr/local/bin/redis-backup.sh
EOF

    log_success "备份脚本已创建"
}

# 测试配置
test_configuration() {
    log_info "测试配置..."

    # 使用安全配置启动Redis
    redis-server /etc/redis/redis-security.conf --daemonize yes

    # 等待Redis启动
    sleep 3

    # 测试认证
    if redis-cli -a $REDIS_PASSWORD ping | grep -q PONG; then
        log_success "Redis配置测试通过"
    else
        log_error "Redis配置测试失败"
        return 1
    fi

    # 停止Redis
    redis-cli -a $REDIS_PASSWORD shutdown
}

# 主函数
main() {
    log_info "开始Redis安全配置..."

    check_root
    backup_config
    configure_redis_security
    configure_redis_users
    set_permissions
    create_systemd_service
    configure_firewall
    create_monitoring_script
    create_backup_script

    if test_configuration; then
        log_success "Redis安全配置完成！"
        log_info "请执行以下操作："
        log_info "1. 启动安全Redis: systemctl start redis-secure"
        log_info "2. 启用开机自启: systemctl enable redis-secure"
        log_info "3. 检查状态: systemctl status redis-secure"
        log_warning "请妥善保管Redis密码！"
    else
        log_error "配置测试失败，请检查配置"
        exit 1
    fi
}

# 执行主函数
main "$@"