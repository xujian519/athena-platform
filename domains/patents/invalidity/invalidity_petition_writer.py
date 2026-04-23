#!/usr/bin/env python3
"""
无效请求书撰写器

撰写专利无效宣告请求书。
"""
import logging
from datetime import datetime
from typing import Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InvalidityPetitionWriter:
    """无效请求书撰写器"""

    def __init__(self):
        """初始化撰写器"""
        logger.info("✅ 无效请求书撰写器初始化成功")

    async def write_petition(
        self,
        target_patent_id: str,
        invalidity_analysis: Any,
        evidence_list: list[Any],
        petitioner_info: dict[str, str]
    ) -> str:
        """
        撰写无效宣告请求书

        Args:
            target_patent_id: 目标专利号
            invalidity_analysis: 无效理由分析
            evidence_list: 证据列表
            petitioner_info: 请求人信息

        Returns:
            请求书文本
        """
        logger.info("📝 开始撰写无效宣告请求书")

        try:
            petition_parts = []

            # 1. 标题和开头
            petition_parts.append(self._write_header(target_patent_id, petitioner_info))

            # 2. 无效理由陈述
            petition_parts.append(self._write_grounds(invalidity_analysis))

            # 3. 证据说明
            petition_parts.append(self._write_evidence(evidence_list))

            # 4. 具体理由
            petition_parts.append(self._write_detailed_reasons(invalidity_analysis, evidence_list))

            # 5. 结尾
            petition_parts.append(self._write_closing())

            return "\n".join(petition_parts)

        except Exception as e:
            logger.error(f"❌ 撰写无效请求书失败: {e}")
            import traceback
            traceback.print_exc()
            return "无效请求书撰写失败"

    def _write_header(self, target_patent_id: str, petitioner_info: dict[str, str]) -> str:
        """撰写开头"""
        return f"""
专利无效宣告请求书

请求人：{petitioner_info.get('name', 'XXX公司')}
地址：{petitioner_info.get('address', 'XXX')}

专利号：{target_patent_id}

根据《专利法》第四十五条及《专利法实施细则》第六十五条的规定，请求人对专利号{target_patent_id}的专利提出无效宣告请求。
"""

    def _write_grounds(self, invalidity_analysis: Any) -> str:
        """撰写无效理由"""
        grounds_text = "\n一、无效理由\n\n"

        if hasattr(invalidity_analysis, 'invalidity_grounds'):
            for i, ground in enumerate(invalidity_analysis.invalidity_grounds, 1):
                grounds_text += f"{i}. {ground.value}问题\n"

        grounds_text += "\n"

        return grounds_text

    def _write_evidence(self, evidence_list: list[Any]) -> str:
        """撰写证据说明"""
        evidence_text = "\n二、证据说明\n\n"

        evidence_text += f"为支持无效理由，请求人提交了{len(evidence_list)}份证据：\n\n"

        for i, evidence in enumerate(evidence_list[:5], 1):
            evidence_text += f"证据{i}：{evidence.patent_id}\n"
            evidence_text += f"      {evidence.title}\n"
            if hasattr(evidence, 'relevance_score'):
                evidence_text += f"      相关度：{evidence.relevance_score:.2f}\n"
            evidence_text += "\n"

        return evidence_text

    def _write_detailed_reasons(
        self,
        invalidity_analysis: Any,
        evidence_list: list[Any]
    ) -> str:
        """撰写具体理由"""
        reasons_text = "\n三、具体理由\n\n"

        reasons_text += "基于上述证据，请求人认为：\n\n"

        # 新颖性理由
        if hasattr(invalidity_analysis, 'invalidity_grounds'):
            from .invalidity_analyzer import InvalidityGround

            if InvalidityGround.NOVELTY in invalidity_analysis.invalidity_grounds:
                reasons_text += "1. 关于新颖性\n"
                reasons_text += "   对比文件1/2公开了权利要求1的技术方案，不具备新颖性。\n\n"

            if InvalidityGround.INVENTIVENESS in invalidity_analysis.invalidity_grounds:
                reasons_text += "2. 关于创造性\n"
                reasons_text += "   权利要求1相对于对比文件1是显而易见的，不具备创造性。\n\n"

        return reasons_text

    def _write_closing(self) -> str:
        """撰写结尾"""
        return """
四、结语

综上所述，该专利不具备专利法规定的新颖性和创造性，应当予以全部无效。

此致
国家知识产权局

请求人：XXX
日期：""" + datetime.now().strftime("%Y年%m月%d日")
