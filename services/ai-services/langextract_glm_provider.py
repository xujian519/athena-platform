#!/usr/bin/env python3
"""
LangExtract GLM模型适配器
将LangExtract与GLM模型深度集成，提供本地化AI能力
"""

import asyncio
import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class GLMModelType(Enum):
    """GLM模型类型"""
    GLM_4_FLASH = 'glm-4-flash'
    GLM_4_AIR = 'glm-4-air'
    GLM_4_PLUS = 'glm-4-plus'
    CHATGLM_3_6B = 'chatglm3-6b'
    CHATGLM_3_130B = 'chatglm3-130b'
    CODEGEEX_2_6B = 'codegeex2-6b'


@dataclass
class GLMModelConfig:
    """GLM模型配置"""
    model_type: GLMModelType
    api_key: str
    base_url: str | None = None
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 0.9
    timeout: int = 60
    retry_count: int = 3
    cost_per_1k_tokens: float = 0.01  # 成本计算
    performance_weight: float = 1.0  # 性能权重


@dataclass
class ExtractionRequest:
    """提取请求"""
    text_or_documents: str | list[str]
    prompt_description: str
    examples: list[Any] | None = None
    extraction_type: str = 'structured_extraction'
    complexity: str = 'medium'
    priority: int = 1
    cost_budget: float | None = None


