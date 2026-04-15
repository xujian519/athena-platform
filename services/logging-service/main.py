#!/usr/bin/env python3
"""
Athena统一日志服务
Athena Unified Logging Service
提供集中式日志收集、处理和分析功能
"""

import asyncio
import gzip
import json
import logging
import os
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any

import aiofiles
import redis
import uvicorn
from elasticsearch import AsyncElasticsearch
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from core.logging_config import setup_logging
from core.security.auth import ALLOWED_ORIGINS

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

class LogLevel(str, Enum):
    """日志级别"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogSource(str, Enum):
    """日志来源"""
    APPLICATION = "application"
    SYSTEM = "system"
    ACCESS = "access"
    ERROR = "error"
    AUDIT = "audit"

@dataclass
class LogEntry:
    """日志条目"""
    timestamp: datetime
    level: LogLevel
    service: str
    message: str
    source: LogSource
    trace_id: str | None = None
    span_id: str | None = None
    user_id: str | None = None
    request_id: str | None = None
    metadata: dict[str, Any] = None
    exception: dict[str, Any] | None = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class LogRequest(BaseModel):
    """日志请求"""
    level: LogLevel
    service: str
    message: str
    source: LogSource = LogSource.APPLICATION
    trace_id: str | None = None
    span_id: str | None = None
    user_id: str | None = None
    request_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

class LogQuery(BaseModel):
    """日志查询"""
    service: str | None = None
    level: LogLevel | None = None
    source: LogSource | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    search: str | None = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)

class LoggingService:
    """日志服务实现"""

    def __init__(self):
        self.redis_client: redis.Redis | None = None
        self.elasticsearch: AsyncElasticsearch | None = None
        self.log_buffer: deque = deque(maxlen=10000)
        self.file_storage_path = Path("./data/logs")
        self.file_storage_path.mkdir(parents=True, exist_ok=True)
        self.log_file_handlers: dict[str, object] = {}
        self.compression_enabled = True
        self.retention_days = 30

    async def initialize(self):
        """初始化日志服务"""
        try:
            # 初始化Redis连接（用于实时日志缓存）
            self.redis_client = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", 6379)),
                password=os.getenv("REDIS_PASSWORD"),
                db=1,  # 使用专门的日志数据库
                decode_responses=True
            )

            self.redis_client.ping()
            logger.info("Redis连接成功")

        except Exception as e:
            logger.warning(f"Redis连接失败: {e}")
            self.redis_client = None

        try:
            # 初始化Elasticsearch连接（用于日志搜索和分析）
            self.elasticsearch = AsyncElasticsearch(
                hosts=[os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")],
                http_auth=(
                    os.getenv("ELASTICSEARCH_USER"),
                    os.getenv("ELASTICSEARCH_PASSWORD")
                ) if os.getenv("ELASTICSEARCH_USER") else None
            )

            # 创建索引模板
            await self._create_index_template()
            logger.info("Elasticsearch连接成功")

        except Exception as e:
            logger.warning(f"Elasticsearch连接失败: {e}")
            self.elasticsearch = None

        # 启动后台任务
        asyncio.create_task(self._flush_logs_periodically())
        asyncio.create_task(self._cleanup_old_logs())

        logger.info("日志服务初始化完成")

    async def _create_index_template(self):
        """创建Elasticsearch索引模板"""
        if not self.elasticsearch:
            return

        template = {
            "index_patterns": ["athena-logs-*"],
            "template": {
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                    "index.refresh_interval": "5s"
                },
                "mappings": {
                    "properties": {
                        "timestamp": {"type": "date"},
                        "level": {"type": "keyword"},
                        "service": {"type": "keyword"},
                        "message": {"type": "text"},
                        "source": {"type": "keyword"},
                        "trace_id": {"type": "keyword"},
                        "span_id": {"type": "keyword"},
                        "user_id": {"type": "keyword"},
                        "request_id": {"type": "keyword"},
                        "metadata": {"type": "object"},
                        "exception": {"type": "object"}
                    }
                }
            }
        }

        await self.elasticsearch.indices.put_index_template(
            name="athena_logs_template",
            body=template
        )

    async def log(self, log_request: LogRequest):
        """记录日志"""
        log_entry = LogEntry(
            timestamp=datetime.now(timezone.utc),
            level=log_request.level,
            service=log_request.service,
            message=log_request.message,
            source=log_request.source,
            trace_id=log_request.trace_id,
            span_id=log_request.span_id,
            user_id=log_request.user_id,
            request_id=log_request.request_id,
            metadata=log_request.metadata
        )

        # 添加到缓冲区
        self.log_buffer.append(log_entry)

        # 如果是错误级别，立即处理
        if log_request.level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            await self._process_log_entry(log_entry)

        # 存储到Redis（实时查询）
        if self.redis_client:
            await self._store_to_redis(log_entry)

    async def _process_log_entry(self, log_entry: LogEntry):
        """处理单个日志条目"""
        # 写入文件
        await self._write_to_file(log_entry)

        # 存储到Elasticsearch
        if self.elasticsearch:
            await self._store_to_elasticsearch(log_entry)

    async def _write_to_file(self, log_entry: LogEntry):
        """写入日志文件"""
        service = log_entry.service
        date_str = log_entry.timestamp.strftime("%Y-%m-%d")

        # 获取或创建文件处理器
        file_key = f"{service}_{date_str}"
        if file_key not in self.log_file_handlers:
            log_file = self.file_storage_path / service / f"{date_str}.log"
            log_file.parent.mkdir(parents=True, exist_ok=True)

            self.log_file_handlers[file_key] = {
                'file': log_file,
                'last_flush': datetime.now()
            }

        # 写入日志
        handler = self.log_file_handlers[file_key]
        log_line = json.dumps({
            "timestamp": log_entry.timestamp.isoformat(),
            "level": log_entry.level.value,
            "service": log_entry.service,
            "message": log_entry.message,
            "source": log_entry.source.value,
            "trace_id": log_entry.trace_id,
            "span_id": log_entry.span_id,
            "user_id": log_entry.user_id,
            "request_id": log_entry.request_id,
            "metadata": log_entry.metadata,
            "exception": log_entry.exception
        }, ensure_ascii=False)

        async with aiofiles.open(handler['file'], 'a') as f:
            await f.write(log_line + '\n')

        handler['last_flush'] = datetime.now()

    async def _store_to_redis(self, log_entry: LogEntry):
        """存储到Redis"""
        try:
            # 使用管道提高性能
            pipe = self.redis_client.pipeline()

            # 存储最新日志（用于实时监控）
            recent_key = f"logs:recent:{log_entry.service}"
            pipe.lpush(recent_key, json.dumps(asdict(log_entry), default=str))
            pipe.ltrim(recent_key, 0, 999)  # 只保留最近1000条

            # 存储错误日志（单独索引）
            if log_entry.level in [LogLevel.ERROR, LogLevel.CRITICAL]:
                error_key = f"logs:errors:{log_entry.service}"
                pipe.lpush(error_key, json.dumps(asdict(log_entry), default=str))
                pipe.ltrim(error_key, 0, 999)

            # 设置过期时间（7天）
            pipe.expire(recent_key, 604800)
            pipe.expire(error_key, 604800)

            await pipe.execute()

        except Exception as e:
            logger.error(f"存储到Redis失败: {e}")

    async def _store_to_elasticsearch(self, log_entry: LogEntry):
        """存储到Elasticsearch"""
        try:
            index_name = f"athena-logs-{log_entry.timestamp.strftime('%Y-%m')}"
            await self.elasticsearch.index(
                index=index_name,
                body=asdict(log_entry, default=str)
            )
        except Exception as e:
            logger.error(f"存储到Elasticsearch失败: {e}")

    async def query_logs(self, query: LogQuery) -> dict[str, Any]:
        """查询日志"""
        # 如果有Elasticsearch，使用其搜索功能
        if self.elasticsearch:
            return await self._query_elasticsearch(query)

        # 否则从文件查询
        return await self._query_files(query)

    async def _query_elasticsearch(self, query: LogQuery) -> dict[str, Any]:
        """从Elasticsearch查询"""
        index_pattern = "athena-logs-*"

        # 构建查询
        search_body = {
            "query": {"bool": {"must": []}},
            "sort": [{"timestamp": {"order": "desc"}}],
            "from": query.offset,
            "size": query.limit
        }

        # 添加过滤条件
        if query.service:
            search_body["query"]["bool"]["must"].append(
                {"term": {"service": query.service}}
            )

        if query.level:
            search_body["query"]["bool"]["must"].append(
                {"term": {"level": query.level.value}}
            )

        if query.source:
            search_body["query"]["bool"]["must"].append(
                {"term": {"source": query.source.value}}
            )

        if query.start_time or query.end_time:
            time_range = {}
            if query.start_time:
                time_range["gte"] = query.start_time.isoformat()
            if query.end_time:
                time_range["lte"] = query.end_time.isoformat()
            search_body["query"]["bool"]["must"].append(
                {"range": {"timestamp": time_range}}
            )

        if query.search:
            search_body["query"]["bool"]["must"].append(
                {"multi_match": {"query": query.search, "fields": ["message"]}}
            )

        try:
            response = await self.elasticsearch.search(
                index=index_pattern,
                body=search_body
            )

            hits = response["hits"]["hits"]
            logs = [hit["_source"] for hit in hits]

            return {
                "logs": logs,
                "total": response["hits"]["total"]["value"],
                "query": query.dict(),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Elasticsearch查询失败: {e}")
            return {"logs": [], "total": 0, "error": str(e)}

    async def _query_files(self, query: LogQuery) -> dict[str, Any]:
        """从文件查询（简化实现）"""
        # 这是一个简化的实现，实际应该遍历文件并解析
        logs = []

        # 从缓冲区查询最近的日志
        buffer_logs = list(self.log_buffer)
        for log_entry in buffer_logs:
            if self._matches_query(log_entry, query):
                logs.append(asdict(log_entry, default=str))

        return {
            "logs": logs[query.offset:query.offset + query.limit],
            "total": len(logs),
            "query": query.dict(),
            "timestamp": datetime.now().isoformat()
        }

    def _matches_query(self, log_entry: LogEntry, query: LogQuery) -> bool:
        """检查日志条目是否匹配查询"""
        if query.service and log_entry.service != query.service:
            return False

        if query.level and log_entry.level != query.level:
            return False

        if query.source and log_entry.source != query.source:
            return False

        if query.start_time and log_entry.timestamp < query.start_time:
            return False

        if query.end_time and log_entry.timestamp > query.end_time:
            return False

        if query.search and query.search.lower() not in log_entry.message.lower():
            return False

        return True

    async def get_log_stats(self) -> dict[str, Any]:
        """获取日志统计"""
        stats = {
            "total_logs": 0,
            "by_level": defaultdict(int),
            "by_service": defaultdict(int),
            "by_source": defaultdict(int),
            "recent_errors": 0,
            "timestamp": datetime.now().isoformat()
        }

        # 统计缓冲区中的日志
        for log_entry in self.log_buffer:
            stats["total_logs"] += 1
            stats["by_level"][log_entry.level.value] += 1
            stats["by_service"][log_entry.service] += 1
            stats["by_source"][log_entry.source.value] += 1

            if log_entry.level in [LogLevel.ERROR, LogLevel.CRITICAL]:
                stats["recent_errors"] += 1

        # 从Redis获取统计
        if self.redis_client:
            try:
                # 获取各服务的错误数量
                for service in stats["by_service"]:
                    error_count = self.redis_client.llen(f"logs:errors:{service}")
                    if error_count > 0:
                        stats[f"errors_{service}"] = error_count
            except Exception as e:
                logger.error(f"获取Redis统计失败: {e}")

        return stats

    async def _flush_logs_periodically(self):
        """定期刷新日志"""
        while True:
            try:
                await asyncio.sleep(60)  # 每分钟刷新一次

                # 处理缓冲区中的日志
                while self.log_buffer:
                    log_entry = self.log_buffer.popleft()
                    await self._process_log_entry(log_entry)

                logger.debug("日志刷新完成")

            except Exception as e:
                logger.error(f"日志刷新失败: {e}")

    async def _cleanup_old_logs(self):
        """清理旧日志"""
        while True:
            try:
                await asyncio.sleep(86400)  # 每天执行一次

                # 压缩旧日志文件
                if self.compression_enabled:
                    await self._compress_old_logs()

                # 删除过期日志
                await self._delete_expired_logs()

                logger.info("日志清理完成")

            except Exception as e:
                logger.error(f"日志清理失败: {e}")

    async def _compress_old_logs(self):
        """压缩旧日志文件"""
        cutoff_date = datetime.now() - timedelta(days=7)

        for service_dir in self.file_storage_path.iterdir():
            if service_dir.is_dir():
                for log_file in service_dir.glob("*.log"):
                    # 从文件名提取日期
                    try:
                        date_str = log_file.stem
                        file_date = datetime.strptime(date_str, "%Y-%m-%d")

                        if file_date < cutoff_date:
                            # 压缩文件
                            compressed_file = log_file.with_suffix('.log.gz')
                            with open(log_file, 'rb') as f_in:
                                with gzip.open(compressed_file, 'wb') as f_out:
                                    f_out.writelines(f_in)

                            # 删除原文件
                            log_file.unlink()
                            logger.info(f"压缩日志文件: {log_file}")

                    except ValueError:
                        continue

    async def _delete_expired_logs(self):
        """删除过期日志"""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)

        for service_dir in self.file_storage_path.iterdir():
            if service_dir.is_dir():
                for log_file in service_dir.glob("*.log.gz"):
                    try:
                        # 获取文件修改时间
                        mtime = datetime.fromtimestamp(log_file.stat().st_mtime)

                        if mtime < cutoff_date:
                            log_file.unlink()
                            logger.info(f"删除过期日志: {log_file}")

                    except Exception as e:
                        logger.error(f"删除日志文件失败 {log_file}: {e}")

# 创建日志服务实例
logging_service = LoggingService()

# 创建FastAPI应用
app = FastAPI(
    title="Athena Logging Service",
    description="Athena平台统一日志服务",
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
    logger.info("启动Athena日志服务")
    await logging_service.initialize()

@app.on_event("shutdown")
async def shutdown_event():
    """关闭时清理"""
    logger.info("正在关闭日志服务")
    if logging_service.redis_client:
        logging_service.redis_client.close()
    if logging_service.elasticsearch:
        await logging_service.close()

# API端点
@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "Athena Logging Service",
        "version": "1.0.0",
        "status": "running",
        "storage": {
            "redis": "connected" if logging_service.redis_client else "disconnected",
            "elasticsearch": "connected" if logging_service.elasticsearch else "disconnected",
            "file": "enabled"
        },
        "buffer_size": len(logging_service.log_buffer),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health():
    """健康检查"""
    redis_status = "connected"
    if logging_service.redis_client:
        try:
            logging_service.redis_client.ping()
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            redis_status = "disconnected"

    es_status = "connected"
    if logging_service.elasticsearch:
        try:
            await logging_service.ping()
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            es_status = "disconnected"

    return {
        "status": "healthy",
        "storage": {
            "redis": redis_status,
            "elasticsearch": es_status,
            "file": "ok"
        },
        "buffer_size": len(logging_service.log_buffer),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/logs")
async def create_log(log_request: LogRequest):
    """记录日志"""
    await logging_service.log(log_request)
    return {"message": "日志记录成功", "timestamp": datetime.now().isoformat()}

@app.post("/api/v1/logs/batch")
async def batch_create_logs(logs: list[LogRequest]):
    """批量记录日志"""
    for log in logs:
        await logging_service.log(log)
    return {
        "message": f"成功记录 {len(logs)} 条日志",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/logs/query")
async def query_logs(query: LogQuery):
    """查询日志"""
    result = await logging_service.query_logs(query)
    return result

@app.get("/api/v1/logs/stats")
async def get_log_stats():
    """获取日志统计"""
    return await logging_service.get_log_stats()

# 中间件：自动记录访问日志
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录请求日志"""
    start_time = datetime.now()

    # 记录请求开始
    log_request = LogRequest(
        level=LogLevel.INFO,
        service="logging-service",
        message=f"{request.method} {request.url.path}",
        source=LogSource.ACCESS,
        request_id=request.headers.get("X-Request-ID"),
        metadata={
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers),
            "client": request.client.host if request.client else None
        }
    )
    await logging_service.log(log_request)

    # 处理请求
    response = await call_next(request)

    # 记录响应
    processing_time = (datetime.now() - start_time).total_seconds()
    log_request = LogRequest(
        level=LogLevel.INFO,
        service="logging-service",
        message=f"{request.method} {request.url.path} - {response.status_code}",
        source=LogSource.ACCESS,
        request_id=request.headers.get("X-Request-ID"),
        metadata={
            "method": request.method,
            "url": str(request.url),
            "status_code": response.status_code,
            "processing_time": processing_time
        }
    )
    await logging_service.log(log_request)

    return response

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8010,
        reload=False
    )
