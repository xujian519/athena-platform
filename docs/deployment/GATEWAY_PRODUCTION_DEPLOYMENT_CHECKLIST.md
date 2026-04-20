# Athena Gateway 生产环境部署清单

> **版本**: 1.0.0
> **更新日期**: 2026-04-20
> **部署状态**: 准备就绪 ✅

---

## 📋 部署前检查清单

### 1. 安全配置 ✅

- [x] **JWT密钥已生成**: 256位随机密钥
- [x] **API密钥已生成**: 2个128位密钥
- [x] **环境变量已配置**: `.env`文件已创建
- [x] **.gitignore已更新**: 防止敏感信息泄露
- [x] **安全中间件已集成**: JWT、CORS、安全头、API密钥

### 2. 配置文件 ✅

- [x] **config.yaml**: 使用环境变量引用
- [x] **config.yaml.secure**: 安全配置模板
- [x] **security.example.yaml**: 完整安全配置示例
- [x] **.env**: 生产环境密钥文件

### 3. 编译和测试 ✅

- [x] **Gateway编译成功**: 无编译错误
- [x] **单元测试通过**: 22个安全测试全部通过
- [x] **功能验证通过**: Gateway正常运行
- [x] **API密钥认证**: 有效密钥可访问，无效密钥被拒绝

### 4. 文档完整性 ✅

- [x] **安全修复报告**: `GATEWAY_SECURITY_FIX_REPORT.md`
- [x] **完成总结**: `SECURITY_FIX_COMPLETION_SUMMARY.md`
- [x] **安全使用指南**: `GATEWAY_SECURITY_GUIDE.md`
- [x] **部署指南**: `GATEWAY_DEPLOYMENT_GUIDE.md`
- [x] **API文档**: `GATEWAY_API_GUIDE.md`

---

## 🚀 生产环境部署步骤

### 步骤1: 准备生产服务器

```bash
# 1. 创建Gateway用户
sudo useradd -r -s /bin/false athena-gateway

# 2. 创建安装目录
sudo mkdir -p /usr/local/athena-gateway
sudo mkdir -p /usr/local/athena-gateway/logs
sudo mkdir -p /usr/local/athena-gateway/config

# 3. 设置权限
sudo chown -R athena-gateway:athena-gateway /usr/local/athena-gateway
sudo chmod 750 /usr/local/athena-gateway
sudo chmod 750 /usr/local/athena-gateway/logs
```

### 步骤2: 部署二进制文件

```bash
# 1. 复制Gateway二进制文件
sudo cp gateway-unified/bin/gateway /usr/local/athena-gateway/
sudo chmod +x /usr/local/athena-gateway/gateway

# 2. 复制配置文件
sudo cp gateway-unified/config.yaml /usr/local/athena-gateway/config/
sudo cp -r gateway-unified/config/routes.yaml /usr/local/athena-gateway/config/
sudo cp -r gateway-unified/config/services.yaml /usr/local/athena-gateway/config/

# 3. 设置配置文件权限
sudo chmod 640 /usr/local/athena-gateway/config/*
sudo chown -R athena-gateway:athena-gateway /usr/local/athena-gateway/config
```

### 步骤3: 配置生产环境变量

```bash
# 1. 生成生产环境密钥
JWT_SECRET=$(openssl rand -base64 32)
API_KEY_1=$(openssl rand -hex 16)
API_KEY_2=$(openssl rand -hex 16)

# 2. 创建环境变量文件
sudo tee /usr/local/athena-gateway/.env > /dev/null <<EOF
JWT_SECRET=$JWT_SECRET
API_KEY_1=$API_KEY_1
API_KEY_2=$API_KEY_2
FRONTEND_URL=https://your-frontend-domain.com
EOF

# 3. 设置严格的文件权限
sudo chmod 600 /usr/local/athena-gateway/.env
sudo chown athena-gateway:athena-gateway /usr/local/athena-gateway/.env

# 4. 记录密钥（安全存储）
echo "生产环境密钥已生成，请妥善保存："
echo "JWT_SECRET: $JWT_SECRET"
echo "API_KEY_1: $API_KEY_1"
echo "API_KEY_2: $API_KEY_2"
```

### 步骤4: 创建systemd服务

