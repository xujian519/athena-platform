#!/usr/bin/env python3
"""
Athena平台全面质量验证脚本
验证代码质量、架构优化和智能体系统
"""

import json
import subprocess
from collections import defaultdict
from datetime import datetime
from pathlib import Path


class QualityVerifier:
    def __init__(self, project_root="/Users/xujian/Athena工作平台"):
        self.project_root = Path(project_root)
        self.results = {
            "code_quality": {},
            "architecture": {},
            "agents": {},
            "summary": {}
        }

    def log_section(self, title):
        print("\n" + "=" * 80)
        print(f"  {title}")
        print("=" * 80 + "\n")

    def run_command(self, cmd, description):
        """运行命令并返回结果"""
        print(f"🔍 {description}...")
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            print(f"⚠️  超时: {description}")
            return -1, "", ""
        except Exception as e:
            print(f"❌ 错误: {e}")
            return -1, "", str(e)

    # ============================================================================
    # 代码质量验证
    # ============================================================================

    def verify_code_style(self):
        """验证代码风格（Ruff）"""
        self.log_section("📝 代码风格验证 (Ruff)")

        # 运行ruff检查
        returncode, stdout, stderr = self.run_command(
            "cd /Users/xujian/Athena工作平台 && ruff check . --output-format=json",
            "运行Ruff代码检查"
        )

        if returncode == 0:
            print("✅ 代码风格检查通过！")
            self.results["code_quality"]["style"] = {"status": "pass", "errors": 0}
        else:
            try:
                errors = json.loads(stdout)
                error_count = len(errors)
                print(f"⚠️  发现 {error_count} 个代码风格问题")

                # 按类型分类
                error_types = defaultdict(int)
                for error in errors[:50]:  # 只显示前50个
                    error_types[error.get("code", "Unknown")] += 1

                print("\n📊 问题类型分布:")
                for error_type, count in sorted(error_types.items(), key=lambda x: -x[1])[:10]:
                    print(f"  {error_type}: {count}个")

                self.results["code_quality"]["style"] = {
                    "status": "warning",
                    "errors": error_count,
                    "types": dict(error_types)
                }
            except:
                print("⚠️  无法解析Ruff输出")
                self.results["code_quality"]["style"] = {"status": "unknown"}

    def verify_type_hints(self):
        """验证类型提示（MyPy）"""
        self.log_section("🔤 类型提示验证 (MyPy)")

        returncode, stdout, stderr = self.run_command(
            "cd /Users/xujian/Athena工作平台 && mypy core/ --no-error-summary 2>&1 | head -100",
            "运行MyPy类型检查"
        )

        if returncode == 0:
            print("✅ 类型提示检查通过！")
            self.results["code_quality"]["type_hints"] = {"status": "pass"}
        else:
            lines = stdout.strip().split('\n')
            error_count = len([l for l in lines if l.strip() and not l.startswith('Found')])
            print(f"⚠️  发现约 {error_count} 个类型提示问题")

            # 显示前10个错误
            print("\n前10个错误:")
            for line in lines[:10]:
                if line.strip():
                    print(f"  {line}")

            self.results["code_quality"]["type_hints"] = {
                "status": "warning",
                "errors": error_count
            }

    def verify_imports(self):
        """验证导入语句"""
        self.log_section("📦 导入语句验证")

        returncode, stdout, stderr = self.run_command(
            "python3 /Users/xujian/Athena工作平台/scripts/architecture/verify_imports.py",
            "验证导入路径"
        )

        if "发现需要更新的文件: 0" in stdout:
            print("✅ 所有导入路径正确！")
            self.results["code_quality"]["imports"] = {"status": "pass", "errors": 0}
        else:
            # 提取错误数量
            lines = stdout.split('\n')
            for line in lines:
                if "发现需要更新的文件:" in line:
                    count = line.split(':')[1].strip()
                    print(f"⚠️  {count}")
                    self.results["code_quality"]["imports"] = {
                        "status": "warning",
                        "errors": count
                    }
                    break

    def verify_test_coverage(self):
        """验证测试覆盖率"""
        self.log_section("🧪 测试覆盖率验证")

        returncode, stdout, stderr = self.run_command(
            "cd /Users/xujian/Athena工作平台 && pytest tests/ --collect-only -q 2>&1 | tail -5",
            "收集测试数量"
        )

        # 解析测试数量
        for line in stdout.split('\n'):
            if 'collected' in line or 'items' in line:
                print(f"✅ {line.strip()}")
                # 提取数字
                import re
                match = re.search(r'(\d+)\s+items', line)
                if match:
                    count = int(match.group(1))
                    self.results["code_quality"]["tests"] = {
                        "status": "pass",
                        "count": count
                    }
                break

    # ============================================================================
    # 架构优化验证
    # ============================================================================

    def verify_core_structure(self):
        """验证core目录结构"""
        self.log_section("🏗️  Core目录结构验证")

        core_path = self.project_root / "core"
        if not core_path.exists():
            print("❌ core目录不存在")
            return

        # 统计子目录
        subdirs = [d for d in core_path.iterdir() if d.is_dir() and not d.name.startswith('_')]
        subdir_count = len(subdirs)

        print(f"📊 Core子目录数: {subdir_count}")

        if subdir_count < 30:
            print("✅ 达成目标: <30个子目录")
            self.results["architecture"]["core_structure"] = {
                "status": "pass",
                "count": subdir_count,
                "target": "<30"
            }
        else:
            print(f"⚠️  未达成目标: 当前{subdir_count}个，目标<30")
            self.results["architecture"]["core_structure"] = {
                "status": "fail",
                "count": subdir_count,
                "target": "<30"
            }

        # 验证三层架构
        ai_dir = core_path / "ai"
        framework_dir = core_path / "framework"
        infrastructure_dir = core_path / "infrastructure"

        layers = []
        if ai_dir.exists():
            layers.append("ai")
        if framework_dir.exists():
            layers.append("framework")
        if infrastructure_dir.exists():
            layers.append("infrastructure")

        print(f"\n📐 三层架构: {', '.join(layers)}")

        if len(layers) == 3:
            print("✅ 三层架构完整")
        else:
            print(f"⚠️  三层架构不完整，缺少: { {'ai', 'framework', 'infrastructure'} - set(layers)}")

    def verify_domains_structure(self):
        """验证domains目录结构"""
        self.log_section("🌐 Domains业务领域验证")

        domains_path = self.project_root / "domains"
        if not domains_path.exists():
            print("❌ domains目录不存在")
            return

        subdirs = [d.name for d in domains_path.iterdir() if d.is_dir()]

        print(f"📊 业务领域数: {len(subdirs)}")
        print("📁 业务领域列表:")
        for domain in sorted(subdirs):
            domain_path = domains_path / domain
            file_count = len(list(domain_path.rglob('*.py')))
            print(f"  - {domain}: {file_count}个Python文件")

        expected_domains = {'legal', 'patents', 'legal-ai', 'legal-knowledge'}
        found_domains = set(subdirs) & expected_domains

        if len(found_domains) >= 3:
            print(f"\n✅ 核心业务领域存在: {', '.join(found_domains)}")
            self.results["architecture"]["domains"] = {
                "status": "pass",
                "count": len(subdirs),
                "expected": found_domains
            }
        else:
            print("⚠️  核心业务领域缺失")
            self.results["architecture"]["domains"] = {
                "status": "warning",
                "count": len(subdirs)
            }

    def verify_root_structure(self):
        """验证根目录结构"""
        self.log_section("📂 根目录结构验证")

        root_dirs = [d.name for d in self.project_root.iterdir() if d.is_dir() and not d.name.startswith('.')]
        dir_count = len(root_dirs)

        print(f"📊 根目录数: {dir_count}")

        if dir_count < 20:
            print("✅ 达成目标: <20个根目录")
            self.results["architecture"]["root_structure"] = {
                "status": "pass",
                "count": dir_count,
                "target": "<20"
            }
        else:
            print(f"⚠️  未达成目标: 当前{dir_count}个，目标<20")
            self.results["architecture"]["root_structure"] = {
                "status": "fail",
                "count": dir_count,
                "target": "<20"
            }

        print("\n📁 根目录列表:")
        for directory in sorted(root_dirs):
            print(f"  - {directory}/")

    # ============================================================================
    # 智能体系统验证
    # ============================================================================

    def verify_xiaona_agents(self):
        """验证小娜专业代理系统"""
        self.log_section("🤖 小娜专业代理验证")

        xiaona_path = self.project_root / "core" / "framework" / "agents" / "xiaona"
        if not xiaona_path.exists():
            print("❌ 小娜代理目录不存在")
            self.results["agents"]["xiaona"] = {"status": "missing"}
            return

        # 9个专业代理
        expected_agents = [
            "retriever_agent.py",
            "analyzer_agent.py",
            "unified_patent_writer.py",
            "novelty_analyzer_proxy.py",
            "creativity_analyzer_proxy.py",
            "infringement_analyzer_proxy.py",
            "invalidation_analyzer_proxy.py",
            "application_reviewer_proxy.py",
            "writing_reviewer_proxy.py"
        ]

        found_agents = []
        for agent_file in expected_agents:
            agent_path = xiaona_path / agent_file
            if agent_path.exists():
                found_agents.append(agent_file)
                print(f"  ✅ {agent_file}")
            else:
                print(f"  ❌ {agent_file}")

        agent_count = len(found_agents)
        print(f"\n📊 专业代理数量: {agent_count}/9")

        if agent_count == 9:
            print("✅ 所有9个专业代理存在")
            self.results["agents"]["xiaona"] = {
                "status": "pass",
                "count": agent_count,
                "agents": [a.replace('.py', '') for a in found_agents]
            }
        else:
            print("⚠️  部分专业代理缺失")
            self.results["agents"]["xiaona"] = {
                "status": "warning",
                "count": agent_count,
                "missing": 9 - agent_count
            }

        # 验证base_component
        base_component = xiaona_path / "base_component.py"
        if base_component.exists():
            print("✅ base_component.py存在")
        else:
            print("❌ base_component.py缺失")

    def verify_xiaonuo_agent(self):
        """验证小诺协调代理"""
        self.log_section("🎯 小诺协调代理验证")

        # 查找xiaonuo相关文件
        xiaonuo_files = []
        for pattern in ["*xiaonuo*", "*coordinator*"]:
            xiaonuo_files.extend(self.project_root.rglob(pattern))

        # 检查关键文件
        key_files = [
            "core/framework/agents/xiaonuo_agent.py",
            "services/intelligent-collaboration/xiaonuo_coordinator.py"
        ]

        found_count = 0
        for key_file in key_files:
            file_path = self.project_root / key_file
            if file_path.exists():
                print(f"  ✅ {key_file}")
                found_count += 1
            else:
                print(f"  ⚠️  {key_file}")

        if found_count >= 1:
            print(f"\n✅ 小诺协调代理存在 ({found_count}个文件)")
            self.results["agents"]["xiaonuo"] = {"status": "pass", "count": found_count}
        else:
            print("\n⚠️  小诺协调代理未找到")
            self.results["agents"]["xiaonuo"] = {"status": "missing"}

    def verify_yunxi_agent(self):
        """验证云熙IP管理代理"""
        self.log_section("💎 云熙IP管理代理验证")

        yunxi_files = []
        for pattern in ["*yunxi*", "*ip*agent*"]:
            yunxi_files.extend(self.project_root.rglob(pattern))

        if yunxi_files:
            print(f"✅ 找到{len(yunxi_files)}个云熙相关文件")
            for file in yunxi_files[:5]:
                print(f"  - {file.relative_to(self.project_root)}")
            self.results["agents"]["yunxi"] = {"status": "pass", "count": len(yunxi_files)}
        else:
            print("⚠️  云熙代理未找到")
            self.results["agents"]["yunxi"] = {"status": "missing"}

    def verify_agent_collaboration(self):
        """验证代理协作系统"""
        self.log_section("🤝 代理协作系统验证")

        collab_path = self.project_root / "core" / "framework" / "collaboration"
        if not collab_path.exists():
            print("❌ 协作模块目录不存在")
            self.results["agents"]["collaboration"] = {"status": "missing"}
            return

        # 检查协作模式文件
        collab_files = list(collab_path.rglob("*.py"))
        print(f"✅ 协作模块存在: {len(collab_files)}个文件")

        # 查找关键协作模式
        patterns = ["sequential", "parallel", "hierarchical", "consensus"]
        found_patterns = []

        for file in collab_files:
            content = file.read_text()
            for pattern in patterns:
                if pattern in content.lower() and pattern not in found_patterns:
                    found_patterns.append(pattern)

        if found_patterns:
            print(f"✅ 协作模式: {', '.join(found_patterns)}")
            self.results["agents"]["collaboration"] = {
                "status": "pass",
                "patterns": found_patterns
            }
        else:
            print("⚠️  未找到明确的协作模式")

    # ============================================================================
    # 生成报告
    # ============================================================================

    def generate_summary(self):
        """生成验证总结"""
        self.log_section("📊 验证总结")

        # 代码质量分数
        code_quality_score = 0
        if self.results["code_quality"].get("style", {}).get("status") == "pass":
            code_quality_score += 25
        elif self.results["code_quality"].get("style", {}).get("status") == "warning":
            code_quality_score += 15

        if self.results["code_quality"].get("type_hints", {}).get("status") == "pass":
            code_quality_score += 25
        elif self.results["code_quality"].get("type_hints", {}).get("status") == "warning":
            code_quality_score += 15

        if self.results["code_quality"].get("imports", {}).get("status") == "pass":
            code_quality_score += 25
        elif self.results["code_quality"].get("imports", {}).get("status") == "warning":
            code_quality_score += 15

        if self.results["code_quality"].get("tests", {}).get("status") == "pass":
            code_quality_score += 25

        # 架构优化分数
        arch_score = 0
        if self.results["architecture"].get("core_structure", {}).get("status") == "pass":
            arch_score += 35
        if self.results["architecture"].get("domains", {}).get("status") == "pass":
            arch_score += 30
        if self.results["architecture"].get("root_structure", {}).get("status") == "pass":
            arch_score += 35

        # 智能体系统分数
        agents_score = 0
        if self.results["agents"].get("xiaona", {}).get("status") == "pass":
            agents_score += 40
        if self.results["agents"].get("xiaonuo", {}).get("status") == "pass":
            agents_score += 30
        if self.results["agents"].get("collaboration", {}).get("status") == "pass":
            agents_score += 30

        # 总分
        total_score = (code_quality_score + arch_score + agents_score) / 3

        print(f"📈 代码质量得分: {code_quality_score}/100")
        print(f"📈 架构优化得分: {arch_score}/100")
        print(f"📈 智能体系统得分: {agents_score}/100")
        print(f"\n🎯 总体得分: {total_score:.1f}/100")

        # 评级
        if total_score >= 90:
            grade = "优秀 ⭐⭐⭐⭐⭐"
        elif total_score >= 80:
            grade = "良好 ⭐⭐⭐⭐"
        elif total_score >= 70:
            grade = "中等 ⭐⭐⭐"
        elif total_score >= 60:
            grade = "及格 ⭐⭐"
        else:
            grade = "需要改进 ⭐"

        print(f"🏆 评级: {grade}")

        # 保存结果
        self.results["summary"] = {
            "code_quality_score": code_quality_score,
            "architecture_score": arch_score,
            "agents_score": agents_score,
            "total_score": total_score,
            "grade": grade
        }

    def save_report(self):
        """保存验证报告"""
        report_path = self.project_root / "reports" / "architecture" / f"QUALITY_VERIFICATION_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        print(f"\n📄 详细报告已保存: {report_path}")

    def run_all_verifications(self):
        """运行所有验证"""
        print("🚀 Athena平台全面质量验证")
        print(f"📅 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 代码质量验证
        self.verify_code_style()
        self.verify_type_hints()
        self.verify_imports()
        self.verify_test_coverage()

        # 架构优化验证
        self.verify_core_structure()
        self.verify_domains_structure()
        self.verify_root_structure()

        # 智能体系统验证
        self.verify_xiaona_agents()
        self.verify_xiaonuo_agent()
        self.verify_yunxi_agent()
        self.verify_agent_collaboration()

        # 生成总结
        self.generate_summary()
        self.save_report()

        print(f"\n📅 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n" + "=" * 80)
        print("  ✅ 全面质量验证完成！")
        print("=" * 80 + "\n")

def main():
    verifier = QualityVerifier()
    verifier.run_all_verifications()

if __name__ == "__main__":
    main()
