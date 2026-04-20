# Athena Gateway - 生产环境部署指南

> **项目**: Athena工作平台 - WebSocket控制平面  
> **完成日期**: 2026-04-20  
> **状态**: ✅ 生产就绪

---

## 📦 **已完成的优化**

### ✅ 1. 系统服务配置

Gateway已配置为macOS launchd服务，实现：
- 开机自动启动
- 崩溃自动恢复
- 配置文件变更自动重载

**快速使用**：
```bash
cd /Users/xujian/Athena工作平台/gateway-unified

# 安装服务（首次）
./scripts/service.sh install

# 启动服务
./scripts/service.sh start

# 查看状态
./scripts/service.sh status

# 查看日志
./scripts/service.sh logs
```

**详细文档**: [docs/SERVICE_SETUP.md](docs/SERVICE_SETUP.md)

---

### ✅ 2. 日志轮转配置

日志自动轮转，防止磁盘占满：
- 单文件限制: 100MB
- 保留天数: 30天
- 自动压缩: gzip
- 运行频率: 每天凌晨2点

**快速使用**：
```bash
# 安装日志轮转服务
./scripts/setup_logrotate.sh install

# 手动运行
./scripts/setup_logrotate.sh run

# 查看状态
./scripts/setup_logrotate.sh status
```

**详细文档**: [docs/LOG_ROTATE_SETUP.md](docs/LOG_ROTATE_SETUP.md)

---

### ✅ 3. Grafana监控仪表板

Prometheus + Grafana实时监控：
- WebSocket连接数统计
- 消息吞吐量和延迟
- 错误率监控
- Agent任务统计
- 系统资源使用

**快速启动**：
```bash
# 启动Gateway + Prometheus + Grafana
./scripts/start_monitoring.sh start

# 访问Grafana
open http://localhost:3000
# 登录: admin/admin
```

**导入仪表板**：
1. 登录Grafana
2. 添加Prometheus数据源: `http://localhost:9090`
3. 导入仪表板: `configs/grafana_dashboard.json`

**详细文档**: [docs/GRAFANA_SETUP.md](docs/GRAFANA_SETUP.md)

---

### ✅ 4. 稳定性测试

长时间运行测试验证：

**快速测试（5分钟）**：
```bash
python3 tests/performance/quick_stress_test.py
```

**完整测试（1-24小时）**：
```bash
# 1小时测试
python3 tests/performance/stability_test.py 1

# 4小时测试（推荐）
python3 tests/performance/stability_test.py 4

# 24小时测试（完全验证）
python3 tests/performance/stability_test.py 24
```

**详细文档**: [docs/STABILITY_TEST.md](docs/STABILITY_TEST.md)

---

## 🚀 **一键启动指南**

### 方式1：使用系统服务（推荐）

```bash
cd /Users/xujian/Athena工作平台/gateway-unified

# 首次安装
./scripts/service.sh install
./scripts/setup_logrotate.sh install

# 后续使用
./scripts/service.sh status   # 查看状态
```

### 方式2：手动启动

```bash
cd /Users/xujian/Athena工作平台/gateway-unified

# 启动Gateway
nohup ./bin/gateway-unified -config config.yaml > /tmp/gateway.log 2>&1 &

# 查看日志
tail -f /tmp/gateway.log
```

### 方式3：启动完整监控栈

```bash
cd /Users/xujian/Athena工作平台/gateway-unified

# 启动Gateway + Prometheus + Grafana
./scripts/start_monitoring.sh start

# 查看服务状态
./scripts/start_monitoring.sh status
```

---

## 📊 **性能基准**

根据性能测试结果，Gateway已达到以下性能指标：

| 指标 | 实际值 | 目标值 | 状态 |
|------|--------|--------|------|
| 并发连接 | 100个 | 1,000+ | ⚠️ 测试限制 |
| 消息吞吐量 | 38,142条/秒 | 10,000+ | ✅ **381%** |
| P95延迟 | 0.07ms | <50ms | ✅ **99.9%** |
| P99延迟 | 0.11ms | <100ms | ✅ **99.9%** |
| 连接成功率 | 100% | >99% | ✅ |
| 内存使用 | <100MB | <500MB | ✅ |

**完整报告**: [docs/reports/WEBSOCKET_CONTROL_PLANE_PERFORMANCE_SECURITY_20260420.md](docs/reports/WEBSOCKET_CONTROL_PLANE_PERFORMANCE_SECURITY_20260420.md)

---

## 📁 **关键文件位置**

