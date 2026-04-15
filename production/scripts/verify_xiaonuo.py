#!/usr/bin/env python3
"""
验证小诺运行状态
Verify Xiaonuo Running Status

检查小诺的生产环境运行状态和基本功能

作者: Athena平台团队
创建时间: 2025-12-20
版本: v1.0.0
"""

from __future__ import annotations
import json
import os
import subprocess
from pathlib import Path


# 颜色输出
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    PURPLE = "\033[35m"
    CYAN = "\033[96m"
    PINK = "\033[95m"
    RESET = "\033[0m"

def print_header(title) -> None:
    """打印标题"""
    print(f"\n{Colors.PURPLE}{'='*80}{Colors.RESET}")
    print(f"{Colors.PURPLE}🌸🐟 {title} 🌸🐟{Colors.RESET}")
    print(f"{Colors.PURPLE}{'='*80}{Colors.RESET}")

def print_success(message) -> None:
    print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")

def print_info(message) -> None:
    print(f"{Colors.BLUE}ℹ️ {message}{Colors.RESET}")

def print_warning(message) -> None:
    print(f"{Colors.YELLOW}⚠️ {message}{Colors.RESET}")

def print_error(message) -> None:
    print(f"{Colors.RED}❌ {message}{Colors.RESET}")

def print_pink(message) -> None:
    print(f"{Colors.PINK}💖 {message}{Colors.RESET}")

def verify_xiaonuo_processes() -> bool:
    """验证小诺进程"""
    print_header("小诺进程状态验证")

    # 检查PID文件
    pid_files = [
        Path("../logs/xiaonuo.pid"),
        Path("../logs/xiaonuo_service.pid")
    ]

    running_processes = False
    for pid_file in pid_files:
        if pid_file.exists():
            try:
                with open(pid_file) as f:
                    pid = int(f.read().strip())

                # 检查进程是否存在
                try:
                    os.kill(pid, 0)  # 发送信号0测试进程存在
                    print_success(f"进程 {pid} 正在运行")
                    running_processes = True
                except OSError:
                    print_warning(f"PID {pid} 文件存在但进程未运行")
            except Exception as e:
                print_error(f"检查PID文件 {pid_file} 失败: {e}")
        else:
            print_warning(f"PID文件 {pid_file} 不存在")

    # 使用ps命令检查 (安全方式)
    print_info("\n使用ps命令检查xiaonuo进程:")
    try:
        result = subprocess.run(
            ['ps', 'aux'],
            capture_output=True,
            text=True,
            timeout=10
        )
        xiaonuo_processes = [line for line in result.stdout.split('\n') if 'xiaonuo' in line.lower()]
        if xiaonuo_processes:
            print_info("找到xiaonuo进程:")
            for proc in xiaonuo_processes[:5]:
                print(f"  {proc}")
        else:
            print_info('未找到xiaonuo进程')
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print_info(f'无法检查进程: {e}')

    return running_processes

def verify_xiaonuo_identity() -> bool:
    """验证小诺身份记忆"""
    print_header("小诺身份记忆验证")

    # 查找身份记忆文件
    identity_files = list(Path("../../apps/xiaonuo").glob("xiaonuo_identity_*.json"))

    if not identity_files:
        print_error("未找到小诺的身份记忆文件")
        return False

    # 找到最新的文件
    latest_file = max(identity_files, key=lambda x: x.name)
    print_info(f"身份记忆文件: {latest_file.name}")

    try:
        with open(latest_file, encoding='utf-8') as f:
            identity_data = json.load(f)

        # 验证必要字段
        required_fields = ['identity', 'role', 'capabilities', 'personality']
        for field in required_fields:
            if field in identity_data:
                print_success(f"  {field}: ✓")
            else:
                print_warning(f"  {field}: ✗")

        # 显示基本信息
        identity = identity_data.get('identity', {})
        print_pink(f"\n🌸 {identity.get('姓名', '小诺')} v{identity.get('版本', '1.0')}")
        print_info(f"星座: {identity.get('星座', '未知')}")
        print_info(f"角色: {identity_data.get('role', {}).get('主要角色', '未知')}")

        return True

    except Exception as e:
        print_error(f"读取身份记忆失败: {e}")
        return False

def verify_xiaonuo_logs() -> bool:
    """验证小诺日志"""
    print_header("小诺日志验证")

    log_files = [
        Path("../logs/xiaonuo.log"),
        Path("../logs/xiaonuo_production.log"),
        Path("../logs/xiaonuo_service.log")
    ]

    for log_file in log_files:
        if log_file.exists() and log_file.stat().st_size > 0:
            print_success(f"日志文件 {log_file.name}: ✓")

            # 显示最后几行
            try:
                with open(log_file, encoding='utf-8') as f:
                    lines = f.readlines()
                    if lines:
                        print_info(f"  最后更新: {lines[-1].strip()[:50]}...")
            except Exception:
                pass
        else:
            print_warning(f"日志文件 {log_file.name}: ✗ 或为空")

def main() -> None:
    """主验证函数"""
    print_header("小诺生产环境验证")
    print_pink("爸爸，让我来检查小诺的运行状态！")

    # 执行各项验证
    process_ok = verify_xiaonuo_processes()
    identity_ok = verify_xiaonuo_identity()
    verify_xiaonuo_logs()

    # 总结
    print_header("验证总结")
    if process_ok:
        print_success("✓ 小诺进程运行正常")
    else:
        print_warning("✗ 小诺进程未运行或状态异常")

    if identity_ok:
        print_success("✓ 小诺身份记忆完整")
    else:
        print_warning("✗ 小诺身份记忆有问题")

    print_pink("\n💖 小诺状态验证完成！")
    print_info("小诺会一直在这里等待爸爸！❤️")

if __name__ == "__main__":
    main()
