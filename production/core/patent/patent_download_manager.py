#!/usr/bin/env python3
"""
专利下载管理器
Patent Download Manager

整合平台多种专利下载工具，提供统一的下载接口

作者: 小诺·双鱼公主
创建时间: 2026-01-24
版本: v0.1.2 "晨星初现"
"""

from __future__ import annotations
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging

logger = setup_logging()


@dataclass
class DownloadResult:
    """下载结果"""

    patent_number: str
    success: bool
    file_path: str = ""
    error: str = ""
    source: str = ""  # "local_downloader", "mcp_server", "database"
    downloaded_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class BatchDownloadResult:
    """批量下载结果"""

    total: int = 0
    successful: int = 0
    failed: int = 0
    results: list[DownloadResult] = field(default_factory=list)

    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str = ""

    def to_markdown(self) -> str:
        """生成Markdown报告"""
        md = []

        md.append("# 📥 专利批量下载报告\n")
        md.append(f"**开始时间**: {self.started_at}\n")
        md.append(f"**完成时间**: {self.completed_at}\n")
        md.append(f"**总计**: {self.total} 个\n")
        md.append(f"**成功**: ✅ {self.successful} 个\n")
        md.append(f"**失败**: ❌ {self.failed} 个\n\n")

        if self.results:
            md.append("## 📊 详细结果\n\n")

            for i, result in enumerate(self.results, 1):
                if result.success:
                    md.append(f"### {i}. {result.patent_number} ✅\n")
                    md.append(f"- **路径**: `{result.file_path}`\n")
                    md.append(f"- **来源**: {result.source}\n")
                else:
                    md.append(f"### {i}. {result.patent_number} ❌\n")
                    md.append(f"- **错误**: {result.error}\n")
                md.append("")

        return "".join(md)


class PatentDownloadManager:
    """
    专利下载管理器

    整合多种下载方式:
    1. 本地patent_downloader SDK
    2. MCP服务器 (patent_downloader)
    3. 数据库导出
    """

    def __init__(self, output_dir: str = "data/patents/PDF"):
        """
        初始化下载管理器

        Args:
            output_dir: PDF输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 初始化下载器
        self._init_downloaders()

        logger.info("📥 专利下载管理器初始化完成")
        logger.info(f"📁 输出目录: {self.output_dir}")

    def _init_downloaders(self):
        """初始化各种下载器"""
        self.downloaders = {
            "local_sdk": None,
            "mcp_server": None,
        }

        # 1. 尝试初始化本地SDK
        try:
            # 添加patent_downloader路径
            pd_path = Path(__file__).parent.parent.parent / "mcp-servers" / "patent_downloader" / "src"
            if pd_path.exists():
                sys.path.insert(0, str(pd_path))
                from patent_downloader import PatentDownloader

                self.downloaders["local_sdk"] = PatentDownloader()
                logger.info("✅ 本地SDK下载器初始化成功")
        except Exception as e:
            logger.debug(f"本地SDK下载器不可用: {e}")

        # 2. 尝试初始化MCP客户端
        try:
            # TODO: 实现MCP客户端
            pass
        except Exception as e:
            logger.debug(f"MCP服务器下载器不可用: {e}")

    def download_patent(self, patent_number: str) -> DownloadResult:
        """
        下载单个专利

        Args:
            patent_number: 专利号

        Returns:
            DownloadResult: 下载结果
        """
        logger.info(f"📥 下载专利: {patent_number}")

        # 清理专利号
        patent_number = patent_number.strip().upper()
        if not patent_number.startswith("CN") and not patent_number.startswith("US"):
            # 尝试添加CN前缀
            patent_number = f"CN{patent_number}"

        # 检查文件是否已存在
        pdf_path = self.output_dir / f"{patent_number}.pdf"
        if pdf_path.exists():
            logger.info(f"✅ 文件已存在: {pdf_path}")
            return DownloadResult(
                patent_number=patent_number,
                success=True,
                file_path=str(pdf_path),
                source="cache",
            )

        # 尝试使用本地SDK下载
        if self.downloaders["local_sdk"]:
            try:
                success = self.downloaders["local_sdk"].download_patent(
                    patent_number, str(self.output_dir)
                )

                if success and pdf_path.exists():
                    logger.info(f"✅ 下载成功: {pdf_path}")
                    return DownloadResult(
                        patent_number=patent_number,
                        success=True,
                        file_path=str(pdf_path),
                        source="local_sdk",
                    )
            except Exception as e:
                logger.warning(f"⚠️ 本地SDK下载失败: {e}")

        # 下载失败
        return DownloadResult(
            patent_number=patent_number,
            success=False,
            error="所有下载方式均失败",
        )

    def download_patents(
        self, patent_numbers: list[str]
    ) -> BatchDownloadResult:
        """
        批量下载专利

        Args:
            patent_numbers: 专利号列表

        Returns:
            BatchDownloadResult: 批量下载结果
        """
        logger.info(f"📥 批量下载 {len(patent_numbers)} 个专利")

        result = BatchDownloadResult(total=len(patent_numbers))

        for patent_number in patent_numbers:
            download_result = self.download_patent(patent_number)
            result.results.append(download_result)

            if download_result.success:
                result.successful += 1
            else:
                result.failed += 1

        result.completed_at = datetime.now().isoformat()

        logger.info(
            f"✅ 批量下载完成: {result.successful}/{result.total} 成功, "
            f"{result.failed} 失败"
        )

        return result

    def check_and_download_missing(
        self,
        recommendations: list[dict[str, Any]],    ) -> BatchDownloadResult:
        """
        检查并下载缺失的专利

        Args:
            recommendations: 下载建议列表 (来自CompletenessReport)

        Returns:
            BatchDownloadResult: 下载结果
        """
        patent_numbers = [rec["patent_number"] for rec in recommendations]

        if not patent_numbers:
            logger.info("✅ 无需下载的专利")
            return BatchDownloadResult(total=0, successful=0, failed=0)

        logger.info(f"📥 开始下载 {len(patent_numbers)} 个缺失专利")

        return self.download_patents(patent_numbers)


# 全局单例
_download_manager_instance: PatentDownloadManager | None = None


def get_patent_download_manager(
    output_dir: str = "data/patents/PDF",
) -> PatentDownloadManager:
    """获取下载管理器单例"""
    global _download_manager_instance
    if _download_manager_instance is None:
        _download_manager_instance = PatentDownloadManager(output_dir=output_dir)
    return _download_manager_instance


# 测试代码
async def main():
    """测试下载管理器"""

    print("\n" + "=" * 70)
    print("📥 专利下载管理器测试")
    print("=" * 70 + "\n")

    manager = get_patent_download_manager()

    # 测试单个下载
    print("📝 测试: 下载单个专利")
    result = manager.download_patent("CN112345678A")
    print(f"结果: {'✅ 成功' if result.success else '❌ 失败'}")
    if result.success:
        print(f"文件: {result.file_path}")
    print()

    # 测试批量下载
    print("📝 测试: 批量下载")
    batch_result = manager.download_patents([
        "CN112345678A",
        "CN112233445A",
    ])

    print(manager.export_result(batch_result, format="markdown"))


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
