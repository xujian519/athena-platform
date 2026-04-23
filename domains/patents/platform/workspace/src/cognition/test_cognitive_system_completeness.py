#!/usr/bin/env python3
"""
认知系统完整性测试
Cognitive System Completeness Test

验证认知与决策模块的所有组件功能

作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# 添加路径
sys.path.append(str(Path(__file__).parent))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CognitiveSystemTester:
    """认知系统测试器"""

    def __init__(self):
        self.test_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_details': []
        }

    async def run_all_tests(self):
        """运行所有测试"""
        logger.info('🚀 开始认知系统完整性测试')
        logger.info('='*60)

        # 测试1: 认知状态管理器
        await self.test_cognitive_state_manager()

        # 测试2: 增强决策引擎
        await self.test_enhanced_decision_engine()

        # 测试3: 神经元链同步器
        await self.test_neural_chain_synchronizer()

        # 测试4: 记忆处理器
        await self.test_memory_processor()

        # 测试5: 日志系统
        await self.test_logging_system()

        # 测试6: 特征提取器
        await self.test_feature_extractor()

        # 测试7: 集成测试
        await self.test_integration()

        # 生成测试报告
        self.generate_test_report()

    async def test_cognitive_state_manager(self):
        """测试认知状态管理器"""
        logger.info("\n📋 测试1: 认知状态管理器")
        logger.info('-'*40)

        try:
            from cognitive_state_manager import (
                CognitiveState,
                CognitiveStateManager,
            )

            # 创建状态管理器
            manager = CognitiveStateManager()

            # 测试状态转换
            await manager.transition_to(CognitiveState.IDLE, trigger='test')
            assert manager.get_current_state() == CognitiveState.IDLE
            self.log_test_pass('状态转换测试')

            # 测试错误处理
            try:
                raise ValueError('测试错误')
            except Exception as e:
                result = await manager.handle_error(e, {'test': True})
                assert result
                self.log_test_pass('错误处理测试')

            # 测试性能报告
            report = manager.get_performance_report()
            assert 'current_state' in report
            self.log_test_pass('性能报告测试')

            # 清理
            await manager.shutdown()

        except Exception as e:
            self.log_test_fail(f"认知状态管理器测试失败: {e}")

    async def test_enhanced_decision_engine(self):
        """测试增强决策引擎"""
        logger.info("\n📋 测试2: 增强决策引擎")
        logger.info('-'*40)

        try:
            from enhanced_decision_engine import (
                DecisionAlternative,
                DecisionContext,
                DecisionFactor,
                DecisionLevel,
                DecisionType,
                EnhancedDecisionEngine,
            )

            # 创建决策引擎
            engine = EnhancedDecisionEngine()

            # 创建测试备选方案
            alternatives = [
                DecisionAlternative(
                    id='alt1',
                    name='方案A',
                    description='测试方案A',
                    factors=[
                        DecisionFactor('novelty', 0.8, 0.85, 0.9, 'test'),
                        DecisionFactor('practical', 0.7, 0.75, 0.8, 'test')
                    ],
                    expected_outcome={'benefit': 0.8},
                    risk_assessment={'risk': 0.2},
                    implementation_cost=1000,
                    time_to_implement=10
                )
            ]

            # 创建决策上下文
            context = DecisionContext(
                decision_type=DecisionType.PATENT_VALIDITY,
                decision_level=DecisionLevel.TACTICAL,
                urgency=0.5,
                available_resources={'budget': 10000},
                constraints=['无特殊约束'],
                stakeholders=['测试者'],
                time_horizon='short',
                previous_decisions=[]
            )

            # 训练模型
            training_data = [
                {
                    'features': {'novelty': 0.8, 'practical': 0.7},
                    'outcome': 1
                }
            ]
            await engine.train_models(training_data)
            self.log_test_pass('决策模型训练测试')

            # 执行决策
            decision = await engine.make_decision(context, alternatives)
            assert decision.decision_type == DecisionType.PATENT_VALIDITY
            self.log_test_pass('决策执行测试')

            # 测试性能报告
            report = engine.get_performance_report()
            assert 'metrics' in report
            self.log_test_pass('决策引擎性能报告测试')

        except Exception as e:
            self.log_test_fail(f"增强决策引擎测试失败: {e}")

    async def test_neural_chain_synchronizer(self):
        """测试神经元链同步器"""
        logger.info("\n📋 测试3: 神经元链同步器")
        logger.info('-'*40)

        try:
            from neural_chain_synchronizer import (
                ConsistencyLevel,
                NeuralChainSynchronizer,
                NeuralNode,
                SyncMode,
            )

            # 创建同步器
            synchronizer = NeuralChainSynchronizer(
                sync_mode=SyncMode.SYNCHRONOUS,
                consistency_level=ConsistencyLevel.EVENTUAL
            )

            # 创建测试神经元
            neuron1 = NeuralNode('test_neuron1', 'input')
            neuron2 = NeuralNode('test_neuron2', 'output')

            # 添加神经元
            synchronizer.add_neuron(neuron1)
            synchronizer.add_neuron(neuron2)
            self.log_test_pass('神经元添加测试')

            # 启动同步器
            await synchronizer.start_all()
            self.log_test_pass('同步器启动测试')

            # 创建同步组
            await synchronizer.create_sync_group('test_group', ['test_neuron1', 'test_neuron2'])
            self.log_test_pass('同步组创建测试')

            # 测试同步
            sync_result = await synchronizer.synchronize_group('test_group')
            assert sync_result
            self.log_test_pass('组同步测试')

            # 停止同步器
            await synchronizer.stop_all()

        except Exception as e:
            self.log_test_fail(f"神经元链同步器测试失败: {e}")

    async def test_memory_processor(self):
        """测试记忆处理器"""
        logger.info("\n📋 测试4: 记忆处理器")
        logger.info('-'*40)

        try:
            from memory_processor import MemoryProcessor, MemoryType, RetrievalCue

            # 创建记忆处理器
            processor = MemoryProcessor(':memory:')  # 使用内存数据库

            # 启动后台任务
            await processor.start_background_tasks()
            self.log_test_pass('记忆处理器启动测试')

            # 存储记忆
            memory_id = await processor.store_memory(
                content={'test': '记忆内容'},
                memory_type=MemoryType.EPISODIC,
                tags=['测试'],
                importance=0.8
            )
            assert memory_id is not None
            self.log_test_pass('记忆存储测试')

            # 检索记忆
            cue = RetrievalCue(
                cue_id='test_cue',
                query='测试',
                memory_types=[MemoryType.EPISODIC],
                tags=['测试'],
                max_results=10
            )

            result = await processor.retrieve_memory(cue)
            assert len(result.matched_traces) > 0
            self.log_test_pass('记忆检索测试')

            # 获取统计信息
            stats = processor.get_memory_statistics()
            assert 'working_memory' in stats
            self.log_test_pass('记忆统计测试')

            # 停止后台任务
            await processor.stop_background_tasks()
            processor.close()

        except Exception as e:
            self.log_test_fail(f"记忆处理器测试失败: {e}")

    async def test_logging_system(self):
        """测试日志系统"""
        logger.info("\n📋 测试5: 日志系统")
        logger.info('-'*40)

        try:
            from logging_system import CognitiveLogger, LogCategory

            # 创建日志管理器
            log_manager = CognitiveLogger('TestComponent')

            # 启动日志管理器
            await log_manager.start()
            self.log_test_pass('日志管理器启动测试')

            # 测试日志记录
            log_manager.info('测试信息日志', category=LogCategory.SYSTEM)
            log_manager.error('测试错误日志', category=LogCategory.ERROR)
            self.log_test_pass('日志记录测试')

            # 测试错误处理
            try:
                raise Exception('测试异常')
            except Exception as e:
                error_id = await log_manager.handle_error(e, {'test': True})
                assert error_id is not None
                self.log_test_pass('错误处理测试')

            # 测试性能计时
            log_manager.start_timer('test_timer')
            await asyncio.sleep(0.01)
            duration = log_manager.end_timer('test_timer')
            assert duration > 0
            self.log_test_pass('性能计时测试')

            # 停止日志管理器
            await log_manager.stop()

        except Exception as e:
            self.log_test_fail(f"日志系统测试失败: {e}")

    async def test_feature_extractor(self):
        """测试特征提取器"""
        logger.info("\n📋 测试6: 特征提取器")
        logger.info('-'*40)

        try:
            from enhanced_patent_feature_extractor import PatentCognitiveProcessor

            # 创建特征提取器
            processor = PatentCognitiveProcessor()

            # 初始化处理器
            await processor.initialize()
            self.log_test_pass('特征提取器初始化测试')

            # 测试文本处理
            test_text = """
            本发明涉及一种智能系统，包括：数据采集模块，用于获取数据；
            处理模块，用于处理数据；输出模块，用于输出结果。
            该系统能够提高处理效率，改善性能。
            """

            result = await processor.process_patent_text(test_text)
            assert 'features' in result
            assert len(result['features']) > 0
            self.log_test_pass('特征提取测试')

            # 检查分析结果
            assert 'analysis' in result
            assert 'cognitive_understanding' in result
            self.log_test_pass('认知理解测试')

        except Exception as e:
            self.log_test_fail(f"特征提取器测试失败: {e}")

    async def test_integration(self):
        """集成测试"""
        logger.info("\n📋 测试7: 集成测试")
        logger.info('-'*40)

        try:
            # 这里测试各组件之间的协作
            logger.info('测试组件协作...')

            # 模拟完整的认知处理流程
            # 1. 使用日志管理器记录开始
            from logging_system import CognitiveLogger
            log_manager = CognitiveLogger('IntegrationTest')
            await log_manager.start()

            log_manager.info('开始集成测试')

            # 2. 使用状态管理器管理处理状态
            from cognitive_state_manager import CognitiveState, CognitiveStateManager
            state_manager = CognitiveStateManager()
            await state_manager.transition_to(CognitiveState.PROCESSING, trigger='integration_test')

            # 3. 使用记忆处理器存储上下文
            from memory_processor import MemoryProcessor, MemoryType
            memory_processor = MemoryProcessor(':memory:')
            await memory_processor.start_background_tasks()

            await memory_processor.store_memory(
                content={'test_context': '集成测试上下文'},
                memory_type=MemoryType.WORKING,
                tags=['集成测试']
            )

            # 4. 使用决策引擎做出简单决策
            from enhanced_decision_engine import (
                DecisionAlternative,
                DecisionContext,
                DecisionFactor,
                DecisionLevel,
                DecisionType,
                EnhancedDecisionEngine,
            )
            decision_engine = EnhancedDecisionEngine()

            alternatives = [
                DecisionAlternative(
                    id='integration_alt',
                    name='集成测试方案',
                    description='测试方案',
                    factors=[
                        DecisionFactor('test_factor', 1.0, 0.8, 0.9, 'integration_test')
                    ],
                    expected_outcome={'success': 0.9},
                    risk_assessment={'risk': 0.1},
                    implementation_cost=100,
                    time_to_implement=1
                )
            ]

            context = DecisionContext(
                decision_type=DecisionType.STRATEGIC_PLANNING,
                decision_level=DecisionLevel.OPERATIONAL,
                urgency=0.5,
                available_resources={'test': 1},
                constraints=['测试约束'],
                stakeholders=['测试者'],
                time_horizon='short',
                previous_decisions=[]
            )

            decision = await decision_engine.make_decision(context, alternatives)
            assert decision.decision_type == DecisionType.STRATEGIC_PLANNING

            # 5. 使用特征提取器分析结果
            from enhanced_patent_feature_extractor import PatentCognitiveProcessor
            feature_processor = PatentCognitiveProcessor()
            await feature_processor.initialize()

            await feature_processor.process_patent_text(
                f"集成测试决策结果: {decision.selected_alternative.name}"
            )

            # 6. 完成处理
            await state_manager.transition_to(CognitiveState.IDLE, trigger='integration_complete')

            # 清理资源
            await memory_processor.stop_background_tasks()
            memory_processor.close()
            await state_manager.shutdown()
            await log_manager.stop()

            self.log_test_pass('集成测试完成')

        except Exception as e:
            self.log_test_fail(f"集成测试失败: {e}")

    def log_test_pass(self, test_name: str):
        """记录测试通过"""
        logger.info(f"✅ {test_name}")
        self.test_results['passed_tests'] += 1

    def log_test_fail(self, test_name: str):
        """记录测试失败"""
        logger.error(f"❌ {test_name}")
        self.test_results['failed_tests'] += 1
        self.test_results['test_details'].append({
            'test': test_name,
            'status': 'FAILED',
            'timestamp': datetime.now().isoformat()
        })

    def generate_test_report(self):
        """生成测试报告"""
        self.test_results['total_tests'] = self.test_results['passed_tests'] + self.test_results['failed_tests']
        success_rate = (self.test_results['passed_tests'] / self.test_results['total_tests'] * 100) if self.test_results['total_tests'] > 0 else 0

        logger.info("\n" + '='*60)
        logger.info('📊 认知系统完整性测试报告')
        logger.info('='*60)
        logger.info(f"总测试数: {self.test_results['total_tests']}")
        logger.info(f"通过测试: {self.test_results['passed_tests']}")
        logger.info(f"失败测试: {self.test_results['failed_tests']}")
        logger.info(f"成功率: {success_rate:.1f}%")

        if self.test_results['failed_tests'] > 0:
            logger.error("\n失败的测试:")
            for detail in self.test_results['test_details']:
                logger.error(f"  - {detail['test']}")

        # 保存报告到文件
        report_file = Path('cognitive_system_test_report.json')
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                'test_summary': {
                    'total_tests': self.test_results['total_tests'],
                    'passed_tests': self.test_results['passed_tests'],
                    'failed_tests': self.test_results['failed_tests'],
                    'success_rate': success_rate,
                    'timestamp': datetime.now().isoformat()
                },
                'test_details': self.test_results['test_details']
            }, f, ensure_ascii=False, indent=2)

        logger.info(f"\n📄 测试报告已保存到: {report_file}")

        # 结论
        if success_rate >= 80:
            logger.info("\n🎉 认知系统完整性验证通过！")
        else:
            logger.error("\n⚠️ 认知系统存在一些问题，需要进一步优化。")

async def main():
    """主函数"""
    logger.info('🧠 认知与决策模块完整性验证')
    logger.info(str('='*60))

    tester = CognitiveSystemTester()
    await tester.run_all_tests()

if __name__ == '__main__':
    asyncio.run(main())
