# Athena Gateway 生产环境部署指南

## 部署前检查清单

### 1. 基础设施准备
- [ ] Linux服务器 (推荐Ubuntu 20.04+ 或 CentOS 7+)
- [ ] Go 1.21+ 运行环境
- [ ] 至少2GB可用内存
- [ ] 10GB可用磁盘空间

### 2. 网络配置
- [ ] 确认防火墙端口开放 (8005/8443)
- [ ] 配置SSL证书 (生产环境)
- [ ] 设置域名解析

### 3. 依赖服务
- [ ] Nginx (用于反向代理和TLS)
- [ ] Prometheus (用于监控，可选)

## 快速部署

### 1. 构建网关
```bash
cd gateway-unified
go build -o bin/gateway ./cmd/gateway
```

### 2. 创建配置文件
```bash
cp gateway-config.yaml.example gateway-config.yaml
vi gateway-config.yaml  # 根据需要修改
```

### 3. 启动网关
```bash
./start.sh
```

### 4. 验证运行状态
```bash
./status.sh
curl http://localhost:8005/health
```

## 生产环境配置

### 方案1: 使用Nginx反向代理 (推荐)

#### 1.1 安装Nginx
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install nginx

# CentOS/RHEL
sudo yum install nginx
```

#### 1.2 配置Nginx
```bash
sudo cp nginx.conf.example /etc/nginx/sites-available/gateway
sudo ln -s /etc/nginx/sites-available/gateway /etc/nginx/sites-enabled/
```

编辑配置文件，修改以下内容：
- `server_name gateway.example.com` → 改为你的域名
- SSL证书路径 → 改为实际证书路径

#### 1.3 配置SSL证书
```bash
# 使用Let's Encrypt获取免费证书
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d gateway.example.com

# 或者使用已有证书
# 将证书和私钥放到指定路径
```

#### 1.4 启动服务
```bash
sudo nginx -t  # 测试配置
sudo systemctl reload nginx

# 启动Gateway
./start.sh
```

### 方案2: Gateway内置TLS

#### 2.1 生成自签名证书 (测试环境)
```bash
chmod +x generate-cert.sh
./generate-cert.sh
```

#### 2.2 创建TLS配置
```bash
cp tls-config.yaml.example tls-config.yaml
vi tls-config.yaml  # 修改证书路径
```

#### 2.3 启动Gateway
```bash
GATEWAY_CONFIG=tls-config.yaml ./start.sh
```

## 系统服务配置

### 创建systemd服务
```bash
sudo vi /etc/systemd/system/athena-gateway.service
```

添加以下内容：
```ini
[Unit]
Description=Athena Gateway
After=network.target

[Service]
Type=simple
User=athena
WorkingDirectory=/opt/athena-gateway
ExecStart=/opt/athena-gateway/start.sh
ExecStop=/opt/athena-gateway/stop.sh
Restart=on-failure
RestartSec=10s

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable athena-gateway
sudo systemctl start athena-gateway
sudo systemctl status athena-gateway
```

## 监控和日志

### 日志文件位置
- 应用日志: `logs/gateway.log`
- 日志轮转: 自动按100MB轮转，保留10个备份

### 查看日志
```bash
# 实时查看日志
tail -f logs/gateway.log

# 查看最近100行
tail -n 100 logs/gateway.log
```

### Prometheus监控
网关暴露Prometheus指标，配置prometheus.yml:
```yaml
scrape_configs:
  - job_name: 'athena-gateway'
    static_configs:
      - targets: ['localhost:9090']
```

## 安全配置

### 1. 启用认证
编辑配置文件添加认证配置：
```yaml
auth:
  api_keys:
    - "your-api-key-here"
  bearer_tokens:
    - "your-bearer-token-here"
  ip_whitelist:
    - "10.0.0.0/8"
```

### 2. 防火墙配置
```bash
# Ubuntu/Debian
sudo ufw allow 8005/tcp
sudo ufw allow 8443/tcp

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=8005/tcp
sudo firewall-cmd --reload
```

### 3. 限制访问权限
```bash
# 创建专用运行用户
sudo useradd -r -s /bin/false athena
sudo chown -R athena:athena /opt/athena-gateway
```

## 故障排查

### 网关无法启动
```bash
# 检查日志
cat logs/gateway.log

# 检查端口占用
sudo lsof -i :8005

# 检查配置文件
./bin/gateway --help  # 查看帮助
```

### 健康检查失败
```bash
curl -v http://localhost:8005/health
curl -v https://localhost:8443/health
```

### 性能问题
```bash
# 查看进程状态
./status.sh

# 查看系统资源
top -p $(cat gateway.pid)

# 抓取性能数据
curl http://localhost:9090/metrics
```

## 备份和恢复

### 配置备份
```bash
# 备份配置文件
tar czf gateway-config-$(date +%Y%m%d).tar.gz \
    gateway-config.yaml \
    tls-config.yaml \
    certs/

# 恢复配置
tar xzf gateway-config-20250221.tar.gz
```

### 日志备份
```bash
# 日志已自动轮转备份到logs/目录
# 可以定期归档到其他存储
```

## 更新部署

### 滚动更新 (无停机)
```bash
# 1. 编译新版本
go build -o bin/gateway-new ./cmd/gateway

# 2. 备份当前版本
cp bin/gateway bin/gateway.backup

# 3. 替换二进制文件
mv bin/gateway-new bin/gateway

# 4. 重启服务
./restart.sh
```

### 回滚
```bash
mv bin/gateway.backup bin/gateway
./restart.sh
```
