#!/usr/bin/env python3
"""
增强版Athena代理 - 集成智能路由系统
Enhanced Athena Agent with Smart Routing Integration

Athena + 智能路由 = 专业高效的问题解决能力

作者: Athena AI系统
创建时间: 2025-12-08
版本: 1.0.0
"""
from __future__ import annotations
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Any

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 尝试导入,如果失败则创建模拟类
try:
    from core.agent.athena_agent import AthenaAgent
except ImportError:
    # 创建模拟AthenaAgent
    class AthenaAgent:
        def __init__(self, config=None):
            self.config = config or {}
            self.logger = logging.getLogger(__name__)

        async def process_input(self, input_data, input_type="text"):
            return {
                "response": f"Athena处理了: {input_data}",
                "success": True,
                "metadata": {"agent": "athena", "routing": "none"},
            }


try:
    from core.smart_routing.intelligent_tool_router import (
        IntelligentToolRouter,
        RoutingResult,
    )
except ImportError:
    # 创建模拟路由器
    class MockRoutingResult:
        def __init__(self):
            self.intent_type = type("IntentType", (), {"value": "general_conversation"})()
            self.confidence = 0.8
            self.primary_tools = []
            self.supporting_tools = []
            self.workflow = "通用流程"
            self.estimated_total_time = 30.0
            self.optimization_suggestions = ["建议使用更具体的描述"]
            self.fallback_options = []

    class IntelligentToolRouter:
        async def route_request(self, user_input, context=None):
            return MockRoutingResult()

        def get_routing_stats(self):
            return {"stats": "mock"}


try:
    from core.performance_monitoring.tool_performance_tracker import (
        ToolExecutionRecord,
        ToolPerformanceTracker,
    )
except ImportError:
    # 创建模拟性能跟踪器
    class ToolExecutionRecord:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    class ToolPerformanceTracker:
        def record_execution(self, record):
            pass

        def get_system_overview(self):
            return {"health_percentage": 0.9}

        def get_optimization_suggestions(self, limit=5):
            return []


logger = logging.getLogger(__name__)


