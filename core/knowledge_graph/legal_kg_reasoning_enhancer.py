#!/usr/bin/env python3
from __future__ import annotations
"""
法律知识图谱推理增强器
Legal Knowledge Graph Reasoning Enhancer

将法律知识图谱集成到超级推理引擎中,提供图谱增强的推理能力

作者: Athena平台团队
版本: v1.0
创建: 2026-01-22
"""

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .kg_integration import (
    Entity,
    EntityType,
    GraphPath,
    KnowledgeGraphClient,
    Relation,
    RelationType,
    get_kg_client,
)

logger = logging.getLogger(__name__)


class LegalEntityType(Enum):
    """法律实体类型扩展"""

    # 基础法律实体
    LAW = "law"  # 法律
    REGULATION = "regulation"  # 法规
    GUIDELINE = "guideline"  # 指南
    CASE = "case"  # 案例
    PATENT = "patent"  # 专利
    COMPANY = "company"  # 公司
    INVENTOR = "inventor"  # 发明人

    # 法律概念
    LEGAL_CONCEPT = "legal_concept"  # 法律概念
    TECH_CONCEPT = "tech_concept"  # 技术概念
    CLAIM = "claim"  # 权利要求
    EMBODIMENT = "embodiment"  # 实施例

    # 审查相关
    OFFICE_ACTION = "office_action"  # 审查意见
    RESPONSE = "response"  # 答复
    APPEAL = "appeal"  # 申诉
    DECISION = "decision"  # 决定

    # 分类
    IPC_CLASS = "ipc_class"  # IPC分类
    CPC_CLASS = "cpc_class"  # CPC分类
    TECH_FIELD = "tech_field"  # 技术领域


class LegalRelationType(Enum):
    """法律关系类型扩展"""

    # 引用关系
    CITES = "cites"  # 引用
    CITED_BY = "cited_by"  # 被引用
    BASED_ON = "based_on"  # 基于
    APPLIES_TO = "applies_to"  # 应用于

    # 法律关系
    CONFLICTS_WITH = "conflicts_with"  # 冲突
    SUPPORTS = "supports"  # 支持
    CONTRADICTS = "contradicts"  # 矛盾
    PRECEDES = "precedes"  # 先于

    # 归属关系
    ASSIGNED_TO = "assigned_to"  # 受让人
    INVENTED_BY = "invented_by"  # 发明者
    FILED_BY = "filed_by"  # 申请人
    REVIEWED_BY = "reviewed_by"  # 审查员

    # 分类关系
    BELONGS_TO_CLASS = "belongs_to_class"  # 属于分类
    SIMILAR_TO = "similar_to"  # 相似
    RELATED_TO = "related_to"  # 相关

    # 审查关系
    TRIGGERED_BY = "triggered_by"  # 触发
    RESPONDED_TO = "responded_to"  # 答复
    APPEALED_AGAINST = "appealed_against"  # 申诉


@dataclass
class GraphReasoningContext:
    """图谱推理上下文"""

    problem: str  # 推理问题
    entities: list[Entity]  # 识别的实体
    relations: list[Relation]  # 发现的关系
    paths: list[GraphPath]  # 推理路径
    confidence: float = 0.0  # 置信度
    metadata: dict[str, Any] = field(default_factory=dict)  # 元数据


