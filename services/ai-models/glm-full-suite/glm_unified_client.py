#!/usr/bin/env python3
"""
智谱AI全系列模型统一客户端
支持GLM-4.7、GLM-4.7-Code、GLM-4.7-Flash、GLM-4V、CogVideoX、CogView等全系列模型
"""

import json
import logging

# 导入安全配置
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)

sys.path.append(str(Path(__file__).parent.parent / "core"))


class GLMModel(Enum):
    """智谱AI全系列模型枚举"""
    # 语言模型 - GLM 4.7系列
    GLM_4_7 = 'glm-4.7'
    GLM_4_7_CODE = 'glm-4.7-code'
    GLM_4_7_FLASH = 'glm-4.7-flash'
    GLM_4V_PLUS = 'glm-4v-plus'

    # 多模态模型
    COGVIDEOX = 'cogvideox'
    COGVIEW_4 = 'cogview-4'
    COGVIEW_3_PLUS = 'cogview-3-plus'
    COGVLM = 'cogvlm'

class ModalityType(Enum):
    """模态类型"""
    TEXT = 'text'
    IMAGE = 'image'
    VIDEO = 'video'
    MULTIMODAL = 'multimodal'

@dataclass
class GLMRequest:
    """GLM统一请求参数"""
    model: GLMModel
    messages: list[dict[str, str]
    modality: ModalityType = ModalityType.TEXT
    max_tokens: int = 4000
    temperature: float = 0.3
    top_p: float = 0.7
    stream: bool = False
    enable_thinking: bool = False
    thinking_type: str | None = None

    # 多模态参数
    images: list[str] | None = None  # base64编码的图片
    video_prompt: str | None = None  # 视频生成提示

    # 生成参数
    image_size: str = '1024*1024'  # 图片尺寸
    video_duration: int = 5  # 视频时长(秒)
    num_frames: int = 16  # 视频帧数

@dataclass
class GLMResponse:
    """GLM统一响应结果"""
    success: bool
    content: str
    thinking_process: str | None = None
    modality: ModalityType = ModalityType.TEXT
    model: str = ''
    usage: dict = field(default_factory=dict)
    finish_reason: str = ''
    response_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    # 多模态输出
    images: list[str] | None = None  # 生成的图片URL或base64
    videos: list[str] | None = None  # 生成的视频URL

    # 错误信息
    error: str | None = None

class ZhipuAIUnifiedClient:
    """智谱AI全系列模型统一客户端"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or '9efe5766a7cd4bb687e40082ee4032b6.0mYTotbC7aRmoNCe'
        self.base_url = 'https://open.bigmodel.cn/api/paas/v4'
        self.session = None
        self.logger = self._setup_logger()

        # 模型能力映射 - GLM 4.7系列
        self.model_capabilities = {
            GLMModel.GLM_4_7: {
                'modalities': [ModalityType.TEXT],
                'specialties': ['reasoning', 'analysis', 'agent', 'patent', 'coding'],
                'context_length': 200000,
                'cost_per_1k': 0.15,
                'thinking_enabled': True,
                'max_tokens': 65536
            },
            GLMModel.GLM_4_7_CODE: {
                'modalities': [ModalityType.TEXT],
                'specialties': ['coding', 'algorithm', 'debugging', 'technical', 'agentic_coding'],
                'context_length': 200000,
                'cost_per_1k': 0.15,
                'thinking_enabled': True,
                'max_tokens': 65536
            },
            GLMModel.GLM_4_7_FLASH: {
                'modalities': [ModalityType.TEXT],
                'specialties': ['quick_response', 'simple_tasks', 'chat', 'coding'],
                'context_length': 128000,
                'cost_per_1k': 0.0,
                'free': True,
                'thinking_enabled': True,
                'max_tokens': 65536
            },
            GLMModel.GLM_4V_PLUS: {
                'modalities': [ModalityType.MULTIMODAL],
                'specialties': ['image_understanding', 'visual_reasoning', 'chart_analysis'],
                'context_length': 8000,
                'cost_per_1k': 0.20
            },
            GLMModel.COGVIDEOX: {
                'modalities': [ModalityType.VIDEO],
                'specialties': ['text_to_video', 'animation', 'content_creation'],
                'context_length': 2000,
                'cost_per_generation': 0.5
            },
            GLMModel.COGVIEW_4: {
                'modalities': [ModalityType.IMAGE],
                'specialties': ['text_to_image', 'chinese_text', 'patent_drawings'],
                'context_length': 1000,
                'cost_per_generation': 0.1
            },
            GLMModel.COGVIEW_3_PLUS: {
                'modalities': [ModalityType.IMAGE],
                'specialties': ['high_quality_image', 'artistic_style', 'technical_diagrams'],
                'context_length': 1000,
                'cost_per_generation': 0.15
            }
        }

        # 统计信息
        self.stats = {
            'total_requests': 0,
            'total_cost': 0.0,
            'model_usage': {model.value: 0 for model in GLMModel},
            'modality_usage': {modality.value: 0 for modality in ModalityType},
            'success_rate': 0.0
        }

    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger('ZhipuUnifiedClient')
        logger.setLevel(logging.INFO)

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
            timeout=aiohttp.ClientTimeout(total=180),
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

    def select_optimal_model(self, task: str, modality: ModalityType, complexity: str = 'medium') -> GLMModel:
        """智能选择最优模型"""
        if modality == ModalityType.VIDEO:
            return GLMModel.COGVIDEOX
        elif modality == ModalityType.IMAGE:
            # 根据任务复杂度选择图片生成模型
            if '专利' in task or '技术' in task or 'diagram' in task:
                return GLMModel.COGVIEW_4
            elif '艺术' in task or '高质量' in task:
                return GLMModel.COGVIEW_3_PLUS
            else:
                return GLMModel.COGVIEW_4

        elif modality == ModalityType.MULTIMODAL:
            return GLMModel.GLM_4V_PLUS

        else:  # TEXT
            # 文本模型选择逻辑 - GLM 4.7系列
            if '代码' in task or '编程' in task or '算法' in task:
                return GLMModel.GLM_4_7_CODE
            elif '专利' in task or '分析' in task or '推理' in task:
                return GLMModel.GLM_4_7
            elif complexity == 'simple' or '快速' in task:
                return GLMModel.GLM_4_7_FLASH
            else:
                return GLMModel.GLM_4_7

    async def call_text_model(self, request: GLMRequest) -> GLMResponse:
        """调用文本模型"""
        start_time = datetime.now()

        try:
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

            async with self.session.post(f"{self.base_url}/chat/completions", json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"文本模型API请求失败: {response.status} - {error_text}")

                result = await response.json()
                choice = result['choices'][0]
                message = choice['message']
                usage = result.get('usage', {})

                thinking_process = None
                if 'thinking' in message:
                    thinking_process = message['thinking']

                content = message.get('content', '')
                response_time = (datetime.now() - start_time).total_seconds()

                # 更新统计
                self._update_stats(request.model, ModalityType.TEXT, usage, response_time, True)

                return GLMResponse(
                    success=len(content) > 0,
                    content=content,
                    thinking_process=thinking_process,
                    modality=ModalityType.TEXT,
                    model=result.get('model', ''),
                    usage=usage,
                    finish_reason=choice.get('finish_reason', ''),
                    response_time=response_time,
                    timestamp=start_time
                )

        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds()
            self._update_stats(request.model, ModalityType.TEXT, {}, response_time, False)
            self.logger.error(f"文本模型调用失败: {str(e)}")
            return GLMResponse(
                success=False,
                content='',
                modality=ModalityType.TEXT,
                response_time=response_time,
                timestamp=start_time,
                error=str(e)
            )

    async def call_image_model(self, request: GLMRequest) -> GLMResponse:
        """调用文生图模型"""
        start_time = datetime.now()

        try:
            payload = {
                'model': request.model.value,
                'prompt': request.messages[0]['content'],
                'size': request.image_size,
                'quality': 'standard'
            }

            # CogView专用参数
            if request.model == GLMModel.COGVIEW_4:
                payload['style'] = 'realistic'

            async with self.session.post(f"{self.base_url}/images/generations", json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"图片生成API请求失败: {response.status} - {error_text}")

                result = await response.json()
                response_time = (datetime.now() - start_time).total_seconds()

                # 提取生成的图片URL
                images = []
                if 'data' in result:
                    for item in result['data']:
                        if 'url' in item:
                            images.append(item['url'])
                        elif 'b64_json' in item:
                            images.append(item['b64_json'])

                # 估算成本（基于模型定价）
                estimated_cost = self.model_capabilities[request.model]['cost_per_generation']

                # 更新统计
                self._update_stats(request.model, ModalityType.IMAGE, {'estimated_cost': estimated_cost}, response_time, True)

                return GLMResponse(
                    success=len(images) > 0,
                    content=f"生成了 {len(images)} 张图片",
                    modality=ModalityType.IMAGE,
                    model=request.model.value,
                    images=images,
                    usage={'estimated_cost': estimated_cost, 'count': len(images)},
                    response_time=response_time,
                    timestamp=start_time
                )

        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds()
            self._update_stats(request.model, ModalityType.IMAGE, {}, response_time, False)
            self.logger.error(f"图片生成失败: {str(e)}")
            return GLMResponse(
                success=False,
                content='',
                modality=ModalityType.IMAGE,
                response_time=response_time,
                timestamp=start_time,
                error=str(e)
            )

    async def call_video_model(self, request: GLMRequest) -> GLMResponse:
        """调用文生视频模型"""
        start_time = datetime.now()

        try:
            payload = {
                'model': request.model.value,
                'prompt': request.video_prompt or request.messages[0]['content'],
                'duration': request.video_duration,
                'num_frames': request.num_frames,
                'resolution': '720p'
            }

            async with self.session.post(f"{self.base_url}/videos/generations", json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"视频生成API请求失败: {response.status} - {error_text}")

                result = await response.json()
                response_time = (datetime.now() - start_time).total_seconds()

                # 提取生成的视频URL
                videos = []
                if 'data' in result:
                    for item in result['data']:
                        if 'url' in item:
                            videos.append(item['url'])

                # 估算成本
                estimated_cost = self.model_capabilities[request.model]['cost_per_generation']

                # 更新统计
                self._update_stats(request.model, ModalityType.VIDEO, {'estimated_cost': estimated_cost}, response_time, True)

                return GLMResponse(
                    success=len(videos) > 0,
                    content=f"生成了 {len(videos)} 个视频",
                    modality=ModalityType.VIDEO,
                    model=request.model.value,
                    videos=videos,
                    usage={'estimated_cost': estimated_cost, 'count': len(videos)},
                    response_time=response_time,
                    timestamp=start_time
                )

        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds()
            self._update_stats(request.model, ModalityType.VIDEO, {}, response_time, False)
            self.logger.error(f"视频生成失败: {str(e)}")
            return GLMResponse(
                success=False,
                content='',
                modality=ModalityType.VIDEO,
                response_time=response_time,
                timestamp=start_time,
                error=str(e)
            )

    async def call_multimodal_model(self, request: GLMRequest) -> GLMResponse:
        """调用多模态模型"""
        start_time = datetime.now()

        try:
            # 构建多模态消息
            messages = []
            for msg in request.messages:
                if msg['role'] == 'user' and request.images:
                    # 添加图片到用户消息
                    multimodal_content = [
                        {'type': 'text', 'text': msg['content']}
                    ]
                    for image in request.images:
                        multimodal_content.append({
                            'type': 'image_url',
                            'image_url': {'url': f"data:image/jpeg;base64,{image}"}
                        })
                    messages.append({'role': 'user', 'content': multimodal_content})
                else:
                    messages.append(msg)

            payload = {
                'model': request.model.value,
                'messages': messages,
                'max_tokens': request.max_tokens,
                'temperature': request.temperature
            }

            async with self.session.post(f"{self.base_url}/chat/completions", json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"多模态模型API请求失败: {response.status} - {error_text}")

                result = await response.json()
                choice = result['choices'][0]
                message = choice['message']
                usage = result.get('usage', {})
                response_time = (datetime.now() - start_time).total_seconds()

                content = message.get('content', '')

                # 更新统计
                self._update_stats(request.model, ModalityType.MULTIMODAL, usage, response_time, True)

                return GLMResponse(
                    success=len(content) > 0,
                    content=content,
                    modality=ModalityType.MULTIMODAL,
                    model=result.get('model', ''),
                    usage=usage,
                    finish_reason=choice.get('finish_reason', ''),
                    response_time=response_time,
                    timestamp=start_time
                )

        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds()
            self._update_stats(request.model, ModalityType.MULTIMODAL, {}, response_time, False)
            self.logger.error(f"多模态模型调用失败: {str(e)}")
            return GLMResponse(
                success=False,
                content='',
                modality=ModalityType.MULTIMODAL,
                response_time=response_time,
                timestamp=start_time,
                error=str(e)
            )

    async def generate_response(self, request: GLMRequest) -> GLMResponse:
        """统一生成响应入口"""
        self.stats['total_requests'] += 1

        if request.modality == ModalityType.IMAGE:
            return await self.call_image_model(request)
        elif request.modality == ModalityType.VIDEO:
            return await self.call_video_model(request)
        elif request.modality == ModalityType.MULTIMODAL:
            return await self.call_multimodal_model(request)
        else:
            return await self.call_text_model(request)

    def _update_stats(self, model: GLMModel, modality: ModalityType, usage: dict, response_time: float, success: bool) -> Any:
        """更新统计信息"""
        self.stats['model_usage'][model.value] += 1
        self.stats['modality_usage'][modality.value] += 1

        # 更新成本
        if 'total_tokens' in usage:
            cost = (usage['total_tokens'] / 1000) * self.model_capabilities[model]['cost_per_1k']
            self.stats['total_cost'] += cost
        elif 'estimated_cost' in usage:
            self.stats['total_cost'] += usage['estimated_cost']

        # 更新成功率
        current_success = self.stats['success_rate'] * (self.stats['total_requests'] - 1)
        new_success = 1 if success else 0
        self.stats['success_rate'] = (current_success + new_success) / self.stats['total_requests']

    def get_model_capabilities(self) -> dict[str, Any]:
        """获取模型能力信息"""
        return {model.value: capabilities for model, capabilities in self.model_capabilities.items()}

    def get_statistics(self) -> dict[str, Any]:
        """获取使用统计"""
        return self.stats.copy()

# 使用示例
async def main():
    """测试全系列模型"""
    async with ZhipuAIUnifiedClient() as client:
        logger.info('🚀 智谱AI全系列模型测试')

        # 测试1: GLM-4.7推理
        request = GLMRequest(
            model=GLMModel.GLM_4_7,
            messages=[{'role': 'user', 'content': '请分析一下AI专利技术的发展趋势'}],
            enable_thinking=True
        )

        response = await client.generate_response(request)
        logger.info(f"✅ GLM-4.6推理: {response.success}, 耗时: {response.response_time:.2f}s")

        # 测试2: GLM-4.7-Code
        request = GLMRequest(
            model=GLMModel.GLM_4_7_CODE,
            messages=[{'role': 'user', 'content': '写一个专利相似度计算的Python函数'}]
        )

        response = await client.generate_response(request)
        logger.info(f"✅ GLM-4.6-Code: {response.success}")

        # 测试3: CogView文生图
        request = GLMRequest(
            model=GLMModel.COGVIEW_4,
            messages=[{'role': 'user', 'content': '专利技术架构图，包含多个模块和数据流'}],
            modality=ModalityType.IMAGE
        )

        response = await client.generate_response(request)
        logger.info(f"✅ CogView-4文生图: {response.success}")

        # 显示统计信息
        stats = client.get_statistics()
        logger.info(f"\n📊 使用统计: {json.dumps(stats, indent=2, ensure_ascii=False)}")

# 入口点: @async_main装饰器已添加到main函数
