#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向量服务
Vector Service
"""

import logging
from core.async_main import async_main
from typing import Any, Dict, List, Optional, Tuple, Callable, Union
import os
import sys
from datetime import datetime

from flask import Flask, jsonify, request

logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/health')
def health() -> Any:
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'service': 'vector-service',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/embed', methods=['POST'])
def create_embedding() -> Any:
    """创建向量嵌入"""
    try:
        data = request.get_json()
        text = data.get('text', '')

        if not text:
            return jsonify({'error': 'text is required'}), 400

        # 简化的向量生成模拟 (768维)
        import hashlib
        hash_object = hashlib.md5(text.encode(), usedforsecurity=False))
        hash_hex = hash_object.hexdigest()

        # 基于哈希生成模拟向量
        vector = []
        for i in range(0, len(hash_hex), 2):
            hex_pair = hash_hex[i:i+2]
            value = int(hex_pair, 16) / 255.0 - 0.5  # 归一化到[-0.5, 0.5]
            vector.extend([value] * 12)  # 重复填充到768维

        vector = vector[:768]  # 确保是768维

        result = {
            'text': text,
            'embedding': vector,
            'dimension': 768,
            'model': 'mock-bert-base',
            'timestamp': datetime.now().isoformat()
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/similarity', methods=['POST'])
def calculate_similarity() -> Any:
    """计算向量相似度"""
    try:
        data = request.get_json()
        text1 = data.get('text1', '')
        text2 = data.get('text2', '')

        if not text1 or not text2:
            return jsonify({'error': 'text1 and text2 are required'}), 400

        # 简化的相似度计算 (基于编辑距离)
        def simple_similarity(a, b) -> None:
            len_a, len_b = len(a), len(b)
            if len_a == 0: return 0.0 if len_b == 0 else 0.0
            if len_b == 0: return 0.0

            # 简化的相似度计算
            common_chars = sum(1 for char in set(a.lower()) if char in set(b.lower()))
            return common_chars / max(len_a, len_b)

        similarity = simple_similarity(text1, text2)

        result = {
            'text1': text1,
            'text2': text2,
            'similarity': similarity,
            'method': 'mock-cosine',
            'timestamp': datetime.now().isoformat()
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 8082))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'

    logger.info(f"🚀 启动向量服务 - {host}:{port}")
    app.run(host=host, port=port, debug=debug)