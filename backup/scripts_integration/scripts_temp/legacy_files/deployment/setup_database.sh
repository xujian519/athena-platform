#!/bin/bash
# 生产数据库和缓存配置脚本
# Production Database and Cache Configuration for Athena

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
DB_PRIMARY_HOST="172.20.0.30"
DB_REPLICA_HOST="172.20.0.31"
DB_PORT="5432"
DB_NAME="athena_production"
DB_USER="athena_user"
DB_PASSWORD_FILE="/etc/athena/secrets/db_password"
REPLICATION_USER="replicator"
REPLICATION_PASSWORD_FILE="/etc/athena/secrets/replication_password"

REDIS_CLUSTER_NODES=(
    "172.20.0.40:6379"
    "172.20.0.41:6379"
    "172.20.0.42:6379"
    "172.20.0.43:6379"
    "172.20.0.44:6379"
    "172.20.0.45:6379"
)
REDIS_CACHE_HOST="172.20.0.50"
REDIS_CACHE_PORT="6379"

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

# 检查依赖
check_dependencies() {
    log_info "检查系统依赖..."

    # 检查PostgreSQL
    if ! command -v psql &> /dev/null; then
        log_error "PostgreSQL客户端未安装，请先安装"
        echo "Ubuntu/Debian: sudo apt-get install postgresql-client"
        echo "CentOS/RHEL: sudo yum install postgresql"
        exit 1
    fi

    # 检查Redis
    if ! command -v redis-cli &> /dev/null; then
        log_error "Redis客户端未安装，请先安装"
        echo "Ubuntu/Debian: sudo apt-get install redis-tools"
        echo "CentOS/RHEL: sudo yum install redis"
        exit 1
    fi

    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi

    log_success "依赖检查完成"
}

# 创建目录结构
create_directories() {
    log_info "创建数据库和缓存目录结构..."

    # PostgreSQL目录
    sudo mkdir -p /data/athena/postgres/{primary,replica,backups,logs}
    sudo mkdir -p /etc/athena/postgres/{config,init}

    # Redis目录
    sudo mkdir -p /data/athena/redis/{cluster,cache,logs}
    sudo mkdir -p /etc/athena/redis/{cluster,cache}

    # 密钥目录
    sudo mkdir -p /etc/athena/secrets
    sudo chmod 700 /etc/athena/secrets

    # 设置权限
    sudo chown -R 999:999 /data/athena/postgres
    sudo chown -R 999:999 /data/athena/redis
    sudo chown -R $(whoami):$(whoami) /etc/athena

    log_success "目录结构创建完成"
}

# 生成数据库密码
generate_passwords() {
    log_info "生成数据库密码..."

    # 生成主数据库密码
    if [ ! -f "$DB_PASSWORD_FILE" ]; then
        openssl rand -base64 32 > "$DB_PASSWORD_FILE"
        chmod 600 "$DB_PASSWORD_FILE"
        log_success "主数据库密码已生成: $DB_PASSWORD_FILE"
    else
        log_info "主数据库密码已存在"
    fi

    # 生成复制密码
    if [ ! -f "$REPLICATION_PASSWORD_FILE" ]; then
        openssl rand -base64 32 > "$REPLICATION_PASSWORD_FILE"
        chmod 600 "$REPLICATION_PASSWORD_FILE"
        log_success "复制密码已生成: $REPLICATION_PASSWORD_FILE"
    else
        log_info "复制密码已存在"
    fi
}

