#!/usr/bin/env python3
"""
工具调用集成器 - 第二阶段
Tool Call Ensemble - Phase 2

核心功能:
1. 多策略工具路由集成
2. 工具组合优化
3. 执行结果聚合
4. 性能自适应调整

作者: 小诺·双鱼公主
版本: v1.0.0 "工具集成"
创建: 2026-01-12
"""

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


logger = logging.getLogger(__name__)


class RoutingStrategy(Enum):
    """路由策略类型"""

    SEMANTIC = "semantic"  # 语义匹配
    RULE_BASED = "rule_based"  # 规则匹配
    LEARNING_BASED = "learning"  # 学习型
    ENSEMBLE = "ensemble"  # 集成型
    ADAPTIVE = "adaptive"  # 自适应型


@dataclass
class ToolSelection:
    """工具选择"""

    strategy: RoutingStrategy
    tools: list[str]
    confidence: float
    reasoning: str
    execution_plan: str  # single, parallel, sequential
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolExecutionResult:
    """工具执行结果"""

    tool_name: str
    success: bool
    result: Any
    execution_time: float
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EnsembleToolResult:
    """集成工具调用结果"""

    selected_tools: list[str]
    execution_plan: str
    individual_results: list[ToolExecutionResult]
    aggregated_result: Any
    success: bool
    total_execution_time: float
    strategy_used: RoutingStrategy
    confidence: float
    reasoning: str


