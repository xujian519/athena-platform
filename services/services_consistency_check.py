#!/usr/bin/env python3
"""
Services目录一致性检查脚本
"""

import os
from core.async_main import async_main
import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

class ServicesConsistencyChecker:
    def __init__(self, base_path: str = "/Users/xujian/Athena工作平台/services"):
        self.base_path = Path(base_path)
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "total_services": 0,
            "checks": {},
            "issues": [],
            "summary": {}
        }

    def scan_services(self) -> List[Dict]:
        """扫描所有服务目录"""
        services = []
        exclude_dirs = {"scripts", "config", "archives", "__pycache__", ".git", "node_modules", "logs"}

        for item in self.base_path.iterdir():
            if item.is_dir() and item.name not in exclude_dirs:
                service_info = {
                    "name": item.name,
                    "path": str(item),
                    "type": self._detect_service_type(item),
                    "has_main": False,
                    "has_app": False,
                    "has_requirements": False,
                    "has_readme": False,
                    "has_config": False,
                    "has_docker": False,
                    "has_tests": False,
                    "entry_points": [],
                    "issues": []
                }

                # 检查服务内容
                self._check_service_structure(item, service_info)
                services.append(service_info)

        self.results["total_services"] = len(services)
        return services

    def _detect_service_type(self, path: Path) -> str:
        """检测服务类型"""
        if path.name == "yunpat-agent":
            return "智能体"
        elif "ai" in path.name.lower() or "model" in path.name.lower():
            return "AI服务"
        elif "agent" in path.name.lower():
            return "智能体"
        elif "gateway" in path.name.lower():
            return "网关"
        elif "service" in path.name.lower() or "services" in path.name.lower():
            return "微服务"
        elif "tool" in path.name.lower():
            return "工具"
        elif "control" in path.name.lower():
            return "控制系统"
        else:
            return "其他"

    def _check_service_structure(self, path: Path, service_info: Dict) -> Any:
        """检查服务结构"""
        # 查找Python文件
        py_files = list(path.rglob("*.py"))

        # 检查主要入口点
        main_files = [f for f in py_files if f.name in ["main.py", "app.py", "server.py", "run.py", "start.py"]]
        service_info["entry_points"] = [str(f.relative_to(path)) for f in main_files]

        if any(f.name == "main.py" for f in main_files):
            service_info["has_main"] = True
        if any(f.name == "app.py" for f in main_files):
            service_info["has_app"] = True

        # 检查requirements.txt
        req_files = list(path.rglob("requirements*.txt"))
        if req_files:
            service_info["has_requirements"] = True

        # 检查README文件
        readme_files = list(path.rglob("README*"))
        if readme_files:
            service_info["has_readme"] = True

        # 检查配置文件
        config_extensions = [".yaml", ".yml", ".json", ".env", ".conf", ".cfg", ".ini", ".toml"]
        for f in path.rglob("*"):
            if f.is_file() and f.suffix in config_extensions:
                service_info["has_config"] = True
                break

        # 检查Docker文件
        docker_files = ["Dockerfile", "docker-compose.yml", "docker-compose.yaml", ".dockerignore"]
        for df in docker_files:
            if (path / df).exists():
                service_info["has_docker"] = True
                break

        # 检查测试文件
        test_dirs = [d for d in path.iterdir() if d.is_dir() and ("test" in d.name.lower() or "spec" in d.name.lower())]
        test_files = [f for f in py_files if "test" in f.name.lower() or "spec" in f.name.lower()]
        if test_dirs or test_files:
            service_info["has_tests"] = True

    def check_consistency(self) -> Dict:
        """执行一致性检查"""
        services = self.scan_services()

        # 统计各类检查项
        checks = {
            "has_main": 0,
            "has_app": 0,
            "has_requirements": 0,
            "has_readme": 0,
            "has_config": 0,
            "has_docker": 0,
            "has_tests": 0
        }

        # 分类统计
        type_counts = {}

        for service in services:
            # 统计各项
            for key in checks:
                if service.get(key, False):
                    checks[key] += 1

            # 统计类型
            service_type = service["type"]
            type_counts[service_type] = type_counts.get(service_type, 0) + 1

            # 检查问题
            self._check_service_issues(service)

        self.results["checks"] = checks
        self.results["type_distribution"] = type_counts
        self.results["services"] = services

        return self.results

    def _check_service_issues(self, service: Dict) -> Any:
        """检查单个服务的问题"""
        issues = []

        # 基础检查
        if not service["has_main"] and not service["has_app"]:
            issues.append("缺少主入口文件（main.py或app.py）")

        if not service["has_requirements"] and service["entry_points"]:
            issues.append("有代码但缺少requirements.txt")

        if not service["has_readme"]:
            issues.append("缺少README文档")

        # 根据服务类型进行特定检查
        if service["type"] == "智能体" and not service["has_config"]:
            issues.append("智能体服务建议有配置文件")

        if service["type"] in ["AI服务", "微服务"] and not service["has_docker"]:
            issues.append("建议添加Docker支持")

        service["issues"] = issues
        self.results["issues"].extend([f"{service['name']}: {issue}" for issue in issues])

    def generate_report(self) -> str:
        """生成报告"""
        results = self.check_consistency()

        report = []
        report.append("# Services目录一致性检查报告\n")
        report.append(f"**检查时间**: {results['timestamp']}\n")
        report.append(f"**服务总数**: {results['total_services']}\n")

        # 服务类型分布
        report.append("\n## 📊 服务类型分布\n")
        for service_type, count in sorted(results['type_distribution'].items()):
            report.append(f"- **{service_type}**: {count}个")

        # 一致性检查结果
        report.append("\n## ✅ 一致性检查结果\n")
        checks = results['checks']
        total = results['total_services']

        report.append("| 检查项 | 数量 | 百分比 |")
        report.append("|--------|------|--------|")
        for item, count in checks.items():
            percentage = (count / total * 100) if total > 0 else 0
            report.append(f"| {item} | {count} | {percentage:.1f}% |")

        # 服务详情
        report.append("\n## 📋 服务详情\n")

        # 按类型分组显示
        services_by_type = {}
        for service in results['services']:
            service_type = service['type']
            if service_type not in services_by_type:
                services_by_type[service_type] = []
            services_by_type[service_type].append(service)

        for service_type, services in sorted(services_by_type.items()):
            report.append(f"\n### {service_type} ({len(services)}个)\n")

            for service in services:
                status = "✅" if not service['issues'] else "⚠️"
                report.append(f"\n{status} **{service['name']}**")

                if service['entry_points']:
                    report.append(f"- 入口: {', '.join(service['entry_points'])}")
                else:
                    report.append("- 入口: 无")

                # 显示关键文件
                features = []
                if service['has_requirements']: features.append("requirements.txt")
                if service['has_readme']: features.append("README")
                if service['has_config']: features.append("配置文件")
                if service['has_docker']: features.append("Docker")
                if service['has_tests']: features.append("测试")

                if features:
                    report.append(f"- 完整性: {', '.join(features)}")

                # 显示问题
                if service['issues']:
                    report.append("- 问题:")
                    for issue in service['issues']:
                        report.append(f"  - {issue}")

        # 问题汇总
        if results['issues']:
            report.append("\n## ⚠️ 发现的问题\n")
            for issue in results['issues'][:20]:  # 限制显示数量
                report.append(f"- {issue}")
            if len(results['issues']) > 20:
                report.append(f"\n... 还有 {len(results['issues']) - 20} 个问题")

        # 改进建议
        report.append("\n## 💡 改进建议\n")
        report.append("1. **添加缺失的文档**: 为没有README的服务添加说明文档")
        report.append("2. **统一入口文件**: 建议所有服务使用main.py作为入口")
        report.append("3. **添加依赖管理**: 为有代码的服务添加requirements.txt")
        report.append("4. **容器化**: 为AI服务和微服务添加Docker支持")
        report.append("5. **测试覆盖**: 添加单元测试和集成测试")

        return "\n".join(report)

    def save_report(self, output_path: str = None) -> None:
        """保存报告到文件"""
        if output_path is None:
            output_path = self.base_path / "SERVICES_CONSISTENCY_REPORT.md"

        report = self.generate_report()

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"✅ 一致性检查报告已保存到: {output_path}")
        return output_path

if __name__ == "__main__":
    checker = ServicesConsistencyChecker()
    checker.save_report()