# 创建PostgreSQL主节点配置
create_postgres_primary_config() {
    log_info "创建PostgreSQL主节点配置..."

    cat > "/etc/athena/postgres/config/postgresql.conf" << EOF
# PostgreSQL主节点配置 - Athena生产环境

# 连接配置
listen_addresses = '*'
port = ${DB_PORT}
max_connections = 300
superuser_reserved_connections = 3

# 内存配置
shared_buffers = 2GB
effective_cache_size = 6GB
work_mem = 16MB
maintenance_work_mem = 256MB
dynamic_shared_memory_type = posix

# WAL配置
wal_level = replica
max_wal_senders = 10
max_replication_slots = 10
wal_keep_size = 2GB
wal_sender_timeout = 60s
wal_compression = on
wal_log_hints = on

# 检查点配置
checkpoint_completion_target = 0.9
checkpoint_timeout = 15min
max_wal_size = 4GB
min_wal_size = 1GB

# 复制配置
synchronous_commit = on
synchronous_standby_names = 'replica1'
vacuum_defer_cleanup_age = 0

# 日志配置
logging_collector = on
log_destination = 'stderr,csvlog'
log_directory = '/var/log/postgresql'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_rotation_age = 1d
log_rotation_size = 100MB
log_min_messages = warning
log_min_error_statement = error
log_min_duration_statement = 1000
log_checkpoints = on
log_connections = on
log_disconnections = on
log_lock_waits = on
log_temp_files = 10MB

# 性能配置
random_page_cost = 1.1
effective_io_concurrency = 200
max_parallel_workers_per_gather = 4
max_parallel_workers = 8
max_parallel_maintenance_workers = 4
parallel_leader_participation = on

# 自动清理配置
autovacuum = on
autovacuum_max_workers = 4
autovacuum_naptime = 10s
autovacuum_vacuum_threshold = 500
autovacuum_analyze_threshold = 250
autovacuum_vacuum_scale_factor = 0.2
autovacuum_analyze_scale_factor = 0.1

# 安全配置
ssl = on
ssl_cert_file = '/etc/ssl/certs/postgres.crt'
ssl_key_file = '/etc/ssl/private/postgres.key'
ssl_ca_file = '/etc/ssl/certs/ca.crt'

# 扩展配置
shared_preload_libraries = 'pg_stat_statements,auto_explain,pg_prewarm'
track_activity_query_size = 2048
pg_stat_statements.track = all
auto_explain.log_min_duration = 1000
auto_explain.log_analyze = on
auto_explain.log_verbose = on

# 时区配置
timezone = 'Asia/Shanghai'
log_timezone = 'Asia/Shanghai'

# 其他配置
default_text_search_config = 'pg_catalog.english'
escape_string_warning = off
standard_conforming_strings = on
EOF

    # 主节点访问控制
    cat > "/etc/athena/postgres/config/pg_hba.conf" << EOF
# PostgreSQL访问控制配置

# 本地连接
local   all             all                                     trust
host    all             all             127.0.0.1/32            md5
host    all             all             ::1/128                 md5

# 复制连接
host    replication     replicator      172.20.0.0/16           md5
host    replication     replicator      ${DB_REPLICA_HOST}/32    md5

# 应用连接
host    ${DB_NAME}      ${DB_USER}      172.20.0.0/16           md5
host    ${DB_NAME}      ${DB_USER}      0.0.0.0/0               md5

# 监控连接
host    postgres        ${DB_USER}      172.20.0.0/16           md5
host    all             all             172.20.0.0/16           md5

# SSL连接
hostssl ${DB_NAME}      ${DB_USER}      0.0.0.0/0               md5
hostssl all             all             0.0.0.0/0               md5
EOF

    log_success "PostgreSQL主节点配置创建完成"
}

