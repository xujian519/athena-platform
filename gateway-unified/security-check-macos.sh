#!/bin/bash
# Athena Gateway macOS 安全检查脚本
# 用途: 检查macOS部署环境的安全配置

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

APP_USER="_athena"
APP_DIR="/usr/local/athena-gateway"
SERVICE_NAME="com.athena.gateway"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Athena Gateway 安全检查 (macOS)${NC}"
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
user_shell=$(dscl . -read /Users/"$APP_USER" UserShell 2>/dev/null | awk '{print $2}')
if [ "$user_shell" = "/usr/bin/false" ]; then
    check_pass "用户 ${APP_USER} 无shell登录权限"
else
    check_warn "用户 ${APP_USER} 有shell登录权限，建议使用 /usr/bin/false"
fi

echo ""
echo -e "${BLUE}[文件权限检查]${NC}"

# 检查应用目录
if [ -d "$APP_DIR" ]; then
    check_pass "应用目录存在: $APP_DIR"

    # 检查目录权限 (macOS使用stat -f %Lp)
    perms=$(stat -f "%Lp" "$APP_DIR")
    if [ "$perms" = "750" ]; then
        check_pass "目录权限正确 (750)"
    else
        check_warn "目录权限为 $perms，建议设置为 750"
    fi

    # 检查目录所有者
    owner=$(stat -f "%Su" "$APP_DIR")
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
    find "$config_dir" -name "*.yaml" -o -name "*.env" 2>/dev/null | while read -r file; do
        perms=$(stat -f "%Lp" "$file")
        if [ "$perms" = "640" ]; then
            check_pass "配置文件权限正确: $(basename "$file") (640)"
        else
            check_warn "配置文件权限不安全: $(basename "$file") ($perms)，建议设置为 640"
        fi
    done
fi

# 检查二进制文件
if [ -f "${APP_DIR}/bin/gateway" ]; then
    check_pass "网关二进制文件存在"

    perms=$(stat -f "%Lp" "${APP_DIR}/bin/gateway")
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
    key_count=$(grep -E 'api_keys:|bearer_tokens:' "$auth_file" -A 5 | grep -E '^\s+-' | wc -l | tr -d ' ')
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
        check_warn "未配置TLS，建议使用反向代理"
    fi
fi

echo ""
echo -e "${BLUE}[防火墙检查]${NC}"

# 检查macOS应用防火墙
if /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate 2>/dev/null | grep -q "enabled"; then
    check_pass "macOS应用防火墙已启用"

    if /usr/libexec/ApplicationFirewall/socketfilterfw --listapps 2>/dev/null | grep -q "gateway"; then
        check_pass "Gateway已添加到防火墙允许列表"
    else
        check_warn "Gateway未添加到防火墙允许列表"
    fi
else
    check_warn "macOS应用防火墙未启用"
fi

# 检查pf
if pfctl -s info 2>/dev/null | grep -q "Enabled"; then
    check_pass "pf防火墙已启用"
else
    check_warn "pf防火墙未启用"
fi

echo ""
echo -e "${BLUE}[服务配置检查]${NC}"

service_file="/Library/LaunchDaemons/${SERVICE_NAME}.plist"
if [ -f "$service_file" ]; then
    check_pass "launchd服务文件已配置"

    # 检查服务是否加载
    if launchctl list | grep -q "$SERVICE_NAME"; then
        check_pass "服务已加载到launchd"
    else
        check_warn "服务未加载到launchd"
    fi

    # 检查运行用户
    if grep -q "<string>${APP_USER}</string>" "$service_file"; then
        check_pass "服务运行用户正确 (${APP_USER})"
    else
        check_warn "服务运行用户未配置或配置不正确"
    fi
else
    check_fail "launchd服务文件未配置"
fi

echo ""
echo -e "${BLUE}[日志配置检查]${NC}"

newsyslog_file="/etc/newsyslog.d/${APP_NAME}.conf"
if [ -f "$newsyslog_file" ]; then
    check_pass "newsyslog已配置"
else
    check_warn "newsyslog未配置，使用内置日志轮转"
fi

echo ""
echo -e "${BLUE}[备份配置检查]${NC}"

backup_script="${APP_DIR}/backup.sh"
if [ -f "$backup_script" ]; then
    check_pass "备份脚本已创建"

    # 检查launchd定时任务
    if [ -f "/Library/LaunchDaemons/com.athena.gateway.backup.plist" ]; then
        check_pass "自动备份已配置"
    else
        check_warn "自动备份未配置"
    fi
else
    check_warn "备份脚本未创建"
fi

echo ""
echo -e "${BLUE}[端口占用检查]${NC}"

# 检查端口占用
ports=(8005 8443 9090)
for port in "${ports[@]}"; do
    if lsof -i ":$port" -sTCP:LISTEN -t >/dev/null 2>&1; then
        check_warn "端口 $port 已被占用"
    else
        check_pass "端口 $port 可用"
    fi
done

# 总结
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  检查结果汇总${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "通过: ${GREEN}${checks_passed}${NC}"
echo -e "失败: ${RED}${checks_failed}${NC}"
echo -e "警告: ${YELLOW}${checks_warned}${NC}"
echo ""

if [ $checks_failed -eq 0 ]; then
    echo -e "${GREEN}✅ 安全检查通过，可以部署到生产环境！${NC}"
    exit 0
else
    echo -e "${RED}❌ 存在 ${checks_failed} 个必须修复的问题！${NC}"
    exit 1
fi
