
"""
统一LLM层 - LiteRT-LM适配器
适配本地LiteRT-LM推理服务(Gemma 4 E4B多模态模型)
通过 OpenAI 兼容 API 连接 LiteRT-LM 推理服务 (端口 8767)

作者: Claude Code
日期: 2026-04-14
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

# LiteRT-LM 服务默认地址
LITERT_LM_BASE_URL = "http://127.0.0.1:8767"


class LiteRTLMLAdapter(BaseLLMAdapter):
    """
    LiteRT-LM适配器

    适配本地部署的LiteRT-LM推理服务(Gemma 4 E4B)
    通过 OpenAI 兼容 API 连接，支持文本对话和图像识别
    """

    def __init__(
        self,
        model_id: str,
        capability: ModelCapability,
        base_url: str = LITERT_LM_BASE_URL,
    ):
        """
        初始化LiteRT-LM适配器

        Args:
            model_id: 模型ID(如 litert-lm-gemma4-e4b)
            capability: 模型能力定义
            base_url: LiteRT-LM服务地址(默认 http://127.0.0.1:8767)
        """
        super().__init__(model_id, capability)
        self.base_url = base_url.rstrip("/")
        self.api_base = f"{self.base_url}/v1"
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
        初始化LiteRT-LM适配器

        Returns:
            bool: 初始化是否成功
        """
        try:
            timeout = aiohttp.ClientTimeout(total=120)
            self.client = aiohttp.ClientSession(timeout=timeout)

            is_healthy = await self.health_check()

            if is_healthy:
                self._initialized = True
                logger.info(f"✅ LiteRT-LM适配器初始化完成: {self.model_id} @ {self.base_url}")
            else:
                logger.warning(f"⚠️ LiteRT-LM服务不可用: {self.base_url}")
                self._initialized = False

            return self._initialized

        except Exception as e:
            logger.warning(f"⚠️ LiteRT-LM适配器初始化失败: {e}")
            self._initialized = False
            return False

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        生成响应（使用 OpenAI Chat Completions API）

        支持纯文本对话和多模态图像识别。

        Args:
            request: LLM请求

        Returns:
            LLMResponse: LLM响应
        """
        start_time = time.time()

        if not await self.validate_request(request):
            return LLMResponse(
                content="请求参数不合法",
                model_used=self.model_id,
                processing_time=time.time() - start_time,
            )

        self.stats["total_requests"] += 1

        try:
            # 构建消息
            messages = []
            if request.context.get("system_prompt"):
                messages.append({
                    "role": "system",
                    "content": request.context["system_prompt"]
                })

            # 多模态支持：检查是否有图像输入
            images = request.context.get("images", [])
            if images:
                content_parts = []
                for img in images:
                    if isinstance(img, str):
                        # 文件路径或 base64
                        if img.startswith("/") or img.startswith("file://"):
                            # 本地文件路径 -> 需要转为 base64 data URL
                            import base64
                            from pathlib import Path
                            path = img.replace("file://", "")
                            img_bytes = Path(path).read_bytes()
                            b64 = base64.b64encode(img_bytes).decode()
                            suffix = Path(path).suffix.lstrip(".") or "png"
                            mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png"}.get(suffix, "png")
                            content_parts.append({
                                "type": "image_url",
                                "image_url": {"url": f"data:image/{mime};base64,{b64}"}
                            })
                        else:
                            # 假设是 base64 编码
                            content_parts.append({
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{img}"}
                            })
                    elif isinstance(img, dict):
                        content_parts.append(img)

                content_parts.append({"type": "text", "text": request.message})
                messages.append({"role": "user", "content": content_parts})
            else:
                messages.append({"role": "user", "content": request.message})

            # 调用LiteRT-LM OpenAI兼容API
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
                    logger.error(f"LiteRT-LM API错误: {response.status} - {error_text}")
                    self.stats["failed_requests"] += 1
                    return LLMResponse(
                        content=f"API调用失败: {response.status}",
                        model_used=self.model_id,
                        processing_time=time.time() - start_time,
                    )

                data = await response.json()

            # 解析响应
            message = data["choices"][0]["message"]
            content = message.get("content", "")
            tokens_used = data.get("usage", {}).get("total_tokens", 0)
            processing_time = time.time() - start_time

            # 更新统计
            self.stats["successful_requests"] += 1
            self.stats["total_tokens"] += tokens_used
            self.stats["total_processing_time"] += processing_time

            return LLMResponse(
                content=content,
                model_used=self.model_id,
                tokens_used=tokens_used,
                processing_time=processing_time,
                cost=0.0,
                quality_score=self.capability.quality_score,
            )

        except TimeoutError:
            logger.error(f"LiteRT-LM请求超时: {self.model_id}")
            self.stats["failed_requests"] += 1
            return LLMResponse(
                content="请求超时",
                model_used=self.model_id,
                processing_time=time.time() - start_time,
            )
        except Exception as e:
            logger.error(f"LiteRT-LM生成失败: {e}", exc_info=True)
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
            async with self.client.get(f"{self.api_base}/models") as response:
                if response.status != 200:
                    return False

                data = await response.json()
                models = data.get("data", [])
                model_ids = [m.get("id", "") for m in models]

                # 精确匹配或前缀匹配
                if self.model_id in model_ids:
                    return True

                short_name = self.model_id.split(":")[0]
                return any(
                    mid.startswith(short_name) or short_name in mid
                    for mid in model_ids
                )

        except Exception as e:
            logger.warning(f"LiteRT-LM健康检查失败: {e}")
            return False

    async def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
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
        logger.info(f"🔌 LiteRT-LM适配器已关闭: {self.model_id}")


# 便捷函数：创建LiteRT模型能力配置
def create_litert_capabilities() -> dict[str, ModelCapability]:
    """
    创建LiteRT-LM模型的能力配置

    Returns:
        Dict[str, ModelCapability]: 模型ID到能力的映射
    """
    return {
        "litert-lm-gemma4-e4b": ModelCapability(
            model_id="litert-lm-gemma4-e4b",
            model_type=ModelType.MULTIMODAL,
            deployment=DeploymentType.LOCAL,
            max_context=4096,  # Gemma 4 E4B 默认上下文
            supports_streaming=True,
            supports_function_call=True,
            supports_vision=True,
            supports_thinking=False,
            avg_latency_ms=6000.0,  # ~6s/100字
            throughput_tps=15.0,
            cost_per_1k_tokens=0.0,  # 本地免费
            quality_score=0.85,
            suitable_tasks=[
                "image_analysis", "multimodal", "chart_analysis",
                "document_analysis", "ocr", "visual_reasoning",
                "chat", "chinese", "general_chat",
            ],
            unsuitable_tasks=[
                "novelty_analysis", "creativity_analysis",
                "invalidation_analysis", "long_document",
            ],
        ),
    }

