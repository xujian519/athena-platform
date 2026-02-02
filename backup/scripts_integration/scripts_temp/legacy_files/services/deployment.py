#!/usr/bin/env python3
"""
部署管理器
处理服务的部署、更新和回滚
"""

import os
import sys
import json
import shutil
import subprocess
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import git

from core.config import config
from core.database import db_manager
from utils.logger import ScriptLogger
from utils.progress_tracker import ProgressTracker
import time
import aiohttp


@dataclass
class DeploymentConfig:
    """部署配置"""
    name: str
    version: str
    environment: str  # dev, test, prod
    source_path: str
    target_path: str
    backup_path: str
    pre_deploy_commands: List[str] = None
    post_deploy_commands: List[str] = None
    health_check_url: str = None
    rollback_commands: List[str] = None
    dependencies: List[str] = None


@dataclass
class Deployment:
    """部署记录"""
    id: str
    config_name: str
    version: str
    environment: str
    status: str  # pending, deploying, success, failed, rolling_back
    start_time: datetime
    end_time: datetime | None = None
    commit_hash: str | None = None
    message: str = ""
    error: str = ""


class DeploymentManager:
    """部署管理器"""

    def __init__(self):
        self.logger = ScriptLogger("DeploymentManager")
        self.deployments: Dict[str, Deployment] = {}
        self.configs: Dict[str, DeploymentConfig] = {}
        self.load_deployment_configs()

    def load_deployment_configs(self):
        """加载部署配置"""
        self.logger.info("加载部署配置...")

        # 从配置文件加载
        deploy_configs = config.get('deployments', {})

        # 默认部署配置
        default_configs = {
            'athena_platform': {
                'name': 'Athena Platform',
                'source_path': '/Users/xujian/Athena工作平台',
                'target_path': '/opt/athena',
                'backup_path': '/opt/athena/backups',
                'health_check_url': 'http://localhost:8000/health',
                'pre_deploy_commands': [
                    'pip install -r requirements.txt',
                    'python manage.py migrate'
                ],
                'post_deploy_commands': [
                    'systemctl reload nginx',
                    'systemctl restart athena-platform'
                ],
                'rollback_commands': [
                    'systemctl stop athena-platform',
                    'rm -rf /opt/athena/current',
                    'cp -r /opt/athena/backups/{version} /opt/athena/current',
                    'systemctl start athena-platform'
                ]
            },
            'ai_models_service': {
                'name': 'AI Models Service',
                'source_path': '/Users/xujian/Athena工作平台/services/ai-models',
                'target_path': '/opt/athena/ai-models',
                'backup_path': '/opt/athena/backups/ai-models',
                'health_check_url': 'http://localhost:8001/health',
                'pre_deploy_commands': [
                    'pip install -r requirements.txt'
                ],
                'post_deploy_commands': [
                    'systemctl restart ai-models-service'
                ]
            }
        }

        # 合并配置
        deploy_configs.update(default_configs)

        # 转换为DeploymentConfig对象
        for name, cfg in deploy_configs.items():
            self.configs[name] = DeploymentConfig(
                name=name,
                version=cfg.get('version', 'latest'),
                environment=cfg.get('environment', 'prod'),
                source_path=cfg.get('source_path', ''),
                target_path=cfg.get('target_path', ''),
                backup_path=cfg.get('backup_path', ''),
                pre_deploy_commands=cfg.get('pre_deploy_commands', []),
                post_deploy_commands=cfg.get('post_deploy_commands', []),
                health_check_url=cfg.get('health_check_url'),
                rollback_commands=cfg.get('rollback_commands', []),
                dependencies=cfg.get('dependencies', [])
            )

        self.logger.info(f"加载了 {len(self.configs)} 个部署配置")

    def create_deployment(self, config_name: str, version: str = None,
                         environment: str = None) -> str:
        """创建部署"""
        if config_name not in self.configs:
            raise ValueError(f"部署配置 {config_name} 不存在")

        config = self.configs[config_name]

        # 生成部署ID
        deploy_id = f"{config_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 创建部署记录
        deployment = Deployment(
            id=deploy_id,
            config_name=config_name,
            version=version or config.version,
            environment=environment or config.environment,
            status='pending',
            start_time=datetime.now(),
            commit_hash=self._get_current_commit(config.source_path)
        )

        self.deployments[deploy_id] = deployment
        self.logger.info(f"创建部署: {deploy_id}")

        return deploy_id

    async def deploy(self, deploy_id: str) -> bool:
        """执行部署"""
        if deploy_id not in self.deployments:
            raise ValueError(f"部署 {deploy_id} 不存在")

        deployment = self.deployments[deploy_id]
        config = self.configs[deployment.config_name]

        deployment.status = 'deploying'
        self.logger.info(f"开始部署: {deploy_id}")

        try:
            # 1. 创建备份
            self._create_backup(config, deployment.version)

            # 2. 同步代码
            self._sync_code(config)

            # 3. 执行预部署命令
            if config.pre_deploy_commands:
                await self._execute_commands(config.pre_deploy_commands, "预部署")

            # 4. 部署应用
            self._deploy_application(config)

            # 5. 执行后部署命令
            if config.post_deploy_commands:
                await self._execute_commands(config.post_deploy_commands, "后部署")

            # 6. 健康检查
            if config.health_check_url:
                await self._health_check(config.health_check_url)

            # 部署成功
            deployment.status = 'success'
            deployment.end_time = datetime.now()
            deployment.message = "部署成功"

            # 保存到数据库
            await self._save_deployment_record(deployment)

            self.logger.info(f"部署成功: {deploy_id}")
            return True

        except Exception as e:
            # 部署失败
            deployment.status = 'failed'
            deployment.end_time = datetime.now()
            deployment.error = str(e)
            deployment.message = "部署失败"

            self.logger.error(f"部署失败: {deploy_id} - {e}")

            # 询问是否回滚
            if input("部署失败，是否回滚？(y/n): ").lower() == 'y':
                await self.rollback(deploy_id)

            return False

    async def rollback(self, deploy_id: str) -> bool:
        """回滚部署"""
        if deploy_id not in self.deployments:
            raise ValueError(f"部署 {deploy_id} 不存在")

        deployment = self.deployments[deploy_id]
        config = self.configs[deployment.config_name]

        deployment.status = 'rolling_back'
        self.logger.info(f"开始回滚: {deploy_id}")

        try:
            # 执行回滚命令
            if config.rollback_commands:
                # 替换版本变量
                commands = [
                    cmd.format(version=deployment.version)
                    for cmd in config.rollback_commands
                ]
                await self._execute_commands(commands, "回滚")

            deployment.status = 'success'
            deployment.message = f"已回滚到版本: {deployment.version}"
            self.logger.info(f"回滚成功: {deploy_id}")
            return True

        except Exception as e:
            deployment.status = 'failed'
            deployment.error = str(e)
            deployment.message = "回滚失败"
            self.logger.error(f"回滚失败: {deploy_id} - {e}")
            return False

    def _get_current_commit(self, path: str) -> str | None:
        """获取当前提交的哈希值"""
        try:
            repo = git.Repo(path)
            return repo.head.commit.hexsha
        except:
            return None

    def _create_backup(self, config: DeploymentConfig, version: str):
        """创建备份"""
        self.logger.info("创建部署备份...")

        backup_dir = Path(config.backup_path) / version
        backup_dir.mkdir(parents=True, exist_ok=True)

        if os.path.exists(config.target_path):
            shutil.copytree(config.target_path, backup_dir / 'current')

        self.logger.info(f"备份创建完成: {backup_dir}")

    def _sync_code(self, config: DeploymentConfig):
        """同步代码"""
        self.logger.info("同步代码...")

        # 创建目标目录
        Path(config.target_path).mkdir(parents=True, exist_ok=True)

        # 复制文件
        if os.path.exists(config.source_path):
            # 排除不需要的文件和目录
            exclude_patterns = {
                '.git', '__pycache__', '.DS_Store',
                'node_modules', '.pytest_cache', 'logs'
            }

            def ignore_func(path, names):
                ignored = []
                for name in names:
                    if name in exclude_patterns:
                        ignored.append(name)
                return ignored

            shutil.copytree(
                config.source_path,
                config.target_path,
                ignore=ignore_func,
                dirs_exist_ok=True
            )

        self.logger.info("代码同步完成")

    def _deploy_application(self, config: DeploymentConfig):
        """部署应用"""
        # 创建当前版本的软链接
        current_link = Path(config.target_path).parent / 'current'
        if current_link.exists():
            current_link.unlink()

        current_link.symlink_to(config.target_path)

    async def _execute_commands(self, commands: List[str], phase: str):
        """执行命令"""
        self.logger.info(f"执行{phase}命令...")

        for command in commands:
            self.logger.info(f"执行: {command}")
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                raise RuntimeError(f"{phase}命令失败: {command}\n{result.stderr}")

            if result.stdout:
                self.logger.info(f"输出: {result.stdout}")

    async def _health_check(self, url: str, timeout: int = 60):
        """健康检查"""
        self.logger.info(f"执行健康检查: {url}")

        import aiohttp
        start_time = time.time()

        async with aiohttp.ClientSession() as session:
            while time.time() - start_time < timeout:
                try:
                    async with session.get(url, timeout=5) as response:
                        if response.status == 200:
                            self.logger.info("健康检查通过")
                            return
