#!/usr/bin/env python3
"""
Co-STORM + Athena 集成测试脚本

测试已实现的 STORM 集成模块,验证端到端功能。

测试内容:
1. 专利视角发现器
2. 多专家 Agent 对话模拟
3. 信息策展(待实现)
4. 协作话语管理(待实现)
5. 思维导图构建(待实现)

作者: Athena 平台团队
创建时间: 2025-01-02
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.storm_integration.patent_agents import (
    AgentFactory,
    AgentRole,
    Conversation,
    simulate_patent_conversation,
)
from core.storm_integration.patent_perspectives import (
    PatentBasicInfo,
    PatentPerspectiveDiscoverer,
    discover_patent_perspectives,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class StormIntegrationTester:
    """STORM 集成测试器"""

    def __init__(self):
        self.test_results = []

    def run_all_tests(self) -> Any:
        """运行所有测试"""
        print("\n" + "=" * 70)
        print(" " * 20 + "Co-STORM + Athena 集成测试")
        print("=" * 70)
        print(f"\n测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        tests = [
            ("专利视角发现器", self.test_perspective_discoverer),
            ("专家 Agent 创建", self.test_agent_creation),
            ("多专家对话模拟", self.test_conversation_simulation),
            ("端到端流程", self.test_end_to_end),
        ]

        passed = 0
        failed = 0

        for test_name, test_func in tests:
            print("\n" + "-" * 70)
            print(f"📋 测试: {test_name}")
            print("-" * 70)

            try:
                result = test_func()
                if result:
                    print(f"✅ {test_name}: 通过")
                    passed += 1
                    self.test_results.append((test_name, "PASS", None))
                else:
                    print(f"⚠️  {test_name}: 未通过")
                    failed += 1
                    self.test_results.append((test_name, "FAIL", "Test returned False"))
            except Exception as e:
                print(f"❌ {test_name}: 异常")
                print(f"   错误: {e}")
                failed += 1
                self.test_results.append((test_name, "ERROR", str(e)))

        # 打印总结
        print("\n" + "=" * 70)
        print("测试总结")
        print("=" * 70)
        print(f"总计: {passed + failed} 个测试")
        print(f"通过: {passed} 个 ✅")
        print(f"失败: {failed} 个 ❌")
        print(f"通过率: {passed/(passed+failed)*100:.1f}%")

        return failed == 0

    def test_perspective_discoverer(self) -> bool:
        """测试专利视角发现器"""
        # 创建测试专利信息
        patent_info = PatentBasicInfo(
            patent_id="CN202310123456.7",
            title="一种基于深度学习的图像识别方法及系统",
            abstract="本发明公开了一种基于深度学习的图像识别方法,涉及人工智能技术领域。该方法通过改进的卷积神经网络架构,实现了高精度的图像识别...",
            applicant="某人工智能科技有限公司",
            inventor="张三, 李四, 王五",
            application_date="2023-05-15",
            ipc_classification="G06N3/00",
            claims=[
                "1. 一种基于深度学习的图像识别方法,其特征在于,包括:获取待识别图像;通过改进的卷积神经网络提取图像特征;基于注意力机制优化特征表示;通过分类器输出识别结果。",
                "2. 根据权利要求1所述的方法,其特征在于,所述改进的卷积神经网络采用残差连接。",
            ],
        )

        # 发现视角
        discoverer = PatentPerspectiveDiscoverer()
        perspectives = discoverer.discover(patent_info)

        # 验证结果
        assert len(perspectives) >= 5, "应该发现至少5个视角"

        # 验证必需的视角类型
        perspective_types = [p.type.value for p in perspectives]
        required_types = ["technical", "legal", "temporal", "applicant", "market"]
        for req_type in required_types:
            assert req_type in perspective_types, f"缺少 {req_type} 视角"

        # 打印结果
        print(f"\n发现 {len(perspectives)} 个分析视角:")
        for i, p in enumerate(perspectives, 1):
            print(f"  {i}. {p.name} (优先级: {p.priority})")
            print(f"     {p.description}")
            print(f"     关键问题: {p.questions[0]}")

        return True

    def test_agent_creation(self) -> bool:
        """测试 Agent 创建"""
        agents = []

        # 测试创建所有类型的 Agent
        for role in AgentRole:
            agent = AgentFactory.create_agent(role)
            agents.append(agent)

            # 验证 Agent 属性
            assert agent.agent_id, "Agent ID 不应为空"
            assert agent.agent_name, "Agent 名称不应为空"
            assert agent.role == role, "Agent 角色不匹配"

            print(f"\n✅ 创建成功: {agent.agent_name} ({role.value})")

        # 测试批量创建
        all_agents = AgentFactory.create_all_agents()
        assert len(all_agents) == 3, "应该创建3个 Agent"

        return True

    def test_conversation_simulation(self) -> bool:
        """测试对话模拟"""
        # 模拟对话
        conversation = simulate_patent_conversation(
            topic="一种基于深度学习的图像识别方法",
            perspectives=["技术分析视角", "法律分析视角", "创造性评估"],
            max_turns=6,  # 2轮完整对话
        )

        # 验证对话
        assert conversation.topic, "对话主题不应为空"
        assert len(conversation.utterances) == 6, "应该有6轮对话"

        # 打印对话内容
        print(f"\n对话主题: {conversation.topic}")
        print(f"\n对话记录 (共 {len(conversation.utterances)} 轮):\n")

        for utterance in conversation.utterances:
            print(f"[轮次 {utterance.turn + 1}] {utterance.agent_name}:")
            print(f"{utterance.content}")
            print(f"查询: {utterance.queries}")
            print(f"引用: {len(utterance.citations)} 条")
            print()

        # 验证引用
        all_citations = conversation.get_all_citations()
        print(f"总共收集 {len(all_citations)} 条引用")

        return True

    def test_end_to_end(self) -> bool:
        """端到端测试"""
        print("\n端到端流程测试:")
        print("-" * 70)

        # 步骤1: 准备专利信息
        print("\n[步骤1] 准备专利信息...")
        patent_info = PatentBasicInfo(
            patent_id="CN202310999999.9",
            title="智能专利检索系统及方法",
            abstract="本发明提供一种智能专利检索系统,通过深度学习技术实现语义检索...",
            applicant="Athena 科技有限公司",
            inventor="徐健, 小娜, 小诺",
            application_date="2024-01-01",
            ipc_classification="G06F16/00",
        )
        print(f"  专利: {patent_info.title}")
        print(f"  申请人: {patent_info.applicant}")

        # 步骤2: 发现分析视角
        print("\n[步骤2] 发现分析视角...")
        discoverer = PatentPerspectiveDiscoverer()
        perspectives = discoverer.discover(patent_info)
        print(f"  发现 {len(perspectives)} 个视角")

        # 步骤3: 创建专家团队
        print("\n[步骤3] 创建专家团队...")
        agents = AgentFactory.create_all_agents()
        print(f"  创建 {len(agents)} 个专家 Agent")
        for agent in agents:
            print(f"    - {agent.agent_name}")

        # 步骤4: 模拟多视角讨论
        print("\n[步骤4] 模拟专家讨论...")
        conversation = Conversation(topic=patent_info.title)

        perspective_names = [p.name for p in perspectives[:3]]
        print(f"  讨论视角: {', '.join(perspective_names)}")

        for i in range(3):
            perspective = perspectives[i]
            agent = agents[i]

            utterance = agent.speak(
                conversation_history=conversation.utterances,
                current_perspective=perspective.name,
                context={"patent_info": patent_info},
            )
            conversation.add_utterance(utterance)

            print(f"\n  [{i+1}] {agent.agent_name} ({perspective.name}):")
            print(f"      {utterance.content[:100]}...")

        # 步骤5: 生成摘要报告
        print("\n[步骤5] 生成摘要报告...")
        report = self._generate_summary_report(conversation, perspectives)
        print(report)

        return True

    def _generate_summary_report(self, conversation: Conversation, perspectives: list) -> str:
        """生成摘要报告"""
        report = f"""
{'='*60}
专利分析摘要报告
{'='*60}

专利主题: {conversation.topic}
分析视角: {len(perspectives)} 个
对话轮次: {len(conversation.utterances)} 轮
收集引用: {len(conversation.get_all_citations())} 条

{'='*60}
专家观点摘要
{'='*60}
"""

        for utterance in conversation.utterances:
            report += f"\n[{utterance.agent_name}]\n"
            report += f"{utterance.content}\n"

        report += f"\n{'='*60}\n"
        report += "下一步建议:\n"
        report += "1. 基于专家观点,进行更深入的现有技术检索\n"
        report += "2. 重点分析技术方案的创造性\n"
        report += "3. 评估权利要求的保护范围\n"
        report += "4. 准备审查意见答复策略\n"

        return report


def main() -> None:
    """主函数"""
    tester = StormIntegrationTester()
    success = tester.run_all_tests()

    if success:
        print("\n🎉 所有测试通过!")
        print("\n下一步:")
        print("1. 集成 STORM 的信息策展模块")
        print("2. 实现协作话语管理器")
        print("3. 开发思维导图可视化")
        print("4. 集成到小娜的 CAP 能力")
        return 0
    else:
        print("\n⚠️  部分测试未通过,请检查问题")
        return 1


if __name__ == "__main__":
    exit(main())
