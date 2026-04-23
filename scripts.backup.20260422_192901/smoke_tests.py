#!/usr/bin/env python3
"""
Athena工作平台 - 冒烟测试脚本
Smoke Tests Script for Athena Platform

用途: 部署后的快速健康检查和功能验证
使用: python3 scripts/smoke_tests.py --env production
"""

import argparse
import sys
import time

import requests


# 颜色输出
class Colors:
    BLUE = "\033[0;34m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    RED = "\033[0;31m"
    NC = "\033[0m"  # No Color


def log_info(message: str):
    print(f"{Colors.BLUE}[INFO]{Colors.NC} {message}")


def log_success(message: str):
    print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {message}")


def log_warning(message: str):
    print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {message}")


def log_error(message: str):
    print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")


def log_step(message: str):
    print(f"\n{Colors.GREEN}==>{Colors.NC} {message}")


# 端点配置
ENDPOINTS = {
    "production": {
        "base_url": "http://localhost:8080",
        "health": "/health",
        "metrics": "/metrics",
        "api_search": "/api/search",
        "api_stats": "/api/stats",
    },
    "staging": {
        "base_url": "http://localhost:8081",
        "health": "/health",
        "metrics": "/metrics",
        "api_search": "/api/search",
        "api_stats": "/api/stats",
    },
}


class SmokeTests:
    """冒烟测试类"""

    def __init__(self, environment: str = "production"):
        self.environment = environment
        self.config = ENDPOINTS.get(environment, ENDPOINTS["production"])
        self.base_url = self.config["base_url"]
        self.results = []

    def run_test(self, test_name: str, test_func) -> bool:
        """运行单个测试"""
        log_info(f"运行测试: {test_name}")
        try:
            test_func()
            self.results.append({"name": test_name, "status": "PASS"})
            log_success(f"✓ {test_name}")
            return True
        except Exception as e:
            self.results.append({"name": test_name, "status": "FAIL", "error": str(e)})
            log_error(f"✗ {test_name}: {e}")
            return False

    def test_health_check(self):
        """测试健康检查端点"""
        response = requests.get(f"{self.base_url}{self.config['health']}", timeout=10)
        response.raise_for_status()
        data = response.json()
        assert data["status"] == "healthy", f"状态不健康: {data}"

    def test_metrics_endpoint(self):
        """测试Prometheus指标端点"""
        response = requests.get(f"{self.base_url}{self.config['metrics']}", timeout=10)
        response.raise_for_status()
        # 验证返回Prometheus格式的指标
        assert "athena_execution" in response.text or "process_" in response.text

    def test_api_search(self):
        """测试搜索API"""
        response = requests.post(
            f"{self.base_url}{self.config['api_search']}",
            json={"query": "测试查询", "limit": 5},
            headers={"X-API-Key": "test-api-key"},
            timeout=30,
        )
        # 401表示需要认证（这是正常的），404表示端点不存在
        if response.status_code in [200, 401]:
            return
        response.raise_for_status()

    def test_api_stats(self):
        """测试统计API"""
        response = requests.get(
            f"{self.base_url}{self.config['api_stats']}",
            headers={"X-API-Key": "test-api-key"},
            timeout=10,
        )
        # 401表示需要认证（这是正常的），404表示端点不存在
        if response.status_code in [200, 401]:
            return
        response.raise_for_status()

    def test_database_connection(self):
        """测试数据库连接（通过健康检查的深度检查）"""
        response = requests.get(f"{self.base_url}/health/deep", timeout=30)
        response.raise_for_status()
        data = response.json()
        # 检查各组件状态
        assert "components" in data, "缺少组件信息"
        components = data["components"]
        # 至少应该有一些组件是健康的
        healthy_count = sum(1 for c in components.values() if isinstance(c, dict) and c.get("status") == "ok")
        assert healthy_count > 0, f"没有健康的组件: {components}"

    def test_response_time(self):
        """测试响应时间"""
        start_time = time.time()
        response = requests.get(f"{self.base_url}{self.config['health']}", timeout=10)
        response.raise_for_status()
        elapsed = time.time() - start_time
        assert elapsed < 2.0, f"响应时间过长: {elapsed:.2f}秒"
        log_info(f"响应时间: {elapsed:.3f}秒")

    def run_all_tests(self):
        """运行所有冒烟测试"""
        log_step("开始冒烟测试...")
        log_info(f"环境: {self.environment}")
        log_info(f"基础URL: {self.base_url}")

        # 定义测试列表
        tests = [
            ("健康检查", self.test_health_check),
            ("响应时间", self.test_response_time),
            ("Prometheus指标", self.test_metrics_endpoint),
            ("搜索API", self.test_api_search),
            ("统计API", self.test_api_stats),
            ("数据库连接", self.test_database_connection),
        ]

        # 运行所有测试
        passed = 0
        failed = 0
        for test_name, test_func in tests:
            if self.run_test(test_name, test_func):
                passed += 1
            else:
                failed += 1

        # 显示测试结果摘要
        log_step("测试结果摘要")
        print(f"\n总计: {len(self.results)} 个测试")
        print(f"通过: {passed} 个")
        print(f"失败: {failed} 个")
        print(f"成功率: {passed / len(self.results) * 100:.1f}%")

        # 如果所有测试通过，返回成功
        if failed == 0:
            log_success("所有冒烟测试通过")
            return 0
        else:
            log_error(f"有 {failed} 个测试失败")
            return 1


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Athena工作平台冒烟测试")
    parser.add_argument("--env", default="production", choices=["production", "staging"], help="部署环境")
    parser.add_argument("--base-url", help="覆盖基础URL")
    args = parser.parse_args()

    print(f"{Colors.BLUE}")
    print("=" * 60)
    print("  Athena工作平台 - 冒烟测试")
    print("=" * 60)
    print(f"{Colors.NC}")

    # 创建测试实例
    tests = SmokeTests(environment=args.env)

    # 如果指定了基础URL，覆盖默认值
    if args.base_url:
        tests.base_url = args.base_url
        log_info(f"使用自定义基础URL: {args.base_url}")

    # 运行测试
    try:
        exit_code = tests.run_all_tests()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        log_warning("\n测试被中断")
        sys.exit(1)
    except Exception as e:
        log_error(f"\n测试失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
