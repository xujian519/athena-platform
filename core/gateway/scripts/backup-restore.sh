#!/bin/bash
# ================================
# Athena API Gateway - 备份恢复系统
# ================================
# 生产环境数据备份和恢复管理
set -euo pipefail

# 配置变量
NAMESPACE=${NAMESPACE:-"athena-gateway"}
BACKUP_DIR=${BACKUP_DIR:-"/opt/backups/athena-gateway"}
S3_BUCKET=${S3_BUCKET:-"athena-backups"}
RETENTION_DAYS=${RETENTION_DAYS:-30}
ENVIRONMENT=${ENVIRONMENT:-"production"}
POSTGRES_HOST=${POSTGRES_HOST:-"your-postgres-host.local"}

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
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

info() {
    echo -e "${PURPLE}[INFO]${NC} $1"
}

# 检查依赖
check_dependencies() {
    log "检查备份系统依赖..."
    
    local deps=("kubectl" "aws" "pg_dump" "redis-cli")
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" >/dev/null 2>&1; then
            error "依赖 $dep 未安装"
        fi
    done
    
    # 创建备份目录
    mkdir -p "$BACKUP_DIR"
    mkdir -p "${BACKUP_DIR}/kubernetes"
    mkdir -p "${BACKUP_DIR}/database"
    mkdir -p "${BACKUP_DIR}/redis"
    mkdir -p "${BACKUP_DIR}/configs"
    mkdir -p "${BACKUP_DIR}/logs"
    
    success "依赖检查完成"
}

# Kubernetes资源备份
backup_kubernetes_resources() {
    log "备份Kubernetes资源..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_dir="${BACKUP_DIR}/kubernetes/${timestamp}"
    
    mkdir -p "$backup_dir"
    
    # 备份命名空间
    kubectl get namespace "$NAMESPACE" -o yaml > "${backup_dir}/namespace.yaml"
    
    # 备份ConfigMaps
    kubectl get configmaps -n "$NAMESPACE" -o yaml > "${backup_dir}/configmaps.yaml"
    
    # 备份Secrets (不包含敏感数据)
    kubectl get secrets -n "$NAMESPACE" -o yaml > "${backup_dir}/secrets.yaml"
    
    # 备份Deployments
    kubectl get deployments -n "$NAMESPACE" -o yaml > "${backup_dir}/deployments.yaml"
    
    # 备份Services
    kubectl get services -n "$NAMESPACE" -o yaml > "${backup_dir}/services.yaml"
    
    # 备份Ingress
    kubectl get ingress -n "$NAMESPACE" -o yaml > "${backup_dir}/ingress.yaml"
    
    # 备份HPA
    kubectl get hpa -n "$NAMESPACE" -o yaml > "${backup_dir}/hpa.yaml"
    
    # 备份PVC
    kubectl get pvc -n "$NAMESPACE" -o yaml > "${backup_dir}/pvc.yaml"
    
    # 打包备份
    cd "$BACKUP_DIR/kubernetes"
    tar -czf "${timestamp}.tar.gz" "$timestamp"
    rm -rf "$timestamp"
    cd - >/dev/null
    
    success "Kubernetes资源备份完成: ${timestamp}.tar.gz"
}

# PostgreSQL数据库备份
backup_postgresql() {
    log "备份PostgreSQL数据库..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="${BACKUP_DIR}/database/postgres_backup_${timestamp}.sql"
    local compressed_file="${backup_file}.gz"
    
    # 执行数据库备份
    PGPASSWORD="$DB_PASSWORD" pg_dump \
        -h "$POSTGRES_HOST" \
        -U athena_user \
        -d athena_gateway \
        --no-password \
        --verbose \
        --format=custom \
        --compress=9 \
        --file="$backup_file" \
        --lock-wait-timeout=30000
    
    # 压缩备份文件
    gzip "$backup_file"
    
    # 验证备份完整性
    if [[ -f "$compressed_file" && -s "$compressed_file" ]]; then
        success "PostgreSQL备份完成: $(basename $compressed_file)"
        
        # 计算备份文件大小
        local file_size=$(du -h "$compressed_file" | cut -f1)
        info "备份文件大小: $file_size"
    else
        error "PostgreSQL备份失败"
    fi
}

