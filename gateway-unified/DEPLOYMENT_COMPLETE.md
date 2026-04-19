# Athena Gateway 生产环境部署完整指南

## 🚀 快速开始

### 一键部署 (推荐)

```bash
# 1. 确保以root权限运行
sudo bash quick-deploy.sh
```

这将自动完成：
- 部署应用到 `/opt/athena-gateway`
- 配置systemd服务
- 设置防火墙规则
- 运行安全检查
- 启动服务

### 手动部署

如果需要自定义部署，请执行以下步骤：

```bash
# 1. 部署
sudo bash deploy.sh

# 2. 配置（可选，修改配置后）
vi /opt/athena-gateway/config/config.yaml

# 3. 安全检查
sudo bash security-check.sh

# 4. 启动服务
systemctl start athena-gateway
```

## 📋 部署前准备

### 1. 系统要求

| 要求 | 最低配置 | 推荐配置 |
|------|----------|----------|
| 操作系统 | Ubuntu 20.04+ / CentOS 7+ | Ubuntu 22.04 LTS |
| CPU | 2核 | 4核+ |
| 内存 | 2GB | 4GB+ |
| 磁盘 | 10GB | 50GB+ |
| Go | 1.21+ | 1.23+ |

### 2. 依赖检查

```bash
# 检查Go版本
go version

# 检查端口占用
sudo lsof -i :8005
sudo lsof -i :8443
```

## 🔧 部署步骤详解

### 步骤1: 部署

```bash
sudo bash deploy.sh
```

部署脚本会：
- 创建专用用户 `athena` (无shell登录权限)
- 创建目录 `/opt/athena-gateway/`
- 配置systemd服务
- 设置防火墙规则 (UFW/firewalld)
- 配置logrotate日志轮转
- 创建Prometheus告警规则
- 设置自动备份

### 步骤2: 安全配置

#### 2.1 修改认证密钥（必须）

```bash
vi /opt/athena-gateway/config/auth.yaml
```

修改以下内容：
- `api_keys`: 替换为强密钥
- `bearer_tokens`: 替换为强Token
- `ip_whitelist`: 添加允许的IP段

#### 2.2 配置SSL/TLS

**选项A: 使用Nginx反向代理（推荐）**

```bash
# 安装Nginx
sudo apt-get install nginx

# 配置
sudo cp nginx.conf.example /etc/nginx/sites-available/gateway
sudo vi /etc/nginx/sites-available/gateway  # 修改域名和证书路径

# 启用
sudo ln -s /etc/nginx/sites-available/gateway /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

**选项B: Gateway内置TLS**

```bash
# 生成证书（测试环境）
/opt/athena-gateway/generate-cert.sh

# 生产环境
# 将证书放到 /opt/athena-gateway/certs/
# 修改配置启用TLS
```

### 步骤3: 启动服务

```bash
# 启动
systemctl start athena-gateway

# 查看状态
systemctl status athena-gateway

# 查看日志
journalctl -u athena-gateway -f
```

### 步骤4: 验证部署

```bash
# 健康检查
curl http://localhost:8005/health

# 查看服务状态
/opt/athena-gateway/status.sh

