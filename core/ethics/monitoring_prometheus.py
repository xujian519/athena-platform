"""
Prometheus监控集成
Prometheus Monitoring Integration for Ethics Framework

提供生产级监控指标导出
"""

import threading
import time
from contextlib import contextmanager
from typing import Any, Dict, Optional

from prometheus_client import (
    REGISTRY,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    start_http_server,
)

# Prometheus指标定义
ETHICS_EVALUATION_TOTAL = Counter(
    "ethics_evaluation_total", "Total number of ethics evaluations", ["agent_id", "status"]
)

ETHICS_EVALUATION_DURATION = Histogram(
    "ethics_evaluation_duration_seconds",
    "Ethics evaluation duration in seconds",
    ["agent_id"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

ETHICS_VIOLATION_TOTAL = Counter(
    "ethics_violation_total",
    "Total number of ethics violations",
    ["agent_id", "principle_id", "severity"],
)

ETHICS_COMPLIANCE_SCORE = Gauge(
    "ethics_compliance_score", "Current compliance score (0-1)", ["agent_id"]
)

ETHICS_ACTIVE_AGENTS = Gauge("ethics_active_agents", "Number of active agents being monitored")

ETHICS_PRINCIPLE_EVALUATION = Counter(
    "ethics_principle_evaluation_total",
    "Total principle evaluations",
    ["principle_id", "compliant"],
)


class PrometheusMonitor:
    """Prometheus监控器

    提供Prometheus指标导出和监控功能
    """

    def __init__(self, port: int = 9091, enable_endpoint: bool = True):
        """初始化Prometheus监控器

        Args:
            port: Prometheus metrics端点端口
            enable_endpoint: 是否启动HTTP端点
        """
        self.port = port
        self.enable_endpoint = enable_endpoint
        self._started = False
        self._lock = threading.Lock()

        # 跟踪活跃的智能体
        self._active_agents: dict[str, float] = {}

    def start(self) -> None:
        """启动监控服务"""
        if self._started:
            return

        with self._lock:
            if self._started:
                return

            if self.enable_endpoint:
                try:
                    start_http_server(self.port)
                    self._started = True
                    print(f"✅ Prometheus监控端点已启动: http://localhost:{self.port}/metrics")
                except OSError as e:
                    print(f"⚠️  无法启动Prometheus端点: {e}")
                    print(f"   端口{self.port}可能已被占用,请尝试其他端口")

    def record_evaluation(self, agent_id: str, status: str, duration: float, score: float | None = None):
        """记录评估指标"""
        ETHICS_EVALUATION_TOTAL.labels(agent_id=agent_id, status=status).inc()
        ETHICS_EVALUATION_DURATION.labels(agent_id=agent_id).observe(duration)

        if score is not None:
            ETHICS_COMPLIANCE_SCORE.labels(agent_id=agent_id).set(score)

    def record_violation(self, agent_id: str, principle_id: str, severity: str):
        """记录违规指标"""
        ETHICS_VIOLATION_TOTAL.labels(
            agent_id=agent_id, principle_id=principle_id, severity=severity
        ).inc()

    def record_principle_evaluation(self, principle_id: str, compliant: bool):
        """记录原则评估指标"""
        ETHICS_PRINCIPLE_EVALUATION.labels(
            principle_id=principle_id, compliant=str(compliant)
        ).inc()

    def track_agent(self, agent_id: str) -> Any:
        """开始跟踪智能体"""
        self._active_agents[agent_id] = time.time()
        ETHICS_ACTIVE_AGENTS.set(len(self._active_agents))

    def untrack_agent(self, agent_id: str) -> Any:
        """停止跟踪智能体"""
        if agent_id in self._active_agents:
            del self._active_agents[agent_id]
            ETHICS_ACTIVE_AGENTS.set(len(self._active_agents))

    def update_compliance_score(self, agent_id: str, score: float) -> None:
        """更新合规评分"""
        ETHICS_COMPLIANCE_SCORE.labels(agent_id=agent_id).set(score)

    @contextmanager
    def track_evaluation(self, agent_id: str) -> Any:
        """上下文管理器:跟踪评估过程"""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            ETHICS_EVALUATION_DURATION.labels(agent_id=agent_id).observe(duration)

    def get_metrics_summary(self) -> dict[str, Any]:
        """获取指标摘要"""
        return {
            "endpoint_port": self.port,
            "endpoint_enabled": self.enable_endpoint,
            "started": self._started,
            "active_agents": list(self._active_agents.keys()),
            "metrics_available": [
                "ethics_evaluation_total",
                "ethics_evaluation_duration_seconds",
                "ethics_violation_total",
                "ethics_compliance_score",
                "ethics_active_agents",
                "ethics_principle_evaluation_total",
            ],
        }


class EthicsEvaluatorWithPrometheus:
    """集成Prometheus监控的伦理评估器"""

    def __init__(self, evaluator, prometheus_monitor: PrometheusMonitor | None = None):
        """初始化

        Args:
            evaluator: 伦理评估器实例
            prometheus_monitor: Prometheus监控器实例
        """
        self.evaluator = evaluator
        self.prometheus_monitor = prometheus_monitor or PrometheusMonitor()

    def evaluate_action(self, agent_id: str, action: str, context=None) -> None:
        """评估行动(带Prometheus监控)"""
        import time


        start_time = time.time()

        try:
            result = self.evaluator.evaluate_action(agent_id, action, context)
            duration = time.time() - start_time

            # 记录指标
            status = result.status.value if hasattr(result.status, "value") else str(result.status)
            self.prometheus_monitor.record_evaluation(
                agent_id=agent_id, status=status, duration=duration, score=result.overall_score
            )

            # 记录违规
            if hasattr(result, "violations"):
                for violation in result.violations:
                    severity = getattr(violation, "severity", "unknown")
                    self.prometheus_monitor.record_violation(
                        agent_id=agent_id,
                        principle_id=violation.principle_id,
                        severity=str(severity),
                    )

            # 记录原则评估
            if hasattr(result, "principle_evaluations"):
                for pe in result.principle_evaluations:
                    self.prometheus_monitor.record_principle_evaluation(
                        principle_id=pe.principle_id, compliant=pe.compliant
                    )

            return result

        except Exception as e:
            duration = time.time() - start_time
            self.prometheus_monitor.record_evaluation(
                agent_id=agent_id, status="error", duration=duration
            )
            raise e


# 全局Prometheus监控器实例
_global_prometheus_monitor: PrometheusMonitor | None = None


def get_prometheus_monitor() -> PrometheusMonitor:
    """获取全局Prometheus监控器"""
    global _global_prometheus_monitor
    if _global_prometheus_monitor is None:
        _global_prometheus_monitor = PrometheusMonitor()
    return _global_prometheus_monitor


def setup_prometheus_monitoring(port: int = 9091) -> PrometheusMonitor:
    """设置Prometheus监控

    Args:
        port: Prometheus metrics端点端口

    Returns:
        Prometheus监控器实例
    """
    monitor = PrometheusMonitor(port=port)
    monitor.start()
    return monitor


# Prometheus配置示例
PROMETHEUS_CONFIG_EXAMPLE = """
# Prometheus配置示例

global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'athena-ethics-framework'
    static_configs:
      - targets: ['localhost:9091']
    scrape_interval: 5s
"""

# Grafana Dashboard配置示例
GRAFANA_DASHBOARD_CONFIG = """
{
  "dashboard": {
    "title": "Athena伦理框架监控",
    "panels": [
      {
        "title": "评估总数",
        "targets": [
          {
            "expr": "sum(rate(ethics_evaluation_total[5m])) by (status)"
          }
        ]
      },
      {
        "title": "评估延迟",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(ethics_evaluation_duration_seconds_bucket[5m]))"
          }
        ]
      },
      {
        "title": "合规评分",
        "targets": [
          {
            "expr": "ethics_compliance_score"
          }
        ]
      },
      {
        "title": "违规趋势",
        "targets": [
          {
            "expr": "sum(rate(ethics_violation_total[5m])) by (severity)"
          }
        ]
      }
    ]
  }
}
"""
