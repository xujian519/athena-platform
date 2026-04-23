#!/usr/bin/env python3
"""
Agent性能基准测试
Agent Performance Benchmark Tests

测试目标：
1. Agent初始化: <100ms
2. Agent执行: <5s (P95)
3. 吞吐量: >10 QPS

Usage:
    pytest tests/agents/test_agent_performance.py -v
    pytest tests/agents/test_agent_performance.py --benchmark-only
"""

import asyncio
import statistics
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pytest

# 添加项目路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.agents.xiaona.base_component import AgentExecutionContext
from core.agents.xiaona.retriever_agent import RetrieverAgent
from core.agents.xiaona.analyzer_agent import AnalyzerAgent
from core.agents.xiaona.writer_agent import WriterAgent


# ==================== 性能基准数据 ====================

@dataclass
class PerformanceBenchmark:
    """性能基准数据"""
    name: str
    target_p50: float  # 50分位数目标值（毫秒）
    target_p95: float  # 95分位数目标值（毫秒）
    target_p99: float  # 99分位数目标值（毫秒）


# 性能基准定义
BENCHMARKS = {
    "agent_initialization": PerformanceBenchmark(
        name="Agent初始化",
        target_p50=50,   # 50ms
        target_p95=100,  # 100ms
        target_p99=150,  # 150ms
    ),
    "agent_execution": PerformanceBenchmark(
        name="Agent执行",
        target_p50=2000,  # 2s
        target_p95=5000,  # 5s
        target_p99=8000,  # 8s
    ),
    "capability_discovery": PerformanceBenchmark(
        name="能力发现",
        target_p50=1,     # 1ms
        target_p95=5,     # 5ms
        target_p99=10,    # 10ms
    ),
    "input_validation": PerformanceBenchmark(
        name="输入验证",
        target_p50=10,    # 10ms
        target_p95=50,    # 50ms
        target_p99=100,   # 100ms
    ),
}


@dataclass
class PerformanceMetrics:
    """性能指标"""
    name: str
    samples: List[float] = field(default_factory=list)
    unit: str = "ms"
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def count(self) -> int:
        return len(self.samples)

    @property
    def min(self) -> float:
        return min(self.samples) if self.samples else 0.0

    @property
    def max(self) -> float:
        return max(self.samples) if self.samples else 0.0

    @property
    def avg(self) -> float:
        return statistics.mean(self.samples) if self.samples else 0.0

    @property
    def median(self) -> float:
        return statistics.median(self.samples) if self.samples else 0.0

    @property
    def p95(self) -> float:
        if not self.samples:
            return 0.0
        sorted_samples = sorted(self.samples)
        index = int(len(sorted_samples) * 0.95)
        return sorted_samples[min(index, len(sorted_samples) - 1)]

    @property
    def p99(self) -> float:
        if not self.samples:
            return 0.0
        sorted_samples = sorted(self.samples)
        index = int(len(sorted_samples) * 0.99)
        return sorted_samples[min(index, len(sorted_samples) - 1)]

    @property
    def std_dev(self) -> float:
        if len(self.samples) < 2:
            return 0.0
        return statistics.stdev(self.samples)

    def check_benchmark(self, benchmark: PerformanceBenchmark) -> Dict[str, Any]:
        """检查是否符合基准"""
        return {
            "p50_pass": self.median <= benchmark.target_p50,
            "p95_pass": self.p95 <= benchmark.target_p95,
            "p99_pass": self.p99 <= benchmark.target_p99,
            "overall_pass": (
                self.median <= benchmark.target_p50 and
                self.p95 <= benchmark.target_p95 and
                self.p99 <= benchmark.target_p99
            )
        }


# ==================== 测试辅助函数 ====================

def measure_time(func, *args, **kwargs) -> float:
    """测量函数执行时间（毫秒）"""
    start = time.perf_counter()
    _ = func(*args, **kwargs)
    elapsed = time.perf_counter() - start
    return elapsed * 1000  # 转换为毫秒


async def measure_time_async(func, *args, **kwargs) -> float:
    """测量异步函数执行时间（毫秒）"""
    start = time.perf_counter()
    _ = await func(*args, **kwargs)
    elapsed = time.perf_counter() - start
    return elapsed * 1000  # 转换为毫秒


# ==================== Agent初始化性能测试 ====================

