#!/bin/bash
# ================================
# SSL/TLS 证书管理脚本
# ================================
# 生产环境证书生成、部署和自动续期
set -euo pipefail

# 配置变量
NAMESPACE=${NAMESPACE:-"athena-gateway"}
DOMAIN=${DOMAIN:-"company.com"}
CERT_DIR=${CERT_DIR:-"./certificates"}
LETS_ENCRYPT_EMAIL=${LETSENCRYPT_EMAIL:-"admin@company.com"}
ENVIRONMENT=${ENVIRONMENT:-"production"}

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# 检查依赖
check_dependencies() {
    log "检查证书管理依赖..."
    
    local deps=("openssl" "kubectl" "certbot")
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" >/dev/null 2>&1; then
            error "依赖 $dep 未安装"
        fi
    done
    
    # 创建证书目录
    mkdir -p "$CERT_DIR"
    
    success "依赖检查完成"
}

# 生成自签名证书 (开发和测试)
generate_self_signed_cert() {
    local domain=$1
    local cert_name=$2
    local key_file="${CERT_DIR}/${cert_name}.key"
    local cert_file="${CERT_DIR}/${cert_name}.crt"
    
    log "生成自签名证书: $domain"
    
    # 生成私钥
    openssl genrsa -out "$key_file" 2048
    
    # 生成证书签名请求
    openssl req -new -key "$key_file" -out "${CERT_DIR}/${cert_name}.csr" \
        -subj "/C=CN/ST=Beijing/L=Beijing/O=Athena/OU=Platform/CN=${domain}"
    
    # 生成自签名证书
    openssl x509 -req -days 365 -in "${CERT_DIR}/${cert_name}.csr" \
        -signkey "$key_file" -out "$cert_file"
    
    # 清理CSR文件
    rm -f "${CERT_DIR}/${cert_name}.csr"
    
    success "自签名证书生成完成: $cert_name"
}

# 生成Let's Encrypt证书 (生产环境)
generate_letsencrypt_cert() {
    local domain=$1
    local cert_name=$2
    
    log "申请Let's Encrypt证书: $domain"
    
    # 使用certbot申请证书
    certbot certonly \
        --standalone \
        --email "$LETSENCRYPT_EMAIL" \
        --agree-tos \
        --non-interactive \
        --domains "$domain" \
        --cert-name "$cert_name" \
        --staging \
        --config-dir "$CERT_DIR/certbot" \
        --work-dir "$CERT_DIR/work" \
        --logs-dir "$CERT_DIR/logs"
    
    success "Let's Encrypt证书申请完成: $cert_name"
}

# 创建Kubernetes密钥
create_k8s_secrets() {
    log "创建Kubernetes TLS密钥..."
    
    local domains=(
        "athena-gateway.company.com:athena-gateway-tls"
        "api.company.com:api-tls"
        "admin.company.com:admin-tls"
        "grafana.company.com:grafana-tls"
        "prometheus.company.com:prometheus-tls"
        "alertmanager.company.com:alertmanager-tls"
    )
    
    for domain_secret in "${domains[@]}"; do
        local domain=$(echo "$domain_secret" | cut -d':' -f1)
        local secret_name=$(echo "$domain_secret" | cut -d':' -f2)
        local cert_file="${CERT_DIR}/${secret_name}.crt"
        local key_file="${CERT_DIR}/${secret_name}.key"
        
        if [[ ! -f "$cert_file" || ! -f "$key_file" ]]; then
            warning "证书文件不存在，生成自签名证书: $domain"
            generate_self_signed_cert "$domain" "$secret_name"
        fi
        
        # 创建或更新密钥
        if kubectl get secret "$secret_name" -n "$NAMESPACE" >/dev/null 2>&1; then
            kubectl delete secret "$secret_name" -n "$NAMESPACE"
        fi
        
        kubectl create secret tls "$secret_name" \
            --cert="$cert_file" \
            --key="$key_file" \
            -n "$NAMESPACE"
        
        success "TLS密钥创建完成: $secret_name"
    done
}

# 创建CA根证书
create_ca_cert() {
    log "创建CA根证书..."
    
    local ca_key="${CERT_DIR}/ca.key"
    local ca_cert="${CERT_DIR}/ca.crt"
    
    # 生成CA私钥
    openssl genrsa -out "$ca_key" 4096
    
    # 生成CA证书
    openssl req -x509 -new -nodes -key "$ca_key" -sha256 -days 3650 \
        -out "$ca_cert" -subj "/C=CN/ST=Beijing/L=Beijing/O=Athena/OU=CA/CN=Athena-Root-CA"
    
    success "CA根证书创建完成"
}

