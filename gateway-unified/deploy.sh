#!/bin/bash
# Athena Gateway 生产环境部署脚本
# 用途: 自动化部署网关到生产环境
# 使用: sudo bash deploy.sh

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
APP_NAME="athena-gateway"
APP_USER="athena"
APP_DIR="/opt/${APP_NAME}"
SERVICE_NAME="${APP_NAME}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Athena Gateway 生产环境部署${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查root权限
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}错误: 请使用root权限运行此脚本 (sudo ./deploy.sh)${NC}"
    exit 1
fi

# 第一步: 创建用户和目录
echo -e "${GREEN}[1/9] 创建部署用户和目录...${NC}"

if id "$APP_USER" &>/dev/null; then
    echo -e "${YELLOW}用户 ${APP_USER} 已存在${NC}"
else
    useradd -r -s /bin/false -d /opt/${APP_NAME} -c "Athena Gateway Service" ${APP_USER}
    echo -e "${GREEN}✓ 创建用户 ${APP_USER}${NC}"
fi

# 创建目录结构
mkdir -p ${APP_DIR}/{bin,config,logs,certs,backup}
echo -e "${GREEN}✓ 创建目录结构${NC}"

# 第二步: 复制文件
echo -e "${GREEN}[2/9] 复制应用文件...${NC}"

cp -f "${SCRIPT_DIR}/bin/gateway" "${APP_DIR}/bin/gateway"
chmod +x "${APP_DIR}/bin/gateway"
echo -e "${GREEN}✓ 复制二进制文件${NC}"

# 复制配置文件
if [ -f "${SCRIPT_DIR}/gateway-config.yaml" ]; then
    cp -f "${SCRIPT_DIR}/gateway-config.yaml" "${APP_DIR}/config/config.yaml"
else
    cp -f "${SCRIPT_DIR}/gateway-config.yaml.example" "${APP_DIR}/config/config.yaml"
fi
echo -e "${GREEN}✓ 复制配置文件${NC}"