except (ConnectionError, OSError, TimeoutError):

                await asyncio.sleep(2)

        raise RuntimeError("健康检查失败")

    async def _save_deployment_record(self, deployment: Deployment):
        """保存部署记录到数据库"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO deployments (
                        id, config_name, version, environment,
                        status, start_time, end_time,
                        commit_hash, message, error
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    deployment.id,
                    deployment.config_name,
                    deployment.version,
                    deployment.environment,
                    deployment.status,
                    deployment.start_time,
                    deployment.end_time,
                    deployment.commit_hash,
                    deployment.message,
                    deployment.error
                ))

                conn.commit()

        except Exception as e:
            self.logger.error(f"保存部署记录失败: {e}")

    def get_deployment(self, deploy_id: str) -> Deployment | None:
        """获取部署信息"""
        return self.deployments.get(deploy_id)

    def list_deployments(self, config_name: str = None,
                        limit: int = 10) -> List[Deployment]:
        """列出部署"""
        deployments = list(self.deployments.values())

        # 过滤
        if config_name:
            deployments = [d for d in deployments if d.config_name == config_name]

        # 排序（最新的在前）
        deployments.sort(key=lambda x: x.start_time, reverse=True)

        return deployments[:limit]

    def generate_deployment_report(self, deploy_id: str) -> str:
        """生成部署报告"""
        deployment = self.get_deployment(deploy_id)
        if not deployment:
            return f"部署 {deploy_id} 不存在"

        duration = ""
        if deployment.end_time:
            duration = str(deployment.end_time - deployment.start_time)

        status_icon = {
            'pending': '⏳',
            'deploying': '🔄',
            'success': '✅',
            'failed': '❌',
            'rolling_back': '↩️'
        }.get(deployment.status, '❓')

        report = [
            "=" * 60,
            f"📦 部署报告: {deployment.id}",
            "=" * 60,
            f"配置名称: {deployment.config_name}",
            f"版本: {deployment.version}",
            f"环境: {deployment.environment}",
            f"状态: {status_icon} {deployment.status}",
            f"开始时间: {deployment.start_time}",
            f"结束时间: {deployment.end_time or '进行中'}",
            f"持续时间: {duration}",
            f"提交哈希: {deployment.commit_hash or 'N/A'}",
            ""
        ]

        if deployment.message:
            report.extend(["消息:", deployment.message, ""])

        if deployment.error:
            report.extend(["错误信息:", deployment.error, ""])

        return "\n".join(report)


# 全局实例
deployment_manager = DeploymentManager()