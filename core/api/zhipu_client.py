#!/usr/bin/env python3
"""
智谱AI客户端(带限流控制)
Zhipu AI Client with Rate Limiting

提供智能的API调用管理,包括:
- 自动重试和指数退避
- 并发控制
- 速率限制
- 错误处理
"""

import asyncio
import os
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from core.logging_config import setup_logging

try:
    import zhipuai

    ZHIPUAI_AVAILABLE = True
except ImportError:
    ZHIPUAI_AVAILABLE = False
    zhipuai = None

from .rate_limiter import (
    APIRateLimiter,
    BackoffStrategy,
    RateLimitConfig,
    RetryConfig,
    get_default_limiter,
    rate_limited,
)

logger = setup_logging()


class ZhipuModel(Enum):
    """智谱AI模型列表"""

    GLM_4 = "glm-4"
    GLM_4_FLASH = "glm-4-flash"
    GLM_4_AIR = "glm-4-air"
    GLM_4_PLUS = "glm-4-plus"
    GLM_3_TURBO = "glm-3-turbo"


@dataclass
class ZhipuResponse:
    """智谱AI响应"""

    content: str
    model: str
    usage: dict[str, int] = field(default_factory=dict)
    finish_reason: str | None = None
    request_id: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)

    def __str__(self) -> str:
        return f"ZhipuResponse(model={self.model}, content_length={len(self.content)})"


class ZhipuRateLimitConfig:
    """智谱AI专用限流配置"""

    # 免费版限制(保守估计)
    FREE_TIER = RateLimitConfig(
        max_concurrent=2,  # 最多2个并发
        requests_per_second=1.0,  # 每秒1个请求
        requests_per_minute=50,  # 每分钟50个请求
    )

    # 付费版限制
    PAID_TIER = RateLimitConfig(
        max_concurrent=5,  # 最多5个并发
        requests_per_second=5.0,  # 每秒5个请求
        requests_per_minute=200,  # 每分钟200个请求
    )

    # 重试配置(针对1302错误优化)
    RETRY_CONFIG = RetryConfig(
        max_retries=5,  # 最多重试5次
        base_delay=2.0,  # 基础延迟2秒
        max_delay=60.0,  # 最大延迟60秒
        backoff_strategy=BackoffStrategy.EXPONENTIAL,
        jitter=True,
        jitter_range=1.0,  # ±1秒随机抖动
        retryable_status_codes=[429, 502, 503, 504],
        retryable_error_codes=["1302", "1301", "1303"],
    )


