# 小诺·双鱼座 - 生产环境部署指南
# Xiaonuo Pisces - Production Deployment Guide

**版本**: v1.0.0
**更新时间**: 2026-02-09
**适用环境**: Linux (Ubuntu 20.04+, CentOS 7+)

---

## 📋 目录

1. [系统要求](#系统要求)
2. [安装步骤](#安装步骤)
3. [配置说明](#配置说明)
4. [服务管理](#服务管理)
5. [健康检查](#健康检查)
6. [日志管理](#日志管理)
7. [备份恢复](#备份恢复)
8. [故障排查](#故障排查)

---

## 系统要求

### 硬件要求

| 资源 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU | 2核心 | 4核心+ |
| 内存 | 512MB | 1GB+ |
| 磁盘 | 5GB | 20GB+ |
| 网络 | 100Mbps | 1Gbps+ |

### 软件要求

- **操作系统**: Linux (Ubuntu 20.04+, CentOS 7+)
- **Python**: 3.11+
- **PostgreSQL**: 15+
- **Redis**: 7+

---

## 安装步骤

### 1. 创建用户

```bash
# 创建xiaonuo用户
sudo useradd -r -s /bin/bash -d /opt/xiaonuo xiaonuo

# 设置密码（可选）
sudo passwd xiaonuo
```

### 2. 创建目录结构

```bash
# 创建目录
sudo mkdir -p /opt/xiaonuo
sudo mkdir -p /var/log/xiaonuo
sudo mkdir -p /var/lib/xiaonuo
sudo mkdir -p /var/run/xiaonuo
sudo mkdir -p /var/backups/xiaonuo
sudo mkdir -p /etc/xiaonuo

# 设置权限
sudo chown -R xiaonuo:xiaonuo /opt/xiaonuo
sudo chown -R xiaonuo:xiaonuo /var/log/xiaonuo
sudo chown -R xiaonuo:xiaonuo /var/lib/xiaonuo
sudo chown -R xiaonuo:xiaonuo /var/run/xiaonuo
sudo chown -R xiaonuo:xiaonuo /var/backups/xiaonuo
sudo chown -R root:root /etc/xiaonuo
sudo chmod 755 /etc/xiaonuo
```

### 3. 部署应用代码

```bash
# 复制代码到目标目录
sudo cp -r /path/to/Athena工作平台/* /opt/xiaonuo/

# 设置权限
sudo chown -R xiaonuo:xiaonuo /opt/xiaonuo
```

### 4. 配置环境变量

```bash
# 复制环境变量模板
sudo cp /opt/xiaonuo/.env.production.xiaonuo /etc/xiaonuo/xiaonuo.conf

# 编辑配置文件
sudo nano /etc/xiaonuo/xiaonuo.conf

# 填写必要的配置值：
# - API密钥
# - 数据库密码
# - 其他敏感信息
```

### 5. 配置systemd服务

```bash
# 复制服务文件
sudo cp /opt/xiaonuo/deploy/xiaonuo.service /etc/systemd/system/

# 重载systemd
sudo systemctl daemon-reload

# 启用服务
sudo systemctl enable xiaonuo
```

### 6. 启动服务

```bash
# 启动服务
sudo systemctl start xiaonuo

# 检查状态
sudo systemctl status xiaonuo

# 查看日志
sudo journalctl -u xiaonuo -f
```

---

## 配置说明

### 主配置文件

**位置**: `/opt/xiaonuo/config/production/xiaonuo_production.yaml`

**主要配置项**:

```yaml
service:
  server:
    host: "127.0.0.1"  # 监听地址
    port: 8005          # 监听端口

agent:
  role:
    name: "小诺"
    family_role: "爸爸最贴心的小女儿"

logging:
  level: "INFO"         # 日志级别
  format: "json"        # 日志格式

monitoring:
  metrics:
    enabled: true
    port: 9095          # Prometheus指标端口
```

### 环境变量

**位置**: `/etc/xiaonuo/xiaonuo.conf`

**必填项**:
- `XIAONUO_API_KEY`: API密钥
- `XIAONUO_JWT_SECRET`: JWT密钥
- `XIAONUO_DB_PASSWORD`: 数据库密码
- `XIAONUO_REDIS_PASSWORD`: Redis密码

---

## 服务管理

### systemd命令

```bash
# 启动服务
sudo systemctl start xiaonuo

# 停止服务
sudo systemctl stop xiaonuo

# 重启服务
sudo systemctl restart xiaonuo

# 查看状态
sudo systemctl status xiaonuo

# 重新加载配置
sudo systemctl reload xiaonuo
```

### 启动脚本

```bash
# 启动
/opt/xiaonuo/deploy/start_xiaonuo_production.sh start

# 停止
/opt/xiaonuo/deploy/start_xiaonuo_production.sh stop

# 重启
/opt/xiaonuo/deploy/start_xiaonuo_production.sh restart

# 状态
/opt/xiaonuo/deploy/start_xiaonuo_production.sh status
```

---

## 健康检查

### 健康检查端点

| 端点 | 说明 | 用途 |
|------|------|------|
| `/health` | 基础健康检查 | 监控系统 |
| `/health/ready` | 就绪检查 | Kubernetes |
| `/health/live` | 存活检查 | Kubernetes |
| `/health/detailed` | 详细健康检查 | 详细诊断 |

### 使用curl检查

```bash
# 基础健康检查
curl http://localhost:8005/health

# 就绪检查
curl http://localhost:8005/health/ready

# 存活检查
curl http://localhost:8005/health/live

# 详细健康检查
curl http://localhost:8005/health/detailed
```

### 健康检查响应示例

```json
{
  "status": "healthy",
  "timestamp": "2026-02-09T12:00:00Z",
  "version": "1.0.0",
  "uptime": 3600.0,
  "components": {
    "memory": {
      "healthy": true,
      "error": null
    },
    "collaboration": {
      "healthy": true,
      "error": null
    }
  }
}
```

---

## 日志管理

### 日志文件位置

| 日志类型 | 位置 | 说明 |
|---------|------|------|
| 主日志 | `/var/log/xiaonuo/xiaonuo.log` | 所有日志 |
| 错误日志 | `/var/log/xiaonuo/xiaonuo-error.log` | 仅错误 |
| 任务日志 | `/var/log/xiaonuo/xiaonuo-tasks.log` | 任务相关 |
| 协作日志 | `/var/log/xiaonuo/xiaonuo-collaboration.log` | 智能体协作 |

### 日志查看

```bash
# 实时查看主日志
tail -f /var/log/xiaonuo/xiaonuo.log

# 查看错误日志
tail -f /var/log/xiaonuo/xiaonuo-error.log

# 搜索特定关键词
grep "ERROR" /var/log/xiaonuo/xiaonuo.log

# 使用journalctl
sudo journalctl -u xiaonuo -f
```

### 日志轮转

日志会自动轮转，配置如下：
- 单个文件最大100MB
- 保留10个备份文件
- 每天轮转一次

---

## 备份恢复

### 备份内容

- 记忆数据
- 配置文件
- 状态数据

### 自动备份

备份每天自动执行，保留30天。

备份位置: `/var/backups/xiaonuo/`

### 手动备份

```bash
# 创建备份
/opt/xiaonuo/scripts/backup.sh

# 备份文件格式
# xiaonuo_backup_YYYYMMDD_HHMMSS.tar.gz
```

### 恢复备份

```bash
# 停止服务
sudo systemctl stop xiaonuo

# 恢复备份
tar -xzf /var/backups/xiaonuo/xiaonuo_backup_YYYYMMDD_HHMMSS.tar.gz -C /

# 启动服务
sudo systemctl start xiaonuo
```

---

## 故障排查

### 常见问题

#### 1. 服务启动失败

**症状**: `systemctl start xiaonuo` 失败

**排查步骤**:
```bash
# 查看详细状态
sudo systemctl status xiaonuo

# 查看日志
sudo journalctl -u xiaonuo -n 50

# 检查配置文件
sudo /opt/xiaonuo/deploy/start_xiaonuo_production.sh status
```

#### 2. 端口被占用

**症状**: `Address already in use`

**解决方案**:
```bash
# 查找占用端口的进程
sudo lsof -i :8005

# 杀死进程
sudo kill -9 <PID>

# 或修改配置文件中的端口
```

#### 3. 权限问题

**症状**: `Permission denied`

**解决方案**:
```bash
# 修复权限
sudo chown -R xiaonuo:xiaonuo /opt/xiaonuo
sudo chown -R xiaonuo:xiaonuo /var/log/xiaonuo
sudo chown -R xiaonuo:xiaonuo /var/lib/xiaonuo
sudo chown -R xiaonuo:xiaonuo /var/run/xiaonuo
```

#### 4. 数据库连接失败

**症状**: `Connection refused`

**解决方案**:
```bash
# 检查PostgreSQL状态
sudo systemctl status postgresql

# 检查连接
sudo -u postgres psql -U xiaonuo -d xiaonuo -c "SELECT 1;"

# 检查配置
cat /etc/xiaonuo/xiaonuo.conf | grep DB
```

---

## 性能优化

### 调整工作进程数

根据CPU核心数调整workers配置：

```yaml
# config/production/xiaonuo_production.yaml
service:
  server:
    workers: 4  # 设置为CPU核心数
```

### 调整内存限制

根据可用内存调整：

```ini
# /etc/systemd/system/xiaonuo.service
[Service]
MemoryMax=1G
```

### 启用缓存

确保Redis已启用：

```bash
sudo systemctl enable redis
sudo systemctl start redis
```

---

## 安全加固

### 1. 限制网络访问

默认绑定127.0.0.1，只允许本地访问。

如需远程访问，建议使用SSH隧道：

```bash
ssh -L 8005:localhost:8005 user@server
```

### 2. 使用强密码

所有密钥和密码使用以下方式生成：

```bash
# 生成随机密钥
openssl rand -hex 32
```

### 3. 定期更新

```bash
# 更新系统包
sudo apt update && sudo apt upgrade

# 更新应用代码
cd /opt/xiaonuo
git pull
```

---

## 监控告警

### Prometheus集成

指标端点: `http://localhost:9095/metrics`

### 关键指标

- `xiaonuo_uptime`: 运行时间
- `xiaonuo_requests_total`: 请求总数
- `xiaonuo_errors_total`: 错误总数
- `xiaonuo_memory_usage`: 内存使用
- `xiaonuo_cpu_usage`: CPU使用

### Grafana仪表板

导入配置: `config/grafana/xiaonuo_dashboard.json`

---

## 参考资源

- [项目主页](https://github.com/athena-platform)
- [API文档](http://localhost:8005/docs)
- [配置参考](../config/production/xiaonuo_production.yaml)

---

**文档版本**: v1.0.0
**最后更新**: 2026-02-09
**维护者**: Athena团队
