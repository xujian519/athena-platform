#!/bin/bash
# Athena Gateway macOS 生产环境部署脚本
# 用途: 在macOS上部署Gateway服务
# 使用: sudo bash deploy-macos.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

APP_NAME="athena-gateway"
APP_USER="_athena"  # macOS用户名通常以_开头表示系统用户
APP_DIR="/usr/local/${APP_NAME}"
SERVICE_NAME="com.athena.gateway"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Athena Gateway macOS 部署${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查root权限
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}错误: 请使用root权限运行此脚本 (sudo ./deploy-macos.sh)${NC}"
    exit 1
fi

# 检查macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}错误: 此脚本仅适用于macOS${NC}"
    exit 1
fi

echo -e "${GREEN}[1/8] 创建应用用户和目录...${NC}"

# 检查用户是否存在
if id "$APP_USER" &>/dev/null; then
    echo -e "${YELLOW}用户 ${APP_USER} 已存在${NC}"
else
    # 创建系统用户
    sysadminctl -addUser "$APP_USER" -password "*" 2>/dev/null || {
        # 备用方法：使用dscl
        lastID=$(dscl . -list /Users | grep -E '^_[0-9]+$' | sort -n | tail -1 | cut -c 2-)
        nextID=$((lastID + 1))
        dscl . -create /Users/"$APP_USER"
        dscl . -create /Users/"$APP_USER" UserShell /usr/bin/false
        dscl . -create /Users/"$APP_USER" RealName "Athena Gateway Service"
        dscl . -create /Users/"$APP_USER" UniqueID "$nextID"
        dscl . -create /Users/"$APP_USER" PrimaryGroupID 20
        dscl . -create /Users/"$APP_USER" NFSHomeDirectory /var/empty
    }
    echo -e "${GREEN}✓ 用户 ${APP_USER} 已创建${NC}"
fi

# 创建目录结构
mkdir -p "$APP_DIR"/{bin,config,logs,certs,backup}
echo -e "${GREEN}✓ 目录结构已创建${NC}"

echo -e "${GREEN}[2/8] 部署应用文件...${NC}"

# 复制二进制文件
if [ -f "${SCRIPT_DIR}/gateway" ]; then
    cp "${SCRIPT_DIR}/gateway" "${APP_DIR}/bin/"
    chmod 750 "${APP_DIR}/bin/gateway"
    echo -e "${GREEN}✓ 二进制文件已部署${NC}"
else
    echo -e "${RED}错误: 找不到gateway二进制文件${NC}"
    echo "请先运行: go build -o gateway ./cmd/gateway"
    exit 1
fi

# 复制配置文件
if [ -f "${SCRIPT_DIR}/gateway-config.yaml.example" ]; then
    cp "${SCRIPT_DIR}/gateway-config.yaml.example" "${APP_DIR}/config/config.yaml"
fi

# 创建认证配置
cat > "${APP_DIR}/config/auth.yaml" << 'EOF'
# Athena Gateway 认证配置
# 生产环境请修改这些默认值！

api_keys:
  - "CHANGE-THIS-TO-SECURE-API-KEY"

bearer_tokens:
  - "CHANGE-THIS-TO-SECURE-BEARER-TOKEN"

basic_auth:
  username: "admin"
  password: "CHANGE-THIS-TO-SECURE-PASSWORD"

ip_whitelist:
  - "127.0.0.1"
  - "::1"
  - "10.0.0.0/8"
  - "172.16.0.0/12"
  - "192.168.0.0/16"
EOF

