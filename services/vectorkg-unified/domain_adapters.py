#!/usr/bin/env python3
"""
领域适配器
Domain Adapters

为不同专业领域提供适配的智能服务接口

作者: 小诺·双鱼公主
创建时间: 2024年12月15日
"""

import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from core.async_main import async_main

logger = logging.getLogger(__name__)

class DomainType(Enum):
    """支持的领域类型"""
    PATENT = "patent"
    LEGAL = "legal"
    MEDICAL = "medical"
    FINANCIAL = "financial"
    TECHNICAL = "technical"
    EDUCATION = "education"
    GENERAL = "general"

class DomainAdapter(ABC):
    """领域适配器抽象基类"""

    def __init__(self, domain: DomainType, infrastructure):
        self.domain = domain
        self.infrastructure = infrastructure
        self.domain_config = self._get_domain_config()

    @abstractmethod
    def _get_domain_config(self) -> dict[str, Any]:
        """获取领域特定配置"""
        pass

    @abstractmethod
    async def process_query(self, query: str, context: dict) -> dict[str, Any]:
        """处理领域特定查询"""
        pass

    @abstractmethod
    def extract_domain_rules(self, text: str, rule_types: list[str]) -> dict[str, Any]:
        """提取领域规则"""
        pass

    def _get_relevant_collections(self) -> list[str]:
        """获取相关的向量集合"""
        return self.domain_config.get("vector_collections", [])

    def _get_relevant_knowledge_graphs(self) -> list[str]:
        """获取相关的知识图谱"""
        return self.domain_config.get("knowledge_graphs", [])