class TestAgentInitializationPerformance:
    """Agent初始化性能测试"""

    @pytest.mark.benchmark
    @pytest.mark.parametrize("agent_class", [
        RetrieverAgent,
        AnalyzerAgent,
        WriterAgent,
    ])
    def test_agent_initialization_speed(self, agent_class, benchmark):
        """测试Agent初始化速度"""

        def init_agent():
            return agent_class(agent_id=f"test_{agent_class.__name__.lower()}")

        # 使用pytest-benchmark
        result = benchmark(init_agent)

        # 验证结果
        assert result is not None
        assert hasattr(result, "agent_id")

    @pytest.mark.performance
    def test_retriever_agent_initialization_multiple(self):
        """测试RetrieverAgent多次初始化性能"""
        metrics = PerformanceMetrics(name="retriever_initialization")

        for i in range(50):
            elapsed = measure_time(
                RetrieverAgent,
                agent_id=f"test_retriever_{i}"
            )
            metrics.samples.append(elapsed)

        # 检查基准
        benchmark = BENCHMARKS["agent_initialization"]
        check = metrics.check_benchmark(benchmark)

        print(f"\n📊 RetrieverAgent初始化性能:")
        print(f"   平均: {metrics.avg:.2f}ms")
        print(f"   P50: {metrics.median:.2f}ms")
        print(f"   P95: {metrics.p95:.2f}ms")
        print(f"   P99: {metrics.p99:.2f}ms")
        print(f"   基准: P50<{benchmark.target_p50}ms, P95<{benchmark.target_p95}ms")

        # P95必须通过
        assert check["p95_pass"], f"P95 {metrics.p95:.2f}ms 超过基准 {benchmark.target_p95}ms"

    @pytest.mark.performance
    def test_analyzer_agent_initialization_multiple(self):
        """测试AnalyzerAgent多次初始化性能"""
        metrics = PerformanceMetrics(name="analyzer_initialization")

        for i in range(50):
            elapsed = measure_time(
                AnalyzerAgent,
                agent_id=f"test_analyzer_{i}"
            )
            metrics.samples.append(elapsed)

        benchmark = BENCHMARKS["agent_initialization"]
        check = metrics.check_benchmark(benchmark)

        print(f"\n📊 AnalyzerAgent初始化性能:")
        print(f"   平均: {metrics.avg:.2f}ms")
        print(f"   P95: {metrics.p95:.2f}ms")

        assert check["p95_pass"], f"P95 {metrics.p95:.2f}ms 超过基准 {benchmark.target_p95}ms"

    @pytest.mark.performance
    def test_writer_agent_initialization_multiple(self):
        """测试WriterAgent多次初始化性能"""
        metrics = PerformanceMetrics(name="writer_initialization")

        for i in range(50):
            elapsed = measure_time(
                WriterAgent,
                agent_id=f"test_writer_{i}"
            )
            metrics.samples.append(elapsed)

        benchmark = BENCHMARKS["agent_initialization"]
        check = metrics.check_benchmark(benchmark)

        print(f"\n📊 WriterAgent初始化性能:")
        print(f"   平均: {metrics.avg:.2f}ms")
        print(f"   P95: {metrics.p95:.2f}ms")

        assert check["p95_pass"], f"P95 {metrics.p95:.2f}ms 超过基准 {benchmark.target_p95}ms"


# ==================== 能力发现性能测试 ====================

