#!/usr/bin/env python3
from __future__ import annotations
"""
声明式Agent适配器

将从.md文件加载的声明式Agent定义为可调用的工具函数。

Author: Athena平台团队
创建时间: 2026-04-21
"""

import json
import logging
from typing import Any

from core.agents.declarative.models import AgentDefinition
from core.llm.unified_llm_manager import get_unified_llm_manager

logger = logging.getLogger(__name__)


class AgentAdapter:
    """
    声明式Agent适配器

    将AgentDefinition转换为可调用的函数，支持通过FunctionCallingSystem调用。

    工作流程:
    1. 接收用户输入参数
    2. 构建LLM输入（system_prompt + user_input）
    3. 调用UnifiedLLMManager
    4. 解析LLM响应
    5. 返回结构化结果
    """

    def __init__(self, agent_def: AgentDefinition):
        """
        初始化Agent适配器

        Args:
            agent_def: Agent定义对象
        """
        self.agent_def = agent_def
        self.agent_name = agent_def.name
        self.description = agent_def.description
        self.system_prompt = agent_def.system_prompt
        self.model = agent_def.model
        self.tools = agent_def.tools

        logger.info(f"✅ Agent适配器创建: {self.agent_name} (model={self.model})")

    async def __call__(self, task: str, context: Optional[dict[str, Any]] = None, **kwargs) -> dict[str, Any]:
        """
        调用Agent处理任务

        Args:
            task: 任务描述
            context: 上下文信息
            **kwargs: 额外参数

        Returns:
            Agent执行结果
        """
        context = context or {}
        start_time = __import__('time').time()

        try:
            logger.info(f"🤖 调用Agent: {self.agent_name} - {task[:100]}...")

            # 1. 构建LLM输入
            input_text = self._prepare_input(task, context, kwargs)

            # 2. 调用LLM
            response = await self._call_llm(input_text)

            # 3. 解析响应
            result = self._parse_response(response)

            # 4. 添加元数据
            execution_time = __import__('time').time() - start_time
            result["metadata"] = {
                "agent_name": self.agent_name,
                "agent_type": "declarative",
                "model": self.model,
                "execution_time": execution_time,
                "timestamp": __import__('datetime').datetime.now().isoformat(),
            }

            logger.info(f"✅ Agent调用完成: {self.agent_name} (耗时={execution_time:.2f}s)")

            return result

        except Exception as e:
            logger.error(f"❌ Agent调用失败: {self.agent_name} - {e}")
            execution_time = __import__('time').time() - start_time

            return {
                "success": False,
                "error": str(e),
                "agent_name": self.agent_name,
                "metadata": {
                    "agent_name": self.agent_name,
                    "agent_type": "declarative",
                    "execution_time": execution_time,
                }
            }

    def _prepare_input(self, task: str, context: dict[str, Any], kwargs: dict[str, Any]) -> str:
        """
        准备LLM输入

        Args:
            task: 任务描述
            context: 上下文信息
            kwargs: 额外参数

        Returns:
            格式化的输入文本
        """
        # 构建输入部分
        parts = []

        # 添加任务
        parts.append(f"## 任务\n{task}")

        # 添加上下文
        if context:
            parts.append(f"\n## 上下文\n```json\n{json.dumps(context, ensure_ascii=False, indent=2)}\n```")

        # 添加额外参数
        if kwargs:
            parts.append(f"\n## 额外信息\n```json\n{json.dumps(kwargs, ensure_ascii=False, indent=2)}\n```")

        return "\n".join(parts)

    async def _call_llm(self, input_text: str) -> str:
        """
        调用LLM生成响应

        Args:
            input_text: 输入文本

        Returns:
            LLM响应文本
        """
        try:
            # 获取LLM管理器
            llm_manager = await get_unified_llm_manager()

            # 构建完整提示词
            full_prompt = f"{self.system_prompt}\n\n{input_text}"

            # 调用LLM（使用正确的参数名）
            from core.llm.base import LLMRequest
            request = LLMRequest(
                message=full_prompt,  # 注意：使用message而不是prompt
                task_type="general",
                context={"agent_name": self.agent_name},
            )

            response = await llm_manager.generate_async(request)

            return response.content

        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            raise

    def _parse_response(self, response: str) -> dict[str, Any]:
        """
        解析LLM响应

        Args:
            response: LLM响应文本

        Returns:
            解析后的结果字典
        """
        # 尝试解析JSON
        try:
            # 查找JSON代码块
            if "```json" in response:
                # 提取JSON代码块
                start = response.find("```json") + 7
                end = response.find("```", start)
                json_str = response[start:end].strip()
                result = json.loads(json_str)

                # 添加success标志
                result["success"] = True
                return result

            elif "```" in response:
                # 提取代码块
                start = response.find("```") + 3
                end = response.find("```", start)
                code_str = response[start:end].strip()
                result = json.loads(code_str)

                result["success"] = True
                return result

            else:
                # 直接解析整个响应
                result = json.loads(response)
                result["success"] = True
                return result

        except json.JSONDecodeError:
            # JSON解析失败，返回文本响应
            logger.warning(f"JSON解析失败，返回文本响应")

            return {
                "success": True,
                "type": "text",
                "content": response,
                "raw_response": response
            }

    def to_tool_definition(self) -> dict[str, Any]:
        """
        转换为工具定义（用于FunctionCallingSystem注册）

        Returns:
            工具定义字典
        """
        return {
            "name": self.agent_name,
            "description": self.description,
            "category": "agent",
            "metadata": {
                "type": "declarative",
                "model": self.model,
                "tools": self.tools,
                "system_prompt_length": len(self.system_prompt)
            }
        }
