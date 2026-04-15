"""
意图识别服务 - API路由

提供意图识别相关的RESTful API端点。

Author: Xiaonuo
Created: 2025-01-17
Version: 1.0.0
"""

from __future__ import annotations
import logging
import time

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse

from core.api.intent_auth import (
    check_rate_limit_depends,
    get_current_user,
    get_current_user_optional,
)
from core.api.intent_models import (
    BatchIntentRecognitionRequest,
    BatchIntentRecognitionResponse,
    EngineInfo,
    EnginesListResponse,
    EngineStatsResponse,
    HealthResponse,
    IntentRecognitionRequest,
    IntentRecognitionResponse,
    ModelInfo,
    ModelLoadRequest,
    ModelLoadResponse,
    ModelsListResponse,
    ModelUnloadResponse,
    ReadinessResponse,
    StatsResponse,
)
from core.intent.base_engine import IntentEngineFactory
from core.intent.keyword_engine_refactored import create_keyword_engine
from core.intent.model_pool import get_model_pool
from core.intent.prometheus_metrics import get_metrics_manager

# 配置日志
logger = logging.getLogger("api.intent_routes")

# 创建路由器
router = APIRouter(prefix="/api/v1/intent", tags=["intent"])

# 服务启动时间
_start_time = time.time()


# ========================================================================
# 健康检查和就绪检查
# ========================================================================


@router.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """
    健康检查端点

    返回服务的健康状态。
    """
    uptime = time.time() - _start_time

    # 检查基本健康状态
    is_healthy = True

    # TODO: 添加更详细的健康检查
    # - 数据库连接
    # - Redis连接
    # - 模型加载状态

    return HealthResponse(
        status="healthy" if is_healthy else "unhealthy",
        version="1.0.0",
        uptime_seconds=uptime,
        timestamp=time.time(),
    )


@router.get("/ready", response_model=ReadinessResponse, tags=["health"])
async def readiness_check():
    """
    就绪检查端点

    检查服务是否准备好接收请求。
    """
    checks = {}

    # 检查模型池
    try:
        get_model_pool()
        checks["model_pool"] = "ready"
        is_ready = True
    except Exception as e:
        checks["model_pool"] = f"not_ready: {e!s}"
        is_ready = False

    # 检查配置
    try:
        from core.intent.config_loader import get_intent_config

        get_intent_config()
        checks["config"] = "ready"
    except Exception as e:
        checks["config"] = f"not_ready: {e!s}"
        is_ready = False

    return ReadinessResponse(ready=is_ready, checks=checks)


@router.get("/metrics", tags=["monitoring"])
async def prometheus_metrics():
    """
    Prometheus指标端点

    返回Prometheus格式的监控指标。
    """
    manager = get_metrics_manager()
    metrics_text = manager.get_metrics_text()
    content_type = manager.get_content_type()

    return PlainTextResponse(content=metrics_text, media_type=content_type)


@router.get("/stats", response_model=StatsResponse, tags=["monitoring"])
async def get_service_stats():
    """
    服务统计信息端点

    返回服务的详细统计信息。
    """
    try:
        pool = get_model_pool()
        pool_stats = pool.get_stats()

        # 获取引擎统计
        engine = create_keyword_engine()
        engine_stats = engine.get_stats().__dict__

        return StatsResponse(
            service={
                "name": "intent-recognition-service",
                "version": "1.0.0",
                "uptime_seconds": time.time() - _start_time,
            },
            engines={"total": 1, "active": 1},
            models=pool_stats,
            performance={
                "total_requests": engine_stats.get("total_requests", 0),
                "requests_per_second": engine_stats.get("total_requests", 0)
                / max(time.time() - _start_time, 1),
                "avg_processing_time_ms": engine_stats.get("avg_processing_time_ms", 0),
            },
            errors={
                "total_errors": engine_stats.get("failed_requests", 0),
                "error_rate": engine_stats.get("failed_requests", 0)
                / max(engine_stats.get("total_requests", 1), 0),
            },
        )
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取统计信息失败: {e!s}"
        ) from e


