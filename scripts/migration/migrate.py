#!/usr/bin/env python3
"""
Scripts模块迁移工具
帮助将现有脚本迁移到新架构
"""

import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# 添加核心库路径
sys.path.append(os.path.dirname(__file__) + '/..')

from utils.logger import ScriptLogger


class ScriptMigrator:
    """脚本迁移器"""

    def __init__(self):
        self.logger = ScriptLogger("ScriptMigrator")
        self.old_scripts_dir = Path("/Users/xujian/Athena工作平台/scripts")
        self.new_scripts_dir = Path("/Users/xujian/Athena工作平台/scripts_new")
        self.legacy_dir = self.new_scripts_dir / "legacy"
        self.migration_log = []

    def migrate_all(self) -> Any:
        """执行完整迁移"""
        print("\n🚀 开始迁移 Scripts 模块...")
        print("=" * 60)

        # 1. 备份现有脚本
        self.backup_old_scripts()

        # 2. 迁移启动脚本
        self.migrate_startup_scripts()

        # 3. 迁移数据脚本
        self.migrate_data_scripts()

        # 4. 迁移部署脚本
        self.migrate_deployment_scripts()

        # 5. 迁移工具脚本
        self.migrate_utility_scripts()

        # 6. 创建快捷方式
        self.create_shortcuts()

        # 7. 生成迁移报告
        self.generate_report()

        print("\n✅ 迁移完成！")
        print("请查看 migration_report.json 了解详细信息")

    def backup_old_scripts(self) -> Any:
        """备份旧脚本"""
        print("\n📦 备份现有脚本...")

        backup_name = f"scripts_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_path = self.old_scripts_dir.parent / backup_name

        if backup_path.exists():
            shutil.rmtree(backup_path)

        shutil.copytree(self.old_scripts_dir, backup_path)

        self.log_migration("backup", f"备份到 {backup_path}")
        print(f"  ✓ 备份完成: {backup_name}")

    def migrate_startup_scripts(self) -> Any:
        """迁移启动脚本"""
        print("\n🚀 迁移启动脚本...")

        startup_scripts = [
            "start_athena.sh",
            "start_xiaonuo_integrated.sh",
            "start_complete_memory_system.sh",
            "start_memory_service.sh",
            "start_agent.sh"
        ]

        for script in startup_scripts:
            src = self.old_scripts_dir / script
            if src.exists():
                # 移动到legacy目录
                dst = self.legacy_dir / script
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dst))

                self.log_migration("moved", f"{script} -> legacy/{script}")
                print(f"  ✓ {script} 已移动到 legacy/")

        # 创建新的启动命令说明
        readme = self.new_scripts_dir / "startup_commands.md"
        with open(readme, 'w', encoding='utf-8') as f:
            f.write("""# 启动命令迁移说明

## 旧命令 -> 新命令

```bash
# 启动完整平台
# 旧: ./start_athena.sh
# 新: python3 athena.py start

# 启动小诺集成服务
# 旧: ./start_xiaonuo_integrated.sh
# 新: python3 athena.py start --services core_server ai_service patent_api

# 启动完整记忆系统
# 旧: ./start_complete_memory_system.sh
# 新: python3 athena.py start --services core_server memory_service

# 启动记忆服务
# 旧: ./start_memory_service.sh
# 新: python3 athena.py start --services memory_service

# 启动智能体
# 旧: ./start_agent.sh
# 新: python3 athena.py start --services agent_service
```

## 更多选项

```bash
# 查看帮助
python3 athena.py --help

# 查看状态
python3 athena.py status

# 实时监控
python3 athena.py monitor

# 快速启动
python3 start.py
```
""")
        self.log_migration("created", "startup_commands.md")

    def migrate_data_scripts(self) -> Any:
        """迁移数据脚本"""
        print("\n💾 迁移数据脚本...")

        data_dir = self.old_scripts_dir / "database"
        if data_dir.exists():
            # 创建新的数据脚本目录
            new_data_dir = self.new_scripts_dir / "actions" / "data"
            new_data_dir.mkdir(parents=True, exist_ok=True)

            # 迁移关键脚本
            key_scripts = [
                "init_postgresql_memory.sh",
                "import_legal_vectors.py",
                "cleanup_logs.sh",
                "backup_database.py"
            ]

            for script in key_scripts:
                src = data_dir / script
                if src.exists():
                    # 创建对应的新Python脚本
                    self.create_new_data_script(script, new_data_dir)

                    # 移动旧脚本到legacy
                    dst = self.legacy_dir / "database" / script
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(src), str(dst))

                    self.log_migration("converted", f"{script} -> actions/data/new_{script}")
                    print(f"  ✓ {script} 已转换")

    def create_new_data_script(self, old_name, target_dir) -> Any:
        """创建新的数据脚本"""
        if old_name.endswith('.sh'):
            new_name = old_name[:-3] + '.py'
        else:
            new_name = "new_" + old_name

        script_path = target_dir / new_name

        # 根据脚本类型创建不同的模板
        if "init" in old_name:
            self.create_init_script(script_path)
        elif "import" in old_name:
            self.create_import_script(script_path)
        elif "cleanup" in old_name:
            self.create_cleanup_script(script_path)
        elif "backup" in old_name:
            self.create_backup_script(script_path)
        else:
            self.create_generic_script(script_path, old_name)

    def create_init_script(self, path) -> Any:
        """创建初始化脚本"""
        content = '''#!/usr/bin/env python3
"""
数据库初始化脚本
使用新的架构实现
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from core.infrastructure.database import db_manager
from utils.logger import ScriptLogger
from utils.progress_tracker import ProgressTracker


def main():
    logger = ScriptLogger("DatabaseInit")

    try:
        logger.info("开始初始化数据库...")

        # 这里添加具体的初始化逻辑
        # 例如：创建表、插入初始数据等

        logger.info("✅ 数据库初始化完成")

    except Exception as e:
        logger.error(f"初始化失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
'''
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        os.chmod(path, 0o755)

    def create_import_script(self, path) -> Any:
        """创建导入脚本"""
        content = '''#!/usr/bin/env python3
"""
数据导入脚本
使用新的架构实现
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from core.infrastructure.database import db_manager
from utils.logger import ScriptLogger
from utils.progress_tracker import ProgressTracker


def main():
    logger = ScriptLogger("DataImport")

    try:
        logger.info("开始导入数据...")

        # 这里添加具体的导入逻辑

        logger.info("✅ 数据导入完成")

    except Exception as e:
        logger.error(f"导入失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
'''
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        os.chmod(path, 0o755)

    def create_cleanup_script(self, path) -> Any:
        """创建清理脚本"""
        content = '''#!/usr/bin/env python3
"""
数据清理脚本
使用新的架构实现
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from core.infrastructure.database import db_manager
from utils.logger import ScriptLogger
from utils.progress_tracker import ProgressTracker


def main():
    logger = ScriptLogger("DataCleanup")

    try:
        logger.info("开始清理数据...")

        # 使用内置的清理功能
        from refactored.database_cleanup import DatabaseCleanup
        cleanup = DatabaseCleanup()

        # 可以通过命令行参数指定天数
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument('--days', type=int, default=30, help='清理多少天前的数据')
        args = parser.parse_args()

        cleanup.run_cleanup()

        logger.info("✅ 数据清理完成")

    except Exception as e:
        logger.error(f"清理失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
'''
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        os.chmod(path, 0o755)

    def create_backup_script(self, path) -> Any:
        """创建备份脚本"""
        content = '''#!/usr/bin/env python3
"""
数据库备份脚本
使用新的架构实现
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from core.infrastructure.database import db_manager
from utils.logger import ScriptLogger
from utils.progress_tracker import ProgressTracker
from utils.file_manager import file_manager


def main():
    logger = ScriptLogger("DatabaseBackup")

    try:
        logger.info("开始备份数据库...")

        # 使用文件管理器进行备份
        backup_path = file_manager.backup_file(
            source_path="/var/lib/postgresql/athena.sql",
            backup_dir="/backups/database",
            compress=True
        )

        if backup_path:
            logger.info(f"✅ 数据库备份完成: {backup_path}")
        else:
            logger.error("备份失败")
            sys.exit(1)

    except Exception as e:
        logger.error(f"备份失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
'''
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        os.chmod(path, 0o755)

    def create_generic_script(self, path, old_name) -> Any:
        """创建通用脚本"""
        content = f'''#!/usr/bin/env python3
"""
{old_name} 的迁移版本
使用新的架构实现
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from core.infrastructure.database import db_manager
from utils.logger import ScriptLogger
from utils.progress_tracker import ProgressTracker


def main():
    logger = ScriptLogger("MigratedScript")

    try:
        logger.info(f"执行 {old_name} 的迁移版本...")

        # TODO: 添加具体的实现逻辑

        logger.info(f"✅ {old_name} 执行完成")

    except Exception as e:
        logger.error(f"执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
'''
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        os.chmod(path, 0o755)

    def migrate_deployment_scripts(self) -> Any:
        """迁移部署脚本"""
        print("\n🚀 迁移部署脚本...")

        deploy_dir = self.old_scripts_dir / "deployment"
        if deploy_dir.exists():
            # 创建新的部署脚本目录
            new_deploy_dir = self.new_scripts_dir / "actions" / "deploy"
            new_deploy_dir.mkdir(parents=True, exist_ok=True)

            # 迁移部署脚本
            for script in deploy_dir.glob("*.sh"):
                # 移动到legacy
                dst = self.legacy_dir / "deployment" / script.name
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(script), str(dst))

                self.log_migration("moved", f"deployment/{script.name} -> legacy/deployment/{script.name}")
                print(f"  ✓ {script.name} 已移动到 legacy/deployment/")

    def migrate_utility_scripts(self) -> Any:
        """迁移工具脚本"""
        print("\n🛠️ 迁移工具脚本...")

        utility_dirs = [
            "maintenance",
            "monitoring",
            "utils",
            "tools"
        ]

        for dir_name in utility_dirs:
            src_dir = self.old_scripts_dir / dir_name
            if src_dir.exists():
                dst_dir = self.legacy_dir / dir_name
                dst_dir.mkdir(parents=True, exist_ok=True)

                # 移动所有文件
                for item in src_dir.glob("*"):
                    dst = dst_dir / item.name
                    if item.is_file():
                        shutil.move(str(item), str(dst))
                        self.log_migration("moved", f"{dir_name}/{item.name} -> legacy/{dir_name}/{item.name}")

                print(f"  ✓ {dir_name}/ 目录已移动到 legacy/{dir_name}/")

    def create_shortcuts(self) -> Any:
        """创建快捷方式"""
        print("\n🔗 创建快捷方式...")

        # 在scripts根目录创建athena.py的软链接
        main_script = self.new_scripts_dir / "athena.py"
        link_path = self.old_scripts_dir / "athena.py"

        if link_path.exists():
            link_path.unlink()

        os.symlink(main_script.absolute(), link_path)
        self.log_migration("created", "快捷方式: scripts/athena.py -> scripts_new/athena.py")
        print("  ✓ 创建了 scripts/athena.py 快捷方式")

    def generate_report(self) -> Any:
        """生成迁移报告"""
        report = {
            "migration_time": datetime.now().isoformat(),
            "total_items": len(self.migration_log),
            "migrations": self.migration_log
        }

        report_path = self.new_scripts_dir / "migration_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print("\n📊 迁移统计:")
        print(f"  - 总计迁移: {len(self.migration_log)} 项")
        print(f"  - 报告位置: {report_path}")

    def log_migration(self, action, description) -> Any:
        """记录迁移日志"""
        self.migration_log.append({
            "time": datetime.now().isoformat(),
            "action": action,
            "description": description
        })


def main() -> None:
    """主函数"""
    migrator = ScriptMigrator()

    print("\n" + "=" * 60)
    print("Athena Scripts 模块迁移工具")
    print("=" * 60)

    answer = input("\n这将迁移所有脚本到新架构。是否继续？(y/n): ").lower()

    if answer == 'y':
        migrator.migrate_all()
    else:
        print("迁移已取消")


if __name__ == "__main__":
    main()
