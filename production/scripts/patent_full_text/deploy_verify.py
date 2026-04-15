#!/usr/bin/env python3
"""
专利全文处理系统 - 部署验证脚本
Patent Full Text Processing System - Deployment Verification

验证小诺调度、按需启动的完整部署流程

作者: Athena平台团队
创建时间: 2025-12-25
"""

from __future__ import annotations
import sys
import time
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


class DeploymentVerifier:
    """部署验证器"""

    def __init__(self):
        """初始化验证器"""
        self.root_dir = Path(__file__).parent
        self.results = []

    def verify_all(self) -> bool:
        """
        执行所有验证

        Returns:
            是否全部通过
        """
        print("\n" + "="*70)
        print("  专利全文处理系统 - 部署验证")
        print("="*70)
        print(f"验证时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

        checks = [
            ("文件结构", self._verify_file_structure),
            ("配置文件", self._verify_config_files),
            ("Docker配置", self._verify_docker_config),
            ("工具注册", self._verify_tool_registration),
            ("服务管理器", self._verify_service_manager),
            ("小诺集成", self._verify_xiaonuo_integration),
        ]

        all_passed = True
        for name, check_func in checks:
            print(f"\n{'='*70}")
            print(f"  验证: {name}")
            print(f"{'='*70}")
            try:
                passed = check_func()
                self.results.append((name, passed))
                if not passed:
                    all_passed = False
            except Exception as e:
                print(f"❌ 验证异常: {e}")
                self.results.append((name, False))
                all_passed = False

        # 打印总结
        self._print_summary(all_passed)

        return all_passed

    def _verify_file_structure(self) -> bool:
        """验证文件结构"""
        required_files = [
            "config/.env",
            "config/.env.template",
            "config/.env.development",
            "config/.env.testing",
            "config/infrastructure/infrastructure/nginx/nginx.conf",
            "docker-compose.yml",
            "service_manager.py",
            "config_manager.py",
            "health_check.py",
            "DEPLOYMENT.md",
            "CONFIG_SUMMARY.md"
        ]

        all_exist = True
        for file_path in required_files:
            full_path = self.root_dir / file_path
            exists = full_path.exists()
            icon = "✅" if exists else "❌"
            print(f"{icon} {file_path}")
            if not exists:
                all_exist = False

        return all_exist

    def _verify_config_files(self) -> bool:
        """验证配置文件"""
        print("\n📋 检查配置文件...")

        # 检查环境变量文件
        env_file = self.root_dir / "config" / ".env"
        if not env_file.exists():
            print("❌ .env文件不存在")
            return False

        # 读取配置
        with open(env_file, encoding='utf-8') as f:
            config_lines = f.readlines()

        # 检查关键配置
        required_configs = [
            "PATENT_ENV",
            "PATENT_VERSION",
            "QDRANT_COLLECTION_NAME",
            "NEBULA_SPACE_NAME"
        ]

        all_present = True
        for config in required_configs:
            present = any(config in line for line in config_lines)
            icon = "✅" if present else "❌"
            print(f"{icon} {config}")
            if not present:
                all_present = False

        return all_present

    def _verify_docker_config(self) -> bool:
        """验证Docker配置"""
        docker_compose = self.root_dir / "docker-compose.yml"

        if not docker_compose.exists():
            print("❌ docker-compose.yml不存在")
            return False

        with open(docker_compose) as f:
            content = f.read()

        # 检查服务配置
        required_services = ["qdrant", "nebula-graphd", "redis", "app"]

        all_present = True
        for service in required_services:
            present = service in content
            icon = "✅" if present else "❌"
            print(f"{icon} 服务: {service}")
            if not present:
                all_present = False

        return all_present

    def _verify_tool_registration(self) -> bool:
        """验证工具注册"""
        print("\n🔧 检查工具注册...")

        try:
            from tools.xiaonuo_patent_integration import get_xiaonuo_patent_registry

            registry = get_xiaonuo_patent_registry()
            tools = registry.get_tools()

            print(f"✅ 工具注册成功: {len(tools)}个工具")

            # 检查服务管理工具
            service_tools = [
                "start_patent_services",
                "stop_patent_services",
                "get_services_status",
                "restart_patent_services"
            ]

            for tool_name in service_tools:
                exists = tool_name in tools
                icon = "✅" if exists else "❌"
                print(f"{icon} {tool_name}")

            return all(t in tools for t in service_tools)

        except Exception as e:
            print(f"❌ 工具注册验证失败: {e}")
            return False

    def _verify_service_manager(self) -> bool:
        """验证服务管理器"""
        print("\n⚙️  检查服务管理器...")

        try:
            from service_manager import PatentServiceManager

            manager = PatentServiceManager()

            # 获取服务状态
            status = manager.get_status()

            print("📊 服务状态:")
            for service, info in status.items():
                icon = "✅" if info.status.value == "running" else "⭕"
                print(f"{icon} {service}: {info.status.value}")

            return True

        except Exception as e:
            print(f"❌ 服务管理器验证失败: {e}")
            return False

    def _verify_xiaonuo_integration(self) -> bool:
        """验证小诺集成"""
        print("\n🤖 检查小诺集成...")

        try:
            from tools.patent_full_text_tool import get_patent_tool

            tool = get_patent_tool()

            # 检查服务管理方法
            methods = [
                "start_services_on_demand",
                "stop_services",
                "get_services_status",
                "restart_services"
            ]

            all_exist = True
            for method_name in methods:
                exists = hasattr(tool, method_name)
                icon = "✅" if exists else "❌"
                print(f"{icon} {method_name}")
                if not exists:
                    all_exist = False

            return all_exist

        except Exception as e:
            print(f"❌ 小诺集成验证失败: {e}")
            return False

    def _print_summary(self, all_passed: bool) -> None:
        """打印验证总结"""
        print(f"\n{'='*70}")
        print("  验证总结")
        print(f"{'='*70}")

        for name, passed in self.results:
            icon = "✅" if passed else "❌"
            print(f"{icon} {name}")

        print(f"{'='*70}")

        if all_passed:
            print("\n🎉 所有验证通过！系统已准备好部署。")
            print("\n📋 后续步骤:")
            print("  1. 初始化环境: python config_manager.py init --env production")
            print("  2. 启动服务: python service_manager.py start --service all")
            print("  3. 验证服务: python health_check.py")
        else:
            print("\n⚠️  部分验证未通过，请检查上述问题。")

        print(f"{'='*70}\n")


def main() -> None:
    """主函数"""
    verifier = DeploymentVerifier()
    success = verifier.verify_all()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
