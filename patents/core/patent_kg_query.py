#!/usr/bin/env python3
from __future__ import annotations
"""
专利知识图谱查询接口
Patent Knowledge Graph Query Interface

轻量级知识图谱查询接口，用于动态提示词生成

Author: Athena平台团队
Created: 2026-01-26
Version: v1.0.0
"""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class PatentKGQueryInterface:
    """
    专利知识图谱查询接口

    轻量级实现，支持：
    1. 术语定义查询
    2. 技术领域知识查询
    3. 法律条文查询
    4. 答复策略查询
    5. 相似案例查询
    """

    def __init__(self, data_path: str | None = None):
        """初始化查询接口"""
        self.data_path = data_path or "data/knowledge_graph/patent_kg_data.json"
        self.kg_data = self._load_kg_data()

        logger.info("✅ 专利知识图谱查询接口初始化完成")

    def _load_kg_data(self) -> dict:
        """加载知识图谱数据"""
        # 如果文件不存在，返回默认数据
        if not Path(self.data_path).exists():
            logger.info("📝 知识图谱数据文件不存在，使用内置数据")
            return self._get_builtin_data()

        try:
            with open(self.data_path, encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"✅ 已加载知识图谱数据: {len(data.get('terms', []))}个术语")
            return data
        except Exception as e:
            logger.error(f"❌ 加载知识图谱数据失败: {e}")
            return self._get_builtin_data()

    def _get_builtin_data(self) -> dict:
        """获取内置的默认数据"""
        return {
            "terms": self._get_ai_terms(),
            "legal_articles": self._get_legal_articles(),
            "response_strategies": self._get_response_strategies(),
            "technical_effects": self._get_technical_effects(),
            "argumentation_templates": self._get_argumentation_templates()
        }

    def _get_ai_terms(self) -> list[dict]:
        """获取AI相关术语（2442个术语的简化版本）"""
        return [
            {"term": "创造性", "definition": "专利法第22条第3款规定的发明创造性，指同现有技术相比，该发明有突出的实质性特点和显著的进步。", "related_concepts": ["显而易见性", "技术启示", "预料不到的技术效果"]},
            {"term": "显而易见性", "definition": "指所属技术领域的技术人员根据现有技术的教导，容易想到将该技术应用于其他技术领域。", "related_concepts": ["技术启示", "常规手段", "本领域技术人员"]},
            {"term": "技术启示", "definition": "指对比文件给出的将对比文件与其他技术结合的教导或指引。", "related_concepts": ["显而易见性", "结合动机"]},
            {"term": "预料不到的技术效果", "definition": "指发明同现有技术相比，产生超出人们预测范围的技术效果。", "related_concepts": ["创造性", "显著性", "商业成功"]},
            {"term": "突出的实质性特点", "definition": "指发明相对于现有技术，具有本质的区别或显著的变化。", "related_concepts": ["创造性", "本质区别"]},
            {"term": "显著的进步", "definition": "指发明与现有技术相比，产生了有益的技术效果。", "related_concepts": ["创造性", "技术效果", "有益效果"]},
            {"term": "四要素协同", "definition": "指四个技术要素组合使用时，产生的效果远大于单独使用效果之和。", "related_concepts": ["协同效应", "组合发明"]},
            {"term": "参数选择", "definition": "指对技术参数进行特定范围内的选择，以达到意想不到的技术效果。", "related_concepts": ["技术参数", "优化"]},
        ]

    def _get_legal_articles(self) -> list[dict]:
        """获取法律条文"""
        return [
            {
                "article": "专利法第22条第3款",
                "content": "创造性，是指同现有技术相比，该发明有突出的实质性特点和显著的进步。",
                "application": "用于判断发明是否具备创造性"
            },
            {
                "article": "专利法第22条第2款",
                "content": "新颖性，是指该发明不属于现有技术；也没有任何单位或者个人就同样的发明在申请日以前向专利局提出过申请。",
                "application": "用于判断发明是否具备新颖性"
            },
            {
                "article": "专利法第26条第3款",
                "content": "说明书应当对发明作出清楚、完整的说明，以所属技术领域的技术人员能够实现为准。",
                "application": "用于判断说明书公开是否充分"
            },
            {
                "article": "专利法实施细则第20条第2款",
                "content": "技术启示是指对比文件给出的将对比文件与其他技术结合的教导。",
                "application": "用于判断显而易见性"
            }
        ]

    def _get_response_strategies(self) -> list[dict]:
        """获取答复策略"""
        return [
            {
                "strategy": "四要素协同论证",
                "description": "强调多个技术要素组合使用时产生的协同效应",
                "key_points": [
                    "单独要素在对比文件中已公开",
                    "但特定组合的协同效果未被公开",
                    "协同效果产生预料不到的技术效果"
                ],
                "evidence_needed": ["对比实验数据", "协同机理分析"]
            },
            {
                "strategy": "参数优化论证",
                "description": "强调特定参数范围内的选择产生了意想不到的效果",
                "key_points": [
                    "参数范围的选择对比文件未公开",
                    "该范围内效果显著优于范围外",
                    "参数优化需要创造性劳动"
                ],
                "evidence_needed": ["参数对比实验", "效果数据对比"]
            },
            {
                "strategy": "技术效果差异论证",
                "description": "强调目标专利的技术效果显著优于对比文件",
                "key_points": [
                    "效果定性差异（完全不同的效果）",
                    "效果定量差异（显著更优的效果）",
                    "对比文件无法达到相同效果"
                ],
                "evidence_needed": ["效果对比数据", "实验结果"]
            },
            {
                "strategy": "技术手段本质区别",
                "description": "强调采用的技术手段与对比文件有本质区别",
                "key_points": [
                    "技术原理不同",
                    "工艺流程不同",
                    "材料组成不同"
                ],
                "evidence_needed": ["技术原理分析", "流程对比图"]
            }
        ]

    def _get_technical_effects(self) -> list[dict]:
        """获取技术效果描述模板"""
        return [
            {
                "effect_type": "去腥味",
                "description": "去除水产品的土腥味",
                "measurement_methods": ["感官评价", "气相色谱分析", "电子鼻检测"],
                "typical_values": {"感官评分": "提高2-3分", "去除率": ">90%"}
            },
            {
                "effect_type": "保鲜",
                "description": "延长产品保质期和新鲜度",
                "measurement_methods": ["货架期测试", "菌落总数", "感官评价"],
                "typical_values": {"保质期延长": "1.5-2倍", "失重率": "<5%"}
            },
            {
                "effect_type": "品质提升",
                "description": "改善产品的品质和口感",
                "measurement_methods": ["质地分析", "营养成分分析", "消费者测试"],
                "typical_values": {"质地改善": "提高20-30%", "营养成分保留": ">90%"}
            },
            {
                "effect_type": "存活率提升",
                "description": "提高活体运输过程中的存活率",
                "measurement_methods": ["存活率统计", "死亡率分析", "应激反应测试"],
                "typical_values": {"存活率": ">95%", "死亡率": "<5%"}
            }
        ]

    def _get_argumentation_templates(self) -> list[dict]:
        """获取论证模板"""
        return [
            {
                "template_name": "协同效应论证",
                "structure": """
# 关于权利要求{claim_number}的创造性陈述

尊敬的审查员：

申请人认为，权利要求{claim_number}具备专利法第22条第3款规定的创造性，理由如下：

## 一、权利要求{claim_number}与对比文件的区别

对比文件{d1}虽然公开了{similar_features}，但未公开{distinguishing_features}。

## 二、四要素协同效应

本申请采用{four_elements}的组合，在特定参数范围内({parameters})产生了显著的协同效应：
1. 单独使用任一要素，去腥效果为{single_effect}%
2. 四要素组合使用，去腥效果达到{combined_effect}%
3. 协同增效达到{synergy_ratio}倍

## 三、预料不到的技术效果

实验数据表明，本申请方法的土腥味去除率达到{removal_rate}%，显著优于对比文件的{prior_art_rate}%。

## 四、结论

综上所述，权利要求{claim_number}相对于对比文件{d1}具有突出的实质性特点和显著的进步，具备创造性。
                """.strip(),
                "variables": ["claim_number", "d1", "similar_features", "distinguishing_features", "four_elements", "parameters", "single_effect", "combined_effect", "synergy_ratio", "removal_rate", "prior_art_rate"]
            },
            {
                "template_name": "参数优化论证",
                "structure": """
# 关于权利要求{claim_number}的创造性陈述

尊敬的审查员：

申请人认为，权利要求{claim_number}具备创造性，理由如下：

## 一、参数选择的创造性

本申请通过大量实验发现，在{parameter_name}为{parameter_range}时，{technical_effect}达到最优。
对比文件虽然使用了{similar_method}，但参数为{prior_parameter}，效果显著不如本申请。

## 二、对比实验数据

| 参数范围 | {effect_metric1} | {effect_metric2} |
|---------|----------------|----------------|
| 本申请   | {our_value1}    | {our_value2}    |
| 对比文件 | {prior_value1}  | {prior_value2}  |

## 三、预料不到的技术效果

本申请在{parameter_range}范围内的效果提升达到了{improvement_rate}%，这是对比文件无法预见的。

## 四、结论

权利要求{claim_number}通过参数优化达到了意想不到的技术效果，具备创造性。
                """.strip(),
                "variables": ["claim_number", "parameter_name", "parameter_range", "technical_effect", "similar_method", "prior_parameter", "effect_metric1", "effect_metric2", "our_value1", "our_value2", "prior_value1", "prior_value2", "improvement_rate"]
            }
        ]

    def query_term_definition(self, term: str) -> dict | None:
        """
        查询术语定义

        Args:
            term: 术语名称

        Returns:
            术语定义和相关概念
        """
        for term_data in self.kg_data.get("terms", []):
            if term_data["term"] == term:
                return term_data

        # 模糊匹配
        for term_data in self.kg_data.get("terms", []):
            if term.lower() in term_data["term"].lower() or term_data["term"].lower() in term.lower():
                return term_data

        return None

    def query_legal_article(self, article_name: str) -> dict | None:
        """
        查询法律条文

        Args:
            article_name: 法律条文名称（如"专利法第22条第3款"）

        Returns:
            法律条文内容
        """
        for article in self.kg_data.get("legal_articles", []):
            if article_name in article["article"] or article["article"] in article_name:
                return article

        return None

    def query_response_strategy(self, strategy_name: str) -> dict | None:
        """
        查询答复策略

        Args:
            strategy_name: 策略名称

        Returns:
            策略详情和要点
        """
        for strategy in self.kg_data.get("response_strategies", []):
            if strategy_name in strategy["strategy"] or strategy["strategy"] in strategy_name:
                return strategy

        return None

    def query_technical_effect(self, effect_type: str) -> dict | None:
        """
        查询技术效果信息

        Args:
            effect_type: 效果类型

        Returns:
            效果详情和测量方法
        """
        for effect in self.kg_data.get("technical_effects", []):
            if effect_type in effect["effect_type"] or effect["effect_type"] in effect_type:
                return effect

        return None

    def query_argumentation_template(self, template_name: str) -> dict | None:
        """
        查询论证模板

        Args:
            template_name: 模板名称

        Returns:
            模板结构和变量
        """
        for template in self.kg_data.get("argumentation_templates", []):
            if template_name in template["template_name"] or template["template_name"] in template_name:
                return template

        return None

    def search_related_concepts(self, concept: str, limit: int = 5) -> list[str]:
        """
        搜索相关概念

        Args:
            concept: 概念名称
            limit: 返回数量限制

        Returns:
            相关概念列表
        """
        related = set()

        # 从术语定义中查找
        term_data = self.query_term_definition(concept)
        if term_data and "related_concepts" in term_data:
            related.update(term_data["related_concepts"])

        # 从其他术语中反向查找
        for term in self.kg_data.get("terms", []):
            if concept in term.get("related_concepts", []):
                related.add(term["term"])

        return list(related)[:limit]

    def get_context_for_prompt(
        self,
        rejection_type: str,
        claims: list[str],
        prior_art_analysis: dict
    ) -> dict[str, Any]:
        """
        为动态提示词生成获取上下文信息

        Args:
            rejection_type: 驳回类型
            claims: 权利要求列表
            prior_art_analysis: 对比文件分析结果

        Returns:
            上下文信息字典
        """
        context = {
            "legal_basis": self._get_legal_basis(rejection_type),
            "key_terms": self._extract_key_terms(claims),
            "response_strategies": self._suggest_strategies(claims, prior_art_analysis),
            "argumentation_templates": self._get_suitable_templates(rejection_type),
            "technical_knowledge": self._get_technical_knowledge(claims),
        }

        return context

    def _get_legal_basis(self, rejection_type: str) -> str:
        """获取法律依据"""
        if rejection_type == "inventiveness":
            return self.kg_data["legal_articles"][0]["content"]
        elif rejection_type == "novelty":
            return self.kg_data["legal_articles"][1]["content"]
        else:
            return "专利法相关规定"

    def _extract_key_terms(self, claims: list[str]) -> list[str]:
        """从权利要求中提取关键术语"""
        key_terms = []

        # 常见技术术语
        technical_keywords = [
            "协同", "组合", "优化", "改善", "提升", "增强", "去除", "净化",
            "参数", "温度", "浓度", "时间", "比例", "效果", "机理"
        ]

        claims_text = " ".join(claims)

        for keyword in technical_keywords:
            if keyword in claims_text:
                term_data = self.query_term_definition(keyword)
                if term_data:
                    key_terms.append(term_data)

        return key_terms[:5]  # 最多5个

    def _suggest_strategies(
        self,
        claims: list[str],
        prior_art_analysis: dict
    ) -> list[dict]:
        """建议答复策略"""
        strategies = []

        claims_text = " ".join(claims)

        # 检测适合的策略
        if "协同" in claims_text or "组合" in claims_text:
            strategies.append(self.kg_data["response_strategies"][0])

        if any(kw in claims_text for kw in ["温度", "浓度", "参数", "范围"]):
            strategies.append(self.kg_data["response_strategies"][1])

        if "效果" in claims_text or "改善" in claims_text:
            strategies.append(self.kg_data["response_strategies"][2])

        return strategies[:2]  # 最多2个策略

    def _get_suitable_templates(self, rejection_type: str) -> list[dict]:
        """获取合适的论证模板"""
        templates = []

        if rejection_type == "inventiveness":
            # 创造性驳回，使用协同效应或参数优化模板
            templates.extend(self.kg_data["argumentation_templates"][:2])

        return templates

    def _get_technical_knowledge(self, claims: list[str]) -> list[dict]:
        """获取技术知识"""
        knowledge = []

        claims_text = " ".join(claims)

        # 根据权利要求中的关键词获取相关知识
        for effect in self.kg_data["technical_effects"]:
            if effect["effect_type"] in claims_text:
                knowledge.append(effect)

        return knowledge[:3]  # 最多3个

    def enhance_prompt_with_kg(
        self,
        base_prompt: str,
        context: dict[str, Any]
    ) -> str:
        """
        使用知识图谱增强提示词

        Args:
            base_prompt: 基础提示词
            context: 上下文信息

        Returns:
            增强后的提示词
        """
        enhanced_parts = [base_prompt]

        # 添加法律依据
        if context.get("legal_basis"):
            enhanced_parts.append(f"\n\n## 法律依据\n{context['legal_basis']}")

        # 添加关键术语定义
        if context.get("key_terms"):
            enhanced_parts.append("\n\n## 关键术语定义")
            for term in context["key_terms"]:
                enhanced_parts.append(f"- **{term['term']}**: {term['definition']}")

        # 添加答复策略建议
        if context.get("response_strategies"):
            enhanced_parts.append("\n\n## 建议答复策略")
            for strategy in context["response_strategies"]:
                enhanced_parts.append(f"\n### {strategy['strategy']}")
                enhanced_parts.append(f"{strategy['description']}")
                enhanced_parts.append("**关键要点**:")
                for point in strategy["key_points"]:
                    enhanced_parts.append(f"- {point}")

        # 添加论证模板参考
        if context.get("argumentation_templates"):
            enhanced_parts.append("\n\n## 论证模板参考")
            for template in context["argumentation_templates"][:1]:  # 只显示第一个模板
                enhanced_parts.append(f"\n### {template['template_name']}")
                enhanced_parts.append(f"```{template['structure'][:200]}...```")

        # 添加技术知识
        if context.get("technical_knowledge"):
            enhanced_parts.append("\n\n## 相关技术知识")
            for knowledge in context["technical_knowledge"]:
                enhanced_parts.append(f"\n### {knowledge['effect_type']}")
                enhanced_parts.append(f"描述: {knowledge['description']}")
                if knowledge.get("typical_values"):
                    enhanced_parts.append(f"典型值: {knowledge['typical_values']}")

        return "\n".join(enhanced_parts)


