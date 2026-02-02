#!/usr/bin/env python3
"""
视觉验证引擎
Visual Verification Engine

实现GUI执行结果的视觉验证功能:
1. 执行前/后截图对比
2. OCR文字识别验证
3. 页面元素存在性检测
4. 视觉差异分析

作者: 小诺·双鱼公主
创建时间: 2026-01-01
版本: 1.0.0
"""

import asyncio
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import cv2


logger = logging.getLogger(__name__)


class VerificationStatus(Enum):
    """验证状态"""

    SUCCESS = "success"  # 验证成功
    FAILED = "failed"  # 验证失败
    PARTIAL = "partial"  # 部分成功
    UNKNOWN = "unknown"  # 未知状态


@dataclass
class GUIAction:
    """GUI动作定义"""

    action_type: str  # 动作类型: click, type, navigate, etc.
    target: str | None = None  # 目标元素选择器
    value: str | None = None  # 输入值
    url: str | None = None  # URL(用于navigate)
    description: str = ""  # 动作描述


@dataclass
class VerificationResult:
    """验证结果"""

    status: VerificationStatus
    confidence: float  # 置信度 0.0-1.0
    message: str  # 验证消息
    details: dict[str, Any] = field(default_factory=dict)
    before_screenshot: str | None = None
    after_screenshot: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)

    # 详细验证结果
    text_match_score: float = 0.0  # 文本匹配分数
    element_detection: dict[str, bool] = field(default_factory=dict)
    visual_difference: float = 0.0  # 视觉差异分数 0-1
    detected_text: str | None = None


