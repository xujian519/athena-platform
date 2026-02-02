#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
激活AI术语向量库到Qdrant
该脚本将AI术语向量数据导入到Qdrant服务中
"""

import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List

import requests

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AITermVectorActivator:
    """AI术语向量激活器"""

    def __init__(self):
        self.qdrant_url = 'http://localhost:6333'
        self.collection_name = 'ai_technical_terms_vector_db'  # AI术语向量库集合名称
        self.batch_size = 50  # 批量导入大小

    def load_ai_term_vectors(self, vectors_file: str) -> Dict[str, Any]:
        """加载AI术语向量数据"""
        try:
            with open(vectors_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            logger.info(f"✅ 加载AI术语向量文件: {vectors_file}")
            
            # 检查数据格式
            if 'vectors' in data:
                vectors = data['vectors']
                logger.info(f"   - 向量数量: {len(vectors)}")
                logger.info(f"   - 向量维度: {data['metadata'].get('dimension', 'Unknown')}")
                logger.info(f"   - 模型: {data['metadata'].get('model', 'Unknown')}")
            else:
                logger.error('❌ 文件中未找到向量数据')
                return {}

            return data

        except Exception as e:
            logger.error(f"❌ 加载AI术语向量文件失败: {e}")
            return {}

    def create_collection(self) -> bool:
        """创建Qdrant集合"""
        try:
            url = f"{self.qdrant_url}/collections/{self.collection_name}"
            
            # 检查集合是否已存在
            response = requests.get(url)
            if response.status_code == 200:
                logger.info(f"⚠️ 集合 {self.collection_name} 已存在，将清空后重新创建")
                # 删除现有集合
                delete_response = requests.delete(url)
                if delete_response.status_code != 200:
                    logger.error(f"❌ 删除现有集合失败: {delete_response.text}")
                    return False
            
            # 获取向量维度，如果可能的话
            # 由于维度是384，需要动态创建
            collection_config = {
                'vectors': {
                    'size': 384,  # 根据文件元数据，这个是384维
                    'distance': 'Cosine'
                },
                'optimizers_config': {
                    'default_segment_number': 2,
                    'indexing_threshold': 20000,
                    'flush_interval_sec': 5
                },
                'hnsw_config': {
                    'm': 16,
                    'ef_construct': 100
                }
            }
            
            response = requests.put(url, json=collection_config)
            
            if response.status_code == 200:
                logger.info(f"✅ 成功创建集合: {self.collection_name}")
                return True
            else:
                logger.error(f"❌ 创建集合失败: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 创建集合异常: {e}")
            return False

    def import_vectors(self, vectors_data: Dict[str, Any]) -> bool:
        """批量导入向量到Qdrant"""
        vectors = vectors_data.get('vectors', [])
        if not vectors:
            logger.error('❌ 向量数据为空')
            return False

        total_vectors = len(vectors)
        logger.info(f"🚀 开始导入AI术语向量到集合: {self.collection_name}")
        logger.info(f"   - 总向量数: {total_vectors}")
        logger.info(f"   - 批次大小: {self.batch_size}")

        success_count = 0
        error_count = 0

        # 分批导入
        for i in range(0, total_vectors, self.batch_size):
            batch_vectors = vectors[i:i + self.batch_size]
            batch_num = i // self.batch_size + 1
            total_batches = (total_vectors + self.batch_size - 1) // self.batch_size

            logger.info(f"📦 处理批次 {batch_num}/{total_batches} ({len(batch_vectors)} 个向量)")

            # 准备Qdrant points
            points = []
            for j, vector_data in enumerate(batch_vectors):
                # 使用原始ID或创建新ID
                if 'id' in vector_data:
                    point_id = vector_data['id']
                    # 如果ID是字符串，需要转换为数字或使用随机ID
                    if isinstance(point_id, str):
                        # 使用哈希将字符串ID转换为整数
                        point_id = abs(hash(point_id)) % (10**9)  # 限制在合理范围内
                else:
                    point_id = i + j  # 使用递增的整数ID

                if 'vector' not in vector_data:
                    logger.error(f"❌ 向量数据缺少vector字段: {vector_data.keys()}")
                    continue

                vector = vector_data['vector']
                
                # 处理payload
                payload = {}
                if 'text' in vector_data:
                    payload['text'] = vector_data['text']
                if 'term' in vector_data:
                    payload['term'] = vector_data['term']
                if 'definition' in vector_data:
                    payload['definition'] = vector_data['definition']
                if 'category' in vector_data:
                    payload['category'] = vector_data['category']
                if 'domain' in vector_data:
                    payload['domain'] = vector_data['domain']
                
                # 默认添加AI术语相关标识
                payload['domain'] = payload.get('domain', 'ai_technical_terms')
                payload['source'] = 'ai_terminology_db'

                point = {
                    'id': point_id,
                    'vector': vector,
                    'payload': payload
                }
                points.append(point)

            if not points:  # 如果没有有效点，跳过这个批次
                continue

            # 执行批量插入
            try:
                url = f"{self.qdrant_url}/collections/{self.collection_name}/points"
                headers = {'Content-Type': 'application/json'}

                payload = {
                    'points': points
                }

                response = requests.put(url, json=payload, headers=headers)

                if response.status_code == 200:
                    success_count += len(points)
                    logger.info(f"✅ 批次 {batch_num} 导入成功 ({len(points)} 个向量)")
                else:
                    error_count += len(points)
                    logger.error(f"❌ 批次 {batch_num} 导入失败: {response.status_code}")
                    logger.error(f"响应内容: {response.text}")

            except Exception as e:
                error_count += len(points)
                logger.error(f"❌ 批次 {batch_num} 导入异常: {e}")

            # 短暂休息避免过载
            time.sleep(0.1)

        # 输出结果
        logger.info('='*60)
        logger.info('📊 AI术语向量导入完成统计')
        logger.info('='*60)
        logger.info(f"✅ 成功导入: {success_count} 个向量")
        logger.info(f"❌ 导入失败: {error_count} 个向量")
        if total_vectors > 0:
            logger.info(f"📈 成功率: {(success_count/total_vectors*100):.1f}%")

        return error_count == 0

    def get_collection_info(self) -> Dict[str, Any]:
        """获取集合信息"""
        try:
            url = f"{self.qdrant_url}/collections/{self.collection_name}"
            response = requests.get(url)
            if response.status_code == 200:
                return response.json().get('result', {})
            else:
                return {}
        except Exception as e:
            logger.error(f"❌ 获取集合信息失败: {e}")
            return {}

    def activate_ai_terms_vector_db(self, vectors_file: str) -> bool:
        """激活AI术语向量库"""
        logger.info('🏗️ 开始激活AI术语向量库流程')
        
        # 加载向量数据
        logger.info(f"📥 加载向量数据: {vectors_file}")
        vectors_data = self.load_ai_term_vectors(vectors_file)
        if not vectors_data or 'vectors' not in vectors_data:
            logger.error('❌ 无法加载有效的AI术语向量数据')
            return False

        # 创建集合
        logger.info('🔨 创建Qdrant集合')
        if not self.create_collection():
            logger.error('❌ 创建集合失败')
            return False

        # 导入向量
        logger.info('📥 开始导入向量')
        success = self.import_vectors(vectors_data)

        # 输出最终状态
        if success:
            collection_info = self.get_collection_info()
            logger.info('='*60)
            logger.info('🎉 AI术语向量库激活成功!')
            logger.info('='*60)
            logger.info(f"📋 集合名称: {self.collection_name}")
            logger.info(f"📊 状态: {collection_info.get('status', 'Unknown')}")
            logger.info(f"📍 点数量: {collection_info.get('points_count', 0)}")
            logger.info(f"🔗 服务地址: {self.qdrant_url}")
            logger.info('='*60)
        else:
            logger.error('❌ AI术语向量库激活失败')

        return success

def main():
    """主函数"""
    activator = AITermVectorActivator()

    logger.info(str('='*70))
    logger.info('🏗️  AI术语向量库激活器')
    logger.info(str('='*70))
    logger.info(f"📍 目标集合: {activator.collection_name}")
    logger.info(f"🌐 Qdrant服务: {activator.qdrant_url}")
    logger.info(f"📊 向量维度: 384 (Cosine距离)")
    logger.info(f"🔄 此操作将清空现有同名集合")
    logger.info(str('='*70))

    # 查找AI术语向量文件
    ai_term_file = '/Users/xujian/Athena工作平台/archive/data_20251210_234532/vectors_qdrant/embeddings/ai_terminology_vectors_20251205_104422.json'
    
    if not os.path.exists(ai_term_file):
        logger.error(f"❌ AI术语向量文件不存在: {ai_term_file}")
        return False

    logger.info(f"\n📁 AI术语向量文件: {ai_term_file}")

    # 检查文件大小
    file_size = os.path.getsize(ai_term_file)
    logger.info(f"💾 文件大小: {file_size:,} 字节 ({file_size/1024/1024:.1f} MB)")

    logger.info("\n🚀 自动激活模式 - 开始激活AI术语向量库...")

    # 激活AI术语向量库
    success = activator.activate_ai_terms_vector_db(ai_term_file)

    if success:
        logger.info(str("\n" + '='*70))
        logger.info('🎉 AI术语向量库激活成功！')
        logger.info(str('='*70))
        logger.info('✅ 现在可以使用AI术语向量库进行检索')
        logger.info('🔗 集合名: ai_technical_terms_vector_db')
        logger.info('🎯 适用场景: AI技术术语匹配、专业词汇检索、知识图谱构建')
        logger.info(str('='*70))
    else:
        logger.info("\n❌ AI术语向量库激活失败，请检查错误日志")

    return success

if __name__ == '__main__':
    main()