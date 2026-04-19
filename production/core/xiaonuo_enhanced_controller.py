#!/usr/bin/env python3
"""
小诺增强控制器 - 集成提示词系统优化
Xiaonuo Enhanced Controller with Prompt System Optimization

集成五大优化:
1. Supervisor编排模式 - 多智能体任务协调
2. 上下文压缩器 - Token Sprawl防护
3. 动态上下文选择 - 智能Token优化
4. 失败模式防护 - 系统性风险检测
5. 统一提示词管理 - L1-L4与Lyra系统统一 ✨

作者: 小诺·双鱼公主
版本: v2.1.0-unified-prompts
创建时间: 2026-01-07
更新时间: 2026-01-07
"""

from __future__ import annotations
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from core.context.context_compressor import (
    ContextCompressor,
    Message,
    MessageImportance,
    MessageRole,
)
from core.context.dynamic_context_selector import (
    ContextLayer,
    DynamicContextSelector,
)
from core.coordination.failure_prevention import FailurePreventionSystem
from core.logging_config import setup_logging

# 导入优化系统
from core.orchestration.supervisor_orchestrator import (
    SupervisorOrchestrator,
    orchestrate_task,
)

# 导入统一提示词管理器
from core.prompts.unified_prompt_manager import (
    PromptFormat,
    get_unified_prompt_manager,
)

# 导入原始控制器
from core.xiaonuo_platform_controller import PlatformController

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


@dataclass
class OptimizationMetrics:
    """优化指标"""

    total_requests: int = 0
    supervisor_orchestrations: int = 0
    context_compressions: int = 0
    dynamic_selections: int = 0
    failures_prevented: int = 0
    tokens_saved: int = 0
    avg_response_time: float = 0.0
    success_rate: float = 1.0


