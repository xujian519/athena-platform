#!/bin/bash

# Athena API Gateway - 生产环境配置验证脚本
# 用于验证生产环境必需的环境变量是否已正确设置

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 检查结果
errors=0
warnings=0

echo "🔍 Athena API Gateway - 生产环境配置验证"
echo "=================================================="

# 必需的环境变量检查
required_vars=(
    "JWT_SECRET"
    "REDIS_PASSWORD"
    "CSRF_SECRET"
)

optional_vars=(
    "GATEWAY_PORT"
    "REDIS_HOST"
    "REDIS_PORT"
    "LOG_LEVEL"
    "PROMETHEUS_ENABLED"
    "TRACING_ENABLED"
)

log_info "检查必需的环境变量..."

for var in "${required_vars[@]}"; do
    if [[ -z "${!var:-}" ]]; then
        log_error "环境变量 $var 未设置"
        ((errors++))
    else
        log_success "环境变量 $var 已设置"
        
        # 特殊验证
        case $var in
            "JWT_SECRET")
                if [[ ${#var} -lt 32 ]]; then
                    log_warning "JWT_SECRET 长度少于32字符，建议使用更长的密钥"
                    ((warnings++))
                fi
                ;;
            "REDIS_PASSWORD")
                if [[ "${!var}" == "" ]]; then
                    log_warning "REDIS_PASSWORD 为空，Redis将无密码运行"
                    ((warnings++))
                fi
                ;;
            "CSRF_SECRET")
                if [[ ${#var} -lt 16 ]]; then
                    log_warning "CSRF_SECRET 长度少于16字符，建议使用更长的密钥"
                    ((warnings++))
                fi
                ;;
        esac
    fi
done

log_info "检查可选的环境变量..."

for var in "${optional_vars[@]}"; do
    if [[ -n "${!var:-}" ]]; then
        log_success "环境变量 $var 已设置为: ${!var}"
    else
        log_info "环境变量 $var 未设置，将使用默认值"
    fi
done

echo ""
echo "📊 验证结果汇总:"
echo "=================================================="

if [[ $errors -eq 0 ]]; then
    if [[ $warnings -eq 0 ]]; then
        log_success "✅ 所有配置验证通过，可以启动生产环境"
        exit_code=0
    else
        log_warning "⚠️  配置验证通过，但有 $warnings 个警告需要注意"
        exit_code=1
    fi
else
    log_error "❌ 发现 $errors 个错误，请修复后重试"
    exit_code=2
fi

echo ""
echo "🔧 安全建议:"
echo "=================================================="
echo "1. 定期轮换 JWT_SECRET 和 CSRF_SECRET"
echo "2. 使用强密码策略，包含大小写字母、数字和特殊字符"
echo "3. 在生产环境中禁用调试模式 (LOG_LEVEL=info)"
echo "4. 启用 HTTPS 和安全头配置"
echo "5. 定期审查配置文件和访问权限"

exit $exit_code