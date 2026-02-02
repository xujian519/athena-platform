#!/bin/bash

# Athena专利数据库初始化脚本
# 针对本地PostgreSQL部署
# 作者: 徐健
# 创建日期: 2025-12-13

set -e

# 配置变量
DB_NAME="athena_patent"
DB_USER="athena_admin"
DB_PASSWORD="Ath3n@2024#PatentSecure"
DB_HOST="localhost"
DB_PORT="5432"
POSTGRES_DATA_DIR="/var/lib/postgresql/15/main"
BACKUP_DIR="/backup/postgresql"
CONFIG_DIR="/etc/postgresql/15/main"
PATENT_DATA_DIR="/data/patent"

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

# 检查PostgreSQL是否已安装
check_postgresql() {
    if ! command -v psql &> /dev/null; then
        log_error "PostgreSQL未安装，请先安装PostgreSQL 15+"
        log_info "Ubuntu/Debian: sudo apt-get install postgresql-15"
        log_info "CentOS/RHEL: sudo yum install postgresql15-server"
        exit 1
    fi

    PG_VERSION=$(psql --version | awk '{print $3}' | cut -d'.' -f1)
    if [[ $PG_VERSION -lt 13 ]]; then
        log_error "需要PostgreSQL 13或更高版本"
        exit 1
    fi

    log_success "PostgreSQL版本检查通过: $PG_VERSION"
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."

    mkdir -p "$BACKUP_DIR"/{archive,wal,base}
    mkdir -p "$PATENT_DATA_DIR"
    mkdir -p "/var/log/postgresql"

    # 设置权限
    chown -R postgres:postgres "$BACKUP_DIR"
    chown -R postgres:postgres "$PATENT_DATA_DIR"
    chown -R postgres:postgres "/var/log/postgresql"

    log_success "目录创建完成"
}

# 初始化数据库集群
init_database() {
    log_info "初始化PostgreSQL数据库集群..."

    # 如果数据目录不存在，则初始化
    if [[ ! -d "$POSTGRES_DATA_DIR/base" ]]; then
        sudo -u postgres pg_createcluster 15 main --start
        log_success "数据库集群初始化完成"
    else
        log_warning "数据库集群已存在，跳过初始化"
    fi
}

# 配置数据库
configure_database() {
    log_info "配置PostgreSQL..."

    # 停止PostgreSQL服务
    systemctl stop postgresql || true

    # 复制配置文件
    cp "$(dirname "$0")/../../config/postgresql_local.conf" "$CONFIG_DIR/postgresql.conf"

    # 配置pg_hba.conf
    cat > "$CONFIG_DIR/pg_hba.conf" << EOF
# PostgreSQL Client Authentication Configuration File
# TYPE  DATABASE        USER            ADDRESS                 METHOD

# "local" is for Unix domain socket connections only
local   all             postgres                                peer
local   all             all                                     md5

# IPv4 local connections:
host    all             all             127.0.0.1/32            md5
host    all             all             0.0.0.0/0               reject

# IPv6 local connections:
host    all             all             ::1/128                 md5

# Allow replication connections from localhost, by a user with the
# replication privilege.
local   replication     all                                     peer
host    replication     all             127.0.0.1/32            md5
host    replication     all             ::1/128                 md5
EOF

    # 设置配置文件权限
    chown postgres:postgres "$CONFIG_DIR/postgresql.conf"
    chown postgres:postgres "$CONFIG_DIR/pg_hba.conf"
    chmod 640 "$CONFIG_DIR/pg_hba.conf"

    log_success "PostgreSQL配置完成"
}

# 启动数据库服务
start_database() {
    log_info "启动PostgreSQL服务..."

    systemctl start postgresql
    systemctl enable postgresql

    # 等待服务启动
    sleep 5

    if pg_isready -q; then
        log_success "PostgreSQL服务启动成功"
    else
        log_error "PostgreSQL服务启动失败"
        exit 1
    fi
}

# 创建用户和数据库
create_database_and_user() {
    log_info "创建专利数据库和用户..."

    # 设置postgres密码
    sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'P0stgr3s@2024#Secure';"

    # 创建应用用户
    sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD' CREATEDB CREATEROLE;"

    # 创建主数据库
    sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER ENCODING 'UTF8' LC_COLLATE 'zh_CN.UTF-8' LC_CTYPE 'zh_CN.UTF-8' TEMPLATE template0;"

    # 创建专利分析用户（只读）
    sudo -u postgres psql -c "CREATE USER patent_analyst WITH PASSWORD 'Analyst@2024#Patent';"
    sudo -u postgres psql -c "GRANT CONNECT ON DATABASE $DB_NAME TO patent_analyst;"

    # 创建备份用户
    sudo -u postgres psql -c "CREATE USER patent_backup WITH PASSWORD 'Backup@2024#Patent';"
    sudo -u postgres psql -c "GRANT CONNECT ON DATABASE $DB_NAME TO patent_backup;"

    log_success "数据库和用户创建完成"
}

