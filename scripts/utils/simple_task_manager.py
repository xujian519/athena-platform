#!/usr/bin/env python3
"""
简单任务管理器
Simple Task Manager

快速查看和管理后台进程

作者: Athena AI团队
创建时间: 2025-12-17 06:15:00
"""

import subprocess
import sys
from typing import Any


def run_command(cmd, description="") -> None:
    """执行命令"""
    print(f"🔧 {description}")
    print(f"   执行: {cmd}")

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        if result.stdout.strip():
            print(f"   输出:\n{result.stdout}")

        if result.stderr.strip():
            print(f"   错误:\n{result.stderr}")

        return result.returncode == 0

    except Exception as e:
        print(f"   ❌ 执行失败: {e}")
        return False

def show_processes() -> Any:
    """显示相关进程"""
    print("🔍 查看Athena工作平台后台进程")
    print("=" * 60)

    # 查看Python进程
    print("\n📋 Python进程:")
    run_command("ps aux | grep python | grep -E 'xiaonuo|8001|8005|8087|8030'", "查找相关Python进程")

    # 查看端口占用
    print("\n📡 端口占用:")
    run_command("lsof -i :8005", "查看8005端口(xiaonuo控制器)")
    run_command("lsof -i :8081", "查看8081端口")
    run_command("lsof -i :8030", "查看8030端口")

    # 查看内存使用
    print("\n💾 内存使用:")
    run_command("ps aux | grep python | awk '{sum += $6} END {print \"Total:\", sum/1024/1024\"}'", "Python进程总内存")

def kill_process(pid, description="") -> None:
    """停止指定进程"""
    if not pid or not pid.isdigit():
        print("❌ 无效的PID")
        return False

    print(f"🛑 停止进程 {pid} ({description})")
    return run_command(f"kill {pid}", f"停止PID {pid}")

def stop_xiaonuo() -> Any:
    """停止小诺控制器"""
    print("🛑 停止小诺平台控制器")

    # 获取PID
    result = subprocess.run("ps aux | grep xiaonuo_platform_controller.py | grep -v grep | awk '{print $2}'",
                       shell=True, capture_output=True, text=True)

    if result.stdout.strip():
        pid = result.stdout.strip()
        print(f"找到小诺进程 PID: {pid}")
        return kill_process(pid, "小诺平台控制器")
    else:
        print("❌ 未找到小诺平台控制器进程")
        return False

def clean_all() -> Any:
    """清理所有相关进程"""
    print("🧹 清理Athena工作平台相关进程")
    print("⚠️ 这将停止所有相关的Python进程！")

    # 获取所有相关进程的PID
    result = subprocess.run("ps aux | grep python | grep -E 'xiaonuo|8001|8005|8087|8030' | awk '{print $2}'",
                       shell=True, capture_output=True, text=True)

    if result.stdout.strip():
        pids = result.stdout.strip().split('\n')
        print(f"找到 {len(pids)} 个相关进程")

        stopped = 0
        for pid in pids:
            if pid.strip():
                if kill_process(pid.strip(), f"进程{pid}"):
                    stopped += 1

        print(f"✅ 已停止 {stopped}/{len(pids)} 个进程")
    else:
        print("✅ 没有找到相关进程")

def main() -> None:
    """主菜单"""
    import argparse

    parser = argparse.ArgumentParser(description='Athena工作平台后台任务管理')
    parser.add_argument('--show', action='store_true', help='显示所有进程')
    parser.add_argument('--kill-xiaonuo', action='store_true', help='停止小诺控制器')
    parser.add_argument('--kill', type=int, help='停止指定PID的进程')
    parser.add_argument('--clean', action='store_true', help='清理所有相关进程')
    parser.add_argument('--memory', action='store_true', help='检查内存使用')

    args = parser.parse_args()

    print("🚀 Athena工作平台 - 后台任务管理器")
    print("=" * 60)

    try:
        if args.show or not any([args.kill_xiaonuo, args.kill, args.clean, args.memory]):
            show_processes()

        if args.memory:
            print("\n💾 内存使用详情:")
            run_command("top -l 1 | grep 'Python'", "Python进程实时状态")

        if args.kill_xiaonuo:
            stop_xiaonuo()

        if args.kill:
            kill_process(args.kill, f"进程{args.kill}")

        if args.clean:
            confirm = input("\n⚠️ 确认清理所有相关进程？(y/N): ").lower().strip()
            if confirm == 'y':
                clean_all()

        print("\n💡 可用命令:")
        print("  python3 simple_task_manager.py --show        # 查看所有进程")
        print("  python3 simple_task_manager.py --kill-xiaonuo # 停止小诺控制器")
        print("  python3 simple_task_manager.py --kill 14214     # 停止指定PID")
        print("  python3 simple_task_manager.py --clean        # 清理所有进程")
        print("  python3 simple_task_manager.py --memory      # 检查内存使用")

    except KeyboardInterrupt:
        print("\n👋 操作已取消")
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
