#!/bin/bash
# ================================
# Athena API Gateway - 密钥管理脚本
# ================================
# 生产环境安全密钥生成和管理
set -euo pipefail

# 配置变量
NAMESPACE=${NAMESPACE:-"athena-gateway"}
SECRET_NAME=${SECRET_NAME:-"athena-gateway-secrets"}
KEY_LENGTH=${KEY_LENGTH:-32}
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
    log "检查依赖工具..."
    
    command -v openssl >/dev/null 2>&1 || error "OpenSSL 未安装"
    command -v kubectl >/dev/null 2>&1 || error "kubectl 未安装"
    command -v base64 >/dev/null 2>&1 || error "base64 未安装"
    
    success "依赖检查完成"
}

# 生成随机密钥
generate_random_key() {
    local length=${1:-$KEY_LENGTH}
    openssl rand -base64 "$length" | tr -d '\n'
}

# 生成JWT密钥
generate_jwt_secret() {
    log "生成JWT密钥..."
    generate_random_key 64
}

# 生成数据库密码
generate_db_password() {
    log "生成数据库密码..."
    generate_random_key 32
}

# 生成Redis密码
generate_redis_password() {
    log "生成Redis密码..."
    generate_random_key 32
}

# 生成加密密钥
generate_encryption_key() {
    log "生成加密密钥..."
    generate_random_key 64
}

# 生成API密钥
generate_api_key() {
    log "生成API密钥..."
    openssl rand -hex 32
}

# 生成TLS证书 (自签名，生产环境应使用CA证书)
generate_tls_cert() {
    log "生成TLS证书..."
    
    local temp_dir=$(mktemp -d)
    local key_file="${temp_dir}/server.key"
    local cert_file="${temp_dir}/server.crt"
    
    # 生成私钥
    openssl genrsa -out "$key_file" 2048
    
    # 生成证书
    openssl req -new -x509 -key "$key_file" -out "$cert_file" -days 365 \
        -subj "/C=CN/ST=Beijing/L=Beijing/O=Athena/OU=Platform/CN=athena-gateway.company.com"
    
    local key_b64=$(base64 -w 0 "$key_file")
    local cert_b64=$(base64 -w 0 "$cert_file")
    
    rm -rf "$temp_dir"
    
    echo "${key_b64}|${cert_b64}"
}

# 生成Prometheus令牌
generate_prometheus_token() {
    log "生成Prometheus令牌..."
    generate_random_key 32
}

# 生成Jaeger令牌
generate_jaeger_token() {
    log "生成Jaeger令牌..."
    generate_random_key 32
}

# 生成OAuth客户端密钥
generate_oauth_secret() {
    log "生成OAuth客户端密钥..."
    generate_random_key 64
}

# 生成Webhook密钥
generate_webhook_secret() {
    log "生成Webhook密钥..."
    generate_random_key 64
}

# 创建密钥
create_secrets() {
    log "创建Kubernetes密钥..."
    
    # 生成所有密钥
    local jwt_secret=$(generate_jwt_secret)
    local db_password=$(generate_db_password)
    local redis_password=$(generate_redis_password)
    local encryption_key=$(generate_encryption_key)
    local api_key=$(generate_api_key)
    
    # 生成TLS证书
    local tls_result=$(generate_tls_cert)
    local tls_key=$(echo "$tls_result" | cut -d'|' -f1)
    local tls_cert=$(echo "$tls_result" | cut -d'|' -f2)
    
    # 生成监控令牌
    local prometheus_token=$(generate_prometheus_token)
    local jaeger_token=$(generate_jaeger_token)
    
    # 生成外部服务密钥
    local oauth_secret=$(generate_oauth_secret)
    local webhook_secret=$(generate_webhook_secret)
    
    # 创建数据库连接字符串
    local db_url="postgres://athena_user:${db_password}@postgres-primary.database.svc.cluster.local:5432/athena_gateway?sslmode=require"
    local db_url_b64=$(echo -n "$db_url" | base64 -w 0)
    
    # 创建密钥YAML
    cat > secrets-temp.yaml << 'EOF'
apiVersion: v1
kind: Secret
metadata:
  name: ${SECRET_NAME}
  namespace: ${NAMESPACE}
  labels:
    app: athena-gateway
    tier: frontend
    environment: ${ENVIRONMENT}
  annotations:
    generated-by: "athena-secrets-generator"
    generated-at: "$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
    rotation-required: "true"
type: Opaque
data:
  # JWT 密钥
  jwt-secret-key: $(echo -n "$jwt_secret" | base64 -w 0)
  
  # Redis 密码
  redis-password: $(echo -n "$redis_password" | base64 -w 0)
  
  # 数据库密码
  db-password: $(echo -n "$db_password" | base64 -w 0)
  
  # 数据库连接字符串
  database-url: ${db_url_b64}
  
  # 加密密钥
  encryption-key: $(echo -n "$encryption_key" | base64 -w 0)
  
  # API 密钥
  api-key: $(echo -n "$api_key" | base64 -w 0)
  
  # TLS 证书
  tls-key: ${tls_key}
  tls-crt: ${tls_cert}
  
  # 监控令牌
  prometheus-token: $(echo -n "$prometheus_token" | base64 -w 0)
  jaeger-token: $(echo -n "$jaeger_token" | base64 -w 0)
  
  # 外部服务密钥
  oauth-client-secret: $(echo -n "$oauth_secret" | base64 -w 0)
  webhook-secret: $(echo -n "$webhook_secret" | base64 -w 0)
EOF
    
    # 应用密钥
    kubectl apply -f secrets-temp.yaml
    
    # 清理临时文件
    rm -f secrets-temp.yaml
    
    success "密钥创建完成"
}