# Redis数据备份
backup_redis() {
    log "备份Redis数据..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="${BACKUP_DIR}/redis/redis_backup_${timestamp}.rdb"
    local aof_file="${BACKUP_DIR}/redis/redis_appendonly_${timestamp}.aof"
    
    # 获取Redis主节点信息
    local redis_pod=$(kubectl get pods -n cache -l app=redis,role=master -o jsonpath='{.items[0].metadata.name}')
    
    # 触发Redis保存
    kubectl exec -n cache "$redis_pod" -- redis-cli BGSAVE
    
    # 等待保存完成
    sleep 10
    
    # 复制RDB文件
    kubectl cp "cache/${redis_pod}:/data/dump.rdb" "$backup_file"
    
    # 复制AOF文件 (如果存在)
    if kubectl exec -n cache "$redis_pod" -- test -f /data/appendonly.aof; then
        kubectl cp "cache/${redis_pod}:/data/appendonly.aof" "$aof_file"
    fi
    
    # 压缩备份文件
    tar -czf "${backup_file}.tar.gz" -C "$(dirname "$backup_file")" "$(basename "$backup_file")"
    rm -f "$backup_file"
    
    if [[ -f "${aof_file}" ]]; then
        tar -czf "${aof_file}.tar.gz" -C "$(dirname "$aof_file")" "$(basename "$aof_file")"
        rm -f "$aof_file"
        success "Redis备份完成: $(basename ${aof_file}.tar.gz) 和 $(basename ${backup_file}.tar.gz)"
    else
        success "Redis备份完成: $(basename ${backup_file}.tar.gz)"
    fi
}

# 应用配置备份
backup_configs() {
    log "备份应用配置..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local config_backup_dir="${BACKUP_DIR}/configs/${timestamp}"
    
    mkdir -p "$config_backup_dir"
    
    # 备份ConfigMaps
    kubectl get configmaps -n "$NAMESPACE" -o yaml > "${config_backup_dir}/configmaps.yaml"
    
    # 备份当前运行的配置
    local gateway_pod=$(kubectl get pods -n "$NAMESPACE" -l app=athena-gateway -o jsonpath='{.items[0].metadata.name}')
    
    if [[ -n "$gateway_pod" ]]; then
        kubectl exec -n "$NAMESPACE" "$gateway_pod" -- cat /app/configs/production.yaml > "${config_backup_dir}/current-config.yaml"
    fi
    
    # 打包配置备份
    cd "$BACKUP_DIR/configs"
    tar -czf "${timestamp}.tar.gz" "$timestamp"
    rm -rf "$timestamp"
    cd - >/dev/null
    
    success "配置备份完成: ${timestamp}.tar.gz"
}

# 日志备份
backup_logs() {
    log "备份应用日志..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local log_backup_dir="${BACKUP_DIR}/logs/${timestamp}"
    
    mkdir -p "$log_backup_dir"
    
    # 收集所有Pod的日志
    local pods=$(kubectl get pods -n "$NAMESPACE" -l app=athena-gateway -o jsonpath='{.items[*].metadata.name}')
    
    for pod in $pods; do
        kubectl logs "$pod" -n "$NAMESPACE" --since=24h > "${log_backup_dir}/${pod}.log" 2>/dev/null || true
    done
    
    # 打包日志备份
    cd "$BACKUP_DIR/logs"
    tar -czf "${timestamp}.tar.gz" "$timestamp"
    rm -rf "$timestamp"
    cd - >/dev/null
    
    success "日志备份完成: ${timestamp}.tar.gz"
}

