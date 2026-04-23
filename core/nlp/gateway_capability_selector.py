#!/usr/bin/env python3
from __future__ import annotations
"""
网关能力选择器
Gateway Capability Selector

基于18个网关能力的智能选择器
训练模型接口:提供与XiaonuoIntelligentToolSelector兼容的接口

作者: Athena平台团队
版本: v2.1.0
"""

import logging
import os
import threading
from dataclasses import dataclass
from typing import Any, TypedDict

import jieba
import joblib
import numpy as np

# 配置日志
logger = logging.getLogger(__name__)

# ==================== 常量定义 ====================

# 用户偏好增强系数:10%
# - 足够影响排序,但不会完全覆盖模型预测
# - 经验值,可在未来通过A/B测试优化
PREFERENCE_BOOST_COEFFICIENT = 0.1

# 用户反馈学习率
LEARNING_RATE_POSITIVE = 0.1
LEARNING_RATE_NEGATIVE = 0.1

# 最大文本长度限制
MAX_TEXT_LENGTH = 10000

# 支持的模型版本
SUPPORTED_MODEL_VERSIONS = ["2.0.0", "2.1.0"]

# 模型文件必需字段
REQUIRED_MODEL_KEYS = [
    "model",
    "vectorizer",
    "scaler",
    "label_encoder",
    "feature_keys",
    "capabilities",
]

# 最大模型文件大小(500MB)
MAX_MODEL_FILE_SIZE = 500 * 1024 * 1024


# ==================== 自定义异常类 ====================


class CapabilitySelectorError(Exception):
    """能力选择器基础异常"""

    pass


class ModelNotFoundError(CapabilitySelectorError):
    """模型文件不存在"""

    pass


class ModelLoadError(CapabilitySelectorError):
    """模型加载失败"""

    pass


class ModelValidationError(CapabilitySelectorError):
    """模型验证失败"""

    pass


class InvalidInputError(CapabilitySelectorError):
    """输入参数无效"""

    pass


class FeatureExtractionError(CapabilitySelectorError):
    """特征提取失败"""

    pass


class PredictionError(CapabilitySelectorError):
    """预测失败"""

    pass


# ==================== 类型定义 ====================


class FlatFeatures(TypedDict):
    """扁平化特征字典"""

    word_count: float
    char_count: float
    avg_word_length: float
    has_question: float
    has_command: float
    urgency: float
    daily_chat_keywords: float
    platform_controller_keywords: float
    coding_assistant_keywords: float
    life_assistant_keywords: float
    patent_keywords: float
    legal_keywords: float
    nlp_keywords: float
    knowledge_graph_keywords: float
    memory_keywords: float
    optimization_keywords: float
    multimodal_keywords: float
    agent_fusion_keywords: float
    autonomous_keywords: float
    enterprise_keywords: float
    quantization_keywords: float
    federated_keywords: float
    xiaochen_keywords: float


class CapabilitySelection(TypedDict):
    """能力选择结果"""

    capability: str
    confidence: float


@dataclass
class UserPreferenceUpdate:
    """用户偏好更新"""

    user_id: str
    selected_tool: str
    success: bool
    satisfaction: float  # 0.0-1.0

    def __post_init__(self):
        if not isinstance(self.satisfaction, (int, float)):
            raise TypeError(f"satisfaction必须是数值类型: {type(self.satisfaction)}")
        if not 0.0 <= self.satisfaction <= 1.0:
            raise ValueError(f"satisfaction必须在0.0-1.0之间: {self.satisfaction}")


# ==================== 辅助函数 ====================


