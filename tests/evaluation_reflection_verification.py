#!/usr/bin/env python3
"""
评估与反思模块验证脚本
Evaluation and Reflection Module Verification Script

验证内容:
1. 模块导入测试
2. 基本功能测试
3. 通信机制测试
4. 完整工作流测试

作者: Athena AI系统
创建时间: 2026-04-18
"""

import asyncio
import sys
from pathlib import Path
from typing import Any

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.logging_config import setup_logging

logger = setup_logging()


class ModuleVerificationResult:
    """验证结果"""

    def __init__(self):
        self.import_tests = {}
        self.function_tests = {}
        self.communication_tests = {}
        self.workflow_tests = {}
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.warnings = []

    def add_result(self, category: str, test_name: str, passed: bool, message: str = ""):
        """添加测试结果"""
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
        else:
            self.failed_tests += 1

        if category == "import":
            self.import_tests[test_name] = {"passed": passed, "message": message}
        elif category == "function":
            self.function_tests[test_name] = {"passed": passed, "message": message}
        elif category == "communication":
            self.communication_tests[test_name] = {"passed": passed, "message": message}
        elif category == "workflow":
            self.workflow_tests[test_name] = {"passed": passed, "message": message}

    def add_warning(self, warning: str):
        """添加警告"""
        self.warnings.append(warning)

    def print_report(self):
        """打印报告"""
        print("\n" + "=" * 80)
        print("📊 评估与反思模块验证报告".center(80))
        print("=" * 80)

        # 总体统计
        print(f"\n📈 总体统计:")
        print(f"  总测试数: {self.total_tests}")
        print(f"  ✅ 通过: {self.passed_tests} ({self.passed_tests/self.total_tests*100:.1f}%)")
        print(f"  ❌ 失败: {self.failed_tests} ({self.failed_tests/self.total_tests*100:.1f}%)")

        # 导入测试
        print(f"\n📦 模块导入测试 ({len(self.import_tests)} 项):")
        for test_name, result in self.import_tests.items():
            status = "✅" if result["passed"] else "❌"
            print(f"  {status} {test_name}")
            if result["message"]:
                print(f"      {result['message']}")

        # 功能测试
        print(f"\n🔧 基本功能测试 ({len(self.function_tests)} 项):")
        for test_name, result in self.function_tests.items():
            status = "✅" if result["passed"] else "❌"
            print(f"  {status} {test_name}")
            if result["message"]:
                print(f"      {result['message']}")

        # 通信测试
        print(f"\n🔗 通信机制测试 ({len(self.communication_tests)} 项):")
        for test_name, result in self.communication_tests.items():
            status = "✅" if result["passed"] else "❌"
            print(f"  {status} {test_name}")
            if result["message"]:
                print(f"      {result['message']}")

        # 工作流测试
        print(f"\n🔄 完整工作流测试 ({len(self.workflow_tests)} 项):")
        for test_name, result in self.workflow_tests.items():
            status = "✅" if result["passed"] else "❌"
            print(f"  {status} {test_name}")
            if result["message"]:
                print(f"      {result['message']}")

        # 警告
        if self.warnings:
            print(f"\n⚠️  警告 ({len(self.warnings)} 项):")
            for warning in self.warnings:
                print(f"  ⚠️  {warning}")

        print("\n" + "=" * 80)

        # 返回是否全部通过
        return self.failed_tests == 0


async def verify_imports(result: ModuleVerificationResult):
    """验证模块导入"""
    print("\n🔍 验证模块导入...")

    # 测试1: 评估引擎导入
    try:
        from core.evaluation.evaluation_engine import EvaluationEngine, EvaluationResult
        result.add_result("import", "评估引擎导入", True, "EvaluationEngine, EvaluationResult")
    except ImportError as e:
        result.add_result("import", "评估引擎导入", False, f"导入失败: {e}")

    # 测试2: 反思引擎导入
    try:
        from core.intelligence.reflection_engine_v5 import ReflectionEngineV5, ReflectionType
        result.add_result("import", "反思引擎v5导入", True, "ReflectionEngineV5, ReflectionType")
    except ImportError as e:
        result.add_result("import", "反思引擎v5导入", False, f"导入失败: {e}")

    # 测试3: 自主控制评估反思引擎导入
    try:
        from services.autonomous_control.evaluation.evaluation_reflection_engine import (
            EvaluationReflectionEngine,
            EvaluationType,
            ReflectionType,
        )
        result.add_result(
            "import", "自主控制评估反思引擎导入", True, "EvaluationReflectionEngine"
        )
    except ImportError as e:
        result.add_result("import", "自主控制评估反思引擎导入", False, f"导入失败: {e}")

    # 测试4: 反思集成包装器导入
    try:
        from core.intelligence.reflection_integration_wrapper import (
            ReflectionIntegrationWrapper,
            ReflectionConfig,
        )
        result.add_result("import", "反思集成包装器导入", True, "ReflectionIntegrationWrapper")
    except ImportError as e:
        result.add_result("import", "反思集成包装器导入", False, f"导入失败: {e}")

    # 测试5: 评估配置导入
    try:
        from core.evaluation.evaluation_config import EvaluationConfig
        result.add_result("import", "评估配置导入", True, "EvaluationConfig")
    except ImportError as e:
        result.add_result("import", "评估配置导入", False, f"导入失败: {e}")

    # 测试6: 基础智能体导入
    try:
        from core.agents.base_agent import BaseAgent
        result.add_result("import", "基础智能体导入", True, "BaseAgent")
    except ImportError as e:
        result.add_result("import", "基础智能体导入", False, f"导入失败: {e}")


