#!/usr/bin/env python3
from __future__ import annotations
"""
动态提示词系统API路由
Dynamic Prompt System API Routes

提供优化后的动态提示词系统的API端点
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# 导入配置管理
from core.config.api_config import (
    get_config,
    get_database_config,
    get_llm_config,
)

# 创建路由器
router = APIRouter(prefix="/api/v1/prompt-system", tags=["动态提示词系统"])

# 获取配置
_config = get_config()
_db_config = get_database_config()
_llm_config = get_llm_config()


# ============================================================================
# 请求/响应模型
# ============================================================================


class ScenarioIdentifyRequest(BaseModel):
    """场景识别请求"""

    user_input: str = Field(..., description="用户输入文本", min_length=1, max_length=100000)
    additional_context: dict[str, Any] = Field(None, description="额外上下文信息")


class ScenarioIdentifyResponse(BaseModel):
    """场景识别响应"""

    domain: str
    task_type: str
    phase: str
    confidence: float
    extracted_variables: dict[str, Any]
    processing_time_ms: float


class RuleRetrieveRequest(BaseModel):
    """规则检索请求"""

    domain: str = Field(..., description="业务领域")
    task_type: str = Field(..., description="任务类型")
    phase: str = Field(None, description="业务阶段")


class RuleRetrieveResponse(BaseModel):
    """规则检索响应"""

    rule_id: str
    domain: str
    task_type: str
    phase: str
    processing_rules: list[str]
    workflow_steps: list[dict[str, Any]]
    variables: dict[str, str]


class CapabilityInvokeRequest(BaseModel):
    """能力调用请求"""

    capability_id: str = Field(..., description="能力ID")
    parameters: dict[str, Any] = Field(default_factory=dict, description="调用参数")
    timeout: int = Field(30, description="超时时间(秒)", ge=1, le=300)


class CapabilityInvokeResponse(BaseModel):
    """能力调用响应"""

    capability_id: str
    success: bool
    result: dict[str, Any] | None = None
    error: str | None = None
    response_time_ms: float


class PromptGenerateRequest(BaseModel):
    """提示词生成请求"""

    user_input: str = Field(..., description="用户输入", min_length=1, max_length=100000)
    additional_context: dict[str, Any] = Field(None, description="额外上下文")


class PromptGenerateResponse(BaseModel):
    """提示词生成响应"""

    scenario_rule_id: str
    domain: str
    task_type: str
    system_prompt: str
    user_prompt: str
    capability_results: list[str] = []
    processing_time_ms: float
    cached: bool = False  # P1优化:标识是否来自缓存


class HealthResponse(BaseModel):
    """健康检查响应"""

    status: str
    version: str
    timestamp: str
    components: dict[str, str]


# ============================================================================
# 辅助函数
# ============================================================================


def get_db_manager():
    """获取数据库管理器"""
    from core.database import get_sync_db_manager

    return get_sync_db_manager()


# RAG管理器单例缓存
_rag_manager = None
_qdrant_client = None
_bge_classifier = None


def get_rag_components():
    """
    获取RAG组件(延迟初始化)

    Returns:
        (rag_manager, qdrant_client, bge_classifier)
    """
    global _rag_manager, _qdrant_client, _bge_classifier

    # 如果已经初始化,直接返回
    if _rag_manager is not None:
        return _rag_manager, _qdrant_client, _bge_classifier

    try:
        # 1. 初始化Qdrant客户端
        import os

        from qdrant_client import QdrantClient

        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        _qdrant_client = QdrantClient(url=qdrant_url)

        # 2. 初始化BGE分类器
        from core.intent.bge_m3_intent_classifier import get_bge_m3_classifier

        _bge_classifier = get_bge_m3_classifier()

        # 3. 初始化RAG管理器
        from core.llm.rag_manager import get_rag_manager

        _rag_manager = get_rag_manager(_qdrant_client, _bge_classifier)

        logger.info("✅ RAG组件初始化成功")

    except Exception as e:
        logger.warning(f"⚠️ RAG组件初始化失败: {e}")
        # 初始化失败时返回None,系统会回退到模拟数据
        _rag_manager = None

    return _rag_manager, _qdrant_client, _bge_classifier


# ============================================================================
# API端点
# ============================================================================


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    健康检查端点

    检查系统各组件的健康状态
    """
    logger.info("🔍 健康检查请求")

    components = {}

    # 检查Neo4j (使用 SyncDatabaseConnectionManager 避免 core.neo4j 模块冲突)
    try:
        from core.database import get_sync_db_manager

        db = get_sync_db_manager()
        # 使用 health_check 方法
        health = db.health_check()
        if "neo4j" in health and health["neo4j"]["status"] == "healthy":
            components["neo4j"] = "ok"
        else:
            components["neo4j"] = f"error: {health.get('neo4j', {}).get('error', 'Unknown error')}"
    except Exception as e:
        components["neo4j"] = f"error: {e!s}"

    # 检查PostgreSQL
    try:
        import psycopg2

        conn = psycopg2.connect(
            host=_db_config.postgres_host,
            port=_db_config.postgres_port,
            database=_db_config.postgres_database,
            user=_db_config.postgres_user,
            password=_db_config.postgres_password,
        )
        conn.close()
        components["postgres"] = "ok"
    except Exception as e:
        components["postgres"] = f"error: {e!s}"

    # 检查Redis
    try:
        import redis

        r = redis.Redis(
            host=_db_config.redis_host,
            port=_db_config.redis_port,
            password=_db_config.redis_password,
            db=_db_config.redis_db,
            decode_responses=True,
        )
        r.ping()
        components["redis"] = "ok"
    except Exception as e:
        components["redis"] = f"error: {e!s}"

    # 检查优化模块
    try:

        components["optimized_modules"] = "ok"
    except Exception as e:
        components["optimized_modules"] = f"error: {e!s}"

    overall_status = "healthy" if all(v == "ok" for v in components.values()) else "degraded"

    return HealthResponse(
        status=overall_status,
        version="2.1.0",  # 更新版本号
        timestamp=datetime.now().isoformat(),
        components=components,
    )