class AthenaEnhancedAgent(AthenaAgent):
    """增强版Athena代理 - 集成智能路由"""

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)

        # 初始化智能路由系统
        self.router = IntelligentToolRouter()

        # 初始化性能跟踪器
        self.performance_tracker = ToolPerformanceTracker()

        # 路由缓存
        self.route_cache = {}
        self.cache_timeout = 300  # 5分钟缓存

        # 路由统计
        self.routing_stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "router_success": 0,
            "router_failures": 0,
        }

        # 确保logger已初始化
        if not hasattr(self, "logger"):
            self.logger = logging.getLogger(__name__)

        self.logger.info("🧠 增强版Athena(集成智能路由)初始化完成")

    async def process_input_with_routing(
        self, input_data: Any, input_type: str = "text"
    ) -> dict[str, Any]:
        """带智能路由的输入处理"""
        start_time = time.time()

        try:
            self.routing_stats["total_requests"] += 1

            # 1. 智能路由
            routing_result = await self._route_to_tools(input_data)

            # 2. 记录路由开始
            execution_records = []

            # 3. 执行推荐的工具链
            execution_results = await self._execute_tool_chain(
                routing_result, input_data, execution_records
            )

            # 4. 基础Athena处理
            base_result = await super().process_input(input_data, input_type)

            # 5. 整合路由结果
            enhanced_result = {
                **base_result,
                "routing_info": {
                    "intent_type": routing_result.intent_type.value,
                    "confidence": routing_result.confidence,
                    "estimated_time": routing_result.estimated_total_time,
                    "workflow": routing_result.workflow,
                },
                "tool_executions": execution_results,
                "optimization_suggestions": routing_result.optimization_suggestions,
                "fallback_options": routing_result.fallback_options,
                "performance_metrics": {
                    "routing_time": routing_result.estimated_total_time,
                    "actual_time": time.time() - start_time,
                    "tools_used": len(routing_result.primary_tools)
                    + len(routing_result.supporting_tools),
                },
            }

            # 6. 记录执行日志
            await self._record_routing_execution(
                routing_result, execution_results, time.time() - start_time
            )

            # 7. 更新统计
            self._update_routing_stats(routing_result, True)

            self.logger.info(f"✅ Athena增强处理完成,耗时: {time.time() - start_time:.1f}秒")

            return enhanced_result

        except Exception as e:
            self.logger.error(f"❌ Athena增强处理失败: {e!s}")
            self._update_routing_stats(None, False)

            # 返回基础结果作为回退
            return await super().process_input(input_data, input_type)

    async def _route_to_tools(self, input_data: Any) -> RoutingResult:
        """路由到合适的工具"""
        try:
            # 检查缓存
            input_str = str(input_data)
            cache_key = hash(input_str)

            if cache_key in self.route_cache:
                cached_time = self.route_cache[cache_key]["timestamp"]
                if time.time() - cached_time < self.cache_timeout:
                    self.routing_stats["cache_hits"] += 1
                    return self.route_cache[cache_key]["result"]

            # 执行智能路由
            routing_result = await self.router.route_request(input_str)

            # 缓存结果
            self.route_cache[cache_key] = {"result": routing_result, "timestamp": time.time()}

            return routing_result

        except Exception as e:
            self.logger.error(f"❌ 工具路由失败: {e!s}")
            # 创建默认路由结果
            return self._create_default_routing_result(str(input_data))

    async def _execute_tool_chain(
        self,
        routing_result: RoutingResult,
        input_data: Any,
        execution_records: list[ToolExecutionRecord],
    ) -> list[dict[str, Any]]:
        """执行工具链"""
        execution_results = []

        all_tools = routing_result.primary_tools + routing_result.supporting_tools

        for tool_recommendation in all_tools:
            start_time = datetime.now()

            try:
                # 模拟工具执行
                result = await self._simulate_tool_execution(
                    tool_recommendation.tool_name, input_data
                )

                end_time = datetime.now()
                success = result.get("success", False)

                # 记录执行记录
                record = ToolExecutionRecord(
                    tool_name=tool_recommendation.tool_name,
                    intent_type=routing_result.intent_type.value,
                    start_time=start_time,
                    end_time=end_time,
                    success=success,
                    error_message=result.get("error") if not success else None,
                    user_input_length=len(str(input_data)),
                    output_length=result.get("output_length", 0),
                    user_satisfaction=result.get("satisfaction", 4.0),
                    resource_usage=result.get("resource_usage", {"cpu": 0.3, "memory": 0.2}),
                    context={
                        "priority": tool_recommendation.priority.value,
                        "confidence": tool_recommendation.confidence,
                    },
                )

                execution_records.append(record)
                self.performance_tracker.record_execution(record)

                execution_results.append(
                    {
                        "tool_name": tool_recommendation.tool_name,
                        "success": success,
                        "result": result,
                        "execution_time": (end_time - start_time).total_seconds(),
                        "record_id": len(execution_records) - 1,
                    }
                )

                if not success and tool_recommendation.priority.value == "critical":
                    # 关键工具失败,停止执行后续工具
                    self.logger.warning(
                        f"⚠️ 关键工具 {tool_recommendation.tool_name} 执行失败,终止工具链"
                    )
                    break

            except Exception as e:
                self.logger.error(f"❌ 工具执行失败 {tool_recommendation.tool_name}: {e!s}")

                execution_results.append(
                    {
                        "tool_name": tool_recommendation.tool_name,
                        "success": False,
                        "error": str(e),
                        "execution_time": 0,
                    }
                )

        return execution_results

    async def _simulate_tool_execution(self, tool_name: str, input_data: Any) -> dict[str, Any]:
        """模拟工具执行"""
        # 模拟不同的执行时间
        tool_times = {
            "patent_professional_workflow": 180,
            "enhanced_patent_perception": 20,
            "patent_crawler": 30,
            "comprehensive_patent_processor": 90,
            "xiaonuo_enhanced": 30,
            "platform_manager": 10,
            "chemical_analyzer": 15,
        }

        tool_times.get(tool_name, 30)

        # 模拟执行过程
        await asyncio.sleep(0.1)  # 短暂延迟

        # 95%成功率,5%失败率
        import random

        success = random.random() > 0.05

        if success:
            return {
                "success": True,
                "output_length": random.randint(500, 2000),
                "satisfaction": random.uniform(3.5, 5.0),
                "resource_usage": {
                    "cpu": random.uniform(0.2, 0.8),
                    "memory": random.uniform(0.1, 0.5),
                },
                "tool_specific_result": f"{tool_name}执行成功",
            }
        else:
            return {
                "success": False,
                "error": "模拟执行失败",
                "satisfaction": random.uniform(1.0, 3.0),
            }

    async def _record_routing_execution(
        self,
        routing_result: RoutingResult,
        execution_results: list[dict[str, Any]],        total_time: float,
    ):
        """记录路由执行"""
        try:
            # 记录到记忆系统
            {
                "routing_result": {
                    "intent_type": routing_result.intent_type.value,
                    "confidence": routing_result.confidence,
                    "workflow": routing_result.workflow,
                    "tools_count": len(routing_result.primary_tools)
                    + len(routing_result.supporting_tools),
                },
                "execution_summary": {
                    "total_tools": len(execution_results),
                    "successful_tools": sum(1 for r in execution_results if r.get("success")),
                    "total_execution_time": total_time,
                    "optimization_suggestions": routing_result.optimization_suggestions,
                },
                "timestamp": datetime.now().isoformat(),
            }

            # 这里可以调用记忆系统的API
            # await self.memory.store("routing_execution", memory_data)

        except Exception as e:
            self.logger.error(f"❌ 记录路由执行失败: {e!s}")

    def _create_default_routing_result(self, input_str: str) -> RoutingResult:
        """创建默认路由结果"""
        try:
            from core.smart_routing.intelligent_tool_router import (
                IntentType,
                ToolPriority,
                ToolRecommendation,
            )
        except ImportError:
            # 创建模拟类
            class ToolPriority:
                CRITICAL = "critical"

            class IntentType:
                GENERAL_CONVERSATION = "general_conversation"

            class ToolRecommendation:
                def __init__(self, tool_name, priority, confidence, reason, estimated_time):
                    self.tool_name = tool_name
                    self.priority = priority
                    self.confidence = confidence
                    self.reason = reason
                    self.estimated_time = estimated_time

            class RoutingResult:
                def __init__(
                    self,
                    intent_type,
                    confidence,
                    primary_tools,
                    supporting_tools,
                    workflow,
                    estimated_total_time,
                    optimization_suggestions,
                    fallback_options,
                ):
                    self.intent_type = intent_type
                    self.confidence = confidence
                    self.primary_tools = primary_tools
                    self.supporting_tools = supporting_tools
                    self.workflow = workflow
                    self.estimated_total_time = estimated_total_time
                    self.optimization_suggestions = optimization_suggestions
                    self.fallback_options = fallback_options

        default_tool = ToolRecommendation(
            tool_name="athena_agent.py",
            priority=ToolPriority.CRITICAL,
            confidence=0.6,
            reason="智能路由失败,使用默认Athena代理",
            estimated_time=30.0,
        )

        return RoutingResult(
            intent_type=IntentType.GENERAL_CONVERSATION,
            confidence=0.5,
            primary_tools=[default_tool],
            supporting_tools=[],
            workflow="通用处理流程",
            estimated_total_time=30.0,
            optimization_suggestions=["建议提供更详细的需求描述"],
            fallback_options=["使用小诺代理", "手动选择工具"],
        )

    def _update_routing_stats(self, routing_result: RoutingResult, success: bool):
        """更新路由统计"""
        if success and routing_result:
            self.routing_stats["router_success"] += 1
        else:
            self.routing_stats["router_failures"] += 1

    def get_routing_insights(self) -> dict[str, Any]:
        """获取路由洞察"""
        insights = {
            "routing_stats": self.routing_stats,
            "cache_stats": {
                "cache_size": len(self.route_cache),
                "cache_hit_rate": self.routing_stats["cache_hits"]
                / max(self.routing_stats["total_requests"], 1),
            },
            "system_health": {
                "router_success_rate": self.routing_stats["router_success"]
                / max(self.routing_stats["total_requests"], 1),
                "router_failure_rate": self.routing_stats["router_failures"]
                / max(self.routing_stats["total_requests"], 1),
            },
        }

        # 添加性能跟踪器洞察
        try:
            performance_overview = self.performance_tracker.get_system_overview()
            if "error" not in performance_overview:
                insights["performance_overview"] = performance_overview

                # 获取最近的优化建议
                suggestions = self.performance_tracker.get_optimization_suggestions(limit=5)
                insights["recent_suggestions"] = suggestions
        except Exception as e:
            self.logger.error(f"❌ 获取性能洞察失败: {e!s}")

        return insights

    async def analyze_performance_trends(self) -> dict[str, Any]:
        """分析性能趋势"""
        try:
            # 获取最近7天的数据
            insights = self.get_routing_insights()

            analysis = {"overall_health": "健康", "recommendations": [], "trends": {}}

            # 分析路由成功率
            if insights["system_health"]["router_success_rate"] > 0.9:
                analysis["overall_health"] = "优秀"
            elif insights["system_health"]["router_success_rate"] > 0.8:
                analysis["overall_health"] = "良好"
            elif insights["system_health"]["router_success_rate"] < 0.7:
                analysis["overall_health"] = "需要改进"

            # 分析缓存命中率
            cache_hit_rate = insights["cache_stats"]["cache_hit_rate"]
            if cache_hit_rate < 0.3:
                analysis["recommendations"].append("缓存命中率较低,建议调整缓存策略")
            elif cache_hit_rate > 0.8:
                analysis["recommendations"].append("缓存使用良好")

            # 分析性能数据
            if "performance_overview" in insights:
                health_percentage = insights["performance_overview"]["health_percentage"]
                if health_percentage < 0.8:
                    analysis["recommendations"].append("工具性能需要关注,建议优化")
                    analysis["recommendations"].extend(insights.get("recent_suggestions", [])[:3])

            return analysis

        except Exception as e:
            self.logger.error(f"❌ 性能趋势分析失败: {e!s}")
            return {"error": str(e)}

    async def get_optimization_report(self) -> dict[str, Any]:
        """获取优化报告"""
        try:
            # 性能趋势分析
            trends = await self.analyze_performance_trends()

            # 获取优化建议
            suggestions = self.performance_tracker.get_optimization_suggestions(limit=10)

            report = {
                "generated_at": datetime.now().isoformat(),
                "system_status": trends["overall_health"],
                "routing_performance": {
                    "cache_hit_rate": self.routing_stats["cache_hits"]
                    / max(self.routing_stats["total_requests"], 1),
                    "router_success_rate": self.routing_stats["router_success"]
                    / max(self.routing_stats["total_requests"], 1),
                },
                "optimization_suggestions": suggestions,
                "trends_analysis": trends,
                "next_actions": self._generate_next_actions(trends, suggestions),
            }

            return report

        except Exception as e:
            self.logger.error(f"❌ 生成优化报告失败: {e!s}")
            return {"error": str(e)}

    def _generate_next_actions(
        self, trends: dict[str, Any], suggestions: list[dict[str, Any]]
    ) -> list[str]:
        """生成下一步行动建议"""
        actions = []

        # 基于系统状态生成建议
        if trends["overall_health"] == "需要改进":
            actions.append("🔧 立即检查系统日志,识别性能瓶颈")
            actions.append("📊 查看具体工具的性能报告")
        elif trends["overall_health"] == "良好":
            actions.append("💡 考虑启用高级缓存策略")
            actions.append("📈 监控并优化高频使用工具")
        else:
            actions.append("✅ 系统运行良好,持续监控")

        # 基于建议数量生成行动
        if len(suggestions) > 5:
            actions.append("⚠️ 优化建议较多,建议分批处理")
            actions.append("📋 优先处理高优先级建议")

        return actions


