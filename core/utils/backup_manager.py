#!/usr/bin/env python3
"""
Athena工作平台 统一备份管理器
Unified Backup Manager

功能:
- 自动检测移动硬盘
- 默认备份到移动硬盘
- 支持模型、数据库、代码备份
- 自动清理旧备份
"""

import logging
import shutil
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml

from core.logging_config import setup_logging

logger = setup_logging()


class BackupManager:
    """统一备份管理器"""

    def __init__(self, config_path: str | None = None):
        """
        初始化备份管理器

        Args:
            config_path: 配置文件路径
        """
        if config_path is None:
            config_path = "/Users/xujian/Athena工作平台/config/backup_config.yaml"

        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.backup_root = Path(self.config["backup_root"])

    def _load_config(self) -> Any:
        """加载配置文件"""
        try:
            with open(self.config_path, encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"配置文件加载失败,使用默认配置: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Any:
        """获取默认配置"""
        return {
            "backup_root": "/Volumes/AthenaData/Athena工作平台_Backups",
            "backup_strategy": {"keep_recent": 5, "compress_old": True, "compress_after_days": 7},
            "external_disk": {"disk_name": "AthenaData", "mount_path": "/Volumes/AthenaData"},
        }

    def check_external_disk(self) -> bool:
        """
        检查移动硬盘是否挂载

        Returns:
            是否已挂载
        """
        mount_path = Path(self.config["external_disk"]["mount_path"])
        return mount_path.exists() and mount_path.is_dir()

    def get_backup_path(self, backup_type: str = "general", create: bool = True) -> Path:
        """
        获取备份路径

        Args:
            backup_type: 备份类型 (models/database/code/configs/logs/general)
            create: 是否创建目录

        Returns:
            备份目录路径
        """
        # 检查移动硬盘
        if not self.check_external_disk():
            logger.warning("⚠️ 移动硬盘未挂载,备份将失败")
            return None

        # 构建备份路径
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_root / f"{backup_type}_{timestamp}"

        if create and not backup_path.exists():
            backup_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ 创建备份目录: {backup_path}")

        return backup_path

    def backup_directory(self, source_dir: Path, backup_type: str = "general") -> bool:
        """
        备份目录

        Args:
            source_dir: 源目录路径
            backup_type: 备份类型

        Returns:
            是否成功
        """
        if not source_dir.exists():
            logger.error(f"源目录不存在: {source_dir}")
            return False

        # 获取备份路径
        backup_path = self.get_backup_path(backup_type)
        if backup_path is None:
            return False

        # 执行备份
        logger.info(f"📦 备份: {source_dir.name}")
        logger.info(f"   源: {source_dir}")
        logger.info(f"   目标: {backup_path}")

        try:
            # 使用 rsync 进行备份
            subprocess.run(
                ["rsync", "-avh", "--progress", f"{source_dir}/", f"{backup_path}/"], check=True
            )
            logger.info("✅ 备份成功")
            return True
        except Exception as e:
            logger.error(f"❌ 备份失败: {e}")
            return False

    def backup_file(self, source_file: Path, backup_type: str = "general") -> bool:
        """
        备份单个文件

        Args:
            source_file: 源文件路径
            backup_type: 备份类型

        Returns:
            是否成功
        """
        if not source_file.exists():
            logger.error(f"源文件不存在: {source_file}")
            return False

        # 获取备份路径
        backup_path = self.get_backup_path(backup_type)
        if backup_path is None:
            return False

        # 执行备份
        try:
            target_file = backup_path / source_file.name
            shutil.copy2(source_file, target_file)
            logger.info(f"✅ 文件备份成功: {source_file.name}")
            return True
        except Exception as e:
            logger.error(f"❌ 文件备份失败: {e}")
            return False

    def cleanup_old_backups(self, backup_type: str | None = None, keep: int | None = None) -> Any:
        """
        清理旧备份

        Args:
            backup_type: 备份类型,None表示所有类型
            keep: 保留数量,None表示使用配置文件中的值
        """
        if keep is None:
            keep = self.config["backup_strategy"]["keep_recent"]

        # 获取备份目录列表
        if backup_type:
            backup_dirs = list(self.backup_root.glob(f"{backup_type}_*"))
        else:
            backup_dirs = list(self.backup_root.glob("*"))

        # 按时间排序(旧到新)
        backup_dirs.sort(key=lambda x: x.stat().st_mtime)

        # 删除旧备份
        removed_count = 0
        for backup_dir in backup_dirs[:-keep]:
            try:
                shutil.rmtree(backup_dir)
                logger.info(f"🗑️ 删除旧备份: {backup_dir.name}")
                removed_count += 1
            except Exception as e:
                logger.error(f"❌ 删除失败: {backup_dir.name} - {e}")

        if removed_count > 0:
            logger.info(f"✅ 清理完成,删除了 {removed_count} 个旧备份")

    def get_backup_info(self) -> dict:
        """
        获取备份信息

        Returns:
            备份信息字典
        """
        info = {
            "external_disk_mounted": self.check_external_disk(),
            "backup_root": str(self.backup_root),
            "backup_root_exists": self.backup_root.exists(),
            "backups": [],
        }

        if self.backup_root.exists():
            for backup_dir in self.backup_root.iterdir():
                if backup_dir.is_dir():
                    size = sum(f.stat().st_size for f in backup_dir.rglob("*") if f.is_file())
                    mtime = datetime.fromtimestamp(backup_dir.stat().st_mtime)

                    info["backups"].append(
                        {
                            "name": backup_dir.name,
                            "size_mb": size / (1024**2),
                            "modified_time": mtime,
                        }
                    )

            # 按时间排序
            info["backups"].sort(key=lambda x: x["modified_time"], reverse=True)

        return info

    def print_backup_summary(self) -> Any:
        """打印备份摘要"""
        info = self.get_backup_info()

        print("\n" + "=" * 70)
        print("📊 Athena 备份系统状态")
        print("=" * 70)
        print(f"移动硬盘: {'✅ 已挂载' if info['external_disk_mounted'] else '❌ 未挂载'}")
        print(f"备份根目录: {info['backup_root']}")
        print(f"备份数量: {len(info['backups'])}")

        if info["backups"]:
            print("\n最近的备份:")
            for backup in info["backups"][:5]:
                print(f"  - {backup['name']}")
                print(f"    大小: {backup['size_mb']:.2f} MB")
                print(f"    时间: {backup['modified_time'].strftime('%Y-%m-%d %H:%M:%S')}")

        print("=" * 70 + "\n")


# 全局单例
_backup_manager = None


def get_backup_manager() -> BackupManager:
    """获取备份管理器单例"""
    global _backup_manager
    if _backup_manager is None:
        _backup_manager = BackupManager()
    return _backup_manager


if __name__ == "__main__":
    # 测试备份管理器
    logging.basicConfig(level=logging.INFO)
    manager = get_backup_manager()
    manager.print_backup_summary()
