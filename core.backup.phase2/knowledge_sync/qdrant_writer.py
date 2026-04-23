#!/usr/bin/env python3
from __future__ import annotations
"""
Qdrant 批量写入器
Qdrant Writer for Bao Chen Knowledge Base

将分块数据批量 upsert 到 Qdrant 的 baochen_wiki collection。
"""

import logging
import uuid
from typing import Any

import requests

from .chunk_processor import BaoChenChunk, ChunkProcessor

logger = logging.getLogger(__name__)

COLLECTION_NAME = "baochen_wiki"
VECTOR_SIZE = 1024
BATCH_SIZE = 64  # 每批写入的 point 数量


class QdrantWriter:
    """Qdrant 批量写入器"""

    def __init__(self, qdrant_url: str = "http://localhost:6333"):
        self.qdrant_url = qdrant_url.rstrip("/")
        self.session = requests.Session()
        self.chunk_processor = ChunkProcessor()
        self._ensure_collection()

    def _ensure_collection(self) -> bool:
        """确保 baochen_wiki collection 存在"""
        try:
            url = f"{self.qdrant_url}/collections/{COLLECTION_NAME}"
            resp = self.session.get(url, timeout=5)

            if resp.status_code == 200:
                logger.info(f"集合 {COLLECTION_NAME} 已存在")
                return True

            # 创建新集合
            create_url = f"{self.qdrant_url}/collections/{COLLECTION_NAME}"
            config = {
                "vectors": {"size": VECTOR_SIZE, "distance": "Cosine"},
                "optimizers_config": {
                    "default_segment_number": 2,
                    "indexing_threshold": 20000,
                    "flush_interval_sec": 5,
                },
                "hnsw_config": {"m": 16, "ef_construct": 100},
            }

            resp = self.session.put(create_url, json=config, timeout=30)
            if resp.status_code == 200:
                logger.info(f"✅ 创建集合 {COLLECTION_NAME} 成功")
                return True
            else:
                logger.error(f"❌ 创建集合失败: {resp.text}")
                return False

        except Exception as e:
            logger.error(f"❌ 检查/创建集合异常: {e}")
            return False

    def upsert_chunks(
        self,
        chunks: list[BaoChenChunk],
        embeddings: list[list[float]],
        sync_version: int = 1,
    ) -> int:
        """
        批量写入 chunks 和对应的 embeddings

        Args:
            chunks: 分块列表
            embeddings: 对应的嵌入向量列表
            sync_version: 同步版本号

        Returns:
            成功写入的 point 数量
        """
        if len(chunks) != len(embeddings):
            logger.error(f"chunks({len(chunks)}) 与 embeddings({len(embeddings)}) 数量不匹配")
            return 0

        success_count = 0
        total = len(chunks)

        for i in range(0, total, BATCH_SIZE):
            batch_chunks = chunks[i : i + BATCH_SIZE]
            batch_embeddings = embeddings[i : i + BATCH_SIZE]

            points = []
            for chunk, embedding in zip(batch_chunks, batch_embeddings):
                point_id = str(
                    uuid.uuid5(
                        uuid.NAMESPACE_URL,
                        f"{chunk.source_file}#{chunk.chunk_index}",
                    )
                )
                payload = self.chunk_processor.chunk_to_payload(chunk, sync_version)
                points.append({"id": point_id, "vector": embedding, "payload": payload})

            if self._batch_upsert(points):
                success_count += len(points)
                logger.info(f"写入批次 {i // BATCH_SIZE + 1}: {len(points)} 个 point ({success_count}/{total})")
            else:
                logger.warning(f"批次 {i // BATCH_SIZE + 1} 写入失败")

        return success_count

    def delete_by_source_file(self, source_file: str) -> bool:
        """删除指定源文件的所有 chunks"""
        try:
            url = f"{self.qdrant_url}/collections/{COLLECTION_NAME}/points/delete"
            payload = {
                "filter": {
                    "must": [{"key": "source_file", "match": {"value": source_file}}]
                }
            }
            resp = self.session.post(url, json=payload, timeout=30)
            if resp.status_code == 200:
                logger.info(f"删除 {source_file} 的所有 chunks")
                return True
            else:
                logger.warning(f"删除失败: {resp.text}")
                return False
        except Exception as e:
            logger.error(f"删除异常: {e}")
            return False

    def delete_all(self) -> bool:
        """清空 collection 中的所有数据"""
        try:
            url = f"{self.qdrant_url}/collections/{COLLECTION_NAME}/points/delete"
            payload = {"filter": {"must": []}}  # 空过滤器 = 匹配所有
            resp = self.session.post(url, json=payload, timeout=30)
            if resp.status_code == 200:
                logger.info(f"清空集合 {COLLECTION_NAME}")
                return True
            return False
        except Exception as e:
            logger.error(f"清空异常: {e}")
            return False

    def get_point_count(self) -> int:
        """获取 collection 中的 point 数量"""
        try:
            url = f"{self.qdrant_url}/collections/{COLLECTION_NAME}"
            resp = self.session.get(url, timeout=10)
            if resp.status_code == 200:
                info = resp.json().get("result", {})
                return info.get("points_count", 0)
            return 0
        except Exception:
            return 0

    def get_category_stats(self) -> dict[str, int]:
        """获取各分类的 chunk 数量统计"""
        try:
            # 使用 Qdrant 的 scroll API 获取所有 payload 进行统计
            # 注意：对于大数据集应使用聚合接口，这里简化处理
            url = f"{self.qdrant_url}/collections/{COLLECTION_NAME}/points/scroll"
            stats: dict[str, int] = {}
            offset = None

            while True:
                payload: dict[str, Any] = {"limit": 100, "with_payload": ["kb_category"]}
                if offset is not None:
                    payload["offset"] = offset

                resp = self.session.post(url, json=payload, timeout=30)
                if resp.status_code != 200:
                    break

                data = resp.json().get("result", {})
                points = data.get("points", [])

                for point in points:
                    cat = point.get("payload", {}).get("kb_category", "未知")
                    stats[cat] = stats.get(cat, 0) + 1

                next_offset = data.get("next_page_offset")
                if not next_offset or not points:
                    break
                offset = next_offset

            return stats

        except Exception as e:
            logger.error(f"获取统计失败: {e}")
            return {}

    def _batch_upsert(self, points: list[dict[str, Any]]) -> bool:
        """执行批量 upsert"""
        try:
            url = f"{self.qdrant_url}/collections/{COLLECTION_NAME}/points"
            payload = {"points": points}
            resp = self.session.put(url, json=payload, timeout=60)

            if resp.status_code == 200:
                return True
            else:
                logger.error(f"批量写入失败: {resp.text}")
                return False
        except Exception as e:
            logger.error(f"批量写入异常: {e}")
            return False
