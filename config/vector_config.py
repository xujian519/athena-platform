import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Athena工作平台向量配置
统一管理所有向量维度设置
"""

# 项目向量维度配置
VECTOR_DIMENSION = 1024  # 项目统一使用1024维向量

# 向量集合配置
COLLECTION_CONFIGS = {
    # 专利无效向量库
    'patents_invalid': {
        'name': 'patents_invalid_1024',
        'dimension': VECTOR_DIMENSION,
        'distance': 'Cosine',
        'description': '专利无效宣告向量库'
    },

    # 法律条款向量库
    'legal_clauses': {
        'name': 'legal_clauses_1024',
        'dimension': VECTOR_DIMENSION,
        'distance': 'Cosine',
        'description': '法律条款向量库'
    },

    # 技术术语向量库
    'technical_terms': {
        'name': 'technical_terms_1024',
        'dimension': VECTOR_DIMENSION,
        'distance': 'Cosine',
        'description': '技术术语向量库'
    }
}

COLLECTION_DISPLAY_NAMES = {
    'patent_rules_1024': '专利规则向量库',
    'legal_clauses_1024': '法律条款向量库',
    'technical_terms_1024': '技术术语向量库',
    'patents_invalid_1024': '专利无效向量库'
}

# 模型配置
MODEL_CONFIGS = {
    # BGE-M3 (默认, 通过 OpenAI 兼容 API 服务)
    'bge_m3': {
        'name': 'bge-m3',
        'type': 'api',
        'api_url': 'http://127.0.0.1:8766/v1',
        'dimension': VECTOR_DIMENSION,
        'max_length': 8192
    },

    # BGE-Large-ZH (备用, 本地 SentenceTransformer)
    'bge_large_zh': {
        'name': 'BAAI/bge-large-zh-v1.5',
        'type': 'local',
        'dimension': VECTOR_DIMENSION,
        'max_length': 512
    },

    # 中文BERT模型
    'bert_chinese': {
        'name': 'bert-base-chinese',
        'type': 'local',
        'dimension': VECTOR_DIMENSION,
        'max_length': 512
    },

    # 法律专用模型
    'legal_electra': {
        'name': 'chinese_legal_electra',
        'type': 'local',
        'dimension': VECTOR_DIMENSION,
        'max_length': 512
    }
}

# 默认嵌入模型
DEFAULT_EMBEDDING_MODEL = 'bge_m3'

# Qdrant配置
QDRANT_CONFIG = {
    'host': 'localhost',
    'port': 6333,
    'timeout': 30,
    'batch_size': 100,
    'prefer_grpc': False
}

# 向量处理配置
PROCESSING_CONFIG = {
    'batch_size': 32,
    'normalize': True,
    'use_cache': True,
    'cache_ttl': 3600  # 1小时
}

def get_vector_dimension() -> Optional[int]:
    """获取标准向量维度"""
    return VECTOR_DIMENSION

def get_collection_config(collection_type) -> Optional[dict[str, Any]]:
    """获取向量集合配置"""
    return COLLECTION_CONFIGS.get(collection_type, {})

def get_collection_display_name(collection_name) -> Optional[str]:
    return COLLECTION_DISPLAY_NAMES.get(collection_name, collection_name)

def get_model_config(model_name) -> Optional[dict[str, Any]]:
    """获取模型配置"""
    return MODEL_CONFIGS.get(model_name, {})

def validate_vector_dimension(vector) -> bool:
    """验证向量维度"""
    if isinstance(vector, list):
        return len(vector) == VECTOR_DIMENSION
    elif hasattr(vector, 'shape'):
        return vector.shape[-1] == VECTOR_DIMENSION
    return False

if __name__ == '__main__':
    logger.info("🚀 Athena工作平台向量配置")
    logger.info(f"📏 标准向量维度: {VECTOR_DIMENSION}")
    logger.info(f"📚 向量集合数量: {len(COLLECTION_CONFIGS)}")
    logger.info(f"🤖 支持模型数量: {len(MODEL_CONFIGS)}")
