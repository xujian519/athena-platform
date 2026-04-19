#!/usr/bin/env python3
"""
配置管理模块
统一管理Phase 2处理管道的所有配置

作者: Athena平台团队
创建时间: 2025-12-25
"""

from __future__ import annotations
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from core.config.secure_config import get_config

config = get_config()

import logging
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# 添加项目路径
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入安全配置
try:
    from production.config import get_nebula_config, get_postgres_config
except ImportError:
    def get_nebula_config() -> Any | None:
        return {'host': '127.0.0.1', 'port': 9669, 'user': 'root', "password": config.get("NEBULA_PASSWORD", required=True), 'space': 'patent_full_text_v2'}
    def get_postgres_config() -> Any | None:
        return {'host': 'localhost', 'port': 5432, 'user': 'athena', "password": config.get("POSTGRES_PASSWORD", required=True), 'database': 'patent_db'}

logger = logging.getLogger(__name__)


@dataclass
class QdrantConfig:
    """Qdrant向量数据库配置"""

    host: str = "localhost"
    port: int = 6333
    collection_name: str = "patent_full_text_v2"  # Phase 3使用v2集合
    vector_size: int = 768  # BGE-base-zh-v1.5维度
    distance: str = "COSINE"
    timeout: int = 60

    # 分片配置
    shard_number: int = 4
    replication_factor: int = 1

    # 混合检索配置
    enable_sparse: bool = False  # Phase 3暂不启用稀疏向量

    # Phase 3: 分层向量化配置
    enable_layered_vectorization: bool = True
    layer1_enabled: bool = True   # 全局检索层
    layer2_enabled: bool = True   # 核心内容层
    layer3_enabled: bool = True   # 发明内容层

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"


@dataclass
class NebulaGraphConfig:
    """NebulaGraph图数据库配置 - 从环境变量读取"""

    connection_pool_size: int = 2

    # 图空间配置
    partition_num: int = 10
    replica_factor: int = 1
    vid_type: str = "FIXED_STRING(32)"

    @property
    def hosts(self) -> str:
        nebula_config = get_nebula_config()
        return f"{nebula_config.get('host', '127.0.0.1')}:{nebula_config.get('port', 9669)}"

    @property
    def username(self) -> str:
        nebula_config = get_nebula_config()
        return nebula_config.get('user', 'root')

    @property
    def password(self) -> str:
        nebula_config = get_nebula_config()
        return nebula_config.get("password", config.get("NEBULA_PASSWORD", required=True))

    @property
    def space_name(self) -> str:
        nebula_config = get_nebula_config()
        return nebula_config.get('space', 'patent_full_text_v2')

    # Phase 3: 增强的图结构配置
    vertex_types: list = field(default_factory=lambda: [
        # 基础顶点
        "patent", "claim", "applicant", "ipc_class",
        # 技术分析顶点（Phase 3新增）
        "technical_problem", "technical_feature", "technical_effect", "solution",
        # 对比分析顶点
        "contrast_document", "discriminating_feature"
    ])
    edge_types: list = field(default_factory=lambda: [
        # 基础边
        "HAS_CLAIM", "HAS_APPLICANT", "BELONGS_TO_IPC", "DEPENDS_ON",
        # 技术逻辑关系（Phase 3新增）
        "SOLVES", "ACHIEVES", "RELATES_TO", "CONSISTS_OF",
        # 专利对比关系
        "CITES", "SIMILAR_TO", "HAS_D1", "HAS_D2", "NOT_IN_D1", "REVEALED_BY"
    ])