# 创建PostgreSQL从节点配置
create_postgres_replica_config() {
    log_info "创建PostgreSQL从节点配置..."

    cat > "/etc/athena/postgres/config/postgresql-replica.conf" << EOF
# PostgreSQL从节点配置 - Athena生产环境

# 连接配置
listen_addresses = '*'
port = ${DB_PORT}
max_connections = 300
superuser_reserved_connections = 1

# 内存配置
shared_buffers = 2GB
effective_cache_size = 6GB
work_mem = 16MB
maintenance_work_mem = 128MB
dynamic_shared_memory_type = posix

# 复制配置
hot_standby = on
max_standby_archive_delay = 30s
max_standby_streaming_delay = 30s
wal_receiver_create_temp_slot = off
max_replication_slots = 10
hot_standby_feedback = on

# WAL配置
wal_level = replica
wal_compression = on
wal_log_hints = on

# 检查点配置
checkpoint_completion_target = 0.9
checkpoint_timeout = 15min
max_wal_size = 4GB
min_wal_size = 1GB

# 恢复配置
primary_conninfo = 'host=${DB_PRIMARY_HOST} port=${DB_PORT} user=${REPLICATION_USER} passwordfile=/etc/athena/secrets/replication_password application_name=replica1'
recovery_min_apply_delay = '0s'
recovery_target_timeline = 'latest'
standby_mode = on

# 日志配置
logging_collector = on
log_destination = 'stderr,csvlog'
log_directory = '/var/log/postgresql'
log_filename = 'postgresql-replica-%Y-%m-%d_%H%M%S.log'
log_rotation_age = 1d
log_rotation_size = 100MB
log_min_messages = warning
log_min_error_statement = error
log_min_duration_statement = 1000
log_checkpoints = on
log_connections = on
log_disconnections = on
log_lock_waits = on

# 性能配置
random_page_cost = 1.1
effective_io_concurrency = 200
max_parallel_workers_per_gather = 2
max_parallel_workers = 4

# 自动清理配置
autovacuum = on
autovacuum_max_workers = 2
autovacuum_naptime = 15s
autovacuum_vacuum_threshold = 1000
autovacuum_analyze_threshold = 500
autovacuum_vacuum_scale_factor = 0.1
autovacuum_analyze_scale_factor = 0.05

# 安全配置
ssl = on
ssl_cert_file = '/etc/ssl/certs/postgres.crt'
ssl_key_file = '/etc/ssl/private/postgres.key'
ssl_ca_file = '/etc/ssl/certs/ca.crt'

# 扩展配置
shared_preload_libraries = 'pg_stat_statements'
track_activity_query_size = 2048
pg_stat_statements.track = none

# 时区配置
timezone = 'Asia/Shanghai'
log_timezone = 'Asia/Shanghai'

# 其他配置
default_text_search_config = 'pg_catalog.english'
EOF

    # 创建恢复信号文件
    cat > "/etc/athena/postgres/config/recovery.conf" << EOF
# PostgreSQL恢复配置

standby_mode = 'on'
primary_conninfo = 'host=${DB_PRIMARY_HOST} port=${DB_PORT} user=${REPLICATION_USER} passwordfile=/etc/athena/secrets/replication_password application_name=replica1'
recovery_target_timeline = 'latest'
restore_command = 'cp /data/athena/backups/wal_archive/%f %p'
EOF

    log_success "PostgreSQL从节点配置创建完成"
}

