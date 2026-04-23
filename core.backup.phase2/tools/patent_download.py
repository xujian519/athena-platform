#!/usr/bin/env python3
"""
统一专利下载工具

仅支持Google Patents PDF下载

Author: Athena平台团队
Created: 2026-04-19
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


class PatentDownloadResult:
    """专利下载结果"""

    def __init__(
        self,
        patent_number: str,
        success: bool,
        file_path: Optional[str] = None,
        file_size: Optional[int] = None,
        error: Optional[str] = None,
        download_time: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.patent_number = patent_number
        self.success = success
        self.file_path = file_path
        self.file_size = file_size
        self.error = error
        self.download_time = download_time
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "patent_number": self.patent_number,
            "success": self.success,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "file_size_mb": round(self.file_size / 1024 / 1024, 2) if self.file_size else None,
            "error": self.error,
            "download_time": self.download_time,
            "metadata": self.metadata
        }


class UnifiedPatentDownloader:
    """
    统一专利下载器

    仅支持Google Patents PDF下载
    """

    def __init__(self):
        self._downloader = None
        self._default_output_dir = "/tmp/patents"

    def _get_downloader(self):
        """获取Google Patents下载器（延迟加载）"""
        if self._downloader is None:
            try:
                import sys
                from pathlib import Path
                # 添加tools到Python路径
                project_root = Path(__file__).parent.parent.parent
                tools_path = project_root / "tools"
                sys.path.insert(0, str(tools_path))

                from google_patents_downloader import GooglePatentsDownloader
                self._downloader = GooglePatentsDownloader()
                logger.info("✅ Google Patents下载器已初始化")
            except Exception as e:
                logger.error(f"❌ Google Patents下载器初始化失败: {e}")
                raise
        return self._downloader

    async def download(
        self,
        patent_numbers: List[str],
        output_dir: Optional[str] = None,
        **kwargs
    ) -> List[PatentDownloadResult]:
        """
        统一下载接口

        Args:
            patent_numbers: 专利号列表
            output_dir: 输出目录（默认/tmp/patents）
            **kwargs: 其他参数

        Returns:
            下载结果列表
        """
        # 设置输出目录
        if output_dir is None:
            output_dir = self._default_output_dir

        # 创建输出目录
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        logger.info(f"📥 开始下载专利: {len(patent_numbers)} 个专利 -> {output_dir}")

        results = []

        for i, patent_number in enumerate(patent_numbers, 1):
            logger.info(f"  [{i}/{len(patent_numbers)}] 下载 {patent_number}...")

            start_time = datetime.now()

            try:
                # 调用Google Patents下载器
                result = await self._download_single(
                    patent_number=patent_number,
                    output_dir=output_dir,
                    **kwargs
                )

                download_time = (datetime.now() - start_time).total_seconds()

                results.append(result)

                if result.success:
                    logger.info(f"    ✅ 成功: {result.file_path} ({result.file_size_mb}MB, {download_time:.1f}s)")
                else:
                    logger.warning(f"    ❌ 失败: {result.error}")

            except Exception as e:
                download_time = (datetime.now() - start_time).total_seconds()
                logger.error(f"    ❌ 异常: {e}")

                results.append(PatentDownloadResult(
                    patent_number=patent_number,
                    success=False,
                    error=str(e),
                    download_time=download_time
                ))

        # 统计
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        total_size = sum(r.file_size or 0 for r in results if r.success)

        logger.info(f"✅ 下载完成: {successful}成功, {failed}失败, 总大小{total_size / 1024 / 1024:.2f}MB")

        return results

    async def _download_single(
        self,
        patent_number: str,
        output_dir: str,
        **kwargs
    ) -> PatentDownloadResult:
        """
        下载单个专利

        Args:
            patent_number: 专利号
            output_dir: 输出目录
            **kwargs: 其他参数

        Returns:
            下载结果
        """
        try:
            downloader = self._get_downloader()

            # 规范化专利号
            patent_number = self._normalize_patent_number(patent_number)

            # 调用下载器
            # 注意：这里需要根据实际的API调整
            start_time = datetime.now()

            result = downloader.download(
                patent_number=patent_number,
                output_dir=output_dir,
                **kwargs
            )

            download_time = (datetime.now() - start_time).total_seconds()

            # 检查结果
            if result and result.get("success"):
                file_path = result.get("file_path")

                # 获取文件大小
                file_size = None
                if file_path and Path(file_path).exists():
                    file_size = Path(file_path).stat().st_size

                return PatentDownloadResult(
                    patent_number=patent_number,
                    success=True,
                    file_path=file_path,
                    file_size=file_size,
                    download_time=download_time,
                    metadata=result
                )
            else:
                error_msg = result.get("error", "下载失败")
                return PatentDownloadResult(
                    patent_number=patent_number,
                    success=False,
                    error=error_msg,
                    download_time=download_time
                )

        except Exception as e:
            logger.error(f"下载 {patent_number} 失败: {e}")
            return PatentDownloadResult(
                patent_number=patent_number,
                success=False,
                error=str(e)
            )

    def _normalize_patent_number(self, patent_number: str) -> str:
        """
        规范化专利号

        Examples:
            "US1234567" -> "US1234567B2"
            "CN123456789A" -> "CN123456789A"
        """
        # 移除空格和特殊字符
        patent_number = patent_number.strip().upper()

        # 移除常见的前缀
        patent_number = patent_number.replace("PATENT", "")
        patent_number = patent_number.replace("NO.", "")

        return patent_number


# ============================================================================
# Tool Handler - 用于工具系统注册
# ============================================================================

async def patent_download_handler(params: Dict[str, Any], context: Dict) -> Dict[str, Any]:
    """
    专利下载工具Handler

    参数:
        patent_numbers: 专利号列表（必需）
            支持单个专利号或专利号列表
        output_dir: 输出目录（可选，默认/tmp/patents）

    返回:
        {
            "success": true,
            "total": 10,
            "successful": 8,
            "failed": 2,
            "total_size_mb": 15.6,
            "results": [...]
        }
    """
    try:
        # 提取参数
        patent_numbers_param = params.get("patent_numbers")
        if not patent_numbers_param:
            return {
                "success": False,
                "error": "缺少必需参数: patent_numbers"
            }

        # 支持单个专利号或列表
        if isinstance(patent_numbers_param, str):
            patent_numbers = [patent_numbers_param]
        else:
            patent_numbers = patent_numbers_param

        output_dir = params.get("output_dir", "/tmp/patents")

        # 创建下载器并执行下载
        downloader = UnifiedPatentDownloader()
        results = await downloader.download(
            patent_numbers=patent_numbers,
            output_dir=output_dir
        )

        # 转换结果为字典格式
        results_dict = [result.to_dict() for result in results]

        # 统计
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        total_size = sum(r.file_size or 0 for r in results if r.success)

        return {
            "success": True,
            "total": len(results),
            "successful": successful,
            "failed": failed,
            "total_size": total_size,
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "output_dir": output_dir,
            "results": results_dict
        }

    except Exception as e:
        logger.error(f"专利下载失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================================
# 便捷函数
# ============================================================================

async def download_patents(
    patent_numbers: List[str],
    output_dir: str = "/tmp/patents"
) -> List[Dict[str, Any]]:
    """
    便捷的专利下载函数

    Args:
        patent_numbers: 专利号列表
        output_dir: 输出目录

    Returns:
        下载结果列表（字典格式）
    """
    downloader = UnifiedPatentDownloader()
    results = await downloader.download(patent_numbers, output_dir)
    return [result.to_dict() for result in results]


async def download_patent(
    patent_number: str,
    output_dir: str = "/tmp/patents"
) -> Dict[str, Any]:
    """
    便捷的单个专利下载函数

    Args:
        patent_number: 专利号
        output_dir: 输出目录

    Returns:
        下载结果（字典格式）
    """
    results = await download_patents([patent_number], output_dir)
    return results[0] if results else {
        "patent_number": patent_number,
        "success": False,
        "error": "下载失败"
    }


# 导出
__all__ = [
    "PatentDownloadResult",
    "UnifiedPatentDownloader",
    "patent_download_handler",
    "download_patents",
    "download_patent",
]
