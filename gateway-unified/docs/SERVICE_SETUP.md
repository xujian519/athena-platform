# Gateway系统服务配置指南

## 概述

Gateway已配置为macOS launchd服务，实现开机自动启动和崩溃自动恢复。

## 快速开始

### 首次安装服务

```bash
cd /Users/xujian/Athena工作平台/gateway-unified
./scripts/service.sh install
```

安装后服务会：
- ✅ 立即启动
- ✅ 开机自动启动
- ✅ 崩溃自动恢复
- ✅ 配置文件变更自动重启

### 常用命令

```bash
# 查看服务状态
./scripts/service.sh status

# 启动服务
./scripts/service.sh start

# 停止服务
./scripts/service.sh stop

# 重启服务
./scripts/service.sh restart

# 查看实时日志
./scripts/service.sh logs

# 卸载服务
./scripts/service.sh uninstall
```

## 服务特性

### 自动启动
- 系统启动后自动运行
- 等待网络可用后启动

### 自动恢复
- 进程崩溃后自动重启（10秒延迟）
- 配置文件修改后自动重载

### 日志管理
- 标准输出：`logs/gateway-stdout.log`
- 错误输出：`logs/gateway-error.log`

### 监控
- 端口8005健康检查
- 进程状态监控

## 故障排查

### 服务未启动

```bash
# 1. 检查服务状态
./scripts/service.sh status

# 2. 查看错误日志
cat logs/gateway-error.log

# 3. 手动启动（前台模式）
./bin/gateway-unified -config config.yaml
```

### 端口被占用

```bash
# 查找占用进程
lsof -i :8005

# 杀死进程
kill -9 <PID>

# 重启服务
./scripts/service.sh restart
```

### 配置文件错误

```bash
# 验证配置文件
cat config.yaml

# 测试配置
./bin/gateway-unified -config config.yaml -test
```

## 卸载

如需完全卸载服务：

```bash
./scripts/service.sh uninstall
```

## 文件位置

| 文件 | 位置 |
|------|------|
| 服务配置 | `com.athena.gateway.plist` |
| 管理脚本 | `scripts/service.sh` |
| 二进制文件 | `bin/gateway-unified` |
| 配置文件 | `config.yaml` |
| 日志文件 | `logs/gateway-*.log` |

## 注意事项

⚠️ **重要**：
- 修改`config.yaml`后会自动重启服务
- 建议定期检查日志文件大小
- 生产环境建议配置日志轮转

## Linux支持

如果需要在Linux上部署，请使用`scripts/systemd/gateway.service`（待创建）。

---

**维护者**: 徐健 (xujian519@gmail.com)
**最后更新**: 2026-04-20
