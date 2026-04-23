#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大语言模型集成系统
Large Language Model Integration System

功能:
1. 自然语言理解增强 - 深度语义分析和专利理解
2. 智能对话系统 - 专业专利问答和分析对话
3. 文本生成能力 - 专利报告、分析意见生成
4. 多模态理解 - 图表、公式等专利内容理解
5. 知识推理增强 - 基于大模型的复杂推理
"""

import asyncio
import hashlib
import json
import logging
import os
import re
import sys
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

# AI相关导入
import torch
from sentence_transformers import SentenceTransformer
from transformers import (
    AutoModelForCausalLM,
    AutoModelForSequenceClassification,
    AutoTokenizer,
    GenerationConfig,
    pipeline,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 配置
MODEL_CACHE_DIR = '/Users/xujian/Athena工作平台/models/llm_cache'
os.makedirs(MODEL_CACHE_DIR, exist_ok=True)


class TaskType(Enum):
    """任务类型枚举"""
    PATENT_ANALYSIS = 'patent_analysis'          # 专利分析
    QUESTION_ANSWERING = 'question_answering'    # 问答对话
    REPORT_GENERATION = 'report_generation'      # 报告生成
    TRANSLATION = 'translation'                  # 翻译
    SUMMARIZATION = 'summarization'              # 摘要生成
    LEGAL_REASONING = 'legal_reasoning'          # 法律推理
    TECH_EXPLANATION = 'tech_explanation'        # 技术解释
    COMPARISON = 'comparison'                    # 对比分析


class ModelSize(Enum):
    """模型规模枚举"""
    SMALL = 'small'          # 小模型 (1-3B)
    MEDIUM = 'medium'        # 中等模型 (3-7B)
    LARGE = 'large'          # 大模型 (7-13B)
    XLARGE = 'xlarge'        # 超大模型 (13B+)


@dataclass
class LLMRequest:
    """大模型请求结构"""
    request_id: str
    task_type: TaskType
    input_text: str
    context: Optional[Dict[str, Any]] = None
    model_size: ModelSize = ModelSize.MEDIUM
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 50
    stream_output: bool = False
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class LLMResponse:
    """大模型响应结构"""
    request_id: str
    task_type: TaskType
    output_text: str
    confidence: float
    model_used: str
    tokens_used: int
    processing_time: float
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ConversationContext:
    """对话上下文"""
    conversation_id: str
    user_id: str
    history: List[Dict[str, str]]
    current_topic: Optional[str] = None
    patent_context: Optional[Dict[str, Any]] = None
    preferences: Dict[str, Any] = None
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if self.preferences is None:
            self.preferences = {}


class ModelManager:
    """模型管理器"""

    def __init__(self):
        self.models = {}
        self.tokenizers = {}
        self.pipelines = {}
        self.model_configs = self._load_model_configs()
        self.model_status = {}

    def _load_model_configs(self) -> Dict[str, Dict[str, Any]]:
        """加载模型配置"""
        return {
            # 中文大模型
            'chatglm3-6b': {
                'model_id': 'THUDM/chatglm3-6b',
                'size': ModelSize.MEDIUM,
                'task_types': [TaskType.PATENT_ANALYSIS, TaskType.QUESTION_ANSWERING],
                'specialization': 'chinese_conversation',
                'memory_requirement': '12GB'
            },
            'baichuan2-7b': {
                'model_id': 'baichuan-inc/Baichuan2-7B-Chat',
                'size': ModelSize.LARGE,
                'task_types': list(TaskType),
                'specialization': 'general_purpose',
                'memory_requirement': '14GB'
            },
            'qwen-7b': {
                'model_id': 'Qwen/Qwen-7B-Chat',
                'size': ModelSize.LARGE,
                'task_types': [TaskType.PATENT_ANALYSIS, TaskType.TECH_EXPLANATION],
                'specialization': 'technical_reasoning',
                'memory_requirement': '14GB'
            },

            # 英文大模型
            'llama2-7b': {
                'model_id': 'meta-llama/Llama-2-7b-chat-hf',
                'size': ModelSize.LARGE,
                'task_types': [TaskType.PATENT_ANALYSIS, TaskType.LEGAL_REASONING],
                'specialization': 'english_legal',
                'memory_requirement': '14GB'
            },

            # 轻量级模型
            'minichat-2b': {
                'model_id': 'microsoft/DialoGPT-medium',
                'size': ModelSize.SMALL,
                'task_types': [TaskType.QUESTION_ANSWERING],
                'specialization': 'simple_dialogue',
                'memory_requirement': '4GB'
            }
        }

    async def load_model(self, model_name: str) -> bool:
        """加载模型"""
        if model_name in self.models:
            return True

        if model_name not in self.model_configs:
            logger.error(f"未知模型: {model_name}")
            return False

        config = self.model_configs[model_name]

        try:
            logger.info(f"正在加载模型: {model_name}")

            # 加载tokenizer
            self.tokenizers[model_name] = AutoTokenizer.from_pretrained(
                config['model_id'],
                cache_dir=MODEL_CACHE_DIR,
                trust_remote_code=True
            )

            # 加载模型
            self.models[model_name] = AutoModelForCausalLM.from_pretrained(
                config['model_id'],
                cache_dir=MODEL_CACHE_DIR,
                torch_dtype=torch.float16,
                device_map='auto',
                trust_remote_code=True
            )

            # 创建pipeline
            self.pipelines[model_name] = pipeline(
                'text-generation',
                model=self.models[model_name],
                tokenizer=self.tokenizers[model_name],
                torch_dtype=torch.float16,
                device_map='auto'
            )

            self.model_status[model_name] = {
                'loaded': True,
                'load_time': datetime.now(),
                'memory_usage': 'unknown',
                'last_used': None
            }

            logger.info(f"模型加载成功: {model_name}")
            return True

        except Exception as e:
            logger.error(f"模型加载失败 {model_name}: {str(e)}")
            return False

    def get_model_for_task(self, task_type: TaskType, model_size: ModelSize = ModelSize.MEDIUM) -> Optional[str]:
        """根据任务类型获取最适合的模型"""
        suitable_models = []

        for model_name, config in self.model_configs.items():
            if (task_type in config['task_types'] and
                config['size'] == model_size and
                model_name in self.models):
                suitable_models.append(model_name)

        if not suitable_models:
            # 回退到任意已加载的合适模型
            for model_name, config in self.model_configs.items():
                if (task_type in config['task_types'] and
                    model_name in self.models):
                    suitable_models.append(model_name)

        return suitable_models[0] if suitable_models else None

    async def unload_model(self, model_name: str):
        """卸载模型释放内存"""
        if model_name in self.models:
            del self.models[model_name]
            del self.tokenizers[model_name]
            if model_name in self.pipelines:
                del self.pipelines[model_name]
            if model_name in self.model_status:
                self.model_status[model_name]['loaded'] = False

            # 清理GPU内存
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            logger.info(f"模型已卸载: {model_name}")


class PatentPromptTemplates:
    """专利提示词模板"""

    @staticmethod
    def patent_analysis_template(patent_text: str, analysis_type: str = 'comprehensive') -> str:
        """专利分析提示词模板"""
        templates = {
            "comprehensive": f"""
