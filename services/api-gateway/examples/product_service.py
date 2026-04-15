#!/usr/bin/env python3
"""
示例微服务 - 产品服务
用于演示Athena API Gateway的自动发现和注册功能
"""

import asyncio
import logging
import uuid
from datetime import datetime

import aiohttp
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 服务配置
SERVICE_NAME = "product-service"
SERVICE_HOST = "localhost"
SERVICE_PORT = 8002
GATEWAY_URL = "http://localhost:8080"
HEALTH_ENDPOINT = "/health"

# 创建FastAPI应用
app = FastAPI(title="产品服务", description="产品管理微服务示例", version="1.0.0")

# 模拟产品数据
products_db = {
    "1": {"id": "1", "name": "智能手表", "category": "电子产品", "price": 1299.00, "stock": 50},
    "2": {"id": "2", "name": "无线耳机", "category": "电子产品", "price": 599.00, "stock": 120},
    "3": {"id": "3", "name": "运动鞋", "category": "服装", "price": 299.00, "stock": 200},
    "4": {"id": "4", "name": "咖啡机", "category": "家电", "price": 2199.00, "stock": 30},
}


# 数据模型
class Product(BaseModel):
    id: str
    name: str
    category: str
    price: float
    stock: int


class CreateProduct(BaseModel):
    name: str
    category: str
    price: float
    stock: int


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
            "description": "产品管理微服务",
            "features": ["CRUD", "库存管理", "分类查询"],
            "startup_time": datetime.now().isoformat(),
        },
        "tags": ["product", "inventory", "catalog"],
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

        await asyncio.sleep(30)


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


@app.get("/api/products", response_model=list[Product])
async def get_products(category: str = None):
    """获取所有产品或按分类筛选"""
    products = list(products_db.values())

    if category:
        products = [p for p in products if p["category"] == category]

    return products


@app.get("/api/products/{product_id}", response_model=Product)
async def get_product(product_id: str):
    """获取指定产品"""
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="产品不存在")
    return products_db[product_id]


@app.post("/api/products", response_model=Product)
async def create_product(product_data: CreateProduct):
    """创建新产品"""
    new_id = str(max(int(pid) for pid in products_db.keys()) + 1)
    new_product = Product(
        id=new_id,
        name=product_data.name,
        category=product_data.category,
        price=product_data.price,
        stock=product_data.stock,
    )
    products_db[new_id] = new_product
    return new_product


@app.put("/api/products/{product_id}", response_model=Product)
async def update_product(product_id: str, product_data: CreateProduct):
    """更新产品信息"""
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="产品不存在")

    products_db[product_id] = Product(
        id=product_id,
        name=product_data.name,
        category=product_data.category,
        price=product_data.price,
        stock=product_data.stock,
    )
    return products_db[product_id]


@app.delete("/api/products/{product_id}")
async def delete_product(product_id: str):
    """删除产品"""
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="产品不存在")

    del products_db[product_id]
    return {"message": "产品删除成功"}


@app.get("/api/products/{product_id}/inventory")
async def get_product_inventory(product_id: str):
    """获取产品库存信息"""
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="产品不存在")

    product = products_db[product_id]
    return {
        "product": product,
        "inventory": {
            "current_stock": product["stock"],
            "reserved": int(product["stock"] * 0.1),  # 模拟预留库存
            "available": int(product["stock"] * 0.9),
            "reorder_level": 20,
            "last_updated": datetime.now().isoformat(),
        },
        "supplier": "示例供应商",
        "delivery_time": "2-3天",
    }


@app.get("/api/categories")
async def get_categories():
    """获取所有产品分类"""
    categories = list({product["category"] for product in products_db.values()})
    return {"categories": sorted(categories)}


# ==================== 生命周期事件 ====================


@app.on_event("startup")
async def startup_event():
    """服务启动事件"""
    logger.info(f"启动 {SERVICE_NAME} (实例ID: {instance_id})")

    # 等待一段时间确保API Gateway已启动
    await asyncio.sleep(7)

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
    logger.info("服务关闭完成")


# ==================== 主函数 ====================

if __name__ == "__main__":
    logger.info(f"启动 {SERVICE_NAME} 在 {SERVICE_HOST}:{SERVICE_PORT}")

    uvicorn.run(
        "product_service:app", host=SERVICE_HOST, port=SERVICE_PORT, reload=True, log_level="info"
    )
