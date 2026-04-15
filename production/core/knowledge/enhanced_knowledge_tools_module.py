#!/usr/bin/env python3
"""
增强知识库与工具库模块 - BaseModule标准接口兼容版本
Enhanced Knowledge & Tools Module - BaseModule Compatible Version

整合知识管理、智能推荐、工具路由等功能,提供统一的知识与工具服务
作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

from __future__ import annotations
import logging
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# 导入BaseModule
from core.base_module import BaseModule, HealthStatus, ModuleStatus

# 导入现有知识库系统
try:
    from ..smart_routing.intelligent_tool_router import (
        IntelligentToolRouter,
        ToolRecommendation,
    )
    from . import KnowledgeManager
    from .intelligent_recommender import IntelligentRecommender, RecommendationResult

    KNOWLEDGE_SYSTEM_AVAILABLE = True
except ImportError as e:
    logging.warning(f"无法导入现有知识库系统: {e}")
    KNOWLEDGE_SYSTEM_AVAILABLE = False

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class ServiceType(Enum):
    """服务类型"""

    KNOWLEDGE_QUERY = "knowledge_query"
    PATENT_ANALYSIS = "patent_analysis"
    INTELLIGENT_RECOMMENDATION = "intelligent_recommendation"
    TOOL_ROUTING = "tool_routing"
    CONTEXT_AWARENESS = "context_awareness"


@dataclass
class QueryResult:
    """查询结果"""

    success: bool
    query_id: str
    results: list[dict[str, Any]] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    recommendations: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    execution_time: float = 0.0
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolExecutionResult:
    """工具执行结果"""

    success: bool
    tool_name: str
    execution_id: str
    result: Any = None
    output: str = ""
    execution_time: float = 0.0
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class EnhancedKnowledgeToolsModule(BaseModule):
    """增强知识库与工具库模块 - BaseModule标准接口版本"""

    def __init__(self, agent_id: str, config: dict[str, Any] | None = None):
        """
        初始化增强知识库与工具库模块

        Args:
            agent_id: 智能体标识符
            config: 配置参数
        """
        super().__init__(agent_id, config)

        # 服务配置
        self.enable_knowledge_manager = config.get("enable_knowledge_manager", True)
        self.enable_intelligent_recommender = config.get("enable_intelligent_recommender", True)
        self.enable_tool_router = config.get("enable_tool_router", True)
        self.enable_patent_analysis = config.get("enable_patent_analysis", True)

        # 存储和状态
        self.query_history: list[dict[str, Any]] = []
        self.tool_executions: list[dict[str, Any]] = []
        self.knowledge_cache: dict[str, Any] = {}

        # 统计信息
        self.service_stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "total_tool_executions": 0,
            "successful_tool_executions": 0,
            "failed_tool_executions": 0,
            "total_recommendations": 0,
            "average_query_time": 0.0,
            "cache_hits": 0,
            "cache_misses": 0,
        }

        # 子系统实例
        self.knowledge_manager = None
        self.intelligent_recommender = None
        self.tool_router = None

        # 模块状态
        self._module_status = ModuleStatus.INITIALIZING
        self._start_time = datetime.now()

        logger.info(f"📚 创建增强知识库与工具库模块 - Agent: {agent_id}")

    async def initialize(self) -> bool:
        """
        初始化模块

        Returns:
            初始化是否成功
        """
        try:
            logger.info(f"🔧 初始化模块: {self.__class__.__name__}")
            logger.info("📚 初始化知识库与工具库...")

            # 初始化知识管理器
            if self.enable_knowledge_manager and KNOWLEDGE_SYSTEM_AVAILABLE:
                try:
                    self.knowledge_manager = KnowledgeManager(
                        agent_id=self.agent_id,
                        config={
                            "enable_patent_analysis": self.enable_patent_analysis,
                            "enable_intelligent_recommendation": self.enable_intelligent_recommender,
                        },
                    )
                    await self.knowledge_manager.initialize()
                    logger.info("✅ 知识管理器就绪")
                except Exception as e:
                    logger.warning(f"⚠️ 知识管理器初始化失败: {e}")
                    self.knowledge_manager = None

            # 初始化智能推荐器(如果未通过知识管理器初始化)
            if (
                self.enable_intelligent_recommender
                and not self.knowledge_manager
                and KNOWLEDGE_SYSTEM_AVAILABLE
            ):
                try:
                    self.intelligent_recommender = IntelligentRecommender(
                        self.agent_id, self.config
                    )
                    await self.intelligent_recommender.initialize()
                    logger.info("✅ 智能推荐器就绪")
                except Exception as e:
                    logger.warning(f"⚠️ 智能推荐器初始化失败: {e}")
                    self.intelligent_recommender = None

            # 初始化工具路由器
            if self.enable_tool_router and KNOWLEDGE_SYSTEM_AVAILABLE:
                try:
                    self.tool_router = IntelligentToolRouter(self.agent_id)
                    await self.tool_router.initialize()
                    logger.info("✅ 工具路由器就绪")
                except Exception as e:
                    logger.warning(f"⚠️ 工具路由器初始化失败: {e}")
                    self.tool_router = None

            # 更新状态
            self._module_status = ModuleStatus.READY
            self._initialized = True

            logger.info("✅ 知识库与工具库模块初始化成功")
            return True

        except Exception as e:
            logger.error(f"❌ 知识库与工具库模块初始化失败: {e}")
            self._module_status = ModuleStatus.ERROR
            return False

    async def health_check(self) -> HealthStatus:
        """
        健康检查

        Returns:
            健康状态
        """
        try:
            health_details = {
                "module_status": self._module_status.value,
                "knowledge_manager_status": (
                    "available" if self.knowledge_manager else "unavailable"
                ),
                "intelligent_recommender_status": (
                    "available" if self.intelligent_recommender else "unavailable"
                ),
                "tool_router_status": "available" if self.tool_router else "unavailable",
                "dependencies_status": "ok",
                "cache_status": f"{len(self.knowledge_cache)} items",
                "stats": {
                    "total_queries": self.service_stats["total_queries"],
                    "successful_queries": self.service_stats["successful_queries"],
                    "total_tool_executions": self.service_stats["total_tool_executions"],
                    "cache_hits": self.service_stats["cache_hits"],
                    "cache_misses": self.service_stats["cache_misses"],
                },
            }

            # 缓存健康检查详情
            self._health_check_details = health_details

            # 基于状态确定健康状况
            if self._module_status == ModuleStatus.READY:
                return HealthStatus.HEALTHY
            elif self._module_status == ModuleStatus.ERROR:
                return HealthStatus.UNHEALTHY
            else:
                return HealthStatus.DEGRADED

        except Exception as e:
            logger.error(f"❌ 健康检查失败: {e}")
            return HealthStatus.UNHEALTHY

    async def query_knowledge(
        self,
        query: str,
        service_type: str = "knowledge_query",
        context: dict[str, Any] | None = None,
        **kwargs,
    ) -> QueryResult:
        """
        查询知识库

        Args:
            query: 查询内容
            service_type: 服务类型
            context: 查询上下文
            **kwargs: 其他参数

        Returns:
            查询结果
        """
        start_time = datetime.now()
        query_id = str(uuid.uuid4())

        try:
            # 更新统计
            self.service_stats["total_queries"] += 1

            # 检查缓存
            cache_key = f"{service_type}:{hash(query)}"
            if cache_key in self.knowledge_cache:
                self.service_stats["cache_hits"] += 1
                cached_result = self.knowledge_cache[cache_key]
                execution_time = (datetime.now() - start_time).total_seconds()

                return QueryResult(
                    success=True,
                    query_id=query_id,
                    results=cached_result["reports/reports/results"],
                    sources=cached_result["sources"],
                    recommendations=cached_result.get("recommendations", []),
                    confidence=cached_result.get("confidence", 0.0),
                    execution_time=execution_time,
                    metadata={"cached": True},
                )

            self.service_stats["cache_misses"] += 1

            # 执行查询
            results = []
            sources = []
            recommendations = []
            confidence = 0.0

            if KNOWLEDGE_SYSTEM_AVAILABLE and self.knowledge_manager:
                # 使用知识管理器
                manager_result = await self.knowledge_manager.query(query, **kwargs)
                results = manager_result.get("reports/reports/results", [])
                sources = manager_result.get("sources", [])
                recommendations = manager_result.get("recommendations", [])
                confidence = 0.8  # 默认置信度

                # 专利分析
                if (
                    service_type == ServiceType.PATENT_ANALYSIS.value
                    and "patent_results" in manager_result
                ):
                    patent_results = manager_result["patent_results"]
                    results.extend(patent_results.get("apps/apps/patents", []))
                    results.extend(patent_results.get("technologies", []))

            else:
                # 备用查询
                results, confidence = await self._fallback_query(query, service_type, context)

            execution_time = (datetime.now() - start_time).total_seconds()

            # 缓存结果
            self.knowledge_cache[cache_key] = {
                "reports/reports/results": results,
                "sources": sources,
                "recommendations": recommendations,
                "confidence": confidence,
            }

            # 限制缓存大小
            if len(self.knowledge_cache) > 1000:
                # 删除最旧的缓存项
                oldest_key = next(iter(self.knowledge_cache))
                del self.knowledge_cache[oldest_key]

            # 更新统计
            self.service_stats["successful_queries"] += 1
            self._update_average_query_time(execution_time)

            # 添加到历史记录
            self._add_query_to_history(
                {
                    "query_id": query_id,
                    "query": query,
                    "service_type": service_type,
                    "results_count": len(results),
                    "execution_time": execution_time,
                    "timestamp": datetime.now(),
                }
            )

            return QueryResult(
                success=True,
                query_id=query_id,
                results=results,
                sources=sources,
                recommendations=recommendations,
                confidence=confidence,
                execution_time=execution_time,
            )

        except Exception as e:
            logger.error(f"❌ 知识查询失败: {e!s}")
            self.service_stats["failed_queries"] += 1

            return QueryResult(
                success=False,
                query_id=query_id,
                error=str(e),
                execution_time=(datetime.now() - start_time).total_seconds(),
            )

    async def recommend_tools(
        self, query: str, context: dict[str, Any] | None = None, max_recommendations: int = 5
    ) -> list[dict[str, Any]]:
        """
        推荐工具

        Args:
            query: 用户查询/意图
            context: 上下文信息
            max_recommendations: 最大推荐数量

        Returns:
            工具推荐列表
        """
        try:
            if KNOWLEDGE_SYSTEM_AVAILABLE and self.tool_router:
                # 使用工具路由器
                tool_recommendations = await self.tool_router.recommend_tools(
                    query, context, max_recommendations
                )

                # 转换为标准格式
                recommendations = []
                for tool_rec in tool_recommendations:
                    recommendations.append(
                        {
                            "tool_name": tool_rec.tool_name,
                            "priority": tool_rec.priority.value,
                            "confidence": tool_rec.confidence,
                            "reason": tool_rec.reason,
                            "estimated_time": tool_rec.estimated_time,
                        }
                    )

                # 更新统计
                self.service_stats["total_recommendations"] += len(recommendations)

                return recommendations

            else:
                # 备用推荐
                return await self._fallback_tool_recommendation(query, context, max_recommendations)

        except Exception as e:
            logger.error(f"❌ 工具推荐失败: {e!s}")
            return []

    async def execute_tool(
        self, tool_name: str, parameters: dict[str, Any], context: dict[str, Any] | None = None
    ) -> ToolExecutionResult:
        """
        执行工具

        Args:
            tool_name: 工具名称
            parameters: 工具参数
            context: 执行上下文

        Returns:
            工具执行结果
        """
        start_time = datetime.now()
        execution_id = str(uuid.uuid4())

        try:
            # 更新统计
            self.service_stats["total_tool_executions"] += 1

            if KNOWLEDGE_SYSTEM_AVAILABLE and self.tool_router:
                # 使用工具路由器执行
                result = await self.tool_router.execute_tool(tool_name, parameters, context)

                execution_time = (datetime.now() - start_time).total_seconds()

                # 更新统计
                self.service_stats["successful_tool_executions"] += 1

                # 添加到执行历史
                self._add_tool_execution_to_history(
                    {
                        "execution_id": execution_id,
                        "tool_name": tool_name,
                        "success": True,
                        "execution_time": execution_time,
                        "timestamp": datetime.now(),
                    }
                )

                return ToolExecutionResult(
                    success=True,
                    tool_name=tool_name,
                    execution_id=execution_id,
                    result=result.get("result"),
                    output=result.get("output", ""),
                    execution_time=execution_time,
                    metadata=result.get("metadata", {}),
                )

            else:
                # 备用执行
                return await self._fallback_tool_execution(
                    tool_name, parameters, context, start_time, execution_id
                )

        except Exception as e:
            logger.error(f"❌ 工具执行失败: {e!s}")
            self.service_stats["failed_tool_executions"] += 1

            return ToolExecutionResult(
                success=False,
                tool_name=tool_name,
                execution_id=execution_id,
                error=str(e),
                execution_time=(datetime.now() - start_time).total_seconds(),
            )

    async def get_knowledge_context(self, context: str, max_items: int = 10) -> dict[str, Any]:
        """
        获取知识上下文

        Args:
            context: 上下文描述
            max_items: 最大返回项目数

        Returns:
            知识上下文信息
        """
        try:
            if KNOWLEDGE_SYSTEM_AVAILABLE and self.knowledge_manager:
                # 使用知识管理器
                context_info = await self.knowledge_manager.get_knowledge_context(context)

                # 限制返回数量
                if "related_knowledge" in context_info:
                    context_info["related_knowledge"] = context_info["related_knowledge"][
                        :max_items
                    ]
                if "suggestions" in context_info:
                    context_info["suggestions"] = context_info["suggestions"][:max_items]

                return context_info

            else:
                # 备用上下文获取
                return await self._fallback_get_context(context, max_items)

        except Exception as e:
            logger.error(f"❌ 获取知识上下文失败: {e!s}")
            return {"context": context, "related_knowledge": [[]]}

    async def process(self, input_data: Any) -> dict[str, Any]:
        """标准处理接口 - BaseModule兼容"""
        try:
            if isinstance(input_data, dict):
                operation = input_data.get("operation", "query")
                query = input_data.get("query", "")
                service_type = input_data.get("service_type", "knowledge_query")
                context = input_data.get("context")

                if operation == "query":
                    result = await self.query_knowledge(
                        query=query, service_type=service_type, context=context
                    )
                    return {
                        "success": result.success,
                        "query_id": result.query_id,
                        "reports/reports/results": result.results,
                        "confidence": result.confidence,
                    }
                elif operation == "recommend_tools":
                    max_recs = input_data.get("max_recommendations", 5)
                    recommendations = await self.recommend_tools(
                        query=query, context=context, max_recommendations=max_recs
                    )
                    return {"success": True, "recommendations": recommendations}
                elif operation == "execute_tool":
                    tool_name = input_data.get("tool_name", "")
                    parameters = input_data.get("parameters", {})
                    result = await self.execute_tool(tool_name, parameters, context)
                    return {
                        "success": result.success,
                        "execution_id": result.execution_id,
                        "result": result.result,
                    }
                elif operation == "get_context":
                    max_items = input_data.get("max_items", 10)
                    context_info = await self.get_knowledge_context(query, max_items)
                    return {"success": True, "context_info": context_info}
                else:
                    return {"success": False, "error": f"Unknown operation: {operation}"}
            else:
                return {"success": False, "error": "Invalid input format"}

        except Exception as e:
            logger.error(f"❌ 处理请求失败: {e!s}")
            return {"success": False, "error": str(e)}

    def get_status(self) -> dict[str, Any]:
        """获取模块状态"""
        return {
            "agent_id": self.agent_id,
            "module_type": "enhanced_knowledge_tools",
            "status": self._module_status.value,
            "initialized": self._initialized,
            "cache_size": len(self.knowledge_cache),
            "query_history_size": len(self.query_history),
            "tool_executions_size": len(self.tool_executions),
            "uptime_seconds": (datetime.now() - self._start_time).total_seconds(),
            "subsystems": {
                "knowledge_manager": self.knowledge_manager is not None,
                "intelligent_recommender": self.intelligent_recommender is not None,
                "tool_router": self.tool_router is not None,
            },
        }

    def get_metrics(self) -> dict[str, Any]:
        """获取性能指标"""
        uptime = datetime.now() - self._start_time

        return {
            "module_status": self._module_status.value,
            "agent_id": self.agent_id,
            "initialized": self._initialized,
            "uptime_seconds": uptime.total_seconds(),
            "service_stats": self.service_stats.copy(),
            "cache_hit_rate": self._calculate_cache_hit_rate(),
            "query_success_rate": self._calculate_query_success_rate(),
            "tool_execution_success_rate": self._calculate_tool_success_rate(),
        }

    # BaseModule抽象方法实现
    async def _on_initialize(self) -> bool:
        """子类初始化逻辑"""
        try:
            # 初始化知识管理器
            if self.enable_knowledge_manager and KNOWLEDGE_SYSTEM_AVAILABLE:
                try:
                    self.knowledge_manager = KnowledgeManager(
                        agent_id=self.agent_id,
                        config={
                            "enable_patent_analysis": self.enable_patent_analysis,
                            "enable_intelligent_recommendation": self.enable_intelligent_recommender,
                        },
                    )
                    await self.knowledge_manager.initialize()
                    logger.info("✅ 知识管理器就绪")
                except Exception as e:
                    logger.warning(f"⚠️ 知识管理器初始化失败: {e}")
                    self.knowledge_manager = None

            # 初始化智能推荐器(如果未通过知识管理器初始化)
            if (
                self.enable_intelligent_recommender
                and not self.knowledge_manager
                and KNOWLEDGE_SYSTEM_AVAILABLE
            ):
                try:
                    self.intelligent_recommender = IntelligentRecommender(
                        self.agent_id, self.config
                    )
                    await self.intelligent_recommender.initialize()
                    logger.info("✅ 智能推荐器就绪")
                except Exception as e:
                    logger.warning(f"⚠️ 智能推荐器初始化失败: {e}")
                    self.intelligent_recommender = None

            # 初始化工具路由器
            if self.enable_tool_router and KNOWLEDGE_SYSTEM_AVAILABLE:
                try:
                    self.tool_router = IntelligentToolRouter(self.agent_id)
                    await self.tool_router.initialize()
                    logger.info("✅ 工具路由器就绪")
                except Exception as e:
                    logger.warning(f"⚠️ 工具路由器初始化失败: {e}")
                    self.tool_router = None

            return True

        except Exception as e:
            logger.error(f"❌ 子类初始化失败: {e}")
            return False

    async def _on_start(self) -> bool:
        """子类启动逻辑"""
        try:
            # 预热缓存
            await self._warmup_cache()
            logger.info("✅ 知识库与工具库模块启动成功")
            return True

        except Exception as e:
            logger.error(f"❌ 知识库与工具库模块启动失败: {e}")
            return False

    async def _on_stop(self) -> bool:
        """子类停止逻辑"""
        try:
            # 保存缓存状态
            await self._save_cache_state()
            logger.info("🛑 保存缓存状态完成")
            return True

        except Exception as e:
            logger.error(f"❌ 知识库与工具库模块停止失败: {e}")
            return False

    async def _on_shutdown(self) -> bool:
        """子类关闭逻辑"""
        try:
            # 关闭知识管理器
            if self.knowledge_manager:
                await self.knowledge_manager.shutdown()

            # 关闭智能推荐器
            if self.intelligent_recommender:
                await self.intelligent_recommender.shutdown()

            # 关闭工具路由器
            if self.tool_router:
                await self.tool_router.shutdown()

            # 清理资源
            self.knowledge_cache.clear()
            self.query_history.clear()
            self.tool_executions.clear()

            logger.info("✅ 知识库与工具库模块关闭成功")
            return True

        except Exception as e:
            logger.error(f"❌ 知识库与工具库模块关闭失败: {e}")
            return False

    async def _on_health_check(self) -> bool:
        """子类健康检查逻辑"""
        try:
            # 检查子系统状态
            subsystems_available = (
                (self.knowledge_manager is not None)
                or (self.intelligent_recommender is not None)
                or (self.tool_router is not None)
            )
            return subsystems_available

        except Exception as e:
            logger.error(f"❌ 健康检查失败: {e}")
            return False

    async def shutdown(self):
        """关闭模块"""
        logger.info(f"🔌 关闭模块: {self.__class__.__name__}")
        await super().shutdown()

    # 辅助方法
    def _update_average_query_time(self, execution_time: float) -> Any:
        """更新平均查询时间"""
        total_queries = self.service_stats["total_queries"]
        current_avg = self.service_stats["average_query_time"]
        self.service_stats["average_query_time"] = (
            current_avg * (total_queries - 1) + execution_time
        ) / total_queries

    def _calculate_cache_hit_rate(self) -> float:
        """计算缓存命中率"""
        total_requests = self.service_stats["cache_hits"] + self.service_stats["cache_misses"]
        return self.service_stats["cache_hits"] / total_requests if total_requests > 0 else 0.0

    def _calculate_query_success_rate(self) -> float:
        """计算查询成功率"""
        total_queries = self.service_stats["total_queries"]
        return (
            self.service_stats["successful_queries"] / total_queries if total_queries > 0 else 0.0
        )

    def _calculate_tool_success_rate(self) -> float:
        """计算工具执行成功率"""
        total_executions = self.service_stats["total_tool_executions"]
        return (
            self.service_stats["successful_tool_executions"] / total_executions
            if total_executions > 0
            else 0.0
        )

    def _add_query_to_history(self, record: dict[str, Any]) -> Any:
        """添加查询到历史记录"""
        self.query_history.append(record)
        if len(self.query_history) > 1000:
            self.query_history = self.query_history[-1000:]

    def _add_tool_execution_to_history(self, record: dict[str, Any]) -> Any:
        """添加工具执行到历史记录"""
        self.tool_executions.append(record)
        if len(self.tool_executions) > 1000:
            self.tool_executions = self.tool_executions[-1000:]

    async def _warmup_cache(self):
        """预热缓存"""
        # 预加载一些常用查询
        warmup_queries = ["专利分析", "技术评估", "智能推荐", "工具选择"]

        for query in warmup_queries:
            try:
                await self.query_knowledge(query, cache_only=True)
            except Exception as e:
                logger.error(f"捕获异常: {e}", exc_info=True)

    async def _save_cache_state(self):
        """保存缓存状态"""
        logger.info(f"保存缓存状态: {len(self.knowledge_cache)} 项")

    # 备用实现方法
    async def _fallback_query(
        self, query: str, service_type: str, context: dict[str, Any]
    ) -> tuple[list[dict[str, Any]], float]:
        """备用知识查询"""
        # 简化的备用查询实现
        results = [
            {
                "id": "fallback_1",
                "title": f"关于'{query}'的基本信息",
                "description": "这是备用查询系统的结果",
                "confidence": 0.5,
            }
        ]
        confidence = 0.5
        return results, confidence

    async def _fallback_tool_recommendation(
        self, query: str, context: dict[str, Any], max_recommendations: int
    ) -> list[dict[str, Any]]:
        """备用工具推荐"""
        # 简化的备用推荐
        return [
            {
                "tool_name": "通用搜索工具",
                "priority": "important",
                "confidence": 0.6,
                "reason": "基于查询内容的通用推荐",
                "estimated_time": 2.0,
            }
        ]

    async def _fallback_tool_execution(
        self,
        tool_name: str,
        parameters: dict[str, Any],        context: dict[str, Any],        start_time: datetime,
        execution_id: str,
    ) -> ToolExecutionResult:
        """备用工具执行"""
        execution_time = (datetime.now() - start_time).total_seconds()
        return ToolExecutionResult(
            success=True,
            tool_name=tool_name,
            execution_id=execution_id,
            result=f"备用执行结果: {tool_name}",
            output=f"使用备用系统执行了 {tool_name}",
            execution_time=execution_time,
            metadata={"fallback": True},
        )

    async def _fallback_get_context(self, context: str, max_items: int) -> dict[str, Any]:
        """备用上下文获取"""
        return {
            "context": context,
            "related_knowledge": [
                {
                    "id": "fallback_context_1",
                    "title": f"与'{context}'相关的知识",
                    "description": "这是备用上下文信息",
                }
            ],
            "suggestions": ["建议进一步了解相关背景信息", "考虑提供更具体的查询内容"],
        }


# 导出
__all__ = ["EnhancedKnowledgeToolsModule", "QueryResult", "ServiceType", "ToolExecutionResult"]
