#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生产环境模型管理器 - 优化版
Production Model Manager - Optimized Version
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import aiohttp

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API密钥配置
API_CONFIG = {
    # DeepSeek配置
    'deepseek': {
        'base_url': 'https://api.deepseek.com',
        'api_key': 'sk-7f0fa1165de249d0a30b62a2584bd4c5',
        'models': {
            'chat': 'deepseek-chat',
            'coder': 'deepseek-coder'
        }
    },

    # GLM配置
    'glm': {
        'base_url': 'https://open.bigmodel.cn/api/paas/v4',
        'api_key': '9efe5766a7cd4bb687e40082ee4032b6.0mYTotbC7aRmoNCe',
        'models': {
            'glm4': 'glm-4',
            'glm4v': 'glm-4v'
        }
    },

    # 通义千问配置
    'qwen': {
        'base_url': 'https://dashscope.aliyuncs.com/api/v1',
        'api_key': 'sk-051fca069bdb42978496df6fb4455e3a',
        'models': {
            'qwen25': 'qwen2.5-72b-instruct'
        }
    },

    # 豆包配置
    'doubao': {
        'base_url': 'https://ark.cn-beijing.volces.com/api/v3',
        'api_key': 'f107c89a-78bd-4f41-be38-694fba19b5d0',
        'models': {
            'doubao': 'ep-20241204104902-qj9qk'
        }
    },

    # Kimi配置
    'kimi': {
        'base_url': 'https://api.moonshot.cn/v1',
        'api_key': 'sk-YpjqR3GImLtIIFflXhn6R6L9AWV6rfjLC1LuQteWzTUoRihl',
        'models': {
            'kimi': 'moonshot-v1-8k'
        }
    }
}

class ProductionModelManager:
    """生产环境模型管理器"""

    def __init__(self):
        self.session = None
        self.routing = self._init_routing()
        self.stats = {
            'requests': 0,
            'success': 0,
            'errors': 0,
            'model_usage': {},
            'total_cost': 0.0
        }

    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=10)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()

    def _init_routing(self) -> Dict:
        """初始化路由规则"""
        return {
            '优先级路由': {
                'chinese_dialogue': ['glm:glm4'],  # GLM-4.6免费，中文优化
                'reasoning': ['deepseek:chat'],  # DeepSeek推理最强
                'coding': ['deepseek:coder'],    # 专业代码
                'knowledge': ['qwen:qwen25'],    # 知识问答
                'creative': ['glm:glm4', 'doubao:doubao'],
                'long_text': ['kimi:kimi'],
                'multimodal': ['glm:glm4v']
            },
            '备用路由': {
                'default': ['glm:glm4', 'deepseek:chat', 'qwen:qwen25']
            }
        }

    async def chat(self, message: str, task_type: str = 'default',
                   model_override: str = None) -> Dict[str, Any]:
        """统一聊天接口"""
        start_time = time.time()
        self.stats['requests'] += 1

        try:
            # 选择模型
            provider_model = await self._select_model(task_type, model_override)
            provider, model = provider_model.split(':')

            logger.info(f"使用模型: {provider} - {model}")

            # 调用模型
            response = await self._call_model(provider, model, message)

            # 更新统计
            self.stats['success'] += 1
            self._update_stats(provider_model)

            return {
                'success': True,
                'response': response,
                'model': f"{provider}_{model}",
                'provider': provider,
                'cost': self._calculate_cost(provider, response),
                'latency': time.time() - start_time
            }

        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"请求失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'latency': time.time() - start_time
            }

    async def _select_model(self, task_type: str, override: str = None) -> str:
        """选择最优模型"""
        if override and self._is_available(override):
            return override

        # 尝试优先级路由
        if task_type in self.routing['优先级路由']:
            for model in self.routing['优先级路由'][task_type]:
                if await self._is_available(model):
                    return model

        # 使用备用路由
        for model in self.routing['备用路由']['default']:
            if await self._is_available(model):
                return model

        # 默认返回GLM
        return 'glm:glm4'

    async def _is_available(self, provider_model: str) -> bool:
        """检查模型可用性"""
        provider, model = provider_model.split(':')
        return provider in API_CONFIG and model in API_CONFIG[provider]['models']

    async def _call_model(self, provider: str, model_id: str, message: str) -> str:
        """调用具体模型"""
        config = API_CONFIG[provider]
        url = f"{config['base_url']}/chat/completions"

        headers = {
            'Authorization': f"Bearer {config['api_key']}",
            'Content-Type': 'application/json'
        }

        # 构建请求体
        payload = {
            'model': config['models'][model_id],
            'messages': [{'role': 'user', 'content': message}],
            'max_tokens': 2048,
            'temperature': 0.7
        }

        # 特殊处理不同的API格式
        if provider == 'qwen':
            url = f"{config['base_url']}/services/aigc/text-generation/generation"
            payload = {
                'model': config['models'][model_id],
                'input': {'messages': [{'role': 'user', 'content': message}]},
                'parameters': {
                    'max_tokens': 2048,
                    'temperature': 0.7
                }
            }

        async with self.session.post(url, headers=headers, json=payload) as response:
            if response.status == 200:
                result = await response.json()
                return self._extract_content(provider, result)
            else:
                error_text = await response.text()
                raise Exception(f"API错误 {response.status}: {error_text}")

    def _extract_content(self, provider: str, result: Dict) -> str:
        """提取响应内容"""
        try:
            if provider in ['deepseek', 'glm', 'doubao', 'kimi']:
                return result['choices'][0]['message']['content']
            elif provider == 'qwen':
                return result['output']['text']
            else:
                return str(result)
        except (KeyError, IndexError) as e:
            logger.error(f"提取内容失败: {e}")
            return '响应解析失败'

    def _calculate_cost(self, provider: str, response: str) -> float:
        """计算成本（简化版）"""
        # 这里可以根据实际的计费规则计算
        # DeepSeek: $1/M tokens
        # GLM: 免费（包月）
        # Qwen: $1.2/M tokens
        # Kimi: $1.5/M tokens
        # Doubao: $0.8/M tokens

        cost_map = {
            'deepseek': 0.001,  # 每1000 tokens $0.001
            'glm': 0,  # 免费
            'qwen': 0.0012,
            'kimi': 0.0015,
            'doubao': 0.0008
        }

        # 简化计算，假设每个请求平均1000 tokens
        return cost_map.get(provider, 0) * len(response) / 1000

    def _update_stats(self, model: str):
        """更新统计信息"""
        if model not in self.stats['model_usage']:
            self.stats['model_usage'][model] = 0
        self.stats['model_usage'][model] += 1

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            'success_rate': self.stats['success'] / max(1, self.stats['requests']) * 100,
            'total_requests': self.stats['requests']
        }

    async def health_check(self) -> Dict[str, bool]:
        """健康检查"""
        health_status = {}

        for provider, config in API_CONFIG.items():
            try:
                # 简单的连接测试
                test_url = f"{config['base_url']}/models"
                headers = {'Authorization': f"Bearer {config['api_key']}"}

                async with self.session.get(test_url, headers=headers) as response:
                    health_status[provider] = response.status == 200
            except Exception as e:
                logger.error(f"{provider} 健康检查失败: {e}")
                health_status[provider] = False

        return health_status