# 复制脚本
cp -f "${SCRIPT_DIR}/start.sh" "${APP_DIR}/start.sh"
cp -f "${SCRIPT_DIR}/stop.sh" "${APP_DIR}/stop.sh"
cp -f "${SCRIPT_DIR}/restart.sh" "${APP_DIR}/restart.sh"
cp -f "${SCRIPT_DIR}/status.sh" "${APP_DIR}/status.sh"
chmod +x ${APP_DIR}/*.sh
echo -e "${GREEN}✓ 复制脚本文件${NC}"

# 设置权限
chown -R ${APP_USER}:${APP_USER} ${APP_DIR}
chmod 750 ${APP_DIR}
chmod 640 ${APP_DIR}/config/*
echo -e "${GREEN}✓ 设置文件权限${NC}"

# 第三步: 创建systemd服务
echo -e "${GREEN}[3/9] 配置系统服务...${NC}"

cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=Athena Gateway Unified
Documentation=https://github.com/athena-workspace/gateway-unified
After=network-online.target network.target
Wants=network-online.target

[Service]
Type=forking
User=${APP_USER}
Group=${APP_USER}
WorkingDirectory=${APP_DIR}
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
EnvironmentFile=-${APP_DIR}/config/env
ExecStart=${APP_DIR}/start.sh
ExecStop=${APP_DIR}/stop.sh
ExecReload=${APP_DIR}/restart.sh
PIDFile=${APP_DIR}/gateway.pid
Restart=always
RestartSec=10s
TimeoutStartSec=30
TimeoutStopSec=30

# 资源限制
MemoryMax=512M
CPUQuota=200%
TasksMax=512

# 安全加固
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=${APP_DIR}/logs
ReadWritePaths=${APP_DIR}/config

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
echo -e "${GREEN}✓ 创建systemd服务${NC}"

# 第四步: 配置防火墙
echo -e "${GREEN}[4/9] 配置防火墙...${NC}"

if command -v ufw &> /dev/null; then
    # Ubuntu/Debian
    ufw allow 8005/tcp comment 'Athena Gateway HTTP' 2>/dev/null || true
    ufw allow 8443/tcp comment 'Athena Gateway HTTPS' 2>/dev/null || true
    ufw allow 9090/tcp comment 'Athena Gateway Metrics' 2>/dev/null || true
    echo -e "${GREEN}✓ 配置UFW防火墙${NC}"
elif command -v firewall-cmd &> /dev/null; then
    # CentOS/RHEL
    firewall-cmd --permanent --add-port=8005/tcp --add-port=8443/tcp --add-port=9090/tcp 2>/dev/null || true
    firewall-cmd --reload 2>/dev/null || true
    echo -e "${GREEN}✓ 配置firewalld防火墙${NC}"
else
    echo -e "${YELLOW}⚠️  未检测到防火墙，请手动配置端口规则${NC}"
fi

# 第五步: 创建环境变量文件
echo -e "${GREEN}[5/9] 配置环境变量...${NC}"

cat > ${APP_DIR}/config/env << EOF
# Athena Gateway 环境变量
# 生产环境配置

# 监听配置
export GATEWAY_PORT=8005
export GATEWAY_PRODUCTION=true

# 日志配置
export GATEWAY_LOG_LEVEL=info
export GATEWAY_LOG_FORMAT=json

# 监控配置
export GATEWAY_METRICS_ENABLED=true
export GATEWAY_METRICS_PORT=9090
EOF

chown ${APP_USER}:${APP_USER} ${APP_DIR}/config/env
chmod 640 ${APP_DIR}/config/env
echo -e "${GREEN}✓ 创建环境变量文件${NC}"

# 第六步: 配置日志轮转
echo -e "${GREEN}[6/9] 配置日志轮转...${NC}"

if command -v logrotate &> /dev/null; then
    cat > /etc/logrotate.d/${APP_NAME} << EOF
${APP_DIR}/logs/gateway.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0640 ${APP_USER} ${APP_USER}
    sharedscripts
    postrotate
        ${APP_DIR}/restart.sh >/dev/null 2>&1 || true
    endscript
}
EOF
    echo -e "${GREEN}✓ 配置logrotate${NC}"
else
    echo -e "${YELLOW}⚠️  logrotate未安装，使用内置日志轮转${NC}"
fi

# 第七步: 创建安全配置
echo -e "${GREEN}[7/9] 配置安全策略...${NC}"

# 创建认证配置文件
cat > ${APP_DIR}/config/auth.yaml << EOF
# Athena Gateway 认证配置
# 请根据实际环境修改以下配置

api_keys:
  # 生产环境API密钥 (请修改为强密钥)
  - "prod-api-key-CHANGE-THIS-2024"
  - "prod-api-key-CHANGE-THIS-2025"

bearer_tokens:
  # Bearer Tokens (请修改为强密钥)
  - "prod-bearer-CHANGE-THIS-2024"

ip_whitelist:
  # 允许的IP地址段
  - "10.0.0.0/8"
  - "172.16.0.0/12"
  - "192.168.0.0/16"
  # 管理员IP (请添加实际管理员IP)
  # - "203.0.113.0"
EOF

chown ${APP_USER}:${APP_USER} ${APP_DIR}/config/auth.yaml
chmod 640 ${APP_DIR}/config/auth.yaml
echo -e "${GREEN}✓ 创建认证配置${NC}"

# 第八步: 配置监控
echo -e "${GREEN}[8/9] 配置监控...${NC}"

# 创建Prometheus配置目录
mkdir -p /etc/prometheus/rules

cat > /etc/prometheus/rules/${APP_NAME}.yml << EOF
groups:
  - name: athena_gateway_alerts
    rules:
      - alert: GatewayDown
        expr: up{job="athena-gateway"} == 0
        for: 1m
        labels:
          severity: critical
          service: athena-gateway
        annotations:
          summary: "Athena Gateway is down"
          description: "Athena Gateway has been down for more than 1 minute"

      - alert: HighErrorRate
        expr: rate(gateway_http_requests_total{status=~"5.."}[5m]) / rate(gateway_http_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
          service: athena-gateway
        annotations:
          summary: "High error rate detected"
          description: "Error rate is above 5% for the last 5 minutes"

      - alert: HighMemoryUsage
        expr: process_resident_memory_bytes{job="athena-gateway"} / 1024 / 1024 > 400
        for: 5m
        labels:
          severity: warning
          service: athena-gateway
        annotations:
          summary: "High memory usage"
          description: "Memory usage is above 400MB"
EOF

echo -e "${GREEN}✓ 配置Prometheus告警规则${NC}"

# 第九步: 创建备份脚本
echo -e "${GREEN}[9/9] 配置备份策略...${NC}"

cat > ${APP_DIR}/backup.sh << 'EOF'
#!/bin/bash
# Athena Gateway 备份脚本

set -e

BACKUP_DIR="/backup/athena-gateway"
DATE=$(date +%Y%m%d_%H%M%S)
APP_DIR="/opt/athena-gateway"

mkdir -p "${BACKUP_DIR}"

echo "开始备份 Athena Gateway..."

# 备份配置文件
tar czf "${BACKUP_DIR}/config-${DATE}.tar.gz" \
    -C "${APP_DIR}/config" \
    config.yaml \
    auth.yaml \
    env 2>/dev/null || true

# 备份证书（如果存在）
if [ -d "${APP_DIR}/certs" ]; then
    tar czf "${BACKUP_DIR}/certs-${DATE}.tar.gz" -C "${APP_DIR}" certs/
fi

# 清理30天前的备份
find "${BACKUP_DIR}" -name "*.tar.gz" -mtime +30 -delete

echo "备份完成: ${BACKUP_DIR}/config-${DATE}.tar.gz"
EOF

chmod +x ${APP_DIR}/backup.sh
chown ${APP_USER}:${APP_USER} ${APP_DIR}/backup.sh

# 添加定时任务 (每天凌晨2点备份)
(crontab -l 2>/dev/null | grep -v backup.sh; echo "0 2 * * * ${APP_DIR}/backup.sh >/dev/null 2>&1") | crontab -
echo -e "${GREEN}✓ 配置自动备份${NC}"

# 完成部署
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}🎉 部署完成！${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "应用目录: ${APP_DIR}"
echo "服务名称: ${SERVICE_NAME}"
echo ""
echo -e "${YELLOW}常用命令:${NC}"
echo "  启动服务: systemctl start ${SERVICE_NAME}"
echo "  停止服务: systemctl stop ${SERVICE_NAME}"
echo "  重启服务: systemctl restart ${SERVICE_NAME}"
echo "  查看状态: systemctl status ${SERVICE_NAME}"
echo "  查看日志: journalctl -u ${SERVICE_NAME} -f"
echo "  查看服务: ./status.sh"
echo ""
echo -e "${YELLOW}配置文件:${NC}"
echo "  主配置: ${APP_DIR}/config/config.yaml"
echo "  认证配置: ${APP_DIR}/config/auth.yaml"
echo "  环境变量: ${APP_DIR}/config/env"
echo ""
echo -e "${YELLOW}下一步操作:${NC}"
echo "  1. 编辑配置文件: vi ${APP_DIR}/config/config.yaml"
echo "  2. 修改认证密钥: vi ${APP_DIR}/config/auth.yaml"
echo "  3. 启动服务: systemctl start ${SERVICE_NAME}"
echo "  4. 检查状态: systemctl status ${SERVICE_NAME}"
echo ""
echo -e "${RED}⚠️  重要安全提醒:${NC}"
echo "  1. 修改 config.yaml 中的端口和TLS配置"
echo "  2. 修改 auth.yaml 中的API密钥和Token"
echo "  3. 配置SSL证书（生产环境必须）"
echo "  4. 检查防火墙规则"
echo ""
