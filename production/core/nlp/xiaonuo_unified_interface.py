#!/usr/bin/env python3
"""
小诺统一NLP接口
整合Phase 1-3的所有模块,提供统一的调用接口和数据流优化

功能模块:
1. 意图识别 - XiaonuoEnhancedIntentClassifier
2. 语义相似度 - XiaonuoSemanticSimilarity
3. 上下文理解 - XiaonuoContextAwareSystem
4. 工具选择 - XiaonuoIntelligentToolSelector
5. 用户偏好学习 - XiaonuoUserPreferenceLearner
6. 工具适用性评分 - XiaonuoToolSuitabilityScorer
7. 反馈循环 - XiaonuoFeedbackLoop
8. NER参数提取 - XiaonuoNERParameterExtractor
9. 参数澄清 - XiaonuoParameterClarification

统一接口:
- 标准化输入/输出格式
- 模块间数据流优化
- 性能监控和缓存
- 错误处理和重试
- 批处理支持

作者: 小诺AI团队
日期: 2025-12-18
"""

from __future__ import annotations
import hashlib
import json
import os
from typing import Any

import numpy as np

from core.logging_config import setup_logging

# 使用安全的序列化方法替代pickle
try:
    from core.serialization.secure_serializer import deserialize_from_cache, serialize_for_cache
except ImportError:
    import json

    def serialize_for_cache(obj: Any) -> bytes:
        return json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8")

    def deserialize_from_cache(data: bytes) -> Any:
        return json.loads(data.decode("utf-8"))


# 导入所有模块
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from xiaonuo_call_chain_monitor import (
    CallChainMonitor,
    SpanConfig,
)
from xiaonuo_context_aware import XiaonuoContextAwareSystem
from xiaonuo_data_flow_optimizer import create_xiaonuo_data_flow
from xiaonuo_enhanced_intent_classifier import XiaonuoEnhancedIntentClassifier
from xiaonuo_feedback_loop import XiaonuoFeedbackLoop
from xiaonuo_intelligent_tool_selector import IntentCategory, XiaonuoIntelligentToolSelector
from xiaonuo_ner_parameter_extractor import NERModelConfig, XiaonuoNERParameterExtractor
from xiaonuo_parameter_clarification import XiaonuoParameterClarification
from xiaonuo_semantic_similarity import XiaonuoSemanticSimilarity
from xiaonuo_user_preference_learner import XiaonuoUserPreferenceLearner

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


class ProcessingMode(Enum):
    """处理模式"""

    SINGLE = "single"  # 单次处理
    BATCH = "batch"  # 批量处理
    STREAM = "stream"  # 流式处理
    CONVERSATION = "conversation"  # 对话模式


class CacheLevel(Enum):
    """缓存级别"""

    NONE = 0  # 无缓存
    MEMORY = 1  # 内存缓存
    DISK = 2  # 磁盘缓存
    DISTRIBUTED = 3  # 分布式缓存


@dataclass
class NLPRequest:
    """NLP处理请求"""

    text: str  # 输入文本
    user_id: str | None = None  # 用户ID
    session_id: str | None = None  # 会话ID
    context: dict[str, Any] | None = None  # 上下文
    mode: ProcessingMode = ProcessingMode.SINGLE  # 处理模式
    enable_caching: bool = True  # 启用缓存
    priority: int = 5  # 优先级 (1-10)
    timeout: float = 30.0  # 超时时间
    metadata: dict[str, Any] = field(default_factory=dict)  # 元数据


@dataclass
class NLPResponse:
    """NLP处理响应"""

    request_id: str  # 请求ID
    intent: str  # 识别的意图
    confidence: float  # 整体置信度
    selected_tools: list[str]  # 选择的工具
    extracted_parameters: dict[str, Any]  # 提取的参数
    entities: list[dict[str, Any]]  # 识别的实体
    similar_examples: list[tuple[str, float]]  # 相似示例
    context_update: dict[str, Any]  # 上下文更新
    processing_time: float  # 处理时间
    module_performance: dict[str, float]  # 各模块性能
    errors: list[str]  # 错误信息
    warnings: list[str]  # 警告信息
    metadata: dict[str, Any] = field(default_factory=dict)  # 响应元数据


@dataclass
class UnifiedConfig:
    """统一接口配置"""

    # 缓存配置
    cache_level: CacheLevel = CacheLevel.MEMORY
    cache_size: int = 1000
    cache_ttl: int = 3600  # 秒
    cache_dir: str = "cache/nlp"

    # 性能配置
    max_workers: int = 4
    timeout: float = 30.0
    retry_count: int = 3
    retry_delay: float = 1.0

    # 模块配置
    enable_intent: bool = True
    enable_semantic: bool = True
    enable_context: bool = True
    enable_tool_selection: bool = True
    enable_user_learning: bool = True
    enable_ner: bool = True
    enable_clarification: bool = True

    # 阈值配置
    intent_threshold: float = 0.8
    similarity_threshold: float = 0.7
    tool_selection_threshold: float = 0.6

    # 性能监控配置
    enable_performance_monitoring: bool = True


