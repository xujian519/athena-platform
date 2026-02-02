#!/usr/bin/env python3
"""
智能体服务管理器
统一管理所有智能体服务的启动、停止和通信
"""

import asyncio
from core.async_main import async_main
import httpx
import json
import logging
from core.logging_config import setup_logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

class AgentManager:
    """智能体服务管理器"""

    def __init__(self):
        self.services = {
            "xiao-nuo": {
                "name": "小诺智能体",
                "port": 9002,
                "path": "xiao-nuo-control",
                "status": "stopped",
                "pid": None,
                "health_url": "http://localhost:9002/health"
            },
            "unified-identity": {
                "name": "统一身份服务",
                "port": 9003,
                "path": "unified-identity",
                "status": "stopped",
                "pid": None,
                "health_url": "http://localhost:9003/health"
            },
            "vector_db": {
                "name": "向量数据库",
                "port": 9004,
                "path": "vector_db",
                "status": "stopped",
                "pid": None,
                "health_url": "http://localhost:9004/status"
            },
            "vector-service": {
                "name": "向量服务",
                "port": 9005,
                "path": "vector-service",
                "status": "stopped",
                "pid": None,
                "health_url": "http://localhost:9005/health"
            },
            "yunpat": {
                "name": "云熙专利智能体",
                "port": 8020,
                "path": "../yunpat-agent",
                "status": "stopped",
                "pid": None,
                "health_url": "http://localhost:8020/api/v1/health"
            }
        }

    async def start_service(self, service_id: str) -> bool:
        """启动单个服务"""
        if service_id not in self.services:
            logger.error(f"服务 {service_id} 不存在")
            return False

        service = self.services[service_id]

        if service["status"] == "running":
            logger.info(f"服务 {service['name']} 已在运行")
            return True

        logger.info(f"启动服务: {service['name']}")

        try:
            # 构建启动命令
            cmd = f"cd {service['path']} && python main.py"

            # 启动服务（实际应该使用subprocess.Popen）
            logger.info(f"执行命令: {cmd}")

            # 模拟启动
            await asyncio.sleep(2)

            service["status"] = "running"
            service["start_time"] = datetime.now().isoformat()

            logger.info(f"服务 {service['name']} 启动成功")
            return True

        except Exception as e:
            logger.error(f"启动服务 {service['name']} 失败: {e}")
            return False

    async def stop_service(self, service_id: str) -> bool:
        """停止单个服务"""
        if service_id not in self.services:
            logger.error(f"服务 {service_id} 不存在")
            return False

        service = self.services[service_id]

        if service["status"] != "running":
            logger.info(f"服务 {service['name']} 未在运行")
            return True

        logger.info(f"停止服务: {service['name']}")

        try:
            # 停止服务
            service["status"] = "stopped"
            service["stop_time"] = datetime.now().isoformat()

            logger.info(f"服务 {service['name']} 已停止")
            return True

        except Exception as e:
            logger.error(f"停止服务 {service['name']} 失败: {e}")
            return False

    async def check_service_health(self, service_id: str) -> bool:
        """检查服务健康状态"""
        if service_id not in self.services:
            return False

        service = self.services[service_id]
        health_url = service.get("health_url")

        if not health_url:
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(health_url, timeout=5.0)
                if response.status_code == 200:
                    service["status"] = "running"
                    service["last_check"] = datetime.now().isoformat()
                    return True
                else:
                    service["status"] = "unhealthy"
                    return False

        except Exception as e:
            logger.warning(f"健康检查失败 {service['name']}: {e}")
            service["status"] = "error"
            return False

    async def start_all(self) -> Dict[str, bool]:
        """启动所有服务"""
        results = {}

        for service_id in self.services:
            results[service_id] = await self.start_service(service_id)
            # 等待一下再启动下一个
            await asyncio.sleep(1)

        return results

    async def stop_all(self) -> Dict[str, bool]:
        """停止所有服务"""
        results = {}

        # 按相反顺序停止服务
        for service_id in reversed(list(self.services.keys())):
            results[service_id] = await self.stop_service(service_id)
            await asyncio.sleep(0.5)

        return results

    async def get_status(self) -> Dict:
        """获取所有服务状态"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "total_services": len(self.services),
            "running": 0,
            "stopped": 0,
            "error": 0,
            "services": {}
        }

        for service_id, service in self.services.items():
            await self.check_service_health(service_id)
            status["services"][service_id] = {
                "name": service["name"],
                "port": service["port"],
                "status": service["status"]
            }

            # 统计状态
            if service["status"] == "running":
                status["running"] += 1
            elif service["status"] == "stopped":
                status["stopped"] += 1
            else:
                status["error"] += 1

        return status

    async def communicate(self, from_agent: str, to_agent: str, message: Dict) -> Dict | None:
        """智能体间通信"""
        if to_agent not in self.services:
            logger.error(f"目标智能体 {to_agent} 不存在")
            return None

        service = self.services[to_agent]

        if service["status"] != "running":
            logger.error(f"目标智能体 {to_agent} 未运行")
            return None

        # 构建通信消息
        comm_message = {
            "from": from_agent,
            "to": to_agent,
            "timestamp": datetime.now().isoformat(),
            "message": message
        }

        logger.info(f"通信: {from_agent} -> {to_agent}")

        # TODO: 实现实际的通信逻辑
        # 这里应该发送到目标智能体的通信端点

        return {"status": "sent", "message_id": "msg_123"}

# CLI接口
async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="智能体服务管理器")
    parser.add_argument("command", choices=["start", "stop", "status", "health", "comm"])
    parser.add_argument("--service", help="指定服务名称")
    parser.add_argument("--from", dest="from_agent", help="发送方智能体")
    parser.add_argument("--to", dest="to_agent", help="接收方智能体")
    parser.add_argument("--message", help="通信消息")

    args = parser.parse_args()

    manager = AgentManager()

    if args.command == "start":
        if args.service:
            await manager.start_service(args.service)
        else:
            results = await manager.start_all()
            print(f"启动结果: {results}")

    elif args.command == "stop":
        if args.service:
            await manager.stop_service(args.service)
        else:
            results = await manager.stop_all()
            print(f"停止结果: {results}")

    elif args.command == "status":
        status = await manager.get_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))

    elif args.command == "health":
        if args.service:
            healthy = await manager.check_service_health(args.service)
            print(f"健康状态: {'正常' if healthy else '异常'}")
        else:
            for service_id in manager.services:
                healthy = await manager.check_service_health(service_id)
                print(f"{service_id}: {'✅' if healthy else '❌'}")

    elif args.command == "comm":
        if not all([args.from_agent, args.to_agent, args.message]):
            print("通信需要指定 --from, --to, --message")
            return

        message = {"text": args.message}
        result = await manager.communicate(args.from_agent, args.to_agent, message)
        print(f"通信结果: {result}")

# 入口点: @async_main装饰器已添加到main函数