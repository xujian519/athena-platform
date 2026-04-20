#!/usr/bin/env python3
"""
权限配置迁移脚本

从旧版权限配置迁移到新版配置格式。

作者: Athena平台团队
创建时间: 2026-04-20
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def migrate_permissions(
    input_path: str,
    output_path: str,
    mode: str = "default",
) -> None:
    """迁移权限配置

    Args:
        input_path: 旧配置文件路径
        output_path: 新配置文件路径
        mode: 权限模式（default/auto/plan/bypass）
    """
    import yaml

    input_file = Path(input_path)
    output_file = Path(output_path)

    if not input_file.exists():
        logger.error(f"❌ 输入文件不存在: {input_path}")
        return

    # 读取旧配置
    logger.info(f"📥 读取旧配置: {input_path}")
    with open(input_file, "r", encoding="utf-8") as f:
        old_config = yaml.safe_load(f) or {}

    # 构建新配置
    new_config = {
        "mode": mode,
        "path_rules": [],
        "denied_commands": [
            "rm -rf /",
            "DROP TABLE *",
            "shutdown -h now",
        ],
    }

    # 迁移路径规则（如果有）
    if "path_rules" in old_config:
        new_config["path_rules"] = old_config["path_rules"]
    else:
        # 使用默认路径规则
        new_config["path_rules"] = [
            {
                "rule_id": "project-dir",
                "pattern": "/Users/xujian/Athena工作平台/**",
                "allow": True,
                "priority": 50,
                "reason": "项目目录允许访问",
                "enabled": True,
            },
            {
                "rule_id": "system-dir",
                "pattern": "/etc/**",
                "allow": False,
                "priority": 100,
                "reason": "系统目录禁止访问",
                "enabled": True,
            },
            {
                "rule_id": "temp-dir",
                "pattern": "/tmp/**",
                "allow": True,
                "priority": 10,
                "reason": "临时目录允许访问",
                "enabled": True,
            },
        ]

    # 迁移命令黑名单（如果有）
    if "denied_commands" in old_config:
        new_config["denied_commands"] = old_config["denied_commands"]

    # 写入新配置
    logger.info(f"💾 写入新配置: {output_path}")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        yaml.dump(new_config, f, allow_unicode=True, default_flow_style=False)

    logger.info(f"✅ 迁移完成！")
    logger.info(f"   新配置文件: {output_path}")
    logger.info(f"   权限模式: {mode}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="迁移权限配置从旧格式到新格式"
    )
    parser.add_argument(
        "-i",
        "--input",
        default="config/permissions.yaml",
        help="旧配置文件路径（默认: config/permissions.yaml）",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="config/permissions_v2.yaml",
        help="新配置文件路径（默认: config/permissions_v2.yaml）",
    )
    parser.add_argument(
        "-m",
        "--mode",
        default="default",
        choices=["default", "auto", "plan", "bypass"],
        help="权限模式（默认: default）",
    )

    args = parser.parse_args()

    migrate_permissions(args.input, args.output, args.mode)


if __name__ == "__main__":
    main()