# 创建Redis集群配置
create_redis_cluster_config() {
    log_info "创建Redis集群配置..."

    for i in "${!REDIS_CLUSTER_NODES[@]}"; do
        node_info=(${REDIS_CLUSTER_NODES[i]//:/ })
        node_host=${node_info[0]}
        node_port=${node_info[1]}
        node_id=$((i + 1))

        config_file="/etc/athena/redis/cluster/redis-${node_id}.conf"

        cat > "$config_file" << EOF
# Redis集群节点${node_id}配置 - Athena生产环境

# 网络配置
bind ${node_host} 127.0.0.1
port ${node_port}
protected-mode yes
tcp-backlog 511
timeout 300
tcp-keepalive 60

# 通用配置
daemonize yes
supervised systemd
pidfile /var/run/redis/redis-${node_id}.pid
loglevel notice
logfile "/var/log/athena/redis/cluster-${node_id}.log"

# 数据库配置
databases 16

# 内存配置
maxmemory 2gb
maxmemory-policy allkeys-lru
maxmemory-samples 5

# 持久化配置
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump-${node_id}.rdb
dir /data/athena/redis/cluster

# AOF配置
appendonly yes
appendfilename "appendonly-${node_id}.aof"
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb

# 集群配置
cluster-enabled yes
cluster-config-file nodes-${node_id}.conf
cluster-node-timeout 5000
cluster-announce-ip ${node_host}
cluster-announce-port ${node_port}
cluster-announce-bus-port $((node_port + 10000))

# 主从复制配置
masterauth "$(cat "$DB_PASSWORD_FILE")"
requirepass "$(cat "$DB_PASSWORD_FILE")"

# 安全配置
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command KEYS ""
rename-command CONFIG "CONFIG_b835c3f8a5d2e7f1"

# 性能配置
hash-max-ziplist-entries 512
hash-max-ziplist-value 64
list-max-ziplist-size -2
list-compress-depth 0
set-max-intset-entries 512
zset-max-ziplist-entries 128
zset-max-ziplist-value 64

# 其他配置
slowlog-log-slower-than 10000
slowlog-max-len 128
latency-monitor-threshold 100
notify-keyspace-events "Ex"
hz 10
dynamic-hz yes
aof-rewrite-incremental-fsync yes
rdb-save-incremental-fsync yes
EOF

        log_success "Redis集群节点${node_id}配置创建完成: $config_file"
    done
}

# 创建Redis缓存配置
create_redis_cache_config() {
    log_info "创建Redis缓存配置..."

    config_file="/etc/athena/redis/cache/redis-cache.conf"

    cat > "$config_file" << EOF
# Redis缓存配置 - Athena生产环境

# 网络配置
bind ${REDIS_CACHE_HOST} 127.0.0.1
port ${REDIS_CACHE_PORT}
protected-mode yes
tcp-backlog 511
timeout 300
tcp-keepalive 60

# 通用配置
daemonize yes
supervised systemd
pidfile /var/run/redis/redis-cache.pid
loglevel notice
logfile "/var/log/athena/redis/cache.log"

# 数据库配置
databases 1

# 内存配置
maxmemory 4gb
maxmemory-policy allkeys-lru
maxmemory-samples 5
lazyfree-lazy-eviction yes
lazyfree-lazy-expire yes
lazyfree-lazy-server-del yes

# 持久化配置（缓存可选择不持久化）
save ""
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump-cache.rdb
dir /data/athena/redis/cache

# AOF配置
appendonly yes
appendfilename "appendonly-cache.aof"
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb

# 安全配置
masterauth "$(cat "$DB_PASSWORD_FILE")"
requirepass "$(cat "$DB_PASSWORD_FILE")"

rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command KEYS ""
rename-command CONFIG "CONFIG_cache_9f7e4d2b6a1c5"

# 性能配置
hash-max-ziplist-entries 512
hash-max-ziplist-value 64
list-max-ziplist-size -2
list-compress-depth 0
set-max-intset-entries 512
zset-max-ziplist-entries 128
zset-max-ziplist-value 64

# 其他配置
slowlog-log-slower-than 1000
slowlog-max-len 256
latency-monitor-threshold 50
notify-keyspace-events "Ex"
hz 10
dynamic-hz yes
aof-rewrite-incremental-fsync yes
rdb-save-incremental-fsync yes
EOF

    log_success "Redis缓存配置创建完成: $config_file"
}

# 创建数据库初始化脚本
create_database_init_scripts() {
    log_info "创建数据库初始化脚本..."

    cat > "/etc/athena/postgres/init/01-create-database.sql" << EOF
-- 创建应用数据库
CREATE DATABASE ${DB_NAME} WITH ENCODING 'UTF8' LC_COLLATE='C' LC_CTYPE='C';

-- 创建应用用户
CREATE USER ${DB_USER} WITH PASSWORD '$(cat "$DB_PASSWORD_FILE")';

-- 授予权限
GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};

-- 创建复制用户
CREATE USER ${REPLICATION_USER} WITH REPLICATION ENCRYPTED PASSWORD '$(cat "$REPLICATION_PASSWORD_FILE")';

-- 连接到应用数据库
\c ${DB_NAME};

-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "btree_gist";
CREATE EXTENSION IF NOT EXISTS "pg_prewarm";

-- 设置权限
GRANT ALL ON SCHEMA public TO ${DB_USER};
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ${DB_USER};
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ${DB_USER};

-- 设置默认权限
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ${DB_USER};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO ${DB_USER};

\q
EOF

    cat > "/etc/athena/postgres/init/02-create-tables.sql" << EOF
-- 连接到应用数据库
\c ${DB_NAME};

-- 创建文档表
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    mime_type VARCHAR(100),
    checksum VARCHAR(64) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb,
    content_text TEXT,
    vector_embedding VECTOR(768)
);

-- 创建文档分析结果表
CREATE TABLE IF NOT EXISTS document_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    analysis_type VARCHAR(50) NOT NULL,
    analysis_result JSONB NOT NULL,
    confidence_score DECIMAL(3,2),
    processing_time INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    model_version VARCHAR(20)
);

-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE
);

-- 创建API密钥表
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key_name VARCHAR(100) NOT NULL,
    api_key VARCHAR(255) UNIQUE NOT NULL,
    permissions JSONB DEFAULT '[]'::jsonb,
    rate_limit INTEGER DEFAULT 1000,
    is_active BOOLEAN DEFAULT true,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used_at TIMESTAMP WITH TIME ZONE
);

-- 创建系统日志表
CREATE TABLE IF NOT EXISTS system_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    level VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    context JSONB DEFAULT '{}'::jsonb,
    user_id UUID REFERENCES users(id),
    service_name VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_documents_filename ON documents(filename);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at);
