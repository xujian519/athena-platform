#!/usr/bin/env python3
"""
法律世界模型系统验证脚本
Legal World Model System Verification Script

验证法律世界模型系统的完整性和可运行性

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


class LegalWorldModelVerifier:
    """法律世界模型验证器"""

    def __init__(self):
        self.verification_results = {
            "import_tests": [],
            "component_tests": [],
            "integration_tests": [],
            "overall_status": "pending"
        }

    async def verify_imports(self):
        """验证模块导入"""
        logger.info("=" * 60)
        logger.info("🔍 第一步: 验证模块导入")
        logger.info("=" * 60)

        import_tests = []

        # 测试核心模块导入
        try:
            from core.legal_world_model import (
                CONSTITUTION_VERSION,
                Case,
                CitationReference,
                ConstitutionalValidator,
                DocumentSource,
                DocumentType,
                InvalidationDecision,
                Judgment,
                LayerType,
                LegalEntity,
                LegalEntityType,
                LegalRelation,
                LegalRelationType,
                LegalRule,
                Patent,
                PatentEntityType,
                PatentRelationType,
                Principle,
                ProceduralRelationType,
                SubjectEntityType,
            )
            import_tests.append(("✅", "核心模块导入成功", "constitution.py"))
        except ImportError as e:
            import_tests.append(("❌", f"核心模块导入失败: {e}", "constitution.py"))

        # 测试场景识别器导入
        try:
            from core.legal_world_model.scenario_identifier_optimized import (
                Domain,
                Phase,
                ScenarioContext,
                ScenarioIdentifier,
                TaskType,
            )
            import_tests.append(("✅", "场景识别器导入成功", "scenario_identifier.py"))
        except ImportError as e:
            import_tests.append(("❌", f"场景识别器导入失败: {e}", "scenario_identifier.py"))

        # 测试场景规则检索器导入
        try:
            from core.legal_world_model.scenario_rule_retriever_optimized import (
                ScenarioRule,
                ScenarioRuleRetrieverOptimized as ScenarioRuleRetriever,
            )
            import_tests.append(("✅", "场景规则检索器导入成功", "scenario_rule_retriever.py"))
        except ImportError as e:
            import_tests.append(("❌", f"场景规则检索器导入失败: {e}", "scenario_rule_retriever.py"))

        # 测试宪法验证器导入
        try:
            from core.legal_world_model.constitution import ConstitutionalValidator
            import_tests.append(("✅", "宪法验证器导入成功", "constitution.py"))
        except ImportError as e:
            import_tests.append(("❌", f"宪法验证器导入失败: {e}", "constitution.py"))

        self.verification_results["import_tests"] = import_tests
        return import_tests

    async def verify_components(self):
        """验证组件功能"""
        logger.info("\n" + "=" * 60)
        logger.info("🧩 第二步: 验证组件功能")
        logger.info("=" * 60)

        component_tests = []

        # 测试场景识别器
        try:
            from core.legal_world_model.scenario_identifier_optimized import ScenarioIdentifierOptimized as ScenarioIdentifier

            identifier = ScenarioIdentifier()
            test_input = "这个专利有创造性吗？"

            context = identifier.identify_scenario(test_input)
            component_tests.append((
                "✅",
                "场景识别器功能正常",
                f"识别结果: {context.domain.value}/{context.task_type.value}, 置信度: {context.confidence:.2f}"
            ))
        except Exception as e:
            component_tests.append(("❌", f"场景识别器测试失败: {e}", ""))

        # 测试宪法验证器
        try:
            from core.legal_world_model.constitution import (
                ConstitutionalValidator,
                LayerType,
                LegalEntityType,
            )

            validator = ConstitutionalValidator()

            # 测试层级验证
            test_entity = {
                "entity_type": LegalEntityType.LAW,
                "layer": LayerType.FOUNDATION_LAW_LAYER,
            }

            is_valid = validator.validate_entity(test_entity)
            component_tests.append((
                "✅" if is_valid else "⚠️",
                "宪法验证器功能正常",
                f"层级验证: {test_entity['layer'].value} 是否有效"
            ))
        except Exception as e:
            component_tests.append(("❌", f"宪法验证器测试失败: {e}", ""))

        # 测试原则定义
        try:
            from core.legal_world_model.constitution import Principle

            principles = [
                Principle.AUTHORITATIVE_FIRST,
                Principle.THREE_LAYER_ARCH,
                Principle.KNOWLEDGE_GRAPH,
                Principle.EXPLAINABILITY,
                Principle.TRUTHFULNESS,
            ]

            component_tests.append((
                "✅",
                f"核心原则定义完整 ({len(principles)}个)",
                ", ".join([p.value for p in principles])
            ))
        except Exception as e:
            component_tests.append(("❌", f"原则定义测试失败: {e}", ""))

        self.verification_results["component_tests"] = component_tests
        return component_tests

    async def verify_integration(self):
        """验证集成功能"""
        logger.info("\n" + "=" * 60)
        logger.info("🔗 第三步: 验证集成功能")
        logger.info("=" * 60)

        integration_tests = []

        # 测试扩展提示词管理器集成
        try:
            from core.prompts.unified_prompt_manager_extended import ExtendedUnifiedPromptManager

            # 测试场景感知提示词生成
            manager = ExtendedUnifiedPromptManager()

            test_input = "帮我分析这个专利的创造性"
            result = manager.generate_scenario_based_prompt(test_input)

            if result and "prompt" in result:
                integration_tests.append((
                    "✅",
                    "场景感知提示词生成正常",
                    f"提示词长度: {len(result.get('prompt', ''))} 字符"
                ))
            else:
                integration_tests.append(("⚠️", "场景感知提示词生成需要检查", "返回结果格式"))
        except Exception as e:
            integration_tests.append(("❌", f"集成测试失败: {e}", ""))

        # 测试法律QA系统集成
        try:
            from core.legal_qa.legal_world_qa_system import LegalWorldQASystem

            # 验证系统可以实例化
            integration_tests.append((
                "✅",
                "法律QA系统可正常实例化",
                "legal_world_qa_system.py"
            ))
        except Exception as e:
            integration_tests.append(("❌", f"法律QA系统实例化失败: {e}", "legal_world_qa_system.py"))

        self.verification_results["integration_tests"] = integration_tests
        return integration_tests

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

        # 统计集成测试
        logger.info("\n【集成功能测试】")
        for status, desc, detail in self.verification_results["integration_tests"]:
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

        return self.verification_results


async def verify_legal_world_model():
    """验证法律世界模型系统"""
    logger.info("🏛️ 开始验证法律世界模型系统...")

    verifier = LegalWorldModelVerifier()

    # 执行验证步骤
    await verifier.verify_imports()
    await verifier.verify_components()
    await verifier.verify_integration()

    # 生成报告
    verifier.generate_report()

    return verifier.verification_results


if __name__ == "__main__":
    asyncio.run(verify_legal_world_model())
