#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BGE Large ZH v1.5 向量模型主配置文件
主要向量模型配置：BAAI/bge-large-zh-v1.5
"""

import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# BGE模型路径配置
BGE_MODEL_PATH = '/Users/xujian/Athena工作平台/models/pretrained/bge-large-zh-v1.5'

# 主要向量模型配置
PRIMARY_MODEL_CONFIG = {
    'model_name': 'bge-large-zh-v1.5',
    'model_path': BGE_MODEL_PATH,
    'model_type': 'SentenceTransformer',
    'dimension': 1024,
    'max_length': 512,
    'similarity_fn': 'cosine',
    'normalize_embeddings': True,
    'batch_size': 32,
    'device': 'auto'  # 自动选择GPU或CPU
}

# 模型详细参数
BGE_MODEL_PARAMS = {
    # 基础配置
    'trust_remote_code': True,
    'device': 'auto',

    # 编码配置
    'batch_size': 32,
    'max_length': 512,
    'normalize_to_unit': True,

    # 池化配置
    'pooling_mode': 'cls',
    'pooling_mode_cls_token': True,
    'pooling_mode_max_tokens': False,
    'pooling_mode_mean_tokens': False,

    # 性能优化
    'show_progress_bar': True,
    'convert_to_numpy': True,
    'convert_to_tensor': False
}

# 向量数据库配置
VECTOR_DB_CONFIG = {
    'qdrant': {
        'host': 'localhost',
        'port': 6333,
        'timeout': 30,
        'prefer_grpc': False,
        'collections': {
            'patents': {
                'name': 'patents_bge_1024',
                'dimension': 1024,
                'distance': 'Cosine'
            },
            'legal': {
                'name': 'legal_bge_1024',
                'dimension': 1024,
                'distance': 'Cosine'
            },
            'technical': {
                'name': 'technical_bge_1024',
                'dimension': 1024,
                'distance': 'Cosine'
            }
        }
    }
}

# 缓存配置
CACHE_CONFIG = {
    'enable_cache': True,
    'cache_dir': '/tmp/bge_embeddings_cache',
    'max_cache_size': 10000,
    'cache_ttl': 3600  # 1小时
}

# 应用场景配置
APPLICATION_CONFIGS = {
    'patent_search': {
        'prompt': '为这个专利生成向量用于语义检索',
        'threshold': 0.7,
        'top_k': 10
    },
    'legal_analysis': {
        'prompt': '为这个法律文本生成向量用于分析',
        'threshold': 0.8,
        'top_k': 5
    },
    'technical_matching': {
        'prompt': '为这个技术术语生成向量用于匹配',
        'threshold': 0.85,
        'top_k': 20
    },
    'similarity_search': {
        'prompt': None,  # 使用默认
        'threshold': 0.75,
        'top_k': 15
    }
}

class BGELargeZHConfig:
    """BGE Large ZH v1.5 模型配置类"""

    def __init__(self):
        self.model_path = BGE_MODEL_PATH
        self.config = PRIMARY_MODEL_CONFIG
        self.params = BGE_MODEL_PARAMS
        self.db_config = VECTOR_DB_CONFIG
        self.cache_config = CACHE_CONFIG
        self.app_configs = APPLICATION_CONFIGS

    def get_model_path(self) -> str:
        """获取模型路径"""
        return self.model_path

    def get_model_config(self) -> Dict[str, Any]:
        """获取模型配置"""
        return self.config

    def get_model_params(self) -> Dict[str, Any]:
        """获取模型参数"""
        return self.params

    def get_db_config(self, db_type: str = 'qdrant') -> Dict[str, Any]:
        """获取数据库配置"""
        return self.db_config.get(db_type, {})

    def get_collection_config(self, db_type: str = 'qdrant', collection_name: str = 'patents') -> Dict[str, Any]:
        """获取集合配置"""
        db_config = self.get_db_config(db_type)
        return db_config.get('collections', {}).get(collection_name, {})

    def get_app_config(self, app_name: str) -> Dict[str, Any]:
        """获取应用场景配置"""
        return self.app_configs.get(app_name, {})

    def is_model_available(self) -> bool:
        """检查模型是否可用"""
        return os.path.exists(self.model_path) and os.path.isdir(self.model_path)

    def validate_model_files(self) -> Dict[str, bool]:
        """验证模型文件完整性"""
        required_files = [
            'config.json',
            'model.safetensors',
            'tokenizer.json',
            'vocab.txt',
            'config_sentence_transformers.json'
        ]

        status = {}
        for file_name in required_files:
            file_path = os.path.join(self.model_path, file_name)
            status[file_name] = os.path.exists(file_path)

        return status

# 全局配置实例
bge_config = BGELargeZHConfig()

# 便捷函数
def get_bge_model_path() -> str:
    """获取BGE模型路径"""
    return bge_config.get_model_path()

def get_bge_config() -> Dict[str, Any]:
    """获取BGE模型配置"""
    return bge_config.get_model_config()

def get_bge_params() -> Dict[str, Any]:
    """获取BGE模型参数"""
    return bge_config.get_model_params()

def is_bge_ready() -> bool:
    """检查BGE模型是否就绪"""
    return bge_config.is_model_available()

def validate_bge_model() -> Dict[str, bool]:
    """验证BGE模型文件"""
    return bge_config.validate_model_files()

if __name__ == '__main__':
    logger.info('🚀 BGE Large ZH v1.5 向量模型配置')
    logger.info(f"📁 模型路径: {get_bge_model_path()}")
    logger.info(f"📊 向量维度: {PRIMARY_MODEL_CONFIG['dimension']}")
    logger.info(f"🔗 最大长度: {PRIMARY_MODEL_CONFIG['max_length']}")
    logger.info(f"💾 相似度函数: {PRIMARY_MODEL_CONFIG['similarity_fn']}")

    # 检查模型状态
    logger.info("\n📋 模型状态检查:")
    logger.info(f"✅ 模型可用: {is_bge_ready()}")

    # 验证模型文件
    logger.info("\n📁 文件完整性检查:")
    file_status = validate_bge_model()
    for file_name, exists in file_status.items():
        status = '✅' if exists else '❌'
        logger.info(f"{status} {file_name}")

    # 显示应用场景
    logger.info("\n🎯 支持的应用场景:")
    for app_name, config in APPLICATION_CONFIGS.items():
        logger.info(f"  - {app_name}: 阈值={config['threshold']}, top_k={config['top_k']}")