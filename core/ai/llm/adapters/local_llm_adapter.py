
"""
统一LLM层 - 本地LLM适配器
适配本地GGUF模型(Qwen2.5-7B-Instruct-GGUF等)

作者: Claude Code
日期: 2026-01-23
"""

import logging
import time
from typing import Any

from core.ai.llm.base import BaseLLMAdapter, LLMRequest, LLMResponse, ModelCapability

logger = logging.getLogger(__name__)


class LocalLLMAdapter(BaseLLMAdapter):
    """
    本地LLM适配器

    适配本地部署的GGUF量化模型,如Qwen2.5-7B-Instruct-GGUF
    """

    def __init__(self, model_id: str, capability: ModelCapability):
        """
        初始化本地LLM适配器

        Args:
            model_id: 模型ID
            capability: 模型能力定义
        """
        super().__init__(model_id, capability)
        self.client = None

    async def initialize(self) -> bool:
        """
        初始化本地LLM

        Returns:
            bool: 初始化是否成功
        """
        try:
            from core.ai.llm.qwen_gguf_llm import LocalLLM

            self.client = LocalLLM()
            await self.client.initialize()
            self._initialized = True
            logger.info(f"✅ LocalLLM适配器初始化完成: {self.model_id}")
            return True
        except Exception as e:
            logger.warning(f"⚠️ LocalLLM适配器初始化失败: {e}")
            # 初始化失败时标记为未初始化
            self._initialized = False
            return False

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        生成响应

        Args:
            request: LLM请求

        Returns:
            LLMResponse: LLM响应
        """
        start_time = time.time()

        # 验证请求
        if not await self.validate_request(request):
            return LLMResponse(content="请求参数不合法", model_used=self.model_id)

        try:
            # 如果客户端未初始化,使用模拟响应
            if self.client is None or not self.client._initialized:
                logger.warning("⚠️ LocalLLM未初始化,返回模拟响应")
                return await self._mock_generate(request)

            # 构建提示词
            prompt = request.message
            if request.context.get("system_prompt"):
                prompt = f"{request.context['system_prompt']}\n\n{request.message}"

            # 调用本地模型
            response_text = await self.client.generate(
                prompt=prompt, max_tokens=request.max_tokens, temperature=request.temperature
            )

            # 本地模型免费
            processing_time = time.time() - start_time

            return LLMResponse(
                content=response_text,
                model_used=self.model_id,
                tokens_used=len(response_text),  # 估算
                processing_time=processing_time,
                cost=0.0,  # 本地模型免费
                quality_score=self.capability.quality_score,
            )

        except Exception as e:
            logger.error(f"❌ LocalLLM生成失败: {e}")
            # 降级到模拟响应
            return await self._mock_generate(request)

    async def _mock_generate(self, request: LLMRequest) -> LLMResponse:
        """
        模拟生成(用于测试或降级)

        Args:
            request: LLM请求

        Returns:
            LLMResponse: 模拟响应
        """
        logger.info("🧪 使用模拟模式生成本地LLM响应")

        task_type = request.task_type

        # 本地模型主要处理简单任务
        if task_type == "general_chat":
            content = f"""您好!我是本地LLM模拟响应。

您说: {request.message[:100]}...

这是一个模拟响应。本地模型(Qwen2.5-7B-Instruct-GGUF)主要用于处理日常对话和简单问答。

要使用真实的本地模型,请确保:
1. llama-cpp-python已安装
2. GGUF模型文件已下载到 models/converted 目录
3. 模型文件路径正确

注:这是模拟响应。本地模型可免费使用,适合日常对话。
"""
        elif task_type in ["simple_qa", "draft"]:
            content = f"""# 本地LLM简单响应

## 问题
{request.message[:150]}

## 回答
(本地模型模拟回答)

注:本地模型适合处理简单任务。对于复杂分析,建议使用云端推理模型。
"""
        else:
            content = f"""# 本地LLM响应(模拟)

## 任务类型
{task_type}

## 输入
{request.message[:100]}...

## 响应
(本地模型模拟响应)

注:建议使用云端推理模型处理 {task_type} 等复杂任务。
本地模型更适合日常对话和简单问答。
"""

        return LLMResponse(
            content=content.strip(),
            model_used=self.model_id,
            tokens_used=300,
            processing_time=1.5,
            cost=0.0,
            quality_score=self.capability.quality_score,
        )

    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            bool: 模型是否健康可用
        """
        if self.client is None:
            return False
        return self.client._initialized

    async def get_stats(self) -> dict[str, Any]:
        """
        获取统计信息

        Returns:
            Dict: 统计信息
        """
        stats = {
            "model_id": self.model_id,
            "initialized": self._initialized,
            "capability": self.capability.to_dict(),
            "has_client": self.client is not None,
        }

        if self.client is not None:
            stats["model_path"] = getattr(self.client, "model_path", "unknown")
            stats["n_ctx"] = getattr(self.client, "n_ctx", 0)
            stats["n_gpu_layers"] = getattr(self.client, "n_gpu_layers", 0)

        return stats