# 安装必要的扩展
install_extensions() {
    log_info "安装PostgreSQL扩展..."

    sudo -u postgres psql -d "$DB_NAME" -c "
        -- 启用UUID扩展
        CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";

        -- 启用全文搜索
        CREATE EXTENSION IF NOT EXISTS pg_trgm;

        -- 启用加密
        CREATE EXTENSION IF NOT EXISTS pgcrypto;

        -- 启用统计信息
        CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

        -- 启用自动解释
        CREATE EXTENSION IF NOT EXISTS auto_explain;

        -- 启用GIN索引支持
        CREATE EXTENSION IF NOT EXISTS btree_gin;

        -- 启用模糊搜索
        CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;

        -- 如果需要中文分词，取消注释下面这行
        -- CREATE EXTENSION IF NOT EXISTS pg_jieba;
    "

    log_success "扩展安装完成"
}

# 创建专利数据表结构
create_patent_tables() {
    log_info "创建专利数据表结构..."

    # 使用创建的脚本
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$(dirname "$0")/create_patent_tables.sql"

    log_success "专利数据表结构创建完成"
}

# 创建索引优化
create_indexes() {
    log_info "创建索引优化..."

    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$(dirname "$0")/create_indexes.sql"

    log_success "索引创建完成"
}

# 初始化数据（如果有）
initialize_data() {
    log_info "检查是否需要初始化数据..."

    # 检查数据目录
    if [[ -d "$PATENT_DATA_DIR/init" ]] && [[ $(ls -A "$PATENT_DATA_DIR/init") ]]; then
        log_info "发现初始化数据，开始导入..."

        # 导入初始数据
        for sql_file in "$PATENT_DATA_DIR/init"/*.sql; do
            if [[ -f "$sql_file" ]]; then
                log_info "导入: $(basename "$sql_file")"
                PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$sql_file"
            fi
        done

        log_success "初始数据导入完成"
    else
        log_info "未发现初始化数据，跳过"
    fi
}

# 配置备份脚本
setup_backup() {
    log_info "配置备份脚本..."

    cat > /usr/local/bin/patent-db-backup.sh << 'EOF'
#!/bin/bash

# 专利数据库备份脚本
DB_NAME="athena_patent"
DB_USER="athena_admin"
BACKUP_DIR="/backup/postgresql/base"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份
pg_dump -h localhost -U "$DB_USER" -d "$DB_NAME" -Fc > "$BACKUP_DIR/athena_patent_$DATE.dump"

# 压缩备份文件
gzip "$BACKUP_DIR/athena_patent_$DATE.dump"

# 删除7天前的备份
find "$BACKUP_DIR" -name "athena_patent_*.dump.gz" -mtime +7 -delete

echo "备份完成: $BACKUP_DIR/athena_patent_$DATE.dump.gz"
EOF

    chmod +x /usr/local/bin/patent-db-backup.sh

    # 创建定时任务
    cat > /etc/cron.d/patent-db-backup << EOF
# 专利数据库备份任务
0 2 * * * postgres /usr/local/bin/patent-db-backup.sh
EOF

    log_success "备份配置完成"
}

# 配置监控脚本
setup_monitoring() {
    log_info "配置数据库监控..."

    cat > /usr/local/bin/patent-db-monitor.sh << 'EOF'
#!/bin/bash

# 专利数据库监控脚本
DB_NAME="athena_patent"
DB_HOST="localhost"
ALERT_EMAIL="admin@athena-platform.com"

# 检查数据库连接
if ! pg_isready -h "$DB_HOST" -d "$DB_NAME" > /dev/null 2>&1; then
    echo "数据库连接失败！" | mail -s "专利数据库告警" "$ALERT_EMAIL"
    exit 1
fi

# 检查活跃连接数
CONNECTIONS=$(psql -h "$DB_HOST" -d "$DB_NAME" -t -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';" | tr -d ' ')

if [[ $CONNECTIONS -gt 150 ]]; then
    echo "活跃连接数过高: $CONNECTIONS" | mail -s "专利数据库告警" "$ALERT_EMAIL"
fi

# 检查数据库大小
DB_SIZE=$(psql -h "$DB_HOST" -d "$DB_NAME" -t -c "SELECT pg_size_pretty(pg_database_size('$DB_NAME'));" | tr -d ' ')

echo "数据库状态正常，大小: $DB_SIZE"
EOF

    chmod +x /usr/local/bin/patent-db-monitor.sh

    # 创建监控定时任务
    cat > /etc/cron.d/patent-db-monitor << EOF
# 专利数据库监控任务
*/5 * * * * postgres /usr/local/bin/patent-db-monitor.sh
EOF

    log_success "监控配置完成"
}

# 显示连接信息
show_connection_info() {
    log_info "数据库连接信息："
    echo "====================================="
    echo "主机: $DB_HOST"
    echo "端口: $DB_PORT"
    echo "数据库: $DB_NAME"
    echo "用户: $DB_USER"
    echo "密码: [已设置]"
    echo "连接命令: psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME"
    echo "====================================="

    log_info "请妥善保管数据库密码！"
}

# 主函数
main() {
    log_info "开始初始化Athena专利数据库..."

    check_root
    check_postgresql
    create_directories
    init_database
    configure_database
    start_database
    create_database_and_user
    install_extensions
    create_patent_tables
    create_indexes
    initialize_data
    setup_backup
    setup_monitoring
    show_connection_info

    log_success "Athena专利数据库初始化完成！"
    log_info "建议操作："
    log_info "1. 检查数据库状态: systemctl status postgresql"
    log_info "2. 测试连接: psql -h localhost -U athena_admin -d athena_patent"
    log_info "3. 配置防火墙允许必要访问"
    log_info "4. 定期检查备份和日志"
}

# 执行主函数
main "$@"