#!/usr/bin/env python3
"""
增强版动态提示词生成器
Enhanced Dynamic Prompt Generator

集成专利规则向量库 + AI术语知识图谱,为专利检索和分析提供全方位支持
"""
from __future__ import annotations
import json
import logging
import os
from dataclasses import dataclass
from typing import Any

import numpy as np
import requests
from sentence_transformers import SentenceTransformer
from services.sqlite_patent_knowledge_service import get_sqlite_patent_knowledge_service

from core.knowledge.graph_manager import KnowledgeGraphManager
from core.logging_config import setup_logging
from core.storage.vector_manager import VectorManager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


@dataclass
class PatentContext:
    """专利业务上下文"""

    business_type: str  # 业务类型:申请、审查、无效、诉讼等
    technology_field: str  # 技术领域
    keywords: list[str]  # 关键词
    user_query: str  # 用户查询
    urgency_level: str  # 紧急程度:低、中、高
    complexity_level: str  # 复杂程度:简单、中等、复杂


@dataclass
class TechnicalTermsContext:
    """技术术语上下文"""

    identified_terms: list[dict]  # 识别到的技术术语
    domain_distribution: dict[str, int]  # 领域分布
    complexity_distribution: dict[str, int]  # 复杂度分布
    related_terms: list[dict]  # 相关术语
    applications: list[str]  # 应用场景


@dataclass
class EnhancedDynamicPrompt:
    """增强版动态生成的提示词"""

    system_prompt: str  # 系统级提示
    context_prompt: str  # 上下文提示
    patent_rules_prompt: str  # 专利规则提示
    technical_terms_prompt: str  # 技术术语提示
    knowledge_prompt: str  # 知识图谱提示
    sqlite_knowledge_prompt: str  # SQLite知识图谱提示
    action_prompt: str  # 行动提示
    search_strategy_prompt: str  # 检索策略提示
    confidence_score: float  # 置信度分数
    sources: list[dict]  # 数据来源


