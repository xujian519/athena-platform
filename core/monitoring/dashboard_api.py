#!/usr/bin/env python3
"""
知识图谱监控仪表板API
Knowledge Graph Monitoring Dashboard API

提供Web界面和REST API来展示系统性能监控数据
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from core.logging_config import setup_logging

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    import uvicorn
    from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
    from fastapi.middleware.cors import CORSMiddleware

from core.security.auth import ALLOWED_ORIGINS
    from fastapi.responses import HTMLResponse, JSONResponse

    FASTAPI_AVAILABLE = True
except ImportError:
    print("⚠️ FastAPI未安装,无法启动Web仪表板")
    FASTAPI_AVAILABLE = False

from .performance_monitor import (
    get_performance_monitor,
    record_cache_performance,
    record_search_performance,
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class DashboardAPI:
    """监控仪表板API"""

    def __init__(self, host: str = "0.0.0.0", port: int = 8899):
        self.host = host
        self.port = port
        self.app = None
        self.server = None

        if FASTAPI_AVAILABLE:
            self._create_app()

    def _create_app(self) -> Any:
        """创建FastAPI应用"""
        self.app = FastAPI(
            title="知识图谱系统监控仪表板",
            description="Knowledge Graph System Monitoring Dashboard",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc",
        )

        # 添加CORS中间件
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=ALLOWED_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # 注册路由
        self._register_routes()

    def _register_routes(self) -> Any:
        """注册API路由"""

        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard_home():
            """仪表板主页"""
            return self._generate_dashboard_html()

        @self.app.get("/api/dashboard")
        async def get_dashboard_data():
            """获取仪表板数据"""
            try:
                monitor = await get_performance_monitor()
                return monitor.get_dashboard_data()
            except Exception as e:
                logger.error(f"❌ 获取仪表板数据失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/metrics")
        async def get_metrics(
            metric_name: str = Query(None, description="指标名称"),
            hours: int = Query(1, description="时间范围(小时)"),
        ):
            """获取指标数据"""
            try:
                monitor = await get_performance_monitor()

                if metric_name:
                    # 获取特定指标
                    trends = monitor.get_performance_trends(hours)
                    if metric_name in trends:
                        return {"metric": metric_name, "data": trends[metric_name]}
                    else:
                        raise HTTPException(status_code=404, detail=f"指标 {metric_name} 未找到")
                else:
                    # 获取所有指标趋势
                    return monitor.get_performance_trends(hours)

            except Exception as e:
                logger.error(f"❌ 获取指标数据失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/alerts")
        async def get_alerts(
            active_only: bool = Query(False, description="仅获取活跃告警"),
            limit: int = Query(50, description="限制数量"),
        ):
            """获取告警信息"""
            try:
                monitor = await get_performance_monitor()
                alerts = monitor.get_recent_alerts(limit)

                if active_only:
                    alerts = [alert for alert in alerts if not alert.get("resolved", False)]

                return {"alerts": alerts, "total": len(alerts)}

            except Exception as e:
                logger.error(f"❌ 获取告警信息失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/system")
        async def get_system_status():
            """获取系统状态"""
            try:
                monitor = await get_performance_monitor()

                return {
                    "status": monitor.get_metrics_summary(),
                    "resources": monitor.get_current_system_resources(),
                    "statistics": monitor.get_statistics(),
                }

            except Exception as e:
                logger.error(f"❌ 获取系统状态失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/record/search")
        async def record_search(
            search_type: str, response_time: float, result_count: int, success: bool = True
        ):
            """记录搜索性能"""
            try:
                await record_search_performance(search_type, response_time, result_count, success)
                return {"status": "success", "message": "搜索性能记录成功"}

            except Exception as e:
                logger.error(f"❌ 记录搜索性能失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/record/cache")
        async def record_cache(
            cache_name: str, hit_count: int, miss_count: int, total_requests: int
        ):
            """记录缓存性能"""
            try:
                await record_cache_performance(cache_name, hit_count, miss_count, total_requests)
                return {"status": "success", "message": "缓存性能记录成功"}

            except Exception as e:
                logger.error(f"❌ 记录缓存性能失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/alerts/{alert_id}/resolve")
        async def resolve_alert(alert_id: str):
            """解决告警"""
            try:
                monitor = await get_performance_monitor()
                success = await monitor.resolve_alert(alert_id)

                if success:
                    return {"status": "success", "message": f"告警 {alert_id} 已解决"}
                else:
                    raise HTTPException(status_code=404, detail=f"告警 {alert_id} 未找到或已解决")

            except Exception as e:
                logger.error(f"❌ 解决告警失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/export")
        async def export_data(
            format: str = Query("json", description="导出格式"),
            hours: int = Query(24, description="时间范围(小时)"),
        ):
            """导出监控数据"""
            try:
                monitor = await get_performance_monitor()

                if format.lower() == "json":
                    filename = f"monitoring_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    success = await monitor.export_metrics(filename, hours)

                    if success:
                        return {"status": "success", "filename": filename}
                    else:
                        raise HTTPException(status_code=500, detail="导出失败")
                else:
                    raise HTTPException(status_code=400, detail=f"不支持的格式: {format}")

            except Exception as e:
                logger.error(f"❌ 导出数据失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/health")
        async def health_check():
            """健康检查"""
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}

    def _generate_dashboard_html(self) -> str:
        """生成仪表板HTML页面"""
        return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>知识图谱系统监控仪表板</title>
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
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }

        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .header p {
            font-size: 1.1rem;
            opacity: 0.9;
        }

        .dashboard {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
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
            color: #333;
            margin-bottom: 15px;
            font-size: 1.2rem;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }

        .metric-value {
            font-size: 2rem;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 10px;
        }

        .metric-label {
            color: #666;
            font-size: 0.9rem;
        }

        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }

        .status-healthy { background-color: #10b981; }
        .status-warning { background-color: #f59e0b; }
        .status-error { background-color: #ef4444; }
        .status-critical { background-color: #dc2626; }

        .alerts-container {
            max-height: 300px;
            overflow-y: auto;
        }

        .alert-item {
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 8px;
            border-left: 4px solid;
        }

        .alert-warning {
            background: #fef3c7;
            border-color: #f59e0b;
        }

        .alert-error {
            background: #fee2e2;
            border-color: #ef4444;
        }

        .alert-critical {
            background: #fecaca;
            border-color: #dc2626;
        }

        .refresh-button {
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1rem;
            transition: background 0.3s ease;
            margin-bottom: 20px;
        }

        .refresh-button:hover {
            background: #5a67d8;
        }

        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }

        .grid-2 {
            grid-template-columns: repeat(2, 1fr);
        }

        .grid-3 {
            grid-template-columns: repeat(3, 1fr);
        }

        @media (max-width: 768px) {
            .dashboard {
                grid-template-columns: 1fr;
            }

            .header h1 {
                font-size: 2rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧠 知识图谱系统监控仪表板</h1>
            <p>实时监控法律知识图谱+向量库 & 专利规则知识图谱+向量库系统性能</p>
        </div>

        <button class="refresh-button" onclick="load_dashboard_data()">🔄 刷新数据</button>

        <div class="dashboard" id="dashboard">
            <div class="loading">正在加载监控数据...</div>
        </div>
    </div>

    <script>
        let last_update = null;

        async function load_dashboard_data() {
            try {
                const response = await fetch('/api/dashboard');
                const data = await response.json();

                render_dashboard(data);
                last_update = new Date();

                // 更新页面标题显示最后更新时间
                document.title = `知识图谱监控仪表板 - 最后更新: ${last_update.to_locale_time_string()}`;

            } catch (error) {
                console.error('加载仪表板数据失败:', error);
                document.get_element_by_id('dashboard').inner_html =
                    '<div class="card"><h3>❌ 加载失败</h3><p>无法获取监控数据,请检查服务状态</p></div>';
            }
        }

        function render_dashboard(data) {
            const dashboard = document.get_element_by_id('dashboard');

            let html = '';

            // 系统概览卡片
            html += create_system_overview_card(data.summary);

            // 系统资源卡片
            if (data.system_resources) {
                html += create_system_resources_card(data.system_resources);
            }

            // 重要指标卡片
            if (data.top_metrics) {
                html += create_top_metrics_card(data.top_metrics);
            }

            // 最近告警卡片
            if (data.recent_alerts && data.recent_alerts.length > 0) {
                html += create_alerts_card(data.recent_alerts);
            }

            // 性能趋势卡片
            if (data.performance_trends) {
                html += create_performance_trends_card(data.performance_trends);
            }

            dashboard.inner_html = html;
        }

        function create_system_overview_card(summary) {
            const status_class = summary.system_status === 'healthy' ? 'status-healthy' :
                               summary.system_status === 'warning' ? 'status-warning' :
                               summary.system_status === 'error' ? 'status-error' : 'status-critical';

            const status_text = summary.system_status === 'healthy' ? '健康' :
                              summary.system_status === 'warning' ? '警告' :
                              summary.system_status === 'error' ? '错误' : '严重';

            return `
                <div class="card">
                    <h3>📊 系统概览</h3>
                    <div style="margin-bottom: 15px;">
                        <span class="status-indicator ${status_class}"></span>
                        <strong>系统状态: ${status_text}</strong>
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                        <div>
                            <div class="metric-value">${summary.total_metrics}</div>
                            <div class="metric-label">监控指标</div>
                        </div>
                        <div>
                            <div class="metric-value">${summary.active_alerts}</div>
                            <div class="metric-label">活跃告警</div>
                        </div>
                    </div>
                    <div style="margin-top: 15px; color: #666; font-size: 0.9rem;">
                        运行时长: ${summary.monitoring_duration || 'N/A'}<br>
                        最后收集: ${summary.last_collection ? new Date(summary.last_collection).to_locale_string() : 'N/A'}
                    </div>
                </div>
            `;
        }

        function create_system_resources_card(resources) {
            return `
                <div class="card">
                    <h3>💻 系统资源</h3>
                    <div style="margin-bottom: 15px;">
                        <div style="margin-bottom: 10px;">
                            <strong>CPU使用率:</strong> ${resources.cpu_percent?.to_fixed(1) || 0}%
                            <div style="background: #e5e7eb; height: 8px; border-radius: 4px; margin-top: 5px;">
                                <div style="background: ${resources.cpu_percent > 80 ? '#ef4444' : '#10b981'}; height: 100%; width: ${resources.cpu_percent || 0}%; border-radius: 4px;"></div>
                            </div>
                        </div>
                        <div style="margin-bottom: 10px;">
                            <strong>内存使用率:</strong> ${resources.memory_percent?.to_fixed(1) || 0}%
                            <div style="background: #e5e7eb; height: 8px; border-radius: 4px; margin-top: 5px;">
                                <div style="background: ${resources.memory_percent > 85 ? '#ef4444' : '#10b981'}; height: 100%; width: ${resources.memory_percent || 0}%; border-radius: 4px;"></div>
                            </div>
                        </div>
                        <div style="margin-bottom: 10px;">
                            <strong>磁盘使用率:</strong> ${resources.disk_usage_percent?.to_fixed(1) || 0}%
                            <div style="background: #e5e7eb; height: 8px; border-radius: 4px; margin-top: 5px;">
                                <div style="background: ${resources.disk_usage_percent > 90 ? '#ef4444' : '#10b981'}; height: 100%; width: ${resources.disk_usage_percent || 0}%; border-radius: 4px;"></div>
                            </div>
                        </div>
                    </div>
                    <div style="color: #666; font-size: 0.9rem;">
                        进程数量: ${resources.process_count || 0}<br>
                        负载平均: ${resources.load_average ? resources.load_average.slice(0, 2).join(', ') : 'N/A'}
                    </div>
                </div>
            `;
        }

        function create_top_metrics_card(metrics) {
            let html = `
                <div class="card">
                    <h3>📈 重要指标</h3>
                    <div class="alerts-container">
            `;

            for (const [name, data] of Object.entries(metrics)) {
                const trend = data.trend === 'increasing' ? '📈' :
                             data.trend === 'decreasing' ? '📉' : '➡️';

                html += `
                    <div style="margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid #e5e7eb;">
                        <strong>${name}</strong>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 5px;">
                            <span class="metric-value" style="font-size: 1.5rem;">${data.current_value?.to_fixed(2) || 0}</span>
                            <span>${trend} ${data.trend}</span>
                        </div>
                        <div style="color: #666; font-size: 0.8rem; margin-top: 5px;">
                            最近: ${data.recent_min?.to_fixed(2) || 0} - ${data.recent_max?.to_fixed(2) || 0}
                        </div>
                    </div>
                `;
            }

            html += '</div></div>';
            return html;
        }

        function create_alerts_card(alerts) {
            let html = `
                <div class="card">
                    <h3>🚨 最近告警</h3>
                    <div class="alerts-container">
            `;

            alerts.slice(0, 5).for_each(alert => {
                const alert_class = alert.severity === 'warning' ? 'alert-warning' :
                                 alert.severity === 'error' ? 'alert-error' : 'alert-critical';

                html += `
                    <div class="alert-item ${alert_class}">
                        <strong>${alert.severity.to_upper_case()}</strong>
                        <div style="margin: 5px 0;">${alert.message}</div>
                        <div style="font-size: 0.8rem; color: #666;">
                            ${new Date(alert.timestamp).to_locale_string()}
                        </div>
                    </div>
                `;
            });

            if (alerts.length === 0) {
                html += '<div style="text-align: center; color: #10b981; padding: 20px;">✅ 暂无告警</div>';
            }

            html += '</div></div>';
            return html;
        }

        function create_performance_trends_card(trends) {
            return `
                <div class="card">
                    <h3>📊 性能趋势</h3>
                    <div style="text-align: center; padding: 40px; color: #666;">
                        <div style="font-size: 3rem; margin-bottom: 10px;">📈</div>
                        <div>性能趋势图表</div>
                        <div style="font-size: 0.9rem; margin-top: 10px;">
                            实时监控系统性能变化趋势
                        </div>
                    </div>
                </div>
            `;
        }

        // 页面加载时初始化
        document.add_event_listener('DOMContentLoaded', function() {
            load_dashboard_data();

            // 每30秒自动刷新
            set_interval(load_dashboard_data, 30000);
        });
    </script>
</body>
</html>
        """

    async def start_server(self):
        """启动服务器"""
        if not FASTAPI_AVAILABLE:
            logger.error("❌ FastAPI未安装,无法启动Web仪表板")
            return False

        try:
            config = uvicorn.Config(app=self.app, host=self.host, port=self.port, log_level="info")
            self.server = uvicorn.Server(config)

            logger.info(f"🚀 启动监控仪表板服务: http://{self.host}:{self.port}")
            await self.server.serve()

            return True

        except Exception as e:
            logger.error(f"❌ 启动仪表板服务失败: {e}")
            return False

    async def stop_server(self):
        """停止服务器"""
        if self.server:
            self.server.should_exit = True
            logger.info("⏹️ 监控仪表板服务已停止")


# 创建全局仪表板实例
_dashboard_api = None


async def get_dashboard_api(host: str = "0.0.0.0", port: int = 8899) -> DashboardAPI:
    """获取仪表板API实例"""
    global _dashboard_api

    if _dashboard_api is None:
        _dashboard_api = DashboardAPI(host, port)

    return _dashboard_api


async def start_monitoring_dashboard(host: str = "0.0.0.0", port: int = 8899):
    """启动监控仪表板"""
    dashboard = await get_dashboard_api(host, port)
    return await dashboard.start_server()


if __name__ == "__main__":
    if FASTAPI_AVAILABLE:
        print("🚀 启动知识图谱系统监控仪表板...")
        asyncio.run(start_monitoring_dashboard())
    else:
        print("❌ 请安装FastAPI和uvicorn以启动Web仪表板")
        print("   pip install fastapi uvicorn")
