#!/usr/bin/env python3
"""
⚠️  DEPRECATED - NebulaGraph版本已废弃，需要更新
DEPRECATED - NebulaGraph version deprecated, needs update

废弃日期: 2026-01-26
废弃原因: TD-001 - 系统已迁移到Neo4j
影响范围: 整个文件
建议操作: 创建Neo4j版本的同步服务，替换SessionPool为GraphDatabase.driver

原功能说明:
实时数据同步服务
Real-time Sync Service for pgvector + NebulaGraph Integration

作者: 小诺·双鱼公主
创建时间: 2025-12-28
更新时间: 2026-01-26 (TD-001: 标记需要更新)
"""

from __future__ import annotations
import asyncio
import json
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import asyncpg
from nebula3.gclient.net.SessionPool import SessionPool

from core.async_main import async_main

# 安全工具导入
from core.database.safe_query import SafeQueryBuilder
from core.database.unified_connection import get_postgres_pool
from core.logging_config import setup_logging

logger = setup_logging()


class SyncDirection(Enum):
    """同步方向"""

    PG_TO_KG = "pg_to_kg"
    KG_TO_PG = "kg_to_pg"
    BIDIRECTIONAL = "bidirectional"


class SyncStatus(Enum):
    """同步状态"""

    PENDING = "pending"
    PROCESSING = "processing"
    SYNCED = "synced"
    FAILED = "failed"
    CONFLICT = "conflict"


class ChangeEventType(Enum):
    """变更事件类型"""

    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"


@dataclass
class ChangeEvent:
    """变更事件"""

    event_id: str
    event_type: ChangeEventType
    source: str  # 'pgvector' or 'nebula'
    entity_id: str
    entity_type: str
    business_key: str
    data: dict[str, Any]
    old_data: dict[str, Any] | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


