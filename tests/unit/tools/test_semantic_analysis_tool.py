#!/usr/bin/env python3
"""
语义分析工具验证测试
Semantic Analysis Tool Verification Test

验证semantic_analysis工具的完整可用性。

Author: Athena平台团队
Created: 2026-04-19
Version: v1.0.0
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_semantic_analysis_handler():
    """测试语义分析Handler"""
    from core.tools.semantic_analysis_handler import semantic_analysis_handler

    print("=" * 80)
    print("🧪 语义分析工具验证测试")
    print("=" * 80)

    # ========================================
    # 测试1: 计算文本相似度
    # ========================================
    print("\n📊 测试1: 计算文本相似度")
    print("-" * 80)

    result = semantic_analysis_handler(
        action="calculate_similarity",
        text1="帮我写个故事",
        text2="创作文案内容"
    )

    print(f"✅ 状态: {result['status']}")
    if result['status'] == 'success':
        print(f"📈 相似度分数: {result['similarity']:.4f}")
        print(f"📝 解释: {result['interpretation']}")
        print(f"📋 文本1: {result['text1']}")
        print(f"📋 文本2: {result['text2']}")
    else:
        print(f"❌ 错误: {result.get('error')}")
        return False

    # ========================================
    # 测试2: 意图识别
    # ========================================
    print("\n🎯 测试2: 意图识别")
    print("-" * 80)

    result = semantic_analysis_handler(
        action="find_best_intent",
        text1="检索人工智能相关专利",
        intent_examples={
            "patent_search": ["检索专利", "搜索专利", "查找专利"],
            "creative_writing": ["写故事", "创作文案", "生成内容"],
            "data_analysis": ["分析数据", "统计结果", "数据可视化"]
        },
        train_model=True
    )

    print(f"✅ 状态: {result['status']}")
    if result['status'] == 'success':
        print(f"🎯 最佳意图: {result['best_intent']}")
        print(f"📊 置信度: {result['confidence']:.4f}")
        print(f"📝 解释: {result['interpretation']}")
        print(f"📋 可用意图数: {len(result['available_intents'])}")
    else:
        print(f"❌ 错误: {result.get('error')}")
        return False

    # ========================================
    # 测试3: 意图排序
    # ========================================
    print("\n🏆 测试3: 意图排序")
    print("-" * 80)

    result = semantic_analysis_handler(
        action="rank_intents",
        text1="帮我写个故事",
        top_k=3
    )

    print(f"✅ 状态: {result['status']}")
    if result['status'] == 'success':
        print(f"📊 排序结果 (Top {len(result['ranked_intents'])}):")
        for i, item in enumerate(result['ranked_intents'], 1):
            print(f"  {i}. {item['intent']}: {item['score']:.4f}")
        print(f"📋 总意图数: {result['total_intents']}")
    else:
        print(f"❌ 错误: {result.get('error')}")
        return False

    # ========================================
    # 测试4: 添加意图示例
    # ========================================
    print("\n📚 测试4: 添加意图示例")
    print("-" * 80)

    result = semantic_analysis_handler(
        action="add_examples",
        intent_examples={
            "test_intent": ["测试示例1", "测试示例2", "测试示例3"]
        }
    )

    print(f"✅ 状态: {result['status']}")
    if result['status'] == 'success':
        print(f"📋 添加的意图: {', '.join(result['added_intents'])}")
        print(f"💡 提示: {result['message']}")
    else:
        print(f"❌ 错误: {result.get('error')}")
        return False

    # ========================================
    # 测试5: 训练模型
    # ========================================
    print("\n🚀 测试5: 训练模型")
    print("-" * 80)

    result = semantic_analysis_handler(
        action="train_model"
    )

    print(f"✅ 状态: {result['status']}")
    if result['status'] == 'success':
        print(f"💬 消息: {result['message']}")
        print(f"📊 总意图数: {result['total_intents']}")
        print(f"✅ 已训练: {result['is_trained']}")
    else:
        print(f"❌ 错误: {result.get('error')}")
        return False

    # ========================================
    # 测试6: 错误处理
    # ========================================
    print("\n⚠️  测试6: 错误处理")
    print("-" * 80)

    # 测试缺少参数
    result = semantic_analysis_handler(
        action="calculate_similarity",
        text1="只有一个文本"
        # 缺少text2参数
    )

    print(f"✅ 状态: {result['status']}")
    if result['status'] == 'error':
        print(f"✅ 正确捕获错误: {result['error']}")
        print(f"📋 错误代码: {result['code']}")
    else:
        print("❌ 应该返回错误但没有")
        return False

    return True


def test_tool_registration():
    """测试工具注册"""
    from core.tools.semantic_analysis_registration import register_semantic_analysis_tool
    from core.tools.unified_registry import get_unified_registry

    print("\n" + "=" * 80)
    print("🔧 工具注册测试")
    print("=" * 80)

    # 注册工具
    print("\n📝 注册工具...")
    success = register_semantic_analysis_tool()

    if not success:
        print("❌ 工具注册失败")
        return False

    print("✅ 工具注册成功")

    # 验证注册
    print("\n🔍 验证注册...")
    registry = get_unified_registry()
    tool = registry.get("semantic_analysis")

    if not tool:
        print("❌ 工具未在注册表中找到")
        return False

    print("✅ 工具已在注册表中找到")
    print("📊 工具信息:")
    print(f"  - ID: {tool.tool_id}")
    print(f"  - 名称: {tool.name}")
    print(f"  - 分类: {tool.category.value}")
    print(f"  - 优先级: {tool.priority.value}")
    print(f"  - 描述: {tool.description[:80]}...")

    # 测试工具调用
    print("\n🧪 测试工具调用...")
    result = tool.function(
        action="calculate_similarity",
        text1="测试文本1",
        text2="测试文本2"
    )

    print(f"✅ 调用状态: {result['status']}")
    if result['status'] == 'success':
        print(f"📈 相似度: {result['similarity']:.4f}")
    else:
        print(f"❌ 调用失败: {result.get('error')}")
        return False

    return True


def test_convenience_functions():
    """测试便捷函数"""
    from core.tools.semantic_analysis_handler import (
        calculate_text_similarity,
        find_text_intent,
    )

    print("\n" + "=" * 80)
    print("⚡ 便捷函数测试")
    print("=" * 80)

    # 测试calculate_text_similarity
    print("\n📊 测试 calculate_text_similarity:")
    similarity = calculate_text_similarity("帮我写个故事", "创作文案内容")
    print(f"✅ 相似度: {similarity:.4f}")

    # 测试find_text_intent
    print("\n🎯 测试 find_text_intent:")
    intent, confidence = find_text_intent(
        "检索人工智能相关专利",
        intent_examples={
            "patent_search": ["检索专利", "搜索专利"],
            "creative_writing": ["写故事", "创作文案"]
        }
    )
    print(f"✅ 意图: {intent}")
    print(f"✅ 置信度: {confidence:.4f}")

    return True


def main():
    """主测试函数"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "语义分析工具完整验证测试" + " " * 30 + "║")
    print("║" + " " * 15 + "Semantic Analysis Tool Verification Test" + " " * 24 + "║")
    print("╚" + "=" * 78 + "╝")

    all_passed = True

    # 测试1: Handler功能测试
    try:
        if not test_semantic_analysis_handler():
            all_passed = False
            print("\n❌ Handler功能测试失败")
        else:
            print("\n✅ Handler功能测试通过")
    except Exception as e:
        all_passed = False
        print(f"\n❌ Handler功能测试异常: {e}")

    # 测试2: 工具注册测试
    try:
        if not test_tool_registration():
            all_passed = False
            print("\n❌ 工具注册测试失败")
        else:
            print("\n✅ 工具注册测试通过")
    except Exception as e:
        all_passed = False
        print(f"\n❌ 工具注册测试异常: {e}")

    # 测试3: 便捷函数测试
    try:
        if not test_convenience_functions():
            all_passed = False
            print("\n❌ 便捷函数测试失败")
        else:
            print("\n✅ 便捷函数测试通过")
    except Exception as e:
        all_passed = False
        print(f"\n❌ 便捷函数测试异常: {e}")

    # 最终结果
    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 所有测试通过！semantic_analysis工具验证成功")
        print("=" * 80)
        return 0
    else:
        print("❌ 部分测试失败，请检查错误信息")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    exit(main())
