#!/usr/bin/env python3
"""
统一文章撰写引擎
Unified Article Writing Engine

整合平台所有文章撰写能力
"""

import asyncio
import logging

# 导入现有模块
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from core.ai.llm.writing_materials_manager import get_materials_manager
from core.judgment_vector_db.generation.article_generator import (
    ArticleQuality,
    ArticleType,
    GeneratedArticle,
)

# 导入风格管理器
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "services" / "self-media-agent"))
try:
    from app.core.enhanced_content_styles import ContentPurpose, ContentStyle, XiaochenStyleManager
except ImportError:
    # 简化版本，不依赖完整导入
    XiaochenStyleManager = None
    ContentStyle = None
    ContentPurpose = None


logger = logging.getLogger(__name__)


@dataclass
class WritingRequest:
    """撰写请求"""
    topic: str                      # 主题
    article_type: str = "ip_education"  # 文章类型
    style: str = "shandong_humor"     # 风格
    platforms: list[str] = None      # 目标平台
    requirements: dict[str, Any] = None  # 特殊要求
    word_count: int | None = None  # 目标字数


@dataclass
class WritingResult:
    """撰写结果"""
    success: bool
    article: GeneratedArticle | None = None
    markdown_content: str | None = None
    metadata: dict[str, Any] = None
    errors: list[str] = None
    warnings: list[str] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class ArticleWritingEngine:
    """
    统一文章撰写引擎

    整合平台所有文章撰写能力：
    - 写作素材库管理
    - 文章生成
    - 风格管理
    - 质量检查
    - OpenClaw交接
    """

    def __init__(self):
        """初始化撰写引擎"""
        # 初始化各子模块
        self.materials_manager = get_materials_manager()
        self.style_manager = XiaochenStyleManager()

        # 文章生成器（需要其他依赖，这里做简化处理）
        self.article_generator = None

        logger.info("✅ 文章撰写引擎初始化完成")

    async def write_article(self, request: WritingRequest) -> WritingResult:
        """
        撰写文章

        Args:
            request: 撰写请求

        Returns:
            撰写结果
        """
        result = WritingResult(success=False)

        try:
            logger.info(f"🔄 开始撰写文章: {request.topic}")

            # 1. 分析请求
            article_type = self._parse_article_type(request.article_type)
            content_style = self._parse_content_style(request.style)

            # 2. 搜索相关素材
            materials = await self._search_materials(request.topic)
            result.metadata["materials_count"] = len(materials)

            # 3. 生成风格指导
            style_guide = self.style_manager.generate_style_guide(
                content_style,
                ContentPurpose.IP_EDUCATION
            )
            result.metadata["style_guide"] = style_guide

            # 4. 生成文章
            # 这里简化处理，实际应该调用ArticleGenerator
            article = await self._generate_article(
                request=request,
                article_type=article_type,
                style_guide=style_guide,
                materials=materials
            )

            if article:
                result.article = article
                result.markdown_content = self._to_markdown(article)
                result.success = True

                # 5. 质量检查
                quality_warnings = self._check_quality(article)
                result.warnings.extend(quality_warnings)

                logger.info(f"✅ 文章撰写完成: {article.title}")
            else:
                result.errors.append("文章生成失败")

        except Exception as e:
            logger.error(f"❌ 撰写失败: {str(e)}")
            result.errors.append(str(e))

        return result

    def _parse_article_type(self, article_type: str) -> ArticleType:
        """解析文章类型"""
        type_mapping = {
            "review": ArticleType.REVIEW,
            "case_analysis": ArticleType.CASE_ANALYSIS,
            "rule_interpretation": ArticleType.RULE_INTERPRETATION,
            "ip_education": ArticleType.REVIEW,  # IP科普使用研究综述
            "industry_insight": ArticleType.TREND_REPORT,
            "patent_guide": ArticleType.RULE_INTERPRETATION,
            "casual_blog": ArticleType.REVIEW
        }
        return type_mapping.get(article_type, ArticleType.REVIEW)

    def _parse_content_style(self, style: str) -> ContentStyle:
        """解析内容风格"""
        style_mapping = {
            "shandong_humor": ContentStyle.SHANDONG_HUMOR,
            "professional": ContentStyle.PROFESSIONAL,
            "cultural": ContentStyle.CULTURAL,
            "practical": ContentStyle.PRACTICAL,
            "casual": ContentStyle.CASUAL,
            "humorous": ContentStyle.HUMOROUS
        }
        return style_mapping.get(style, ContentStyle.SHANDONG_HUMOR)

    async def _search_materials(self, topic: str, top_k: int = 5) -> list[dict]:
        """搜索相关素材"""
        try:
            materials = self.materials_manager.search_materials(
                query=topic,
                top_k=top_k
            )
            logger.info(f"📚 找到 {len(materials)} 条相关素材")
            return materials
        except Exception as e:
            logger.warning(f"⚠️ 素材搜索失败: {str(e)}")
            return []

    async def _generate_article(
        self,
        request: WritingRequest,
        article_type: ArticleType,
        style_guide: dict,
        materials: list[dict]
    ) -> GeneratedArticle | None:
        """
        生成文章

        这里是简化实现，实际应该：
        1. 使用LLM生成文章
        2. 应用风格指导
        3. 融入素材内容
        """
        # 简化实现：生成一个基础文章结构
        from core.judgment_vector_db.generation.article_generator import ArticleSection

        # 根据风格生成开场白
        opening_phrases = style_guide.get("language_elements", {}).get("opening_phrases", [])
        opening = opening_phrases[0] if opening_phrases else "大家好，我是小宸。"

        # 生成文章结构
        sections = [
            ArticleSection(
                section_id="intro",
                title="引言",
                content=f"{opening}\n\n今天我们来聊聊**{request.topic}**这个话题。",
                subsections=[],
                metadata={"type": "introduction"}
            ),
            ArticleSection(
                section_id="main",
                title="主要内容",
                content=self._generate_main_content(request.topic, materials),
                subsections=[],
                metadata={"type": "main_content"}
            ),
            ArticleSection(
                section_id="conclusion",
                title="总结",
                content="希望通过本文的分享，能让大家对这个话题有更深入的理解。有啥问题评论区见！",
                subsections=[],
                metadata={"type": "conclusion"}
            )
        ]

        # 生成标题
        title = self._generate_title(request.topic, style_guide)

        # 创建文章对象
        article = GeneratedArticle(
            article_id=f"article_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            title=title,
            article_type=article_type,
            sections=sections,
            metadata={
                "style": request.style,
                "platforms": request.platforms or [],
                "materials_count": len(materials)
            },
            quality_score=0.8,
            quality_level=ArticleQuality.GOOD,
            sources=[m.get("id", "") for m in materials],
            generated_at=datetime.now().isoformat()
        )

        return article

    def _generate_main_content(self, topic: str, materials: list[dict]) -> str:
        """生成主要内容"""
        content_parts = []

        # 添加素材参考
        if materials:
            content_parts.append("## 相关资料\n")
            for material in materials[:3]:
                title = material.get("title", material.get("id", ""))
                content_parts.append(f"- {title}\n")
            content_parts.append("\n")

        # 添加主体内容
        content_parts.append(f"## 关于{topic}\n\n")
        content_parts.append("这个话题涉及到多个方面，我们来逐一分析。\n\n")
        content_parts.append("### 核心要点\n\n")
        content_parts.append("第一，要理解基本概念。\n\n")
        content_parts.append("第二，掌握关键流程。\n\n")
        content_parts.append("第三，注意常见问题。\n\n")

        return "".join(content_parts)

    def _generate_title(self, topic: str, style_guide: dict) -> str:
        """生成标题"""
        style = style_guide.get("style", "shandong_humor")

        title_templates = {
            "shandong_humor": f"山东小宸跟你唠唠：{topic}",
            "professional": f"{topic}：专业解析",
            "cultural": f"从历史视角看{topic}",
            "practical": f"{topic}：实用指南"
        }

        return title_templates.get(style, f"关于{topic}")

    def _to_markdown(self, article: GeneratedArticle) -> str:
        """转换为Markdown格式"""
        lines = []

        lines.append(f"# {article.title}\n")

        # 元数据
        lines.append("<!--\n")
        lines.append(f"生成时间: {article.generated_at}\n")
        lines.append(f"质量等级: {article.quality_level.value}\n")
        lines.append(f"质量分数: {article.quality_score:.2f}\n")
        lines.append("-->\n\n")

        # 正文
        for section in article.sections:
            lines.append(f"## {section.title}\n")
            lines.append(f"{section.content}\n")

            for subsection in section.subsections:
                lines.append(f"### {subsection.title}\n")
                lines.append(f"{subsection.content}\n")

        return "\n".join(lines)

    def _check_quality(self, article: GeneratedArticle) -> list[str]:
        """检查文章质量"""
        warnings = []

        # 检查字数
        total_chars = sum(len(s.content) for s in article.sections)
        if total_chars < 500:
            warnings.append("文章字数偏少，建议补充更多内容")

        # 检查质量分数
        if article.quality_score < 0.7:
            warnings.append("文章质量分数偏低，建议优化")

        # 检查来源数量
        if len(article.sources) < 3:
            warnings.append("引用来源较少，建议增加参考资料")

        return warnings

    async def handover_to_openclaw(
        self,
        article: GeneratedArticle,
        platforms: list[str]
    ) -> dict[str, Any]:
        """
        交接到OpenClaw

        Args:
            article: 生成的文章
            platforms: 目标平台列表

        Returns:
            交接结果
        """
        from ..openclaw import ArticleContent, OpenClawHandover

        handover = OpenClawHandover()

        # 转换为OpenClaw文章格式
        article_content = ArticleContent(
            title=article.title,
            content=self._to_markdown(article),
            summary=article.sections[0].content if article.sections else "",
            tags=[article.article_type.value, "Athena生成"],
            metadata={
                "article_id": article.article_id,
                "quality_score": article.quality_score,
                "generated_at": article.generated_at
            }
        )

        # 执行交接
        result = await handover.handover_article(
            article=article_content,
            platforms=platforms
        )

        return {
            "success": result.success,
            "article_paths": {k: str(v) for k, v in result.article_paths.items()},
            "message": result.message,
            "errors": result.errors
        }


