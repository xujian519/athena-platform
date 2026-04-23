#!/usr/bin/env python3

"""
Athena工作平台 - 共用向量库构建器
构建用于Athena和小诺的通用记忆向量库
"""

# Numpy兼容性导入
import logging
import os

# 添加项目路径
import sys
from datetime import datetime
from typing import Any

from config.numpy_compatibility import random
from core.logging_config import setup_logging

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from core.vector_db.vector_db_manager import VectorDBManager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

class GeneralMemoryBuilder:
    """共用记忆库构建器"""

    def __init__(self):
        self.vector_db_manager = VectorDBManager()
        self.collection_name = 'general_memory_db'

    def create_general_memory_collection(self) -> bool:
        """创建共用记忆集合"""
        logger.info(f"🏗️ 创建共用记忆库: {self.collection_name}")

        # 创建集合 (1024维,适用于通用知识)
        success = self.vector_db_manager.create_collection(
            collection_name=self.collection_name,
            vector_size=1024,
            distance='Cosine'
        )

        if success:
            self.vector_db_manager.existing_collections.add(self.collection_name)
            logger.info(f"✅ 共用记忆库创建成功: {self.collection_name}")
        else:
            logger.error(f"❌ 共用记忆库创建失败: {self.collection_name}")

        return success

    def generate_sample_general_memory_data(self) -> list[dict[str, Any]]:
        """生成示例通用记忆数据"""
        logger.info('📝 生成示例通用记忆数据...')

        sample_data = [
            # 通用知识
            {
                'id': 'general_001',
                'text': '人工智能是计算机科学的一个分支,它试图理解智能的实质,并生产出一种新的能以人类智能相似的方式做出反应的智能机器。',
                'category': 'AI知识',
                'type': 'definition',
                'domain': 'general'
            },
            {
                'id': 'general_002',
                'text': '机器学习是人工智能的一个子集,它使计算机能够从数据中学习并改进算法,而无需明确编程。',
                'category': 'AI知识',
                'type': 'definition',
                'domain': 'general'
            },
            {
                'id': 'general_003',
                'text': '深度学习是机器学习的一个分支,它使用多层神经网络来模拟和解决复杂问题。',
                'category': 'AI知识',
                'type': 'definition',
                'domain': 'general'
            },
            {
                'id': 'general_004',
                'text': '神经网络是由大量节点(或称神经元)相互连接而成的网络,用于模拟人脑处理信息的方式。',
                'category': 'AI知识',
                'type': 'definition',
                'domain': 'general'
            },
            # 对话历史示例
            {
                'id': 'conversation_001',
                'text': '用户: 你好,小娜。小娜: 你好!有什么可以帮助你的吗?',
                'category': '对话历史',
                'type': 'conversation',
                'domain': 'conversation',
                'user': 'user123',
                'timestamp': datetime.now().isoformat()
            },
            {
                'id': 'conversation_002',
                'text': '用户: 请解释一下什么是专利。小娜: 专利是政府授予发明者的一套排他性权利,通常在有限的时间内生效。',
                'category': '对话历史',
                'type': 'conversation',
                'domain': 'conversation',
                'user': 'user124',
                'timestamp': datetime.now().isoformat()
            },
            # 用户偏好
            {
                'id': 'preference_001',
                'text': '用户喜欢技术类对话,偏好详细的解释和实例。',
                'category': '用户偏好',
                'type': 'preference',
                'domain': 'user_profile',
                'user': 'tech_enthusiast'
            },
            {
                'id': 'preference_002',
                'text': '用户关注专利法律知识,经常询问专利申请和保护相关问题。',
                'category': '用户偏好',
                'type': 'preference',
                'domain': 'user_profile',
                'user': 'patent_user'
            },
            # 学习历史
            {
                'id': 'learning_001',
                'text': '用户最近学习了关于神经网络的基础知识,包括前向传播和反向传播算法。',
                'category': '学习历史',
                'type': 'learning',
                'domain': 'learning_history',
                'user': 'student_001'
            },
            {
                'id': 'learning_002',
                'text': '用户对专利检索方法学表现出浓厚兴趣,学习了关键词检索和分类号检索。',
                'category': '学习历史',
                'type': 'learning',
                'domain': 'learning_history',
                'user': 'researcher_001'
            }
        ]

        logger.info(f"✅ 生成了 {len(sample_data)} 条示例数据")
        return sample_data

    def generate_embedding_vector(self, text: str) -> list[float]:
        """生成嵌入向量 - 在实际应用中这里应该调用真实的embedding模型"""
        # 使用随机向量作为占位符,实际应用中应使用真实的嵌入模型
        # 如 sentence-transformers, OpenAI embeddings, etc.
        vector = random(1024).tolist()
        return vector

    def build_general_memory_db(self) -> bool:
        """构建共用记忆数据库"""
        logger.info('🚀 开始构建共用记忆库...')

        # 创建集合
        if not self.create_general_memory_collection():
            logger.error('❌ 共用记忆库创建失败')
            return False

        # 生成示例数据
        sample_data = self.generate_sample_general_memory_data()

        # 准备插入数据 (需要将ID转换为整数)
        vectors_data = []
        for i, item in enumerate(sample_data):
            vector = self.generate_embedding_vector(item['text'])

            vector_data = {
                'id': i,  # 使用整数ID
                'vector': vector,
                'payload': item  # 包含所有元数据
            }
            vectors_data.append(vector_data)

        logger.info(f"📦 准备插入 {len(vectors_data)} 个向量到共用记忆库")

        # 批量插入向量
        success = self.vector_db_manager.batch_insert(
            collection_name=self.collection_name,
            vectors_data=vectors_data
        )

        if success:
            logger.info(f"✅ 共用记忆库构建完成: {self.collection_name}")
            collection_info = self.vector_db_manager.get_collection_info(self.collection_name)
            if collection_info:
                points_count = collection_info.get('points_count', 0)
                logger.info(f"📊 集合状态: {points_count} 个向量点")
        else:
            logger.error('❌ 共用记忆库构建失败')

        return success

    def test_general_memory_db(self) -> bool:
        """测试共用记忆库功能"""
        logger.info('🧪 测试共用记忆库功能...')

        if self.collection_name not in self.vector_db_manager.existing_collections:
            logger.error(f"❌ 集合 {self.collection_name} 不存在")
            return False

        # 生成测试向量
        test_vector = self.generate_embedding_vector('人工智能技术')

        from core.vector_db.vector_db_manager import VectorQuery

        query = VectorQuery(
            vector=test_vector,
            text='人工智能技术',
            limit=3,
            with_payload=True
        )

        results = self.vector_db_manager.search_in_collection(self.collection_name, query)

        logger.info(f"🔍 在共用记忆库中找到 {len(results)} 个结果")

        for i, result in enumerate(results):
            logger.info(f"  {i+1}. 评分: {result.score:.3f}")
            logger.info(f"     内容: {result.payload.get('text', '')[:100]}...")
            logger.info(f"     类别: {result.payload.get('category', 'Unknown')}")
            print()

        return len(results) > 0

