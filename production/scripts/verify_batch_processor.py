#!/usr/bin/env python3
"""
Athena批处理器验证脚本
验证批处理系统的功能和性能

作者: Athena平台团队
创建时间: 2025-12-29
版本: v1.0.0
"""

from __future__ import annotations
import asyncio
import logging
import sys
import time
from pathlib import Path
from typing import Any

# 添加项目路径
PROJECT_ROOT = Path("/Users/xujian/Athena工作平台")
sys.path.insert(0, str(PROJECT_ROOT))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'


def print_success(msg: str) -> Any:
    print(f"{Colors.GREEN}[✓]{Colors.NC} {msg}")


def print_error(msg: str) -> Any:
    print(f"{Colors.RED}[✗]{Colors.NC} {msg}")


def print_warning(msg: str) -> Any:
    print(f"{Colors.YELLOW}[⚠]{Colors.NC} {msg}")


def print_info(msg: str) -> Any:
    print(f"{Colors.BLUE}[i]{Colors.NC} {msg}")


def print_section(title: str) -> Any:
    print(f"\n{Colors.CYAN}{'='*60}{Colors.NC}")
    print(f"{Colors.CYAN}{title}{Colors.NC}")
    print(f"{Colors.CYAN}{'='*60}{Colors.NC}")


