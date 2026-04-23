#!/usr/bin/env python3
"""
智能体和工具服务网关注册脚本
Register Agent and Tool Services to Gateway

将以下服务注册到Athena统一网关：
- 工具注册表API服务 (Port 8021)
- 小娜智能体API服务 (Port 8023)
- 小诺智能体API服务 (Port 8024)

用法:
    python register_agent_and_tool_services.py [--host HOST] [--port PORT]

作者: Athena平台团队
版本: 1.0.0
"""

import argparse
import logging
import sys

import requests

# =============================================================================
# 配置
# =============================================================================

GATEWAY_HOST = "localhost"
GATEWAY_PORT = 8005
GATEWAY_BASE_URL = f"http://{GATEWAY_HOST}:{GATEWAY_PORT}"

# 服务配置
SERVICES_TO_REGISTER = [
    {
        "name": "tool-registry-api",
        "host": "localhost",
        "port": 8021,
        "metadata": {
            "version": "1.0.0",
            "description": "统一工具注册表API服务 - 提供工具调用、权限检查、监控功能",
            "environment": "production",
            "service_type": "tool_management",
            "capabilities": [
                "tool_execution",
                "permission_check",
                "tool_monitoring",
                "health_check"
            ],
            "endpoints": {
                "health": "/health",
                "list_tools": "/api/v1/tools",
                "execute_tool": "/api/v1/tools/execute",
                "get_tool": "/api/v1/tools/{tool_name}",
                "categories": "/api/v1/categories",
                "stats": "/api/v1/stats"
            }
        }
    },
    {
        "name": "xiaona-agent",
        "host": "localhost",
        "port": 8023,
        "metadata": {
            "version": "1.0.0",
            "description": "小娜·天秤女神法律专家智能体API服务",
            "environment": "production",
            "service_type": "agent",
            "agent_role": "legal_expert",
            "capabilities": [
                "patent_analysis",
                "legal_consult",
                "case_search",
                "document_review"
            ],
            "endpoints": {
                "health": "/health",
                "process_task": "/api/v1/xiaona/process",
                "analyze_patent": "/api/v1/xiaona/analyze-patent",
                "capabilities": "/api/v1/xiaona/capabilities"
            }
        }
    },
    {
        "name": "xiaonuo-agent",
        "host": "localhost",
        "port": 8024,
        "metadata": {
            "version": "1.0.0",
            "description": "小诺·双鱼公主协调官智能体API服务",
            "environment": "production",
            "service_type": "agent",
            "agent_role": "coordinator",
            "capabilities": [
                "task_coordination",
                "agent_dispatch",
                "resource_management",
                "parallel_execution"
            ],
            "endpoints": {
                "health": "/health",
                "coordinate": "/api/v1/xiaonuo/coordinate",
                "dispatch": "/api/v1/xiaonuo/dispatch",
                "list_agents": "/api/v1/xiaonuo/agents",
                "capabilities": "/api/v1/xiaonuo/capabilities"
            }
        }
    }
]

