#!/usr/bin/env python3

"""
动态提示词系统API路由
Dynamic Prompt System API Routes

提供优化后的动态提示词系统的API端点
"""

import asyncio
import logging
import os
import time
import uuid
from dataclasses import asdict
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# 导入配置管理
from core.config.api_config import (
    get_config,
    get_database_config,
    get_llm_config,
)

# B5-PerfObs: Token 估算器（用于指标维度）
from core.prompt_engine.budget.utils import TokenEstimator

_token_estimator = TokenEstimator()

# C1-Budget: Context Budget Manager（环境变量控制，默认 8K）
from core.prompt_engine.budget.manager import ContextBudgetManager
from core.prompt_engine.budget.truncation import EvidenceItem

_budget_manager: ContextBudgetManager | None = None


def _get_budget_manager() -> ContextBudgetManager:
    """获取 Budget Manager 单例（延迟初始化）。"""
    global _budget_manager
    if _budget_manager is None:
        total_budget = int(os.getenv("LEGAL_FUSION_BUDGET_TOKENS", "8192"))
        _budget_manager = ContextBudgetManager(total_budget=total_budget)
    return _budget_manager

# 创建路由器
router = APIRouter(prefix="/api/v1/prompt-system", tags=["动态提示词系统"])

# 获取配置
_config = get_config()
_db_config = get_database_config()
_llm_config = get_llm_config()

# 灰度配置（延迟初始化，支持热重载）
_rollout_config = None


