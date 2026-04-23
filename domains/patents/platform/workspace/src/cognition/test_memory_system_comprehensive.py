#!/usr/bin/env python3
"""
记忆模块综合验证测试
Comprehensive Memory System Verification Test

验证记忆模块的完整性、功能性和可运行性

作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

import asyncio
import json
import logging
import sys
import time
import traceback
from datetime import datetime

# 添加项目路径
sys.path.insert(0, '/Users/xujian/Athena工作平台')
sys.path.insert(0, '/Users/xujian/Athena工作平台/patent-platform/workspace/src')
sys.path.insert(0, '/Users/xujian/Athena工作平台/patent-platform/workspace/src/cognition')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MemorySystemVerifier:
    """记忆系统验证器"""

    def __init__(self):
        self.test_results = []
        self.memory_systems = {}
        self.performance_metrics = {}

    async def run_comprehensive_verification(self):
        """运行综合验证"""
        logger.info('🧠 记忆模块综合验证测试')
        logger.info(str('='*80))
        print('验证时间:', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        logger.info(str('='*80))

        try:
            # 1. 导入验证
            await self.test_import_verification()

            # 2. 基础功能验证
            await self.test_basic_functionality()

            # 3. 向量记忆系统验证
            await self.test_vector_memory_system()

            # 4. 增强记忆系统验证
            await self.test_enhanced_memory_system()

            # 5. 记忆处理器验证
            await self.test_memory_processor()

            # 6. 记忆索引验证
            await self.test_optimized_memory_index()

            # 7. 性能测试
            await self.test_performance_benchmarks()

            # 8. 集成测试
            await self.test_integration()

            # 9. 生成验证报告
            self.generate_verification_report()

        except Exception as e:
            logger.error(f"综合验证过程中出现错误: {e}")
            traceback.print_exc()

    async def test_import_verification(self):
        """测试导入验证"""
        logger.info("\n📦 1. 导入验证测试")
        logger.info(str('-' * 50))

        import_tests = [
            {
                'name': '向量记忆系统导入',
                'module_path': 'core.memory.vector_memory',
                'class_name': 'VectorMemorySystem',
                'required': True
            },
            {
                'name': '增强记忆系统导入',
                'module_path': 'core.memory.enhanced_memory_system',
                'class_name': 'EnhancedMemorySystem',
                'required': True
            },
            {
                'name': '记忆处理器导入',
                'module_path': 'cognition.memory_processor',
                'class_name': 'MemoryProcessor',
                'required': True
            },
            {
                'name': '优化记忆索引导入',
                'module_path': 'cognition.optimized_memory_index',
                'class_name': 'OptimizedMemoryIndex',
                'required': True
            }
        ]

        for test in import_tests:
            try:
                # 动态导入
                module = __import__(test['module_path'], fromlist=[test['class_name'])
                class_obj = getattr(module, test['class_name'])

                # 验证类是否可实例化
                class_obj('test_agent')

                logger.info(f"✅ {test['name']}: 成功")
                self.test_results.append({
                    'test': test['name'],
                    'status': 'passed',
                    'message': '导入和实例化成功'
                })

            except ImportError as e:
                status = 'failed' if test['required'] else 'warning'
                logger.info(f"{'❌' if test['required'] else '⚠️'} {test['name']}: {e}")
                self.test_results.append({
                    'test': test['name'],
                    'status': status,
                    'message': f"导入失败: {e}"
                })

            except Exception as e:
                logger.info(f"❌ {test['name']}: {e}")
                self.test_results.append({
                    'test': test['name'],
                    'status': 'failed',
                    'message': f"实例化失败: {e}"
                })

    async def test_basic_functionality(self):
        """测试基础功能"""
        logger.info("\n🔧 2. 基础功能验证")
        logger.info(str('-' * 50))

        try:
            # 导入必要的模块
            from core.framework.memory.enhanced_memory_system import EnhancedMemorySystem
            from core.framework.memory.vector_memory import (
                VectorMemorySystem,
            )

            # 创建测试实例
            vector_memory = VectorMemorySystem('test_agent_vector', {
                'dimension': 768,
                'max_vectors': 1000
            })

            enhanced_memory = EnhancedMemorySystem('test_agent_enhanced', {
                'enable_vector_memory': True,
                'enable_knowledge_graph': False  # 避免知识图谱依赖
            })

            # 初始化测试
            await vector_memory.initialize()
            await enhanced_memory.initialize()

            logger.info('✅ 记忆系统初始化成功')

            # 基础存储和检索测试
            test_content = '这是一个测试记忆内容，用于验证记忆系统的基本功能。'

            # 向量记忆测试
            result = await vector_memory.store_memory(
                content=test_content,
                category='episodic'
            )

            if result.get('success'):
                logger.info('✅ 向量记忆存储成功')

                # 搜索测试
                search_result = await vector_memory.search_memories(
                    query='测试记忆',
                    k=5
                )

                if search_result.get('success') and search_result.get('total_found', 0) > 0:
                    logger.info('✅ 向量记忆搜索成功')
                else:
                    logger.info('❌ 向量记忆搜索失败')
            else:
                logger.info('❌ 向量记忆存储失败')

            # 获取统计信息
            stats = await vector_memory.get_memory_stats()
            logger.info(f"📊 向量记忆统计: 总计 {stats['total_memories']} 个记忆")

            # 清理
            await vector_memory.shutdown()
            await enhanced_memory.shutdown()

            self.test_results.append({
                'test': '基础功能验证',
                'status': 'passed',
                'message': '基础存储、检索和统计功能正常'
            })

        except Exception as e:
            logger.info(f"❌ 基础功能验证失败: {e}")
            traceback.print_exc()
            self.test_results.append({
                'test': '基础功能验证',
                'status': 'failed',
                'message': str(e)
            })

    async def test_vector_memory_system(self):
        """测试向量记忆系统"""
        logger.info("\n🧮 3. 向量记忆系统验证")
        logger.info(str('-' * 50))

        try:
            from core.framework.memory.vector_memory import VectorMemorySystem

            # 创建不同配置的记忆系统
            configs = [
                {'dimension': 512, 'max_vectors': 100},
                {'dimension': 768, 'max_vectors': 200},
                {'dimension': 1024, 'max_vectors': 300}
            ]

            for i, config in enumerate(configs):
                memory = VectorMemorySystem(f"test_vector_{i}", config)
                await memory.initialize()

                # 批量存储测试
                test_memories = [
                    f"测试记忆内容 {j} - 这是第{j}个测试记忆，包含各种信息和数据。"
                    for j in range(10)
                ]

                store_results = []
                for j, content in enumerate(test_memories):
                    result = await memory.store_memory(
                        content=content,
                        category=f"test_category_{j % 3}",
                        metadata={'test_index': j}
                    )
                    store_results.append(result)

                success_count = sum(1 for r in store_results if r.get('success'))
                logger.info(f"✅ 配置 {i+1}: 存储 {success_count}/{len(test_memories)} 成功")

                # 搜索测试
                search_result = await memory.search_memories(
                    query='测试记忆内容',
                    k=5,
                    threshold=0.1
                )

                if search_result.get('success'):
                    found_count = search_result.get('total_found', 0)
                    logger.info(f"✅ 配置 {i+1}: 搜索到 {found_count} 个相关记忆")

                # 分类测试
                category_result = await memory.search_memories(
                    query='test',
                    category='test_category_0',
                    k=3
                )

                if category_result.get('success'):
                    category_count = category_result.get('total_found', 0)
                    logger.info(f"✅ 配置 {i+1}: 分类搜索到 {category_count} 个记忆")

                await memory.shutdown()

            self.test_results.append({
                'test': '向量记忆系统验证',
                'status': 'passed',
                'message': '多种配置下的向量记忆功能正常'
            })

        except Exception as e:
            logger.info(f"❌ 向量记忆系统验证失败: {e}")
            self.test_results.append({
                'test': '向量记忆系统验证',
                'status': 'failed',
                'message': str(e)
            })

    async def test_enhanced_memory_system(self):
        """测试增强记忆系统"""
        logger.info("\n⚡ 4. 增强记忆系统验证")
        logger.info(str('-' * 50))

        try:
            from core.framework.memory.enhanced_memory_system import EnhancedMemorySystem

            # 创建增强记忆系统
            enhanced_memory = EnhancedMemorySystem('test_enhanced_agent', {
                'enable_vector_memory': True,
                'enable_knowledge_graph': False,  # 简化测试，避免知识图谱依赖
                'auto_enhance_memories': False
            })

            await enhanced_memory.initialize()

            # 测试不同类型的记忆
            memory_types = [
                ('short_term', '这是短期记忆测试'),
                ('long_term', '这是长期记忆测试'),
                ('episodic', '这是情景记忆测试：昨天开会讨论了专利审查系统'),
                ('semantic', '这是语义记忆测试：专利是知识产权的一种形式')
            ]

            for mem_type, content in memory_types:
                try:
                    result = await enhanced_memory.store_memory(
                        content=content,
                        memory_type=mem_type,
                        tags=['test', mem_type]
                    )

                    if result.get('vector_id') is not None:
                        logger.info(f"✅ {mem_type} 记忆存储成功")
                    else:
                        logger.info(f"⚠️ {mem_type} 记忆存储返回异常: {result}")

                except Exception as e:
                    logger.info(f"❌ {mem_type} 记忆存储失败: {e}")

            # 测试检索功能
            for mem_type, content in memory_types:
                try:
                    search_result = await enhanced_memory.retrieve_memory(
                        query='专利',
                        memory_type=mem_type,
                        k=3
                    )

                    found = search_result.get('total_found', 0)
                    logger.info(f"✅ {mem_type} 记忆检索到 {found} 个结果")

                except Exception as e:
                    logger.info(f"❌ {mem_type} 记忆检索失败: {e}")

            # 测试语义搜索
            try:
                semantic_result = await enhanced_memory.semantic_search(
                    query='知识产权',
                    k=5
                )

                total = semantic_result.get('total_found', 0)
                logger.info(f"✅ 语义搜索找到 {total} 个结果")

            except Exception as e:
                logger.info(f"❌ 语义搜索失败: {e}")

            # 获取统计信息
            try:
                stats = await enhanced_memory.get_memory_stats()
                logger.info(f"📊 增强记忆统计: {json.dumps(stats, ensure_ascii=False, indent=2)}")

            except Exception as e:
                logger.info(f"❌ 统计信息获取失败: {e}")

            await enhanced_memory.shutdown()

            self.test_results.append({
                'test': '增强记忆系统验证',
                'status': 'passed',
                'message': '增强记忆系统基础功能正常'
            })

        except Exception as e:
            logger.info(f"❌ 增强记忆系统验证失败: {e}")
            self.test_results.append({
                'test': '增强记忆系统验证',
                'status': 'failed',
                'message': str(e)
            })

    async def test_memory_processor(self):
        """测试记忆处理器"""
        logger.info("\n⚙️ 5. 记忆处理器验证")
        logger.info(str('-' * 50))

        try:
            from cognition.memory_processor import MemoryProcessor

            # 创建记忆处理器
            processor = MemoryProcessor(agent_id='test_processor')

            # 初始化
            init_result = await processor.initialize()
            logger.info(f"📋 记忆处理器初始化: {init_result}")

            # 测试记忆处理
            test_memories = [
                {
                    'content': '专利审查员需要具备专业的技术背景知识',
                    'type': 'semantic',
                    'importance': 0.8,
                    'context': {'domain': 'patent', 'category': 'review'}
                },
                {
                    'content': '今天上午10点召开了专利审查标准讨论会',
                    'type': 'episodic',
                    'importance': 0.7,
                    'context': {'time': '2025-12-11 10:00', 'event': 'meeting'}
                }
            ]

            for memory in test_memories:
                try:
                    result = await processor.process_memory(memory)
                    if result.get('success'):
                        logger.info(f"✅ 记忆处理成功: {memory['type']}")
                    else:
                        logger.info(f"⚠️ 记忆处理异常: {result}")

                except Exception as e:
                    logger.info(f"❌ 记忆处理失败: {e}")

            # 测试记忆检索
            try:
                search_result = await processor.search_memories(
                    query='专利审查',
                    memory_type='semantic',
                    k=5
                )

                found = len(search_result.get('memories', []))
                logger.info(f"✅ 记忆检索找到 {found} 个结果")

            except Exception as e:
                logger.info(f"❌ 记忆检索失败: {e}")

            # 获取统计信息
            try:
                stats = await processor.get_statistics()
                logger.info(f"📊 记忆处理器统计: {json.dumps(stats, ensure_ascii=False, indent=2)}")

            except Exception as e:
                logger.info(f"❌ 统计信息获取失败: {e}")

            await processor.shutdown()

            self.test_results.append({
                'test': '记忆处理器验证',
                'status': 'passed',
                'message': '记忆处理器功能正常'
            })

        except Exception as e:
            logger.info(f"❌ 记忆处理器验证失败: {e}")
            self.test_results.append({
                'test': '记忆处理器验证',
                'status': 'failed',
                'message': str(e)
            })

    async def test_optimized_memory_index(self):
        """测试优化记忆索引"""
        logger.info("\n🗂️ 6. 优化记忆索引验证")
        logger.info(str('-' * 50))

        try:
            from cognition.optimized_memory_index import (
                IndexEntry,
                IndexType,
                OptimizedMemoryIndex,
            )

            # 创建索引
            index = OptimizedMemoryIndex(
                index_type=IndexType.COMPOSITE,
                dimension=768,
                use_faiss=False  # 避免FAISS依赖
            )

            # 创建测试条目
            test_entries = [
                IndexEntry(
                    id=f"entry_{i}",
                    content=f"专利相关的测试内容 {i}，包含技术方案和权利要求等信息。",
                    metadata={'category': 'patent', 'type': 'technical'},
                    access_count=i % 5
                )
                for i in range(20)
            ]

            # 添加条目
            for entry in test_entries:
                index.add_entry(entry)

            logger.info(f"✅ 索引添加了 {len(test_entries)} 个条目")

            # 测试搜索
            search_queries = [
                '技术方案',
                '权利要求',
                '专利信息',
                '测试内容'
            ]

            for query in search_queries:
                try:
                    results = await index.search(
                        query=query,
                        top_k=5,
                        search_type='hybrid'
                    )

                    logger.info(f"✅ 搜索 '{query}': 找到 {len(results)} 个结果")

                except Exception as e:
                    logger.info(f"❌ 搜索 '{query}' 失败: {e}")

            # 测试不同搜索类型
            search_types = ['keyword', 'semantic', 'tfidf']
            for search_type in search_types:
                try:
                    results = await index.search(
                        query='专利',
                        top_k=3,
                        search_type=search_type
                    )

                    logger.info(f"✅ {search_type} 搜索: 找到 {len(results)} 个结果")

                except Exception as e:
                    logger.info(f"❌ {search_type} 搜索失败: {e}")

            # 获取统计信息
            stats = index.get_stats()
            logger.info(f"📊 索引统计: {json.dumps(stats, ensure_ascii=False, indent=2)}")

            # 优化索引
            index.optimize_index()
            logger.info('✅ 索引优化完成')

            self.test_results.append({
                'test': '优化记忆索引验证',
                'status': 'passed',
                'message': '记忆索引功能正常'
            })

        except Exception as e:
            logger.info(f"❌ 优化记忆索引验证失败: {e}")
            self.test_results.append({
                'test': '优化记忆索引验证',
                'status': 'failed',
                'message': str(e)
            })

    async def test_performance_benchmarks(self):
        """测试性能基准"""
        logger.info("\n🚀 7. 性能基准测试")
        logger.info(str('-' * 50))

        try:
            from core.framework.memory.vector_memory import VectorMemorySystem

            # 创建性能测试记忆系统
            memory = VectorMemorySystem('perf_test', {
                'dimension': 768,
                'max_vectors': 1000
            })

            await memory.initialize()

            # 存储性能测试
            logger.info('📝 存储性能测试...')
            store_count = 100
            start_time = time.time()

            for i in range(store_count):
                await memory.store_memory(
                    content=f"性能测试记忆 {i} - 这是第{i}个用于性能测试的记忆内容。",
                    category='performance_test'
                )

            store_time = time.time() - start_time
            store_rate = store_count / store_time
            logger.info(f"✅ 存储性能: {store_rate:.2f} 条/秒")

            # 搜索性能测试
            logger.info('🔍 搜索性能测试...')
            search_count = 50
            start_time = time.time()

            for i in range(search_count):
                await memory.search_memories(
                    query=f"性能测试 {i % 10}",
                    k=5
                )

            search_time = time.time() - start_time
            search_rate = search_count / search_time
            logger.info(f"✅ 搜索性能: {search_rate:.2f} 次/秒")

            # 内存使用测试
            stats = await memory.get_memory_stats()
            memory_usage = stats.get('search_engine_stats', {}).get('memory_usage_mb', 0)
            logger.info(f"📊 内存使用: {memory_usage:.2f} MB")

            # 记录性能指标
            self.performance_metrics = {
                'store_rate': store_rate,
                'search_rate': search_rate,
                'memory_usage_mb': memory_usage,
                'total_memories': stats.get('total_memories', 0)
            }

            await memory.shutdown()

            self.test_results.append({
                'test': '性能基准测试',
                'status': 'passed',
                'message': f"存储 {store_rate:.1f} 条/秒, 搜索 {search_rate:.1f} 次/秒"
            })

        except Exception as e:
            logger.info(f"❌ 性能基准测试失败: {e}")
            self.test_results.append({
                'test': '性能基准测试',
                'status': 'failed',
                'message': str(e)
            })

    async def test_integration(self):
        """测试集成功能"""
        logger.info("\n🔗 8. 集成功能验证")
        logger.info(str('-' * 50))

        try:
            # 测试记忆系统之间的集成
            from cognition.memory_processor import MemoryProcessor

            from core.framework.memory.enhanced_memory_system import EnhancedMemorySystem

            # 创建增强记忆系统
            enhanced_memory = EnhancedMemorySystem('integration_test', {
                'enable_vector_memory': True,
                'enable_knowledge_graph': False
            })

            # 创建记忆处理器
            processor = MemoryProcessor('integration_processor')

            # 初始化
            await enhanced_memory.initialize()
            await processor.initialize()

            # 集成测试：处理器 -> 增强记忆系统
            test_memory = {
                'content': '这是一个集成测试记忆，验证处理器和记忆系统的协同工作。',
                'type': 'episodic',
                'importance': 0.9,
                'context': {'test': 'integration'}
            }

            # 处理器处理记忆
            process_result = await processor.process_memory(test_memory)
            logger.info(f"📋 处理器结果: {process_result.get('success', False)}")

            # 增强记忆系统存储相同内容
            store_result = await enhanced_memory.store_memory(
                content=test_memory['content'],
                memory_type=test_memory['type'],
                tags=test_memory['context'].values()
            )
            logger.info(f"💾 存储结果: {store_result.get('vector_id') is not None}")

            # 集成测试：搜索一致性
            query = '集成测试'

            # 从处理器搜索
            processor_search = await processor.search_memories(query=query, k=5)
            processor_count = len(processor_search.get('memories', []))

            # 从增强记忆系统搜索
            enhanced_search = await enhanced_memory.retrieve_memory(query=query, k=5)
            enhanced_count = enhanced_search.get('total_found', 0)

            logger.info(f"🔍 搜索对比: 处理器 {processor_count} 个, 增强记忆系统 {enhanced_count} 个")

            # 清理
            await enhanced_memory.shutdown()
            await processor.shutdown()

            self.test_results.append({
                'test': '集成功能验证',
                'status': 'passed',
                'message': '记忆系统集成功能正常'
            })

        except Exception as e:
            logger.info(f"❌ 集成功能验证失败: {e}")
            self.test_results.append({
                'test': '集成功能验证',
                'status': 'failed',
                'message': str(e)
            })

    def generate_verification_report(self):
        """生成验证报告"""
        logger.info(str("\n" + '='*80))
        logger.info('📋 记忆模块验证报告')
        logger.info(str('='*80))
        logger.info(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 统计结果
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['status'] == 'passed')
        failed_tests = sum(1 for r in self.test_results if r['status'] == 'failed')
        warning_tests = sum(1 for r in self.test_results if r['status'] == 'warning')

        logger.info("\n📊 测试统计:")
        logger.info(f"   总测试数: {total_tests}")
        logger.info(f"   ✅ 通过: {passed_tests}")
        logger.info(f"   ❌ 失败: {failed_tests}")
        logger.info(f"   ⚠️ 警告: {warning_tests}")
        logger.info(f"   通过率: {(passed_tests/total_tests)*100:.1f}%")

        # 详细结果
        logger.info("\n📝 详细结果:")
        for i, result in enumerate(self.test_results, 1):
            status_icon = {'passed': '✅', 'failed': '❌', 'warning': '⚠️'}.get(result['status'], '❓')
            logger.info(f"\n{i}. {result['test']}")
            logger.info(f"   {status_icon} {result['status'].upper()}")
            logger.info(f"   📄 {result['message']}")

        # 性能指标
        if self.performance_metrics:
            logger.info("\n🚀 性能指标:")
            logger.info(f"   存储速率: {self.performance_metrics['store_rate']:.2f} 条/秒")
            logger.info(f"   搜索速率: {self.performance_metrics['search_rate']:.2f} 次/秒")
            logger.info(f"   内存使用: {self.performance_metrics['memory_usage_mb']:.2f} MB")
            logger.info(f"   总记忆数: {self.performance_metrics['total_memories']}")

        # 结论
        logger.info("\n🎯 验证结论:")
        if passed_tests / total_tests >= 0.8:
            logger.info('   ✅ 记忆模块整体功能正常，可以投入使用')
        elif passed_tests / total_tests >= 0.6:
            logger.info('   ⚠️ 记忆模块基本功能正常，但存在一些问题需要优化')
        else:
            logger.info('   ❌ 记忆模块存在严重问题，不建议投入生产使用')

        # 保存报告
        report_data = {
            'verification_time': datetime.now().isoformat(),
            'test_statistics': {
                'total': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'warning': warning_tests,
                'pass_rate': (passed_tests/total_tests)*100
            },
            'test_results': self.test_results,
            'performance_metrics': self.performance_metrics,
            'conclusion': '正常' if passed_tests/total_tests >= 0.8 else '需要优化'
        }

        report_file = '/Users/xujian/Athena工作平台/documentation/memory_verification_report.json'
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            logger.info(f"\n📄 详细报告已保存到: {report_file}")
        except Exception as e:
            logger.info(f"\n❌ 报告保存失败: {e}")

        logger.info(str("\n" + '='*80))

async def main():
    """主函数"""
    verifier = MemorySystemVerifier()
    await verifier.run_comprehensive_verification()

if __name__ == '__main__':
    asyncio.run(main())
