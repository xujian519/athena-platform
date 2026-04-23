#!/usr/bin/env python3
"""
外部AI模型集成
External AI Models Integration

集成多种外部AI模型，包括OpenAI、Google AI、Claude等

作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

import asyncio
import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)

class AIProvider(Enum):
    """AI服务提供商"""
    OPENAI = 'openai'
    GOOGLE = 'google'
    ANTHROPIC = 'anthropic'
    HUGGING_FACE = 'hugging_face'
    OLLAMA = 'ollama'
    AZURE_OPENAI = 'azure_openai'
    LOCAL = 'local'

class ModelType(Enum):
    """模型类型"""
    TEXT_GENERATION = 'text_generation'
    TEXT_COMPLETION = 'text_completion'
    EMBEDDING = 'embedding'
    CHAT = 'chat'
    INSTRUCTION_FOLLOWING = 'instruction_following'
    CODE_GENERATION = 'code_generation'
    SUMMARIZATION = 'summarization'
    TRANSLATION = 'translation'
    QUESTION_ANSWERING = 'question_answering'

@dataclass
class AIModel:
    """AI模型配置"""
    provider: AIProvider
    model_name: str
    model_type: ModelType
    api_key: str | None = None
    api_base: str | None = None
    max_tokens: int = 4096
    temperature: float = 0.7
    top_p: float = 0.9
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    custom_params: dict[str, Any] = field(default_factory=dict)

@dataclass
class ModelRequest:
    """模型请求"""
    model: AIModel
    prompt: str
    context: dict[str, Any] | None = None
    stream: bool = False
    system_prompt: str | None = None
    examples: list[dict[str, str] = field(default_factory=list)

@dataclass
class ModelResponse:
    """模型响应"""
    request_id: str
    model_name: str
    provider: str
    content: str
    usage: dict[str, int] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    latency: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

class OpenAIIntegration:
    """OpenAI集成"""

    def __init__(self, api_key: str | None = None, api_base: str = 'https://api.openai.com/v1'):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.api_base = api_base
        self.headers = {
            'Authorization': f"Bearer {self.api_key}",
            'Content-Type': 'application/json'
        }

    async def generate_response(self, request: ModelRequest) -> ModelResponse:
        """生成响应"""
        start_time = time.time()
        request_id = f"openai_{int(time.time() * 1000)}"

        url = f"{self.api_base}/chat/completions"

        payload = {
            'model': request.model.model_name,
            'messages': [
                {'role': 'system', 'content': request.system_prompt or 'You are a helpful assistant.'},
                {'role': 'user', 'content': request.prompt}
            ],
            'max_tokens': request.model.max_tokens,
            'temperature': request.model.temperature,
            'top_p': request.model.top_p,
            'stream': request.stream
        }

        # 添加示例
        for example in request.examples:
            payload['messages'].append({
                'role': 'assistant',
                'content': example['assistant']
            })
            payload['messages'].append({
                'role': 'user',
                'content': example['user']
            })

        # 添加自定义参数
        payload.update(request.model.custom_params)

        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                if request.stream:
                    content = ''
                    response = await session.post(url, json=payload)
                    response.raise_for_status()

                    # 流式响应处理（简化版）
                    async for line in response.content:
                        if line:
                            content += line.decode()

                    return ModelResponse(
                        request_id=request_id,
                        model_name=request.model.model_name,
                        provider='openai',
                        content=content,
                        latency=time.time() - start_time
                    )
                else:
                    async with session.post(url, json=payload) as response:
                        response.raise_for_status()
                        data = await response.json()

                        content = data['choices'][0]['message']['content']
                        usage = data.get('usage')

                        return ModelResponse(
                            request_id=request_id,
                            model_name=request.model.model_name,
                            provider='openai',
                            content=content,
                            usage=usage,
                            latency=time.time() - start_time
                        )

            except Exception as e:
                logger.error(f"OpenAI API调用失败: {e}")
                raise

class GoogleAIIntegration:
    """Google AI集成"""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv('GOOGLE_AI_API_KEY')
        self.api_url = 'https://generativelanguage.googleapis.com/v1beta/models'

    async def generate_response(self, request: ModelRequest) -> ModelResponse:
        """生成响应"""
        start_time = time.time()
        request_id = f"google_{int(time.time() * 1000)}"

        url = f"{self.api_url}/{request.model.model_name}:generateContent"

        payload = {
            'contents': [{
                'parts': [{'text': request.prompt}]
            }],
            'generationConfig': {
                'maxOutputTokens': request.model.max_tokens,
                'temperature': request.model.temperature,
                'topP': request.model.top_p
            }
        }

        headers = {
            'Content-Type': 'application/json',
            'x-goog-api-key': self.api_key
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                async with session.post(url, json=payload) as response:
                    response.raise_for_status()
                    data = await response.json()

                    content = data['candidates'][0]['content']['parts'][0]['text']

                    return ModelResponse(
                        request_id=request_id,
                        model_name=request.model.model_name,
                        provider='google',
                        content=content,
                        latency=time.time() - start_time
                    )

            except Exception as e:
                logger.error(f"Google AI API调用失败: {e}")
                raise

class AnthropicIntegration:
    """Anthropic Claude集成"""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        self.api_url = 'https://api.anthropic.com/v1/messages'

    async def generate_response(self, request: ModelRequest) -> ModelResponse:
        """生成响应"""
        start_time = time.time()
        request_id = f"anthropic_{int(time.time() * 1000)}"

        headers = {
            'x-api-key': self.api_key,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json'
        }

        payload = {
            'model': request.model.model_name,
            'max_tokens': request.model.max_tokens,
            'temperature': request.model.temperature,
            'messages': [
                {
                    'role': 'user',
                    'content': request.prompt
                }
            ]
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                async with session.post(self.api_url, json=payload) as response:
                    response.raise_for_status()
                    data = await response.json()

                    content = data['content'][0]['text']

                    return ModelResponse(
                        request_id=request_id,
                        model_name=request.model.model_name,
                        provider='anthropic',
                        content=content,
                        latency=time.time() - start_time
                    )

            except Exception as e:
                logger.error(f"Anthropic API调用失败: {e}")
                raise

class HuggingFaceIntegration:
    """Hugging Face模型集成"""

    def __init__(self, api_token: str | None = None):
        self.api_token = api_token or os.getenv('HUGGINGFACE_API_TOKEN')
        self.api_url = 'https://api-inference.huggingface.co/models'

    async def generate_response(self, request: ModelRequest) -> ModelResponse:
        """生成响应"""
        start_time = time.time()
        request_id = f"huggingface_{int(time.time() * 1000)}"

        url = f"{self.api_url}/{request.model.model_name}"

        headers = {
            'Authorization': f"Bearer {self.api_token}",
            'Content-Type': 'application/json'
        }

        payload = {
            'inputs': request.prompt,
            'parameters': {
                'max_new_tokens': request.model.max_tokens,
                'temperature': request.model.temperature,
                'top_p': request.model.top_p,
                'do_sample': True
            }
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                async with session.post(url, json=payload) as response:
                    response.raise_for_status()
                    data = await response.json()

                    # 处理不同模型返回格式
                    if isinstance(data, list):
                        content = data[0].get('generated_text', '')
                    else:
                        content = data.get('generated_text', '')

                    return ModelResponse(
                        request_id=request_id,
                        model_name=request.model.model_name,
                        provider='hugging_face',
                        content=content,
                        latency=time.time() - start_time
                    )

            except Exception as e:
                logger.error(f"Hugging Face API调用失败: {e}")
                raise

class OllamaIntegration:
    """Ollama本地模型集成"""

    def __init__(self, base_url: str = 'http://localhost:11434'):
        self.base_url = base_url

    async def generate_response(self, request: ModelRequest) -> ModelResponse:
        """生成响应"""
        start_time = time.time()
        request_id = f"ollama_{int(time.time() * 1000)}"

        url = f"{self.base_url}/api/generate"

        payload = {
            'model': request.model.model_name,
            'prompt': request.prompt,
            'stream': request.stream,
            'options': {
                'temperature': request.model.temperature,
                'top_p': request.model.top_p,
                'num_predict': request.model.max_tokens
            }
        }

        async with aiohttp.ClientSession() as session:
            try:
                if request.stream:
                    content = ''
                    async with session.post(url, json=payload) as response:
                        response.raise_for_status()

                        # 简化的流式处理
                        async for line in response.content:
                            if line:
                                try:
                                    data = json.loads(line.decode())
                                    if 'response' in data:
                                        content += data['response']
                                except:
                                    pass

                    return ModelResponse(
                        request_id=request_id,
                        model_name=request.model.model_name,
                        provider='ollama',
                        content=content,
                        latency=time.time() - start_time
                    )
                else:
                    async with session.post(url, json=payload) as response:
                        response.raise_for_status()
                        data = await response.json()

                        content = data['response']

                        return ModelResponse(
                            request_id=request_id,
                            model_name=request.model.model_name,
                            provider='ollama',
                            content=content,
                            latency=time.time() - start_time
                        )

            except Exception as e:
                logger.error(f"Ollama API调用失败: {e}")
                raise

class ExternalAIManager:
    """外部AI管理器"""

    def __init__(self):
        self.integrations = {
            AIProvider.OPENAI: OpenAIIntegration(),
            AIProvider.GOOGLE: GoogleAIIntegration(),
            AIProvider.ANTHROPIC: AnthropicIntegration(),
            AIProvider.HUGGING_FACE: HuggingFaceIntegration(),
            AIProvider.OLLAMA: OllamaIntegration()
        }

        # 模型配置
        self.available_models = self._initialize_models()

        # 使用统计
        self.usage_stats = {
            'total_requests': 0,
            'by_provider': defaultdict(int),
            'by_model': defaultdict(int),
            'total_latency': 0.0,
            'error_count': 0
        }

        # 响应缓存
        self.response_cache = {}
        self.cache_ttl = 300  # 5分钟

    def _initialize_models(self) -> dict[str, list[AIModel]:
        """初始化可用模型"""
        models = {
            'openai': [
                AIModel(AIProvider.OPENAI, 'gpt-4', ModelType.CHAT),
                AIModel(AIProvider.OPENAI, 'gpt-3.5-turbo', ModelType.CHAT),
                AIModel(AIProvider.OPENAI, 'text-davinci-003', ModelType.TEXT_GENERATION),
            ],
            'google': [
                AIModel(AIProvider.GOOGLE, 'gemini-pro', ModelType.CHAT),
                AIModel(AIProvider.GOOGLE, 'gemini-pro-vision', ModelType.CHAT),
            ],
            'anthropic': [
                AIModel(AIProvider.ANTHROPIC, 'claude-3-opus-20240229', ModelType.CHAT),
                AIModel(AIProvider.ANTHROPIC, 'claude-3-sonnet-20240229', ModelType.CHAT),
            ],
            'hugging_face': [
                AIModel(AIProvider.HUGGING_FACE, 'microsoft/DialoGPT-medium', ModelType.CHAT),
                AIModel(AIProvider.HUGGING_FACE, 'bigscience/bloom', ModelType.TEXT_GENERATION),
            ],
            'ollama': [
                AIModel(AIProvider.OLLAMA, 'llama2', ModelType.CHAT),
                AIModel(AIProvider.OLLAMA, 'codellama', ModelType.CODE_GENERATION),
                AIModel(AIProvider.OLLAMA, 'mistral', ModelType.CHAT),
            ]
        }

        return models

    def get_available_models(self, provider: AIProvider | None = None) -> dict[str, list[AIModel]:
        """获取可用模型"""
        if provider:
            return {provider.value: self.available_models.get(provider.value, [])}
        return self.available_models

    def add_custom_model(self, model: AIModel):
        """添加自定义模型"""
        provider_key = model.provider.value
        if provider_key not in self.available_models:
            self.available_models[provider_key] = []

        # 检查是否已存在
        existing = [m for m in self.available_models[provider_key]
                   if m.model_name == model.model_name]
        if not existing:
            self.available_models[provider_key].append(model)
            logger.info(f"添加自定义模型: {model.provider.value}/{model.model_name}")

    async def generate_response(self,
                              provider: AIProvider,
                              model_name: str,
                              prompt: str,
                              **kwargs) -> ModelResponse:
        """生成响应"""
        # 检查缓存
        cache_key = self._get_cache_key(provider, model_name, prompt)
        cached_response = self._get_cached_response(cache_key)
        if cached_response:
            self.usage_stats['total_requests'] += 1
            return cached_response

        # 查找模型
        models = self.available_models.get(provider.value, [])
        model = next((m for m in models if m.model_name == model_name), None)

        if not model:
            raise ValueError(f"未找到模型: {provider.value}/{model_name}")

        # 创建请求
        request = ModelRequest(
            model=model,
            prompt=prompt,
            **kwargs
        )

        time.time()

        try:
            # 调用相应的集成
            integration = self.integrations[provider]
            response = await integration.generate_response(request)

            # 更新统计
            self._update_stats(provider, response.latency)

            # 缓存响应
            self._cache_response(cache_key, response)

            return response

        except Exception as e:
            self.usage_stats['error_count'] += 1
            logger.error(f"生成响应失败 [{provider.value}]: {e}")
            raise

    def _get_cache_key(self, provider: AIProvider, model_name: str, prompt: str) -> str:
        """获取缓存键"""
        content = f"{provider.value}:{model_name}:{prompt}"
        return hashlib.md5(content.encode('utf-8'), usedforsecurity=False).hexdigest()

    def _get_cached_response(self, cache_key: str) -> ModelResponse | None:
        """获取缓存的响应"""
        if cache_key in self.response_cache:
            cached_time, response = self.response_cache[cache_key]
            if time.time() - cached_time < self.cache_ttl:
                return response
            else:
                del self.response_cache[cache_key]
        return None

    def _cache_response(self, cache_key: str, response: ModelResponse):
        """缓存响应"""
        self.response_cache[cache_key] = (time.time(), response)

        # 清理过期缓存
        current_time = time.time()
        expired_keys = [
            k for k, (t, _) in self.response_cache.items()
            if current_time - t > self.cache_ttl
        ]
        for key in expired_keys:
            del self.response_cache[key]

    def _update_stats(self, provider: AIProvider, latency: float):
        """更新使用统计"""
        self.usage_stats['total_requests'] += 1
        self.usage_stats['by_provider'][provider.value] += 1
        self.usage_stats['total_latency'] += latency

    def get_usage_stats(self) -> dict[str, Any]:
        """获取使用统计"""
        return {
            'total_requests': self.usage_stats['total_requests'],
            'by_provider': dict(self.usage_stats['by_provider']),
            'by_model': dict(self.usage_stats['by_model']),
            'average_latency': (
                self.usage_stats['total_latency'] /
                max(self.usage_stats['total_requests'], 1)
            ),
            'error_rate': (
                self.usage_stats['error_count'] /
                max(self.usage_stats['total_requests'], 1)
            ),
            'cache_size': len(self.response_cache)
        }

    async def generate_with_fallback(self,
                                    providers: list[AIProvider],
                                    model_name: str,
                                    prompt: str,
                                    **kwargs) -> ModelResponse:
        """使用多个提供商的备用机制"""
        errors = []

        for provider in providers:
            try:
                return await self.generate_response(provider, model_name, prompt, **kwargs)
            except Exception as e:
                errors.append(f"{provider.value}: {str(e)}")
                logger.warning(f"提供商 {provider.value} 失败，尝试下一个")
                continue

        # 所有提供商都失败
        error_msg = f"所有AI提供商都失败: {'; '.join(errors)}"
        logger.error(error_msg)
        raise Exception(error_msg)

    async def analyze_patent_content(self,
                                     content: str,
                                     analysis_type: str = 'general',
                                     preferred_provider: AIProvider | None = None) -> dict[str, Any]:
        """分析专利内容"""
        providers = [preferred_provider] if preferred_provider else [
            AIProvider.OPENAI,
            AIProvider.GOOGLE,
            AIProvider.ANTHROPIC
        ]

        # 构建分析提示
        system_prompt = f"""
