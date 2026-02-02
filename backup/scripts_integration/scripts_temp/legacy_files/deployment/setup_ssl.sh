#!/bin/bash
# SSL证书设置脚本
# SSL Certificate Setup for Athena Production Deployment

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
DOMAIN="athena.multimodal.ai"
SSL_DIR="/etc/ssl/certs"
SSL_KEY_DIR="/etc/ssl/private"
CONFIG_DIR="/Users/xujian/Athena工作平台/deploy"
PRODUCTION_CONFIG="$CONFIG_DIR/production_config.yaml"

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

# 检查openssl
check_openssl() {
    if ! command -v openssl &> /dev/null; then
        log_error "OpenSSL未安装，请先安装OpenSSL"
        echo "Ubuntu/Debian: sudo apt-get install openssl"
        echo "CentOS/RHEL: sudo yum install openssl"
        echo "macOS: brew install openssl"
        exit 1
    fi
}

# 创建SSL目录
create_ssl_directories() {
    log_info "创建SSL目录结构..."

    sudo mkdir -p "$SSL_DIR"
    sudo mkdir -p "$SSL_KEY_DIR"
    sudo mkdir -p "/etc/ssl/private/backup"

    # 设置权限
    sudo chmod 755 "$SSL_DIR"
    sudo chmod 700 "$SSL_KEY_DIR"
    sudo chmod 700 "/etc/ssl/private/backup"

    log_success "SSL目录创建完成"
}

