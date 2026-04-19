#!/usr/bin/env python3
from __future__ import annotations
"""
智能意图识别API路由
Intelligent Intent Recognition API Routes

提供RESTful API接口,整合Athena平台的多种AI能力:
- 三层意图识别(规则 + 语义 + 深度分析)
- BGE-M3语义理解
- BERT-NER实体识别
- 推理引擎自动选择

作者: Athena AI Team
版本: 1.0.0
创建: 2026-01-23
"""

import logging
import time
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

# 导入智能意图识别服务
from core.intent.intelligent_intent_service import (
    IntentRecognitionResult,
    get_intelligent_intent_service,
)

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/v1/intent", tags=["智能意图识别"])


# =============================================================================
# 请求/响应模型
# =============================================================================


class IntentRecognitionRequest(BaseModel):
    """意图识别请求"""

    text: str = Field(..., description="用户输入文本", min_length=1, max_length=5000)
    context: dict[str, Any] = Field(None, description="上下文信息(可选)")
    enable_l1: bool = Field(True, description="启用第一层规则匹配")
    enable_l2: bool = Field(True, description="启用第二层语义匹配")
    enable_l3: bool = Field(True, description="启用第三层深度分析")
    return_task_profile: bool = Field(False, description="是否返回任务画像")
    return_entities: bool = Field(False, description="是否返回提取的实体")
    return_thought_trace: bool = Field(
        False, description="是否返回思维协议追踪(仅在L3深度分析时有效)"
    )


class IntentBatchRecognitionRequest(BaseModel):
    """批量意图识别请求"""

    texts: list[str] = Field(..., description="文本列表", min_length=1, max_length=100)
    context: dict[str, Any] | None = None


class EngineRecommendation(BaseModel):
    """推理引擎推荐"""

    engine_name: str
    engine_type: str
    confidence: float
    reason: str
    bypass_super_reasoning: bool = False


class IntentRecognitionResponse(BaseModel):
    """意图识别响应"""

    success: bool
    intent: str
    confidence: float
    matched_at_layer: str
    processing_time_ms: float
    methods_used: list[str]

    # 可选字段
    recommended_engine: str | None = None
    engine_reason: str | None = None
    bypass_super_reasoning: bool | None = None
    entities: dict[str, list[str]] | None = None
    task_profile: dict[str, Any] | None = None
    thought_trace: dict[str, Any] | None = None  # 思维协议追踪
    timestamp: str = None


class BatchIntentResponse(BaseModel):
    """批量意图识别响应"""

    success: bool
    total: int
    results: list[IntentRecognitionResponse]
    total_time_ms: float
    average_time_ms: float


class ServiceStatistics(BaseModel):
    """服务统计信息"""

    total_requests: int
    l1_matches: int
    l2_matches: int
    l3_matches: int
    thinking_protocol_used: int  # 思维协议使用次数
    no_match: int
    l1_rate: float
    l2_rate: float
    l3_rate: float
    no_match_rate: float


# =============================================================================
# API端点
# =============================================================================


@router.post("/recognize", response_model=IntentRecognitionResponse)
async def recognize_intent(request: IntentRecognitionRequest):
    """
    识别用户意图

    整合三层识别能力:
    1. 规则匹配 - 快速响应(<5ms)
    2. 语义理解 - BGE-M3向量匹配(<50ms)
    3. 深度分析 - NER + 推理引擎编排 + 思维协议(<500ms)

    通过设置 return_thought_trace=True,可以获取L3深度分析的完整思维轨迹。
    """
    try:
        # 获取服务实例
        config = {
            "enable_l1": request.enable_l1,
            "enable_l2": request.enable_l2,
            "enable_l3": request.enable_l3,
        }
        service = get_intelligent_intent_service(config)

        # 构建上下文(包含思维追踪请求)
        context = request.context or {}
        if request.return_thought_trace:
            context["return_thought_trace"] = True

        # 执行意图识别
        result: IntentRecognitionResult = await service.recognize_intent(request.text, context)

        # 构建响应
        response_data = {
            "success": True,
            "intent": result.intent.value,
            "confidence": result.confidence,
            "matched_at_layer": result.matched_at_layer.value,
            "processing_time_ms": result.processing_time_ms,
            "methods_used": result.methods_used,
            "timestamp": result.timestamp.isoformat(),
        }

        # 可选字段
        if result.recommended_engine:
            response_data["recommended_engine"] = result.recommended_engine
        if result.engine_reason:
            response_data["engine_reason"] = result.engine_reason
        if result.bypass_super_reasoning:
            response_data["bypass_super_reasoning"] = result.bypass_super_reasoning

        if request.return_entities and result.entities:
            response_data["entities"] = result.entities

        if request.return_task_profile and result.task_profile:
            response_data["task_profile"] = result.task_profile

        # 思维追踪
        if result.thought_trace:
            response_data["thought_trace"] = result.thought_trace

        return IntentRecognitionResponse(**response_data)

    except Exception as e:
        logger.error(f"意图识别失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"意图识别失败: {e!s}"
        ) from e


