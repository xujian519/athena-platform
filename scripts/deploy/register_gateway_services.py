#!/usr/bin/env python3
"""
Athena Gateway 服务注册脚本
自动将所有后端服务注册到统一网关
"""

import sys

import requests

# Gateway配置
GATEWAY_URL = "http://localhost:8005"
VERIFY_SSL = False  # 不需要SSL验证

# 后端服务定义
BACKEND_SERVICES = [
    {
        "name": "knowledge-graph",
        "host": "localhost",
        "port": 8100,
        "weight": 100,
        "metadata": {
            "service_type": "knowledge-graph",
            "description": "知识图谱服务 (Neo4j)",
            "health_endpoint": "/health"
        }
    },
    {
        "name": "qdrant-vector",
        "host": "localhost",
        "port": 16333,
        "weight": 100,
        "metadata": {
            "service_type": "vector-db",
            "description": "Qdrant向量数据库",
            "health_endpoint": "/"
        }
    },
    {
        "name": "athena-postgres",
        "host": "localhost",
        "port": 15432,
        "weight": 100,
        "metadata": {
            "service_type": "database",
            "description": "PostgreSQL数据库",
            "database": "athena"
        }
    },
    {
        "name": "athena-redis",
        "host": "localhost",
        "port": 16379,
        "weight": 100,
        "metadata": {
            "service_type": "cache",
            "description": "Redis缓存"
        }
    },
    {
        "name": "local-search-engine",
        "host": "localhost",
        "port": 3003,
        "weight": 100,
        "metadata": {
            "service_type": "search",
            "description": "本地搜索引擎 (SearXNG+Firecrawl)",
            "health_endpoint": "/health"
        }
    },
    {
        "name": "mineru-parser",
        "host": "localhost",
        "port": 7860,
        "weight": 100,
        "metadata": {
            "service_type": "document-parser",
            "description": "MinerU文档解析服务",
            "health_endpoint": "/docs"
        }
    }
]

# 路由规则定义
ROUTE_RULES = [
    {
        "name": "kg-query-route",
        "path": "/api/v1/kg/*",
        "target_service": "knowledge-graph",
        "strip_path": True,
        "methods": ["GET", "POST"],
        "plugins": {
            "rate_limit": {
                "enabled": True,
                "requests_per_second": 100
            },
            "timeout": {
                "enabled": True,
                "duration_seconds": 30
            }
        }
    },
    {
        "name": "vector-search-route",
        "path": "/api/v1/vector/*",
        "target_service": "qdrant-vector",
        "strip_path": False,
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "plugins": {
            "rate_limit": {
                "enabled": True,
                "requests_per_second": 50
            }
        }
    },
    {
        "name": "legal-search-route",
        "path": "/api/v1/legal/*",
        "target_service": "knowledge-graph",
        "strip_path": True,
        "methods": ["GET", "POST"],
        "plugins": {
            "rate_limit": {
                "enabled": True,
                "requests_per_second": 100
            }
        }
    },
    {
        "name": "search-route",
        "path": "/api/search",
        "target_service": "local-search-engine",
        "strip_path": False,
        "methods": ["GET", "POST"],
        "plugins": {
            "timeout": {
                "enabled": True,
                "duration_seconds": 60
            }
        }
    },
    {
        "name": "tools-route",
        "path": "/api/v1/tools/*",
        "target_service": "knowledge-graph",
        "strip_path": True,
        "methods": ["GET", "POST"],
        "plugins": {
            "rate_limit": {
                "enabled": True,
                "requests_per_second": 20
            }
        }
    }
]


