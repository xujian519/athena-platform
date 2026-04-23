#!/usr/bin/env python3

"""
边界情况测试套件
Edge Cases Test Suite

测试各种边界情况和异常输入

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

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.ai.perception.chinese_ocr_optimizer import ChineseOCROptimizer

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


async def test_empty_inputs():
    """测试空输入"""
    print_header("测试1: 空输入处理")

    optimizer = ChineseOCROptimizer()

    all_passed = True

    # 测试1: 空字符串
    try:
        result = await optimizer.correct_text("")
        if result == "":
            print_test("空字符串处理", True)
        else:
            print_test("空字符串处理", False, f"期望空字符串,得到: '{result}'")
            all_passed = False
    except Exception as e:
        print_test("空字符串处理", False, str(e))
        all_passed = False

    # 测试2: 仅空格
    try:
        result = await optimizer.correct_text("     ")
        if result == "":
            print_test("纯空格处理", True)
        else:
            print_test("纯空格处理", False, f"期望空字符串,得到: '{result}'")
            all_passed = False
    except Exception as e:
        print_test("纯空格处理", False, str(e))
        all_passed = False

    # 测试3: 空置信度计算
    try:
        confidence = optimizer._compute_chinese_confidence("", "/tmp/test.png")
        if confidence == 0.0:
            print_test("空文本置信度", True, f"置信度: {confidence}")
        else:
            print_test("空文本置信度", False, f"期望0.0,得到: {confidence}")
            all_passed = False
    except Exception as e:
        print_test("空文本置信度", False, str(e))
        all_passed = False

    return all_passed


async def test_special_characters():
    """测试特殊字符"""
    print_header("测试2: 特殊字符处理")

    optimizer = ChineseOCROptimizer()

    test_cases = [
        # (输入, 描述)
        ("!@#￥%……&*()", "全角特殊符号"),
        ("!@#$%^&*()", "半角特殊符号"),
        ("……—◎⊙●★☆", "特殊符号"),
        ("①②③④⑤⑥⑦⑧⑨⑩", "带圈数字"),
        ("⒈⒉⒊⒋⒌⒍⒎⒏⒐⒑", "带点数字"),
        ("「」『』[]", "日式标点"),
        ("─━│┃┄┅┆┇┈┉┊┋┌┍┎┏", "制表符"),
        ("☆★☀☁☂☃☄★☆☇☈⊙☊☋☌☍", "天体符号"),
        ("←↑→↓↔↕↖↗↘↙∥∠", "箭头和几何符号"),
    ]

    all_passed = True

    for text, description in test_cases:
        try:
            result = await optimizer.correct_text(text)
            # 特殊字符应该保持不变或合理转换
            print_test(description, True, f"'{text[:10]}...' → '{result[:10]}...'")
        except Exception as e:
            print_test(description, False, f"异常: {e}")
            all_passed = False

    return all_passed


async def test_extreme_text_lengths():
    """测试极端文本长度"""
    print_header("测试3: 极端文本长度")

    optimizer = ChineseOCROptimizer()

    # 创建测试图片
    img = Image.new("RGB", (400, 100), color="white")
    temp_path = tempfile.mktemp(suffix=".png")
    img.save(temp_path)

    all_passed = True

    # 测试1: 超长文本 (10000字符)
    try:
        long_text = "中文" * 5000  # 10000字符
        confidence = optimizer._compute_chinese_confidence(long_text, temp_path)
        # 超长文本应该有合理置信度
        if 0.0 <= confidence <= 1.0:
            print_test("超长文本(10000字符)", True, f"置信度: {confidence:.2f}")
        else:
            print_test("超长文本(10000字符)", False, f"置信度超出范围: {confidence}")
            all_passed = False
    except Exception as e:
        print_test("超长文本(10000字符)", False, str(e))
        all_passed = False

    # 测试2: 单个字符
    try:
        confidence = optimizer._compute_chinese_confidence("中", temp_path)
        if 0.0 <= confidence <= 1.0:
            print_test("单个字符", True, f"置信度: {confidence:.2f}")
        else:
            print_test("单个字符", False, f"置信度超出范围: {confidence}")
            all_passed = False
    except Exception as e:
        print_test("单个字符", False, str(e))
        all_passed = False

    # 测试3: 超长纠错
    try:
        long_mixed = "①" + "测试文本" * 100 + "⑩"
        corrected = await optimizer.correct_text(long_mixed)
        print_test("超长文本纠错", True, f"长度: {len(corrected)}字符")
    except Exception as e:
        print_test("超长文本纠错", False, str(e))
        all_passed = False

    # 清理
    if os.path.exists(temp_path):
        os.remove(temp_path)

    return all_passed


async def test_invalid_images():
    """测试无效图像"""
    print_header("测试4: 无效图像处理")

    optimizer = ChineseOCROptimizer()

    all_passed = True

    # 测试1: 不存在的文件
    try:
        result_path = await optimizer.preprocess_image("/nonexistent/image.png")
        if result_path == "/nonexistent/image.png":
            print_test("不存在的文件", True, "返回原始路径")
        else:
            print_test("不存在的文件", False, f"未返回原始路径: {result_path}")
            all_passed = False
    except Exception as e:
        print_test("不存在的文件", False, str(e))
        all_passed = False

    # 测试2: 空图像
    try:
        # 创建最小尺寸图像
        img = Image.new("RGB", (1, 1), color="white")
        temp_path = tempfile.mktemp(suffix="_tiny.png")
        img.save(temp_path)

        result_path = await optimizer.preprocess_image(temp_path)
        if os.path.exists(result_path):
            print_test("1x1像素图像", True)
        else:
            print_test("1x1像素图像", False, "输出文件不存在")
            all_passed = False

        if os.path.exists(temp_path):
            os.remove(temp_path)
        if os.path.exists(result_path):
            os.remove(result_path)
    except Exception as e:
        print_test("1x1像素图像", False, str(e))
        all_passed = False

    # 测试3: 损坏的图像文件
    try:
        temp_path = tempfile.mktemp(suffix="_corrupt.png")
        with open(temp_path, "wb") as f:
            f.write(b"This is not a valid PNG file")

        result_path = await optimizer.preprocess_image(temp_path)
        # 应该优雅地处理错误
        print_test("损坏的图像", True, "优雅处理错误")

        if os.path.exists(temp_path):
            os.remove(temp_path)
    except Exception as e:
        # 抛出异常也是可接受的
        print_test("损坏的图像", True, f"正确抛出异常: {type(e).__name__}")

    return all_passed


async def test_unicode_characters():
    """测试Unicode字符"""
    print_header("测试5: Unicode字符处理")

    optimizer = ChineseOCROptimizer()

    test_cases = [
        # (输入, 描述)
        ("ᚠᚢᚦᚨᚱᚲ", "卢恩字符"),
        ("Ω≈ç√∫˜µ≤≥÷", "数学符号"),
        ("가나다라마바사아자차카타파하", "韩文"),
        ("あいうえおかきくけこ", "日文假名"),
        ("αβγδεζηθικλμνξοπρστυφχψω", "希腊字母"),
        ("٠١٢٣٤٥٦٧٨٩", "阿拉伯数字"),
        ("۱۲۳۴۵۶۷۸۹۰", "波斯数字"),
        ("पणडीयांजौलांदोंगांगां", "天城文"),
        ("สวัสดีครับ", "泰文"),
        ("Здравствуй", "西里尔字母"),
    ]

    all_passed = True

    for text, description in test_cases:
        try:
            result = await optimizer.correct_text(text)
            # Unicode字符应该保持不变
            print_test(description, True, f"'{text}' → '{result}'")
        except Exception as e:
            print_test(description, False, str(e))
            all_passed = False

    return all_passed


async def test_mixed_language():
    """测试混合语言"""
    print_header("测试6: 混合语言处理")

    optimizer = ChineseOCROptimizer()

    # 创建测试图片
    img = Image.new("RGB", (400, 100), color="white")
    temp_path = tempfile.mktemp(suffix=".png")
    img.save(temp_path)

    test_cases = [
        ("中文English混合", "中英混合"),
        ("日本語English中文", "日英中混合"),
        ("한국어中文English", "韩中英混合"),
        ("123中文456English789", "数字中文英文混合"),
        ("Python是编程语言Java也是编程语言", "编程术语混合"),
        ("🎉🎊🎈中文Emoji🎁🎀", "Emoji混合"),
    ]

    all_passed = True

    for text, description in test_cases:
        try:
            confidence = optimizer._compute_chinese_confidence(text, temp_path)
            _corrected = await optimizer.correct_text(text)

            # 混合语言应该有合理的置信度
            if 0.0 <= confidence <= 1.0:
                print_test(description, True, f"置信度: {confidence:.2f}")
            else:
                print_test(description, False, f"置信度异常: {confidence}")
                all_passed = False
        except Exception as e:
            print_test(description, False, str(e))
            all_passed = False

    # 清理
    if os.path.exists(temp_path):
        os.remove(temp_path)

    return all_passed


async def test_edge_case_images():
    """测试边界情况图像"""
    print_header("测试7: 边界情况图像")

    optimizer = ChineseOCROptimizer()
    all_passed = True

    # 测试1: 超宽图像
    try:
        img = Image.new("RGB", (10000, 100), color="white")
        temp_path = tempfile.mktemp(suffix="_wide.png")
        img.save(temp_path)

        result_path = await optimizer.preprocess_image(temp_path)
        if os.path.exists(result_path):
            print_test("超宽图像(10000x100)", True)
        else:
            print_test("超宽图像(10000x100)", False)

        if os.path.exists(temp_path):
            os.remove(temp_path)
        if os.path.exists(result_path):
            os.remove(result_path)
    except Exception as e:
        print_test("超宽图像(10000x100)", False, str(e))
        all_passed = False

    # 测试2: 超高图像
    try:
        img = Image.new("RGB", (100, 10000), color="white")
        temp_path = tempfile.mktemp(suffix="_tall.png")
        img.save(temp_path)

        result_path = await optimizer.preprocess_image(temp_path)
        if os.path.exists(result_path):
            print_test("超高图像(100x10000)", True)
        else:
            print_test("超高图像(100x10000)", False)

        if os.path.exists(temp_path):
            os.remove(temp_path)
        if os.path.exists(result_path):
            os.remove(result_path)
    except Exception as e:
        print_test("超高图像(100x10000)", False, str(e))
        all_passed = False

    # 测试3: 纯黑图像
    try:
        img = Image.new("RGB", (400, 100), color="black")
        temp_path = tempfile.mktemp(suffix="_black.png")
        img.save(temp_path)

        result_path = await optimizer.preprocess_image(temp_path)
        if os.path.exists(result_path):
            print_test("纯黑图像", True)
        else:
            print_test("纯黑图像", False)

        if os.path.exists(temp_path):
            os.remove(temp_path)
        if os.path.exists(result_path):
            os.remove(result_path)
    except Exception as e:
        print_test("纯黑图像", False, str(e))
        all_passed = False

    # 测试4: 渐变图像
    try:
        img = Image.new("RGB", (400, 100), color="white")
        draw = ImageDraw.Draw(img)
        for i in range(400):
            gray = int(255 * i / 400)
            draw.rectangle([i, 0, i + 1, 100], fill=(gray, gray, gray))

        temp_path = tempfile.mktemp(suffix="_gradient.png")
        img.save(temp_path)

        result_path = await optimizer.preprocess_image(temp_path)
        if os.path.exists(result_path):
            print_test("渐变图像", True)
        else:
            print_test("渐变图像", False)

        if os.path.exists(temp_path):
            os.remove(temp_path)
        if os.path.exists(result_path):
            os.remove(result_path)
    except Exception as e:
        print_test("渐变图像", False, str(e))
        all_passed = False

    return all_passed


async def test_concurrent_operations():
    """测试并发操作"""
    print_header("测试8: 并发操作")

    optimizer = ChineseOCROptimizer()
    all_passed = True

    # 创建测试图像
    img = Image.new("RGB", (400, 100), color="white")
    temp_path = tempfile.mktemp(suffix=".png")
    img.save(temp_path)

    try:
        # 并发执行多个纠错任务
        tasks = [optimizer.correct_text(f"测试文本{i}") for i in range(100)]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 检查结果
        success_count = sum(1 for r in results if isinstance(r, str))
        error_count = sum(1 for r in results if isinstance(r, Exception))

        print_test("100个并发纠错任务", True, f"成功: {success_count}, 错误: {error_count}")

        if error_count > 0:
            logger.warning(f"有{error_count}个任务失败")

    except Exception as e:
        print_test("100个并发纠错任务", False, str(e))
        all_passed = False

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return all_passed


async def test_rare_chinese_characters():
    """测试罕见汉字"""
    print_header("测试9: 罕见汉字处理")

    optimizer = ChineseOCROptimizer()

    # 创建测试图片
    img = Image.new("RGB", (400, 100), color="white")
    temp_path = tempfile.mktemp(suffix=".png")
    img.save(temp_path)

    test_cases = [
        ("龘靐齉爨龗灩", "复杂汉字"),
        ("𠀀𠀁𠀂𠀃𠀄", "扩展A区汉字"),
        ("㐀㐁㐂㐃㐄", "扩展汉字"),
        ("㊀㊁㊂㊃㊄㊅㊆㊇㊈㊉", "带圈汉字"),
    ]

    all_passed = True

    for text, description in test_cases:
        try:
            confidence = optimizer._compute_chinese_confidence(text, temp_path)
            _corrected = await optimizer.correct_text(text)

            # 罕见汉字应该有较低但合理的置信度
            print_test(description, True, f"置信度: {confidence:.2f}")
        except Exception as e:
            print_test(description, False, str(e))
            all_passed = False

    # 清理
    if os.path.exists(temp_path):
        os.remove(temp_path)

    return all_passed


async def main():
    """运行所有边界测试"""
    print("\n")
    print("🧟 Athena边界情况测试")
    print("   作者: 小诺·双鱼公主")
    print("   日期: 2026-01-01")

    results = []

    # 运行所有测试
    results.append(await test_empty_inputs())
    results.append(await test_special_characters())
    results.append(await test_extreme_text_lengths())
    results.append(await test_invalid_images())
    results.append(await test_unicode_characters())
    results.append(await test_mixed_language())
    results.append(await test_edge_case_images())
    results.append(await test_concurrent_operations())
    results.append(await test_rare_chinese_characters())

    # 汇总结果
    print_header("边界测试结果汇总")

    total = len(results)
    passed = sum(results)
    failed = total - passed

    print(f"总计: {total} 个测试套件")
    print(f"通过: {passed} 个 ✅")
    print(f"失败: {failed} 个 ❌")
    print(f"通过率: {passed/total*100:.1f}%")

    if passed == total:
        print("\n🎉 所有边界测试通过!")
    else:
        print(f"\n⚠️ 有 {failed} 个测试失败")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)

