#!/usr/bin/env python3
"""
自动清理过期的归档文件

根据清理配置（cleanup_config.yaml）自动删除过期的归档目录。

Author: Athena平台团队
Created: 2026-04-23
"""

import yaml
from pathlib import Path
from datetime import datetime
import shutil
import sys
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config(config_path: Path) -> dict:
    """加载清理配置"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"配置文件未找到: {config_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        logger.error(f"配置文件解析失败: {e}")
        sys.exit(1)


def cleanup_archives(project_root: Path, config: dict, dry_run: bool = False) -> list:
    """
    根据清理配置自动删除过期归档

    Args:
        project_root: 项目根目录
        config: 清理配置字典
        dry_run: 是否仅模拟运行（不实际删除）

    Returns:
        清理的归档列表
    """
    today = datetime.now().date()
    cleaned_archives = []

    archive_policies = config.get("archive_policies", [])

    if not archive_policies:
        logger.info("没有找到归档清理策略")
        return cleaned_archives

    logger.info(f"开始检查归档清理策略（共{len(archive_policies)}个）")

    for policy in archive_policies:
        archive_path = project_root / policy["path"]

        # 检查归档是否存在
        if not archive_path.exists():
            logger.warning(f"归档不存在: {archive_path}")
            continue

        # 解析清理日期
        try:
            cleanup_date = datetime.strptime(
                policy["cleanup_date"], "%Y-%m-%d"
            ).date()
        except (ValueError, KeyError) as e:
            logger.error(f"无效的清理日期: {policy.get('cleanup_date')}, 错误: {e}")
            continue

        # 检查是否需要清理
        if today >= cleanup_date and policy.get("auto_cleanup", False):
            description = policy.get("description", "未知归档")

            if dry_run:
                logger.info(f"[模拟] 将清理归档: {archive_path} ({description})")
            else:
                logger.info(f"清理归档: {archive_path} ({description})")

                try:
                    # 记录到日志
                    log_cleanup(archive_path, description, policy)

                    # 删除归档目录
                    shutil.rmtree(archive_path)

                    logger.info(f"✅ 已清理: {description}")
                    cleaned_archives.append({
                        "path": str(archive_path),
                        "description": description,
                        "cleanup_date": policy["cleanup_date"]
                    })

                except Exception as e:
                    logger.error(f"清理失败: {archive_path}, 错误: {e}")
        else:
            days_until_cleanup = (cleanup_date - today).days
            logger.info(f"归档 {policy['description']} 将在 {days_until_cleanup} 天后清理")

    return cleaned_archives


def log_cleanup(archive_path: Path, description: str, policy: dict):
    """记录清理操作到日志文件"""
    log_file = Path("archive/cleanup.log")

    # 确保日志目录存在
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # 写入日志
    with open(log_file, 'a', encoding='utf-8') as log:
        log.write(f"{datetime.now().isoformat()}: 已清理 {description}\n")
        log.write(f"  路径: {archive_path}\n")
        log.write(f"  策略: {policy}\n")
        log.write(f"  文件数: {policy.get('file_count', 'N/A')}\n")
        log.write("-" * 80 + "\n")


def show_summary(cleaned_archives: list):
    """显示清理摘要"""
    if not cleaned_archives:
        logger.info("没有归档需要清理")
        return

    logger.info("=" * 80)
    logger.info("清理摘要")
    logger.info("=" * 80)
    logger.info(f"清理的归档数量: {len(cleaned_archives)}")

    for archive in cleaned_archives:
        logger.info(f"  - {archive['description']}")
        logger.info(f"    路径: {archive['path']}")
        logger.info(f"    清理日期: {archive['cleanup_date']}")

    logger.info("=" * 80)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="自动清理过期的归档文件")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="模拟运行，不实际删除文件"
    )
    parser.add_argument(
        "--config",
        default="scripts/cleanup_config.yaml",
        help="清理配置文件路径"
    )

    args = parser.parse_args()

    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    config_path = project_root / args.config

    logger.info(f"项目根目录: {project_root}")
    logger.info(f"配置文件: {config_path}")

    if args.dry_run:
        logger.info("⚠️  模拟运行模式，不会实际删除文件")

    # 加载配置
    config = load_config(config_path)

    # 执行清理
    cleaned_archives = cleanup_archives(
        project_root=project_root,
        config=config,
        dry_run=args.dry_run
    )

    # 显示摘要
    show_summary(cleaned_archives)

    return 0


if __name__ == "__main__":
    sys.exit(main())
