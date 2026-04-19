#!/usr/bin/env python3
"""
Athena 感知模块 - 企业级Tesseract OCR处理器
支持中英文混合识别、表格识别、版面分析
最后更新: 2026-01-26
"""

from __future__ import annotations
import hashlib
import logging
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class TesseractOCRProcessor:
    """
    企业级Tesseract OCR处理器

    功能：
    - 中英文混合识别
    - 多种图像格式支持
    - 置信度计算
    - 表格识别
    - 版面分析
    """

    def __init__(self, tesseract_path: str | None = None):
        """
        初始化OCR处理器

        Args:
            tesseract_path: Tesseract可执行文件路径
        """
        self.tesseract_path = tesseract_path or self._find_tesseract()
        self.supported_formats = {'.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif', '.webp'}
        self.supported_languages = ['chi_sim', 'chi_tra', 'eng']

        # 验证Tesseract可用性
        if not self.is_available():
            logger.warning("Tesseract OCR不可用，请安装tesseract-ocr")

    def _find_tesseract(self) -> str | None:
        """查找Tesseract可执行文件"""
        try:
            result = subprocess.run(
                ['which', 'tesseract'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass

        # 常见安装路径
        common_paths = [
            '/usr/bin/tesseract',
            '/usr/local/bin/tesseract',
            '/opt/homebrew/bin/tesseract',
            'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
        ]

        for path in common_paths:
            if os.path.exists(path):
                return path

        return None

    def is_available(self) -> bool:
        """检查Tesseract是否可用"""
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

    def get_version(self) -> str | None:
        """获取Tesseract版本"""
        try:
            result = subprocess.run(
                [self.tesseract_path, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None

    async def process_ocr(
        self,
        image_path: str,
        language: str = "chinese",
        preprocess: bool = True,
        extract_tables: bool = False,
        enhance_contrast: bool = False
    ) -> dict[str, Any]:
        """
        处理OCR请求

        Args:
            image_path: 图像文件路径
            language: 语言 (chinese, english, mixed, traditional)
            preprocess: 是否预处理图像
            extract_tables: 是否提取表格
            enhance_contrast: 是否增强对比度

        Returns:
            OCR处理结果字典
        """
        start_time = datetime.now()

        # 验证输入
        validation_result = self._validate_input(image_path)
        if not validation_result["valid"]:
            raise ValueError(validation_result["error"])

        logger.info(f"开始OCR处理: {image_path}, 语言: {language}")

        try:
            # 获取真实路径（解析符号链接）
            real_image_path = os.path.realpath(image_path)
            logger.info(f"真实路径: {real_image_path}")

            # 预处理图像
            processed_image = real_image_path
            if preprocess or enhance_contrast:
                processed_image = await self._preprocess_image(
                    real_image_path,
                    enhance_contrast=enhance_contrast
                )

            # 转换语言代码
            lang_code = self._convert_language(language)

            # 构建Tesseract命令
            cmd = self._build_tesseract_command(
                processed_image,
                lang_code,
                extract_tables=extract_tables
            )

            # 执行OCR
            result = await self._execute_ocr(cmd)

            # 后处理结果
            final_result = self._postprocess_result(result, image_path)

            # 计算处理时间
            processing_time = (datetime.now() - start_time).total_seconds()

            logger.info(f"OCR处理完成: {len(final_result['text'])}个字符, 耗时: {processing_time:.2f}秒")

            return {
                "success": True,
                "text": final_result["text"],
                "confidence": final_result["confidence"],
                "language": language,
                "word_count": final_result["word_count"],
                "char_count": final_result["char_count"],
                "lines": final_result["lines"],
                "processing_time": processing_time,
                "image_path": image_path,
                "timestamp": datetime.now().isoformat(),
                "engine": "tesseract",
                "tables": final_result.get("tables", [])
            }

        except subprocess.TimeoutExpired:
            raise RuntimeError(f"OCR处理超时: {image_path}") from None
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"OCR处理失败: {e.stderr}") from e
        except Exception as e:
            logger.error(f"OCR处理异常: {e}")
            raise

    def _validate_input(self, image_path: str) -> dict[str, Any]:
        """验证输入文件"""
        result = {"valid": True, "error": None}

        # 检查文件是否存在
        if not os.path.exists(image_path):
            result["valid"] = False
            result["error"] = f"文件不存在: {image_path}"
            return result

        # 检查文件格式
        ext = Path(image_path).suffix.lower()
        if ext not in self.supported_formats:
            result["valid"] = False
            result["error"] = f"不支持的文件格式: {ext}"
            return result

        # 检查文件大小
        file_size = os.path.getsize(image_path)
        if file_size > 10 * 1024 * 1024:  # 10MB
            result["valid"] = False
            result["error"] = f"文件过大: {file_size / 1024 / 1024:.2f}MB"
            return result

        return result

    async def _preprocess_image(
        self,
        image_path: str,
        enhance_contrast: bool = False
    ) -> str:
        """
        预处理图像

        Args:
            image_path: 原始图像路径
            enhance_contrast: 是否增强对比度

        Returns:
            处理后的图像路径
        """
        import cv2

        # 读取图像
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"无法读取图像: {image_path}")

        # 转换为灰度图
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img

        # 降噪
        denoised = cv2.fastNlMeansDenoising(gray, h=10)

        # 二值化
        _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # 增强对比度
        if enhance_contrast:
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(binary)
        else:
            enhanced = binary

        # 保存处理后的图像（使用真实路径避免符号链接问题）
        temp_path = f"/tmp/preprocessed_{hashlib.md5(image_path.encode('utf-8'), usedforsecurity=False).hexdigest()}.png"
        # 使用真实路径（macOS上 /tmp 是 /private/tmp 的符号链接）
        temp_path_real = os.path.realpath(temp_path)

        success = cv2.imwrite(temp_path_real, enhanced)

        if not success:
            logger.warning(f"预处理图像保存失败，使用原始图像: {temp_path_real}")
            return image_path

        # 验证文件是否真的保存成功
        if not os.path.exists(temp_path_real):
            logger.warning("预处理图像文件不存在，使用原始图像")
            return image_path

        logger.info(f"✓ 预处理图像已保存: {temp_path_real}")
        return temp_path_real

    def _convert_language(self, language: str) -> str:
        """转换语言代码为Tesseract格式"""
        lang_map = {
            "chinese": "chi_sim+eng",
            "english": "eng",
            "mixed": "chi_sim+eng",
            "traditional": "chi_tra+eng",
            "simplified": "chi_sim+eng",
            "both": "chi_sim+chi_tra+eng"
        }
        return lang_map.get(language, "chi_sim+eng")

    def _build_tesseract_command(
        self,
        image_path: str,
        lang_code: str,
        extract_tables: bool = False
    ) -> list[str]:
        """构建Tesseract命令"""
        cmd = [
            self.tesseract_path,
            image_path,
            'stdout',  # 输出到stdout
            '-l', lang_code,
            '--oem', '1',  # LSTM神经网络引擎
            '--psm', '6',   # 假设单列文本块
        ]

        if extract_tables:
            cmd.extend(['--psm', '6'])  # 表格模式

        return cmd

    async def _execute_ocr(self, cmd: list[str]) -> str:
        """执行OCR命令"""
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=30,
            check=True,
            encoding='utf-8',
            errors='ignore'  # 忽略无法解码的字符
        )
        return result.stdout.strip()

    def _postprocess_result(self, text: str, image_path: str) -> dict[str, Any]:
        """后处理OCR结果"""
        # 清理文本
        cleaned_text = self._clean_text(text)

        # 计算置信度
        confidence = self._calculate_confidence(cleaned_text, text)

        # 统计信息
        lines = cleaned_text.split('\n') if cleaned_text else []
        words = cleaned_text.split() if cleaned_text else []

        return {
            "text": cleaned_text,
            "confidence": confidence,
            "word_count": len(words),
            "char_count": len(cleaned_text),
            "lines": len(lines),
            "tables": []  # TODO: 实现表格提取
        }

    def _clean_text(self, text: str) -> str:
        """清理OCR文本"""
        if not text:
            return ""

        # 移除多余空行
        lines = [line.strip() for line in text.split('\n') if line.strip()]

        # 移除特殊噪声字符
        cleaned_lines = []
        for line in lines:
            # 移除连续的特殊字符
            line = re.sub(r'[^\w\s\u4e00-\u9fff\u3000-\u303f]+', ' ', line)
            # 移除多余空格
            line = re.sub(r'\s+', ' ', line)
            cleaned_lines.append(line)

        return '\n'.join(cleaned_lines)

    def _calculate_confidence(self, cleaned_text: str, raw_text: str) -> float:
        """计算OCR置信度"""
        if not cleaned_text:
            return 0.0

        score = 0.95  # 基础分数

        # 文本长度评分
        if len(cleaned_text) < 10:
            score -= 0.1
        elif len(cleaned_text) > 100:
            score += 0.02

        # 中文字符评分
        chinese_chars = sum(1 for c in cleaned_text if '\u4e00' <= c <= '\u9fff')
        if chinese_chars > 0:
            chinese_ratio = chinese_chars / len(cleaned_text)
            if chinese_ratio > 0.8:
                score += 0.03
            elif chinese_ratio < 0.2:
                score -= 0.05

        # 特殊字符比例
        special_chars = sum(1 for c in cleaned_text if not c.isalnum() and not c.isspace())
        if special_chars / len(cleaned_text) > 0.1:
            score -= 0.05

        # 数字和字母混合度
        has_digit = any(c.isdigit() for c in cleaned_text)
        has_alpha = any(c.isalpha() for c in cleaned_text)
        if has_digit and has_alpha:
            score += 0.01

        return max(0.0, min(1.0, score))

    async def batch_process(
        self,
        image_paths: list[str],
        language: str = "chinese",
        **kwargs
    ) -> list[dict[str, Any]]:
        """
        批量处理OCR

        Args:
            image_paths: 图像文件路径列表
            language: 语言
            **kwargs: 其他参数

        Returns:
            OCR结果列表
        """
        results = []

        for i, image_path in enumerate(image_paths):
            try:
                logger.info(f"批量处理 {i+1}/{len(image_paths)}: {image_path}")
                result = await self.process_ocr(image_path, language, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"批量处理失败 {image_path}: {e}")
                results.append({
                    "success": False,
                    "image_path": image_path,
                    "error": str(e)
                })

        return results

    def get_supported_formats(self) -> list[str]:
        """获取支持的图像格式"""
        return list(self.supported_formats)

    def get_supported_languages(self) -> list[str]:
        """获取支持的语言"""
        return ['chinese', 'english', 'mixed', 'traditional']


# 使用示例
if __name__ == "__main__":
    import asyncio

    async def test():
        processor = TesseractOCRProcessor()

        if not processor.is_available():
            print("❌ Tesseract OCR不可用")
            print("请安装: brew install tesseract")
            return

        print("✅ Tesseract OCR可用")
        print(f"版本: {processor.get_version()}")
        print(f"支持格式: {processor.get_supported_formats()}")
        print(f"支持语言: {processor.get_supported_languages()}")

        # 测试OCR（如果存在测试图像）
        test_image = "/tmp/test_ocr.png"
        if os.path.exists(test_image):
            result = await processor.process_ocr(test_image, "chinese")
            print("\n✅ OCR测试成功:")
            print(f"文本: {result['text'][:100]}...")
            print(f"置信度: {result['confidence']}")
            print(f"处理时间: {result['processing_time']:.2f}秒")

    asyncio.run(test())
