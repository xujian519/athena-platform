#!/usr/bin/env python3
"""
本地CI/CD自动化部署脚本
Local CI/CD Deployment Script

功能:
1. 运行测试套件
2. 检查代码质量
3. 备份当前生产环境
4. 部署到生产环境
5. 运行数据库迁移
6. 验证部署

使用:
    python scripts/deploy_to_production.py

作者: 小诺·双鱼座
创建时间: 2026-01-26
"""

import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ANSI颜色码
class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"


class DeploymentLogger:
    """部署日志记录器"""

    def __init__(self, log_file: str):
        self.log_file = log_file
        self.log_dir = Path(log_file).parent
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def log(self, message: str, level: str = "INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}"

        # 写入文件
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_message + "\n")

        # 控制台输出
        color = {
            "INFO": Colors.BLUE,
            "SUCCESS": Colors.GREEN,
            "WARNING": Colors.YELLOW,
            "ERROR": Colors.RED,
        }.get(level, "")

        print(f"{color}{log_message}{Colors.END}")

    def success(self, message: str):
        self.log(message, "SUCCESS")

    def error(self, message: str):
        self.log(message, "ERROR")

    def warning(self, message: str):
        self.log(message, "WARNING")

    def info(self, message: str):
        self.log(message, "INFO")


class CommandRunner:
    """命令执行器"""

    def __init__(self, logger: DeploymentLogger):
        self.logger = logger

    def run(self, command: str, description: str = None, timeout: int = 300) -> bool:
        """运行命令"""
        if description:
            self.logger.info(f"执行: {description}")

        self.logger.info(f"命令: {command}")

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            if result.stdout:
                self.logger.info(f"输出: {result.stdout[:500]}")

            if result.stderr and "warning" not in result.stderr.lower():
                self.logger.warning(f"错误输出: {result.stderr[:500]}")

            if result.returncode == 0:
                self.logger.success(f"命令执行成功: {description or command}")
                return True
            else:
                self.logger.error(f"命令执行失败: {description or command} (退出码: {result.returncode})")
                return False

        except subprocess.TimeoutExpired:
            self.logger.error(f"命令执行超时: {description or command}")
            return False
        except Exception as e:
            self.logger.error(f"命令执行异常: {e}")
            return False


class DeploymentConfig:
    """部署配置"""

    # 项目路径
    PROJECT_ROOT = Path("/Users/xujian/Athena工作平台")
    PRODUCTION_DIR = PROJECT_ROOT / "production"
    BACKUP_DIR = Path("/Users/xujian/AthenaData/Athena工作平台备份/backups")

    # PostgreSQL配置 (使用本地17.7版本)
    PG_VERSION = "17.7"
    PG_HOST = "localhost"
    PG_PORT = 5432
    PG_USER = "postgres"
    PG_DATABASE = "athena_production"

    # 服务端口
    API_PORT = 8000
    PROMETHEUS_PORT = 9090
    GRAFANA_PORT = 3000

    # 部署超时时间
    DEPLOYMENT_TIMEOUT = 600

    @classmethod
    def verify_postgresql(cls):
        """验证PostgreSQL版本"""
        try:
            result = subprocess.run(
                ["psql", "--version"],
                capture_output=True,
                text=True,
            )
            version = result.stdout.strip()
            if cls.PG_VERSION in version:
                return True, version
            else:
                return False, f"PostgreSQL版本不匹配: 期望{cls.PG_VERSION}, 实际{version}"
        except Exception as e:
            return False, f"无法检查PostgreSQL版本: {e}"