请对以下专利进行全面分析：

专利内容：
{patent_text}

请从以下维度进行分析：
1. 技术方案概述
2. 新颖性分析
3. 创造性分析
4. 实用性分析
5. 技术价值评估
6. 商业应用前景
7. 潜在侵权风险
8. 改进建议

请以专业、客观的语言进行分析，并给出具体的评估结果。
""",
            "novelty": f"""
请分析以下专利的新颖性：

专利内容：
{patent_text}

分析要点：
1. 与现有技术的对比
2. 创新点的识别
3. 新颖性评估结论
4. 支持理由和证据
""",
            "inventive": f"""
请评估以下专利的创造性：

专利内容：
{patent_text}

评估维度：
1. 技术方案的进步性
2. 突出性技术特点
3. 有益效果分析
4. 创造性等级评定
""",
            "technical_value": f"""
请评估以下专利的技术价值：

专利内容：
{patent_text}

评估内容：
1. 技术先进性
2. 技术成熟度
3. 技术通用性
4. 技术影响力
5. 技术发展潜力
"""
        }
        return templates.get(analysis_type, templates['comprehensive'])

    @staticmethod
    def patent_qa_template(question: str, patent_context: str = '') -> str:
        """专利问答提示词模板"""
        if patent_context:
            return f"""
