#!/bin/bash

# TLS证书生成脚本
# 为Athena Gateway生成自签名TLS证书

set -e

CERTS_DIR="/Users/xujian/Athena工作平台/gateway-unified/certs"
CERT_FILE="$CERTS_DIR/server.crt"
KEY_FILE="$CERTS_DIR/server.key"
CSR_FILE="$CERTS_DIR/server.csr"
CONFIG_FILE="$CERTS_DIR/openssl.conf"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# 创建证书目录
log_info "创建证书目录..."
mkdir -p "$CERTS_DIR"

# 生成OpenSSL配置文件
log_info "生成OpenSSL配置文件..."
cat > "$CONFIG_FILE" << 'EOF'
[req]
default_bits = 2048
default_md = sha256
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = CN
ST = Beijing
L = Beijing
O = Athena Platform
OU = Gateway Team
CN = localhost

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = *.localhost
DNS.3 = 127.0.0.1
IP.1 = 127.0.0.1
IP.2 = ::1
EOF

# 生成私钥
log_info "生成私钥..."
openssl genrsa -out "$KEY_FILE" 2048

# 生成证书签名请求（CSR）
log_info "生成证书签名请求（CSR）..."
openssl req -new -key "$KEY_FILE" -out "$CSR_FILE" -config "$CONFIG_FILE"

# 生成自签名证书（有效期1年）
log_info "生成自签名证书（有效期365天）..."
openssl x509 -req -days 365 -in "$CSR_FILE" -signkey "$KEY_FILE" -out "$CERT_FILE" \
    -extensions v3_req -extfile "$CONFIG_FILE"

# 清理CSR文件
rm -f "$CSR_FILE"

# 设置权限
chmod 600 "$KEY_FILE"
chmod 644 "$CERT_FILE"

# 验证证书
log_info "验证证书..."
openssl x509 -in "$CERT_FILE" -text -noout | grep -E "(Subject:|Issuer:|Not Before|Not After|DNS:|IP Address:)"

log_info "✅ TLS证书生成完成！"
log_warn "⚠️  注意：这是自签名证书，仅用于测试环境"
log_warn "⚠️  生产环境请使用CA签发的证书"

echo ""
echo "证书文件位置:"
echo "  证书: $CERT_FILE"
echo "  私钥: $KEY_FILE"
echo ""
echo "使用方法:"
echo "  在config.yaml中配置:"
echo "  tls:"
echo "    enabled: true"
echo "    cert_file: $CERT_FILE"
echo "    key_file: $KEY_FILE"
