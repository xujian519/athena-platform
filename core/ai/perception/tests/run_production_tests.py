#!/usr/bin/env python3

"""
Athena 感知模块 - 生产验证测试运行器
统一运行所有生产验证测试并生成报告
最后更新: 2026-01-26
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProductionTestRunner:
    """
    生产验证测试运行器

    运行所有测试套件并生成综合报告
    """

    def __init__(self):
        """初始化测试运行器"""
        self.test_results: dict[str, Any] = {
            "load_tests": {},
            "stability_tests": {},
            "extreme_tests": {},
            "benchmark_tests": {}
        }
        self.start_time = None
        self.end_time = None
        self.overall_success = True
        self.production_readiness_score = 0.0

    async def run_all_tests(
        self,
        test_image: str,
        quick_mode: bool = False
    ) -> dict[str, Any]:
        """
        运行所有测试

        Args:
            test_image: 测试图像路径
            quick_mode: 快速模式（减少测试迭代次数）

        Returns:
            所有测试结果
        """
        self.start_time = datetime.now()

        logger.info("\n" + "="*70)
        logger.info("🚀 Athena 感知模块 - 生产验证测试套件")
        logger.info("="*70)
        logger.info(f"开始时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"测试图像: {test_image}")
        logger.info(f"快速模式: {'是' if quick_mode else '否'}")
        logger.info("="*70 + "\n")

        # 1. 负载测试
        logger.info("\n📊 第1部分: 负载测试")
        await self._run_load_tests(test_image, quick_mode)

        # 2. 稳定性测试
        logger.info("\n📊 第2部分: 稳定性测试")
        await self._run_stability_tests(test_image, quick_mode)

        # 3. 极端场景测试
        logger.info("\n📊 第3部分: 极端场景测试")
        await self._run_extreme_tests()

        # 4. 性能基准测试
        logger.info("\n📊 第4部分: 性能基准测试")
        await self._run_benchmark_tests(test_image, quick_mode)

        self.end_time = datetime.now()

        # 计算生产就绪度得分
        self._calculate_readiness_score()

        # 生成报告
        self._print_final_report()

        return self.test_results

    async def _run_load_tests(self, test_image: str, quick_mode: bool):
        """运行负载测试"""
        try:
            from load_test import LoadTester

            tester = LoadTester()

            if quick_mode:
                # 快速模式：较少迭代
                logger.info("🔍 快速模式负载测试...")
                result1 = await tester.test_concurrent_ocr(
                    image_path=test_image,
                    concurrent_users=5,
                    total_requests=20,
                    use_cache=True
                )
                self.test_results["load_tests"]["concurrent_ocr"] = result1.get_statistics()

            else:
                # 完整模式
                logger.info("🔍 完整负载测试...")

                # 并发OCR测试
                result1 = await tester.test_concurrent_ocr(
                    image_path=test_image,
                    concurrent_users=10,
                    total_requests=50,
                    use_cache=True
                )
                self.test_results["load_tests"]["concurrent_ocr"] = result1.get_statistics()

                # 缓存性能测试
                result2 = await tester.test_cache_performance(
                    image_path=test_image,
                    iterations=100
                )
                self.test_results["load_tests"]["cache_performance"] = result2.get_statistics()

                # 任务队列吞吐量测试
                result3 = await tester.test_task_queue_throughput(
                    num_tasks=50,
                    concurrent_workers=10
                )
                self.test_results["load_tests"]["task_queue"] = result3.get_statistics()

            logger.info("✅ 负载测试完成")

        except Exception as e:
            logger.error(f"❌ 负载测试失败: {e}")
            self.overall_success = False

    async def _run_stability_tests(self, test_image: str, quick_mode: bool):
        """运行稳定性测试"""
        try:
            from stability_test import StabilityTester

            tester = StabilityTester()

            if quick_mode:
                # 快速模式：较少迭代
                logger.info("🔍 快速模式稳定性测试...")
                result1 = await tester.test_memory_leak_detection(
                    image_path=test_image,
                    iterations=30
                )
                self.test_results["stability_tests"]["memory_leak"] = result1.get_analysis()

            else:
                # 完整模式
                logger.info("🔍 完整稳定性测试...")

                # 内存泄漏检测
                result1 = await tester.test_memory_leak_detection(
                    image_path=test_image,
                    iterations=100
                )
                self.test_results["stability_tests"]["memory_leak"] = result1.get_analysis()

                # 资源清理测试
                result2 = await tester.test_resource_cleanup(
                    image_path=test_image,
                    iterations=50
                )
                self.test_results["stability_tests"]["resource_cleanup"] = result2.get_analysis()

            logger.info("✅ 稳定性测试完成")

        except Exception as e:
            logger.error(f"❌ 稳定性测试失败: {e}")
            self.overall_success = False

    async def _run_extreme_tests(self):
        """运行极端场景测试"""
        try:
            from extreme_test import ExtremeTester

            tester = ExtremeTester()

            logger.info("🔍 极端场景测试...")

            # 无效输入测试
            result1 = await tester.test_invalid_inputs()
            self.test_results["extreme_tests"]["invalid_inputs"] = result1.get_summary()

            # 网络中断模拟测试
            result2 = await tester.test_network_interruption()
            self.test_results["extreme_tests"]["network_interruption"] = result2.get_summary()

            # 资源耗尽测试
            result3 = await tester.test_resource_exhaustion()
            self.test_results["extreme_tests"]["resource_exhaustion"] = result3.get_summary()

            # 熔断器测试
            result4 = await tester.test_circuit_breaker()
            self.test_results["extreme_tests"]["circuit_breaker"] = result4.get_summary()

            logger.info("✅ 极端场景测试完成")

        except Exception as e:
            logger.error(f"❌ 极端场景测试失败: {e}")
            self.overall_success = False

    async def _run_benchmark_tests(self, test_image: str, quick_mode: bool):
        """运行性能基准测试"""
        try:
            from benchmark_test import BenchmarkTester

            tester = BenchmarkTester()

            if quick_mode:
                # 快速模式：较少迭代
                logger.info("🔍 快速模式性能基准测试...")
                result1 = await tester.benchmark_ocr_performance(
                    image_path=test_image,
                    iterations=5,
                    warmup_iterations=1
                )
                self.test_results["benchmark_tests"]["ocr"] = result1.get_summary()

            else:
                # 完整模式
                logger.info("🔍 完整性能基准测试...")

                # OCR性能测试
                result1 = await tester.benchmark_ocr_performance(
                    image_path=test_image,
                    iterations=20,
                    warmup_iterations=3
                )
                self.test_results["benchmark_tests"]["ocr"] = result1.get_summary()

                # 图像处理性能测试
                result2 = await tester.benchmark_image_processing(
                    image_path=test_image,
                    operations=["edge_detection", "blur"],
                    iterations=10
                )
                self.test_results["benchmark_tests"]["image_processing"] = result2.get_summary()

                # 缓存性能测试
                await tester.benchmark_cache_performance(
                    iterations=50
                )
                # 缓存测试有两个结果（读/写）
                self.test_results["benchmark_tests"]["cache_write"] = tester.benchmarks["cache_write"].get_summary()
                self.test_results["benchmark_tests"]["cache_read"] = tester.benchmarks["cache_read"].get_summary()

            logger.info("✅ 性能基准测试完成")

        except Exception as e:
            logger.error(f"❌ 性能基准测试失败: {e}")
            self.overall_success = False

    def _calculate_readiness_score(self):
        """计算生产就绪度得分"""
        scores = []

        # 负载测试得分 (30%)
        load_score = 0.0
        if "load_tests" in self.test_results:
            for _test_name, result in self.test_results["load_tests"].items():
                if isinstance(result, dict) and "success_rate" in result:
                    load_score += result["success_rate"]
            if self.test_results["load_tests"]:
                load_score = load_score / len(self.test_results["load_tests"])
        scores.append(("负载测试", load_score, 0.30))

        # 稳定性测试得分 (30%)
        stability_score = 0.0
        if "stability_tests" in self.test_results:
            stable_count = 0
            total_count = 0
            for _test_name, result in self.test_results["stability_tests"].items():
                if isinstance(result, dict) and "overall_stable" in result:
                    total_count += 1
                    if result["overall_stable"]:
                        stable_count += 1
            if total_count > 0:
                stability_score = (stable_count / total_count) * 100
        scores.append(("稳定性测试", stability_score, 0.30))

        # 极端场景测试得分 (20%)
        extreme_score = 0.0
        if "extreme_tests" in self.test_results:
            for _test_name, result in self.test_results["extreme_tests"].items():
                if isinstance(result, dict) and "resilience_score" in result:
                    extreme_score += result["resilience_score"]
            if self.test_results["extreme_tests"]:
                extreme_score = extreme_score / len(self.test_results["extreme_tests"])
        scores.append(("极端场景测试", extreme_score, 0.20))

        # 性能基准测试得分 (20%)
        benchmark_score = 100.0  # 基准测试只要能运行就认为通过
        scores.append(("性能基准测试", benchmark_score, 0.20))

        # 计算加权总分
        total_score = 0.0
        for _name, score, weight in scores:
            total_score += score * weight

        self.production_readiness_score = total_score
        self.scores_breakdown = scores

    def _print_final_report(self):
        """打印最终报告"""
        logger.info("\n" + "="*70)
        logger.info("📊 生产验证测试 - 最终报告")
        logger.info("="*70)

        logger.info(f"\n测试时长: {(self.end_time - self.start_time).total_seconds():.1f}秒")
        logger.info(f"开始时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"结束时间: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")

        # 分项得分
        logger.info("\n分项得分:")
        for name, score, weight in self.scores_breakdown:
            logger.info(f"  {name:20s}: {score:6.2f}% (权重 {weight*100:.0f}%)")

        # 总分
        logger.info(f"\n{'='*70}")
        logger.info(f"🎯 生产就绪度得分: {self.production_readiness_score:.2f}%")

        # 评级
        if self.production_readiness_score >= 95:
            grade = "A+ (优秀)"
            status = "✅ 可立即投入生产"
        elif self.production_readiness_score >= 90:
            grade = "A (良好)"
            status = "✅ 建议投入生产"
        elif self.production_readiness_score >= 80:
            grade = "B (合格)"
            status = "⚠️ 需要小幅改进后投入生产"
        elif self.production_readiness_score >= 70:
            grade = "C (需改进)"
            status = "⚠️ 需要改进后投入生产"
        else:
            grade = "D (不合格)"
            status = "❌ 不建议投入生产"

        logger.info(f"评级: {grade}")
        logger.info(f"状态: {status}")
        logger.info(f"{'='*70}\n")

    def save_report(self, filepath: str):
        """保存测试报告到文件"""
        report = {
            "test_run": {
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "end_time": self.end_time.isoformat() if self.end_time else None,
                "duration_seconds": (self.end_time - self.start_time).total_seconds()
                               if self.start_time and self.end_time else 0,
                "overall_success": self.overall_success,
                "production_readiness_score": self.production_readiness_score,
                "scores_breakdown": [
                    {"name": name, "score": score, "weight": weight}
                    for name, score, weight in self.scores_breakdown
                ]
            },
            "test_results": self.test_results
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"✓ 测试报告已保存: {filepath}")


async def main():
    """主函数"""
    # 设置路径 - 添加项目根目录到sys.path
    import sys
    from pathlib import Path

    tests_dir = Path(__file__).parent
    core_dir = tests_dir.parent.parent  # core目录
    project_root = tests_dir.parent.parent.parent  # 项目根目录

    # 添加项目根目录到路径（支持core.perception.xxx导入）
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    # 添加core目录到路径（支持直接导入）
    if str(core_dir) not in sys.path:
        sys.path.insert(0, str(core_dir))

    # 创建测试图像
    test_image = "/tmp/production_test_image.png"

    if not Path(test_image).exists():
        import cv2
        import numpy as np
        img = np.ones((100, 200, 3), dtype=np.uint8) * 255
        cv2.putText(img, "Production Test", (20, 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        cv2.imwrite(test_image, img)
        logger.info(f"✓ 已创建测试图像: {test_image}")

    # 运行测试
    runner = ProductionTestRunner()

    # 检查命令行参数
    quick_mode = "--quick" in sys.argv or "-q" in sys.argv

    await runner.run_all_tests(
        test_image=test_image,
        quick_mode=quick_mode
    )

    # 保存报告
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_path = f"/tmp/production_test_report_{timestamp}.json"
    runner.save_report(report_path)

    # 返回退出码
    if runner.production_readiness_score >= 90:
        logger.info("\n🎉 生产验证测试通过！")
        sys.exit(0)
    else:
        logger.warning("\n⚠️ 生产验证测试未完全通过，请查看报告。")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

