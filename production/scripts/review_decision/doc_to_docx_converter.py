#!/usr/bin/env python3
"""
DOC转DOCX批量转换工具（带去重功能）
使用LibreOffice进行批量转换

作者: Athena平台团队
创建时间: 2025-12-24
"""

from __future__ import annotations
import logging
import subprocess
import time
from pathlib import Path
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DocToDocxConverter:
    """DOC转DOCX转换器（带去重）"""

    def __init__(self):
        # 使用合并后的目录
        self.decision_dir = Path("/Volumes/AthenaData/语料/专利/专利无效复审决定原文")
        self.converted_dir = Path("/Volumes/AthenaData/语料/专利/专利决定已转换")

        # 检查LibreOffice
        self.libreoffice_path = self._find_libreoffice()

    def _find_libreoffice(self) -> str:
        """查找LibreOffice安装路径"""
        possible_paths = [
            "/Applications/LibreOffice.app/Contents/MacOS/soffice",
            "/Applications/LibreOffice.app/Contents/MacOS/soffice",
            "/Applications/LibreOffice.app/Contents/program/soffice",
        ]

        for path in possible_paths:
            if Path(path).exists():
                logger.info(f"✅ 找到LibreOffice: {path}")
                return path

        logger.warning("⚠️ 未找到LibreOffice，将尝试使用系统默认路径")
        return "soffice"

    def find_doc_files(self, directory: Path) -> list[Path]:
        """查找目录中的DOC文件"""
        doc_files = list(directory.glob("*.doc"))
        # 过滤掉临时文件
        doc_files = [f for f in doc_files if not f.name.startswith("~$")]
        return doc_files

    def convert_single_file(self, doc_path: Path, output_dir: Path) -> tuple[bool, str]:
        """转换单个文件"""
        try:
            # 使用LibreOffice headless模式转换
            cmd = [
                self.libreoffice_path,
                "--headless",
                "--convert-to", "docx",
                "--outdir", str(output_dir),
                str(doc_path)
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60  # 60秒超时
            )

            if result.returncode == 0:
                # 检查输出文件
                output_file = output_dir / f"{doc_path.stem}.docx"
                if output_file.exists():
                    return True, str(output_file)
                else:
                    return False, "输出文件未生成"
            else:
                return False, result.stderr

        except subprocess.TimeoutExpired:
            return False, "转换超时"
        except Exception as e:
            return False, str(e)

    def convert_directory(self, source_dir: Path, batch_size: int = 100) -> Any:
        """批量转换目录（带去重）"""
        doc_files = self.find_doc_files(source_dir)

        if not doc_files:
            logger.info(f"目录中没有DOC文件: {source_dir}")
            return

        logger.info("=" * 70)
        logger.info(f"📂 开始转换: {source_dir.name}")
        logger.info("=" * 70)
        logger.info(f"DOC文件数: {len(doc_files)}")
        logger.info("")

        # 创建输出目录
        output_dir = self.converted_dir / source_dir.name
        output_dir.mkdir(parents=True, exist_ok=True)

        # 统计
        success_count = 0
        failed_count = 0
        skipped_count = 0
        duplicate_count = 0  # 新增：跳过的重复文件
        start_time = time.time()

        # 批量处理
        for i, doc_file in enumerate(doc_files, 1):
            # 去重检查：文件名是否已处理
            file_name_lower = doc_file.stem.lower()
            if file_name_lower in self.processed_names:
                duplicate_count += 1
                if duplicate_count <= 10 or duplicate_count % 1000 == 0:
                    logger.debug(f"跳过重复: {doc_file.name}")
                continue

            # 检查是否已转换
            output_file = output_dir / f"{doc_file.stem}.docx"
            if output_file.exists():
                skipped_count += 1
                # 已转换的文件也要加入已处理集合
                self.processed_names.add(file_name_lower)
                if i % 100 == 0:
                    logger.info(f"进度: {i}/{len(doc_files)} | 跳过已存在: {skipped_count}")
                continue

            # 转换
            success, message = self.convert_single_file(doc_file, output_dir)

            if success:
                success_count += 1
                # 标记文件名已处理
                self.processed_names.add(file_name_lower)
            else:
                failed_count += 1
                logger.warning(f"转换失败: {doc_file.name} - {message}")

            # 进度报告
            if i % 10 == 0:
                elapsed = time.time() - start_time
                speed = i / elapsed if elapsed > 0 else 0
                logger.info(f"进度: {i}/{len(doc_files)} | "
                           f"成功: {success_count} | "
                           f"失败: {failed_count} | "
                           f"跳过已存在: {skipped_count} | "
                           f"跳过重复: {duplicate_count} | "
                           f"速度: {speed:.1f} 文件/秒")

        # 最终报告
        total_time = time.time() - start_time
        logger.info("")
        logger.info("=" * 70)
        logger.info(f"✅ 转换完成: {source_dir.name}")
        logger.info("=" * 70)
        logger.info(f"总计: {len(doc_files)} 文件")
        logger.info(f"成功: {success_count}")
        logger.info(f"失败: {failed_count}")
        logger.info(f"跳过已存在: {skipped_count}")
        logger.info(f"跳过重复: {duplicate_count}")
        logger.info(f"实际处理: {success_count + failed_count}")
        logger.info(f"耗时: {total_time/60:.1f} 分钟")
        logger.info(f"输出目录: {output_dir}")
        logger.info("")

    def convert_all(self) -> Any:
        """转换所有DOC文件（合并目录版）"""
        logger.info("🚀 开始批量DOC转DOCX转换")
        logger.info("📋 数据源: 专利无效复审决定原文（合并后）")
        logger.info("")

        # 转换合并目录中的DOC文件
        self.convert_directory(self.decision_dir)

        logger.info("=" * 70)
        logger.info("🎉 DOC转换完成！")
        logger.info("=" * 70)
        logger.info("💡 提示: 转换后的DOCX文件将添加到处理队列")
        logger.info("=" * 70)


def main() -> None:
    """主函数"""
    converter = DocToDocxConverter()
    converter.convert_all()


if __name__ == "__main__":
    main()
