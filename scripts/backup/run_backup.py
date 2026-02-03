#!/usr/bin/env python3
"""
主备份协调器
Master Backup Coordinator

协调所有数据源的自动化备份。

作者: Athena平台团队
创建时间: 2026-02-03
版本: v1.0.0
"""

import asyncio
import gzip
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


class BackupCoordinator:
    """备份协调器"""

    def __init__(self, backup_root: str = "/backup/athena"):
        """
        初始化备份协调器

        Args:
            backup_root: 备份根目录
        """
        self.backup_root = Path(backup_root)
        self.backup_root.mkdir(parents=True, exist_ok=True)

        # 备份配置
        self.config = {
            "retention_days": 30,  # 保留30天
            "max_backups": 10,  # 最多保留10个完整备份
        }

    async def backup_all(self) -> dict[str, Any]:
        """
        执行所有备份任务

        Returns:
            备份结果汇总
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results = {}

        print(f"🔄 开始备份流程 - {timestamp}")

        # 1. PostgreSQL备份
        print("\n【1/6】备份PostgreSQL...")
        results["postgres"] = await self._backup_postgres(timestamp)

        # 2. Neo4j备份
        print("\n【2/6】备份Neo4j...")
        results["neo4j"] = await self._backup_neo4j(timestamp)

        # 3. Qdrant备份
        print("\n【3/6】备份Qdrant...")
        results["qdrant"] = await self._backup_qdrant(timestamp)

        # 4. Redis备份
        print("\n【4/6】备份Redis...")
        results["redis"] = await self._backup_redis(timestamp)

        # 5. 配置文件备份
        print("\n【5/6】备份配置文件...")
        results["config"] = await self._backup_config(timestamp)

        # 6. 清理旧备份
        print("\n【6/6】清理旧备份...")
        results["cleanup"] = await self._cleanup_old_backups()

        # 汇总报告
        print("\n" + "=" * 60)
        print("备份完成报告")
        print("=" * 60)

        for name, result in results.items():
            status = "✅" if result.get("success") else "❌"
            print(f"{status} {name}: {result.get('message', '未知')}")

        return results

    async def _backup_postgres(self, timestamp: str) -> dict[str, Any]:
        """备份PostgreSQL数据库"""
        try:
            load_dotenv()

            # 备份目录
            backup_dir = self.backup_root / "postgres" / timestamp
            backup_dir.mkdir(parents=True, exist_ok=True)

            # 使用pg_dump备份
            env = os.environ.copy()
            env["PGPASSWORD"] = os.getenv("DB_PASSWORD", "")

            dump_file = backup_dir / "athena_dump.sql"

            cmd = [
                "pg_dump",
                "-h", os.getenv("DB_HOST", "localhost"),
                "-p", os.getenv("DB_PORT", "5432"),
                "-U", os.getenv("DB_USER", "postgres"),
                "-d", os.getenv("DB_NAME", "athena"),
                "-f", str(dump_file),
                "-F", "c",  # 自定义格式
            ]

            result = subprocess.run(cmd, env=env, capture_output=True, text=True)

            if result.returncode == 0:
                # 压缩备份文件
                with open(dump_file, "rb") as f_in:
                    with gzip.open(f"{dump_file}.gz", "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)

                os.remove(dump_file)

                size = os.path.getsize(f"{dump_file}.gz")

                return {
                    "success": True,
                    "message": f"备份成功 ({size/1024/1024:.2f} MB)",
                    "path": str(backup_dir),
                }
            else:
                return {
                    "success": False,
                    "message": f"备份失败: {result.stderr}",
                }

        except Exception as e:
            return {"success": False, "message": str(e)}

    async def _backup_neo4j(self, timestamp: str) -> dict[str, Any]:
        """备份Neo4j数据库"""
        try:
            # Neo4j数据已经在data/neo4j目录
            neo4j_data = Path("/Users/xujian/Athena工作平台/data/neo4j")

            if not neo4j_data.exists():
                return {"success": False, "message": "Neo4j数据目录不存在"}

            backup_dir = self.backup_root / "neo4j" / timestamp
            backup_dir.mkdir(parents=True, exist_ok=True)

            # 使用rsync进行增量备份
            result = subprocess.run(
                ["rsync", "-av", "--progress", f"{neo4j_data}/", f"{backup_dir}/"],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                return {
                    "success": True,
                    "message": "备份成功",
                    "path": str(backup_dir),
                }
            else:
                return {
                    "success": False,
                    "message": f"备份失败: {result.stderr}",
                }

        except Exception as e:
            return {"success": False, "message": str(e)}

    async def _backup_qdrant(self, timestamp: str) -> dict[str, Any]:
        """备份Qdrant向量数据"""
        try:
            qdrant_data = Path("/Users/xujian/Athena工作平台/data/qdrant")

            if not qdrant_data.exists():
                return {"success": False, "message": "Qdrant数据目录不存在"}

            backup_dir = self.backup_root / "qdrant" / timestamp
            backup_dir.mkdir(parents=True, exist_ok=True)

            result = subprocess.run(
                ["rsync", "-av", "--progress", f"{qdrant_data}/", f"{backup_dir}/"],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                return {
                    "success": True,
                    "message": "备份成功",
                    "path": str(backup_dir),
                }
            else:
                return {
                    "success": False,
                    "message": f"备份失败: {result.stderr}",
                }

        except Exception as e:
            return {"success": False, "message": str(e)}

    async def _backup_redis(self, timestamp: str) -> dict[str, Any]:
        """备份Redis数据"""
        try:
            import redis

            # 连接Redis
            r = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", 6379)),
                password=os.getenv("REDIS_PASSWORD", ""),
                decode_responses=False,
            )

            # 触发保存
            r.save()

            # 使用redis导出功能
            backup_dir = self.backup_root / "redis" / timestamp
            backup_dir.mkdir(parents=True, exist_ok=True)

            dump_file = backup_dir / "dump.rdb"

            # 复制dump文件
            redis_dump = Path("/Users/xujian/Athena工作平台/data/redis/dump.rdb")
            if redis_dump.exists():
                shutil.copy2(redis_dump, dump_file)

                return {
                    "success": True,
                    "message": f"备份成功 ({os.path.getsize(dump_file)/1024:.2f} KB)",
                    "path": str(backup_dir),
                }
            else:
                return {
                    "success": True,
                    "message": "无持久化数据（跳过）",
                    "path": str(backup_dir),
                }

        except Exception as e:
            return {"success": False, "message": str(e)}

    async def _backup_config(self, timestamp: str) -> dict[str, Any]:
        """备份配置文件"""
        try:
            backup_dir = self.backup_root / "config" / timestamp
            backup_dir.mkdir(parents=True, exist_ok=True)

            # 备份关键配置文件
            config_files = [
                ".env",
                "config/database.yaml",
                "docker-compose.yml",
            ]

            for config_file in config_files:
                source = Path("/Users/xujian/Athena工作平台") / config_file
                if source.exists():
                    dest = backup_dir / config_file
                    shutil.copy2(source, dest)

            return {
                "success": True,
                "message": f"备份 {len(config_files)} 个配置文件",
                "path": str(backup_dir),
            }

        except Exception as e:
            return {"success": False, "message": str(e)}

    async def _cleanup_old_backups(self) -> dict[str, Any]:
        """清理旧备份"""
        try:
            import time

            cutoff_time = time.time() - (self.config["retention_days"] * 86400)

            deleted_count = 0

            for backup_type in ["postgres", "neo4j", "qdrant", "redis", "config"]:
                type_dir = self.backup_root / backup_type
                if not type_dir.exists():
                    continue

                for backup_dir in type_dir.iterdir():
                    if backup_dir.is_dir():
                        # 检查目录修改时间
                        mtime = backup_dir.stat().st_mtime

                        if mtime < cutoff_time:
                            # 删除旧备份
                            shutil.rmtree(backup_dir)
                            deleted_count += 1

            return {
                "success": True,
                "message": f"清理了 {deleted_count} 个过期备份",
            }

        except Exception as e:
            return {"success": False, "message": str(e)}


# 便捷函数
async def run_backup() -> dict[str, Any]:
    """运行备份（便捷函数）"""
    coordinator = BackupCoordinator()
    return await coordinator.backup_all()


if __name__ == "__main__":
    import sys

    print("=" * 80)
    print("Athena自动化备份系统")
    print("=" * 80)
    print()

    result = asyncio.run(run_backup())

    print()
    if all(r.get("success") for r in result.values()):
        print("🎉 所有备份任务成功完成！")
        sys.exit(0)
    else:
        print("⚠️  部分备份任务失败，请检查日志")
        sys.exit(1)
