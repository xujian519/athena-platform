#!/usr/bin/env python3
"""
Phase 2 测试和报告生成
Phase 2 Testing and Report Generation

测试本地BERT意图识别系统并生成详细报告

作者: 小诺·双鱼公主
版本: v2.0.0
创建: 2025-12-29
"""

from __future__ import annotations
import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


async def test_intent_classifier():
    """测试意图识别系统"""
    print("🧪 意图识别系统测试")
    print("=" * 60)

    # 导入分类器
    from core.intent.local_bert_intent_classifier import LocalBERTIntentClassifier

    # 加载测试数据
    test_file = project_root / "data/intent_recognition/test_data.json"
    with open(test_file, encoding="utf-8") as f:
        test_data = json.load(f)

    print(f"📊 测试数据: {len(test_data)} 条")

    # 选择几个测试用例
    test_cases = [
        {"text": "分析这个专利", "expected": "PATENT_ANALYSIS"},
        {"text": "检索人工智能专利", "expected": "PATENT_SEARCH"},
        {"text": "帮我写Python代码", "expected": "CODE_GENERATION"},
        {"text": "谢谢爸爸", "expected": "EMOTIONAL"},
        {"text": "启动服务", "expected": "SYSTEM_CONTROL"},
        {"text": "审查意见怎么答复", "expected": "OPINION_RESPONSE"},
        {"text": "撰写发明专利", "expected": "PATENT_DRAFTING"},
        {"text": "分析数据报告", "expected": "DATA_ANALYSIS"},
        {"text": "写个故事", "expected": "CREATIVE_WRITING"},
        {"text": "解释法律条款", "expected": "LEGAL_QUERY"},
    ]

    # 初始化分类器(使用已保存的模型)
    classifier = LocalBERTIntentClassifier()

    # 尝试加载已训练的模型
    model_dir = project_root / "models/intent_recognition/bert_enhanced"
    if model_dir.exists():
        classifier.load_model(model_dir)
        print("✅ 已加载训练好的模型")
    else:
        print("⚠️ 未找到训练好的模型,使用实时训练...")
        training_file = project_root / "data/intent_recognition/training_data.json"
        with open(training_file, encoding="utf-8") as f:
            training_data = json.load(f)
        classifier.train_with_data(training_data)

    # 测试每个用例
    print("\n📝 测试结果:")
    print("-" * 60)

    correct = 0
    total = len(test_cases)
    results = []

    for i, case in enumerate(test_cases, 1):
        text = case["text"]
        expected = case["expected"]

        start = time.time()
        result = classifier.predict_intent(text)
        elapsed = time.time() - start

        predicted = result["intent"]
        confidence = result["confidence"]
        is_correct = predicted == expected

        if is_correct:
            correct += 1
            status = "✅"
        else:
            status = "❌"

        print(f"\n{i}. {text}")
        print(f"   预期: {expected}")
        print(f"   实际: {predicted}")
        print(f"   置信度: {confidence:.2%}")
        print(f"   耗时: {elapsed*1000:.1f}ms")
        print(f"   {status} {'正确' if is_correct else '错误'}")

        results.append(
            {
                "text": text,
                "expected": expected,
                "predicted": predicted,
                "confidence": confidence,
                "correct": is_correct,
                "inference_time": elapsed,
            }
        )

    # 统计结果
    accuracy = correct / total
    avg_time = sum(r["inference_time"] for r in results) / len(results)

    print("\n" + "=" * 60)
    print("📊 总体结果:")
    print(f"  准确率: {accuracy:.2%} ({correct}/{total})")
    print(f"  平均耗时: {avg_time*1000:.1f}ms")

    # 获取性能统计
    stats = classifier.get_performance_stats()
    print("\n📈 性能统计:")
    print(f"  总预测次数: {stats['total_predictions']}")
    print(f"  缓存命中率: {stats['cache_hit_rate']:.2%}")
    print(f"  平均推理时间: {stats['avg_total_inference_time']*1000:.1f}ms")
    print(f"  缓存大小: {stats['cache_size']}")

    return results, accuracy


async def generate_phase2_report(results: list[dict], accuracy: float):
    """生成Phase 2报告"""
    print("\n📄 生成Phase 2报告...")

    report = {
        "phase": "Phase 2 - 本地BERT增强",
        "completion_time": datetime.now().isoformat(),
        "target_accuracy": "85%",
        "actual_accuracy": f"{accuracy:.2%}",
        "improvement_needed": max(0, 0.85 - accuracy),
        "status": "✅ 达标" if accuracy >= 0.85 else "⚠️ 需要改进",
        "test_results": results,
        "summary": {
            "total_tests": len(results),
            "correct": sum(1 for r in results if r["correct"]),
            "incorrect": sum(1 for r in results if not r["correct"]),
            "avg_confidence": sum(r["confidence"] for r in results) / len(results),
            "avg_inference_time": sum(r["inference_time"] for r in results) / len(results),
        },
        "next_steps": (
            ["1. 集成到小诺主系统", "2. 实现在线学习", "3. 添加知识图谱增强", "4. 优化多模态融合"]
            if accuracy >= 0.85
            else ["1. 增加训练数据", "2. 调整模型超参数", "3. 使用数据增强", "4. 尝试其他BERT模型"]
        ),
    }

    # 保存报告
    report_dir = project_root / "docs/intent_optimization"
    report_dir.mkdir(parents=True, exist_ok=True)

    report_file = report_dir / "phase2_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"✅ 报告已保存: {report_file}")

    # 打印报告摘要
    print("\n📋 Phase 2 报告摘要:")
    print(f"  实际准确率: {accuracy:.2%}")
    print("  目标准确率: 85%")
    print(f"  状态: {report['status']}")
    print("  下一步:")
    for step in report["next_steps"]:
        print(f"    {step}")


async def main():
    """主程序"""
    print("🎯 Phase 2 测试和报告生成")
    print("=" * 60)

    # 测试系统
    results, accuracy = await test_intent_classifier()

    # 生成报告
    await generate_phase2_report(results, accuracy)

    print("\n✅ 完成!")


if __name__ == "__main__":
    asyncio.run(main())
