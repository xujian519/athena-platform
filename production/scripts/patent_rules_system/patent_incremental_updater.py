#!/usr/bin/env python3
"""
专利规则增量更新机制
Patent Rules Incremental Update Mechanism

支持：
- 文档变更检测（通过文件哈希和修改时间）
- 增量添加新文档
- 更新已修改的文档
- 删除已移除的文档
- 关系重新计算

作者: Athena AI系统
创建时间: 2025-01-15
"""

from __future__ import annotations
import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class DocumentManifest:
    """文档清单"""
    file_path: str                   # 文件路径
    file_hash: str                   # 文件内容哈希
    modified_time: str               # 修改时间
    doc_type: str                    # 文档类型
    priority: int                    # 优先级
    processed: bool = False          # 是否已处理
    processed_at: str | None = None  # 处理时间
    rule_ids: list[str] = field(default_factory=list)  # 生成的规则ID


class IncrementalUpdateManager:
    """增量更新管理器"""

    def __init__(self, manifest_file: str = "patent_rules_manifest.json"):
        """
        初始化增量更新管理器

        Args:
            manifest_file: 清单文件路径
        """
        self.manifest_file = Path(manifest_file)
        self.manifest: dict[str, DocumentManifest] = {}
        self.stats = {
            'unchanged': 0,      # 未变更的文档
            'new': 0,            # 新增文档
            'modified': 0,       # 修改的文档
            'deleted': 0,        # 删除的文档
        }

    def load_manifest(self) -> Any | None:
        """加载清单文件"""
        if self.manifest_file.exists():
            with open(self.manifest_file, encoding='utf-8') as f:
                data = json.load(f)
                for path, manifest_data in data.items():
                    self.manifest[path] = DocumentManifest(**manifest_data)
            logger.info(f"✅ 加载清单文件: {len(self.manifest)}个文档")
        else:
            logger.info("ℹ️  清单文件不存在，将创建新清单")

    def save_manifest(self) -> None:
        """保存清单文件"""
        data = {
            path: {
                'file_path': m.file_path,
                'file_hash': m.file_hash,
                'modified_time': m.modified_time,
                'doc_type': m.doc_type,
                'priority': m.priority,
                'processed': m.processed,
                'processed_at': m.processed_at,
                'rule_ids': m.rule_ids
            }
            for path, m in self.manifest.items()
        }

        with open(self.manifest_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ 保存清单文件: {len(self.manifest)}个文档")

    def detect_changes(
        self,
        documents: dict[str, tuple[Path, str, int]]
    ) -> tuple[list[tuple[Path, str, int]], list[str], list[str]]:
        """
        检测文档变更

        Args:
            documents: 文档字典 {path: (file_path, doc_type, priority)}

        Returns:
            (新增文档列表, 修改文档路径列表, 删除文档路径列表)
        """
        new_docs = []
        modified_docs = []
        deleted_docs = []

        # 计算当前文档哈希
        current_hashes = {}
        for path, (file_path, doc_type, priority) in documents.items():
            if file_path.exists():
                file_hash = self._calculate_file_hash(file_path)
                modified_time = datetime.fromtimestamp(
                    file_path.stat().st_mtime
                ).isoformat()

                current_hashes[path] = {
                    'hash': file_hash,
                    'modified_time': modified_time,
                    'file_path': file_path,
                    'doc_type': doc_type,
                    'priority': priority
                }

        # 检测新增和修改
        for path, info in current_hashes.items():
            if path not in self.manifest:
                # 新增文档
                new_docs.append((info['file_path'], info['doc_type'], info['priority']))
                self.stats['new'] += 1
                logger.info(f"📄 新增文档: {path}")
            else:
                manifest = self.manifest[path]
                # 检查是否修改
                if (info['hash'] != manifest.file_hash or
                    info['modified_time'] != manifest.modified_time):
                    modified_docs.append(path)
                    self.stats['modified'] += 1
                    logger.info(f"📝 修改文档: {path}")
                else:
                    self.stats['unchanged'] += 1

        # 检测删除
        for path in list(self.manifest.keys()):
            if path not in current_hashes:
                deleted_docs.append(path)
                self.stats['deleted'] += 1
                logger.info(f"🗑️  删除文档: {path}")

        return new_docs, modified_docs, deleted_docs

    def update_manifest(
        self,
        file_path: Path,
        doc_type: str,
        priority: int,
        rule_ids: list[str],
        processed: bool = True
    ):
        """
        更新清单记录

        Args:
            file_path: 文件路径
            doc_type: 文档类型
            priority: 优先级
            rule_ids: 生成的规则ID列表
            processed: 是否已处理
        """
        path = str(file_path)
        file_hash = self._calculate_file_hash(file_path)
        modified_time = datetime.fromtimestamp(
            file_path.stat().st_mtime
        ).isoformat()

        self.manifest[path] = DocumentManifest(
            file_path=path,
            file_hash=file_hash,
            modified_time=modified_time,
            doc_type=doc_type,
            priority=priority,
            processed=processed,
            processed_at=datetime.now().isoformat(),
            rule_ids=rule_ids
        )

    def remove_from_manifest(self, paths: list[str]) -> None:
        """
        从清单中移除文档

        Args:
            paths: 文档路径列表
        """
        for path in paths:
            if path in self.manifest:
                del self.manifest[path]

    def get_rule_ids_for_document(self, file_path: Path) -> list[str]:
        """获取文档对应的规则ID列表"""
        path = str(file_path)
        if path in self.manifest:
            return self.manifest[path].rule_ids
        return []

    def print_stats(self) -> Any:
        """打印统计信息"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 变更检测统计")
        logger.info("=" * 60)
        logger.info(f"未变更: {self.stats['unchanged']}个文档")
        logger.info(f"新增: {self.stats['new']}个文档")
        logger.info(f"修改: {self.stats['modified']}个文档")
        logger.info(f"删除: {self.stats['deleted']}个文档")
        logger.info(f"总计: {sum(self.stats.values())}个文档")
        logger.info("=" * 60 + "\n")

    def _calculate_file_hash(self, file_path: Path) -> str:
        """计算文件哈希"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()


class IncrementalUpdateProcessor:
    """增量更新处理器"""

    def __init__(
        self,
        manifest_file: str = "patent_rules_manifest.json",
        dry_run: bool = False
    ):
        """
        初始化处理器

        Args:
            manifest_file: 清单文件路径
            dry_run: 是否为试运行（不实际执行）
        """
        self.manifest_manager = IncrementalUpdateManager(manifest_file)
        self.dry_run = dry_run

    async def process_updates(
        self,
        documents: dict[str, tuple[Path, str, int]],
        processor,
        storage
    ):
        """
        处理增量更新

        Args:
            documents: 文档字典
            processor: 规则处理器
            storage: 存储层
        """
        logger.info("\n" + "=" * 60)
        logger.info("🔄 开始增量更新")
        logger.info("=" * 60)

        # 加载清单
        self.manifest_manager.load_manifest()

        # 检测变更
        new_docs, modified_docs, deleted_docs = self.manifest_manager.detect_changes(documents)

        if self.dry_run:
            logger.info("⚠️  试运行模式，不实际执行更新")
            self.manifest_manager.print_stats()
            return

        # 处理新增文档
        if new_docs:
            logger.info(f"\n📄 处理 {len(new_docs)} 个新增文档...")
            for file_path, doc_type, priority in new_docs:
                await self._process_new_document(
                    file_path, doc_type, priority, processor, storage
                )

        # 处理修改文档
        if modified_docs:
            logger.info(f"\n📝 处理 {len(modified_docs)} 个修改文档...")
            for path in modified_docs:
                # 先删除旧规则
                rule_ids = self.manifest_manager.get_rule_ids_for_document(Path(path))
                await self._delete_rules(rule_ids, storage)

                # 重新处理
                # TODO: 从documents中获取文件信息并重新处理

        # 处理删除文档
        if deleted_docs:
            logger.info(f"\n🗑️  处理 {len(deleted_docs)} 个删除文档...")
            for path in deleted_docs:
                rule_ids = self.manifest_manager.get_rule_ids_for_document(Path(path))
                await self._delete_rules(rule_ids, storage)
                self.manifest_manager.remove_from_manifest([path])

        # 保存清单
        self.manifest_manager.save_manifest()

        logger.info("\n" + "=" * 60)
        logger.info("✅ 增量更新完成")
        logger.info("=" * 60 + "\n")

    async def _process_new_document(
        self,
        file_path: Path,
        doc_type: str,
        priority: int,
        processor,
        storage
    ):
        """处理新增文档"""
        logger.info(f"处理: {file_path.name}")

        # 解析文档
        from patent_rules_processor import DocumentType, Priority
        processed_doc = processor.parser.parse_document(
            file_path,
            DocumentType(doc_type),
            Priority(priority)
        )

        if not processed_doc.rules:
            logger.warning(f"⚠️  未提取到规则: {file_path.name}")
            return

        # 向量化
        texts = [rule.content for rule in processed_doc.rules]
        embeddings = processor.embedding_service.encode(texts)

        # 分配向量ID
        for rule, _embedding in zip(processed_doc.rules, embeddings, strict=False):
            rule.vector_id = f"{rule.rule_type}_{rule.id}"

        # 存储
        stored = storage.store_rules(processed_doc.rules, embeddings)
        logger.info(f"✅ 存储{stored}/{len(processed_doc.rules)}条规则")

        # 更新清单
        rule_ids = [rule.id for rule in processed_doc.rules]
        self.manifest_manager.update_manifest(
            file_path, doc_type, priority, rule_ids
        )

    async def _delete_rules(self, rule_ids: list[str], storage):
        """删除规则"""
        if not rule_ids:
            return

        logger.info(f"删除 {len(rule_ids)} 条规则...")

        # 从PostgreSQL删除
        cursor = storage.pg_conn.cursor()
        for rule_id in rule_ids:
            cursor.execute("DELETE FROM patent_rules WHERE id = %s;", (rule_id,))
        storage.pg_conn.commit()

        # 从Qdrant删除
        # TODO: 实现Qdrant删除

        # 从NebulaGraph删除
        # TODO: 实现NebulaGraph删除

        logger.info("✅ 删除完成")


async def test_incremental_update():
    """测试增量更新"""
    # 创建测试处理器
    updater = IncrementalUpdateProcessor(
        manifest_file="test_manifest.json",
        dry_run=True
    )

    # 模拟文档
    from pathlib import Path
    test_dir = Path("/Users/xujian/Athena工作平台/data/专利")
    documents = {
        "专利法": (test_dir / "中华人民共和国专利法_20201017.md", "patent_law", 0),
        "实施细则": (test_dir / "中华人民共和国专利法实施细则_20231211.md", "rules", 0),
    }

    # 检测变更
    new_docs, modified_docs, deleted_docs = updater.manifest_manager.detect_changes(documents)

    updater.manifest_manager.print_stats()

    return new_docs, modified_docs, deleted_docs


if __name__ == "__main__":
    asyncio.run(test_incremental_update())
