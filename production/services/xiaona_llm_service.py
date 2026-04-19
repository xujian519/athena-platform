#!/usr/bin/env python3
"""
小娜LLM集成服务
支持GLM和DeepSeek API，带自动回退机制
"""

from __future__ import annotations
import logging
import os
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

try:
    import requests
    from openai import OpenAI
except ImportError:
    requests = None
    OpenAI = None

# MLX本地服务配置
MLX_BASE_URL = "http://127.0.0.1:8765"
MLX_DEFAULT_MODEL = "glm47flash"


class LLMProvider(Enum):
    """LLM提供商"""
    GLM = "glm"
    DEEPSEEK = "deepseek"
    OLLAMA = "ollama"  # 本地Ollama服务 -> 已迁移为MLX
    MLX = "mlx"  # 本地MLX服务


@dataclass
class LLMResponse:
    """LLM响应"""
    content: str
    provider: LLMProvider
    model: str
    tokens_used: int
    latency_ms: int
    success: bool
    error: str | None = None


class XiaonaLLMService:
    """小娜LLM服务 - 支持GLM和DeepSeek"""

    def __init__(self,
                 glm_api_key: str = None,
                 deepseek_api_key: str = None,
                 ollama_base_url: str = MLX_BASE_URL,
                 ollama_model: str = MLX_DEFAULT_MODEL,
                 primary: LLMProvider = LLMProvider.MLX,  # 默认使用MLX
                 fallback: LLMProvider = LLMProvider.DEEPSEEK,
                 auto_fallback: bool = True,
                 max_retries: int = 3):
        """
        初始化LLM服务

        Args:
            glm_api_key: GLM API密钥
            deepseek_api_key: DeepSeek API密钥
            ollama_base_url: Ollama服务地址
            ollama_model: Ollama模型名称
            primary: 主要LLM提供商
            fallback: 备用LLM提供商
            auto_fallback: 是否自动回退
            max_retries: 最大重试次数
        """
        self.primary = primary
        self.fallback = fallback
        self.auto_fallback = auto_fallback
        self.max_retries = max_retries
        self.ollama_base_url = ollama_base_url
        self.ollama_model = ollama_model

        # 日志 (在初始化客户端之前)
        self.logger = logging.getLogger(__name__)

        # 初始化客户端
        self.glm_client = self._init_glm_client(glm_api_key)
        self.deepseek_client = self._init_deepseek_client(deepseek_api_key)
        self.ollama_available = self._check_mlx_available()

        # 统计信息
        self.stats = {
            "glm_requests": 0,
            "glm_success": 0,
            "glm_errors": 0,
            "deepseek_requests": 0,
            "deepseek_success": 0,
            "deepseek_errors": 0,
            "ollama_requests": 0,
            "ollama_success": 0,
            "ollama_errors": 0,
            "fallback_count": 0
        }

    def _init_glm_client(self, api_key: str) -> Any:
        """初始化GLM客户端"""
        if not api_key:
            self.logger.warning("GLM API密钥未配置")
            return None

        try:
            return OpenAI(
                api_key=api_key,
                base_url="https://open.bigmodel.cn/api/paas/v4"
            )
        except Exception as e:
            self.logger.error(f"GLM客户端初始化失败: {e}")
            return None

    def _init_deepseek_client(self, api_key: str) -> Any:
        """初始化DeepSeek客户端"""
        if not api_key:
            self.logger.warning("DeepSeek API密钥未配置")
            return None

        try:
            return OpenAI(
                api_key=api_key,
                base_url="https://api.deepseek.com/v1"
            )
        except Exception as e:
            self.logger.error(f"DeepSeek客户端初始化失败: {e}")
            return None

    def _check_mlx_available(self) -> bool:
        """检查MLX服务是否可用"""
        if not requests:
            return False

        try:
            response = requests.get(f"{MLX_BASE_URL}/v1/models", timeout=2)
            if response.status_code == 200:
                data = response.json()
                models = data.get("data", [])
                model_names = [m["id"] for m in models]
                self.logger.info(f"✅ MLX服务可用，模型: {model_names}")
                return True
        except Exception as e:
            self.logger.warning(f"⚠️ MLX服务不可用: {e}")
        return False

    def generate(self,
                 system_prompt: str,
                 user_message: str,
                 provider: LLMProvider = None,
                 model: str = None,
                 max_tokens: int = 8000,
                 temperature: float = 0.3) -> LLMResponse:
        """
        生成LLM响应

        Args:
            system_prompt: 系统提示词
            user_message: 用户消息
            provider: LLM提供商 (None则使用primary)
            model: 模型名称 (None则使用默认)
            max_tokens: 最大token数
            temperature: 温度参数

        Returns:
            LLMResponse对象
        """
        provider = provider or self.primary

        # 模型配置
        model_configs = {
            LLMProvider.GLM: {
                "default": "glm-4-flash",
                "client": self.glm_client,
                "stats_key": "glm_requests"
            },
            LLMProvider.DEEPSEEK: {
                "default": "deepseek-chat",
                "client": self.deepseek_client,
                "stats_key": "deepseek_requests"
            },
            LLMProvider.OLLAMA: {
                "default": self.ollama_model,
                "client_url": self.ollama_base_url,
                "stats_key": "ollama_requests"
            },
            LLMProvider.MLX: {
                "default": self.ollama_model,
                "client_url": self.ollama_base_url,
                "stats_key": "ollama_requests"
            }
        }

        config = model_configs[provider]
        model = model or config["default"]

        # 特殊处理Ollama/MLX（使用requests而不是OpenAI客户端）
        if provider in (LLMProvider.OLLAMA, LLMProvider.MLX):
            return self._call_mlx(system_prompt, user_message, model, max_tokens, temperature)

        client = config.get("client")

        if not client:
            if provider == self.primary and self.auto_fallback:
                self.logger.warning(f"{provider.value}客户端未初始化，回退到{self.fallback.value}")
                self.stats["fallback_count"] += 1
                return self.generate(system_prompt, user_message,
                                    provider=self.fallback,
                                    model=model,
                                    max_tokens=max_tokens,
                                    temperature=temperature)
            return LLMResponse(
                content="",
                provider=provider,
                model=model,
                tokens_used=0,
                latency_ms=0,
                success=False,
                error=f"{provider.value}客户端未初始化"
            )

        # 更新统计
        self.stats[config["stats_key"]] += 1

        # 调用API
        start_time = time.time()
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )

            latency_ms = int((time.time() - start_time) * 1000)
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens

            # 更新成功统计
            success_key = "glm_success" if provider == LLMProvider.GLM else "deepseek_success"
            self.stats[success_key] += 1

            self.logger.info(f"{provider.value} 请求成功: {latency_ms}ms, {tokens_used} tokens")

            return LLMResponse(
                content=content,
                provider=provider,
                model=model,
                tokens_used=tokens_used,
                latency_ms=latency_ms,
                success=True
            )

        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            error_key = "glm_errors" if provider == LLMProvider.GLM else "deepseek_errors"
            self.stats[error_key] += 1

            self.logger.error(f"{provider.value} 请求失败: {e}")

            # 自动回退
            if provider == self.primary and self.auto_fallback:
                self.logger.info(f"回退到 {self.fallback.value}")
                self.stats["fallback_count"] += 1
                return self.generate(system_prompt, user_message,
                                    provider=self.fallback,
                                    model=model,
                                    max_tokens=max_tokens,
                                    temperature=temperature)

            return LLMResponse(
                content="",
                provider=provider,
                model=model,
                tokens_used=0,
                latency_ms=latency_ms,
                success=False,
                error=str(e)
            )

    def _call_mlx(self, system_prompt: str, user_message: str,
                       model: str, max_tokens: int, temperature: float) -> LLMResponse:
        """调用MLX API"""
        if not requests:
            return LLMResponse(
                content="",
                provider=LLMProvider.OLLAMA,
                model=model,
                tokens_used=0,
                latency_ms=0,
                success=False,
                error="requests库未安装"
            )

        if not self.ollama_available:
            # 回退到fallback
            if self.auto_fallback:
                self.logger.warning("MLX不可用，回退到fallback")
                self.stats["fallback_count"] += 1
                return self.generate(system_prompt, user_message,
                                    provider=self.fallback,
                                    model=model,
                                    max_tokens=max_tokens,
                                    temperature=temperature)
            return LLMResponse(
                content="",
                provider=LLMProvider.OLLAMA,
                model=model,
                tokens_used=0,
                latency_ms=0,
                success=False,
                error="MLX服务不可用"
            )

        self.stats["ollama_requests"] += 1
        start_time = time.time()

        try:
            base_url = self.ollama_base_url
            url = f"{base_url}/v1/chat/completions"

            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": False
            }

            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()

            latency_ms = int((time.time() - start_time) * 1000)
            data = response.json()

            content = data["choices"][0]["message"]["content"]
            tokens_used = data.get("usage", {}).get("total_tokens", 0)

            self.stats["ollama_success"] += 1
            self.logger.info(f"mlx 请求成功: {latency_ms}ms, {tokens_used} tokens")

            return LLMResponse(
                content=content,
                provider=LLMProvider.OLLAMA,
                model=model,
                tokens_used=tokens_used,
                latency_ms=latency_ms,
                success=True
            )

        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            self.stats["ollama_errors"] += 1
            self.logger.error(f"mlx 请求失败: {e}")

            # 自动回退
            if self.primary in (LLMProvider.OLLAMA, LLMProvider.MLX) and self.auto_fallback:
                self.logger.info(f"回退到 {self.fallback.value}")
                self.stats["fallback_count"] += 1
                return self.generate(system_prompt, user_message,
                                    provider=self.fallback,
                                    model=model,
                                    max_tokens=max_tokens,
                                    temperature=temperature)

            return LLMResponse(
                content="",
                provider=LLMProvider.OLLAMA,
                model=model,
                tokens_used=0,
                latency_ms=latency_ms,
                success=False,
                error=str(e)
            )

    def generate_with_retry(self,
                           system_prompt: str,
                           user_message: str,
                           provider: LLMProvider = None,
                           **kwargs) -> LLMResponse:
        """带重试的生成"""
        last_error = None

        for attempt in range(self.max_retries):
            response = self.generate(system_prompt, user_message,
                                    provider=provider, **kwargs)

            if response.success:
                return response

            last_error = response.error
            self.logger.warning(f"第{attempt + 1}次尝试失败: {last_error}")

            # 指数退避
            wait_time = 2 ** attempt
            time.sleep(wait_time)

        # 所有重试都失败
        return LLMResponse(
            content="",
            provider=provider or self.primary,
            model=kwargs.get('model', 'unknown'),
            tokens_used=0,
            latency_ms=0,
            success=False,
            error=f"重试{self.max_retries}次后仍失败: {last_error}"
        )

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        total_requests = (self.stats["glm_requests"] + self.stats["deepseek_requests"] +
                       self.stats["ollama_requests"])
        total_success = (self.stats["glm_success"] + self.stats["deepseek_success"] +
                       self.stats["ollama_success"])
        total_errors = (self.stats["glm_errors"] + self.stats["deepseek_errors"] +
                      self.stats["ollama_errors"])

        return {
            "total_requests": total_requests,
            "total_success": total_success,
            "total_errors": total_errors,
            "success_rate": total_success / total_requests if total_requests > 0 else 0,
            "fallback_count": self.stats["fallback_count"],
            "glm": {
                "requests": self.stats["glm_requests"],
                "success": self.stats["glm_success"],
                "errors": self.stats["glm_errors"],
                "success_rate": self.stats["glm_success"] / self.stats["glm_requests"] if self.stats["glm_requests"] > 0 else 0
            },
            "deepseek": {
                "requests": self.stats["deepseek_requests"],
                "success": self.stats["deepseek_success"],
                "errors": self.stats["deepseek_errors"],
                "success_rate": self.stats["deepseek_success"] / self.stats["deepseek_requests"] if self.stats["deepseek_requests"] > 0 else 0
            },
            "ollama": {
                "requests": self.stats["ollama_requests"],
                "success": self.stats["ollama_success"],
                "errors": self.stats["ollama_errors"],
                "success_rate": self.stats["ollama_success"] / self.stats["ollama_requests"] if self.stats["ollama_requests"] > 0 else 0
            }
        }

    def health_check(self) -> dict[str, bool]:
        """健康检查"""
        # 确定primary和fallback的可用性
        primary_available = False
        if self.primary == LLMProvider.GLM:
            primary_available = self.glm_client is not None
        elif self.primary == LLMProvider.DEEPSEEK:
            primary_available = self.deepseek_client is not None
        elif self.primary == LLMProvider.OLLAMA:
            primary_available = self.ollama_available
        elif self.primary == LLMProvider.MLX:
            primary_available = self.ollama_available

        fallback_available = False
        if self.fallback == LLMProvider.GLM:
            fallback_available = self.glm_client is not None
        elif self.fallback == LLMProvider.DEEPSEEK:
            fallback_available = self.deepseek_client is not None
        elif self.fallback == LLMProvider.OLLAMA:
            fallback_available = self.ollama_available
        elif self.fallback == LLMProvider.MLX:
            fallback_available = self.ollama_available

        return {
            "glm_available": self.glm_client is not None,
            "deepseek_available": self.deepseek_client is not None,
            "ollama_available": self.ollama_available,
            "mlx_available": self.ollama_available,
            "primary_available": primary_available,
            "fallback_available": fallback_available
        }


