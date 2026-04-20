#!/usr/bin/env python3
"""
语义分析工具注册模块
Semantic Analysis Tool Registration

将semantic_analysis工具注册到统一工具注册表。

Author: Athena平台团队
Created: 2026-04-19
Version: v1.0.0
"""

import logging
from typing import TYPE_CHECKING

from core.tools.base import (
    ToolCapability,
    ToolCategory,
    ToolDefinition,
    ToolPriority,
)

if TYPE_CHECKING:
    from .semantic_analysis_handler import semantic_analysis_handler

logger = logging.getLogger(__name__)


def create_semantic_analysis_tool_definition() -> ToolDefinition:
    """
    创建语义分析工具定义

    Returns:
        ToolDefinition: 语义分析工具定义
    """
    from .semantic_analysis_handler import semantic_analysis_handler

    return ToolDefinition(
        tool_id="semantic_analysis",
        name="文本语义分析",
        description="""
文本语义分析工具 - 提供高精度的语义理解能力

核心功能:
1. 文本相似度计算 - 基于TF-IDF和余弦相似度
2. 意图识别 - 从候选意图中找到最佳匹配
3. 语义排序 - 按相似度对意图进行排序
4. 意图学习 - 支持添加自定义训练示例

技术特点:
- 使用jieba分词进行中文文本预处理
- TF-IDF向量化（max_features=3000）
- 余弦相似度计算
- 支持多语言（中文优化）

适用场景:
- 用户意图识别
- 文本相似度匹配
- 语义搜索重排序
- 问答系统意图分类
        """,
        category=ToolCategory.SEMANTIC_ANALYSIS,
        priority=ToolPriority.MEDIUM,
        capability=ToolCapability(
            input_types=["text", "query", "intent_examples"],
            output_types=["similarity_score", "intent_match", "ranking"],
            domains=["nlp", "semantic", "intent", "classification"],
            task_types=["analyze", "match", "rank", "classify"],
            features={
                "text_similarity": True,
                "intent_recognition": True,
                "semantic_ranking": True,
                "custom_training": True,
                "chinese_optimized": True,
                "tfidf_vectorizer": True,
                "cosine_similarity": True,
            }
        ),
        required_params=["action"],
        optional_params=[
            "text1",
            "text2",
            "intent_examples",
            "top_k",
            "train_model"
        ],
        handler=semantic_analysis_handler,
        timeout=30.0,
        enabled=True,
    )


def register_semantic_analysis_tool() -> bool:
    """
    注册语义分析工具到统一工具注册表

    Returns:
        bool: 注册是否成功
    """
    from core.tools.unified_registry import get_unified_registry

    registry = get_unified_registry()

    try:
        # 创建工具定义
        tool_definition = create_semantic_analysis_tool_definition()

        # 注册工具
        registry.register(tool_definition)

        logger.info("✅ 语义分析工具已成功注册: semantic_analysis")
        return True

    except Exception as e:
        logger.error(f"❌ 语义分析工具注册失败: {e}")
        return False


# 自动注册（当模块被导入时）
if __name__ != "__main__":
    register_semantic_analysis_tool()


# ========================================
# 测试代码
# ========================================

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 语义分析工具注册测试")
    print("=" * 60)

    # 注册工具
    success = register_semantic_analysis_tool()

    if success:
        print("\n✅ 工具注册成功！")

        # 验证注册
        from core.tools.unified_registry import get_unified_registry
        registry = get_unified_registry()

        # 获取工具
        tool = registry.get("semantic_analysis")

        if tool:
            print("\n📊 工具信息:")
            print(f"  工具ID: {tool.tool_id}")
            print(f"  名称: {tool.name}")
            print(f"  分类: {tool.category.value}")
            print(f"  优先级: {tool.priority.value}")
            print(f"  描述: {tool.description[:100]}...")

            # 测试工具调用
            print("\n🧪 测试工具调用:")
            result = tool.function(
                action="calculate_similarity",
                text1="帮我写个故事",
                text2="创作文案内容"
            )

            print(f"  状态: {result['status']}")
            if result['status'] == 'success':
                print(f"  相似度: {result['similarity']:.4f}")
                print(f"  解释: {result['interpretation']}")
        else:
            print("\n❌ 工具未找到")
    else:
        print("\n❌ 工具注册失败")

    print("\n" + "=" * 60)
