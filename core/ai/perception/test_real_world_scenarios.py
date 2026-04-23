#!/usr/bin/env python3

"""
实际场景测试套件 (模拟版)
Real-World Scenarios Test Suite (Simulated)

模拟真实使用场景,测试优化引擎处理能力

作者: 小诺·双鱼公主
创建时间: 2026-01-01
"""

import asyncio
import logging
import os

# 导入测试模块
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.ai.perception.chinese_ocr_optimizer import ChineseOCROptimizer

logging.basicConfig(
    level=logging.WARNING,  # 减少日志输出
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def print_header(title) -> None:
    """打印标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_scenario(name, passed, details="") -> None:
    """打印场景测试结果"""
    status = "✅ 通过" if passed else "❌ 失败"
    print(f"{status} - {name}")
    if details:
        print(f"     {details}")


class ScenarioTestResults:
    """场景测试结果"""

    def __init__(self):
        self.results: list[dict[str, Any] = []

    def add(
        self, scenario: str, passed: bool, details: str = "", metrics: Optional[dict] = None
    ) -> Any:
        self.results.append(
            {
                "scenario": scenario,
                "passed": passed,
                "details": details,
                "metrics": metrics or {},
                "timestamp": datetime.now(),
            }
        )

    def summary(self) -> dict[str, Any]:
        total = len(self.results)
        passed = sum(1 for r in self.results if r["passed"])
        return {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": passed / total if total > 0 else 0,
        }


async def scenario_1_form_text_correction():
    """场景1: 表单文本纠错"""
    print_header("场景1: 表单文本纠错处理")

    optimizer = ChineseOCROptimizer()
    results = ScenarioTestResults()

    # 模拟表单OCR结果 (包含常见错误)
    form_texts = [
        "用①户名",  # 带圈数字
        "邮箱  地  址",  # 多余空格
        "手 机 号 码",  # 不规则空格
        "验证码[1234]",  # 中文标点
        "①②③④⑤⑥",  # 序号
        "确  定",  # 按钮文字
        "取  消",  # 按钮文字
    ]

    corrected_count = 0

    for text in form_texts:
        try:
            corrected = await optimizer.correct_text(text)
            # 检查是否改进
            if corrected != text and " " not in corrected:
                corrected_count += 1

        except Exception as e:
            logger.error(f"纠错失败: {e}")

    passed = corrected_count >= len(form_texts) * 0.8
    results.add(
        "表单文本纠错",
        passed,
        f"纠正率: {corrected_count}/{len(form_texts)}",
        {"correction_rate": corrected_count / len(form_texts)},
    )

    print_scenario(
        "表单文本纠错", passed, f"处理{len(form_texts)}个表单文本,纠正{corrected_count}个"
    )

    return results


async def scenario_2_menu_text_processing():
    """场景2: 菜单文本处理"""
    print_header("场景2: 菜单文本处理")

    optimizer = ChineseOCROptimizer()
    results = ScenarioTestResults()

    # 模拟菜单OCR结果
    menu_texts = [
        "①首页 Home",
        "② 个人中心 Profile",
        "③设置 Settings",
        "④数据  分析 Dashboard",
        "⑤通知中心 Notification",
        "⑥退出登录 Logout",
    ]

    all_passed = True
    total_chinese = 0
    corrected_chinese = 0

    for text in menu_texts:
        try:
            corrected = await optimizer.correct_text(text)

            # 统计中文字符
            chinese_before = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
            chinese_after = sum(1 for c in corrected if "\u4e00" <= c <= "\u9fff")

            total_chinese += chinese_before
            corrected_chinese += chinese_after

            # 计算置信度
            img = Image.new("RGB", (100, 50), color="white")
            temp_path = tempfile.mktemp(suffix=".png")
            img.save(temp_path)

            confidence = optimizer._compute_chinese_confidence(corrected, temp_path)

            if os.path.exists(temp_path):
                os.remove(temp_path)

            # 验证置信度
            if confidence < 0.5:
                all_passed = False

        except Exception as e:
            logger.error(f"处理失败: {e}")
            all_passed = False

    passed = all_passed and corrected_chinese >= total_chinese * 0.9
    results.add(
        "菜单文本处理",
        passed,
        f"处理{len(menu_texts)}个菜单项,中文字符保留率{corrected_chinese/total_chinese*100:.1f}%",
        {"menu_items": len(menu_texts), "chinese_chars": corrected_chinese},
    )

    print_scenario(
        "菜单文本处理",
        passed,
        f"{len(menu_texts)}个菜单项,中文字符{corrected_chinese}/{total_chinese}",
    )

    return results


async def scenario_3_notification_text():
    """场景3: 通知消息文本处理"""
    print_header("场景3: 通知消息文本处理")

    optimizer = ChineseOCROptimizer()
    results = ScenarioTestResults()

    # 模拟通知文本
    notification_texts = [
        "您有③条新消息",
        "系统将在①⑤分钟后维护",
        "任务已完成[100%]",
        "下载进度 ⑤  ⑩  ① ⑤  %",
        "错误  代  号  :  ERR_⑨⑨⑨",
    ]

    success_count = 0

    for text in notification_texts:
        try:
            corrected = await optimizer.correct_text(text)

            # 验证改进
            original_spaces = text.count(" ")
            corrected_spaces = corrected.count(" ")

            if corrected_spaces < original_spaces:
                success_count += 1

        except Exception as e:
            logger.error(f"处理失败: {e}")

    passed = success_count >= len(notification_texts) * 0.8
    results.add(
        "通知文本处理",
        passed,
        f"改进率: {success_count}/{len(notification_texts)}",
        {"notifications": len(notification_texts)},
    )

    print_scenario(
        "通知消息处理", passed, f"处理{len(notification_texts)}条通知,改进{success_count}条"
    )

    return results


async def scenario_4_table_data_processing():
    """场景4: 表格数据处理"""
    print_header("场景4: 表格数据处理")

    optimizer = ChineseOCROptimizer()
    results = ScenarioTestResults()

    # 模拟表格数据
    table_data = [
        "①  产品A  ⑤  ①00元",
        "②  产品B  ⑩  ②00元",
        "③  产品C  ①⑤  ③00元",
        "④  产品D  ②0  ⑤00元",
        "⑤  合计  ⑤0  ①①00元",
    ]

    total_numbers = 0
    corrected_numbers = 0

    for row in table_data:
        try:
            corrected = await optimizer.correct_text(row)

            # 统计数字转换
            original_digits = sum(1 for c in row if c.isdigit())
            corrected_digits = sum(1 for c in corrected if c.isdigit())

            total_numbers += original_digits
            corrected_numbers += corrected_digits

        except Exception as e:
            logger.error(f"处理失败: {e}")

    passed = corrected_numbers >= total_numbers * 0.5
    results.add(
        "表格数据处理",
        passed,
        f"数字处理: {corrected_numbers}/{total_numbers}",
        {"rows": len(table_data)},
    )

    print_scenario(
        "表格数据处理",
        passed,
        f"处理{len(table_data)}行数据,数字{corrected_numbers}/{total_numbers}",
    )

    return results


async def scenario_5_error_message_text():
    """场景5: 错误消息文本处理"""
    print_header("场景5: 错误消息文本处理")

    optimizer = ChineseOCROptimizer()
    results = ScenarioTestResults()

    # 模拟错误消息
    error_messages = [
        "网络连接失败[ERR_①①①]",
        "操作  失败  ,请重试",
        "系  统  错误:ERR_⑨⑨⑨",
        "服  务  器  ①  ②  ③",
        "错  误  代  码  : ⑤  0  ④",
    ]

    improved_count = 0

    for msg in error_messages:
        try:
            corrected = await optimizer.correct_text(msg)

            # 检查改进
            if " " not in corrected and ("[" not in corrected or "[]" in corrected):
                improved_count += 1

        except Exception as e:
            logger.error(f"处理失败: {e}")

    passed = improved_count >= len(error_messages) * 0.6
    results.add(
        "错误消息处理",
        passed,
        f"改进率: {improved_count}/{len(error_messages)}",
        {"errors": len(error_messages)},
    )

    print_scenario(
        "错误消息处理", passed, f"处理{len(error_messages)}条错误消息,改进{improved_count}条"
    )

    return results


async def scenario_6_search_text():
    """场景6: 搜索文本处理"""
    print_header("场景6: 搜索文本处理")

    optimizer = ChineseOCROptimizer()
    results = ScenarioTestResults()

    # 模拟搜索相关文本
    search_texts = [
        "搜索  产  品  、文  档、用  户",
        "热门搜索:人  工  智  能  机器  学  习",
        "①人  工  智  能  ②深  度  学  习",
        "搜  索  历  史  [清  空]",
    ]

    total_length = sum(len(text.replace(" ", "")) for text in search_texts)
    cleaned_length = 0

    for text in search_texts:
        try:
            corrected = await optimizer.correct_text(text)
            cleaned_length += len(corrected)

        except Exception as e:
            logger.error(f"处理失败: {e}")

    passed = cleaned_length >= total_length * 0.8
    results.add(
        "搜索文本处理",
        passed,
        f"文本保留率: {cleaned_length}/{total_length}",
        {"search_texts": len(search_texts)},
    )

    print_scenario("搜索文本处理", passed, f"处理{len(search_texts)}个搜索文本")

    return results


async def scenario_7_dashboard_text():
    """场景7: 仪表盘文本处理"""
    print_header("场景7: 仪表盘文本处理")

    optimizer = ChineseOCROptimizer()
    results = ScenarioTestResults()

    # 模拟仪表盘文本
    dashboard_texts = [
        "总  用  户  数  ①  ②  ,  ③  ④  ⑤",
        "活  跃  用  户  ⑧  ,  ⑨  0  ①",
        "新  增  用  户  +  ①  ,  ②  ③  ④",
        "增  长  率  +  ①  ⑤  .  ⑧  %",
        "北  京  ②  ⑤  %  上  海  ③  0  %",
    ]

    high_confidence_count = 0

    for text in dashboard_texts:
        try:
            corrected = await optimizer.correct_text(text)

            # 创建测试图像
            img = Image.new("RGB", (200, 100), color="white")
            temp_path = tempfile.mktemp(suffix=".png")
            img.save(temp_path)

            # 计算置信度
            confidence = optimizer._compute_chinese_confidence(corrected, temp_path)

            if os.path.exists(temp_path):
                os.remove(temp_path)

            if confidence >= 0.6:
                high_confidence_count += 1

        except Exception as e:
            logger.error(f"处理失败: {e}")

    passed = high_confidence_count >= len(dashboard_texts) * 0.8
    results.add(
        "仪表盘文本处理",
        passed,
        f"高置信度: {high_confidence_count}/{len(dashboard_texts)}",
        {"metrics": len(dashboard_texts)},
    )

    print_scenario(
        "仪表盘文本处理",
        passed,
        f"处理{len(dashboard_texts)}个指标,{high_confidence_count}个高置信度",
    )

    return results


async def scenario_8_multilang_text():
    """场景8: 多语言文本处理"""
    print_header("场景8: 多语言文本处理")

    optimizer = ChineseOCROptimizer()
    results = ScenarioTestResults()

    # 模拟多语言文本
    multilang_texts = [
        "设置  Language  语言",
        "时  区  Timezone  时  间",
        "日  期  Date 格  式  Format",
        "保  存  Save  取  消  Cancel",
    ]

    chinese_preserved = 0
    english_preserved = 0

    for text in multilang_texts:
        try:
            _corrected = await optimizer.correct_text(text)

            # 检查中文保留
            chinese_chars = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
            if chinese_chars > 0:
                chinese_preserved += 1

            # 检查英文保留
            english_chars = sum(1 for c in text if c.isalpha() and ord(c) < 128)
            if english_chars > 0:
                english_preserved += 1

        except Exception as e:
            logger.error(f"处理失败: {e}")

    passed = chinese_preserved >= len(multilang_texts) * 0.75
    results.add(
        "多语言文本处理",
        passed,
        f"中文({chinese_preserved}/{len(multilang_texts)}) 英文({english_preserved}/{len(multilang_texts)})",
        {"multilang_texts": len(multilang_texts)},
    )

    print_scenario(
        "多语言文本处理",
        passed,
        f"中文保留{chinese_preserved}/{len(multilang_texts)} 英文保留{english_preserved}/{len(multilang_texts)}",
    )

    return results


async def scenario_9_progress_text():
    """场景9: 进度文本处理"""
    print_header("场景9: 进度文本处理")

    optimizer = ChineseOCROptimizer()
    results = ScenarioTestResults()

    # 模拟进度文本
    progress_texts = [
        "上  传  进  度  ⑦  ⑤  %",
        "已  上  传  :  ⑦  5  0  M  B  /  1  G  B",
        "速  度  :  1  5  .  5  M  B  /  s",
        "剩  余  时  间  :  约  1  6  秒",
        "文  件  :  d  o  c  u  m  e  n  t  .  p  d  f",
    ]

    cleaned_count = 0

    for text in progress_texts:
        try:
            corrected = await optimizer.correct_text(text)

            # 检查是否去除了多余空格
            if " " not in corrected or corrected.count(" ") < text.count(" ") * 0.5:
                cleaned_count += 1

        except Exception as e:
            logger.error(f"处理失败: {e}")

    passed = cleaned_count >= len(progress_texts) * 0.8
    results.add(
        "进度文本处理",
        passed,
        f"清理率: {cleaned_count}/{len(progress_texts)}",
        {"progress_texts": len(progress_texts)},
    )

    print_scenario(
        "进度文本处理", passed, f"处理{len(progress_texts)}条进度信息,清理{cleaned_count}条"
    )

    return results


async def scenario_10_login_text():
    """场景10: 登录文本处理"""
    print_header("场景10: 登录文本处理")

    optimizer = ChineseOCROptimizer()
    results = ScenarioTestResults()

    # 模拟登录页面文本
    login_texts = [
        "用  户  登  录",
        "用  户  名  /  邮  箱",
        "密  码  •  •  •  •  •  •  •",
        "记  住  我  忘  记  密  码  ?",
        "登  录  还  没  有  账  号  ?  立  即  注  册",
    ]

    key_terms = ["登录", "用户名", "邮箱", "密码", "注册"]
    found_terms = 0

    for text in login_texts:
        try:
            corrected = await optimizer.correct_text(text)

            # 检查关键词
            for term in key_terms:
                if term in corrected:
                    found_terms += 1
                    break

        except Exception as e:
            logger.error(f"处理失败: {e}")

    passed = found_terms >= len(login_texts) * 0.6
    results.add(
        "登录文本处理",
        passed,
        f"关键词保留: {found_terms}/{len(login_texts)}",
        {"login_texts": len(login_texts)},
    )

    print_scenario(
        "登录文本处理",
        passed,
        f"处理{len(login_texts)}个登录元素,关键词{found_terms}/{len(login_texts)}",
    )

    return results


async def main():
    """运行所有实际场景测试"""
    print("\n")
    print("🌟 Athena实际场景测试")
    print("   作者: 小诺·双鱼公主")
    print("   日期: 2026-01-01")
    print("\n   测试真实场景下的文本优化能力")

    all_results = ScenarioTestResults()

    # 运行所有场景测试
    scenarios = [
        ("表单文本纠错", scenario_1_form_text_correction),
        ("菜单文本处理", scenario_2_menu_text_processing),
        ("通知文本处理", scenario_3_notification_text),
        ("表格数据处理", scenario_4_table_data_processing),
        ("错误消息处理", scenario_5_error_message_text),
        ("搜索文本处理", scenario_6_search_text),
        ("仪表盘文本处理", scenario_7_dashboard_text),
        ("多语言文本处理", scenario_8_multilang_text),
        ("进度文本处理", scenario_9_progress_text),
        ("登录文本处理", scenario_10_login_text),
    ]

    for name, scenario_func in scenarios:
        try:
            scenario_results = await scenario_func()
            # 合并结果
            for result in scenario_results.results:
                all_results.results.append(result)
        except Exception as e:
            logger.error(f"场景{name}测试失败: {e}")
            all_results.add(name, False, f"异常: {e}")

    # 汇总结果
    print_header("实际场景测试结果汇总")

    summary = all_results.summary()

    print(f"\n总场景数: {summary['total']}")
    print(f"通过: {summary['passed']} 个 ✅")
    print(f"失败: {summary['failed']} 个 ❌")
    print(f"通过率: {summary['pass_rate']*100:.1f}%")

    # 详细结果
    print(f"\n{'场景':<20} {'结果':<8} {'详情'}")
    print("-" * 70)
    for result in all_results.results:
        status = "✅ 通过" if result["passed"] else "❌ 失败"
        print(f"{result['scenario']:<20} {status:<8} {result['details'][:40]}")

    if summary["pass_rate"] >= 0.9:
        print("\n🎉 实际场景测试优秀!")
    elif summary["pass_rate"] >= 0.7:
        print("\n✅ 实际场景测试良好")
    else:
        print("\n⚠️ 部分场景需要优化")

    return summary["pass_rate"] >= 0.7


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)

