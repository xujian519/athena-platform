#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一模型管理器 - 集成所有云端模型
Unified Model Manager - Integrating All Cloud Models
"""

import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import requests

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 配置API密钥（注意：生产环境中应该使用环境变量）
API_KEYS = {
    'deepseek': 'sk-7f0fa1165de249d0a30b62a2584bd4c5',
    'qwen': 'sk-051fca069bdb42978496df6fb4455e3a',
    'doubao': 'f107c89a-78bd-4f41-be38-694fba19b5d0',
    'glm': '9efe5766a7cd4bb687e40082ee4032b6.0mYTotbC7aRmoNCe',
    'kimi': 'sk-YpjqR3GImLtIIFflXhn6R6L9AWV6rfjLC1LuQteWzTUoRihl'
}

@dataclass
class ModelConfig:
    """模型配置"""
    name: str
    provider: str
    api_endpoint: str
    model_id: str
    max_tokens: int
    temperature: float = 0.7
    timeout: int = 30

class UnifiedModelManager:
    """统一模型管理器"""

    def __init__(self):
        self.models = self._initialize_models()
        self.routing_table = self._create_routing_table()
        self.usage_stats = {
            'total_requests': 0,
            'model_usage': {},
            'total_tokens': 0,
            'total_cost': 0.0
        }

    def _initialize_models(self) -> Dict[str, ModelConfig]:
        """初始化所有模型配置"""
        return {
            # DeepSeek 模型
            'deepseek_v3': ModelConfig(
                name='DeepSeek-V3',
                provider='deepseek',
                api_endpoint='https://api.deepseek.com/v1/chat/completions',
                model_id='deepseek-chat',
                max_tokens=4096,
                temperature=0.7
            ),
            'deepseek_coder': ModelConfig(
                name='DeepSeek-Coder',
                provider='deepseek',
                api_endpoint='https://api.deepseek.com/v1/chat/completions',
                model_id='deepseek-coder',
                max_tokens=4096,
                temperature=0.1
            ),

            # GLM 模型
            'glm_4_6': ModelConfig(
                name='GLM-4.6',
                provider='glm',
                api_endpoint='https://open.bigmodel.cn/api/paas/v4/chat/completions',
                model_id='glm-4',
                max_tokens=4096,
                temperature=0.7
            ),
            'glm_4v': ModelConfig(
                name='GLM-4V',
                provider='glm',
                api_endpoint='https://open.bigmodel.cn/api/paas/v4/chat/completions',
                model_id='glm-4v',
                max_tokens=4096,
                temperature=0.7
            ),

            # 通义千问模型
            'qwen_2_5': ModelConfig(
                name='Qwen-2.5-72B',
                provider='qwen',
                api_endpoint='https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation',
                model_id='qwen2.5-72b-instruct',
                max_tokens=4096,
                temperature=0.7
            ),

            # 豆包模型
            'doubao_pro': ModelConfig(
                name='Doubao-pro-32k',
                provider='doubao',
                api_endpoint='https://ark.cn-beijing.volces.com/api/v3/chat/completions',
                model_id='ep-20241204104902-qj9qk',
                max_tokens=4096,
                temperature=0.7
            ),

            # Kimi模型
            'kimi_k2': ModelConfig(
                name='Kimi-k2-200k',
                provider='kimi',
                api_endpoint='https://api.moonshot.cn/v1/chat/completions',
                model_id='moonshot-v1-8k',
                max_tokens=4096,
                temperature=0.7
            )
        }

    def _create_routing_table(self) -> Dict[str, str]:
        """创建路由表"""
        return {
            # 默认优先级路由
            'default': ['glm_4_6', 'deepseek_v3'],

            # 任务特定路由
            'chinese_dialogue': ['glm_4_6'],  # GLM中文优化
            'complex_reasoning': ['deepseek_v3'],  # DeepSeek推理最强
            'coding': ['deepseek_coder'],  # 专业代码模型
            'long_text': ['kimi_k2', 'deepseek_v3'],  # 长文本
            'image_understanding': ['glm_4v'],  # 多模态
            'knowledge_qa': ['qwen_2_5', 'glm_4_6'],  # 知识问答
            'creative_writing': ['glm_4_6', 'doubao_pro'],  # 创作
        }

    async def chat(self,
                   message: str,
                   task_type: str = 'default',
                   model_preference: str | None = None,
                   stream: bool = False) -> Dict[str, Any]:
        """统一聊天接口"""
        logger.info(f"收到请求: {task_type} - {message[:50]}...")

        # 更新统计
        self.usage_stats['total_requests'] += 1

        try:
            # 选择模型
            if model_preference:
                model_name = model_preference
            else:
                model_name = self._select_optimal_model(task_type)

            # 获取模型配置
            model_config = self.models.get(model_name)
            if not model_config:
                raise ValueError(f"未找到模型: {model_name}")

            # 调用模型
            result = await self._call_model(model_config, message, stream)

            # 更新使用统计
            self._update_usage_stats(model_name, result)

            return {
                'success': True,
                'response': result,
                'model_used': model_name,
                'task_type': task_type,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"调用失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _select_optimal_model(self, task_type: str) -> str:
        """选择最优模型"""
        # 获取候选模型列表
        candidates = self.routing_table.get(task_type, self.routing_table['default'])

        # 检查模型可用性
        for model_name in candidates:
            if self._is_model_available(model_name):
                return model_name

        # 如果都不可用，返回默认
        return 'glm_4_6'

    def _is_model_available(self, model_name: str) -> bool:
        """检查模型是否可用"""
        # 简化实现，可以添加健康检查
        return True

    async def _call_model(self,
                         config: ModelConfig,
                         message: str,
                         stream: bool) -> str:
        """调用具体模型"""
        headers = self._get_headers(config.provider)

        # 根据不同provider构造请求
        if config.provider == 'deepseek':
            payload = self._build_deepseek_payload(config, message)
        elif config.provider == 'glm':
            payload = self._build_glm_payload(config, message)
        elif config.provider == 'qwen':
            payload = self._build_qwen_payload(config, message)
        elif config.provider == 'doubao':
            payload = self._build_doubao_payload(config, message)
        elif config.provider == 'kimi':
            payload = self._build_kimi_payload(config, message)
        else:
            raise ValueError(f"不支持的provider: {config.provider}")

        # 发送请求
        response = requests.post(
            config.api_endpoint,
            headers=headers,
            json=payload,
            timeout=config.timeout
        )

        if response.status_code == 200:
            result = response.json()
            return self._extract_response(config.provider, result)
        else:
            raise Exception(f"API调用失败: {response.status_code} - {response.text}")

    def _get_headers(self, provider: str) -> Dict[str, str]:
        """获取请求头"""
        if provider == 'deepseek':
            return {
                'Authorization': f"Bearer {API_KEYS['deepseek']}",
                'Content-Type': 'application/json'
            }
        elif provider == 'glm':
            return {
                'Authorization': f"Bearer {API_KEYS['glm']}",
                'Content-Type': 'application/json'
            }
        elif provider == 'qwen':
            return {
                'Authorization': f"Bearer {API_KEYS['qwen']}",
                'Content-Type': 'application/json'
            }
        elif provider == 'doubao':
            return {
                'Authorization': f"Bearer {API_KEYS['doubao']}",
                'Content-Type': 'application/json'
            }
        elif provider == 'kimi':
            return {
                'Authorization': f"Bearer {API_KEYS['kimi']}",
                'Content-Type': 'application/json'
            }
        else:
            return {'Content-Type': 'application/json'}

    def _build_deepseek_payload(self, config: ModelConfig, message: str) -> Dict:
        """构建DeepSeek请求载荷"""
        return {
            'model': config.model_id,
            'messages': [{'role': 'user', 'content': message}],
            'max_tokens': config.max_tokens,
            'temperature': config.temperature,
            'stream': False
        }

    def _build_glm_payload(self, config: ModelConfig, message: str) -> Dict:
        """构建GLM请求载荷"""
        return {
            'model': config.model_id,
            'messages': [{'role': 'user', 'content': message}],
            'max_tokens': config.max_tokens,
            'temperature': config.temperature
        }

    def _build_qwen_payload(self, config: ModelConfig, message: str) -> Dict:
        """构建Qwen请求载荷"""
        return {
            'model': config.model_id,
            'input': {'messages': [{'role': 'user', 'content': message}]},
            'parameters': {
                'max_tokens': config.max_tokens,
                'temperature': config.temperature
            }
        }

    def _build_doubao_payload(self, config: ModelConfig, message: str) -> Dict:
        """构建豆包请求载荷"""
        return {
            'model': config.model_id,
            'messages': [{'role': 'user', 'content': message}],
            'max_tokens': config.max_tokens,
            'temperature': config.temperature
        }

    def _build_kimi_payload(self, config: ModelConfig, message: str) -> Dict:
        """构建Kimi请求载荷"""
        return {
            'model': config.model_id,
            'messages': [{'role': 'user', 'content': message}],
            'max_tokens': config.max_tokens,
            'temperature': config.temperature
        }

    def _extract_response(self, provider: str, result: Dict) -> str:
        """提取响应内容"""
        try:
            if provider in ['deepseek', 'glm', 'doubao', 'kimi']:
                return result['choices'][0]['message']['content']
            elif provider == 'qwen':
                return result['output']['text']
            else:
                return str(result)
        except (KeyError, IndexError) as e:
            logger.error(f"提取响应失败: {e}")
            return '响应解析失败'

    def _update_usage_stats(self, model_name: str, response: Any):
        """更新使用统计"""
        # 更新模型使用次数
        if model_name not in self.usage_stats['model_usage']:
            self.usage_stats['model_usage'][model_name] = 0
        self.usage_stats['model_usage'][model_name] += 1

        # 这里可以添加token和成本计算
        # self.usage_stats["total_tokens"] += token_count
        # self.usage_stats["total_cost"] += cost

    def get_usage_stats(self) -> Dict[str, Any]:
        """获取使用统计"""
        return {
            **self.usage_stats,
            'models_available': list(self.models.keys()),
            'routing_table': self.routing_table
        }

    def health_check(self) -> Dict[str, bool]:
        """健康检查"""
        health_status = {}

        for model_name, config in self.models.items():
            try:
                # 简单的ping测试
                test_response = requests.get(
                    config.api_endpoint.replace('/chat/completions', '/models'),
                    headers=self._get_headers(config.provider),
                    timeout=5
                )
                health_status[model_name] = test_response.status_code == 200
            except:
                health_status[model_name] = False

        return health_status

# 使用示例
async def test_models():
    """测试所有模型"""
    manager = UnifiedModelManager()

    logger.info(str("\n" + '='*60))
    logger.info('🚀 测试统一模型管理器')
    logger.info(str('='*60))

    # 测试不同任务
    test_cases = [
        ('你好，介绍一下自己', 'chinese_dialogue'),
        ('解释一下量子计算的基本原理', 'complex_reasoning'),
        ('用Python写一个快速排序算法', 'coding'),
        ('如何保持工作与生活的平衡？', 'knowledge_qa'),
        ('请写一首关于春天的诗', 'creative_writing')
    ]

    for message, task_type in test_cases:
        logger.info(f"\n📝 测试: {task_type}")
        logger.info(f"输入: {message}")

        result = await manager.chat(message, task_type)

        if result['success']:
            logger.info(f"✅ 模型: {result['model_used']}")
            logger.info(f"响应: {result['response'][:100]}...")
        else:
            logger.info(f"❌ 错误: {result['error']}")

    # 显示使用统计
    logger.info("\n📊 使用统计:")
    stats = manager.get_usage_stats()
    print(json.dumps(stats, indent=2, ensure_ascii=False))

    # 健康检查
    logger.info("\n🏥 健康检查:")
    health = manager.health_check()
    for model, status in health.items():
        logger.info(f"   {model}: {'✅ 正常' if status else '❌ 异常'}")

if __name__ == '__main__':
    import asyncio

    # 立即运行测试
    asyncio.run(test_models())