class EnhancedDynamicPromptGenerator:
    """增强版动态提示词生成器"""

    def __init__(self):
        """初始化增强版动态提示词生成器"""
        self.vector_manager = VectorManager()
        self.graph_manager = KnowledgeGraphManager()
        self.encoder = SentenceTransformer("shibing624/text2vec-base-chinese")

        # SQLite专利知识图谱服务
        self.sqlite_kg_service = get_sqlite_patent_knowledge_service()

        # API服务端点
        self.api_base = "http://localhost:8080"

        # 业务类型映射
        self.business_type_mapping = {
            "专利申请": ["申请", "提交", "文件准备", "审查", "授权"],
            "专利审查": ["审查", "检索", "新颖性", "创造性", "实用性"],
            "专利无效": ["无效", "宣告无效", "证据", "现有技术", "公开充分"],
            "专利诉讼": ["诉讼", "侵权", "证据", "赔偿", "禁令"],
            "专利转让": ["转让", "许可", "合同", "备案", "登记"],
            "专利维护": ["年费", "维护", "期限", "续展", "恢复"],
        }

        # 技术领域映射(扩展AI领域)
        self.technology_field_mapping = {
            "人工智能": ["AI", "人工智能", "机器学习", "深度学习", "神经网络", "算法"],
            "电子信息": ["电子", "信息", "通信", "芯片", "半导体", "集成电路"],
            "生物医药": ["生物", "医药", "基因", "蛋白质", "药物", "医疗"],
            "机械制造": ["机械", "制造", "设备", "装置", "零件", "材料"],
            "化学材料": ["化学", "材料", "化合物", "组合物", "合成", "催化"],
            "新能源": ["能源", "电池", "太阳能", "风能", "储能", "环保"],
        }

        # 加载AI术语数据
        self.ai_terminology_data = self.load_ai_terminology()

        # 紧急程度权重
        self.urgency_weights = {"低": 0.3, "中": 0.6, "高": 1.0}

        logger.info("增强版动态提示词生成器初始化完成")

    def load_ai_terminology(self) -> dict[str, Any]:
        """加载AI术语数据"""
        try:
            # 查找最新的AI术语文件
            data_dir = "/Users/xujian/Athena工作平台/data"
            ai_files = [f for f in os.listdir(data_dir) if f.startswith("ai_terminology_enhanced_")]

            if not ai_files:
                logger.warning("未找到AI术语数据文件")
                return {}

            # 选择最新文件
            latest_file = sorted(ai_files)[-1]
            file_path = os.path.join(data_dir, latest_file)

            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)

            logger.info(f"成功加载AI术语数据: {len(data.get('ai_terms', []))} 个术语")
            return data

        except Exception as e:
            logger.error(f"加载AI术语数据失败: {e}")
            return {}

    def extract_technical_terms(self, text: str) -> TechnicalTermsContext:
        """提取技术术语"""
        identified_terms = []
        domain_distribution = {}
        complexity_distribution = {}
        related_terms = []
        applications = set()

        ai_terms = self.ai_terminology_data.get("ai_terms", [])
        text_lower = text.lower()

        # 识别AI术语
        for term_data in ai_terms:
            english_term = term_data["english_term"].lower()
            chinese_term = term_data["chinese_translation"]
            abbreviation = term_data.get("abbreviation", "").lower()

            # 检查是否匹配
            if (
                english_term in text_lower
                or chinese_term in text
                or (abbreviation and abbreviation in text_lower)
            ):

                identified_terms.append(
                    {
                        "term_id": term_data["term_id"],
                        "english_term": term_data["english_term"],
                        "chinese_translation": term_data["chinese_translation"],
                        "domain": term_data["domain"],
                        "complexity": term_data["complexity"],
                        "applications": term_data["applications"],
                    }
                )

                # 统计领域分布
                domain = term_data["domain"]
                domain_distribution[domain] = domain_distribution.get(domain, 0) + 1

                # 统计复杂度分布
                complexity = term_data["complexity"]
                complexity_distribution[complexity] = complexity_distribution.get(complexity, 0) + 1

                # 收集应用场景
                applications.update(term_data["applications"])

                # 收集相关术语
                for related in term_data.get("related_terms", [])[:3]:  # 限制数量
                    related_terms.append(
                        {
                            "english_term": related["english_term"],
                            "chinese_translation": related["chinese_translation"],
                            "relation_type": related["relation_type"],
                        }
                    )

        return TechnicalTermsContext(
            identified_terms=identified_terms,
            domain_distribution=domain_distribution,
            complexity_distribution=complexity_distribution,
            related_terms=related_terms[:10],  # 限制相关术语数量
            applications=list(applications)[:8],  # 限制应用场景数量
        )

    def parse_business_context(self, user_input: str) -> PatentContext:
        """解析业务上下文"""
        user_input_lower = user_input.lower()

        # 识别业务类型
        business_type = "通用咨询"
        for btype, keywords in self.business_type_mapping.items():
            if any(kw in user_input_lower for kw in keywords):
                business_type = btype
                break

        # 识别技术领域(增强版,包含AI领域)
        technology_field = "通用"
        for field, keywords in self.technology_field_mapping.items():
            if any(kw in user_input_lower for kw in keywords):
                technology_field = field
                break

        # 提取关键词
        keywords = []
        if "发明" in user_input:
            keywords.append("发明专利")
        if "实用新型" in user_input:
            keywords.append("实用新型专利")
        if "外观设计" in user_input:
            keywords.append("外观设计专利")

        # 从识别的技术术语中提取关键词
        tech_context = self.extract_technical_terms(user_input)
        for term in tech_context.identified_terms:
            keywords.append(term["chinese_translation"])
            if term["abbreviation"]:
                keywords.append(term["abbreviation"])

        # 判断紧急程度
        urgency_level = "中"
        if any(word in user_input_lower for word in ["紧急", "加急", "尽快"]):
            urgency_level = "高"
        elif any(word in user_input_lower for word in ["不急", "一般", "了解"]):
            urgency_level = "低"

        # 判断复杂程度
        complexity_level = "中等"
        tech_term_count = len(tech_context.identified_terms)
        if tech_term_count == 0:
            complexity_level = "简单"
        elif tech_term_count >= 5:
            complexity_level = "复杂"
        elif tech_term_count >= 2:
            complexity_level = "中等"

        return PatentContext(
            business_type=business_type,
            technology_field=technology_field,
            keywords=list(set(keywords)),  # 去重
            user_query=user_input,
            urgency_level=urgency_level,
            complexity_level=complexity_level,
        )

    async def search_patent_rules(self, context: PatentContext) -> list[dict]:
        """搜索相关专利规则"""
        try:
            # 构建搜索查询
            query = (
                f"{context.business_type} {context.technology_field} {' '.join(context.keywords)}"
            )

            # 调用向量搜索API
            async with requests.Session() as session, session.post(
                f"{self.api_base}/vector/search",
                json={"collection_name": "patent_rules_1024", "query_text": query, "limit": 10},
            ) as response:
                if response.status_code == 200:
                    results = await response.json()
                    return results.get("results", [])
        except Exception as e:
            logger.error(f"搜索专利规则失败: {e}")

        return []

    async def search_ai_terminology_vectors(self, context: PatentContext) -> list[dict]:
        """搜索AI术语向量"""
        try:
            # 构建搜索查询
            query = f"{context.technology_field} {' '.join(context.keywords)}"

            # 调用向量搜索API - 假设AI术语向量集合名称
            async with requests.Session() as session, session.post(
                f"{self.api_base}/vector/search",
                json={
                    "collection_name": "ai_terminology_vectors",
                    "query_text": query,
                    "limit": 15,
                },
            ) as response:
                if response.status_code == 200:
                    results = await response.json()
                    return results.get("results", [])
        except Exception as e:
            logger.error(f"搜索AI术语向量失败: {e}")

        return []

    def search_sqlite_knowledge_graph(self, context: PatentContext) -> dict[str, Any]:
        """搜索SQLite专利知识图谱"""
        try:
            # 构建搜索查询
            query_parts = [context.business_type, context.technology_field]
            query_parts.extend(context.keywords)
            query = " ".join(filter(None, query_parts))

            logger.info(f"🔍 搜索SQLite知识图谱: {query}")

            # 调用SQLite知识图谱服务
            knowledge = self.sqlite_kg_service.get_related_knowledge(
                query=query, max_entities=15, max_relations=30
            )

            logger.info(
                f"✅ SQLite知识图谱搜索完成: {knowledge.get('total_entities', 0)}个实体, {knowledge.get('total_relations', 0)}个关系"
            )

            return {
                "entities": knowledge.get("entities", []),
                "relations": knowledge.get("relations", []),
                "total_entities": knowledge.get("total_entities", 0),
                "total_relations": knowledge.get("total_relations", 0),
                "source": "sqlite_patent_kg",
            }

        except Exception as e:
            logger.error(f"搜索SQLite知识图谱失败: {e}")
            return {
                "entities": [],
                "relations": [],
                "total_entities": 0,
                "total_relations": 0,
                "source": "sqlite_patent_kg",
                "error": str(e),
            }

    def generate_patent_rules_prompt(self, rules: list[dict], context: PatentContext) -> str:
        """生成专利规则提示词"""
        if not rules:
            return ""

        prompt = "[专利规则参考]\n"
        prompt += f"基于您的{context.business_type}需求,以下相关专利规则需要特别注意:\n\n"

        for i, rule in enumerate(rules[:5], 1):  # 限制规则数量
            rule_text = rule.get("metadata", {}).get("text", "")
            score = rule.get("score", 0)

            if rule_text:
                prompt += f"{i}. {rule_text[:200]}... (相关度: {score:.2f})\n\n"

        return prompt

    def generate_technical_terms_prompt(
        self, tech_context: TechnicalTermsContext, context: PatentContext
    ) -> str:
        """生成技术术语提示词"""
        if not tech_context.identified_terms:
            return ""

        prompt = "[技术术语解析]\n"
        prompt += f"识别到 {len(tech_context.identified_terms)} 个相关技术术语:\n\n"

        # 按领域组织术语
        domain_groups = {}
        for term in tech_context.identified_terms:
            domain = term["domain"]
            if domain not in domain_groups:
                domain_groups[domain] = []
            domain_groups[domain].append(term)

        for domain, terms in domain_groups.items():
            prompt += f"**{domain}领域**:\n"
            for term in terms[:3]:  # 每个领域最多显示3个术语
                prompt += f"- {term['english_term']} ({term['chinese_translation']}) - {term['complexity']}\n"
            prompt += "\n"

        # 添加相关术语
        if tech_context.related_terms:
            prompt += "**相关技术术语**:\n"
            for term in tech_context.related_terms[:5]:
                prompt += f"- {term['english_term']} ({term['chinese_translation']}) - {term['relation_type']}\n"
            prompt += "\n"

        # 添加应用场景
        if tech_context.applications:
            prompt += "**技术可能的应用场景**:\n"
            for app in tech_context.applications:
                prompt += f"- {app}\n"
            prompt += "\n"

        return prompt

    def generate_knowledge_graph_prompt(
        self, context: PatentContext, tech_context: TechnicalTermsContext
    ) -> str:
        """生成知识图谱提示词"""
        prompt = "[知识图谱洞察]\n"

        # 技术领域分析
        if tech_context.domain_distribution:
            prompt += "**技术领域分布**:\n"
            for domain, count in sorted(
                tech_context.domain_distribution.items(), key=lambda x: x[1], reverse=True
            ):
                prompt += f"- {domain}: {count} 个术语\n"
            prompt += "\n"

        # 复杂度分析
        if tech_context.complexity_distribution:
            prompt += "**技术复杂度分析**:\n"
            for complexity, count in tech_context.complexity_distribution.items():
                prompt += f"- {complexity}: {count} 个术语\n"
            prompt += "\n"

        # 业务建议
        prompt += "**业务处理建议**:\n"
        if context.complexity_level == "复杂":
            prompt += "- 技术复杂度较高,建议进行深入的技术背景调查\n"
            prompt += "- 需要重点关注技术实现细节和创新点\n"
        elif context.complexity_level == "简单":
            prompt += "- 技术相对成熟,可重点关注商业应用和法律层面\n"
        else:
            prompt += "- 需要平衡技术和商业层面的考虑\n"

        prompt += f"- 基于{context.business_type}类型,建议重点关注相关领域的专利布局\n"

        return prompt

    def generate_search_strategy_prompt(
        self, context: PatentContext, tech_context: TechnicalTermsContext
    ) -> str:
        """生成检索策略提示词"""
        prompt = "[智能检索策略]\n"

        # 基于识别的技术术语生成检索词
        if tech_context.identified_terms:
            prompt += "**推荐检索关键词**:\n"

            # 英文检索词
            english_terms = [term["english_term"] for term in tech_context.identified_terms[:8]]
            prompt += f"- 英文: {' OR '.join(english_terms)}\n"

            # 中文检索词
            chinese_terms = [
                term["chinese_translation"] for term in tech_context.identified_terms[:8]
            ]
            prompt += f"- 中文: {' OR '.join(chinese_terms)}\n"

            # 缩写词
            abbreviations = [
                term["abbreviation"]
                for term in tech_context.identified_terms
                if term["abbreviation"]
            ]
            if abbreviations:
                prompt += f"- 缩写: {' OR '.join(abbreviations)}\n"

            prompt += "\n"

        # 分类号建议
        prompt += "**技术分类号建议**:\n"
        domain_ipc_mapping = {
            "机器学习": "G06N 20/00",
            "深度学习": "G06N 3/04",
            "自然语言处理": "G06F 40/00",
            "计算机视觉": "G06V 10/00",
            "强化学习": "G06N 20/00",
        }

        for domain in tech_context.domain_distribution:
            if domain in domain_ipc_mapping:
                prompt += f"- {domain}: {domain_ipc_mapping[domain]}\n"

        prompt += "\n"

        # 检索策略
        prompt += "**检索策略建议**:\n"
        if context.business_type == "专利审查":
            prompt += "- 建议进行技术对比分析,关注现有技术布局\n"
            prompt += "- 重点检索同领域主要竞争对手的专利\n"
        elif context.business_type == "专利申请":
            prompt += "- 建议进行全面的现有技术检索\n"
            prompt += "- 关注相关技术的专利保护范围\n"
        elif context.business_type == "专利无效":
            prompt += "- 建议检索在先公开的技术文献\n"
            prompt += "- 关注技术原理的现有实现方式\n"

        return prompt

    async def generate_enhanced_dynamic_prompt(self, user_input: str) -> EnhancedDynamicPrompt:
        """生成增强版动态提示词"""
        logger.info(f"开始生成增强版动态提示词: {user_input[:50]}...")

        # 1. 解析业务上下文
        patent_context = self.parse_business_context(user_input)

        # 2. 提取技术术语
        tech_context = self.extract_technical_terms(user_input)

        # 3. 搜索相关专利规则
        patent_rules = await self.search_patent_rules(patent_context)

        # 4. 搜索AI术语向量(如果需要)
        ai_vectors = []
        if patent_context.technology_field == "人工智能" or tech_context.identified_terms:
            ai_vectors = await self.search_ai_terminology_vectors(patent_context)

        # 5. 搜索SQLite专利知识图谱
        sqlite_knowledge = self.search_sqlite_knowledge_graph(patent_context)

        # 6. 生成各部分提示词
        system_prompt = self.generate_system_prompt(patent_context)
        context_prompt = self.generate_context_prompt(patent_context, tech_context)
        patent_rules_prompt = self.generate_patent_rules_prompt(patent_rules, patent_context)
        technical_terms_prompt = self.generate_technical_terms_prompt(tech_context, patent_context)
        knowledge_prompt = self.generate_knowledge_graph_prompt(patent_context, tech_context)
        sqlite_knowledge_prompt = self.generate_sqlite_knowledge_prompt(sqlite_knowledge)
        action_prompt = self.generate_action_prompt(patent_context)
        search_strategy_prompt = self.generate_search_strategy_prompt(patent_context, tech_context)

        # 6. 计算置信度
        confidence_score = self.calculate_confidence_score(
            patent_rules, tech_context, ai_vectors, patent_context
        )

        # 7. 收集数据来源
        sources = []
        if patent_rules:
            sources.append({"type": "patent_rules", "count": len(patent_rules)})
        if tech_context.identified_terms:
            sources.append({"type": "ai_terminology", "count": len(tech_context.identified_terms)})
        if ai_vectors:
            sources.append({"type": "ai_vectors", "count": len(ai_vectors)})
        if sqlite_knowledge.get("total_entities", 0) > 0:
            sources.append(
                {
                    "type": "sqlite_knowledge_graph",
                    "count": sqlite_knowledge.get("total_entities", 0),
                }
            )

        return EnhancedDynamicPrompt(
            system_prompt=system_prompt,
            context_prompt=context_prompt,
            patent_rules_prompt=patent_rules_prompt,
            technical_terms_prompt=technical_terms_prompt,
            knowledge_prompt=knowledge_prompt,
            sqlite_knowledge_prompt=sqlite_knowledge_prompt,
            action_prompt=action_prompt,
            search_strategy_prompt=search_strategy_prompt,
            confidence_score=confidence_score,
            sources=sources,
        )

    def generate_system_prompt(self, context: PatentContext) -> str:
        """生成系统级提示词"""
        prompt = """你是Athena智能专利助手,具备以下核心能力:
1. 专利法律专业知识 - 基于专利规则向量库
2. 技术术语理解能力 - 基于2442个AI术语知识图谱
3. 智能检索分析能力 - 多维度专利分析
4. 动态知识整合能力 - 实时提取相关规则和术语

在处理专利业务时,始终:
- 准确识别技术术语和创新点
- 结合专利规则提供专业建议
- 给出具体的检索和分析策略
- 确保建议的准确性和可操作性"""
        return prompt

    def generate_context_prompt(
        self, context: PatentContext, tech_context: TechnicalTermsContext
    ) -> str:
        """生成上下文提示词"""
        prompt = f"""[业务上下文]
- 业务类型: {context.business_type}
- 技术领域: {context.technology_field}
- 复杂程度: {context.complexity_level}
- 紧急程度: {context.urgency_level}

[技术背景]
- 识别技术术语: {len(tech_context.identified_terms)} 个
- 涉及技术领域: {len(tech_context.domain_distribution)} 个
"""
        return prompt

    def generate_sqlite_knowledge_prompt(self, sqlite_knowledge: dict[str, Any]) -> str:
        """生成SQLite知识图谱提示词"""
        if not sqlite_knowledge.get("entities") and not sqlite_knowledge.get("relations"):
            return ""

        prompt = "[SQLite专利知识图谱洞察]\n"
        prompt += "从专利知识图谱(125万+实体, 328万+关系)中检索到以下相关信息:\n\n"

        # 实体信息
        entities = sqlite_knowledge.get("entities", [])
        if entities:
            prompt += f"**相关实体** ({len(entities)}个):\n"
            for entity in entities[:8]:  # 限制显示数量
                entity_name = entity.get("name", "未知实体")
                entity_type = entity.get("entity_type", "未知类型")
                confidence = entity.get("confidence", 0)
                prompt += f"- {entity_name} ({entity_type}) - 置信度: {confidence:.2f}\n"
            prompt += "\n"

        # 关系信息
        relations = sqlite_knowledge.get("relations", [])
        if relations:
            prompt += f"**实体关系** ({len(relations)}个):\n"
            for relation in relations[:10]:  # 限制显示数量
                source_name = relation.get("source_name", "未知源")
                target_name = relation.get("target_name", "未知目标")
                relation_type = relation.get("relation_type", "未知关系")
                confidence = relation.get("confidence", 0)
                prompt += f"- {source_name} --[{relation_type}]--> {target_name} (置信度: {confidence:.2f})\n"
            prompt += "\n"

        # 数据来源说明
        prompt += "**数据来源**: SQLite专利知识图谱 (1,255,147个实体, 3,285,109个关系)\n"
        prompt += "**覆盖范围**: 专利实体、关系网络、技术领域等多维度专利知识\n"
        prompt += "**应用价值**: 为专利分析提供全面的关系网络和实体知识支撑\n\n"

        return prompt

    def generate_action_prompt(self, context: PatentContext) -> str:
        """生成行动提示词"""
        actions = {
            "专利申请": "建议进行现有技术检索,分析技术创新点,准备申请文件",
            "专利审查": "建议进行技术对比分析,评估新颖性、创造性、实用性",
            "专利无效": "建议收集现有技术证据,分析专利的有效性",
            "专利诉讼": "建议分析侵权行为,收集证据材料",
            "专利转让": "建议评估专利价值,准备转让合同",
            "专利维护": "建议关注年费缴纳期限,评估专利维护价值",
        }

        return f"[行动建议]\n{actions.get(context.business_type, '建议根据具体需求制定相应策略')}"

    def calculate_confidence_score(
        self,
        patent_rules: list,
        tech_context: TechnicalTermsContext,
        ai_vectors: list,
        context: PatentContext,
    ) -> float:
        """计算置信度分数"""
        score = 0.0

        # 专利规则贡献 (30%)
        if patent_rules:
            rule_scores = [rule.get("score", 0) for rule in patent_rules]
            score += np.mean(rule_scores) * 0.3

        # 技术术语匹配贡献 (40%)
        if tech_context.identified_terms:
            term_count = len(tech_context.identified_terms)
            term_score = min(term_count / 5.0, 1.0)  # 5个术语以上得满分
            score += term_score * 0.4

        # 向量相似度贡献 (20%)
        if ai_vectors:
            vector_scores = [v.get("score", 0) for v in ai_vectors]
            score += np.mean(vector_scores) * 0.2

        # 业务类型匹配贡献 (10%)
        if context.business_type != "通用咨询":
            score += 0.1

        return min(score, 1.0)


# 使用示例
async def main():
    """测试增强版动态提示词生成器"""
    generator = EnhancedDynamicPromptGenerator()

    # 测试用例
    test_queries = [
        "我想申请一个关于机器学习算法的专利",
        "这个深度学习神经网络的发明如何进行专利审查?",
        "人工智能技术在图像识别领域的专利布局分析",
        "基于强化学习的自动驾驶系统专利无效宣告",
    ]

    for query in test_queries:
        logger.info(f"\n{'='*60}")
        logger.info(f"用户查询: {query}")
        logger.info(str("=" * 60))

        prompt = await generator.generate_enhanced_dynamic_prompt(query)

        logger.info(f"\n置信度: {prompt.confidence_score:.2f}")
        logger.info(f"数据来源: {prompt.sources}")

        if prompt.technical_terms_prompt:
            logger.info(str("\n" + prompt.technical_terms_prompt))

        if prompt.search_strategy_prompt:
            logger.info(str("\n" + prompt.search_strategy_prompt))


# 入口点: @async_main装饰器已添加到main函数
