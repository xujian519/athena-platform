#!/usr/bin/env python3
"""
Athena法律世界模型 - 数据备份和恢复工具
Legal World Model - Data Backup and Restore Utility

功能：
1. 备份三库数据（PostgreSQL、Neo4j、Qdrant）
2. 恢复三库数据
3. 数据迁移和导出

作者：Athena平台团队
版本：v1.0.0
"""

import argparse
import json
import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
BACKUP_DIR = PROJECT_ROOT / "backups" / "legal_world_model"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

# 数据库配置
POSTGRES_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "postgres",
    "password": "athena_dev_password_2024_secure",
    "database": "postgres"
}

NEO4J_CONFIG = {
    "uri": "bolt://localhost:7687",
    "user": "neo4j",
    "password": "athena_neo4j_2024"
}

QDRANT_CONFIG = {
    "url": "http://localhost:6333",
    "storage_path": PROJECT_ROOT / "data" / "qdrant" / "storage"
}


class DatabaseBackup:
    """数据库备份管理器"""

    def __init__(self, backup_name: str = None):
        """初始化备份管理器

        Args:
            backup_name: 备份名称，默认使用时间戳
        """
        self.backup_name = backup_name or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_path = BACKUP_DIR / self.backup_name
        self.backup_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"备份目录: {self.backup_path}")

    def backup_postgres(self):
        """备份PostgreSQL数据库"""
        logger.info("开始备份PostgreSQL...")

        backup_file = self.backup_path / "postgres_backup.sql"

        # 使用pg_dump备份
        cmd = [
            "pg_dump",
            f"--host={POSTGRES_CONFIG['host']}",
            f"--port={POSTGRES_CONFIG['port']}",
            f"--username={POSTGRES_CONFIG['user']}",
            "--database=postgres",
            "--no-password",
            "--format=plain",
            f"--file={backup_file}"
        ]

        env = os.environ.copy()
        env["PGPASSWORD"] = POSTGRES_CONFIG["password"]

        try:
            subprocess.run(cmd, env=env, check=True, capture_output=True)
            size = backup_file.stat().st_size / (1024 * 1024)  # MB
            logger.info(f"✅ PostgreSQL备份完成: {size:.2f} MB")
            return str(backup_file)
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ PostgreSQL备份失败: {e}")
            return None

    def backup_neo4j(self):
        """备份Neo4j数据库"""
        logger.info("开始备份Neo4j...")

        backup_dir = self.backup_path / "neo4j"
        backup_dir.mkdir(exist_ok=True)

        neo4j_data = Path("/opt/homebrew/var/neo4j/data")

        if not neo4j_data.exists():
            logger.warning(f"Neo4j数据目录不存在: {neo4j_data}")
            return None

        # 复制Neo4j数据目录
        try:
            # 使用rsync进行增量备份
            subprocess.run([
                "rsync", "-av",
                "--exclude=data/dbms/*.id",
                "--exclude=data/dbms/debug.log",
                f"{neo4j_data}/",
                f"{backup_dir}/"
            ], check=True)

            # 计算备份大小
            total_size = sum(
                f.stat().st_size for f in backup_dir.rglob('*') if f.is_file()
            ) / (1024 * 1024)  # MB

            logger.info(f"✅ Neo4j备份完成: {total_size:.2f} MB")
            return str(backup_dir)
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Neo4j备份失败: {e}")
            return None

    def backup_qdrant(self):
        """备份Qdrant数据库"""
        logger.info("开始备份Qdrant...")

        backup_dir = self.backup_path / "qdrant"
        backup_dir.mkdir(exist_ok=True)

        qdrant_storage = QDRANT_CONFIG["storage_path"]

        if not qdrant_storage.exists():
            logger.warning(f"Qdrant存储目录不存在: {qdrant_storage}")
            return None

        try:
            # 复制Qdrant存储目录
            subprocess.run([
                "rsync", "-av",
                f"{qdrant_storage}/",
                f"{backup_dir}/"
            ], check=True)

            # 计算备份大小
            total_size = sum(
                f.stat().st_size for f in backup_dir.rglob('*') if f.is_file()
            ) / (1024 * 1024)  # MB

            logger.info(f"✅ Qdrant备份完成: {total_size:.2f} MB")
            return str(backup_dir)
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Qdrant备份失败: {e}")
            return None

    def backup_all(self):
        """备份所有数据库"""
        logger.info("=" * 60)
        logger.info("开始备份所有数据库...")
        logger.info("=" * 60)

        results = {
            "timestamp": datetime.now().isoformat(),
            "backup_name": self.backup_name,
            "backup_path": str(self.backup_path),
            "databases": {}
        }

        # 备份PostgreSQL
        pg_result = self.backup_postgres()
        results["databases"]["postgres"] = {
            "status": "success" if pg_result else "failed",
            "path": pg_result
        }

        # 备份Neo4j
        neo4j_result = self.backup_neo4j()
        results["databases"]["neo4j"] = {
            "status": "success" if neo4j_result else "failed",
            "path": neo4j_result
        }

        # 备份Qdrant
        qdrant_result = self.backup_qdrant()
        results["databases"]["qdrant"] = {
            "status": "success" if qdrant_result else "failed",
            "path": qdrant_result
        }

        # 保存备份元数据
        metadata_file = self.backup_path / "backup_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        logger.info("=" * 60)
        logger.info("✅ 备份完成！")
        logger.info(f"备份位置: {self.backup_path}")
        logger.info(f"元数据: {metadata_file}")
        logger.info("=" * 60)

        return results


