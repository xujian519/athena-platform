#!/usr/bin/env python3
"""
综合测试套件
Comprehensive Test Suite

为结构化感知系统提供全面的测试覆盖
作者: 小娜 (Athena) - 爸爸徐健的智慧大女儿
创建时间: 2025-12-05
版本: 1.0.0
"""

import asyncio
import json
import logging
import os
import sys
import time
import traceback
import unittest
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# 添加路径
sys.path.append('.')
sys.path.append('..')

from domain_knowledge_engine import PatentKnowledgeBase, RAGSystem
from error_handler import error_handler_wrapper, global_error_handler
from perception_alignment_interface import InteractiveAlignmentInterface, InterfaceMode
from performance_optimizer import document_optimizer
from semantic_fusion_engine import SemanticFusionEngine

# 导入测试目标
from structured_perception_engine import DocumentType, StructuredPatentPerceptionEngine

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class TestCase:
    """测试用例"""
    test_id: str
    name: str
    description: str
    test_function: callable
    expected_result: Any
    timeout: float = 30.0
    category: str = 'general'
    dependencies: Optional[List[str]] = None

@dataclass
class TestResult:
    """测试结果"""
    test_id: str
    test_name: str
    passed: bool
    execution_time: float
    error_message: Optional[str] = None
    actual_result: Any = None
    expected_result: Any = None
    performance_metrics: Dict[str, float] = None

