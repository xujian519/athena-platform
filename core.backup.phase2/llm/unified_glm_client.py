#!/usr/bin/env python3
"""
统一GLM客户端 - 支持所有GLM模型
基于GLM Model Selector智能选择模型

Author: Athena平台团队
Date: 2026-04-22
"""

import asyncio
import httpx
import logging
from typing import Any, Dict, List, Optional
from core.llm.glm_model_selector import (
    GLMModelSelector,
    TaskType,
    PerformancePreference,
    get_recommended_model
)

logger = logging.getLogger(__name__)


class UnifiedGLMClient:
    """统一GLM客户端 - 支持所有GLM模型"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://open.bigmodel.cn/api/coding/paas/v4",
        model: Optional[str] = None,
        task_type: TaskType = TaskType.PATENT_DEEP_ANALYSIS,
        preference: PerformancePreference = PerformancePreference.BALANCED
    ):
        """
        初始化统一GLM客户端

        Args:
            api_key: API密钥（如果不提供，从环境变量读取）
            base_url: API基础URL
            model: 指定模型（如果不指定，自动选择）
            task_type: 任务类型（用于自动选择模型）
            preference: 性能偏好（用于自动选择模型）
        """
        # API配置
        if not api_key:
            import os
            api_key = os.getenv("ZHIPUAI_API_KEY")

        if not api_key:
            raise ValueError("未找到API密钥，请设置ZHIPUAI_API_KEY环境变量或传入api_key参数")

        self.api_key = api_key
        self.base_url = base_url.rstrip('/')

        # 模型选择
        self.model_selector = GLMModelSelector()

        if model:
            # 使用指定模型
            self.model = model
        else:
            # 自动选择模型
            self.model = self.model_selector.select_model(task_type, preference)

        # 获取模型信息
        self.model_info = self.model_selector.get_model_info(self.model)

        # 根据模型设置超时时间
        timeout_map = {
            "glm-4-flash": 30,
            "glm-4-air": 60,
            "glm-4-plus": 120,
            "glm-4-0520": 120,
            "glm-4": 120
        }
        self.timeout = timeout_map.get(self.model, 120)

        logger.info(f"✅ 统一GLM客户端初始化完成")
        logger.info(f"   模型: {self.model} ({self.model_info.get('name', 'Unknown')})")
        logger.info(f"   质量: {self.model_info.get('quality', 'Unknown')}")
        logger.info(f"   速度: {self.model_info.get('speed', 'Unknown')}")
        logger.info(f"   端点: {self.base_url}")

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2500,
        response_format: Optional[str] = None
    ) -> str:
        """
        生成文本

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            temperature: 温度参数
            max_tokens: 最大token数
            response_format: 响应格式（可选：json）

        Returns:
            生成的文本
        """
        # 构建消息
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        # 调用API
        return await self._call_api(messages, temperature, max_tokens)

    async def generate_with_usage(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2500
    ) -> Dict[str, Any]:
        """
        生成文本（包含使用统计）

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            temperature: 温度参数
            max_tokens: 最大token数

        Returns:
            包含文本和使用统计的字典
        """
        # 构建消息
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        # 调用API
        content, usage = await self._call_api_with_usage(messages, temperature, max_tokens)

        # 计算成本
        pricing = self.model_info.get('pricing', {})
        input_cost = (usage['prompt_tokens'] / 1000) * pricing.get('input', 0.005)
        output_cost = (usage['completion_tokens'] / 1000) * pricing.get('output', 0.005)

        return {
            'content': content,
            'usage': usage,
            'cost': {
                'input': round(input_cost, 6),
                'output': round(output_cost, 6),
                'total': round(input_cost + output_cost, 6)
            }
        }

    async def _call_api(
        self,
        messages: List[Dict],
        temperature: float,
        max_tokens: int
    ) -> str:
        """调用API（简化版）"""
        result, _ = await self._call_api_with_usage(messages, temperature, max_tokens)
        return result

    async def _call_api_with_usage(
        self,
        messages: List[Dict],
        temperature: float,
        max_tokens: int
    ):
        """调用API（完整版，包含使用统计）"""
        url = f"{self.base_url}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=headers, json=payload)

                if response.status_code != 200:
                    raise Exception(f"API错误: {response.status_code} - {response.text}")

                result = response.json()
                content = result["choices"][0]["message"]["content"]
                usage = result.get("usage", {})

                return content, usage

        except httpx.TimeoutException:
            raise Exception(f"请求超时（{self.timeout}秒）")
        except Exception as e:
            raise Exception(f"API调用失败: {e}")

    def get_model_info(self) -> dict:
        """获取当前模型信息"""
        return self.model_info

    def estimate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        files: int = 1
    ) -> dict:
        """
        估算成本

        Args:
            input_tokens: 输入token数
            output_tokens: 输出token数
            files: 文件数量

        Returns:
            成本估算
        """
        return self.model_selector.estimate_cost(
            self.model,
            input_tokens,
            output_tokens,
            files
        )


# ==================== 便捷函数 ====================

async def quick_generate(
    prompt: str,
    model: str = "glm-4-flash",
    api_key: Optional[str] = None
) -> str:
    """
    快速生成（使用Flash模型）

    Args:
        prompt: 提示词
        model: 模型名称
        api_key: API密钥

    Returns:
            生成的文本
    """
    client = UnifiedGLMClient(api_key=api_key, model=model)
    return await client.generate(prompt)


async def deep_analyze(
    prompt: str,
    system_prompt: Optional[str] = None,
    api_key: Optional[str] = None
) -> str:
    """
    深度分析（使用Plus模型）

    Args:
        prompt: 提示词
        system_prompt: 系统提示词
        api_key: API密钥

    Returns:
        生成的文本
    """
    client = UnifiedGLMClient(
        api_key=api_key,
        task_type=TaskType.PATENT_DEEP_ANALYSIS,
        preference=PerformancePreference.QUALITY
    )
    return await client.generate(prompt, system_prompt)


async def batch_screening(
    prompts: List[str],
    api_key: Optional[str] = None
) -> List[str]:
    """
    批量筛选（使用Air模型）

    Args:
        prompts: 提示词列表
        api_key: API密钥

    Returns:
        生成的文本列表
    """
    client = UnifiedGLMClient(
        api_key=api_key,
        task_type=TaskType.PATENT_SCREENING,
        preference=PerformancePreference.SPEED
    )

    tasks = [client.generate(prompt) for prompt in prompts]
    return await asyncio.gather(*tasks)


# ==================== 使用示例 ====================

if __name__ == "__main__":
    async def example_usage():
        """使用示例"""

        # 示例1：快速生成（Flash模型）
        print("示例1：快速生成")
        result = await quick_generate("请用一句话介绍专利CN109346360A的技术领域")
        print(result)
        print()

        # 示例2：深度分析（Plus模型，自动选择）
        print("示例2：深度分析（自动选择模型）")
        client = UnifiedGLMClient(
            task_type=TaskType.PATENT_DEEP_ANALYSIS,
            preference=PerformancePreference.QUALITY
        )
        print(f"自动选择的模型: {client.model}")
        print(f"模型信息: {client.get_model_info()}")
        print()

        # 示例3：成本估算
        print("示例3：成本估算")
        cost = client.estimate_cost(
            input_tokens=1500,
            output_tokens=400,
            files=169
        )
        print(f"169个文件分析成本估算: ¥{cost['total_cost']:.2f}")
        print(f"  输入成本: ¥{cost['input_cost']:.2f}")
        print(f"  输出成本: ¥{cost['output_cost']:.2f}")
        print()

        # 示例4：批量处理
        print("示例4：批量筛选（使用Air模型）")
        prompts = [
            "分析专利A的技术领域",
            "分析专利B的技术领域"
        ]
        results = await batch_screening(prompts)
        for i, result in enumerate(results, 1):
            print(f"结果{i}: {result[:50]}...")

    # 运行示例
    asyncio.run(example_usage())