```bash
# 1. 创建服务文件
sudo tee /etc/systemd/system/athena-gateway.service > /dev/null <<EOF
[Unit]
Description=Athena Gateway Unified
Documentation=https://github.com/athena-workspace/gateway
After=network.target
Wants=network.target

[Service]
Type=simple
User=athena-gateway
Group=athena-gateway

WorkingDirectory=/usr/local/athena-gateway

# 环境变量
EnvironmentFile=-/usr/local/athena-gateway/.env

# 执行命令
ExecStart=/usr/local/athena-gateway/gateway -config /usr/local/athena-gateway/config/config.yaml
ExecReload=/bin/kill -HUP \$MAINPID

# 重启策略
Restart=always
RestartSec=5
StartLimitInterval=0

# 安全设置
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/usr/local/athena-gateway/logs

# 日志
StandardOutput=append:/usr/local/athena-gateway/logs/gateway.log
StandardError=append:/usr/local/athena-gateway/logs/gateway-error.log

[Install]
WantedBy=multi-user.target
EOF

# 2. 重新加载systemd配置
sudo systemctl daemon-reload

# 3. 启用服务（开机自启）
sudo systemctl enable athena-gateway

# 4. 启动服务
sudo systemctl start athena-gateway

# 5. 查看服务状态
sudo systemctl status athena-gateway
```

### 步骤5: 配置防火墙

```bash
# 1. 允许Gateway端口
sudo firewall-cmd --permanent --add-port=8005/tcp
sudo firewall-cmd --permanent --add-port=9091/tcp

# 2. 如果使用HTTPS，允许443端口
sudo firewall-cmd --permanent --add-service=https

# 3. 重载防火墙规则
sudo firewall-cmd --reload

# 4. 查看防火墙规则
sudo firewall-cmd --list-all
```

### 步骤6: 配置Nginx反向代理（可选）

```bash
# 1. 创建Nginx配置
sudo tee /etc/nginx/conf.d/athena-gateway.conf > /dev/null <<EOF
server {
    listen 80;
    server_name gateway.yourdomain.com;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name gateway.yourdomain.com;

    # SSL证书
    ssl_certificate /etc/ssl/certs/gateway.crt;
    ssl_certificate_key /etc/ssl/private/gateway.key;

    # SSL配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # 日志
    access_log /var/log/nginx/gateway-access.log;
    error_log /var/log/nginx/gateway-error.log;

    # 代理配置
    location / {
        proxy_pass http://127.0.0.1:8005;
        proxy_http_version 1.1;

        # 代理头
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # WebSocket支持
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";

        # 超时配置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 监控端点（限制访问）
    location /metrics {
        proxy_pass http://127.0.0.1:9091/metrics;
        allow 127.0.0.1;
        allow 10.0.0.0/8;
        deny all;
    }
}
EOF

# 2. 测试Nginx配置
sudo nginx -t

# 3. 重载Nginx
sudo systemctl reload nginx
```

### 步骤7: 配置监控和告警

```bash
# 1. 配置Prometheus抓取
sudo tee /etc/prometheus/prometheus.d/gateway.yml > /dev/null <<EOF
- job_name: 'athena-gateway'
  scrape_interval: 15s
  static_configs:
    - targets: ['localhost:9091']
    labels:
      service: 'gateway'
      environment: 'production'
EOF

# 2. 重启Prometheus
sudo systemctl restart prometheus

# 3. 配置Grafana仪表板
# 导入仪表板: docs/monitoring/gateway-dashboard.json
```

---

## ✅ 部署验证清单

### 1. 服务状态检查

```bash
# 检查服务状态
sudo systemctl status athena-gateway

# 检查端口监听
sudo netstat -tlnp | grep :8005
sudo netstat -tlnp | grep :9091

# 检查进程
ps aux | grep gateway
```

### 2. 健康检查

```bash
# 基本健康检查
curl http://localhost:8005/health

# 预期响应
{
  "success": true,
  "data": {
    "status": "UP",
    "instances": 10,
    "routes": 6
  }
}
```

### 3. 安全功能验证

```bash
# 测试API密钥认证
curl http://localhost:8005/api/routes \
  -H "X-API-Key: YOUR_API_KEY"

# 测试CORS
curl -I -H "Origin: https://yourdomain.com" \
  http://localhost:8005/health

# 测试安全响应头
curl -I http://localhost:8005/ | grep -E "X-Frame|X-Content|X-XSS"
```

### 4. 性能基准测试

```bash
# 使用Apache Bench进行压力测试
ab -n 1000 -c 10 http://localhost:8005/health

# 预期结果
# - 请求成功率: >99%
# - 平均响应时间: <100ms
# - 95百分位响应时间: <200ms
```

---

## 🔧 运维和维护