# 设置权限
chown -R "$APP_USER:staff" "$APP_DIR"
chmod 750 "$APP_DIR"
chmod 750 "${APP_DIR}/config"
chmod 640 "${APP_DIR}/config"/*.yaml
chmod 750 "${APP_DIR}/logs"
echo -e "${GREEN}✓ 配置文件已部署${NC}"

echo -e "${GREEN}[3/8] 配置launchd服务...${NC}"

# 创建launchd plist文件
cat > "/Library/LaunchDaemons/${SERVICE_NAME}.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${SERVICE_NAME}</string>

    <key>ProgramArguments</key>
    <array>
        <string>${APP_DIR}/bin/gateway</string>
        <string>-config</string>
        <string>${APP_DIR}/config/config.yaml</string>
    </array>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>WorkingDirectory</key>
    <string>${APP_DIR}</string>

    <key>UserName</key>
    <string>${APP_USER}</string>

    <key>GroupName</key>
    <string>staff</string>

    <key>StandardOutPath</key>
    <string>${APP_DIR}/logs/gateway.log</string>

    <key>StandardErrorPath</key>
    <string>${APP_DIR}/logs/gateway-error.log</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>GATEWAY_CONFIG</key>
        <string>${APP_DIR}/config/config.yaml</string>
        <key>GATEWAY_LOG_DIR</key>
        <string>${APP_DIR}/logs</string>
    </dict>

    <key>SoftResourceLimits</key>
    <dict>
        <key>NumberOfFiles</key>
        <integer>4096</integer>
    </dict>

    <key>HardResourceLimits</key>
    <dict>
        <key>NumberOfFiles</key>
        <integer>8192</integer>
    </dict>
</dict>
</plist>
EOF

chmod 644 "/Library/LaunchDaemons/${SERVICE_NAME}.plist"
echo -e "${GREEN}✓ launchd服务已配置${NC}"

echo -e "${GREEN}[4/8] 配置防火墙...${NC}"

# macOS使用应用防火墙或pf
if command -v /usr/libexec/ApplicationFirewall/socketfilterfw &>/dev/null; then
    # 添加到应用防火墙
    /usr/libexec/ApplicationFirewall/socketfilterfw --add "${APP_DIR}/bin/gateway" 2>/dev/null || true
    /usr/libexec/ApplicationFirewall/socketfilterfw --unblockapp "${APP_DIR}/bin/gateway" 2>/dev/null || true
    echo -e "${GREEN}✓ 应用防火墙已配置${NC}"
else
    echo -e "${YELLOW}⚠️  应用防火墙未启用，请手动配置${NC}"
fi

# 配置pf（可选）
if [ -f "/etc/pf.anchors/com.athena.gateway" ]; then
    echo -e "${YELLOW}⚠️  pf规则已存在，跳过${NC}"
else
    cat > "/etc/pf.anchors/com.athena.gateway" << EOF
# Athena Gateway pf规则
anchor "com.athena.gateway"
pass in proto tcp from any to any port 8005
pass in proto tcp from any to any port 8443
pass in proto tcp from any to any port 9090
EOF
    echo -e "${GREEN}✓ pf锚点已创建${NC}"
    echo -e "${YELLOW}⚠️  要启用pf，请运行: sudo pfctl -e${NC}"
fi

echo -e "${GREEN}[5/8] 配置环境变量...${NC}"

# 创建环境配置
cat > "${APP_DIR}/config/env" << EOF
# Athena Gateway 环境配置
GATEWAY_CONFIG=${APP_DIR}/config/config.yaml
GATEWAY_LOG_DIR=${APP_DIR}/logs
GATEWAY_PID_FILE=${APP_DIR}/gateway.pid

# 可选：外部服务配置
# POSTGRES_URL=localhost:5432
# REDIS_URL=localhost:6379
EOF

chmod 640 "${APP_DIR}/config/env"
echo -e "${GREEN}✓ 环境变量已配置${NC}"

echo -e "${GREEN}[6/8] 配置日志轮转...${NC}"

# 配置newsyslog（macOS原生日志轮转）
cat > "/etc/newsyslog.d/${APP_NAME}.conf" << EOF
# Athena Gateway 日志轮转配置
${APP_DIR}/logs/gateway.log ${APP_USER}:staff 640 10 * 48 Z
${APP_DIR}/logs/gateway-error.log ${APP_USER}:staff 640 10 * 48 Z
EOF

echo -e "${GREEN}✓ 日志轮转已配置${NC}"

echo -e "${GREEN}[7/8] 配置备份...${NC}"

# 创建备份脚本
cat > "${APP_DIR}/backup.sh" << 'EOF'
#!/bin/bash
# Athena Gateway 备份脚本

APP_DIR="/usr/local/athena-gateway"
BACKUP_DIR="/backup/athena-gateway"
BACKUP_FILE="${BACKUP_DIR}/config-$(date +%Y%m%d_%H%M%S).tar.gz"

mkdir -p "$BACKUP_DIR"
tar -czf "$BACKUP_FILE" -C "$APP_DIR" config/

# 保留最近30天的备份
find "$BACKUP_DIR" -name "config-*.tar.gz" -mtime +30 -delete

echo "备份完成: $BACKUP_FILE"
EOF

chmod 750 "${APP_DIR}/backup.sh"
chown "$APP_USER:staff" "${APP_DIR}/backup.sh"

# 创建backup目录
mkdir -p /backup/athena-gateway
chown "$APP_USER:staff" /backup/athena-gateway

echo -e "${GREEN}✓ 备份脚本已配置${NC}"

echo -e "${GREEN}[8/8] 创建管理脚本...${NC}"

# 创建启动脚本
cat > "${APP_DIR}/start.sh" << 'EOF'
#!/bin/bash
APP_DIR="/usr/local/athena-gateway"
SERVICE="com.athena.gateway"

sudo launchctl load -w /Library/LaunchDaemons/${SERVICE}.plist
echo "Gateway服务已启动"
EOF

# 创建停止脚本
cat > "${APP_DIR}/stop.sh" << 'EOF'
#!/bin/bash
APP_DIR="/usr/local/athena-gateway"
SERVICE="com.athena.gateway"

sudo launchctl unload -w /Library/LaunchDaemons/${SERVICE}.plist
echo "Gateway服务已停止"
EOF

# 创建状态脚本
cat > "${APP_DIR}/status.sh" << 'EOF'
#!/bin/bash
SERVICE="com.athena.gateway"

if launchctl list | grep -q "$SERVICE"; then
    echo "Gateway服务: 运行中"
    PID=$(launchctl list | grep "$SERVICE" | awk '{print $1}')
    echo "PID: $PID"
else
    echo "Gateway服务: 未运行"
fi

# 健康检查
echo ""
echo "健康检查:"
curl -s http://localhost:8005/health || echo "健康检查失败"
EOF

# 创建日志查看脚本
cat > "${APP_DIR}/logs.sh" << 'EOF'
#!/bin/bash
APP_DIR="/usr/local/athena-gateway"

tail -f "${APP_DIR}/logs/gateway.log"
EOF

chmod 750 "${APP_DIR}"/{start.sh,stop.sh,status.sh,logs.sh}
echo -e "${GREEN}✓ 管理脚本已创建${NC}"

# 完成
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  部署完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}服务信息:${NC}"
echo "  安装目录: $APP_DIR"
echo "  配置文件: $APP_DIR/config/config.yaml"
echo "  服务名称: $SERVICE_NAME"
echo ""
echo -e "${YELLOW}管理命令:${NC}"
echo "  启动服务: sudo launchctl load -w /Library/LaunchDaemons/${SERVICE_NAME}.plist"
echo "  停止服务: sudo launchctl unload -w /Library/LaunchDaemons/${SERVICE_NAME}.plist"
echo "  重启服务: sudo launchctl kickstart -k gui/$(id -u)/${SERVICE_NAME}"
echo "  查看状态: launchctl list | grep $SERVICE_NAME"
echo "  查看日志: $APP_DIR/status.sh 或 tail -f $APP_DIR/logs/gateway.log"
echo "  快捷启动: $APP_DIR/start.sh"
echo "  快捷停止: $APP_DIR/stop.sh"
echo "  快捷状态: $APP_DIR/status.sh"
echo ""
echo -e "${YELLOW}下一步操作:${NC}"
echo "  1. 修改认证密钥: sudo vi $APP_DIR/config/auth.yaml"
echo "  2. 配置TLS证书（如需要）"
echo "  3. 启动服务: $APP_DIR/start.sh"
echo "  4. 验证服务: curl http://localhost:8005/health"
echo ""
