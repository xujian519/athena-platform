#!/usr/bin/env python3
from __future__ import annotations
"""
Athena 感知模块 - 性能基准测试
建立性能基线，对比不同配置的性能表现
最后更新: 2026-01-26
"""

import asyncio
import json
import logging
import statistics
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BenchmarkResult:
    """性能基准测试结果"""

    def __init__(self, benchmark_name: str):
        self.benchmark_name = benchmark_name
        self.start_time = datetime.now()
        self.end_time = None
        self.measurements: list[float] = []
        self.metadata: dict[str, Any] = {}

    def add_measurement(self, value: float):
        """添加测量值"""
        self.measurements.append(value)

    def get_statistics(self) -> dict[str, Any]:
        """获取统计数据"""
        if not self.measurements:
            return {
                "count": 0,
                "mean": 0,
                "median": 0,
                "min": 0,
                "max": 0,
                "std_dev": 0,
                "p95": 0,
                "p99": 0
            }

        sorted_data = sorted(self.measurements)
        n = len(sorted_data)

        return {
            "count": n,
            "mean": statistics.mean(sorted_data),
            "median": sorted_data[n // 2],
            "min": min(sorted_data),
            "max": max(sorted_data),
            "std_dev": statistics.stdev(sorted_data) if n > 1 else 0,
            "p95": sorted_data[int(n * 0.95)] if n >= 20 else sorted_data[-1],
            "p99": sorted_data[int(n * 0.99)] if n >= 100 else sorted_data[-1]
        }

    def get_summary(self) -> dict[str, Any]:
        """获取测试摘要"""
        self.end_time = datetime.now()
        stats = self.get_statistics()

        return {
            "benchmark_name": self.benchmark_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_seconds": (self.end_time - self.start_time).total_seconds(),
            "measurements_count": len(self.measurements),
            "statistics": stats,
            "metadata": self.metadata
        }


class BenchmarkTester:
    """
    性能基准测试器

    测试内容：
    1. OCR处理性能
    2. 图像处理性能
    3. 缓存性能
    4. 任务队列性能
    5. 端到端性能
    """

    def __init__(self):
        """初始化性能基准测试器"""
        self.benchmarks: dict[str, BenchmarkResult] = {}
        self.baseline_scores: dict[str, float] = {}

    async def benchmark_ocr_performance(
        self,
        image_path: str,
        iterations: int = 20,
        warmup_iterations: int = 3
    ) -> BenchmarkResult:
        """
        OCR性能基准测试

        Args:
            image_path: 测试图像路径
            iterations: 测试迭代次数
            warmup_iterations: 预热迭代次数

        Returns:
            性能基准测试结果
        """
        logger.info(f"🔍 开始OCR性能基准测试: {iterations}次迭代, {warmup_iterations}次预热")

        try:
            import sys
            core_dir = str(Path(__file__).parent.parent)
            if core_dir not in sys.path:
                sys.path.insert(0, core_dir)

            from core.perception.processors.tesseract_ocr import TesseractOCRProcessor

            ocr_processor = TesseractOCRProcessor()
        except ImportError as e:
            logger.error(f"导入失败: {e}")
            result = BenchmarkResult("OCR性能测试")
            return result

        result = BenchmarkResult("OCR性能测试")
        result.metadata = {
            "image_path": image_path,
            "iterations": iterations,
            "warmup_iterations": warmup_iterations
        }

        # 预热
        logger.info(f"预热阶段: {warmup_iterations}次迭代")
        for i in range(warmup_iterations):
            try:
                await ocr_processor.process_ocr(
                    image_path=image_path,
                    language="chinese",
                    preprocess=True
                )
                logger.info(f"  预热 {i+1}/{warmup_iterations} 完成")
            except Exception as e:
                logger.warning(f"预热失败: {e}")

        # 正式测试
        logger.info(f"正式测试: {iterations}次迭代")
        for i in range(iterations):
            start_time = time.time()

            try:
                await ocr_processor.process_ocr(
                    image_path=image_path,
                    language="chinese",
                    preprocess=True
                )

                elapsed = time.time() - start_time
                result.add_measurement(elapsed)

                if (i + 1) % 5 == 0:
                    logger.info(f"  进度: {i+1}/{iterations}")

            except Exception as e:
                logger.error(f"迭代{i}失败: {e}")

        # 输出统计
        stats = result.get_statistics()
        self._print_benchmark_statistics(result, stats, "秒")

        # 保存基准线
        self.baseline_scores["ocr"] = stats["mean"]

        # 记录结果
        self.benchmarks["ocr_performance"] = result

        return result

    async def benchmark_image_processing(
        self,
        image_path: str,
        operations: list[str],
        iterations: int = 10
    ) -> BenchmarkResult:
        """
        图像处理性能基准测试

        Args:
            image_path: 测试图像路径
            operations: 要测试的操作列表
            iterations: 每个操作的迭代次数

        Returns:
            性能基准测试结果
        """
        logger.info(f"🖼️ 开始图像处理性能基准测试: {len(operations)}个操作, {iterations}次迭代/操作")

        try:
            import sys
            core_dir = str(Path(__file__).parent.parent)
            if core_dir not in sys.path:
                sys.path.insert(0, core_dir)

            from core.perception.processors.opencv_image_processor import OpenCVImageProcessor

            image_processor = OpenCVImageProcessor()
        except ImportError as e:
            logger.error(f"导入失败: {e}")
            result = BenchmarkResult("图像处理性能测试")
            return result

        result = BenchmarkResult("图像处理性能测试")
        result.metadata = {
            "image_path": image_path,
            "operations": operations,
            "iterations": iterations
        }

        for operation in operations:
            logger.info(f"测试操作: {operation}")

            for i in range(iterations):
                start_time = time.time()

                try:
                    await image_processor.process_image(
                        image_path=image_path,
                        operation=operation
                    )

                    elapsed = time.time() - start_time
                    result.add_measurement(elapsed)

                except Exception as e:
                    logger.error(f"{operation} 迭代{i}失败: {e}")

        # 输出统计
        stats = result.get_statistics()
        self._print_benchmark_statistics(result, stats, "秒")

        # 保存基准线
        self.baseline_scores["image_processing"] = stats["mean"]

        # 记录结果
        self.benchmarks["image_processing"] = result

        return result

    async def benchmark_cache_performance(
        self,
        iterations: int = 100
    ) -> BenchmarkResult:
        """
        缓存性能基准测试

        Args:
            iterations: 测试迭代次数

        Returns:
            性能基准测试结果
        """
        logger.info(f"💾 开始缓存性能基准测试: {iterations}次迭代")

        try:
            import sys
            core_dir = str(Path(__file__).parent.parent)
            if core_dir not in sys.path:
                sys.path.insert(0, core_dir)

            from core.perception.cache.redis_cache import RedisCacheManager

            cache_manager = RedisCacheManager()
        except ImportError as e:
            logger.error(f"导入失败: {e}")
            result = BenchmarkResult("缓存性能测试")
            return result

        result = BenchmarkResult("缓存性能测试")
        result.metadata = {
            "iterations": iterations
        }

        # 测试写入性能
        logger.info("测试写入性能...")
        for i in range(iterations):
            start_time = time.time()

            try:
                await cache_manager.set(
                    f"bench_key_{i}",
                    {"data": f"bench_value_{i}"},
                    ttl=60
                )

                elapsed = time.time() - start_time
                result.add_measurement(elapsed)

            except Exception as e:
                logger.error(f"写入迭代{i}失败: {e}")

        # 输出统计
        stats = result.get_statistics()
        self._print_benchmark_statistics(result, stats, "秒")

        # 保存基准线
        self.baseline_scores["cache_write"] = stats["mean"]

        # 记录结果
        self.benchmarks["cache_write"] = result

        # 测试读取性能
        logger.info("测试读取性能...")
        read_result = BenchmarkResult("缓存读取性能测试")

        for i in range(iterations):
            start_time = time.time()

            try:
                await cache_manager.get(f"bench_key_{i}")

                elapsed = time.time() - start_time
                read_result.add_measurement(elapsed)

            except Exception as e:
                logger.error(f"读取迭代{i}失败: {e}")

        # 输出统计
        read_stats = read_result.get_statistics()
        self._print_benchmark_statistics(read_result, read_stats, "秒")

        # 保存基准线
        self.baseline_scores["cache_read"] = read_stats["mean"]

        # 记录结果
        self.benchmarks["cache_read"] = read_result

        return result

    async def benchmark_task_queue(
        self,
        num_tasks: int = 50,
        num_workers: int = 10
    ) -> BenchmarkResult:
        """
        任务队列性能基准测试

        Args:
            num_tasks: 任务数量
            num_workers: 工作线程数

        Returns:
            性能基准测试结果
        """
        logger.info(f"📋 开始任务队列性能基准测试: {num_tasks}任务, {num_workers}工作线程")

        try:
            import sys
            core_dir = str(Path(__file__).parent.parent)
            if core_dir not in sys.path:
                sys.path.insert(0, core_dir)

            from core.perception.queue.async_task_queue import AsyncTaskQueue, TaskPriority
        except ImportError as e:
            logger.error(f"导入失败: {e}")
            result = BenchmarkResult("任务队列性能测试")
            return result

        result = BenchmarkResult("任务队列性能测试")
        result.metadata = {
            "num_tasks": num_tasks,
            "num_workers": num_workers
        }

        task_queue = AsyncTaskQueue(max_workers=num_workers)

        # 测试任务提交和执行
        async def mock_task(task_id: int, duration: float = 0.01):
            await asyncio.sleep(duration)
            return task_id

        logger.info("提交和执行任务...")
        for i in range(num_tasks):
            start_time = time.time()

            try:
                # 提交任务
                queue_task_id = await task_queue.submit(
                    mock_task,
                    i,
                    0.01,
                    priority=TaskPriority.NORMAL
                )

                # 等待完成
                await task_queue.get_task_result(queue_task_id, timeout=10)

                elapsed = time.time() - start_time
                result.add_measurement(elapsed)

                if (i + 1) % 10 == 0:
                    logger.info(f"  进度: {i+1}/{num_tasks}")

            except Exception as e:
                logger.error(f"任务{i}失败: {e}")

        # 输出统计
        stats = result.get_statistics()
        self._print_benchmark_statistics(result, stats, "秒")

        # 保存基准线
        self.baseline_scores["task_queue"] = stats["mean"]

        # 记录结果
        self.benchmarks["task_queue"] = result

        return result

    async def benchmark_end_to_end(
        self,
        image_path: str,
        iterations: int = 10
    ) -> BenchmarkResult:
        """
        端到端性能基准测试

        Args:
            image_path: 测试图像路径
            iterations: 测试迭代次数

        Returns:
            性能基准测试结果
        """
        logger.info(f"🔄 开始端到端性能基准测试: {iterations}次迭代")

        try:
            import sys
            core_dir = str(Path(__file__).parent.parent)
            if core_dir not in sys.path:
                sys.path.insert(0, core_dir)

            from core.perception.cache.redis_cache import RedisCacheManager
            from core.perception.processors.tesseract_ocr import TesseractOCRProcessor
            from core.perception.queue.async_task_queue import AsyncTaskQueue, TaskPriority

            ocr_processor = TesseractOCRProcessor()
            cache_manager = RedisCacheManager()
            task_queue = AsyncTaskQueue(max_workers=5)
        except ImportError as e:
            logger.error(f"导入失败: {e}")
            result = BenchmarkResult("端到端性能测试")
            return result

        result = BenchmarkResult("端到端性能测试")
        result.metadata = {
            "image_path": image_path,
            "iterations": iterations
        }

        for i in range(iterations):
            start_time = time.time()

            try:
                # 1. 检查缓存
                cached = await cache_manager.get_ocr_result(
                    image_path,
                    "chinese",
                    True
                )

                if not cached:
                    # 2. 执行OCR
                    async def ocr_task():
                        ocr_result = await ocr_processor.process_ocr(
                            image_path=image_path,
                            language="chinese",
                            preprocess=True
                        )

                        # 3. 缓存结果
                        await cache_manager.set_ocr_result(
                            image_path,
                            "chinese",
                            True,
                            ocr_result
                        )

                        return ocr_result

                    # 提交到任务队列
                    queue_task_id = await task_queue.submit(
                        ocr_task,
                        priority=TaskPriority.NORMAL
                    )

                    # 等待完成
                    await task_queue.get_task_result(queue_task_id, timeout=30)

                elapsed = time.time() - start_time
                result.add_measurement(elapsed)

                logger.info(f"  迭代 {i+1}/{iterations}: {elapsed*1000:.2f}ms")

            except Exception as e:
                logger.error(f"迭代{i}失败: {e}")

        # 输出统计
        stats = result.get_statistics()
        self._print_benchmark_statistics(result, stats, "秒")

        # 保存基准线
        self.baseline_scores["end_to_end"] = stats["mean"]

        # 记录结果
        self.benchmarks["end_to_end"] = result

        return result

    def _print_benchmark_statistics(
        self,
        result: BenchmarkResult,
        stats: dict[str, Any],
        unit: str = "秒"
    ):
        """打印性能基准统计"""
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 {result.benchmark_name} - 性能基准")
        logger.info(f"{'='*60}")
        logger.info(f"测量次数:         {stats['count']}")
        logger.info(f"平均值:           {stats['mean']:.4f} {unit}")
        logger.info(f"中位数:           {stats['median']:.4f} {unit}")
        logger.info(f"最小值:           {stats['min']:.4f} {unit}")
        logger.info(f"最大值:           {stats['max']:.4f} {unit}")
        logger.info(f"标准差:           {stats['std_dev']:.4f} {unit}")
        logger.info(f"P95:              {stats['p95']:.4f} {unit}")
        logger.info(f"P99:              {stats['p99']:.4f} {unit}")
        logger.info(f"{'='*60}\n")

    def compare_with_baseline(
        self,
        benchmark_name: str,
        current_value: float
    ) -> dict[str, Any]:
        """
        与基准线对比

        Args:
            benchmark_name: 基准名称
            current_value: 当前值

        Returns:
            对比结果
        """
        if benchmark_name not in self.baseline_scores:
            return {
                "status": "no_baseline",
                "message": "没有可用的基准线"
            }

        baseline = self.baseline_scores[benchmark_name]
        diff = current_value - baseline
        diff_percent = (diff / baseline * 100) if baseline > 0 else 0

        # 判断性能变化
        if diff_percent < -5:  # 提升5%以上
            status = "improved"
            message = f"性能提升 {abs(diff_percent):.1f}%"
        elif diff_percent > 5:  # 下降5%以上
            status = "degraded"
            message = f"性能下降 {diff_percent:.1f}%"
        else:
            status = "stable"
            message = f"性能稳定 (变化 {diff_percent:.1f}%)"

        return {
            "status": status,
            "baseline": baseline,
            "current": current_value,
            "diff": diff,
            "diff_percent": diff_percent,
            "message": message
        }

    def generate_report(self) -> str:
        """生成测试报告"""
        report = []
        report.append("# 性能基准测试报告")
        report.append(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # 基准线总览
        report.append("## 基准线总览\n")
        report.append("| 指标 | 基准值 |")
        report.append("|------|--------|")
        for name, value in self.baseline_scores.items():
            report.append(f"| {name} | {value:.4f}s |")

        # 详细结果
        report.append("\n## 详细测试结果\n")

        for _benchmark_name, result in self.benchmarks.items():
            summary = result.get_summary()
            stats = summary["statistics"]

            report.append(f"### {summary['benchmark_name']}")
            report.append(f"- 测量次数: {stats['count']}")
            report.append(f"- 平均值: {stats['mean']:.4f}s")
            report.append(f"- 中位数: {stats['median']:.4f}s")
            report.append(f"- P95: {stats['p95']:.4f}s")
            report.append(f"- P99: {stats['p99']:.4f}s")
            report.append(f"- 标准差: {stats['std_dev']:.4f}s\n")

        return "\n".join(report)

    def save_baseline(self, filepath: str):
        """保存基准线到文件"""
        baseline_data = {
            "generated_at": datetime.now().isoformat(),
            "baselines": self.baseline_scores,
            "benchmarks": {
                name: result.get_summary()
                for name, result in self.benchmarks.items()
            }
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(baseline_data, f, ensure_ascii=False, indent=2)

        logger.info(f"✓ 基准线已保存: {filepath}")

    def load_baseline(self, filepath: str) -> bool:
        """从文件加载基准线"""
        try:
            with open(filepath, encoding='utf-8') as f:
                data = json.load(f)

            self.baseline_scores = data.get("baselines", {})
            logger.info(f"✓ 基准线已加载: {filepath}")
            return True

        except Exception as e:
            logger.error(f"加载基准线失败: {e}")
            return False


# 使用示例
if __name__ == "__main__":
    async def main():
        tester = BenchmarkTester()

        # 测试图像路径
        test_image = "/tmp/benchmark_test_image.png"

        # 创建测试图像
        from pathlib import Path
        if not Path(test_image).exists():
            import cv2
            import numpy as np
            img = np.ones((100, 200, 3), dtype=np.uint8) * 255
            cv2.putText(img, "Test", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
            cv2.imwrite(test_image, img)
            logger.info(f"✓ 已创建测试图像: {test_image}")

        # 运行测试套件
        logger.info("\n" + "="*60)
        logger.info("🚀 开始性能基准测试套件")
        logger.info("="*60 + "\n")

        # 1. OCR性能测试
        await tester.benchmark_ocr_performance(
            image_path=test_image,
            iterations=10,
            warmup_iterations=2
        )

        # 2. 图像处理性能测试
        await tester.benchmark_image_processing(
            image_path=test_image,
            operations=["edge_detection", "blur", "sharpen"],
            iterations=10
        )

        # 3. 缓存性能测试
        await tester.benchmark_cache_performance(iterations=50)

        # 4. 任务队列性能测试
        await tester.benchmark_task_queue(
            num_tasks=30,
            num_workers=5
        )

        # 5. 端到端性能测试
        await tester.benchmark_end_to_end(
            image_path=test_image,
            iterations=5
        )

        # 保存基准线
        tester.save_baseline("/tmp/performance_baseline.json")

        # 生成报告
        logger.info("\n" + "="*60)
        logger.info("📄 性能基准测试报告")
        logger.info("="*60 + "\n")
        print(tester.generate_report())

    asyncio.run(main())
