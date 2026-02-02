#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向量库功能测试脚本
测试所有激活的向量库是否正常工作
"""

# Numpy兼容性导入
from config.numpy_compatibility import array, zeros, ones, random, mean, sum, dot
import json
import logging
from typing import Any, Dict

import numpy as np
import requests

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorDBTester:
    """向量库测试器"""
    
    def __init__(self, qdrant_url: str = 'http://localhost:6333'):
        self.qdrant_url = qdrant_url

    def create_random_vector(self, dimension: int) -> list:
        """创建一个随机向量用于测试"""
        return random(dimension).tolist()

    def test_collection_exists(self, collection_name: str) -> bool:
        """测试集合是否存在"""
        try:
            url = f"{self.qdrant_url}/collections/{collection_name}"
            response = requests.get(url)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"❌ 检查集合 {collection_name} 时出错: {e}")
            return False

    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """获取集合信息"""
        try:
            url = f"{self.qdrant_url}/collections/{collection_name}"
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            logger.error(f"❌ 获取集合 {collection_name} 信息时出错: {e}")
            return {}

    def test_vector_search(self, collection_name: str, dimension: int) -> bool:
        """测试向量搜索功能"""
        try:
            # 创建一个随机测试向量
            test_vector = self.create_random_vector(dimension)
            
            url = f"{self.qdrant_url}/collections/{collection_name}/points/search"
            payload = {
                'vector': test_vector,
                'limit': 1
            }
            
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ 搜索测试成功，返回 {len(result.get('result', []))} 个结果")
                return True
            else:
                logger.error(f"❌ 搜索测试失败: {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ 搜索测试异常: {e}")
            return False

    def test_all_collections(self):
        """测试所有集合"""
        collections = [
            {'name': 'patent_rules_unified_1024', 'dimension': 1024},
            {'name': 'legal_vector_db', 'dimension': 1024},
            {'name': 'ai_technical_terms_vector_db', 'dimension': 384}
        ]
        
        logger.info(str('='*80))
        logger.info('🧪 向量库功能测试报告')
        logger.info(str('='*80))
        
        all_tests_passed = True
        
        for collection in collections:
            collection_name = collection['name']
            dimension = collection['dimension']
            
            logger.info(f"\n📋 测试集合: {collection_name}")
            logger.info(str('-' * 50))
            
            # 测试集合是否存在
            exists = self.test_collection_exists(collection_name)
            logger.info(f"🔍 集合存在性: {'✅' if exists else '❌'}")
            
            if not exists:
                all_tests_passed = False
                logger.info(f"   ❌ 集合 {collection_name} 不存在")
                continue
            
            # 获取集合信息
            info = self.get_collection_info(collection_name)
            if info:
                points_count = info.get('result', {}).get('points_count', 0)
                status = info.get('result', {}).get('status', 'unknown')
                vector_size = info.get('result', {}).get('config', {}).get('params', {}).get('vectors', {}).get('size', 0)
                
                logger.info(f"📊 点数量: {points_count}")
                logger.info(f"📈 状态: {status}")
                logger.info(f"📐 向量维度: {vector_size}")
            
            # 测试向量搜索功能
            search_ok = self.test_vector_search(collection_name, dimension)
            logger.info(f"🔍 搜索功能: {'✅' if search_ok else '❌'}")
            
            if not search_ok:
                all_tests_passed = False
        
        logger.info(str("\n" + '='*80))
        if all_tests_passed:
            logger.info('🎉 所有向量库测试通过！')
            logger.info('✅ 专利规则向量库 - 可用于专利检索分析')
            logger.info('✅ 法律向量库 - 可用于法律文档检索')
            logger.info('✅ AI术语向量库 - 可用于技术术语匹配')
        else:
            logger.info('❌ 部分向量库测试未通过')
        logger.info(str('='*80))
        
        return all_tests_passed

def main():
    logger.info('🚀 开始向量库功能测试...')
    
    tester = VectorDBTester()
    success = tester.test_all_collections()
    
    if success:
        logger.info('✅ 所有向量库均已成功激活并可正常工作')
    else:
        logger.error('❌ 部分向量库存在问题')
    
    return success

if __name__ == '__main__':
    main()