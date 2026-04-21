"""
简化的接口合规性测试

专注于核心功能测试。
"""

import pytest
from typing import Any
from core.agents.xiaona.base_component import (
    BaseXiaonaComponent,
    AgentCapability,
    AgentExecutionContext,
    AgentExecutionResult,
    AgentStatus,
)


class InterfaceComplianceChecker:
    """接口合规性检查器"""

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

        # 3. 检查get_info方法
        try:
            info = agent.get_info()
            if not isinstance(info, dict):
                results["failed"].append({
                    "check": "get_info",
                    "message": "get_info 应该返回字典"
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

@pytest.mark.asyncio
async def test_retriever_agent_compliance():
    """测试RetrieverAgent是否符合接口标准"""
    from core.agents.xiaona.retriever_agent import RetrieverAgent

    # 创建Agent实例
    agent = RetrieverAgent(agent_id="test_retriever")

    # 检查实例合规性
    checker = InterfaceComplianceChecker()
    results = checker.check_agent_instance(agent)

    # 输出检查结果
    print("\n=== RetrieverAgent 实例合规性检查 ===")
    for result in results["passed"]:
        print(f"✅ {result['check']}: {result['message']}")
    for result in results["warnings"]:
        print(f"⚠️  {result['check']}: {result['message']}")
    for result in results["failed"]:
        print(f"❌ {result['check']}: {result['message']}")

    # 断言：应该没有失败项
    assert len(results["failed"]) == 0, f"合规性检查失败: {results['failed']}"

    # 测试能力注册
    capabilities = agent.get_capabilities()
    assert len(capabilities) >= 1, "RetrieverAgent 应该至少注册一个能力"

    # 验证能力名称符合规范（小写+下划线）
    for cap in capabilities:
        assert cap.name.islower() or "_" in cap.name, \
            f"能力名称应该使用小写字母和下划线: {cap.name}"


@pytest.mark.asyncio
async def test_analyzer_agent_compliance():
    """测试AnalyzerAgent是否符合接口标准"""
    from core.agents.xiaona.analyzer_agent import AnalyzerAgent

    # 创建Agent实例
    agent = AnalyzerAgent(agent_id="test_analyzer")

    # 检查实例合规性
    checker = InterfaceComplianceChecker()
    results = checker.check_agent_instance(agent)

    # 输出检查结果
    print("\n=== AnalyzerAgent 实例合规性检查 ===")
    for result in results["passed"]:
        print(f"✅ {result['check']}: {result['message']}")
    for result in results["failed"]:
        print(f"❌ {result['check']}: {result['message']}")

    # 断言：应该没有失败项
    assert len(results["failed"]) == 0, f"合规性检查失败: {results['failed']}"


@pytest.mark.asyncio
async def test_writer_agent_compliance():
    """测试WriterAgent是否符合接口标准"""
    from core.agents.xiaona.writer_agent import WriterAgent

    # 创建Agent实例
    agent = WriterAgent(agent_id="test_writer")

    # 检查实例合规性
    checker = InterfaceComplianceChecker()
    results = checker.check_agent_instance(agent)

    # 输出检查结果
    print("\n=== WriterAgent 实例合规性检查 ===")
    for result in results["passed"]:
        print(f"✅ {result['check']}: {result['message']}")
    for result in results["failed"]:
        print(f"❌ {result['check']}: {result['message']}")

    # 断言：应该没有失败项
    assert len(results["failed"]) == 0, f"合规性检查失败: {results['failed']}"


def test_all_agents_compliance():
    """测试所有Agent是否符合接口标准"""
    from core.agents.xiaona import retriever_agent, analyzer_agent, writer_agent

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

        # 创建实例
        try:
            agent = agent_class(agent_id=f"test_{agent_name.lower()}")
            results = checker.check_agent_instance(agent)
        except Exception as e:
            print(f"❌ 创建实例失败: {e}")
            assert False, f"{agent_name} 创建实例失败: {e}"

        # 统计结果
        total_passed = len(results["passed"])
        total_warnings = len(results["warnings"])
        total_failed = len(results["failed"])

        print(f"\n结果: ✅ {total_passed} | ⚠️  {total_warnings} | ❌ {total_failed}")

        # 断言：不应该有失败项
        assert total_failed == 0, f"{agent_name} 合规性检查失败: {total_failed} 个失败项"


# ==================== 运行测试 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