def _get_rollout_config():
    """获取灰度配置单例，支持热重载。"""
    global _rollout_config
    if _rollout_config is None:
        from core.legal_prompt_fusion.rollout_config import FusionRolloutConfig

        _rollout_config = FusionRolloutConfig.from_file("config/prompt_fusion_rollout.yaml")
    else:
        _rollout_config.maybe_reload()
    return _rollout_config


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

        # 4.5 变量治理（校验 + 清洗 + Schema Registry 集成）
        try:
            from core.prompt_engine.sanitizer import PromptSanitizer
            from core.prompt_engine.schema import PromptSchema, VariableSpec, VariableType
            from core.prompt_engine.validators import VariableValidator
            from core.prompt_engine.registry import PromptSchemaRegistry

            sanitizer = PromptSanitizer()
            validator = VariableValidator()
            registry = PromptSchemaRegistry()

            # C2-SchemaIntegration: 优先从 PromptSchemaRegistry 获取 Schema
            schema = registry.get(rule.rule_id)
            if schema is None:
                # 回退：从规则的 variables 字段或模板推断 schema（存量模板兼容）
                schema_vars = []
                if hasattr(rule, "variables") and rule.variables:
                    for var_name, var_info in rule.variables.items():
                        if isinstance(var_info, dict):
                            schema_vars.append(VariableSpec(
                                name=var_name,
                                type=VariableType(var_info.get("type", "string")),
                                required=var_info.get("required", True),
                                source=var_info.get("source", ""),
                                default=var_info.get("default"),
                                max_length=var_info.get("max_length"),
                            ))
                        else:
                            # 简单字符串标记，默认 required=True
                            schema_vars.append(VariableSpec(name=var_name, required=True))
                else:
                    # 无 schema 时，从模板中提取占位符作为 required 变量
                    import re
                    placeholders = set(
                        re.findall(r"\{\{?\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}?\}", rule.system_prompt_template)
                    ) | set(
                        re.findall(r"\{\{?\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}?\}", rule.user_prompt_template)
                    )
                    for ph in placeholders:
                        if ph not in ("__wiki_revision", "__fusion_template_version"):
                            schema_vars.append(VariableSpec(name=ph, required=True))

                schema = PromptSchema(
                    rule_id=rule.rule_id,
                    template_version=getattr(rule, "template_version", "1.0.0"),
                    variables=schema_vars,
                )

            # 校验
            validation = validator.validate(schema, all_variables)
            if not validation.valid:
                logger.warning(f"变量校验失败: {validation.errors}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "MISSING_VARIABLES",
                        "missing": validation.errors,
                        "message": f"Required variables missing: {', '.join(validation.errors)}",
                    },
                )

            # C2-SchemaIntegration: 填充默认值（对 registry 和 fallback schema 均生效）
            all_variables = registry.upgrade_variables(rule.rule_id, all_variables)

            # 清洗
            sanitized_vars, risks = sanitizer.sanitize_variables(all_variables, schema=schema)
            high_risks = [r for r in risks if r.level in ("high", "critical")]
            if high_risks:
                logger.warning(f"检测到高风险注入: {[r.pattern_matched for r in high_risks]}")
            all_variables = sanitized_vars

            # C2-SchemaIntegration: 暴露 Schema 覆盖率指标到 Prometheus
            try:
                from core.monitoring.metrics_collector import get_metrics_collector

                collector = get_metrics_collector()
                coverage = registry.get_coverage_report()
                collector.set_gauge("prompt_schema_total", float(coverage["total_schemas"]))
                collector.set_gauge("prompt_schema_with_variables", float(coverage["schemas_with_variables"]))
                collector.set_gauge("prompt_schema_coverage_rate", coverage["coverage_rate"])
            except Exception:
                # 指标暴露失败不阻断主链路
                pass

        except HTTPException:
            raise
        except Exception as e:
            # 变量治理模块异常时不阻断主链路（避免影响已有功能）
            logger.warning(f"变量治理模块异常，跳过校验: {e}")

        # 5. 判断融合开关 + 初始化指标
        request_id = uuid.uuid4().hex
        rollout = _get_rollout_config()
        user_id = (request.additional_context or {}).get("user_id", "")
        fusion_enabled = rollout.should_enable(
            domain=context.domain.value,
            task_type=context.task_type.value,
            user_id=user_id,
        )

        from core.legal_prompt_fusion.metrics import FusionMetrics, _send_metrics_async

        fusion_metrics = FusionMetrics(
            request_id=request_id,
            domain=context.domain.value,
            task_type=context.task_type.value,
            fusion_enabled=fusion_enabled,
        )

        # 6. 检查提示词缓存(P1优化)
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
            fusion_metrics.cache_hit = True
            # 异步发送基线指标（不阻塞）
            asyncio.create_task(_send_metrics_async(fusion_metrics))
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

        # 缓存未命中
        fusion_metrics.cache_hit = False

        # 7. 生成提示词（融合注入点）
        budget_metrics = None  # C1-BudgetIntegration
        if fusion_enabled:
            from core.legal_prompt_fusion.models import PromptGenerationRequest
            from core.legal_prompt_fusion.prompt_context_builder import LegalPromptContextBuilder

            fusion_start = time.monotonic()
            try:
                builder = LegalPromptContextBuilder()
                fusion_request = PromptGenerationRequest(
                    user_query=request.user_input,
                    domain=context.domain.value,
                    scenario=context.task_type.value,
                    additional_context=request.additional_context or {},
                )
                # 融合 builder 是同步 IO 密集型操作，放入线程池避免阻塞事件循环
                fusion_result = await asyncio.to_thread(builder.build, fusion_request)
                fusion_metrics.latency_ms = round((time.monotonic() - fusion_start) * 1000, 3)
                fusion_metrics.evidence_count = len(fusion_result.context.evidence)
                fusion_metrics.evidence_by_source = {
                    "postgres": len(fusion_result.context.legal_articles),
                    "neo4j": len(fusion_result.context.graph_relations),
                    "wiki": len(fusion_result.context.wiki_background),
                }
                fusion_metrics.wiki_revision = fusion_result.context.freshness.get("wiki_revision", "unknown")
                fusion_metrics.template_version = fusion_result.template_version

                # C1-BudgetIntegration: 接入 Budget Manager
                system_prompt = fusion_result.system_prompt
                user_prompt = fusion_result.user_prompt
                if fusion_result.context.evidence:
                    try:
                        evidence_items = [
                            EvidenceItem(
                                content=ev.content,
                                relevance_score=ev.score,
                                source=ev.source_type.value,
                                metadata={"original": ev},
                            )
                            for ev in fusion_result.context.evidence
                        ]
                        budget_result = _get_budget_manager().build_context(
                            system_prompt=system_prompt,
                            user_query=user_prompt,
                            evidence_list=evidence_items,
                            elapsed_ms=fusion_metrics.latency_ms if fusion_metrics.latency_ms > 0 else None,
                        )
                        budget_metrics = budget_result["metrics"]
                        fusion_metrics.evidence_count = budget_metrics.evidence_count_after
                        fusion_metrics.budget_usage = budget_metrics.budget_usage_ratio
                        fusion_metrics.budget_usage_ratio = budget_metrics.budget_usage_ratio
                        fusion_metrics.budget_metrics = asdict(budget_metrics)

                        if budget_result["target_mode"] in ("single_source", "aborted"):
                            logger.warning(
                                f"⚠️ Budget rollback: {budget_result['rollback'].message}"
                            )
                            fusion_metrics.source_degradation.append("budget_rollback")
                            system_prompt, user_prompt = rule.substitute_variables(all_variables)
                        else:
                            kept_items = budget_result["evidence"]
                            if budget_metrics.evidence_count_after < budget_metrics.evidence_count_before:
                                kept_evidence = [
                                    item.metadata["original"] for item in kept_items
                                ]
                                fusion_result.context.evidence = kept_evidence
                                fusion_result.context.legal_articles = builder._convert_to_snippets(
                                    kept_evidence, SourceType.POSTGRES
                                )
                                fusion_result.context.graph_relations = builder._convert_to_snippets(
                                    kept_evidence, SourceType.NEO4J
                                )
                                fusion_result.context.wiki_background = builder._convert_to_snippets(
                                    kept_evidence, SourceType.WIKI
                                )
                                system_prompt = builder._render_system_prompt(fusion_result.context)
                                user_prompt = builder._render_user_prompt(
                                    fusion_result.context, request.additional_context or {}
                                )

                            fusion_metrics.evidence_by_source = {
                                "postgres": len(fusion_result.context.legal_articles),
                                "neo4j": len(fusion_result.context.graph_relations),
                                "wiki": len(fusion_result.context.wiki_background),
                            }
                    except Exception as budget_err:
                        logger.warning(f"⚠️ Budget manager 异常，跳过裁剪: {budget_err}")
                        # 保持原有的 system_prompt / user_prompt
            except Exception as e:
                fusion_metrics.latency_ms = round((time.monotonic() - fusion_start) * 1000, 3)
                fusion_metrics.error = str(e)
                logger.warning(f"⚠️ 法律提示词融合失败，回退到规则变量替换: {e}")
                # 融合失败时回退到原逻辑
                system_prompt, user_prompt = rule.substitute_variables(all_variables)
        else:
            # 融合关闭，使用原逻辑
            system_prompt, user_prompt = rule.substitute_variables(all_variables)

        # B5-PerfObs: 填充新增指标维度
        fusion_metrics.token_count_input = _token_estimator.estimate(request.user_input)
        fusion_metrics.token_count_output = (
            _token_estimator.estimate(system_prompt) + _token_estimator.estimate(user_prompt)
        )
        if fusion_enabled and "fusion_result" in locals() and fusion_result.context.evidence:
            scores = [ev.score for ev in fusion_result.context.evidence if hasattr(ev, "score")]
            fusion_metrics.evidence_relevance_score = round(sum(scores) / len(scores), 4) if scores else 0.0
        if budget_metrics is not None:
            fusion_metrics.budget_usage = budget_metrics.budget_usage_ratio
            fusion_metrics.budget_usage_ratio = budget_metrics.budget_usage_ratio
        else:
            ratio = round(fusion_metrics.token_count_output / 8192, 4)
            fusion_metrics.budget_usage = ratio
            fusion_metrics.budget_usage_ratio = ratio

        # 异步发送指标（不阻塞主链路）
        asyncio.create_task(_send_metrics_async(fusion_metrics))

        # 8. 保存到缓存
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
async def get_metrics(format: str = "json"):
    """
    获取系统性能指标

    支持两种格式：
    - `format=json`（默认）：返回 JSON 结构化数据
    - `format=prometheus`：返回 Prometheus 纯文本格式（纯 Python 模拟，无外部依赖）
    """
    logger.info(f"📊 获取性能指标 (format={format})")

    try:
        from core.monitoring.metrics_collector import get_metrics_collector

        collector = get_metrics_collector()

        if format.lower() == "prometheus":
            # B5-PerfObs: 纯 Python 模拟 Prometheus 文本格式
            prometheus_text = collector.export_prometheus()
            return PlainTextResponse(
                content=prometheus_text,
                media_type="text/plain; version=0.0.4; charset=utf-8",
            )

        # JSON 格式（默认，向后兼容）
        from core.capabilities.capability_invoker_optimized import CapabilityInvokerOptimized
        from core.legal_world_model.scenario_identifier_optimized import ScenarioIdentifierOptimized

        identifier = ScenarioIdentifierOptimized()
        identifier_metrics = identifier.get_metrics()

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
            config_status = {
                "config_path": config_manager.config_path,
                "version": config_manager._config_version,
                "hot_reload_enabled": config_manager.enable_hot_reload,
                "is_watching": config_manager._observer is not None,
                "subscriber_count": len(config_manager._subscribers),
                "history_length": len(config_manager._config_history),
            }
        except Exception:
            # 全局配置管理器未初始化
            config_status = {"status": "not_initialized", "message": "全局配置管理器未初始化"}

        logger.info("📋 获取配置状态")
        return config_status

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