### 日常维护任务

**每日**:
- [ ] 检查服务状态
- [ ] 查看错误日志
- [ ] 监控资源使用

**每周**:
- [ ] 检查日志文件大小
- [ ] 审查安全日志
- [ ] 验证备份完整性

**每月**:
- [ ] 更新API密钥（可选）
- [ ] 审查访问权限
- [ ] 性能优化分析
- [ ] 安全漏洞扫描

### 密钥轮换流程

```bash
# 1. 生成新密钥
NEW_JWT_SECRET=$(openssl rand -base64 32)
NEW_API_KEY=$(openssl rand -hex 16)

# 2. 更新.env文件
sudo sed -i "s/JWT_SECRET=.*/JWT_SECRET=$NEW_JWT_SECRET/" /usr/local/athena-gateway/.env
sudo sed -i "s/API_KEY_1=.*/API_KEY_1=$NEW_API_KEY/" /usr/local/athena-gateway/.env

# 3. 重启服务
sudo systemctl restart athena-gateway

# 4. 通知客户端更新密钥
```

### 故障排查指南

**服务无法启动**:
```bash
# 查看服务日志
sudo journalctl -u athena-gateway -n 50

# 检查配置文件
sudo -u athena-gateway /usr/local/athena-gateway/gateway -config /usr/local/athena-gateway/config/config.yaml -check

# 检查端口占用
sudo netstat -tlnp | grep :8005
```

**API认证失败**:
```bash
# 验证环境变量
sudo cat /usr/local/athena-gateway/.env

# 测试API密钥
curl -v http://localhost:8005/api/routes -H "X-API-Key: YOUR_KEY"
```

---

## 📊 监控指标

### 关键性能指标（KPI）

| 指标 | 目标值 | 告警阈值 |
|------|--------|---------|
| 可用性 | 99.9% | <99% |
| 平均响应时间 | <100ms | >200ms |
| 错误率 | <0.1% | >1% |
| 请求吞吐量 | >100 QPS | <50 QPS |
| 内存使用 | <512MB | >1GB |
| CPU使用 | <50% | >80% |

### Prometheus查询示例

```promql
# 可用性
rate(gateway_requests_total{status="200"}[5m])

# 响应时间
rate(gateway_request_duration_seconds_sum[5m]) / rate(gateway_request_duration_seconds_count[5m])

# 错误率
rate(gateway_requests_total{status=~"5.."}[5m]) / rate(gateway_requests_total[5m])
```

---

## 🚨 应急响应计划

### 场景1: 服务宕机

```bash
# 1. 立即检查服务状态
sudo systemctl status athena-gateway

# 2. 尝试重启服务
sudo systemctl restart athena-gateway

# 3. 如果重启失败，查看日志
sudo journalctl -u athena-gateway -n 100

# 4. 回滚到上一版本
sudo systemctl stop athena-gateway
sudo cp /usr/local/athena-gateway/gateway.backup /usr/local/athena-gateway/gateway
sudo systemctl start athena-gateway
```

### 场景2: 密钥泄露

```bash
# 1. 立即轮换所有密钥
NEW_JWT=$(openssl rand -base64 32)
NEW_KEY1=$(openssl rand -hex 16)
NEW_KEY2=$(openssl rand -hex 16)

# 2. 更新配置
sudo systemctl stop athena-gateway
sudo sed -i "s/JWT_SECRET=.*/JWT_SECRET=$NEW_JWT/" /usr/local/athena-gateway/.env
sudo sed -i "s/API_KEY_1=.*/API_KEY_1=$NEW_KEY1/" /usr/local/athena-gateway/.env
sudo sed -i "s/API_KEY_2=.*/API_KEY_2=$NEW_KEY2/" /usr/local/athena-gateway/.env

# 3. 重启服务
sudo systemctl start athena-gateway

# 4. 通知所有客户端更新密钥
```

### 场景3: 性能下降

```bash
# 1. 检查系统资源
top
htop

# 2. 检查网络连接
sudo netstat -an | grep :8005 | wc -l

# 3. 查看慢查询日志
sudo tail -100 /usr/local/athena-gateway/logs/gateway.log | grep "duration"

# 4. 如果必要，增加资源或进行扩容
```

---

## 📞 联系方式

- **技术支持**: xujian519@gmail.com
- **安全问题**: security@athena.example.com
- **运维团队**: ops@athena.example.com

---

**文档版本**: 1.0.0
**最后更新**: 2026-04-20
**状态**: ✅ 生产就绪
