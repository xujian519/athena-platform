"""
Agent接口合规性测试

测试Agent是否符合统一接口标准。
"""

from typing import Any

import pytest

from core.framework.agents.xiaona.base_component import BaseXiaonaComponent


class InterfaceComplianceChecker:
    """接口合规性检查器"""

    @staticmethod
    def check_agent_class(agent_class: Any) -> dict:
        """
        检查Agent类是否符合接口标准

        Args:
            agent_class: Agent类

        Returns:
            检查结果字典
        """
        results = {
            "passed": [],
            "failed": [],
            "warnings": [],
        }

        # 1. 检查继承关系
        if not issubclass(agent_class, BaseXiaonaComponent):
            results["failed"].append({
                "check": "继承关系",
                "message": f"{agent_class.__name__} 未继承 BaseXiaonaComponent"
            })
            return results
        else:
            results["passed"].append({
                "check": "继承关系",
                "message": f"{agent_class.__name__} 正确继承 BaseXiaonaComponent"
            })

        # 2. 检查必需方法
        required_methods = ["_initialize", "execute", "get_system_prompt"]
        for method_name in required_methods:
            if not hasattr(agent_class, method_name):
                results["failed"].append({
                    "check": f"必需方法: {method_name}",
                    "message": f"缺少 {method_name} 方法"
                })
            else:
                results["passed"].append({
                    "check": f"必需方法: {method_name}",
                    "message": f"{method_name} 方法存在"
                })

        # 3. 检查execute方法是否是异步的
        if hasattr(agent_class, "execute"):
            import inspect
            if not inspect.iscoroutinefunction(agent_class.execute):
                results["failed"].append({
                    "check": "execute方法签名",
                    "message": "execute 方法必须是异步的（async def）"
                })
            else:
                results["passed"].append({
                    "check": "execute方法签名",
                    "message": "execute 方法是异步的"
                })

        return results

    @staticmethod
    def check_agent_instance(agent: BaseXiaonaComponent) -> dict:
        """
        检查Agent实例是否符合接口标准

        Args:
            agent: Agent实例

        Returns:
            检查结果字典
        """
        results = {
            "passed": [],
            "failed": [],
            "warnings": [],
        }

        # 1. 检查agent_id
        if not hasattr(agent, "agent_id") or not agent.agent_id:
            results["failed"].append({
                "check": "agent_id",
                "message": "Agent 缺少 agent_id"
            })
        else:
            results["passed"].append({
                "check": "agent_id",
                "message": f"agent_id: {agent.agent_id}"
            })

        # 2. 检查能力注册
        capabilities = agent.get_capabilities()
        if not capabilities:
            results["failed"].append({
                "check": "能力注册",
                "message": "Agent 未注册任何能力"
            })
        else:
            results["passed"].append({
                "check": "能力注册",
                "message": f"注册了 {len(capabilities)} 个能力"
            })

            # 检查每个能力的完整性
            for i, cap in enumerate(capabilities):
                if not cap.name:
                    results["failed"].append({
                        "check": f"能力{i}: name",
                        "message": "能力缺少 name 字段"
                    })
                if not cap.description:
                    results["warnings"].append({
                        "check": f"能力{i}: description",
                        "message": "能力缺少 description 字段"
                    })
                if not cap.input_types:
                    results["warnings"].append({
                        "check": f"能力{i}: input_types",
                        "message": "能力缺少 input_types 字段"
                    })
                if not cap.output_types:
                    results["warnings"].append({
                        "check": f"能力{i}: output_types",
                        "message": "能力缺少 output_types 字段"
                    })
                if cap.estimated_time <= 0:
                    results["warnings"].append({
                        "check": f"能力{i}: estimated_time",
                        "message": "能力的 estimated_time 应该大于0"
                    })

        # 3. 检查get_info方法
        try:
            info = agent.get_info()
            if not isinstance(info, dict):
                results["failed"].append({
                    "check": "get_info",
                    "message": "get_info 应该返回字典"
                })
            elif "agent_id" not in info:
                results["failed"].append({
                    "check": "get_info",
                    "message": "get_info 返回的字典缺少 agent_id"
                })
            else:
                results["passed"].append({
                    "check": "get_info",
                    "message": "get_info 方法正常"
                })
        except Exception as e:
            results["failed"].append({
                "check": "get_info",
                "message": f"get_info 执行失败: {str(e)}"
            })

        # 4. 检查get_system_prompt方法
        try:
            prompt = agent.get_system_prompt()
            if not isinstance(prompt, str):
                results["failed"].append({
                    "check": "get_system_prompt",
                    "message": "get_system_prompt 应该返回字符串"
                })
            elif len(prompt) < 10:
                results["warnings"].append({
                    "check": "get_system_prompt",
                    "message": "get_system_prompt 返回的字符串过短"
                })
            else:
                results["passed"].append({
                    "check": "get_system_prompt",
                    "message": f"get_system_prompt 返回 {len(prompt)} 个字符"
                })
        except Exception as e:
            results["failed"].append({
                "check": "get_system_prompt",
                "message": f"get_system_prompt 执行失败: {str(e)}"
            })

        return results


