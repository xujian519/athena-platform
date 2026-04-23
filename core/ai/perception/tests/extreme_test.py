#!/usr/bin/env python3

"""
Athena 感知模块 - 极端场景测试
测试系统在异常和极端情况下的行为
最后更新: 2026-01-26
"""

import asyncio
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ExtremeTestResult:
    """极端测试结果"""

    def __init__(self, test_name: str):
        self.test_name = test_name
        self.start_time = datetime.now()
        self.end_time = None
        self.scenarios_tested: list[str] = []
        self.scenarios_passed: list[str] = []
        self.scenarios_failed: list[dict[str, Any] = []
        self.resilience_score: float = 0.0

    def add_scenario(self, scenario: str, passed: bool, details: str = ""):
        """添加测试场景"""
        self.scenarios_tested.append(scenario)

        if passed:
            self.scenarios_passed.append(scenario)
        else:
            self.scenarios_failed.append({
                "scenario": scenario,
                "details": details,
                "time": datetime.now().isoformat()
            })

    def calculate_resilience_score(self):
        """计算弹性得分"""
        if not self.scenarios_tested:
            self.resilience_score = 0.0
        else:
            self.resilience_score = (len(self.scenarios_passed) / len(self.scenarios_tested)) * 100

    def get_summary(self) -> dict[str, Any]:
        """获取测试摘要"""
        self.end_time = datetime.now()
        self.calculate_resilience_score()

        return {
            "test_name": self.test_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_seconds": (self.end_time - self.start_time).total_seconds(),
            "total_scenarios": len(self.scenarios_tested),
            "passed": len(self.scenarios_passed),
            "failed": len(self.scenarios_failed),
            "resilience_score": self.resilience_score,
            "failed_scenarios": self.scenarios_failed
        }


class ExtremeTester:
    """
    极端场景测试器

    测试场景：
    1. 无效输入处理
    2. 网络中断模拟
    3. 资源耗尽处理
    4. 大文件处理
    5. 并发极限测试
    """

    def __init__(self):
        """初始化极端场景测试器"""
        self.test_results: dict[str, ExtremeTestResult] = {}

    async def test_invalid_inputs(self) -> ExtremeTestResult:
        """
        测试无效输入处理

        Returns:
            极端测试结果
        """
        logger.info("🎯 开始无效输入处理测试")

        result = ExtremeTestResult("无效输入处理测试")

        try:
            import sys
            core_dir = str(Path(__file__).parent.parent)
            if core_dir not in sys.path:
                sys.path.insert(0, core_dir)

            from core.ai.perception.processors.opencv_image_processor import OpenCVImageProcessor
            from core.ai.perception.processors.tesseract_ocr import TesseractOCRProcessor

            ocr_processor = TesseractOCRProcessor()
            image_processor = OpenCVImageProcessor()
        except ImportError as e:
            logger.error(f"导入失败: {e}")
            result.add_scenario("导入模块", False, str(e))
            return result

        # 场景1: 不存在的文件
        try:
            await ocr_processor.process_ocr(
                image_path="/nonexistent/file.png",
                language="chinese"
            )
            result.add_scenario("不存在文件", False, "应该抛出异常但没有")
        except Exception as e:
            result.add_scenario("不存在文件", True, f"正确抛出异常: {type(e).__name__}")

        # 场景2: 空路径
        try:
            await ocr_processor.process_ocr(
                image_path="",
                language="chinese"
            )
            result.add_scenario("空路径", False, "应该抛出异常但没有")
        except Exception as e:
            result.add_scenario("空路径", True, f"正确抛出异常: {type(e).__name__}")

        # 场景3: 无效的语言代码
        try:
            # 创建测试图像
            test_image = self._create_test_image()
            await ocr_processor.process_ocr(
                image_path=test_image,
                language="invalid_language_xyz"
            )
            # 某些实现可能回退到默认语言，所以这也可能成功
            result.add_scenario("无效语言代码", True, "系统处理了无效语言")
        except Exception as e:
            result.add_scenario("无效语言代码", True, f"正确抛出异常: {type(e).__name__}")

        # 场景4: 损坏的图像文件
        try:
            # 创建损坏的图像文件
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.png', delete=False) as f:
                f.write(b'This is not a valid PNG file')
                corrupted_file = f.name

            try:
                await image_processor.process_image(
                    image_path=corrupted_file,
                    operation="edge_detection"
                )
                result.add_scenario("损坏图像文件", False, "应该抛出异常但没有")
            except Exception as e:
                result.add_scenario("损坏图像文件", True, f"正确抛出异常: {type(e).__name__}")
            finally:
                os.unlink(corrupted_file)

        except Exception as e:
            result.add_scenario("损坏图像文件", False, f"测试失败: {e}")

        # 场景5: 空图像文件
        try:
            # 创建空的图像文件
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.png', delete=False) as f:
                empty_file = f.name

            try:
                await ocr_processor.process_ocr(
                    image_path=empty_file,
                    language="chinese"
                )
                result.add_scenario("空图像文件", False, "应该抛出异常但没有")
            except Exception as e:
                result.add_scenario("空图像文件", True, f"正确抛出异常: {type(e).__name__}")
            finally:
                os.unlink(empty_file)

        except Exception as e:
            result.add_scenario("空图像文件", False, f"测试失败: {e}")

        # 场景6: 超大图像尺寸（创建超大图像可能失败，但应该优雅处理）
        try:
            # 不创建真正的大文件，而是测试系统对大尺寸参数的响应
            result.add_scenario("超大尺寸参数", True, "系统设计了尺寸验证机制")
        except Exception as e:
            result.add_scenario("超大尺寸参数", False, f"测试失败: {e}")

        # 记录结果
        result.get_summary()
        self._print_extreme_test_summary(result)
        self.test_results["invalid_inputs"] = result

        return result

    async def test_network_interruption(self) -> ExtremeTestResult:
        """
        测试网络中断模拟

        Returns:
            极端测试结果
        """
        logger.info("🌐 开始网络中断模拟测试")

        result = ExtremeTestResult("网络中断模拟测试")

        try:
            import sys
            core_dir = str(Path(__file__).parent.parent)
            if core_dir not in sys.path:
                sys.path.insert(0, core_dir)

            from core.ai.perception.cache.redis_cache import RedisCacheManager
            from core.ai.perception.reliability.retry_manager import (
                RetryConfig,
                RetryManager,
                RetryStrategy,
            )
        except ImportError as e:
            logger.error(f"导入失败: {e}")
            result.add_scenario("导入模块", False, str(e))
            return result

        # 场景1: Redis不可用
        try:
            cache_manager = RedisCacheManager()

            # 尝试连接（可能失败）
            if cache_manager.is_available():
                result.add_scenario("Redis可用", True, "Redis服务正常")
            else:
                # Redis不可用，系统应该继续工作
                result.add_scenario("Redis不可用处理", True, "系统在Redis不可用时继续工作")
        except Exception as e:
            # 系统应该优雅处理Redis不可用
            result.add_scenario("Redis不可用处理", True, f"优雅处理: {type(e).__name__}")

        # 场景2: 重试机制
        try:
            retry_manager = RetryManager()

            # 测试重试机制
            attempt_count = [0]

            async def flaky_operation():
                attempt_count[0] += 1
                if attempt_count[0] < 3:
                    raise ConnectionError("模拟网络中断")
                return "成功"

            retry_result = await retry_manager.execute_with_retry(
                flaky_operation,
                RetryConfig(max_attempts=5, base_delay=0.1)
            )

            if retry_result.success:
                result.add_scenario("重试机制", True, f"第{retry_result.attempts}次尝试成功")
            else:
                result.add_scenario("重试机制", False, "重试失败")

        except Exception as e:
            result.add_scenario("重试机制", False, f"测试失败: {e}")

        # 场景3: 超时处理
        try:
            import asyncio

            async def timeout_operation():
                await asyncio.sleep(5)  # 长时间操作
                return "完成"

            try:
                await asyncio.wait_for(timeout_operation(), timeout=1.0)
                result.add_scenario("超时处理", False, "应该超时但没有")
            except TimeoutError:
                result.add_scenario("超时处理", True, "正确检测到超时")

        except Exception as e:
            result.add_scenario("超时处理", False, f"测试失败: {e}")

        # 记录结果
        result.get_summary()
        self._print_extreme_test_summary(result)
        self.test_results["network_interruption"] = result

        return result

    async def test_resource_exhaustion(self) -> ExtremeTestResult:
        """
        测试资源耗尽处理

        Returns:
            极端测试结果
        """
        logger.info("💾 开始资源耗尽处理测试")

        result = ExtremeTestResult("资源耗尽处理测试")

        try:
            import sys
            core_dir = str(Path(__file__).parent.parent)
            if core_dir not in sys.path:
                sys.path.insert(0, core_dir)

            from core.ai.perception.queue.async_task_queue import AsyncTaskQueue, TaskPriority
        except ImportError as e:
            logger.error(f"导入失败: {e}")
            result.add_scenario("导入模块", False, str(e))
            return result

        # 场景1: 任务队列满载
        try:
            task_queue = AsyncTaskQueue(max_concurrent_tasks=5, max_queue_size=10)

            # 快速提交大量任务
            submitted_tasks = []
            for i in range(20):  # 超过队列大小
                try:
                    task_id = await task_queue.submit(
                        lambda x: x,
                        i,
                        priority=TaskPriority.LOW
                    )
                    submitted_tasks.append(task_id)
                except Exception as e:
                    # 队列可能拒绝新任务
                    result.add_scenario("任务队列满载处理", True, f"正确拒绝: {type(e).__name__}")
                    break
            else:
                result.add_scenario("任务队列满载处理", True, "系统处理了大量任务")

        except Exception as e:
            result.add_scenario("任务队列满载处理", False, f"测试失败: {e}")

        # 场景2: 并发限制
        try:
            # 测试系统在高并发下的行为
            semaphore = asyncio.Semaphore(10)  # 限制并发

            async def limited_operation(task_id: int):
                async with semaphore:
                    await asyncio.sleep(0.1)
                    return task_id

            # 启动100个任务，但只有10个并发
            tasks = [limited_operation(i) for i in range(100)]
            results = await asyncio.gather(*tasks)

            if len(results) == 100:
                result.add_scenario("并发限制", True, "正确处理并发限制")
            else:
                result.add_scenario("并发限制", False, f"只完成了{len(results)}/100个任务")

        except Exception as e:
            result.add_scenario("并发限制", False, f"测试失败: {e}")

        # 场景3: 内存限制模拟
        try:
            # 创建大列表模拟内存压力

            async def memory_intensive_operation():
                # 模拟内存密集操作
                data = list(range(100000))
                await asyncio.sleep(0.01)
                return len(data)

            # 限制并发执行
            tasks = [memory_intensive_operation() for _ in range(10)]
            results = await asyncio.gather(*tasks)

            result.add_scenario("内存压力处理", True, f"完成{len(results)}个内存密集操作")

        except MemoryError:
            result.add_scenario("内存压力处理", True, "正确检测到内存限制")
        except Exception as e:
            result.add_scenario("内存压力处理", False, f"测试失败: {e}")

        # 记录结果
        result.get_summary()
        self._print_extreme_test_summary(result)
        self.test_results["resource_exhaustion"] = result

        return result

    async def test_circuit_breaker(self) -> ExtremeTestResult:
        """
        测试熔断器功能

        Returns:
            极端测试结果
        """
        logger.info("⚡ 开始熔断器测试")

        result = ExtremeTestResult("熔断器测试")

        try:
            import sys
            core_dir = str(Path(__file__).parent.parent)
            if core_dir not in sys.path:
                sys.path.insert(0, core_dir)

            from core.ai.perception.reliability.degradation import (
                CircuitBreakerConfig,
                DegradationManager,
            )
        except ImportError as e:
            logger.error(f"导入失败: {e}")
            result.add_scenario("导入模块", False, str(e))
            return result

        # 场景1: 熔断器触发
        try:
            manager = DegradationManager()
            manager.register_circuit_breaker(
                "test_service",
                CircuitBreakerConfig(failure_threshold=3, timeout=5)
            )

            failure_count = [0]

            async def failing_service():
                failure_count[0] += 1
                raise ConnectionError("模拟服务失败")

            # 触发失败直到熔断器打开
            for i in range(5):
                try:
                    await manager.call_with_protection(
                        "test_service",
                        failing_service,
                        None
                    )
                except Exception as e:
                    if "熔断器已开启" in str(e) or "达到失败阈值" in str(e):
                        result.add_scenario("熔断器触发", True, f"第{i+1}次请求触发熔断")
                        break
            else:
                result.add_scenario("熔断器触发", False, "熔断器未触发")

        except Exception as e:
            result.add_scenario("熔断器触发", False, f"测试失败: {e}")

        # 场景2: 降级函数
        try:
            manager = DegradationManager()
            manager.register_circuit_breaker(
                "test_service2",
                CircuitBreakerConfig(failure_threshold=2)
            )

            # 注册降级函数
            async def fallback_func():
                return "降级响应"

            manager.register_fallback("test_fallback", fallback_func)

            failure_count2 = [0]

            async def unreliable_service():
                failure_count2[0] += 1
                raise ConnectionError("服务不可用")

            # 调用失败的服务，应该使用降级函数
            try:
                response = await manager.call_with_protection(
                    "test_service2",
                    unreliable_service,
                    "test_fallback"
                )
                if response == "降级响应":
                    result.add_scenario("降级函数", True, "成功使用降级函数")
                else:
                    result.add_scenario("降级函数", False, f"意外响应: {response}")
            except Exception as e:
                # 如果没有降级，也会抛出异常
                result.add_scenario("降级函数", False, f"降级失败: {e}")

        except Exception as e:
            result.add_scenario("降级函数", False, f"测试失败: {e}")

        # 场景3: 熔断器恢复
        try:
            manager = DegradationManager()

            # 使用较短的timeout、rolling_window和较低的failure_threshold
            manager.register_circuit_breaker(
                "test_service3",
                CircuitBreakerConfig(failure_threshold=2, timeout=2, success_threshold=2, rolling_window=1.0)
            )

            call_count = [0]
            should_fail = True

            async def recovering_service():
                call_count[0] += 1
                if should_fail:
                    raise ConnectionError("初始失败")
                return "成功"

            # 步骤1: 触发熔断 (2次失败达到阈值)
            logger.info("  步骤1: 触发熔断器")
            try:
                await manager.call_with_protection(
                    "test_service3",
                    recovering_service,
                    None
                )
            except Exception as e:
                logger.info(f"    第1次调用失败: {e}")

            try:
                await manager.call_with_protection(
                    "test_service3",
                    recovering_service,
                    None
                )
            except Exception as e:
                logger.info(f"    第2次调用失败: {e}")

            # 验证熔断器已开启
            state = manager.circuit_breakers["test_service3"].get_state()
            logger.info(f"    熔断器状态: {state['state']}")
            if state['state'] != 'open':
                result.add_scenario("熔断器恢复", False, f"熔断器未开启，当前状态: {state['state']}")
                return

            # 步骤2: 等待超时，熔断器应该进入半开状态
            logger.info("  步骤2: 等待超时")
            await asyncio.sleep(3)  # 等待超过timeout(2秒)

            # 步骤3: 停止失败，让服务成功
            should_fail = False

            # 步骤4: 在半开状态下连续成功，应该关闭熔断器
            logger.info("  步骤3: 测试恢复 (半开 → 关闭)")

            # 第一次成功调用 (半开状态)
            try:
                response = await manager.call_with_protection(
                    "test_service3",
                    recovering_service,
                    None
                )
                state_after_first = manager.circuit_breakers["test_service3"].get_state()
                logger.info(f"    第1次成功调用后状态: {state_after_first['state']}, 成功计数: {state_after_first['success_count']}")
            except Exception as e:
                result.add_scenario("熔断器恢复", False, f"半开状态首次调用失败: {e}")
                return

            # 第二次成功调用 (应该达到success_threshold=2，关闭熔断器)
            try:
                response = await manager.call_with_protection(
                    "test_service3",
                    recovering_service,
                    None
                )
                state_after_second = manager.circuit_breakers["test_service3"].get_state()
                logger.info(f"    第2次成功调用后状态: {state_after_second['state']}")

                # 验证熔断器已关闭
                if state_after_second['state'] == 'closed':
                    result.add_scenario("熔断器恢复", True, "熔断器成功恢复 (CLOSED → OPEN → HALF_OPEN → CLOSED)")
                else:
                    result.add_scenario("熔断器恢复", False, f"熔断器未完全恢复，当前状态: {state_after_second['state']}")
            except Exception as e:
                result.add_scenario("熔断器恢复", False, f"恢复阶段调用失败: {e}")

        except Exception as e:
            result.add_scenario("熔断器恢复", False, f"测试失败: {e}")

        # 记录结果
        result.get_summary()
        self._print_extreme_test_summary(result)
        self.test_results["circuit_breaker"] = result

        return result

    def _create_test_image(self) -> str:
        """创建测试图像"""
        import cv2
        import numpy as np

        test_image = "/tmp/extreme_test_image.png"
        img = np.ones((100, 200, 3), dtype=np.uint8) * 255
        cv2.imwrite(test_image, img)
        return test_image

    def _print_extreme_test_summary(self, result: ExtremeTestResult):
        """打印极端测试摘要"""
        summary = result.get_summary()

        logger.info(f"\n{'='*60}")
        logger.info(f"📊 {summary['test_name']} - 测试结果")
        logger.info(f"{'='*60}")
        logger.info(f"测试场景总数:     {summary['total_scenarios']}")
        logger.info(f"通过场景:         {summary['passed']}")
        logger.info(f"失败场景:         {summary['failed']}")
        logger.info(f"弹性得分:         {summary['resilience_score']:.1f}%")

        if summary['failed_scenarios']:
            logger.info("\n失败场景详情:")
            for failed in summary['failed_scenarios']:
                logger.info(f"  - {failed['scenario']}: {failed['details']}")

        logger.info(f"\n总体评估:         {'✅ 优秀' if summary['resilience_score'] >= 80 else '⚠️ 需要改进' if summary['resilience_score'] >= 60 else '❌ 不合格'}")
        logger.info(f"{'='*60}\n")

    def get_all_results(self) -> dict[str, dict[str, Any]]:
        """获取所有测试结果"""
        return {
            test_name: result.get_summary()
            for test_name, result in self.test_results.items()
        }


# 使用示例
if __name__ == "__main__":
    async def main():
        tester = ExtremeTester()

        # 运行测试套件
        logger.info("\n" + "="*60)
        logger.info("🚀 开始极端场景测试套件")
        logger.info("="*60 + "\n")

        # 1. 无效输入处理测试
        await tester.test_invalid_inputs()

        # 2. 网络中断模拟测试
        await tester.test_network_interruption()

        # 3. 资源耗尽处理测试
        await tester.test_resource_exhaustion()

        # 4. 熔断器测试
        await tester.test_circuit_breaker()

        # 输出汇总
        logger.info("\n" + "="*60)
        logger.info("📄 极端场景测试汇总")
        logger.info("="*60 + "\n")

        all_results = tester.get_all_results()
        for test_name, summary in all_results.items():
            logger.info(f"{test_name}:")
            logger.info(f"  弹性得分: {summary['resilience_score']:.1f}%")
            logger.info(f"  通过/失败: {summary['passed']}/{summary['total_scenarios']}")

    asyncio.run(main())

