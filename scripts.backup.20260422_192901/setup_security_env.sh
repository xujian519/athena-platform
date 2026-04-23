#!/bin/bash
# ============================================================================
# Athena安全环境变量快速配置脚本
# 用途: 快速生成和配置所有必需的安全环境变量
# ============================================================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo -e "${BLUE}"
    echo "============================================================================"
    echo "$1"
    echo "============================================================================"
    echo -e "${NC}"
}

# 检查依赖
check_dependencies() {
    print_header "检查依赖工具"

    if ! command -v openssl &> /dev/null; then
        print_error "未找到 openssl 命令"
        print_info "请安装 OpenSSL:"
        print_info "  macOS: brew install openssl"
        print_info "  Ubuntu/Debian: sudo apt-get install openssl"
        exit 1
    fi

    print_success "依赖检查通过"
}

# 检查.env文件
check_env_file() {
    print_header "检查环境变量文件"

    if [ -f ".env" ]; then
        print_warning ".env 文件已存在"
        read -p "是否备份现有文件？(y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            backup_file=".env.backup.$(date +%Y%m%d_%H%M%S)"
            cp .env "$backup_file"
            print_success "已备份到: $backup_file"
        fi
    else
        print_info "将创建新的 .env 文件"
    fi
}

# 生成安全密钥
generate_secrets() {
    print_header "生成安全密钥"

    # 生成数据库密码
    DB_PASSWORD=$(openssl rand -base64 16 | tr -d '=+/' | cut -c1-16)
    print_success "DB_PASSWORD: ${DB_PASSWORD:0:4}...${DB_PASSWORD: -4}"

    # 生成JWT密钥
    JWT_SECRET=$(openssl rand -hex 32)
    print_success "JWT_SECRET: ${JWT_SECRET:0:8}...${JWT_SECRET: -8}"

    # 生成JWT备用密钥
    JWT_SECRET_KEY=$(openssl rand -hex 32)
    print_success "JWT_SECRET_KEY: ${JWT_SECRET_KEY:0:8}...${JWT_SECRET_KEY: -8}"

    # 生成Neo4j密码
    NEO4J_PASSWORD=$(openssl rand -base64 12 | tr -d '=+/' | cut -c1-12)
    print_success "NEO4J_PASSWORD: ${NEO4J_PASSWORD:0:4}...${NEO4J_PASSWORD: -4}"

    # 生成Redis密码
    REDIS_PASSWORD=$(openssl rand -base64 16 | tr -d '=+/' | cut -c1-16)
    print_success "REDIS_PASSWORD: ${REDIS_PASSWORD:0:4}...${REDIS_PASSWORD: -4}"

    # 生成加密密钥
    ENCRYPTION_KEY=$(openssl rand -base64 32)
    print_success "ENCRYPTION_KEY: ${ENCRYPTION_KEY:0:8}...${ENCRYPTION_KEY: -8}"
}

# 写入.env文件
write_env_file() {
    print_header "写入环境变量文件"

    cat > .env << EOF
# ============================================================================
# Athena安全环境变量配置
# 自动生成时间: $(date)
# ============================================================================

# ============================================================================
# 🔐 核心安全配置 - 必需
# ============================================================================

# 数据库密码（必需）
DB_PASSWORD=${DB_PASSWORD}

# JWT密钥（必需，至少32个字符）
JWT_SECRET=${JWT_SECRET}
JWT_SECRET_KEY=${JWT_SECRET_KEY}

# Neo4j图数据库密码（必需）
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=${NEO4J_PASSWORD}

# Redis密码（生产环境必需）
REDIS_PASSWORD=${REDIS_PASSWORD}

# ============================================================================
# 数据库连接配置
# ============================================================================

DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_NAME=athena

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# ============================================================================
# 加密配置
# ============================================================================

ENCRYPTION_KEY=${ENCRYPTION_KEY}

# ============================================================================
# AI模型API密钥（可选，按需配置）
# ============================================================================

# OpenAI API密钥
# OPENAI_API_KEY=sk-your-openai-api-key-here

# 智谱AI API密钥
# ZHIPU_API_KEY=your-zhipu-ai-api-key-here

# DeepSeek API密钥
# DEEPSEEK_API_KEY=sk-your-deepseek-api-key-here

# ============================================================================
# 其他服务配置（可选）
# ============================================================================

# 高德地图API密钥
# AMAP_API_KEY=your-amap-api-key-here

# 谷歌搜索API密钥
# GOOGLE_API_KEY=your-google-api-key-here

# Qdrant向量数据库
# QDRANT_URL=http://localhost:6333
# QDRANT_API_KEY=

EOF

    print_success ".env 文件已创建"
}

# 设置文件权限
set_permissions() {
    print_header "设置文件权限"

    chmod 600 .env
    print_success ".env 文件权限已设置为 600"
}

# 验证配置
verify_config() {
    print_header "验证配置"

    print_info "运行安全配置验证..."

    if python3 scripts/verify_security_config.py; then
        print_success "安全配置验证通过"
        return 0
    else
        print_warning "安全配置验证发现问题"
        return 1
    fi
}

# 显示配置摘要
show_summary() {
    print_header "配置完成摘要"

    cat << EOF
🎉 安全环境变量配置完成！

已生成的密钥:
  ✅ 数据库密码 (DB_PASSWORD)
  ✅ JWT密钥 (JWT_SECRET)
  ✅ JWT备用密钥 (JWT_SECRET_KEY)
  ✅ Neo4j密码 (NEO4J_PASSWORD)
  ✅ Redis密码 (REDIS_PASSWORD)
  ✅ 加密密钥 (ENCRYPTION_KEY)

下一步操作:
  1. 检查 .env 文件内容
  2. 添加其他可选的API密钥（如需要）
  3. 运行验证: python3 scripts/verify_security_config.py
  4. 启动服务

重要提醒:
  ⚠️  请妥善保管 .env 文件，不要提交到版本控制系统
  ⚠️  生产环境建议定期轮换密钥
  ⚠️  确保数据库密码与实际数据库配置一致

EOF
}

# 主函数
main() {
    print_header "Athena安全环境变量配置"

    # 检查是否在项目根目录
    if [ ! -f "pyproject.toml" ] && [ ! -f "SECURITY_CONFIG_GUIDE.md" ]; then
        print_error "请在项目根目录运行此脚本"
        exit 1
    fi

    # 执行配置步骤
    check_dependencies
    check_env_file
    generate_secrets
    write_env_file
    set_permissions

    # 验证配置
    if verify_config; then
        show_summary
        print_success "配置完成！"
    else
        print_warning "配置已完成，但验证发现了一些问题"
        print_info "请运行 'python3 scripts/verify_security_config.py' 查看详情"
    fi
}

# 运行主函数
main "$@"
