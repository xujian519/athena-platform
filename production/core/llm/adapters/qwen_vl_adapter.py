from __future__ import annotations
"""
统一LLM层 - 通义千问视觉语言模型适配器
支持Qwen-VL-Max、Qwen-VL-Plus等视觉模型

作者: Claude Code
日期: 2026-01-27
"""

import base64
import logging
import os

from core.llm.base import DeploymentType, LLMRequest, LLMResponse, ModelCapability, ModelType

logger = logging.getLogger(__name__)


class QwenVLAdapter:
    """
    通义千问视觉语言模型适配器

    支持模型:
    - qwen-vl-max (最强视觉理解能力)
    - qwen-vl-plus (平衡性能和成本)
    - qwen-vl-v1 (轻量级视觉模型)
    """

    def __init__(self, model_id: str, capability: ModelCapability, api_key: str | None = None):
        """
        初始化Qwen-VL适配器

        Args:
            model_id: 模型ID
            capability: 模型能力定义
            api_key: 阿里云API密钥
        """
        self.model_id = model_id
        self.capability = capability
        self._api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        self._initialized = False

    async def initialize(self) -> bool:
        """
        初始化模型

        Returns:
            bool: 初始化是否成功
        """
        try:
            if not self._api_key:
                logger.warning("⚠️ 未配置DASHSCOPE_API_KEY，Qwen-VL模型将不可用")
                return False

            # 尝试导入dashscope库
            try:
                import dashscope

                dashscope.api_key = self._api_key
                self._initialized = True
                logger.info(f"✅ Qwen-VL适配器初始化成功: {self.model_id}")
                return True
            except ImportError:
                logger.warning("⚠️ dashscope库未安装，运行: pip install dashscope")
                return False

        except Exception as e:
            logger.error(f"❌ Qwen-VL适配器初始化失败: {e}")
            return False

    async def generate(
        self,
        request: LLMRequest,
        image_data: bytes | None = None,
        image_url: str | None = None,
    ) -> LLMResponse:
        """
        生成响应（支持多模态输入）

        Args:
            request: LLM请求
            image_data: 图像二进制数据
            image_url: 图像URL

        Returns:
            LLMResponse: LLM响应
        """
        if not self._initialized:
            return LLMResponse(
                content="",
                model_used=self.model_id,
                error="模型未初始化",
            )

        try:
            import time

            from dashscope import MultiModalConversation

            start_time = time.time()

            # 构建消息内容
            messages = []

            # 添加文本和图像
            if image_url:
                messages.append(
                    {
                        "role": "user",
                        "content": [
                            {"image": image_url},
                            {"text": request.message},
                        ],
                    }
                )
            elif image_data:
                # 将二进制数据转换为base64
                base64_image = base64.b64encode(image_data).decode("utf-8")
                messages.append(
                    {
                        "role": "user",
                        "content": [
                            {"image": f"data:image/jpeg;base64,{base64_image}"},
                            {"text": request.message},
                        ],
                    }
                )
            else:
                # 纯文本模式
                messages.append(
                    {
                        "role": "user",
                        "content": [{"text": request.message}],
                    }
                )

            # 调用API
            response = await MultiModalConversation.call(
                model=self.model_id,
                messages=messages,
            )

            processing_time = time.time() - start_time

            # 检查响应状态
            if response.status_code != 200:
                logger.error(f"❌ Qwen-VL API错误: {response.message}")
                return LLMResponse(
                    content="",
                    model_used=self.model_id,
                    error=response.message,
                )

            # 提取响应内容
            content_text = response.output.choices[0].message.content[0].text or ""
            tokens_used = response.usage.total_tokens if hasattr(response, "usage") else 0

            # 计算成本
            cost = self.capability.estimate_cost(tokens_used)

            return LLMResponse(
                content=content_text,
                model_used=self.model_id,
                tokens_used=tokens_used,
                processing_time=processing_time,
                cost=cost,
                quality_score=self.capability.quality_score,
                confidence=0.88,
                raw_response=response.__dict__ if hasattr(response, "__dict__") else {},
            )

        except Exception as e:
            logger.error(f"❌ Qwen-VL生成失败: {e}")
            return LLMResponse(
                content="",
                model_used=self.model_id,
                error=str(e),
            )

    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            bool: 模型是否健康可用
        """
        if not self._initialized:
            return False

        try:
            from dashscope import MultiModalConversation

            response = await MultiModalConversation.call(
                model=self.model_id,
                messages=[{"role": "user", "content": [{"text": "ping"}]}],
            )
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"⚠️ Qwen-VL健康检查失败: {e}")
            return False

    async def get_stats(self) -> dict:
        """
        获取统计信息

        Returns:
            dict: 统计信息字典
        """
        return {
            "model_id": self.model_id,
            "model_type": self.capability.model_type.value,
            "deployment": self.capability.deployment.value,
            "initialized": self._initialized,
            "supports_vision": True,
            "max_context": self.capability.max_context,
        }

    def is_initialized(self) -> bool:
        """检查是否已初始化"""
        return self._initialized


# 预定义的Qwen-VL模型能力
QWEN_VL_MODELS = {
    "qwen-vl-max": ModelCapability(
        model_id="qwen-vl-max",
        model_type=ModelType.MULTIMODAL,
        deployment=DeploymentType.CLOUD,
        max_context=30000,
        supports_streaming=True,
        supports_function_call=False,
        supports_vision=True,
        supports_thinking=False,
        avg_latency_ms=2000,
        throughput_tps=60,
        cost_per_1k_tokens=0.02,  # 约¥0.02/1K tokens
        quality_score=0.94,
        suitable_tasks=[
            "image_analysis",
            "multimodal",
            "chart_analysis",
            "document_analysis",
            "ocr",
            "visual_reasoning",
        ],
        unsuitable_tasks=[],
    ),
    "qwen-vl-plus": ModelCapability(
        model_id="qwen-vl-plus",
        model_type=ModelType.MULTIMODAL,
        deployment=DeploymentType.CLOUD,
        max_context=30000,
        supports_streaming=True,
        supports_function_call=False,
        supports_vision=True,
        supports_thinking=False,
        avg_latency_ms=1200,
        throughput_tps=90,
        cost_per_1k_tokens=0.008,  # 约¥0.008/1K tokens
        quality_score=0.90,
        suitable_tasks=[
            "image_analysis",
            "multimodal",
            "simple_visual_qa",
        ],
        unsuitable_tasks=[],
    ),
}


def create_qwen_vl_adapter(model_id: str | None = None,
    api_key: str | None = None) -> QwenVLAdapter:
    """
    创建Qwen-VL适配器的便捷函数

    Args:
        model_id: 模型ID
        api_key: 阿里云API密钥

    Returns:
        QwenVLAdapter: 适配器实例
    """
    capability = QWEN_VL_MODELS.get(model_id)
    if not capability:
        raise ValueError(f"不支持的模型: {model_id}")

    return QwenVLAdapter(model_id, capability, api_key)
