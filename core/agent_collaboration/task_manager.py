#!/usr/bin/env python3
from __future__ import annotations
"""
任务管理器
Task Manager

管理多Agent协作系统的任务调度和生命周期
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from .agent_coordinator import AgentCoordinator, get_agent_coordinator
from .agent_registry import AgentRegistry, get_agent_registry
from .communication import MessageBus, TaskMessage, get_message_bus

logger = logging.getLogger(__name__)


@dataclass
class TaskRequest:
    """任务请求"""

    request_id: str
    user_id: str
    user_request: str
    workflow_type: str = "sequential"
    priority: int = 2
    deadline: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskResponse:
    """任务响应"""

    request_id: str
    success: bool
    result: dict[str, Any]
    execution_time: float
    error_message: Optional[str] = None
    agent_details: dict[str, Any] = field(default_factory=dict)


class TaskManager:
    """任务管理器 - 统一管理多Agent协作任务"""

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}

        # 核心组件
        self.message_bus: MessageBus | None = None
        self.agent_registry: AgentRegistry | None = None
        self.agent_coordinator: AgentCoordinator | None = None

        # 任务管理
        # 内存泄漏修复: 添加活动请求大小限制
        self.max_active_requests = (config or {}).get("max_active_requests", 1000)
        self.active_requests: dict[str, TaskRequest] = {}
        self.task_history: list[TaskResponse] = []
        self.max_history_size = 1000

        # 性能统计
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.avg_response_time = 0.0

        # 内存泄漏修复: 保存后台任务引用以便取消
        self._background_tasks: list[asyncio.Task] = []

        # 初始化状态
        self.initialized = False

    async def initialize(self):
        """初始化任务管理器"""
        try:
            logger.info("🚀 初始化任务管理器...")

            # 初始化核心组件
            await self._initialize_components()

            # 启动后台任务
            await self._start_background_tasks()

            self.initialized = True
            logger.info("✅ 任务管理器初始化完成")

        except Exception as e:
            logger.error(f"❌ 任务管理器初始化失败: {e}")
            raise

    async def _initialize_components(self):
        """初始化核心组件"""
        # 初始化消息总线
        self.message_bus = get_message_bus()
        await self.message_bus.start()

        # 初始化Agent注册中心
        self.agent_registry = get_agent_registry()

        # 初始化Agent协调器
        self.agent_coordinator = get_agent_coordinator(self.config)
        await self.agent_coordinator.initialize()

    async def _start_background_tasks(self):
        """启动后台任务"""
        # 内存泄漏修复: 保存任务引用以便后续取消
        health_check_task = asyncio.create_task(self._health_check_loop())
        self._background_tasks.append(health_check_task)

        performance_task = asyncio.create_task(self._performance_monitoring_loop())
        self._background_tasks.append(performance_task)

        cleanup_task = asyncio.create_task(self._history_cleanup_loop())
        self._background_tasks.append(cleanup_task)

    async def submit_task(
        self,
        user_request: str,
        user_id: str = "default_user",
        workflow_type: str = "sequential",
        priority: int = 2,
        deadline: datetime | None = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> TaskResponse:
        """
        提交任务给多Agent系统处理

        Args:
            user_request: 用户请求
            user_id: 用户ID
            workflow_type: 工作流类型
            priority: 优先级
            deadline: 截止时间
            metadata: 元数据

        Returns:
            TaskResponse: 任务处理结果
        """
        if not self.initialized:
            raise RuntimeError("TaskManager not initialized")

        start_time = datetime.now()
        request_id = f"req_{start_time.strftime('%Y%m%d_%H%M%S')}_{len(self.active_requests)}"

        try:
            # 内存泄漏修复: 检查活动请求数量限制
            if len(self.active_requests) >= self.max_active_requests:
                raise RuntimeError(
                    f"活动请求数量已达上限 ({self.max_active_requests})，请稍后重试"
                )

            # 创建任务请求
            task_request = TaskRequest(
                request_id=request_id,
                user_id=user_id,
                user_request=user_request,
                workflow_type=workflow_type,
                priority=priority,
                deadline=deadline,
                metadata=metadata or {},
            )

            self.active_requests[request_id] = task_request
            self.total_requests += 1

            logger.info(f"📝 提交任务 {request_id}: {user_request[:50]}...")

            # 智能任务分析和分解
            task_workflow = await self._analyze_and_decompose_task(user_request, workflow_type)

            # 执行工作流
            workflow_result = await self._execute_workflow(task_workflow, request_id)

            # 生成综合响应
            result = await self._generate_comprehensive_response(
                user_request, workflow_result, request_id
            )

            execution_time = (datetime.now() - start_time).total_seconds()

            # 创建成功响应
            response = TaskResponse(
                request_id=request_id,
                success=True,
                result=result,
                execution_time=execution_time,
                agent_details=workflow_result.get("coordination_summary", {}),
            )

            # 更新统计
            self.successful_requests += 1
            self._update_avg_response_time(execution_time)

            # 保存到历史
            self._save_to_history(response)

            # 清理活动请求
            del self.active_requests[request_id]

            logger.info(f"✅ 任务 {request_id} 完成,耗时: {execution_time:.2f}s")
            return response

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()

            # 创建失败响应
            response = TaskResponse(
                request_id=request_id,
                success=False,
                result={},
                execution_time=execution_time,
                error_message=str(e),
            )

            # 更新统计
            self.failed_requests += 1

            # 保存到历史
            self._save_to_history(response)

            # 清理活动请求
            if request_id in self.active_requests:
                del self.active_requests[request_id]

            logger.error(f"❌ 任务 {request_id} 失败: {e}")
            return response

    async def _analyze_and_decompose_task(
        self, user_request: str, workflow_type: str
    ) -> dict[str, Any]:
        """分析任务并分解为工作流"""
        request_lower = user_request.lower()

        # 智能任务类型识别
        if "专利" in request_lower and "搜索" in request_lower:
            return {
                "workflow_type": "pipeline",
                "user_request": user_request,
                "tasks": [
                    {
                        "type": "patent_search",
                        "content": {"query": user_request, "limit": 20},
                        "priority": 3,
                    },
                    {
                        "type": "patent_analysis",
                        "content": {"analysis_type": "comprehensive"},
                        "priority": 2,
                    },
                ],
            }
        elif "分析" in request_lower or "评估" in request_lower:
            return {
                "workflow_type": "sequential",
                "user_request": user_request,
                "tasks": [
                    {
                        "type": "patent_search",
                        "content": {"query": user_request, "limit": 10},
                        "priority": 3,
                    },
                    {
                        "type": "patent_analysis",
                        "content": {"analysis_type": "comprehensive"},
                        "priority": 2,
                    },
                    {
                        "type": "competitive_analysis",
                        "content": {"analysis_depth": "deep"},
                        "priority": 2,
                    },
                ],
            }
        elif "创新" in request_lower or "创意" in request_lower:
            return {
                "workflow_type": "collaborative",
                "user_request": user_request,
                "tasks": [
                    {"type": "semantic_search", "content": {"text": user_request}, "priority": 2},
                    {
                        "type": "innovation_generation",
                        "content": {"problem_domain": self._extract_domain(user_request)},
                        "priority": 3,
                    },
                    {
                        "type": "creative_solutions",
                        "content": {"problem_statement": user_request},
                        "priority": 2,
                    },
                ],
            }
        else:
            # 默认通用搜索
            return {
                "workflow_type": "sequential",
                "user_request": user_request,
                "tasks": [
                    {"type": "patent_search", "content": {"query": user_request}, "priority": 2}
                ],
            }

    def _extract_domain(self, user_request: str) -> str:
        """提取技术领域"""
        domain_keywords = {
            "人工智能": ["AI", "人工智能", "机器学习"],
            "医疗": ["医疗", "健康", "医药", "医院"],
            "金融": ["金融", "银行", "支付", "保险"],
            "教育": ["教育", "学习", "培训", "学校"],
            "制造": ["制造", "生产", "工厂", "设备"],
        }

        request_lower = user_request.lower()
        for domain, keywords in domain_keywords.items():
            if any(keyword.lower() in request_lower for keyword in keywords):
                return domain

        return "通用技术"

    async def _execute_workflow(
        self, task_workflow: dict[str, Any], request_id: str
    ) -> dict[str, Any]:
        """执行工作流"""
        # 调用Agent协调器执行工作流
        from .communication import TaskPriority

        task_priority_value = task_workflow["tasks"][0].get("priority", 2)
        if isinstance(task_priority_value, int):
            task_priority = TaskPriority(task_priority_value)
        else:
            task_priority = TaskPriority.MEDIUM

        if not self.agent_coordinator:
            raise RuntimeError("AgentCoordinator not initialized")

        coordination_message = TaskMessage(
            task_id=f"coord_{request_id}",
            sender_id="task_manager",
            recipient_id=self.agent_coordinator.agent_id,  # type: ignore[attr-defined]
            task_type="coordinate_workflow",
            content=task_workflow,
            priority=task_priority,
        )

        # 发送协调任务
        if not self.message_bus:
            raise RuntimeError("MessageBus not initialized")
        await self.message_bus.send_message(coordination_message)  # type: ignore[attr-defined]

        # 等待协调结果
        return await self._wait_for_coordination_result(f"coord_{request_id}")

    async def _wait_for_coordination_result(
        self, coordination_task_id: str, timeout: float = 120.0
    ) -> dict[str, Any]:
        """等待协调结果"""
        start_time = datetime.now()

        while (datetime.now() - start_time).total_seconds() < timeout:
            # 检查消息历史
            if self.message_bus and hasattr(self.message_bus, "message_history"):
                history = self.message_bus.message_history
                if history:  # type: ignore[attr-defined]
                    recent_messages = history[-20:]  # type: ignore[attr-defined]
                    for message in recent_messages:
                        if (
                            message.get("task_id") == coordination_task_id  # type: ignore[arg-type]
                            and message.get("recipient_id") == "task_manager"
                            and message.get("message_type") == "response"
                        ):
                            return message.get("content", {})

            await asyncio.sleep(1.0)

        raise asyncio.TimeoutError(f"协调任务 {coordination_task_id} 执行超时")

    async def _generate_comprehensive_response(
        self, user_request: str, workflow_result: dict[str, Any], request_id: str
    ) -> dict[str, Any]:
        """生成综合响应"""
        # 提取各Agent的结果
        task_results = workflow_result.get("workflow_result", {}).get("task_results", [])

        # 构建综合响应
        comprehensive_response = {
            "request_id": request_id,
            "user_request": user_request,
            "response_summary": self._generate_summary(user_request, task_results),
            "detailed_results": self._organize_detailed_results(task_results),
            "agent_insights": self._extract_agent_insights(task_results),
            "recommendations": self._generate_recommendations(user_request, task_results),
            "related_suggestions": self._generate_related_suggestions(user_request),
            "execution_metadata": {
                "workflow_type": workflow_result.get("workflow_type"),
                "agents_involved": workflow_result.get("workflow_result", {}).get(
                    "agents_used", []
                ),
                "execution_time": workflow_result.get("workflow_result", {}).get(
                    "total_execution_time", 0
                ),
                "success_rate": workflow_result.get("workflow_result", {}).get("success_rate", 0),
            },
        }

        return comprehensive_response

    def _generate_summary(self, user_request: str, task_results: list[dict[str, Any]]) -> str:
        """生成响应摘要"""
        if not task_results:
            return f"已完成对您的请求'{user_request}'的处理,但未获得详细结果。"

        successful_tasks = [t for t in task_results if t.get("success", False)]

        if len(successful_tasks) == len(task_results):
            return f"成功完成了您的请求'{user_request}',共处理{len(task_results)}项任务,所有任务均成功完成。"
        elif len(successful_tasks) > 0:
            return f"部分完成了您的请求'{user_request}',{len(successful_tasks)}/{len(task_results)}项任务成功完成。"
        else:
            return f"处理您的请求'{user_request}'时遇到了问题,所有任务均未成功完成。"

    def _organize_detailed_results(self, task_results: list[dict[str, Any]]) -> dict[str, Any]:
        """组织详细结果"""
        organized = {}

        for result in task_results:
            if not result.get("success", False):
                continue

            task_type = result.get("task_id", "").split("_")[0]  # 提取任务类型
            content = result.get("content", {})

            if task_type == "patent":
                organized["patent_search_results"] = content.get("results", [])
            elif task_type == "patent":
                organized["patent_analysis_results"] = content
            elif task_type == "innovation":
                organized["innovation_results"] = content.get("innovations", [])
            elif task_type == "creative":
                organized["creative_solutions"] = content.get("solutions", [])

        return organized

    def _extract_agent_insights(self, task_results: list[dict[str, Any]]) -> list[str]:
        """提取Agent洞察"""
        insights = []

        for result in task_results:
            if not result.get("success", False):
                continue

            agent_used = result.get("agent_used", "unknown")
            content = result.get("content", {})

            if agent_used == "search_agent_001":
                results_count = len(content.get("results", []))
                insights.append(f"搜索Agent发现了{results_count}个相关结果,匹配度高")
            elif agent_used == "analysis_agent_001":
                innovation_score = content.get("innovation_assessment", {}).get("overall_score", 0)
                insights.append(f"分析Agent评估创新性为{innovation_score:.1%},技术价值较高")
            elif agent_used == "creative_agent_001":
                innovations_count = len(content.get("innovations", []))
                insights.append(f"创意Agent生成了{innovations_count}个创新想法,创意性强")

        return insights

    def _generate_recommendations(
        self, user_request: str, task_results: list[dict[str, Any]]
    ) -> list[str]:
        """生成建议"""
        recommendations = []

        # 基于结果生成建议
        successful_results = [r for r in task_results if r.get("success", False)]

        if len(successful_results) > 0:
            recommendations.append("建议进一步深入分析相关技术领域,寻找更多创新机会")

            if any("analysis" in r.get("task_id", "") for r in successful_results):
                recommendations.append("建议基于分析结果制定详细的技术发展路线图")

            if any("creative" in r.get("task_id", "") for r in successful_results):
                recommendations.append("建议对创新想法进行可行性评估和市场分析")

        recommendations.append("建议定期跟踪相关技术领域的最新发展动态")

        return recommendations

    def _generate_related_suggestions(self, user_request: str) -> list[str]:
        """生成相关建议"""
        suggestions = []

        request_lower = user_request.lower()

        if "专利" in request_lower:
            suggestions.extend(
                [
                    "您可能还想了解相关技术的专利布局情况",
                    "建议进行专利侵权风险分析",
                    "考虑制定专利申请策略",
                ]
            )

        if "创新" in request_lower:
            suggestions.extend(
                [
                    "探索相关领域的颠覆性创新机会",
                    "分析竞争对手的技术创新路径",
                    "考虑建立开放创新生态",
                ]
            )

        if "分析" in request_lower:
            suggestions.extend(
                [
                    "进行更深层次的技术趋势预测",
                    "分析潜在的合作伙伴和收购目标",
                    "评估技术的商业化前景",
                ]
            )

        return suggestions

    def _update_avg_response_time(self, execution_time: float) -> Any:
        """更新平均响应时间"""
        total_completed = self.successful_requests + self.failed_requests
        if total_completed == 1:
            self.avg_response_time = execution_time
        else:
            self.avg_response_time = (
                self.avg_response_time * (total_completed - 1) + execution_time
            ) / total_completed

    def _save_to_history(self, response: TaskResponse) -> Any:
        """保存到历史记录"""
        self.task_history.append(response)

        # 限制历史记录大小
        if len(self.task_history) > self.max_history_size:
            self.task_history = self.task_history[-self.max_history_size :]

    async def get_task_status(self, request_id: str) -> Optional[dict[str, Any]]:
        """获取任务状态"""
        if request_id in self.active_requests:
            request = self.active_requests[request_id]
            return {
                "request_id": request_id,
                "status": "active",
                "user_request": request.user_request,
                "submitted_at": request.metadata.get("submitted_at"),
                "estimated_completion": request.metadata.get("estimated_completion"),
            }

        # 在历史中查找
        for response in self.task_history:
            if response.request_id == request_id:
                return {
                    "request_id": request_id,
                    "status": "completed",
                    "success": response.success,
                    "execution_time": response.execution_time,
                    "completed_at": response.result.get("execution_metadata", {}).get(
                        "completion_time"
                    ),
                }

        return None

    def get_system_stats(self) -> dict[str, Any]:
        """获取系统统计信息"""
        success_rate = (
            self.successful_requests / self.total_requests if self.total_requests > 0 else 0
        )

        return {
            "task_manager_stats": {
                "total_requests": self.total_requests,
                "successful_requests": self.successful_requests,
                "failed_requests": self.failed_requests,
                "success_rate": success_rate,
                "avg_response_time": self.avg_response_time,
                "active_requests": len(self.active_requests),
                "history_size": len(self.task_history),
            },
            "agent_system_stats": (
                self.agent_coordinator.get_coordination_stats() if self.agent_coordinator else {}
            ),
            "registry_stats": (
                self.agent_registry.get_registry_stats() if self.agent_registry else {}
            ),
            "message_bus_stats": self.message_bus.get_stats() if self.message_bus else {},
        }

    async def _health_check_loop(self):
        """健康检查循环"""
        try:
            while True:
                try:
                    if self.agent_coordinator and self.agent_registry:
                        # 检查Agent健康状态
                        await self.agent_registry.check_agent_health()

                    await asyncio.sleep(60)  # 每分钟检查一次

                except Exception as e:
                    logger.error(f"❌ 健康检查异常: {e}")
                    await asyncio.sleep(5)
        except asyncio.CancelledError:
            # 内存泄漏修复: 正确处理取消信号
            logger.info("📋 健康检查循环已收到取消信号，正在退出...")
            raise

    async def _performance_monitoring_loop(self):
        """性能监控循环"""
        try:
            while True:
                try:
                    # 记录性能指标
                    stats = self.get_system_stats()
                    logger.debug(f"📊 系统统计: {stats}")

                    await asyncio.sleep(300)  # 每5分钟记录一次

                except Exception as e:
                    logger.error(f"❌ 性能监控异常: {e}")
                    await asyncio.sleep(30)
        except asyncio.CancelledError:
            # 内存泄漏修复: 正确处理取消信号
            logger.info("📊 性能监控循环已收到取消信号，正在退出...")
            raise

    async def _history_cleanup_loop(self):
        """历史清理循环"""
        try:
            while True:
                try:
                    # 清理过期历史记录(保留最近30天)
                    datetime.now() - timedelta(days=30)

                    # 这里简化处理,只根据数量限制
                    if len(self.task_history) > self.max_history_size // 2:
                        # 保留最近的记录
                        self.task_history = self.task_history[-self.max_history_size // 2:]

                    await asyncio.sleep(3600)  # 每小时清理一次

                except Exception as e:
                    logger.error(f"❌ 历史清理异常: {e}")
                    await asyncio.sleep(60)
        except asyncio.CancelledError:
            # 内存泄漏修复: 正确处理取消信号
            logger.info("🧹 历史清理循环已收到取消信号，正在退出...")
            raise

    async def shutdown(self):
        """关闭任务管理器"""
        try:
            logger.info("🛑 关闭任务管理器...")

            # 内存泄漏修复: 取消所有后台任务
            for task in self._background_tasks:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        logger.debug("后台任务已取消")
                        # 不重新抛出，因为我们在循环中处理多个任务

            self._background_tasks.clear()

            # 关闭Agent协调器
            if self.agent_coordinator:
                await self.agent_coordinator.shutdown()

            # 关闭消息总线
            if self.message_bus:
                await self.message_bus.stop()

            self.initialized = False
            logger.info("✅ 任务管理器已关闭")

        except Exception as e:
            logger.error(f"❌ 任务管理器关闭失败: {e}")


# 全局任务管理器实例
_task_manager = None


def get_task_manager(config: Optional[dict[str, Any]] = None) -> TaskManager:
    """获取全局任务管理器实例"""
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager(config)
    return _task_manager
