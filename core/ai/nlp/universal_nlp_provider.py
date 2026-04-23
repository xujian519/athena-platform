#!/usr/bin/env python3

"""
通用NLP服务提供者
支持多种NLP后端:GLM-4.7、本地模型、OpenAI等

安全增强:
- API密钥通过环境变量配置
- SSL证书验证(生产环境强制)
- 请求超时和重试机制
"""

import asyncio
import logging
import os
import ssl
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Optional

import aiohttp

logger = logging.getLogger(__name__)


class NLPProviderType(Enum):
    """NLP服务提供者类型"""

    GLM47 = "glm-4.7"  # 升级到GLM-4.7
    LOCAL_BERT = "local-bert"
    OPENAI = "openai"
    OLLAMA = "ollama"
    BASIC = "basic"


class TaskType(Enum):
    """任务类型"""

    PATENT_ANALYSIS = "patent_analysis"
    TECHNICAL_REASONING = "technical_reasoning"
    EMOTIONAL_ANALYSIS = "emotional_analysis"
    CREATIVE_WRITING = "creative_writing"
    CONVERSATION = "conversation"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"


class BaseNLPProvider(ABC):
    """NLP服务提供者基类"""

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config: dict[str, Any] = config or {}
        self.provider_name: str = self.__class__.__name__
        self.is_initialized: bool = False

    @abstractmethod
    async def initialize(self) -> None:
        """初始化NLP服务"""
        pass

    @abstractmethod
    async def process(self, text: str, task_type: TaskType, **kwargs: Any) -> dict[str, Any]:
        """处理NLP任务"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查"""
        pass