# 保存密钥备份
backup_secrets() {
    log "备份密钥信息..."
    
    local backup_file="secrets-backup-$(date +%Y%m%d-%H%M%S).txt"
    
    # 创建备份目录
    mkdir -p secrets-backup
    
    # 导出现有密钥 (注意：这包含敏感信息，请安全存储)
    kubectl get secret "${SECRET_NAME}" -n "${NAMESPACE}" -o json > "secrets-backup/${backup_file}"
    
    # 创建可读的备份文件
    cat > "secrets-backup/${backup_file}.readable" << EOF
# Athena API Gateway 密钥备份
# 生成时间: $(date)
# 环境: ${ENVIRONMENT}
# 命名空间: ${NAMESPACE}

# 重要警告：此文件包含敏感信息，请安全存储！

# 获取密钥命令：
kubectl get secret ${SECRET_NAME} -n ${NAMESPACE} -o yaml

# 解码密钥示例：
kubectl get secret ${SECRET_NAME} -n ${NAMESPACE} -o jsonpath='{.data.jwt-secret-key}' | base64 -d

# 备份文件位置: secrets-backup/${backup_file}
EOF
    
    success "密钥备份完成: secrets-backup/${backup_file}.readable"
}

# 验证密钥
verify_secrets() {
    log "验证密钥..."
    
    # 检查密钥是否存在
    if ! kubectl get secret "${SECRET_NAME}" -n "${NAMESPACE}" >/dev/null 2>&1; then
        error "密钥 ${SECRET_NAME} 不存在"
    fi
    
    # 检查必要的密钥字段
    local required_keys=(
        "jwt-secret-key"
        "redis-password" 
        "db-password"
        "database-url"
        "encryption-key"
        "api-key"
        "tls-key"
        "tls-crt"
    )
    
    for key in "${required_keys[@]}"; do
        if ! kubectl get secret "${SECRET_NAME}" -n "${NAMESPACE}" -o "jsonpath={.data.${key}}" | grep -q .; then
            error "密钥字段 ${key} 不存在"
        fi
    done
    
    success "密钥验证完成"
}

# 轮换密钥
rotate_secrets() {
    log "轮换密钥..."
    
    # 备份当前密钥
    backup_secrets
    
    # 生成新密钥
    create_secrets
    
    # 验证新密钥
    verify_secrets
    
    success "密钥轮换完成"
}

# 显示密钥状态
show_status() {
    log "显示密钥状态..."
    
    echo "===================="
    echo "密钥状态报告"
    echo "===================="
    echo "命名空间: ${NAMESPACE}"
    echo "密钥名称: ${SECRET_NAME}"
    echo "环境: ${ENVIRONMENT}"
    echo "时间: $(date)"
    echo ""
    
    # 检查密钥是否存在
    if kubectl get secret "${SECRET_NAME}" -n "${NAMESPACE}" >/dev/null 2>&1; then
        echo "状态: ✅ 存在"
        echo "创建时间: $(kubectl get secret ${SECRET_NAME} -n ${NAMESPACE} -o jsonpath='{.metadata.creationTimestamp}')"
        echo ""
        
        # 显示密钥字段
        echo "密钥字段:"
        kubectl get secret "${SECRET_NAME}" -n "${NAMESPACE}" -o jsonpath='{range .data[*]}{.}{"\n"}{end}' | wc -l | xargs echo "  - 总字段数:"
        echo ""
        
        # 显示最近的备份
        echo "最近的备份:"
        ls -lt secrets-backup/ | head -5 | grep -v "^total"
    else
        echo "状态: ❌ 不存在"
        echo ""
        echo "建议运行: $0 create"
    fi
}

# 主函数
main() {
    local action=${1:-"status"}
    
    case "$action" in
        "create")
            check_dependencies
            create_secrets
            verify_secrets
            backup_secrets
            ;;
        "rotate")
            check_dependencies
            rotate_secrets
            ;;
        "verify")
            check_dependencies
            verify_secrets
            ;;
        "backup")
            check_dependencies
            backup_secrets
            ;;
        "status")
            check_dependencies
            show_status
            ;;
        *)
            echo "使用方法: $0 {create|rotate|verify|backup|status}"
            echo ""
            echo "命令说明:"
            echo "  create  - 创建新的密钥"
            echo "  rotate  - 轮换现有密钥"
            echo "  verify  - 验证密钥完整性"
            echo "  backup  - 备份密钥"
            echo "  status  - 显示密钥状态"
            exit 1
            ;;
    esac
}

# 错误处理
trap 'error "密钥管理过程中发生错误，退出码: $?"' ERR

# 执行主函数
main "$@"