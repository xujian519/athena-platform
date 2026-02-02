#!/bin/bash

# SSL证书生成脚本
# 为Athena工作平台生成自签名SSL证书

echo "🔐 SSL证书生成工具"
echo "=================="

# 设置目录
CERT_DIR="certs"
mkdir -p $CERT_DIR

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查依赖
check_dependencies() {
    log_info "检查依赖..."

    # 检查OpenSSL
    if ! command -v openssl &> /dev/null; then
        log_error "OpenSSL未安装"
        echo "请安装OpenSSL:"
        echo "  Ubuntu/Debian: sudo apt-get install openssl"
        echo "  CentOS/RHEL: sudo yum install openssl"
        echo "  macOS: brew install openssl"
        exit 1
    fi

    log_info "依赖检查完成"
}

# 生成私钥
generate_private_key() {
    local key_file="$CERT_DIR/server.key"

    log_info "生成私钥..."
    openssl genrsa -out "$key_file" 2048

    if [ $? -eq 0 ]; then
        log_info "私钥生成成功: $key_file"
        chmod 600 "$key_file"
    else
        log_error "私钥生成失败"
        exit 1
    fi
}

# 生成证书签名请求
generate_csr() {
    local key_file="$CERT_DIR/server.key"
    local csr_file="$CERT_DIR/server.csr"

    log_info "生成证书签名请求..."

    # 创建配置文件
    cat > "$CERT_DIR/openssl.cnf" << EOF
[req]
default_bits = 2048
prompt = no
default_md = sha256
distinguished_name = dn
req_extensions = v3_req

[dn]
CN = Athena Platform
O = Athena Platform
OU = IT Department
L = Beijing
ST = Beijing
C = CN

[v3_req]
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = *.localhost
DNS.3 = 127.0.0.1
IP.1 = 127.0.0.1
IP.2 = ::1
EOF

    openssl req -new -key "$key_file" -out "$csr_file" -config "$CERT_DIR/openssl.cnf"

    if [ $? -eq 0 ]; then
        log_info "CSR生成成功: $csr_file"
    else
        log_error "CSR生成失败"
        exit 1
    fi
}

# 生成自签名证书
generate_certificate() {
    local key_file="$CERT_DIR/server.key"
    local csr_file="$CERT_DIR/server.csr"
    local cert_file="$CERT_DIR/server.crt"
    local config_file="$CERT_DIR/openssl.cnf"

    log_info "生成自签名证书..."

    openssl x509 -req -days 365 -in "$csr_file" -signkey "$key_file" -out "$cert_file" -extensions v3_req -extfile "$config_file"

    if [ $? -eq 0 ]; then
        log_info "证书生成成功: $cert_file"
    else
        log_error "证书生成失败"
        exit 1
    fi
}

# 验证证书
verify_certificate() {
    local cert_file="$CERT_DIR/server.crt"

    log_info "验证证书..."

    openssl x509 -in "$cert_file" -text -noout | grep -A 2 "Subject Alternative Name"

    if [ $? -eq 0 ]; then
        log_info "证书验证成功"
    else
        log_warn "证书验证时出现警告"
    fi
}

# 生成DH参数（可选）
generate_dhparam() {
    local dh_file="$CERT_DIR/dhparam.pem"

    log_info "生成DH参数（可能需要几分钟）..."

    openssl dhparam -out "$dh_file" 2048

    if [ $? -eq 0 ]; then
        log_info "DH参数生成成功: $dh_file"
    else
        log_error "DH参数生成失败"
    fi
}

# 生成Nginx配置
generate_nginx_config() {
    local config_file="$CERT_DIR/nginx.conf"

    log_info "生成Nginx配置示例..."

    cat > "$config_file" << EOF
# Nginx配置示例
# 将此内容添加到您的Nginx配置中

server {
    listen 80;
    server_name localhost;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name localhost;

    ssl_certificate $(pwd)/$CERT_DIR/server.crt;
    ssl_certificate_key $(pwd)/$CERT_DIR/server.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers on;

    # 安全头
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

    log_info "Nginx配置已生成: $config_file"
}

# 显示证书信息
show_certificate_info() {
    local cert_file="$CERT_DIR/server.crt"

    echo -e "\n${GREEN}证书信息${NC}"
    echo "============"

    openssl x509 -in "$cert_file" -noout -dates
    openssl x509 -in "$cert_file" -noout -subject

    echo -e "\n${YELLOW}文件位置${NC}"
    echo "----------"
    echo "证书文件: $cert_file"
    echo "私钥文件: $CERT_DIR/server.key"
    echo "CSR文件: $CERT_DIR/server.csr"
    if [ -f "$CERT_DIR/dhparam.pem" ]; then
        echo "DH参数: $CERT_DIR/dhparam.pem"
    fi
}

# 清理函数
cleanup() {
    log_info "清理临时文件..."
    rm -f "$CERT_DIR/openssl.cnf"
}

# 主函数
main() {
    local generate_dh=false

    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dh)
                generate_dh=true
                shift
                ;;
            --clean)
                log_info "清理现有证书..."
                rm -f $CERT_DIR/*
                shift
                ;;
            -h|--help)
                echo "用法: $0 [选项]"
                echo ""
                echo "选项:"
                echo "  --dh      同时生成DH参数"
                echo "  --clean   清理现有证书"
                echo "  -h, --help 显示帮助信息"
                exit 0
                ;;
            *)
                log_error "未知选项: $1"
                exit 1
                ;;
        esac
    done

    echo -e "\n${GREEN}开始生成SSL证书${NC}"
    echo "=================="

    # 检查依赖
    check_dependencies

    # 生成私钥
    generate_private_key

    # 生成CSR
    generate_csr

    # 生成证书
    generate_certificate

    # 验证证书
    verify_certificate

    # 生成DH参数（可选）
    if [ "$generate_dh" = true ]; then
        generate_dhparam
    fi

    # 生成Nginx配置
    generate_nginx_config

    # 显示证书信息
    show_certificate_info

    # 清理
    cleanup

    echo -e "\n${GREEN}✅ SSL证书生成完成！${NC}"
    echo -e "\n${YELLOW}注意：${NC}"
    echo "1. 这是自签名证书，浏览器会显示安全警告"
    echo "2. 生产环境请使用受信任的CA签发的证书"
    echo "3. 证书有效期为365天，请及时更新"
    echo "4. 请妥善保管私钥文件"
}

# 错误处理
set -e
trap 'log_error "脚本执行失败"; cleanup; exit 1' ERR

# 执行主函数
main "$@"