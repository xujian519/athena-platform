#!/usr/bin/env python3
"""
动态提示词生成器
为小诺提供法律专业的动态提示词和规则依据
作者: 小诺·双鱼座
"""

import logging
from datetime import datetime

from legal_kg_support import LegalKnowledgeGraphSupport

logger = logging.getLogger(__name__)

class LegalPromptGenerator:
    """法律提示词生成器"""

    def __init__(self, kg_support: LegalKnowledgeGraphSupport):
        """初始化提示词生成器"""
        self.kg_support = kg_support
        self.prompt_templates = self._load_prompt_templates()
        self.rule_cache = {}

    def _load_prompt_templates(self) -> dict:
        """加载提示词模板"""
        return {
            "法律咨询": {
                "base_template": """你是小诺，专业的法律AI助手，拥有深厚的法律知识和实践经验。

当前咨询：{query}

相关法律依据：
{legal_basis}

专业提示：
1. 准确引用法条，注意法律效力层级
2. 考虑特殊情况下的适用性
3. 提供可操作的建议
4. 提醒潜在的法律风险

回答要求：
- 专业准确，使用规范的法律术语
- 条理清晰，逻辑严密
- 通俗易懂，避免过度使用法言法语
- 实事求是，不夸大或遗漏重要信息

请基于上述信息回答：
""",
                "keywords": ["如何", "怎样", "是否合法", "可以", "应该", "需要", "要求"],
                "confidence_threshold": 0.7
            },

            "条文解释": {
                "base_template": """你是小诺，专业的法律条文解读专家。

需解释条文：{query}

条文背景：
{background_info}

相关法律依据：
{legal_basis}

解释要点：
1. 条文的核心含义和立法目的
2. 条文的适用范围和条件
3. 实务中的理解和应用
4. 相关案例或司法解释
5. 注意事项和例外情况

请提供专业、准确的条文解释：
""",
                "keywords": ["解释", "含义", "是什么意思", "如何理解"],
                "confidence_threshold": 0.8
            },

            "案件分析": {
                "base_template": """你是小诺，具备丰富案件分析经验的法律专家。

案件情况：{query}

相关法律分析：
{legal_analysis}

可能涉及的法律关系：
{legal_relations}

分析框架：
1. 案件基本事实认定
2. 法律关系识别
3. 适用法律条文
4. 权利义务分析
5. 法律责任判断
6. 解决方案建议

请进行专业的案件分析：
""",
                "keywords": ["案件", "纠纷", "争议", "诉讼", "仲裁"],
                "confidence_threshold": 0.75
            },

            "程序指导": {
                "base_template": """你是小诺，熟悉各类法律程序的法律实务专家。

程序问题：{query}

程序依据：
{procedure_basis}

办理流程：
{procedure_steps}

注意事项：
{precautions}

指导要点：
1. 清晰的步骤指引
2. 所需材料和条件
3. 时间节点和期限
4. 可能遇到的问题及解决方案
5. 相关费用及时长

请提供详细的程序指导：
""",
                "keywords": ["流程", "步骤", "程序", "如何办理", "申请", "起诉", "上诉"],
                "confidence_threshold": 0.8
            },

            "合同审查": {
                "base_template": """你是小诺，专业的合同审查专家。

合同问题：{query}

相关合同法规：
{contract_laws}

审查要点：
{review_points}

审查框架：
1. 合同主体资格审查
2. 合同内容合法性
3. 权利义务明确性
4. 违约责任合理性
5. 争议解决条款
6. 其他重要条款

请提供专业的合同审查意见：
""",
                "keywords": ["合同", "协议", "条款", "违约", "签署"],
                "confidence_threshold": 0.85
            }
        }

    def generate_prompt(self, query: str, context: dict = None) -> dict:
        """生成动态提示词"""
        # 识别查询类型
        query_type = self._identify_query_type(query)

        # 搜索相关法律依据
        legal_basis = self._get_legal_basis(query, query_type)

        # 获取额外上下文
        extra_context = self._get_extra_context(query, query_type)

        # 生成提示词
        template = self.prompt_templates.get(query_type, self.prompt_templates["法律咨询"])

        prompt = template["base_template"].format(
            query=query,
            legal_basis=self._format_legal_basis(legal_basis),
            background_info=extra_context.get("background", ""),
            legal_analysis=extra_context.get("analysis", ""),
            legal_relations=extra_context.get("relations", ""),
            procedure_basis=extra_context.get("procedure", ""),
            procedure_steps=extra_context.get("steps", ""),
            precautions=extra_context.get("precautions", ""),
            contract_laws=extra_context.get("contract", ""),
            review_points=extra_context.get("review", "")
        )

        # 添加专业增强
        prompt = self._enhance_prompt(prompt, query_type, legal_basis)

        return {
            "prompt": prompt,
            "type": query_type,
            "legal_basis": legal_basis,
            "confidence": self._calculate_confidence(legal_basis, query_type),
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "template_used": query_type,
                "basis_count": len(legal_basis)
            }
        }

    def _identify_query_type(self, query: str) -> str:
        """识别查询类型"""
        query_lower = query.lower()

        # 按优先级检查关键词
        for query_type, template in self.prompt_templates.items():
            if any(keyword in query_lower for keyword in template["keywords"]):
                return query_type

        # 默认返回法律咨询
        return "法律咨询"

    def _get_legal_basis(self, query: str, query_type: str) -> list[dict]:
        """获取法律依据"""
        # 使用混合搜索获取相关法律
        results = self.kg_support.hybrid_search(query, top_k=10)

        # 根据查询类型过滤和排序
        filtered_results = self._filter_results(results, query_type)

        return filtered_results[:5]  # 返回前5个最相关的

    def _filter_results(self, results: list[dict], query_type: str) -> list[dict]:
        """根据查询类型过滤结果"""
        if query_type == "条文解释":
            # 优先显示条文内容
            results.sort(key=lambda x: (
                1 if "条文" in x.get("type", "") or "条" in x.get("title", "") else 0,
                x.get("score", 0)
            ), reverse=True)
        elif query_type == "程序指导":
            # 优先显示程序相关内容
            procedure_keywords = ["程序", "流程", "步骤", "办法", "规定"]
            results.sort(key=lambda x: (
                sum(1 for kw in procedure_keywords if kw in (x.get("title", "") + x.get("content", ""))),
                x.get("score", 0)
            ), reverse=True)
        elif query_type == "合同审查":
            # 优先显示合同相关法律
            contract_keywords = ["合同", "协议", "民法典合同编"]
            results.sort(key=lambda x: (
                sum(1 for kw in contract_keywords if kw in (x.get("title", "") + x.get("content", ""))),
                x.get("score", 0)
            ), reverse=True)

        return results

    def _format_legal_basis(self, legal_basis: list[dict]) -> str:
        """格式化法律依据"""
        if not legal_basis:
            return "暂无直接相关法律依据"

        formatted = []
        for i, basis in enumerate(legal_basis, 1):
            if basis.get("title"):
                formatted.append(f"{i}. 《{basis['title']}》")
                if basis.get("content"):
                    content = basis['content'][:150] + "..." if len(basis['content']) > 150 else basis['content']
                    formatted.append(f"   {content}")
                if basis.get("similarity"):
                    formatted.append(f"   相似度: {basis['similarity']:.2%}")
                formatted.append("")

        return "\n".join(formatted)

    def _get_extra_context(self, query: str, query_type: str) -> dict:
        """获取额外上下文"""
        context = {}

        if query_type == "条文解释":
            # 获取条文背景
            context["background"] = self._get_article_background(query)
        elif query_type == "案件分析":
            # 获取法律关系分析
            context["relations"] = self._analyze_legal_relations(query)
        elif query_type == "程序指导":
            # 获取程序步骤
            context["steps"] = self._get_procedure_steps(query)
            context["precautions"] = self._get_procedure_precautions(query)
        elif query_type == "合同审查":
            # 获取审查要点
            context["review"] = self._get_contract_review_points(query)

        return context

    def _get_article_background(self, query: str) -> str:
        """获取条文背景信息"""
        # 查找条文的立法背景
        background = """
立法背景：
- 该条文制定的初衷和目的
- 旨在解决的实际问题
- 在法律体系中的地位和作用
        """.strip()
        return background

    def _analyze_legal_relations(self, query: str) -> str:
        """分析法律关系"""
        return """
可能涉及的法律关系：
1. 民事法律关系：物权、债权、合同等
2. 行政法律关系：行政许可、行政处罚等
3. 刑事法律关系：犯罪构成、刑事责任等
4. 程序法律关系：诉讼、仲裁、执行等
        """.strip()

    def _get_procedure_steps(self, query: str) -> str:
        """获取程序步骤"""
        return """
标准程序步骤：
1. 准备阶段：收集材料、整理证据
2. 申请阶段：提交申请、缴纳费用
3. 审查阶段：部门审查、补充材料
4. 决定阶段：作出决定、送达文书
5. 救济阶段：行政复议、行政诉讼
        """.strip()

    def _get_procedure_precautions(self, query: str) -> str:
        """获取程序注意事项"""
        return """
重要注意事项：
- 注意法定时限和期限
- 确保材料真实、完整
- 保留所有证据和凭证
- 及时跟进办理进度
- 必要时寻求专业帮助
        """.strip()

    def _get_contract_review_points(self, query: str) -> str:
        """获取合同审查要点"""
        return """
合同审查要点：
1. 主体资格：核实签约主体资质
2. 内容合法：确保内容不违反法律
3. 条款明确：权利义务表述清晰
4. 违约责任：违约条款合理明确
5. 争议解决：约定合适的解决方式
6. 其他条款：保密、不可抗力等
        """.strip()

    def _enhance_prompt(self, prompt: str, query_type: str, legal_basis: list[dict]) -> str:
        """增强提示词"""
        # 添加专业身份强化
        identity_enhancement = """
身份强化：
作为小诺，你拥有：
- 深厚的法学理论基础
- 丰富的实务操作经验
- 敏锐的法律风险意识
- 良好的沟通表达能力

专业素养：
- 始终以事实为依据，以法律为准绳
- 保持客观中立，不偏不倚
- 注重保护当事人合法权益
- 提供实用、可操作的建议
"""

        # 添加时效性提醒
        time_reminder = f"""
时效提醒：
当前日期：{datetime.now().strftime('%Y年%m月%d日')}
请注意法律的时效性和最新变化
"""

        # 添加免责声明
        disclaimer = """
免责声明：
本回答仅供参考，不构成正式法律意见
具体案件请咨询专业律师
"""

        # 组合增强
        enhanced_prompt = identity_enhancement + "\n" + prompt + "\n" + time_reminder + "\n" + disclaimer

        return enhanced_prompt

    def _calculate_confidence(self, legal_basis: list[dict], query_type: str) -> float:
        """计算置信度"""
        if not legal_basis:
            return 0.3

        # 基础置信度
        base_confidence = self.prompt_templates[query_type]["confidence_threshold"]

        # 根据法律依据调整
        high_similarity_count = sum(1 for b in legal_basis if b.get("similarity", 0) > 0.8)
        if high_similarity_count >= 2:
            base_confidence += 0.1

        # 根据数量调整
        if len(legal_basis) >= 3:
            base_confidence += 0.05

        return min(base_confidence, 0.95)  # 最高0.95

    def generate_rule_basis(self, query: str) -> dict:
        """生成规则依据"""
        # 搜索相关规则
        search_results = self.kg_support.hybrid_search(query, top_k=20)

        # 分类整理
        categorized = self._categorize_rules(search_results)

        # 生成规则树
        rule_tree = self._build_rule_tree(categorized)

        return {
            "query": query,
            "rule_tree": rule_tree,
            "categorized_rules": categorized,
            "total_rules": len(search_results),
            "high_confidence_rules": len([r for r in search_results if r.get("score", 0) > 0.7])
        }

    def _categorize_rules(self, rules: list[dict]) -> dict:
        """分类规则"""
        categories = {
            "宪法法律": [],
            "行政法规": [],
            "部门规章": [],
            "司法解释": [],
            "地方性法规": [],
            "其他": []
        }

        for rule in rules:
            title = rule.get("title", "")
            if "宪法" in title:
                categories["宪法法律"].append(rule)
            elif "行政法规" in title or "条例" in title:
                categories["行政法规"].append(rule)
            elif "司法解释" in title or "解释" in title:
                categories["司法解释"].append(rule)
            elif "办法" in title or "规定" in title or "决定" in title:
                categories["部门规章"].append(rule)
            else:
                categories["其他"].append(rule)

        return {k: v for k, v in categories.items() if v}

    def _build_rule_tree(self, categorized: dict) -> dict:
        """构建规则树"""
        tree = {
            "root": {
                "type": "法律依据",
                "children": []
            }
        }

        for category, rules in categorized.items():
            node = {
                "type": category,
                "count": len(rules),
                "children": []
            }

            for rule in rules[:5]:  # 限制每个类别最多5个
                node["children"].append({
                    "type": "规则",
                    "title": rule.get("title", ""),
                    "content": rule.get("content", "")[:100],
                    "confidence": rule.get("score", 0)
                })

            tree["root"]["children"].append(node)

        return tree

    def get_prompt_suggestions(self, query: str) -> list[str]:
        """获取提示词建议"""
        suggestions = []

        # 基于查询类型生成建议
        query_type = self._identify_query_type(query)

        if query_type == "法律咨询":
            suggestions.extend([
                "请提供更多案件细节",
                "您是否已经尝试过其他解决方式？",
                "是否有相关的书面材料？"
            ])
        elif query_type == "程序指导":
            suggestions.extend([
                "您目前处于哪个阶段？",
                "是否已经准备了必要材料？",
                "时间要求是否紧迫？"
            ])
        elif query_type == "合同审查":
            suggestions.extend([
                "合同签署方是谁？",
                "合同主要内容是什么？",
                "是否已经签署？"
            ])

        return suggestions[:3]


# 使用示例
if __name__ == "__main__":
    # 初始化
    from legal_kg_support import LegalKnowledgeGraphSupport

    kg_support = LegalKnowledgeGraphSupport()
    generator = LegalPromptGenerator(kg_support)

    # 测试生成提示词
    test_queries = [
        "离婚时财产如何分割？",
        "请解释民法典第一千零七十七条",
        "如何申请劳动仲裁？",
        "房屋买卖合同需要注意什么？"
    ]

    for query in test_queries:
        print(f"\n=== 查询: {query} ===")
        result = generator.generate_prompt(query)
        print(f"类型: {result['type']}")
        print(f"置信度: {result['confidence']:.2f}")
        print(f"法律依据数量: {len(result['legal_basis'])}")
        print("\n生成的提示词（前500字）:")
        print(result['prompt'][:500] + "...")

        # 获取建议
        suggestions = generator.get_prompt_suggestions(query)
        if suggestions:
            print("\n建议追问:")
            for s in suggestions:
                print(f"- {s}")

    kg_support.close()