# 路由配置（使用/api/v1前缀以匹配API端点）
ROUTES_CONFIG = [
    # 工具注册表路由
    {
        "id": "route-tool-registry-health",
        "path": "/api/v1/tools/health",
        "target_service": "tool-registry-api",
        "methods": ["GET"],
        "weight": 100,
        "metadata": {
            "description": "工具注册表健康检查",
            "auth_required": False
        }
    },
    {
        "id": "route-tool-registry-list",
        "path": "/api/v1/tools",
        "target_service": "tool-registry-api",
        "methods": ["GET"],
        "weight": 100,
        "strip_prefix": False,
        "metadata": {
            "description": "获取工具列表",
            "auth_required": False
        }
    },
    {
        "id": "route-tool-registry-execute",
        "path": "/api/v1/tools/execute",
        "target_service": "tool-registry-api",
        "methods": ["POST"],
        "weight": 100,
        "strip_prefix": False,
        "metadata": {
            "description": "执行工具",
            "auth_required": True
        }
    },
    {
        "id": "route-tool-registry-detail",
        "path": "/api/v1/tools/{tool_name}",
        "target_service": "tool-registry-api",
        "methods": ["GET"],
        "weight": 100,
        "strip_prefix": False,
        "metadata": {
            "description": "获取工具详情",
            "auth_required": False
        }
    },
    {
        "id": "route-tool-registry-categories",
        "path": "/api/v1/tools/categories",
        "target_service": "tool-registry-api",
        "methods": ["GET"],
        "weight": 100,
        "strip_prefix": False,
        "metadata": {
            "description": "获取工具分类列表",
            "auth_required": False
        }
    },
    {
        "id": "route-tool-registry-stats",
        "path": "/api/v1/tools/stats",
        "target_service": "tool-registry-api",
        "methods": ["GET"],
        "weight": 100,
        "strip_prefix": False,
        "metadata": {
            "description": "获取工具统计信息",
            "auth_required": False
        }
    },

    # 小娜智能体路由
    {
        "id": "route-xiaona-process",
        "path": "/api/v1/xiaona/process",
        "target_service": "xiaona-agent",
        "methods": ["POST"],
        "weight": 100,
        "strip_prefix": False,
        "metadata": {
            "description": "小娜任务处理",
            "auth_required": False
        }
    },
    {
        "id": "route-xiaona-analyze-patent",
        "path": "/api/v1/xiaona/analyze-patent",
        "target_service": "xiaona-agent",
        "methods": ["POST"],
        "weight": 100,
        "strip_prefix": False,
        "metadata": {
            "description": "小娜专利分析",
            "auth_required": False
        }
    },
    {
        "id": "route-xiaona-capabilities",
        "path": "/api/v1/xiaona/capabilities",
        "target_service": "xiaona-agent",
        "methods": ["GET"],
        "weight": 100,
        "strip_prefix": False,
        "metadata": {
            "description": "获取小娜能力列表",
            "auth_required": False
        }
    },

    # 小诺智能体路由
    {
        "id": "route-xiaonuo-coordinate",
        "path": "/api/v1/xiaonuo/coordinate",
        "target_service": "xiaonuo-agent",
        "methods": ["POST"],
        "weight": 100,
        "strip_prefix": False,
        "metadata": {
            "description": "小诺任务协调",
            "auth_required": False
        }
    },
    {
        "id": "route-xiaonuo-dispatch",
        "path": "/api/v1/xiaonuo/dispatch",
        "target_service": "xiaonuo-agent",
        "methods": ["POST"],
        "weight": 100,
        "strip_prefix": False,
        "metadata": {
            "description": "小诺任务分发",
            "auth_required": False
        }
    },
    {
        "id": "route-xiaonuo-agents",
        "path": "/api/v1/xiaonuo/agents",
        "target_service": "xiaonuo-agent",
        "methods": ["GET"],
        "weight": 100,
        "strip_prefix": False,
        "metadata": {
            "description": "获取可用智能体列表",
            "auth_required": False
        }
    },
    {
        "id": "route-xiaonuo-capabilities",
        "path": "/api/v1/xiaonuo/capabilities",
        "target_service": "xiaonuo-agent",
        "methods": ["GET"],
        "weight": 100,
        "strip_prefix": False,
        "metadata": {
            "description": "获取小诺能力列表",
            "auth_required": False
        }
    }
]

# =============================================================================
# 日志配置
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# 核心功能
# =============================================================================

