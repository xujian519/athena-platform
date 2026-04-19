#!/usr/bin/env python3
from __future__ import annotations
"""
能力编排器
Capability Orchestrator

负责编排多个能力调用,实现复杂工作流
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CapabilityInvocation:
    """能力调用定义"""

    step: int
    name: str
    capability_id: str
    parameters: dict[str, Any]
    output_mapping: dict[str, str] | None = None
    required: bool = True
    timeout: int = 30
    parallel: bool = False


class CapabilityOrchestrator:
    """能力编排器"""

    def __init__(self, invoker):
        """
        初始化能力编排器

        Args:
            invoker: 能力调用器实例
        """
        self.invoker = invoker
        logger.info("✅ 能力编排器初始化完成")

    def _resolve_parameters(
        self, parameters: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        解析参数(支持变量替换)

        Args:
            parameters: 参数模板
            context: 上下文变量

        Returns:
            解析后的参数
        """
        resolved = {}

        for key, value in parameters.items():
            if isinstance(value, str):
                # 简单的变量替换
                if value.startswith("{") and value.endswith("}"):
                    var_name = value[1:-1]
                    resolved[key] = context.get(var_name, value)
                else:
                    resolved[key] = value
            elif isinstance(value, dict):
                resolved[key] = self._resolve_parameters(value, context)
            elif isinstance(value, list):
                resolved[key] = [
                    (
                        self._resolve_parameters(v, context)
                        if isinstance(v, dict)
                        else v
                    )
                    for v in value
                ]
            else:
                resolved[key] = value

        return resolved

    def _extract_value(self, data: dict[str, Any], path: str) -> Any:
        """
        从字典中提取值(支持路径)

        Args:
            data: 数据字典
            path: 路径(如 "results[0].title")

        Returns:
            提取的值
        """
        keys = path.replace("[", ".").replace("]", "").split(".")
        value = data

        for key in keys:
            if key:
                try:
                    value = value[int(key)] if isinstance(value, list) else value[key]
                except (KeyError, IndexError, ValueError):
                    return None

        return value

    async def execute_workflow(
        self, invocations: list[dict[str, Any]], context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        执行能力工作流

        Args:
            invocations: 能力调用列表
            context: 上下文变量

        Returns:
            所有能力的结果
        """
        logger.info(f"🔄 执行能力工作流: {len(invocations)}个能力")

        results = {}

        # 按步骤分组
        steps = {}
        for inv in invocations:
            step = inv.get("step", 0)
            if step not in steps:
                steps[step] = []
            steps[step].append(CapabilityInvocation(**inv))

        # 按步骤顺序执行
        for step_num in sorted(steps.keys()):
            step_invocations = steps[step_num]

            # 检查是否需要并行执行
            if any(inv.parallel for inv in step_invocations):
                # 并行执行
                logger.info(f"  步骤{step_num}: 并行执行{len(step_invocations)}个能力")
                tasks = [
                    self._execute_invocation(inv, context, results) for inv in step_invocations
                ]
                step_results = await asyncio.gather(*tasks, return_exceptions=True)

                # 处理结果
                for inv, result in zip(step_invocations, step_results, strict=False):
                    if isinstance(result, Exception):
                        if inv.required:
                            raise result
                        else:
                            logger.warning(f"  ⚠️  可选能力失败: {inv.name} - {result}")
                    elif result and inv.output_mapping:
                        self._map_output(result, inv.output_mapping, results)

            else:
                # 串行执行
                logger.info(f"  步骤{step_num}: 串行执行{len(step_invocations)}个能力")
                for inv in step_invocations:
                    result = await self._execute_invocation(inv, context, results)
                    if inv.output_mapping:
                        self._map_output(result, inv.output_mapping, results)

        logger.info(f"✅ 工作流执行完成: {len(results)}个结果")

        return results

    async def _execute_invocation(
        self,
        invocation: CapabilityInvocation,
        context: dict[str, Any],        previous_results: dict[str, Any],    ) -> dict[str, Any] | None:
        """
        执行单个能力调用

        Args:
            invocation: 能力调用定义
            context: 原始上下文
            previous_results: 之前步骤的结果

        Returns:
            能力执行结果
        """
        logger.info(f"    → 调用能力: {invocation.name} ({invocation.capability_id})")

        # 合并上下文(原始上下文 + 之前的结果)
        full_context = {**context, **previous_results}

        # 解析参数
        parameters = self._resolve_parameters(invocation.parameters, full_context)

        try:
            # 调用能力
            result = await self.invoker.invoke(
                invocation.capability_id, parameters, invocation.timeout
            )

            logger.info(f"    ✅ {invocation.name} 完成")
            return result

        except Exception as e:
            logger.error(f"    ❌ {invocation.name} 失败: {e}")
            if invocation.required:
                raise
            return None

    def _map_output(
        self, result: dict[str, Any], output_mapping: dict[str, str], results: dict[str, Any]
    ):
        """
        映射输出结果

        Args:
            result: 能力执行结果
            output_mapping: 输出映射
            results: 结果集合
        """
        for key, path in output_mapping.items():
            value = self._extract_value(result, path)
            if value is not None:
                results[key] = value

    async def execute_parallel(
        self, invocations: list[dict[str, Any]], context: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        并行执行多个能力

        Args:
            invocations: 能力调用列表
            context: 上下文变量

        Returns:
            所有能力的结果列表
        """
        logger.info(f"⚡ 并行执行{len(invocations)}个能力")

        tasks = [
            self._execute_invocation(CapabilityInvocation(**inv), context, {})
            for inv in invocations
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 过滤异常
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"  能力{i}失败: {result}")
                processed_results.append(None)
            else:
                processed_results.append(result)

        logger.info(f"✅ 并行执行完成: {len(results)}个结果")

        return processed_results


class CapabilityComposer:
    """能力组合器(支持能力链和复合能力)"""

    def __init__(self, orchestrator: CapabilityOrchestrator):
        self.orchestrator = orchestrator

    async def execute_chain(
        self, chain: list[dict[str, Any]], initial_context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        执行能力链(前一个的输出是后一个的输入)

        Args:
            chain: 能力链定义
            initial_context: 初始上下文

        Returns:
            最终结果
        """
        logger.info(f"⛓️  执行能力链: {len(chain)}个环节")

        context = initial_context.copy()
        final_output = None

        for i, link in enumerate(chain, 1):
            logger.info(f"  环节{i}: {link.get('name', 'Unknown')}")

            # 执行能力
            result = await self.orchestrator.invoker.invoke(
                link["capability_id"],
                self._resolve_chain_parameters(link, context),
                link.get("timeout", 30),
            )

            # 更新上下文
            if "output" in link:
                context[link["output"]] = result

            final_output = result

        logger.info("✅ 能力链执行完成")

        return final_output

    def _resolve_chain_parameters(
        self, link: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """解析能力链参数"""
        parameters = link.get("parameters", {})

        if "input" in link:
            # 使用指定输入
            input_data = context.get(link["input"], {})
            if isinstance(input_data, dict):
                return {**parameters, **input_data}
            else:
                return {**parameters, "data": input_data}

        return parameters

    async def execute_composite(
        self, composite: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        执行复合能力

        Args:
            composite: 复合能力定义
            context: 上下文

        Returns:
            聚合结果
        """
        logger.info(f"🔗 执行复合能力: {composite.get('name', 'Unknown')}")

        sub_capabilities = composite.get("sub_capabilities", [])
        aggregation = composite.get("aggregation", "merge")

        # 并行执行所有子能力
        tasks = [
            self.orchestrator.invoker.invoke(
                sub["capability_id"], sub.get("parameters", {}), sub.get("timeout", 30)
            )
            for sub in sub_capabilities
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 聚合结果
        if aggregation == "merge":
            # 简单合并
            merged = {}
            for result in results:
                if isinstance(result, dict):
                    merged.update(result)
            return merged

        elif aggregation == "weighted_merge":
            # 加权合并
            weighted = {}
            for sub, result in zip(sub_capabilities, results, strict=False):
                if isinstance(result, dict):
                    weight = sub.get("weight", 1.0)
                    for key, value in result.items():
                        if key not in weighted:
                            weighted[key] = value * weight
                        else:
                            weighted[key] += value * weight
            return weighted

        else:
            return {"results": results}


# 便捷函数
async def execute_capability_workflow(
    invocations: list[dict[str, Any]], context: dict[str, Any]
) -> dict[str, Any]:
    """
    便捷的工作流执行函数

    Args:
        invocations: 能力调用列表
        context: 上下文变量

    Returns:
        所有能力的结果
    """
    from core.capabilities.capability_invoker import CapabilityInvoker

    invoker = CapabilityInvoker()
    orchestrator = CapabilityOrchestrator(invoker)

    return await orchestrator.execute_workflow(invocations, context)


async def invoke_capability_parallel(
    invocations: list[dict[str, Any]], context: dict[str, Any]
) -> list[dict[str, Any]]:
    """
    便捷的并行调用函数

    Args:
        invocations: 能力调用列表
        context: 上下文变量

    Returns:
        所有能力的结果列表
    """
    from core.capabilities.capability_invoker import CapabilityInvoker

    invoker = CapabilityInvoker()
    orchestrator = CapabilityOrchestrator(invoker)

    return await orchestrator.execute_parallel(invocations, context)