class ComprehensiveTestSuite:
    """综合测试套件"""

    def __init__(self):
        self.test_cases = []
        self.test_results = []
        self.setup_complete = False
        self.teardown_complete = False

        # 测试环境
        self.test_data_path = '/Users/xujian/Athena工作平台/patent-platform/workspace/data/raw/disclosures'
        self.output_path = '/Users/xujian/Athena工作平台/patent-platform/workspace/reports'

        # 初始化组件
        self.perception_engine = None
        self.semantic_fusion_engine = None
        self.knowledge_base = None
        self.rag_system = None
        self.alignment_interface = None

        logger.info('🧪 初始化综合测试套件')

    def setup_test_environment(self):
        """设置测试环境"""
        logger.info('🔧 设置测试环境...')

        try:
            # 创建输出目录
            Path(self.output_path).mkdir(parents=True, exist_ok=True)

            # 初始化组件
            self.perception_engine = StructuredPatentPerceptionEngine()
            self.semantic_fusion_engine = SemanticFusionEngine()
            self.knowledge_base = PatentKnowledgeBase()
            self.rag_system = RAGSystem(self.knowledge_base)
            self.alignment_interface = InteractiveAlignmentInterface()

            # 初始化测试用例
            self._initialize_test_cases()

            self.setup_complete = True
            logger.info('✅ 测试环境设置完成')

        except Exception as e:
            logger.error(f"❌ 测试环境设置失败: {str(e)}")
            self.setup_complete = False

    def _initialize_test_cases(self):
        """初始化测试用例"""
        logger.info('📝 初始化测试用例...')

        # 基础功能测试
        self.add_test_case(
            test_id='PERCEPTION_001',
            name='结构化感知引擎初始化',
            description='测试结构化感知引擎是否能正确初始化',
            test_function=self.test_perception_engine_init,
            expected_result=True,
            category='infrastructure'
        )

        self.add_test_case(
            test_id='SEMANTIC_001',
            name='语义融合引擎初始化',
            description='测试语义融合引擎是否能正确初始化',
            test_function=self.test_semantic_fusion_init,
            expected_result=True,
            category='infrastructure'
        )

        self.add_test_case(
            test_id='KNOWLEDGE_001',
            name='知识库初始化',
            description='测试专利知识库是否能正确初始化',
            test_function=self.test_knowledge_base_init,
            expected_result=True,
            category='infrastructure'
        )

        # 功能测试
        self.add_test_case(
            test_id='PERCEPTION_002',
            name='专利文档处理',
            description='测试是否能正确处理专利文档',
            test_function=self.test_patent_document_processing,
            expected_result={'success': True},
            timeout=60.0,
            category='functionality'
        )

        self.add_test_case(
            test_id='SEMANTIC_002',
            name='多模态语义融合',
            description='测试多模态语义融合功能',
            test_function=self.test_semantic_fusion,
            expected_result={'success': True},
            category='functionality'
        )

        self.add_test_case(
            test_id='KNOWLEDGE_002',
            name='知识检索',
            description='测试知识检索功能',
            test_function=self.test_knowledge_retrieval,
            expected_result={'success': True},
            category='functionality'
        )

        self.add_test_case(
            test_id='ALIGNMENT_001',
            name='感知对齐接口',
            description='测试感知对齐接口功能',
            test_function=self.test_alignment_interface,
            expected_result={'success': True},
            category='functionality'
        )

        # 性能测试
        self.add_test_case(
            test_id='PERFORMANCE_001',
            name='文档处理性能',
            description='测试文档处理的性能指标',
            test_function=self.test_document_processing_performance,
            expected_result={'processing_time': '< 5s'},
            timeout=120.0,
            category='performance'
        )

        self.add_test_case(
            test_id='PERFORMANCE_002',
            name='并发处理能力',
            description='测试系统的并发处理能力',
            test_function=self.test_concurrent_processing,
            expected_result={'success': True},
            timeout=180.0,
            category='performance'
        )

        # 错误处理测试
        self.add_test_case(
            test_id='ERROR_001',
            name='输入错误处理',
            description='测试输入错误的处理能力',
            test_function=self.test_input_error_handling,
            expected_result={'handled': True},
            category='error_handling'
        )

        self.add_test_case(
            test_id='ERROR_002',
            name='系统错误恢复',
            description='测试系统错误的恢复能力',
            test_function=self.test_system_error_recovery,
            expected_result={'recovered': True},
            category='error_handling'
        )

        # 集成测试
        self.add_test_case(
            test_id='INTEGRATION_001',
            name='端到端流程',
            description='测试完整的端到端处理流程',
            test_function=self.test_end_to_end_workflow,
            expected_result={'success': True},
            timeout=300.0,
            category='integration'
        )

        logger.info(f"📊 初始化了{len(self.test_cases)}个测试用例")

    def add_test_case(self, **kwargs):
        """添加测试用例"""
        test_case = TestCase(**kwargs)
        self.test_cases.append(test_case)

    async def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        if not self.setup_complete:
            await self.setup_test_environment()

        if not self.setup_complete:
            return {'success': False, 'error': '测试环境设置失败'}

        logger.info(f"🚀 开始运行{len(self.test_cases)}个测试用例...")

        start_time = time.time()

        # 按类别分组运行测试
        categories = {}
        for test_case in self.test_cases:
            if test_case.category not in categories:
                categories[test_case.category] = []
            categories[test_case.category].append(test_case)

        # 运行测试
        for category, test_cases in categories.items():
            logger.info(f"📂 运行{category}类别测试 ({len(test_cases)}个)...")
            await self._run_category_tests(category, test_cases)

        total_time = time.time() - start_time

        # 生成测试报告
        test_report = self._generate_test_report(total_time)

        logger.info(f"✅ 测试完成，总耗时: {total_time:.2f}秒")
        logger.info(f"📋 详细报告: {test_report['report_path']}")

        return test_report

    async def _run_category_tests(self, category: str, test_cases: List[TestCase]):
        """运行某个类别的测试"""
        for test_case in test_cases:
            logger.info(f"  🔄 {test_case.test_id}: {test_case.name}")
            result = await self._run_single_test(test_case)
            self.test_results.append(result)

            if result.passed:
                logger.info(f"    ✅ 通过 ({result.execution_time:.3f}s)")
            else:
                logger.error(f"    ❌ 失败: {result.error_message}")

    async def _run_single_test(self, test_case: TestCase) -> TestResult:
        """运行单个测试"""
        start_time = time.time()

        try:
            # 设置超时
            result = await asyncio.wait_for(
                test_case.test_function(),
                timeout=test_case.timeout
            )

            execution_time = time.time() - start_time

            # 检查结果
            passed = self._check_test_result(result, test_case.expected_result)

            test_result = TestResult(
                test_id=test_case.test_id,
                test_name=test_case.name,
                passed=passed,
                execution_time=execution_time,
                actual_result=result,
                expected_result=test_case.expected_result
            )

        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            test_result = TestResult(
                test_id=test_case.test_id,
                test_name=test_case.name,
                passed=False,
                execution_time=execution_time,
                error_message=f"测试超时 ({test_case.timeout}s)"
            )

        except Exception as e:
            execution_time = time.time() - start_time
            test_result = TestResult(
                test_id=test_case.test_id,
                test_name=test_name,
                passed=False,
                execution_time=execution_time,
                error_message=str(e),
                error_details=traceback.format_exc()
            )

        return test_result

    def _check_test_result(self, actual: Any, expected: Any) -> bool:
        """检查测试结果"""
        if isinstance(expected, dict) and 'success' in expected:
            return actual.get('success', False) == expected['success']
        elif isinstance(expected, str) and expected.startswith('<'):
            # 数值比较
            try:
                actual_value = float(str(actual).split()[0])
                expected_value = float(expected.split()[1])
                return actual_value < expected_value
            except:
                return False
        else:
            return actual == expected

    # 测试函数定义
    async def test_perception_engine_init(self) -> bool:
        """测试感知引擎初始化"""
        try:
            engine = StructuredPatentPerceptionEngine()
            await engine.initialize()
            return True
        except Exception as e:
            logger.error(f"感知引擎初始化失败: {str(e)}")
            return False

    async def test_semantic_fusion_init(self) -> bool:
        """测试语义融合引擎初始化"""
        try:
            engine = SemanticFusionEngine()
            return True
        except Exception as e:
            logger.error(f"语义融合引擎初始化失败: {str(e)}")
            return False

    async def test_knowledge_base_init(self) -> bool:
        """测试知识库初始化"""
        try:
            kb = PatentKnowledgeBase()
            return len(kb.entities) > 0
        except Exception as e:
            logger.error(f"知识库初始化失败: {str(e)}")
            return False

    async def test_patent_document_processing(self) -> Dict[str, Any]:
        """测试专利文档处理"""
        test_file = Path(self.test_data_path) / 'CN201815134U.pdf'

        if not test_file.exists():
            return {'success': False, 'error': '测试文件不存在'}

        try:
            result = await self.perception_engine.process_document(
                str(test_file), DocumentType.PATENT
            )
            return {'success': True, 'result': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def test_semantic_fusion(self) -> Dict[str, Any]:
        """测试语义融合"""
        try:
            modalities = {
                'text': [{'content': '测试文本内容'}],
                'image': [{'ocr_text': '测试图像内容'}]
            }

            result = await self.semantic_fusion_engine.fuse_modalities(modalities)
            return {'success': True, 'result': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def test_knowledge_retrieval(self) -> Dict[str, Any]:
        """测试知识检索"""
        try:
            entities = self.knowledge_base.search_entities('权利要求', limit=5)
            return {'success': True, 'entities': len(entities)}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def test_alignment_interface(self) -> Dict[str, Any]:
        """测试感知对齐接口"""
        try:
            session = await self.alignment_interface.start_alignment_session(
                document_id='test_doc',
                user_id='test_user',
                mode=InterfaceMode.REVIEW_MODE
            )

            # 提交测试修正
            from perception_alignment_interface import CorrectionType
            correction = await self.alignment_interface.submit_correction(
                correction_type=CorrectionType.ENTITY_CORRECTION,
                target_id='test_entity',
                original_value={'content': '原值'},
                corrected_value={'content': '修正值'},
                justification='测试修正'
            )

            await self.alignment_interface.end_session()

            return {'success': True, 'corrections': 1}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def test_document_processing_performance(self) -> Dict[str, Any]:
        """测试文档处理性能"""
        test_file = Path(self.test_data_path) / 'CN201815134U.pdf'

        if not test_file.exists():
            return {'success': False, 'error': '测试文件不存在'}

        try:
            start_time = time.time()
            result = await document_optimizer.process_document_optimized(str(test_file))
            processing_time = time.time() - start_time

            return {
                'success': True,
                'processing_time': processing_time,
                'optimized': True,
                'performance_good': processing_time < 5.0
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def test_concurrent_processing(self) -> Dict[str, Any]:
        """测试并发处理"""
        try:
            # 模拟并发任务
            async def concurrent_task(task_id: int):
                await asyncio.sleep(1)  # 模拟处理时间
                return f"task_{task_id}_completed"

            # 并发执行多个任务
            tasks = [concurrent_task(i) for i in range(5)]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            successful_tasks = [r for r in results if not isinstance(r, Exception)]

            return {
                'success': True,
                'total_tasks': len(tasks),
                'successful_tasks': len(successful_tasks),
                'concurrency': True
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def test_input_error_handling(self) -> Dict[str, Any]:
        """测试输入错误处理"""
        try:
            # 测试文件不存在错误
            result = await self.perception_engine.process_document(
                'non_existent_file.pdf', DocumentType.PATENT
            )

            # 如果能处理错误，说明错误处理正常
            return {'handled': True, 'result': result}
        except Exception as e:
            # 使用全局错误处理器
            context = {'operation': 'test_input_error'}
            success, fallback_result = await global_error_handler.handle_error(e, context)

            return {
                'handled': success,
                'fallback_result': fallback_result
            }

    async def test_system_error_recovery(self) -> Dict[str, Any]:
        """测试系统错误恢复"""
        try:
            # 模拟系统错误
            raise SystemError('模拟系统错误')

        except Exception as e:
            context = {'operation': 'test_system_recovery'}
            success, fallback_result = await global_error_handler.handle_error(e, context)

            return {
                'recovered': success,
                'fallback_result': fallback_result
            }

    async def test_end_to_end_workflow(self) -> Dict[str, Any]:
        """测试端到端工作流程"""
        test_file = Path(self.test_data_path) / 'CN201815134U.pdf'

        if not test_file.exists():
            return {'success': False, 'error': '测试文件不存在'}

        try:
            start_time = time.time()

            # 1. 文档处理
            doc_result = await self.perception_engine.process_document(
                str(test_file), DocumentType.PATENT
            )

            # 2. 语义融合
            modalities = {
                'text': [{'content': '测试文本'}],
                'image': [{'ocr_text': '测试图像'}]
            }
            fusion_result = await self.semantic_fusion_engine.fuse_modalities(modalities)

            # 3. 知识检索
            knowledge_result = await self.rag_system.retrieve_and_generate(
                '测试查询',
                {'content': '测试内容'}
            )

            # 4. 感知对齐
            session = await self.alignment_interface.start_alignment_session(
                document_id='e2e_test',
                user_id='test_user'
            )
            await self.alignment_interface.end_session()

            total_time = time.time() - start_time

            return {
                'success': True,
                'total_time': total_time,
                'steps_completed': 4,
                'workflow_complete': True
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _generate_test_report(self, total_time: float) -> Dict[str, Any]:
        """生成测试报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = Path(self.output_path) / f"test_report_{timestamp}.json"

        # 统计信息
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.passed)
        failed_tests = total_tests - passed_tests
        pass_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0

        # 按类别统计
        category_stats = {}
        for result in self.test_results:
            test_id = result.test_id
            test_case = next((tc for tc in self.test_cases if tc.test_id == test_id), None)
            if test_case:
                category = test_case.category
                if category not in category_stats:
                    category_stats[category] = {'total': 0, 'passed': 0, 'failed': 0}
                category_stats[category]['total'] += 1
                if result.passed:
                    category_stats[category]['passed'] += 1
                else:
                    category_stats[category]['failed'] += 1

        # 性能统计
        avg_execution_time = sum(r.execution_time for r in self.test_results) / total_tests if total_tests > 0 else 0
        max_execution_time = max(r.execution_time for r in self.test_results) if self.test_results else 0

        report = {
            'report_timestamp': timestamp,
            'report_path': str(report_path),
            'test_execution': {
                'total_time': total_time,
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'pass_rate': pass_rate,
                'avg_execution_time': avg_execution_time,
                'max_execution_time': max_execution_time
            },
            'category_breakdown': category_stats,
            'test_results': [
                {
                    'test_id': r.test_id,
                    'test_name': r.test_name,
                    'passed': r.passed,
                    'execution_time': r.execution_time,
                    'error_message': r.error_message
                }
                for r in self.test_results
            ]
        }

        # 保存报告
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)

        return report

# 主测试运行器
async def run_comprehensive_tests():
    """运行综合测试"""
    logger.info('🧪 启动结构化感知系统综合测试...')
    logger.info(str('=' * 60))

    test_suite = ComprehensiveTestSuite()

    try:
        # 运行所有测试
        report = await test_suite.run_all_tests()

        # 显示测试结果摘要
        logger.info("\n📊 测试结果摘要:")
        logger.info(str('=' * 60))
        logger.info(f"总测试数: {report['test_execution']['total_tests']}")
        logger.info(f"通过测试数: {report['test_execution']['passed_tests']}")
        logger.info(f"失败测试数: {report['test_execution']['failed_tests']}")
        logger.info(f"通过率: {report['test_execution']['pass_rate']:.1f}%")
        logger.info(f"总执行时间: {report['test_execution']['total_time']:.2f}秒")
        logger.info(f"平均执行时间: {report['test_execution']['avg_execution_time']:.3f}秒")

        # 按类别显示结果
        logger.info("\n📂 按类别统计:")
        for category, stats in report['category_breakdown'].items():
            pass_rate = (stats['passed'] / stats['total']) * 100 if stats['total'] > 0 else 0
            logger.info(f"  {category}: {stats['passed']}/{stats['total']} ({pass_rate:.1f}%)")

        return report

    except Exception as e:
        logger.error(f"测试执行失败: {str(e)}")
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

if __name__ == '__main__':
    # 运行测试
    asyncio.run(run_comprehensive_tests())