#!/usr/bin/env python3
"""
统一LLM服务
Unified LLM Service

整合所有LLM调用,提供统一的接口

作者: 小诺·双鱼公主 v4.0
创建时间: 2025-12-25
版本: 1.0.0
"""

from __future__ import annotations
import asyncio
import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class LLMRequest:
    """LLM请求"""

    prompt: str
    system_message: str | None = None
    temperature: float = 0.7
    max_tokens: int = 2000
    model: str | None = None
    enable_cache: bool = True


@dataclass
class LLMResponse:
    """LLM响应"""

    content: str
    model: str
    tokens_used: int = 0
    cached: bool = False
    response_time: float = 0.0
    confidence: float = 0.0


class LLMService:
    """统一LLM服务"""

    def __init__(self, config=None):
        self.config = config
        self._cache = {}
        self._stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "api_calls": 0,
        }

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        生成LLM响应

        Args:
            request: LLM请求

        Returns:
            LLMResponse: LLM响应
        """
        import time

        start_time = time.time()
        self._stats["total_requests"] += 1

        # 检查缓存
        if request.enable_cache:
            cache_key = self._get_cache_key(request)
            if cache_key in self._cache:
                self._stats["cache_hits"] += 1
                cached_response = self._cache[cache_key]
                logger.info(f"缓存命中: {cache_key[:20]}...")
                return LLMResponse(
                    content=cached_response["content"],
                    model=cached_response["model"],
                    cached=True,
                    response_time=(time.time() - start_time) * 1000,
                )

        # 调用LLM
        self._stats["api_calls"] += 1
        response = await self._call_llm(request)
        response.response_time = (time.time() - start_time) * 1000

        # 缓存结果
        if request.enable_cache:
            self._cache[cache_key] = {
                "content": response.content,
                "model": response.model,
            }

        return response

    async def _call_llm(self, request: LLMRequest) -> LLMResponse:
        """调用实际的LLM"""
        try:
            # 使用GLM-4
            from core.cognition.llm_interface import LLMInterface
            from core.cognition.llm_interface import LLMRequest as CoreLLMRequest

            async with LLMInterface() as llm:
                core_request = CoreLLMRequest(
                    prompt=request.prompt,
                    system_message=request.system_message,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                    model_name=request.model,
                )

                core_response = await llm.call_llm(core_request)

                return LLMResponse(
                    content=core_response.content,
                    model=core_response.model_used,
                    tokens_used=core_response.usage.get("total_tokens", 0),
                    cached=core_response.usage.get("cache_hit", False),
                    confidence=core_response.confidence_score,
                )

        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            # 降级到简单响应
            return LLMResponse(
                content=f"LLM服务暂时不可用: {e!s}",
                model="fallback",
                confidence=0.0,
            )

    def _get_cache_key(self, request: LLMRequest) -> str:
        """生成缓存键"""
        import hashlib

        content = f"{request.prompt}:{request.temperature}:{request.max_tokens}"
        return hashlib.md5(content.encode('utf-8'), usedforsecurity=False).hexdigest()

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        total = self._stats["total_requests"]
        hits = self._stats["cache_hits"]
        cache_hit_rate = hits / total if total > 0 else 0

        return {
            "total_requests": total,
            "cache_hits": hits,
            "api_calls": self._stats["api_calls"],
            "cache_hit_rate": f"{cache_hit_rate:.2%}",
            "cache_size": len(self._cache),
        }

    def clear_cache(self) -> None:
        """清空缓存"""
        self._cache.clear()
        logger.info("LLM缓存已清空")


# 全局服务实例
_llm_service: LLMService | None = None


def get_llm_service(config=None) -> LLMService:
    """获取LLM服务实例"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService(config)
    return _llm_service


if __name__ == "__main__":
    # 测试LLM服务
    async def test():
        service = get_llm_service()

        request = LLMRequest(
            prompt="你好,请简单介绍一下你自己。",
            temperature=0.7,
            max_tokens=500,
        )

        response = await service.generate(request)

        print("🤖 LLM服务测试")
        print("=" * 60)
        print(f"模型: {response.model}")
        print(f"响应: {response.content}")
        print(f"耗时: {response.response_time:.2f}ms")
        print(f"缓存: {'是' if response.cached else '否'}")
        print()
        print("📊 统计:")
        stats = service.get_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")

    asyncio.run(test())