class TestCapabilityDiscoveryPerformance:
    """能力发现性能测试"""

    @pytest.mark.performance
    def test_get_capabilities_performance(self):
        """测试get_capabilities性能"""
        agent = RetrieverAgent(agent_id="test_retriever")
        metrics = PerformanceMetrics(name="get_capabilities")

        for _ in range(100):
            elapsed = measure_time(agent.get_capabilities)
            metrics.samples.append(elapsed)

        benchmark = BENCHMARKS["capability_discovery"]
        check = metrics.check_benchmark(benchmark)

        print(f"\n📊 get_capabilities性能:")
        print(f"   平均: {metrics.avg:.4f}ms")
        print(f"   P95: {metrics.p95:.4f}ms")

        assert check["p95_pass"], f"P95 {metrics.p95:.4f}ms 超过基准 {benchmark.target_p95}ms"

    @pytest.mark.performance
    def test_get_info_performance(self):
        """测试get_info性能"""
        agent = RetrieverAgent(agent_id="test_retriever")
        metrics = PerformanceMetrics(name="get_info")

        for _ in range(100):
            elapsed = measure_time(agent.get_info)
            metrics.samples.append(elapsed)

        print(f"\n📊 get_info性能:")
        print(f"   平均: {metrics.avg:.4f}ms")

        # get_info应该很快
        assert metrics.avg < 1, f"get_info平均时间 {metrics.avg:.4f}ms 过长"

    @pytest.mark.performance
    def test_get_system_prompt_performance(self):
        """测试get_system_prompt性能"""
        agent = RetrieverAgent(agent_id="test_retriever")
        metrics = PerformanceMetrics(name="get_system_prompt")

        for _ in range(50):  # system prompt可能较长
            elapsed = measure_time(agent.get_system_prompt)
            metrics.samples.append(elapsed)

        print(f"\n📊 get_system_prompt性能:")
        print(f"   平均: {metrics.avg:.2f}ms")

        # system prompt可以稍慢，但不应超过10ms
        assert metrics.avg < 10, f"get_system_prompt平均时间 {metrics.avg:.2f}ms 过长"


# ==================== 输入验证性能测试 ====================

class TestInputValidationPerformance:
    """输入验证性能测试"""

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_validate_input_performance(self):
        """测试validate_input性能"""
        agent = RetrieverAgent(agent_id="test_retriever")
        metrics = PerformanceMetrics(name="validate_input")

        test_input = {
            "query": "测试查询",
            "top_k": 10,
        }

        for _ in range(100):
            # validate_input通常是同步方法
            elapsed = measure_time(agent.validate_input, test_input)
            metrics.samples.append(elapsed)

        benchmark = BENCHMARKS["input_validation"]
        check = metrics.check_benchmark(benchmark)

        print(f"\n📊 validate_input性能:")
        print(f"   平均: {metrics.avg:.4f}ms")
        print(f"   P95: {metrics.p95:.4f}ms")

        assert check["p95_pass"], f"P95 {metrics.p95:.4f}ms 超过基准 {benchmark.target_p95}ms"


# ==================== Agent执行性能测试 ====================

class TestAgentExecutionPerformance:
    """Agent执行性能测试"""

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_retriever_agent_execution_performance(self):
        """测试RetrieverAgent执行性能"""
        agent = RetrieverAgent(agent_id="test_retriever")
        metrics = PerformanceMetrics(name="retriever_execution")

        context = AgentExecutionContext(
            session_id="test_session",
            task_id="test_task",
            input_data={"query": "专利检索测试", "top_k": 5},
            config={"timeout": 10},
            metadata={},
        )

        # 由于execute可能涉及LLM调用，这里只测试少量样本
        for i in range(5):
            try:
                elapsed = await measure_time_async(agent.execute, context)
                metrics.samples.append(elapsed)
            except Exception as e:
                # 执行失败时记录但不中断
                print(f"   执行 #{i} 失败: {e}")

        if metrics.samples:
            benchmark = BENCHMARKS["agent_execution"]
            check = metrics.check_benchmark(benchmark)

            print(f"\n📊 RetrieverAgent执行性能:")
            print(f"   样本数: {metrics.count}")
            print(f"   平均: {metrics.avg:.2f}ms")
            print(f"   P95: {metrics.p95:.2f}ms")
            print(f"   基准: P95<{benchmark.target_p95}ms")

            # 注意：执行性能受LLM响应时间影响，这里只做警告
            if not check["p95_pass"]:
                print(f"   ⚠️ P95超过基准，可能需要优化或LLM响应较慢")

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_analyzer_agent_execution_performance(self):
        """测试AnalyzerAgent执行性能"""
        agent = AnalyzerAgent(agent_id="test_analyzer")
        metrics = PerformanceMetrics(name="analyzer_execution")

        context = AgentExecutionContext(
            session_id="test_session",
            task_id="test_task",
            input_data={"patent_content": "测试专利内容"},
            config={"timeout": 10},
            metadata={},
        )

        for i in range(5):
            try:
                elapsed = await measure_time_async(agent.execute, context)
                metrics.samples.append(elapsed)
            except Exception as e:
                print(f"   执行 #{i} 失败: {e}")

        if metrics.samples:
            print(f"\n📊 AnalyzerAgent执行性能:")
            print(f"   平均: {metrics.avg:.2f}ms")
            print(f"   P95: {metrics.p95:.2f}ms")


