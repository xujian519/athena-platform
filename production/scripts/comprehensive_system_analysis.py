#!/usr/bin/env python3
"""
Athena工作平台生产环境全面分析系统
Comprehensive System Analysis for Athena Platform Production Environment

作者: Athena平台团队
创建时间: 2025-12-21
版本: v1.0.0
"""

from __future__ import annotations
import asyncio
import json
import logging
import os
import socket
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import psutil
import requests

try:
    import aiohttp
except ImportError:
    aiohttp = None

# 设置路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root.parent))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 颜色输出
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    PURPLE = "\033[35m"
    CYAN = "\033[96m"
    PINK = "\033[95m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

@dataclass
class SystemMetric:
    """系统指标"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    disk_percent: float
    disk_used_gb: float
    network_io: dict[str, float]
    load_average: list[float]

@dataclass
class ServiceStatus:
    """服务状态"""
    name: str
    pid: int | None
    status: str  # running, stopped, error
    cpu_percent: float
    memory_mb: float
    uptime: float | None
    port: int | None
    health_check_url: str | None
    response_time: float | None

@dataclass
class DatabaseStatus:
    """数据库状态"""
    name: str
    type: str
    status: str
    version: str
    connections: int
    size_gb: float
    query_time: float

@dataclass
class AnalysisReport:
    """分析报告"""
    analysis_time: str
    system_metrics: SystemMetric
    services: list[ServiceStatus]
    databases: list[DatabaseStatus]
    issues: list[dict[str, Any]]
    recommendations: list[str]
    performance_score: float

class SystemAnalyzer:
    """系统分析器"""

    def __init__(self):
        self.project_root = project_root
        self.production_dir = project_root / "production"
        self.logs_dir = self.production_dir / "logs"
        self.config_dir = self.production_dir / "config"

        # 关键服务配置
        self.service_configs = {
            "expert_rule_engine": {
                "port": 8001,
                "health_path": "/health",
                "description": "专家规则推理引擎"
            },
            "patent_rule_chain": {
                "port": 8002,
                "health_path": "/health",
                "description": "专利规则链引擎"
            },
            "prior_art_analyzer": {
                "port": 8003,
                "health_path": "/health",
                "description": "现有技术分析器"
            },
            "llm_enhanced_judgment": {
                "port": 8004,
                "health_path": "/health",
                "description": "LLM增强判断系统"
            },
            "xiaonuo_service": {
                "port": 8000,
                "health_path": "/status",
                "description": "小诺核心服务"
            },
            "nlp_service": {
                "port": 8005,
                "health_path": "/health",
                "description": "NLP服务"
            }
        }

        # 数据库配置
        self.database_configs = {
            "postgresql": {
                "port": 5432,
                "host": "localhost",
                "user": "postgres",
                "password": "xj781102",
                "databases": ["athena_kg", "patent_db", "xiaonuo_db"]
            },
            "qdrant": {
                "port": 6333,
                "host": "localhost",
                "api_path": "/"
            },
            "redis": {
                "port": 6379,
                "host": "localhost"
            }
        }

        self.analysis_results = {
            "issues": [],
            "warnings": [],
            "recommendations": []
        }

    def print_header(self, title: str) -> Any:
        """打印标题"""
        print(f"\n{Colors.PURPLE}{'='*80}{Colors.RESET}")
        print(f"{Colors.PURPLE}{Colors.BOLD}📊 {title} 📊{Colors.RESET}")
        print(f"{Colors.PURPLE}{'='*80}{Colors.RESET}")

    def print_success(self, message: str) -> Any:
        """打印成功信息"""
        print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")

    def print_error(self, message: str) -> Any:
        """打印错误信息"""
        print(f"{Colors.RED}❌ {message}{Colors.RESET}")

    def print_warning(self, message: str) -> Any:
        """打印警告信息"""
        print(f"{Colors.YELLOW}⚠️ {message}{Colors.RESET}")

    def print_info(self, message: str) -> Any:
        """打印信息"""
        print(f"{Colors.BLUE}ℹ️ {message}{Colors.RESET}")

    async def analyze_system_metrics(self) -> SystemMetric:
        """分析系统指标"""
        self.print_header("系统资源使用分析")

        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)

        # 内存使用
        memory = psutil.virtual_memory()
        memory_used_gb = memory.used / (1024**3)

        # 磁盘使用
        disk = psutil.disk_usage('/')
        disk_used_gb = disk.used / (1024**3)

        # 网络IO
        net_io = psutil.net_io_counters()
        network_io = {
            "bytes_sent": net_io.bytes_sent / (1024**2),  # MB
            "bytes_recv": net_io.bytes_recv / (1024**2),  # MB
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv
        }

        # 负载均衡
        try:
            load_avg = list(psutil.getloadavg())
        except AttributeError:
            load_avg = [0.0, 0.0, 0.0]  # Windows不支持

        metric = SystemMetric(
            timestamp=datetime.now().isoformat(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used_gb=memory_used_gb,
            disk_percent=disk.percent,
            disk_used_gb=disk_used_gb,
            network_io=network_io,
            load_average=load_avg
        )

        # 显示指标
        print(f"🖥️  CPU使用率: {cpu_percent:.1f}%")
        if cpu_percent > 80:
            self.print_warning("CPU使用率过高！")
            self.analysis_results["issues"].append({
                "type": "performance",
                "component": "CPU",
                "issue": "CPU使用率过高",
                "value": cpu_percent,
                "threshold": 80
            })

        print(f"💾 内存使用: {memory.percent:.1f}% ({memory_used_gb:.1f}GB)")
        if memory.percent > 85:
            self.print_warning("内存使用率过高！")
            self.analysis_results["issues"].append({
                "type": "performance",
                "component": "Memory",
                "issue": "内存使用率过高",
                "value": memory.percent,
                "threshold": 85
            })

        print(f"💿 磁盘使用: {disk.percent:.1f}% ({disk_used_gb:.1f}GB)")
        if disk.percent > 90:
            self.print_error("磁盘空间不足！")
            self.analysis_results["issues"].append({
                "type": "storage",
                "component": "Disk",
                "issue": "磁盘空间不足",
                "value": disk.percent,
                "threshold": 90
            })

        print(f"📡 网络IO: 发送{network_io['bytes_sent']:.1f}MB, 接收{network_io['bytes_recv']:.1f}MB")
        print(f"⚖️  负载均衡: {load_avg[0]:.2f}, {load_avg[1]:.2f}, {load_avg[2]:.2f}")

        return metric

    async def analyze_services(self) -> list[ServiceStatus]:
        """分析服务状态"""
        self.print_header("微服务架构一致性检查")

        services = []

        # 检查PID文件
        for service_name, config in self.service_configs.items():
            status = self._check_service_status(service_name, config)
            services.append(status)

            # 显示状态
            if status.status == "running":
                self.print_success(f"{service_name}: 运行中 (PID:{status.pid}, CPU:{status.cpu_percent:.1f}%, 内存:{status.memory_mb:.1f}MB)")
            else:
                self.print_error(f"{service_name}: {status.status}")

            # 检查健康状态
            if status.status == "running" and config.get("health_path"):
                health_status = await self._check_service_health(status, config)
                if health_status["healthy"]:
                    self.print_success(f"  健康检查: 正常 (响应时间: {health_status['response_time']:.2f}s)")
                else:
                    self.print_error(f"  健康检查: 失败 - {health_status['error']}")
                    self.analysis_results["issues"].append({
                        "type": "service_health",
                        "component": service_name,
                        "issue": "健康检查失败",
                        "error": health_status["error"]
                    })

        # 检查服务间通信
        await self._check_service_communication(services)

        return services

    def _check_service_status(self, service_name: str, config: dict[str, Any]) -> ServiceStatus:
        """检查单个服务状态"""
        pid_file = self.logs_dir / f"{service_name}.pid"

        if not pid_file.exists():
            return ServiceStatus(
                name=service_name,
                pid=None,
                status="stopped",
                cpu_percent=0,
                memory_mb=0,
                uptime=None,
                port=config.get("port"),
                health_check_url=f"http://localhost:{config.get('port')}{config.get('health_path', '')}",
                response_time=None
            )

        try:
            with open(pid_file) as f:
                pid = int(f.read().strip())

            if not psutil.pid_exists(pid):
                return ServiceStatus(
                    name=service_name,
                    pid=pid,
                    status="stopped",
                    cpu_percent=0,
                    memory_mb=0,
                    uptime=None,
                    port=config.get("port"),
                    health_check_url=f"http://localhost:{config.get('port')}{config.get('health_path', '')}",
                    response_time=None
                )

            process = psutil.Process(pid)

            # 检查进程是否是Python进程
            if "python" not in process.name().lower():
                return ServiceStatus(
                    name=service_name,
                    pid=pid,
                    status="error",
                    cpu_percent=0,
                    memory_mb=0,
                    uptime=None,
                    port=config.get("port"),
                    health_check_url=f"http://localhost:{config.get('port')}{config.get('health_path', '')}",
                    response_time=None
                )

            return ServiceStatus(
                name=service_name,
                pid=pid,
                status="running",
                cpu_percent=process.cpu_percent(),
                memory_mb=process.memory_info().rss / (1024**2),
                uptime=time.time() - process.create_time(),
                port=config.get("port"),
                health_check_url=f"http://localhost:{config.get('port')}{config.get('health_path', '')}",
                response_time=None
            )

        except Exception as e:
            logger.error(f"检查服务{service_name}失败: {e}")
            return ServiceStatus(
                name=service_name,
                pid=None,
                status="error",
                cpu_percent=0,
                memory_mb=0,
                uptime=None,
                port=config.get("port"),
                health_check_url=f"http://localhost:{config.get('port')}{config.get('health_path', '')}",
                response_time=None
            )

    async def _check_service_health(self, service: ServiceStatus, config: dict[str, Any]) -> dict[str, Any]:
        """检查服务健康状态"""
        if not service.health_check_url:
            return {"healthy": False, "error": "无健康检查URL"}

        try:
            start_time = time.time()
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(service.health_check_url) as response:
                    response_time = time.time() - start_time
                    if response.status == 200:
                        return {
                            "healthy": True,
                            "response_time": response_time,
                            "status_code": response.status
                        }
                    else:
                        return {
                            "healthy": False,
                            "error": f"HTTP {response.status}",
                            "response_time": response_time
                        }
        except asyncio.TimeoutError:
            return {"healthy": False, "error": "请求超时"}
        except Exception as e:
            return {"healthy": False, "error": str(e)}

    async def _check_service_communication(self, services: list[ServiceStatus]):
        """检查服务间通信"""
        self.print_info("\n检查服务间通信...")

        running_services = [s for s in services if s.status == "running"]

        # 检查端口占用
        for service in running_services:
            if service.port:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('localhost', service.port))
                sock.close()

                if result == 0:
                    self.print_success(f"  {service.port}端口开放: {service.name}")
                else:
                    self.print_error(f"  {service.port}端口未开放: {service.name}")
                    self.analysis_results["issues"].append({
                        "type": "network",
                        "component": service.name,
                        "issue": f"端口{service.port}未开放",
                        "port": service.port
                    })

    async def analyze_databases(self) -> list[DatabaseStatus]:
        """分析数据库状态"""
        self.print_header("数据库连接池和缓存系统检查")

        databases = []

        # 检查PostgreSQL
        pg_status = await self._check_postgresql()
        databases.append(pg_status)

        # 检查Qdrant
        qdrant_status = await self._check_qdrant()
        databases.append(qdrant_status)

        # 检查Redis
        redis_status = await self._check_redis()
        databases.append(redis_status)

        return databases

    async def _check_postgresql(self) -> DatabaseStatus:
        """检查PostgreSQL状态"""
        try:
            import psycopg2
            config = self.database_configs["postgresql"]

            conn = psycopg2.connect(
                host=config["host"],
                port=config["port"],
                user=config["user"],
                password=config["password"],
                database="postgres"
            )

            cursor = conn.cursor()

            # 获取版本
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0].split(',')[0]

            # 获取连接数
            cursor.execute("SELECT count(*) FROM pg_stat_activity;")
            connections = cursor.fetchone()[0]

            # 获取数据库大小
            cursor.execute("SELECT pg_size_pretty(pg_database_size('athena_kg'));")
            size_str = cursor.fetchone()[0]
            size_gb = self._parse_size_to_gb(size_str)

            # 测试查询时间
            start_time = time.time()
            cursor.execute("SELECT 1;")
            cursor.fetchone()
            query_time = time.time() - start_time

            cursor.close()
            conn.close()

            self.print_success(f"PostgreSQL: {version}, 连接数:{connections}, 大小:{size_str}, 查询时间:{query_time:.3f}s")

            return DatabaseStatus(
                name="PostgreSQL",
                type="关系型数据库",
                status="running",
                version=version,
                connections=connections,
                size_gb=size_gb,
                query_time=query_time
            )

        except ImportError:
            self.print_warning("PostgreSQL: psycopg2未安装")
            return DatabaseStatus(
                name="PostgreSQL",
                type="关系型数据库",
                status="unknown",
                version="unknown",
                connections=0,
                size_gb=0,
                query_time=0
            )
        except Exception as e:
            self.print_error(f"PostgreSQL连接失败: {e}")
            return DatabaseStatus(
                name="PostgreSQL",
                type="关系型数据库",
                status="error",
                version="unknown",
                connections=0,
                size_gb=0,
                query_time=0
            )

    async def _check_qdrant(self) -> DatabaseStatus:
        """检查Qdrant状态"""
        try:
            config = self.database_configs["qdrant"]

            # 检查API
            response = requests.get(f"http://{config['host']}:{config['port']}{config['api_path']}", timeout=5)

            if response.status_code == 200:
                data = response.json()
                version = data.get('version', 'unknown')

                self.print_success(f"Qdrant: {version}, API响应正常")

                return DatabaseStatus(
                    name="Qdrant",
                    type="向量数据库",
                    status="running",
                    version=version,
                    connections=1,
                    size_gb=0,  # Qdrant不直接提供大小信息
                    query_time=0.001
                )
            else:
                self.print_error(f"Qdrant API响应异常: {response.status_code}")
                return DatabaseStatus(
                    name="Qdrant",
                    type="向量数据库",
                    status="error",
                    version="unknown",
                    connections=0,
                    size_gb=0,
                    query_time=0
                )

        except Exception as e:
            self.print_error(f"Qdrant连接失败: {e}")
            return DatabaseStatus(
                name="Qdrant",
                type="向量数据库",
                status="error",
                version="unknown",
                connections=0,
                size_gb=0,
                query_time=0
            )

    async def _check_redis(self) -> DatabaseStatus:
        """检查Redis状态"""
        try:
            import redis
            config = self.database_configs["redis"]

            r = redis.Redis(host=config['host'], port=config['port'], decode_responses=True)

            # 测试连接
            info = r.info()

            version = info.get('redis_version', 'unknown')
            connections = info.get('connected_clients', 0)
            used_memory = info.get('used_memory_human', '0B')
            size_gb = self._parse_size_to_gb(used_memory)

            self.print_success(f"Redis: {version}, 连接数:{connections}, 内存:{used_memory}")

            return DatabaseStatus(
                name="Redis",
                type="缓存数据库",
                status="running",
                version=version,
                connections=connections,
                size_gb=size_gb,
                query_time=0.0001
            )

        except ImportError:
            self.print_warning("Redis: redis-py未安装")
            return DatabaseStatus(
                name="Redis",
                type="缓存数据库",
                status="unknown",
                version="unknown",
                connections=0,
                size_gb=0,
                query_time=0
            )
        except Exception as e:
            self.print_error(f"Redis连接失败: {e}")
            return DatabaseStatus(
                name="Redis",
                type="缓存数据库",
                status="error",
                version="unknown",
                connections=0,
                size_gb=0,
                query_time=0
            )

    def _parse_size_to_gb(self, size_str: str) -> float:
        """解析大小字符串为GB"""
        try:
            size_str = size_str.strip().upper()
            if 'TB' in size_str:
                return float(size_str.replace('TB', '').strip()) * 1024
            elif 'GB' in size_str:
                return float(size_str.replace('GB', '').strip())
            elif 'MB' in size_str:
                return float(size_str.replace('MB', '').strip()) / 1024
            elif 'KB' in size_str:
                return float(size_str.replace('KB', '').strip()) / (1024**2)
            else:
                return float(size_str.replace('B', '').strip()) / (1024**3)
        except Exception as e:
            logger.debug(f"空except块已触发: {e}")
            return 0

    async def analyze_data_flow(self) -> dict[str, Any]:
        """分析数据流和服务链"""
        self.print_header("数据流和服务链检查")

        # 检查日志文件
        log_files = list(self.logs_dir.glob("*.log"))

        # 分析日志中的错误
        error_count = 0
        warning_count = 0
        recent_errors = []

        for log_file in log_files[-5:]:  # 只检查最近5个日志文件
            try:
                with open(log_file, encoding='utf-8') as f:
                    lines = f.readlines()[-100:]  # 只读取最后100行

                for line in lines:
                    if 'ERROR' in line.upper():
                        error_count += 1
                        if len(recent_errors) < 10:
                            recent_errors.append(line.strip())
                    elif 'WARNING' in line.upper():
                        warning_count += 1

            except Exception as e:
                logger.error(f"读取日志文件{log_file}失败: {e}")

        print(f"📊 日志统计: {len(log_files)}个日志文件")
        print(f"❌ 错误数: {error_count}")
        print(f"⚠️ 警告数: {warning_count}")

        if error_count > 10:
            self.print_warning("错误数量过多，需要关注！")
            self.analysis_results["warnings"].append({
                "type": "logs",
                "issue": "错误数量过多",
                "count": error_count
            })

        # 检查服务依赖关系
        dependencies = {
            "expert_rule_engine": [],
            "patent_rule_chain": ["expert_rule_engine"],
            "prior_art_analyzer": ["patent_rule_chain"],
            "llm_enhanced_judgment": ["prior_art_analyzer"],
            "xiaonuo_service": ["llm_enhanced_judgment", "nlp_service"],
            "nlp_service": []
        }

        # 验证依赖
        dependency_issues = []
        for service, deps in dependencies.items():
            for dep in deps:
                dep_status = self._get_service_status(dep)
                if dep_status != "running":
                    dependency_issues.append(f"{service}依赖的{dep}未运行")

        if dependency_issues:
            self.print_warning("发现服务依赖问题:")
            for issue in dependency_issues:
                self.print_warning(f"  - {issue}")

        return {
            "log_files_count": len(log_files),
            "error_count": error_count,
            "warning_count": warning_count,
            "recent_errors": recent_errors[:5],
            "dependency_issues": dependency_issues
        }

    def _get_service_status(self, service_name: str) -> str:
        """获取服务状态"""
        pid_file = self.logs_dir / f"{service_name}.pid"
        if not pid_file.exists():
            return "stopped"

        try:
            with open(pid_file) as f:
                pid = int(f.read().strip())
        except Exception as e:
            logger.debug(f"空except块已触发: {e}")
            return "error"

    async def check_configuration_consistency(self) -> dict[str, Any]:
        """检查配置一致性"""
        self.print_header("配置一致性检查")

        config_issues = []

        # 检查配置文件存在性
        required_configs = [
            "production/xiaonuo_enhanced_config.json",
            "identity/xiaonuo_pisces_princess.json"
        ]

        for config_path in required_configs:
            full_path = self.config_dir / config_path
            if full_path.exists():
                self.print_success(f"✓ 配置文件存在: {config_path}")
            else:
                self.print_error(f"✗ 配置文件缺失: {config_path}")
                config_issues.append(f"配置文件缺失: {config_path}")

        # 检查服务端口冲突
        port_usage = {}
        for service_name, config in self.service_configs.items():
            port = config.get("port")
            if port:
                if port in port_usage:
                    config_issues.append(f"端口冲突: {service_name}和{port_usage[port]}都使用端口{port}")
                else:
                    port_usage[port] = service_name

        # 检查环境变量
        required_env_vars = [
            "PYTHONPATH",
            "ATHENA_ENV"
        ]

        for env_var in required_env_vars:
            if env_var in os.environ:
                self.print_success(f"✓ 环境变量设置: {env_var}")
            else:
                self.print_warning(f"⚠ 环境变量未设置: {env_var}")

        return {
            "config_issues": config_issues,
            "port_conflicts": len([i for i in config_issues if "端口冲突" in i]),
            "missing_configs": len([i for i in config_issues if "配置文件缺失" in i])
        }

    def calculate_performance_score(self, metrics: SystemMetric, services: list[ServiceStatus],
                                  databases: list[DatabaseStatus]) -> float:
        """计算性能得分"""
        score = 100.0

        # CPU扣分
        if metrics.cpu_percent > 80:
            score -= (metrics.cpu_percent - 80) * 0.5

        # 内存扣分
        if metrics.memory_percent > 85:
            score -= (metrics.memory_percent - 85) * 0.5

        # 磁盘扣分
        if metrics.disk_percent > 90:
            score -= (metrics.disk_percent - 90) * 1.0

        # 服务扣分
        running_services = len([s for s in services if s.status == "running"])
        total_services = len(services)
        if total_services > 0:
            service_ratio = running_services / total_services
            score -= (1 - service_ratio) * 20

        # 数据库扣分
        running_dbs = len([d for d in databases if d.status == "running"])
        total_dbs = len(databases)
        if total_dbs > 0:
            db_ratio = running_dbs / total_dbs
            score -= (1 - db_ratio) * 15

        return max(0, score)

    async def generate_recommendations(self, report: AnalysisReport) -> list[str]:
        """生成优化建议"""
        recommendations = []

        # 基于系统指标的建议
        if report.system_metrics.cpu_percent > 80:
            recommendations.append("🔧 CPU使用率过高，建议优化计算密集型任务或增加CPU资源")

        if report.system_metrics.memory_percent > 85:
            recommendations.append("🔧 内存使用率过高，建议检查内存泄漏或增加内存配置")

        if report.system_metrics.disk_percent > 90:
            recommendations.append("🔧 磁盘空间不足，建议清理日志文件或扩展存储")

        # 基于服务状态的建议
        stopped_services = [s for s in report.services if s.status == "stopped"]
        if stopped_services:
            recommendations.append(f"🔧 以下服务已停止，建议检查并重启: {', '.join([s.name for s in stopped_services])}")

        # 基于数据库的建议
        slow_dbs = [d for d in report.databases if d.query_time > 0.1]
        if slow_dbs:
            recommendations.append(f"🔧 数据库查询缓慢，建议优化索引: {', '.join([d.name for d in slow_dbs])}")

        # 基于问题的建议
        for issue in report.issues:
            if issue["type"] == "network":
                recommendations.append(f"🔧 网络问题: {issue['issue']}")
            elif issue["type"] == "service_health":
                recommendations.append(f"🔧 服务健康检查失败: {issue['component']}")

        # 通用建议
        if report.performance_score < 70:
            recommendations.append("🔧 系统整体性能较低，建议进行全面的性能优化")

        if not recommendations:
            recommendations.append("✅ 系统运行良好，继续保持！")

        return recommendations

    async def run_comprehensive_analysis(self) -> AnalysisReport:
        """运行全面分析"""
        self.print_header("Athena工作平台生产环境全面分析")
        self.print_info("开始时间: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        # 1. 系统指标分析
        system_metrics = await self.analyze_system_metrics()

        # 2. 服务状态分析
        services = await self.analyze_services()

        # 3. 数据库状态分析
        databases = await self.analyze_databases()

        # 4. 数据流分析
        data_flow = await self.analyze_data_flow()

        # 5. 配置一致性检查
        config_consistency = await self.check_configuration_consistency()

        # 6. 计算性能得分
        performance_score = self.calculate_performance_score(system_metrics, services, databases)

        # 7. 生成建议
        report = AnalysisReport(
            analysis_time=datetime.now().isoformat(),
            system_metrics=system_metrics,
            services=services,
            databases=databases,
            issues=self.analysis_results["issues"],
            recommendations=[],
            performance_score=performance_score
        )

        report.recommendations = await self.generate_recommendations(report)

        # 8. 显示总结
        self.print_header("分析总结")
        print(f"📊 性能得分: {performance_score:.1f}/100")

        if performance_score >= 90:
            self.print_success("系统状态: 优秀")
        elif performance_score >= 70:
            self.print_warning("系统状态: 良好")
        else:
            self.print_error("系统状态: 需要优化")

        print("\n📝 主要发现:")
        print(f"  - 运行中的服务: {len([s for s in services if s.status == 'running'])}/{len(services)}")
        print(f"  - 运行中的数据库: {len([d for d in databases if d.status == 'running'])}/{len(databases)}")
        print(f"  - 发现的问题: {len(self.analysis_results['issues'])}")
        print(f"  - 警告数量: {len(self.analysis_results['warnings'])}")

        print("\n💡 优化建议:")
        for i, rec in enumerate(report.recommendations[:5], 1):
            print(f"  {i}. {rec}")

        # 保存报告
        report_file = self.logs_dir / f"system_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(report), f, indent=2, ensure_ascii=False)

        self.print_success(f"\n📄 详细报告已保存: {report_file}")

        return report

async def main():
    """主函数"""
    # 安装必要的依赖
    try:
        import aiohttp
    except ImportError:
        print("正在安装aiohttp...")
        subprocess.run([sys.executable, "-m", "pip", "install", "aiohttp"])

    # 创建分析器
    analyzer = SystemAnalyzer()

    # 运行分析
    report = await analyzer.run_comprehensive_analysis()

    # 返回退出码
    if report.performance_score >= 70:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
