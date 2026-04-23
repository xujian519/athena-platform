#!/usr/bin/env python3
"""
OpenClaw内容交接模块
OpenClaw Content Handover Module

实现Athena文章撰写服务与OpenClaw自媒体运营系统的内容交接
"""

import asyncio
import logging
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ArticleContent:
    """文章内容"""
    title: str
    content: str  # Markdown格式
    summary: str
    tags: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ImageContent:
    """配图内容"""
    path: Path
    style: str  # 专业风格、法律风格、生活风格、科技风格
    description: str


@dataclass
class HandoverResult:
    """交接结果"""
    success: bool
    article_paths: dict[str, Path] = field(default_factory=dict)  # platform -> path
    image_paths: list[Path] = field(default_factory=list)
    message: str = ""
    errors: list[str] = field(default_factory=list)


class OpenClawHandover:
    """OpenClaw内容交接器"""

    # OpenClaw自媒体运营路径
    OPENCLAW_BASE_PATH = Path("/Users/xujian/Documents/自媒体运营")

    # 子路径配置
    PATHS = {
        "articles": OPENCLAW_BASE_PATH / "文章草稿",
        "images": OPENCLAW_BASE_PATH / "配图素材",
        "templates": OPENCLAW_BASE_PATH / "模板库",
        "materials": OPENCLAW_BASE_PATH / "素材库",
        "queue": OPENCLAW_BASE_PATH / "发布队列"
    }

    # 平台路径映射
    PLATFORM_PATHS = {
        "微信公众号": "微信公众号",
        "公众号": "微信公众号",
        "weixin": "微信公众号",
        "小红书": "小红书",
        "xiaohongshu": "小红书",
        "知乎": "知乎",
        "zhihu": "知乎",
        "今日头条": "今日头条",
        "toutiao": "今日头条",
        "抖音": "抖音",
        "douyin": "抖音",
        "快手": "快手",
        "kuaishou": "快手",
        "微博": "微博",
        "weibo": "微博"
    }

    # 配图风格映射
    IMAGE_STYLE_PATHS = {
        "专业风格": "专业风格",
        "professional": "专业风格",
        "法律风格": "法律风格",
        "legal": "法律风格",
        "生活风格": "生活风格",
        "lifestyle": "生活风格",
        "科技风格": "科技风格",
        "tech": "科技风格"
    }

    def __init__(self, base_path: Path | None = None):
        """
        初始化OpenClaw内容交接器

        Args:
            base_path: OpenClaw基础路径（默认为标准路径）
        """
        if base_path:
            self.OPENCLAW_BASE_PATH = base_path
            self.PATHS = {
                "articles": base_path / "文章草稿",
                "images": base_path / "配图素材",
                "templates": base_path / "模板库",
                "materials": base_path / "素材库",
                "queue": base_path / "发布队列"
            }

        # 验证路径
        self._validate_paths()

    def _validate_paths(self):
        """验证并创建必要的路径"""
        for _key, path in self.PATHS.items():
            if not path.exists():
                logger.warning(f"路径不存在，将自动创建: {path}")
                path.mkdir(parents=True, exist_ok=True)

        # 为每个平台创建子目录
        articles_path = self.PATHS["articles"]
        for platform_name in set(self.PLATFORM_PATHS.values()):
            platform_path = articles_path / platform_name
            if not platform_path.exists():
                platform_path.mkdir(parents=True, exist_ok=True)

        # 为每个配图风格创建子目录
        images_path = self.PATHS["images"]
        for style_name in set(self.IMAGE_STYLE_PATHS.values()):
            style_path = images_path / style_name
            if not style_path.exists():
                style_path.mkdir(parents=True, exist_ok=True)

    def _normalize_platform(self, platform: str) -> str:
        """标准化平台名称"""
        return self.PLATFORM_PATHS.get(platform, platform)

    def _normalize_image_style(self, style: str) -> str:
        """标准化配图风格名称"""
        return self.IMAGE_STYLE_PATHS.get(style, style)

    def _generate_filename(
        self,
        title: str,
        platform: str,
        date: datetime | None = None
    ) -> str:
        """
        生成文件名

        Args:
            title: 文章标题
            platform: 平台名称
            date: 日期（默认为当前日期）

        Returns:
            文件名
        """
        if date is None:
            date = datetime.now()

        # 格式：YYYY-MM-DD-标题.md
        date_str = date.strftime("%Y-%m-%d")

        # 清理标题中的特殊字符
        clean_title = title
        for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
            clean_title = clean_title.replace(char, '-')

        # 限制长度
        if len(clean_title) > 50:
            clean_title = clean_title[:50]

        return f"{date_str}-{clean_title}.md"

    async def handover_article(
        self,
        article: ArticleContent,
        platforms: list[str],
        images: list[ImageContent] | None = None,
        date: datetime | None = None
    ) -> HandoverResult:
        """
        交接文章到OpenClaw

        Args:
            article: 文章内容
            platforms: 目标平台列表
            images: 配图列表（可选）
            date: 文章日期（可选）

        Returns:
            交接结果
        """
        result = HandoverResult(success=False)

        try:
            # 1. 保存文章到各平台目录
            for platform in platforms:
                normalized_platform = self._normalize_platform(platform)
                if not normalized_platform:
                    result.errors.append(f"不支持的平台: {platform}")
                    continue

                # 生成文件名
                filename = self._generate_filename(
                    article.title,
                    normalized_platform,
                    date
                )

                # 构建完整路径
                article_path = self.PATHS["articles"] / normalized_platform / filename

                # 生成Markdown内容
                markdown_content = self._generate_markdown(article, platform)

                # 写入文件
                article_path.write_text(markdown_content, encoding='utf-8')
                result.article_paths[platform] = article_path

                logger.info(f"✅ 文章已保存: {article_path}")

            # 2. 保存配图
            if images:
                for image in images:
                    normalized_style = self._normalize_image_style(image.style)
                    if not normalized_style:
                        result.errors.append(f"不支持的配图风格: {image.style}")
                        continue

                    # 复制配图到对应风格目录
                    style_path = self.PATHS["images"] / normalized_style

                    # 生成配图文件名
                    image_filename = f"{article.title}-{image.path.name}"
                    clean_image_filename = self._sanitize_filename(image_filename)
                    target_path = style_path / clean_image_filename

                    # 复制文件
                    if image.path.exists():
                        shutil.copy2(image.path, target_path)
                        result.image_paths.append(target_path)
                        logger.info(f"✅ 配图已保存: {target_path}")
                    else:
                        result.errors.append(f"配图文件不存在: {image.path}")

            # 3. 更新发布队列
            await self._update_publish_queue(article, platforms, result.article_paths)

            result.success = len(result.errors) == 0
            result.message = f"成功交接到 {len(result.article_paths)} 个平台"

            return result

        except Exception as e:
            logger.error(f"❌ 交接失败: {str(e)}")
            result.errors.append(str(e))
            return result

    def _generate_markdown(self, article: ArticleContent, platform: str) -> str:
        """
        生成Markdown内容

        Args:
            article: 文章内容
            platform: 目标平台

        Returns:
            Markdown格式的内容
        """
        lines = []

        # 标题
        lines.append(f"# {article.title}\n")

        # 元数据
        lines.append("<!--")
        lines.append(f"生成时间: {datetime.now().isoformat()}")
        lines.append(f"目标平台: {platform}")
        lines.append(f"标签: {', '.join(article.tags)}")
        lines.append("-->\n")

        # 摘要
        if article.summary:
            lines.append(f"> {article.summary}\n")

        # 正文内容
        lines.append(article.content)

        # 标签（作为脚注）
        if article.tags:
            lines.append("\n---\n")
            lines.append(f"**标签**: {', '.join(article.tags)}\n")

        return "\n".join(lines)

    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名中的非法字符"""
        for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
            filename = filename.replace(char, '-')
        return filename

    async def _update_publish_queue(
        self,
        article: ArticleContent,
        platforms: list[str],
        article_paths: dict[str, Path]
    ):
        """
        更新发布队列

        Args:
            article: 文章内容
            platforms: 平台列表
            article_paths: 文章路径映射
        """
        queue_file = self.PATHS["queue"] / "待发布.md"

        # 准备新条目
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        new_entry = f"\n## {article.title}\n\n"
        new_entry += f"- **时间**: {timestamp}\n"
        new_entry += f"- **平台**: {', '.join(platforms)}\n"
        new_entry += "- **状态**: 待发布\n"
        new_entry += "- **文件路径**:\n"

        for platform, path in article_paths.items():
            new_entry += f"  - {platform}: `{path}`\n"

        new_entry += "\n---\n"

        # 追加到待发布文件
        try:
            with open(queue_file, 'a', encoding='utf-8') as f:
                f.write(new_entry)
            logger.info(f"✅ 已更新发布队列: {queue_file}")
        except Exception as e:
            logger.error(f"❌ 更新发布队列失败: {str(e)}")

    async def batch_handover(
        self,
        articles: list[ArticleContent],
        platforms: list[str],
        generate_images: bool = False
    ) -> list[HandoverResult]:
        """
        批量交接文章

        Args:
            articles: 文章列表
            platforms: 目标平台列表
            generate_images: 是否生成配图

        Returns:
            交接结果列表
        """
        results = []

        for article in articles:
            # 如果需要生成配图，这里可以调用配图生成模块
            images = None
            if generate_images:
                # TODO: 集成配图生成
                pass

            result = await self.handover_article(
                article=article,
                platforms=platforms,
                images=images
            )
            results.append(result)

        return results

    def get_handover_status(self) -> dict[str, Any]:
        """
        获取交接状态

        Returns:
            状态信息
        """
        status = {
            "openclaw_path": str(self.OPENCLAW_BASE_PATH),
            "paths": {k: str(v) for k, v in self.PATHS.items()},
            "platforms": list(set(self.PLATFORM_PATHS.values())),
            "image_styles": list(set(self.IMAGE_STYLE_PATHS.values())),
            "available": self.OPENCLAW_BASE_PATH.exists()
        }

        # 统计各平台文章数量
        article_counts = {}
        articles_path = self.PATHS["articles"]
        if articles_path.exists():
            for platform_dir in articles_path.iterdir():
                if platform_dir.is_dir():
                    count = len(list(platform_dir.glob("*.md")))
                    article_counts[platform_dir.name] = count

        status["article_counts"] = article_counts

        return status


# 便捷函数
async def handover_to_openclaw(
    title: str,
    content: str,
    platforms: list[str],
    summary: str = "",
    tags: list[str] | None = None,
    images: list[Path] | None = None
) -> HandoverResult:
    """
    便捷函数：交接文章到OpenClaw

    Args:
        title: 文章标题
        content: 文章内容（Markdown格式）
        platforms: 目标平台列表
        summary: 文章摘要
        tags: 文章标签
        images: 配图路径列表

    Returns:
        交接结果
    """
    handover = OpenClawHandover()

    article = ArticleContent(
        title=title,
        content=content,
        summary=summary,
        tags=tags or [],
        metadata={"handover_time": datetime.now().isoformat()}
    )

    # 转换图片路径为ImageContent对象
    image_contents = None
    if images:
        image_contents = [
            ImageContent(path=img, style="专业风格", description="")
            for img in images
        ]

    return await handover.handover_article(
        article=article,
        platforms=platforms,
        images=image_contents
    )


if __name__ == "__main__":
    # 测试代码
    async def test():
        print("🧪 测试OpenClaw内容交接")
        print("=" * 70)

        handover = OpenClawHandover()

        # 测试状态获取
        status = handover.get_handover_status()
        print("\n📊 交接状态:")
        print(f"   OpenClaw路径: {status['openclaw_path']}")
        print(f"   可用状态: {status['available']}")
        print(f"   支持平台: {', '.join(status['platforms'])}")
        print(f"   配图风格: {', '.join(status['image_styles'])}")
        print(f"   文章统计: {status['article_counts']}")

        # 测试文章交接
        print("\n📝 测试文章交接...")

        test_article = ArticleContent(
            title="专利申请流程详解",
            content="""## 引言

专利申请是保护创新成果的重要手段。本文将详细介绍专利申请的完整流程。

## 专利申请流程

### 1. 专利检索

在申请之前，需要进行充分的专利检索，确保创新性。

### 2. 准备申请材料

包括请求书、说明书、权利要求书等。

### 3. 提交申请

向国家知识产权局提交申请。

### 4. 审查

经过初步审查和实质审查。

### 5. 授权

审查通过后，授予专利权。

## 结语

专利申请需要专业知识和经验，建议寻求专业代理机构的帮助。
""",
            summary="本文详细介绍专利申请的完整流程，包括检索、准备材料、提交申请、审查和授权等步骤。",
            tags=["专利", "知识产权", "专利申请", "IP科普"],
            metadata={"author": "小宸", "article_type": "ip_education"}
        )

        result = await handover.handover_article(
            article=test_article,
            platforms=["微信公众号", "小红书"]
        )

        print("\n✅ 交接结果:")
        print(f"   成功: {result.success}")
        print(f"   消息: {result.message}")
        print(f"   文章路径: {result.article_paths}")
        if result.errors:
            print(f"   错误: {result.errors}")

    asyncio.run(test())
