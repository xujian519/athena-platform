#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Athena工作平台爬虫系统完整性验证脚本
Crawler System Integrity Verification Script
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

logger = logging.getLogger(__name__)

# 添加路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'services'))
sys.path.insert(0, str(project_root / 'services' / 'patents'))

class CrawlerSystemVerifier:
    """爬虫系统验证器"""

    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'system': 'Athena工作平台爬虫系统',
            'components': {},
            'overall_status': 'unknown'
        }
        self.errors = []

    def log(self, component: str, status: str, message: str, details: dict = None):
        """记录验证结果"""
        if component not in self.results['components']:
            self.results['components'][component] = []

        result = {
            'status': status,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        if details:
            result['details'] = details

        self.results['components'][component].append(result)

        # 显示结果
        status_icon = {'✅': 'success', '⚠️': 'warning', '❌': 'error', 'ℹ️': 'info'}.get(status[:1], status)
        logger.info(f"{status} {component}: {message}")

    def verify_data_directories(self):
        """验证数据目录结构"""
        logger.info("\n🔍 验证数据目录结构...")

        base_path = project_root / 'data' / 'patents'
        required_dirs = ['raw', 'processed', 'cache', 'exports', 'logs']

        for dir_name in required_dirs:
            dir_path = base_path / dir_name
            if dir_path.exists():
                file_count = len(list(dir_path.glob('*')))
                self.log('数据目录', '✅', f"{dir_name} 目录存在，包含 {file_count} 个文件', {'path": str(dir_path)})
            else:
                self.log('数据目录', '❌', f"{dir_name} 目录不存在', {'path": str(dir_path)})
                # 创建目录
                dir_path.mkdir(parents=True, exist_ok=True)
                self.log('数据目录', 'ℹ️', f"已创建 {dir_name} 目录', {'path": str(dir_path)})

    def verify_patent_services(self):
        """验证专利服务模块"""
        logger.info("\n🔍 验证专利服务模块...")

        services = [
            ('enhanced_patent_search', 'EnhancedPatentSearchSystem'),
            ('patents/optimized_google_patents_service', 'OptimizedGooglePatentsService'),
            ('patent_analysis_engine', 'PatentAnalysisEngine'),
            ('patent_document_retriever', 'PatentDocumentRetriever'),
            ('patent_professional_search', 'PatentProfessionalSearchSystem')
        ]

        for module_name, class_name in services:
            try:
                module = __import__(module_name, fromlist=[class_name])
                service_class = getattr(module, class_name)

                # 尝试实例化
                if 'google' in module_name.lower():
                    # Google Patents服务可能需要网络，简单检查导入
                    self.log('专利服务', '✅', f"{class_name} 模块导入成功")
                else:
                    instance = service_class()
                    self.log('专利服务', '✅', f"{class_name} 实例化成功', {'class": str(type(instance))})

            except Exception as e:
                self.log('专利服务', '❌', f"{class_name} 加载失败: {str(e)}")
                self.errors.append(f"专利服务 {class_name}: {str(e)}")

    def verify_patent_search_functionality(self):
        """验证专利搜索功能"""
        logger.info("\n🔍 验证专利搜索功能...")

        try:
            from enhanced_patent_search import EnhancedPatentSearchSystem

            # 初始化系统
            search_system = EnhancedPatentSearchSystem()

            # 测试本地搜索（不需要网络）
            test_keywords = '人工智能'
            results = search_system.search_local_patents(test_keywords, limit=5)

            if isinstance(results, pd.DataFrame):
                count = len(results)
                self.log('专利搜索', '✅', f"本地搜索成功，找到 {count} 条结果", {
                    'keywords': test_keywords,
                    'columns': list(results.columns)[:3] if len(results.columns) > 3 else list(results.columns)
                })
            else:
                self.log('专利搜索', '⚠️', f"本地搜索返回非DataFrame结果: {type(results)}")

        except Exception as e:
            self.log('专利搜索', '❌', f"专利搜索功能测试失败: {str(e)}")
            self.errors.append(f"专利搜索: {str(e)}")

    def verify_database_connections(self):
        """验证数据库连接"""
        logger.info("\n🔍 验证数据库连接...")

        # 检查SQLite数据库
        try:
            import sqlite3
            db_path = project_root / 'data' / 'patents' / 'processed' / 'indexed_patents.db'

            if db_path.exists():
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                conn.close()

                self.log('数据库', '✅', f"SQLite数据库连接正常，包含 {len(tables)} 个表", {
                    'path': str(db_path),
                    'tables': [t[0] for t in tables]
                })
            else:
                self.log('数据库', 'ℹ️', f"SQLite数据库文件不存在，将在首次使用时创建", {
                    'path': str(db_path)
                })

        except Exception as e:
            self.log('数据库', '❌', f"数据库连接失败: {str(e)}")
            self.errors.append(f"数据库连接: {str(e)}")

    def verify_external_apis(self):
        """验证外部API连接"""
        logger.info("\n🔍 验证外部API连接...")

        # 测试Google Patents API可访问性
        try:
            response = requests.get('https://patents.google.com', timeout=10)
            if response.status_code == 200:
                self.log('外部API', '✅', 'Google Patents 网站可访问', {
                    'status_code': response.status_code,
                    'response_time': response.elapsed.total_seconds()
                })
            else:
                self.log('外部API', '⚠️', f"Google Patents 访问异常，状态码: {response.status_code}")

        except requests.exceptions.Timeout:
            self.log('外部API', '⚠️', 'Google Patents 访问超时')
        except Exception as e:
            self.log('外部API', '❌', f"Google Patents 连接失败: {str(e)}")

    def verify_configuration_files(self):
        """验证配置文件"""
        logger.info("\n🔍 验证配置文件...")

        config_files = [
            'services/common_tools/crawler_tool.py',
            'misc/production/crawler/config/crawler_config.json',
            'services/patents/performance_config.py'
        ]

        for config_file in config_files:
            config_path = project_root / config_file
            if config_path.exists():
                self.log('配置文件', '✅', f"配置文件存在: {config_file}")
            else:
                self.log('配置文件', '⚠️', f"配置文件不存在: {config_file}")

    def verify_monitoring_tools(self):
        """验证监控工具"""
        logger.info("\n🔍 验证监控工具...")

        monitoring_tools = [
            'tools/monitoring/crawler_performance_dashboard.py',
            'tools/automation/crawler_auto_trigger.py',
            'tools/optimization/crawler_performance_optimizer.py'
        ]

        for tool_path in monitoring_tools:
            tool_file = project_root / tool_path
            if tool_file.exists():
                self.log('监控工具', '✅', f"监控工具存在: {tool_path}")
            else:
                self.log('监控工具', '⚠️', f"监控工具不存在: {tool_path}")

    def calculate_overall_status(self):
        """计算整体状态"""
        total_checks = 0
        success_checks = 0
        warning_checks = 0
        error_checks = 0

        for component, checks in self.results['components'].items():
            for check in checks:
                total_checks += 1
                if '✅' in check['status']:
                    success_checks += 1
                elif '⚠️' in check['status']:
                    warning_checks += 1
                elif '❌' in check['status']:
                    error_checks += 1

        success_rate = (success_checks / total_checks * 100) if total_checks > 0 else 0

        if error_checks == 0:
            if warning_checks == 0:
                self.results['overall_status'] = 'healthy'
            else:
                self.results['overall_status'] = 'degraded'
        else:
            self.results['overall_status'] = 'unhealthy'

        self.results['summary'] = {
            'total_checks': total_checks,
            'success_checks': success_checks,
            'warning_checks': warning_checks,
            'error_checks': error_checks,
            'success_rate': success_rate
        }

        return self.results['overall_status']

    def generate_report(self):
        """生成验证报告"""
        logger.info(str("\n" + '='*60))
        logger.info('📊 Athena工作平台爬虫系统验证报告')
        logger.info(str('='*60))

        overall_status = self.calculate_overall_status()
        summary = self.results['summary']

        # 整体状态
        status_icon = {
            'healthy': '✅ 健康',
            'degraded': '⚠️ 降级',
            'unhealthy': '❌ 异常'
        }.get(overall_status, '❓ 未知')

        logger.info(f"\n🎯 整体状态: {status_icon}")
        logger.info(f"📈 成功率: {summary['success_rate']:.1f}%")
        logger.info(f"✅ 成功: {summary['success_checks']}")
        logger.info(f"⚠️  警告: {summary['warning_checks']}")
        logger.info(f"❌ 错误: {summary['error_checks']}")
        logger.info(f"📋 总计: {summary['total_checks']}")

        # 错误详情
        if self.errors:
            logger.info(f"\n❌ 错误详情:")
            for i, error in enumerate(self.errors, 1):
                logger.info(f"  {i}. {error}")

        # 建议
        logger.info(f"\n💡 建议:")
        if overall_status == 'healthy':
            logger.info('  🎉 爬虫系统运行良好，所有组件正常')
        elif overall_status == 'degraded':
            logger.info('  ⚠️  系统基本正常，但存在一些警告，建议检查并优化')
        else:
            logger.info('  🚨 系统存在严重问题，需要立即修复')

        logger.info("\n🔧 下一步操作:")
        logger.info('  1. 运行完整爬虫测试: python3 scripts/test_crawler_functionality.py')
        logger.info('  2. 启动爬虫服务: ./scripts/start_patent_crawler.sh')
        logger.info('  3. 查看监控面板: python3 tools/monitoring/crawler_performance_dashboard.py')

    def save_report(self, filename: str = None):
        """保存报告"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"crawler_verification_report_{timestamp}.json"

        report_path = project_root / 'logs' / filename
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)

        logger.info(f"\n📄 验证报告已保存: {report_path}")
        return report_path

    def run_verification(self):
        """运行完整验证"""
        logger.info('🚀 开始Athena工作平台爬虫系统完整性验证...')
        logger.info(str('='*60))

        try:
            self.verify_data_directories()
            self.verify_patent_services()
            self.verify_patent_search_functionality()
            self.verify_database_connections()
            self.verify_external_apis()
            self.verify_configuration_files()
            self.verify_monitoring_tools()

            # 生成报告
            self.generate_report()

            return self.results['overall_status']

        except Exception as e:
            logger.info(f"\n💥 验证过程中发生错误: {str(e)}")
            self.results['overall_status'] = 'error'
            return 'error'

def main():
    """主函数"""
    verifier = CrawlerSystemVerifier()

    try:
        status = verifier.run_verification()

        # 保存报告
        verifier.save_report()

        # 返回状态码
        status_code = {
            'healthy': 0,
            'degraded': 1,
            'unhealthy': 2,
            'error': 3
        }.get(status, 3)

        sys.exit(status_code)

    except KeyboardInterrupt:
        logger.info("\n\n⚠️  验证被用户中断")
        sys.exit(130)
    except Exception as e:
        logger.info(f"\n💥 程序异常: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()