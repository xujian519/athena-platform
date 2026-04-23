#!/usr/bin/env python3
"""
Athena安全配置验证脚本
验证所有安全配置是否正确设置
"""

import logging
import os
import sys
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SecurityValidator:
    """安全配置验证器"""

    # 必需的环境变量
    REQUIRED_VARS = {
        'DB_PASSWORD': {
            'description': '数据库密码',
            'min_length': 8,
            'check_default': True,
            'default_values': ['password', 'postgres', 'xj781102', 'xujian519_athena']
        },
        'JWT_SECRET': {
            'description': 'JWT密钥',
            'min_length': 32,
            'check_default': True,
            'default_values': [
                'your-super-secret-key',
                'jwt_secret',
                'change-in-production',
                'your-secret-key-here'
            ]
        },
        'JWT_SECRET_KEY': {
            'description': 'JWT密钥（备用）',
            'min_length': 32,
            'check_default': True,
            'default_values': [
                'AthenaJWT2025#VerySecureKey256Bit',
                'your-jwt-secret-key'
            ]
        },
        'NEO4J_PASSWORD': {
            'description': 'Neo4j密码',
            'min_length': 8,
            'check_default': True,
            'default_values': ['password']
        }
    }

    # 推荐的环境变量
    RECOMMENDED_VARS = {
        'REDIS_PASSWORD': {
            'description': 'Redis密码',
            'min_length': 16
        },
        'OPENAI_API_KEY': {
            'description': 'OpenAI API密钥',
            'min_length': 20
        },
        'ZHIPU_API_KEY': {
            'description': '智谱AI API密钥',
            'min_length': 20
        },
        'DEEPSEEK_API_KEY': {
            'description': 'DeepSeek API密钥',
            'min_length': 20
        }
    }

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.passed = []

    def validate_required_var(self, var_name: str, config: dict) -> bool:
        """验证必需的环境变量"""
        value = os.getenv(var_name)

        if not value:
            self.errors.append(
                f"❌ {var_name} ({config['description']}) 未设置"
            )
            return False

        # 检查长度
        if len(value) < config['min_length']:
            self.errors.append(
                f"❌ {var_name} 长度不足（当前: {len(value)}，要求: {config['min_length']}）"
            )
            return False

        # 检查是否使用默认值
        if config.get('check_default'):
            for default in config.get('default_values', []):
                if default in value.lower():
                    self.errors.append(
                        f"❌ {var_name} 使用了不安全的默认值（包含: {default}）"
                    )
                    return False

        self.passed.append(f"✅ {var_name} ({config['description']})")
        return True

    def validate_recommended_var(self, var_name: str, config: dict) -> bool:
        """验证推荐的环境变量"""
        value = os.getenv(var_name)

        if not value:
            self.warnings.append(
                f"⚠️  {var_name} ({config['description']}) 未设置（推荐配置）"
            )
            return False

        # 检查长度
        if len(value) < config['min_length']:
            self.warnings.append(
                f"⚠️  {var_name} 长度可能不足（当前: {len(value)}，推荐: {config['min_length']}）"
            )
            return False

        self.passed.append(f"✅ {var_name} ({config['description']})")
        return True

    def check_hardcoded_secrets(self) -> list[str]:
        """检查代码中是否还有硬编码的密钥"""
        hardcoded_secrets = []

        # 已知的硬编码密钥（应该被替换的）
        known_secrets = [
            'xj781102',
            'xujian519_athena',
            'AthenaJWT2025#VerySecureKey256Bit',
            'Athena@2025#RedisSecure',
            '9efe5766a7cd4bb687e40082ee4032b6.0mYTotbC7aRmoNCe',
            'sk-7f0fa1165de249d0a30b62a2584bd4c5',
            'athena_integration_2024',
            'athena_perception_secure_2024',
        ]

        # 检查关键文件
        files_to_check = [
            'core/auth/authentication.py',
            'shared/auth/auth_middleware.py',
            'knowledge_graph/neo4j_graph_engine.py',
            'tools/patent_archive_updater.py',
        ]

        for file_path in files_to_check:
            full_path = Path(file_path)
            if not full_path.exists():
                continue

            try:
                content = full_path.read_text(encoding='utf-8')
                for secret in known_secrets:
                    if secret in content:
                        hardcoded_secrets.append(f"{file_path}: {secret[:10]}...")
            except Exception as e:
                logger.error(f"检查文件 {file_path} 失败: {e}")

        return hardcoded_secrets

    def check_env_file_permissions(self) -> bool:
        """检查.env文件权限"""
        env_path = Path('.env')

        if not env_path.exists():
            self.warnings.append("⚠️  .env 文件不存在（请复制.env.example为.env）")
            return False

        # 检查文件权限
        stat = env_path.stat()
        mode = oct(stat.st_mode)[-3:]

        if mode != '600':
            self.warnings.append(
                f"⚠️  .env 文件权限不安全（当前: {mode}，推荐: 600）"
            )
            self.warnings.append("   运行: chmod 600 .env")
            return False

        self.passed.append("✅ .env 文件权限正确 (600)")
        return True

    def validate_all(self) -> dict:
        """执行所有验证"""
        logger.info("🔍 开始安全配置验证...")

        # 验证必需的环境变量
        logger.info("\n📋 验证必需的环境变量:")
        for var_name, config in self.REQUIRED_VARS.items():
            self.validate_required_var(var_name, config)

        # 验证推荐的环境变量
        logger.info("\n📋 验证推荐的环境变量:")
        for var_name, config in self.RECOMMENDED_VARS.items():
            self.validate_recommended_var(var_name, config)

        # 检查硬编码密钥
        logger.info("\n📋 检查硬编码密钥:")
        hardcoded = self.check_hardcoded_secrets()
        if hardcoded:
            for secret in hardcoded:
                self.errors.append(f"❌ 发现硬编码密钥: {secret}")
        else:
            self.passed.append("✅ 未发现硬编码密钥")

        # 检查文件权限
        logger.info("\n📋 检查文件权限:")
        self.check_env_file_permissions()

        return {
            'passed': len(self.passed),
            'warnings': len(self.warnings),
            'errors': len(self.errors),
            'success': len(self.errors) == 0
        }

    def print_report(self):
        """打印验证报告"""
        print("\n" + "=" * 80)
        print("Athena安全配置验证报告")
        print("=" * 80)

        if self.passed:
            print(f"\n✅ 通过检查 ({len(self.passed)} 项):")
            for item in self.passed:
                print(f"  {item}")

        if self.warnings:
            print(f"\n⚠️  警告 ({len(self.warnings)} 项):")
            for warning in self.warnings:
                print(f"  {warning}")

        if self.errors:
            print(f"\n❌ 错误 ({len(self.errors)} 项):")
            for error in self.errors:
                print(f"  {error}")

        print("\n" + "=" * 80)

        # 总体评估
        if not self.errors:
            if not self.warnings:
                print("🎉 安全配置完美！所有检查都通过了。")
            else:
                print("✅ 安全配置基本合格，但有一些警告需要注意。")
        else:
            print("⚠️  安全配置存在问题，请按照错误提示进行修复。")

        print("=" * 80)

    def get_fix_commands(self) -> str:
        """生成修复命令"""
        commands = []
        commands.append("\n# 🔧 修复命令:")
        commands.append("\n# 1. 生成安全的密码和密钥:")
        commands.append("echo \"DB_PASSWORD=$(openssl rand -base64 16)\" >> .env")
        commands.append("echo \"JWT_SECRET=$(openssl rand -hex 32)\" >> .env")
        commands.append("echo \"JWT_SECRET_KEY=$(openssl rand -hex 32)\" >> .env")
        commands.append("echo \"NEO4J_PASSWORD=$(openssl rand -base64 12)\" >> .env")
        commands.append("echo \"REDIS_PASSWORD=$(openssl rand -base64 16)\" >> .env")

        commands.append("\n# 2. 设置.env文件权限:")
        commands.append("chmod 600 .env")

        commands.append("\n# 3. 验证配置:")
        commands.append("python3 scripts/verify_security_config.py")

        return "\n".join(commands)


def main():
    """主函数"""
    # 切换到项目根目录
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    # 创建验证器
    validator = SecurityValidator()

    # 执行验证
    result = validator.validate_all()

    # 打印报告
    validator.print_report()

    # 如果有错误，显示修复命令
    if result['errors']:
        print(validator.get_fix_commands())
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    main()
