#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
法律知识图谱API服务修复工具
Legal Knowledge Graph API Service Fix Tool

修复API服务连接问题，重启服务，验证端到端功能
"""

import json
import logging
import os
import signal
import subprocess
import time
from datetime import datetime
from pathlib import Path

import psutil
import requests

logger = logging.getLogger(__name__)

class LegalKGAPIFixer:
    """法律知识图谱API修复器"""

    def __init__(self):
        PROJECT_ROOT = Path(__file__).resolve().parents[1]
        self.project_root = PROJECT_ROOT
        self.api_processes = {
            'knowledge_graph_api': {
                'script': 'domains/legal/apis/knowledge_graph_api.py',
                'port': 8002,
                'process_name': 'knowledge_graph_api.py',
            },
            'unified_knowledge_manager': {
                'script': 'domains/legal/apis/unified_knowledge_manager.py',
                'port': 8005,
                'process_name': 'unified_knowledge_manager.py',
            },
            'unified_intelligent_search': {
                'script': 'domains/legal/apis/unified_intelligent_search.py',
                'port': 8003,
                'process_name': 'unified_intelligent_search.py',
            },
            'legal_vector_api': {
                'script': 'domains/legal/apis/legal_vector_api.py',
                'port': 8001,
                'process_name': 'legal_vector_api.py',
            },
        }

        self.results = {
            'timestamp': datetime.now().isoformat(),
            'services_status': {},
            'fixes_applied': [],
            'end_to_end_tests': {},
            'overall_status': 'unknown',
        }

    def check_port_conflicts(self):
        """检查端口冲突"""
        logger.info('🔍 检查端口冲突...')

        port_conflicts = {}

        for service_name, service_info in self.api_processes.items():
            port = service_info['port']

            try:
                # 检查端口是否被占用
                for conn in psutil.net_connections():
                    if conn.laddr.port == port:
                        port_conflicts[port] = {
                            'service': service_name,
                            'pid': conn.pid,
                            'process_name': (
                                psutil.Process(conn.pid).name()
                                if conn.pid
                                else 'unknown'
                            ),
                        }
                        logger.info(str(
                            f"  ⚠️ 端口 {port} 被占用: {port_conflicts[port]['process_name']} (PID: {conn.pid}))"
                        )
                        break
                else:
                    logger.info(f"  ✅ 端口 {port} 可用")

            except Exception as e:
                logger.info(f"  ❌ 检查端口 {port} 失败: {str(e)}")

        return port_conflicts

    def kill_existing_processes(self, port_conflicts):
        """杀死占用端口的现有进程"""
        logger.info('🔪 杀死占用端口的现有进程...')

        killed_count = 0

        for port, conflict_info in port_conflicts.items():
            pid = conflict_info.get('pid')
            if pid:
                try:
                    # 优雅地终止进程
                    process = psutil.Process(pid)
                    process.terminate()

                    # 等待进程结束
                    try:
                        process.wait(timeout=5)
                        logger.info(f"  ✅ 终止进程 {pid} ({conflict_info['process_name']})")
                        killed_count += 1
                    except psutil.TimeoutExpired:
                        # 强制终止
                        process.kill()
                        logger.info(str(
                            f"  🔨 强制终止进程 {pid} ({conflict_info['process_name']}))"
                        )
                        killed_count += 1

                except psutil.NoSuchProcess:
                    logger.info(f"  ℹ️ 进程 {pid} 已不存在")
                except Exception as e:
                    logger.info(f"  ❌ 无法终止进程 {pid}: {str(e)}")

        # 等待端口释放
        logger.info('⏳ 等待端口释放...')
        time.sleep(2)

        return killed_count

    def start_api_services(self):
        """启动API服务"""
        logger.info('🚀 启动API服务...')

        started_services = []

        for service_name, service_info in self.api_processes.items():
            script_path = self.project_root / service_info['script']

            if not script_path.exists():
                logger.info(f"  ❌ 脚本不存在: {script_path}")
                self.results['services_status'][service_name] = {
                    'status': 'script_not_found',
                    'error': f"脚本不存在: {script_path}",
                }
                continue

            try:
                # 设置环境变量
                env = {
                    'PYTHONPATH': str(self.project_root),
                    'UNIFIED_KG_PATH': str(
                        self.project_root
                        / 'data'
                        / 'unified_legal_knowledge_graph.json'
                    ),
                    'TUGRAPH_GRAPH_NAME': 'unified_legal_knowledge_graph',
                    'TUGRAPH_HOST': 'localhost',
                    'TUGRAPH_PORT': '7687',
                }

                # 启动服务
                cmd = ['python3', str(script_path)]
                process = subprocess.Popen(
                    cmd,
                    cwd=str(self.project_root),
                    env={**os.environ, **env},
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )

                # 等待服务启动
                time.sleep(3)

                # 检查进程是否还在运行
                if process.poll() is None:
                    logger.info(f"  ✅ {service_name} 启动成功 (PID: {process.pid})")
                    started_services.append(
                        {
                            'name': service_name,
                            'pid': process.pid,
                            'port': service_info['port'],
                            'process': process,
                        }
                    )
                    self.results['services_status'][service_name] = {
                        'status': 'started',
                        'pid': process.pid,
                        'port': service_info['port'],
                    }
                else:
                    stdout, stderr = process.communicate()
                    logger.info(f"  ❌ {service_name} 启动失败:")
                    logger.info(f"    stdout: {stdout}")
                    logger.info(f"    stderr: {stderr}")
                    self.results['services_status'][service_name] = {
                        'status': 'failed_to_start',
                        'error': stderr,
                    }

            except Exception as e:
                logger.info(f"  ❌ {service_name} 启动异常: {str(e)}")
                self.results['services_status'][service_name] = {
                    'status': 'start_error',
                    'error': str(e),
                }

        logger.info(f"✅ 启动完成: {len(started_services)} 个服务")
        return started_services

    def test_api_endpoints(self, started_services):
        """测试API端点"""
        logger.info('🔍 测试API端点...')

        test_results = {}

        for service in started_services:
            service_name = service['name']
            port = service['port']

            # 根据服务类型选择测试端点
            if 'knowledge_graph' in service_name:
                endpoints = [
                    f"http://localhost:{port}/api/v1/graph/stats",
                    f"http://localhost:{port}/api/v1/graph/entities",
                    f"http://localhost:{port}/api/v1/graph/relations",
                ]
            elif 'manager' in service_name:
                endpoints = [
                    f"http://localhost:{port}/api/v1/health",
                    f"http://localhost:{port}/api/v1/entities/search",
                ]
            elif 'search' in service_name:
                endpoints = [
                    f"http://localhost:{port}/api/v1/health",
                    f"http://localhost:{port}/api/v1/search",
                ]
            else:  # legal_vector_api
                endpoints = [
                    f"http://localhost:{port}/api/v1/health",
                    f"http://localhost:{port}/api/v1/vector/search",
                ]

            service_tests = []

            for endpoint in endpoints:
                try:
                    response = requests.get(endpoint, timeout=10)
                    if response.status_code == 200:
                        service_tests.append(
                            {
                                'endpoint': endpoint,
                                'status': 'success',
                                'response_code': response.status_code,
                            }
                        )
                        logger.info(f"  ✅ {endpoint}: {response.status_code}")
                    else:
                        service_tests.append(
                            {
                                'endpoint': endpoint,
                                'status': f"http_{response.status_code}",
                                'response_code': response.status_code,
                            }
                        )
                        logger.info(f"  ⚠️ {endpoint}: HTTP {response.status_code}")

                except requests.exceptions.ConnectionError:
                    service_tests.append(
                        {
                            'endpoint': endpoint,
                            'status': 'connection_error',
                            'response_code': None,
                        }
                    )
                    logger.info(f"  ❌ {endpoint}: 连接失败")
                except Exception as e:
                    service_tests.append(
                        {
                            'endpoint': endpoint,
                            'status': 'error',
                            'response_code': None,
                            'error': str(e),
                        }
                    )
                    logger.info(f"  ❌ {endpoint}: {str(e)}")

            test_results[service_name] = service_tests
            self.results['end_to_end_tests'][service_name] = {
                'port': port,
                'tests': service_tests,
                'success_rate': len(
                    [t for t in service_tests if t['status'] == 'success']
                )
                / len(service_tests)
                * 100,
            }

        return test_results

    def test_unified_kg_functionality(self):
        """测试统一知识图谱功能"""
        logger.info('🧪 测试统一知识图谱功能...')

        test_results = {}

        # 测试知识图谱API
        try:
            # 获取图统计信息
            response = requests.get(
                'http://localhost:8002/api/v1/graph/stats', timeout=10
            )

            if response.status_code == 200:
                stats = response.json()
                test_results['graph_stats'] = {'status': 'success', 'data': stats}
                logger.info(f"  ✅ 图统计信息: {stats}")
            else:
                test_results['graph_stats'] = {
                    'status': 'http_error',
                    'response_code': response.status_code,
                }
                logger.info(f"  ❌ 图统计信息: HTTP {response.status_code}")

        except Exception as e:
            test_results['graph_stats'] = {'status': 'error', 'error': str(e)}
            logger.info(f"  ❌ 图统计信息: {str(e)}")

        # 测试实体搜索
        try:
            response = requests.get(
                'http://localhost:8005/api/v1/entities/search?q=宪法', timeout=10
            )

            if response.status_code == 200:
                entities = response.json()
                test_results['entity_search'] = {
                    'status': 'success',
                    'result_count': len(entities) if isinstance(entities, list) else 0,
                }
                logger.info(str(
                    f"  ✅ 实体搜索: 找到 {test_results['entity_search']['result_count']} 个结果"
                ))
            else:
                test_results['entity_search'] = {
                    'status': 'http_error',
                    'response_code': response.status_code,
                }
                logger.info(f"  ❌ 实体搜索: HTTP {response.status_code}")

        except Exception as e:
            test_results['entity_search'] = {'status': 'error', 'error': str(e)}
            logger.info(f"  ❌ 实体搜索: {str(e)}")

        # 测试智能搜索
        try:
            response = requests.post(
                'http://localhost:8003/api/v1/search',
                json={'query': '民法典', 'limit': 5},
                timeout=10,
            )

            if response.status_code == 200:
                results = response.json()
                test_results['intelligent_search'] = {
                    'status': 'success',
                    'result_count': len(results.get('results', [])),
                }
                logger.info(str(
                    f"  ✅ 智能搜索: 找到 {test_results['intelligent_search']['result_count']} 个结果"
                ))
            else:
                test_results['intelligent_search'] = {
                    'status': 'http_error',
                    'response_code': response.status_code,
                }
                logger.info(f"  ❌ 智能搜索: HTTP {response.status_code}")

        except Exception as e:
            test_results['intelligent_search'] = {'status': 'error', 'error': str(e)}
            logger.info(f"  ❌ 智能搜索: {str(e)}")

        self.results['end_to_end_tests']['unified_kg_functionality'] = test_results
        return test_results

    def generate_fix_report(
        self,
        port_conflicts,
        killed_processes,
        started_services,
        test_results,
        functionality_tests,
    ):
        """生成修复报告"""
        logger.info('📄 生成修复报告...')

        # 计算整体状态
        total_services = len(self.api_processes)
        working_services = sum(
            1
            for service in started_services
            if any(
                test['status'] == 'success'
                for test in self.results['end_to_end_tests']
                .get(service['name'], {})
                .get('tests', [])
            )
        )

        if working_services == total_services:
            overall_status = '✅ 全部正常'
        elif working_services >= total_services * 0.5:
            overall_status = '⚠️ 部分正常'
        else:
            overall_status = '❌ 需要修复'

        self.results['overall_status'] = overall_status

        report_content = f"""# 法律知识图谱API服务修复报告

