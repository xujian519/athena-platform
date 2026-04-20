# system_monitor工具使用指南

> **工具版本**: v1.0.0
> **最后更新**: 2026-04-20
> **作者**: Athena平台团队

---

## 📖 目录

1. [概述](#概述)
2. [快速开始](#快速开始)
3. [功能说明](#功能说明)
4. [API参考](#api参考)
5. [使用示例](#使用示例)
6. [最佳实践](#最佳实践)
7. [故障排查](#故障排查)
8. [FAQ](#faq)

---

## 概述

system_monitor工具是Athena平台的系统监控工具，提供CPU使用率、内存使用情况、磁盘使用情况的实时监控功能。

### 核心特性

- ✅ **无外部依赖**: 仅使用系统命令，无需安装额外库
- ✅ **跨平台支持**: 支持macOS和Linux
- ✅ **健康状态判断**: 自动判断系统健康状态
- ✅ **优雅降级**: 单个监控项失败不影响其他项
- ✅ **类型安全**: 完整的Python 3.11+类型注解

### 支持的监控指标

| 指标 | 说明 | 健康阈值 |
|-----|------|---------|
| CPU | CPU使用率 | 80% |
| 内存 | 内存使用率 | 80% |
| 磁盘 | 磁盘使用率 | 85% |

---

## 快速开始

### 安装

system_monitor工具已集成到Athena平台，无需额外安装。

### 基础用法

```python
from core.tools.system_monitor_wrapper import system_monitor_wrapper

# 监控所有指标
result = await system_monitor_wrapper(
    params={"target": "system", "metrics": ["cpu", "memory", "disk"]},
    context={}
)

# 查看结果
print(f"CPU使用率: {result['metrics']['cpu']['usage_percent']}%")
print(f"内存使用率: {result['metrics']['memory']['usage_percent']}%")
print(f"磁盘使用率: {result['metrics']['disk']['usage_percent']}%")
```

### 通过统一工具注册表调用

```python
from core.tools.unified_registry import get_unified_registry

registry = get_unified_registry()

# 获取工具
tool = registry.get("system_monitor")

# 调用工具
result = await tool.function(
    params={"metrics": ["cpu", "memory", "disk"]},
    context={}
)
```

---

## 功能说明

### CPU监控

监控CPU使用率，自动判断健康状态。

**返回数据**:
```python
{
    "usage_percent": 45.2,  # CPU使用率（百分比）
    "status": "healthy"     # 健康状态：healthy/warning/error
}
```

**健康阈值**: 使用率超过80%时状态变为warning

### 内存监控

监控内存使用情况，包括使用率、可用空间、已用空间。

**返回数据**:
```python
{
    "usage_percent": 65.8,  # 内存使用率（百分比）
    "free_gb": 4.2,        # 可用内存（GB）
    "used_gb": 8.1,        # 已用内存（GB）
    "status": "healthy"     # 健康状态：healthy/warning/error
}
```

**健康阈值**: 使用率超过80%时状态变为warning

### 磁盘监控

监控磁盘使用情况，包括总容量、已用空间、可用空间。

**返回数据**:
```python
{
    "total": "/dev/disk3s1s1",  # 磁盘设备
    "used": "926Gi",            # 已用空间
    "available": "12Gi",        # 可用空间
    "usage_percent": 6,         # 磁盘使用率（百分比）
    "status": "healthy"         # 健康状态：healthy/warning/error
}
```

**健康阈值**: 使用率超过85%时状态变为warning

---

## API参考

### 函数签名

```python
async def system_monitor_wrapper(
    params: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """
    系统监控处理器包装器

    Args:
        params: {
            "target": str,  # 监控目标 (system/process)，默认为"system"
            "metrics": list[str]  # 指标列表，可选值: ["cpu", "memory", "disk"]
        }
        context: 上下文信息（可选）

    Returns:
        dict[str, Any]: 监控数据字典
    """
```

### 参数说明

#### params

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|-----|------|------|--------|------|
| target | str | 否 | "system" | 监控目标（system/process） |
| metrics | list[str] | 否 | ["cpu", "memory"] | 监控指标列表 |

**metrics支持的值**:
- `"cpu"`: CPU监控
- `"memory"`: 内存监控
- `"disk"`: 磁盘监控

#### context

| 字段 | 类型 | 说明 |
|-----|------|------|
| （可选） | dict[str, Any] | 上下文信息，当前版本未使用 |

### 返回值

```python
{
    "target": "system",                    # 监控目标
    "timestamp": "2026-04-20T10:30:00",   # ISO格式时间戳
    "metrics": {
        "cpu": {
            "usage_percent": 45.2,
            "status": "healthy"
        },
        "memory": {
            "usage_percent": 65.8,
            "free_gb": 4.2,
            "used_gb": 8.1,
            "status": "healthy"
        },
        "disk": {
            "total": "/dev/disk3s1s1",
            "used": "926Gi",
            "available": "12Gi",
            "usage_percent": 6,
            "status": "healthy"
        }
    }
}
```

### 错误处理

工具不会抛出异常，所有错误都在返回的metrics中通过`status="error"`标识。

```python
# 示例：CPU监控失败
{
    "metrics": {
        "cpu": {
            "usage_percent": 0.0,
            "status": "error"
        }
    }
}
```

---

## 使用示例

### 示例1: 仅监控CPU

```python
result = await system_monitor_wrapper(
    params={"metrics": ["cpu"]},
    context={}
)

cpu_usage = result["metrics"]["cpu"]["usage_percent"]
cpu_status = result["metrics"]["cpu"]["status"]

print(f"CPU使用率: {cpu_usage}% ({cpu_status})")
```

### 示例2: 监控CPU和内存

```python
result = await system_monitor_wrapper(
    params={"metrics": ["cpu", "memory"]},
    context={}
)

cpu_usage = result["metrics"]["cpu"]["usage_percent"]
memory_usage = result["metrics"]["memory"]["usage_percent"]

print(f"CPU: {cpu_usage}%, 内存: {memory_usage}%")
```

### 示例3: 监控所有指标

```python
result = await system_monitor_wrapper(
    params={"metrics": ["cpu", "memory", "disk"]},
    context={}
)

# 打印完整报告
print("系统监控报告")
print("=" * 40)
print(f"CPU使用率: {result['metrics']['cpu']['usage_percent']}% ({result['metrics']['cpu']['status']})")
print(f"内存使用率: {result['metrics']['memory']['usage_percent']}% ({result['metrics']['memory']['status']})")
print(f"磁盘使用率: {result['metrics']['disk']['usage_percent']}% ({result['metrics']['disk']['status']})")
print(f"时间戳: {result['timestamp']}")
```

### 示例4: 健康检查

```python
result = await system_monitor_wrapper(
    params={"metrics": ["cpu", "memory", "disk"]},
    context={}
)

# 检查是否有任何指标处于warning状态
warnings = []
for metric_name, metric_data in result["metrics"].items():
    if metric_data["status"] == "warning":
        warnings.append(metric_name)

if warnings:
    print(f"⚠️ 警告: 以下指标超过阈值: {', '.join(warnings)}")
else:
    print("✅ 系统运行正常")
```

### 示例5: 定期监控

```python
import asyncio
from datetime import datetime

async def monitor_system(interval_seconds: int = 60, duration_seconds: int = 300):
    """定期监控系统状态"""
    start_time = datetime.now()
    end_time = start_time.timestamp() + duration_seconds

    while datetime.now().timestamp() < end_time:
        result = await system_monitor_wrapper(
            params={"metrics": ["cpu", "memory", "disk"]},
            context={}
        )

        print(f"[{datetime.now().strftime('%H:%M:%S')}] "
              f"CPU: {result['metrics']['cpu']['usage_percent']}%, "
              f"内存: {result['metrics']['memory']['usage_percent']}%, "
              f"磁盘: {result['metrics']['disk']['usage_percent']}%")

        await asyncio.sleep(interval_seconds)

# 运行监控（每60秒检查一次，持续5分钟）
await monitor_system(interval_seconds=60, duration_seconds=300)
```

### 示例6: 告警通知

```python
async def monitor_with_alert(threshold_cpu: float = 90.0):
    """监控并在超过阈值时发送告警"""
    result = await system_monitor_wrapper(
        params={"metrics": ["cpu", "memory", "disk"]},
        context={}
    )

    alerts = []

    # CPU告警
    cpu_usage = result["metrics"]["cpu"]["usage_percent"]
    if cpu_usage > threshold_cpu:
        alerts.append(f"CPU使用率过高: {cpu_usage}%")

    # 内存告警
    memory_usage = result["metrics"]["memory"]["usage_percent"]
    if memory_usage > threshold_cpu:
        alerts.append(f"内存使用率过高: {memory_usage}%")

    # 磁盘告警
    disk_usage = result["metrics"]["disk"]["usage_percent"]
    if disk_usage > threshold_cpu:
        alerts.append(f"磁盘使用率过高: {disk_usage}%")

    if alerts:
        print("🚨 系统告警:")
        for alert in alerts:
            print(f"  - {alert}")
    else:
        print("✅ 系统正常")

await monitor_with_alert(threshold_cpu=90.0)
```

---

## 最佳实践

### 1. 选择合适的监控指标

根据应用场景选择需要的监控指标：

```python
# Web应用：重点监控CPU和内存
result = await system_monitor_wrapper(
    params={"metrics": ["cpu", "memory"]},
    context={}
)

# 数据存储：重点监控磁盘
result = await system_monitor_wrapper(
    params={"metrics": ["disk"]},
    context={}
)

# 完整监控：所有指标
result = await system_monitor_wrapper(
    params={"metrics": ["cpu", "memory", "disk"]},
    context={}
)
```

### 2. 设置合理的监控频率

避免过度频繁的监控：

```python
# ❌ 不推荐：每秒监控（频率过高）
await monitor_system(interval_seconds=1, duration_seconds=60)

# ✅ 推荐：每分钟监控
await monitor_system(interval_seconds=60, duration_seconds=3600)

# ✅ 推荐：每5分钟监控
await monitor_system(interval_seconds=300, duration_seconds=3600)
```

### 3. 处理监控错误

始终检查返回的状态：

```python
result = await system_monitor_wrapper(
    params={"metrics": ["cpu", "memory", "disk"]},
    context={}
)

for metric_name, metric_data in result["metrics"].items():
    if metric_data["status"] == "error":
        print(f"⚠️ {metric_name}监控失败")
        continue

    # 正常处理
    print(f"{metric_name}: {metric_data['usage_percent']}%")
```

### 4. 设置告警阈值

根据实际需求设置告警阈值：

```python
# 严格阈值（生产环境）
STRICT_THRESHOLD = 80.0

# 宽松阈值（开发环境）
RELAXED_THRESHOLD = 90.0

# 使用阈值监控
async def monitor_with_threshold(threshold: float):
    result = await system_monitor_wrapper(
        params={"metrics": ["cpu", "memory", "disk"]},
        context={}
    )

    for metric_name, metric_data in result["metrics"].items():
        if metric_data["usage_percent"] > threshold:
            print(f"🚨 {metric_name}超过阈值: {metric_data['usage_percent']}%")
```

### 5. 记录历史数据

建议记录历史数据用于趋势分析：

```python
import json
from datetime import datetime
from pathlib import Path

async def monitor_and_log(log_file: str = "system_monitor.log"):
    """监控并记录到日志文件"""
    result = await system_monitor_wrapper(
        params={"metrics": ["cpu", "memory", "disk"]},
        context={}
    )

    # 添加时间戳
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "data": result
    }

    # 追加到日志文件
    log_path = Path(log_file)
    with log_path.open("a") as f:
        f.write(json.dumps(log_entry) + "\n")

    return result
```

---

## 故障排查

### 问题1: CPU监控失败

**症状**: `status="error"`

**可能原因**:
- `ps`命令不存在或无权限
- 系统兼容性问题

**解决方案**:
```bash
# 检查ps命令是否可用
ps -A -o %cpu

# 如果不可用，检查系统兼容性
uname -a
```

### 问题2: 内存监控失败

**症状**: `status="error"`

**可能原因**:
- `vm_stat`命令不存在（非macOS系统）
- 内存数据解析失败

**解决方案**:
```bash
# 检查vm_stat命令是否可用（仅macOS）
vm_stat

# Linux系统使用free命令
free -h
```

### 问题3: 磁盘监控失败

**症状**: `status="error"`

**可能原因**:
- `df`命令不存在或无权限
- 磁盘路径不正确

**解决方案**:
```bash
# 检查df命令是否可用
df -h /

# 尝试其他磁盘路径
df -h /home
df -h /var
```

### 问题4: 返回数据为空

**症状**: `metrics`字段为空

**可能原因**:
- 传入了无效的metrics参数
- 所有监控项都失败

**解决方案**:
```python
# 检查参数
params = {"metrics": ["cpu", "memory", "disk"]}  # 确保metrics有效

# 检查返回值
result = await system_monitor_wrapper(params, {})
if not result["metrics"]:
    print("⚠️ 没有有效的监控数据")
```

---

## FAQ

### Q1: system_monitor工具支持Windows吗？

**A**: 当前版本不支持Windows。Windows需要使用不同的系统命令（如`wmic`），未来版本可能会添加支持。

### Q2: 监控频率建议是多少？

**A**: 建议监控频率为1-5分钟，避免过度频繁的监控影响系统性能。

### Q3: 如何修改健康阈值？

**A**: 当前版本的健康阈值是硬编码的（CPU/内存: 80%, 磁盘: 85%）。如果需要自定义阈值，可以在调用后自行判断：

```python
result = await system_monitor_wrapper(
    params={"metrics": ["cpu", "memory", "disk"]},
    context={}
)

# 自定义阈值
custom_threshold = 75.0

if result["metrics"]["cpu"]["usage_percent"] > custom_threshold:
    print(f"⚠️ CPU超过自定义阈值: {custom_threshold}%")
```

### Q4: 工具会影响系统性能吗？

**A**: 工具的性能影响极小（响应时间~20ms），仅在监控时短暂占用CPU资源。

### Q5: 如何监控远程服务器？

**A**: 当前版本仅支持本地监控。如需监控远程服务器，需要先通过SSH连接到远程服务器，然后在远程服务器上运行监控工具。

### Q6: 支持进程级监控吗？

**A**: 当前版本仅支持系统级监控（`target="system"`）。进程级监控（`target="process"`）已在规划中，未来版本可能会添加支持。

---

## 附录

### A. 系统命令参考

| 命令 | 功能 | 平台 |
|-----|------|------|
| `ps -A -o %cpu` | 获取CPU使用率 | macOS/Linux |
| `vm_stat` | 获取内存使用情况 | macOS |
| `free` | 获取内存使用情况 | Linux |
| `df -h /` | 获取磁盘使用情况 | macOS/Linux |

### B. 健康阈值参考

| 指标 | 阈值 | 说明 |
|-----|------|------|
| CPU | 80% | 超过80%表示CPU负载较高 |
| 内存 | 80% | 超过80%表示内存紧张 |
| 磁盘 | 85% | 超过85%表示磁盘空间不足 |

### C. 相关文档

- **验证报告**: `docs/reports/SYSTEM_MONITOR_TOOL_VERIFICATION_REPORT_20260420.md`
- **包装器文件**: `core/tools/system_monitor_wrapper.py`
- **验证脚本**: `scripts/verify_system_monitor_tool.py`

---

**文档版本**: v1.0.0
**最后更新**: 2026-04-20
**维护者**: Athena平台团队