@dataclass
class PostgreSQLConfig:
    """PostgreSQL数据库配置 - 从环境变量读取"""

    # 表名配置
    patents_table: str = "apps/apps/patents"

    @property
    def host(self) -> str:
        config = get_postgres_config()
        return config.get('host', 'localhost')

    @property
    def port(self) -> int:
        config = get_postgres_config()
        return config.get('port', 5432)

    @property
    def database(self) -> str:
        config = get_postgres_config()
        return config.get('database', 'patent_db')

    @property
    def user(self) -> str:
        config = get_postgres_config()
        return config.get('user', 'athena')

    @property
    def password(self) -> str:
        config = get_postgres_config()
        return config.get("password", config.get("POSTGRES_PASSWORD", required=True))

    @property
    def dsn(self) -> str:
        config = get_postgres_config()
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class BGEModelConfig:
    """BGE模型配置"""

    # 本地模型路径 - 使用项目Apple Silicon优化的模型
    model_path: str = "/Users/xujian/Athena工作平台/models/bge-base-zh-v1.5"

    # 模型参数
    device: str = "mps"  # mps为Apple Silicon GPU加速，cpu/cuda为其他设备
    batch_size: int = 32

    # 向量化参数
    chunk_size: int = 500  # token块大小
    chunk_overlap: int = 50  # 块重叠
    max_length: int = 512  # 最大序列长度

    # 稀疏向量（BM25）参数
    sparse_enabled: bool = True
    sparse_top_k: int = 50  # 提取关键词数量


@dataclass
class PDFProcessorConfig:
    """PDF处理配置"""

    # PDF提取器选择
    preferred_backend: str = "pdfplumber"  # pdfplumber 或 PyPDF2

    # 语言检测
    enable_language_detection: bool = True
    default_language: str = "zh"  # zh, en, mixed

    # 文本清理
    clean_extra_whitespace: bool = True
    remove_page_numbers: bool = True

    # 输出目录
    pdf_output_dir: str = "/Users/xujian/apps/apps/patents/PDF"
    text_output_dir: str = "/Users/xujian/apps/apps/patents/text"


@dataclass
class PatentDownloaderConfig:
    """专利下载器配置"""

    # 输出目录
    output_dir: str = "/Users/xujian/apps/apps/patents/PDF"

    # 下载参数
    timeout: int = 120  # 超时时间（秒）
    max_retries: int = 3  # 最大重试次数

    # 支持的专利号格式
    supported_formats: list = field(default_factory=lambda: [
        "CN", "US", "EP", "WO", "JP", "KR", "GB", "DE", "FR"
    ])


@dataclass
class ProcessingConfig:
    """处理管道配置"""

    # 批处理配置
    batch_size: int = 10
    max_workers: int = 4

    # 错误处理
    max_retries: int = 3
    retry_delay: float = 1.0
    continue_on_error: bool = True

    # 日志配置
    log_level: str = "INFO"
    log_file: str | None = None

    # 性能监控
    enable_profiling: bool = False
    profile_output_dir: str | None = None


