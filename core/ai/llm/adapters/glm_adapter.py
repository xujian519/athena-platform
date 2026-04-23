
"""
统一LLM层 - GLM模型适配器
适配GLM-4.7-Plus和GLM-4-Flash模型

作者: Claude Code
日期: 2026-01-23
"""

import logging
import time
from typing import Any

from core.ai.llm.base import BaseLLMAdapter, LLMRequest, LLMResponse, ModelCapability
from core.ai.llm.security_utils import SensitiveDataFilter

logger = logging.getLogger(__name__)
# 添加敏感数据过滤器
logger.addFilter(SensitiveDataFilter())


class GLMAdapter(BaseLLMAdapter):
    """
    GLM模型适配器

    适配智谱AI的GLM系列模型,包括GLM-4-Plus和GLM-4-Flash
    """

    def __init__(self, model_id: str, capability: ModelCapability):
        """
        初始化GLM适配器

        Args:
            model_id: 模型ID (glm-4-plus 或 glm-4-flash)
            capability: 模型能力定义
        """
        super().__init__(model_id, capability)
        self.client = None

    async def initialize(self) -> bool:
        """
        初始化GLM客户端

        Returns:
            bool: 初始化是否成功
        """
        try:
            from core.ai.llm.glm47_client import GLM47Client

            self.client = GLM47Client(model=self.model_id)
            self._initialized = True
            logger.info(f"✅ GLM适配器初始化完成: {self.model_id}")
            return True
        except (ImportError, ValueError, ConnectionError) as e:
            logger.warning(f"⚠️ GLM适配器初始化失败: {e}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"❌ GLM适配器初始化发生未预期错误: {e}", exc_info=True)
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
            # 如果客户端是模拟模式,使用模拟响应
            if hasattr(self.client, "mock_mode") and self.client.mock_mode:
                return await self._mock_generate(request)

            # 构建消息
            messages = []
            if request.context.get("system_prompt"):
                messages.append({"role": "system", "content": request.context["system_prompt"]})
            messages.append({"role": "user", "content": request.message})

            # 调用GLM API - 使用httpx直接调用
            response = await self._call_glm_api(
                messages=messages, temperature=request.temperature, max_tokens=request.max_tokens
            )

            # 计算成本和统计
            tokens_used = response.get("usage", {}).get("total_tokens", 0)
            cost = self.capability.estimate_cost(tokens_used)
            processing_time = time.time() - start_time

            return LLMResponse(
                content=response.get("content", ""),
                model_used=self.model_id,
                tokens_used=tokens_used,
                processing_time=processing_time,
                cost=cost,
                quality_score=self.capability.quality_score,
                raw_response=response,
            )

        except (ConnectionError, TimeoutError, ValueError) as e:
            logger.error(f"❌ GLM生成失败: {e}", exc_info=True)
            return LLMResponse(content=f"生成失败: {e!s}", model_used=self.model_id)
        except Exception as e:
            logger.error(f"❌ GLM生成发生未预期错误: {e}", exc_info=True)
            return LLMResponse(content="生成失败: 系统错误", model_used=self.model_id)

    async def _call_glm_api(
        self, messages: list, temperature: float, max_tokens: int
    ) -> dict[str, Any]:
        """
        调用GLM API

        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大tokens数

        Returns:
            Dict: API响应
        """
        import httpx

        headers = {
            "Authorization": f"Bearer {self.client.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model_id,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=self.client.timeout) as client:
            response = await client.post(
                f"{self.client.base_url}chat/completions", headers=headers, json=payload
            )
            response.raise_for_status()
            data = response.json()

            # 解析响应
            return {
                "content": data["choices"][0]["message"]["content"],
                "usage": {
                    "total_tokens": data["usage"]["total_tokens"],
                    "prompt_tokens": data["usage"]["prompt_tokens"],
                    "completion_tokens": data["usage"]["completion_tokens"],
                },
                "model": data.get("model", self.model_id),
            }

    async def _mock_generate(self, request: LLMRequest) -> LLMResponse:
        """
        模拟生成(用于测试)

        Args:
            request: LLM请求

        Returns:
            LLMResponse: 模拟响应
        """
        logger.info("🧪 使用模拟模式生成响应")

        # 根据任务类型返回不同的模拟响应
        task_type = request.task_type
        if task_type == "creativity_analysis":
            content = f"""
# 创造性分析(模拟)

基于您的请求:" {request.message[:100]}..."

## 三步法分析

### 第一步:确定最接近的现有技术
(此处为模拟分析结果)

### 第二步:确定区别技术特征和实际解决的技术问题
(此处为模拟分析结果)

### 第三步:判断是否显而易见
(此处为模拟分析结果)

## 结论
本申请具备创造性。

注:这是模拟响应,请配置真实的API密钥以获取实际分析。
"""
        elif task_type == "novelty_analysis":
            content = f"""
# 新颖性分析(模拟)

基于您的请求:" {request.message[:100]}..."

## 对比分析
(此处为模拟分析结果)

## 结论
本申请新颖性分析完成。

注:这是模拟响应,请配置真实的API密钥以获取实际分析。
"""
        else:
            content = f"""
# 响应(模拟)

您的问题是: {request.message[:100]}...

(此处为模拟响应)

注:这是模拟响应,请配置真实的API密钥以获取实际响应。
"""

        return LLMResponse(
            content=content.strip(),
            model_used=self.model_id,
            tokens_used=500,  # 模拟token数
            processing_time=0.5,  # 模拟处理时间
            cost=0.0,  # 模拟模式无成本
        )

    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            bool: 模型是否健康可用
        """
        if not self._initialized or self.client is None:
            return False

        # 如果是模拟模式,总是返回健康
        if hasattr(self.client, "mock_mode") and self.client.mock_mode:
            return True

        try:
            # 简单测试请求
            test_response = await self._call_glm_api(
                messages=[{"role": "user", "content": "test"}], temperature=0.1, max_tokens=10
            )
            return bool(test_response.get("content"))
        except (ConnectionError, TimeoutError) as e:
            logger.warning(f"⚠️ GLM健康检查失败: {e}")
            return False
        except Exception as e:
            logger.warning(f"⚠️ GLM健康检查发生未预期错误: {e}", exc_info=True)
            return False

    async def get_stats(self) -> dict[str, Any]:
        """
        获取统计信息

        Returns:
            Dict: 统计信息
        """
        return {
            "model_id": self.model_id,
            "initialized": self._initialized,
            "capability": self.capability.to_dict(),
            "mock_mode": getattr(self.client, "mock_mode", False) if self.client else False,
        }

