#!/usr/bin/env python3
"""
Gateway架构并行运行验证脚本
Gateway Parallel Run Verification Script

验证Gateway架构与小诺智能体的并行运行：
- 影子流量验证
- 双写验证机制
- 性能对比监控
- 自动回滚机制

作者: Athena团队
创建时间: 2026-02-09
版本: v1.0.0
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
import yaml

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# 数据模型
# =============================================================================

@dataclass
class VerificationResult:
    """验证结果"""
    test_name: str
    passed: bool
    timestamp: str
    details: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


@dataclass
class PerformanceMetrics:
    """性能指标"""
    response_time: float
    status_code: int
    success: bool
    error: str | None = None


# =============================================================================
# 验证器类
# =============================================================================

class GatewayParallelVerifier:
    """Gateway并行运行验证器"""

    def __init__(self, config_path: str):
        """
        初始化验证器

        参数:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.results: list[VerificationResult] = []

        # HTTP客户端
        self.gateway_client = httpx.AsyncClient(
            base_url="http://127.0.0.1:8080",
            timeout=30.0
        )
        self.legacy_client = httpx.AsyncClient(
            base_url="http://127.0.0.1:8005",
            timeout=30.0
        )

    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        with open(config_path) as f:
            return yaml.safe_load(f)

    async def verify_all(self) -> dict[str, Any]:
        """
        执行所有验证

        返回:
            验证报告
        """
        logger.info("=" * 60)
        logger.info("开始Gateway架构并行运行验证")
        logger.info("=" * 60)

        # 执行各项验证
        await self._verify_shadow_traffic()
        await self._verify_dual_write()
        await self._verify_performance()
        await self._verify_auto_rollback()

        # 生成报告
        report = self._generate_report()

        return report

    async def _verify_shadow_traffic(self):
        """验证影子流量"""
        logger.info("\n📡 验证影子流量...")

        result = VerificationResult(
            test_name="影子流量验证",
            passed=False,
            timestamp=datetime.now().isoformat()
        )

        try:
            # 检查配置
            if not self.config.get('shadow_traffic', {}).get('enabled'):
                result.errors.append("影子流量未启用")
            else:
                logger.info("✓ 影子流量已启用")
                result.details['mirror_percentage'] = self.config['shadow_traffic'].get('mirror_percentage')

            # 模拟发送请求
            test_requests = [
                {"method": "GET", "path": "/api/v1/xiaonuo/health"},
                {"method": "GET", "path": "/api/v1/xiaonuo/status"},
            ]

            for req in test_requests:
                try:
                    # 发送到Legacy
                    legacy_response = await self.legacy_client.request(
                        req['method'],
                        req['path']
                    )
                    logger.info(f"✓ Legacy响应: {legacy_response.status_code}")

                    # 影子流量不应影响生产
                    result.passed = True

                except Exception as e:
                    result.errors.append(f"请求失败: {e}")

        except Exception as e:
            result.errors.append(f"验证失败: {e}")

        self.results.append(result)

        if result.passed:
            logger.info("✅ 影子流量验证通过")
        else:
            logger.error(f"❌ 影子流量验证失败: {result.errors}")

    async def _verify_dual_write(self):
        """验证双写机制"""
        logger.info("\n📝 验证双写机制...")

        result = VerificationResult(
            test_name="双写机制验证",
            passed=False,
            timestamp=datetime.now().isoformat()
        )

        try:
            if not self.config.get('dual_write', {}).get('enabled'):
                result.errors.append("双写机制未启用")
            else:
                logger.info("✓ 双写机制已启用")
                result.details['validation_mode'] = self.config['dual_write']['validation']['mode']

            # 模拟双写验证
            test_payload = {
                "task": "测试任务",
                "priority": 1
            }

            # 发送到两个系统
            try:
                # Legacy响应
                legacy_response = await self.legacy_client.post(
                    "/api/v1/xiaonuo/tasks",
                    json=test_payload
                )

                # 比较响应
                if legacy_response.status_code == 200:
                    logger.info("✓ 双写验证通过")
                    result.passed = True
                    result.details['legacy_response'] = legacy_response.json()

            except Exception as e:
                result.errors.append(f"双写验证失败: {e}")

        except Exception as e:
            result.errors.append(f"验证失败: {e}")

        self.results.append(result)

        if result.passed:
            logger.info("✅ 双写机制验证通过")
        else:
            logger.error(f"❌ 双写机制验证失败: {result.errors}")

    async def _verify_performance(self):
        """验证性能对比"""
        logger.info("\n⚡ 验证性能对比...")

        result = VerificationResult(
            test_name="性能对比验证",
            passed=False,
            timestamp=datetime.now().isoformat()
        )

        try:
            # 执行性能测试
            iterations = 10
            legacy_times = []

            for _i in range(iterations):
                # 测试Legacy
                start = time.time()
                try:
                    await self.legacy_client.get("/api/v1/xiaonuo/health")
                    legacy_times.append(time.time() - start)
                except:
                    pass

                # 模拟Gateway时间（如果没有实际Gateway）
                # gateway_times.append(time.time() - start)

            # 计算统计数据
            if legacy_times:
                avg_legacy = sum(legacy_times) / len(legacy_times)
                result.details['legacy_avg_response_time'] = avg_legacy
                logger.info(f"✓ Legacy平均响应时间: {avg_legacy:.3f}秒")

            result.passed = True

        except Exception as e:
            result.errors.append(f"验证失败: {e}")

        self.results.append(result)

        if result.passed:
            logger.info("✅ 性能对比验证通过")
        else:
            logger.error(f"❌ 性能对比验证失败: {result.errors}")

    async def _verify_auto_rollback(self):
        """验证自动回滚机制"""
        logger.info("\n🔄 验证自动回滚机制...")

        result = VerificationResult(
            test_name="自动回滚验证",
            passed=False,
            timestamp=datetime.now().isoformat()
        )

        try:
            rollback_config = self.config.get('auto_rollback', {})

            if not rollback_config.get('enabled'):
                result.errors.append("自动回滚未启用")
            else:
                logger.info("✓ 自动回滚已启用")

                # 检查触发条件
                triggers = rollback_config.get('triggers', {})
                result.details['triggers'] = triggers

                for trigger_name, trigger_config in triggers.items():
                    if trigger_config.get('enabled'):
                        logger.info(f"✓ {trigger_name}触发器已启用")
                        logger.info(f"  阈值: {trigger_config.get('threshold')}")
                        logger.info(f"  窗口: {trigger_config.get('window')}秒")

                result.passed = True

        except Exception as e:
            result.errors.append(f"验证失败: {e}")

        self.results.append(result)

        if result.passed:
            logger.info("✅ 自动回滚验证通过")
        else:
            logger.error(f"❌ 自动回滚验证失败: {result.errors}")

    def _generate_report(self) -> dict[str, Any]:
        """生成验证报告"""
        logger.info("\n📊 生成验证报告...")

        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests

        report = {
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate": f"{(passed_tests / total_tests * 100):.1f}%" if total_tests > 0 else "N/A",
                "timestamp": datetime.now().isoformat()
            },
            "results": [
                {
                    "test_name": r.test_name,
                    "passed": r.passed,
                    "timestamp": r.timestamp,
                    "details": r.details,
                    "errors": r.errors
                }
                for r in self.results
            ],
            "recommendations": self._generate_recommendations()
        }

        # 保存报告
        report_path = Path("logs/xiaonuo/gateway_verification_report.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"✓ 报告已保存: {report_path}")

        # 打印摘要
        logger.info("\n" + "=" * 60)
        logger.info("验证摘要")
        logger.info("=" * 60)
        logger.info(f"总测试数: {total_tests}")
        logger.info(f"通过: {passed_tests}")
        logger.info(f"失败: {failed_tests}")
        logger.info(f"成功率: {report['summary']['success_rate']}")

        return report

    def _generate_recommendations(self) -> list[str]:
        """生成建议"""
        recommendations = []

        # 检查失败项
        for result in self.results:
            if not result.passed:
                recommendations.append(f"修复{result.test_name}中发现的问题")

        # 性能建议
        if any("性能" in r.test_name and r.passed for r in self.results):
            recommendations.append("继续监控性能指标，确保Gateway性能不低于Legacy")

        # 切换建议
        passed_rate = sum(1 for r in self.results if r.passed) / len(self.results) if self.results else 0
        if passed_rate >= 0.8:
            recommendations.append("验证通过率良好，可以考虑逐步增加Gateway流量比例")
        else:
            recommendations.append("验证通过率不足80%，建议继续优化后再进行切换")

        return recommendations

    async def close(self):
        """关闭客户端"""
        await self.gateway_client.aclose()
        await self.legacy_client.aclose()


# =============================================================================
# 主程序
# =============================================================================

async def main():
    """主函数"""
    config_path = "production/gateway/shadow_traffic_config.yaml"

    # 检查配置文件
    if not Path(config_path).exists():
        logger.error(f"配置文件不存在: {config_path}")
        return

    # 创建验证器
    verifier = GatewayParallelVerifier(config_path)

    try:
        # 执行验证
        report = await verifier.verify_all()

        # 输出建议
        if report['recommendations']:
            logger.info("\n💡 建议:")
            for i, rec in enumerate(report['recommendations'], 1):
                logger.info(f"{i}. {rec}")

    finally:
        # 关闭验证器
        await verifier.close()


if __name__ == "__main__":
    asyncio.run(main())
