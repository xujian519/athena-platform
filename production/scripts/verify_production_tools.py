#!/usr/bin/env python3
"""
Athena生产级工具综合验证脚本
Production Tools Comprehensive Verification

验证所有工具是否适用于生产环境

作者: Athena平台团队
创建时间: 2025-12-29
版本: v1.0.0
"""

from __future__ import annotations
import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# 添加项目路径
PROJECT_ROOT = Path("/Users/xujian/Athena工作平台")
sys.path.insert(0, str(PROJECT_ROOT))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'


def print_success(msg: str) -> Any:
    print(f"{Colors.GREEN}[✓]{Colors.NC} {msg}")


def print_error(msg: str) -> Any:
    print(f"{Colors.RED}[✗]{Colors.NC} {msg}")


def print_warning(msg: str) -> Any:
    print(f"{Colors.YELLOW}[⚠]{Colors.NC} {msg}")


def print_info(msg: str) -> Any:
    print(f"{Colors.BLUE}[i]{Colors.NC} {msg}")


def print_section(title: str) -> Any:
    print(f"\n{Colors.CYAN}{'='*60}{Colors.NC}")
    print(f"{Colors.CYAN}{title}{Colors.NC}")
    print(f"{Colors.CYAN}{'='*60}{Colors.NC}")


class ProductionToolsVerifier:
    """生产级工具验证器"""

    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tools": {},
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "warnings": 0
            }
        }

    def add_result(self, tool_name: str, status: str, details: str = "",
                   execution_time: float = 0.0, result_data: Any = None):
        """添加验证结果"""
        self.results["tools"][tool_name] = {
            "status": status,  # passed, failed, warning
            "details": details,
            "execution_time": execution_time,
            "result": result_data
        }

        self.results["summary"]["total"] += 1
        if status == "passed":
            self.results["summary"]["passed"] += 1
        elif status == "failed":
            self.results["summary"]["failed"] += 1
        else:
            self.results["summary"]["warnings"] += 1

    async def verify_tool(self, tool_manager, tool_name: str,
                         test_params: dict[str, Any]) -> bool:
        """验证单个工具"""
        print_info(f"测试工具: {tool_name}")

        try:
            import time
            start_time = time.time()

            result = await tool_manager.call_tool(tool_name, test_params)

            execution_time = time.time() - start_time

            if result.status.value == "success":
                print_success(f"  ✓ {tool_name} 调用成功 ({execution_time:.3f}秒)")
                self.add_result(tool_name, "passed", "调用成功",
                             execution_time, result.result)
                return True
            else:
                print_error(f"  ✗ {tool_name} 调用失败: {result.error}")
                self.add_result(tool_name, "failed", result.error,
                             execution_time)
                return False

        except Exception as e:
            print_error(f"  ✗ {tool_name} 测试异常: {e}")
            self.add_result(tool_name, "failed", str(e))
            return False

    async def run_all_verifications(self):
        """运行所有工具验证"""
        print_section("Athena生产级工具综合验证")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 导入必要的模块
        from core.tools.production_tool_implementations import register_production_tools
        from core.tools.tool_call_manager import get_tool_manager
        from core.tools.tool_implementations import register_real_tools

        # 获取工具管理器
        manager = get_tool_manager()

        # 注册所有工具
        register_real_tools(manager)
        register_production_tools(manager)

        all_tools = manager.list_tools()
        print_info(f"已注册工具总数: {len(all_tools)}")

        # 定义测试用例
        test_cases = [
            # 代码分析类
            ("code_analyzer", {
                "code": "def hello(): print('Hello, World!')",
                "language": "python"
            }),
            ("code_analyzer_real", {
                "code": "def test(): return 42",
                "language": "python",
                "style": "detailed"
            }),

            # 系统监控类
            ("system_monitor", {
                "target": "system",
                "metrics": ["cpu", "memory"]
            }),
            ("system_monitor_real", {
                "target": "system",
                "metrics": ["cpu"]
            }),

            # 文件操作类
            ("file_operator_real", {
                "action": "list",
                "path": "/Users/xujian/Athena工作平台"
            }),

            # 代码执行类
            ("code_executor_real", {
                "code": "print('test'); result = 1 + 1"
            }),

            # 嵌入和向量化类
            ("text_embedding", {
                "text": "测试文本向量化"
            }),

            # API测试类
            ("api_tester", {
                "endpoint": "https://httpbin.org/get",
                "method": "GET"
            }),

            # 文档处理类
            ("document_parser", {
                "file_path": "/Users/xujian/Athena工作平台/README.md",
                "extract_content": False
            }),

            # 聊天完成类
            ("chat_companion", {
                "message": "你好"
            }),
            ("emotional_support", {
                "emotion": "焦虑",
                "intensity": 7
            }),

            # 决策引擎类
            ("decision_engine", {
                "context": "选择技术方案",
                "options": ["方案A", "方案B", "方案C"]
            }),
            ("risk_analyzer", {
                "scenario": "新项目启动",
                "risk_factors": [{"name": "技术风险", "description": "实现难度"}]
            }),

            # 搜索类
            ("web_search", {
                "query": "人工智能",
                "limit": 5
            }),

            # 知识图谱类
            ("knowledge_graph", {
                "query": "Python编程",
                "domain": "技术"
            }),
        ]

        # 执行测试
        passed = 0
        failed = 0

        for tool_name, params in test_cases:
            if tool_name in all_tools:
                if await self.verify_tool(manager, tool_name, params):
                    passed += 1
                else:
                    failed += 1
            else:
                print_warning(f"  ⚠ 工具未注册: {tool_name}")

        # 打印摘要
        self.print_summary()

        # 保存报告
        self.save_report()

        return failed == 0

    def print_summary(self) -> Any:
        """打印验证摘要"""
        print_section("验证摘要")

        summary = self.results["summary"]
        total = summary["total"]
        passed = summary["passed"]
        failed = summary["failed"]
        warnings = summary["warnings"]

        print(f"总工具数: {total}")
        print_success(f"通过: {passed}")
        if failed > 0:
            print_error(f"失败: {failed}")
        if warnings > 0:
            print_warning(f"警告: {warnings}")

        success_rate = (passed / total * 100) if total > 0 else 0
        print(f"\n通过率: {success_rate:.1f}%")

        if success_rate >= 90:
            print_success("\n🎉 生产环境就绪!")
        elif success_rate >= 70:
            print_warning("\n⚠ 基本可用,建议优化失败工具")
        else:
            print_error("\n❌ 不建议用于生产环境")

    def save_report(self) -> None:
        """保存验证报告"""
        import json

        report_dir = Path("logs/production")
        report_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"production_tools_verification_{timestamp}.json"

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)

        print_info(f"\n报告已保存: {report_file}")


async def main():
    """主函数"""
    verifier = ProductionToolsVerifier()
    success = await verifier.run_all_verifications()

    # 返回退出码
    if success:
        return 0
    else:
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