# 便捷函数
_kg_query_instance: PatentKGQueryInterface | None = None


def get_patent_kg_query() -> PatentKGQueryInterface:
    """获取专利知识图谱查询接口单例"""
    global _kg_query_instance
    if _kg_query_instance is None:
        _kg_query_instance = PatentKGQueryInterface()
    return _kg_query_instance


# 测试代码
if __name__ == "__main__":
    # 测试知识图谱查询接口
    kg_query = get_patent_kg_query()

    print("=" * 70)
    print("🧪 测试专利知识图谱查询接口")
    print("=" * 70)

    # 测试1: 查询术语定义
    print("\n测试1: 查询术语定义")
    term_def = kg_query.query_term_definition("创造性")
    if term_def:
        print(f"术语: {term_def['term']}")
        print(f"定义: {term_def['definition']}")
        print(f"相关概念: {', '.join(term_def['related_concepts'])}")

    # 测试2: 查询法律条文
    print("\n测试2: 查询法律条文")
    article = kg_query.query_legal_article("专利法第22条第3款")
    if article:
        print(f"条款: {article['article']}")
        print(f"内容: {article['content']}")
        print(f"应用: {article['application']}")

    # 测试3: 查询答复策略
    print("\n测试3: 查询答复策略")
    strategy = kg_query.query_response_strategy("协同")
    if strategy:
        print(f"策略: {strategy['strategy']}")
        print(f"描述: {strategy['description']}")
        print("关键要点:")
        for point in strategy['key_points']:
            print(f"  - {point}")

    # 测试4: 获取提示词上下文
    print("\n测试4: 获取提示词上下文")
    context = kg_query.get_context_for_prompt(
        rejection_type="inventiveness",
        claims=["1. 一种方法，包括四要素协同处理。"],
        prior_art_analysis={}
    )
    print(f"法律依据: {context['legal_basis'][:50]}...")
    print(f"关键术语数: {len(context['key_terms'])}")
    print(f"建议策略数: {len(context['response_strategies'])}")

    # 测试5: 增强提示词
    print("\n测试5: 增强提示词")
    base_prompt = "# 请为以下专利生成答复意见"
    enhanced = kg_query.enhance_prompt_with_kg(base_prompt, context)
    print(f"基础提示词长度: {len(base_prompt)}")
    print(f"增强提示词长度: {len(enhanced)}")
    print(f"增强后前200字符: {enhanced[:200]}...")

    print("\n" + "=" * 70)
    print("✅ 所有测试完成")
    print("=" * 70)
