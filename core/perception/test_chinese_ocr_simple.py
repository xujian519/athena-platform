#!/usr/bin/env python3
from __future__ import annotations
"""
中文OCR优化简化测试
Chinese OCR Optimization Simple Tests

不依赖外部OCR引擎的测试

作者: 小诺·双鱼公主
创建时间: 2026-01-01
"""

import asyncio
import logging
import os

# 导入测试模块
import sys
import tempfile
from pathlib import Path

import cv2
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.perception.chinese_ocr_optimizer import ChineseOCROptimizer, GUITextExtractor, OCRResult

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def print_header(title) -> None:
    """打印标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_test(name, passed, details="") -> None:
    """打印测试结果"""
    status = "✅ 通过" if passed else "❌ 失败"
    print(f"{status} - {name}")
    if details:
        print(f"     {details}")


async def test_text_correction():
    """测试文本纠错"""
    print_header("测试1: 文本纠错")

    optimizer = ChineseOCROptimizer()

    test_cases = [
        ("①②③", "数字符号转汉字"),
        ("人工智Neng", "混合字符"),
        ("这  是  测  试", "空格规范化"),
        ("测试,文本。", "标点符号规范化"),
    ]

    all_passed = True
    for text, description in test_cases:
        try:
            corrected = await optimizer.correct_text(text)
            print_test(description, True, f"'{text}' → '{corrected}'")
        except Exception as e:
            print_test(description, False, str(e))
            all_passed = False

    return all_passed


async def test_confidence_scoring():
    """测试置信度评分"""
    print_header("测试2: 置信度评分")

    optimizer = ChineseOCROptimizer()

    # 创建测试图片
    img = Image.new("RGB", (400, 100), color="white")
    temp_path = tempfile.mktemp(suffix=".png")
    img.save(temp_path)

    test_cases = [
        ("这是中文测试文本", "高质量中文", 0.8),
        ("This is English", "英文文本", 0.5),
        ("", "空文本", 0.0),
        ("混合Mixed文本Text", "混合文本", 0.6),
    ]

    all_passed = True
    for text, description, min_confidence in test_cases:
        try:
            confidence = optimizer._compute_chinese_confidence(text, temp_path)
            passed = 0.0 <= confidence <= 1.0
            if passed and min_confidence > 0:
                passed = confidence >= min_confidence

            print_test(description, passed, f"置信度: {confidence:.2f}")
            if not passed:
                all_passed = False
        except Exception as e:
            print_test(description, False, str(e))
            all_passed = False

    # 清理
    if os.path.exists(temp_path):
        os.remove(temp_path)

    return all_passed


async def test_image_preprocessing():
    """测试图像预处理"""
    print_header("测试3: 图像预处理")

    optimizer = ChineseOCROptimizer()

    # 创建测试图片
    img = Image.new("RGB", (400, 100), color="white")
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), "测试文本", fill="black")

    input_path = tempfile.mktemp(suffix=".png")
    output_path = tempfile.mktemp(suffix="_preprocessed.png")
    img.save(input_path)

    all_passed = True

    try:
        # 测试预处理
        result_path = await optimizer.preprocess_image(input_path, output_path)

        if os.path.exists(result_path):
            # 检查输出图像
            processed = cv2.imread(result_path)
            if processed is not None:
                print_test("图像预处理", True, f"输出: {result_path}")
                print(f"     原始尺寸: {img.size}, 处理后尺寸: {processed.shape[:2][::-1]}")
            else:
                print_test("图像预处理", False, "无法读取处理后的图像")
                all_passed = False
        else:
            print_test("图像预处理", False, "输出文件不存在")
            all_passed = False

    except Exception as e:
        print_test("图像预处理", False, str(e))
        all_passed = False

    finally:
        # 清理
        for path in [input_path, output_path]:
            if os.path.exists(path):
                os.remove(path)

    return all_passed


async def test_gui_text_extractor():
    """测试GUI文本提取器"""
    print_header("测试4: GUI文本提取器")

    extractor = GUITextExtractor()

    # 创建模拟GUI图像
    img = Image.new("RGB", (800, 600), color="#f0f0f0")
    draw = ImageDraw.Draw(img)

    # 绘制标题区域
    draw.rectangle([50, 50, 750, 100], fill="#333333")
    draw.text((400, 75), "页面标题", fill="white", anchor="mm")

    # 保存到临时文件
    temp_path = tempfile.mktemp(suffix="_gui.png")
    img.save(temp_path)

    all_passed = True

    try:
        # 测试区域检测
        cv_img = cv2.imread(temp_path)

        # 测试标题区域检测
        title_regions = extractor._detect_title_area(cv_img)
        if len(title_regions) > 0:
            print_test("标题区域检测", True, f"检测到 {len(title_regions)} 个区域")
            print(f"     标题区域尺寸: {title_regions[0].shape}")
        else:
            print_test("标题区域检测", False, "未检测到标题区域")
            all_passed = False

        # 测试按钮区域检测
        button_regions = extractor._detect_button_area(cv_img)
        if len(button_regions) > 0:
            print_test("按钮区域检测", True, f"检测到 {len(button_regions)} 个区域")
        else:
            print_test("按钮区域检测", False, "未检测到按钮区域")
            all_passed = False

    except Exception as e:
        print_test("GUI文本提取器", False, str(e))
        all_passed = False

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return all_passed


async def test_optimization_pipeline():
    """测试完整优化流程"""
    print_header("测试5: 完整优化流程")

    optimizer = ChineseOCROptimizer()

    # 创建测试图像
    img = Image.new("RGB", (400, 100), color="white")
    temp_path = tempfile.mktemp(suffix=".png")
    img.save(temp_path)

    all_passed = True

    try:
        # 执行完整优化流程
        raw_text = "①②③ 测试文本"
        result = await optimizer.optimize_chinese_text(temp_path, raw_result=raw_text)

        # 验证结果
        checks = [
            (isinstance(result, OCRResult), "返回OCRResult对象"),
            (isinstance(result.text, str), "文本是字符串"),
            (0.0 <= result.confidence <= 1.0, "置信度在0-1范围内"),
            (result.engine == "optimized_chinese", "引擎名称正确"),
        ]

        for check, description in checks:
            if check:
                print_test(description, True)
            else:
                print_test(description, False)
                all_passed = False

        print(f"     优化结果: '{result.text}'")
        print(f"     置信度: {result.confidence:.2f}")
        print(f"     引擎: {result.engine}")

    except Exception as e:
        print_test("完整优化流程", False, str(e))
        all_passed = False

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return all_passed


async def test_common_chinese_boost():
    """测试常见汉字加分"""
    print_header("测试6: 常见汉字加分")

    optimizer = ChineseOCROptimizer()

    # 创建测试图片
    img = Image.new("RGB", (400, 100), color="white")
    temp_path = tempfile.mktemp(suffix=".png")
    img.save(temp_path)

    all_passed = True

    try:
        # 常见汉字 vs 罕见汉字
        common_text = "的一是在不了有和人这中大为"
        rare_text = "乂丿亐亗亓"

        common_conf = optimizer._compute_chinese_confidence(common_text, temp_path)
        rare_conf = optimizer._compute_chinese_confidence(rare_text, temp_path)

        print(f"     常见字置信度: {common_conf:.2f}")
        print(f"     罕见字置信度: {rare_conf:.2f}")

        if common_conf > rare_conf:
            print_test("常见汉字加分", True, "常见字置信度更高")
        else:
            print_test(
                "常见汉字加分", False, f"常见字({common_conf:.2f})未高于罕见字({rare_conf:.2f})"
            )
            all_passed = False

    except Exception as e:
        print_test("常见汉字加分", False, str(e))
        all_passed = False

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return all_passed


async def main():
    """运行所有测试"""
    print("\n")
    print("🧟 Athena中文OCR优化测试")
    print("   作者: 小诺·双鱼公主")
    print("   日期: 2026-01-01")

    results = []

    # 运行所有测试
    results.append(await test_text_correction())
    results.append(await test_confidence_scoring())
    results.append(await test_image_preprocessing())
    results.append(await test_gui_text_extractor())
    results.append(await test_optimization_pipeline())
    results.append(await test_common_chinese_boost())

    # 汇总结果
    print_header("测试结果汇总")

    total = len(results)
    passed = sum(results)
    failed = total - passed

    print(f"总计: {total} 个测试")
    print(f"通过: {passed} 个 ✅")
    print(f"失败: {failed} 个 ❌")
    print(f"通过率: {passed/total*100:.1f}%")

    if passed == total:
        print("\n🎉 所有测试通过!")
    else:
        print(f"\n⚠️ 有 {failed} 个测试失败")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
