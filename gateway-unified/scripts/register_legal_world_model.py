#!/usr/bin/env python3
"""
法律世界模型服务注册脚本
Register Legal World Model Service to Gateway

将法律世界模型微服务注册到统一网关

用法:
    python register_legal_world_model.py [--host HOST] [--port PORT]

作者: Athena平台团队
版本: 1.0.0
"""

import argparse
import logging
import sys
import time

import requests

# =============================================================================
# 配置
# =============================================================================

GATEWAY_HOST = "localhost"
GATEWAY_PORT = 8005
GATEWAY_BASE_URL = f"http://{GATEWAY_HOST}:{GATEWAY_PORT}"

# 法律世界模型服务配置
LEGAL_WORLD_MODEL_SERVICE = {
    "name": "legal-world-model",
    "host": "localhost",
    "port": 8020,
    "metadata": {
        "version": "1.0.0",
        "description": "法律世界模型API服务 - 提供法律知识检索、场景规则查询、动态提示词生成",
        "environment": "production",
        "service_type": "legal_intelligence",
        "capabilities": [
            "dynamic_prompt_generation",
            "scenario_rules_retrieval",
            "legal_knowledge_graph",
            "health_check"
        ],
        "endpoints": {
            "health": "/health",
            "generate_prompt": "/api/v1/generate-prompt",
            "retrieve_rules": "/api/v1/retrieve-rules",
            "scenarios": "/api/v1/scenarios",
            "layers": "/api/v1/layers",
            "stats": "/api/v1/stats"
        }
    }
}

# 路由配置
ROUTES_CONFIG = [
    {
        "id": "route-legal-world-model-generate-prompt",
        "path": "/api/legal-world-model/v1/generate-prompt",
        "target_service": "legal-world-model",
        "methods": ["POST"],
        "weight": 100,
        "metadata": {
            "description": "生成动态提示词",
            "capability": "dynamic_prompt_generation",
            "auth_required": False
        }
    },
    {
        "id": "route-legal-world-model-retrieve-rules",
        "path": "/api/legal-world-model/v1/retrieve-rules",
        "target_service": "legal-world-model",
        "methods": ["POST"],
        "weight": 100,
        "metadata": {
            "description": "检索场景规则",
            "capability": "scenario_rules_retrieval",
            "auth_required": False
        }
    },
    {
        "id": "route-legal-world-model-scenarios",
        "path": "/api/legal-world-model/v1/scenarios",
        "target_service": "legal-world-model",
        "methods": ["GET"],
        "weight": 100,
        "metadata": {
            "description": "列出所有可用场景",
            "auth_required": False
        }
    },
    {
        "id": "route-legal-world-model-layers",
        "path": "/api/legal-world-model/v1/layers",
        "target_service": "legal-world-model",
        "methods": ["GET"],
        "weight": 100,
        "metadata": {
            "description": "列出法律世界模型层级",
            "auth_required": False
        }
    },
    {
        "id": "route-legal-world-model-stats",
        "path": "/api/legal-world-model/v1/stats",
        "target_service": "legal-world-model",
        "methods": ["GET"],
        "weight": 100,
        "metadata": {
            "description": "获取统计信息",
            "auth_required": False
        }
    },
    {
        "id": "route-legal-world-model-health",
        "path": "/api/legal-world-model/health",
        "target_service": "legal-world-model",
        "methods": ["GET"],
        "weight": 100,
        "metadata": {
            "description": "健康检查",
            "auth_required": False
        }
    },
    {
        "id": "route-legal-world-model-root",
        "path": "/api/legal-world-model",
        "target_service": "legal-world-model",
        "methods": ["GET"],
        "weight": 100,
        "metadata": {
            "description": "服务信息",
            "auth_required": False
        }
    }
]

# 依赖配置
DEPENDENCIES_CONFIG = {
    "service": "legal-world-model",
    "depends_on": ["neo4j", "postgresql"]
}

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# Gateway API客户端
# =============================================================================

