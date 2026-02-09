#!/usr/bin/env python3
"""
小诺目录清理脚本
Xiaonuo Directory Cleanup Script

清理xiaonuo/目录下的重复文件，保留核心文件，归档旧版本
"""

import os
import shutil
from pathlib import Path

# 定义归档目录
ARCHIVE_DIR = Path(__file__).parent / "archive_cleanup_20250209"

# 定义要归档的文件分类
FILES_TO_ARCHIVE = {
    "old_agent_versions": [
        "xiaonuo_integrated.py",
        "xiaonuo_final_optimized.py",
        "xiaonuo_v2_complete.py",
        "xiaonuo_with_enhanced_memory.py",
        "xiaonuo_with_reflection_engine.py",
        "xiaonuo_integrated_reflection_system.py",
        "xiaonuo_enhanced_memory_system.py",
        "xiaonuo_enhanced_planning_system.py",
    ],
    "analysis_tools": [
        "xiaonuo_capabilities_analysis.py",
        "xiaonuo_core_modules_analysis.py",
        "xiaonuo_modules_comparison_analysis.py",
        "xiaonuo_planner_analysis.py",
        "xiaonuo_reasoning_engines_analysis.py",
        "xiaonuo_complete_capabilities.py",
    ],
    "startup_scripts": [
        "start_xiaonuo_complete.py",
        "start_xiaonuo_final.py",
        "xiaonuo_interactive.py",
        "start_xiaona_patent_search.py",
    ],
    "utility_scripts": [
        "xiaonuo_ai_processor_interface.py",
        "xiaonuo_file_system_control.py",
        "xiaonuo_unified_memory_manager.py",
        "xiaonuo_simplified_xiaona.py",
        "xiaonuo_simple_reflection_demo.py",
    ],
    "patent_search_scripts": [
        "comprehensive_patent_search.py",
        "found_su_patents.py",
        "search_large_patent_db.py",
        "search_real_database.py",
        "search_su_dongxia_patents.py",
    ],
    "test_files": [
        "test_xiaonuo_reflection.py",
        "show_xiaonuo_identity.py",
    ],
    "old_configs": [
        "xiaonuo_identity_20251217_081501.json",
        "xiaonuo_identity_20251218_083213.json",
    ],
}

# 定义要保留的文件
FILES_TO_KEEP = [
    "xiaonuo_simple.py",           # 简化版主文件
    "xiaonuo_simple_api.py",       # API接口
]


def cleanup_xiaonuo_directory():
    """清理xiaonuo目录"""
    base_dir = Path(__file__).parent

    # 创建归档目录
    ARCHIVE_DIR.mkdir(exist_ok=True)
    print(f"📁 归档目录: {ARCHIVE_DIR}")

    # 统计信息
    moved_count = 0
    total_size = 0

    # 归档文件
    for category, files in FILES_TO_ARCHIVE.items():
        category_dir = ARCHIVE_DIR / category
        category_dir.mkdir(exist_ok=True)

        for filename in files:
            src_path = base_dir / filename
            if src_path.exists():
                dst_path = category_dir / filename
                try:
                    shutil.move(str(src_path), str(dst_path))
                    size = dst_path.stat().st_size
                    total_size += size
                    moved_count += 1
                    print(f"✓ 移动: {filename} ({size:,} bytes)")
                except Exception as e:
                    print(f"✗ 失败: {filename} - {e}")

    # 创建README
    readme_content = f"""# 小诺目录清理归档
# Xiaonuo Directory Cleanup Archive

归档时间: 2025-02-09
归档文件数: {moved_count}
总大小: {total_size:,} bytes ({total_size / 1024 / 1024:.2f} MB)

## 目录说明

- old_agent_versions: 旧版本智能体文件
- analysis_tools: 分析工具
- startup_scripts: 启动脚本
- utility_scripts: 工具脚本
- patent_search_scripts: 专利搜索脚本
- test_files: 测试文件
- old_configs: 旧配置文件

## 保留的核心文件

- xiaonuo_simple.py: 简化版主文件
- xiaonuo_simple_api.py: API接口

## 注意

这些文件已归档，如需使用请从归档目录恢复。
核心智能体实现已迁移到: core/agents/xiaonuo_pisces_with_memory.py
"""

    (ARCHIVE_DIR / "README.md").write_text(readme_content, encoding="utf-8")

    print(f"\n✅ 清理完成！")
    print(f"   移动文件: {moved_count}")
    print(f"   释放空间: {total_size / 1024 / 1024:.2f} MB")
    print(f"   归档位置: {ARCHIVE_DIR}")


if __name__ == "__main__":
    cleanup_xiaonuo_directory()
