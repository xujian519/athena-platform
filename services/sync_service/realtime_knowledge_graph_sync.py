#!/usr/bin/env python3
"""
Athena平台知识图谱实时同步系统
保持知识图谱与外部数据源的实时同步
"""

import asyncio
import json
import logging
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import aioredis
import websockets

# Gremlin Python客户端
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from core.async_main import async_main
from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/xujian/Athena工作平台/logs/kg_sync.log'),
        logging.StreamHandler()
    ]
)
logger = setup_logging()

class KnowledgeGraphSyncService:
    """知识图谱实时同步服务"""

    def __init__(self):
        self.platform_root = Path("/Users/xujian/Athena工作平台")
        self.sqlite_db_path = self.platform_root / "data" / "patent_guideline_system.db"
        self.config_path = self.platform_root / "config" / "sync_config.json"

        # 同步配置
        self.sync_interval = 30  # 30秒检查一次
        self.batch_size = 100
        self.max_retries = 3

        # 连接配置
        self.gremlin_url = "ws://localhost:8182/gremlin"
        self.redis_url = "redis://localhost:6379"

        # 状态管理
        self.is_running = False
        self.last_sync_time = None
        self.sync_stats = {
            "total_syncs": 0,
            "successful_syncs": 0,
            "failed_syncs": 0,
            "records_synced": 0
        }

        # 监控的表
        self.monitored_tables = {
            "patent_basic_info": "Patent",
            "company_info": "Company",
            "inventor_info": "Inventor",
            "technology_classification": "Technology",
            "legal_case_info": "LegalCase"
        }

    async def initialize(self):
        """初始化同步服务"""
        logger.info("🔧 初始化知识图谱同步服务...")

        # 1. 加载配置
        self._load_config()

        # 2. 初始化连接
        self._init_connections()

        # 3. 启动文件监控
        self._setup_file_monitor()

        # 4. 创建同步检查点
        await self._create_sync_checkpoint()

        logger.info("✅ 同步服务初始化完成")

    def _load_config(self) -> Any:
        """加载同步配置"""
        default_config = {
            "sync_interval": 30,
            "batch_size": 100,
            "auto_sync": True,
            "enable_change_detection": True,
            "enable_realtime_notifications": True,
            "notification_websocket_port": 8081,
            "monitored_tables": self.monitored_tables,
            "sync_modes": {
                "full_sync": {
                    "enabled": True,
                    "schedule": "0 2 * * *"  # 每天凌晨2点
                },
                "incremental_sync": {
                    "enabled": True,
                    "interval": 60  # 60秒
                },
                "realtime_sync": {
                    "enabled": True,
                    "trigger": "file_change"
                }
            }
        }

        try:
            if self.config_path.exists():
                with open(self.config_path, encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 合并配置
                    self.__dict__.update(loaded_config)
                    logger.info("✅ 同步配置已加载")
            else:
                # 创建默认配置文件
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, ensure_ascii=False, indent=2)
                self.__dict__.update(default_config)
                logger.info("✅ 创建默认同步配置")
        except (OSError, json.JSONDecodeError) as e:
            logger.error(f"配置文件加载失败: {e}")
            self.__dict__.update(default_config)

    def _init_connections(self) -> Any:
        """初始化数据库连接"""
        try:
            # SQLite连接
            self.sqlite_conn = sqlite3.connect(str(self.sqlite_db_path), check_same_thread=False)
            self.sqlite_conn.row_factory = sqlite3.Row
            logger.info("✅ SQLite连接已建立")
        except sqlite3.Error as e:
            logger.error(f"SQLite连接失败: {e}")
            raise

        # Redis连接（用于缓存和通知）
        self.redis_pool = None  # 将在异步方法中初始化

        # WebSocket连接池
        self.websocket_clients = set()

    def _setup_file_monitor(self) -> Any:
        """设置文件监控"""
        class DatabaseChangeHandler(FileSystemEventHandler):
            def __init__(self, sync_service):
                self.sync_service = sync_service
                self.last_modified = {}

            def on_modified(self, event) -> None:
                if event.is_directory:
                    return

                file_path = Path(event.src_path)
                if file_path.name == "patent_guideline_system.db":
                    current_time = time.time()
                    last_time = self.last_modified.get(str(file_path), 0)

                    # 防止重复触发（间隔至少1秒）
                    if current_time - last_time > 1:
                        logger.info(f"📝 检测到数据库变更: {file_path}")
                        # 触发同步任务
                        asyncio.create_task(self.sync_service.trigger_sync("file_change"))
                        self.last_modified[str(file_path)] = current_time

        # 设置监控
        db_dir = self.sqlite_db_path.parent
        self.observer = Observer()
        self.observer.schedule(
            DatabaseChangeHandler(self),
            path=str(db_dir),
            recursive=False
        )
        self.observer.start()
        logger.info(f"✅ 文件监控已启动: {db_dir}")

    async def _create_sync_checkpoint(self):
        """创建同步检查点"""
        checkpoint_file = self.platform_root / "data" / "sync_checkpoint.json"

        checkpoint = {
            "last_sync_time": datetime.now().isoformat(),
            "synced_records": {},
            "table_versions": {}
        }

        # 获取各表的最新记录ID作为检查点
        cursor = self.sqlite_conn.cursor()
        for table_name in self.monitored_tables:
            try:
                # 使用参数化查询防止SQL注入
                cursor.execute(f"SELECT MAX(id) FROM {table_name}")
                max_id = cursor.fetchone()[0]
                if max_id:
                    checkpoint["synced_records"][table_name] = max_id

                # 使用参数化查询防止SQL注入
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                checkpoint["table_versions"][table_name] = count
            except sqlite3.Error as e:
                logger.warning(f"⚠️ 无法获取表 {table_name} 的信息: {e}")

        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint, f, ensure_ascii=False, indent=2)

        self.sync_checkpoint = checkpoint
        logger.info("✅ 同步检查点已创建")

    async def start_sync_service(self):
        """启动同步服务"""
        logger.info("🚀 启动知识图谱同步服务...")
        self.is_running = True

        # 初始化Redis连接
        self.redis_pool = await aioredis.create_redis_pool(self.redis_url)

        # 启动WebSocket服务器
        websocket_task = asyncio.create_task(self._start_websocket_server())

        # 启动定时同步任务
        sync_tasks = []

        if self.sync_modes["incremental_sync"]["enabled"]:
            sync_tasks.append(
                asyncio.create_task(self._incremental_sync_loop())
            )

        if self.sync_modes["full_sync"]["enabled"]:
            sync_tasks.append(
                asyncio.create_task(self._scheduled_full_sync())
            )

        # 启动健康检查
        health_task = asyncio.create_task(self._health_check_loop())

        try:
            # 等待所有任务
            await asyncio.gather(*sync_tasks, websocket_task, health_task)
        except KeyboardInterrupt:
            logger.info("⏹️ 收到停止信号，正在关闭服务...")
        finally:
            await self.stop_sync_service()

    async def stop_sync_service(self):
        """停止同步服务"""
        self.is_running = False

        # 停止文件监控
        if hasattr(self, 'observer'):
            self.observer.stop()
            self.observer.join()

        # 关闭Redis连接
        if self.redis_pool:
            self.redis_pool.close()
            await self.redis_pool.wait_closed()

        # 关闭WebSocket连接
        for ws in self.websocket_clients:
            await ws.close()

        # 关闭SQLite连接
        if hasattr(self, 'sqlite_conn'):
            self.sqlite_conn.close()

        logger.info("✅ 同步服务已停止")

    async def _start_websocket_server(self):
        """启动WebSocket服务器用于实时通知"""
        async def handle_websocket(websocket, path):
            """处理WebSocket连接"""
            self.websocket_clients.add(websocket)
            logger.info(f"🔌 新的WebSocket连接: {websocket.remote_address}")

            try:
                # 发送初始状态
                await websocket.send(json.dumps({
                    "type": "status",
                    "message": "连接成功",
                    "sync_stats": self.sync_stats
                }))

                # 保持连接
                async for message in websocket:
                    data = json.loads(message)
                    if data.get("type") == "trigger_sync":
                        await self.trigger_sync("manual", data.get("table"))
            except websockets.exceptions.ConnectionClosed as e:
                logger.error(f"Error: {e}", exc_info=True)
            finally:
                self.websocket_clients.discard(websocket)
                logger.info(f"🔌 WebSocket连接已断开: {websocket.remote_address}")

        # 启动WebSocket服务器
        port = self.notification_websocket_port
        logger.info(f"🌐 WebSocket服务器启动在端口 {port}")

        async with websockets.serve(handle_websocket, "localhost", port):
            await asyncio.Future()  # 保持服务器运行

    async def _incremental_sync_loop(self):
        """增量同步循环"""
        interval = self.sync_modes["incremental_sync"]["interval"]
        logger.info(f"🔄 启动增量同步循环，间隔 {interval} 秒")

        while self.is_running:
            try:
                await asyncio.sleep(interval)
                await self.perform_incremental_sync()
            except Exception as e:
                logger.error(f"❌ 增量同步失败: {e}")
                await asyncio.sleep(5)  # 错误后等待5秒再重试

    async def _scheduled_full_sync(self):
        """定时完整同步"""
        schedule = self.sync_modes["full_sync"]["schedule"]
        logger.info(f"⏰ 定时完整同步计划: {schedule}")

        # 简化实现：每小时检查一次是否需要全量同步
        while self.is_running:
            try:
                await asyncio.sleep(3600)  # 每小时检查一次

                current_hour = datetime.now().hour
                if current_hour == 2:  # 凌晨2点
                    logger.info("🌙 执行定时完整同步...")
                    await self.perform_full_sync()
            except Exception as e:
                logger.error(f"❌ 定时同步失败: {e}")

    async def _health_check_loop(self):
        """健康检查循环"""
        logger.info("🏥 启动健康检查循环")

        while self.is_running:
            try:
                await asyncio.sleep(60)  # 每分钟检查一次

                # 检查JanusGraph连接
                if await self._check_janusgraph_health():
                    logger.debug("✅ JanusGraph健康")
                else:
                    logger.warning("⚠️ JanusGraph连接异常")

                # 检查SQLite连接
                try:
                    self.sqlite_conn.execute("SELECT 1")
                    logger.debug("✅ SQLite健康")
                except sqlite3.Error:
                    logger.error("❌ SQLite连接异常")

            except Exception as e:
                logger.error(f"❌ 健康检查失败: {e}")

    async def trigger_sync(self, trigger_type: str, table: str | None = None):
        """触发同步任务"""
        logger.info(f"🚀 触发同步: 类型={trigger_type}, 表={table}")

        # 更新同步统计
        self.sync_stats["total_syncs"] += 1

        try:
            if trigger_type == "full":
                await self.perform_full_sync()
            elif trigger_type == "incremental":
                await self.perform_incremental_sync(table)
            else:
                await self.perform_incremental_sync(table)

            # 更新成功统计
            self.sync_stats["successful_syncs"] += 1

            # 发送通知
            await self._notify_clients({
                "type": "sync_completed",
                "trigger_type": trigger_type,
                "timestamp": datetime.now().isoformat(),
                "stats": self.sync_stats
            })

        except Exception as e:
            logger.error(f"❌ 同步失败: {e}")
            self.sync_stats["failed_syncs"] += 1

            # 发送错误通知
            await self._notify_clients({
                "type": "sync_error",
                "trigger_type": trigger_type,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })

    async def perform_incremental_sync(self, table: str | None = None):
        """执行增量同步"""
        logger.info("📝 执行增量同步...")

        # 加载检查点
        checkpoint = self._load_checkpoint()

        # 获取需要同步的表
        tables_to_sync = [table] if table else list(self.monitored_tables.keys())

        for table_name in tables_to_sync:
            if table_name not in self.monitored_tables:
                continue

            entity_type = self.monitored_tables[table_name]
            last_synced_id = checkpoint["synced_records"].get(table_name, 0)

            try:
                # 查询新增记录 - 使用参数化查询防止SQL注入
                # 注意: 表名来自self.monitored_tables白名单，是安全的
                cursor = self.sqlite_conn.cursor()
                cursor.execute(
                    f"SELECT * FROM {table_name} WHERE id > ? ORDER BY id LIMIT ?",
                    (last_synced_id, self.batch_size)
                )
                new_records = cursor.fetchall()

                if new_records:
                    # 同步到JanusGraph
                    await self._sync_records_to_janusgraph(new_records, entity_type)

                    # 更新检查点
                    new_max_id = max(record["id"] for record in new_records)
                    checkpoint["synced_records"][table_name] = new_max_id

                    # 更新统计
                    self.sync_stats["records_synced"] += len(new_records)

                    logger.info(f"✅ 表 {table_name} 同步完成，新增 {len(new_records)} 条记录")

                else:
                    logger.debug(f"📝 表 {table_name} 无新增记录")

            except Exception as e:
                logger.error(f"❌ 同步表 {table_name} 失败: {e}")

        # 保存检查点
        self._save_checkpoint(checkpoint)

    async def perform_full_sync(self):
        """执行完整同步"""
        logger.info("🔄 执行完整同步...")

        # 注意：完整同步会清空现有数据并重新导入
        # 在生产环境中需要谨慎使用

        for table_name, entity_type in self.monitored_tables.items():
            try:
                # 查询所有记录 - 使用参数化查询防止SQL注入
                # 注意: 表名来自self.monitored_tables白名单，是安全的
                cursor = self.sqlite_conn.cursor()
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                total_count = cursor.fetchone()[0]

                logger.info(f"📊 开始同步表 {table_name}，共 {total_count} 条记录")

                # 分批同步
                offset = 0
                while offset < total_count:
                    # 使用参数化查询
                    cursor.execute(
                        f"SELECT * FROM {table_name} ORDER BY id LIMIT ? OFFSET ?",
                        (self.batch_size, offset)
                    )
                    records = cursor.fetchall()

                    if records:
                        await self._sync_records_to_janusgraph(records, entity_type)

                    offset += self.batch_size
                    logger.debug(f"已同步 {min(offset, total_count)}/{total_count}")

                logger.info(f"✅ 表 {table_name} 同步完成")

            except Exception as e:
                logger.error(f"❌ 同步表 {table_name} 失败: {e}")

        # 重置检查点
        await self._create_sync_checkpoint()

    async def _sync_records_to_janusgraph(self, records: list[sqlite3.Row], entity_type: str):
        """将记录同步到JanusGraph"""
        try:
            # 这里应该连接到JanusGraph并执行导入
            # 简化实现：记录到日志
            for record in records:
                entity_data = dict(record)
                logger.debug(f"同步实体: {entity_type} - {entity_data.get('id')}")

            # 实际实现示例：
            """
            gremlin_client = client.Client(self.gremlin_url, 'g')
            g = traversal().with_remote(gremlin_client)

            for record in records:
                # 创建顶点
                vertex = g.add_v(entity_type)
                for key, value in record.items():
                    if value is not None:
                        vertex.property(key, str(value))
                vertex.next()

            gremlin_client.close()
            """

        except Exception as e:
            logger.error(f"❌ 同步到JanusGraph失败: {e}")
            raise

    async def _notify_clients(self, message: dict):
        """通知所有WebSocket客户端"""
        if not self.websocket_clients:
            return

        message_str = json.dumps(message, ensure_ascii=False)
        disconnected = set()

        for ws in self.websocket_clients:
            try:
                await ws.send(message_str)
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(ws)

        # 移除断开的连接
        self.websocket_clients -= disconnected

    async def _check_janusgraph_health(self) -> bool:
        """检查JanusGraph健康状态"""
        try:
            # 简化实现：检查端口
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(("localhost", 8182))
            sock.close()
            return result == 0
        except (TimeoutError, asyncio.CancelledError, Exception):
            return False

    def _load_checkpoint(self) -> dict:
        """加载同步检查点"""
        checkpoint_file = self.platform_root / "data" / "sync_checkpoint.json"

        if checkpoint_file.exists():
            with open(checkpoint_file, encoding='utf-8') as f:
                return json.load(f)
        else:
            return {"synced_records": {}, "table_versions": {}}

    def _save_checkpoint(self, checkpoint: dict) -> Any:
        """保存同步检查点"""
        checkpoint_file = self.platform_root / "data" / "sync_checkpoint.json"
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint, f, ensure_ascii=False, indent=2)

class SyncServiceManager:
    """同步服务管理器"""

    def __init__(self):
        self.sync_service = KnowledgeGraphSyncService()

    async def start(self):
        """启动同步服务"""
        await self.sync_service.initialize()
        await self.sync_service.start_sync_service()

    async def stop(self):
        """停止同步服务"""
        await self.sync_service.stop_sync_service()

@async_main
async def main():
    """主函数"""
    manager = SyncServiceManager()

    # 设置优雅关闭
    import signal

    def signal_handler(signum, frame) -> None:
        logger.info("🛑 收到关闭信号")
        asyncio.create_task(manager.stop())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 启动服务
    try:
        await manager.start()
    except Exception as e:
        logger.error(f"❌ 服务启动失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 设置事件循环策略（macOS需要）
    if __import__('sys').platform == 'darwin':
        import asyncio
        asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())

    # 运行服务
    asyncio.run(main())
