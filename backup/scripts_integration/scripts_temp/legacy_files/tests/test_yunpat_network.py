#!/usr/bin/env python3
"""
YunPat网络连接测试脚本
Test script for YunPat network connectivity
"""

import requests
import socket
import json
import time
from typing import Dict, List, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class YunPatNetworkTester:
    def __init__(self):
        self.services = {
            "YunPat Web": {"host": "localhost", "port": 8020},
            "YunPat API": {"host": "localhost", "port": 8087},
            "AI模型服务": {"host": "localhost", "port": 8082},
            "Athena搜索": {"host": "localhost", "port": 8008},
            "Qdrant": {"host": "localhost", "port": 6333}
        }

        self.local_ip = self.get_local_ip()
        logger.info(f"本机局域网IP: {self.local_ip}")

    def get_local_ip(self):
        """获取本机局域网IP"""
        try:
            # 连接到外部地址获取本地IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "192.168.1.100"  # 默认值

    def test_service(self, service_name: str, config: Dict[str, Any],
                     host_override: str = None) -> Dict[str, Any]:
        """测试单个服务"""
        host = host_override or config["host"]
        port = config["port"]

        result = {
            "service": service_name,
            "host": host,
            "port": port,
            "status": "unknown",
            "response_time": None,
            "error": None
        }

        try:
            # 测试端口连通性
            start_time = time.time()

            # 测试HTTP服务
            if service_name == "YunPat Web":
                url = f"http://{host}:{port}/docs"
            elif service_name == "YunPat API":
                url = f"http://{host}:{port}/"
            elif service_name == "AI模型服务":
                url = f"http://{host}:{port}/"
            elif service_name == "Athena搜索":
                url = f"http://{host}:{port}/"
            elif service_name == "Qdrant":
                url = f"http://{host}:{port}/health"
            else:
                url = f"http://{host}:{port}/"

            response = requests.get(url, timeout=5)
            response_time = time.time() - start_time

            result["status"] = "online" if response.status_code == 200 else "error"
            result["response_time"] = round(response_time * 1000, 2)  # 毫秒

            # 获取服务信息
            if result["status"] == "online":
                try:
                    data = response.json() if response.content else {}
                    result["info"] = data
                except:
                    result["info"] = response.text[:200] + "..." if len(response.text) > 200 else response.text

        except requests.exceptions.ConnectionError:
            result["status"] = "offline"
            result["error"] = "Connection refused"
        except requests.exceptions.Timeout:
            result["status"] = "timeout"
            result["error"] = "Request timeout"
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)

        return result

    def run_tests(self):
        """运行所有测试"""
        print("="*60)
        print("🔍 YunPat网络连接测试")
        print("="*60)
        print()

        # 测试本机服务
        print("1️⃣ 测试本机服务")
        print("-" * 40)
        local_results = {}

        for service_name, config in self.services.items():
            result = self.test_service(service_name, config)
            local_results[service_name] = result

            status_emoji = "✅" if result["status"] == "online" else "❌"
            print(f"{status_emoji} {service_name}:")
            print(f"   URL: http://{config['host']}:{config['port']}")
            print(f"   状态: {result['status']}")
            if result["response_time"]:
                print(f"   响应时间: {result['response_time']}ms")
            if result["error"]:
                print(f"   错误: {result['error']}")
            print()

        # 测试局域网访问
        print("2️⃣ 测试局域网访问")
        print("-" * 40)
        print(f"本机IP: {self.local_ip}")
        print("请确保其他设备在同一局域网内（192.168.x.x）")
        print()

        lan_results = {}

        # 只测试主要服务
        main_services = {
            "YunPat Web": {"host": self.local_ip, "port": 8020},
            "YunPat API": {"host": self.local_ip, "port": 8087}
        }

        for service_name, config in main_services.items():
            result = self.test_service(service_name, config)
            lan_results[service_name] = result

            status_emoji = "✅" if result["status"] == "online" else "❌"
            print(f"{status_emoji} {service_name} (局域网):")
            print(f"   URL: http://{config['host']}:{config['port']}")
            print(f"   状态: {result['status']}")
            print()

        # 测试API功能
        print("3️⃣ 测试YunPat API功能")
        print("-" * 40)

        try:
            # 测试云熙信息接口
            response = requests.get(f"http://localhost:8087/api/v1/info", timeout=5)
            if response.status_code == 200:
                info = response.json()
                print("✅ 云熙信息接口:")
                print(f"   姓名: {info.get('name')}")
                print(f"   年龄: {info.get('age')}")
                print(f"   特点: {', '.join(info.get('personality', []))}")
                print()

            # 测试专利搜索接口
            search_data = {
                "query": "人工智能",
                "limit": 5
            }
            response = requests.post(
                f"http://localhost:8087/api/v1/patent/search",
                json=search_data,
                timeout=5
            )
            if response.status_code == 200:
                result = response.json()
                print("✅ 专利搜索接口:")
                print(f"   查询: {result.get('query')}")
                print(f"   结果数: {result.get('total')}")
                print(f"   消息: {result.get('message')}")
                print()

        except Exception as e:
            print(f"❌ API功能测试失败: {e}")
            print()

        # 生成测试报告
        self.generate_report(local_results, lan_results)

        # 提供客户端连接指南
        self.print_client_guide()

    def generate_report(self, local_results: Dict, lan_results: Dict):
        """生成测试报告"""
        report = {
            "test_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "local_ip": self.local_ip,
            "local_services": local_results,
            "lan_services": lan_results,
            "summary": {
                "total_services": len(self.services),
                "online_local": sum(1 for r in local_results.values() if r["status"] == "online"),
                "online_lan": sum(1 for r in lan_results.values() if r["status"] == "online")
            }
        }

        # 保存报告
        report_file = "yunpat_network_test_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print("📊 测试报告已生成")
        print(f"   文件: {report_file}")
        print()

    def print_client_guide(self):
        """打印客户端连接指南"""
        print("4️⃣ 客户端连接指南")
        print("-" * 40)
        print()

        if self.local_ip and any(r["status"] == "online" for r in self.services.values()):
            print("🌐 局域网访问地址:")
            print(f"   YunPat Web界面: http://{self.local_ip}:8020/docs")
            print(f"   YunPat API接口: http://{self.local_ip}:8087")
            print()
            print("📋 客户端使用说明:")
            print("   1. 确保客户端设备与服务器在同一局域网")
            print("   2. 使用上述地址访问YunPat服务")
            print("   3. API文档: http://{self.local_ip}:8020/docs")
            print()
            print("🔧 API示例:")
            print(f"   # 获取云熙信息")
            print(f"   curl http://{self.local_ip}:8087/api/v1/info")
            print()
            print(f"   # 搜索专利")
            print(f"   curl -X POST http://{self.local_ip}:8087/api/v1/patent/search \\")
            print(f"        -H 'Content-Type: application/json' \\")
            print(f"        -d '{{\"query\": \"专利\"}}'")
            print()
            print("📝 测试方法:")
            print("   1. 在同局域网的其他设备浏览器中访问Web界面")
            print("   2. 使用Postman或curl测试API接口")
            print("   3. 检查防火墙设置（确保端口开放）")
        else:
            print("⚠️ 服务未完全启动，请检查服务状态")


def main():
    """主函数"""
    tester = YunPatNetworkTester()
    tester.run_tests()


if __name__ == "__main__":
    main()