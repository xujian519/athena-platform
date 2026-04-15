#!/usr/bin/env python3
"""
宝宸知识库同步 CLI 工具
Bao Chen Knowledge Base Sync CLI

用法:
    python scripts/sync_baochen_kb.py full-rebuild    # 全量重建
    python scripts/sync_baochen_kb.py sync             # 增量同步
    python scripts/sync_baochen_kb.py status           # 查看状态
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

# 添加项目根目录到 sys.path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("baochen_sync")


async def cmd_full_rebuild(args: argparse.Namespace) -> None:
    """执行全量重建"""
    from core.knowledge_sync.sync_manager import BaoChenSyncManager

    manager = BaoChenSyncManager(
        wiki_path=args.wiki_path,
        qdrant_url=args.qdrant_url,
    )

    logger.info("=" * 60)
    logger.info("开始全量重建")
    logger.info(f"Wiki 路径: {args.wiki_path}")
    logger.info(f"Qdrant: {args.qdrant_url}")
    logger.info("=" * 60)

    result = await manager.full_rebuild()

    logger.info("=" * 60)
    logger.info("全量重建完成")
    logger.info(f"文件数: {result.get('total_files', 0)}")
    logger.info(f"分块数: {result.get('total_chunks', 0)}")
    logger.info(f"写入数: {result.get('total_written', 0)}")
    logger.info(f"耗时: {result.get('elapsed_seconds', 0)}s")
    if "kb_counts" in result:
        logger.info("分类分布:")
        for kb, count in sorted(result["kb_counts"].items(), key=lambda x: -x[1]):
            logger.info(f"  {kb}: {count}")
    logger.info("=" * 60)


async def cmd_sync(args: argparse.Namespace) -> None:
    """执行增量同步"""
    from core.knowledge_sync.sync_manager import BaoChenSyncManager

    manager = BaoChenSyncManager(
        wiki_path=args.wiki_path,
        qdrant_url=args.qdrant_url,
    )

    logger.info("开始增量同步...")
    result = await manager.incremental_sync()

    if result.get("sync_type") == "no_changes":
        logger.info("无变更，同步跳过")
    else:
        logger.info(f"同步完成: +{result.get('added', 0)} 新增, "
                     f"~{result.get('modified', 0)} 修改, "
                     f"-{result.get('deleted', 0)} 删除, "
                     f"耗时 {result.get('elapsed_seconds', 0)}s")


async def cmd_status(args: argparse.Namespace) -> None:
    """显示同步状态"""
    from core.knowledge_sync.sync_manager import BaoChenSyncManager

    manager = BaoChenSyncManager(
        wiki_path=args.wiki_path,
        qdrant_url=args.qdrant_url,
    )

    status = manager.status()

    print("\n" + "=" * 60)
    print("宝宸知识库同步状态")
    print("=" * 60)
    print(f"Wiki 路径:     {status['wiki_path']}")
    print(f"Wiki 可用:     {'是' if status['wiki_exists'] else '否'}")
    print(f"上次同步:     {status['last_sync']}")
    print(f"源文件数:     {status['total_files']}")
    print(f"总 chunk 数:  {status['total_chunks']}")
    print(f"Qdrant 点数:  {status['qdrant_points']}")
    print()

    if status["category_distribution"]:
        print("分类分布:")
        for cat, count in sorted(
            status["category_distribution"].items(), key=lambda x: -x[1]
        ):
            print(f"  {cat}: {count}")
    else:
        print("Qdrant 中暂无数据")
    print("=" * 60)


async def cmd_validate(args: argparse.Namespace) -> None:
    """验证数据一致性"""
    from core.knowledge_sync.sync_manager import BaoChenSyncManager

    manager = BaoChenSyncManager(
        wiki_path=args.wiki_path,
        qdrant_url=args.qdrant_url,
    )

    logger.info("开始数据验证...")
    result = await manager.validate()

    status_icon = {"healthy": "✅", "warning": "⚠️", "error": "❌"}.get(
        result.get("status", "error"), "?"
    )
    print(f"\n{status_icon} 验证结果: {result.get('status', 'unknown')}")
    print(f"   {result.get('message', '')}")

    if result.get("issues"):
        print("\n发现的问题:")
        for issue in result["issues"]:
            print(f"  - {issue}")

    if result.get("category_distribution"):
        print("\n分类分布:")
        for cat, count in sorted(
            result["category_distribution"].items(), key=lambda x: -x[1]
        ):
            print(f"  {cat}: {count}")

    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="宝宸知识库同步工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python scripts/sync_baochen_kb.py full-rebuild
  python scripts/sync_baochen_kb.py sync
  python scripts/sync_baochen_kb.py status
        """,
    )

    parser.add_argument(
        "--wiki-path",
        default="/Users/xujian/projects/宝宸知识库/Wiki",
        help="Wiki 目录路径",
    )
    parser.add_argument(
        "--qdrant-url",
        default="http://localhost:6333",
        help="Qdrant 服务地址",
    )

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    subparsers.add_parser("full-rebuild", help="全量重建（清空后重新导入所有文件）")
    subparsers.add_parser("sync", help="增量同步（仅处理变更文件）")
    subparsers.add_parser("status", help="查看同步状态")
    subparsers.add_parser("validate", help="验证数据一致性")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # 根据命令分发
    commands = {
        "full-rebuild": cmd_full_rebuild,
        "sync": cmd_sync,
        "status": cmd_status,
        "validate": cmd_validate,
    }

    asyncio.run(commands[args.command](args))


if __name__ == "__main__":
    main()
