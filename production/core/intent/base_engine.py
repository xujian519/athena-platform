"""
意图识别服务 - 基础引擎抽象类

定义所有意图识别引擎的统一接口和公共方法。

Author: Xiaonuo
Created: 2025-01-17
Version: 1.0.0
"""

from __future__ import annotations
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from types import TracebackType
from typing import Any

from pydantic import BaseModel, Field

# ========================================================================
# 数据模型定义
# ========================================================================


class IntentType(str, Enum):
    """意图类型枚举 - 统一版本

    整合所有引擎的意图类型,提供统一的分类体系。
    """

    # ==================== 专利相关 ====================
    PATENT_SEARCH = "PATENT_SEARCH"  # 专利检索/查新
    PATENT_ANALYSIS = "PATENT_ANALYSIS"  # 专利分析
    PATENT_COMPARISON = "PATENT_COMPARISON"  # 专利对比
    PATENT_DRAFTING = "PATENT_DRAFTING"  # 专利撰写
    PATENT_TRANSLATION = "PATENT_TRANSLATION"  # 专利翻译

    # 专利专业类
    OPINION_RESPONSE = "OPINION_RESPONSE"  # 审查意见答复
    INFRINGEMENT_ANALYSIS = "INFRINGEMENT_ANALYSIS"  # 侵权分析

    # ==================== 法律相关 ====================
    LEGAL_CONSULTING = "LEGAL_CONSULTING"  # 法律咨询
    LEGAL_RESEARCH = "LEGAL_RESEARCH"  # 法律研究
    CONTRACT_ANALYSIS = "CONTRACT_ANALYSIS"  # 合同分析

    # ==================== 代码相关 ====================
    CODE_GENERATION = "CODE_GENERATION"  # 代码生成
    CODE_REVIEW = "CODE_REVIEW"  # 代码审查
    CODE_DEBUGGING = "CODE_DEBUGGING"  # 代码调试
    CODE_REFCTORING = "CODE_REFCTORING"  # 代码重构

    # ==================== 查询相关 ====================
    INFORMATION_QUERY = "INFORMATION_QUERY"  # 信息查询
    DEFINITION_QUERY = "DEFINITION_QUERY"  # 定义查询
    EXPLANATION_QUERY = "EXPLANATION_QUERY"  # 解释说明
    KNOWLEDGE_QUERY = "KNOWLEDGE_QUERY"  # 知识查询
    QUESTION_ANSWERING = "QUESTION_ANSWERING"  # 问答

    # ==================== 分析相关 ====================
    ANALYSIS_REQUEST = "ANALYSIS_REQUEST"  # 分析请求
    COMPARISON_REQUEST = "COMPARISON_REQUEST"  # 比较请求
    EVALUATION_REQUEST = "EVALUATION_REQUEST"  # 评估请求
    DATA_ANALYSIS = "DATA_ANALYSIS"  # 数据分析

    # ==================== 操作相关 ====================
    TASK_EXECUTION = "TASK_EXECUTION"  # 任务执行
    PROBLEM_SOLVING = "PROBLEM_SOLVING"  # 问题解决
    RECOMMENDATION_REQUEST = "RECOMMENDATION_REQUEST"  # 推荐请求

    # ==================== 文档相关 ====================
    DOCUMENT_PROCESSING = "DOCUMENT_PROCESSING"  # 文档处理

    # ==================== 交互相关 ====================
    GENERAL_CHAT = "GENERAL_CHAT"  # 通用对话
    CONVERSATION = "CONVERSATION"  # 会话
    EMOTIONAL = "EMOTIONAL"  # 情感表达

    # ==================== 创意相关 ====================
    CREATIVE_WRITING = "CREATIVE_WRITING"  # 创意写作

    # ==================== 系统相关 ====================
    TASK_MANAGEMENT = "TASK_MANAGEMENT"  # 任务管理
    SYSTEM_COMMAND = "SYSTEM_COMMAND"  # 系统命令
    CONFIGURATION_CHANGE = "CONFIGURATION_CHANGE"  # 配置变更
    HEALTH_CHECK = "HEALTH_CHECK"  # 健康检查
    SYSTEM_MONITORING = "SYSTEM_MONITORING"  # 系统监控
    TECHNICAL_EVALUATION = "TECHNICAL_EVALUATION"  # 技术评估

    # ==================== 默认 ====================
    UNKNOWN = "UNKNOWN"


