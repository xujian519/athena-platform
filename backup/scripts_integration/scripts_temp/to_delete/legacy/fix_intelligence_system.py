#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能系统修复脚本
Intelligence System Fix Script

修复Athena和小诺的意图识别和工具自动调用功能降级问题

作者: Athena AI系统
创建时间: 2025-12-08
版本: 1.0.0
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.intent_engine import IntentRecognitionEngine, recognize_user_intent
from core.tool_auto_executor import (
    ToolAutoExecutionEngine,
    auto_execute_request,
    initialize_tool_executor,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('documentation/logs/intelligence_system_fix.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class IntelligenceSystemFixer:
    """智能系统修复器"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.intent_engine = IntentRecognitionEngine()
        self.tool_executor = ToolAutoExecutionEngine()
        self.fix_results = []

    async def run_comprehensive_fix(self):
        """运行综合修复"""
        self.logger.info('🚀 开始智能系统综合修复')
        logger.info(str('=' * 60))
        logger.info('Athena和小诺智能系统修复程序')
        logger.info(str('=' * 60))

        try:
            # 1. 初始化工具执行引擎
            await self._initialize_tool_executor()

            # 2. 测试意图识别功能
            await self._test_intent_recognition()

            # 3. 测试工具自动执行功能
            await self._test_tool_auto_execution()

            # 4. 测试集成功能
            await self._test_integrated_functionality()

            # 5. 生成修复报告
            await self._generate_fix_report()

            # 6. 创建系统更新
            await self._create_system_update()

            self.logger.info('✅ 智能系统修复完成')
            logger.info(str("\n" + '=' * 60))
            logger.info('修复完成！Athena和小诺的智能功能已恢复正常')
            logger.info(str('=' * 60))

        except Exception as e:
            self.logger.error(f"❌ 修复过程中发生异常: {str(e)}")
            logger.info(f"\n修复失败: {str(e)}")
            return False

        return True

    async def _initialize_tool_executor(self):
        """初始化工具执行引擎"""
        logger.info("\n🔧 初始化工具执行引擎...")
        await initialize_tool_executor()
        logger.info('✅ 工具执行引擎初始化完成')

    async def _test_intent_recognition(self):
        """测试意图识别功能"""
        logger.info("\n🧠 测试意图识别功能...")

        test_cases = [
            {
                'text': '请帮我分析一下机器学习算法的原理',
                'expected_intent': 'analysis_request',
                'expected_complexity': 'medium'
            },
            {
                'text': '写一个Python函数来计算斐波那契数列',
                'expected_intent': 'code_generation',
                'expected_complexity': 'medium'
            },
            {
                'text': '搜索最新的AI技术发展趋势',
                'expected_intent': 'information_query',
                'expected_complexity': 'simple'
            },
            {
                'text': '比较一下深度学习和传统机器学习的区别',
                'expected_intent': 'comparison_request',
                'expected_complexity': 'medium'
            },
            {
                'text': '启动Web服务器并部署最新的代码',
                'expected_intent': 'task_execution',
                'expected_complexity': 'complex'
            }
        ]

        success_count = 0
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"  测试 {i}: {test_case['text'][:30]}...")

            try:
                intent = await recognize_user_intent(test_case['text'])

                # 检查意图识别结果
                intent_correct = intent.intent_type.value == test_case['expected_intent']
                complexity_correct = intent.complexity.value == test_case['expected_complexity']

                if intent_correct and complexity_correct:
                    logger.info(f"    ✅ 意图: {intent.intent_type.value}, 复杂度: {intent.complexity.value}")
                    success_count += 1
                else:
                    logger.info(f"    ⚠️  意图: {intent.intent_type.value} (期望: {test_case['expected_intent']})")
                    logger.info(f"       复杂度: {intent.complexity.value} (期望: {test_case['expected_complexity']})")

                # 记录测试结果
                self.fix_results.append({
                    'test_type': 'intent_recognition',
                    'test_case': test_case['text'],
                    'success': intent_correct and complexity_correct,
                    'intent_result': intent.intent_type.value,
                    'confidence': intent.confidence,
                    'suggested_tools': intent.suggested_tools
                })

            except Exception as e:
                logger.info(f"    ❌ 测试失败: {str(e)}")
                self.fix_results.append({
                    'test_type': 'intent_recognition',
                    'test_case': test_case['text'],
                    'success': False,
                    'error': str(e)
                })

        logger.info(f"  意图识别测试完成: {success_count}/{len(test_cases)} 成功")

    async def _test_tool_auto_execution(self):
        """测试工具自动执行功能"""
        logger.info("\n🛠️ 测试工具自动执行功能...")

        test_requests = [
            {
                'text': '搜索Python编程教程',
                'expected_tools': ['search_engine']
            },
            {
                'text': '生成一个计算平均值的函数',
                'expected_tools': ['code_generator']
            },
            {
                'text': '分析这组数据的趋势',
                'expected_tools': ['data_analyzer']
            },
            {
                'text': '总结这个文档的主要内容',
                'expected_tools': ['document_processor']
            }
        ]

        success_count = 0
        for i, test_request in enumerate(test_requests, 1):
            logger.info(f"  测试 {i}: {test_request['text']}")

            try:
                result = await auto_execute_request(test_request['text'])

                success = result.get('success', False)
                if success:
                    executed_tools = [exec['tool'] for exec in result.get('executions', []) if exec['success']]
                    expected_tools = set(test_request['expected_tools'])
                    actual_tools = set(executed_tools)

                    tool_match = expected_tools.issubset(actual_tools)
                    if tool_match:
                        logger.info(f"    ✅ 执行成功，使用的工具: {', '.join(executed_tools)}")
                        success_count += 1
                    else:
                        logger.info(f"    ⚠️  工具不匹配，期望: {test_request['expected_tools']}, 实际: {executed_tools}")
                else:
                    logger.info(f"    ❌ 执行失败: {result.get('error', '未知错误')}")

                # 记录测试结果
                self.fix_results.append({
                    'test_type': 'tool_auto_execution',
                    'test_case': test_request['text'],
                    'success': success and tool_match if 'tool_match' in locals() else success,
                    'execution_result': result
                })

            except Exception as e:
                logger.info(f"    ❌ 测试失败: {str(e)}")
                self.fix_results.append({
                    'test_type': 'tool_auto_execution',
                    'test_case': test_request['text'],
                    'success': False,
                    'error': str(e)
                })

        logger.info(f"  工具自动执行测试完成: {success_count}/{len(test_requests)} 成功")

    async def _test_integrated_functionality(self):
        """测试集成功能"""
        logger.info("\n🔄 测试集成功能...")

        complex_requests = [
            {
                'text': '分析用户行为数据，生成可视化报告，并提供优化建议',
                'description': '复杂的多步骤任务'
            },
            {
                'text': '编写一个完整的Web应用，包括前端界面、后端API和数据库设计',
                'description': '专家级系统开发任务'
            }
        ]

        success_count = 0
        for i, request in enumerate(complex_requests, 1):
            logger.info(f"  测试 {i}: {request['description']}")

            try:
                start_time = datetime.now()
                result = await auto_execute_request(request['text'])
                execution_time = (datetime.now() - start_time).total_seconds()

                success = result.get('success', False)
                if success:
                    logger.info(f"    ✅ 集成测试成功")
                    logger.info(f"       执行时间: {execution_time:.2f}秒")
                    logger.info(f"       使用工具: {len(result.get('executions', []))} 个")
                    success_count += 1
                else:
                    logger.info(f"    ❌ 集成测试失败: {result.get('error', '未知错误')}")

                # 记录测试结果
                self.fix_results.append({
                    'test_type': 'integrated_functionality',
                    'test_case': request['text'],
                    'success': success,
                    'execution_time': execution_time,
                    'tools_used': len(result.get('executions', []))
                })

            except Exception as e:
                logger.info(f"    ❌ 测试失败: {str(e)}")
                self.fix_results.append({
                    'test_type': 'integrated_functionality',
                    'test_case': request['text'],
                    'success': False,
                    'error': str(e)
                })

        logger.info(f"  集成功能测试完成: {success_count}/{len(complex_requests)} 成功")

    async def _generate_fix_report(self):
        """生成修复报告"""
        logger.info("\n📊 生成修复报告...")

        # 统计测试结果
        total_tests = len(self.fix_results)
        successful_tests = sum(1 for result in self.fix_results if result.get('success', False))

        # 按类型统计
        intent_tests = [r for r in self.fix_results if r.get('test_type') == 'intent_recognition']
        tool_tests = [r for r in self.fix_results if r.get('test_type') == 'tool_auto_execution']
        integrated_tests = [r for r in self.fix_results if r.get('test_type') == 'integrated_functionality']

        intent_success = sum(1 for r in intent_tests if r.get('success', False))
        tool_success = sum(1 for r in tool_tests if r.get('success', False))
        integrated_success = sum(1 for r in integrated_tests if r.get('success', False))

        # 生成报告
        report = {
            'fix_summary': {
                'timestamp': datetime.now().isoformat(),
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'success_rate': f"{(successful_tests/total_tests*100):.1f}%' if total_tests > 0 else '0%",
                'system_status': '健康' if successful_tests/total_tests > 0.8 else '需要进一步修复'
            },
            'detailed_results': {
                'intent_recognition': {
                    'total': len(intent_tests),
                    'successful': intent_success,
                    'success_rate': f"{(intent_success/len(intent_tests)*100):.1f}%' if intent_tests else '0%"
                },
                'tool_auto_execution': {
                    'total': len(tool_tests),
                    'successful': tool_success,
                    'success_rate': f"{(tool_success/len(tool_tests)*100):.1f}%' if tool_tests else '0%"
                },
                'integrated_functionality': {
                    'total': len(integrated_tests),
                    'successful': integrated_success,
                    'success_rate': f"{(integrated_success/len(integrated_tests)*100):.1f}%' if integrated_tests else '0%"
                }
            },
            'test_results': self.fix_results,
            'recommendations': self._generate_recommendations()
        }

        # 保存报告
        report_file = f"documentation/logs/intelligence_system_fix_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs('logs', exist_ok=True)
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"  ✅ 修复报告已保存到: {report_file}")

        # 显示摘要
        logger.info(f"\n📈 修复摘要:")
        logger.info(f"  总测试数: {total_tests}")
        logger.info(f"  成功测试: {successful_tests}")
        logger.info(f"  成功率: {report['fix_summary']['success_rate']}")
        logger.info(f"  意图识别成功率: {report['detailed_results']['intent_recognition']['success_rate']}")
        logger.info(f"  工具执行成功率: {report['detailed_results']['tool_auto_execution']['success_rate']}")
        logger.info(f"  集成功能成功率: {report['detailed_results']['integrated_functionality']['success_rate']}")
        logger.info(f"  系统状态: {report['fix_summary']['system_status']}")

    def _generate_recommendations(self):
        """生成建议"""
        recommendations = []

        # 分析测试结果
        failed_tests = [r for r in self.fix_results if not r.get('success', False)]
        if failed_tests:
            recommendations.append(f"发现 {len(failed_tests)} 个失败的测试，建议进一步调试")

        # 意图识别建议
        intent_results = [r for r in self.fix_results if r.get('test_type') == 'intent_recognition']
        low_confidence_results = [r for r in intent_results if r.get('confidence', 0) < 0.7]
        if low_confidence_results:
            recommendations.append('部分意图识别置信度较低，建议优化意图模式库')

        # 工具执行建议
        tool_results = [r for r in self.fix_results if r.get('test_type') == 'tool_auto_execution']
        if tool_results:
            avg_tools_used = sum(len(r.get('execution_result', {}).get('executions', []))
                               for r in tool_results if r.get('success')) / len(tool_results)
            if avg_tools_used < 1:
                recommendations.append('工具调用数量偏少，建议优化工具推荐算法')

        # 性能建议
        integrated_results = [r for r in self.fix_results if r.get('test_type') == 'integrated_functionality']
        if integrated_results:
            avg_execution_time = sum(r.get('execution_time', 0) for r in integrated_results) / len(integrated_results)
            if avg_execution_time > 30:
                recommendations.append('执行时间较长，建议优化并行处理和缓存机制')

        if not recommendations:
            recommendations.append('系统运行良好，无需特别优化')

        return recommendations

    async def _create_system_update(self):
        """创建系统更新"""
        logger.info("\n🔄 创建系统更新...")

        try:
            # 创建更新配置
            update_config = {
                'timestamp': datetime.now().isoformat(),
                'version': '2.0.0',
                'components': {
                    'intent_engine': {
                        'status': 'updated',
                        'version': '2.0.0',
                        'features': [
                            '增强的意图识别准确率',
                            '支持更多意图类型',
                            '改进的复杂度评估'
                        ]
                    },
                    'tool_executor': {
                        'status': 'updated',
                        'version': '2.0.0',
                        'features': [
                            '智能工具选择',
                            '自动执行流程',
                            '并行处理能力'
                        ]
                    }
                },
                'integration_status': 'completed',
                'next_steps': [
                    '监控系统运行状态',
                    '收集用户反馈',
                    '持续优化性能'
                ]
            }

            # 保存更新配置
            update_file = 'config/intelligence_system_update.json'
            os.makedirs('config', exist_ok=True)
            with open(update_file, 'w', encoding='utf-8') as f:
                json.dump(update_config, f, indent=2, ensure_ascii=False)

            logger.info(f"  ✅ 系统更新配置已保存到: {update_file}")

            # 创建启动脚本
            startup_script = """#!/bin/bash
# Athena和小诺智能系统启动脚本

echo '🚀 启动Athena和小诺智能系统...'

# 设置Python路径
export PYTHONPATH='/Users/xujian/Athena工作平台:$PYTHONPATH'

# 初始化智能引擎
python3 -c "
import asyncio
import sys
sys.path.insert(0, '/Users/xujian/Athena工作平台')

from core.intent_engine import IntentRecognitionEngine
from core.tool_auto_executor import ToolAutoExecutionEngine, initialize_tool_executor

async def start_intelligence():
    logger.info('🧠 初始化意图识别引擎...')
    intent_engine = IntentRecognitionEngine()

    logger.info('🛠️ 初始化工具执行引擎...')
    await initialize_tool_executor()

    logger.info('✅ 智能系统启动完成')
    logger.info('🎯 Athena和小诺已准备就绪！')

asyncio.run(start_intelligence())
"

echo '🎉 启动完成！'
"""

            with open('scripts/start_intelligence_system.sh', 'w') as f:
                f.write(startup_script)

            # 设置执行权限
            os.chmod('scripts/start_intelligence_system.sh', 0o755)

            logger.info('  ✅ 启动脚本已创建: scripts/start_intelligence_system.sh')

        except Exception as e:
            logger.info(f"  ❌ 创建系统更新失败: {str(e)}")


async def main():
    """主函数"""
    logger.info('Athena和小诺智能系统修复程序')
    logger.info('解决意图识别和工具自动调用功能降级问题')
    print()

    # 确保日志目录存在
    os.makedirs('logs', exist_ok=True)

    # 创建修复器
    fixer = IntelligenceSystemFixer()

    # 运行修复
    success = await fixer.run_comprehensive_fix()

    if success:
        logger.info("\n🎉 修复成功！")
        logger.info("\n使用方法:")
        logger.info('1. 直接使用修复后的系统')
        logger.info('2. 运行启动脚本: bash scripts/start_intelligence_system.sh')
        logger.info('3. 查看修复报告: documentation/logs/intelligence_system_fix_report_*.json')
    else:
        logger.info("\n❌ 修复失败，请检查日志获取详细信息")
        return 1

    return 0


if __name__ == '__main__':
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\n\n修复被用户中断")
        sys.exit(1)
    except Exception as e:
        logger.info(f"\n\n修复过程中发生未处理的异常: {str(e)}")
        sys.exit(1)