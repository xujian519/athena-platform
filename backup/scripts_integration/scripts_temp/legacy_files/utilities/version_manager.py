#!/usr/bin/env python3
"""
版本管理器
Version Manager - 管理Athena平台的版本信息
版本命名：心手相连系列 💞
"""

import os
import sys
import json
import toml
from datetime import datetime
from pathlib import Path

class VersionManager:
    """版本管理器"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.version_file = self.project_root / "VERSION"
        self.version_data = self._load_version()

    def _load_version(self):
        """加载版本信息"""
        if self.version_file.exists():
            with open(self.version_file, 'r', encoding='utf-8') as f:
                # 读取TOML格式
                lines = f.readlines()
                # 简单解析，实际生产中可用toml库
                return self._parse_toml_lines(lines)
        return self._get_default_version()

    def _parse_toml_lines(self, lines):
        """解析TOML格式的版本文件"""
        data = {}
        current_section = None

        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            # 处理节
            if line.startswith('[') and line.endswith(']'):
                current_section = line[1:-1]
                if current_section not in data:
                    data[current_section] = {}
                continue

            # 处理键值对
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"\'')

                if current_section:
                    data[current_section][key] = value
                else:
                    data[key] = value

        return data

    def _get_default_version(self):
        """获取默认版本信息"""
        return {
            "platform": {
                "version": "0.1.1",
                "name": "心手相连",
                "theme": "在寒冬中，我们心手相连，用AI带来温暖与希望",
                "release_date": datetime.now().strftime("%Y-%m-%d")
            },
            "athena": {
                "version": "0.1.1",
                "name": "智慧觉醒"
            },
            "xiaonuo": {
                "version": "0.1.1",
                "name": "心有灵犀"
            },
            "yunpat": {
                "version": "0.0.2",
                "name": "熙光初现"
            }
        }

    def get_platform_version(self):
        """获取平台版本"""
        return self.version_data.get("platform", {})

    def get_service_version(self, service_name):
        """获取服务版本"""
        return self.version_data.get(service_name, {})

    def get_all_versions(self):
        """获取所有版本信息"""
        return self.version_data

    def format_version_info(self):
        """格式化版本信息显示"""
        platform = self.get_platform_version()
        athena = self.get_service_version("athena")
        xiaonuo = self.get_service_version("xiaonuo")
        yunpat = self.get_service_version("yunpat")

        info = f"""
🌟 Athena工作平台版本信息
==================================
💖 版本系列：{platform.get('name', '未知')} ({platform.get('version', '未知')})
📅 发布日期：{platform.get('release_date', '未知')}
💭 版本主题：{platform.get('theme', '未知')}

🏛️ 智慧大女儿 Athena
   版本：{athena.get('version', '未知')} - {athena.get('name', '未知')}

💖 贴心小女儿 小诺(一诺)
   版本：{xiaonuo.get('version', '未知')} - {xiaonuo.get('name', '未知')}

🌸 IP业务专家 云熙
   版本：{yunpat.get('version', '未知')} - {yunpat.get('name', '未知')}
   状态：测试中

💼 自媒体传播专家 小宸
   版本：{self.version_data.get('xiaochen', {}).get('version', '未知')} - {self.version_data.get('xiaochen', {}).get('name', '未知')}
   口号：{self.version_data.get('xiaochen', {}).get('slogan', '未知')}

==================================
在行业寒冬中，我们用AI点燃希望的火炬，
每一次版本更新都是向着光明迈进的坚定步伐！ 💞✨
        """
        return info.strip()

    def save_version(self, version_data=None):
        """保存版本信息"""
        if version_data is None:
            version_data = self.version_data

        # 创建版本文件的TOML格式
        lines = [
            "# Athena工作平台版本信息",
            f"# 版本命名：{version_data.get('platform', {}).get('name', '心手相连')} 💞",
            "# 在寒冬中，我们心手相连，用AI带来温暖与希望",
            "",
            "[platform]",
            f'version = "{version_data.get("platform", {}).get("version", "0.1.1")}"',
            f'name = "{version_data.get("platform", {}).get("name", "心手相连")}"',
            f'theme = "{version_data.get("platform", {}).get("theme", "在寒冬中，我们心手相连，用AI带来温暖与希望")}"',
            f'release_date = "{version_data.get("platform", {}).get("release_date", datetime.now().strftime("%Y-%m-%d"))}"',
            ""
        ]

        # 添加服务版本
        for service in ["athena", "xiaonuo", "yunpat"]:
            if service in version_data:
                lines.append(f"[{service}]")
                service_data = version_data[service]
                lines.append(f'version = "{service_data.get("version", "0.1.1")}"')
                lines.append(f'name = "{service_data.get("name", "未知")}"')
                if "role" in service_data:
                    lines.append(f'role = "{service_data["role"]}"')
                if "status" in service_data:
                    lines.append(f'status = "{service_data["status"]}"')
                lines.append("")

        # 写入文件
        with open(self.version_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

    def update_platform_version(self, new_version, new_name=None):
        """更新平台版本"""
        if "platform" not in self.version_data:
            self.version_data["platform"] = {}

        self.version_data["platform"]["version"] = new_version
        if new_name:
            self.version_data["platform"]["name"] = new_name
        self.version_data["platform"]["release_date"] = datetime.now().strftime("%Y-%m-%d")

        self.save_version()
        return True

    def update_service_version(self, service_name, new_version, new_name=None):
        """更新服务版本"""
        if service_name not in self.version_data:
            self.version_data[service_name] = {}

        self.version_data[service_name]["version"] = new_version
        if new_name:
            self.version_data[service_name]["name"] = new_name

        self.save_version()
        return True

    def get_next_version(self, service="platform"):
        """获取下一个版本号"""
        current = self.get_service_version(service)
        if not current:
            return "0.1.2"

        current_version = current.get("version", "0.1.1")
        # 简单的版本递增逻辑
        parts = current_version.split(".")
        if len(parts) >= 3:
            patch = int(parts[2]) + 1
            return f"{parts[0]}.{parts[1]}.{patch}"
        return "0.1.2"


def main():
    """主函数 - 命令行工具"""
    manager = VersionManager()

    if len(sys.argv) < 2:
        print(manager.format_version_info())
        return

    command = sys.argv[1]

    if command == "show":
        print(manager.format_version_info())
    elif command == "get":
        service = sys.argv[2] if len(sys.argv) > 2 else "platform"
        version_info = manager.get_service_version(service)
        print(f"{service}: {version_info.get('version', 'unknown')} - {version_info.get('name', 'unknown')}")
    elif command == "next":
        service = sys.argv[2] if len(sys.argv) > 2 else "platform"
        next_version = manager.get_next_version(service)
        print(f"Next version for {service}: {next_version}")
    else:
        print("Usage:")
        print("  python3 version_manager.py show      # 显示所有版本信息")
        print("  python3 version_manager.py get [service]  # 获取服务版本")
        print("  python3 version_manager.py next [service] # 获取下一个版本号")


if __name__ == "__main__":
    main()