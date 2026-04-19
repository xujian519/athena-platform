#!/usr/bin/env python3
"""
Athena工作平台目录结构设置脚本
"""

from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def create_directory_structure() -> Any:
    """创建标准目录结构"""

    base_path = Path("/Users/xujian/Athena工作平台/production")

    # 目录结构定义
    directory_structure = {
        "data": {
            "raw": "原始数据",
            "processed": "处理后的数据",
            "cache": "缓存数据",
            "temp": "临时数据",
            "uploads": "上传数据",
            "exports": "导出数据"
        },
        "models": {
            "ai_models": "AI模型文件",
            "ml_models": "机器学习模型",
            "vector_models": "向量模型",
            "cache": "模型缓存"
        },
        "backups": {
            "daily": "每日备份",
            "weekly": "每周备份",
            "monthly": "每月备份",
            "config": "配置备份",
            "data": "数据备份"
        },
        "logs": {
            "archive": "归档日志",
            "errors": "错误日志",
            "access": "访问日志",
            "performance": "性能日志",
            "security": "安全日志"
        },
        "cache": {
            "redis": "Redis缓存",
            "modules/modules/memory/modules/memory/modules/memory/memory": "内存缓存",
            "disk": "磁盘缓存",
            "session": "会话缓存"
        },
        "dev/scripts": {
            "maintenance": "维护脚本",
            "backup": "备份脚本",
            "infrastructure/infrastructure/monitoring": "监控脚本",
            "infrastructure/infrastructure/deployment": "部署脚本",
            "migration": "迁移脚本"
        }
    }

    print("📁 创建Athena工作平台标准目录结构...")

    created_dirs = []

    for main_dir, subdirs in directory_structure.items():
        main_path = base_path / main_dir

        # 创建主目录
        main_path.mkdir(parents=True, exist_ok=True)
        created_dirs.append(str(main_path))

        # 创建子目录
        for subdir, description in subdirs.items():
            subdir_path = main_path / subdir
            subdir_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(subdir_path))

            # 创建目录说明文件
            readme_file = subdir_path / "README.md"
            if not readme_file.exists():
                readme_content = f"""# {subdir}

## 描述
{description}

## 用途
- 存放{description}
- 定期清理和维护
- 遵循命名规范

## 创建时间
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 维护者
小诺·双鱼公主 (平台总调度官)
"""
                with open(readme_file, 'w', encoding='utf-8') as f:
                    f.write(readme_content)

        print(f"✅ {main_dir}/ - {len(subdirs)} 个子目录")

    # 创建根级别说明文件
    structure_file = base_path / "DIRECTORY_STRUCTURE.md"
    structure_content = f"""# Athena工作平台目录结构

## 创建时间
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 目录说明

### 📁 data/ - 数据目录
- raw/: 原始数据
- processed/: 处理后的数据
- cache/: 缓存数据
- temp/: 临时数据
- uploads/: 上传数据
- exports/: 导出数据

### 🤖 models/ - 模型目录
- ai_models/: AI模型文件
- ml_models/: 机器学习模型
- vector_models/: 向量模型
- cache/: 模型缓存

### 💾 backups/ - 备份目录
- daily/: 每日备份
- weekly/: 每周备份
- monthly/: 每月备份
- config/: 配置备份
- data/: 数据备份

### 📝 logs/ - 日志目录
- archive/: 归档日志
- errors/: 错误日志
- access/: 访问日志
- performance/: 性能日志
- security/: 安全日志

### ⚡ cache/ - 缓存目录
- redis/: Redis缓存
- modules/memory/: 内存缓存
- disk/: 磁盘缓存
- session/: 会话缓存

### 🔧 dev/scripts/ - 脚本目录
- maintenance/: 维护脚本
- backup/: 备份脚本
- infrastructure/monitoring/: 监控脚本
- infrastructure/deployment/: 部署脚本
- migration/: 迁移脚本

## 维护者
小诺·双鱼公主 (平台总调度官)
"""
    with open(structure_file, 'w', encoding='utf-8') as f:
        f.write(structure_content)

    # 保存目录结构信息
    structure_info = {
        "created_at": datetime.now().isoformat(),
        "total_directories": len(created_dirs),
        "directory_list": created_dirs,
        "structure_definition": directory_structure
    }

    info_file = base_path / "directory_structure_info.json"
    with open(info_file, 'w', encoding='utf-8') as f:
        json.dump(structure_info, f, indent=2, ensure_ascii=False)

    print("\n🎯 目录结构创建完成！")
    print(f"📊 总计创建 {len(created_dirs)} 个目录")
    print("📄 结构说明文件: DIRECTORY_STRUCTURE.md")
    print("📋 结构信息文件: directory_structure_info.json")

    return created_dirs

def set_directory_permissions() -> None:
    """设置目录权限"""
    base_path = Path("/Users/xujian/Athena工作平台/production")

    print("\n🔒 设置目录权限...")

    # 设置标准权限
    for dirpath in base_path.rglob("*"):
        if dirpath.is_dir():
            # 目录权限：755
            dirpath.chmod(0o755)
        elif dirpath.is_file():
            # 文件权限：644
            dirpath.chmod(0o644)

    print("✅ 目录权限设置完成")

def main() -> None:
    """主函数"""
    print("🌸🐟 Athena工作平台目录结构设置器")
    print("=" * 60)

    # 创建目录结构
    created_dirs = create_directory_structure()

    # 设置权限
    set_directory_permissions()

    print("\n" + "=" * 60)
    print("✅ 目录结构设置完成！")
    print("💖 小诺已为您创建了完整的目录结构！")

if __name__ == "__main__":
    main()
