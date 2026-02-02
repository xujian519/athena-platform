#!/usr/bin/env python3
"""
Athena统一LLM服务(增强版)
支持本地GGUF模型和云端API

作者: 小诺·双鱼公主 v4.0
创建时间: 2025-01-09
"""

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from core.logging_config import setup_logging

logger = setup_logging()


class LLMProvider(Enum):
    """LLM提供者"""

    LOCAL_GGUF = "local_gguf"  # 本地GGUF模型
    GLM_4 = "glm_4"  # 智谱GLM-4
    OPENAI = "openai"  # OpenAI API


@dataclass
class LLMRequest:
    """LLM请求"""

    prompt: str
    system_message: str | None = None
    temperature: float = 0.7
    max_tokens: int = 2000
    model: str | None = None
    provider: LLMProvider | None = None
    enable_cache: bool = True


@dataclass
class LLMResponse:
    """LLM响应"""

    content: str
    model: str
    provider: str
    tokens_used: int = 0
    cached: bool = False
    response_time: float = 0.0
    confidence: float = 0.0


class AthenaLLMService:
    """Athena统一LLM服务(增强版)"""

    def __init__(self, config: dict[str, Any] | None = None):
        """
        初始化LLM服务

        Args:
            config: 服务配置
        """
        self.config = config or {}
        self._cache = {}
        self._stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "local_calls": 0,
            "api_calls": 0,
        }

        # 默认提供者
        self.default_provider = LLMProvider.LOCAL_GGUF
        self.fallback_provider = LLMProvider.GLM_4

        # 本地模型管理
        self.local_model_loaded = False
        self.local_model_adapter = None

        logger.info("✅ Athena LLM服务初始化完成")
        logger.info(f"   默认提供者: {self.default_provider.value}")
        logger.info(f"   备用提供者: {self.fallback_provider.value}")

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

        # 确定提供者
        provider = request.provider or self.default_provider

        # 检查缓存
        if request.enable_cache:
            cache_key = self._get_cache_key(request)
            if cache_key in self._cache:
                self._stats["cache_hits"] += 1
                cached_response = self._cache[cache_key]
                logger.info(f"🎯 缓存命中: {cache_key[:20]}...")
                return LLMResponse(
                    content=cached_response["content"],
                    model=cached_response["model"],
                    provider=cached_response["provider"],
                    cached=True,
                    response_time=(time.time() - start_time) * 1000,
                    confidence=cached_response.get("confidence", 0.8),
                )

        # 调用LLM
        try:
            if provider == LLMProvider.LOCAL_GGUF:
                response = await self._call_local_gguf(request)
                self._stats["local_calls"] += 1
            else:
                response = await self._call_cloud_api(request, provider)
                self._stats["api_calls"] += 1

            response.response_time = (time.time() - start_time) * 1000

            # 缓存结果
            if request.enable_cache:
                cache_key = self._get_cache_key(request)
                self._cache[cache_key] = {
                    "content": response.content,
                    "model": response.model,
                    "provider": response.provider,
                    "confidence": response.confidence,
                }

            return response

        except Exception as e:
            logger.error(f"❌ LLM调用失败 ({provider.value}): {e}")

            # 尝试备用提供者
            if provider != self.fallback_provider:
                logger.info(f"🔄 尝试备用提供者: {self.fallback_provider.value}")
                request.provider = self.fallback_provider
                return await self.generate(request)

            # 最终降级
            return LLMResponse(
                content=f"LLM服务暂时不可用: {e!s}",
                model="fallback",
                provider="none",
                confidence=0.0,
            )

    async def _call_local_gguf(self, request: LLMRequest) -> LLMResponse:
        """
        调用本地GGUF模型

        Args:
            request: LLM请求

        Returns:
            LLM响应
        """
        try:
            # 动态导入GGUF适配器
            from core.models.gguf_model_adapter import get_gguf_manager
            from core.models.model_registry import get_model_registry

            # 获取模型注册中心
            registry = get_model_registry()

            # 确定模型ID
            model_id = request.model or "qwen2.5-14b-instruct-q4_k_m"

            # 获取模型配置
            model_config = registry.get_model_config(model_id)
            if not model_config:
                raise ValueError(f"模型未注册: {model_id}")

            # 获取GGUF管理器
            manager = get_gguf_manager()
            adapter = manager.get_adapter(model_id)

            # 如果模型未加载,先加载
            if adapter is None:
                logger.info(f"📦 正在加载模型: {model_id}")

                # 转换配置
                config = {
                    "n_ctx": model_config.n_ctx,
                    "n_batch": model_config.n_batch,
                    "n_threads": model_config.n_threads,
                    "gpu_layers": model_config.gpu_layers,
                    "use_mmap": model_config.use_mmap,
                    "use_mlock": model_config.use_mlock,
                    "temperature": model_config.temperature,
                    "top_p": model_config.top_p,
                    "top_k": model_config.top_k,
                    "repeat_penalty": model_config.repeat_penalty,
                }

                # 加载模型
                success = await manager.load_model(model_id, model_config.model_path, config)
                if not success:
                    raise RuntimeError(f"模型加载失败: {model_id}")

                adapter = manager.get_adapter(model_id)
                registry.update_model_status(model_id, registry.ModelStatus.LOADED)

            # 构建提示
            full_prompt = request.prompt
            if request.system_message:
                full_prompt = f"{request.system_message}\n\n{request.prompt}"

            # 生成
            result = await adapter.generate(
                prompt=full_prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
            )

            return LLMResponse(
                content=result.text,
                model=model_id,
                provider=LLMProvider.LOCAL_GGUF.value,
                tokens_used=result.tokens_used,
                confidence=0.85,
            )

        except ImportError as e:
            logger.error(f"❌ llama-cpp-python未安装: {e}")
            logger.error("   请运行: pip install llama-cpp-python")
            raise
        except Exception as e:
            logger.error(f"❌ 本地GGUF调用失败: {e}")
            raise

    async def _call_cloud_api(self, request: LLMRequest, provider: LLMProvider) -> LLMResponse:
        """
        调用云端API

        Args:
            request: LLM请求
            provider: 云端提供者

        Returns:
            LLM响应
        """
        try:
            # 使用现有LLM接口
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
                    provider=provider.value,
                    tokens_used=core_response.usage.get("total_tokens", 0),
                    cached=core_response.usage.get("cache_hit", False),
                    confidence=core_response.confidence_score,
                )

        except Exception as e:
            logger.error(f"❌ 云端API调用失败: {e}")
            raise

    def _get_cache_key(self, request: LLMRequest) -> str:
        """生成缓存键"""
        import hashlib

        content = f"{request.prompt}:{request.temperature}:{request.max_tokens}:{request.provider}"
        return hashlib.md5(content.encode('utf-8'), usedforsecurity=False).hexdigest()

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        total = self._stats["total_requests"]
        hits = self._stats["cache_hits"]
        cache_hit_rate = hits / total if total > 0 else 0

        return {
            "total_requests": total,
            "cache_hits": hits,
            "local_calls": self._stats["local_calls"],
            "api_calls": self._stats["api_calls"],
            "cache_hit_rate": f"{cache_hit_rate:.2%}",
            "cache_size": len(self._cache),
            "default_provider": self.default_provider.value,
        }

    def clear_cache(self) -> None:
        """清空缓存"""
        self._cache.clear()
        logger.info("LLM缓存已清空")

    def set_default_provider(self, provider: LLMProvider) -> None:
        """
        设置默认提供者

        Args:
            provider: LLM提供者
        """
        self.default_provider = provider
        logger.info(f"✅ 默认提供者已设置为: {provider.value}")


