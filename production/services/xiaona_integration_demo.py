#!/usr/bin/env python3
"""
小娜与Athena平台集成示例
展示如何将小娜的提示词系统与平台能力集成
"""

from __future__ import annotations
from typing import Any

from xiaona_agent import XiaonaAgent


class XiaonaPlatformIntegration:
    """
    小娜与Athena平台集成

    平台数据资产：
    - Qdrant向量数据库 (patent_rules_complete, patent_decisions, patent_full_text)
    - Neo4j知识图谱 (patent_rules, legal_kg, patent_kg)
    - PostgreSQL专利数据库 (28,036,796件中国专利)
    """

    def __init__(self):
        """初始化集成"""
        self.agent = XiaonaAgent()

        # 平台数据源配置
        self.platform_data_sources = {
            "vector_db": {
                "name": "Qdrant向量数据库",
                "collections": {
                    "patent_rules_complete": 2694,
                    "patent_decisions": 64815,
                    "patent_full_text": 13
                },
                "capability": "语义相似度检索"
            },
            "knowledge_graph": {
                "name": "Neo4j知识图谱",
                "graphs": {
                    "patent_rules": {"nodes": 64913, "edges": 182722},
                    "legal_kg": {"nodes": 22372, "edges": 71314},
                    "patent_kg": {"nodes": 28000000, "edges": 85000000}
                },
                "capability": "关系推理、知识关联"
            },
            "patent_db": {
                "name": "PostgreSQL专利数据库",
                "total_patents": 28036796,
                "capability": "精确检索、结构化查询"
            }
        }

    def execute_task_with_platform_data(self,
                                       task_type: str,
                                       user_input: str,
                                       platform_context: dict[str, Any] = None) -> dict[str, Any]:
        """
        使用平台数据执行任务

        Args:
            task_type: 任务类型 (patent_writing/office_action)
            user_input: 用户输入
            platform_context: 平台上下文信息

        Returns:
            执行结果
        """
        # 1. 获取系统提示词
        system_prompt = self.agent.get_system_prompt(task_type)

        # 2. 构建增强的提示词（包含平台数据信息）
        enhanced_prompt = self._build_enhanced_prompt(system_prompt, platform_context)

        # 3. 执行查询
        response = self.agent.query(user_input, task_type, platform_context)

        # 4. 如果需要，调用平台数据检索
        if self._needs_data_retrieval(user_input, task_type):
            data_results = self._retrieve_from_platform(user_input, task_type)
            response["platform_data"] = data_results

        return response

    def _build_enhanced_prompt(self, base_prompt: str, context: dict[str, Any]) -> str:
        """构建增强提示词"""
        if not context:
            return base_prompt

        # 添加平台数据资产信息
        data_section = f"""

## 📊 Athena平台数据资产

你现在可以使用以下平台数据源：

### 向量数据库 (Qdrant)
- patent_rules_complete: {self.platform_data_sources['vector_db']['collections']['patent_rules_complete']:,} 条专利法条
- patent_decisions: {self.platform_data_sources['vector_db']['collections']['patent_decisions']:,} 条复审无效决定
- patent_full_text: {self.platform_data_sources['vector_db']['collections']['patent_full_text']:,} 条专利全文

### 知识图谱 (Neo4j)
- patent_rules: {self.platform_data_sources['knowledge_graph']['graphs']['patent_rules']['nodes']:,} 个法条节点
- legal_kg: {self.platform_data_sources['knowledge_graph']['graphs']['legal_kg']['nodes']:,} 个法律概念节点
- patent_kg: {self.platform_data_sources['knowledge_graph']['graphs']['patent_kg']['nodes']:,} 个专利节点

### 专利数据库 (PostgreSQL)
- 总专利数: {self.platform_data_sources['patent_db']['total_patents']:,} 件中国专利

在回答问题时，请基于这些真实数据源进行检索和分析。
"""

        return base_prompt + data_section

    def _needs_data_retrieval(self, user_input: str, task_type: str) -> bool:
        """判断是否需要数据检索"""
        retrieval_keywords = [
            "检索", "搜索", "查找", "现有技术", "对比文件",
            "相关案例", "复审决定", "无效决定", "法条"
        ]
        return any(keyword in user_input for keyword in retrieval_keywords)

    def _retrieve_from_platform(self, query: str, task_type: str) -> dict[str, Any]:
        """
        从平台检索数据

        这里是示例，实际应该调用相应的检索服务
        """
        # 模拟检索结果
        return {
            "vector_search": {
                "collection": "patent_decisions",
                "results": [
                    {"id": "决定号: 12345", "score": 0.95, "summary": "类似技术方案的创造性判断"},
                    {"id": "决定号: 67890", "score": 0.89, "summary": "权利要求修改超范围判断"}
                ]
            },
            "graph_query": {
                "graph": "patent_rules",
                "path": ["A26.3", "A26.4", "A22.3"],
                "relationships": ["上位概念", "下位概念", "相关法条"]
            },
            "structured_query": {
                "database": "patent_db",
                "sql": "SELECT * FROM patents WHERE ...",
                "count": 15
            }
        }


