#!/usr/bin/env python3

"""
GLM-4.7 LLM客户端
集成GLM-4.7作为Athena平台的大语言模型

功能:
1. 计划生成
2. 工具调用推理
3. 动态调整建议

作者: 小诺·双鱼座
版本: v1.0.0
创建时间: 2025-01-05
"""

import json
import logging
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


class GLM47Client:
    """
    GLM-4.7客户端

    支持通过API调用GLM-4.7模型
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://open.bigmodel.cn/api/paas/v4/",
        model: str = "glm-4-plus",
        timeout: int = 60,
    ):
        """
        初始化GLM-4.7客户端

        Args:
            api_key: API密钥(如果为None,从环境变量读取)
            base_url: API基础URL
            model: 模型名称 (glm-4-plus, glm-4-0520, glm-4-air, etc.)
            timeout: 请求超时时间(秒)
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.timeout = timeout

        # 如果没有提供api_key,尝试从环境变量读取
        if not self.api_key:
            import os

            self.api_key = os.getenv("ZHIPUAI_API_KEY")

        if not self.api_key:
            logger.warning("⚠️ 未找到API密钥,将使用模拟模式")
            self.mock_mode = True
        else:
            self.mock_mode = False

        logger.info(f"🤖 GLM-4.7客户端初始化完成 (模型: {model}, 模拟模式: {self.mock_mode})")

    async def generate_plan(
        self,
        task_description: str,
        context: dict[[[str, Any]]],        available_tools: list[[[dict[str, str]]],
        requirements: Optional[[list[str]]] = None,
        constraints: Optional[[list[str]]] = None,
    ) -> dict[str, Any]:
        """
        使用GLM-4.7生成执行计划

        Args:
            task_description: 任务描述
            context: 任务上下文
            available_tools: 可用工具列表
            requirements: 任务要求
            constraints: 约束条件

        Returns:
            生成的计划(JSON格式)
        """
        logger.info(f"📋 使用GLM-4.7生成计划: {task_description[:50]}...")

        if self.mock_mode:
            return await self._mock_generate_plan(task_description, context, available_tools)

        # 构建提示词
        prompt = self._build_planning_prompt(
            task_description, context, available_tools, requirements, constraints
        )

        try:
            # 调用GLM-4.7 API
            response = await self._call_llm(
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的任务规划专家。你的职责是将用户的复杂任务分解为清晰、可执行的步骤。请严格按照JSON格式输出。",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=2000,
            )

            # 解析响应
            plan_json = self._parse_plan_response(response)

            logger.info("✅ GLM-4.7计划生成成功")
            return plan_json

        except Exception as e:
            logger.error(f"❌ GLM-4.7计划生成失败: {e}", exc_info=True)
            # 降级到模拟模式
            logger.info("⚠️ 降级到模拟模式")
            return await self._mock_generate_plan(task_description, context, available_tools)

    def _build_planning_prompt(
        self,
        task_description: str,
        context: dict[[[str, Any]]],        available_tools: list[[[dict[str, str]]],
        requirements: Optional[[list[str]]] = None,
        constraints: Optional[[list[str]]] = None,
    ) -> str:
        """构建规划提示词"""

        # 格式化可用工具
        tools_str = "\n".join(
            [f"- {tool['name']}: {tool['description']}" for tool in available_tools]
        )

        # 格式化上下文
        context_str = json.dumps(context, ensure_ascii=False, indent=2)

        # 构建提示词
        prompt = f"""
你是一个专业的任务规划专家。请将以下任务分解为清晰的执行步骤。

## 用户任务
{task_description}

## 任务上下文
{context_str}

## 可用工具
{tools_str}

"""

        if requirements:
            prompt += "\n## 任务要求\n"
            for req in requirements:
                prompt += f"- {req}\n"

        if constraints:
            prompt += "\n## 约束条件\n"
            for constraint in constraints:
                prompt += f"- {constraint}\n"

        prompt += """
## 要求
1. 将任务分解为 3-10 个具体、可执行的步骤
2. 每个步骤必须明确要做什么
3. 标注每个步骤需要使用的工具
4. 识别步骤之间的依赖关系
5. 评估每个步骤的成功概率(0-1之间)
6. 预估每个步骤的执行时间(分钟)

## 输出格式
请严格按照以下JSON格式输出(不要添加任何其他文字):

```json
{
  "plan_name": "执行计划的简短名称",
  "plan_description": "计划的总体描述",
  "steps": [
    {
      "step_number": 1,
      "name": "步骤名称",
      "description": "详细描述该步骤要做什么",
      "tool": "工具名称",
      "tool_parameters": {},
      "dependencies": [],
      "confidence": 0.9,
      "estimated_duration_minutes": 5
    }
  ]
}
```

请开始规划:
"""

        return prompt

    async def _call_llm(
        self,
        messages: list[[[dict[str, str]]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        top_p: float = 0.9,
    ) -> str:
        """
        调用GLM-4.7 API

        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            top_p: top_p采样参数

        Returns:
            模型响应文本
        """
        url = f"{self.base_url}chat/completions"

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()

            result = response.json()

            # 提取响应内容
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                raise ValueError(f"无效的响应格式: {result}")

    def _parse_plan_response(self, response: str) -> dict[str, Any]:
        """
        解析LLM的计划响应

        Args:
            response: LLM返回的文本

        Returns:
            解析后的计划JSON
        """
        # 尝试直接解析JSON
        try:
            # 移除可能的markdown代码块标记
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]

            response = response.strip()

            # 解析JSON
            plan_json = json.loads(response)

            # 验证必需字段
            if "steps" not in plan_json:
                raise ValueError("计划缺少steps字段")

            if not isinstance(plan_json["steps"], list):
                raise ValueError("steps必须是列表")

            if len(plan_json["steps"]) == 0:
                raise ValueError("steps不能为空")

            # 为每个步骤添加默认值
            for step in plan_json["steps"]:
                step.setdefault("tool_parameters", {})
                step.setdefault("dependencies", [])
                step.setdefault("confidence", 0.8)
                step.setdefault("estimated_duration_minutes", 5)

            return plan_json

        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            logger.error(f"响应内容: {response}")
            raise ValueError(f"无法解析LLM响应为JSON: {e}") from e

    async def _mock_generate_plan(
        self, task_description: str, context: dict[[[str, Any]]], available_tools: list[[[dict[str, str]]]
    ) -> dict[str, Any]:
        """
        模拟计划生成(用于测试或降级)

        Args:
            task_description: 任务描述
            context: 任务上下文
            available_tools: 可用工具列表

        Returns:
            模拟的计划JSON
        """
        logger.info("🎭 使用模拟模式生成计划")

        # 根据任务描述生成模拟计划
        if "检索" in task_description or "搜索" in task_description:
            return {
                "plan_name": "专利检索与分析计划",
                "plan_description": f"根据用户需求'{task_description}'进行专利检索和分析",
                "steps": [
                    {
                        "step_number": 1,
                        "name": "理解用户需求",
                        "description": f"分析用户的查询意图:{task_description}",
                        "tool": "manual",
                        "tool_parameters": {"instruction": "理解用户查询的真实意图"},
                        "dependencies": [],
                        "confidence": 0.95,
                        "estimated_duration_minutes": 2,
                    },
                    {
                        "step_number": 2,
                        "name": "执行专利检索",
                        "description": "根据提取的关键词进行专利数据库检索",
                        "tool": "patent_search",
                        "tool_parameters": {
                            "query": task_description,
                            "limit": 20,
                            "database": "all",
                        },
                        "dependencies": [1],
                        "confidence": 0.85,
                        "estimated_duration_minutes": 3,
                    },
                    {
                        "step_number": 3,
                        "name": "向量语义检索",
                        "description": "使用向量搜索找到语义相似的专利",
                        "tool": "vector_search",
                        "tool_parameters": {"query": task_description, "top_k": 10},
                        "dependencies": [1],
                        "confidence": 0.80,
                        "estimated_duration_minutes": 2,
                    },
                    {
                        "step_number": 4,
                        "name": "知识图谱关联分析",
                        "description": "查询知识图谱中的相关实体和关系",
                        "tool": "knowledge_graph",
                        "tool_parameters": {"entity": context.get("entity", "专利"), "depth": 2},
                        "dependencies": [1],
                        "confidence": 0.75,
                        "estimated_duration_minutes": 2,
                    },
                    {
                        "step_number": 5,
                        "name": "专利深度分析",
                        "description": "对检索到的专利进行技术分析和创新点识别",
                        "tool": "patent_analysis",
                        "tool_parameters": {
                            "patent_id": "从前述步骤获得",
                            "analysis_type": "comprehensive",
                        },
                        "dependencies": [2, 3, 4],
                        "confidence": 0.90,
                        "estimated_duration_minutes": 10,
                    },
                    {
                        "step_number": 6,
                        "name": "综合生成报告",
                        "description": "整合所有分析结果,生成最终报告",
                        "tool": "data_synthesis",
                        "tool_parameters": {
                            "sources": ["检索结果", "分析结果", "图谱数据"],
                            "output_format": "structured_report",
                        },
                        "dependencies": [5],
                        "confidence": 0.92,
                        "estimated_duration_minutes": 5,
                    },
                ],
            }
        else:
            # 通用任务计划
            return {
                "plan_name": "通用任务执行计划",
                "plan_description": f"执行任务:{task_description}",
                "steps": [
                    {
                        "step_number": 1,
                        "name": "分析任务需求",
                        "description": f"分析任务:{task_description}",
                        "tool": "manual",
                        "tool_parameters": {},
                        "dependencies": [],
                        "confidence": 0.95,
                        "estimated_duration_minutes": 2,
                    },
                    {
                        "step_number": 2,
                        "name": "执行主要任务",
                        "description": "执行用户请求的主要任务",
                        "tool": available_tools[0]["name"] if available_tools else "manual",
                        "tool_parameters": {"query": task_description},
                        "dependencies": [1],
                        "confidence": 0.85,
                        "estimated_duration_minutes": 5,
                    },
                    {
                        "step_number": 3,
                        "name": "生成结果",
                        "description": "整理并返回执行结果",
                        "tool": "manual",
                        "tool_parameters": {},
                        "dependencies": [2],
                        "confidence": 0.90,
                        "estimated_duration_minutes": 2,
                    },
                ],
            }

    async def suggest_adjustment(
        self, failed_step: dict[[[str, Any]]], error_message: str, plan_context: dict[[[str, Any]]]]
    ) -> dict[str, Any]:
        """
        当步骤失败时,使用GLM-4.7生成调整建议

        Args:
            failed_step: 失败的步骤
            error_message: 错误信息
            plan_context: 计划上下文

        Returns:
            调整建议
        """
        logger.info(f"🔄 使用GLM-4.7生成调整建议: {failed_step.get('name')}")

        if self.mock_mode:
            # 模拟调整建议
            return {
                "adjustment_type": "retry_with_alternative",
                "suggestion": f"步骤'{failed_step.get('name')}'失败,建议使用替代方法",
                "alternative_steps": [
                    {
                        "step_number": failed_step.get("step_number", 0) + 0.5,
                        "name": f"替代方案: {failed_step.get('name')}",
                        "description": f"由于原步骤失败({error_message}),尝试使用替代方法",
                        "tool": "manual",
                        "confidence": 0.6,
                        "estimated_duration_minutes": 3,
                    }
                ],
                "confidence": 0.7,
            }

        # 构建提示词
        prompt = f"""
以下任务步骤执行失败:

步骤信息:
- 步骤名称: {failed_step.get('name')}
- 步骤描述: {failed_step.get('description')}
- 使用的工具: {failed_step.get('tool')}
- 工具参数: {json.dumps(failed_step.get('tool_parameters', {}), ensure_ascii=False)}

错误信息:
{error_message}

请分析失败原因并提供调整建议,包括:
1. 失败原因分析
2. 可行的替代方案
3. 是否可以继续执行

请以JSON格式回复:
{{
  "adjustment_type": "retry|skip|alternative|abort",
  "reasoning": "失败原因分析",
  "suggestion": "具体建议",
  "alternative_steps": [...],
  "confidence": 0.8
}}
"""

        try:
            response = await self._call_llm(
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个任务执行专家,擅长分析失败原因并提供解决方案。",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=1000,
            )

            # 解析响应
            # 这里简化处理,实际应该更robust
            return {
                "adjustment_type": "alternative",
                "reasoning": response,
                "suggestion": "根据错误信息调整执行策略",
                "alternative_steps": [],
                "confidence": 0.7,
            }

        except Exception as e:
            logger.error(f"❌ GLM-4.7调整建议生成失败: {e}")
            # 返回默认建议
            return {
                "adjustment_type": "retry",
                "reasoning": "重试失败的步骤",
                "suggestion": f"步骤'{failed_step.get('name')}'失败,建议重试",
                "alternative_steps": [],
                "confidence": 0.5,
            }

    async def identify_parallel_tasks(self, plan: dict[[[[[str, Any]]]]]) -> list[list[int]]:
        """
        识别可以并行执行的任务

        Args:
            plan: 执行计划

        Returns:
            并行任务组列表,每个组包含可以并行执行的步骤编号
        """
        logger.info("🔍 使用GLM-4.7识别并行任务")

        if self.mock_mode:
            # 简单的并行性分析
            steps = plan.get("steps", [])
            parallel_groups = []

            # 找出没有相互依赖的步骤
            for i, step1 in enumerate(steps):
                group = [step1["step_number"]
                deps1 = set(step1.get("dependencies", []))

                for step2 in steps[i + 1 :]:
                    deps2 = set(step2.get("dependencies", []))

                    # 如果两个步骤没有依赖关系,可以并行
                    if step2["step_number"] not in deps1 and step1["step_number"] not in deps2:
                        group.append(step2["step_number"])

                if len(group) > 1:
                    parallel_groups.append(group)

            return parallel_groups

        # 使用LLM分析并行性
        steps = plan.get("steps", [])
        steps_summary = "\n".join(
            [
                f"步骤{s['step_number']}: {s['name']} (依赖: {s.get('dependencies', [])})"
                for s in steps
            ]
        )

        prompt = f"""
分析以下执行计划中的步骤,找出可以并行执行的步骤组:

{steps_summary}

请分析:
1. 哪些步骤之间没有依赖关系,可以并行执行?
2. 将可以并行的步骤分组

请以JSON格式回复:
{{
  "parallel_groups": [
    [1, 2],
    [3, 4]
  ],
  "reasoning": "分析原因"
}}
"""

        try:
            await self._call_llm(
                messages=[
                    {"role": "system", "content": "你是一个任务规划专家,擅长分析任务的并行性。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.5,
                max_tokens=500,
            )

            # 解析响应
            # 简化处理
            return [[1, 2], [3, 4]  # 示例

        except Exception as e:
            logger.error(f"❌ GLM-4.7并行任务识别失败: {e}")
            return []

    def get_model_info(self) -> dict[str, Any]:
        """获取模型信息"""
        return {
            "model": self.model,
            "provider": "Zhipu AI",
            "mock_mode": self.mock_mode,
            "api_key_configured": bool(self.api_key),
            "capabilities": [
                "plan_generation",
                "adjustment_suggestion",
                "parallel_task_identification",
            ],
        }


# 全局实例
glm47_client = None


def get_glm47_client() -> GLM47Client:
    """获取GLM-4.7客户端单例"""
    global glm47_client
    if glm47_client is None:
        glm47_client = GLM47Client()
    return glm47_client

