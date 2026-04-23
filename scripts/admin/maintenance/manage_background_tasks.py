#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
后台任务管理器
Background Task Manager

查看和管理Athena工作平台的后台进程

作者: Athena AI团队
创建时间: 2025-12-17 06:10:00
版本: v1.0.0
"""

import subprocess
import psutil
import signal
import sys
import os
from datetime import datetime
from typing import List, Dict, Tuple

class TaskManager:
    """任务管理器"""

    def __init__(self):
        self.port_mappings = {
            8005: "小诺平台控制器 (xiaonuo_platform_controller)",
            8001: "小娜专利专家 (xiaona_agent)",
            8087: "云熙IP管理 (yunxi_agent)",
            8030: "小宸自媒体 (xiaochen_agent)",
            8000: "Web界面",
            8080: "Web界面备用",
            8002: "API网关",
            8010: "数据服务"
        }

    def get_python_processes(self) -> List[Dict]:
        """获取所有Python进程"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_percent']):
            try:
                if proc.info['name'] == 'Python':
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if any(keyword in cmdline for keyword in [
                        'xiaonuo', 'xiaona', 'yunxi', 'xiaochen',
                        'athena', 'agent', 'controller',
                        '8000', '8001', '8005', '8030', '8087', '8080'
                    ]):
                        processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'cmdline': cmdline,
                            'cpu_percent': proc.info['cpu_percent'],
                            'memory_percent': proc.info['memory_percent'],
                            'memory_mb': proc.info['memory_info'].rss / 1024 / 1024 if proc.info.get('memory_info') else 0,
                            'create_time': datetime.fromtimestamp(proc.info['create_time']).strftime('%Y-%m-%d %H:%M:%S'),
                            'status': proc.status()
                        })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return processes

    def get_port_usage(self) -> List[Dict]:
        """获取端口使用情况"""
        port_usage = []
        for port, description in self.port_mappings.items():
            try:
                for conn in psutil.net_connections():
                    if conn.status == psutil.CONN_LISTEN and conn.laddr.port == port:
                        try:
                            proc = psutil.Process(conn.pid)
                            port_usage.append({
                                'port': port,
                                'description': description,
                                'pid': conn.pid,
                                'process_name': proc.name(),
                                'status': 'LISTENING',
                                'address': f"{conn.laddr.ip}:{conn.laddr.port}"
                            })
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            port_usage.append({
                                'port': port,
                                'description': description,
                                'pid': conn.pid,
                                'process_name': 'Unknown',
                                'status': 'LISTENING',
                                'address': f"{conn.laddr.ip}:{conn.laddr.port}"
                            })
                        break
            except:
                continue
        return port_usage

    def show_processes(self):
        """显示进程状态"""
        print("🔍 Athena工作平台后台进程状态")
        print("=" * 70)
        print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # 获取Python进程
        python_processes = self.get_python_processes()
        if not python_processes:
            print("✅ 没有发现相关的Python进程")
            return

        print("🐍 Python进程列表:")
        print("-" * 70)
        print(f"{'PID':<8} {'CPU%':<8} {'内存%':<10} {'内存(MB)':<10} {'状态':<10} {'描述'}")
        print("-" * 70)

        for proc in python_processes:
            print(f"{proc['pid']:<8} {proc['cpu_percent']:<8.1} {proc['memory_percent']:<10.1} {proc['memory_mb']:<10.1} {proc['status']:<10} {proc['cmdline'][:30]}...")

        # 获取端口使用
        port_usage = self.get_port_usage()
        if port_usage:
            print("\n📡 端口使用情况:")
            print("-" * 70)
            print(f"{'端口':<8} {'PID':<8} {'状态':<12} {'描述'}")
            print("-" * 70)

            for port_info in port_usage:
                print(f"{port_info['port']:<8} {port_info['pid']:<8} {port_info['status']:<12} {port_info['description']}")

        # 资源使用统计
        total_memory = sum(proc['memory_mb'] for proc in python_processes)
        avg_cpu = sum(proc['cpu_percent'] for proc in python_processes) / len(python_processes)

        print(f"\n📊 资源使用统计:")
        print(f"   总进程数: {len(python_processes)}")
        print(f"   总内存使用: {total_memory:.1f} MB")
        print(f"   平均CPU使用: {avg_cpu:.1f}%")
        print(f"   系统负载: {psutil.cpu_percent():.1f}%")

    def identify_unnecessary_tasks(self) -> List[Dict]:
        """识别不必要的任务"""
        unnecessary = []

        python_processes = self.get_python_processes()

        for proc in python_processes:
            cmdline = proc['cmdline']

            # 识别可能的测试/开发进程
            if any(keyword in cmdline for keyword in [
                'test', 'demo', 'example', 'debug', 'dev'
            ]):
                unnecessary.append({
                    'pid': proc['pid'],
                    'type': 'development',
                    'description': '开发/测试进程',
                    'cmdline': cmdline,
                    'memory_mb': proc['memory_mb']
                })

            # 识别长期空闲进程
            if proc['status'] == 'sleeping' and proc['memory_mb'] > 100:
                unnecessary.append({
                    'pid': proc['pid'],
                    'type': 'idle',
                    'description': '长时间空闲进程',
                    'cmdline': cmdline,
                    'memory_mb': proc['memory_mb']
                })

        return unnecessary

    def stop_process(self, pid: int, force: bool = False) -> bool:
        """停止进程"""
        try:
            proc = psutil.Process(pid)

            if force:
                print(f"🔨 强制停止进程 {pid}...")
                proc.terminate()
                proc.kill()
            else:
                    print(f"🛑 停止进程 {pid}...")
                    proc.terminate()

                # 等待进程结束
                try:
                    proc.wait(timeout=5)
                    print(f"✅ 进程 {pid} 已停止")
                    return True
                except psutil.TimeoutExpired:
                    print(f"⏰ 进程 {pid} 停止超时，强制终止...")
                    proc.kill()
                    print(f"✅ 进程 {pid} 已强制停止")
                    return True

        except psutil.NoSuchProcess:
            print(f"✅ 进程 {pid} 已不存在")
            return True
        except Exception as e:
            print(f"❌ 停止进程 {pid} 失败: {e}")
            return False

    def stop_unnecessary_tasks(self, dry_run: bool = True):
        """停止不必要的任务"""
        print("🧹 识别不必要的任务")
        print("=" * 50)

        unnecessary = self.identify_unnecessary_tasks()

        if not unnecessary:
            print("✅ 没有发现不必要的任务")
            return

        total_memory_saved = sum(task['memory_mb'] for task in unnecessary)

        print(f"\n发现 {len(unnecessary)} 个不必要任务:")
        print(f"💾 可节省内存: {total_memory:.1f} MB")
        print("-" * 50)

        for i, task in enumerate(unnecessary, 1):
            print(f"{i}. PID: {task['pid']}")
            print(f"   类型: {task['type']}")
            print(f"   描述: {task['description']}")
            print(f"   内存: {task['memory_mb']:.1f} MB")
            print(f"   命令: {task['cmdline'][:80]}...")

        if dry_run:
            print(f"\n🔍 这是预览模式，实际停止请使用 --stop 参数")
        else:
            print(f"\n🛑 开始停止不必要的任务...")
            stopped_count = 0

            for task in unnecessary:
                if self.stop_process(task['pid']):
                    stopped_count += 1

            print(f"\n✅ 成功停止 {stopped_count}/{len(unnecessary)} 个任务")
            print(f"💾 释放内存: {total_memory_saved:.1f} MB")

    def check_system_health(self):
        """检查系统健康状态"""
        print("🏥 系统健康检查")
        print("=" * 50)

        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        print(f"CPU使用率: {cpu_percent:.1f}%")

        # 内存使用率
        memory = psutil.virtual_memory()
        print(f"内存使用: {memory.percent:.1f}% ({memory.used/1024/1024/1024:.1f}GB/{memory.total/1024/1024/1024:.1f}GB)")

        # 磀查是否有异常进程
        python_processes = self.get_python_processes()
        high_memory_procs = [p for p in python_processes if p['memory_mb'] > 200]
        high_cpu_procs = [p for p in python_processes if p['cpu_percent'] > 50]

        if high_memory_procs:
            print(f"\n⚠️  高内存使用进程 ({len(high_memory_procs)}个):")
            for proc in high_memory_procs:
                print(f"   PID {proc['pid']}: {proc['memory_mb']:.1f}MB")

        if high_cpu_procs:
            print(f"\n⚠️  高CPU使用进程 ({len(high_cpu_procs)}个):")
            for proc in high_cpu_procs:
                print(f"   PID {proc['pid']}: {proc['cpu_percent']:.1f}%")

        if not high_memory_procs and not high_cpu_procs:
            print("\n✅ 所有进程运行正常")

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='Athena工作平台后台任务管理器')
    parser.add_argument('--status', action='store_true', help='显示进程状态')
    parser.add_argument('--stop', action='store_true', help='停止不必要的任务')
    parser.add_argument('--check', action='store_true', help='检查系统健康')
    parser.add_argument('--cleanup', action='store_true', help='清理所有相关进程')
    parser.add_argument('--kill', type=int, help='停止指定PID的进程')

    args = parser.parse_args()

    manager = TaskManager()

    try:
        if args.status or not any([args.stop, args.check, args.cleanup, args.kill]):
            manager.show_processes()

        if args.check:
            manager.check_system_health()

        if args.stop:
            manager.stop_unnecessary_tasks(dry_run=False)

        if args.cleanup:
            print("🧹 清理所有相关进程")
            print("⚠️ 这将停止所有Athena相关的Python进程！")
            confirm = input("确认继续吗？(y/N): ").lower().strip()

            if confirm == 'y':
                python_processes = manager.get_python_processes()
                if python_processes:
                    for proc in python_processes:
                        manager.stop_process(proc['pid'], force=True)
                    print(f"✅ 已清理 {len(python_processes)} 个进程")
                else:
                    print("✅ 没有发现相关进程")

        if args.kill:
            manager.stop_process(args.kill, force=True)

    except KeyboardInterrupt:
        print("\n👋 操作已取消")
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()