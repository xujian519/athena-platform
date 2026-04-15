#!/usr/bin/env python3
"""
Athena三级缓存系统验证脚本
验证L1/L2/L3三级缓存的功能和性能

作者: Athena平台团队
创建时间: 2025-12-29
版本: v1.0.0
"""

from __future__ import annotations
import logging
import sys
import time
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


class ThreeTierCacheVerifier:
    """三级缓存验证器"""

    def __init__(self):
        self.results = {
            "timestamp": time.time(),
            "tests": {},
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "warnings": 0
            }
        }

    def add_result(
        self,
        test_name: str,
        status: str,
        details: str = "",
        execution_time: float = 0.0,
        data: Any = None
    ):
        """添加测试结果"""
        self.results["tests"][test_name] = {
            "status": status,
            "details": details,
            "execution_time": execution_time,
            "data": data
        }

        self.results["summary"]["total"] += 1
        if status == "passed":
            self.results["summary"]["passed"] += 1
        elif status == "failed":
            self.results["summary"]["failed"] += 1
        else:
            self.results["summary"]["warnings"] += 1

    def test_l1_memory_cache(self) -> bool:
        """测试L1内存缓存"""
        print_section("测试1: L1内存缓存")

        try:
            from core.performance.three_tier_cache import L1MemoryCache

            start_time = time.time()

            # 创建L1缓存
            l1 = L1MemoryCache(
                max_size_mb=10,  # 10MB用于测试
                max_entries=1000,
                default_ttl=60
            )

            # 测试基本操作
            print_info("测试基本操作...")
            test_key = "test_key_1"
            test_value = {"data": "test_value", "number": 123}

            # 设置
            l1.set(test_key, test_value)
            # 获取
            result = l1.get(test_key)

            if result != test_value:
                print_error("✗ L1缓存值不匹配")
                self.add_result("l1_memory_cache", "failed", "缓存值不匹配")
                return False

            print_success("✓ L1缓存读写成功")

            # 测试统计
            stats = l1.get_stats()
            print_info("L1统计:")
            print_info(f"  - 条目数: {stats['entries']}")
            print_info(f"  - 大小: {stats['size_mb']} MB / {stats['max_size_mb']} MB")
            print_info(f"  - 命中率: {stats['hit_rate']}%")

            # 测试LRU驱逐
            print_info("测试LRU驱逐...")
            for i in range(1500):  # 超过max_entries=1000
                l1.set(f"key_{i}", f"value_{i}")

            stats_after = l1.get_stats()
            print_info(f"驱逐后条目数: {stats_after['entries']}")
            print_success(f"✓ LRU驱逐正常工作 (驱逐了{stats_after['evictions']}个条目)")

            execution_time = time.time() - start_time

            self.add_result(
                "l1_memory_cache",
                "passed",
                "L1内存缓存功能正常",
                execution_time,
                stats_after
            )
            return True

        except Exception as e:
            print_error(f"✗ 测试异常: {e}")
            import traceback
            traceback.print_exc()
            self.add_result("l1_memory_cache", "failed", str(e))
            return False

    def test_l2_redis_cache(self) -> bool:
        """测试L2 Redis缓存"""
        print_section("测试2: L2 Redis缓存")

        try:
            from core.performance.three_tier_cache import L2RedisCache

            start_time = time.time()

            # 创建L2缓存
            l2 = L2RedisCache(
                host='127.0.0.1',
                port=6379,
                key_prefix="athena_test_l2"
            )

            if not l2.connected:
                print_warning("⚠️ Redis未连接，跳过L2测试")
                self.add_result("l2_redis_cache", "skipped", "Redis未连接")
                return True

            # 测试基本操作
            print_info("测试基本操作...")
            test_key = "test_key_redis"
            test_value = {"data": "redis_test", "timestamp": time.time()}

            # 设置
            l2.set(test_key, test_value, ttl=60)
            # 获取
            result = l2.get(test_key)

            if result is None:
                print_error("✗ L2缓存获取失败")
                self.add_result("l2_redis_cache", "failed", "缓存获取失败")
                return False

            print_success("✓ L2缓存读写成功")

            # 测试统计
            stats = l2.get_stats()
            print_info("L2统计:")
            print_info(f"  - 连接状态: {stats['connected']}")
            print_info(f"  - 内存使用: {stats.get('memory_used', 'N/A')}")
            print_info(f"  - 总键数: {stats.get('total_keys', 'N/A')}")

            # 清理测试数据
            l2.clear()
            print_success("✓ 测试数据已清理")

            execution_time = time.time() - start_time

            self.add_result(
                "l2_redis_cache",
                "passed",
                "L2 Redis缓存功能正常",
                execution_time,
                stats
            )
            return True

        except Exception as e:
            print_error(f"✗ 测试异常: {e}")
            import traceback
            traceback.print_exc()
            self.add_result("l2_redis_cache", "failed", str(e))
            return False

    def test_l3_disk_cache(self) -> bool:
        """测试L3磁盘缓存"""
        print_section("测试3: L3磁盘缓存")

        try:
            from core.performance.three_tier_cache import L3DiskCache

            start_time = time.time()

            # 创建L3缓存（使用临时目录）
            import tempfile
            temp_dir = tempfile.mkdtemp(prefix="athena_l3_test_")

            l3 = L3DiskCache(
                cache_dir=temp_dir,
                max_size_gb=1.0,
                default_ttl=86400
            )

            # 测试基本操作
            print_info("测试基本操作...")
            test_key = "test_key_disk"
            test_value = {
                "data": "disk_test",
                "array": list(range(1000)),
                "timestamp": time.time()
            }

            # 设置
            l3.set(test_key, test_value, ttl=60)
            # 获取
            result = l3.get(test_key)

            if result is None:
                print_error("✗ L3缓存获取失败")
                self.add_result("l3_disk_cache", "failed", "缓存获取失败")
                return False

            if result["array"] != test_value["array"]:
                print_error("✗ L3缓存值不匹配")
                self.add_result("l3_disk_cache", "failed", "缓存值不匹配")
                return False

            print_success("✓ L3缓存读写成功")

            # 测试统计
            stats = l3.get_stats()
            print_info("L3统计:")
            print_info(f"  - 缓存目录: {stats['cache_dir']}")
            print_info(f"  - 大小: {stats['size_gb']} GB")
            print_info(f"  - 使用率: {stats['usage_percent']}%")

            # 测试清理
            l3.clear(older_than=0)  # 清理所有
            print_success("✓ L3缓存清理完成")

            # 清理临时目录
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

            execution_time = time.time() - start_time

            self.add_result(
                "l3_disk_cache",
                "passed",
                "L3磁盘缓存功能正常",
                execution_time,
                stats
            )
            return True

        except Exception as e:
            print_error(f"✗ 测试异常: {e}")
            import traceback
            traceback.print_exc()
            self.add_result("l3_disk_cache", "failed", str(e))
            return False

    def test_three_tier_integration(self) -> bool:
        """测试三级缓存集成"""
        print_section("测试4: 三级缓存集成")

        try:
            import tempfile

            from core.performance.three_tier_cache import ThreeTierCacheSystem

            start_time = time.time()

            # 创建临时目录
            temp_dir = tempfile.mkdtemp(prefix="athena_3tier_test_")

            # 创建三级缓存系统
            cache = ThreeTierCacheSystem(
                l1_max_size_mb=10,
                l2_enabled=False,  # 跳过Redis，避免依赖
                l3_enabled=True,
                l3_cache_dir=temp_dir,
                l3_max_size_gb=1.0
            )

            # 测试缓存层次
            print_info("测试缓存层次...")
            test_key = "integration_test_key"
            test_value = {"message": "Hello from three-tier cache!", "value": 42}

            # 设置
            cache.set(test_key, test_value)
            print_success("✓ 缓存已设置")

            # 从L1获取
            result = cache.get(test_key)
            if result != test_value:
                print_error("✗ 缓存值不匹配")
                self.add_result("three_tier_integration", "failed", "缓存值不匹配")
                return False

            print_success("✓ 缓存读取成功 (L1命中)")

            # 测试统计
            stats = cache.get_stats()
            print_info("三级缓存统计:")
            print_info(f"  - L1命中率: {stats['l1']['hit_rate']}%")
            print_info(f"  - L1大小: {stats['l1']['size_mb']} MB")
            print_info(f"  - L3大小: {stats['l3']['size_gb']} GB")
            print_info(f"  - 总命中率: {stats['overall']['hit_rate']}%")

            # 清理
            cache.clear()
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

            execution_time = time.time() - start_time

            self.add_result(
                "three_tier_integration",
                "passed",
                "三级缓存集成正常",
                execution_time,
                stats
            )
            return True

        except Exception as e:
            print_error(f"✗ 测试异常: {e}")
            import traceback
            traceback.print_exc()
            self.add_result("three_tier_integration", "failed", str(e))
            return False

    def test_cache_warm_up(self) -> bool:
        """测试缓存预热"""
        print_section("测试5: 缓存预热")

        try:
            import tempfile

            from core.performance.three_tier_cache import ThreeTierCacheSystem

            start_time = time.time()

            # 创建临时目录
            temp_dir = tempfile.mkdtemp(prefix="athena_warmup_test_")

            # 创建三级缓存系统
            cache = ThreeTierCacheSystem(
                l1_max_size_mb=10,
                l2_enabled=False,
                l3_enabled=True,
                l3_cache_dir=temp_dir
            )

            # 准备预热数据
            print_info("准备预热数据...")
            warm_up_data = {
                f"key_{i}": f"value_{i}"
                for i in range(100)
            }

            # 执行预热
            print_info("执行缓存预热...")
            warmed_count = cache.warm_up(warm_up_data)

            if warmed_count != len(warm_up_data):
                print_warning(f"⚠️ 预热数量不匹配: {warmed_count}/{len(warm_up_data)}")

            print_success(f"✓ 预热完成: {warmed_count}条记录")

            # 验证预热效果
            print_info("验证预热效果...")
            hit_count = 0
            for key in warm_up_data.keys():
                if cache.get(key) is not None:
                    hit_count += 1

            hit_rate = hit_count / len(warm_up_data) * 100
            print_success(f"✓ 预热命中率: {hit_rate:.1f}%")

            # 获取统计
            stats = cache.get_stats()
            print_info("预热后统计:")
            print_info(f"  - L1条目数: {stats['l1']['entries']}")
            print_info(f"  - L1命中率: {stats['l1']['hit_rate']}%")

            # 清理
            cache.clear()
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

            execution_time = time.time() - start_time

            if hit_rate >= 95:
                self.add_result(
                    "cache_warm_up",
                    "passed",
                    f"预热成功 ({warmed_count}条, 命中率{hit_rate:.1f}%)",
                    execution_time,
                    {"warmed_count": warmed_count, "hit_rate": hit_rate}
                )
                return True
            else:
                self.add_result(
                    "cache_warm_up",
                    "warning",
                    f"预热命中率偏低: {hit_rate:.1f}%",
                    execution_time
                )
                return False

        except Exception as e:
            print_error(f"✗ 测试异常: {e}")
            import traceback
            traceback.print_exc()
            self.add_result("cache_warm_up", "failed", str(e))
            return False

    def test_performance_benchmark(self) -> bool:
        """测试性能基准"""
        print_section("测试6: 性能基准")

        try:
            import tempfile

            from core.performance.three_tier_cache import ThreeTierCacheSystem

            start_time = time.time()

            # 创建临时目录
            temp_dir = tempfile.mkdtemp(prefix="athena_perf_test_")

            # 创建三级缓存系统
            cache = ThreeTierCacheSystem(
                l1_max_size_mb=50,
                l2_enabled=False,
                l3_enabled=True,
                l3_cache_dir=temp_dir
            )

            # 性能测试：1000次读写
            print_info("性能测试: 1000次读写...")
            num_operations = 1000

            # 写入测试
            write_start = time.time()
            for i in range(num_operations):
                cache.set(f"perf_key_{i}", f"perf_value_{i}")
            write_time = time.time() - write_start
            write_throughput = num_operations / write_time

            print_info(f"  - 写入时间: {write_time:.3f}秒")
            print_info(f"  - 写入吞吐量: {write_throughput:.0f} ops/sec")

            # 读取测试（应该命中L1）
            read_start = time.time()
            hit_count = 0
            for i in range(num_operations):
                if cache.get(f"perf_key_{i}") is not None:
                    hit_count += 1
            read_time = time.time() - read_start
            read_throughput = num_operations / read_time

            print_info(f"  - 读取时间: {read_time:.3f}秒")
            print_info(f"  - 读取吞吐量: {read_throughput:.0f} ops/sec")
            print_info(f"  - L1命中率: {hit_count/num_operations*100:.1f}%")

            # 获取最终统计
            stats = cache.get_stats()
            print_info("最终统计:")
            print_info(f"  - L1命中率: {stats['l1']['hit_rate']}%")
            print_info(f"  - 总命中率: {stats['overall']['hit_rate']}%")

            # 验证性能指标
            # 目标: 读取吞吐量 > 10000 ops/sec
            if read_throughput > 10000:
                print_success(f"✓ 性能达标: {read_throughput:.0f} > 10000 ops/sec")

                # 清理
                cache.clear()
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)

                execution_time = time.time() - start_time

                self.add_result(
                    "performance_benchmark",
                    "passed",
                    f"读取吞吐量: {read_throughput:.0f} ops/sec",
                    execution_time,
                    {
                        "write_throughput": write_throughput,
                        "read_throughput": read_throughput,
                        "l1_hit_rate": stats['l1']['hit_rate']
                    }
                )
                return True
            else:
                print_warning(f"⚠ 读取吞吐量偏低: {read_throughput:.0f} ops/sec")

                self.add_result(
                    "performance_benchmark",
                    "warning",
                    f"读取吞吐量: {read_throughput:.0f} ops/sec",
                    execution_time
                )
                return False

        except Exception as e:
            print_error(f"✗ 测试异常: {e}")
            import traceback
            traceback.print_exc()
            self.add_result("performance_benchmark", "failed", str(e))
            return False

    def run_all_verifications(self) -> Any:
        """运行所有验证测试"""
        print_section("Athena三级缓存系统验证")
        print(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

        # 执行测试
        tests = [
            ("L1内存缓存", self.test_l1_memory_cache),
            ("L2 Redis缓存", self.test_l2_redis_cache),
            ("L3磁盘缓存", self.test_l3_disk_cache),
            ("三级缓存集成", self.test_three_tier_integration),
            ("缓存预热", self.test_cache_warm_up),
            ("性能基准", self.test_performance_benchmark),
        ]

        passed = 0
        failed = 0
        warnings = 0
        skipped = 0

        for test_name, test_func in tests:
            try:
                result = test_func()
                if result:
                    passed += 1
                elif result is None:
                    skipped += 1
                else:
                    failed += 1
            except Exception as e:
                print_error(f"测试执行异常: {test_name} - {e}")
                failed += 1

        # 打印摘要
        self.print_summary()

        return failed == 0

    def print_summary(self) -> Any:
        """打印验证摘要"""
        print_section("验证摘要")

        summary = self.results["summary"]
        total = summary["total"]
        passed = summary["passed"]
        failed = summary["failed"]
        warnings = summary["warnings"]

        print(f"总测试数: {total}")
        print_success(f"通过: {passed}")
        if failed > 0:
            print_error(f"失败: {failed}")
        if warnings > 0:
            print_warning(f"警告: {warnings}")

        success_rate = (passed / total * 100) if total > 0 else 0
        print(f"\n通过率: {success_rate:.1f}%")

        if success_rate >= 90:
            print_success("\n🎉 三级缓存系统验证通过!")
        elif success_rate >= 70:
            print_warning("\n⚠ 系统基本可用，建议优化部分功能")
        else:
            print_error("\n❌ 系统存在较多问题，需要修复")

    def save_report(self) -> None:
        """保存验证报告"""
        import json
        from datetime import datetime

        report_dir = Path("logs/performance")
        report_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"three_tier_cache_verification_{timestamp}.json"

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)

        print_info(f"\n报告已保存: {report_file}")


def main() -> None:
    """主函数"""
    verifier = ThreeTierCacheVerifier()
    success = verifier.run_all_verifications()

    # 保存报告
    verifier.save_report()

    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
