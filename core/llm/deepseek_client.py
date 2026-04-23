from __future__ import annotations
"""
DeepSeek-R1 API客户端
用于交叉验证引擎
"""

import json
import logging
from dataclasses import dataclass
from typing import Any

try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None

logger = logging.getLogger(__name__)


@dataclass
class DeepSeekResponse:
    """DeepSeek响应"""

    answer: str
    reasoning: str
    confidence: float
    model: str
    tokens_used: int
    raw_response: dict[str, Any]
class DeepSeekClient:
    """DeepSeek-R1客户端"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.deepseek.com/v1",
        model: str = "deepseek-chat",
        timeout: int = 180,
        max_retries: int = 3,
    ):
        if api_key is None:
            # 优先从环境变量读取
            import os

            api_key = os.getenv("DEEPSEEK_API_KEY")

            # 如果环境变量没有,再从配置文件读取
            if not api_key:
                config_path = "/Users/xujian/Athena工作平台/config/domestic_llm_config.json"
                try:
                    with open(config_path) as f:
                        config = json.load(f)
                        api_key = config.get("deepseek_api_key")
                except Exception as e:
                    logger.warning(f"无法从配置文件读取DeepSeek API密钥: {e}")

            # 如果仍然没有API密钥,抛出异常
            if not api_key:
                logger.error(
                    "DeepSeek API密钥未配置。请设置DEEPSEEK_API_KEY环境变量或在配置文件中提供。"
                )
                raise ValueError("DeepSeek API密钥未配置")

        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries

        if AsyncOpenAI is None:
            logger.error("OpenAI SDK未安装,请运行: pip install openai")
            raise ImportError("OpenAI SDK未安装")

        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,  # 添加自动重试
        )

        logger.info(f"✅ DeepSeek客户端初始化完成: {model}")
        logger.info(f"   超时设置: {timeout}秒")
        logger.info(f"   最大重试: {max_retries}次")

    async def reason(
        self,
        problem: str,
        task_type: str = "math_reasoning",
        temperature: float = 0.1,
        max_tokens: int = 4000,
    ) -> DeepSeekResponse:
        """
        推理接口(DeepSeek-R1专门优化数学推理)

        Args:
            problem: 问题文本
            task_type: 任务类型
            temperature: 温度参数(低温度更精确)
            max_tokens: 最大token数

        Returns:
            DeepSeekResponse: 响应结果
        """
        try:
            # 构建系统提示
            system_prompt = self._build_system_prompt(task_type)

            # 调用API
            logger.info(f"📡 DeepSeek 推理中... (模型: {self.model}, 任务类型: {task_type})")

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": problem},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # 解析响应
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if hasattr(response, "usage") else 0

            # DeepSeek-R1 特殊处理:如果有reasoning_content字段
            reasoning_content = ""
            if hasattr(response.choices[0].message, "reasoning_content"):
                reasoning_content = response.choices[0].message.reasoning_content
                answer = content
            else:
                # 手动分离
                reasoning_content, answer = self._parse_reasoning(content)

            # DeepSeek的推理通常更可靠
            confidence = self._estimate_confidence(reasoning_content, tokens_used, model_boost=0.1)

            logger.info(f"✅ DeepSeek 推理完成,使用 {tokens_used} tokens")

            return DeepSeekResponse(
                answer=answer,
                reasoning=reasoning_content,
                confidence=confidence,
                model=self.model,
                tokens_used=tokens_used,
                raw_response=response.model_dump() if hasattr(response, "model_dump") else {},
            )

        except Exception as e:
            logger.error(f"❌ DeepSeek推理失败: {e}")
            raise

    def _build_system_prompt(self, task_type: str) -> str:
        """构建系统提示"""
        # DeepSeek-R1专门优化
        prompt = """你是DeepSeek-R1,Athena平台的数学推理验证专家。

你的专长:
- 复杂数学问题的深度推理
- 多步骤逻辑验证
- 数列递推、证明题等

