#!/usr/bin/env python3
"""
Athena 感知模块 - 负载测试
测试系统在高并发情况下的性能表现
最后更新: 2026-01-26
"""

from __future__ import annotations
import asyncio
import logging
import statistics
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LoadTestResult:
    """负载测试结果"""

    def __init__(self):
        self.success_count = 0
        self.failure_count = 0
        self.total_requests = 0
        self.response_times: list[float] = []
        self.errors: list[dict[str, Any]] = []
        self.start_time = None
        self.end_time = None

    def add_success(self, response_time: float):
        """添加成功请求"""
        self.success_count += 1
        self.total_requests += 1
        self.response_times.append(response_time)

    def add_failure(self, error: Exception, response_time: float = 0):
        """添加失败请求"""
        self.failure_count += 1
        self.total_requests += 1
        if response_time > 0:
            self.response_times.append(response_time)
        self.errors.append({
            "error": str(error),
            "type": type(error).__name__,
            "time": datetime.now().isoformat()
        })

    def get_statistics(self) -> dict[str, Any]:
        """获取统计数据"""
        if not self.response_times:
            return {
                "success_rate": 0,
                "avg_response_time": 0,
                "min_response_time": 0,
                "max_response_time": 0,
                "p50_response_time": 0,
                "p95_response_time": 0,
                "p99_response_time": 0,
                "requests_per_second": 0,
                "total_errors": len(self.errors)
            }

        duration = (self.end_time - self.start_time).total_seconds() if self.end_time and self.start_time else 1

        sorted_times = sorted(self.response_times)
        return {
            "total_requests": self.total_requests,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": (self.success_count / self.total_requests * 100) if self.total_requests > 0 else 0,
            "avg_response_time": statistics.mean(self.response_times),
            "min_response_time": min(self.response_times),
            "max_response_time": max(self.response_times),
            "p50_response_time": sorted_times[len(sorted_times) // 2],
            "p95_response_time": sorted_times[int(len(sorted_times) * 0.95)] if len(sorted_times) >= 20 else max(sorted_times),
            "p99_response_time": sorted_times[int(len(sorted_times) * 0.99)] if len(sorted_times) >= 100 else max(sorted_times),
            "requests_per_second": self.total_requests / duration,
            "duration_seconds": duration,
            "total_errors": len(self.errors),
            "error_types": self._get_error_types()
        }

    def _get_error_types(self) -> dict[str, int]:
        """获取错误类型统计"""
        error_types = {}
        for error in self.errors:
            error_type = error["type"]
            error_types[error_type] = error_types.get(error_type, 0) + 1
        return error_types


class LoadTester:
    """
    负载测试器

    测试场景：
    1. 并发OCR处理
    2. 批量图像处理
    3. 缓存性能
    4. 任务队列吞吐量
    """

    def __init__(self):
        """初始化负载测试器"""
        self.test_results: dict[str, LoadTestResult] = {}

    async def test_concurrent_ocr(
        self,
        image_path: str,
        concurrent_users: int = 10,
        total_requests: int = 100,
        use_cache: bool = True
    ) -> LoadTestResult:
        """
        测试并发OCR处理

        Args:
            image_path: 测试图像路径
            concurrent_users: 并发用户数
            total_requests: 总请求数
            use_cache: 是否使用缓存

        Returns:
            负载测试结果
        """
        logger.info(f"🔥 开始并发OCR测试: {concurrent_users}并发用户, {total_requests}总请求")

        # 导入OCR处理器
        try:
            import sys
            # 添加感知模块目录到路径
            str(Path(__file__).parent.parent)
            core_dir = str(Path(__file__).parent.parent.parent)
            if core_dir not in sys.path:
                sys.path.insert(0, core_dir)

            # 使用绝对导入
            from core.perception.cache.redis_cache import RedisCacheManager
            from core.perception.processors.tesseract_ocr import TesseractOCRProcessor

            ocr_processor = TesseractOCRProcessor()
            cache_manager = RedisCacheManager() if use_cache else None
        except Exception as e:
            logger.error(f"导入失败: {e}")
            logger.error(f"sys.path: {sys.path[:3]}")
            result = LoadTestResult()
            result.add_failure(e)
            return result

        result = LoadTestResult()
        result.start_time = datetime.now()

        # 创建信号量限制并发数
        semaphore = asyncio.Semaphore(concurrent_users)

        async def process_ocr_with_cache(request_id: int) -> float:
            """处理单个OCR请求"""
            start_time = time.time()

            try:
                async with semaphore:
                    # 检查缓存
                    if cache_manager and cache_manager.is_available():
                        cached = await cache_manager.get_ocr_result(
                            image_path,
                            language="chinese",
                            preprocess=True
                        )
                        if cached:
                            response_time = time.time() - start_time
                            result.add_success(response_time)
                            return response_time

                    # 执行OCR
                    await ocr_processor.process_ocr(
                        image_path=image_path,
                        language="chinese",
                        preprocess=True
                    )

                    response_time = time.time() - start_time
                    result.add_success(response_time)

                    return response_time

            except Exception as e:
                response_time = time.time() - start_time
                result.add_failure(e, response_time)
                logger.error(f"请求{request_id}失败: {e}")
                return response_time

        # 创建任务
        tasks = [
            process_ocr_with_cache(i)
            for i in range(total_requests)
        ]

        # 并发执行
        await asyncio.gather(*tasks)

        result.end_time = datetime.now()

        # 记录结果
        test_name = f"concurrent_ocr_{concurrent_users}users_{total_requests}requests"
        self.test_results[test_name] = result

        # 输出统计
        stats = result.get_statistics()
        self._print_statistics(f"并发OCR测试 ({concurrent_users}并发)", stats)

        return result

    async def test_cache_performance(
        self,
        image_path: str,
        iterations: int = 100
    ) -> LoadTestResult:
        """
        测试缓存性能

        Args:
            image_path: 测试图像路径
            iterations: 测试迭代次数

        Returns:
            负载测试结果
        """
        logger.info(f"💾 开始缓存性能测试: {iterations}次迭代")

        try:
            import sys
            core_dir = str(Path(__file__).parent.parent)
            if core_dir not in sys.path:
                sys.path.insert(0, core_dir)

            from core.perception.cache.redis_cache import RedisCacheManager
            from core.perception.processors.tesseract_ocr import TesseractOCRProcessor

            ocr_processor = TesseractOCRProcessor()
            cache_manager = RedisCacheManager()
        except ImportError as e:
            logger.error(f"导入失败: {e}")
            result = LoadTestResult()
            result.add_failure(e)
            return result

        result = LoadTestResult()
        result.start_time = datetime.now()

        # 第一次请求（缓存未命中）
        try:
            await ocr_processor.process_ocr(
                image_path=image_path,
                language="chinese",
                preprocess=True
            )
            await cache_manager.set_ocr_result(
                image_path,
                "chinese",
                True,
                {"text": "test", "confidence": 0.95}
            )
        except Exception as e:
            logger.warning(f"首次请求失败: {e}")

        # 后续请求（测试缓存命中）
        async def test_cache_hit(iteration: int) -> float:
            """测试缓存命中"""
            start_time = time.time()

            try:
                cached = await cache_manager.get_ocr_result(
                    image_path,
                    language="chinese",
                    preprocess=True
                )

                response_time = time.time() - start_time

                if cached:
                    result.add_success(response_time)
                else:
                    result.add_failure(Exception("缓存未命中"), response_time)

                return response_time

            except Exception as e:
                response_time = time.time() - start_time
                result.add_failure(e, response_time)
                return response_time

        tasks = [test_cache_hit(i) for i in range(iterations)]
        await asyncio.gather(*tasks)

        result.end_time = datetime.now()

        # 记录结果
        test_name = f"cache_performance_{iterations}iterations"
        self.test_results[test_name] = result

        # 输出统计
        stats = result.get_statistics()
        self._print_statistics("缓存性能测试", stats)

        return result

    async def test_task_queue_throughput(
        self,
        num_tasks: int = 50,
        concurrent_workers: int = 10
    ) -> LoadTestResult:
        """
        测试任务队列吞吐量

        Args:
            num_tasks: 任务数量
            concurrent_workers: 并发工作线程数

        Returns:
            负载测试结果
        """
        logger.info(f"📋 开始任务队列吞吐量测试: {num_tasks}任务, {concurrent_workers}工作线程")

        try:
            import sys
            core_dir = str(Path(__file__).parent.parent)
            if core_dir not in sys.path:
                sys.path.insert(0, core_dir)

            from core.perception.queue.async_task_queue import AsyncTaskQueue, TaskPriority
        except ImportError as e:
            logger.error(f"导入失败: {e}")
            result = LoadTestResult()
            result.add_failure(e)
            return result

        result = LoadTestResult()
        result.start_time = datetime.now()

        task_queue = AsyncTaskQueue(max_workers=concurrent_workers)

        # 模拟任务
        async def mock_task(task_id: int, duration: float = 0.1) -> str:
            """模拟任务"""
            await asyncio.sleep(duration)
            return f"task-{task_id}"

        # 提交任务
        async def submit_and_wait(task_id: int) -> float:
            """提交并等待任务完成"""
            start_time = time.time()

            try:
                # 提交任务
                queue_task_id = await task_queue.submit(
                    mock_task,
                    task_id,
                    0.1,  # 100ms处理时间
                    priority=TaskPriority.NORMAL
                )

                # 等待完成
                await task_queue.get_task_result(queue_task_id, timeout=30)

                response_time = time.time() - start_time
                result.add_success(response_time)
                return response_time

            except Exception as e:
                response_time = time.time() - start_time
                result.add_failure(e, response_time)
                return response_time

        tasks = [submit_and_wait(i) for i in range(num_tasks)]
        await asyncio.gather(*tasks)

        result.end_time = datetime.now()

        # 记录结果
        test_name = f"task_queue_{num_tasks}tasks_{concurrent_workers}workers"
        self.test_results[test_name] = result

        # 输出统计
        stats = result.get_statistics()
        self._print_statistics("任务队列吞吐量测试", stats)

        return result

    async def test_sustained_load(
        self,
        image_path: str,
        duration_seconds: int = 60,
        requests_per_second: int = 10
    ) -> LoadTestResult:
        """
        测试持续负载

        Args:
            image_path: 测试图像路径
            duration_seconds: 测试持续时间（秒）
            requests_per_second: 每秒请求数

        Returns:
            负载测试结果
        """
        logger.info(f"⏱️ 开始持续负载测试: {duration_seconds}秒, {requests_per_second}QPS")

        try:
            import sys
            core_dir = str(Path(__file__).parent.parent)
            if core_dir not in sys.path:
                sys.path.insert(0, core_dir)

            from core.perception.processors.tesseract_ocr import TesseractOCRProcessor

            ocr_processor = TesseractOCRProcessor()
        except ImportError as e:
            logger.error(f"导入失败: {e}")
            result = LoadTestResult()
            result.add_failure(e)
            return result

        result = LoadTestResult()
        result.start_time = datetime.now()
        end_time = datetime.now() + timedelta(seconds=duration_seconds)

        request_count = 0

        while datetime.now() < end_time:
            batch_start = time.time()

            # 创建一批请求
            batch_size = min(requests_per_second, 10)  # 每批最多10个
            tasks = []

            for _ in range(batch_size):
                async def process_request(req_id: int):
                    start = time.time()
                    try:
                        await ocr_processor.process_ocr(
                            image_path=image_path,
                            language="chinese",
                            preprocess=False  # 加快速度
                        )
                        response_time = time.time() - start
                        result.add_success(response_time)
                    except Exception as e:
                        response_time = time.time() - start
                        result.add_failure(e, response_time)

                tasks.append(process_request(request_count))
                request_count += 1

            # 执行批次
            await asyncio.gather(*tasks)

            # 控制速率
            batch_duration = time.time() - batch_start
            target_duration = 1.0 / (requests_per_second / batch_size)
            if batch_duration < target_duration:
                await asyncio.sleep(target_duration - batch_duration)

        result.end_time = datetime.now()

        # 记录结果
        test_name = f"sustained_load_{duration_seconds}s_{requests_per_second}qps"
        self.test_results[test_name] = result

        # 输出统计
        stats = result.get_statistics()
        self._print_statistics("持续负载测试", stats)

        return result

    def _print_statistics(self, test_name: str, stats: dict[str, Any]):
        """打印统计数据"""
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 {test_name} - 测试结果")
        logger.info(f"{'='*60}")
        logger.info(f"总请求数:         {stats.get('total_requests', 0)}")
        logger.info(f"成功请求:         {stats.get('success_count', 0)}")
        logger.info(f"失败请求:         {stats.get('failure_count', 0)}")
        logger.info(f"成功率:           {stats.get('success_rate', 0):.2f}%")
        logger.info(f"平均响应时间:     {stats.get('avg_response_time', 0)*1000:.2f}ms")
        logger.info(f"最小响应时间:     {stats.get('min_response_time', 0)*1000:.2f}ms")
        logger.info(f"最大响应时间:     {stats.get('max_response_time', 0)*1000:.2f}ms")
        logger.info(f"P50响应时间:      {stats.get('p50_response_time', 0)*1000:.2f}ms")
        logger.info(f"P95响应时间:      {stats.get('p95_response_time', 0)*1000:.2f}ms")
        logger.info(f"P99响应时间:      {stats.get('p99_response_time', 0)*1000:.2f}ms")
        logger.info(f"吞吐量:           {stats.get('requests_per_second', 0):.2f} req/s")
        logger.info(f"测试时长:         {stats.get('duration_seconds', 0):.2f}秒")

        if stats.get('total_errors', 0) > 0:
            logger.info("错误统计:")
            for error_type, count in stats.get('error_types', {}).items():
                logger.info(f"  - {error_type}: {count}")

        logger.info(f"{'='*60}\n")

    def get_all_results(self) -> dict[str, dict[str, Any]]:
        """获取所有测试结果"""
        return {
            test_name: result.get_statistics()
            for test_name, result in self.test_results.items()
        }

    def generate_report(self) -> str:
        """生成测试报告"""
        report = []
        report.append("# 负载测试报告")
        report.append(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        for test_name, result in self.test_results.items():
            stats = result.get_statistics()
            report.append(f"## {test_name}")
            report.append(f"- 总请求数: {stats.get('total_requests', 0)}")
            report.append(f"- 成功率: {stats.get('success_rate', 0):.2f}%")
            report.append(f"- 平均响应时间: {stats.get('avg_response_time', 0)*1000:.2f}ms")
            report.append(f"- P95响应时间: {stats.get('p95_response_time', 0)*1000:.2f}ms")
            report.append(f"- 吞吐量: {stats.get('requests_per_second', 0):.2f} req/s\n")

        return "\n".join(report)


# 使用示例
if __name__ == "__main__":

    async def main():
        tester = LoadTester()

        # 测试图像路径（需要提供一个真实图像）
        test_image = "/tmp/test_image.png"

        # 如果测试图像不存在，创建一个简单的测试图像
        from pathlib import Path
        if not Path(test_image).exists():
            import cv2
            import numpy as np
            # 创建白色测试图像
            img = np.ones((100, 200, 3), dtype=np.uint8) * 255
            cv2.imwrite(test_image, img)
            logger.info(f"✓ 已创建测试图像: {test_image}")

        # 运行测试套件
        logger.info("\n" + "="*60)
        logger.info("🚀 开始负载测试套件")
        logger.info("="*60 + "\n")

        # 1. 并发OCR测试
        await tester.test_concurrent_ocr(
            image_path=test_image,
            concurrent_users=10,
            total_requests=50,
            use_cache=True
        )

        # 2. 缓存性能测试
        await tester.test_cache_performance(
            image_path=test_image,
            iterations=100
        )

        # 3. 任务队列吞吐量测试
        await tester.test_task_queue_throughput(
            num_tasks=50,
            concurrent_workers=10
        )

        # 4. 持续负载测试（可选，时间较长）
        # await tester.test_sustained_load(
        #     image_path=test_image,
        #     duration_seconds=30,
        #     requests_per_second=5
        # )

        # 生成报告
        logger.info("\n" + "="*60)
        logger.info("📄 负载测试报告")
        logger.info("="*60 + "\n")
        print(tester.generate_report())

    asyncio.run(main())