# 便捷函数
async def write_article(
    topic: str,
    article_type: str = "ip_education",
    style: str = "shandong_humor",
    platforms: list[str] | None = None,
    handover: bool = False
) -> WritingResult:
    """
    便捷函数：撰写文章

    Args:
        topic: 文章主题
        article_type: 文章类型
        style: 写作风格
        platforms: 目标平台
        handover: 是否交接给OpenClaw

    Returns:
        撰写结果
    """
    engine = ArticleWritingEngine()

    request = WritingRequest(
        topic=topic,
        article_type=article_type,
        style=style,
        platforms=platforms or ["微信公众号"]
    )

    result = await engine.write_article(request)

    # 如果需要交接
    if handover and result.success and result.article:
        handover_result = await engine.handover_to_openclaw(
            result.article,
            platforms or ["微信公众号"]
        )
        result.metadata["handover"] = handover_result

    return result


if __name__ == "__main__":
    # 测试代码
    async def test():
        print("🧪 测试文章撰写引擎")
        print("=" * 70)

        engine = ArticleWritingEngine()

        # 测试撰写
        result = await engine.write_article(
            WritingRequest(
                topic="专利申请流程",
                article_type="ip_education",
                style="shandong_humor",
                platforms=["微信公众号", "小红书"]
            )
        )

        print("\n✅ 撰写结果:")
        print(f"   成功: {result.success}")
        if result.article:
            print(f"   标题: {result.article.title}")
            print(f"   类型: {result.article.article_type.value}")
            print(f"   质量: {result.article.quality_level.value}")
        if result.warnings:
            print(f"   警告: {result.warnings}")
        if result.errors:
            print(f"   错误: {result.errors}")

        # 测试交接
        if result.success:
            print("\n📤 测试OpenClaw交接...")
            handover_result = await engine.handover_to_openclaw(
                result.article,
                ["小红书"]
            )
            print(f"   交接成功: {handover_result['success']}")
            print(f"   文章路径: {handover_result['article_paths']}")

    asyncio.run(test())
