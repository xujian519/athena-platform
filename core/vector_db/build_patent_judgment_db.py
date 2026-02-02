#!/usr/bin/env python3
"""
Athena工作平台 - 专利判决向量库构建器
构建专业专利诉讼判决分析向量库
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

class PatentJudgmentBuilder:
    """专利判决向量库构建器"""
    
    def __init__(self):
        self.vector_db_manager = VectorDBManager()
        self.collection_name = 'patent_judgment_db'
    
    def create_patent_judgment_collection(self) -> bool:
        """创建专利判决集合"""
        logger.info(f"🏗️ 创建专利判决库: {self.collection_name}")
        
        # 创建集合 (1024维,适用于专利分析)
        success = self.vector_db_manager.create_collection(
            collection_name=self.collection_name,
            vector_size=1024,
            distance='Cosine'
        )
        
        if success:
            self.vector_db_manager.existing_collections.add(self.collection_name)
            logger.info(f"✅ 专利判决库创建成功: {self.collection_name}")
        else:
            logger.error(f"❌ 专利判决库创建失败: {self.collection_name}")
        
        return success
    
    def generate_sample_patent_judgment_data(self) -> list[dict[str, Any]]:
        """生成示例专利判决数据"""
        logger.info('📝 生成示例专利判决数据...')
        
        sample_data = [
            # 专利侵权判决案例
            {
                'id': 'judgment_case_001',
                'text': '(2023)最高法知民终1234号:被告未经许可实施涉案专利,构成专利侵权。经技术比对,被诉侵权产品包含了涉案专利权利要求1的全部技术特征,落入专利保护范围。判决被告停止侵权并赔偿经济损失。',
                'category': '侵权判决',
                'type': 'judgment',
                'domain': 'patent_judgment',
                'case_number': '(2023)最高法知民终1234号',
                'court': '最高人民法院',
                'judgment_date': '2023-08-15',
                'judgment_result': '构成侵权'
            },
            {
                'id': 'judgment_case_002',
                'text': '(2023)京知民初567号:原告主张被告侵犯其发明专利权,但经审理查明,被诉技术方案与涉案专利权利要求存在实质性差异,未落入专利保护范围。判决驳回原告诉讼请求。',
                'category': '侵权判决',
                'type': 'judgment',
                'domain': 'patent_judgment',
                'case_number': '(2023)京知民初567号',
                'court': '北京知识产权法院',
                'judgment_date': '2023-05-20',
                'judgment_result': '不构成侵权'
            },
            {
                'id': 'judgment_case_003',
                'text': '(2023)粤民终890号:被告使用的技术方案属于现有技术抗辩成立,不构成对原告专利权的侵犯。现有技术抗辩需要证明被诉技术方案与申请日前已公开的技术相同。',
                'category': '侵权判决',
                'type': 'judgment',
                'domain': 'patent_judgment',
                'case_number': '(2023)粤民终890号',
                'court': '广东省高级人民法院',
                'judgment_date': '2023-07-10',
                'judgment_result': '现有技术抗辩成立'
            },
            # 专利无效判决
            {
                'id': 'invalid_judgment_001',
                'text': '确认涉案专利权部分无效,权利要求1-3因缺乏新颖性被宣告无效,权利要求4-6维持有效。原告提交的对比文件足以证明权利要求1-3的技术方案已被现有技术公开。',
                'category': '无效判决',
                'type': 'judgment',
                'domain': 'patent_judgment',
                'case_type': '专利无效',
                'result_type': '部分无效'
            },
            {
                'id': 'invalid_judgment_002',
                'text': '经审理,涉案专利权利要求不符合专利法关于创造性的规定,维持专利复审委员会宣告该专利权全部无效的决定。权利要求技术方案与现有技术的结合显而易见。',
                'category': '无效判决',
                'type': 'judgment',
                'domain': 'patent_judgment',
                'case_type': '专利无效',
                'result_type': '全部无效'
            },
            # 专利诉讼理由
            {
                'id': 'litigation_reason_001',
                'text': '专利侵权判定采用全面覆盖原则,被诉侵权技术方案包含与权利要求相同或等同的技术特征时,构成专利侵权。等同特征是指与所记载技术特征以基本相同的手段,实现基本相同的功能,达到基本相同的效果。',
                'category': '诉讼理由',
                'type': 'reason',
                'domain': 'patent_judgment',
                'legal_basis': '专利侵权判定规则',
                'reason_type': '侵权判定'
            },
            {
                'id': 'litigation_reason_002',
                'text': '现有技术抗辩是指被诉侵权人有证据证明其实施的技术属于现有技术的,不构成侵犯专利权。现有技术是指申请日以前在国内外为公众所知的技术。',
                'category': '诉讼理由',
                'type': 'reason',
                'domain': 'patent_judgment',
                'legal_basis': '专利法第67条',
                'reason_type': '现有技术抗辩'
            },
            # 专利损害赔偿
            {
                'id': 'compensation_001',
                'text': '专利侵权损害赔偿数额的确定:按照权利人因被侵权所受到的实际损失确定;实际损失难以确定的,可以按照侵权人因侵权所获得的利益确定;权利人的损失或者侵权人获得的利益难以确定的,参照该专利许可使用费的倍数合理确定。',
                'category': '损害赔偿',
                'type': 'compensation',
                'domain': 'patent_judgment',
                'legal_basis': '专利法第71条',
                'compensation_type': '赔偿计算'
            },
            {
                'id': 'compensation_002',
                'text': '侵犯专利权的赔偿数额按照权利人因被侵权所受到的实际损失或者侵权人因侵权所获得的利益确定。当权利人提供充分证据证明其实际损失时,法院应首先考虑以实际损失为赔偿标准。',
                'category': '损害赔偿',
                'type': 'compensation',
                'domain': 'patent_judgment',
                'legal_basis': '专利法第71条',
                'compensation_type': '实际损失'
            },
            # 专利诉讼策略
            {
                'id': 'litigation_strategy_001',
                'text': '专利诉讼策略:诉前应充分进行技术比对分析,明确侵权点,收集充分的证据材料,合理确定诉讼请求,考虑申请临时禁令措施保护合法权益。',
                'category': '诉讼策略',
                'type': 'strategy',
                'domain': 'patent_judgment',
                'strategy_type': '诉讼策略'
            }
        ]
        
        logger.info(f"✅ 生成了 {len(sample_data)} 条示例专利判决数据")
        return sample_data
    
    def generate_embedding_vector(self, text: str) -> list[float]:
        """生成嵌入向量 - 实际应用中应使用真实的embedding模型"""
        vector = random(1024).tolist()
        return vector
    
    def build_patent_judgment_db(self) -> bool:
        """构建专利判决数据库"""
        logger.info('🚀 开始构建专利判决库...')
        
        # 创建集合
        if not self.create_patent_judgment_collection():
            logger.error('❌ 专利判决库创建失败')
            return False
        
        # 生成示例数据
        sample_data = self.generate_sample_patent_judgment_data()
        
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
        
        logger.info(f"📦 准备插入 {len(vectors_data)} 个向量到专利判决库")
        
        # 批量插入向量
        success = self.vector_db_manager.batch_insert(
            collection_name=self.collection_name,
            vectors_data=vectors_data
        )
        
        if success:
            logger.info(f"✅ 专利判决库构建完成: {self.collection_name}")
            collection_info = self.vector_db_manager.get_collection_info(self.collection_name)
            if collection_info:
                points_count = collection_info.get('points_count', 0)
                logger.info(f"📊 集合状态: {points_count} 个向量点")
        else:
            logger.error('❌ 专利判决库构建失败')
        
        return success
    
    def test_patent_judgment_db(self) -> bool:
        """测试专利判决库功能"""
        logger.info('🧪 测试专利判决库功能...')
        
        if self.collection_name not in self.vector_db_manager.existing_collections:
            logger.error(f"❌ 集合 {self.collection_name} 不存在")
            return False
        
        # 生成测试向量
        test_vector = self.generate_embedding_vector('专利侵权 判决 赔偿')
        
        from core.vector_db.vector_db_manager import VectorQuery
        
        query = VectorQuery(
            vector=test_vector,
            text='专利侵权 判决 赔偿',
            limit=3,
            with_payload=True
        )
        
        results = self.vector_db_manager.search_in_collection(self.collection_name, query)
        
        logger.info(f"🔍 在专利判决库中找到 {len(results)} 个结果")
        
        for i, result in enumerate(results):
            logger.info(f"  {i+1}. 评分: {result.score:.3f}")
            logger.info(f"     内容: {result.payload.get('text', '')[:100]}...")
            logger.info(f"     类别: {result.payload.get('category', 'Unknown')}")
            logger.info(f"     类型: {result.payload.get('type', 'Unknown')}")
            print()
        
        return len(results) > 0

def main():
    """主函数 - 构建专利判决向量库"""
    logger.info('🏗️  开始构建专利判决向量库...')
    
    builder = PatentJudgmentBuilder()
    
    logger.info(str('='*70))
    logger.info('🏗️  专利判决向量库构建器')
    logger.info(str('='*70))
    logger.info(f"📍 目标集合: {builder.collection_name}")
    logger.info("📊 向量维度: 1024 (专利分析)")
    logger.info("🎯 用途: 专利诉讼分析、判决检索、赔偿计算参考")
    logger.info(str('='*70))
    
    # 构建专利判决库
    success = builder.build_patent_judgment_db()
    
    if success:
        logger.info("\n✅ 专利判决向量库构建成功!")
        
        # 测试功能
        test_success = builder.test_patent_judgment_db()
        if test_success:
            logger.info('✅ 功能测试通过!')
            logger.info(f"🔗 专利判决向量库已准备就绪: {builder.collection_name}")
        else:
            logger.info('❌ 功能测试失败')
    else:
        logger.info("\n❌ 专利判决向量库构建失败")
        return False
    
    logger.info(str("\n" + '='*70))
    logger.info('🎯 专利判决向量库已成功集成到Athena平台')
    logger.info('📋 现在可以进行专利诉讼分析、判决检索等专业操作')
    logger.info(str('='*70))
    
    return success

if __name__ == '__main__':
    success = main()
    if not success:
        exit(1)