@router.post("/recognize-batch", response_model=BatchIntentResponse)
async def recognize_intent_batch(request: IntentBatchRecognitionRequest):
    """
    批量识别意图

    适用于需要处理多个文本的场景,如日志分析、客服对话等。
    """
    try:
        service = get_intelligent_intent_service()

        start_time = time.time()
        results = []

        for text in request.texts:
            result = await service.recognize_intent(text, request.context)

            response_data = {
                "success": True,
                "intent": result.intent.value,
                "confidence": result.confidence,
                "matched_at_layer": result.matched_at_layer.value,
                "processing_time_ms": result.processing_time_ms,
                "methods_used": result.methods_used,
                "timestamp": result.timestamp.isoformat(),
            }

            results.append(IntentRecognitionResponse(**response_data))

        total_time = (time.time() - start_time) * 1000
        avg_time = total_time / len(request.texts)

        return BatchIntentResponse(
            success=True,
            total=len(results),
            results=results,
            total_time_ms=total_time,
            average_time_ms=avg_time,
        )

    except Exception as e:
        logger.error(f"批量意图识别失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"批量识别失败: {e!s}"
        ) from e


@router.get("/categories", response_model=dict[str, str])
async def list_intent_categories():
    """
    列出所有支持的意图类别

    返回意图类别及其描述
    """
    categories = {
        # 专利相关
        "patent_search": "专利检索 - 搜索和查找专利文献",
        "patent_drafting": "专利撰写 - 起草专利申请文件",
        "patent_analysis": "专利分析 - 分析专利内容",
        "novelty_analysis": "新颖性分析 - 评估发明的新颖性",
        "inventiveness_analysis": "创造性分析 - 评估发明的创造性",
        "invalidity_request": "无效宣告 - 专利无效宣告请求",
        # 法律相关
        "legal_query": "法律咨询 - 法律问题咨询",
        "legal_research": "法律检索 - 法律文献检索",
        "contract_analysis": "合同分析 - 分析合同内容",
        "compliance_check": "合规检查 - 检查合规性",
        # 技术相关
        "code_generation": "代码生成 - 生成代码",
        "data_analysis": "数据分析 - 分析数据",
        "technical_research": "技术研究 - 技术研究",
        # 通用任务
        "problem_solving": "问题解决 - 解决问题",
        "decision_support": "决策支持 - 辅助决策",
        "creative_writing": "创意写作 - 创意内容生成",
        # 系统相关
        "system_control": "系统控制 - 控制系统",
        "knowledge_query": "知识查询 - 查询知识",
        # 情感交互
        "emotional": "情感表达 - 情感交流",
        "chitchat": "闲聊 - 日常对话",
    }

    return categories


@router.get("/statistics", response_model=ServiceStatistics)
async def get_service_statistics():
    """
    获取服务统计信息

    返回意图识别服务的性能统计数据
    """
    try:
        service = get_intelligent_intent_service()
        stats = service.get_statistics()

        return ServiceStatistics(**stats)

    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取统计信息失败: {e!s}"
        ) from e


@router.get("/health")
async def health_check():
    """
    健康检查端点

    检查智能意图识别服务的健康状态
    """
    try:
        service = get_intelligent_intent_service()
        stats = service.get_statistics()

        return {
            "status": "healthy",
            "service": "intelligent_intent_recognition",
            "version": "1.1.0",  # 升级版本号
            "total_processed": stats["total_requests"],
            "components": {
                "l1_rule_matcher": service.l1_matcher is not None,
                "l2_semantic_matcher": service.l2_matcher is not None,
                "l3_deep_analyzer": service.l3_analyzer is not None,
                "thinking_protocol_analyzer": service.thinking_analyzer is not None,
            },
        }

    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


# =============================================================================
# 路由注册函数
# =============================================================================


def register_intelligent_intent_routes(app):
    """
    注册智能意图识别路由到FastAPI应用

    Args:
        app: FastAPI应用实例
    """
    app.include_router(router)
    logger.info("✅ 智能意图识别API路由已注册")


# 导出路由器
__all__ = ["register_intelligent_intent_routes", "router"]