你是一个专业的专利分析师。请分析以下专利内容，重点关注{analysis_type}方面。

分析要求：
1. 识别技术方案的核心创新点
2. 评估专利的新颖性和创造性
3. 分析技术实施的可行性
4. 识别潜在的技术风险
5. 提供改进建议

请提供结构化的分析结果，包括：
- 创新性评分 (0-100)
- 创造性评分 (0-100)
- 实用性评分 (0-100)
- 技术风险等级
- 关键要点分析
- 改进建议

内容:
"""

        prompt = f"""
专利内容:
{content}
"""

        try:
            response = await self.generate_with_fallback(
                providers=providers,
                model_name='gpt-4',
                prompt=prompt,
                system_prompt=system_prompt
            )

            # 解析响应（简化版）
            analysis = {
                'provider': response.provider,
                'model': response.model_name,
                'response': response.content,
                'analysis_type': analysis_type,
                'timestamp': response.timestamp.isoformat(),
                'latency': response.latency
            }

            return analysis

        except Exception as e:
            logger.error(f"专利内容分析失败: {e}")
            return {'error': str(e), 'analysis_type': analysis_type}

    async def translate_patent_text(self,
                                    text: str,
                                    target_language: str = 'en',
                                    preferred_provider: AIProvider | None = None) -> str:
        """翻译专利文本"""
        providers = [preferred_provider] if preferred_provider else [
            AIProvider.GOOGLE,
            AIProvider.OPENAI,
            AIProvider.HUGGING_FACE
        ]

        prompt = f"""
