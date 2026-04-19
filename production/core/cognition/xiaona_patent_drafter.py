#!/usr/bin/env python3
from __future__ import annotations
# pyright: ignore
"""
小娜专利撰写助手
Xiaona Patent Drafting Assistant

专业专利申请文件撰写系统,支持权利要求书、说明书、摘要等

作者: 小娜·天秤女神
创建时间: 2025-12-16
版本: v1.0 Patent Writing
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


@dataclass
class PatentDraftingRequest:
    """专利撰写请求"""

    invention_title: str
    technical_field: str
    background_art: str
    invention_summary: str
    brief_description: str
    detailed_description: str
    claims: list[str]
    abstract: str
    drawings: list[dict] = field(default_factory=list)  # type: ignore
    applicant: str = ""
    inventor: str = ""
    priority_date: str | None = None


@dataclass
class PatentDraftingResult:
    """专利撰写结果"""

    title: str
    abstract: str
    claims: list[dict[str, Any]]
    description: str
    drawings_description: str
    application_suggestions: list[str]
    quality_score: float
    drafting_time: float


class XiaonaPatentDrafter:
    """小娜专利撰写助手"""

    def __init__(self):
        self.name = "小娜专利撰写助手"
        self.version = "v1.0 Patent Writing"

        # 专利撰写模板
        self.claim_templates = {
            "independent": "一种{technical_field},其特征在于,包括:{technical_features}。",
            "apparatus": "一种{technical_field}装置,其特征在于,包括:{components}。",
            "method": "一种{technical_field}方法,其特征在于,包括以下步骤:{steps}。",
            "system": "一种{technical_field}系统,其特征在于,包括:{system_components}。",
        }

        # 技术特征连接词
        self.feature_connectors = [
            "所述的{feature},其中,{description}",
            "根据权利要求{number}所述的{feature},其特征在于,{description}",
            "如权利要求{number}所述的{feature},其中,{description}",
        ]

        # 说明书段落模板
        self.description_templates = {
            "technical_field": "本发明涉及{field}技术领域,尤其涉及一种{specific_field}。",
            "background": "{current_situation}。现有技术中,{existing_problems}。因此,需要一种{solution}来解决上述问题。",
            "summary": "本发明的目的在于提供一种{invention},以解决{technical_problem}。",
            "detailed": "为了更清楚地说明本发明实施例的技术方案,下面将对实施例描述中所需要使用的附图作简单地介绍。",
            "beneficial_effects": "与现有技术相比,本发明具有以下有益效果:{effects}。",
        }

    async def initialize(self):
        """初始化撰写助手"""
        logger.info("📝 小娜专利撰写助手初始化...")
        await self._load_patent_templates()
        await self._initialize_claim_analyzer()
        await self._setup_description_generator()
        logger.info("✅ 小娜专利撰写助手初始化完成")

    async def draft_patent_application(
        self, request: PatentDraftingRequest
    ) -> PatentDraftingResult:
        """撰写专利申请文件"""
        logger.info(f"📝 开始撰写专利申请: {request.invention_title}")
        start_time = datetime.now()

        # 1. 优化标题
        optimized_title = await self._optimize_title(
            request.invention_title, request.technical_field
        )

        # 2. 撰写权利要求书
        claims_result = await self._draft_claims(request)

        # 3. 撰写说明书
        description_result = await self._draft_description(request)

        # 4. 撰写摘要
        abstract_result = await self._draft_abstract(request)

        # 5. 生成附图说明
        drawings_result = await self._draft_drawings_description(request.drawings)

        # 6. 生成申请建议
        suggestions = await self._generate_application_suggestions(request, claims_result)

        # 7. 质量评估
        quality_score = await self._assess_drafting_quality(
            {
                "title": optimized_title,
                "claims": claims_result,
                "description": description_result,
                "abstract": abstract_result,
            }
        )

        drafting_time = (datetime.now() - start_time).total_seconds()

        logger.info(f"✅ 专利申请撰写完成,耗时: {drafting_time:.2f}秒")

        return PatentDraftingResult(
            title=optimized_title,
            abstract=abstract_result,
            claims=claims_result,
            description=description_result,
            drawings_description=drawings_result,
            application_suggestions=suggestions,
            quality_score=quality_score,
            drafting_time=drafting_time,
        )

    async def _optimize_title(self, original_title: str, technical_field: str) -> str:
        """优化专利标题"""
        # 移除不必要的修饰词
        title = re.sub(r"(新型|改进型|基于.*的|一种.*的)", "", original_title)

        # 确保标题包含技术特征
        if not any(keyword in title for keyword in ["装置", "方法", "系统", "设备"]):
            if "方法" in technical_field or "步骤" in original_title:
                title += "方法"
            elif "系统" in original_title:
                title += "系统"
            else:
                title += "装置"

        # 确保以"一种"开头
        if not title.startswith("一种"):
            title = "一种" + title

        return title

    async def _draft_claims(self, request: PatentDraftingRequest) -> list[dict[str, Any]]:
        """撰写权利要求书"""
        claims = []

        # 独立权利要求
        independent_claim = await self._draft_independent_claim(request)
        claims.append(independent_claim)

        # 从属权利要求
        for i, claim_text in enumerate(request.claims[1:], 2):  # 跳过第一个,假设是独立权利要求
            dependent_claim = await self._draft_dependent_claim(claim_text, i)
            claims.append(dependent_claim)

        return claims

    async def _draft_independent_claim(self, request: PatentDraftingRequest) -> dict[str, Any]:
        """撰写独立权利要求"""
        # 提取技术特征
        technical_features = await self._extract_technical_features(request.detailed_description)

        # 确定权利要求类型
        claim_type = await self._determine_claim_type(request.technical_field, technical_features)

        # 选择模板
        template = self.claim_templates.get(claim_type, self.claim_templates["independent"])

        # 构建权利要求
        if claim_type == "method":
            steps = await self._extract_method_steps(request.detailed_description)
            features_text = ";".join([f"步骤{i + 1}:{step}" for i, step in enumerate(steps)])
        elif claim_type == "apparatus":
            components = await self._extract_components(request.detailed_description)
            features_text = ";".join(components)
        else:
            features = technical_features.get("features", [])
            features_text = ";".join(features)

        claim_text = template.format(
            technical_field=request.technical_field,
            technical_features=features_text,
            steps=features_text,
            components=features_text,
            system_components=features_text,
        )

        return {
            "type": "independent",
            "number": 1,
            "text": claim_text,
            "category": claim_type,
            "features_count": len(features_text.split(";")),
            "scope": await self._analyze_claim_scope(claim_text),
        }

    async def _draft_dependent_claim(self, claim_text: str, claim_number: int) -> dict[str, Any]:
        """撰写从属权利要求"""
        # 确定所引用的权利要求
        reference_claim = await self._determine_reference_claim(claim_text, claim_number)

        # 构建从属权利要求
        dependent_text = f"根据权利要求{reference_claim}所述的装置,其特征在于,{claim_text}"

        return {
            "type": "dependent",
            "number": claim_number,
            "text": dependent_text,
            "reference_claim": reference_claim,
            "additional_features": await self._extract_additional_features(claim_text),
        }

    async def _draft_description(self, request: PatentDraftingRequest) -> str:
        """撰写说明书"""
        description_parts = []

        # 技术领域
        technical_field = self.description_templates["technical_field"].format(
            field=request.technical_field, specific_field=request.invention_title
        )
        description_parts.append(("技术领域", technical_field))

        # 背景技术
        background = self.description_templates["background"].format(
            current_situation=request.background_art or "现有技术发展迅速",
            existing_problems="存在...问题",
            solution=request.invention_title,
        )
        description_parts.append(("背景技术", background))

        # 发明内容
        summary = self.description_templates["summary"].format(
            invention=request.invention_title, technical_problem="解决现有技术中的不足"
        )
        description_parts.append(("发明内容", summary))

        # 具体实施方式
        detailed = await self._draft_detailed_implementation(request)
        description_parts.append(("具体实施方式", detailed))

        # 有益效果
        effects = await self._extract_beneficial_effects(request.detailed_description)
        beneficial_effects = self.description_templates["beneficial_effects"].format(
            effects=";".join(effects)
        )
        description_parts.append(("有益效果", beneficial_effects))

        # 组合说明书
        full_description = ""
        for title, content in description_parts:
            full_description += f"\n## {title}\n\n{content}\n"

        return full_description

    async def _draft_abstract(self, request: PatentDraftingRequest) -> str:
        """撰写摘要"""
        # 提取核心技术要点
        technical_essence = await self._extract_technical_essence(request.detailed_description)

        # 构建摘要
        abstract_parts = [
            f"本发明公开了{request.invention_title}",
            f"属于{request.technical_field}技术领域",
            f"包括{technical_essence}",
            "具有结构简单、使用方便、效果显著等优点",
        ]

        return "。".join(abstract_parts) + "。"

    async def _draft_drawings_description(self, drawings: list[dict]) -> str:  # type: ignore
        """撰写附图说明"""
        if not drawings:
            return "本申请不包含附图。"

        description = "## 附图说明\n\n"
        for i, drawing in enumerate(drawings):
            description += f"图{i + 1}是{drawing.get('description', f'示意图{i + 1}')}。\n"

            if drawing.get("components"):
                description += "图中:\n"
                for j, component in enumerate(drawing["components"], 1):
                    description += (
                        f"  {j}-{component.get('label', j)}:{component.get('description', '')}\n"
                    )

            description += "\n"

        return description

    async def _generate_application_suggestions(
        self, request: PatentDraftingRequest, claims: list[dict]  # type: ignore
    ) -> list[str]:
        """生成申请建议"""
        suggestions = []

        # 权利要求分析
        independent_claims = [c for c in claims if c["type"] == "independent"]
        dependent_claims = [c for c in claims if c["type"] == "dependent"]

        if len(independent_claims) > 1:
            suggestions.append("建议考虑是否需要多个独立权利要求,确保保护范围适当")

        if len(dependent_claims) < 2:
            suggestions.append("建议增加更多从属权利要求,提供更全面的保护层次")

        # 技术特征分析
        technical_features = await self._extract_technical_features(request.detailed_description)
        if len(technical_features.get("features", [])) < 3:
            suggestions.append("建议详细描述更多技术特征,增强专利的可授权性")

        # 申请策略建议
        suggestions.extend(
            [
                "建议在提交前进行专业的专利检索,确保新颖性",
                "考虑是否需要申请PCT国际专利,扩大保护范围",
                "建议准备审查意见答复策略,提前预判可能的驳回理由",
            ]
        )

        return suggestions

    async def _assess_drafting_quality(self, patent_content: dict) -> float:  # type: ignore
        """评估撰写质量"""
        score = 0.0

        # 标题质量 (10分)
        title = patent_content.get("title", "")
        if title.startswith("一种") and len(title) <= 50:
            score += 10

        # 权利要求质量 (40分)
        claims = patent_content.get("claims", [])
        if claims:
            independent_count = len([c for c in claims if c["type"] == "independent"])
            dependent_count = len([c for c in claims if c["type"] == "dependent"])

            if independent_count == 1:
                score += 15  # 独立权利要求数量合适
            if dependent_count >= 2:
                score += 15  # 有足够的从属权利要求
            if all(len(c["text"]) > 50 for c in claims):
                score += 10  # 权利要求描述充分

        # 说明书质量 (30分)
        description = patent_content.get("description", "")
        required_sections = ["技术领域", "背景技术", "发明内容", "具体实施方式"]
        found_sections = sum(1 for section in required_sections if section in description)
        score += (found_sections / len(required_sections)) * 30

        # 摘要质量 (10分)
        abstract = patent_content.get("abstract", "")
        if 100 <= len(abstract) <= 300:
            score += 10

        # 整体完整性 (10分)
        if all(patent_content.values()):
            score += 10

        return score

    async def _extract_technical_features(self, description: str) -> dict[str, Any]:
        """提取技术特征"""
        # 技术特征关键词
        feature_keywords = [
            "包括",
            "设置",
            "具有",
            "连接",
            "控制",
            "处理",
            "检测",
            "显示",
            "输入",
            "输出",
            "存储",
            "计算",
            "传输",
            "接收",
            "发送",
            "生成",
        ]

        features = []
        sentences = re.split(r"[。!?]", description)

        for sentence in sentences:
            if any(keyword in sentence for keyword in feature_keywords):
                features.append(sentence.strip())

        return {
            "features": features[:10],  # 最多提取10个特征
            "feature_count": len(features),
            "extraction_confidence": 0.85,
        }

    async def _determine_claim_type(self, technical_field: str, features: dict) -> str:  # type: ignore
        """确定权利要求类型"""
        description = " ".join(features.get("features", []))

        if any(word in description for word in ["步骤", "流程", "过程", "方法"]):
            return "method"
        elif any(word in description for word in ["系统", "平台", "架构"]):
            return "system"
        elif any(word in description for word in ["装置", "设备"]):
            return "apparatus"
        else:
            return "independent"

    async def _extract_method_steps(self, description: str) -> list[str]:
        """提取方法步骤"""
        step_patterns = [
            r"步骤[一二三四五六七八九十\d]+[::]\s*([^。,!?;;\n]+)",
            r"第[一二三四五六七八九十\d]+步[::]\s*([^。,!?;;\n]+)",
            r"Step\s*\d+[::]\s*([^。,!?;;\n]+)",
        ]

        steps = []
        for pattern in step_patterns:
            matches = re.findall(pattern, description)
            steps.extend(matches)

        return steps[:10]  # 最多10个步骤

    async def _extract_components(self, description: str) -> list[str]:
        """提取组件"""
        component_patterns = [
            r"([^。,!?;;\n]*(?:模块|单元|部件|元件|装置|设备|机构)[^。,!?;;\n]*)",
            r"([^。,!?;;\n]*(?:处理器|控制器|传感器、存储器、显示器)[^。,!?;;\n]*)",
        ]

        components = []
        for pattern in component_patterns:
            matches = re.findall(pattern, description)
            components.extend(matches)

        # 去重并清理
        unique_components = []
        seen = set()
        for component in components:
            clean_component = component.strip()
            if clean_component and clean_component not in seen:
                unique_components.append(clean_component)
                seen.add(clean_component)

        return unique_components[:10]

    async def _analyze_claim_scope(self, claim_text: str) -> str:
        """分析权利要求保护范围"""
        # 简单的范围分析
        if "包括以下步骤" in claim_text:
            return "方法专利"
        elif "包括" in claim_text and len(claim_text) > 100:
            return "宽范围保护"
        elif "其特征在于" in claim_text:
            return "中等范围保护"
        else:
            return "窄范围保护"

    async def _determine_reference_claim(self, claim_text: str, current_number: int) -> int:
        """确定引用的权利要求"""
        # 简单策略:从属权利要求引用前一个权利要求
        return max(1, current_number - 1)

    async def _extract_additional_features(self, claim_text: str) -> list[str]:
        """提取附加特征"""
        features = re.findall(r"其特征在于,([^。,!?;;\n]+)", claim_text)
        return [feature.strip() for feature in features if feature.strip()]

    async def _draft_detailed_implementation(self, request: PatentDraftingRequest) -> str:
        """撰写具体实施方式"""
        implementation = "下面结合附图和具体实施例对本发明进行详细说明。\n\n"

        # 从详细描述中提取实施方式
        if request.detailed_description:
            implementation += "具体实施例:\n"
            implementation += request.detailed_description
        else:
            implementation += "基于本发明的技术方案,本领域技术人员可以设计出多种具体的实施方式。"

        return implementation

    async def _extract_beneficial_effects(self, description: str) -> list[str]:
        """提取有益效果"""
        effect_patterns = [
            r"([^。,!?;;\n]*(?:提高|增强|改善|减少|降低|避免|防止)[^。,!?;;\n]*)",
            r"([^。,!?;;\n]*(?:优点|有益效果|优势)[^。,!?;;\n]*)",
        ]

        effects = []
        for pattern in effect_patterns:
            matches = re.findall(pattern, description)
            effects.extend(matches)

        return effects[:5]  # 最多5个效果

    async def _extract_technical_essence(self, description: str) -> str:
        """提取技术要点"""
        sentences = re.split(r"[。!?]", description)

        # 找出最核心的技术描述
        core_sentences = []
        for sentence in sentences:
            if any(keyword in sentence for keyword in ["包括", "设置", "具有", "特征"]):
                core_sentences.append(sentence.strip())

        if core_sentences:
            return ";".join(core_sentences[:3])
        else:
            return "创新技术方案"

    async def _load_patent_templates(self):
        """加载专利模板"""
        # 这里可以从文件或数据库加载更多模板
        pass

    async def _initialize_claim_analyzer(self):
        """初始化权利要求分析器"""
        # 初始化权利要求分析模块
        pass

    async def _setup_description_generator(self):
        """设置说明书生成器"""
        # 初始化说明书生成模块
        pass

    async def optimize_claims_hierarchy(self, claims: list[dict]) -> list[dict]:  # type: ignore
        """优化权利要求层次结构"""
        # 重新排序和优化权利要求的引用关系
        optimized_claims = []

        # 独立权利要求在前
        independent_claims = [c for c in claims if c["type"] == "independent"]
        optimized_claims.extend(independent_claims)

        # 从属权利要求按引用关系排序
        dependent_claims = [c for c in claims if c["type"] == "dependent"]
        dependent_claims.sort(key=lambda x: x.get("reference_claim", 999))  # type: ignore
        optimized_claims.extend(dependent_claims)

        # 重新编号
        for i, claim in enumerate(optimized_claims, 1):
            claim["number"] = i

        return optimized_claims


# 导出主类
__all__ = ["PatentDraftingRequest", "PatentDraftingResult", "XiaonaPatentDrafter"]