class XiaonuoUnifiedInterface:
    """小诺统一NLP接口"""

    def __init__(self, config: UnifiedConfig | None = None):
        self.config = config if config is not None else UnifiedConfig()
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_workers)

        # 🔧 线程安全修复:添加缓存锁
        import threading

        self.cache_lock = threading.Lock()

        # 初始化数据流优化器
        self.data_flow_optimizer = create_xiaonuo_data_flow()

        # 初始化调用链路监控器
        span_config = SpanConfig(
            service_name="xiaonuo-unified-nlp",
            service_version="1.0.0",
            environment="development",
            slow_threshold_ms=500.0,
            error_threshold_percent=3.0,
            sample_rate=1.0,
            enable_realtime_alerts=True,
        )
        self.call_chain_monitor = CallChainMonitor(span_config)

        # 初始化性能瓶颈分析器
        from xiaonuo_performance_monitoring_integration import PerformanceMonitoringIntegration

        self.performance_monitoring = PerformanceMonitoringIntegration(
            enable_monitoring=self.config.enable_performance_monitoring
        )

        # 缓存系统
        self.cache: dict[str, Any] = {}
        self.cache_stats: dict[str, int] = {"hits": 0, "misses": 0}

        # 性能统计
        self.performance_stats: dict[str, Any] = {
            "total_requests": 0,
            "total_time": 0.0,
            "module_times": {},
            "error_count": 0,
        }

        # 创建数据处理管道
        self._setup_data_pipelines()

        # 初始化所有模块
        self._initialize_modules()

        logger.info("🚀 小诺统一NLP接口初始化完成")
        logger.info(
            f"⚙️ 配置: 缓存级别={self.config.cache_level.name}, "
            f"最大工作线程={self.config.max_workers}, "
            f"超时={self.config.timeout}s"
        )

    def _setup_data_pipelines(self) -> Any:
        """设置数据处理管道"""
        from xiaonuo_data_flow_optimizer import CommonProcessors

        # 意图识别处理管道
        self.data_flow_optimizer.create_pipeline(
            "intent_processing",
            [
                CommonProcessors.data_validator,
                self._preprocess_intent_request,
            ],
        )

        # 语义相似度处理管道
        self.data_flow_optimizer.create_pipeline(
            "semantic_processing",
            [
                CommonProcessors.data_validator,
                self._preprocess_semantic_request,
            ],
        )

        # 工具选择处理管道
        self.data_flow_optimizer.create_pipeline(
            "tool_selection",
            [
                self._validate_tool_request,
                self._optimize_tool_data,
            ],
        )

        # NER参数提取管道
        self.data_flow_optimizer.create_pipeline(
            "ner_extraction",
            [
                CommonProcessors.data_validator,
                self._preprocess_ner_request,
            ],
        )

        # 响应序列化管道
        self.data_flow_optimizer.create_pipeline(
            "response_serialization",
            [
                self._format_response_data,
                CommonProcessors.json_serializer,
            ],
        )

        logger.info("📋 数据处理管道设置完成")

    def _preprocess_intent_request(self, data: dict[str, Any]) -> dict[str, Any]:
        """预处理意图识别请求"""
        if "text" in data and isinstance(data["text"], str):
            # 文本清理和预处理
            data["text"] = data["text"].strip()
            data["length"] = len(data["text"])
        return data

    def _preprocess_semantic_request(self, data: str) -> str:
        """预处理语义相似度请求"""
        if isinstance(data, str):
            return data.strip()
        return str(data)

    def _validate_tool_request(self, data: dict[str, Any]) -> dict[str, Any]:
        """验证工具选择请求"""
        if "text" not in data or "intent" not in data:
            raise ValueError("工具选择请求必须包含text和intent字段")
        return data

    def _optimize_tool_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """优化工具选择数据传输"""
        # 只传输必要的字段
        essential_fields = ["text", "intent", "user_id"]
        return self.data_flow_optimizer.optimize_data_transfer(data, essential_fields)

    def _preprocess_ner_request(self, data: str) -> str:
        """预处理NER请求"""
        if isinstance(data, str):
            # 基础文本清理
            return data.strip()
        return str(data)

    def _format_response_data(self, response: NLPResponse) -> dict[str, Any]:
        """格式化响应数据"""
        return {
            "request_id": response.request_id,
            "intent": response.intent,
            "confidence": response.confidence,
            "selected_tools": response.selected_tools,
            "extracted_parameters": response.extracted_parameters,
            "entities": response.entities,
            "processing_time": response.processing_time,
            "errors": response.errors,
            "warnings": response.warnings,
        }

    def _initialize_modules(self) -> Any:
        """初始化所有模块"""
        try:
            self.modules = {}

            if self.config.enable_intent:
                logger.info("🧠 初始化意图识别模块...")
                intent_classifier = XiaonuoEnhancedIntentClassifier()
                # 自动训练模型
                try:
                    logger.info("🎯 开始训练意图识别模型...")
                    intent_classifier.create_expanded_training_data()  # 创建数据
                    intent_classifier.train_model()  # 训练模型
                    logger.info("✅ 意图识别模型训练完成")
                except Exception as e:
                    logger.warning(f"⚠️ 意图识别模型训练失败: {e}")
                self.modules["intent"] = intent_classifier

            if self.config.enable_semantic:
                logger.info("🔍 初始化语义相似度模块...")
                self.modules["semantic"] = XiaonuoSemanticSimilarity()

            if self.config.enable_context:
                logger.info("💭 初始化上下文理解模块...")
                self.modules["context"] = XiaonuoContextAwareSystem()

            if self.config.enable_tool_selection:
                logger.info("🔧 初始化工具选择模块...")
                tool_selector = XiaonuoIntelligentToolSelector()
                # 训练工具选择模型
                tool_selector.train_tool_selection_model()
                self.modules["tool_selector"] = tool_selector

            if self.config.enable_user_learning:
                logger.info("👤 初始化用户偏好学习模块...")
                self.modules["user_learner"] = XiaonuoUserPreferenceLearner()

            if self.config.enable_ner:
                logger.info("🏷️ 初始化NER参数提取模块...")
                ner_config = NERModelConfig(model_dir="models/ner")
                self.modules["ner_extractor"] = XiaonuoNERParameterExtractor(ner_config)

            if self.config.enable_clarification:
                logger.info("💬 初始化参数澄清模块...")
                self.modules["clarification"] = XiaonuoParameterClarification()

            # 初始化反馈循环(总是启用)
            logger.info("🔄 初始化反馈循环模块...")
            self.modules["feedback"] = XiaonuoFeedbackLoop()

            logger.info(f"✅ 成功初始化 {len(self.modules)} 个模块")

        except Exception as e:
            logger.error(f"❌ 模块初始化失败: {e}")
            raise

    def _get_cache_key(self, request: NLPRequest) -> str:
        """生成缓存键 - 🔧 性能优化:使用xxhash替代md5"""
        content = f"{request.text}_{request.user_id}_{request.context}"
        # 性能优化:优先使用xxhash(比md5快3-5倍)
        try:
            import xxhash

            return xxhash.xxh64(content.encode("utf-8")).hexdigest()
        except ImportError:
            # 回退到hashlib.sha256(比md5更安全)
            return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _get_from_cache(self, cache_key: str) -> NLPResponse | None:
        """从缓存获取结果 - 🔧 线程安全修复:添加线程锁"""
        if self.config.cache_level == CacheLevel.NONE:
            return None

        # 线程安全修复:使用锁保护缓存访问
        with self.cache_lock if hasattr(self, "cache_lock") else self._get_default_lock():
            if cache_key in self.cache:
                cached_time, response = self.cache[cache_key]
                if time.time() - cached_time < self.config.cache_ttl:
                    self.cache_stats["hits"] += 1
                    return response
                else:
                    # 删除过期缓存
                    del self.cache[cache_key]

        self.cache_stats["misses"] += 1
        return None

    def _save_to_cache(self, cache_key: str, response: NLPResponse) -> Any:
        """保存结果到缓存 - 🔧 线程安全修复:添加线程锁和改进缓存清理"""
        if self.config.cache_level != CacheLevel.NONE:
            # 线程安全修复:使用锁保护缓存访问
            with self.cache_lock if hasattr(self, "cache_lock") else self._get_default_lock():
                # 清理旧缓存(添加安全检查)
                if len(self.cache) >= self.config.cache_size:
                    # 找到最旧的条目
                    oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][0])
                    del self.cache[oldest_key]

                self.cache[cache_key] = (time.time(), response)

    def _get_default_lock(self) -> Any:
        """获取默认锁(向后兼容)"""
        if not hasattr(self, "_default_cache_lock"):
            import threading

            self._default_cache_lock = threading.Lock()
        return self._default_cache_lock

    def process_single(self, request: NLPRequest) -> NLPResponse:
        """处理单个请求 - 🔧 性能优化:使用xxhash生成请求ID"""
        start_time = time.time()
        # 性能优化:使用xxhash生成请求ID
        try:
            import xxhash

            request_id = xxhash.xxh64(f"{request.text}_{time.time()}".encode()).hexdigest()
        except ImportError:
            request_id = hashlib.sha256(f"{request.text}_{time.time()}".encode()).hexdigest()

        # 检查缓存
        if request.enable_caching:
            cache_key = self._get_cache_key(request)
            cached_response = self._get_from_cache(cache_key)
            if cached_response:
                cached_response.metadata["from_cache"] = True
                return cached_response

        try:
            # 开始调用链路追踪
            main_span = self.call_chain_monitor.start_trace(
                "process_single",
                tags={
                    "request_id": request_id,
                    "user_id": request.user_id or "anonymous",
                    "text_length": str(len(request.text)),
                },
            )

            # 初始化响应
            response = NLPResponse(
                request_id=request_id,
                intent="",
                confidence=0.0,
                selected_tools=[],
                extracted_parameters={},
                entities=[],
                similar_examples=[],
                context_update={},
                processing_time=0.0,
                module_performance={},
                errors=[],
                warnings=[],
            )

            module_performance = {}

            # 1. 意图识别(使用数据流优化器)
            if "intent" in self.modules:
                # 开始意图识别追踪
                intent_span = self.call_chain_monitor.start_trace(
                    "intent_classification",
                    parent_span_id=main_span.span_id,
                    tags={
                        "module": "intent_classifier",
                        "text_length": str(len(request.text)),
                        "user_id": request.user_id or "anonymous",
                    },
                )

                module_start = time.time()

                try:
                    # 使用数据流管道预处理
                    intent_request_data = {
                        "text": request.text,
                        "user_id": request.user_id,
                        "timestamp": datetime.now().isoformat(),
                    }

                    processed_data = self.data_flow_optimizer.process_pipeline_sync(
                        "intent_processing", intent_request_data
                    )

                    # 执行意图识别
                    intent_result = self.modules["intent"].predict_intent(processed_data["text"])

                    module_time = time.time() - module_start
                    module_performance["intent_classification"] = module_time

                    response.intent = intent_result[0]  # (intent, confidence)
                    response.confidence = intent_result[1]

                    # 完成意图识别追踪
                    self.call_chain_monitor.finish_span(
                        intent_span,
                        status="success",
                        result={
                            "intent": response.intent,
                            "confidence": response.confidence,
                            "processing_time": module_time,
                        },
                    )

                    if response.confidence < self.config.intent_threshold:
                        response.warnings.append(f"意图置信度较低: {response.confidence:.3f}")

                except Exception as e:
                    # 意图识别失败
                    self.call_chain_monitor.finish_span(
                        intent_span, status="error", error_message=str(e)
                    )
                    raise

            # 2. 语义相似度(使用数据流优化器)
            if "semantic" in self.modules:
                # 开始语义相似度追踪
                semantic_span = self.call_chain_monitor.start_trace(
                    "semantic_similarity",
                    parent_span_id=main_span.span_id,
                    tags={
                        "module": "semantic_similarity",
                        "top_k": "5",
                        "text_length": str(len(request.text)),
                    },
                )

                module_start = time.time()

                try:
                    # 使用数据流管道预处理
                    processed_text = self.data_flow_optimizer.process_pipeline_sync(
                        "semantic_processing", request.text
                    )

                    similar_examples = self.modules["semantic"].find_similar_intents(
                        processed_text, top_k=5
                    )
                    module_time = time.time() - module_start
                    module_performance["semantic_similarity"] = module_time

                    response.similar_examples = similar_examples

                    # 完成语义相似度追踪
                    self.call_chain_monitor.finish_span(
                        semantic_span,
                        status="success",
                        result={
                            "similar_count": len(similar_examples),
                            "processing_time": module_time,
                        },
                    )

                except Exception as e:
                    # 语义相似度分析失败
                    self.call_chain_monitor.finish_span(
                        semantic_span, status="error", error_message=str(e)
                    )
                    raise

            # 3. 上下文理解
            context_aware = None
            if "context" in self.modules:
                # 开始上下文理解追踪
                context_span = self.call_chain_monitor.start_trace(
                    "context_awareness",
                    parent_span_id=main_span.span_id,
                    tags={
                        "module": "context_understanding",
                        "intent": response.intent,
                        "confidence": str(response.confidence),
                    },
                )

                module_start = time.time()

                try:
                    context_aware = self.modules["context"]

                    # 使用意图识别结果来更新上下文
                    enhanced_intent, enhanced_confidence = context_aware.enhance_intent_prediction(
                        response.intent, response.confidence, request.text
                    )

                    # 添加对话轮次到上下文
                    context_aware.add_conversation_turn(
                        user_input=request.text,
                        intent=response.intent,
                        entities=[e[0] for e in response.entities] if response.entities else [],
                        response=f"识别意图: {response.intent}",
                        confidence=response.confidence,
                    )

                    # 获取上下文特征
                    context_features = context_aware.get_context_features(request.text)

                    module_time = time.time() - module_start
                    module_performance["context_awareness"] = module_time

                    response.context_update = {
                        "enhanced_intent": enhanced_intent,
                        "enhanced_confidence": enhanced_confidence,
                        "context_features": context_features,
                        "context_utterances": len(context_aware.conversation_history),
                    }

                    # 完成上下文理解追踪
                    self.call_chain_monitor.finish_span(
                        context_span,
                        status="success",
                        result={
                            "enhanced_intent": enhanced_intent,
                            "enhanced_confidence": enhanced_confidence,
                            "context_utterances": len(context_aware.conversation_history),
                            "processing_time": module_time,
                        },
                    )

                except Exception as e:
                    # 上下文理解失败
                    self.call_chain_monitor.finish_span(
                        context_span, status="error", error_message=str(e)
                    )
                    raise

            # 4. 用户偏好学习
            if "user_learner" in self.modules and request.user_id:
                module_start = time.time()
                user_learner = self.modules["user_learner"]
                user_persona = user_learner.infer_user_persona(request.user_id)
                user_behavior = user_learner.analyze_user_behavior(request.user_id)
                module_time = time.time() - module_start
                module_performance["user_learning"] = module_time

                if user_persona:
                    response.metadata["user_persona"] = user_persona.value
                if user_behavior:
                    response.metadata["user_behavior"] = user_behavior

            # 5. NER参数提取(使用数据流优化器)
            if "ner_extractor" in self.modules:
                # 开始NER参数提取追踪
                ner_span = self.call_chain_monitor.start_trace(
                    "ner_parameter_extraction",
                    parent_span_id=main_span.span_id,
                    tags={
                        "module": "ner_extractor",
                        "intent": response.intent,
                        "text_length": str(len(request.text)),
                    },
                )

                module_start = time.time()

                try:
                    enhanced_text = response.context_update.get("enhanced_text", request.text)

                    # 使用数据流管道预处理
                    processed_text = self.data_flow_optimizer.process_pipeline_sync(
                        "ner_extraction", enhanced_text
                    )

                    extraction = self.modules["ner_extractor"].extract_parameters(
                        processed_text, response.intent
                    )
                    module_time = time.time() - module_start
                    module_performance["ner_extraction"] = module_time

                    response.extracted_parameters = extraction.parameters
                    response.entities = [
                        {
                            "text": entity.text,
                            "type": entity.entity_type.value,
                            "confidence": entity.confidence,
                            "start": entity.start_pos,
                            "end": entity.end_pos,
                        }
                        for entity in extraction.entities
                    ]

                    # 完成NER参数提取追踪
                    self.call_chain_monitor.finish_span(
                        ner_span,
                        status="success",
                        result={
                            "parameters_count": len(response.extracted_parameters),
                            "entities_count": len(response.entities),
                            "missing_params": len(extraction.missing_params),
                            "processing_time": module_time,
                        },
                    )

                    if extraction.missing_params:
                        response.warnings.append(
                            f"缺失参数: {', '.join(extraction.missing_params)}"
                        )

                    if extraction.validation_errors:
                        response.errors.extend(extraction.validation_errors)

                except Exception as e:
                    # NER参数提取失败
                    self.call_chain_monitor.finish_span(
                        ner_span, status="error", error_message=str(e)
                    )
                    raise

            # 6. 工具选择(使用数据流优化器)
            if "tool_selector" in self.modules:
                # 开始工具选择追踪
                tool_span = self.call_chain_monitor.start_trace(
                    "intelligent_tool_selection",
                    parent_span_id=main_span.span_id,
                    tags={
                        "module": "tool_selector",
                        "intent": response.intent,
                        "confidence": str(response.confidence),
                        "user_id": request.user_id or "anonymous",
                    },
                )

                module_start = time.time()

                try:
                    tool_selector = self.modules["tool_selector"]

                    # 转换意图字符串为枚举类型
                    try:
                        intent_enum = IntentCategory(response.intent.lower())
                    except ValueError:
                        intent_enum = IntentCategory.QUERY  # 默认值

                    # 使用数据流管道优化数据传输
                    tool_request_data = {
                        "text": request.text,
                        "intent": (
                            intent_enum.value if hasattr(intent_enum, "value") else str(intent_enum)
                        ),
                        "user_id": request.user_id or "",
                        "confidence": response.confidence,
                        "selected_tools": response.selected_tools,
                    }

                    optimized_data = self.data_flow_optimizer.process_pipeline_sync(
                        "tool_selection", tool_request_data
                    )

                    selected_tools = tool_selector.select_tools(
                        optimized_data["text"],
                        IntentCategory(optimized_data["intent"]),
                        user_id=optimized_data["user_id"],
                    )
                    module_time = time.time() - module_start
                    module_performance["tool_selection"] = module_time

                    response.selected_tools = [tool[0] for tool in selected_tools]

                    # 完成工具选择追踪
                    self.call_chain_monitor.finish_span(
                        tool_span,
                        status="success",
                        result={
                            "selected_tools_count": len(response.selected_tools),
                            "dev/tools": response.selected_tools,
                            "processing_time": module_time,
                        },
                    )

                    if not selected_tools and response.intent != "unknown":
                        response.warnings.append("未找到合适的工具")

                except Exception as e:
                    # 工具选择失败
                    self.call_chain_monitor.finish_span(
                        tool_span, status="error", error_message=str(e)
                    )
                    raise

            # 7. 反馈循环记录
            if "feedback" in self.modules:
                try:
                    self.modules["feedback"].record_feedback(
                        user_id=request.user_id or "anonymous",
                        tool_name=response.selected_tools[0] if response.selected_tools else "none",
                        intent=response.intent,
                        context=request.context or {},
                        feedback_type="automatic_detection",
                        feedback_channel="implicit_monitoring",
                        execution_success=len(response.errors) == 0,
                        response_time=time.time() - start_time,
                        satisfaction_score=response.confidence,
                        quality_metrics={"tool_count": len(response.selected_tools)},
                        user_comments="",
                    )
                except Exception as e:
                    logger.warning(f"⚠️ 反馈记录失败: {e}")

            # 更新性能统计
            total_time = time.time() - start_time
            response.processing_time = total_time
            response.module_performance = module_performance

            self.performance_stats["total_requests"] += 1
            self.performance_stats["total_time"] += total_time
            for module, time_spent in module_performance.items():
                if module not in self.performance_stats["module_times"]:
                    self.performance_stats["module_times"][module] = []
                self.performance_stats["module_times"][module].append(time_spent)

            # 保存到缓存
            if request.enable_caching:
                self._save_to_cache(self._get_cache_key(request), response)

            # 完成主追踪span
            self.call_chain_monitor.finish_span(
                main_span,
                status="success",
                result={
                    "intent": response.intent,
                    "confidence": response.confidence,
                    "tools_count": len(response.selected_tools),
                    "entities_count": len(response.entities),
                    "total_processing_time": total_time,
                    "module_performance": module_performance,
                },
            )

            # 记录性能指标到瓶颈分析器
            if self.config.enable_performance_monitoring:
                self.performance_monitoring.record_request_metrics(request, response)

            logger.info(f"✅ 请求处理完成: {request_id}, 耗时: {total_time:.3f}s")

            return response

        except Exception as e:
            self.performance_stats["error_count"] += 1
            total_time = time.time() - start_time
            logger.error(f"❌ 请求处理失败 {request_id}: {e}")

            # 完成主追踪span(错误状态)
            if "main_span" in locals():
                self.call_chain_monitor.finish_span(
                    main_span,
                    status="error",
                    error_message=str(e),
                    result={"error_type": type(e).__name__, "processing_time": total_time},
                )

            error_response = NLPResponse(
                request_id=request_id,
                intent="error",
                confidence=0.0,
                selected_tools=[],
                extracted_parameters={},
                entities=[],
                similar_examples=[],
                context_update={},
                processing_time=total_time,
                module_performance={},
                errors=[str(e)],
                warnings=[],
                metadata={"error_type": type(e).__name__},
            )

            # 记录错误请求的性能指标
            if self.config.enable_performance_monitoring:
                self.performance_monitoring.record_request_metrics(request, error_response)

            return error_response

    def process_batch(self, requests: list[NLPRequest]) -> list[NLPResponse]:
        """批量处理请求 - 🔧 性能优化:使用xxhash生成批次ID"""
        batch_start_time = time.time()
        # 性能优化:使用xxhash生成批次ID
        try:
            import xxhash

            batch_id = xxhash.xxh64(f"batch_{len(requests)}_{time.time()}".encode()).hexdigest()
        except ImportError:
            batch_id = hashlib.sha256(f"batch_{len(requests)}_{time.time()}".encode()).hexdigest()

        # 开始批量处理追踪
        batch_span = self.call_chain_monitor.start_trace(
            "process_batch",
            tags={
                "batch_id": batch_id,
                "batch_size": str(len(requests)),
                "priority_levels": str(len({r.priority for r in requests})),
            },
        )

        logger.info(f"🔄 开始批量处理 {len(requests)} 个请求 (ID: {batch_id})")

        try:
            # 按优先级排序
            sorted_requests = sorted(requests, key=lambda r: r.priority, reverse=True)

            # 创建子span追踪各个请求
            request_spans = []
            futures = []

            for i, request in enumerate(sorted_requests):
                # 为每个请求创建子span
                request_span = self.call_chain_monitor.start_trace(
                    "batch_request",
                    parent_span_id=batch_span.span_id,
                    tags={
                        "request_index": str(i),
                        "priority": str(request.priority),
                        "text_length": str(len(request.text)),
                        "user_id": request.user_id or "anonymous",
                    },
                )
                request_spans.append(request_span)

                future = self.executor.submit(self.process_single, request)
                futures.append((future, request_span))

            responses = []
            successful_requests = 0
            failed_requests = 0

            for future, request_span in futures:
                try:
                    response = future.result(timeout=request.timeout)
                    responses.append(response)

                    if response.intent != "error":
                        successful_requests += 1
                        # 完成成功的请求span
                        self.call_chain_monitor.finish_span(
                            request_span,
                            status="success",
                            result={
                                "intent": response.intent,
                                "confidence": response.confidence,
                                "processing_time": response.processing_time,
                            },
                        )
                    else:
                        failed_requests += 1
                        # 完成失败的请求span
                        self.call_chain_monitor.finish_span(
                            request_span,
                            status="error",
                            error_message="处理失败",
                            result={"processing_time": response.processing_time},
                        )

                except Exception as e:
                    failed_requests += 1
                    logger.error(f"❌ 批量处理中发生错误: {e}")

                    # 完成失败的请求span
                    self.call_chain_monitor.finish_span(
                        request_span, status="error", error_message=str(e)
                    )

                    # 创建错误响应
                    error_response = NLPResponse(
                        request_id="error",
                        intent="error",
                        confidence=0.0,
                        selected_tools=[],
                        extracted_parameters={},
                        entities=[],
                        similar_examples=[],
                        context_update={},
                        processing_time=0.0,
                        module_performance={},
                        errors=[str(e)],
                        warnings=[],
                        metadata={"batch_error": True},
                    )
                    responses.append(error_response)

            # 完成批量处理追踪
            batch_time = time.time() - batch_start_time
            self.call_chain_monitor.finish_span(
                batch_span,
                status="success",
                result={
                    "successful_requests": successful_requests,
                    "failed_requests": failed_requests,
                    "total_requests": len(requests),
                    "batch_processing_time": batch_time,
                    "success_rate": successful_requests / len(requests) if requests else 0,
                },
            )

            logger.info(
                f"✅ 批量处理完成 (ID: {batch_id}),成功: {successful_requests}, 失败: {failed_requests}, 耗时: {batch_time:.3f}s"
            )

        except Exception as e:
            # 完成批量处理追踪(错误状态)
            batch_time = time.time() - batch_start_time
            self.call_chain_monitor.finish_span(
                batch_span,
                status="error",
                error_message=str(e),
                result={"batch_processing_time": batch_time, "error_type": type(e).__name__},
            )
            logger.error(f"❌ 批量处理失败 (ID: {batch_id}): {e}")

        return responses

    def process_conversation(
        self, user_id: str, message: str, session_id: str | None = None
    ) -> NLPResponse:
        """处理对话消息 - 🔧 性能优化:使用xxhash生成会话ID"""
        if not session_id:
            # 性能优化:使用xxhash生成会话ID
            try:
                import xxhash

                session_id = xxhash.xxh64(f"{user_id}_{time.time()}".encode()).hexdigest()
            except ImportError:
                session_id = hashlib.sha256(f"{user_id}_{time.time()}".encode()).hexdigest()

        # 获取上下文
        context = {}
        if "context" in self.modules:
            context_module = self.modules["context"]
            # 获取对话历史
            context = {
                "utterances": [
                    turn.user_input for turn in list(context_module.conversation_history)
                ],
                "entity_memory": context_module.entity_memory,
                "session_id": session_id,
            }

        # 创建请求
        request = NLPRequest(
            text=message,
            user_id=user_id,
            session_id=session_id,
            context=context,
            mode=ProcessingMode.CONVERSATION,
        )

        # 处理请求
        response = self.process_single(request)

        # 如果需要参数澄清
        if response.extracted_parameters.get("_missing_params") and "clarification" in self.modules:

            clarification = self.modules["clarification"]

            # 如果是新的会话,开始澄清
            if not hasattr(self, "_clarification_sessions"):
                self._clarification_sessions = {}

            if session_id not in self._clarification_sessions:
                self._clarification_sessions[session_id] = (
                    clarification.start_clarification_session(user_id, response.intent, message)
                )
            else:
                clar_response, state = clarification.continue_clarification(session_id, message)
                if clar_response:
                    response.metadata["clarification_response"] = clar_response
                    response.metadata["clarification_state"] = state.value

        return response

    def get_performance_stats(self) -> dict[str, Any]:
        """获取性能统计"""
        stats = {
            "cache": {
                "hits": self.cache_stats["hits"],
                "misses": self.cache_stats["misses"],
                "hit_rate": self.cache_stats["hits"]
                / max(1, self.cache_stats["hits"] + self.cache_stats["misses"]),
            },
            "requests": {
                "total": self.performance_stats["total_requests"],
                "errors": self.performance_stats["error_count"],
                "success_rate": 1
                - (
                    self.performance_stats["error_count"]
                    / max(1, self.performance_stats["total_requests"])
                ),
            },
            "timing": {
                "total_time": self.performance_stats["total_time"],
                "avg_time": (
                    self.performance_stats["total_time"]
                    / max(1, self.performance_stats["total_requests"])
                ),
                "module_times": {},
            },
        }

        # 计算各模块平均时间
        for module, times in self.performance_stats["module_times"].items():
            if times:
                stats["timing"]["module_times"][module] = {
                    "avg": np.mean(times),
                    "min": np.min(times),
                    "max": np.max(times),
                    "std": np.std(times),
                    "count": len(times),
                }

        return stats

    def clear_cache(self) -> None:
        """清空缓存"""
        self.cache.clear()
        self.cache_stats = {"hits": 0, "misses": 0}

    def get_enhanced_performance_stats(self) -> dict[str, Any]:
        """获取增强的性能统计(包含数据流优化器数据)"""
        # 执行智能内存清理
        self.data_flow_optimizer.smart_memory_cleanup()

        # 获取基础统计
        stats = self.get_performance_stats()

        # 获取数据流优化器性能报告
        data_flow_report = self.data_flow_optimizer.get_performance_report()

        # 合并数据流优化器数据
        stats["dataflow_cache"] = data_flow_report["cache"]
        stats["dataflow_metrics"] = data_flow_report["metrics"]
        stats["dataflow_pipelines"] = data_flow_report["pipelines"]
        stats["memory_usage_mb"] = data_flow_report["memory_usage_mb"]
        stats["gc_count"] = data_flow_report["gc_count"]

        return stats

    def get_performance_bottleneck_analysis(self) -> dict[str, Any]:
        """获取性能瓶颈分析结果"""
        if not self.config.enable_performance_monitoring:
            return {"performance_monitoring_enabled": False}

        try:
            return self.performance_monitoring.get_performance_report()
        except Exception as e:
            logger.error(f"❌ 获取性能瓶颈分析失败: {e}")
            return {"performance_monitoring_enabled": True, "error": str(e)}

    def run_performance_analysis(self) -> dict[str, Any]:
        """运行完整的性能分析"""
        if not self.config.enable_performance_monitoring:
            return {"performance_monitoring_enabled": False}

        try:
            return self.performance_monitoring.run_performance_analysis()
        except Exception as e:
            logger.error(f"❌ 运行性能分析失败: {e}")
            return {"performance_monitoring_enabled": True, "error": str(e)}

    def get_optimization_recommendations(self) -> list[dict[str, Any]]:
        """获取性能优化建议"""
        if not self.config.enable_performance_monitoring:
            return []

        try:
            return self.performance_monitoring.get_optimization_recommendations()
        except Exception as e:
            logger.error(f"❌ 获取优化建议失败: {e}")
            return []

    def save_comprehensive_performance_data(self, filepath: str | None = None) -> None:
        """保存完整的性能数据"""
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"data/comprehensive_performance_report_{timestamp}.json"

        try:
            # 收集所有性能数据
            data = {
                "timestamp": datetime.now().isoformat(),
                "unified_interface_stats": self.get_enhanced_performance_stats(),
                "call_chain_dashboard": self.get_call_chain_dashboard(),
                "bottleneck_analysis": self.get_performance_bottleneck_analysis(),
                "data_flow_report": self.data_flow_optimizer.get_performance_report(),
            }

            # 保存到文件
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)

            logger.info(f"💾 综合性能数据已保存: {filepath}")

        except Exception as e:
            logger.error(f"❌ 保存综合性能数据失败: {e}")

    def get_call_chain_dashboard(self) -> dict[str, Any]:
        """获取调用链路监控仪表板"""
        return self.call_chain_monitor.get_performance_dashboard()

    def get_tracing_report(self, time_range_minutes: int = 60) -> dict[str, Any]:
        """获取指定时间范围内的追踪报告"""
        return self.call_chain_monitor.generate_tracing_report(time_range_minutes)

    def get_active_alerts(self) -> list[dict[str, Any]]:
        """获取当前活跃的告警"""
        return self.call_chain_monitor.get_active_alerts()

    def save_call_chain_data(self, filepath: str | None = None) -> None:
        """保存调用链路监控数据"""
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"data/call_chain_report_{timestamp}.json"

        try:
            # 获取完整的监控数据
            dashboard = self.get_call_chain_dashboard()
            alerts = self.get_active_alerts()
            tracing_report = self.get_tracing_report(1440)  # 24小时数据

            # 合并数据
            call_chain_data = {
                "timestamp": datetime.now().isoformat(),
                "dashboard": dashboard,
                "alerts": alerts,
                "tracing_report": tracing_report,
            }

            # 保存到文件
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(call_chain_data, f, indent=2, ensure_ascii=False, default=str)

            logger.info(f"💾 调用链路监控数据已保存: {filepath}")
        except Exception as e:
            logger.error(f"❌ 保存调用链路数据失败: {e}")

    def save_performance_data(self, filepath: str | None = None) -> None:
        """保存性能数据"""
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"data/nlp_performance_report_{timestamp}.json"

        try:
            # 保存数据流优化器数据
            self.data_flow_optimizer.save_performance_data(filepath)

            logger.info(f"💾 NLP性能数据已保存: {filepath}")
        except Exception as e:
            logger.error(f"❌ 保存性能数据失败: {e}")

    def cleanup_resources(self) -> None:
        """清理资源"""
        logger.info("🧹 正在清理统一接口资源...")

        # 关闭线程池
        if hasattr(self, "executor"):
            self.executor.shutdown(wait=True)

        # 清理调用链路监控器
        if hasattr(self, "call_chain_monitor"):
            self.call_chain_monitor.cleanup()

        # 清理性能监控器
        if hasattr(self, "performance_monitoring"):
            self.performance_monitoring.cleanup()

        # 清理数据流优化器
        if hasattr(self, "data_flow_optimizer"):
            self.data_flow_optimizer.cleanup()

        # 清理缓存
        self.cache.clear()

        logger.info("✅ 统一接口资源清理完成")
        logger.info("🗑️ 缓存已清空")

    def save_state(self, filepath: str) -> None:
        """保存状态 - 🔧 安全修复:使用上下文管理器确保文件正确关闭"""
        state = {
            "performance_stats": self.performance_stats,
            "cache_stats": self.cache_stats,
            "config": self.config.__dict__,
        }

        # 保存用户学习状态
        if "user_learner" in self.modules:
            state["user_profiles"] = self.modules["user_learner"].export_profiles()

        # 安全修复:使用上下文管理器确保文件正确关闭
        with open(filepath, "wb") as f:
            f.write(serialize_for_cache(state))

        logger.info(f"💾 状态已保存到: {filepath}")

    def load_state(self, filepath: str) -> Any | None:
        """加载状态 - 🔧 安全修复:使用上下文管理器确保文件正确关闭"""
        if not os.path.exists(filepath):
            logger.warning(f"⚠️ 状态文件不存在: {filepath}")
            return

        try:
            # 安全修复:使用上下文管理器确保文件正确关闭
            with open(filepath, "rb") as f:
                state = deserialize_from_cache(f.read())

            self.performance_stats = state.get("performance_stats", {})
            self.cache_stats = state.get("cache_stats", {})

            # 加载用户学习状态
            if "user_profiles" in state and "user_learner" in self.modules:
                self.modules["user_learner"].import_profiles(state["user_profiles"])

            logger.info(f"📂 状态已从 {filepath} 加载")

        except Exception as e:
            logger.error(f"❌ 状态加载失败: {e}")


