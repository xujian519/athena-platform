from __future__ import annotations
"""
统一意图识别服务
Unified Intent Recognition Service

提供统一的意图识别引擎接口,支持多种实现方式:
- enhanced: 基于关键词和模式匹配的增强引擎
- semantic: 集成NLP语义分析的语义增强引擎
- adapter: BGE模型和BERT分类器的适配器

作者: Athena AI系统
版本: 2.0.0
"""

from typing import Any, Optional

from core.intent.base_engine import (
    BaseIntentEngine,
    ComplexityLevel,
    EngineStats,
    IntentCategory,
    IntentEngineFactory,
    IntentResult,
    IntentType,
    create_default_result,
    infer_category_from_intent,
    merge_results,
)

# 导入具体实现
from core.intent.enhanced_intent_recognition import (
    EnhancedIntentRecognitionEngine,
    create_enhanced_intent_engine,
    get_enhanced_intent_engine,
)
from core.intent.enhanced_intent_recognition import (
    recognize_intent as recognize_intent_enhanced,
)
from core.intent.enhanced_intent_recognition import (
    recognize_intent_async as recognize_intent_enhanced_async,
)

# ========================================================================
# 统一入口
# ========================================================================


def get_intent_engine(
    engine_type: str = "enhanced", config: dict[str, Any] | None = None
) -> BaseIntentEngine:
    """
    获取意图识别引擎(统一入口)

    Args:
        engine_type: 引擎类型
            - "enhanced" 或 "keyword": 基于关键词和模式的引擎(默认)
            - "semantic": 语义增强引擎(需要NLP模块)
            - "adapter": BGE/BERT模型适配器
        config: 配置字典

    Returns:
        意图识别引擎实例

    Raises:
        ValueError: 不支持的引擎类型

    示例:
        >>> engine = get_intent_engine("enhanced")
        >>> result = engine.recognize_intent("帮我写代码")
        >>> print(result.intent)
    """
    if engine_type in ("enhanced", "keyword", "enhanced_keyword"):
        return EnhancedIntentRecognitionEngine(config)

    elif engine_type == "semantic":
        # 延迟导入以避免循环依赖
        from core.intent.semantic_enhanced_intent_engine import (
            SemanticEnhancedIntentEngine,
        )

        # 返回引擎实例(不初始化异步部分)
        return SemanticEnhancedIntentEngine()

    elif engine_type == "adapter":
        # 延迟导入
        from core.intent.intent_recognition_adapter import (
            IntentRecognitionAdapter,
        )

        # IntentRecognitionAdapter现在继承BaseIntentEngine,接受config字典
        return IntentRecognitionAdapter({"use_phase2_model": True})

    else:
        raise ValueError(
            f"不支持的引擎类型: {engine_type}。" f"支持的类型: enhanced, semantic, adapter"
        )


async def get_intent_engine_async(
    engine_type: str = "semantic", config: dict[str, Any] | None = None
) -> BaseIntentEngine:
    """
    获取意图识别引擎(异步版本,用于需要异步初始化的引擎)

    Args:
        engine_type: 引擎类型
        config: 配置字典

    Returns:
        已初始化的意图识别引擎实例
    """
    if engine_type == "semantic":
        from core.intent.semantic_enhanced_intent_engine import (
            SemanticEnhancedIntentEngine,
            get_semantic_intent_engine,
        )

        return await get_semantic_intent_engine()

    else:
        # 其他引擎不需要异步初始化
        return get_intent_engine(engine_type, config)


# ========================================================================
# 便捷函数
# ========================================================================


def recognize_intent(
    text: str, context: dict[str, Any] | None = None, engine_type: str = "enhanced"
) -> IntentResult:
    """
    识别意图(同步便捷函数)

    Args:
        text: 输入文本
        context: 上下文信息
        engine_type: 引擎类型

    Returns:
        意图识别结果
    """
    engine = get_intent_engine(engine_type)
    return engine.recognize_intent(text, context)


async def recognize_intent_async(
    text: str,
    context: dict[str, Any] | None = None,
    user_id: str | None = None,
    engine_type: str = "enhanced",
) -> IntentResult:
    """
    识别意图(异步便捷函数)

    Args:
        text: 输入文本
        context: 上下文信息
        user_id: 用户ID
        engine_type: 引擎类型

    Returns:
        意图识别结果
    """
    if engine_type == "semantic":
        # Semantic引擎需要异步初始化
        engine = await get_intent_engine_async(engine_type)
        return await engine.recognize_intent_async(text, context, user_id)
    else:
        # 其他引擎直接使用同步或异步方法
        engine = get_intent_engine(engine_type)
        return await engine.recognize_intent_async(text, context, user_id)


# ========================================================================
# 工厂注册
# ========================================================================


def register_custom_engine(engine_type: str, engine_class: type[BaseIntentEngine]) -> None:
    """
    注册自定义引擎

    Args:
        engine_type: 引擎类型标识
        engine_class: 引擎类(必须继承BaseIntentEngine)

    示例:
        >>> class MyEngine(BaseIntentEngine):
        ...     pass
        >>> register_custom_engine("my_engine", MyEngine)
    """
    if not issubclass(engine_class, BaseIntentEngine):
        raise TypeError("引擎类必须继承BaseIntentEngine")

    IntentEngineFactory.register(engine_type, engine_class)


# ========================================================================
# 导出
# ========================================================================

__all__ = [
    # 基础类
    "BaseIntentEngine",
    "ComplexityLevel",
    "EngineStats",
    # 具体实现
    "EnhancedIntentRecognitionEngine",
    "IntentCategory",
    # 工厂和创建函数
    "IntentEngineFactory",
    "IntentResult",
    "IntentType",
    "create_default_result",
    "create_enhanced_intent_engine",
    "get_enhanced_intent_engine",
    "get_intent_engine",
    "get_intent_engine_async",
    # 辅助函数
    "infer_category_from_intent",
    "merge_results",
    # 便捷函数
    "recognize_intent",
    "recognize_intent_async",
    "recognize_intent_enhanced",
    "recognize_intent_enhanced_async",
    "register_custom_engine",
]

__version__ = "2.0.0"
