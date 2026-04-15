#!/usr/bin/env python3
from __future__ import annotations
# ============================================================
# AI伦理框架 - 容器健康检查脚本
# AI Ethics Framework - Container Health Check
# ============================================================

import json
import os
import sys
import urllib.request

# 健康检查配置
HEALTH_CHECK_URL = os.getenv(
    "HEALTH_CHECK_URL", f"http://localhost:{os.getenv('API_PORT', '8080')}/health"
)
TIMEOUT = int(os.getenv("HEALTH_CHECK_TIMEOUT", "5"))


def check_api_health() -> bool:
    """检查API健康状态"""
    try:
        request = urllib.request.Request(
            HEALTH_CHECK_URL, method="GET", headers={"Accept": "application/json"}
        )

        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                return data.get("status") == "healthy"
            return False
    except Exception as e:
        print(f"API健康检查失败: {e}", file=sys.stderr)
        return False


def check_evaluator() -> bool:
    """检查评估器是否正常工作"""
    try:
        from core.ethics import get_container

        container = get_container()
        evaluator = container.create_evaluator()

        # 执行简单的评估
        result = evaluator.evaluate_action(agent_id="health_check", action="健康检查", context={})

        return result is not None
    except Exception as e:
        print(f"评估器健康检查失败: {e}", file=sys.stderr)
        return False


def check_monitor() -> bool:
    """检查监控器是否正常工作"""
    try:
        from core.ethics import get_container

        container = get_container()
        monitor = container.create_monitor()

        # 获取指标
        metrics = monitor.get_current_metrics()
        return metrics is not None
    except Exception as e:
        print(f"监控器健康检查失败: {e}", file=sys.stderr)
        return False


def check_config() -> bool:
    """检查配置是否正确加载"""
    try:
        from core.ethics.config.config_loader import ConfigLoader

        loader = ConfigLoader()
        config = loader.load_config()

        return config is not None
    except Exception as e:
        print(f"配置健康检查失败: {e}", file=sys.stderr)
        return False


def check_prometheus() -> bool:
    """检查Prometheus监控是否正常"""
    try:
        prometheus_port = os.getenv("PROMETHEUS_PORT", "9091")
        url = f"http://localhost:{prometheus_port}/metrics"

        request = urllib.request.Request(url, method="GET")

        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return response.status == 200
    except Exception as e:
        print(f"Prometheus健康检查失败: {e}", file=sys.stderr)
        return False


def run_health_checks() -> dict[str, bool]:
    """运行所有健康检查"""
    checks = {
        "api": check_api_health(),
        "evaluator": check_evaluator(),
        "monitor": check_monitor(),
        "config": check_config(),
        "prometheus": check_prometheus(),
    }

    return checks


def main() -> int:
    """主函数"""
    print("运行健康检查...", file=sys.stderr)

    checks = run_health_checks()

    # 打印检查结果
    for name, status in checks.items():
        status_str = "✓" if status else "✗"
        print(f"  {status_str} {name}", file=sys.stderr)

    # 所有检查都必须通过
    all_healthy = all(checks.values())

    if all_healthy:
        print("健康状态: 健康", file=sys.stderr)
        return 0
    else:
        print("健康状态: 不健康", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
