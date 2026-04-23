#!/usr/bin/env python3
"""
RapidOCR批量专利PDF处理脚本
直接使用RapidOCR处理170个专利PDF

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


class RapidOCRBatchProcessor:
    """RapidOCR批量处理器"""

    def __init__(
        self,
        input_dir: str,
        output_dir: str,
        parallel: int = 4
    ):
        """
        初始化批量处理器

        Args:
            input_dir: 输入PDF目录
            output_dir: 输出目录
            parallel: 并行处理数量
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.parallel = parallel

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

            # 导入依赖
            from pdf2image import convert_from_path
            from rapidocr_onnxruntime import RapidOCR

            # 初始化RapidOCR
            ocr = RapidOCR()

            # PDF转图像
            logger.info("  📄 转换PDF为图像...")
            images = convert_from_path(str(pdf_path), dpi=200)

            logger.info(f"  ✅ 成功转换 {len(images)} 页")

            # 识别每一页
            full_text = []
            pages_info = []

            for img_idx, image in enumerate(images):
                # 转换为numpy数组
                img_array = numpy.array(image)

                # OCR识别
                result, _ = ocr(img_array)

                # 提取文本
                page_text = "\n".join([line[1] for line in result]) if result else ""

                full_text.append(page_text)
                pages_info.append({
                    "page_number": img_idx + 1,
                    "char_count": len(page_text),
                    "has_content": len(page_text) > 0
                })

                if (img_idx + 1) % 5 == 0:
                    logger.info(f"    📊 已处理 {img_idx + 1}/{len(images)} 页")

            # 保存文本文件
            output_txt = self.output_dir / f"{pdf_path.stem}.txt"
            output_txt.write_text("\n\n".join(full_text), encoding="utf-8")

            # 保存JSON元数据
            metadata = {
                "source": str(pdf_path),
                "file_name": pdf_path.name,
                "total_pages": len(images),
                "total_characters": sum(len(p) for p in full_text),
                "pages": pages_info,
                "processing_time": time.time() - file_start_time,
                "method": "RapidOCR + pdf2image"
            }

            output_json = self.output_dir / f"{pdf_path.stem}.json"
            output_json.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

            logger.info(f"  ✅ 成功: {pdf_path.name} ({len(images)}页, {metadata['total_characters']}字符)")

            return {
                "file": str(pdf_path),
                "success": True,
                "pages": len(images),
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
        logger.info("   OCR引擎: RapidOCR")
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
                if completed % 5 == 0 or completed == len(pdf_files):
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
        md_content = f"""# RapidOCR批量处理报告

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

**报告生成**: Athena RapidOCR批量处理器 🚀
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
        print("使用方法: python batch_rapidocr_patents.py <输入目录> <输出目录> [并行数量]")
        print("")
        print("参数说明:")
        print("  输入目录: 包含PDF文件的目录")
        print("  输出目录: 保存处理结果的目录")
        print("  并行数量: 可选，默认4")
        print("")
        print("示例:")
        print("  python batch_rapidocr_patents.py ./pdfs ./output")
        print("  python batch_rapidocr_patents.py ./pdfs ./output 8")
        sys.exit(1)

    input_dir = sys.argv[1]
    output_dir = sys.argv[2]
    parallel = int(sys.argv[3]) if len(sys.argv) > 3 else 4

    # 检查输入目录
    input_path = Path(input_dir)
    if not input_path.exists():
        logger.error(f"❌ 输入目录不存在: {input_dir}")
        sys.exit(1)

    # 创建处理器
    processor = RapidOCRBatchProcessor(
        input_dir=input_dir,
        output_dir=output_dir,
        parallel=parallel
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
    import numpy
    main()
