#!/usr/bin/env python3
"""
Athena治理模块
Athena Governance Module

提供统一的工具治理能力,包括:
1. 统一工具注册中心(UnifiedToolRegistry)
2. ReAct执行引擎(ReActExecutor)
3. Reflection反思引擎(ReflectionEngine)
4. 工具评估框架(ToolEvaluationFramework)

使用方法:
    from core.governance import (
        get_unified_registry,
        get_react_executor,
        get_reflection_engine,
        ToolEvaluationFramework
    )

    # 初始化所有组件
    await initialize_governance()

    # 使用注册中心
    registry = get_unified_registry()
    tools = await registry.discover_tools("搜索专利")

    # 使用ReAct引擎
    executor = get_react_executor()
    result = await executor.execute("搜索关于人工智能的专利")

    # 使用反思引擎
    reflector = get_reflection_engine()
    reflection = await reflector.reflect_on_execution(tool_id, result, {})

    # 使用评估框架
    evaluator = ToolEvaluationFramework()
    evaluation = await evaluator.evaluate_tool(tool_id)
"""

from __future__ import annotations
__version__ = "1.0.0"
__author__ = "Athena Team"

# ================================
# 导入核心类
# ================================

from core.async_main import async_main

from .react_executor import (
    ReActExecutor,
    ReActResult,
    ReActStep,
    ReActStepType,
    get_react_executor,
    initialize_react_executor,
)
from .reflection_engine import (
    ReflectionEngine,
    ReflectionHistory,
    ReflectionOutcome,
    ReflectionResult,
    ReflectionType,
    get_reflection_engine,
)
from .tool_evaluation_framework import (
    EvaluationLevel,
    EvaluationMetric,
    MetricScore,
    ToolEvaluationFramework,
    ToolEvaluationResult,
)
from .unified_tool_registry import (
    ToolCategory,
    ToolExecutionResult,
    ToolMetadata,
    ToolStatus,
    UnifiedToolRegistry,
    get_unified_registry,
    initialize_unified_registry,
)

# ================================
# 公共接口
# ================================

__all__ = [
    "EvaluationLevel",
    "EvaluationMetric",
    "MetricScore",
    # ReAct执行引擎
    "ReActExecutor",
    "ReActResult",
    "ReActStep",
    "ReActStepType",
    # Reflection反思引擎
    "ReflectionEngine",
    "ReflectionHistory",
    "ReflectionOutcome",
    "ReflectionResult",
    "ReflectionType",
    "ToolCategory",
    # 工具评估框架
    "ToolEvaluationFramework",
    "ToolEvaluationResult",
    "ToolExecutionResult",
    "ToolMetadata",
    "ToolStatus",
    # 统一工具注册中心
    "UnifiedToolRegistry",
    "get_react_executor",
    "get_reflection_engine",
    "get_unified_registry",
    # 初始化函数
    "initialize_governance",
    "initialize_react_executor",
    "initialize_unified_registry",
    "shutdown_governance",
]

# ================================
# 全局初始化
# ================================


async def initialize_governance(config: dict | None = None) -> bool:
    """
    初始化治理模块的所有组件

    Args:
        config: 配置字典

    Returns:
        bool: 是否成功初始化
    """
    import logging

    logger = logging.getLogger(__name__)

    logger.info("=" * 80)
    logger.info("🚀 初始化Athena治理模块")
    logger.info("=" * 80)

    try:
        # 1. 初始化统一工具注册中心
        logger.info("1️⃣ 初始化统一工具注册中心...")
        registry = get_unified_registry()
        await registry.initialize()
        logger.info(f"✅ 注册中心已初始化 | None = None, 共 {len(registry.tools)} 个工具")

        # 2. 初始化ReAct执行引擎
        logger.info("2️⃣ 初始化ReAct执行引擎...")
        reactor = get_react_executor()
        await reactor.initialize()
        logger.info("✅ ReAct引擎已初始化")

        # 3. 反思引擎无需初始化(无状态)
        logger.info("3️⃣ 反思引擎就绪")
        get_reflection_engine()
        logger.info("✅ 反思引擎已就绪")

        # 4. 评估框架初始化
        logger.info("4️⃣ 初始化工具评估框架...")
        evaluator = ToolEvaluationFramework(config)
        await evaluator.initialize()
        logger.info("✅ 评估框架已初始化")

        logger.info("=" * 80)
        logger.info("✅ Athena治理模块初始化完成")
        logger.info("=" * 80)

        return True

    except Exception as e:
        logger.error(f"❌ 治理模块初始化失败: {e}")
        import traceback

        traceback.print_exc()
        return False


