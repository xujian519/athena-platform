#!/usr/bin/env python3
"""
简化版文章撰写引擎（用于快速测试）
Simplified Article Writing Engine for Testing
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class WritingRequest:
    """撰写请求"""
    topic: str
    article_type: str = "ip_education"
    style: str = "shandong_humor"
    platforms: List[str] = None
    requirements: Dict[str, Any] = None
    word_count: Optional[int] = None


@dataclass
class WritingResult:
    """撰写结果"""
    success: bool
    article: Optional[Any] = None
    markdown_content: Optional[str] = None
    metadata: Dict[str, Any] = None
    errors: List[str] = None
    warnings: List[str] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class SimpleArticleWritingEngine:
    """简化版文章撰写引擎"""

    def __init__(self):
        logger.info("✅ 简化版文章撰写引擎初始化完成")

    async def write_article(self, request: WritingRequest) -> WritingResult:
        """撰写文章"""
        result = WritingResult(success=False)

        try:
            logger.info(f"🔄 开始撰写文章: {request.topic}")

            # 生成文章
            article = self._generate_simple_article(request)

            result.article = article
            result.markdown_content = self._to_markdown(article)
            result.success = True

            logger.info(f"✅ 文章撰写完成: {article['title']}")

        except Exception as e:
            logger.error(f"❌ 撰写失败: {str(e)}")
            result.errors.append(str(e))

        return result

    def _generate_simple_article(self, request: WritingRequest) -> Dict[str, Any]:
        """生成简单文章"""
        # 根据风格生成标题
        title_templates = {
            "shandong_humor": f"山东小宸跟你唠唠：{request.topic}",
            "professional": f"{request.topic}：专业解析",
            "cultural": f"从历史视角看{request.topic}",
            "practical": f"{request.topic}：实用指南"
        }
        title = title_templates.get(request.style, f"关于{request.topic}")

        # 根据风格生成开场白
        opening_phrases = {
            "shandong_humor": "哎哟，老铁们！今天咱聊个有意思的...",
            "professional": "大家好，我是小宸。今天我们来探讨...",
            "cultural": "说起这个话题，我想起古人云...",
            "practical": "今天给大家分享一些实用的东西..."
        }
        opening = opening_phrases.get(request.style, "大家好！")

        # 生成文章内容
        content = f"""{opening}

## 关于{request.topic}

这个话题涉及到多个方面，我们来逐一分析。

### 核心要点

第一，要理解基本概念。

第二，掌握关键流程。

第三，注意常见问题。

### 实用建议

希望以上分享对大家有所帮助。

## 总结

**小宸提醒**：有问题评论区见！觉得有用记得点赞关注！

---

*本文由Athena文章撰写服务生成*
*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""

        return {
            "article_id": f"article_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "title": title,
            "content": content,
            "article_type": request.article_type,
            "style": request.style,
            "platforms": request.platforms or ["微信公众号"],
            "generated_at": datetime.now().isoformat()
        }

    def _to_markdown(self, article: Dict[str, Any]) -> str:
        """转换为Markdown格式"""
        lines = []

        lines.append(f"# {article['title']}\n")
        lines.append("<!--\n")
        lines.append(f"生成时间: {article['generated_at']}\n")
        lines.append(f"文章类型: {article['article_type']}\n")
        lines.append(f"写作风格: {article['style']}\n")
        lines.append("-->\n\n")
        lines.append(article['content'])

        return "\n".join(lines)


# 便捷函数
async def write_article_simple(
    topic: str,
    article_type: str = "ip_education",
    style: str = "shandong_humor",
    platforms: Optional[List[str]] = None
) -> WritingResult:
    """便捷函数：撰写文章"""
    engine = SimpleArticleWritingEngine()

    request = WritingRequest(
        topic=topic,
        article_type=article_type,
        style=style,
        platforms=platforms or ["微信公众号"]
    )

    return await engine.write_article(request)


if __name__ == "__main__":
    # 测试代码
    async def test():
        print("🧪 测试简化版文章撰写引擎")
        print("=" * 70)

        engine = SimpleArticleWritingEngine()

        result = await engine.write_article(
            WritingRequest(
                topic="专利无效宣告程序",
                article_type="ip_education",
                style="shandong_humor",
                platforms=["小红书"]
            )
        )

        print(f"\n✅ 撰写结果:")
        print(f"   成功: {result.success}")
        if result.article:
            print(f"   标题: {result.article['title']}")
        if result.markdown_content:
            print(f"\n📝 文章内容预览:")
            print(result.markdown_content[:500] + "...")
        if result.errors:
            print(f"   错误: {result.errors}")

    asyncio.run(test())
