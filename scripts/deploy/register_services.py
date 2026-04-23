#!/usr/bin/env python3
"""
服务注册脚本
Register existing services to Service Registry
"""
import asyncio
import logging
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.service_registry import HealthCheckConfig, ServiceRegistration, ServiceRegistryCenter
from core.service_registry.storage_memory import InMemoryServiceRegistryStorage

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# 服务配置列表
SERVICES_TO_REGISTER = [
    {
        "service_name": "xiaona",
        "instance_id": "xiaona-001",
        "host": "localhost",
        "port": 8001,
        "metadata": {
            "version": "2.0",
            "type": "agent",
            "capabilities": ["patent_analysis", "legal_research", "case_analysis"],
            "description": "小娜·法律专家Agent"
        },
        "health_check": HealthCheckConfig(
            check_type="http",
            check_interval=30,
            check_timeout=5,
            http_path="/health",
            http_expected_status=200
        )
    },
    {
        "service_name": "xiaonuo",
        "instance_id": "xiaonuo-001",
        "host": "localhost",
        "port": 8002,
        "metadata": {
            "version": "2.0",
            "type": "coordinator",
            "capabilities": ["task_coordination", "agent_orchestration"],
            "description": "小诺·协调器Agent"
        },
        "health_check": HealthCheckConfig(
            check_type="http",
            check_interval=30,
            check_timeout=5,
            http_path="/health",
            http_expected_status=200
        )
    },
    {
        "service_name": "yunxi",
        "instance_id": "yunxi-001",
        "host": "localhost",
        "port": 8003,
        "metadata": {
            "version": "1.0",
            "type": "agent",
            "capabilities": ["ip_management", "customer_management"],
            "description": "云熙·IP管理Agent"
        },
        "health_check": HealthCheckConfig(
            check_type="http",
            check_interval=30,
            check_timeout=5,
            http_path="/health",
            http_expected_status=200
        )
    },
    {
        "service_name": "gateway",
        "instance_id": "gateway-001",
        "host": "localhost",
        "port": 8005,
        "metadata": {
            "version": "1.0",
            "type": "api_gateway",
            "capabilities": ["routing", "load_balancing", "websocket"],
            "description": "统一Gateway"
        },
        "health_check": HealthCheckConfig(
            check_type="http",
            check_interval=30,
            check_timeout=5,
            http_path="/health",
            http_expected_status=200
        )
    },
    {
        "service_name": "knowledge_graph",
        "instance_id": "kg-001",
        "host": "localhost",
        "port": 7474,
        "metadata": {
            "version": "1.0",
            "type": "database",
            "capabilities": ["graph_storage", "graph_query"],
            "description": "知识图谱服务 (Neo4j)"
        },
        "health_check": HealthCheckConfig(
            check_type="http",
            check_interval=60,
            check_timeout=5,
            http_path="/",
            http_expected_status=200
        )
    }
]


async def register_all_services(registry: ServiceRegistryCenter):
    """注册所有服务

    Args:
        registry: 注册中心实例
    """
    logger.info(f"开始注册 {len(SERVICES_TO_REGISTER)} 个服务...")

    success_count = 0
    failed_count = 0

    for service_config in SERVICES_TO_REGISTER:
        try:
            # 创建注册信息
            registration = ServiceRegistration(
                service_name=service_config["service_name"],
                instance_id=service_config["instance_id"],
                host=service_config["host"],
                port=service_config["port"],
                metadata=service_config["metadata"]
            )

            # 注册服务
            success = await registry.register_service(registration)

            if success:
                logger.info(
                    f"✅ {service_config['service_name']} 注册成功 "
                    f"@ {service_config['host']}:{service_config['port']}"
                )
                success_count += 1
            else:
                logger.error(f"❌ {service_config['service_name']} 注册失败")
                failed_count += 1

        except Exception as e:
            logger.error(f"❌ 注册 {service_config['service_name']} 时出错: {e}")
            failed_count += 1

    logger.info(f"\n注册完成: ✅{success_count} 成功, ❌{failed_count} 失败")

    return success_count, failed_count


async def verify_services(registry: ServiceRegistryCenter):
    """验证注册的服务

    Args:
        registry: 注册中心实例
    """
    logger.info("\n验证已注册的服务...")

    # 获取所有服务
    services = await registry.get_all_services()
    logger.info(f"已注册服务: {', '.join(services)}")

    # 显示每个服务的统计信息
    for service_name in services:
        stats = await registry.get_service_statistics(service_name)

        logger.info(
            f"\n📊 {service_name}:"
            f"\n   总实例数: {stats['total_instances']}"
            f"\n   健康实例: {stats['healthy_instances']}"
            f"\n   不健康实例: {stats['unhealthy_instances']}"
        )

        if stats['instances']:
            for inst in stats['instances']:
                logger.info(
                    f"   - {inst['instance_id']} @ {inst['address']} "
                    f"({inst['status']})"
                )


async def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("Athena服务注册脚本")
    logger.info("=" * 60)

    # 创建内存存储（演示模式）
    storage = InMemoryServiceRegistryStorage()

    # 创建注册中心
    registry = ServiceRegistryCenter(storage=storage)

    try:
        # 注册所有服务
        success_count, failed_count = await register_all_services(registry)

        # 验证服务
        if success_count > 0:
            await verify_services(registry)

        # 显示注册中心统计
        stats = await registry.get_registry_statistics()
        logger.info(
            f"\n📊 注册中心统计:"
            f"\n   总服务数: {stats.get('total_services', 0)}"
            f"\n   总实例数: {stats.get('total_instances', 0)}"
            f"\n   健康实例: {stats.get('healthy_instances', 0)}"
            f"\n   不健康实例: {stats.get('unhealthy_instances', 0)}"
        )

        return failed_count == 0

    except Exception as e:
        logger.error(f"❌ 服务注册失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        await registry.close()


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
