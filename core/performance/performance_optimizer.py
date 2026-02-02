"""
性能优化器 - 统一的性能优化管理
集成响应缓存、模型预加载、上下文压缩等功能
"""

import json
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


from .context_compressor import get_context_manager
from .model_preloader import get_preloader
from .response_cache import get_cache


@dataclass
class PerformanceMetrics:
    """性能指标"""

    response_time: float
    cache_hit: bool
    model_load_time: float
    context_compression_time: float
    token_count: int
    timestamp: float
    operation_type: str


class PerformanceOptimizer:
    """性能优化器"""

    def __init__(self, config_path: str | None = None):
        """
        初始化性能优化器

        Args:
            config_path: 配置文件路径
        """
        self.config_path = (
            Path(config_path)
            if config_path
            else Path(__file__).parent.parent.parent / "config" / "performance.json"
        )

        # 加载配置
        self.config = self._load_config()

        # 初始化各组件
        self.cache = get_cache()
        self.preloader = get_preloader()
        self.context_manager = get_context_manager()
        self.compressor = self.context_manager.compressor

        # 配置组件
        self._configure_components()

        # 性能监控
        self.metrics: list[PerformanceMetrics] = []
        self.performance_stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "average_response_time": 0,
            "fast_responses": 0,  # < 1秒
            "slow_responses": 0,  # > 3秒
            "context_compressions": 0,
            "model_loads": 0,
        }

        # 线程锁
        self.metrics_lock = threading.RLock()

    def _load_config(self) -> dict:
        """加载配置文件"""
        try:
            if self.config_path.exists():
                with open(self.config_path, encoding="utf-8") as f:
                    config = json.load(f)
                    print(f"加载性能优化配置: {self.config_path}")
                    return config
            else:
                # 创建默认配置
                default_config = {
                    "cache": {
                        "enabled": True,
                        "max_memory_items": 1000,
                        "max_ttl_hours": 24,
                        "auto_cleanup": True,
                        "cleanup_interval_hours": 6,
                    },
                    "preload": {
                        "enabled": True,
                        "preload_on_startup": True,
                        "models": ["text_embedding", "chat_gpt"],
                        "strategy": "parallel",
                    },
                    "context": {
                        "enabled": True,
                        "max_history_length": 10,
                        "max_tokens": 4000,
                        "compression_strategy": "smart",
                    },
                    "monitoring": {
                        "enabled": True,
                        "max_metrics_history": 10000,
                        "auto_save_interval": 300,  # 5分钟
                        "performance_alerts": True,
                        "slow_response_threshold": 3.0,  # 3秒
                    },
                }
                self._save_config(default_config)
                return default_config
        except Exception as e:
            print(f"加载性能配置失败: {e}")
            return {}

    def _save_config(self, config: dict) -> None:
        """保存配置文件"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存性能配置失败: {e}")

    def _configure_components(self) -> None:
        """配置各组件"""
        try:
            # 配置缓存
            cache_config = self.config.get("cache", {})
            if cache_config.get("enabled", True):
                print("✅ 响应缓存已启用")
                self.cache.max_memory_items = cache_config.get("max_memory_items", 1000)
                # 其他缓存配置...

            # 配置预加载
            preload_config = self.config.get("preload", {})
            if preload_config.get("enabled", True):
                print("✅ 模型预加载已启用")
                if preload_config.get("preload_on_startup", True):
                    self.preloader.start_preload()

            # 配置上下文压缩
            context_config = self.config.get("context", {})
            if context_config.get("enabled", True):
                print("✅ 上下文压缩已启用")
                self.compressor.max_history_length = context_config.get("max_history_length", 10)
                self.compressor.max_tokens = context_config.get("max_tokens", 4000)
                self.compressor.set_strategy(context_config.get("compression_strategy", "smart"))

            print("🚀 性能优化器配置完成")

        except Exception as e:
            print(f"配置性能优化器失败: {e}")

    def optimize_request(
        self,
        conversation_id: str,
        prompt: str,
        context: dict | None = None,
        model: str = "default",
        operation_type: str = "unknown",
    ) -> dict:
        """
        优化请求处理

        Args:
            conversation_id: 对话ID
            prompt: 用户输入
            context: 上下文信息
            model: 使用的模型
            operation_type: 操作类型

        Returns:
            优化结果
        """
        start_time = time.time()

        # 记录请求指标
        cache_hit = False
        model_load_time = 0
        context_compression_time = 0

        try:
            # 1. 检查缓存
            cached_response = self.cache.get(prompt, context, model)
            if cached_response is not None:
                cache_hit = True
                response_time = time.time() - start_time
                self._record_metrics(
                    prompt,
                    response_time,
                    cache_hit,
                    model_load_time,
                    context_compression_time,
                    0,
                    operation_type,
                )
                return {
                    "response": cached_response,
                    "from_cache": True,
                    "response_time": response_time,
                    "optimization_applied": ["cache"],
                }

            # 2. 检查模型是否已加载
            if not self.preloader.is_model_loaded(model):
                model_load_start = time.time()
                # 这里可以触发模型加载
                model_load_time = time.time() - model_load_start
                self.performance_stats["model_loads"] += 1

            # 3. 压缩上下文
            compressed_context = []
            if self.config.get("context", {}).get("enabled", True):
                compression_start = time.time()

                # 添加用户消息到上下文管理器
                self.context_manager.add_message(conversation_id, "user", prompt)

                # 获取压缩后的上下文
                compressed_context = self.context_manager.get_compressed_context(conversation_id)

                context_compression_time = time.time() - compression_start
                self.performance_stats["context_compressions"] += 1

            # 返回优化结果(实际应用中这里会调用AI模型)
            response_time = time.time() - start_time

            return {
                "compressed_context": compressed_context,
                "model_loaded": self.preloader.is_model_loaded(model),
                "response_time": response_time,
                "optimization_applied": [
                    "context_compression" if context_compression_time > 0 else None,
                    "model_check" if model_load_time > 0 else None,
                ],
                "from_cache": False,
            }

        except Exception as e:
            response_time = time.time() - start_time
            print(f"请求优化失败: {e}")
            return {
                "error": str(e),
                "response_time": response_time,
                "from_cache": False,
                "optimization_applied": [],
            }
        finally:
            # 记录性能指标
            self._record_metrics(
                prompt,
                time.time() - start_time,
                cache_hit,
                model_load_time,
                context_compression_time,
                0,
                operation_type,
            )

    def cache_response(
        self,
        conversation_id: str,
        prompt: str,
        response: Any,
        context: dict | None = None,
        model: str = "default",
    ) -> None:
        """
        缓存响应结果

        Args:
            conversation_id: 对话ID
            prompt: 用户输入
            response: 响应内容
            context: 上下文信息
            model: 使用的模型
        """
        try:
            # 缓存到响应缓存
            self.cache.set(prompt, response, context, model)

            # 添加助手回复到上下文管理器
            if isinstance(response, str):
                self.context_manager.add_message(conversation_id, "assistant", response)

        except Exception as e:
            print(f"缓存响应失败: {e}")

    def _record_metrics(
        self,
        prompt: str,
        response_time: float,
        cache_hit: bool,
        model_load_time: float,
        context_compression_time: float,
        token_count: int,
        operation_type: str,
    ) -> None:
        """记录性能指标"""
        with self.metrics_lock:
            # 创建指标对象
            metric = PerformanceMetrics(
                response_time=response_time,
                cache_hit=cache_hit,
                model_load_time=model_load_time,
                context_compression_time=context_compression_time,
                token_count=token_count,
                timestamp=time.time(),
                operation_type=operation_type,
            )

            # 添加到历史记录
            self.metrics.append(metric)

            # 限制历史记录数量
            max_history = self.config.get("monitoring", {}).get("max_metrics_history", 10000)
            if len(self.metrics) > max_history:
                self.metrics = self.metrics[-max_history:]

            # 更新统计信息
            self.performance_stats["total_requests"] += 1
            if cache_hit:
                self.performance_stats["cache_hits"] += 1

            # 计算平均响应时间
            total_time = sum(m.response_time for m in self.metrics)
            self.performance_stats["average_response_time"] = total_time / len(self.metrics)

            # 分类响应时间
            if response_time < 1.0:
                self.performance_stats["fast_responses"] += 1
            elif response_time > 3.0:
                self.performance_stats["slow_responses"] += 1

    def get_performance_stats(self) -> dict:
        """获取性能统计信息"""
        with self.metrics_lock:
            stats = self.performance_stats.copy()

            # 添加缓存统计
            cache_stats = self.cache.get_stats()
            stats["cache"] = cache_stats

            # 添加预加载统计
            preload_stats = self.preloader.get_load_status()
            stats["preload"] = preload_stats

            # 添加上下文压缩统计
            compression_stats = self.compressor.get_stats()
            stats["context_compression"] = compression_stats

            # 计算缓存命中率
            if stats["total_requests"] > 0:
                stats["cache_hit_rate"] = (stats["cache_hits"] / stats["total_requests"]) * 100
            else:
                stats["cache_hit_rate"] = 0

            # 添加最近响应时间
            if self.metrics:
                recent_metrics = self.metrics[-10:]  # 最近10次请求
                stats["recent_avg_response_time"] = sum(
                    m.response_time for m in recent_metrics
                ) / len(recent_metrics)
                stats["latest_response_time"] = self.metrics[-1].response_time

            return stats

    def get_detailed_metrics(self, limit: int = 100) -> list[dict]:
        """获取详细的性能指标"""
        with self.metrics_lock:
            recent_metrics = self.metrics[-limit:] if limit > 0 else self.metrics
            return [asdict(metric) for metric in recent_metrics]

    def cleanup(self) -> dict:
        """执行清理操作"""
        cleanup_results = {}

        try:
            # 清理过期缓存
            if self.config.get("cache", {}).get("auto_cleanup", True):
                cache_cleaned = self.cache.cleanup_expired()
                cleanup_results["cache_cleaned"] = cache_cleaned

            # 清理旧的性能指标
            max_metrics = self.config.get("monitoring", {}).get("max_metrics_history", 10000)
            with self.metrics_lock:
                if len(self.metrics) > max_metrics:
                    removed = len(self.metrics) - max_metrics
                    self.metrics = self.metrics[-max_metrics:]
                    cleanup_results["metrics_cleaned"] = removed

            cleanup_results["cleanup_time"] = datetime.now().isoformat()
            cleanup_results["status"] = "success"

        except Exception as e:
            cleanup_results["status"] = "error"
            cleanup_results["error"] = str(e)

        return cleanup_results

    def export_metrics(self, file_path: str | None = None) -> str:
        """导出性能指标"""
        if file_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"performance_metrics_{timestamp}.json"

        try:
            export_data = {
                "export_time": datetime.now().isoformat(),
                "performance_stats": self.get_performance_stats(),
                "detailed_metrics": self.get_detailed_metrics(1000),
                "config": self.config,
            }

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            return file_path

        except Exception as e:
            print(f"导出指标失败: {e}")
            return ""

    def reset_stats(self) -> None:
        """重置统计信息"""
        with self.metrics_lock:
            self.metrics.clear()
            self.performance_stats = {
                "total_requests": 0,
                "cache_hits": 0,
                "average_response_time": 0,
                "fast_responses": 0,
                "slow_responses": 0,
                "context_compressions": 0,
                "model_loads": 0,
            }

        self.cache.clear()
        self.compressor.reset_stats()

    def get_health_status(self) -> dict:
        """获取系统健康状态"""
        stats = self.get_performance_stats()
        health_status = {"overall_status": "healthy", "warnings": [], "errors": []}

        # 检查响应时间
        if stats.get("average_response_time", 0) > 2.0:
            health_status["overall_status"] = "degraded"
            health_status["warnings"].append("平均响应时间过高")

        if stats.get("latest_response_time", 0) > 5.0:
            health_status["overall_status"] = "degraded"
            health_status["warnings"].append("最新响应时间过慢")

        # 检查缓存命中率
        if stats.get("cache_hit_rate", 0) < 20:
            health_status["warnings"].append("缓存命中率较低")

        # 检查慢响应比例
        if stats.get("total_requests", 0) > 0:
            slow_ratio = stats.get("slow_responses", 0) / stats["total_requests"]
            if slow_ratio > 0.1:  # 超过10%的请求很慢
                health_status["overall_status"] = "degraded"
                health_status["warnings"].append("慢响应请求比例过高")

        health_status["performance_summary"] = {
            "total_requests": stats.get("total_requests", 0),
            "avg_response_time": f"{stats.get('average_response_time', 0):.2f}s",
            "cache_hit_rate": f"{stats.get('cache_hit_rate', 0):.1f}%",
            "cache_loaded_models": len(stats.get("preload", {}).get("success", [])),
        }

        return health_status


# 全局性能优化器实例
_global_optimizer: PerformanceOptimizer | None = None


def get_optimizer() -> PerformanceOptimizer:
    """获取全局性能优化器实例"""
    global _global_optimizer
    if _global_optimizer is None:
        _global_optimizer = PerformanceOptimizer()
    return _global_optimizer


# 装饰器:自动性能优化
def optimize_request(conversation_id: str = "default", operation_type: str = "api_call") -> Any:
    """自动性能优化装饰器"""

    def decorator(func) -> None:
        def wrapper(*args, **kwargs) -> Any:
            optimizer = get_optimizer()

            # 提取prompt和参数
            prompt = kwargs.get("prompt", "") or (args[0] if args else "")
            context = kwargs.get("context", {})
            model = kwargs.get("model", "default")

            # 执行优化
            optimization_result = optimizer.optimize_request(
                conversation_id, prompt, context, model, operation_type
            )

            # 如果缓存命中,直接返回
            if optimization_result.get("from_cache"):
                return optimization_result["response"]

            # 执行原函数
            result = func(*args, **kwargs)

            # 缓存结果
            optimizer.cache_response(conversation_id, prompt, result, context, model)

            return result

        wrapper._optimized = True
        wrapper._optimizer_decorator = optimize_request
        return wrapper

    return decorator


# 示例使用
if __name__ == "__main__":
    # 创建性能优化器
    optimizer = PerformanceOptimizer()

    # 模拟请求
    conversation_id = "test_conversation"

    print("🔧 测试性能优化器...")

    # 第一次请求(缓存未命中)
    result1 = optimizer.optimize_request(
        conversation_id=conversation_id, prompt="什么是专利申请?", operation_type="question"
    )
    print(f"第一次请求: {result1['response_time']:.3f}s, 缓存: {result1.get('from_cache', False)}")

    # 缓存响应
    optimizer.cache_response(
        conversation_id=conversation_id,
        prompt="什么是专利申请?",
        response="专利申请是向专利局提交申请的法律程序...",
    )

    # 第二次请求(缓存命中)
    result2 = optimizer.optimize_request(
        conversation_id=conversation_id, prompt="什么是专利申请?", operation_type="question"
    )
    print(f"第二次请求: {result2['response_time']:.3f}s, 缓存: {result2.get('from_cache', False)}")

    # 查看性能统计
    stats = optimizer.get_performance_stats()
    print("\\n性能统计:")
    print(f"  总请求数: {stats['total_requests']}")
    print(f"  缓存命中数: {stats['cache_hits']}")
    print(f"  缓存命中率: {stats['cache_hit_rate']:.1f}%")
    print(f"  平均响应时间: {stats['average_response_time']:.3f}s")

    # 查看健康状态
    health = optimizer.get_health_status()
    print(f"\\n健康状态: {health['overall_status']}")
    if health["warnings"]:
        print(f"  警告: {', '.join(health['warnings'])}")
