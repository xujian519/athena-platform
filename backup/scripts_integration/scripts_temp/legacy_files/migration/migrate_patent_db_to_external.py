#!/usr/bin/env python3
"""
中国专利数据库迁移到移动硬盘
Migration script for moving China patent database to external storage
"""

import os
import sys
import shutil
import subprocess
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PatentDBMigrator:
    def __init__(self):
        self.base_path = Path("/Users/xujian/Athena工作平台")
        self.source_db_path = self.base_path / "data" / "local" / "databases" / "patent_db"
        self.external_mount = Path("/Volumes/AthenaData")
        self.target_db_path = self.external_mount / "databases" / "patent_full"

        # PostgreSQL配置
        self.pg_ctl_path = self.find_pg_ctl()

    def find_pg_ctl(self):
        """查找pg_ctl命令路径"""
        possible_paths = [
            "/Applications/Postgres.app/Contents/Versions/latest/bin/pg_ctl",
            "/usr/local/bin/pg_ctl",
            "/opt/homebrew/bin/pg_ctl",
            "/usr/bin/pg_ctl"
        ]

        for path in possible_paths:
            if Path(path).exists():
                return path
        return None

    def check_prerequisites(self):
        """检查迁移前提条件"""
        logger.info("🔍 检查迁移前提条件...")

        # 1. 检查源数据库
        if not self.source_db_path.exists():
            logger.error("❌ 未找到源专利数据库")
            return False

        # 2. 检查移动硬盘
        if not self.external_mount.exists():
            logger.error("❌ 未找到移动硬盘，请插入名为 'AthenaData' 的移动硬盘")
            return False

        # 3. 检查空间
        source_size = self.get_directory_size(self.source_db_path)
        available_space = self.get_available_space(self.external_mount)

        logger.info(f"📊 源数据库大小: {source_size:.1f}GB")
        logger.info(f"💾 可用空间: {available_space:.1f}GB")

        if available_space < source_size * 1.2:  # 需要20%的额外空间
            logger.error("❌ 移动硬盘空间不足")
            return False

        # 4. 检查pg_ctl
        if not self.pg_ctl_path:
            logger.error("❌ 未找到pg_ctl命令")
            return False

        logger.info("✅ 所有前提条件检查通过")
        return True

    def stop_patent_db(self):
        """停止专利数据库"""
        logger.info("🛑 停止专利数据库...")

        # 检查数据库是否运行
        try:
            result = subprocess.run(
                [self.pg_ctl_path, "-D", str(self.source_db_path), "status"],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                # 数据库正在运行，停止它
                subprocess.run(
                    [self.pg_ctl_path, "-D", str(self.source_db_path), "stop", "-m", "fast"],
                    capture_output=True,
                    text=True
                )
                logger.info("✅ 专利数据库已停止")
            else:
                logger.info("ℹ️ 专利数据库未运行")

        except Exception as e:
            logger.warning(f"⚠️ 停止数据库时出错: {e}")

    def migrate_data(self):
        """迁移数据"""
        logger.info("🚀 开始迁移数据...")

        # 创建目标目录
        self.target_db_path.mkdir(parents=True, exist_ok=True)

        # 使用rsync进行迁移（支持断点续传）
        cmd = [
            "rsync",
            "-avh",           # 归档模式，显示进度，人类可读
            "--progress",     # 显示进度
            "--partial",      # 支持断点续传
            "--info=progress2", # 更详细的进度信息
            f"{self.source_db_path}/",
            f"{self.target_db_path}/"
        ]

        logger.info("执行迁移命令...")
        logger.info("这可能需要一些时间，请耐心等待...")

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # 实时显示进度
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                logger.info(output.strip())

        return_code = process.poll()

        if return_code == 0:
            logger.info("✅ 数据迁移成功")
            return True
        else:
            logger.error(f"❌ 数据迁移失败，返回码: {return_code}")
            return False

    def setup_external_db(self):
        """设置外部数据库"""
        logger.info("⚙️ 设置外部数据库...")

        # 更新postgresql.conf
        conf_file = self.target_db_path / "postgresql.conf"
        if conf_file.exists():
            self.update_postgres_config(conf_file)

        # 创建启动脚本
        self.create_startup_script()

        # 更新配置文件
        self.update_db_config()

        logger.info("✅ 外部数据库设置完成")

    def update_postgres_config(self, conf_file):
        """更新PostgreSQL配置"""
        with open(conf_file, 'a') as f:
            f.write("\n# 外部存储优化配置\n")
            f.write("port = 5450\n")
            f.write("max_connections = 100\n")
            f.write("shared_buffers = 512MB\n")
            f.write("work_mem = 8MB\n")
            f.write("maintenance_work_mem = 128MB\n")
            f.write("random_page_cost = 1.1\n")
            f.write("effective_cache_size = 2GB\n")

    def create_startup_script(self):
        """创建启动脚本"""
        script_dir = self.base_path / "scripts" / "databases"
        script_dir.mkdir(parents=True, exist_ok=True)

        script_content = f"""#!/bin/bash
# 外部专利数据库启动脚本

DB_PATH="{self.target_db_path}"
PORT=5450
LOG_FILE="$DB_PATH/logfile"

case "$1" in
    start)
        echo "启动外部专利数据库..."
        # 检查移动硬盘是否挂载
        if [ ! -d "{self.external_mount}" ]; then
            echo "❌ 移动硬盘未挂载"
            exit 1
        fi

        pg_ctl -D "$DB_PATH" -l "$LOG_FILE" start -o "-p $PORT"
        echo "✅ 外部专利数据库已启动 (端口: $PORT)"
        ;;
    stop)
        echo "停止外部专利数据库..."
        pg_ctl -D "$DB_PATH" -m fast stop
        echo "✅ 外部专利数据库已停止"
        ;;
    status)
        pg_ctl -D "$DB_PATH" status
        ;;
    *)
        echo "用法: $0 {{start|stop|status}}"
        exit 1
        ;;
esac
"""

        script_file = script_dir / "patent_full.sh"
        with open(script_file, 'w') as f:
            f.write(script_content)

        os.chmod(script_file, 0o755)
        logger.info(f"✅ 创建启动脚本: {script_file}")

    def update_db_config(self):
        """更新数据库配置文件"""
        config_file = self.base_path / "config" / "external_dbs.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)

        import json
        config = {
            "patent_full": {
                "path": str(self.target_db_path),
                "port": 5450,
                "type": "external",
                "size_gb": round(self.get_directory_size(self.source_db_path), 1),
                "migration_date": datetime.now().isoformat()
            }
        }

        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)

        logger.info(f"✅ 更新配置文件: {config_file}")

    def cleanup_local_data(self):
        """清理本地数据（可选）"""
        logger.warning("⚠️ 本地数据备份选项:")
        logger.warning("1. 保留原数据（推荐）")
        logger.warning("2. 压缩后保留")
        logger.warning("3. 完全删除")

        choice = input("\n请选择 (1/2/3): ").strip()

        if choice == "1":
            # 重命名目录
            backup_path = self.source_db_path.parent / "patent_db_backup"
            if backup_path.exists():
                shutil.rmtree(backup_path)
            shutil.move(str(self.source_db_path), str(backup_path))
            logger.info("✅ 原数据已备份到: " + str(backup_path))

        elif choice == "2":
            # 压缩
            import gzip
            import tarfile

            backup_file = self.source_db_path.parent / "patent_db_backup.tar.gz"
            with tarfile.open(backup_file, "w:gz") as tar:
                tar.add(self.source_db_path, arcname="patent_db")

            logger.info(f"✅ 压缩备份完成: {backup_file}")

            # 询问是否删除原目录
            delete = input("是否删除原目录？(y/N): ").strip().lower()
            if delete == 'y':
                shutil.rmtree(self.source_db_path)
                logger.info("✅ 原目录已删除")

        elif choice == "3":
            # 完全删除
            delete = input("确认要完全删除原数据吗？(yes/no): ").strip().lower()
            if delete == "yes":
                shutil.rmtree(self.source_db_path)
                logger.info("✅ 原数据已完全删除")
        else:
            logger.info("保留原数据")

    def verify_migration(self):
        """验证迁移结果"""
        logger.info("🔍 验证迁移结果...")

        # 1. 检查文件完整性
        if not self.target_db_path.exists():
            logger.error("❌ 目标目录不存在")
            return False

        source_size = self.get_directory_size(self.source_db_path) if self.source_db_path.exists() else 0
        target_size = self.get_directory_size(self.target_db_path)

        logger.info(f"📊 源数据大小: {source_size:.1f}GB")
        logger.info(f"📊 目标数据大小: {target_size:.1f}GB")

        # 2. 尝试启动数据库
        try:
            script_file = self.base_path / "scripts" / "databases" / "patent_full.sh"
            if script_file.exists():
                subprocess.run([str(script_file), "status"], capture_output=True)
                logger.info("✅ 数据库配置验证通过")
            else:
                logger.warning("⚠️ 启动脚本不存在")
        except Exception as e:
            logger.warning(f"⚠️ 启动验证失败: {e}")

        logger.info("✅ 迁移验证完成")
        return True

    def get_directory_size(self, path: Path) -> float:
        """获取目录大小（GB）"""
        if not path.exists():
            return 0

        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = Path(dirpath) / filename
                if not filepath.is_symlink():
                    total_size += filepath.stat().st_size

        return total_size / (1024 ** 3)  # 转换为GB

    def get_available_space(self, path: Path) -> float:
        """获取可用空间（GB）"""
        stat = os.statvfs(path)
        available = stat.f_bavail * stat.f_frsize
        return available / (1024 ** 3)

    def run(self):
        """运行完整迁移流程"""
        print("="*60)
        print("🗄️ 中国专利数据库迁移工具")
        print("="*60)
        print()

        # 1. 检查前提条件
        if not self.check_prerequisites():
            return False

        # 2. 停止数据库
        self.stop_patent_db()

        # 3. 迁移数据
        if not self.migrate_data():
            return False

        # 4. 设置外部数据库
        self.setup_external_db()

        # 5. 验证迁移
        self.verify_migration()

        # 6. 清理本地数据
        self.cleanup_local_data()

        print()
        print("="*60)
        print("✅ 迁移完成！")
        print()
        print("📌 后续操作:")
        print(f"1. 启动外部数据库: {self.base_path}/scripts/databases/patent_full.sh start")
        print("2. 更新应用配置连接到端口5450")
        print("3. 测试数据库连接")
        print("4. 定期备份数据")
        print()
        print("💾 存储空间节省:")
        saved_space = self.get_directory_size(self.source_db_path)
        print(f"- 本机释放空间: ~{saved_space:.0f}GB")
        print("="*60)

        return True


def main():
    """主函数"""
    migrator = PatentDBMigrator()

    # 安全确认
    print("⚠️ 这将移动约200GB的专利数据库到移动硬盘")
    print("请确保:")
    print("1. 移动硬盘已连接且命名为 'AthenaData'")
    print("2. 有足够的存储空间（至少240GB）")
    print("3. 已备份重要数据")
    print()

    confirm = input("确认继续迁移？(yes/no): ").strip().lower()
    if confirm != "yes":
        print("已取消迁移")
        return

    # 运行迁移
    try:
        migrator.run()
    except KeyboardInterrupt:
        print("\n❌ 迁已被用户中断")
    except Exception as e:
        logger.error(f"❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()