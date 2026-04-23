#!/usr/bin/env python3

"""
小诺性能监控集成
Xiaonuo Performance Monitoring Integration

将性能瓶颈分析器集成到统一NLP接口中

功能:
1. 实时性能监控集成
2. 自动瓶颈检测和报告
3. 性能数据收集和分析
4. 优化建议生成

作者: 小诺AI团队
日期: 2025-12-18
"""

import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any, Optional

import psutil

from core.logging_config import setup_logging

# 添加模块路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from xiaonuo_performance_bottleneck_analyzer import (
    PerformanceBottleneckAnalyzer,
    PerformanceMetrics,
)
from xiaonuo_unified_interface import NLPRequest, NLPResponse

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


class PerformanceMonitoringIntegration:
    """性能监控集成器"""

    def __init__(self, enable_monitoring: bool = True):
        self.enable_monitoring = enable_monitoring

        if self.enable_monitoring:
            # 创建性能分析器
            self.bottleneck_analyzer = PerformanceBottleneckAnalyzer()

            # 监控配置
            self.monitoring_enabled = True
            self.metrics_collection_enabled = True
            self.auto_optimization_enabled = False  # 默认关闭自动优化

            # 性能统计
            self.request_stats = {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "total_processing_time": 0.0,
                "operation_stats": {},
            }

            # 系统资源监控
            self.system_monitor = SystemResourceMonitor()

            # 监控线程
            self.monitoring_executor = ThreadPoolExecutor(
                max_workers=2, thread_name_prefix="perf_monitor"
            )

            logger.info("🚀 性能监控集成初始化完成")
        else:
            self.bottleneck_analyzer = None
            logger.info("⚠️ 性能监控已禁用")

    def record_request_metrics(self, request: NLPRequest, response: NLPResponse) -> Any:
        """记录请求性能指标"""
        if not self.enable_monitoring or not self.metrics_collection_enabled:
            return

        try:
            # 收集系统资源使用情况
            cpu_usage = psutil.cpu_percent(interval=None)
            psutil.virtual_memory()
            process = psutil.Process()
            process_memory = process.memory_info().rss / 1024 / 1024  # MB

            # 创建性能指标
            metrics = PerformanceMetrics(
                timestamp=datetime.now(),
                request_id=response.request_id,
                operation=f"nlp_processing_{request.mode.value}",
                total_time_ms=response.processing_time * 1000,
                preprocessing_time_ms=response.module_performance.get("intent_classification", 0)
                * 1000,
                model_inference_time_ms=response.module_performance.get("semantic_similarity", 0)
                * 1000,
                postprocessing_time_ms=response.module_performance.get("tool_selection", 0) * 1000,
                cpu_usage_percent=cpu_usage,
                memory_usage_mb=process_memory,
                disk_io_mb=0.0,  # 简化处理
                network_io_mb=0.0,  # 简化处理
                input_text_length=len(request.text),
                output_token_count=len(str(response.selected_tools)),
                cache_hit=response.metadata.get("from_cache", False),
                batch_size=1,
                error_occurred=len(response.errors) > 0,
                error_type="processing_error" if response.errors else "",
                error_message="; ".join(response.errors) if response.errors else "",
            )

            # 记录到分析器
            self.bottleneck_analyzer.record_metrics(metrics)

            # 更新统计信息
            self._update_request_stats(request, response)

        except Exception as e:
            logger.error(f"❌ 记录性能指标失败: {e}")

    def _update_request_stats(self, request: NLPRequest, response: NLPResponse) -> Any:
        """更新请求统计"""
        self.request_stats["total_requests"] += 1
        self.request_stats["total_processing_time"] += response.processing_time

        if len(response.errors) > 0:
            self.request_stats["failed_requests"] += 1
        else:
            self.request_stats["successful_requests"] += 1

        # 按操作类型统计
        operation = f"nlp_processing_{request.mode.value}"
        if operation not in self.request_stats["operation_stats"]:
            self.request_stats["operation_stats"][operation]] = {
                "count": 0,
                "total_time": 0.0,
                "errors": 0,
            }

        op_stats = self.request_stats["operation_stats"][operation]
        op_stats["count"] += 1
        op_stats["total_time"] += response.processing_time
        if len(response.errors) > 0:
            op_stats["errors"] += 1

    def get_performance_report(self) -> dict[str, Any]:
        """获取性能报告"""
        if not self.enable_monitoring:
            return {"monitoring_enabled": False}

        try:
            # 获取瓶颈分析结果
            bottleneck_report = self.bottleneck_analyzer.get_bottleneck_report()

            # 获取系统资源信息
            system_info = self.system_monitor.get_current_stats()

            # 计算统计指标
            total_requests = self.request_stats["total_requests"]
            avg_processing_time = (
                self.request_stats["total_processing_time"] / total_requests
                if total_requests > 0
                else 0
            )
            success_rate = (
                self.request_stats["successful_requests"] / total_requests * 100
                if total_requests > 0
                else 0
            )

            # 按操作分析性能
            operation_performance = {}
            for op_name, op_stats in self.request_stats["operation_stats"].items():
                operation_performance[op_name]] = {
                    "count": op_stats["count"],
                    "avg_time": op_stats["total_time"] / op_stats["count"],
                    "success_rate": (
                        (op_stats["count"] - op_stats["errors"]) / op_stats["count"] * 100
                    ),
                }

            return {
                "monitoring_enabled": True,
                "timestamp": datetime.now().isoformat(),
                "request_statistics": {
                    "total_requests": total_requests,
                    "successful_requests": self.request_stats["successful_requests"],
                    "failed_requests": self.request_stats["failed_requests"],
                    "success_rate_percent": success_rate,
                    "avg_processing_time_seconds": avg_processing_time,
                },
                "bottleneck_analysis": bottleneck_report,
                "system_resources": system_info,
                "operation_performance": operation_performance,
                "health_score": bottleneck_report.get("active_bottlenecks", 0) > 0,
            }

        except Exception as e:
            logger.error(f"❌ 生成性能报告失败: {e}")
            return {
                "monitoring_enabled": True,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def run_performance_analysis(self) -> dict[str, Any]:
        """运行性能分析"""
        if not self.enable_monitoring:
            return {"monitoring_enabled": False}

        try:
            logger.info("🔍 开始运行性能分析...")
            analysis_results = self.bottleneck_analyzer.analyze_performance()

            # 添加额外的监控信息
            analysis_results["monitoring_integration"]] = {
                "requests_processed": self.request_stats["total_requests"],
                "system_health": self._assess_system_health(),
                "recommendations_count": len(
                    analysis_results.get("optimization_recommendations", [])
                ),
            }

            logger.info(f"✅ 性能分析完成: 健康分数{analysis_results.get('health_score', 0):.1f}")

            return analysis_results

        except Exception as e:
            logger.error(f"❌ 运行性能分析失败: {e}")
            return {
                "monitoring_enabled": True,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def _assess_system_health(self) -> str:
        """评估系统健康状态"""
        try:
            cpu_usage = psutil.cpu_percent(interval=None)
            memory_usage = psutil.virtual_memory().percent

            if cpu_usage > 90 or memory_usage > 90:
                return "critical"
            elif cpu_usage > 80 or memory_usage > 80:
                return "warning"
            else:
                return "healthy"

        except Exception:
            return "unknown"

    def get_optimization_recommendations(self) -> list[dict[str, Any]]:
        """获取优化建议"""
        if not self.enable_monitoring:
            return []

        try:
            # 运行性能分析
            analysis_results = self.run_performance_analysis()
            return analysis_results.get("optimization_recommendations", [])

        except Exception as e:
            logger.error(f"❌ 获取优化建议失败: {e}")
            return []

    def auto_optimize(self) -> dict[str, Any]:
        """自动优化(实验性功能)"""
        if not self.enable_monitoring or not self.auto_optimization_enabled:
            return {"auto_optimization_enabled": False}

        try:
            logger.info("🔧 开始自动优化...")
            recommendations = self.get_optimization_recommendations()

            applied_optimizations = []
            for rec in recommendations[:3]:  # 只应用前3个建议
                if rec.get("impact") in ["high", "critical"]:
                    optimization_result = self._apply_optimization(rec)
                    if optimization_result["success"]:
                        applied_optimizations.append(
                            {"recommendation": rec["suggestion"], "result": optimization_result}
                        )

            return {
                "auto_optimization_enabled": True,
                "recommendations_analyzed": len(recommendations),
                "optimizations_applied": len(applied_optimizations),
                "applied_optimizations": applied_optimizations,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"❌ 自动优化失败: {e}")
            return {
                "auto_optimization_enabled": True,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def _apply_optimization(self, recommendation: dict[str, Any]) -> dict[str, Any]:
        """应用单个优化建议(简化版本)"""
        try:
            # 这里是简化版本的优化逻辑
            # 实际应用中需要根据具体建议实现对应的优化逻辑

            category = recommendation.get("category", "")
            operation = recommendation.get("operation", "")

            if category == "performance_degradation":
                # 示例:调整处理参数
                return {
                    "success": True,
                    "action": f"调整{operation}的处理参数",
                    "impact": "moderate",
                }
            elif category == "cache_efficiency":
                # 示例:优化缓存配置
                return {"success": True, "action": f"优化{operation}的缓存配置", "impact": "high"}
            else:
                return {"success": False, "reason": f"暂不支持自动应用 {category} 类型的优化"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def save_monitoring_data(self, filepath: Optional[str] = None) -> bool:
        """保存监控数据"""
        if not self.enable_monitoring:
            return False

        try:
            if filepath is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filepath = f"data/performance_monitoring_{timestamp}.json"

            # 准备数据
            data = {
                "timestamp": datetime.now().isoformat(),
                "monitoring_integration_stats": self.request_stats,
                "performance_report": self.get_performance_report(),
                "bottleneck_analysis": self.bottleneck_analyzer.get_bottleneck_report(),
            }

            # 保存到文件
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)

            logger.info(f"💾 监控数据已保存: {filepath}")
            return True

        except Exception as e:
            logger.error(f"❌ 保存监控数据失败: {e}")
            return False

    def cleanup(self) -> Any:
        """清理资源"""
        if not self.enable_monitoring:
            return

        logger.info("🧹 正在清理性能监控集成资源...")

        try:
            # 关闭线程池
            self.monitoring_executor.shutdown(wait=True)

            # 清理分析器
            if self.bottleneck_analyzer:
                self.bottleneck_analyzer.cleanup()

            # 清理系统监控
            if self.system_monitor:
                self.system_monitor.cleanup()

            # 重置统计
            self.request_stats.clear()

            logger.info("✅ 性能监控集成资源清理完成")

        except Exception as e:
            logger.error(f"❌ 清理资源失败: {e}")


class SystemResourceMonitor:
    """系统资源监控器"""

    def __init__(self):
        self.monitoring_enabled = True
        self.start_time = datetime.now()

    def get_current_stats(self) -> dict[str, Any]:
        """获取当前系统统计"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)

            # 内存使用情况
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / 1024 / 1024
            memory_total_mb = memory.total / 1024 / 1024

            # 磁盘使用情况
            disk = psutil.disk_usage("/")
            disk_percent = disk.percent
            disk_used_gb = disk.used / 1024 / 1024 / 1024
            disk_total_gb = disk.total / 1024 / 1024 / 1024

            # 网络IO(简化)
            network = psutil.net_io_counters()
            network_sent_mb = network.bytes_sent / 1024 / 1024
            network_recv_mb = network.bytes_recv / 1024 / 1024

            # 进程信息
            process = psutil.Process()
            process_memory_mb = process.memory_info().rss / 1024 / 1024
            process_cpu_percent = process.cpu_percent()

            return {
                "timestamp": datetime.now().isoformat(),
                "cpu": {"usage_percent": cpu_percent, "core_count": psutil.cpu_count()},
                "modules/modules/memory/modules/memory/modules/memory/memory": {
                    "usage_percent": memory_percent,
                    "used_mb": memory_used_mb,
                    "total_mb": memory_total_mb,
                    "available_mb": memory.available / 1024 / 1024,
                },
                "disk": {
                    "usage_percent": disk_percent,
                    "used_gb": disk_used_gb,
                    "total_gb": disk_total_gb,
                    "free_gb": disk.free / 1024 / 1024 / 1024,
                },
                "network": {"sent_mb": network_sent_mb, "recv_mb": network_recv_mb},
                "process": {
                    "pid": process.pid,
                    "memory_mb": process_memory_mb,
                    "cpu_percent": process_cpu_percent,
                    "num_threads": process.num_threads(),
                    "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
                },
            }

        except Exception as e:
            logger.error(f"❌ 获取系统统计失败: {e}")
            return {"timestamp": datetime.now().isoformat(), "error": str(e)}

    def cleanup(self) -> Any:
        """清理资源"""
        self.monitoring_enabled = False


# 性能监控装饰器
def monitor_performance(monitoring_integration: PerformanceMonitoringIntegration) -> Any:
    """性能监控装饰器"""

    def decorator(func) -> None:
        def wrapper(*args, **kwargs) -> Any:
            if not monitoring_integration.enable_monitoring:
                return func(*args, **kwargs)

            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                success = True
            except Exception as e:
                success = False
                str(e)
                raise
            finally:
                # 记录性能数据(这里简化处理)
                processing_time = time.time() - start_time
                logger.debug(f"🔍 监控 {func.__name__}: {processing_time:.3f}s, 成功: {success}")

            return result

        return wrapper

    return decorator


# 使用示例
def create_performance_integration(
    enable_monitoring: bool = True,
) -> PerformanceMonitoringIntegration:
    """创建性能监控集成实例"""
    return PerformanceMonitoringIntegration(enable_monitoring=enable_monitoring)


# 测试代码
if __name__ == "__main__":
    print("🧪 开始测试性能监控集成...")

    # 创建监控集成
    monitoring = create_performance_integration(enable_monitoring=True)

    # 模拟一些请求
    print("\n📝 模拟NLP请求处理...")

    for i in range(10):
        # 模拟请求
        request = NLPRequest(text=f"测试请求 {i}", user_id="test_user", session_id="test_session")

        # 模拟响应
        response = NLPResponse(
            request_id=f"req_{i}",
            intent="test",
            confidence=0.9,
            selected_tools=["test_tool"],
            processing_time=0.1 + (i % 3) * 0.05,  # 变化的处理时间
            module_performance={
                "intent_classification": 0.02,
                "semantic_similarity": 0.03,
                "tool_selection": 0.01,
            },
        )

        # 记录性能指标
        monitoring.record_request_metrics(request, response)

        if i % 3 == 0:
            print(f"   处理请求 {i}: {response.processing_time:.3f}s")

    # 运行性能分析
    print("\n🔍 运行性能分析...")
    analysis_results = monitoring.run_performance_analysis()

    print("\n📊 分析结果:")
    print(f"   总请求数: {analysis_results.get('total_metrics_analyzed', 0)}")
    print(f"   发现瓶颈: {len(analysis_results.get('bottlenecks_found', []))}")
    print(f"   健康分数: {analysis_results.get('health_score', 0):.1f}")

    # 获取优化建议
    print("\n💡 获取优化建议...")
    recommendations = monitoring.get_optimization_recommendations()
    if recommendations:
        print(f"   建议数量: {len(recommendations)}")
        for i, rec in enumerate(recommendations[:3]):
            print(f"   {i+1}. {rec.get('suggestion', 'N/A')}")

    # 获取性能报告
    print("\n📈 生成性能报告...")
    report = monitoring.get_performance_report()
    print(f"   监控状态: {'启用' if report.get('monitoring_enabled') else '禁用'}")
    print(f"   请求总数: {report.get('request_statistics', {}).get('total_requests', 0)}")
    print(f"   成功率: {report.get('request_statistics', {}).get('success_rate_percent', 0):.1f}%")

    # 保存数据
    print("\n💾 保存监控数据...")
    monitoring.save_monitoring_data()

    # 清理资源
    monitoring.cleanup()
    print("\n✅ 性能监控集成测试完成!")