@dataclass
class Phase2Config:
    """Phase 2处理管道总配置"""

    # 子配置
    qdrant: QdrantConfig = field(default_factory=QdrantConfig)
    nebula: NebulaGraphConfig = field(default_factory=NebulaGraphConfig)
    postgresql: PostgreSQLConfig = field(default_factory=PostgreSQLConfig)
    bge_model: BGEModelConfig = field(default_factory=BGEModelConfig)
    pdf_processor: PDFProcessorConfig = field(default_factory=PDFProcessorConfig)
    downloader: PatentDownloaderConfig = field(default_factory=PatentDownloaderConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)

    # 项目路径
    project_root: Path = field(default_factory=lambda: Path("/Users/xujian/Athena工作平台"))
    phase2_dir: Path | None = None
    patent_downloader_src: Path | None = None

    def __post_init__(self):
        """初始化派生路径"""
        if self.phase2_dir is None:
            self.phase2_dir = self.project_root / "production/dev/scripts/patent_full_text/phase2"
        if self.patent_downloader_src is None:
            self.patent_downloader_src = self.project_root / "dev/tools/patent_downloader/src"

    @classmethod
    def from_env(cls) -> "Phase2Config":
        """
        从环境变量加载配置

        环境变量命名规则:
        - QDRANT_HOST
        - NEBULA_HOSTS
        - POSTGRES_HOST
        - BGE_MODEL_PATH
        - PDF_OUTPUT_DIR
        """
        config = cls()

        # Qdrant配置
        if os.getenv("QDRANT_HOST"):
            config.qdrant.host = os.getenv("QDRANT_HOST")
        if os.getenv("QDRANT_PORT"):
            config.qdrant.port = int(os.getenv("QDRANT_PORT"))
        if os.getenv("QDRANT_COLLECTION"):
            config.qdrant.collection_name = os.getenv("QDRANT_COLLECTION")

        # NebulaGraph配置
        if os.getenv("NEBULA_HOSTS"):
            config.nebula.hosts = os.getenv("NEBULA_HOSTS")
        if os.getenv("NEBULA_USERNAME"):
            config.nebula.username = os.getenv("NEBULA_USERNAME")
        if os.getenv("NEBULA_PASSWORD"):
            config.nebula.password = os.getenv("NEBULA_PASSWORD")
        if os.getenv("NEBULA_SPACE"):
            config.nebula.space_name = os.getenv("NEBULA_SPACE")

        # PostgreSQL配置
        if os.getenv("POSTGRES_HOST"):
            config.postgresql.host = os.getenv("POSTGRES_HOST")
        if os.getenv("POSTGRES_PORT"):
            config.postgresql.port = int(os.getenv("POSTGRES_PORT"))
        if os.getenv("POSTGRES_DATABASE"):
            config.postgresql.database = os.getenv("POSTGRES_DATABASE")
        if os.getenv("POSTGRES_USER"):
            config.postgresql.user = os.getenv("POSTGRES_USER")
        if os.getenv("POSTGRES_PASSWORD"):
            config.postgresql.password = os.getenv("POSTGRES_PASSWORD")

        # BGE模型配置
        if os.getenv("BGE_MODEL_PATH"):
            config.bge_model.model_path = os.getenv("BGE_MODEL_PATH")
        if os.getenv("BGE_DEVICE"):
            config.bge_model.device = os.getenv("BGE_DEVICE")

        # PDF处理配置
        if os.getenv("PDF_OUTPUT_DIR"):
            config.pdf_processor.pdf_output_dir = os.getenv("PDF_OUTPUT_DIR")
        if os.getenv("TEXT_OUTPUT_DIR"):
            config.pdf_processor.text_output_dir = os.getenv("TEXT_OUTPUT_DIR")

        # 专利下载配置
        if os.getenv("PATENT_OUTPUT_DIR"):
            config.downloader.output_dir = os.getenv("PATENT_OUTPUT_DIR")

        # 处理配置
        if os.getenv("LOG_LEVEL"):
            config.processing.log_level = os.getenv("LOG_LEVEL")

        return config

    @classmethod
    def from_file(cls, config_file: str) -> "Phase2Config":
        """
        从配置文件加载（支持JSON和YAML）

        Args:
            config_file: 配置文件路径

        Returns:
            Phase2Config实例
        """
        config_path = Path(config_file)

        if not config_path.exists():
            logger.warning(f"配置文件不存在: {config_file}，使用默认配置")
            return cls()

        suffix = config_path.suffix.lower()

        if suffix == '.json':
            import json
            with open(config_path, encoding='utf-8') as f:
                data = json.load(f)
            return cls._from_dict(data)

        elif suffix in ['.yaml', '.yml']:
            try:
                import yaml
                with open(config_path, encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                return cls._from_dict(data)
            except ImportError:
                logger.error("YAML支持需要安装PyYAML: pip install pyyaml")
                return cls()

        else:
            logger.error(f"不支持的配置文件格式: {suffix}")
            return cls()

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "Phase2Config":
        """从字典创建配置"""
        config = cls()

        if not isinstance(data, dict):
            return config

        # Qdrant配置
        if "qdrant" in data:
            for key, value in data["qdrant"].items():
                if hasattr(config.qdrant, key):
                    setattr(config.qdrant, key, value)

        # NebulaGraph配置
        if "nebula" in data:
            for key, value in data["nebula"].items():
                if hasattr(config.nebula, key):
                    setattr(config.nebula, key, value)

        # PostgreSQL配置
        if "postgresql" in data:
            for key, value in data["postgresql"].items():
                if hasattr(config.postgresql, key):
                    setattr(config.postgresql, key, value)

        # BGE模型配置
        if "bge_model" in data:
            for key, value in data["bge_model"].items():
                if hasattr(config.bge_model, key):
                    setattr(config.bge_model, key, value)

        # PDF处理配置
        if "pdf_processor" in data:
            for key, value in data["pdf_processor"].items():
                if hasattr(config.pdf_processor, key):
                    setattr(config.pdf_processor, key, value)

        # 专利下载配置
        if "downloader" in data:
            for key, value in data["downloader"].items():
                if hasattr(config.downloader, key):
                    setattr(config.downloader, key, value)

        # 处理配置
        if "processing" in data:
            for key, value in data["processing"].items():
                if hasattr(config.processing, key):
                    setattr(config.processing, key, value)

        return config

    def to_file(self, config_file: str, format: str = "yaml") -> Any:
        """
        保存配置到文件

        Args:
            config_file: 配置文件路径
            format: 文件格式 (yaml 或 json)
        """
        config_path = Path(config_file)
        config_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "qdrant": {
                "host": self.qdrant.host,
                "port": self.qdrant.port,
                "collection_name": self.qdrant.collection_name,
                "vector_size": self.qdrant.vector_size,
                "distance": self.qdrant.distance,
                "timeout": self.qdrant.timeout,
                "enable_sparse": self.qdrant.enable_sparse
            },
            "nebula": {
                "hosts": self.nebula.hosts,
                "username": self.nebula.username,
                "password": self.nebula.password,
                "space_name": self.nebula.space_name,
                "connection_pool_size": self.nebula.connection_pool_size
            },
            "postgresql": {
                "host": self.postgresql.host,
                "port": self.postgresql.port,
                "infrastructure/infrastructure/database": self.postgresql.database,
                "user": self.postgresql.user,
                "password": self.postgresql.password,
                "patents_table": self.postgresql.patents_table
            },
            "bge_model": {
                "model_path": self.bge_model.model_path,
                "device": self.bge_model.device,
                "batch_size": self.bge_model.batch_size,
                "chunk_size": self.bge_model.chunk_size,
                "chunk_overlap": self.bge_model.chunk_overlap,
                "max_length": self.bge_model.max_length,
                "sparse_enabled": self.bge_model.sparse_enabled,
                "sparse_top_k": self.bge_model.sparse_top_k
            },
            "pdf_processor": {
                "preferred_backend": self.pdf_processor.preferred_backend,
                "enable_language_detection": self.pdf_processor.enable_language_detection,
                "default_language": self.pdf_processor.default_language,
                "pdf_output_dir": self.pdf_processor.pdf_output_dir,
                "text_output_dir": self.pdf_processor.text_output_dir
            },
            "downloader": {
                "output_dir": self.downloader.output_dir,
                "timeout": self.downloader.timeout,
                "max_retries": self.downloader.max_retries
            },
            "processing": {
                "batch_size": self.processing.batch_size,
                "max_workers": self.processing.max_workers,
                "max_retries": self.processing.max_retries,
                "continue_on_error": self.processing.continue_on_error,
                "log_level": self.processing.log_level
            }
        }

        if format == "yaml":
            try:
                import yaml
                with open(config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
            except ImportError:
                logger.error("YAML支持需要安装PyYAML: pip install pyyaml")
        else:  # json
            import json
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"配置已保存到: {config_file}")

    def validate(self) -> bool:
        """验证配置有效性"""
        valid = True

        # 验证路径
        if not Path(self.bge_model.model_path).exists():
            logger.warning(f"BGE模型路径不存在: {self.bge_model.model_path}")
            valid = False

        # 验证输出目录
        Path(self.pdf_processor.pdf_output_dir).mkdir(parents=True, exist_ok=True)
        Path(self.pdf_processor.text_output_dir).mkdir(parents=True, exist_ok=True)
        Path(self.downloader.output_dir).mkdir(parents=True, exist_ok=True)

        return valid

    def setup_logging(self) -> Any:
        """设置日志"""
        log_level = getattr(logging, self.processing.log_level.upper(), logging.INFO)

        handlers = [logging.stream_handler()]

        if self.processing.log_file:
            handlers.append(
                logging.file_handler(self.processing.log_file, encoding='utf-8')
            )

        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=handlers
        )

        logger.info(f"日志级别设置为: {self.processing.log_level}")


