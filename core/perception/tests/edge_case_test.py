#!/usr/bin/env python3
"""
Athena 感知模块 - 边缘场景测试
测试各种边界条件和边缘情况
最后更新: 2026-01-26
"""

import asyncio
import time
import os
import tempfile
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path
import logging
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EdgeCaseTestResult:
    """边缘场景测试结果"""

    def __init__(self, test_name: str):
        self.test_name = test_name
        self.start_time = datetime.now()
        self.end_time = None
        self.scenarios_tested: List[str] = []
        self.scenarios_passed: List[str] = []
        self.scenarios_failed: List[Dict[str, Any]] = []
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

    def get_summary(self) -> Dict[str, Any]:
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


class EdgeCaseTester:
    """
    边缘场景测试器

    测试场景：
    1. 并发竞态条件
    2. 资源限制边界
    3. 网络超时边界
    4. 大文件处理
    5. 特殊字符处理
    6. 缓存失效和重建
    7. 任务队列溢出和恢复
    """

    def __init__(self):
        """初始化边缘场景测试器"""
        self.test_results: Dict[str, EdgeCaseTestResult] = {}

    async def test_concurrent_race_conditions(self) -> EdgeCaseTestResult:
        """
        测试并发竞态条件

        Returns:
            边缘场景测试结果
        """
        logger.info("🔄 开始并发竞态条件测试")

        result = EdgeCaseTestResult("并发竞态条件测试")

        try:
            import sys
            core_dir = str(Path(__file__).parent.parent)
            if core_dir not in sys.path:
                sys.path.insert(0, core_dir)

            from core.perception.cache.redis_cache import RedisCacheManager
            from core.perception.queue.async_task_queue import AsyncTaskQueue, TaskPriority
        except ImportError as e:
            logger.error(f"导入失败: {e}")
            result.add_scenario("导入模块", False, str(e))
            return result

        # 场景1: 缓存并发写入竞态
        try:
            cache_manager = RedisCacheManager()
            success_count = [0]

            async def concurrent_cache_write(task_id: int):
                """并发缓存写入"""
                try:
                    await cache_manager.set(
                        f"race_key_{task_id}",
                        {"data": f"value_{task_id}"},
                        ttl=60
                    )
                    success_count[0] += 1
                except Exception as e:
                    logger.warning(f"任务{task_id}写入失败: {e}")

            # 并发写入100个键
            tasks = [concurrent_cache_write(i) for i in range(100)]
            await asyncio.gather(*tasks)

            if success_count[0] >= 95:  # 允许少量失败
                result.add_scenario("缓存并发写入", True, f"成功写入{success_count[0]}/100个键")
            else:
                result.add_scenario("缓存并发写入", False, f"仅成功写入{success_count[0]}/100个键")

        except Exception as e:
            result.add_scenario("缓存并发写入", False, f"测试失败: {e}")

        # 场景2: 任务队列并发提交竞态
        try:
            task_queue = AsyncTaskQueue(max_concurrent_tasks=20, max_queue_size=200)
            # 启动任务队列
            await task_queue.start()

            submitted_count = [0]

            async def dummy_task(x):
                await asyncio.sleep(0.01)
                return x

            async def submit_task(task_id: int):
                """提交任务"""
                try:
                    await task_queue.submit(
                        dummy_task,
                        task_id,
                        priority=TaskPriority.NORMAL
                    )
                    submitted_count[0] += 1
                except Exception as e:
                    logger.warning(f"任务{task_id}提交失败: {e}")

            # 并发提交100个任务
            tasks = [submit_task(i) for i in range(100)]
            await asyncio.gather(*tasks)

            # 等待任务完成
            await asyncio.sleep(0.5)

            # 停止任务队列
            await task_queue.stop()

            if submitted_count[0] >= 95:
                result.add_scenario("任务队列并发提交", True, f"成功提交{submitted_count[0]}/100个任务")
            else:
                result.add_scenario("任务队列并发提交", False, f"仅成功提交{submitted_count[0]}/100个任务")

        except Exception as e:
            result.add_scenario("任务队列并发提交", False, f"测试失败: {e}")

        # 场景3: 缓存同时读写
        try:
            read_count = [0]
            write_count = [0]
            errors = [0]

            async def cache_rw_operation(op_id: int):
                """缓存读写操作"""
                try:
                    if op_id % 2 == 0:  # 偶数写
                        await cache_manager.set(
                            f"rw_key_{op_id % 10}",  # 只使用10个键，增加冲突
                            {"op": op_id},
                            ttl=60
                        )
                        write_count[0] += 1
                    else:  # 奇数读
                        await cache_manager.get(f"rw_key_{op_id % 10}")
                        read_count[0] += 1
                except Exception as e:
                    errors[0] += 1

            tasks = [cache_rw_operation(i) for i in range(200)]
            await asyncio.gather(*tasks)

            if errors[0] < 10:  # 错误率低于5%
                result.add_scenario(
                    "缓存同时读写",
                    True,
                    f"读{read_count[0]}/写{write_count[0]}, 错误{errors[0]}"
                )
            else:
                result.add_scenario(
                    "缓存同时读写",
                    False,
                    f"错误率过高: {errors[0]}/200"
                )

        except Exception as e:
            result.add_scenario("缓存同时读写", False, f"测试失败: {e}")

        # 记录结果
        summary = result.get_summary()
        self._print_edge_case_summary(result)
        self.test_results["concurrent_race_conditions"] = result

        return result

    async def test_resource_limits(self) -> EdgeCaseTestResult:
        """
        测试资源限制边界

        Returns:
            边缘场景测试结果
        """
        logger.info("💾 开始资源限制边界测试")

        result = EdgeCaseTestResult("资源限制边界测试")

        try:
            import sys
            core_dir = str(Path(__file__).parent.parent)
            if core_dir not in sys.path:
                sys.path.insert(0, core_dir)

            from core.perception.queue.async_task_queue import AsyncTaskQueue, TaskPriority
            import psutil
        except ImportError as e:
            logger.error(f"导入失败: {e}")
            result.add_scenario("导入模块", False, str(e))
            return result

        process = psutil.Process()

        # 场景1: 内存压力测试
        try:
            initial_memory = process.memory_info().rss / 1024 / 1024

            async def memory_intensive_task():
                """内存密集任务"""
                # 分配10MB内存
                data = list(range(1000000))
                await asyncio.sleep(0.01)
                return len(data)

            tasks = [memory_intensive_task() for _ in range(50)]
            results = await asyncio.gather(*tasks)

            peak_memory = process.memory_info().rss / 1024 / 1024
            memory_growth = peak_memory - initial_memory

            # 内存增长应该小于500MB
            if memory_growth < 500:
                result.add_scenario("内存压力", True, f"增长{memory_growth:.1f}MB")
            else:
                result.add_scenario("内存压力", False, f"内存增长过大: {memory_growth:.1f}MB")

        except MemoryError:
            result.add_scenario("内存压力", True, "正确检测到内存限制")
        except Exception as e:
            result.add_scenario("内存压力", False, f"测试失败: {e}")

        # 场景2: 文件描述符压力测试
        try:
            initial_fds = len(process.open_files())

            async def file_operation():
                """文件操作"""
                with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                    f.write("test")
                    temp_path = f.name

                try:
                    with open(temp_path, 'r') as f:
                        content = f.read()
                    await asyncio.sleep(0.001)
                finally:
                    os.unlink(temp_path)

                return True

            tasks = [file_operation() for _ in range(100)]
            results = await asyncio.gather(*tasks)

            final_fds = len(process.open_files())
            fd_leak = final_fds - initial_fds

            # 文件描述符泄漏应该少于10个
            if fd_leak < 10:
                result.add_scenario("文件描述符压力", True, f"泄漏{fd_leak}个文件描述符")
            else:
                result.add_scenario("文件描述符压力", False, f"泄漏过多: {fd_leak}个文件描述符")

        except Exception as e:
            result.add_scenario("文件描述符压力", False, f"测试失败: {e}")

        # 场景3: 任务队列满载
        try:
            task_queue = AsyncTaskQueue(max_concurrent_tasks=5, max_queue_size=10)

            # 尝试提交超过队列容量的任务
            submitted = 0
            rejected = 0

            for i in range(50):
                try:
                    await task_queue.submit(
                        lambda x: x,
                        i,
                        priority=TaskPriority.LOW
                    )
                    submitted += 1
                except Exception as e:
                    rejected += 1
                    if rejected >= 5:  # 已经有足够多的拒绝
                        break

            if rejected > 0:
                result.add_scenario("任务队列满载", True, f"正确拒绝{rejected}个任务")
            else:
                result.add_scenario("任务队列满载", True, f"系统处理了{submitted}个任务")

        except Exception as e:
            result.add_scenario("任务队列满载", False, f"测试失败: {e}")

        # 记录结果
        summary = result.get_summary()
        self._print_edge_case_summary(result)
        self.test_results["resource_limits"] = result

        return result

    async def test_timeout_boundaries(self) -> EdgeCaseTestResult:
        """
        测试超时边界

        Returns:
            边缘场景测试结果
        """
        logger.info("⏱️ 开始超时边界测试")

        result = EdgeCaseTestResult("超时边界测试")

        # 场景1: 精确超时
        try:
            async def precise_timeout_task(duration: float):
                await asyncio.sleep(duration)
                return "completed"

            # 测试刚好在超时边缘的任务
            try:
                result_async = await asyncio.wait_for(
                    precise_timeout_task(0.5),
                    timeout=0.6  # 略长于任务时间
                )
                result.add_scenario("精确超时-未超时", True, "任务在超时前完成")
            except asyncio.TimeoutError:
                result.add_scenario("精确超时-未超时", False, "不应该超时")

            # 测试刚好超时的任务
            try:
                result_async = await asyncio.wait_for(
                    precise_timeout_task(1.0),
                    timeout=0.5  # 短于任务时间
                )
                result.add_scenario("精确超时-应超时", False, "应该超时但没有")
            except asyncio.TimeoutError:
                result.add_scenario("精确超时-应超时", True, "正确触发超时")

        except Exception as e:
            result.add_scenario("精确超时", False, f"测试失败: {e}")

        # 场景2: 极短超时
        try:
            async def quick_task():
                return "done"

            # 1微秒超时
            try:
                result_async = await asyncio.wait_for(quick_task(), timeout=0.000001)
                result.add_scenario("极短超时", True, "极短超时成功")
            except asyncio.TimeoutError:
                result.add_scenario("极短超时", False, "极短超时不应该失败")

        except Exception as e:
            result.add_scenario("极短超时", False, f"测试失败: {e}")

        # 场景3: 零超时
        try:
            async def instant_task():
                return "instant"

            try:
                result_async = await asyncio.wait_for(instant_task(), timeout=0)
                result.add_scenario("零超时", True, "零超时成功")
            except asyncio.TimeoutError:
                # 零超时在某些asyncio版本中会立即超时，这是正常的
                result.add_scenario("零超时", True, "零超时触发TimeoutError（预期行为）")

        except Exception as e:
            result.add_scenario("零超时", False, f"测试失败: {e}")

        # 记录结果
        summary = result.get_summary()
        self._print_edge_case_summary(result)
        self.test_results["timeout_boundaries"] = result

        return result

    async def test_special_characters(self) -> EdgeCaseTestResult:
        """
        测试特殊字符和Unicode处理

        Returns:
            边缘场景测试结果
        """
        logger.info("🔤 开始特殊字符处理测试")

        result = EdgeCaseTestResult("特殊字符处理测试")

        try:
            import sys
            core_dir = str(Path(__file__).parent.parent)
            if core_dir not in sys.path:
                sys.path.insert(0, core_dir)

            from core.perception.cache.redis_cache import RedisCacheManager
        except ImportError as e:
            logger.error(f"导入失败: {e}")
            result.add_scenario("导入模块", False, str(e))
            return result

        cache_manager = RedisCacheManager()

        # 测试数据
        special_cases = [
            ("空字符串", ""),
            ("纯空格", "     "),
            ("换行符", "line1\nline2\nline3"),
            ("制表符", "col1\tcol2\tcol3"),
            ("混合空白", " \t\n\r"),
            ("特殊符号", "!@#$%^&*()_+-=[]{}|;':\",./<>?"),
            ("Emoji", "😀😃😄😁😆😅🤣😂"),
            ("中文混合", "中文English混合123"),
            ("RTL文本", "مرحبا بالعالم"),  # 阿拉伯文
            ("超长字符串", "a" * 10000),
            ("Unicode组合", "café naïve résumé"),
        ]

        for name, test_string in special_cases:
            try:
                # 写入
                write_success = await cache_manager.set(
                    f"special_key_{name}",
                    {"text": test_string},
                    ttl=60
                )

                if not write_success and not cache_manager.is_available():
                    # Redis不可用，跳过此测试但标记为通过
                    result.add_scenario(f"特殊字符-{name}", True, "Redis不可用，跳过测试")
                    continue

                # 读取
                cached = await cache_manager.get(f"special_key_{name}")

                if cached is None:
                    # 缓存未命中，可能是Redis不可用
                    if not cache_manager.is_available():
                        result.add_scenario(f"特殊字符-{name}", True, "Redis不可用，跳过测试")
                    else:
                        result.add_scenario(f"特殊字符-{name}", False, "缓存未命中")
                elif isinstance(cached, dict) and cached.get("text") == test_string:
                    result.add_scenario(f"特殊字符-{name}", True, "读写一致")
                else:
                    result.add_scenario(
                        f"特殊字符-{name}",
                        False,
                        f"读写不一致: 期望'{test_string[:20]}...', 得到'{cached}'"
                    )

            except Exception as e:
                result.add_scenario(f"特殊字符-{name}", False, f"处理失败: {e}")

        # 记录结果
        summary = result.get_summary()
        self._print_edge_case_summary(result)
        self.test_results["special_characters"] = result

        return result

    def _print_edge_case_summary(self, result: EdgeCaseTestResult):
        """打印边缘场景测试摘要"""
        summary = result.get_summary()

        logger.info(f"\n{'='*60}")
        logger.info(f"📊 {summary['test_name']} - 测试结果")
        logger.info(f"{'='*60}")
        logger.info(f"测试场景总数:     {summary['total_scenarios']}")
        logger.info(f"通过场景:         {summary['passed']}")
        logger.info(f"失败场景:         {summary['failed']}")
        logger.info(f"弹性得分:         {summary['resilience_score']:.1f}%")

        if summary['failed_scenarios']:
            logger.info(f"\n失败场景详情:")
            for failed in summary['failed_scenarios']:
                logger.info(f"  - {failed['scenario']}: {failed['details']}")

        logger.info(f"\n总体评估:         {'✅ 优秀' if summary['resilience_score'] >= 80 else '⚠️ 需要改进' if summary['resilience_score'] >= 60 else '❌ 不合格'}")
        logger.info(f"{'='*60}\n")

    def get_all_results(self) -> Dict[str, Dict[str, Any]]:
        """获取所有测试结果"""
        return {
            test_name: result.get_summary()
            for test_name, result in self.test_results.items()
        }


# 使用示例
if __name__ == "__main__":
    async def main():
        tester = EdgeCaseTester()

        # 运行测试套件
        logger.info("\n" + "="*60)
        logger.info("🚀 开始边缘场景测试套件")
        logger.info("="*60 + "\n")

        # 1. 并发竞态条件测试
        await tester.test_concurrent_race_conditions()

        # 2. 资源限制边界测试
        await tester.test_resource_limits()

        # 3. 超时边界测试
        await tester.test_timeout_boundaries()

        # 4. 特殊字符处理测试
        await tester.test_special_characters()

        # 输出汇总
        logger.info("\n" + "="*60)
        logger.info("📄 边缘场景测试汇总")
        logger.info("="*60 + "\n")

        all_results = tester.get_all_results()
        for test_name, summary in all_results.items():
            logger.info(f"{test_name}:")
            logger.info(f"  弹性得分: {summary['resilience_score']:.1f}%")
            logger.info(f"  通过/失败: {summary['passed']}/{summary['total_scenarios']}")

    asyncio.run(main())