# 生成自签名证书（开发/测试环境）
generate_self_signed_cert() {
    log_info "生成自签名SSL证书..."

    # 生成私钥
    sudo openssl genrsa -out "$SSL_KEY_DIR/$DOMAIN.key" 4096

    # 生成证书签名请求
    sudo openssl req -new -key "$SSL_KEY_DIR/$DOMAIN.key" \
        -out "$SSL_DIR/$DOMAIN.csr" \
        -subj "/C=CN/ST=Beijing/L=Beijing/O=Athena Multimodal AI/CN=$DOMAIN"

    # 生成自签名证书
    sudo openssl x509 -req -days 365 \
        -in "$SSL_DIR/$DOMAIN.csr" \
        -signkey "$SSL_KEY_DIR/$DOMAIN.key" \
        -out "$SSL_DIR/$DOMAIN.crt" \
        -extensions v3_req \
        -extfile <(echo "
[v3_req]
basicConstraints = CA:FALSE
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth, clientAuth
subjectAltName = @alt_names
[alt_names]
DNS.1 = $DOMAIN
DNS.2 = *.$DOMAIN
DNS.3 = www.$DOMAIN
DNS.4 = api.$DOMAIN
DNS.5 = admin.$DOMAIN
") \
        -passin "$SSL_DIR/$DOMAIN.csr"

    # 备份私钥
    sudo cp "$SSL_KEY_DIR/$DOMAIN.key" "/etc/ssl/private/backup/$DOMAIN.key.backup"

    log_success "自签名证书生成完成"
}

# 生成CA证书（生产环境）
generate_ca_cert() {
    log_info "生成CA根证书..."

    # 生成CA私钥
    sudo openssl genrsa -out "$SSL_KEY_DIR/ca.key" 4096

    # 生成CA证书
    sudo openssl req -x509 -new -nodes \
        -key "$SSL_KEY_DIR/ca.key" \
        -sha256 -days 3650 \
        -out "$SSL_DIR/ca.crt" \
        -subj "/C=CN/ST=Beijing/L=Beijing/O=Athena Multimodal AI/CN=athena-ca.multimodal.ai"

    # 设置CA权限
    sudo chmod 600 "$SSL_KEY_DIR/ca.key"
    sudo chmod 644 "$SSL_DIR/ca.crt"

    log_success "CA根证书生成完成"
}

# 使用CA签名服务器证书
sign_server_cert() {
    log_info "使用CA签名服务器证书..."

    # 生成服务器私钥
    sudo openssl genrsa -out "$SSL_KEY_DIR/$DOMAIN.key" 2048

    # 生成证书签名请求
    sudo openssl req -new -key "$SSL_KEY_DIR/$DOMAIN.key" \
        -out "$SSL_DIR/$DOMAIN.csr" \
        -subj "/C=CN/ST=Beijing/L=Beijing/O=Athena Multimodal AI/CN=$DOMAIN"

    # 创建扩展文件
    cat > "$SSL_DIR/$DOMAIN.ext" << EOF
authorityKeyIdentifier=keyid,authority
authorityKeyIdentifier=keyid,issuer
basicConstraints = CA:FALSE
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth, clientAuth, codeSigning, emailProtection, timeStamping
subjectAltName = @alt_names
[alt_names]
DNS.1 = $DOMAIN
DNS.2 = *.$DOMAIN
DNS.3 = www.$DOMAIN
DNS.4 = api.$DOMAIN
DNS.5 = admin.$DOMAIN
IP.1 = 127.0.0.1
IP.2 = ::1
EOF

    # 使用CA签名证书
    sudo openssl x509 -req -in "$SSL_DIR/$DOMAIN.csr" \
        -CA "$SSL_DIR/ca.crt" -CAkey "$SSL_KEY_DIR/ca.key" \
        -CAcreateserial -CAserial $(( $(date +%s))) \
        -out "$SSL_DIR/$DOMAIN.crt" \
        -days 365 -sha256 \
        -extfile "$SSL_DIR/$DOMAIN.ext"

    # 备份私钥
    sudo cp "$SSL_KEY_DIR/$DOMAIN.key" "/etc/ssl/private/backup/$DOMAIN.key.backup"

    log_success "服务器证书签名完成"
}

# 设置Let's Encrypt证书（推荐用于生产环境）
setup_letsencrypt() {
    log_info "设置Let's Encrypt证书..."

    # 检查certbot
    if ! command -v certbot &> /dev/null; then
        log_info "安装Certbot..."
        sudo apt-get update
        sudo apt-get install -y certbot python3-certbot-nginx
    fi

    # 创建nginx配置目录
    sudo mkdir -p "/etc/nginx/conf.d"

    # 创建临时nginx配置用于证书验证
    cat > "/etc/nginx/conf.d/temp.conf" << EOF
server {
    listen 80;
    server_name $DOMAIN;
    root /var/www/html;
}
EOF

    # 启动nginx
    sudo systemctl start nginx || true

    # 获取证书
    sudo certbot certonly --nginx \
        -d "$DOMAIN" \
        --email "admin@athena.multimodal.ai" \
        --agree-tos \
        --no-eff-email \
        --keep-until-expiring \
        --non-interactive

    # 删除临时配置
    sudo rm "/etc/nginx/conf.d/temp.conf"
    sudo systemctl reload nginx

    log_success "Let's Encrypt证书设置完成"
}

# 配置nginx
configure_nginx() {
    log_info "配置Nginx SSL..."

    # 创建nginx配置目录
    sudo mkdir -p "/etc/nginx/conf.d"
    sudo mkdir -p "/etc/nginx/ssl"

    # 复制SSL证书到nginx目录
    sudo cp "$SSL_DIR/$DOMAIN.crt" "/etc/nginx/ssl/"
    sudo cp "$SSL_KEY_DIR/$DOMAIN.key" "/etc/nginx/ssl/"

    # 创建nginx SSL配置
    cat > "/etc/nginx/conf.d/ssl.conf" << EOF
# SSL安全配置
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA384:DHE-RSA-AES128-SHA256:DHE-RSA-AES256-SHA384';
ssl_prefer_server_ciphers on;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
ssl_session_tickets off;

# 安全头
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
add_header X-Frame-Options "SAMEORIGIN";
add_header X-Content-Type-Options "nosniff";
add_header X-XSS-Protection "1; mode=block";
add_header Referrer-Policy "strict-origin-when-cross-origin";
EOF

    log_success "Nginx SSL配置完成"
}

# 创建Docker-compose SSL配置
create_docker_ssl_config() {
    log_info "创建Docker Compose SSL配置..."

    docker_compose_dir="/Users/xujian/Athena工作平台/docker"
    mkdir -p "$docker_compose_dir"

    cat > "$docker_compose_dir/docker-compose.prod.yml" << 'EOF'
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /etc/nginx/conf.d:/etc/nginx/conf.d:ro
      - /etc/ssl/certs:/etc/ssl/certs:ro
      - /var/log/nginx:/var/log/nginx
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - api-gateway
      - xiao-nuo-control
      - athena-platform
      - monitoring
    restart: unless-stopped
    networks:
      - athena-network

  api-gateway:
    image: registry.cn-hangzhou.aliyuncs.com/athena/multimodal-api:v2.0
    environment:
      - DATABASE_URL=postgresql://athena_user:${DB_PASSWORD}@postgres:5432/athena_production
      - REDIS_URL=redis://redis:6379/0
      - JWT_SECRET=${JWT_SECRET}
      - SSL_CERT_PATH=/etc/ssl/certs/athena.multimodal.ai.crt
      - SSL_KEY_PATH=/etc/ssl/private/athena.multimodal.ai.key
    volumes:
      - /etc/ssl/certs:/etc/ssl/certs:ro
      - /etc/ssl/private:/etc/ssl/private:ro
      - /data/athena/multimodal:/data/athena/multimodal
    networks:
      - athena-network
    restart: unless-stopped
    deploy:
      replicas: 3

  xiao-nuo-control:
    image: registry.cn-hangzhou.aliyuncs.com/athena/xiao-nuo-control:v2.0
    environment:
      - DATABASE_URL=postgresql://athena_user:${DB_PASSWORD}@postgres:5432/athena_production
      - REDIS_URL=redis://redis:6379/0
    networks:
      - athena-network
    restart: unless-stopped
    deploy:
      replicas: 2

  athena-platform:
    image: registry.cn-hangzhou.aliyuncs.com/athena/platform-manager:v2.0
    environment:
      - DATABASE_URL=postgresql://athena_user:${DB_PASSWORD}@postgres:5432/athena_production
      - REDIS_URL=redis://redis:6379/0
      - JWT_SECRET=${JWT_SECRET}
    networks:
      - athena-network
    restart: unless-stopped
    deploy:
      replicas: 2

  monitoring:
    image: registry.cn-hangzhou.aliyuncs.com/athena/platform-monitor:v2.0
    ports:
      - "9090:9090"
      - "3000:3000"
    environment:
      - PROMETHEUS_URL=http://prometheus:9090
    networks:
      - athena-network
    restart: unless-stopped

networks:
  athena-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
        - gateway: 172.20.0.1

volumes:
  ssl_certs:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /etc/ssl/certs

  ssl_private:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /etc/ssl/private

  nginx_logs:
    driver: local

  data_athena:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /data/athena
EOF

    log_success "Docker Compose SSL配置创建完成"
}

# 设置证书自动续期
setup_auto_renewal() {
    log_info "设置证书自动续期..."

    # 创建续期脚本
    cat > "/Users/xujian/Athena工作平台/scripts/renew_ssl.sh" << 'EOF'
#!/bin/bash
# SSL证书自动续期脚本

LOG_FILE="/var/log/ssl_renew.log"
DOMAIN="athena.multimodal.ai"
SSL_DIR="/etc/ssl/certs"
SSL_KEY_DIR="/ssl/private"

echo "$(date): 开始证书续期检查..." >> $LOG_FILE

# 检查证书有效期
if [ -f "$SSL_DIR/$DOMAIN.crt" ]; then
    EXPIRY_DATE=$(openssl x509 -enddate -noout -in "$SSL_DIR/$DOMAIN.crt" | cut -d= -f1)
    CURRENT_DATE=$(date +%s)
    EXPIRY_TIMESTAMP=$(date -d "$EXPIRY_DATE" +%s)

    DAYS_LEFT=$((($EXPIRY_TIMESTAMP - $CURRENT_DATE) / 86400))

    echo "$(date): 证书有效期还剩 $DAYS_LEFT 天" >> $LOG_FILE

    # 如果证书少于30天，则续期
    if [ $DAYS_LEFT -lt 30 ]; then
        echo "$(date): 开始续期证书..." >> $LOG_FILE

        # 备份当前证书
        cp "$SSL_DIR/$DOMAIN.crt" "$SSL_DIR/$DOMAIN.crt.backup"
        cp "$SSL_KEY_DIR/$DOMAIN.key" "$SSL_KEY_DIR/$DOMAIN.key.backup"

        # 如果是Let's Encrypt证书，使用certbot续期
        if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
            echo "$(date): 续期Let's Encrypt证书..." >> $LOG_FILE
            sudo certbot renew --force-renewal --quiet >> $LOG_FILE 2>&1
        else
            echo "$(date): 续期自签名证书..." >> $LOG_FILE

            # 生成新的自签名证书
            openssl x509 -req -x509 -days 365 \
                -signkey "$SSL_KEY_DIR/$DOMAIN.key.backup" \
                -in "$SSL_DIR/$DOMAIN.crt.backup" \
                -out "$SSL_DIR/$DOMAIN.crt" \
                -sha256

            # 更新nginx配置
            sudo cp "$SSL_DIR/$DOMAIN.crt" "/etc/ssl/certs/"
            sudo cp "$SSL_KEY_DIR/$DOMAIN.key" "/etc/ssl/private/"
            sudo systemctl reload nginx
        fi

        echo "$(date): 证书续期完成" >> $LOG_FILE
    else
        echo "$(date): 证书还有 $DAYSNG 天，无需续期" >> $LOG_FILE
    fi
else
    echo "$(date): 证书文件不存在" >> $LOG_FILE
fi
EOF

    chmod +x "/Users/xujian/Athena工作平台/scripts/renew_ssl.sh"

    # 添加到crontab（每月1号凌晨3点检查）
    (crontab -l 2>/dev/null; echo "0 3 1 * * /Users/xujian/Athena工作平台/scripts/renew_ssl.sh") | crontab -

    log_success "证书自动续期设置完成"
}

# 验证SSL配置
verify_ssl_config() {
    log_info "验证SSL配置..."

    if [ ! -f "$SSL_DIR/$DOMAIN.crt" ]; then
        log_error "SSL证书文件不存在"
        return 1
    fi

    if [ ! -f "$SSL_KEY_DIR/$DOMAIN.key" ]; then
        log_error "SSL私钥文件不存在"
        return 1
    fi

    # 验证证书有效期
    EXPIRY_DATE=$(openssl x509 -enddate -noout -in "$SSL_DIR/$DOMAIN.crt" | cut -d - -f1)
    CURRENT_DATE=$(date)

    log_info "证书信息:"
    log_info "  域名: $DOMAIN"
    log_info "  有效期至: $EXPIRY_DATE"
    log_info "  当前时间: $CURRENT_DATE"

    # 检查证书有效性
    if openssl x509 -check -in "$SSL_DIR/$DOMAIN.crt" >/dev/null 2>&1; then
        log_success "SSL证书验证通过"
    else
        log_error "SSL证书验证失败"
        return 1
    fi

    # 检查私钥和证书匹配
    CERT_HASH=$(openssl x509 -pubkey -noout -in "$SSL_DIR/$DOMAIN.crt" | openssl md5)
    KEY_HASH=$(openssl rsa -pubout -outform PEM -in "$SSL_KEY_DIR/$DOMAIN.key" | openssl md5)

    if [ "$CERT_HASH" = "$KEY_HASH" ]; then
        log_success "SSL证书和私钥匹配"
    else
        log_error "SSL证书和私钥不匹配"
        return 1
    fi

    return 0
}

# 创建证书信息文件
create_cert_info() {
    cat > "/Users/xujian/Athena工作平台/ssl_info.json" << EOF
{
    "domain": "$DOMAIN",
    "certificate_path": "$SSL_DIR/$DOMAIN.crt",
    "key_path": "$SSL_KEY_DIR/$DOMAIN.key",
    "config_file": "$PRODUCTION_CONFIG",
    "created_at": "$(date -Iseconds)",
    "auto_renewal": true",
    "renewal_script": "/Users/xiuJian/Athena工作平台/scripts/renew_ssl.sh",
    "nginx_config": "/etc/nginx/conf.d/ssl.conf"
}
EOF

    log_success "证书信息文件创建完成"
}

# 主函数
main() {
    echo -e "${BLUE}🔐 Athena多模态文件系统SSL证书设置${NC}"
    echo "=========================================="
    echo -e "${CYAN}开始时间: $(date)${NC}"

    # 选择证书类型
    echo -e "${YELLOW}请选择证书类型:${NC}"
    echo "1. 自签名证书（开发/测试）"
    echo "2. CA签名证书（生产推荐）"
    echo "3. Let's Encrypt（生产环境）"
    echo "4. 仅配置目录"

    read -p "请选择 (1-4): " choice

    # 检查依赖
    check_openssl

    # 创建目录
    create_ssl_directories

    case $choice in
        1)
            generate_self_signed_cert
            ;;
        2)
            generate_ca_cert
            sign_server_cert
            ;;
        3)
            setup_letsencrypt
            ;;
        4)
            echo -e "${BLUE}仅创建SSL目录，不生成证书${NC}"
            ;;
        *)
            log_error "无效选择"
            exit 1
            ;;
    esac

    # 配置nginx
    if [ "$choice" -ne "4" ]; then
        configure_nginx
    fi

    # 创建Docker配置
    create_docker_ssl_config

    # 设置自动续期
    setup_auto_renewal

    # 验证配置
    if verify_ssl_config; then
        create_cert_info
        echo ""
        echo -e "${GREEN}✅ SSL证书设置完成！${NC}"
        echo ""
        echo -e "${BLUE}📋 证书信息:${NC}"
        echo -e "  📄 证书文件: ${YELLOW}$SSL_DIR/$DOMAIN.crt${NC}"
        echo -e "  🔑 私钥文件: ${YELLOW}$SSL_KEY_DIR/$DOMAIN.key${NC}"
        echo -e "  🔗 配置文件: ${YELLOW}$PRODUCTION_CONFIG${NC}"
        echo -e "  📋 信息文件: ${YELLOW}/Users/xujian/Athena工作平台/ssl_info.json${NC}"
        echo ""
        echo -e "${BLUE}🔧 管理命令:${NC}"
        echo -e "  🔍 查看证书: ${YELLOW}openssl x509 -in $SSL_DIR/$DOMAIN.crt -text -noout${NC}"
        echo -e "  ⏰ 验证证书: ${YELLOW}openssl x509 -check -in $SSL_DIR/$DOMAIN.crt${NC}"
        echo -e "  📅 查看私钥: ${YELLOW}openssl rsa -in $SSL_KEY_DIR/$DOMAIN.key -check${NC}"
        echo -e "  📅 证书信息: ${YELLOW}openssl x509 -in $SSL_DIR/$DOMAIN.crt -noout -dates${NC}"
        echo -e "  🔄 自动续期: ${YELLOW}/Users/xujian/Athena工作平台/scripts/renew_ssl.sh${NC}"
        echo ""
        echo -e "${PURPLE}✨ 现在您可以使用HTTPS安全访问Athena多模态文件系统！${NC}"
    else
        echo -e "${RED}❌ SSL配置验证失败${NC}"
        exit 1
    fi
}

# 执行主函数
main "$@"