# ==================== 全局配置实例 ====================

# 默认配置
_default_config: Phase2Config | None = None


def get_config() -> Phase2Config:
    """
    获取全局配置实例

    优先级: 环境变量 > 配置文件 > 默认值
    """
    global _default_config

    if _default_config is None:
        # 1. 尝试从环境变量加载
        config = Phase2Config.from_env()

        # 2. 尝试从配置文件加载（如果存在）
        config_file = Path.home() / ".athena" / "patent_phase2_config.yaml"
        if config_file.exists():
            file_config = Phase2Config.from_file(str(config_file))
            # 环境变量优先
            for key in ["qdrant", "nebula", "postgresql", "bge_model", "pdf_processor", "downloader", "processing"]:
                if hasattr(file_config, key):
                    section = getattr(file_config, key)
                    default_section = getattr(config, key)
                    for attr in dir(section):
                        if not attr.startswith('_'):
                            env_value = os.getenv(f"{key.upper()}_{attr.upper()}")
                            if env_value:
                                setattr(section, attr, env_value)
            config = file_config

        # 3. 验证并设置日志
        config.validate()
        config.setup_logging()

        _default_config = config

    return _default_config


def reset_config() -> Any:
    """重置全局配置"""
    global _default_config
    _default_config = None


# ==================== 示例使用 ====================

