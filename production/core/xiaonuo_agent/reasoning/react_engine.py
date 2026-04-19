#!/usr/bin/env python3
"""
ReAct推理引擎
实现Think-Act-Observe推理循环

核心思想:
1. Thought(思考):分析当前情况
2. Action(行动):选择并执行行动
3. Observation(观察):观察行动结果
4. 迭代直到完成任务

作者: Athena平台团队
创建时间: 2026-01-22
版本: v2.0.0
"""

from __future__ import annotations
import asyncio
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ThoughtType(Enum):
    """思考类型"""

    ANALYSIS = "analysis"  # 分析
    PLANNING = "planning"  # 规划
    REASONING = "reasoning"  # 推理
    REFLECTION = "reflection"  # 反思
    DECISION = "decision"  # 决策


@dataclass
class Thought:
    """思考步骤"""

    step: int
    thought_type: ThoughtType
    content: str
    confidence: float = 0.5
    evidence: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "step": self.step,
            "type": self.thought_type.value,
            "content": self.content,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "timestamp": self.timestamp,
        }


@dataclass
class Action:
    """行动步骤"""

    step: int
    action_type: str  # 工具类型/函数名
    parameters: dict[str, Any]
    reasoning: str  # 为什么选择这个行动
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "step": self.step,
            "type": self.action_type,
            "parameters": self.parameters,
            "reasoning": self.reasoning,
            "timestamp": self.timestamp,
        }


@dataclass
class Observation:
    """观察结果"""

    step: int
    result: Any
    success: bool
    error_message: str | None = None
    new_information: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "step": self.step,
            "result": str(self.result)[:500],  # 限制长度
            "success": self.success,
            "error": self.error_message,
            "new_info": self.new_information,
            "timestamp": self.timestamp,
        }


@dataclass
class ReActResult:
    """ReAct推理结果"""

    task: str
    thoughts: list[Thought]
    actions: list[Action]
    observations: list[Observation]
    final_answer: str | None = None
    success: bool = False
    error_message: str | None = None
    total_steps: int = 0
    execution_time: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "task": self.task,
            "thoughts": [t.to_dict() for t in self.thoughts],
            "actions": [a.to_dict() for a in self.actions],
            "observations": [o.to_dict() for o in self.observations],
            "final_answer": self.final_answer,
            "success": self.success,
            "error": self.error_message,
            "total_steps": self.total_steps,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp,
        }