def main() -> None:
    """测试LLM服务"""

    from dotenv import load_dotenv

    # 加载环境变量
    load_dotenv("/Users/xujian/Athena工作平台/.env.production.unified")

    print("=" * 60)
    print("小娜LLM服务测试")
    print("=" * 60)

    # 初始化服务
    glm_key = os.getenv("GLM_API_KEY", "test_key")
    deepseek_key = os.getenv("DEEPSEEK_API_KEY", "test_key")

    service = XiaonaLLMService(
        glm_api_key=glm_key,
        deepseek_api_key=deepseek_key
    )

    # 健康检查
    print("\n🔍 健康检查:")
    health = service.health_check()
    for key, value in health.items():
        status = "✅" if value else "❌"
        print(f"  {status} {key}: {value}")

    # 测试生成
    print("\n🧪 测试生成 (模拟模式):")
    response = service.generate(
        system_prompt="你是小娜，专利法律AI专家",
        user_message="请简述专利法第22条",
        max_tokens=500
    )

    print(f"  提供商: {response.provider.value}")
    print(f"  模型: {response.model}")
    print(f"  成功: {response.success}")
    print(f"  延迟: {response.latency_ms}ms")
    if response.error:
        print(f"  错误: {response.error}")
    else:
        print(f"  内容长度: {len(response.content)} 字符")


if __name__ == "__main__":
    main()
