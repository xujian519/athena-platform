from __future__ import annotations
"""
统一LLM层 - 统一LLM管理器
核心协调者,管理所有模型适配器,提供统一的调用接口

作者: Claude Code
日期: 2026-01-23
"""

import asyncio
import logging
from datetime import datetime
from typing import Any

from core.llm.base import (
    BaseLLMAdapter,
    LLMRequest,
    LLMResponse,
)
from core.llm.cache_warmer import get_cache_warmer
from core.llm.cost_monitor import get_cost_monitor
from core.llm.model_registry import ModelCapabilityRegistry, get_model_registry
from core.llm.model_selector import IntelligentModelSelector
from core.llm.prometheus_metrics import get_metrics
from core.llm.response_cache import get_response_cache

# 智能模型路由 (Hermes Agent 设计模式)
try:
    from core.llm.smart_model_routing import RoutingDecision, SmartModelRouter
    SMART_ROUTING_AVAILABLE = True
except ImportError:
    SMART_ROUTING_AVAILABLE = False
    SmartModelRouter = None  # type: ignore
    RoutingDecision = None  # type: ignore

logger = logging.getLogger(__name__)


class UnifiedLLMManager:
    """
    统一LLM管理器

    职责:
    1. 管理所有模型适配器
    2. 智能选择模型
    3. 统一调用接口
    4. 监控和统计
    """

    def __init__(self, registry: ModelCapabilityRegistry = None):
        """
        初始化管理器

        Args:
            registry: 模型能力注册表(可选)
        """
        # 核心组件
        self.registry = registry or get_model_registry()
        self.selector = IntelligentModelSelector(self.registry)
        self.adapters: dict[str, BaseLLMAdapter] = {}

        # 提示词管理器(可选)
        self.prompt_manager = None
        self._init_prompt_manager()

        # 成本监控器
        self.cost_monitor = get_cost_monitor()

        # 响应缓存
        self.response_cache = get_response_cache()

        # 缓存预热器
        self.cache_warmer = get_cache_warmer(
            registry=self.registry,
            response_cache=self.response_cache,
            enabled=True,  # 默认启用缓存预热
        )

        # Prometheus监控指标
        self.metrics = get_metrics(enabled=True)

        # 统计信息
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "model_usage": {},
            "total_cost": 0.0,
            "total_tokens": 0,
            "total_processing_time": 0.0,
            "warmup_results": None,  # 缓存预热结果
            "smart_routing_savings": 0.0,  # 智能路由节省的成本
        }

        # 智能模型路由器 (Hermes Agent 设计模式)
        self.smart_router: SmartModelRouter | None = None
        self._smart_routing_enabled = False
        if SMART_ROUTING_AVAILABLE and SmartModelRouter is not None:
            try:
                self.smart_router = SmartModelRouter()
                self._smart_routing_enabled = True
                logger.info("✅ 智能模型路由器已启用")
            except Exception as e:
                logger.warning(f"⚠️ 智能模型路由器初始化失败: {e}")

        logger.info("✅ 统一LLM管理器初始化完成")

    def _init_prompt_manager(self):
        """初始化提示词管理器"""
        try:
            from core.prompts.unified_prompt_manager import get_unified_prompt_manager

            self.prompt_manager = get_unified_prompt_manager()
            logger.info("✅ 提示词管理器已加载")
        except ImportError as e:
            logger.warning(f"⚠️ 提示词管理器不可用: {e}")
        except Exception as e:
            logger.warning(f"⚠️ 提示词管理器初始化失败: {e}", exc_info=True)

    async def initialize(self, enable_cache_warmup: bool = True, warmup_cache: bool = False):
        """
        初始化管理器

        Args:
            enable_cache_warmup: 是否启用缓存预热
            warmup_cache: 是否预热响应缓存(默认false,因为真实数据需要LLM调用)

        加载所有模型适配器并初始化
        """
        logger.info("🔄 初始化统一LLM管理器...")

        # 加载所有适配器
        await self._load_adapters()

        # 缓存预热(可选)
        if enable_cache_warmup and self.cache_warmer:
            try:
                warmup_results = await self.cache_warmer.warmup(
                    warmup_models=True, warmup_cache=warmup_cache
                )
                self.stats["warmup_results"] = warmup_results

                if warmup_results.get("errors"):
                    logger.warning(f"⚠️ 缓存预热完成但有 {len(warmup_results['errors'])} 个错误")
            except Exception as e:
                logger.error(f"❌ 缓存预热失败: {e}", exc_info=True)

        logger.info("✅ 统一LLM管理器初始化完成")

    async def _load_adapters(self):
        """加载所有模型适配器"""
        # 加载Ollama适配器(优先本地模型)
        await self._load_ollama_adapters()

        # 加载GLM适配器
        await self._load_glm_adapters()

        # 加载DeepSeek适配器
        await self._load_deepseek_adapters()

        # 加载LocalLLM适配器
        await self._load_local_adapters()

        # 加载Qwen适配器
        await self._load_qwen_adapters()

        logger.info(f"✅ 加载了 {len(self.adapters)} 个模型适配器")

    async def _load_glm_adapters(self):
        """加载GLM模型适配器"""
        glm_models = ["glm-4-plus", "glm-4-flash"]
        for model_id in glm_models:
            try:
                # 动态导入以避免循环依赖
                from core.llm.adapters.glm_adapter import GLMAdapter

                capability = self.registry.get_capability(model_id)
                if capability:
                    adapter = GLMAdapter(model_id, capability)
                    if await adapter.initialize():
                        self.adapters[model_id] = adapter
            except Exception as e:
                logger.warning(f"⚠️ GLM模型 {model_id} 适配器加载失败: {e}")

    async def _load_deepseek_adapters(self):
        """加载DeepSeek模型适配器"""
        deepseek_models = ["deepseek-chat", "deepseek-reasoner"]
        for model_id in deepseek_models:
            try:
                from core.llm.adapters.deepseek_adapter import DeepSeekAdapter

                capability = self.registry.get_capability(model_id)
                if capability:
                    adapter = DeepSeekAdapter(model_id, capability)
                    if await adapter.initialize():
                        self.adapters[model_id] = adapter
            except Exception as e:
                logger.warning(f"⚠️ DeepSeek模型 {model_id} 适配器加载失败: {e}")

    async def _load_local_adapters(self):
        """加载本地模型适配器"""
        local_models = ["qwen2.5-7b-instruct-gguf"]
        for model_id in local_models:
            try:
                from core.llm.adapters.local_llm_adapter import LocalLLMAdapter

                capability = self.registry.get_capability(model_id)
                if capability:
                    adapter = LocalLLMAdapter(model_id, capability)
                    if await adapter.initialize():
                        self.adapters[model_id] = adapter
            except Exception as e:
                logger.warning(f"⚠️ 本地模型 {model_id} 适配器加载失败: {e}")

    async def _load_ollama_adapters(self):
        """加载Ollama模型适配器"""
        # Ollama模型列表(本地模型优先)
        ollama_models = ["glm-4.7-flash:q4_K_M", "glm-4.7-flash", "qwen2.5-14b", "qwen2.5-7b"]

        for model_id in ollama_models:
            try:
                from core.llm.adapters.ollama_adapter import OllamaAdapter

                # 先尝试从registry获取
                capability = self.registry.get_capability(model_id)

                # 如果registry中没有,使用默认配置
                if not capability:
                    from core.llm.base import DeploymentType, ModelCapability, ModelType
                    capability = ModelCapability(
                        model_id=model_id,
                        model_type=ModelType.CHAT,
                        deployment=DeploymentType.LOCAL,
                        max_context=128000,
                        supports_streaming=True,
                        cost_per_1k_tokens=0.0,
                        quality_score=0.90,
                    )

                adapter = OllamaAdapter(model_id, capability)
                if await adapter.initialize():
                    self.adapters[model_id] = adapter
                    logger.info(f"✅ Ollama模型加载成功: {model_id}")
            except Exception as e:
                logger.warning(f"⚠️ Ollama模型 {model_id} 适配器加载失败: {e}")

    async def _load_qwen_adapters(self):
        """加载Qwen云端模型适配器"""
        qwen_models = ["qwen-plus", "qwen-max"]
        for model_id in qwen_models:
            try:
                from core.llm.adapters.qwen_adapter import QwenAdapter

                capability = self.registry.get_capability(model_id)
                if capability:
                    adapter = QwenAdapter(model_id, capability)
                    if await adapter.initialize():
                        self.adapters[model_id] = adapter
            except Exception as e:
                logger.warning(f"⚠️ Qwen模型 {model_id} 适配器加载失败: {e}")

    async def generate(
        self, message: str, task_type: str, context: dict | None = None, **kwargs
    ) -> LLMResponse:
        """
        统一生成接口

        Args:
            message: 用户消息
            task_type: 任务类型
            context: 上下文信息
            **kwargs: 其他参数(temperature, max_tokens, stream, enable_thinking等)

        Returns:
            LLMResponse: 统一响应对象
        """
        start_time = datetime.now()
        self.stats["total_requests"] += 1

        try:
            # 0.1 输入验证
            # 验证message长度
            if not message or not isinstance(message, str):
                logger.warning(f"⚠️ 无效的message参数: type={type(message)}, value={message}")
                return LLMResponse(content="无效的输入:消息不能为空", model_used="none")

            # 检查message长度(防止超长输入)
            MAX_MESSAGE_LENGTH = 50000  # 50K字符限制
            message_length = len(message)
            if message_length > MAX_MESSAGE_LENGTH:
                logger.warning(
                    f"⚠️ Message长度超过限制: {message_length} > {MAX_MESSAGE_LENGTH} "
                    f"(task_type={task_type})"
                )
                return LLMResponse(
                    content=f"输入过长:消息长度为{message_length}字符,超过限制{MAX_MESSAGE_LENGTH}字符",
                    model_used="none",
                )

            # 验证task_type
            # 定义支持的任务类型白名单
            SUPPORTED_TASK_TYPES = {
                "simple_chat",
                "simple_qa",
                "general_chat",
                "patent_search",
                "tech_analysis",
                "novelty_analysis",
                "creativity_analysis",
                "invalidation_analysis",
                "oa_response",
                "reasoning",
                "complex_analysis",
                "math_reasoning",
                "general_analysis",
                "reflection",  # 反思评估任务
                "quality_evaluation",  # 质量评估任务
            }

            if not task_type or task_type not in SUPPORTED_TASK_TYPES:
                logger.warning(
                    f"⚠️ 不支持的task_type: {task_type}. "
                    f"支持的类型: {', '.join(sorted(SUPPORTED_TASK_TYPES))}"
                )
                return LLMResponse(content=f"不支持的任务类型: {task_type}", model_used="none")

            # 0.2 检查缓存(在模型选择之前)
            cached_entry = self.response_cache.get(message, task_type)
            if cached_entry:
                logger.info(f"💾 使用缓存响应 (任务: {task_type})")

                # 记录缓存命中到metrics
                processing_time = (datetime.now() - start_time).total_seconds()
                self.metrics.record_request(
                    model_id=cached_entry.model_used,
                    task_type=task_type,
                    status="cached",
                    duration=processing_time,
                    tokens=cached_entry.tokens_used,
                    cost=0.0,
                    cached=True,
                )
                self.metrics.record_cache_hit(task_type)

                return LLMResponse(
                    content=cached_entry.response_content,
                    model_used=cached_entry.model_used,
                    tokens_used=cached_entry.tokens_used,
                    processing_time=0.001,  # 缓存响应几乎无延迟
                    cost=0.0,  # 缓存响应无成本
                    quality_score=1.0,
                    from_cache=True,
                )

            # 1. 构建请求
            request = LLMRequest(
                message=message, task_type=task_type, context=context or {}, **kwargs
            )

            # 2. 智能选择模型
            model_id = await self.selector.select_model(request)
            if not model_id:
                logger.error("❌ 没有可用的模型")
                return LLMResponse(
                    content="抱歉,暂时没有可用的模型来处理您的请求。", model_used="none"
                )

            # 3. 获取适配器
            adapter = self.adapters.get(model_id)
            if not adapter:
                logger.error(f"❌ 模型适配器不存在: {model_id}")
                return LLMResponse(content=f"模型 {model_id} 不可用。", model_used=model_id)

            # 4. 应用提示词系统
            if self.prompt_manager:
                system_prompt = await self._get_system_prompt(task_type, model_id)
                if system_prompt:
                    request.context["system_prompt"] = system_prompt

            # 5. 调用模型生成
            logger.info(f"🤖 使用模型 {model_id} 处理任务 {task_type}")
            response = await adapter.generate(request)

            # 6. 更新统计
            processing_time = (datetime.now() - start_time).total_seconds()
            response.processing_time = processing_time

            self.stats["successful_requests"] += 1
            self.stats["model_usage"][model_id] = self.stats["model_usage"].get(model_id, 0) + 1
            self.stats["total_cost"] += response.cost
            self.stats["total_tokens"] += response.tokens_used
            self.stats["total_processing_time"] += processing_time

            # 记录到Prometheus metrics
            self.metrics.record_request(
                model_id=model_id,
                task_type=task_type,
                status="success",
                duration=processing_time,
                tokens=response.tokens_used,
                cost=response.cost,
                cached=False,
            )
            self.metrics.record_cache_miss(task_type)  # 缓存未命中

            # 记录到成本监控器
            self.cost_monitor.record_cost(
                model_id=model_id,
                task_type=task_type,
                tokens_used=response.tokens_used,
                cost=response.cost,
                processing_time=processing_time,
            )

            # 存储到缓存
            if response.cost > 0:  # 只缓存有成本的响应
                self.response_cache.set(
                    message=message,
                    task_type=task_type,
                    response_content=response.content,
                    model_used=model_id,
                    tokens_used=response.tokens_used,
                    cost=response.cost,
                )

            logger.info(
                f"✅ 请求完成 (模型: {model_id}, "
                f"耗时: {processing_time:.2f}s, "
                f"tokens: {response.tokens_used}, "
                f"成本: ¥{response.cost:.4f})"
            )

            return response

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"❌ 生成失败: {e}", exc_info=True)
            self.stats["failed_requests"] += 1

            # 记录失败到metrics
            self.metrics.record_request(
                model_id="unknown",
                task_type=task_type,
                status="failure",
                duration=processing_time,
                tokens=0,
                cost=0.0,
                cached=False,
            )

            return LLMResponse(content=f"处理请求时出错: {e!s}", model_used="error")

    async def _get_system_prompt(self, task_type: str, model_id: str) -> str:
        """
        获取系统提示词

        Args:
            task_type: 任务类型
            model_id: 模型ID

        Returns:
            str: 系统提示词
        """
        try:
            # 根据任务类型获取对应的提示词
            agent_name = self._map_task_to_agent(task_type)
            if agent_name and self.prompt_manager:
                result = await self.prompt_manager.load_prompt(
                    agent=agent_name, layers=["L1", "L2"]  # 身份层+数据层
                )
                if result.status == "success":
                    return result.content
        except (AttributeError, KeyError, TypeError) as e:
            logger.warning(f"⚠️ 获取系统提示词失败: {e}", exc_info=True)
        except Exception as e:
            logger.warning(f"⚠️ 获取系统提示词发生未预期错误: {e}", exc_info=True)
        return ""

    def _map_task_to_agent(self, task_type: str) -> str | None:
        """
        将任务类型映射到智能体

        Args:
            task_type: 任务类型

        Returns:
            Optional[str]: 智能体名称
        """
        mapping = {
            "patent_search": "xiaona",
            "tech_analysis": "xiaona",
            "novelty_analysis": "xiaona",
            "creativity_analysis": "xiaona",
            "oa_response": "xiaona",
            "invalidation_analysis": "xiaona",
        }
        return mapping.get(task_type)

    async def health_check(self) -> dict[str, bool]:
        """
        健康检查所有模型

        Returns:
            dict[str, bool]: 模型ID到健康状态的映射
        """
        results = {}
        for model_id, adapter in self.adapters.items():
            try:
                results[model_id] = await adapter.health_check()
            except Exception as e:
                logger.warning(f"⚠️ 模型 {model_id} 健康检查失败: {e}")
                results[model_id] = False
        return results

    def get_stats(self) -> dict[str, Any]:
        """
        获取统计信息

        Returns:
            Dict: 统计信息
        """
        avg_processing_time = 0.0
        if self.stats["successful_requests"] > 0:
            avg_processing_time = (
                self.stats["total_processing_time"] / self.stats["successful_requests"]
            )

        return {
            **self.stats,
            "available_models": list(self.adapters.keys()),
            "total_models": len(self.adapters),
            "success_rate": (
                self.stats["successful_requests"] / self.stats["total_requests"]
                if self.stats["total_requests"] > 0
                else 0.0
            ),
            "avg_processing_time": avg_processing_time,
            "avg_cost_per_request": (
                self.stats["total_cost"] / self.stats["successful_requests"]
                if self.stats["successful_requests"] > 0
                else 0.0
            ),
        }

    def export_metrics(self) -> tuple[bytes, str]:
        """
        导出Prometheus格式的metrics

        Returns:
            tuple: (metrics数据, content_type)
        """
        return self.metrics.export_metrics(), self.metrics.get_content_type()

    def get_metrics_summary(self) -> dict[str, Any]:
        """
        获取metrics摘要信息

        Returns:
            Dict: metrics摘要
        """
        return self.metrics.get_summary()

    def get_available_models(self) -> list[str]:
        """
        获取可用模型列表

        Returns:
            list[str]: 可用模型ID列表
        """
        return list(self.adapters.keys())

    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "model_usage": {},
            "total_cost": 0.0,
            "total_tokens": 0,
            "total_processing_time": 0.0,
        }
        logger.info("✅ 统计信息已重置")

    def get_cost_report(self, time_window: str = "today") -> str:
        """
        获取成本报告

        Args:
            time_window: 时间窗口 (today, week, month, all)

        Returns:
            str: 格式化的成本报告
        """
        return self.cost_monitor.generate_report(time_window)

    def get_budget_status(self) -> dict[str, Any]:
        """
        获取预算状态

        Returns:
            Dict: 预算状态信息
        """
        return self.cost_monitor.check_budget_status()

    def get_recent_alerts(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        获取最近的告警

        Args:
            limit: 最大返回数量

        Returns:
            list[Dict]: 告警列表
        """
        alerts = self.cost_monitor.get_recent_alerts(limit)
        return [
            {
                "level": alert.level.value,
                "message": alert.message,
                "current_cost": alert.current_cost,
                "threshold": alert.threshold,
                "timestamp": alert.timestamp.isoformat(),
                "recommendations": alert.recommendations,
            }
            for alert in alerts
        ]

    async def reflect(
        self,
        original_prompt: str,
        output: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        反思评估便捷方法

        对AI输出进行质量评估，返回改进建议

        Args:
            original_prompt: 原始提示
            output: AI输出
            context: 上下文信息

        Returns:
            dict: 包含overall_score, feedback, suggestions的字典
        """
        import json
        import re

        # 构建反思提示
        reflection_prompt = f'''你是一个专业的AI输出质量评估专家。请对以下AI输出进行评估。

## 原始提示
{original_prompt}

## 输出结果
{output}

## 上下文信息
{json.dumps(context or {}, ensure_ascii=False, indent=2)}

## 评估标准 (0-1分)
- accuracy: 准确性
- completeness: 完整性
- clarity: 清晰度
- relevance: 相关性
- usefulness: 有用性
- consistency: 一致性

请严格按以下JSON格式返回:
{{
    "overall_score": 0.85,
    "metric_scores": {{
        "accuracy": 0.9,
        "completeness": 0.8,
        "clarity": 0.88,
        "relevance": 0.92,
        "usefulness": 0.85,
        "consistency": 0.9
    }},
    "feedback": "评估反馈",
    "suggestions": ["建议1", "建议2"],
    "should_refine": true
}}'''

        try:
            # 调用LLM进行反思
            response = await self.generate(
                message=reflection_prompt,
                task_type="reflection",
                temperature=0.1,
                max_tokens=2000,
            )

            # 提取JSON
            content = response.content
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', content)
            if json_match:
                json_str = json_match.group(1).strip()
            else:
                json_match = re.search(r'\{[\s\S]*\}', content)
                json_str = json_match.group(0) if json_match else content

            result = json.loads(json_str)
            result["model_used"] = response.model_used
            result["processing_time"] = response.processing_time

            return result

        except Exception as e:
            logger.error(f"反思评估失败: {e}")
            return {
                "overall_score": 0.5,
                "feedback": f"反思评估出现错误: {str(e)}",
                "suggestions": ["请重新生成输出"],
                "should_refine": False,
                "error": str(e),
            }

    async def shutdown(self):
        """关闭管理器,清理资源"""
        logger.info("🔄 关闭统一LLM管理器...")
        # 这里可以添加适配器的清理逻辑
        self.adapters.clear()
        logger.info("✅ 统一LLM管理器已关闭")


# 单例
_unified_llm_manager: UnifiedLLMManager | None = None
_unified_llm_manager_lock = asyncio.Lock()


async def get_unified_llm_manager() -> UnifiedLLMManager:
    """
    获取统一LLM管理器单例(异步线程安全)

    Returns:
        UnifiedLLMManager: 管理器实例
    """
    global _unified_llm_manager
    if _unified_llm_manager is None:
        async with _unified_llm_manager_lock:
            # 双重检查锁定
            if _unified_llm_manager is None:
                _unified_llm_manager = UnifiedLLMManager()
                await _unified_llm_manager.initialize()
    return _unified_llm_manager


def reset_unified_llm_manager():
    """重置单例(用于测试)"""
    global _unified_llm_manager
    _unified_llm_manager = None
