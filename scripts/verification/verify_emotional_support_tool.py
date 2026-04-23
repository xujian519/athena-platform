#!/usr/bin/env python3
"""
Emotional Support工具验证脚本

验证情感支持工具的完整功能:
1. 情感识别准确性
2. 强度分级处理
3. 支持策略生成
4. 响应适当性
5. 边界情况处理
6. 对话连续性

作者: Athena平台团队
创建时间: 2026-04-20
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.tools.production_tool_implementations import emotional_support_handler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("data/emotional_support_verification.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class EmotionalSupportVerifier:
    """情感支持工具验证器"""

    def __init__(self):
        self.test_results = []
        self.success_count = 0
        self.failure_count = 0
        self.warning_count = 0

    async def test_emotion_recognition(self):
        """测试情感识别准确性"""
        logger.info("\n" + "=" * 60)
        logger.info("测试1: 情感识别准确性")
        logger.info("=" * 60)

        test_cases = [
            # (输入情感, 期望识别结果, 描述)
            ("我很焦虑", "焦虑", "直接表达焦虑"),
            ("担心考试不及格", "焦虑", "关键词:担心"),
            ("感到很悲伤", "悲伤", "直接表达悲伤"),
            ("难过的时候", "悲伤", "关键词:难过"),
            ("非常生气", "愤怒", "直接表达愤怒"),
            ("恼火的事情", "愤怒", "关键词:恼火"),
            ("压力很大", "压力", "直接表达压力"),
            ("感觉很累", "压力", "关键词:累"),
            ("孤独一人", "孤独", "直接表达孤独"),
            ("没人陪我", "孤独", "关键词:没人陪"),
            ("心情平静", "一般", "中性情感"),
            ("不知道说什么", "一般", "模糊表达"),
        ]

        passed = 0
        failed = 0

        for emotion_input, expected, description in test_cases:
            result = await emotional_support_handler(
                params={"emotion": emotion_input, "intensity": 5, "context": "测试"},
                context={},
            )

            detected = result.get("detected_emotion")
            is_correct = detected == expected

            status = "✅ PASS" if is_correct else "❌ FAIL"
            logger.info(f"{status} | {description}")
            logger.info(f"  输入: '{emotion_input}'")
            logger.info(f"  期望: {expected} | 实际: {detected}")

            if is_correct:
                passed += 1
            else:
                failed += 1

            self.test_results.append(
                {
                    "test_type": "emotion_recognition",
                    "input": emotion_input,
                    "expected": expected,
                    "actual": detected,
                    "passed": is_correct,
                    "description": description,
                }
            )

        accuracy = passed / len(test_cases) * 100
        logger.info(f"\n识别准确率: {accuracy:.1f}% ({passed}/{len(test_cases)})")

        if accuracy >= 90:
            logger.info("✅ 情感识别准确性: 优秀")
            self.success_count += 1
        elif accuracy >= 70:
            logger.info("⚠️ 情感识别准确性: 良好")
            self.warning_count += 1
        else:
            logger.info("❌ 情感识别准确性: 需要改进")
            self.failure_count += 1

    async def test_intensity_handling(self):
        """测试强度分级处理"""
        logger.info("\n" + "=" * 60)
        logger.info("测试2: 强度分级处理")
        logger.info("=" * 60)

        test_cases = [
            (1, "一般建议即可", "低强度"),
            (3, "一般建议即可", "低强度"),
            (5, "建议采取积极的自我调节", "中强度"),
            (7, "建议采取积极的自我调节", "中高强度"),
            (8, "强烈建议寻求专业心理支持", "高强度"),
            (10, "强烈建议寻求专业心理支持", "极高强度"),
        ]

        passed = 0
        failed = 0

        for intensity, expected_advice, description in test_cases:
            result = await emotional_support_handler(
                params={"emotion": "焦虑", "intensity": intensity, "context": "测试"},
                context={},
            )

            actual_advice = result.get("advice_level")
            is_correct = actual_advice == expected_advice

            status = "✅ PASS" if is_correct else "❌ FAIL"
            logger.info(f"{status} | {description}")
            logger.info(f"  强度: {intensity}/10")
            logger.info(f"  期望: {expected_advice}")
            logger.info(f"  实际: {actual_advice}")

            if is_correct:
                passed += 1
            else:
                failed += 1

            self.test_results.append(
                {
                    "test_type": "intensity_handling",
                    "input": intensity,
                    "expected": expected_advice,
                    "actual": actual_advice,
                    "passed": is_correct,
                    "description": description,
                }
            )

        accuracy = passed / len(test_cases) * 100
        logger.info(f"\n强度分级准确率: {accuracy:.1f}% ({passed}/{len(test_cases)})")

        if accuracy >= 90:
            logger.info("✅ 强度分级处理: 优秀")
            self.success_count += 1
        elif accuracy >= 70:
            logger.info("⚠️ 强度分级处理: 良好")
            self.warning_count += 1
        else:
            logger.info("❌ 强度分级处理: 需要改进")
            self.failure_count += 1

    async def test_support_strategies(self):
        """测试支持策略生成"""
        logger.info("\n" + "=" * 60)
        logger.info("测试3: 支持策略生成")
        logger.info("=" * 60)

        emotions = ["焦虑", "悲伤", "愤怒", "压力", "孤独", "一般"]

        for emotion in emotions:
            result = await emotional_support_handler(
                params={"emotion": emotion, "intensity": 5, "context": "测试"},
                context={},
            )

            strategies = result.get("strategies", [])
            activities = result.get("suggested_activities", [])
            understanding = result.get("understanding", "")

            logger.info(f"\n📊 情感类型: {emotion}")
            logger.info(f"  理解回应: {understanding}")
            logger.info(f"  策略数量: {len(strategies)}")
            logger.info(f"  策略: {', '.join(strategies[:2])}...")
            logger.info(f"  建议活动: {', '.join(activities)}")

            # 验证策略有效性
            has_strategies = len(strategies) > 0
            has_activities = len(activities) > 0
            has_understanding = len(understanding) > 0

            all_valid = has_strategies and has_activities and has_understanding

            if all_valid:
                logger.info("  ✅ 策略完整")
                self.success_count += 1
            else:
                logger.info("  ❌ 策略不完整")
                self.failure_count += 1

            self.test_results.append(
                {
                    "test_type": "support_strategies",
                    "emotion": emotion,
                    "has_strategies": has_strategies,
                    "has_activities": has_activities,
                    "has_understanding": has_understanding,
                    "passed": all_valid,
                }
            )

    async def test_response_appropriateness(self):
        """测试响应适当性"""
        logger.info("\n" + "=" * 60)
        logger.info("测试4: 响应适当性")
        logger.info("=" * 60)

        test_cases = [
            {
                "emotion": "焦虑",
                "intensity": 8,
                "context": "考试前非常紧张",
                "expect_keywords": ["理解", "焦虑", "专业", "支持"],
                "avoid_keywords": ["开心", "兴奋"],
            },
            {
                "emotion": "悲伤",
                "intensity": 6,
                "context": "亲人去世",
                "expect_keywords": ["悲伤", "允许", "感受", "温柔"],
                "avoid_keywords": ["兴奋", "激动"],
            },
            {
                "emotion": "愤怒",
                "intensity": 7,
                "context": "被误解",
                "expect_keywords": ["愤怒", "理解", "冷静", "表达"],
                "avoid_keywords": ["开心", "快乐"],
            },
        ]

        for test_case in test_cases:
            result = await emotional_support_handler(
                params={
                    "emotion": test_case["emotion"],
                    "intensity": test_case["intensity"],
                    "context": test_case["context"],
                },
                context={},
            )

            understanding = result.get("understanding", "")
            additional_advice = result.get("additional_advice", "")
            full_response = understanding + " " + additional_advice

            logger.info(f"\n📝 情感: {test_case['emotion']} (强度: {test_case['intensity']})")
            logger.info(f"  上下文: {test_case['context']}")
            logger.info(f"  回应: {full_response[:100]}...")

            # 检查期望的关键词
            has_expected = any(kw in full_response for kw in test_case["expect_keywords"])
            # 检查避免的关键词
            has_avoided = not any(kw in full_response for kw in test_case["avoid_keywords"])

            is_appropriate = has_expected and has_avoided

            if is_appropriate:
                logger.info("  ✅ 响应适当")
                self.success_count += 1
            else:
                logger.info("  ❌ 响应不当")
                if not has_expected:
                    logger.info(f"    缺少期望关键词: {test_case['expect_keywords']}")
                if not has_avoided:
                    logger.info(f"    包含避免关键词: {test_case['avoid_keywords']}")
                self.failure_count += 1

            self.test_results.append(
                {
                    "test_type": "response_appropriateness",
                    "emotion": test_case["emotion"],
                    "has_expected_keywords": has_expected,
                    "avoided_inappropriate": has_avoided,
                    "passed": is_appropriate,
                }
            )

    async def test_edge_cases(self):
        """测试边界情况"""
        logger.info("\n" + "=" * 60)
        logger.info("测试5: 边界情况处理")
        logger.info("=" * 60)

        edge_cases = [
            {
                "params": {"emotion": "", "intensity": 5, "context": ""},
                "description": "空输入",
                "should_succeed": True,
            },
            {
                "params": {"emotion": "未知情感XYZ", "intensity": 5, "context": "测试"},
                "description": "未知情感",
                "should_succeed": True,
            },
            {
                "params": {"emotion": "焦虑", "intensity": 0, "context": "测试"},
                "description": "零强度",
                "should_succeed": True,
            },
            {
                "params": {"emotion": "焦虑", "intensity": 15, "context": "测试"},
                "description": "超范围强度",
                "should_succeed": True,
            },
            {
                "params": {"emotion": "焦虑", "intensity": -5, "context": "测试"},
                "description": "负强度",
                "should_succeed": True,
            },
            {
                "params": {"emotion": "a" * 1000, "intensity": 5, "context": "测试"},
                "description": "超长输入",
                "should_succeed": True,
            },
        ]

        for edge_case in edge_cases:
            try:
                result = await emotional_support_handler(
                    params=edge_case["params"],
                    context={},
                )

                success = result.get("success", False)
                is_handled = success == edge_case["should_succeed"]

                status = "✅ PASS" if is_handled else "❌ FAIL"
                logger.info(f"{status} | {edge_case['description']}")
                logger.info(f"  输入: {edge_case['params']}")
                logger.info(f"  结果: {result.get('message', 'N/A')}")

                if is_handled:
                    self.success_count += 1
                else:
                    self.failure_count += 1

                self.test_results.append(
                    {
                        "test_type": "edge_case",
                        "description": edge_case["description"],
                        "passed": is_handled,
                    }
                )

            except Exception as e:
                logger.info(f"❌ EXCEPTION | {edge_case['description']}")
                logger.info(f"  错误: {str(e)}")
                self.failure_count += 1

                self.test_results.append(
                    {
                        "test_type": "edge_case",
                        "description": edge_case["description"],
                        "passed": False,
                        "error": str(e),
                    }
                )

    async def test_conversation_continuity(self):
        """测试对话连续性"""
        logger.info("\n" + "=" * 60)
        logger.info("测试6: 对话连续性")
        logger.info("=" * 60)

        # 模拟连续对话
        conversation_flow = [
            {"emotion": "焦虑", "intensity": 7, "context": "第一次对话"},
            {"emotion": "焦虑", "intensity": 5, "context": "持续关注"},
            {"emotion": "焦虑", "intensity": 3, "context": "情况好转"},
            {"emotion": "平静", "intensity": 1, "context": "基本恢复"},
        ]

        logger.info("模拟连续对话过程:")
        prev_emotion = None
        intensity_trend = []

        for i, turn in enumerate(conversation_flow, 1):
            result = await emotional_support_handler(
                params=turn,
                context={"conversation_turn": i},
            )

            detected = result.get("detected_emotion")
            intensity = result.get("intensity")
            understanding = result.get("understanding", "")

            intensity_trend.append(intensity)

            logger.info(f"\n第{i}轮:")
            logger.info(f"  情感: {detected} (强度: {intensity}/10)")
            logger.info(f"  回应: {understanding[:60]}...")

            if prev_emotion:
                if intensity < prev_emotion["intensity"]:
                    logger.info(f"  📉 强度下降: {prev_emotion['intensity']} → {intensity} (改善)")
                elif intensity > prev_emotion["intensity"]:
                    logger.info(f"  📈 强度上升: {prev_emotion['intensity']} → {intensity} (需关注)")

            prev_emotion = {"emotion": detected, "intensity": intensity}

        # 评估趋势
        if len(intensity_trend) >= 2:
            overall_trend = intensity_trend[-1] - intensity_trend[0]
            logger.info(f"\n整体趋势: {overall_trend:+.1f}")

            if overall_trend < 0:
                logger.info("✅ 对话连续性: 支持有效,情感强度下降")
                self.success_count += 1
            else:
                logger.info("⚠️ 对话连续性: 需要更多支持")
                self.warning_count += 1

        self.test_results.append(
            {
                "test_type": "conversation_continuity",
                "intensity_trend": intensity_trend,
                "overall_change": intensity_trend[-1] - intensity_trend[0] if len(intensity_trend) >= 2 else 0,
            }
        )

    def generate_report(self):
        """生成验证报告"""
        logger.info("\n" + "=" * 60)
        logger.info("验证报告汇总")
        logger.info("=" * 60)

        # 统计
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.get("passed", False))
        success_rate = passed_tests / total_tests * 100 if total_tests > 0 else 0

        logger.info(f"\n总测试数: {total_tests}")
        logger.info(f"通过: {passed_tests}")
        logger.info(f"成功率: {success_rate:.1f}%")
        logger.info(f"成功计数: {self.success_count}")
        logger.info(f"警告计数: {self.warning_count}")
        logger.info(f"失败计数: {self.failure_count}")

        # 生成报告文件
        report = {
            "verification_date": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "success_rate": f"{success_rate:.1f}%",
                "success_count": self.success_count,
                "warning_count": self.warning_count,
                "failure_count": self.failure_count,
            },
            "test_results": self.test_results,
            "conclusions": self._generate_conclusions(success_rate),
        }

        # 保存报告
        report_path = Path("docs/reports/EMOTIONAL_SUPPORT_TOOL_VERIFICATION_REPORT_20260420.md")
        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, "w", encoding="utf-8") as f:
            f.write("# Emotional Support工具验证报告\n\n")
            f.write(f"**验证日期**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")
            f.write("## 验证摘要\n\n")
            f.write(f"- **总测试数**: {total_tests}\n")
            f.write(f"- **通过测试**: {passed_tests}\n")
            f.write(f"- **成功率**: {success_rate:.1f}%\n")
            f.write(f"- **成功计数**: {self.success_count}\n")
            f.write(f"- **警告计数**: {self.warning_count}\n")
            f.write(f"- **失败计数**: {self.failure_count}\n\n")
            f.write("---\n\n")
            f.write("## 测试结果详情\n\n")
            f.write("### 1. 情感识别准确性\n\n")
            self._write_test_results(f, "emotion_recognition")
            f.write("\n### 2. 强度分级处理\n\n")
            self._write_test_results(f, "intensity_handling")
            f.write("\n### 3. 支持策略生成\n\n")
            self._write_test_results(f, "support_strategies")
            f.write("\n### 4. 响应适当性\n\n")
            self._write_test_results(f, "response_appropriateness")
            f.write("\n### 5. 边界情况处理\n\n")
            self._write_test_results(f, "edge_case")
            f.write("\n### 6. 对话连续性\n\n")
            self._write_test_results(f, "conversation_continuity")
            f.write("\n---\n\n")
            f.write("## 结论\n\n")
            for conclusion in report["conclusions"]:
                f.write(f"- {conclusion}\n"
)

        logger.info(f"\n✅ 报告已生成: {report_path}")

        return report

    def _generate_conclusions(self, success_rate: float) -> list[str]:
        """生成结论"""
        conclusions = []

        if success_rate >= 90:
            conclusions.append("✅ 工具整体表现优秀,所有核心功能正常工作")
        elif success_rate >= 70:
            conclusions.append("⚠️ 工具整体表现良好,部分功能需要优化")
        else:
            conclusions.append("❌ 工具存在多个问题,需要重点改进")

        if self.success_count >= 5:
            conclusions.append("✅ 核心功能完整,支持策略丰富有效")
        else:
            conclusions.append("⚠️ 核心功能不完整,需要增强")

        if self.failure_count == 0:
            conclusions.append("✅ 无严重缺陷,边界处理良好")
        else:
            conclusions.append(f"❌ 存在{self.failure_count}个失败案例,需要修复")

        conclusions.append("\n**建议**:")
        conclusions.append("- 继续优化情感识别算法,提高准确率")
        conclusions.append("- 扩展支持策略库,增加更多场景")
        conclusions.append("- 加强对话历史管理,提升连续性")
        conclusions.append("- 定期进行伦理审查,确保响应适当性")

        return conclusions

    def _write_test_results(self, f, test_type: str):
        """写入测试结果"""
        results = [r for r in self.test_results if r.get("test_type") == test_type]

        if not results:
            f.write("无测试数据\n\n")
            return

        for i, result in enumerate(results, 1):
            status = "✅" if result.get("passed", False) else "❌"
            f.write(f"{status} **测试{i}**: ")

            if test_type == "emotion_recognition":
                f.write(f"{result['description']}\n")
                f.write(f"  - 输入: `{result['input']}`\n")
                f.write(f"  - 期望: {result['expected']}\n")
                f.write(f"  - 实际: {result['actual']}\n\n")

            elif test_type == "intensity_handling":
                f.write(f"{result['description']}\n")
                f.write(f"  - 强度: {result['input']}/10\n")
                f.write(f"  - 期望: {result['expected']}\n")
                f.write(f"  - 实际: {result['actual']}\n\n")

            elif test_type == "support_strategies":
                f.write(f"情感类型: {result['emotion']}\n")
                f.write(f"  - 策略: {'✅' if result['has_strategies'] else '❌'}\n")
                f.write(f"  - 活动: {'✅' if result['has_activities'] else '❌'}\n")
                f.write(f"  - 理解: {'✅' if result['has_understanding'] else '❌'}\n\n")

            elif test_type == "response_appropriateness":
                f.write(f"情感: {result['emotion']}\n")
                f.write(f"  - 包含期望关键词: {'✅' if result['has_expected_keywords'] else '❌'}\n")
                f.write(f"  - 避免不当关键词: {'✅' if result['avoided_inappropriate'] else '❌'}\n\n")

            elif test_type == "edge_case":
                f.write(f"{result['description']}\n")
                if "error" in result:
                    f.write(f"  - 错误: {result['error']}\n\n")
                else:
                    f.write(f"  - 状态: {'✅ 已处理' if result['passed'] else '❌ 未处理'}\n\n")

            elif test_type == "conversation_continuity":
                f.write(f"强度趋势: {result['intensity_trend']}\n")
                f.write(f"  - 整体变化: {result['overall_change']:+.1f}\n\n")


async def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("Emotional Support工具验证")
    logger.info("=" * 60)

    verifier = EmotionalSupportVerifier()

    try:
        # 执行所有测试
        await verifier.test_emotion_recognition()
        await verifier.test_intensity_handling()
        await verifier.test_support_strategies()
        await verifier.test_response_appropriateness()
        await verifier.test_edge_cases()
        await verifier.test_conversation_continuity()

        # 生成报告
        report = verifier.generate_report()

        logger.info("\n" + "=" * 60)
        logger.info("验证完成")
        logger.info("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"验证过程出错: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