def _validate_text_input(text: str) -> None:
    """
    验证文本输入

    Args:
        text: 待验证的文本

    Raises:
        InvalidInputError: 如果文本无效
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected str, got {type(text).__name__}")

    text = text.strip()
    if not text:
        raise ValueError("Text cannot be empty")

    if len(text) > MAX_TEXT_LENGTH:
        raise ValueError(f"Text too long: {len(text)} > {MAX_TEXT_LENGTH}")


def _validate_model_file(model_path: str) -> None:
    """
    验证模型文件的完整性

    Args:
        model_path: 模型文件路径

    Raises:
        ModelNotFoundError: 文件不存在
        ModelValidationError: 文件验证失败
    """
    if not os.path.exists(model_path):
        raise ModelNotFoundError(f"Model file not found: {model_path}")

    # 检查文件扩展名
    if not model_path.endswith(".pkl"):
        raise ModelValidationError(f"Model file must be .pkl format: {model_path}")

    # 检查文件大小
    file_size = os.path.getsize(model_path)
    if file_size > MAX_MODEL_FILE_SIZE:
        raise ModelValidationError(f"Model file too large: {file_size} bytes")
    if file_size == 0:
        raise ModelValidationError(f"Model file is empty: {model_path}")


def _has_keywords(text: str, keywords: list[str]) -> float:
    """
    检测文本中是否包含指定关键词

    Args:
        text: 待检测的文本
        keywords: 关键词列表

    Returns:
        float: 1.0表示包含,0.0表示不包含
    """
    return 1.0 if any(kw in text for kw in keywords) else 0.0


# ==================== 特征提取 ====================


def extract_flat_features(text: str) -> FlatFeatures:
    """
    提取扁平化数值特征(与训练脚本一致)

    此函数提取两类特征:
    1. 基础统计特征:词数、字符数、平均词长等
    2. 关键词匹配特征:18个能力类别的关键词命中数

    Args:
        text: 待分析的输入文本

    Returns:
        FlatFeatures: 包含25+特征的字典,特征键名与训练时一致

    Raises:
        InvalidInputError: 如果文本输入无效
        FeatureExtractionError: 如果特征提取失败

    Examples:
        >>> features = extract_flat_features("帮我查一下专利")
        >>> features['patent_keywords']
        1.0
    """
    try:
        # 输入验证
        _validate_text_input(text)

        words = list(jieba.cut(text))
        word_count = len(words)
        char_count = len(text)

        # 基础特征
        features: dict[str, float] = {
            "word_count": float(word_count),
            "char_count": float(char_count),
            "avg_word_length": char_count / max(word_count, 1),
            "has_question": _has_keywords(text, ["?", "?", "什么", "怎么", "如何", "为什么"]),
            "has_command": _has_keywords(text, ["启动", "停止", "开始", "结束", "执行", "运行"]),
            "urgency": _has_keywords(text, ["紧急", "马上", "立即", "快", "急"]),
        }

        # 能力关键词特征
        capability_keywords = {
            # 基础能力关键词
            "daily_chat_keywords": [
                "你好",
                "心情",
                "聊天",
                "无聊",
                "放松",
                "天气",
                "新闻",
                "娱乐",
                "搜索",
            ],
            "platform_controller_keywords": [
                "启动",
                "停止",
                "重启",
                "系统",
                "服务",
                "监控",
                "配置",
                "部署",
                "运维",
            ],
            "coding_assistant_keywords": [
                "代码",
                "程序",
                "API",
                "函数",
                "算法",
                "bug",
                "调试",
                "优化",
                "性能",
            ],
            "life_assistant_keywords": [
                "日程",
                "提醒",
                "计划",
                "时间",
                "安排",
                "备忘",
                "待办",
                "助理",
                "助手",
            ],
            # 专业能力关键词
            "patent_keywords": [
                "专利",
                "申请专利",
                "专利检索",
                "专利分析",
                "专利侵权",
                "专利法律",
                "专利申请",
            ],
            "legal_keywords": [
                "法律",
                "法规",
                "诉讼",
                "合同",
                "法律咨询",
                "法律文书",
                "案例分析",
                "合规",
            ],
            # 高级能力关键词
            "nlp_keywords": [
                "文本",
                "语义",
                "情感",
                "摘要",
                "分析",
                "提取",
                "理解",
                "识别",
                "分类",
            ],
            "knowledge_graph_keywords": [
                "知识图谱",
                "实体",
                "关系",
                "图谱",
                "推理",
                "链接",
                "节点",
                "可视化",
            ],
            "memory_keywords": ["记住", "回忆", "保存", "记忆", "存储", "记录", "历史", "上下文"],
            "optimization_keywords": [
                "优化",
                "提升",
                "改进",
                "效率",
                "性能",
                "决策",
                "资源",
                "流程",
            ],
            # Phase 3能力关键词
            "multimodal_keywords": [
                "图片",
                "图像",
                "语音",
                "视频",
                "视觉",
                "音频",
                "多模态",
                "看图",
            ],
            "agent_fusion_keywords": [
                "智能体",
                "agent",
                "协作",
                "融合",
                "多智能体",
                "协同",
                "编排",
                "调度",
            ],
            "autonomous_keywords": [
                "自主",
                "自动",
                "学习",
                "适应",
                "自我",
                "智能",
                "独立",
                "自动化",
            ],
            # Phase 4能力关键词
            "enterprise_keywords": [
                "企业",
                "公司",
                "租户",
                "组织",
                "多租户",
                "管理",
                "协作",
                "数据",
            ],
            "quantization_keywords": [
                "量化",
                "压缩",
                "精度",
                "加速",
                "模型",
                "推理",
                "训练",
                "优化",
            ],
            "federated_keywords": [
                "联邦",
                "分布式",
                "隐私",
                "协同",
                "联合",
                "隐私保护",
                "协作学习",
            ],
            # 智能体能力关键词
            "xiaochen_keywords": ["小晨", "xiaochen", "小晨智能体", "小晨助手"],
        }

        # 计算每个能力的关键词匹配分数
        for feature_name, keywords in capability_keywords.items():
            features[feature_name] = float(sum(1 for kw in keywords if kw in text))

        return FlatFeatures(**features)

    except (TypeError, ValueError) as e:
        raise InvalidInputError(f"Invalid input: {e}") from e
    except Exception as e:
        raise FeatureExtractionError(f"Feature extraction failed: {e}") from e


# ==================== 网关能力选择器 ====================


class GatewayCapabilitySelector:
    """网关能力选择器(基于训练模型)"""

    # 类成员类型声明
    model: Any
    vectorizer: Any
    scaler: Any
    label_encoder: Any
    feature_keys: list[str]
    capabilities: list[str]
    accuracy: float
    user_preferences: dict[str, dict[str, float]]
    model_version: str

    def __init__(self, model_path: Optional[str] = None, fail_fast: bool = False):
        """
        初始化能力选择器

        Args:
            model_path: 模型文件路径,默认为最新模型
            fail_fast: 如果为True,模型加载失败时立即抛出异常

        Raises:
            ModelNotFoundError: 模型文件不存在且fail_fast=True
            RuntimeError: 模型加载失败且fail_fast=True
        """
        if model_path is None:
            model_path = "models/intelligent_tool_selector/latest_capability_selector.pkl"

        self.model_path = model_path
        self.model_version = "unknown"
        self._initialize_attributes()
        self._load_model_if_exists(fail_fast)

    def _initialize_attributes(self) -> None:
        """初始化所有属性为None或空值"""
        self.model = None
        self.vectorizer = None
        self.scaler = None
        self.label_encoder = None
        self.feature_keys = None
        self.capabilities = []
        self.accuracy = 0.0
        self.user_preferences: dict[str, dict[str, float]] = {}
        self.model_version = "unknown"

    def _load_model_if_exists(self, fail_fast: bool = False) -> None:
        """
        如果模型文件存在则加载

        Args:
            fail_fast: 如果为True,加载失败时抛出异常

        Raises:
            ModelNotFoundError: 文件不存在且fail_fast=True
            RuntimeError: 加载失败且fail_fast=True
        """
        loaded = False
        if os.path.exists(self.model_path):
            loaded = self.load_models(self.model_path)
        else:
            logger.warning(f"Model file not found: {self.model_path}")

        if fail_fast and not loaded:
            raise RuntimeError(
                f"Failed to initialize capability selector. "
                f"Model path: {self.model_path}, Loaded: {loaded}"
            )

    def load_models(self, model_path: str) -> bool:
        """
        加载训练好的模型

        Args:
            model_path: 模型文件路径

        Returns:
            bool: 是否成功加载

        Raises:
            ModelValidationError: 模型文件验证失败
            ModelLoadError: 模型加载失败
        """
        try:
            # 验证模型文件
            _validate_model_file(model_path)

            with open(model_path, "rb") as f:
                model_data = joblib.load(f)

            # 验证模型数据结构
            missing_keys = [k for k in REQUIRED_MODEL_KEYS if k not in model_data]
            if missing_keys:
                raise ModelValidationError(f"Missing keys in model data: {missing_keys}")

            # 验证模型版本
            model_version = model_data.get("version", "2.0.0")
            if model_version not in SUPPORTED_MODEL_VERSIONS:
                logger.warning(
                    f"Model version {model_version} not in supported list: "
                    f"{SUPPORTED_MODEL_VERSIONS}"
                )

            # 验证模型对象
            model = model_data["model"]
            if not hasattr(model, "predict_proba"):
                raise ModelValidationError("Model object does not have predict_proba method")

            # 加载模型组件
            self.model = model
            self.vectorizer = model_data["vectorizer"]
            self.scaler = model_data["scaler"]
            self.label_encoder = model_data["label_encoder"]
            self.feature_keys = model_data["feature_keys"]
            self.capabilities = model_data["capabilities"]
            self.accuracy = model_data.get("accuracy", 0.0)
            self.model_version = model_version

            logger.info(f"Successfully loaded capability selector model: {model_path}")
            logger.info(f"Model version: {self.model_version}")
            logger.info(f"Model accuracy: {self.accuracy:.4f}")
            logger.info(f"Supported capabilities: {len(self.capabilities)}")
            return True

        except (ModelValidationError, OSError) as e:
            logger.error(f"Model validation failed: {e}", exc_info=True)
            raise ModelLoadError(f"Failed to load model: {e}") from e
        except Exception as e:
            logger.error(f"Model loading failed: {e}", exc_info=True)
            raise ModelLoadError(f"Failed to load model: {e}") from e

    def is_available(self) -> bool:
        """检查模型是否可用"""
        return self.model is not None

    def select_capability(
        self,
        text: str,
        intent: str,
        context: Optional[dict[str, Any]] = None,
        user_id: str = "default",
    ) -> tuple[str, float]:
        """
        选择最合适的网关能力

        使用训练好的机器学习模型,结合用户历史偏好,
        从18个网关能力中选择最匹配的能力。

        Args:
            text: 用户输入文本
            intent: 意图类别(当前未使用,保留用于未来扩展)
            context: 上下文特征(可选,当前未使用)
            user_id: 用户ID(用于个性化偏好调整)

        Returns:
            tuple[str, float]: (能力名称, 置信度)
                - 能力名称: 18个预定义能力之一
                - 置信度: 0.0-1.0之间的置信分数

        Raises:
            InvalidInputError: 当输入参数无效时
            PredictionError: 当预测过程失败时
            ModelLoadError: 当模型未加载时
        """
        if not self.is_available():
            raise ModelLoadError(f"Model not loaded. Current model path: {self.model_path}")

        try:
            # 输入验证
            _validate_text_input(text)

            # 1. 提取特征
            features = extract_flat_features(text)
            features_array = np.array([[features[k] for k in self.feature_keys]])

            # 2. 文本向量化
            text_vec = self.vectorizer.transform([text]).toarray()

            # 3. 特征缩放
            features_scaled = self.scaler.transform(features_array)

            # 4. 组合特征
            combined = np.hstack([text_vec, features_scaled])

            # 5. 预测
            pred_proba = self.model.predict_proba(combined)[0]
            pred_idx = pred_proba.argmax()
            predicted_capability = self.label_encoder.classes_[pred_idx]
            confidence = float(pred_proba[pred_idx])

            # 6. 应用用户偏好增强
            confidence = self._apply_user_preference(confidence, predicted_capability, user_id)

            return (predicted_capability, confidence)

        except InvalidInputError:
            raise
        except (ValueError, TypeError) as e:
            raise InvalidInputError(f"Invalid input: {e}") from e
        except Exception as e:
            logger.error(
                f"Capability selection failed: {e}",
                extra={
                    "user_id": user_id,
                    "text_length": len(text),
                    "intent": intent,
                    "model_available": self.is_available(),
                },
            )
            raise PredictionError(f"Capability selection failed: {e}") from e

    def _apply_user_preference(
        self, confidence: float, predicted_capability: str, user_id: str
    ) -> float:
        """
        应用用户偏好调整置信度

        Args:
            confidence: 原始置信度
            predicted_capability: 预测的能力
            user_id: 用户ID

        Returns:
            float: 调整后的置信度
        """
        if user_id not in self.user_preferences:
            return confidence

        user_prefs = self.user_preferences[user_id]
        if predicted_capability in user_prefs:
            pref_boost = user_prefs[predicted_capability] * PREFERENCE_BOOST_COEFFICIENT
            confidence = min(confidence + pref_boost, 1.0)

        return confidence

    def select_tools(
        self,
        text: str,
        intent: str,
        context: Optional[dict[str, Any]] = None,
        user_id: str = "default",
    ) -> list[tuple[str, float]]:
        """
        选择工具(兼容接口)

        注意:此方法返回的是能力名称,而不是低级工具名称

        Args:
            text: 用户输入文本
            intent: 意图类别
            context: 上下文特征(可选)
            user_id: 用户ID(用于个性化)

        Returns:
            list[tuple[str, float]]: [(能力名称, 置信度), ...]
        """
        try:
            result = self.select_capability(text, intent, context, user_id)
            return [result]
        except CapabilitySelectorError:
            return []

    def update_user_feedback(self, update: UserPreferenceUpdate) -> None:
        """
        更新用户反馈(带验证和持久化)

        Args:
            update: 用户偏好更新数据

        Raises:
            InvalidInputError: 如果satisfaction不在0.0-1.0之间
        """
        # 验证输入
        if not 0.0 <= update.satisfaction <= 1.0:
            raise InvalidInputError(f"satisfaction必须在0.0-1.0之间: {update.satisfaction}")

        # 获取当前偏好
        if update.user_id not in self.user_preferences:
            self.user_preferences[update.user_id] = {}

        current_pref = self.user_preferences[update.user_id].get(update.selected_tool, 0.5)

        # 更新偏好(带学习率衰减)
        learning_rate = LEARNING_RATE_POSITIVE if update.success else LEARNING_RATE_NEGATIVE

        if update.success:
            new_pref = min(current_pref + update.satisfaction * learning_rate, 1.0)
        else:
            new_pref = max(current_pref - (1 - update.satisfaction) * learning_rate, 0.0)

        self.user_preferences[update.user_id][update.selected_tool] = new_pref

        # TODO: 持久化到数据库
        # await self._persist_preferences(update.user_id)

        logger.info(
            "User preference updated",
            extra={
                "user_id": update.user_id,
                "tool": update.selected_tool,
                "old_pref": current_pref,
                "new_pref": new_pref,
                "success": update.success,
                "satisfaction": update.satisfaction,
            },
        )

    def get_model_info(self) -> dict[str, Any]:
        """
        获取模型信息

        Returns:
            dict[str, Any]: 模型信息字典
        """
        return {
            "model_path": self.model_path,
            "model_version": self.model_version,
            "is_available": self.is_available(),
            "accuracy": self.accuracy,
            "capabilities": self.capabilities,
            "feature_count": len(self.feature_keys) if self.feature_keys else 0,
            "user_count": len(self.user_preferences),
            "supported_versions": SUPPORTED_MODEL_VERSIONS,
        }


# ==================== 线程安全的单例模式 ====================

_selector_instance: GatewayCapabilitySelector | None = None
_selector_lock = threading.Lock()


def get_capability_selector() -> GatewayCapabilitySelector:
    """
    获取能力选择器单例(线程安全)

    注意:此实现使用双重检查锁定模式,确保线程安全。

    Returns:
        GatewayCapabilitySelector: 能力选择器实例
    """
    global _selector_instance

    if _selector_instance is None:
        with _selector_lock:
            # 双重检查锁定
            if _selector_instance is None:
                _selector_instance = GatewayCapabilitySelector()

    return _selector_instance