# 使用示例
async def test_athena_enhanced():
    """测试增强版Athena"""
    logger.info("🏛️ 测试增强版Athena(集成智能路由)")

    agent = AthenaEnhancedAgent()

    # 测试各种输入
    test_inputs = [
        "帮我处理专利202311334091.8的第一次审查意见",
        "检索机器学习相关的专利文献",
        "评估这个AI算法的技术可行性",
        "写一个关于创新的短文" "检查系统健康状态",
    ]

    for i, test_input in enumerate(test_inputs, 1):
        logger.info(f"\n📝 测试 {i}: {test_input}")
        logger.info(str("-" * 60))

        result = await agent.process_input_with_routing(test_input)

        if "routing_info" in result:
            routing = result["routing_info"]
            logger.info(f"🎯 识别意图: {routing['intent_type']}")
            logger.info(f"📊 置信度: {routing['confidence']:.2f}")
            logger.info(f"⏱️  预估时间: {routing['estimated_time']:.1f}分钟")

        if "tool_executions" in result:
            logger.info(f"🔧 执行工具: {len(result['tool_executions'])}个")
            for exec_result in result["tool_executions"]:
                status = "✅" if exec_result["success"] else "❌"
                logger.info(
                    f"  {status} {exec_result['tool_name']} ({exec_result['execution_time']:.1f}s)"
                )

        if "optimization_suggestions" in result["routing_info"]:
            if result["routing_info"]["optimization_suggestions"]:
                logger.info("💡 优化建议:")
                for suggestion in result["routing_info"]["optimization_suggestions"][:3]:
                    logger.info(f"  • {suggestion}")

    # 获取性能洞察
    logger.info("\n📊 性能洞察:")
    insights = agent.get_routing_insights()
    print(json.dumps(insights, ensure_ascii=False, indent=2))

    # 获取优化报告
    logger.info("\n📈 优化报告:")
    report = await agent.get_optimization_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(test_athena_enhanced())
