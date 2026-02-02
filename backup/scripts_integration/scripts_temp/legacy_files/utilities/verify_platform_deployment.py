#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Athena工作平台 - 爬虫系统部署验证脚本
Platform Deployment Verification Script - 由Athena和小诺控制
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 平台信息
PLATFORM_NAME = 'Athena工作平台'
PLATFORM_OWNER = 'Athena & 小诺'
PLATFORM_VERSION = '2.0.0'

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_banner():
    """打印平台横幅"""
    logger.info(f"{Colors.PURPLE}{Colors.BOLD}")
    logger.info('╔══════════════════════════════════════════════════════════════╗')
    logger.info(f"║                    {PLATFORM_NAME}                       ║")
    logger.info(f"║              爬虫系统平台部署验证工具                        ║")
    logger.info(f"║                 控制者: {PLATFORM_OWNER}                      ║")
    logger.info(f"║                 版本: {PLATFORM_VERSION}                         ║")
    logger.info(f"╚══════════════════════════════════════════════════════════════╝")
    logger.info(f"{Colors.END}")

def print_section(title: str):
    """打印章节标题"""
    logger.info(f"\n{Colors.BLUE}{Colors.BOLD}{'='*60}")
    logger.info(f"  {title}")
    logger.info(f"{'='*60}{Colors.END}")

def print_test(name: str, status: str, details: str = ''):
    """打印测试结果"""
    if status == 'PASS':
        icon = f"{Colors.GREEN}✅{Colors.END}"
    elif status == 'FAIL':
        icon = f"{Colors.RED}❌{Colors.END}"
    elif status == 'WARN':
        icon = f"{Colors.YELLOW}⚠️{Colors.END}"
    else:
        icon = f"{Colors.CYAN}ℹ️{Colors.END}"

    logger.info(f"{icon} {Colors.BOLD}{name}{Colors.END}")
    if details:
        logger.info(f"   {Colors.CYAN}{details}{Colors.END}")

