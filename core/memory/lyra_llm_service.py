#!/usr/bin/env python3
"""
Lyra LLM服务集成
Lyra LLM Service Integration for Athena Platform

为Lyra提示词优化引擎提供统一的LLM服务接口
支持多种LLM提供者：Ollama、智谱、DeepSeek、OpenAI、Anthropic

作者: 小诺·双鱼公主 v1.0
创建时间: 2026-02-06
"""

import asyncio
import json
import logging
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import aiohttp

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """LLM提供者"""
    OLLAMA = "ollama"
    ZHIPU = "zhipu"
    DEEPSEEK = "deepseek"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


@dataclass
class LLMRequest:
    """LLM请求"""
    prompt: str
    system_message: Optional[str] = None
    temperature: float = 0.3
    max_tokens: int = 2000
    top_p: float = 0.9
    top_k: int = 40


@dataclass
class LLMResponse:
    """LLM响应"""
    content: str
    provider: str
    model: str
    tokens_used: int = 0
    response_time: float = 0.0
    cached: bool = False
    success: bool = True
    error: Optional[str] = None


class LyraLLMConfig:
    """Lyra LLM配置管理器"""

    CONFIG_PATH = Path("/Users/xujian/Athena工作平台/config/lyra_llm_config.json")

    def __init__(self):
        """初始化配置"""
        self.config: dict[str, Any] = {}
        self._load_config()

    def _load_config(self):
        """加载配置文件"""
        try:
            if self.CONFIG_PATH.exists():
                with open(self.CONFIG_PATH, encoding='utf-8') as f:
                    self.config = json.load(f)
                logger.info(f"✅ 已加载Lyra LLM配置: {self.CONFIG_PATH}")
            else:
                logger.warning(f"⚠️ 配置文件不存在，使用默认配置: {self.CONFIG_PATH}")
                self.config = self._get_default_config()
        except json.JSONDecodeError as e:
            logger.error(f"❌ 配置文件JSON格式错误: {e}")
            self.config = self._get_default_config()
        except Exception as e:
            logger.error(f"❌ 加载配置失败: {e}")
            self.config = self._get_default_config()

    def _get_default_config(self) -> dict[str, Any]:
        """获取默认配置"""
        return {
            "default_provider": "ollama",
            "fallback_providers": ["zhipu"],
            "providers": {
                "ollama": {
                    "enabled": True,
                    "base_url": "http://localhost:11434",
                    "models": {"default": "qwen:7b"},
                    "parameters": {"temperature": 0.3, "num_predict": 2048}
                },
                "zhipu": {
                    "enabled": True,
                    "base_url": "https://open.bigmodel.cn/api/paas/v4/",
                    "models": {"default": "glm-4"},
                    "api_key": os.getenv("ZHIPU_API_KEY", "")
                }
            },
            "fallback": {
                "enabled": True,
                "fallback_to_rules": True
            }
        }

    def get_provider_config(self, provider: LLMProvider) -> dict[str, Any]:
        """获取提供者配置"""
        provider_key = provider.value
        providers = self.config.get("providers", {})
        return providers.get(provider_key, {})

    def get_default_provider(self) -> LLMProvider:
        """获取默认提供者"""
        default = self.config.get("default_provider", "ollama")
        try:
            return LLMProvider(default)
        except ValueError:
            return LLMProvider.OLLAMA

    def get_fallback_providers(self) -> list[LLMProvider]:
        """获取备用提供者列表"""
        fallbacks = self.config.get("fallback_providers", [])
        providers = []
        for f in fallbacks:
            try:
                providers.append(LLMProvider(f))
            except ValueError:
                pass
        return providers

    def get_model_for_provider(self, provider: LLMProvider, model_type: str = "default") -> str:
        """获取提供者的模型"""
        config = self.get_provider_config(provider)
        models = config.get("models", {})
        return models.get(model_type, models.get("default", "qwen:7b"))

    def get_parameters_for_profile(self, profile: str) -> dict[str, Any]:
        """获取优化配置文件的参数"""
        profiles = self.config.get("optimization_profiles", {})
        return profiles.get(profile, {
            "temperature": 0.3,
            "max_tokens": 2000
        })

    def is_provider_enabled(self, provider: LLMProvider) -> bool:
        """检查提供者是否启用"""
        config = self.get_provider_config(provider)
        return config.get("enabled", False)

    def is_fallback_enabled(self) -> bool:
        """检查是否启用降级"""
        fallback = self.config.get("fallback", {})
        return fallback.get("enabled", True)


