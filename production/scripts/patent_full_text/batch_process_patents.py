#!/usr/bin/env python3
"""
专利PDF批处理脚本 - 集成OCR功能
Batch Patent PDF Processing with OCR Integration

使用本地多模态系统和智能OCR路由器处理专利PDF
"""

from __future__ import annotations
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# 设置路径
PROJECT_ROOT = Path("/Users/xujian/Athena工作平台")
PATENT_PDF_DIR = Path("/Users/xujian/apps/apps/patents/PDF")
PATENT_PROCESSED_DIR = PROJECT_ROOT / "apps/apps/patents" / "processed"

# 添加OCR路由器路径
sys.path.insert(0, str(PROJECT_ROOT / "production/dev/scripts/patent_full_text"))
sys.path.insert(0, str(PROJECT_ROOT))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def extract_patent_number(pdf_path: Path) -> str:
    """从文件路径提取专利号"""
    # 文件名格式: CN/US/WO + 专利号.pdf
    parts = pdf_path.stem.split('/')
    if len(parts) > 1:
        return parts[-1]
    return pdf_path.stem


def extract_text_from_pdf(pdf_path: str, enable_ocr: bool = True) -> dict:
    """
    从PDF提取文本 - 集成智能OCR路由器

    Args:
        pdf_path: PDF文件路径
        enable_ocr: 是否启用OCR（用于扫描版PDF）

    Returns:
        包含提取结果的字典
    """
    # 导入智能OCR路由器
    from smart_ocr_router import LocalOCRRouter

    router = LocalOCRRouter()

    # 使用OCR路由器提取文本
    result = router.extract_text_from_pdf(pdf_path, use_ocr=enable_ocr)

    return result


def process_patent_text(text: str, patent_number: str) -> dict:
    """处理专利文本，提取结构化信息"""
    # 简单的文本分析
    lines = text.split('\n')

    # 查找标题（通常是第一行非空行）
    title = ""
    for line in lines:
        if line.strip() and len(line.strip()) > 5:
            title = line.strip()
            break

    # 提取摘要（通常是包含"摘要"或"abstract"的部分）
    abstract = ""
    in_abstract = False
    abstract_lines = []
    for line in lines:
        if '摘要' in line or 'abstract' in line.lower():
            in_abstract = True
            continue
        if in_abstract:
            if line.strip() and len(line.strip()) > 10:
                abstract_lines.append(line.strip())
            if len(abstract_lines) > 5:  # 摘要通常几行
                break
    abstract = ' '.join(abstract_lines[:10])  # 取前10行

    # 如果没找到摘要，使用文本开头
    if not abstract and len(text) > 200:
        abstract = text[:500]

    return {
        "patent_number": patent_number,
        "title": title or patent_number,
        "abstract": abstract or text[:500] if text else "",
        "full_text": text,
        "text_length": len(text)
    }


def save_to_file(data: dict, output_dir: Path) -> None:
    """保存处理结果到JSON文件"""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{data['patent_number']}.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return output_file


def main() -> None:
    """主处理流程 - 集成OCR功能"""
    logger.info("="*70)
    logger.info("专利PDF批处理 - 集成OCR功能")
    logger.info("="*70)

    # 查找所有PDF文件
    pdf_files = list(PATENT_PDF_DIR.rglob("*.pdf"))

    if not pdf_files:
        logger.warning("未找到PDF文件")
        return

    logger.info(f"找到 {len(pdf_files)} 个PDF文件")
    logger.info("")

    # 输出目录
    output_dir = PATENT_PROCESSED_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    # 处理结果
    results = []
    success_count = 0
    failed_count = 0

    # 处理每个PDF
    for i, pdf_path in enumerate(pdf_files, 1):
        patent_number = extract_patent_number(pdf_path)

        logger.info(f"[{i}/{len(pdf_files)}] 处理: {patent_number}")
        logger.info(f"  文件: {pdf_path}")

        try:
            # 使用OCR路由器提取文本
            logger.info("  - 提取文本（启用OCR）...")
            extract_result = extract_text_from_pdf(str(pdf_path), enable_ocr=True)

            if not extract_result['success'] or extract_result['text_length'] < 50:
                logger.warning("  ⚠️  文本提取失败")
                logger.warning(f"     方法: {extract_result.get('method', 'unknown')}")
                logger.warning(f"     长度: {extract_result['text_length']}")
                logger.warning(f"     错误: {extract_result.get('error', 'unknown')}")

                failed_count += 1
                results.append({
                    "patent_number": patent_number,
                    "status": "failed",
                    "error": extract_result.get('error', '文本提取失败')
                })
                continue

            text = extract_result['text']
            logger.info("  ✅ 提取成功")
            logger.info(f"     方法: {extract_result.get('method', 'unknown')}")
            logger.info(f"     页数: {extract_result.get('pages_processed', 0)}")
            logger.info(f"     长度: {len(text)} 字符")

            # 处理文本
            logger.info("  - 分析结构...")
            patent_data = process_patent_text(text, patent_number)

            # 添加提取方法信息
            patent_data['extraction_method'] = extract_result.get('method', 'unknown')
            patent_data['pages_processed'] = extract_result.get('pages_processed', 0)

            # 保存结果
            output_file = save_to_file(patent_data, output_dir)
            logger.info(f"  ✅ 保存到: {output_file}")

            success_count += 1
            results.append({
                "patent_number": patent_number,
                "status": "success",
                "text_length": len(text),
                "output_file": str(output_file),
                "method": extract_result.get('method', 'unknown')
            })

        except Exception as e:
            logger.error(f"  ❌ 处理失败: {e}")
            failed_count += 1
            results.append({
                "patent_number": patent_number,
                "status": "failed",
                "error": str(e)
            })

        logger.info("")

    # 保存处理报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "total": len(pdf_files),
        "success": success_count,
        "failed": failed_count,
        "reports/reports/results": results
    }

    report_file = output_dir / f"processing_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # 打印总结
    logger.info("="*70)
    logger.info("处理完成")
    logger.info("="*70)
    logger.info(f"总计: {len(pdf_files)}")
    logger.info(f"成功: {success_count}")
    logger.info(f"失败: {failed_count}")
    logger.info(f"报告: {report_file}")
    logger.info("")
    logger.info("处理详情:")

    for result in results:
        status_icon = "✅" if result["status"] == "success" else "❌"
        logger.info(f"  {status_icon} {result['patent_number']}: {result.get('error', '成功')}")


if __name__ == "__main__":
    main()