请将以下专利相关文本翻译为{target_language}，保持技术术语的准确性：

原文:
{text}

要求：
1. 保持原文的技术含义
2. 专利术语使用标准翻译
3. 保持文本结构和格式
4. 确保翻译的准确性和流畅性

请只返回翻译结果，不要添加其他说明。
"""

        try:
            response = await self.generate_with_fallback(
                providers=providers,
                model_name='gpt-4',
                prompt=prompt
            )

            return response.content.strip()

        except Exception as e:
            logger.error(f"专利文本翻译失败: {e}")
            return text  # 返回原文

    async def summarize_patent(self,
                             patent_data: dict[str, Any],
                             summary_type: str = 'technical',
                             preferred_provider: AIProvider | None = None) -> str:
        """生成专利摘要"""
        providers = [preferred_provider] if preferred_provider else [
            AIProvider.OPENAI,
            AIProvider.GOOGLE,
            AIProvider.ANTHROPIC
        ]

        # 提取专利信息
        title = patent_data.get('title', '')
        abstract = patent_data.get('abstract', '')
        claims = patent_data.get('claims', '')[:2000]  # 限制长度

        prompt = f"""
请为以下专利生成{summary_type}摘要：

专利标题: {title}
摘要: {abstract}
权利要求: {claims}