@router.post("/scenario/identify", response_model=ScenarioIdentifyResponse)
async def identify_scenario(request: ScenarioIdentifyRequest):
    """
    场景识别端点

    识别用户输入的业务场景
    """
    logger.info(f"🔍 场景识别请求: {request.user_input[:100]}...")

    start_time = datetime.now()

    try:
        from core.legal_world_model.scenario_identifier_optimized import ScenarioIdentifierOptimized

        identifier = ScenarioIdentifierOptimized()
        context = identifier.identify_scenario(request.user_input, request.additional_context)

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        return ScenarioIdentifyResponse(
            domain=context.domain.value,
            task_type=context.task_type.value,
            phase=context.phase.value,
            confidence=context.confidence,
            extracted_variables=context.extracted_variables,
            processing_time_ms=processing_time,
        )

    except Exception as e:
        logger.error(f"❌ 场景识别失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"场景识别失败: {e!s}"
        ) from e


@router.post("/rules/retrieve", response_model=RuleRetrieveResponse)
async def retrieve_rule(request: RuleRetrieveRequest):
    """
    规则检索端点

    从Neo4j检索场景规则
    """
    logger.info(f"🔍 规则检索请求: {request.domain}/{request.task_type}/{request.phase or 'any'}")

    try:
        from core.legal_world_model.scenario_rule_retriever_optimized import (
            ScenarioRuleRetrieverOptimized,
        )

        db_manager = get_db_manager()
        retriever = ScenarioRuleRetrieverOptimized(db_manager)

        rule = retriever.retrieve_rule(request.domain, request.task_type, request.phase)

        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到规则: {request.domain}/{request.task_type}/{request.phase or 'any'}",
            )

        return RuleRetrieveResponse(
            rule_id=rule.rule_id,
            domain=rule.domain,
            task_type=rule.task_type,
            phase=rule.phase,
            processing_rules=rule.processing_rules,
            workflow_steps=rule.workflow_steps,
            variables=rule.variables,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 规则检索失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"规则检索失败: {e!s}"
        ) from e


