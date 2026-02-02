#!/usr/bin/env python3
"""
Athena工作平台 - 专利无效向量库构建器
构建专业专利无效分析向量库
"""

# Numpy兼容性导入
import logging
import os

# 添加项目路径
import sys
from typing import Any


from config.numpy_compatibility import random
from core.logging_config import setup_logging

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from core.vector_db.vector_db_manager import VectorDBManager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

class PatentInvalidBuilder:
    """专利无效向量库构建器"""
    
    def __init__(self):
        self.vector_db_manager = VectorDBManager()
        self.collection_name = 'patent_invalid_db'
    
    def create_patent_invalid_collection(self) -> bool:
        """创建专利无效集合"""
        logger.info(f"🏗️ 创建专利无效库: {self.collection_name}")
        
        # 创建集合 (1024维,适用于专利分析)
        success = self.vector_db_manager.create_collection(
            collection_name=self.collection_name,
            vector_size=1024,
            distance='Cosine'
        )
        
        if success:
            self.vector_db_manager.existing_collections.add(self.collection_name)
            logger.info(f"✅ 专利无效库创建成功: {self.collection_name}")
        else:
            logger.error(f"❌ 专利无效库创建失败: {self.collection_name}")
        
        return success
    
    def generate_sample_patent_invalid_data(self) -> list[dict[str, Any]]:
        """生成示例专利无效数据"""
        logger.info('📝 生成示例专利无效数据...')
        
        sample_data = [
            # 专利无效宣告案例
            {
                'id': 'invalid_case_001',
                'text': '宣告201810294048.1号发明专利权无效的决定:该专利因现有技术公开而被宣告无效。对比文件公开了相同的技术方案,权利要求1相对于对比文件缺乏新颖性。',
                'category': '无效决定',
                'type': 'decision',
                'domain': 'patent_invalid',
                'patent_number': '201810294048.1',
                'decision_date': '2023-05-15',
                'invalid_reason': '缺乏新颖性'
            },
            {
                'id': 'invalid_case_002', 
                'text': '宣告201710789543.2号发明专利权部分无效的决定:权利要求1-3不具备创造性,权利要求4-6维持有效。对比文件1结合对比文件2可以显而易见地得到权利要求1的技术方案。',
                'category': '无效决定',
                'type': 'decision', 
                'domain': 'patent_invalid',
                'patent_number': '201710789543.2',
                'decision_date': '2023-08-20',
                'invalid_reason': '缺乏创造性'
            },
            {
                'id': 'invalid_case_003',
                'text': '宣告201910876543.9号实用新型专利权无效:该专利技术方案已被多份对比文件公开,权利要求1-10均不具备新颖性,宣告全部无效。',
                'category': '无效决定',
                'type': 'decision',
                'domain': 'patent_invalid', 
                'patent_number': '201910876543.9',
                'decision_date': '2023-11-02',
                'invalid_reason': '缺乏新颖性'
            },
            # 专利无效理由
            {
                'id': 'invalid_reason_001',
                'text': '根据《专利法》第22条,发明和实用新型应当具备新颖性、创造性和实用性。如果权利要求的技术方案已经被现有技术公开,则不具备新颖性。',
                'category': '无效理由',
                'type': 'reason',
                'domain': 'patent_invalid',
                'legal_basis': '专利法第22条',
                'reason_type': '新颖性'
            },
            {
                'id': 'invalid_reason_002',
                'text': '创造性是指与现有技术相比,该发明具有突出的实质性特点和显著的进步,该实用新型具有实质性特点和进步。如果现有技术给出技术启示,则不具备创造性。',
                'category': '无效理由', 
                'type': 'reason',
                'domain': 'patent_invalid',
                'legal_basis': '专利法第22条',
                'reason_type': '创造性'
            },
            {
                'id': 'invalid_reason_003',
                'text': '根据《专利法》第5条,对违反法律、社会公德或者妨害公共利益的发明创造,不授予专利权。此为专利无效的法定理由之一。',
                'category': '无效理由',
                'type': 'reason',
                'domain': 'patent_invalid', 
                'legal_basis': '专利法第5条',
                'reason_type': '违法性'
            },
            # 专利无效策略
            {
                'id': 'invalid_strategy_001',
                'text': '专利无效策略:优先查找公开日期早于专利申请日的现有技术,特别是技术领域相同或相近的技术文献。重点分析权利要求的技术特征,寻找公开相同或等同技术方案的对比文件。',
                'category': '无效策略',
                'type': 'strategy', 
                'domain': 'patent_invalid',
                'strategy_type': '现有技术检索'
            },
            {
                'id': 'invalid_strategy_002',
                'text': '专利无效分析要点:明确无效宣告请求的理由和证据,详细分析权利要求的技术方案,确定其与现有技术的区别,论证是否具备专利法规定的新颖性和创造性。',
                'category': '无效策略',
                'type': 'strategy',
                'domain': 'patent_invalid',
                'strategy_type': '技术分析'
            },
            # 专利无效流程
            {
                'id': 'invalid_process_001',
                'text': '专利无效宣告流程:提交无效宣告请求书和相关证据材料,缴纳费用,专利复审委员会受理,通知专利权人,专利权人陈述意见,发出无效宣告请求受理通知书,进入审查程序。',
                'category': '无效流程', 
                'type': 'process',
                'domain': 'patent_invalid',
                'process_type': '请求流程'
            },
            {
                'id': 'invalid_process_002',
                'text': '专利无效审查要点:审查证据的充分性、技术对比的准确性、法律适用的正确性,确保无效宣告请求的事实清楚、理由充分、证据确凿。',
                'category': '无效流程',
                'type': 'process',
                'domain': 'patent_invalid',
                'process_type': '审查要点'
            }
        ]
        
        logger.info(f"✅ 生成了 {len(sample_data)} 条示例专利无效数据")
        return sample_data
    
    def generate_embedding_vector(self, text: str) -> list[float]:
        """生成嵌入向量 - 实际应用中应使用真实的embedding模型"""
        vector = random(1024).tolist()
        return vector
    
    def build_patent_invalid_db(self) -> bool:
        """构建专利无效数据库"""
        logger.info('🚀 开始构建专利无效库...')
        
        # 创建集合
        if not self.create_patent_invalid_collection():
            logger.error('❌ 专利无效库创建失败')
            return False
        
        # 生成示例数据
        sample_data = self.generate_sample_patent_invalid_data()
        
        # 准备插入数据
        vectors_data = []
        for i, item in enumerate(sample_data):
            vector = self.generate_embedding_vector(item['text'])
            
            vector_data = {
                'id': i,  # 使用整数ID
                'vector': vector,
                'payload': item  # 包含所有元数据
            }
            vectors_data.append(vector_data)
        
        logger.info(f"📦 准备插入 {len(vectors_data)} 个向量到专利无效库")
        
        # 批量插入向量
        success = self.vector_db_manager.batch_insert(
            collection_name=self.collection_name,
            vectors_data=vectors_data
        )
        
        if success:
            logger.info(f"✅ 专利无效库构建完成: {self.collection_name}")
            collection_info = self.vector_db_manager.get_collection_info(self.collection_name)
            if collection_info:
                points_count = collection_info.get('points_count', 0)
                logger.info(f"📊 集合状态: {points_count} 个向量点")
        else:
            logger.error('❌ 专利无效库构建失败')
        
        return success
    
    def test_patent_invalid_db(self) -> bool:
        """测试专利无效库功能"""
        logger.info('🧪 测试专利无效库功能...')
        
        if self.collection_name not in self.vector_db_manager.existing_collections:
            logger.error(f"❌ 集合 {self.collection_name} 不存在")
            return False
        
        # 生成测试向量
        test_vector = self.generate_embedding_vector('专利无效 新颖性 创造性')
        
        from core.vector_db.vector_db_manager import VectorQuery
        
        query = VectorQuery(
            vector=test_vector,
            text='专利无效 新颖性 创造性',
            limit=3,
            with_payload=True
        )
        
        results = self.vector_db_manager.search_in_collection(self.collection_name, query)
        
        logger.info(f"🔍 在专利无效库中找到 {len(results)} 个结果")
        
        for i, result in enumerate(results):
            logger.info(f"  {i+1}. 评分: {result.score:.3f}")
            logger.info(f"     内容: {result.payload.get('text', '')[:100]}...")
            logger.info(f"     类别: {result.payload.get('category', 'Unknown')}")
            logger.info(f"     类型: {result.payload.get('type', 'Unknown')}")
            print()
        
        return len(results) > 0