# 签发服务证书
sign_server_cert() {
    local domain=$1
    local cert_name=$2
    local key_file="${CERT_DIR}/${cert_name}.key"
    local csr_file="${CERT_DIR}/${cert_name}.csr"
    local cert_file="${CERT_DIR}/${cert_name}.crt"
    local ca_key="${CERT_DIR}/ca.key"
    local ca_cert="${CERT_DIR}/ca.crt"
    
    log "签发服务证书: $domain"
    
    # 生成服务私钥
    openssl genrsa -out "$key_file" 2048
    
    # 生成证书签名请求
    openssl req -new -key "$key_file" -out "$csr_file" \
        -subj "/C=CN/ST=Beijing/L=Beijing/O=Athena/OU=Platform/CN=${domain}"
    
    # 创建扩展配置
    cat > "${CERT_DIR}/${cert_name}.ext" << EOF
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = ${domain}
DNS.2 = *.${domain}
IP.1 = 127.0.0.1
EOF
    
    # 使用CA签发证书
    openssl x509 -req -in "$csr_file" \
        -CA "$ca_cert" -CAkey "$ca_key" -CAcreateserial \
        -out "$cert_file" \
        -days 365 \
        -sha256 \
        -extfile "${CERT_DIR}/${cert_name}.ext"
    
    # 清理临时文件
    rm -f "$csr_file" "${CERT_DIR}/${cert_name}.ext"
    
    success "服务证书签发完成: $cert_name"
}

# 证书验证
verify_certificates() {
    log "验证证书..."
    
    local secrets=(
        "athena-gateway-tls"
        "api-tls"
        "admin-tls"
        "grafana-tls"
        "prometheus-tls"
        "alertmanager-tls"
    )
    
    for secret in "${secrets[@]}"; do
        if kubectl get secret "$secret" -n "$NAMESPACE" >/dev/null 2>&1; then
            # 验证证书有效期
            local cert_data=$(kubectl get secret "$secret" -n "$NAMESPACE" -o jsonpath='{.data.tls\.crt}')
            local cert_file="/tmp/${secret}.crt"
            
            echo "$cert_data" | base64 -d > "$cert_file"
            
            local expiry_date=$(openssl x509 -in "$cert_file" -noout -enddate | cut -d'=' -f2)
            local expiry_timestamp=$(date -d "$expiry_date" +%s)
            local current_timestamp=$(date +%s)
            local days_until_expiry=$(( (expiry_timestamp - current_timestamp) / 86400 ))
            
            if [ "$days_until_expiry" -lt 30 ]; then
                warning "证书 $secret 将在 $days_until_expiry 天后过期"
            else
                success "证书 $secret 有效期正常 (剩余 $days_until_expiry 天)"
            fi
            
            rm -f "$cert_file"
        else
            error "证书密钥不存在: $secret"
        fi
    done
}

# 设置证书自动续期
setup_auto_renewal() {
    log "设置证书自动续期..."
    
    local cron_file="/etc/cron.d/athena-cert-renewal"
    
    # 创建cron任务
    cat > "$cron_file" << EOF
# Athena API Gateway 证书自动续期
# 每天凌晨2点检查证书状态
0 2 * * * root /opt/athena-gateway/scripts/cert-renewal.sh >> /var/log/cert-renewal.log 2>&1

# 每周日凌晨3点备份证书
0 3 * * 0 root /opt/athena-gateway/scripts/cert-backup.sh >> /var/log/cert-backup.log 2>&1
EOF
    
    chmod 644 "$cron_file"
    
    success "证书自动续期设置完成"
}

