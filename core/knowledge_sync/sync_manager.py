#!/usr/bin/env python3
from __future__ import annotations
"""
同步编排器
Sync Manager for Bao Chen Knowledge Base

编排全量/增量同步流程：扫描文件 → 分块 → 嵌入 → 写入 Qdrant。
"""

import asyncio
import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any

from .chunk_processor import BaoChenChunk, ChunkProcessor
from .qdrant_writer import QdrantWriter

logger = logging.getLogger(__name__)

# 默认配置
DEFAULT_WIKI_PATH = "/Users/xujian/projects/宝宸知识库/Wiki"
DEFAULT_QDRANT_URL = "http://localhost:6333"
STATE_FILE = Path(__file__).parent.parent.parent / "data" / "baochen_sync_state.json"
EMBED_BATCH_SIZE = 32  # 嵌入批次大小


class BaoChenSyncManager:
    """宝宸知识库同步管理器"""

    def __init__(
        self,
        wiki_path: str = DEFAULT_WIKI_PATH,
        qdrant_url: str = DEFAULT_QDRANT_URL,
    ):
        self.wiki_path = Path(wiki_path)
        self.processor = ChunkProcessor()
        self.writer = QdrantWriter(qdrant_url=qdrant_url)
        self.qdrant_url = qdrant_url
        self._embedding_service = None

    async def full_rebuild(self) -> dict[str, Any]:
        """
        全量重建：处理所有 Wiki 文件并写入 Qdrant

        Returns:
            同步结果统计
        """
        start_time = time.time()
        logger.info(f"开始全量重建，Wiki 路径: {self.wiki_path}")

        if not self.wiki_path.is_dir():
            raise FileNotFoundError(f"Wiki 目录不存在: {self.wiki_path}")

        # 1. 收集文件
        files = self.processor.collect_files(self.wiki_path)
        logger.info(f"扫描到 {len(files)} 个 .md 文件")

        # 2. 分块
        all_chunks: list[BaoChenChunk] = []
        for md_file, _kb_name in files:
            chunks = self.processor.process_file(md_file, self.wiki_path)
            all_chunks.extend(chunks)

        logger.info(f"共生成 {len(all_chunks)} 个分块")

        # 统计各分类
        kb_counts: dict[str, int] = {}
        for chunk in all_chunks:
            kb_counts[chunk.kb_category] = kb_counts.get(chunk.kb_category, 0) + 1
        for kb, count in sorted(kb_counts.items(), key=lambda x: -x[1]):
            logger.info(f"  {kb}: {count} 块")

        # 3. 清空现有数据
        self.writer.delete_all()
        logger.info("已清空现有数据")

        # 4. 生成嵌入并批量写入
        total_written = await self._embed_and_write(all_chunks, sync_version=1)

        # 5. 保存同步状态
        elapsed = time.time() - start_time
        state = {
            "last_sync": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "sync_type": "full_rebuild",
            "total_files": len(files),
            "total_chunks": len(all_chunks),
            "total_written": total_written,
            "elapsed_seconds": round(elapsed, 1),
            "kb_counts": kb_counts,
            "files": self._build_file_state(files, all_chunks),
        }
        self._save_state(state)

        logger.info(f"全量重建完成: {total_written}/{len(all_chunks)} chunks, 耗时 {elapsed:.1f}s")
        return state

    async def incremental_sync(self) -> dict[str, Any]:
        """
        增量同步：仅处理变更的文件

        Returns:
            同步结果统计
        """
        start_time = time.time()
        logger.info("开始增量同步...")

        # 加载上次状态
        old_state = self._load_state()
        if not old_state or "files" not in old_state:
            logger.info("无历史状态，执行全量重建")
            return await self.full_rebuild()

        # 收集当前文件
        files = self.processor.collect_files(self.wiki_path)
        current_file_map = {str(f.relative_to(self.wiki_path)): f for f, _ in files}

        # 检测变更
        old_file_map = old_state.get("files", {})
        added, modified, deleted = self._detect_changes(current_file_map, old_file_map)

        if not added and not modified and not deleted:
            logger.info("无变更，跳过同步")
            return {"sync_type": "no_changes", "total_files": len(files)}

        logger.info(f"变更检测: +{len(added)} 新增, ~{len(modified)} 修改, -{len(deleted)} 删除")

        # 处理删除
        for rel_path in deleted:
            self.writer.delete_by_source_file(rel_path)

        # 处理新增和修改
        changed_files = added | modified
        all_chunks: list[BaoChenChunk] = []
        for rel_path in changed_files:
            file_path = current_file_map[rel_path]
            chunks = self.processor.process_file(file_path, self.wiki_path)
            all_chunks.extend(chunks)

        # 删除修改文件的旧 chunks（新增文件无需删除）
        for rel_path in modified:
            self.writer.delete_by_source_file(rel_path)

        # 嵌入并写入
        sync_version = old_state.get("sync_version", 0) + 1
        total_written = await self._embed_and_write(all_chunks, sync_version)

        # 更新状态
        elapsed = time.time() - start_time
        new_state = {
            "last_sync": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "sync_type": "incremental",
            "total_files": len(files),
            "added": len(added),
            "modified": len(modified),
            "deleted": len(deleted),
            "total_written": total_written,
            "elapsed_seconds": round(elapsed, 1),
            "files": self._update_file_state(old_file_map, current_file_map, added, modified, deleted, all_chunks),
        }
        self._save_state(new_state)

        logger.info(f"增量同步完成: {total_written} chunks, 耗时 {elapsed:.1f}s")
        return new_state

    def status(self) -> dict[str, Any]:
        """获取当前同步状态"""
        state = self._load_state()
        point_count = self.writer.get_point_count()
        category_stats = self.writer.get_category_stats()

        return {
            "state_file": str(STATE_FILE),
            "last_sync": state.get("last_sync", "从未同步"),
            "total_files": state.get("total_files", 0),
            "total_chunks": state.get("total_chunks", 0),
            "qdrant_points": point_count,
            "category_distribution": category_stats,
            "wiki_path": str(self.wiki_path),
            "wiki_exists": self.wiki_path.is_dir(),
        }

    async def _embed_and_write(
        self, chunks: list[BaoChenChunk], sync_version: int
    ) -> int:
        """分批嵌入并写入 Qdrant"""
        if not chunks:
            return 0

        # 初始化嵌入服务
        service = await self._get_embedding_service()

        total_written = 0
        for i in range(0, len(chunks), EMBED_BATCH_SIZE):
            batch = chunks[i : i + EMBED_BATCH_SIZE]
            texts = [c.text for c in batch]

            try:
                result = await service.encode(texts, self._module_type.LEGAL_ANALYSIS)
                embeddings = result["embeddings"]

                # 统一为 list[list[float]] 格式
                if embeddings and not isinstance(embeddings[0], list):
                    embeddings = [embeddings]

                written = self.writer.upsert_chunks(batch, embeddings, sync_version)
                total_written += written

            except Exception as e:
                logger.error(f"嵌入批次 {i // EMBED_BATCH_SIZE + 1} 失败: {e}")
                # 跳过失败批次，继续处理
                continue

            # 进度报告
            progress = min(i + EMBED_BATCH_SIZE, len(chunks))
            logger.info(f"进度: {progress}/{len(chunks)} ({progress * 100 // len(chunks)}%)")

        return total_written

    async def _get_embedding_service(self):
        """获取统一嵌入服务"""
        if self._embedding_service is None:
            from core.embedding.unified_embedding_service import (
                ModuleType,
                UnifiedEmbeddingService,
            )

            self._embedding_service = UnifiedEmbeddingService()
            await self._embedding_service.initialize()
            # 保存 ModuleType 引用以便后续使用
            self._module_type = ModuleType
            logger.info("嵌入服务初始化完成")
        return self._embedding_service

    def _detect_changes(
        self,
        current_files: dict[str, Path],
        old_files: dict[str, Any],
    ) -> tuple[set[str], set[str], set[str]]:
        """检测文件变更：返回 (新增, 修改, 删除) 集合"""
        current_set = set(current_files.keys())
        old_set = set(old_files.keys())

        added = current_set - old_set
        deleted = old_set - current_set
        potentially_modified = current_set & old_set

        modified: set[str] = set()
        for rel_path in potentially_modified:
            file_path = current_files[rel_path]
            current_hash = self._file_hash(file_path)
            old_hash = old_files[rel_path].get("content_hash", "")
            if current_hash != old_hash:
                modified.add(rel_path)

        return added, modified, deleted

    def _file_hash(self, file_path: Path) -> str:
        """计算文件的 SHA-256 哈希"""
        content = file_path.read_bytes()
        return hashlib.sha256(content).hexdigest()

    def _build_file_state(
        self,
        files: list[tuple[Path, str]],
        chunks: list[BaoChenChunk],
    ) -> dict[str, Any]:
        """构建全量文件状态"""
        state: dict[str, Any] = {}
        chunk_map: dict[str, int] = {}
        for chunk in chunks:
            chunk_map[chunk.source_file] = chunk_map.get(chunk.source_file, 0) + 1

        for md_file, _kb_name in files:
            rel_path = str(md_file.relative_to(self.wiki_path))
            state[rel_path] = {
                "content_hash": self._file_hash(md_file),
                "chunk_count": chunk_map.get(rel_path, 0),
                "byte_size": md_file.stat().st_size,
            }

        return state

    def _update_file_state(
        self,
        old_files: dict[str, Any],
        current_files: dict[str, Path],
        added: set[str],
        modified: set[str],
        deleted: set[str],
        new_chunks: list[BaoChenChunk],
    ) -> dict[str, Any]:
        """更新增量文件状态"""
        state = dict(old_files)

        # 移除已删除的文件
        for rel_path in deleted:
            state.pop(rel_path, None)

        # 统计变更文件的 chunk 数量
        chunk_map: dict[str, int] = {}
        for chunk in new_chunks:
            chunk_map[chunk.source_file] = chunk_map.get(chunk.source_file, 0) + 1

        # 更新新增和修改的文件
        for rel_path in added | modified:
            file_path = current_files[rel_path]
            state[rel_path] = {
                "content_hash": self._file_hash(file_path),
                "chunk_count": chunk_map.get(rel_path, 0),
                "byte_size": file_path.stat().st_size,
            }

        return state

    def _save_state(self, state: dict[str, Any]) -> None:
        """保存同步状态到 JSON 文件"""
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        logger.info(f"同步状态已保存: {STATE_FILE}")

    def _load_state(self) -> dict[str, Any]:
        """加载同步状态"""
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载状态文件失败: {e}")
        return {}

    async def validate(self) -> dict[str, Any]:
        """
        验证同步状态和数据一致性

        Returns:
            验证结果报告
        """
        logger.info("开始数据验证...")

        state = self._load_state()
        if not state:
            return {"status": "error", "message": "无同步状态，请先执行全量重建"}

        report: dict[str, Any] = {
            "status": "healthy",
            "issues": [],
        }

        # 1. 检查 Wiki 目录可用性
        if not self.wiki_path.is_dir():
            report["status"] = "error"
            report["issues"].append(f"Wiki 目录不可用: {self.wiki_path}")
            return report

        # 2. 检查 Qdrant point 数量
        point_count = self.writer.get_point_count()
        expected_chunks = state.get("total_chunks", 0)
        report["qdrant_points"] = point_count
        report["expected_chunks"] = expected_chunks

        if point_count == 0 and expected_chunks > 0:
            report["status"] = "error"
            report["issues"].append(f"Qdrant 无数据但状态记录有 {expected_chunks} 个 chunks")
        elif abs(point_count - expected_chunks) > expected_chunks * 0.1:
            report["status"] = "warning"
            report["issues"].append(
                f"Qdrant 点数({point_count})与预期({expected_chunks})差异超过 10%"
            )

        # 3. 检查分类分布
        category_stats = self.writer.get_category_stats()
        report["category_distribution"] = category_stats
        expected_categories = {"法律法规", "审查指南", "专利实务", "复审无效", "专利侵权", "专利判决"}
        missing = expected_categories - set(category_stats.keys())
        if missing:
            report["status"] = "warning"
            report["issues"].append(f"缺少分类: {missing}")

        # 4. 抽样验证 — 检查几个文件是否在 Qdrant 中存在对应数据
        files = self.processor.collect_files(self.wiki_path)
        report["wiki_file_count"] = len(files)
        state_file_count = state.get("total_files", 0)

        if len(files) != state_file_count:
            report["status"] = "warning"
            report["issues"].append(
                f"文件数量不匹配: 当前 {len(files)} 个, 状态记录 {state_file_count} 个"
            )

        # 5. 总结
        if not report["issues"]:
            report["message"] = f"数据一致性验证通过: {point_count} points, {len(files)} 文件"
        else:
            report["message"] = f"发现 {len(report['issues'])} 个问题"

        logger.info(f"验证完成: {report['status']} - {report['message']}")
        return report
