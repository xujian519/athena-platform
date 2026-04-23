#!/usr/bin/env python3
"""
智能告警阈值调整工具
Intelligent Alert Threshold Adjuster

基于历史指标数据自动调整Prometheus告警阈值

作者: Athena Platform Team
版本: v1.0
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class MetricStats:
    """指标统计数据"""
    name: str
    current_value: float
    p50: float
    p95: float
    p99: float
    max: float
    trend: str  # increasing, decreasing, stable


class PrometheusQueryClient:
    """Prometheus查询客户端"""

    def __init__(self, base_url: str = "http://localhost:9090"):
        self.base_url = base_url

    def query(self, promql: str, time_range: str = "1h") -> List[Dict]:
        """执行Prometheus查询"""
        try:
            # 查询当前值
            response = requests.get(
                f"{self.base_url}/api/v1/query",
                params={"query": promql},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if data["status"] == "success" and data["data"]["result"]:
                    return data["data"]["result"]

        except Exception as e:
            print(f"⚠️  查询失败: {e}")

        return []

    def query_range(self, promql: str, start: str, end: str, step: str = "15s") -> Dict:
        """执行Prometheus范围查询"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/query_range",
                params={
                    "query": promql,
                    "start": start,
                    "end": end,
                    "step": step
                },
                timeout=30
            )

            if response.status_code == 200:
                return response.json()

        except Exception as e:
            print(f"⚠️  范围查询失败: {e}")

        return {}

    def get_metric_stats(self, metric_name: str, duration_hours: int = 24) -> MetricStats:
        """获取指标统计数据"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=duration_hours)

        # 获取当前值
        current_results = self.query(metric_name)
        current_value = float(current_results[0]["value"][1]) if current_results else 0

        # 计算百分位数
        p50_query = f'quantile(0.50, {metric_name})'
        p95_query = f'quantile(0.95, {metric_name})'
        p99_query = f'quantile(0.99, {metric_name})'
        max_query = f'max({metric_name})'

        p50_results = self.query(p50_query)
        p95_results = self.query(p95_query)
        p99_results = self.query(p99_query)
        max_results = self.query(max_query)

        p50 = float(p50_results[0]["value"][1]) if p50_results else current_value
        p95 = float(p95_results[0]["value"][1]) if p95_results else current_value
        p99 = float(p99_results[0]["value"][1]) if p99_results else current_value
        max_val = float(max_results[0]["value"][1]) if max_results else current_value

        # 分析趋势
        trend = "stable"
        if p95 > current_value * 1.2:
            trend = "increasing"
        elif p95 < current_value * 0.8:
            trend = "decreasing"

        return MetricStats(
            name=metric_name,
            current_value=current_value,
            p50=p50,
            p95=p95,
            p99=p99,
            max=max_val,
            trend=trend
        )


class AlertThresholdOptimizer:
    """告警阈值优化器"""

    def __init__(self, prometheus_url: str = "http://localhost:9090"):
        self.client = PrometheusQueryClient(prometheus_url)

    def optimize_cognitive_latency_thresholds(self) -> Dict[str, float]:
        """优化认知延迟告警阈值"""
        print("\n📊 分析认知处理延迟...")

        # 获取延迟统计数据
        latency_metric = "rate(cognitive_processing_duration_seconds_bucket[5m])"
        stats = self.client.get_metric_stats(latency_metric, duration_hours=24)

        # 基于P95和P99值设置阈值
        warning_threshold = stats.p95 * 1.5  # Warning: P95的1.5倍
        critical_threshold = stats.p99 * 1.2  # Critical: P99的1.2倍

        # 确保最小阈值
        warning_threshold = max(warning_threshold, 5.0)   # 最小5秒
        critical_threshold = max(critical_threshold, 30.0)  # 最小30秒

        return {
            "high_cognitive_latency": round(warning_threshold, 2),
            "critical_cognitive_latency": round(critical_threshold, 2)
        }

    def optimize_decision_error_rate_thresholds(self) -> Dict[str, float]:
        """优化决策错误率告警阈值"""
        print("\n📊 分析决策错误率...")

        error_rate_metric = """
            rate(decision_errors_total[5m]) /
            rate(decision_requests_total[5m])
        """

        stats = self.client.get_metric_stats(error_rate_metric, duration_hours=24)

        # 基于当前P95设置阈值
        warning_threshold = stats.p95 * 1.3  # Warning: P95的1.3倍
        critical_threshold = stats.p95 * 2.0  # Critical: P95的2倍

        # 限制在合理范围
        warning_threshold = min(max(warning_threshold, 0.02), 0.10)  # 2%-10%
        critical_threshold = min(max(critical_threshold, 0.05), 0.20)  # 5%-20%

        return {
            "high_decision_error_rate": round(warning_threshold, 4),
            "critical_decision_error_rate": round(critical_threshold, 4)
        }

    def optimize_memory_thresholds(self) -> Dict[str, float]:
        """优化内存使用告警阈值"""
        print("\n📊 分析内存使用...")

        memory_metric = "super_reasoning_memory_bytes"
        stats = self.client.get_metric_stats(memory_metric, duration_hours=24)

        # 基于P95值设置阈值
        warning_threshold = stats.p95 * 1.5  # P95的1.5倍
        warning_threshold = min(warning_threshold, 2 * 1024**3)  # 最大2GB

        return {
            "super_reasoning_high_memory": round(warning_threshold, 0)
        }

    def optimize_cache_hit_rate_thresholds(self) -> Dict[str, float]:
        """优化缓存命中率告警阈值"""
        print("\n📊 分析缓存命中率...")

        cache_hit_metric = """
            rate(memory_cache_hits_total[5m]) /
            (rate(memory_cache_hits_total[5m]) + rate(memory_cache_misses_total[5m]))
        """

        stats = self.client.get_metric_stats(cache_hit_metric, duration_hours=24)

        # 基于当前P95设置阈值
        warning_threshold = stats.p95 * 0.85  # Warning: P95的85%

        # 限制在合理范围
        warning_threshold = max(warning_threshold, 0.60)  # 最小60%

        return {
            "memory_cache_low_hit": round(warning_threshold, 2)
        }

    def optimize_all_thresholds(self) -> Dict[str, Dict[str, float]]:
        """优化所有告警阈值"""
        print("🔧 开始优化告警阈值...")
        print("=" * 60)

        thresholds = {}
        thresholds.update(self.optimize_cognitive_latency_thresholds())
        thresholds.update(self.optimize_decision_error_rate_thresholds())
        thresholds.update(self.optimize_memory_thresholds())
        thresholds.update(self.optimize_cache_hit_rate_thresholds())

        return thresholds

    def generate_prometheus_rules(self, thresholds: Dict[str, float]) -> str:
        """生成优化后的Prometheus告警规则"""
        rules = f"""# 优化的认知与决策模块告警规则
