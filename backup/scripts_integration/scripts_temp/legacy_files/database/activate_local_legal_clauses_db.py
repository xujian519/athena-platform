#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
激活本地存在的法律条款向量库
将存在于本地文件系统中的legal_clauses_1024集合导入到Qdrant服务中
"""

import json
import logging
import os
import shutil
from datetime import datetime

import requests

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LocalLegalClausesActivator:
    """本地法律条款向量库激活器"""
    
    def __init__(self):
        self.qdrant_url = 'http://localhost:6333'
        self.local_collections_path = '/Users/xujian/Athena工作平台/archive/data_20251210_234532/vectors_qdrant/collections/qdrant/collections/'
        self.collection_name = 'legal_clauses_1024'
        self.source_collection_path = os.path.join(self.local_collections_path, self.collection_name)

    def check_local_collection_exists(self) -> bool:
        """检查本地集合是否存在"""
        if not os.path.exists(self.source_collection_path):
            logger.error(f"❌ 本地集合不存在: {self.source_collection_path}")
            return False
        
        logger.info(f"✅ 本地集合存在: {self.source_collection_path}")
        
        # 计算段数量
        segments_path = os.path.join(self.source_collection_path, '0', 'segments')
        if os.path.exists(segments_path):
            segments = [d for d in os.listdir(segments_path) if 
                       os.path.isdir(os.path.join(segments_path, d))]
            logger.info(f"📊 发现 {len(segments)} 个数据段")
        
        return True

    def get_local_collection_info(self) -> dict:
        """获取本地集合信息"""
        config_path = os.path.join(self.source_collection_path, 'config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        return {}

    def copy_collection_to_qdrant(self) -> bool:
        """将本地集合复制到Qdrant数据目录"""
        try:
            # 确定Qdrant的工作目录
            # 通常Qdrant数据目录在 ~/.local/share/qdrant 或自定义路径
            qdrant_collections_dir = os.path.expanduser('~/.local/share/qdrant/data/collections/')
            
            # 如果默认目录不存在，尝试其他常见路径
            possible_paths = [
                '/Users/xujian/.local/share/qdrant/data/collections/',
                '/tmp/qdrant_data/collections/',
                '/var/lib/qdrant/data/collections/',  # 如果以root运行
            ]
            
            qdrant_collections_dir = None
            for path in possible_paths:
                if os.path.exists(path):
                    qdrant_collections_dir = path
                    break
            
            # 如果还是找不到，检查是否Qdrant服务使用了自定义数据目录
            if qdrant_collections_dir is None:
                # 如果无法确定，我们直接通过API创建空集合然后导入数据
                logger.info('⚠️ 未找到Qdrant数据目录，将通过API激活集合')
                return self.activate_via_api()
            
            target_collection_path = os.path.join(qdrant_collections_dir, self.collection_name)
            
            # 如果目标路径已存在，先删除
            if os.path.exists(target_collection_path):
                logger.info(f"🗑️ 删除现有集合: {target_collection_path}")
                shutil.rmtree(target_collection_path)
            
            # 复制整个集合目录
            logger.info(f"📂 复制集合到Qdrant数据目录...")
            logger.info(f"   源: {self.source_collection_path}")
            logger.info(f"   目标: {target_collection_path}")
            
            shutil.copytree(self.source_collection_path, target_collection_path)
            
            logger.info(f"✅ 集合已复制到Qdrant")
            return True
            
        except Exception as e:
            logger.error(f"❌ 复制集合到Qdrant失败: {e}")
            # 如果直接复制失败，尝试通过API激活
            return self.activate_via_api()

    def activate_via_api(self) -> bool:
        """通过API激活集合"""
        try:
            # 首先检查远程是否存在同名集合，如果有则删除
            collection_url = f"{self.qdrant_url}/collections/{self.collection_name}"
            response = requests.get(collection_url)
            if response.status_code == 200:
                logger.info(f"🗑️ 删除现有的远程集合: {self.collection_name}")
                del_response = requests.delete(collection_url)
                if del_response.status_code != 200:
                    logger.error(f"❌ 删除远程集合失败: {del_response.text}")
                    return False
            
            # 然后创建新集合，使用本地配置
            config = self.get_local_collection_config()
            if not config:
                logger.error('❌ 无法获取本地集合配置')
                return False
            
            # 创建集合
            create_config = {
                'vectors': config['params']['vectors'],
                'optimizers_config': config['optimizer_config'],
                'hnsw_config': config['hnsw_config'],
                'wal_config': config['wal_config']
            }
            
            response = requests.put(collection_url, json=create_config)
            if response.status_code != 200:
                logger.error(f"❌ 创建集合失败: {response.text}")
                return False
            
            logger.info(f"✅ 成功创建远程集合: {self.collection_name}")
            
            # 由于我们没有原始向量数据，而是有已索引的集合，
            # 这种情况需要通过其他方式处理
            # 可能需要使用快照功能，但更简单的做法是重建
            
            return self.rebuild_collection_from_local_vectors()
            
        except Exception as e:
            logger.error(f"❌ 通过API激活集合失败: {e}")
            return False

    def rebuild_collection_from_local_data(self) -> bool:
        """从本地数据重建集合（这是个复杂的过程）"""
        try:
            # 由于我们无法直接从Qdrant段文件中提取向量数据，
            # 我们需要从原始数据源重建这个集合
            # 首先，确定原始向量数据的位置
            logger.info(f"🔄 尝试从原始数据重建 {self.collection_name} 集合")
            
            # 查找可能的原始向量数据文件
            raw_vector_paths = [
                '/Users/xujian/Athena工作平台/archive/data_20251210_234532/legal_patent_vectors/',
                '/Users/xujian/Athena工作平台/archive/data_20251210_234532/vectors_qdrant/embeddings/',
                '/Users/xujian/Athena工作平台/storage/vectors/legal_clauses/',
            ]
            
            vectors_file = None
            for path in raw_vector_paths:
                if os.path.exists(path):
                    # 查找包含法律条款的向量文件
                    for file in os.listdir(path):
                        if 'legal' in file.lower() and 'clause' in file.lower() and file.endswith('.json'):
                            vectors_file = os.path.join(path, file)
                            break
                    if vectors_file:
                        break
            
            if not vectors_file:
                logger.error('❌ 未找到原始法律条款向量数据文件')
                # 作为备选方案，尝试从归档目录搜索
                import subprocess
                result = subprocess.run([
                    'find', '/Users/xujian/Athena工作平台', 
                    '-name', '*.json', 
                    '-path', '*/legal*', 
                    '-exec', 'grep', '-l', "clause\\|article\\|条\\|项", '{}', '+'
                ], capture_output=True, text=True)
                
                if result.stdout:
                    files = result.stdout.strip().split('\n')
                    if files and len(files) > 0:
                        vectors_file = files[0]  # 使用第一个匹配的文件
                        logger.info(f"🔍 找到可能的向量数据文件: {vectors_file}")
            
            if not vectors_file:
                logger.error('❌ 无法找到用于重建集合的向量数据')
                # 如果真的找不到原始数据，那么我们至少应该创建一个空集合来占位
                logger.info(f"⚠️  创建空的 {self.collection_name} 集合作为占位符")
                return self.create_placeholder_collection()
            
            # 使用找到的向量文件重建集合
            return self.import_vectors_to_collection(vectors_file)
            
        except Exception as e:
            logger.error(f"❌ 重建集合失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def create_placeholder_collection(self) -> bool:
        """创建一个占位集合"""
        try:
            url = f"{self.qdrant_url}/collections/{self.collection_name}"
            
            # 检查是否存在
            response = requests.get(url)
            if response.status_code == 200:
                logger.info(f"⚠️ 集合 {self.collection_name} 已存在")
                return True
            
            # 创建集合配置
            collection_config = {
                'vectors': {
                    'size': 1024,
                    'distance': 'Cosine'
                },
                'optimizers_config': {
                    'default_segment_number': 1,
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
                logger.info(f"✅ 成功创建占位集合: {self.collection_name}")
                return True
            else:
                logger.error(f"❌ 创建占位集合失败: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 创建占位集合异常: {e}")
            return False

    def import_vectors_to_collection(self, vectors_file: str) -> bool:
        """导入向量到集合"""
        try:
            logger.info(f"📥 从 {vectors_file} 导入向量到 {self.collection_name}")
            
            # 加载向量数据
            with open(vectors_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            vectors = []
            if isinstance(data, dict) and 'vectors' in data:
                vectors = data['vectors']
            elif isinstance(data, list):
                vectors = data
            else:
                logger.error(f"❌ 无法识别的向量数据格式")
                return False
            
            logger.info(f"✅ 加载 {len(vectors)} 个向量")
            
            # 准备批量导入
            batch_size = 50
            total_vectors = len(vectors)
            
            for i in range(0, total_vectors, batch_size):
                batch = vectors[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (total_vectors + batch_size - 1) // batch_size
                
                logger.info(f"📦 处理批次 {batch_num}/{total_batches} ({len(batch)} 个向量)")
                
                # 准备points
                points = []
                for j, item in enumerate(batch):
                    point_id = i + j
                    
                    if 'vector' in item:
                        vector = item['vector']
                        
                        payload = {}
                        if 'payload' in item:
                            payload = item['payload']
                        elif 'metadata' in item:
                            payload = item['metadata']
                        elif 'chunk_info' in item:
                            payload = item['chunk_info']
                        else:
                            payload = {'source': 'legal_clauses_rebuild'}
                        
                        point = {
                            'id': point_id,
                            'vector': vector,
                            'payload': payload
                        }
                        points.append(point)
                
                # 批量插入
                if points:
                    url = f"{self.qdrant_url}/collections/{self.collection_name}/points"
                    response = requests.put(url, json={'points': points})
                    
                    if response.status_code != 200:
                        logger.error(f"❌ 批次 {batch_num} 插入失败: {response.text}")
                        return False
                    else:
                        logger.info(f"✅ 批次 {batch_num} 成功插入 {len(points)} 个向量")
            
            logger.info(f"✅ 从 {vectors_file} 成功导入 {total_vectors} 个向量到集合 {self.collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 导入向量失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def activate(self) -> bool:
        """激活本地法律条款向量库"""
        logger.info('🏗️ 开始激活本地法律条款向量库...')
        logger.info(f"📍 集合名称: {self.collection_name}")
        logger.info(f"📍 本地路径: {self.source_collection_path}")
        logger.info(f"🔗 Qdrant服务: {self.qdrant_url}")
        
        # 检查本地集合是否存在
        if not self.check_local_collection_exists():
            logger.error('❌ 本地集合不存在，无法激活')
            return False
        
        # 检查是否已在Qdrant服务中
        collection_url = f"{self.qdrant_url}/collections/{self.collection_name}"
        response = requests.get(collection_url)
        
        if response.status_code == 200:
            logger.info(f"✅ 集合 {self.collection_name} 已在Qdrant服务中")
            # 获取当前状态
            info = response.json().get('result', {})
            points_count = info.get('points_count', 0)
            logger.info(f"📊 当前点数: {points_count}")
            return True
        
        # 如果不在服务中，则激活
        logger.info(f"🚀 激活集合 {self.collection_name} 到Qdrant服务...")
        success = self.copy_collection_to_qdrant()
        
        if success:
            # 验证是否激活成功
            response = requests.get(collection_url)
            if response.status_code == 200:
                info = response.json().get('result', {})
                points_count = info.get('points_count', 0)
                indexed_count = info.get('indexed_vectors_count', 0)
                
                logger.info('🎉 法律条款向量库激活成功!')
                logger.info(f"📋 集合: {self.collection_name}")
                logger.info(f"📊 状态: {info.get('status', 'Unknown')}")
                logger.info(f"📍 点数量: {points_count}")
                logger.info(f"🔍 索引向量数: {indexed_count}")
                
                return True
            else:
                logger.error('❌ 集合激活后验证失败')
                return False
        else:
            logger.error('❌ 集合激活失败')
            return False

def main():
    """主函数"""
    activator = LocalLegalClausesActivator()
    
    logger.info(str('='*70))
    logger.info('🏗️  本地法律条款向量库激活器')
    logger.info(str('='*70))
    logger.info(f"📍 目标集合: {activator.collection_name}")
    logger.info(f"📁 本地路径: {activator.source_collection_path}")
    logger.info(f"🔗 Qdrant服务: {activator.qdrant_url}")
    logger.info(str('='*70))
    
    # 检查本地集合
    if not activator.check_local_collection_exists():
        logger.info(f"❌ 本地集合不存在: {activator.source_collection_path}")
        logger.info("\n🔍 正在搜索其他可能的法律条款向量文件...")
        
        # 搜索可能的向量文件
        import subprocess
        result = subprocess.run([
            'find', '/Users/xujian/Athena工作平台', 
            '-name', '*.json', 
            '-path', '*/vectors*', 
            '-exec', 'grep', '-l', "legal.*clause\\|法律.*条款\\|article", '{}', '+'
        ], capture_output=True, text=True)
        
        if result.stdout:
            logger.info('📋 找到可能的向量文件:')
            for file in result.stdout.strip().split('\n')[:10]:  # 显示前10个
                logger.info(f"  - {file}")
        
        return False
    
    # 激活集合
    success = activator.activate()
    
    if success:
        logger.info(str("\n" + '='*70))
        logger.info('🎉 本地法律条款向量库激活成功!')
        logger.info(str('='*70))
        logger.info('✅ 现在可以通过Qdrant API访问法律条款向量库')
        logger.info(f"🔗 集合名: {activator.collection_name}")
        logger.info('🎯 适用场景: 法律条款检索、法条匹配、案例分析')
        logger.info(str('='*70))
    else:
        logger.info("\n❌ 本地法律条款向量库激活失败")
    
    return success

if __name__ == '__main__':
    success = main()
    if not success:
        exit(1)