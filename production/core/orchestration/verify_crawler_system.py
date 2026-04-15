#!/usr/bin/env python3
"""
爬虫系统完整性验证脚本
Crawler System Integrity Verification Script

验证平台爬虫系统的完整性和可运行性

作者: 小诺·双鱼公主
创建时间: 2025-12-14
"""

from __future__ import annotations
import asyncio
import json
import os
import sys
import time
from datetime import datetime

from core.async_main import async_main
from core.logging_config import setup_logging

# 添加路径
sys.path.append("/Users/xujian/Athena工作平台")

from core.orchestration.xiaonuo_crawler_intelligent_router import XiaonuoCrawlerIntelligentRouter
from core.orchestration.xiaonuo_universal_crawler_controller import (
    CrawlerTask,
    CrawlerType,
    XiaonuoUniversalCrawlerController,
)

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


class CrawlerSystemVerifier:
    """爬虫系统验证器"""

    def __init__(self):
        self.name = "小诺·双鱼公主爬虫系统验证器"
        self.test_results = {}
        self.start_time = datetime.now()

    async def run_complete_verification(self):
        """运行完整验证"""
        print(f"🔍 {self.name} - 开始完整验证")
        print("=" * 60)

        # 1. 验证爬虫文件完整性
        await self._verify_crawler_files()

        # 2. 验证依赖环境
        await self._verify_dependencies()

        # 3. 验证核心功能
        await self._verify_core_functions()

        # 4. 验证智能路由
        await self._verify_intelligent_routing()

        # 5. 验证任务执行
        await self._verify_task_execution()

        # 6. 生成验证报告
        await self._generate_report()

    async def _verify_crawler_files(self):
        """验证爬虫文件完整性"""
        print("\n1️⃣ 验证爬虫文件完整性")
        print("-" * 40)

        # 定义需要验证的文件
        crawler_files = {
            "universal_crawler": "/Users/xujian/Athena工作平台/services/crawler-service/core/universal_crawler.py",
            "hybrid_crawler_manager": "/Users/xujian/Athena工作平台/services/crawler-service/core/hybrid_crawler_manager.py",
            "enhanced_patent_crawler": "/Users/xujian/Athena工作平台/patent-platform/workspace/enhanced_patent_crawler.py",
            "distributed_crawler": "/Users/xujian/Athena工作平台/tools/advanced/distributed_crawler.py",
            "browser_automation": "/Users/xujian/Athena工作平台/services/browser-automation-service/browser_automation_server.py",
            "douyin_scraper": "/Users/xujian/Athena工作平台/services/browser-automation-service/douyin_scraper.py",
            "crawler_api_server": "/Users/xujian/Athena工作平台/services/platform-integration-service/crawler_api_server.py",
            "xiaonuo_crawler_control": "/Users/xujian/Athena工作平台/services/scripts/xiaonuo_crawler_control.py",
        }

        file_status = {}
        for name, path in crawler_files.items():
            if os.path.exists(path):
                size = os.path.getsize(path) / 1024  # KB
                file_status[name] = {"exists": True, "size_kb": round(size, 2)}
                print(f"   ✅ {name}: 存在 ({size:.2f} KB)")
            else:
                file_status[name] = {"exists": False}
                print(f"   ❌ {name}: 缺失")

        self.test_results["file_integrity"] = {
            "status": "passed" if all(s["exists"] for s in file_status.values()) else "failed",
            "details": file_status,
        }

    async def _verify_dependencies(self):
        """验证依赖环境"""
        print("\n2️⃣ 验证依赖环境")
        print("-" * 40)

        import subprocess

        dependencies = {
            "python3": ["python3", "--version"],
            "pip3": ["pip3", "--version"],
            "node": ["node", "--version"],
            "npm": ["npm", "--version"],
            "chromedriver": ["chromedriver", "--version"],
            "aiohttp": ["pip3", "show", "aiohttp"],
            "beautifulsoup4": ["pip3", "show", "beautifulsoup4"],
            "selenium": ["pip3", "show", "selenium"],
            "requests": ["pip3", "show", "requests"],
        }

        dep_status = {}
        for dep, cmd in dependencies.items():
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    dep_status[dep] = {"installed": True, "version": result.stdout.strip()}
                    print(f"   ✅ {dep}: {result.stdout.strip()}")
                else:
                    dep_status[dep] = {"installed": False}
                    print(f"   ❌ {dep}: 未安装")
            except subprocess.TimeoutExpired:
                dep_status[dep] = {"installed": False, "error": "timeout"}
                print(f"   ⏰ {dep}: 检查超时")
            except Exception as e:
                dep_status[dep] = {"installed": False, "error": str(e)}
                print(f"   ❌ {dep}: {e!s}")

        # 计算通过率
        installed_count = sum(1 for d in dep_status.values() if d.get("installed"))
        total_count = len(dep_status)
        pass_rate = installed_count / total_count

        self.test_results["dependencies"] = {
            "status": "passed" if pass_rate >= 0.8 else "partial",
            "pass_rate": pass_rate,
            "details": dep_status,
        }

    async def _verify_core_functions(self):
        """验证核心功能"""
        print("\n3️⃣ 验证核心功能")
        print("-" * 40)

        try:
            # 测试爬虫控制器初始化
            controller = XiaonuoUniversalCrawlerController()
            print("   ✅ 爬虫控制器初始化成功")

            # 获取系统状态
            status = await controller.get_system_status()
            print("   ✅ 获取系统状态成功")

            # 验证服务注册
            services = status.get("services", {})
            expected_services = [
                "universal_crawler",
                "patent_crawler",
                "browser_automation",
                "distributed_crawler",
                "hybrid_manager",
                "douyin_scraper",
                "crawler_api",
            ]

            missing_services = [s for s in expected_services if s not in services]
            if not missing_services:
                print(f"   ✅ 所有爬虫服务已注册 ({len(services)}/{len(expected_services)})")
                service_status = "passed"
            else:
                print(f"   ⚠️ 缺少服务: {missing_services}")
                service_status = "partial"

            self.test_results["core_functions"] = {
                "status": service_status,
                "details": {
                    "controller_initialized": True,
                    "services_registered": len(services),
                    "expected_services": len(expected_services),
                    "missing_services": missing_services,
                },
            }

            await controller.shutdown()

        except Exception as e:
            print(f"   ❌ 核心功能验证失败: {e}")
            self.test_results["core_functions"] = {"status": "failed", "error": str(e)}

    async def _verify_intelligent_routing(self):
        """验证智能路由"""
        print("\n4️⃣ 验证智能路由")
        print("-" * 40)

        try:
            # 初始化路由器
            router = XiaonuoCrawlerIntelligentRouter()
            await router.initialize()
            print("   ✅ 智能路由器初始化成功")

            # 创建测试任务
            test_tasks = [
                CrawlerTask(
                    task_id="test_1",
                    service_type=CrawlerType.UNIVERSAL,
                    target_urls=["https://example.com"],
                    config={},
                ),
                CrawlerTask(
                    task_id="test_2",
                    service_type=CrawlerType.PATENT,
                    target_urls=["https://patents.google.com"],
                    config={},
                ),
            ]

            # 测试路由决策
            routing_results = []
            for task in test_tasks:
                decision = await router.route_task(task)
                routing_results.append(
                    {
                        "task_id": task.task_id,
                        "recommended": decision.get("service_type"),
                        "score": decision.get("score"),
                        "confidence": decision.get("confidence"),
                    }
                )
                print(
                    f"   ✅ 任务 {task.task_id}: {decision.get('service_type')} (评分: {decision.get('score', 0):.2f})"
                )

            self.test_results["intelligent_routing"] = {
                "status": "passed",
                "details": {"router_initialized": True, "routing_decisions": routing_results},
            }

        except Exception as e:
            print(f"   ❌ 智能路由验证失败: {e}")
            self.test_results["intelligent_routing"] = {"status": "failed", "error": str(e)}

    async def _verify_task_execution(self):
        """验证任务执行"""
        print("\n5️⃣ 验证任务执行")
        print("-" * 40)

        try:
            # 初始化控制器
            controller = XiaonuoUniversalCrawlerController()
            await controller.initialize()

            # 创建测试任务
            test_task = CrawlerTask(
                task_id=f"test_task_{int(time.time())}",
                service_type=CrawlerType.UNIVERSAL,
                target_urls=["https://httpbin.org/json", "https://httpbin.org/uuid"],
                config={"timeout": 10},
            )

            # 提交任务
            submit_result = await controller.submit_task(test_task)
            if submit_result.get("success"):
                print(f"   ✅ 任务提交成功: {test_task.task_id}")

                # 等待任务执行
                await asyncio.sleep(3)

                # 检查任务状态
                task_status = await controller.get_task_status(test_task.task_id)
                if task_status:
                    print(f"   📊 任务状态: {task_status.get('status')}")

                    execution_result = {
                        "task_submitted": True,
                        "task_status": task_status.get("status"),
                        "execution_complete": task_status.get("status") in ["completed", "failed"],
                    }

                    self.test_results["task_execution"] = {
                        "status": "passed",
                        "details": execution_result,
                    }
                else:
                    print("   ⚠️ 无法获取任务状态")
                    self.test_results["task_execution"] = {
                        "status": "partial",
                        "details": {"task_submitted": True, "status_retrieved": False},
                    }
            else:
                print(f"   ❌ 任务提交失败: {submit_result.get('message')}")
                self.test_results["task_execution"] = {
                    "status": "failed",
                    "error": submit_result.get("message"),
                }

            await controller.shutdown()

        except Exception as e:
            print(f"   ❌ 任务执行验证失败: {e}")
            self.test_results["task_execution"] = {"status": "failed", "error": str(e)}

    async def _generate_report(self):
        """生成验证报告"""
        print("\n📋 验证报告")
        print("=" * 60)

        # 统计结果
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results.values() if r["status"] == "passed")
        partial_tests = sum(1 for r in self.test_results.values() if r["status"] == "partial")
        failed_tests = total_tests - passed_tests - partial_tests

        print("\n📊 总体统计:")
        print(f"   总测试项: {total_tests}")
        print(f"   ✅ 通过: {passed_tests}")
        print(f"   ⚠️ 部分通过: {partial_tests}")
        print(f"   ❌ 失败: {failed_tests}")

        pass_rate = passed_tests / total_tests
        print(f"   通过率: {pass_rate:.1%}")

        # 详细结果
        print("\n📝 详细结果:")
        for test_name, result in self.test_results.items():
            status_icon = {"passed": "✅", "partial": "⚠️", "failed": "❌"}
            print(f"   {status_icon[result['status']]} {test_name}: {result['status']}")

            # 显示关键错误信息
            if result["status"] == "failed" and "error" in result:
                print(f"      错误: {result['error'][:100]}...")

        # 结论
        print("\n🎯 结论:")
        if pass_rate >= 0.9:
            print("   🟢 爬虫系统完整且可运行!小诺可以全量控制所有爬虫。")
        elif pass_rate >= 0.7:
            print("   🟡 爬虫系统基本可用,但需要解决部分问题。")
        else:
            print("   🔴 爬虫系统存在严重问题,需要修复后才能使用。")

        # 保存报告
        report_path = "/Users/xujian/Athena工作平台/logs/crawler_verification_report.json"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)

        report_data = {
            "verification_time": datetime.now().isoformat(),
            "duration_seconds": (datetime.now() - self.start_time).total_seconds(),
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "partial": partial_tests,
                "failed": failed_tests,
                "pass_rate": pass_rate,
            },
            "test_results": self.test_results,
        }

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        print(f"\n📄 详细报告已保存至: {report_path}")

        return pass_rate >= 0.9


@async_main
async def main():
    """主函数"""
    verifier = CrawlerSystemVerifier()
    success = await verifier.run_complete_verification()
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
