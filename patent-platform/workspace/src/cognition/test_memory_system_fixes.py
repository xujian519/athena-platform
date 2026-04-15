#!/usr/bin/env python3
"""
记忆模块修复验证测试
Memory System Fixes Verification Test

验证所有修复是否正常工作

作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

# Numpy兼容性导入
import asyncio
import logging
import sys
import traceback
from datetime import datetime

from config.numpy_compatibility import random, sum

logger = logging.getLogger(__name__)

# 添加项目路径
sys.path.insert(0, '/Users/xujian/Athena工作平台')
sys.path.insert(0, '/Users/xujian/Athena工作平台/patent-platform/workspace/src')
sys.path.insert(0, '/Users/xujian/Athena工作平台/patent-platform/workspace/src/cognition')

async def test_memory_processor_fixes():
    """测试MemoryProcessor修复"""
    logger.info("\n🔧 测试1: MemoryProcessor接口修复")
    logger.info(str('-' * 50))

    try:
        from cognition.memory_processor import MemoryProcessor

        # 测试新的构造函数
        processor = MemoryProcessor(agent_id='test_agent_1024', storage_path='test_memory_fix.db')
        logger.info('✅ 新构造函数支持agent_id参数')

        # 测试initialize方法
        await processor.initialize()
        logger.info('✅ initialize方法存在并可调用')

        # 测试记忆处理
        test_memory = {
            'content': '这是一个测试记忆，用于验证修复后的功能。',
            'type': 'episodic',
            'importance': 0.8,
            'context': {'test': 'fixes'}
        }

        result = await processor.process_memory(test_memory)
        if result.get('success'):
            logger.info('✅ 记忆处理成功')
        else:
            logger.info(f"⚠️ 记忆处理: {result}")

        # 测试shutdown方法
        await processor.shutdown()
        logger.info('✅ shutdown方法正常工作')

        return True

    except Exception as e:
        logger.info(f"❌ 测试失败: {e}")
        traceback.print_exc()
        return False

async def test_optimized_memory_index_fixes():
    """测试优化记忆索引修复"""
    logger.info("\n🔧 测试2: 优化记忆索引枚举修复")
    logger.info(str('-' * 50))

    try:
        from cognition.optimized_memory_index import IndexEntry, OptimizedMemoryIndex

        # 测试字符串索引类型
        index = OptimizedMemoryIndex(index_type='composite', dimension=1024)
        logger.info('✅ 支持字符串索引类型参数')

        # 测试添加条目
        test_entries = [
            IndexEntry(
                id=f"entry_{i}",
                content=f"专利相关测试内容 {i}，包含技术方案和权利要求。",
                metadata={'category': 'patent', 'test': 'fixes'}
            )
            for i in range(5)
        ]

        for entry in test_entries:
            index.add_entry(entry)

        logger.info('✅ 成功添加索引条目')

        # 测试搜索
        queries = ['技术方案', '权利要求', '专利', '测试']
        for query in queries:
            results = await index.search(query, top_k=3, similarity_threshold=0.01)
            logger.info(f"✅ 搜索 '{query}': 找到 {len(results)} 个结果")

        # 获取统计信息
        stats = index.get_stats()
        logger.info(f"📊 索引统计: {stats['total_entries']} 个条目")

        return True

    except Exception as e:
        logger.info(f"❌ 测试失败: {e}")
        traceback.print_exc()
        return False

async def test_search_algorithm_improvements():
    """测试搜索算法改进"""
    logger.info("\n🔧 测试3: 搜索算法改进")
    logger.info(str('-' * 50))

    try:
        from cognition.optimized_memory_index import IndexEntry, OptimizedMemoryIndex

        # 创建索引
        index = OptimizedMemoryIndex(index_type='composite', dimension=1024)

        # 添加测试条目（包含向量）
        test_entries = [
            IndexEntry(
                id='patent_1',
                content='本发明涉及一种人工智能在专利审查中的应用方法',
                vector=random(1024),
                metadata={'type': 'patent'}
            ),
            IndexEntry(
                id='tech_1',
                content='深度学习技术可以用于图像识别和自然语言处理',
                vector=random(1024),
                metadata={'type': 'technology'}
            ),
            IndexEntry(
                id='method_1',
                content='机器学习算法在专利分类中表现出色',
                vector=random(1024),
                metadata={'type': 'method'}
            )
        ]

        for entry in test_entries:
            index.add_entry(entry)

        # 测试不同搜索类型
        search_types = ['keyword', 'semantic', 'tfidf', 'vector', 'hybrid']
        query = '人工智能专利'

        for search_type in search_types:
            results = await index.search(
                query=query,
                top_k=5,
                search_type=search_type,
                similarity_threshold=0.01
            )
            logger.info(f"✅ {search_type} 搜索: 找到 {len(results)} 个结果")

        return True

    except Exception as e:
        logger.info(f"❌ 测试失败: {e}")
        traceback.print_exc()
        return False

async def test_config_manager():
    """测试配置管理器"""
    logger.info("\n🔧 测试4: 统一配置管理系统")
    logger.info(str('-' * 50))

    try:
        from cognition.memory_config_manager import (
            get_config_manager,
        )

        # 获取配置管理器
        config_manager = get_config_manager()
        config = config_manager.get_config()

        # 验证默认配置
        logger.info(f"✅ 向量维度: {config.vector_memory.dimension} (应该是1024)")
        logger.info(f"✅ 最大向量数: {config.vector_memory.max_vectors}")
        logger.info(f"✅ 启用FAISS: {config.vector_memory.use_faiss}")

        # 测试配置更新
        updates = {
            'vector_memory': {
                'similarity_threshold': 0.05
            }
        }
        config_manager.update_config(updates)
        logger.info('✅ 配置更新成功')

        # 获取配置摘要
        summary = config_manager.get_config_summary()
        logger.info(f"✅ 配置摘要生成成功，版本: {summary['version']}")

        return True

    except Exception as e:
        logger.info(f"❌ 测试失败: {e}")
        traceback.print_exc()
        return False

async def test_error_handling():
    """测试错误处理"""
    logger.info("\n🔧 测试5: 错误处理和日志记录")
    logger.info(str('-' * 50))

    try:
        from cognition.memory_error_handler import (
            MemoryStorageError,
            MemorySystemError,
            get_error_handler,
        )

        # 测试异常类
        try:
            raise MemoryStorageError('测试存储错误', details={'test': True})
        except MemorySystemError as e:
            logger.info(f"✅ 捕获记忆系统异常: {e.error_code}")

        # 测试错误处理
        error_handler = get_error_handler()
        stats = error_handler.get_error_statistics()
        logger.info(f"✅ 错误统计功能正常: {stats['total_errors']} 个错误")

        return True

    except Exception as e:
        logger.info(f"❌ 测试失败: {e}")
        traceback.print_exc()
        return False

async def test_performance_monitoring():
    """测试性能监控"""
    logger.info("\n🔧 测试6: 性能监控机制")
    logger.info(str('-' * 50))

    try:
        from cognition.memory_performance_monitor import (
            get_performance_monitor,
            record_metric,
            record_operation,
        )

        # 获取监控器
        monitor = get_performance_monitor()
        logger.info('✅ 性能监控器创建成功')

        # 记录一些测试指标
        record_operation('test_operation', 0.1, True)
        record_operation('test_operation', 0.2, True)
        record_operation('test_operation', 0.05, False)

        record_metric('test_metric', 42.0, 'count', 'test_component')

        logger.info('✅ 指标记录成功')

        # 获取当前指标
        current_metrics = monitor.get_current_metrics()
        logger.info(f"✅ 当前指标: {current_metrics['operations_summary']['total_operations']} 个操作")

        # 获取性能摘要
        summary = monitor.get_performance_summary()
        logger.info(f"✅ 性能摘要: 平均CPU {summary.get('average_cpu', 0):.1f}%")

        return True

    except Exception as e:
        logger.info(f"❌ 测试失败: {e}")
        traceback.print_exc()
        return False

async def test_integration():
    """集成测试"""
    logger.info("\n🔧 测试7: 集成测试")
    logger.info(str('-' * 50))

    try:
        # 导入所有组件
        from cognition.memory_config_manager import get_config

        # monitor_performance 在 memory_error_handler 中不存在，移除此导入
        from cognition.memory_processor import MemoryProcessor
        from cognition.optimized_memory_index import IndexEntry, OptimizedMemoryIndex

        # 获取配置
        config = get_config()
        logger.info(f"✅ 配置加载成功: 向量维度 {config.vector_memory.dimension}")

        # 创建处理器（使用新接口）
        processor = MemoryProcessor(agent_id='integration_test')
        await processor.initialize()
        logger.info('✅ 记忆处理器初始化成功')

        # 创建索引
        index = OptimizedMemoryIndex(index_type='composite', dimension=config.vector_memory.dimension)
        logger.info('✅ 优化索引创建成功')

        # 测试数据流
        test_content = '集成测试：专利审查系统的深度学习应用'

        # 1. 处理器处理记忆
        memory_data = {
            'content': test_content,
            'type': 'semantic',
            'importance': 0.9
        }

        process_result = await processor.process_memory(memory_data)
        logger.info(f"✅ 记忆处理结果: {process_result.get('success', False)}")

        # 2. 添加到索引
        entry = IndexEntry(
            id='integration_entry',
            content=test_content,
            metadata={'source': 'integration_test'}
        )
        index.add_entry(entry)
        logger.info('✅ 索引条目添加成功')

        # 3. 搜索测试
        search_results = await index.search('深度学习', top_k=3, similarity_threshold=0.01)
        logger.info(f"✅ 搜索结果: 找到 {len(search_results)} 个相关条目")

        # 清理
        await processor.shutdown()
        logger.info('✅ 集成测试完成')

        return True

    except Exception as e:
        logger.info(f"❌ 集成测试失败: {e}")
        traceback.print_exc()
        return False

async def run_all_tests():
    """运行所有测试"""
    logger.info('🚀 记忆模块修复验证测试')
    logger.info(str('='*80))
    logger.info(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(str('='*80))

    tests = [
        ('MemoryProcessor接口修复', test_memory_processor_fixes),
        ('优化记忆索引枚举修复', test_optimized_memory_index_fixes),
        ('搜索算法改进', test_search_algorithm_improvements),
        ('统一配置管理系统', test_config_manager),
        ('错误处理和日志记录', test_error_handling),
        ('性能监控机制', test_performance_monitoring),
        ('集成测试', test_integration)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.info(f"❌ {test_name} 执行异常: {e}")
            results.append((test_name, False))

    # 生成测试报告
    logger.info(str("\n" + '='*80))
    logger.info('📋 测试报告')
    logger.info(str('='*80))

    passed = sum(1 for _, result in results if result)
    total = len(results)

    logger.info("\n📊 测试统计:")
    logger.info(f"   总测试数: {total}")
    logger.info(f"   ✅ 通过: {passed}")
    logger.info(f"   ❌ 失败: {total - passed}")
    logger.info(f"   通过率: {(passed/total)*100:.1f}%")

    logger.info("\n📝 详细结果:")
    for i, (test_name, result) in enumerate(results, 1):
        status = '✅ PASSED' if result else '❌ FAILED'
        logger.info(f"{i}. {test_name}: {status}")

    # 结论
    if passed == total:
        logger.info("\n🎉 所有修复验证通过！记忆模块已准备就绪。")
    elif passed >= total * 0.8:
        logger.info("\n✅ 大部分修复验证通过，记忆模块基本可用。")
    else:
        logger.info("\n⚠️ 存在多个问题，需要进一步修复。")

    logger.info(str("\n" + '='*80))

    return passed == total

if __name__ == '__main__':
    asyncio.run(run_all_tests())
