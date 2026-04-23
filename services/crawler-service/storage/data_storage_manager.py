#!/usr/bin/env python3
"""
数据存储管理器 - 支持多种存储后端和数据格式
Data Storage Manager - Support for multiple storage backends and data formats
控制者: Athena & 小诺
"""

import gzip
import hashlib
import json
import logging
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

import aiofiles
import aiosqlite

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class StorageType(Enum):
    """存储类型枚举"""
    SQLITE = 'sqlite'
    JSON = 'json'
    PICKLE = 'pickle'
    PARQUET = 'parquet'


class CompressionType(Enum):
    """压缩类型枚举"""
    NONE = 'none'
    GZIP = 'gzip'
    ZSTD = 'zstd'


@dataclass
class StorageConfig:
    """存储配置"""
    storage_type: StorageType
    compression: CompressionType = CompressionType.NONE
    base_path: str = '/Users/xujian/Athena工作平台/data/crawler/storage'
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    retention_days: int = 30
    auto_vacuum: bool = True
    enable_indexing: bool = True


@dataclass
class StoredData:
    """存储数据项"""
    id: str
    url: str
    content: str
    metadata: dict[str, Any]
    crawler_type: str
    timestamp: datetime
    content_hash: str
    size: int
    compressed_size: int | None = None

    def __post_init__(self):
        if not self.content_hash:
            self.content_hash = hashlib.md5(self.content.encode(), usedforsecurity=False).hexdigest()
        self.size = len(self.content.encode('utf-8'))


class StorageBackend(ABC):
    """存储后端抽象基类"""

    @abstractmethod
    async def store(self, data: StoredData) -> bool:
        """存储数据"""
        pass

    @abstractmethod
    async def retrieve(self, data_id: str) -> StoredData | None:
        """检索数据"""
        pass

    @abstractmethod
    async def search(self, query: dict[str, Any], limit: int = 100) -> list[StoredData]:
        """搜索数据"""
        pass

    @abstractmethod
    async def delete(self, data_id: str) -> bool:
        """删除数据"""
        pass

    @abstractmethod
    async def cleanup_old_data(self, days: int) -> int:
        """清理旧数据"""
        pass

    @abstractmethod
    async def get_stats(self) -> dict[str, Any]:
        """获取存储统计信息"""
        pass


