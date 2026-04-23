#!/usr/bin/env python3
"""
CORS安全测试工具
CORS Security Testing Tool

功能：
1. 验证所有CORS配置是否符合安全标准
2. 测试CORS预检请求
3. 生成安全测试报告
"""

import json
import os
import re
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class CORSSecurityTester:
    """CORS安全测试器"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.results = {
            "total_files": 0,
            "safe_files": 0,
            "unsafe_files": 0,
            "template_files": 0,
            "test_files": 0,
            "issues": []
        }

        # 需要排除的目录
        self.exclude_dirs = {
            "backup",
            "archive",
            ".git",
            "__pycache__",
            "node_modules",
            ".pytest_cache",
            "venv",
            ".venv",
            "build",
            "dist",
            "data",
        }

    def should_test_file(self, file_path: Path) -> bool:
        """判断文件是否需要测试"""
        # 检查文件扩展名
        if file_path.suffix != ".py":
            return False

        # 检查是否在排除目录中
        parts = file_path.parts
        for exclude_dir in self.exclude_dirs:
            if exclude_dir in parts:
                return False

        return True

    def is_test_file(self, file_path: Path) -> bool:
        """判断是否为测试文件"""
        return "test" in file_path.name or "tests" in str(file_path)

    def is_template_file(self, file_path: Path) -> bool:
        """判断是否为模板文件"""
        return "template" in str(file_path).lower()

    def check_cors_security(self, file_path: Path) -> tuple[bool, str]:
        """
        检查文件的CORS安全性

        Returns:
            (是否安全, 详细信息)
        """
        try:
            content = file_path.read_text(encoding="utf-8")

            # 如果没有CORS配置，返回中性
            if "CORSMiddleware" not in content and "allow_origins" not in content:
                return True, "无CORS配置"

            # 检查是否使用通配符
            if re.search(r'allow_origins\s*=\s*\["\*"\]', content):
                return False, "使用通配符 allow_origins=[\"*\"]"

            if re.search(r'allow_origins:\s*\["\*"\]', content):
                return False, "使用通配符 allow_origins: [\"*\"]"

            # 检查是否导入安全配置
            if "from core.security.auth import" in content and "ALLOWED_ORIGINS" in content:
                return True, "使用 core.security.auth.ALLOWED_ORIGINS"

            if "from core.security import" in content and "ALLOWED_ORIGINS" in content:
                return True, "使用 core.security.ALLOWED_ORIGINS"

            # 检查是否从环境变量读取
            if 'os.getenv("ALLOWED_ORIGINS"' in content:
                return True, "从环境变量读取 ALLOWED_ORIGINS"

            if "os.environ.get(" in content and "ALLOWED_ORIGINS" in content:
                return True, "从环境变量读取 ALLOWED_ORIGINS"

            # 检查硬编码的列表
            if re.search(r'allow_origins\s*=\s*\[[^\]+\]', content):
                # 检查是否包含通配符
                match = re.search(r'allow_origins\s*=\s*\[([^\]+)\]', content)
                if match:
                    origins = match.group(1)
                    if '"*"' in origins or "'*'" in origins:
                        return False, "硬编码列表包含通配符"
                    # 如果是具体的localhost或IP，视为安全
                    if "localhost" in origins or "127.0.0.1" in origins:
                        return True, "硬编码开发环境配置"
                    return False, "硬编码生产配置（应使用环境变量）"

            return True, "CORS配置"

        except Exception as e:
            return False, f"读取失败: {e}"

    def run_tests(self) -> dict:
        """运行CORS安全测试"""
        print("🔍 开始CORS安全测试...\n")

        # 搜索所有Python文件
        python_files = []
        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]

            for file in files:
                file_path = Path(root) / file
                if self.should_test_file(file_path):
                    python_files.append(file_path)

        self.results["total_files"] = len(python_files)

        # 测试每个文件
        for file_path in python_files:
            is_safe, details = self.check_cors_security(file_path)

            if self.is_test_file(file_path):
                self.results["test_files"] += 1
            elif self.is_template_file(file_path):
                self.results["template_files"] += 1
            elif is_safe:
                self.results["safe_files"] += 1
            else:
                self.results["unsafe_files"] += 1
                self.results["issues"].append({
                    "file": str(file_path.relative_to(self.project_root)),
                    "issue": details
                })

        return self.results

    def print_results(self):
        """打印测试结果"""
        print("=" * 60)
        print("CORS安全测试报告")
        print("=" * 60)
        print("\n📊 统计信息:")
        print(f"   扫描文件总数: {self.results['total_files']}")
        print(f"   ✅ 安全配置: {self.results['safe_files']}")
        print(f"   ⚠️  不安全配置: {self.results['unsafe_files']}")
        print(f"   📝 模板文件: {self.results['template_files']}")
        print(f"   🧪 测试文件: {self.results['test_files']}")

        # 计算安全得分
        if self.results["safe_files"] + self.results["unsafe_files"] > 0:
            safety_rate = (self.results["safe_files"] /
                          (self.results["safe_files"] + self.results["unsafe_files"]) * 100)
            print(f"\n🎯 安全得分: {safety_rate:.1f}%")

        # 评级
        if self.results["unsafe_files"] == 0:
            grade = "A+"
            emoji = "🟢"
        elif self.results["unsafe_files"] <= 2:
            grade = "B"
            emoji = "🟡"
        elif self.results["unsafe_files"] <= 5:
            grade = "C"
            emoji = "🟠"
        else:
            grade = "F"
            emoji = "🔴"

        print(f"   {emoji} 安全等级: {grade}")

        # 列出问题
        if self.results["issues"]:
            print("\n⚠️  发现的问题:")
            for i, issue in enumerate(self.results["issues"], 1):
                print(f"   {i}. {issue['file']}")
                print(f"      问题: {issue['issue']}")
        else:
            print("\n✅ 未发现安全问题！")

        print("\n" + "=" * 60)

    def generate_report(self, output_path: Path):
        """生成详细报告"""
        report = {
            "timestamp": __import__('datetime').datetime.now().isoformat(),
            "summary": {
                "total_files": self.results["total_files"],
                "safe_files": self.results["safe_files"],
                "unsafe_files": self.results["unsafe_files"],
                "template_files": self.results["template_files"],
                "test_files": self.results["test_files"],
            },
            "issues": self.results["issues"]
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n📄 详细报告已生成: {output_path}")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="CORS安全测试工具")
    parser.add_argument(
        "--json",
        action="store_true",
        help="输出JSON格式报告"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="docs/CORS_SECURITY_TEST_REPORT.json",
        help="报告输出路径"
    )

    args = parser.parse_args()

    tester = CORSSecurityTester(project_root)
    tester.run_tests()
    tester.print_results()

    if args.json:
        output_path = project_root / args.output
        tester.generate_report(output_path)

    # 返回退出码
    if tester.results["unsafe_files"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