class ComplexityLevel(str, Enum):
    """复杂度级别枚举"""

    SIMPLE = "simple"  # 简单
    MEDIUM = "medium"  # 中等
    COMPLEX = "complex"  # 复杂
    EXPERT = "expert"  # 专家级


class IntentCategory(str, Enum):
    """意图类别枚举"""

    PATENT = "patent"  # 专利相关
    LEGAL = "legal"  # 法律相关
    CODE = "code"  # 代码相关
    QUERY = "query"  # 查询相关
    ANALYSIS = "analysis"  # 分析相关
    OPERATION = "operation"  # 操作相关
    CREATIVE = "creative"  # 创意相关
    SYSTEM = "system"  # 系统相关
    GENERAL = "general"  # 通用


class IntentResult(BaseModel):
    """意图识别结果模型 - 统一版本"""

    # 基础字段
    intent: IntentType = Field(description="识别出的意图类型")
    confidence: float = Field(ge=0.0, le=1.0, description="置信度,范围0-1")
    category: IntentCategory = Field(description="意图类别")
    raw_text: str = Field(description="原始输入文本")
    processing_time_ms: float = Field(description="处理时间(毫秒)")
    model_version: str = Field(default="unknown", description="模型版本")

    # 实体和概念
    entities: list[str] = Field(default_factory=list, description="提取的实体")
    key_concepts: list[str] = Field(default_factory=list, description="关键概念")

    # 复杂度和评估
    complexity: ComplexityLevel = Field(default=ComplexityLevel.MEDIUM, description="任务复杂度")

    # 语义相关
    semantic_similarity: float = Field(default=0.0, ge=0.0, le=1.0, description="语义相似度分数")

    # 上下文和建议
    context_requirements: list[str] = Field(default_factory=list, description="上下文要求")
    suggested_tools: list[str] = Field(default_factory=list, description="建议使用的工具")

    # 处理策略
    processing_strategy: str = Field(default="", description="处理策略描述")

    # 预估时间
    estimated_time: float = Field(default=0.0, description="预估处理时间(秒)")

    # 扩展元数据
    metadata: dict[str, Any] = Field(default_factory=dict, description="额外元数据")

    class Config:
        """Pydantic配置"""

        use_enum_values = False  # 保持枚举类型,不转换为字符串
        json_encoders = {datetime: lambda v: v.isoformat()}  # type: ignore[call-arg]


class EngineStats(BaseModel):
    """引擎统计信息模型"""

    total_requests: int = Field(default=0, description="总请求数")
    successful_requests: int = Field(default=0, description="成功请�数")
    failed_requests: int = Field(default=0, description="失败请求数")
    cache_hits: int = Field(default=0, description="缓存命中数")
    semantic_enhancements: int = Field(default=0, description="语义增强次数")
    avg_processing_time_ms: float = Field(default=0.0, description="平均处理时间")
    last_request_time: datetime = Field(default=None, description="最后请求时间")


# ========================================================================
# 基础引擎抽象类
# ========================================================================


