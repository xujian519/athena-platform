#!/usr/bin/env python3
from __future__ import annotations
"""
意图识别适配器
Intent Recognition Adapter

统一不同意图识别模型的接口,支持:
- Phase 2 本地BGE模型 (97.17%准确率)
- 原有BERT分类器

继承自BaseIntentEngine,实现统一的意图识别接口。

作者: 小诺·双鱼公主
版本: 2.0.0
创建: 2025-12-29
更新: 2026-01-20 (重构为继承BaseIntentEngine)
"""

import logging
import sys
import time
from pathlib import Path
from typing import Any

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入基类
from core.intent.base_engine import (
    BaseIntentEngine,
    ComplexityLevel,
    IntentResult,
    IntentType,
    create_default_result,
    infer_category_from_intent,
)

logger = logging.getLogger(__name__)


class IntentRecognitionAdapter(BaseIntentEngine):
    """
    意图识别适配器 - 统一接口

    继承自BaseIntentEngine,包装不同的分类器实现:
    - Phase 2 BGE分类器 (97.17%准确率)
    - 原有BERT分类器

    继承关系: BaseIntentEngine → IntentRecognitionAdapter
    """

    engine_name = "intent_adapter"
    engine_version = "2.0.0"

    # 支持的意图类别(字符串常量,用于兼容)
    SUPPORTED_INTENTS = [
        "CODE_GENERATION",
        "CREATIVE_WRITING",
        "DATA_ANALYSIS",
        "EMOTIONAL",
        "LEGAL_QUERY",
        "OPINION_RESPONSE",
        "PATENT_DRAFTING",
        "PATENT_SEARCH",
        "PROBLEM_SOLVING",
        "SYSTEM_CONTROL",
    ]

    def __init__(self, config: dict[str, Any] | None = None):
        """
        初始化适配器

        Args:
            config: 配置字典,支持的配置项:
                - use_phase2_model: 是否使用Phase 2高精度模型 (默认: True)
                - model_dir: Phase 2模型目录(可选)
        """
        # 解析配置
        if config is None:
            config = {}
        use_phase2_model = config.get("use_phase2_model", True)
        model_dir = config.get("model_dir")

        # 先设置适配器特定属性
        self.use_phase2_model = use_phase2_model
        self.model_dir = model_dir
        self.classifier = None

        # 调用父类初始化
        super().__init__(config)

        # 初始化分类器(在_initialize中实现)
        logger.info("🎯 初始化意图识别适配器...")

    def _initialize(self) -> None:
        """初始化分类器(由BaseIntentEngine调用)"""
        if self.use_phase2_model:
            self._init_phase2_classifier()
        else:
            self._init_legacy_classifier()

    def _init_phase2_classifier(self) -> Any:
        """初始化Phase 2本地BGE分类器"""
        try:
            from core.intent.local_bge_phase2_classifier import LocalBGEPhase2Classifier

            logger.info("📂 使用Phase 2本地BGE模型 (97.17%准确率)")

            # 初始化分类器
            self.classifier = LocalBGEPhase2Classifier(use_local_model=True)

            # 确定模型目录
            if self.model_dir is None:
                self.model_dir = project_root / "models/intent_recognition/unified_classifier"

            # 加载训练好的模型
            if self.model_dir.exists():
                import joblib

                self.classifier.classifier = joblib.load(self.model_dir / "classifier.joblib")
                self.classifier.label_encoder = joblib.load(self.model_dir / "label_encoder.joblib")
                logger.info(f"✅ Phase 2模型加载成功: {self.model_dir}")
                logger.info(f"📊 意图类别: {len(self.get_supported_intents())}个")
                logger.info("🎯 准确率: 97.17%")
            else:
                logger.warning(f"⚠️ Phase 2模型不存在: {self.model_dir}")
                logger.info("💡 提示: 请先运行训练脚本生成模型")
                raise FileNotFoundError(f"模型不存在: {self.model_dir}")

        except Exception as e:
            logger.error(f"❌ Phase 2模型初始化失败: {e}")
            logger.info("🔄 尝试使用原有BERT分类器...")
            self.use_phase2_model = False
            self._init_legacy_classifier()

    def _init_legacy_classifier(self) -> Any:
        """初始化原有BERT分类器"""
        try:
            from core.nlp.optimized_bert_intent_classifier import get_optimized_bert_classifier

            logger.info("📂 使用原有BERT分类器")
            self.classifier = get_optimized_bert_classifier()
            self.use_phase2_model = False
            logger.info("✅ 原有BERT分类器初始化成功")

        except Exception as e:
            logger.error(f"❌ 原有BERT分类器初始化失败: {e}")
            # 不抛出异常,而是让引擎进入degraded状态
            self.classifier = None
            logger.warning("⚠️ 意图识别适配器进入degraded模式,将返回默认结果")

    def recognize_intent(self, text: str, context: dict[str, Any] | None = None) -> IntentResult:
        """
        识别意图(同步版本)

        Args:
            text: 输入文本
            context: 上下文信息(可选,当前未使用)

        Returns:
            意图识别结果
        """
        start_time = time.time()

        try:
            # 验证输入
            self._validate_input(text)

            # 如果分类器未初始化,返回默认结果
            if self.classifier is None:
                logger.warning("⚠️ 分类器未初始化,返回默认结果")
                return create_default_result(
                    text=text, processing_time_ms=0, model_version=self.engine_version
                )

            # 调用分类器
            raw_result = self._predict_internal(text, top_k=1)

            # 转换为IntentResult
            result = self._convert_to_intent_result(
                raw_result, text, (time.time() - start_time) * 1000
            )

            # 更新统计
            self._update_stats(
                success=True, processing_time_ms=result.processing_time_ms, cache_hit=False
            )

            return result

        except Exception as e:
            self.logger.error(f"❌ 意图识别失败: {e}")
            # 更新统计
            self._update_stats(
                success=False, processing_time_ms=(time.time() - start_time) * 1000, cache_hit=False
            )
            # 返回默认结果
            return create_default_result(
                text=text,
                processing_time_ms=(time.time() - start_time) * 1000,
                model_version=self.engine_version,
            )

    def _predict_internal(self, text: str, top_k: int = 3) -> dict[str, Any]:
        """
        内部预测方法

        Args:
            text: 输入文本
            top_k: 返回top-k结果

        Returns:
            预测结果字典
        """
        if self.use_phase2_model:
            # Phase 2模型调用
            result = self.classifier.predict(text, top_k=top_k)
            return {
                "intent": result["intent"],
                "confidence": result["confidence"],
                "top_k": result["top_k"],
                "inference_time": result["inference_time"],
                "model_type": "Phase 2 BGE + RandomForest",
            }
        else:
            # 原有BERT分类器调用
            result = self.classifier.predict_intent(text, top_k=top_k)
            return {
                "intent": result.get("intent", "UNKNOWN"),
                "confidence": result.get("confidence", 0.0),
                "top_k": result.get("top_k", []),
                "inference_time": result.get("inference_time", 0.0),
                "model_type": "Legacy BERT",
            }

    def _convert_to_intent_result(
        self, raw_result: dict[str, Any], text: str, processing_time_ms: float
    ) -> IntentResult:
        """
        将内部预测结果转换为IntentResult

        Args:
            raw_result: 内部预测结果
            text: 原始文本
            processing_time_ms: 处理时间

        Returns:
            IntentResult对象
        """
        # 转换意图字符串到IntentType枚举
        intent_str = raw_result.get("intent", "UNKNOWN")
        try:
            intent = IntentType(intent_str)
        except ValueError:
            # 如果无法映射,使用UNKNOWN
            logger.warning(f"⚠️ 未知意图类型: {intent_str},映射为UNKNOWN")
            intent = IntentType.UNKNOWN

        # 推断类别
        category = infer_category_from_intent(intent)

        # 确定复杂度
        complexity = self._determine_complexity(text, intent)

        # 构建结果
        return IntentResult(
            intent=intent,
            confidence=raw_result.get("confidence", 0.0),
            category=category,
            raw_text=text,
            processing_time_ms=processing_time_ms,
            model_version=f"{self.engine_version} ({raw_result.get('model_type', 'unknown')})",
            entities=self._extract_entities(text),
            key_concepts=[],
            complexity=complexity,
            semantic_similarity=raw_result.get("confidence", 0.0),
            context_requirements=[],
            suggested_tools=self._get_suggested_tools(intent),
            processing_strategy=self._get_processing_strategy(intent),
            estimated_time=self._estimate_time(complexity),
            metadata={
                "top_k": raw_result.get("top_k", []),
                "inference_time": raw_result.get("inference_time", 0.0),
                "model_type": raw_result.get("model_type", "unknown"),
            },
        )

    def _determine_complexity(self, text: str, intent: IntentType) -> ComplexityLevel:
        """确定任务复杂度"""
        word_count = len(text.split())

        # 高复杂度意图
        high_complexity_intents = {
            IntentType.OPINION_RESPONSE,
            IntentType.INFRINGEMENT_ANALYSIS,
            IntentType.PATENT_COMPARISON,
        }

        if word_count < 10:
            return ComplexityLevel.SIMPLE
        elif intent in high_complexity_intents or word_count > 50:
            return ComplexityLevel.COMPLEX
        elif word_count > 30:
            return ComplexityLevel.EXPERT
        else:
            return ComplexityLevel.MEDIUM

    def _get_suggested_tools(self, intent: IntentType) -> list[str]:
        """获取建议使用的工具"""
        tool_map = {
            IntentType.PATENT_SEARCH: ["patent_search", "patent_database"],
            IntentType.PATENT_ANALYSIS: ["patent_analyzer", "nlp_processor"],
            IntentType.CODE_GENERATION: ["code_generator", "linter"],
            IntentType.OPINION_RESPONSE: ["legal_analyzer", "template_manager"],
            IntentType.DATA_ANALYSIS: ["data_processor", "visualizer"],
        }
        return tool_map.get(intent, [])

    def _get_processing_strategy(self, intent: IntentType) -> str:
        """获取处理策略描述"""
        strategy_map = {
            IntentType.PATENT_SEARCH: "使用混合检索策略(关键词+向量+图谱)",
            IntentType.PATENT_ANALYSIS: "使用深度分析策略(NLP+规则引擎)",
            IntentType.CODE_GENERATION: "使用模板生成策略",
            IntentType.OPINION_RESPONSE: "使用法律推理策略",
        }
        return strategy_map.get(intent, "使用标准处理流程")

    def _estimate_time(self, complexity: ComplexityLevel) -> float:
        """估算处理时间"""
        time_map = {
            ComplexityLevel.SIMPLE: 1.0,
            ComplexityLevel.MEDIUM: 3.0,
            ComplexityLevel.COMPLEX: 8.0,
            ComplexityLevel.EXPERT: 15.0,
        }
        return time_map.get(complexity, 3.0)

    def get_supported_intents(self) -> list[str]:
        """
        获取支持的意图列表

        Returns:
            意图类别列表
        """
        if self.use_phase2_model and self.classifier and hasattr(self.classifier, "label_encoder"):
            if self.classifier.label_encoder:
                return list(self.classifier.label_encoder.classes_)
        return self.SUPPORTED_INTENTS.copy()

    def get_adapter_stats(self) -> dict[str, Any]:
        """
        获取适配器性能统计信息

        Returns:
            统计信息字典
        """
        base_stats = self.get_stats()

        return {
            "total_predictions": base_stats.total_requests,
            "successful_predictions": base_stats.successful_requests,
            "avg_processing_time_ms": base_stats.avg_processing_time_ms,
            "model_type": "Phase 2 BGE" if self.use_phase2_model else "Legacy BERT",
            "accuracy": "97.17%" if self.use_phase2_model else "N/A",
            "supported_intents": self.get_supported_intents(),
        }


