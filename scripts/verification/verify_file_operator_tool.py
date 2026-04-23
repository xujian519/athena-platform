#!/usr/bin/env python3
"""
file_operator工具验证脚本

验证file_operator_handler的功能完整性、错误处理和性能指标。
"""

import asyncio
import json

# 添加项目根目录到Python路径
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.tools.tool_implementations import file_operator_handler


class FileOperatorVerifier:
    """file_operator工具验证器"""

    def __init__(self):
        self.test_results = []
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "test.txt"
        self.test_content = "Hello, Athena Platform!\n这是测试内容。"

    async def test_write_file(self) -> bool:
        """测试写入文件功能"""
        print("📝 测试写入文件...")
        try:
            params = {
                "action": "write",
                "path": str(self.test_file),
                "content": self.test_content,
            }
            result = await file_operator_handler(params, {})

            success = result.get("success", False)
            message = result.get("message", "")

            print(f"  结果: {'✅ 成功' if success else '❌ 失败'}")
            print(f"  消息: {message}")

            if success:
                # 验证文件实际写入
                if self.test_file.exists():
                    actual_content = self.test_file.read_text(encoding="utf-8")
                    if actual_content == self.test_content:
                        print("  ✅ 文件内容验证成功")
                    else:
                        print(f"  ❌ 文件内容不匹配: {actual_content}")
                        return False
                else:
                    print("  ❌ 文件未实际创建")
                    return False

            self.test_results.append(
                {"test": "write_file", "success": success, "message": message}
            )
            return success
        except Exception as e:
            print(f"  ❌ 异常: {e}")
            self.test_results.append({"test": "write_file", "success": False, "error": str(e)})
            return False

    async def test_read_file(self) -> bool:
        """测试读取文件功能"""
        print("📖 测试读取文件...")
        try:
            # 先确保文件存在
            if not self.test_file.exists():
                await self.test_write_file()

            params = {"action": "read", "path": str(self.test_file)}
            result = await file_operator_handler(params, {})

            success = result.get("success", False)
            message = result.get("message", "")
            data = result.get("data", {})

            print(f"  结果: {'✅ 成功' if success else '❌ 失败'}")
            print(f"  消息: {message}")

            if success and data:
                content = data.get("content", "")
                size = data.get("size", 0)
                lines = data.get("lines", 0)

                print(f"  📊 内容长度: {size} 字符")
                print(f"  📊 行数: {lines} 行")
                print(f"  📊 内容预览: {content[:50]}...")

                if content == self.test_content:
                    print("  ✅ 读取内容正确")
                else:
                    print("  ❌ 读取内容不匹配")
                    return False

            self.test_results.append(
                {"test": "read_file", "success": success, "message": message}
            )
            return success
        except Exception as e:
            print(f"  ❌ 异常: {e}")
            self.test_results.append({"test": "read_file", "success": False, "error": str(e)})
            return False

    async def test_list_directory(self) -> bool:
        """测试列出目录功能"""
        print("📁 测试列出目录...")
        try:
            params = {"action": "list", "path": self.temp_dir}
            result = await file_operator_handler(params, {})

            success = result.get("success", False)
            message = result.get("message", "")
            items = result.get("items", [])

            print(f"  结果: {'✅ 成功' if success else '❌ 失败'}")
            print(f"  消息: {message}")

            if success and items:
                print(f"  📊 找到 {len(items)} 个项目:")
                for item in items[:5]:  # 只显示前5个
                    name = item.get("name", "")
                    item_type = item.get("type", "")
                    size = item.get("size", 0)
                    print(f"    - {name} ({item_type}, {size} bytes)")

            self.test_results.append(
                {"test": "list_directory", "success": success, "message": message, "items_count": len(items) if items else 0}
            )
            return success
        except Exception as e:
            print(f"  ❌ 异常: {e}")
            self.test_results.append({"test": "list_directory", "success": False, "error": str(e)})
            return False

    async def test_search_files(self) -> bool:
        """测试搜索文件功能"""
        print("🔍 测试搜索文件...")
        try:
            params = {"action": "search", "path": self.temp_dir, "pattern": "*.txt"}
            result = await file_operator_handler(params, {})

            success = result.get("success", False)
            message = result.get("message", "")
            data = result.get("data", {})

            print(f"  结果: {'✅ 成功' if success else '❌ 失败'}")
            print(f"  消息: {message}")

            if success and data:
                matches = data.get("matches", [])
                count = data.get("count", 0)

                print(f"  📊 找到 {count} 个匹配:")
                for match in matches[:5]:  # 只显示前5个
                    print(f"    - {match}")

            self.test_results.append(
                {"test": "search_files", "success": success, "message": message, "matches_count": data.get("count", 0) if data else 0}
            )
            return success
        except Exception as e:
            print(f"  ❌ 异常: {e}")
            self.test_results.append({"test": "search_files", "success": False, "error": str(e)})
            return False

    async def test_error_handling(self) -> bool:
        """测试错误处理"""
        print("⚠️  测试错误处理...")
        try:
            # 测试读取不存在的文件
            params = {"action": "read", "path": "/nonexistent/file.txt"}
            result = await file_operator_handler(params, {})

            success = result.get("success", False)
            message = result.get("message", "")

            print(f"  读取不存在文件: {'✅ 正确处理' if not success else '❌ 未正确处理'}")
            print(f"  消息: {message}")

            if not success:
                print("  ✅ 错误处理正确（返回success=False）")
            else:
                print("  ❌ 错误处理失败（应返回success=False）")
                return False

            self.test_results.append(
                {"test": "error_handling", "success": True, "message": "错误处理正确"}
            )
            return True
        except Exception as e:
            print(f"  ❌ 异常抛出（不应抛出异常）: {e}")
            self.test_results.append({"test": "error_handling", "success": False, "error": str(e)})
            return False

    async def test_performance(self) -> dict[str, float]:
        """测试性能指标"""
        print("⚡ 测试性能指标...")
        performance = {}

        # 测试写入性能
        start = time.time()
        await self.test_write_file()
        write_time = time.time() - start
        performance["write_time"] = write_time
        print(f"  📊 写入时间: {write_time*1000:.2f} ms")

        # 测试读取性能
        start = time.time()
        await self.test_read_file()
        read_time = time.time() - start
        performance["read_time"] = read_time
        print(f"  📊 读取时间: {read_time*1000:.2f} ms")

        # 测试列出目录性能
        start = time.time()
        await self.test_list_directory()
        list_time = time.time() - start
        performance["list_time"] = list_time
        print(f"  📊 列出目录时间: {list_time*1000:.2f} ms")

        # 测试搜索性能
        start = time.time()
        await self.test_search_files()
        search_time = time.time() - start
        performance["search_time"] = search_time
        print(f"  📊 搜索时间: {search_time*1000:.2f} ms")

        return performance

    async def run_all_tests(self) -> dict[str, Any]:
        """运行所有测试"""
        print("=" * 60)
        print("🚀 开始验证file_operator工具")
        print("=" * 60)

        # 功能测试
        print("\n📋 功能测试:")
        print("-" * 60)

        await self.test_write_file()
        await self.test_read_file()
        await self.test_list_directory()
        await self.test_search_files()
        await self.test_error_handling()

        # 性能测试
        print("\n⚡ 性能测试:")
        print("-" * 60)
        performance = await self.test_performance()

        # 生成报告
        print("\n📊 测试结果汇总:")
        print("-" * 60)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.get("success", False))

        print(f"  总测试数: {total_tests}")
        print(f"  通过测试: {passed_tests}")
        print(f"  失败测试: {total_tests - passed_tests}")
        print(f"  通过率: {passed_tests/total_tests*100:.1f}%")

        print("\n📈 性能指标:")
        print(f"  写入: {performance['write_time']*1000:.2f} ms")
        print(f"  读取: {performance['read_time']*1000:.2f} ms")
        print(f"  列出: {performance['list_time']*1000:.2f} ms")
        print(f"  搜索: {performance['search_time']*1000:.2f} ms")

        # 清理临时文件
        try:
            if self.test_file.exists():
                self.test_file.unlink()
        except Exception:
            pass

        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "pass_rate": passed_tests / total_tests * 100,
            "performance": performance,
            "results": self.test_results,
        }


async def main():
    """主函数"""
    verifier = FileOperatorVerifier()
    report = await verifier.run_all_tests()

    # 保存报告
    report_path = Path(__file__).parent.parent / "docs" / "reports" / "file_operator_verification.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n📄 详细报告已保存到: {report_path}")

    # 返回退出码
    exit_code = 0 if report["pass_rate"] == 100 else 1
    exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())