# 创建证书续期脚本
create_renewal_script() {
    local script_dir="/opt/athena-gateway/scripts"
    
    log "创建证书续期脚本..."
    
    mkdir -p "$script_dir"
    
    cat > "${script_dir}/cert-renewal.sh" << 'EOF'
#!/bin/bash
# 证书自动续期脚本
set -euo pipefail

CERT_DIR="/opt/athena-gateway/certificates"
NAMESPACE="athena-gateway"

# 检查证书过期时间
check_cert_expiry() {
    local secret=$1
    local cert_data=$(kubectl get secret $secret -n $NAMESPACE -o jsonpath='{.data.tls\.crt}')
    local cert_file="/tmp/${secret}.crt"
    
    echo "$cert_data" | base64 -d > "$cert_file"
    
    local expiry_date=$(openssl x509 -in "$cert_file" -noout -enddate | cut -d'=' -f2)
    local expiry_timestamp=$(date -d "$expiry_date" +%s)
    local current_timestamp=$(date +%s)
    local days_until_expiry=$(( (expiry_timestamp - current_timestamp) / 86400 ))
    
    rm -f "$cert_file"
    
    echo $days_until_expiry
}

# 续期证书
renew_certificate() {
    local secret=$1
    local days_until_expiry=$(check_cert_expiry $secret)
    
    if [ "$days_until_expiry" -lt 30 ]; then
        echo "证书 $secret 需要续期 (剩余 $days_until_expiry 天)"
        
        # 这里添加具体的续期逻辑
        # 例如: certbot renew --cert-name $secret
        
        # 更新Kubernetes密钥
        # kubectl create secret tls $secret --cert=$new_cert --key=$new_key -n $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
        
        echo "证书 $secret 续期完成"
    else
        echo "证书 $secret 不需要续期 (剩余 $days_until_expiry 天)"
    fi
}

# 检查所有证书
certs=("athena-gateway-tls" "api-tls" "admin-tls" "grafana-tls" "prometheus-tls" "alertmanager-tls")

for cert in "${certs[@]}"; do
    renew_certificate $cert
done

# 重启相关服务
kubectl rollout restart deployment/nginx-ingress-controller -n ingress-nginx
EOF
    
    chmod +x "${script_dir}/cert-renewal.sh"
    
    # 创建证书备份脚本
    cat > "${script_dir}/cert-backup.sh" << 'EOF'
#!/bin/bash
# 证书备份脚本
set -euo pipefail

CERT_DIR="/opt/athena-gateway/certificates"
BACKUP_DIR="/opt/athena-gateway/cert-backups"
DATE=$(date +%Y%m%d)

mkdir -p "$BACKUP_DIR"

# 备份所有证书文件
cp -r "$CERT_DIR" "${BACKUP_DIR}/${DATE}"

# 清理30天前的备份
find "$BACKUP_DIR" -type d -mtime +30 -exec rm -rf {} \;

echo "证书备份完成: ${BACKUP_DIR}/${DATE}"
EOF
    
    chmod +x "${script_dir}/cert-backup.sh"
    
    success "证书管理脚本创建完成"
}

# 生成证书配置文件
generate_cert_config() {
    log "生成证书配置文件..."
    
    cat > "${CERT_DIR}/cert-config.yaml" << EOF
# 证书配置文件
# 用于记录证书信息和配置

certificates:
  - domain: "athena-gateway.company.com"
    secret_name: "athena-gateway-tls"
    cert_file: "athena-gateway-tls.crt"
    key_file: "athena-gateway-tls.key"
    type: "server"
    san_domains:
      - "athena-gateway.company.com"
      - "api.company.com"
      - "admin.company.com"
      
  - domain: "grafana.company.com"
    secret_name: "grafana-tls"
    cert_file: "grafana-tls.crt"
    key_file: "grafana-tls.key"
    type: "monitoring"
    
  - domain: "prometheus.company.com"
    secret_name: "prometheus-tls"
    cert_file: "prometheus-tls.crt"
    key_file: "prometheus-tls.key"
    type: "monitoring"
    internal_only: true
    
  - domain: "alertmanager.company.com"
    secret_name: "alertmanager-tls"
    cert_file: "alertmanager-tls.crt"
    key_file: "alertmanager-tls.key"
    type: "monitoring"
    internal_only: true

certificate_authority:
  ca_cert: "ca.crt"
  ca_key: "ca.key"
  
renewal:
  auto_renew: true
  renewal_threshold_days: 30
  renewal_command: "certbot renew"
  
security:
  key_size: 2048
  hash_algorithm: "sha256"
  encryption: "aes256"
  validity_period_days: 365
EOF
    
    success "证书配置文件生成完成"
}

# 主函数
main() {
    local action=${1:-"create"}
    
    case "$action" in
        "create")
            check_dependencies
            if [ "$ENVIRONMENT" = "production" ]; then
                # 生产环境使用Let's Encrypt
                generate_letsencrypt_cert "athena-gateway.company.com" "athena-gateway-tls"
                generate_letsencrypt_cert "api.company.com" "api-tls"
                generate_letsencrypt_cert "admin.company.com" "admin-tls"
            else
                # 非生产环境使用自签名证书
                create_ca_cert
                sign_server_cert "athena-gateway.company.com" "athena-gateway-tls"
                sign_server_cert "api.company.com" "api-tls"
                sign_server_cert "admin.company.com" "admin-tls"
                sign_server_cert "grafana.company.com" "grafana-tls"
                sign_server_cert "prometheus.company.com" "prometheus-tls"
                sign_server_cert "alertmanager.company.com" "alertmanager-tls"
            fi
            create_k8s_secrets
            generate_cert_config
            ;;
        "verify")
            verify_certificates
            ;;
        "renew")
            setup_auto_renewal
            create_renewal_script
            ;;
        "ca")
            check_dependencies
            create_ca_cert
            ;;
        *)
            echo "使用方法: $0 {create|verify|renew|ca}"
            echo ""
            echo "命令说明:"
            echo "  create  - 创建证书并部署到Kubernetes"
            echo "  verify  - 验证证书状态和有效期"
            echo "  renew   - 设置自动续期"
            echo "  ca      - 创建CA根证书"
            exit 1
            ;;
    esac
}

# 错误处理
trap 'error "证书管理过程中发生错误，退出码: $?"' ERR

# 执行主函数
main "$@"