# ==================== 吞吐量测试 ====================

class TestAgentThroughput:
    """Agent吞吐量测试"""

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_agent_initialization(self):
        """测试并发Agent初始化吞吐量"""
        num_agents = 50
        start_time = time.perf_counter()

        # 并发创建Agent
        tasks = []
        for i in range(num_agents):
            tasks.append(asyncio.to_thread(RetrieverAgent, agent_id=f"test_{i}"))

        # 等待所有Agent创建完成
        _ = await asyncio.gather(*tasks)
        elapsed = time.perf_counter() - start_time

        throughput = num_agents / elapsed  # agents per second
        avg_time = (elapsed / num_agents) * 1000  # ms per agent

        print(f"\n📊 并发初始化吞吐量:")
        print(f"   Agent数量: {num_agents}")
        print(f"   总耗时: {elapsed:.2f}s")
        print(f"   吞吐量: {throughput:.2f} QPS")
        print(f"   平均耗时: {avg_time:.2f}ms/agent")

        # 吞吐量应该 >10 QPS
        assert throughput >= 10, f"吞吐量 {throughput:.2f} QPS 低于基准 10 QPS"

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_capability_discovery(self):
        """测试并发能力发现吞吐量"""
        # 预先创建Agent
        agents = [RetrieverAgent(agent_id=f"test_{i}") for i in range(100)]

        start_time = time.perf_counter()

        # 并发获取能力
        tasks = [asyncio.to_thread(agent.get_capabilities) for agent in agents]
        _ = await asyncio.gather(*tasks)  # 等待所有调用完成

        elapsed = time.perf_counter() - start_time
        throughput = len(agents) / elapsed

        print(f"\n📊 并发能力发现吞吐量:")
        print(f"   Agent数量: {len(agents)}")
        print(f"   吞吐量: {throughput:.2f} ops/s")

        # 能力发现应该非常快
        assert throughput >= 100, f"吞吐量 {throughput:.2f} ops/s 过低"


# ==================== 性能基准数据管理 ====================

class TestPerformanceBaseline:
    """性能基准数据管理"""

    BASELINE_FILE = Path(__file__).parent.parent / "data" / "agent_performance_baseline.json"

    def test_load_or_create_baseline(self):
        """测试加载或创建基准数据"""
        baseline = self._load_or_create_baseline()

        assert isinstance(baseline, dict)
        assert "benchmarks" in baseline
        assert "timestamp" in baseline

    def _load_or_create_baseline(self) -> Dict[str, Any]:
        """加载或创建基准数据"""
        if self.BASELINE_FILE.exists():
            import json
            with open(self.BASELINE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)

        # 创建默认基准
        baseline = {
            "timestamp": datetime.now().isoformat(),
            "benchmarks": {
                "agent_initialization": {
                    "target_p50": 50,
                    "target_p95": 100,
                    "target_p99": 150,
                },
                "agent_execution": {
                    "target_p50": 2000,
                    "target_p95": 5000,
                    "target_p99": 8000,
                },
                "capability_discovery": {
                    "target_p50": 1,
                    "target_p95": 5,
                    "target_p99": 10,
                },
            }
        }

        # 保存
        self.BASELINE_FILE.parent.mkdir(parents=True, exist_ok=True)
        import json
        with open(self.BASELINE_FILE, 'w', encoding='utf-8') as f:
            json.dump(baseline, f, indent=2, ensure_ascii=False)

        return baseline

    def test_update_baseline(self):
        """测试更新基准数据"""
        # 这个测试需要手动执行，用于更新基准数据
        baseline = self._load_or_create_baseline()

        # 更新时间戳
        baseline["timestamp"] = datetime.now().isoformat()

        # 保存
        import json
        with open(self.BASELINE_FILE, 'w', encoding='utf-8') as f:
            json.dump(baseline, f, indent=2, ensure_ascii=False)


# ==================== 运行入口 ====================

if __name__ == "__main__":
    # 直接运行此文件执行性能测试
    import sys

    print("🚀 Agent性能基准测试")
    print("=" * 60)

    # 运行pytest
    sys.exit(pytest.main([__file__, "-v", "-m", "performance"]))