# S3上传备份
upload_to_s3() {
    log "上传备份到S3..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    
    # 上传各种备份类型
    local backup_types=("kubernetes" "database" "redis" "configs" "logs")
    
    for backup_type in "${backup_types[@]}"; do
        local backup_path="${BACKUP_DIR}/${backup_type}"
        
        if [[ -d "$backup_path" ]]; then
            # 上传最新备份文件
            find "$backup_path" -name "*.tar.gz" -mmin -60 -exec aws s3 cp {} "s3://${S3_BUCKET}/${backup_type}/" \;
            find "$backup_path" -name "*.sql.gz" -mmin -60 -exec aws s3 cp {} "s3://${S3_BUCKET}/${backup_type}/" \;
            
            success "$backup_type 备份已上传到S3"
        fi
    done
    
    # 创建备份清单
    local manifest_file="${BACKUP_DIR}/backup_manifest_${timestamp}.json"
    cat > "$manifest_file" << EOF
{
  "backup_timestamp": "$(date -u +'%Y-%m-%dT%H:%M:%SZ')",
  "environment": "$ENVIRONMENT",
  "namespace": "$NAMESPACE",
  "backups": {
    "kubernetes": "$(find ${BACKUP_DIR}/kubernetes -name '*.tar.gz' -mmin -60 | head -1 | xargs basename)",
    "database": "$(find ${BACKUP_DIR}/database -name '*.sql.gz' -mmin -60 | head -1 | xargs basename)",
    "redis": "$(find ${BACKUP_DIR}/redis -name '*.tar.gz' -mmin -60 | head -1 | xargs basename)",
    "configs": "$(find ${BACKUP_DIR}/configs -name '*.tar.gz' -mmin -60 | head -1 | xargs basename)",
    "logs": "$(find ${BACKUP_DIR}/logs -name '*.tar.gz' -mmin -60 | head -1 | xargs basename)"
  },
  "s3_bucket": "$S3_BUCKET",
  "retention_days": $RETENTION_DAYS
}
EOF
    
    aws s3 cp "$manifest_file" "s3://${S3_BUCKET}/manifests/"
    
    success "备份清单已上传到S3"
}

# 清理旧备份
cleanup_old_backups() {
    log "清理旧备份文件..."
    
    local cleanup_date=$(date -d "${RETENTION_DAYS} days ago" +%Y%m%d)
    
    # 清理本地备份
    for backup_type in "kubernetes" "database" "redis" "configs" "logs"; do
        local backup_path="${BACKUP_DIR}/${backup_type}"
        
        if [[ -d "$backup_path" ]]; then
            find "$backup_path" -name "*.tar.gz" -type f -mtime +${RETENTION_DAYS} -delete
            find "$backup_path" -name "*.sql.gz" -type f -mtime +${RETENTION_DAYS} -delete
        fi
    done
    
    # 清理S3备份
    aws s3 ls "s3://${S3_BUCKET}/" --recursive | while read -r line; do
        local file_date=$(echo "$line" | awk '{print $1}' | cut -d'/' -f2)
        if [[ "$file_date" < "$cleanup_date" ]]; then
            aws s3 rm "s3://${S3_BUCKET}/$file_date" --recursive
        fi
    done
    
    success "旧备份清理完成"
}

# 数据库恢复
restore_postgresql() {
    local backup_file=$1
    
    log "恢复PostgreSQL数据库..."
    
    if [[ ! -f "$backup_file" ]]; then
        error "备份文件不存在: $backup_file"
    fi
    
    # 解压备份文件
    local uncompressed_file="${backup_file%.gz}"
    if [[ "$backup_file" == *.gz ]]; then
        gunzip -c "$backup_file" > "$uncompressed_file"
        backup_file="$uncompressed_file"
    fi
    
    # 执行数据库恢复
    PGPASSWORD="$DB_PASSWORD" psql \
        -h "$POSTGRES_HOST" \
        -U athena_user \
        -d athena_gateway \
        -f "$backup_file" \
        -v ON_ERROR_STOP=1
    
    success "PostgreSQL数据库恢复完成"
    
    # 清理临时文件
    rm -f "$uncompressed_file"
}

# Redis恢复
restore_redis() {
    local backup_file=$1
    
    log "恢复Redis数据..."
    
    if [[ ! -f "$backup_file" ]]; then
        error "备份文件不存在: $backup_file"
    fi
    
    # 获取Redis主节点Pod
    local redis_pod=$(kubectl get pods -n cache -l app=redis,role=master -o jsonpath='{.items[0].metadata.name}')
    
    # 解压备份文件到Pod
    kubectl cp "$backup_file" "cache/${redis_pod}:/tmp/restore_data.tar.gz"
    
    # 停止Redis服务
    kubectl exec -n cache "$redis_pod" -- redis-cli SHUTDOWN NOSAVE
    
    # 恢复数据文件
    kubectl exec -n cache "$redis_pod" -- tar -xzf /tmp/restore_data.tar.gz -C /data/
    
    # 重启Redis服务
    kubectl delete pod "$redis_pod" -n cache --wait=false
    kubectl wait --for=condition=ready pod -l app=redis,role=master -n cache --timeout=300s
    
    success "Redis数据恢复完成"
}

