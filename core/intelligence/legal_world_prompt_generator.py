#!/usr/bin/env python3
from __future__ import annotations
"""
法律世界模型动态提示词生成器
基于Neo4j法律世界模型数据直接生成动态提示词，不依赖外部API服务

作者: Athena平台团队
版本: 2.0.0
创建时间: 2026-02-19
"""

import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from dotenv import load_dotenv
from neo4j import GraphDatabase

from core.logging_config import setup_logging

# 加载环境变量
load_dotenv()

# 配置日志
logger = setup_logging()


@dataclass
class LegalContext:
    """法律业务上下文"""

    business_type: str  # 业务类型
    domain: str  # 领域 (patent/trademark/copyright等)
    keywords: list[str]  # 关键词
    user_query: str  # 用户查询
    urgency_level: str  # 紧急程度
    complexity_level: str  # 复杂程度


@dataclass
class LegalDocument:
    """法律文档"""

    doc_id: str
    title: str
    content: str
    source: str
    relevance_score: float
    doc_type: str


@dataclass
class ScenarioRule:
    """场景规则"""

    rule_id: str
    domain: str
    task_type: str
    phase: str
    system_prompt: str
    user_prompt: str
    processing_rules: list[str]


@dataclass
class DynamicPrompt:
    """动态生成的提示词"""

    system_prompt: str
    context_prompt: str
    rules_prompt: str
    knowledge_prompt: str
    action_prompt: str
    confidence_score: float
    sources: list[dict[str, Any]]
    matched_scenario: ScenarioRule | None = None


