#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中文BERT专业模型集成测试
Chinese BERT Professional Model Integration Test
"""

import logging
import os
import sys
import time
from datetime import datetime

logger = logging.getLogger(__name__)

# 添加路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def test_model_manager():
    """测试模型管理器"""
    logger.info(str("\n" + '='*60))
    logger.info('第一步：测试中文BERT模型管理器')
    logger.info(str('='*60))

    try:
        from model_manager import ChineseBERTModelManager

        manager = ChineseBERTModelManager()

        # 显示可用模型
        logger.info("\n1. 可用模型列表：")
        models = manager.list_available_models()
        for model in models:
            logger.info(f"   - {model['name']}")
            logger.info(f"     描述: {model['config']['description']}")
            logger.info(f"     维度: {model['config']['dimension']}")
            logger.info(f"     特长: {', '.join(model['config']['specialties'])}")

        # 测试模型切换
        logger.info("\n2. 测试模型切换...")
        test_models = ['bge-base-zh-v1.5', 'patent-bert-base']

        for model_name in test_models:
            logger.info(f"\n   加载模型: {model_name}")
            start_time = time.time()

            if manager.switch_model(model_name):
                load_time = time.time() - start_time
                logger.info(f"   ✅ 加载成功，耗时: {load_time:.2f}s")

                # 测试编码
                test_text = ['这是一个测试文本']
                embeddings = manager.encode_texts(test_text)
                if embeddings is not None and len(embeddings) > 0:
                    logger.info(f"   ✅ 编码成功，向量维度: {embeddings.shape}")
                else:
                    logger.info(f"   ❌ 编码失败")
            else:
                logger.info(f"   ❌ 加载失败")

        # 显示性能指标
        logger.info("\n3. 性能指标:")
        metrics = manager.get_performance_metrics()
        for model_name, metric in metrics.items():
            if metric['total_requests'] > 0:
                logger.info(f"   - {model_name}:")
                logger.info(f"     请求数: {metric['total_requests']}")
                logger.info(f"     平均速度: {metric['avg_texts_per_second']:.1f} texts/s")

        manager.cleanup()
        return True

    except Exception as e:
        logger.info(f"❌ 模型管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_intelligent_selector():
    """测试智能模型选择器"""
    logger.info(str("\n" + '='*60))
    logger.info('第二步：测试智能模型选择器')
    logger.info(str('='*60))

    try:
        from intelligent_model_selector import IntelligentModelSelector

        selector = IntelligentModelSelector()

        # 测试查询
        test_queries = [
            '本发明涉及一种电池管理系统',
            '根据专利法第二十二条规定',
            '人工智能在医疗诊断中的应用',
            '快速检索算法',
            '一种复杂的深度学习系统架构设计'
        ]

        for i, query in enumerate(test_queries, 1):
            logger.info(f"\n{i}. 查询: {query}")
            logger.info(str('-' * 50))

            # 选择模型
            model_name, reason = selector.select_model(query)
            logger.info(f"   推荐模型: {model_name}")
            logger.info(f"   选择原因: {reason.get('reason', 'N/A')}")

            # 显示详细分析
            if 'analysis' in reason:
                analysis = reason['analysis']
                logger.info(f"\n   查询分析:")
                logger.info(f"   - 文本长度: {analysis['length']} 字符")
                logger.info(f"   - 复杂度: {analysis['complexity']}")

                # 显示领域评分
                logger.info(f"\n   领域匹配:")
                for domain, score_info in analysis['domain_scores'].items():
                    if score_info['score'] > 0:
                        logger.info(f"   - {domain}: {score_info['score']:.2f}")

        return True

    except Exception as e:
        logger.info(f"❌ 智能选择器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multi_model_vectorizer():
    """测试多模型向量器"""
    logger.info(str("\n" + '='*60))
    logger.info('第三步：测试多模型向量融合器')
    logger.info(str('='*60))

    try:
        from multi_model_vectorizer import MultiModelVectorizer

        vectorizer = MultiModelVectorizer()

        # 测试文本
        test_texts = [
            '本发明涉及一种新型电池管理系统，包括电池状态监测模块',
            '根据专利法规定，发明应当具备新颖性、创造性和实用性',
            '人工智能在医疗诊断设备中的应用，包括图像识别'
        ]

        # 测试自动选择模型融合
        logger.info("\n1. 自动选择模型融合...")
        start_time = time.time()

        result = vectorizer.encode_with_multiple_models(
            test_texts,
            model_config={
                'auto_select': True,
                'max_models': 3
            }
        )

        fusion_time = time.time() - start_time

        logger.info(f"   ✅ 融合成功，耗时: {fusion_time:.3f}s")
        logger.info(f"   向量维度: {result['fused_vector'].shape}")
        logger.info(f"   使用模型: {result['fusion_info']['models_used']}")
        logger.info(f"   融合时间: {result['fusion_info']['fusion_time']:.3f}s")

        # 测试指定模型融合
        logger.info("\n2. 指定模型融合...")
        result2 = vectorizer.encode_with_multiple_models(
            test_texts,
            model_config={
                'models': ['bge-base-zh-v1.5'],
                'weights': [1.0]
            },
            fusion_strategy='weighted_average'
        )

        logger.info(f"   ✅ 指定模型融合成功")
        logger.info(f"   向量维度: {result2['fused_vector'].shape}")

        # 测试专利编码
        logger.info("\n3. 专利数据编码测试...")
        patents = [
            {
                'title': '智能电池管理系统',
                'abstract': '一种用于实时监测和管理电池状态的智能系统',
                'patent_type': '发明专利'
            },
            {
                'title': 'AI医疗诊断设备',
                'abstract': '基于人工智能技术的医疗诊断装置及其方法',
                'patent_type': '实用新型'
            }
        ]

        patent_result = vectorizer.encode_patents(patents)
        logger.info(f"   编码专利数: {len(patent_result['patents'])}")

        for patent in patent_result['patents']:
            if 'vector' in patent:
                logger.info(f"   - {patent['title']}")
                logger.info(f"     向量维度: {len(patent['vector'])}")
                logger.info(f"     专利类型: {patent.get('patent_type', 'N/A')}")

        # 缓存统计
        logger.info("\n4. 缓存统计:")
        cache_stats = vectorizer.get_cache_stats()
        logger.info(f"   缓存大小: {cache_stats['cache_size']}")
        logger.info(f"   缓存命中率: {cache_stats['cache_hit_rate']:.2%}")

        vectorizer.cleanup()
        return True

    except Exception as e:
        logger.info(f"❌ 多模型向量器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration():
    """测试完整的集成功能"""
    logger.info(str("\n" + '='*60))
    logger.info('第四步：测试完整集成功能')
    logger.info(str('='*60))

    try:
        from intelligent_model_selector import IntelligentModelSelector
        from multi_model_vectorizer import MultiModelVectorizer
        from real_patent_connector_v2 import RealPatentConnectorV2

        # 创建组件
        vectorizer = MultiModelVectorizer()
        selector = IntelligentModelSelector()
        connector = RealPatentConnectorV2()

        logger.info('1. 加载专利数据...')
        patents = connector.load_patents(limit=5)
        logger.info(f"   加载了 {len(patents)} 条专利")

        if patents:
            logger.info("\n2. 分析专利文本类型...")
            # 分析第一条专利
            first_patent = patents[0]
            patent_text = f"{first_patent.get('patent_name', '')} {first_patent.get('abstract', '')}"

            # 智能选择模型
            model_name, reason = selector.select_model(patent_text)
            logger.info(f"   推荐模型: {model_name}")
            logger.info(f"   选择原因: {reason.get('reason', 'N/A')}")

            # 多模型编码
            logger.info("\n3. 多模型编码专利数据...")
            patent_result = vectorizer.encode_patents(patents[:2])
            logger.info(f"   成功编码 {len(patent_result['patents'])} 条专利")

        connector.close()
        vectorizer.cleanup()
        return True

    except Exception as e:
        logger.info(f"❌ 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    logger.info("\n🚀 中文BERT专业模型集成测试")
    logger.info(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(str('='*60))

    # 执行测试
    test_steps = [
        ('模型管理器', test_model_manager),
        ('智能选择器', test_intelligent_selector),
        ('多模型向量器', test_multi_model_vectorizer),
        ('完整集成', test_integration)
    ]

    # 执行测试
    passed = 0
    failed = 0

    for step_name, test_func in test_steps:
        logger.info(f"\n{'='*60}")
        logger.info(f"执行测试: {step_name}")
        logger.info(f"{'='*60}")

        try:
            if test_func():
                passed += 1
                logger.info(f"\n✅ {step_name} - 通过")
            else:
                failed += 1
                logger.info(f"\n❌ {step_name} - 失败")
        except Exception as e:
            failed += 1
            logger.info(f"\n❌ {step_name} - 异常: {e}")

    # 测试总结
    logger.info(f"\n{'='*60}")
    logger.info('测试总结')
    logger.info(f"{'='*60}")
    logger.info(f"总测试数: {passed + failed}")
    logger.info(f"通过: {passed}")
    logger.info(f"失败: {failed}")

    if failed == 0:
        logger.info("\n🎉 所有测试通过！中文BERT专业模型集成成功。")
        logger.info("\n系统功能：")
        logger.info('1. ✅ 多个中文BERT模型管理')
        logger.info('2. ✅ 智能模型自动选择')
        logger.info('3. ✅ 多模型向量融合')
        logger.info('4. ✅ 专利数据智能编码')
        logger.info('5. ✅ 缓存和性能优化')

        logger.info("\n下一步：")
        logger.info('1. 实现Redis缓存系统')
        logger.info('2. 添加并行处理优化')
    else:
        logger.info("\n⚠️ 部分测试失败，请检查错误信息并修复问题。")

if __name__ == '__main__':
    main()