class PatentDomainAdapter(DomainAdapter):
    """专利领域适配器"""

    def __init__(self, infrastructure):
        super().__init__(DomainType.PATENT, infrastructure)

    def _get_domain_config(self) -> dict[str, Any]:
        return {
            "vector_collections": [
                "patent_legal_vectors_1024",
                "patent_guideline",
                "technical_patents_1024",
                "innovation_vectors_1024"
            ],
            "knowledge_graphs": [
                "patent_sqlite_kg",
                "patent_legal_kg",
                "technical_kg"
            ],
            "intent_keywords": {
                "novelty": ["新颖性", "现有技术", "申请日", "公开", "抵触申请"],
                "creativity": ["创造性", "进步性", "非显而易见", "技术启示"],
                "practicality": ["实用性", "可实施性", "技术方案"],
                "infringement": ["侵权", "保护范围", "权利要求", "等同"],
                "filing": ["申请", "撰写", "提交", "流程"]
            }
        }

    async def process_query(self, query: str, context: dict) -> dict[str, Any]:
        """处理专利领域查询"""
        # 意图识别
        intent = self._classify_intent(query)

        # 执行混合搜索
        search_results = await self.infrastructure.hybrid_search(
            query_text=query,
            collections=self._get_relevant_collections(),
            max_vector_results=10,
            max_graph_paths=5
        )

        # 生成专利特定响应
        response = self._generate_patent_response(
            query=query,
            intent=intent,
            search_results=search_results,
            context=context
        )

        return response

    def extract_domain_rules(self, text: str, rule_types: list[str]) -> dict[str, Any]:
        """提取专利规则"""
        extracted_rules = {}

        for rule_type in rule_types:
            keywords = self.domain_config["intent_keywords"].get(rule_type, [])
            if keywords:
                # 使用关键词从知识图谱提取相关规则
                rules = self._extract_rules_by_keywords(text, keywords, rule_type)
                extracted_rules[rule_type] = rules

        return {
            "domain": "patent",
            "rule_types": rule_types,
            "extracted_rules": extracted_rules,
            "total_rules": sum(len(rules) for rules in extracted_rules.values())
        }

    def _classify_intent(self, query: str) -> str:
        """分类查询意图"""
        query_lower = query.lower()

        for intent, keywords in self.domain_config["intent_keywords"].items():
            if any(keyword in query_lower for keyword in keywords):
                return intent

        return "general"

    def _generate_patent_response(self, query: str, intent: str,
                                 search_results: dict, context: dict) -> dict[str, Any]:
        """生成专利特定响应"""
        return {
            "domain": "patent",
            "intent": intent,
            "query": query,
            "prompts": {
                "system_role": f"你是一位专业的专利{self._get_role_by_intent(intent)}",
                "task_description": f"请根据查询'{query}'提供专业的专利分析",
                "knowledge_guidance": self._extract_knowledge_guidance(search_results),
                "assessment_framework": self._get_assessment_framework(intent),
                "output_format": self._get_output_format(intent)
            },
            "search_results": search_results,
            "suggested_actions": self._get_suggested_actions(intent),
            "confidence": self._calculate_confidence(search_results),
            "metadata": {
                "domain": "patent",
                "intent": intent,
                "timestamp": search_results.get("timestamp")
            }
        }

    def _get_role_by_intent(self, intent: str) -> str:
        """根据意图获取角色"""
        role_map = {
            "novelty": "审查员",
            "creativity": "技术专家",
            "practicality": "实施顾问",
            "infringement": "法律顾问",
            "filing": "申请代理人"
        }
        return role_map.get(intent, "顾问")

    def _extract_knowledge_guidance(self, search_results: dict) -> str:
        """提取知识指导"""
        guidance_parts = []

        # 从向量结果提取
        for result in search_results.get("vector_results", [])[:3]:
            content = result.get("content", "")
            if content:
                guidance_parts.append(f"- {content[:100]}...")

        # 从图谱结果提取
        for result in search_results.get("graph_results", [])[:3]:
            node_name = result["node"].get("name", "")
            node_desc = result["node"].get("description", "")
            if node_name:
                guidance_parts.append(f"- {node_name}: {node_desc[:80]}...")

        return "\n".join(guidance_parts) if guidance_parts else "暂无相关指导"

    def _get_assessment_framework(self, intent: str) -> str:
        """获取评估框架"""
        frameworks = {
            "novelty": "1. 查询现有技术数据库\n2. 对比技术特征\n3. 判断是否构成抵触申请\n4. 评估新颖性",
            "creativity": "1. 确定最接近的现有技术\n2. 识别区别技术特征\n3. 判断是否显而易见\n4. 评估技术进步",
            "practicality": "1. 分析技术方案可行性\n2. 评估实施成本\n3. 考虑产业化前景\n4. 判断实用性",
            "infringement": "1. 解释权利要求保护范围\n2. 对比被控侵权技术\n3. 应用等同原则\n4. 评估侵权风险",
            "filing": "1. 准备申请文件\n2. 确定申请策略\n3. 撰写技术方案\n4. 提交申请材料"
        }
        return frameworks.get(intent, "提供专业的分析和建议")

    def _get_output_format(self, intent: str) -> str:
        """获取输出格式"""
        formats = {
            "novelty": "## 新颖性分析\n### 技术特征对比\n### 现有技术检索\n### 结论",
            "creativity": "## 创造性评估\n### 技术进步性\n### 非显而易见性\n### 结论",
            "practicality": "## 实用性评估\n### 技术可行性\n### 实施可能性\n### 结论",
            "infringement": "## 侵权分析\n### 权利要求解释\n### 侵权判定\n### 风险评估",
            "filing": "## 申请指导\n### 申请策略\n### 文件准备\n### 流程说明"
        }
        return formats.get(intent, "## 分析报告\n### 要点分析\n### 结论建议")

    def _get_suggested_actions(self, intent: str) -> list[dict[str, str]]:
        """获取建议操作"""
        actions = {
            "novelty": [
                {"action": "search_prior_art", "label": "检索现有技术"},
                {"action": "compare_features", "label": "对比技术特征"},
                {"action": "generate_report", "label": "生成新颖性报告"}
            ],
            "creativity": [
                {"action": "technical_analysis", "label": "技术进步分析"},
                {"action": "obviousness_check", "label": "显而易见性检查"},
                {"action": "creativity_report", "label": "生成创造性报告"}
            ],
            "filing": [
                {"action": "prepare_documents", "label": "准备申请文件"},
                {"action": "filing_strategy", "label": "制定申请策略"},
                {"action": "submit_application", "label": "提交申请"}
            ]
        }
        return actions.get(intent, [])

    def _calculate_confidence(self, search_results: dict) -> float:
        """计算置信度"""
        vector_count = len(search_results.get("vector_results", []))
        graph_count = len(search_results.get("graph_results", []))

        # 基于结果数量和质量计算置信度
        confidence = min(1.0, (vector_count * 0.6 + graph_count * 0.4) / 10)

        return round(confidence, 2)

    def _extract_rules_by_keywords(self, text: str, keywords: list[str],
                                  rule_type: str) -> list[dict[str, Any]]:
        """根据关键词提取规则"""
        # 这里应该调用知识图谱进行规则提取
        # 简化实现，返回模拟规则
        return [
            {
                "rule_id": f"{rule_type}_001",
                "title": f"{rule_type.title()}规则示例",
                "content": f"基于关键词{keywords}提取的{rule_type}相关规则",
                "source": "patent_knowledge_graph",
                "confidence": 0.85
            }
        ]

