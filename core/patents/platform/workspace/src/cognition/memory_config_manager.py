#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
记忆系统配置管理器
Memory System Configuration Manager

提供统一的配置管理、验证和环境变量支持

作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

import json
import logging
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

logger = logging.getLogger(__name__)

class ConfigSource(Enum):
    """配置来源"""
    DEFAULT = 'default'
    FILE = 'file'
    ENVIRONMENT = 'environment'
    RUNTIME = 'runtime'

@dataclass
class VectorMemoryConfig:
    """向量记忆配置"""
    dimension: int = 1024  # 默认1024维
    max_vectors: int = 10000
    use_faiss: bool = True
    similarity_threshold: float = 0.3
    index_type: str = 'composite'

@dataclass
class EnhancedMemoryConfig:
    """增强记忆配置"""
    enable_vector_memory: bool = True
    enable_knowledge_graph: bool = False
    auto_enhance_memories: bool = True
    knowledge_weight: float = 0.3

@dataclass
class MemoryProcessorConfig:
    """记忆处理器配置"""
    working_memory_capacity: int = 100
    short_term_capacity: int = 1000
    consolidation_interval: int = 3600
    forgetting_threshold: float = 0.1
    storage_path: str = 'memory_storage.db'

@dataclass
class PerformanceConfig:
    """性能配置"""
    monitoring_interval: int = 30
    cache_max_size: int = 1000
    max_concurrent_operations: int = 10
    enable_performance_monitoring: bool = True

@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = 'INFO'
    format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    file_path: Optional[str] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5

