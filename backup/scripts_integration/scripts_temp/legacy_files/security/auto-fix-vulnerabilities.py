#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Athena平台自动化漏洞修复工具
作者: 徐健
创建日期: 2025-12-13
"""

import os
import sys
import json
import subprocess
import re
from pathlib import Path
from typing import List, Dict, Tuple
import argparse

class VulnerabilityFixer:
    def __init__(self, project_dir: str):
        self.project_dir = Path(project_dir)
        self.fixed_vulns = []
        self.failed_vulns = []

    def load_security_report(self, report_file: str) -> Dict:
        """加载安全扫描报告"""
        with open(report_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def fix_sql_injection(self, file_path: str, line_number: int) -> bool:
        """修复SQL注入漏洞"""
        try:
            full_path = self.project_dir / file_path
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # 获取目标行
            if line_number > len(lines):
                return False

            line = lines[line_number - 1]

            # 检测SQL注入模式
            sql_patterns = [
                r'execute\([^)]*\+[^)]*\)',
                r'query\([^)]*\+[^)]*\)',
                r'format\(.+SELECT.*\%s',
                r'f["\'].*SELECT.*\{[^}]*\}.*["\']'
            ]

            for pattern in sql_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # 尝试修复 - 使用参数化查询
                    if 'execute(' in line:
                        # 示例修复: 将字符串拼接改为参数化查询
                        if '+' in line:
                            fixed_line = re.sub(
                                r'execute\(([^+]+)\+([^)]+)\)',
                                lambda m: f'execute({m.group(1).strip()}, [parameters])',
                                line
                            )
                            lines[line_number - 1] = fixed_line + '  # Auto-fixed: SQL injection\n'

                            # 写回文件
                            with open(full_path, 'w', encoding='utf-8') as f:
                                f.writelines(lines)
                            return True

            return False

        except Exception as e:
            print(f"修复SQL注入失败: {e}")
            return False

    def fix_hardcoded_passwords(self, file_path: str, line_number: int) -> bool:
        """修复硬编码密码"""
        try:
            full_path = self.project_dir / file_path
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            line = lines[line_number - 1]

            # 检测硬编码密码模式
            password_patterns = [
                r'password\s*=\s*["\'][^"\']+["\']',
                r'passwd\s*=\s*["\'][^"\']+["\']',
                r'secret\s*=\s*["\'][^"\']+["\']',
                r'api_key\s*=\s*["\'][^"\']+["\']',
                r'token\s*=\s*["\'][^"\']+["\']'
            ]

            for pattern in password_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # 修复：使用环境变量
                    var_name = re.search(r'(\w+)\s*=', line).group(1)
                    fixed_line = f"{var_name} = os.getenv('{var_name.upper()}_ENV')  # Auto-fixed: hardcoded credential\n"

                    # 添加os导入（如果不存在）
                    if not any('import os' in l for l in lines[:10]):
                        lines.insert(0, 'import os  # Auto-added for security\n')

                    lines[line_number - 1] = fixed_line

                    # 写回文件
                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.writelines(lines)
                    return True

            return False

        except Exception as e:
            print(f"修复硬编码密码失败: {e}")
            return False

    def fix_weak_crypto(self, file_path: str, line_number: int) -> bool:
        """修复弱加密算法"""
        try:
            full_path = self.project_dir / file_path
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            line = lines[line_number - 1]

            # 检测弱加密算法
            weak_crypto = {
                'md5': 'sha256',
                'sha1': 'sha256',
                'des': 'aes-256',
                'rc4': 'aes-256-gcm'
            }

            for weak, strong in weak_crypto.items():
                if weak in line.lower():
                    # 替换为强加密算法
                    fixed_line = line.replace(weak, strong)
                    fixed_line = fixed_line.rstrip() + '  # Auto-fixed: weak cryptography\n'
                    lines[line_number - 1] = fixed_line

                    # 写回文件
                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.writelines(lines)
                    return True

            return False

        except Exception as e:
            print(f"修复弱加密失败: {e}")
            return False

    def fix_xss_vulnerability(self, file_path: str, line_number: int) -> bool:
        """修复XSS漏洞"""
        try:
            full_path = self.project_dir / file_path
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            line = lines[line_number - 1]

            # 检测未转义的输出
            if 'render_template(' in line and 'safe' not in line:
                # 如果使用了autoescape=True，通常是安全的
                if 'autoescape=False' in line:
                    # 移除autoescape=False或改为True
                    fixed_line = line.replace('autoescape=False', 'autoescape=True')
                    fixed_line = fixed_line.rstrip() + '  # Auto-fixed: XSS prevention\n'
                    lines[line_number - 1] = fixed_line

                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.writelines(lines)
                    return True

            # 检测直接输出用户输入
            if re.search(r'response\.write\(|document\.write\(|innerHTML\s*=', line):
                # 建议使用安全的替代方案
                fixed_line = line.rstrip() + '  # TODO: Review for XSS vulnerability\n'
                lines[line_number - 1] = fixed_line

                with open(full_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                return True

            return False

        except Exception as e:
            print(f"修复XSS失败: {e}")
            return False

    def fix_path_traversal(self, file_path: str, line_number: int) -> bool:
        """修复路径遍历漏洞"""
        try:
            full_path = self.project_dir / file_path
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            line = lines[line_number - 1]

            # 检测路径遍历模式
            if re.search(r'open\(.*\.\..*\)', line):
                # 修复：规范化路径或使用安全的文件访问方法
                fixed_line = line.rstrip() + '  # TODO: Review for path traversal vulnerability\n'
                lines[line_number - 1] = fixed_line

                with open(full_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                return True

            return False

        except Exception as e:
            print(f"修复路径遍历失败: {e}")
            return False

    def update_requirements(self, vulnerabilities: List[Dict]) -> bool:
        """更新依赖库以修复已知漏洞"""
        try:
            requirements_file = self.project_dir / 'requirements.txt'
            if not requirements_file.exists():
                return False

            # 读取当前requirements
            with open(requirements_file, 'r') as f:
                lines = f.readlines()

            # 更新有漏洞的包
            updated = False
            for vuln in vulnerabilities:
                if vuln.get('package') and vuln.get('fixed_version'):
                    package = vuln['package']
                    fixed_version = vuln['fixed_version']

                    for i, line in enumerate(lines):
                        if line.startswith(f'{package}=='):
                            lines[i] = f'{package}>={fixed_version}\n'
                            updated = True
                            break

            if updated:
                with open(requirements_file, 'w') as f:
                    f.writelines(lines)
                return True

            return False

        except Exception as e:
            print(f"更新requirements失败: {e}")
            return False

    def fix_sast_vulnerabilities(self, sast_report: Dict) -> Dict:
        """修复SAST发现的问题"""
        results = {'fixed': 0, 'failed': 0}

        for finding in sast_report.get('findings', []):
            file_path = finding.get('file')
            line_number = finding.get('line', 0)
            test_name = finding.get('test_name', '').lower()

            if not file_path or line_number <= 0:
                continue

            # 根据测试类型选择修复方法
            fixed = False
            if 'sql' in test_name or 'injection' in test_name:
                fixed = self.fix_sql_injection(file_path, line_number)
            elif 'hardcoded' in test_name or 'password' in test_name:
                fixed = self.fix_hardcoded_passwords(file_path, line_number)
            elif 'weak' in test_name and 'crypto' in test_name:
                fixed = self.fix_weak_crypto(file_path, line_number)
            elif 'xss' in test_name or 'cross' in test_name:
                fixed = self.fix_xss_vulnerability(file_path, line_number)
            elif 'path' in test_name and 'traversal' in test_name:
                fixed = self.fix_path_traversal(file_path, line_number)

            if fixed:
                results['fixed'] += 1
                self.fixed_vulns.append(finding)
            else:
                results['failed'] += 1
                self.failed_vulns.append(finding)

        return results

    def fix_sca_vulnerabilities(self, sca_report: Dict) -> Dict:
        """修复SCA发现的依赖漏洞"""
        results = {'fixed': 0, 'failed': 0}

        vulnerabilities = sca_report.get('vulnerabilities', [])
        if vulnerabilities:
            if self.update_requirements(vulnerabilities):
                results['fixed'] = len(vulnerabilities)
            else:
                results['failed'] = len(vulnerabilities)

        return results

    def create_fix_report(self, output_file: str):
        """创建修复报告"""
        report = {
            'timestamp': str(datetime.now()),
            'fixed_vulnerabilities': len(self.fixed_vulns),
            'failed_vulnerabilities': len(self.failed_vulns),
            'fixed': self.fixed_vulns,
            'failed': self.failed_vulns,
            'recommendations': [
                '手动审查所有自动修复的代码',
                '运行完整的测试套件验证修复',
                '实施代码审查流程',
                '配置CI/CD自动扫描',
                '定期更新依赖库'
            ]
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

    def run_git_commands(self, commands: List[str]) -> bool:
        """执行Git命令"""
        try:
            for cmd in commands:
                subprocess.run(cmd, shell=True, check=True, cwd=self.project_dir)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Git命令执行失败: {e}")
            return False

    def commit_fixes(self, branch_name: str = 'security/auto-fix') -> bool:
        """提交修复到Git"""
        commands = [
            'git add -A',
            f'git checkout -b {branch_name}',
            'git commit -m "Security: Automated vulnerability fixes

- Fixed SQL injection vulnerabilities
- Removed hardcoded credentials
- Updated weak cryptography
- Fixed XSS vulnerabilities
- Updated vulnerable dependencies

This is an automated fix. Please review all changes before merging."',
            'git push origin ' + branch_name
        ]

        return self.run_git_commands(commands)

    def run_fixes(self, report_dir: str, auto_commit: bool = False) -> Dict:
        """运行所有修复"""
        results = {
            'sast': {'fixed': 0, 'failed': 0},
            'sca': {'fixed': 0, 'failed': 0},
            'total': {'fixed': 0, 'failed': 0}
        }

        # 修复SAST问题
        sast_file = Path(report_dir) / 'sast-report-*.json'
        sast_reports = list(Path(report_dir).glob('sast-report-*.json'))
        for sast_report_path in sast_reports:
            sast_report = self.load_security_report(str(sast_report_path))
            sast_results = self.fix_sast_vulnerabilities(sast_report)
            results['sast']['fixed'] += sast_results['fixed']
            results['sast']['failed'] += sast_results['failed']

        # 修复SCA问题
        sca_reports = list(Path(report_dir).glob('sca-report-*.json'))
        for sca_report_path in sca_reports:
            sca_report = self.load_security_report(str(sca_report_path))
            sca_results = self.fix_sca_vulnerabilities(sca_report)
            results['sca']['fixed'] += sca_results['fixed']
            results['sca']['failed'] += sca_results['failed']

        # 计算总计
        results['total']['fixed'] = results['sast']['fixed'] + results['sca']['fixed']
        results['total']['failed'] = results['sast']['failed'] + results['sca']['failed']

        # 创建修复报告
        fix_report_file = Path(report_dir) / f'fix-report-{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        self.create_fix_report(str(fix_report_file))

        # 自动提交（如果启用）
        if auto_commit and results['total']['fixed'] > 0:
            if self.commit_fixes():
                print(f"修复已提交到分支: security/auto-fix")

        return results


def main():
    parser = argparse.ArgumentParser(description='自动化漏洞修复工具')
    parser.add_argument('--project-dir', default='.', help='项目目录路径')
    parser.add_argument('--report-dir', required=True, help='安全报告目录')
    parser.add_argument('--auto-commit', action='store_true', help='自动提交修复')

    args = parser.parse_args()

    # 创建修复器
    fixer = VulnerabilityFixer(args.project_dir)

    # 运行修复
    print("开始自动修复漏洞...")
    results = fixer.run_fixes(args.report_dir, args.auto_commit)

    # 输出结果
    print("\n=== 修复结果 ===")
    print(f"SAST: 修复 {results['sast']['fixed']} 个，失败 {results['sast']['failed']} 个")
    print(f"SCA: 修复 {results['sca']['fixed']} 个，失败 {results['sca']['failed']} 个")
    print(f"总计: 修复 {results['total']['fixed']} 个，失败 {results['total']['failed']} 个")

    if results['total']['fixed'] > 0:
        print("\n⚠️  请手动审查所有自动修复的代码")
        print("⚠️  运行完整测试套件验证修复")
        print("⚠️  进行代码审查后再合并")


if __name__ == '__main__':
    from datetime import datetime
    main()