# Kubernetes资源恢复
restore_kubernetes_resources() {
    local backup_dir=$1
    
    log "恢复Kubernetes资源..."
    
    if [[ ! -d "$backup_dir" ]]; then
        error "备份目录不存在: $backup_dir"
    fi
    
    # 恢复资源
    kubectl apply -f "${backup_dir}/namespace.yaml" --wait=false
    kubectl apply -f "${backup_dir}/configmaps.yaml" -n "$NAMESPACE"
    kubectl apply -f "${backup_dir}/deployments.yaml" -n "$NAMESPACE"
    kubectl apply -f "${backup_dir}/services.yaml" -n "$NAMESPACE"
    kubectl apply -f "${backup_dir}/ingress.yaml" -n "$NAMESPACE"
    kubectl apply -f "${backup_dir}/hpa.yaml" -n "$NAMESPACE"
    
    # 等待部署完成
    kubectl wait --for=condition=available deployment --all -n "$NAMESPACE" --timeout=600s
    
    success "Kubernetes资源恢复完成"
}

# 备份验证
verify_backup() {
    local backup_file=$1
    local backup_type=$2
    
    log "验证备份完整性..."
    
    case "$backup_type" in
        "postgresql")
            # 验证SQL备份文件
            if gunzip -t "$backup_file" 2>/dev/null; then
                success "PostgreSQL备份文件格式正确"
            else
                error "PostgreSQL备份文件损坏"
            fi
            ;;
        "redis")
            # 验证Redis备份文件
            if tar -tzf "$backup_file" >/dev/null 2>&1; then
                success "Redis备份文件格式正确"
            else
                error "Redis备份文件损坏"
            fi
            ;;
        "kubernetes")
            # 验证K8s资源备份
            if kubectl apply --dry-run=client -f "$backup_file" >/dev/null 2>&1; then
                success "Kubernetes资源备份文件格式正确"
            else
                error "Kubernetes资源备份文件损坏"
            fi
            ;;
    esac
}

# 主函数
main() {
    local action=${1:-"backup"}
    local backup_type=${2:-"all"}
    
    case "$action" in
        "backup")
            check_dependencies
            case "$backup_type" in
                "all")
                    backup_kubernetes_resources
                    backup_postgresql
                    backup_redis
                    backup_configs
                    backup_logs
                    upload_to_s3
                    cleanup_old_backups
                    ;;
                "kubernetes")
                    backup_kubernetes_resources
                    ;;
                "database")
                    backup_postgresql
                    ;;
                "redis")
                    backup_redis
                    ;;
                "configs")
                    backup_configs
                    ;;
                "logs")
                    backup_logs
                    ;;
                *)
                    error "未知的备份类型: $backup_type"
                    ;;
            esac
            ;;
        "restore")
            local backup_file=$2
            local restore_type=$3
            
            check_dependencies
            case "$restore_type" in
                "postgresql")
                    restore_postgresql "$backup_file"
                    ;;
                "redis")
                    restore_redis "$backup_file"
                    ;;
                "kubernetes")
                    restore_kubernetes_resources "$backup_file"
                    ;;
                *)
                    error "未知的恢复类型: $restore_type"
                    ;;
            esac
            ;;
        "verify")
            local backup_file=$2
            local backup_type=$3
            
            verify_backup "$backup_file" "$backup_type"
            ;;
        "cleanup")
            cleanup_old_backups
            ;;
        *)
            echo "使用方法: $0 {backup|restore|verify|cleanup} [args...]"
            echo ""
            echo "备份命令:"
            echo "  $0 backup [all|kubernetes|database|redis|configs|logs]"
            echo ""
            echo "恢复命令:"
            echo "  $0 restore <backup_file> <type>"
            echo "  类型: postgresql|redis|kubernetes"
            echo ""
            echo "验证命令:"
            echo "  $0 verify <backup_file> <type>"
            echo ""
            echo "清理命令:"
            echo "  $0 cleanup"
            exit 1
            ;;
    esac
}

# 错误处理
trap 'error "备份恢复过程中发生错误，退出码: $?"' ERR

# 执行主函数
main "$@"