class LyraLLMService:
    """Lyra LLM服务 - 统一的LLM调用接口"""

    def __init__(self, config: Optional[LyraLLMConfig] = None):
        """初始化LLM服务"""
        self.config = config or LyraLLMConfig()
        self.default_provider = self.config.get_default_provider()
        self.fallback_providers = self.config.get_fallback_providers()
        self._cache: dict[str, LLMResponse] = {}
        logger.info(f"✅ Lyra LLM服务初始化完成 (默认: {self.default_provider.value})")

    async def generate(self, request: LLMRequest, provider: Optional[LLMProvider] = None) -> LLMResponse:
        """
        生成LLM响应

        Args:
            request: LLM请求
            provider: 指定提供者（可选）

        Returns:
            LLM响应
        """
        import time
        start_time = time.time()

        # 确定提供者
        target_provider = provider or self.default_provider

        # 检查缓存
        cache_key = self._get_cache_key(request, target_provider)
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            logger.info(f"🎯 缓存命中: {cache_key[:20]}...")
            return cached

        # 尝试调用
        providers_to_try = [target_provider] + self.fallback_providers
        last_error = None

        for prov in providers_to_try:
            if not self.config.is_provider_enabled(prov):
                continue

            try:
                logger.info(f"📞 调用 {prov.value}...")
                response = await self._call_provider(prov, request)
                response.response_time = (time.time() - start_time) * 1000

                # 缓存成功响应
                if response.success:
                    self._cache[cache_key] = response

                return response

            except Exception as e:
                last_error = e
                logger.warning(f"⚠️ {prov.value} 调用失败: {e}")
                continue

        # 所有提供者都失败
        if self.config.is_fallback_enabled():
            logger.warning("🔄 所有LLM提供者失败，返回错误响应")
            return LLMResponse(
                content=f"LLM服务暂时不可用",
                provider="none",
                model="fallback",
                success=False,
                error=str(last_error),
                response_time=(time.time() - start_time) * 1000
            )

        raise last_error or Exception("LLM服务不可用")

    async def _call_provider(self, provider: LLMProvider, request: LLMRequest) -> LLMResponse:
        """调用指定提供者"""
        if provider == LLMProvider.OLLAMA:
            return await self._call_ollama(request)
        elif provider == LLMProvider.ZHIPU:
            return await self._call_zhipu(request)
        elif provider == LLMProvider.DEEPSEEK:
            return await self._call_deepseek(request)
        elif provider == LLMProvider.OPENAI:
            return await self._call_openai(request)
        elif provider == LLMProvider.ANTHROPIC:
            return await self._call_anthropic(request)
        else:
            raise ValueError(f"不支持的提供者: {provider}")

    async def _call_ollama(self, request: LLMRequest) -> LLMResponse:
        """调用Ollama API"""
        config = self.config.get_provider_config(LLMProvider.OLLAMA)
        base_url = config.get("base_url", "http://localhost:11434")
        model = self.config.get_model_for_provider(LLMProvider.OLLAMA)
        params = config.get("parameters", {})

        # 构建完整提示
        full_prompt = request.prompt
        if request.system_message:
            full_prompt = f"{request.system_message}\n\n{request.prompt}"

        payload = {
            "model": model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": request.temperature or params.get("temperature", 0.3),
                "top_p": request.top_p or params.get("top_p", 0.9),
                "top_k": request.top_k or params.get("top_k", 40),
                "num_predict": request.max_tokens or params.get("num_predict", 2048)
            }
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{base_url}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return LLMResponse(
                        content=data.get("response", ""),
                        provider="ollama",
                        model=model,
                        tokens_used=data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
                        success=True
                    )
                else:
                    error_text = await response.text()
                    raise Exception(f"Ollama API错误 {response.status}: {error_text}")

    async def _call_zhipu(self, request: LLMRequest) -> LLMResponse:
        """调用智谱AI API"""
        config = self.config.get_provider_config(LLMProvider.ZHIPU)
        api_key = config.get("api_key", "")
        base_url = config.get("base_url", "https://open.bigmodel.cn/api/paas/v4/")
        model = self.config.get_model_for_provider(LLMProvider.ZHIPU)

        if not api_key:
            raise Exception("智谱API密钥未配置")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        messages = []
        if request.system_message:
            messages.append({"role": "system", "content": request.system_message})
        messages.append({"role": "user", "content": request.prompt})

        payload = {
            "model": model,
            "messages": messages,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "max_tokens": request.max_tokens
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{base_url}chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data["choices"][0]["message"]["content"]
                    return LLMResponse(
                        content=content,
                        provider="zhipu",
                        model=model,
                        tokens_used=data.get("usage", {}).get("total_tokens", 0),
                        success=True
                    )
                else:
                    error_text = await response.text()
                    raise Exception(f"智谱API错误 {response.status}: {error_text}")

    async def _call_deepseek(self, request: LLMRequest) -> LLMResponse:
        """调用DeepSeek API（兼容OpenAI格式）"""
        config = self.config.get_provider_config(LLMProvider.DEEPSEEK)
        api_key = config.get("api_key", "")
        base_url = config.get("base_url", "https://api.deepseek.com/v1")
        model = self.config.get_model_for_provider(LLMProvider.DEEPSEEK)

        if not api_key:
            raise Exception("DeepSeek API密钥未配置")

        return await self._call_openai_format(base_url, api_key, model, request, "deepseek")

    async def _call_openai(self, request: LLMRequest) -> LLMResponse:
        """调用OpenAI API"""
        config = self.config.get_provider_config(LLMProvider.OPENAI)
        api_key = config.get("api_key", "")
        base_url = config.get("base_url", "https://api.openai.com/v1")
        model = self.config.get_model_for_provider(LLMProvider.OPENAI)

        if not api_key:
            raise Exception("OpenAI API密钥未配置")

        return await self._call_openai_format(base_url, api_key, model, request, "openai")

    async def _call_anthropic(self, request: LLMRequest) -> LLMResponse:
        """调用Anthropic Claude API"""
        config = self.config.get_provider_config(LLMProvider.ANTHROPIC)
        api_key = config.get("api_key", "")
        base_url = config.get("base_url", "https://api.anthropic.com/v1")
        model = self.config.get_model_for_provider(LLMProvider.ANTHROPIC)

        if not api_key:
            raise Exception("Anthropic API密钥未配置")

        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "messages": [{"role": "user", "content": request.prompt}]
        }

        if request.system_message:
            payload["system"] = request.system_message

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{base_url}/messages",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data["content"][0]["text"]
                    return LLMResponse(
                        content=content,
                        provider="anthropic",
                        model=model,
                        tokens_used=data.get("usage", {}).get("input_tokens", 0) + data.get("usage", {}).get("output_tokens", 0),
                        success=True
                    )
                else:
                    error_text = await response.text()
                    raise Exception(f"Anthropic API错误 {response.status}: {error_text}")

    async def _call_openai_format(self, base_url: str, api_key: str, model: str,
                                   request: LLMRequest, provider_name: str) -> LLMResponse:
        """调用OpenAI格式的API"""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        messages = []
        if request.system_message:
            messages.append({"role": "system", "content": request.system_message})
        messages.append({"role": "user", "content": request.prompt})

        payload = {
            "model": model,
            "messages": messages,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "max_tokens": request.max_tokens
        }

        logger.info(f"📤 发送请求到 {provider_name}: {base_url}/chat/completions")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    logger.info(f"📥 收到响应状态: {response.status}")

                    if response.status == 200:
                        data = await response.json()
                        content = data["choices"][0]["message"]["content"]
                        logger.info(f"✅ {provider_name} 调用成功，内容长度: {len(content)}")
                        return LLMResponse(
                            content=content,
                            provider=provider_name,
                            model=model,
                            tokens_used=data.get("usage", {}).get("total_tokens", 0),
                            success=True
                        )
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ {provider_name} API错误 {response.status}: {error_text}")
                        raise Exception(f"{provider_name.upper()} API错误 {response.status}: {error_text}")
        except aiohttp.ClientError as e:
            logger.error(f"❌ {provider_name} 网络错误: {e}")
            raise Exception(f"{provider_name.upper()} 网络错误: {e}")
        except Exception as e:
            logger.error(f"❌ {provider_name} 未知错误: {e}")
            raise

    def _get_cache_key(self, request: LLMRequest, provider: LLMProvider) -> str:
        """生成缓存键"""
        import hashlib
        content = f"{request.prompt}:{request.temperature}:{request.max_tokens}:{provider.value}"
        return hashlib.md5(content.encode('utf-8'), usedforsecurity=False).hexdigest()

    def clear_cache(self) -> None:
        """清空缓存"""
        self._cache.clear()
        logger.info("LLM缓存已清空")

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "default_provider": self.default_provider.value,
            "fallback_providers": [p.value for p in self.fallback_providers],
            "cache_size": len(self._cache),
            "config_path": str(self.config.CONFIG_PATH)
        }