@dataclass
class MemorySystemConfig:
    """记忆系统完整配置"""
    vector_memory: VectorMemoryConfig = field(default_factory=VectorMemoryConfig)
    enhanced_memory: EnhancedMemoryConfig = field(default_factory=EnhancedMemoryConfig)
    memory_processor: MemoryProcessorConfig = field(default_factory=MemoryProcessorConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    # 元数据
    version: str = '1.0.0'
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    source: ConfigSource = ConfigSource.DEFAULT

class MemoryConfigManager:
    """记忆系统配置管理器"""

    DEFAULT_CONFIG_PATHS = [
        'memory_config.yaml',
        'memory_config.json',
        'config/memory_config.yaml',
        'config/memory_config.json',
        '~/.athena/memory_config.yaml',
        '/etc/athena/memory_config.yaml'
    ]

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self.config: MemorySystemConfig | None = None
        self._config_sources = {}  # 记录每个配置项的来源

    def load_config(self, config_path: Optional[str] = None) -> MemorySystemConfig:
        """加载配置"""
        # 1. 从默认配置开始
        self.config = MemorySystemConfig()
        self._config_sources = {'default': ConfigSource.DEFAULT}

        # 2. 从文件加载配置（如果存在）
        file_config = self._load_from_file(config_path)
        if file_config:
            self._merge_config(file_config, ConfigSource.FILE)

        # 3. 从环境变量加载配置
        env_config = self._load_from_environment()
        if env_config:
            self._merge_config(env_config, ConfigSource.ENVIRONMENT)

        # 4. 验证配置
        self._validate_config()

        # 5. 记录更新时间
        self.config.updated_at = datetime.now()

        sources = list(self._config_sources.values())
        unique_sources = list(dict.fromkeys(sources))  # 去重
        logger.info(f"✅ 配置加载完成，来源: {unique_sources}")
        return self.config

    def _load_from_file(self, config_path: Optional[str] = None) -> Dict[str, Any] | None:
        """从文件加载配置"""
        search_paths = []

        if config_path:
            search_paths.append(config_path)
        else:
            search_paths.extend(self.DEFAULT_CONFIG_PATHS)

        for path in search_paths:
            # 展开用户目录
            path = os.path.expanduser(path)

            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        if path.endswith('.yaml') or path.endswith('.yml'):
                            config_data = yaml.safe_load(f)
                        else:
                            config_data = json.load(f)

                    logger.info(f"📄 从文件加载配置: {path}")
                    return config_data

                except Exception as e:
                    logger.warning(f"⚠️ 加载配置文件失败 {path}: {e}")

        return None

    def _load_from_environment(self) -> Dict[str, Any]:
        """从环境变量加载配置"""
        env_config = {}

        # 定义环境变量映射
        env_mappings = {
            'MEMORY_VECTOR_DIMENSION': ('vector_memory', 'dimension', int),
            'MEMORY_MAX_VECTORS': ('vector_memory', 'max_vectors', int),
            'MEMORY_USE_FAISS': ('vector_memory', 'use_faiss', bool),
            'MEMORY_SIMILARITY_THRESHOLD': ('vector_memory', 'similarity_threshold', float),
            'MEMORY_INDEX_TYPE': ('vector_memory', 'index_type', str),

            'MEMORY_ENABLE_VECTOR_MEMORY': ('enhanced_memory', 'enable_vector_memory', bool),
            'MEMORY_ENABLE_KNOWLEDGE_GRAPH': ('enhanced_memory', 'enable_knowledge_graph', bool),
            'MEMORY_AUTO_ENHANCE': ('enhanced_memory', 'auto_enhance_memories', bool),
            'MEMORY_KNOWLEDGE_WEIGHT': ('enhanced_memory', 'knowledge_weight', float),

            'MEMORY_WORKING_CAPACITY': ('memory_processor', 'working_memory_capacity', int),
            'MEMORY_SHORT_TERM_CAPACITY': ('memory_processor', 'short_term_capacity', int),
            'MEMORY_CONSOLIDATION_INTERVAL': ('memory_processor', 'consolidation_interval', int),
            'MEMORY_FORGETTING_THRESHOLD': ('memory_processor', 'forgetting_threshold', float),
            'MEMORY_STORAGE_PATH': ('memory_processor', 'storage_path', str),

            'MEMORY_MONITORING_INTERVAL': ('performance', 'monitoring_interval', int),
            'MEMORY_CACHE_MAX_SIZE': ('performance', 'cache_max_size', int),
            'MEMORY_MAX_CONCURRENT': ('performance', 'max_concurrent_operations', int),
            'MEMORY_ENABLE_MONITORING': ('performance', 'enable_performance_monitoring', bool),

            'MEMORY_LOG_LEVEL': ('logging', 'level', str),
            'MEMORY_LOG_FORMAT': ('logging', 'format', str),
            'MEMORY_LOG_FILE': ('logging', 'file_path', str),
        }

        for env_var, (section, key, type_func) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    # 转换类型
                    if type_func == bool:
                        converted_value = value.lower() in ('true', '1', 'yes', 'on')
                    else:
                        converted_value = type_func(value)

                    # 构建嵌套字典结构
                    if section not in env_config:
                        env_config[section] = {}
                    env_config[section][key] = converted_value

                    # 记录配置来源
                    config_key = f"{section}.{key}"
                    self._config_sources[config_key] = ConfigSource.ENVIRONMENT

                except (ValueError, TypeError) as e:
                    logger.warning(f"⚠️ 环境变量 {env_var} 转换失败: {e}")

        if env_config:
            logger.info(f"🌍 从环境变量加载了 {len(env_config)} 个配置项")

        return env_config

    def _merge_config(self, new_config: Dict[str, Any], source: ConfigSource):
        """合并配置"""
        def _merge_dict(target: Dict, source: Dict, prefix: str = ''):
            for key, value in source.items():
                full_key = f"{prefix}.{key}" if prefix else key

                if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                    _merge_dict(target[key], value, full_key)
                else:
                    target[key] = value
                    self._config_sources[full_key] = source

        # 将字典转换为配置对象
        config_dict = asdict(self.config)
        _merge_dict(config_dict, new_config)

        # 重新创建配置对象
        self.config = self._dict_to_config(config_dict)

    def _dict_to_config(self, config_dict: Dict[str, Any]) -> MemorySystemConfig:
        """将字典转换为配置对象"""
        try:
            # 提取各部分配置
            vector_memory_config = VectorMemoryConfig(**config_dict.get('vector_memory', {}))
            enhanced_memory_config = EnhancedMemoryConfig(**config_dict.get('enhanced_memory', {}))
            memory_processor_config = MemoryProcessorConfig(**config_dict.get('memory_processor', {}))
            performance_config = PerformanceConfig(**config_dict.get('performance', {}))
            logging_config = LoggingConfig(**config_dict.get('logging', {}))

            return MemorySystemConfig(
                vector_memory=vector_memory_config,
                enhanced_memory=enhanced_memory_config,
                memory_processor=memory_processor_config,
                performance=performance_config,
                logging=logging_config,
                version=config_dict.get('version', '1.0.0'),
                created_at=config_dict.get('created_at', datetime.now()),
                updated_at=datetime.now(),
                source=config_dict.get('source', ConfigSource.RUNTIME)
            )

        except Exception as e:
            logger.error(f"❌ 配置转换失败: {e}")
            # 返回默认配置
            return MemorySystemConfig()

    def _validate_config(self):
        """验证配置"""
        if not self.config:
            raise ValueError('配置未初始化')

        # 验证向量记忆配置
        if self.config.vector_memory.dimension <= 0:
            raise ValueError('向量维度必须大于0')

        if self.config.vector_memory.max_vectors <= 0:
            raise ValueError('最大向量数必须大于0')

        if not 0 <= self.config.vector_memory.similarity_threshold <= 1:
            raise ValueError('相似度阈值必须在0-1之间')

        # 验证记忆处理器配置
        if self.config.memory_processor.working_memory_capacity <= 0:
            raise ValueError('工作记忆容量必须大于0')

        if self.config.memory_processor.short_term_capacity <= 0:
            raise ValueError('短期记忆容量必须大于0')

        if not 0 <= self.config.memory_processor.forgetting_threshold <= 1:
            raise ValueError('遗忘阈值必须在0-1之间')

        # 验证性能配置
        if self.config.performance.monitoring_interval <= 0:
            raise ValueError('监控间隔必须大于0')

        if self.config.performance.cache_max_size <= 0:
            raise ValueError('缓存大小必须大于0')

        # 验证日志配置
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.config.logging.level not in valid_log_levels:
            raise ValueError(f"日志级别必须是: {valid_log_levels}")

        logger.debug('✅ 配置验证通过')

    def get_config(self) -> MemorySystemConfig:
        """获取当前配置"""
        if not self.config:
            return self.load_config()
        return self.config

    def update_config(self, updates: Dict[str, Any], source: ConfigSource = ConfigSource.RUNTIME):
        """更新配置"""
        if not self.config:
            self.load_config()

        self._merge_config(updates, source)
        self._validate_config()
        self.config.updated_at = datetime.now()

        logger.info(f"📝 配置已更新，来源: {source}")

    def save_config(self, file_path: Optional[str] = None):
        """保存配置到文件"""
        if not self.config:
            raise ValueError('没有可保存的配置')

        target_path = file_path or self.config_path or 'memory_config.yaml'

        # 创建目录
        Path(target_path).parent.mkdir(parents=True, exist_ok=True)

        # 准备保存数据
        config_dict = asdict(self.config)
        # 处理datetime对象
        for key in ['created_at', 'updated_at']:
            if key in config_dict:
                config_dict[key] = config_dict[key].isoformat()

        try:
            with open(target_path, 'w', encoding='utf-8') as f:
                if target_path.endswith('.yaml') or target_path.endswith('.yml'):
                    yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
                else:
                    json.dump(config_dict, f, ensure_ascii=False, indent=2)

            logger.info(f"💾 配置已保存到: {target_path}")

        except Exception as e:
            logger.error(f"❌ 保存配置失败: {e}")
            raise

    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要"""
        if not self.config:
            return {'status': 'not_loaded'}

        return {
            'version': self.config.version,
            'updated_at': self.config.updated_at.isoformat(),
            'sources': list(set(self._config_sources.values())),
            'vector_memory': {
                'dimension': self.config.vector_memory.dimension,
                'max_vectors': self.config.vector_memory.max_vectors,
                'use_faiss': self.config.vector_memory.use_faiss
            },
            'enhanced_memory': {
                'enable_vector_memory': self.config.enhanced_memory.enable_vector_memory,
                'enable_knowledge_graph': self.config.enhanced_memory.enable_knowledge_graph
            },
            'memory_processor': {
                'working_memory_capacity': self.config.memory_processor.working_memory_capacity,
                'short_term_capacity': self.config.memory_processor.short_term_capacity
            },
            'performance': {
                'monitoring_interval': self.config.performance.monitoring_interval,
                'enable_performance_monitoring': self.config.performance.enable_performance_monitoring
            }
        }

    def apply_logging_config(self):
        """应用日志配置"""
        if not self.config:
            return

        # 设置日志级别
        log_level = getattr(logging, self.config.logging.level.upper(), logging.INFO)
        logging.getLogger().setLevel(log_level)

        # 配置日志格式
        formatter = logging.Formatter(self.config.logging.format)

        # 配置文件日志
        if self.config.logging.file_path:
            try:
                from logging.handlers import RotatingFileHandler

                # 创建目录
                Path(self.config.logging.file_path).parent.mkdir(parents=True, exist_ok=True)

                # 添加文件处理器
                file_handler = RotatingFileHandler(
                    self.config.logging.file_path,
                    maxBytes=self.config.logging.max_file_size,
                    backupCount=self.config.logging.backup_count,
                    encoding='utf-8'
                )
                file_handler.setFormatter(formatter)

                # 添加到根日志器
                logging.getLogger().addHandler(file_handler)

                logger.info(f"📝 日志文件配置: {self.config.logging.file_path}")

            except Exception as e:
                logger.warning(f"⚠️ 配置日志文件失败: {e}")

# 全局配置管理器实例
_global_config_manager: MemoryConfigManager | None = None

def get_config_manager(config_path: Optional[str] = None) -> MemoryConfigManager:
    """获取全局配置管理器实例"""
    global _global_config_manager

    if _global_config_manager is None:
        _global_config_manager = MemoryConfigManager(config_path)
        _global_config_manager.load_config()
        _global_config_manager.apply_logging_config()

    return _global_config_manager

def get_config() -> MemorySystemConfig:
    """获取当前配置"""
    return get_config_manager().get_config()

def update_config(updates: Dict[str, Any]):
    """更新配置"""
    get_config_manager().update_config(updates)

def save_config(file_path: Optional[str] = None):
    """保存配置"""
    get_config_manager().save_config(file_path)