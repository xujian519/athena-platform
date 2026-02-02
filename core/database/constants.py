"""
常量定义模块
集中管理所有魔法数字和字符串
"""

import uuid
from enum import Enum
from typing import Final, List

# ==================== UUID命名空间 ====================
UUID_NAMESPACE: Final = uuid.NAMESPACE_DNS

# ==================== 批处理配置 ====================
DEFAULT_BATCH_SIZE: Final[int] = 500
DEFAULT_CONCURRENT_WORKERS: Final[int] = 10
MAX_RETRIES: Final[int] = 3
TIMEOUT_SECONDS: Final[int] = 30

# ==================== 向量配置 ====================
BGE_M3_DIM: Final[int] = 1024
BGE_M3_MAX_SEQ_LENGTH: Final[int] = 8192
DEFAULT_EMBEDDING_BATCH_SIZE: Final[int] = 32

# ==================== 数据库端口配置 ====================
DEFAULT_PG_PORT: Final[int] = 5432
DEFAULT_NEO4J_PORT: Final[int] = 7687
DEFAULT_QDRANT_PORT: Final[int] = 6333


# ==================== 实体标签 ====================
class EntityLabels(str, Enum):
    """实体标签常量"""

    LAW_CONCEPT = "LAW_CONCEPT"
    AUTHORITY = "AUTHORITY"
    ORGANIZATION = "ORGANIZATION"
    PERSON = "PERSON"
    PATENT_NUMBER = "PATENT_NUMBER"

    @classmethod
    def all(cls) -> list[str]:
        """
        获取所有标签

        Returns:
            所有实体标签的列表
        """
        return [v.value for v in cls.__members__.values()]

    @classmethod
    def concept_labels(cls) -> list[str]:
        """
        获取概念类标签(用于实体匹配)

        Returns:
            概念标签列表
        """
        return [
            cls.LAW_CONCEPT.value,
            cls.AUTHORITY.value,
        ]


# ==================== 关系类型 ====================
class RelationTypes(str, Enum):
    """关系类型常量"""

    # Layer 1 内部
    HAS_ARTICLE = "HAS_ARTICLE"

    # Layer 2 内部
    MENTIONS = "MENTIONS"
    BELONGS_TO = "BELONGS_TO"

    # 跨层关系
    CITES = "CITES"  # Layer 3 → Layer 1
    CITED_IN_GUIDE = "CITED_IN_GUIDE"  # Layer 1 → Layer 2
    REFRERS_TO_REVIEW_DECISION = "REFERS_TO_REVIEW_DECISION"  # Layer 3 → Layer 2
    MENTIONS_IN_JUDGMENT = "MENTIONS_IN_JUDGMENT"  # Layer 3 → Layer 2
    CITES_JUDGMENT = "CITES_JUDGMENT"  # Layer 3 → Layer 3

    @classmethod
    def cross_layer_relations(cls) -> list[str]:
        """
        获取所有跨层关系类型

        Returns:
            跨层关系类型列表
        """
        return [
            cls.CITES.value,
            cls.CITED_IN_GUIDE.value,
            cls.REFERS_TO_REVIEW_DECISION.value,
            cls.MENTIONS_IN_JUDGMENT.value,
            cls.CITES_JUDGMENT.value,
        ]


# ==================== 文档类型 ====================
class DocumentTypes(str, Enum):
    """文档类型常量"""

    # Layer 1
    LAW = "法律"
    INTERPRETATION = "司法解释"
    CIVIL_CODE = "民法典"
    CONSTITUTION = "宪法"

    # Layer 2
    REVIEW_DECISION = "review_decision"
    GUIDE_CHAPTER = "guide_chapter"
    CORE_LAW = "core_law"
    OTHER = "other"

    # Layer 3
    JUDGMENT = "judgment"

    @classmethod
    def layer1_types(cls) -> list[str]:
        """获取Layer 1文档类型"""
        return [cls.LAW, cls.INTERPRETATION, cls.CIVIL_CODE, cls.CONSTITUTION]

    @classmethod
    def layer2_types(cls) -> list[str]:
        """获取Layer 2文档类型"""
        return [cls.REVIEW_DECISION, cls.GUIDE_CHAPTER, cls.CORE_LAW, cls.OTHER]


# ==================== 案件类型 ====================
class CaseTypes(str, Enum):
    """案件类型常量"""

    CIVIL_FIRST = "民初"
    CIVIL_FINAL = "民终"
    ADMINISTRATIVE_FINAL = "行终"
    OTHER = "其他"


# ==================== 错误消息 ====================
class ErrorMessages:
    """错误消息常量"""

    CONFIG_MISSING = "缺少必需的环境变量配置"
    FILE_NOT_FOUND = "文件不存在"
    JSON_PARSE_ERROR = "JSON解析失败"
    DATABASE_CONNECTION_ERROR = "数据库连接失败"
    DATABASE_QUERY_ERROR = "数据库查询失败"
