#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Athena平台知识图谱性能监控和告警系统
实时监控系统性能、服务状态，并在异常时发送告警
"""

import asyncio
from core.async_main import async_main
import json
import logging
from core.logging_config import setup_logging
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
import aiohttp
import aiofiles
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import websockets
from dataclasses import dataclass, asdict

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/xujian/Athena工作平台/logs/kg_monitoring.log'),
        logging.StreamHandler()
    ]
)
logger = setup_logging()

@dataclass
class MetricData:
    """指标数据"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    tags: Dict[str, str] = None

@dataclass
class AlertRule:
    """告警规则"""
    name: str
    metric: str
    condition: str  # gt, lt, eq, ne
    threshold: float
    duration: int  # 持续时间（秒）
    severity: str  # info, warning, critical
    message: str
    enabled: bool = True

class KnowledgeGraphMonitoringSystem:
    """知识图谱监控系统"""

    def __init__(self):
        self.platform_root = Path("/Users/xujian/Athena工作平台")
        self.config_path = self.platform_root / "config" / "monitoring_config.json"
        self.metrics_dir = self.platform_root / "data" / "metrics"
        self.metrics_dir.mkdir(parents=True, exist_ok=True)

        # 监控状态
        self.is_running = False
        self.metrics_store: List[MetricData] = []
        self.alert_rules: List[AlertRule] = []
        self.alert_history: List[Dict] = []
        self.last_alert_time: Dict[str, datetime] = {}

        # 服务配置
        self.services = {
            "janusgraph": {"host": "localhost", "port": 8182, "name": "JanusGraph"},
            "qdrant": {"host": "localhost", "port": 6333, "name": "Qdrant"},
            "redis": {"host": "localhost", "port": 6379, "name": "Redis"},
            "kg_api": {"host": "localhost", "port": 8080, "name": "知识图谱API"},
            "qa_system": {"host": "localhost", "port": 8082, "name": "问答系统"},
            "sync_service": {"host": "localhost", "port": 8081, "name": "同步服务"}
        }

        # WebSocket客户端
        self.websocket_clients = set()

        # 加载配置
        self._load_config()

    def _load_config(self) -> Any:
        """加载监控配置"""
        default_config = {
            "monitoring": {
                "interval": 30,  # 监控间隔（秒）
                "retention_days": 7,  # 数据保留天数
                "max_metrics": 10000  # 最大指标数量
            },
            "alerts": {
                "email": {
                    "enabled": False,
                    "smtp_server": "smtp.gmail.com",
                    "smtp_port": 587,
                    "username": "",
                    "password": "",
                    "recipients": []
                },
                "webhook": {
                    "enabled": False,
                    "url": "",
                    "headers": {}
                },
                "slack": {
                    "enabled": False,
                    "webhook_url": ""
                }
            },
            "dashboard": {
                "port": 8083,
                "refresh_interval": 5
            }
        }

        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    self.config = {**default_config, **loaded_config}
            else:
                self.config = default_config
                # 创建配置文件
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, ensure_ascii=False, indent=2)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"配置文件加载失败: {e}，使用默认配置")
            self.config = default_config

        # 初始化告警规则
        self._init_alert_rules()

    def _init_alert_rules(self) -> Any:
        """初始化告警规则"""
        default_rules = [
            AlertRule(
                name="CPU使用率过高",
                metric="cpu_usage",
                condition="gt",
                threshold=80.0,
                duration=300,  # 5分钟
                severity="warning",
                message="CPU使用率超过80%"
            ),
            AlertRule(
                name="内存使用率过高",
                metric="memory_usage",
                condition="gt",
                threshold=90.0,
                duration=300,
                severity="critical",
                message="内存使用率超过90%"
            ),
            AlertRule(
                name="磁盘空间不足",
                metric="disk_usage",
                condition="gt",
                threshold=85.0,
                duration=60,
                severity="warning",
                message="磁盘使用率超过85%"
            ),
            AlertRule(
                name="服务不可用",
                metric="service_down",
                condition="gt",
                threshold=0.5,
                duration=30,
                severity="critical",
                message="检测到服务不可用"
            ),
            AlertRule(
                name="API响应时间过长",
                metric="api_response_time",
                condition="gt",
                threshold=5000,  # 5秒
                duration=120,
                severity="warning",
                message="API响应时间超过5秒"
            )
        ]

        self.alert_rules = default_rules

    async def start_monitoring(self):
        """启动监控"""
        logger.info("🚀 启动知识图谱监控系统...")
        self.is_running = True

        # 启动WebSocket服务器
        websocket_task = asyncio.create_task(self._start_websocket_server())

        # 启动监控循环
        monitor_task = asyncio.create_task(self._monitoring_loop())

        # 启动数据清理任务
        cleanup_task = asyncio.create_task(self._cleanup_loop())

        try:
            await asyncio.gather(monitor_task, websocket_task, cleanup_task)
        except KeyboardInterrupt:
            logger.info("⏹️ 收到停止信号")
        finally:
            await self.stop_monitoring()

    async def stop_monitoring(self):
        """停止监控"""
        self.is_running = False
        logger.info("✅ 监控系统已停止")

    async def _monitoring_loop(self):
        """监控循环"""
        interval = self.config["monitoring"]["interval"]
        logger.info(f"📊 启动监控循环，间隔 {interval} 秒")

        while self.is_running:
            try:
                # 收集系统指标
                await self._collect_system_metrics()

                # 检查服务状态
                await self._check_service_status()

                # 检查API性能
                await self._check_api_performance()

                # 检查告警规则
                await self._check_alert_rules()

                # 保存指标数据
                await self._save_metrics()

                await asyncio.sleep(interval)

            except Exception as e:
                logger.error(f"❌ 监控循环错误: {e}")
                await asyncio.sleep(5)

    async def _collect_system_metrics(self):
        """收集系统指标"""
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        self._add_metric("cpu_usage", cpu_percent, "%")

        # 内存使用率
        memory = psutil.virtual_memory()
        self._add_metric("memory_usage", memory.percent, "%")
        self._add_metric("memory_total", memory.total / (1024**3), "GB")
        self._add_metric("memory_used", memory.used / (1024**3), "GB")

        # 磁盘使用率
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        self._add_metric("disk_usage", disk_percent, "%")
        self._add_metric("disk_total", disk.total / (1024**3), "GB")
        self._add_metric("disk_free", disk.free / (1024**3), "GB")

        # 网络IO
        net_io = psutil.net_io_counters()
        self._add_metric("network_bytes_sent", net_io.bytes_sent, "bytes")
        self._add_metric("network_bytes_recv", net_io.bytes_recv, "bytes")

        # 负载平均
        load_avg = psutil.getloadavg()
        self._add_metric("load_1m", load_avg[0], "")
        self._add_metric("load_5m", load_avg[1], "")
        self._add_metric("load_15m", load_avg[2], "")

    async def _check_service_status(self):
        """检查服务状态"""
        services_down = []

        for service_key, service_config in self.services.items():
            is_up = await self._check_service_health(service_config)
            status_value = 1.0 if is_up else 0.0

            self._add_metric(
                f"service_{service_key}_status",
                status_value,
                "",
                {"service": service_config["name"]}
            )

            if not is_up:
                services_down.append(service_config["name"])

        # 服务不可用告警指标
        self._add_metric(
            "service_down",
            len(services_down) / len(self.services),
            "",
            {"services": ",".join(services_down)}
        )

    async def _check_service_health(self, service_config: Dict) -> bool:
        """检查单个服务健康状态"""
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((service_config["host"], service_config["port"]))
            sock.close()
            return result == 0
        except (KeyError, TypeError, IndexError, ValueError):
            return False

    async def _check_api_performance(self):
        """检查API性能"""
        apis_to_check = [
            {"name": "kg_api", "url": "http://localhost:8080/health"},
            {"name": "qa_system", "url": "http://localhost:8082/api/v1/health"}
        ]

        for api in apis_to_check:
            try:
                start_time = time.time()
                async with aiohttp.ClientSession() as session:
                    async with session.get(api["url"], timeout=10) as resp:
                        response_time = (time.time() - start_time) * 1000  # 毫秒
                        status_code = resp.status

                        self._add_metric(
                            f"{api['name']}_response_time",
                            response_time,
                            "ms"
                        )

                        self._add_metric(
                            f"{api['name']}_status_code",
                            status_code,
                            ""
                        )

                        # 记录API可用性
                        is_available = 200 <= status_code < 400
                        self._add_metric(
                            f"{api['name']}_availability",
                            1.0 if is_available else 0.0,
                            ""
                        )

            except Exception as e:
                logger.warning(f"⚠️ API检查失败 {api['name']}: {e}")
                self._add_metric(f"{api['name']}_availability", 0.0, "")

    async def _check_alert_rules(self):
        """检查告警规则"""
        for rule in self.alert_rules:
            if not rule.enabled:
                continue

            try:
                await self._evaluate_alert_rule(rule)
            except Exception as e:
                logger.error(f"❌ 告警规则检查失败 {rule.name}: {e}")

    async def _evaluate_alert_rule(self, rule: AlertRule):
        """评估告警规则"""
        # 获取最近的指标数据
        recent_metrics = [
            m for m in self.metrics_store
            if m.name == rule.metric and
               m.timestamp > datetime.now() - timedelta(seconds=rule.duration)
        ]

        if not recent_metrics:
            return

        # 检查是否触发告警
        latest_metric = recent_metrics[-1]
        triggered = self._evaluate_condition(
            latest_metric.value,
            rule.condition,
            rule.threshold
        )

        if triggered:
            # 检查是否需要发送告警（避免重复）
            now = datetime.now()
            last_time = self.last_alert_time.get(rule.name)

            if not last_time or (now - last_time).total_seconds() > rule.duration:
                await self._send_alert(rule, latest_metric)
                self.last_alert_time[rule.name] = now

    def _evaluate_condition(self, value: float, condition: str, threshold: float) -> bool:
        """评估条件"""
        if condition == "gt":
            return value > threshold
        elif condition == "lt":
            return value < threshold
        elif condition == "eq":
            return abs(value - threshold) < 0.001
        elif condition == "ne":
            return abs(value - threshold) >= 0.001
        return False

    async def _send_alert(self, rule: AlertRule, metric: MetricData):
        """发送告警"""
        alert_data = {
            "rule_name": rule.name,
            "severity": rule.severity,
            "message": rule.message,
            "metric_name": metric.name,
            "metric_value": metric.value,
            "threshold": rule.threshold,
            "timestamp": datetime.now().isoformat()
        }

        # 记录告警历史
        self.alert_history.append(alert_data)

        # 发送到WebSocket客户端
        await self._broadcast_alert(alert_data)

        # 发送邮件通知
        if self.config["alerts"]["email"]["enabled"]:
            await self._send_email_alert(alert_data)

        # 发送Webhook通知
        if self.config["alerts"]["webhook"]["enabled"]:
            await self._send_webhook_alert(alert_data)

        # 记录日志
        logger.warning(f"🚨 告警: {rule.name} - {rule.message}")

    async def _broadcast_alert(self, alert_data: Dict):
        """广播告警到WebSocket客户端"""
        if not self.websocket_clients:
            return

        message = json.dumps({
            "type": "alert",
            "data": alert_data
        })

        disconnected = set()
        for ws in self.websocket_clients:
            try:
                await ws.send(message)
            except (json.JSONDecodeError, TypeError, ValueError):
                disconnected.add(ws)

        self.websocket_clients -= disconnected

    async def _send_email_alert(self, alert_data: Dict):
        """发送邮件告警"""
        try:
            email_config = self.config["alerts"]["email"]

            msg = MimeMultipart()
            msg['From'] = email_config["username"]
            msg['To'] = ", ".join(email_config["recipients"])
            msg['Subject'] = f"[Athena告警] {alert_data['rule_name']}"

            body = f"""
告警名称: {alert_data['rule_name']}
严重程度: {alert_data['severity']}
告警信息: {alert_data['message']}
指标名称: {alert_data['metric_name']}
当前值: {alert_data['metric_value']}
阈值: {alert_data['threshold']}
时间: {alert_data['timestamp']}
            """

            msg.attach(MimeText(body, 'plain', 'utf-8'))

            # 发送邮件
            with smtplib.SMTP(email_config["smtp_server"], email_config["smtp_port"]) as server:
                server.starttls()
                server.login(email_config["username"], email_config["password"])
                server.send_message(msg)

            logger.info("✅ 邮件告警已发送")

        except Exception as e:
            logger.error(f"❌ 发送邮件告警失败: {e}")

    async def _send_webhook_alert(self, alert_data: Dict):
        """发送Webhook告警"""
        try:
            webhook_config = self.config["alerts"]["webhook"]

            async with aiohttp.ClientSession() as session:
                await session.post(
                    webhook_config["url"],
                    json=alert_data,
                    headers=webhook_config["headers"]
                )

            logger.info("✅ Webhook告警已发送")

        except Exception as e:
            logger.error(f"❌ 发送Webhook告警失败: {e}")

    def _add_metric(self, name: str, value: float, unit: str, tags: Dict[str, str] = None) -> Any:
        """添加指标数据"""
        metric = MetricData(
            name=name,
            value=value,
            unit=unit,
            timestamp=datetime.now(),
            tags=tags or {}
        )

        self.metrics_store.append(metric)

        # 限制指标数量
        max_metrics = self.config["monitoring"]["max_metrics"]
        if len(self.metrics_store) > max_metrics:
            self.metrics_store = self.metrics_store[-max_metrics:]

    async def _save_metrics(self):
        """保存指标数据"""
        if not self.metrics_store:
            return

        # 按日期保存
        date_str = datetime.now().strftime("%Y%m%d")
        metrics_file = self.metrics_dir / f"metrics_{date_str}.json"

        # 转换为可序列化格式
        metrics_data = [
            {
                "name": m.name,
                "value": m.value,
                "unit": m.unit,
                "timestamp": m.timestamp.isoformat(),
                "tags": m.tags
            }
            for m in self.metrics_store[-100:]  # 只保存最近100条
        ]

        try:
            async with aiofiles.open(metrics_file, 'w') as f:
                await f.write(json.dumps(metrics_data, ensure_ascii=False, indent=2))
        except Exception as e:
            logger.error(f"❌ 保存指标数据失败: {e}")

    async def _cleanup_loop(self):
        """数据清理循环"""
        while self.is_running:
            try:
                # 每天清理一次
                await asyncio.sleep(86400)
                await self._cleanup_old_data()
            except Exception as e:
                logger.error(f"❌ 数据清理失败: {e}")

    async def _cleanup_old_data(self):
        """清理旧数据"""
        retention_days = self.config["monitoring"]["retention_days"]
        cutoff_date = datetime.now() - timedelta(days=retention_days)

        # 清理内存中的指标数据
        self.metrics_store = [
            m for m in self.metrics_store if m.timestamp > cutoff_date
        ]

        # 清理文件中的指标数据
        for metrics_file in self.metrics_dir.glob("metrics_*.json"):
            try:
                file_date_str = metrics_file.stem.split("_")[1]
                file_date = datetime.strptime(file_date_str, "%Y%m%d")

                if file_date < cutoff_date:
                    metrics_file.unlink()
                    logger.info(f"🗑️ 已删除旧指标文件: {metrics_file}")

            except Exception as e:
                logger.error(f"❌ 清理文件失败 {metrics_file}: {e}")

    async def _start_websocket_server(self):
        """启动WebSocket服务器"""
        port = self.config["dashboard"]["port"]

        async def handle_client(websocket, path):
            self.websocket_clients.add(websocket)
            logger.info(f"🔌 监控客户端连接: {websocket.remote_address}")

            try:
                # 发送初始数据
                await websocket.send(json.dumps({
                    "type": "init",
                    "metrics_count": len(self.metrics_store),
                    "services": list(self.services.keys())
                }))

                # 保持连接
                async for message in websocket:
                    data = json.loads(message)

                    if data.get("type") == "get_metrics":
                        # 返回最近的指标数据
                        recent_metrics = self.metrics_store[-100:]
                        metrics_data = [asdict(m) for m in recent_metrics]

                        await websocket.send(json.dumps({
                            "type": "metrics_data",
                            "data": metrics_data
                        }))

            except websockets.exceptions.ConnectionClosed:
                logger.error(f"Error: {e}", exc_info=True)
            finally:
                self.websocket_clients.discard(websocket)

        logger.info(f"🌐 监控WebSocket服务器启动在端口 {port}")

        async with websockets.serve(handle_client, "localhost", port):
            await asyncio.Future()  # 保持服务器运行

    async def get_metrics_summary(self) -> Dict:
        """获取指标摘要"""
        if not self.metrics_store:
            return {"total": 0, "by_name": {}}

        # 按名称分组统计
        metrics_by_name = {}
        for metric in self.metrics_store[-1000:]:  # 只统计最近1000条
            if metric.name not in metrics_by_name:
                metrics_by_name[metric.name] = {
                    "count": 0,
                    "latest": None,
                    "min": float('inf'),
                    "max": float('-inf'),
                    "avg": 0
                }

            stats = metrics_by_name[metric.name]
            stats["count"] += 1
            stats["min"] = min(stats["min"], metric.value)
            stats["max"] = max(stats["max"], metric.value)
            stats["latest"] = metric.value

        # 计算平均值
        for name, stats in metrics_by_name.items():
            values = [
                m.value for m in self.metrics_store[-1000:]
                if m.name == name
            ]
            if values:
                stats["avg"] = sum(values) / len(values)

        return {
            "total": len(self.metrics_store),
            "by_name": metrics_by_name
        }

async def main():
    """主函数"""
    monitoring = KnowledgeGraphMonitoringSystem()

    # 设置优雅关闭
    import signal

    def signal_handler(signum, frame) -> None:
        logger.info("🛑 收到关闭信号")
        asyncio.create_task(monitoring.stop_monitoring())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 启动监控
    try:
        await monitoring.start_monitoring()
    except Exception as e:
        logger.error(f"❌ 监控系统启动失败: {e}")
        import traceback
        traceback.print_exc()

# 入口点: @async_main装饰器已添加到main函数