# ==================== pytest测试用例 ====================

def test_base_agent_compliance():
    """测试BaseXiaonaComponent是否符合接口标准"""
    from core.framework.agents.xiaona.base_component import BaseXiaonaComponent

    checker = InterfaceComplianceChecker()
    results = checker.check_agent_class(BaseXiaonaComponent)

    # BaseXiaonaComponent是抽象类，应该有必需方法
    assert any(r["check"] == "必需方法: _initialize" for r in results["passed"])
    assert any(r["check"] == "必需方法: execute" for r in results["passed"])
    assert any(r["check"] == "必需方法: get_system_prompt" for r in results["passed"])


@pytest.mark.asyncio
async def test_example_agent_compliance():
    """测试ExampleAgent是否符合接口标准"""
    import sys
    from pathlib import Path

    # 添加examples目录到路径
    examples_path = Path(__file__).parent.parent.parent / "examples"
    sys.path.insert(0, str(examples_path))

    try:
        from example_agent import ExampleAgent

        from core.framework.agents.xiaona.base_component import (
            AgentExecutionContext,
            AgentStatus,
        )

        # 创建Agent实例
        agent = ExampleAgent(agent_id="test_agent")

        # 检查类合规性
        checker = InterfaceComplianceChecker()
        class_results = checker.check_agent_class(ExampleAgent)
        instance_results = checker.check_agent_instance(agent)

        # 输出检查结果
        print("\n=== 类合规性检查 ===")
        for result in class_results["passed"]:
            print(f"✅ {result['check']}: {result['message']}")
        for result in class_results["failed"]:
            print(f"❌ {result['check']}: {result['message']}")

        print("\n=== 实例合规性检查 ===")
        for result in instance_results["passed"]:
            print(f"✅ {result['check']}: {result['message']}")
        for result in instance_results["warnings"]:
            print(f"⚠️  {result['check']}: {result['message']}")
        for result in instance_results["failed"]:
            print(f"❌ {result['check']}: {result['message']}")

        # 断言：应该没有失败项
        assert len(class_results["failed"]) == 0, f"类合规性检查失败: {class_results['failed']}"
        assert len(instance_results["failed"]) == 0, f"实例合规性检查失败: {instance_results['failed']}"

        # 测试execute方法
        context = AgentExecutionContext(
            session_id="SESSION_001",
            task_id="TASK_001",
            input_data={
                "user_input": "test",
                "operation": "example_capability",
            },
            config={},
            metadata={},
        )

        result = await agent.execute(context)

        # 验证返回值
        assert isinstance(result, AgentExecutionResult)
        assert result.agent_id == "test_agent"
        assert result.status in [AgentStatus.COMPLETED, AgentStatus.ERROR]

        if result.status == AgentStatus.COMPLETED:
            assert result.output_data is not None
        else:
            assert result.error_message is not None

    finally:
        # 清理路径
        if str(examples_path) in sys.path:
            sys.path.remove(str(examples_path))


@pytest.mark.asyncio
async def test_retriever_agent_compliance():
    """测试RetrieverAgent是否符合接口标准"""
    from core.framework.agents.xiaona.retiever_agent import RetrieverAgent


    # 创建Agent实例
    agent = RetrieverAgent(agent_id="test_retriever")

    # 检查类合规性
    checker = InterfaceComplianceChecker()
    class_results = checker.check_agent_class(RetrieverAgent)
    instance_results = checker.check_agent_instance(agent)

    # 输出检查结果
    print("\n=== RetrieverAgent 类合规性检查 ===")
    for result in class_results["passed"]:
        print(f"✅ {result['check']}: {result['message']}")
    for result in class_results["failed"]:
        print(f"❌ {result['check']}: {result['message']}")

    print("\n=== RetrieverAgent 实例合规性检查 ===")
    for result in instance_results["passed"]:
        print(f"✅ {result['check']}: {result['message']}")
    for result in instance_results["warnings"]:
        print(f"⚠️  {result['check']}: {result['message']}")
    for result in instance_results["failed"]:
        print(f"❌ {result['check']}: {result['message']}")

    # 断言：应该没有失败项
    assert len(class_results["failed"]) == 0, f"类合规性检查失败: {class_results['failed']}"
    assert len(instance_results["failed"]) == 0, f"实例合规性检查失败: {instance_results['failed']}"

    # 测试能力注册
    capabilities = agent.get_capabilities()
    assert len(capabilities) >= 1, "RetrieverAgent 应该至少注册一个能力"

    # 验证能力名称符合规范（小写+下划线）
    for cap in capabilities:
        assert cap.name.islower() or "_" in cap.name, \
            f"能力名称应该使用小写字母和下划线: {cap.name}"


