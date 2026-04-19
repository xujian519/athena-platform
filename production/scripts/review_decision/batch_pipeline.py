#!/usr/bin/env python3
"""
复审决定书全量批处理管道
分批处理20945个复审决定书文件，生成向量并导入Qdrant

作者: Athena平台团队
创建时间: 2025-12-23
"""

from __future__ import annotations
import asyncio
import json
import logging
import re
import subprocess

# 添加项目路径
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from docx import Document

# 使用安全哈希函数替代不安全的MD5/SHA1
from production.utils.security_helpers import short_hash

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# 导入项目现有服务
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from core.nlp.bge_embedding_service import BGEEmbeddingService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.file_handler(f'/Users/xujian/Athena工作平台/logs/batch_pipeline_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.stream_handler()
    ]
)
logger = logging.getLogger(__name__)


class BatchDecisionPipeline:
    """复审决定书批处理管道"""

    def __init__(self):
        self.base_dir = Path("/Users/xujian/Athena工作平台")
        self.review_dir = Path("/Volumes/AthenaData/语料/专利/专利复审决定原文")
        self.invalid_dir = Path("/Volumes/AthenaData/语料/专利/专利无效宣告原文")
        self.output_dir = self.base_dir / "production/data/patent_decisions"
        self.checkpoint_dir = self.output_dir / "checkpoints"

        # 服务
        self.bge_service = None
        self.qdrant_client = None

        # 正则模式
        self.patterns = {
            'decision_number': re.compile(r'第(\d+)号'),
            'decision_date': re.compile(r'(\d{4})年(\d{1,2})月(\d{1,2})日'),
            'law_reference': re.compile(r'(专利法|实施细则)[\s\u3000]*第?([\d一二三四五六七八九十]+)[条条款款](?:第([\d一二三四五六七八九十]+)[款项])?'),
        }

        # 检查点
        self.checkpoint = self._load_checkpoint()

        logger.info("批处理管道初始化完成")
        logger.info(f"检查点: {self.checkpoint}")

    def _load_checkpoint(self) -> dict[str, Any]:
        """加载检查点"""
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        checkpoint_file = self.checkpoint_dir / "progress.json"

        if checkpoint_file.exists():
            with open(checkpoint_file) as f:
                return json.load(f)
        return {
            'processed_files': [],
            'total_chunks': 0,
            'total_vectors': 0,
            'qdrant_uploaded': 0
        }

    def _save_checkpoint(self) -> Any:
        """保存检查点"""
        checkpoint_file = self.checkpoint_dir / "progress.json"
        with open(checkpoint_file, 'w') as f:
            json.dump(self.checkpoint, f, indent=2)

    async def initialize_services(self):
        """初始化服务"""
        logger.info("=" * 60)
        logger.info("🚀 初始化服务")
        logger.info("=" * 60)

        # BGE服务
        try:
            model_path = self.base_dir / "models/converted/bge-large-zh-v1.5"
            if not model_path.exists():
                model_path = self.base_dir / "models/bge-large-zh-v1.5"

            config = {
                "model_path": str(model_path),
                "device": "cpu",
                "batch_size": 32,
                "max_length": 512,
                "normalize_embeddings": True,
                "cache_enabled": True,
                "preload": True
            }

            self.bge_service = BGEEmbeddingService(config)
            await self.bge_service.initialize()

            health = await self.bge_service.health_check()
            logger.info(f"✅ BGE服务: {health['status']}, 维度: {health['dimension']}")

        except Exception as e:
            logger.error(f"❌ BGE初始化失败: {e}")
            raise

        # Qdrant客户端
        try:
            self.qdrant_client = QdrantClient(url="http://localhost:6333")

            # 创建或获取集合
            collection_name = "patent_decisions"

            collections = self.qdrant_client.get_collections().collections
            collection_names = [c.name for c in collections]

            if collection_name not in collection_names:
                self.qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
                )
                logger.info(f"✅ 创建Qdrant集合: {collection_name}")
            else:
                info = self.qdrant_client.get_collection(collection_name)
                logger.info(f"✅ Qdrant集合已存在: {collection_name}, 点数: {info.points_count}")

        except Exception as e:
            logger.error(f"❌ Qdrant初始化失败: {e}")
            raise

        logger.info("=" * 60)

    def extract_from_docx(self, file_path: Path) -> tuple[str, dict[str, Any]]:
        """从DOCX提取文本和元数据"""
        try:
            doc = Document(str(file_path))
            paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
            full_text = "\n".join(paragraphs)

            metadata = {
                'filename': file_path.name,
                'doc_id': file_path.stem,
                'file_size': file_path.stat().st_size,
                'paragraph_count': len(paragraphs)
            }

            # 提取决定号和日期
            match = self.patterns['decision_number'].search(full_text)
            if match:
                metadata['decision_number'] = match.group(1)

            match = self.patterns['decision_date'].search(full_text)
            if match:
                metadata['decision_date'] = f"{match.group(1)}-{match.group(2).zfill(2)}-{match.group(3).zfill(2)}"

            return full_text, metadata

        except Exception as e:
            logger.error(f"DOCX提取失败 {file_path.name}: {e}")
            return "", {}

    def extract_from_doc(self, file_path: Path) -> tuple[str, dict[str, Any]]:
        """从旧版DOC文件提取文本和元数据（使用textutil）"""
        try:
            # macOS使用textutil转换DOC文件
            try:
                # 使用textutil转换为文本
                result = subprocess.run([
                    'textutil',
                    '-convert', 'txt',
                    '-stdout',
                    str(file_path)
                ], capture_output=True, text=True, timeout=30)

                full_text = result.stdout

            except subprocess.TimeoutExpired:
                logger.warning(f"DOC提取超时 {file_path.name}")
                return "", {}
            except subprocess.CalledProcessError:
                # 尝试使用catdoc作为备选方案
                try:
                    result = subprocess.run(['catdoc', '-w', str(file_path)],
                                          capture_output=True, text=True, timeout=30)
                    full_text = result.stdout
                except Exception:
                    logger.error(f"DOC提取失败 {file_path.name}: textutil和catdoc都不可用")
                    return "", {}

            if not full_text or not full_text.strip():
                return "", {}

            # 清理DOC格式的文本标记
            # 移除FORMTEXT、FORMCHECKBOX等标记
            full_text = re.sub(r'FORMTEXT\s*', '', full_text)
            full_text = re.sub(r'FORMCHECKBOX\s*', '', full_text)
            # 移除连续空行
            full_text = re.sub(r'\n\s*\n\s*\n', '\n\n', full_text)
            # 移除制表符和多余空格
            full_text = re.sub(r'\t+', ' ', full_text)
            full_text = re.sub(r' +', ' ', full_text)

            # 清理并分割段落
            paragraphs = [line.strip() for line in full_text.split('\n') if line.strip() and len(line.strip()) > 1]
            full_text = "\n".join(paragraphs)

            metadata = {
                'filename': file_path.name,
                'doc_id': file_path.stem,
                'file_size': file_path.stat().st_size,
                'paragraph_count': len(paragraphs),
                'file_format': 'doc'
            }

            # 提取决定号和日期
            match = self.patterns['decision_number'].search(full_text)
            if match:
                metadata['decision_number'] = match.group(1)

            match = self.patterns['decision_date'].search(full_text)
            if match:
                metadata['decision_date'] = f"{match.group(1)}-{match.group(2).zfill(2)}-{match.group(3).zfill(2)}"

            return full_text, metadata

        except Exception as e:
            logger.error(f"DOC提取失败 {file_path.name}: {e}")
            return "", {}

    def chunk_decision_text(self, text: str, metadata: dict[str, Any]) -> list[dict[str, Any]]:
        """将决定书分块"""
        if not text:
            return []

        doc_id = metadata.get('doc_id', 'unknown')
        lines = text.split('\n')

        chunks = []
        current_section = "未分类"
        current_content = []

        main_sections = {
            '决定要点': 'keypoints',
            '案由': 'background',
            '决定的理由': 'reasoning',
            '理由': 'reasoning',
            '决定': 'decision'
        }

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 检测章节
            matched = False
            for section_name, _block_type in main_sections.items():
                if section_name in line:
                    if current_content:
                        chunks.append(self._create_chunk(doc_id, current_section, current_content, metadata))
                    current_section = section_name
                    current_content = []
                    matched = True
                    break

            if matched:
                continue

            current_content.append(line)

        # 最后一块
        if current_content:
            chunks.append(self._create_chunk(doc_id, current_section, current_content, metadata))

        return chunks

    def _create_chunk(self, doc_id: str, section: str, content: list[str],
                     metadata: dict[str, Any]) -> dict[str, Any]:
        """创建数据块"""
        content_text = "\n".join(content)

        block_type_map = {
            '决定要点': 'keypoints',
            '案由': 'background',
            '决定的理由': 'reasoning',
            '理由': 'reasoning',
            '决定': 'decision'
        }
        block_type = block_type_map.get(section, 'other')

        chunk_hash = short_hash(f"{doc_id}_{section}_{len(content_text)}".encode())[:8]
        chunk_id = f"dec_{doc_id}_{chunk_hash}"

        # 提取法律引用
        law_refs = self.patterns['law_reference'].findall(content_text)
        law_refs_cleaned = [f"{law} {art}" + (f"第{itm}项" if itm else "") for law, art, itm in law_refs]

        return {
            'chunk_id': chunk_id,
            'doc_id': doc_id,
            'block_type': block_type,
            'section': section,
            'text': content_text,
            'metadata': {
                'filename': metadata.get('filename', ''),
                'decision_date': metadata.get('decision_date', ''),
                'decision_number': metadata.get('decision_number', ''),
                'char_count': len(content_text),
                'law_references': law_refs_cleaned,
                # 关联到现有知识库
                'related_laws': [ref for ref in law_refs_cleaned if '专利法' in ref or '实施细则' in ref]
            }
        }

    async def process_batch(self, file_paths: list[Path], batch_name: str,
                           batch_index: int, total_batches: int) -> dict[str, Any]:
        """处理一个批次"""
        logger.info("")
        logger.info("=" * 60)
        logger.info(f"📦 批次 {batch_index + 1}/{total_batches}: {batch_name}")
        logger.info(f"   文件数: {len(file_paths)}")
        logger.info("=" * 60)

        start_time = time.time()
        all_chunks = []
        failed_files = []

        # 过滤已处理的文件
        processed_set = set(self.checkpoint['processed_files'])
        files_to_process = [f for f in file_paths if str(f) not in processed_set]

        skipped = len(file_paths) - len(files_to_process)
        if skipped > 0:
            logger.info(f"⏭️  跳过已处理: {skipped} 个文件")

        # 提取文本和分块
        for i, file_path in enumerate(files_to_process):
            if (i + 1) % 100 == 0:
                logger.info(f"   进度: {i + 1}/{len(files_to_process)}")

            try:
                # 根据文件扩展名选择提取方法
                if file_path.suffix.lower() == '.docx':
                    text, metadata = self.extract_from_docx(file_path)
                elif file_path.suffix.lower() == '.doc':
                    text, metadata = self.extract_from_doc(file_path)
                else:
                    logger.warning(f"跳过未知格式: {file_path.suffix}")
                    continue

                if not text:
                    failed_files.append((file_path.name, "empty"))
                    continue

                chunks = self.chunk_decision_text(text, metadata)
                all_chunks.extend(chunks)

            except Exception as e:
                failed_files.append((file_path.name, str(e)))

        extract_time = time.time() - start_time
        logger.info(f"✅ 提取完成: {len(files_to_process)} 文件, {len(all_chunks)} 块 (耗时: {extract_time:.1f}秒)")

        if not all_chunks:
            return {'skipped': True, 'files_processed': 0}

        # 生成向量
        logger.info("🔄 生成向量...")
        vector_start = time.time()

        texts = [chunk['text'] for chunk in all_chunks]
        chunk_ids = [chunk['chunk_id'] for chunk in all_chunks]

        batch_size = 32
        vectors = []

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_ids = chunk_ids[i:i + batch_size]

            try:
                response = await self.bge_service.encode(batch_texts, task_type="patent_decision")

                for chunk_id, embedding in zip(batch_ids, response.embeddings, strict=False):
                    vectors.append({
                        'chunk_id': chunk_id,
                        'embedding': embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)
                    })

            except Exception as e:
                logger.warning(f"向量生成失败: {e}")

        vector_time = time.time() - vector_start
        logger.info(f"✅ 向量生成: {len(vectors)} 个 (耗时: {vector_time:.1f}秒)")

        # 上传到Qdrant
        logger.info("📤 上传到Qdrant...")
        upload_start = time.time()

        points = []
        for chunk, vec in zip(all_chunks, vectors, strict=False):
            hash_id = abs(hash(vec['chunk_id'])) % (10 ** 10)

            # 构建payload，包含关联信息
            payload = {
                'chunk_id': vec['chunk_id'],
                'doc_id': chunk['doc_id'],
                'block_type': chunk['block_type'],
                'section': chunk['section'],
                'text': chunk['text'][:500],
                'decision_date': chunk['metadata'].get('decision_date', ''),
                'decision_number': chunk['metadata'].get('decision_number', ''),
                'char_count': chunk['metadata'].get('char_count', 0),
                'law_references': chunk['metadata'].get('law_references', []),
                # 关联标记
                'source': 'patent_decision',
                'related_laws': chunk['metadata'].get('related_laws', [])
            }

            points.append(PointStruct(
                id=hash_id,
                vector=vec['embedding'],
                payload=payload
            ))

        # 批量上传
        upsert_batch_size = 100
        for i in range(0, len(points), upsert_batch_size):
            batch_points = points[i:i + upsert_batch_size]
            self.qdrant_client.upsert(
                collection_name="patent_decisions",
                points=batch_points
            )

        upload_time = time.time() - upload_start
        logger.info(f"✅ Qdrant上传: {len(points)} 点 (耗时: {upload_time:.1f}秒)")

        # 更新检查点
        for file_path in files_to_process:
            self.checkpoint['processed_files'].append(str(file_path))

        self.checkpoint['total_chunks'] += len(all_chunks)
        self.checkpoint['total_vectors'] += len(vectors)
        self.checkpoint['qdrant_uploaded'] += len(points)
        self._save_checkpoint()

        total_time = time.time() - start_time

        # 保存批次结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        batch_file = self.output_dir / "batches" / f"{batch_name}_{timestamp}.json"
        batch_file.parent.mkdir(parents=True, exist_ok=True)

        with open(batch_file, 'w', encoding='utf-8') as f:
            json.dump({
                'batch_name': batch_name,
                'batch_index': batch_index,
                'processed_at': datetime.now().isoformat(),
                'files_processed': len(files_to_process),
                'files_skipped': skipped,
                'chunks_created': len(all_chunks),
                'vectors_generated': len(vectors),
                'qdrant_uploaded': len(points),
                'failed_files': failed_files,
                'timing': {
                    'extraction': extract_time,
                    'vectorization': vector_time,
                    'upload': upload_time,
                    'total': total_time
                }
            }, f, ensure_ascii=False, indent=2)

        logger.info(f"📄 批次结果: {batch_file}")
        logger.info(f"⏱️  总耗时: {total_time:.1f}秒")

        return {
            'files_processed': len(files_to_process),
            'chunks_created': len(all_chunks),
            'vectors_generated': len(vectors),
            'qdrant_uploaded': len(points),
            'failed_files': failed_files,
            'timing': total_time
        }

    async def run_full_pipeline(self, batch_size: int = 1000, file_format: str = "all"):
        """运行完整管道

        Args:
            batch_size: 每批处理文件数
            file_format: 文件格式 ("docx", "doc", "all")
        """
        logger.info("=" * 60)
        logger.info("🚀 启动复审决定书全量处理管道")
        logger.info("=" * 60)

        # 初始化服务
        await self.initialize_services()

        # 获取所有文件
        review_docx_files = list(self.review_dir.glob("*.docx"))
        review_doc_files = list(self.review_dir.glob("*.doc"))
        invalid_docx_files = list(self.invalid_dir.glob("*.docx"))
        invalid_doc_files = list(self.invalid_dir.glob("*.doc"))

        # 根据格式选择文件
        if file_format == "docx":
            review_files = review_docx_files
            invalid_files = invalid_docx_files
        elif file_format == "doc":
            review_files = review_doc_files
            invalid_files = invalid_doc_files
        else:  # "all"
            review_files = review_docx_files + review_doc_files
            invalid_files = invalid_docx_files + invalid_doc_files

        logger.info("📊 文件统计:")
        logger.info(f"   专利复审决定 .docx: {len(review_docx_files)}")
        logger.info(f"   专利复审决定 .doc: {len(review_doc_files)}")
        logger.info(f"   专利无效宣告 .docx: {len(invalid_docx_files)}")
        logger.info(f"   专利无效宣告 .doc: {len(invalid_doc_files)}")
        logger.info(f"   本次处理: {len(review_files)} 复审 + {len(invalid_files)} 无效 = {len(review_files) + len(invalid_files)} 总计")

        # 分批处理
        all_files = review_files + invalid_files
        total_batches = (len(all_files) + batch_size - 1) // batch_size

        results = []

        for batch_idx in range(total_batches):
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, len(all_files))
            batch_files = all_files[start_idx:end_idx]

            batch_name = f"batch_{batch_idx + 1:04d}"

            try:
                result = await self.process_batch(
                    batch_files,
                    batch_name,
                    batch_idx,
                    total_batches
                )

                if not result.get('skipped'):
                    results.append(result)

            except Exception as e:
                logger.error(f"❌ 批次 {batch_idx + 1} 失败: {e}")
                continue

        # 生成最终报告
        self._generate_final_report(results)

    def _generate_final_report(self, results: list[dict[str, Any]]) -> Any:
        """生成最终报告"""
        logger.info("")
        logger.info("=" * 60)
        logger.info("📊 生成最终报告")
        logger.info("=" * 60)

        total_files = sum(r.get('files_processed', 0) for r in results)
        total_chunks = sum(r.get('chunks_created', 0) for r in results)
        total_vectors = sum(r.get('vectors_generated', 0) for r in results)
        total_uploaded = sum(r.get('qdrant_uploaded', 0) for r in results)
        total_time = sum(r.get('timing', 0) for r in results)

        report = {
            'completed_at': datetime.now().isoformat(),
            'summary': {
                'total_batches': len(results),
                'files_processed': total_files,
                'chunks_created': total_chunks,
                'vectors_generated': total_vectors,
                'qdrant_uploaded': total_uploaded,
                'total_time_seconds': total_time
            },
            'batches': results,
            'checkpoint': self.checkpoint
        }

        report_file = self.output_dir / f"final_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"📄 报告文件: {report_file}")
        logger.info("")
        logger.info("=" * 60)
        logger.info("🎉 全量处理完成！")
        logger.info(f"📊 处理文件: {total_files}")
        logger.info(f"📦 生成块: {total_chunks}")
        logger.info(f"🔢 生成向量: {total_vectors}")
        logger.info(f"📤 上传Qdrant: {total_uploaded}")
        logger.info(f"⏱️  总耗时: {total_time:.1f}秒 ({total_time/3600:.2f}小时)")
        logger.info("=" * 60)

        # 验证Qdrant集合
        try:
            info = self.qdrant_client.get_collection("patent_decisions")
            logger.info(f"✅ Qdrant集合状态: 点数={info.points_count}")
        except Exception as e:
            logger.warning(f"验证失败: {e}")


async def main():
    """主函数"""
    import sys

    pipeline = BatchDecisionPipeline()

    # 使用较小的批次大小以便更好地控制
    batch_size = 500

    # 支持命令行参数指定文件格式
    file_format = "all"  # 默认处理所有格式
    if len(sys.argv) > 1:
        file_format = sys.argv[1]
        if file_format not in ["docx", "doc", "all"]:
            print(f"❌ 未知格式: {file_format}")
            print("用法: python batch_pipeline.py [docx|doc|all]")
            sys.exit(1)

    logger.info(f"📁 处理文件格式: {file_format}")
    await pipeline.run_full_pipeline(batch_size=batch_size, file_format=file_format)


if __name__ == "__main__":
    asyncio.run(main())