基于以下专利信息，请回答用户问题：

专利信息：
{patent_context}

用户问题：{question}

请基于专利内容进行准确、专业的回答。如果专利信息不足以回答问题，请明确说明。
"""
        else:
            return f"""
专利相关问题：{question}

请提供专业的专利领域回答，涉及法律条款时请准确引用相关法规。
"""

    @staticmethod
    def patent_comparison_template(patent1: str, patent2: str) -> str:
        """专利对比分析提示词模板"""
        return f"""
请对以下两个专利进行对比分析：

专利1：
{patent1}

专利2：
{patent2}

对比维度：
1. 技术方案相似性
2. 创新点对比
3. 技术效果对比
4. 保护范围对比
5. 侵权风险评估
6. 优劣势分析

请提供详细的对比报告和结论。
"""

    @staticmethod
    def patent_report_template(patents_data: List[Dict[str, Any]], report_type: str = 'analysis') -> str:
        """专利报告生成提示词模板"""
        patents_text = "\n".join([f"专利{i+1}: {p.get('abstract', p.get('title', '未知'))}"
                                 for i, p in enumerate(patents_data)])

        templates = {
            "analysis": f"""
基于以下专利信息，请生成专利分析报告：

{patents_text}

报告应包含：
1. 专利概况统计
2. 技术领域分布
3. 核心技术分析
4. 创新趋势总结
5. 竞争格局分析
6. 发展建议

请生成结构化、专业的分析报告。
""",
            "portfolio": f"""
基于以下专利组合信息，请生成专利组合评估报告：

{patents_text}

报告内容：
1. 专利组合概况
2. 技术覆盖度分析
3. 专利质量评估
4. 组合价值评估
5. 风险分析
6. 优化建议