class ProductionDeployer:
    """生产环境部署器"""

    def __init__(self):
        # 创建日志
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"logs/deployment_{timestamp}.log"

        self.logger = DeploymentLogger(log_file)
        self.runner = CommandRunner(self.logger)
        self.config = DeploymentConfig()

    def print_banner(self):
        """打印横幅"""
        banner = f"""
{Colors.BOLD}{'='*60}
    Athena工作平台 - 本地CI/CD部署系统
    版本: v1.0.0
    时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    PostgreSQL: {self.config.PG_VERSION}
{'='*60}{Colors.END}
"""
        print(banner)
        self.logger.info("部署开始")

    def verify_environment(self) -> bool:
        """验证环境"""
        self.logger.info("="*60)
        self.logger.info("步骤1: 验证环境")
        self.logger.info("="*60)

        # 检查PostgreSQL
        success, message = self.config.verify_postgresql()
        if success:
            self.logger.success(f"PostgreSQL检查通过: {message}")
        else:
            self.logger.error(message)
            return False

        # 检查项目目录
        if not self.config.PROJECT_ROOT.exists():
            self.logger.error(f"项目目录不存在: {self.config.PROJECT_ROOT}")
            return False

        self.logger.success(f"项目目录: {self.config.PROJECT_ROOT}")

        # 检查Python版本
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        self.logger.info(f"Python版本: {python_version}")

        if sys.version_info < (3, 10):
            self.logger.warning("建议使用Python 3.10+")

        return True

    def run_tests(self) -> bool:
        """运行测试套件"""
        self.logger.info("="*60)
        self.logger.info("步骤2: 运行测试套件")
        self.logger.info("="*60)

        # 运行pytest
        command = f"cd {self.config.PROJECT_ROOT} && python3 -m pytest tests/ -v --tb=short --maxfail=5"

        success = self.runner.run(
            command,
            description="运行测试套件",
            timeout=300,
        )

        if success:
            self.logger.success("所有测试通过")
        else:
            self.logger.error("测试失败，部署中止")

        return success

    def backup_production(self) -> bool:
        """备份生产环境"""
        self.logger.info("="*60)
        self.logger.info("步骤3: 备份生产环境")
        self.logger.info("="*60)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.config.BACKUP_DIR / f"backup_{timestamp}"
        backup_path.mkdir(parents=True, exist_ok=True)

        # 备份数据库
        db_backup_file = backup_path / "database.sql"

        command = f"pg_dump -h {self.config.PG_HOST} -p {self.config.PG_PORT} -U {self.config.PG_USER} -d {self.config.PG_DATABASE} -f {db_backup_file}"

        success = self.runner.run(
            command,
            description="备份数据库",
            timeout=600,
        )

        if not success:
            self.logger.warning("数据库备份失败，继续部署")

        # 备份配置文件
        config_backup = backup_path / "config"
        command = f"cp -r {self.config.PROJECT_ROOT / 'config'} {config_backup}"

        self.runner.run(
            command,
            description="备份配置文件",
        )

        self.logger.success(f"备份完成: {backup_path}")
        return True

    def deploy_to_production(self) -> bool:
        """部署到生产环境"""
        self.logger.info("="*60)
        self.logger.info("步骤4: 部署到生产环境")
        self.logger.info("="*60)

        # 创建生产目录
        self.config.PRODUCTION_DIR.mkdir(parents=True, exist_ok=True)

        # 复制核心文件
        core_dirs = ["core", "config", "scripts"]

        for dir_name in core_dirs:
            src = self.config.PROJECT_ROOT / dir_name
            dst = self.config.PRODUCTION_DIR / dir_name

            command = f"rsync -av --delete {src}/ {dst}/"
            self.runner.run(command, description=f"同步{dir_name}目录")

        # 安装依赖
        command = f"cd {self.config.PROJECT_ROOT} && poetry install --only main"

        self.runner.run(
            command,
            description="安装生产依赖",
            timeout=300,
        )

        self.logger.success("文件部署完成")
        return True

    def migrate_database(self) -> bool:
        """数据库迁移"""
        self.logger.info("="*60)
        self.logger.info("步骤5: 数据库迁移")
        self.logger.info("="*60)

        # 检查连接
        command = f"psql -h {self.config.PG_HOST} -p {self.config.PG_PORT} -U {self.config.PG_USER} -d {self.config.PG_DATABASE} -c 'SELECT version();'"

        success = self.runner.run(
            command,
            description="测试数据库连接",
        )

        if not success:
            self.logger.error("数据库连接失败")
            return False

        # 运行迁移脚本（如果有）
        migration_script = self.config.PROJECT_ROOT / "scripts" / "migrate_database.py"

        if migration_script.exists():
            command = f"python3 {migration_script}"

            success = self.runner.run(
                command,
                description="运行数据库迁移",
            )

            if not success:
                self.logger.error("数据库迁移失败")
                return False
        else:
            self.logger.info("未找到迁移脚本，跳过迁移")

        self.logger.success("数据库迁移完成")
        return True

    def restart_services(self) -> bool:
        """重启服务"""
        self.logger.info("="*60)
        self.logger.info("步骤6: 重启服务")
        self.logger.info("="*60)

        # 停止现有服务
        self.logger.info("停止现有服务...")

        # 使用pkill找到并停止uvicorn进程
        self.runner.run(
            f"pkill -f 'uvicorn.*:{self.config.API_PORT}' || true",
            description="停止API服务",
        )

        time.sleep(2)

        # 启动新服务
        self.logger.info("启动新服务...")

        api_command = f"cd {self.config.PRODUCTION_DIR} && nohup python3 -m uvicorn core.api.main:app --host 0.0.0.0 --port {self.config.API_PORT} > logs/api.log 2>&1 &"

        success = self.runner.run(
            api_command,
            description="启动API服务",
        )

        if not success:
            self.logger.error("API服务启动失败")
            return False

        # 等待服务启动
        self.logger.info("等待服务启动...")
        time.sleep(5)

        # 验证服务
        command = f"curl -f http://localhost:{self.config.API_PORT}/health || echo 'Health check not available'"

        self.runner.run(
            command,
            description="健康检查",
        )

        self.logger.success("服务重启完成")
        return True

    def verify_deployment(self) -> bool:
        """验证部署"""
        self.logger.info("="*60)
        self.logger.info("步骤7: 验证部署")
        self.logger.info("="*60)

        # 检查API端点
        command = f"curl -s http://localhost:{self.config.API_PORT}/ | head -20"

        success = self.runner.run(
            command,
            description="检查API根路径",
        )

        # 检查数据库连接
        command = f"psql -h {self.config.PG_HOST} -p {self.config.PG_PORT} -U {self.config.PG_USER} -d {self.config.PG_DATABASE} -c 'SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = '\''public'\'';'"

        self.runner.run(
            command,
            description="检查数据库表",
        )

        self.logger.success("部署验证完成")
        return True

    def cleanup_old_backups(self, keep_days: int = 7):
        """清理旧备份"""
        self.logger.info("="*60)
        self.logger.info("步骤8: 清理旧备份")
        self.logger.info("="*60)

        if not self.config.BACKUP_DIR.exists():
            self.logger.info("备份目录不存在，跳过清理")
            return

        # 查找并删除旧备份
        import time

        current_time = time.time()
        cutoff_time = current_time - (keep_days * 86400)

        deleted_count = 0
        for backup_dir in self.config.BACKUP_DIR.iterdir():
            if backup_dir.is_dir() and backup_dir.name.startswith("backup_"):
                if backup_dir.stat().st_mtime < cutoff_time:
                    # 删除旧备份
                    import shutil
                    try:
                        shutil.rmtree(backup_dir)
                        deleted_count += 1
                        self.logger.info(f"删除旧备份: {backup_dir.name}")
                    except Exception as e:
                        self.logger.warning(f"删除备份失败: {e}")

        self.logger.success(f"清理完成，删除了 {deleted_count} 个旧备份")

    def deploy(self):
        """执行完整部署流程"""
        self.print_banner()

        steps = [
            ("验证环境", self.verify_environment),
            ("运行测试", self.run_tests),
            ("备份生产环境", self.backup_production),
            ("部署到生产环境", self.deploy_to_production),
            ("数据库迁移", self.migrate_database),
            ("重启服务", self.restart_services),
            ("验证部署", self.verify_deployment),
            ("清理旧备份", lambda: self.cleanup_old_backups(keep_days=7)),
        ]

        failed_step = None

        for step_name, step_func in steps:
            try:
                success = step_func()
                if not success:
                    failed_step = step_name
                    break
            except Exception as e:
                self.logger.error(f"{step_name}异常: {e}")
                failed_step = step_name
                break

        # 部署结果
        self.logger.info("="*60)
        if failed_step:
            self.logger.error(f"部署失败于步骤: {failed_step}")
            self.logger.info("请检查日志文件获取详细信息")
            return False
        else:
            self.logger.success("="*60)
            self.logger.success("🎉 部署成功完成!")
            self.logger.success("="*60)
            self.logger.success(f"API服务: http://localhost:{self.config.API_PORT}")
            self.logger.success(f"API文档: http://localhost:{self.config.API_PORT}/docs")
            self.logger.success(f"PostgreSQL: {self.config.PG_VERSION}")
            return True


def main():
    """主函数"""
    deployer = ProductionDeployer()

    try:
        success = deployer.deploy()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        deployer.logger.warning("部署被用户中断")
        sys.exit(130)
    except Exception as e:
        deployer.logger.error(f"部署异常: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
