# Gateway日志轮转配置

## 概述

Gateway已配置自动日志轮转，防止日志文件无限增长占用磁盘空间。

## 配置参数

| 参数 | 值 | 说明 |
|------|-----|------|
| 单文件大小限制 | 100MB | 超过此大小自动轮转 |
| 保留天数 | 30天 | 超过30天的归档自动删除 |
| 最大归档数 | 10个 | 超过10个归档自动删除旧文件 |
| 运行频率 | 每天 | 凌晨2点自动运行 |
| 压缩格式 | gzip | 归档文件自动压缩 |

## 快速开始

### 安装日志轮转服务

```bash
cd /Users/xujian/Athena工作平台/gateway-unified
./scripts/setup_logrotate.sh install
```

### 手动运行日志轮转

```bash
./scripts/setup_logrotate.sh run
```

### 查看日志轮转状态

```bash
./scripts/setup_logrotate.sh status
```

## 日志文件位置

```
gateway-unified/logs/
├── gateway-stdout.log          # 当前标准输出
├── gateway-stdout.log.1        # 最新归档（未压缩）
├── gateway-stdout.log.2.gz     # 第2个归档（已压缩）
├── gateway-stdout.log.3.gz
├── ...
├── gateway-error.log           # 当前错误日志
├── gateway-error.log.1
├── gateway-error.log.2.gz
├── ...
├── logrotate.log               # 日志轮转执行日志
└── logrotate-error.log         # 日志轮转错误日志
```

## 配置调整

如需修改轮转参数，编辑 `scripts/log_rotate.sh`：

```bash
# 编辑配置
vim scripts/log_rotate.sh

# 修改参数
MAX_SIZE=100M      # 单文件最大大小
MAX_AGE=30         # 保留天数
MAX_FILES=10       # 最大归档数

# 重新安装服务
./scripts/setup_logrotate.sh uninstall
./scripts/setup_logrotate.sh install
```

## 手动管理

### 查看日志文件大小

```bash
du -sh gateway-unified/logs/*
```

### 查看归档文件

```bash
ls -lh gateway-unified/logs/*.gz
```

### 清理所有日志

⚠️ **危险操作**，会删除所有日志：

```bash
rm -f gateway-unified/logs/*.log*
```

### 查看特定日志

```bash
# 查看错误日志
tail -f gateway-unified/logs/gateway-error.log

# 查看标准输出
tail -f gateway-unified/logs/gateway-stdout.log

# 查看日志轮转日志
cat gateway-unified/logs/logrotate.log
```

## 故障排查

### 日志轮转未运行

```bash
# 1. 检查服务是否加载
launchctl list | grep logrotate

# 2. 查看日志轮转日志
cat gateway-unified/logs/logrotate-error.log

# 3. 手动运行测试
./scripts/setup_logrotate.sh run
```

### 归档文件过多

```bash
# 手动清理旧归档
find gateway-unified/logs -name "*.gz" -mtime +30 -delete

# 或保留最新10个
ls -t gateway-unified/logs/*.gz | tail -n +11 | xargs rm -f
```

### 磁盘空间不足

```bash
# 1. 检查日志目录大小
du -sh gateway-unified/logs

# 2. 立即运行日志轮转
./scripts/setup_logrotate.sh run

# 3. 清理所有gz归档（保留最近7天）
find gateway-unified/logs -name "*.gz" -mtime +7 -delete
```

## 卸载

```bash
./scripts/setup_logrotate.sh uninstall
```

## 注意事项

⚠️ **重要**：
- 日志轮转在凌晨2点运行，确保系统在这段时间运行
- 轮转时会短暂重启Gateway（通常<1秒）
- 压缩归档可以节省90%以上空间
- 建议定期检查日志目录大小

## 监控建议

可以创建一个简单的监控脚本，当日志目录超过1GB时发送告警：

```bash
#!/bin/bash
LOG_SIZE=$(du -sm gateway-unified/logs | cut -f1)
if [ $LOG_SIZE -gt 1024 ]; then
    echo "警告：日志目录大小超过1GB (${LOG_SIZE}MB)"
fi
```

---

**维护者**: 徐健 (xujian519@gmail.com)
**最后更新**: 2026-04-20
