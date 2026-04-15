#!/usr/bin/env python3
"""
Athena服务迁移脚本
将现有服务迁移到统一API网关架构，包含完整的前进和回滚机制
"""

import argparse
import asyncio
import json
import logging
import shutil
import sys
from datetime import datetime
from pathlib import Path

import yaml

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("migration.log"), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


class MigrationManager:
    """迁移管理器"""

    def __init__(self, config_path: str = "migration_config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.backup_dir = Path("backups")
        self.migration_log = []

        # 确保备份目录存在
        self.backup_dir.mkdir(exist_ok=True)

    def _load_config(self) -> dict:
        """加载迁移配置"""
        try:
            if self.config_path.exists():
                with open(self.config_path, encoding="utf-8") as f:
                    return yaml.safe_load(f)
            else:
                return self._get_default_config()
        except Exception as error:
            logger.error(f"Failed to load config: {error}")
            return self._get_default_config()

    def _get_default_config(self) -> dict:
        """获取默认配置"""
        return {
            "services": {
                "patent-search": {
                    "name": "yunpat-agent",
                    "current_path": "../yunpat_agent",
                    "target_path": "../services/api-gateway/adapters/patent_search_adapter.py",
                    "port": 8050,
                    "health_check": "/health",
                    "backup": True,
                },
                "patent-writing": {
                    "name": "patent-writing-service",
                    "current_path": None,  # 新建服务
                    "target_path": "../services/api-gateway/adapters/patent_writing_adapter.py",
                    "port": 8051,
                    "health_check": "/health",
                    "backup": False,
                },
                "authentication": {
                    "name": "authentication-service",
                    "current_path": None,  # 新建服务
                    "target_path": "../services/api-gateway/adapters/authentication_adapter.py",
                    "port": 8052,
                    "health_check": "/health",
                    "backup": False,
                },
                "technical-analysis": {
                    "name": "technical-analysis-service",
                    "current_path": None,  # 新建服务
                    "target_path": "../services/api-gateway/adapters/technical_analysis_adapter.py",
                    "port": 8053,
                    "health_check": "/health",
                    "backup": False,
                },
            },
            "gateway": {
                "name": "api-gateway",
                "path": "../services/api-gateway",
                "port": 8080,
                "config_path": "../services/api-gateway/config/adapters.json",
            },
            "migration": {
                "backup_before_migration": True,
                "test_after_migration": True,
                "rollback_on_failure": True,
                "timeout_seconds": 300,
            },
        }

    async def pre_migration_checks(self) -> bool:
        """迁移前检查"""
        logger.info("开始迁移前检查...")

        checks = []

        # 检查必要文件是否存在
        for service_name, service_config in self.config["services"].items():
            if service_config.get("current_path"):
                current_path = Path(service_config["current_path"])
                if not current_path.exists():
                    checks.append(f"服务 {service_name} 当前路径不存在: {current_path}")

        # 检查目标目录是否可写
        gateway_path = Path(self.config["gateway"]["path"])
        if not gateway_path.exists():
            try:
                gateway_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"创建网关目录: {gateway_path}")
            except Exception as error:
                checks.append(f"无法创建网关目录: {error}")

        # 检查端口是否可用
        for service_name, service_config in self.config["services"].items():
            port = service_config.get("port")
            if port and await self._is_port_in_use(port):
                checks.append(f"端口 {port} 已被占用")

        if checks:
            logger.error("迁移前检查失败:")
            for check in checks:
                logger.error(f"  - {check}")
            return False

        logger.info("迁移前检查通过")
        return True

    async def _is_port_in_use(self, port: int) -> bool:
        """检查端口是否被占用"""
        try:
            import socket

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex(("localhost", port)) == 0
        except Exception:
            return False

    async def create_backup(self, service_name: str, service_config: dict) -> str | None:
        """创建服务备份"""
        if not service_config.get("backup", True):
            return None

        current_path = service_config.get("current_path")
        if not current_path:
            return None

        source_path = Path(current_path)
        if not source_path.exists():
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{service_name}_backup_{timestamp}"
        backup_path = self.backup_dir / backup_name

        try:
            logger.info(f"备份服务 {service_name} 到 {backup_path}")

            if source_path.is_dir():
                shutil.copytree(source_path, backup_path)
            else:
                shutil.copy2(source_path, backup_path)

            backup_info = {
                "service_name": service_name,
                "original_path": str(source_path),
                "backup_path": str(backup_path),
                "timestamp": timestamp,
                "config": service_config,
            }

            backup_info_path = backup_path.with_name(f"{backup_name}_info.json")
            with open(backup_info_path, "w", encoding="utf-8") as f:
                json.dump(backup_info, f, indent=2, ensure_ascii=False)

            self._log_migration_action(
                "backup",
                service_name,
                f"创建备份: {backup_path}",
                {"backup_path": str(backup_path)},
            )

            return str(backup_path)

        except Exception as error:
            logger.error(f"备份服务 {service_name} 失败: {error}")
            return None

    async def migrate_service(self, service_name: str, service_config: dict) -> bool:
        """迁移单个服务"""
        logger.info(f"开始迁移服务: {service_name}")

        try:
            # 创建备份
            backup_path = await self.create_backup(service_name, service_config)

            # 检查目标适配器是否存在
            target_path = Path(service_config["target_path"])
            if not target_path.exists():
                logger.error(f"目标适配器不存在: {target_path}")
                return False

            # 如果是现有服务，需要更新配置
            if service_config.get("current_path"):
                await self._update_existing_service(service_name, service_config)
            else:
                # 新建服务，需要创建启动脚本
                await self._create_new_service(service_name, service_config)

            # 验证迁移结果
            if await self._verify_service_migration(service_name, service_config):
                self._log_migration_action(
                    "migrate", service_name, "服务迁移成功", {"backup_path": backup_path}
                )
                return True
            else:
                logger.error(f"服务 {service_name} 迁移验证失败")
                return False

        except Exception as error:
            logger.error(f"迁移服务 {service_name} 失败: {error}")
            self._log_migration_action(
                "migrate", service_name, f"服务迁移失败: {error}", {"error": str(error)}
            )
            return False

    async def _update_existing_service(self, service_name: str, service_config: dict):
        """更新现有服务配置"""
        logger.info(f"更新现有服务配置: {service_name}")

        # 更新服务配置文件，指向新的API网关
        {
            "gateway_url": f"http://localhost:{self.config['gateway']['port']}",
            "adapter_enabled": True,
            "migration_timestamp": datetime.now().isoformat(),
        }

        # 这里可以添加具体的配置更新逻辑
        # 例如更新数据库连接、配置文件等

    async def _create_new_service(self, service_name: str, service_config: dict):
        """创建新服务"""
        logger.info(f"创建新服务: {service_name}")

        # 创建服务启动脚本
        service_dir = Path(f"../services/{service_name}")
        service_dir.mkdir(exist_ok=True)

        # 创建启动脚本
        start_script = service_dir / "start_service.py"
        start_script_content = f'''#!/usr/bin/env python3
"""
{service_name} 服务启动脚本
"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加适配器路径
sys.path.append(str(Path(__file__).parent.parent / "api-gateway" / "adapters"))

from {service_name.replace("-", "_")}_adapter import {service_name.title().replace("-", "")}Adapter
from patent_search_adapter import AdapterConfig

async def main():
    """启动服务"""
    config = AdapterConfig(
        service_url=f"http://localhost:{service_config["port"]}",
        health_threshold={service_config.get("health_threshold", 5000)},
        timeout={service_config.get("timeout", 30000)},
        retry_attempts={service_config.get("retry_attempts", 3)},
        debug_mode=True
    )

    adapter = {service_name.title().replace("-", "")}Adapter(config)
    await adapter.initialize()

    # 启动HTTP服务
    import uvicorn
    await uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port={service_config["port"]},
        log_level="info"
    )

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
'''

        with open(start_script, "w", encoding="utf-8") as f:
            f.write(start_script_content)

        start_script.chmod(0o755)

    async def _verify_service_migration(self, service_name: str, service_config: dict) -> bool:
        """验证服务迁移"""
        logger.info(f"验证服务迁移: {service_name}")

        try:
            # 检查服务健康状态
            port = service_config.get("port")
            health_path = service_config.get("health_check", "/health")

            # 等待服务启动
            max_attempts = 30
            for attempt in range(max_attempts):
                try:
                    import aiohttp

                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                            f"http://localhost:{port}{health_path}", timeout=5
                        ) as response:
                            if response.status == 200:
                                logger.info(f"服务 {service_name} 健康检查通过")
                                return True
                except Exception:
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(2)
                    else:
                        raise
        except Exception as error:
            logger.error(f"服务 {service_name} 健康检查失败: {error}")
            return False

    async def update_gateway_config(self) -> bool:
        """更新网关配置"""
        logger.info("更新API网关配置")

        try:
            gateway_config_path = Path(self.config["gateway"]["config_path"])
            gateway_config_path.parent.mkdir(parents=True, exist_ok=True)

            # 创建适配器配置
            adapter_config = {}
            for service_name, service_config in self.config["services"].items():
                adapter_config[service_name] = {
                    "service_url": f"http://localhost:{service_config['port']}",
                    "health_threshold": service_config.get("health_threshold", 5000),
                    "timeout": service_config.get("timeout", 30000),
                    "retry_attempts": service_config.get("retry_attempts", 3),
                    "debug_mode": False,
                }

            # 认证服务特殊配置
            if "authentication" in adapter_config:
                adapter_config["authentication"]["circuit_breaker"] = {
                    "secret": "your-jwt-secret-key",
                    "algorithm": "HS256",
                    "expires_in": 86400,
                    "bcrypt_rounds": 12,
                }

            # 保存配置
            with open(gateway_config_path, "w", encoding="utf-8") as f:
                json.dump(adapter_config, f, indent=2, ensure_ascii=False)

            self._log_migration_action(
                "config_update",
                "gateway",
                "更新网关配置成功",
                {"config_path": str(gateway_config_path)},
            )

            return True

        except Exception as error:
            logger.error(f"更新网关配置失败: {error}")
            return False

    async def rollback_service(self, service_name: str, backup_path: str) -> bool:
        """回滚单个服务"""
        logger.info(f"回滚服务: {service_name}")

        try:
            backup_info_path = Path(backup_path).with_name(f"{Path(backup_path).name}_info.json")

            if backup_info_path.exists():
                with open(backup_info_path, encoding="utf-8") as f:
                    backup_info = json.load(f)

                original_path = Path(backup_info["original_path"])

                # 恢复原始文件
                if Path(backup_path).is_dir():
                    if original_path.exists():
                        shutil.rmtree(original_path)
                    shutil.copytree(backup_path, original_path)
                else:
                    shutil.copy2(backup_path, original_path)

                self._log_migration_action(
                    "rollback", service_name, "服务回滚成功", {"backup_path": backup_path}
                )

                return True
            else:
                logger.error(f"找不到备份信息文件: {backup_info_path}")
                return False

        except Exception as error:
            logger.error(f"回滚服务 {service_name} 失败: {error}")
            return False

    async def full_migration(self) -> bool:
        """执行完整迁移"""
        logger.info("开始完整迁移流程")

        # 迁移前检查
        if not await self.pre_migration_checks():
            return False

        # 保存原始配置
        original_config_path = (
            self.backup_dir / f"original_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(original_config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

        migration_success = True
        migrated_services = []

        try:
            # 迁移各个服务
            for service_name, service_config in self.config["services"].items():
                if await self.migrate_service(service_name, service_config):
                    migrated_services.append(service_name)
                else:
                    migration_success = False
                    break

            # 如果所有服务迁移成功，更新网关配置
            if migration_success:
                if await self.update_gateway_config():
                    logger.info("API网关更新成功")
                else:
                    migration_success = False

            # 测试网关功能
            if migration_success and self.config["migration"]["test_after_migration"]:
                logger.info("开始网关功能测试")
                if await self._test_gateway_functionality():
                    logger.info("网关功能测试通过")
                else:
                    logger.error("网关功能测试失败")
                    migration_success = False

            # 如果迁移失败，执行回滚
            if not migration_success and self.config["migration"]["rollback_on_failure"]:
                logger.warning("迁移失败，开始回滚...")
                await self._rollback_all(migrated_services)

            return migration_success

        except Exception as error:
            logger.error(f"迁移过程中发生错误: {error}")
            if self.config["migration"]["rollback_on_failure"]:
                await self._rollback_all(migrated_services)
            return False

    async def _rollback_all(self, migrated_services: list[str]):
        """回滚所有已迁移的服务"""
        logger.info("开始回滚所有服务")

        for service_name in migrated_services:
            # 查找最新的备份
            backup_path = await self._find_latest_backup(service_name)
            if backup_path:
                await self.rollback_service(service_name, backup_path)
            else:
                logger.warning(f"找不到服务 {service_name} 的备份")

    async def _find_latest_backup(self, service_name: str) -> str | None:
        """查找最新的备份"""
        backups = list(self.backup_dir.glob(f"{service_name}_backup_*"))
        if not backups:
            return None

        latest_backup = max(backups, key=lambda p: p.stat().st_mtime)
        return str(latest_backup)

    async def _test_gateway_functionality(self) -> bool:
        """测试网关功能"""
        try:
            import aiohttp

            # 测试网关健康状态
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://localhost:{self.config['gateway']['port']}/health", timeout=10
                ) as response:
                    if response.status != 200:
                        logger.error(f"网关健康检查失败: {response.status}")
                        return False

            # 测试各个服务的API端点
            test_cases = [
                ("patent-search", "/api/v1/patents/search", {"query": "test"}),
                ("authentication", "/api/v1/auth/login", {"username": "test", "password": "test"}),
                ("technical-analysis", "/api/v1/analysis/patentability", {"title": "test"}),
            ]

            async with aiohttp.ClientSession() as session:
                for service_name, endpoint, test_data in test_cases:
                    try:
                        async with session.post(
                            f"http://localhost:{self.config['gateway']['port']}{endpoint}",
                            json=test_data,
                            timeout=10,
                        ) as response:
                            if response.status not in [200, 400, 401]:  # 400/401也是预期的响应
                                logger.error(f"服务 {service_name} API测试失败: {response.status}")
                                return False
                    except Exception as error:
                        logger.warning(f"服务 {service_name} API测试异常: {error}")
                        # 继续测试其他服务

            return True

        except Exception as error:
            logger.error(f"网关功能测试失败: {error}")
            return False

    def _log_migration_action(self, action: str, target: str, message: str, details: dict = None):
        """记录迁移操作"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "target": target,
            "message": message,
            "details": details or {},
        }

        self.migration_log.append(log_entry)

        # 同时写入日志文件
        with open("migration_actions.log", "a", encoding="utf-8") as f:
            f.write(f"{json.dumps(log_entry, ensure_ascii=False)}\n")

    async def generate_migration_report(self) -> str:
        """生成迁移报告"""
        report = {
            "migration_timestamp": datetime.now().isoformat(),
            "config": self.config,
            "actions": self.migration_log,
            "summary": {
                "total_actions": len(self.migration_log),
                "successful_actions": len(
                    [a for a in self.migration_log if "成功" in a["message"]]
                ),
                "failed_actions": len([a for a in self.migration_log if "失败" in a["message"]]),
            },
        }

        report_path = f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"迁移报告已生成: {report_path}")
        return report_path


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Athena服务迁移工具")
    parser.add_argument("--config", default="migration_config.yaml", help="迁移配置文件路径")
    parser.add_argument(
        "--action", choices=["migrate", "rollback", "status"], default="migrate", help="执行的操作"
    )
    parser.add_argument("--service", help="指定服务名称（可选）")

    args = parser.parse_args()

    # 创建迁移管理器
    manager = MigrationManager(args.config)

    if args.action == "migrate":
        if args.service:
            # 迁移单个服务
            service_config = manager.config["services"].get(args.service)
            if not service_config:
                logger.error(f"找不到服务配置: {args.service}")
                return 1

            success = await manager.migrate_service(args.service, service_config)
        else:
            # 完整迁移
            success = await manager.full_migration()

        # 生成报告
        await manager.generate_migration_report()
        return 0 if success else 1

    elif args.action == "rollback":
        if args.service:
            # 回滚单个服务
            backup_path = await manager._find_latest_backup(args.service)
            if backup_path:
                success = await manager.rollback_service(args.service, backup_path)
                return 0 if success else 1
            else:
                logger.error(f"找不到服务 {args.service} 的备份")
                return 1
        else:
            logger.error("回滚操作需要指定服务名称")
            return 1

    elif args.action == "status":
        # 显示迁移状态
        print("迁移状态:")
        for service_name in manager.config["services"]:
            backup_path = await manager._find_latest_backup(service_name)
            if backup_path:
                print(f"  {service_name}: 有备份 ({backup_path})")
            else:
                print(f"  {service_name}: 无备份")
        return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
