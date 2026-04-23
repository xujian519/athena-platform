#!/usr/bin/env python3
"""
Docling批量专利PDF处理脚本
处理170个专利PDF，提取文本和结构

Author: Athena平台团队
Date: 2026-04-22
"""

import json
import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DoclingBatchProcessor:
    """Docling批量处理器"""

    def __init__(
        self,
        input_dir: str,
        output_dir: str,
        parallel: int = 4,
        ocr_engine: str = "rapidocr"  # 使用RapidOCR引擎（轻量快速）
    ):
        """
        初始化批量处理器

        Args:
            input_dir: 输入PDF目录
            output_dir: 输出目录
            parallel: 并行处理数量
            ocr_engine: OCR引擎选择 (rapidocr/easyocr/tesseract)
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.parallel = parallel
        self.ocr_engine = ocr_engine

        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 统计信息
        self.stats = {
            "total_files": 0,
            "successful": 0,
            "failed": 0,
            "skipped": 0,
            "start_time": None,
            "end_time": None,
            "errors": []
        }

    def find_pdf_files(self) -> list[Path]:
        """查找所有PDF文件"""
        logger.info(f"🔍 扫描目录: {self.input_dir}")

        pdf_files = list(self.input_dir.rglob("*.pdf"))

        logger.info(f"✅ 找到 {len(pdf_files)} 个PDF文件")

        return sorted(pdf_files)

    def process_single_pdf(self, pdf_path: Path) -> dict[str, Any]:
        """
        处理单个PDF文件

        Args:
            pdf_path: PDF文件路径

        Returns:
            处理结果
        """
        file_start_time = time.time()

        try:
            logger.info(f"🔄 处理: {pdf_path.name}")

            # 导入Docling
            from docling.datamodel.pipeline_options import AcceleratorOptions
            from docling.document_converter import DocumentConverter
            from docling.pipeline_options import PdfPipelineOptions

            # 配置pipeline选项 - 强制使用RapidOCR
            pipeline_options = PdfPipelineOptions()
            pipeline_options.do_ocr = True
            pipeline_options.do_table_structure = True

            # 强制使用RapidOCR（不使用ocrmac）
            pipeline_options.ocr_options = {
                "ocr_engine": self.ocr_engine,  # rapidocr
                "force_full_page_ocr": True
            }

            # 加速器选项（使用MPS if available）
            accelerator_options = AcceleratorOptions(
                num_threads=2,  # 限制线程数
                device="mps"  # 使用MPS加速
            )
            pipeline_options.accelerator_options = accelerator_options

            # 创建转换器（指定OCR引擎）
            converter = DocumentConverter(format_options={
                "application/pdf": pipeline_options
            })

            # 转换PDF
            doc = converter.convert(str(pdf_path))

            # 提取文本内容
            full_text = []
            pages_info = []

            for page_idx, page in enumerate(doc.pages):
                page_text = ""

                # 提取页面内容
                if hasattr(page, 'items'):
                    for item in page.items:
                        if hasattr(item, 'text') and item.text:
                            page_text += item.text + "\n"

                full_text.append(page_text)

                # 页面信息
                pages_info.append({
                    "page_number": page_idx + 1,
                    "char_count": len(page_text),
                    "has_content": len(page_text) > 0
                })

            # 保存文本文件
            output_txt = self.output_dir / f"{pdf_path.stem}.txt"
            output_txt.write_text("\n\n".join(full_text), encoding="utf-8")

            # 保存JSON元数据
            metadata = {
                "source": str(pdf_path),
                "file_name": pdf_path.name,
                "total_pages": len(doc.pages) if hasattr(doc, 'pages') else 0,
                "total_characters": sum(len(p) for p in full_text),
                "pages": pages_info,
                "processing_time": time.time() - file_start_time,
                "ocr_engine": self.ocr_engine
            }

            output_json = self.output_dir / f"{pdf_path.stem}.json"
            output_json.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

            logger.info(f"  ✅ 成功: {pdf_path.name} ({len(full_text)}页, {metadata['total_characters']}字符)")

            return {
                "file": str(pdf_path),
                "success": True,
                "pages": len(full_text),
                "characters": metadata['total_characters'],
                "processing_time": time.time() - file_start_time
            }

        except Exception as e:
            logger.error(f"  ❌ 失败: {pdf_path.name} - {e}")

            return {
                "file": str(pdf_path),
                "success": False,
                "error": str(e),
                "processing_time": time.time() - file_start_time
            }

    def process_batch(self, pdf_files: list[Path]) -> dict[str, Any]:
        """
        批量处理PDF文件

        Args:
            pdf_files: PDF文件列表

        Returns:
            批量处理结果
        """
        self.stats["start_time"] = time.time()
        self.stats["total_files"] = len(pdf_files)

        logger.info("=" * 80)
        logger.info(f"🚀 开始批量处理 {len(pdf_files)} 个PDF文件")
        logger.info(f"   输入目录: {self.input_dir}")
        logger.info(f"   输出目录: {self.output_dir}")
        logger.info(f"   并行数量: {self.parallel}")
        logger.info(f"   OCR引擎: {self.ocr_engine}")
        logger.info("=" * 80)

        # 使用线程池并行处理
        with ThreadPoolExecutor(max_workers=self.parallel) as executor:
            # 提交所有任务
            future_to_pdf = {
                executor.submit(self.process_single_pdf, pdf): pdf
                for pdf in pdf_files
            }

            # 收集结果
            results = []
            completed = 0

            for future in as_completed(future_to_pdf):
                pdf = future_to_pdf[future]
                completed += 1

                try:
                    result = future.result()
                    results.append(result)

                    if result["success"]:
                        self.stats["successful"] += 1
                    else:
                        self.stats["failed"] += 1
                        self.stats["errors"].append({
                            "file": result["file"],
                            "error": result.get("error", "Unknown error")
                        })

                except Exception as e:
                    logger.error(f"❌ 处理异常: {pdf} - {e}")
                    self.stats["failed"] += 1
                    self.stats["errors"].append({
                        "file": str(pdf),
                        "error": str(e)
                    })

                # 进度报告
                if completed % 10 == 0 or completed == len(pdf_files):
                    progress = completed / len(pdf_files) * 100
                    logger.info(f"📊 进度: {completed}/{len(pdf_files)} ({progress:.1f}%)")

        self.stats["end_time"] = time.time()

        return {
            "results": results,
            "stats": self.stats
        }

    def generate_summary_report(self, batch_result: dict[str, Any]):
        """生成汇总报告"""

        stats = self.stats
        total_time = stats["end_time"] - stats["start_time"]

        # 生成Markdown报告
        md_content = f"""# Docling批量处理报告