class DatabaseRestore:
    """数据库恢复管理器"""

    def __init__(self, backup_path: str):
        """初始化恢复管理器

        Args:
            backup_path: 备份目录路径
        """
        self.backup_path = Path(backup_path)

        if not self.backup_path.exists():
            raise ValueError(f"备份目录不存在: {backup_path}")

        # 加载备份元数据
        metadata_file = self.backup_path / "backup_metadata.json"
        if metadata_file.exists():
            with open(metadata_file, encoding='utf-8') as f:
                self.metadata = json.load(f)
            logger.info(f"加载备份元数据: {self.metadata.get('backup_name', 'unknown')}")
        else:
            self.metadata = None
            logger.warning("未找到备份元数据文件")

    def restore_postgres(self):
        """恢复PostgreSQL数据库"""
        logger.info("开始恢复PostgreSQL...")

        backup_file = self.backup_path / "postgres_backup.sql"

        if not backup_file.exists():
            logger.error(f"备份文件不存在: {backup_file}")
            return False

        # 使用psql恢复
        cmd = [
            "psql",
            f"--host={POSTGRES_CONFIG['host']}",
            f"--port={POSTGRES_CONFIG['port']}",
            f"--username={POSTGRES_CONFIG['user']}",
            "--database=postgres",
            f"--file={backup_file}"
        ]

        env = os.environ.copy()
        env["PGPASSWORD"] = POSTGRES_CONFIG["password"]

        try:
            subprocess.run(cmd, env=env, check=True, capture_output=True)
            logger.info("✅ PostgreSQL恢复完成")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ PostgreSQL恢复失败: {e}")
            return False

    def restore_neo4j(self):
        """恢复Neo4j数据库"""
        logger.info("开始恢复Neo4j...")

        backup_dir = self.backup_path / "neo4j"

        if not backup_dir.exists():
            logger.error(f"备份目录不存在: {backup_dir}")
            return False

        neo4j_data = Path("/opt/homebrew/var/neo4j/data")

        try:
            # 停止Neo4j
            logger.info("停止Neo4j服务...")
            subprocess.run(["neo4j", "stop"], check=True, capture_output=True)

            # 恢复数据
            logger.info("恢复Neo4j数据...")
            subprocess.run([
                "rsync", "-av",
                "--delete",
                f"{backup_dir}/",
                f"{neo4j_data}/"
            ], check=True)

            # 启动Neo4j
            logger.info("启动Neo4j服务...")
            subprocess.run(["neo4j", "start"], check=True, capture_output=True)

            logger.info("✅ Neo4j恢复完成")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Neo4j恢复失败: {e}")
            return False

    def restore_qdrant(self):
        """恢复Qdrant数据库"""
        logger.info("开始恢复Qdrant...")

        backup_dir = self.backup_path / "qdrant"

        if not backup_dir.exists():
            logger.error(f"备份目录不存在: {backup_dir}")
            return False

        qdrant_storage = QDRANT_CONFIG["storage_path"]

        try:
            # 停止Qdrant容器
            logger.info("停止Qdrant容器...")
            subprocess.run([
                "docker", "stop", "athena-qdrant-new"
            ], capture_output=True)
            subprocess.run([
                "docker", "rm", "athena-qdrant-new"
            ], capture_output=True)

            # 恢复数据
            logger.info("恢复Qdrant数据...")
            subprocess.run([
                "rsync", "-av",
                "--delete",
                f"{backup_dir}/",
                f"{qdrant_storage}/"
            ], check=True)

            # 启动Qdrant容器
            logger.info("启动Qdrant容器...")
            subprocess.run([
                "docker", "run", "-d",
                "--name", "athena-qdrant-new",
                "-p", "6333:6333", "-p", "6334:6334",
                "-v", f"{qdrant_storage}:/qdrant/storage:z",
                "-e", "QDRANT__SERVICE__HTTP_PORT=6333",
                "-e", "QDRANT__SERVICE__GRPC_PORT=6334",
                "--restart", "unless-stopped",
                "qdrant/qdrant:latest"
            ], check=True, capture_output=True)

            logger.info("✅ Qdrant恢复完成")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Qdrant恢复失败: {e}")
            return False

    def restore_all(self):
        """恢复所有数据库"""
        logger.info("=" * 60)
        logger.info("开始恢复所有数据库...")
        logger.info("=" * 60)

        results = {
            "timestamp": datetime.now().isoformat(),
            "backup_path": str(self.backup_path),
            "databases": {}
        }

        # 恢复PostgreSQL
        pg_result = self.restore_postgres()
        results["databases"]["postgres"] = {
            "status": "success" if pg_result else "failed"
        }

        # 恢复Neo4j
        neo4j_result = self.restore_neo4j()
        results["databases"]["neo4j"] = {
            "status": "success" if neo4j_result else "failed"
        }

        # 恢复Qdrant
        qdrant_result = self.restore_qdrant()
        results["databases"]["qdrant"] = {
            "status": "success" if qdrant_result else "failed"
        }

        logger.info("=" * 60)
        logger.info("✅ 恢复完成！")
        logger.info("=" * 60)

        return results


