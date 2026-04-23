#!/usr/bin/env python3

"""
感知模块统一类型定义
Unified Perception Module Type Definitions

此文件集中定义感知模块的所有类型,避免重复定义和类型不一致问题。

作者: Athena AI系统
创建时间: 2026-01-24
版本: 1.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

# =============================================================================
# 枚举类型定义
# =============================================================================


class InputType(Enum):
    """输入类型枚举"""

    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    MULTIMODAL = "multimodal"
    STREAM = "stream"
    UNKNOWN = "unknown"


class DocumentType(Enum):
    """文档类型枚举"""

    PATENT = "patent"
    CONTRACT = "contract"  # 合同文档
    TECH_DISCLOSURE = "tech_disclosure"
    TECH_MANUAL = "tech_manual"
    TECH_DRAWING = "tech_drawing"
    SPECIFICATION = "specification"
    IMAGE = "image"
    UNKNOWN = "unknown"


class ModalityType(Enum):
    """模态类型枚举"""

    TEXT = "text"
    IMAGE = "image"
    TABLE = "table"
    FORMULA = "formula"
    DRAWING = "drawing"
    MARKUP = "markup"
    STRUCTURE = "structure"
    CAD = "cad"
    HANDWRITING = "handwriting"
    MIXED = "mixed"  # 混合模态


class ConfidenceLevel(Enum):
    """置信度等级枚举"""

    HIGH = 0.9  # 高置信度,可直接使用
    MEDIUM = 0.6  # 中等置信度,需要人工确认
    LOW = 0.3  # 低置信度,需要重新处理


class ProcessingMode(Enum):
    """处理模式枚举"""

    STANDARD = "standard"  # 标准处理
    REALTIME = "realtime"  # 实时处理
    BATCH = "batch"  # 批处理
    ADAPTIVE = "adaptive"  # 自适应
    PIPELINE = "pipeline"  # 流水线


class StreamType(Enum):
    """流类型枚举"""

    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    MULTIMODAL = "multimodal"


class DocumentChangeType(Enum):
    """文档变更类型枚举"""

    CREATED = "created"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"
    PARTIAL_MODIFIED = "partial_modified"


class AgentStatus(Enum):
    """智能体状态枚举"""

    INACTIVE = "inactive"
    STARTING = "starting"
    ACTIVE = "active"
    BUSY = "busy"
    IDLE = "idle"
    STOPPING = "stopping"
    ERROR = "error"


# =============================================================================
# 数据类定义
# =============================================================================


@dataclass
class PerceptionResult:
    """感知结果数据类"""

    input_type: InputType
    raw_content: Any
    processed_content: Any
    features: dict[str, Any]
    confidence: float
    metadata: dict[str, Any]
    timestamp: datetime


@dataclass
class PatentPerceptionResult:
    """专利感知结果数据类(统一版本)

    整合了原types.py和enhanced_patent_perception.py中的定义,
    提供完整的专利分析结果结构。
    """

    # 基础标识
    patent_id: Optional[str] = None
    input_type: Optional[str] = None  # PatentInputType枚举值
    modality_type: Optional[str] = None  # ModalityType枚举值

    # 原始内容
    raw_content: Optional[Any] = None
    structured_content: dict[str, Any] = field(default_factory=dict)

    # 专利核心信息
    title: Optional[str] = None
    abstract: Optional[str] = None
    technical_field: Optional[str] = None
    ipc_classification: Optional[list[str]] = None

    # 分析结果
    features: list[dict[str, Any] = field(default_factory=list)
    key_features: dict[str, Any] = field(default_factory=dict)
    novelty_analysis: dict[str, Any] = field(default_factory=dict)
    drawing_elements: list[dict[str, Any] = field(default_factory=list)
    claims_analysis: dict[str, Any] = field(default_factory=dict)

    # 元数据和质量
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    cross_references: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    verification_needed: bool = False
    family_comment: str = ""

    def validate(self) -> bool:
        """验证感知结果的有效性"""
        if self.confidence < 0 or self.confidence > 1:
            raise ValueError(f"无效的置信度: {self.confidence}")
        return True


@dataclass
class DocumentGraph:
    """文档图数据类"""

    document_id: str
    document_type: DocumentType
    nodes: list[dict[str, Any]
    edges: list[dict[str, Any]
    cross_modal_alignments: list[dict[str, Any]
    context_state: dict[str, Any]
    knowledge_injections: list[dict[str, Any]
@dataclass
class PatentDocumentStructure:
    """专利文档结构数据类"""

    title: str
    abstract: str
    claims: dict[int, str]
    description: str
    drawings: list[dict[str, Any]
    tables: list[dict[str, Any]
    technical_specifications: dict[str, Any]
@dataclass
class DocumentChunk:
    """文档分块数据类"""

    chunk_id: str
    start_pos: int
    end_pos: int
    content_hash: str
    processing_status: str = "pending"
    ocr_result: Optional[dict[str, Any]] = None
    last_processed: Optional[datetime] = None
    dependencies: set[str] = field(default_factory=set)


@dataclass
class DocumentMetadata:
    """文档元数据类"""

    file_path: str
    file_hash: str
    last_modified: datetime
    file_size: int
    document_type: DocumentType
    total_chunks: int
    processed_chunks: int
    change_type: DocumentChangeType
    processing_priority: int = 0


@dataclass
class OCRCacheEntry:
    """OCR缓存条目数据类"""

    content_hash: str
    ocr_result: dict[str, Any]
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    chunk_size: int = 0


@dataclass
class StreamChunk:
    """流数据块数据类"""

    chunk_id: str
    data: Any
    timestamp: float
    metadata: dict[str, Any] = field(default_factory=dict)
    sequence_number: int = 0
    is_final: bool = False


@dataclass
class ProcessingResult:
    """处理结果数据类"""

    chunk_id: str
    result: Any
    confidence: float = 0.0
    processing_time: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class StreamConfig:
    """流配置数据类"""

    chunk_size: int = 1024
    buffer_size: int = 8192
    processing_mode: ProcessingMode = ProcessingMode.ADAPTIVE
    overlap_ratio: float = 0.1  # 重叠比例
    enable_gpu_acceleration: bool = True
    batch_timeout: float = 0.1  # 批处理超时
    max_queue_size: int = 100
    enable_backpressure: bool = True


@dataclass
class DIKWPResult:
    """DIKWP框架结果数据类"""

    data: dict[str, Any]
    information: dict[str, Any]
    knowledge: dict[str, Any]
    wisdom: dict[str, Any]
    purpose: dict[str, Any]
    confidence: float
    processing_time: float


@dataclass
class FamilyGuidance:
    """家庭指导数据类(宪法原则应用)"""

    principle_type: str  # 进化/真实/情感
    guidance: str
    confidence_adjustment: float
    verification_requirement: str
    implementation_suggestion: str


# =============================================================================
# 配置类定义
# =============================================================================


@dataclass
class PerceptionConfig:
    """感知模块统一配置类"""

    # 多模态处理配置
    enable_multimodal: bool = True
    enable_cross_modal_alignment: bool = True
    enable_knowledge_injection: bool = True
    enable_dikwp_processing: bool = True

    # 文件处理配置
    supported_formats: list[str] = field(
        default_factory=lambda: [".pdf", ".docx", ".txt", ".jpg", ".png"]
    )
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    ocr_languages: list[str] = field(default_factory=lambda: ["chi_sim", "eng"])

    # 性能优化配置
    enable_incremental_ocr: bool = True
    enable_document_chunking: bool = True
    enable_parallel_processing: bool = True
    enable_memory_optimization: bool = True
    enable_smart_caching: bool = True
    max_concurrent_documents: int = 3
    chunk_size: int = 1024 * 1024  # 1MB
    max_memory_usage: int = 512 * 1024 * 1024  # 512MB

    # 缓存配置
    cache_ttl: timedelta = field(default_factory=lambda: timedelta(days=7))
    cache_max_size: int = 100 * 1024 * 1024  # 100MB

    # 监控配置
    enable_monitoring: bool = True
    enable_performance_tracking: bool = True
    health_check_interval: int = 30  # 秒

    def validate(self) -> bool:
        """验证配置有效性"""
        if self.max_file_size <= 0:
            raise ValueError("max_file_size must be positive")

        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be positive")

        if self.max_concurrent_documents <= 0:
            raise ValueError("max_concurrent_documents must be positive")

        if not self.supported_formats:
            raise ValueError("supported_formats cannot be empty")

        return True


@dataclass
class OptimizedPerceptionConfig(PerceptionConfig):
    """优化感知配置类(继承基础配置)"""

    # 增量OCR配置
    incremental_ocr_enabled: bool = True
    change_detection_enabled: bool = True

    # 并行处理配置
    thread_pool_size: Optional[int] = None  # None表示自动检测CPU核心数

    def __post_init__(self) -> None:
        """初始化后处理"""
        if self.thread_pool_size is None:
            import os

            self.thread_pool_size = min(os.cpu_count() or 4, 8)


@dataclass
class CacheConfig:
    """统一缓存配置类

    定义不同类型缓存的TTL(Time To Live)配置。
    基于缓存的数据特性和访问模式优化TTL设置。
    """

    # OCR结果缓存 - 长TTL,因为OCR计算成本高
    ocr_cache_ttl: timedelta = field(default_factory=lambda: timedelta(days=7))

    # 感知结果缓存 - 中等TTL,平衡新鲜度和性能
    result_cache_ttl: timedelta = field(default_factory=lambda: timedelta(days=1))

    # 元数据缓存 - 短TTL,确保文件变更及时检测
    metadata_cache_ttl: timedelta = field(default_factory=lambda: timedelta(hours=1))

    # 性能优化缓存 - 短TTL,用于实时性能优化
    performance_cache_ttl: timedelta = field(default_factory=lambda: timedelta(hours=1))

    # 向量嵌入缓存 - 长TTL,因为嵌入计算成本高
    embedding_cache_ttl: timedelta = field(default_factory=lambda: timedelta(days=3))

    # LRU缓存最大大小
    lru_max_size: int = 1000

    def get_ttl_for_cache_type(self, cache_type: str) -> timedelta:
        """根据缓存类型获取对应的TTL

        Args:
            cache_type: 缓存类型 ('ocr', 'result', 'metadata', 'performance', 'embedding')

        Returns:
            对应的TTL配置

        Raises:
            ValueError: 未知的缓存类型
        """
        ttl_map = {
            "ocr": self.ocr_cache_ttl,
            "result": self.result_cache_ttl,
            "metadata": self.metadata_cache_ttl,
            "performance": self.performance_cache_ttl,
            "embedding": self.embedding_cache_ttl,
        }

        if cache_type not in ttl_map:
            raise ValueError(f"未知的缓存类型: {cache_type}。支持的类型: {list(ttl_map.keys())}")

        return ttl_map[cache_type]

    def validate(self) -> bool:
        """验证缓存配置有效性"""
        if self.lru_max_size <= 0:
            raise ValueError("lru_max_size must be positive")

        # 验证TTL设置合理
        if self.ocr_cache_ttl < timedelta(minutes=10):
            raise ValueError("ocr_cache_ttl should not be less than 10 minutes")

        if self.metadata_cache_ttl > timedelta(hours=4):
            raise ValueError("metadata_cache_ttl should not exceed 4 hours for freshness")

        return True


# =============================================================================
# 导出所有类型
# =============================================================================

__all__ = [
    "AgentStatus",
    "CacheConfig",
    "ConfidenceLevel",
    "DIKWPResult",
    "DocumentChangeType",
    "DocumentChunk",
    "DocumentGraph",
    "DocumentMetadata",
    "DocumentType",
    "FamilyGuidance",
    # 枚举类型
    "InputType",
    "ModalityType",
    "OCRCacheEntry",
    "OptimizedPerceptionConfig",
    "PatentDocumentStructure",
    "PatentPerceptionResult",
    # 配置类
    "PerceptionConfig",
    # 数据类
    "PerceptionResult",
    "ProcessingMode",
    "ProcessingResult",
    "StreamChunk",
    "StreamConfig",
    "StreamType",
]

