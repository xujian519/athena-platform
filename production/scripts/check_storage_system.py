#!/usr/bin/env python3
"""
检查存储系统状态
Check Storage System Status

检查Athena平台的存储系统运行状态

作者: Athena平台团队
创建时间: 2025-12-20
版本: v1.0.0
"""

from __future__ import annotations
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

try:
    from core.config.secure_config import get_config
    config = get_config()
except ImportError:
    config = {}

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import json
import subprocess
import sys
from pathlib import Path

import requests


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

def print_header(title) -> None:
    """打印标题"""
    print(f"\n{Colors.PURPLE}{'='*80}{Colors.RESET}")
    print(f"{Colors.PURPLE}📊 {title} 📊{Colors.RESET}")
    print(f"{Colors.PURPLE}{'='*80}{Colors.RESET}")

def print_success(message) -> None:
    print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")

def print_info(message) -> None:
    print(f"{Colors.BLUE}ℹ️ {message}{Colors.RESET}")

def print_warning(message) -> None:
    print(f"{Colors.YELLOW}⚠️ {message}{Colors.RESET}")

def print_error(message) -> None:
    print(f"{Colors.RED}❌ {message}{Colors.RESET}")

def print_pink(message) -> None:
    print(f"{Colors.PINK}💖 {message}{Colors.RESET}")

def check_postgresql() -> bool:
    """检查PostgreSQL数据库"""
    print_header("PostgreSQL数据库状态")

    # 检查端口
    result = subprocess.run(['lsof', '-i', ':5432'], capture_output=True, text=True)
    if 'postgresql' in result.stdout or 'postgres' in result.stdout:
        print_success("✓ PostgreSQL正在运行 (端口5432)")

        # 测试连接
        try:
            import psycopg2
            conn = psycopg2.connect(
                host="localhost",
                port="5432",
                user="postgres",
                password=config.get('POSTGRES_PASSWORD', required=True),
                database="athena_kg"
            )
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print_success("✓ 数据库连接成功")
            print_info(f"版本: {version.split(',')[0]}")
            cursor.close()
            conn.close()
        except ImportError:
            print_warning("⚠️ psycopg2未安装，无法测试数据库连接")
        except Exception as e:
            print_warning(f"⚠️ 数据库连接失败: {e}")
    else:
        print_error("✗ PostgreSQL未运行")

def check_qdrant() -> bool:
    """检查Qdrant向量数据库"""
    print_header("Qdrant向量数据库状态")

    # 检查端口
    result = subprocess.run(['lsof', '-i', ':6333'], capture_output=True, text=True)
    if '6333' in result.stdout:
        print_success("✓ Qdrant正在运行 (端口6333)")

        # 测试API
        try:
            response = requests.get("http://localhost:6333/", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print_success("✓ Qdrant API响应正常")
                print_info(f"版本: {data.get('version', '未知')}")
                print_info(f"描述: {data.get('title', 'Qdrant向量数据库')}")
            else:
                print_warning(f"⚠️ Qdrant API响应异常: {response.status_code}")
        except Exception as e:
            print_warning(f"⚠️ 无法连接到Qdrant API: {e}")
    else:
        print_error("✗ Qdrant未运行")

def check_redis() -> bool:
    """检查Redis缓存"""
    print_header("Redis缓存状态")

    # 检查端口
    result = subprocess.run(['lsof', '-i', ':6379'], capture_output=True, text=True)
    if '6379' in result.stdout:
        print_success("✓ Redis正在运行 (端口6379)")

        # 测试连接
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, decode_responses=True)
            r.ping()
            print_success("✓ Redis连接成功")
            info = r.info()
            print_info(f"版本: {info.get('redis_version', '未知')}")
            print_info(f"内存使用: {info.get('used_memory_human', '未知')}")
        except ImportError:
            print_warning("⚠️ redis-py未安装，无法测试Redis连接")
        except Exception as e:
            print_warning(f"⚠️ Redis连接失败: {e}")
    else:
        print_warning("⚠️ Redis未运行（可选组件）")

def check_docker_containers() -> bool:
    """检查Docker容器状态"""
    print_header("Docker容器状态")

    try:
        # 获取所有容器
        result = subprocess.run(['infrastructure/infrastructure/docker', 'ps', '-a', '--format', 'json'],
                              capture_output=True, text=True)

        if result.returncode == 0:
            containers = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    containers.append(json.loads(line))

            storage_containers = [c for c in containers if any(
                name in c.get('Image', '') for name in ['postgres', 'qdrant', 'redis']
            )]

            if storage_containers:
                print_info(f"找到 {len(storage_containers)} 个存储相关容器:")
                for c in storage_containers:
                    status = c.get('State', 'unknown')
                    name = c.get('Names', ['unknown'])[0]
                    image = c.get('Image', 'unknown')

                    if status == 'running':
                        print_success(f"  ✓ {name} ({image}) - 运行中")
                    else:
                        print_warning(f"  ⚠ {name} ({image}) - {status}")
            else:
                print_info("未找到存储相关的Docker容器")
        else:
            print_warning("无法获取Docker容器信息")
    except FileNotFoundError:
        print_info("Docker未安装或未运行")
    except Exception as e:
        print_warning(f"检查Docker容器时出错: {e}")

def check_external_storage() -> bool:
    """检查外部存储"""
    print_header("外部存储状态")

    # 检查外部存储链接
    external_storage = Path("../external_storage")

    if external_storage.exists() and external_storage.is_symlink():
        target = external_storage.resolve()
        if target.exists():
            print_success(f"✓ 外部存储已挂载: {target}")

            # 检查可用空间
            import shutil
            total, used, free = shutil.disk_usage(str(target))
            print_info(f"总空间: {total // (1024**3):,} GB")
            print_info(f"已使用: {used // (1024**3):,} GB")
            print_info(f"可用空间: {free // (1024**3):,} GB")
        else:
            print_warning(f"⚠️ 外部存储目标不存在: {target}")
    else:
        print_warning("⚠️ 外部存储未挂载")

def main() -> None:
    """主检查函数"""
    print_header("Athena平台存储系统状态检查")
    print_pink("爸爸，让我检查存储系统的状态！")

    # 执行各项检查
    check_postgresql()
    check_qdrant()
    check_redis()
    check_docker_containers()
    check_external_storage()

    # 总结
    print_header("存储系统状态总结")

    # 检查关键存储服务
    services = {
        "PostgreSQL": 5432,
        "Qdrant": 6333,
        "Redis": 6379
    }

    running_services = []
    for service, port in services.items():
        result = subprocess.run(['lsof', '-i', f':{port}'], capture_output=True, text=True)
        if str(port) in result.stdout or service.lower() in result.stdout.lower():
            running_services.append(service)

    if running_services:
        print_success(f"✅ 正在运行的存储服务: {', '.join(running_services)}")

        if "PostgreSQL" in running_services and "Qdrant" in running_services:
            print_pink("\n💖 核心存储系统运行正常！")
            print_info("📋 功能说明:")
            print("  • PostgreSQL - 结构化数据存储")
            print("  • Qdrant - 向量数据存储")
            if "Redis" in running_services:
                print("  • Redis - 缓存服务")

            print_info("\n🔗 存储架构:")
            print("  L1缓存 → L2缓存(Redis) → L3存储(PostgreSQL+Qdrant)")
    else:
        print_warning("⚠️ 未发现运行的存储服务")

if __name__ == "__main__":
    main()