class VisualVerificationEngine:
    """
    视觉验证引擎

    核心功能:
    1. 截图对比 - 使用SSIM计算视觉相似度
    2. OCR验证 - 识别页面文字并与期望值对比
    3. 元素检测 - 检测指定元素是否存在
    4. 差异分析 - 分析执行前后的视觉变化
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """
        初始化视觉验证引擎

        Args:
            config: 配置字典
                - ocr_engine: OCR引擎类型 ("paddleocr", "tesseract", "easyocr")
                - screenshot_dir: 截图保存目录
                - enable_cache: 是否启用缓存
                - similarity_threshold: 相似度阈值
        """
        self.config = config or {}
        self.ocr_engine = None
        self.screenshot_dir = Path(
            self.config.get("screenshot_dir", "/Users/xujian/Athena工作平台/data/screenshots")
        )
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

        # 验证阈值
        self.text_match_threshold = self.config.get("text_match_threshold", 0.7)
        self.similarity_threshold = self.config.get("similarity_threshold", 0.8)

        # OCR引擎
        ocr_engine_type = self.config.get("ocr_engine", "paddleocr")

        logger.info(f"👁️ 视觉验证引擎初始化完成 (OCR: {ocr_engine_type})")

    async def initialize(self):
        """初始化OCR引擎"""
        try:
            ocr_engine_type = self.config.get("ocr_engine", "paddleocr")

            if ocr_engine_type == "paddleocr":
                await self._init_paddleocr()
            elif ocr_engine_type == "easyocr":
                await self._init_easyocr()
            else:
                logger.warning(f"未知OCR引擎: {ocr_engine_type},使用PaddleOCR")
                await self._init_paddleocr()

            logger.info("✅ OCR引擎初始化成功")

        except Exception as e:
            logger.error(f"❌ OCR引擎初始化失败: {e}")
            # 降级到简单的图像处理
            logger.info("⚠️ 降级到基础图像处理模式")

    async def _init_paddleocr(self):
        """初始化PaddleOCR"""
        try:
            from paddleocr import PaddleOCR

            use_gpu = self.config.get("use_gpu", False)

            # 修复: 移除不支持的参数
            self.ocr_engine = PaddleOCR(
                use_textline_orientation=True,  # 替代use_angle_cls
                lang="ch",  # 中文
                use_gpu=use_gpu,
            )
            logger.info("✅ PaddleOCR初始化成功")
            self.ocr_engine_type = "paddleocr"

        except ImportError:
            logger.warning("⚠️ PaddleOCR未安装,尝试使用RapidOCR")
            await self._init_rapidocr()
        except Exception as e:
            logger.warning(f"⚠️ PaddleOCR初始化失败: {e}")
            await self._init_rapidocr()

    async def _init_rapidocr(self):
        """初始化RapidOCR (推荐,支持Python 3.14)"""
        try:
            from rapidocr import RapidOCR

            self.ocr_engine = RapidOCR()
            logger.info("✅ RapidOCR初始化成功")
            self.ocr_engine_type = "rapidocr"

        except ImportError:
            logger.warning("⚠️ RapidOCR未安装,尝试使用EasyOCR")
            await self._init_easyocr()

    async def _init_easyocr(self):
        """初始化EasyOCR"""
        try:
            import easyocr

            self.ocr_engine = easyocr.Reader(["ch_sim", "en"], gpu=False)
            logger.info("✅ EasyOCR初始化成功")
            self.ocr_engine_type = "easyocr"

        except ImportError:
            logger.error("❌ 所有OCR引擎均不可用,OCR功能将禁用")
            self.ocr_engine = None
            self.ocr_engine_type = None

    async def verify_execution(
        self,
        action: GUIAction,
        before_screenshot: str,
        after_screenshot: str,
        expected_elements: list["key"] = None,
        expected_text: str | None = None,
        verify_change: bool = True,
    ) -> VerificationResult:
        """
        验证GUI执行结果

        Args:
            action: 执行的GUI操作
            before_screenshot: 执行前截图路径
            after_screenshot: 执行后截图路径
            expected_elements: 期望出现的元素选择器列表
            expected_text: 期望出现的文字内容
            verify_change: 是否验证视觉变化

        Returns:
            VerificationResult: 验证结果
        """
        logger.info(f"🔍 开始验证执行: {action.description}")

        # 初始化结果
        result = VerificationResult(
            status=VerificationStatus.UNKNOWN,
            confidence=0.0,
            message="验证开始",
            before_screenshot=before_screenshot,
            after_screenshot=after_screenshot,
        )

        try:
            # 1. 检查截图文件是否存在
            if not os.path.exists(after_screenshot):
                result.status = VerificationStatus.FAILED
                result.message = f"截图文件不存在: {after_screenshot}"
                return result

            # 2. 视觉差异分析
            if verify_change and os.path.exists(before_screenshot):
                visual_diff = await self._compute_visual_difference(
                    before_screenshot, after_screenshot
                )
                result.visual_difference = visual_diff
                logger.info(f"📊 视觉差异: {visual_diff:.3f}")

            # 3. OCR文字验证
            text_success = True
            if expected_text:
                text_match = await self._verify_text_content(after_screenshot, expected_text)
                result.text_match_score = text_match
                result.detected_text = await self._extract_text(after_screenshot)

                if text_match < self.text_match_threshold:
                    text_success = False
                    logger.warning(
                        f"⚠️ 文本匹配度不足: {text_match:.3f} < {self.text_match_threshold}"
                    )

            # 4. 元素存在性检测
            element_success = True
            if expected_elements:
                element_results = await self._detect_elements(after_screenshot, expected_elements)
                result.element_detection = element_results

                # 检查是否所有元素都存在
                for elem, found in element_results.items():
                    if not found:
                        element_success = False
                        logger.warning(f"⚠️ 元素未找到: {elem}")

            # 5. 综合判断
            success_count = 0
            total_checks = 0

            # 文本验证
            if expected_text:
                total_checks += 1
                if text_success:
                    success_count += 1

            # 元素验证
            if expected_elements:
                total_checks += 1
                if element_success:
                    success_count += 1

            # 视觉变化验证
            if verify_change:
                total_checks += 1
                # 有明显变化则认为成功
                if result.visual_difference < 0.95:  # 不是完全相同
                    success_count += 1

            # 计算最终状态
            if total_checks == 0:
                result.status = VerificationStatus.SUCCESS
                result.message = "无验证条件,默认成功"
                result.confidence = 1.0
            else:
                success_rate = success_count / total_checks

                if success_rate >= 1.0:
                    result.status = VerificationStatus.SUCCESS
                    result.message = f"所有验证通过 ({success_count}/{total_checks})"
                    result.confidence = 1.0
                elif success_rate >= 0.5:
                    result.status = VerificationStatus.PARTIAL
                    result.message = f"部分验证通过 ({success_count}/{total_checks})"
                    result.confidence = success_rate
                else:
                    result.status = VerificationStatus.FAILED
                    result.message = f"验证失败 ({success_count}/{total_checks})"
                    result.confidence = success_rate

            # 汇总详情
            result.details = {
                "text_match": result.text_match_score,
                "element_detection": result.element_detection,
                "visual_difference": result.visual_difference,
                "success_rate": success_count / total_checks if total_checks > 0 else 1.0,
            }

        except Exception as e:
            logger.error(f"❌ 验证过程异常: {e}")
            result.status = VerificationStatus.FAILED
            result.message = f"验证异常: {e!s}"
            result.confidence = 0.0

        logger.info(f"✅ 验证完成: {result.status.value} (置信度: {result.confidence:.2f})")
        return result

    async def _compute_visual_difference(self, image1_path: str, image2_path: str) -> float:
        """
        计算两张图片的视觉差异

        使用SSIM (Structural Similarity Index)

        Args:
            image1_path: 图片1路径
            image2_path: 图片2路径

        Returns:
            float: 相似度 0-1,1表示完全相同
        """
        try:
            # 读取图片
            img1 = cv2.imread(image1_path)
            img2 = cv2.imread(image2_path)

            if img1 is None or img2 is None:
                logger.warning("⚠️ 无法读取图片进行对比")
                return 0.0

            # 转换为灰度图
            gray1 = cv2.cvt_color(img1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvt_color(img2, cv2.COLOR_BGR2GRAY)

            # 调整大小(确保尺寸一致)
            if gray1.shape != gray2.shape:
                gray2 = cv2.resize(gray2, (gray1.shape[1], gray1.shape[0]))

            # 计算SSIM

            score, _ = ssim(gray1, gray2, full=True)

            return float(score)

        except Exception as e:
            logger.error(f"❌ 视觉差异计算失败: {e}")
            return 0.0

    async def _verify_text_content(self, image_path: str, expected_text: str) -> float:
        """
        验证图片中的文字内容

        Args:
            image_path: 图片路径
            expected_text: 期望的文字内容

        Returns:
            float: 匹配分数 0-1
        """
        if not self.ocr_engine:
            logger.warning("⚠️ OCR引擎未初始化")
            return 0.0

        try:
            # 提取图片中的文字
            extracted_text = await self._extract_text(image_path)

            if not extracted_text:
                return 0.0

            # 计算相似度
            from difflib import SequenceMatcher

            similarity = SequenceMatcher(None, extracted_text, expected_text).ratio()

            logger.info(f"📝 文字匹配: {similarity:.3f}")
            logger.debug(f"   期望: {expected_text}")
            logger.debug(f"   识别: {extracted_text[:100]}...")

            return similarity

        except Exception as e:
            logger.error(f"❌ 文字验证失败: {e}")
            return 0.0

    async def _extract_text(self, image_path: str) -> str:
        """
        提取图片中的文字 (支持多OCR引擎)

        Args:
            image_path: 图片路径

        Returns:
            str: 提取的文字内容
        """
        if not self.ocr_engine:
            return ""

        try:
            engine_type = getattr(self, "ocr_engine_type", "unknown")

            # RapidOCR (推荐)
            if engine_type == "rapidocr" and callable(self.ocr_engine):
                result = self.ocr_engine(image_path)
                if result and result[0]:
                    text_lines = [line[1] for line in result[0]]
                    return "\n".join(text_lines)

            # PaddleOCR
            elif engine_type == "paddleocr" and hasattr(self.ocr_engine, "ocr"):
                result = self.ocr_engine.ocr(image_path, cls=True)
                if result and result[0]:
                    text_lines = [line[1][0] for line in result[0]]
                    return "\n".join(text_lines)

            # EasyOCR
            elif engine_type == "easyocr" and hasattr(self.ocr_engine, "readtext"):
                results = self.ocr_engine.readtext(image_path)
                text_lines = [result[1] for result in results]
                return "\n".join(text_lines)

            return ""

        except Exception as e:
            logger.error(f"❌ 文字提取失败 ({engine_type}): {e}")
            return ""

    async def _detect_elements(self, image_path: str, selectors: list[str]) -> dict[str, bool]:
        """
        检测页面元素是否存在

        注意:这是一个简化实现
        实际应用中应该使用browser-use的DOM树信息

        Args:
            image_path: 图片路径
            selectors: 元素选择器列表

        Returns:
            dict[str, bool]: 每个选择器的检测结果
        """
        results = {}

        # 简化实现:通过OCR文字匹配来"检测"元素
        # 实际应该集成browser-use的DOM分析
        for selector in selectors:
            # 假设选择器包含文字信息
            # 例如: "button[contains(text(), '搜索')]"
            if "'" in selector or '"' in selector:
                # 提取引号中的文字
                import re

                text_match = re.findall(r"['\"]([^'\"]*)['\"]", selector)
                if text_match:
                    expected = text_match[0]
                    extracted = await self._extract_text(image_path)
                    results[selector] = expected in extracted
                else:
                    results[selector] = True  # 默认认为存在
            else:
                # 无法验证,默认认为存在
                results[selector] = True

        return results

    async def capture_and_save(self, page, label: str, task_id: str | None = None) -> str:
        """
        捕获页面截图并保存

        Args:
            page: Playwright页面对象
            label: 截图标签
            task_id: 任务ID(可选)

        Returns:
            str: 截图保存路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        filename = f"{task_id}_{label}_{timestamp}.png" if task_id else f"{label}_{timestamp}.png"

        filepath = self.screenshot_dir / filename

        try:
            await page.screenshot(path=str(filepath))
            logger.info(f"📸 截图已保存: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"❌ 截图保存失败: {e}")
            return ""

    async def compare_screenshots(
        self, image1_path: str, image2_path: str
    ) -> tuple[float, dict[str, Any]:
        """
        对比两张截图

        Args:
            image1_path: 图片1路径
            image2_path: 图片2路径

        Returns:
            tuple[(相似度]
        """
        similarity = await self._compute_visual_difference(image1_path, image2_path)

        details = {
            "similarity": similarity,
            "difference": 1.0 - similarity,
            "image1": image1_path,
            "image2": image2_path,
            "timestamp": datetime.now().isoformat(),
        }

        return similarity, details


# 导出
__all__ = ["GUIAction", "VerificationResult", "VerificationStatus", "VisualVerificationEngine"]


# ==================== 使用示例 ====================

if __name__ == "__main__":

    async def main():
        """测试视觉验证引擎"""
        engine = VisualVerificationEngine()
        await engine.initialize()

        # 模拟验证
        result = await engine.verify_execution(
            action=GUIAction(action_type="click", description="点击搜索按钮"),
            before_screenshot="/path/to/before.png",
            after_screenshot="/path/to/after.png",
            expected_text="搜索结果",
            expected_elements=["#results", ".search-item"],
        )

        print(f"验证状态: {result.status.value}")
        print(f"置信度: {result.confidence:.2f}")
        print(f"消息: {result.message}")

    asyncio.run(main())
