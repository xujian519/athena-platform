#!/usr/bin/env python3
"""
本地8009端口LLM适配器
支持LM Studio/Ollama等本地服务

Author: Athena平台团队
创建时间: 2026-04-22
"""

import logging

import aiohttp
from typing import Optional

logger = logging.getLogger(__name__)


class Local8009Adapter:
    """
    本地8009端口LLM适配器

    支持LM Studio、Ollama等OpenAI兼容的本地服务
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8009",
        api_key: str = "xj781102@",
        model: str = "gemma-4-e2b-it-4bit",  # 默认使用gemma（多模态+快速）
        timeout: int = 180,
    ):
        """
        初始化本地8009适配器

        Args:
            base_url: 服务地址
            api_key: API密钥
            model: 模型名称
            timeout: 超时时间（秒）
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.client: aiohttp.Optional[ClientSession] = None
        self._initialized = False

        logger.info(f"🔧 本地8009适配器初始化: {model} @ {base_url}")

    async def initialize(self) -> bool:
        """
        初始化适配器

        Returns:
            是否初始化成功
        """
        try:
            # 创建HTTP客户端
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.client = aiohttp.ClientSession(timeout=timeout)

            # 健康检查
            is_healthy = await self.health_check()

            if is_healthy:
                self._initialized = True
                logger.info(f"✅ 本地8009适配器初始化成功: {self.model}")
            else:
                logger.warning(f"⚠️ 本地8009服务不可用: {self.base_url}")
                self._initialized = False

            return self._initialized

        except Exception as e:
            logger.warning(f"⚠️ 本地8009适配器初始化失败: {e}")
            self._initialized = False
            return False

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """
        生成响应

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            temperature: 温度参数
            max_tokens: 最大token数

        Returns:
            生成的文本
        """
        if not self._initialized:
            raise RuntimeError("本地8009适配器未初始化")

        try:
            # 构建消息
            messages = []
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            messages.append({
                "role": "user",
                "content": prompt
            })

            # 构建请求头
            headers = {
                "Content-Type": "application/json",
            }
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            # 调用API
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False,
            }

            async with self.client.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                headers=headers,
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"本地8009 API错误: {response.status} - {error_text}")
                    raise RuntimeError(f"API调用失败: {response.status} - {error_text}")

                data = await response.json()

            # 解析响应
            content = data["choices"][0]["message"]["content"]
            tokens_used = data.get("usage", {}).get("total_tokens", 0)

            logger.info(f"✅ 本地8009生成完成: {tokens_used} tokens")

            return content

        except TimeoutError:
            logger.error("本地8009请求超时")
            raise RuntimeError("请求超时")
        except Exception as e:
            logger.error(f"本地8009生成失败: {e}", exc_info=True)
            raise

    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            服务是否可用
        """
        if not self.client:
            return False

        try:
            # 检查服务是否运行
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            async with self.client.get(
                f"{self.base_url}/v1/models",
                headers=headers,
            ) as response:
                if response.status != 200:
                    return False

                data = await response.json()

                # 检查模型是否存在
                models = data.get("data", [])
                model_ids = [m.get("id", "") for m in models]

                # 检查完整模型名或短名称
                if self.model in model_ids:
                    return True

                # 检查短名称匹配
                short_name = self.model.split(":")[0]
                return any(m.startswith(short_name) for m in model_ids)

        except Exception as e:
            logger.warning(f"本地8009健康检查失败: {e}")
            return False

    async def close(self):
        """关闭客户端"""
        if self.client:
            await self.client.close()
            self.client = None
            logger.info("🔌 本地8009适配器已关闭")


# 单例
_local_8009_adapter: Optional[Local8009Adapter] = None


async def get_local_8009_adapter() -> Local8009Adapter:
    """
    获取本地8009适配器单例

    Returns:
        本地8009适配器
    """
    global _local_8009_adapter

    if _local_8009_adapter is None:
        _local_8009_adapter = Local8009Adapter()
        await _local_8009_adapter.initialize()

    return _local_8009_adapter
