#!/usr/bin/env python3
from __future__ import annotations
"""
性能监控仪表板
Performance Monitoring Dashboard

实时监控和展示性能优化指标

作者: Athena AI Team
创建时间: 2026-01-11
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class PerformanceDashboard:
    """性能监控仪表板"""

    def __init__(self):
        self.metrics_history = []
        self.max_history = 1000  # 保留最近1000条记录
        self.start_time = datetime.now()

    async def collect_metrics(self) -> dict[str, Any]:
        """收集当前性能指标"""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "optimizations": {},
        }

        try:
            # 收集并发限制器指标
            from core.performance.concurrency_control import (
                get_limiter,
                get_limiters_status,
                get_rate_limiter,
            )

            # API限流器
            api_limiter = get_limiter("api_requests", max_concurrent=100)
            metrics["optimizations"]["api_limiter"] = api_limiter.get_stats()

            # 数据库限流器
            db_limiter = get_limiter("db_queries", max_concurrent=50)
            metrics["optimizations"]["db_limiter"] = db_limiter.get_stats()

            # 速率限制器
            try:
                rate_limiter = get_rate_limiter("external_api", rate=100, per=1.0)
                metrics["optimizations"]["rate_limiter"] = rate_limiter.get_stats()
            except Exception as e:
                logger.debug(f"空except块已触发: {e}")
                pass

            # 所有限制器状态
            metrics["limiters_status"] = get_limiters_status()

        except Exception as e:
            logger.error(f"收集并发控制指标失败: {e}")
            metrics["optimizations"]["concurrency_control"] = {"error": str(e)}

        try:
            # 收集批处理器指标
            from core.performance.batch_processor import _batch_processors

            metrics["batch_processors"] = {}
            for name, processor in _batch_processors.items():
                stats = processor.get_stats()
                metrics["batch_processors"][name] = {
                    "total_requests": stats.get("total_requests", 0),
                    "total_batches": stats.get("total_batches", 0),
                    "avg_batch_size": stats.get("avg_batch_size", 0),
                    "avg_latency_ms": stats.get("avg_latency_ms", 0),
                    "throughput_per_sec": stats.get("throughput_per_sec", 0),
                    "running": stats.get("running", False),
                }

        except Exception as e:
            logger.error(f"收集批处理器指标失败: {e}")
            metrics["batch_processors"] = {"error": str(e)}

        try:
            # 收集数据库连接池指标
            from core.database.connection_pool import get_connection_pool

            pool = await get_connection_pool()
            metrics["database_pool"] = pool.get_pool_status()

        except Exception as e:
            logger.error(f"收集数据库连接池指标失败: {e}")
            metrics["database_pool"] = {"status": "error", "message": str(e)}

        return metrics

    async def start_monitoring(self, interval_seconds: int = 60):
        """启动监控(定期收集指标)"""
        logger.info(f"📊 启动性能监控, 采集间隔: {interval_seconds}秒")

        while True:
            try:
                metrics = await self.collect_metrics()
                self.add_to_history(metrics)
                logger.info(f"📈 指标已收集: {len(metrics.get('optimizations', {}))} 个优化器")
            except Exception as e:
                logger.error(f"监控收集失败: {e}")

            await asyncio.sleep(interval_seconds)

    def add_to_history(self, metrics: dict[str, Any]) -> None:
        """添加到历史记录"""
        self.metrics_history.append(metrics)
        # 限制历史记录大小
        if len(self.metrics_history) > self.max_history:
            self.metrics_history = self.metrics_history[-self.max_history :]

    def get_summary(self) -> dict[str, Any]:
        """获取摘要统计"""
        if not self.metrics_history:
            return {"status": "no_data"}

        latest = self.metrics_history[-1]

        summary = {
            "monitoring_period": {
                "start": self.metrics_history[0]["timestamp"],
                "end": latest["timestamp"],
                "data_points": len(self.metrics_history),
            },
            "current_status": latest,
            "highlights": [],
        }

        # 计算关键指标
        try:
            # API限流器
            api_stats = latest["optimizations"].get("api_limiter", {})
            if api_stats:
                summary["highlights"].append(
                    {
                        "component": "API限流器",
                        "total_requests": api_stats.get("total_requests", 0),
                        "peak_concurrent": api_stats.get("peak_concurrent", 0),
                        "rejection_rate": api_stats.get("rejection_rate", "0%"),
                    }
                )

            # 数据库限流器
            db_stats = latest["optimizations"].get("db_limiter", {})
            if db_stats:
                summary["highlights"].append(
                    {
                        "component": "数据库限流器",
                        "total_requests": db_stats.get("total_requests", 0),
                        "peak_concurrent": db_stats.get("peak_concurrent", 0),
                    }
                )

            # 批处理器
            for name, stats in latest.get("batch_processors", {}).items():
                if isinstance(stats, dict) and stats.get("total_requests", 0) > 0:
                    summary["highlights"].append(
                        {
                            "component": f"批处理器({name})",
                            "total_requests": stats.get("total_requests", 0),
                            "avg_batch_size": stats.get("avg_batch_size", 0),
                            "throughput_per_sec": stats.get("throughput_per_sec", 0),
                        }
                    )

        except Exception as e:
            logger.error(f"生成摘要失败: {e}")

        return summary

    def export_metrics(self, filepath: Optional[str] = None) -> Any:
        """导出指标到文件"""
        if not filepath:
            filepath = f"performance_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        try:
            export_data = {
                "metadata": {
                    "export_time": datetime.now().isoformat(),
                    "total_records": len(self.metrics_history),
                    "monitoring_start": self.start_time.isoformat(),
                },
                "metrics": self.metrics_history,
            }

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            logger.info(f"✅ 指标已导出: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"导出指标失败: {e}")
            return None


# HTML仪表板模板
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Athena性能监控仪表板</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        .header {
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }

        .header h1 {
            color: #333;
            margin-bottom: 10px;
        }

        .header .subtitle {
            color: #666;
            font-size: 14px;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }

        .card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }

        .card:hover {
            transform: translate_y(-5px);
        }

        .card h3 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 18px;
        }

        .metric {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #f0f0f0;
        }

        .metric:last-child {
            border-bottom: none;
        }

        .metric-label {
            color: #666;
            font-size: 14px;
        }

        .metric-value {
            font-weight: bold;
            color: #333;
        }

        .status {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
        }

        .status.healthy {
            background: #d4edda;
            color: #155724;
        }

        .status.warning {
            background: #fff3cd;
            color: #856404;
        }

        .status.error {
            background: #f8d7da;
            color: #721c24;
        }

        .refresh-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.3s ease;
        }

        .refresh-btn:hover {
            background: #5a67d8;
        }

        .timestamp {
            color: #999;
            font-size: 12px;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Athena性能监控仪表板</h1>
            <p class="subtitle">实时性能优化指标监控</p>
            <button class="refresh-btn" onclick="location.reload()">🔄 刷新数据</button>
            <span class="timestamp" id="timestamp"></span>
        </div>

        <div class="grid" id="metrics">
            <!-- 指标卡片将通过JavaScript动态生成 -->
        </div>
    </div>

    <script>
        // 更新时间戳
        document.get_element_by_id('timestamp').text_content = '最后更新: ' + new Date().to_locale_string('zh-CN');

        // 从API获取指标数据
        async function fetch_metrics() {
            try {
                const response = await fetch('/api/performance/stats');
                const data = await response.json();
                render_metrics(data);
            } catch (error) {
                console.error('获取指标失败:', error);
                render_error();
            }
        }

        // 渲染指标
        function render_metrics(data) {
            const container = document.get_element_by_id('metrics');
            container.inner_html = '';

            if (data.optimizations) {
                // API限流器
                if (data.optimizations.api_limiter) {
                    container.inner_html += create_card('API限流器', data.optimizations.api_limiter, [
                        { key: 'total_requests', label: '总请求数' },
                        { key: 'peak_concurrent', label: '峰值并发' },
                        { key: 'utilization', label: '利用率' }
                    ]);
                }

                // 数据库限流器
                if (data.optimizations.db_limiter) {
                    container.inner_html += create_card('数据库限流器', data.optimizations.db_limiter, [
                        { key: 'total_requests', label: '总请求数' },
                        { key: 'peak_concurrent', label: '峰值并发' },
                        { key: 'utilization', label: '利用率' }
                    ]);
                }

                // 速率限制器
                if (data.optimizations.rate_limiter) {
                    container.inner_html += create_card('速率限制器', data.optimizations.rate_limiter, [
                        { key: 'rate', label: '速率' },
                        { key: 'utilization', label: '利用率' }
                    ]);
                }
            }
        }

        // 创建卡片
        function create_card(title, data, fields) {
            let metrics_html = fields.map(field => {
                const value = data[field.key];
                return `
                    <div class="metric">
                        <span class="metric-label">${field.label}</span>
                        <span class="metric-value">${value}</span>
                    </div>
                `;
            }).join('');

            return `
                <div class="card">
                    <h3>${title}</h3>
                    ${metrics_html}
                </div>
            `;
        }

        // 渲染错误
        function render_error() {
            document.get_element_by_id('metrics').inner_html = `
                <div class="card" style="grid-column: 1 / -1;">
                    <h3>❌ 无法获取指标数据</h3>
                    <p style="color: #999;">请确保API服务正在运行</p>
                </div>
            `;
        }

        // 页面加载时获取指标
        fetch_metrics();

        // 每30秒自动刷新
        set_interval(fetch_metrics, 30000);
    </script>
</body>
</html>
"""


async def main():
    """主函数 - 演示仪表板使用"""
    import sys

    # 添加项目根目录到路径
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    dashboard = PerformanceDashboard()

    # 收集一次指标
    metrics = await dashboard.collect_metrics()
    print("\n📊 当前性能指标:")
    print(json.dumps(metrics, indent=2, ensure_ascii=False))

    # 生成HTML仪表板
    html_path = Path(__file__).parent / "performance_dashboard.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(DASHBOARD_HTML)

    print(f"\n✅ HTML仪表板已生成: {html_path}")
    print("💡 在API服务运行时,访问 http://localhost:8000/api/performance/stats 查看实时数据")

    # 导出指标
    export_path = dashboard.export_metrics()
    if export_path:
        print(f"✅ 指标已导出: {export_path}")


# 入口点: @async_main装饰器已添加到main函数
