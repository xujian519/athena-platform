# 原文件存储技术栈方案

## ✅ 修正方案：PostgreSQL元数据 + 文件系统存储

### 为什么PostgreSQL比SQLite更好？

| 特性 | SQLite | PostgreSQL |
|------|--------|------------|
| **并发访问** | ❌ 单线程锁 | ✅ 多用户并发 |
| **ACID事务** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ 完整ACID |
| **全文搜索** | ❌ 需要扩展 | ✅ 内置FTS |
| **JSON支持** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ JSONB |
| **索引优化** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ 多种索引 |
| **备份恢复** | ⭐⭐ | ⭐⭐⭐⭐⭐ 专业工具 |
| **监控工具** | ⭐⭐ | ⭐⭐⭐⭐⭐ 丰富生态 |
| **未来扩展** | ⭐ | ⭐⭐⭐⭐⭐ 可集群 |

## 🏗️ 架构设计

### 存储架构图
```
┌─────────────────────────────────────────────────────────┐
│                    云熙文档管理系统                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │  客户端A    │  │  客户端B    │  │  本地上传   │    │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘    │
│         │                 │                 │          │
│    HTTP REST API    HTTP REST API    本地文件操作      │
│         │                 │                 │          │
└─────────┼─────────────────┼─────────────────┼──────────┘
          │                 │                 │
          └─────────────────┴─────────────────┘
                            │
                    ┌───────▼────────┐
                    │  存储管理器      │
                    │ StorageManager  │
                    └───────┬────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼───────┐  ┌───────▼───────┐  ┌───────▼───────┐
│ PostgreSQL    │  │  文件系统      │  │  备份系统     │
│              │  │              │  │              │
│ • 元数据      │  │ • 原文件存储   │  │ • 每月备份    │
│ • 版本控制    │  │ • 文件组织     │  │ • 压缩归档    │
│ • 权限管理    │  │ • 文件访问     │  │ • 异地存储    │
│ • 全文索引    │  │ • 文件预览     │  │ • 恢复机制    │
└───────────────┘  └───────────────┘  └───────────────┘
```

### PostgreSQL数据库设计

```sql
-- 创建文档管理数据库
CREATE DATABASE document_management;
\c document_management;

-- 文档主表
CREATE TABLE documents (
    document_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    original_name VARCHAR(500) NOT NULL,
    stored_name VARCHAR(100) UNIQUE NOT NULL,
    file_path TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    file_hash TEXT NOT NULL,
    mime_type VARCHAR(100),

    -- 分类信息
    document_type VARCHAR(50) NOT NULL, -- patent/trademark/copyright/contract
    client_id VARCHAR(50),
    project_id VARCHAR(50),
    folder_path TEXT, -- virtual folder path

    -- 元数据
    metadata JSONB, -- extended metadata

    -- 状态信息
    status VARCHAR(20) DEFAULT 'active', -- active/archived/deleted
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP,

    -- 审计信息
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    updated_by VARCHAR(50),

    -- 版本控制
    version INTEGER DEFAULT 1,
    parent_document_id UUID REFERENCES documents(document_id),

    -- 索引
    INDEX idx_documents_type (document_type),
    INDEX idx_documents_client (client_id),
    INDEX idx_documents_project (project_id),
    INDEX idx_documents_status (status),
    INDEX idx_documents_created (created_at),
    INDEX idx_documents_metadata USING GIN(metadata),
    INDEX idx_documents_hash (file_hash)
);

-- 文档版本表
CREATE TABLE document_versions (
    version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(document_id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    file_hash TEXT NOT NULL,
    change_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),

    UNIQUE(document_id, version_number)
);

-- 文档标签表
CREATE TABLE document_tags (
    tag_id SERIAL PRIMARY KEY,
    document_id UUID REFERENCES documents(document_id) ON DELETE CASCADE,
    tag_name VARCHAR(50) NOT NULL,
    tag_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(document_id, tag_name)
);

-- 文档访问日志表
CREATE TABLE document_access_logs (
    log_id BIGSERIAL PRIMARY KEY,
    document_id UUID REFERENCES documents(document_id),
    access_type VARCHAR(20) NOT NULL, -- view/download/upload/delete
    client_ip INET,
    user_agent TEXT,
    access_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id VARCHAR(50)
);

-- 全文搜索配置
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;

-- 全文搜索向量
ALTER TABLE documents ADD COLUMN search_vector tsvector;

-- 创建全文搜索更新函数
CREATE OR REPLACE FUNCTION update_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('simple', COALESCE(NEW.original_name, '')), 'A') ||
        setweight(to_tsvector('simple', COALESCE(NEW.metadata::text, '')), 'B');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 创建触发器
CREATE TRIGGER update_document_search_vector
    BEFORE INSERT OR UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_search_vector();

-- 全文搜索索引
CREATE INDEX idx_documents_search ON documents USING GIN(search_vector);
```

