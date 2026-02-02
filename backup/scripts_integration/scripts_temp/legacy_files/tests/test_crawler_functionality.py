#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Athena工作平台爬虫系统功能性测试脚本
Crawler System Functionality Test Script
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

# 添加路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'services'))
sys.path.insert(0, str(project_root / 'services' / 'patents'))

class CrawlerFunctionalityTester:
    """爬虫功能测试器"""

    def __init__(self):
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'system': 'Athena工作平台爬虫系统',
            'tests': {},
            'summary': {}
        }

    def log_test(self, test_name: str, status: str, message: str, data=None):
        """记录测试结果"""
        if test_name not in self.test_results['tests']:
            self.test_results['tests'][test_name] = []

        result = {
            'status': status,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        if data:
            result['data'] = data

        self.test_results['tests'][test_name].append(result)

        # 显示结果
        status_icon = {'✅': 'PASS', '❌': 'FAIL', '⚠️': 'WARN'}.get(status[:1], status)
        logger.info(f"{status} {test_name}: {message}")

    def test_patent_search_basic(self):
        """测试基础专利搜索功能"""
        logger.info("\n🔍 测试基础专利搜索功能...")

        try:
            from enhanced_patent_search import EnhancedPatentSearchSystem

            # 初始化系统
            search_system = EnhancedPatentSearchSystem()
            self.log_test('专利搜索初始化', '✅', 'EnhancedPatentSearchSystem 初始化成功')

            # 测试搜索功能（即使没有数据）
            test_keywords = ['人工智能', '机器学习', '区块链']

            for keyword in test_keywords:
                try:
                    results = search_system.search_local_patents(keyword, limit=5)

                    if isinstance(results, pd.DataFrame):
                        count = len(results)
                        self.log_test(f"专利搜索-{keyword}', '✅', f'搜索'{keyword}'成功，找到{count}条结果", {
                            'keyword': keyword,
                            'result_count': count
                        })
                    else:
                        self.log_test(f"专利搜索-{keyword}', '⚠️', f'搜索返回非DataFrame结果: {type(results)}")

                except Exception as e:
                    self.log_test(f"专利搜索-{keyword}', '❌', f'搜索'{keyword}'失败: {str(e)}")

            # 测试数据库功能
            try:
                db_path = search_system.indexed_db_path
                if db_path.exists():
                    self.log_test('专利数据库', '✅', f"专利数据库存在: {db_path}")
                else:
                    self.log_test('专利数据库', 'ℹ️', '专利数据库将首次使用时创建')
            except Exception as e:
                self.log_test('专利数据库', '❌', f"数据库检查失败: {str(e)}")

        except Exception as e:
            self.log_test('专利搜索基础', '❌', f"专利搜索系统加载失败: {str(e)}")

    def test_google_patents_service(self):
        """测试Google Patents服务"""
        logger.info("\n🌐 测试Google Patents服务...")

        try:
            sys.path.append(str(project_root / 'services' / 'patents'))
            from optimized_google_patents_service import OptimizedGooglePatentsService

            service = OptimizedGooglePatentsService()
            self.log_test('Google Patents初始化', '✅', 'OptimizedGooglePatentsService 初始化成功')

            # 测试专利号搜索方法
            if hasattr(service, 'search_patent_by_number'):
                try:
                    result = service.search_patent_by_number('CN123456789A')
                    self.log_test('专利号搜索', '✅', '专利号搜索方法调用成功', {
                        'has_result': result is not None
                    })
                except Exception as e:
                    self.log_test('专利号搜索', '⚠️', f"专利号搜索调用失败: {str(e)}")
            else:
                self.log_test('专利号搜索', 'ℹ️', '专利号搜索方法不存在')

            # 测试缓存机制
            try:
                cache_key = service._get_cache_key('TEST123')
                is_valid = service._is_cache_valid('TEST123')
                self.log_test('缓存机制', '✅', '缓存机制正常', {
                    'cache_key': cache_key,
                    'cache_valid': is_valid
                })
            except Exception as e:
                self.log_test('缓存机制', '❌', f"缓存测试失败: {str(e)}")

        except Exception as e:
            self.log_test('Google Patents服务', '❌', f"服务加载失败: {str(e)}")

    def test_external_connectivity(self):
        """测试外部连接性"""
        logger.info("\n🌐 测试外部连接性...")

        # 测试网络连接
        test_urls = [
            ('Google Patents', 'https://patents.google.com'),
            ('Baidu', 'https://www.baidu.com'),
            ('CNIPA', 'https://www.cnipa.gov.cn')
        ]

        for name, url in test_urls:
            try:
                response = requests.get(url, timeout=10, headers={
                    'User-Agent': 'Mozilla/5.0 (compatible; Athena-Crawler/1.0)'
                })

                if response.status_code == 200:
                    self.log_test(f"外部连接-{name}', '✅', f'{name} 连接成功", {
                        'response_time': response.elapsed.total_seconds(),
                        'status_code': response.status_code
                    })
                else:
                    self.log_test(f"外部连接-{name}', '⚠️', f'{name} 连接异常，状态码: {response.status_code}")

            except requests.exceptions.Timeout:
                self.log_test(f"外部连接-{name}', '⚠️', f'{name} 连接超时")
            except Exception as e:
                self.log_test(f"外部连接-{name}', '❌', f'{name} 连接失败: {str(e)}")

    def test_data_storage(self):
        """测试数据存储"""
        logger.info("\n💾 测试数据存储...")

        base_path = project_root / 'data' / 'patents'
        storage_dirs = ['raw', 'processed', 'cache', 'exports', 'logs']

        for dir_name in storage_dirs:
            dir_path = base_path / dir_name
            try:
                dir_path.mkdir(parents=True, exist_ok=True)

                # 测试写入权限
                test_file = dir_path / 'test_write.tmp'
                test_file.write_text('test')
                test_file.unlink()

                self.log_test(f"数据存储-{dir_name}', '✅', f'{dir_name} 目录读写正常", {
                    'path': str(dir_path)
                })

            except Exception as e:
                self.log_test(f"数据存储-{dir_name}', '❌', f'{dir_name} 目录测试失败: {str(e)}")

    def test_crawler_components(self):
        """测试爬虫组件"""
        logger.info("\n🔧 测试爬虫组件...")

        components = [
            ('专利分析引擎', 'patent_analysis_engine', 'PatentAnalysisEngine'),
            ('专利文档检索', 'patent_document_retriever', 'PatentDocumentRetriever'),
            ('专利专业搜索', 'patent_professional_search', 'PatentProfessionalSearchSystem'),
            ('专利批量处理', 'patent_batch_processor', 'PatentBatchProcessor')
        ]

        for name, module_name, class_name in components:
            try:
                module = __import__(module_name, fromlist=[class_name])
                service_class = getattr(module, class_name)

                # 尝试实例化
                instance = service_class()
                self.log_test(f"爬虫组件-{name}', '✅', f'{name} 组件正常", {
                    'class': str(type(instance))
                })

            except Exception as e:
                self.log_test(f"爬虫组件-{name}', '❌', f'{name} 组件失败: {str(e)}")

    def test_performance_monitoring(self):
        """测试性能监控"""
        logger.info("\n📊 测试性能监控...")

        try:
            # 检查性能优化器
            sys.path.append(str(project_root / 'tools' / 'optimization'))
            import crawler_performance_optimizer

            self.log_test('性能监控', '✅', '爬虫性能优化器可用')

            # 检查系统资源
            import psutil

            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()

            self.log_test('系统资源', '✅', '系统资源监控正常', {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'available_memory_gb': memory.available / (1024**3)
            })

        except Exception as e:
            self.log_test('性能监控', '❌', f"性能监控测试失败: {str(e)}")

    def calculate_summary(self):
        """计算测试总结"""
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        warning_tests = 0

        for test_category, tests in self.test_results['tests'].items():
            for test in tests:
                total_tests += 1
                if '✅' in test['status']:
                    passed_tests += 1
                elif '❌' in test['status']:
                    failed_tests += 1
                elif '⚠️' in test['status']:
                    warning_tests += 1

        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        self.test_results['summary'] = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'warning_tests': warning_tests,
            'success_rate': success_rate,
            'overall_status': 'healthy' if failed_tests == 0 else 'degraded' if failed_tests <= 2 else 'unhealthy'
        }

    def generate_report(self):
        """生成测试报告"""
        logger.info(str("\n" + '='*60))
        logger.info('📊 Athena工作平台爬虫系统功能性测试报告')
        logger.info(str('='*60))

        self.calculate_summary()
        summary = self.test_results['summary']

        # 整体状态
        status_icon = {
            'healthy': '✅ 健康',
            'degraded': '⚠️ 降级',
            'unhealthy': '❌ 异常'
        }.get(summary['overall_status'], '❓ 未知')

        logger.info(f"\n🎯 整体状态: {status_icon}")
        logger.info(f"📈 成功率: {summary['success_rate']:.1f}%")
        logger.info(f"✅ 通过: {summary['passed_tests']}")
        logger.info(f"❌ 失败: {summary['failed_tests']}")
        logger.info(f"⚠️  警告: {summary['warning_tests']}")
        logger.info(f"📋 总计: {summary['total_tests']}")

        logger.info(f"\n🔧 测试详情:")
        for category, tests in self.test_results['tests'].items():
            logger.info(f"\n  📂 {category}:")
            for test in tests:
                status_icon = {'✅': 'PASS', '❌': 'FAIL', '⚠️': 'WARN', 'ℹ️': 'INFO'}.get(test['status'][:1], test['status'])
                logger.info(f"    {status_icon} {test['message']}")

        logger.info(f"\n💡 系统评估:")
        if summary['overall_status'] == 'healthy':
            logger.info('  🎉 爬虫系统功能完整，所有组件正常工作')
        elif summary['overall_status'] == 'degraded':
            logger.info('  ⚠️  爬虫系统基本正常，存在一些需要优化的问题')
        else:
            logger.info('  🚨 爬虫系统存在多个问题，需要修复后才能正常运行')

        logger.info(f"\n🚀 下一步建议:")
        if summary['failed_tests'] > 0:
            logger.info('  1. 修复失败的测试组件')
        logger.info('  2. 运行完整爬虫任务验证实际功能')
        logger.info('  3. 启动监控面板观察系统性能')
        logger.info('  4. 检查数据存储和备份策略')

    def save_report(self, filename: str = None):
        """保存测试报告"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"crawler_functionality_test_{timestamp}.json"

        report_path = project_root / 'logs' / filename
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)

        logger.info(f"\n📄 测试报告已保存: {report_path}")
        return report_path

    def run_tests(self):
        """运行所有测试"""
        logger.info('🚀 开始Athena工作平台爬虫系统功能性测试...')
        logger.info(str('='*60))

        try:
            self.test_patent_search_basic()
            self.test_google_patents_service()
            self.test_external_connectivity()
            self.test_data_storage()
            self.test_crawler_components()
            self.test_performance_monitoring()

            # 生成报告
            self.generate_report()

            return self.test_results['summary']['overall_status']

        except Exception as e:
            logger.info(f"\n💥 测试过程中发生错误: {str(e)}")
            self.test_results['summary'] = {'overall_status': 'error'}
            return 'error'

def main():
    """主函数"""
    tester = CrawlerFunctionalityTester()

    try:
        status = tester.run_tests()

        # 保存报告
        tester.save_report()

        # 返回状态码
        status_code = {
            'healthy': 0,
            'degraded': 1,
            'unhealthy': 2,
            'error': 3
        }.get(status, 3)

        sys.exit(status_code)

    except KeyboardInterrupt:
        logger.info("\n\n⚠️  测试被用户中断")
        sys.exit(130)
    except Exception as e:
        logger.info(f"\n💥 程序异常: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()