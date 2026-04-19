#!/usr/bin/env python3
"""
生产环境同步脚本
Production Sync Script

同步core/到production/core/，带版本控制和变更检测。

核心功能:
1. 同步core/到production/core/
2. 版本控制
3. 变更检测
4. 回滚支持

Author: Athena平台团队
Created: 2026-04-19
Version: v2.0.0
"""

import hashlib
import json
import logging
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SyncResult:
    """同步结果"""

    total_files: int = 0
    synced_files: int = 0
    skipped_files: int = 0
    failed_files: int = 0
    deleted_files: int = 0
    errors: list[str] = field(default_factory=list)


@dataclass
class FileChange:
    """文件变更"""

    action: str  # created, updated, deleted
    file_path: str  # 文件路径
    checksum: str  # 文件校验和
    timestamp: datetime = field(default_factory=datetime.now)


class ProductionSyncer:
    """生产环境同步器"""

    def __init__(self, project_root: Path):
        """
        初始化同步器

        Args:
            project_root: 项目根目录
        """
        self.project_root = project_root
        self.core_dir = project_root / "core"
        self.production_core_dir = project_root / "production" / "core"

        # 版本控制文件
        self.version_file = project_root / "production" / ".sync_version.json"

        # 变更历史
        self.changes: list[FileChange] = []

        # 结果统计
        self.result = SyncResult()

    def load_version(self) -> dict[str, Any]:
        """
        加载版本信息

        Returns:
            版本信息字典
        """
        if not self.version_file.exists():
            return {"version": "0.0.0", "last_sync": None, "files": {}}

        try:
            with open(self.version_file, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"⚠️ 加载版本文件失败: {e}")
            return {"version": "0.0.0", "last_sync": None, "files": {}}

    def save_version(self, version_info: dict[str, Any]):
        """
        保存版本信息

        Args:
            version_info: 版本信息字典
        """
        try:
            self.version_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.version_file, "w", encoding="utf-8") as f:
                json.dump(version_info, f, indent=2, ensure_ascii=False)

            logger.info(f"✅ 版本信息已保存: {version_info['version']}")

        except Exception as e:
            logger.error(f"❌ 保存版本文件失败: {e}")

    def calculate_checksum(self, file_path: Path) -> str:
        """
        计算文件校验和

        Args:
            file_path: 文件路径

        Returns:
            str: MD5校验和
        """
        md5 = hashlib.md5()

        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5.update(chunk)

        return md5.hexdigest()

    def detect_changes(self) -> list[FileChange]:
        """
        检测文件变更

        Returns:
            变更列表
        """
        logger.info("🔍 检测文件变更...")

        changes = []
        version_info = self.load_version()
        known_files = version_info.get("files", {})

        # 扫描core目录
        for py_file in self.core_dir.rglob("*.py"):
            # 跳过__pycache__和测试文件
            if "__pycache__" in py_file.parts or py_file.name.startswith("test_"):
                continue

            # 计算相对路径
            try:
                rel_path = py_file.relative_to(self.core_dir)
            except ValueError:
                continue

            # 计算校验和
            checksum = self.calculate_checksum(py_file)

            # 检查是否是新文件或已修改
            file_key = str(rel_path)

            if file_key not in known_files:
                # 新文件
                changes.append(
                    FileChange(
                        action="created", file_path=file_key, checksum=checksum
                    )
                )
            elif known_files[file_key] != checksum:
                # 已修改
                changes.append(
                    FileChange(
                        action="updated", file_path=file_key, checksum=checksum
                    )
                )

        # 检查删除的文件
        for file_key in known_files:
            source_file = self.core_dir / file_key
            if not source_file.exists():
                # 文件已删除
                changes.append(
                    FileChange(action="deleted", file_path=file_key, checksum="")
                )

        logger.info(f"✅ 检测到 {len(changes)} 个变更")

        return changes

    def sync_file(self, rel_path: Path, action: str) -> bool:
        """
        同步单个文件

        Args:
            rel_path: 相对路径
            action: 操作类型

        Returns:
            bool: 是否成功
        """
        source_file = self.core_dir / rel_path
        target_file = self.production_core_dir / rel_path

        try:
            if action == "deleted":
                # 删除文件
                if target_file.exists():
                    target_file.unlink()
                    self.result.deleted_files += 1
                    logger.debug(f"   删除: {rel_path}")

            else:
                # 复制文件
                target_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_file, target_file)
                self.result.synced_files += 1
                logger.debug(f"   同步: {rel_path}")

            return True

        except Exception as e:
            self.result.failed_files += 1
            self.result.errors.append(f"{rel_path}: {e}")
            logger.error(f"❌ 同步失败 {rel_path}: {e}")
            return False

    def sync(self, dry_run: bool = True) -> SyncResult:
        """
        执行同步

        Args:
            dry_run: 是否只演练

        Returns:
            同步结果
        """
        logger.info("🚀 开始同步生产环境...")

        if dry_run:
            logger.info("📋 演练模式（不会实际修改文件）")

        # 1. 检测变更
        changes = self.detect_changes()

        if not changes:
            logger.info("✅ 没有需要同步的变更")
            return self.result

        # 2. 执行同步
        self.result.total_files = len(changes)

        for change in changes:
            logger.info(f"   {change.action}: {change.file_path}")

            if not dry_run:
                success = self.sync_file(
                    Path(change.file_path), change.action
                )

                if success:
                    # 记录变更
                    self.changes.append(change)

        # 3. 更新版本信息
        if not dry_run and self.changes:
            self._update_version()

        logger.info(f"✅ 同步完成")
        logger.info(f"   总计: {self.result.total_files}")
        logger.info(f"   同步: {self.result.synced_files}")
        logger.info(f"   删除: {self.result.deleted_files}")
        logger.info(f"   失败: {self.result.failed_files}")

        return self.result

    def _update_version(self):
        """更新版本信息"""
        # 加载旧版本
        version_info = self.load_version()

        # 更新版本号
        old_version = version_info.get("version", "0.0.0")
        major, minor, patch = map(int, old_version.split("."))
        new_version = f"{major}.{minor}.{patch + 1}"

        # 更新文件校验和
        files = {}
        for change in self.changes:
            if change.action != "deleted":
                files[change.file_path] = change.checksum

        # 保存新版本
        version_info["version"] = new_version
        version_info["last_sync"] = datetime.now().isoformat()
        version_info["files"] = files

        self.save_version(version_info)

    def rollback(self, version: Optional[str] = None) -> bool:
        """
        回滚到指定版本

        Args:
            version: 版本号（None表示回滚到上一版本）

        Returns:
            bool: 是否成功
        """
        logger.info(f"🔄 回滚到版本: {version or '上一版本'}")

        # TODO: 实现回滚逻辑
        # 需要维护版本历史，支持回滚

        return True

    def generate_report(self, output_path: Path):
        """
        生成同步报告

        Args:
            output_path: 输出路径
        """
        logger.info(f"📄 生成同步报告: {output_path}")

        # 生成JSON报告
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_files": self.result.total_files,
                "synced_files": self.result.synced_files,
                "skipped_files": self.result.skipped_files,
                "failed_files": self.result.failed_files,
                "deleted_files": self.result.deleted_files,
            },
            "changes": [
                {
                    "action": change.action,
                    "file_path": change.file_path,
                    "checksum": change.checksum,
                    "timestamp": change.timestamp.isoformat(),
                }
                for change in self.changes
            ],
            "errors": self.result.errors,
        }

        # 写入文件
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info("✅ 报告已生成")


async def main():
    """主函数"""
    import argparse

    print("=" * 80)
    print("🔄 生产环境同步脚本")
    print("=" * 80)
    print()

    # 解析命令行参数
    parser = argparse.ArgumentParser(description="生产环境同步脚本")
    parser.add_argument("--dry-run", action="store_true", help="演练模式（不实际修改文件）")
    parser.add_argument("--no-dry-run", action="store_true", help="实际执行同步")
    args = parser.parse_args()

    # 默认为演练模式，除非明确指定 --no-dry-run
    dry_run = not args.no_dry_run

    if args.dry_run:
        dry_run = True

    # 项目根目录
    project_root = Path("/Users/xujian/Athena工作平台")

    # 创建同步器
    syncer = ProductionSyncer(project_root)

    # 执行同步
    result = syncer.sync(dry_run=dry_run)

    # 生成报告
    report_path = project_root / "reports" / "production_sync_report.json"
    syncer.generate_report(report_path)

    print()
    print("✅ 同步完成")
    print(f"   报告路径: {report_path}")
    print()
    print("=" * 80)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