### 文件系统组织结构

```
/data/local/documents/
├── uploads/                 # 客户端上传
│   ├── 2024/
│   │   ├── 01/
│   │   │   ├── patent/
│   │   │   ├── trademark/
│   │   │   └── copyright/
│   │   └── 02/
│   └── 2023/
│
├── projects/               # 项目文档
│   ├── project_001/
│   │   ├── apps/patents/
│   │   ├── contracts/
│   │   └── correspondence/
│   └── project_002/
│
├── archives/               # 归档文档
│   ├── 2022/
│   └── 2021/
│
├── temp/                   # 临时文件
└── preview/                # 预览文件
    ├── thumbnails/
    ├── pdf_previews/
    └── image_previews/
```

## 💻 实现代例

### 1. 文档管理器核心类

```python
import os
import hashlib
import shutil
from datetime import datetime
from pathlib import Path
import psycopg2
from psycopg2 import sql, extras
from typing import Optional, List, Dict, Any

class DocumentStorageManager:
    """文档存储管理器"""

    def __init__(self, db_config: Dict[str, Any], storage_root: str):
        self.db_config = db_config
        self.storage_root = Path(storage_root)
        self.storage_root.mkdir(parents=True, exist_ok=True)

        # 初始化目录结构
        self._init_directories()

    def _init_directories(self):
        """初始化目录结构"""
        directories = [
            'uploads', 'projects', 'archives', 'temp', 'preview'
        ]
        for dir_name in directories:
            (self.storage_root / dir_name).mkdir(exist_ok=True)

    def upload_document(self, file_content: bytes, original_name: str,
                       document_type: str, client_id: Optional[str] = None,
                       project_id: Optional[str] = None,
                       metadata: Optional[Dict] = None) -> str:
        """上传文档"""
        # 1. 计算文件hash
        file_hash = self._calculate_hash(file_content)

        # 2. 检查是否已存在
        existing_doc = self._get_document_by_hash(file_hash)
        if existing_doc and existing_doc['status'] == 'active':
            return existing_doc['document_id']

        # 3. 生成存储文件名
        stored_name = self._generate_stored_name(original_name, file_hash)

        # 4. 确定存储路径
        year_month = datetime.now().strftime('%Y/%m')
        storage_path = self.storage_root / 'uploads' / year_month / document_type
        storage_path.mkdir(parents=True, exist_ok=True)

        file_path = storage_path / stored_name

        # 5. 保存文件
        with open(file_path, 'wb') as f:
            f.write(file_content)

        # 6. 保存到数据库
        document_id = self._save_to_database({
            'original_name': original_name,
            'stored_name': stored_name,
            'file_path': str(file_path),
            'file_size': len(file_content),
            'file_hash': file_hash,
            'mime_type': self._get_mime_type(original_name),
            'document_type': document_type,
            'client_id': client_id,
            'project_id': project_id,
            'metadata': metadata or {}
        })

        return document_id

    def get_document(self, document_id: str) -> Optional[Dict]:
        """获取文档信息"""
        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM documents
                    WHERE document_id = %s AND status = 'active'
                """, (document_id,))
                result = cur.fetchone()

                if result:
                    # 记录访问
                    self._log_access(document_id, 'view')
                    # 更新访问统计
                    self._update_access_stats(document_id)

                return dict(result) if result else None

    def download_document(self, document_id: str) -> Optional[str]:
        """获取文档下载路径"""
        doc_info = self.get_document(document_id)
        if not doc_info:
            return None

        file_path = doc_info['file_path']
        if not os.path.exists(file_path):
            return None

        # 记录下载
        self._log_access(document_id, 'download')

        return file_path

    def search_documents(self, query: str, filters: Optional[Dict] = None,
                        limit: int = 50, offset: int = 0) -> List[Dict]:
        """搜索文档"""
        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # 构建搜索查询
                sql_query = """
                    SELECT *, ts_rank(search_vector, plainto_tsquery(%s)) as rank
                    FROM documents
                    WHERE status = 'active'
                """
                params = [query]

                # 添加搜索条件
                if query:
                    sql_query += " AND search_vector @@ plainto_tsquery(%s)"

                # 添加过滤条件
                if filters:
                    if 'document_type' in filters:
                        sql_query += " AND document_type = %s"
                        params.append(filters['document_type'])

                    if 'client_id' in filters:
                        sql_query += " AND client_id = %s"
                        params.append(filters['client_id'])

                    if 'date_from' in filters:
                        sql_query += " AND created_at >= %s"
                        params.append(filters['date_from'])

                    if 'date_to' in filters:
                        sql_query += " AND created_at <= %s"
                        params.append(filters['date_to'])

                # 排序和分页
                if query:
                    sql_query += " ORDER BY rank DESC"
                else:
                    sql_query += " ORDER BY created_at DESC"

                sql_query += " LIMIT %s OFFSET %s"
                params.extend([limit, offset])

                cur.execute(sql_query, params)
                return [dict(row) for row in cur.fetchall()]

    def create_document_version(self, document_id: str,
                              new_file_content: bytes,
                              change_description: str) -> str:
        """创建文档版本"""
        # 获取当前文档信息
        doc_info = self.get_document(document_id)
        if not doc_info:
            raise ValueError("Document not found")

        # 获取下一版本号
        next_version = doc_info['version'] + 1

        # 生成新文件名
        original_name = doc_info['original_name']
        name, ext = os.path.splitext(original_name)
        version_name = f"{name}_v{next_version}{ext}"

        # 保存新版本文件
        version_path = self.storage_root / 'versions' / document_id
        version_path.mkdir(parents=True, exist_ok=True)

        new_file_path = version_path / version_name

        with open(new_file_path, 'wb') as f:
            f.write(new_file_content)

        # 保存版本信息到数据库
        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor() as cur:
                # 插入版本记录
                cur.execute("""
                    INSERT INTO document_versions
                    (document_id, version_number, file_path, file_size,
                     file_hash, change_description)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING version_id
                """, (
                    document_id,
                    next_version,
                    str(new_file_path),
                    len(new_file_content),
                    self._calculate_hash(new_file_content),
                    change_description
                ))

                version_id = cur.fetchone()[0]

                # 更新主表版本号
                cur.execute("""
                    UPDATE documents
                    SET version = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE document_id = %s
                """, (next_version, document_id))

                conn.commit()

        return version_id

    def backup_documents(self, backup_path: str) -> bool:
        """备份文档系统"""
        try:
            backup_date = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = Path(backup_path) / f"athena_docs_{backup_date}"
            backup_dir.mkdir(parents=True, exist_ok=True)

            # 1. 备份文件系统
            shutil.copytree(
                self.storage_root,
                backup_dir / 'files',
                ignore=shutil.ignore_patterns('temp', '*.tmp')
            )

            # 2. 备份数据库
            pg_dump_cmd = [
                'pg_dump',
                '-h', self.db_config['host'],
                '-p', str(self.db_config['port']),
                '-U', self.db_config['user'],
                '-d', self.db_config['infrastructure/infrastructure/database'],
                '-f', str(backup_dir / 'documents.sql')
            ]

            subprocess.run(pg_dump_cmd, check=True)

            # 3. 创建压缩包
            backup_archive = f"{backup_dir}.tar.gz"
            shutil.make_archive(
                str(backup_dir.parent / backup_dir.name),
                'gztar',
                root_dir=backup_dir.parent,
                base_dir=backup_dir.name
            )

            # 4. 清理临时目录
            shutil.rmtree(backup_dir)

            return True

        except Exception as e:
            logging.error(f"Backup failed: {e}")
            return False
```