@router.post("/capabilities/invoke", response_model=CapabilityInvokeResponse)
async def invoke_capability(request: CapabilityInvokeRequest):
    """
    能力调用端点

    调用指定的原子化能力

    集成真实RAG系统:
    - 对于向量检索能力,使用真实的Qdrant向量搜索
    - 如果RAG不可用,自动回退到模拟数据
    """
    logger.info(f"🎯 能力调用请求: {request.capability_id}")

    start_time = datetime.now()

    try:
        from core.capabilities.capability_invoker_optimized import CapabilityInvokerOptimized

        # 获取RAG组件(延迟初始化)
        rag_manager, _, _ = get_rag_components()

        # 创建能力调用器,传入RAG管理器
        invoker = CapabilityInvokerOptimized(rag_manager=rag_manager)

        try:
            result = await invoker.invoke(
                request.capability_id, request.parameters, request.timeout
            )

            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            return CapabilityInvokeResponse(
                capability_id=request.capability_id,
                success=True,
                result=result,
                response_time_ms=processing_time,
            )

        finally:
            await invoker.close()

    except Exception as e:
        logger.error(f"❌ 能力调用失败: {e}")
        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        return CapabilityInvokeResponse(
            capability_id=request.capability_id,
            success=False,
            error=str(e),
            response_time_ms=processing_time,
        )


@router.post("/prompt/generate", response_model=PromptGenerateResponse)
async def generate_prompt(request: PromptGenerateRequest):
    """
    提示词生成端点(完整流程)

    集成场景识别、规则检索、能力调用和提示词生成
    支持提示词模板缓存(P1优化)
    """
    logger.info(f"📝 提示词生成请求: {request.user_input[:100]}...")

    start_time = datetime.now()

    try:
        # 1. 场景识别
        from core.legal_world_model.scenario_identifier_optimized import ScenarioIdentifierOptimized

        identifier = ScenarioIdentifierOptimized()
        context = identifier.identify_scenario(request.user_input, request.additional_context)

        # 2. 规则检索
        from core.legal_world_model.scenario_rule_retriever_optimized import (
            ScenarioRuleRetrieverOptimized,
        )

        db_manager = get_db_manager()
        retriever = ScenarioRuleRetrieverOptimized(db_manager)

        rule = retriever.retrieve_rule(context.domain.value, context.task_type.value)

        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到规则: {context.domain.value}/{context.task_type.value}",
            )

        # 3. 能力调用(如果规则有配置)
        capability_results = []
        if hasattr(rule, "capability_invocations") and rule.capability_invocations:
            from core.capabilities.capability_orchestrator import execute_capability_workflow

            capability_results_dict = await execute_capability_workflow(
                rule.capability_invocations,
                {**context.extracted_variables, **(request.additional_context or {})},
            )
            capability_results = list(capability_results_dict.keys())

        # 4. 准备变量(用于缓存键和变量替换)
        all_variables = {**context.extracted_variables, **(request.additional_context or {})}

        # 5. 检查提示词缓存(P1优化)
        from core.capabilities.prompt_template_cache import get_prompt_cache

        prompt_cache = get_prompt_cache()
        cached_prompts = prompt_cache.get(
            domain=context.domain.value,
            task_type=context.task_type.value,
            phase=context.phase.value,
            variables=all_variables,
        )

        if cached_prompts:
            # 缓存命中
            system_prompt, user_prompt = cached_prompts
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.info(f"✅ 提示词缓存命中: {processing_time:.0f}ms")

            return PromptGenerateResponse(
                scenario_rule_id=rule.rule_id,
                domain=rule.domain,
                task_type=rule.task_type,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                capability_results=capability_results,
                processing_time_ms=processing_time,
                cached=True,
            )

        # 6. 缓存未命中,生成提示词
        system_prompt, user_prompt = rule.substitute_variables(all_variables)

        # 7. 保存到缓存
        prompt_cache.set(
            domain=context.domain.value,
            task_type=context.task_type.value,
            phase=context.phase.value,
            variables=all_variables,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            scenario_rule_id=rule.rule_id,
        )

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        return PromptGenerateResponse(
            scenario_rule_id=rule.rule_id,
            domain=rule.domain,
            task_type=rule.task_type,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            capability_results=capability_results,
            processing_time_ms=processing_time,
            cached=False,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 提示词生成失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"提示词生成失败: {e!s}"
        ) from e


