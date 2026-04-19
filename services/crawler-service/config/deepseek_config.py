"""
DeepSeek LLM配置 - 用于Crawl4AI AI增强功能
DeepSeek LLM Configuration - 由Athena和小诺控制
"""

import os
from dataclasses import dataclass
from typing import Any


@dataclass
class DeepSeekConfig:
    """DeepSeek配置类"""
    api_key: str
    base_url: str = 'https://api.deepseek.com'
    model: str = 'deepseek-chat'
    max_tokens: int = 4000
    temperature: float = 0.1
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0

class DeepSeekManager:
    """DeepSeek管理器"""

    def __init__(self):
        self.config = self._load_config()

    def _load_config(self) -> DeepSeekConfig:
        """从环境变量加载配置"""
        api_key = os.getenv('CRAWL4AI_LLM_API_KEY', '')
        base_url = os.getenv('CRAWL4AI_LLM_BASE_URL', 'https://api.deepseek.com')
        model = os.getenv('CRAWL4AI_LLM_MODEL', 'deepseek-chat')

        if not api_key:
            raise ValueError('DeepSeek API密钥未配置，请设置CRAWL4AI_LLM_API_KEY环境变量')

        return DeepSeekConfig(
            api_key=api_key,
            base_url=base_url,
            model=model
        )

    def get_openai_config(self) -> dict[str, Any]:
        """获取OpenAI兼容格式的配置"""
        return {
            'provider': 'openai',
            'api_key': self.config.api_key,
            'api_base': self.config.base_url + '/v1',
            'model': self.config.model,
            'max_tokens': self.config.max_tokens,
            'temperature': self.config.temperature,
            'timeout': self.config.timeout,
            'retry_attempts': self.config.retry_attempts,
            'retry_delay': self.config.retry_delay
        }

    def get_extraction_prompt(self) -> str:
        """获取智能提取提示词"""
        return """请从以下网页内容中提取结构化信息，包括：
1. 页面标题和副标题
2. 主要内容摘要
3. 关键数据（数字、日期、价格等）
4. 产品信息（如果有）
5. 联系信息（如果有）
6. 链接列表（如果有）

请以JSON格式返回结果，包含以下字段：
{
  'title': '页面标题',
  'subtitle': '副标题',
  'summary': '内容摘要',
  'key_data': ['关键数据1', '关键数据2'],
  'products': [{'name': '产品名', 'price': '价格', 'description': '描述'}],
  'contact': {'email': '邮箱', 'phone': '电话', 'address': '地址'},
  'links': [{'url': '链接地址', 'text': '链接文本'}]
}

请确保提取的信息准确、完整。"""

# 全局实例
deepseek_manager = None

def get_deepseek_config() -> DeepSeekConfig:
    """获取DeepSeek配置"""
    global deepseek_manager
    if deepseek_manager is None:
        deepseek_manager = DeepSeekManager()
    return deepseek_manager.config

def get_deepseek_manager() -> DeepSeekManager:
    """获取DeepSeek管理器"""
    global deepseek_manager
    if deepseek_manager is None:
        deepseek_manager = DeepSeekManager()
    return deepseek_manager
