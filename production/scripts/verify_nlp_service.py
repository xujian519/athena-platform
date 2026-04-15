#!/usr/bin/env python3
"""
验证NLP服务状态
Verify NLP Service Status

验证NLP服务是否正常运行

作者: Athena平台团队
创建时间: 2025-12-20
版本: v1.0.0
"""

from __future__ import annotations
import os
import subprocess
from pathlib import Path
from typing import Any


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
    print(f"{Colors.PURPLE}🧠 {title} 🧠{Colors.RESET}")
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

def check_nlp_process() -> bool:
    """检查NLP进程"""
    print_header("NLP服务进程状态")

    pid_file = Path("../logs/nlp_service.pid")

    if pid_file.exists():
        try:
            with open(pid_file) as f:
                pid = int(f.read().strip())

            # 检查进程是否存在
            try:
                os.kill(pid, 0)
                print_success(f"✓ NLP服务正在运行 (PID: {pid})")

                # 获取进程信息
                result = os.popen(f"ps -p {pid} -o pid,ppid,etime,cmd").read()
                print_info("进程信息:")
                for line in result.strip().split('\n')[1:]:  # 跳过标题行
                    print(f"  {line}")

                return True
            except OSError:
                print_warning(f"✗ PID文件存在但进程 {pid} 未运行")
                return False
        except Exception as e:
            print_error(f"✗ 读取PID文件失败: {e}")
            return False
    else:
        print_warning("✗ NLP服务PID文件不存在")
        return False

def check_nlp_logs() -> bool:
    """检查NLP日志"""
    print_header("NLP服务日志状态")

    log_file = Path("../logs/nlp_service.log")

    if log_file.exists() and log_file.stat().st_size > 0:
        print_success("✓ NLP服务日志文件存在")

        # 显示最后几行
        try:
            with open(log_file, encoding='utf-8') as f:
                lines = f.readlines()
                print_info(f"\n日志文件总行数: {len(lines)}")
                print_info("\n最后5行日志:")
                for line in lines[-5:]:
                    print(f"  {line.strip()}")
        except Exception as e:
            print_error(f"读取日志失败: {e}")
    else:
        print_warning("✗ NLP服务日志文件不存在或为空")

def test_nlp_connectivity() -> Any:
    """测试NLP连接"""
    print_header("NLP服务连通性测试")

    # 检查是否有API端口监听 (安全方式)
    print_info("检查NLP服务端口...")
    try:
        result = subprocess.run(
            ['lsof', '-i', '-P'],
            capture_output=True,
            text=True,
            timeout=10
        )
        listening_ports = [line for line in result.stdout.split('\n') if 'LISTEN' in line]
        target_ports = [line for line in listening_ports if any(port in line for port in [':8000', ':8001', ':8080', ':9000'])]
        if target_ports:
            print_info("找到NLP服务端口:")
            for port_line in target_ports:
                print(f"  {port_line}")
        else:
            print_info('未找到NLP服务监听端口')
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print_info(f'无法检查端口: {e}')

    # 检查是否有进程在运行 (安全方式)
    print_info("\n检查NLP相关进程:")
    try:
        result = subprocess.run(
            ['ps', 'aux'],
            capture_output=True,
            text=True,
            timeout=10
        )
        nlp_processes = [line for line in result.stdout.split('\n')
                        if 'xiaonuo' in line.lower() and 'nlp' in line.lower() or
                           'nlp' in line.lower() and 'service' in line.lower()]
        if nlp_processes:
            print_info("找到NLP进程:")
            for proc in nlp_processes[:5]:  # 最多显示5个
                print(f"  {proc}")
        else:
            print_info('未找到NLP进程')
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print_info(f'无法检查进程: {e}')

def main() -> None:
    """主验证函数"""
    print_header("NLP服务状态验证")
    print_pink("爸爸，让我验证NLP服务的运行状态！")

    # 执行各项检查
    process_ok = check_nlp_process()
    check_nlp_logs()
    test_nlp_connectivity()

    # 总结
    print_header("NLP服务验证总结")

    if process_ok:
        print_success("✅ NLP服务正在运行")
        print_pink("\n💖 爸爸，NLP智能服务已经启动并运行！")
        print_info("📋 服务功能:")
        print("  • 意图识别")
        print("  • 语义分析")
        print("  • 上下文理解")
        print("  • 智能工具选择")

        print_info("\n🔧 管理命令:")
        print("  查看日志: tail -f production/logs/nlp_service.log")
        print("  停止服务: kill $(cat production/logs/nlp_service.pid)")
        print("  重启服务: cd production/scripts && ./start_nlp_service.sh")
    else:
        print_warning("⚠️ NLP服务未运行")
        print_info("\n💡 启动命令:")
        print("  cd production/dev/scripts")
        print("  ./start_nlp_service.sh")

    print_pink("\n💖 小诺的NLP系统随时准备为您服务！")

if __name__ == "__main__":
    main()