def test_all_agents_compliance():
    """测试所有Agent是否符合接口标准"""
    from core.framework.agents.xiaona import analyzer_agent, retriever_agent, writer_agent

    agents_to_test = [
        ("RetrieverAgent", retriever_agent.RetrieverAgent),
        ("AnalyzerAgent", analyzer_agent.AnalyzerAgent),
        ("WriterAgent", writer_agent.WriterAgent),
    ]

    checker = InterfaceComplianceChecker()

    for agent_name, agent_class in agents_to_test:
        print(f"\n{'='*60}")
        print(f"测试 {agent_name}")
        print(f"{'='*60}")

        class_results = checker.check_agent_class(agent_class)

        # 创建实例
        try:
            agent = agent_class(agent_id=f"test_{agent_name.lower()}")
            instance_results = checker.check_agent_instance(agent)
        except Exception as e:
            print(f"❌ 创建实例失败: {e}")
            raise AssertionError(f"{agent_name} 创建实例失败: {e}")

        # 统计结果
        total_passed = len(class_results["passed"]) + len(instance_results["passed"])
        total_warnings = len(instance_results["warnings"])
        total_failed = len(class_results["failed"]) + len(instance_results["failed"])

        print(f"\n结果: ✅ {total_passed} | ⚠️  {total_warnings} | ❌ {total_failed}")

        # 断言：不应该有失败项
        assert total_failed == 0, f"{agent_name} 合规性检查失败: {total_failed} 个失败项"


# ==================== 自定义pytest标记 ====================

def pytest_configure(config):
    """配置pytest自定义标记"""
    config.addinivalue_line(
        "markers",
        "compliance: 标记接口合规性测试"
    )


# ==================== 测试工具函数 ====================

def run_compliance_check(agent_class: type[BaseXiaconaComponent]) -> dict:
    """
    运行完整的接口合规性检查

    Args:
        agent_class: Agent类

    Returns:
        检查结果字典
    """
    checker = InterfaceComplianceChecker()

    # 检查类
    class_results = checker.check_agent_class(agent_class)

    # 创建实例
    try:
        agent = agent_class(agent_id="compliance_test_agent")
        instance_results = checker.check_agent_instance(agent)
    except Exception as e:
        return {
            "class_results": class_results,
            "instance_results": None,
            "error": str(e),
        }

    return {
        "class_results": class_results,
        "instance_results": instance_results,
        "summary": {
            "total_passed": len(class_results["passed"]) + len(instance_results["passed"]),
            "total_warnings": len(instance_results["warnings"]),
            "total_failed": len(class_results["failed"]) + len(instance_results["failed"]),
        }
    }


def print_compliance_report(agent_class: Any):
    """
    打印接口合规性检查报告

    Args:
        agent_class: Agent类
    """
    results = run_compliance_check(agent_class)

    print(f"\n{'='*70}")
    print(f"接口合规性检查报告: {agent_class.__name__}")
    print(f"{'='*70}")

    if "error" in results:
        print(f"\n❌ 检查失败: {results['error']}")
        return

    class_results = results["class_results"]
    instance_results = results["instance_results"]
    summary = results["summary"]

    print(f"\n✅ 通过: {summary['total_passed']}")
    print(f"⚠️  警告: {summary['total_warnings']}")
    print(f"❌ 失败: {summary['total_failed']}")

    if class_results["passed"]:
        print("\n类检查 - 通过项:")
        for result in class_results["passed"]:
            print(f"  ✅ {result['check']}: {result['message']}")

    if instance_results["passed"]:
        print("\n实例检查 - 通过项:")
        for result in instance_results["passed"]:
            print(f"  ✅ {result['check']}: {result['message']}")

    if instance_results["warnings"]:
        print("\n实例检查 - 警告项:")
        for result in instance_results["warnings"]:
            print(f"  ⚠️  {result['check']}: {result['message']}")

    if class_results["failed"]:
        print("\n类检查 - 失败项:")
        for result in class_results["failed"]:
            print(f"  ❌ {result['check']}: {result['message']}")

    if instance_results["failed"]:
        print("\n实例检查 - 失败项:")
        for result in instance_results["failed"]:
            print(f"  ❌ {result['check']}: {result['message']}")

    print(f"\n{'='*70}")

    if summary["total_failed"] == 0:
        print(f"✅ {agent_class.__name__} 符合接口标准")
    else:
        print(f"❌ {agent_class.__name__} 不符合接口标准")

    print(f"{'='*70}\n")


if __name__ == "__main__":
    # 直接运行此文件时，执行所有Agent的合规性检查
    from core.framework.agents.xiaona import retriever_agent

    print_compliance_report(retriever_agent.RetrieverAgent)
