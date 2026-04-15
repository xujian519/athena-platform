#!/usr/bin/env python3
"""
测试失败专利PDF的OCR处理
Test OCR Processing for Failed Patent PDFs
"""

from __future__ import annotations
import logging
import sys
from pathlib import Path
from typing import Any

# 设置路径
PROJECT_ROOT = Path("/Users/xujian/Athena工作平台")
PATENT_PDF_DIR = Path("/Users/xujian/apps/apps/patents/PDF")

sys.path.insert(0, str(PROJECT_ROOT / "production/dev/scripts/patent_full_text"))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_tesseract() -> Any:
    """测试Tesseract是否可用"""
    logger.info("=" * 60)
    logger.info("测试Tesseract OCR环境")
    logger.info("=" * 60)

    # 检查tesseract命令
    import subprocess
    try:
        result = subprocess.run(
            ['tesseract', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            logger.info(f"✅ Tesseract已安装: {version}")
        else:
            logger.warning("⚠️ Tesseract命令返回错误")
            return False
    except Exception as e:
        logger.warning(f"⚠️ Tesseract未安装: {e}")
        logger.info("   安装方法: brew install tesseract tesseract-lang")
        return False

    # 检查语言包
    result = subprocess.run(
        ['tesseract', '--list-langs'],
        capture_output=True,
        text=True,
        timeout=5
    )

    langs = result.stdout.strip().split('\n')[1:]  # 跳过第一行
    logger.info(f"📚 可用语言包 ({len(langs)}):")

    has_chinese = False
    for lang in langs:
        if 'chi_sim' in lang or 'chi_tra' in lang:
            logger.info(f"   ✅ {lang}")
            has_chinese = True
        elif lang.strip():
            logger.info(f"   • {lang}")

    if not has_chinese:
        logger.warning("⚠️ 未找到中文语言包")
        logger.info("   安装方法: brew install tesseract-lang")
    else:
        logger.info("✅ 中文语言包已安装")

    # 测试pytesseract
    try:
        import pytesseract
        logger.info("✅ pytesseract Python库已安装")
        return True
    except ImportError:
        logger.warning("⚠️ pytesseract Python库未安装")
        logger.info("   安装方法:")
        logger.info("   pip3 install --break-system-packages pytesseract")
        return False


def test_single_pdf_with_tesseract(pdf_path: str) -> Any:
    """使用Tesseract测试单个PDF"""
    logger.info(f"\n{'='*60}")
    logger.info(f"测试PDF: {Path(pdf_path).name}")
    logger.info(f"{'='*60}")

    try:
        import io

        import fitz  # PyMuPDF
        import pytesseract
        from PIL import Image

        doc = fitz.open(pdf_path)
        total_pages = len(doc)

        logger.info(f"📄 总页数: {total_pages}")
        logger.info("🔍 开始OCR处理...")

        all_text = ""

        # 只处理前3页作为测试
        max_pages = min(3, total_pages)

        for page_num in range(max_pages):
            logger.info(f"   处理第{page_num+1}页...")

            page = doc[page_num]

            # 转换为高分辨率图像
            mat = fitz.Matrix(3.0, 3.0)  # 3倍分辨率
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes('png')
            img = Image.open(io.BytesIO(img_data))

            # 图像预处理
            from PIL import ImageEnhance

            # 转灰度
            if img.mode != 'L':
                img = img.convert('L')

            # 增强对比度
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(2.0)

            # 增强锐度
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(2.0)

            # OCR识别
            page_text = pytesseract.image_to_string(
                img,
                lang='chi_sim+eng',
                config='--psm 6 --oem 3'
            )

            all_text += f"\n\n--- 第{page_num+1}页 ---\n\n{page_text}"

            # 显示预览
            preview = page_text[:200].replace('\n', ' ')
            logger.info(f"   预览: {preview}...")

        doc.close()

        logger.info("\n✅ OCR完成!")
        logger.info(f"📝 总字符数: {len(all_text)}")
        logger.info("\n文本预览:")
        logger.info("-" * 60)
        logger.info(all_text[:500])
        logger.info("-" * 60)

        return len(all_text) > 100

    except Exception as e:
        logger.error(f"❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main() -> None:
    """主测试流程"""
    logger.info("\n" + "=" * 60)
    logger.info("专利PDF OCR测试")
    logger.info("=" * 60)

    # 1. 测试Tesseract环境
    tesseract_ok = test_tesseract()

    if not tesseract_ok:
        logger.error("\n❌ Tesseract环境未就绪，请先安装")
        logger.info("\n安装步骤:")
        logger.info("1. brew install tesseract tesseract-lang")
        logger.info("2. pip3 install --break-system-packages pytesseract")
        return

    # 2. 测试之前失败的PDF
    failed_pdfs = [
        "CN/CN207305556U.pdf",
        "CN/CN205249962U.pdf",
        "CN/CN205124552U.pdf",
        "CN/CN2418669Y.pdf",
        "WO/WO2013078254A1.pdf"
    ]

    results = {}

    for pdf_name in failed_pdfs:
        pdf_path = PATENT_PDF_DIR / pdf_name

        if not pdf_path.exists():
            logger.warning(f"⚠️ 文件不存在: {pdf_path}")
            continue

        success = test_single_pdf_with_tesseract(str(pdf_path))
        results[pdf_name] = "✅ 成功" if success else "❌ 失败"

    # 打印总结
    logger.info(f"\n{'='*60}")
    logger.info("测试总结")
    logger.info(f"{'='*60}")

    for pdf_name, result in results.items():
        logger.info(f"{result}: {pdf_name}")


if __name__ == "__main__":
    main()