请提供专业的专利组合管理建议。
"""
        }
        return templates.get(report_type, templates['analysis'])


class ConversationManager:
    """对话管理器"""

    def __init__(self):
        self.conversations = {}  # conversation_id -> ConversationContext
        self.user_sessions = {}  # user_id -> list of conversation_id

    def create_conversation(self, user_id: str, patent_context: Optional[Dict[str, Any]] = None) -> str:
        """创建新对话"""
        conversation_id = str(uuid.uuid4())

        context = ConversationContext(
            conversation_id=conversation_id,
            user_id=user_id,
            history=[],
            patent_context=patent_context
        )

        self.conversations[conversation_id] = context

        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = []
        self.user_sessions[user_id].append(conversation_id)

        logger.info(f"创建新对话: {conversation_id} for user: {user_id}")
        return conversation_id

    def get_conversation(self, conversation_id: str) -> ConversationContext | None:
        """获取对话上下文"""
        return self.conversations.get(conversation_id)

    def add_message(self, conversation_id: str, role: str, content: str) -> bool:
        """添加对话消息"""
        if conversation_id not in self.conversations:
            return False

        context = self.conversations[conversation_id]
        context.history.append({
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })

        # 限制历史记录长度
        if len(context.history) > 20:
            context.history = context.history[-20:]

        context.updated_at = datetime.now()
        return True

    def get_conversation_history(self, conversation_id: str, limit: int = 10) -> List[Dict[str, str]]:
        """获取对话历史"""
        if conversation_id not in self.conversations:
            return []

        history = self.conversations[conversation_id].history
        return history[-limit:] if limit > 0 else history

    def clear_conversation(self, conversation_id: str) -> bool:
        """清空对话历史"""
        if conversation_id in self.conversations:
            self.conversations[conversation_id].history = []
            self.conversations[conversation_id].updated_at = datetime.now()
            return True
        return False


class LargeLanguageModelIntegration:
    """大语言模型集成主系统"""

    def __init__(self):
        self.model_manager = ModelManager()
        self.conversation_manager = ConversationManager()
        self.prompt_templates = PatentPromptTemplates()
        self.request_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_response_time': 0.0,
            'model_usage': {}
        }

        # 初始化默认模型
        self._initialize_default_models()

    def _initialize_default_models(self):
        """初始化默认模型"""
        # 预加载轻量级模型用于快速响应
        # 不在初始化时加载模型，改为按需加载
        logger.info('大语言模型集成系统初始化完成，模型将按需加载')

    async def process_request(self, request: LLMRequest) -> LLMResponse:
        """处理大模型请求"""
        start_time = time.time()

        try:
            self.request_stats['total_requests'] += 1

            # 选择合适的模型
            model_name = self.model_manager.get_model_for_task(
                request.task_type,
                request.model_size
            )

            if not model_name:
                # 尝试加载合适的模型
                await self._load_model_for_task(request.task_type, request.model_size)
                model_name = self.model_manager.get_model_for_task(
                    request.task_type,
                    request.model_size
                )

            if not model_name:
                raise Exception(f"没有可用的模型处理任务类型: {request.task_type}")

            # 构建提示词
            prompt = self._build_prompt(request)

            # 生成响应
            output_text, confidence = await self._generate_response(
                model_name,
                prompt,
                request
            )

            processing_time = time.time() - start_time

            # 统计模型使用
            if model_name not in self.request_stats['model_usage']:
                self.request_stats['model_usage'][model_name] = 0
            self.request_stats['model_usage'][model_name] += 1

            # 更新统计信息
            self._update_stats(processing_time, True)

            return LLMResponse(
                request_id=request.request_id,
                task_type=request.task_type,
                output_text=output_text,
                confidence=confidence,
                model_used=model_name,
                tokens_used=len(output_text.split()),
                processing_time=processing_time,
                metadata=request.metadata
            )

        except Exception as e:
            processing_time = time.time() - start_time
            self._update_stats(processing_time, False)
            logger.error(f"处理请求失败 {request.request_id}: {str(e)}")

            return LLMResponse(
                request_id=request.request_id,
                task_type=request.task_type,
                output_text=f"处理失败: {str(e)}",
                confidence=0.0,
                model_used='none',
                tokens_used=0,
                processing_time=processing_time,
                metadata={'error': str(e)}
            )

    def _build_prompt(self, request: LLMRequest) -> str:
        """构建提示词"""
        if request.task_type == TaskType.PATENT_ANALYSIS:
            analysis_type = request.context.get('analysis_type', 'comprehensive') if request.context else 'comprehensive'
            patent_text = request.context.get('patent_text', request.input_text) if request.context else request.input_text
            return self.prompt_templates.patent_analysis_template(patent_text, analysis_type)

        elif request.task_type == TaskType.QUESTION_ANSWERING:
            patent_context = request.context.get('patent_context', '') if request.context else ''
            return self.prompt_templates.patent_qa_template(request.input_text, patent_context)

        elif request.task_type == TaskType.COMPARISON:
            patent1 = request.context.get('patent1', '') if request.context else ''
            patent2 = request.context.get('patent2', '') if request.context else ''
            return self.prompt_templates.patent_comparison_template(patent1, patent2)

        elif request.task_type == TaskType.REPORT_GENERATION:
            patents_data = request.context.get('patents_data', []) if request.context else []
            report_type = request.context.get('report_type', 'analysis') if request.context else 'analysis'
            return self.prompt_templates.patent_report_template(patents_data, report_type)

        else:
            # 默认提示词
            return f"""
任务类型：{request.task_type.value}
输入内容：{request.input_text}

