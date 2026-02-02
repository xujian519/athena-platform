#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试多模型向量融合功能
Test Multi-Model Vector Fusion
"""

import logging
import os
import sys
import time
from datetime import datetime

logger = logging.getLogger(__name__)

# 添加路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_multi_model_vectorizer():
    """测试多模型向量器"""
    logger.info(str("\n" + '='*60))
    logger.info('🔀 测试多模型向量融合器')
    logger.info(str('='*60))

    try:
        from multi_model_vectorizer import MultiModelVectorizer

        vectorizer = MultiModelVectorizer()

        # 测试文本
        test_texts = [
            '本发明涉及一种新型电池管理系统，包括电池状态监测模块和均衡控制模块。',
            '根据专利法规定，发明应当具备新颖性、创造性和实用性。',
            '人工智能在医疗诊断中的应用，包括图像识别和病理分析。'
        ]

        logger.info("\n1. 测试自动选择模型融合...")
        start_time = time.time()

        result = vectorizer.encode_with_multiple_models(
            test_texts,
            model_config={
                'auto_select': True,
                'max_models': 2
            },
            fusion_strategy='weighted_average'
        )

        fusion_time = time.time() - start_time

        logger.info(f"   ✅ 融合成功，耗时: {fusion_time:.3f}s")
        logger.info(f"   向量维度: {result['fused_vector'].shape}")
        logger.info(f"   使用的模型: {result['fusion_info']['models_used']}")
        logger.info(f"   融合时间: {result['fusion_info']['fusion_time']:.3f}s")

        # 测试指定模型融合
        logger.info("\n2. 测试指定模型融合...")
        result2 = vectorizer.encode_with_multiple_models(
            test_texts,
            model_config={
                'models': ['bge-large-zh-v1.5', 'bge-base-zh-v1.5'],
                'weights': [0.7, 0.3]
            },
            fusion_strategy='weighted_average',
            return_individual=True
        )

        logger.info(f"   ✅ 指定模型融合成功")
        logger.info(f"   向量维度: {result2['fused_vector'].shape}")
        logger.info(f"   独立向量数量: {len(result2['individual_vectors'])}")

        # 测试拼接融合
        logger.info("\n3. 测试拼接融合策略...")
        result3 = vectorizer.encode_with_multiple_models(
            test_texts[:1],  # 只用一个文本测试
            model_config={
                'models': ['bge-large-zh-v1.5', 'bge-base-zh-v1.5'],
                'weights': [0.6, 0.4]
            },
            fusion_strategy='concatenation'
        )

        logger.info(f"   ✅ 拼接融合成功")
        logger.info(f"   拼接后向量维度: {result3['fused_vector'].shape}")
        logger.info(f"   预期维度: {1024 + 768} (1024+768)")

        # 测试专利编码
        logger.info("\n4. 测试专利数据编码...")
        patents = [
            {
                'title': '智能电池管理系统',
                'abstract': '一种用于实时监测和管理电池状态的智能系统，包括状态监测模块和均衡控制模块。',
                'patent_type': '发明专利'
            },
            {
                'title': 'AI医疗诊断设备',
                'abstract': '基于人工智能技术的医疗诊断装置和方法，通过图像识别技术进行病理分析。',
                'patent_type': '实用新型'
            }
        ]

        patent_result = vectorizer.encode_patents(patents)
        logger.info(f"   编码专利数: {len(patent_result['patents'])}")

        for patent in patent_result['patents']:
            if 'vector' in patent:
                logger.info(f"   - {patent['title']}: 向量维度 {len(patent['vector'])}")

        # 缓存统计
        logger.info("\n5. 缓存统计:")
        cache_stats = vectorizer.get_cache_stats()
        logger.info(f"   缓存大小: {cache_stats['cache_size']}")
        logger.info(f"   缓存命中率: {cache_stats['cache_hit_rate']:.2%}")

        # 性能统计
        logger.info("\n6. 性能统计:")
        perf_stats = vectorizer.get_performance_stats()
        logger.info(f"   总请求数: {perf_stats['total_requests']}")
        logger.info(f"   缓存命中数: {perf_stats['cache_hits']}")
        logger.info(f"   模型切换次数: {sum(perf_stats['model_switches'].values())}")

        vectorizer.cleanup()
        return True

    except Exception as e:
        logger.info(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_patent_integration():
    """测试与真实专利数据的集成"""
    logger.info(str("\n" + '='*60))
    logger.info('📊 测试与真实专利数据集成')
    logger.info(str('='*60))

    try:
        from multi_model_vectorizer import MultiModelVectorizer
        from real_patent_integration.real_patent_connector_v2 import (
            RealPatentConnectorV2,
        )

        # 加载少量专利数据进行测试
        logger.info("\n1. 加载专利数据...")
        connector = RealPatentConnectorV2()
        patents = connector.load_patents(limit=10)
        logger.info(f"   加载了 {len(patents)} 条专利")

        if patents:
            # 使用多模型向量器编码
            logger.info("\n2. 使用多模型编码专利数据...")
            vectorizer = MultiModelVectorizer()

            # 只编码前3条专利以节省时间
            patent_result = vectorizer.encode_patents(patents[:3])
            logger.info(f"   成功编码 {len(patent_result['patents'])} 条专利")

            # 显示编码结果
            logger.info("\n3. 编码结果:")
            for patent in patent_result['patents']:
                if 'vector' in patent:
                    logger.info(f"   - 专利ID: {patent.get('id', 'N/A')}")
                    logger.info(f"     标题: {patent.get('patent_name', 'N/A')[:30]}...")
                    logger.info(f"     向量维度: {patent.get('vector_dimension', 'N/A')}")
                    logger.info(f"     专利类型: {patent.get('patent_type', 'N/A')}")

            vectorizer.cleanup()

        connector.close()
        return True

    except Exception as e:
        logger.info(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    logger.info("\n🚀 多模型向量融合集成测试")
    logger.info(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(str('='*60))

    # 执行测试
    test_results = []

    # 测试多模型向量器
    test_results.append(('多模型向量器', test_multi_model_vectorizer()))

    # 测试专利数据集成
    test_results.append(('专利数据集成', test_patent_integration()))

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
        logger.info("\n🎉 所有测试通过！多模型向量融合功能正常。")
        logger.info("\n系统功能：")
        logger.info('1. ✅ 多个中文BERT模型管理和切换')
        logger.info('2. ✅ 智能模型自动选择')
        logger.info('3. ✅ 多模型向量融合（加权平均、拼接）')
        logger.info('4. ✅ 专利数据智能编码')
        logger.info('5. ✅ 缓存和性能优化（内存级）')

        logger.info("\n下一步：实现Redis缓存和并行处理优化")
    else:
        logger.info("\n⚠️ 部分测试失败，请检查错误信息。")

if __name__ == '__main__':
    main()