**修复时间**: {self.results['timestamp']}
**修复工具**: Athena API修复器
**整体状态**: {overall_status}

---

## 📊 修复统计

- 🚫 发现端口冲突: {len(port_conflicts)} 个
- 🔪 终止冲突进程: {killed_processes} 个
- 🚀 启动API服务: {len(started_services)} 个
- ✅ 正常运行服务: {working_services}/{total_services}

---

## 🔧 修复操作

### 1. 端口冲突处理
"""

        if port_conflicts:
            for port, conflict in port_conflicts.items():
                report_content += f"- 端口 {port}: {conflict['process_name']} (PID: {conflict['pid']})\n"
        else:
            report_content += "- 无端口冲突\n"

        report_content += f"""
### 2. 服务启动状态
"""

        for service_name, service_info in self.results['services_status'].items():
            status_icon = '✅' if service_info['status'] == 'started' else '❌'
            report_content += (
                f"- {status_icon} {service_name}: {service_info['status']}\n"
            )

        report_content += f"""
### 3. API端点测试
"""

        for service_name, test_info in self.results['end_to_end_tests'].items():
            if service_name != 'unified_kg_functionality':
                success_rate = test_info.get('success_rate', 0)
                report_content += f"- {service_name}: {success_rate:.1f}% 成功率\n"

        report_content += f"""