def register_services(services: list[dict]) -> bool:
    """批量注册服务实例"""
    url = f"{GATEWAY_URL}/api/services/batch_register"
    headers = {"Content-Type": "application/json"}

    print(f"📝 正在注册 {len(services)} 个服务实例...")
    print(f"   URL: {url}")

    try:
        response = requests.post(
            url,
            json={"services": services},
            headers=headers,
            verify=VERIFY_SSL,
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            print("✅ 服务注册成功！")
            print(f"   已注册: {result.get('data', {}).get('registered', 0)} 个服务")
            return True
        else:
            print("❌ 服务注册失败！")
            print(f"   状态码: {response.status_code}")
            print(f"   响应: {response.text}")
            return False

    except Exception as e:
        print(f"❌ 服务注册异常: {e}")
        return False


def register_routes(routes: list[dict]) -> bool:
    """注册路由规则"""
    url = f"{GATEWAY_URL}/api/routes"
    headers = {"Content-Type": "application/json"}

    print(f"\n🛣️  正在注册 {len(routes)} 条路由规则...")

    success_count = 0
    for route in routes:
        try:
            response = requests.post(
                url,
                json=route,
                headers=headers,
                verify=VERIFY_SSL,
                timeout=10
            )

            if response.status_code in [200, 201]:
                print(f"   ✅ {route['name']}: {route['path']} → {route['target_service']}")
                success_count += 1
            else:
                print(f"   ❌ {route['name']}: {response.status_code} - {response.text}")

        except Exception as e:
            print(f"   ❌ {route['name']}: {e}")

    print(f"\n路由注册完成: {success_count}/{len(routes)} 成功")
    return success_count == len(routes)


def verify_registration():
    """验证注册结果"""
    print("\n🔍 验证注册结果...")

    # 检查服务实例
    try:
        response = requests.get(
            f"{GATEWAY_URL}/api/services/instances",
            verify=VERIFY_SSL,
            timeout=5
        )

        if response.status_code == 200:
            result = response.json()
            count = result.get('data', {}).get('count', 0)
            print(f"   ✅ 已注册服务实例: {count} 个")

            if count > 0:
                services = result.get('data', {}).get('data', [])
                for svc in services:
                    print(f"      - {svc['name']} ({svc['host']}:{svc['port']})")
        else:
            print(f"   ❌ 获取服务列表失败: {response.status_code}")

    except Exception as e:
        print(f"   ❌ 验证服务实例异常: {e}")

    # 检查路由规则
    try:
        response = requests.get(
            f"{GATEWAY_URL}/api/routes",
            verify=VERIFY_SSL,
            timeout=5
        )

        if response.status_code == 200:
            result = response.json()
            routes = result.get('data', [])
            print(f"   ✅ 已注册路由规则: {len(routes)} 条")

            for route in routes:
                print(f"      - {route.get('name', 'unnamed')}: {route.get('path', 'N/A')}")
        else:
            print(f"   ⚠️  获取路由列表失败: {response.status_code}")

    except Exception as e:
        print(f"   ⚠️  验证路由规则异常: {e}")


def main():
    """主函数"""
    print("=" * 70)
    print("Athena Gateway 服务注册脚本")
    print("=" * 70)

    # 检查Gateway是否运行
    try:
        response = requests.get(
            f"{GATEWAY_URL}/health",
            verify=VERIFY_SSL,
            timeout=5
        )
        if response.status_code == 200:
            print("✅ Gateway运行正常 (端口8005)")
        else:
            print(f"⚠️  Gateway状态异常: {response.status_code}")
    except Exception as e:
        print(f"❌ 无法连接到Gateway: {e}")
        print("   请确保Gateway正在运行: sudo systemctl start athena-gateway")
        sys.exit(1)

    # 注册服务
    success_services = register_services(BACKEND_SERVICES)

    # 注册路由
    success_routes = register_routes(ROUTE_RULES)

    # 验证结果
    verify_registration()

    # 总结
    print("\n" + "=" * 70)
    if success_services and success_routes:
        print("✅ 服务和路由注册完成！")
        print("=" * 70)
        sys.exit(0)
    else:
        print("⚠️  注册过程存在问题，请检查上述错误信息")
        print("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    main()
