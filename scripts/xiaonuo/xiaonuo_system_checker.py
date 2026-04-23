#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小诺系统状态检查器
Xiaonuo System Status Checker

检查平台所有组件的健康状态，诊断启动问题

作者: 小诺·双鱼座
创建时间: 2025-12-16
版本: v1.0.0
"""

import asyncio
import json
import logging
import socket
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class XiaonuoSystemChecker:
    """小诺系统状态检查器"""

    def __init__(self):
        self.name = "小诺系统检查器"
        self.version = "v1.0.0"

        # 需要检查的服务
        self.services = {
            "PostgreSQL": {"port": 5432, "type": "database", "essential": True},
            "Redis": {"port": 6379, "type": "cache", "essential": True},
            "Qdrant": {"port": 6333, "type": "vector_db", "essential": True},
            "Neo4j": {"port": 7474, "type": "graph_db", "essential": True},
            "Neo4j-Bolt": {"port": 7687, "type": "graph_db", "essential": False},
            "Elasticsearch": {"port": 9200, "type": "search", "essential": False},
            "小诺记忆系统": {"port": 8083, "type": "service", "essential": True},
            "小诺控制中心": {"port": 8005, "type": "service", "essential": True},
            "小娜智能体": {"port": 8001, "type": "service", "essential": False},
            "云熙系统": {"port": 8087, "type": "service", "essential": False},
            "Nginx": {"port": 80, "type": "proxy", "essential": False}
        }

        # 检查结果
        self.check_results = {}

    async def check_all_services(self):
        """检查所有服务状态"""
        print("\n" + "="*80)
        print("🔍" + " "*28 + "小诺系统状态检查器" + " "*28 + "🔍")
        print("="*80)
        print(f"💖 检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔢 版本: {self.version}")
        print("="*80)

        # 检查Docker状态
        await self._check_docker_status()

        # 检查各个服务
        for service_name, service_info in self.services.items():
            await self._check_service(service_name, service_info)

        # 检查系统资源
        await self._check_system_resources()

        # 生成健康报告
        self._generate_health_report()

    async def _check_docker_status(self):
        """检查Docker状态"""
        print("\n🐳 Docker状态检查")
        print("-" * 40)

        try:
            # 检查Docker是否运行
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                print(f"✅ Docker版本: {result.stdout.strip()}")

                # 检查Docker服务状态
                result = subprocess.run(
                    ["docker", "info"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if result.returncode == 0:
                    print("✅ Docker服务运行正常")

                    # 统计运行中的容器
                    result = subprocess.run(
                        ["docker", "ps", "--format", "{{.Names}}"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )

                    if result.returncode == 0:
                        containers = result.stdout.strip().split('\n') if result.stdout.strip() else []
                        print(f"📦 运行中容器: {len([c for c in containers if c])}个")

                        # 检查Athena相关容器
                        athena_containers = [c for c in containers if 'athena' in c.lower() or 'xiaonuo' in c.lower()]
                        if athena_containers:
                            print(f"🌸 Athena相关容器: {len(athena_containers)}个")
                            for container in athena_containers[:5]:  # 只显示前5个
                                print(f"   - {container}")
                            if len(athena_containers) > 5:
                                print(f"   ... 还有{len(athena_containers) - 5}个容器")
                else:
                    print("❌ Docker服务异常")
            else:
                print("❌ Docker未安装或无法访问")

        except subprocess.TimeoutExpired:
            print("⚠️  Docker命令超时")
        except Exception as e:
            print(f"❌ Docker检查失败: {e}")

    async def _check_service(self, service_name: str, service_info: Dict):
        """检查单个服务"""
        port = service_info["port"]
        service_type = service_info["type"]
        essential = service_info["essential"]

        print(f"\n🔍 检查 {service_name} (端口: {port})")
        print("-" * 40)

        # 端口检查
        port_status = await self._check_port(port)

        # 服务类型特定检查
        detailed_status = await self._check_service_by_type(service_name, service_type)

        # 记录结果
        self.check_results[service_name] = {
            "port": port,
            "port_status": port_status,
            "detailed_status": detailed_status,
            "type": service_type,
            "essential": essential,
            "status": "healthy" if port_status and detailed_status.get("healthy", False) else "unhealthy"
        }

        # 显示结果
        status_icon = "✅" if port_status else "❌"
        essential_mark = " [核心]" if essential else ""
        print(f"{status_icon} {service_name}{essential_mark}: {'正常' if port_status else '异常'}")

        if detailed_status:
            for key, value in detailed_status.items():
                if key != "healthy":
                    print(f"   📊 {key}: {value}")

    async def _check_port(self, port: int, timeout: int = 3) -> bool:
        """检查端口是否可访问"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            return result == 0
        except Exception:
            return False

    async def _check_service_by_type(self, service_name: str, service_type: str) -> Dict:
        """根据服务类型进行详细检查"""
        result = {"healthy": False}

        try:
            if service_type == "database":
                result = await self._check_database_service(service_name)
            elif service_type == "cache":
                result = await self._check_redis_service(service_name)
            elif service_type == "vector_db":
                result = await self._check_qdrant_service(service_name)
            elif service_type == "graph_db":
                result = await self._check_neo4j_service(service_name)
            elif service_type == "search":
                result = await self._check_elasticsearch_service(service_name)
            elif service_type == "service":
                result = await self._check_http_service(service_name)
            elif service_type == "proxy":
                result = await self._check_proxy_service(service_name)
        except Exception as e:
            result["error"] = str(e)

        return result

    async def _check_database_service(self, service_name: str) -> Dict:
        """检查数据库服务"""
        result = {"healthy": False}

        if "PostgreSQL" in service_name:
            try:
                # 尝试连接PostgreSQL
                import psycopg2
                conn = psycopg2.connect(
                    host="localhost",
                    port=5432,
                    database="athena",
                    user="athena",
                    password="xujian519_athena",
                    connect_timeout=5
                )

                # 执行简单查询
                cursor = conn.cursor()
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]

                result = {
                    "healthy": True,
                    "version": version.split(',')[0],
                    "database": "athena"
                }

                conn.close()

            except ImportError:
                result["error"] = "psycopg2未安装"
            except Exception as e:
                result["error"] = str(e)

        return result

    async def _check_redis_service(self, service_name: str) -> Dict:
        """检查Redis服务"""
        result = {"healthy": False}

        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, decode_responses=True, socket_timeout=5)

            # 测试连接
            info = r.info()

            result = {
                "healthy": True,
                "version": info.get('redis_version', 'unknown'),
                "used_memory": f"{info.get('used_memory_human', 'unknown')}",
                "connected_clients": info.get('connected_clients', 'unknown')
            }

        except ImportError:
            result["error"] = "redis未安装"
        except Exception as e:
            result["error"] = str(e)

        return result

    async def _check_qdrant_service(self, service_name: str) -> Dict:
        """检查Qdrant服务"""
        result = {"healthy": False}

        try:
            import requests
            response = requests.get(f"http://localhost:6333/health", timeout=5)

            if response.status_code == 200:
                data = response.json()
                result = {
                    "healthy": True,
                    "version": data.get("version", "unknown"),
                    "commit": data.get("commit", "unknown")[:8] if data.get("commit") else "unknown"
                }

        except ImportError:
            result["error"] = "requests未安装"
        except Exception as e:
            result["error"] = str(e)

        return result

    async def _check_neo4j_service(self, service_name: str) -> Dict:
        """检查Neo4j服务"""
        result = {"healthy": False}

        try:
            if "Bolt" in service_name:
                # Bolt协议检查
                from neo4j import GraphDatabase

                driver = GraphDatabase.driver(
                    "bolt://localhost:7687",
                    auth=("neo4j", "xiaonuo_neo4j_2025"),
                    max_connection_lifetime=30,
                    connection_timeout=5
                )

                with driver.session() as session:
                    result_query = session.run("RETURN 1 as test")
                    record = result_query.single()

                    if record["test"] == 1:
                        result["healthy"] = True

                driver.close()
                result["protocol"] = "Bolt"
            else:
                # HTTP检查
                import requests
                response = requests.get("http://localhost:7474", timeout=5)

                if response.status_code == 200:
                    result = {
                        "healthy": True,
                        "protocol": "HTTP",
                        "web_interface": "available"
                    }

        except ImportError:
            result["error"] = "neo4j或requests未安装"
        except Exception as e:
            result["error"] = str(e)

        return result

    async def _check_elasticsearch_service(self, service_name: str) -> Dict:
        """检查Elasticsearch服务"""
        result = {"healthy": False}

        try:
            import requests
            response = requests.get("http://localhost:9200/_cluster/health", timeout=5)

            if response.status_code == 200:
                data = response.json()
                result = {
                    "healthy": True,
                    "status": data.get("status", "unknown"),
                    "nodes": data.get("number_of_nodes", "unknown")
                }

        except ImportError:
            result["error"] = "requests未安装"
        except Exception as e:
            result["error"] = str(e)

        return result

    async def _check_http_service(self, service_name: str) -> Dict:
        """检查HTTP服务"""
        result = {"healthy": False}

        # 获取服务端口
        port = None
        for s_name, s_info in self.services.items():
            if s_name == service_name:
                port = s_info["port"]
                break

        if not port:
            result["error"] = "找不到服务端口信息"
            return result

        try:
            import requests

            # 尝试健康检查
            health_urls = [
                f"http://localhost:{port}/health",
                f"http://localhost:{port}/api/v1/status",
                f"http://localhost:{port}/",
                f"http://localhost:{port}/ping"
            ]

            for url in health_urls:
                try:
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        result["healthy"] = True
                        result["health_url"] = url
                        if response.headers.get("content-type", "").startswith("application/json"):
                            try:
                                data = response.json()
                                result.update(data)
                            except:
                                pass
                        break
                except:
                    continue

            if not result["healthy"]:
                result["error"] = "健康检查失败"

        except ImportError:
            result["error"] = "requests未安装"
        except Exception as e:
            result["error"] = str(e)

        return result

    async def _check_proxy_service(self, service_name: str) -> Dict:
        """检查代理服务"""
        result = {"healthy": False}

        try:
            import requests
            response = requests.get("http://localhost:80", timeout=5)

            if response.status_code in [200, 404, 502]:  # 各种可能的响应
                result = {
                    "healthy": True,
                    "status_code": response.status_code,
                    "server": response.headers.get("server", "unknown")
                }

        except Exception as e:
            result["error"] = str(e)

        return result

    async def _check_system_resources(self):
        """检查系统资源"""
        print("\n📊 系统资源检查")
        print("-" * 40)

        try:
            # 检查CPU和内存
            try:
                import psutil

                # CPU信息
                cpu_percent = psutil.cpu_percent(interval=1)
                cpu_count = psutil.cpu_count()

                # 内存信息
                memory = psutil.virtual_memory()

                # 磁盘信息
                disk = psutil.disk_usage('/')

                print(f"💻 CPU使用率: {cpu_percent}% ({cpu_count}核心)")
                print(f"🧠 内存使用: {memory.percent}% ({memory.used//1024//1024}MB/{memory.total//1024//1024}MB)")
                print(f"💾 磁盘使用: {disk.percent}% ({disk.free//1024//1024//1024}GB可用)")

                # 网络连接数
                connections = len(psutil.net_connections())
                print(f"🌐 网络连接: {connections}个")

            except ImportError:
                print("⚠️  psutil未安装，无法检查系统资源")

            # 检查Docker资源使用
            try:
                result = subprocess.run(
                    ["docker", "stats", "--no-stream", "--format", "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if result.returncode == 0 and result.stdout.strip():
                    print(f"\n🐳 Docker容器资源使用:")
                    lines = result.stdout.strip().split('\n')
                    for line in lines[:10]:  # 只显示前10个
                        print(f"   {line}")
                    if len(lines) > 10:
                        print(f"   ... 还有{len(lines) - 10}个容器")

            except Exception as e:
                print(f"⚠️  Docker资源检查失败: {e}")

        except Exception as e:
            print(f"❌ 系统资源检查失败: {e}")

    def _generate_health_report(self) -> Any:
        """生成健康报告"""
        print("\n" + "="*80)
        print("📋" + " "*28 + "系统健康报告" + " "*28 + "📋")
        print("="*80)

        # 统计信息
        total_services = len(self.services)
        healthy_services = len([s for s in self.check_results.values() if s["status"] == "healthy"])
        essential_services = len([s for s in self.services.values() if s["essential"]])
        healthy_essential = len([s for s in self.check_results.values() if s["essential"] and s["status"] == "healthy"])

        print(f"📊 服务状态总览:")
        print(f"   总服务数: {total_services}")
        print(f"   健康服务: {healthy_services} ({healthy_services/total_services*100:.1f}%)")
        print(f"   核心服务: {healthy_essential}/{essential_services}")

        # 问题服务列表
        problematic_services = [name for name, status in self.check_results.items() if status["status"] != "healthy"]

        if problematic_services:
            print(f"\n❌ 问题服务 ({len(problematic_services)}个):")
            for service_name in problematic_services:
                service_info = self.check_results[service_name]
                error_info = service_info.get("detailed_status", {}).get("error", "连接失败")
                print(f"   - {service_name}: {error_info}")
        else:
            print(f"\n✅ 所有服务运行正常!")

        # 建议和修复提示
        print(f"\n💡 修复建议:")

        if healthy_essential < essential_services:
            print("   1. 核心服务异常，建议检查Docker服务状态")
            print("   2. 尝试重新启动异常的核心服务")
            print("   3. 检查端口是否被其他程序占用")

        if healthy_services < total_services and healthy_essential == essential_services:
            print("   1. 核心服务正常，部分可选服务异常")
            print("   2. 可选择性修复或忽略非核心服务")

        if healthy_services == total_services:
            print("   🎉 系统状态完美！可以开始使用小诺平台！")

        # 生成JSON报告
        self._save_health_report()

        print("\n" + "="*80)

    def _save_health_report(self) -> Any:
        """保存健康报告"""
        try:
            report_data = {
                "timestamp": datetime.now().isoformat(),
                "checker": {
                    "name": self.name,
                    "version": self.version
                },
                "summary": {
                    "total_services": len(self.services),
                    "healthy_services": len([s for s in self.check_results.values() if s["status"] == "healthy"]),
                    "essential_services": len([s for s in self.services.values() if s["essential"]])
                },
                "services": self.check_results
            }

            # 保存报告
            reports_dir = Path("reports")
            reports_dir.mkdir(exist_ok=True)

            report_file = reports_dir / f"xiaonuo_health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)

            print(f"📄 详细报告已保存: {report_file}")

        except Exception as e:
            print(f"⚠️  保存报告失败: {e}")

async def main():
    """主程序"""
    checker = XiaonuoSystemChecker()

    # 检查命令行参数
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command in ["检查", "check", "status", "健康检查"]:
            await checker.check_all_services()
        elif command in ["快速检查", "quick"]:
            # 只检查核心服务
            essential_services = {k: v for k, v in checker.services.items() if v["essential"]}
            checker.services = essential_services
            await checker.check_all_services()
        else:
            print("🔍 小诺系统检查器")
            print("用法:")
            print("  python xiaonuo_system_checker.py 检查")
            print("  python xiaonuo_system_checker.py 快速检查")
    else:
        # 默认完整检查
        await checker.check_all_services()

if __name__ == "__main__":
    asyncio.run(main())