要求：
1. 准确概括技术方案的核心内容
2. 突出创新点和关键技术特征
3. 说明技术效果和应用领域
4. 保持专业性和准确性
5. 摘要长度控制在200-500字

请生成简洁、专业的专利摘要：
"""

        try:
            response = await self.generate_with_fallback(
                providers=providers,
                model_name='gpt-4',
                prompt=prompt
            )

            return response.content.strip()

        except Exception as e:
            logger.error(f"专利摘要生成失败: {e}")
            return abstract[:200]  # 返回摘要的前200字符

# 测试用例
async def main():
    """主函数"""
    logger.info('🧠 外部AI模型集成测试')
    logger.info(str('='*50))

    # 创建AI管理器
    ai_manager = ExternalAIManager()

    # 获取可用模型
    logger.info("\n📋 可用模型:")
    for provider, models in ai_manager.get_available_models().items():
        logger.info(f"\n{provider}:")
        for model in models[:3]:  # 只显示前3个
            logger.info(f"  - {model.model_name} ({model.model_type.value})")

    # 测试专利内容分析
    logger.info("\n📝 测试专利内容分析...")
    patent_content = """
    本发明提供一种基于深度学习的智能图像识别系统，包括：
    1. 图像预处理模块，用于对输入图像进行标准化和增强处理；
    2. 特征提取模块，使用卷积神经网络提取图像特征；
    3. 分类模块，通过全连接层实现图像分类；
    4. 输出模块，生成分类结果和置信度。

    该系统具有高精度、实时性强的特点，可广泛应用于安防、医疗等领域。
    """

    analysis = await ai_manager.analyze_patent_content(
        content=patent_content,
        analysis_type='技术创新性'
    )

    logger.info(f"\n分析结果提供商: {analysis['provider']}")
    logger.info(f"分析响应长度: {len(analysis['response'])} 字符")

    # 测试文本翻译
    logger.info("\n🌐 测试文本翻译...")
    chinese_text = '本发明涉及一种新型的数据处理方法'
    translated = await ai_manager.translate_patent_text(
        text=chinese_text,
        target_language='English'
    )
    logger.info(f"原文: {chinese_text}")
    logger.info(f"译文: {translated}")

    # 测试专利摘要
    logger.info("\n📄 测试专利摘要...")
    patent_data = {
        'title': '基于区块链的分布式数据存储系统',
        'abstract': '本发明提供一种基于区块链技术的分布式数据存储方案，通过智能合约实现数据的去中心化存储和访问控制。',
        'claims': '1. 一种基于区块链的分布式数据存储系统，其特征在于包括：区块链网络，用于记录数据交易；智能合约模块，用于定义数据访问规则；分布式存储节点，用于存储数据块；共识模块，用于维护网络一致性。'
    }

    summary = await ai_manager.summarize_patent(
        patent_data=patent_data,
        summary_type='技术要点'
    )
    logger.info(f"\n摘要长度: {len(summary)} 字符")
    logger.info(f"摘要内容: {summary[:100]}...")

    # 获取使用统计
    logger.info("\n📊 AI模型使用统计:")
    stats = ai_manager.get_usage_stats()
    for key, value in stats.items():
        logger.info(f"  {key}: {value}")

    logger.info("\n✅ 外部AI模型集成测试完成！")

if __name__ == '__main__':
    # 设置模拟环境变量
    import os
    os.environ['OPENAI_API_KEY'] = 'test-key'
    os.environ['GOOGLE_AI_API_KEY'] = 'test-key'
    os.environ['ANTHROPIC_API_KEY'] = 'test-key'
    os.environ['HUGGINGFACE_API_TOKEN'] = 'test-token'

    # 使用模拟的HTTP客户端

    import aiohttp

    original_post = aiohttp.ClientSession.post

    class MockResponse:
        def __init__(self, content, status=200):
            self.content = content.encode()
            self.status = status
            self.headers = {}

        async def json(self):
            if 'choices' in self.content.decode():
                return json.loads(self.content.decode())
            return {'response': {'text': 'Mock response'}}

        def raise_for_status(self):
            if self.status >= 400:
                raise aiohttp.ClientResponseError(self.request_info, self.history, self.status, message='Error')

        async def content(self):
            return self.content

    async def mock_post(self, *args, **kwargs):
        # 模拟不同的API响应
        if 'anthropic.com' in str(args[0]):
            content = json.dumps({
                'content': [{'text': 'Mock Anthropic response'}]
            })
        elif 'api.openai.com' in str(args[0]):
            content = json.dumps({
                'choices': [{'message': {'content': 'Mock OpenAI response'}}]
            })
        elif 'generativelanguage.googleapis.com' in str(args[0]):
            content = json.dumps({
                'candidates': [{'content': {'parts': [{'text': 'Mock Google AI response'}]}}]
            })
        else:
            content = json.dumps({'response': 'Mock response'})

        return MockResponse(content)

    aiohttp.ClientSession.post = mock_post

    asyncio.run(main())
