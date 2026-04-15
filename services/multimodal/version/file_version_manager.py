#!/usr/bin/env python3
"""
文件版本管理器
File Version Manager

支持文件的版本控制、历史记录、差异对比和回滚功能
"""

import asyncio
import difflib
import hashlib
import json
import logging
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

import aiofiles

logger = logging.getLogger(__name__)

class ChangeType(Enum):
    """变更类型"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    RENAME = "rename"
    MOVE = "move"
    COPY = "copy"

@dataclass
class FileVersion:
    """文件版本"""
    version_id: str
    file_id: str
    version_number: int
    created_at: datetime
    created_by: str
    change_type: ChangeType
    file_name: str
    file_path: str
    file_size: int
    file_hash: str
    mime_type: str | None = None
    metadata: dict[str, Any] = None
    parent_version_id: str | None = None
    branch_name: str | None = None
    tags: list[str] = None
    comment: str | None = None
    storage_path: str | None = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.tags is None:
            self.tags = []

@dataclass
class VersionDiff:
    """版本差异"""
    old_version_id: str
    new_version_id: str
    diff_type: str  # text, binary, metadata
    changes: list[dict[str, Any]]
    summary: str

class FileVersionManager:
    """文件版本管理器"""

    def __init__(self, storage_path: str = "/tmp/file_versions"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.metadata_path = self.storage_path / "metadata"
        self.metadata_path.mkdir(exist_ok=True)
        self.versions_path = self.storage_path / "versions"
        self.versions_path.mkdir(exist_ok=True)

        # 版本数据库
        self.versions_db: dict[str, list[FileVersion]] = {}  # file_id -> versions
        self.version_index: dict[str, FileVersion] = {}  # version_id -> version

        # 版本策略配置
        self.max_versions_per_file = 50
        self.max_storage_days = 365
        self.compression_enabled = True
        self.diff_storage_enabled = True

    async def create_version(self, file_id: str, file_content: bytes,
                           file_name: str, user_id: str,
                           change_type: ChangeType = ChangeType.UPDATE,
                           parent_version_id: str = None,
                           branch_name: str = None,
                           comment: str = None,
                           metadata: dict[str, Any] = None) -> FileVersion:
        """创建文件版本"""
        try:
            # 生成版本信息
            version_number = self._get_next_version_number(file_id)
            version_id = str(uuid.uuid4())
            file_hash = hashlib.sha256(file_content).hexdigest()
            mime_type = self._get_mime_type(file_name)

            # 检查是否实际发生变化
            if parent_version_id:
                parent_version = self.version_index.get(parent_version_id)
                if parent_version and parent_version.file_hash == file_hash:
                    logger.info(f"文件 {file_id} 内容未发生变化，跳过版本创建")
                    return parent_version

            # 存储文件内容
            storage_path = await self._store_version_content(
                version_id, file_content, parent_version_id
            )

            # 创建版本对象
            version = FileVersion(
                version_id=version_id,
                file_id=file_id,
                version_number=version_number,
                created_at=datetime.now(),
                created_by=user_id,
                change_type=change_type,
                file_name=file_name,
                file_path=f"{file_id}/{version_id}",
                file_size=len(file_content),
                file_hash=file_hash,
                mime_type=mime_type,
                metadata=metadata or {},
                parent_version_id=parent_version_id,
                branch_name=branch_name,
                comment=comment,
                storage_path=storage_path
            )

            # 保存版本元数据
            await self._save_version_metadata(version)

            # 更新内存索引
            self._update_indices(version)

            logger.info(f"创建文件版本: {file_id} v{version_number} ({version_id})")

            return version

        except Exception as e:
            logger.error(f"创建文件版本失败: {e}")
            raise

    def _get_next_version_number(self, file_id: str) -> int:
        """获取下一个版本号"""
        versions = self.versions_db.get(file_id, [])
        if not versions:
            return 1
        return max(v.version_number for v in versions) + 1

    def _get_mime_type(self, filename: str) -> str | None:
        """获取MIME类型"""
        import mimetypes
        return mimetypes.guess_type(filename)[0]

    async def _store_version_content(self, version_id: str, file_content: bytes,
                                   parent_version_id: str = None) -> str:
        """存储版本内容"""
        if self.diff_storage_enabled and parent_version_id:
            # 使用差异存储
            parent_version = self.version_index.get(parent_version_id)
            if parent_version:
                # 读取父版本内容
                parent_content = await self._load_version_content(parent_version_id)

                # 计算差异
                diff = self._calculate_binary_diff(parent_content, file_content)

                # 存储差异
                diff_path = self.versions_path / f"{version_id}.diff"
                async with aiofiles.open(diff_path, 'wb') as f:
                    await f.write(diff)

                return str(diff_path)

        # 完整存储
        version_path = self.versions_path / f"{version_id}.bin"

        if self.compression_enabled:
            import gzip
            file_content = gzip.compress(file_content)
            version_path = self.versions_path / f"{version_id}.gz"

        async with aiofiles.open(version_path, 'wb') as f:
            await f.write(file_content)

        return str(version_path)

    async def _load_version_content(self, version_id: str) -> bytes:
        """加载版本内容"""
        version = self.version_index.get(version_id)
        if not version:
            raise FileNotFoundError(f"版本不存在: {version_id}")

        storage_path = Path(version.storage_path)

        if storage_path.suffix == '.diff':
            # 需要重建完整内容
            return await self._reconstruct_from_diff(version_id)
        elif storage_path.suffix == '.gz':
            # 解压缩
            import gzip
            async with aiofiles.open(storage_path, 'rb') as f:
                compressed_content = await f.read()
            return gzip.decompress(compressed_content)
        else:
            # 直接读取
            async with aiofiles.open(storage_path, 'rb') as f:
                return await f.read()

    async def _reconstruct_from_diff(self, version_id: str) -> bytes:
        """从差异重建完整内容"""
        version = self.version_index[version_id]

        # 递归重建父版本
        if version.parent_version_id:
            parent_content = await self._reconstruct_from_diff(version.parent_version_id)
        else:
            parent_content = b""

        # 读取差异
        diff_path = Path(version.storage_path)
        async with aiofiles.open(diff_path, 'rb') as f:
            diff = await f.read()

        # 应用差异
        return self._apply_binary_diff(parent_content, diff)

    def _calculate_binary_diff(self, old_content: bytes, new_content: bytes) -> bytes:
        """计算二进制差异（简化实现）"""
        # 这里使用简单的差异存储，实际可以使用更高效的算法
        diff_data = {
            "old_size": len(old_content),
            "new_size": len(new_content),
            "changes": []
        }

        # 简单的块级差异检测
        block_size = 1024
        old_blocks = [old_content[i:i+block_size] for i in range(0, len(old_content), block_size)]
        new_blocks = [new_content[i:i+block_size] for i in range(0, len(new_content), block_size)]

        for i, (old_block, new_block) in enumerate(zip(old_blocks, new_blocks, strict=False)):
            if old_block != new_block:
                diff_data["changes"].append({
                    "block_index": i,
                    "old_block": old_block.hex(),
                    "new_block": new_block.hex()
                })

        return json.dumps(diff_data).encode()

    def _apply_binary_diff(self, base_content: bytes, diff: bytes) -> bytes:
        """应用二进制差异"""
        try:
            diff_data = json.loads(diff.decode())

            # 重建内容
            blocks = list(base_content)
            block_size = 1024

            for change in diff_data.get("changes", []):
                block_index = change["block_index"]
                new_block = bytes.fromhex(change["new_block"])

                # 替换块
                start = block_index * block_size
                end = start + len(new_block)
                blocks[start:end] = list(new_block)

            return bytes(blocks)
        except Exception as e:
            logger.error(f"应用差异失败: {e}")
            return base_content

    async def _save_version_metadata(self, version: FileVersion):
        """保存版本元数据"""
        metadata_file = self.metadata_path / f"{version.file_id}.json"

        # 读取现有元数据
        if metadata_file.exists():
            async with aiofiles.open(metadata_file, encoding='utf-8') as f:
                metadata = json.loads(await f.read())
        else:
            metadata = {"file_id": version.file_id, "versions": []}

        # 添加新版本
        version_data = asdict(version)
        version_data['created_at'] = version.created_at.isoformat()
        version_data['change_type'] = version.change_type.value
        metadata["versions"].append(version_data)

        # 保持版本数量限制
        if len(metadata["versions"]) > self.max_versions_per_file:
            metadata["versions"] = metadata["versions"][-self.max_versions_per_file:]

        # 保存元数据
        async with aiofiles.open(metadata_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(metadata, ensure_ascii=False, indent=2))

    def _update_indices(self, version: FileVersion) -> Any:
        """更新内存索引"""
        file_id = version.file_id
        version_id = version.version_id

        # 更新文件版本列表
        if file_id not in self.versions_db:
            self.versions_db[file_id] = []
        self.versions_db[file_id].append(version)

        # 更新版本索引
        self.version_index[version_id] = version

    async def get_file_versions(self, file_id: str, limit: int = None) -> list[FileVersion]:
        """获取文件的所有版本"""
        versions = self.versions_db.get(file_id, [])
        versions.sort(key=lambda v: v.version_number, reverse=True)

        if limit:
            versions = versions[:limit]

        return versions

    async def get_version(self, version_id: str) -> FileVersion | None:
        """获取特定版本信息"""
        return self.version_index.get(version_id)

    async def get_version_content(self, version_id: str) -> bytes:
        """获取版本内容"""
        return await self._load_version_content(version_id)

    async def get_latest_version(self, file_id: str) -> FileVersion | None:
        """获取文件的最新版本"""
        versions = await self.get_file_versions(file_id, 1)
        return versions[0] if versions else None

    async def compare_versions(self, version_id1: str, version_id2: str) -> VersionDiff:
        """比较两个版本"""
        version1 = await self.get_version(version_id1)
        version2 = await self.get_version(version_id2)

        if not version1 or not version2:
            raise ValueError("版本不存在")

        # 获取内容
        content1 = await self.get_version_content(version_id1)
        content2 = await self.get_version_content(version_id2)

        # 确定差异类型
        if version1.mime_type and version1.mime_type.startswith('text/'):
            diff_type = 'text'
            changes = self._compare_text_content(
                content1.decode('utf-8', errors='ignore'),
                content2.decode('utf-8', errors='ignore')
            )
        else:
            diff_type = 'binary'
            changes = self._compare_binary_content(content1, content2)

        # 生成摘要
        summary = self._generate_diff_summary(version1, version2, changes)

        return VersionDiff(
            old_version_id=version_id1,
            new_version_id=version_id2,
            diff_type=diff_type,
            changes=changes,
            summary=summary
        )

    def _compare_text_content(self, text1: str, text2: str) -> list[dict[str, Any]]:
        """比较文本内容"""
        lines1 = text1.splitlines(keepends=True)
        lines2 = text2.splitlines(keepends=True)

        diff = list(difflib.unified_diff(
            lines1, lines2,
            fromfile="版本1",
            tofile="版本2",
            lineterm=""
        ))

        return [
            {
                "type": "line_diff",
                "content": line,
                "line_number": idx
            }
            for idx, line in enumerate(diff)
        ]

    def _compare_binary_content(self, content1: bytes, content2: bytes) -> list[dict[str, Any]]:
        """比较二进制内容"""
        changes = []

        # 大小变化
        if len(content1) != len(content2):
            changes.append({
                "type": "size_change",
                "old_size": len(content1),
                "new_size": len(content2)
            })

        # 哈希值变化
        hash1 = hashlib.sha256(content1).hexdigest()
        hash2 = hashlib.sha256(content2).hexdigest()
        if hash1 != hash2:
            changes.append({
                "type": "content_change",
                "old_hash": hash1,
                "new_hash": hash2
            })

        # 简单的块级差异
        block_size = 1024
        different_blocks = []
        for i in range(max(len(content1), len(content2)) // block_size):
            block1 = content1[i*block_size:(i+1)*block_size]
            block2 = content2[i*block_size:(i+1)*block_size]
            if block1 != block2:
                different_blocks.append(i)

        if different_blocks:
            changes.append({
                "type": "block_diff",
                "different_blocks": different_blocks,
                "total_blocks": max(len(content1), len(content2)) // block_size
            })

        return changes

    def _generate_diff_summary(self, version1: FileVersion, version2: FileVersion,
                             changes: list[dict[str, Any]]) -> str:
        """生成差异摘要"""
        summary_parts = []

        # 基本信息
        summary_parts.append(f"版本 {version1.version_number} -> {version2.version_number}")

        # 文件大小变化
        size_change = version2.file_size - version1.file_size
        if size_change != 0:
            change_str = f"增加 {size_change} 字节" if size_change > 0 else f"减少 {abs(size_change)} 字节"
            summary_parts.append(f"文件大小{change_str}")

        # 内容变化
        content_changes = [c for c in changes if c['type'] in ['content_change', 'line_diff']]
        if content_changes:
            summary_parts.append("内容已修改")

        # 元数据变化
        if version1.metadata != version2.metadata:
            summary_parts.append("元数据已更新")

        return ", ".join(summary_parts)

    async def create_branch(self, file_id: str, branch_name: str,
                           from_version_id: str, user_id: str) -> FileVersion:
        """创建版本分支"""
        from_version = await self.get_version(from_version_id)
        if not from_version:
            raise ValueError("源版本不存在")

        # 创建分支版本
        branch_version = FileVersion(
            version_id=str(uuid.uuid4()),
            file_id=file_id,
            version_number=self._get_next_version_number(file_id),
            created_at=datetime.now(),
            created_by=user_id,
            change_type=ChangeType.COPY,
            file_name=from_version.file_name,
            file_path=from_version.file_path,
            file_size=from_version.file_size,
            file_hash=from_version.file_hash,
            mime_type=from_version.mime_type,
            metadata=from_version.metadata.copy(),
            parent_version_id=from_version_id,
            branch_name=branch_name,
            comment=f"创建分支: {branch_name}",
            storage_path=from_version.storage_path
        )

        # 保存分支版本
        await self._save_version_metadata(branch_version)
        self._update_indices(branch_version)

        logger.info(f"创建版本分支: {branch_name} from {from_version_id}")
        return branch_version

    async def revert_to_version(self, file_id: str, target_version_id: str,
                              user_id: str, comment: str = None) -> FileVersion:
        """回滚到指定版本"""
        target_version = await self.get_version(target_version_id)
        if not target_version:
            raise ValueError("目标版本不存在")

        # 获取目标版本内容
        target_content = await self.get_version_content(target_version_id)

        # 创建回滚版本
        revert_version = await self.create_version(
            file_id=file_id,
            file_content=target_content,
            file_name=target_version.file_name,
            user_id=user_id,
            change_type=ChangeType.UPDATE,
            parent_version_id=target_version_id,
            comment=comment or f"回滚到版本 {target_version.version_number}",
            metadata={"revert_from_version": target_version_id}
        )

        logger.info(f"文件 {file_id} 已回滚到版本 {target_version.version_number}")
        return revert_version

    async def delete_version(self, version_id: str, user_id: str) -> bool:
        """删除版本"""
        version = self.version_index.get(version_id)
        if not version:
            return False

        try:
            # 检查是否有子版本
            file_versions = self.versions_db.get(version.file_id, [])
            child_versions = [
                v for v in file_versions
                if v.parent_version_id == version_id
            ]

            if child_versions:
                raise ValueError("无法删除有子版本的版本")

            # 删除文件内容
            if version.storage_path:
                storage_path = Path(version.storage_path)
                if storage_path.exists():
                    storage_path.unlink()

            # 从内存索引中删除
            self.versions_db[version.file_id] = [
                v for v in self.versions_db[version.file_id]
                if v.version_id != version_id
            ]
            del self.version_index[version_id]

            # 更新元数据文件
            metadata_file = self.metadata_path / f"{version.file_id}.json"
            if metadata_file.exists():
                async with aiofiles.open(metadata_file, encoding='utf-8') as f:
                    metadata = json.loads(await f.read())

                metadata["versions"] = [
                    v for v in metadata["versions"]
                    if v["version_id"] != version_id
                ]

                async with aiofiles.open(metadata_file, 'w', encoding='utf-8') as f:
                    await f.write(json.dumps(metadata, ensure_ascii=False, indent=2))

            logger.info(f"删除版本: {version_id}")
            return True

        except Exception as e:
            logger.error(f"删除版本失败: {e}")
            return False

    async def cleanup_old_versions(self, days: int = None) -> int:
        """清理旧版本"""
        cutoff_time = datetime.now() - timedelta(days=days or self.max_storage_days)
        deleted_count = 0

        for _file_id, versions in self.versions_db.items():
            # 保留最新版本
            versions.sort(key=lambda v: v.version_number, reverse=True)
            versions[:1]  # 保留最新版本

            # 检查其他版本
            for version in versions[1:]:
                if version.created_at < cutoff_time and version.change_type != ChangeType.CREATE:
                    if await self.delete_version(version.version_id, "system"):
                        deleted_count += 1

        logger.info(f"清理了 {deleted_count} 个旧版本")
        return deleted_count

    async def get_file_history(self, file_id: str) -> dict[str, Any]:
        """获取文件历史信息"""
        versions = await self.get_file_versions(file_id)

        if not versions:
            return {"file_id": file_id, "history": []}

        # 统计信息
        total_versions = len(versions)
        total_size = sum(v.file_size for v in versions)
        creators = list({v.created_by for v in versions})

        # 构建历史树
        history_tree = self._build_history_tree(versions)

        return {
            "file_id": file_id,
            "total_versions": total_versions,
            "total_storage": total_size,
            "creators": creators,
            "first_version": versions[-1].created_at.isoformat(),
            "last_version": versions[0].created_at.isoformat(),
            "history_tree": history_tree,
            "branches": list({v.branch_name for v in versions if v.branch_name})
        }

    def _build_history_tree(self, versions: list[FileVersion]) -> list[dict[str, Any]]:
        """构建版本历史树"""
        version_map = {v.version_id: v for v in versions}
        tree = []

        # 找到根版本（没有父版本或父版本不在当前版本列表中）
        root_versions = [
            v for v in versions
            if not v.parent_version_id or v.parent_version_id not in version_map
        ]

        def build_node(version: FileVersion) -> dict[str, Any]:
            node = {
                "version_id": version.version_id,
                "version_number": version.version_number,
                "created_at": version.created_at.isoformat(),
                "created_by": version.created_by,
                "change_type": version.change_type.value,
                "file_name": version.file_name,
                "file_size": version.file_size,
                "comment": version.comment,
                "branch": version.branch_name,
                "children": []
            }

            # 添加子节点
            for v in versions:
                if v.parent_version_id == version.version_id:
                    node["children"].append(build_node(v))

            return node

        for root_version in root_versions:
            tree.append(build_node(root_version))

        return tree

    def get_statistics(self) -> dict[str, Any]:
        """获取版本管理统计信息"""
        total_files = len(self.versions_db)
        total_versions = len(self.version_index)
        total_storage = sum(
            v.file_size for v in self.version_index.values()
        )

        # 按变更类型统计
        change_type_counts = {}
        for version in self.version_index.values():
            change_type = version.change_type.value
            change_type_counts[change_type] = change_type_counts.get(change_type, 0) + 1

        # 按用户统计
        user_counts = {}
        for version in self.version_index.values():
            user = version.created_by
            user_counts[user] = user_counts.get(user, 0) + 1

        return {
            "total_files": total_files,
            "total_versions": total_versions,
            "total_storage_bytes": total_storage,
            "average_versions_per_file": total_versions / total_files if total_files > 0 else 0,
            "change_type_distribution": change_type_counts,
            "user_distribution": user_counts,
            "max_versions_per_file": self.max_versions_per_file,
            "compression_enabled": self.compression_enabled,
            "diff_storage_enabled": self.diff_storage_enabled
        }

# 全局文件版本管理器实例
file_version_manager = FileVersionManager()

# 使用示例
async def example_usage():
    """使用示例"""
    # 创建文件版本
    content1 = b"Hello, World!"
    version1 = await file_version_manager.create_version(
        file_id="test_file",
        file_content=content1,
        file_name="test.txt",
        user_id="user1",
        comment="初始版本"
    )

    # 更新文件
    content2 = b"Hello, World! Updated!"
    version2 = await file_version_manager.create_version(
        file_id="test_file",
        file_content=content2,
        file_name="test.txt",
        user_id="user1",
        parent_version_id=version1.version_id,
        comment="更新内容"
    )

    # 比较版本
    diff = await file_version_manager.compare_versions(
        version1.version_id, version2.version_id
    )
    print(f"版本差异: {diff.summary}")

    # 获取版本历史
    history = await file_version_manager.get_file_history("test_file")
    print(f"文件历史: {history}")

    # 回滚版本
    revert_version = await file_version_manager.revert_to_version(
        file_id="test_file",
        target_version_id=version1.version_id,
        user_id="user1",
        comment="回滚到初始版本"
    )
    print(f"回滚到版本: {revert_version.version_number}")

if __name__ == "__main__":
    asyncio.run(example_usage())
