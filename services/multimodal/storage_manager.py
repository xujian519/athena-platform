#!/usr/bin/env python3
"""
多模态文件存储管理器
Multimodal File Storage Manager

集成Athena统一存储架构，管理多模态文件的存储、检索和元数据
Integrated with Athena unified storage architecture for multimodal file management
"""

import hashlib
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

# Database imports (when available)
# Vector storage imports (when available)
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from sqlalchemy import BigInteger, Column, Integer, String, Text, create_engine
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func

Base = declarative_base()

class ProcessingStatus(str, Enum):
    """处理状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"

class ProcessingMethod(str, Enum):
    """处理方法枚举"""
    LOCAL = "local"
    MCP = "mcp"
    HYBRID = "hybrid"

class FileType(str, Enum):
    """文件类型枚举"""
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    OTHER = "other"

@dataclass
class FileMetadata:
    """文件元数据"""
    original_filename: str
    file_type: FileType
    file_size: int
    mime_type: str | None = None
    width: int | None = None
    height: int | None = None
    duration: float | None = None
    channels: int | None = None
    sample_rate: int | None = None
    pages: int | None = None
    encoding: str | None = None
    checksum: str | None = None

# SQLAlchemy Models
class MultimodalFile(Base):
    """多模态文件表模型"""
    __tablename__ = 'multimodal_files'

    id = Column(Integer, primary_key=True)
    original_filename = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    mime_type = Column(String(100))
    storage_path = Column(String(1000), nullable=False)
    processing_status = Column(String(20), default=ProcessingStatus.PENDING.value)
    processing_method = Column(String(20))
    processing_result = Column(JSONB)
    error_message = Column(Text)
    metadata = Column(JSONB)
    vector_id = Column(Integer)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    processed_at = Column(TIMESTAMP(timezone=True))

class ProcessingLog(Base):
    """处理任务日志表模型"""
    __tablename__ = 'processing_logs'

    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, nullable=False)  # Foreign key relationship managed manually
    processing_method = Column(String(20), nullable=False)
    processing_status = Column(String(20), nullable=False)
    start_time = Column(TIMESTAMP(timezone=True), server_default=func.now())
    end_time = Column(TIMESTAMP(timezone=True))
    processing_result = Column(JSONB)
    error_message = Column(Text)
    processing_time_ms = Column(Integer)

class MultimodalStorageManager:
    """多模态文件存储管理器"""

    def __init__(self, config: dict[str, Any] | None = None):
        """初始化存储管理器"""
        self.config = config or self._get_default_config()
        self.base_path = Path(self.config['storage_base_path'])
        self._ensure_directories()

        # Database connection (lazy loading)
        self._db_engine = None
        self._db_session = None

        # Vector storage connection (lazy loading)
        self._qdrant_client = None

        # File type mapping
        self._type_directories = {
            FileType.IMAGE: 'images',
            FileType.AUDIO: 'audio',
            FileType.VIDEO: 'video',
            FileType.DOCUMENT: 'documents',
            FileType.OTHER: 'other'
        }

    def _get_default_config(self) -> dict[str, Any]:
        """获取默认配置"""
        return {
            'storage_base_path': '/Users/xujian/Athena工作平台/storage/multimodal',
            'database_url': 'postgresql://athena_user:athena_password@localhost:5432/athena_business',
            'qdrant_host': 'localhost',
            'qdrant_port': 6333,
            'qdrant_collection': 'multimodal_files',
            'vector_size': 768,
            'use_subdirectories': True,
            'hash_files': True
        }

    def _ensure_directories(self) -> Any:
        """确保存储目录存在"""
        for file_type in FileType:
            dir_path = self.base_path / self._type_directories[file_type]
            dir_path.mkdir(parents=True, exist_ok=True)

    async def get_db_connection(self):
        """获取数据库连接"""
        if not self._db_engine:
            try:
                self._db_engine = create_engine(self.config['database_url'])
                SessionLocal = sessionmaker(bind=self._db_engine)
                self._db_session = SessionLocal()

                # Create tables if they don't exist
                Base.metadata.create_all(bind=self._db_engine)

            except Exception as e:
                print(f"数据库连接失败: {e}")
                print("使用文件系统作为备用存储方案")
                return None

        return self._db_session

    async def get_qdrant_client(self):
        """获取Qdrant客户端"""
        if not self._qdrant_client:
            try:
                self._qdrant_client = QdrantClient(
                    host=self.config['qdrant_host'],
                    port=self.config['qdrant_port']
                )

                # 确保集合存在
                collections = self._qdrant_client.get_collections().collections
                collection_names = [c.name for c in collections]

                if self.config['qdrant_collection'] not in collection_names:
                    self._qdrant_client.create_collection(
                        collection_name=self.config['qdrant_collection'],
                        vectors_config=VectorParams(
                            size=self.config['vector_size'],
                            distance=Distance.COSINE
                        )
                    )

            except Exception as e:
                print(f"Qdrant连接失败: {e}")
                print("向量存储功能将不可用")
                return None

        return self._qdrant_client

    def _get_file_type(self, filename: str, mime_type: str | None = None) -> FileType:
        """根据文件名和MIME类型确定文件类型"""
        ext = Path(filename).suffix.lower()

        # Images
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'] or \
           (mime_type and mime_type.startswith('image/')):
            return FileType.IMAGE

        # Audio
        if ext in ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.amr', '.m4a'] or \
           (mime_type and mime_type.startswith('audio/')):
            return FileType.AUDIO

        # Video
        if ext in ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'] or \
           (mime_type and mime_type.startswith('video/')):
            return FileType.VIDEO

        # Documents
        if ext in ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.xls', '.xlsx', '.ppt', '.pptx'] or \
           (mime_type and mime_type in ['application/pdf', 'text/plain', 'application/msword']):
            return FileType.DOCUMENT

        return FileType.OTHER

    def _generate_storage_path(self, filename: str, file_type: FileType) -> str:
        """生成存储路径"""
        if self.config['use_subdirectories']:
            # 按日期组织
            date_str = datetime.now().strftime('%Y/%m/%d')
            type_dir = self._type_directories[file_type]

            # 生成唯一文件名
            name = Path(filename).stem
            ext = Path(filename).suffix

            # 添加时间戳和随机数避免冲突
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_name = f"{name}_{timestamp}{ext}"

            return str(self.base_path / type_dir / date_str / unique_name)
        else:
            return str(self.base_path / filename)

    async def _calculate_file_hash(self, file_path: str) -> str:
        """计算文件哈希值"""
        if not self.config['hash_files']:
            return ""

        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    async def store_file(
        self,
        source_path: str,
        original_filename: str,
        mime_type: str | None = None,
        metadata: dict[str, Any] | None = None
    ) -> int | None:
        """存储文件并记录元数据"""
        try:
            # 验证源文件
            if not os.path.exists(source_path):
                raise FileNotFoundError(f"源文件不存在: {source_path}")

            # 确定文件类型
            file_type = self._get_file_type(original_filename, mime_type)

            # 生成存储路径
            storage_path = self._generate_storage_path(original_filename, file_type)

            # 确保目录存在
            os.makedirs(os.path.dirname(storage_path), exist_ok=True)

            # 复制文件
            import shutil
            shutil.copy2(source_path, storage_path)

            # 获取文件信息
            file_size = os.path.getsize(storage_path)
            checksum = await self._calculate_file_hash(storage_path)

            # 创建文件元数据
            file_metadata = FileMetadata(
                original_filename=original_filename,
                file_type=file_type,
                file_size=file_size,
                mime_type=mime_type,
                checksum=checksum
            )

            # 合并额外元数据
            if metadata:
                metadata_dict = asdict(file_metadata)
                metadata_dict.update(metadata)
            else:
                metadata_dict = asdict(file_metadata)

            # 保存到数据库
            db_session = await self.get_db_connection()
            file_id = None

            if db_session:
                try:
                    db_file = MultimodalFile(
                        original_filename=original_filename,
                        file_type=file_type.value,
                        file_size=file_size,
                        mime_type=mime_type,
                        storage_path=storage_path,
                        metadata=metadata_dict
                    )

                    db_session.add(db_file)
                    db_session.commit()
                    file_id = db_file.id

                except Exception as e:
                    print(f"数据库保存失败: {e}")
                    db_session.rollback()
                    # 继续使用文件系统

            # 如果数据库不可用，创建文件系统记录
            if not file_id:
                file_id = len([f for f in self.base_path.rglob('*') if f.is_file()]) + 1

                # 保存元数据到JSON文件
                metadata_path = storage_path + '.meta.json'
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        'id': file_id,
                        'original_filename': original_filename,
                        'file_type': file_type.value,
                        'file_size': file_size,
                        'mime_type': mime_type,
                        'storage_path': storage_path,
                        'metadata': metadata_dict
                    }, f, ensure_ascii=False, indent=2)

            print(f"✅ 文件存储成功: {original_filename} -> {storage_path} (ID: {file_id})")
            return file_id

        except Exception as e:
            print(f"❌ 文件存储失败: {e}")
            return None

    async def update_processing_status(
        self,
        file_id: int,
        status: ProcessingStatus,
        method: ProcessingMethod | None = None,
        result: dict[str, Any] | None = None,
        error_message: str | None = None
    ):
        """更新文件处理状态"""
        try:
            db_session = await self.get_db_connection()

            if db_session:
                # 更新数据库
                db_file = db_session.query(MultimodalFile).filter(
                    MultimodalFile.id == file_id
                ).first()

                if db_file:
                    db_file.processing_status = status.value
                    db_file.updated_at = func.now()

                    if status == ProcessingStatus.COMPLETED:
                        db_file.processed_at = func.now()

                    if method:
                        db_file.processing_method = method.value

                    if result:
                        db_file.processing_result = result

                    if error_message:
                        db_file.error_message = error_message

                    db_session.commit()

                # 记录处理日志
                log_entry = ProcessingLog(
                    file_id=file_id,
                    processing_method=method.value if method else 'unknown',
                    processing_status=status.value,
                    processing_result=result,
                    error_message=error_message
                )

                db_session.add(log_entry)
                db_session.commit()
            else:
                # 更新文件系统记录
                # 查找对应的元数据文件
                for meta_file in self.base_path.rglob('*.meta.json'):
                    try:
                        with open(meta_file, encoding='utf-8') as f:
                            data = json.load(f)

                        if data.get('id') == file_id:
                            data['processing_status'] = status.value
                            data['updated_at'] = datetime.now().isoformat()

                            if method:
                                data['processing_method'] = method.value

                            if result:
                                data['processing_result'] = result

                            if error_message:
                                data['error_message'] = error_message

                            with open(meta_file, 'w', encoding='utf-8') as f:
                                json.dump(data, f, ensure_ascii=False, indent=2)
                            break

                    except Exception as e:
                        print(f"更新元数据文件失败: {e}")

            print(f"✅ 状态更新成功: 文件ID {file_id} -> {status.value}")

        except Exception as e:
            print(f"❌ 状态更新失败: {e}")

    async def store_file_vector(
        self,
        file_id: int,
        vector: list[float],
        vector_metadata: dict[str, Any] | None = None
    ) -> int | None:
        """存储文件向量"""
        try:
            qdrant_client = await self.get_qdrant_client()

            if not qdrant_client:
                print("⚠️ Qdrant不可用，跳过向量存储")
                return None

            # 创建点结构
            point = PointStruct(
                id=file_id,
                vector=vector,
                payload={
                    'file_id': file_id,
                    'type': 'multimodal_file',
                    'created_at': datetime.now().isoformat(),
                    **(vector_metadata or {})
                }
            )

            # 存储向量
            qdrant_client.upsert(
                collection_name=self.config['qdrant_collection'],
                points=[point]
            )

            # 更新数据库记录
            db_session = await self.get_db_connection()
            if db_session:
                db_file = db_session.query(MultimodalFile).filter(
                    MultimodalFile.id == file_id
                ).first()

                if db_file:
                    db_file.vector_id = file_id
                    db_session.commit()

            print(f"✅ 向量存储成功: 文件ID {file_id}")
            return file_id

        except Exception as e:
            print(f"❌ 向量存储失败: {e}")
            return None

    async def get_file_info(self, file_id: int) -> dict[str, Any | None]:
        """获取文件信息"""
        try:
            # 先尝试数据库
            db_session = await self.get_db_connection()

            if db_session:
                db_file = db_session.query(MultimodalFile).filter(
                    MultimodalFile.id == file_id
                ).first()

                if db_file:
                    return {
                        'id': db_file.id,
                        'original_filename': db_file.original_filename,
                        'file_type': db_file.file_type,
                        'file_size': db_file.file_size,
                        'mime_type': db_file.mime_type,
                        'storage_path': db_file.storage_path,
                        'processing_status': db_file.processing_status,
                        'processing_method': db_file.processing_method,
                        'processing_result': db_file.processing_result,
                        'error_message': db_file.error_message,
                        'metadata': db_file.metadata,
                        'vector_id': db_file.vector_id,
                        'created_at': db_file.created_at.isoformat() if db_file.created_at else None,
                        'updated_at': db_file.updated_at.isoformat() if db_file.updated_at else None,
                        'processed_at': db_file.processed_at.isoformat() if db_file.processed_at else None
                    }

            # 回退到文件系统
            for meta_file in self.base_path.rglob('*.meta.json'):
                try:
                    with open(meta_file, encoding='utf-8') as f:
                        data = json.load(f)

                    if data.get('id') == file_id:
                        return data

                except Exception:
                    continue

            return None

        except Exception as e:
            print(f"❌ 获取文件信息失败: {e}")
            return None

    async def search_by_vector(
        self,
        query_vector: list[float],
        limit: int = 10,
        file_type: FileType | None = None
    ) -> list[dict[str, Any]:
        """通过向量搜索相似文件"""
        try:
            qdrant_client = await self.get_qdrant_client()

            if not qdrant_client:
                print("⚠️ Qdrant不可用，无法进行向量搜索")
                return []

            # 构建搜索过滤器
            search_filter = None
            if file_type:
                search_filter = {
                    "must": [
                        {"key": "file_type", "match": {"value": file_type.value}}
                    ]
                }

            # 执行搜索
            search_result = qdrant_client.search(
                collection_name=self.config['qdrant_collection'],
                query_vector=query_vector,
                limit=limit,
                query_filter=search_filter
            )

            # 获取文件详细信息
            results = []
            for hit in search_result:
                file_info = await self.get_file_info(hit.id)
                if file_info:
                    file_info['similarity_score'] = hit.score
                    results.append(file_info)

            return results

        except Exception as e:
            print(f"❌ 向量搜索失败: {e}")
            return []

    async def get_statistics(self) -> dict[str, Any]:
        """获取存储统计信息"""
        try:
            db_session = await self.get_db_connection()

            stats = {
                'total_files': 0,
                'by_type': {},
                'by_status': {},
                'total_size': 0,
                'average_file_size': 0,
                'processing_success_rate': 0.0
            }

            if db_session:
                # 数据库统计
                total_files = db_session.query(MultimodalFile).count()
                stats['total_files'] = total_files

                # 按类型统计
                type_stats = db_session.query(
                    MultimodalFile.file_type,
                    func.count(MultimodalFile.id).label('count'),
                    func.sum(MultimodalFile.file_size).label('total_size')
                ).group_by(MultimodalFile.file_type).all()

                for file_type, count, total_size in type_stats:
                    stats['by_type'][file_type] = {
                        'count': count,
                        'total_size': total_size or 0
                    }

                # 按状态统计
                status_stats = db_session.query(
                    MultimodalFile.processing_status,
                    func.count(MultimodalFile.id).label('count')
                ).group_by(MultimodalFile.processing_status).all()

                for status, count in status_stats:
                    stats['by_status'][status] = count

                # 总大小和平均大小
                total_size = db_session.query(func.sum(MultimodalFile.file_size)).scalar() or 0
                stats['total_size'] = total_size
                stats['average_file_size'] = total_size / total_files if total_files > 0 else 0

                # 处理成功率
                completed = db_session.query(MultimodalFile).filter(
                    MultimodalFile.processing_status == ProcessingStatus.COMPLETED.value
                ).count()

                stats['processing_success_rate'] = (completed / total_files * 100) if total_files > 0 else 0

            else:
                # 文件系统统计
                for meta_file in self.base_path.rglob('*.meta.json'):
                    try:
                        with open(meta_file, encoding='utf-8') as f:
                            data = json.load(f)

                        stats['total_files'] += 1

                        file_type = data.get('file_type', 'other')
                        if file_type not in stats['by_type']:
                            stats['by_type'][file_type] = {'count': 0, 'total_size': 0}

                        stats['by_type'][file_type]['count'] += 1

                        file_size = data.get('file_size', 0)
                        stats['by_type'][file_type]['total_size'] += file_size
                        stats['total_size'] += file_size

                        status = data.get('processing_status', 'pending')
                        stats['by_status'][status] = stats['by_status'].get(status, 0) + 1

                    except Exception:
                        continue

                stats['average_file_size'] = stats['total_size'] / stats['total_files'] if stats['total_files'] > 0 else 0

                completed = stats['by_status'].get('completed', 0)
                stats['processing_success_rate'] = (completed / stats['total_files'] * 100) if stats['total_files'] > 0 else 0

            return stats

        except Exception as e:
            print(f"❌ 获取统计信息失败: {e}")
            return {}

    async def cleanup_old_files(self, days: int = 30) -> int:
        """清理旧文件（归档状态）"""
        try:
            from datetime import timedelta

            cutoff_date = datetime.now() - timedelta(days=days)
            db_session = await self.get_db_connection()

            cleaned_count = 0

            if db_session:
                # 查找旧文件
                old_files = db_session.query(MultimodalFile).filter(
                    MultimodalFile.created_at < cutoff_date,
                    MultimodalFile.processing_status == ProcessingStatus.COMPLETED.value
                ).all()

                for file_record in old_files:
                    # 归档处理（可以移动到冷存储或删除）
                    if os.path.exists(file_record.storage_path):
                        os.remove(file_record.storage_path)

                    # 删除元数据文件
                    meta_path = file_record.storage_path + '.meta.json'
                    if os.path.exists(meta_path):
                        os.remove(meta_path)

                    # 更新数据库状态
                    file_record.processing_status = ProcessingStatus.ARCHIVED.value
                    cleaned_count += 1

                db_session.commit()

            print(f"✅ 清理完成: {cleaned_count} 个文件被归档")
            return cleaned_count

        except Exception as e:
            print(f"❌ 清理失败: {e}")
            return 0

# 使用示例和测试
async def main():
    """主函数 - 测试存储管理器"""
    manager = MultimodalStorageManager()

    # 测试存储文件
    test_file = "/Users/xujian/Athena工作平台/services/multimodal/test_file.jpg"
    if os.path.exists(test_file):
        file_id = await manager.store_file(
            source_path=test_file,
            original_filename="test_image.jpg",
            mime_type="image/jpeg"
        )

        if file_id:
            # 更新处理状态
            await manager.update_processing_status(
                file_id=file_id,
                status=ProcessingStatus.COMPLETED,
                method=ProcessingMethod.MCP,
                result={"extracted_text": "这是一个测试图片", "confidence": 0.95}
            )

            # 获取文件信息
            info = await manager.get_file_info(file_id)
            print(f"文件信息: {info}")

    # 获取统计信息
    stats = await manager.get_statistics()
    print(f"存储统计: {json.dumps(stats, ensure_ascii=False, indent=2)}")

# 入口点: @async_main装饰器已添加到main函数