CREATE INDEX IF NOT EXISTS idx_documents_file_type ON documents(file_type);
CREATE INDEX IF NOT EXISTS idx_documents_vector_embedding ON documents USING ivfflat (vector_embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_document_analysis_document_id ON document_analysis(document_id);
CREATE INDEX IF NOT EXISTS idx_document_analysis_type ON document_analysis(analysis_type);
CREATE INDEX IF NOT EXISTS idx_document_analysis_created_at ON document_analysis(created_at);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_api_key ON api_keys(api_key);
CREATE INDEX IF NOT EXISTS idx_api_keys_is_active ON api_keys(is_active);

CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(level);
CREATE INDEX IF NOT EXISTS idx_system_logs_created_at ON system_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_system_logs_service_name ON system_logs(service_name);

-- 创建更新时间触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS \$\$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
\$\$ language 'plpgsql';

-- 为需要的表添加触发器
CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

\q
EOF

    log_success "数据库初始化脚本创建完成"
}

# 创建备份脚本
create_backup_scripts() {
    log_info "创建数据库备份脚本..."

    # PostgreSQL备份脚本
    cat > "/Users/xujian/Athena工作平台/scripts/backup_postgres.sh" << 'EOF'
#!/bin/bash
# PostgreSQL备份脚本

BACKUP_DIR="/data/athena/backups/postgres"
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="athena_production"
DB_USER="athena_user"
DB_PASSWORD_FILE="/etc/athena/secrets/db_password"
RETENTION_DAYS=30

mkdir -p "$BACKUP_DIR"

# 生成备份文件名
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/backup_${TIMESTAMP}.sql"
COMPRESSED_FILE="$BACKUP_FILE.gz"

echo "开始PostgreSQL备份..."

# 执行备份
PGPASSWORD=$(cat "$DB_PASSWORD_FILE") pg_dump \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --verbose \
    --clean \
    --if-exists \
    --create \
    --format=custom \
    --compress=9 \
    --file="$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "备份成功: $BACKUP_FILE"

    # 压缩备份文件
    gzip "$BACKUP_FILE"
    echo "备份已压缩: $COMPRESSED_FILE"

    # 删除过期备份
    find "$BACKUP_DIR" -name "backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete
    echo "已删除 $RETENTION_DAYS 天前的备份文件"
else
    echo "备份失败"
    exit 1
fi
EOF

    # Redis备份脚本
    cat > "/Users/xujian/Athena工作平台/scripts/backup_redis.sh" << 'EOF'
#!/bin/bash
# Redis备份脚本

BACKUP_DIR="/data/athena/backups/redis"
REDIS_HOST="localhost"
REDIS_PORT="6379"
REDIS_PASSWORD_FILE="/etc/athena/secrets/db_password"
RETENTION_DAYS=7

mkdir -p "$BACKUP_DIR"

# 生成备份文件名
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/redis_backup_${TIMESTAMP}.rdb"

echo "开始Redis备份..."

# 执行备份
redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$(cat "$REDIS_PASSWORD_FILE")" --rdb "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "备份成功: $BACKUP_FILE"

    # 压缩备份文件
    gzip "$BACKUP_FILE"
    echo "备份已压缩: ${BACKUP_FILE}.gz"

    # 删除过期备份
    find "$BACKUP_DIR" -name "redis_backup_*.rdb.gz" -mtime +$RETENTION_DAYS -delete
    echo "已删除 $RETENTION_DAYS 天前的备份文件"
else
    echo "备份失败"
    exit 1
fi
EOF

    chmod +x /Users/xujian/Athena工作平台/scripts/backup_*.sh

    log_success "备份脚本创建完成"
}

