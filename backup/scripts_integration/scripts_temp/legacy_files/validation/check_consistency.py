#!/usr/bin/env python3
"""
Athena工作平台配置一致性验证脚本
检查系统配置的一致性和完整性

最后更新: 2025-12-13
"""

import os
import sys
import json
import yaml
import toml
import socket
import sqlite3
import subprocess
import requests
from pathlib import Path
from typing import Dict, List, Tuple, Any
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

class ConsistencyChecker:
    """配置一致性检查器"""

    def __init__(self):
        self.project_root = project_root
        self.results = {
            'total_checks': 0,
            'passed_checks': 0,
            'failed_checks': [],
            'warnings': [],
            'score': 0,
            'details': {}
        }
        self.config_dir = self.project_root / 'config'
        self.docs_dir = self.project_root / 'docs'

    def log(self, message: str, level: str = 'INFO'):
        """记录日志"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {level}: {message}")

    def check_port_configuration(self) -> bool:
        """检查端口配置一致性"""
        self.log('检查端口配置一致性...')

        try:
            # 检查ports.yaml文件存在
            ports_file = self.config_dir / 'ports.yaml'
            if not ports_file.exists():
                self.results['failed_checks'].append('ports.yaml文件不存在')
                return False

            with open(ports_file, 'r', encoding='utf-8') as f:
                ports_config = yaml.safe_load(f)

            services = ports_config.get('services', {})

            # 检查必需的服务端口
            required_ports = {
                'api_gateway': 8080,
                'unified_identity': 8010,
                'yunpat_agent': 8020,
                'browser_automation': 8030,
                'autonomous_control': 8040
            }

            all_passed = True

            for service, expected_port in required_ports.items():
                if service not in services:
                    self.results['failed_checks'].append(f'缺少服务端口配置: {service}')
                    all_passed = False
                elif services[service] != expected_port:
                    self.results['failed_checks'].append(
                        f'{service}端口不一致: 期望{expected_port}, 实际{services[service]}'
                    )
                    all_passed = False

            # 检查端口冲突
            port_values = list(services.values())
            if len(port_values) != len(set(port_values)):
                self.results['warnings'].append('检测到端口冲突')
                all_passed = False

            self.results['details']['ports'] = {
                'configured_services': len(services),
                'expected_services': len(required_ports),
                'port_conflicts': len(port_values) != len(set(port_values))
            }

            return all_passed

        except Exception as e:
            self.results['failed_checks'].append(f'端口配置检查失败: {str(e)}')
            return False

    def check_environment_variables(self) -> bool:
        """检查环境变量配置"""
        self.log('检查环境变量配置...')

        try:
            env_template = self.project_root / '.env.template'
            if not env_template.exists():
                self.results['failed_checks'].append('.env.template文件不存在')
                return False

            # 读取环境变量模板
            env_vars = {}
            with open(env_template, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key] = value

            # 检查必需的环境变量
            required_vars = [
                'ENVIRONMENT',
                'HOST',
                'PORT',
                'POSTGRES_HOST',
                'POSTGRES_PORT',
                'POSTGRES_DB',
                'REDIS_HOST',
                'REDIS_PORT',
                'JWT_SECRET'
            ]

            all_passed = True
            missing_vars = []

            for var in required_vars:
                if var not in env_vars:
                    missing_vars.append(var)
                    all_passed = False

            if missing_vars:
                self.results['failed_checks'].append(
                    f'缺少必需的环境变量: {", ".join(missing_vars)}'
                )

            # 检查默认值
            expected_values = {
                'ENVIRONMENT': 'development',
                'HOST': '0.0.0.0',
                'PORT': '8080',
                'POSTGRES_HOST': 'localhost',
                'POSTGRES_PORT': '5432',
                'REDIS_HOST': 'localhost',
                'REDIS_PORT': '6379'
            }

            for var, expected in expected_values.items():
                if var in env_vars and env_vars[var] != expected:
                    self.results['warnings'].append(
                        f'{var}默认值可能不正确: 期望{expected}, 实际{env_vars[var]}'
                    )

            self.results['details']['environment'] = {
                'total_variables': len(env_vars),
                'required_variables': len(required_vars),
                'missing_variables': len(missing_vars)
            }

            return all_passed

        except Exception as e:
            self.results['failed_checks'].append(f'环境变量检查失败: {str(e)}')
            return False

    def check_project_configuration(self) -> bool:
        """检查项目配置文件"""
        self.log('检查项目配置文件...')

        try:
            # 检查pyproject.toml
            pyproject_file = self.project_root / 'pyproject.toml'
            if not pyproject_file.exists():
                self.results['failed_checks'].append('pyproject.toml文件不存在')
                return False

            with open(pyproject_file, 'r', encoding='utf-8') as f:
                pyproject_config = toml.load(f)

            # 检查必需的配置节
            required_sections = [
                'build-system',
                'project',
                'tool.black',
                'tool.isort',
                'tool.flake8',
                'tool.mypy'
            ]

            all_passed = True
            missing_sections = []

            for section in required_sections:
                # 分割嵌套的键名
                keys = section.split('.')
                current = pyproject_config

                for key in keys:
                    if key not in current:
                        missing_sections.append(section)
                        all_passed = False
                        break
                    current = current[key]

            if missing_sections:
                self.results['failed_checks'].append(
                    f'pyproject.toml缺少配置节: {", ".join(missing_sections)}'
                )

            # 检查pre-commit配置
            precommit_file = self.project_root / '.pre-commit-config.yaml'
            if not precommit_file.exists():
                self.results['warnings'].append('pre-commit配置文件不存在')
            else:
                with open(precommit_file, 'r', encoding='utf-8') as f:
                    precommit_config = yaml.safe_load(f)

                repos = precommit_config.get('repos', [])
                required_hooks = ['black', 'isort', 'flake8', 'mypy', 'bandit']

                found_hooks = []
                for repo in repos:
                    if 'repo' in repo and 'hooks' in repo:
                        for hook in repo['hooks']:
                            hook_id = hook.get('id', '')
                            if hook_id in required_hooks:
                                found_hooks.append(hook_id)

                missing_hooks = set(required_hooks) - set(found_hooks)
                if missing_hooks:
                    self.results['warnings'].append(
                        f'pre-commit缺少hooks: {", ".join(missing_hooks)}'
                    )

            self.results['details']['project_config'] = {
                'pyproject_exists': True,
                'precommit_exists': precommit_file.exists(),
                'configured_hooks': len(found_hooks),
                'expected_hooks': len(required_hooks)
            }

            return all_passed

        except Exception as e:
            self.results['failed_checks'].append(f'项目配置检查失败: {str(e)}')
            return False

    def check_monitoring_configuration(self) -> bool:
        """检查监控配置"""
        self.log('检查监控配置...')

        try:
            monitoring_dir = self.project_root / 'monitoring'

            # 检查Grafana配置
            grafana_dir = monitoring_dir / 'grafana'
            dashboard_dir = grafana_dir / 'dashboards'

            checks = {
                'prometheus_config': (monitoring_dir / 'prometheus' / 'prometheus.yml'),
                'grafana_config': (grafana_dir / 'grafana.ini'),
                'dashboard_config': (dashboard_dir / 'athena-system-overview.json')
            }

            all_passed = True
            missing_configs = []

            for name, path in checks.items():
                if not path.exists():
                    missing_configs.append(f'{name}: {path}')
                    all_passed = False

            if missing_configs:
                self.results['warnings'].append(
                    f'监控配置缺失: {", ".join(missing_configs)}'
                )

            # 检查仪表盘配置
            dashboard_file = checks['dashboard_config']
            if dashboard_file.exists():
                with open(dashboard_file, 'r', encoding='utf-8') as f:
                    dashboard = json.load(f)

                # 验证服务名称
                panels = dashboard.get('panels', [])
                service_names = set()

                for panel in panels:
                    targets = panel.get('targets', [])
                    for target in targets:
                        expr = target.get('expr', '')
                        if 'job=' in expr:
                            # 提取服务名称
                            import re
                            matches = re.findall(r'job=~"([^"]+)"', expr)
                            service_names.update(matches)

                expected_services = {'api-gateway', 'unified-identity', 'yunpat-agent'}
                missing_services = expected_services - service_names

                if missing_services:
                    self.results['warnings'].append(
                        f'仪表盘缺少服务监控: {", ".join(missing_services)}'
                    )

            self.results['details']['monitoring'] = {
                'config_files_exist': len([c for c in checks.values() if c.exists()]),
                'total_config_files': len(checks),
                'dashboard_panels': len(panels) if 'panels' in locals() else 0
            }

            return all_passed

        except Exception as e:
            self.results['failed_checks'].append(f'监控配置检查失败: {str(e)}')
            return False

    def check_documentation_consistency(self) -> bool:
        """检查文档一致性"""
        self.log('检查文档一致性...')

        try:
            # 检查必需的文档文件
            required_docs = [
                'README.md',
                'docs/project-structure.md',
                'docs/license-header.txt'
            ]

            all_passed = True
            missing_docs = []

            for doc in required_docs:
                doc_path = self.project_root / doc
                if not doc_path.exists():
                    missing_docs.append(doc)
                    all_passed = False

            if missing_docs:
                self.results['warnings'].append(
                    f'缺少文档文件: {", ".join(missing_docs)}'
                )

            # 检查文档内容一致性
            structure_doc = self.project_root / 'docs/project-structure.md'
            if structure_doc.exists():
                with open(structure_doc, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 检查是否包含关键信息
                required_sections = [
                    '项目架构',
                    '服务端口',
                    '开发环境',
                    '部署架构'
                ]

                missing_sections = []
                for section in required_sections:
                    if section not in content:
                        missing_sections.append(section)

                if missing_sections:
                    self.results['warnings'].append(
                        f'项目结构文档缺少章节: {", ".join(missing_sections)}'
                    )

            self.results['details']['documentation'] = {
                'required_docs_exist': len(required_docs) - len(missing_docs),
                'total_required_docs': len(required_docs),
                'missing_docs': len(missing_docs)
            }

            return all_passed

        except Exception as e:
            self.results['failed_checks'].append(f'文档检查失败: {str(e)}')
            return False

    def check_service_connectivity(self) -> bool:
        """检查服务连通性"""
        self.log('检查服务连通性...')

        try:
            # 读取端口配置
            ports_file = self.config_dir / 'ports.yaml'
            if not ports_file.exists():
                return True  # 跳过连通性检查如果配置不存在

            with open(ports_file, 'r', encoding='utf-8') as f:
                ports_config = yaml.safe_load(f)

            services = ports_config.get('services', {})

            # 检查关键服务是否运行
            critical_services = ['api_gateway']
            failed_services = []

            for service in critical_services:
                if service in services:
                    port = services[service]
                    try:
                        # 简单的TCP连接测试
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(3)
                        result = sock.connect_ex(('localhost', port))
                        sock.close()

                        if result != 0:
                            failed_services.append(f'{service} (端口 {port})')
                    except:
                        failed_services.append(f'{service} (端口 {port} - 连接超时)')

            if failed_services:
                self.results['warnings'].append(
                    f'服务连接失败: {", ".join(failed_services)}'
                )

            self.results['details']['connectivity'] = {
                'critical_services': len(critical_services),
                'failed_services': len(failed_services),
                'success_rate': (len(critical_services) - len(failed_services)) / len(critical_services) * 100
            }

            return len(failed_services) == 0

        except Exception as e:
            self.results['warnings'].append(f'服务连通性检查失败: {str(e)}')
            return True  # 不将连通性问题作为严重错误

    def run_all_checks(self) -> Dict[str, Any]:
        """运行所有检查"""
        self.log('开始运行配置一致性检查...')

        # 执行所有检查
        checks = [
            ('端口配置', self.check_port_configuration),
            ('环境变量', self.check_environment_variables),
            ('项目配置', self.check_project_configuration),
            ('监控配置', self.check_monitoring_configuration),
            ('文档一致性', self.check_documentation_consistency),
            ('服务连通性', self.check_service_connectivity)
        ]

        for check_name, check_func in checks:
            self.results['total_checks'] += 1
            try:
                if check_func():
                    self.results['passed_checks'] += 1
                    self.log(f'✓ {check_name}检查通过')
                else:
                    self.log(f'✗ {check_name}检查失败', 'ERROR')
            except Exception as e:
                self.log(f'✗ {check_name}检查异常: {str(e)}', 'ERROR')
                self.results['failed_checks'].append(f'{check_name}检查异常: {str(e)}')

        # 计算得分
        if self.results['total_checks'] > 0:
            self.results['score'] = int(
                (self.results['passed_checks'] / self.results['total_checks']) * 100
            )

        return self.results

    def generate_report(self) -> str:
        """生成检查报告"""
        report = []
        report.append('\n' + '='*60)
        report.append('Athena工作平台配置一致性检查报告')
        report.append('='*60)
        report.append(f'检查时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        report.append(f'一致性得分: {self.results["score"]}/100')
        report.append(f'通过检查: {self.results["passed_checks"]}/{self.results["total_checks"]}')

        # 通过/失败统计
        if self.results['passed_checks'] == self.results['total_checks']:
            report.append('\n🎉 所有配置检查均通过！')
        else:
            report.append('\n⚠️ 发现以下问题:')
            for i, issue in enumerate(self.results['failed_checks'], 1):
                report.append(f'  {i}. {issue}')

        # 警告信息
        if self.results['warnings']:
            report.append('\n⚠️ 警告信息:')
            for i, warning in enumerate(self.results['warnings'], 1):
                report.append(f'  {i}. {warning}')

        # 详细信息
        report.append('\n📊 详细统计:')
        for category, stats in self.results['details'].items():
            report.append(f'  {category}:')
            for key, value in stats.items():
                report.append(f'    - {key}: {value}')

        # 建议
        report.append('\n💡 改进建议:')
        if self.results['score'] < 80:
            report.append('  - 建议立即修复配置问题以确保系统稳定运行')
        elif self.results['score'] < 90:
            report.append('  - 建议处理警告信息以提高系统可靠性')
        else:
            report.append('  - 系统配置良好，建议定期执行一致性检查')

        report.append('='*60)

        return '\n'.join(report)

def main():
    """主函数"""
    checker = ConsistencyChecker()

    # 运行所有检查
    results = checker.run_all_checks()

    # 生成报告
    report = checker.generate_report()
    print(report)

    # 保存报告到文件
    report_file = project_root / 'consistency_report.txt'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f'\n详细报告已保存到: {report_file}')

    # 返回适当的退出码
    if results['score'] >= 90:
        print('\n✅ 配置一致性检查通过')
        sys.exit(0)
    elif results['score'] >= 70:
        print('\n⚠️ 配置基本一致，但有改进空间')
        sys.exit(1)
    else:
        print('\n❌ 配置存在严重问题，需要立即修复')
        sys.exit(2)

if __name__ == '__main__':
    main()