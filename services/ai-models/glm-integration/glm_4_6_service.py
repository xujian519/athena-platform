#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GLM-4.6 集成服务
为Athena工作平台提供智谱AI GLM-4.6最强能力
"""

import asyncio
from core.async_main import async_main
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import aiohttp


class GLMModelType(Enum):
    """GLM模型类型"""
    GLM_4_6 = 'glm-4.6'
    GLM_4_6_THINKING = 'glm-4.6-thinking'
    GLM_4_6_FLASH = 'glm-4.6-flash'

class TaskType(Enum):
    """任务类型"""
    PATENT_ANALYSIS = 'patent_analysis'
    CODE_GENERATION = 'code_generation'
    AGENT_COORDINATION = 'agent_coordination'
    LONG_TEXT_PROCESSING = 'long_text_processing'
    REASONING = 'reasoning'
    SEARCH = 'search'
    WRITING = 'writing'

@dataclass
class GLMRequest:
    """GLM请求参数"""
    messages: List[Dict[str, str]]
    model: GLMModelType = GLMModelType.GLM_4_6
    max_tokens: int = 4000
    temperature: float = 0.3
    top_p: float = 0.7
    enable_thinking: bool = False
    thinking_type: str | None = None  # 'step_by_step' or 'chain_of_thought'
    tools: Optional[List[Dict]] = None  # 智能体工具调用
    stream: bool = False

@dataclass
class GLMResponse:
    """GLM响应结果"""
    content: str
    thinking_process: str | None = None
    tool_calls: Optional[List[Dict]] = None
    usage: Dict = field(default_factory=dict)
    model: str = ''
    finish_reason: str = ''
    response_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

class GLM46APIClient:
    """GLM-4.6 API客户端"""

    def __init__(self, api_key: str = None):
        # 从平台获取GLM API密钥
        self.api_key = api_key or self._get_platform_api_key()
        self.base_url = 'https://open.bigmodel.cn/api/paas/v4'
        self.session = None
        self.logger = self._setup_logger()

        # 统计信息
        self.stats = {
            'total_requests': 0,
            'total_tokens': 0,
            'thinking_requests': 0,
            'agent_requests': 0,
            'success_rate': 0.0,
            'average_response_time': 0.0
        }

    def _get_platform_api_key(self) -> str:
        """从Athena平台获取GLM API密钥"""
        # 这里应该从平台的配置系统获取密钥
        # 临时使用环境变量或配置文件
        return os.getenv('GLM_API_KEY', 'your-platform-glm-api-key')

    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger('GLM46Client')
        logger.set_level(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.set_formatter(formatter)
            logger.add_handler(handler)

        return logger

    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=120),  # GLM-4.6可能需要更长时间
            headers={
                'Authorization': f"Bearer {self.api_key}",
                'Content-Type': 'application/json'
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()

    def _create_patent_analysis_prompt(self, patent_info: Dict) -> List[Dict[str, str]]:
        """创建专利分析专用提示词"""
        system_prompt = """你是一位专业的专利分析师，具有深厚的技术背景和法律知识。请对给定的专利信息进行深度分析。

分析维度包括：
1. 技术创新性评估
2. 专利保护范围分析
3. 实施可行性评估
4. 商业价值分析
5. 竞争优势分析
6. 潜在风险评估

请使用结构化的方式呈现分析结果。"""

        user_prompt = f"""请分析以下专利信息：

专利标题：{patent_info.get('title', '')}
专利摘要：{patent_info.get('abstract', '')}
技术领域：{patent_info.get('technical_field', '')}
背景技术：{patent_info.get('background', '')}
发明内容：{patent_info.get('invention', '')}
具体实施方式：{patent_info.get('implementation', '')}

请提供全面而深入的专利分析报告。"""

        return [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ]

    def _create_agent_coordination_prompt(self, task: str, available_tools: List[str]) -> List[Dict[str, str]]:
        """创建智能体协调提示词"""
        system_prompt = """你是一个强大的AI智能体协调器，能够合理分配任务给不同的专业工具。