# 创建监控脚本
create_monitoring_scripts() {
    log_info "创建数据库监控脚本..."

    cat > "/Users/xujian/Athena工作平台/scripts/monitor_database.sh" << 'EOF'
#!/bin/bash
# 数据库监控脚本

DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="athena_production"
DB_USER="athena_user"
DB_PASSWORD_FILE="/etc/athena/secrets/db_password"

REDIS_HOST="localhost"
REDIS_PORT="6379"
REDIS_PASSWORD_FILE="/etc/athena/secrets/db_password"

METRICS_FILE="/tmp/database_metrics.txt"

# PostgreSQL监控
monitor_postgres() {
    echo "=== PostgreSQL监控数据 ==="

    PGPASSWORD=$(cat "$DB_PASSWORD_FILE") psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
    SELECT
        'active_connections' as metric,
        count(*) as value
    FROM pg_stat_activity
    WHERE state = 'active'

    UNION ALL

    SELECT
        'database_size' as metric,
        pg_size_pretty(pg_database_size('$DB_NAME')) as value

    UNION ALL

    SELECT
        'cache_hit_ratio' as metric,
        round(sum(blks_hit)::numeric / (sum(blks_hit) + sum(blks_read)) * 100, 2) || '%' as value
    FROM pg_stat_database
    WHERE datname = '$DB_NAME'

    UNION ALL

    SELECT
        'transactions_per_second' as metric,
        round((sum(xact_commit) + sum(xact_rollback)) / extract(epoch from (now() - stats_reset)))::text as value
    FROM pg_stat_database
    WHERE datname = '$DB_NAME'
    ;
    "

    echo ""
}

# Redis监控
monitor_redis() {
    echo "=== Redis监控数据 ==="

    redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$(cat "$REDIS_PASSWORD_FILE")" info server | grep -E "redis_version|os|arch"
    redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$(cat "$REDIS_PASSWORD_FILE")" info memory | grep -E "used_memory_human|maxmemory_human"
    redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$(cat "$REDIS_PASSWORD_FILE")" info stats | grep -E "total_commands_processed|total_connections_received|keyspace_hits|keyspace_misses"
    redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$(cat "$REDIS_PASSWORD_FILE")" info replication | grep -E "role|connected_slaves|master_replid"

    echo ""
}

# 检查数据库健康状态
check_health() {
    echo "=== 健康状态检查 ==="

    # PostgreSQL健康检查
    if PGPASSWORD=$(cat "$DB_PASSWORD_FILE") pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER"; then
        echo "✓ PostgreSQL: 健康"
    else
        echo "✗ PostgreSQL: 异常"
    fi

    # Redis健康检查
    if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$(cat "$REDIS_PASSWORD_FILE")" ping | grep -q PONG; then
        echo "✓ Redis: 健康"
    else
        echo "✗ Redis: 异常"
    fi

    echo ""
}

# 主函数
main() {
    echo "============================================"
    echo "     数据库监控报告"
    echo "     时间: $(date)"
    echo "============================================"
    echo ""

    monitor_postgres
    monitor_redis
    check_health

    echo "监控完成"
}

main "$@" > "$METRICS_FILE"

# 发送指标到监控系统
curl -X POST -H "Content-Type: text/plain" \
    --data-binary @"$METRICS_FILE" \
    http://localhost:9090/metrics/job/database 2>/dev/null || true
EOF

    chmod +x "/Users/xujian/Athena工作平台/scripts/monitor_database.sh"

    log_success "监控脚本创建完成"
}

