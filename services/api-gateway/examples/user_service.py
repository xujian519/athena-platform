#!/usr/bin/env python3
"""
示例微服务 - 用户服务
用于演示Athena API Gateway的自动发现和注册功能
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any

import aiohttp
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 服务配置
SERVICE_NAME = "user-service"
SERVICE_HOST = "localhost"
SERVICE_PORT = 8001
GATEWAY_URL = "http://localhost:8080"
HEALTH_ENDPOINT = "/health"

# 创建FastAPI应用
app = FastAPI(title="用户服务", description="用户管理微服务示例", version="1.0.0")

# 模拟用户数据
users_db = {
    "1": {"id": "1", "name": "张三", "email": "zhangsan@example.com", "role": "admin"},
    "2": {"id": "2", "name": "李四", "email": "lisi@example.com", "role": "user"},
    "3": {"id": "3", "name": "王五", "email": "wangwu@example.com", "role": "user"},
}


# 数据模型
class User(BaseModel):
    id: str
    name: str
    email: str
    role: str = "user"


class CreateUser(BaseModel):
    name: str
    email: str
    role: str = "user"


class ServiceRegistration(BaseModel):
    service_name: str
    instance_id: str
    host: str
    port: int
    protocol: str = "http"
    health_endpoint: str = "/health"
    metadata: dict[str, Any] = {}
    tags: list = []


# 全局变量
instance_id = str(uuid.uuid4())
registered = False

# ==================== 服务注册功能 ====================


async def register_with_gateway():
    """向API Gateway注册服务"""
    global registered

    registration_data = {
        "service_name": SERVICE_NAME,
        "instance_id": instance_id,
        "host": SERVICE_HOST,
        "port": SERVICE_PORT,
        "protocol": "http",
        "health_endpoint": HEALTH_ENDPOINT,
        "metadata": {
            "version": "1.0.0",
            "description": "用户管理微服务",
            "startup_time": datetime.now().isoformat(),
        },
        "tags": ["user", "management", "core"],
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{GATEWAY_URL}/api/v1/services/register",
                json=registration_data,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 200:
                    logger.info(f"服务注册成功: {SERVICE_NAME}/{instance_id}")
                    registered = True
                    return True
                else:
                    logger.error(f"服务注册失败: HTTP {response.status}")
                    return False
    except Exception as e:
        logger.error(f"服务注册异常: {e}")
        return False


async def deregister_from_gateway():
    """从API Gateway注销服务"""
    if not registered:
        return True

    try:
        async with aiohttp.ClientSession() as session:
            url = f"{GATEWAY_URL}/api/v1/services/{SERVICE_NAME}/instances/{instance_id}"
            async with session.delete(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    logger.info(f"服务注销成功: {SERVICE_NAME}/{instance_id}")
                    return True
                else:
                    logger.error(f"服务注销失败: HTTP {response.status}")
                    return False
    except Exception as e:
        logger.error(f"服务注销异常: {e}")
        return False


async def periodic_heartbeat():
    """定期心跳任务"""
    while registered:
        try:
            # 通过发送健康检查来保持心跳
            async with aiohttp.ClientSession() as session:
                health_url = f"{GATEWAY_URL}/health"
                async with session.get(
                    health_url, timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        logger.debug("心跳检查成功")
                    else:
                        logger.warning(f"心跳检查失败: HTTP {response.status}")
        except Exception as e:
            logger.warning(f"心跳检查异常: {e}")

        await asyncio.sleep(30)  # 每30秒发送一次心跳


# ==================== API 端点 ====================


@app.get("/")
async def root():
    """根端点"""
    return {
        "service": SERVICE_NAME,
        "instance_id": instance_id,
        "status": "running",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "instance_id": instance_id,
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
    }


@app.get("/api/users", response_model=list[User])
async def get_users():
    """获取所有用户"""
    return list(users_db.values())


@app.get("/api/users/{user_id}", response_model=User)
async def get_user(user_id: str):
    """获取指定用户"""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="用户不存在")
    return users_db[user_id]


@app.post("/api/users", response_model=User)
async def create_user(user_data: CreateUser):
    """创建新用户"""
    new_id = str(max(int(uid) for uid in users_db.keys()) + 1)
    new_user = User(id=new_id, name=user_data.name, email=user_data.email, role=user_data.role)
    users_db[new_id] = new_user
    return new_user


@app.put("/api/users/{user_id}", response_model=User)
async def update_user(user_id: str, user_data: CreateUser):
    """更新用户信息"""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="用户不存在")

    users_db[user_id] = User(
        id=user_id, name=user_data.name, email=user_data.email, role=user_data.role
    )
    return users_db[user_id]


@app.delete("/api/users/{user_id}")
async def delete_user(user_id: str):
    """删除用户"""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="用户不存在")

    del users_db[user_id]
    return {"message": "用户删除成功"}


@app.get("/api/users/{user_id}/profile")
async def get_user_profile(user_id: str):
    """获取用户详细信息"""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="用户不存在")

    user = users_db[user_id]
    return {
        "user": user,
        "permissions": {
            "can_read": True,
            "can_write": user["role"] == "admin",
            "can_delete": user["role"] == "admin",
        },
        "last_login": datetime.now().isoformat(),
        "account_created": "2024-01-01T00:00:00Z",
    }


# ==================== 生命周期事件 ====================


@app.on_event("startup")
async def startup_event():
    """服务启动事件"""
    logger.info(f"启动 {SERVICE_NAME} (实例ID: {instance_id})")

    # 等待一段时间确保API Gateway已启动
    await asyncio.sleep(5)

    # 注册到API Gateway
    max_retries = 3
    for i in range(max_retries):
        if await register_with_gateway():
            # 启动心跳任务
            asyncio.create_task(periodic_heartbeat())
            logger.info("服务启动并注册完成")
            return
        else:
            logger.warning(f"注册失败，重试 {i + 1}/{max_retries}")
            await asyncio.sleep(5)

    logger.error("服务注册失败，服务将继续运行但未注册到网关")


@app.on_event("shutdown")
async def shutdown_event():
    """服务关闭事件"""
    logger.info(f"关闭 {SERVICE_NAME} (实例ID: {instance_id})")

    # 从API Gateway注销
    await deregister_from_gateway()

    logger.info("服务关闭完成")


# ==================== 主函数 ====================

if __name__ == "__main__":
    logger.info(f"启动 {SERVICE_NAME} 在 {SERVICE_HOST}:{SERVICE_PORT}")

    uvicorn.run(
        "user_service:app", host=SERVICE_HOST, port=SERVICE_PORT, reload=True, log_level="info"
    )
