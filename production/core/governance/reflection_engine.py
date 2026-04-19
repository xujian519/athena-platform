#!/usr/bin/env python3
from __future__ import annotations
"""
Athena反思引擎
Reflection Engine for Athena Platform

基于Andrew Ng的Reflection机制实现
提供执行后反思、工具选择反思和性能反思能力

核心功能:
1. Execution Reflection: 执行反思(工具调用后立即评估)
2. Selection Reflection: 选择反思(评估工具选择是否合理)
3. Performance Reflection: 性能反思(分析执行效率)
4. Score Adjustment: 分数调整(动态调整工具评分)

使用方法:
    from core.governance.reflection_engine import ReflectionEngine, get_reflection_engine

    engine = get_reflection_engine()
    reflection = await engine.reflect_on_execution(
        tool_id="search.patent",
        result=result,
        context={}
    )
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

# ================================
# 数据模型
# ================================


class ReflectionType(Enum):
    """反思类型"""

    EXECUTION = "execution"  # 执行反思
    SELECTION = "selection"  # 选择反思
    PERFORMANCE = "performance"  # 性能反思
    STRATEGY = "strategy"  # 策略反思


class ReflectionOutcome(Enum):
    """反思结果"""

    EXCELLENT = "excellent"  # 优秀
    GOOD = "good"  # 良好
    ACCEPTABLE = "acceptable"  # 可接受
    POOR = "poor"  # 较差
    TERRIBLE = "terrible"  # 很差


@dataclass
class ReflectionResult:
    """反思结果"""

    reflection_type: ReflectionType
    tool_id: str
    outcome: ReflectionOutcome
    score: float  # 0.0 - 1.0
    insights: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    adjustments: dict[str, float] = field(default_factory=dict)  # 工具ID -> 分数调整
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "reflection_type": self.reflection_type.value,
            "tool_id": self.tool_id,
            "outcome": self.outcome.value,
            "score": self.score,
            "insights": self.insights,
            "suggestions": self.suggestions,
            "adjustments": self.adjustments,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class ReflectionHistory:
    """反思历史"""

    tool_id: str
    reflections: list[ReflectionResult] = field(default_factory=list)
    total_reflections: int = 0
    average_score: float = 0.0
    trend: str = "stable"  # improving, stable, declining

    def add_reflection(self, reflection: ReflectionResult) -> None:
        """添加反思记录"""
        self.reflections.append(reflection)
        self.total_reflections += 1

        # 更新平均分数
        self.average_score = sum(r.score for r in self.reflections) / len(self.reflections)

        # 分析趋势
        if len(self.reflections) >= 3:
            recent = self.reflections[-3:]
            if all(
                r.score > self.reflections[-4].score for r in recent if len(self.reflections) > 3
            ):
                self.trend = "improving"
            elif all(
                r.score < self.reflections[-4].score for r in recent if len(self.reflections) > 3
            ):
                self.trend = "declining"
            else:
                self.trend = "stable"


# ================================
# 反思引擎
# ================================


class ReflectionEngine:
    """
    反思引擎

    基于Andrew Ng的Reflection机制,提供多层次反思能力

    核心功能:
    1. 执行反思:评估工具执行结果的质量
    2. 选择反思:评估工具选择的合理性
    3. 性能反思:分析执行效率
    4. 分数调整:动态调整工具评分

    参考:Andrew Ng - Agentic Design Patterns
    """

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}

        # 反思历史 - 使用正确的工厂方法
        self.history: dict[str, ReflectionHistory] = {}

        # 反思阈值
        self.thresholds = {
            "excellent": self.config.get("excellent_threshold", 0.9),
            "good": self.config.get("good_threshold", 0.75),
            "acceptable": self.config.get("acceptable_threshold", 0.6),
            "poor": self.config.get("poor_threshold", 0.4),
        }

        # 反思模板
        self.insight_templates = {
            "execution_success": [
                "工具 {tool} 执行成功,返回了 {result_count} 个结果",
                "工具调用响应时间: {response_time:.2f}s,表现良好",
            ],
            "execution_failure": ["工具 {tool} 执行失败: {error}", "可能原因: {possible_cause}"],
            "selection_optimal": ["工具 {tool} 是当前最优选择", "匹配度: {match_score:.2f}"],
            "selection_suboptimal": [
                "工具 {tool} 可能不是最优选择",
                "建议考虑: {alternative_tools}",
            ],
            "performance_good": ["执行效率: {efficiency:.2f} results/s", "资源使用合理"],
            "performance_poor": [
                "执行时间过长: {execution_time:.2f}s",
                "建议优化: {optimization_suggestion}",
            ],
        }

        logger.info("✅ 反思引擎已创建")

    async def reflect_on_execution(
        self, tool_id: str, result: Any, context: dict[str, Any], execution_time: float = 0.0
    ) -> ReflectionResult:
        """
        执行反思

        评估工具执行结果的质量

        Args:
            tool_id: 工具ID
            result: 执行结果
            context: 执行上下文
            execution_time: 执行时间

        Returns:
            ReflectionResult
        """
        logger.debug(f"🤔 执行反思: {tool_id}")

        insights = []
        suggestions = []
        score = 0.0

        # 分析执行结果
        success = self._is_execution_successful(result)
        result_quality = self._evaluate_result_quality(result)
        efficiency = self._evaluate_efficiency(result, execution_time)

        # 生成洞察
        if success:
            insights.append(
                self.insight_templates["execution_success"][0].format(
                    tool=tool_id, result_count=self._count_results(result)
                )
            )
            if execution_time > 0:
                insights.append(
                    self.insight_templates["execution_success"][1].format(
                        response_time=execution_time
                    )
                )
        else:
            error = self._extract_error(result)
            insights.append(
                self.insight_templates["execution_failure"][0].format(tool=tool_id, error=error)
            )
            insights.append(
                self.insight_templates["execution_failure"][1].format(
                    possible_cause=self._guess_possible_cause(error)
                )
            )

        # 计算分数
        score = (
            (1.0 if success else 0.0) * 0.5  # 成功率权重50%
            + result_quality * 0.3  # 结果质量权重30%
            + efficiency * 0.2  # 效率权重20%
        )

        # 生成建议
        if score < self.thresholds["acceptable"]:
            suggestions.append("工具执行质量较低,建议检查工具配置或尝试替代工具")
        if execution_time > 10.0:
            suggestions.append("执行时间过长,建议优化工具实现或增加缓存")

        # 确定反思结果
        outcome = self._determine_outcome(score)

        # 计算分数调整
        adjustment = self._calculate_score_adjustment(score, execution_time)
        adjustments = {tool_id: adjustment}

        reflection = ReflectionResult(
            reflection_type=ReflectionType.EXECUTION,
            tool_id=tool_id,
            outcome=outcome,
            score=score,
            insights=insights,
            suggestions=suggestions,
            adjustments=adjustments,
            metadata={
                "execution_time": execution_time,
                "success": success,
                "result_quality": result_quality,
                "efficiency": efficiency,
            },
        )

        # 保存到历史
        self._save_to_history(tool_id, reflection)

        return reflection

    async def reflect_on_selection(
        self,
        selected_tool_id: str,
        alternative_tools: list[dict[str, Any]],        context: dict[str, Any],    ) -> ReflectionResult:
        """
        选择反思

        评估工具选择的合理性

        Args:
            selected_tool_id: 选择的工具ID
            alternative_tools: 可替代工具列表
            context: 执行上下文

        Returns:
            ReflectionResult
        """
        logger.debug(f"🤔 选择反思: {selected_tool_id}")

        insights = []
        suggestions = []
        score = 0.0

        # 分析选择质量
        selected_score = context.get("selected_tool_score", 0.0)
        best_alternative_score = max([t.get("score", 0.0) for t in alternative_tools], default=0.0)

        # 生成洞察
        if selected_score >= best_alternative_score:
            insights.append(
                self.insight_templates["selection_optimal"][0].format(tool=selected_tool_id)
            )
            insights.append(
                self.insight_templates["selection_optimal"][1].format(match_score=selected_score)
            )
            score = 0.9
        else:
            gap = best_alternative_score - selected_score
            insights.append(
                self.insight_templates["selection_suboptimal"][0].format(tool=selected_tool_id)
            )

            # 找出更好的替代工具
            better_tools = [
                t["name"] for t in alternative_tools if t.get("score", 0.0) > selected_score
            ]
            insights.append(
                self.insight_templates["selection_suboptimal"][1].format(
                    alternative_tools=", ".join(better_tools[:3])
                )
            )

            suggestions.append(f"建议下次选择匹配度更高的工具(差距: {gap:.2f})")
            score = max(0.5, 1.0 - gap)  # 分数根据差距降低

        # 确定反思结果
        outcome = self._determine_outcome(score)

        # 计算分数调整
        adjustment = (score - 0.5) * 0.1  # 选择反思的调整幅度较小
        adjustments = {selected_tool_id: adjustment}

        # 对更好的工具给予正面调整
        for tool in alternative_tools:
            if tool.get("score", 0.0) > selected_score:
                tool_id = tool.get("tool_id")
                if tool_id:
                    adjustments[tool_id] = 0.05

        reflection = ReflectionResult(
            reflection_type=ReflectionType.SELECTION,
            tool_id=selected_tool_id,
            outcome=outcome,
            score=score,
            insights=insights,
            suggestions=suggestions,
            adjustments=adjustments,
            metadata={
                "selected_score": selected_score,
                "best_alternative_score": best_alternative_score,
                "alternatives_count": len(alternative_tools),
            },
        )

        self._save_to_history(selected_tool_id, reflection)

        return reflection

    async def reflect_on_performance(
        self, tool_id: str, execution_history: list[dict[str, Any]], context: dict[str, Any]
    ) -> ReflectionResult:
        """
        性能反思

        分析工具的执行效率趋势

        Args:
            tool_id: 工具ID
            execution_history: 执行历史记录
            context: 执行上下文

        Returns:
            ReflectionResult
        """
        logger.debug(f"🤔 性能反思: {tool_id}")

        insights = []
        suggestions = []
        score = 0.0

        if not execution_history:
            return ReflectionResult(
                reflection_type=ReflectionType.PERFORMANCE,
                tool_id=tool_id,
                outcome=ReflectionOutcome.ACCEPTABLE,
                score=0.5,
                insights=["暂无执行历史"],
                suggestions=["需要更多执行数据才能进行性能分析"],
            )

        # 分析性能指标
        avg_time = sum(h.get("execution_time", 0) for h in execution_history) / len(
            execution_history
        )
        success_rate = sum(1 for h in execution_history if h.get("success", False)) / len(
            execution_history
        )

        # 计算效率
        total_results = sum(h.get("result_count", 0) for h in execution_history)
        total_time = sum(h.get("execution_time", 0) for h in execution_history)
        efficiency = total_results / total_time if total_time > 0 else 0

        # 生成洞察
        insights.append(f"平均执行时间: {avg_time:.2f}s")
        insights.append(f"成功率: {success_rate*100:.1f}%")
        insights.append(f"效率: {efficiency:.2f} results/s")

        if success_rate >= 0.9 and avg_time < 2.0:
            insights.extend(self.insight_templates["performance_good"])
            score = 0.9
        elif success_rate < 0.7 or avg_time > 5.0:
            insights.extend(self.insight_templates["performance_poor"][:1])
            if avg_time > 5.0:
                insights.append(
                    self.insight_templates["performance_poor"][1].format(
                        execution_time=avg_time, optimization_suggestion="考虑增加缓存或优化算法"
                    )
                )
            score = 0.4
        else:
            score = 0.7

        # 生成建议
        if success_rate < 0.8:
            suggestions.append("成功率偏低,建议检查工具稳定性或增加错误处理")
        if avg_time > 3.0:
            suggestions.append("执行时间较长,建议考虑使用更快的替代工具")

        # 确定反思结果
        outcome = self._determine_outcome(score)

        reflection = ReflectionResult(
            reflection_type=ReflectionType.PERFORMANCE,
            tool_id=tool_id,
            outcome=outcome,
            score=score,
            insights=insights,
            suggestions=suggestions,
            metadata={
                "avg_execution_time": avg_time,
                "success_rate": success_rate,
                "efficiency": efficiency,
                "total_executions": len(execution_history),
            },
        )

        self._save_to_history(tool_id, reflection)

        return reflection

    async def reflect_on_strategy(
        self, task_result: Any, steps: list[Any], context: dict[str, Any]
    ) -> ReflectionResult:
        """
        策略反思

        评估整体任务执行策略

        Args:
            task_result: 任务结果
            steps: 执行步骤
            context: 执行上下文

        Returns:
            ReflectionResult
        """
        logger.debug("🤔 策略反思")

        insights = []
        suggestions = []
        score = 0.0

        # 分析任务完成度
        success = getattr(task_result, "success", False)
        total_steps = len(steps)
        successful_steps = sum(1 for s in steps if getattr(s, "success", True))

        # 生成洞察
        if success:
            insights.append(f"任务成功完成,共执行 {total_steps} 步")
            score = 0.9
        else:
            insights.append(f"任务未完成,成功步数: {successful_steps}/{total_steps}")
            score = 0.5

        # 分析工具使用效率
        unique_tools = len({getattr(s, "tool_id", None) for s in steps if hasattr(s, "tool_id")})
        insights.append(f"使用了 {unique_tools} 个不同的工具")

        # 确定反思结果
        outcome = self._determine_outcome(score)

        reflection = ReflectionResult(
            reflection_type=ReflectionType.STRATEGY,
            tool_id="strategy",
            outcome=outcome,
            score=score,
            insights=insights,
            suggestions=suggestions,
            metadata={
                "total_steps": total_steps,
                "successful_steps": successful_steps,
                "unique_tools": unique_tools,
            },
        )

        return reflection

    # ================================
    # 辅助方法
    # ================================

    def _is_execution_successful(self, result: Any) -> bool:
        """判断执行是否成功"""
        if result is None:
            return False

        if isinstance(result, dict):
            return result.get("success", True) and not result.get("error")

        return True

    def _evaluate_result_quality(self, result: Any) -> float:
        """评估结果质量(0-1)"""
        if result is None:
            return 0.0

        if isinstance(result, dict):
            # 有结果数据
            if result.get("result"):
                return 0.9
            if result.get("data"):
                return 0.9
            if result.get("items"):
                return 0.9

        # 默认质量
        return 0.7

    def _evaluate_efficiency(self, result: Any, execution_time: float) -> float:
        """评估执行效率(0-1)"""
        if execution_time <= 0:
            return 0.5

        # 根据执行时间评分
        if execution_time < 1.0:
            return 1.0
        elif execution_time < 3.0:
            return 0.8
        elif execution_time < 5.0:
            return 0.6
        elif execution_time < 10.0:
            return 0.4
        else:
            return 0.2

    def _count_results(self, result: Any) -> int:
        """统计结果数量"""
        if result is None:
            return 0

        if isinstance(result, dict):
            for key in ["result", "data", "items", "results"]:
                value = result.get(key)
                if isinstance(value, (list, dict)):
                    return len(value)

        if isinstance(result, (list, dict)):
            return len(result)

        return 1

    def _extract_error(self, result: Any) -> str:
        """提取错误信息"""
        if isinstance(result, dict):
            return result.get("error", "Unknown error") or "Unknown error"
        return str(result)

    def _guess_possible_cause(self, error: str) -> str:
        """猜测可能的错误原因"""
        error_lower = error.lower()

        if "timeout" in error_lower:
            return "超时,可能是工具响应慢或网络问题"
        elif "not found" in error_lower or "404" in error_lower:
            return "资源不存在"
        elif "permission" in error_lower or "403" in error_lower:
            return "权限不足"
        elif "connection" in error_lower:
            return "连接问题"
        else:
            return "工具配置或实现问题"

    def _determine_outcome(self, score: float) -> ReflectionOutcome:
        """根据分数确定反思结果"""
        if score >= self.thresholds["excellent"]:
            return ReflectionOutcome.EXCELLENT
        elif score >= self.thresholds["good"]:
            return ReflectionOutcome.GOOD
        elif score >= self.thresholds["acceptable"]:
            return ReflectionOutcome.ACCEPTABLE
        elif score >= self.thresholds["poor"]:
            return ReflectionOutcome.POOR
        else:
            return ReflectionOutcome.TERRIBLE

    def _calculate_score_adjustment(self, score: float, execution_time: float) -> float:
        """计算分数调整值"""
        # 基础调整
        adjustment = (score - 0.5) * 0.2

        # 时间惩罚
        if execution_time > 10.0:
            adjustment -= 0.1

        # 时间奖励
        if execution_time < 1.0:
            adjustment += 0.05

        # 限制调整范围
        return max(-0.2, min(0.2, adjustment))

    def _save_to_history(self, tool_id: str, reflection: ReflectionResult) -> Any:
        """保存反思到历史"""
        if tool_id not in self.history:
            # 正确创建ReflectionHistory实例
            self.history[tool_id] = ReflectionHistory(tool_id=tool_id)

        self.history[tool_id].add_reflection(reflection)

    def get_tool_history(self, tool_id: str) -> ReflectionHistory | None:
        """获取工具的反思历史"""
        return self.history.get(tool_id)

    def get_all_history(self) -> dict[str, ReflectionHistory]:
        """获取所有反思历史"""
        return dict(self.history)

    def clear_history(self, tool_id: str | None = None) -> None:
        """清除反思历史"""
        if tool_id:
            self.history.pop(tool_id, None)
        else:
            self.history.clear()


# ================================
# 全局单例
# ================================

_reflection_engine: ReflectionEngine | None = None


def get_reflection_engine() -> ReflectionEngine:
    """获取反思引擎单例"""
    global _reflection_engine
    if _reflection_engine is None:
        _reflection_engine = ReflectionEngine()
    return _reflection_engine


# ================================
# 测试代码
# ================================


async def main():
    """主函数(用于测试)"""
    print("=" * 80)
    print("🤔 反思引擎测试")
    print("=" * 80)
    print()

    engine = get_reflection_engine()

    # 测试执行反思
    print("测试1: 执行反思(成功)")
    result1 = {
        "success": True,
        "result": {"items": ["item1", "item2", "item3"]},
        "execution_time": 1.5,
    }
    reflection1 = await engine.reflect_on_execution("search.patent", result1, {}, 1.5)
    print(f"分数: {reflection1.score:.2f}")
    print(f"结果: {reflection1.outcome.value}")
    print(f"洞察: {reflection1.insights}")
    print()

    # 测试执行反思(失败)
    print("测试2: 执行反思(失败)")
    result2 = {"success": False, "error": "Connection timeout"}
    reflection2 = await engine.reflect_on_execution("search.patent", result2, {}, 15.0)
    print(f"分数: {reflection2.score:.2f}")
    print(f"结果: {reflection2.outcome.value}")
    print(f"洞察: {reflection2.insights}")
    print()

    # 测试选择反思
    print("测试3: 选择反思")
    selected = "search.patent"
    alternatives = [
        {"tool_id": "search.web", "name": "Web Search", "score": 0.7},
        {"tool_id": "search.patent", "name": "Patent Search", "score": 0.9},
    ]
    reflection3 = await engine.reflect_on_selection(
        selected, alternatives, {"selected_tool_score": 0.9}
    )
    print(f"分数: {reflection3.score:.2f}")
    print(f"结果: {reflection3.outcome.value}")
    print(f"洞察: {reflection3.insights}")
    print()

    # 测试性能反思
    print("测试4: 性能反思")
    history = [
        {"success": True, "execution_time": 1.2, "result_count": 10},
        {"success": True, "execution_time": 1.5, "result_count": 15},
        {"success": True, "execution_time": 1.3, "result_count": 12},
    ]
    reflection4 = await engine.reflect_on_performance("search.patent", history, {})
    print(f"分数: {reflection4.score:.2f}")
    print(f"结果: {reflection4.outcome.value}")
    print(f"洞察: {reflection4.insights}")
    print()

    print("=" * 80)
    print("✅ 测试完成")
    print("=" * 80)


# 入口点: @async_main装饰器已添加到main函数