### 4. 功能测试结果
"""

        if 'graph_stats' in functionality_tests:
            report_content += (
                f"- 图统计信息: {functionality_tests['graph_stats']['status']}\n"
            )
        if 'entity_search' in functionality_tests:
            report_content += (
                f"- 实体搜索: {functionality_tests['entity_search']['status']}\n"
            )
        if 'intelligent_search' in functionality_tests:
            report_content += (
                f"- 智能搜索: {functionality_tests['intelligent_search']['status']}\n"
            )

        report_content += f"""

---

## 💡 后续建议

1. **监控服务状态**: 定期检查API服务健康状态
2. **自动重启机制**: 建立服务异常时的自动重启机制
3. **负载均衡**: 考虑使用负载均衡器分发请求
4. **错误日志**: 建立统一的错误日志收集和分析
5. **性能监控**: 监控API响应时间和资源使用情况

---

## 📋 API服务列表

| 服务名称 | 端口 | 状态 | 健康检查端点 |
|---------|------|------|-------------|
"""

        for service_name, service_info in self.api_processes.items():
            status = (
                self.results['services_status']
                .get(service_name, {})
                .get('status', 'unknown')
            )
            health_endpoint = f"http://localhost:{service_info['port']}/api/v1/health"
            report_content += f"| {service_name} | {service_info['port']} | {status} | {health_endpoint} |\n"

        report_content += f"""