# 全局服务实例
_llm_service: AthenaLLMService | None = None


def get_athena_llm_service(config: dict[str, Any] | None = None) -> AthenaLLMService:
    """获取Athena LLM服务实例"""
    global _llm_service
    if _llm_service is None:
        _llm_service = AthenaLLMService(config)
    return _llm_service


if __name__ == "__main__":
    # 测试Athena LLM服务
    async def test():
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

        # 注册模型
        from core.models.model_registry import register_preset_models

        register_preset_models()

        # 获取服务
        service = get_athena_llm_service()

        # 测试请求
        request = LLMRequest(
            prompt="你好,请简单介绍一下你自己。",
            temperature=0.7,
            max_tokens=200,
            provider=LLMProvider.LOCAL_GGUF,
        )

        print("\n🤖 Athena LLM服务测试")
        print("=" * 80)

        response = await service.generate(request)

        print(f"\n提供者: {response.provider}")
        print(f"模型: {response.model}")
        print(f"响应:\n{response.content}")
        print("\n统计:")
        print(f"  Tokens: {response.tokens_used}")
        print(f"  耗时: {response.response_time:.2f}ms")
        print(f"  缓存: {'是' if response.cached else '否'}")
        print(f"  置信度: {response.confidence:.2f}")

        # 全局统计
        stats = service.get_stats()
        print("\n📊 全局统计:")
        for key, value in stats.items():
            print(f"  {key}: {value}")

    asyncio.run(test())
