#!/usr/bin/env python3
"""
技能集成：专利下载工具

集成 ~/skills/patent-download/scripts/download_patent.py

Author: Athena平台团队
Created: 2026-04-23
"""

import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
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
        title: Optional[str] = None,
        error: Optional[str] = None,
        download_time: Optional[float] = None
    ):
        self.patent_number = patent_number
        self.success = success
        self.file_path = file_path
        self.file_size = file_size
        self.title = title
        self.error = error
        self.download_time = download_time

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "patent_number": self.patent_number,
            "success": self.success,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "file_size_mb": round(self.file_size / 1024 / 1024, 2) if self.file_size else None,
            "title": self.title,
            "error": self.error,
            "download_time": self.download_time
        }


class SkillsPatentDownloadTool:
    """技能集成：专利下载工具"""

    def __init__(self):
        self.python_path = Path.home() / "小诺工作/.venv/bin/python3"
        self.script_path = Path.home() / "skills/patent-download/scripts/download_patent.py"

    def download_single(
        self,
        patent_number: str,
        output_dir: str = ".",
        open_after_download: bool = False,
        proxy: Optional[str] = None
    ) -> PatentDownloadResult:
        """
        下载单个专利PDF

        Args:
            patent_number: 专利号（如：CN123456789A, US11739244B2）
            output_dir: 输出目录
            open_after_download: 下载后自动打开
            proxy: 代理设置（端口号或地址）

        Returns:
            下载结果
        """
        start_time = datetime.now()

        try:
            # 构建命令
            cmd = [
                str(self.python_path),
                str(self.script_path),
                patent_number,
                "-o", output_dir
            ]

            if open_after_download:
                cmd.append("--open")

            if proxy:
                cmd.extend(["--proxy", proxy])

            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,  # 2分钟超时
                check=True
            )

            # 解析输出
            output = result.stdout

            # 提取文件路径
            file_path = None
            file_size = None
            title = None

            for line in output.split('\n'):
                if '下载成功:' in line:
                    # 提取文件路径
                    parts = line.split('下载成功:')
                    if len(parts) > 1:
                        file_info = parts[1].strip()
                        # 提取路径和大小
                        if '(' in file_info:
                            path_part = file_info.rsplit('(', 1)[0].strip()
                            file_path = path_part
                            # 提取大小
                            size_part = file_info.rsplit('(', 1)[1].rsplit(')', 1)[0]
                            if 'KB' in size_part:
                                file_size = float(size_part.replace('KB', '').strip()) * 1024
                            elif 'MB' in size_part:
                                file_size = float(size_part.replace('MB', '').strip()) * 1024 * 1024

                if '标题:' in line:
                    title = line.split('标题:')[1].strip()

            # 计算下载时间
            download_time = (datetime.now() - start_time).total_seconds()

            # 验证文件存在
            if file_path and Path(file_path).exists():
                return PatentDownloadResult(
                    patent_number=patent_number,
                    success=True,
                    file_path=file_path,
                    file_size=file_size,
                    title=title,
                    download_time=download_time
                )
            else:
                return PatentDownloadResult(
                    patent_number=patent_number,
                    success=False,
                    error="文件未找到或下载失败",
                    download_time=download_time
                )

        except subprocess.TimeoutExpired:
            return PatentDownloadResult(
                patent_number=patent_number,
                success=False,
                error="下载超时（超过2分钟）"
            )
        except subprocess.CalledProcessError as e:
            return PatentDownloadResult(
                patent_number=patent_number,
                success=False,
                error=f"下载失败: {e.stderr}"
            )
        except Exception as e:
            logger.exception(f"专利下载异常: {patent_number}")
            return PatentDownloadResult(
                patent_number=patent_number,
                success=False,
                error=f"下载异常: {str(e)}"
            )

    def download_batch(
        self,
        patent_numbers: List[str],
        output_dir: str = ".",
        proxy: Optional[str] = None
    ) -> List[PatentDownloadResult]:
        """
        批量下载专利PDF

        Args:
            patent_numbers: 专利号列表
            output_dir: 输出目录
            proxy: 代理设置

        Returns:
            下载结果列表
        """
        results = []

        for patent_number in patent_numbers:
            result = self.download_single(
                patent_number=patent_number,
                output_dir=output_dir,
                proxy=proxy
            )
            results.append(result)

        return results

    def download_from_file(
        self,
        file_path: str,
        output_dir: str = ".",
        proxy: Optional[str] = None
    ) -> List[PatentDownloadResult]:
        """
        从文件批量下载专利

        Args:
            file_path: 包含专利号的文件（每行一个）
            output_dir: 输出目录
            proxy: 代理设置

        Returns:
            下载结果列表
        """
        try:
            # 读取专利号列表
            with open(file_path, 'r', encoding='utf-8') as f:
                patent_numbers = [
                    line.strip()
                    for line in f
                    if line.strip() and not line.startswith('#')
                ]

            # 批量下载
            return self.download_batch(patent_numbers, output_dir, proxy)

        except Exception as e:
            logger.exception(f"从文件下载专利异常: {file_path}")
            return []

    def get_patent_info(
        self,
        patent_number: str,
        proxy: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取专利信息（不下载）

        Args:
            patent_number: 专利号
            proxy: 代理设置

        Returns:
            专利信息字典
        """
        try:
            # 构建命令
            cmd = [
                str(self.python_path),
                str(self.script_path),
                patent_number,
                "--info"
            ]

            if proxy:
                cmd.extend(["--proxy", proxy])

            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                check=True
            )

            # 解析输出
            output = result.stdout
            info = {}

            for line in output.split('\n'):
                if '标题:' in line:
                    info['title'] = line.split('标题:')[1].strip()
                elif '专利页:' in line:
                    info['patent_url'] = line.split('专利页:')[1].strip()
                elif 'PDF链接:' in line:
                    info['pdf_url'] = line.split('PDF链接:')[1].strip()

            info['patent_number'] = patent_number
            info['success'] = True

            return info

        except Exception as e:
            logger.exception(f"获取专利信息异常: {patent_number}")
            return {
                "patent_number": patent_number,
                "success": False,
                "error": str(e)
            }


# 创建工具实例
_patent_download_tool = None


def get_patent_download_tool() -> SkillsPatentDownloadTool:
    """获取专利下载工具单例"""
    global _patent_download_tool
    if _patent_download_tool is None:
        _patent_download_tool = SkillsPatentDownloadTool()
    return _patent_download_tool