---

**修复完成时间**: {datetime.now().isoformat()}
**整体评估**: {overall_status}
"""

        # 保存报告
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = self.project_root / 'reports' / f"api_fix_report_{timestamp}.md"
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)

        # 保存详细JSON结果
        json_path = self.project_root / 'reports' / f"api_fix_data_{timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ 修复报告已保存: {report_path}")
        return report_path

    def run_api_fix(self):
        """运行完整API修复流程"""
        logger.info('🛠️ 开始法律知识图谱API服务修复')
        logger.info(str('=' * 60))

        try:
            # 1. 检查端口冲突
            port_conflicts = self.check_port_conflicts()

            # 2. 解决端口冲突
            killed_processes = 0
            if port_conflicts:
                killed_processes = self.kill_existing_processes(port_conflicts)

            # 3. 启动API服务
            started_services = self.start_api_services()

            if not started_services:
                logger.info('❌ 没有成功启动任何API服务')
                return False

            # 4. 等待服务完全启动
            logger.info('⏳ 等待服务完全启动...')
            time.sleep(5)

            # 5. 测试API端点
            test_results = self.test_api_endpoints(started_services)

            # 6. 测试统一知识图谱功能
            functionality_tests = self.test_unified_kg_functionality()

            # 7. 生成修复报告
            report_path = self.generate_fix_report(
                port_conflicts,
                killed_processes,
                started_services,
                test_results,
                functionality_tests,
            )

            logger.info(str('=' * 60))
            logger.info('🎉 API服务修复完成!')
            logger.info(f"📊 整体状态: {self.results['overall_status']}")
            logger.info(f"🚀 启动服务: {len(started_services)}/{len(self.api_processes)}")
            logger.info(f"📄 详细报告: {report_path}")

            # 显示访问信息
            logger.info("\n🌐 API服务访问信息:")
            for service in started_services:
                service_name = service['name']
                port = service['port']
                logger.info(f"  - {service_name}: http://localhost:{port}")

            return True

        except Exception as e:
            logger.info(f"❌ API修复过程异常: {str(e)}")
            return False


def main():
    """主函数"""
    logger.info('🛠️ 法律知识图谱API服务修复工具')
    logger.info('修复API服务连接问题，重启服务，验证端到端功能')
    logger.info(str('=' * 60))

    # 创建修复器
    fixer = LegalKGAPIFixer()

    # 运行修复
    success = fixer.run_api_fix()

    if success:
        status = fixer.results['overall_status']
        if '✅' in status:
            logger.info(f"\n🟢 API修复成功！{status}")
        elif '⚠️' in status:
            logger.info(f"\n🟡 API修复部分成功！{status}")
        else:
            logger.info(f"\n🔴 API修复需要进一步检查！{status}")
        logger.info('💡 建议查看详细报告了解具体状态')
    else:
        logger.info("\n❌ API修复失败")


if __name__ == '__main__':
    main()
