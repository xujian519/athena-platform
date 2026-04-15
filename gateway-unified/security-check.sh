#!/bin/bash
# Athena Gateway 安全检查脚本
# 用途: 检查部署环境的安全配置

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

APP_USER="athena"
APP_DIR="/opt/athena-gateway"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Athena Gateway 安全检查${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查项目
checks_passed=0
checks_failed=0
checks_warned=0

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((checks_passed++))
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    ((checks_failed++))
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((checks_warned++))
}

echo -e "${BLUE}[用户权限检查]${NC}"

# 检查应用用户
if id "$APP_USER" &>/dev/null; then
    check_pass "应用用户 ${APP_USER} 已创建"
else
    check_fail "应用用户 ${APP_USER} 不存在"
fi

# 检查用户shell
if getent passwd "$APP_USER" | grep -q "/bin/false"; then
    check_pass "用户 ${APP_USER} 无shell登录权限"
else
    check_warn "用户 ${APP_USER} 有shell登录权限，建议使用 /bin/false"
fi

echo ""
echo -e "${BLUE}[文件权限检查]${NC}"

# 检查应用目录
if [ -d "$APP_DIR" ]; then
    check_pass "应用目录存在: $APP_DIR"

    # 检查目录权限
    perms=$(stat -c %a "$APP_DIR")
    if [ "$perms" = "750" ]; then
        check_pass "目录权限正确 (750)"
    else
        check_warn "目录权限为 $perms，建议设置为 750"
    fi

    # 检查目录所有者
    owner=$(stat -c %U "$APP_DIR")
    if [ "$owner" = "$APP_USER" ]; then
        check_pass "目录所有者正确 (${APP_USER})"
    else
        check_fail "目录所有者为 $owner，应为 ${APP_USER}"
    fi
else
    check_fail "应用目录不存在: $APP_DIR"
fi

# 检查配置文件权限
config_dir="${APP_DIR}/config"
if [ -d "$config_dir" ]; then
    # 检查配置文件权限
    find "$config_dir" -name "*.yaml" -o -name "*.env" | while read -r file; do
        perms=$(stat -c %a "$file")
        if [ "$perms" = "640" ]; then
            check_pass "配置文件权限正确: $(basename $file) (640)"
        else
            check_warn "配置文件权限不安全: $(basename $file) ($perms)，建议设置为 640"
        fi
    done
fi

# 检查二进制文件
if [ -f "${APP_DIR}/bin/gateway" ]; then
    check_pass "网关二进制文件存在"

    # 检查二进制权限
    perms=$(stat -c %a "${APP_DIR}/bin/gateway")
    if [ "$perms" = "750" ] || [ "$perms" = "755" ]; then
        check_pass "二进制权限正确 ($perms)"
    else
        check_warn "二进制权限为 $perms，建议设置为 750"
    fi
else
    check_fail "网关二进制文件不存在"
fi

echo ""
echo -e "${BLUE}[认证配置检查]${NC}"

auth_file="${APP_DIR}/config/auth.yaml"
if [ -f "$auth_file" ]; then
    check_pass "认证配置文件存在"

    # 检查默认密钥
    if grep -q "CHANGE-THIS" "$auth_file"; then
        check_fail "检测到默认密钥，请修改为强密钥！"
    else
        check_pass "未使用默认密钥"
    fi

    # 检查密钥强度
    key_count=$(grep -E 'api_keys:|bearer_tokens:' "$auth_file" -A 5 | grep -E '^\s+-' | wc -l)
    if [ "$key_count" -ge 1 ]; then
        check_pass "已配置 $key_count 个认证密钥"
    else
        check_warn "未配置认证密钥，建议启用"
    fi
else
    check_warn "认证配置文件不存在"
fi

echo ""
echo -e "${BLUE}[TLS/SSL检查]${NC}"

