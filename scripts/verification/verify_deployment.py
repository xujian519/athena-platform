#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署验证脚本
验证智能体设计模式组件是否正确部署
"""

import sys
from typing import Any, Dict, List, Optional, Tuple, Callable, Union
import os
from pathlib import Path

# 添加项目路径
sys.path.append('/Users/xujian/Athena工作平台')

def verify_component_deployment() -> bool:
    """验证组件部署"""
    print("🔍 验证智能体设计模式组件部署...")
    print("=" * 50)

    # 验证核心组件目录
    core_cognition_path = Path("/Users/xujian/Athena工作平台/core/cognition")
    core_management_path = Path("/Users/xujian/Athena工作平台/core/management")

    print("📁 检查目录结构:")

    # 检查认知模块
    if core_cognition_path.exists():
        print(f"   ✅ 认知模块目录: {core_cognition_path}")

        required_files = [
            "agentic_task_planner.py",
            "prompt_chain_processor.py",
            "__init__.py"
        ]

        for file_name in required_files:
            file_path = core_cognition_path / file_name
            if file_path.exists():
                print(f"      ✅ {file_name}")
            else:
                print(f"      ❌ {file_name} - 缺失")
    else:
        print(f"   ❌ 认知模块目录不存在: {core_cognition_path}")

    # 检查管理模块
    if core_management_path.exists():
        print(f"   ✅ 管理模块目录: {core_management_path}")

        required_files = [
            "goal_management_system.py",
            "__init__.py"
        ]

        for file_name in required_files:
            file_path = core_management_path / file_name
            if file_path.exists():
                print(f"      ✅ {file_name}")
            else:
                print(f"      ❌ {file_name} - 缺失")
    else:
        print(f"   ❌ 管理模块目录不存在: {core_management_path}")

    # 验证组件导入
    print("\n📦 检查组件导入:")

    try:
        from core.cognition import AgenticTaskPlanner, PromptChainProcessor
        print("   ✅ 智能任务规划器导入成功")
        print("   ✅ 提示链处理器导入成功")
    except ImportError as e:
        print(f"   ❌ 认知组件导入失败: {e}")

    try:
        from core.management import GoalManagementSystem
        print("   ✅ 目标管理系统导入成功")
    except ImportError as e:
        print(f"   ❌ 管理组件导入失败: {e}")

    # 验证实施组件目录
    implementations_path = Path("/Users/xujian/Athena工作平台/implementations")

    print("\n📋 检查实施组件:")

    if implementations_path.exists():
        implementation_files = [
            "agentic_task_planner.py",
            "prompt_chain_processor.py",
            "goal_management_system.py"
        ]

        for file_name in implementation_files:
            file_path = implementations_path / file_name
            if file_path.exists():
                print(f"   ✅ {file_name}")
            else:
                print(f"   ❌ {file_name} - 缺失")
    else:
        print(f"   ❌ 实施组件目录不存在: {implementations_path}")

    # 基础功能测试
    print("\n🧪 基础功能测试:")

    try:
        from core.cognition import AgenticTaskPlanner
        planner = AgenticTaskPlanner()
        print("   ✅ 任务规划器实例化成功")

        from core.management import GoalManagementSystem
        goal_manager = GoalManagementSystem()
        print("   ✅ 目标管理器实例化成功")

        # 测试基本功能
        test_goal = goal_manager.create_goal({
            'title': '测试目标',
            'description': '这是一个测试目标',
            'priority': 2
        })
        print("   ✅ 目标创建功能正常")

        print(f"      📊 创建测试目标: {test_goal.title}")
        print(f"      📊 目标ID: {test_goal.id}")
        print(f"      📊 子目标数: {len(test_goal.subgoals)}")
        print(f"      📊 指标数: {len(test_goal.metrics)}")

    except Exception as e:
        print(f"   ❌ 基础功能测试失败: {e}")

    print("\n📊 部署验证总结:")

    # 检查部署完整性
    deployment_complete = True

    check_items = [
        (core_cognition_path / "agentic_task_planner.py", "任务规划器"),
        (core_cognition_path / "prompt_chain_processor.py", "提示链处理器"),
        (core_management_path / "goal_management_system.py", "目标管理系统")
    ]

    for file_path, component_name in check_items:
        if not file_path.exists():
            deployment_complete = False
            print(f"   ❌ {component_name}: 部署不完整")
        else:
            print(f"   ✅ {component_name}: 部署完整")

    if deployment_complete:
        print("\n🎉 部署验证通过! 所有组件已正确部署")
        print("💡 下一步: 运行集成测试")
        return True
    else:
        print("\n⚠️ 部署验证失败! 请检查缺失的组件")
        return False

if __name__ == "__main__":
    success = verify_component_deployment()
    sys.exit(0 if success else 1)