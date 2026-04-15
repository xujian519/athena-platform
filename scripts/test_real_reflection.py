#!/usr/bin/env python3
"""
真实反思引擎测试脚本
使用Ollama qwen3.5:latest进行真实反思评估
"""

import asyncio
import json
import re
import sys

sys.path.insert(0, '.')

from core.intelligence.reflection_engine import QualityMetric, ReflectionResult
from core.llm.adapters.ollama_adapter import OllamaAdapter, create_ollama_capabilities
from core.llm.base import LLMRequest


def extract_json(response: str) -> str:
    """从响应中提取JSON（处理markdown代码块）"""
    # 尝试markdown代码块
    match = re.search(r'```(?:json)?\s*([\s\S]*?)```', response)
    if match:
        return match.group(1).strip()
    # 尝试直接JSON对象
    match = re.search(r'\{[\s\S]*\}', response)
    if match:
        return match.group(0)
    return response


class OllamaReflectionClient:
    """Ollama反思客户端"""

    def __init__(self, model_id: str = 'qwen3.5:latest'):
        self.model_id = model_id
        self.adapter = None

    async def initialize(self):
        capabilities = create_ollama_capabilities()
        capability = capabilities.get(self.model_id, capabilities.get('qwen3.5'))

        self.adapter = OllamaAdapter(
            model_id=self.model_id,
            capability=capability,
            base_url='http://127.0.0.1:8765'
        )

        return await self.adapter.initialize()

    async def generate_response(self, prompt: str) -> str:
        request = LLMRequest(
            message=prompt,
            task_type='reflection',
            temperature=0.1,
            max_tokens=2000
        )

        response = await self.adapter.generate(request)
        return extract_json(response.content)

    async def close(self):
        if self.adapter:
            await self.adapter.close()


async def main():
    print('=' * 70)
    print('🎯 真实反思引擎验证 - qwen3.5:latest')
    print('=' * 70)

    print()
    print('📦 初始化Ollama客户端...')

    client = OllamaReflectionClient('qwen3.5:latest')

    try:
        if not await client.initialize():
            print('❌ 初始化失败')
            return
        print('✅ 客户端就绪')

        # 测试数据
        original_prompt = '请分析以下专利的技术特征和创新点'

        output = '''该专利(CN202310456789.X)涉及一种基于深度学习的图像识别方法。

主要技术特征：
1. 采用多尺度特征融合网络结构
2. 引入自注意力机制优化特征提取
3. 使用残差连接增强梯度传播

创新点分析：
1. 提出了一种新的多尺度融合策略
2. 优化了注意力机制的计算效率
3. 在ImageNet数据集上取得了95.2%的准确率'''

        # 构建反思提示
        reflection_prompt = f'''你是一个专业的AI输出质量评估专家。请对以下AI输出进行全面评估。

## 原始提示
{original_prompt}

## 输出结果
{output}

## 评估标准
请从以下维度评估输出质量(0-1分):
- accuracy: 准确性
- completeness: 完整性
- clarity: 清晰度
- relevance: 相关性
- usefulness: 有用性
- consistency: 一致性

请严格按以下JSON格式返回:
{{
    "overall_score": 0.85,
    "metric_scores": {{
        "accuracy": 0.9,
        "completeness": 0.8,
        "clarity": 0.88,
        "relevance": 0.92,
        "usefulness": 0.85,
        "consistency": 0.9
    }},
    "feedback": "评估反馈",
    "suggestions": ["建议1", "建议2"],
    "should_refine": true
}}'''

        print()
        print('⏳ 调用 qwen3.5:latest 进行反思评估...')
        print()

        response_json = await client.generate_response(reflection_prompt)

        # 解析结果
        data = json.loads(response_json)

        metric_scores = {}
        for metric in QualityMetric:
            metric_scores[metric] = data.get('metric_scores', {}).get(metric.value, 0.5)

        result = ReflectionResult(
            overall_score=data.get('overall_score', 0.5),
            metric_scores=metric_scores,
            feedback=data.get('feedback', ''),
            suggestions=data.get('suggestions', []),
            should_refine=data.get('should_refine', False),
        )

        # 显示结果
        print('=' * 70)
        print('📊 真实反思评估结果 (qwen3.5:latest)')
        print('=' * 70)
        print(f'🎯 总体评分: {result.overall_score:.2f}')
        print(f'🔄 需要改进: {result.should_refine}')
        print()

        thresholds = {
            QualityMetric.ACCURACY: 0.85,
            QualityMetric.COMPLETENESS: 0.80,
            QualityMetric.CLARITY: 0.85,
            QualityMetric.RELEVANCE: 0.90,
            QualityMetric.USEFULNESS: 0.80,
            QualityMetric.CONSISTENCY: 0.90,
        }

        print('📈 各项指标评分:')
        for metric, score in result.metric_scores.items():
            threshold = thresholds.get(metric, 0.8)
            status = '✅' if score >= threshold else '⚠️'
            print(f'  {status} {metric.value:15}: {score:.2f} (阈值: {threshold})')

        print()
        print('📝 反馈:')
        print(f'  {result.feedback}')
        print()

        print('💡 改进建议:')
        for i, s in enumerate(result.suggestions, 1):
            print(f'  {i}. {s}')

        print()
        print('=' * 70)
        print('✅ 真实反思评估完成!')
        print('=' * 70)

    except json.JSONDecodeError as e:
        print(f'❌ JSON解析错误: {e}')
        print(f'原始响应: {response_json if "response_json" in dir() else "无"}')
    except Exception as e:
        print(f'❌ 错误: {e}')
        import traceback
        traceback.print_exc()
    finally:
        await client.close()
        print('🔌 客户端已关闭')


if __name__ == '__main__':
    asyncio.run(main())