class RealtimeSyncService:
    """实时同步服务"""

    def __init__(
        self,
        pg_config: dict[str, Any],        nebula_config: dict[str, Any],        sync_config: dict[str, Any] | None = None,
    ):
        """初始化同步服务"""
        self.pg_config = pg_config
        self.nebula_config = nebula_config
        self.sync_config = sync_config or {}

        # 连接池
        self.pg_pool: asyncpg.Pool | None = None
        self.nebula_pool: SessionPool | None = None

        # 状态管理
        self.is_running = False
        self.sync_stats = {
            "total_events": 0,
            "synced_events": 0,
            "failed_events": 0,
            "conflict_events": 0,
            "avg_latency_ms": 0.0,
            "last_sync_time": None,
        }

        # 事件队列
        self.event_queue: asyncio.Queue = None
        self.pending_syncs: set[str] = set()

        # 重试队列
        self.retry_queue: asyncio.Queue = None

    async def initialize(self):
        """初始化同步服务"""
        logger.info("🚀 初始化实时同步服务...")

        # 初始化事件队列
        self.event_queue = asyncio.Queue(maxsize=10000)
        self.retry_queue = asyncio.Queue(maxsize=1000)

        # 初始化 PostgreSQL 连接池
        # 要求必须提供密码,不使用默认值
        pg_password = self.pg_config.get("password")
        if not pg_password:
            raise ValueError("PostgreSQL密码未配置,请在pg_config中提供password字段")

        self.pg_db = await get_postgres_pool(
            host=self.pg_config.get("host", "localhost"),
            port=self.pg_config.get("port", 5438),
            user=self.pg_config.get("user", "postgres"),
            password=pg_password,
            database=self.pg_config.get("database", "agent_memory_db"),
            min_size=5,
            max_size=20,
        )
        logger.info("✅ PostgreSQL 连接池已初始化")

        # 初始化 NebulaGraph 连接池
        # 要求必须提供密码,不使用默认值
        nebula_password = self.nebula_config.get("password")
        if not nebula_password:
            raise ValueError("NebulaGraph密码未配置,请在nebula_config中提供password字段")

        self.nebula_pool = SessionPool(
            username=self.nebula_config.get("username", "root"),
            password=nebula_password,
            space_name=self.nebula_config.get("space", "vgraph_unified_space"),
            addresses=[
                (self.nebula_config.get("host", "localhost"), self.nebula_config.get("port", 9669))
            ],
        )
        await self.nebula_pool.init(None)
        logger.info("✅ NebulaGraph 连接池已初始化")

        # 启动同步处理器
        asyncio.create_task(self._process_sync_events())
        asyncio.create_task(self._process_retry_events())

        self.is_running = True
        logger.info("✅ 实时同步服务初始化完成")

    async def start_pg_cdc_listener(self):
        """启动 pgvector CDC 监听器"""
        logger.info("🔍 启动 pgvector CDC 监听器...")

        while self.is_running:
            try:
                # 使用 PostgreSQL LISTEN/NOTIFY 机制
                async with self.pg_pool.acquire() as conn:
                    await conn.add_listener("vgraph_changes", self._on_pg_change_event)

                    # 保持监听
                    while self.is_running:
                        await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"❌ pgvector CDC 监听异常: {e}")
                await asyncio.sleep(5)  # 等待后重连

    async def _on_pg_change_event(self, connection, pid, channel, payload):
        """处理 pgvector 变更事件"""
        try:
            event_data = json.loads(payload)
            event = ChangeEvent(
                event_id=event_data.get("event_id", f"pg_{datetime.now().timestamp()}"),
                event_type=ChangeEventType(event_data["event_type"]),
                source="pgvector",
                entity_id=event_data["entity_id"],
                entity_type=event_data["entity_type"],
                business_key=event_data["business_key"],
                data=event_data["data"],
                old_data=event_data.get("old_data"),
            )

            # 发送到事件队列
            await self._publish_event(event)

        except Exception as e:
            logger.error(f"❌ 处理 pgvector 变更事件失败: {e}")

    async def start_nebula_cdc_listener(self):
        """启动 NebulaGraph CDC 监听器"""
        logger.info("🔍 启动 NebulaGraph CDC 监听器...")

        while self.is_running:
            try:
                # 定期查询待同步的 NebulaGraph 变更
                async with self.pg_pool.acquire() as conn:
                    # 查询待同步的 NebulaGraph 变更
                    rows = await conn.fetch("""
                        SELECT
                            entity_id,
                            entity_type,
                            business_key,
                            sync_direction
                        FROM vgraph_unified_mapping
                        WHERE sync_status = 'pending'
                          AND sync_direction IN ('kg_to_pg', 'bidirectional')
                        ORDER BY last_sync_time ASC
                        LIMIT 100
                    """)

                    for row in rows:
                        event = ChangeEvent(
                            event_id=f"nebula_{row['entity_id']}_{datetime.now().timestamp()}",
                            event_type=ChangeEventType.UPDATE,
                            source="nebula",
                            entity_id=str(row["entity_id"]),
                            entity_type=row["entity_type"],
                            business_key=row["business_key"],
                            data={"sync_direction": row["sync_direction"]},
                        )
                        await self._publish_event(event)

                await asyncio.sleep(10)  # 定期轮询

            except Exception as e:
                logger.error(f"❌ NebulaGraph CDC 监听异常: {e}")
                await asyncio.sleep(5)

    async def _publish_event(self, event: ChangeEvent):
        """发布事件到队列"""
        try:
            self.sync_stats["total_events"] += 1

            # 检查去重
            event_key = f"{event.source}_{event.entity_id}"
            if event_key in self.pending_syncs:
                logger.debug(f"⏭️  事件已处理中,跳过: {event_key}")
                return

            self.pending_syncs.add(event_key)

            # 添加到事件队列
            try:
                self.event_queue.put_nowait(event)
                logger.debug(f"📤 事件已入队: {event.event_type.value} - {event.entity_id}")
            except asyncio.QueueFull:
                logger.warning(f"⚠️  事件队列已满,事件丢失: {event.event_id}")

        except Exception as e:
            logger.error(f"❌ 发布事件失败: {e}")

    async def _process_sync_events(self):
        """处理同步事件"""
        logger.info("⚙️  启动同步事件处理器...")

        while self.is_running:
            try:
                # 从队列获取事件
                event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)

                # 处理事件
                await self._sync_entity(event)

                # 从待处理集合中移除
                event_key = f"{event.source}_{event.entity_id}"
                self.pending_syncs.discard(event_key)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"❌ 同步事件处理异常: {e}")
                traceback.print_exc()

    async def _sync_entity(self, event: ChangeEvent):
        """同步实体"""
        start_time = datetime.now()
        try:
            # 记录事件日志
            await self._log_sync_event(event, "processing")

            # 获取映射信息
            async with self.pg_pool.acquire() as conn:
                mapping = await conn.fetchrow(
                    """
                    SELECT
                        entity_id,
                        entity_type,
                        pgvector_table,
                        pgvector_id,
                        nebula_space,
                        nebula_vertex_id,
                        sync_direction
                    FROM vgraph_unified_mapping
                    WHERE entity_id = $1
                """,
                    event.entity_id,
                )

                if not mapping:
                    logger.warning(f"⚠️  未找到映射: {event.entity_id}")
                    return

                # 根据同步方向执行相应操作
                sync_direction = mapping["sync_direction"]

                if sync_direction in ["pg_to_kg", "bidirectional"]:
                    await self._sync_to_nebula(event, mapping)

                if sync_direction in ["kg_to_pg", "bidirectional"]:
                    await self._sync_to_pgvector(event, mapping)

                # 更新同步状态
                await conn.execute(
                    """
                    UPDATE vgraph_unified_mapping
                    SET sync_status = 'synced',
                        last_sync_time = CURRENT_TIMESTAMP,
                        sync_version = sync_version + 1
                    WHERE entity_id = $1
                """,
                    event.entity_id,
                )

                # 记录成功
                await self._log_sync_event(event, "synced")

                # 更新统计
                self.sync_stats["synced_events"] += 1
                latency = (datetime.now() - start_time).total_seconds() * 1000
                self._update_avg_latency(latency)
                self.sync_stats["last_sync_time"] = datetime.now().isoformat()

                logger.info(f"✅ 同步成功: {event.entity_id} ({latency:.2f}ms)")

            # 从待处理集合中移除
            event_key = f"{event.source}_{event.entity_id}"
            self.pending_syncs.discard(event_key)

        except Exception as e:
            logger.error(f"❌ 同步失败: {event.entity_id}, 错误: {e}")
            traceback.print_exc()

            # 记录失败
            await self._log_sync_event(event, "failed", str(e))

            # 加入重试队列
            if self.retry_queue:
                try:
                    self.retry_queue.put_nowait(event)
                    self.sync_stats["failed_events"] += 1
                except asyncio.QueueFull:
                    logger.warning(f"⚠️  重试队列已满,丢弃: {event.event_id}")

    async def _sync_to_nebula(self, event: ChangeEvent, mapping: dict[str, Any]):
        """同步到 NebulaGraph"""
        try:
            # 获取 pgvector 数据
            async with self.pg_pool.acquire() as conn:
                # 验证表名(防止SQL注入)
                table_name = mapping["pgvector_table"]
                SafeQueryBuilder.validate_table_name(table_name, "athena")

                # 使用参数化查询和标识符引用
                pg_data = await conn.fetchrow(
                    f"""
                    SELECT
                        id,
                        content,
                        title,
                        metadata
                    FROM "{table_name}"
                    WHERE id = $1
                """,
                    mapping["pgvector_id"],
                )

                if not pg_data:
                    logger.warning(f"⚠️  pgvector 数据不存在: {mapping['pgvector_id']}")
                    return

            # 构建 NebulaGraph UPSERT 语句
            vertex_id = mapping["nebula_vertex_id"]
            nebula_query = f'UPSERT VERTEX "{vertex_id}"'
            nebula_query += " SET unified_entity.content = $content"
            nebula_query += ", unified_entity.title = $title"
            nebula_query += ', unified_entity.vector_id = "$vector_id"'
            nebula_query += ', unified_entity.updated_at = "$updated_at"'

            # 准备参数
            params = {
                "content": pg_data["content"] or "",
                "title": pg_data["title"] or "",
                "vector_id": str(mapping["pgvector_id"]),
                "updated_at": datetime.now().isoformat(),
            }

            # 执行 NebulaGraph 操作
            session = self.nebula_pool.get_session()
            try:
                result = session.execute(nebula_query, params)
                if not result.is_succeeded():
                    logger.error(f"❌ NebulaGraph 同步失败: {result.error_msg()}")
            finally:
                session.release()

        except Exception as e:
            logger.error(f"❌ 同步到 NebulaGraph 失败: {e}")
            raise

    async def _sync_to_pgvector(self, event: ChangeEvent, mapping: dict[str, Any]):
        """同步到 pgvector"""
        try:
            # 从 NebulaGraph 获取数据
            nebula_query = f'FETCH PROP ON unified_entity "{mapping["nebula_vertex_id"]}"'

            session = self.nebula_pool.get_session()
            try:
                result = session.execute(nebula_query)
                if not result.is_succeeded():
                    logger.error(f"❌ NebulaGraph 查询失败: {result.error_msg()}")
                    return

                # 解析结果并更新 pgvector
                # 这里简化处理,实际需要解析 ResultSet
                async with self.pg_pool.acquire() as conn:
                    # 验证表名(防止SQL注入)
                    table_name = mapping["pgvector_table"]
                    SafeQueryBuilder.validate_table_name(table_name, "athena")

                    # 使用参数化查询和标识符引用
                    await conn.execute(
                        f"""
                        UPDATE "{table_name}"
                        SET metadata = metadata || $1,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = $2
                    """,
                        json.dumps(
                            {"nebula_synced": True, "sync_time": datetime.now().isoformat()}
                        ),
                        mapping["pgvector_id"],
                    )

            finally:
                session.release()

        except Exception as e:
            logger.error(f"❌ 同步到 pgvector 失败: {e}")
            raise

    async def _log_sync_event(self, event: ChangeEvent, status: str, error_message: str | None = None):
        """记录同步事件日志"""
        try:
            async with self.pg_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO vgraph_sync_event_log (
                        event_id, event_type, event_source,
                        entity_id, entity_type, business_key,
                        event_data, sync_status, error_message,
                        processed_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    ON CONFLICT (event_id, entity_id)
                    DO UPDATE SET
                        sync_status = EXCLUDED.sync_status,
                        error_message = EXCLUDED.error_message,
                        processed_at = EXCLUDED.processed_at
                """,
                    event.event_id,
                    event.event_type.value,
                    event.source,
                    event.entity_id,
                    event.entity_type,
                    event.business_key,
                    json.dumps(event.data),
                    status,
                    error_message,
                    datetime.now() if status in ["synced", "failed"] else None,
                )
        except Exception as e:
            logger.warning(f"记录同步事件日志失败: {e}")

    async def _process_retry_events(self):
        """处理重试事件"""
        logger.info("🔄 启动重试事件处理器...")

        while self.is_running:
            try:
                # 从重试队列获取事件
                event = await asyncio.wait_for(self.retry_queue.get(), timeout=5.0)

                # 重试同步
                logger.info(f"🔄 重试同步: {event.entity_id}")
                await self._sync_entity(event)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"❌ 重试事件处理异常: {e}")

    def _update_avg_latency(self, latency_ms: float) -> Any:
        """更新平均延迟"""
        current_avg = self.sync_stats["avg_latency_ms"]
        synced_count = self.sync_stats["synced_events"]

        if synced_count > 0:
            # 指数移动平均
            alpha = 0.1
            self.sync_stats["avg_latency_ms"] = alpha * latency_ms + (1 - alpha) * current_avg

    async def trigger_sync(self, entity_id: str, direction: str = "bidirectional"):
        """手动触发同步"""
        # 创建手动同步事件
        async with self.pg_pool.acquire() as conn:
            mapping = await conn.fetchrow(
                """
                SELECT entity_id, entity_type, business_key
                FROM vgraph_unified_mapping
                WHERE entity_id = $1
            """,
                entity_id,
            )

            if not mapping:
                logger.warning(f"未找到实体: {entity_id}")
                return False

            event = ChangeEvent(
                event_id=f"manual_{entity_id}_{datetime.now().timestamp()}",
                event_type=ChangeEventType.UPDATE,
                source="manual",
                entity_id=entity_id,
                entity_type=mapping["entity_type"],
                business_key=mapping["business_key"],
                data={"direction": direction},
            )

            await self._publish_event(event)
            logger.info(f"✅ 手动触发同步: {entity_id}")
            return True

    async def get_sync_statistics(self) -> dict[str, Any]:
        """获取同步统计"""
        async with self.pg_pool.acquire() as conn:
            # 获取待处理事件数量
            pending_count = await conn.fetchval("""
                SELECT COUNT(*)
                FROM vgraph_unified_mapping
                WHERE sync_status = 'pending'
            """)

            # 获取失败事件数量
            failed_count = await conn.fetchval("""
                SELECT COUNT(*)
                FROM vgraph_unified_mapping
                WHERE sync_status = 'failed'
            """)

            return {
                **self.sync_stats,
                "pending_events": pending_count,
                "failed_events": failed_count,
                "queue_size": self.event_queue.qsize() if self.event_queue else 0,
                "retry_queue_size": self.retry_queue.qsize() if self.retry_queue else 0,
                "is_running": self.is_running,
            }

    async def close(self):
        """关闭连接"""
        self.is_running = False

        if self.pg_pool:
            await self.pg_pool.close()
        if self.nebula_pool:
            self.nebula_pool.close()

        logger.info("🔌 实时同步服务已关闭")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()
        return False


# 使用示例
@async_main
async def main():
    """使用示例"""
    sync_service = RealtimeSyncService(
        pg_config={
            "host": "localhost",
            "port": 5438,
            "user": "postgres",
            "password": "athena_password",
            "database": "agent_memory_db",
        },
        nebula_config={
            "host": "localhost",
            "port": 9669,
            "username": "root",
            "password": "nebula",
            "space": "vgraph_unified_space",
        },
    )

    await sync_service.initialize()

    # 启动 CDC 监听器
    asyncio.create_task(sync_service.start_pg_cdc_listener())
    asyncio.create_task(sync_service.start_nebula_cdc_listener())

    # 运行一段时间
    await asyncio.sleep(60)

    # 获取统计
    stats = await sync_service.get_sync_statistics()
    print(f"同步统计: {json.dumps(stats, indent=2, ensure_ascii=False)}")

    await sync_service.close()


if __name__ == "__main__":
    # setup_logging()  # 日志配置已移至模块导入
    asyncio.run(main())
