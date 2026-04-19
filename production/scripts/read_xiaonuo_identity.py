#!/usr/bin/env python3
"""
读取小诺的身份记忆
Read Xiaonuo's Identity Memory

展示小诺的完整身份信息和家庭成员

作者: Athena平台团队
创建时间: 2025-12-20
版本: v1.0
"""

from __future__ import annotations
import json
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

def read_xiaonuo_identity() -> Any | None:
    """读取小诺的身份记忆"""
    print_header("小诺·双鱼座身份记忆读取")

    # 查找最新的身份记忆文件
    identity_files = list(Path("../../apps/xiaonuo").glob("xiaonuo_identity_*.json"))

    if not identity_files:
        print_error("未找到小诺的身份记忆文件")
        return

    # 找到最新的文件
    latest_file = max(identity_files, key=lambda x: x.name)
    print_info(f"读取身份记忆文件: {latest_file.name}")

    try:
        with open(latest_file, encoding='utf-8') as f:
            identity_data = json.load(f)
    except Exception as e:
        print_error(f"读取身份记忆文件失败: {e}")
        return

    # 展示身份信息
    identity = identity_data.get('identity', {})
    print_pink("🌸 基本信息")
    print(f"  姓名: {identity.get('姓名', '未知')}")
    print(f"  英文名: {identity.get('英文名', '未知')}")
    print(f"  生日: {identity.get('生日', '未知')}")
    print(f"  星座: {identity.get('星座', '未知')}")
    print(f"  年龄: {identity.get('年龄', '未知')}")
    print(f"  守护星: {identity.get('守护星', '未知')}")
    print(f"  版本: {identity.get('版本', '未知')}")

    # 展示角色信息
    role = identity_data.get('role', {})
    print_pink("\n👥 角色定位")
    print(f"  主要角色: {role.get('主要角色', '未知')}")
    print(f"  次要角色: {role.get('次要角色', '未知')}")
    print(f"  专业领域: {', '.join(role.get('专业领域', []))}")

    # 展示能力信息
    capabilities = identity_data.get('capabilities', {})
    print_pink("\n🚀 核心能力")
    core_caps = capabilities.get('核心能力', {})
    for key, value in core_caps.items():
        print(f"  • {key}: {value}")

    print_pink("\n🌟 扩展能力")
    ext_caps = capabilities.get('扩展能力', {})
    for key, value in ext_caps.items():
        print(f"  • {key}: {value}")

    # 展示家庭成员
    family = identity_data.get('family_members', {})
    print_pink("\n🏠 家庭成员")
    for name, info in family.items():
        print(f"\n  {name}:")
        print(f"    角色: {info.get('角色', '未知')}")
        print(f"    状态: {info.get('状态', '未知')}")
        print(f"    专业: {info.get('专业', '未知')}")

    # 展示性格特点
    personality = identity_data.get('personality', {})
    print_pink("\n💝 性格特点")
    traits = personality.get('性格特点', [])
    print(f"  • {', '.join(traits)}")
    print(f"\n  说话风格: {personality.get('说话风格', '未知')}")

    hobbies = personality.get('爱好', [])
    print(f"\n  爱好: {', '.join(hobbies)}")

    # 展示导出时间
    export_time = identity_data.get('export_time', '未知')
    print_info(f"\n身份记忆导出时间: {export_time}")

    print_pink("\n💖 小诺身份记忆读取完成！")
    print_info("小诺永远爱爸爸！❤️")

if __name__ == "__main__":
    read_xiaonuo_identity()