# 创建Docker Compose数据库配置
create_database_docker_compose() {
    log_info "创建数据库Docker Compose配置..."

    cat > "/Users/xujian/Athena工作平台/docker/docker-compose.database.yml" << EOF
version: '3.8'

services:
  # PostgreSQL主节点
  postgres-primary:
    image: postgres:15-alpine
    container_name: athena-postgres-primary
    environment:
      - POSTGRES_DB=athena_production
      - POSTGRES_USER=athena_user
      - POSTGRES_PASSWORD_FILE=/run/secrets/db_password
      - POSTGRES_INITDB_ARGS=--encoding=UTF-8 --lc-collate=C --lc-ctype=C
      - PGDATA=/var/lib/postgresql/data/pgdata
    volumes:
      - /data/athena/postgres/primary:/var/lib/postgresql/data
      - /etc/athena/postgres/config/postgresql.conf:/etc/postgresql/postgresql.conf:ro
      - /etc/athena/postgres/config/pg_hba.conf:/etc/postgresql/pg_hba.conf:ro
      - /etc/athena/postgres/init:/docker-entrypoint-initdb.d:ro
      - /var/log/athena/postgres:/var/log/postgresql
      - /data/athena/backups/postgres:/backups
    networks:
      - database-network
    ports:
      - "${DB_PORT}:5432"
    restart: unless-stopped
    secrets:
      - db_password
      - replication_password
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U athena_user -d athena_production"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 8Gi
        reservations:
          cpus: '1.0'
          memory: 4Gi

  # PostgreSQL从节点
  postgres-replica:
    image: postgres:15-alpine
    container_name: athena-postgres-replica
    environment:
      - POSTGRES_DB=athena_production
      - POSTGRES_USER=athena_user
      - POSTGRES_PASSWORD_FILE=/run/secrets/db_password
      - PGUSER=athena_user
      - POSTGRES_MASTER_SERVICE=postgres-primary
      - POSTGRES_REPLICATION_USER=replicator
      - POSTGRES_REPLICATION_PASSWORD_FILE=/run/secrets/replication_password
      - PGDATA=/var/lib/postgresql/data/pgdata
    volumes:
      - /data/athena/postgres/replica:/var/lib/postgresql/data
      - /etc/athena/postgres/config/postgresql-replica.conf:/etc/postgresql/postgresql.conf:ro
      - /etc/athena/postgres/config/recovery.conf:/etc/postgresql/recovery.conf:ro
      - /var/log/athena/postgres:/var/log/postgresql
    networks:
      - database-network
    ports:
      - "5433:5432"
    restart: unless-stopped
    secrets:
      - db_password
      - replication_password
    depends_on:
      postgres-primary:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U athena_user -d athena_production"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 8Gi
        reservations:
          cpus: '1.0'
          memory: 4Gi

  # Redis集群节点
  redis-cluster-1:
    image: redis:7-alpine
    container_name: athena-redis-cluster-1
    command: redis-server /etc/redis/redis.conf --cluster-enabled yes
    volumes:
      - /data/athena/redis/cluster/node1:/data
      - /etc/athena/redis/cluster/redis-1.conf:/etc/redis/redis.conf:ro
      - /var/log/athena/redis:/var/log/redis
    networks:
      - database-network
    ports:
      - "6379:6379"
      - "16379:16379"
    restart: unless-stopped
    secrets:
      - db_password
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 2Gi
        reservations:
          cpus: '0.5'
          memory: 1Gi

  redis-cluster-2:
    image: redis:7-alpine
    container_name: athena-redis-cluster-2
    command: redis-server /etc/redis/redis.conf --cluster-enabled yes
    volumes:
      - /data/athena/redis/cluster/node2:/data
      - /etc/athena/redis/cluster/redis-2.conf:/etc/redis/redis.conf:ro
      - /var/log/athena/redis:/var/log/redis
    networks:
      - database-network
    ports:
      - "6380:6379"
      - "16380:16379"
    restart: unless-stopped
    secrets:
      - db_password
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 2Gi
        reservations:
          cpus: '0.5'
          memory: 1Gi

  redis-cluster-3:
    image: redis:7-alpine
    container_name: athena-redis-cluster-3
    command: redis-server /etc/redis/redis.conf --cluster-enabled yes
    volumes:
      - /data/athena/redis/cluster/node3:/data
      - /etc/athena/redis/cluster/redis-3.conf:/etc/redis/redis.conf:ro
      - /var/log/athena/redis:/var/log/redis
    networks:
      - database-network
    ports:
      - "6381:6379"
      - "16381:16379"
    restart: unless-stopped
    secrets:
      - db_password
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 2Gi
        reservations:
          cpus: '0.5'
          memory: 1Gi

  # Redis缓存
  redis-cache:
    image: redis:7-alpine
    container_name: athena-redis-cache
    command: redis-server /etc/redis/redis.conf
    volumes:
      - /data/athena/redis/cache:/data
      - /etc/athena/redis/cache/redis-cache.conf:/etc/redis/redis.conf:ro
      - /var/log/athena/redis:/var/log/redis
    networks:
      - database-network
    ports:
      - "6382:6379"
    restart: unless-stopped
    secrets:
      - db_password
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3
      start_period: 30s
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 2Gi
        reservations:
          cpus: '0.25'
          memory: 1Gi

# 网络配置
networks:
  database-network:
    driver: bridge
    ipam:
      driver: default
      config:
        - subnet: 172.23.0.0/16
          gateway: 172.23.0.1

# 密钥配置
secrets:
  db_password:
    file: /etc/athena/secrets/db_password
  replication_password:
    file: /etc/athena/secrets/replication_password
EOF

    log_success "数据库Docker Compose配置创建完成"
}

# 启动数据库服务
start_database_services() {
    log_info "启动数据库服务..."

    # 创建网络
    docker network create athena-database --driver bridge --subnet=172.23.0.0/16 || true

    # 启动数据库服务
    cd /Users/xujian/Athena工作平台/docker
    docker-compose -f docker-compose.database.yml up -d

    # 等待服务启动
    log_info "等待数据库服务启动..."
    sleep 30

    # 初始化Redis集群
    if docker ps | grep -q "athena-redis-cluster"; then
        log_info "初始化Redis集群..."

        # 获取Redis容器IP地址
        REDIS_IPS=()
        for i in {1..3}; do
            IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "athena-redis-cluster-$i")
            REDIS_IPS+=("$IP:6379")
        done

        # 创建Redis集群
        docker exec athena-redis-cluster-1 redis-cli --cluster create "${REDIS_IPS[@]}" --cluster-replicas 0 --cluster-yes -a "$(cat "$DB_PASSWORD_FILE")"

        log_success "Redis集群初始化完成"
    fi

    log_success "数据库服务启动完成"
}