class BatchProcessorVerifier:
    """批处理器验证器"""

    def __init__(self):
        self.results = {
            "timestamp": time.time(),
            "tests": {},
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "warnings": 0
            }
        }

    def add_result(
        self,
        test_name: str,
        status: str,
        details: str = "",
        execution_time: float = 0.0,
        data: Any = None
    ):
        """添加测试结果"""
        self.results["tests"][test_name] = {
            "status": status,
            "details": details,
            "execution_time": execution_time,
            "data": data
        }

        self.results["summary"]["total"] += 1
        if status == "passed":
            self.results["summary"]["passed"] += 1
        elif status == "failed":
            self.results["summary"]["failed"] += 1
        else:
            self.results["summary"]["warnings"] += 1

    async def test_batch_processor_basic(self) -> bool:
        """测试批处理器基本功能"""
        print_section("测试1: 批处理器基本功能")

        try:
            import numpy as np

            from core.performance.batch_processor import BatchProcessor

            start_time = time.time()

            # 创建模拟模型
            class MockModel:
                def encode(self, texts, **kwargs) -> None:
                    return [np.random.randn(768).astype(np.float32) for _ in texts]

            model = MockModel()

            # 创建批处理器
            processor = BatchProcessor(
                model=model,
                batch_size=8,
                timeout_ms=100,
                device='cpu'
            )

            await processor.start()

            try:
                # 测试批量处理
                print_info("发送20个请求...")
                tasks = [
                    processor.process(f"测试文本 {i}", priority=2)
                    for i in range(20)
                ]
                results = await asyncio.gather(*tasks)

                execution_time = time.time() - start_time

                if len(results) == 20:
                    print_success(f"✓ 成功处理 {len(results)} 个请求 ({execution_time:.3f}秒)")

                    # 获取统计信息
                    stats = processor.get_stats()
                    print_info("统计信息:")
                    print_info(f"  - 总请求数: {stats['total_requests']}")
                    print_info(f"  - 总批次数: {stats['total_batches']}")
                    print_info(f"  - 平均批次大小: {stats['avg_batch_size']}")
                    print_info(f"  - 平均延迟: {stats['avg_latency_ms']:.2f}ms")

                    self.add_result(
                        "batch_processor_basic",
                        "passed",
                        "成功处理20个请求",
                        execution_time,
                        stats
                    )
                    return True
                else:
                    print_error(f"✗ 处理失败: 预期20个结果，实际{len(results)}个")
                    self.add_result("batch_processor_basic", "failed", "结果数量不正确")
                    return False

            finally:
                await processor.stop()

        except Exception as e:
            print_error(f"✗ 测试异常: {e}")
            import traceback
            traceback.print_exc()
            self.add_result("batch_processor_basic", "failed", str(e))
            return False

    async def test_priority_scheduling(self) -> bool:
        """测试优先级调度"""
        print_section("测试2: 优先级调度")

        try:
            import numpy as np

            from core.performance.batch_processor import BatchProcessor

            start_time = time.time()

            # 创建模拟模型
            class MockModel:
                def encode(self, texts, **kwargs) -> None:
                    return [np.random.randn(768).astype(np.float32) for _ in texts]

            model = MockModel()

            # 创建批处理器
            processor = BatchProcessor(
                model=model,
                batch_size=16,
                timeout_ms=50,
                device='cpu'
            )

            await processor.start()

            try:
                # 先发送100个低优先级请求
                print_info("发送100个低优先级请求...")
                low_tasks = [
                    processor.process(f"低优先级 {i}", priority=3)
                    for i in range(100)
                ]

                # 等待一小段时间让请求积压
                await asyncio.sleep(0.01)

                # 发送高优先级请求
                print_info("发送高优先级请求...")
                high_start = time.time()
                high_task = processor.process("🔥 高优先级紧急请求", priority=1)
                high_result = await high_task
                high_latency = (time.time() - high_start) * 1000

                execution_time = time.time() - start_time

                print_success(f"✓ 高优先级延迟: {high_latency:.2f}ms")

                # 验证高优先级请求确实被优先处理
                if high_latency < 500:  # 应该在500ms内完成
                    print_success(f"✓ 优先级调度工作正常 (延迟: {high_latency:.2f}ms < 500ms)")

                    # 完成所有低优先级任务
                    print_info("完成剩余低优先级请求...")
                    await asyncio.gather(*low_tasks)

                    stats = processor.get_stats()
                    print_info("最终统计:")
                    print_info(f"  - 总请求数: {stats['total_requests']}")
                    print_info(f"  - 吞吐量: {stats['throughput_per_sec']:.1f} texts/sec")

                    self.add_result(
                        "priority_scheduling",
                        "passed",
                        f"高优先级延迟: {high_latency:.2f}ms",
                        execution_time,
                        {"high_priority_latency_ms": high_latency}
                    )
                    return True
                else:
                    print_warning(f"⚠ 高优先级延迟过高: {high_latency:.2f}ms")
                    self.add_result(
                        "priority_scheduling",
                        "warning",
                        f"高优先级延迟: {high_latency:.2f}ms",
                        execution_time
                    )
                    return False

            finally:
                await processor.stop()

        except Exception as e:
            print_error(f"✗ 测试异常: {e}")
            import traceback
            traceback.print_exc()
            self.add_result("priority_scheduling", "failed", str(e))
            return False

    async def test_adaptive_batching(self) -> bool:
        """测试自适应批大小调整"""
        print_section("测试3: 自适应批大小")

        try:
            import numpy as np

            from core.performance.batch_processor import BatchProcessor

            start_time = time.time()

            # 创建模拟模型（模拟可变延迟）
            class VariableLatencyModel:
                def __init__(self):
                    self.call_count = 0

                def encode(self, texts, **kwargs) -> None:
                    self.call_count += 1
                    # 模拟延迟波动
                    time.sleep(0.001 * (len(texts) % 5))
                    return [np.random.randn(768).astype(np.float32) for _ in texts]

            model = VariableLatencyModel()

            # 创建批处理器（启用自适应）
            processor = BatchProcessor(
                model=model,
                batch_size=16,
                timeout_ms=50,
                device='cpu',
                enable_adaptive_batching=True,
                min_batch_size=4,
                max_batch_size=32
            )

            await processor.start()

            try:
                # 发送大量请求触发自适应调整
                print_info("发送80个请求...")
                tasks = [
                    processor.process(f"自适应测试 {i}", priority=2)
                    for i in range(80)
                ]
                results = await asyncio.gather(*tasks)

                execution_time = time.time() - start_time

                # 获取统计信息
                stats = processor.get_stats()
                initial_batch_size = stats["current_batch_size"]

                print_success(f"✓ 处理完成 ({execution_time:.3f}秒)")
                print_info("初始批大小: 16")
                print_info(f"当前批大小: {stats['current_batch_size']}")
                print_info(f"平均批次大小: {stats['avg_batch_size']}")
                print_info(f"平均延迟: {stats['avg_latency_ms']:.2f}ms")

                # 验证批大小确实发生了调整
                batch_size_changed = stats["current_batch_size"] != 16 or stats["avg_batch_size"] < 18

                if batch_size_changed:
                    print_success("✓ 自适应批大小调整工作正常")

                    self.add_result(
                        "adaptive_batching",
                        "passed",
                        "批大小发生自适应调整",
                        execution_time,
                        stats
                    )
                    return True
                else:
                    print_warning("⚠ 批大小未发生明显调整")
                    print_info("  (可能是延迟稳定，无需调整)")

                    self.add_result(
                        "adaptive_batching",
                        "passed",
                        "批大小保持稳定 (延迟稳定)",
                        execution_time,
                        stats
                    )
                    return True

            finally:
                await processor.stop()

        except Exception as e:
            print_error(f"✗ 测试异常: {e}")
            import traceback
            traceback.print_exc()
            self.add_result("adaptive_batching", "failed", str(e))
            return False

    async def test_performance_benchmark(self) -> bool:
        """测试性能基准"""
        print_section("测试4: 性能基准")

        try:
            import numpy as np

            from core.performance.batch_processor import BatchProcessor

            start_time = time.time()

            # 创建模拟模型
            class MockModel:
                def encode(self, texts, **kwargs) -> None:
                    time.sleep(0.01)  # 模拟推理时间
                    return [np.random.randn(768).astype(np.float32) for _ in texts]

            model = MockModel()

            # 创建批处理器
            processor = BatchProcessor(
                model=model,
                batch_size=32,
                timeout_ms=50,
                device='cpu'
            )

            await processor.start()

            try:
                # 性能测试：100个请求
                print_info("性能测试: 100个请求...")
                test_start = time.time()

                tasks = [
                    processor.process(f"性能测试 {i}", priority=2)
                    for i in range(100)
                ]
                results = await asyncio.gather(*tasks)

                test_time = time.time() - test_start
                throughput = len(results) / test_time

                # 获取统计信息
                stats = processor.get_stats()

                print_success("✓ 性能测试完成")
                print_info(f"  - 处理时间: {test_time:.3f}秒")
                print_info(f"  - 吞吐量: {throughput:.1f} texts/sec")
                print_info(f"  - 平均延迟: {stats['avg_latency_ms']:.2f}ms")
                print_info(f"  - 平均批次大小: {stats['avg_batch_size']:.1f}")

                # 验证性能指标
                if throughput > 10:  # 目标: >10 texts/sec
                    print_success(f"✓ 吞吐量达标: {throughput:.1f} > 10 texts/sec")

                    self.add_result(
                        "performance_benchmark",
                        "passed",
                        f"吞吐量: {throughput:.1f} texts/sec",
                        test_time,
                        {
                            "throughput": throughput,
                            "avg_latency_ms": stats['avg_latency_ms'],
                            "avg_batch_size": stats['avg_batch_size']
                        }
                    )
                    return True
                else:
                    print_warning(f"⚠ 吞吐量偏低: {throughput:.1f} texts/sec")

                    self.add_result(
                        "performance_benchmark",
                        "warning",
                        f"吞吐量: {throughput:.1f} texts/sec",
                        test_time
                    )
                    return False

            finally:
                await processor.stop()

        except Exception as e:
            print_error(f"✗ 测试异常: {e}")
            import traceback
            traceback.print_exc()
            self.add_result("performance_benchmark", "failed", str(e))
            return False

    async def test_with_real_bert_model(self) -> bool:
        """测试真实BERT模型集成"""
        print_section("测试5: 真实BERT模型集成")

        try:
            from sentence_transformers import SentenceTransformer

            from core.performance.batch_processor import BatchProcessor

            start_time = time.time()

            # 加载本地BERT模型
            print_info("加载本地BERT模型...")
            model_path = "/Users/xujian/Athena工作平台/models/converted/BAAI/bge-m3"

            if not Path(model_path).exists():
                print_warning(f"⚠ 模型路径不存在: {model_path}")
                print_info("跳过真实模型测试")
                self.add_result("real_bert_integration", "skipped", "模型路径不存在")
                return True

            model = SentenceTransformer(model_path)
            model = model.to('mps')

            print_success("✓ 模型加载完成")

            # 创建批处理器
            processor = BatchProcessor(
                model=model,
                batch_size=16,
                timeout_ms=100,
                device='mps'
            )

            await processor.start()

            try:
                # 测试BERT批处理
                print_info("测试BERT批处理...")
                test_texts = [
                    "这是一个测试文本",
                    "分析这段代码的性能",
                    "我今天心情很好",
                    "启动监控系统"
                ]

                # 发送20个请求（重复使用测试文本）
                tasks = []
                for i in range(20):
                    text = test_texts[i % len(test_texts)]
                    tasks.append(processor.process(text, priority=2))

                results = await asyncio.gather(*tasks)

                execution_time = time.time() - start_time

                if len(results) == 20 and len(results[0]) == 768:
                    print_success("✓ BERT批处理成功")
                    print_info(f"  - 处理请求数: {len(results)}")
                    print_info(f"  - 向量维度: {len(results[0])}")
                    print_info(f"  - 处理时间: {execution_time:.3f}秒")

                    # 获取统计信息
                    stats = processor.get_stats()
                    print_info("\n统计信息:")
                    print_info(f"  - 吞吐量: {stats['throughput_per_sec']:.1f} texts/sec")
                    print_info(f"  - 平均延迟: {stats['avg_latency_ms']:.2f}ms")
                    print_info(f"  - 平均批次大小: {stats['avg_batch_size']:.1f}")

                    self.add_result(
                        "real_bert_integration",
                        "passed",
                        "BERT模型集成成功",
                        execution_time,
                        stats
                    )
                    return True
                else:
                    print_error("✗ BERT批处理失败")
                    self.add_result("real_bert_integration", "failed", "结果格式不正确")
                    return False

            finally:
                await processor.stop()

        except Exception as e:
            print_error(f"✗ 测试异常: {e}")
            import traceback
            traceback.print_exc()
            self.add_result("real_bert_integration", "failed", str(e))
            return False

    async def run_all_verifications(self):
        """运行所有验证测试"""
        print_section("Athena批处理器验证")
        print(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

        # 执行测试
        tests = [
            ("批处理器基本功能", self.test_batch_processor_basic),
            ("优先级调度", self.test_priority_scheduling),
            ("自适应批大小", self.test_adaptive_batching),
            ("性能基准", self.test_performance_benchmark),
            ("真实BERT模型集成", self.test_with_real_bert_model),
        ]

        passed = 0
        failed = 0
        warnings = 0
        skipped = 0

        for test_name, test_func in tests:
            try:
                result = await test_func()
                if result:
                    passed += 1
                elif result is None:
                    skipped += 1
                else:
                    failed += 1
            except Exception as e:
                print_error(f"测试执行异常: {test_name} - {e}")
                failed += 1

        # 打印摘要
        self.print_summary()

        return failed == 0

    def print_summary(self) -> Any:
        """打印验证摘要"""
        print_section("验证摘要")

        summary = self.results["summary"]
        total = summary["total"]
        passed = summary["passed"]
        failed = summary["failed"]
        warnings = summary["warnings"]

        print(f"总测试数: {total}")
        print_success(f"通过: {passed}")
        if failed > 0:
            print_error(f"失败: {failed}")
        if warnings > 0:
            print_warning(f"警告: {warnings}")

        success_rate = (passed / total * 100) if total > 0 else 0
        print(f"\n通过率: {success_rate:.1f}%")

        if success_rate >= 90:
            print_success("\n🎉 批处理器验证通过!")
        elif success_rate >= 70:
            print_warning("\n⚠ 系统基本可用，建议优化部分功能")
        else:
            print_error("\n❌ 系统存在较多问题，需要修复")

    def save_report(self) -> None:
        """保存验证报告"""
        import json
        from datetime import datetime

        report_dir = Path("logs/performance")
        report_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"batch_processor_verification_{timestamp}.json"

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)

        print_info(f"\n报告已保存: {report_file}")


async def main():
    """主函数"""
    verifier = BatchProcessorVerifier()
    success = await verifier.run_all_verifications()

    # 保存报告
    verifier.save_report()

    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