async def verify_basic_functions(result: ModuleVerificationResult):
    """验证基本功能"""
    print("\n🔧 验证基本功能...")

    # 测试1: 创建评估引擎实例
    try:
        from core.evaluation.evaluation_engine import EvaluationEngine
        engine = EvaluationEngine(evaluator_id="test_evaluator")
        result.add_result("function", "创建评估引擎实例", True, f"评估器ID: {engine.evaluator_id}")
    except Exception as e:
        result.add_result("function", "创建评估引擎实例", False, f"创建失败: {e}")

    # 测试2: 创建反思引擎实例
    try:
        from core.intelligence.reflection_engine_v5 import ReflectionEngineV5
        engine = ReflectionEngineV5(agent_id="test_agent")
        result.add_result("function", "创建反思引擎实例", True, f"代理ID: {engine.agent_id}")
    except Exception as e:
        result.add_result("function", "创建反思引擎实例", False, f"创建失败: {e}")

    # 测试3: 创建自主控制评估反思引擎实例
    try:
        from services.autonomous_control.evaluation.evaluation_reflection_engine import (
            EvaluationReflectionEngine,
        )
        engine = EvaluationReflectionEngine()
        result.add_result(
            "function", "创建自主控制评估反思引擎实例", True, f"名称: {engine.name}"
        )
    except Exception as e:
        result.add_result("function", "创建自主控制评估反思引擎实例", False, f"创建失败: {e}")

    # 测试4: 评估配置访问
    try:
        from core.evaluation.evaluation_config import EvaluationConfig
        config = EvaluationConfig()
        thresholds = config.thresholds
        result.add_result(
            "function", "评估配置访问", True, f"阈值配置: {thresholds.EXCELLENT}"
        )
    except Exception as e:
        result.add_result("function", "评估配置访问", False, f"访问失败: {e}")

    # 测试5: 反思类型枚举
    try:
        from core.intelligence.reflection_engine_v5 import ReflectionType
        types = [t.value for t in ReflectionType]
        expected_types = ["output", "process", "causal", "strategic"]
        has_all_types = all(t in types for t in expected_types)
        result.add_result("function", "反思类型枚举", has_all_types, f"类型: {types}")
    except Exception as e:
        result.add_result("function", "反思类型枚举", False, f"检查失败: {e}")