# 基于历史数据自动生成 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

groups:
  - name: cognitive_module_alerts_optimized
    interval: 30s
    rules:
      # 认知处理延迟告警（已优化）
      - alert: HighCognitiveLatency
        expr: histogram_quantile(0.95, rate(cognitive_processing_duration_seconds_bucket[5m])) > {thresholds.get('high_cognitive_latency', 5)}
        for: 5m
        labels:
          severity: warning
          service: cognitive
        annotations:
          summary: "认知处理延迟过高"
          description: "认知模块P95延迟超过{thresholds.get('high_cognitive_latency', 5)}秒，当前值: {{{{ $value }}}}秒"

      - alert: CriticalCognitiveLatency
        expr: histogram_quantile(0.95, rate(cognitive_processing_duration_seconds_bucket[5m])) > {thresholds.get('critical_cognitive_latency', 30)}
        for: 2m
        labels:
          severity: critical
          service: cognitive
        annotations:
          summary: "认知处理严重延迟"
          description: "认知模块P95延迟超过{thresholds.get('critical_cognitive_latency', 30)}秒，当前值: {{{{ $value }}}}秒"

  - name: decision_module_alerts_optimized
    interval: 30s
    rules:
      # 决策错误率告警（已优化）
      - alert: HighDecisionErrorRate
        expr: |
          (
            rate(decision_errors_total[5m]) /
            rate(decision_requests_total[5m])
          ) > {thresholds.get('high_decision_error_rate', 0.05)}
        for: 5m
        labels:
          severity: warning
          service: decision
        annotations:
          summary: "决策错误率过高"
          description: "决策错误率超过{thresholds.get('high_decision_error_rate', 0.05)*100:.1f}%，当前值: {{{{ $value | humanizePercentage }}}"

      - alert: CriticalDecisionErrorRate
        expr: |
          (
            rate(decision_errors_total[5m]) /
            rate(decision_requests_total[5m])
          ) > {thresholds.get('critical_decision_error_rate', 0.15)}
        for: 2m
        labels:
          severity: critical
          service: decision
        annotations:
          summary: "决策错误率严重"
          description: "决策错误率超过{thresholds.get('critical_decision_error_rate', 0.15)*100:.1f}%，当前值: {{{{ $value | humanizePercentage }}}"

  - name: super_reasoning_alerts_optimized
    interval: 30s
    rules:
      # 内存使用告警（已优化）
      - alert: SuperReasoningHighMemory
        expr: super_reasoning_memory_bytes > {thresholds.get('super_reasoning_high_memory', 1073741824)}
        for: 10m
        labels:
          severity: warning
          service: super_reasoning
        annotations:
          summary: "超级推理引擎内存使用过高"
          description: "超级推理引擎内存使用超过{thresholds.get('super_reasoning_high_memory', 1073741824)/1024/1024/1024:.1f}GB，当前值: {{{{ $value | humanize }}}}B"

  - name: memory_system_alerts_optimized
    interval: 30s
    rules:
      # 缓存命中率告警（已优化）
      - alert: MemoryCacheLowHit
        expr: |
          (
            rate(memory_cache_hits_total[5m]) /
            (rate(memory_cache_hits_total[5m]) + rate(memory_cache_misses_total[5m]))
          ) < {thresholds.get('memory_cache_low_hit', 0.7)}
        for: 15m
        labels:
          severity: warning
          service: memory
        annotations:
          summary: "记忆缓存命中率过低"
          description: "记忆缓存命中率低于{thresholds.get('memory_cache_low_hit', 0.7)*100:.0f}%，当前值: {{{{ $value | humanizePercentage }}}"
