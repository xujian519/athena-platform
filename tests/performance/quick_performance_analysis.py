#!/usr/bin/env python3
"""
性能监控和基准测试脚本
Performance Monitoring and Benchmarking Script
"""

import asyncio
import json
import platform
import sqlite3
import statistics
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import aiohttp
import psutil


class PerformanceAnalyzer:
    """性能分析器"""

    def __init__(self):
        self.results = {}
        self.process = psutil.Process()
        self.start_time = datetime.now()

    def collect_system_metrics(self) -> dict[str, Any]:
        """收集系统指标"""
        return {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "memory_available_gb": psutil.virtual_memory().available / (1024**3),
            "disk_usage_percent": psutil.disk_usage("/").percent,
            "network_io": {
                "bytes_sent": psutil.net_io_counters().bytes_sent,
                "bytes_recv": psutil.net_io_counters().bytes_recv,
            },
        }

    def collect_process_metrics(self) -> dict[str, Any]:
        """收集进程指标"""
        memory_info = self.process.memory_info()
        return {
            "timestamp": datetime.now().isoformat(),
            "memory_rss_mb": memory_info.rss / (1024**2),
            "memory_vms_mb": memory_info.vms / (1024**2),
            "cpu_percent": self.process.cpu_percent(),
            "num_threads": self.process.num_threads(),
            "open_files": len(self.process.open_files()),
            "connections": len(self.process.net_connections()),
        }

    async def test_database_performance(self, db_path: str = None) -> dict[str, Any]:
        """测试数据库性能"""
        if db_path is None:
            # 查找默认数据库
            db_paths = [
                "/Users/xujian/Athena工作平台/data/athena.db",
                "/Users/xujian/Athena工作平台/data/memory.db",
                "/Users/xujian/Athena工作平台/data/goals.db",
            ]
            db_path = next((p for p in db_paths if Path(p).exists()), None)

        if not db_path:
            return {"error": "未找到数据库文件"}

        results = {"database_path": db_path, "tests": {}}

        try:
            # 连接测试
            start_time = time.time()
            conn = sqlite3.connect(db_path)
            connection_time = time.time() - start_time

            # 查询性能测试
            cursor = conn.cursor()

            # 测试简单查询
            queries = [
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table'",
                "PRAGMA table_info(goals)"
                if "goals"
                in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
                else "SELECT 1",
                "SELECT name FROM sqlite_master WHERE type='table' LIMIT 10",
            ]

            query_times = []
            for query in queries:
                try:
                    start_time = time.time()
                    cursor.execute(query)
                    cursor.fetchall()
                    query_time = time.time() - start_time
                    query_times.append(query_time)
                except Exception as e:
                    query_times.append(float("inf"))
                    print(f"查询失败: {query}, 错误: {e}")

            # 写入性能测试
            test_table = "performance_test"
            cursor.execute(
                f"CREATE TABLE IF NOT EXISTS {test_table} (id INTEGER PRIMARY KEY, data TEXT, timestamp DATETIME)"
            )

            insert_times = []
            for i in range(100):
                start_time = time.time()
                cursor.execute(
                    f"INSERT INTO {test_table} (data, timestamp) VALUES (?, ?)",
                    (f"test_data_{i}", datetime.now()),
                )
                insert_time = time.time() - start_time
                insert_times.append(insert_time)

            conn.commit()

            # 清理测试数据
            cursor.execute(f"DROP TABLE {test_table}")
            conn.commit()
            conn.close()

            results["tests"] = {
                "connection_time": connection_time,
                "avg_query_time": statistics.mean(query_times),
                "max_query_time": max(query_times),
                "min_query_time": min(query_times),
                "avg_insert_time": statistics.mean(insert_times),
                "max_insert_time": max(insert_times),
                "min_insert_time": min(insert_times),
                "total_inserts": len(insert_times),
            }

        except Exception as e:
            results["error"] = str(e)

        return results

    async def test_api_response_time(
        self, base_url: str = "http://localhost:8005"
    ) -> dict[str, Any]:
        """测试API响应时间"""
        endpoints = ["/", "/api/health", "/api/status", "/api/agents"]

        results = {"base_url": base_url, "endpoints": {}}

        timeout = aiohttp.ClientTimeout(total=10)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            for endpoint in endpoints:
                url = f"{base_url}{endpoint}"

                try:
                    # 测试多次请求
                    response_times = []
                    success_count = 0

                    for _ in range(10):
                        start_time = time.time()
                        async with session.get(url) as response:
                            await response.text()
                            response_time = time.time() - start_time

                            if response.status == 200:
                                response_times.append(response_time)
                                success_count += 1

                    if response_times:
                        results["endpoints"][endpoint] = {
                            "avg_response_time": statistics.mean(response_times),
                            "min_response_time": min(response_times),
                            "max_response_time": max(response_times),
                            "success_rate": success_count / 10,
                            "status_code": 200,
                        }
                    else:
                        results["endpoints"][endpoint] = {
                            "error": "所有请求都失败了",
                            "success_rate": 0,
                        }

                except Exception as e:
                    results["endpoints"][endpoint] = {"error": str(e), "success_rate": 0}

        return results

    async def test_concurrent_load(self, num_concurrent: int = 50) -> dict[str, Any]:
        """测试并发负载"""

        async def make_request(session, url):
            try:
                start_time = time.time()
                async with session.get(url) as response:
                    await response.text()
                    return {
                        "response_time": time.time() - start_time,
                        "success": response.status == 200,
                        "status_code": response.status,
                    }
            except Exception as e:
                return {"response_time": float("inf"), "success": False, "error": str(e)}

        base_url = "http://localhost:8005"
        url = f"{base_url}/api/health"

        timeout = aiohttp.ClientTimeout(total=30)

        start_time = time.time()
        async with aiohttp.ClientSession(timeout=timeout) as session:
            tasks = [make_request(session, url) for _ in range(num_concurrent)]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        total_time = time.time() - start_time

        # 分析结果
        successful_requests = [
            r for r in results if isinstance(r, dict) and r.get("success", False)
        ]
        failed_requests = [
            r for r in results if isinstance(r, dict) and not r.get("success", False)
        ]

        if successful_requests:
            response_times = [r["response_time"] for r in successful_requests]
            return {
                "total_time": total_time,
                "num_concurrent": num_concurrent,
                "successful_requests": len(successful_requests),
                "failed_requests": len(failed_requests),
                "success_rate": len(successful_requests) / num_concurrent,
                "avg_response_time": statistics.mean(response_times),
                "min_response_time": min(response_times),
                "max_response_time": max(response_times),
                "requests_per_second": num_concurrent / total_time,
            }
        else:
            return {
                "total_time": total_time,
                "num_concurrent": num_concurrent,
                "successful_requests": 0,
                "failed_requests": len(failed_requests),
                "success_rate": 0,
                "error": "所有并发请求都失败了",
            }

    def analyze_memory_patterns(self, duration: int = 60) -> dict[str, Any]:
        """分析内存使用模式"""
        print(f"🧠 开始分析内存使用模式，持续{duration}秒...")

        memory_samples = []
        cpu_samples = []

        start_time = time.time()
        while time.time() - start_time < duration:
            memory_info = self.process.memory_info()
            memory_samples.append(memory_info.rss / (1024**2))  # MB
            cpu_samples.append(self.process.cpu_percent())
            time.sleep(1)

        return {
            "duration_seconds": duration,
            "samples_count": len(memory_samples),
            "memory": {
                "initial_mb": memory_samples[0],
                "final_mb": memory_samples[-1],
                "peak_mb": max(memory_samples),
                "min_mb": min(memory_samples),
                "avg_mb": statistics.mean(memory_samples),
                "std_dev_mb": statistics.stdev(memory_samples) if len(memory_samples) > 1 else 0,
                "growth_mb": memory_samples[-1] - memory_samples[0],
            },
            "cpu": {
                "avg_percent": statistics.mean(cpu_samples),
                "max_percent": max(cpu_samples),
                "min_percent": min(cpu_samples),
            },
        }

    def generate_performance_report(self) -> dict[str, Any]:
        """生成性能报告"""
        print("📊 生成性能分析报告...")

        report = {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "analysis_duration": str(datetime.now() - self.start_time),
                "system_info": {
                    "platform": platform.platform(),
                    "python_version": platform.python_version(),
                    "cpu_count": psutil.cpu_count(),
                    "memory_total_gb": psutil.virtual_memory().total / (1024**3),
                },
            }
        }

        return report

    async def run_comprehensive_analysis(self) -> dict[str, Any]:
        """运行综合性能分析"""
        print("🚀 开始综合性能分析...")
        print("=" * 60)

        # 1. 基础指标收集
        print("📈 收集基础系统指标...")
        system_metrics = self.collect_system_metrics()
        process_metrics = self.collect_process_metrics()

        # 2. 数据库性能测试
        print("🗄️ 测试数据库性能...")
        db_performance = await self.test_database_performance()

        # 3. API响应时间测试
        print("🌐 测试API响应时间...")
        api_performance = await self.test_api_response_time()

        # 4. 并发负载测试
        print("⚡ 测试并发负载...")
        concurrent_performance = await self.test_concurrent_load()

        # 5. 内存模式分析
        print("🧠 分析内存使用模式...")
        memory_patterns = self.analyze_memory_patterns(duration=30)

        # 6. 生成综合报告
        print("📋 生成综合报告...")
        performance_report = self.generate_performance_report()

        # 整合所有结果
        comprehensive_results = {
            "analysis_type": "comprehensive_performance_analysis",
            "timestamp": datetime.now().isoformat(),
            "system_metrics": system_metrics,
            "process_metrics": process_metrics,
            "database_performance": db_performance,
            "api_performance": api_performance,
            "concurrent_performance": concurrent_performance,
            "memory_patterns": memory_patterns,
            "performance_report": performance_report,
        }

        return comprehensive_results

    def save_results(self, results: dict[str, Any], filename: str = None):
        """保存分析结果"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_analysis_{timestamp}.json"

        reports_dir = Path("/Users/xujian/Athena工作平台/tests/reports")
        reports_dir.mkdir(exist_ok=True)

        report_file = reports_dir / filename
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"📄 性能分析报告已保存: {report_file}")
        return str(report_file)


async def main():
    """主函数"""
    analyzer = PerformanceAnalyzer()

    try:
        # 运行综合分析
        results = await analyzer.run_comprehensive_analysis()

        # 保存结果
        report_file = analyzer.save_results(results)

        # 生成优化建议
        print("\n" + "=" * 60)
        print("🎯 性能优化建议")
        print("=" * 60)

        # 分析结果并提供建议
        suggestions = []

        # CPU使用率分析
        cpu_percent = results["system_metrics"]["cpu_percent"]
        if cpu_percent > 80:
            suggestions.append("⚠️ CPU使用率过高，建议优化算法或增加处理能力")
        elif cpu_percent < 20:
            suggestions.append("✅ CPU使用率正常，系统负载较轻")

        # 内存使用分析
        memory_percent = results["system_metrics"]["memory_percent"]
        if memory_percent > 85:
            suggestions.append("⚠️ 内存使用率过高，建议优化内存使用或增加内存")

        memory_growth = results["memory_patterns"]["memory"]["growth_mb"]
        if memory_growth > 50:
            suggestions.append("⚠️ 检测到内存增长过快，可能存在内存泄漏")
        elif memory_growth < 0:
            suggestions.append("✅ 内存使用稳定，无内存泄漏迹象")

        # API性能分析
        if "api_performance" in results and "endpoints" in results["api_performance"]:
            endpoints = results["api_performance"]["endpoints"]
            for endpoint, data in endpoints.items():
                if "avg_response_time" in data and data["avg_response_time"] > 2.0:
                    suggestions.append(
                        f"⚠️ 端点 {endpoint} 响应时间过长 ({data['avg_response_time']:.3f}s)"
                    )

        # 并发性能分析
        if "concurrent_performance" in results:
            concurrent = results["concurrent_performance"]
            success_rate = concurrent.get("success_rate", 0)
            if success_rate < 0.9:
                suggestions.append(f"⚠️ 并发请求成功率过低 ({success_rate:.1%})")

        # 数据库性能分析
        if "database_performance" in results and "tests" in results["database_performance"]:
            db_tests = results["database_performance"]["tests"]
            if "avg_query_time" in db_tests and db_tests["avg_query_time"] > 1.0:
                suggestions.append("⚠️ 数据库查询时间过长，建议优化查询或添加索引")

        if not suggestions:
            suggestions.append("✅ 系统性能表现良好，未发现明显问题")

        for suggestion in suggestions:
            print(suggestion)

        print(f"\n📊 详细报告: {report_file}")

    except Exception as e:
        print(f"❌ 性能分析失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
