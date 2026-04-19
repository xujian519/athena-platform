#!/usr/bin/env python3
from __future__ import annotations
"""
Athena工作平台 - 专利复审向量库构建器
构建专业专利复审分析向量库
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

class PatentReviewBuilder:
    """专利复审向量库构建器"""

    def __init__(self):
        self.vector_db_manager = VectorDBManager()
        self.collection_name = 'patent_review_db'

    def create_patent_review_collection(self) -> bool:
        """创建专利复审集合"""
        logger.info(f"🏗️ 创建专利复审库: {self.collection_name}")

        # 创建集合 (1024维,适用于专利分析)
        success = self.vector_db_manager.create_collection(
            collection_name=self.collection_name,
            vector_size=1024,
            distance='Cosine'
        )

        if success:
            self.vector_db_manager.existing_collections.add(self.collection_name)
            logger.info(f"✅ 专利复审库创建成功: {self.collection_name}")
        else:
            logger.error(f"❌ 专利复审库创建失败: {self.collection_name}")

        return success

    def generate_sample_patent_review_data(self) -> list[dict[str, Any]]:
        """生成示例专利复审数据"""
        logger.info('📝 生成示例专利复审数据...')

        sample_data = [
            # 专利复审决定
            {
                'id': 'review_decision_001',
                'text': '第29584号复审决定:申请号201810294048.1的发明专利申请,因权利要求1相对于对比文件1和公知常识的结合不具备创造性,维持驳回决定。申请人提交的意见陈述和修改后的权利要求书未能克服创造性缺陷。',
                'category': '复审决定',
                'type': 'decision',
                'domain': 'patent_review',
                'application_number': '201810294048.1',
                'decision_number': '第29584号',
                'decision_date': '2023-06-15',
                'review_result': '维持驳回'
            },
            {
                'id': 'review_decision_002',
                'text': '第31205号复审决定:申请号201710876543.2的发明专利申请,经复审组审查认为,申请人修改后的权利要求1具备创造性,撤销驳回决定,由原审查部门继续进行审批程序。',
                'category': '复审决定',
                'type': 'decision',
                'domain': 'patent_review',
                'application_number': '201710876543.2',
                'decision_number': '第31205号',
                'decision_date': '2023-09-20',
                'review_result': '撤销驳回'
            },
            {
                'id': 'review_decision_003',
                'text': '第28765号复审决定:申请号201910789543.8的发明专利申请,经形式审查和实质审查,认为申请文件符合专利法及其实施细则的规定,准予专利申请。',
                'category': '复审决定',
                'type': 'decision',
                'domain': 'patent_review',
                'application_number': '201910789543.8',
                'decision_number': '第28765号',
                'decision_date': '2023-04-12',
                'review_result': '准予申请'
            },
            # 专利复审理由
            {
                'id': 'review_reason_001',
                'text': '根据《专利法》第22条,发明应当具备新颖性、创造性和实用性。如果权利要求的技术方案相对于现有技术显而易见,则不具备创造性。复审中需重点论证技术启示的存在。',
                'category': '复审理由',
                'type': 'reason',
                'domain': 'patent_review',
                'legal_basis': '专利法第22条',
                'reason_type': '创造性'
            },
            {
                'id': 'review_reason_002',
                'text': '根据《专利法》第26条第3款,说明书应当对发明或实用新型作出清楚、完整的说明,以所属技术领域的技术人员能够实现为准。如果说明书公开不充分,将导致权利要求得不到支持。',
                'category': '复审理由',
                'type': 'reason',
                'domain': 'patent_review',
                'legal_basis': '专利法第26条第3款',
                'reason_type': '说明书公开不充分'
            },
            {
                'id': 'review_reason_003',
                'text': '根据《专利法》第26条第4款,权利要求书应当以说明书为依据,清楚、简要地限定要求专利保护的范围。如果权利要求的技术特征不清楚或得不到说明书支持,不符合规定。',
                'category': '复审理由',
                'type': 'reason',
                'domain': 'patent_review',
                'legal_basis': '专利法第26条第4款',
                'reason_type': '权利要求不清楚'
            },
            # 专利复审策略
            {
                'id': 'review_strategy_001',
                'text': '专利复审应对策略:详细分析驳回理由,明确技术争议焦点,补充技术证据,修改权利要求书以突出技术区别,提供充分的技术论证说明。',
                'category': '复审策略',
                'type': 'strategy',
                'domain': 'patent_review',
                'strategy_type': '应对策略'
            },
            {
                'id': 'review_strategy_002',
                'text': '专利复审证据组织:收集相关技术文献,提供技术专家意见,准备实验数据或测试报告,形成完整的证据链以支持复审请求。',
                'category': '复审策略',
                'type': 'strategy',
                'domain': 'patent_review',
                'strategy_type': '证据组织'
            },
            # 专利复审流程
            {
                'id': 'review_process_001',
                'text': '专利复审流程:收到驳回决定后3个月内提交复审请求,缴纳复审费,提交意见陈述书和修改文件,经形式审查后发给原审查部门预审,然后成立合议组进行审理,发出复审通知书,申请人答复,合议组作出复审决定。',
                'category': '复审流程',
                'type': 'process',
                'domain': 'patent_review',
                'process_type': '申请流程'
            },
            {
                'id': 'review_process_002',
                'text': '专利复审审查要点:审查修改是否超范围、技术方案是否清楚完整、新颖性和创造性是否符合要求、说明书是否充分公开、权利要求是否以说明书为依据。',
                'category': '复审流程',
                'type': 'process',
                'domain': 'patent_review',
                'process_type': '审查要点'
            }
        ]

        logger.info(f"✅ 生成了 {len(sample_data)} 条示例专利复审数据")
        return sample_data

    def generate_embedding_vector(self, text: str) -> list[float]:
        """生成嵌入向量 - 实际应用中应使用真实的embedding模型"""
        vector = random(1024).tolist()
        return vector

    def build_patent_review_db(self) -> bool:
        """构建专利复审数据库"""
        logger.info('🚀 开始构建专利复审库...')

        # 创建集合
        if not self.create_patent_review_collection():
            logger.error('❌ 专利复审库创建失败')
            return False

        # 生成示例数据
        sample_data = self.generate_sample_patent_review_data()

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

        logger.info(f"📦 准备插入 {len(vectors_data)} 个向量到专利复审库")

        # 批量插入向量
        success = self.vector_db_manager.batch_insert(
            collection_name=self.collection_name,
            vectors_data=vectors_data
        )

        if success:
            logger.info(f"✅ 专利复审库构建完成: {self.collection_name}")
            collection_info = self.vector_db_manager.get_collection_info(self.collection_name)
            if collection_info:
                points_count = collection_info.get('points_count', 0)
                logger.info(f"📊 集合状态: {points_count} 个向量点")
        else:
            logger.error('❌ 专利复审库构建失败')

        return success

    def test_patent_review_db(self) -> bool:
        """测试专利复审库功能"""
        logger.info('🧪 测试专利复审库功能...')

        if self.collection_name not in self.vector_db_manager.existing_collections:
            logger.error(f"❌ 集合 {self.collection_name} 不存在")
            return False

        # 生成测试向量
        test_vector = self.generate_embedding_vector('专利复审 创造性 驳回决定')

        from core.vector_db.vector_db_manager import VectorQuery

        query = VectorQuery(
            vector=test_vector,
            text='专利复审 创造性 驳回决定',
            limit=3,
            with_payload=True
        )

        results = self.vector_db_manager.search_in_collection(self.collection_name, query)

        logger.info(f"🔍 在专利复审库中找到 {len(results)} 个结果")

        for i, result in enumerate(results):
            logger.info(f"  {i+1}. 评分: {result.score:.3f}")
            logger.info(f"     内容: {result.payload.get('text', '')[:100]}...")
            logger.info(f"     类别: {result.payload.get('category', 'Unknown')}")
            logger.info(f"     类型: {result.payload.get('type', 'Unknown')}")
            print()

        return len(results) > 0

def main():
    """主函数 - 构建专利复审向量库"""
    logger.info('🏗️  开始构建专利复审向量库...')

    builder = PatentReviewBuilder()

    logger.info(str('='*70))
    logger.info('🏗️  专利复审向量库构建器')
    logger.info(str('='*70))
    logger.info(f"📍 目标集合: {builder.collection_name}")
    logger.info("📊 向量维度: 1024 (专利分析)")
    logger.info("🎯 用途: 专利复审分析、复审决定检索、策略参考")
    logger.info(str('='*70))

    # 构建专利复审库
    success = builder.build_patent_review_db()

    if success:
        logger.info("\n✅ 专利复审向量库构建成功!")

        # 测试功能
        test_success = builder.test_patent_review_db()
        if test_success:
            logger.info('✅ 功能测试通过!')
            logger.info(f"🔗 专利复审向量库已准备就绪: {builder.collection_name}")
        else:
            logger.info('❌ 功能测试失败')
    else:
        logger.info("\n❌ 专利复审向量库构建失败")
        return False

    logger.info(str("\n" + '='*70))
    logger.info('🎯 专利复审向量库已成功集成到Athena平台')
    logger.info('📋 现在可以进行专利复审分析、决定检索等专业操作')
    logger.info(str('='*70))

    return success

if __name__ == '__main__':
    success = main()
    if not success:
        exit(1)
