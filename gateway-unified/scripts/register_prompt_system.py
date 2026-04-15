#!/usr/bin/env python3
"""
动态提示词系统Gateway注册脚本
Dynamic Prompt System Gateway Registration Script
"""

import json
import subprocess
import sys
from pathlib import Path


class GatewayClient:
    """Gateway客户端"""

    def __init__(self, gateway_url="http://localhost:8005"):
        self.gateway_url = gateway_url
        self.headers = {"Content-Type": "application/json"}

    def register_services(self, services):
        """批量注册服务"""
        url = f"{self.gateway_url}/api/services/batch_register"
        data = {"services": services}

        response = subprocess.run(
            ["curl", "-s", "-X", "POST", url, "-H", "Content-Type: application/json", "-d", json.dumps(data)],
            capture_output=True,
            text=True
        )

        return json.loads(response.stdout) if response.returncode == 0 else None

    def create_route(self, route_config):
        """创建路由"""
        url = f"{self.gateway_url}/api/routes"

        response = subprocess.run(
            ["curl", "-s", "-X", "POST", url, "-H", "Content-Type: application/json", "-d", json.dumps(route_config)],
            capture_output=True,
            text=True
        )

        return json.loads(response.stdout) if response.returncode == 0 else None

    def check_health(self):
        """检查Gateway健康状态"""
        response = subprocess.run(
            ["curl", "-s", f"{self.gateway_url}/health"],
            capture_output=True,
            text=True
        )

        return json.loads(response.stdout) if response.returncode == 0 else None


def load_config(config_path):
    """加载配置文件"""
    with open(config_path, encoding='utf-8') as f:
        import yaml
        return yaml.safe_load(f)


def register_prompt_system():
    """注册动态提示词系统到Gateway"""

    print("=" * 60)
    print("  动态提示词系统 - Gateway注册")
    print("=" * 60)
    print()

    # 初始化客户端
    client = GatewayClient()

    # 检查Gateway健康状态
    print("1. 检查Gateway状态...")
    health = client.check_health()
    if not health or health.get("data", {}).get("status") != "UP":
        print("   ❌ Gateway未运行或状态异常")
        print("   请先启动Gateway: cd gateway-unified && ./bin/gateway-unified")
        return False
    print("   ✅ Gateway运行正常")
    print()

    # 加载配置
    config_path = Path(__file__).parent.parent / "configs" / "prompt-system-service.yaml"
    print(f"2. 加载配置: {config_path}")
    try:
        config = load_config(config_path)
        print("   ✅ 配置加载成功")
    except Exception as e:
        print(f"   ❌ 配置加载失败: {e}")
        return False
    print()

    # 注册服务
    print("3. 注册服务实例...")
    services = config.get("services", [])
    if not services:
        print("   ❌ 配置中没有服务定义")
        return False

    result = client.register_services(services)
    if result and result.get("success"):
        service = services[0]
        print(f"   ✅ 服务注册成功: {service['name']} -> {service['host']}:{service['port']}")
    else:
        print(f"   ❌ 服务注册失败: {result}")
        return False
    print()

    # 创建路由
    print("4. 创建路由规则...")
    routes = config.get("routes", [])
    created_count = 0
    failed_count = 0

    for route in routes:
        result = client.create_route(route)
        if result and result.get("success"):
            created_count += 1
            print(f"   ✅ {route['path']}")
        else:
            failed_count += 1
            print(f"   ❌ {route['path']}: {result}")

    print()
    print(f"   路由创建完成: {created_count} 成功, {failed_count} 失败")
    print()

    # 设置依赖关系
    if "dependencies" in config:
        print("5. 设置服务依赖...")
        for dep in config.get("dependencies", []):
            url = f"{client.gateway_url}/api/dependencies"
            data = {
                "service": dep["service"],
                "depends_on": dep["depends_on"]
            }
            response = subprocess.run(
                ["curl", "-s", "-X", "POST", url, "-H", "Content-Type: application/json", "-d", json.dumps(data)],
                capture_output=True,
                text=True
            )
            result = json.loads(response.stdout) if response.returncode == 0 else None
            if result and result.get("success"):
                print(f"   ✅ {dep['service']} 依赖: {', '.join(dep['depends_on'])}")
        print()

    # 显示服务信息
    print("=" * 60)
    print("  注册完成")
    print("=" * 60)
    print()
    service = services[0]
    print(f"服务名称: {service['name']}")
    print(f"服务地址: http://{service['host']}:{service['port']}")
    print("Gateway路径: /api/prompt-system/*")
    print()
    print("📋 主要端点:")
    print("  - 健康检查: GET  /api/prompt-system/health")
    print("  - 场景识别: POST /api/prompt-system/scenario/identify")
    print("  - 规则检索: POST /api/prompt-system/rules/retrieve")
    print("  - 能力调用: POST /api/prompt-system/capabilities/invoke")
    print("  - 提示词生成: POST /api/prompt-system/prompt/generate")
    print("  - 能力列表: GET  /api/prompt-system/capabilities/list")
    print()
    print("📖 API文档: http://localhost:8002/docs")
    print()
    print("=" * 60)

    return True


if __name__ == "__main__":
    try:
        import yaml
    except ImportError:
        print("❌ 缺少依赖: pip install pyyaml")
        sys.exit(1)

    success = register_prompt_system()
    sys.exit(0 if success else 1)