你的职责：
1. 理解用户任务的复杂性和需求
2. 将复杂任务分解为子任务
3. 选择最合适的工具来执行每个子任务
4. 协调工具之间的协作
5. 整合结果并提供最终解决方案

可用工具包括代码生成、文档分析、数据处理、可视化等。"""

        user_prompt = f"""任务：{task}

可用工具：{', '.join(available_tools)}

请制定详细的执行计划，包括：
1. 任务分解
2. 工具选择
3. 执行步骤
4. 协调方案"""

        return [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ]

    def _create_long_text_processing_prompt(self, text: str, analysis_type: str) -> List[Dict[str, str]]:
        """创建长文本处理提示词"""
        system_prompt = f"""你是一个专业的长文本分析专家，能够处理和分析大量的技术文档。

分析类型：{analysis_type}

分析能力包括：
1. 关键信息提取
2. 主题分类
3. 情感分析
4. 关联性分析
5. 趋势识别
6. 总结归纳"""

        user_prompt = f"""请分析以下长文本内容：

{text[:10000]}... [文本已截断，总长度：{len(text)}字符]

请提供详细的分析报告。"""

        return [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ]

    async def create_patent_analysis_request(self, patent_info: Dict) -> GLMRequest:
        """创建专利分析请求"""
        messages = self._create_patent_analysis_prompt(patent_info)

        return GLMRequest(
            messages=messages,
            model=GLMModelType.GLM_4_6,
            max_tokens=6000,  # 专利分析需要更长输出
            temperature=0.2,  # 降低随机性
            enable_thinking=True,  # 启用思考模式
            thinking_type='step_by_step'
        )

    async def create_agent_coordination_request(self, task: str, tools: List[str]) -> GLMRequest:
        """创建智能体协调请求"""
        messages = self._create_agent_coordination_prompt(task, tools)

        return GLMRequest(
            messages=messages,
            model=GLMModelType.GLM_4_6,
            max_tokens=4000,
            temperature=0.3,
            enable_thinking=True,
            thinking_type='chain_of_thought'
        )

    async def create_long_text_request(self, text: str, analysis_type: str) -> GLMRequest:
        """创建长文本处理请求"""
        messages = self._create_long_text_processing_prompt(text, analysis_type)

        return GLMRequest(
            messages=messages,
            model=GLMModelType.GLM_4_6,  # 200K上下文优势
            max_tokens=3000,
            temperature=0.1,
            enable_thinking=True
        )

    async def call_glm_api(self, request: GLMRequest) -> GLMResponse:
        """调用GLM API"""
        start_time = datetime.now()

        try:
            if not self.session:
                raise RuntimeError('Session not initialized')

            # 构建请求体
            payload = {
                'model': request.model.value,
                'messages': request.messages,
                'max_tokens': request.max_tokens,
                'temperature': request.temperature,
                'top_p': request.top_p,
                'stream': request.stream
            }

            # GLM-4.6思考模式参数
            if request.enable_thinking:
                payload['enable_thinking'] = True
                if request.thinking_type:
                    payload['thinking_type'] = request.thinking_type

            # 工具调用参数
            if request.tools:
                payload['tools'] = request.tools

            self.logger.info(f"调用GLM API: {request.model.value}, 思考模式: {request.enable_thinking}")

            async with self.session.post(f"{self.base_url}/chat/completions", json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"GLM API请求失败: {response.status} - {error_text}")

                result = await response.json()

                # 解析响应
                choice = result['choices'][0]
                message = choice['message']
                usage = result.get('usage', {})

                # 提取思考过程
                thinking_process = None
                if 'thinking' in message:
                    thinking_process = message['thinking']

                # 提取工具调用
                tool_calls = None
                if 'tool_calls' in message:
                    tool_calls = message['tool_calls']

                content = message.get('content', '')
                response_time = (datetime.now() - start_time).total_seconds()

                # 更新统计信息
                self.stats['total_requests'] += 1
                self.stats['total_tokens'] += usage.get('total_tokens', 0)
                if request.enable_thinking:
                    self.stats['thinking_requests'] += 1
                if request.tools:
                    self.stats['agent_requests'] += 1

                # 计算平均响应时间
                self.stats['average_response_time'] = (
                    (self.stats['average_response_time'] * (self.stats['total_requests'] - 1) + response_time)
                    / self.stats['total_requests']
                )

                self.logger.info(f"GLM API响应成功: 耗时{response_time:.2f}s, tokens: {usage.get('total_tokens', 0)}")

                return GLMResponse(
                    content=content,
                    thinking_process=thinking_process,
                    tool_calls=tool_calls,
                    usage=usage,
                    model=result.get('model', ''),
                    finish_reason=choice.get('finish_reason', ''),
                    response_time=response_time,
                    timestamp=start_time
                )

        except Exception as e:
            self.logger.error(f"GLM API调用失败: {str(e)}")
            return GLMResponse(
                content=f"API调用失败: {str(e)}",
                response_time=(datetime.now() - start_time).total_seconds(),
                timestamp=start_time
            )

    async def analyze_patent(self, patent_info: Dict) -> GLMResponse:
        """专利分析"""
        request = await self.create_patent_analysis_request(patent_info)
        return await self.call_glm_api(request)

    async def coordinate_agents(self, task: str, available_tools: List[str]) -> GLMResponse:
        """智能体协调"""
        request = await self.create_agent_coordination_request(task, available_tools)
        return await self.call_glm_api(request)

    async def process_long_text(self, text: str, analysis_type: str = 'comprehensive') -> GLMResponse:
        """长文本处理"""
        request = await self.create_long_text_request(text, analysis_type)
        return await self.call_glm_api(request)

    async def generate_code_with_thinking(self, prompt: str, language: str = 'python') -> GLMResponse:
        """带思考过程的代码生成"""
        system_prompt = f"""你是一个顶级的{language}开发工程师，请在生成代码时展示你的思考过程。