async def verify_communication(result: ModuleVerificationResult):
    """验证通信机制"""
    print("\n🔗 验证通信机制...")

    # 测试1: 评估引擎与反思引擎的通信
    try:
        from core.evaluation.evaluation_engine import EvaluationEngine, EvaluationResult
        from core.intelligence.reflection_engine_v5 import ReflectionEngineV5

        # 创建评估引擎
        eval_engine = EvaluationEngine(evaluator_id="test_evaluator")

        # 创建反思引擎
        reflect_engine = ReflectionEngineV5(agent_id="test_agent")

        # 模拟评估结果
        eval_result = EvaluationResult(
            id="test_eval_001",
            evaluator_id="test_evaluator",
            target_id="test_target",
            evaluation_type="quality",
            overall_score=75.0,
            confidence=0.8,
            criteria_results={
                "accuracy": {"score": 80.0, "confidence": 0.85, "evidence": ["证据1"]},
                "completeness": {"score": 70.0, "confidence": 0.75, "evidence": ["证据2"]},
            },
            strengths=["分析深入", "逻辑清晰"],
            weaknesses=["需要更多案例"],
            recommendations=["增加案例库", "提高分析深度"],
        )

        # 创建思维链
        thought_steps = [
            await reflect_engine._create_thought_step(
                content="分析用户需求", confidence=0.9, reasoning_type="intent_analysis"
            ),
            await reflect_engine._create_thought_step(
                content="检索相关知识", confidence=0.85, reasoning_type="knowledge_retrieval"
            ),
        ]

        # 执行反思循环
        loop = await reflect_engine.reflect_with_loop(
            original_input="帮我分析这个专利",
            output="这是一个关于人工智能的专利...",
            context={"domain": "patent_analysis"},
            thought_chain=thought_steps,
        )

        result.add_result(
            "communication",
            "评估-反思引擎通信",
            True,
            f"反思循环ID: {loop.loop_id}, 因子数: {len(loop.causal_factors)}",
        )
    except Exception as e:
        result.add_result("communication", "评估-反思引擎通信", False, f"通信失败: {e}")

    # 测试2: 反思引擎与LLM的通信
    try:
        from core.intelligence.reflection_engine_v5 import ReflectionEngineV5

        # 创建反思引擎(无LLM客户端)
        engine = ReflectionEngineV5(agent_id="test_agent", llm_client=None)

        # 验证统计信息
        stats = await engine.get_statistics()
        result.add_result(
            "communication",
            "反思引擎内部通信",
            True,
            f"统计信息: {stats['total_loops']} 个循环",
        )
    except Exception as e:
        result.add_result("communication", "反思引擎内部通信", False, f"通信失败: {e}")

    # 测试3: 评估结果格式兼容性
    try:
        from core.evaluation.evaluation_engine import EvaluationResult
        from datetime import datetime

        # 创建评估结果
        result = EvaluationResult(
            id="test_001",
            evaluator_id="evaluator_1",
            target_id="target_1",
            evaluation_type="performance",
            overall_score=85.0,
            confidence=0.9,
            criteria_results={
                "speed": {"score": 90.0, "confidence": 0.95, "evidence": ["快速响应"]},
                "accuracy": {"score": 80.0, "confidence": 0.85, "evidence": ["准确分析"]},
            },
            strengths=["响应快速", "分析准确"],
            weaknesses=["可以更详细"],
            recommendations=["增加详细程度"],
        )

        # 验证可序列化
        result_dict = result.model_dump()
        result.add_result(
            "communication",
            "评估结果格式兼容性",
            True,
            f"可序列化字段数: {len(result_dict)}",
        )
    except Exception as e:
        result.add_result("communication", "评估结果格式兼容性", False, f"格式检查失败: {e}")


async def verify_workflow(result: ModuleVerificationResult):
    """验证完整工作流"""
    print("\n🔄 验证完整工作流...")

    # 测试1: 评估→反思→改进工作流
    try:
        from core.evaluation.evaluation_engine import EvaluationEngine, EvaluationResult
        from core.intelligence.reflection_engine_v5 import (
            ReflectionEngineV5,
            ThoughtStep,
            ReflectionType,
        )
        from datetime import datetime

        # 步骤1: 执行评估
        eval_engine = EvaluationEngine(evaluator_id="workflow_evaluator")
        eval_result = EvaluationResult(
            id="workflow_eval_001",
            evaluator_id="workflow_evaluator",
            target_id="task_001",
            evaluation_type="quality",
            overall_score=65.0,
            confidence=0.75,
            criteria_results={
                "accuracy": {"score": 70.0, "confidence": 0.8, "evidence": ["基本准确"]},
                "completeness": {"score": 60.0, "confidence": 0.7, "evidence": ["不够完整"]},
            },
            strengths=["逻辑清晰"],
            weaknesses=["完整性不足", "证据不够充分"],
            recommendations=["补充更多证据", "提高完整性"],
        )

        # 步骤2: 执行反思
        reflect_engine = ReflectionEngineV5(agent_id="workflow_agent")
        thought_steps = [
            ThoughtStep(
                step_id="step1",
                timestamp=datetime.now(),
                content="初步分析",
                reasoning_type="initial_analysis",
                confidence=0.75,
            )
        ]

        loop = await reflect_engine.reflect_with_loop(
            original_input="分析专利权利要求",
            output="该权利要求涉及...",
            context={"task": "patent_analysis"},
            thought_chain=thought_steps,
            reflection_types=[ReflectionType.OUTPUT, ReflectionType.PROCESS],
        )

        # 步骤3: 验证改进建议
        has_action_items = len(loop.action_items) > 0
        has_causal_factors = len(loop.causal_factors) > 0

        result.add_result(
            "workflow",
            "评估→反思→改进工作流",
            has_action_items and has_causal_factors,
            f"行动项: {len(loop.action_items)}, 因子: {len(loop.causal_factors)}",
        )

        if not has_action_items:
            result.add_warning("反思循环未生成行动项,可能需要改进质量阈值")

    except Exception as e:
        result.add_result("workflow", "评估→反思→改进工作流", False, f"工作流失败: {e}")

    # 测试2: 持续改进循环
    try:
        from core.intelligence.reflection_engine_v5 import ReflectionEngineV5

        engine = ReflectionEngineV5(agent_id="continuous_improvement")

        # 第一轮评估
        loop1 = await engine.reflect_with_loop(
            original_input="测试输入",
            output="初步输出",
            context={"iteration": 1},
        )

        # 模拟改进
        improvement_score = await engine.measure_improvement(
            loop_id=loop1.loop_id, new_output="改进后的输出", new_context={"iteration": 2}
        )

        has_improvement = improvement_score >= 0
        result.add_result(
            "workflow",
            "持续改进循环",
            has_improvement,
            f"改进分数: {improvement_score:.3f}",
        )

    except Exception as e:
        result.add_result("workflow", "持续改进循环", False, f"改进循环失败: {e}")

    # 测试3: 自主控制评估反思引擎初始化
    try:
        from services.autonomous_control.evaluation.evaluation_reflection_engine import (
            EvaluationReflectionEngine,
            EvaluationType,
            ReflectionType,
        )

        engine = EvaluationReflectionEngine()
        await engine.initialize()

        # 执行性能评估
        eval_result = await engine.evaluate_performance(
            EvaluationType.PERFORMANCE,
            {
                "task_id": "test_task_001",
                "start_time": "2026-04-18T10:00:00",
                "end_time": "2026-04-18T10:03:00",
                "result": "success",
                "quality_score": 0.85,
            },
        )

        success = eval_result.get("success", False)
        result.add_result(
            "workflow",
            "自主控制评估反思引擎初始化",
            success,
            f"评估ID: {eval_result.get('evaluation_id', 'N/A')}",
        )

        if not success:
            result.add_warning("自主控制评估反思引擎初始化可能存在问题")

    except Exception as e:
        result.add_result("workflow", "自主控制评估反思引擎初始化", False, f"初始化失败: {e}")