# 使用示例
async def demo_production_manager():
    """演示生产环境管理器"""

    logger.info(str("\n" + '='*60))
    logger.info('🚀 生产环境模型管理器演示')
    logger.info(str('='*60))

    async with ProductionModelManager() as manager:
        # 健康检查
        logger.info("\n🏥 执行健康检查...")
        health = await manager.health_check()
        for provider, status in health.items():
            logger.info(f"   {provider}: {'✅ 正常' if status else '❌ 异常'}")

        # 测试不同任务
        test_cases = [
            ('你好，请用中文回答', 'chinese_dialogue'),
            ('解释一下什么是机器学习', 'reasoning'),
            ('写一个Python函数计算斐波那契数列', 'coding'),
            ('如何提高工作效率？', 'knowledge'),
            ('请写一首关于科技的短诗', 'creative')
        ]

        logger.info("\n📝 测试不同任务类型...")
        for message, task_type in test_cases:
            logger.info(f"\n任务类型: {task_type}")
            logger.info(f"输入: {message}")

            result = await manager.chat(message, task_type)

            if result['success']:
                logger.info(f"✅ 模型: {result['model']}")
                logger.info(f"响应: {result['response'][:150]}...")
                logger.info(f"延迟: {result['latency']:.2f}s")
                logger.info(f"成本: ${result['cost']:.4f}")
            else:
                logger.info(f"❌ 错误: {result['error']}")

        # 显示统计信息
        logger.info("\n📊 使用统计:")
        stats = manager.get_stats()
        logger.info(f"   总请求数: {stats['total_requests']}")
        logger.info(f"   成功率: {stats['success_rate']:.1f}%")
        logger.info(f"   模型使用情况:")
        for model, count in stats['model_usage'].items():
            logger.info(f"     {model}: {count} 次")
        logger.info(f"   总成本: ${stats['total_cost']:.4f}")

        logger.info("\n✅ 演示完成！")

if __name__ == '__main__':
    asyncio.run(demo_production_manager())