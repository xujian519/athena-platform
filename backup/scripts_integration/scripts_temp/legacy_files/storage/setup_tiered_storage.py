#!/usr/bin/env python3
"""
Athena平台分层存储设置脚本
Setup script for Athena platform tiered storage
"""

import os
import sys
import json
import shutil
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TieredStorageSetup:
    def __init__(self, base_path: str = "/Users/xujian/Athena工作平台"):
        self.base_path = Path(base_path)
        self.data_path = self.base_path / "data"

        # 存储配置
        self.storage_config = {
            "local": {
                "path": self.data_path / "local",
                "description": "本机SSD存储 - 核心业务数据",
                "databases": [
                    {
                        "name": "patent_business",
                        "port": 5432,
                        "description": "专利申请业务流程"
                    },
                    {
                        "name": "trademark_business",
                        "port": 5433,
                        "description": "商标申请业务流程"
                    },
                    {
                        "name": "copyright_business",
                        "port": 5434,
                        "description": "版权申请业务流程"
                    },
                    {
                        "name": "finance_management",
                        "port": 5435,
                        "description": "财务管理"
                    },
                    {
                        "name": "task_management",
                        "port": 5436,
                        "description": "任务管理"
                    },
                    {
                        "name": "project_management",
                        "port": 5437,
                        "description": "项目管理"
                    },
                    {
                        "name": "memory_module",
                        "port": 5438,
                        "description": "记忆模块数据"
                    },
                    {
                        "name": "law_database",
                        "port": 5439,
                        "description": "法律数据库"
                    },
                    {
                        "name": "patent_database",
                        "port": 5440,
                        "description": "专利数据库(活跃)"
                    },
                    {
                        "name": "trademark_database",
                        "port": 5441,
                        "description": "商标数据库"
                    }
                ]
            },
            "external": {
                "mount_point": "/Volumes/AthenaData",
                "description": "移动硬盘 - 大型只读数据库",
                "databases": [
                    {
                        "name": "patent_full",
                        "port": 5450,
                        "description": "完整中国专利数据库"
                    },
                    {
                        "name": "invalidation",
                        "port": 5451,
                        "description": "专利复审无效案例库"
                    },
                    {
                        "name": "judgments",
                        "port": 5452,
                        "description": "专利判决文书库"
                    }
                ]
            }
        }

    def setup_storage_structure(self):
        """设置存储目录结构"""
        logger.info("🚀 设置存储目录结构...")

        # 创建本地存储目录
        local_path = self.storage_config["local"]["path"]
        local_subdirs = [
            "databases",
            "documents/uploads",
            "documents/processed",
            "documents/active",
            "cache",
            "logs",
            "backups",
            "temp"
        ]

        for subdir in local_subdirs:
            full_path = local_path / subdir
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ 创建目录: {full_path}")

        # 检查外部存储
        self.check_external_storage()

        # 保存配置
        self.save_storage_config()

        logger.info("✅ 存储目录结构设置完成")

    def check_external_storage(self):
        """检查外部存储"""
        mount_point = Path(self.storage_config["external"]["mount_point"])

        if mount_point.exists():
            logger.info(f"✅ 检测到外部存储: {mount_point}")

            # 创建外部存储子目录
            for db in self.storage_config["external"]["databases"]:
                db_path = mount_point / "databases" / db["name"]
                db_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"✅ 创建外部数据库目录: {db_path}")
        else:
            logger.warning("⚠️ 未检测到外部存储设备")
            logger.info("请插入名为 'AthenaData' 的移动硬盘")

    def setup_postgresql_instances(self):
        """设置PostgreSQL多实例"""
        logger.info("🗄️ 设置PostgreSQL多实例...")

        # 获取PostgreSQL路径
        pg_bin = self.find_postgresql_bin()
        if not pg_bin:
            logger.error("❌ 未找到PostgreSQL安装")
            return False

        # 设置本地数据库实例
        for db in self.storage_config["local"]["databases"]:
            self.setup_database_instance(db, pg_bin, local=True)

        # 设置外部数据库实例（如果外部存储可用）
        if Path(self.storage_config["external"]["mount_point"]).exists():
            for db in self.storage_config["external"]["databases"]:
                self.setup_database_instance(db, pg_bin, local=False)

        return True

    def find_postgresql_bin(self) -> str | None:
        """查找PostgreSQL安装路径"""
        possible_paths = [
            "/Applications/Postgres.app/Contents/Versions/latest/bin",
            "/usr/local/bin",
            "/opt/homebrew/bin",
            "/usr/bin"
        ]

        for path in possible_paths:
            if Path(path).exists():
                if Path(path / "initdb").exists():
                    return path

        return None

    def setup_database_instance(self, db_config: Dict, pg_bin: str, local: bool):
        """设置单个数据库实例"""
        db_name = db_config["name"]
        port = db_config["port"]

        # 确定数据目录
        if local:
            data_dir = self.storage_config["local"]["path"] / "databases" / db_name
        else:
            data_dir = Path(self.storage_config["external"]["mount_point"]) / "databases" / db_name

        logger.info(f"设置数据库: {db_name} (端口: {port})")

        # 如果数据目录不存在，初始化数据库
        if not (data_dir / "PG_VERSION").exists():
            logger.info(f"初始化数据库: {db_name}")

            cmd = [
                f"{pg_bin}/initdb",
                "-D", str(data_dir),
                "-U", "postgres",
                "--encoding", "UTF8",
                "--locale=C"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"初始化数据库失败 {db_name}: {result.stderr}")
                return False

            # 配置postgresql.conf
            self.configure_postgres_conf(data_dir, port)

        # 创建启动脚本
        self.create_db_start_script(db_name, data_dir, port)

        # 保存数据库信息
        db_info_file = data_dir / "db_info.json"
        db_info = {
            "name": db_name,
            "port": port,
            "created_at": datetime.now().isoformat(),
            "storage_type": "local" if local else "external"
        }

        with open(db_info_file, 'w') as f:
            json.dump(db_info, f, indent=2)

        logger.info(f"✅ 数据库 {db_name} 设置完成")

    def configure_postgres_conf(self, data_dir: Path, port: int):
        """配置PostgreSQL参数"""
        conf_file = data_dir / "postgresql.conf"

        # 读取现有配置
        with open(conf_file, 'r') as f:
            lines = f.readlines()

        # 添加或更新配置
        new_config = [
            "# Athena平台自定义配置\n",
            f"port = {port}\n",
            "max_connections = 200\n",
            "shared_buffers = 256MB\n",
            "effective_cache_size = 1GB\n",
            "work_mem = 4MB\n",
            "maintenance_work_mem = 64MB\n",
            "checkpoint_completion_target = 0.9\n",
            "wal_buffers = 16MB\n",
            "default_statistics_target = 100\n",
            "random_page_cost = 1.1\n",
            "effective_io_concurrency = 200\n",
            "log_min_duration_statement = 1000\n",
            "log_checkpoints = on\n",
            "log_connections = on\n",
            "log_disconnections = on\n",
            "log_lock_waits = on\n"
        ]

        # 写回配置文件
        with open(conf_file, 'w') as f:
            f.writelines(lines)
            f.writelines(new_config)

    def create_db_start_script(self, db_name: str, data_dir: Path, port: int):
        """创建数据库启动脚本"""
        script_dir = self.base_path / "scripts" / "databases"
        script_dir.mkdir(parents=True, exist_ok=True)

        script_content = f"""#!/bin/bash
# {db_name} 数据库启动脚本

DB_PATH="{data_dir}"
PORT={port}
LOG_FILE="$DB_PATH/logfile"

case "$1" in
    start)
        echo "启动数据库 {db_name}..."
        pg_ctl -D "$DB_PATH" -l "$LOG_FILE" start -o "-p $PORT"
        ;;
    stop)
        echo "停止数据库 {db_name}..."
        pg_ctl -D "$DB_PATH" -m fast stop
        ;;
    status)
        pg_ctl -D "$DB_PATH" status
        ;;
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    *)
        echo "用法: $0 {{start|stop|status|restart}}"
        exit 1
        ;;
esac
"""

        script_file = script_dir / f"{db_name}.sh"
        with open(script_file, 'w') as f:
            f.write(script_content)

        # 添加执行权限
        os.chmod(script_file, 0o755)

        logger.info(f"✅ 创建启动脚本: {script_file}")

    def save_storage_config(self):
        """保存存储配置"""
        config_file = self.base_path / "config" / "storage_config.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)

        # 添加时间戳
        config = self.storage_config.copy()
        config["created_at"] = datetime.now().isoformat()
        config["setup_version"] = "1.0"

        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)

        logger.info(f"✅ 保存配置文件: {config_file}")

    def create_database_manager(self):
        """创建数据库管理工具"""
        manager_content = '''#!/usr/bin/env python3
"""
Athena平台数据库管理工具
Database Manager for Athena Platform
"""

import os
import sys
import subprocess
import json
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent.parent))

from scripts.storage.setup_tiered_storage import TieredStorageSetup

class DatabaseManager:
    def __init__(self):
        self.base_path = Path("/Users/xujian/Athena工作平台")
        self.config_file = self.base_path / "config" / "storage_config.json"
        self.load_config()

    def load_config(self):
        """加载配置"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            print("❌ 未找到配置文件，请先运行 setup_tiered_storage.py")
            sys.exit(1)

    def start_all_databases(self):
        """启动所有本地数据库"""
        print("🚀 启动所有本地数据库...")

        for db in self.config["local"]["databases"]:
            self.start_database(db, local=True)

    def start_database(self, db_config, local=True):
        """启动单个数据库"""
        name = db_config["name"]
        script_path = self.base_path / "scripts" / "databases" / f"{name}.sh"

        if script_path.exists():
            result = subprocess.run([str(script_path), "start"], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ {name} 启动成功")
            else:
                print(f"❌ {name} 启动失败: {result.stderr}")
        else:
            print(f"⚠️ {name} 启动脚本不存在")

    def stop_all_databases(self):
        """停止所有数据库"""
        print("🛑 停止所有数据库...")

        for db in self.config["local"]["databases"]:
            self.stop_database(db)

        # 如果外部存储存在，也停止外部数据库
        if Path(self.config["external"]["mount_point"]).exists():
            for db in self.config["external"]["databases"]:
                self.stop_database(db)

    def stop_database(self, db_config):
        """停止单个数据库"""
        name = db_config["name"]
        script_path = self.base_path / "scripts" / "databases" / f"{name}.sh"

        if script_path.exists():
            result = subprocess.run([str(script_path), "stop"], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ {name} 停止成功")
            else:
                print(f"⚠️ {name} 已经停止或停止失败")

    def show_status(self):
        """显示所有数据库状态"""
        print("📊 数据库状态:")
        print("-" * 50)

        all_dbs = self.config["local"]["databases"]

        # 检查外部存储
        if Path(self.config["external"]["mount_point"]).exists():
            all_dbs += self.config["external"]["databases"]

        for db in all_dbs:
            name = db["name"]
            port = db["port"]
            script_path = self.base_path / "scripts" / "databases" / f"{name}.sh"

            if script_path.exists():
                result = subprocess.run([str(script_path), "status"], capture_output=True, text=True)
                if "no server running" in result.stdout.lower():
                    status = "❌ 未运行"
                else:
                    status = "✅ 运行中"

                print(f"{name:20} | 端口:{port:5} | {status}")
            else:
                print(f"{name:20} | 端口:{port:5} | ⚠️ 未配置")

if __name__ == "__main__":
    manager = DatabaseManager()

    if len(sys.argv) < 2:
        print("用法: python database_manager.py [start|stop|status|restart]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "start":
        manager.start_all_databases()
    elif command == "stop":
        manager.stop_all_databases()
    elif command == "status":
        manager.show_status()
    elif command == "restart":
        manager.stop_all_databases()
        import time
        time.sleep(3)
        manager.start_all_databases()
    else:
        print("未知命令:", command)
'''

        manager_file = self.base_path / "scripts" / "databases" / "database_manager.py"
        with open(manager_file, 'w') as f:
            f.write(manager_content)

        os.chmod(manager_file, 0o755)

        # 创建快捷脚本
        shortcut_script = self.base_path / "scripts" / "db_manager.sh"
        shortcut_content = f"""#!/bin/bash
cd {self.base_path}
python3 scripts/databases/database_manager.py "$@"
"""
        with open(shortcut_script, 'w') as f:
            f.write(shortcut_content)

        os.chmod(shortcut_script, 0o755)

        logger.info("✅ 创建数据库管理工具")
        logger.info(f"  - 管理工具: {manager_file}")
        logger.info(f"  - 快捷命令: {shortcut_script}")

    def generate_setup_summary(self):
        """生成设置总结"""
        summary = {
            "setup_date": datetime.now().isoformat(),
            "storage_structure": {
                "local_path": str(self.storage_config["local"]["path"]),
                "external_mount": self.storage_config["external"]["mount_point"]
            },
            "databases": {
                "local_count": len(self.storage_config["local"]["databases"]),
                "external_count": len(self.storage_config["external"]["databases"])
            },
            "next_steps": [
                "1. 插入移动硬盘并命名为 'AthenaData'",
                "2. 运行: python scripts/databases/database_manager.py start",
                "3. 访问Web界面查看数据库状态"
            ]
        }

        summary_file = self.base_path / "docs" / "STORAGE_SETUP_SUMMARY.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        logger.info("📄 生成设置总结")
        return summary