class BaseIntentEngine(ABC):
    """
    意图识别引擎基础抽象类

    定义所有意图识别引擎的统一接口和公共方法。
    所有具体的引擎实现都应该继承此类。
    """

    # 类级别的配置
    engine_name: str = "base_engine"
    engine_version: str = "1.0.0"
    supported_intents: set[IntentType] = {IntentType.UNKNOWN}

    def __init__(self, config: dict[str, Any] | None = None):
        """
        初始化引擎

        Args:
            config: 引擎配置字典
        """
        self.config = config or {}
        self.logger = logging.getLogger(f"intent.{self.engine_name}")
        self._stats = EngineStats()

        # 初始化引擎
        self._initialize()

    @abstractmethod
    def _initialize(self) -> None:
        """
        初始化引擎(子类实现)

        在此方法中加载模型、初始化资源等。
        """
        pass

    @abstractmethod
    def recognize_intent(self, text: str, context: dict[str, Any] | None = None) -> IntentResult:
        """
        识别意图(核心方法,子类必须实现)

        Args:
            text: 输入文本
            context: 上下文信息(可选)

        Returns:
            意图识别结果

        Raises:
            ValidationError: 输入验证失败
            ModelInferenceError: 模型推理失败
        """
        pass

    async def recognize_intent_async(
        self, text: str, context: dict[str, Any]  | None = None, user_id: str | None = None
    ) -> IntentResult:
        """
        异步识别意图(默认实现,子类可重写优化)

        默认实现使用ThreadPoolExecutor在异步上下文中运行同步方法。

        Args:
            text: 输入文本
            context: 上下文信息(可选)
            user_id: 用户ID(可选)

        Returns:
            意图识别结果
        """
        # 默认实现:在异步上下文中运行同步方法
        import asyncio
        import concurrent.futures

        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            result = await loop.run_in_executor(pool, self.recognize_intent, text, context)
        return result

    def recognize_batch(
        self, texts: list[str], context: dict[str, Any] | None = None
    ) -> list[IntentResult]:
        """
        批量识别意图(默认实现,子类可重写优化)

        Args:
            texts: 输入文本列表
            context: 上下文信息(可选)

        Returns:
            意图识别结果列表
        """
        return [self.recognize_intent(text, context) for text in texts]

    def get_stats(self) -> EngineStats:
        """
        获取引擎统计信息

        Returns:
            统计信息对象
        """
        return self._stats

    def reset_stats(self) -> None:
        """重置统计信息"""
        self._stats = EngineStats()

    # ========================================================================
    # 公共工具方法
    # ========================================================================

    def _normalize_text(self, text: str) -> str:
        """
        标准化文本

        执行文本清洗、格式化等预处理操作。

        Args:
            text: 原始文本

        Returns:
            标准化后的文本
        """
        if not text:
            return ""

        # 去除首尾空白
        text = text.strip()

        # 统一换行符
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # 去除多余空白
        text = " ".join(text.split())

        return text

    def _validate_input(self, text: str) -> None:
        """
        验证输入文本

        Args:
            text: 输入文本

        Raises:
            ValidationError: 输入不符合要求
        """
        from core.intent.exceptions import ValidationError

        if not isinstance(text, str):
            raise ValidationError(
                field_name="input_text", provided_value=text, reason="输入必须是字符串类型"
            )

        if not text:
            raise ValidationError(
                field_name="input_text", provided_value="", reason="输入文本不能为空"
            )

        max_length = self.config.get("max_input_length", 10000)
        if len(text) > max_length:
            raise ValidationError(
                field_name="input_text",
                provided_value=f"长度:{len(text)}",
                reason=f"输入文本长度超过限制({max_length}字符)",
            )

    def _extract_entities(self, text: str) -> list[str]:
        """
        提取实体(基础实现)

        子类可以重写此方法以实现更复杂的实体提取。

        Args:
            text: 输入文本

        Returns:
            提取的实体列表
        """
        # 基础实现:提取常见的专利相关实体
        entities = []

        # 专利号模式
        import re

        patent_pattern = r"(CN\d{7,}[A-Z]?|US\d{7,}|EP\d{7,}|WO\d{8,})"
        patents = re.findall(patent_pattern, text, re.IGNORECASE)
        entities.extend(patents)

        # 数字模式(可能是年份、数量等)
        number_pattern = r"\d{4,}"
        numbers = re.findall(number_pattern, text)
        entities.extend(numbers)

        return list(set(entities))  # 去重

    def _update_stats(
        self, success: bool, processing_time_ms: float, cache_hit: bool = False
    ) -> None:
        """
        更新统计信息

        Args:
            success: 是否成功
            processing_time_ms: 处理时间(毫秒)
            cache_hit: 是否命中缓存
        """
        self._stats.total_requests += 1

        if success:
            self._stats.successful_requests += 1
        else:
            self._stats.failed_requests += 1

        if cache_hit:
            self._stats.cache_hits += 1

        # 更新平均处理时间
        total_time = (
            self._stats.avg_processing_time_ms * (self._stats.total_requests - 1)
            + processing_time_ms
        )
        self._stats.avg_processing_time_ms = total_time / self._stats.total_requests

        self._stats.last_request_time = datetime.now()

    # ========================================================================
    # 生命周期管理
    # ========================================================================

    def cleanup(self) -> None:
        """
        清理资源

        子类应该重写此方法以释放资源(如GPU内存)。
        """
        self.logger.info(f"{self.engine_name}: 清理资源")
        self._initialize = lambda: None  # 防止重复初始化

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException],
        exc_val: BaseException,
        exc_tb: TracebackType,
    ):
        """上下文管理器出口"""
        self.cleanup()

    def __repr__(self) -> str:
        """字符串表示"""
        return (
            f"{self.__class__.__name__}("
            f"name='{self.engine_name}', "
            f"version='{self.engine_version}', "
            f"requests={self._stats.total_requests})"
        )