def main() -> None:
    """示例使用"""
    print("=" * 70)
    print("配置管理模块示例")
    print("=" * 70)

    # 获取配置
    config = get_config()

    print("\n📋 Qdrant配置:")
    print(f"   URL: {config.qdrant.url}")
    print(f"   集合: {config.qdrant.collection_name}")
    print(f"   向量维度: {config.qdrant.vector_size}")

    print("\n📋 NebulaGraph配置:")
    print(f"   地址: {config.nebula.hosts}")
    print(f"   空间: {config.nebula.space_name}")

    print("\n📋 PostgreSQL配置:")
    print(f"   DSN: {config.postgresql.dsn}")

    print("\n📋 BGE模型配置:")
    print(f"   路径: {config.bge_model.model_path}")
    print(f"   块大小: {config.bge_model.chunk_size}")

    # 保存示例配置
    example_config_file = Path.home() / ".athena" / "patent_phase2_config_example.yaml"
    config.to_file(str(example_config_file), format="yaml")
    print(f"\n✅ 示例配置已保存到: {example_config_file}")


# ========== Phase 3: 新增配置类 ==========

@dataclass
class TripleExtractionConfig:
    """三元组提取配置 (Phase 3)"""

    # 提取方法配置
    enable_rule_extraction: bool = True
    enable_local_model: bool = True
    enable_cloud_llm: bool = False  # 默认不使用云端LLM

    # 规则提取器配置
    rule_confidence_threshold: float = 0.6
    rule_max_problems: int = 10
    rule_max_effects: int = 10

    # 本地模型配置
    local_model_name: str = "chinese_legal_electra"
    local_model_confidence: float = 0.7

    # 云端LLM配置
    cloud_llm_provider: str = "glm-4.6"  # glm-4.6 或其他
    cloud_llm_api_key: str = "9efe5766a7cd4bb687e40082ee4032b6.0mYTotbC7aRmoNCe"
    cloud_llm_api_url: str = "https://open.bigmodel.cn/api/paas/v4"
    cloud_llm_timeout: int = 30

    # 特征关系提取配置
    enable_syntax_relations: bool = True  # 句法关系
    enable_context_relations: bool = True  # 上下文关系
    enable_llm_relations: bool = False  # LLM推理关系
    relation_similarity_threshold: float = 0.7

    # 输出配置
    min_confidence: float = 0.6
    max_triples_per_feature: int = 5


