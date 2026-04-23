#!/usr/bin/env python3
"""
脚本迁移映射表
"""

# 旧脚本到新命令的映射
MIGRATION_MAP = {
    # 启动脚本
    "start_athena.sh": "athena.py start",
    "start_xiaonuo_integrated.sh": "athena.py start --services core_server ai_service patent_api",
    "start_complete_memory_system.sh": "athena.py start --services core_server memory_service",
    "start_memory_service.sh": "athena.py start --services memory_service",
    "start_agent.sh": "athena.py start --services agent_service",

    # 数据库脚本
    "database/backup_db.sh": "athena.py deploy database_backup",
    "database/cleanup_db.sh": "athena.py cleanup --days 30",
    "database/init_db.sh": "athena.py deploy database_init",

    # 部署脚本
    "deployment/deploy.sh": "athena.py deploy athena_platform",
    "deployment/rollback.sh": "athena.py rollback athena_platform",

    # 监控脚本
    "monitoring/check_services.sh": "athena.py status",
    "monitoring/monitor.sh": "athena.py monitor",

    # 维护脚本
    "maintenance/health_check.sh": "athena.py status",
    "maintenance/system_update.sh": "athena.py deploy system_update",
}

# 服务配置映射
SERVICE_CONFIG = {
    "core_server": {
        "name": "核心服务",
        "command": "python -m core.app",
        "port": 8000,
        "dependencies": []
    },
    "ai_service": {
        "name": "AI服务",
        "command": "python -m services.ai_app",
        "port": 8001,
        "dependencies": ["core_server"]
    },
    "patent_api": {
        "name": "专利API",
        "command": "python -m services.patent_api",
        "port": 8002,
        "dependencies": ["core_server"]
    },
    "memory_service": {
        "name": "记忆服务",
        "command": "python -m memory.main",
        "port": 8003,
        "dependencies": ["core_server"]
    },
    "storage_service": {
        "name": "存储服务",
        "command": "python -m storage-system.main",
        "dependencies": ["core_server"]
    },
    "agent_service": {
        "name": "智能体服务",
        "command": "python -m agents.main",
        "port": 8004,
        "dependencies": ["core_server", "ai_service"]
    }
}

def get_migration_info(old_script) -> None:
    """获取迁移信息"""
    if old_script in MIGRATION_MAP:
        return {
            "old": old_script,
            "new": MIGRATION_MAP[old_script],
            "status": "已映射"
        }
    else:
        return {
            "old": old_script,
            "new": "athena.py help",
            "status": "需要手动迁移"
        }

def print_migration_table() -> Any:
    """打印迁移表"""
    print("\n" + "=" * 80)
    print("脚本迁移映射表")
    print("=" * 80)
    print(f"{'旧脚本':<40} {'新命令':<40} {'状态':<10}")
    print("-" * 80)

    for old_script, new_command in MIGRATION_MAP.items():
        print(f"{old_script:<40} {new_command:<40} {'✅已映射':<10}")

    print("\n" + "=" * 80)
    print("服务配置")
    print("=" * 80)
    print(f"{'服务名':<20} {'端口':<6} {'依赖':<30} {'命令':<50}")
    print("-" * 80)

    for service_name, config in SERVICE_CONFIG.items():
        deps = ', '.join(config['dependencies']) if config['dependencies'] else '无'
        print(f"{service_name:<20} {config['port'] or 'N/A':<6} {deps:<30} {config['command']:<50}")

if __name__ == "__main__":
    print_migration_table()