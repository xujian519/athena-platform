#!/usr/bin/env python3
"""
动态提示词管理器
Dynamic Prompt Manager

基于统一知识图谱的智能提示词生成和管理

作者: 小诺·双鱼公主
创建时间: 2024年12月15日
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging

from .unified_knowledge_graph_service import get_unified_knowledge_service

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

class DynamicPromptManager:
    """动态提示词管理器"""

    def __init__(self):
        """初始化"""
        self.knowledge_service = None
        self.prompt_templates = self._load_prompt_templates()
        self.cache = {}
        self.cache_ttl = 3600  # 缓存1小时

    async def initialize(self):
        """初始化服务"""
        self.knowledge_service = await get_unified_knowledge_service()
        logger.info("动态提示词管理器初始化完成")

    def _load_prompt_templates(self) -> dict[str, str]:
        """加载提示词模板"""
        return {
            "patent_analysis": """
# 专利智能分析报告

## 基础信息
- 专利类型: {patent_type}
- 技术领域: {tech_field}
- 关键词: {keywords}

## 分析维度
{analysis_dimensions}

## 知识库参考
{knowledge_references}

## 结论建议
{conclusions}
""",

            "novelty_assessment": """
# 新颖性审查意见书

## 审查要点
{review_points}

## 相关法条引用
{legal_references}

## 现有技术对比
{prior_art_comparison}

## 结论
{novelty_conclusion}
""",

            "creative_response": """
# 创造性审查回应

## 技术方案分析
{technical_analysis}

## 创造性论证
{creativity_argument}

## 对比文件回应
{response_to_references}

## 补充说明
{additional_explanation}
"""
        }

    async def generate_context_aware_prompts(
        self,
        user_query: str,
        patent_text: str = "",
        context_type: str = "general",
        additional_context: dict[str, Any] = None
    ) -> dict[str, Any]:
        """生成上下文感知的提示词"""

        # 检查缓存
        cache_key = f"{hash(user_query)}_{context_type}"
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            if datetime.now().timestamp() - cached_data['timestamp'] < self.cache_ttl:
                logger.info(f"使用缓存的提示词: {context_type}")
                return cached_data['prompts']

        # 根据上下文类型生成不同的提示词
        if context_type == "patent_review":
            prompts = await self._generate_review_prompts(user_query, patent_text, additional_context)
        elif context_type == "legal_advice":
            prompts = await self._generate_legal_prompts(user_query, patent_text, additional_context)
        elif context_type == "technical_analysis":
            prompts = await self._generate_technical_prompts(user_query, patent_text, additional_context)
        else:
            prompts = await self._generate_general_prompts(user_query, patent_text, additional_context)

        # 更新缓存
        self.cache[cache_key] = {
            'prompts': prompts,
            'timestamp': datetime.now().timestamp()
        }

        return prompts

    async def _generate_review_prompts(
        self,
        query: str,
        patent_text: str,
        context: dict[str, Any] = None
    ) -> dict[str, Any]:
        """生成审查相关的提示词"""

        # 提取关键词
        await self._extract_relevant_keywords(patent_text + " " + query)

        # 获取相关规则
        rules = await self.knowledge_service.get_comprehensive_rules(patent_text)

        # 构建提示词
        review_prompts = {
            "system_role": """
你是一位资深的专利审查员，具有15年以上的专利审查经验。
你精通专利法、实施细则和审查指南，能够准确判断专利的新颖性、创造性和实用性。
请以专业、严谨的态度提供审查意见。
""",
            "task_description": f"""
请对以下专利申请进行审查：

用户查询：{query}

专利内容：{patent_text[:1000]}...
""",
            "analysis_framework": """
## 审查框架

### 1. 形式审查
- 申请文件完整性
- 格式规范性
- 缴费情况

### 2. 实质审查
- 新颖性判断（专利法第22条）
- 创造性判断（专利法第22条）
- 实用性判断（专利法第22条）
- 单一性判断

### 3. 依据知识库的特定规则
""",
            "knowledge_guidance": self._format_rules_as_guidance(rules),
            "output_format": """
## 审查意见格式

### 一、初步结论
- 总体评价
- 可能的授权前景

### 二、具体分析
1. 新颖性分析
2. 创造性分析
3. 实用性分析

### 三、审查建议
- 需要申请人答复的问题
- 建议的修改方向
"""
        }

        return review_prompts

    async def _generate_legal_prompts(
        self,
        query: str,
        patent_text: str,
        context: dict[str, Any] = None
    ) -> dict[str, Any]:
        """生成法律咨询相关的提示词"""

        # 获取相关法律规则
        rules = await self.knowledge_service.get_comprehensive_rules(query + " " + patent_text)

        legal_prompts = {
            "system_role": """