# ========================================================================
# 工厂模式支持
# ========================================================================


class IntentEngineFactory:
    """
    意图识别引擎工厂

    使用工厂模式创建引擎实例。
    """

    _registered_engines: dict[str, type[BaseIntentEngine]] = {}

    @classmethod
    def register(cls, engine_type: str, engine_class: type[BaseIntentEngine]) -> None:
        """
        注册引擎类型

        Args:
            engine_type: 引擎类型标识
            engine_class: 引擎类
        """
        cls._registered_engines[engine_type] = engine_class

    @classmethod
    def create(cls, engine_type: str | None = None, config: dict[str, Any] | None = None) -> BaseIntentEngine:
        """
        创建引擎实例

        Args:
            engine_type: 引擎类型
            config: 配置字典

        Returns:
            引擎实例

        Raises:
            ConfigurationError: 引擎类型未注册
        """
        from core.intent.exceptions import ConfigurationError

        if engine_type not in cls._registered_engines:
            raise ConfigurationError(
                config_key="engine_type",
                reason=f"未知的引擎类型: {engine_type},"
                f"可用类型: {list(cls._registered_engines.keys())}",
            )

        engine_class = cls._registered_engines[engine_type]
        return engine_class(config)

    @classmethod
    def list_engines(cls) -> list[str]:
        """
        列出所有已注册的引擎类型

        Returns:
            引擎类型列表
        """
        return list(cls._registered_engines.keys())


# ========================================================================
# 辅助函数
# ========================================================================


def create_default_result(
    text: str, processing_time_ms: float, model_version: str = "unknown"
) -> IntentResult:
    """
    创建默认的意图识别结果

    Args:
        text: 输入文本
        processing_time_ms: 处理时间
        model_version: 模型版本

    Returns:
        默认意图结果
    """
    return IntentResult(
        intent=IntentType.UNKNOWN,
        confidence=0.0,
        entities=[],
        category=IntentCategory.GENERAL,
        raw_text=text,
        processing_time_ms=processing_time_ms,
        model_version=model_version,
    )