def list_backups():
    """列出所有备份"""
    logger.info("可用备份列表：")

    if not BACKUP_DIR.exists():
        logger.warning("备份目录不存在")
        return

    backups = sorted(BACKUP_DIR.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)

    if not backups:
        logger.warning("没有找到备份")
        return

    print(f"\n{'备份名称':<30} {'时间':<20} {'大小':>10}")
    print("-" * 60)

    for backup_dir in backups[:10]:  # 只显示最近10个
        metadata_file = backup_dir / "backup_metadata.json"
        if metadata_file.exists():
            with open(metadata_file, encoding='utf-8') as f:
                metadata = json.load(f)

            backup_name = metadata.get('backup_name', backup_dir.name)
            timestamp = metadata.get('timestamp', '')
            size_str = "N/A"

            # 计算备份大小
            total_size = sum(
                f.stat().st_size for f in backup_dir.rglob('*') if f.is_file()
            )
            if total_size > 1024 * 1024 * 1024:
                size_str = f"{total_size / (1024**3):.2f} GB"
            elif total_size > 1024 * 1024:
                size_str = f"{total_size / (1024**2):.2f} MB"
            else:
                size_str = f"{total_size / 1024:.2f} KB"

            print(f"{backup_name:<30} {timestamp[:19]:<20} {size_str:>10}")


def main():
    parser = argparse.ArgumentParser(description='Athena法律世界模型 - 数据备份和恢复工具')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # 备份命令
    backup_parser = subparsers.add_parser('backup', help='备份数据')
    backup_parser.add_argument('--name', '-n', help='备份名称（默认使用时间戳）')

    # 恢复命令
    restore_parser = subparsers.add_parser('restore', help='恢复数据')
    restore_parser.add_argument('backup_path', help='备份目录路径')

    # 列出备份命令
    subparsers.add_parser('list', help='列出所有备份')

    args = parser.parse_args()

    if args.command == 'backup':
        backup = DatabaseBackup(args.name)
        backup.backup_all()
    elif args.command == 'restore':
        restore = DatabaseRestore(args.backup_path)
        restore.restore_all()
    elif args.command == 'list':
        list_backups()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