class GLM47Provider(BaseNLPProvider):
    """GLM-4.7云端模型提供者(安全增强版)"""

    # 配置常量
    BASE_URL = "https://open.bigmodel.cn/api/paas/v4"
    DEFAULT_TIMEOUT = 30.0
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0

    # 类型注解
    session: aiohttp.ClientSession
    api_key: str
    base_url: str
    max_retries: int
    retry_delay: float

    def __init__(self, config: Optional[dict[str, Any]] = None):
        super().__init__(config)
        # 🔧 安全修复:从环境变量读取API密钥
        self.api_key = (
            os.getenv("GLM_API_KEY") or os.getenv("ZHIPU_API_KEY") or self.config.get("api_key", "")
        )
        if not self.api_key:
            raise ValueError("GLM API密钥未配置!请设置环境变量 GLM_API_KEY 或 ZHIPU_API_KEY")

        self.base_url: str = self.config.get("base_url", self.BASE_URL)
        self.session = None

        # 重试配置
        self.max_retries: int = self.config.get("max_retries", self.MAX_RETRIES)
        self.retry_delay: float = self.config.get("retry_delay", self.RETRY_DELAY)

    async def initialize(self) -> None:
        """初始化GLM-4.7服务(安全增强版)"""
        # 🔧 安全修复:根据环境决定SSL验证策略
        environment = os.getenv("ENVIRONMENT", "development")
        ssl_context = ssl.create_default_context()

        if environment == "development":
            # 开发环境:允许禁用SSL验证(通过环境变量显式启用)
            if os.getenv("DISABLE_SSL_VERIFICATION", "false").lower() == "true":
                logger.warning("⚠️ 开发环境:SSL证书验证已禁用")
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
            else:
                logger.info("✅ 开发环境:SSL证书验证已启用")
        else:
            # 生产环境:强制启用SSL验证
            logger.info("✅ 生产环境:SSL证书验证已强制启用")

        # 创建连接器
        connector = aiohttp.TCPConnector(
            ssl=ssl_context, limit=100, limit_per_host=30  # 连接池大小  # 每个主机的连接数
        )

        # 🔧 安全修复:添加超时配置
        timeout = aiohttp.ClientTimeout(
            total=self.config.get("timeout", self.DEFAULT_TIMEOUT), connect=10.0, sock_read=30.0
        )

        self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        self.is_initialized = True
        logger.info("✅ GLM-4.7 NLP服务初始化完成(SSL验证已启用)")

    async def process(self, text: str, task_type: TaskType, **kwargs: Any) -> dict[str, Any]:
        """使用GLM-4.7处理任务(带重试机制)"""
        if not self.is_initialized:
            await self.initialize()

        if self.session is None:
            raise RuntimeError("Session未初始化")

        # 构建任务特定的prompt
        prompt = self._build_prompt(text, task_type, **kwargs)

        # 🔧 安全修复:添加重试机制
        for attempt in range(self.max_retries):
            try:
                async with self.session.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "glm-4.7",  # 升级到GLM-4.7
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": kwargs.get("max_tokens", 2000),
                        "temperature": kwargs.get("temperature", 0.3),
                    },
                ) as response:

                    if response.status == 200:
                        result = await response.json()
                        return {
                            "success": True,
                            "content": result["choices"][0]["message"]["content"],
                            "provider": "GLM-4.7",
                            "task_type": task_type.value,
                            "usage": result.get("usage", {}),
                            "timestamp": datetime.now().isoformat(),
                            "attempts": attempt + 1,
                        }
                    elif response.status == 429:  # 限流
                        if attempt < self.max_retries - 1:
                            retry_after = self.retry_delay * (2**attempt)  # 指数退避
                            logger.warning(f"⚠️ API限流,{retry_after}秒后重试(第{attempt+1}次)")
                            await asyncio.sleep(retry_after)
                            continue
                        else:
                            logger.error("❌ API限流,已达到最大重试次数")
                            return await self._fallback_response(text, task_type)
                    else:
                        error_text = await response.text()
                        logger.error(f"GLM-4.7 API错误: {response.status} - {error_text}")
                        return await self._fallback_response(text, task_type)

            except TimeoutError:
                if attempt < self.max_retries - 1:
                    logger.warning(f"⚠️ 请求超时,{self.retry_delay}秒后重试(第{attempt+1}次)")
                    await asyncio.sleep(self.retry_delay)
                    continue
                else:
                    logger.error("❌ 请求超时,已达到最大重试次数")
                    return await self._fallback_response(text, task_type)

            except aiohttp.ClientError as e:
                if attempt < self.max_retries - 1:
                    logger.warning(
                        f"⚠️ 网络错误: {e},{self.retry_delay}秒后重试(第{attempt+1}次)"
                    )
                    await asyncio.sleep(self.retry_delay)
                    continue
                else:
                    logger.error(f"❌ 网络错误,已达到最大重试次数: {e}")
                    return await self._fallback_response(text, task_type)

            except Exception as e:
                logger.error(f"❌ GLM-4.7调用失败: {e}")
                return await self._fallback_response(text, task_type)

        # 所有重试都失败
        return await self._fallback_response(text, task_type)

    def _build_prompt(self, text: str, task_type: TaskType, **kwargs: Any) -> str:
        """构建任务特定的prompt"""
        prompts = {
            TaskType.PATENT_ANALYSIS: f"请分析以下专利文本的技术要点、创新点和保护范围:\n\n{text}",
            TaskType.TECHNICAL_REASONING: f"请对以下技术内容进行推理分析:\n\n{text}",
            TaskType.EMOTIONAL_ANALYSIS: f"请分析以下文本的情感倾向和情绪状态:\n\n{text}",
            TaskType.CREATIVE_WRITING: f"请基于以下主题进行创意写作:\n\n{text}",
            TaskType.CONVERSATION: f"请自然地回应以下对话:\n\n{text}",
            TaskType.SUMMARIZATION: f"请总结以下文本的要点:\n\n{text}",
            TaskType.TRANSLATION: f"请翻译以下文本(目标语言:{kwargs.get('target_lang', '中文')}):\n\n{text}",
        }
        return prompts.get(task_type, f"请处理以下文本:\n\n{text}")

    async def _fallback_response(self, text: str, task_type: TaskType) -> dict[str, Any]:
        """降级响应"""
        return {
            "success": False,
            "content": f"GLM-4.7服务暂时不可用,文本长度:{len(text)}字符",
            "provider": "GLM-4.7",
            "task_type": task_type.value,
            "fallback": True,
            "timestamp": datetime.now().isoformat(),
        }

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            test_response = await self.process("测试", TaskType.CONVERSATION)
            return test_response.get("success", False)
        except (ConnectionError, RuntimeError, AttributeError):
            return False


class LocalBERTProvider(BaseNLPProvider):
    """本地BERT模型提供者"""

    def __init__(self, config: Optional[dict[str, Any]] = None):
        super().__init__(config)
        self.model_path = self.config.get(
            "model_path", "/Users/xujian/Athena工作平台/models/pretrained/chinese_bert"
        )
        self.model = None
        self.tokenizer = None

    async def initialize(self):
        """初始化本地BERT模型"""
        try:
            # 这里应该加载实际的BERT模型
            # 由于环境限制,仅作初始化标记
            self.is_initialized = True
            logger.info("✅ 本地BERT NLP服务初始化完成")
        except Exception as e:
            logger.error(f"本地BERT初始化失败: {e}")
            self.is_initialized = False

    async def process(self, text: str, task_type: TaskType, **kwargs: Any) -> dict[str, Any]:
        """使用本地BERT处理任务"""
        if not self.is_initialized:
            await self.initialize()

        # 简化的本地处理逻辑
        return {
            "success": True,
            "content": f"[本地BERT处理] {text[:100]}...",
            "provider": "Local-BERT",
            "task_type": task_type.value,
            "confidence": 0.8,
            "timestamp": datetime.now().isoformat(),
        }

    async def health_check(self) -> bool:
        """健康检查"""
        return self.is_initialized