class ReActEngine:
    """
    ReAct推理引擎

    实现Think-Act-Observe推理循环:
    1. Thought: 分析当前情况,决定下一步行动
    2. Action: 执行选定的行动
    3. Observation: 观察行动结果
    4. 循环直到任务完成

    特点:
    - 推理过程透明
    - 可解释性强
    - 支持多步推理
    - 自我纠错能力
    """

    def __init__(
        self,
        max_steps: int = 10,
        tools: dict[str, Any] | None = None,
        llm_client: Any | None = None,
    ):
        """
        初始化ReAct推理引擎

        Args:
            max_steps: 最大推理步数
            tools: 可用工具字典 {name: callable}
            llm_client: LLM客户端(用于生成思考)
        """
        self.max_steps = max_steps
        self.tools = tools or {}
        self._llm = llm_client

        # 推理统计
        self.stats = {
            "total_reasonings": 0,
            "successful_reasonings": 0,
            "failed_reasonings": 0,
            "avg_steps": 0.0,
            "avg_time": 0.0,
        }

    async def solve(
        self,
        task: str,
        context: dict[str, Any] | None = None,
        tools: dict[str, Any] | None = None,
    ) -> ReActResult:
        """
        使用ReAct循环解决问题

        Args:
            task: 任务描述
            context: 上下文信息
            tools: 可用工具(覆盖默认)

        Returns:
            推理结果
        """
        start_time = datetime.now()
        context = context or {}

        # 使用提供的工具或默认工具
        available_tools = tools or self.tools

        result = ReActResult(task=task, thoughts=[], actions=[], observations=[])

        try:
            logger.info(f"🧠 开始ReAct推理: {task[:100]}...")

            # 初始思考
            thought = await self._think(task=task, context=context, previous_steps=[], step=1)
            result.thoughts.append(thought)

            # ReAct循环
            for step in range(1, self.max_steps + 1):
                # 1. 分析当前情况,决定行动
                action = await self._decide_action(
                    thought=thought,
                    task=task,
                    available_tools=available_tools,
                    context=context,
                    step=step,
                )
                result.actions.append(action)

                # 2. 执行行动
                observation = await self._execute_action(
                    action=action, available_tools=available_tools, context=context, step=step
                )
                result.observations.append(observation)

                # 3. 观察结果并判断是否完成
                if await self._is_done(observation, task):
                    result.success = True
                    result.final_answer = await self._generate_final_answer(
                        task, result.thoughts, result.observations
                    )
                    break

                # 4. 基于观察结果进行新的思考
                thought = await self._think(
                    task=task,
                    context=context,
                    previous_steps=result.thoughts,
                    observations=result.observations,
                    step=step + 1,
                )
                result.thoughts.append(thought)

                # 检查是否应该放弃
                if await self._should_abort(thought, result.observations):
                    result.error_message = "推理无法继续,可能需要更多信息"
                    break

            result.total_steps = len(result.thoughts)

            # 更新统计
            self.stats["total_reasonings"] += 1
            if result.success:
                self.stats["successful_reasonings"] += 1
            else:
                self.stats["failed_reasonings"] += 1

            execution_time = (datetime.now() - start_time).total_seconds()
            result.execution_time = execution_time

            logger.info(
                f"✅ ReAct推理完成: 步骤={result.total_steps}, 耗时={execution_time:.2f}s, 成功={result.success}"
            )

        except Exception as e:
            logger.error(f"❌ ReAct推理异常: {e}")
            result.success = False
            result.error_message = str(e)

        return result

    async def _think(
        self,
        task: str,
        context: dict[str, Any],        previous_steps: list[Thought],
        observations: list[Observation] | None = None,
        step: int = 1,
    ) -> Thought:
        """
        生成思考

        Args:
            task: 任务
            context: 上下文
            previous_steps: 之前的思考步骤
            observations: 之前的观察结果
            step: 当前步骤

        Returns:
            思考内容
        """
        observations = observations or []

        # 构建思考提示
        prompt = f"""
你是一个AI推理助手。请根据以下信息进行思考:

任务: {task}

上下文:
{json.dumps(context, ensure_ascii=False, indent=2)}

"""

        if previous_steps:
            prompt += "\n之前的思考:\n"
            for t in previous_steps[-3:]:  # 只显示最近3步
                prompt += f"  步骤{t.step}: {t.content}\n"

        if observations:
            prompt += "\n之前的观察:\n"
            for o in observations[-3:]:
                prompt += f"  步骤{o.step}: {o.result}\n"

        prompt += f"""
现在,请进行第{step}步思考。请分析:
1. 当前情况如何?
2. 我们已经知道了什么?
3. 下一步应该做什么?
4. 有什么不确定性?

请用1-2句话简洁地表达你的思考。
"""

        # 如果有LLM,使用LLM生成思考
        if self._llm:
            try:
                llm_response = await self._call_llm(prompt)
                thought_content = self._parse_llm_response(llm_response)
            except Exception as e:
                logger.warning(f"⚠️  LLM调用失败,使用规则生成: {e}")
                thought_content = await self._rule_based_thinking(task, context, observations)
        else:
            # 规则生成思考
            thought_content = await self._rule_based_thinking(task, context, observations)

        # 确定思考类型
        thought_type = self._classify_thought_type(thought_content, step)

        thought = Thought(
            step=step,
            thought_type=thought_type,
            content=thought_content,
            confidence=0.7,  # 默认置信度
            evidence=[],
        )

        logger.debug(f"💭 思考{step}: {thought_content[:100]}...")
        return thought

    async def _decide_action(
        self,
        thought: Thought,
        task: str,
        available_tools: dict[str, Any],        context: dict[str, Any],        step: int,
    ) -> Action:
        """
        决定下一步行动

        Args:
            thought: 当前思考
            task: 任务
            available_tools: 可用工具
            context: 上下文
            step: 步骤

        Returns:
            行动
        """
        # 基于思考内容决定行动类型
        action_prompt = f"""
基于以下思考,决定下一步行动:

思考: {thought.content}

任务: {task}

可用工具: {', '.join(available_tools.keys()) if available_tools else '无'}

请决定:
1. 是否需要使用工具?如果需要,选择哪个工具?
2. 工具的参数是什么?
3. 为什么选择这个行动?

请以JSON格式返回:
{{
    "action_type": "工具名称或'think_only'",
    "parameters": {{"param": "value"}},
    "reasoning": "行动理由"
}}
"""

        # 尝试解析行动决策
        try:
            if self._llm:
                llm_response = await self._call_llm(action_prompt)
                action_decision = json.loads(llm_response)
            else:
                action_decision = await self._rule_based_action_decision(
                    thought, task, available_tools
                )

            # 确保action_decision格式正确
            if "action_type" not in action_decision:
                action_decision["action_type"] = "think_only"
            if "parameters" not in action_decision:
                action_decision["parameters"] = {}
            if "reasoning" not in action_decision:
                action_decision["reasoning"] = "基于思考结果决定"

            action = Action(
                step=step,
                action_type=action_decision["action_type"],
                parameters=action_decision["parameters"],
                reasoning=action_decision["reasoning"],
            )

        except Exception as e:
            logger.warning(f"⚠️  行动决策失败,使用默认: {e}")
            action = Action(
                step=step,
                action_type="think_only",
                parameters={},
                reasoning="无法确定具体行动,继续思考",
            )

        logger.debug(f"🎯 行动{step}: {action.action_type} - {action.reasoning[:50]}...")
        return action

    async def _execute_action(
        self, action: Action, available_tools: dict[str, Any], context: dict[str, Any], step: int
    ) -> Observation:
        """
        执行行动

        Args:
            action: 行动
            available_tools: 可用工具
            context: 上下文
            step: 步骤

        Returns:
            观察结果
        """
        try:
            if action.action_type == "think_only":
                # 纯思考行动,无需执行
                observation = Observation(
                    step=step, result="思考完成", success=True, new_information=[]
                )

            elif action.action_type in available_tools:
                # 执行工具
                tool_func = available_tools[action.action_type]
                result = await self._call_tool(tool_func, action.parameters, context)

                observation = Observation(
                    step=step,
                    result=result,
                    success=True,
                    new_information=self._extract_new_information(result),
                )

            else:
                # 工具不存在
                observation = Observation(
                    step=step,
                    result=None,
                    success=False,
                    error_message=f"工具 '{action.action_type}' 不可用",
                )

        except Exception as e:
            logger.error(f"❌ 行动执行失败: {e}")
            observation = Observation(step=step, result=None, success=False, error_message=str(e))

        logger.debug(
            f"👀 观察{step}: {observation.result if isinstance(observation.result, str) else str(observation.result)[:100]}..."
        )
        return observation

    async def _is_done(self, observation: Observation, task: str) -> bool:
        """
        判断任务是否完成

        Args:
            observation: 最新观察
            task: 原始任务

        Returns:
            是否完成
        """
        # 简单判断:观察成功且包含实质性结果
        if observation.success and observation.result:
            # 检查结果是否足够完整
            result_str = str(observation.result)
            if len(result_str) > 50:  # 有实质内容
                return True

        return False

    async def _should_abort(self, thought: Thought, observations: list[Observation]) -> bool:
        """
        判断是否应该中止推理

        Args:
            thought: 最新思考
            observations: 观察历史

        Returns:
            是否中止
        """
        # 连续失败
        recent_failures = sum(1 for o in observations[-3:] if not o.success)
        if recent_failures >= 2:
            return True

        # 思考中表达困惑
        confusion_keywords = ["不知道", "无法确定", "信息不足", "需要更多信息"]
        return bool(any(kw in thought.content for kw in confusion_keywords))

    async def _generate_final_answer(
        self, task: str, thoughts: list[Thought], observations: list[Observation]
    ) -> str:
        """
        生成最终答案

        Args:
            task: 任务
            thoughts: 思考历史
            observations: 观察历史

        Returns:
            最终答案
        """
        # 收集所有有用信息
        key_info = []

        for obs in observations:
            if obs.success and obs.result:
                result_str = str(obs.result)
                if len(result_str) > 20:
                    key_info.append(result_str)

        # 构建最终答案
        if key_info:
            final_answer = f"基于{len(key_info)}个步骤的推理,我得出以下结论:\n\n"
            final_answer += "\n".join(f"{i+1}. {info}" for i, info in enumerate(key_info[:5]))
        else:
            final_answer = "基于推理过程,我完成了任务分析。"

        return final_answer

    async def _rule_based_thinking(
        self, task: str, context: dict[str, Any], observations: list[Observation]
    ) -> str:
        """基于规则生成思考(备用方案)"""
        if not observations:
            return f"我需要理解任务:{task}。让我分析一下需要做什么。"
        else:
            last_obs = observations[-1]
            if last_obs.success:
                return (
                    f"基于上一步的结果,我已经获得了{str(last_obs.result)[:50]}...,让我继续分析。"
                )
            else:
                return f"上一步遇到了问题:{last_obs.error_message},让我尝试其他方法。"

    async def _rule_based_action_decision(
        self, thought: Thought, task: str, available_tools: dict[str, Any]
    ) -> dict[str, Any]:
        """基于规则决定行动(备用方案)"""
        # 简单规则:如果有工具,尝试使用第一个
        if available_tools:
            tool_name = next(iter(available_tools.keys()))
            return {
                "action_type": tool_name,
                "parameters": {"query": task},
                "reasoning": f"使用{tool_name}来处理任务",
            }
        else:
            return {"action_type": "think_only", "parameters": {}, "reasoning": "继续思考分析"}

    def _classify_thought_type(self, content: str, step: int) -> ThoughtType:
        """分类思考类型"""
        if step == 1:
            return ThoughtType.ANALYSIS
        elif "计划" in content or "步骤" in content:
            return ThoughtType.PLANNING
        elif "因为" in content or "所以" in content:
            return ThoughtType.REASONING
        elif "决定" in content or "选择" in content:
            return ThoughtType.DECISION
        else:
            return ThoughtType.REFLECTION

    def _extract_new_information(self, result: Any) -> list[str]:
        """从结果中提取新信息"""
        # 简化实现:将结果分割成句子
        result_str = str(result)
        sentences = re.split(r"[。!?.!?]", result_str)
        return [s.strip() for s in sentences if len(s.strip()) > 10]

    async def _call_llm(self, prompt: str) -> str:
        """调用LLM(需要实现)"""
        # 这里应该调用实际的LLM API
        # 暂时返回模拟响应
        return f"根据分析,{prompt[:50]}..."

    async def _call_tool(self, tool_func, parameters: dict, context: dict) -> Any:
        """调用工具函数"""
        # 执行工具
        if asyncio.iscoroutinefunction(tool_func):
            return await tool_func(**parameters, **context)
        else:
            return tool_func(**parameters, **context)

    async def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        total = self.stats["total_reasonings"]
        return {
            **self.stats,
            "success_rate": (self.stats["successful_reasonings"] / total if total > 0 else 0),
            "avg_steps": (self.stats["avg_steps"] if total > 0 else 0),
            "avg_time": (self.stats["avg_time"] if total > 0 else 0),
        }


# 便捷函数
async def create_react_engine(**kwargs) -> ReActEngine:
    """创建ReAct推理引擎"""
    return ReActEngine(**kwargs)