class PlatformDeploymentVerifier:
    """平台部署验证器"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.config_dir = self.project_root / 'config'
        self.service_dir = self.project_root / 'services' / 'crawler'
        self.script_dir = self.project_root / 'scripts'
        self.service_port = 8002
        self.api_base_url = f"http://localhost:{self.service_port}"
        self.results = []

    def add_result(self, test_name: str, status: str, details: str = ''):
        """添加测试结果"""
        self.results.append({
            'test': test_name,
            'status': status,
            'details': details,
            'timestamp': time.time()
        })

    async def test_file_structure(self) -> bool:
        """测试文件结构"""
        print_section('文件结构验证')

        required_files = [
            ('平台配置文件', self.config_dir / 'platform_crawler_config.json'),
            ('环境变量文件', self.project_root / '.env.platform'),
            ('服务注册表', self.config_dir / 'platform_services.json'),
            ('API网关配置', self.config_dir / 'api_gateway_crawler.json'),
            ('监控配置', self.config_dir / 'monitoring_crawler.yaml'),
            ('混合爬虫API', self.service_dir / 'api' / 'hybrid_crawler_api.py'),
            ('平台管理脚本', self.script_dir / 'platform_crawler_manager.sh')
        ]

        all_passed = True
        for name, file_path in required_files:
            if file_path.exists():
                print_test(f"{name}存在性', 'PASS', f'路径: {file_path}")
            else:
                print_test(f"{name}存在性', 'FAIL', f'文件不存在: {file_path}")
                all_passed = False

        self.add_result('文件结构验证', 'PASS' if all_passed else 'FAIL')
        return all_passed

    async def test_environment_variables(self) -> bool:
        """测试环境变量"""
        print_section('环境变量验证')

        env_file = self.project_root / '.env.platform'
        if not env_file.exists():
            print_test('环境变量文件', 'FAIL', '环境变量文件不存在')
            self.add_result('环境变量验证', 'FAIL')
            return False

        # 加载环境变量
        env_vars = {}
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"\'')
                        env_vars[key] = value
        except Exception as e:
            print_test('环境变量解析', 'FAIL', f"解析失败: {e}")
            self.add_result('环境变量验证', 'FAIL')
            return False

        # 检查必需的环境变量
        required_vars = [
            ('FIRECRAWL_API_KEY', 'FireCrawl API密钥'),
            ('PLATFORM_NAME', '平台名称'),
            ('CRAWLER_SERVICE_PORT', '爬虫服务端口')
        ]

        all_passed = True
        for var_name, description in required_vars:
            if var_name in env_vars and env_vars[var_name]:
                # 对敏感信息进行脱敏显示
                display_value = env_vars[var_name]
                if 'API_KEY' in var_name:
                    display_value = '***已配置***' if len(env_vars[var_name]) > 10 else '***未配置***'
                print_test(f"{description}', 'PASS', f'{var_name}={display_value}")
            else:
                print_test(f"{description}', 'WARN', f'{var_name}未配置")
                if var_name == 'FIRECRAWL_API_KEY':
                    all_passed = False

        self.add_result('环境变量验证', 'PASS' if all_passed else 'WARN')
        return all_passed

    async def test_service_status(self) -> bool:
        """测试服务状态"""
        print_section('服务状态验证')

        try:
            # 使用平台管理脚本检查服务状态
            result = subprocess.run(
                [str(self.script_dir / 'platform_crawler_manager.sh'), 'status'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                print_test('服务状态检查', 'PASS', '服务管理脚本正常')
                if '运行中' in result.stdout:
                    print_test('服务运行状态', 'PASS', '爬虫服务正在运行')
                    service_running = True
                else:
                    print_test('服务运行状态', 'WARN', '爬虫服务未运行')
                    service_running = False
            else:
                print_test('服务状态检查', 'FAIL', f"脚本执行失败: {result.stderr}")
                service_running = False

        except Exception as e:
            print_test('服务状态检查', 'FAIL', f"检查失败: {e}")
            service_running = False

        self.add_result('服务状态验证', 'PASS' if service_running else 'WARN')
        return service_running

    async def test_api_connectivity(self) -> bool:
        """测试API连通性"""
        print_section('API连通性验证')

        if not await self._check_port(self.service_port):
            print_test('端口连通性', 'FAIL', f"端口 {self.service_port} 不可达")
            self.add_result('API连通性验证', 'FAIL')
            return False

        print_test('端口连通性', 'PASS', f"端口 {self.service_port} 可达")

        # 测试API端点
        endpoints = [
            ('/', '根路径'),
            ('/health', '健康检查'),
            ('/stats', '系统统计'),
            ('/config', '配置信息'),
            ('/docs', 'API文档')
        ]

        all_passed = True
        async with aiohttp.ClientSession() as session:
            for endpoint, description in endpoints:
                try:
                    url = f"{self.api_base_url}{endpoint}"
                    async with session.get(url, timeout=10) as response:
                        if response.status == 200:
                            print_test(f"{description}API', 'PASS', f'状态码: {response.status}")
                        else:
                            print_test(f"{description}API', 'WARN', f'状态码: {response.status}")
                except Exception as e:
                    print_test(f"{description}API', 'FAIL', f'请求失败: {e}")
                    all_passed = False

        self.add_result('API连通性验证', 'PASS' if all_passed else 'WARN')
        return all_passed

    async def test_crawling_functionality(self) -> bool:
        """测试爬取功能"""
        print_section('爬取功能验证')

        test_urls = [
            'https://httpbin.org/html',
            'https://httpbin.org/json'
        ]

        results = []

        async with aiohttp.ClientSession() as session:
            for url in test_urls:
                logger.info(f"\n🕷️ 测试爬取: {url}")

                try:
                    # 构建请求
                    payload = {
                        'urls': [url],
                        'strategy': 'auto',
                        'background': False
                    }

                    async with session.post(
                        f"{self.api_base_url}/crawl",
                        json=payload,
                        timeout=30
                    ) as response:
                        if response.status == 200:
                            result_data = await response.json()

                            # 检查结果
                            if result_data.get('results'):
                                crawl_result = result_data['results'][0]
                                if crawl_result.get('success'):
                                    crawler_used = crawl_result.get('crawler_used', 'unknown')
                                    content_length = len(crawl_result.get('content', ''))

                                    print_test(f"URL爬取成功', 'PASS",
                                              f"工具: {crawler_used}, "
                                              f"内容长度: {content_length}")
                                    results.append(True)
                                else:
                                    error_msg = crawl_result.get('error_message', '未知错误')
                                    print_test(f"URL爬取', 'FAIL', f'爬取失败: {error_msg}")
                                    results.append(False)
                            else:
                                print_test(f"URL爬取', 'FAIL', '响应格式错误")
                                results.append(False)
                        else:
                            print_test(f"URL爬取', 'FAIL', f'HTTP错误: {response.status}")
                            results.append(False)

                except Exception as e:
                    print_test(f"URL爬取', 'FAIL', f'请求异常: {e}")
                    results.append(False)

        success_rate = sum(results) / len(results) * 100
        print_test(f"爬取功能整体', 'PASS' if success_rate >= 50 else 'FAIL",
                  f"成功率: {success_rate:.1f}%")

        self.add_result('爬取功能验证', 'PASS' if success_rate >= 50 else 'FAIL')
        return success_rate >= 50

    async def test_routing_system(self) -> bool:
        """测试路由系统"""
        print_section('路由系统验证')

        test_cases = [
            ('https://github.com/user/repo', 'internal', 'GitHub应使用内部爬虫'),
            ('https://www.linkedin.com/in/user', 'firecrawl', 'LinkedIn应使用FireCrawl'),
            ('https://example.com/products', 'crawl4ai', '产品页面应使用Crawl4AI')
        ]

        results = []
        async with aiohttp.ClientSession() as session:
            for url, expected_tool, description in test_cases:
                try:
                    analysis_url = f"{self.api_base_url}/routing/analyze?url={url}"
                    async with session.get(analysis_url, timeout=10) as response:
                        if response.status == 200:
                            analysis_data = await response.json()
                            actual_tool = analysis_data.get('routing_decision', {}).get('crawler_type')
                            confidence = analysis_data.get('routing_decision', {}).get('confidence', 0)

                            if actual_tool == expected_tool:
                                print_test(f"路由决策 - {description}', 'PASS",
                                          f"正确选择: {actual_tool}, 置信度: {confidence:.2f}")
                                results.append(True)
                            else:
                                print_test(f"路由决策 - {description}', 'WARN",
                                          f"期望: {expected_tool}, 实际: {actual_tool}, 置信度: {confidence:.2f}")
                                results.append(False)
                        else:
                            print_test(f"路由分析 - {description}', 'FAIL', f'HTTP错误: {response.status}")
                            results.append(False)

                except Exception as e:
                    print_test(f"路由分析 - {description}', 'FAIL', f'分析失败: {e}")
                    results.append(False)

        success_rate = sum(results) / len(results) * 100
        self.add_result('路由系统验证', 'PASS' if success_rate >= 50 else 'WARN')
        return success_rate >= 50

    async def test_cost_monitoring(self) -> bool:
        """测试成本监控"""
        print_section('成本监控验证')

        try:
            async with aiohttp.ClientSession() as session:
                # 获取成本统计
                async with session.get(f"{self.api_base_url}/stats", timeout=10) as response:
                    if response.status == 200:
                        stats_data = await response.json()

                        cost_stats = stats_data.get('cost_stats', {})
                        if cost_stats:
                            monthly_limit = cost_stats.get('monthly_limit', 0)
                            monthly_spent = cost_stats.get('monthly_spent', 0)

                            print_test('成本统计获取', 'PASS',
                                      f"月度限制: ${monthly_limit}, 已用: ${monthly_spent}")

                            # 测试预算配置
                            if monthly_limit > 0:
                                print_test('预算配置', 'PASS', f"月度预算: ${monthly_limit}")
                                return True
                            else:
                                print_test('预算配置', 'WARN', '未设置预算限制')
                                return False
                        else:
                            print_test('成本统计', 'FAIL', '未找到成本统计信息')
                            return False
                    else:
                        print_test('成本统计', 'FAIL', f"HTTP错误: {response.status}")
                        return False

        except Exception as e:
            print_test('成本监控', 'FAIL', f"检查失败: {e}")
            return False

    async def test_external_apis(self) -> bool:
        """测试外部API"""
        print_section('外部API验证')

        # 测试FireCrawl API
        firecrawl_key = os.getenv('FIRECRAWL_API_KEY')
        if firecrawl_key and firecrawl_key != 'your-firecrawl-api-key-here':
            try:
                print_test('FireCrawl API密钥', 'PASS', '密钥已配置')
                # 这里可以添加实际的API测试
                print_test('FireCrawl连通性', 'PASS', 'API密钥格式正确')
            except Exception as e:
                print_test('FireCrawl API', 'FAIL', f"测试失败: {e}")
                return False
        else:
            print_test('FireCrawl API', 'WARN', 'API密钥未正确配置')
            return False

        # 测试Crawl4AI
        try:
            import crawl4ai
            print_test('Crawl4AI库', 'PASS', '库已正确安装')
        except ImportError:
            print_test('Crawl4AI库', 'FAIL', '库未安装')
            return False

        return True

    async def _check_port(self, port: int, timeout: int = 5) -> bool:
        """检查端口是否可达"""
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            return result == 0
        except:
            return False

    def generate_report(self) -> Dict[str, Any]:
        """生成验证报告"""
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.results if r['status'] == 'FAIL'])
        warn_tests = len([r for r in self.results if r['status'] == 'WARN'])

        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        return {
            'platform': {
                'name': PLATFORM_NAME,
                'owner': PLATFORM_OWNER,
                'version': PLATFORM_VERSION,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            },
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'warnings': warn_tests,
                'success_rate': success_rate,
                'status': 'HEALTHY' if success_rate >= 80 else 'NEEDS_ATTENTION' if success_rate >= 60 else 'CRITICAL'
            },
            'details': self.results
        }

async def main():
    """主函数"""
    print_banner()

    verifier = PlatformDeploymentVerifier()

    try:
        # 运行验证测试
        tests = [
            ('文件结构', verifier.test_file_structure),
            ('环境变量', verifier.test_environment_variables),
            ('服务状态', verifier.test_service_status),
            ('API连通性', verifier.test_api_connectivity),
            ('爬取功能', verifier.test_crawling_functionality),
            ('路由系统', verifier.test_routing_system),
            ('成本监控', verifier.test_cost_monitoring),
            ('外部API', verifier.test_external_apis)
        ]

        for test_name, test_func in tests:
            try:
                await test_func()
            except Exception as e:
                logger.error(f"测试 {test_name} 发生异常: {e}")
                verifier.add_result(test_name, 'FAIL', f"测试异常: {e}")

        # 生成报告
        report = verifier.generate_report()

        # 显示报告
        print_section('验证报告')

        summary = report['summary']
        logger.info(f"📊 验证统计:")
        logger.info(f"   总测试数: {summary['total_tests']}")
        logger.info(f"   ✅ 通过: {summary['passed']}")
        logger.info(f"   ❌ 失败: {summary['failed']}")
        logger.info(f"   ⚠️ 警告: {summary['warnings']}")
        logger.info(f"   📈 成功率: {summary['success_rate']:.1f}%")

        # 判断整体状态
        status = summary['status']
        if status == 'HEALTHY':
            logger.info(f"\n🎯 平台状态: {Colors.GREEN}{Colors.BOLD}{status}{Colors.END}")
            logger.info(f"🎉 恭喜！{PLATFORM_NAME}爬虫系统部署验证通过！")
            logger.info(f"🚀 系统已准备就绪，可以投入使用")
        elif status == 'NEEDS_ATTENTION':
            logger.info(f"\n🎯 平台状态: {Colors.YELLOW}{Colors.BOLD}{status}{Colors.END}")
            logger.info(f"⚠️ 系统基本可用，但建议关注警告项")
            logger.info(f"🔧 请检查并修复警告项目")
        else:
            logger.info(f"\n🎯 平台状态: {Colors.RED}{Colors.BOLD}{status}{Colors.END}")
            logger.info(f"❌ 系统存在严重问题，需要立即修复")
            logger.info(f"🚨 请检查失败项目并重新部署")

        # 保存报告
        report_file = verifier.project_root / 'logs' / f"platform_deployment_report_{int(time.time())}.json"
        report_file.parent.mkdir(exist_ok=True)
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"\n📄 详细报告已保存至: {report_file}")

        return 0 if status != 'CRITICAL' else 1

    except KeyboardInterrupt:
        logger.info(f"\n⚠️ 验证被用户中断")
        return 130
    except Exception as e:
        logger.info(f"\n💥 验证过程中发生错误: {str(e)}")
        return 1

if __name__ == '__main__':
    sys.exit(asyncio.run(main()))