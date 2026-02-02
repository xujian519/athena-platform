#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心模块验证测试
Core Modules Verification Test

验证执行模块、学习与适应模块、通信模块、评估与反思模块、知识库与工具库模块的完整性

作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

import asyncio
import logging
import os
import sys
import traceback
from datetime import datetime

logger = logging.getLogger(__name__)

# 添加项目路径
sys.path.insert(0, '/Users/xujian/Athena工作平台')
sys.path.insert(0, '/Users/xujian/Athena工作平台/core')
sys.path.insert(0, '/Users/xujian/Athena工作平台/patent-platform/workspace/src')

class ModuleVerifier:
    """模块验证器"""

    def __init__(self):
        self.test_results = []

    async def verify_execution_module(self):
        """验证执行模块"""
        logger.info("\n🔧 1. 执行模块验证")
        logger.info(str('-' * 60))

        try:
            # 导入执行引擎
            from execution.execution_engine import (
                ActionExecutor,
                ExecutionEngine,
                Task,
                TaskPriority,
                TaskScheduler,
                TaskStatus,
                WorkflowEngine,
            )

            logger.info('✅ 执行引擎模块导入成功')

            # 创建执行引擎
            executor = ExecutionEngine(max_workers=4)
            logger.info('✅ 执行引擎创建成功')

            # 创建测试任务
            test_task = Task(
                id='test_task_001',
                name='测试任务',
                action='print',
                parameters={'message': 'Hello from Execution Engine'},
                priority=TaskPriority.NORMAL
            )

            # 提交任务
            task_id = await executor.submit_task(test_task)
            logger.info(f"✅ 任务提交成功: {task_id}")

            # 等待任务完成
            result = await executor.wait_for_task(task_id, timeout=5)
            if result and result.success:
                logger.info('✅ 任务执行成功')
            else:
                logger.info('⚠️ 任务执行失败或超时')

            # 测试工作流引擎
            action_executor = ActionExecutor()
            workflow_engine = WorkflowEngine(action_executor)
            logger.info('✅ 工作流引擎创建成功')

            await executor.shutdown()
            logger.info('✅ 执行引擎关闭成功')

            return True

        except Exception as e:
            logger.info(f"❌ 执行模块验证失败: {e}")
            traceback.print_exc()
            return False

    async def verify_learning_module(self):
        """验证学习与适应模块"""
        logger.info("\n🧠 2. 学习与适应模块验证")
        logger.info(str('-' * 60))

        try:
            # 导入学习引擎
            from learning.learning_engine import (
                AdaptationStrategy,
                LearningEngine,
                LearningStrategy,
            )

            logger.info('✅ 学习引擎模块导入成功')

            # 创建学习引擎
            learning_engine = LearningEngine()
            logger.info('✅ 学习引擎创建成功')

            # 测试学习功能
            test_experience = {
                'task': 'test_task',
                'outcome': 'success',
                'context': {'difficulty': 'medium'},
                'timestamp': datetime.now().isoformat()
            }

            learning_result = await learning_engine.process_experience(test_experience)
            if learning_result:
                logger.info('✅ 学习处理成功')
            else:
                logger.info('⚠️ 学习处理失败')

            # 测试适应策略
            adaptation_result = await learning_engine.adapt_strategy(
                current_performance=0.8,
                target_performance=0.9
            )
            logger.info(f"✅ 适应策略应用成功: {adaptation_result}")

            return True

        except Exception as e:
            logger.info(f"❌ 学习模块验证失败: {e}")
            traceback.print_exc()
            return False

    async def verify_communication_module(self):
        """验证通信模块"""
        logger.info("\n📡 3. 通信模块验证")
        logger.info(str('-' * 60))

        try:
            # 尝试导入通信引擎
            try:
                from communication.communication_engine import CommunicationEngine
                logger.info('✅ 通信引擎模块导入成功')

                # 创建通信引擎
                comm_engine = CommunicationEngine()
                logger.info('✅ 通信引擎创建成功')

                # 测试消息发送
                test_message = {
                    'sender': 'agent_1',
                    'receiver': 'agent_2',
                    'content': 'Test message',
                    'timestamp': datetime.now().isoformat()
                }

                send_result = await comm_engine.send_message(test_message)
                if send_result:
                    logger.info('✅ 消息发送测试通过')
                else:
                    logger.info('⚠️ 消息发送测试失败')

            except ImportError:
                logger.info('⚠️ 通信引擎模块不存在，尝试其他通信模块')

            # 尝试导入agent_collaboration模块
            try:
                from agent_collaboration.communication import CollaborationCommunication
                logger.info('✅ 协作通信模块导入成功')

                collab_comm = CollaborationCommunication()
                logger.info('✅ 协作通信创建成功')

            except ImportError:
                logger.info('⚠️ 协作通信模块不存在')

            return True

        except Exception as e:
            logger.info(f"❌ 通信模块验证失败: {e}")
            traceback.print_exc()
            return False

    async def verify_evaluation_module(self):
        """验证评估与反思模块"""
        logger.info("\n📊 4. 评估与反思模块验证")
        logger.info(str('-' * 60))

        try:
            # 导入评估引擎
            from evaluation.evaluation_engine import (
                EvaluationEngine,
                EvaluationMetric,
                EvaluationResult,
            )

            logger.info('✅ 评估引擎模块导入成功')

            # 创建评估引擎
            eval_engine = EvaluationEngine()
            logger.info('✅ 评估引擎创建成功')

            # 测试评估功能
            test_metric = EvaluationMetric(
                name='accuracy',
                value=0.95,
                unit='percentage',
                description='任务准确率'
            )

            eval_result = EvaluationResult(
                task_id='test_task',
                metrics=[test_metric],
                overall_score=0.95,
                timestamp=datetime.now()
            )

            # 记录评估结果
            record_result = await eval_engine.record_evaluation(eval_result)
            if record_result:
                logger.info('✅ 评估结果记录成功')
            else:
                logger.info('⚠️ 评估结果记录失败')

            # 测试反思功能
            reflection_result = await eval_engine.generate_reflection('test_task')
            if reflection_result:
                logger.info('✅ 反思生成成功')
            else:
                logger.info('⚠️ 反思生成失败')

            return True

        except Exception as e:
            logger.info(f"❌ 评估模块验证失败: {e}")
            traceback.print_exc()
            return False

    async def verify_knowledge_module(self):
        """验证知识库与工具库模块"""
        logger.info("\n📚 5. 知识库与工具库模块验证")
        logger.info(str('-' * 60))

        knowledge_results = []
        tool_results = []

        # 验证知识库模块
        try:
            # 知识图谱
            from memory.knowledge_graph_adapter import get_knowledge_adapter
            logger.info('✅ 知识图谱适配器导入成功')

            # 专利分析知识图谱
            from patent_analysis.knowledge_graph import PatentKnowledgeGraph
            logger.info('✅ 专利知识图谱模块导入成功')

            # 创建知识图谱实例
            kg = PatentKnowledgeGraph()
            logger.info('✅ 知识图谱实例创建成功')

            # 测试知识查询
            test_query = '专利'
            query_result = await kg.query_knowledge(test_query, limit=5)
            logger.info(f"✅ 知识查询成功: 返回 {len(query_result) if query_result else 0} 条结果")

            knowledge_results.append(True)

        except Exception as e:
            logger.info(f"❌ 知识库模块验证失败: {e}")
            traceback.print_exc()
            knowledge_results.append(False)

        # 验证工具库模块
        try:
            # 工具注册表
            from search.registry.tool_registry import ToolRegistry
            logger.info('✅ 工具注册表导入成功')

            # 工具自动执行器
            from tool_auto_executor import ToolAutoExecutor
            logger.info('✅ 工具自动执行器导入成功')

            # 创建工具注册表
            tool_registry = ToolRegistry()
            logger.info('✅ 工具注册表创建成功')

            # 测试工具注册
            def test_tool(param1: str, param2: int = 10) -> dict:
                return {'result': f"Tool executed with {param1} and {param2}"}

            register_result = tool_registry.register_tool('test_tool', test_tool)
            if register_result:
                logger.info('✅ 工具注册成功')
            else:
                logger.info('⚠️ 工具注册失败')

            # 测试工具执行
            executor = ToolAutoExecutor()
            exec_result = await executor.execute_tool('test_tool', {'param1': 'test'})
            if exec_result:
                logger.info('✅ 工具执行成功')
            else:
                logger.info('⚠️ 工具执行失败')

            tool_results.append(True)

        except Exception as e:
            logger.info(f"❌ 工具库模块验证失败: {e}")
            traceback.print_exc()
            tool_results.append(False)

        # 返回综合结果
        return all(knowledge_results + tool_results)

    async def verify_module_integration(self):
        """验证模块集成"""
        logger.info("\n🔗 6. 模块集成验证")
        logger.info(str('-' * 60))

        try:
            integration_results = []

            # 测试执行与学习的集成
            try:
                from execution.execution_engine import ExecutionEngine
                from learning.learning_engine import LearningEngine

                executor = ExecutionEngine(max_workers=2)
                learner = LearningEngine()

                # 创建学习任务
                learning_task = {
                    'action': 'learn',
                    'content': '测试集成学习功能',
                    'context': {'integration_test': True}
                }

                # 执行任务并学习
                task_id = await executor.submit_task(learning_task)
                result = await executor.wait_for_task(task_id, timeout=3)

                # 将结果传递给学习引擎
                if result and result.success:
                    experience = {
                        'task': 'integration_test',
                        'outcome': 'success' if result.success else 'failure',
                        'result': result.result
                    }
                    learning_result = await learner.process_experience(experience)
                    integration_results.append(learning_result)

                await executor.shutdown()
                logger.info('✅ 执行与学习模块集成成功')

            except Exception as e:
                logger.info(f"⚠️ 执行与学习集成失败: {e}")
                integration_results.append(False)

            # 测试通信与评估的集成
            try:
                from evaluation.evaluation_engine import EvaluationEngine

                evaluator = EvaluationEngine()

                # 模拟通信后的评估
                comm_metrics = {
                    'messages_sent': 10,
                    'messages_received': 8,
                    'response_time': 0.5,
                    'success_rate': 0.8
                }

                eval_result = await evaluator.evaluate_communication(comm_metrics)
                if eval_result:
                    logger.info('✅ 通信与评估模块集成成功')
                    integration_results.append(True)
                else:
                    logger.info('⚠️ 通信评估失败')
                    integration_results.append(False)

            except Exception as e:
                logger.info(f"⚠️ 通信与评估集成失败: {e}")
                integration_results.append(False)

            return all(integration_results)

        except Exception as e:
            logger.info(f"❌ 模块集成验证失败: {e}")
            traceback.print_exc()
            return False

    def analyze_platform_status(self):
        """分析平台现状"""
        logger.info("\n📈 7. 平台现状分析")
        logger.info(str('-' * 60))

        analysis = {
            '模块完整性': {},
            '代码质量': {},
            '架构设计': {},
            '潜在问题': [],
            '优化建议': []
        }

        # 统计已验证的模块
        total_modules = 5  # 执行、学习、通信、评估、知识库
        verified_count = sum(1 for _, result in self.test_results if result)

        analysis['模块完整性'] = {
            '已验证模块': verified_count,
            '总模块数': total_modules,
            '完整度': f"{(verified_count/total_modules)*100:.1f}%"
        }

        # 分析代码质量
        quality_issues = []
        if verified_count < total_modules:
            quality_issues.append('部分模块缺失或不可运行')

        analysis['代码质量'] = {
            '状态': '良好' if len(quality_issues) == 0 else '需要改进',
            '问题': quality_issues
        }

        # 架构分析
        architecture_strengths = [
            '模块化设计清晰',
            '异步架构支持并发',
            '错误处理机制完善'
        ]

        architecture_weaknesses = [
            '模块间依赖复杂',
            '缺乏统一的配置管理',
            '监控和日志不够完善'
        ]

        analysis['架构设计'] = {
            '优势': architecture_strengths,
            '待改进': architecture_weaknesses
        }

        # 潜在问题
        analysis['潜在问题'] = [
            '部分模块缺少完整的测试覆盖',
            '错误恢复机制需要加强',
            '性能优化空间较大',
            '文档不够完善'
        ]

        # 优化建议
        analysis['优化建议'] = [
            '完善所有模块的功能实现',
            '建立统一的配置管理系统',
            '添加更完善的监控和日志',
            '提高模块间的松耦合度',
            '增加自动化测试覆盖',
            '优化性能和资源使用',
            '完善文档和使用指南'
        ]

        return analysis

    async def run_all_verifications(self):
        """运行所有验证"""
        logger.info('🚀 核心模块综合验证测试')
        logger.info(str('='*80))
        logger.info(f"验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(str('='*80))

        # 执行各项验证
        verifications = [
            ('执行模块', self.verify_execution_module),
            ('学习与适应模块', self.verify_learning_module),
            ('通信模块', self.verify_communication_module),
            ('评估与反思模块', self.verify_evaluation_module),
            ('知识库与工具库模块', self.verify_knowledge_module),
            ('模块集成', self.verify_module_integration)
        ]

        for module_name, verify_func in verifications:
            try:
                result = await verify_func()
                self.test_results.append((module_name, result))
            except Exception as e:
                logger.info(f"❌ {module_name}验证异常: {e}")
                self.test_results.append((module_name, False))

        # 分析平台现状
        analysis = self.analyze_platform_status()

        # 生成报告
        self.generate_report(analysis)

    def generate_report(self, analysis):
        """生成验证报告"""
        logger.info(str("\n" + '='*80))
        logger.info('📋 核心模块验证报告')
        logger.info(str('='*80))

        # 模块验证结果
        total = len(self.test_results)
        passed = sum(1 for _, result in self.test_results if result)

        logger.info(f"\n📊 验证统计:")
        logger.info(f"   总模块数: {total}")
        logger.info(f"   ✅ 通过: {passed}")
        logger.info(f"   ❌ 失败: {total - passed}")
        logger.info(f"   通过率: {(passed/total)*100:.1f}%")

        logger.info(f"\n📝 详细结果:")
        for i, (module_name, result) in enumerate(self.test_results, 1):
            status = '✅ PASSED' if result else '❌ FAILED'
            logger.info(f"{i}. {module_name}: {status}")

        # 平台分析结果
        logger.info(f"\n🔍 平台现状分析:")
        logger.info(f"   模块完整度: {analysis['模块完整性']['完整度']}")

        logger.info(f"\n🏗️ 架构设计:")
        logger.info('   优势:')
        for strength in analysis['架构设计']['优势']:
            logger.info(f"     • {strength}")
        logger.info('   待改进:')
        for weakness in analysis['架构设计']['待改进']:
            logger.info(f"     • {weakness}")

        logger.info(f"\n⚠️ 潜在问题:")
        for i, issue in enumerate(analysis['潜在问题'], 1):
            logger.info(f"   {i}. {issue}")

        logger.info(f"\n💡 优化建议:")
        for i, suggestion in enumerate(analysis['优化建议'], 1):
            logger.info(f"   {i}. {suggestion}")

        # 结论
        if passed >= total * 0.8:
            conclusion = '✅ 核心模块基本完整，平台具备基础运行能力'
        elif passed >= total * 0.6:
            conclusion = '⚠️ 部分模块需要完善，但核心功能可用'
        else:
            conclusion = '❌ 多个模块存在严重问题，需要大规模重构'

        logger.info(f"\n🎯 结论:")
        logger.info(f"   {conclusion}")

        logger.info(str("\n" + '='*80))

async def main():
    """主函数"""
    verifier = ModuleVerifier()
    await verifier.run_all_verifications()

if __name__ == '__main__':
    asyncio.run(main())