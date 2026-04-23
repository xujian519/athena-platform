#!/usr/bin/env python3

"""
GLM-4.7-Flash LLM客户端
智谱AI GLM-4.7-Flash 模型集成

模型特点:
- 30B级SOTA模型,兼顾性能与效率
- 面向 Agentic Coding 场景强化
- 长程任务规划与工具协同能力
- 200K tokens 上下文窗口
- 采用 DeepSeek MLA 技术
- 完全开源,可在本地部署

作者: Athena AI Platform
版本: v1.0.0
创建时间: 2026-01-21
"""

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass
class GLM47FlashResponse:
    """GLM-4.7-Flash 响应对象"""

    content: str  # 生成内容
    reasoning_content: str = ""  # 推理内容(深度思考模式)
    model: str = "glm-4.7-flash"  # 使用的模型
    finish_reason: str = ""  # 结束原因
    usage: dict[[str, int]] = field(default_factory=dict)  # token使用情况
    raw_response: dict[[str, Any]] = field(default_factory=dict)  # 原始响应


@dataclass
class GLM47FlashMessage:
    """消息对象"""

    role: str  # 角色: system/user/assistant
    content: str  # 消息内容


@dataclass
class GLM47FlashThinkingConfig:
    """深度思考配置"""

    type: str = "enabled"  # enabled/auto