@dataclass
class VectorizationConfigV2:
    """向量化配置V2 (Phase 3)"""

    # 分层向量化开关
    enable_layer1: bool = True  # 全局检索层
    enable_layer2: bool = True  # 核心内容层
    enable_layer3: bool = True  # 发明内容层

    # Layer 1: 全局检索层
    l1_enable_title: bool = True
    l1_enable_abstract: bool = True
    l1_enable_ipc: bool = True

    # Layer 2: 核心内容层
    l2_enable_independent_claims: bool = True
    l2_enable_dependent_claims: bool = True

    # Layer 3: 发明内容层
    l3_enable_technical_problem: bool = True
    l3_enable_technical_solution: bool = True
    l3_enable_beneficial_effects: bool = True
    l3_enable_embodiments: bool = True

    # 分块配置
    solution_chunk_size: int = 1000  # 技术方案块大小
    solution_chunk_overlap: int = 100
    max_embodiment_chunks: int = 10

    # 批处理配置
    batch_size: int = 10
    max_workers: int = 4


@dataclass
class AppConfig:
    """应用主配置"""

    # Phase选择
    current_phase: str = "phase3"  # phase2 或 phase3

    # 日志配置
    log_level: str = "INFO"
    log_file: str | None = None

    # 性能配置
    enable_parallel_processing: bool = True
    max_parallel_workers: int = 4

    # 缓存配置
    enable_cache: bool = True
    cache_ttl: int = 3600  # 秒

    # 调试模式
    debug_mode: bool = False
    verbose: bool = False


# ========== 更新主配置类 ==========


@dataclass
class Config:
    """主配置类 - 整合所有配置"""

    # 数据库配置
    qdrant: QdrantConfig = field(default_factory=QdrantConfig)
    nebula: NebulaGraphConfig = field(default_factory=NebulaGraphConfig)
    postgresql: PostgreSQLConfig = field(default_factory=PostgreSQLConfig)

    # 模型配置
    bge_model: BGEModelConfig = field(default_factory=BGEModelConfig)
    pdf_processor: PDFProcessorConfig = field(default_factory=PDFProcessorConfig)
    patent_downloader: PatentDownloaderConfig = field(default_factory=PatentDownloaderConfig)

    # Phase 3: 新增配置
    triple_extraction: TripleExtractionConfig = field(default_factory=TripleExtractionConfig)
    vectorization_v2: VectorizationConfigV2 = field(default_factory=VectorizationConfigV2)
    app: AppConfig = field(default_factory=AppConfig)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        from dataclasses import asdict
        return asdict(self)

    def to_file(self, filepath: str, format: str = "yaml") -> Any:
        """保存到文件"""
        from pathlib import Path

        import yaml

        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            if format == "yaml":
                yaml.dump(self.to_dict(), f, allow_unicode=True, default_flow_style=False)
            elif format == "json":
                import json
                json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

        logger.info(f"✅ 配置已保存到: {filepath}")


# ========== 便捷函数 ==========

_config_instance = None


def get_config(config_file: str | None = None) -> Config:
    """
    获取配置实例（单例）

    Args:
        config_file: 配置文件路径（可选）

    Returns:
        Config实例
    """
    global _config_instance

    if _config_instance is None:
        _config_instance = Config()

        # 如果提供了配置文件，加载配置
        if config_file:
            from pathlib import Path

            import yaml

            config_path = Path(config_file)
            if config_path.exists():
                with open(config_path, encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    # 更新配置（简单的覆盖方式）
                    for key, value in data.items():
                        if hasattr(_config_instance, key):
                            setattr(_config_instance, key, value)
                logger.info(f"✅ 配置已加载: {config_file}")

    return _config_instance


def set_config(config: Config) -> None:
    """设置配置实例"""
    global _config_instance
    _config_instance = config
    logger.info("✅ 配置已更新")


if __name__ == "__main__":
    main()