def merge_results(results: list[IntentResult], strategy: str = "weighted_vote") -> IntentResult:
    """
    合并多个意图识别结果

    Args:
        results: 结果列表
        strategy: 合并策略 (weighted_vote, max_confidence, first)

    Returns:
        合并后的结果
    """
    if not results:
        raise ValueError("结果列表不能为空")

    if strategy == "max_confidence":
        # 选择置信度最高的结果
        return max(results, key=lambda r: r.confidence)

    elif strategy == "first":
        # 返回第一个结果
        return results[0]

    elif strategy == "weighted_vote":
        # 加权投票(基于置信度)
        intent_scores = {}
        category_scores = {}

        for result in results:
            intent_scores[result.intent] = intent_scores.get(result.intent, 0) + result.confidence
            category_scores[result.category] = (
                category_scores.get(result.category, 0) + result.confidence
            )

        # 选择得分最高的意图
        best_intent = max(intent_scores, key=lambda k: intent_scores[k])  # type: ignore[call-arg]
        best_category = max(category_scores, key=lambda k: category_scores[k])  # type: ignore[call-arg]

        # 使用最佳结果的基础信息
        best_result = max(results, key=lambda r: r.confidence)

        return IntentResult(
            intent=best_intent,
            confidence=min(intent_scores[best_intent] / len(results), 1.0),
            entities=best_result.entities,
            category=best_category,
            raw_text=best_result.raw_text,
            processing_time_ms=sum(r.processing_time_ms for r in results),
            model_version="ensemble",
            metadata={"merged_from": len(results)},
        )

    else:
        raise ValueError(f"未知的合并策略: {strategy}")


# ========================================================================
# 辅助函数
# ========================================================================


def infer_category_from_intent(intent: IntentType) -> IntentCategory:
    """
    从意图类型推断类别

    Args:
        intent: 意图类型

    Returns:
        意图类别
    """
    # 专利相关
    if intent in {
        IntentType.PATENT_SEARCH,
        IntentType.PATENT_ANALYSIS,
        IntentType.PATENT_COMPARISON,
        IntentType.PATENT_DRAFTING,
        IntentType.PATENT_TRANSLATION,
        IntentType.OPINION_RESPONSE,
        IntentType.INFRINGEMENT_ANALYSIS,
    }:
        return IntentCategory.PATENT

    # 法律相关
    if intent in {
        IntentType.LEGAL_CONSULTING,
        IntentType.LEGAL_RESEARCH,
        IntentType.CONTRACT_ANALYSIS,
    }:
        return IntentCategory.LEGAL

    # 代码相关
    if intent in {
        IntentType.CODE_GENERATION,
        IntentType.CODE_REVIEW,
        IntentType.CODE_DEBUGGING,
        IntentType.CODE_REFCTORING,
    }:
        return IntentCategory.CODE

    # 查询相关
    if intent in {
        IntentType.INFORMATION_QUERY,
        IntentType.DEFINITION_QUERY,
        IntentType.EXPLANATION_QUERY,
        IntentType.KNOWLEDGE_QUERY,
        IntentType.QUESTION_ANSWERING,
    }:
        return IntentCategory.QUERY

    # 分析相关
    if intent in {
        IntentType.ANALYSIS_REQUEST,
        IntentType.COMPARISON_REQUEST,
        IntentType.EVALUATION_REQUEST,
        IntentType.DATA_ANALYSIS,
    }:
        return IntentCategory.ANALYSIS

    # 操作相关
    if intent in {
        IntentType.TASK_EXECUTION,
        IntentType.PROBLEM_SOLVING,
        IntentType.RECOMMENDATION_REQUEST,
    }:
        return IntentCategory.OPERATION

    # 创意相关
    if intent in {
        IntentType.CREATIVE_WRITING,
    }:
        return IntentCategory.CREATIVE

    # 系统相关
    if intent in {
        IntentType.SYSTEM_COMMAND,
        IntentType.CONFIGURATION_CHANGE,
        IntentType.HEALTH_CHECK,
        IntentType.SYSTEM_MONITORING,
        IntentType.TECHNICAL_EVALUATION,
        IntentType.TASK_MANAGEMENT,
        IntentType.DOCUMENT_PROCESSING,
    }:
        return IntentCategory.SYSTEM

    # 交互相关
    if intent in {
        IntentType.GENERAL_CHAT,
        IntentType.CONVERSATION,
        IntentType.EMOTIONAL,
    }:
        return IntentCategory.GENERAL

    # 默认
    return IntentCategory.GENERAL