def test_unified_interface() -> Any:
    """测试统一接口"""
    print("🧪 开始测试统一NLP接口...")

    # 初始化统一接口
    interface = XiaonuoUnifiedInterface()

    # 测试单次处理
    print("\n📝 测试1: 单次处理")
    request = NLPRequest(
        text="帮我分析这段Python代码的性能", user_id="test_user", context={}, enable_caching=True
    )

    response = interface.process_single(request)

    print(f"请求ID: {response.request_id}")
    print(f"意图: {response.intent}")
    print(f"置信度: {response.confidence:.3f}")
    print(f"选择的工具: {response.selected_tools}")
    print(f"提取的参数: {list(response.extracted_parameters.keys())}")
    print(f"识别的实体: {len(response.entities)}个")
    print(f"处理时间: {response.processing_time:.3f}s")

    # 测试批量处理
    print("\n📝 测试2: 批量处理")
    requests = [
        NLPRequest(text="今天天气怎么样?", user_id="user1"),
        NLPRequest(text="发送邮件给张三", user_id="user2"),
        NLPRequest(text="部署应用到服务器", user_id="user3"),
    ]

    batch_responses = interface.process_batch(requests)
    print(f"批量处理完成: {len(batch_responses)}个响应")

    # 测试对话处理
    print("\n📝 测试3: 对话处理")
    conv_response1 = interface.process_conversation("test_user", "我想预约会议室")
    print(f"第一轮响应: {conv_response1.intent}")

    conv_response2 = interface.process_conversation("test_user", "明天下午3点")
    print(f"第二轮响应: {conv_response2.intent}")
    print(f"提取参数: {conv_response2.extracted_parameters}")

    # 显示增强性能统计(包含数据流优化器数据)
    stats = interface.get_enhanced_performance_stats()
    print("\n📊 增强性能统计:")
    print(f"  总请求数: {stats['requests']['total']}")
    print(f"  成功率: {stats['requests']['success_rate']:.2%}")
    print(f"  缓存命中率: {stats['cache']['hit_rate']:.2%}")
    print(f"  数据流缓存命中率: {stats['dataflow_cache']['hit_rate']:.2%}")
    print(f"  内存使用: {stats['memory_usage_mb']:.1f}MB")
    print(f"  平均延迟: {stats['dataflow_metrics']['avg_latency']:.4f}s")
    print(f"  吞吐量: {stats['dataflow_metrics']['throughput']:.2f} req/s")

    # 保存性能数据
    interface.save_performance_data()

    # 清理资源
    interface.cleanup_resources()

    print("\n✅ 统一接口测试完成!")


if __name__ == "__main__":
    test_unified_interface()