class LegalKGReasoningEnhancer:
    """法律知识图谱推理增强器"""

    def __init__(self, kg_client: KnowledgeGraphClient | None = None):
        """
        初始化推理增强器

        Args:
            kg_client: 知识图谱客户端(如果为None则使用默认客户端)
        """
        self.kg_client = kg_client or get_kg_client()
        self.entity_cache: dict[str, list[Entity]] = {}
        self.relation_cache: dict[str, list[Relation]] = {}

        logger.info("🔗 法律知识图谱推理增强器初始化完成")

    async def enhance_reasoning(
        self, problem: str, reasoning_phase: str = "analysis"
    ) -> GraphReasoningContext:
        """
        增强推理过程

        Args:
            problem: 推理问题
            reasoning_phase: 推理阶段 (analysis, hypothesis, verification, synthesis)

        Returns:
            图谱推理上下文
        """
        logger.info(f"🔍 使用知识图谱增强推理: {reasoning_phase}")

        context = GraphReasoningContext(problem=problem, entities=[], relations=[], paths=[])

        # 1. 识别问题中的实体
        entities = await self._extract_entities(problem)
        context.entities = entities

        # 2. 根据推理阶段执行不同的增强策略
        if reasoning_phase == "analysis":
            # 问题分析阶段:获取实体关系和背景
            await self._enhance_analysis(context)
        elif reasoning_phase == "hypothesis":
            # 假设生成阶段:基于图谱生成假设
            await self._enhance_hypothesis(context)
        elif reasoning_phase == "verification":
            # 验证阶段:使用图谱验证假设
            await self._enhance_verification(context)
        elif reasoning_phase == "synthesis":
            # 综合阶段:整合图谱信息
            await self._enhance_synthesis(context)

        logger.info(
            f"✅ 图谱增强完成,发现{len(context.entities)}个实体,{len(context.relations)}个关系"
        )

        return context

    async def _extract_entities(self, text: str) -> list[Entity]:
        """从文本中提取实体"""
        # 使用知识图谱搜索相关实体
        entities = []

        # 搜索法律概念
        legal_entities = await self.kg_client.search_entities(
            text, entity_type=EntityType.LEGAL, limit=5
        )
        entities.extend(legal_entities)

        # 搜索专利
        patent_entities = await self.kg_client.search_entities(
            text, entity_type=EntityType.PATENT, limit=3
        )
        entities.extend(patent_entities)

        # 搜索技术概念
        tech_entities = await self.kg_client.search_entities(
            text, entity_type=EntityType.CONCEPT, limit=5
        )
        entities.extend(tech_entities)

        # 去重
        seen_ids = set()
        unique_entities = []
        for entity in entities:
            if entity.id not in seen_ids:
                seen_ids.add(entity.id)
                unique_entities.append(entity)

        return unique_entities

    async def _enhance_analysis(self, context: GraphReasoningContext) -> None:
        """增强问题分析阶段"""
        # 获取实体之间的关系
        all_relations = []

        for entity in context.entities:
            # 获取出边关系
            out_rels = await self.kg_client.get_relations(entity.id, direction="out")
            all_relations.extend(out_rels)

            # 获取入边关系
            in_rels = await self.kg_client.get_relations(entity.id, direction="in")
            all_relations.extend(in_rels)

        context.relations = all_relations[:20]  # 限制关系数量

        # 查找实体之间的路径
        if len(context.entities) >= 2:
            paths = await self._find_relevant_paths(context.entities[:3])
            context.paths = paths

    async def _enhance_hypothesis(self, context: GraphReasoningContext) -> None:
        """增强假设生成阶段"""
        # 基于图谱关系生成假设
        hypothesis_hints = []

        # 分析关系模式
        for relation in context.relations:
            if relation.type == RelationType.CITES:
                hypothesis_hints.append(f"实体{relation.from_entity}引用了{relation.to_entity}")
            elif relation.type == RelationType.SIMILAR_TO:
                hypothesis_hints.append(f"实体{relation.from_entity}与{relation.to_entity}相似")
            elif relation.type == RelationType.RELATED_TO:
                hypothesis_hints.append(f"实体{relation.from_entity}与{relation.to_entity}相关")

        context.metadata["hypothesis_hints"] = hypothesis_hints

    async def _enhance_verification(self, context: GraphReasoningContext) -> None:
        """增强验证阶段"""
        # 使用图谱验证推理路径
        verified_paths = []

        for path in context.paths:
            # 检查路径的可靠性
            if self._validate_path(path):
                verified_paths.append(path)

        context.paths = verified_paths

    async def _enhance_synthesis(self, context: GraphReasoningContext) -> None:
        """增强综合阶段"""
        # 整合所有图谱信息
        summary = {
            "entity_count": len(context.entities),
            "relation_count": len(context.relations),
            "path_count": len(context.paths),
            "key_entities": [e.name for e in context.entities[:5]],
            "key_relations": [
                {"from": r.from_entity, "to": r.to_entity, "type": r.type.value}
                for r in context.relations[:5]
            ],
        }

        context.metadata["summary"] = summary

    async def _find_relevant_paths(
        self, entities: list[Entity], max_depth: int = 3
    ) -> list[GraphPath]:
        """查找实体之间的相关路径"""
        paths = []

        # 两两组合查找路径
        for i in range(len(entities)):
            for j in range(i + 1, len(entities)):
                entity_paths = await self.kg_client.find_paths(
                    entities[i].id, entities[j].id, max_depth=max_depth, max_paths=3
                )
                paths.extend(entity_paths)

        # 按路径长度和权重排序
        paths.sort(key=lambda p: (p.length(), -p.score))

        return paths[:5]  # 返回top 5路径

    def _validate_path(self, path: GraphPath) -> bool:
        """验证路径的可靠性"""
        # 检查路径长度
        if path.length() > 3:
            return False

        # 检查路径得分
        if path.score < 0.5:
            return False

        # 检查关系类型
        critical_relations = [
            RelationType.CITES,
            RelationType.CONFLICTS_WITH,
            RelationType.SUPPORTS,
        ]
        has_critical = any(r.type in critical_relations for r in path.relations)

        return has_critical or path.score >= 0.7

    async def get_graph_insights(self, context: GraphReasoningContext) -> list[str]:
        """
        基于图谱上下文生成洞察

        Args:
            context: 图谱推理上下文

        Returns:
            洞察列表
        """
        insights = []

        # 实体洞察
        if len(context.entities) > 0:
            insights.append(f"知识图谱识别了{len(context.entities)}个相关实体")

        # 关系洞察
        if len(context.relations) > 0:
            relation_types = {r.type.value for r in context.relations}
            insights.append(f"发现{len(relation_types)}种关系类型")

        # 路径洞察
        if len(context.paths) > 0:
            avg_length = sum(p.length() for p in context.paths) / len(context.paths)
            insights.append(f"平均推理路径长度: {avg_length:.1f}")

        # 关键实体洞察
        if context.entities:
            key_entities = context.entities[:3]
            entity_names = ", ".join(e.name for e in key_entities)
            insights.append(f"关键实体: {entity_names}")

        return insights

    async def explain_reasoning(self, context: GraphReasoningContext) -> str:
        """
        解释推理过程

        Args:
            context: 图谱推理上下文

        Returns:
            推理解释文本
        """
        explanation = "基于知识图谱的推理分析:\n\n"

        # 实体分析
        if context.entities:
            explanation += f"**识别的实体**({len(context.entities)}个):\n"
            for entity in context.entities[:5]:
                explanation += f"- {entity.name} ({entity.type.value})\n"
            explanation += "\n"

        # 关系分析
        if context.relations:
            explanation += f"**发现的关系**({len(context.relations)}个):\n"
            for relation in context.relations[:5]:
                explanation += (
                    f"- {relation.from_entity} --[{relation.type.value}]--> {relation.to_entity}\n"
                )
            explanation += "\n"

        # 路径分析
        if context.paths:
            explanation += f"**推理路径**({len(context.paths)}条):\n"
            for i, path in enumerate(context.paths[:3], 1):
                path_str = " → ".join([e.name for e in path.entities])
                explanation += f"{i}. {path_str} (得分: {path.score:.2f})\n"

        return explanation


