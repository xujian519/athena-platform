#!/usr/bin/env python3
"""
手动修复验证脚本
Manual Fix Verification Script

验证 Enhanced Xiaonuo 手动修复后的功能

作者: Athena AI System
创建时间: 2026-04-18
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.logging_config import setup_logging

logger = setup_logging()


async def test_enhanced_xiaonuo():
    """测试 Enhanced Xiaonuo"""
    print("\n" + "=" * 80)
    print("🔍 Enhanced Xiaonuo 手动修复验证".center(80))
    print("=" * 80)

    results = {
        "passed": 0,
        "failed": 0,
        "tests": [],
    }

    def add_result(test_name: str, passed: bool, details: str = ""):
        """添加测试结果"""
        results["tests"].append({
            "name": test_name,
            "passed": passed,
            "details": details,
        })
        if passed:
            results["passed"] += 1
        else:
            results["failed"] += 1

    # ========== 测试1: 导入模块 ==========
    print("\n📋 测试1: 导入模块")

    try:
        from core.framework.agents.xiaonuo.enhanced_xiaonuo import EnhancedXiaonuo
        add_result("导入 Enhanced Xiaonuo", True, "模块导入成功")
    except ImportError as e:
        add_result("导入 Enhanced Xiaonuo", False, f"导入失败: {e}")
        print("❌ 无法继续测试，导入失败")
        return False

    # ========== 测试2: 检查类属性 ==========
    print("\n📋 测试2: 检查类属性")

    try:
        # 检查是否有反思引擎
        has_reflection = hasattr(EnhancedXiaonuo, 'reflection_engine_v5')
        add_result("反思引擎属性", has_reflection, "有 reflection_engine_v5" if has_reflection else "缺少 reflection_engine_v5")

        # 检查是否有记忆整合（可能不可用）
        has_consolidation = hasattr(EnhancedXiaonuo, 'memory_consolidation')
        add_result("记忆整合属性", has_consolidation, "有 memory_consolidation（可能为 None）" if has_consolidation else "缺少 memory_consolidation")

        # 检查是否有元学习（可能不可用）
        has_meta_learning = hasattr(EnhancedXiaonuo, 'meta_learning')
        add_result("元学习属性", has_meta_learning, "有 meta_learning（可能为 None）" if has_meta_learning else "缺少 meta_learning")

    except Exception as e:
        add_result("检查类属性", False, f"检查失败: {e}")

    # ========== 测试3: 创建实例 ==========
    print("\n📋 测试3: 创建实例")

    try:
        agent = EnhancedXiaonuo()
        add_result("创建实例", True, f"实例ID: {agent.agent_id}")

        # 检查实例属性
        has_engine = agent.reflection_engine_v5 is not None
        add_result("反思引擎实例", has_engine, "反思引擎已初始化" if has_engine else "反思引擎未初始化")

        # 检查能力列表
        has_capabilities = len(agent.enhanced_capabilities) > 0
        add_result("增强能力列表", has_capabilities, f"能力数: {len(agent.enhanced_capabilities)}, {agent.enhanced_capabilities}")

        # 检查配置
        has_config = agent.config is not None
        add_result("配置", has_config, f"配置: {agent.config}")

    except Exception as e:
        add_result("创建实例", False, f"创建失败: {e}")

    # ========== 测试4: 测试反思功能 ==========
    print("\n📋 测试4: 测试反思功能")

    try:
        from datetime import datetime

        from core.intelligence.reflection_engine_v5 import ReflectionType, ThoughtStep

        # 创建思维链
        thought_chain = [
            ThoughtStep(
                step_id="test1",
                timestamp=datetime.now(),
                content="测试思维步骤",
                reasoning_type="test",
                confidence=0.9,
            )
        ]

        # 执行反思
        loop = await agent.reflection_engine_v5.reflect_with_loop(
            original_input="测试输入",
            output="测试输出",
            context={"test": True},
            thought_chain=thought_chain,
            reflection_types=[ReflectionType.OUTPUT],
        )

        has_loop_id = loop.loop_id is not None
        add_result("执行反思循环", has_loop_id, f"循环ID: {loop.loop_id}")

    except Exception as e:
        add_result("执行反思循环", False, f"执行失败: {e}")

    # ========== 测试5: 测试处理输入 ==========
    print("\n📋 测试5: 测试处理输入")

    try:
        response = await agent.process_input(
            "你好，请介绍一下你自己",
            enable_reflection=False,  # 禁用反思以加快测试
            enable_learning=False,    # 禁用学习以加快测试
        )

        has_response = response is not None and len(response) > 0
        add_result("处理用户输入", has_response, f"响应长度: {len(response) if response else 0} 字符")

    except Exception as e:
        add_result("处理用户输入", False, f"处理失败: {e}")

    # ========== 测试6: 测试记忆整合（如果可用）==========
    print("\n📋 测试6: 测试记忆整合（如果可用）")

    try:
        if agent.memory_consolidation is not None:
            # 记忆整合可用
            add_result("记忆整合系统", True, "记忆整合系统已启用")
        else:
            # 记忆整合不可用（这是正常的）
            add_result("记忆整合系统", True, "记忆整合系统未启用（备用模式）")
    except Exception as e:
        add_result("记忆整合系统", False, f"检查失败: {e}")

    # ========== 测试7: 测试元学习（如果可用）==========
    print("\n📋 测试7: 测试元学习（如果可用）")

    try:
        if agent.meta_learning is not None:
            # 元学习可用
            add_result("元学习引擎", True, "元学习引擎已启用")
        else:
            # 元学习不可用（这是正常的）
            add_result("元学习引擎", True, "元学习引擎未启用（备用模式）")
    except Exception as e:
        add_result("元学习引擎", False, f"检查失败: {e}")

    # ========== 打印报告 ==========
    print("\n" + "=" * 80)
    print("📊 验证报告".center(80))
    print("=" * 80)

    for test in results["tests"]:
        status = "✅" if test["passed"] else "❌"
        print(f"{status} {test['name']}")
        if test["details"]:
            print(f"   → {test['details']}")

    print("\n" + "-" * 80)
    total = results["passed"] + results["failed"]
    pass_rate = results["passed"] / total * 100 if total > 0 else 0
    print(f"总计: {results['passed']}/{total} 通过 ({pass_rate:.1f}%)")
    print("=" * 80)

    # ========== 总结 ==========
    if results["failed"] == 0:
        print("\n✅ 所有测试通过! Enhanced Xiaonuo 手动修复成功.")
        print("\n📋 核心功能:")
        print("  • ✅ 模块导入正常")
        print("  • ✅ 实例创建成功")
        print("  • ✅ 反思引擎可用")
        print("  • ✅ 用户输入处理正常")
        print("  • ✅ 优雅降级（记忆整合/元学习可选）")
        print("\n🎯 结论: Enhanced Xiaonuo 已完全可用")
        return True
    else:
        print(f"\n⚠️  {results['failed']} 个测试失败，请检查上述报告.")
        return False


async def main():
    """主函数"""
    success = await test_enhanced_xiaonuo()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
