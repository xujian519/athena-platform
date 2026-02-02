#!/usr/bin/env python3
"""
专利审查意见解析器
Patent Examination Opinion Parser

专门用于解析专利审查过程中的审查意见（非驳回类），包括:
- 说明书相关问题
- 权利要求相关问题
- 具体法律条款引用
- 权利要求编号关联

作者: 小诺·双鱼公主
创建时间: 2025-12-24
版本: v0.1.2 "晨星初现"
"""

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


@dataclass
class LegalArticle:
    """法律条款"""

    law_name: str = ""  # 法律名称 (专利法/专利法实施细则)
    article_number: str = ""  # 条款号 (如"第26条第3款")
    full_reference: str = ""  # 完整引用
    description: str = ""  # 条款描述

    def __str__(self) -> str:
        return f"{self.law_name}{self.article_number}"


@dataclass
class ExaminerInfo:
    """审查员信息"""

    name: str = ""  # 审查员姓名
    phone: str = ""  # 审查员电话
    department: str = ""  # 审查部门
    examiner_id: str = ""  # 审查员编号

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "phone": self.phone,
            "department": self.department,
            "examiner_id": self.examiner_id,
        }


@dataclass
class ExaminationOpinion:
    """
    审查意见

    关联具体权利要求与法律条款
    """

    opinion_type: str = ""  # 意见类型 (说明书问题/权利要求问题等)
    target_claims: list[str] = field(default_factory=list)  # 涉及的权利要求 (如["2", "4-8"])
    legal_articles: list[LegalArticle] = field(default_factory=list)  # 违反的法律条款
    issue_description: str = ""  # 问题描述
    examiner_comment: str = ""  # 审查员意见
    suggestion: str = ""  # 修改建议

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "opinion_type": self.opinion_type,
            "target_claims": self.target_claims,
            "legal_articles": [
                {
                    "law_name": art.law_name,
                    "article_number": art.article_number,
                    "full_reference": art.full_reference,
                    "description": art.description,
                }
                for art in self.legal_articles
            ],
            "issue_description": self.issue_description,
            "examiner_comment": self.examiner_comment,
            "suggestion": self.suggestion,
        }