class SQLiteStorageBackend(StorageBackend):
    """SQLite存储后端"""

    def __init__(self, config: StorageConfig):
        self.config = config
        self.db_path = Path(config.base_path) / 'crawler_data.db'
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    async def initialize(self):
        """初始化数据库"""
        async with aiosqlite.connect(self.db_path) as db:
            # 创建数据表
            await db.execute("""
                CREATE TABLE IF NOT EXISTS crawler_data (
                    id TEXT PRIMARY KEY,
                    url TEXT NOT NULL,
                    content TEXT,
                    metadata TEXT,
                    crawler_type TEXT,
                    timestamp TEXT,
                    content_hash TEXT,
                    size INTEGER,
                    compressed_size INTEGER
                )
            """)

            # 创建索引
            if self.config.enable_indexing:
                await db.execute('CREATE INDEX IF NOT EXISTS idx_url ON crawler_data(url)')
                await db.execute('CREATE INDEX IF NOT EXISTS idx_crawler_type ON crawler_data(crawler_type)')
                await db.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON crawler_data(timestamp)')
                await db.execute('CREATE INDEX IF NOT EXISTS idx_content_hash ON crawler_data(content_hash)')

            await db.commit()

        logger.info(f"SQLite存储后端已初始化: {self.db_path}")

    async def store(self, data: StoredData) -> bool:
        """存储数据"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # 压缩内容
                content = self._compress_content(data.content)
                compressed_size = len(content) if content != data.content else None

                await db.execute("""
                    INSERT OR REPLACE INTO crawler_data
                    (id, url, content, metadata, crawler_type, timestamp,
                     content_hash, size, compressed_size)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data.id,
                    data.url,
                    content,
                    json.dumps(data.metadata),
                    data.crawler_type,
                    data.timestamp.isoformat(),
                    data.content_hash,
                    data.size,
                    compressed_size
                ))

                await db.commit()
                return True

        except Exception as e:
            logger.error(f"存储数据失败: {e}")
            return False

    async def retrieve(self, data_id: str) -> StoredData | None:
        """检索数据"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    'SELECT * FROM crawler_data WHERE id = ?',
                    (data_id,)
                )
                row = await cursor.fetchone()

                if row:
                    # 解压内容
                    content = self._decompress_content(row['content'])
                    return StoredData(
                        id=row['id'],
                        url=row['url'],
                        content=content,
                        metadata=json.loads(row['metadata']),
                        crawler_type=row['crawler_type'],
                        timestamp=datetime.fromisoformat(row['timestamp']),
                        content_hash=row['content_hash'],
                        size=row['size'],
                        compressed_size=row['compressed_size']
                    )

                return None

        except Exception as e:
            logger.error(f"检索数据失败: {e}")
            return None

    async def search(self, query: dict[str, Any], limit: int = 100) -> list[StoredData]:
        """搜索数据"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row

                # 构建查询条件
                conditions = []
                params = []

                if 'url' in query:
                    conditions.append('url LIKE ?')
                    params.append(f"%{query['url']}%")

                if 'crawler_type' in query:
                    conditions.append('crawler_type = ?')
                    params.append(query['crawler_type'])

                if 'start_time' in query:
                    conditions.append('timestamp >= ?')
                    params.append(query['start_time'])

                if 'end_time' in query:
                    conditions.append('timestamp <= ?')
                    params.append(query['end_time'])

                # 构建SQL查询
                sql = 'SELECT * FROM crawler_data'
                if conditions:
                    sql += ' WHERE ' + ' AND '.join(conditions)
                sql += f" ORDER BY timestamp DESC LIMIT {limit}"

                cursor = await db.execute(sql, params)
                rows = await cursor.fetchall()

                results = []
                for row in rows:
                    content = self._decompress_content(row['content'])
                    results.append(StoredData(
                        id=row['id'],
                        url=row['url'],
                        content=content,
                        metadata=json.loads(row['metadata']),
                        crawler_type=row['crawler_type'],
                        timestamp=datetime.fromisoformat(row['timestamp']),
                        content_hash=row['content_hash'],
                        size=row['size'],
                        compressed_size=row['compressed_size']
                    ))

                return results

        except Exception as e:
            logger.error(f"搜索数据失败: {e}")
            return []

    async def delete(self, data_id: str) -> bool:
        """删除数据"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    'DELETE FROM crawler_data WHERE id = ?',
                    (data_id,)
                )
                await db.commit()
                return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"删除数据失败: {e}")
            return False

    async def cleanup_old_data(self, days: int) -> int:
        """清理旧数据"""
        try:
            cutoff_date = (datetime.now(UTC) -
                          timedelta(days=days)).isoformat()

            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    'DELETE FROM crawler_data WHERE timestamp < ?',
                    (cutoff_date,)
                )
                deleted_count = cursor.rowcount
                await db.commit()

                # 如果启用自动清理，执行VACUUM
                if self.config.auto_vacuum and deleted_count > 0:
                    await db.execute('VACUUM')
                    await db.commit()

                logger.info(f"清理了 {deleted_count} 条旧数据")
                return deleted_count

        except Exception as e:
            logger.error(f"清理旧数据失败: {e}")
            return 0

    async def get_stats(self) -> dict[str, Any]:
        """获取存储统计信息"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # 总记录数
                cursor = await db.execute('SELECT COUNT(*) FROM crawler_data')
                total_records = (await cursor.fetchone())[0]

                # 总大小
                cursor = await db.execute('SELECT SUM(size), SUM(compressed_size) FROM crawler_data')
                total_size, compressed_size = await cursor.fetchone()

                # 按爬虫类型统计
                cursor = await db.execute("""
                    SELECT crawler_type, COUNT(*), SUM(size)
                    FROM crawler_data
                    GROUP BY crawler_type
                """)
                type_stats = {}
                for row in await cursor.fetchall():
                    type_stats[row[0] = {
                        'count': row[1],
                        'size': row[2]
                    }

                # 按日期统计
                cursor = await db.execute("""
                    SELECT DATE(timestamp) as date, COUNT(*)
                    FROM crawler_data
                    WHERE timestamp >= date('now', '-7 days')
                    GROUP BY date
                    ORDER BY date
                """)
                daily_stats = {}
                for row in await cursor.fetchall():
                    daily_stats[row[0] = row[1]

                return {
                    'total_records': total_records,
                    'total_size_bytes': total_size or 0,
                    'compressed_size_bytes': compressed_size or 0,
                    'compression_ratio': (compressed_size / total_size) if total_size > 0 else 0,
                    'by_crawler_type': type_stats,
                    'daily_counts': daily_stats,
                    'database_size': self.db_path.stat().st_size
                }

        except Exception as e:
            logger.error(f"获取存储统计失败: {e}")
            return {}

    def _compress_content(self, content: str) -> str:
        """压缩内容"""
        if self.config.compression == CompressionType.GZIP:
            return gzip.compress(content.encode('utf-8')).decode('latin-1')
        return content

    def _decompress_content(self, content: str) -> str:
        """解压内容"""
        if self.config.compression == CompressionType.GZIP:
            try:
                return gzip.decompress(content.encode('latin-1')).decode('utf-8')
            except Exception:  # TODO: 指定具体异常类型
                return content
        return content


class JSONStorageBackend(StorageBackend):
    """JSON文件存储后端"""

    def __init__(self, config: StorageConfig):
        self.config = config
        self.base_path = Path(config.base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, data: StoredData) -> Path:
        """获取文件路径"""
        # 按日期分组存储
        date_str = data.timestamp.strftime('%Y-%m-%d')
        date_dir = self.base_path / date_str
        date_dir.mkdir(exist_ok=True)
        return date_dir / f"{data.id}.json"

    async def store(self, data: StoredData) -> bool:
        """存储数据"""
        try:
            file_path = self._get_file_path(data)

            # 准备数据
            stored_data = asdict(data)
            stored_data['timestamp'] = data.timestamp.isoformat()

            # 写入文件
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(stored_data, indent=2, ensure_ascii=False))

            return True

        except Exception as e:
            logger.error(f"存储JSON数据失败: {e}")
            return False

    async def retrieve(self, data_id: str) -> StoredData | None:
        """检索数据"""
        try:
            # 在所有日期目录中搜索文件
            for date_dir in self.base_path.iterdir():
                if date_dir.is_dir():
                    file_path = date_dir / f"{data_id}.json"
                    if file_path.exists():
                        async with aiofiles.open(file_path, encoding='utf-8') as f:
                            content = await f.read()
                            data_dict = json.loads(content)
                            data_dict['timestamp'] = datetime.fromisoformat(data_dict['timestamp'])
                            return StoredData(**data_dict)

            return None

        except Exception as e:
            logger.error(f"检索JSON数据失败: {e}")
            return None

    async def search(self, query: dict[str, Any], limit: int = 100) -> list[StoredData]:
        """搜索数据"""
        results = []
        processed = 0

        try:
            # 搜索所有文件
            for date_dir in sorted(self.base_path.iterdir(), reverse=True):
                if not date_dir.is_dir() or processed >= limit:
                    break

                for file_path in date_dir.glob('*.json'):
                    if processed >= limit:
                        break

                    try:
                        async with aiofiles.open(file_path, encoding='utf-8') as f:
                            content = await f.read()
                            data_dict = json.loads(content)

                            # 应用查询过滤
                            if self._match_query(data_dict, query):
                                data_dict['timestamp'] = datetime.fromisoformat(data_dict['timestamp'])
                                results.append(StoredData(**data_dict))
                                processed += 1

                    except Exception as e:
                        logger.warning(f"读取文件失败 {file_path}: {e}")

            return results[:limit]

        except Exception as e:
            logger.error(f"搜索JSON数据失败: {e}")
            return []

    async def delete(self, data_id: str) -> bool:
        """删除数据"""
        try:
            for date_dir in self.base_path.iterdir():
                if date_dir.is_dir():
                    file_path = date_dir / f"{data_id}.json"
                    if file_path.exists():
                        file_path.unlink()
                        return True
            return False

        except Exception as e:
            logger.error(f"删除JSON数据失败: {e}")
            return False

    async def cleanup_old_data(self, days: int) -> int:
        """清理旧数据"""
        deleted_count = 0
        cutoff_date = datetime.now() - timedelta(days=days)

        try:
            for date_dir in self.base_path.iterdir():
                if date_dir.is_dir():
                    try:
                        dir_date = datetime.strptime(date_dir.name, '%Y-%m-%d')
                        if dir_date < cutoff_date:
                            # 删除整个目录
                            for file_path in date_dir.glob('*.json'):
                                file_path.unlink()
                                deleted_count += 1
                            date_dir.rmdir()
                    except ValueError:
                        continue

            logger.info(f"清理了 {deleted_count} 个JSON文件")
            return deleted_count

        except Exception as e:
            logger.error(f"清理JSON数据失败: {e}")
            return 0

    async def get_stats(self) -> dict[str, Any]:
        """获取存储统计信息"""
        try:
            total_files = 0
            total_size = 0
            type_counts = {}
            daily_counts = {}

            for date_dir in self.base_path.iterdir():
                if not date_dir.is_dir():
                    continue

                daily_count = 0
                for file_path in date_dir.glob('*.json'):
                    total_files += 1
                    total_size += file_path.stat().st_size
                    daily_count += 1

                    # 读取文件获取类型信息
                    try:
                        async with aiofiles.open(file_path, encoding='utf-8') as f:
                            content = await f.read()
                            data_dict = json.loads(content)
                            crawler_type = data_dict.get('crawler_type', 'unknown')
                            type_counts[crawler_type] = type_counts.get(crawler_type, 0) + 1
                    except Exception as e:
                        logger.error(f"Error: {e}", exc_info=True)

                daily_counts[date_dir.name] = daily_count

            return {
                'total_files': total_files,
                'total_size_bytes': total_size,
                'by_crawler_type': type_counts,
                'daily_counts': daily_counts
            }

        except Exception as e:
            logger.error(f"获取JSON存储统计失败: {e}")
            return {}

    def _match_query(self, data_dict: dict[str, Any], query: dict[str, Any]) -> bool:
        """匹配查询条件"""
        if 'url' in query and query['url'] not in data_dict.get('url', ''):
            return False

        if 'crawler_type' in query and data_dict.get('crawler_type') != query['crawler_type']:
            return False

        if 'start_time' in query:
            try:
                timestamp = datetime.fromisoformat(data_dict['timestamp'])
                if timestamp < datetime.fromisoformat(query['start_time']):
                    return False
            except Exception as e:
                logger.error(f"Error: {e}", exc_info=True)

        if 'end_time' in query:
            try:
                timestamp = datetime.fromisoformat(data_dict['timestamp'])
                if timestamp > datetime.fromisoformat(query['end_time']):
                    return False
            except Exception as e:
                logger.error(f"Error: {e}", exc_info=True)

        return True


class DataStorageManager:
    """数据存储管理器"""

    def __init__(self, config: StorageConfig = None):
        self.config = config or StorageConfig(storage_type=StorageType.SQLITE)
        self.backend: StorageBackend | None = None

    async def initialize(self):
        """初始化存储管理器"""
        if self.config.storage_type == StorageType.SQLITE:
            self.backend = SQLiteStorageBackend(self.config)
            await self.backend.initialize()
        elif self.config.storage_type == StorageType.JSON:
            self.backend = JSONStorageBackend(self.config)
        else:
            raise ValueError(f"不支持的存储类型: {self.config.storage_type}")

        logger.info(f"数据存储管理器已初始化: {self.config.storage_type.value}")

    async def store_crawl_result(self, crawl_result: dict[str, Any]) -> str:
        """存储爬取结果"""
        data = StoredData(
            id=crawl_result.get('task_id', str(uuid.uuid4())),
            url=crawl_result.get('url', ''),
            content=crawl_result.get('content', ''),
            metadata={
                'title': crawl_result.get('title', ''),
                'status_code': crawl_result.get('status_code', 200),
                'processing_time': crawl_result.get('processing_time', 0),
                'crawler_used': crawl_result.get('crawler_used', 'unknown'),
                'links': crawl_result.get('links', []),
                'images': crawl_result.get('images', []),
                'extracted_data': crawl_result.get('extracted_data', {})
            },
            crawler_type=crawl_result.get('crawler_used', 'unknown'),
            timestamp=datetime.now(UTC),
            content_hash=''
        )

        success = await self.backend.store(data)
        if success:
            logger.info(f"爬取结果已存储: {data.url}")
            return data.id
        else:
            raise Exception('存储爬取结果失败')

    async def retrieve_data(self, data_id: str) -> dict[str, Any | None]:
        """检索数据"""
        data = await self.backend.retrieve(data_id)
        if data:
            return {
                'id': data.id,
                'url': data.url,
                'content': data.content,
                'metadata': data.metadata,
                'crawler_type': data.crawler_type,
                'timestamp': data.timestamp.isoformat(),
                'size': data.size,
                'compressed_size': data.compressed_size
            }
        return None

    async def search_data(self, query: dict[str, Any], limit: int = 100) -> list[dict[str, Any]:
        """搜索数据"""
        results = await self.backend.search(query, limit)
        return [
            {
                'id': data.id,
                'url': data.url,
                'metadata': data.metadata,
                'crawler_type': data.crawler_type,
                'timestamp': data.timestamp.isoformat(),
                'size': data.size
            }
            for data in results
        ]

    async def delete_data(self, data_id: str) -> bool:
        """删除数据"""
        return await self.backend.delete(data_id)

    async def cleanup_old_data(self, days: int = None) -> int:
        """清理旧数据"""
        days = days or self.config.retention_days
        return await self.backend.cleanup_old_data(days)

    async def get_storage_stats(self) -> dict[str, Any]:
        """获取存储统计信息"""
        stats = await self.backend.get_stats()
        stats['config'] = {
            'storage_type': self.config.storage_type.value,
            'compression': self.config.compression.value,
            'retention_days': self.config.retention_days,
            'base_path': self.config.base_path
        }
        return stats

    async def export_data(self, query: dict[str, Any], format: str = 'json') -> str:
        """导出数据"""
        results = await self.search_data(query, limit=10000)  # 最大导出1万条

        if format == 'json':
            export_data = {
                'export_time': datetime.now(UTC).isoformat(),
                'query': query,
                'count': len(results),
                'data': results
            }
            return json.dumps(export_data, indent=2, ensure_ascii=False)

        else:
            raise ValueError(f"不支持的导出格式: {format}")


# 全局存储管理器实例
storage_manager = DataStorageManager()


@asynccontextmanager
async def storage_context(config: StorageConfig = None):
    """存储管理器上下文管理器"""
    manager = DataStorageManager(config)
    await manager.initialize()
    try:
        yield manager
    finally:
        # 清理资源
        pass


import uuid

# 导入必要的模块
from datetime import timedelta
