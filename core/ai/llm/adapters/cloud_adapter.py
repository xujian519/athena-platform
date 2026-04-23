"""
云端LLM适配器 - OpenAI兼容API
支持DeepSeek、通义千问、智谱GLM、Claude等云端服务
"""

import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Optional

try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None

logger = logging.getLogger(__name__)


@dataclass
class CloudLLMConfig:
    """云端LLM配置"""
    api_key: str
    base_url: str
    model: str
    timeout: int = 60
    max_retries: int = 3
    endpoint_type: str = "chat"  # chat 或 coding


class CloudLLMAdapter:
    """
    云端LLM适配器

    支持所有OpenAI兼容的API:
    - DeepSeek (https://api.deepseek.com)
    - 通义千问 (https://dashscope.aliyuncs.com/compatible-mode/v1)
    - 智谱GLM (https://open.bigmodel.cn/api/paas/v4)
    - Claude (通过SDK转换)
    """

    # 默认配置
    DEFAULT_ENDPOINTS = {
        "deepseek": {
            "base_url": "https://api.deepseek.com/v1",
            "models": {
                "chat": "deepseek-chat",
                "reasoner": "deepseek-reasoner"
            }
        },
        "qwen": {
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "models": {
                "turbo": "qwen-turbo",
                "plus": "qwen-plus",
                "max": "qwen-max"
            }
        },
        "zhipu": {
            "chat": {
                "base_url": "https://open.bigmodel.cn/api/paas/v4",
                "models": {
                    "flash": "glm-4-flash",
                    "plus": "glm-4-plus",
                    "air": "glm-4-air"
                }
            },
            "coding": {
                "base_url": "https://open.bigmodel.cn/api/coding/paas/v4",
                "models": {
                    "coding": "glm-4-flash"
                }
            }
        }
    }

    def __init__(
        self,
        provider: str = "deepseek",
        model: str = "chat",
        api_key: Optional[str] = None,
        config: Optional[CloudLLMConfig] = None,
        endpoint_type: str = "chat"  # 新增：endpoint_type参数
    ):
        """
        初始化云端LLM适配器

        Args:
            provider: 服务提供商 (deepseek, qwen, zhipu, claude)
            model: 模型名称
            api_key: API密钥（可选，默认从环境变量读取）
            config: 完整配置（可选）
            endpoint_type: 端点类型 (chat 或 coding，仅zhipu支持)
        """
        self.provider = provider
        self.endpoint_type = endpoint_type

        if config:
            self.config = config
        else:
            # 从环境变量读取API密钥
            api_key = api_key or self._get_api_key(provider)

            # 获取默认配置
            endpoint_config = self.DEFAULT_ENDPOINTS.get(provider, {})

            # 处理智谱GLM的多端点配置
            if provider == "zhipu" and isinstance(endpoint_config, dict):
                if endpoint_type in endpoint_config:
                    # 使用指定的端点类型
                    endpoint_type_config = endpoint_config[endpoint_type]
                    base_url = endpoint_type_config.get("base_url", "")
                    model_name = endpoint_type_config.get("models", {}).get(model, model)
                else:
                    # 默认使用chat端点
                    chat_config = endpoint_config.get("chat", {})
                    base_url = chat_config.get("base_url", "https://open.bigmodel.cn/api/paas/v4")
                    model_name = chat_config.get("models", {}).get(model, model)
            else:
                # 其他服务商使用单一端点
                base_url = endpoint_config.get("base_url", "")
                model_name = endpoint_config.get("models", {}).get(model, model)

            self.config = CloudLLMConfig(
                api_key=api_key,
                base_url=base_url,
                model=model_name,
                endpoint_type=endpoint_type
            )

        # 初始化客户端
        self.client: Optional[AsyncOpenAI] = None
        self._initialized = False

    def _get_api_key(self, provider: str) -> str:
        """从环境变量获取API密钥"""
        env_keys = {
            "deepseek": "DEEPSEEK_API_KEY",
            "qwen": "DASHSCOPE_API_KEY",
            "zhipu": "ZHIPU_API_KEY",
            "claude": "ANTHROPIC_API_KEY"
        }

        api_key = os.getenv(env_keys.get(provider, ""))

        if not api_key:
            # 尝试从配置文件读取
            try:
                import json
                config_path = "/Users/xujian/Athena工作平台/config/cloud_llm_config.json"
                with open(config_path) as f:
                    config = json.load(f)
                    api_key = config.get("services", {}).get(provider, {}).get("api_key", "")
                    api_key = os.path.expandvars(api_key)  # 展开环境变量
            except Exception as e:
                logger.warning(f"无法从配置文件读取API密钥: {e}")

        if not api_key:
            raise ValueError(f"无法获取{provider}的API密钥，请设置环境变量或配置文件")

        return api_key

    async def initialize(self) -> bool:
        """初始化客户端"""
        if AsyncOpenAI is None:
            logger.error("OpenAI SDK未安装，请运行: pip install openai")
            return False

        try:
            self.client = AsyncOpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries
            )

            # 测试连接
            await self._test_connection()

            self._initialized = True
            logger.info(f"✅ 云端LLM适配器初始化成功: {self.provider}/{self.config.model}")
            return True

        except Exception as e:
            logger.error(f"❌ 云端LLM适配器初始化失败: {e}")
            return False

    async def _test_connection(self):
        """测试API连接"""
        try:
            # 发送简单测试请求（响应不需要使用，只是验证连接）
            _ = await self.client.chat.completions.create(
                model=self.config.model,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=10
            )
            logger.info(f"✅ API连接测试成功: {self.provider}")
            return True
        except Exception as e:
            logger.warning(f"⚠️ API连接测试失败: {e}")
            return False

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        生成文本

        Args:
            prompt: 提示词
            temperature: 温度参数
            max_tokens: 最大token数
            system_prompt: 系统提示词

        Returns:
            生成的文本
        """
        if not self._initialized:
            await self.initialize()

        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            content = response.choices[0].message.content
            usage = response.usage

            logger.info(f"✅ 云端LLM调用成功: {self.provider}")
            logger.debug(f"  使用tokens: {usage.total_tokens}")

            return content

        except Exception as e:
            logger.error(f"❌ 云端LLM调用失败: {e}")
            raise

    async def chat(
        self,
        message: str,
        history: list[dict[str, str]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """
        对话接口

        Args:
            message: 用户消息
            history: 对话历史
            temperature: 温度参数
            max_tokens: 最大token数

        Returns:
            AI回复
        """
        if not self._initialized:
            await self.initialize()

        messages = history or []
        messages.append({"role": "user", "content": message})

        try:
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"❌ 对话失败: {e}")
            raise

    async def close(self):
        """关闭连接"""
        if self.client:
            await self.client.close()
        self._initialized = False


# 使用示例
async def example_usage():
    """使用示例"""

    # 1. DeepSeek (最便宜)
    deepseek = CloudLLMAdapter(provider="deepseek", model="chat")
    await deepseek.initialize()
    result = await deepseek.generate("分析专利CN123456789A的创造性")
    print(f"DeepSeek回复: {result}\n")
    await deepseek.close()

    # 2. 通义千问 (中文优化)
    qwen = CloudLLMAdapter(provider="qwen", model="turbo")
    await qwen.initialize()
    result = await qwen.generate("分析专利CN123456789A的创造性")
    print(f"通义千问回复: {result}\n")
    await qwen.close()

    # 3. 智谱GLM (快速响应)
    zhipu = CloudLLMAdapter(provider="zhipu", model="flash")
    await zhipu.initialize()
    result = await zhipu.generate("分析专利CN123456789A的创造性")
    print(f"智谱GLM回复: {result}\n")
    await zhipu.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