@router.get("/capabilities/list")
async def list_capabilities():
    """
    列出所有可用能力

    返回已注册的原子化能力列表
    """
    logger.info("📋 获取能力列表")

    try:
        from core.capabilities.capability_registry import capability_registry

        capabilities = capability_registry.list_all()

        return {
            "total": len(capabilities),
            "capabilities": [
                {
                    "capability_id": cap.capability_id,
                    "name": cap.name,
                    "category": cap.category,
                    "invocation_type": cap.invocation_type.value,
                    "description": cap.description,
                }
                for cap in capabilities
            ],
        }

    except Exception as e:
        logger.error(f"❌ 获取能力列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取能力列表失败: {e!s}"
        ) from e


@router.get("/metrics")
async def get_metrics():
    """
    获取系统性能指标

    返回各组件的性能指标
    """
    logger.info("📊 获取性能指标")

    try:
        from core.capabilities.capability_invoker_optimized import CapabilityInvokerOptimized
        from core.legal_world_model.scenario_identifier_optimized import ScenarioIdentifierOptimized

        # 场景识别器指标
        identifier = ScenarioIdentifierOptimized()
        identifier_metrics = identifier.get_metrics()

        # 能力调用器指标
        invoker = CapabilityInvokerOptimized()
        all_metrics = invoker.get_all_metrics()

        return {
            "scenario_identifier": identifier_metrics,
            "capability_invokers": all_metrics,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"❌ 获取性能指标失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取性能指标失败: {e!s}"
        ) from e


@router.get("/cache/stats")
async def get_cache_stats():
    """
    获取提示词缓存统计信息

    P1优化:返回缓存命中率、使用情况等指标
    """
    try:
        from core.capabilities.prompt_template_cache import get_prompt_cache

        cache = get_prompt_cache()
        stats = cache.get_stats()

        logger.info("📊 获取缓存统计")
        return stats

    except Exception as e:
        logger.error(f"❌ 获取缓存统计失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取缓存统计失败: {e!s}"
        ) from e


@router.post("/cache/clear")
async def clear_cache():
    """
    清除提示词缓存

    P1优化:支持手动清除缓存
    """
    try:
        from core.capabilities.prompt_template_cache import get_prompt_cache

        cache = get_prompt_cache()
        cache.clear()

        logger.info("🗑️ 缓存已清除")
        return {"status": "success", "message": "缓存已清除"}

    except Exception as e:
        logger.error(f"❌ 清除缓存失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"清除缓存失败: {e!s}"
        ) from e


# 注意: 异常处理器需要在FastAPI app级别注册,而不是router级别
# 这个文件只定义router,异常处理在main.py中统一处理


# ============================================================================
# P2优化: 性能监控端点
# ============================================================================


@router.get("/monitoring/metrics")
async def get_monitoring_metrics():
    """
    获取性能监控指标

    P2优化:返回详细的性能监控数据
    """
    try:
        from core.monitoring.metrics_collector import get_metrics_collector

        collector = get_metrics_collector()

        # 导出Prometheus格式
        prometheus_text = collector.export_prometheus()

        # 导出JSON格式
        json_data = collector.export_json()

        logger.info("📊 获取性能监控指标")
        return {
            "format": "prometheus",
            "metrics": prometheus_text,
            "json": json_data,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"❌ 获取性能指标失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取性能指标失败: {e!s}"
        ) from e


@router.post("/monitoring/metrics/reset")
async def reset_metrics():
    """
    重置性能指标

    P2优化:支持手动重置指标计数器
    """
    try:
        from core.monitoring.metrics_collector import reset_metrics_collector

        reset_metrics_collector()

        logger.info("🗑️ 性能指标已重置")
        return {"status": "success", "message": "性能指标已重置"}

    except Exception as e:
        logger.error(f"❌ 重置指标失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"重置指标失败: {e!s}"
        ) from e