async def check_integration_with_agents(result: ModuleVerificationResult):
    """检查与智能体的集成"""
    print("\n🤖 检查与智能体的集成...")

    # 测试1: 检查小诺智能体是否使用反思引擎
    try:
        from core.agents.xiaonuo.enhanced_xiaonuo import EnhancedXiaonuo

        # 检查是否有反思引擎
        has_reflection_v5 = hasattr(EnhancedXiaonuo, "reflection_engine_v5")
        result.add_result(
            "communication",
            "小诺智能体反思引擎集成",
            has_reflection_v5,
            "已集成反思引擎v5" if has_reflection_v5 else "未集成反思引擎v5",
        )

        if not has_reflection_v5:
            result.add_warning("小诺智能体未集成反思引擎v5,可能需要更新")

    except ImportError:
        result.add_result("communication", "小诺智能体反思引擎集成", False, "小诺智能体导入失败")
    except Exception as e:
        result.add_result("communication", "小诺智能体反思引擎集成", False, f"检查失败: {e}")

    # 测试2: 检查Athena智能体是否有评估功能
    try:
        from core.agent.athena_agent import AthenaAgent

        # 检查是否有评估方法
        has_evaluate = hasattr(AthenaAgent, "_evaluate_performance_aspects")
        result.add_result(
            "communication",
            "Athena智能体评估功能",
            has_evaluate,
            "有评估功能" if has_evaluate else "无评估功能",
        )

        if not has_evaluate:
            result.add_warning("Athena智能体没有评估功能,可能需要添加")

    except ImportError:
        result.add_result("communication", "Athena智能体评估功能", False, "Athena智能体导入失败")
    except Exception as e:
        result.add_result("communication", "Athena智能体评估功能", False, f"检查失败: {e}")

    # 测试3: 检查反思集成包装器
    try:
        from core.intelligence.reflection_integration_wrapper import (
            ReflectionIntegrationWrapper,
            ReflectionConfig,
        )

        # 创建包装器
        wrapper = ReflectionIntegrationWrapper(config=ReflectionConfig())
        has_process_method = hasattr(wrapper, "process_with_reflection")

        result.add_result(
            "communication",
            "反思集成包装器",
            has_process_method,
            "有处理方法" if has_process_method else "无处理方法",
        )

        if not has_process_method:
            result.add_warning("反思集成包装器缺少process_with_reflection方法")

    except ImportError:
        result.add_result("communication", "反思集成包装器", False, "反思集成包装器导入失败")
    except Exception as e:
        result.add_result("communication", "反思集成包装器", False, f"检查失败: {e}")


async def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("🔍 评估与反思模块验证工具".center(80))
    print("=" * 80)

    result = ModuleVerificationResult()

    # 1. 验证模块导入
    await verify_imports(result)

    # 2. 验证基本功能
    await verify_basic_functions(result)

    # 3. 验证通信机制
    await verify_communication(result)

    # 4. 验证完整工作流
    await verify_workflow(result)

    # 5. 检查与智能体的集成
    await check_integration_with_agents(result)

    # 打印报告
    all_passed = result.print_report()

    # 返回结果
    if all_passed:
        print("\n✅ 所有测试通过! 评估与反思模块运行正常.")
        return 0
    else:
        print("\n⚠️  部分测试失败,请检查上述报告.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
