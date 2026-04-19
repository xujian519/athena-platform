# Athena Gateway 部署快速参考

## 🚀 一键部署命令

### macOS
```bash
cd /Users/xujian/Athena工作平台/gateway-unified
sudo bash quick-deploy-macos.sh
```

### Linux
```bash
cd /path/to/gateway-unified
sudo bash quick-deploy.sh
```

---

## 📁 安装位置对照

| 项目 | macOS | Linux |
|------|-------|-------|
| 安装目录 | `/usr/local/athena-gateway` | `/opt/athena-gateway` |
| 服务用户 | `_athena` | `athena` |
| 服务配置 | `/Library/LaunchDaemons/com.athena.gateway.plist` | `/etc/systemd/system/athena-gateway.service` |
| 日志轮转配置 | `/etc/newsyslog.d/athena-gateway.conf` | `/etc/logrotate.d/athena-gateway` |

---

## 🔧 服务管理命令

### macOS (launchd)
```bash
# 启动
sudo launchctl load -w /Library/LaunchDaemons/com.athena.gateway.plist

# 停止
sudo launchctl unload -w /Library/LaunchDaemons/com.athena.gateway.plist

# 重启
sudo launchctl kickstart -k gui/$(id -u)/com.athena.gateway

# 状态
launchctl list | grep com.athena.gateway
```

### Linux (systemd)
```bash
# 启动
systemctl start athena-gateway

# 停止
systemctl stop athena-gateway

# 重启
systemctl restart athena-gateway

# 状态
systemctl status athena-gateway

# 日志
journalctl -u athena-gateway -f
```

---

## 🔐 部署后必做

1. **修改认证密钥**
   - macOS: `sudo vi /usr/local/athena-gateway/config/auth.yaml`
   - Linux: `sudo vi /opt/athena-gateway/config/auth.yaml`

2. **验证健康检查**
   ```bash
   curl http://localhost:8005/health
   ```

3. **配置防火墙**（如需要）

4. **配置TLS**（生产环境推荐）

---

## 🐛 故障排查

| 问题 | 检查命令 |
|------|---------|
| 服务未启动 | `launchctl list \| grep gateway` 或 `systemctl status athena-gateway` |
| 端口被占用 | `lsof -i :8005` |
| 日志查看 | macOS: `tail -f /usr/local/athena-gateway/logs/gateway.log`<br>Linux: `journalctl -u athena-gateway -f` |
| 权限错误 | 重新运行部署脚本 |

---

## 📋 安全检查

### macOS
```bash
sudo bash security-check-macos.sh
```

### Linux
```bash
sudo bash security-check.sh
```

---

## 🗑️ 卸载

### macOS
```bash
sudo bash uninstall-macos.sh
```

### Linux
```bash
sudo bash uninstall.sh
```

---

## 📚 完整文档

- [README.md](README.md) - 项目主文档
- [CHANGELOG.md](CHANGELOG.md) - 开发日志
- [DEPLOYMENT_MACOS.md](DEPLOYMENT_MACOS.md) - macOS部署详细指南
- [DEPLOYMENT.md](DEPLOYMENT.md) - Linux部署详细指南
- [DEPLOYMENT_COMPLETE.md](DEPLOYMENT_COMPLETE.md) - 完整部署指南

---

**版本**: v1.0.0-macos
**更新时间**: 2025-02-21
