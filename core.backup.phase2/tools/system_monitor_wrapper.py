#!/usr/bin/env python3
"""
system_monitor工具包装器

提供符合统一工具接口的system_monitor工具包装器。

核心功能:
1. CPU使用率监控
2. 内存使用情况监控
3. 磁盘使用情况监控
4. 健康状态判断
5. 跨平台兼容性

Author: Athena平台团队
Created: 2026-04-20
"""

from __future__ import annotations

import asyncio
import logging
import subprocess
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


async def system_monitor_wrapper(
    params: dict[str, Any],
    context: dict[str, Any],  # noqa: ARG001 (保留用于接口兼容性)
) -> dict[str, Any]:
    """
    系统监控处理器包装器 - 符合统一工具接口

    功能:
    1. CPU使用率监控
    2. 内存使用情况监控
    3. 磁盘使用情况监控
    4. 系统负载监控

    Args:
        params: {
            "target": str,  # 监控目标 (system/process)，默认为"system"
            "metrics": list[str]  # 指标列表，可选值: ["cpu", "memory", "disk"]，默认为["cpu", "memory"]
        }
        context: 上下文信息（当前未使用，保留用于接口兼容性）

    Returns:
        dict[str, Any]: 监控数据字典，包含：
            - target: 监控目标
            - timestamp: ISO格式时间戳
            - metrics: 包含各项指标的字典
                - cpu: CPU使用率信息
                    - usage_percent: 使用率百分比
                    - status: 健康状态 (healthy/warning/error)
                - memory: 内存使用信息
                    - usage_percent: 使用率百分比
                    - free_gb: 可用内存（GB）
                    - used_gb: 已用内存（GB）
                    - status: 健康状态
                - disk: 磁盘使用信息
                    - total: 总容量
                    - used: 已用空间
                    - available: 可用空间
                    - usage_percent: 使用率百分比
                    - status: 健康状态

    Raises:
        不抛出异常，所有错误都在metrics中返回status="error"

    Examples:
        >>> # 仅监控CPU
        >>> result = await system_monitor_wrapper(
        ...     params={"target": "system", "metrics": ["cpu"]},
        ...     context={}
        ... )

        >>> # 监控CPU和内存
        >>> result = await system_monitor_wrapper(
        ...     params={"target": "system", "metrics": ["cpu", "memory"]},
        ...     context={}
        ... )

        >>> # 监控所有指标
        >>> result = await system_monitor_wrapper(
        ...     params={"target": "system", "metrics": ["cpu", "memory", "disk"]},
        ...     context={}
        ... )
    """
    # 解析参数
    target: str = params.get("target", "system")
    metrics: list[str] = params.get("metrics", ["cpu", "memory"])

    # 验证参数
    if target not in ["system", "process"]:
        logger.warning(f"不支持的监控目标: {target}，使用默认值'system'")
        target = "system"

    valid_metrics = {"cpu", "memory", "disk"}
    invalid_metrics = set(metrics) - valid_metrics
    if invalid_metrics:
        logger.warning(f"不支持的监控指标: {invalid_metrics}，将被忽略")
        metrics = [m for m in metrics if m in valid_metrics]

    # 如果没有有效的metrics，返回空结果
    if not metrics:
        logger.warning("没有有效的监控指标")
        return {
            "target": target,
            "timestamp": datetime.now().isoformat(),
            "metrics": {},
            "error": "No valid metrics to monitor",
        }

    # 模拟监控延迟（实际监控中可能需要）
    await asyncio.sleep(0.02)

    # 初始化结果字典
    result = {
        "target": target,
        "timestamp": datetime.now().isoformat(),
        "metrics": {},
    }

    # ========================================
    # CPU监控
    # ========================================
    if "cpu" in metrics:
        try:
            if target == "system":
                # 获取CPU使用率（使用ps命令）
                cpu_output = subprocess.check_output(
                    ["ps", "-A", "-o", "%cpu"],
                    text=True,
                    stderr=subprocess.DEVNULL,
                )

                # 解析CPU使用率
                cpu_values = [
                    float(line.strip())
                    for line in cpu_output.split("\n")[1:]
                    if line.strip()
                ]
                avg_cpu = sum(cpu_values) / len(cpu_values) if cpu_values else 0.0

                result["metrics"]["cpu"] = {
                    "usage_percent": round(avg_cpu, 2),
                    "status": "healthy" if avg_cpu < 80 else "warning",
                }
            else:
                # process目标的CPU监控暂未实现
                result["metrics"]["cpu"] = {
                    "usage_percent": 0.0,
                    "status": "unknown",
                }

        except FileNotFoundError:
            logger.warning("ps命令未找到，CPU监控失败")
            result["metrics"]["cpu"] = {"usage_percent": 0.0, "status": "error"}
        except subprocess.CalledProcessError as e:
            logger.warning(f"CPU监控命令执行失败: {e}")
            result["metrics"]["cpu"] = {"usage_percent": 0.0, "status": "error"}
        except Exception as e:
            logger.warning(f"CPU监控失败: {e}")
            result["metrics"]["cpu"] = {"usage_percent": 0.0, "status": "error"}

    # ========================================
    # 内存监控
    # ========================================
    if "memory" in metrics:
        try:
            # 获取内存使用情况（使用vm_stat命令）
            mem_output = subprocess.check_output(
                ["vm_stat"],
                text=True,
                stderr=subprocess.DEVNULL,
            )

            # 解析vm_stat输出
            mem_stats = {}
            for line in mem_output.split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    mem_stats[key.strip()] = value.strip().replace(".", "")

            # 计算内存使用（macOS页面大小为4096字节）
            page_size = 4096
            free_pages = int(mem_stats.get("Pages free", "0"))
            active_pages = int(mem_stats.get("Pages active", "0"))
            inactive_pages = int(mem_stats.get("Pages inactive", "0"))
            wired_pages = int(mem_stats.get("Pages wired", "0"))

            total_pages = free_pages + active_pages + inactive_pages + wired_pages
            used_percent = (
                (active_pages + wired_pages) / total_pages * 100
                if total_pages > 0
                else 0.0
            )

            result["metrics"]["memory"] = {
                "usage_percent": round(used_percent, 2),
                "free_gb": round(free_pages * page_size / (1024**3), 2),
                "used_gb": round((active_pages + wired_pages) * page_size / (1024**3), 2),
                "status": "healthy" if used_percent < 80 else "warning",
            }

        except FileNotFoundError:
            logger.warning("vm_stat命令未找到，内存监控失败")
            result["metrics"]["memory"] = {"usage_percent": 0.0, "status": "error"}
        except subprocess.CalledProcessError as e:
            logger.warning(f"内存监控命令执行失败: {e}")
            result["metrics"]["memory"] = {"usage_percent": 0.0, "status": "error"}
        except (ValueError, KeyError) as e:
            logger.warning(f"内存数据解析失败: {e}")
            result["metrics"]["memory"] = {"usage_percent": 0.0, "status": "error"}
        except Exception as e:
            logger.warning(f"内存监控失败: {e}")
            result["metrics"]["memory"] = {"usage_percent": 0.0, "status": "error"}

    # ========================================
    # 磁盘监控
    # ========================================
    if "disk" in metrics:
        try:
            # 获取磁盘使用情况（使用df命令）
            disk_output = subprocess.check_output(
                ["df", "-h", "/"],
                text=True,
                stderr=subprocess.DEVNULL,
            )

            # 解析df输出
            lines = disk_output.split("\n")
            if len(lines) >= 2:
                parts = lines[1].split()
                if len(parts) >= 5:
                    used_percent = int(parts[4].replace("%", ""))
                    result["metrics"]["disk"] = {
                        "total": parts[0],
                        "used": parts[1],
                        "available": parts[2],
                        "usage_percent": used_percent,
                        "status": "healthy" if used_percent < 85 else "warning",
                    }
                else:
                    logger.warning("磁盘输出格式不正确")
                    result["metrics"]["disk"] = {"usage_percent": 0, "status": "error"}
            else:
                logger.warning("磁盘输出为空")
                result["metrics"]["disk"] = {"usage_percent": 0, "status": "error"}

        except FileNotFoundError:
            logger.warning("df命令未找到，磁盘监控失败")
            result["metrics"]["disk"] = {"usage_percent": 0, "status": "error"}
        except subprocess.CalledProcessError as e:
            logger.warning(f"磁盘监控命令执行失败: {e}")
            result["metrics"]["disk"] = {"usage_percent": 0, "status": "error"}
        except (ValueError, IndexError) as e:
            logger.warning(f"磁盘数据解析失败: {e}")
            result["metrics"]["disk"] = {"usage_percent": 0, "status": "error"}
        except Exception as e:
            logger.warning(f"磁盘监控失败: {e}")
            result["metrics"]["disk"] = {"usage_percent": 0, "status": "error"}

    return result


# 为了向后兼容，保留原始名称
async def system_monitor_handler(
    params: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """
    向后兼容的别名

    Deprecated: 建议直接使用system_monitor_wrapper
    """
    return await system_monitor_wrapper(params, context)