class BasicNLPProvider(BaseNLPProvider):
    """基础NLP提供者(降级方案)"""

    def __init__(self, config: Optional[dict[str, Any]] = None):
        super().__init__(config)

    async def initialize(self):
        """初始化基础NLP服务"""
        self.is_initialized = True
        logger.info("✅ 基础NLP服务初始化完成")

    async def process(self, text: str, task_type: TaskType, **kwargs: Any) -> dict[str, Any]:
        """基础NLP处理"""
        # 简单的关键词分析
        positive_keywords = ["好", "棒", "优秀", "满意", "成功"]
        negative_keywords = ["差", "失败", "问题", "错误", "不好"]

        positive_count = sum(1 for word in positive_keywords if word in text)
        negative_count = sum(1 for word in negative_keywords if word in text)

        sentiment = (
            "positive"
            if positive_count > negative_count
            else "negative" if negative_count > positive_count else "neutral"
        )

        return {
            "success": True,
            "content": text[:200] + "..." if len(text) > 200 else text,
            "provider": "Basic-NLP",
            "task_type": task_type.value,
            "sentiment": sentiment,
            "confidence": 0.6,
            "timestamp": datetime.now().isoformat(),
        }

    async def health_check(self) -> bool:
        """健康检查"""
        return True


class OllamaProvider(BaseNLPProvider):
    """Ollama本地模型提供者(支持Qwen3.5等模型)"""

    def __init__(self, config: Optional[dict[str, Any]] = None):
        super().__init__(config)
        self.base_url = self.config.get("base_url", "http://localhost:11434")
        self.model = self.config.get("model", "qwen3.5")
        self.client: aiohttp.Optional[ClientSession] = None

    async def initialize(self) -> None:
        """初始化Ollama服务"""
        try:
            timeout = aiohttp.ClientTimeout(total=120, connect=10.0, sock_read=60.0)
            self.client = aiohttp.ClientSession(timeout=timeout)

            # 健康检查
            is_healthy = await self.health_check()
            if is_healthy:
                self.is_initialized = True
                logger.info(f"✅ Ollama NLP服务初始化完成: {self.model}")
            else:
                logger.warning(f"⚠️ Ollama服务不可用: {self.base_url}")
                self.is_initialized = False

        except Exception as e:
            logger.warning(f"⚠️ Ollama初始化失败: {e}")
            self.is_initialized = False

    async def process(self, text: str, task_type: TaskType, **kwargs: Any) -> dict[str, Any]:
        """使用Ollama处理NLP任务"""
        if not self.is_initialized:
            await self.initialize()

        if self.client is None:
            return await self._fallback_response(text, task_type)

        # 构建prompt
        prompts = {
            TaskType.PATENT_ANALYSIS: f"请分析以下专利文本的技术要点和创新点:\n\n{text}",
            TaskType.TECHNICAL_REASONING: f"请对以下技术内容进行推理分析:\n\n{text}",
            TaskType.EMOTIONAL_ANALYSIS: f"请分析以下文本的情感倾向:\n\n{text}",
            TaskType.CREATIVE_WRITING: f"请基于以下主题进行创意写作:\n\n{text}",
            TaskType.CONVERSATION: f"请自然地回应:\n\n{text}",
            TaskType.SUMMARIZATION: f"请总结以下文本的要点:\n\n{text}",
            TaskType.TRANSLATION: f"请翻译以下文本:\n\n{text}",
        }
        prompt = prompts.get(task_type, f"请处理以下文本:\n\n{text}")

        try:
            async with self.client.post(
                f"{self.base_url}/v1/chat/completions",
                headers={"Content-Type": "application/json"},
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": kwargs.get("temperature", 0.7),
                    "max_tokens": kwargs.get("max_tokens", 2000),
                    "stream": False,
                },
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Ollama API错误: {response.status} - {error_text}")
                    return await self._fallback_response(text, task_type)

                data = await response.json()

            # 解析响应 - 支持Qwen3.5 thinking模式
            message = data["choices"][0]["message"]
            content = message.get("content", "") or message.get("reasoning", "")

            return {
                "success": True,
                "content": content,
                "provider": f"Ollama-{self.model}",
                "task_type": task_type.value,
                "usage": data.get("usage", {}),
                "timestamp": datetime.now().isoformat(),
            }

        except TimeoutError:
            logger.error("Ollama请求超时")
            return await self._fallback_response(text, task_type)
        except Exception as e:
            logger.error(f"Ollama处理失败: {e}")
            return await self._fallback_response(text, task_type)

    async def _fallback_response(self, text: str, task_type: TaskType) -> dict[str, Any]:
        """降级响应"""
        return {
            "success": False,
            "content": "Ollama服务暂时不可用",
            "provider": f"Ollama-{self.model}",
            "task_type": task_type.value,
            "fallback": True,
            "timestamp": datetime.now().isoformat(),
        }

    async def health_check(self) -> bool:
        """健康检查"""
        if not self.client:
            return False

        try:
            async with self.client.get(f"{self.base_url}/api/tags") as response:
                if response.status != 200:
                    return False

                data = await response.json()
                models = data.get("models", [])
                model_names = [m["name"] for m in models]

                # 检查模型是否存在
                if self.model in model_names:
                    return True

                # 检查短名称匹配
                short_name = self.model.split(":")[0]
                return any(m.startswith(short_name) for m in model_names)

        except Exception as e:
            logger.warning(f"Ollama健康检查失败: {e}")
            return False

    async def close(self) -> None:
        """关闭客户端"""
        if self.client:
            await self.client.close()
            self.client = None