@dataclass
class ExtractionResult:
    """提取结果"""
    success: bool
    extractions: list[dict[str, Any] = field(default_factory=list)
    raw_response: str = ''
    model_used: str = ''
    tokens_used: int = 0
    processing_time: float = 0.0
    cost: float = 0.0
    confidence_score: float = 0.0
    error: str | None = None


class GLMLangExtractProvider:
    """GLM LangExtract提供商"""

    def __init__(self):
        """初始化GLM提供商"""
        self.models = {}
        self.default_model = GLMModelType.GLM_4_FLASH
        self.performance_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'total_tokens_used': 0,
            'total_cost': 0.0,
            'average_response_time': 0.0
        }

        # 初始化模型配置
        self._initialize_models()

        logger.info('GLM LangExtract提供商初始化完成')

    def _initialize_models(self) -> Any:
        """初始化GLM模型配置"""
        # 检查环境变量中的API配置
        import os

        glm_api_key = os.environ.get('GLM_API_KEY', '')
        if not glm_api_key:
            logger.warning('未设置GLM_API_KEY环境变量，将使用模拟模式')

        base_url = os.environ.get('GLM_BASE_URL', 'https://open.bigmodel.cn/api/paas/v4/')

        # 配置各种GLM模型
        self.models = {
            GLMModelType.GLM_4_FLASH: GLMModelConfig(
                model_type=GLMModelType.GLM_4_FLASH,
                api_key=glm_api_key,
                base_url=base_url,
                temperature=0.7,
                max_tokens=4096,
                cost_per_1k_tokens=0.01,
                performance_weight=0.9  # 高性能
            ),
            GLMModelType.GLM_4_AIR: GLMModelConfig(
                model_type=GLMModelType.GLM_4_AIR,
                api_key=glm_api_key,
                base_url=base_url,
                temperature=0.5,
                max_tokens=8192,
                cost_per_1k_tokens=0.02,
                performance_weight=0.8  # 平衡性能和成本
            ),
            GLMModelType.GLM_4_PLUS: GLMModelConfig(
                model_type=GLMModelType.GLM_4_PLUS,
                api_key=glm_api_key,
                base_url=base_url,
                temperature=0.3,
                max_tokens=16384,
                cost_per_1k_tokens=0.05,
                performance_weight=0.6  # 高质量，成本较高
            ),
            GLMModelType.CHATGLM_3_6B: GLMModelConfig(
                model_type=GLMModelType.CHATGLM_3_6B,
                api_key=glm_api_key,
                base_url=base_url,
                temperature=0.8,
                max_tokens=2048,
                cost_per_1k_tokens=0.005,
                performance_weight=0.7  # 轻量级
            )
        }

    async def extract_with_glm(
        self,
        request: ExtractionRequest,
        preferred_model: GLMModelType | None = None
    ) -> ExtractionResult:
        """使用GLM进行信息提取"""
        start_time = datetime.now()

        try:
            # 选择最佳模型
            selected_model = await self._select_optimal_model(request, preferred_model)
            model_config = self.models[selected_model]

            logger.info(f"选择模型: {selected_model.value} 进行提取")

            # 构建提示词
            prompt = await self._build_extraction_prompt(request)

            # 调用GLM API
            response = await self._call_glm_api(prompt, model_config)

            # 解析响应
            extractions = await self._parse_extraction_response(response, request)

            # 计算统计信息
            processing_time = (datetime.now() - start_time).total_seconds()
            tokens_used = self._estimate_tokens(prompt + response)
            cost = (tokens_used / 1000) * model_config.cost_per_1k_tokens

            # 计算置信度
            confidence_score = await self._calculate_confidence(extractions, response)

            # 更新性能统计
            self._update_performance_stats(processing_time, tokens_used, cost, True)

            result = ExtractionResult(
                success=True,
                extractions=extractions,
                raw_response=response,
                model_used=selected_model.value,
                tokens_used=tokens_used,
                processing_time=processing_time,
                cost=cost,
                confidence_score=confidence_score
            )

            logger.info(f"GLM提取完成: {len(extractions)}个实体, 耗时: {processing_time:.2f}秒")

            return result

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            self._update_performance_stats(processing_time, 0, 0, False)

            logger.error(f"GLM提取失败: {e}")

            return ExtractionResult(
                success=False,
                processing_time=processing_time,
                error=str(e)
            )

    async def _select_optimal_model(
        self,
        request: ExtractionRequest,
        preferred_model: GLMModelType | None = None
    ) -> GLMModelType:
        """选择最优模型"""
        if preferred_model and preferred_model in self.models:
            # 检查是否符合约束条件
            model_config = self.models[preferred_model]
            if request.cost_budget and model_config.cost_per_1k_tokens > request.cost_budget:
                logger.warning("首选模型成本超预算，自动选择其他模型")
            else:
                return preferred_model

        # 基于任务复杂度和优先级选择模型
        if request.priority >= 3 or request.complexity == 'high':
            # 高优先级或复杂任务使用高质量模型
            return GLMModelType.GLM_4_PLUS

        elif request.complexity == 'medium':
            # 中等复杂度使用平衡模型
            return GLMModelType.GLM_4_AIR

        else:
            # 简单任务使用高性能模型
            return GLMModelType.GLM_4_FLASH

    async def _build_extraction_prompt(self, request: ExtractionRequest) -> str:
        """构建提取提示词"""
        prompt = f"""你是一个专业的信息提取专家。请根据以下要求从文本中提取结构化信息。

任务类型: {request.extraction_type}
复杂度: {request.complexity}

提取要求:
{request.prompt_description}

"""

        # 添加示例
        if request.examples:
            prompt += "\n提取示例:\n"
            for i, example in enumerate(request.examples, 1):
                prompt += f"\n示例{i}:\n"
                if isinstance(example, dict):
                    prompt += f"输入文本: {example.get('text', '')}\n"
                    if 'extractions' in example:
                        prompt += "期望输出:\n"
                        for ext in example['extractions']:
                            if isinstance(ext, dict):
                                class_name = ext.get('extraction_class', 'unknown')
                                text = ext.get('extraction_text', '')
                                attrs = ext.get('attributes', {})
                                prompt += f"- {class_name}: \"{text}\""
                                if attrs:
                                    prompt += f" (属性: {attrs})"
                                prompt += "\n"
                prompt += "\n"

        # 添加输出格式要求
        prompt += """
请严格按照以下JSON格式输出提取结果:
{
  'extractions': [
    {
      'extraction_class': '实体类型',
      'extraction_text': '提取的文本',
      'attributes': {
        '属性名': '属性值'
      },
      'start_char': 开始位置,
      'end_char': 结束位置,
      'confidence': 置信度
    }
  ]
}

现在开始提取以下文本:
"""

        # 添加待提取的文本
        if isinstance(request.text_or_documents, list):
            text = "\n\n".join(request.text_or_documents)
        else:
            text = request.text_or_documents

        prompt += text

        return prompt

    async def _call_glm_api(self, prompt: str, model_config: GLMModelConfig) -> str:
        """调用GLM API"""
        # 这里实现实际的GLM API调用
        # 如果没有API密钥，返回模拟响应
        if not model_config.api_key:
            return await self._simulate_glm_response(prompt)

        try:
            import httpx

            headers = {
                'Authorization': f"Bearer {model_config.api_key}",
                'Content-Type': 'application/json'
            }

            data = {
                'model': model_config.model_type.value,
                'messages': [
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'temperature': model_config.temperature,
                'max_tokens': model_config.max_tokens,
                'top_p': model_config.top_p
            }

            async with httpx.AsyncClient(timeout=model_config.timeout) as client:
                response = await client.post(
                    f"{model_config.base_url}/chat/completions",
                    headers=headers,
                    json=data
                )
                response.raise_for_status()

                result = response.json()
                return result['choices'][0]['message']['content']

        except Exception as e:
            logger.error(f"GLM API调用失败: {e}")
            raise

    async def _simulate_glm_response(self, prompt: str) -> str:
        """模拟GLM响应（用于测试）"""
        # 简单的模拟响应
        mock_response = {
            'extractions': [
                {
                    'extraction_class': 'patent_number',
                    'extraction_text': 'CN202310000000.0',
                    'attributes': {'type': 'patent_id', 'country': 'CN'},
                    'start_char': 0,
                    'end_char': 15,
                    'confidence': 0.95
                },
                {
                    'extraction_class': 'invention_title',
                    'extraction_text': '智能数据处理方法',
                    'attributes': {'language': 'zh', 'type': 'method'},
                    'start_char': 20,
                    'end_char': 30,
                    'confidence': 0.92
                }
            ]
        }

        return json.dumps(mock_response, ensure_ascii=False, indent=2)

    async def _parse_extraction_response(
        self,
        response: str,
        request: ExtractionRequest
    ) -> list[dict[str, Any]:
        """解析提取响应"""
        try:
            # 尝试解析JSON响应
            if response.strip().startswith('{'):
                data = json.loads(response)
                return data.get('extractions', [])
            else:
                # 如果不是JSON格式，尝试从文本中提取
                return await self._extract_from_text(response)

        except json.JSONDecodeError:
            # JSON解析失败，尝试文本提取
            return await self._extract_from_text(response)

    async def _extract_from_text(self, text: str) -> list[dict[str, Any]:
        """从文本中提取结构化信息"""
        # 简单的文本提取逻辑
        extractions = []

        # 提取专利号
        import re
        patent_pattern = r'CN\d{13}\.\d'
        patent_matches = re.findall(patent_pattern, text)
        for match in patent_matches:
            extractions.append({
                'extraction_class': 'patent_number',
                'extraction_text': match,
                'attributes': {'type': 'patent_id', 'country': 'CN'},
                'confidence': 0.9
            })

        # 提取发明名称
        title_pattern = r'发明名称[：:]\s*([^\n\r]+)'
        title_match = re.search(title_pattern, text)
        if title_match:
            extractions.append({
                'extraction_class': 'invention_title',
                'extraction_text': title_match.group(1).strip(),
                'attributes': {'type': 'title'},
                'confidence': 0.85
            })

        return extractions

    def _estimate_tokens(self, text: str) -> int:
        """估算token数量"""
        # 简单估算：中文字符数 * 1.5 + 英文单词数
        chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
        english_words = len(text.split()) - chinese_chars

        return int(chinese_chars * 1.5 + english_words)

    async def _calculate_confidence(
        self,
        extractions: list[dict[str, Any],
        response: str
    ) -> float:
        """计算置信度分数"""
        if not extractions:
            return 0.0

        # 基于提取数量和质量计算置信度
        base_confidence = 0.5
        extraction_bonus = min(len(extractions) * 0.1, 0.3)

        # 检查响应质量
        response_quality = 0.0
        if response.strip():
            response_quality = 0.2

        # 检查提取质量
        extraction_quality = 0.0
        valid_extractions = sum(1 for ext in extractions if ext.get('confidence', 0) > 0.7)
        if extractions:
            extraction_quality = (valid_extractions / len(extractions)) * 0.2

        confidence = base_confidence + extraction_bonus + response_quality + extraction_quality
        return min(confidence, 1.0)

    def _update_performance_stats(
        self,
        processing_time: float,
        tokens_used: int,
        cost: float,
        success: bool
    ):
        """更新性能统计"""
        self.performance_stats['total_requests'] += 1

        if success:
            self.performance_stats['successful_requests'] += 1
            self.performance_stats['total_tokens_used'] += tokens_used
            self.performance_stats['total_cost'] += cost

            # 更新平均响应时间
            current_avg = self.performance_stats['average_response_time']
            successful_count = self.performance_stats['successful_requests']
            new_avg = (current_avg * (successful_count - 1) + processing_time) / successful_count
            self.performance_stats['average_response_time'] = new_avg

    async def get_model_performance(self) -> dict[str, Any]:
        """获取模型性能统计"""
        return {
            'models': {
                model_type.value: {
                    'config': {
                        'temperature': config.temperature,
                        'max_tokens': config.max_tokens,
                        'cost_per_1k_tokens': config.cost_per_1k_tokens,
                        'performance_weight': config.performance_weight
                    },
                    'available': bool(config.api_key)
                }
                for model_type, config in self.models.items()
            },
            'performance_stats': self.performance_stats,
            'recommendations': await self._get_model_recommendations()
        }

    async def _get_model_recommendations(self) -> list[str]:
        """获取模型使用建议"""
        recommendations = []

        stats = self.performance_stats
        success_rate = stats['successful_requests'] / max(stats['total_requests'], 1)
        avg_response_time = stats['average_response_time']

        if success_rate < 0.8:
            recommendations.append('建议检查模型配置，成功率偏低')

        if avg_response_time > 5.0:
            recommendations.append('响应时间较长，考虑使用更快的模型')

        if stats['total_cost'] > 100:
            recommendations.append('成本较高，建议优化模型选择策略')

        if not recommendations:
            recommendations.append('系统运行正常，性能良好')

        return recommendations

    async def batch_extract(
        self,
        requests: list[ExtractionRequest],
        max_concurrent: int = 5
    ) -> list[ExtractionResult]:
        """批量提取"""
        logger.info(f"开始批量提取 {len(requests)} 个请求")

        # 创建信号量控制并发
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_single_request(req):
            async with semaphore:
                return await self.extract_with_glm(req)

        # 并发处理
        tasks = [process_single_request(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常结果
        processed_results = []
        for _i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(
                    ExtractionResult(
                        success=False,
                        error=str(result)
                    )
                )
            else:
                processed_results.append(result)

        successful_count = sum(1 for r in processed_results if r.success)
        logger.info(f"批量提取完成: {successful_count}/{len(processed_results)} 成功")

        return processed_results


# 全局实例
_glm_provider = None

def get_glm_provider() -> GLMLangExtractProvider:
    """获取GLM提供商实例"""
    global _glm_provider
    if _glm_provider is None:
        _glm_provider = GLMLangExtractProvider()
    return _glm_provider
