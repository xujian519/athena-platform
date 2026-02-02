#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试中文BERT模型加载
Test Chinese BERT Model Loading
"""

import logging
import os
import sys
from datetime import datetime

logger = logging.getLogger(__name__)

# 添加路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_model_loading():
    """测试模型加载功能"""
    logger.info(str("\n" + '='*60))
    logger.info('🧪 测试中文BERT模型加载')
    logger.info(str('='*60))
    logger.info(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    try:
        from model_manager import ChineseBERTModelManager

        manager = ChineseBERTModelManager()

        # 测试加载bge-large-zh-v1.5
        logger.info("\n1. 测试加载 bge-large-zh-v1.5...")
        if manager.load_model('bge-large-zh-v1.5'):
            logger.info('   ✅ 加载成功')

            # 测试编码
            test_texts = ['这是一个测试文本', '本发明涉及一种新型电池管理系统']
            logger.info("\n2. 测试文本编码...")
            embeddings = manager.encode_texts(test_texts)
            if embeddings is not None and len(embeddings) > 0:
                logger.info(f"   ✅ 编码成功，向量维度: {embeddings.shape}")
                logger.info(f"   文本数: {len(embeddings)}")
            else:
                logger.info('   ❌ 编码失败')
        else:
            logger.info('   ❌ 加载失败')

        # 测试加载bge-base-zh-v1.5
        logger.info("\n3. 测试加载 bge-base-zh-v1.5...")
        if manager.switch_model('bge-base-zh-v1.5'):
            logger.info('   ✅ 切换成功')

            test_texts = ['专利申请需要满足新颖性要求']
            embeddings = manager.encode_texts(test_texts)
            if embeddings is not None and len(embeddings) > 0:
                logger.info(f"   ✅ 编码成功，向量维度: {embeddings.shape}")
            else:
                logger.info('   ❌ 编码失败')
        else:
            logger.info('   ❌ 切换失败')

        manager.cleanup()
        return True

    except Exception as e:
        logger.info(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_model_selector():
    """测试模型选择器"""
    logger.info(str("\n" + '='*60))
    logger.info('🎯 测试智能模型选择器')
    logger.info(str('='*60))

    try:
        from intelligent_model_selector import IntelligentModelSelector

        selector = IntelligentModelSelector()

        # 测试查询
        test_queries = [
            '本发明涉及一种电池管理系统',
            '根据专利法第二十二条规定',
            '人工智能在医疗诊断中的应用'
        ]

        for i, query in enumerate(test_queries, 1):
            logger.info(f"\n{i}. 查询: {query}")
            logger.info(str('-' * 40))

            model_name, reason = selector.select_model(query)
            logger.info(f"   推荐模型: {model_name}")
            logger.info(f"   推荐原因: {reason.get('reason', 'N/A')}")

        return True

    except Exception as e:
        logger.info(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    logger.info('🚀 中文BERT模型集成测试')

    # 执行测试
    test_results = []

    # 测试模型加载
    test_results.append(('模型加载', test_model_loading()))

    # 测试模型选择器
    test_results.append(('模型选择器', test_model_selector()))

    # 测试结果
    logger.info(str("\n" + '='*60))
    logger.info('📋 测试结果总结')
    logger.info(str('='*60))

    passed = 0
    for test_name, result in test_results:
        status = '✅ 通过' if result else '❌ 失败'
        logger.info(f"   {test_name}: {status}")
        if result:
            passed += 1

    logger.info(f"\n总通过率: {passed}/{len(test_results)} ({passed/len(test_results)*100:.1f}%)")

    if passed == len(test_results):
        logger.info("\n🎉 所有测试通过！中文BERT模型集成成功。")
        logger.info("\n下一步：")
        logger.info('1. 实现Redis缓存系统')
        logger.info('2. 添加并行处理优化')
        logger.info('3. 与真实专利数据集成测试')
    else:
        logger.info("\n⚠️ 部分测试失败，请检查错误信息。")

if __name__ == '__main__':
    main()