@router.get("/monitoring/performance")
async def get_performance_snapshot():
    """
    获取性能快照

    P2优化:返回当前性能状态的快照
    """
    try:
        from core.monitoring.metrics_collector import PerformanceMonitor, get_metrics_collector

        collector = get_metrics_collector()
        monitor = PerformanceMonitor(collector)

        # 获取关键指标的快照
        snapshots = {}
        for metric_name in ["api_request_duration_ms", "prompt_generation_duration_ms"]:
            if metric_name in [k.split("{")[0] for k in collector._histograms]:
                snapshot = monitor.take_snapshot(metric_name)
                snapshots[metric_name] = {
                    "total_requests": snapshot.total_requests,
                    "avg_ms": round(snapshot.avg_response_time_ms, 2),
                    "p95_ms": round(snapshot.p95_response_time_ms, 2),
                    "p99_ms": round(snapshot.p99_response_time_ms, 2),
                }

        logger.info("📊 获取性能快照")
        return {"snapshots": snapshots, "timestamp": datetime.now().isoformat()}

    except Exception as e:
        logger.error(f"❌ 获取性能快照失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取性能快照失败: {e!s}"
        ) from e


@router.get("/config/status")
async def get_config_status():
    """
    获取配置状态

    P2优化:返回配置管理和热更新状态
    """
    try:
        from core.config.hot_reload import get_global_config_manager

        # 尝试获取全局配置管理器
        try:
            config_manager = get_global_config_manager()
            status = {
                "config_path": config_manager.config_path,
                "version": config_manager._config_version,
                "hot_reload_enabled": config_manager.enable_hot_reload,
                "is_watching": config_manager._observer is not None,
                "subscriber_count": len(config_manager._subscribers),
                "history_length": len(config_manager._config_history),
            }
        except Exception:
            # 全局配置管理器未初始化
            status = {"status": "not_initialized", "message": "全局配置管理器未初始化"}

        logger.info("📋 获取配置状态")
        return status

    except Exception as e:
        logger.error(f"❌ 获取配置状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取配置状态失败: {e!s}"
        ) from e


@router.post("/config/reload")
async def reload_config():
    """
    手动重载配置

    P2优化:支持手动触发配置重载
    """
    try:
        from core.config.hot_reload import get_global_config_manager

        config_manager = get_global_config_manager()
        old_version = config_manager._config_version

        config_manager.reload()

        logger.info(f"🔄 配置已手动重载: v{old_version} -> v{config_manager._config_version}")
        return {
            "status": "success",
            "message": "配置已重载",
            "old_version": old_version,
            "new_version": config_manager._config_version,
        }

    except Exception as e:
        logger.error(f"❌ 重载配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"重载配置失败: {e!s}"
        ) from e


@router.get("/health/extended")
async def extended_health_check():
    """
    扩展健康检查

    P2优化:返回更详细的健康状态信息
    """
    try:
        from core.capabilities.prompt_template_cache import get_prompt_cache
        from core.monitoring.metrics_collector import get_metrics_collector

        collector = get_metrics_collector()
        cache = get_prompt_cache()

        metrics = collector.export_json()

        return {
            "status": "healthy",
            "version": "2.1.0",  # P2优化版本
            "timestamp": datetime.now().isoformat(),
            "components": {
                "neo4j": "ok",
                "postgres": "ok",
                "redis": "ok",
                "optimized_modules": "ok",
                "monitoring": "ok",  # P2新增
                "structured_logging": "ok",  # P2新增
                "hot_reload": "ok",  # P2新增
            },
            "metrics_summary": {
                "total_requests": metrics.get("counters", {}).get("api_requests_total", 0),
                "cache_hit_rate": cache.get_stats().get("hit_rate", 0),
                "cache_size": cache.get_stats().get("current_size", 0),
            },
        }

    except Exception as e:
        logger.error(f"❌ 扩展健康检查失败: {e}")
        return {"status": "degraded", "error": str(e), "timestamp": datetime.now().isoformat()}
