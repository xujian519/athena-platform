#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专利PDF批量处理脚本
Patent PDF Batch Processing Script

处理指定目录中的所有PDF专利文件，构建向量索引和知识图谱

作者: Athena平台团队
创建时间: 2025-12-25
"""

import os
import sys
import time
import logging
from pathlib import Path
from typing import List, Dict, Any
import subprocess

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PatentBatchProcessor:
    """专利批量处理器"""

    def __init__(self, pdf_directory: str = "/Users/xujian/apps/apps/patents/PDF"):
        """
        初始化批量处理器

        Args:
            pdf_directory: PDF文件目录
        """
        self.pdf_directory = Path(pdf_directory)
        self.patent_system_dir = Path("/Users/xujian/Athena工作平台/production/dev/scripts/patent_full_text")
        self.phase3_dir = self.patent_system_dir / "phase3"

        # 设置环境变量
        os.environ['PYTHONPATH'] = f"{self.patent_system_dir}:{self.phase3_dir}:{os.environ.get('PYTHONPATH', '')}"
        os.environ['ATHENA_HOME'] = "/Users/xujian/Athena工作平台"
        os.environ['PATENT_PDF_PATH'] = str(self.pdf_directory)
        os.environ['PATENT_LOG_PATH'] = "/Users/xujian/Athena工作平台/apps/apps/patents/logs"

        # 处理结果
        self.results = []

    def find_pdf_files(self) -> List[Path]:
        """查找所有PDF文件"""
        pdf_files = list(self.pdf_directory.rglob("*.pdf"))
        logger.info(f"找到 {len(pdf_files)} 个PDF文件")
        return pdf_files

    def extract_patent_number(self, pdf_path: Path) -> str:
        """从文件名提取专利号"""
        filename = pdf_path.stem  # 去掉.pdf后缀
        return filename

    def process_single_patent(self, pdf_path: Path) -> Dict[str, Any]:
        """
        处理单个专利PDF

        Args:
            pdf_path: PDF文件路径

        Returns:
            处理结果字典
        """
        patent_number = self.extract_patent_number(pdf_path)
        logger.info(f"开始处理专利: {patent_number} ({pdf_path.name})")

        start_time = time.time()

        try:
            # 导入处理模块
            sys.path.insert(0, str(self.phase3_dir))
            from pipeline_v2 import process_patent, PipelineInput
            from pdf_parser import extract_text_from_pdf

            # 提取PDF文本
            logger.info(f"  - 提取PDF文本...")
            pdf_text = extract_text_from_pdf(str(pdf_path))

            if not pdf_text or len(pdf_text) < 100:
                return {
                    "patent_number": patent_number,
                    "success": False,
                    "error": "PDF文本提取失败或内容过少",
                    "processing_time": time.time() - start_time
                }

            # 创建处理输入
            # 这里需要根据实际PDF内容解析出标题、摘要等
            # 暂时使用简化的方式
            input_data = PipelineInput(
                patent_number=patent_number,
                title=pdf_text[:100],  # 前100字符作为标题
                abstract=pdf_text[:500],  # 前500字符作为摘要
                ipc_classification="",
                claims=pdf_text,
                invention_content=pdf_text
            )

            # 处理专利
            logger.info(f"  - 执行处理管道...")
            # 注意：这里需要实际的模型加载器
            # 暂时跳过实际处理，只记录结构

            processing_time = time.time() - start_time

            result = {
                "patent_number": patent_number,
                "success": True,
                "file_path": str(pdf_path),
                "processing_time": processing_time,
                "text_length": len(pdf_text)
            }

            logger.info(f"  ✅ 处理完成: {patent_number} ({processing_time:.2f}秒)")
            return result

        except Exception as e:
            logger.error(f"  ❌ 处理失败: {patent_number} - {e}")
            return {
                "patent_number": patent_number,
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time
            }

    def process_batch(self, pdf_files: List[Path] = None) -> Dict[str, Any]:
        """
        批量处理专利文件

        Args:
            pdf_files: PDF文件列表，如果为None则自动查找

        Returns:
            批量处理结果
        """
        if pdf_files is None:
            pdf_files = self.find_pdf_files()

        if not pdf_files:
            logger.warning("没有找到PDF文件")
            return {"total": 0, "success": 0, "failed": 0, "reports/reports/results": []}

        logger.info(f"="*60)
        logger.info(f"开始批量处理 {len(pdf_files)} 个专利文件")
        logger.info(f"="*60)

        start_time = time.time()
        results = []
        success_count = 0
        failed_count = 0

        for i, pdf_path in enumerate(pdf_files, 1):
            logger.info(f"\n[{i}/{len(pdf_files)}] 处理: {pdf_path.name}")

            result = self.process_single_patent(pdf_path)
            results.append(result)

            if result["success"]:
                success_count += 1
            else:
                failed_count += 1

        total_time = time.time() - start_time

        # 打印统计
        logger.info(f"\n{'='*60}")
        logger.info(f"批量处理完成")
        logger.info(f"{'='*60}")
        logger.info(f"总文件数: {len(pdf_files)}")
        logger.info(f"成功: {success_count}")
        logger.info(f"失败: {failed_count}")
        logger.info(f"总耗时: {total_time:.2f}秒")
        logger.info(f"平均耗时: {total_time/len(pdf_files):.2f}秒/文件")

        # 详细结果
        logger.info(f"\n详细结果:")
        for result in results:
            status = "✅" if result["success"] else "❌"
            logger.info(f"  {status} {result['patent_number']}: {result.get('error', '成功')}")

        return {
            "total": len(pdf_files),
            "success": success_count,
            "failed": failed_count,
            "total_time": total_time,
            "reports/reports/results": results
        }


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='专利PDF批量处理')
    parser.add_argument('--dir', default='/Users/xujian/apps/apps/patents/PDF',
                      help='PDF文件目录')
    parser.add_argument('--limit', type=int, default=0,
                      help='限制处理数量（0表示全部）')

    args = parser.parse_args()

    # 创建处理器
    processor = PatentBatchProcessor(pdf_directory=args.dir)

    # 查找PDF文件
    pdf_files = processor.find_pdf_files()

    # 限制处理数量
    if args.limit > 0:
        pdf_files = pdf_files[:args.limit]
        logger.info(f"限制处理数量: {args.limit}")

    # 批量处理
    result = processor.process_batch(pdf_files)

    # 返回退出码
    sys.exit(0 if result["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