# 验证数据库配置
verify_database_setup() {
    log_info "验证数据库配置..."

    # 检查PostgreSQL主节点
    if docker exec athena-postgres-primary pg_isready -U athena_user -d athena_production; then
        log_success "PostgreSQL主节点运行正常"
    else
        log_error "PostgreSQL主节点异常"
        return 1
    fi

    # 检查PostgreSQL从节点
    if docker exec athena-postgres-replica pg_isready -U athena_user -d athena_production; then
        log_success "PostgreSQL从节点运行正常"
    else
        log_error "PostgreSQL从节点异常"
        return 1
    fi

    # 检查Redis集群
    if docker exec athena-redis-cluster-1 redis-cli -a "$(cat "$DB_PASSWORD_FILE")" ping | grep -q PONG; then
        log_success "Redis集群运行正常"
    else
        log_error "Redis集群异常"
        return 1
    fi

    # 检查Redis缓存
    if docker exec athena-redis-cache redis-cli -a "$(cat "$DB_PASSWORD_FILE")" ping | grep -q PONG; then
        log_success "Redis缓存运行正常"
    else
        log_error "Redis缓存异常"
        return 1
    fi

    return 0
}

# 主函数
main() {
    echo -e "${BLUE}🗄️ Athena多模态文件系统数据库和缓存配置${NC}"
    echo "============================================"
    echo -e "${CYAN}开始时间: $(date)${NC}"

    # 检查依赖
    check_dependencies

    # 创建目录和密码
    create_directories
    generate_passwords

    # 创建配置
    create_postgres_primary_config
    create_postgres_replica_config
    create_redis_cluster_config
    create_redis_cache_config
    create_database_init_scripts
    create_backup_scripts
    create_monitoring_scripts
    create_database_docker_compose

    # 启动服务
    start_database_services

    # 验证配置
    if verify_database_setup; then
        echo ""
        echo -e "${GREEN}✅ 数据库和缓存配置完成！${NC}"
        echo ""
        echo -e "${BLUE}📋 配置信息:${NC}"
        echo -e "  🗄️ PostgreSQL主节点: ${YELLOW}172.20.0.30:5432${NC}"
        echo -e "  🗄️ PostgreSQL从节点: ${YELLOW}172.20.0.31:5432${NC}"
        echo -e "  🔴 Redis集群: ${YELLOW}172.20.0.40-45:6379${NC}"
        echo -e "  💾 Redis缓存: ${YELLOW}172.20.0.50:6379${NC}"
        echo -e "  📁 数据目录: ${YELLOW}/data/athena/${NC}"
        echo -e "  🔧 配置目录: ${YELLOW}/etc/athena/${NC}"
        echo ""
        echo -e "${BLUE}🔧 管理命令:${NC}"
        echo -e "  🗄️ 数据库监控: ${YELLOW}/Users/xujian/Athena工作平台/scripts/monitor_database.sh${NC}"
        echo -e "  💾 PostgreSQL备份: ${YELLOW}/Users/xujian/Athena工作平台/scripts/backup_postgres.sh${NC}"
        echo -e "  💾 Redis备份: ${YELLOW}/Users/xujian/Athena工作平台/scripts/backup_redis.sh${NC}"
        echo -e "  🐳 Docker状态: ${YELLOW}docker-compose -f docker-compose.database.yml ps${NC}"
        echo ""
        echo -e "${PURPLE}✨ 数据库和缓存系统已就绪！${NC}"
        echo ""
        echo -e "${YELLOW}📌 重要提示:${NC}"
        echo -e "  1. 定期检查复制延迟"
        echo -e "  2. 监控内存使用情况"
        echo -e "  3. 设置自动备份任务"
        echo -e "  4. 定期测试备份恢复"
        echo -e "  5. 监控Redis集群状态"
    else
        echo -e "${RED}❌ 数据库配置验证失败${NC}"
        exit 1
    fi
}

# 执行主函数
main "$@"