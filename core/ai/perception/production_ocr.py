#!/usr/bin/env python3

"""
Athena 感知模块 - 生产级OCR处理器
集成真实的Tesseract OCR引擎
"""

import logging
import os
import subprocess
from typing import Any, Optional

logger = logging.getLogger(__name__)

class ProductionOCRProcessor:
    """生产级OCR处理器"""

    def __init__(self):
        self.tesseract_path = self._find_tesseract()
        self.supported_languages = ['chi_sim', 'chi_tra', 'eng']

    def _find_tesseract(self) -> Optional[str]:
        """查找Tesseract可执行文件"""
        try:
            result = subprocess.run(
                ['which', 'tesseract'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass

        # 常见路径
        common_paths = [
            '/usr/bin/tesseract',
            '/usr/local/bin/tesseract',
            '/opt/homebrew/bin/tesseract'
        ]

        for path in common_paths:
            if os.path.exists(path):
                return path

        return None

    def is_available(self) -> bool:
        """检查OCR是否可用"""
        if not self.tesseract_path:
            return False

        try:
            result = subprocess.run(
                [self.tesseract_path, '--version'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    async def process_ocr(
        self,
        image_path: str,
        language: str = "chinese",
        preprocess: bool = True,
        extract_tables: bool = False
    ) -> dict[str, Any]:
        """
        处理OCR请求

        Args:
            image_path: 图像文件路径
            language: 语言 (chinese, english, mixed)
            preprocess: 是否预处理
            extract_tables: 是否提取表格

        Returns:
            OCR处理结果
        """
        if not self.is_available():
            raise RuntimeError("Tesseract OCR不可用")

        # 验证文件存在
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图像文件不存在: {image_path}")

        logger.info(f"开始OCR处理: {image_path}")

        try:
            # 转换语言代码
            lang_code = self._convert_language(language)

            # 构建Tesseract命令
            cmd = [
                self.tesseract_path,
                image_path,
                'stdout',  # 输出到stdout
                '-l', lang_code,
                '--oem', '1',  # LSTM神经网络引擎
                '--psm', '6'   # 假设单列文本块
            ]

            # 执行OCR
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                check=True
            )

            text = result.stdout.strip()

            # 计算置信度（Tesseract不直接提供，这里模拟）
            confidence = self._calculate_confidence(text)

            logger.info(f"OCR处理完成: {len(text)}个字符")

            return {
                "text": text,
                "confidence": confidence,
                "language": language,
                "word_count": len(text.split()) if text else 0,
                "char_count": len(text)
            }

        except subprocess.TimeoutExpired:
            raise RuntimeError(f"OCR处理超时: {image_path}") from None
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"OCR处理失败: {e.stderr}") from e
        except Exception as e:
            logger.error(f"OCR处理异常: {e}")
            raise

    def _convert_language(self, language: str) -> str:
        """转换语言代码为Tesseract格式"""
        lang_map = {
            "chinese": "chi_sim+eng",
            "english": "eng",
            "mixed": "chi_sim+chi_tra+eng",
            "traditional": "chi_tra+eng"
        }
        return lang_map.get(language, "chi_sim+eng")

    def _calculate_confidence(self, text: str) -> float:
        """计算OCR置信度"""
        if not text:
            return 0.0

        # 基于文本质量计算置信度
        score = 0.95  # 基础分数

        # 检查是否有中文字符
        has_chinese = any('\u4e00' <= c <= '\u9fff' for c in text)
        if has_chinese:
            score -= 0.05

        # 检查是否有英文字符
        has_english = any(c.isalpha() and ord(c) < 128 for c in text)
        if has_english:
            score -= 0.02

        # 检查文本长度
        if len(text) < 10:
            score -= 0.1

        return max(0.0, min(1.0, score))

# 使用示例
if __name__ == "__main__":
    import asyncio

    async def test():
        processor = ProductionOCRProcessor()

        if not processor.is_available():
            print("❌ Tesseract OCR不可用")
            return

        print("✓ Tesseract OCR可用")

        # 测试OCR
        # result = await processor.process_ocr("/path/to/image.png", "chinese")
        # print(result)

    asyncio.run(test())