class GraphEnhancedReasoningEngine:
    """图谱增强推理引擎"""

    def __init__(self, kg_client: KnowledgeGraphClient | None = None, llm_client=None):
        """
        初始化引擎

        Args:
            kg_client: 知识图谱客户端
            llm_client: LLM客户端(可选,用于生成图谱增强的推理内容)
        """
        self.kg_enhancer = LegalKGReasoningEnhancer(kg_client)
        self.llm_client = llm_client

        logger.info("🧠 图谱增强推理引擎初始化完成")

    async def reason_with_graph(
        self, problem: str, context: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """
        使用知识图谱增强的推理

        Args:
            problem: 推理问题
            context: 上下文信息

        Returns:
            推理结果
        """
        logger.info(f"🚀 执行图谱增强推理: {problem[:50]}...")

        result = {"problem": problem, "graph_contexts": {}, "insights": [], "reasoning_trace": []}

        # 阶段1: 问题分析(图谱增强)
        analysis_context = await self.kg_enhancer.enhance_reasoning(
            problem, reasoning_phase="analysis"
        )
        result["graph_contexts"]["analysis"] = analysis_context

        # 生成分析洞察
        analysis_insights = await self.kg_enhancer.get_graph_insights(analysis_context)
        result["insights"].extend(analysis_insights)
        result["reasoning_trace"].append(
            {
                "phase": "analysis",
                "entities_found": len(analysis_context.entities),
                "relations_found": len(analysis_context.relations),
                "paths_found": len(analysis_context.paths),
            }
        )

        # 阶段2: 假设生成(图谱增强)
        hypothesis_context = await self.kg_enhancer.enhance_reasoning(
            problem, reasoning_phase="hypothesis"
        )
        result["graph_contexts"]["hypothesis"] = hypothesis_context

        # 提取假设提示
        hypothesis_hints = hypothesis_context.metadata.get("hypothesis_hints", [])
        if hypothesis_hints:
            result["insights"].append(f"图谱生成{len(hypothesis_hints)}个假设提示")

        # 阶段3: 验证(图谱增强)
        verification_context = await self.kg_enhancer.enhance_reasoning(
            problem, reasoning_phase="verification"
        )
        result["graph_contexts"]["verification"] = verification_context

        # 阶段4: 综合(图谱增强)
        synthesis_context = await self.kg_enhancer.enhance_reasoning(
            problem, reasoning_phase="synthesis"
        )
        result["graph_contexts"]["synthesis"] = synthesis_context

        # 生成最终解释
        explanation = await self.kg_enhancer.explain_reasoning(synthesis_context)
        result["graph_explanation"] = explanation

        logger.info("✅ 图谱增强推理完成")

        return result

    async def generate_graph_enhanced_hypotheses(
        self, problem: str, graph_context: GraphReasoningContext, num_hypotheses: int = 3
    ) -> list[dict[str, Any]]:
        """
        基于图谱上下文生成假设

        Args:
            problem: 推理问题
            graph_context: 图谱上下文
            num_hypotheses: 假设数量

        Returns:
            假设列表
        """
        hypotheses = []

        # 如果有LLM客户端,使用LLM生成假设
        if self.llm_client and hasattr(self.llm_client, "_call_llm"):
            # 构建包含图谱信息的提示词
            graph_info = await self.kg_enhancer.explain_reasoning(graph_context)

            system_prompt = """你是一位专业的法律和专利分析专家。
你擅长基于知识图谱信息生成有深度的假设。

请基于提供的知识图谱信息,生成多角度的分析假设。"""

            user_prompt = f"""请基于以下问题生成{num_hypotheses}个假设:

## 问题
{problem}

## 知识图谱信息
{graph_info}

## 要求
1. 结合图谱中的实体和关系
2. 从不同角度分析(系统性、创造性、风险评估等)
3. 每个假设50-100字
4. 按重要性排序

请以JSON格式输出:
```json
{{
  "hypotheses": [
    {{
      "description": "假设描述",
      "confidence": 0.9,
      "basis": "基于图谱的推理依据"
    }}
  ]
}}
```"""

            try:
                response = await self.llm_client._call_llm(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.8,
                    max_tokens=1500,
                )

                # 解析响应
                import re

                json_match = re.search(r"\{[\s\S]*\}", response)
                response_text = json_match.group() if json_match else response

                # 清理markdown
                response_text = response_text.strip()
                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                if response_text.startswith("```"):
                    response_text = response_text[3:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                response_text = response_text.strip()

                result = json.loads(response_text)
                hypotheses = result.get("hypotheses", [])

                logger.info(f"✅ LLM基于图谱生成了{len(hypotheses)}个假设")

            except Exception as e:
                logger.error(f"❌ LLM假设生成失败: {e}")

        # 如果没有LLM或LLM失败,使用基于规则的方法
        if not hypotheses and graph_context.relations:
            # 基于关系生成简单假设
            for i, relation in enumerate(graph_context.relations[:num_hypotheses]):
                hypothesis = {
                    "description": f"基于{relation.type.value}关系,{relation.from_entity}与{relation.to_entity}之间存在重要联系",
                    "confidence": 0.7 - i * 0.1,
                    "basis": f"图谱关系: {relation.type.value}",
                }
                hypotheses.append(hypothesis)

        return hypotheses


# 使用示例
async def main():
    """主函数演示"""
    # 初始化引擎
    engine = GraphEnhancedReasoningEngine()

    # 测试问题
    test_problem = "分析专利创造性的判断标准"

    # 执行图谱增强推理
    result = await engine.reason_with_graph(test_problem)

    # 输出结果
    print("=== 图谱增强推理结果 ===")
    print(f"问题: {result['problem']}")
    print("\n洞察:")
    for insight in result["insights"]:
        print(f"- {insight}")

    print("\n图谱解释:")
    print(result["graph_explanation"])


# 入口点: @async_main装饰器已添加到main函数
