# Gateway稳定性测试指南

## 概述

Gateway稳定性测试用于验证长时间运行下的性能和可靠性。

## 测试类型

### 1. 快速压力测试（5分钟）

快速验证Gateway的基本稳定性。

**运行**：
```bash
cd /Users/xujian/Athena工作平台
python3 tests/performance/quick_stress_test.py
```

**测试内容**：
- 5分钟持续测试
- 每5秒创建10个并发连接
- 每个连接发送5条消息
- 实时统计连接数、消息数、错误数

**预期结果**：
- 错误数 < 10
- 错误率 < 0.1%
- 连接成功率 > 99%

### 2. 长时间稳定性测试（1小时+）

验证Gateway在长时间运行下的稳定性。

**运行**：
```bash
cd /Users/xujian/Athena工作平台
python3 tests/performance/stability_test.py 1  # 1小时
python3 tests/performance/stability_test.py 4  # 4小时
python3 tests/performance/stability_test.py 24 # 24小时
```

**测试内容**：
- 持续创建和关闭连接
- 监控内存使用变化
- 统计错误发生频率
- 每5分钟生成报告

**预期结果**：
- 内存增长 < 1MB/小时
- 错误率 < 1 错误/小时
- 无崩溃或死锁

## 测试指标

### 内存稳定性

| 评级 | 内存增长率 |
|------|-----------|
| ✅ 优秀 | < 1MB/小时 |
| ⚠️ 良好 | 1-5MB/小时 |
| ❌ 需优化 | > 5MB/小时 |

### 错误率

| 评级 | 错误率 |
|------|--------|
| ✅ 优秀 | < 1 错误/小时 |
| ⚠️ 良好 | 1-10 错误/小时 |
| ❌ 需优化 | > 10 错误/小时 |

## 运行测试前准备

### 1. 启动Gateway

```bash
cd /Users/xujian/Athena工作平台/gateway-unified
./scripts/service.sh start
```

### 2. 验证Gateway运行

```bash
./scripts/service.sh status
```

### 3. 检查端口

```bash
lsof -i :8005  # Gateway
```

## 运行测试

### 快速测试（推荐首次运行）

```bash
python3 tests/performance/quick_stress_test.py
```

### 完整稳定性测试

```bash
# 1小时测试
python3 tests/performance/stability_test.py 1

# 4小时测试（建议）
python3 tests/performance/stability_test.py 4

# 24小时测试（完全验证）
python3 tests/performance/stability_test.py 24
```

## 监控测试进度

测试会每5分钟输出一次报告：

```
================================================================================
📊 稳定性测试报告 - 2026-04-20 18:30:00
================================================================================
测试时长: 0.50 小时
样本数: 6

内存使用:
  初始: 45.23 MB
  当前: 46.01 MB
  增长: 0.78 MB (1.56 MB/小时)
  范围: 45.00 - 46.50 MB

错误统计:
  总数: 2
  速率: 4.00 错误/小时

响应时间:
  平均: 0.05 ms
  范围: 0.03 - 0.11 ms
================================================================================
```

## 中断测试

按 `Ctrl+C` 可随时中断测试，中断时会显示当前统计。

## 结果分析

### 优秀结果示例

```
✅ 内存稳定性: 优秀 (增长 < 1MB/小时)
✅ 错误率: 优秀 (< 1 错误/小时)
```

### 需要优化示例

```
❌ 内存稳定性: 需要优化 (增长 ≥ 5MB/小时)
❌ 错误率: 需要优化 (≥ 10 错误/小时)
```

## 故障排查

### Gateway崩溃

1. 查看Gateway日志：
```bash
tail -100 gateway-unified/logs/gateway-error.log
```

2. 检查内存使用：
```bash
ps aux | grep gateway-unified
```

3. 重启Gateway：
```bash
./scripts/service.sh restart
```

### 测试客户端连接失败

1. 检查Gateway是否运行：
```bash
lsof -i :8005
```

2. 测试WebSocket连接：
```bash
python3 tests/performance/handshake_test.py
```

### 内存持续增长

1. 使用Grafana监控：
```bash
./scripts/start_monitoring.sh start
# 访问 http://localhost:3000
```

2. 检查连接泄漏：
```bash
curl http://localhost:8005/api/websocket/stats
```

3. 重启Gateway清理泄漏：
```bash
./scripts/service.sh restart
```

## 自动化测试

### 创建定时任务

```bash
# 编辑crontab
crontab -e

# 每天凌晨3点运行1小时测试
0 3 * * * cd /Users/xujian/Athena工作平台 && python3 tests/performance/stability_test.py 1 >> logs/stability_test.log 2>&1

# 每周日凌晨2点运行4小时测试
0 2 * * 0 cd /Users/xujian/Athena工作平台 && python3 tests/performance/stability_test.py 4 >> logs/stability_test.log 2>&1
```

### 测试结果保存

```bash
# 保存测试输出
python3 tests/performance/stability_test.py 1 | tee logs/stability_test_$(date +%Y%m%d_%H%M%S).log
```

## 性能基准

根据性能测试结果，Gateway的性能基准：

| 指标 | 基准值 |
|------|--------|
| 并发连接 | 100+ |
| 吞吐量 | 38,000+ 条/秒 |
| P95延迟 | < 0.1ms |
| 内存使用 | < 100MB |
| 错误率 | < 0.01% |

稳定性测试应确保：
- 长时间运行后性能不低于基准值的80%
- 内存增长控制在合理范围
- 无崩溃或死锁

## 下一步

稳定性测试通过后，可以：

1. **生产部署** - 配置为系统服务自动启动
2. **监控告警** - 配置Grafana仪表板实时监控
3. **日志管理** - 配置日志轮转自动清理
4. **性能优化** - 根据测试结果优化性能瓶颈

## 注意事项

⚠️ **重要**：
- 测试期间Gateway会承受持续负载
- 建议在非生产环境运行测试
- 长时间测试会占用系统资源
- 定期检查磁盘空间（日志和数据）

## 扩展阅读

- [性能测试报告](docs/reports/WEBSOCKET_CONTROL_PLANE_PERFORMANCE_SECURITY_20260420.md)
- [系统服务配置](docs/SERVICE_SETUP.md)
- [Grafana监控配置](docs/GRAFANA_SETUP.md)

---

**维护者**: 徐健 (xujian519@gmail.com)
**最后更新**: 2026-04-20