class GatewayClient:
    """Gateway API客户端"""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()

    def check_gateway_health(self) -> bool:
        """检查Gateway健康状态"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Gateway健康检查失败: {e}")
            return False

    def register_service_batch(self, services: list[dict]) -> dict:
        """批量注册服务"""
        url = f"{self.base_url}/api/services/batch_register"
        payload = {"services": services}

        try:
            response = self.session.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"批量注册服务失败: {e}")
            raise

    def list_instances(self) -> dict:
        """查询所有服务实例"""
        url = f"{self.base_url}/api/services/instances"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"查询服务实例失败: {e}")
            raise

    def create_route(self, route: dict) -> dict:
        """创建路由"""
        url = f"{self.base_url}/api/routes"

        try:
            response = self.session.post(url, json=route, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"创建路由失败: {e}")
            raise

    def list_routes(self) -> dict:
        """查询所有路由"""
        url = f"{self.base_url}/api/routes"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"查询路由失败: {e}")
            raise

    def set_dependencies(self, dep: dict) -> dict:
        """设置服务依赖"""
        url = f"{self.base_url}/api/dependencies"

        try:
            response = self.session.post(url, json=dep, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"设置依赖失败: {e}")
            raise

    def get_dependencies(self, service: str) -> dict:
        """查询服务依赖"""
        url = f"{self.base_url}/api/dependencies/{service}"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"查询依赖失败: {e}")
            raise


# =============================================================================
# 注册逻辑
# =============================================================================

def check_legal_world_model_service(host: str, port: int) -> bool:
    """检查法律世界模型服务是否运行"""
    try:
        url = f"http://{host}:{port}/health"
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"法律世界模型服务健康检查失败: {e}")
        return False


def register_service(client: GatewayClient, service_config: dict) -> bool:
    """注册服务到Gateway"""
    logger.info(f"注册服务: {service_config['name']}")

    try:
        result = client.register_service_batch([service_config])
        if result.get("success"):
            logger.info(f"✅ 服务注册成功: {service_config['name']}")
            return True
        else:
            logger.error(f"❌ 服务注册失败: {result}")
            return False
    except Exception as e:
        logger.error(f"❌ 服务注册异常: {e}")
        return False


def register_routes(client: GatewayClient, routes: list[dict]) -> bool:
    """注册路由到Gateway"""
    logger.info(f"注册 {len(routes)} 条路由规则...")

    success_count = 0
    for route in routes:
        try:
            result = client.create_route(route)
            if result.get("success"):
                logger.info(f"  ✅ 路由创建成功: {route['path']}")
                success_count += 1
            else:
                logger.warning(f"  ⚠️  路由创建失败: {route['path']} - {result}")
        except Exception as e:
            logger.warning(f"  ⚠️  路由创建异常: {route['path']} - {e}")

    logger.info(f"路由注册完成: {success_count}/{len(routes)} 成功")
    return success_count > 0


def register_dependencies(client: GatewayClient, dep_config: dict) -> bool:
    """注册服务依赖"""
    logger.info(f"设置服务依赖: {dep_config['service']} -> {dep_config['depends_on']}")

    try:
        result = client.set_dependencies(dep_config)
        if result.get("success"):
            logger.info("✅ 依赖设置成功")
            return True
        else:
            logger.warning(f"⚠️  依赖设置失败: {result}")
            return False
    except Exception as e:
        logger.warning(f"⚠️  依赖设置异常: {e}")
        return False


def verify_registration(client: GatewayClient) -> bool:
    """验证注册结果"""
    logger.info("验证注册结果...")

    try:
        # 验证服务实例
        instances = client.list_instances()
        if instances.get("success"):
            data = instances.get("data", [])
            lwm_instances = [i for i in data if i.get("service_name") == "legal-world-model"]
            if lwm_instances:
                logger.info(f"✅ 找到 {len(lwm_instances)} 个法律世界模型服务实例")
            else:
                logger.warning("⚠️  未找到法律世界模型服务实例")
                return False

        # 验证路由
        routes = client.list_routes()
        if routes.get("success"):
            data = routes.get("data", [])
            lwm_routes = [r for r in data if r.get("target_service") == "legal-world-model"]
            if lwm_routes:
                logger.info(f"✅ 找到 {len(lwm_routes)} 条法律世界模型路由")
            else:
                logger.warning("⚠️  未找到法律世界模型路由")
                return False

        # 验证依赖
        deps = client.get_dependencies("legal-world-model")
        if deps.get("success"):
            dep_data = deps.get("data", {})
            depends_on = dep_data.get("dependencies", [])
            logger.info(f"✅ 服务依赖: {depends_on}")

        return True

    except Exception as e:
        logger.error(f"❌ 验证失败: {e}")
        return False


def test_gateway_routing(client: GatewayClient) -> bool:
    """测试Gateway路由"""
    logger.info("测试Gateway路由...")

    try:
        # 测试健康检查路由
        url = f"{client.base_url}/api/legal-world-model/health"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            logger.info("✅ Gateway路由测试成功")
            return True
        else:
            logger.warning(f"⚠️  Gateway路由测试返回状态码: {response.status_code}")
            return False

    except Exception as e:
        logger.error(f"❌ Gateway路由测试失败: {e}")
        return False


# =============================================================================
# 主函数
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="注册法律世界模型服务到Gateway")
    parser.add_argument("--host", default=GATEWAY_HOST, help="Gateway主机地址")
    parser.add_argument("--port", type=int, default=GATEWAY_PORT, help="Gateway端口")
    parser.add_argument("--service-host", default="localhost", help="法律世界模型服务主机地址")
    parser.add_argument("--service-port", type=int, default=8020, help="法律世界模型服务端口")
    parser.add_argument("--verify", action="store_true", help="只验证不注册")

    args = parser.parse_args()

    # 更新配置
    GATEWAY_BASE_URL = f"http://{args.host}:{args.port}"
    LEGAL_WORLD_MODEL_SERVICE["host"] = args.service_host
    LEGAL_WORLD_MODEL_SERVICE["port"] = args.service_port

    # 创建Gateway客户端
    client = GatewayClient(GATEWAY_BASE_URL)

    # 检查Gateway健康状态
    logger.info(f"检查Gateway状态: {GATEWAY_BASE_URL}")
    if not client.check_gateway_health():
        logger.error("❌ Gateway不可用，请确保Gateway正在运行")
        return 1

    logger.info("✅ Gateway可用")

    # 检查法律世界模型服务
    logger.info(f"检查法律世界模型服务: {args.service_host}:{args.service_port}")
    if not check_legal_world_model_service(args.service_host, args.service_port):
        logger.warning("⚠️  法律世界模型服务不可用")
        if not args.verify:
            logger.error("❌ 无法注册不可用的服务")
            return 1
    else:
        logger.info("✅ 法律世界模型服务可用")

    if args.verify:
        # 只验证
        logger.info("验证模式，跳过注册...")
        verify_registration(client)
        test_gateway_routing(client)
        return 0

    # 执行注册
    logger.info("=" * 60)
    logger.info("开始注册法律世界模型服务到Gateway")
    logger.info("=" * 60)

    # 1. 注册服务实例
    if not register_service(client, LEGAL_WORLD_MODEL_SERVICE):
        logger.error("❌ 服务注册失败，终止")
        return 1

    # 等待服务注册生效
    time.sleep(1)

    # 2. 注册路由规则
    if not register_routes(client, ROUTES_CONFIG):
        logger.warning("⚠️  部分路由注册失败，继续...")

    # 3. 设置服务依赖
    register_dependencies(client, DEPENDENCIES_CONFIG)

    # 4. 验证注册结果
    if not verify_registration(client):
        logger.warning("⚠️  注册验证失败，但服务可能已正常注册")

    # 5. 测试Gateway路由
    test_gateway_routing(client)

    logger.info("=" * 60)
    logger.info("注册完成！")
    logger.info("=" * 60)
    logger.info("")
    logger.info("您现在可以通过以下方式访问法律世界模型服务:")
    logger.info(f"  - 健康检查: {GATEWAY_BASE_URL}/api/legal-world-model/health")
    logger.info(f"  - 生成提示词: {GATEWAY_BASE_URL}/api/legal-world-model/v1/generate-prompt")
    logger.info(f"  - 场景列表: {GATEWAY_BASE_URL}/api/legal-world-model/v1/scenarios")
    logger.info("")

    return 0


if __name__ == "__main__":
    sys.exit(main())
