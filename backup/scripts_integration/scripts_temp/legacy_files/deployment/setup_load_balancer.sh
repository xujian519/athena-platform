#!/bin/bash
# 负载均衡和高可用配置脚本
# Load Balancer and High Availability Configuration for Athena Production

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
NGINX_CONFIG_DIR="/etc/nginx"
UPSTREAM_SERVERS=(
    "172.20.0.10:8020"
    "172.20.0.11:8020"
    "172.20.0.12:8020"
)
DOMAIN="athena.multimodal.ai"
BACKUP_DOMAINS=("api.athena.multimodal.ai" "admin.athena.multimodal.ai")

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

# 检查nginx
check_nginx() {
    if ! command -v nginx &> /dev/null; then
        log_error "Nginx未安装，请先安装Nginx"
        echo "Ubuntu/Debian: sudo apt-get install nginx"
        echo "CentOS/RHEL: sudo yum install nginx"
        echo "macOS: brew install nginx"
        exit 1
    fi
}

# 创建nginx主配置
create_nginx_main_config() {
    log_info "创建Nginx主配置文件..."

    sudo mkdir -p "$NGINX_CONFIG_DIR/conf.d"
    sudo mkdir -p "$NGINX_CONFIG_DIR/ssl"
    sudo mkdir -p "/var/log/nginx"

    cat > "$NGINX_CONFIG_DIR/nginx.conf" << 'EOF'
# Nginx主配置文件 - Athena多模态文件系统生产环境

user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

# 工作连接数优化
events {
    worker_connections 2048;
    use epoll;
    multi_accept on;
}

# 性能优化配置
http {
    # 基础配置
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # 日志格式
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for" '
                    'rt=$request_time uct="$upstream_connect_time" '
                    'uht="$upstream_header_time" urt="$upstream_response_time"';

    log_format detailed '$remote_addr - $remote_user [$time_local] "$request" '
                       '$status $body_bytes_sent "$http_referer" '
                       '"$http_user_agent" "$http_x_forwarded_for" '
                       'request_time=$request_time '
                       'upstream_addr=$upstream_addr '
                       'upstream_status=$upstream_status '
                       'upstream_response_time=$upstream_response_time';

    access_log /var/log/nginx/access.log main;

    # 性能优化
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    server_tokens off;

    # 客户端配置
    client_max_body_size 200M;
    client_body_buffer_size 128k;
    client_header_buffer_size 1k;
    large_client_header_buffers 4 4k;
    client_body_timeout 12;
    client_header_timeout 12;
    send_timeout 10;

    # Gzip压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;

    # 缓冲区配置
    proxy_buffering on;
    proxy_buffer_size 4k;
    proxy_buffers 8 4k;
    proxy_busy_buffers_size 8k;

    # 限流配置
    limit_req_zone $binary_remote_addr zone=api:10m rate=100r/m;
    limit_req_zone $binary_remote_addr zone=upload:10m rate=10r/m;
    limit_conn_zone $binary_remote_addr zone=conn_limit_per_ip:10m;

    # 包含站点配置
    include /etc/nginx/conf.d/*.conf;
}
EOF

    log_success "Nginx主配置文件创建完成"
}

# 创建负载均衡配置
create_load_balancer_config() {
    log_info "创建负载均衡配置..."

    cat > "$NGINX_CONFIG_DIR/conf.d/load_balancer.conf" << EOF
# 负载均衡配置 - Athena多模态文件系统

# API网关上游服务器组
upstream api_gateway_backend {
    least_conn;
    server ${UPSTREAM_SERVERS[0]} weight=3 max_fails=3 fail_timeout=30s;
    server ${UPSTREAM_SERVERS[1]} weight=3 max_fails=3 fail_timeout=30s;
    server ${UPSTREAM_SERVERS[2]} weight=2 max_fails=3 fail_timeout=30s backup;

    # 健康检查
    keepalive 32;
}
EOF

    # 为每个服务创建上游服务器组
    services=("dolphin_parser:8013" "glm_vision:8091" "multimodal_processor:8012" "xiao_nuo_control:9001" "athena_platform:9000" "platform_monitor:9090")

    for service in "${services[@]}"; do
        service_name=$(echo $service | cut -d':' -f1)
        service_port=$(echo $service | cut -d':' -f2)

        cat >> "$NGINX_CONFIG_DIR/conf.d/load_balancer.conf" << EOF

# ${service_name}上游服务器组
upstream ${service_name}_backend {
    least_conn;
    server 172.20.0.10:${service_port} weight=3 max_fails=3 fail_timeout=30s;
    server 172.20.0.11:${service_port} weight=3 max_fails=3 fail_timeout=30s;
    server 172.20.0.12:${service_port} weight=2 max_fails=3 fail_timeout=30s backup;

    keepalive 16;
}
EOF
    done

    log_success "负载均衡配置创建完成"
}

# 创建SSL站点配置
create_ssl_site_config() {
    log_info "创建SSL站点配置..."

    cat > "$NGINX_CONFIG_DIR/conf.d/ssl_sites.conf" << EOF
# SSL站点配置 - Athena多模态文件系统

# 主域名配置
server {
    listen 80;
    server_name $DOMAIN ${BACKUP_DOMAINS[@]};

    # 重定向到HTTPS
    return 301 https://\$server_name\$request_uri;
}

# HTTPS主站点
server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    # SSL证书配置
    ssl_certificate /etc/ssl/certs/$DOMAIN.crt;
    ssl_certificate_key /etc/ssl/private/$DOMAIN.key;

    # SSL安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA384:DHE-RSA-AES128-SHA256:DHE-RSA-AES256-SHA384';
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_session_tickets off;

    # 安全头
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self'; frame-ancestors 'none';" always;

    # 日志配置
    access_log /var/log/nginx/${DOMAIN}_access.log detailed;
    error_log /var/log/nginx/${DOMAIN}_error.log;

    # 根路径
    location / {
        proxy_pass http://api_gateway_backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$host;
        proxy_set_header X-Forwarded-Port \$server_port;

        # 超时配置
        proxy_connect_timeout 5s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # 限流
        limit_req zone=api burst=50 nodelay;
        limit_conn conn_limit_per_ip 20;
    }

    # API端点
    location /api/ {
        proxy_pass http://api_gateway_backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # API专用配置
        proxy_connect_timeout 3s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;

        limit_req zone=api burst=100 nodelay;
    }

    # 文件上传
    location /upload/ {
        proxy_pass http://api_gateway_backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # 上传专用配置
        client_max_body_size 200M;
        proxy_connect_timeout 10s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        proxy_request_buffering off;

        limit_req zone=upload burst=5 nodelay;
    }

    # 健康检查
    location /health {
        proxy_pass http://api_gateway_backend;
        access_log off;
        proxy_connect_timeout 1s;
        proxy_send_timeout 1s;
        proxy_read_timeout 1s;
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        add_header X-Cache-Status "STATIC";
        try_files \$uri @api_fallback;
    }

    location @api_fallback {
        proxy_pass http://api_gateway_backend;
    }
}
EOF

    # 为子域名创建配置
    for subdomain in "${BACKUP_DOMAINS[@]}"; do
        service_name=$(echo $subdomain | cut -d'.' -f1)

        cat >> "$NGINX_CONFIG_DIR/conf.d/ssl_sites.conf" << EOF

# $subdomain 子域名配置
server {
    listen 443 ssl http2;
    server_name $subdomain;

    # SSL证书配置
    ssl_certificate /etc/ssl/certs/$DOMAIN.crt;
    ssl_certificate_key /etc/ssl/private/$DOMAIN.key;

    # SSL安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA384:DHE-RSA-AES128-SHA256:DHE-RSA-AES256-SHA384';
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_session_tickets off;

    # 安全头
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # 日志配置
    access_log /var/log/nginx/${subdomain}_access.log detailed;
    error_log /var/log/nginx/${subdomain}_error.log;

    # 根据子域名路由到对应服务
    location / {
        proxy_pass http://${service_name}_backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        proxy_connect_timeout 5s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        limit_req zone=api burst=50 nodelay;
    }
}
EOF
    done

    log_success "SSL站点配置创建完成"
}

# 创建高可用配置
create_high_availability_config() {
    log_info "创建高可用配置..."

    cat > "$NGINX_CONFIG_DIR/conf.d/high_availability.conf" << 'EOF'
# 高可用配置 - Athena多模态文件系统

# 故障转移配置
map $http_upgrade $connection_upgrade {
    default upgrade;
    '' close;
}

# 健康检查端点
server {
    listen 8080;
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}

# 维护模式页面
server {
    listen 8081;
    location / {
        return 503 "系统维护中，请稍后访问...\n";
        add_header Content-Type text/plain;
        add_header Retry-After "300";
    }
}

# 限流和防护
limit_conn_status 429;
limit_req_status 429;

# IP白名单（管理员访问）
geo $admin_allowed {
    default 0;
    127.0.0.1 1;
    ::1 1;
    # 添加管理员IP地址
    # 192.168.1.0/24 1;
}

# 管理员访问控制
server {
    listen 8082;
    location /admin {
        if ($admin_allowed = 0) {
            return 403;
        }
        proxy_pass http://api_gateway_backend;
    }
}
EOF

    log_success "高可用配置创建完成"
}

# 创建Keepalived配置
create_keepalived_config() {
    log_info "创建Keepalived高可用配置..."

    # 创建主节点配置
    cat > "/etc/keepalived/keepalived.conf" << EOF
# Keepalived配置 - Athena多模态文件系统主节点

global_defs {
    router_id LB_MASTER
    script_user root
    enable_script_security
}

# 检查nginx是否运行
vrrp_script check_nginx {
    script "/usr/local/bin/check_nginx.sh"
    interval 2
    weight -20
    fall 3
    rise 2
}

# 虚拟IP配置
vrrp_instance VI_1 {
    state MASTER
    interface eth0
    virtual_router_id 51
    priority 110
    advert_int 1

    authentication {
        auth_type PASS
        auth_pass athena2024
    }

    virtual_ipaddress {
        172.20.0.100
    }

    track_script {
        check_nginx
    }

    # 状态切换通知
    notify_master "/etc/keepalived/notify.sh master"
    notify_backup "/etc/keepalived/notify.sh backup"
    notify_fault "/etc/keepalived/notify.sh fault"
}
EOF

    # 创建nginx检查脚本
    cat > "/usr/local/bin/check_nginx.sh" << 'EOF'
#!/bin/bash
# 检查nginx服务状态
if ! pgrep nginx > /dev/null; then
    exit 1
fi

# 检查nginx端口
if ! nc -z localhost 80; then
    exit 1
fi

exit 0
EOF

    # 创建状态通知脚本
    cat > "/etc/keepalived/notify.sh" << 'EOF'
#!/bin/bash
# Keepalived状态通知脚本

TYPE=$1
NAME=$2

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> /var/log/keepalived.log
}

case $TYPE in
    master)
        log_message "Keepalived transitioned to MASTER state"
        systemctl start nginx
        # 发送通知
        curl -X POST -H "Content-Type: application/json" \
            -d '{"alert": "Keepalived MASTER", "server": "'$(hostname)'"}' \
            http://localhost:9090/alerts || true
        ;;
    backup)
        log_message "Keepalived transitioned to BACKUP state"
        systemctl stop nginx
        # 发送通知
        curl -X POST -H "Content-Type: application/json" \
            -d '{"alert": "Keepalived BACKUP", "server": "'$(hostname)'"}' \
            http://localhost:9090/alerts || true
        ;;
    fault)
        log_message "Keepalived transitioned to FAULT state"
        systemctl stop nginx
        # 发送通知
        curl -X POST -H "Content-Type: application/json" \
            -d '{"alert": "Keepalived FAULT", "server": "'$(hostname)'"}' \
            http://localhost:9090/alerts || true
        ;;
esac
EOF

    chmod +x "/usr/local/bin/check_nginx.sh"
    chmod +x "/etc/keepalived/notify.sh"

    log_success "Keepalived配置创建完成"
}

# 创建监控配置
create_monitoring_config() {
    log_info "创建监控配置..."

    cat > "$NGINX_CONFIG_DIR/conf.d/monitoring.conf" << 'EOF'
# Nginx监控配置

# Nginx状态页面
server {
    listen 127.0.0.1:8090;
    location /nginx_status {
        stub_status on;
        access_log off;
        allow 127.0.0.1;
        allow ::1;
        deny all;
    }

    location /metrics {
        access_log off;
        return 200 "nginx_up 1\nnginx_connections_active $connections_active\nnginx_connections_reading $connections_reading\nnginx_connections_writing $connections_writing\nnginx_connections_waiting $connections_waiting\n";
        add_header Content-Type text/plain;
    }
}
EOF

    log_success "监控配置创建完成"
}

# 创建性能优化配置
create_performance_config() {
    log_info "创建性能优化配置..."

    cat > "$NGINX_CONFIG_DIR/conf.d/performance.conf" << 'EOF'
# 性能优化配置

# 文件描述符限制
worker_rlimit_nofile 65535;

# 缓存配置
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:100m max_size=10g inactive=60m use_temp_path=off;
proxy_cache_path /var/cache/nginx/static levels=1:2 keys_zone=static_cache:50m max_size=5g inactive=24h use_temp_path=off;

# 缓存规则
proxy_cache_key "$scheme$request_method$host$request_uri";
proxy_cache_valid 200 302 10m;
proxy_cache_valid 404 1m;

# 缓存配置示例
location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg)$ {
    proxy_pass http://api_gateway_backend;
    proxy_cache static_cache;
    proxy_cache_valid 200 1h;
    add_header X-Cache-Status $upstream_cache_status;
    expires 1y;
    add_header Cache-Control "public, immutable";
}
EOF

    log_success "性能优化配置创建完成"
}

# 测试nginx配置
test_nginx_config() {
    log_info "测试Nginx配置..."

    if nginx -t; then
        log_success "Nginx配置测试通过"
        return 0
    else
        log_error "Nginx配置测试失败"
        return 1
    fi
}

# 启动服务
start_services() {
    log_info "启动负载均衡服务..."

    # 启动nginx
    sudo systemctl enable nginx
    sudo systemctl start nginx

    # 启动keepalived
    sudo systemctl enable keepalived
    sudo systemctl start keepalived

    log_success "负载均衡服务启动完成"
}

# 验证配置
verify_configuration() {
    log_info "验证负载均衡配置..."

    # 检查服务状态
    if systemctl is-active --quiet nginx; then
        log_success "Nginx服务运行正常"
    else
        log_error "Nginx服务未运行"
    fi

    if systemctl is-active --quiet keepalived; then
        log_success "Keepalived服务运行正常"
    else
        log_warning "Keepalived服务未运行"
    fi

    # 检查端口监听
    if netstat -tlnp | grep -q ":80 "; then
        log_success "HTTP端口(80)监听正常"
    else
        log_error "HTTP端口(80)未监听"
    fi

    if netstat -tlnp | grep -q ":443 "; then
        log_success "HTTPS端口(443)监听正常"
    else
        log_error "HTTPS端口(443)未监听"
    fi

    # 测试健康检查
    if curl -f http://localhost:8080/health >/dev/null 2>&1; then
        log_success "健康检查端点正常"
    else
        log_warning "健康检查端点异常"
    fi
}

# 创建管理脚本
create_management_scripts() {
    log_info "创建负载均衡管理脚本..."

    # 创建重载脚本
    cat > "/Users/xujian/Athena工作平台/scripts/reload_load_balancer.sh" << 'EOF'
#!/bin/bash
# 负载均衡配置重载脚本

echo "开始重载负载均衡配置..."

# 测试配置
if nginx -t; then
    echo "配置测试通过，开始重载..."
    nginx -s reload
    echo "配置重载完成"
else
    echo "配置测试失败，请检查配置文件"
    exit 1
fi
EOF

    # 创建状态检查脚本
    cat > "/Users/xujian/Athena工作平台/scripts/check_load_balancer.sh" << 'EOF'
#!/bin/bash
# 负载均衡状态检查脚本

echo "=== 负载均衡状态检查 ==="
echo "时间: $(date)"
echo ""

# 检查nginx状态
echo "1. Nginx服务状态:"
systemctl status nginx --no-pager -l
echo ""

# 检查keepalived状态
echo "2. Keepalived服务状态:"
systemctl status keepalived --no-pager -l
echo ""

# 检查端口监听
echo "3. 端口监听状态:"
netstat -tlnp | grep -E ":(80|443|8080|8090)"
echo ""

# 检查nginx状态
echo "4. Nginx连接状态:"
curl -s http://127.0.0.1:8090/nginx_status
echo ""

# 检查虚拟IP
echo "5. 虚拟IP状态:"
ip addr show | grep "172.20.0.100"
echo ""

# 检查上游服务器
echo "6. 上游服务器状态:"
curl -s http://localhost/upstream_status || echo "上游状态检查失败"
echo ""
EOF

    chmod +x "/Users/xujian/Athena工作平台/scripts/reload_load_balancer.sh"
    chmod +x "/Users/xujian/Athena工作平台/scripts/check_load_balancer.sh"

    log_success "管理脚本创建完成"
}

# 主函数
main() {
    echo -e "${BLUE}🔄 Athena多模态文件系统负载均衡和高可用配置${NC}"
    echo "=============================================="
    echo -e "${CYAN}开始时间: $(date)${NC}"

    # 检查依赖
    check_nginx

    # 创建配置
    create_nginx_main_config
    create_load_balancer_config
    create_ssl_site_config
    create_high_availability_config
    create_keepalived_config
    create_monitoring_config
    create_performance_config

    # 测试配置
    if test_nginx_config; then
        # 启动服务
        start_services

        # 创建管理脚本
        create_management_scripts

        # 验证配置
        verify_configuration

        echo ""
        echo -e "${GREEN}✅ 负载均衡和高可用配置完成！${NC}"
        echo ""
        echo -e "${BLUE}📋 配置信息:${NC}"
        echo -e "  🌐 主域名: ${YELLOW}$DOMAIN${NC}"
        echo -e "  📡 负载均衡: ${YELLOW}172.20.0.100${NC}"
        echo -e "  🔧 配置目录: ${YELLOW}$NGINX_CONFIG_DIR${NC}"
        echo -e "  📊 监控端口: ${YELLOW}8090${NC}"
        echo -e "  ❤️ 健康检查: ${YELLOW}8080${NC}"
        echo ""
        echo -e "${BLUE}🔧 管理命令:${NC}"
        echo -e "  🔄 重载配置: ${YELLOW}/Users/xujian/Athena工作平台/scripts/reload_load_balancer.sh${NC}"
        echo -e "  🔍 状态检查: ${YELLOW}/Users/xujian/Athena工作平台/scripts/check_load_balancer.sh${NC}"
        echo -e "  📈 Nginx状态: ${YELLOW}http://127.0.0.1:8090/nginx_status${NC}"
        echo ""
        echo -e "${PURPLE}✨ 负载均衡和高可用系统已就绪！${NC}"
    else
        echo -e "${RED}❌ 配置验证失败${NC}"
        exit 1
    fi
}

# 执行主函数
main "$@"