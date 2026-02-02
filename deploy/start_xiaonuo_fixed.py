#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小诺系统启动器 - 修复版
解决了无限循环和EOF错误问题
"""

import sys
import os
import signal
import asyncio
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def signal_handler(sig, frame):
    """处理Ctrl+C信号"""
    print("\n\n👋 收到退出信号，正在安全关闭...")
    sys.exit(0)

def check_environment():
    """检查运行环境"""
    print("🔍 检查运行环境...")

    # 检查Python版本
    if sys.version_info < (3, 7):
        print("❌ 错误: 需要Python 3.7或更高版本")
        return False

    # 检查必要目录
    required_dirs = ['core', 'data', 'logs']
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            print(f"📁 创建目录: {dir_name}")
            os.makedirs(dir_name, exist_ok=True)

    # 检查核心模块
    try:
        from core.xiaonuo_hybrid_architecture import HybridArchitectureController
        print("✅ 核心模块检查通过")
    except ImportError as e:
        print(f"❌ 核心模块导入失败: {e}")
        return False

    return True

def show_menu():
    """显示启动菜单"""
    print("\n" + "="*50)
    print("🌸 小诺混合架构系统启动器")
    print("="*50)
    print("1. 🎯 交互模式 - 通过命令行与小诺交互")
    print("2. 🧪 测试模式 - 运行系统测试")
    print("3. 🚀 Web服务模式 - 启动Web界面服务")
    print("4. 📊 状态检查 - 检查系统状态")
    print("5. 👋 退出")
    print("-"*50)

def interactive_mode():
    """交互模式启动"""
    print("\n🎯 启动交互模式...")
    print("💡 提示:")
    print("  - 输入 'help' 查看可用命令")
    print("  - 输入 'exit' 或 'quit' 退出系统")
    print("  - 按 Ctrl+C 强制退出")
    print("")

    try:
        # 导入主程序
        from xiaonuo_hybrid_main import XiaonuoHybridSystem

        # 创建并启动系统
        system = XiaonuoHybridSystem()

        # 运行异步主循环
        asyncio.run(system.start())

    except ImportError as e:
        print(f"❌ 无法导入主程序: {e}")
        return False
    except KeyboardInterrupt:
        print("\n\n👋 再见！小诺会想您的...")
        return True
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return False

    return True

def test_mode():
    """测试模式"""
    print("\n🧪 运行系统测试...")

    try:
        import test_hybrid_system
        print("✅ 测试模块导入成功")
        # 这里可以添加具体的测试逻辑
        print("📋 系统测试功能待完善")
        return True
    except ImportError as e:
        print(f"❌ 测试模块导入失败: {e}")
        return False

def web_mode():
    """Web服务模式"""
    print("\n🚀 启动Web服务模式...")
    print("📋 Web服务功能待开发")
    return True

def status_check():
    """状态检查"""
    print("\n📊 检查系统状态...")

    # 检查数据库
    try:
        from core.xiaonuo_basic_operations import DatabaseManager
        db = DatabaseManager()
        databases = ['performance_metrics.db', 'baochen_finance.db', 'xiaonuo_life.db', 'xiaonuo_knowledge.db']

        for db_name in databases:
            conn = db.get_connection(db_name)
            print(f"✅ {db_name} - 正常")
            conn.close()

    except Exception as e:
        print(f"❌ 数据库检查失败: {e}")

    # 检查日志
    if os.path.exists('logs'):
        log_files = list(Path('logs').glob('*.log'))
        if log_files:
            print(f"📝 找到 {len(log_files)} 个日志文件")
            for log_file in log_files[-3:]:  # 显示最新的3个日志
                size = log_file.stat().st_size
                print(f"   - {log_file.name} ({size} bytes)")
        else:
            print("📝 暂无日志文件")

    print("\n✅ 状态检查完成")
    return True

def get_user_choice():
    """获取用户选择，支持命令行参数"""
    # 检查命令行参数
    if len(sys.argv) > 1:
        try:
            return int(sys.argv[1])
        except ValueError:
            print(f"⚠️ 无效的命令行参数: {sys.argv[1]}")

    # 交互式获取选择
    max_attempts = 3
    attempt = 0

    while attempt < max_attempts:
        try:
            choice = input("\n请选择启动模式 (1-5): ").strip()
            if not choice:
                continue

            choice_num = int(choice)
            if 1 <= choice_num <= 5:
                return choice_num
            else:
                print("❌ 请输入 1-5 之间的数字")

        except ValueError:
            print("❌ 请输入有效的数字")
        except (EOFError, KeyboardInterrupt):
            print("\n👋 检测到退出信号，返回主菜单...")
            return 5

        attempt += 1
        print(f"尝试次数: {attempt}/{max_attempts}")

    print("⚠️ 达到最大尝试次数，将退出")
    return 5

def main():
    """主函数"""
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)

    print("🌸 小诺系统启动器 - 修复版")
    print("=" * 30)

    # 检查环境
    if not check_environment():
        print("❌ 环境检查失败，无法启动")
        return 1

    while True:
        try:
            show_menu()
            choice = get_user_choice()

            if choice == 1:
                interactive_mode()
            elif choice == 2:
                test_mode()
            elif choice == 3:
                web_mode()
            elif choice == 4:
                status_check()
            elif choice == 5:
                print("\n👋 再见！")
                return 0
            else:
                print("❌ 无效选择")

        except KeyboardInterrupt:
            print("\n\n👋 收到退出信号，正在退出...")
            return 0
        except Exception as e:
            print(f"❌ 发生未预期的错误: {e}")

        # 非交互模式下只执行一次
        if len(sys.argv) > 1:
            break

        input("\n按回车键继续...")

if __name__ == "__main__":
    sys.exit(main())