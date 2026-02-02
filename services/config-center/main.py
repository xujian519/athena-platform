#!/usr/bin/env python3
"""
Athena配置中心服务
Athena Configuration Center Service
提供统一的配置管理和动态配置更新功能
"""

import logging
from core.async_main import async_main
from core.logging_config import setup_logging
import os
import json
import yaml
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass, asdict

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from core.security.auth import ALLOWED_ORIGINS
from pydantic import BaseModel, Field
import redis
import asyncio
import uvicorn

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

@dataclass
class ConfigItem:
    """配置项"""
    key: str
    value: Any
    type: str = "string"  # string, number, boolean, json, yaml
    description: str = ""
    tags: List[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    version: int = 1

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if self.tags is None:
            self.tags = []

class ConfigRequest(BaseModel):
    """配置请求"""
    key: str = Field(..., description="配置键")
    value: Any = Field(..., description="配置值")
    type: str = Field("string", description="配置类型")
    description: str = Field("", description="配置描述")
    tags: List[str] = Field(default_factory=list, description="配置标签")

class ConfigResponse(BaseModel):
    """配置响应"""
    key: str
    value: Any
    type: str
    description: str
    tags: List[str]
    version: int
    updated_at: datetime

class ConfigCenter:
    """配置中心实现"""

    def __init__(self):
        self.redis_client: redis.Redis | None = None
        self.file_storage_path = Path("./data/configs")
        self.file_storage_path.mkdir(parents=True, exist_ok=True)
        self.config_cache: Dict[str, ConfigItem] = {}
        self.watchers: Dict[str, List[callable]] = {}

    async def initialize(self):
        """初始化配置中心"""
        try:
            # 初始化Redis连接
            self.redis_client = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", 6379)),
                password=os.getenv("REDIS_PASSWORD"),
                db=0,
                decode_responses=True
            )

            # 测试连接
            self.redis_client.ping()
            logger.info("Redis连接成功")

        except Exception as e:
            logger.warning(f"Redis连接失败，使用文件存储: {e}")
            self.redis_client = None

        # 加载现有配置
        await self._load_existing_configs()

        logger.info("配置中心初始化完成")

    async def _load_existing_configs(self):
        """加载现有配置"""
        # 从文件加载
        for config_file in self.file_storage_path.glob("*.json"):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    config = ConfigItem(**data)
                    self.config_cache[config.key] = config
            except Exception as e:
                logger.error(f"加载配置文件失败 {config_file}: {e}")

        # 从Redis加载
        if self.redis_client:
            try:
                keys = self.redis_client.keys("config:*")
                for key in keys:
                    data = self.redis_client.hgetall(key)
                    if data:
                        config = ConfigItem(
                            key=data['key'],
                            value=json.loads(data['value']),
                            type=data['type'],
                            description=data['description'],
                            tags=json.loads(data['tags']),
                            version=int(data['version']),
                            created_at=datetime.fromisoformat(data['created_at']),
                            updated_at=datetime.fromisoformat(data['updated_at'])
                        )
                        self.config_cache[config.key] = config
            except Exception as e:
                logger.error(f"从Redis加载配置失败: {e}")

        logger.info(f"加载了 {len(self.config_cache)} 个配置项")

    async def set_config(self, key: str, value: Any, config_type: str = "string",
                         description: str = "", tags: List[str] = None) -> bool:
        """设置配置"""
        try:
            # 检查是否已存在
            existing = self.config_cache.get(key)
            version = (existing.version + 1) if existing else 1

            # 创建配置项
            config = ConfigItem(
                key=key,
                value=value,
                type=config_type,
                description=description,
                tags=tags or [],
                version=version,
                updated_at=datetime.now()
            )

            # 保存到缓存
            self.config_cache[key] = config

            # 保存到Redis
            if self.redis_client:
                redis_key = f"config:{key}"
                self.redis_client.hset(redis_key, mapping={
                    'key': key,
                    'value': json.dumps(value),
                    'type': config_type,
                    'description': description,
                    'tags': json.dumps(tags or []),
                    'version': str(version),
                    'created_at': config.created_at.isoformat(),
                    'updated_at': config.updated_at.isoformat()
                })
                self.redis_client.expire(redis_key, 86400 * 30)  # 30天过期

            # 保存到文件
            config_file = self.file_storage_path / f"{key.replace('/', '_')}.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(config), f, ensure_ascii=False, indent=2, default=str)

            # 通知观察者
            await self._notify_watchers(key, config)

            logger.info(f"配置设置成功: {key} (版本: {version})")
            return True

        except Exception as e:
            logger.error(f"设置配置失败 {key}: {e}")
            return False

    async def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置"""
        config = self.config_cache.get(key)
        return config.value if config else default

    async def get_config_item(self, key: str) -> ConfigItem | None:
        """获取配置项详情"""
        return self.config_cache.get(key)

    async def delete_config(self, key: str) -> bool:
        """删除配置"""
        try:
            if key in self.config_cache:
                # 从缓存删除
                del self.config_cache[key]

                # 从Redis删除
                if self.redis_client:
                    self.redis_client.delete(f"config:{key}")

                # 从文件删除
                config_file = self.file_storage_path / f"{key.replace('/', '_')}.json"
                if config_file.exists():
                    config_file.unlink()

                # 通知观察者
                await self._notify_watchers(key, None)

                logger.info(f"配置删除成功: {key}")
                return True

            return False

        except Exception as e:
            logger.error(f"删除配置失败 {key}: {e}")
            return False

    async def list_configs(self, prefix: str = None, tags: List[str] = None) -> List[ConfigItem]:
        """列出配置"""
        configs = list(self.config_cache.values())

        # 按前缀过滤
        if prefix:
            configs = [c for c in configs if c.key.startswith(prefix)]

        # 按标签过滤
        if tags:
            configs = [c for c in configs if any(tag in c.tags for tag in tags)]

        return configs

    async def watch_config(self, key: str, callback: callable):
        """监听配置变化"""
        if key not in self.watchers:
            self.watchers[key] = []
        self.watchers[key].append(callback)
        logger.info(f"注册配置监听: {key}")

    async def unwatch_config(self, key: str, callback: callable):
        """取消监听配置"""
        if key in self.watchers:
            try:
                self.watchers[key].remove(callback)
                if not self.watchers[key]:
                    del self.watchers[key]
                logger.info(f"取消配置监听: {key}")
            except ValueError:
                logger.error(f"Error: {e}", exc_info=True)

    async def _notify_watchers(self, key: str, config: Optional[ConfigItem]):
        """通知配置观察者"""
        if key in self.watchers:
            for callback in self.watchers[key]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(key, config)
                    else:
                        callback(key, config)
                except Exception as e:
                    logger.error(f"配置监听器回调失败 {key}: {e}")

    async def export_configs(self, format: str = "json") -> str:
        """导出所有配置"""
        configs = [asdict(c) for c in self.config_cache.values()]

        if format == "json":
            return json.dumps(configs, ensure_ascii=False, indent=2, default=str)
        elif format == "yaml":
            return yaml.dump(configs, default_flow_style=False, allow_unicode=True)
        else:
            raise ValueError(f"不支持的导出格式: {format}")

    async def import_configs(self, config_data: str, format: str = "json"):
        """导入配置"""
        try:
            if format == "json":
                configs = json.loads(config_data)
            elif format == "yaml":
                configs = yaml.safe_load(config_data)
            else:
                raise ValueError(f"不支持的导入格式: {format}")

            for config_data in configs:
                await self.set_config(
                    key=config_data['key'],
                    value=config_data['value'],
                    config_type=config_data.get('type', 'string'),
                    description=config_data.get('description', ''),
                    tags=config_data.get('tags', [])
                )

            logger.info(f"成功导入 {len(configs)} 个配置")
            return True

        except Exception as e:
            logger.error(f"导入配置失败: {e}")
            return False

# 创建配置中心实例
config_center = ConfigCenter()

# 创建FastAPI应用
app = FastAPI(
    title="Athena Configuration Center",
    description="Athena平台配置中心服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 启动和关闭事件
@app.on_event("startup")
async def startup_event():
    """启动时初始化"""
    logger.info("启动Athena配置中心服务")
    await config_center.initialize()

@app.on_event("shutdown")
async def shutdown_event():
    """关闭时清理"""
    logger.info("正在关闭配置中心服务")
    if config_center.redis_client:
        config_center.redis_client.close()

# API端点
@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "Athena Configuration Center",
        "version": "1.0.0",
        "status": "running",
        "storage": {
            "redis": "connected" if config_center.redis_client else "disconnected",
            "file": "enabled"
        },
        "configs_count": len(config_center.config_cache),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health():
    """健康检查"""
    redis_status = "connected"
    if config_center.redis_client:
        try:
            config_center.redis_client.ping()
        except (FileNotFoundError, PermissionError, OSError):
            redis_status = "disconnected"

    return {
        "status": "healthy",
        "storage": {
            "redis": redis_status,
            "file": "ok"
        },
        "configs_loaded": len(config_center.config_cache),
        "timestamp": datetime.now().isoformat()
    }

# 配置管理端点
@app.post("/api/v1/configs", response_model=ConfigResponse)
async def create_config(request: ConfigRequest):
    """创建配置"""
    success = await config_center.set_config(
        key=request.key,
        value=request.value,
        config_type=request.type,
        description=request.description,
        tags=request.tags
    )

    if success:
        config = await config_center.get_config_item(request.key)
        return ConfigResponse(
            key=config.key,
            value=config.value,
            type=config.type,
            description=config.description,
            tags=config.tags,
            version=config.version,
            updated_at=config.updated_at
        )
    else:
        raise HTTPException(status_code=500, detail="创建配置失败")

@app.get("/api/v1/configs/{key}", response_model=ConfigResponse)
async def get_config(key: str):
    """获取配置"""
    config = await config_center.get_config_item(key)
    if config:
        return ConfigResponse(
            key=config.key,
            value=config.value,
            type=config.type,
            description=config.description,
            tags=config.tags,
            version=config.version,
            updated_at=config.updated_at
        )
    else:
        raise HTTPException(status_code=404, detail=f"配置不存在: {key}")

@app.put("/api/v1/configs/{key}", response_model=ConfigResponse)
async def update_config(key: str, request: ConfigRequest):
    """更新配置"""
    if key != request.key:
        raise HTTPException(status_code=400, detail="路径中的key与请求体中的key不匹配")

    success = await config_center.set_config(
        key=key,
        value=request.value,
        config_type=request.type,
        description=request.description,
        tags=request.tags
    )

    if success:
        config = await config_center.get_config_item(key)
        return ConfigResponse(
            key=config.key,
            value=config.value,
            type=config.type,
            description=config.description,
            tags=config.tags,
            version=config.version,
            updated_at=config.updated_at
        )
    else:
        raise HTTPException(status_code=500, detail="更新配置失败")

@app.delete("/api/v1/configs/{key}")
async def delete_config(key: str):
    """删除配置"""
    success = await config_center.delete_config(key)
    if success:
        return {"message": f"配置删除成功: {key}"}
    else:
        raise HTTPException(status_code=404, detail=f"配置不存在: {key}")

@app.get("/api/v1/configs")
async def list_configs(prefix: str = None, tags: str = None):
    """列出配置"""
    tag_list = tags.split(',') if tags else None
    configs = await config_center.list_configs(prefix=prefix, tags=tag_list)

    return {
        "configs": [
            {
                "key": c.key,
                "type": c.type,
                "description": c.description,
                "tags": c.tags,
                "version": c.version,
                "updated_at": c.updated_at
            }
            for c in configs
        ],
        "total": len(configs),
        "timestamp": datetime.now().isoformat()
    }

# 批量操作
@app.post("/api/v1/configs/batch")
async def batch_set_configs(configs: List[ConfigRequest]):
    """批量设置配置"""
    results = []
    for config in configs:
        success = await config_center.set_config(
            key=config.key,
            value=config.value,
            config_type=config.type,
            description=config.description,
            tags=config.tags
        )
        results.append({"key": config.key, "success": success})

    success_count = sum(1 for r in results if r["success"])

    return {
        "results": results,
        "success_count": success_count,
        "total": len(configs),
        "timestamp": datetime.now().isoformat()
    }

# 导入导出
@app.post("/api/v1/configs/import")
async def import_configs(background_tasks: BackgroundTasks):
    """导入配置"""
    # 这里应该接收上传的文件
    # 简化实现，返回上传说明
    return {
        "message": "请使用 multipart/form-data 上传配置文件",
        "endpoint": "/api/v1/configs/upload",
        "formats": ["json", "yaml"]
    }

@app.post("/api/v1/configs/upload")
async def upload_configs(background_tasks: BackgroundTasks, file):
    """上传并导入配置文件"""
    content = await file.read()
    filename = file.filename

    # 确定格式
    format = "json" if filename.endswith('.json') else "yaml" if filename.endswith('.yml') or filename.endswith('.yaml') else None

    if not format:
        raise HTTPException(status_code=400, detail="不支持的文件格式")

    # 导入配置
    success = await config_center.import_configs(content.decode('utf-8'), format)

    if success:
        return {"message": "配置导入成功"}
    else:
        raise HTTPException(status_code=500, detail="配置导入失败")

@app.get("/api/v1/configs/export")
async def export_configs(format: str = "json"):
    """导出配置"""
    if format not in ["json", "yaml"]:
        raise HTTPException(status_code=400, detail="不支持的导出格式")

    content = await config_center.export_configs(format)

    from fastapi.responses import Response
    return Response(
        content=content,
        media_type="application/json" if format == "json" else "application/x-yaml",
        headers={"Content-Disposition": f"attachment; filename=configs.{format}"}
    )

# 监听端点
@app.post("/api/v1/configs/{key}/watch")
async def watch_config(key: str, callback_url: str):
    """监听配置变化（通过回调URL）"""
    async def callback_handler(config_key, config):
        if config:
            # 发送HTTP回调
            async with httpx.AsyncClient() as client:
                await client.post(
                    callback_url,
                    json={
                        "key": config_key,
                        "value": config.value,
                        "version": config.version,
                        "updated_at": config.updated_at.isoformat()
                    }
                )

    await config_center.watch_config(key, callback_handler)
    return {"message": f"已注册监听: {key}"}

# 统计信息
@app.get("/api/v1/stats")
async def get_stats():
    """获取统计信息"""
    # 统计配置类型分布
    type_counts = {}
    tag_counts = {}

    for config in config_center.config_cache.values():
        type_counts[config.type] = type_counts.get(config.type, 0) + 1
        for tag in config.tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    return {
        "total_configs": len(config_center.config_cache),
        "type_distribution": type_counts,
        "tag_distribution": tag_counts,
        "storage": {
            "redis": "connected" if config_center.redis_client else "disconnected",
            "file": "enabled"
        },
        "watchers": len(config_center.watchers),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8009,
        reload=False
    )