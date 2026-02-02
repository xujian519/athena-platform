#!/usr/bin/env python3
"""
权威文档专业Agent系统
针对专利、商标、法律等领域的专业AI Agent
作者: Athena AI Team
创建时间: 2026-01-19
版本: v1.0.0
"""

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Agent角色"""

    PATENT_LAW = "patent_law"  # 专利法律专家
    GUIDELINE = "guideline"  # 审查指南专家
    RULE = "rule"  # 规则解析专家
    DECISION = "decision"  # 决定分析专家
    COORDINATOR = "coordinator"  # 协调器


@dataclass
class AgentTask:
    """Agent任务"""

    task_id: str
    query: str
    task_type: str
    context: dict[str, Any]
    priority: int = 0


@dataclass
class AgentResponse:
    """Agent响应"""

    agent_role: AgentRole
    task_id: str
    content: str
    sources: list[dict[str, Any]]
    confidence: float
    reasoning: str


class AuthoritativeAgent:
    """权威文档专业Agent基类"""

    def __init__(
        self,
        role: AgentRole,
        name: str,
        description: str,
        knowledge_base: list[str] | None = None,
    ):
        """
        初始化Agent

        Args:
            role: Agent角色
            name: Agent名称
            description: Agent描述
            knowledge_base: 知识库article_id列表
        """
        self.role = role
        self.name = name
        self.description = description
        self.knowledge_base = knowledge_base or []

        logger.info(f"✅ Agent初始化: {self.name} ({self.role.value})")

    def analyze(
        self, task: AgentTask, search_results: list[dict[str, Any]] | None = None
    ) -> AgentResponse:
        """
        分析任务

        Args:
            task: 任务对象
            search_results: 检索结果

        Returns:
            Agent响应
        """
        raise NotImplementedError("子类必须实现analyze方法")

    def extract_key_points(self, documents: list[dict[str, Any]]) -> list[str]:
        """从文档中提取关键点"""
        key_points = []

        for doc in documents:
            content = doc.get("content", "")
            title = doc.get("title", "")

            # 简单提取: 取前200字符作为关键点
            if content:
                key_point = f"{title}: {content[:200]}..."
                key_points.append(key_point)

        return key_points

    def format_citation(self, doc: dict[str, Any]) -> str:
        """格式化引用"""
        article_type = doc.get("article_type", "")
        article_id = doc.get("article_id", "")
        title = doc.get("title", "")

        type_map = {"law": "法律", "guideline": "审查指南", "rule": "规则", "decision": "决定"}

        type_name = type_map.get(article_type, article_type)
        return f"[{type_name}] {title} ({article_id})"


class PatentLawAgent(AuthoritativeAgent):
    """专利法律专家Agent"""

    def __init__(self):
        super().__init__(
            role=AgentRole.PATENT_LAW,
            name="专利法律专家",
            description="专门解读专利法律条文,提供法理依据",
            knowledge_base=["law"],  # 专注于法律文档
        )

    def analyze(
        self, task: AgentTask, search_results: list[dict[str, Any]] | None = None
    ) -> AgentResponse:
        """
        分析专利法律问题

        关注点:
        - 法律条文解读
        - 法理依据分析
        - 法律适用性判断
        """
        if not search_results:
            return AgentResponse(
                agent_role=self.role,
                task_id=task.task_id,
                content="未找到相关法律文档",
                sources=[],
                confidence=0.0,
                reasoning="无数据支持",
            )

        # 筛选法律文档
        law_docs = [doc for doc in search_results if doc.get("article_type") == "law"]

        if not law_docs:
            return AgentResponse(
                agent_role=self.role,
                task_id=task.task_id,
                content="未找到专利法律相关条文",
                sources=[],
                confidence=0.3,
                reasoning="检索结果中无法律文档",
            )

        # 提取法律要点
        key_points = []
        sources = []

        for doc in law_docs[:3]:  # 取Top-3
            title = doc.get("title", "")
            content = doc.get("content", "")
            article_id = doc.get("article_id", "")

            # 提取法律条文
            if content:
                key_point = f"根据{title}:{content[:300]}..."
                key_points.append(key_point)
                sources.append(
                    {
                        "article_id": article_id,
                        "title": title,
                        "type": "law",
                        "citation": self.format_citation(doc),
                    }
                )

        content = "\n\n".join(key_points)
        reasoning = f"基于{len(law_docs)}条法律文档分析"

        return AgentResponse(
            agent_role=self.role,
            task_id=task.task_id,
            content=content,
            sources=sources,
            confidence=0.85 if len(law_docs) >= 2 else 0.6,
            reasoning=reasoning,
        )


class GuidelineAgent(AuthoritativeAgent):
    """审查指南专家Agent"""

    def __init__(self):
        super().__init__(
            role=AgentRole.GUIDELINE,
            name="审查指南专家",
            description="专门解读专利审查指南,提供操作指引",
            knowledge_base=["guideline"],
        )

    def analyze(
        self, task: AgentTask, search_results: list[dict[str, Any]] | None = None
    ) -> AgentResponse:
        """
        分析审查指南问题

        关注点:
        - 审查标准解读
        - 操作指南说明
        - 审查流程指引
        """
        if not search_results:
            return AgentResponse(
                agent_role=self.role,
                task_id=task.task_id,
                content="未找到相关审查指南",
                sources=[],
                confidence=0.0,
                reasoning="无数据支持",
            )

        # 筛选审查指南文档
        guideline_docs = [doc for doc in search_results if doc.get("article_type") == "guideline"]

        if not guideline_docs:
            return AgentResponse(
                agent_role=self.role,
                task_id=task.task_id,
                content="未找到相关审查指南章节",
                sources=[],
                confidence=0.3,
                reasoning="检索结果中无审查指南文档",
            )

        # 提取审查要点
        key_points = []
        sources = []

        for doc in guideline_docs[:5]:  # 取Top-5
            title = doc.get("title", "")
            content = doc.get("content", "")
            article_id = doc.get("article_id", "")
            hierarchy_level = doc.get("hierarchy_level", 0)

            # 按层级组织内容
            level_prefix = "  " * hierarchy_level
            if content:
                key_point = f"{level_prefix}● {title}\n{level_prefix}  {content[:200]}..."
                key_points.append(key_point)
                sources.append(
                    {
                        "article_id": article_id,
                        "title": title,
                        "type": "guideline",
                        "hierarchy_level": hierarchy_level,
                        "citation": self.format_citation(doc),
                    }
                )

        content = "\n\n".join(key_points)
        reasoning = f"基于{len(guideline_docs)}条审查指南分析"

        return AgentResponse(
            agent_role=self.role,
            task_id=task.task_id,
            content=content,
            sources=sources,
            confidence=0.90 if len(guideline_docs) >= 3 else 0.7,
            reasoning=reasoning,
        )


class RuleAgent(AuthoritativeAgent):
    """规则解析专家Agent"""

    def __init__(self):
        super().__init__(
            role=AgentRole.RULE,
            name="规则解析专家",
            description="专门分析具体规则,提供执行细节",
            knowledge_base=["rule"],
        )

    def analyze(
        self, task: AgentTask, search_results: list[dict[str, Any]] | None = None
    ) -> AgentResponse:
        """
        分析规则问题

        关注点:
        - 规则条文解析
        - 执行要点说明
        - 注意事项提醒
        """
        if not search_results:
            return AgentResponse(
                agent_role=self.role,
                task_id=task.task_id,
                content="未找到相关规则",
                sources=[],
                confidence=0.0,
                reasoning="无数据支持",
            )

        # 筛选规则文档
        rule_docs = [doc for doc in search_results if doc.get("article_type") == "rule"]

        if not rule_docs:
            return AgentResponse(
                agent_role=self.role,
                task_id=task.task_id,
                content="未找到相关规则条文",
                sources=[],
                confidence=0.3,
                reasoning="检索结果中无规则文档",
            )

        # 提取规则要点
        key_points = []
        sources = []

        for doc in rule_docs[:3]:
            title = doc.get("title", "")
            content = doc.get("content", "")
            article_id = doc.get("article_id", "")

            if content:
                key_point = f"规则: {title}\n内容: {content[:200]}..."
                key_points.append(key_point)
                sources.append(
                    {
                        "article_id": article_id,
                        "title": title,
                        "type": "rule",
                        "citation": self.format_citation(doc),
                    }
                )

        content = "\n\n".join(key_points)
        reasoning = f"基于{len(rule_docs)}条规则分析"

        return AgentResponse(
            agent_role=self.role,
            task_id=task.task_id,
            content=content,
            sources=sources,
            confidence=0.75 if len(rule_docs) >= 2 else 0.5,
            reasoning=reasoning,
        )


class DecisionAgent(AuthoritativeAgent):
    """决定分析专家Agent"""

    def __init__(self):
        super().__init__(
            role=AgentRole.DECISION,
            name="决定分析专家",
            description="专门分析复审无效决定,提供案例参考",
            knowledge_base=["decision"],
        )

    def analyze(
        self, task: AgentTask, search_results: list[dict[str, Any]] | None = None
    ) -> AgentResponse:
        """
        分析决定案例

        关注点:
        - 案例检索
        - 决定理由分析
        - 裁决趋势总结
        """
        if not search_results:
            return AgentResponse(
                agent_role=self.role,
                task_id=task.task_id,
                content="未找到相关决定案例",
                sources=[],
                confidence=0.0,
                reasoning="无数据支持",
            )

        # 简化: 这里应该查询复审无效决定数据库
        # 暂时返回通用信息
        content = "案例分析功能需要连接复审无效决定数据库。当前基于文档类型,建议参考相关审查指南和法律条文。"

        return AgentResponse(
            agent_role=self.role,
            task_id=task.task_id,
            content=content,
            sources=[],
            confidence=0.4,
            reasoning="案例数据库未集成",
        )


class AgentCoordinator:
    """Agent协调器"""

    def __init__(self):
        """初始化协调器"""
        self.agents = {
            AgentRole.PATENT_LAW: PatentLawAgent(),
            AgentRole.GUIDELINE: GuidelineAgent(),
            AgentRole.RULE: RuleAgent(),
            AgentRole.DECISION: DecisionAgent(),
        }

        logger.info(f"✅ Agent协调器初始化完成,注册{len(self.agents)}个专业Agent")

    def coordinate(
        self, query: str, search_results: list[dict[str, Any]], task_type: str = "general"
    ) -> dict[str, Any]:
        """
        协调多个Agent进行分析

        Args:
            query: 用户查询
            search_results: 检索结果
            task_type: 任务类型

        Returns:
            融合后的分析结果
        """
        task = AgentTask(
            task_id=f"task_{int(time.time())}",
            query=query,
            task_type=task_type,
            context={"search_results_count": len(search_results)},
        )

        # 并行调用所有Agent
        responses = {}
        for role, agent in self.agents.items():
            try:
                response = agent.analyze(task, search_results)
                responses[role] = response
            except Exception as e:
                logger.error(f"❌ Agent {role} 分析失败: {e}")

        # 融合结果
        fused_result = self._fuse_responses(query, responses)

        return fused_result

    def _fuse_responses(
        self, query: str, responses: dict[AgentRole, AgentResponse]
    ) -> dict[str, Any]:
        """
        融合多个Agent的响应

        融合策略:
        - GuidelineAgent主导 (审查指南最详细)
        - PatentLawAgent补充 (法律依据)
        - RuleAgent支持 (执行细节)
        - DecisionAgent参考 (案例支持)
        """
        fused = {
            "query": query,
            "analysis": {},
            "sources": [],
            "confidence": 0.0,
            "agent_count": len(responses),
        }

        # 按优先级组织响应
        priority_order = [
            AgentRole.GUIDELINE,
            AgentRole.PATENT_LAW,
            AgentRole.RULE,
            AgentRole.DECISION,
        ]

        total_confidence = 0.0
        valid_responses = 0

        for role in priority_order:
            if role in responses:
                response = responses[role]

                # 添加到分析结果
                fused["analysis"][role.value] = {
                    "content": response.content,
                    "confidence": response.confidence,
                    "reasoning": response.reasoning,
                }

                # 合并来源
                fused["sources"].extend(response.sources)

                # 累加置信度
                total_confidence += response.confidence
                valid_responses += 1

        # 计算平均置信度
        fused["confidence"] = total_confidence / max(valid_responses, 1)

        # 去重来源
        seen_ids = set()
        unique_sources = []
        for source in fused["sources"]:
            article_id = source.get("article_id")
            if article_id and article_id not in seen_ids:
                seen_ids.add(article_id)
                unique_sources.append(source)

        fused["sources"] = unique_sources

        return fused


# 便捷函数
_agent_coordinator_instance = None


def get_agent_coordinator() -> AgentCoordinator:
    """获取Agent协调器单例"""
    global _agent_coordinator_instance
    if _agent_coordinator_instance is None:
        _agent_coordinator_instance = AgentCoordinator()
    return _agent_coordinator_instance


# 使用示例
if __name__ == "__main__":
    import time

    print("=" * 80)
    print("🧪 权威文档专业Agent系统测试")
    print("=" * 80)
    print()

    # 创建协调器
    coordinator = get_agent_coordinator()

    # 模拟检索结果
    search_results = [
        {
            "article_id": "L1_2",
            "article_type": "law",
            "title": "专利法",
            "content": "授予专利权的发明和实用新型,应当具备新颖性、创造性和实用性。",
            "hierarchy_level": 0,
            "score": 0.8,
        },
        {
            "article_id": "L2_2_3",
            "article_type": "guideline",
            "title": "创造性",
            "content": "创造性是指与现有技术相比,该发明有突出的实质性特点和显著的进步。",
            "hierarchy_level": 1,
            "score": 0.9,
        },
        {
            "article_id": "R1",
            "article_type": "rule",
            "title": "审查规则",
            "content": "专利审查的具体规则和流程。",
            "hierarchy_level": 1,
            "score": 0.7,
        },
    ]

    query = "专利创造性判断标准"

    print(f"查询: {query}")
    print(f"检索结果: {len(search_results)} 条\n")

    # 协调分析
    result = coordinator.coordinate(query, search_results)

    print("融合分析结果:")
    print("-" * 80)

    for role, analysis in result["analysis"].items():
        print(f"\n[{role.upper()}]")
        print(f"置信度: {analysis['confidence']:.2f}")
        print(f"推理: {analysis['reasoning']}")
        print(f"内容:\n{analysis['content'][:200]}...")

    print(f"\n\n总置信度: {result['confidence']:.2f}")
    print(f"参与Agent数: {result['agent_count']}")
    print(f"引用来源数: {len(result['sources'])}")

    print("\n" + "=" * 80)