请按照以下步骤：
1. 理解需求
2. 分析设计思路
3. 考虑边界情况
4. 实现代码
5. 验证正确性

代码要求：
- 遵循最佳实践
- 包含详细注释
- 考虑错误处理
- 优化性能"""

        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': f"请用{language}语言实现：{prompt}"}
        ]

        request = GLMRequest(
            messages=messages,
            model=GLMModelType.GLM_4_6,
            max_tokens=4000,
            temperature=0.2,
            enable_thinking=True,
            thinking_type='step_by_step'
        )

        return await self.call_glm_api(request)

    def get_statistics(self) -> Dict[str, Any]:
        """获取使用统计"""
        return self.stats.copy()

    async def test_connection(self) -> bool:
        """测试API连接"""
        try:
            test_request = GLMRequest(
                messages=[{'role': 'user', 'content': "你好，请回复'连接成功'"}],
                model=GLMModelType.GLM_4_6_FLASH,
                max_tokens=50
            )

            response = await self.call_glm_api(test_request)
            return '连接成功' in response.content or len(response.content) > 0

        except Exception as e:
            self.logger.error(f"GLM连接测试失败: {str(e)}")
            return False

# 全局实例
_glm_client = None

async def get_glm_client() -> GLM46APIClient:
    """获取GLM客户端实例"""
    global _glm_client
    if _glm_client is None:
        _glm_client = GLM46APIClient()
    return _glm_client

# 使用示例
async def main():
    """测试函数"""
    async with await get_glm_client() as client:
        # 测试连接
        if await client.test_connection():
            logger.info('✅ GLM-4.6 API连接成功!')

            # 测试带思考过程的代码生成
            response = await client.generate_code_with_thinking(
                '创建一个专利分析器类，包含文本处理、相似度计算等功能',
                'python'
            )

            logger.info(f"\n🤔 思考过程:")
            if response.thinking_process:
                logger.info(str(response.thinking_process))

            logger.info(f"\n💻 生成的代码:")
            logger.info(str(response.content))

            logger.info(f"\n📊 响应信息:")
            logger.info(f"- 模型: {response.model}")
            logger.info(f"- 耗时: {response.response_time:.2f}秒")
            logger.info(f"- Tokens: {response.usage.get('total_tokens', 0)}")

        else:
            logger.info('❌ GLM-4.6 API连接失败!')

# 入口点: @async_main装饰器已添加到main函数