### 2. HTTP API接口（使用FastAPI）

```python
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Query
from fastapi.responses import FileResponse
from typing import Optional, List
import aiofiles

app = FastAPI(title="Athena文档管理系统", version="1.0.0")

# 全局文档管理器
doc_manager = DocumentStorageManager(
    db_config={
        'host': 'localhost',
        'port': 5432,
        'infrastructure/infrastructure/database': 'document_management',
        'user': 'athena',
        'password': 'your_password'
    },
    storage_root='/data/local/documents'
)

@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Query(...),
    client_id: Optional[str] = Query(None),
    project_id: Optional[str] = Query(None)
):
    """上传文档"""
    try:
        # 读取文件内容
        async with aiofiles.open(file.filename, 'wb') as f:
            content = await file.read()

        # 上传文档
        document_id = doc_manager.upload_document(
            file_content=content,
            original_name=file.filename,
            document_type=document_type,
            client_id=client_id,
            project_id=project_id
        )

        return {
            "document_id": document_id,
            "message": "Document uploaded successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/{document_id}")
async def download_document(document_id: str):
    """下载文档"""
    file_path = doc_manager.download_document(document_id)

    if not file_path:
        raise HTTPException(status_code=404, detail="Document not found")

    doc_info = doc_manager.get_document(document_id)

    return FileResponse(
        path=file_path,
        filename=doc_info['original_name'],
        media_type=doc_info['mime_type']
    )

@app.get("/search")
async def search_documents(
    q: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    client: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0)
):
    """搜索文档"""
    filters = {}
    if type:
        filters['document_type'] = type
    if client:
        filters['client_id'] = client

    results = doc_manager.search_documents(
        query=q or "",
        filters=filters if filters else None,
        limit=limit,
        offset=offset
    )

    return {
        "reports/reports/results": results,
        "total": len(results)
    }

@app.get("/metadata/{document_id}")
async def get_document_metadata(document_id: str):
    """获取文档元数据"""
    metadata = doc_manager.get_document(document_id)

    if not metadata:
        raise HTTPException(status_code=404, detail="Document not found")

    # 移除文件路径等敏感信息
    del metadata['file_path']

    return metadata

@app.post("/backup")
async def trigger_backup():
    """触发备份"""
    success = doc_manager.backup_documents('/backup/documents')

    if success:
        return {"message": "Backup triggered successfully"}
    else:
        raise HTTPException(status_code=500, detail="Backup failed")
```

## 📋 实施计划

### 第一阶段：基础设施搭建（3天）
- PostgreSQL数据库创建和初始化
- 文件目录结构创建
- 基础存储管理器实现

### 第二阶段：核心功能开发（5天）
- 文档上传下载功能
- 元数据管理
- 全文搜索功能
- 版本控制系统

### 第三阶段：API接口开发（3天）
- FastAPI服务搭建
- RESTful API实现
- 客户端访问测试

### 第四阶段：备份和优化（2天）
- 自动备份脚本
- 性能优化
- 监控告警

## ✅ 方案优势

1. **PostgreSQL优势**
   - 完善的ACID事务支持
   - 强大的JSONB和全文搜索
   - 优秀的并发性能
   - 丰富的监控工具

2. **文件系统优势**
   - 直接存储，无性能损耗
   - 支持任何文件类型
   - 简单的备份恢复
   - 与现有备份策略兼容

3. **扩展性**
   - 可以轻松迁移到PostgreSQL集群
   - 文件存储可以迁移到对象存储
   - API设计支持多客户端

这个方案完全满足云熙智能体的文档管理需求！