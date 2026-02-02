#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Athena工作平台一致性检查器
Platform Consistency Checker

全面检查平台各个组件的一致性问题
"""

import hashlib
import json
import logging
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import psycopg2

logger = logging.getLogger(__name__)

class AthenaConsistencyChecker:
    """Athena一致性检查器"""

    def __init__(self):
        self.base_dir = Path('/Users/xujian/Athena工作平台')
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'checks': {},
            'summary': {
                'total_checks': 0,
                'passed_checks': 0,
                'failed_checks': 0,
                'warnings': 0
            },
            'issues': [],
            'recommendations': []
        }

        # 数据库配置
        self.db_configs = [
            {
                'name': 'patents_original',
                'host': 'localhost',
                'port': 5432,
                'user': 'postgres',
                'password': 'postgres',
                'database': 'patents_original'
            },
            {
                'name': 'patent_db',
                'host': 'localhost',
                'port': 5432,
                'user': 'postgres',
                'password': 'postgres',
                'database': 'patent_db'
            },
            {
                'name': 'yunpat',
                'host': 'localhost',
                'port': 7687,
                'user': 'neo4j',
                'password': 'password',
                'database': 'neo4j'
            }
        ]

        # 核心服务列表
        self.core_services = [
            {'name': 'patent_search', 'port': 8080, 'type': 'web'},
            {'name': 'patent_analysis', 'port': 8081, 'type': 'web'},
            {'name': 'vector_service', 'port': 8082, 'type': 'web'},
            {'name': 'ollama', 'port': 11434, 'type': 'api'},
            {'name': 'redis', 'port': 6379, 'type': 'service'},
            {'name': 'postgresql', 'port': 5432, 'type': 'service'},
            {'name': 'neo4j', 'port': 7474, 'type': 'web'},
            {'name': 'neo4j_bolt', 'port': 7687, 'type': 'service'}
        ]

        # 关键配置文件
        self.config_files = [
            'config/database.yaml',
            'config/redis.yaml',
            'config/elasticsearch.yaml',
            'config/ollama.yaml',
            'config/services.yaml',
            'docker/docker-compose.yml',
            'scripts/start_athena_platform.sh',
            '.claude/context-config.json'
        ]

        # 关键目录结构
        self.key_directories = [
            'scripts',
            'config',
            'docs',
            'services',
            'database',
            'docker',
            'monitoring',
            'deployment',
            'utils',
            'core',
            'apps'
        ]

        # Python依赖检查
        self.python_requirements = [
            'requirements.txt',
            'requirements/requirements.txt',
            'services/requirements.txt',
            'services/ai-models/requirements.txt',
            'services/patent-search/requirements.txt'
        ]

    def run_all_checks(self) -> Dict:
        """运行所有一致性检查"""
        logger.info('🔍 开始Athena工作平台全面一致性检查...')

        # 1. 目录结构一致性检查
        self.check_directory_structure()

        # 2. 数据库连接检查
        self.check_database_connectivity()

        # 3. 服务状态检查
        self.check_service_status()

        # 4. 配置文件一致性检查
        self.check_configuration_consistency()

        # 5. 路径引用完整性检查
        self.check_path_references()

        # 6. 依赖关系检查
        self.check_dependencies()

        # 7. 数据完整性检查
        self.check_data_integrity()

        # 8. 权限和安全检查
        self.check_permissions_and_security()

        # 9. 性能一致性检查
        self.check_performance_consistency()

        # 10. 文档一致性检查
        self.check_documentation_consistency()

        # 生成报告
        self.generate_report()

        return self.results

    def check_directory_structure(self):
        """检查目录结构一致性"""
        logger.info("\n📁 检查目录结构一致性...")

        check_result = {
            'status': 'passed',
            'issues': [],
            'missing_dirs': [],
            'unexpected_dirs': [],
            'empty_dirs': []
        }

        # 检查关键目录是否存在
        for dir_path in self.key_directories:
            full_path = self.base_dir / dir_path
            if not full_path.exists():
                check_result['missing_dirs'].append(dir_path)
                check_result['status'] = 'failed'

        # 检查空目录
        for root, dirs, files in os.walk(self.base_dir):
            if len(files) == 0 and len(dirs) == 0:
                rel_path = str(Path(root).relative_to(self.base_dir))
                if not rel_path.startswith('.'):
                    check_result['empty_dirs'].append(rel_path)

        # 检查是否有异常的顶级目录
        expected_top_dirs = set(self.key_directories + ['论文', '工作', 'logs', 'README.md'])
        actual_top_dirs = [d.name for d in self.base_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
        unexpected = set(actual_top_dirs) - expected_top_dirs

        if unexpected:
            check_result['unexpected_dirs'] = list(unexpected)
            check_result['issues'].append(f"发现未预期的顶级目录: {unexpected}")

        self.results['checks']['directory_structure'] = check_result

    def check_database_connectivity(self):
        """检查数据库连接"""
        logger.info("\n🗄️ 检查数据库连接...")

        check_result = {
            'status': 'passed',
            'databases': {},
            'issues': []
        }

        for db_config in self.db_configs:
            db_name = db_config['name']
            db_result = {'status': 'unknown', 'error': None}

            try:
                if db_name == 'yunpat':
                    # Neo4j检查
                    from neo4j import GraphDatabase
                    driver = GraphDatabase.driver(
                        f"bolt://{db_config['host']}:{db_config['port']}",
                        auth=(db_config['user'], db_config['password'])
                    )
                    with driver.session() as session:
                        result = session.run('RETURN 1')
                        db_result['status'] = 'connected'
                        db_result['version'] = 'Neo4j'
                    driver.close()
                else:
                    # PostgreSQL检查
                    conn = psycopg2.connect(
                        host=db_config['host'],
                        port=db_config['port'],
                        user=db_config['user'],
                        password=db_config['password'],
                        database=db_config['database']
                    )
                    cursor = conn.cursor()
                    cursor.execute('SELECT version()')
                    version = cursor.fetchone()[0]
                    db_result['status'] = 'connected'
                    db_result['version'] = version
                    conn.close()

            except Exception as e:
                db_result['status'] = 'failed'
                db_result['error'] = str(e)
                check_result['status'] = 'failed'
                check_result['issues'].append(f"数据库 {db_name} 连接失败: {e}")

            check_result['databases'][db_name] = db_result

        self.results['checks']['database_connectivity'] = check_result

    def check_service_status(self):
        """检查服务状态"""
        logger.info("\n🚀 检查服务状态...")

        check_result = {
            'status': 'passed',
            'services': {},
            'issues': [],
            'running_services': 0,
            'stopped_services': 0
        }

        for service in self.core_services:
            service_name = service['name']
            port = service['port']
            service_type = service['type']

            service_result = {
                'status': 'unknown',
                'port': port,
                'type': service_type,
                'response_time': None
            }

            try:
                if service_type == 'service':
                    # 检查系统服务
                    result = subprocess.run(
                        ['lsof', '-i', f":{port}"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        service_result['status'] = 'running'
                        check_result['running_services'] += 1
                    else:
                        service_result['status'] = 'stopped'
                        check_result['stopped_services'] += 1
                        check_result['status'] = 'failed'
                else:
                    # 检查Web/API服务
                    import socket
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(3)
                    start_time = datetime.now()
                    result = sock.connect_ex(('localhost', port))
                    end_time = datetime.now()
                    sock.close()

                    if result == 0:
                        service_result['status'] = 'running'
                        service_result['response_time'] = (end_time - start_time).total_seconds()
                        check_result['running_services'] += 1
                    else:
                        service_result['status'] = 'stopped'
                        check_result['stopped_services'] += 1
                        check_result['status'] = 'failed'

            except Exception as e:
                service_result['status'] = 'error'
                service_result['error'] = str(e)
                check_result['issues'].append(f"服务 {service_name} 检查失败: {e}")

            check_result['services'][service_name] = service_result

        self.results['checks']['service_status'] = check_result

    def check_configuration_consistency(self):
        """检查配置文件一致性"""
        logger.info("\n⚙️ 检查配置文件一致性...")

        check_result = {
            'status': 'passed',
            'configs': {},
            'issues': [],
            'missing_configs': []
        }

        for config_file in self.config_files:
            config_path = self.base_dir / config_file
            config_result = {
                'exists': False,
                'valid': False,
                'errors': []
            }

            if not config_path.exists():
                check_result['missing_configs'].append(config_file)
                check_result['status'] = 'failed'
                continue

            config_result['exists'] = True

            try:
                if config_file.endswith('.yaml') or config_file.endswith('.yml'):
                    import yaml
                    with open(config_path, 'r', encoding='utf-8') as f:
                        yaml.safe_load(f)
                    config_result['valid'] = True
                elif config_file.endswith('.json'):
                    with open(config_path, 'r', encoding='utf-8') as f:
                        json.load(f)
                    config_result['valid'] = True
                else:
                    # 检查脚本文件语法
                    if config_file.endswith('.sh'):
                        result = subprocess.run(
                            ['bash', '-n', str(config_path)],
                            capture_output=True
                        )
                        if result.returncode == 0:
                            config_result['valid'] = True
                        else:
                            config_result['errors'].append(result.stderr.decode())
                    else:
                        config_result['valid'] = True

            except Exception as e:
                config_result['valid'] = False
                config_result['errors'].append(str(e))
                check_result['status'] = 'failed'
                check_result['issues'].append(f"配置文件 {config_file} 验证失败: {e}")

            check_result['configs'][config_file] = config_result

        self.results['checks']['configuration_consistency'] = check_result

    def check_path_references(self):
        """检查路径引用完整性"""
        logger.info("\n🔗 检查路径引用完整性...")

        check_result = {
            'status': 'passed',
            'broken_references': [],
            'total_checked': 0,
            'valid_references': 0
        }

        # 检查Python文件中的import路径
        python_files = list(self.base_dir.rglob('*.py'))

        for py_file in python_files:
            if '.git' in str(py_file) or '__pycache__' in str(py_file):
                continue

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 查找本地模块引用
                import_pattern = r"from\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)\s+import"
                matches = re.findall(import_pattern, content)

                for match in matches:
                    if not match.startswith('.'):  # 跳过相对导入
                        check_result['total_checked'] += 1

                        # 尝试解析路径
                        module_path = self.base_dir / match.replace('.', '/')

                        # 检查.py文件或包目录
                        py_file_path = Path(str(module_path) + '.py')
                        pkg_dir_path = module_path / '__init__.py'

                        if py_file_path.exists() or pkg_dir_path.exists():
                            check_result['valid_references'] += 1
                        else:
                            check_result['broken_references'].append({
                                'file': str(py_file.relative_to(self.base_dir)),
                                'reference': match,
                                'suggested_path': str(module_path)
                            })

            except Exception as e:
                continue

        if check_result['broken_references']:
            check_result['status'] = 'failed'

        self.results['checks']['path_references'] = check_result

    def check_dependencies(self):
        """检查依赖关系"""
        logger.info("\n📦 检查依赖关系...")

        check_result = {
            'status': 'passed',
            'python_packages': {},
            'system_packages': {},
            'missing_packages': [],
            'conflicts': []
        }

        # 检查Python依赖
        for req_file in self.python_requirements:
            req_path = self.base_dir / req_file
            if not req_path.exists():
                continue

            try:
                with open(req_path, 'r') as f:
                    requirements = f.read().strip().split('\n')

                for req in requirements:
                    if req.strip() and not req.startswith('#'):
                        package_name = req.split('==')[0].split('>=')[0].split('<=')[0].strip()

                        # 检查包是否已安装
                        try:
                            __import__(package_name.replace('-', '_'))
                            check_result['python_packages'][package_name] = 'installed'
                        except ImportError:
                            check_result['python_packages'][package_name] = 'missing'
                            check_result['missing_packages'].append(package_name)
                            check_result['status'] = 'failed'

            except Exception as e:
                check_result['conflicts'].append(f"读取 {req_file} 失败: {e}")

        # 检查系统依赖
        system_commands = [
            ('psql', 'PostgreSQL客户端'),
            ('redis-cli', 'Redis客户端'),
            ('docker', 'Docker'),
            ('git', 'Git'),
            ('python3', 'Python3')
        ]

        for cmd, desc in system_commands:
            try:
                result = subprocess.run(
                    ['which', cmd],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    check_result['system_packages'][cmd] = 'installed'
                else:
                    check_result['system_packages'][cmd] = 'missing'
                    check_result['missing_packages'].append(f"{cmd} ({desc})")
                    check_result['status'] = 'failed'

            except Exception:
                check_result['system_packages'][cmd] = 'error'

        self.results['checks']['dependencies'] = check_result

    def check_data_integrity(self):
        """检查数据完整性"""
        logger.info("\n🔒 检查数据完整性...")

        check_result = {
            'status': 'passed',
            'database_stats': {},
            'file_integrity': {},
            'issues': []
        }

        # 检查专利数据库统计
        try:
            conn = psycopg2.connect(
                host='localhost',
                port=5432,
                user='postgres',
                password='postgres',
                database='patent_db'
            )
            cursor = conn.cursor()

            # 检查表记录数
            tables = ['patents', 'patents_vector', 'companies', 'inventors']
            for table in tables:
                try:
        # TODO: 检查SQL注入风险 - cursor.execute(f"SELECT COUNT(*) FROM {table}")
                            cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    check_result['database_stats'][table] = count

                    # 检查数据完整性
                    if table == 'patents':
                        # 使用正确的字段名patent_name而不是title
        # TODO: 检查SQL注入风险 - cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE patent_name IS NULL OR abstract IS NULL")
                                cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE patent_name IS NULL OR abstract IS NULL")
                        null_count = cursor.fetchone()[0]
                        if null_count > 0:
                            check_result['issues'].append(f"表 {table} 有 {null_count} 条记录的patent_name或abstract为NULL")
                            check_result['status'] = 'failed'

                except Exception as e:
                    check_result['issues'].append(f"检查表 {table} 失败: {e}")

            conn.close()

        except Exception as e:
            check_result['issues'].append(f"数据库连接失败: {e}")
            check_result['status'] = 'failed'

        # 检查关键文件完整性
        key_files = [
            'README.md',
            'config/database.yaml',
            'scripts/start_athena_platform.sh',
            'docs/专利检索系统实施方案_v2.md'
        ]

        for file_path in key_files:
            full_path = self.base_dir / file_path
            if full_path.exists():
                # 计算文件哈希
                try:
                    with open(full_path, 'rb') as f:
                        file_hash = hashlib.md5(f.read(, usedforsecurity=False).hexdigest()
                    check_result['file_integrity'][file_path] = {
                        'exists': True,
                        'hash': file_hash,
                        'size': full_path.stat().st_size
                    }
                except Exception as e:
                    check_result['file_integrity'][file_path] = {
                        'exists': True,
                        'error': str(e)
                    }
            else:
                check_result['file_integrity'][file_path] = {'exists': False}
                check_result['issues'].append(f"关键文件缺失: {file_path}")
                check_result['status'] = 'failed'

        self.results['checks']['data_integrity'] = check_result

    def check_permissions_and_security(self):
        """检查权限和安全"""
        logger.info("\n🔐 检查权限和安全...")

        check_result = {
            'status': 'passed',
            'permission_issues': [],
            'security_issues': [],
            'executable_permissions': {}
        }

        # 检查关键脚本的执行权限
        critical_scripts = [
            'scripts/start_athena_platform.sh',
            'scripts/start_core_services.sh',
            'scripts/global_context_optimizer.py',
            'scripts/search/smart_patent_search.py'
        ]

        for script in critical_scripts:
            script_path = self.base_dir / script
            if script_path.exists():
                permissions = oct(script_path.stat().st_mode)[-3:]
                check_result['executable_permissions'][script] = permissions

                if script.endswith('.sh') and not permissions.endswith('5') and not permissions.endswith('7'):
                    check_result['permission_issues'].append(f"脚本 {script} 没有执行权限")
                    check_result['status'] = 'failed'

        # 检查敏感信息泄露
        sensitive_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']'
        ]

        config_files = list(self.base_dir.rglob('*.yaml')) + list(self.base_dir.rglob('*.yml')) + list(self.base_dir.rglob('*.json'))

        for config_file in config_files:
            if '.git' in str(config_file):
                continue

            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                for pattern in sensitive_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches and 'password' not in str(config_file).lower():
                        check_result['security_issues'].append(f"文件 {config_file} 可能包含敏感信息")
                        check_result['status'] = 'failed'
                        break

            except Exception:
                continue

        self.results['checks']['permissions_and_security'] = check_result

    def check_performance_consistency(self):
        """检查性能一致性"""
        logger.info("\n⚡ 检查性能一致性...")

        check_result = {
            'status': 'passed',
            'system_resources': {},
            'database_performance': {},
            'issues': []
        }

        # 检查系统资源使用
        try:
            # CPU使用率
            cpu_result = subprocess.run(
                ['ps', '-A', '-o', '%cpu'],
                capture_output=True,
                text=True
            )
            cpu_usage = sum(float(line.strip()) for line in cpu_result.stdout.strip().split('\n')[1:] if line.strip())
            check_result['system_resources']['cpu_usage'] = cpu_usage

            # 内存使用率
            mem_result = subprocess.run(
                ['vm_stat'],
                capture_output=True,
                text=True
            )

            # 磁盘空间
            disk_result = subprocess.run(
                ['df', '-h', str(self.base_dir)],
                capture_output=True,
                text=True
            )
            disk_lines = disk_result.stdout.strip().split('\n')
            if len(disk_lines) >= 2:
                disk_info = disk_lines[1].split()
                check_result['system_resources']['disk_usage'] = disk_info[4]

        except Exception as e:
            check_result['issues'].append(f"系统资源检查失败: {e}")

        # 检查数据库性能
        try:
            conn = psycopg2.connect(
                host='localhost',
                port=5432,
                user='postgres',
                password='postgres',
                database='patent_db'
            )
            cursor = conn.cursor()

            # 检查数据库大小
            cursor.execute("SELECT pg_size_pretty(pg_database_size('patent_db'))")
            db_size = cursor.fetchone()[0]
            check_result['database_performance']['database_size'] = db_size

            # 检查连接数
            cursor.execute('SELECT count(*) FROM pg_stat_activity')
            connections = cursor.fetchone()[0]
            check_result['database_performance']['active_connections'] = connections

            conn.close()

        except Exception as e:
            check_result['issues'].append(f"数据库性能检查失败: {e}")

        self.results['checks']['performance_consistency'] = check_result

    def check_documentation_consistency(self):
        """检查文档一致性"""
        logger.info("\n📚 检查文档一致性...")

        check_result = {
            'status': 'passed',
            'documentation_files': {},
            'outdated_docs': [],
            'missing_docs': []
        }

        # 检查关键文档
        key_docs = [
            ('README.md', '项目主文档'),
            ('docs/专利检索系统实施方案_v2.md', '专利检索系统方案'),
            ('documentation/claude_context_management_guide.md', '上下文管理指南'),
            ('architecture.md', '架构文档'),
            ('CHANGELOG.md', '更新日志')
        ]

        for doc_path, doc_desc in key_docs:
            full_path = self.base_dir / doc_path
            doc_info = {
                'description': doc_desc,
                'exists': False,
                'size': 0,
                'last_modified': None
            }

            if full_path.exists():
                doc_info['exists'] = True
                doc_info['size'] = full_path.stat().st_size
                doc_info['last_modified'] = datetime.fromtimestamp(full_path.stat().st_mtime).isoformat()

                # 检查文档是否过于陈旧（超过6个月）
                age_days = (datetime.now() - datetime.fromtimestamp(full_path.stat().st_mtime)).days
                if age_days > 180 and doc_path not in ['README.md']:
                    check_result['outdated_docs'].append(f"{doc_path} (超过{age_days}天未更新)")
            else:
                check_result['missing_docs'].append(f"{doc_path} ({doc_desc})")
                if doc_path in ['README.md', 'docs/专利检索系统实施方案_v2.md']:
                    check_result['status'] = 'failed'

            check_result['documentation_files'][doc_path] = doc_info

        self.results['checks']['documentation_consistency'] = check_result

    def generate_report(self):
        """生成一致性报告"""
        logger.info("\n📋 生成一致性报告...")

        # 统计检查结果
        total_checks = len(self.results['checks'])
        passed_checks = sum(1 for check in self.results['checks'].values() if check.get('status') == 'passed')
        failed_checks = total_checks - passed_checks

        self.results['summary'].update({
            'total_checks': total_checks,
            'passed_checks': passed_checks,
            'failed_checks': failed_checks
        })

        # 收集所有问题
        all_issues = []
        for check_name, check_result in self.results['checks'].items():
            if 'issues' in check_result:
                for issue in check_result['issues']:
                    all_issues.append(f"[{check_name}] {issue}")

        self.results['issues'] = all_issues

        # 生成建议
        recommendations = []

        if failed_checks > 0:
            recommendations.append(f"发现{failed_checks}项检查失败，建议优先解决关键问题")

        if not self.results['checks'].get('database_connectivity', {}).get('databases', {}).get('patent_db', {}).get('status') == 'connected':
            recommendations.append('数据库连接异常，将影响专利检索功能')

        if self.results['summary']['failed_checks'] > self.results['summary']['passed_checks']:
            recommendations.append('系统一致性较差，建议进行全面维护')

        if len(all_issues) == 0:
            recommendations.append('系统一致性良好，继续保持定期检查')

        self.results['recommendations'] = recommendations

        # 保存报告
        report_dir = self.base_dir / 'documentation' / 'consistency-reports'
        report_dir.mkdir(parents=True, exist_ok=True)

        report_file = report_dir / f"consistency_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ 一致性报告已保存: {report_file}")

def main():
    """主函数"""
    import argparse

# 导入标准化数据库工具
from shared.database.db_utils import DatabaseManager, build_safe_query

    parser = argparse.ArgumentParser(description='Athena工作平台一致性检查器')
    parser.add_argument('--output', '-o', help='输出报告文件路径')
    parser.add_argument('--quiet', '-q', action='store_true', help='静默模式')

    args = parser.parse_args()

    checker = AthenaConsistencyChecker()
    results = checker.run_all_checks()

    if not args.quiet:
        logger.info(str("\n" + '='*60))
        logger.info('🎯 Athena工作平台一致性检查报告')
        logger.info(str('='*60))
        logger.info(f"📊 检查统计:")
        logger.info(f"   总检查项: {results['summary']['total_checks']}")
        logger.info(f"   通过: {results['summary']['passed_checks']} ✅")
        logger.info(f"   失败: {results['summary']['failed_checks']} ❌")
        logger.info(f"   警告: {results['summary']['warnings']} ⚠️")

        if results['issues']:
            logger.info(f"\n❌ 发现的问题 ({len(results['issues'])}项):")
            for i, issue in enumerate(results['issues'][:10], 1):
                logger.info(f"   {i}. {issue}")
            if len(results['issues']) > 10:
                logger.info(f"   ... 还有{len(results['issues'])-10}个问题，详见报告文件")

        if results['recommendations']:
            logger.info(f"\n💡 建议 ({len(results['recommendations'])}项):")
            for i, rec in enumerate(results['recommendations'], 1):
                logger.info(f"   {i}. {rec}")

        logger.info(f"\n📁 详细报告: documentation/consistency-reports/")

    return results['summary']['failed_checks'] == 0

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)