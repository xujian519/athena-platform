#!/usr/bin/env python3
"""
分布式存储管理器
Distributed Storage Manager

支持本地存储、云存储（S3、阿里云OSS、腾讯云COS）和混合存储策略
"""

import asyncio
import hashlib
import logging
import mimetypes
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import aiofiles

# 云存储SDK（可选依赖）
try:
    import boto3
    from botocore.exceptions import ClientError
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False

try:
    import oss2
    OSS_AVAILABLE = True
except ImportError:
    OSS_AVAILABLE = False

try:
    from qcloud_cos import CosS3Client
    from qcloud_cos.cos_exception import CosClientError
    TENCENT_AVAILABLE = True
except ImportError:
    TENCENT_AVAILABLE = False

logger = logging.getLogger(__name__)

class StorageType(Enum):
    """存储类型"""
    LOCAL = "local"
    S3 = "s3"
    ALIYUN_OSS = "aliyun_oss"
    TENCENT_COS = "tencent_cos"

class StorageTier(Enum):
    """存储层级"""
    HOT = "hot"      # 热存储（频繁访问）
    WARM = "warm"    # 温存储（偶尔访问）
    COLD = "cold"    # 冷存储（很少访问）

@dataclass
class StorageConfig:
    """存储配置"""
    storage_type: StorageType
    tier: StorageTier
    access_key: str | None = None
    secret_key: str | None = None
    region: str | None = None
    bucket_name: str | None = None
    endpoint: str | None = None
    base_path: str | None = None
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    retention_days: int = 30

@dataclass
class FileLocation:
    """文件位置信息"""
    storage_type: StorageType
    storage_path: str
    bucket_name: str | None = None
    region: str | None = None
    url: str | None = None
    size: int = 0
    last_modified: datetime | None = None
    etag: str | None = None
    tier: StorageTier = StorageTier.HOT

