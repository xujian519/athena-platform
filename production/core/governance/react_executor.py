#!/usr/bin/env python3
from __future__ import annotations
"""
Athena ReAct执行引擎
ReAct Executor for Athena Platform

基于ReAct论文(Reasoning + Acting)的实现
实现Thought-Action-Observation循环,提供可解释的工具调用决策

核心功能:
1. Thought: 推理思考,生成决策依据
2. Action: 选择并执行工具
3. Observation: 观察执行结果
4. Reflection: 反思和优化策略

使用方法:
    from core.governance.react_executor import ReActExecutor, get_react_executor

    executor = get_react_executor()
    result = await executor.execute(
        query="搜索关于人工智能的专利",
        context={}
    )
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

# ================================
# 数据模型
# ================================


class ReActStepType(Enum):
    """ReAct步骤类型"""

    THOUGHT = "thought"  # 思考
    ACTION = "action"  # 行动
    OBSERVATION = "observation"  # 观察
    REFLECTION = "reflection"  # 反思
    ANSWER = "answer"  # 最终答案


@dataclass
class ReActStep:
    """ReAct步骤"""

    step_type: ReActStepType
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    tool_id: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)
    result: Any = None
    success: bool = True
    error: str | None = None
    thinking_time: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "step_type": self.step_type.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "tool_id": self.tool_id,
            "parameters": self.parameters,
            "result": str(self.result)[:500] if self.result else None,  # 限制长度
            "success": self.success,
            "error": self.error,
            "thinking_time": self.thinking_time,
        }


@dataclass
class ReActResult:
    """ReAct执行结果"""

    success: bool
    final_answer: str
    steps: list[ReActStep] = field(default_factory=list)
    total_time: float = 0.0
    total_steps: int = 0
    tools_used: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "final_answer": self.final_answer,
            "steps": [step.to_dict() for step in self.steps],
            "total_time": self.total_time,
            "total_steps": self.total_steps,
            "tools_used": self.tools_used,
            "metadata": self.metadata,
        }


# ================================
# ReAct执行引擎
# ================================


class ReActExecutor:
    """
    ReAct执行引擎

    基于ReAct论文的实现,提供可解释的工具调用决策

    核心循环:
    1. Thought: 分析当前状态,思考下一步行动
    2. Action: 选择并执行合适的工具
    3. Observation: 观察工具执行结果
    4. Reflection: 评估结果,决定是否继续

    参考:ReAct: Synergizing Reasoning and Acting in Language Models
    """

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}

        # 最大迭代次数
        self.max_iterations = self.config.get("max_iterations", 10)
        self.max_thinking_time = self.config.get("max_thinking_time", 300)  # 5分钟

        # 工具注册中心(延迟加载)
        self._registry = None

        # 思考模板
        self.thought_templates = {
            "initial": [
                "用户请求: {query}\n"
                "我需要分析这个请求并确定需要使用哪些工具。\n"
                "让我先理解用户的需求..."
            ],
            "tool_selection": [
                "基于当前信息,我需要选择合适的工具。\n"
                "可选工具: {tools}\n"
                "我将使用: {tool},因为: {reason}"
            ],
            "observation": ["工具执行结果: {result}\n" "我需要分析这个结果..."],
            "reflection": [
                "已完成 {iterations} 次迭代。\n"
                "当前进展: {progress}\n"
                "下一步行动: {next_action}"
            ],
            "final": ["经过 {steps} 步推理,我得出以下答案:"],
        }

        # 停止条件
        self.stop_patterns = ["最终答案", "完成", "无法", "失败", "ERROR"]

        logger.info("✅ ReAct执行引擎已创建")

    async def initialize(self) -> bool:
        """初始化ReAct引擎"""
        logger.info("🚀 初始化ReAct执行引擎...")

        try:
            # 获取统一工具注册中心
            from core.governance.unified_tool_registry import get_unified_registry

            self._registry = get_unified_registry()

            # 如果注册中心未初始化,先初始化
            if not self._registry.metadata:
                await self._registry.initialize()

            logger.info("✅ ReAct执行引擎初始化完成")
            return True

        except Exception as e:
            logger.error(f"❌ ReAct引擎初始化失败: {e}")
            return False

    async def execute(
        self,
        query: str,
        context: dict[str, Any] | None = None,
        max_iterations: int | None = None,
    ) -> ReActResult:
        """
        执行ReAct循环

        Args:
            query: 用户查询
            context: 执行上下文
            max_iterations: 最大迭代次数

        Returns:
            ReActResult: 执行结果
        """
        start_time = datetime.now()
        max_iter = max_iterations or self.max_iterations

        logger.info(f"🔍 开始ReAct执行: {query}")

        # 初始化结果
        steps: list[ReActStep] = []
        tools_used: list[str] = []
        context = context or {}

        try:
            # 步骤1: 初始思考
            thought = await self._think_initial(query, context)
            steps.append(thought)

            # ReAct主循环
            for iteration in range(max_iter):
                logger.debug(f"--- 迭代 {iteration + 1}/{max_iter} ---")

                # 检查时间限制
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed > self.max_thinking_time:
                    logger.warning(f"⏱️ 超时限制 ({self.max_thinking_time}s)")
                    steps.append(
                        ReActStep(
                            step_type=ReActStepType.REFLECTION,
                            content=f"达到最大思考时间 ({self.max_thinking_time}s),停止推理",
                        )
                    )
                    break

                # 步骤2: 选择并执行工具
                action_step = await self._decide_and_act(query, context, steps)
                steps.append(action_step)

                if not action_step.success:
                    logger.warning(f"❌ 工具执行失败: {action_step.error}")
                    # 继续尝试其他工具

                if action_step.tool_id and action_step.tool_id not in tools_used:
                    tools_used.append(action_step.tool_id)

                # 步骤3: 观察结果
                observation = await self._observe(action_step, context)
                steps.append(observation)

                # 步骤4: 反思和决策
                reflection = await self._reflect(iteration, steps, context)
                steps.append(reflection)

                # 检查是否应该停止
                if self._should_stop(reflection.content, action_step):
                    logger.info("✅ 达到停止条件")
                    break

            # 步骤5: 生成最终答案
            answer_step = await self._generate_final_answer(steps, context)
            steps.append(answer_step)

            total_time = (datetime.now() - start_time).total_seconds()

            result = ReActResult(
                success=True,
                final_answer=answer_step.content,
                steps=steps,
                total_time=total_time,
                total_steps=len(steps),
                tools_used=tools_used,
                metadata={
                    "iterations": iteration + 1,
                    "query": query,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            logger.info(f"✅ ReAct执行完成,耗时 {total_time:.2f}s,共 {len(steps)} 步")
            return result

        except Exception as e:
            logger.error(f"❌ ReAct执行异常: {e}")
            import traceback

            traceback.print_exc()

            total_time = (datetime.now() - start_time).total_seconds()

            return ReActResult(
                success=False,
                final_answer=f"执行失败: {e!s}",
                steps=steps,
                total_time=total_time,
                total_steps=len(steps),
                tools_used=tools_used,
                metadata={"error": str(e)},
            )

    async def _think_initial(self, query: str, context: dict[str, Any]) -> ReActStep:
        """初始思考"""
        start_time = datetime.now()

        # 生成初始思考内容
        thought_content = self.thought_templates["initial"][0].format(query=query)

        # 尝试发现相关工具
        if self._registry:
            relevant_tools = await self._registry.discover_tools(query, limit=5)
            thought_content += "\n\n发现的相关工具:\n"
            for tool in relevant_tools:
                thought_content += f"  - {tool['name']}: {tool['description']}\n"

        thinking_time = (datetime.now() - start_time).total_seconds()

        return ReActStep(
            step_type=ReActStepType.THOUGHT, content=thought_content, thinking_time=thinking_time
        )

    async def _decide_and_act(
        self, query: str, context: dict[str, Any], previous_steps: list[ReActStep]
    ) -> ReActStep:
        """决策并执行行动"""
        start_time = datetime.now()

        try:
            # 发现相关工具
            if not self._registry:
                return ReActStep(
                    step_type=ReActStepType.ACTION,
                    content="工具注册中心未初始化",
                    success=False,
                    error="No registry available",
                )

            # 基于查询和历史步骤发现工具
            tools = await self._registry.discover_tools(query, limit=3)

            if not tools:
                return ReActStep(
                    step_type=ReActStepType.ACTION,
                    content="未找到相关工具",
                    success=False,
                    error="No tools found",
                )

            # 选择最佳工具(简化:选择分数最高的)
            selected_tool = tools[0]
            tool_id = selected_tool["tool_id"]

            # 生成思考内容
            thought = self.thought_templates["tool_selection"][0].format(
                tools=", ".join([t["name"] for t in tools]),
                tool=selected_tool["name"],
                reason=f"匹配度最高 (分数: {selected_tool['score']:.2f})",
            )

            # 准备参数(简化:使用query作为参数)
            parameters = {"query": query}

            # 执行工具
            result = await self._registry.execute_tool(tool_id, parameters, context)

            thinking_time = (datetime.now() - start_time).total_seconds()

            return ReActStep(
                step_type=ReActStepType.ACTION,
                content=thought,
                tool_id=tool_id,
                parameters=parameters,
                result=result.result,
                success=result.success,
                error=result.error,
                thinking_time=thinking_time,
            )

        except Exception as e:
            thinking_time = (datetime.now() - start_time).total_seconds()
            return ReActStep(
                step_type=ReActStepType.ACTION,
                content="工具执行异常",
                success=False,
                error=str(e),
                thinking_time=thinking_time,
            )

    async def _observe(self, action_step: ReActStep, context: dict[str, Any]) -> ReActStep:
        """观察执行结果"""
        start_time = datetime.now()

        if action_step.success:
            observation = self.thought_templates["observation"][0].format(
                result=str(action_step.result)[:200]  # 限制长度
            )
        else:
            observation = f"工具执行失败: {action_step.error}"

        thinking_time = (datetime.now() - start_time).total_seconds()

        return ReActStep(
            step_type=ReActStepType.OBSERVATION, content=observation, thinking_time=thinking_time
        )

    async def _reflect(
        self, iteration: int, steps: list[ReActStep], context: dict[str, Any]
    ) -> ReActStep:
        """反思当前进展"""
        start_time = datetime.now()

        # 分析当前进展
        successful_actions = sum(
            1 for s in steps if s.step_type == ReActStepType.ACTION and s.success
        )
        total_actions = sum(1 for s in steps if s.step_type == ReActStepType.ACTION)

        progress = f"成功执行 {successful_actions}/{total_actions} 个工具调用"

        # 决定下一步
        if iteration >= self.max_iterations - 1:
            next_action = "已达到最大迭代次数,应该生成最终答案"
        elif successful_actions == 0:
            next_action = "工具调用失败,尝试其他工具或生成最终答案"
        else:
            next_action = "继续执行更多工具调用以获取更完整的信息"

        reflection = self.thought_templates["reflection"][0].format(
            iterations=iteration + 1, progress=progress, next_action=next_action
        )

        thinking_time = (datetime.now() - start_time).total_seconds()

        return ReActStep(
            step_type=ReActStepType.REFLECTION, content=reflection, thinking_time=thinking_time
        )

    async def _generate_final_answer(
        self, steps: list[ReActStep], context: dict[str, Any]
    ) -> ReActStep:
        """生成最终答案"""
        # 收集所有成功的工具结果
        results = []
        for step in steps:
            if step.step_type == ReActStepType.ACTION and step.success:
                results.append(str(step.result))

        if results:
            answer = self.thought_templates["final"][0].format(steps=len(steps))
            answer += "\n\n" + "\n\n".join(results[:3])  # 最多显示3个结果
        else:
            answer = "抱歉,无法完成您的请求。工具调用未返回有效结果。"

        return ReActStep(step_type=ReActStepType.ANSWER, content=answer)

    def _should_stop(self, reflection_content: str, last_action: ReActStep) -> bool:
        """判断是否应该停止"""
        # 检查停止模式
        for pattern in self.stop_patterns:
            if pattern in reflection_content or pattern in last_action.content:
                return True

        return False

    async def explain_trace(self, result: ReActResult) -> str:
        """
        生成可解释的轨迹

        Args:
            result: ReAct执行结果

        Returns:
            格式化的轨迹说明
        """
        lines = []
        lines.append("=" * 80)
        lines.append("🔍 ReAct执行轨迹")
        lines.append("=" * 80)
        lines.append("")

        for i, step in enumerate(result.steps, 1):
            icon = {
                ReActStepType.THOUGHT: "💭",
                ReActStepType.ACTION: "🔧",
                ReActStepType.OBSERVATION: "👀",
                ReActStepType.REFLECTION: "🤔",
                ReActStepType.ANSWER: "✅",
            }.get(step.step_type, "📌")

            lines.append(f"{icon} 步骤 {i}: {step.step_type.value.upper()}")
            lines.append(f"   时间: {step.timestamp.strftime('%H:%M:%S')}")
            if step.tool_id:
                lines.append(f"   工具: {step.tool_id}")
            if step.thinking_time > 0:
                lines.append(f"   思考时间: {step.thinking_time:.2f}s")
            lines.append(f"   内容: {step.content[:200]}")
            lines.append("")

        lines.append("=" * 80)
        lines.append(f"📊 总计: {result.total_steps} 步, {result.total_time:.2f}s")
        lines.append(f"🔧 使用工具: {', '.join(result.tools_used)}")
        lines.append("=" * 80)

        return "\n".join(lines)

    async def save_trace(self, result: ReActResult, output_path: Path):
        """保存执行轨迹到文件"""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        trace_data = {"result": result.to_dict(), "explanation": await self.explain_trace(result)}

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(trace_data, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ 执行轨迹已保存: {output_path}")

    async def shutdown(self):
        """关闭ReAct引擎"""
        logger.info("🛒 关闭ReAct执行引擎...")
        logger.info("✅ ReAct执行引擎已关闭")


# ================================
# 全局单例
# ================================

_react_executor: ReActExecutor | None = None


def get_react_executor() -> ReActExecutor:
    """获取ReAct执行引擎单例"""
    global _react_executor
    if _react_executor is None:
        _react_executor = ReActExecutor()
    return _react_executor


async def initialize_react_executor() -> ReActExecutor:
    """初始化ReAct执行引擎"""
    executor = get_react_executor()
    await executor.initialize()
    return executor


# ================================
# 测试代码
# ================================


async def main():
    """主函数(用于测试)"""
    print("=" * 80)
    print("🔍 ReAct执行引擎测试")
    print("=" * 80)
    print()

    # 获取执行引擎
    executor = get_react_executor()

    # 初始化
    print("初始化ReAct引擎...")
    success = await executor.initialize()

    if not success:
        print("❌ 初始化失败")
        return

    print()

    # 测试查询
    test_queries = ["搜索关于人工智能的专利", "查找法律相关的文档"]

    for query in test_queries:
        print(f"\n{'=' * 80}")
        print(f"查询: {query}")
        print("=" * 80)

        # 执行ReAct
        result = await executor.execute(query, max_iterations=3)

        # 显示结果
        if result.success:
            print(f"\n✅ 最终答案:\n{result.final_answer}\n")
            print(f"📊 统计: {result.total_steps} 步, {result.total_time:.2f}s")
            print(f"🔧 使用工具: {', '.join(result.tools_used)}")
        else:
            print(f"\n❌ 执行失败: {result.final_answer}")

        # 显示轨迹
        explanation = await executor.explain_trace(result)
        print("\n" + explanation)

        print()

    print("=" * 80)
    print("✅ 测试完成")
    print("=" * 80)


# 入口点: @async_main装饰器已添加到main函数