class LegalWorldPromptGenerator:
    """基于法律世界模型的动态提示词生成器"""

    # 业务类型映射
    BUSINESS_TYPE_MAPPING = {
        "专利申请": ["申请", "提交", "文件准备", "授权", "说明书"],
        "专利审查": ["审查", "检索", "新颖性", "创造性", "审查意见"],
        "专利无效": ["无效", "宣告无效", "证据", "现有技术", "稳定性"],
        "专利诉讼": ["诉讼", "侵权", "赔偿", "禁令", "侵权分析"],
        "专利转让": ["转让", "许可", "合同", "备案"],
        "专利维护": ["年费", "维护", "期限", "续展", "恢复"],
    }

    # 技术领域
    TECH_FIELDS = ["电子信息", "生物医药", "机械制造", "化学材料", "新能源", "人工智能"]

    # 关键词提取
    KEYWORD_PATTERNS = {
        "发明": ["发明", "发明专利"],
        "实用新型": ["实用新型", "实用新型专利"],
        "外观设计": ["外观", "外观设计"],
        "权利要求": ["权利要求", "权利要求书"],
        "说明书": ["说明书", "技术方案"],
    }

    def __init__(self):
        """初始化提示词生成器"""
        # Neo4j连接配置
        self.neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user = os.getenv("NEO4J_USERNAME", "neo4j")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD", "athena_neo4j_2024")

        # 创建Neo4j驱动
        self.driver = GraphDatabase.driver(
            self.neo4j_uri, auth=(self.neo4j_user, self.neo4j_password)
        )

        # 测试连接
        self._verify_connection()

        logger.info("法律世界模型动态提示词生成器初始化完成")

    def _verify_connection(self):
        """验证Neo4j连接"""
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                result.single()
            logger.info("✅ Neo4j连接成功")
        except Exception as e:
            logger.error(f"❌ Neo4j连接失败: {e}")
            raise

    def close(self):
        """关闭数据库连接"""
        if self.driver:
            self.driver.close()

    def parse_business_context(self, user_input: str) -> LegalContext:
        """解析业务上下文"""
        if isinstance(user_input, str):
            user_input_lower = user_input.lower()
        else:
            user_input_lower = str(user_input).lower()

        # 识别业务类型
        business_type = "通用咨询"
        for btype, keywords in self.BUSINESS_TYPE_MAPPING.items():
            if any(kw in user_input_lower for kw in keywords):
                business_type = btype
                break

        # 识别技术领域
        for field in self.TECH_FIELDS:
            if field in user_input:
                break

        # 提取关键词
        keywords = []
        for _key_word, patterns in self.KEYWORD_PATTERNS.items():
            if any(pattern in user_input for pattern in patterns):
                keywords.extend(patterns)

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

        return LegalContext(
            business_type=business_type,
            domain="patent",  # 当前专注专利领域
            keywords=keywords,
            user_query=user_input,
            urgency_level=urgency_level,
            complexity_level=complexity_level,
        )

    def search_legal_documents(self, context: LegalContext, limit: int = 10) -> list[LegalDocument]:
        """从Neo4j搜索相关法律文档"""
        # 使用article_title而不是title
        query = """
        MATCH (doc:LawDocument)
        WHERE doc.article_title IS NOT NULL
          AND (
            doc.article_title CONTAINS $business_type
            OR doc.article_title CONTAINS $keyword1
            OR doc.article_title CONTAINS $keyword2
            OR doc.source_file CONTAINS $keyword3
          )
        RETURN doc
        ORDER BY doc.article_order
        LIMIT $limit
        """

        try:
            with self.driver.session() as session:
                result = session.run(
                    query,
                    {
                        "business_type": context.business_type[:4],  # 使用前4个字符匹配
                        "keyword1": context.keywords[0] if context.keywords else "",
                        "keyword2": context.keywords[1] if len(context.keywords) > 1 else "",
                        "keyword3": context.keywords[2] if len(context.keywords) > 2 else "",
                        "limit": limit,
                    },
                )

                documents = []
                for record in result:
                    doc = record["doc"]
                    documents.append(
                        LegalDocument(
                            doc_id=doc.get("article_id", ""),
                            title=doc.get("article_title", ""),
                            content=doc.get("content", "")[:500],  # 限制长度
                            source=doc.get("source_file", "法律世界模型"),
                            relevance_score=0.8,  # 默认相关性
                            doc_type=doc.get("category", "法规"),
                        )
                    )

                logger.info(f"📜 搜索到 {len(documents)} 条法律文档")
                return documents

        except Exception as e:
            logger.error(f"搜索法律文档失败: {e}")
            return []

    def retrieve_scenario_rule(self, context: LegalContext) -> ScenarioRule | None:
        """检索匹配的场景规则"""
        # 根据业务类型匹配场景
        task_type_mapping = {
            "专利申请": ["specification_completion", "claims_layout", "quality_check"],
            "专利审查": ["correction_response", "novelty_response", "creativity_response"],
            "专利无效": ["invalidation_analysis", "invalidation_defense"],
            "专利诉讼": ["infringement_analysis"],
        }

        task_types = task_type_mapping.get(context.business_type, [])

        for task_type in task_types:
            query = """
            MATCH (sr:ScenarioRule)
            WHERE sr.domain = $domain
              AND sr.task_type = $task_type
              AND sr.is_active = true
            RETURN sr
            LIMIT 1
            """

            try:
                with self.driver.session() as session:
                    result = session.run(query, {"domain": "patent", "task_type": task_type})
                    record = result.single()

                    if record:
                        sr = record["sr"]
                        return ScenarioRule(
                            rule_id=sr.get("rule_id", ""),
                            domain=sr.get("domain", ""),
                            task_type=sr.get("task_type", ""),
                            phase=sr.get("phase", ""),
                            system_prompt=sr.get("system_prompt_template", ""),
                            user_prompt=sr.get("user_prompt_template", ""),
                            processing_rules=json.loads(sr.get("processing_rules", "[]")),
                        )

            except Exception as e:
                logger.debug(f"检索场景规则失败: {e}")
                continue

        return None

    def generate_system_prompt(self, context: LegalContext) -> str:
        """生成系统级提示"""
        base_prompt = f"""你是Athena平台的专业法律助手,专注于{context.domain.upper()}领域。

## 核心能力
1. **专业知识**: 精通{context.domain.upper()}相关法律法规
2. **数据支撑**: 基于法律世界模型34万+法律文档和知识图谱
3. **实时检索**: 动态检索相关法规、案例和规则
4. **专业服务**: 提供准确、及时、专业的法律咨询

## 服务原则
- 基于最新法律法规提供准确信息
- 根据具体业务场景提供定制化建议
- 明确标识信息来源和时效性
- 提供法律依据和具体条文
- 标注重要期限和注意事项

## 质量保证
- 提供的法律建议基于权威法律条文
- 标注信息来源和更新时间
- 建议后续行动和风险提示
- 必要时建议咨询专业律师"""

        # 根据业务类型添加专项提示
        business_specific = {
            "专利申请": "\n\n## 专利申请专项\n- 指导申请文件准备\n- 评估可专利性\n- 规划申请策略",
            "专利审查": "\n\n## 专利审查专项\n- 分析审查意见\n- 制定答复策略\n- 提供对比文件分析",
            "专利诉讼": "\n\n## 专利诉讼专项\n- 评估侵权风险\n- 制定诉讼策略\n- 提供证据指引",
        }

        if context.business_type in business_specific:
            base_prompt += business_specific[context.business_type]

        return base_prompt

    def generate_context_prompt(self, context: LegalContext) -> str:
        """生成上下文提示"""
        return f"""## 当前业务场景
- **业务类型**: {context.business_type}
- **技术领域**: {context.domain.upper()}
- **关键要素**: {", ".join(context.keywords) if context.keywords else "通用"}
- **紧急程度**: {context.urgency_level}
- **复杂程度**: {context.complexity_level}

## 用户需求
{context.user_query}

## 处理要求
- 基于法律世界模型34万+法律文档提供专业解答
- 引用具体的法律条文和规定
- 明确重要期限和程序要求
- 提供可操作的建议和后续步骤
- 标注信息来源和更新时间"""

    def generate_rules_prompt(self, documents: list[LegalDocument], context: LegalContext) -> str:
        """生成法规提示"""
        if not documents:
            return "## 相关法规规则\n\n暂未找到完全匹配的法规文件。"

        prompt = "## 相关法规规则\n\n"

        for i, doc in enumerate(documents[:5], 1):  # 最多显示5条
            prompt += f"### {i}. {doc.title}\n\n"
            prompt += f"**来源**: {doc.source}\n"
            prompt += f"**相关性**: {doc.relevance_score:.2f}\n"
            prompt += f"**内容摘要**: {doc.content[:200]}...\n\n"

        prompt += "---\n\n"
        prompt += "**数据来源**: 法律世界模型 (Neo4j)\n"
        prompt += f"**检索时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

        return prompt

    def generate_scenario_prompt(self, scenario: ScenarioRule | None) -> str:
        """生成场景规则提示"""
        if not scenario:
            return "## 场景规则\n\n暂无匹配的场景规则。"

        prompt = f"""## 匹配的场景规则

**规则ID**: {scenario.rule_id}
**任务类型**: {scenario.task_type}
**适用阶段**: {scenario.phase}

### 处理规则
"""

        for i, rule in enumerate(scenario.processing_rules, 1):
            prompt += f"{i}. {rule}\n"

        return prompt

    def generate_action_prompt(self, context: LegalContext) -> str:
        """生成行动提示词"""
        if not context:
            return "请提供具体的业务上下文以生成针对性的行动提示词。"

        action_words = {
            "专利申请": ["准备申请文件", "提交申请", "跟踪进度"],
            "专利审查": ["分析审查意见", "准备答复策略", "修改权利要求"],
            "专利无效": ["收集证据", "分析现有技术", "准备无效理由"],
            "专利诉讼": ["准备诉讼材料", "分析侵权行为", "计算赔偿"],
            "专利转让": ["评估价值", "起草合同", "办理备案"],
            "专利维护": ["缴纳年费", "监控期限", "续展保护"],
        }

        if context and context.business_type in action_words:
            actions = action_words.get(
                "通用咨询", ["分析具体情况", "查找相关法规", "制定解决方案", "咨询专业意见"]
            )
        else:
            actions = action_words.get(
                "通用咨询", ["分析具体情况", "查找相关法规", "制定解决方案", "咨询专业意见"]
            )

        prompt = ""
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
        self,
        documents: list[LegalDocument],
        scenario: ScenarioRule | None,
        context: LegalContext,
    ) -> float:
        """计算置信度分数"""
        score = 0.5  # 基础分数

        # 文档匹配度
        if documents:
            score += min(len(documents) / 10, 0.3)

        # 场景规则匹配
        if scenario:
            score += 0.2

        # 业务类型明确度
        if context.business_type != "通用咨询":
            score += 0.1

        # 关键词丰富度
        if context and context.keywords:
            score += min(len(context.keywords) / 5, 0.1)

        return min(score, 1.0)

    def generate_dynamic_prompt(
        self, business_context: str, user_domain: str | None = None, max_rules: int = 10
    ) -> dict[str, Any]:
        """
        生成动态提示词

        Args:
            business_context: 业务上下文描述
            user_domain: 用户领域（可选）
            max_rules: 最大返回规则数

        Returns:
            包含提示词和相关信息的字典
        """
        try:
            # 解析业务上下文
            context = self.parse_business_context(business_context)
            logger.info(f"📋 业务类型: {context.business_type}")

            # 搜索法律文档
            documents = (
                self.search_legal_documents(context, max_rules=max_rules) if context else None
            )

            # 检索场景规则
            scenario = self.retrieve_scenario_rule(context) if context else None
            if scenario:
                logger.info(f"✅ 匹配场景规则: {scenario.rule_id}")

            # 生成各部分提示词
            system_prompt = self.generate_system_prompt(context)
            context_prompt = self.generate_context_prompt(context)
            rules_prompt = self.generate_rules_prompt(documents, context)
            scenario_prompt = self.generate_scenario_prompt(scenario)
            action_prompt = self.generate_action_prompt(context)

            # 组合完整提示词
            full_prompt = f"{system_prompt}\n\n{context_prompt}\n\n{rules_prompt}\n\n{scenario_prompt}\n\n{action_prompt}"

            # 计算置信度
            confidence_score = (
                self.calculate_confidence_score(documents, scenario, context) if context else 0.5
            )

            # 提取数据来源
            sources = [
                {
                    "type": "法律世界模型",
                    "name": "Neo4j法律文档库",
                    "count": len(documents),
                    "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            ]

            # 构建匹配规则信息
            matched_rules = []
            if scenario:
                matched_rules.append(
                    {
                        "rule_id": scenario.rule_id,
                        "task_type": scenario.task_type,
                        "phase": scenario.phase,
                        "processing_rules": scenario.processing_rules,
                    }
                )

            return {
                "prompt": full_prompt,
                "context": {
                    "business_context": business_context,
                    "user_domain": user_domain,
                    "business_type": context.business_type,
                    "matched_rules_count": len(matched_rules),
                },
                "matched_rules": matched_rules,
                "confidence_score": confidence_score,
                "sources": sources,
            }

        except Exception as e:
            logger.error(f"生成动态提示词失败: {e}")
            # 返回基础提示词
            return {
                "prompt": f"""你是Athena平台的专业法律助手。

## 用户咨询
{business_context}

## 服务说明
- 基于法律世界模型34万+法律文档
- 提供专业、准确的法律建议
- 建议咨询专业律师获取具体指导""",
                "context": {
                    "business_context": business_context,
                    "user_domain": user_domain,
                    "error": str(e),
                },
                "matched_rules": [],
                "confidence_score": 0.3,
                "sources": [],
            }


# =============================================================================
# 便捷函数
# =============================================================================

# 全局生成器实例
_generator_instance = None


def get_prompt_generator() -> LegalWorldPromptGenerator:
    """获取提示词生成器实例（单例模式）"""
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = LegalWorldPromptGenerator()
    return _generator_instance


# =============================================================================
# 主函数（测试用）
# =============================================================================


def main():
    """测试提示词生成器"""
    generator = LegalWorldPromptGenerator()

    try:
        # 测试用例
        test_queries = [
            "我有一个发明,想申请专利,需要准备什么材料?",
            "专利审查意见收到了,说我没有创造性,怎么办?",
            "发现有人侵犯我的专利权,如何起诉?",
        ]

        for query in test_queries:
            print("\n" + "=" * 60)
            print(f"用户查询: {query}")
            print("=" * 60)

            result = generator.generate_dynamic_prompt(query)

            print(f"\n置信度: {result['confidence_score']:.2f}")
            print(f"匹配规则数: {len(result['matched_rules'])}")
            print(f"\n生成的提示词:\n{result['prompt'][:500]}...")

    finally:
        generator.close()


if __name__ == "__main__":
    main()