**处理时间**: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stats['start_time']))}
**总耗时**: {total_time / 60:.1f} 分钟
**平均速度**: {total_time / max(stats['total_files'], 1):.1f} 秒/文件

---

## 📊 处理统计

| 项目 | 数量 | 占比 |
|------|------|------|
| **总文件数** | {stats['total_files']} | 100% |
| **成功** | {stats['successful']} | {stats['successful'] / max(stats['total_files'], 1) * 100:.1f}% |
| **失败** | {stats['failed']} | {stats['failed'] / max(stats['total_files'], 1) * 100:.1f}% |

---

## ⚡ 性能指标

- **总耗时**: {total_time / 60:.1f} 分钟
- **平均速度**: {total_time / max(stats['total_files'], 1):.1f} 秒/文件
- **预估170个PDF**: {(total_time / max(stats['total_files'], 1)) * 170 / 60:.1f} 分钟

---

## ❌ 失败文件

"""

        if stats["errors"]:
            for error in stats["errors"]:
                md_content += f"""
### {Path(error['file']).name}

**错误**: {error['error']}

---
"""
        else:
            md_content += "\n✅ 所有文件处理成功，无失败文件！\n"

        md_content += f"""

---

## 📁 输出文件

所有处理结果已保存至: `{self.output_dir}`

**文件格式**:
- `.txt` - 提取的文本内容
- `.json` - 结构化元数据

---

**报告生成**: Athena Docling批量处理器 🚀
"""

        # 保存报告
        report_path = self.output_dir / "批量处理报告.md"
        report_path.write_text(md_content, encoding="utf-8")

        logger.info(f"📝 汇总报告已生成: {report_path}")

        # 同时保存JSON报告
        json_report = {
            "processing_time": time.strftime('%Y-%m-%d %H:%M:%S'),
            "stats": stats,
            "performance": {
                "total_time_seconds": total_time,
                "avg_time_per_file": total_time / max(stats['total_files'], 1),
                "estimated_170_files_minutes": (total_time / max(stats['total_files'], 1)) * 170 / 60
            },
            "errors": stats["errors"]
        }

        json_report_path = self.output_dir / "批量处理报告.json"
        json_report_path.write_text(json.dumps(json_report, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    """主函数"""

    # 检查命令行参数
    if len(sys.argv) < 3:
        print("使用方法: python batch_docling_patents.py <输入目录> <输出目录> [并行数量] [OCR引擎]")
        print("")
        print("参数说明:")
        print("  输入目录: 包含PDF文件的目录")
        print("  输出目录: 保存处理结果的目录")
        print("  并行数量: 可选，默认4")
        print("  OCR引擎: 可选，默认rapidocr (可选: easyocr/tesseract)")
        print("")
        print("示例:")
        print("  python batch_docling_patents.py ./pdfs ./output")
        print("  python batch_docling_patents.py ./pdfs ./output 8 rapidocr")
        sys.exit(1)

    input_dir = sys.argv[1]
    output_dir = sys.argv[2]
    parallel = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    ocr_engine = sys.argv[4] if len(sys.argv) > 4 else "rapidocr"

    # 检查输入目录
    input_path = Path(input_dir)
    if not input_path.exists():
        logger.error(f"❌ 输入目录不存在: {input_dir}")
        sys.exit(1)

    # 创建处理器
    processor = DoclingBatchProcessor(
        input_dir=input_dir,
        output_dir=output_dir,
        parallel=parallel,
        ocr_engine=ocr_engine
    )

    # 查找PDF文件
    pdf_files = processor.find_pdf_files()

    if not pdf_files:
        logger.warning(f"⚠️ 未找到PDF文件: {input_dir}")
        sys.exit(0)

    # 批量处理
    batch_result = processor.process_batch(pdf_files)

    # 生成汇总报告
    processor.generate_summary_report(batch_result)

    # 输出最终统计
    stats = processor.stats
    logger.info("=" * 80)
    logger.info("✅ 批量处理完成！")
    logger.info(f"   总文件数: {stats['total_files']}")
    logger.info(f"   成功: {stats['successful']}")
    logger.info(f"   失败: {stats['failed']}")
    logger.info(f"   总耗时: {(stats['end_time'] - stats['start_time']) / 60:.1f} 分钟")
    logger.info(f"   输出目录: {processor.output_dir}")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
