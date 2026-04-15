# Athena Gateway macOS 生产环境部署完整指南

## 🚀 快速开始

### 一键部署 (推荐)

```bash
# 1. 确保以root权限运行
sudo bash quick-deploy-macos.sh
```

这将自动完成：
- 部署应用到 `/usr/local/athena-gateway`
- 配置launchd服务
- 设置防火墙规则
- 运行安全检查
- 创建管理脚本

### 手动部署

如果需要自定义部署，请执行以下步骤：

```bash
# 1. 部署
sudo bash deploy-macos.sh

# 2. 配置（可选，修改配置后）
sudo vi /usr/local/athena-gateway/config/config.yaml

# 3. 安全检查
sudo bash security-check-macos.sh

# 4. 启动服务
sudo /usr/local/athena-gateway/start.sh
```

## 📋 部署前准备

### 1. 系统要求

| 要求 | 最低配置 | 推荐配置 |
|------|----------|----------|
| 操作系统 | macOS 11 (Big Sur) | macOS 14 (Sonoma) |
| CPU | Apple M1 / Intel x64 | Apple M2/M3 Pro |
| 内存 | 4GB | 8GB+ |
| 磁盘 | 500MB | 2GB+ |
| Go | 1.21+ | 1.23+ |

### 2. 依赖检查

```bash
# 检查Go版本
go version

# 检查端口占用
lsof -i :8005
lsof -i :8443
lsof -i :9090
```

## 🔧 部署步骤详解

### 步骤1: 部署

```bash
sudo bash deploy-macos.sh
```

部署脚本会：
- 创建专用用户 `_athena` (无shell登录权限)
- 创建目录 `/usr/local/athena-gateway/`
- 配置launchd服务
- 设置防火墙规则
- 配置newsyslog日志轮转
- 创建备份脚本

### 步骤2: 安全配置

#### 2.1 修改认证密钥（必须）

```bash
sudo vi /usr/local/athena-gateway/config/auth.yaml
```

修改以下内容：
- `api_keys`: 替换为强密钥
- `bearer_tokens`: 替换为强Token
- `ip_whitelist`: 添加允许的IP段

#### 2.2 配置SSL/TLS

**选项A: 使用内置TLS**

```bash
# 生成证书（测试环境）
/usr/local/athena-gateway/generate-cert.sh

# 生产环境
# 将证书放到 /usr/local/athena-gateway/certs/
# 修改配置启用TLS
```

**选项B: 使用Nginx反向代理**

```bash
# 安装Nginx
brew install nginx

# 配置
sudo cp nginx.conf.example /opt/homebrew/etc/nginx/servers/gateway.conf
sudo vi /opt/homebrew/etc/nginx/servers/gateway.conf  # 修改域名和证书路径

# 重启Nginx
brew services restart nginx
```

### 步骤3: 启动服务

```bash
# 使用快捷脚本
sudo /usr/local/athena-gateway/start.sh

# 或直接使用launchctl
sudo launchctl load -w /Library/LaunchDaemons/com.athena.gateway.plist

# 查看状态
launchctl list | grep com.athena.gateway
```

### 步骤4: 验证部署

```bash
# 健康检查
curl http://localhost:8005/health

# 查看服务状态
sudo /usr/local/athena-gateway/status.sh

# 检查端口
lsof -i :8005
```

## 🔒 安全加固

### 1. 用户权限

应用以专用用户 `_athena` 运行：
- 无shell登录 (`/usr/bin/false`)
- 最小权限原则
- 文件描述符限制：软4096，硬8192

### 2. 文件权限

| 文件/目录 | 权限 | 所有者 |
|----------|------|--------|
| `/usr/local/athena-gateway/` | 750 | _athena:staff |
| `bin/gateway` | 750 | _athena:staff |
| `config/` | 750 | _athena:staff |
| `config/*.yaml` | 640 | _athena:staff |
| `logs/` | 750 | _athena:staff |

### 3. 防火墙

macOS提供两种防火墙选项：

**应用防火墙** (自动配置):
```bash
# 检查状态
/usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate

# 添加Gateway
/usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/local/athena-gateway/bin/gateway
/usr/libexec/ApplicationFirewall/socketfilterfw --unblockapp /usr/local/athena-gateway/bin/gateway
```

**pf防火墙** (高级):
```bash
# 启用pf
sudo pfctl -e

# 加载规则
sudo pfctl -f /etc/pf.anchors/com.athena.gateway

# 查看状态
sudo pfctl -s info
```

### 4. 认证配置

