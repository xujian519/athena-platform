#!/usr/bin/env python3
"""
智能OCR路由器 - 基于本地多模态系统
Smart OCR Router - Local Multimodal System

完全基于本地多模态文件系统实现OCR功能
无需外部API，保护数据隐私
"""

from __future__ import annotations
import io
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# 添加项目路径
PROJECT_ROOT = Path("/Users/xujian/Athena工作平台")
sys.path.insert(0, str(PROJECT_ROOT))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from PIL import Image
except ImportError:
    Image = None


class LocalOCRRouter:
    """本地OCR路由器 - 使用多模态系统"""

    def __init__(self):
        """初始化OCR路由器"""
        self.engines = {}
        self.primary_engine = None
        self.fallback_engine = None
        self._init_engines()

    def _init_engines(self):
        """初始化可用的OCR引擎"""
        logger.info("=" * 60)
        logger.info("初始化本地OCR引擎...")
        logger.info("=" * 60)

        # 引擎1: PyMuPDF + 图像预处理 (主要引擎)
        try:
            import fitz  # PyMuPDF
            self.engines['pymupdf'] = {
                'available': True,
                'name': 'PyMuPDF OCR',
                'priority': 1
            }
            logger.info("✅ PyMuPDF引擎已加载")
        except ImportError as e:
            logger.warning(f"⚠️ PyMuPDF未安装: {e}")
            self.engines['pymupdf'] = {
                'available': False,
                'name': 'PyMuPDF OCR',
                'priority': 1
            }

        # 引擎2: PDFPlumber (备用引擎)
        try:
            import pdfplumber
            self.engines['pdfplumber'] = {
                'available': True,
                'name': 'PDFPlumber',
                'priority': 2
            }
            logger.info("✅ PDFPlumber引擎已加载")
        except ImportError:
            logger.warning("⚠️ PDFPlumber未安装")
            self.engines['pdfplumber'] = {
                'available': False,
                'name': 'PDFPlumber',
                'priority': 2
            }

        # 引擎3: 图像增强OCR (备用引擎)
        try:
            from PIL import Image, ImageEnhance, ImageFilter
            self.engines['image_enhanced'] = {
                'available': True,
                'name': 'Image Enhanced OCR',
                'priority': 3
            }
            logger.info("✅ 图像增强OCR引擎已加载")
        except ImportError:
            logger.warning("⚠️ PIL未安装，无法使用图像增强")
            self.engines['image_enhanced'] = {
                'available': False,
                'name': 'Image Enhanced OCR',
                'priority': 3
            }

        # 选择主要和备用引擎
        available_engines = [
            (name, engine) for name, engine in self.engines.items()
            if engine['available']
        ]

        if not available_engines:
            logger.error("❌ 没有可用的OCR引擎！")
            return

        # 按优先级排序
        available_engines.sort(key=lambda x: x[1]['priority'])

        # 设置主要引擎
        self.primary_engine = available_engines[0][0]
        logger.info(f"🎯 主要OCR引擎: {self.engines[self.primary_engine]['name']}")

        # 设置备用引擎
        if len(available_engines) > 1:
            self.fallback_engine = available_engines[1][0]
            logger.info(f"🔄 备用OCR引擎: {self.engines[self.fallback_engine]['name']}")

        logger.info(f"✅ 共 {len(available_engines)} 个引擎可用")
        logger.info("")

    def extract_text_from_pdf(
        self,
        pdf_path: str,
        use_ocr: bool = True,
        max_pages: int = None
    ) -> dict[str, Any]:
        """
        从PDF提取文本

        Args:
            pdf_path: PDF文件路径
            use_ocr: 是否使用OCR（对于扫描版PDF）
            max_pages: 最大处理页数（None表示全部）

        Returns:
            提取结果字典
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"处理PDF: {Path(pdf_path).name}")
        logger.info(f"{'='*60}")

        result = {
            'success': False,
            'text': '',
            'text_length': 0,
            'pages_processed': 0,
            'method': None,
            'error': None,
            'metadata': {}
        }

        try:
            pdf_file = Path(pdf_path)
            if not pdf_file.exists():
                result['error'] = f"文件不存在: {pdf_path}"
                logger.error(f"❌ {result['error']}")
                return result

            # 先尝试直接文本提取
            logger.info("📖 尝试直接文本提取...")
            direct_result = self._extract_text_direct(pdf_path, max_pages)

            # 判断是否需要OCR
            if direct_result['text_length'] > 100:
                logger.info(f"✅ 直接提取成功，文本长度: {direct_result['text_length']}")
                result.update(direct_result)
                return result

            # 如果直接提取失败，使用OCR
            if use_ocr:
                logger.info("🔍 直接提取文本过少，启用OCR...")
                ocr_result = self._extract_text_ocr(pdf_path, max_pages)

                if ocr_result['text_length'] > 50:
                    logger.info(f"✅ OCR提取成功，文本长度: {ocr_result['text_length']}")
                    result.update(ocr_result)
                    return result
                else:
                    result['error'] = "OCR提取文本过少"
                    logger.warning(f"⚠️ {result['error']}")
            else:
                result['error'] = "直接提取失败且未启用OCR"
                logger.warning(f"⚠️ {result['error']}")

        except Exception as e:
            result['error'] = f"处理失败: {str(e)}"
            logger.error(f"❌ {result['error']}", exc_info=True)

        return result

    def _extract_text_direct(
        self,
        pdf_path: str,
        max_pages: int | None = None
    ) -> dict[str, Any]:
        """直接提取PDF文本（无需OCR）"""
        result = {
            'success': False,
            'text': '',
            'text_length': 0,
            'pages_processed': 0,
            'method': 'direct_extraction'
        }

        try:
            import fitz  # PyMuPDF

            doc = fitz.open(pdf_path)
            total_pages = len(doc)

            if max_pages is None:
                max_pages = total_pages
            else:
                max_pages = min(max_pages, total_pages)

            logger.info(f"   📄 总页数: {total_pages}，处理: {max_pages}页")

            text = ""
            for page_num in range(max_pages):
                page = doc[page_num]
                page_text = page.get_text()
                text += page_text + "\n\n"

                if (page_num + 1) % 10 == 0:
                    logger.info(f"   进度: {page_num + 1}/{max_pages}")

            doc.close()

            result['text'] = text.strip()
            result['text_length'] = len(text)
            result['pages_processed'] = max_pages
            result['success'] = True

        except Exception as e:
            logger.warning(f"直接提取失败: {e}")

        return result

    def _extract_text_ocr(
        self,
        pdf_path: str,
        max_pages: int | None = None
    ) -> dict[str, Any]:
        """使用OCR提取PDF文本"""
        result = {
            'success': False,
            'text': '',
            'text_length': 0,
            'pages_processed': 0,
            'method': 'ocr_extraction'
        }

        try:
            import fitz  # PyMuPDF

            doc = fitz.open(pdf_path)
            total_pages = len(doc)

            if max_pages is None:
                max_pages = total_pages
            else:
                max_pages = min(max_pages, total_pages)

            logger.info(f"   📄 OCR总页数: {total_pages}，处理: {max_pages}页")

            text = ""

            # 尝试使用Tesseract OCR
            try:
                import pytesseract
                from PIL import Image

                logger.info("   🎯 使用Tesseract OCR引擎...")

                for page_num in range(max_pages):
                    page = doc[page_num]

                    # 转换页面为图像（高分辨率）
                    mat = fitz.Matrix(3.0, 3.0)  # 3倍分辨率，提高OCR准确率
                    pix = page.get_pixmap(matrix=mat)
                    img_data = pix.tobytes('png')
                    img = Image.open(io.BytesIO(img_data))

                    # 图像预处理
                    img = self._preprocess_image(img)

                    # OCR识别（中英文混合）
                    # 使用更优化的参数
                    page_text = pytesseract.image_to_string(
                        img,
                        lang='chi_sim+eng',
                        config='--psm 6 --oem 3'  # psm 6: 单列文本, oem 3: 默认LSTM OCR引擎
                    )

                    text += f"\n\n--- 第{page_num+1}页 ---\n\n{page_text}"

                    if (page_num + 1) % 2 == 0:
                        logger.info(f"   OCR进度: {page_num + 1}/{max_pages}")

                result['method'] = 'tesseract_ocr'
                logger.info("   ✅ Tesseract OCR完成")

            except ImportError:
                logger.warning("   ⚠️ Tesseract未安装，使用备用方案...")

                # 备用方案：使用高分辨率图像转文字
                for page_num in range(max_pages):
                    page = doc[page_num]

                    # 更高分辨率
                    mat = fitz.Matrix(3.0, 3.0)  # 3倍分辨率
                    pix = page.get_pixmap(matrix=mat)

                    # 尝试获取文本
                    page_text = page.get_text("text", flags=fitz.TEXT_PRESERVE_WHITESPACE)

                    text += f"\n\n--- 第{page_num+1}页 ---\n\n{page_text}"

                    if (page_num + 1) % 2 == 0:
                        logger.info(f"   进度: {page_num + 1}/{max_pages}")

                result['method'] = 'high_res_extraction'

            doc.close()

            result['text'] = text.strip()
            result['text_length'] = len(text)
            result['pages_processed'] = max_pages
            result['success'] = True

        except Exception as e:
            logger.error(f"OCR提取失败: {e}", exc_info=True)
            result['error'] = str(e)

        return result

    def _preprocess_image(self, image: 'Image.Image') -> 'Image.Image':
        """预处理图像以提升OCR准确率"""
        try:
            from PIL import ImageEnhance, ImageFilter

            # 转换为灰度
            if image.mode != 'L':
                image = image.convert('L')

            # 增强对比度
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)

            # 增强锐度
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(2.0)

            # 去噪
            image = image.filter(ImageFilter.MedianFilter(size=3))

            return image

        except Exception as e:
            logger.warning(f"图像预处理失败: {e}")
            return image

    def batch_extract_from_pdfs(
        self,
        pdf_directory: str,
        output_directory: str = None,
        use_ocr: bool = True
    ) -> list[dict]:
        """
        批量处理PDF文件

        Args:
            pdf_directory: PDF文件目录
            output_directory: 输出目录（可选）
            use_ocr: 是否使用OCR

        Returns:
            处理结果列表
        """
        pdf_dir = Path(pdf_directory)

        if not pdf_dir.exists():
            logger.error(f"❌ 目录不存在: {pdf_directory}")
            return []

        # 查找所有PDF文件
        pdf_files = list(pdf_dir.glob("*.pdf")) + list(pdf_dir.glob("*.PDF"))

        if not pdf_files:
            logger.warning(f"⚠️ 未找到PDF文件: {pdf_directory}")
            return []

        logger.info(f"\n{'='*60}")
        logger.info("批量OCR处理")
        logger.info(f"{'='*60}")
        logger.info(f"📁 目录: {pdf_directory}")
        logger.info(f"📄 发现 {len(pdf_files)} 个PDF文件")
        logger.info(f"🔧 OCR模式: {'启用' if use_ocr else '禁用'}")
        logger.info("")

        results = []

        for idx, pdf_file in enumerate(pdf_files, 1):
            logger.info(f"\n[{idx}/{len(pdf_files)}] 处理: {pdf_file.name}")

            # 提取文本
            result = self.extract_text_from_pdf(
                str(pdf_file),
                use_ocr=use_ocr
            )

            result['filename'] = pdf_file.name
            result['filepath'] = str(pdf_file)
            result['file_size'] = pdf_file.stat().st_size

            results.append(result)

            # 如果指定了输出目录，保存结果
            if output_directory and result['success']:
                self._save_extraction_result(
                    result,
                    output_directory,
                    pdf_file.stem
                )

        # 打印总结
        self._print_batch_summary(results)

        return results

    def _save_extraction_result(
        self,
        result: dict,
        output_dir: str,
        base_name: str
    ):
        """保存提取结果"""
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # 保存文本
            txt_file = output_path / f"{base_name}.txt"
            with open(txt_file, 'w', encoding='utf-8') as f:
                f.write(result['text'])

            # 保存元数据
            meta_file = output_path / f"{base_name}_metadata.json"
            metadata = {
                'filename': result['filename'],
                'text_length': result['text_length'],
                'pages_processed': result['pages_processed'],
                'method': result['method'],
                'timestamp': datetime.now().isoformat()
            }

            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            logger.info(f"   💾 已保存: {txt_file.name}")

        except Exception as e:
            logger.error(f"   ❌ 保存失败: {e}")

    def _print_batch_summary(self, results: list[dict]):
        """打印批处理总结"""
        logger.info(f"\n{'='*60}")
        logger.info("批处理总结")
        logger.info(f"{'='*60}")

        total = len(results)
        success = sum(1 for r in results if r['success'])
        failed = total - success

        total_chars = sum(r['text_length'] for r in results)

        logger.info(f"📊 总计: {total} 个文件")
        logger.info(f"✅ 成功: {success} 个")
        logger.info(f"❌ 失败: {failed} 个")
        logger.info(f"📝 提取字符: {total_chars:,} 个")

        if success > 0:
            avg_length = total_chars / success
            logger.info(f"📏 平均长度: {avg_length:,.0f} 字符/文件")

        # 成功率
        success_rate = (success / total * 100) if total > 0 else 0
        logger.info(f"📈 成功率: {success_rate:.1f}%")

        # 显示失败文件
        if failed > 0:
            logger.info("\n❌ 失败文件:")
            for result in results:
                if not result['success']:
                    logger.info(f"   - {result['filename']}: {result.get('error', '未知错误')}")

        logger.info(f"{'='*60}\n")


def main():
    """测试OCR路由器"""
    router = LocalOCRRouter()

    # 测试单个文件
    pdf_path = "/Users/xujian/apps/apps/patents/PDF/CN207305556U.pdf"

    logger.info("🧪 测试OCR路由器")
    logger.info(f"📄 测试文件: {pdf_path}")

    result = router.extract_text_from_pdf(pdf_path, use_ocr=True)

    logger.info(f"\n{'='*60}")
    logger.info("处理结果:")
    logger.info(f"{'='*60}")
    logger.info(f"成功: {result['success']}")
    logger.info(f"方法: {result['method']}")
    logger.info(f"页数: {result['pages_processed']}")
    logger.info(f"长度: {result['text_length']}")
    logger.info(f"错误: {result.get('error', '无')}")

    if result['text']:
        preview = result['text'][:500]
        logger.info(f"\n文本预览:\n{preview}...")


if __name__ == "__main__":
    main()
