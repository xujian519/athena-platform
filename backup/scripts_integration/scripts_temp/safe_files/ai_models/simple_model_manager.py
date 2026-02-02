#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版模型管理器 - 解决SSL问题
Simplified Model Manager - Solving SSL Issues
"""

import json
import logging
import os
import ssl
from datetime import datetime
from typing import Any, Dict, List

import requests

logger = logging.getLogger(__name__)

class SimpleModelManager:
    """简化版模型管理器"""

    def __init__(self):
        # 禁用SSL验证（仅用于测试，生产环境需要正确配置）
        self.session = requests.Session()
        self.session.verify = False

        # 加载配置
        with open('/Users/xujian/Athena工作平台/model_config.json', 'r') as f:
            self.config = json.load(f)

        self.usage_stats = {
            'total_requests': 0,
            'model_usage': {},
            'successful': 0,
            'failed': 0
        }

    def chat(self, message: str, task_type: str = 'default') -> Dict[str, Any]:
        """聊天接口"""
        self.usage_stats['total_requests'] += 1

        try:
            # 选择模型
            model_id = self._select_model(task_type)
            provider, model = self._parse_model_id(model_id)

            # 调用API
            response_text = self._call_api(provider, model, message)

            # 更新统计
            self.usage_stats['successful'] += 1
            if model_id not in self.usage_stats['model_usage']:
                self.usage_stats['model_usage'][model_id] = 0
            self.usage_stats['model_usage'][model_id] += 1

            return {
                'success': True,
                'response': response_text,
                'model_used': model_id,
                'provider': provider,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            self.usage_stats['failed'] += 1
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _select_model(self, task_type: str) -> str:
        """选择模型"""
        # 优先使用路由规则
        if task_type in self.config['routing_rules']:
            preferred = self.config['routing_rules'][task_type][0]
            return preferred

        # 使用默认模型
        return self.config['routing_rules']['default'][0]

    def _parse_model_id(self, model_id: str) -> tuple:
        """解析模型ID"""
        # 查找模型所属的provider
        for provider, config in self.config['endpoints'].items():
            if model_id in config['models']:
                return provider, model_id

        # 默认返回glm
        return 'glm', 'glm-4'

    def _call_api(self, provider: str, model: str, message: str) -> str:
        """调用API"""
        api_key = self.config['api_keys'][provider]
        endpoint_config = self.config['endpoints'][provider]

        # 构建URL
        url = endpoint_config['base_url'] + endpoint_config['chat_endpoint']

        # 构建请求头
        headers = {
            'Authorization': f"Bearer {api_key}",
            'Content-Type': 'application/json'
        }

        # 构建请求体
        payload = {
            'model': model,
            'messages': [{'role': 'user', 'content': message}],
            'max_tokens': 2048,
            'temperature': 0.7
        }

        # 特殊处理不同的API格式
        if provider == 'qwen':
            payload = {
                'model': model,
                'input': {'messages': [{'role': 'user', 'content': message}]},
                'parameters': {
                    'max_tokens': 2048,
                    'temperature': 0.7
                }
            }

        # 发送请求
        response = self.session.post(url, headers=headers, json=payload, timeout=30)

        if response.status_code == 200:
            result = response.json()
            return self._extract_content(provider, result)
        else:
            raise Exception(f"API错误 {response.status_code}: {response.text}")

    def _extract_content(self, provider: str, result: Dict) -> str:
        """提取响应内容"""
        try:
            if provider in ['deepseek', 'glm', 'doubao', 'kimi']:
                return result['choices'][0]['message']['content']
            elif provider == 'qwen':
                return result['output']['text']
            else:
                return str(result)
        except (KeyError, IndexError):
            return '响应解析失败'

    def get_stats(self) -> Dict[str, Any]:
        """获取使用统计"""
        return {
            'usage_stats': self.usage_stats,
            'available_models': self._list_available_models(),
            'routing_rules': self.config['routing_rules']
        }

    def _list_available_models(self) -> List[str]:
        """列出可用模型"""
        models = []
        for provider, config in self.config['endpoints'].items():
            for model_id in config['models']:
                models.append(f"{provider}:{model_id}")
        return models

# 测试函数
def test_simple_manager():
    """测试简化版管理器"""

    logger.info(str("\n" + '='*60))
    logger.info('🚀 简化版模型管理器测试')
    logger.info(str('='*60))

    manager = SimpleModelManager()

    # 测试用例
    test_cases = [
        ('你好，请介绍一下自己', 'chinese_dialogue'),
        ('解释一下什么是人工智能', 'knowledge_qa'),
        ('写一个Python的Hello World', 'coding'),
        ('请写一首关于春天的诗', 'creative_writing')
    ]

    for message, task_type in test_cases:
        logger.info(f"\n📝 任务类型: {task_type}")
        logger.info(f"输入: {message}")

        result = manager.chat(message, task_type)

        if result['success']:
            logger.info(f"✅ 模型: {result['model_used']}")
            logger.info(f"提供商: {result['provider']}")
            logger.info(f"响应: {result['response'][:100]}...")
        else:
            logger.info(f"❌ 错误: {result['error']}")

    # 显示统计
    logger.info("\n📊 使用统计:")
    stats = manager.get_stats()
    logger.info(f"总请求数: {stats['usage_stats']['total_requests']}")
    logger.info(f"成功: {stats['usage_stats']['successful']}")
    logger.info(f"失败: {stats['usage_stats']['failed']}")
    logger.info(f"模型使用情况:")
    for model, count in stats['usage_stats']['model_usage'].items():
        logger.info(f"  {model}: {count} 次")

if __name__ == '__main__':
    test_simple_manager()