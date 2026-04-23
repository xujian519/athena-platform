#!/usr/bin/env python3
from __future__ import annotations
"""
Athena工具评估框架
Tool Evaluation Framework for Athena Platform

基于Anthropic团队的评估驱动优化理念
提供多维度工具评估、基准测试和持续监控能力

核心功能:
1. 多维度评估(功能性、性能、可靠性、可用性、效率、安全)
2. 基准测试和对比
3. 改进建议生成
4. 评估报告生成

使用方法:
    from core.governance.tool_evaluation_framework import ToolEvaluationFramework

    framework = ToolEvaluationFramework()
    result = await framework.evaluate_tool("search.patent")
    report = await framework.generate_evaluation_report([result])
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from statistics import mean
from typing import Any

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

# ================================
# 数据模型
# ================================


class EvaluationMetric(Enum):
    """评估指标"""

    FUNCTIONALITY = "functionality"  # 功能性:覆盖率、准确性、输出质量
    PERFORMANCE = "performance"  # 性能:响应时间、吞吐量
    RELIABILITY = "reliability"  # 可靠性:成功率、稳定性
    USABILITY = "usability"  # 可用性:易用性、文档完善度
    EFFICIENCY = "efficiency"  # 效率:资源消耗比
    SECURITY = "security"  # 安全性:数据保护、权限控制


class EvaluationLevel(Enum):
    """评估等级"""

    EXCELLENT = "excellent"  # 优秀 (90-100分)
    GOOD = "good"  # 良好 (75-89分)
    SATISFACTORY = "satisfactory"  # 满意 (60-74分)
    NEEDS_IMPROVEMENT = "needs_improvement"  # 需改进 (40-59分)
    POOR = "poor"  # 较差 (0-39分)


@dataclass
class MetricScore:
    """指标分数"""

    metric: EvaluationMetric
    score: float  # 0.0 - 1.0
    level: EvaluationLevel
    details: dict[str, Any] = field(default_factory=dict)
    issues: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)


@dataclass
class ToolEvaluationResult:
    """工具评估结果"""

    tool_id: str
    tool_name: str
    overall_score: float  # 0.0 - 1.0
    overall_level: EvaluationLevel
    metric_scores: list[MetricScore] = field(default_factory=list)
    benchmark_comparison: dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "tool_id": self.tool_id,
            "tool_name": self.tool_name,
            "overall_score": self.overall_score,
            "overall_level": self.overall_level.value,
            "metric_scores": [
                {
                    "metric": ms.metric.value,
                    "score": ms.score,
                    "level": ms.level.value,
                    "details": ms.details,
                    "issues": ms.issues,
                    "suggestions": ms.suggestions,
                }
                for ms in self.metric_scores
            ],
            "benchmark_comparison": self.benchmark_comparison,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


# ================================
# 评估框架
# ================================


class ToolEvaluationFramework:
    """
    工具评估框架

    提供多维度工具评估能力

    评估维度:
    1. 功能性(30%):覆盖率、准确性、输出质量
    2. 性能(25%):响应时间、吞吐量
    3. 可靠性(25%):成功率、稳定性
    4. 可用性(10%):易用性、文档完善度
    5. 效率(5%):资源消耗比
    6. 安全性(5%):数据保护、权限控制

    参考:Anthropic团队 - Evaluation-Driven Optimization
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}

        # 指标权重
        self.metric_weights = {
            EvaluationMetric.FUNCTIONALITY: self.config.get("functionality_weight", 0.30),
            EvaluationMetric.PERFORMANCE: self.config.get("performance_weight", 0.25),
            EvaluationMetric.RELIABILITY: self.config.get("reliability_weight", 0.25),
            EvaluationMetric.USABILITY: self.config.get("usability_weight", 0.10),
            EvaluationMetric.EFFICIENCY: self.config.get("efficiency_weight", 0.05),
            EvaluationMetric.SECURITY: self.config.get("security_weight", 0.05),
        }

        # 评估阈值
        self.thresholds = {
            EvaluationLevel.EXCELLENT: self.config.get("excellent_threshold", 0.90),
            EvaluationLevel.GOOD: self.config.get("good_threshold", 0.75),
            EvaluationLevel.SATISFACTORY: self.config.get("satisfactory_threshold", 0.60),
            EvaluationLevel.NEEDS_IMPROVEMENT: self.config.get("needs_improvement_threshold", 0.40),
        }

        # 基准数据(可以从文件加载)
        self.benchmarks: dict[str, dict[str, float]] = {
            # 工具类别 -> 平均分数
            "search": {"functionality": 0.85, "performance": 0.80, "reliability": 0.90},
            "mcp": {"functionality": 0.80, "performance": 0.75, "reliability": 0.85},
            "service": {"functionality": 0.75, "performance": 0.70, "reliability": 0.80},
        }

        # 工具注册中心引用
        self._registry = None

        logger.info("✅ 工具评估框架已创建")

    async def initialize(self) -> bool:
        """初始化评估框架"""
        logger.info("🚀 初始化工具评估框架...")

        try:
            # 获取统一工具注册中心
            from core.governance.unified_tool_registry import get_unified_registry

            self._registry = get_unified_registry()

            # 如果注册中心未初始化,先初始化
            if not self._registry.metadata:
                await self._registry.initialize()

            logger.info("✅ 工具评估框架初始化完成")
            return True

        except Exception as e:
            logger.error(f"❌ 评估框架初始化失败: {e}")
            return False

    async def evaluate_tool(
        self, tool_id: str, test_cases: list[dict[str, Any]] | None = None
    ) -> ToolEvaluationResult:
        """
        评估单个工具

        Args:
            tool_id: 工具ID
            test_cases: 测试用例(可选)

        Returns:
            ToolEvaluationResult
        """
        logger.info(f"📊 开始评估工具: {tool_id}")

        # 获取工具信息
        if not self._registry:
            return self._create_error_result(tool_id, "注册中心未初始化")

        tool_info = self._registry.get_tool_info(tool_id)
        if not tool_info:
            return self._create_error_result(tool_id, "工具不存在")

        # 执行多维度评估
        metric_scores = []

        # 1. 功能性评估
        functionality = await self._evaluate_functionality(tool_id, tool_info, test_cases)
        metric_scores.append(functionality)

        # 2. 性能评估
        performance = await self._evaluate_performance(tool_id, tool_info)
        metric_scores.append(performance)

        # 3. 可靠性评估
        reliability = await self._evaluate_reliability(tool_id, tool_info)
        metric_scores.append(reliability)

        # 4. 可用性评估
        usability = await self._evaluate_usability(tool_id, tool_info)
        metric_scores.append(usability)

        # 5. 效率评估
        efficiency = await self._evaluate_efficiency(tool_id, tool_info)
        metric_scores.append(efficiency)

        # 6. 安全性评估
        security = await self._evaluate_security(tool_id, tool_info)
        metric_scores.append(security)

        # 计算总体分数
        overall_score = sum(ms.score * self.metric_weights[ms.metric] for ms in metric_scores)

        overall_level = self._determine_level(overall_score)

        # 基准对比
        benchmark_comparison = self._compare_with_benchmark(
            tool_id, tool_info.get("category", "service"), metric_scores
        )

        result = ToolEvaluationResult(
            tool_id=tool_id,
            tool_name=tool_info.get("name", tool_id),
            overall_score=overall_score,
            overall_level=overall_level,
            metric_scores=metric_scores,
            benchmark_comparison=benchmark_comparison,
            metadata={
                "category": tool_info.get("category"),
                "total_calls": tool_info.get("total_calls", 0),
                "success_rate": tool_info.get("success_rate", 0.0),
            },
        )

        logger.info(f"✅ 工具评估完成: {tool_id} - 分数: {overall_score:.2f}")
        return result

    async def evaluate_all_tools(
        self, category: Optional[str] = None
    ) -> list[ToolEvaluationResult]:
        """
        评估所有工具或指定类别的工具

        Args:
            category: 工具类别过滤

        Returns:
            评估结果列表
        """
        logger.info("📊 开始批量工具评估...")

        if not self._registry:
            logger.error("❌ 注册中心未初始化")
            return []

        # 获取工具列表
        tools = self._registry.list_tools()

        # 过滤类别
        if category:
            tools = [t for t in tools if t.get("category") == category]

        logger.info(f"将评估 {len(tools)} 个工具")

        # 并发评估(限制并发数)
        results = []
        semaphore = asyncio.Semaphore(5)  # 最多5个并发

        async def evaluate_with_semaphore(tool):
            async with semaphore:
                return await self.evaluate_tool(tool["tool_id"])

        tasks = [evaluate_with_semaphore(tool) for tool in tools]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 过滤异常结果
        valid_results = [r for r in results if isinstance(r, ToolEvaluationResult)]

        logger.info(f"✅ 批量评估完成: {len(valid_results)}/{len(tools)}")
        return valid_results

    async def _evaluate_functionality(
        self, tool_id: str, tool_info: dict[str, Any], test_cases: list[dict[str, Any]]
    ) -> MetricScore:
        """评估功能性"""
        details = {}
        issues = []
        suggestions = []

        # 1. 覆盖率评估
        has_capability = bool(tool_info.get("capabilities"))
        has_input_schema = bool(tool_info.get("input_schema"))
        has_output_schema = bool(tool_info.get("output_schema"))

        coverage_score = (
            (1.0 if has_capability else 0.0) * 0.4
            + (1.0 if has_input_schema else 0.0) * 0.3
            + (1.0 if has_output_schema else 0.0) * 0.3
        )
        details["coverage"] = coverage_score

        if not has_capability:
            issues.append("缺少能力描述")
            suggestions.append("添加工具能力描述")

        # 2. 准确性评估(基于成功率)
        success_rate = tool_info.get("success_rate", 0.0)
        accuracy_score = success_rate
        details["accuracy"] = accuracy_score

        if success_rate < 0.8:
            issues.append(f"成功率偏低 ({success_rate*100:.1f}%)")
            suggestions.append("优化工具实现,提高成功率")

        # 3. 输出质量评估(基于健康分数)
        health_score = tool_info.get("health_score", 1.0)
        quality_score = health_score
        details["quality"] = quality_score

        if health_score < 0.8:
            issues.append(f"健康分数偏低 ({health_score:.2f})")
            suggestions.append("检查工具配置和依赖")

        # 综合分数
        overall_score = coverage_score * 0.3 + accuracy_score * 0.4 + quality_score * 0.3

        return MetricScore(
            metric=EvaluationMetric.FUNCTIONALITY,
            score=overall_score,
            level=self._determine_level(overall_score),
            details=details,
            issues=issues,
            suggestions=suggestions,
        )

    async def _evaluate_performance(self, tool_id: str, tool_info: dict[str, Any]) -> MetricScore:
        """评估性能"""
        details = {}
        issues = []
        suggestions = []

        # 获取平均响应时间
        avg_response_time = tool_info.get("avg_response_time", 0.0)

        # 1. 响应时间评分
        if avg_response_time <= 0:
            response_time_score = 0.5  # 无数据,给中等分
        elif avg_response_time < 1.0:
            response_time_score = 1.0
        elif avg_response_time < 3.0:
            response_time_score = 0.8
        elif avg_response_time < 5.0:
            response_time_score = 0.6
        elif avg_response_time < 10.0:
            response_time_score = 0.4
        else:
            response_time_score = 0.2

        details["response_time"] = avg_response_time
        details["response_time_score"] = response_time_score

        if avg_response_time > 5.0:
            issues.append(f"响应时间过长 ({avg_response_time:.2f}s)")
            suggestions.append("优化工具实现或增加缓存")

        # 2. 吞吐量评分(基于总调用次数)
        total_calls = tool_info.get("total_calls", 0)
        if total_calls > 1000:
            throughput_score = 1.0
        elif total_calls > 500:
            throughput_score = 0.8
        elif total_calls > 100:
            throughput_score = 0.6
        elif total_calls > 10:
            throughput_score = 0.4
        else:
            throughput_score = 0.2

        details["throughput_score"] = throughput_score
        details["total_calls"] = total_calls

        # 综合分数
        overall_score = response_time_score * 0.7 + throughput_score * 0.3

        return MetricScore(
            metric=EvaluationMetric.PERFORMANCE,
            score=overall_score,
            level=self._determine_level(overall_score),
            details=details,
            issues=issues,
            suggestions=suggestions,
        )

    async def _evaluate_reliability(self, tool_id: str, tool_info: dict[str, Any]) -> MetricScore:
        """评估可靠性"""
        details = {}
        issues = []
        suggestions = []

        # 1. 成功率评估
        success_rate = tool_info.get("success_rate", 0.0)
        details["success_rate"] = success_rate

        if success_rate >= 0.95:
            reliability_score = 1.0
        elif success_rate >= 0.85:
            reliability_score = 0.8
        elif success_rate >= 0.70:
            reliability_score = 0.6
        elif success_rate >= 0.50:
            reliability_score = 0.4
        else:
            reliability_score = 0.2

        if success_rate < 0.8:
            issues.append(f"成功率偏低 ({success_rate*100:.1f}%)")
            suggestions.append("增加错误处理和重试机制")

        # 2. 稳定性评估(基于健康分数)
        health_score = tool_info.get("health_score", 1.0)
        details["health_score"] = health_score

        stability_score = health_score

        # 综合分数
        overall_score = reliability_score * 0.7 + stability_score * 0.3

        return MetricScore(
            metric=EvaluationMetric.RELIABILITY,
            score=overall_score,
            level=self._determine_level(overall_score),
            details=details,
            issues=issues,
            suggestions=suggestions,
        )

    async def _evaluate_usability(self, tool_id: str, tool_info: dict[str, Any]) -> MetricScore:
        """评估可用性"""
        details = {}
        issues = []
        suggestions = []

        # 1. 文档完善度
        has_description = bool(tool_info.get("description"))
        has_capabilities = bool(tool_info.get("capabilities"))
        has_input_schema = bool(tool_info.get("input_schema"))

        documentation_score = (
            (1.0 if has_description else 0.0) * 0.4
            + (1.0 if has_capabilities else 0.0) * 0.3
            + (1.0 if has_input_schema else 0.0) * 0.3
        )
        details["documentation_score"] = documentation_score

        if not has_description:
            issues.append("缺少工具描述")
            suggestions.append("添加工具描述文档")

        # 2. 易用性评分(基于工具ID清晰度)
        id_parts = tool_id.split(".")
        clarity_score = min(1.0, len(id_parts) * 0.3)  # 越详细越清晰
        details["clarity_score"] = clarity_score

        # 综合分数
        overall_score = documentation_score * 0.7 + clarity_score * 0.3

        return MetricScore(
            metric=EvaluationMetric.USABILITY,
            score=overall_score,
            level=self._determine_level(overall_score),
            details=details,
            issues=issues,
            suggestions=suggestions,
        )

    async def _evaluate_efficiency(self, tool_id: str, tool_info: dict[str, Any]) -> MetricScore:
        """评估效率"""
        details = {}
        issues = []
        suggestions = []

        # 基于响应时间估算资源效率
        avg_response_time = tool_info.get("avg_response_time", 0.0)

        if avg_response_time <= 0:
            efficiency_score = 0.5
        elif avg_response_time < 2.0:
            efficiency_score = 1.0
        elif avg_response_time < 5.0:
            efficiency_score = 0.7
        else:
            efficiency_score = 0.4

        details["efficiency_score"] = efficiency_score

        if efficiency_score < 0.6:
            suggestions.append("考虑优化算法或使用更高效的实现")

        return MetricScore(
            metric=EvaluationMetric.EFFICIENCY,
            score=efficiency_score,
            level=self._determine_level(efficiency_score),
            details=details,
            issues=issues,
            suggestions=suggestions,
        )

    async def _evaluate_security(self, tool_id: str, tool_info: dict[str, Any]) -> MetricScore:
        """评估安全性"""
        details = {}
        issues = []
        suggestions = []

        # 1. 依赖安全性
        dependencies = tool_info.get("dependencies", [])
        has_external_deps = len(dependencies) > 0

        # MCP工具依赖外部服务器
        if tool_id.startswith("mcp.") or has_external_deps:
            security_score = 0.8  # 外部依赖,给中等分数
            suggestions.append("定期检查外部依赖的安全性")
        else:
            security_score = 1.0  # 内部工具,给高分

        details["has_external_deps"] = has_external_deps

        # 2. 数据保护(简化评估)
        # 实际应用中需要检查工具是否处理敏感数据
        data_protection_score = 0.9  # 默认较高分数
        details["data_protection_score"] = data_protection_score

        # 综合分数
        overall_score = security_score * 0.6 + data_protection_score * 0.4

        return MetricScore(
            metric=EvaluationMetric.SECURITY,
            score=overall_score,
            level=self._determine_level(overall_score),
            details=details,
            issues=issues,
            suggestions=suggestions,
        )

    def _determine_level(self, score: float) -> EvaluationLevel:
        """根据分数确定等级"""
        if score >= self.thresholds[EvaluationLevel.EXCELLENT]:
            return EvaluationLevel.EXCELLENT
        elif score >= self.thresholds[EvaluationLevel.GOOD]:
            return EvaluationLevel.GOOD
        elif score >= self.thresholds[EvaluationLevel.SATISFACTORY]:
            return EvaluationLevel.SATISFACTORY
        elif score >= self.thresholds[EvaluationLevel.NEEDS_IMPROVEMENT]:
            return EvaluationLevel.NEEDS_IMPROVEMENT
        else:
            return EvaluationLevel.POOR

    def _compare_with_benchmark(
        self, tool_id: str, category: str, metric_scores: list[MetricScore]
    ) -> dict[str, float]:
        """与基准对比"""
        comparison = {}

        benchmark = self.benchmarks.get(category, {})

        for ms in metric_scores:
            metric_name = ms.metric.value
            if metric_name in benchmark:
                diff = ms.score - benchmark[metric_name]
                comparison[metric_name] = diff

        return comparison

    def _create_error_result(self, tool_id: str, error_message: str) -> ToolEvaluationResult:
        """创建错误结果"""
        return ToolEvaluationResult(
            tool_id=tool_id,
            tool_name=tool_id,
            overall_score=0.0,
            overall_level=EvaluationLevel.POOR,
            metadata={"error": error_message},
        )

    async def generate_evaluation_report(
        self, results: list[ToolEvaluationResult], output_format: str = "markdown"
    ) -> str:
        """
        生成评估报告

        Args:
            results: 评估结果列表
            output_format: 输出格式 (markdown, json, html)

        Returns:
            报告内容
        """
        if output_format == "json":
            return json.dumps([r.to_dict() for r in results], ensure_ascii=False, indent=2)

        # Markdown报告
        lines = []
        lines.append("# Athena工具评估报告")
        lines.append("")
        lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**评估工具数**: {len(results)}")
        lines.append("")

        # 总体统计
        lines.append("## 📊 总体统计")
        lines.append("")

        avg_score = mean(r.overall_score for r in results)
        lines.append(f"- **平均分数**: {avg_score:.2f}")
        lines.append("")

        # 按等级统计
        level_counts = {}
        for result in results:
            level = result.overall_level.value
            level_counts[level] = level_counts.get(level, 0) + 1

        lines.append("**等级分布**:")
        for level, count in sorted(level_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = count / len(results) * 100
            lines.append(f"- {level}: {count} ({percentage:.1f}%)")
        lines.append("")

        # 详细评估结果
        lines.append("## 📋 详细评估结果")
        lines.append("")

        # 按分数排序
        sorted_results = sorted(results, key=lambda r: r.overall_score, reverse=True)

        for i, result in enumerate(sorted_results, 1):
            level_icon = {
                EvaluationLevel.EXCELLENT: "🌟",
                EvaluationLevel.GOOD: "✅",
                EvaluationLevel.SATISFACTORY: "👍",
                EvaluationLevel.NEEDS_IMPROVEMENT: "⚠️",
                EvaluationLevel.POOR: "❌",
            }.get(result.overall_level, "📌")

            lines.append(f"### {i}. {level_icon} {result.tool_name}")
            lines.append("")
            lines.append(f"**工具ID**: `{result.tool_id}`")
            lines.append(f"**总分**: {result.overall_score:.2f} ({result.overall_level.value})")
            lines.append("")

            # 指标分数
            lines.append("**指标分数**:")
            for ms in result.metric_scores:
                lines.append(f"- {ms.metric.value}: {ms.score:.2f}")
                if ms.issues:
                    lines.append(f"  - 问题: {', '.join(ms.issues)}")
                if ms.suggestions:
                    lines.append(f"  - 建议: {', '.join(ms.suggestions)}")
            lines.append("")

            # 基准对比
            if result.benchmark_comparison:
                lines.append("**基准对比**:")
                for metric, diff in result.benchmark_comparison.items():
                    icon = "📈" if diff > 0 else "📉" if diff < 0 else "➡️"
                    lines.append(f"- {metric}: {icon} {diff:+.2f}")
                lines.append("")

        return "\n".join(lines)

    async def save_evaluation_report(
        self,
        results: list[ToolEvaluationResult],
        output_path: Path,
        output_format: str = "markdown",
    ):
        """保存评估报告到文件"""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        report = await self.generate_evaluation_report(results, output_format)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)

        logger.info(f"✅ 评估报告已保存: {output_path}")


# ================================
# 测试代码
# ================================


async def main():
    """主函数(用于测试)"""
    print("=" * 80)
    print("📊 工具评估框架测试")
    print("=" * 80)
    print()

    framework = ToolEvaluationFramework()

    # 初始化
    print("初始化评估框架...")
    success = await framework.initialize()

    if not success:
        print("❌ 初始化失败")
        return

    print()

    # 评估几个工具
    test_tools = ["search.patent", "mcp.bing-cn-search", "service.agent_manager"]

    results = []
    for tool_id in test_tools:
        print(f"评估工具: {tool_id}")
        result = await framework.evaluate_tool(tool_id)
        results.append(result)
        print(f"分数: {result.overall_score:.2f} ({result.overall_level.value})")
        print()

    # 生成报告
    report = await framework.generate_evaluation_report(results)
    print(report)

    # 保存报告
    output_path = Path("/Users/xujian/Athena工作平台/reports/tool_evaluation_report.md")
    await framework.save_evaluation_report(results, output_path)

    print("=" * 80)
    print("✅ 测试完成")
    print("=" * 80)


# 入口点: @async_main装饰器已添加到main函数