核心要求:
1. 仔细阅读题目,不要遗漏任何条件
2. 逐步推理,展示完整的思维链
3. 特别注意验证:对递推数列,必须验证n=1,2,3,4,5
4. 如果发现之前的答案有误,明确指出

验证重点:
- 通项公式是否满足递推关系
- 前几项的计算是否正确
- 逻辑推导是否严密
"""

        if task_type == "sequence_problems":
            prompt += """

数列问题特别提醒:
1. 必须计算前5项并验证
2. 不能跳过任何一项的验证
3. 检查指数规律是否真实
4. 用特征方程法求解递推关系
5. 验证最终答案的正确性
"""

        return prompt

    def _parse_reasoning(self, content: str) -> tuple[str, str]:
        """解析推理内容和最终答案"""
        # DeepSeek可能会用特定格式分隔
        # 尝试多种分隔符
        separators = ["\n\n答案:", "\n\n答案:", "\n\n_Final Answer:", "[最终答案]"]

        reasoning = content
        answer = content

        for sep in separators:
            if sep in content:
                parts = content.split(sep, 1)
                reasoning = parts[0]
                answer = sep + parts[1]
                break

        return reasoning, answer

    def _estimate_confidence(
        self, reasoning: str, tokens_used: int, model_boost: float = 0.0
    ) -> float:
        """估算置信度"""
        confidence = 0.5

        # DeepSeek-R1本身有提升
        confidence += model_boost

        # 详细推理过程
        if len(reasoning) > 500:
            confidence += 0.15

        # 包含验证步骤
        if "验证" in reasoning or "检查" in reasoning or "确认" in reasoning:
            confidence += 0.15

        # 合理的token使用
        if 1000 < tokens_used < 3500:
            confidence += 0.1

        # 包含数学符号和公式
        if any(symbol in reasoning for symbol in ["∑", "∏", "∫", "∂", "√"]):
            confidence += 0.05

        return min(confidence, 1.0)

    async def validate(
        self, problem: str, primary_answer: str, task_type: str = "math_reasoning"
    ) -> dict[str, Any]:
        """
        验证模式:检查主模型的答案

        Args:
            problem: 原问题
            primary_answer: 主模型的答案
            task_type: 任务类型

        Returns:
            验证结果字典
        """
        try:
            validation_prompt = f"""请验证以下答案是否正确:

问题:{problem}

待验证的答案:{primary_answer}

请独立思考并给出你的判断:
1. 这个答案是否正确?
2. 如果不正确,错误在哪里?
3. 正确的答案应该是什么?
"""

            logger.info("🔍 DeepSeek-R1 验证模式...")

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是答案验证专家"},
                    {"role": "user", "content": validation_prompt},
                ],
                temperature=0.1,
                max_tokens=2000,
            )

            validation_result = response.choices[0].message.content

            # 简单的肯定/否定分析
            is_correct = "正确" in validation_result or "没错" in validation_result
            has_errors = "错误" in validation_result or "不正确" in validation_result

            return {
                "validation_content": validation_result,
                "is_correct": is_correct and not has_errors,
                "has_errors": has_errors,
                "confidence": 0.9 if is_correct and not has_errors else 0.5,
            }

        except Exception as e:
            logger.error(f"❌ DeepSeek验证失败: {e}")
            return {
                "validation_content": f"验证失败: {e!s}",
                "is_correct": False,
                "has_errors": True,
                "confidence": 0.0,
            }

    async def close(self):
        """关闭客户端"""
        await self.client.close()
        logger.info("🔌 DeepSeek客户端已关闭")


# 单例
_deepseek_client: DeepSeekClient | None = None


def get_deepseek_client() -> DeepSeekClient:
    """获取DeepSeek客户端单例"""
    global _deepseek_client
    if _deepseek_client is None:
        _deepseek_client = DeepSeekClient()
    return _deepseek_client