请提供专业、准确的分析和回答。
"""

    async def _generate_response(self, model_name: str, prompt: str, request: LLMRequest) -> Tuple[str, float]:
        """生成模型响应"""
        if model_name not in self.model_manager.pipelines:
            raise Exception(f"模型未加载: {model_name}")

        pipeline = self.model_manager.pipelines[model_name]

        # 配置生成参数
        generation_config = GenerationConfig(
            max_new_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            top_k=request.top_k,
            do_sample=True,
            pad_token_id=151643,  # chatglm特殊token
            eos_token_id=151643
        )

        # 生成响应
        outputs = pipeline(
            prompt,
            generation_config=generation_config,
            num_return_sequences=1,
            return_full_text=False
        )

        response_text = outputs[0]['generated_text'].strip()
        confidence = self._calculate_confidence(response_text, model_name)

        return response_text, confidence

    def _calculate_confidence(self, text: str, model_name: str) -> float:
        """计算响应置信度"""
        # 简单的置信度计算，基于文本长度和模型性能
        base_confidence = 0.8

        # 根据文本长度调整
        length_factor = min(len(text) / 100, 1.0)

        # 根据模型类型调整
        model_adjustment = {
            'baichuan2-7b': 0.1,
            'qwen-7b': 0.1,
            'chatglm3-6b': 0.05,
            'minichat-2b': -0.1
        }.get(model_name, 0.0)

        confidence = base_confidence + length_factor * 0.1 + model_adjustment
        return max(0.0, min(1.0, confidence))

    async def _load_model_for_task(self, task_type: TaskType, model_size: ModelSize):
        """为任务类型加载模型"""
        # 根据任务类型和模型大小选择最佳模型
        model_preferences = {
            ModelSize.SMALL: ['minichat-2b'],
            ModelSize.MEDIUM: ['chatglm3-6b'],
            ModelSize.LARGE: ['baichuan2-7b', 'qwen-7b'],
            ModelSize.XLARGE: ['baichuan2-7b']
        }

        preferred_models = model_preferences.get(model_size, [])

        for model_name in preferred_models:
            if await self.model_manager.load_model(model_name):
                break

    def _update_stats(self, processing_time: float, success: bool):
        """更新统计信息"""
        if success:
            self.request_stats['successful_requests'] += 1
        else:
            self.request_stats['failed_requests'] += 1

        # 更新平均响应时间
        total = self.request_stats['total_requests']
        current_avg = self.request_stats['average_response_time']
        self.request_stats['average_response_time'] = (
            (current_avg * (total - 1) + processing_time) / total
        )

    async def start_conversation(self, user_id: str, patent_context: Optional[Dict[str, Any]] = None) -> str:
        """开始新对话"""
        return self.conversation_manager.create_conversation(user_id, patent_context)

    async def send_message(self, conversation_id: str, message: str) -> str:
        """发送消息并获取回复"""
        # 添加用户消息
        self.conversation_manager.add_message(conversation_id, 'user', message)

        # 获取对话上下文
        context = self.conversation_manager.get_conversation(conversation_id)
        if not context:
            return '对话不存在'

        # 构建请求
        request = LLMRequest(
            request_id=str(uuid.uuid4()),
            task_type=TaskType.QUESTION_ANSWERING,
            input_text=message,
            context={
                'patent_context': json.dumps(context.patent_context) if context.patent_context else '',
                'conversation_history': self.conversation_manager.get_conversation_history(conversation_id, 5)
            }
        )

        # 处理请求
        response = await self.process_request(request)

        # 添加助手回复
        self.conversation_manager.add_message(conversation_id, 'assistant', response.output_text)

        return response.output_text

    async def analyze_patent(self, patent_text: str, analysis_type: str = 'comprehensive') -> str:
        """分析专利"""
        request = LLMRequest(
            request_id=str(uuid.uuid4()),
            task_type=TaskType.PATENT_ANALYSIS,
            input_text=patent_text,
            context={
                'patent_text': patent_text,
                'analysis_type': analysis_type
            },
            model_size=ModelSize.LARGE
        )

        response = await self.process_request(request)
        return response.output_text

    async def generate_patent_report(self, patents_data: List[Dict[str, Any]], report_type: str = 'analysis') -> str:
        """生成专利报告"""
        request = LLMRequest(
            request_id=str(uuid.uuid4()),
            task_type=TaskType.REPORT_GENERATION,
            input_text='生成专利报告',
            context={
                'patents_data': patents_data,
                'report_type': report_type
            },
            model_size=ModelSize.LARGE,
            max_tokens=2048
        )

        response = await self.process_request(request)
        return response.output_text

    async def compare_patents(self, patent1: str, patent2: str) -> str:
        """对比两个专利"""
        request = LLMRequest(
            request_id=str(uuid.uuid4()),
            task_type=TaskType.COMPARISON,
            input_text='专利对比分析',
            context={
                'patent1': patent1,
                'patent2': patent2
            },
            model_size=ModelSize.LARGE,
            max_tokens=1024
        )

        response = await self.process_request(request)
        return response.output_text

    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        return {
            'request_stats': self.request_stats,
            'loaded_models': [
                {
                    'name': name,
                    'status': status
                }
                for name, status in self.model_manager.model_status.items()
                if status.get('loaded', False)
            ],
            'active_conversations': len(self.conversation_manager.conversations)
        }

    def export_conversation(self, conversation_id: str) -> Dict[str, Any] | None:
        """导出对话记录"""
        context = self.conversation_manager.get_conversation(conversation_id)
        if not context:
            return None

        return {
            'conversation_id': context.conversation_id,
            'user_id': context.user_id,
            'created_at': context.created_at.isoformat(),
            'updated_at': context.updated_at.isoformat(),
            'current_topic': context.current_topic,
            'patent_context': context.patent_context,
            'history': context.history,
            'preferences': context.preferences
        }


# 创建全局实例
llm_integration = LargeLanguageModelIntegration()


# 使用示例和测试
async def test_llm_integration():
    """测试大语言模型集成"""
    logger.info('🧠 测试大语言模型集成系统')

    # 1. 测试专利分析
    test_patent = """
    本发明公开了一种基于人工智能的专利审查方法，包括以下步骤：
    1. 获取待审查专利文本；
    2. 使用自然语言处理技术提取专利特征；
    3. 基于机器学习模型进行新颖性判断；
    4. 输出审查结果和修改建议。
    """

    logger.info("\n📋 测试专利分析...")
    analysis_result = await llm_integration.analyze_patent(test_patent, 'technical_value')
    print('分析结果:', analysis_result[:200] + '...' if len(analysis_result) > 200 else analysis_result)

    # 2. 测试对话功能
    logger.info("\n💬 测试对话功能...")
    conversation_id = await llm_integration.start_conversation('test_user')

    response1 = await llm_integration.send_message(
        conversation_id,
        '请解释一下专利的新颖性要求'
    )
    print('AI回复1:', response1[:150] + '...' if len(response1) > 150 else response1)

    response2 = await llm_integration.send_message(
        conversation_id,
        '那创造性呢？有什么区别？'
    )
    print('AI回复2:', response2[:150] + '...' if len(response2) > 150 else response2)

    # 3. 测试专利对比
    logger.info("\n⚖️ 测试专利对比...")
    patent2 = """
    本发明涉及一种智能专利检索系统，通过关键词匹配和语义分析，从专利数据库中检索相关现有技术。
    """

    comparison_result = await llm_integration.compare_patents(test_patent, patent2)
    print('对比结果:', comparison_result[:200] + '...' if len(comparison_result) > 200 else comparison_result)

    # 4. 测试报告生成
    logger.info("\n📊 测试报告生成...")
    patents_data = [
        {'title': 'AI专利审查方法', 'abstract': test_patent},
        {'title': '智能专利检索系统', 'abstract': patent2}
    ]

    report = await llm_integration.generate_patent_report(patents_data, 'analysis')
    print('生成的报告:', report[:200] + '...' if len(report) > 200 else report)

    # 5. 显示系统统计
    logger.info("\n📈 系统统计:")
    stats = llm_integration.get_system_stats()
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    # 运行测试
    asyncio.run(test_llm_integration())