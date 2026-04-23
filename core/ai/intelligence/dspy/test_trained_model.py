#!/usr/bin/env python3

"""
测试已训练的DSPy模型
Test the trained DSPy model

作者: 小诺·双鱼公主
版本: v1.0.0
创建时间: 2026-01-04
"""

import logging
import sys
from pathlib import Path
from typing import Any

import dspy

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# 导入训练好的模型
from core.intelligence.dspy.training_system_v3_enhanced import (
    EnhancedPatentAnalyzer,
)


def setup_llm() -> Any:
    """配置LLM"""
    try:
        import os

        api_key = os.getenv("ZHIPUAI_API_KEY", "")
        lm = dspy.LM(
            model="zai/glm-4-plus",
            api_key=api_key or "dummy",
            api_base="https://open.bigmodel.cn/api/paas/v4/",
        )
        dspy.configure(lm=lm)
        logger.info("✅ LLM配置成功")
        return lm
    except Exception as e:
        logger.error(f"❌ LLM配置失败: {e}")
        return None


def test_with_real_case() -> Any:
    """测试真实案例"""

    logger.info("\n" + "=" * 70)
    logger.info("🧪 测试已训练的DSPy模型")
    logger.info("=" * 70)

    # 创建分析器
    analyzer = EnhancedPatentAnalyzer(use_cot=True)

    # 测试案例1: 新颖性案例
    test_case_1 = {
        "background": """
案由
本专利的专利号为CN202110234567.8,发明名称为一种新型锂电池正极材料,申请日为2021年03月15日,授权公告日为2022年08月20日。
无效宣告请求人于2023年05月10日向国家知识产权局提出了无效宣告请求,其理由是权利要求1-3不符合专利法第22条第2款关于新颖性的规定。
请求人提交了如下证据:
证据1:CN108765432A,公开日为2020年12月01日,公开了一种锂离子电池正极材料,包含镍钴锰三元材料;
证据2:US20210012345A1,公开日为2021年01月15日,公开了类似的正极材料组成。
请求人认为:权利要求1的技术方案与证据1公开的技术方案实质相同,不具备新颖性。
        """,
        "technical_field": "新能源/锂电池",
        "patent_number": "CN202110234567.8",
    }

    # 测试案例2: 创造性案例
    test_case_2 = {
        "background": """
案由
本专利涉及一种基于深度学习的图像识别方法,专利号为CN202010123456.7,申请日为2020年04月20日。
无效宣告请求人主张:权利要求1-5不具备创造性,不符合专利法第22条第3款的规定。
提交证据:
证据1:CN105678901A,公开日为2018年05月10日,公开了基础的CNN图像识别方法;
证据2:EP3456789B1,授权公告日为2019年08月15日,公开了使用注意力机制改进图像识别。
请求人认为:本申请权利要求1相对于证据1和证据2的结合是显而易见的,不具备突出的实质性特点和显著的进步。
        """,
        "technical_field": "人工智能/计算机视觉",
        "patent_number": "CN202010123456.7",
    }

    # 测试案例3: 清楚性案例
    test_case_3 = {
        "background": """
案由
本专利涉及一种智能家具控制系统,专利号为CN201980012345.6。
无效宣告请求人主张:权利要求1、3、5不符合专利法第26条第4款的规定,未清楚限定要求保护的范围。
具体理由:
1. 权利要求1中的"智能控制单元"表述模糊,未明确其具体结构和功能;
2. 权利要求3中的"适当的时间"缺乏明确标准;
3. 权利要求5中的"舒适模式"定义不清晰。
请求人认为:这些技术术语无法让本领域技术人员准确理解专利保护范围的边界。
        """,
        "technical_field": "智能家居",
        "patent_number": "CN201980012345.6",
    }

    test_cases = [
        ("案例1: 新颖性问题", test_case_1, "novelty"),
        ("案例2: 创造性问题", test_case_2, "creative"),
        ("案例3: 清楚性问题", test_case_3, "clarity"),
    ]

    results = []

    for name, case, expected_type in test_cases:
        logger.info(f"\n{'─'*70}")
        logger.info(f"📋 {name}")
        logger.info(f"{'─'*70}")
        logger.info(f"技术领域: {case['technical_field']}")
        logger.info(f"专利号: {case['patent_number']}")
        logger.info(f"预期类型: {expected_type}")

        try:
            # 执行分析
            result = analyzer(
                background=case["background"],
                technical_field=case["technical_field"],
                patent_number=case["patent_number"],
            )

            # 提取结果
            case_type = getattr(result, "case_type", "N/A")
            legal_issues = getattr(result, "legal_issues", "N/A")
            reasoning = getattr(result, "reasoning", "N/A")
            conclusion = getattr(result, "conclusion", "N/A")

            # 打印结果
            logger.info("\n📊 分析结果:")
            logger.info(f"  案例类型: {case_type}")
            logger.info(f"  法律问题: {legal_issues}")
            logger.info(f"  结论: {conclusion}")
            logger.info("\n📝 推理过程:")
            logger.info(f"  {reasoning[:200]}...")

            # 检查是否匹配预期
            is_correct = str(case_type).lower() == expected_type.lower()
            status = "✅ 正确" if is_correct else "❌ 错误"
            logger.info(f"\n{status}")

            results.append(
                {
                    "name": name,
                    "expected": expected_type,
                    "actual": case_type,
                    "correct": is_correct,
                }
            )

        except Exception as e:
            logger.error(f"❌ 分析失败: {e}")
            import traceback

            traceback.print_exc()
            results.append(
                {"name": name, "expected": expected_type, "actual": "ERROR", "correct": False}
            )

    # 总结
    logger.info("\n" + "=" * 70)
    logger.info("📈 测试结果总结")
    logger.info("=" * 70)

    correct_count = sum(1 for r in results if r["correct"])
    total_count = len(results)
    accuracy = correct_count / total_count * 100 if total_count > 0 else 0

    logger.info(f"\n准确率: {correct_count}/{total_count} = {accuracy:.1f}%")

    for r in results:
        status = "✅" if r["correct"] else "❌"
        logger.info(f"{status} {r['name']}: 预期={r['expected']}, 实际={r['actual']}")

    return accuracy


def main() -> None:
    """主函数"""
    # 配置LLM
    lm = setup_llm()
    if not lm:
        logger.error("❌ 无法继续测试,LLM配置失败")
        return

    # 运行测试
    accuracy = test_with_real_case()

    logger.info(f"\n🎯 测试完成!总体准确率: {accuracy:.1f}%")


if __name__ == "__main__":
    main()