class ExaminationOpinionParser:
    """
    专利审查意见解析器

    专门处理非驳回类审查意见，精准提取:
    - 具体法律条款
    - 关联的权利要求编号
    - 问题性质和建议
    """

    def __init__(self):
        """初始化解析器"""
        self.name = "专利审查意见解析器"
        self.version = "v0.1.2"

        # 初始化法律条款模式
        self.legal_patterns = self._init_legal_patterns()

        logger.info(f"📜 {self.name} ({self.version}) 初始化完成")

    def _init_legal_patterns(self) -> dict[str, re.Pattern]:
        """
        初始化法律条款识别模式
        """
        return {
            # 说明书相关条款
            "description_26_3": re.compile(
                r"专利法\s*第\s*26\s*条\s*第\s*3\s*款|专利法二十六条第三款"
            ),
            "description_impl_20": re.compile(
                r"专利法实施细则\s*第\s*20\s*条|专利法实施细则第二十条"
            ),
            "description_33": re.compile(r"专利法\s*第\s*33\s*条|专利法第三十三条"),

            # 权利要求相关条款
            "claims_22_2": re.compile(r"专利法\s*第\s*22\s*条\s*第\s*2\s*款"),
            "claims_22_3": re.compile(r"专利法\s*第\s*22\s*条\s*第\s*3\s*款"),
            "claims_22_4": re.compile(r"专利法\s*第\s*22\s*条\s*第\s*4\s*款"),
            "claims_22": re.compile(r"专利法\s*第\s*22\s*条"),
            "claims_26_4": re.compile(
                r"专利法\s*第\s*26\s*条\s*第\s*4\s*款|专利法二十六条第四款"
            ),
            "claims_31_1": re.compile(r"专利法\s*第\s*31\s*条\s*第\s*1\s*款"),
            "claims_33": re.compile(r"专利法\s*第\s*33\s*条"),

            # 实施细则条款
            "impl_22": re.compile(r"专利法实施细则\s*第\s*22\s*条"),
            "impl_23": re.compile(r"专利法实施细则\s*第\s*23\s*条"),
            "impl_24": re.compile(r"专利法实施细则\s*第\s*24\s*条"),
            "impl_25": re.compile(r"专利法实施细则\s*第\s*25\s*条"),
        }

    def parse_examination_opinions(self, text: str) -> list[ExaminationOpinion]:
        """
        解析审查意见

        Args:
            text: 审查意见文本

        Returns:
            审查意见列表
        """
        opinions = []

        # 按段落或章节分割
        sections = self._split_sections(text)

        for section in sections:
            opinion = self._parse_section(section)
            if opinion:
                opinions.append(opinion)

        logger.info(f"📝 解析到 {len(opinions)} 条审查意见")
        return opinions

    def extract_examiner_info(self, text: str) -> ExaminerInfo:
        """
        提取审查员信息

        Args:
            text: 审查意见文本

        Returns:
            审查员信息
        """
        examiner_info = ExaminerInfo()

        # 提取审查员姓名
        name_patterns = [
            r"审查员\s*[:：]?\s*([\u4e00-\u9fa5]{2,4})",
            r"审查人\s*[:：]?\s*([\u4e00-\u9fa5]{2,4})",
            r"([审查员|审查人])\s*(\w{2,10})",
        ]

        for pattern in name_patterns:
            match = re.search(pattern, text)
            if match:
                examiner_info.name = match.group(1).strip()
                break

        # 提取审查员电话
        phone_patterns = [
            r"电话\s*[:：]?\s*(\d{3,4}[-\s]?\d{7,8})",
            r"联系电话\s*[:：]?\s*(\d{3,4}[-\s]?\d{7,8})",
            r"联系方式\s*[:：]?\s*(\d{3,4}[-\s]?\d{7,8})",
            r"(?:tel|phone)\s*[:：]?\s*(\d{3,4}[-\s]?\d{7,8})",
        ]

        for pattern in phone_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                examiner_info.phone = match.group(1).strip()
                break

        # 提取审查部门
        dept_patterns = [
            r"审查部门\s*[:：]?\s*([^\n]{2,20})",
            r"所属部门\s*[:：]?\s*([^\n]{2,20})",
            r"(?:部门|科室)\s*[:：]?\s*([^\n]{2,20})",
        ]

        for pattern in dept_patterns:
            match = re.search(pattern, text)
            if match:
                examiner_info.department = match.group(1).strip()
                break

        # 提取审查员编号
        id_patterns = [
            r"审查员编号\s*[:：]?\s*([A-Z]\d{4,6})",
            r"审查员代码\s*[:：]?\s*([A-Z]\d{4,6})",
            r"工号\s*[:：]?\s*([A-Z]?\d{4,6})",
        ]

        for pattern in id_patterns:
            match = re.search(pattern, text)
            if match:
                examiner_info.examiner_id = match.group(1).strip()
                break

        if examiner_info.name or examiner_info.phone:
            logger.info(f"👤 提取到审查员信息: {examiner_info.name}")

        return examiner_info

    def _split_sections(self, text: str) -> list[str]:
        """
        分割审查意见文本为多个章节

        通常每条意见包含:
        - 权利要求编号
        - 法律条款引用
        - 问题描述
        """
        sections = []

        # 按权利要求分割模式
        # 例如: "权利要求1、2-8", "权利要求1-3", "说明书"
        split_patterns = [
            r"(权利要求\s*\d+[、\-至到至到and及]\s*[\d\-、]+)",
            r"(权利要求\s*\d+)",
            r"(说明书[^，。]{0,50})",
            r"(摘要[^，。]{0,30})",
        ]

        # 首先尝试找到所有分割点
        split_points = []
        for pattern in split_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                split_points.append((match.start(), match.group()))

        # 按位置排序
        split_points.sort(key=lambda x: x[0])

        # 分割文本
        if split_points:
            for i in range(len(split_points)):
                start = split_points[i][0]
                if i < len(split_points) - 1:
                    end = split_points[i + 1][0]
                else:
                    end = len(text)
                section = text[start:end].strip()
                if section:
                    sections.append(section)
        else:
            # 没有找到分割点，返回整个文本
            sections = [text]

        return sections

    def _parse_section(self, section: str) -> ExaminationOpinion | None:
        """
        解析单个审查意见章节

        Args:
            section: 审查意见文本章节

        Returns:
            审查意见对象
        """
        opinion = ExaminationOpinion()

        # 提取涉及的权利要求
        opinion.target_claims = self._extract_target_claims(section)

        # 提取法律条款
        opinion.legal_articles = self._extract_legal_articles(section)

        # 判断意见类型
        opinion.opinion_type = self._determine_opinion_type(section, opinion.legal_articles)

        # 提取问题描述
        opinion.issue_description = self._extract_issue_description(section)

        # 提取审查员意见
        opinion.examiner_comment = self._extract_examiner_comment(section)

        # 提取修改建议
        opinion.suggestion = self._extract_suggestion(section)

        # 只有当有意义的内容时才返回
        if opinion.legal_articles or opinion.target_claims or opinion.issue_description:
            return opinion

        return None

    def _extract_target_claims(self, text: str) -> list[str]:
        """
        提取涉及的权利要求编号

        支持格式:
        - 权利要求1、2-8
        - 权利要求1,2,3
        - 权利要求1至3
        """
        claims = []

        # 多种匹配模式
        patterns = [
            r"权利要求\s*(\d+)[、\-至到至and及]\s*(\d+)[、\-至到至and及]\s*([\d\-、]+)",  # 权利要求1、2-8
            r"权利要求\s*([、\-至到至and及\s\d]+)",  # 权利要求1、2、3
            r"权利要求\s*(\d+)[-至至to](\d+)",  # 权利要求1-3
            r"权利要求\s*(\d+)",  # 权利要求1
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                if match.lastindex >= 3:  # 有范围
                    start = match.group(1)
                    end = match.group(2)
                    additional = match.group(3) if len(match.groups()) >= 3 else ""
                    claims.append(f"{start}-{end}")
                    if additional:
                        # 解析额外的权利要求
                        for num in re.findall(r"\d+", additional):
                            if num not in [start, end]:
                                claims.append(num)
                elif match.lastindex >= 2:  # 有起止
                    start = match.group(1)
                    end = match.group(2)
                    claims.append(f"{start}-{end}")
                else:  # 单个或列表
                    matched_text = match.group(1)
                    # 解析列表中的所有数字
                    for num in re.findall(r"\d+", matched_text):
                        claims.append(num)
                break

        # 去重并保持顺序
        seen = set()
        unique_claims = []
        for claim in claims:
            if claim not in seen:
                seen.add(claim)
                unique_claims.append(claim)

        return unique_claims

    def _extract_legal_articles(self, text: str) -> list[LegalArticle]:
        """
        提取法律条款

        支持的条款:
        - 专利法第26条第3款
        - 专利法第22条第2、3、4款 (新颖性、创造性、实用性)
        - 专利法第26条第4款
        - 专利法第31条第1款
        - 专利法第33条
        - 专利法实施细则第20、22、23、24、25条
        """
        articles = []

        # 定义完整的条款映射
        article_mappings = {
            "description_26_3": {
                "law_name": "专利法",
                "article_number": "第26条第3款",
                "description": "说明书应当清楚、完整地写明发明所要解决的技术问题",
            },
            "description_impl_20": {
                "law_name": "专利法实施细则",
                "article_number": "第20条",
                "description": "说明书应当包含的内容",
            },
            "description_33": {
                "law_name": "专利法",
                "article_number": "第33条",
                "description": "申请人可以对其专利申请文件进行修改",
            },
            "claims_22_2": {
                "law_name": "专利法",
                "article_number": "第22条第2款",
                "description": "新颖性",
            },
            "claims_22_3": {
                "law_name": "专利法",
                "article_number": "第22条第3款",
                "description": "创造性",
            },
            "claims_22_4": {
                "law_name": "专利法",
                "article_number": "第22条第4款",
                "description": "实用性",
            },
            "claims_22": {
                "law_name": "专利法",
                "article_number": "第22条",
                "description": "新颖性、创造性和实用性",
            },
            "claims_26_4": {
                "law_name": "专利法",
                "article_number": "第26条第4款",
                "description": "权利要求应当以说明书为依据",
            },
            "claims_31_1": {
                "law_name": "专利法",
                "article_number": "第31条第1款",
                "description": "单一性",
            },
            "claims_33": {
                "law_name": "专利法",
                "article_number": "第33条",
                "description": "专利申请文件的修改",
            },
            "impl_22": {
                "law_name": "专利法实施细则",
                "article_number": "第22条",
                "description": "权利要求的撰写规定",
            },
            "impl_23": {
                "law_name": "专利法实施细则",
                "article_number": "第23条",
                "description": "权利要求的撰写规定",
            },
            "impl_24": {
                "law_name": "专利法实施细则",
                "article_number": "第24条",
                "description": "权利要求的撰写规定",
            },
            "impl_25": {
                "law_name": "专利法实施细则",
                "article_number": "第25条",
                "description": "权利要求的撰写规定",
            },
        }

        # 查找匹配的条款
        for key, pattern in self.legal_patterns.items():
            if pattern.search(text):
                if key in article_mappings:
                    mapping = article_mappings[key]
                    article = LegalArticle(
                        law_name=mapping["law_name"],
                        article_number=mapping["article_number"],
                        full_reference=f"{mapping['law_name']}{mapping['article_number']}",
                        description=mapping["description"],
                    )
                    articles.append(article)

        return articles

    def _determine_opinion_type(self, text: str, legal_articles: list[LegalArticle]) -> str:
        """
        判断审查意见类型

        Args:
            text: 审查意见文本
            legal_articles: 提取的法律条款

        Returns:
            意见类型
        """
        # 根据法律条款判断类型
        article_nums = [art.article_number for art in legal_articles]

        if any("26条" in num and "第3款" in num for num in article_nums):
            return "说明书内容问题"

        if any("20条" in num for num in article_nums):
            return "说明书撰写问题"

        if any("26条" in num and "第4款" in num for num in article_nums):
            return "权利要求不支持问题"

        if any("22条" in num and ("第2款" in num or "第3款" in num) for num in article_nums):
            return "新颖性/创造性问题"

        if any("31条" in num for num in article_nums):
            return "单一性问题"

        # 根据文本关键词判断
        if "说明书" in text[:50]:
            return "说明书相关问题"

        if "权利要求" in text[:50]:
            return "权利要求相关问题"

        return "其他问题"

    def _extract_issue_description(self, text: str) -> str:
        """提取问题描述"""
        # 查找包含"不符合"、"未"等关键词的句子
        patterns = [
            r"([^。]{10,200})(?:不符合|未|缺少|缺陷|问题)([^。]{10,200})",
            r"([^。]{20,300})。",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0).strip()

        return text[:200] if text else ""

    def _extract_examiner_comment(self, text: str) -> str:
        """提取审查员意见"""
        # 查找审查员观点
        patterns = [
            r"审查员认为[：:]?\s*([^。]{10,300})",
            r"审查员指出[：:]?\s*([^。]{10,300})",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()

        return ""

    def _extract_suggestion(self, text: str) -> str:
        """提取修改建议"""
        patterns = [
            r"建议[：:]?\s*([^。]{10,300})",
            r"应当[：:]?\s*([^。]{10,300})",
            r"修改为[：:]?\s*([^。]{10,200})",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()

        return ""

    def opinions_to_markdown(self, opinions: list[ExaminationOpinion], examiner_info: ExaminerInfo | None = None) -> str:
        """
        将审查意见转换为Markdown格式（用于用户确认）

        Args:
            opinions: 审查意见列表
            examiner_info: 审查员信息（可选）

        Returns:
            Markdown格式的确认模板
        """
        md = []
        md.append("# 📋 专利审查意见解析结果\n")
        md.append("---\n")

        # 审查员信息（新增）
        if examiner_info and (examiner_info.name or examiner_info.phone):
            md.append("## 👤 审查员信息")
            if examiner_info.name:
                md.append(f"- **姓名**: {examiner_info.name}")
            if examiner_info.phone:
                md.append(f"- **电话**: `{examiner_info.phone}`")
            if examiner_info.department:
                md.append(f"- **部门**: {examiner_info.department}")
            if examiner_info.examiner_id:
                md.append(f"- **编号**: {examiner_info.examiner_id}")
            md.append("")

        if not opinions:
            md.append("⚠️ 未提取到审查意见")
            return "\n".join(md)

        md.append(f"## 📝 共解析到 {len(opinions)} 条审查意见\n")

        for i, opinion in enumerate(opinions, 1):
            md.append(f"### 审查意见 {i}\n")

            # 意见类型
            md.append(f"**类型**: {opinion.opinion_type}\n")

            # 涉及的权利要求
            if opinion.target_claims:
                claims_str = "、".join([f"权利要求{c}" for c in opinion.target_claims])
                md.append(f"**涉及权利要求**: {claims_str}\n")

            # 违反的法律条款
            if opinion.legal_articles:
                md.append("**违反条款**:")
                for article in opinion.legal_articles:
                    md.append(f"  - `{article.full_reference}` - {article.description}")
                md.append("")

            # 问题描述
            if opinion.issue_description:
                md.append(f"**问题描述**: {opinion.issue_description}\n")

            # 审查员意见
            if opinion.examiner_comment:
                md.append(f"**审查员意见**: {opinion.examiner_comment}\n")

            # 修改建议
            if opinion.suggestion:
                md.append(f"**修改建议**: {opinion.suggestion}\n")

            md.append("---\n")

        # 确认提示
        md.append("### ✅ 请确认以上审查意见是否准确")
        md.append("")
        md.append("**重点检查**:")
        md.append("- 权利要求编号是否准确")
        md.append("- 法律条款引用是否正确")
        md.append("- 问题描述是否完整")
        md.append("")
        md.append("- 如有错误，请指出需要修改的部分")
        md.append("- 确认无误后，回复 `确认` 或 `confirm` 继续")
        md.append("")

        return "\n".join(md)


# 全局单例
_examination_parser_instance = None


def get_examination_opinion_parser() -> ExaminationOpinionParser:
    """获取审查意见解析器单例"""
    global _examination_parser_instance
    if _examination_parser_instance is None:
        _examination_parser_instance = ExaminationOpinionParser()
    return _examination_parser_instance


# 测试代码
async def main():
    """测试专利审查意见解析器"""

    print("\n" + "=" * 60)
    print("📜 专利审查意见解析器测试")
    print("=" * 60 + "\n")

    parser = get_examination_opinion_parser()

    # 测试文本
    test_text = """
    审查意见通知书

    申请号: 202310000001.X

    经审查，申请存在以下问题:

    1. 权利要求2、4-8不符合专利法第26条第4款规定，权利要求所限定的技术方案中，
       "所述的特征"在说明书中没有明确记载，本领域技术人员根据说明书公开的
       内容无法确定该特征的具体含义。

    2. 说明书不符合专利法第26条第3款的规定，说明书对发明技术方案的描述
       不够清楚、完整，未充分公开发明的技术方案，所属技术领域的技术人员
       无法根据说明书实现该发明。

    3. 权利要求1不符合专利法第22条第2款、第3款规定，不具备新颖性和创造性。
       对比文件D1(CN112345678A)公开了相同的技术方案。
    """

    print("📝 测试: 解析审查意见\n")

    opinions = parser.parse_examination_opinions(test_text)

    print(f"✅ 解析到 {len(opinions)} 条审查意见\n")

    # 输出每条意见
    for i, opinion in enumerate(opinions, 1):
        print(f"意见 {i}:")
        print(f"  类型: {opinion.opinion_type}")
        print(f"  涉及权利要求: {opinion.target_claims}")
        print(f"  法律条款: {[str(art) for art in opinion.legal_articles]}")
        print(f"  问题描述: {opinion.issue_description[:100]}...")
        print()

    # 输出Markdown确认模板
    print("📄 Markdown确认模板:")
    print(parser.opinions_to_markdown(opinions))

    print("\n✅ 测试完成!")


# 入口点
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
