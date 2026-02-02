"""
统一LLM层 - DeepSeek模型适配器
适配DeepSeek-Chat和DeepSeek-Reasoner模型

作者: Claude Code
日期: 2026-01-23
"""

import logging
import time
from typing import Any, Dict

from core.llm.base import BaseLLMAdapter, LLMRequest, LLMResponse, ModelCapability
from core.llm.security_utils import SensitiveDataFilter, mask_api_key

logger = logging.getLogger(__name__)
# 添加敏感数据过滤器
logger.addFilter(SensitiveDataFilter())


class DeepSeekAdapter(BaseLLMAdapter):
    """
    DeepSeek模型适配器

    适配DeepSeek的AI模型,包括DeepSeek-Chat和DeepSeek-Reasoner
    """

    def __init__(self, model_id: str, capability: ModelCapability):
        """
        初始化DeepSeek适配器

        Args:
            model_id: 模型ID (deepseek-chat 或 deepseek-reasoner)
            capability: 模型能力定义
        """
        super().__init__(model_id, capability)
        self.client = None

    async def initialize(self) -> bool:
        """
        初始化DeepSeek客户端

        Returns:
            bool: 初始化是否成功
        """
        try:
            from core.llm.deepseek_client import DeepSeekClient

            self.client = DeepSeekClient(model=self.model_id)
            self._initialized = True
            logger.info(f"✅ DeepSeek适配器初始化完成: {self.model_id}")
            return True
        except (ImportError, ValueError, ConnectionError) as e:
            logger.warning(f"⚠️ DeepSeek适配器初始化失败: {e}", exc_info=True)
            self._initialized = False
            return False
        except Exception as e:
            logger.error(f"❌ DeepSeek适配器初始化发生未预期错误: {e}", exc_info=True)
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
            if self.client is None:
                return await self._mock_generate(request)

            # 调用DeepSeek推理接口
            response = await self.client.reason(
                problem=request.message,
                task_type=request.task_type,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )

            # 计算成本和统计
            cost = self.capability.estimate_cost(response.tokens_used)
            processing_time = time.time() - start_time

            return LLMResponse(
                content=response.answer,
                reasoning_content=response.reasoning,
                model_used=self.model_id,
                tokens_used=response.tokens_used,
                processing_time=processing_time,
                cost=cost,
                confidence=response.confidence,
                raw_response=response.raw_response,
            )

        except (ConnectionError, TimeoutError, ValueError) as e:
            logger.error(f"❌ DeepSeek生成失败: {e}", exc_info=True)
            return await self._mock_generate(request)
        except Exception as e:
            logger.error(f"❌ DeepSeek生成发生未预期错误: {e}", exc_info=True)
            return await self._mock_generate(request)

    async def _mock_generate(self, request: LLMRequest) -> LLMResponse:
        """
        模拟生成(用于测试或降级)

        Args:
            request: LLM请求

        Returns:
            LLMResponse: 模拟响应
        """
        logger.info("🧪 使用模拟模式生成DeepSeek响应")

        # 根据任务类型返回不同的模拟响应
        task_type = request.task_type

        if task_type in ["creativity_analysis", "novelty_analysis", "invalidation_analysis"]:
            content = f"""# {task_type.replace('_', ' ').title()}(DeepSeek模拟)

## 任务类型
{task_type}

## 输入
{request.message[:200]}...

## 分析过程
(DeepSeek推理过程模拟)

### 步骤1:理解问题
首先分析请求的核心内容...

### 步骤2:技术对比
将目标技术与现有技术进行对比...

### 步骤3:结论判断
基于分析得出结论...

## 结论
(模拟分析结论)

注:这是模拟响应。请配置DeepSeek API密钥以获取实际分析。
"""
        elif task_type == "math_reasoning":
            content = f"""# 数学推理(DeepSeek模拟)

## 问题
{request.message[:200]}

## 推理过程
(详细的推理步骤)

## 答案
(最终答案)

注:这是模拟响应。请配置DeepSeek API密钥以获取实际推理。
"""
        else:
            content = f"""# DeepSeek响应(模拟)

您的问题是: {request.message[:200]}...

(DeepSeek模拟响应)

注:这是模拟响应。请配置DeepSeek API密钥以获取实际响应。
"""

        return LLMResponse(
            content=content.strip(),
            reasoning_content="(模拟推理过程)",
            model_used=self.model_id,
            tokens_used=600,
            processing_time=0.8,
            cost=0.0,
            confidence=0.85,
        )

    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            bool: 模型是否健康可用
        """
        if self.client is None:
            return False

        try:
            # 简单测试请求
            test_response = await self.client.reason(
                problem="1+1=?", task_type="math_reasoning", max_tokens=50
            )
            return bool(test_response.answer)
        except (ConnectionError, TimeoutError) as e:
            logger.warning(f"⚠️ DeepSeek健康检查失败: {e}")
            return False
        except Exception as e:
            logger.warning(f"⚠️ DeepSeek健康检查发生未预期错误: {e}", exc_info=True)
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
            "has_client": self.client is not None,
        }