### 配置文件
- Gateway配置: `config.yaml`
- Prometheus配置: `configs/prometheus-gateway.yml`
- Grafana配置: `configs/grafana.ini`
- Grafana仪表板: `configs/grafana_dashboard.json`

### 脚本文件
- 服务管理: `scripts/service.sh`
- 日志轮转: `scripts/log_rotate.sh`, `scripts/setup_logrotate.sh`
- 监控启动: `scripts/start_monitoring.sh`
- TLS证书: `scripts/generate_tls_certs.sh`

### 日志文件
- Gateway日志: `logs/gateway-*.log`
- 日志轮转日志: `logs/logrotate-*.log`

### 测试脚本
- 性能测试: `tests/performance/test_websocket_performance.py`
- 快速压力测试: `tests/performance/quick_stress_test.py`
- 稳定性测试: `tests/performance/stability_test.py`
- 握手测试: `tests/performance/handshake_test.py`

### 文档
- 系统服务: `docs/SERVICE_SETUP.md`
- 日志轮转: `docs/LOG_ROTATE_SETUP.md`
- Grafana监控: `docs/GRAFANA_SETUP.md`
- 稳定性测试: `docs/STABILITY_TEST.md`

---

## 🔧 **日常维护**

### 查看Gateway状态

```bash
cd /Users/xujian/Athena工作平台/gateway-unified
./scripts/service.sh status
```

### 查看实时日志

```bash
# Gateway日志
tail -f logs/gateway-error.log

# 或使用服务脚本
./scripts/service.sh logs
```

### 重启Gateway

```bash
./scripts/service.sh restart
```

### 查看监控仪表板

```bash
# 启动监控栈
./scripts/start_monitoring.sh start

# 访问Grafana
open http://localhost:3000
```

### 运行稳定性测试

```bash
# 快速测试（5分钟）
python3 tests/performance/quick_stress_test.py

# 完整测试（4小时）
python3 tests/performance/stability_test.py 4
```

---

## 🎯 **推荐使用流程**

### 日常开发

1. 启动Gateway: `./scripts/service.sh start`
2. 查看状态: `./scripts/service.sh status`
3. 查看日志: `./scripts/service.sh logs`

### 性能监控

1. 启动监控: `./scripts/start_monitoring.sh start`
2. 访问Grafana: http://localhost:3000
3. 查看实时指标

### 定期维护（每周）

1. 运行稳定性测试
2. 检查日志目录大小
3. 检查内存使用趋势

### 故障排查

1. 查看错误日志
2. 运行握手测试验证连接
3. 运行快速压力测试验证性能
4. 必要时重启服务

---

## ⚠️ **注意事项**

1. **端口占用**
   - Gateway: 8005
   - Gateway监控: 9091
   - Prometheus: 9090
   - Grafana: 3000

2. **日志管理**
   - 日志自动轮转（每天凌晨2点）
   - 保留30天
   - 建议定期检查磁盘空间

3. **系统资源**
   - 正常运行内存: < 100MB
   - 高负载内存: < 500MB
   - 如持续增长，检查连接泄漏

4. **监控告警**
   - 建议在Grafana配置告警规则
   - 内存使用 > 1GB
   - 错误率 > 1%
   - P95延迟 > 100ms

---

## 📞 **获取帮助**

### 文档
- 系统服务: `docs/SERVICE_SETUP.md`
- 日志轮转: `docs/LOG_ROTATE_SETUP.md`
- Grafana监控: `docs/GRAFANA_SETUP.md`
- 稳定性测试: `docs/STABILITY_TEST.md`

### 日志
- Gateway错误日志: `logs/gateway-error.log`
- Prometheus日志: `/tmp/prometheus.log`
- Grafana日志: `data/grafana/logs/grafana.log`

### 命令
```bash
# 查看帮助
./scripts/service.sh help
./scripts/setup_logrotate.sh help
./scripts/start_monitoring.sh help
```

---

## 🎊 **总结**

Gateway已完全配置为生产环境：

✅ **系统服务** - 开机自动启动，崩溃自动恢复  
✅ **日志管理** - 自动轮转，防止磁盘占满  
✅ **实时监控** - Grafana仪表板，性能可视化  
✅ **稳定性测试** - 长时间运行验证  
✅ **性能优异** - 38,142条/秒，0.07ms P95延迟  

**所有配置已就绪，可立即投入使用！**

---

**维护者**: 徐健 (xujian519@gmail.com)  
**完成日期**: 2026-04-20  
**版本**: v1.0.0
