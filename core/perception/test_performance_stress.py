#!/usr/bin/env python3
from __future__ import annotations
"""
性能压力测试套件
Performance and Stress Test Suite

测试性能指标和压力承受能力

作者: 小诺·双鱼公主
创建时间: 2026-01-01
"""

import asyncio
import logging
import os

# 导入测试模块
import sys
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.perception.chinese_ocr_optimizer import ChineseOCROptimizer

logging.basicConfig(
    level=logging.WARNING,  # 减少日志输出
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """性能指标"""

    operation: str
    total_time: float
    count: int
    avg_time: float = field(init=False)
    min_time: float = float("inf")
    max_time: float = 0.0
    throughput: float = field(init=False)
    success_count: int = 0
    error_count: int = 0

    def __post_init__(self):
        self.avg_time = self.total_time / self.count if self.count > 0 else 0
        self.throughput = self.count / self.total_time if self.total_time > 0 else 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation": self.operation,
            "total_time": self.total_time,
            "count": self.count,
            "avg_time": self.avg_time,
            "min_time": self.min_time,
            "max_time": self.max_time,
            "throughput": self.throughput,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": self.success_count / self.count if self.count > 0 else 0,
        }


def print_header(title) -> None:
    """打印标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_metrics(metrics: PerformanceMetrics) -> Any:
    """打印性能指标"""
    print(f"\n📊 {metrics.operation}")
    print(f"   总次数: {metrics.count}")
    print(f"   总时间: {metrics.total_time:.3f}秒")
    print(f"   平均时间: {metrics.avg_time*1000:.2f}毫秒")
    print(f"   最小时间: {metrics.min_time*1000:.2f}毫秒")
    print(f"   最大时间: {metrics.max_time*1000:.2f}毫秒")
    print(f"   吞吐量: {metrics.throughput:.1f} 次/秒")
    print(f"   成功: {metrics.success_count} | 失败: {metrics.error_count}")
    print(f"   成功率: {metrics.success_count/metrics.count*100:.1f}%")


async def test_text_correction_performance():
    """测试文本纠错性能"""
    print_header("性能测试1: 文本纠错")

    optimizer = ChineseOCROptimizer()

    test_cases = [
        "①②③ 测试文本",
        "这  是  测  试  文  本",
        "测试,文本。包含[各种]标点符号",
        "人工智Neng混合文本",
        "这是一段较长的中文文本,包含多个句子和标点符号,用来测试性能。这是第二句话,继续测试。",
        "Mixed English and Chinese 中文混合 text for testing 性能测试。",
    ]

    # 预热
    for text in test_cases[:2]:
        await optimizer.correct_text(text)

    # 性能测试
    iterations = 1000
    times = []

    start_time = time.time()
    for i in range(iterations):
        text = test_cases[i % len(test_cases)]

        iter_start = time.time()
        try:
            await optimizer.correct_text(text)
            times.append(time.time() - iter_start)
        except Exception as e:
            logger.error(f"纠错失败: {e}")

    total_time = time.time() - start_time

    metrics = PerformanceMetrics(
        operation="文本纠错",
        total_time=total_time,
        count=iterations,
        min_time=min(times) if times else 0,
        max_time=max(times) if times else 0,
        success_count=len(times),
        error_count=iterations - len(times),
    )

    print_metrics(metrics)

    # 性能基准检查
    if metrics.avg_time < 0.001:  # < 1ms
        print(f"   ✅ 性能优秀 (平均{metrics.avg_time*1000:.2f}ms)")
        return True
    elif metrics.avg_time < 0.01:  # < 10ms
        print(f"   ✅ 性能良好 (平均{metrics.avg_time*1000:.2f}ms)")
        return True
    else:
        print(f"   ⚠️ 性能待优化 (平均{metrics.avg_time*1000:.2f}ms)")
        return False


async def test_confidence_scoring_performance():
    """测试置信度评分性能"""
    print_header("性能测试2: 置信度评分")

    optimizer = ChineseOCROptimizer()

    # 创建测试图片
    img = Image.new("RGB", (400, 100), color="white")
    temp_path = tempfile.mktemp(suffix=".png")
    img.save(temp_path)

    test_cases = [
        "这是中文测试文本",
        "This is English text",
        "混合Mixed文本Text",
        "这是一段非常长的中文文本,包含了超过十个字符的内容,用来测试置信度计算算法对于长文本的处理能力",
        "",
    ]

    # 预热
    for text in test_cases[:2]:
        optimizer._compute_chinese_confidence(text, temp_path)

    # 性能测试
    iterations = 10000
    times = []

    start_time = time.time()
    for i in range(iterations):
        text = test_cases[i % len(test_cases)]

        iter_start = time.time()
        try:
            optimizer._compute_chinese_confidence(text, temp_path)
            times.append(time.time() - iter_start)
        except Exception as e:
            logger.error(f"评分失败: {e}")

    total_time = time.time() - start_time

    metrics = PerformanceMetrics(
        operation="置信度评分",
        total_time=total_time,
        count=iterations,
        min_time=min(times) if times else 0,
        max_time=max(times) if times else 0,
        success_count=len(times),
        error_count=iterations - len(times),
    )

    print_metrics(metrics)

    # 清理
    if os.path.exists(temp_path):
        os.remove(temp_path)

    # 性能基准检查
    if metrics.avg_time < 0.0001:  # < 0.1ms
        print(f"   ✅ 性能优秀 (平均{metrics.avg_time*1000:.3f}ms)")
        return True
    elif metrics.avg_time < 0.001:  # < 1ms
        print(f"   ✅ 性能良好 (平均{metrics.avg_time*1000:.3f}ms)")
        return True
    else:
        print(f"   ⚠️ 性能待优化 (平均{metrics.avg_time*1000:.3f}ms)")
        return False


async def test_image_preprocessing_performance():
    """测试图像预处理性能"""
    print_header("性能测试3: 图像预处理")

    optimizer = ChineseOCROptimizer()

    # 创建不同尺寸的测试图片
    test_images = [
        (800, 600),  # 标准截图
        (1920, 1080),  # 全屏截图
        (400, 300),  # 小尺寸
        (2560, 1440),  # 2K截图
    ]

    all_passed = True

    for width, height in test_images:
        img = Image.new("RGB", (width, height), color="white")
        input_path = tempfile.mktemp(suffix=f"_{width}x{height}.png")
        output_path = tempfile.mktemp(suffix="_preprocessed.png")
        img.save(input_path)

        # 预热
        await optimizer.preprocess_image(input_path, output_path)

        # 性能测试
        iterations = 50
        times = []

        start_time = time.time()
        for _i in range(iterations):
            iter_start = time.time()
            try:
                await optimizer.preprocess_image(input_path, output_path)
                times.append(time.time() - iter_start)
            except Exception as e:
                logger.error(f"预处理失败: {e}")

        total_time = time.time() - start_time

        metrics = PerformanceMetrics(
            operation=f"图像预处理({width}x{height})",
            total_time=total_time,
            count=iterations,
            min_time=min(times) if times else 0,
            max_time=max(times) if times else 0,
            success_count=len(times),
            error_count=iterations - len(times),
        )

        print_metrics(metrics)

        # 清理
        for path in [input_path, output_path]:
            if os.path.exists(path):
                os.remove(path)

        # 性能基准检查
        if metrics.avg_time < 0.1:  # < 100ms
            print("   ✅ 性能良好")
        elif metrics.avg_time < 0.5:  # < 500ms
            print("   ⚠️ 性能一般")
            all_passed = False
        else:
            print("   ❌ 性能不足")
            all_passed = False

    return all_passed


async def test_stress_concurrent_operations():
    """压力测试: 并发操作"""
    print_header("压力测试1: 并发操作压力")

    optimizer = ChineseOCROptimizer()

    test_cases = [
        "①②③ 测试文本",
        "这  是  测  试",
        "Mixed English and Chinese",
        "这是一段较长的中文文本,用来测试并发性能。",
    ]

    # 测试不同的并发级别
    concurrency_levels = [10, 50, 100, 200, 500]

    all_passed = True

    for concurrency in concurrency_levels:
        print(f"\n🔥 并发级别: {concurrency}")

        # 预热
        for text in test_cases[:2]:
            await optimizer.correct_text(text)

        start_time = time.time()

        # 创建并发任务
        tasks = [
            optimizer.correct_text(test_cases[i % len(test_cases)]) for i in range(concurrency)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        total_time = time.time() - start_time

        success_count = sum(1 for r in results if isinstance(r, str))
        error_count = sum(1 for r in results if isinstance(r, Exception))

        print(f"   总时间: {total_time:.3f}秒")
        print(f"   成功: {success_count}/{concurrency}")
        print(f"   失败: {error_count}/{concurrency}")
        print(f"   吞吐量: {concurrency/total_time:.1f} 次/秒")
        print(f"   平均延迟: {total_time/concurrency*1000:.2f}ms")

        if error_count > 0:
            print("   ⚠️ 存在失败")
            all_passed = False
        else:
            print("   ✅ 全部成功")

    return all_passed


async def test_stress_memory_usage():
    """压力测试: 内存使用"""
    print_header("压力测试2: 内存使用")

    import gc

    import psutil

    process = psutil.Process()
    optimizer = ChineseOCROptimizer()

    # 记录初始内存
    gc.collect()
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB

    print(f"   初始内存: {initial_memory:.2f}MB")

    # 执行大量操作
    iterations = 1000
    test_cases = [
        "①②③ 测试文本",
        "这  是  测  试",
        "Mixed English and Chinese",
    ]

    for i in range(iterations):
        text = test_cases[i % len(test_cases)]
        await optimizer.correct_text(text)

        # 每100次检查一次内存
        if (i + 1) % 100 == 0:
            gc.collect()
            current_memory = process.memory_info().rss / 1024 / 1024
            memory_growth = current_memory - initial_memory
            print(f"   第{i+1}次迭代: {current_memory:.2f}MB (增长: {memory_growth:.2f}MB)")

    # 最终内存检查
    gc.collect()
    final_memory = process.memory_info().rss / 1024 / 1024
    total_growth = final_memory - initial_memory

    print(f"\n   最终内存: {final_memory:.2f}MB")
    print(f"   总增长: {total_growth:.2f}MB")
    print(f"   平均每次增长: {total_growth/iterations*1024:.2f}KB")

    # 内存增长检查
    if total_growth < 10:  # < 10MB
        print("   ✅ 内存使用良好")
        return True
    elif total_growth < 50:  # < 50MB
        print("   ⚠️ 内存使用一般")
        return True
    else:
        print("   ❌ 内存泄漏风险")
        return False


async def test_stress_large_scale_processing():
    """压力测试: 大规模处理"""
    print_header("压力测试3: 大规模处理")

    optimizer = ChineseOCROptimizer()

    # 创建测试图片
    img = Image.new("RGB", (800, 600), color="white")
    temp_path = tempfile.mktemp(suffix=".png")
    img.save(temp_path)

    # 大规模文本处理
    iterations = 5000
    test_texts = [
        "这是中文测试文本",
        "This is English text",
        "混合Mixed文本Text",
        "①②③④⑤⑥⑦⑧⑨⑩",
        "这是一段中等长度的中文文本,包含多个词语和标点符号,用于测试大规模处理的性能表现。",
    ]

    print(f"   处理规模: {iterations}次")
    print(f"   开始时间: {datetime.now().strftime('%H:%M:%S')}")

    start_time = time.time()

    for i in range(iterations):
        text = test_texts[i % len(test_texts)]

        # 综合操作
        _corrected = await optimizer.correct_text(text)
        _confidence = optimizer._compute_chinese_confidence(text, temp_path)

        if (i + 1) % 1000 == 0:
            elapsed = time.time() - start_time
            print(
                f"   进度: {i+1}/{iterations} ({(i+1)/iterations*100:.1f}%) - 已用时: {elapsed:.1f}秒"
            )

    total_time = time.time() - start_time
    end_time = datetime.now().strftime("%H:%M:%S")

    print(f"\n   结束时间: {end_time}")
    print(f"   总时间: {total_time:.2f}秒")
    print(f"   吞吐量: {iterations/total_time:.1f} 次/秒")
    print(f"   平均延迟: {total_time/iterations*1000:.2f}ms/次")

    # 清理
    if os.path.exists(temp_path):
        os.remove(temp_path)

    # 性能检查
    if iterations / total_time > 100:  # > 100次/秒
        print("   ✅ 性能优秀")
        return True
    elif iterations / total_time > 50:  # > 50次/秒
        print("   ✅ 性能良好")
        return True
    else:
        print("   ⚠️ 性能待优化")
        return False


async def test_long_running_stability():
    """稳定性测试: 长时间运行"""
    print_header("稳定性测试: 长时间运行")

    optimizer = ChineseOCROptimizer()

    # 持续运行30秒
    duration = 30  # 秒
    start_time = time.time()

    operation_count = 0
    error_count = 0

    print(f"   运行时长: {duration}秒")
    print(f"   开始时间: {datetime.now().strftime('%H:%M:%S')}")

    while time.time() - start_time < duration:
        # 执行混合操作
        try:
            text = f"测试文本{operation_count} ①②③ Mixed"
            await optimizer.correct_text(text)
            operation_count += 1
        except Exception as e:
            error_count += 1
            logger.error(f"操作失败: {e}")

        # 每5秒报告一次
        if int(time.time() - start_time) % 5 == 0 and operation_count % 10 == 0:
            elapsed = time.time() - start_time
            print(f"   已运行: {elapsed:.0f}秒 | 操作: {operation_count} | 错误: {error_count}")

    total_time = time.time() - start_time

    print(f"\n   总操作: {operation_count}")
    print(f"   总错误: {error_count}")
    print(f"   成功率: {(operation_count-error_count)/operation_count*100:.1f}%")
    print(f"   吞吐量: {operation_count/total_time:.1f} 次/秒")

    if error_count == 0:
        print("   ✅ 稳定性优秀")
        return True
    elif error_count < operation_count * 0.01:  # < 1%错误率
        print("   ✅ 稳定性良好")
        return True
    else:
        print("   ⚠️ 稳定性待改进")
        return False


async def main():
    """运行所有性能和压力测试"""
    print("\n")
    print("🔥 Athena性能压力测试")
    print("   作者: 小诺·双鱼公主")
    print("   日期: 2026-01-01")

    results = []

    # 性能测试
    results.append(await test_text_correction_performance())
    results.append(await test_confidence_scoring_performance())
    results.append(await test_image_preprocessing_performance())

    # 压力测试
    results.append(await test_stress_concurrent_operations())
    results.append(await test_stress_memory_usage())
    results.append(await test_stress_large_scale_processing())
    results.append(await test_long_running_stability())

    # 汇总结果
    print_header("性能压力测试结果汇总")

    total = len(results)
    passed = sum(results)
    failed = total - passed

    print(f"总计: {total} 个测试套件")
    print(f"通过: {passed} 个 ✅")
    print(f"失败: {failed} 个 ❌")
    print(f"通过率: {passed/total*100:.1f}%")

    if passed == total:
        print("\n🎉 所有性能压力测试通过!")
    else:
        print(f"\n⚠️ 有 {failed} 个测试需要优化")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