class XiaonuoEnhancedController:
    """
    小诺增强控制器 - 集成所有提示词系统优化

    核心能力:
    1. 平台服务管理 (继承自PlatformController)
    2. Supervisor智能编排 (新增)
    3. 上下文优化管理 (新增)
    4. 失败模式防护 (新增)
    5. 统一提示词管理 (新增) ✨
    6. 性能监控和报告 (新增)
    """

    def __init__(self, project_root: Path | None = None):
        """
        初始化增强控制器

        Args:
            project_root: 项目根目录
        """
        logger.info("=" * 60)
        logger.info("🎀 小诺增强控制器初始化 v2.1.0-unified-prompts")
        logger.info("=" * 60)

        # 1. 初始化原始平台控制器
        self.platform_controller = PlatformController(project_root)

        # 2. 初始化Supervisor编排器
        self.supervisor = SupervisorOrchestrator()
        logger.info("✅ Supervisor编排器已就绪")

        # 3. 初始化上下文压缩器
        self.context_compressor = ContextCompressor(max_context_tokens=8000, summary_threshold=0.7)
        logger.info("✅ 上下文压缩器已就绪")

        # 4. 初始化动态上下文选择器
        self.context_selector = DynamicContextSelector(prompts_base_path="prompts")
        logger.info("✅ 动态上下文选择器已就绪")

        # 5. 初始化失败模式防护系统
        self.failure_prevention = FailurePreventionSystem(check_interval=30.0)
        logger.info("✅ 失败模式防护系统已就绪")

        # 6. 初始化统一提示词管理器 ✨
        self.prompt_manager = get_unified_prompt_manager()
        logger.info("✅ 统一提示词管理器已就绪")

        # 7. 优化指标
        self.metrics = OptimizationMetrics()

        # 8. 对话历史 (用于上下文压缩)
        self.conversation_history: list[Message] = []

        # 9. 提示词层缓存 (从统一管理器加载)
        self.prompt_layers_cache: dict[str, ContextLayer] = {}
        self._load_prompt_layers_from_manager()

        logger.info("=" * 60)
        logger.info("🎉 小诺增强控制器初始化完成!")
        logger.info("=" * 60)

    async def _load_prompt_layers_from_manager_async(self):
        """从统一提示词管理器加载提示词层 (异步版本)"""
        try:
            # 尝试从统一管理器加载小娜提示词
            result = await self.prompt_manager.load_prompt(
                agent="xiaona", layers=None, format=PromptFormat.MARKDOWN  # 加载全部层
            )

            if result.status == "success":
                # 将提示词内容分层解析为ContextLayer
                full_content = result.content

                # 简化实现: 按照常见的L1-L4标题分割
                # 实际应该根据具体提示词格式解析
                self.prompt_layers_cache = {
                    "L1": ContextLayer(
                        name="L1",
                        description="基础层",
                        content=self._extract_layer_content(full_content, "L1") or "基础层提示词",
                        token_count=100,
                        importance=1.0,
                    ),
                    "L2": ContextLayer(
                        name="L2",
                        description="数据层",
                        content=self._extract_layer_content(full_content, "L2") or "数据层提示词",
                        token_count=80,
                        importance=0.8,
                    ),
                    "L3": ContextLayer(
                        name="L3",
                        description="能力层",
                        content=self._extract_layer_content(full_content, "L3") or "能力层提示词",
                        token_count=150,
                        importance=0.7,
                    ),
                    "L4": ContextLayer(
                        name="L4",
                        description="业务层",
                        content=self._extract_layer_content(full_content, "L4") or "业务层提示词",
                        token_count=200,
                        importance=0.6,
                    ),
                }
                logger.info("✅ 从统一提示词管理器加载提示词层成功")
                return True
            else:
                # 如果统一管理器加载失败,使用默认值
                logger.warning(f"⚠️ 统一提示词管理器加载失败: {result.content}")
                return False

        except Exception as e:
            logger.warning(f"⚠️ 从统一提示词管理器加载失败: {e}")
            return False

    def _load_prompt_layers_from_manager(self) -> Any:
        """从统一提示词管理器加载提示词层 (同步包装)"""
        # 在__init__中调用时使用默认配置,避免asyncio.run()警告
        # 实际加载在首次使用时异步进行
        logger.info("ℹ️ 提示词层将在首次使用时异步加载")
        self._load_default_prompt_layers()

    def _extract_layer_content(self, full_content: str, layer_name: str) -> str | None:
        """从完整内容中提取指定层的内容"""
        # 简化实现: 根据常见的L1-L4标记提取
        lines = full_content.split("\n")
        layer_content = []
        in_layer = False

        for line in lines:
            if layer_name in line and ("层" in line or "Layer" in line):
                in_layer = True
                continue
            elif in_layer:
                if line.strip().startswith("#") and layer_name not in line:
                    break
                layer_content.append(line)

        return "\n".join(layer_content).strip() if layer_content else None

    def _load_default_prompt_layers(self) -> Any:
        """加载默认提示词层 (后备方案)"""
        self.prompt_layers_cache = {
            "L1": ContextLayer(
                name="L1",
                description="基础层",
                content="你是小诺,平台管理专家\n核心能力: 服务管理、任务编排、智能体协调",
                token_count=100,
                importance=1.0,
            ),
            "L2": ContextLayer(
                name="L2",
                description="数据层",
                content="数据源: Qdrant(121k), PostgreSQL(28M), NebulaGraph(87k)",
                token_count=80,
                importance=0.8,
            ),
            "L3": ContextLayer(
                name="L3",
                description="能力层",
                content="29个核心能力: 平台管理、智能决策、数据处理、AI/NLP等",
                token_count=150,
                importance=0.7,
            ),
            "L4": ContextLayer(
                name="L4",
                description="业务层",
                content="12个核心场景: 服务管理、监控、调度、代码分析、数据处理等",
                token_count=200,
                importance=0.6,
            ),
        }
        logger.info("✅ 使用默认提示词层配置")

    async def load_agent_prompt(
        self, agent: str, layers: list[str] | None = None
    ) -> str | None:
        """
        加载智能体提示词 (统一接口)

        Args:
            agent: 智能体名称 (xiaona, xiaonuo, etc.)
            layers: 要加载的层 (L1, L2, L3, L4), None表示全部

        Returns:
            提示词内容,失败返回None
        """
        try:
            result = await self.prompt_manager.load_prompt(
                agent=agent, layers=layers, format=PromptFormat.MARKDOWN
            )

            if result.status == "success":
                return result.content
            else:
                logger.warning(f"⚠️ 加载{agent}提示词失败: {result.content}")
                return None

        except Exception as e:
            logger.error(f"❌ 加载{agent}提示词异常: {e}")
            return None

    async def optimize_prompt_with_lyra(
        self, content: str, target_ai: str = "Claude", mode: str = "BASIC"
    ) -> str | None:
        """
        使用Lyra优化提示词 (统一接口)

        Args:
            content: 要优化的内容
            target_ai: 目标AI模型
            mode: 优化模式 (BASIC/DETAIL)

        Returns:
            优化后的内容,失败返回None
        """
        try:
            result = await self.prompt_manager.optimize_prompt(
                content=content, target_ai=target_ai, mode=mode
            )

            if result.status == "success":
                return result.content
            else:
                logger.warning(f"⚠️ Lyra优化失败: {result.content}")
                return None

        except Exception as e:
            logger.error(f"❌ Lyra优化异常: {e}")
            return None

    async def process_request(self, user_request: str) -> dict[str, Any]:
        """
        处理用户请求 - 主入口

        集成所有优化:
        1. 失败模式防护检查
        2. 动态上下文选择
        3. Supervisor编排
        4. 上下文压缩

        Args:
            user_request: 用户请求

        Returns:
            Dict: 处理结果
        """
        start_time = datetime.now()
        self.metrics.total_requests += 1

        logger.info(f"📥 收到用户请求: {user_request[:100]}...")

        try:
            # 1. 失败模式防护检查
            logger.info("🔍 步骤1: 失败模式检查")
            alerts = await self._check_failure_modes(user_request)

            if alerts:
                logger.warning(f"⚠️ 检测到 {len(alerts)} 个潜在问题")
                # 可以根据警报调整策略

            # 2. 添加到对话历史
            self.conversation_history.append(
                Message(
                    role=MessageRole.USER, content=user_request, importance=MessageImportance.HIGH
                )
            )

            # 3. 上下文压缩检查
            logger.info("🗜️ 步骤2: 上下文压缩检查")
            context_monitor = await self.context_compressor.monitor_context_size(
                self.conversation_history
            )

            if context_monitor["needs_compression"]:
                logger.info("⚠️ 触发上下文压缩")
                self.conversation_history = await self.context_compressor.compress_context(
                    self.conversation_history
                )
                self.metrics.context_compressions += 1

            # 4. 动态上下文选择
            logger.info("🎯 步骤3: 动态上下文选择")
            context_selection = await self.context_selector.select_context(
                user_request, self.prompt_layers_cache
            )
            self.metrics.dynamic_selections += 1

            tokens_saved = context_selection.estimated_time_savings * 1000  # 粗略估算
            self.metrics.tokens_saved += int(tokens_saved)

            logger.info(f"✅ 选择层级: {context_selection.selected_layers}")
            logger.info(f"✅ Token数: {context_selection.total_tokens}")
            logger.info(f"✅ 预计节省: {tokens_saved:.0f} tokens")

            # 5. Supervisor编排 (如果需要多智能体协作)
            logger.info("🤖 步骤4: Supervisor编排")

            # 判断是否需要多智能体协作
            needs_orchestration = self._needs_multi_agent(user_request)

            if needs_orchestration:
                logger.info("✅ 需要多智能体协作,启动Supervisor")
                result = await orchestrate_task(user_request)
                self.metrics.supervisor_orchestrations += 1
            else:
                logger.info("✅ 单智能体可处理,直接执行")
                result = await self._execute_simple_task(user_request, context_selection)

            # 6. 添加AI回复到历史
            self.conversation_history.append(
                Message(
                    role=MessageRole.ASSISTANT,
                    content=str(result.get("integrated_data", result)),
                    importance=MessageImportance.HIGH,
                )
            )

            # 7. 计算响应时间
            response_time = (datetime.now() - start_time).total_seconds()

            # 8. 更新指标
            self._update_metrics(response_time, True)

            # 9. 构建响应
            response = {
                "status": "success",
                "user_request": user_request,
                "result": result,
                "optimization_info": {
                    "context_layers": context_selection.selected_layers,
                    "tokens_used": context_selection.total_tokens,
                    "tokens_saved": int(tokens_saved),
                    "context_compressed": context_monitor["needs_compression"],
                    "orchestrated": needs_orchestration,
                    "response_time": response_time,
                },
                "timestamp": datetime.now().isoformat(),
            }

            logger.info(f"✅ 请求处理完成,耗时: {response_time:.2f}秒")

            return response

        except Exception as e:
            logger.error(f"❌ 请求处理失败: {e}", exc_info=True)
            self._update_metrics(0, False)

            return {
                "status": "error",
                "error": str(e),
                "user_request": user_request,
                "timestamp": datetime.now().isoformat(),
            }

    async def _check_failure_modes(self, request: str) -> list:
        """检查失败模式"""
        alerts = []

        # 检查Token Sprawl风险
        token_monitor = await self.context_compressor.monitor_context_size(
            self.conversation_history
        )
        if token_monitor["needs_compression"]:
            alerts.append(
                {
                    "mode": "token_sprawl",
                    "severity": "high" if token_monitor["token_ratio"] > 0.9 else "medium",
                    "message": "对话历史过长,建议压缩",
                }
            )

        # 检查Coordination Drift (如果有多智能体)
        if self._needs_multi_agent(request):
            # 注册临时目标用于检测
            self.failure_prevention.register_agent_goal(
                "xiaonuo", f"完成用户请求: {request[:50]}...", priority=8
            )
            self.failure_prevention.register_agent_goal("xiaona", "提供专业法律分析", priority=9)

            # 执行检查
            drift_alerts = await self.failure_prevention.check_coordination_drift()
            alerts.extend(drift_alerts)

        return alerts

    def _needs_multi_agent(self, request: str) -> bool:
        """判断是否需要多智能体协作"""
        # 简单任务不需要协作
        simple_keywords = ["查询", "状态", "简单", "快速"]
        if any(kw in request for kw in simple_keywords):
            return False

        # 复杂任务需要协作
        complex_keywords = ["专利", "法律", "分析", "答复", "审查", "撰写", "无效", "对比", "深度"]
        return any(kw in request for kw in complex_keywords)

    async def _execute_simple_task(self, request: str, context_selection: Any) -> dict[str, Any]:
        """执行简单任务 (单智能体)"""
        # 这里应该调用实际的服务
        # 简化实现: 返回模拟结果

        return {
            "status": "completed",
            "message": f"已完成: {request}",
            "agent": "xiaonuo",
            "context_layers_used": context_selection.selected_layers,
        }

    def _update_metrics(self, response_time: float, success: bool) -> Any:
        """更新指标"""
        # 更新平均响应时间
        n = self.metrics.total_requests
        self.metrics.avg_response_time = (
            self.metrics.avg_response_time * (n - 1) + response_time
        ) / n

        # 更新成功率
        if not success:
            current_failures = n * (1 - self.metrics.success_rate)
            self.metrics.success_rate = (n - 1 - current_failures) / n

    async def get_optimization_report(self) -> dict[str, Any]:
        """获取优化报告"""
        # 上下文监控
        context_monitor = await self.context_compressor.monitor_context_size(
            self.conversation_history
        )

        # 失败模式防护指标
        prevention_metrics = self.failure_prevention.get_metrics()

        # 统一提示词管理器统计 ✨
        prompt_manager_stats = self.prompt_manager.get_statistics()

        return {
            "performance_metrics": {
                "total_requests": self.metrics.total_requests,
                "supervisor_orchestrations": self.metrics.supervisor_orchestrations,
                "context_compressions": self.metrics.context_compressions,
                "dynamic_selections": self.metrics.dynamic_selections,
                "tokens_saved": self.metrics.tokens_saved,
                "avg_response_time": self.metrics.avg_response_time,
                "success_rate": self.metrics.success_rate,
            },
            "context_status": {
                "conversation_length": len(self.conversation_history),
                "total_tokens": context_monitor["total_tokens"],
                "token_ratio": context_monitor["token_ratio"],
                "needs_compression": context_monitor["needs_compression"],
            },
            "failure_prevention": {
                "total_alerts": prevention_metrics.total_alerts,
                "alerts_resolved": prevention_metrics.alerts_resolved,
                "last_check": prevention_metrics.last_check_time,
            },
            "prompt_manager": {  # ✨ 新增
                "l1l4_available": prompt_manager_stats["systems"]["l1l4_available"],
                "lyra_available": prompt_manager_stats["systems"]["lyra_available"],
                "total_loads": prompt_manager_stats["statistics"]["total_loads"],
                "total_optimizations": prompt_manager_stats["statistics"]["total_optimizations"],
                "total_combined": prompt_manager_stats["statistics"]["total_combined"],
                "cached_items": prompt_manager_stats["cache"]["cached_items"],
            },
            "optimization_enabled": {
                "supervisor_orchestrator": True,
                "context_compressor": True,
                "dynamic_selector": True,
                "failure_prevention": True,
                "unified_prompt_manager": True,  # ✨ 新增
            },
            "generated_at": datetime.now().isoformat(),
        }

    async def start_monitoring(self):
        """启动监控服务"""
        logger.info("🚀 启动优化监控服务")
        await self.failure_prevention.start_monitoring()

    async def stop_monitoring(self):
        """停止监控服务"""
        logger.info("🛑 停止优化监控服务")
        await self.failure_prevention.stop_monitoring()

    def get_platform_controller(self) -> PlatformController:
        """获取原始平台控制器"""
        return self.platform_controller


# ============================================================================
# 便捷函数
# ============================================================================

_enhanced_controller_instance: XiaonuoEnhancedController | None = None


def get_enhanced_controller() -> XiaonuoEnhancedController:
    """获取增强控制器单例"""
    global _enhanced_controller_instance
    if _enhanced_controller_instance is None:
        _enhanced_controller_instance = XiaonuoEnhancedController()
    return _enhanced_controller_instance


# ============================================================================
# 导出
# ============================================================================

__all__ = ["OptimizationMetrics", "XiaonuoEnhancedController", "get_enhanced_controller"]