# 其他领域适配器（可扩展）
class LegalDomainAdapter(DomainAdapter):
    """法律领域适配器"""

    def __init__(self, infrastructure):
        super().__init__(DomainType.LEGAL, infrastructure)

    def _get_domain_config(self) -> dict[str, Any]:
        return {
            "vector_collections": [
                "patent_legal_vectors_1024",
                "legal_case_vectors",
                "legal_statute_vectors"
            ],
            "knowledge_graphs": [
                "patent_legal_kg",
                "legal_case_kg",
                "legal_statute_kg"
            ],
            "intent_keywords": {
                "contract": ["合同", "协议", "条款", "违约"],
                "tort": ["侵权", "损害", "责任", "赔偿"],
                "litigation": ["诉讼", "起诉", "答辩", "证据"],
                "compliance": ["合规", "监管", "义务", "违规"]
            }
        }

    async def process_query(self, query: str, context: dict) -> dict[str, Any]:
        """处理法律领域查询"""
        # 类似专利领域的实现
        return {
            "domain": "legal",
            "query": query,
            "response": "法律领域查询处理中..."
        }

    def extract_domain_rules(self, text: str, rule_types: list[str]) -> dict[str, Any]:
        """提取法律规则"""
        return {
            "domain": "legal",
            "message": "法律规则提取功能开发中"
        }

class MedicalDomainAdapter(DomainAdapter):
    """医疗领域适配器"""

    def __init__(self, infrastructure):
        super().__init__(DomainType.MEDICAL, infrastructure)

    def _get_domain_config(self) -> dict[str, Any]:
        return {
            "vector_collections": [
                "medical_literature_vectors",
                "clinical_guideline_vectors",
                "drug_database_vectors"
            ],
            "knowledge_graphs": [
                "medical_knowledge_kg",
                "drug_interaction_kg",
                "disease_kg"
            ],
            "intent_keywords": {
                "diagnosis": ["诊断", "症状", "检查", "鉴别"],
                "treatment": ["治疗", "药物", "手术", "方案"],
                "prevention": ["预防", "筛查", "疫苗", "保健"]
            }
        }

    async def process_query(self, query: str, context: dict) -> dict[str, Any]:
        """处理医疗领域查询"""
        return {
            "domain": "medical",
            "query": query,
            "response": "医疗领域查询处理中..."
        }

    def extract_domain_rules(self, text: str, rule_types: list[str]) -> dict[str, Any]:
        """提取医疗规则"""
        return {
            "domain": "medical",
            "message": "医疗规则提取功能开发中"
        }

class DomainAdapterFactory:
    """领域适配器工厂"""

    @staticmethod
    def create_adapter(domain: DomainType, infrastructure) -> DomainAdapter:
        """创建领域适配器"""
        adapters = {
            DomainType.PATENT: PatentDomainAdapter,
            DomainType.LEGAL: LegalDomainAdapter,
            DomainType.MEDICAL: MedicalDomainAdapter
        }

        adapter_class = adapters.get(domain, PatentDomainAdapter)
        return adapter_class(infrastructure)

    @staticmethod
    def get_supported_domains() -> list[DomainType]:
        """获取支持的领域列表"""
        return [DomainType.PATENT, DomainType.LEGAL, DomainType.MEDICAL]

# 使用示例
@async_main
async def main():
    """使用示例"""
    from vector_knowledge_infrastructure import get_vector_knowledge_infrastructure

    # 获取基础设施
    infra = await get_vector_knowledge_infrastructure()

    # 创建专利领域适配器
    patent_adapter = DomainAdapterFactory.create_adapter(
        DomainType.PATENT,
        infra
    )

    # 处理查询
    response = await patent_adapter.process_query(
        query="这个专利具有新颖性吗？",
        context={"patent_text": "本发明涉及一种新的技术方案..."}
    )

    print("=== 专利领域查询结果 ===")
    print(f"领域: {response['domain']}")
    print(f"意图: {response['intent']}")
    print(f"置信度: {response['confidence']}")

    # 提取规则
    rules = patent_adapter.extract_domain_rules(
        text="专利技术方案描述...",
        rule_types=["novelty", "creativity"]
    )

    print("\n=== 提取的规则 ===")
    print(f"总规则数: {rules['total_rules']}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