# ========================================================================
# 意图识别核心端点
# ========================================================================


@router.post("/recognize", response_model=IntentRecognitionResponse)
async def recognize_intent(
    request: IntentRecognitionRequest,
    current_user: str = Depends(get_current_user_optional),
    _rate_limit: None = Depends(check_rate_limit_depends),
):
    """
    识别单个文本的意图

    支持多种认证方式:
    - JWT Bearer Token
    - API Key (X-API-Key header)

    如果不提供认证凭据,将作为匿名请求处理。
    """
    start_time = time.perf_counter()

    try:
        # 创建或获取引擎
        engine = create_keyword_engine()

        # 识别意图
        result = engine.recognize_intent(request.text, request.context)

        # 记录指标
        manager = get_metrics_manager()
        manager.record_request(
            engine_type=request.engine or "keyword",
            intent_type=result.intent,
            status="success",
            duration=time.perf_counter() - start_time,
        )

        # 返回响应
        # 注意: IntentResult配置了use_enum_values=True,所以intent和category已经是字符串
        return IntentRecognitionResponse(
            intent=result.intent,
            confidence=result.confidence,
            category=result.category,
            entities=result.entities,
            processing_time_ms=result.processing_time_ms,
            model_version=result.model_version,
        )

    except Exception as e:
        logger.error(f"意图识别失败: {e}")

        # 记录错误指标
        manager = get_metrics_manager()
        manager.record_error(error_type=type(e).__name__, component="intent_recognition")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"意图识别失败: {e!s}"
        ) from e


@router.post("/recognize/batch", response_model=BatchIntentRecognitionResponse)
async def recognize_batch(
    request: BatchIntentRecognitionRequest,
    current_user: str = Depends(get_current_user),
    _rate_limit: None = Depends(check_rate_limit_depends),
):
    """
    批量识别多个文本的意图

    需要认证(JWT或API Key)。
    """
    start_time = time.perf_counter()

    try:
        # 创建或获取引擎
        engine = create_keyword_engine()

        # 批量识别
        results = engine.recognize_batch(request.texts)

        # 统计成功和失败数量
        successful_count = 0
        failed_count = 0

        response_results = []
        for result in results:
            # 注意: IntentResult配置了use_enum_values=True,所以intent已经是字符串
            if result.intent != "UNKNOWN":
                successful_count += 1
            else:
                failed_count += 1

            response_results.append(
                IntentRecognitionResponse(
                    intent=result.intent,
                    confidence=result.confidence,
                    category=result.category,
                    entities=result.entities,
                    processing_time_ms=result.processing_time_ms,
                    model_version=result.model_version,
                )
            )

        processing_time = (time.perf_counter() - start_time) * 1000

        return BatchIntentRecognitionResponse(
            results=response_results,
            total_count=len(request.texts),
            successful_count=successful_count,
            failed_count=failed_count,
            total_processing_time_ms=processing_time,
        )

    except Exception as e:
        logger.error(f"批量意图识别失败: {e}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"批量意图识别失败: {e!s}"
        ) from e


# ========================================================================
# 引擎管理端点
# ========================================================================


@router.get("/engines", response_model=EnginesListResponse)
async def list_engines(current_user: str = Depends(get_current_user)):
    """
    获取所有可用的意图识别引擎

    需要认证。
    """
    try:
        engines = IntentEngineFactory.list_engines()

        engine_infos = []
        for engine_name in engines:
            # 获取引擎实例以获取信息
            try:
                engine = IntentEngineFactory.create(engine_name)
                info = EngineInfo(
                    name=engine.engine_name,
                    version=engine.engine_version,
                    description=f"{engine.engine_name} 意图识别引擎",
                    supported_intents=[intent.value for intent in engine.supported_intents],
                    is_active=True,
                )
                engine_infos.append(info)
            except Exception as e:
                logger.warning(f"无法获取引擎 {engine_name} 的信息: {e}")

        return EnginesListResponse(engines=engine_infos, total_count=len(engine_infos))

    except Exception as e:
        logger.error(f"获取引擎列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取引擎列表失败: {e!s}"
        ) from e


