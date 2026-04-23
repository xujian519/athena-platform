#!/usr/bin/env python3
from __future__ import annotations
"""
语义增强意图识别引擎
Semantic-Enhanced Intent Recognition Engine

基于平台现有NLP能力的语义增强版本,继承自EnhancedIntentRecognitionEngine:
1. 集成平台语义相似度模块
2. 集成BGE嵌入服务
3. 集成智能语义路由器
4. 复用平台缓存机制

预期提升: +8-12% (语义理解增强)

作者: Athena AI系统
版本: 2.0.0
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Any

import numpy as np

# 导入基类
from core.intent.base_engine import (
    IntentResult,
    IntentType,
    infer_category_from_intent,
)
from core.intent.enhanced_intent_recognition import EnhancedIntentRecognitionEngine

# 导入平台NLP模块
try:
    from core.nlp.xiaonuo_semantic_similarity import (
        SemanticConfig,
        XiaonuoSemanticSimilarity,
    )

    SEMANTIC_SIMILARITY_AVAILABLE = True
except ImportError:
    SEMANTIC_SIMILARITY_AVAILABLE = False
    logging.warning("⚠️ 语义相似度模块不可用")

try:
    from core.embedding.unified_embedding_service import (
        ModuleType,
        UnifiedEmbeddingService,
        get_unified_embedding_service,
    )

    EMBEDDING_SERVICE_AVAILABLE = True
except ImportError:
    EMBEDDING_SERVICE_AVAILABLE = False
    logging.warning("⚠️ 统一嵌入服务不可用")

try:
    from core.vector.semantic_router import SemanticRouter

    SEMANTIC_ROUTER_AVAILABLE = True
except ImportError:
    SEMANTIC_ROUTER_AVAILABLE = False
    logging.warning("⚠️ 语义路由器不可用")

logger = logging.getLogger(__name__)


class SemanticEnhancedIntentEngine(EnhancedIntentRecognitionEngine):
    """
    语义增强意图识别引擎

    继承自EnhancedIntentRecognitionEngine,在关键词+模式匹配的基础上,
    增加语义相似度、嵌入服务、语义路由器等增强功能。

    继承关系: BaseIntentEngine → EnhancedIntentRecognitionEngine → SemanticEnhancedIntentEngine
    """

    engine_name = "semantic_enhanced_engine"
    engine_version = "2.0.0"

    def __init__(self, config: Optional[dict[str, Any]] = None):
        """
        初始化语义增强引擎

        Args:
            config: 配置字典
        """
        super().__init__(config)

        # 语义增强模块
        self.semantic_similarity = None
        self.embedding_service = None
        self.semantic_router = None

        # 意图示例库(用于语义匹配)
        self.intent_examples = self._create_intent_examples()

        # 嵌入缓存
        self.embedding_cache = {}
        self.cache_ttl = 3600  # 1小时缓存

        # 语义增强统计
        self.semantic_stats = {
            "total_intents": 0,
            "semantic_boosts": 0,
            "semantic_hits": 0,
            "semantic_misses": 0,
            "avg_semantic_score": 0.0,
        }

        # 标记异步初始化状态
        self._async_initialized = False

        # 同步初始化NLP模块
        self._initialize_nlp_modules_sync()

        logger.info("🧠 语义增强意图识别引擎初始化完成 (v2.0.0)")

    def _initialize(self) -> None:
        """
        初始化引擎(由BaseIntentEngine调用)

        注意:这里只做同步初始化,异步NLP模块需要在initialize_async中初始化
        """
        pass

    def _initialize_nlp_modules_sync(self) -> Any:
        """同步初始化平台NLP模块"""
        # 1. 初始化语义相似度模块
        if SEMANTIC_SIMILARITY_AVAILABLE:
            try:
                self.semantic_similarity = XiaonuoSemanticSimilarity()
                self.semantic_similarity.train_semantic_models()
                logger.info("✅ 语义相似度模块加载成功")
            except Exception as e:
                logger.warning(f"⚠️ 语义相似度模块加载失败: {e}")
                self.semantic_similarity = None

        # 2. 初始化语义路由器(同步)
        if SEMANTIC_ROUTER_AVAILABLE:
            try:
                self.semantic_router = SemanticRouter()
                logger.info("✅ 语义路由器加载成功")
            except Exception as e:
                logger.warning(f"⚠️ 语义路由器加载失败: {e}")

    async def initialize_async(self):
        """异步初始化(需要调用)"""
        if not self._async_initialized:
            # 初始化嵌入服务
            if EMBEDDING_SERVICE_AVAILABLE:
                try:
                    self.embedding_service = await get_unified_embedding_service()
                    logger.info("✅ 统一嵌入服务初始化成功")
                except Exception as e:
                    logger.warning(f"⚠️ 统一嵌入服务初始化失败: {e}")

            self._async_initialized = True

    def _create_intent_examples(self) -> dict[str, list[str]]:
        """创建意图示例库(用于语义匹配)"""
        return {
            # 专利专业类(扩展)
            "PATENT_SEARCH": [
                "检索人工智能相关专利",
                "搜索机器学习现有技术",
                "查新区块链技术专利",
                "查找深度学习相关专利",
                "专利数据库检索",
                "现有技术对比文件",
                "专利性分析检索",
                "技术方案查新",
                "专利申请前检索",
                "专利布局分析",
            ],
            "OPINION_RESPONSE": [
                "审查意见怎么答复",
                "如何回复审查员意见",
                "审查意见通知书答复",
                "专利审查意见答复策略",
                "驳回意见答复",
                "补正请求处理",
                "专利法第26条答复",
                "不清楚答复",
                "不支持答复",
                "公开不充分答复",
            ],
            "PATENT_DRAFTING": [
                "撰写发明专利申请",
                "写专利申请文件",
                "专利权利要求书撰写",
                "专利说明书撰写",
                "技术交底书撰写",
                "专利申请文档准备",
                "发明点描述撰写",
                "技术特征撰写",
                "保护范围界定",
                "专利申请格式",
            ],
            "INFRINGEMENT_ANALYSIS": [
                "分析产品是否侵权",
                "专利侵权风险评估",
                "技术方案侵权分析",
                "产品侵权比对",
                "专利侵权预警",
                "FTO分析",
                "防侵权检索",
                "专利侵权风险排查",
                "技术方案自由实施",
                "知识产权侵权分析",
            ],
            # 代码生成类(扩展)
            "CODE_GENERATION": [
                "帮我写代码",
                "生成Python函数",
                "编写算法实现",
                "创建代码框架",
                "实现功能代码",
                "开发接口程序",
                "编写脚本工具",
                "代码生成器",
                "自动生成代码",
                "程序设计编码",
            ],
            # 问题解决类(扩展)
            "PROBLEM_SOLVING": [
                "系统启动不了了",
                "程序有错误",
                "系统崩溃修复",
                "代码调试问题",
                "bug修复方法",
                "故障诊断排查",
                "错误解决",
                "异常处理",
                "系统故障排除",
                "问题诊断",
            ],
            # 创意写作类(扩展)
            "CREATIVE_WRITING": [
                "帮我写个故事",
                "创作文案内容",
                "编写创意内容",
                "生成文章内容",
                "创作广告文案",
                "写小说脚本",
                "内容创作",
                "文案编写",
                "创意输出",
                "文字创作",
            ],
            # 数据分析类(扩展)
            "DATA_ANALYSIS": [
                "分析数据报告",
                "统计分析结果",
                "数据可视化",
                "生成数据图表",
                "研究报告分析",
                "数据挖掘",
                "趋势分析",
                "统计报告",
                "数据洞察",
                "分析数据",
            ],
            # 系统监控类
            "SYSTEM_MONITORING": [
                "监控服务状态",
                "检查系统健康",
                "性能监控",
                "日志分析",
                "资源使用情况",
                "系统运行状态",
                "健康检查",
                "服务可用性",
                "系统诊断",
                "运行监控",
            ],
        }

    def recognize_intent(self, text: str, context: Optional[dict[str, Any]] = None) -> IntentResult:
        """
        识别意图(同步版本)

        注意:语义增强功能需要异步,因此同步版本只使用基础引擎

        Args:
            text: 输入文本
            context: 上下文信息

        Returns:
            意图识别结果
        """
        return super().recognize_intent(text, context)

    async def recognize_intent_async(
        self,
        text: str,
        context: Optional[dict[str, Any]] = None,
        user_id: Optional[str] = None,
        enable_semantic: bool = True,
        force_semantic: bool = False,
    ) -> IntentResult:
        """
        异步识别意图(语义增强版本)

        Args:
            text: 输入文本
            context: 上下文信息
            user_id: 用户ID
            enable_semantic: 是否启用语义增强
            force_semantic: 是否强制使用语义增强

        Returns:
            意图识别结果
        """
        self.semantic_stats["total_intents"] += 1

        try:
            # 第一步:基础意图识别(关键词+模式)
            base_result = await super().recognize_intent_async(text, context, user_id)

            # 如果禁用语义增强,直接返回基础结果
            if not enable_semantic:
                return base_result

            # 第二步:语义增强
            # 当基础置信度 < 0.95 或 强制语义增强时启用
            should_apply_semantic = force_semantic or base_result.confidence < 0.95

            if should_apply_semantic:
                semantic_result = await self._apply_semantic_enhancement(text, base_result, context)
                if semantic_result:
                    # 返回语义增强结果
                    return semantic_result

            return base_result

        except Exception as e:
            self.logger.error(f"❌ 意图识别失败: {e}")
            # 返回默认结果
            from core.intent.base_engine import create_default_result

            return create_default_result(
                text=text, processing_time_ms=0, model_version=self.engine_version
            )

    async def _apply_semantic_enhancement(
        self, text: str, base_result: IntentResult, context: dict[str, Any]
    ) -> IntentResult | None:
        """应用语义增强"""

        # 1. 使用语义相似度匹配
        if self.semantic_similarity:
            similarity_result = await self._semantic_similarity_match(text, base_result)
            if similarity_result:
                # 如果意图类型不同或置信度更高,使用语义结果
                semantic_intent = similarity_result["result"].intent
                if (
                    semantic_intent != base_result.intent
                    or similarity_result["confidence"] > base_result.confidence
                ):
                    self.semantic_stats["semantic_boosts"] += 1
                    return similarity_result["result"]

        # 2. 使用嵌入服务进行语义匹配
        if self.embedding_service:
            embedding_result = await self._embedding_similarity_match(text, base_result)
            if embedding_result:
                # 如果意图类型不同或置信度更高,使用嵌入结果
                embedding_intent = embedding_result["result"].intent
                if (
                    embedding_intent != base_result.intent
                    or embedding_result["confidence"] > base_result.confidence
                ):
                    self.semantic_stats["semantic_boosts"] += 1
                    return embedding_result["result"]

        # 3. 使用语义路由器
        if self.semantic_router:
            router_result = await self._semantic_route_match(text, base_result)
            if router_result:
                # 如果意图类型不同或置信度更高,使用路由结果
                router_intent = router_result["result"].intent
                if (
                    router_intent != base_result.intent
                    or router_result["confidence"] > base_result.confidence
                ):
                    self.semantic_stats["semantic_boosts"] += 1
                    return router_result["result"]

        # 没有更好的结果,返回None
        return None

    async def _semantic_similarity_match(
        self, text: str, base_result: IntentResult
    ) -> dict | None:
        """使用语义相似度模块匹配"""
        try:
            best_match = None
            best_score = 0.0

            # 遍历意图示例库
            for intent_str, examples in self.intent_examples.items():
                # 计算与该意图示例的最大相似度
                max_sim_for_intent = 0.0

                for example in examples:
                    similarity = self.semantic_similarity.calculate_similarity(text, example)
                    max_sim_for_intent = max(max_sim_for_intent, similarity)

                if max_sim_for_intent > best_score:
                    best_score = max_sim_for_intent
                    best_match = intent_str

            # 转换为IntentType
            intent_enum = self._string_to_intent_type(best_match)
            if not intent_enum:
                return None

            # 如果找到更好的匹配
            if best_score > 0.15:  # 降低阈值
                self.semantic_stats["semantic_hits"] += 1
                # 置信度计算:基础置信度 + 语义提升
                confidence = min(0.98, base_result.confidence + best_score * 0.2)

                return {
                    "result": IntentResult(
                        intent=intent_enum,
                        confidence=confidence,
                        category=infer_category_from_intent(intent_enum),
                        raw_text=base_result.raw_text,
                        processing_time_ms=base_result.processing_time_ms,
                        model_version=self.engine_version,
                        entities=base_result.entities,
                        key_concepts=base_result.key_concepts,
                        complexity=base_result.complexity,
                        semantic_similarity=best_score,
                        estimated_time=base_result.estimated_time,
                        processing_strategy=base_result.processing_strategy,
                        metadata={
                            **base_result.metadata,
                            "enhancement_method": "semantic_similarity",
                        },
                    ),
                    "confidence": confidence,
                    "method": "semantic_similarity",
                    "score": best_score,
                }

            self.semantic_stats["semantic_misses"] += 1
            return None

        except Exception as e:
            self.logger.error(f"❌ 语义相似度匹配失败: {e}")
            return None

    async def _embedding_similarity_match(
        self, text: str, base_result: IntentResult
    ) -> dict | None:
        """使用嵌入服务进行语义匹配"""
        try:
            # 生成查询嵌入
            result = await self.embedding_service.encode(text, ModuleType.COMMUNICATION)

            if not result or "embeddings" not in result:
                return None

            query_embedding = result["embeddings"]

            # 计算与意图示例的相似度
            best_match = None
            best_score = 0.0

            for intent_type, examples in self.intent_examples.items():
                # 批量编码示例(取前5个以提高效率)
                sample_examples = examples[:5]

                # 检查缓存
                cached_embeddings = self._get_cached_embeddings(intent_type)
                if cached_embeddings is None:
                    # 编码示例
                    encode_result = await self.embedding_service.encode(
                        sample_examples, ModuleType.COMMUNICATION
                    )
                    if encode_result and "embeddings" in encode_result:
                        cached_embeddings = encode_result["embeddings"]
                        self._cache_embeddings(intent_type, cached_embeddings)

                if cached_embeddings is None:
                    continue

                # 计算余弦相似度
                similarities = self._cosine_similarity_batch(query_embedding, cached_embeddings)
                avg_similarity = sum(similarities) / len(similarities)

                if avg_similarity > best_score:
                    best_score = avg_similarity
                    best_match = intent_type

            # 如果找到更好的匹配
            if best_match and best_score > 0.6:  # 嵌入相似度阈值更高
                intent_enum = self._string_to_intent_type(best_match)
                if intent_enum:
                    self.semantic_stats["semantic_hits"] += 1
                    confidence = min(0.98, base_result.confidence + (best_score - 0.6) * 0.5)

                    return {
                        "result": IntentResult(
                            intent=intent_enum,
                            confidence=confidence,
                            category=infer_category_from_intent(intent_enum),
                            raw_text=base_result.raw_text,
                            processing_time_ms=base_result.processing_time_ms,
                            model_version=self.engine_version,
                            entities=base_result.entities,
                            key_concepts=base_result.key_concepts,
                            complexity=base_result.complexity,
                            semantic_similarity=best_score,
                            estimated_time=base_result.estimated_time,
                            processing_strategy=base_result.processing_strategy,
                            metadata={
                                **base_result.metadata,
                                "enhancement_method": "embedding_similarity",
                            },
                        ),
                        "confidence": confidence,
                        "method": "embedding_similarity",
                        "score": best_score,
                    }

            self.semantic_stats["semantic_misses"] += 1
            return None

        except Exception as e:
            self.logger.error(f"❌ 嵌入相似度匹配失败: {e}")
            return None

    async def _semantic_route_match(self, text: str, base_result: IntentResult) -> dict | None:
        """使用语义路由器匹配"""
        try:
            # 获取路由分类
            route_result = await self.semantic_router.classify_query(text)

            # 基于路由结果推断意图
            domain = route_result.get("primary_domain", "")

            # 域名到意图的映射
            domain_to_intent = {
                "patent_domain": IntentType.PATENT_SEARCH,
                "legal_domain": IntentType.OPINION_RESPONSE,
                "mixed_domain": IntentType.INFRINGEMENT_ANALYSIS,
            }

            intent_enum = domain_to_intent.get(domain)
            if intent_enum and intent_enum != base_result.intent:
                # 计算置信度
                confidence = min(0.95, base_result.confidence + 0.1)

                return {
                    "result": IntentResult(
                        intent=intent_enum,
                        confidence=confidence,
                        category=infer_category_from_intent(intent_enum),
                        raw_text=base_result.raw_text,
                        processing_time_ms=base_result.processing_time_ms,
                        model_version=self.engine_version,
                        entities=base_result.entities,
                        key_concepts=base_result.key_concepts,
                        complexity=base_result.complexity,
                        semantic_similarity=0.7,
                        estimated_time=base_result.estimated_time,
                        processing_strategy=base_result.processing_strategy,
                        metadata={**base_result.metadata, "enhancement_method": "semantic_router"},
                    ),
                    "confidence": confidence,
                    "method": "semantic_router",
                    "score": 0.7,
                }

            return None

        except Exception as e:
            self.logger.error(f"❌ 语义路由匹配失败: {e}")
            return None

    def _string_to_intent_type(self, intent_str: str) -> IntentType | None:
        """将字符串转换为IntentType枚举"""
        try:
            return IntentType(intent_str)
        except ValueError:
            return None

    def _cosine_similarity_batch(
        self, vector: list[float], vectors: list[list[float]]
    ) -> list[float]:
        """批量计算余弦相似度"""

        vec = np.array(vector)
        vecs = np.array(vectors)

        # 计算余弦相似度
        dot_products = np.dot(vecs, vec)
        norms = np.linalg.norm(vecs, axis=1) * np.linalg.norm(vec)
        similarities = dot_products / norms

        return similarities.tolist()

    def _get_cached_embeddings(self, intent_type: str) -> Optional[list[list[float]]]:
        """获取缓存的嵌入向量"""
        cache_entry = self.embedding_cache.get(intent_type)
        if cache_entry:
            timestamp = cache_entry["timestamp"]
            if datetime.now().timestamp() - timestamp < self.cache_ttl:
                return cache_entry["embeddings"]
        return None

    def _cache_embeddings(self, intent_type: str, embeddings: list[list[float]]) -> Any:
        """缓存嵌入向量"""
        self.embedding_cache[intent_type] = {
            "embeddings": embeddings,
            "timestamp": datetime.now().timestamp(),
        }

    def get_semantic_performance_report(self) -> dict[str, Any]:
        """获取语义增强性能报告"""
        total = self.semantic_stats["total_intents"]
        boost_rate = self.semantic_stats["semantic_boosts"] / max(total, 1)
        hit_rate = self.semantic_stats["semantic_hits"] / max(
            self.semantic_stats["semantic_hits"] + self.semantic_stats["semantic_misses"], 1
        )

        return {
            "total_intents": total,
            "semantic_boosts": self.semantic_stats["semantic_boosts"],
            "semantic_boost_rate": f"{boost_rate:.1%}",
            "semantic_hit_rate": f"{hit_rate:.1%}",
            "semantic_misses": self.semantic_stats["semantic_misses"],
            "avg_semantic_score": self.semantic_stats["avg_semantic_score"],
            "nlp_modules": {
                "semantic_similarity": self.semantic_similarity is not None,
                "embedding_service": self.embedding_service is not None,
                "semantic_router": self.semantic_router is not None,
            },
            "cache_size": len(self.embedding_cache),
            "base_stats": self.get_stats().model_dump() if hasattr(self, "get_stats") else {},
        }

    def cleanup(self) -> None:
        """清理资源"""
        super().cleanup()
        # 清理语义增强模块
        self.embedding_cache.clear()


# ========================================================================
# 工厂函数
# ========================================================================


def create_semantic_intent_engine(
    config: Optional[dict[str, Any]] = None,
) -> SemanticEnhancedIntentEngine:
    """
    创建语义增强意图识别引擎

    Args:
        config: 配置字典

    Returns:
        引擎实例
    """
    return SemanticEnhancedIntentEngine(config)


# 注册到工厂
from core.intent.base_engine import IntentEngineFactory

IntentEngineFactory.register("semantic", SemanticEnhancedIntentEngine)


# ========================================================================
# 全局实例和便捷函数
# ========================================================================

_semantic_engine = None


async def get_semantic_intent_engine() -> SemanticEnhancedIntentEngine:
    """获取语义增强意图识别引擎实例(已初始化)"""
    global _semantic_engine
    if _semantic_engine is None:
        _semantic_engine = SemanticEnhancedIntentEngine()
        await _semantic_engine.initialize_async()
    return _semantic_engine


# 便捷函数
async def recognize_intent_semantic(
    text: str, context: dict[str, Any]  | None = None, user_id: Optional[str] = None
) -> IntentResult:
    """便捷函数:语义增强意图识别"""
    engine = await get_semantic_intent_engine()
    return await engine.recognize_intent_async(text, context, user_id, enable_semantic=True)


if __name__ == "__main__":
    # 测试
    async def test():
        engine = await get_semantic_intent_engine()

        test_cases = [
            "帮我写个故事",  # 之前被错误识别为code_generation
            "介绍一下机器学习",  # 需要识别为explanation而非information
            "分析这个产品是否侵权",  # 侵权分析
            "审查意见怎么答复",  # 专利审查意见答复
        ]

        print("🧪 语义增强意图识别测试")
        for test in test_cases:
            result = await engine.recognize_intent_async(test)
            print(f"\n输入: {test}")
            print(f"意图: {result.intent.value}")
            print(f"置信度: {result.confidence:.3f}")
            print(f"语义相似度: {result.semantic_similarity:.3f}")

        # 性能报告
        report = engine.get_semantic_performance_report()
        print("\n📊 性能报告:")
        print(json.dumps(report, indent=2, ensure_ascii=False))

    asyncio.run(test())
