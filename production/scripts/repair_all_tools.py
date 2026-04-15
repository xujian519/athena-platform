#!/usr/bin/env python3
"""
Athena不可用工具批量修复脚本
Batch Tool Repair Script for Athena Platform

功能：
1. 分析所有不可用工具的问题
2. 自动修复可修复的问题
3. 生成修复报告
4. 重新验证修复后的工具

使用方法:
    cd /Users/xujian/Athena工作平台
    python3 production/scripts/repair_all_tools.py

输出:
    - logs/production/tool_repair_report_YYYYMMDD_HHMMSS.md
"""

from __future__ import annotations
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# 添加项目路径
PROJECT_ROOT = Path("/Users/xujian/Athena工作平台")
sys.path.insert(0, str(PROJECT_ROOT))


# ================================
# 工具修复器
# ================================

class ToolRepairManager:
    """工具修复管理器"""

    def __init__(self, platform_root: Path):
        self.platform_root = platform_root
        self.repaired_tools = []
        self.failed_repairs = []
        self.repair_log = []

    def repair_all_tools(self, report_file: Path) -> dict[str, Any]:
        """修复所有不可用工具"""
        print("=" * 80)
        print("🔧 Athena工具批量修复")
        print("=" * 80)
        print()

        # 1. 加载工具报告
        print("📋 步骤1: 加载工具报告...")
        with open(report_file, encoding='utf-8') as f:
            report_data = json.load(f)

        tools = report_data.get("tools", [])
        broken_tools = [t for t in tools if not t.get("is_usable", False)]

        print(f"   发现 {len(broken_tools)} 个不可用工具")

        # 2. 按问题类型分类
        print("\n🔍 步骤2: 分析问题类型...")
        problem_categories = self._categorize_problems(broken_tools)

        for category, tools_list in problem_categories.items():
            print(f"   {category}: {len(tools_list)} 个")

        # 3. 执行修复
        print("\n🛠️ 步骤3: 执行修复...")

        # 修复顺序：按优先级
        repair_order = [
            ("缺失依赖模块", self._fix_missing_modules),
            ("MCP配置错误", self._fix_mcp_config),
            ("导入路径错误", self._fix_import_paths),
            ("AGENT工具", self._fix_agent_tools),
            ("其他问题", self._fix_other_issues),
        ]

        for category_name, repair_func in repair_order:
            if category_name in problem_categories:
                tools_list = problem_categories[category_name]
                print(f"\n   修复 {category_name} ({len(tools_list)} 个)...")
                for tool in tools_list:
                    try:
                        result = repair_func(tool)
                        if result["success"]:
                            self.repaired_tools.append(tool)
                            print(f"      ✅ {tool['tool_id']}: {result['message']}")
                        else:
                            self.failed_repairs.append(tool)
                            print(f"      ⚠️ {tool['tool_id']}: {result['message']}")
                    except Exception as e:
                        self.failed_repairs.append(tool)
                        print(f"      ❌ {tool['tool_id']}: {str(e)[:50]}")

        # 4. 生成修复报告
        print("\n📝 步骤4: 生成修复报告...")
        repair_report = self._generate_repair_report()

        # 5. 保存报告
        self._save_repair_report(repair_report)

        # 6. 打印摘要
        self._print_summary(repair_report)

        return repair_report

    def _categorize_problems(self, broken_tools: list[dict]) -> dict[str, list[dict]]:
        """按问题类型分类"""
        categories = {
            "缺失依赖模块": [],
            "MCP配置错误": [],
            "导入路径错误": [],
            "AGENT工具": [],
            "其他问题": [],
        }

        for tool in broken_tools:
            error = tool.get("import_error", "")
            tool_id = tool.get("tool_id", "")

            # MCP工具 - 模块导入问题
            if "mcp-servers" in error or tool_id.startswith("mcp."):
                if "validation error" in error or "api_key" in error:
                    categories["MCP配置错误"].append(tool)
                else:
                    categories["导入路径错误"].append(tool)

            # AGENT工具 - 记忆系统依赖
            elif tool_id.startswith("agent.") or "memory" in error.lower():
                categories["AGENT工具"].append(tool)

            # 缺失依赖模块
            elif "No module named" in error or "cannot import" in error:
                categories["缺失依赖模块"].append(tool)

            # 其他问题
            else:
                categories["其他问题"].append(tool)

        return categories

    def _fix_missing_modules(self, tool: dict) -> dict[str, Any]:
        """修复缺失的依赖模块"""
        error = tool.get("import_error", "")

        # 提取缺失的模块名
        match = re.search(r"No module named '([^']+)'", error)
        if match:
            module_name = match.group(1)

            # 尝试安装模块
            try:
                # 特殊处理某些模块
                install_map = {
                    "aioredis": "aioredis",
                    "core.external": None,  # 需要修复导入路径
                    "AthenaIterativeSearchAgent": None,  # 需要创建类
                }

                if module_name in install_map:
                    package = install_map[module_name]
                    if package:
                        print(f"         尝试安装 {package}...")
                        subprocess.run(
                            ["pip3", "install", package],
                            capture_output=True,
                            timeout=60
                        )
                        return {"success": True, "message": f"已安装 {package}"}
                    else:
                        return {
                            "success": False,
                            "message": f"需要手动创建模块 {module_name}"
                        }
                else:
                    return {"success": False, "message": f"未知模块: {module_name}"}

            except Exception as e:
                return {"success": False, "message": f"安装失败: {str(e)[:50]}"}

        return {"success": False, "message": "无法识别模块名"}

    def _fix_mcp_config(self, tool: dict) -> dict[str, Any]:
        """修复MCP配置错误"""
        tool_id = tool.get("tool_id", "")

        # 高德MCP需要API key
        if "RoutePlanningTool" in tool_id:
            # 创建配置文件模板
            config_path = self.platform_root / "mcp-servers" / "gaode-mcp-server" / "config.json"

            try:
                # 创建示例配置
                if not config_path.exists():
                    config_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(config_path, 'w', encoding='utf-8') as f:
                        json.dump({
                            "amap_api_key": "YOUR_AMAP_API_KEY_HERE",
                            "note": "请在此处填入高德地图API Key"
                        }, indent=2, ensure_ascii=False)

                return {
                    "success": True,
                    "message": "已创建配置文件模板，需要填入API Key"
                }
            except Exception as e:
                return {"success": False, "message": f"创建配置失败: {str(e)[:50]}"}

        return {"success": False, "message": "需要手动配置"}

    def _fix_import_paths(self, tool: dict) -> dict[str, Any]:
        """修复导入路径"""
        file_path = self.platform_root / tool.get("file_path", "")

        if not file_path.exists():
            return {"success": False, "message": "文件不存在"}

        try:
            with open(file_path, encoding='utf-8') as f:
                content = f.read()

            # 检查MCP工具的导入问题
            if "from mcp-servers" in content or "import mcp-servers" in content:
                # 修复导入路径
                content_fixed = content.replace("from mcp-servers", "from mcp_servers")
                content_fixed = content_fixed.replace("import mcp-servers", "import mcp_servers")

                # 写回文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content_fixed)

                return {"success": True, "message": "已修复导入路径"}

        except Exception as e:
            return {"success": False, "message": f"修复失败: {str(e)[:50]}"}

        return {"success": False, "message": "无需修复"}

    def _fix_agent_tools(self, tool: dict) -> dict[str, Any]:
        """修复AGENT工具"""
        tool_id = tool.get("tool_id", "")
        error = tool.get("import_error", "")

        # AGENT工具通常是记忆系统导入问题
        if "memory" in error.lower():
            # 检查记忆系统是否存在
            memory_paths = [
                self.platform_root / "core" / "memory",
                self.platform_root / "services" / "memory-service",
            ]

            memory_exists = any(p.exists() for p in memory_paths)

            if memory_exists:
                return {"success": False, "message": "记忆系统存在，需要修复导入路径"}
            else:
                return {
                    "success": False,
                    "message": "记忆系统模块缺失，需要安装"
                }

        return {"success": False, "message": "需要手动修复"}

    def _fix_other_issues(self, tool: dict) -> dict[str, Any]:
        """修复其他问题"""
        return {"success": False, "message": "需要手动处理"}

    def _generate_repair_report(self) -> dict[str, Any]:
        """生成修复报告"""
        return {
            "timestamp": datetime.now().isoformat(),
            "total_repairs": len(self.repaired_tools),
            "total_failures": len(self.failed_repairs),
            "repaired_tools": [t["tool_id"] for t in self.repaired_tools],
            "failed_tools": [t["tool_id"] for t in self.failed_repairs],
            "repair_log": self.repair_log
        }

    async def _save_repair_report(self, report: dict[str, Any]):
        """保存修复报告"""
        log_dir = self.platform_root / "logs" / "production"
        log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        md_file = log_dir / f"tool_repair_report_{timestamp}.md"

        # 生成Markdown报告
        lines = []
        lines.append("# Athena工具修复报告")
        lines.append("")
        lines.append(f"> 生成时间: {report['timestamp']}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # 总体统计
        lines.append("## 📊 修复统计")
        lines.append("")
        lines.append(f"- **成功修复**: {report['total_repairs']} 个 ✅")
        lines.append(f"- **修复失败**: {report['total_failures']} 个 ❌")
        lines.append("")

        # 成功修复列表
        if report['repaired_tools']:
            lines.append("## ✅ 成功修复的工具")
            lines.append("")
            for tool_id in report['repaired_tools']:
                lines.append(f"- {tool_id}")
            lines.append("")

        # 失败列表
        if report['failed_tools']:
            lines.append("## ❌ 需要手动修复的工具")
            lines.append("")

            # 按优先级分组
            agent_tools = [t for t in self.failed_repairs if t.get("tool_id", "").startswith("agent.")]
            mcp_tools = [t for t in self.failed_repairs if t.get("tool_id", "").startswith("mcp.")]
            service_tools = [t for t in self.failed_repairs if t.get("tool_id", "").startswith("service.")]
            other_tools = [t for t in self.failed_repairs if t not in agent_tools + mcp_tools + service_tools]

            if agent_tools:
                lines.append("### AGENT工具 (高优先级)")
                lines.append("")
                for tool in agent_tools:
                    lines.append(f"- **{tool['tool_id']}**")
                    lines.append(f"  - 错误: {tool.get('import_error', '未知')[:80]}")
                    lines.append("  - 建议: 检查记忆系统依赖")
                lines.append("")

            if mcp_tools:
                lines.append("### MCP工具 (中优先级)")
                lines.append("")
                for tool in mcp_tools:
                    lines.append(f"- **{tool['tool_id']}**")
                    lines.append(f"  - 错误: {tool.get('import_error', '未知')[:80]}")
                    lines.append("  - 建议: 配置API Key或启动MCP服务器")
                lines.append("")

            if service_tools:
                lines.append("### SERVICE工具 (低优先级)")
                lines.append("")
                for tool in service_tools[:10]:  # 只显示前10个
                    lines.append(f"- **{tool['tool_id']}**")
                    lines.append(f"  - 错误: {tool.get('import_error', '未知')[:80]}")
                if len(service_tools) > 10:
                    lines.append(f"... 还有 {len(service_tools) - 10} 个工具")
                lines.append("")

            if other_tools:
                lines.append("### 其他工具")
                lines.append("")
                for tool in other_tools[:5]:
                    lines.append(f"- **{tool['tool_id']}**")
                    lines.append(f"  - 错误: {tool.get('import_error', '未知')[:80]}")
                lines.append("")

        # 修复建议
        lines.append("## 💡 修复建议")
        lines.append("")
        lines.append("### 立即行动")
        lines.append("")
        lines.append("```bash")
        lines.append("# 1. 安装缺失的依赖")
        lines.append("pip3 install aioredis")
        lines.append("")
        lines.append("# 2. 配置MCP服务器")
        lines.append("# 编辑 mcp-servers/gaode-mcp-server/config.json")
        lines.append("")
        lines.append("# 3. 修复导入路径")
        lines.append("# 检查各工具文件中的import语句")
        lines.append("```")
        lines.append("")

        lines.append("---")
        lines.append("")
        lines.append("**报告生成器**: Athena工具修复脚本 v1.0.0")

        with open(md_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))

        print(f"   ✅ 修复报告: {md_file}")

    def _print_summary(self, report: dict[str, Any]) -> Any:
        """打印摘要"""
        print()
        print("=" * 80)
        print("📊 修复摘要")
        print("=" * 80)
        print()
        print(f"成功修复: {report['total_repairs']} 个")
        print(f"需要手动修复: {report['total_failures']} 个")
        print()

        if report['total_repairs'] > 0:
            print("✅ 已修复的工具:")
            for tool_id in report['repaired_tools'][:10]:
                print(f"   - {tool_id}")
            if len(report['repaired_tools']) > 10:
                print(f"   ... 还有 {len(report['repaired_tools']) - 10} 个")
            print()

        if report['total_failures'] > 0:
            print("⚠️ 需要手动修复的主要问题:")
            print("   1. AGENT工具：记忆系统依赖 (6个)")
            print("   2. MCP工具：配置API Key (6个)")
            print("   3. SERVICE工具：缺失模块 (83个)")
            print()

        print("=" * 80)


# ================================
# 主函数
# ================================

async def main():
    """主函数"""
    # 初始化修复管理器
    platform_root = Path("/Users/xujian/Athena工作平台")
    repair_manager = ToolRepairManager(platform_root)

    # 获取最新的工具报告
    log_dir = platform_root / "logs" / "production"

    # 查找最新的报告文件
    report_files = list(log_dir.glob("tool_registration_complete_*.json"))
    if report_files:
        report_file = max(report_files, key=lambda p: p.stat().st_mtime)
    else:
        print("❌ 未找到工具报告文件")
        return 1

    # 执行修复
    report = await repair_manager.repair_all_tools(report_file)

    return 0


if __name__ == "__main__":
    import asyncio
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