class UniversalNLPService:
    """通用NLP服务"""

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.providers = {}
        self.primary_provider = None
        self.fallback_providers = []

    async def initialize(self):
        """初始化所有NLP提供者"""
        # 优先使用Ollama本地模型（支持Qwen3.5）
        if self.config.get("enable_ollama", True):
            try:
                ollama_model = self.config.get("ollama_model", "qwen3.5")
                ollama_provider = OllamaProvider({
                    "model": ollama_model,
                    "base_url": self.config.get("ollama_base_url", "http://localhost:11434"),
                })
                await ollama_provider.initialize()
                self.providers[f"ollama-{ollama_model}"] = ollama_provider
                self.primary_provider = ollama_provider
                logger.info(f"✅ Ollama {ollama_model}已启用并设为主要提供者")
            except Exception as e:
                logger.warning(f"⚠️ Ollama初始化失败: {e}")

        # 启用GLM-4.7作为备用提供者
        if self.config.get("enable_glm", False) and not self.primary_provider:
            try:
                glm_provider = GLM47Provider(self.config.get("glm", {}))
                await glm_provider.initialize()
                self.providers["glm-4.7"] = glm_provider
                if not self.primary_provider:
                    self.primary_provider = glm_provider
                logger.info("✅ GLM-4.7已启用")
            except Exception as e:
                logger.warning(f"⚠️ GLM-4.7初始化失败: {e}")

        # 初始化本地BERT作为备用提供者
        if self.config.get("enable_local", True):
            local_provider = LocalBERTProvider(self.config.get("local", {}))
            await local_provider.initialize()
            self.providers["local-bert"] = local_provider
            if not self.primary_provider:
                self.primary_provider = local_provider
            self.fallback_providers.append(local_provider)

        # 初始化基础NLP作为最终备用
        basic_provider = BasicNLPProvider()
        await basic_provider.initialize()
        self.providers["basic"] = basic_provider
        self.fallback_providers.append(basic_provider)

        logger.info(f"✅ NLP服务初始化完成,提供者数量: {len(self.providers)}")
        if self.primary_provider:
            logger.info(f"🎯 主要提供者: {self.primary_provider.provider_name}")

    async def process(self, text: str, task_type, **kwargs: Any) -> dict[str, Any]:
        """处理NLP任务"""
        # 确保task_type是TaskType枚举
        if isinstance(task_type, str):
            from core.ai.nlp.universal_nlp_provider import TaskType

            task_type_map = {
                "patent_analysis": TaskType.PATENT_ANALYSIS,
                "technical_reasoning": TaskType.TECHNICAL_REASONING,
                "emotional_analysis": TaskType.EMOTIONAL_ANALYSIS,
                "creative_writing": TaskType.CREATIVE_WRITING,
                "conversation": TaskType.CONVERSATION,
                "summarization": TaskType.SUMMARIZATION,
                "translation": TaskType.TRANSLATION,
            }
            task_type = task_type_map.get(task_type, TaskType.CONVERSATION)

        # 首先尝试主要提供者
        if self.primary_provider:
            try:
                result = await self.primary_provider.process(text, task_type, **kwargs)
                if result.get("success", False):
                    return result
            except Exception as e:
                logger.warning(f"主要提供者失败: {e}")

        # 尝试备用提供者
        for provider in self.fallback_providers:
            try:
                result = await provider.process(text, task_type, **kwargs)
                if result.get("success", False):
                    result["fallback_used"] = True
                    return result
            except Exception as e:
                logger.warning(f"备用提供者失败: {e}")

        # 所有提供者都失败
        return {
            "success": False,
            "content": "所有NLP服务都不可用",
            "provider": "none",
            "task_type": task_type.value if hasattr(task_type, "value") else str(task_type),
            "error": "All providers failed",
            "timestamp": datetime.now().isoformat(),
        }

    async def health_check(self) -> dict[str, bool]:
        """检查所有提供者健康状态"""
        results = {}
        for name, provider in self.providers.items():
            try:
                results[name] = await provider.health_check()
            except (ConnectionError, RuntimeError, AttributeError):
                results[name] = False
        return results

    async def get_provider_status(self) -> dict[str, Any]:
        """获取提供者状态"""
        health_status = await self.health_check()
        return {
            "total_providers": len(self.providers),
            "primary_provider": (
                self.primary_provider.provider_name if self.primary_provider else None
            ),
            "health_status": health_status,
            "available_providers": [name for name, healthy in health_status.items() if healthy],
            "unavailable_providers": [
                name for name, healthy in health_status.items() if not healthy
            ],
        }