def main():
    """主函数 - 构建共用向量库"""
    logger.info('🏗️  开始构建Athena和小诺共用向量库...')

    builder = GeneralMemoryBuilder()

    logger.info(str('='*70))
    logger.info('🏗️  Athena和小诺共用向量库构建器')
    logger.info(str('='*70))
    logger.info(f"📍 目标集合: {builder.collection_name}")
    logger.info("📊 向量维度: 1024 (通用知识)")
    logger.info("🎯 用途: 存储Athena和小诺的通用记忆")
    logger.info(str('='*70))

    # 构建共用记忆库
    success = builder.build_general_memory_db()

    if success:
        logger.info("\n✅ 共用向量库构建成功!")

        # 测试功能
        test_success = builder.test_general_memory_db()
        if test_success:
            logger.info('✅ 功能测试通过!')
            logger.info(f"🔗 共用向量库已准备就绪: {builder.collection_name}")
        else:
            logger.info('❌ 功能测试失败')
    else:
        logger.info("\n❌ 共用向量库构建失败")
        return False

    logger.info(str("\n" + '='*70))
    logger.info('🎯 共用向量库已成功集成到Athena和小诺的记忆系统')
    logger.info('📋 现在可以存储和检索通用知识、对话历史、用户偏好等信息')
    logger.info(str('='*70))

    return success

if __name__ == '__main__':
    success = main()
    if not success:
        exit(1)

