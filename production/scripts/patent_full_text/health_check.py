#!/usr/bin/env python3
"""
专利全文处理系统 - 健康检查脚本
Patent Full Text Processing System - Health Check

检查所有服务组件的健康状态

作者: Athena平台团队
创建时间: 2025-12-25
"""

from __future__ import annotations
import argparse
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import requests


@dataclass
class HealthCheckResult:
    """健康检查结果"""
    name: str
    healthy: bool
    message: str
    latency_ms: float = 0.0
    details: dict = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}


class PatentHealthChecker:
    """专利系统健康检查器"""

    def __init__(self, timeout: int = 5):
        """
        初始化健康检查器

        Args:
            timeout: 请求超时时间（秒）
        """
        self.timeout = timeout
        self.results: list[HealthCheckResult] = []

    def check_all(self, config: dict) -> dict[str, HealthCheckResult]:
        """
        检查所有服务

        Args:
            config: 配置字典

        Returns:
            检查结果字典
        """
        print("\n" + "="*60)
        print("  专利全文处理系统 - 健康检查")
        print("="*60)
        print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        results = {}

        # 检查Qdrant
        results["qdrant"] = self._check_qdrant(
            config.get("QDRANT_HOST", "localhost"),
            int(config.get("QDRANT_PORT", 6333))
        )

        # 检查NebulaGraph
        results["nebula"] = self._check_nebula(
            config.get("NEBULA_HOST", "localhost"),
            int(config.get("NEBULA_PORT", 9669))
        )

        # 检查Redis
        results["redis"] = self._check_redis(
            config.get("REDIS_HOST", "localhost"),
            int(config.get("REDIS_PORT", 6379))
        )

        # 检查应用API
        results["api"] = self._check_api(
            config.get("PATENT_API_HOST", "localhost"),
            int(config.get("PATENT_API_PORT", 8000))
        )

        # 打印结果
        self._print_results(results)

        return results

    def _check_qdrant(self, host: str, port: int) -> HealthCheckResult:
        """检查Qdrant"""
        url = f"http://{host}:{port}/health"
        return self._check_http("Qdrant", url)

    def _check_nebula(self, host: str, port: int) -> HealthCheckResult:
        """检查NebulaGraph"""
        # Nebula没有内置健康检查端点，我们检查端口是否开放
        import socket
        start = time.time()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((host, port))
            sock.close()

            latency = (time.time() - start) * 1000
            if result == 0:
                return HealthCheckResult(
                    name="NebulaGraph",
                    healthy=True,
                    message=f"连接成功 ({host}:{port})",
                    latency_ms=latency
                )
            else:
                return HealthCheckResult(
                    name="NebulaGraph",
                    healthy=False,
                    message=f"连接失败 ({host}:{port})",
                    latency_ms=latency
                )
        except Exception as e:
            return HealthCheckResult(
                name="NebulaGraph",
                healthy=False,
                message=f"检查失败: {str(e)}"
            )

    def _check_redis(self, host: str, port: int) -> HealthCheckResult:
        """检查Redis"""
        import socket
        start = time.time()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((host, port))
            sock.close()

            latency = (time.time() - start) * 1000
            if result == 0:
                return HealthCheckResult(
                    name="Redis",
                    healthy=True,
                    message=f"连接成功 ({host}:{port})",
                    latency_ms=latency
                )
            else:
                return HealthCheckResult(
                    name="Redis",
                    healthy=False,
                    message=f"连接失败 ({host}:{port})",
                    latency_ms=latency
                )
        except Exception as e:
            return HealthCheckResult(
                name="Redis",
                healthy=False,
                message=f"检查失败: {str(e)}"
            )

    def _check_api(self, host: str, port: int) -> HealthCheckResult:
        """检查应用API"""
        url = f"http://{host}:{port}/health"
        return self._check_http("API服务", url)

    def _check_http(self, name: str, url: str) -> HealthCheckResult:
        """执行HTTP健康检查"""
        start = time.time()
        try:
            response = requests.get(url, timeout=self.timeout)
            latency = (time.time() - start) * 1000

            if response.status_code == 200:
                return HealthCheckResult(
                    name=name,
                    healthy=True,
                    message="健康检查通过",
                    latency_ms=latency,
                    details=response.json() if response.headers.get('content-type', '').startswith('application/json') else None
                )
            else:
                return HealthCheckResult(
                    name=name,
                    healthy=False,
                    message=f"状态码: {response.status_code}",
                    latency_ms=latency
                )
        except requests.exceptions.Timeout:
            return HealthCheckResult(
                name=name,
                healthy=False,
                message=f"请求超时 (> {self.timeout}秒)"
            )
        except Exception as e:
            return HealthCheckResult(
                name=name,
                healthy=False,
                message=f"检查失败: {str(e)}"
            )

    def _print_results(self, results: dict[str, HealthCheckResult]) -> None:
        """打印检查结果"""
        print("\n服务状态:")
        print("-" * 60)

        healthy_count = 0
        total_count = len(results)

        for _service_name, result in results.items():
            icon = "✅" if result.healthy else "❌"
            latency_info = f" ({result.latency_ms:.0f}ms)" if result.healthy else ""
            print(f"{icon} {result.name}: {result.message}{latency_info}")
            if result.healthy:
                healthy_count += 1

        print("-" * 60)
        print(f"\n健康度: {healthy_count}/{total_count} ({healthy_count*100//total_count}%)")

        # 判断整体健康状态
        if healthy_count == total_count:
            print("✅ 所有服务运行正常")
            sys.exit(0)
        else:
            print("⚠️  部分服务异常，请检查")
            sys.exit(1)


def load_config_from_env(env_file: Path) -> dict[str, str]:
    """从环境文件加载配置"""
    config = {}
    if env_file.exists():
        with open(env_file, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = os.path.expandvars(value.strip())
    return config


def main() -> None:
    """主函数"""
    parser = argparse.ArgumentParser(description="专利全文处理系统健康检查")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).parent.parent / "config" / ".env",
        help="环境配置文件路径"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=5,
        help="请求超时时间（秒）"
    )

    args = parser.parse_args()

    # 加载配置
    config = load_config_from_env(args.config)

    # 执行健康检查
    checker = PatentHealthChecker(timeout=args.timeout)
    checker.check_all(config)


if __name__ == "__main__":
    main()