class GLM47FlashClient:
    """
    GLM-4.7-Flash 客户端

    支持功能:
    1. 基础对话: 单轮/多轮对话
    2. 深度思考模式: Chain of Thought 推理
    3. 流式输出: 实时返回生成内容
    4. 工具调用: Agentic 编程支持
    5. 长文本处理: 200K tokens 上下文
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://open.bigmodel.cn/api/paas/v4",
        model: str = "glm-4.7-flash",
        timeout: int = 60,
        max_tokens: int = 65536,
        temperature: float = 0.7,
    ):
        """
        初始化 GLM-4.7-Flash 客户端

        Args:
            api_key: API密钥(如果为None,从环境变量读取)
            base_url: API基础URL
            model: 模型名称
            timeout: 请求超时时间(秒)
            max_tokens: 最大生成token数
            temperature: 温度参数
        """
        # API密钥优先级: 参数 > 环境变量 > 配置文件
        if api_key is None:
            api_key = os.getenv("ZHIPUAI_API_KEY")

        if not api_key:
            logger.warning("⚠️ 未找到 ZHIPUAI_API_KEY 环境变量")
            raise ValueError(
                "请设置 ZHIPUAI_API_KEY 环境变量:\n"
                "  export ZHIPUAI_API_KEY='your-api-key'\n"
                "获取API密钥: https://open.bigmodel.cn/"
            )

        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self.default_max_tokens = max_tokens
        self.default_temperature = temperature

        logger.info(f"🤖 GLM-4.7-Flash 客户端初始化完成 (模型: {model})")

    async def chat(
        self,
        messages: list[[dict[str, str]] | GLM47FlashMessage],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: float = 0.9,
        enable_thinking: bool = True,
        thinking_type: str = "enabled",
        stream: bool = False,
    ) -> GLM47FlashResponse:
        """
        对话接口

        Args:
            messages: 消息列表
            max_tokens: 最大生成token数
            temperature: 温度参数
            top_p: top_p采样参数
            enable_thinking: 是否启用深度思考模式
            thinking_type: 思考类型 (enabled/auto)
            stream: 是否使用流式输出

        Returns:
            GLM47FlashResponse: 响应结果
        """
        # 转换消息格式
        formatted_messages = self._format_messages(messages)

        # 构建请求参数
        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "max_tokens": max_tokens or self.default_max_tokens,
            "temperature": temperature or self.default_temperature,
            "top_p": top_p,
            "stream": stream,
        }

        # 添加深度思考配置
        if enable_thinking:
            payload["thinking"]] = {"type": thinking_type}

        logger.info(f"📡 调用 GLM-4.7-Flash (深度思考: {enable_thinking})")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                response.raise_for_status()

                result = response.json()

                # 解析响应
                return self._parse_response(result)

        except httpx.HTTPStatusError as e:
            logger.error(f"❌ HTTP错误: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"❌ GLM-4.7-Flash 调用失败: {e}")
            raise

    async def chat_simple(
        self, prompt: str, system_prompt: Optional[str] = None, **kwargs
    ) -> GLM47FlashResponse:
        """
        简化的对话接口(单轮对话)

        Args:
            prompt: 用户提示
            system_prompt: 系统提示(可选)
            **kwargs: 其他参数传递给 chat()

        Returns:
            GLM47FlashResponse: 响应结果
        """
        messages = []

        if system_prompt:
            messages.append(GLM47FlashMessage(role="system", content=system_prompt))

        messages.append(GLM47FlashMessage(role="user", content=prompt))

        return await self.chat(messages, **kwargs)

    async def chat_stream(self, messages: list[[[dict[str, str]]] | GLM47FlashMessage], **kwargs):
        """
        流式对话接口

        Args:
            messages: 消息列表
            **kwargs: 其他参数

        Yields:
            str: 流式返回的内容片段
        """
        kwargs["stream"] = True
        formatted_messages = self._format_messages(messages)

        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "max_tokens": kwargs.get("max_tokens", self.default_max_tokens),
            "temperature": kwargs.get("temperature", self.default_temperature),
            "top_p": kwargs.get("top_p", 0.9),
            "stream": True,
        }

        if kwargs.get("enable_thinking", True):
            payload["thinking"]] = {"type": kwargs.get("thinking_type", "enabled")}

        logger.info("📡 GLM-4.7-Flash 流式输出...")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client, client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.strip().startswith("data: "):
                        data_str = line.strip()[6:]
                        if data_str == "[DONE]":
                            break

                        try:
                            data = json.loads(data_str)
                            delta = data.get("choices", [{}])[0].get("delta", {})

                            # 返回推理内容
                            if "reasoning_content" in delta:
                                yield delta["reasoning_content"]

                            # 返回主要内容
                            if "content" in delta:
                                yield delta["content"]

                        except json.JSONDecodeError:
                            continue

        except Exception as e:
            logger.error(f"❌ 流式输出失败: {e}")
            raise

    def _format_messages(
        self, messages: list[[dict[str, str]] | GLM47FlashMessage]
    ) -> list[dict[str, str]]:
        """格式化消息列表"""
        formatted = []
        for msg in messages:
            if isinstance(msg, dict):
                formatted.append(
                    {"role": msg.get("role", "user"), "content": msg.get("content", "")}
                )
            elif isinstance(msg, GLM47FlashMessage):
                formatted.append({"role": msg.role, "content": msg.content})
        return formatted

    def _parse_response(self, result: dict[[[str, Any]]]) -> GLM47FlashResponse:
        """解析API响应"""
        try:
            choice = result.get("choices", [{}])[0]
            message = choice.get("message", {})

            return GLM47FlashResponse(
                content=message.get("content", ""),
                reasoning_content=message.get("reasoning_content", ""),
                model=result.get("model", self.model),
                finish_reason=choice.get("finish_reason", ""),
                usage=result.get("usage", {}),
                raw_response=result,
            )
        except Exception as e:
            logger.error(f"❌ 响应解析失败: {e}")
            raise

    def get_model_info(self) -> dict[str, Any]:
        """获取模型信息"""
        return {
            "model": self.model,
            "provider": "Zhipu AI",
            "api_endpoint": self.base_url,
            "context_window": 200000,  # 200K tokens
            "max_output_tokens": self.default_max_tokens,
            "features": [
                "deep_thinking",  # 深度思考模式
                "agentic_coding",  # Agentic 编程
                "tool_calling",  # 工具调用
                "long_context",  # 长文本处理
                "streaming",  # 流式输出
            ],
            "capabilities": {
                "coding": "enhanced",
                "reasoning": "advanced",
                "planning": "optimized",
                "tools": "strong_following",
            },
        }


# ==================== 单例模式 ====================

_glm47_flash_client: Optional[GLM47FlashClient] = None


def get_glm47_flash_client() -> GLM47FlashClient:
    """获取 GLM-4.7-Flash 客户端单例"""
    global _glm47_flash_client
    if _glm47_flash_client is None:
        _glm47_flash_client = GLM47FlashClient()
    return _glm47_flash_client


# ==================== 便捷函数 ====================


async def ask_glm47_flash(
    prompt: Optional[str] = None, system_prompt: Optional[str] = None, enable_thinking: bool = True, **kwargs
) -> str:
    """
    快速提问函数

    Args:
        prompt: 用户问题
        system_prompt: 系统提示
        enable_thinking: 是否启用深度思考
        **kwargs: 其他参数

    Returns:
        str: 模型回答
    """
    client = get_glm47_flash_client()
    response = await client.chat_simple(
        prompt=prompt, system_prompt=system_prompt, enable_thinking=enable_thinking, **kwargs
    )
    return response.content


# ==================== 主程序测试 ====================


async def main():
    """测试 GLM-4.7-Flash 客户端"""
    import argparse

    parser = argparse.ArgumentParser(description="GLM-4.7-Flash 客户端测试")
    parser.add_argument("--test", action="store_true", help="运行测试")
    parser.add_argument("--prompt", default="你好,请介绍一下你自己", help="测试提示")
    parser.add_argument("--no-thinking", action="store_true", help="禁用深度思考")

    args = parser.parse_args()

    if not args.test:
        return

    client = get_glm47_flash_client()

    # 显示模型信息
    info = client.get_model_info()
    print("\n🤖 GLM-4.7-Flash 模型信息:")
    print(f"  模型: {info['model']}")
    print(f"  提供商: {info['provider']}")
    print(f"  上下文窗口: {info['context_window']:,} tokens")
    print(f"  功能特性: {', '.join(info['features'])}")
    print()

    # 运行测试
    print(f"📝 测试提示: {args.prompt}")
    print(f"🧠 深度思考: {not args.no_thinking}")
    print()

    response = await client.chat_simple(
        prompt=args.prompt,
        system_prompt="你是Athena平台的AI助手,基于智谱AI GLM-4.7-Flash模型。",
        enable_thinking=not args.no_thinking,
    )

    print("✅ 回答:")
    print(response.content)

    if response.reasoning_content:
        print("\n🧠 推理过程:")
        print(response.reasoning_content)

    print("\n📊 Token使用:")
    print(f"  {json.dumps(response.usage, indent=2, ensure_ascii=False)}")


# 入口点: @async_main装饰器已添加到main函数

