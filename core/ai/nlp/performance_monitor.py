#!/usr/bin/env python3

"""
NLP性能监控系统
NLP Performance Monitor

实时监控NLP系统性能,提供性能分析和优化建议

作者: 系统管理员
创建时间: 2025-12-20
版本: v1.0.0
"""

import json
import statistics
import threading
import time
from datetime import datetime
from typing import Any

import psutil


class PerformanceMonitor:
    """性能监控器 - 🔧 线程安全修复:改进锁机制和资源管理"""

    def __init__(self, history_size: int = 10000):
        self.history_size = history_size
        self.metrics = {
            "inference_times": [],
            "memory_usage": [],
            "cache_hit_rates": {},
            "error_rates": {},
            "system_resources": [],
        }

        # 线程安全修复:使用RLock允许可重入
        self.lock = threading.RLock()
        self.start_time = datetime.now()
        self.last_report_time = self.start_time

        # 性能阈值
        self.thresholds = {
            "inference_time_warning": 1.0,  # 1秒警告阈值
            "inference_time_critical": 2.0,  # 2秒严重阈值
            "memory_usage_warning": 0.8,  # 80%内存警告
            "cache_hit_rate_minimum": 0.7,  # 70%缓存命中率最低要求
            "error_rate_maximum": 0.05,  # 5%错误率最高容忍
        }

    def record_inference_time(self, operation: str, duration: float, success: bool = True) -> Any:
        """记录推理时间"""
        with self.lock:
            record = {
                "timestamp": time.time(),
                "operation": operation,
                "duration": duration,
                "success": success,
            }

            self.metrics["inference_times"].append(record)

            # 保持历史记录大小
            if len(self.metrics["inference_times"]) > self.history_size:
                self.metrics["inference_times"] = self.metrics["inference_times"][
                    -self.history_size :
                ]

            # 检查性能阈值
            self._check_inference_thresholds(operation, duration, success)

    def record_cache_hit_rate(self, cache_name: str, hit_rate: float) -> Any:
        """记录缓存命中率"""
        with self.lock:
            record = {"timestamp": time.time(), "cache_name": cache_name, "hit_rate": hit_rate}

            if cache_name not in self.metrics["cache_hit_rates"]:
                self.metrics["cache_hit_rates"][cache_name]] = []

            self.metrics["cache_hit_rates"][cache_name].append(record)

            # 保持历史记录大小
            if len(self.metrics["cache_hit_rates"][cache_name]) > self.history_size:
                self.metrics["cache_hit_rates"][cache_name] = self.metrics["cache_hit_rates"][
                    cache_name
                ][-self.history_size :]

    def record_system_resources(self) -> Any:
        """记录系统资源使用情况"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()

            record = {
                "timestamp": time.time(),
                "memory_rss_mb": memory_info.rss / (1024 * 1024),
                "memory_vms_mb": memory_info.vms / (1024 * 1024),
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory_percent": process.memory_percent(),
            }

            with self.lock:
                self.metrics["system_resources"].append(record)

                # 保持历史记录大小
                if len(self.metrics["system_resources"]) > self.history_size:
                    self.metrics["system_resources"] = self.metrics["system_resources"][
                        -self.history_size :
                    ]

        except Exception as e:
            print(f"⚠️ 系统资源监控失败: {e}")

    def _check_inference_thresholds(self, operation: str, duration: float, success: bool) -> Any:
        """检查推理性能阈值"""
        if not success:
            print(f"🚨 推理失败: {operation} (耗时: {duration:.3f}s)")
            return

        if duration > self.thresholds["inference_time_critical"]:
            print(
                f"🚨 严重性能警告: {operation} 耗时 {duration:.3f}s (超过 {self.thresholds['inference_time_critical']}s)"
            )
        elif duration > self.thresholds["inference_time_warning"]:
            print(
                f"⚠️ 性能警告: {operation} 耗时 {duration:.3f}s (超过 {self.thresholds['inference_time_warning']}s)"
            )

    def get_real_time_stats(self) -> dict[str, Any]:
        """获取实时统计"""
        with self.lock:
            now = time.time()
            recent_threshold = 300  # 最近5分钟

            # 过滤最近的记录
            recent_inference = [
                r
                for r in self.metrics["inference_times"]
                if now - r["timestamp"] <= recent_threshold
            ]

            recent_system = [
                r
                for r in self.metrics["system_resources"]
                if now - r["timestamp"] <= recent_threshold
            ]

            # 计算推理统计
            inference_stats = {}
            if recent_inference:
                operations = {}
                for record in recent_inference:
                    op = record["operation"]
                    if op not in operations:
                        operations[op]] = []
                    operations[op].append(record["duration"])

                for op, times in operations.items():
                    inference_stats[op]] = {
                        "count": len(times),
                        "avg_time": statistics.mean(times),
                        "min_time": min(times),
                        "max_time": max(times),
                        "success_rate": sum(
                            1 for r in recent_inference if r["operation"] == op and r["success"]
                        )
                        / len(times),
                    }

            # 计算系统资源统计
            system_stats = {}
            if recent_system:
                system_stats = {
                    "avg_memory_mb": statistics.mean(r["memory_rss_mb"] for r in recent_system),
                    "max_memory_mb": max(r["memory_rss_mb"] for r in recent_system),
                    "avg_cpu_percent": statistics.mean(r["cpu_percent"] for r in recent_system),
                    "max_cpu_percent": max(r["cpu_percent"] for r in recent_system),
                }

            # 计算缓存统计
            cache_stats = {}
            for cache_name, records in self.metrics["cache_hit_rates"].items():
                recent_cache = [r for r in records if now - r["timestamp"] <= recent_threshold]
                if recent_cache:
                    cache_stats[cache_name]] = {
                        "current_hit_rate": recent_cache[-1]["hit_rate"],
                        "avg_hit_rate": statistics.mean(r["hit_rate"] for r in recent_cache),
                    }

            return {
                "timestamp": datetime.now().isoformat(),
                "uptime_seconds": now - self.start_time.timestamp(),
                "inference_stats": inference_stats,
                "system_stats": system_stats,
                "cache_stats": cache_stats,
            }

    def generate_performance_report(self) -> dict[str, Any]:
        """生成性能报告"""
        with self.lock:
            now = datetime.now()

            # 基础信息
            report = {
                "generated_at": now.isoformat(),
                "uptime": str(now - self.start_time),
                "total_inferences": len(self.metrics["inference_times"]),
                "total_system_samples": len(self.metrics["system_resources"]),
            }

            # 推理性能分析
            if self.metrics["inference_times"]:
                all_durations = [
                    r["duration"] for r in self.metrics["inference_times"] if r["success"]
                ]
                if all_durations:
                    report["inference_performance"]] = {
                        "avg_time": statistics.mean(all_durations),
                        "median_time": statistics.median(all_durations),
                        "min_time": min(all_durations),
                        "max_time": max(all_durations),
                        "std_dev": statistics.stdev(all_durations) if len(all_durations) > 1 else 0,
                        "total_success_rate": sum(
                            1 for r in self.metrics["inference_times"] if r["success"]
                        )
                        / len(self.metrics["inference_times"]),
                    }

            # 系统资源分析
            if self.metrics["system_resources"]:
                memory_usage = [r["memory_rss_mb"] for r in self.metrics["system_resources"]
                cpu_usage = [r["cpu_percent"] for r in self.metrics["system_resources"]

                report["system_performance"]] = {
                    "modules/modules/memory/modules/memory/modules/memory/memory": {
                        "avg_mb": statistics.mean(memory_usage),
                        "max_mb": max(memory_usage),
                        "current_mb": memory_usage[-1] if memory_usage else 0,
                    },
                    "cpu": {
                        "avg_percent": statistics.mean(cpu_usage),
                        "max_percent": max(cpu_usage),
                        "current_percent": cpu_usage[-1] if cpu_usage else 0,
                    },
                }

            # 缓存性能分析
            cache_performance = {}
            for cache_name, records in self.metrics["cache_hit_rates"].items():
                if records:
                    hit_rates = [r["hit_rate"] for r in records]
                    cache_performance[cache_name]] = {
                        "avg_hit_rate": statistics.mean(hit_rates),
                        "min_hit_rate": min(hit_rates),
                        "max_hit_rate": max(hit_rates),
                        "current_hit_rate": hit_rates[-1],
                    }

            if cache_performance:
                report["cache_performance"] = cache_performance

            # 性能建议
            report["recommendations"] = self._generate_recommendations(report)

            return report

    def _generate_recommendations(self, report: dict[str, Any]) -> list[str]:
        """生成性能优化建议"""
        recommendations = []

        # 推理性能建议
        if "inference_performance" in report:
            avg_time = report["inference_performance"]["avg_time"]
            success_rate = report["inference_performance"]["total_success_rate"]

            if avg_time > self.thresholds["inference_time_warning"]:
                recommendations.append(
                    f"🐌 推理时间过长 ({avg_time:.3f}s),建议启用缓存或优化批处理"
                )

            if success_rate < (1 - self.thresholds["error_rate_maximum"]):
                recommendations.append(
                    f"❌ 错误率过高 ({(1-success_rate)*100:.1f}%),建议检查错误处理机制"
                )

        # 系统资源建议
        if "system_performance" in report:
            current_memory = report["system_performance"][
                "modules/modules/memory/modules/memory/modules/memory/memory"
            ]["current_mb"]
            if current_memory > 2000:  # 2GB
                recommendations.append(
                    f"💾 内存使用较高 ({current_memory:.0f}MB),建议启用内存优化或懒加载"
                )

        # 缓存性能建议
        if "cache_performance" in report:
            for cache_name, stats in report["cache_performance"].items():
                if stats["current_hit_rate"] < self.thresholds["cache_hit_rate_minimum"]:
                    recommendations.append(
                        f"💡 缓存 {cache_name} 命中率较低 ({stats['current_hit_rate']*100:.1f}%),建议增加缓存大小"
                    )

        if not recommendations:
            recommendations.append("✅ 系统性能良好,无特殊建议")

        return recommendations

    def save_report(self, filepath: str) -> None:
        """保存性能报告到文件 - 🔧 安全修复:使用上下文管理器确保文件正确关闭"""
        try:
            # 线程安全修复:生成报告时加锁
            with self.lock:
                report = self.generate_performance_report()

            # 安全修复:使用上下文管理器确保文件正确关闭
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"📄 性能报告已保存: {filepath}")
        except Exception as e:
            print(f"❌ 保存报告失败: {e}")

    def start_monitoring(self, interval: int = 30) -> Any:
        """启动自动监控 - 🔧 线程安全修复:添加停止标志和线程安全控制"""
        # 线程安全修复:添加停止标志
        if hasattr(self, "_monitoring_thread") and self._monitoring_thread.is_alive():
            print("⚠️ 监控已在运行中")
            return

        self._stop_monitoring = False

        def monitor_loop() -> Any:
            while not self._stop_monitoring:
                try:
                    self.record_system_resources()
                    time.sleep(interval)
                except Exception as e:
                    print(f"⚠️ 监控循环出错: {e}")
                    time.sleep(interval)  # 出错后继续监控

        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        self._monitoring_thread = monitor_thread
        print(f"🔍 性能监控已启动 (间隔: {interval}秒)")

    def stop_monitoring(self) -> Any:
        """停止监控 - 🔧 线程安全修复:添加停止方法"""
        self._stop_monitoring = True
        if hasattr(self, "_monitoring_thread"):
            self._monitoring_thread.join(timeout=5)
            print("🛑 性能监控已停止")

    def get_health_score(self) -> dict[str, Any]:
        """获取系统健康评分"""
        with self.lock:
            scores = {}

            # 推理性能评分
            if self.metrics["inference_times"]:
                recent_times = [
                    r["duration"] for r in self.metrics["inference_times"][-100:] if r["success"]
                ]
                if recent_times:
                    avg_time = statistics.mean(recent_times)
                    if avg_time <= 0.1:
                        scores["inference"] = 100  # 优秀
                    elif avg_time <= 0.5:
                        scores["inference"] = 85  # 良好
                    elif avg_time <= 1.0:
                        scores["inference"] = 70  # 一般
                    else:
                        scores["inference"] = 50  # 较差

            # 内存使用评分
            if self.metrics["system_resources"]:
                recent_memory = [
                    r["memory_rss_mb"] for r in self.metrics["system_resources"][-100:]
                ]
                if recent_memory:
                    avg_memory = statistics.mean(recent_memory)
                    if avg_memory <= 500:
                        scores["modules/modules/memory/modules/memory/modules/memory/memory"] = 100
                    elif avg_memory <= 1000:
                        scores["modules/modules/memory/modules/memory/modules/memory/memory"] = 85
                    elif avg_memory <= 2000:
                        scores["modules/modules/memory/modules/memory/modules/memory/memory"] = 70
                    else:
                        scores["modules/modules/memory/modules/memory/modules/memory/memory"] = 50

            # 缓存效率评分
            if self.metrics["cache_hit_rates"]:
                cache_scores = []
                for _cache_name, records in self.metrics["cache_hit_rates"].items():
                    if records:
                        current_rate = records[-1]["hit_rate"]
                        if current_rate >= 0.9:
                            cache_scores.append(100)
                        elif current_rate >= 0.8:
                            cache_scores.append(85)
                        elif current_rate >= 0.7:
                            cache_scores.append(70)
                        else:
                            cache_scores.append(50)

                if cache_scores:
                    scores["cache"] = statistics.mean(cache_scores)

            # 综合评分
            overall_score = statistics.mean(scores.values()) if scores else 0

            return {
                "individual_scores": scores,
                "overall_score": overall_score,
                "grade": self._get_grade(overall_score),
                "timestamp": datetime.now().isoformat(),
            }

    def _get_grade(self, score: float) -> str:
        """根据分数获取等级"""
        if score >= 90:
            return "A+ (优秀)"
        elif score >= 80:
            return "A (良好)"
        elif score >= 70:
            return "B (一般)"
        elif score >= 60:
            return "C (较差)"
        else:
            return "D (需要改进)"


# 全局性能监控器实例
global_performance_monitor = None


def get_performance_monitor() -> PerformanceMonitor:
    """获取全局性能监控器实例"""
    global global_performance_monitor
    if global_performance_monitor is None:
        global_performance_monitor = PerformanceMonitor()
        global_performance_monitor.start_monitoring()
    return global_performance_monitor


if __name__ == "__main__":
    # 测试性能监控器
    monitor = PerformanceMonitor()
    monitor.start_monitoring()

    # 模拟一些推理记录
    for i in range(10):
        monitor.record_inference_time("test_operation", 0.1 + i * 0.01, True)
        time.sleep(0.1)

    # 获取实时统计
    stats = monitor.get_real_time_stats()
    print("📊 实时统计:")
    print(json.dumps(stats, indent=2, ensure_ascii=False))

    # 生成性能报告
    report = monitor.generate_performance_report()
    print("\n📋 性能报告:")
    print(json.dumps(report, indent=2, ensure_ascii=False))

    # 健康评分
    health = monitor.get_health_score()
    print(f"\n💚 系统健康评分: {health['overall_score']:.1f} - {health['grade']}")