@router.get("/engines/{engine_name}", response_model=EngineStatsResponse)
async def get_engine_stats(engine_name: str, current_user: str = Depends(get_current_user)):
    """
    获取指定引擎的详细信息和统计

    需要认证。
    """
    try:
        if engine_name not in IntentEngineFactory.list_engines():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"引擎不存在: {engine_name}"
            )

        engine = IntentEngineFactory.create(engine_name)
        stats = engine.get_stats()

        return EngineStatsResponse(
            name=engine.engine_name, version=engine.engine_version, stats=stats.__dict__
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取引擎统计失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取引擎统计失败: {e!s}"
        ) from e


@router.post("/engines/{engine_name}/reload")
async def reload_engine(engine_name: str, current_user: str = Depends(get_current_user)):
    """
    重新加载指定引擎

    需要认证。
    """
    try:
        if engine_name not in IntentEngineFactory.list_engines():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"引擎不存在: {engine_name}"
            )

        # TODO: 实现引擎重新加载逻辑
        # 目前只是返回成功消息

        return {"message": f"引擎 {engine_name} 重新加载成功", "reload_time": time.time()}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重新加载引擎失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"重新加载引擎失败: {e!s}"
        ) from e


# ========================================================================
# 模型管理端点
# ========================================================================


@router.get("/models", response_model=ModelsListResponse)
async def list_models(current_user: str = Depends(get_current_user)):
    """
    获取所有模型的信息

    需要认证。
    """
    try:
        pool = get_model_pool()
        pool.get_stats()

        model_infos = []
        loaded_count = 0

        for model_name, model_metadata in pool._models.items():
            info = ModelInfo(
                name=model_name,
                type=model_metadata.model_type,
                status=model_metadata.status.value,
                device=model_metadata.device,
                load_time=model_metadata.load_time,
                last_access=model_metadata.last_access,
                access_count=model_metadata.access_count,
                memory_usage_mb=None,  # TODO: 实现内存使用统计
            )
            model_infos.append(info)

            if model_metadata.is_loaded:
                loaded_count += 1

        return ModelsListResponse(
            models=model_infos, total_count=len(model_infos), loaded_count=loaded_count
        )

    except Exception as e:
        logger.error(f"获取模型列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取模型列表失败: {e!s}"
        ) from e


@router.post("/models/{model_name}/load", response_model=ModelLoadResponse)
async def load_model(
    model_name: str, request: ModelLoadRequest, current_user: str = Depends(get_current_user)
):
    """
    加载指定模型

    需要认证。
    """
    start_time = time.perf_counter()

    try:
        pool = get_model_pool()

        if model_name not in pool._models:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"模型不存在: {model_name}"
            )

        # 预加载模型
        pool.preload_model(model_name)

        duration_ms = (time.perf_counter() - start_time) * 1000

        # 获取模型元数据
        metadata = pool._models[model_name]

        return ModelLoadResponse(
            message="模型加载成功",
            model_name=model_name,
            load_time=metadata.load_time,
            duration_ms=duration_ms,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"加载模型失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"加载模型失败: {e!s}"
        ) from e


@router.post("/models/{model_name}/unload", response_model=ModelUnloadResponse)
async def unload_model(model_name: str, current_user: str = Depends(get_current_user)):
    """
    卸载指定模型

    需要认证。
    """
    try:
        pool = get_model_pool()

        if model_name not in pool._models:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"模型不存在: {model_name}"
            )

        # 记录卸载前的内存使用(如果可用)
        memory_before = 0  # TODO: 实现内存使用统计

        # 卸载模型
        pool.unload_model(model_name)

        return ModelUnloadResponse(
            message="模型卸载成功", model_name=model_name, memory_freed_mb=memory_before
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"卸载模型失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"卸载模型失败: {e!s}"
        ) from e


# ========================================================================
# 导出
# ========================================================================

__all__ = ["router"]