你是一位专业的专利律师，精通专利法律法规和实务操作。
能够为用户提供专业的法律建议和风险提示。
""",
            "case_context": f"""
咨询事项：{query}

相关技术背景：{patent_text[:500]}...
""",
            "legal_basis": """
## 法律依据

基于以下知识库提供专业建议：
""",
            "applicable_rules": self._format_rules_as_legal_basis(rules),
            "risk_assessment": """
## 风险评估要点

1. 侵权风险评估
2. 无效宣告风险
3. 申请策略风险
4. 商业化风险
"""
        }

        return legal_prompts

    async def _generate_technical_prompts(
        self,
        query: str,
        patent_text: str,
        context: dict[str, Any] = None
    ) -> dict[str, Any]:
        """生成技术分析相关的提示词"""

        tech_prompts = {
            "system_role": """
你是一位资深的技术专家和专利分析师，能够深入理解技术创新点，
并评估其技术先进性和产业化潜力。
""",
            "technical_context": f"""
技术问题：{query}

技术方案：{patent_text[:1000]}...
""",
            "analysis_dimensions": """
## 技术分析维度

1. 创新点识别
2. 技术难点分析
3. 技术效果评估
4. 产业化可行性
""",
            "knowledge_references": """
请参考知识库中的相关技术案例和分析方法，
提供专业、准确的技术评估。
"""
        }

        return tech_prompts

    async def _generate_general_prompts(
        self,
        query: str,
        patent_text: str,
        context: dict[str, Any] = None
    ) -> dict[str, Any]:
        """生成通用提示词"""

        general_prompts = {
            "system_role": """
你是Athena工作平台的智能助手，能够整合专利知识图谱、
法律法规库和审查指南，为用户提供全面的专利相关服务。
""",
            "user_query": query,
            "patent_context": patent_text[:500] if patent_text else "",
            "knowledge_integration": """
请基于以下知识库提供专业回答：
- 专利法律法规知识图谱
- 大规模专利案例知识图谱
- 审查指南向量数据库
"""
        }

        return general_prompts

    async def _extract_relevant_keywords(self, text: str) -> list[str]:
        """提取相关关键词"""
        # 这里可以调用知识服务的关键词提取功能
        import jieba.analyse
        keywords = jieba.analyse.extract_tags(text, top_k=15)
        return [kw[0] for kw in keywords]

    def _format_rules_as_guidance(self, rules: dict[str, list[dict]) -> str:
        """将规则格式化为指导内容"""
        guidance = ""

        for category, rule_list in rules.items():
            if rule_list:
                guidance += f"\n### {category.upper()}相关规则\n"
                for rule in rule_list[:3]:  # 限制数量
                    guidance += f"- {rule['title']}: {rule['content'][:100]}...\n"

        return guidance

    def _format_rules_as_legal_basis(self, rules: dict[str, list[dict]) -> str:
        """将规则格式化为法律依据"""
        basis = ""

        # 法规引用
        if 'procedure' in rules:
            basis += "\n### 程序性规定\n"
            for rule in rules['procedure'][:3]:
                basis += f"• {rule['title']}\n"

        # 实体性规定
        if 'novelty' in rules or 'creativity' in rules:
            basis += "\n### 实体性规定\n"
            for rule in (rules.get('novelty', []) + rules.get('creativity', []))[:3]:
                basis += f"• {rule['title']}: {rule['content'][:80]}...\n"

        return basis

    async def save_prompt_session(self, session_id: str, prompts: dict[str, Any]):
        """保存提示词会话"""
        session_data = {
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'prompts': prompts
        }

        # 保存到文件
        output_dir = Path("/Users/xujian/Athena工作平台/data/prompt_sessions")
        output_dir.mkdir(parents=True, exist_ok=True)

        session_file = output_dir / f"session_{session_id}.json"
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)

        logger.info(f"提示词会话已保存: {session_file}")

    async def load_prompt_session(self, session_id: str) -> dict[str, Any | None]:
        """加载提示词会话"""
        session_file = Path(f"/Users/xujian/Athena工作平台/data/prompt_sessions/session_{session_id}.json")

        if session_file.exists():
            with open(session_file, encoding='utf-8') as f:
                return json.load(f)
        return None

# 使用示例
async def example_usage():
    """使用示例"""
    manager = DynamicPromptManager()
    await manager.initialize()

    # 生成审查相关的提示词
    prompts = await manager.generate_context_aware_prompts(
        user_query="这个专利是否具有新颖性？",
        patent_text="本发明涉及一种新材料的制备方法...",
        context_type="patent_review"
    )

    print("生成的提示词:")
    for key, value in prompts.items():
        print(f"\n{key}:")
        print(value[:200] + "...")

if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