class DistributedStorageManager:
    """分布式存储管理器"""

    def __init__(self):
        self.storage_configs: dict[StorageType, StorageConfig] = {}
        self.default_storage: StorageType = StorageType.LOCAL
        self.tier_routing: dict[StorageTier, list[StorageType]] = {
            StorageTier.HOT: [StorageType.LOCAL, StorageType.S3],
            StorageTier.WARM: [StorageType.S3, StorageType.ALIYUN_OSS],
            StorageTier.COLD: [StorageType.ALIYUN_OSS, StorageType.TENCENT_COS]
        }
        self.storage_clients: dict[StorageType, Any] = {}
        self.access_patterns: dict[str, dict[str, Any]] = {}  # 文件访问模式记录
        self.replication_enabled = True
        self.compression_enabled = True

    def add_storage_config(self, config: StorageConfig):
        """添加存储配置"""
        self.storage_configs[config.storage_type] = config

        # 初始化存储客户端
        if config.storage_type == StorageType.LOCAL:
            self._init_local_storage(config)
        elif config.storage_type == StorageType.S3 and AWS_AVAILABLE:
            self._init_s3_storage(config)
        elif config.storage_type == StorageType.ALIYUN_OSS and OSS_AVAILABLE:
            self._init_oss_storage(config)
        elif config.storage_type == StorageType.TENCENT_COS and TENCENT_AVAILABLE:
            self._init_cos_storage(config)

        logger.info(f"已添加存储配置: {config.storage_type.value}")

    def _init_local_storage(self, config: StorageConfig):
        """初始化本地存储"""
        if config.base_path:
            Path(config.base_path).mkdir(parents=True, exist_ok=True)

    def _init_s3_storage(self, config: StorageConfig):
        """初始化AWS S3存储"""
        try:
            session = boto3.Session(
                aws_access_key_id=config.access_key,
                aws_secret_access_key=config.secret_key,
                region_name=config.region
            )
            s3_client = session.client('s3')
            # 测试连接
            s3_client.head_bucket(Bucket=config.bucket_name)
            self.storage_clients[StorageType.S3] = s3_client
            logger.info("S3存储初始化成功")
        except Exception as e:
            logger.error(f"S3存储初始化失败: {e}")

    def _init_oss_storage(self, config: StorageConfig):
        """初始化阿里云OSS存储"""
        try:
            auth = oss2.Auth(config.access_key, config.secret_key)
            bucket = oss2.Bucket(auth, config.endpoint, config.bucket_name)
            # 测试连接
            bucket.get_bucket_info()
            self.storage_clients[StorageType.ALIYUN_OSS] = bucket
            logger.info("阿里云OSS存储初始化成功")
        except Exception as e:
            logger.error(f"阿里云OSS存储初始化失败: {e}")

    def _init_cos_storage(self, config: StorageConfig):
        """初始化腾讯云COS存储"""
        try:
            config_dict = {
                'Region': config.region,
                'SecretId': config.access_key,
                'SecretKey': config.secret_key
            }
            cos_client = CosS3Client(config_dict)
            self.storage_clients[StorageType.TENCENT_COS] = cos_client
            logger.info("腾讯云COS存储初始化成功")
        except Exception as e:
            logger.error(f"腾讯云COS存储初始化失败: {e}")

    def determine_storage_tier(self, file_id: str, file_size: int = 0) -> StorageTier:
        """确定存储层级"""
        # 检查访问模式
        access_pattern = self.access_patterns.get(file_id, {})

        # 新文件默认为热存储
        if not access_pattern:
            return StorageTier.HOT

        # 根据访问频率和最后访问时间确定层级
        last_access = access_pattern.get('last_access')
        access_count = access_pattern.get('access_count', 0)
        days_since_access = (datetime.now() - last_access).days if last_access else 0

        # 小文件默认热存储
        if file_size < 10 * 1024 * 1024:  # 10MB
            return StorageTier.HOT

        # 根据访问模式决定层级
        if days_since_access < 7 and access_count > 10:
            return StorageTier.HOT
        elif days_since_access < 30 and access_count > 3:
            return StorageTier.WARM
        else:
            return StorageTier.COLD

    async def store_file(self, file_content: bytes, filename: str,
                        file_id: str = None, tier: StorageTier = None,
                        replicate: bool = None) -> list[FileLocation]:
        """存储文件到分布式存储"""
        if not file_id:
            file_id = hashlib.sha256(file_content).hexdigest()

        # 确定存储层级
        if tier is None:
            tier = self.determine_storage_tier(file_id, len(file_content))

        # 获取可用的存储类型
        available_storages = self.tier_routing.get(tier, [self.default_storage])

        # 过滤已配置的存储
        configured_storages = [
            storage_type for storage_type in available_storages
            if storage_type in self.storage_configs
        ]

        if not configured_storages:
            # 回退到默认存储
            if self.default_storage not in self.storage_configs:
                raise ValueError("没有可用的存储配置")
            configured_storages = [self.default_storage]

        # 复制开关
        should_replicate = replicate if replicate is not None else self.replication_enabled
        if should_replicate:
            # 复制到多个存储（最多2个）
            storage_types = configured_storages[:2]
        else:
            # 只存储到第一个可用存储
            storage_types = configured_storages[:1]

        locations = []
        for storage_type in storage_types:
            try:
                location = await self._store_to_storage(
                    file_content, filename, file_id, storage_type, tier
                )
                locations.append(location)
                logger.info(f"文件 {filename} 已存储到 {storage_type.value}")
            except Exception as e:
                logger.error(f"存储到 {storage_type.value} 失败: {e}")

        if not locations:
            raise RuntimeError("文件存储失败")

        # 记录访问模式
        self.access_patterns[file_id] = {
            'first_access': datetime.now(),
            'last_access': datetime.now(),
            'access_count': 0,
            'total_bytes': len(file_content),
            'tier': tier.value
        }

        return locations

    async def _store_to_storage(self, file_content: bytes, filename: str,
                               file_id: str, storage_type: StorageType,
                               tier: StorageTier) -> FileLocation:
        """存储到特定存储后端"""
        config = self.storage_configs[storage_type]
        storage_path = self._generate_storage_path(file_id, filename, tier)

        if storage_type == StorageType.LOCAL:
            return await self._store_local(file_content, storage_path, config, tier)
        elif storage_type == StorageType.S3:
            return await self._store_s3(file_content, storage_path, config, tier)
        elif storage_type == StorageType.ALIYUN_OSS:
            return await self._store_oss(file_content, storage_path, config, tier)
        elif storage_type == StorageType.TENCENT_COS:
            return await self._store_cos(file_content, storage_path, config, tier)
        else:
            raise ValueError(f"不支持的存储类型: {storage_type}")

    def _generate_storage_path(self, file_id: str, filename: str, tier: StorageTier) -> str:
        """生成存储路径"""
        file_ext = Path(filename).suffix
        # 使用文件ID的前两位作为目录分片
        prefix = file_id[:2]
        return f"{tier.value}/{prefix}/{file_id}{file_ext}"

    async def _store_local(self, file_content: bytes, storage_path: str,
                         config: StorageConfig, tier: StorageTier) -> FileLocation:
        """存储到本地"""
        full_path = Path(config.base_path) / storage_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(full_path, 'wb') as f:
            await f.write(file_content)

        return FileLocation(
            storage_type=StorageType.LOCAL,
            storage_path=str(full_path),
            size=len(file_content),
            last_modified=datetime.now(),
            etag=hashlib.md5(file_content, usedforsecurity=False).hexdigest(),
            tier=tier
        )

    async def _store_s3(self, file_content: bytes, storage_path: str,
                       config: StorageConfig, tier: StorageTier) -> FileLocation:
        """存储到S3"""
        client = self.storage_clients[StorageType.S3]

        try:
            # 上传文件
            response = client.put_object(
                Bucket=config.bucket_name,
                Key=storage_path,
                Body=file_content,
                ContentType=mimetypes.guess_type(storage_path)[0]
            )

            return FileLocation(
                storage_type=StorageType.S3,
                storage_path=storage_path,
                bucket_name=config.bucket_name,
                region=config.region,
                url=f"https://{config.bucket_name}.s3.{config.region}.amazonaws.com/{storage_path}",
                size=len(file_content),
                etag=response.get('ETag', '').strip('"'),
                tier=tier
            )

        except ClientError as e:
            logger.error(f"S3上传失败: {e}")
            raise

    async def _store_oss(self, file_content: bytes, storage_path: str,
                        config: StorageConfig, tier: StorageTier) -> FileLocation:
        """存储到阿里云OSS"""
        bucket = self.storage_clients[StorageType.ALIYUN_OSS]

        try:
            result = bucket.put_object(storage_path, file_content)

            return FileLocation(
                storage_type=StorageType.ALIYUN_OSS,
                storage_path=storage_path,
                bucket_name=config.bucket_name,
                endpoint=config.endpoint,
                url=f"https://{config.bucket_name}.{config.endpoint}/{storage_path}",
                size=len(file_content),
                etag=result.etag,
                tier=tier
            )

        except Exception as e:
            logger.error(f"OSS上传失败: {e}")
            raise

    async def _store_cos(self, file_content: bytes, storage_path: str,
                        config: StorageConfig, tier: StorageTier) -> FileLocation:
        """存储到腾讯云COS"""
        client = self.storage_clients[StorageType.TENCENT_COS]

        try:
            response = client.put_object(
                Bucket=config.bucket_name,
                Key=storage_path,
                Body=file_content
            )

            return FileLocation(
                storage_type=StorageType.TENCENT_COS,
                storage_path=storage_path,
                bucket_name=config.bucket_name,
                region=config.region,
                url=f"https://{config.bucket_name}.cos.{config.region}.myqcloud.com/{storage_path}",
                size=len(file_content),
                etag=response['ETag'],
                tier=tier
            )

        except CosClientError as e:
            logger.error(f"COS上传失败: {e}")
            raise

    async def retrieve_file(self, file_id: str, preferred_storage: StorageType = None) -> bytes:
        """从分布式存储检索文件"""
        # 更新访问模式
        if file_id in self.access_patterns:
            self.access_patterns[file_id]['last_access'] = datetime.now()
            self.access_patterns[file_id]['access_count'] += 1

        # 尝试从首选存储检索
        if preferred_storage and preferred_storage in self.storage_configs:
            try:
                return await self._retrieve_from_storage(file_id, preferred_storage)
            except Exception as e:
                logger.warning(f"从 {preferred_storage.value} 检索失败: {e}")

        # 按层级顺序尝试检索
        for tier in [StorageTier.HOT, StorageTier.WARM, StorageTier.COLD]:
            storage_types = self.tier_routing.get(tier, [])
            for storage_type in storage_types:
                if storage_type in self.storage_configs:
                    try:
                        return await self._retrieve_from_storage(file_id, storage_type)
                    except Exception:
                        continue

        raise FileNotFoundError(f"文件 {file_id} 在所有存储中都未找到")

    async def _retrieve_from_storage(self, file_id: str, storage_type: StorageType) -> bytes:
        """从特定存储检索文件"""
        # 这里需要实现具体的检索逻辑
        # 实际使用时应该从数据库或元数据中查找文件的存储位置
        raise NotImplementedError("需要实现具体的文件位置查找逻辑")

    async def delete_file(self, file_id: str) -> bool:
        """从所有存储中删除文件"""
        success = True
        for storage_type in self.storage_configs.keys():
            try:
                await self._delete_from_storage(file_id, storage_type)
            except Exception as e:
                logger.error(f"从 {storage_type.value} 删除失败: {e}")
                success = False

        # 清理访问模式记录
        self.access_patterns.pop(file_id, None)

        return success

    async def _delete_from_storage(self, file_id: str, storage_type: StorageType):
        """从特定存储删除文件"""
        # 这里需要实现具体的删除逻辑
        raise NotImplementedError("需要实现具体的文件位置查找和删除逻辑")

    async def migrate_file(self, file_id: str, target_tier: StorageTier) -> bool:
        """迁移文件到不同存储层级"""
        try:
            # 1. 检索文件内容
            file_content = await self.retrieve_file(file_id)

            # 2. 存储到目标层级
            await self.store_file(
                file_content, f"migrated_{file_id}", file_id, target_tier, replicate=False
            )

            # 3. 删除旧位置的文件（可选）
            # await self.delete_file(file_id)

            # 4. 更新访问模式
            if file_id in self.access_patterns:
                self.access_patterns[file_id]['tier'] = target_tier.value

            logger.info(f"文件 {file_id} 已迁移到 {target_tier.value}")
            return True

        except Exception as e:
            logger.error(f"文件迁移失败: {e}")
            return False

    async def optimize_storage(self) -> dict[str, Any]:
        """优化存储布局"""
        optimized_files = 0
        freed_space = 0

        for file_id, pattern in self.access_patterns.items():
            current_tier = StorageTier(pattern['tier'])
            optimal_tier = self.determine_storage_tier(
                file_id, pattern.get('total_bytes', 0)
            )

            if current_tier != optimal_tier:
                if await self.migrate_file(file_id, optimal_tier):
                    optimized_files += 1
                    # 估算释放的空间（简化计算）
                    if optimal_tier.value < current_tier.value:
                        freed_space += pattern.get('total_bytes', 0)

        return {
            "optimized_files": optimized_files,
            "estimated_freed_space": freed_space,
            "total_files": len(self.access_patterns)
        }

    def get_storage_stats(self) -> dict[str, Any]:
        """获取存储统计信息"""
        stats = {
            "configured_storages": [t.value for t in self.storage_configs.keys()],
            "default_storage": self.default_storage.value,
            "replication_enabled": self.replication_enabled,
            "total_files": len(self.access_patterns),
            "tier_distribution": {}
        }

        # 统计各层级的文件数量
        for _file_id, pattern in self.access_patterns.items():
            tier = pattern.get('tier', 'hot')
            stats["tier_distribution"][tier] = stats["tier_distribution"].get(tier, 0) + 1

        return stats

    async def cleanup_expired_files(self) -> int:
        """清理过期文件"""
        current_time = datetime.now()
        expired_files = []

        for file_id, pattern in self.access_patterns.items():
            retention_days = pattern.get('retention_days', 30)
            last_access = pattern.get('last_access', pattern.get('first_access', current_time))

            if (current_time - last_access).days > retention_days:
                expired_files.append(file_id)

        # 删除过期文件
        deleted_count = 0
        for file_id in expired_files:
            if await self.delete_file(file_id):
                deleted_count += 1

        logger.info(f"清理了 {deleted_count} 个过期文件")
        return deleted_count

# 全局分布式存储管理器实例
distributed_storage = DistributedStorageManager()

# 使用示例
async def example_usage():
    """使用示例"""
    # 配置本地存储
    local_config = StorageConfig(
        storage_type=StorageType.LOCAL,
        tier=StorageTier.HOT,
        base_path="/tmp/distributed_storage"
    )
    distributed_storage.add_storage_config(local_config)

    # 配置S3存储（如果可用）
    if AWS_AVAILABLE:
        s3_config = StorageConfig(
            storage_type=StorageType.S3,
            tier=StorageTier.WARM,
            access_key="your_access_key",
            secret_key="your_secret_key",
            region="us-west-2",
            bucket_name="your-bucket"
        )
        distributed_storage.add_storage_config(s3_config)

    # 存储文件
    file_content = b"Hello, distributed storage!"
    locations = await distributed_storage.store_file(file_content, "test.txt")

    print(f"文件存储位置: {asdict(locations[0])}")

    # 检索文件
    retrieved_content = await distributed_storage.retrieve_file(locations[0].etag)
    print(f"检索内容: {retrieved_content}")

if __name__ == "__main__":
    asyncio.run(example_usage())