"""
        return rules

    def save_optimized_rules(self, rules: str, output_path: str):
        """保存优化后的规则"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(rules)
        print(f"\n✅ 优化后的告警规则已保存到: {output_path}")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="智能告警阈值调整工具")
    parser.add_argument(
        '--prometheus-url',
        default='http://localhost:9090',
        help='Prometheus服务URL'
    )
    parser.add_argument(
        '--output',
        default='config/docker/prometheus/cognitive_decision_alerts_optimized.yml',
        help='输出文件路径'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='仅分析不保存'
    )

    args = parser.parse_args()

    # 创建优化器
    optimizer = AlertThresholdOptimizer(args.prometheus_url)

    try:
        # 优化所有阈值
        thresholds = optimizer.optimize_all_thresholds()

        print("\n" + "=" * 60)
        print("📊 优化后的告警阈值")
        print("=" * 60)

        for name, value in thresholds.items():
            print(f"  {name}: {value}")

        if not args.dry_run:
            # 生成并保存规则
            rules = optimizer.generate_prometheus_rules(thresholds)
            optimizer.save_optimized_rules(rules, args.output)

            print("\n💡 使用方法:")
            print("   1. 备份当前规则: cp config/docker/prometheus/cognitive_decision_alerts.yml config/docker/prometheus/cognitive_decision_alerts.yml.backup")
            print("   2. 应用新规则: cp config/docker/prometheus/cognitive_decision_alerts_optimized.yml config/docker/prometheus/cognitive_decision_alerts.yml")
            print("   3. 重启Prometheus: docker-compose restart prometheus")
        else:
            print("\n⚠️  Dry-run模式，未保存规则")

    except Exception as e:
        print(f"\n❌ 优化失败: {e}")
        print("\n💡 请确保:")
        print("   1. Prometheus正在运行 (http://localhost:9090)")
        print("   2. 指标导出器正在运行 (http://localhost:9100)")
        print("   3. 有足够的指标数据 (至少1小时)")


if __name__ == '__main__':
    main()
