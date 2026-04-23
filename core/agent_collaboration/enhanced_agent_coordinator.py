from __future__ import annotations
"""
增强版Agent协调器 - 集成智能工具路由引擎
"""

from typing import Any

from loguru import logger

from core.agent_collaboration.router_config import RouterConfig, get_config
from core.agent_collaboration.tool_router_engine import (
    RoutingDecision,
    get_tool_router,
)


class EnhancedAgentCoordinator:
    """
    增强版Agent协调器

    集成智能工具路由引擎,实现对80+微服务的全量精确控制
    """

    def __init__(self, config: RouterConfig | None = None):
        # 加载配置
        self.config = config or get_config()

        # 初始化智能路由引擎
        if self.config.enabled:
            self.tool_router = get_tool_router()
            logger.info(f"智能工具路由引擎已启用,策略: {self.config.strategy}")
        else:
            self.tool_router = None
            logger.info("智能工具路由引擎未启用,使用传统路由")

        # 路由统计
        self.routing_stats = {
            "total_requests": 0,
            "new_router_used": 0,
            "old_router_used": 0,
            "fallback_count": 0,
        }

    async def select_agent_for_task(
        self, task_type: str, task_content: dict[str, Any], user_id: Optional[str] = None
    ) -> str:
        """
        选择合适的Agent执行任务

        增强版:优先使用智能路由引擎,失败时降级到传统路由
        """
        self.routing_stats["total_requests"] += 1

        # 检查是否启用新路由
        if not self.config.enabled:
            self.routing_stats["old_router_used"] += 1
            return await self._select_agent_traditional(task_type, task_content)

        # 检查用户是否在灰度范围内
        if not self.config.is_enabled_for_user(user_id):
            self.routing_stats["old_router_used"] += 1
            return await self._select_agent_traditional(task_type, task_content)

        # 使用智能路由引擎
        try:
            agent_id = await self._select_agent_with_router(task_type, task_content, user_id)

            # 影子模式:记录但不使用
            if self.config.traffic_percentage == 0:
                # 记录新旧路由对比
                traditional_agent = await self._select_agent_traditional(task_type, task_content)
                logger.info(f"[影子模式] 新路由: {agent_id}, 传统路由: {traditional_agent}")
                return traditional_agent

            self.routing_stats["new_router_used"] += 1
            return agent_id

        except Exception as e:
            logger.error(f"智能路由失败,降级到传统路由: {e}")
            self.routing_stats["fallback_count"] += 1
            return await self._select_agent_traditional(task_type, task_content)

    async def _select_agent_with_router(
        self, task_type: str, task_content: dict[str, Any], user_id: Optional[str] = None
    ) -> str:
        """使用智能路由引擎选择Agent"""

        # 构造用户输入
        user_input = task_content.get("description", task_type)
        if "query" in task_content:
            user_input = task_content["query"]

        # 添加上下文
        context = {"task_type": task_type, "user_id": user_id, **task_content}

        # 调用路由引擎
        if not self.tool_router:
            raise RuntimeError("工具路由引擎未初始化")
        decisions = await self.tool_router.route(
            user_input=user_input, context=context, top_k=1
        )  # type: ignore[attr-defined]

        if not decisions:
            raise ValueError("路由引擎未返回任何决策")

        # 获取最佳决策
        best_decision = decisions[0]

        # 检查置信度
        if best_decision.confidence < self.config.min_confidence_threshold:
            logger.warning(
                f"路由决策置信度过低: {best_decision.confidence:.2f} < "
                f"{self.config.min_confidence_threshold:.2f}"
            )
            # 可以在这里触发降级或返回备选方案

        # 记录决策(如果启用)
        if self.config.log_decisions:
            logger.info(
                f"[路由决策] 任务: {task_type}, "
                f"选择: {best_decision.service_name}, "
                f"置信度: {best_decision.confidence:.2f}, "
                f"理由: {best_decision.reasoning}"
            )

        # 返回服务ID
        return best_decision.service_id

    async def _select_agent_traditional(self, task_type: str, task_content: dict[str, Any]) -> str:
        """传统路由方式(降级方案)"""
        # 简单的硬编码映射作为降级方案
        task_agent_map = {
            "patent_search": "patent-analysis",
            "patent_analysis": "patent-analysis",
            "patent_download": "patent-analysis",
            "knowledge_graph": "knowledge-graph-service",
            "browser_control": "browser-automation",
            "autonomous_control": "autonomous-control",
            "academic_search": "academic-search-mcp",
            "map_service": "gaode-mcp",
        }
        return task_agent_map.get(task_type, "patent-analysis")

    async def coordinate_task_execution(
        self,
        task_type: str,
        task_content: dict[str, Any],        workflow_type: str = "sequential",
        user_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        协调任务执行

        增强版:使用智能路由选择Agent
        """
        logger.info(f"开始协调任务: {task_type}, 工作流: {workflow_type}")

        # 选择Agent
        agent_id = await self.select_agent_for_task(task_type, task_content, user_id)

        # 执行任务
        result = await self._execute_with_agent(agent_id, task_content)

        # 记录反馈(如果启用学习)
        if self.config.enable_learning and self.tool_router:
            # 这里可以根据执行结果记录反馈
            # success = result.get("success", False)
            # satisfaction = result.get("satisfaction", 0.5)
            # await self._record_feedback(agent_id, success, satisfaction)
            pass

        return result

    async def _execute_with_agent(
        self, agent_id: str, task_content: dict[str, Any]
    ) -> dict[str, Any]:
        """使用指定Agent执行任务"""

        # 这里需要调用实际的Agent服务
        # 可以通过服务发现、HTTP调用等方式

        # 示例实现:
        try:
            # 获取Agent实例
            agent = self._get_agent_by_id(agent_id)

            # 执行任务
            if agent:
                result = await agent.execute(task_content)  # type: ignore[attr-defined]
                return {"success": True, "agent_id": agent_id, "result": result}
            else:
                # 通过HTTP调用Agent服务
                result = await self._call_agent_service(agent_id, task_content)
                return result

        except Exception as e:
            logger.error(f"Agent执行失败 [{agent_id}]: {e}")
            return {"success": False, "agent_id": agent_id, "error": str(e)}

    def _get_agent_by_id(self, agent_id: str):
        """根据ID获取Agent实例"""
        # 从现有Agent映射中获取
        agent_map = {
            self.search_agent.agent_id: self.search_agent,
            self.analysis_agent.agent_id: self.analysis_agent,
            self.creative_agent.agent_id: self.creative_agent,
        }
        return agent_map.get(agent_id)

    async def _call_agent_service(
        self, service_id: str, task_content: dict[str, Any]
    ) -> dict[str, Any]:
        """调用Agent服务"""
        # 这里需要实现HTTP调用逻辑
        # 可以使用httpx、aiohttp等库

        # 示例:

        # 获取服务端点
        # from core.agent_collaboration.service_kg import get_service_kg
        # kg = get_service_kg()
        # service = kg.get_service(service_id)
        # endpoint = service.metadata.get("endpoint")

        # 暂时返回模拟结果
        return {"success": True, "service_id": service_id, "result": {"message": "调用成功"}}

    async def _record_feedback(self, service_id: str, success: bool, satisfaction: float):
        """记录反馈用于学习"""
        if self.tool_router:
            # 记录到路由引擎
            decision = RoutingDecision(  # type: ignore[call-arg]
                service_id=service_id, confidence=1.0, reasoning="User feedback"
            )
            self.tool_router.record_feedback(decision, satisfaction)  # type: ignore[attr-defined]

    def get_routing_stats(self) -> dict[str, Any]:
        """获取路由统计信息"""
        stats: dict[str, Any] = dict(self.routing_stats)

        if self.tool_router:
            stats["tool_router_stats"] = self.tool_router.get_statistics()  # type: ignore[attr-defined]

        # 计算使用率
        if stats["total_requests"] > 0:
            stats["new_router_usage_rate"] = (
                stats["new_router_used"] / stats["total_requests"] * 100
            )
            stats["fallback_rate"] = stats["fallback_count"] / stats["total_requests"] * 100

        return stats

    def reset_routing_stats(self):
        """重置路由统计"""
        self.routing_stats = {
            "total_requests": 0,
            "new_router_used": 0,
            "old_router_used": 0,
            "fallback_count": 0,
        }


# 创建全局增强协调器实例
_enhanced_coordinator: EnhancedAgentCoordinator | None = None


def get_enhanced_coordinator(config: RouterConfig | None = None) -> EnhancedAgentCoordinator:
    """获取增强版协调器实例"""
    global _enhanced_coordinator

    if _enhanced_coordinator is None:
        _enhanced_coordinator = EnhancedAgentCoordinator(config)

    return _enhanced_coordinator


def reset_coordinator():
    """重置协调器(用于配置更新后)"""
    global _enhanced_coordinator
    _enhanced_coordinator = None
