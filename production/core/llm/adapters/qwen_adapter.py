"""
统一LLM层 - Qwen模型适配器
适配Qwen-Plus和Qwen-Max云端模型

作者: Claude Code
日期: 2026-01-23
"""

from __future__ import annotations
import logging
import time
from typing import Any

from core.llm.base import BaseLLMAdapter, LLMRequest, LLMResponse, ModelCapability
from core.llm.security_utils import SensitiveDataFilter

logger = logging.getLogger(__name__)
# 添加敏感数据过滤器
logger.addFilter(SensitiveDataFilter())


class QwenAdapter(BaseLLMAdapter):
    """
    Qwen模型适配器

    适配阿里云通义千问系列模型
    """

    def __init__(self, model_id: str, capability: ModelCapability):
        """
        初始化Qwen适配器

        Args:
            model_id: 模型ID (qwen-plus 或 qwen-max)
            capability: 模型能力定义
        """
        super().__init__(model_id, capability)
        self.client = None

    async def initialize(self) -> bool:
        """
        初始化Qwen客户端

        Returns:
            bool: 初始化是否成功
        """
        try:
            from core.llm.qwen_client import QwenClient

            self.client = QwenClient(model=self.model_id)
            self._initialized = True
            logger.info(f"✅ Qwen适配器初始化完成: {self.model_id}")
            return True
        except (ImportError, ValueError, ConnectionError) as e:
            logger.warning(f"⚠️ Qwen适配器初始化失败: {e}", exc_info=True)
            self._initialized = False
            return False
        except Exception as e:
            logger.error(f"❌ Qwen适配器初始化发生未预期错误: {e}", exc_info=True)
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
            # 如果客户端是模拟模式或未初始化,使用模拟响应
            if self.client is None or getattr(self.client, "mock_mode", False):
                return await self._mock_generate(request)

            # 构建消息
            messages = []
            if request.context.get("system_prompt"):
                messages.append({"role": "system", "content": request.context["system_prompt"]})
            messages.append({"role": "user", "content": request.message})

            # 调用Qwen API
            response = await self.client.chat(
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
            logger.error(f"❌ Qwen生成失败: {e}", exc_info=True)
            return await self._mock_generate(request)
        except Exception as e:
            logger.error(f"❌ Qwen生成发生未预期错误: {e}", exc_info=True)
            return await self._mock_generate(request)

    async def _mock_generate(self, request: LLMRequest) -> LLMResponse:
        """
        模拟生成(用于测试或降级)

        Args:
            request: LLM请求

        Returns:
            LLMResponse: 模拟响应
        """
        logger.info("🧪 使用模拟模式生成Qwen响应")

        task_type = request.task_type

        if task_type in ["creativity_analysis", "novelty_analysis", "invalidation_analysis"]:
            content = f"""# {task_type.replace('_', ' ').title()}(Qwen模拟)

## 任务类型
{task_type}

## 输入
{request.message[:200]}...

## 分析过程
(Qwen推理过程模拟)

### 步骤1:理解问题
分析请求的核心内容...

### 步骤2:技术对比
对比现有技术与目标技术...

### 步骤3:结论判断
基于分析得出结论...

## 结论
(模拟分析结论)

注:这是模拟响应。请配置DASHSCOPE_API_KEY以获取实际分析。
"""
        elif task_type == "general_chat":
            content = f"""您好!我是Qwen(通义千问)模拟响应。

您说: {request.message[:100]}...

这是一个模拟响应。通义千问是阿里云开发的大语言模型。

要使用真实的Qwen API,请设置DASHSCOPE_API_KEY环境变量。

注:这是模拟响应,仅供测试。
"""
        else:
            content = f"""# Qwen响应(模拟)

## 任务类型
{task_type}

## 输入
{request.message[:150]}...

## 响应
(Qwen模拟响应)

注:请配置DASHSCOPE_API_KEY以获取实际响应。
"""

        return LLMResponse(
            content=content.strip(),
            model_used=self.model_id,
            tokens_used=500,
            processing_time=0.6,
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

        # 如果是模拟模式,总是返回健康
        if getattr(self.client, "mock_mode", False):
            return True

        try:
            # 简单测试请求
            test_response = await self.client.chat(
                messages=[{"role": "user", "content": "test"}], temperature=0.1, max_tokens=10
            )
            return bool(test_response.get("content"))
        except (ConnectionError, TimeoutError) as e:
            logger.warning(f"⚠️ Qwen健康检查失败: {e}")
            return False
        except Exception as e:
            logger.warning(f"⚠️ Qwen健康检查发生未预期错误: {e}", exc_info=True)
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
