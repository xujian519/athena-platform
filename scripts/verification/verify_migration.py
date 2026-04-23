#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具注册表迁移验证脚本

功能：
1. 验证所有工具已注册到新注册表
2. 验证智能体可以获取工具
3. 验证无循环导入
4. 验证性能基准
5. 生成验证报告

使用方法：
    python3 scripts/verify_migration.py --all
    python3 scripts/verify_migration.py --check-registration
    python3 scripts/verify_migration.py --check-agents
    python3 scripts/verify_migration.py --check-imports
    python3 scripts/verify_migration.py --check-performance

Author: Agent 4 (迁移专家)
Created: 2026-04-19
"""

import argparse
import importlib
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Set, Tuple

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MigrationVerifier:
    """迁移验证器"""

    def __init__(self, root_path: str = "."):
        """
        初始化验证器

        Args:
            root_path: 项目根目录
        """
        self.root_path = Path(root_path)
        self.verification_results: Dict[str, Dict] = {}
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def verify_all(self) -> Dict:
        """
        执行所有验证检查

        Returns:
            验证结果汇总
        """
        logger.info("🔍 开始执行完整迁移验证...")
        logger.info("=" * 80)

        checks = [
            ("工具注册验证", self.verify_tool_registration),
            ("智能体集成验证", self.verify_agent_integration),
            ("循环导入检查", self.verify_no_circular_imports),
            ("性能基准验证", self.verify_performance_benchmarks),
            ("文档完整性验证", self.verify_documentation),
        ]

        for check_name, check_func in checks:
            logger.info(f"\n📋 {check_name}...")
            try:
                result = check_func()
                self.verification_results[check_name] = result
                self._print_check_result(check_name, result)
            except Exception as e:
                logger.error(f"❌ {check_name}失败: {e}", exc_info=True)
                self.verification_results[check_name] = {
                    "status": "error",
                    "message": str(e)
                }

        self._print_summary()
        return self.verification_results

    def verify_tool_registration(self) -> Dict:
        """
        验证工具注册

        Returns:
            验证结果
        """
        try:
            # 尝试导入新的注册表
            from core.tools.centralized_registry import get_centralized_registry

            registry = get_centralized_registry()

            # 获取所有注册的工具
            stats = registry.get_statistics()

            result = {
                "status": "success" if stats["total_tools"] > 0 else "warning",
                "total_tools": stats.get("total_tools", 0),
                "enabled_tools": stats.get("enabled_tools", 0),
                "disabled_tools": stats.get("disabled_tools", 0),
                "category_distribution": stats.get("category_distribution", {}),
                "message": f"发现 {stats.get('total_tools', 0)} 个工具"
            }

            # 检查核心工具是否存在
            required_tools = [
                "patent_search",
                "academic_search",
                "vector_search",
                "document_parser",
            ]

            missing_tools = []
            for tool_id in required_tools:
                tool = registry.get_tool(tool_id)
                if tool is None:
                    missing_tools.append(tool_id)

            if missing_tools:
                result["status"] = "warning"
                result["message"] += f"，缺少核心工具: {', '.join(missing_tools)}"
                self.warnings.append(f"缺少核心工具: {', '.join(missing_tools)}")

            return result

        except ImportError as e:
            return {
                "status": "error",
                "message": f"无法导入新注册表: {e}"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"工具注册验证失败: {e}"
            }

    def verify_agent_integration(self) -> Dict:
        """
        验证智能体集成

        Returns:
            验证结果
        """
        result = {
            "status": "success",
            "agents_checked": [],
            "agents_failed": [],
            "message": ""
        }

        # 要检查的智能体列表
        agents_to_check = [
            "core.agents.xiaona_professional",
            "core.agents.xiaonuo_coordinator",
            "core.agents.yunxi_vega_with_memory",
        ]

        for agent_module in agents_to_check:
            try:
                logger.info(f"  检查智能体: {agent_module}")
                agent = importlib.import_module(agent_module)

                # 检查智能体是否有获取工具的方法
                if hasattr(agent, "get_available_tools") or hasattr(agent, "get_tools"):
                    result["agents_checked"].append(agent_module)
                    logger.info(f"    ✅ {agent_module} 可以获取工具")
                else:
                    result["agents_failed"].append(agent_module)
                    logger.warning(f"    ⚠️ {agent_module} 缺少工具获取方法")
                    self.warnings.append(f"{agent_module} 缺少工具获取方法")

            except ImportError as e:
                result["agents_failed"].append(agent_module)
                logger.warning(f"    ⚠️ {agent_module} 导入失败: {e}")
                self.warnings.append(f"{agent_module} 导入失败: {e}")
            except Exception as e:
                result["agents_failed"].append(agent_module)
                logger.error(f"    ❌ {agent_module} 检查失败: {e}")
                self.errors.append(f"{agent_module} 检查失败: {e}")

        result["message"] = f"检查了 {len(result['agents_checked'])} 个智能体"
        if result["agents_failed"]:
            result["status"] = "warning"
            result["message"] += f"，{len(result['agents_failed'])} 个失败"

        return result

    def verify_no_circular_imports(self) -> Dict:
        """
        验证无循环导入

        Returns:
            验证结果
        """
        # 简化的循环导入检测
        result = {
            "status": "success",
            "circular_imports": [],
            "message": "未检测到循环导入"
        }

        # 要检查的关键模块
        modules_to_check = [
            "core.tools.centralized_registry",
            "core.tools.decorators",
            "core.agents.base_agent",
            "core.agents.xiaona_professional",
            "core.agents.xiaonuo_coordinator",
        ]

        for module_name in modules_to_check:
            try:
                importlib.import_module(module_name)
                logger.info(f"  ✅ {module_name} 导入成功")
            except ImportError as e:
                if "circular import" in str(e).lower():
                    result["circular_imports"].append({
                        "module": module_name,
                        "error": str(e)
                    })
                    logger.error(f"  ❌ {module_name} 存在循环导入: {e}")
                    self.errors.append(f"{module_name} 存在循环导入")

        if result["circular_imports"]:
            result["status"] = "error"
            result["message"] = f"发现 {len(result['circular_imports'])} 个循环导入"

        return result

    def verify_performance_benchmarks(self) -> Dict:
        """
        验证性能基准

        Returns:
            验证结果
        """
        result = {
            "status": "success",
            "benchmarks": {},
            "message": "性能基准达标"
        }

        try:
            from core.tools.centralized_registry import get_centralized_registry

            registry = get_centralized_registry()

            # 测试工具查询性能
            iterations = 100
            start_time = time.time()

            for _ in range(iterations):
                registry.get_tool("patent_search")

            elapsed_time = time.time() - start_time
            avg_time = elapsed_time / iterations

            result["benchmarks"]["tool_query"] = {
                "avg_time_ms": avg_time * 1000,
                "target_ms": 5.0,
                "passed": avg_time < 0.005  # 5ms目标
            }

            # 测试工具搜索性能
            start_time = time.time()

            for _ in range(iterations):
                registry.search_tools(domain="patent")

            elapsed_time = time.time() - start_time
            avg_time = elapsed_time / iterations

            result["benchmarks"]["tool_search"] = {
                "avg_time_ms": avg_time * 1000,
                "target_ms": 10.0,
                "passed": avg_time < 0.010  # 10ms目标
            }

            # 检查是否所有基准都通过
            all_passed = all(b["passed"] for b in result["benchmarks"].values())

            if not all_passed:
                result["status"] = "warning"
                result["message"] = "部分性能基准未达标"
                self.warnings.append("性能基准未达标")

        except Exception as e:
            result["status"] = "error"
            result["message"] = f"性能验证失败: {e}"
            self.errors.append(f"性能验证失败: {e}")

        return result

    def verify_documentation(self) -> Dict:
        """
        验证文档完整性

        Returns:
            验证结果
        """
        result = {
            "status": "success",
            "missing_docs": [],
            "message": "文档完整"
        }

        # 检查关键文档是否存在
        required_docs = [
            "docs/api/TOOL_REGISTRY_API.md",
            "docs/guides/TOOL_MIGRATION_GUIDE.md",
            "docs/reports/tool-registry-migration/agent-4-preparation-report.md",
        ]

        for doc_path in required_docs:
            doc_file = self.root_path / doc_path
            if not doc_file.exists():
                result["missing_docs"].append(doc_path)
                logger.warning(f"  ⚠️ 缺少文档: {doc_path}")
                self.warnings.append(f"缺少文档: {doc_path}")

        if result["missing_docs"]:
            result["status"] = "warning"
            result["message"] = f"缺少 {len(result['missing_docs'])} 个文档"

        return result

    def _print_check_result(self, check_name: str, result: Dict):
        """打印检查结果"""
        status_icon = {
            "success": "✅",
            "warning": "⚠️",
            "error": "❌"
        }

        status = result.get("status", "unknown")
        message = result.get("message", "")

        logger.info(f"{status_icon.get(status, '?')} {check_name}: {message}")

    def _print_summary(self):
        """打印验证摘要"""
        logger.info("\n" + "=" * 80)
        logger.info("📊 验证摘要")
        logger.info("=" * 80)

        total_checks = len(self.verification_results)
        success_checks = sum(1 for r in self.verification_results.values() if r.get("status") == "success")
        warning_checks = sum(1 for r in self.verification_results.values() if r.get("status") == "warning")
        error_checks = sum(1 for r in self.verification_results.values() if r.get("status") == "error")

        logger.info(f"总检查项: {total_checks}")
        logger.info(f"✅ 通过: {success_checks}")
        logger.info(f"⚠️  警告: {warning_checks}")
        logger.info(f"❌ 错误: {error_checks}")

        if self.warnings:
            logger.info(f"\n⚠️  警告列表 ({len(self.warnings)}):")
            for warning in self.warnings:
                logger.info(f"  - {warning}")

        if self.errors:
            logger.info(f"\n❌ 错误列表 ({len(self.errors)}):")
            for error in self.errors:
                logger.info(f"  - {error}")

        # 整体状态
        if error_checks > 0:
            overall_status = "❌ 验证失败"
        elif warning_checks > 0:
            overall_status = "⚠️  验证通过（有警告）"
        else:
            overall_status = "✅ 验证完全通过"

        logger.info(f"\n{overall_status}")
        logger.info("=" * 80)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="工具注册表迁移验证脚本"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="执行所有验证检查"
    )
    parser.add_argument(
        "--check-registration",
        action="store_true",
        help="检查工具注册"
    )
    parser.add_argument(
        "--check-agents",
        action="store_true",
        help="检查智能体集成"
    )
    parser.add_argument(
        "--check-imports",
        action="store_true",
        help="检查循环导入"
    )
    parser.add_argument(
        "--check-performance",
        action="store_true",
        help="检查性能基准"
    )
    parser.add_argument(
        "--root-path",
        type=str,
        default=".",
        help="项目根目录路径"
    )

    args = parser.parse_args()

    # 创建验证器
    verifier = MigrationVerifier(root_path=args.root_path)

    # 执行验证
    if args.all:
        verifier.verify_all()
    elif args.check_registration:
        result = verifier.verify_tool_registration()
        verifier._print_check_result("工具注册验证", result)
    elif args.check_agents:
        result = verifier.verify_agent_integration()
        verifier._print_check_result("智能体集成验证", result)
    elif args.check_imports:
        result = verifier.verify_no_circular_imports()
        verifier._print_check_result("循环导入检查", result)
    elif args.check_performance:
        result = verifier.verify_performance_benchmarks()
        verifier._print_check_result("性能基准验证", result)
    else:
        # 默认执行所有检查
        verifier.verify_all()


if __name__ == "__main__":
    main()
