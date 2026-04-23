#!/usr/bin/env python3
"""
Athena硬编码密码批量修复脚本
自动扫描并修复所有硬编码的敏感信息
"""

import logging
import re
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SecurityFixer:
    """安全修复器"""

    # 需要修复的敏感信息模式
    PATTERNS = {
        'database_url': r'postgresql://\w+:(?P<password>[^@]+)@',
        'password_var': r'password\s*=\s*["\'](?P<password>[^"\']+)["\']',
        'jwt_secret': r'jwt_secret\s*[:=]\s*["\'](?P<secret>[^"\']+)["\']',
        'api_key': r'(?:ZHIPU|OPENAI|DEEPSEEK)_API_KEY\s*=\s*["\'](?P<key>[^"\']+)["\']',
        'redis_password': r'REDIS_PASSWORD\s*=\s*["\'](?P<password>[^"\']+)["\']',
        'neo4j_password': r'password\s*=\s*["\']password["\']',  # 默认密码
    }

    # 需要替换的已知硬编码值
    KNOWN_SECRETS = {
        'xj781102': 'DB_PASSWORD',
        'xujian519_athena': 'DB_PASSWORD',
        'AthenaJWT2025#VerySecureKey256Bit': 'JWT_SECRET',
        'Athena@2025#RedisSecure': 'REDIS_PASSWORD',
        'your-super-secret-key-change-in-production': 'JWT_SECRET',
        '9efe5766a7cd4bb687e40082ee4032b6.0mYTotbC7aRmoNCe': 'ZHIPU_API_KEY',
        'sk-7f0fa1165de249d0a30b62a2584bd4c5': 'DEEPSEEK_API_KEY',
    }

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.fixes_applied = []
        self.errors = []

    def scan_file(self, file_path: Path) -> list[dict]:
        """扫描单个文件"""
        issues = []

        try:
            content = file_path.read_text(encoding='utf-8')

            # 检查已知硬编码密钥
            for secret, env_var in self.KNOWN_SECRETS.items():
                if secret in content:
                    issues.append({
                        'type': 'known_secret',
                        'secret': secret,
                        'env_var': env_var,
                        'line': self.find_line_number(content, secret)
                    })

            # 检查默认密码
            if re.search(r'password\s*=\s*["\']password["\']', content):
                issues.append({
                    'type': 'default_password',
                    'line': self.find_line_number(content, "password='password'")
                })

        except Exception as e:
            logger.error(f"扫描文件 {file_path} 失败: {e}")
            self.errors.append(str(e))

        return issues

    def find_line_number(self, content: str, search_text: str) -> int:
        """查找文本所在的行号"""
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if search_text in line:
                return i
        return 0

    def fix_file(self, file_path: Path, issues: list[dict]) -> bool:
        """修复文件中的问题"""
        try:
            content = file_path.read_text(encoding='utf-8')
            modified = False

            # 添加导入语句（如果需要）
            if issues and 'from security.env_config import' not in content:
                # 在文件开头添加导入
                lines = content.split('\n')
                import_idx = 0

                # 找到最后一个import语句
                for i, line in enumerate(lines):
                    if line.strip().startswith('import ') or line.strip().startswith('from '):
                        import_idx = i + 1

                # 添加路径配置和安全导入
                insert_lines = [
                    '',
                    '# 导入安全配置',
                    'import sys',
                    'from pathlib import Path',
                    'sys.path.append(str(Path(__file__).parent.parent / "core"))',
                    'from security.env_config import get_env_var, get_database_url, get_jwt_secret',
                ]

                for line in reversed(insert_lines):
                    lines.insert(import_idx, line)

                content = '\n'.join(lines)
                modified = True

            # 替换硬编码密码
            for secret, env_var in self.KNOWN_SECRETS.items():
                if secret in content:
                    if env_var == 'DB_PASSWORD':
                        # 替换数据库URL
                        content = re.sub(
                            r'postgresql://\w+:' + re.escape(secret) + r'@',
                            'postgresql://postgres:${DB_PASSWORD}@',
                            content
                        )
                        # 或者使用get_database_url()函数
                        content = re.sub(
                            r'create_engine\(["\']postgresql://[^"\']+["\']\)',
                            'create_engine(get_database_url())',
                            content
                        )
                        content = re.sub(
                            r'["\']postgresql://[^"\']+["\']',
                            'get_database_url()',
                            content
                        )
                    elif env_var == 'JWT_SECRET':
                        content = content.replace(
                            f'jwt_secret = "{secret}"',
                            'jwt_secret = get_jwt_secret()'
                        )
                        content = content.replace(
                            f"jwt_secret = '{secret}'",
                            'jwt_secret = get_jwt_secret()'
                        )
                    else:
                        # 其他API密钥
                        env_var.lower()
                        content = content.replace(
                            f'{env_var} = "{secret}"',
                            f'{env_var} = get_env_var("{env_var}")'
                        )
                        content = content.replace(
                            f"{env_var} = '{secret}'",
                            f'{env_var} = get_env_var("{env_var}")'
                        )

                    modified = True
                    self.fixes_applied.append({
                        'file': str(file_path),
                        'secret': secret[:10] + '...',
                        'env_var': env_var
                    })

            # 替换默认密码
            content = re.sub(
                r'password\s*=\s*["\']password["\']',
                'password=os.getenv("DB_PASSWORD", "password")',
                content
            )

            if modified:
                # 写回文件
                file_path.write_text(content, encoding='utf-8')
                logger.info(f"✅ 已修复: {file_path}")
                return True

        except Exception as e:
            logger.error(f"修复文件 {file_path} 失败: {e}")
            self.errors.append(f"{file_path}: {e}")

        return False

    def scan_directory(self, directory: Path, extensions: tuple[str, ...] = ('.py',)) -> dict:
        """扫描目录"""
        results = {
            'scanned': 0,
            'issues': [],
            'files_with_issues': []
        }

        logger.info(f"🔍 扫描目录: {directory}")

        for ext in extensions:
            for file_path in directory.rglob(f'*{ext}'):
                # 跳过虚拟环境和备份目录
                if 'venv' in str(file_path) or '.git' in str(file_path):
                    continue
                if 'backup' in str(file_path) or 'legacy' in str(file_path):
                    continue

                results['scanned'] += 1
                issues = self.scan_file(file_path)

                if issues:
                    results['files_with_issues'].append(str(file_path))
                    results['issues'].extend([
                        {**issue, 'file': str(file_path)} for issue in issues
                    ])

        return results

    def generate_report(self) -> str:
        """生成修复报告"""
        report = []
        report.append("=" * 80)
        report.append("Athena硬编码密码修复报告")
        report.append("=" * 80)
        report.append("")

        if self.fixes_applied:
            report.append(f"✅ 成功修复: {len(self.fixes_applied)} 处")
            report.append("")
            report.append("修复详情:")
            for fix in self.fixes_applied:
                report.append(f"  - {fix['file']}")
                report.append(f"    密钥: {fix['secret']}")
                report.append(f"    环境变量: {fix['env_var']}")
        else:
            report.append("ℹ️  未发现需要修复的问题")

        if self.errors:
            report.append("")
            report.append(f"⚠️  错误: {len(self.errors)} 处")
            for error in self.errors:
                report.append(f"  - {error}")

        report.append("")
        report.append("=" * 80)

        return '\n'.join(report)


def main():
    """主函数"""
    # 项目根目录
    project_root = Path(__file__).parent.parent

    # 创建修复器
    fixer = SecurityFixer(project_root)

    # 扫描关键目录
    directories = [
        project_root / 'tools',
        project_root / 'core',
        project_root / 'shared',
        project_root / 'services',
        project_root / 'knowledge_graph',
    ]

    logger.info("🚀 开始扫描和修复硬编码密码...")

    total_issues = 0
    for directory in directories:
        if directory.exists():
            results = fixer.scan_directory(directory)
            total_issues += len(results['issues'])

            # 自动修复
            for file_path in results['files_with_issues']:
                file_issues = [i for i in results['issues'] if i['file'] == str(file_path)]
                fixer.fix_file(Path(file_path), file_issues)

    # 生成报告
    report = fixer.generate_report()
    print(report)

    # 保存报告
    report_path = project_root / 'HARDCODED_PASSWORD_FIX_REPORT.md'
    report_path.write_text(report, encoding='utf-8')
    logger.info(f"📄 报告已保存到: {report_path}")


if __name__ == '__main__':
    main()
