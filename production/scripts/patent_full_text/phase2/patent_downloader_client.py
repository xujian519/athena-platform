#!/usr/bin/env python3
"""
专利下载器客户端
直接使用patent_downloader Python SDK下载专利PDF

作者: Athena平台团队
创建时间: 2025-12-25
"""

from __future__ import annotations
import logging
import sys
from pathlib import Path
from typing import Any

# 添加patent_downloader路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "dev/tools" / "patent_downloader" / "src"))

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PatentDownloaderClient:
    """专利下载器客户端"""

    def __init__(self, output_dir: str = "/Users/xujian/apps/apps/patents/PDF"):
        """
        初始化专利下载器

        Args:
            output_dir: PDF输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        try:
            from patent_downloader import PatentDownloader
            self.downloader = PatentDownloader()
            logger.info("✅ patent_downloader 初始化成功")
            logger.info(f"📁 输出目录: {self.output_dir}")
        except ImportError as e:
            logger.error(f"❌ 无法导入 patent_downloader: {e}")
            logger.error(f"请检查路径: {Path(__file__).parent.parent.parent.parent.parent / 'dev/tools' / 'patent_downloader' / 'src'}")
            raise

    def download_patent(
        self,
        patent_number: str,
        output_dir: str | None = None
    ) -> dict[str, Any]:
        """
        下载单个专利PDF

        Args:
            patent_number: 专利号
            output_dir: 输出目录（可选，默认使用初始化时的目录）

        Returns:
            下载结果字典
        """
        out_dir = output_dir or str(self.output_dir)
        Path(out_dir).mkdir(parents=True, exist_ok=True)

        logger.info(f"📥 开始下载: {patent_number}")

        try:
            success = self.downloader.download_patent(patent_number, out_dir)

            if success:
                file_path = Path(out_dir) / f"{patent_number}.pdf"
                logger.info(f"✅ 下载成功: {file_path}")
                return {
                    "success": True,
                    "patent_number": patent_number,
                    "output_dir": out_dir,
                    "file_path": str(file_path),
                    "file_exists": file_path.exists()
                }
            else:
                logger.warning(f"⚠️ 下载失败: {patent_number}")
                return {
                    "success": False,
                    "patent_number": patent_number,
                    "error": "下载失败，可能专利号不存在或网络问题"
                }

        except Exception as e:
            logger.error(f"❌ 下载出错: {e}")
            return {
                "success": False,
                "patent_number": patent_number,
                "error": str(e)
            }

    def download_patents(
        self,
        patent_numbers: list[str],
        output_dir: str | None = None
    ) -> dict[str, Any]:
        """
        批量下载专利PDF

        Args:
            patent_numbers: 专利号列表
            output_dir: 输出目录（可选）

        Returns:
            批量下载结果
        """
        out_dir = output_dir or str(self.output_dir)

        logger.info(f"📥 批量下载 {len(patent_numbers)} 个专利")

        results = []
        successful = []
        failed = []

        for patent_number in patent_numbers:
            result = self.download_patent(patent_number, out_dir)
            results.append(result)

            if result["success"]:
                successful.append(patent_number)
            else:
                failed.append(patent_number)

        logger.info(f"✅ 批量下载完成: {len(successful)}/{len(patent_numbers)} 成功")

        return {
            "success": True,
            "total": len(patent_numbers),
            "successful": len(successful),
            "failed": len(failed),
            "successful_patents": successful,
            "failed_patents": failed,
            "output_dir": out_dir,
            "reports/reports/results": results
        }

    def get_patent_info(self, patent_number: str) -> dict[str, Any]:
        """
        获取专利元数据信息

        Args:
            patent_number: 专利号

        Returns:
            专利信息字典
        """
        logger.info(f"🔍 查询专利信息: {patent_number}")

        try:
            info = self.downloader.get_patent_info(patent_number)

            result = {
                "success": True,
                "patent_number": patent_number,
                "title": getattr(info, 'title', ''),
                "inventors": list(getattr(info, 'inventors', [])),
                "assignee": getattr(info, 'assignee', ''),
                "publication_date": getattr(info, 'publication_date', ''),
                "abstract": getattr(info, 'abstract', ''),
                "url": getattr(info, 'url', '')
            }

            logger.info(f"✅ 获取成功: {result.get('title', 'N/A')}")
            return result

        except Exception as e:
            logger.error(f"❌ 查询出错: {e}")
            return {
                "success": False,
                "patent_number": patent_number,
                "error": str(e)
            }

    def download_from_file(
        self,
        file_path: str,
        output_dir: str | None = None,
        has_header: bool = True
    ) -> dict[str, Any]:
        """
        从文件读取专利号并批量下载

        Args:
            file_path: 文件路径（TXT或CSV）
            output_dir: 输出目录
            has_header: CSV文件是否有表头

        Returns:
            下载结果
        """
        file_path = Path(file_path)

        if not file_path.exists():
            return {
                "success": False,
                "error": f"文件不存在: {file_path}"
            }

        # 读取专利号
        patent_numbers = []
        suffix = file_path.suffix.lower()

        if suffix == '.csv':
            import csv
            with open(file_path, encoding='utf-8') as f:
                reader = csv.reader(f)
                if has_header:
                    next(reader)  # 跳过表头
                for row in reader:
                    if row:  # 第一列为专利号
                        patent_numbers.append(row[0].strip())

        else:  # TXT 或其他，每行一个专利号
            with open(file_path, encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):  # 忽略空行和注释
                        patent_numbers.append(line)

        logger.info(f"📄 从文件读取 {len(patent_numbers)} 个专利号")

        # 批量下载
        return self.download_patents(patent_numbers, output_dir)


# ==================== 示例使用 ====================

def main() -> None:
    """示例使用"""
    print("=" * 70)
    print("专利下载器客户端示例")
    print("=" * 70)

    client = PatentDownloaderClient()

    # 示例1: 下载单个专利
    print("\n[示例1] 下载单个专利")
    result = client.download_patent("CN112233445A")
    print(f"结果: {result}")

    # 示例2: 获取专利信息
    print("\n[示例2] 获取专利信息")
    info = client.get_patent_info("CN112233445A")
    print(f"标题: {info.get('title', 'N/A')}")
    print(f"申请人: {info.get('assignee', 'N/A')}")

    # 示例3: 批量下载
    print("\n[示例3] 批量下载")
    batch_result = client.download_patents([
        "CN112233445A",
        "US8460931B2"
    ])
    print(f"成功: {batch_result['successful']}/{batch_result['total']}")


if __name__ == "__main__":
    main()