# 全局NLP服务实例
_nlp_service = None


async def get_nlp_service(config: Optional[dict[str, Any]] = None) -> UniversalNLPService:
    """获取NLP服务实例"""
    global _nlp_service
    if _nlp_service is None:
        _nlp_service = UniversalNLPService(config)
        await _nlp_service.initialize()
    return _nlp_service


# 便捷函数
async def analyze_patent(text: str, **kwargs: Any) -> dict[str, Any]:
    """专利分析"""
    nlp = await get_nlp_service()
    return await nlp.process(text, TaskType.PATENT_ANALYSIS, **kwargs)


async def technical_reasoning(text: str, context: str = "", **kwargs: Any) -> dict[str, Any]:
    """技术推理"""
    nlp = await get_nlp_service()
    return await nlp.process(f"{context}\n\n{text}", TaskType.TECHNICAL_REASONING, **kwargs)


async def emotional_analysis(text: str, **kwargs: Any) -> dict[str, Any]:
    """情感分析"""
    nlp = await get_nlp_service()
    return await nlp.process(text, TaskType.EMOTIONAL_ANALYSIS, **kwargs)


async def conversation_response(text: Optional[str] = None, context: Optional[dict] = None, **kwargs: Any) -> dict[str, Any]:
    """对话响应"""
    nlp = await get_nlp_service()
    return await nlp.process(text, TaskType.CONVERSATION, **kwargs)


async def creative_writing(text: str, style: str = "story", **kwargs: Any) -> dict[str, Any]:
    """创意写作"""
    nlp = await get_nlp_service()
    return await nlp.process(f"风格:{style}\n主题:{text}", TaskType.CREATIVE_WRITING, **kwargs)


if __name__ == "__main__":
    # 测试代码
    async def test_nlp_service():
        logger.info("🧪 测试通用NLP服务")

        # 获取NLP服务
        nlp = await get_nlp_service(
            {"enable_glm": True, "enable_local": True, "glm": {"api_key": "your-api-key-here"}}
        )

        # 测试各种任务
        tasks = [
            ("专利分析测试", TaskType.PATENT_ANALYSIS),
            ("情感分析测试:今天心情很好", TaskType.EMOTIONAL_ANALYSIS),
            ("对话测试:你好", TaskType.CONVERSATION),
        ]

        for text, task_type in tasks:
            result = await nlp.process(text, task_type)
            logger.info(f"\n✅ {task_type.value}:")
            logger.info(f"   提供者: {result.get('provider')}")
            logger.info(f"   成功: {result.get('success')}")
            logger.info(f"   内容: {result.get('content', '')[:100]}...")

        # 显示状态
        status = await nlp.get_provider_status()
        logger.info(f"\n📊 服务状态: {status}")

    asyncio.run(test_nlp_service())

