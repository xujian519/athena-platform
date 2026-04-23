"""
审查意见答复和无效宣告模块

负责审查意见答复和无效宣告请求书的撰写。

主要功能：
- 审查意见答复陈述书撰写
- 无效宣告请求书撰写
- 文档格式化
- 证据分析集成
"""

import json
import logging
from typing import Any

from core.llm.unified_llm_manager import UnifiedLLMManager

logger = logging.getLogger(__name__)


class ResponseModule:
    """
    审查意见答复和无效宣告模块

    专注于：
    - 审查意见答复撰写
    - 无效宣告请求书撰写
    """

    # 审查意见答复系统提示词
    OFFICE_ACTION_SYSTEM_PROMPT = """你是小娜·撰写者，专利文书撰写专家。

你的核心能力：
1. 权利要求书撰写：独立权利要求和从属权利要求
2. 说明书撰写：完整的技术描述
3. 审查意见答复：针对审查意见的陈述
4. 无效宣告请求书：无效理由和证据组织

撰写原则：
- 法律性：符合专利法及实施细则要求
- 技术性：准确描述技术方案
- 逻辑性：层次清晰、逻辑严谨
- 规范性：符合专利局格式要求

输出格式：
- 权利要求书：独立权利要求 + 从属权利要求
- 说明书：发明名称、技术领域、背景技术、发明内容、附图说明、具体实施方式
- 意见陈述书：意见陈述、修改说明、对比分析
"""

    # 无效宣告请求书系统提示词
    INVALIDATION_SYSTEM_PROMPT = """你是小娜·撰写者，专利无效宣告专家。

你的核心能力：
1. 无效理由分析：新颖性、创造性、实用性
2. 证据组织：对比文件筛选和组合
3. 权利要求分析：逐一分析每项权利要求
4. 请求书撰写：符合专利局格式要求

撰写原则：
- 法律性：符合专利法及实施细则要求
- 针对性：针对每项权利要求具体分析
- 证据性：引用证据文件具体内容
- 逻辑性：论证逻辑清晰、层次分明

输出格式：
- 请求书标题
- 目标专利信息
- 无效理由（法条依据）
- 证据列表
- 权利要求分析
- 请求结论
"""

    def __init__(self):
        """初始化响应模块"""
        self.llm_manager = UnifiedLLMManager()
        self.logger = logger

    async def draft_response(
        self, user_input: str, previous_results: dict[str, Any], model: str = "kimi-k2.5"
    ) -> dict[str, Any]:
        """
        撰写审查意见答复

        Args:
            user_input: 用户输入
            previous_results: 前面步骤的结果
            model: 使用的LLM模型

        Returns:
            意见陈述书
        """
        # 获取审查意见和分析结果
        office_action = self._get_office_action(user_input, previous_results)
        analysis = self._get_analysis(previous_results)

        prompt = f"""请撰写审查意见答复陈述书。

审查意见：
{office_action}

分析结果：
{analysis}

要求：
1. 针对每条审查意见进行答复
2. 说明修改内容和理由
3. 与对比文件进行对比
4. 论述专利性和创造性
5. 使用礼貌、专业的语言

输出格式：JSON
{{
    "introduction": "开场陈述",
    "responses": [
        {{
            "issue": "审查意见1",
            "response": "答复内容",
            "amendments": "修改说明",
            "arguments": "论述理由"
        }}
    ],
    "conclusion": "总结陈述"
}}
"""

        response = await self.llm_manager.generate(
            prompt=prompt,
            system_prompt=self.OFFICE_ACTION_SYSTEM_PROMPT,
            model=model,
        )

        # 解析JSON
        try:
            response_doc = json.loads(response)
            return {
                "document_type": "office_action_response",
                "content": response_doc,
                "full_text": self._format_response(response_doc),
            }
        except json.JSONDecodeError:
            self.logger.error("审查意见答复撰写响应解析失败")
            return {
                "document_type": "office_action_response",
                "content": {},
                "full_text": response,  # 返回原始文本
            }

    async def draft_invalidation(
        self, user_input: str, previous_results: dict[str, Any], model: str = "kimi-k2.5"
    ) -> dict[str, Any]:
        """
        撰写无效宣告请求书

        Args:
            user_input: 用户输入
            previous_results: 前面步骤的结果
            model: 使用的LLM模型

        Returns:
            无效宣告请求书
        """
        # 获取目标专利和证据
        target_patent = self._get_target_patent(user_input, previous_results)
        evidence = self._get_evidence(previous_results)
        analysis = self._get_analysis(previous_results)

        prompt = f"""请撰写无效宣告请求书。

目标专利：
{target_patent}

证据：
{evidence}

分析结果：
{analysis}

要求：
1. 明确无效理由（新颖性/创造性/其他）
2. 引用证据文件
3. 逐一分析权利要求
4. 论述无效理由

输出格式：JSON
{{
    "petition_title": "无效宣告请求书",
    "target_patent": "目标专利信息",
    "ground_for_invalidity": "无效理由",
    "evidence_list": ["证据列表"],
    "claim_analysis": [
        {{
            "claim": "权利要求1",
            "evidence": "D1+D2",
            "analysis": "分析",
            "conclusion": "应予无效"
        }}
    ],
    "conclusion": "请求结论"
}}
"""

        response = await self.llm_manager.generate(
            prompt=prompt,
            system_prompt=self.INVALIDATION_SYSTEM_PROMPT,
            model=model,
        )

        # 解析JSON
        try:
            petition = json.loads(response)
            return {
                "document_type": "invalidation_petition",
                "content": petition,
                "full_text": self._format_petition(petition),
            }
        except json.JSONDecodeError:
            self.logger.error("无效宣告请求书撰写响应解析失败")
            return {
                "document_type": "invalidation_petition",
                "content": {},
                "full_text": response,  # 返回原始文本
            }

    def _format_response(self, response: dict[str, Any]) -> str:
        """格式化意见陈述书"""
        full_text = response.get("introduction", "") + "\n\n"
        for resp in response.get("responses", []):
            full_text += f"审查意见：{resp.get('issue', '')}\n"
            full_text += f"答复：{resp.get('response', '')}\n\n"
        full_text += response.get("conclusion", "")
        return full_text

    def _format_petition(self, petition: dict[str, Any]) -> str:
        """格式化无效宣告请求书"""
        parts = []

        if petition.get("petition_title"):
            parts.append(f"# {petition['petition_title']}\n")

        if petition.get("target_patent"):
            parts.append(f"## 目标专利\n{petition['target_patent']}\n")

        if petition.get("ground_for_invalidity"):
            parts.append(f"## 无效理由\n{petition['ground_for_invalidity']}\n")

        if petition.get("evidence_list"):
            parts.append("## 证据列表")
            for i, evidence in enumerate(petition["evidence_list"], 1):
                parts.append(f"{i}. {evidence}")
            parts.append("")

        if petition.get("claim_analysis"):
            parts.append("## 权利要求分析")
            for claim_item in petition["claim_analysis"]:
                parts.append(f"\n### {claim_item.get('claim', '')}")
                if claim_item.get("evidence"):
                    parts.append(f"证据：{claim_item['evidence']}")
                if claim_item.get("analysis"):
                    parts.append(f"分析：{claim_item['analysis']}")
                if claim_item.get("conclusion"):
                    parts.append(f"结论：{claim_item['conclusion']}")

        if petition.get("conclusion"):
            parts.append(f"\n## 请求结论\n{petition['conclusion']}")

        return "\n".join(parts)

    def _get_office_action(self, user_input: str, previous_results: dict[str, Any]) -> str:
        """获取审查意见"""
        return user_input

    def _get_analysis(self, previous_results: dict[str, Any]) -> Any:
        """获取分析结果"""
        if "xiaona_analyzer" in previous_results:
            return previous_results["xiaona_analyzer"]
        return {}

    def _get_target_patent(self, user_input: str, previous_results: dict[str, Any]) -> str:
        """获取目标专利"""
        return user_input

    def _get_evidence(self, previous_results: dict[str, Any]) -> list[Any]:
        """获取证据"""
        if "xiaona_retriever" in previous_results:
            return previous_results["xiaona_retriever"].get("patents", [])
        return []
