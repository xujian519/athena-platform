#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小诺反思引擎测试脚本
Test Xiaonuo Reflection Engine Integration

测试小诺系统与反思引擎的集成效果，
验证反思功能的正确性和性能。

作者: Athena AI团队
创建时间: 2025-12-17
版本: v1.0.0 "功能验证"
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class XiaonuoReflectionTester:
    """小诺反思引擎测试器"""

    def __init__(self):
        self.test_results = []
        self.start_time = None
        self.end_time = None

    async def run_all_tests(self):
        """运行所有测试"""
        print("🧪 开始小诺反思引擎测试...")
        print("=" * 60)

        self.start_time = time.time()

        # 测试用例
        test_cases = [
            {
                "name": "基础响应测试",
                "prompt": "你好小诺",
                "expected_keywords": ["爸爸", "小诺"],
                "min_quality_score": 0.7
            },
            {
                "name": "需求分析测试",
                "prompt": "我需要一个新的功能来管理系统",
                "expected_keywords": ["需求", "分析", "计划"],
                "min_quality_score": 0.8
            },
            {
                "name": "技术支持测试",
                "prompt": "帮我设计一个数据库架构",
                "expected_keywords": ["技术", "方案", "设计"],
                "min_quality_score": 0.8
            },
            {
                "name": "情感交流测试",
                "prompt": "小诺，爸爸很想你",
                "expected_keywords": ["爱", "爸爸", "心里"],
                "min_quality_score": 0.9
            },
            {
                "name": "问题解决测试",
                "prompt": "系统出现了性能问题，如何解决？",
                "expected_keywords": ["问题", "解决方案", "分析"],
                "min_quality_score": 0.8
            },
            {
                "name": "计划规划测试",
                "prompt": "帮我制定下周的开发计划",
                "expected_keywords": ["计划", "时间", "安排"],
                "min_quality_score": 0.8
            }
        ]

        # 运行每个测试
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🔍 测试 {i}/{len(test_cases)}: {test_case['name']}")
            print("-" * 40)

            result = await self._run_single_test(test_case)
            self.test_results.append(result)

            # 显示测试结果
            self._display_test_result(result)

        self.end_time = time.time()

        # 生成测试报告
        await self._generate_test_report()

    async def _run_single_test(self, test_case: Dict) -> Dict[str, Any]:
        """运行单个测试"""
        try:
            # 导入小诺反思版本
            from xiaonuo_with_reflection_engine import XiaonuoWithReflection

            # 创建小诺实例
            xiaonuo = XiaonuoWithReflection()

            # 检查反思引擎是否启用
            reflection_enabled = xiaonuo.reflection_enabled

            # 构建测试上下文
            context = {
                'test_mode': True,
                'test_name': test_case['name'],
                'timestamp': datetime.now().isoformat()
            }

            # 执行测试
            start_time = time.time()
            result = await xiaonuo.process_with_reflection(
                prompt=test_case['prompt'],
                context=context
            )
            end_time = time.time()

            # 分析结果
            response = result.get('response', '')
            quality_score = result.get('quality_score', 0)
            reflection = result.get('reflection')
            processing_time = end_time - start_time

            # 检查期望关键词
            keyword_matches = []
            for keyword in test_case['expected_keywords']:
                if keyword in response:
                    keyword_matches.append(keyword)

            # 判断测试是否通过
            quality_pass = quality_score >= test_case['min_quality_score'] if quality_score else False
            keyword_pass = len(keyword_matches) >= len(test_case['expected_keywords']) * 0.5
            reflection_pass = reflection is not None if reflection_enabled else True

            test_passed = quality_pass and keyword_pass and reflection_pass

            return {
                'test_name': test_case['name'],
                'prompt': test_case['prompt'],
                'passed': test_passed,
                'response': response,
                'quality_score': quality_score,
                'quality_pass': quality_pass,
                'expected_keywords': test_case['expected_keywords'],
                'keyword_matches': keyword_matches,
                'keyword_pass': keyword_pass,
                'reflection_present': reflection is not None,
                'reflection_pass': reflection_pass,
                'reflection_enabled': reflection_enabled,
                'processing_time': processing_time,
                'suggestions': reflection.get('suggestions', []) if reflection else [],
                'should_refine': reflection.get('should_refine', False) if reflection else False,
                'error': None
            }

        except Exception as e:
            logger.error(f"测试执行失败: {e}")
            return {
                'test_name': test_case['name'],
                'prompt': test_case['prompt'],
                'passed': False,
                'error': str(e),
                'response': None,
                'quality_score': None,
                'reflection_enabled': False,
                'processing_time': 0
            }

    def _display_test_result(self, result: Dict):
        """显示测试结果"""
        status = "✅ 通过" if result['passed'] else "❌ 失败"
        print(f"状态: {status}")
        print(f"处理时间: {result['processing_time']:.2f}秒")

        if result.get('error'):
            print(f"错误: {result['error']}")
            return

        print(f"反思引擎: {'✅ 启用' if result['reflection_enabled'] else '❌ 未启用'}")

        if result['quality_score'] is not None:
            quality_status = "✅" if result['quality_pass'] else "❌"
            print(f"质量分数: {result['quality_score']:.2f} {quality_status}")

        print(f"关键词匹配: {len(result['keyword_matches'])}/{len(result['expected_keywords'])}")

        if result.get('response'):
            response_preview = result['response'][:100] + "..." if len(result['response']) > 100 else result['response']
            print(f"响应预览: {response_preview}")

        if result.get('reflection_present'):
            print(f"反思结果: ✅ 已执行")
            if result.get('should_refine'):
                print(f"改进建议: {len(result.get('suggestions', []))}条")

    async def _generate_test_report(self):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("📊 测试报告")
        print("=" * 60)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['passed'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0

        total_time = self.end_time - self.start_time

        print(f"\n📈 总体统计:")
        print(f"   总测试数: {total_tests}")
        print(f"   通过测试: {passed_tests}")
        print(f"   失败测试: {failed_tests}")
        print(f"   成功率: {success_rate:.1f}%")
        print(f"   总耗时: {total_time:.2f}秒")

        # 反思引擎统计
        reflection_enabled_tests = sum(1 for result in self.test_results if result.get('reflection_enabled'))
        print(f"\n🤔 反思引擎统计:")
        print(f"   启用反思的测试: {reflection_enabled_tests}/{total_tests}")

        if reflection_enabled_tests > 0:
            quality_scores = [r['quality_score'] for r in self.test_results if r.get('quality_score') is not None]
            if quality_scores:
                avg_quality = sum(quality_scores) / len(quality_scores)
                print(f"   平均质量分数: {avg_quality:.2f}")

            reflection_tests = sum(1 for result in self.test_results if result.get('reflection_present'))
            print(f"   执行反思的测试: {reflection_tests}")

        # 失败测试详情
        if failed_tests > 0:
            print(f"\n❌ 失败测试详情:")
            for result in self.test_results:
                if not result['passed']:
                    print(f"   • {result['test_name']}: {result.get('error', '质量或关键词不达标')}")

        # 性能统计
        processing_times = [r['processing_time'] for r in self.test_results if r.get('processing_time')]
        if processing_times:
            avg_time = sum(processing_times) / len(processing_times)
            max_time = max(processing_times)
            min_time = min(processing_times)
            print(f"\n⚡ 性能统计:")
            print(f"   平均处理时间: {avg_time:.2f}秒")
            print(f"   最长处理时间: {max_time:.2f}秒")
            print(f"   最短处理时间: {min_time:.2f}秒")

        # 保存详细报告
        await self._save_detailed_report()

    async def _save_detailed_report(self):
        """保存详细测试报告"""
        report = {
            'test_summary': {
                'total_tests': len(self.test_results),
                'passed_tests': sum(1 for r in self.test_results if r['passed']),
                'failed_tests': sum(1 for r in self.test_results if not r['passed']),
                'success_rate': (sum(1 for r in self.test_results if r['passed']) / len(self.test_results)) * 100,
                'total_time': self.end_time - self.start_time,
                'timestamp': datetime.now().isoformat()
            },
            'test_results': self.test_results,
            'reflection_stats': self._calculate_reflection_stats(),
            'performance_stats': self._calculate_performance_stats()
        }

        filename = f"xiaonuo_reflection_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n📄 详细报告已保存到: {filename}")

    def _calculate_reflection_stats(self) -> Dict:
        """计算反思统计信息"""
        reflection_enabled = [r for r in self.test_results if r.get('reflection_enabled')]
        if not reflection_enabled:
            return {'reflection_available': False}

        quality_scores = [r['quality_score'] for r in reflection_enabled if r.get('quality_score') is not None]
        reflection_performed = [r for r in reflection_enabled if r.get('reflection_present')]

        return {
            'reflection_available': True,
            'reflection_enabled_count': len(reflection_enabled),
            'reflection_performed_count': len(reflection_performed),
            'average_quality_score': sum(quality_scores) / len(quality_scores) if quality_scores else 0,
            'quality_score_distribution': {
                'min': min(quality_scores) if quality_scores else 0,
                'max': max(quality_scores) if quality_scores else 0,
                'avg': sum(quality_scores) / len(quality_scores) if quality_scores else 0
            }
        }

    def _calculate_performance_stats(self) -> Dict:
        """计算性能统计信息"""
        processing_times = [r['processing_time'] for r in self.test_results if r.get('processing_time')]
        if not processing_times:
            return {}

        return {
            'total_tests': len(processing_times),
            'average_time': sum(processing_times) / len(processing_times),
            'min_time': min(processing_times),
            'max_time': max(processing_times),
            'total_time': sum(processing_times)
        }

async def main():
    """主函数"""
    tester = XiaonuoReflectionTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())