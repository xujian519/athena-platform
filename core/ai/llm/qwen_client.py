
"""
统一LLM层 - Qwen(通义千问)云端模型客户端
支持Qwen-Max、Qwen-Plus、Qwen-Turbo等模型

作者: Claude Code
日期: 2026-01-23
"""

import logging
from dataclasses import dataclass
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class QwenResponse:
    """Qwen响应"""

    content: str
    model: str
    tokens_used: int
    raw_response: dict[str, Any]
class QwenClient:
    """
    Qwen(通义千问)客户端

    支持阿里云通义千问系列模型
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
        model: str = "qwen-plus",
        timeout: int = 60,
    ):
        """
        初始化Qwen客户端

        Args:
            api_key: API密钥(如果为None,从环境变量读取)
            base_url: API基础URL
            model: 模型名称 (qwen-plus, qwen-max, qwen-turbo)
            timeout: 请求超时时间(秒)
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.timeout = timeout

        # 如果没有提供api_key,尝试从环境变量读取
        if not self.api_key:
            import os

            self.api_key = os.getenv("DASHSCOPE_API_KEY")

        if not self.api_key:
            logger.warning("⚠️ 未找到DASHSCOPE_API_KEY,将使用模拟模式")
            self.mock_mode = True
        else:
            self.mock_mode = False

        # 导入OpenAI兼容客户端
        try:
            from openai import AsyncOpenAI

            self.client = AsyncOpenAI(
                api_key=self.api_key, base_url=self.base_url, timeout=self.timeout
            )
        except ImportError:
            logger.warning("⚠️ OpenAI SDK未安装,请运行: pip install openai")
            self.mock_mode = True

        logger.info(f"✅ Qwen客户端初始化完成 (模型: {model}, 模拟模式: {self.mock_mode})")

    async def chat(
        self, messages: list[dict[str, str], temperature: float = 0.7, max_tokens: int = 2000
    ) -> dict[str, Any]:
        """
        对话接口

        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大tokens数

        Returns:
            Dict: 响应内容
        """
        if self.mock_mode:
            return await self._mock_chat(messages, temperature, max_tokens)

        try:
            response = await self.client.chat.completions.create(
                model=self.model, messages=messages, temperature=temperature, max_tokens=max_tokens
            )

            return {
                "content": response.choices[0].message.content,
                "usage": {
                    "total_tokens": response.usage.total_tokens,
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                },
                "model": response.model,
            }
        except Exception as e:
            logger.error(f"❌ Qwen调用失败: {e}")
            raise

    async def _mock_chat(
        self, messages: list[dict[str, str], temperature: float, max_tokens: int
    ) -> dict[str, Any]:
        """模拟对话(用于测试)"""
        user_message = messages[-1].get("content", "") if messages else ""

        return {
            "content": f"""# Qwen响应(模拟)

您的问题是: {user_message[:200]}...

这是Qwen(通义千问)的模拟响应。

要使用真实的Qwen API,请设置DASHSCOPE_API_KEY环境变量。

注:这是模拟响应,仅供测试。
""",
            "usage": {"total_tokens": 500, "prompt_tokens": 300, "completion_tokens": 200},
            "model": self.model,
        }

    async def reason(
        self,
        problem: str,
        task_type: str = "reasoning",
        temperature: float = 0.1,
        max_tokens: int = 4000,
    ) -> QwenResponse:
        """
        推理接口

        Args:
            problem: 待推理的问题
            task_type: 任务类型
            temperature: 温度参数
            max_tokens: 最大tokens数

        Returns:
            QwenResponse: 推理结果
        """
        messages = [
            {"role": "system", "content": "你是一个专业的AI助手,擅长逻辑推理和问题分析。"},
            {"role": "user", "content": problem},
        ]

        response_dict = await self.chat(messages, temperature, max_tokens)

        return QwenResponse(
            content=response_dict["content"],
            model=response_dict["model"],
            tokens_used=response_dict["usage"]["total_tokens"],
            raw_response=response_dict,
        )

    def get_model_info(self) -> dict[str, Any]:
        """获取模型信息"""
        model_info = {
            "qwen-plus": {
                "name": "Qwen Plus",
                "max_context": 32000,
                "description": "通义千问Plus模型,适合日常对话和分析",
            },
            "qwen-max": {
                "name": "Qwen Max",
                "max_context": 32000,
                "description": "通义千问Max模型,高质量推理和分析",
            },
            "qwen-turbo": {
                "name": "Qwen Turbo",
                "max_context": 8192,
                "description": "通义千问Turbo模型,快速响应",
            },
        }
        return model_info.get(self.model, {"name": "Unknown", "max_context": 0, "description": ""})

