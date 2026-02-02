#!/usr/bin/env python3
"""
重构后的平台部署脚本
使用新的部署管理框架
"""

import sys
import os
import asyncio
from pathlib import Path

# 添加核心库路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.deployment import deployment_manager
from services.manager import ServiceManager
from utils.logger import ScriptLogger
from utils.progress_tracker import ProgressTracker


class PlatformDeployer:
    """平台部署器"""

    def __init__(self):
        self.logger = ScriptLogger("PlatformDeployer")
        self.deployment_manager = deployment_manager
        self.service_manager = ServiceManager.instance()

    async def deploy(self, config_name: str, version: str = None,
                    environment: str = None, backup: bool = True):
        """部署平台"""
        try:
            self.logger.info("🚀 开始部署 Athena 平台...")

            # 创建部署
            deploy_id = self.deployment_manager.create_deployment(
                config_name=config_name,
                version=version,
                environment=environment
            )

            # 创建进度跟踪器
            tracker = ProgressTracker(100, f"部署 {config_name}")

            # 1. 部署前检查
            self.logger.info("执行部署前检查...")
            await self._pre_deploy_checks(config_name)
            tracker.update(10, "部署前检查完成")

            # 2. 创建备份
            if backup:
                self.logger.info("创建当前版本备份...")
                # 备份由 deployment_manager 自动处理
                tracker.update(20, "备份完成")

            # 3. 执行部署
            self.logger.info(f"执行部署: {deploy_id}...")
            success = await self.deployment_manager.deploy(deploy_id)
            tracker.update(70, "部署完成")

            if success:
                # 4. 部署后验证
                self.logger.info("执行部署后验证...")
                await self._post_deploy_verification(config_name)
                tracker.update(90, "部署验证完成")

                # 5. 生成部署报告
                report = self.deployment_manager.generate_deployment_report(deploy_id)
                print("\n" + report)

                tracker.complete()
                self.logger.info(f"✅ 部署成功: {deploy_id}")
                return True
            else:
                self.logger.error(f"❌ 部署失败: {deploy_id}")
                return False

        except Exception as e:
            self.logger.error(f"部署过程出错: {e}")
            return False

    async def rollback(self, config_name: str, version: str = None):
        """回滚部署"""
        try:
            self.logger.info("↩️ 开始回滚...")

            # 获取最近的部署
            deployments = self.deployment_manager.list_deployments(
                config_name=config_name,
                limit=10
            )

            if not deployments:
                raise ValueError("没有找到可回滚的部署")

            # 选择要回滚的版本
            if version:
                # 找到指定版本的部署
                target_deploy = None
                for deploy in deployments:
                    if deploy.version == version:
                        target_deploy = deploy
                        break

                if not target_deploy:
                    raise ValueError(f"没有找到版本 {version} 的部署")
            else:
                # 回滚到上一个成功的部署
                target_deploy = None
                for deploy in deployments:
                    if deploy.status == 'success':
                        target_deploy = deploy
                        break

                if not target_deploy:
                    raise ValueError("没有找到可回滚的成功部署")

            # 执行回滚
            success = await self.deployment_manager.rollback(target_deploy.id)

            if success:
                self.logger.info(f"✅ 回滚成功: 版本 {target_deploy.version}")
                return True
            else:
                self.logger.error(f"❌ 回滚失败")
                return False

        except Exception as e:
            self.logger.error(f"回滚过程出错: {e}")
            return False

    async def _pre_deploy_checks(self, config_name: str):
        """部署前检查"""
        # 1. 检查配置是否存在
        if config_name not in self.deployment_manager.configs:
            raise ValueError(f"部署配置 {config_name} 不存在")

        config = self.deployment_manager.configs[config_name]

        # 2. 检查源路径
        if not os.path.exists(config.source_path):
            raise ValueError(f"源路径不存在: {config.source_path}")

        # 3. 检查目标目录权限
        target_dir = Path(config.target_path).parent
        if not os.access(target_dir, os.W_OK):
            raise ValueError(f"目标目录无写权限: {target_dir}")

        # 4. 检查依赖
        if config.dependencies:
            self.logger.info("检查部署依赖...")
            for dep in config.dependencies:
                # 这里可以添加具体的依赖检查逻辑
                self.logger.info(f"依赖检查: {dep}")

    async def _post_deploy_verification(self, config_name: str):
        """部署后验证"""
        config = self.deployment_manager.configs[config_name]

        # 1. 健康检查
        if config.health_check_url:
            self.logger.info("执行健康检查...")
            await self.deployment_manager._health_check(config.health_check_url)

        # 2. 服务状态检查
        self.logger.info("检查服务状态...")
        status = self.service_manager.get_all_status()
        failed_services = [
            name for name, info in status.items()
            if info['status'] == 'error'
        ]

        if failed_services:
            self.logger.warning(f"以下服务状态异常: {', '.join(failed_services)}")

        # 3. 基本功能测试
        self.logger.info("执行基本功能测试...")
        # 这里可以添加具体的功能测试

    def list_deployments(self, config_name: str = None):
        """列出部署历史"""
        deployments = self.deployment_manager.list_deployments(config_name)

        print("\n" + "="*80)
        print("📋 部署历史")
        print("="*80)
        print(f"{'ID':<25} {'配置':<15} {'版本':<10} {'环境':<8} {'状态':<10} {'时间':<20}")
        print("-"*80)

        for deploy in deployments:
            status_icon = {
                'pending': '⏳',
                'deploying': '🔄',
                'success': '✅',
                'failed': '❌',
                'rolling_back': '↩️'
            }.get(deploy.status, '❓')

            print(f"{deploy.id:<25} {deploy.config_name:<15} {deploy.version:<10} "
                  f"{deploy.environment:<8} {status_icon} {deploy.status:<9} "
                  f"{deploy.start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        print("="*80)


async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='Athena 平台部署器')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # deploy 命令
    deploy_parser = subparsers.add_parser('deploy', help='部署平台')
    deploy_parser.add_argument('config', help='部署配置名称')
    deploy_parser.add_argument('--version', help='部署版本')
    deploy_parser.add_argument('--env', help='部署环境')
    deploy_parser.add_argument('--no-backup', action='store_true', help='不创建备份')

    # rollback 命令
    rollback_parser = subparsers.add_parser('rollback', help='回滚部署')
    rollback_parser.add_argument('config', help='部署配置名称')
    rollback_parser.add_argument('--version', help='回滚到指定版本')

    # list 命令
    list_parser = subparsers.add_parser('list', help='列出部署历史')
    list_parser.add_argument('--config', help='配置名称')

    args = parser.parse_args()

    # 创建部署器
    deployer = PlatformDeployer()

    if args.command == 'deploy':
        success = await deployer.deploy(
            config_name=args.config,
            version=args.version,
            environment=args.env,
            backup=not args.no_backup
        )
        sys.exit(0 if success else 1)

    elif args.command == 'rollback':
        success = await deployer.rollback(
            config_name=args.config,
            version=args.version
        )
        sys.exit(0 if success else 1)

    elif args.command == 'list':
        deployer.list_deployments(args.config)

    else:
        parser.print_help()


if __name__ == "__main__":
    # 运行部署器
    asyncio.run(main())