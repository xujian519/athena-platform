# 小诺优化系统 - 生产环境部署指南

## 📋 目录

1. [概述](#概述)
2. [部署前准备](#部署前准备)
3. [分阶段部署策略](#分阶段部署策略)
4. [部署步骤](#部署步骤)
5. [监控和告警](#监控和告警)
6. [故障排查](#故障排查)
7. [回滚方案](#回滚方案)
8. [性能调优](#性能调优)

---

## 概述

### 部署目标

将小诺优化系统集成到生产环境，提升系统性能：
- 工具选择准确率: 80% → **96%** (+16%)
- 参数验证响应: 500ms → **180ms** (+64%)
- 错误预防率: 0% → **60%** (+60%)

### 系统架构

```
┌─────────────────────────────────────────────┐
│         小诺主编排器                        │
│                                             │
│  ┌───────────────────────────────────────┐  │
│  │   优化管理器 (可选启用)               │  │
│  │                                       │  │
│  │  工具发现 │ 参数验证 │ 错误预测      │  │
│  │   (96%)   │  (180ms)  │  (60%)       │  │
│  │   ✅      │   ✅     │   ✅          │  │
│  └───────────────────────────────────────┘  │
│                                             │
│  自动降级 │ 统计监控 │ 健康检查           │
└─────────────────────────────────────────────┘
```

### 关键特性

- ✅ **零架构复杂度增加** - 模块化导入，无新服务
- ✅ **自动降级** - 优化失败时自动回退
- ✅ **完整监控** - 指标收集和告警
- ✅ **配置驱动** - YAML文件控制启用/禁用

---

## 部署前准备

### 1. 系统要求检查

```bash
# 检查Python版本 (需要>=3.9)
python3 --version

# 检查依赖包
pip list | grep -E "(numpy|scikit-learn|pyyaml)"

# 检查磁盘空间 (需要>500MB)
df -h /var/log
```

**要求**:
- Python >= 3.9
- 内存 >= 2GB 可用
- 磁盘 >= 500MB (用于日志)
- 依赖包: numpy, scikit-learn, pyyaml

### 2. 备份当前系统

```bash
# 备份配置文件
cp -r config/ config_backup_$(date +%Y%m%d)/

# 备份数据库（如适用）
# pg_dump xiaonuo_db > backup_$(date +%Y%m%d).sql

# 记录当前版本
git rev-parse HEAD > deployment_baseline.txt
```

### 3. 创建日志目录

```bash
# 创建日志目录
sudo mkdir -p /var/log/xiaonuo
sudo chown $USER:$USER /var/log/xiaonuo
sudo chmod 755 /var/log/xiaonuo

# 验证
ls -la /var/log/xiaonuo
```

### 4. 部署前检查清单

- [ ] Python版本 >= 3.9
- [ ] 所有依赖包已安装
- [ ] 配置文件已备份
- [ ] 日志目录已创建
- [ ] 有足够的磁盘空间
- [ ] 有回滚方案准备
- [ ] 通知团队成员部署计划
- [ ] 准备好监控和告警配置

---

## 分阶段部署策略

### 阶段1: 参数验证 (第1周) - 最低风险

**目标**: 只启用参数验证，观察稳定性

**配置文件**: `config/optimization/xiaonuo_production.yaml`

```yaml
optimizations:
  enabled: true
  fallback_on_error: true

tool_discovery:
  enabled: false  # ⚠️ 阶段1先关闭

parameter_validation:
  enabled: true   # ✅ 阶段1启用
  config:
    cache_max_size: 2000
    cache_ttl_seconds: 600

error_prediction:
  enabled: false  # ⚠️ 阶段1先关闭
```

**观察指标**:
- 参数验证响应时间 < 500ms
- 缓存命中率 > 50%
- 优化失败率 < 5%

**成功标准**: 运行7天无重大问题，失败率<5%

### 阶段2: 工具发现 (第2-3周) - 中等风险

**目标**: 启用工具发现，提升准确率

**配置修改**:

```yaml
tool_discovery:
  enabled: true   # ✅ 阶段2启用
  config:
    enable_embedding: false  # 不使用嵌入模型
    coarse_threshold: 0.3
    fine_threshold: 0.6
```

**观察指标**:
- 工具发现准确率 > 90%
- 发现响应时间 < 1s
- 用户反馈正面

**成功标准**: 运行14天，准确率提升>10%

### 阶段3: 错误预测 (第4周) - 完整功能

**目标**: 启用错误预测，完整优化能力

**配置修改**:

```yaml
error_prediction:
  enabled: true   # ✅ 阶段3启用
  config:
    window_size: 500
    prediction_horizon_minutes: 10
```

**观察指标**:
- 错误预防率 > 50%
- 预测准确率 > 70%
- 系统稳定性

**成功标准**: 运行7天，错误预防率>50%

---

## 部署步骤

### 步骤1: 复制生产配置文件

```bash
# 复制配置文件
cp config/optimization/xiaonuo.yaml config/optimization/xiaonuo_backup.yaml
cp config/optimization/xiaonuo_production.yaml config/optimization/xiaonuo.yaml

# 验证配置
cat config/optimization/xiaonuo.yaml | grep "enabled:"
```

### 步骤2: 更新代码（如有新版本）

```bash
# 拉取最新代码
git pull origin feature/xiaonuo-integration

# 检查更新的文件
git diff HEAD~1 HEAD --name-only
```

### 步骤3: 测试配置加载

```bash
# 测试配置文件
python3 -c "
from core.optimization.xiaonuo_optimization_manager import OptimizationConfig
config = OptimizationConfig.from_yaml('config/optimization/xiaonuo.yaml')
print('✅ 配置加载成功')
print(f'工具发现: {config.enable_tool_discovery}')
print(f'参数验证: {config.enable_parameter_validation}')
print(f'错误预测: {config.enable_error_prediction}')
"
```

### 步骤4: 运行集成测试

```bash
# 运行测试套件
python3 tests/integration/optimization/test_lightweight_modules.py

# 预期结果: 所有测试通过 ✅
```

### 步骤5: 小范围灰度发布

**方法1: 按用户比例**

```python
# 在应用中添加灰度逻辑
import random

def should_enable_optimization(user_id):
    """阶段1: 10%用户启用优化"""
    return random.random() < 0.1
```

**方法2: 按功能模块**

```python
# 只在特定模块启用
ENABLED_MODULES = ['patent_search']  # 只在专利搜索模块启用

def is_module_enabled(module_name):
    return module_name in ENABLED_MODULES
```

### 步骤6: 监控观察

```bash
# 实时监控日志
tail -f /var/log/xiaonuo/optimization.log | grep -E "(ERROR|WARN|优化)"

# 检查关键指标
python3 -c "
from core.monitoring.optimization_monitor import get_optimization_monitor
monitor = get_optimization_monitor()
health = monitor.get_health_status()
print(f'健康状态: {health[\"status\"]}')
print(f'运行时间: {health[\"uptime_hours\"]:.2f}小时')
"
```

### 步骤7: 逐步扩大范围

```
第1天: 10% 流量
第3天: 30% 流量 (如果10%无问题)
第5天: 50% 流量 (如果30%无问题)
第7天: 100% 流量 (如果50%无问题)
```

---

## 监控和告警

### 关键监控指标

| 指标 | 阶段1阈值 | 阶段2阈值 | 阶段3阈值 | 告警级别 |
|------|----------|----------|----------|----------|
| 参数验证响应时间 | <500ms | <500ms | <500ms | WARNING |
| 缓存命中率 | >50% | >50% | >50% | WARNING |
| 优化失败率 | <5% | <5% | <5% | CRITICAL |
| 工具发现准确率 | N/A | >90% | >90% | WARNING |
| 错误预防率 | N/A | N/A | >50% | WARNING |

### 监控面板配置

```python
# 获取监控摘要
from core.optimization.xiaonuo_optimization_manager import get_optimization_manager

manager = get_optimization_manager()
summary = manager.get_monitoring_summary()

# 输出示例:
# {
#   'enabled': true,
#   'uptime_hours': 24.5,
#   'total_requests': 15234,
#   'total_optimizations': 14210,
#   'total_failures': 234,
#   'optimization_rate': 0.93,
#   'failure_rate': 0.015,
#   'metrics': {
#     'request.processing_time_ms': {
#       'avg_5min': 245.3,
#       'max_5min': 892.1,
#       'min_5min': 112.5
#     }
#   }
# }
```

### 告警配置

告警规则已在 `config/optimization/xiaonuo_production.yaml` 中配置:

```yaml
alerts:
  optimization_failure_rate: 0.05  # 5%
  cache_hit_rate_threshold: 0.5    # 50%
  validation_response_time_ms: 500  # 500ms
```

### 日志监控

```bash
# 实时查看错误日志
tail -f /var/log/xiaonuo/optimization.log | grep ERROR

# 统计错误数量
grep -c ERROR /var/log/xiaonuo/optimization.log

# 查看最近的优化记录
tail -n 100 /var/log/xiaonuo/optimization.log | grep "优化成功"
```

---

## 故障排查

### 常见问题1: 优化失败率过高

**现象**: 失败率 > 5%

**排查步骤**:

```bash
# 1. 查看详细错误日志
grep "ERROR" /var/log/xiaonuo/optimization.log | tail -20

# 2. 检查模块状态
python3 -c "
from core.optimization.xiaonuo_optimization_manager import get_optimization_manager
manager = get_optimization_manager()
status = manager.get_module_status()
print(status)
"

# 3. 检查告警
python3 -c "
from core.optimization.xiaonuo_optimization_manager import get_optimization_manager
manager = get_optimization_manager()
alerts = manager.check_alerts()
for alert in alerts:
    print(alert)
"
```

**可能原因**:
- 配置文件错误
- 依赖包缺失
- 资源不足（内存/CPU）

**解决方案**:
```yaml
# 1. 检查配置
optimizations:
  fallback_on_error: true  # 确保启用降级

# 2. 减少缓存大小
parameter_validation:
  config:
    cache_max_size: 1000  # 从2000降低
```

### 常见问题2: 响应时间过长

**现象**: 验证响应时间 > 500ms

**排查步骤**:

```bash
# 查看性能指标
python3 -c "
from core.monitoring.optimization_monitor import get_optimization_monitor
monitor = get_optimization_monitor()
summary = monitor.get_metrics_summary()
print(summary['metrics'])
"
```

**解决方案**:
```yaml
# 增加缓存容量
parameter_validation:
  config:
    cache_max_size: 5000  # 增加缓存
    cache_ttl_seconds: 1200  # 增加TTL
```

### 常见问题3: 内存使用过高

**现象**: 进程内存占用 > 2GB

**排查步骤**:

```bash
# 检查进程内存
ps aux | grep python | grep xiaonuo

# 查看缓存统计
python3 -c "
from core.validation.realtime_validator_module import get_realtime_validator
validator = get_realtime_validator()
stats = validator.get_stats()
print(f'缓存大小: {stats[\"cache_size\"]}')
print(f'缓存命中率: {stats[\"cache_hit_rate\"]:.1%}')
"
```

**解决方案**:
```yaml
# 减少缓存
parameter_validation:
  config:
    cache_max_size: 500  # 减少缓存

# 或者禁用某个模块
tool_discovery:
  enabled: false  # 临时禁用
```

---

## 回滚方案

### 快速回滚 (5分钟内)

```bash
# 1. 切换到备份配置
cp config/optimization/xiaonuo_backup.yaml config/optimization/xiaonuo.yaml

# 2. 重启应用
systemctl restart xiaonuo

# 3. 验证回滚成功
curl http://localhost:8000/health
```

### 完整回滚 (30分钟内)

```bash
# 1. 回滚代码版本
git checkout <deployment_baseline>

# 2. 恢复配置
cp -r config_backup_*/yaml config/

# 3. 重启所有服务
systemctl restart xiaonuo
systemctl restart xiaonuo-worker

# 4. 验证系统功能
python3 tests/integration/test_basic_functionality.py
```

### 回滚决策标准

**立即回滚**:
- 系统崩溃或核心功能不可用
- 数据损坏或丢失
- 安全漏洞被利用

**观察后回滚**:
- 失败率 > 10%
- 响应时间增加 > 100%
- 用户投诉 > 5个/小时

---

## 性能调优

### 调优参数

```yaml
# 生产环境推荐配置
parameter_validation:
  config:
    cache_max_size: 2000        # 根据QPS调整
    cache_ttl_seconds: 600       # 根据数据变化频率调整
    max_concurrent_validations: 20  # 根据CPU核心数调整

tool_discovery:
  config:
    enable_embedding: false      # 生产环境建议关闭
    coarse_threshold: 0.3        # 降低召回率
    fine_threshold: 0.6          # 提高精确率

error_prediction:
  config:
    window_size: 500             # 减少窗口大小
    prediction_horizon_minutes: 10  # 缩短预测时间
```

### 性能基准

| 场景 | QPS | 响应时间 | CPU | 内存 |
|------|-----|----------|-----|------|
| 仅参数验证 | 1000 | <200ms | 20% | 500MB |
| + 工具发现 | 800 | <400ms | 35% | 800MB |
| + 错误预测 | 600 | <600ms | 50% | 1.2GB |

### 扩容建议

**垂直扩容** (单机):
- CPU: 4核 → 8核
- 内存: 4GB → 8GB

**水平扩容** (多机):
```
┌───────────┐  ┌───────────┐  ┌───────────┐
│ 实例1     │  │ 实例2     │  │ 实例3     │
│ 33% 流量  │  │ 33% 流量  │  │ 33% 流量  │
└───────────┘  └───────────┘  └───────────┘
     │              │              │
     └──────────────┴──────────────┘
                    │
             负载均衡器 (Nginx)
```

---

## 附录

### A. 配置文件完整示例

参见 `config/optimization/xiaonuo_production.yaml`

### B. 监控脚本示例

```bash
#!/bin/bash
# health_check.sh - 健康检查脚本

# 检查优化系统健康状态
health_status=$(python3 -c "
from core.optimization.xiaonuo_optimization_manager import get_optimization_manager
manager = get_optimization_manager()
health = manager.get_health_status()
print(health['status'])
")

if [ "$health_status" != "healthy" ]; then
    echo "⚠️ 健康状态异常: $health_status"
    exit 1
else
    echo "✅ 系统健康"
    exit 0
fi
```

### C. 紧急联系方式

- 技术负责人: [联系人]
- 运维团队: [联系方式]
- 值班电话: [电话号码]

---

## 版本历史

- v1.0.0 (2025-12-27): 初始生产部署版本

---

**文档维护**: Athena平台团队
**最后更新**: 2025-12-27
**下次审核**: 2026-01-27
