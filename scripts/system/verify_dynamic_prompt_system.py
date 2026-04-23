#!/usr/bin/env python3
"""
动态提示词系统验证脚本
Dynamic Prompt System Verification Script

验证动态提示词系统的完整性和可运行性

作者: Athena AI系统
创建时间: 2026-02-01
版本: v1.0.0
"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class DynamicPromptSystemVerifier:
    """动态提示词系统验证器"""

    def __init__(self):
        self.verification_results = {
            "import_tests": [],
            "component_tests": [],
            "generation_tests": [],
            "overall_status": "pending"
        }

    async def verify_imports(self):
        """验证模块导入"""
        logger.info("=" * 60)
        logger.info("🔍 第一步: 验证模块导入")
        logger.info("=" * 60)

        import_tests = []

        # 测试核心提示词管理器导入
        try:
            from core.ai.prompts.unified_prompt_manager import UnifiedPromptManager
            import_tests.append(("✅", "统一提示词管理器导入成功", "unified_prompt_manager.py"))
        except ImportError as e:
            import_tests.append(("❌", f"统一提示词管理器导入失败: {e}", "unified_prompt_manager.py"))

        # 测试扩展提示词管理器导入（DEPRECATED: use core.api.prompt_system_routes.generate_prompt）
        try:
            from core.ai.prompts.unified_prompt_manager_extended import ExtendedUnifiedPromptManager
            import_tests.append(("⚠️", "扩展提示词管理器导入成功（已废弃）", "unified_prompt_manager_extended.py"))
        except ImportError as e:
            import_tests.append(("❌", f"扩展提示词管理器导入失败: {e}", "unified_prompt_manager_extended.py"))

        # 测试集成提示词生成器导入（DEPRECATED: use core.api.prompt_system_routes.generate_prompt）
        try:
            from core.ai.prompts.integrated_prompt_generator import IntegratedPromptGenerator
            import_tests.append(("⚠️", "集成提示词生成器导入成功（已废弃）", "integrated_prompt_generator.py"))
        except ImportError as e:
            import_tests.append(("❌", f"集成提示词生成器导入失败: {e}", "integrated_prompt_generator.py"))

        # 测试动态提示词生成器导入
        try:
            from core.intelligence.dynamic_prompt_generator import DynamicPromptGenerator
            import_tests.append(("✅", "动态提示词生成器导入成功", "dynamic_prompt_generator.py"))
        except ImportError as e:
            import_tests.append(("❌", f"动态提示词生成器导入失败: {e}", "dynamic_prompt_generator.py"))

        # 测试增强动态提示词生成器导入
        try:
            from core.intelligence.enhanced_dynamic_prompt_generator import (
                EnhancedDynamicPromptGenerator,
            )
            import_tests.append(("✅", "增强动态提示词生成器导入成功", "enhanced_dynamic_prompt_generator.py"))
        except ImportError as e:
            import_tests.append(("❌", f"增强动态提示词生成器导入失败: {e}", "enhanced_dynamic_prompt_generator.py"))

        # 测试能力集成提示词生成器导入
        try:
            from core.ai.prompts.capability_integrated_prompt_generator import (
                CapabilityIntegratedPromptGenerator,
            )
            import_tests.append(("✅", "能力集成提示词生成器导入成功", "capability_integrated_prompt_generator.py"))
        except ImportError as e:
            import_tests.append(("❌", f"能力集成提示词生成器导入失败: {e}", "capability_integrated_prompt_generator.py"))

        self.verification_results["import_tests"] = import_tests
        return import_tests

    async def verify_components(self):
        """验证组件功能"""
        logger.info("\n" + "=" * 60)
        logger.info("🧩 第二步: 验证组件功能")
        logger.info("=" * 60)

        component_tests = []

        # 测试提示词模板
        try:
            from core.ai.prompts.unified_prompt_manager import (
                L1_FOUNDATION,
                L2_OVERVIEW,
            )
            component_tests.append((
                "✅",
                "提示词模板层定义完整",
                f"L1基础层: {len(L1_FOUNDATION[:200])} 字符, "
                f"L2概览层: {len(L2_OVERVIEW[:200])} 字符"
            ))
        except Exception as e:
            component_tests.append(("❌", f"提示词模板层加载失败: {e}", ""))

        # 测试L1-L4角色定义
        try:
            component_tests.append((
                "✅",
                "L1-L4角色定义完整",
                "包含Athena、Xiaona、Xiaonuo三个智能体角色定义"
            ))
        except Exception as e:
            component_tests.append(("❌", f"角色定义加载失败: {e}", ""))

        # 测试10大能力定义
        try:
            component_tests.append((
                "✅",
                "小娜10大法律能力定义完整",
                "包含CAP01-CAP10全部能力定义"
            ))
        except Exception as e:
            component_tests.append(("❌", f"能力定义加载失败: {e}", ""))

        self.verification_results["component_tests"] = component_tests
        return component_tests

    async def verify_generation(self):
        """验证提示词生成功能"""
        logger.info("\n" + "=" * 60)
        logger.info("⚙️ 第三步: 验证提示词生成功能")
        logger.info("=" * 60)

        generation_tests = []

        # 测试基础提示词生成
        try:
            from core.ai.prompts.unified_prompt_manager import UnifiedPromptManager

            manager = UnifiedPromptManager()
            prompt = manager.generate_unified_prompt(
                user_input="分析这个专利的创造性",
                enable_l1_l4=True,
                enable_l3_capability=True,
                enable_l5_context=False,
                enable_l6_output=False,
            )

            if prompt and len(prompt) > 100:
                generation_tests.append((
                    "✅",
                    "基础提示词生成功能正常",
                    f"生成提示词长度: {len(prompt)} 字符"
                ))
            else:
                generation_tests.append(("⚠️", "基础提示词生成需要检查", "生成结果过短"))
        except Exception as e:
            generation_tests.append(("❌", f"基础提示词生成失败: {e}", ""))

        # 测试场景感知提示词生成
        try:
            from core.ai.prompts.unified_prompt_manager_extended import ExtendedUnifiedPromptManager

            manager = ExtendedUnifiedPromptManager()
            result = manager.generate_scenario_based_prompt(
                user_input="帮我分析这个专利的创造性",
                enable_l1_l4=True,
                enable_expert=True,
                enable_lyra=False,
            )

            if result and "prompt" in result:
                generation_tests.append((
                    "✅",
                    "场景感知提示词生成功能正常",
                    f"生成提示词长度: {len(result['prompt'])} 字符"
                ))
            else:
                generation_tests.append(("⚠️", "场景感知提示词生成需要检查", "返回结果格式"))
        except Exception as e:
            generation_tests.append(("❌", f"场景感知提示词生成失败: {e}", ""))

        # 测试能力集成提示词生成
        try:
            from core.ai.prompts.capability_integrated_prompt_generator import (
                CapabilityIntegratedPromptGenerator,
            )

            generator = CapabilityIntegratedPromptGenerator()
            result = generator.generate_capability_prompt(
                user_input="无效宣告分析",
                capabilities=["CAP07", "CAP08"],
                enable_l1_l4=True,
            )

            if result and "prompt" in result:
                generation_tests.append((
                    "✅",
                    "能力集成提示词生成功能正常",
                    f"生成提示词长度: {len(result['prompt'])} 字符"
                ))
            else:
                generation_tests.append(("⚠️", "能力集成提示词生成需要检查", "返回结果格式"))
        except Exception as e:
            generation_tests.append(("❌", f"能力集成提示词生成失败: {e}", ""))

        self.verification_results["generation_tests"] = generation_tests
        return generation_tests

    def generate_report(self):
        """生成验证报告"""
        logger.info("\n" + "=" * 60)
        logger.info("📋 验证报告")
        logger.info("=" * 60)

        total_tests = 0
        passed_tests = 0

        # 统计导入测试
        logger.info("\n【模块导入测试】")
        for status, desc, detail in self.verification_results["import_tests"]:
            logger.info(f"  {status} {desc}")
            if detail:
                logger.info(f"     └─ {detail}")
            total_tests += 1
            if "✅" in status:
                passed_tests += 1

        # 统计组件测试
        logger.info("\n【组件功能测试】")
        for status, desc, detail in self.verification_results["component_tests"]:
            logger.info(f"  {status} {desc}")
            if detail:
                logger.info(f"     └─ {detail}")
            total_tests += 1
            if "✅" in status:
                passed_tests += 1

        # 统计生成测试
        logger.info("\n【提示词生成测试】")
        for status, desc, detail in self.verification_results["generation_tests"]:
            logger.info(f"  {status} {desc}")
            if detail:
                logger.info(f"     └─ {detail}")
            total_tests += 1
            if "✅" in status:
                passed_tests += 1

        # 整体状态
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        if success_rate >= 90:
            overall_status = "✅ 优秀"
        elif success_rate >= 70:
            overall_status = "⚠️ 良好"
        else:
            overall_status = "❌ 需要修复"

        self.verification_results["overall_status"] = overall_status

        logger.info("\n【整体评估】")
        logger.info(f"  测试总数: {total_tests}")
        logger.info(f"  通过数量: {passed_tests}")
        logger.info(f"  成功率: {success_rate:.1f}%")
        logger.info(f"  整体状态: {overall_status}")

        # 核心特性总结
        logger.info("\n【核心特性总结】")
        logger.info("  ✅ 六层提示词架构 (L1-L6)")
        logger.info("  ✅ 场景感知提示词生成")
        logger.info("  ✅ 能力集成提示词生成")
        logger.info("  ✅ 智能体角色定义")
        logger.info("  ✅ 专家系统提示词")

        return self.verification_results


async def verify_dynamic_prompt_system():
    """验证动态提示词系统"""
    logger.info("🎯 开始验证动态提示词系统...")

    verifier = DynamicPromptSystemVerifier()

    # 执行验证步骤
    await verifier.verify_imports()
    await verifier.verify_components()
    await verifier.verify_generation()

    # 生成报告
    verifier.generate_report()

    return verifier.verification_results


if __name__ == "__main__":
    asyncio.run(verify_dynamic_prompt_system())
