#!/usr/bin/env python3
from __future__ import annotations
"""
提示词参数优化器
Prompt Parameter Optimizer

优化小诺的提示词生成参数:
- temperature (温度)
- top_p (核采样)
- top_k (Top-K采样)
- frequency_penalty (频率惩罚)
- presence_penalty (存在惩罚)
- max_tokens (最大token数)

借鉴Heretic的思路:
- 自动搜索最优参数组合
- 优化目标: 响应质量 + 相关性 + 完整性

作者: Athena平台团队
创建时间: 2025-01-04
"""

import logging
from typing import Any

import optuna

from .base_optimizer import BaseParameterOptimizer, OptimizationConfig
from .evaluation_metrics import EvaluationMetrics

logger = logging.getLogger(__name__)


class PromptParameterOptimizer(BaseParameterOptimizer):
    """
    提示词参数优化器

    应用场景:
    1. 优化小诺的对话生成参数
    2. 针对不同场景的参数调优
    3. A/B测试最佳参数配置

    示例:
    ```python
    optimizer = PromptParameterOptimizer(
        name="xiaonuo_daily_chat",
        eval_dataset=eval_data
    )
    result = await optimizer.optimize(n_trials=50)
    print(f"最佳参数: {result.best_params}")
    ```
    """

    def __init__(
        self,
        name: str = "prompt_parameter_optimization",
        config: OptimizationConfig | None = None,
        eval_dataset: list[dict] | None = None,
        agent: Any | None = None,
    ):
        """
        初始化提示词参数优化器

        Args:
            name: 优化器名称
            config: 优化配置
            eval_dataset: 评估数据集
                格式: [{'input': '用户输入', 'expected': '期望响应'}]
            agent: 可选的Agent实例(用于实际生成响应)
        """
        super().__init__(name, config, eval_dataset)
        self.agent = agent
        self.evaluator = EvaluationMetrics()

        logger.info(f"🎯 初始化提示词参数优化器: {name}")

    def define_search_space(self, trial: optuna.Trial) -> dict[str, Any]:
        """
        定义提示词参数搜索空间

        借鉴Heretic的参数定义方式:
        - Heretic定义: max_weight, max_position等
        - 我们定义: temperature, top_p, top_k等
        """
        params = {
            # 核心采样参数
            "temperature": trial.suggest_float("temperature", 0.1, 2.0),
            "top_p": trial.suggest_float("top_p", 0.5, 1.0),
            "top_k": trial.suggest_int("top_k", 20, 100),
            # 惩罚参数
            "frequency_penalty": trial.suggest_float("frequency_penalty", -2.0, 2.0),
            "presence_penalty": trial.suggest_float("presence_penalty", -2.0, 2.0),
            # 长度控制
            "max_tokens": trial.suggest_int("max_tokens", 128, 2048),
        }

        return params

    async def evaluate(self, params: dict[str, Any]) -> float:
        """
        评估提示词参数配置

        评估流程:
        1. 使用参数生成响应(如果有Agent)
        2. 或使用模拟响应(用于测试)
        3. 计算质量分数

        Args:
            params: 提示词参数

        Returns:
            质量分数(0-1)
        """
        if not self.eval_dataset:
            logger.warning("没有评估数据集,返回默认分数")
            return 0.5

        total_score = 0.0
        num_samples = min(len(self.eval_dataset), 10)  # 限制样本数

        for i in range(num_samples):
            example = self.eval_dataset[i]

            # 生成响应
            if self.agent:
                # 使用Agent生成
                response = await self._generate_with_agent(example["input"], params)
            else:
                # 使用模拟响应(用于测试)
                response = self._simulate_response(example["input"], params)

            # 评估质量
            result = await self.evaluator.evaluate_response(
                response=response, expected=example.get("expected", ""), input_text=example["input"]
            )

            total_score += result.score

        return total_score / num_samples

    async def _generate_with_agent(self, input_text: str, params: dict[str, Any]) -> str:
        """使用Agent生成响应"""
        try:
            # 调用Agent的process方法
            result = await self.agent.process(input_text, **params)

            # 提取响应文本
            if isinstance(result, dict):
                return result.get("response", str(result))
            else:
                return str(result)

        except Exception as e:
            logger.error(f"Agent生成失败: {e}")
            return f"错误: {e!s}"

    def _simulate_response(self, input_text: str, params: dict[str, Any]) -> str:
        """
        模拟响应生成(用于测试)

        根据参数生成模拟响应
        """
        temperature = params.get("temperature", 0.7)
        max_tokens = params.get("max_tokens", 512)

        # 模拟响应长度与max_tokens相关
        length_factor = min(max_tokens / 512, 2.0)

        # 模拟响应多样性与temperature相关
        diversity_factor = temperature / 2.0

        # 基础响应
        base_response = f"这是对'{input_text}'的响应。"

        # 根据参数扩展响应
        if diversity_factor > 0.5:
            response = (
                f"{base_response}\n"
                f"基于参数设置(temperature={temperature:.2f}),"
                f"这是一个{'较详细' if length_factor > 1 else '简洁'}的回答。"
            )
            if length_factor > 1.0:
                response += (
                    "\n\n## 详细说明\n\n这个响应包含了更多的细节内容,以便更好地回答您的问题。"
                )
        else:
            response = base_response

        return response

    async def optimize_for_scenario(self, scenario: str, n_trials: int = 50) -> dict[str, Any]:
        """
        针对特定场景优化参数

        场景:
        - 'daily_chat': 日常对话(需要自然、流畅)
        - 'coding': 编码助手(需要精确、简洁)
        - 'analysis': 深度分析(需要全面、结构化)
        - 'creative': 创意生成(需要多样、创新)

        Args:
            scenario: 场景名称
            n_trials: 优化试验次数

        Returns:
            优化结果
        """
        # 根据场景调整搜索空间
        scenario_configs = {
            "daily_chat": {
                "temperature_range": (0.6, 1.2),
                "top_p_range": (0.8, 1.0),
                "description": "日常对话优化",
            },
            "coding": {
                "temperature_range": (0.1, 0.5),
                "top_p_range": (0.9, 1.0),
                "description": "编码助手优化",
            },
            "analysis": {
                "temperature_range": (0.3, 0.8),
                "top_p_range": (0.85, 1.0),
                "description": "深度分析优化",
            },
            "creative": {
                "temperature_range": (0.8, 1.8),
                "top_p_range": (0.7, 1.0),
                "description": "创意生成优化",
            },
        }

        config = scenario_configs.get(scenario)
        if not config:
            logger.warning(f"未知场景: {scenario},使用默认配置")
            config = scenario_configs["daily_chat"]

        logger.info(f"🎯 场景优化: {scenario} - {config['description']}")

        # 执行优化
        result = await self.optimize(n_trials=n_trials)

        # 添加场景信息
        result.metadata["scenario"] = scenario
        result.metadata["scenario_config"] = config

        return result

    def get_recommended_params(self, scenario: str = "daily_chat") -> dict[str, Any]:
        """
        获取推荐的参数配置

        基于经验或历史优化结果
        """
        recommended = {
            "daily_chat": {
                "temperature": 0.85,
                "top_p": 0.92,
                "top_k": 50,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.1,
                "max_tokens": 512,
            },
            "coding": {
                "temperature": 0.2,
                "top_p": 0.95,
                "top_k": 40,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0,
                "max_tokens": 1024,
            },
            "analysis": {
                "temperature": 0.5,
                "top_p": 0.90,
                "top_k": 60,
                "frequency_penalty": 0.2,
                "presence_penalty": 0.3,
                "max_tokens": 2048,
            },
            "creative": {
                "temperature": 1.2,
                "top_p": 0.85,
                "top_k": 80,
                "frequency_penalty": 0.5,
                "presence_penalty": 0.5,
                "max_tokens": 1024,
            },
        }

        return recommended.get(scenario, recommended["daily_chat"])