config_file="${APP_DIR}/config/config.yaml"
if [ -f "$config_file" ]; then
    if grep -q "tls:" "$config_file"; then
        tls_enabled=$(grep "enabled:" "$config_file" | head -1)
        if echo "$tls_enabled" | grep -q "true"; then
            check_warn "TLS已启用"

            # 检查证书路径
            cert_file=$(grep "cert_file:" "$config_file" | awk '{print $2}' | tr -d '"')
            key_file=$(grep "key_file:" "$config_file" | awk '{print $2}' | tr -d '"')

            if [ -f "$cert_file" ] && [ -f "$key_file" ]; then
                check_pass "TLS证书文件存在"
            else
                check_fail "TLS证书文件不存在，请配置证书"
            fi
        else
            check_warn "TLS未启用，生产环境建议启用"
        fi
    else
        check_warn "未配置TLS，建议使用Nginx反向代理"
    fi
fi

echo ""
echo -e "${BLUE}[防火墙检查]${NC}"

# 检查UFW
if command -v ufw &> /dev/null; then
    if ufw status | grep -q "8005.*ALLOW"; then
        check_pass "UFW规则已配置 (端口8005)"
    else
        check_fail "UFW规则未配置 (端口8005)"
    fi
else
    check_warn "UFW未安装，请手动配置防火墙"
fi

# 检查firewalld
if command -v firewall-cmd &> /dev/null; then
    if firewall-cmd --list-ports | grep -q "8005/tcp"; then
        check_pass "firewalld规则已配置 (端口8005)"
    else
        check_fail "firewalld规则未配置 (端口8005)"
    fi
fi

echo ""
echo -e "${BLUE}[服务配置检查]${NC}"

service_file="/etc/systemd/system/athena-gateway.service"
if [ -f "$service_file" ]; then
    check_pass "systemd服务文件已配置"

    # 检查安全设置
    if grep -q "NoNewPrivileges=true" "$service_file"; then
        check_pass "NoNewPrivileges已启用"
    else
        check_warn "NoNewPrivileges未启用"
    fi

    if grep -q "PrivateTmp=true" "$service_file"; then
        check_pass "PrivateTmp已启用"
    else
        check_warn "PrivateTmp未启用"
    fi

    if grep -q "ProtectSystem=strict" "$service_file"; then
        check_pass "ProtectSystem=strict已启用"
    else
        check_warn "ProtectSystem未启用"
    fi
else
    check_fail "systemd服务文件未配置"
fi

echo ""
echo -e "${BLUE}[日志配置检查]${NC}"

logrotate_file="/etc/logrotate.d/athena-gateway"
if [ -f "$logrotate_file" ]; then
    check_pass "logrotate已配置"
else
    check_warn "logrotate未配置，使用内置日志轮转"
fi

echo ""
echo -e "${BLUE}[备份配置检查]${NC}"

backup_script="${APP_DIR}/backup.sh"
if [ -f "$backup_script" ]; then
    check_pass "备份脚本已创建"

    # 检查cron任务
    if crontab -l 2>/dev/null | grep -q "backup.sh"; then
        check_pass "自动备份已配置"
    else
        check_warn "自动备份未配置"
    fi
else
    check_warn "备份脚本未创建"
fi

echo ""
echo -e "${BLUE}[监控配置检查]${NC}"

if [ -f "/etc/prometheus/rules/athena-gateway.yml" ]; then
    check_pass "Prometheus告警规则已配置"
else
    check_warn "Prometheus告警规则未配置"
fi

# 总结
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  检查结果汇总${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "通过: ${GREEN}${checks_passed}${NC}"
echo -e "失败: ${RED}${checks_failed}${NC}"
echo -e "警告: ${YELLOW}$(grep -c "^⚠" <<< "$(check_warn "警告" 2>/dev/null || echo "0")${NC}"
echo ""

if [ $checks_failed -eq 0 ]; then
    echo -e "${GREEN}✅ 安全检查通过，可以部署到生产环境！${NC}"
    exit 0
else
    echo -e "${RED}❌ 存在 ${checks_failed} 个必须修复的问题！${NC}"
    exit 1
fi
