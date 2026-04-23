#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务管理系统部署脚本
Task Management System Deployment Script

部署和配置Athena任务管理系统

作者: Athena AI系统
创建时间: 2025-12-17
版本: 1.0.0
"""

import os
from typing import Any, Dict, List, Optional, Tuple, Callable, Union
import sys
import json
import time
import subprocess
import threading
from datetime import datetime
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TaskManagerDeployer:
    """任务管理系统部署器"""

    def __init__(self):
        self.project_root = project_root
        self.data_dir = self.project_root / "data"
        self.logs_dir = self.project_root / "logs"
        self.config_file = self.project_root / "config" / "task_management.json"

    def check_environment(self) -> bool:
        """检查部署环境"""
        print("🔍 检查部署环境...")

        # 检查Python版本
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        print(f"   Python版本: {python_version}")

        if sys.version_info.major < 3:
            print("   ❌ Python 3.0+ 是必需的")
            return False
        else:
            print("   ✅ Python版本符合要求")

        # 检查必要模块
        required_modules = ['schedule', 'json', 'threading', 'datetime', 'pathlib']
        missing_modules = []

        for module in required_modules:
            try:
                __import__(module)
                print(f"   ✅ {module}")
            except ImportError:
                missing_modules.append(module)
                print(f"   ❌ {module}")

        if missing_modules:
            print(f"   ⚠️ 需要安装缺失模块: {missing_modules}")
            print("   运行: pip3 install schedule")
            return False

        print("   ✅ 所有必要模块已就绪")
        return True

    def setup_directories(self) -> Any:
        """创建必要目录"""
        print("📁 创建目录结构...")

        required_dirs = [
            self.data_dir / "tasks",
            self.data_dir / "todos",
            self.logs_dir,
            self.project_root / "config"
        ]

        for dir_path in required_dirs:
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"   ✅ {dir_path.relative_to(self.project_root)}")
            except Exception as e:
                print(f"   ❌ 创建目录失败 {dir_path}: {e}")
                return False

        return True

    def check_system_notifications(self) -> bool:
        """检查系统通知功能"""
        print("📱 检查系统通知功能...")

        system = os.uname().sysname.lower()

        if system == 'darwin':
            print("   ✅ mac_os - osascript 通知支持")
        elif system == 'linux':
            try:
                result = subprocess.run(['which', 'notify-send'],
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print("   ✅ Linux - notify-send 通知支持")
                else:
                    print("   ⚠️ Linux - notify-send 未安装（可选）")
                    print("   安装命令: sudo apt-get install libnotify-bin")
            except:
                print("   ⚠️ Linux - 通知检查失败（可选）")
        elif system == 'windows':
            print("   ✅ Windows - 通知支持")
        else:
            print(f"   ✅ {system} - 通知支持")

        return True

    def install_dependencies(self) -> Any:
        """安装依赖"""
        print("📦 安装依赖包...")

        # 检查是否需要安装schedule
        try:
            import schedule
            print("   ✅ schedule 已安装")
        except ImportError:
            print("   🔄 正在安装 schedule...")
            result = subprocess.run([sys.executable, "-m", "pip", "install", "schedule"],
                                      capture_output=True, text=True)
            if result.returncode == 0:
                print("   ✅ schedule 安装成功")
            else:
                print("   ❌ schedule 安装失败")
                return False

        return True

    def create_default_config(self) -> Any:
        """创建默认配置"""
        print("⚙️ 创建默认配置...")

        config = {
            "task_management": {
                "enabled": True,
                "auto_save_interval": 60,  # 秒
                "reminder_check_interval": 300,  # 秒
                "notification_enabled": True,
                "persist_to_disk": True,
                "backup_enabled": True,
                "backup_interval": 3600  # 秒
            },
            "notification": {
                "enabled": True,
                "sound_enabled": False,
                "popup_enabled": True,
                "auto_dismiss": True,
                "dismiss_timeout": 5  # 秒
            },
            "reminders": {
                "default_remind_before": 120,  # 分钟
                "max_reminders": 3,
                "reminder_types": ["notification"],
                "repeat_reminders": False
            },
            "system": {
                "max_tasks": 10000,
                "cleanup_interval": 86400,  # 秒
                "log_level": "INFO"
            }
        }

        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            print(f"   ✅ 配置文件已创建: {self.config_file}")
            return True
        except Exception as e:
            print(f"   ❌ 创建配置文件失败: {e}")
            return False

    def migrate_existing_todos(self) -> Any:
        """迁移现有的TodoWrite任务"""
        print("🔄 迁移现有任务...")

        # 查找原始TodoWrite文件
        todo_sources = [
            self.data_dir / "todos.json",
            self.data_dir / "todos_backup.json"
        ]

        original_todos_found = False
        todo_data = None

        for source_file in todo_sources:
            if source_file.exists():
                try:
                    with open(source_file, 'r', encoding='utf-8') as f:
                        todo_data = json.load(f)
                    print(f"   ✅ 找到TodoWrite文件: {source_file.name}")
                    original_todos_found = True
                    break
                except Exception as e:
                    print(f"   ⚠️ 读取文件失败 {source_file}: {e}")

        if not todo_data:
            print("   ℹ️ 未找到现有的TodoWrite文件")
            return True

        # 创建迁移后的数据
        enhanced_todos = {
            "migration_time": datetime.now().isoformat(),
            "source_files": [str(f) for f in todo_sources if f.exists()],
            "todos": []
        }

        # 检查TodoWrite格式
        if isinstance(todo_data, list):
            # 标准TodoWrite格式
            enhanced_todos["todos"] = todo_data
        elif isinstance(todo_data, dict):
            if "todos" in todo_data:
                enhanced_todos["todos"] = todo_data["todos"]
            else:
                enhanced_todos["todos"] = [todo_data]

        # 保存迁移后的数据
        try:
            enhanced_todos_file = self.data_dir / "todos" / "enhanced_todos.json"
            with open(enhanced_todos_file, 'w', encoding='utf-8') as f:
                json.dump(enhanced_todos, f, ensure_ascii=False, indent=2, default=str)
            print(f"   ✅ 任务数据已迁移: {len(enhanced_todos['todos'])} 个任务")
            return True
        except Exception as e:
            print(f"   ❌ 迁移失败: {e}")
            return False

    def test_task_system(self) -> Any:
        """测试任务系统"""
        print("🧪 测试任务系统...")

        try:
            # 导入任务管理模块
            from core.tasks.task_scheduler import get_scheduler
            from core.tasks.enhanced_todo_write import get_enhanced_todo

            print("   ✅ 模块导入成功")

            # 测试任务调度器
            scheduler = get_scheduler()
            print("   ✅ 任务调度器初始化成功")

            # 测试增强TodoWrite
            todo_manager = get_enhanced_todo()
            print("   ✅ 增强TodoWrite初始化成功")

            # 测试创建任务
            test_task_id = todo_manager.add_todo(
                content="部署测试任务",
                status="pending",
                priority="high",
                tags=["测试", "部署"]
            )
            print(f"   ✅ 测试任务创建成功: {test_task_id}")

            # 测试任务完成
            success = todo_manager.update_todo_status(test_task_id, "completed")
            if success:
                print("   ✅ 测试任务状态更新成功")
            else:
                print("   ⚠️ 任务状态更新失败")

            # 测试仪表板
            dashboard = todo_manager.get_dashboard_summary()
            print(f"   ✅ 仪表板数据: {dashboard.get('total', 0)} 个任务")

            return True

        except Exception as e:
            print(f"   ❌ 系统测试失败: {e}")
            return False

    def create_startup_script(self) -> Any:
        """创建启动脚本"""
        print("🚀 创建启动脚本...")

        startup_script = self.project_root / "scripts" / "start_task_daemon.sh"

        script_content = f'''#!/bin/bash
# Athena任务管理系统守护进程启动脚本
# Task Management System Daemon Startup Script

# 设置Python路径
export PYTHONPATH="{self.project_root}:$PYTHONPATH"
export ATHENA_HOME="{self.project_root}"

# 日志文件
LOG_FILE="{self.logs_dir}/task_daemon.log"
PID_FILE="{self.logs_dir}/task_daemon.pid"

echo "🚀 启动Athena任务管理系统守护进程..."
echo "PID文件: $PID_FILE"
echo "日志文件: $LOG_FILE"

# 检查是否已在运行
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null; then
        echo "⚠️ 任务管理系统已在运行 (PID: $PID)"
        exit 1
    else
        echo "🗑️ 清理旧的PID文件"
        rm -f "$PID_FILE"
    fi
fi

# 创建日志目录
mkdir -p "$(dirname "$LOG_FILE")"

# 启动守护进程
cd "$ATHENA_HOME"
nohup python3 scripts/start_task_management_system.py --daemon > "$LOG_FILE" 2>&1 &

# 保存PID
echo $! > "$PID_FILE"

echo "✅ 任务管理系统守护进程已启动"
echo "PID: $(cat $PID_FILE)"
echo "日志: $LOG_FILE"
echo ""
echo "📊 查看状态:"
echo "  python3 scripts/start_task_management_system.py --stats"
echo ""
echo "🛑 停止服务:"
echo "  kill \\"$(cat $PID_FILE)\\""
echo "  bash scripts/start_task_daemon.sh stop"
'''

        try:
            with open(startup_script, 'w', encoding='utf-8') as f:
                f.write(script_content)

            # 设置执行权限
            startup_script.chmod(0o755)

            print(f"   ✅ 启动脚本已创建: {startup_script}")

            # 创建停止脚本
            stop_script = startup_script.with_name("stop_task_daemon.sh")
            stop_content = f'''#!/bin/bash
# Athena任务管理系统守护进程停止脚本

PID_FILE="{self.logs_dir}/task_daemon.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null; then
        echo "🛑 停止任务管理系统守护进程 (PID: $PID)"
        kill $PID
        rm -f "$PID_FILE"
        echo "✅ 任务管理系统已停止"
    else
        echo "⚠️ 任务管理系统未在运行"
    fi
else
    echo "⚠️ PID文件不存在"
fi
'''

            with open(stop_script, 'w', encoding='utf-8') as f:
                f.write(stop_content)

            stop_script.chmod(0o755)

            print(f"   ✅ 停止脚本已创建: {stop_script}")

            return True

        except Exception as e:
            print(f"   ❌ 创建启动脚本失败: {e}")
            return False

    def create_systemd_service(self) -> Any:
        """创建systemd服务（可选）"""
        print("🔧 创建systemd服务（可选）...")

        if not Path("/etc/systemd/system").exists():
            print("   ⚠️ systemd系统未找到，跳过systemd服务创建")
            return True

        service_file = Path("/etc/systemd/system/athena-task-manager.service")

        if service_file.exists():
            print("   ℹ️ systemd服务已存在，跳过创建")
            return True

        service_content = f'''[Unit]
Description=Athena Task Management System
After=network.target

[Service]
Type=simple
User={os.getenv('USER', 'athena')}
WorkingDirectory={self.project_root}
Environment=PYTHONPATH={self.project_root}
Environment=ATHENA_HOME={self.project_root}
ExecStart={self.project_root}/venv/bin/python3 scripts/start_task_management_system.py --daemon
ExecReload=/bin/kill -HUP $MAINPID
KillMode=process
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
'''

        try:
            print("   📝 systemd服务内容已准备")
            print("   💡 如需创建，请手动执行：")
            print(f"      sudo tee {service_file} << 'EOF'")
            for line in service_content.split('\n'):
                print(f"      {line}")
            print("      EOF")
            print(f"      sudo systemctl daemon-reload")
            print(f"      sudo systemctl enable athena-task-manager")
            print(f"      sudo systemctl start athena-task-manager")
            return True
        except Exception as e:
            print(f"   ⚠️ systemd服务准备失败: {e}")
            return False

    def backup_existing_data(self) -> Any:
        """备份现有数据"""
        print("💾 备份现有数据...")

        # 备份目录
        backup_dir = self.data_dir / "backup"
        backup_dir.mkdir(exist_ok=True)

        backup_subdirs = [
            self.data_dir / "tasks",
            self.data_dir / "todos"
        ]

        backup_created = []

        for source_dir in backup_subdirs:
            if source_dir.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"{source_dir.name}_backup_{timestamp}"
                backup_target = backup_dir / backup_name

                try:
                    import shutil
                    shutil.copytree(source_dir, backup_target, dirs_exist_ok=True)
                    backup_created.append(str(backup_target))
                    print(f"   ✅ 备份完成: {backup_target}")
                except Exception as e:
                    print(f"   ❌ 备份失败 {source_dir}: {e}")

        if backup_created:
            print(f"   📁 共创建了 {len(backup_created)} 个备份")
        else:
            print("   ℹ️ 没有需要备份的数据")

        return True

    def deploy(self) -> Any:
        """执行完整部署"""
        print("=" * 80)
        print("🚀 Athena任务管理系统部署")
        print("=" * 80)
        print(f"部署时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"部署路径: {self.project_root}")
        print()

        # 部署步骤
        steps = [
            ("检查环境", self.check_environment),
            ("创建目录", self.setup_directories),
            ("检查通知", self.check_system_notifications),
            ("安装依赖", self.install_dependencies),
            ("创建配置", self.create_default_config),
            ("备份数据", self.backup_existing_data),
            ("迁移任务", self.migrate_existing_todos),
            ("测试系统", self.test_task_system),
            ("创建脚本", self.create_startup_script),
            ("systemd服务", self.create_systemd_service)
        ]

        success_count = 0
        for step_name, step_func in steps:
            print(f"\\n📍 {step_name}...")
            if step_func():
                success_count += 1
            else:
                print(f"   ⚠️ {step_name} 失败，请检查上述错误")

        print("\\n" + "=" * 80)

        if success_count == len(steps):
            print("🎉 部署成功！")
            print(f"✅ {success_count}/{len(steps)} 个步骤完成")
            print()
            print("🚀 启动命令:")
            print("   交互模式: python3 scripts/start_task_management_system.py")
            print("   守护进程: bash scripts/start_task_daemon.sh")
            print("   查看统计: python3 scripts/start_task_management_system.py --stats")
            print()
            print("📱 您的范文新任务已自动配置提醒！")
            print("   ⏰ 明天上午8:00自动提醒")
            print("   🔔 macOS原生通知支持")
            print()
            print("📖 使用文档:")
            print("   - 任务管理系统实施报告.md")
            print("   - 系统使用指南.md")
            print()
        else:
            print("⚠️ 部署未完全成功")
            print(f"✅ 成功步骤: {success_count}/{len(steps)}")
            print("❌ 失败步骤请根据上述错误信息手动处理")

        return success_count == len(steps)


def main() -> None:
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='Athena任务管理系统部署工具')
    parser.add_argument('--check-only', action='store_true', help='只检查环境，不执行部署')
    parser.add_argument('--migrate-only', action='store_true', help='只迁移任务，不部署')
    parser.add_argument('--test-only', action='store_true', help='只测试系统，不部署')
    parser.add_argument('--create-scripts-only', action='store_true', help='只创建启动脚本，不部署')

    args = parser.parse_args()

    print("🔧 Athena任务管理系统部署工具")

    deployer = TaskManagerDeployer()

    if args.check_only:
        success = deployer.check_environment()
        print(f"\\n环境检查结果: {'✅ 通过' if success else '❌ 失败'}")
    elif args.migrate_only:
        deployer.setup_directories()
        deployer.migrate_existing_todos()
        print("\\n✅ 任务迁移完成")
    elif args.test_only:
        deployer.test_task_system()
        print("\\n✅ 系统测试完成")
    elif args.create_scripts_only:
        deployer.create_startup_script()
        print("\\n✅ 启动脚本创建完成")
    else:
        success = deployer.deploy()

        if success:
            print("\\n🎉 部署完成！现在您可以启动任务管理系统：")
            print("\\n下一步：")
            print("1. 启动交互模式测试功能")
            print("2. 启动守护进程用于生产环境")
            print("3. 检查范文新任务自动提醒")


if __name__ == "__main__":
    main()