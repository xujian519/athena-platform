#!/usr/bin/env python3
"""
语义分析工具处理器
Semantic Analysis Tool Handler

提供文本语义分析功能，包括：
1. 文本相似度计算
2. 意图识别
3. 语义匹配排序
4. 文本预处理

Author: Athena平台团队
Created: 2026-04-19
Version: v1.0.0
"""

import logging
from typing import Any, Dict, List, Optional

from core.logging_config import setup_logging

# 导入语义相似度模块
from core.nlp.stable_semantic_similarity import (
    StableSemanticSimilarity,
    get_stable_semantic_similarity,
)

logger = setup_logging()


# ========================================
# 语义分析Handler函数
# ========================================

def semantic_analysis_handler(
    action: str,
    text1: Optional[str] = None,
    text2: Optional[str] = None,
    intent_examples: Optional[dict[str, list[str]] = None,
    top_k: int = 5,
    train_model: bool = False,
) -> dict[str, Any]:
    """
    语义分析工具Handler

    Args:
        action: 操作类型
            - "calculate_similarity": 计算两个文本的相似度
            - "find_best_intent": 从意图列表中找到最佳匹配
            - "rank_intents": 根据相似度对意图进行排序
            - "add_examples": 添加意图训练示例
            - "train_model": 训练语义模型
        text1: 第一个文本（用于相似度计算）
        text2: 第二个文本（用于相似度计算）
        intent_examples: 意图示例字典 {"intent_type": ["example1", "example2"]}
        top_k: 返回前K个结果（用于rank_intents）
        train_model: 是否重新训练模型

    Returns:
        分析结果字典

    Examples:
        >>> # 计算相似度
        >>> result = semantic_analysis_handler(
        ...     action="calculate_similarity",
        ...     text1="帮我写个故事",
        ...     text2="创作文案内容"
        ... )

        >>> # 意图识别
        >>> result = semantic_analysis_handler(
        ...     action="find_best_intent",
        ...     text1="检索人工智能专利",
        ...     intent_examples={
        ...         "patent_search": ["检索专利", "搜索专利"],
        ...         "creative_writing": ["写故事", "创作文案"]
        ...     }
        ... )

        >>> # 意图排序
        >>> result = semantic_analysis_handler(
        ...     action="rank_intents",
        ...     text1="帮我写个故事",
        ...     top_k=3
        ... )
    """
    try:
        # 获取语义分析器实例
        analyzer = get_stable_semantic_similarity()

        # ========================================
        # 1. 计算文本相似度
        # ========================================
        if action == "calculate_similarity":
            if not text1 or not text2:
                return {
                    "status": "error",
                    "error": "text1和text2参数不能为空",
                    "code": "MISSING_PARAMS"
                }

            similarity = analyzer.calculate_similarity(text1, text2)

            return {
                "status": "success",
                "action": "calculate_similarity",
                "similarity": similarity,
                "text1": text1,
                "text2": text2,
                "interpretation": _interpret_similarity(similarity),
            }

        # ========================================
        # 2. 查找最佳意图匹配
        # ========================================
        elif action == "find_best_intent":
            if not text1:
                return {
                    "status": "error",
                    "error": "text1参数不能为空",
                    "code": "MISSING_PARAMS"
                }

            # 如果提供了新的意图示例，先添加
            if intent_examples:
                for intent_type, examples in intent_examples.items():
                    analyzer.add_intent_examples(intent_type, examples)

                # 重新训练模型
                if train_model:
                    analyzer.train()

            # 获取所有可用的意图类型
            available_intents = list(analyzer.intent_examples.keys())

            if not available_intents:
                return {
                    "status": "error",
                    "error": "没有可用的意图类型，请先添加意图示例",
                    "code": "NO_INTENTS"
                }

            best_intent, score = analyzer.find_best_intent(text1, available_intents)

            return {
                "status": "success",
                "action": "find_best_intent",
                "text": text1,
                "best_intent": best_intent,
                "confidence": score,
                "interpretation": _interpret_confidence(score),
                "available_intents": available_intents,
            }

        # ========================================
        # 3. 意图排序
        # ========================================
        elif action == "rank_intents":
            if not text1:
                return {
                    "status": "error",
                    "error": "text1参数不能为空",
                    "code": "MISSING_PARAMS"
                }

            # 如果提供了新的意图示例，先添加
            if intent_examples:
                for intent_type, examples in intent_examples.items():
                    analyzer.add_intent_examples(intent_type, examples)

                # 重新训练模型
                if train_model:
                    analyzer.train()

            # 排序意图
            ranked_intents = analyzer.rank_intents_by_similarity(text1, top_k=top_k)

            return {
                "status": "success",
                "action": "rank_intents",
                "text": text1,
                "ranked_intents": [
                    {"intent": intent, "score": score}
                    for intent, score in ranked_intents
                ],
                "total_intents": len(analyzer.intent_examples),
            }

        # ========================================
        # 4. 添加意图示例
        # ========================================
        elif action == "add_examples":
            if not intent_examples:
                return {
                    "status": "error",
                    "error": "intent_examples参数不能为空",
                    "code": "MISSING_PARAMS"
                }

            # 添加示例
            for intent_type, examples in intent_examples.items():
                analyzer.add_intent_examples(intent_type, examples)
                logger.info(f"✅ 添加意图示例: {intent_type} ({len(examples)}个)")

            return {
                "status": "success",
                "action": "add_examples",
                "added_intents": list(intent_examples.keys()),
                "message": "意图示例已添加，使用train_model=True重新训练模型",
            }

        # ========================================
        # 5. 训练模型
        # ========================================
        elif action == "train_model":
            analyzer.train()

            return {
                "status": "success",
                "action": "train_model",
                "message": "语义模型训练完成",
                "total_intents": len(analyzer.intent_examples),
                "is_trained": analyzer.is_trained,
            }

        # ========================================
        # 未知操作
        # ========================================
        else:
            return {
                "status": "error",
                "error": f"未知的操作类型: {action}",
                "code": "UNKNOWN_ACTION",
                "supported_actions": [
                    "calculate_similarity",
                    "find_best_intent",
                    "rank_intents",
                    "add_examples",
                    "train_model",
                ],
            }

    except Exception as e:
        logger.error(f"❌ 语义分析失败: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "code": "ANALYSIS_FAILED"
        }


# ========================================
# 辅助函数
# ========================================

def _interpret_similarity(score: float) -> str:
    """
    解释相似度分数

    Args:
        score: 相似度分数 (0-1)

    Returns:
        解释文本
    """
    if score >= 0.8:
        return "高度相似 - 语义非常接近"
    elif score >= 0.6:
        return "相似 - 语义较为相关"
    elif score >= 0.4:
        return "中等相似 - 有一定关联"
    elif score >= 0.2:
        return "低相似度 - 关联较弱"
    else:
        return "不相似 - 基本无关联"


def _interpret_confidence(score: float) -> str:
    """
    解释置信度分数

    Args:
        score: 置信度分数 (0-1)

    Returns:
        解释文本
    """
    if score >= 0.8:
        return "高置信度 - 匹配结果非常可靠"
    elif score >= 0.6:
        return "中等置信度 - 匹配结果较为可靠"
    elif score >= 0.4:
        return "低置信度 - 匹配结果可能不准确"
    else:
        return "极低置信度 - 匹配结果不可靠"


# ========================================
# 便捷函数
# ========================================

def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    计算两个文本的语义相似度

    Args:
        text1: 第一个文本
        text2: 第二个文本

    Returns:
        相似度分数 (0-1)
    """
    result = semantic_analysis_handler(
        action="calculate_similarity",
        text1=text1,
        text2=text2
    )

    if result["status"] == "success":
        return result["similarity"]
    else:
        return 0.0


def find_text_intent(
    text: str,
    intent_examples: Optional[dict[str, list[str]] = None
) -> tuple[str, float]:
    """
    识别文本的意图

    Args:
        text: 输入文本
        intent_examples: 意图示例字典（可选）

    Returns:
        (意图类型, 置信度)
    """
    result = semantic_analysis_handler(
        action="find_best_intent",
        text1=text,
        intent_examples=intent_examples,
        train_model=True if intent_examples else False
    )

    if result["status"] == "success":
        return result["best_intent"], result["confidence"]
    else:
        return None, 0.0


# ========================================
# 测试代码
# ========================================

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 语义分析工具测试")
    print("=" * 60)

    # 测试1: 计算相似度
    print("\n📊 测试1: 计算文本相似度")
    print("-" * 60)
    result = semantic_analysis_handler(
        action="calculate_similarity",
        text1="帮我写个故事",
        text2="创作文案内容"
    )
    print(f"✅ 相似度: {result['similarity']:.4f}")
    print(f"📝 解释: {result['interpretation']}")

    # 测试2: 意图识别
    print("\n🎯 测试2: 意图识别")
    print("-" * 60)
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
    print(f"✅ 最佳意图: {result['best_intent']}")
    print(f"📊 置信度: {result['confidence']:.4f}")
    print(f"📝 解释: {result['interpretation']}")

    # 测试3: 意图排序
    print("\n🏆 测试3: 意图排序")
    print("-" * 60)
    result = semantic_analysis_handler(
        action="rank_intents",
        text1="帮我写个故事",
        top_k=3
    )
    print(f"📊 排序结果:")
    for i, item in enumerate(result['ranked_intents'], 1):
        print(f"  {i}. {item['intent']}: {item['score']:.4f}")

    print("\n" + "=" * 60)
    print("✅ 所有测试完成")
    print("=" * 60)