def main():
    """主函数 - 构建专利无效向量库"""
    logger.info('🏗️  开始构建专利无效向量库...')
    
    builder = PatentInvalidBuilder()
    
    logger.info(str('='*70))
    logger.info('🏗️  专利无效向量库构建器')
    logger.info(str('='*70))
    logger.info(f"📍 目标集合: {builder.collection_name}")
    logger.info("📊 向量维度: 1024 (专利分析)")
    logger.info("🎯 用途: 专利无效宣告分析、无效理由检索、案例参考")
    logger.info(str('='*70))
    
    # 构建专利无效库
    success = builder.build_patent_invalid_db()
    
    if success:
        logger.info("\n✅ 专利无效向量库构建成功!")
        
        # 测试功能
        test_success = builder.test_patent_invalid_db()
        if test_success:
            logger.info('✅ 功能测试通过!')
            logger.info(f"🔗 专利无效向量库已准备就绪: {builder.collection_name}")
        else:
            logger.info('❌ 功能测试失败')
    else:
        logger.info("\n❌ 专利无效向量库构建失败")
        return False
    
    logger.info(str("\n" + '='*70))
    logger.info('🎯 专利无效向量库已成功集成到Athena平台')
    logger.info('📋 现在可以进行专利无效分析、案例检索等专业操作')
    logger.info(str('='*70))
    
    return success

if __name__ == '__main__':
    success = main()
    if not success:
        exit(1)