class ZhipuClient:
    """智谱AI客户端(带限流控制)"""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "glm-4",
        rate_limit_config: RateLimitConfig | None = None,
        retry_config: RetryConfig | None = None,
        enable_rate_limit: bool = True,
    ):
        """
        Args:
            api_key: 智谱AI API密钥
            model: 默认模型
            rate_limit_config: 速率限制配置
            retry_config: 重试配置
            enable_rate_limit: 是否启用限流
        """
        if not ZHIPUAI_AVAILABLE:
            raise ImportError("请安装 zhipuai 包: pip install zhipuai")

        # API密钥
        self.api_key = api_key or os.getenv("ZHIPU_API_KEY")
        if not self.api_key:
            raise ValueError("请设置 ZHIPU_API_KEY 环境变量")

        # 初始化客户端
        self._client = zhipuai.ZhipuAI(api_key=self.api_key)
        self.model = model

        # 限流配置
        self.enable_rate_limit = enable_rate_limit
        if enable_rate_limit:
            # 根据API密钥类型选择配置
            is_paid_key = self.api_key.startswith("paid.") or len(self.api_key) > 50
            rate_limit = rate_limit_config or (
                ZhipuRateLimitConfig.PAID_TIER if is_paid_key else ZhipuRateLimitConfig.FREE_TIER
            )
            retry_config = retry_config or ZhipuRateLimitConfig.RETRY_CONFIG

            self.limiter = APIRateLimiter(
                retry_config=retry_config,
                rate_limit_config=rate_limit,
            )
        else:
            self.limiter = None

        # 统计信息
        self.call_count = 0
        self.total_tokens = 0

        logger.info(f"智谱AI客户端初始化完成 (model={model}, rate_limit={enable_rate_limit})")

    def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: int | None = None,
        **kwargs,
    ) -> ZhipuResponse:
        """
        发送聊天请求

        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            model: 模型名称
            temperature: 温度参数(0-1)
            top_p: 采样参数
            max_tokens: 最大token数
            **kwargs: 其他参数

        Returns:
            ZhipuResponse对象
        """
        model = model or self.model

        def _call_api() -> Any:
            response = self._client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
                **kwargs,
            )
            return response

        # 执行调用(带限流)
        if self.enable_rate_limit:
            response = self.limiter.sync_call_with_retry(_call_api)
        else:
            response = _call_api()

        # 解析响应
        self.call_count += 1

        return ZhipuResponse(
            content=response.choices[0].message.content,
            model=response.model,
            usage=response.usage.model_dump() if hasattr(response, "usage") else {},
            finish_reason=response.choices[0].finish_reason,
            request_id=response.id if hasattr(response, "id") else None,
        )

    async def achat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: int | None = None,
        **kwargs,
    ) -> ZhipuResponse:
        """异步聊天请求"""
        # 智谱AI SDK目前不支持原生异步,使用线程池执行
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.chat(
                messages=messages,
                model=model,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
                **kwargs,
            ),
        )

    def simple_chat(self, prompt: str, **kwargs) -> str:
        """简单聊天(单轮)"""
        messages = [{"role": "user", "content": prompt}]
        response = self.chat(messages, **kwargs)
        return response.content

    async def asimple_chat(self, prompt: str, **kwargs) -> str:
        """异步简单聊天"""
        messages = [{"role": "user", "content": prompt}]
        response = await self.achat(messages, **kwargs)
        return response.content

    def batch_chat(
        self,
        prompts: list[str],
        callback: Callable[[str, ZhipuResponse], None] | None = None,
        **kwargs,
    ) -> list[ZhipuResponse]:
        """
        批量聊天(自动控制并发)

        Args:
            prompts: 提示词列表
            callback: 回调函数 (prompt, response)
            **kwargs: 传递给chat的参数

        Returns:
            响应列表
        """
        responses = []

        for i, prompt in enumerate(prompts):
            try:
                logger.info(f"处理第 {i+1}/{len(prompts)} 个请求")
                response = self.simple_chat(prompt, **kwargs)
                responses.append(response)

                if callback:
                    callback(prompt, response)

            except Exception as e:
                logger.error(f"请求失败 ({i+1}/{len(prompts)}): {e}")
                # 可以选择继续或中断
                raise

        return responses

    async def abatch_chat(
        self,
        prompts: list[str],
        callback: Callable[[str, ZhipuResponse], None] | None = None,
        **kwargs,
    ) -> list[ZhipuResponse]:
        """异步批量聊天"""
        if not self.enable_rate_limit:
            # 未启用限流,使用简单的并发
            tasks = [self.asimple_chat(p, **kwargs) for p in prompts]
            return await asyncio.gather(*tasks)

        # 启用限流,使用信号量控制并发
        responses = []

        for i, prompt in enumerate(prompts):
            try:
                logger.info(f"处理第 {i+1}/{len(prompts)} 个请求")
                response = await self.asimple_chat(prompt, **kwargs)
                responses.append(response)

                if callback:
                    await asyncio.get_event_loop().run_in_executor(None, callback, prompt, response)

            except Exception as e:
                logger.error(f"请求失败 ({i+1}/{len(prompts)}): {e}")
                raise

        return responses

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        stats = {
            "call_count": self.call_count,
            "total_tokens": self.total_tokens,
        }

        if self.enable_rate_limit and self.limiter:
            stats["rate_limiter"] = self.limiter.get_stats()

        return stats

    def reset_stats(self) -> None:
        """重置统计信息"""
        self.call_count = 0
        self.total_tokens = 0
        if self.enable_rate_limit and self.limiter:
            self.limiter.reset_stats()


# 便捷函数
def create_zhipu_client(
    api_key: str | None = None,
    model: str = "glm-4",
    enable_rate_limit: bool = True,
) -> ZhipuClient:
    """创建智谱AI客户端"""
    return ZhipuClient(
        api_key=api_key,
        model=model,
        enable_rate_limit=enable_rate_limit,
    )


# 全局客户端实例
_default_client: ZhipuClient | None = None


def get_default_client() -> ZhipuClient:
    """获取默认客户端"""
    global _default_client
    if _default_client is None:
        _default_client = create_zhipu_client()
    return _default_client


# 便捷函数(使用默认客户端)
def chat(prompt: str, **kwargs) -> str:
    """简单聊天"""
    return get_default_client().simple_chat(prompt, **kwargs)


async def achat(prompt: str, **kwargs) -> str:
    """异步简单聊天"""
    return await get_default_client().asimple_chat(prompt, **kwargs)


if __name__ == "__main__":
    # 测试代码

    # 配置日志
    # setup_logging()  # 日志配置已移至模块导入

    async def test_batch():
        """测试批量调用"""
        client = create_zhipu_client(enable_rate_limit=True)

        prompts = [
            "什么是专利?",
            "什么是商标?",
            "什么是著作权?",
            "什么是商业秘密?",
            "什么是知识产权?",
        ]

        print("🚀 开始批量调用(带限流控制)...")
        responses = await client.abatch_chat(prompts)

        for i, (prompt, response) in enumerate(zip(prompts, responses, strict=False), 1):
            print(f"\n{i}. Q: {prompt}")
            print(f"   A: {response.content[:100]}...")

        print("\n📊 统计信息:")
        print(client.get_stats())

    # 运行测试
    asyncio.run(test_batch())
