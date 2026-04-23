from __future__ import annotations
"""
客户端任务处理API

处理来自客户端的任务请求,路由到合适的智能体
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from core.agent_collaboration.agent_coordinator import AgentCoordinator
from core.router.intelligent_router import ClientTaskRequest, RouteDecision, intelligent_router

logger = logging.getLogger(__name__)


# =============================================================================
# 数据模型
# =============================================================================


class TaskAnalysisRequest(BaseModel):
    """任务分析请求"""

    request_id: str
    client_id: str
    timestamp: str
    user_intent: dict[str, Any]
    data: dict[str, Any]
    force_cloud: bool = False


class TaskAnalysisResponse(BaseModel):
    """任务分析响应"""

    request_id: str
    status: str
    result: dict[str, Any] | None = None
    error: str = None
    metadata: dict[str, Any] | None = None


# =============================================================================
# 任务处理器
# =============================================================================


class ClientTaskProcessor:
    """
    客户端任务处理器

    处理来自客户端的任务请求,路由到合适的智能体
    """

    def __init__(self):
        """初始化任务处理器"""
        self.agent_coordinator = AgentCoordinator()

    async def process_task(self, request: TaskAnalysisRequest) -> TaskAnalysisResponse:
        """
        处理任务

        Args:
            request: 任务请求

        Returns:
            TaskAnalysisResponse: 任务响应
        """
        try:
            # 1. 转换为路由请求
            route_request = ClientTaskRequest(
                request_id=request.request_id,
                client_id=request.client_id,
                timestamp=request.timestamp,
                user_intent=request.user_intent,
                data=request.data,
                force_cloud=request.force_cloud,
                fallback_mode=request.data.get("fallback_mode", False),
            )

            # 2. 智能路由
            route_decision: RouteDecision = await intelligent_router.route(route_request)

            # 3. 调用智能体
            agent_result = await self._call_agent(
                route_decision.agent_type,
                route_decision.input_data,
                route_decision.use_local_data,
                route_decision.fallback_to_file,
            )

            # 4. 构造响应
            return TaskAnalysisResponse(
                request_id=request.request_id,
                status="success",
                result=agent_result,
                metadata={
                    "agent_used": route_decision.agent_type.value,
                    "used_local_data": route_decision.use_local_data,
                    "fallback_mode": route_decision.fallback_to_file,
                },
            )

        except Exception as e:
            logger.error(f"处理任务失败: {e}", exc_info=True)

            return TaskAnalysisResponse(
                request_id=request.request_id,
                status="error",
                error=str(e),
                metadata={"error_type": type(e).__name__},
            )

    async def _call_agent(
        self,
        agent_type: str,
        input_data: dict[str, Any],        use_local_data: bool,
        fallback_to_file: bool,
    ) -> dict[str, Any]:
        """
        调用智能体

        Args:
            agent_type: 智能体类型
            input_data: 输入数据
            use_local_data: 是否使用本地数据
            fallback_to_file: 是否降级到文件

        Returns:
            Dict: 智能体处理结果
        """
        # 根据智能体类型调用不同的智能体
        if agent_type == "xiaonuo":
            # 小诺 - 专利专家
            return await self._call_xiaonuo(input_data, use_local_data, fallback_to_file)
        elif agent_type == "xiaona":
            # 小娜 - 法律专家
            return await self._call_xiaona(input_data, use_local_data, fallback_to_file)
        elif agent_type == "athena":
            # Athena - 通用智能体
            return await self._call_athena(input_data, use_local_data, fallback_to_file)
        else:
            raise ValueError(f"未知的智能体类型: {agent_type}")

    async def _call_xiaonuo(
        self, input_data: dict[str, Any], use_local_data: bool, fallback_to_file: bool
    ) -> dict[str, Any]:
        """
        调用小诺智能体

        Args:
            input_data: 输入数据
            use_local_data: 是否使用本地数据
            fallback_to_file: 是否降级到文件

        Returns:
            Dict: 处理结果
        """
        logger.info(
            f"调用小诺智能体 (use_local_data={use_local_data}, fallback={fallback_to_file})"
        )

        # 构造提示词
        prompt_parts = []

        # 添加OCR文本
        if "text" in input_data:
            prompt_parts.append(f"OCR文本:\n{input_data['text']}")

        # 添加图片描述
        if "image_description" in input_data:
            prompt_parts.append(f"图片描述:\n{input_data['image_description']}")

        # 添加结构化数据
        if "structured_data" in input_data:
            prompt_parts.append(f"结构化数据:\n{input_data['structured_data']}")

        # 添加原始用户意图
        if "user_intent" in input_data:
            raw_input = input_data["user_intent"].get("raw_input", "")
            if raw_input:
                prompt_parts.append(f"用户请求:\n{raw_input}")

        prompt = "\n\n".join(prompt_parts)

        # 调用智能体协调器
        try:
            result = await self.agent_coordinator.process_request(
                agent_type="patent_analyst",
                request=prompt,
                context=input_data,
            )

            return {
                "analysis": result.get("analysis", ""),
                "agent_type": "xiaonuo",
                "data_sources": result.get("data_sources", []),
                "confidence": result.get("confidence", 0.0),
            }

        except Exception as e:
            logger.error(f"调用小诺失败: {e}")
            return {
                "analysis": f"处理失败: {e!s}",
                "agent_type": "xiaonuo",
                "error": str(e),
            }

    async def _call_xiaona(
        self, input_data: dict[str, Any], use_local_data: bool, fallback_to_file: bool
    ) -> dict[str, Any]:
        """
        调用小娜智能体

        Args:
            input_data: 输入数据
            use_local_data: 是否使用本地数据
            fallback_to_file: 是否降级到文件

        Returns:
            Dict: 处理结果
        """
        logger.info(
            f"调用小娜智能体 (use_local_data={use_local_data}, fallback={fallback_to_file})"
        )

        # 构造提示词
        prompt_parts = []

        # 添加OCR文本
        if "text" in input_data:
            prompt_parts.append(f"OCR文本:\n{input_data['text']}")

        # 添加图片描述
        if "image_description" in input_data:
            prompt_parts.append(f"图片描述:\n{input_data['image_description']}")

        # 添加结构化数据
        if "structured_data" in input_data:
            prompt_parts.append(f"结构化数据:\n{input_data['structured_data']}")

        # 添加原始用户意图
        if "user_intent" in input_data:
            raw_input = input_data["user_intent"].get("raw_input", "")
            if raw_input:
                prompt_parts.append(f"用户请求:\n{raw_input}")

        prompt = "\n\n".join(prompt_parts)

        # 调用智能体协调器
        try:
            result = await self.agent_coordinator.process_request(
                agent_type="legal_expert",
                request=prompt,
                context=input_data,
            )

            return {
                "analysis": result.get("analysis", ""),
                "agent_type": "xiaona",
                "data_sources": result.get("data_sources", []),
                "confidence": result.get("confidence", 0.0),
            }

        except Exception as e:
            logger.error(f"调用小娜失败: {e}")
            return {
                "analysis": f"处理失败: {e!s}",
                "agent_type": "xiaona",
                "error": str(e),
            }

    async def _call_athena(
        self, input_data: dict[str, Any], use_local_data: bool, fallback_to_file: bool
    ) -> dict[str, Any]:
        """
        调用Athena通用智能体

        Args:
            input_data: 输入数据
            use_local_data: 是否使用本地数据
            fallback_to_file: 是否降级到文件

        Returns:
            Dict: 处理结果
        """
        logger.info(
            f"调用Athena智能体 (use_local_data={use_local_data}, fallback={fallback_to_file})"
        )

        # 构造提示词
        prompt_parts = []

        # 添加OCR文本
        if "text" in input_data:
            prompt_parts.append(f"OCR文本:\n{input_data['text']}")

        # 添加图片描述
        if "image_description" in input_data:
            prompt_parts.append(f"图片描述:\n{input_data['image_description']}")

        # 添加结构化数据
        if "structured_data" in input_data:
            prompt_parts.append(f"结构化数据:\n{input_data['structured_data']}")

        # 添加原始用户意图
        if "user_intent" in input_data:
            raw_input = input_data["user_intent"].get("raw_input", "")
            if raw_input:
                prompt_parts.append(f"用户请求:\n{raw_input}")

        prompt = "\n\n".join(prompt_parts)

        # 调用智能体协调器
        try:
            result = await self.agent_coordinator.process_request(
                agent_type="general",
                request=prompt,
                context=input_data,
            )

            return {
                "analysis": result.get("analysis", ""),
                "agent_type": "athena",
                "data_sources": result.get("data_sources", []),
                "confidence": result.get("confidence", 0.0),
            }

        except Exception as e:
            logger.error(f"调用Athena失败: {e}")
            return {
                "analysis": f"处理失败: {e!s}",
                "agent_type": "athena",
                "error": str(e),
            }


# 全局任务处理器实例
client_task_processor = ClientTaskProcessor()

# =============================================================================
# API路由
# =============================================================================

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


@router.post("/analyze", response_model=TaskAnalysisResponse)
async def analyze_task(request: TaskAnalysisRequest):
    """
    分析任务

    处理来自客户端的任务请求,路由到合适的智能体
    """
    try:
        response = await client_task_processor.process_task(request)

        if response.status == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=response.error,
            )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"处理任务失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理任务失败: {e!s}",
        ) from e


# =============================================================================
# 将路由添加到主应用
# =============================================================================

# 注意:需要在主应用启动时添加
# app.include_router(router)
