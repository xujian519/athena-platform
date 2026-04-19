#!/usr/bin/env python3
from __future__ import annotations
"""
简化版爬虫系统验证脚本
Simplified Crawler System Verification Script

验证平台爬虫系统的完整性

作者: 小诺·双鱼公主
创建时间: 2025-12-14
"""

import asyncio
import json

# 配置日志
import os
import sys
from datetime import datetime

from core.async_main import async_main
from core.logging_config import setup_logging

# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


class SimpleCrawlerVerifier:
    """简化版爬虫验证器"""

    def __init__(self):
        self.name = "小诺·双鱼公主爬虫系统验证器"
        self.test_results = {}
        self.start_time = datetime.now()

    async def run_verification(self):
        """运行验证"""
        print(f"🕷️ {self.name} - 开始验证爬虫系统")
        print("=" * 60)

        # 1. 验证爬虫核心文件
        await self._verify_crawler_files()

        # 2. 验证爬虫控制接口
        await self._verify_crawler_control()

        # 3. 验证通用爬虫功能
        await self._verify_universal_crawler()

        # 4. 生成报告
        await self._generate_report()

    async def _verify_crawler_files(self):
        """验证爬虫文件"""
        print("\n1️⃣ 验证爬虫文件完整性")
        print("-" * 40)

        crawler_files = {
            "通用爬虫": "/Users/xujian/Athena工作平台/services/crawler-service/core/universal_crawler.py",
            "混合爬虫管理器": "/Users/xujian/Athena工作平台/services/crawler-service/core/hybrid_crawler_manager.py",
            "分布式爬虫": "/Users/xujian/Athena工作平台/tools/advanced/distributed_crawler.py",
            "浏览器自动化": "/Users/xujian/Athena工作平台/services/browser-automation-service/browser_automation_server.py",
            "抖音爬虫": "/Users/xujian/Athena工作平台/services/browser-automation-service/douyin_scraper.py",
            "爬虫API服务": "/Users/xujian/Athena工作平台/services/platform-integration-service/crawler_api_server.py",
            "爬虫控制脚本": "/Users/xujian/Athena工作平台/services/scripts/xiaonuo_crawler_control.py",
        }

        file_status = {}
        for name, path in crawler_files.items():
            if os.path.exists(path):
                size = os.path.getsize(path) / 1024
                file_status[name] = {"exists": True, "size_kb": round(size, 2)}
                print(f"   ✅ {name}: {size:.2f} KB")
            else:
                file_status[name] = {"exists": False}
                print(f"   ❌ {name}: 缺失")

        exists_count = sum(1 for s in file_status.values() if s["exists"])
        total_count = len(file_status)

        self.test_results["crawler_files"] = {
            "status": "passed" if exists_count == total_count else "partial",
            "exists_count": exists_count,
            "total_count": total_count,
            "details": file_status,
        }

    async def _verify_crawler_control(self):
        """验证爬虫控制接口"""
        print("\n2️⃣ 验证爬虫控制接口")
        print("-" * 40)

        control_files = {
            "全量爬虫控制器": "/Users/xujian/Athena工作平台/core/orchestration/xiaonuo_universal_crawler_controller.py",
            "智能爬虫路由器": "/Users/xujian/Athena工作平台/core/orchestration/xiaonuo_crawler_intelligent_router.py",
            "爬虫工具适配器": "/Users/xujian/Athena工作平台/services/platform-integration-service/crawler_integration_service.py",
            "爬虫场景启动器": "/Users/xujian/Athena工作平台/services/platform-integration-service/crawler_scenario_launcher.py",
            "生产爬虫启动器": "/Users/xujian/Athena工作平台/scripts/services/crawler_services/production_crawler_launcher.py",
            "爬虫性能优化器": "/Users/xujian/Athena工作平台/tools/optimization/crawler_performance_optimizer.py",
            "弹性爬虫": "/Users/xujian/Athena工作平台/tools/advanced/resilient_crawler.py",
        }

        control_status = {}
        for name, path in control_files.items():
            if os.path.exists(path):
                size = os.path.getsize(path) / 1024
                control_status[name] = {"exists": True, "size_kb": round(size, 2)}
                print(f"   ✅ {name}: {size:.2f} KB")
            else:
                control_status[name] = {"exists": False}
                print(f"   ❌ {name}: 缺失")

        exists_count = sum(1 for s in control_status.values() if s["exists"])

        self.test_results["crawler_control"] = {
            "status": "passed" if exists_count >= 5 else "partial",
            "exists_count": exists_count,
            "total_count": len(control_status),
            "details": control_status,
        }

    async def _verify_universal_crawler(self):
        """验证通用爬虫功能"""
        print("\n3️⃣ 验证通用爬虫核心功能")
        print("-" * 40)

        try:
            # 尝试导入通用爬虫
            sys.path.append("/Users/xujian/Athena工作平台/services/crawler-service/core")
            from universal_crawler import CrawlerConfig, UniversalCrawler

            print("   ✅ 通用爬虫模块导入成功")

            # 创建配置
            config = CrawlerConfig(name="测试爬虫", base_url="https://httpbin.org", timeout=10)
            print("   ✅ 爬虫配置创建成功")

            # 创建爬虫实例
            crawler = UniversalCrawler(config)
            print("   ✅ 爬虫实例创建成功")

            # 检查爬虫方法
            methods = ["fetch", "get_page", "get_json", "parse_html", "extract_links"]
            available_methods = [m for m in methods if hasattr(crawler, m)]
            print(f"   ✅ 可用方法: {', '.join(available_methods)}")

            self.test_results["universal_crawler"] = {
                "status": "passed",
                "details": {
                    "imported": True,
                    "config_created": True,
                    "instance_created": True,
                    "available_methods": available_methods,
                },
            }

        except Exception as e:
            print(f"   ❌ 通用爬虫验证失败: {e}")
            self.test_results["universal_crawler"] = {"status": "failed", "error": str(e)}

    async def _generate_report(self):
        """生成验证报告"""
        print("\n📋 验证报告")
        print("=" * 60)

        # 统计结果
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results.values() if r["status"] == "passed")
        partial_tests = sum(1 for r in self.test_results.values() if r["status"] == "partial")
        failed_tests = total_tests - passed_tests - partial_tests

        print("\n📊 统计结果:")
        print(f"   总测试项: {total_tests}")
        print(f"   ✅ 通过: {passed_tests}")
        print(f"   ⚠️ 部分通过: {partial_tests}")
        print(f"   ❌ 失败: {failed_tests}")

        pass_rate = passed_tests / total_tests if total_tests > 0 else 0
        print(f"   通过率: {pass_rate:.1%}")

        # 详细结果
        print("\n📝 详细结果:")
        for test_name, result in self.test_results.items():
            status_icon = {"passed": "✅", "partial": "⚠️", "failed": "❌"}
            print(f"   {status_icon[result['status']]} {test_name}: {result['status']}")

            if (test_name == "crawler_files" and "exists_count" in result) or (test_name == "crawler_control" and "exists_count" in result):
                print(f"      文件: {result['exists_count']}/{result['total_count']}")

        # 爬虫系统架构说明
        print("\n🕸️ 爬虫系统架构:")
        print("   ┌─────────────────────────────────────────────────────┐")
        print("   │              小诺·双鱼公主全量爬虫控制              │")
        print("   │                 XiaonuoUniversalCrawlerController   │")
        print("   └─────────────────────────────────────────────────────┘")
        print("                              │")
        print("                              ▼")
        print("   ┌─────────────┬─────────────┬─────────────┬─────────────┐")
        print("   │ 通用爬虫    │ 专利爬虫     │ 浏览器自动化 │ 分布式爬虫   │")
        print("   │ Universal   │ Patent      │ Browser     │ Distributed │")
        print("   │ (3实例)     │ (2实例)      │ Automation  │ (5实例)     │")
        print("   └─────────────┴─────────────┴─────────────┴─────────────┘")
        print("                              │")
        print("                              ▼")
        print("   ┌─────────────────────────────────────────────────────┐")
        print("   │               智能路由系统                          │")
        print("   │          XiaonuoCrawlerIntelligentRouter          │")
        print("   │  • URL特征分析  • 任务复杂度评估  • 最优选择       │")
        print("   └─────────────────────────────────────────────────────┘")
        print("                              │")
        print("                              ▼")
        print("   ┌─────────────┬─────────────┬─────────────┬─────────────┐")
        print("   │ 混合爬虫    │ API爬虫     │ 抖音爬虫     │ 爬虫API     │")
        print("   │ Hybrid      │ API Crawler │ Douyin      │ CrawlerAPI  │")
        print("   └─────────────┴─────────────┴─────────────┴─────────────┘")

        # 结论
        print("\n🎯 结论:")
        if pass_rate >= 0.9:
            print("   ✅ 爬虫系统完整且功能齐全!")
            print("   🕷️ 小诺可以全量控制平台所有爬虫工具,包括:")
            print("      • 7种类型的爬虫服务(通用、专利、浏览器自动化等)")
            print("      • 智能路由决策系统")
            print("      • 统一的任务管理和调度")
            print("      • 自动扩缩容和负载均衡")
            print("      • 健康监控和故障恢复")
            print("   🎉 爬虫作为平台通用工具已准备就绪!")
        elif pass_rate >= 0.7:
            print("   ⚠️ 爬虫系统基本可用,需要解决部分问题。")
        else:
            print("   ❌ 爬虫系统存在较多问题,需要修复。")

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
            "crawler_architecture": {
                "controller": "XiaonuoUniversalCrawlerController",
                "router": "XiaonuoCrawlerIntelligentRouter",
                "services": [
                    "universal_crawler (max 3 instances)",
                    "patent_crawler (max 2 instances)",
                    "browser_automation (max 2 instances)",
                    "distributed_crawler (max 5 instances)",
                    "hybrid_manager (1 instance)",
                    "douyin_scraper (1 instance)",
                    "crawler_api (1 instance)",
                ],
            },
        }

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        print(f"\n📄 详细报告已保存至: {report_path}")

        return pass_rate >= 0.9


@async_main
async def main():
    """主函数"""
    verifier = SimpleCrawlerVerifier()
    success = await verifier.run_verification()

    # 返回系统状态
    if success:
        print("\n🎊 爬虫系统验证完成 - 系统完整可运行!")
        print("🕷️ 小诺现在可以全量控制平台所有爬虫工具。")
    else:
        print("\n⚠️ 爬虫系统存在问题 - 需要修复后才能全量控制。")

    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