async def shutdown_governance():
    """关闭治理模块的所有组件"""
    import logging

    logger = logging.getLogger(__name__)

    logger.info("=" * 80)
    logger.info("🛒 关闭Athena治理模块")
    logger.info("=" * 80)

    try:
        # 1. 关闭ReAct引擎
        reactor = get_react_executor()
        await reactor.shutdown()

        # 2. 关闭统一注册中心
        registry = get_unified_registry()
        await registry.shutdown()

        logger.info("=" * 80)
        logger.info("✅ Athena治理模块已关闭")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"❌ 关闭治理模块时出错: {e}")


# ================================
# 便捷函数
# ================================


async def execute_with_reflection(
    query: str | None = None, context: dict | None = None, enable_reflection: bool = True
) -> dict:
    """
    执行查询并返回结果(可选反思)

    Args:
        query: 用户查询
        context: 执行上下文
        enable_reflection: 是否启用反思

    Returns:
        dict: 包含执行结果和反思的字典
    """
    from .react_executor import get_react_executor
    from .reflection_engine import get_reflection_engine

    # 执行ReAct
    executor = get_react_executor()
    react_result = await executor.execute(query, context or {})

    result = {
        "success": react_result.success,
        "answer": react_result.final_answer,
        "steps": react_result.total_steps,
        "time": react_result.total_time,
        "tools_used": react_result.tools_used,
    }

    # 可选反思
    if enable_reflection:
        reflector = get_reflection_engine()

        # 对每个使用的工具进行反思
        reflections = []
        for tool_id in react_result.tools_used:
            reflection = await reflector.reflect_on_execution(
                tool_id=tool_id,
                result={"success": True},
                context=context or {},
                execution_time=react_result.total_time / len(react_result.tools_used),
            )
            reflections.append(
                {"tool_id": tool_id, "score": reflection.score, "insights": reflection.insights}
            )

        result["reflections"] = reflections

    return result


async def evaluate_and_report(tool_ids: list = None, output_path: str | None = None) -> str:
    """
    评估工具并生成报告

    Args:
        tool_ids: 要评估的工具ID列表(None表示全部)
        output_path: 报告输出路径

    Returns:
        str: 报告内容
    """
    from .tool_evaluation_framework import ToolEvaluationFramework

    # 创建评估框架
    evaluator = ToolEvaluationFramework()
    await evaluator.initialize()

    # 执行评估
    if tool_ids:
        results = []
        for tool_id in tool_ids:
            result = await evaluator.evaluate_tool(tool_id)
            results.append(result)
    else:
        results = await evaluator.evaluate_all_tools()

    # 生成报告
    report = await evaluator.generate_evaluation_report(results)

    # 保存报告
    if output_path:
        from pathlib import Path

        await evaluator.save_evaluation_report(results, Path(output_path))

    return report


# ================================
# 模块信息
# ================================


def get_module_info() -> dict:
    """获取模块信息"""
    return {
        "name": "Athena Governance Module",
        "version": __version__,
        "author": __author__,
        "description": "统一工具治理系统,提供工具注册、执行、反思和评估能力",
        "components": {
            "unified_registry": "统一工具注册中心",
            "react_executor": "ReAct执行引擎",
            "reflection_engine": "Reflection反思引擎",
            "evaluation_framework": "工具评估框架",
        },
        "features": [
            "工具统一注册和发现",
            "基于ReAct框架的可解释执行",
            "多层次反思机制",
            "多维度工具评估",
            "性能监控和健康检查",
            "基准测试和对比分析",
        ],
    }


# ================================
# 测试代码
# ================================


@async_main
async def main():
    """主函数(用于测试)"""
    print("=" * 80)
    print("🧪 Athena治理模块测试")
    print("=" * 80)
    print()

    # 显示模块信息
    info = get_module_info()
    print(f"📦 模块: {info['name']}")
    print(f"📌 版本: {info['version']}")
    print(f"👤 作者: {info['author']}")
    print(f"📝 描述: {info['description']}")
    print()

    print("🔧 组件:")
    for name, desc in info["components"].items():
        print(f"  - {name}: {desc}")
    print()

    print("✨ 特性:")
    for feature in info["features"]:
        print(f"  - {feature}")
    print()

    # 初始化治理模块
    print("初始化治理模块...")
    success = await initialize_governance()

    if success:
        print()
        print("✅ 治理模块初始化成功")
        print()

        # 测试便捷函数
        print("测试便捷函数...")
        result = await execute_with_reflection("搜索关于人工智能的专利", enable_reflection=True)
        print(f"结果: {result['success']}")
        print(f"答案: {result['answer'][:100]}...")
        print(f"工具: {result['tools_used']}")
        print(f"反思: {len(result.get('reflections', []))} 个")
        print()

    # 关闭治理模块
    print("关闭治理模块...")
    await shutdown_governance()

    print()
    print("=" * 80)
    print("✅ 测试完成")
    print("=" * 80)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