# ========================================================================
# 工厂函数
# ========================================================================


def create_intent_adapter(
    use_phase2_model: bool | None = None, model_dir: Path | None = None
) -> IntentRecognitionAdapter:
    """
    创建意图识别适配器(便捷函数)

    Args:
        use_phase2_model: 是否使用Phase 2高精度模型
        model_dir: Phase 2模型目录(可选)

    Returns:
        适配器实例
    """
    config = {"use_phase2_model": use_phase2_model, "model_dir": model_dir}
    return IntentRecognitionAdapter(config)


def get_default_adapter() -> IntentRecognitionAdapter:
    """
    获取默认的意图识别适配器

    优先使用Phase 2模型,如果不可用则回退到原有模型

    Returns:
        适配器实例
    """
    try:
        return IntentRecognitionAdapter({"use_phase2_model": True})
    except Exception as e:
        logger.warning(f"⚠️ Phase 2模型不可用,使用原有模型: {e}")
        return IntentRecognitionAdapter({"use_phase2_model": False})


# 注册到工厂
from core.intent.base_engine import IntentEngineFactory

IntentEngineFactory.register("adapter", IntentRecognitionAdapter)


# ========================================================================
# 测试代码
# ========================================================================

if __name__ == "__main__":

    async def test_adapter():
        """测试适配器功能"""
        print("\n" + "=" * 80)
        print("🧪 意图识别适配器测试")
        print("=" * 80)

        # 创建适配器
        print("\n1️⃣ 创建适配器...")
        try:
            adapter = create_intent_adapter(use_phase2_model=True)
        except Exception as e:
            print(f"⚠️ Phase 2模型不可用: {e}")
            print("🔄 使用原有模型...")
            adapter = create_intent_adapter(use_phase2_model=False)

        # 测试用例
        print("\n2️⃣ 测试意图预测...")
        test_cases = [
            "帮我写Python代码",
            "检索人工智能专利",
            "谢谢爸爸",
            "启动服务",
            "分析这个专利",
        ]

        for text in test_cases:
            result = adapter.recognize_intent(text)

            print(f"\n📝 输入: '{text}'")
            print(f"   意图: {result.intent.value}")
            print(f"   置信度: {result.confidence:.2%}")
            print(f"   类别: {result.category.value}")
            print(f"   复杂度: {result.complexity.value}")
            print(f"   处理时间: {result.processing_time_ms:.1f}ms")

        # 统计信息
        print("\n3️⃣ 性能统计...")
        stats = adapter.get_adapter_stats()
        print(f"   总预测数: {stats['total_predictions']}")
        print(f"   成功预测: {stats['successful_predictions']}")
        print(f"   平均时间: {stats['avg_processing_time_ms']:.1f}ms")
        print(f"   模型类型: {stats['model_type']}")
        print(f"   准确率: {stats['accuracy']}")

        # 支持的意图
        print("\n4️⃣ 支持的意图类别...")
        intents = adapter.get_supported_intents()
        print(f"   总数: {len(intents)}个")
        for intent in intents[:10]:  # 只显示前10个
            print(f"   • {intent}")
        if len(intents) > 10:
            print(f"   ... 还有{len(intents)-10}个")

        print("\n✅ 测试完成!")

    import asyncio

    asyncio.run(test_adapter())
