#!/usr/bin/env python3
"""
小诺快速启动脚本
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

# 设置工作目录
os.chdir(Path(__file__).parent)

# 颜色定义
GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

def print_banner() -> Any:
    print(f"""
{BLUE}╔═════════════════════════════════════════════════════════════╗
║                                                             ║
║  {GREEN}🌸 小诺智能助手启动器 - Xiaonuo Launcher 🌸{BLUE}               ║
║                                                             ║
╚═════════════════════════════════════════════════════════════╝{RESET}

{YELLOW}请选择启动模式:{RESET}
  1. {GREEN}交互模式{RESET}    - 完整交互，与诺诺对话
  2. {BLUE}演示模式{RESET}    - 快速查看系统状态
  3. {YELLOW}信息模式{RESET}    - 只显示身份信息
  4. {RED}退出{RESET}
""")

def main() -> None:
    print_banner()

    try:
        choice = input("请输入选项 (1-4): ").strip()

        if choice == "1":
            print(f"\n{GREEN}启动交互模式...{RESET}")
            subprocess.run([sys.executable, "services/intelligent-collaboration/xiaonuo_main.py"])
        elif choice == "2":
            print(f"\n{BLUE}启动演示模式...{RESET}")
            subprocess.run([sys.executable, "services/intelligent-collaboration/xiaonuo_main.py", "--mode", "demo"])
        elif choice == "3":
            print(f"\n{YELLOW}显示身份信息...{RESET}")
            subprocess.run([sys.executable, "services/intelligent-collaboration/xiaonuo_main.py", "--info"])
        elif choice == "4":
            print(f"\n{RED}再见！{RESET}")
            sys.exit(0)
        else:
            print(f"\n{RED}无效选项！{RESET}")
            main()

    except KeyboardInterrupt:
        print(f"\n\n{GREEN}爸爸再见！诺诺会想您的~{RESET}")
    except EOFError:
        print(f"\n\n{GREEN}输入结束，诺诺准备休息...{RESET}")

if __name__ == "__main__":
    main()
