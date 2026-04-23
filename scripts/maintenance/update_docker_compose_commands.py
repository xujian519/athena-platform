#!/usr/bin/env python3
"""
批量更新项目中的docker-compose命令为新格式

旧格式: docker-compose [command]
新格式: docker-compose -f docker-compose.unified.yml --profile <profile> [command]
"""

import re
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path("/Users/xujian/Athena工作平台")

# 需要更新的文件列表
FILES_TO_UPDATE = [
    "scripts/start_docker_monitoring.sh",
    "tests/verification/quick_test.sh",
    "tests/integration/run_tests.sh",
    "scripts/deploy_to_production.sh",
    "scripts/backup_to_external_drive.sh",
    "scripts/verify_data_persistence.sh",
    "scripts/start_production_environment.sh",
    "scripts/setup-test-env.sh",
    "scripts/memory/start_infrastructure.sh",
    "scripts/local_ci.sh",
    "scripts/deployment/deploy_perception.sh",
    "scripts/deploy_prompt_system_fixes.sh",
    "scripts/deploy_local_cicd.sh",
    "scripts/deploy/local_ci_cd.sh",
    "scripts/deploy/deploy_local_production.sh",
    "scripts/deploy-all.sh",
    "scripts/ci/local-ci-check.sh",
    "infrastructure/deploy/deploy_local_pg.sh",
    "services/sync_service/start_sync_service.sh",
    "services/knowledge-graph-service/start.sh",
    "core/fusion/deploy_vgraph_fusion.sh",
]

# 替换规则
REPLACEMENTS = [
    # 基础命令替换（开发环境）
    (
        r"docker-compose up -d",
        r"docker-compose -f docker-compose.unified.yml --profile dev up -d"
    ),
    (
        r"docker-compose down",
        r"docker-compose -f docker-compose.unified.yml --profile dev down"
    ),
    # 测试环境
    (
        r"docker-compose -f docker-compose\.test\.yml up -d",
        r"docker-compose -f docker-compose.unified.yml --profile test up -d"
    ),
    (
        r"docker-compose -f docker-compose\.test\.yml down",
        r"docker-compose -f docker-compose.unified.yml --profile test down"
    ),
    # 监控服务
    (
        r"docker-compose -f .+?monitoring/docker-compose\.yml up -d",
        r"docker-compose -f docker-compose.unified.yml --profile monitoring up -d"
    ),
    # 带参数的命令
    (
        r"docker-compose ps",
        r"docker-compose -f docker-compose.unified.yml --profile dev ps"
    ),
    (
        r"docker-compose logs",
        r"docker-compose -f docker-compose.unified.yml --profile dev logs"
    ),
    (
        r"docker-compose restart",
        r"docker-compose -f docker-compose.unified.yml --profile dev restart"
    ),
]


def update_file(file_path: Path) -> bool:
    """更新单个文件"""
    try:
        # 读取文件内容
        content = file_path.read_text(encoding='utf-8')
        original_content = content

        # 应用所有替换规则
        for pattern, replacement in REPLACEMENTS:
            content = re.sub(pattern, replacement, content)

        # 如果内容有变化，写回文件
        if content != original_content:
            # 创建备份
            backup_path = file_path.with_suffix(f"{file_path.suffix}.bak")
            backup_path.write_text(original_content, encoding='utf-8')

            # 写入新内容
            file_path.write_text(content, encoding='utf-8')
            return True

        return False

    except Exception as e:
        print(f"❌ 错误: {file_path} - {e}")
        return False


def main():
    print("🔧 开始批量更新docker-compose命令...")
    print()

    updated_count = 0
    skipped_count = 0
    error_count = 0

    for file_path_str in FILES_TO_UPDATE:
        file_path = PROJECT_ROOT / file_path_str

        if not file_path.exists():
            print(f"⚠️  文件不存在，跳过: {file_path_str}")
            skipped_count += 1
            continue

        print(f"📝 处理: {file_path_str}")

        if update_file(file_path):
            print("  ✅ 已更新")
            updated_count += 1
        else:
            print("  ℹ️  无需更新")
            skipped_count += 1

    print()
    print("=" * 60)
    print("📊 更新统计:")
    print(f"  ✅ 已更新: {updated_count} 个文件")
    print(f"  ℹ️  跳过: {skipped_count} 个文件")
    print(f"  ❌ 错误: {error_count} 个文件")
    print("=" * 60)
    print()
    print("⚠️  注意:")
    print("  - 原文件已备份为 .bak 文件")
    print("  - 请检查更新后的文件是否正确")
    print("  - 确认无误后可删除备份文件")
    print()


if __name__ == "__main__":
    main()
