
"""
统一LLM层 - MLX适配器
适配本地MLX推理服务(支持glm-4.7-flash、qwen等模型)
通过 OpenAI 兼容 API 连接 MLX 推理服务 (端口 8765/8766)

作者: Claude Code
日期: 2026-04-07
"""

import logging
import time
from typing import Any, Optional

import aiohttp

from core.ai.llm.base import (
    BaseLLMAdapter,
    DeploymentType,
    LLMRequest,
    LLMResponse,
    ModelCapability,
    ModelType,
)

logger = logging.getLogger(__name__)

# MLX 服务默认地址
MLX_LLM_BASE_URL = "http://127.0.0.1:8765"
MLX_EMBEDDING_BASE_URL = "http://127.0.0.1:8766"


class MLXAdapter(BaseLLMAdapter):
    """
    MLX适配器

    适配本地部署的MLX推理服务
    通过 OpenAI 兼容 API 连接，支持 glm-4.7-flash、qwen 等模型
    """

    def __init__(
        self,
        model_id: str,
        capability: ModelCapability,
        base_url: str = MLX_LLM_BASE_URL,
    ):
        """
        初始化MLX适配器

        Args:
            model_id: 模型ID(如 glm47flash)
            capability: 模型能力定义
            base_url: MLX服务地址(默认 http://127.0.0.1:8765)
        """
        super().__init__(model_id, capability)
        self.base_url = base_url.rstrip("/")
        self.api_base = f"{self.base_url}/v1"  # OpenAI兼容API
        self.client: aiohttp.Optional[ClientSession] = None

        # 统计信息
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_tokens": 0,
            "total_processing_time": 0.0,
        }

    async def initialize(self) -> bool:
        """
        初始化MLX适配器

        Returns:
            bool: 初始化是否成功
        """
        try:
            # 创建HTTP客户端
            timeout = aiohttp.ClientTimeout(total=120)
            self.client = aiohttp.ClientSession(timeout=timeout)

            # 健康检查
            is_healthy = await self.health_check()

            if is_healthy:
                self._initialized = True
                logger.info(f"✅ MLX适配器初始化完成: {self.model_id} @ {self.base_url}")
            else:
                logger.warning(f"⚠️ MLX服务不可用: {self.base_url}")
                self._initialized = False

            return self._initialized

        except Exception as e:
            logger.warning(f"⚠️ MLX适配器初始化失败: {e}")
            self._initialized = False
            return False

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        生成响应（使用 OpenAI Chat Completions API）

        Args:
            request: LLM请求

        Returns:
            LLMResponse: LLM响应
        """
        start_time = time.time()

        # 验证请求
        if not await self.validate_request(request):
            return LLMResponse(
                content="请求参数不合法",
                model_used=self.model_id,
                processing_time=time.time() - start_time,
            )

        # 更新统计
        self.stats["total_requests"] += 1

        try:
            # 构建消息
            messages = []
            if request.context.get("system_prompt"):
                messages.append({
                    "role": "system",
                    "content": request.context["system_prompt"]
                })
            messages.append({
                "role": "user",
                "content": request.message
            })

            # 调用MLX OpenAI兼容API
            payload = {
                "model": self.model_id,
                "messages": messages,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "stream": False,
            }

            async with self.client.post(
                f"{self.api_base}/chat/completions",
                json=payload,
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"MLX API错误: {response.status} - {error_text}")
                    self.stats["failed_requests"] += 1
                    return LLMResponse(
                        content=f"API调用失败: {response.status}",
                        model_used=self.model_id,
                        processing_time=time.time() - start_time,
                    )

                data = await response.json()

            # 解析响应 - 支持Qwen3.5 thinking模式
            message = data["choices"][0]["message"]
            # 优先使用content字段，如果为空则使用reasoning字段（Qwen3.5 thinking模式）
            content = message.get("content", "") or message.get("reasoning", "")
            reasoning_content = message.get("reasoning", "")
            tokens_used = data.get("usage", {}).get("total_tokens", 0)
            processing_time = time.time() - start_time

            # 更新统计
            self.stats["successful_requests"] += 1
            self.stats["total_tokens"] += tokens_used
            self.stats["total_processing_time"] += processing_time

            return LLMResponse(
                content=content,
                model_used=self.model_id,
                reasoning_content=reasoning_content,  # 保存思考过程
                tokens_used=tokens_used,
                processing_time=processing_time,
                cost=0.0,  # 本地模型免费
                quality_score=self.capability.quality_score,
            )

        except TimeoutError:
            logger.error(f"MLX请求超时: {self.model_id}")
            self.stats["failed_requests"] += 1
            return LLMResponse(
                content="请求超时",
                model_used=self.model_id,
                processing_time=time.time() - start_time,
            )
        except Exception as e:
            logger.error(f"MLX生成失败: {e}", exc_info=True)
            self.stats["failed_requests"] += 1
            return LLMResponse(
                content=f"生成失败: {str(e)}",
                model_used=self.model_id,
                processing_time=time.time() - start_time,
            )

    async def health_check(self) -> bool:
        """
        健康检查（使用 OpenAI 兼容 /v1/models 端点）

        Returns:
            bool: 模型是否健康可用
        """
        if not self.client:
            return False

        try:
            # 使用 OpenAI 兼容的 /v1/models 端点检查服务状态
            async with self.client.get(f"{self.api_base}/models") as response:
                if response.status != 200:
                    return False

                data = await response.json()

                # OpenAI 格式: data.data[].id
                models = data.get("data", [])
                model_ids = [m.get("id", "") for m in models]

                # 检查模型是否在列表中
                if self.model_id in model_ids:
                    return True

                # 模糊匹配（前缀或短名称）
                short_name = self.model_id.split(":")[0]
                return any(
                    mid.startswith(short_name) or short_name in mid
                    for mid in model_ids
                )

        except Exception as e:
            logger.warning(f"MLX健康检查失败: {e}")
            return False

    async def get_stats(self) -> dict[str, Any]:
        """
        获取统计信息

        Returns:
            Dict: 统计信息字典
        """
        avg_time = 0.0
        if self.stats["successful_requests"] > 0:
            avg_time = (
                self.stats["total_processing_time"]
                / self.stats["successful_requests"]
            )

        success_rate = 0.0
        if self.stats["total_requests"] > 0:
            success_rate = self.stats["successful_requests"] / self.stats["total_requests"]

        return {
            "model_id": self.model_id,
            "total_requests": self.stats["total_requests"],
            "successful_requests": self.stats["successful_requests"],
            "failed_requests": self.stats["failed_requests"],
            "success_rate": success_rate,
            "total_tokens": self.stats["total_tokens"],
            "average_processing_time": avg_time,
            "base_url": self.base_url,
        }

    async def close(self):
        """关闭客户端"""
        if self.client:
            await self.client.close()
            self.client = None
        logger.info(f"🔌 MLX适配器已关闭: {self.model_id}")


# 便捷函数：创建常用的MLX模型配置
def create_mlx_capabilities() -> dict[str, ModelCapability]:
    """
    创建常用MLX模型的能力配置

    Returns:
        Dict[str, ModelCapability]: 模型ID到能力的映射
    """
    return {
        # ==================== GLM-4.7-Flash (默认) ====================
        "glm47flash": ModelCapability(
            model_id="glm47flash",
            model_type=ModelType.CHAT,
            deployment=DeploymentType.LOCAL,
            max_context=131072,  # 128K上下文
            supports_streaming=True,
            supports_function_call=False,
            supports_vision=False,
            supports_thinking=False,
            avg_latency_ms=800.0,
            throughput_tps=45.0,
            cost_per_1k_tokens=0.0,  # 本地免费
            quality_score=0.92,
            suitable_tasks=["chat", "analysis", "reasoning", "chinese"],
        ),
        # ==================== Qwen3.5 多模态模型 ====================
        "qwen3.5": ModelCapability(
            model_id="qwen3.5",
            model_type=ModelType.MULTIMODAL,
            deployment=DeploymentType.LOCAL,
            max_context=262144,  # 支持超长上下文
            supports_streaming=True,
            supports_function_call=True,
            supports_vision=True,
            supports_thinking=True,
            avg_latency_ms=1000.0,
            throughput_tps=40.0,
            cost_per_1k_tokens=0.0,
            quality_score=0.93,
            suitable_tasks=[
                "image_analysis", "multimodal", "chart_analysis",
                "document_analysis", "ocr", "visual_reasoning",
                "chat", "chinese", "reasoning",
            ],
        ),
        # ==================== 其他本地模型 ====================
        "qwen2.5-14b": ModelCapability(
            model_id="qwen2.5-14b",
            model_type=ModelType.CHAT,
            deployment=DeploymentType.LOCAL,
            max_context=32768,
            supports_streaming=True,
            supports_function_call=False,
            supports_vision=False,
            supports_thinking=False,
            avg_latency_ms=1200.0,
            throughput_tps=30.0,
            cost_per_1k_tokens=0.0,
            quality_score=0.88,
            suitable_tasks=["chat", "chinese", "writing"],
        ),
        "qwen2.5-7b": ModelCapability(
            model_id="qwen2.5-7b",
            model_type=ModelType.CHAT,
            deployment=DeploymentType.LOCAL,
            max_context=32768,
            supports_streaming=True,
            supports_function_call=False,
            supports_vision=False,
            supports_thinking=False,
            avg_latency_ms=600.0,
            throughput_tps=60.0,
            cost_per_1k_tokens=0.0,
            quality_score=0.82,
            suitable_tasks=["chat", "chinese", "writing"],
        ),
        # ==================== Embedding 模型 ====================
        "bge-m3": ModelCapability(
            model_id="bge-m3",
            model_type=ModelType.SPECIALIZED,
            deployment=DeploymentType.LOCAL,
            max_context=8192,
            supports_streaming=False,
            supports_function_call=False,
            supports_vision=False,
            supports_thinking=False,
            avg_latency_ms=200.0,
            throughput_tps=100.0,
            cost_per_1k_tokens=0.0,
            quality_score=0.95,
            suitable_tasks=["embedding", "search", "retrieval"],
        ),
    }