三层防护：
- IP白名单（网络层）
- API Key/Token（应用层）
- Basic Auth（可选）

### 5. 系统安全加固

launchd服务已启用：
- `UserName`: 以专用用户运行
- `GroupName`: staff组
- `SoftResourceLimits`: 文件描述符限制
- `WorkingDirectory`: 指定工作目录

## 📊 监控配置

### 启动Prometheus采集

如果使用Prometheus监控，添加到配置：

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

## 🔄 运维操作

### 服务管理

```bash
# 启动
sudo /usr/local/athena-gateway/start.sh
# 或
sudo launchctl load -w /Library/LaunchDaemons/com.athena.gateway.plist

# 停止
sudo /usr/local/athena-gateway/stop.sh
# 或
sudo launchctl unload -w /Library/LaunchDaemons/com.athena.gateway.plist

# 重启
sudo launchctl kickstart -k gui/$(id -u)/com.athena.gateway

# 查看状态
launchctl list | grep com.athena.gateway
# 或
sudo /usr/local/athena-gateway/status.sh
```

### 日志查看

```bash
# 实时日志
sudo /usr/local/athena-gateway/logs.sh
# 或
tail -f /usr/local/athena-gateway/logs/gateway.log

# launchd日志
log show --predicate 'process == "gateway"' --last 1h
```

### 配置更新

```bash
# 编辑配置
sudo vi /usr/local/athena-gateway/config/config.yaml

# 重启服务应用
sudo /usr/local/athena-gateway/stop.sh
sudo /usr/local/athena-gateway/start.sh
```

### 备份与恢复

```bash
# 手动备份
sudo /usr/local/athena-gateway/backup.sh

# 查看备份
ls -lh /backup/athena-gateway/

# 恢复配置
sudo tar -xzf /backup/athena-gateway/config-20250221_120000.tar.gz -C /usr/local/athena-gateway/
sudo /usr/local/athena-gateway/stop.sh
sudo /usr/local/athena-gateway/start.sh
```

## 🐛 故障排查

### 问题1: 服务无法启动

```bash
# 查看服务状态
launchctl list | grep com.athena.gateway

# 查看详细日志
tail -50 /usr/local/athena-gateway/logs/gateway-error.log

# 检查配置
sudo /usr/local/athena-gateway/status.sh

# 检查端口占用
lsof -i :8005
```

### 问题2: 权限错误

```bash
# 检查文件权限
ls -la /usr/local/athena-gateway/

# 修复权限
sudo chown -R _athena:staff /usr/local/athena-gateway/
sudo chmod 750 /usr/local/athena-gateway
sudo chmod 640 /usr/local/athena-gateway/config/*.yaml
```

### 问题3: 防火墙阻止

```bash
# 检查防火墙状态
/usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate

# 临时禁用防火墙测试
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate off

# 重新启用
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on
```

### 问题4: 完全重置

如果需要完全卸载重新部署：

```bash
# 卸载
sudo bash uninstall-macos.sh

# 重新部署
sudo bash quick-deploy-macos.sh
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

### launchd性能调优

编辑 `/Library/LaunchDaemons/com.athena.gateway.plist`:

```xml
<key>SoftResourceLimits</key>
<dict>
    <key>NumberOfFiles</key>
    <integer>8192</integer>
    <key>Memory</key>
    <integer>1073741824</integer>  <!-- 1GB -->
</dict>
```

## 🔔 生产环境检查清单

部署前必须确认：

- [ ] 已修改所有默认密钥
- [ ] 已配置SSL/TLS证书
- [ ] 已配置防火墙规则
- [ ] 已设置IP白名单
- [ ] 已配置监控
- [ ] 已配置自动备份
- [ ] 已进行负载测试

## 📞 支持与帮助

- 查看日志: `tail -f /usr/local/athena-gateway/logs/gateway.log`
- 检查状态: `sudo /usr/local/athena-gateway/status.sh`
- 配置文件: `sudo vi /usr/local/athena-gateway/config/config.yaml`

## 🆚 macOS vs Linux 部署差异

| 特性 | macOS | Linux |
|------|-------|-------|
| 服务管理 | launchd | systemd |
| 安装路径 | `/usr/local/` | `/opt/` |
| 用户管理 | `sysadminctl/dscl` | `useradd` |
| 防火墙 | 应用防火墙/pf | ufw/firewalld |
| 日志轮转 | newsyslog | logrotate |
| PID文件 | launchctl管理 | 自定义 |
| 资源限制 | launchd plist | systemd配置 |
