#!/usr/bin/env python3
"""
动态提示词生成器
根据专利业务场景,从专利规则向量库和知识图谱中提取相关规则和知识,动态生成提示词
"""
import logging
from dataclasses import dataclass
from datetime import datetime

import numpy as np
import requests
from sentence_transformers import SentenceTransformer

from core.knowledge.unified_knowledge_graph import UnifiedKnowledgeGraph as KnowledgeGraphManager
from core.logging_config import setup_logging
from core.storage.unified_storage_manager import UnifiedStorageManager as VectorManager

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
class DynamicPrompt:
    """动态生成的提示词"""

    system_prompt: str  # 系统级提示
    context_prompt: str  # 上下文提示
    rules_prompt: str  # 规则提示
    knowledge_prompt: str  # 知识提示
    action_prompt: str  # 行动提示
    confidence_score: float  # 置信度分数
    sources: list[dict]  # 数据来源


class DynamicPromptGenerator:
    """动态提示词生成器"""

    def __init__(self):
        """初始化动态提示词生成器"""
        self.vector_manager = VectorManager()
        self.graph_manager = KnowledgeGraphManager()
        self.encoder = SentenceTransformer("shibing624/text2vec-base-chinese")

        # API服务端点
        self.api_base = "http://localhost:8085/api/v2"

        # 业务类型映射
        self.business_type_mapping = {
            "专利申请": ["申请", "提交", "文件准备", "审查", "授权"],
            "专利审查": ["审查", "检索", "新颖性", "创造性", "实用性"],
            "专利无效": ["无效", "宣告无效", "证据", "现有技术", "公开充分"],
            "专利诉讼": ["诉讼", "侵权", "证据", "赔偿", "禁令"],
            "专利转让": ["转让", "许可", "合同", "备案", "登记"],
            "专利维护": ["年费", "维护", "期限", "续展", "恢复"],
        }

        # 紧急程度权重
        self.urgency_weights = {"低": 0.3, "中": 0.6, "高": 1.0}

        logger.info("动态提示词生成器初始化完成")

    def parse_business_context(self, user_input: str) -> PatentContext:
        """解析业务上下文"""
        user_input_lower = user_input.lower()

        # 识别业务类型
        business_type = "通用咨询"
        for btype, keywords in self.business_type_mapping.items():
            if any(kw in user_input_lower for kw in keywords):
                business_type = btype
                break

        # 识别技术领域
        tech_fields = ["电子信息", "生物医药", "机械制造", "化学材料", "新能源", "人工智能"]
        technology_field = "通用"
        for field in tech_fields:
            if field in user_input:
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

        # 识别紧急程度
        urgency_level = "中"
        if any(word in user_input for word in ["紧急", "尽快", "立即", "加急"]):
            urgency_level = "高"
        elif any(word in user_input for word in ["不急", "慢慢", "常规"]):
            urgency_level = "低"

        # 识别复杂程度
        complexity_level = "中等"
        if any(word in user_input for word in ["简单", "基础", "基本"]):
            complexity_level = "简单"
        elif any(word in user_input for word in ["复杂", "疑难", "专业"]):
            complexity_level = "复杂"

        return PatentContext(
            business_type=business_type,
            technology_field=technology_field,
            keywords=keywords,
            user_query=user_input,
            urgency_level=urgency_level,
            complexity_level=complexity_level,
        )

    async def search_relevant_rules(self, context: PatentContext, top_k: int = 10) -> list[dict]:
        """从向量库搜索相关规则"""
        try:
            # 构建搜索查询
            search_query = (
                f"{context.business_type} {context.technology_field} {' '.join(context.keywords)}"
            )

            # 调用向量搜索API
            search_data = {
                "query": search_query,
                "collection": "patent_rules_1024",
                "top_k": top_k,
                "threshold": 0.5,
            }

            response = requests.post(f"{self.api_base}/search", json=search_data, timeout=10)

            if response.status_code == 200:
                result = response.json()
                return result.get("results", [])
            else:
                logger.error(f"向量搜索失败: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"搜索相关规则时出错: {e}")
            return []

    async def get_related_knowledge(self, context: PatentContext, max_depth: int = 2) -> list[dict]:
        """从知识图谱获取相关知识"""
        try:
            # 调用知识图谱查询API
            query_data = {
                "query": context.business_type,
                "node_types": ["概念", "程序", "期限"],
                "max_depth": max_depth,
                "limit": 20,
            }

            response = requests.post(f"{self.api_base}/graph/query", json=query_data, timeout=10)

            if response.status_code == 200:
                result = response.json()
                return result.get("nodes", []) + result.get("relations", [])
            else:
                logger.error(f"知识图谱查询失败: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"获取相关知识时出错: {e}")
            return []

    def calculate_rule_relevance(self, rule: dict, context: PatentContext) -> float:
        """计算规则与上下文的相关性分数"""
        score = 0.0

        # 业务类型匹配
        if context.business_type in rule.get("content", ""):
            score += 0.4

        # 关键词匹配
        rule_content = rule.get("content", "").lower()
        for keyword in context.keywords:
            if keyword.lower() in rule_content:
                score += 0.2

        # 技术领域匹配
        if context.technology_field in rule.get("source_file", ""):
            score += 0.1

        # 相似度分数
        similarity = rule.get("similarity", 0.0)
        score += similarity * 0.3

        return min(score, 1.0)

    def organize_rules_by_category(
        self, rules: list[dict], context: PatentContext
    ) -> dict[str, list[dict]]:
        """按类别组织规则"""
        categories = {
            "核心原则": [],
            "程序要求": [],
            "期限规定": [],
            "费用标准": [],
            "特殊条款": [],
        }

        for rule in rules:
            content = rule.get("content", "")

            # 根据内容特征分类
            if any(word in content for word in ["原则", "要求", "条件"]):
                categories["核心原则"].append(rule)
            elif any(word in content for word in ["程序", "流程", "步骤", "提交"]):
                categories["程序要求"].append(rule)
            elif any(word in content for word in ["期限", "时间", "日内", "月内"]):
                categories["期限规定"].append(rule)
            elif any(word in content for word in ["费用", "收费", "金额"]):
                categories["费用标准"].append(rule)
            else:
                categories["特殊条款"].append(rule)

        return categories

    def generate_system_prompt(self, context: PatentContext) -> str:
        """生成系统级提示"""
        base_prompt = """你是Athena平台的专业专利助手,具备以下核心能力:

1. 专业知识体系:
   - 精通中国专利法律法规
   - 熟悉专利申请、审查、无效、诉讼全流程
   - 掌握各技术领域的专利特点

2. 数据支撑:
   - 专利规则向量库:3032条规则,动态更新
   - 专利知识图谱:2992个节点,2989个关系
   - 实时检索相关规则和知识

3. 服务原则:
   - 基于最新法律法规提供准确信息
   - 根据具体业务场景提供定制化建议
   - 明确标识信息来源和时效性

4. 质量保证:
   - 提供法律依据和具体条文
   - 标注重要期限和注意事项
   - 建议后续行动和风险提示"""

        # 根据业务类型添加专项提示
        business_specific_prompts = {
            "专利申请": """
5. 专利申请专项:
   - 指导申请文件准备
   - 评估可专利性
   - 规划申请策略""",
            "专利审查": """
5. 专利审查专项:
   - 分析审查意见
   - 制定答复策略
   - 提供对比文件分析""",
            "专利诉讼": """
5. 专利诉讼专项:
   - 评估侵权风险
   - 制定诉讼策略
   - 提供证据指引""",
        }

        if context.business_type in business_specific_prompts:
            base_prompt += business_specific_prompts[context.business_type]

        return base_prompt

    def generate_context_prompt(self, context: PatentContext) -> str:
        """生成上下文提示"""
        prompt = f"""## 当前业务场景
- **业务类型**: {context.business_type}
- **技术领域**: {context.technology_field}
- **关键要素**: {', '.join(context.keywords) if context.keywords else '通用'}
- **紧急程度**: {context.urgency_level}
- **复杂程度**: {context.complexity_level}

## 用户需求
{context.user_query}

## 处理要求
- 基于专利规则向量库和知识图谱提供专业解答
- 引用具体的法律条文和规定
- 明确重要期限和程序要求
- 提供可操作的建议和后续步骤
- 标注信息来源和更新时间"""

        return prompt

    def generate_rules_prompt(
        self, categorized_rules: dict[str, list[dict], context: PatentContext
    ) -> str:
        """生成规则提示"""
        prompt = "## 相关法规规则\n\n"

        for category, rules in categorized_rules.items():
            if rules:
                prompt += f"### {category}\n\n"
                for i, rule in enumerate(rules[:3], 1):  # 每类最多显示3条
                    relevance = self.calculate_rule_relevance(rule, context)
                    if relevance > 0.5:  # 只显示相关性高的规则
                        content = rule.get("content", "")[:150]  # 限制长度
                        if len(content) == 150:
                            content += "..."
                        source = rule.get("source_file", "未知来源")
                        prompt += (
                            f"{i}. {content}\n   - 来源: {source}\n   - 相关性: {relevance:.2f}\n\n"
                        )

        # 添加使用说明
        prompt += """
## 规则使用说明
- 上述规则基于向量相似度和业务类型匹配得出
- 相关性分数越高,规则与当前场景的关联性越强
- 实际应用时请结合具体案情和最新法规
- 建议核对原始法规条文以确认准确性"""

        return prompt

    def generate_knowledge_prompt(self, knowledge: list[dict]) -> str:
        """生成知识提示"""
        prompt = "## 专利知识图谱要点\n\n"

        if not knowledge:
            prompt += "暂无相关知识图谱信息。"
            return prompt

        # 组织知识要点
        concepts = []
        procedures = []
        deadlines = []

        for item in knowledge:
            if isinstance(item, dict):
                if item.get("type") == "概念":
                    concepts.append(item)
                elif item.get("type") == "程序":
                    procedures.append(item)
                elif item.get("type") == "期限":
                    deadlines.append(item)

        # 概念知识
        if concepts:
            prompt += "### 核心概念\n"
            for concept in concepts[:5]:
                name = concept.get("name", "未知概念")
                desc = concept.get("description", "")[:100]
                prompt += f"- **{name}**: {desc}\n"
            prompt += "\n"

        # 程序流程
        if procedures:
            prompt += "### 程序流程\n"
            for procedure in procedures[:3]:
                name = procedure.get("name", "未知程序")
                steps = procedure.get("steps", [])
                prompt += f"- **{name}**: {' → '.join(steps[:3])}\n"
            prompt += "\n"

        # 重要期限
        if deadlines:
            prompt += "### 重要期限\n"
            for deadline in deadlines[:3]:
                name = deadline.get("name", "未知期限")
                time_limit = deadline.get("time_limit", "")
                prompt += f"- **{name}**: {time_limit}\n"
            prompt += "\n"

        return prompt

    def generate_action_prompt(self, context: PatentContext, rules: list[dict]) -> str:
        """生成行动提示"""
        prompt = "## 建议行动计划\n\n"

        # 基于业务类型的行动建议
        action_templates = {
            "专利申请": [
                "评估发明的可专利性",
                "准备专利申请文件",
                "确定申请策略和路径",
                "关注申请时限",
            ],
            "专利审查": ["分析审查意见通知", "检索对比文件", "制定答复策略", "准备修改或答辩材料"],
            "专利无效": ["收集无效宣告证据", "分析专利稳定性", "准备无效宣告理由", "关注法定期限"],
            "专利诉讼": ["评估侵权指控", "收集侵权证据", "制定诉讼策略", "考虑和解可能"],
        }

        if context.business_type in action_templates:
            actions = action_templates[context.business_type]
        else:
            actions = ["分析具体情况", "查找相关法规", "制定解决方案", "咨询专业意见"]

        for i, action in enumerate(actions, 1):
            prompt += f"{i}. {action}\n"

        # 添加风险提示
        prompt += "\n## 重要提醒\n"
        prompt += "- 请注意相关法定期限,避免丧失权利\n"
        prompt += "- 建议咨询专业专利代理人或律师\n"
        prompt += "- 法规可能更新,请确认最新版本\n"

        if context.urgency_level == "高":
            prompt += "- 紧急事项请优先处理,必要时寻求加急服务\n"

        return prompt

    def calculate_confidence_score(
        self, rules: list[dict], knowledge: list[dict], context: PatentContext
    ) -> float:
        """计算整体置信度分数"""
        score = 0.5  # 基础分数

        # 规则匹配度
        if rules:
            avg_similarity = np.mean([r.get("similarity", 0) for r in rules])
            score += avg_similarity * 0.3

        # 知识覆盖度
        if knowledge:
            score += min(len(knowledge) / 10, 0.2)

        # 业务类型明确度
        if context.business_type != "通用咨询":
            score += 0.1

        # 关键词丰富度
        if context.keywords:
            score += min(len(context.keywords) / 5, 0.1)

        return min(score, 1.0)

    def extract_sources(self, rules: list[dict], knowledge: list[dict]) -> list[dict]:
        """提取数据来源信息"""
        sources = []

        # 规则来源
        rule_sources = {}
        for rule in rules:
            source_file = rule.get("source_file", "未知来源")
            if source_file not in rule_sources:
                rule_sources[source_file] = 0
            rule_sources[source_file] += 1

        for source, count in rule_sources.items():
            sources.append(
                {
                    "type": "法规文件",
                    "name": source,
                    "count": count,
                    "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

        # 知识图谱来源
        if knowledge:
            sources.append(
                {
                    "type": "知识图谱",
                    "name": "专利规则知识图谱",
                    "count": len(knowledge),
                    "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

        return sources

    async def generate_dynamic_prompt(self, user_input: str) -> DynamicPrompt:
        """生成动态提示词"""
        try:
            # 解析业务上下文
            context = self.parse_business_context(user_input)
            logger.info(f"解析业务上下文: {context.business_type}")

            # 搜索相关规则
            rules = await self.search_relevant_rules(context)
            logger.info(f"搜索到 {len(rules)} 条相关规则")

            # 获取相关知识
            knowledge = await self.get_related_knowledge(context)
            logger.info(f"获取到 {len(knowledge)} 条相关知识")

            # 组织规则
            categorized_rules = self.organize_rules_by_category(rules, context)

            # 生成各部分提示词
            system_prompt = self.generate_system_prompt(context)
            context_prompt = self.generate_context_prompt(context)
            rules_prompt = self.generate_rules_prompt(categorized_rules, context)
            knowledge_prompt = self.generate_knowledge_prompt(knowledge)
            action_prompt = self.generate_action_prompt(context, rules)

            # 计算置信度
            confidence_score = self.calculate_confidence_score(rules, knowledge, context)

            # 提取数据来源
            sources = self.extract_sources(rules, knowledge)

            # 组装动态提示词
            dynamic_prompt = DynamicPrompt(
                system_prompt=system_prompt,
                context_prompt=context_prompt,
                rules_prompt=rules_prompt,
                knowledge_prompt=knowledge_prompt,
                action_prompt=action_prompt,
                confidence_score=confidence_score,
                sources=sources,
            )

            logger.info(f"动态提示词生成完成,置信度: {confidence_score:.2f}")
            return dynamic_prompt

        except Exception as e:
            logger.error(f"生成动态提示词时出错: {e}")
            # 返回基础提示词
            return DynamicPrompt(
                system_prompt="你是Athena平台的专利助手,请基于您的专业知识为用户提供帮助。",
                context_prompt=f"用户咨询: {user_input}",
                rules_prompt="暂时无法获取相关规则信息。",
                knowledge_prompt="暂时无法获取相关知识图谱信息。",
                action_prompt="建议咨询专业专利代理人或律师。",
                confidence_score=0.3,
                sources=[],
            )

    def format_prompt_for_display(self, prompt: DynamicPrompt) -> str:
        """格式化提示词用于显示"""
        formatted = f"""# Athena平台动态提示词

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
置信度分数: {prompt.confidence_score:.2f}

{prompt.system_prompt}

{prompt.context_prompt}

{prompt.rules_prompt}

{prompt.knowledge_prompt}

{prompt.action_prompt}

## 数据来源
"""
        for source in prompt.sources:
            formatted += f"- {source['type']}: {source['name']} ({source['count']}条)\n"

        return formatted


# 异步主函数
async def main():
    """测试动态提示词生成器"""
    generator = DynamicPromptGenerator()

    # 测试用例
    test_queries = [
        "我有一个发明,想申请专利,需要准备什么材料?",
        "专利审查意见收到了,说我没有创造性,怎么办?",
        "发现有人侵犯我的专利权,如何起诉?",
        "专利年费快到期了,怎么缴纳?",
    ]

    for query in test_queries:
        logger.info(f"\n{'='*60}")
        logger.info(f"用户查询: {query}")
        logger.info(str("=" * 60))

        prompt = await generator.generate_dynamic_prompt(query)
        logger.info(str(generator.format_prompt_for_display(prompt)))


# 入口点: @async_main装饰器已添加到main函数
