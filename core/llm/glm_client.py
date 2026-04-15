from __future__ import annotations
"""
GLM-4.7 API客户端
用于主推理引擎
"""

import asyncio
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
class GLMResponse:
    """GLM响应"""

    answer: str
    reasoning: str
    confidence: float
    model: str
    tokens_used: int
    raw_response: dict[str, Any]
class GLMClient:
    """GLM-4.7客户端"""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://open.bigmodel.cn/api/paas/v4",
        model: str = "glm-4.7",
        timeout: int = 60,
    ):
        if api_key is None:
            # 从配置文件读取

            config_path = "/Users/xujian/Athena工作平台/config/domestic_llm_config.json"
            try:
                with open(config_path) as f:
                    config = json.load(f)
                    api_key = config.get("zhipu_api_key")
            except Exception as e:
                logger.error(f"无法读取API密钥: {e}")
                raise

        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.timeout = timeout

        if AsyncOpenAI is None:
            logger.error("OpenAI SDK未安装,请运行: pip install openai")
            raise ImportError("OpenAI SDK未安装")

        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=timeout)

        logger.info(f"✅ GLM客户端初始化完成: {model}")

    async def reason(
        self,
        problem: str,
        task_type: str = "general",
        temperature: float = 0.3,
        max_tokens: int = 4000,
        enable_reasoning: bool = True,
    ) -> GLMResponse:
        """
        推理接口

        Args:
            problem: 问题文本
            task_type: 任务类型
            temperature: 温度参数
            max_tokens: 最大token数
            enable_reasoning: 是否启用推理模式

        Returns:
            GLMResponse: 响应结果
        """
        try:
            # 构建系统提示
            system_prompt = self._build_system_prompt(task_type, enable_reasoning)

            # 调用API
            logger.info(f"📡 GLM-4.7 推理中... (任务类型: {task_type})")

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

            # 分离推理过程和答案
            reasoning, answer = self._parse_response(content, enable_reasoning)

            # 估算置信度
            confidence = self._estimate_confidence(content, tokens_used)

            logger.info(f"✅ GLM-4.7 推理完成,使用 {tokens_used} tokens")

            return GLMResponse(
                answer=answer,
                reasoning=reasoning,
                confidence=confidence,
                model=self.model,
                tokens_used=tokens_used,
                raw_response=response.model_dump() if hasattr(response, "model_dump") else {},
            )

        except Exception as e:
            logger.error(f"❌ GLM推理失败: {e}")
            raise

    def _build_system_prompt(self, task_type: str, enable_reasoning: bool) -> str:
        """构建系统提示"""
        base_prompt = """你是Athena平台的数学推理专家(GLM-4.7)。

你的任务:
1. 仔细分析数学问题
2. 展示完整的推理过程
3. 给出清晰的最终答案

重要提醒:
- 必须验证前几项以确保答案正确
- 对于递推数列问题,至少验证n=1,2,3,4,5
- 如果不确定,明确说明置信度
"""

        if task_type == "sequence_problems":
            base_prompt += """

对于数列递推问题,请遵循以下步骤:
1. 计算前几项(至少5项)
2. 观察规律
3. 建立递推关系
4. 求解通项公式
5. 逐项验证(重要!)
6. 给出最终答案
"""

        return base_prompt

    def _parse_response(self, content: str, enable_reasoning: bool) -> tuple[str, str]:
        """解析响应,分离推理过程和答案"""
        if not enable_reasoning:
            return "", content

        # 尝试分离推理和答案
        # 查找常见的答案标记
        answer_markers = ["最终答案", "答案", "结论", "因此", "综上"]
        reasoning = content
        answer = content

        for marker in answer_markers:
            if marker in content:
                parts = content.split(marker, 1)
                reasoning = parts[0]
                answer = marker + parts[1]
                break

        return reasoning, answer

    def _estimate_confidence(self, content: str, tokens_used: int) -> float:
        """估算置信度"""
        # 基于多个因素估算置信度
        confidence = 0.5

        # 如果包含验证步骤,提高置信度
        if "验证" in content or "检查" in content:
            confidence += 0.2

        # 如果推理过程详细,提高置信度
        if len(content) > 500:
            confidence += 0.1

        # 如果token使用合理,提高置信度
        if 1000 < tokens_used < 3500:
            confidence += 0.1

        return min(confidence, 1.0)

    async def batch_reason(
        self, problems: list[str], task_type: str = "general"
    ) -> list[GLMResponse]:
        """批量推理"""
        logger.info(f"🚀 GLM批量推理: {len(problems)} 个问题")

        tasks = [self.reason(problem, task_type) for problem in problems]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"❌ 问题 {i+1} 推理失败: {result}")
                final_results.append(
                    GLMResponse(
                        answer="",
                        reasoning=f"推理失败: {result!s}",
                        confidence=0.0,
                        model=self.model,
                        tokens_used=0,
                        raw_response={"error": str(result)},
                    )
                )
            else:
                final_results.append(result)

        return final_results

    async def close(self):
        """关闭客户端"""
        await self.client.close()
        logger.info("🔌 GLM客户端已关闭")


# 单例
_glm_client: GLMClient | None = None


def get_glm_client() -> GLMClient:
    """获取GLM客户端单例"""
    global _glm_client
    if _glm_client is None:
        _glm_client = GLMClient()
    return _glm_client