# 检查端口
sudo lsof -i :8005
```

## 🔒 安全加固

### 1. 用户权限

应用以专用用户 `athena` 运行：
- 无shell登录 (`/bin/false`)
- 最小权限原则
- 资源限制（内存512MB，CPU 200%）

### 2. 文件权限

| 文件/目录 | 权限 | 所有者 |
|----------|------|--------|
| `/opt/athena-gateway/` | 750 | athena:athena |
| `bin/gateway` | 750 | athena:athena |
| `config/` | 750 | athena:athena |
| `config/*.yaml` | 640 | athena:athena |
| `logs/` | 750 | athena:athena |

### 3. 防火墙

确保只开放必要端口：
- **8005** - HTTP (可选，建议只用HTTPS)
- **8443** - HTTPS
- **9090** - Prometheus指标

### 4. 认证配置

三层防护：
- IP白名单（网络层）
- API Key/Token（应用层）
- Basic Auth（可选）

### 5. 系统安全加固

systemd服务已启用：
- `NoNewPrivileges` - 禁止获取新权限
- `PrivateTmp` - 私有/tmp目录
- `ProtectSystem=strict` - 只读系统路径

## 📊 监控配置

### Prometheus配置

添加到 `/etc/prometheus/prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'athena-gateway'
    static_configs:
      - targets: ['localhost:9090']
    scrape_interval: 15s
```

### Grafana仪表板

```bash
# 导入仪表板
curl http://localhost:3000/api/dashboards/import \
  -H "Content-Type: application/json" \
  -u admin:admin \
  -X POST \
  -d @grafana-dashboard.json
```

### 告警规则

告警规则已配置到 `/etc/prometheus/rules/athena-gateway.yml`：

- **GatewayDown**: 服务宕机
- **HighErrorRate**: 错误率>5%
- **HighMemoryUsage**: 内存>400MB

## 🔄 运维操作

### 配置更新

```bash
# 方式1: 使用配置更新脚本
./update-config.sh new-config.yaml

# 方式2: 手动更新
vi /opt/athena-gateway/config/config.yaml
systemctl reload athena-gateway
```

### 日志查看

```bash
# 实时日志
journalctl -u athena-gateway -f

# 最近100行
journalctl -u athena-gateway -n 100

# 应用日志
tail -f /opt/athena-gateway/logs/gateway.log
```

### 服务管理

```bash
# 启动
systemctl start athena-gateway

# 停止
systemctl stop athena-gateway

# 重启
systemctl restart athena-gateway

# 开机自启
systemctl enable athena-gateway

# 禁用自启
systemctl disable athena-gateway

# 查看状态
systemctl status athena-gateway
```

### 备份与恢复

```bash
# 手动备份
/opt/athena-gateway/backup.sh

# 查看备份
ls -lh /backup/athena-gateway/

# 恢复配置
cp /backup/athena-gateway/config-20250221_120000.tar.gz \
   /opt/athena-gateway/config/config.yaml
systemctl restart athena-gateway
```

## 🐛 故障排查

### 问题1: 服务无法启动

```bash
# 查看服务状态
systemctl status athena-gateway

# 查看详细日志
journalctl -u athena-gateway -n 50

# 检查配置
/opt/athena-gateway/status.sh

# 检查端口占用
sudo lsof -i :8005
```

### 问题2: 认证失败

```bash
# 检查认证配置
cat /opt/athena-gateway/config/auth.yaml

# 检查服务状态
curl -H "X-API-Key: your-key" http://localhost:8005/health
```

### 问题3: 性能问题

```bash
# 查看资源使用
systemctl status athena-gateway

# 查看进程
ps aux | grep gateway

# 查看连接数
curl http://localhost:9090/metrics | grep active_connections
```

### 问题4: 完全重置

如果需要完全卸载重新部署：

```bash
# 卸载
sudo bash uninstall.sh

# 重新部署
sudo bash quick-deploy.sh
```

## 📈 性能优化

### 推荐配置

**高负载场景**:
```yaml
server:
  read_timeout: 60
  write_timeout: 60
  idle_timeout: 300
```

**低延迟场景**:
```yaml
server:
  read_timeout: 10
  write_timeout: 10
  idle_timeout: 60
```

## 🔔 生产环境检查清单

部署前必须确认：

- [ ] 已修改所有默认密钥
- [ ] 已配置SSL/TLS证书
- [ ] 已配置防火墙规则
- [ ] 已设置IP白名单
- [ ] 已配置监控告警
- [ ] 已配置自动备份
- [ ] 已进行负载测试

## 📞 支持与帮助

- 查看日志: `journalctl -u athena-gateway -f`
- 检查状态: `/opt/athena-gateway/status.sh`
- 配置文件: `/opt/athena-gateway/config/config.yaml`
