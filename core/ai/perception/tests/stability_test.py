#!/usr/bin/env python3

"""
Athena 感知模块 - 稳定性测试
长时间运行测试，检测内存泄漏、资源泄漏等问题
最后更新: 2026-01-26
"""

import asyncio
import json
import logging
import time
import tracemalloc
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import psutil

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StabilityMetrics:
    """稳定性指标"""

    def __init__(self):
        self.timestamps: list[datetime] = []
        self.memory_usage_mb: list[float] = []
        self.cpu_percent: list[float] = []
        self.open_files: list[int] = []
        self.thread_count: list[int] = []
        self.success_count: int = 0
        self.failure_count: int = 0
        self.response_times: list[float] = []

    def add_sample(
        self,
        memory_mb: float,
        cpu_percent: float,
        open_files: int,
        thread_count: int,
        response_time: float = 0,
        success: bool = True
    ):
        """添加样本"""
        self.timestamps.append(datetime.now())
        self.memory_usage_mb.append(memory_mb)
        self.cpu_percent.append(cpu_percent)
        self.open_files.append(open_files)
        self.thread_count.append(thread_count)

        if response_time > 0:
            self.response_times.append(response_time)

        if success:
            self.success_count += 1
        else:
            self.failure_count += 1

    def get_analysis(self) -> dict[str, Any]:
        """获取分析结果"""
        if not self.memory_usage_mb:
            return {"error": "没有数据"}

        # 内存分析
        initial_memory = self.memory_usage_mb[0]
        final_memory = self.memory_usage_mb[-1]
        memory_growth = final_memory - initial_memory
        memory_growth_percent = (memory_growth / initial_memory * 100) if initial_memory > 0 else 0

        # CPU分析
        avg_cpu = sum(self.cpu_percent) / len(self.cpu_percent)
        max_cpu = max(self.cpu_percent)

        # 响应时间分析
        avg_response = 0
        if self.response_times:
            avg_response = sum(self.response_times) / len(self.response_times)

        # 检测内存泄漏
        memory_leak_detected = False
        if len(self.memory_usage_mb) >= 10:
            # 检查是否有持续增长趋势
            first_half = self.memory_usage_mb[:len(self.memory_usage_mb)//2]
            second_half = self.memory_usage_mb[len(self.memory_usage_mb)//2:]
            avg_first = sum(first_half) / len(first_half)
            avg_second = sum(second_half) / len(second_half)

            if avg_second > avg_first * 1.5:  # 增长超过50%
                memory_leak_detected = True

        # 检测文件描述符泄漏
        fd_leak_detected = False
        if len(self.open_files) >= 10:
            first_half_fd = self.open_files[:len(self.open_files)//2]
            second_half_fd = self.open_files[len(self.open_files)//2:]
            avg_first_fd = sum(first_half_fd) / len(first_half_fd)
            avg_second_fd = sum(second_half_fd) / len(second_half_fd)

            if avg_second_fd > avg_first_fd * 2:  # 增长超过100%
                fd_leak_detected = True

        return {
            "duration_hours": (self.timestamps[-1] - self.timestamps[0]).total_seconds() / 3600,
            "total_requests": self.success_count + self.failure_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": (self.success_count / (self.success_count + self.failure_count) * 100)
                           if (self.success_count + self.failure_count) > 0 else 0,
            "memory": {
                "initial_mb": initial_memory,
                "final_mb": final_memory,
                "growth_mb": memory_growth,
                "growth_percent": memory_growth_percent,
                "leak_detected": memory_leak_detected
            },
            "cpu": {
                "avg_percent": avg_cpu,
                "max_percent": max_cpu
            },
            "file_descriptors": {
                "initial": self.open_files[0] if self.open_files else 0,
                "final": self.open_files[-1] if self.open_files else 0,
                "leak_detected": fd_leak_detected
            },
            "threads": {
                "avg": sum(self.thread_count) / len(self.thread_count) if self.thread_count else 0,
                "max": max(self.thread_count) if self.thread_count else 0
            },
            "response_time": {
                "avg_seconds": avg_response
            },
            "overall_stable": not (memory_leak_detected or fd_leak_detected)
        }


class StabilityTester:
    """
    稳定性测试器

    测试场景：
    1. 长时间运行测试（1小时+）
    2. 内存泄漏检测
    3. 文件描述符泄漏检测
    4. 资源使用监控
    """

    def __init__(self):
        """初始化稳定性测试器"""
        self.process = psutil.Process()
        self.test_results: dict[str, StabilityMetrics] = {}

        # 启动内存跟踪
        tracemalloc.start()

    def _get_current_metrics(self) -> dict[str, Any]:
        """获取当前进程指标"""
        try:
            memory_info = self.process.memory_info()
            return {
                "memory_mb": memory_info.rss / 1024 / 1024,  # RSS内存
                "cpu_percent": self.process.cpu_percent(),
                "open_files": len(self.process.open_files()),
                "thread_count": self.process.num_threads()
            }
        except Exception as e:
            logger.error(f"获取指标失败: {e}")
            return {
                "memory_mb": 0,
                "cpu_percent": 0,
                "open_files": 0,
                "thread_count": 0
            }

    async def test_long_running_stability(
        self,
        image_path: str,
        duration_minutes: int = 30,
        requests_per_minute: int = 10
    ) -> StabilityMetrics:
        """
        长时间运行稳定性测试

        Args:
            image_path: 测试图像路径
            duration_minutes: 测试持续时间（分钟）
            requests_per_minute: 每分钟请求数

        Returns:
            稳定性指标
        """
        logger.info(f"⏰ 开始长时间运行稳定性测试: {duration_minutes}分钟, {requests_per_minute}请求/分钟")

        try:
            import sys
            core_dir = str(Path(__file__).parent.parent)
            if core_dir not in sys.path:
                sys.path.insert(0, core_dir)

            from core.ai.perception.processors.tesseract_ocr import TesseractOCRProcessor

            ocr_processor = TesseractOCRProcessor()
        except ImportError as e:
            logger.error(f"导入失败: {e}")
            metrics = StabilityMetrics()
            return metrics

        metrics = StabilityMetrics()
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)

        request_interval = 60.0 / requests_per_minute

        logger.info(f"✓ 测试开始: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"✓ 预计结束: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")

        request_count = 0

        while datetime.now() < end_time:
            request_start = time.time()

            try:
                # 获取基线指标
                current_metrics = self._get_current_metrics()

                # 执行OCR
                await ocr_processor.process_ocr(
                    image_path=image_path,
                    language="chinese",
                    preprocess=True
                )

                response_time = time.time() - request_start

                # 记录指标
                metrics.add_sample(
                    memory_mb=current_metrics["memory_mb"],
                    cpu_percent=current_metrics["cpu_percent"],
                    open_files=current_metrics["open_files"],
                    thread_count=current_metrics["thread_count"],
                    response_time=response_time,
                    success=True
                )

                request_count += 1

                # 每10个请求报告一次进度
                if request_count % 10 == 0:
                    elapsed = (datetime.now() - start_time).total_seconds() / 60
                    logger.info(
                        f"进度: {elapsed:.1f}分钟 / {duration_minutes}分钟 "
                        f"({request_count}请求, 内存: {current_metrics['memory_mb']:.1f}MB)"
                    )

            except Exception as e:
                # 记录失败
                current_metrics = self._get_current_metrics()
                metrics.add_sample(
                    memory_mb=current_metrics["memory_mb"],
                    cpu_percent=current_metrics["cpu_percent"],
                    open_files=current_metrics["open_files"],
                    thread_count=current_metrics["thread_count"],
                    response_time=time.time() - request_start,
                    success=False
                )
                logger.error(f"请求失败: {e}")

            # 等待下一个请求间隔
            elapsed = time.time() - request_start
            if elapsed < request_interval:
                await asyncio.sleep(request_interval - elapsed)

        logger.info(f"✓ 测试完成: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 分析结果
        analysis = metrics.get_analysis()
        self._print_stability_analysis("长时间运行稳定性测试", analysis)

        # 记录结果
        test_name = f"long_running_{duration_minutes}min_{requests_per_minute}rpm"
        self.test_results[test_name] = metrics

        return metrics

    async def test_memory_leak_detection(
        self,
        image_path: str,
        iterations: int = 100
    ) -> StabilityMetrics:
        """
        内存泄漏检测测试

        Args:
            image_path: 测试图像路径
            iterations: 迭代次数

        Returns:
            稳定性指标
        """
        logger.info(f"🔍 开始内存泄漏检测测试: {iterations}次迭代")

        try:
            import sys
            core_dir = str(Path(__file__).parent.parent)
            if core_dir not in sys.path:
                sys.path.insert(0, core_dir)

            from core.ai.perception.cache.redis_cache import RedisCacheManager
            from core.ai.perception.processors.tesseract_ocr import TesseractOCRProcessor

            ocr_processor = TesseractOCRProcessor()
            RedisCacheManager()
        except ImportError as e:
            logger.error(f"导入失败: {e}")
            metrics = StabilityMetrics()
            return metrics

        metrics = StabilityMetrics()

        # 获取初始内存快照
        tracemalloc.clear_traces()
        snapshot1 = tracemalloc.take_snapshot()

        for i in range(iterations):
            try:
                # 获取当前指标
                current_metrics = self._get_current_metrics()

                # 执行OCR（每次都创建新实例，模拟真实使用）
                await ocr_processor.process_ocr(
                    image_path=image_path,
                    language="chinese",
                    preprocess=True
                )

                # 记录指标
                metrics.add_sample(
                    memory_mb=current_metrics["memory_mb"],
                    cpu_percent=current_metrics["cpu_percent"],
                    open_files=current_metrics["open_files"],
                    thread_count=current_metrics["thread_count"],
                    success=True
                )

                # 每20次迭代报告一次
                if (i + 1) % 20 == 0:
                    logger.info(f"进度: {i+1}/{iterations} 迭代")

            except Exception as e:
                current_metrics = self._get_current_metrics()
                metrics.add_sample(
                    memory_mb=current_metrics["memory_mb"],
                    cpu_percent=current_metrics["cpu_percent"],
                    open_files=current_metrics["open_files"],
                    thread_count=current_metrics["thread_count"],
                    success=False
                )
                logger.error(f"迭代{i}失败: {e}")

        # 获取最终内存快照
        snapshot2 = tracemalloc.take_snapshot()

        # 比较快照
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')
        logger.info("\n内存增长Top 10:")
        for stat in top_stats[:10]:
            logger.info(f"  {stat}")

        # 分析结果
        analysis = metrics.get_analysis()
        self._print_stability_analysis("内存泄漏检测测试", analysis)

        # 记录结果
        test_name = f"memory_leak_{iterations}iterations"
        self.test_results[test_name] = metrics

        return metrics

    async def test_resource_cleanup(
        self,
        image_path: str,
        iterations: int = 50
    ) -> StabilityMetrics:
        """
        资源清理测试

        Args:
            image_path: 测试图像路径
            iterations: 迭代次数

        Returns:
            稳定性指标
        """
        logger.info(f"🧹 开始资源清理测试: {iterations}次迭代")

        try:
            import sys
            core_dir = str(Path(__file__).parent.parent)
            if core_dir not in sys.path:
                sys.path.insert(0, core_dir)

            from core.ai.perception.processors.opencv_image_processor import OpenCVImageProcessor
        except ImportError as e:
            logger.error(f"导入失败: {e}")
            metrics = StabilityMetrics()
            return metrics

        metrics = StabilityMetrics()

        for i in range(iterations):
            try:
                # 获取当前指标
                current_metrics = self._get_current_metrics()

                # 执行图像处理（需要打开文件）
                await OpenCVImageProcessor().process_image(
                    image_path=image_path,
                    operation="edge_detection"
                )

                # 记录指标
                metrics.add_sample(
                    memory_mb=current_metrics["memory_mb"],
                    cpu_percent=current_metrics["cpu_percent"],
                    open_files=current_metrics["open_files"],
                    thread_count=current_metrics["thread_count"],
                    success=True
                )

                if (i + 1) % 10 == 0:
                    logger.info(f"进度: {i+1}/{iterations}")

            except Exception as e:
                current_metrics = self._get_current_metrics()
                metrics.add_sample(
                    memory_mb=current_metrics["memory_mb"],
                    cpu_percent=current_metrics["cpu_percent"],
                    open_files=current_metrics["open_files"],
                    thread_count=current_metrics["thread_count"],
                    success=False
                )
                logger.error(f"迭代{i}失败: {e}")

        # 分析结果
        analysis = metrics.get_analysis()
        self._print_stability_analysis("资源清理测试", analysis)

        # 记录结果
        test_name = f"resource_cleanup_{iterations}iterations"
        self.test_results[test_name] = metrics

        return metrics

    def _print_stability_analysis(self, test_name: str, analysis: dict[str, Any]):
        """打印稳定性分析"""
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 {test_name} - 稳定性分析")
        logger.info(f"{'='*60}")

        if "error" in analysis:
            logger.error(f"错误: {analysis['error']}")
            return

        logger.info(f"测试时长:         {analysis.get('duration_hours', 0):.2f}小时")
        logger.info(f"总请求数:         {analysis.get('total_requests', 0)}")
        logger.info(f"成功请求:         {analysis.get('success_count', 0)}")
        logger.info(f"失败请求:         {analysis.get('failure_count', 0)}")
        logger.info(f"成功率:           {analysis.get('success_rate', 0):.2f}%")

        # 内存分析
        memory = analysis.get('memory', {})
        logger.info("\n内存:")
        logger.info(f"  初始:           {memory.get('initial_mb', 0):.2f} MB")
        logger.info(f"  最终:           {memory.get('final_mb', 0):.2f} MB")
        logger.info(f"  增长:           {memory.get('growth_mb', 0):.2f} MB "
                   f"({memory.get('growth_percent', 0):.2f}%)")
        logger.info(f"  泄漏检测:       {'⚠️ 检测到泄漏' if memory.get('leak_detected') else '✅ 无泄漏'}")

        # CPU分析
        cpu = analysis.get('cpu', {})
        logger.info("\nCPU:")
        logger.info(f"  平均使用:       {cpu.get('avg_percent', 0):.2f}%")
        logger.info(f"  峰值使用:       {cpu.get('max_percent', 0):.2f}%")

        # 文件描述符分析
        fd = analysis.get('file_descriptors', {})
        logger.info("\n文件描述符:")
        logger.info(f"  初始:           {fd.get('initial', 0)}")
        logger.info(f"  最终:           {fd.get('final', 0)}")
        logger.info(f"  泄漏检测:       {'⚠️ 检测到泄漏' if fd.get('leak_detected') else '✅ 无泄漏'}")

        # 线程分析
        threads = analysis.get('threads', {})
        logger.info("\n线程:")
        logger.info(f"  平均:           {threads.get('avg', 0):.1f}")
        logger.info(f"  峰值:           {threads.get('max', 0)}")

        # 响应时间
        resp_time = analysis.get('response_time', {})
        logger.info("\n响应时间:")
        logger.info(f"  平均:           {resp_time.get('avg_seconds', 0)*1000:.2f} ms")

        # 总体评估
        logger.info(f"\n总体评估:         {'✅ 稳定' if analysis.get('overall_stable') else '⚠️ 不稳定'}")
        logger.info(f"{'='*60}\n")

    def get_all_results(self) -> dict[str, dict[str, Any]]:
        """获取所有测试结果"""
        return {
            test_name: metrics.get_analysis()
            for test_name, metrics in self.test_results.items()
        }

    def save_report(self, filepath: str):
        """保存测试报告到文件"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "tests": self.get_all_results()
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"✓ 报告已保存: {filepath}")


# 使用示例
if __name__ == "__main__":
    async def main():
        tester = StabilityTester()

        # 测试图像路径
        test_image = "/tmp/test_image.png"

        # 如果测试图像不存在，创建一个
        from pathlib import Path
        if not Path(test_image).exists():
            import cv2
            import numpy as np
            img = np.ones((100, 200, 3), dtype=np.uint8) * 255
            cv2.imwrite(test_image, img)
            logger.info(f"✓ 已创建测试图像: {test_image}")

        # 运行测试套件
        logger.info("\n" + "="*60)
        logger.info("🚀 开始稳定性测试套件")
        logger.info("="*60 + "\n")

        # 1. 内存泄漏检测测试
        await tester.test_memory_leak_detection(
            image_path=test_image,
            iterations=50
        )

        # 2. 资源清理测试
        await tester.test_resource_cleanup(
            image_path=test_image,
            iterations=30
        )

        # 3. 长时间运行测试（时间较长，可选）
        # await tester.test_long_running_stability(
        #     image_path=test_image,
        #     duration_minutes=10,
        #     requests_per_minute=6
        # )

        # 保存报告
        tester.save_report("/tmp/stability_test_report.json")

    asyncio.run(main())