class ToolCallEnsemble:
    """工具调用集成器"""

    def __init__(self):
        self.name = "工具调用集成器 v1.0"
        self.version = "1.0.0"

        # 路由策略注册表
        self.strategies: dict[RoutingStrategy, Any] = {}

        # 工具注册表
        self.tool_registry: dict[str, dict[str, Any]] = {}

        # 策略性能历史
        self.strategy_performance: dict[str, list[float]] = defaultdict(list)

        # 策略权重(动态调整)
        self.strategy_weights: dict[str, float] = {
            "semantic": 0.30,
            "rule_based": 0.25,
            "learning": 0.25,
            "ensemble": 0.20,
        }

        # 工具组合缓存
        self.combination_cache: dict[str, list[str]] = {}

        # 统计信息
        self.stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "single_tool_calls": 0,
            "parallel_calls": 0,
            "sequential_calls": 0,
            "avg_execution_time": 0.0,
            "strategy_usage": defaultdict(int),
        }

        logger.info(f"🔧 {self.name} 初始化完成")

    def register_tool(self, tool_name: str, metadata: dict[str, Any]):
        """注册工具"""
        self.tool_registry[tool_name] = {**metadata, "registered_at": datetime.now()}
        logger.info(f"✅ 工具已注册: {tool_name}")

    async def execute(
        self,
        intent: str,
        parameters: dict[str, Any],        context: dict[str, Any] | None = None,
        strategy: RoutingStrategy | None = None,
    ) -> EnsembleToolResult:
        """
        执行集成工具调用

        Args:
            intent: 用户意图
            parameters: 参数
            context: 上下文
            strategy: 指定策略(可选)

        Returns:
            EnsembleToolResult: 集成结果
        """
        import time

        start_time = time.time()

        self.stats["total_calls"] += 1

        # 1. 选择策略
        if strategy is None:
            strategy = self._select_strategy(intent, context)

        # 2. 获取各策略的工具选择
        selections = await self._get_strategy_selections(intent, parameters, context)

        # 3. 集成选择结果
        final_selection = self._ensemble_selections(selections, strategy)

        # 4. 执行工具
        execution_results = await self._execute_tools(
            final_selection.tools, final_selection.execution_plan, parameters, context
        )

        # 5. 聚合结果
        aggregated_result = self._aggregate_results(execution_results)

        # 6. 计算统计
        total_time = time.time() - start_time
        success = all(r.success for r in execution_results) if execution_results else False

        self.stats["successful_calls"] += success
        self.stats["avg_execution_time"] = (
            self.stats["avg_execution_time"] * (self.stats["total_calls"] - 1) + total_time
        ) / self.stats["total_calls"]
        self.stats["strategy_usage"][strategy.value] += 1

        if final_selection.execution_plan == "single":
            self.stats["single_tool_calls"] += 1
        elif final_selection.execution_plan == "parallel":
            self.stats["parallel_calls"] += 1
        else:
            self.stats["sequential_calls"] += 1

        # 7. 更新策略性能
        self._update_strategy_performance(strategy.value, success)

        return EnsembleToolResult(
            selected_tools=final_selection.tools,
            execution_plan=final_selection.execution_plan,
            individual_results=execution_results,
            aggregated_result=aggregated_result,
            success=success,
            total_execution_time=total_time,
            strategy_used=strategy,
            confidence=final_selection.confidence,
            reasoning=final_selection.reasoning,
        )

    def _select_strategy(self, intent: str, context: dict[str, Any]) -> RoutingStrategy:
        """选择路由策略"""
        # 基于意图选择
        intent_strategy_map = {
            "patent_analysis": RoutingStrategy.SEMANTIC,
            "coding": RoutingStrategy.LEARNING_BASED,
            "daily_chat": RoutingStrategy.RULE_BASED,
            "legal_consulting": RoutingStrategy.SEMANTIC,
            "data_analysis": RoutingStrategy.LEARNING_BASED,
        }

        base_strategy = intent_strategy_map.get(intent, RoutingStrategy.ENSEMBLE)

        # 根据性能动态调整
        if self._should_use_adaptive():
            return RoutingStrategy.ADAPTIVE

        return base_strategy

    def _should_use_adaptive(self) -> bool:
        """判断是否使用自适应策略"""
        # 如果有足够的性能数据,使用自适应
        return any(len(perf_history) >= 10 for perf_history in self.strategy_performance.values())

    async def _get_strategy_selections(
        self, intent: str, parameters: dict[str, Any], context: dict[str, Any]
    ) -> list[ToolSelection]:
        """获取各策略的选择结果"""
        selections = []

        # 1. 语义匹配策略
        semantic_selection = await self._semantic_strategy(intent, parameters, context)
        if semantic_selection:
            selections.append(semantic_selection)

        # 2. 规则匹配策略
        rule_selection = await self._rule_based_strategy(intent, parameters, context)
        if rule_selection:
            selections.append(rule_selection)

        # 3. 学习型策略
        learning_selection = await self._learning_strategy(intent, parameters, context)
        if learning_selection:
            selections.append(learning_selection)

        return selections

    async def _semantic_strategy(
        self, intent: str, parameters: dict[str, Any], context: dict[str, Any]
    ) -> ToolSelection | None:
        """语义匹配策略"""
        try:
            # 基于意图语义匹配工具
            intent_tool_map = {
                "patent_analysis": ["patent", "xiaona", "knowledge_graph"],
                "coding": ["coding_assistant", "optimization"],
                "daily_chat": ["daily_chat"],
                "legal_consulting": ["xiaona", "legal"],
                "data_analysis": ["nlp", "knowledge_graph"],
            }

            candidate_tools = intent_tool_map.get(intent, [])
            if not candidate_tools:
                return None

            # 过滤可用工具
            available_tools = [t for t in candidate_tools if t in self.tool_registry]

            if not available_tools:
                return None

            # 根据参数复杂度决定工具数量
            complexity_score = self._calculate_complexity(parameters)

            if complexity_score < 0.3:
                # 简单任务: 单个工具
                selected_tools = [available_tools[0]]
                execution_plan = "single"
            elif complexity_score < 0.7:
                # 中等任务: 并行执行
                selected_tools = available_tools[:2]
                execution_plan = "parallel"
            else:
                # 复杂任务: 顺序执行
                selected_tools = available_tools
                execution_plan = "sequential"

            return ToolSelection(
                strategy=RoutingStrategy.SEMANTIC,
                tools=selected_tools,
                confidence=0.85,
                reasoning=f"语义匹配: 意图'{intent}' → 工具{selected_tools}",
                execution_plan=execution_plan,
                metadata={"complexity_score": complexity_score},
            )

        except Exception as e:
            logger.error(f"❌ 语义策略失败: {e}")
            return None

    async def _rule_based_strategy(
        self, intent: str, parameters: dict[str, Any], context: dict[str, Any]
    ) -> ToolSelection | None:
        """规则匹配策略"""
        try:
            # 定义规则
            rules = [
                {
                    "condition": lambda i, p: i == "patent_analysis" and "patent_number" in p,
                    "tools": ["patent"],
                    "plan": "single",
                    "confidence": 0.95,
                },
                {
                    "condition": lambda i, p: i == "coding" and "requirements" in p,
                    "tools": ["coding_assistant"],
                    "plan": "single",
                    "confidence": 0.92,
                },
                {
                    "condition": lambda i, p: i == "daily_chat",
                    "tools": ["daily_chat"],
                    "plan": "single",
                    "confidence": 0.90,
                },
                {
                    "condition": lambda i, p: i == "legal_consulting",
                    "tools": ["xiaona", "legal"],
                    "plan": "parallel",
                    "confidence": 0.85,
                },
            ]

            for rule in rules:
                if rule["condition"](intent, parameters):
                    return ToolSelection(
                        strategy=RoutingStrategy.RULE_BASED,
                        tools=rule["tools"],
                        confidence=rule["confidence"],
                        reasoning=f"规则匹配: {intent}",
                        execution_plan=rule["plan"],
                    )

            return None

        except Exception as e:
            logger.error(f"❌ 规则策略失败: {e}")
            return None

    async def _learning_strategy(
        self, intent: str, parameters: dict[str, Any], context: dict[str, Any]
    ) -> ToolSelection | None:
        """学习型策略"""
        try:
            # 基于历史性能选择工具
            tool_scores = {}

            for tool_name, tool_meta in self.tool_registry.items():
                # 计算工具得分
                reliability = tool_meta.get("reliability", 0.8)
                performance = tool_meta.get("performance", 0.8)
                cost_efficiency = 1.0 - tool_meta.get("cost", 0.3)

                score = 0.4 * reliability + 0.4 * performance + 0.2 * cost_efficiency
                tool_scores[tool_name] = score

            # 选择top工具
            if not tool_scores:
                return None

            sorted_tools = sorted(tool_scores, key=tool_scores.get, reverse=True)

            # 根据意图过滤
            intent_relevant_tools = self._filter_by_intent(sorted_tools, intent)

            if not intent_relevant_tools:
                intent_relevant_tools = sorted_tools[:2]

            return ToolSelection(
                strategy=RoutingStrategy.LEARNING_BASED,
                tools=intent_relevant_tools[:2],
                confidence=0.82,
                reasoning="学习型: 基于历史性能选择",
                execution_plan="parallel",
                metadata={"tool_scores": tool_scores},
            )

        except Exception as e:
            logger.error(f"❌ 学习策略失败: {e}")
            return None

    def _calculate_complexity(self, parameters: dict[str, Any]) -> float:
        """计算参数复杂度"""
        # 基于参数数量和嵌套深度
        param_count = len(parameters)
        nested_count = sum(1 for v in parameters.values() if isinstance(v, (dict, list)))

        complexity = min(1.0, (param_count * 0.1 + nested_count * 0.2))
        return complexity

    def _filter_by_intent(self, tools: list[str], intent: str) -> list[str]:
        """根据意图过滤工具"""
        # 简化实现: 基于工具名称判断
        intent_keywords = {
            "patent_analysis": ["patent", "xiaona"],
            "coding": ["coding", "optimization"],
            "daily_chat": ["chat"],
            "legal_consulting": ["xiaona", "legal"],
            "data_analysis": ["nlp", "knowledge", "graph"],
        }

        keywords = intent_keywords.get(intent, [])
        filtered = [t for t in tools if any(kw in t.lower() for kw in keywords)]

        return filtered if filtered else tools[:2]

    def _ensemble_selections(
        self, selections: list[ToolSelection], primary_strategy: RoutingStrategy
    ) -> ToolSelection:
        """集成多个策略的选择结果"""
        if not selections:
            # 默认选择
            return ToolSelection(
                strategy=primary_strategy,
                tools=["daily_chat"],
                confidence=0.5,
                reasoning="默认选择: 闲聊工具",
                execution_plan="single",
            )

        if len(selections) == 1:
            return selections[0]

        # 加权投票
        tool_votes = defaultdict(float)
        plan_votes = defaultdict(float)

        for selection in selections:
            weight = self.strategy_weights.get(selection.strategy.value, 0.25)

            for tool in selection.tools:
                tool_votes[tool] += weight * selection.confidence

            plan_votes[selection.execution_plan] += weight

        # 选择得票最高的工具
        sorted_tools = sorted(tool_votes, key=tool_votes.get, reverse=True)

        # 选择前2个工具
        final_tools = sorted_tools[:2]

        # 选择执行计划
        final_plan = max(plan_votes, key=plan_votes.get)

        # 计算综合置信度
        avg_confidence = sum(s.confidence for s in selections) / len(selections)

        return ToolSelection(
            strategy=RoutingStrategy.ENSEMBLE,
            tools=final_tools,
            confidence=min(0.95, avg_confidence * 1.1),
            reasoning=f"集成选择: {len(selections)}个策略投票",
            execution_plan=final_plan,
            metadata={"vote_details": dict(tool_votes)},
        )

    async def _execute_tools(
        self,
        tools: list[str],
        execution_plan: str,
        parameters: dict[str, Any],        context: dict[str, Any],    ) -> list[ToolExecutionResult]:
        """执行工具"""
        results = []

        if execution_plan == "single":
            # 单个工具
            if tools:
                result = await self._execute_single_tool(tools[0], parameters, context)
                results.append(result)

        elif execution_plan == "parallel":
            # 并行执行
            tasks = [self._execute_single_tool(tool, parameters, context) for tool in tools]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 处理异常
            processed_results = []
            for r in results:
                if isinstance(r, Exception):
                    processed_results.append(
                        ToolExecutionResult(
                            tool_name="unknown",
                            success=False,
                            result=None,
                            execution_time=0.0,
                            error=str(r),
                        )
                    )
                else:
                    processed_results.append(r)
            results = processed_results

        elif execution_plan == "sequential":
            # 顺序执行
            for tool in tools:
                result = await self._execute_single_tool(tool, parameters, context)
                results.append(result)

                # 如果失败,停止后续执行
                if not result.success:
                    logger.warning(f"⚠️ 工具{tool}执行失败,停止后续执行")
                    break

                # 更新参数(传递上一个工具的输出)
                if result.result:
                    parameters.update(result.result)

        return results

    async def _execute_single_tool(
        self, tool_name: str, parameters: dict[str, Any], context: dict[str, Any]
    ) -> ToolExecutionResult:
        """执行单个工具"""
        import time

        start_time = time.time()

        try:
            # 检查工具是否存在
            if tool_name not in self.tool_registry:
                return ToolExecutionResult(
                    tool_name=tool_name,
                    success=False,
                    result=None,
                    execution_time=time.time() - start_time,
                    error=f"工具不存在: {tool_name}",
                )

            # 模拟工具执行
            # 实际应该调用: self.tool_registry[tool_name].execute(parameters, context)
            await asyncio.sleep(0.1)  # 模拟执行时间

            # 模拟成功结果
            result = {"tool": tool_name, "status": "success", "data": f"执行结果_{tool_name}"}

            execution_time = time.time() - start_time

            return ToolExecutionResult(
                tool_name=tool_name,
                success=True,
                result=result,
                execution_time=execution_time,
                metadata={"timestamp": datetime.now().isoformat()},
            )

        except Exception as e:
            return ToolExecutionResult(
                tool_name=tool_name,
                success=False,
                result=None,
                execution_time=time.time() - start_time,
                error=str(e),
            )

    def _aggregate_results(self, results: list[ToolExecutionResult]) -> Any:
        """聚合执行结果"""
        if not results:
            return None

        successful_results = [r for r in results if r.success]

        if not successful_results:
            return {"success": False, "errors": [r.error for r in results if r.error]}

        if len(successful_results) == 1:
            return successful_results[0].result

        # 聚合多个结果
        aggregated = {
            "success": True,
            "tool_count": len(successful_results),
            "results": [r.result for r in successful_results],
            "total_time": sum(r.execution_time for r in results),
        }

        return aggregated

    def _update_strategy_performance(self, strategy_name: str, success: bool):
        """更新策略性能"""
        performance = 1.0 if success else 0.0
        self.strategy_performance[strategy_name].append(performance)

        # 限制历史长度
        if len(self.strategy_performance[strategy_name]) > 100:
            self.strategy_performance[strategy_name] = self.strategy_performance[strategy_name][
                -50:
            ]

        # 更新权重
        self._update_strategy_weights()

    def _update_strategy_weights(self) -> Any:
        """基于性能更新策略权重"""
        for strategy_name, perf_history in self.strategy_performance.items():
            if len(perf_history) >= 5:
                recent_avg = sum(perf_history[-5:]) / 5

                # 调整权重
                if recent_avg > 0.9:
                    self.strategy_weights[strategy_name] = min(
                        0.5, self.strategy_weights[strategy_name] * 1.05
                    )
                elif recent_avg < 0.7:
                    self.strategy_weights[strategy_name] = max(
                        0.1, self.strategy_weights[strategy_name] * 0.95
                    )

        # 归一化
        total = sum(self.strategy_weights.values())
        self.strategy_weights = {k: v / total for k, v in self.strategy_weights.items()}

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "tool_count": len(self.tool_registry),
            "strategy_weights": self.strategy_weights,
            "strategy_performance": {
                k: {"avg": sum(v) / len(v) if v else 0, "samples": len(v)}
                for k, v in self.strategy_performance.items()
            },
        }


# 全局实例
_ensemble_instance: ToolCallEnsemble | None = None


def get_tool_call_ensemble() -> ToolCallEnsemble:
    """获取工具调用集成器单例"""
    global _ensemble_instance
    if _ensemble_instance is None:
        _ensemble_instance = ToolCallEnsemble()
    return _ensemble_instance