def demo_patent_writing_workflow() -> Any:
    """演示专利撰写工作流程"""
    print("=" * 70)
    print("【演示】专利撰写工作流程")
    print("=" * 70)

    integration = XiaonaPlatformIntegration()

    # 任务1: 理解技术交底书
    print("\n📝 任务1: 理解技术交底书")
    print("-" * 70)

    disclosure = """
    技术领域：智能物流
    发明名称：一种基于深度学习的智能分拣系统

    技术问题：
    现有物流分拣效率低、错误率高

    技术方案：
    1. 使用YOLOv5进行目标检测
    2. 使用DeepSORT进行跟踪
    3. 使用强化学习优化分拣路径

    技术效果：
    分拣效率提升40%，错误率降低至0.1%
    """

    response = integration.execute_task_with_platform_data(
        task_type="patent_writing",
        user_input=f"请帮我分析这个技术交底书的核心创新点：\n{disclosure}",
        platform_context={"task": "task_1_1"}
    )

    print(f"小娜: {response['response']}")

    # 任务2: 现有技术调研
    print("\n🔍 任务2: 现有技术调研")
    print("-" * 70)

    response = integration.execute_task_with_platform_data(
        task_type="patent_writing",
        user_input="请在patent_db中检索与'深度学习 物流分拣'相关的现有技术",
        platform_context={"task": "task_1_2"}
    )

    if "platform_data" in response:
        print("小娜: 基于平台数据检索结果：")
        print(f"  - 向量检索: 找到 {len(response['platform_data']['vector_search']['results'])} 条相关决定")
        print(f"  - 图谱推理: 发现法条关联路径 {response['platform_data']['graph_query']['path']}")
        print(f"  - 结构化查询: 检索到 {response['platform_data']['structured_query']['count']} 件相关专利")

    # 任务3: 撰写权利要求书
    print("\n📄 任务3: 撰写权利要求书")
    print("-" * 70)

    response = integration.execute_task_with_platform_data(
        task_type="patent_writing",
        user_input="基于以上分析，帮我起草权利要求书",
        platform_context={"task": "task_1_4"}
    )

    print(f"小娜: {response['response']}")
    if response['need_human_input']:
        print("⚠️  需要您确认权利要求书的保护范围")


def demo_office_action_workflow() -> Any:
    """演示审查意见答复工作流程"""
    print("\n" + "=" * 70)
    print("【演示】审查意见答复工作流程")
    print("=" * 70)

    integration = XiaonaPlatformIntegration()

    # 任务1: 解读审查意见
    print("\n📋 任务1: 解读审查意见")
    print("-" * 70)

    office_action = """
    审查意见通知书

    驳回理由：
    1. 权利要求1-3不具备创造性 (专利法第22条第3款)
    2. 权利要求4不清楚 (专利法第26条第4款)

    引用对比文件：
    D1: CN112345678A (公开日期: 2020-05-15)
    D2: US2021234567A1 (公开日期: 2021-03-20)
    """

    response = integration.execute_task_with_platform_data(
        task_type="office_action",
        user_input=f"请帮我分析这个审查意见：\n{office_action}",
        platform_context={"task": "task_2_1"}
    )

    print(f"小娜: {response['response']}")

    # 任务2: 分析驳回理由
    print("\n🔎 任务2: 分析驳回理由")
    print("-" * 70)

    response = integration.execute_task_with_platform_data(
        task_type="office_action",
        user_input="请检索patent_decisions中关于A22.3创造性的类似案例",
        platform_context={"task": "task_2_2"}
    )

    if "platform_data" in response:
        print("小娜: 基于复审决定库检索结果：")
        for result in response['platform_data']['vector_search']['results']:
            print(f"  - {result['id']} (相似度: {result['score']:.2f})")
            print(f"    {result['summary']}")

    # 任务3: 制定答复策略
    print("\n💡 任务3: 制定答复策略")
    print("-" * 70)

    response = integration.execute_task_with_platform_data(
        task_type="office_action",
        user_input="基于以上分析，请提供答复策略建议",
        platform_context={"task": "task_2_3"}
    )

    print(f"小娜: {response['response']}")
    if response['need_human_input']:
        print("⚠️  需要您选择答复策略")


def demo_multi_scenario_switching() -> Any:
    """演示多场景切换"""
    print("\n" + "=" * 70)
    print("【演示】多场景切换")
    print("=" * 70)

    agent = XiaonaAgent()

    # 场景1: 通用协作
    print("\n🔄 切换到: 通用协作模式")
    print(agent.switch_scenario("general"))

    # 场景2: 专利撰写
    print("\n🔄 切换到: 专利撰写模式")
    print(agent.switch_scenario("patent_writing"))

    # 场景3: 意见答复
    print("\n🔄 切换到: 意见答复模式")
    print(agent.switch_scenario("office_action"))


def main() -> None:
    """主函数"""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║  小娜智能代理 - Athena平台集成演示                               ║
║                                                                  ║
║  四层提示词架构 + 平台数据资产 + HITL人机协作                    ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """)

    # 演示1: 专利撰写工作流程
    demo_patent_writing_workflow()

    # 演示2: 审查意见答复工作流程
    demo_office_action_workflow()

    # 演示3: 多场景切换
    demo_multi_scenario_switching()

    print("\n" + "=" * 70)
    print("✅ 演示完成！")
    print("=" * 70)
    print("""
小娜已准备就绪，可以开始为您服务：

📋 可用场景:
  1. 专利撰写模式 (task_1_1 → task_1_5)
  2. 意见答复模式 (task_2_1 → task_2_4)
  3. 通用协作模式 (全部10大能力)

🔗 平台集成:
  - Qdrant向量数据库: 语义检索
  - Neo4j知识图谱: 关系推理
  - PostgreSQL专利数据库: 精确查询

🤝 HITL人机协作:
  - 关键决策点需要您的确认
  - 支持中断、回退、偏好学习
  - 完整的对话历史记录

使用示例:
  integration = XiaonaPlatformIntegration()
  response = integration.execute_task_with_platform_data(
      task_type="patent_writing",
      user_input="您的请求...",
      platform_context={"task": "task_1_1"}
  )
    """)


if __name__ == "__main__":
    main()
