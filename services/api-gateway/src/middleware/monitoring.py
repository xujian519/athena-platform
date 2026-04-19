"""
性能监控中间件

提供全面的请求性能监控和指标收集。
"""

import threading
import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from datetime import datetime

from fastapi import Response

from .base import Middleware, MiddlewareContext


class MonitoringMiddleware(Middleware):
    """性能监控中间件

    收集以下指标：
    1. 请求计数（按路径、方法、状态码）
    2. 响应时间分布（P50, P95, P99）
    3. 错误率
    4. 慢请求检测
    5. 并发请求数
    6. Prometheus 格式指标导出

    配置选项：
    - slow_threshold: 慢请求阈值（秒），默认 3.0
    - metrics_window_size: 指标窗口大小，默认 1000
    - enable_prometheus: 启用 Prometheus 格式导出，默认 True
    - track_paths: 需要追踪的路径列表，None 表示全部
    - skip_paths: 跳过监控的路径列表
    """

    def __init__(
        self,
        slow_threshold: float = 3.0,
        metrics_window_size: int = 1000,
        enable_prometheus: bool = True,
        track_paths: list[str] | None = None,
        skip_paths: list[str] | None = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self._slow_threshold = slow_threshold
        self._metrics_window_size = metrics_window_size
        self._enable_prometheus = enable_prometheus
        self._track_paths = set(track_paths) if track_paths else None
        self._skip_paths = set(skip_paths or [])

        # 指标存储
        self._request_times: dict[str, deque] = defaultdict(lambda: deque(maxlen=metrics_window_size))
        self._request_counts: dict[tuple[str, str, int], int] = defaultdict(int)  # (path, method, status)
        self._error_counts: dict[tuple[str, str], int] = defaultdict(int)  # (path, method)
        self._slow_requests: list[dict] = []
        self._concurrent_requests = 0
        self._max_concurrent_requests = 0
        self._lock = threading.Lock()

    async def process(
        self,
        ctx: MiddlewareContext,
        call_next: Callable[[MiddlewareContext], Awaitable[Response]]
    ) -> Response:
        """处理请求监控"""

        request = ctx.request
        path = request.url.path
        method = request.method

        # 检查是否跳过监控
        if self._should_skip_monitoring(path):
            return await call_next(ctx)

        # 检查是否需要追踪
        if self._track_paths is not None and path not in self._track_paths:
            return await call_next(ctx)

        # 增加并发计数
        with self._lock:
            self._concurrent_requests += 1
            if self._concurrent_requests > self._max_concurrent_requests:
                self._max_concurrent_requests = self._concurrent_requests

        start_time = time.time()

        try:
            # 执行请求
            response = await call_next(ctx)

            # 计算处理时间
            process_time = time.time() - start_time

            # 记录指标
            self._record_metrics(
                path=path,
                method=method,
                status_code=response.status_code,
                process_time=process_time,
                success=response.status_code < 400,
            )

            # 检查慢请求
            if process_time > self._slow_threshold:
                self._record_slow_request(
                    path=path,
                    method=method,
                    process_time=process_time,
                    status_code=response.status_code,
                )

            # 添加响应头
            response.headers["X-Process-Time"] = f"{process_time:.4f}"

            return response

        finally:
            # 减少并发计数
            with self._lock:
                self._concurrent_requests -= 1

    def _should_skip_monitoring(self, path: str) -> bool:
        """检查是否跳过监控"""
        for skip_path in self._skip_paths:
            if path.startswith(skip_path):
                return True
        return False

    def _record_metrics(
        self,
        path: str,
        method: str,
        status_code: int,
        process_time: float,
        success: bool
    ) -> None:
        """记录请求指标"""
        with self._lock:
            # 记录响应时间
            key = f"{method}:{path}"
            self._request_times[key].append(process_time)

            # 记录请求计数
            count_key = (path, method, status_code)
            self._request_counts[count_key] += 1

            # 记录错误
            if not success:
                error_key = (path, method)
                self._error_counts[error_key] += 1

    def _record_slow_request(
        self,
        path: str,
        method: str,
        process_time: float,
        status_code: int
    ) -> None:
        """记录慢请求"""
        with self._lock:
            self._slow_requests.append({
                "path": path,
                "method": method,
                "process_time": round(process_time, 4),
                "status_code": status_code,
                "timestamp": datetime.now().isoformat(),
            })

            # 限制慢请求记录数量
            if len(self._slow_requests) > 100:
                self._slow_requests = self._slow_requests[-100:]

    def get_metrics(self) -> dict:
        """获取当前指标

        Returns:
            dict: 包含所有监控指标的字典
        """
        with self._lock:
            # 计算响应时间百分位数
            percentiles = {}
            for key, times in self._request_times.items():
                if times:
                    sorted_times = sorted(times)
                    n = len(sorted_times)
                    percentiles[key] = {
                        "count": n,
                        "min": round(sorted_times[0], 4),
                        "max": round(sorted_times[-1], 4),
                        "avg": round(sum(sorted_times) / n, 4),
                        "p50": round(sorted_times[int(n * 0.5)], 4),
                        "p95": round(sorted_times[int(n * 0.95)], 4) if n >= 20 else None,
                        "p99": round(sorted_times[int(n * 0.99)], 4) if n >= 100 else None,
                    }

            # 计算总请求数和错误率
            total_requests = sum(self._request_counts.values())
            total_errors = sum(self._error_counts.values())
            error_rate = total_errors / total_requests if total_requests > 0 else 0

            return {
                "summary": {
                    "total_requests": total_requests,
                    "total_errors": total_errors,
                    "error_rate": round(error_rate, 4),
                    "concurrent_requests": self._concurrent_requests,
                    "max_concurrent_requests": self._max_concurrent_requests,
                    "slow_threshold": self._slow_threshold,
                    "slow_request_count": len(self._slow_requests),
                },
                "response_times": percentiles,
                "request_counts": {
                    f"{method} {path} [{status}]": count
                    for (path, method, status), count in self._request_counts.items()
                },
                "error_counts": {
                    f"{method} {path}": count
                    for (path, method), count in self._error_counts.items()
                },
                "slow_requests": self._slow_requests[-10:],  # 最近 10 个
            }

    def get_prometheus_metrics(self) -> str:
        """获取 Prometheus 格式的指标

        Returns:
            str: Prometheus 格式的指标文本
        """
        if not self._enable_prometheus:
            return ""

        lines = []

        with self._lock:
            # 请求计数指标
            for (path, method, status), count in self._request_counts.items():
                lines.append(
                    f'athena_http_requests_total{{path="{path}",method="{method}",status="{status}"}} {count}'
                )

            # 错误计数指标
            for (path, method), count in self._error_counts.items():
                lines.append(
                    f'athena_http_errors_total{{path="{path}",method="{method}"}} {count}'
                )

            # 响应时间指标
            for key, times in self._request_times.items():
                if times:
                    method, path = key.split(":", 1)
                    sorted_times = sorted(times)
                    n = len(sorted_times)

                    lines.append(
                        f'athena_http_request_duration_seconds{{path="{path}",method="{method}",quantile="0.5"}} {sorted_times[int(n * 0.5)]}'
                    )
                    lines.append(
                        f'athena_http_request_duration_seconds{{path="{path}",method="{method}",quantile="0.95"}} {sorted_times[int(n * 0.95)] if n >= 20 else 0}'
                    )
                    lines.append(
                        f'athena_http_request_duration_seconds{{path="{path}",method="{method}",quantile="0.99"}} {sorted_times[int(n * 0.99)] if n >= 100 else 0}'
                    )

            # 并发请求指标
            lines.append(
                f'athena_concurrent_requests {self._concurrent_requests}'
            )
            lines.append(
                f'athena_concurrent_requests_max {self._max_concurrent_requests}'
            )

            # 慢请求计数
            lines.append(
                f'athena_slow_requests_total {len(self._slow_requests)}'
            )

        return "\n".join(lines)

    def get_slow_requests(self, limit: int = 50) -> list[dict]:
        """获取慢请求列表

        Args:
            limit: 返回的最大数量

        Returns:
            list[dict]: 慢请求列表
        """
        with self._lock:
            return self._slow_requests[-limit:]

    def reset_metrics(self) -> None:
        """重置所有指标"""
        with self._lock:
            self._request_times.clear()
            self._request_counts.clear()
            self._error_counts.clear()
            self._slow_requests.clear()
            self._max_concurrent_requests = 0


class MetricsExporter:
    """指标导出器

    提供多种格式的指标导出功能。
    """

    def __init__(self, middleware: MonitoringMiddleware):
        self._middleware = middleware

    def export_prometheus(self) -> str:
        """导出 Prometheus 格式"""
        return self._middleware.get_prometheus_metrics()

    def export_json(self) -> str:
        """导出 JSON 格式"""
        import json
        return json.dumps(self._middleware.get_metrics(), indent=2, ensure_ascii=False)

    def export_influx(self) -> str:
        """导出 InfluxDB 行协议格式"""
        lines = []
        metrics = self._middleware.get_metrics()

        timestamp = int(datetime.now().timestamp() * 1e9)

        # 请求计数
        for path_method_status, count in metrics["request_counts"].items():
            parts = path_method_status.split()
            if len(parts) >= 3:
                method, path, status = parts[0], parts[1], parts[2].strip("[]")
                lines.append(
                    f"athena_http_requests,method={method},path={path},status={status} value={count} {timestamp}"
                )

        # 响应时间
        for key, stats in metrics["response_times"].items():
            method, path = key.split(":", 1)
            lines.append(
                f"athena_http_request_duration,method={method},path={path},quantile=p50 value={stats['p50']} {timestamp}"
            )
            if stats.get("p95"):
                lines.append(
                    f"athena_http_request_duration,method={method},path={path},quantile=p95 value={stats['p95']} {timestamp}"
                )

        return "\n".join(lines)

    def export_statsd(self) -> str:
        """导出 StatsD 格式"""
        lines = []
        metrics = self._middleware.get_metrics()

        # 请求计数
        for path_method_status, count in metrics["request_counts"].items():
            sanitized = path_method_status.replace(" ", "_").replace("/", ".").lower()
            lines.append(f"athena.http.requests.{sanitized}:{count}|c")

        # 响应时间
        for key, stats in metrics["response_times"].items():
            sanitized = key.replace(":", "_").replace("/", ".").lower()
            lines.append(f"athena.http.response_time.{sanitized}:{stats['avg']}|ms")

        return "\n".join(lines)