def check_gateway_health():
    """检查网关健康状态"""
    try:
        response = requests.get(f"{GATEWAY_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            logger.info("✅ 网关服务正常运行")
            return True
        else:
            logger.error(f"❌ 网关返回异常状态码: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ 无法连接到网关: {e}")
        return False


def register_services(services):
    """批量注册服务到网关"""
    logger.info(f"📝 开始注册 {len(services)} 个服务...")

    try:
        response = requests.post(
            f"{GATEWAY_BASE_URL}/api/services/batch_register",
            json={"services": services},
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                logger.info(f"✅ 成功注册 {len(services)} 个服务")
                for service in services:
                    logger.info(f"   • {service['name']}:{service['port']}")
                return True
            else:
                logger.error(f"❌ 服务注册失败: {result.get('message', '未知错误')}")
                return False
        else:
            logger.error(f"❌ 服务注册请求失败: {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ 注册服务时发生错误: {e}")
        return False


def register_routes(routes):
    """批量注册路由到网关"""
    logger.info(f"🛣️ 开始注册 {len(routes)} 条路由...")

    success_count = 0
    failed_routes = []

    for route in routes:
        try:
            response = requests.post(
                f"{GATEWAY_BASE_URL}/api/routes",
                json=route,
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if response.status_code in [200, 201]:
                logger.info(f"   ✅ {route['path']} → {route['target_service']}")
                success_count += 1
            else:
                logger.warning(f"   ⚠️ {route['path']} 注册失败: {response.status_code}")
                failed_routes.append(route['path'])

        except requests.exceptions.RequestException as e:
            logger.warning(f"   ⚠️ {route['path']} 注册失败: {e}")
            failed_routes.append(route['path'])

    logger.info(f"✅ 成功注册 {success_count}/{len(routes)} 条路由")

    if failed_routes:
        logger.warning(f"⚠️ 以下路由注册失败: {', '.join(failed_routes)}")

    return success_count > 0


def verify_registration():
    """验证服务注册状态"""
    logger.info("🔍 验证服务注册状态...")

    try:
        response = requests.get(f"{GATEWAY_BASE_URL}/api/services/instances", timeout=10)

        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                services = result["data"]["data"]

                # 检查我们注册的服务
                registered_services = [
                    "tool-registry-api",
                    "xiaona-agent",
                    "xiaonuo-agent"
                ]

                for service_name in registered_services:
                    found = any(s["service_name"] == service_name for s in services)
                    if found:
                        service = next(s for s in services if s["service_name"] == service_name)
                        logger.info(f"   ✅ {service_name}:{service['port']} - {service['status']}")
                    else:
                        logger.warning(f"   ❌ {service_name} 未找到")

                return True

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ 验证注册状态失败: {e}")
        return False


def verify_routes():
    """验证路由注册状态"""
    logger.info("🔍 验证路由注册状态...")

    try:
        response = requests.get(f"{GATEWAY_BASE_URL}/api/routes", timeout=10)

        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                routes = result["data"]["data"]
                logger.info(f"✅ 网关共有 {len(routes)} 条路由")
                return True

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ 验证路由状态失败: {e}")
        return False


# =============================================================================
# 主函数
# =============================================================================

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="注册智能体和工具服务到Athena网关"
    )
    parser.add_argument(
        "--host",
        default=GATEWAY_HOST,
        help=f"网关主机地址 (默认: {GATEWAY_HOST})"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=GATEWAY_PORT,
        help=f"网关端口 (默认: {GATEWAY_PORT})"
    )
    parser.add_argument(
        "--skip-health-check",
        action="store_true",
        help="跳过健康检查"
    )

    args = parser.parse_args()

    # 更新网关地址
    global GATEWAY_BASE_URL
    GATEWAY_BASE_URL = f"http://{args.host}:{args.port}"

    logger.info("🚀 Athena智能体和工具服务网关注册脚本")
    logger.info(f"📡 网关地址: {GATEWAY_BASE_URL}\n")

    # 1. 检查网关健康
    if not args.skip_health_check:
        if not check_gateway_health():
            logger.error("❌ 网关健康检查失败，请确保网关正在运行")
            sys.exit(1)

    # 2. 注册服务
    if not register_services(SERVICES_TO_REGISTER):
        logger.error("❌ 服务注册失败")
        sys.exit(1)

    # 3. 注册路由
    if not register_routes(ROUTES_CONFIG):
        logger.warning("⚠️ 部分路由注册失败，但服务已可用")

    # 4. 验证注册
    print("\n" + "="*60)
    verify_registration()
    print()
    verify_routes()
    print("="*60 + "\n")

    logger.info("✅ 注册完成！")
    logger.info("\n📖 使用示例:")
    logger.info("  # 工具列表")
    logger.info(f"  curl http://{args.host}:{args.port}/api/v1/tools")
    logger.info("\n  # 小娜任务处理")
    logger.info(f"  curl -X POST http://{args.host}:{args.port}/api/v1/xiaona/process \\")
    logger.info("    -H 'Content-Type: application/json' \\")
    logger.info("    -d '{\"task_type\": \"general\", \"input_data\": {\"input\": \"分析专利CN123456789A\"}}'")
    logger.info("\n  # 小诺任务协调")
    logger.info(f"  curl -X POST http://{args.host}:{args.port}/api/v1/xiaonuo/coordinate \\")
    logger.info("    -H 'Content-Type: application/json' \\")
    logger.info("    -d '{\"task_type\": \"patent_analysis\", \"agents\": [\"xiaona\"], \"input_data\": {\"patent_id\": \"CN123456789A\"}}'")


if __name__ == "__main__":
    main()