# 全局实例
_lyra_llm_service: Optional[LyraLLMService] = None


def get_lyra_llm_service() -> LyraLLMService:
    """获取Lyra LLM服务实例"""
    global _lyra_llm_service
    if _lyra_llm_service is None:
        _lyra_llm_service = LyraLLMService()
    return _lyra_llm_service


if __name__ == "__main__":
    # 测试LLM服务
    async def test():
        print("🧪 Lyra LLM服务测试")
        print("=" * 50)

        service = get_lyra_llm_service()

        # 显示统计信息
        stats = service.get_stats()
        print(f"默认提供者: {stats['default_provider']}")
        print(f"备用提供者: {stats['fallback_providers']}")
        print(f"配置路径: {stats['config_path']}")

        # 测试请求
        request = LLMRequest(
            prompt="你好，请简单介绍一下你自己。",
            temperature=0.7,
            max_tokens=200
        )

        print("\n📞 测试LLM调用...")
        try:
            response = await service.generate(request)
            if response.success:
                print(f"✅ 调用成功")
                print(f"提供者: {response.provider}")
                print(f"模型: {response.model}")
                print(f"响应: {response.content[:100]}...")
                print(f"耗时: {response.response_time:.2f}ms")
            else:
                print(f"❌ 调用失败: {response.error}")
        except Exception as e:
            print(f"❌ 测试失败: {e}")

    asyncio.run(test())