def main():
    """主函数"""
    setup = TieredStorageSetup()

    print("="*60)
    print("🏗️ Athena平台分层存储设置向导")
    print("="*60)
    print()

    # 步骤1：创建存储结构
    print("步骤 1/4: 创建存储目录结构")
    setup.setup_storage_structure()
    print()

    # 步骤2：设置数据库实例
    print("步骤 2/4: 设置PostgreSQL实例")
    if setup.setup_postgresql_instances():
        print("✅ PostgreSQL实例设置完成")
    else:
        print("❌ PostgreSQL实例设置失败")
        return
    print()

    # 步骤3：创建管理工具
    print("步骤 3/4: 创建数据库管理工具")
    setup.create_database_manager()
    print()

    # 步骤4：生成总结
    print("步骤 4/4: 生成设置总结")
    summary = setup.generate_setup_summary()
    print()

    # 完成
    print("="*60)
    print("✅ 分层存储设置完成！")
    print()
    print("📌 后续操作:")
    print("1. 插入移动硬盘并命名为 'AthenaData'")
    print("2. 启动数据库: ./scripts/db_manager.sh start")
    print("3. 查看状态: ./scripts/db_manager.sh status")
    print()
    print("💾 存储空间规划:")
    print("- 本机SSD建议: 512GB-1TB")
    print("- 移动硬盘建议: 2TB-4TB")
    print("="*60)


if __name__ == "__main__":
    main()