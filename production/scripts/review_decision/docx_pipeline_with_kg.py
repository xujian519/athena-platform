#!/usr/bin/env python3
"""
DOCX处理管道 - 知识图谱增强版
同时生成向量数据库(Qdrant)和知识图谱(NebulaGraph)
自动提取决定要点和法律条款关联

作者: Athena平台团队
创建时间: 2025-12-24
"""

from __future__ import annotations
import asyncio
import json
import logging
import re

# 添加项目路径
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any

from docx import Document

# 使用安全哈希函数替代不安全的MD5/SHA1
from production.utils.security_helpers import short_hash

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# 导入项目现有服务
from nebula3.Config import Config

# NebulaGraph客户端 (同步API)
from nebula3.gclient.net import ConnectionPool
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from core.nlp.bge_embedding_service import BGEEmbeddingService

# 导入智能决定要点提取器
from production.scripts.review_decision.smart_keypoints_extractor import SmartKeypointsExtractor

# 简化日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.file_handler(f'/Users/xujian/Athena工作平台/logs/docx_pipeline_kg_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.stream_handler()
    ]
)
logger = logging.getLogger(__name__)


class NebulaGraphManager:
    """NebulaGraph管理器 - 线程安全"""

    def __init__(self):
        self.pool = None
        self.session = None
        self.lock = threading.Lock()
        self.space_name = "patent_rules"
        self.connected = False

    def connect(self) -> Any:
        """连接NebulaGraph"""
        with self.lock:
            if self.connected:
                return

            logger.info("连接NebulaGraph...")
            config = Config()
            config.max_connection_pool_size = 10

            try:
                self.pool = ConnectionPool()
                self.pool.init([('127.0.0.1', 9669)], config)
                self.session = self.pool.get_session('root', 'nebula')

                # 使用空间
                result = self.session.execute(f'USE {self.space_name};')
                self.connected = True
                logger.info(f"✅ NebulaGraph已连接: {self.space_name}")

                # 确保schema存在
                self._ensure_schema()

            except Exception as e:
                logger.error(f"❌ NebulaGraph连接失败: {e}")
                raise

    def _ensure_schema(self) -> Any:
        """确保schema存在"""
        try:
            # 检查现有TAG
            result = self.session.execute('SHOW TAGS;')
            existing_tags = set()
            if result.is_succeeded():
                for row in result.rows():
                    existing_tags.add(row[0].as_string())

            # 创建patent_decision TAG（如果不存在）
            if 'patent_decision' not in existing_tags:
                logger.info("创建patent_decision标签...")
                self.session.execute('''
                    CREATE TAG IF NOT EXISTS patent_decision(
                        doc_id string,
                        decision_number string,
                        decision_date string,
                        block_type string,
                        section string,
                        text string,
                        filename string,
                        char_count int,
                        source string DEFAULT "patent_decision"
                    );
                ''')

            # 创建legal_provision TAG（法律条款节点）
            if 'legal_provision' not in existing_tags:
                logger.info("创建legal_provision标签...")
                self.session.execute('''
                    CREATE TAG IF NOT EXISTS legal_provision(
                        law_name string,
                        article_number string,
                        full_text string,
                        provision_type string
                    );
                ''')

            # 检查边类型
            edge_result = self.session.execute('SHOW EDGES;')
            existing_edges = set()
            if edge_result.is_succeeded():
                for row in edge_result.rows():
                    existing_edges.add(row[0].as_string())

            # 创建引用关系边
            if 'cites_provision' not in existing_edges:
                logger.info("创建cites_provision边类型...")
                self.session.execute('''
                    CREATE EDGE IF NOT EXISTS cites_provision(
                        context string,
                        confidence double DEFAULT 1.0
                    );
                ''')

            logger.info("✅ Schema检查完成")

        except Exception as e:
            logger.warning(f"Schema检查警告: {e}")

    def insert_decision_chunk(self, chunk: dict[str, Any]) -> Any:
        """插入决定书数据块节点"""
        with self.lock:
            if not self.connected:
                return False

            try:
                chunk_id = chunk['chunk_id']
                doc_id = chunk.get('doc_id', '')
                text = chunk.get('text', '')[:500].replace('"', '\\"').replace('\n', '\\n')

                decision_num = str(chunk.get('metadata', {}).get('decision_number', '')).replace('"', '\\"')
                decision_date_val = str(chunk.get('metadata', {}).get('decision_date', '')).replace('"', '\\"')
                block_type_val = str(chunk.get('block_type', '')).replace('"', '\\"')
                section_val = str(chunk.get('section', '')).replace('"', '\\"')
                filename_val = str(chunk.get('metadata', {}).get('filename', '')).replace('"', '\\"')
                char_count_val = chunk.get('metadata', {}).get('char_count', 0)

                stmt = f'''INSERT VERTEX patent_decision VALUES "{chunk_id}":("{doc_id}", "{decision_num}", "{decision_date_val}", "{block_type_val}", "{section_val}", "{text}", "{filename_val}", {char_count_val}, "patent_decision");'''

                result = self.session.execute(stmt)
                return result.is_succeeded()

            except Exception as e:
                logger.debug(f"插入决定书节点失败: {e}")
                return False

    def insert_and_link_provision(self, chunk: dict[str, Any], law_ref: str) -> Any:
        """插入法律条款节点并创建关联关系"""
        with self.lock:
            if not self.connected:
                return False

            try:
                chunk_id = chunk['chunk_id']

                # 解析法律引用
                # 格式: "专利法 22", "实施细则 123"
                parts = law_ref.strip().split()
                if len(parts) < 2:
                    return False

                law_name = parts[0]
                article_num = parts[1]

                # 创建条款节点ID
                provision_id = f"prov_{law_name}_{article_num}"

                # 插入条款节点（如果不存在）
                prov_stmt = f'''INSERT VERTEX legal_provision VALUES "{provision_id}":("{law_name}", "{article_num}", "{law_ref}", "statute");'''
                self.session.execute(prov_stmt)

                # 创建引用关系边
                edge_stmt = f'''INSERT EDGE cites_provision VALUES "{chunk_id}"->"{provision_id}":("{law_ref}", 1.0);'''
                result = self.session.execute(edge_stmt)

                return result.is_succeeded()

            except Exception as e:
                logger.debug(f"插入法律条款节点失败: {e}")
                return False

    def get_statistics(self) -> dict[str, int]:
        """获取知识图谱统计"""
        with self.lock:
            if not self.connected:
                return {}

            stats = {}

            try:
                # 统计patent_decision节点
                result = self.session.execute('MATCH (v:patent_decision) RETURN count(v) as cnt;')
                if result.is_succeeded() and result.rows():
                    stats['patent_decision_nodes'] = result.rows()[0][0].as_int()

                # 统计legal_provision节点
                result = self.session.execute('MATCH (v:legal_provision) RETURN count(v) as cnt;')
                if result.is_succeeded() and result.rows():
                    stats['legal_provision_nodes'] = result.rows()[0][0].as_int()

                # 统计引用关系
                result = self.session.execute('MATCH ()-[e:cites_provision]->() RETURN count(e) as cnt;')
                if result.is_succeeded() and result.rows():
                    stats['cites_provision_edges'] = result.rows()[0][0].as_int()

            except Exception as e:
                logger.warning(f"获取统计失败: {e}")

            return stats

    def close(self) -> Any:
        """关闭连接"""
        with self.lock:
            if self.session:
                self.session.release()
            if self.pool:
                self.pool.close()
            self.connected = False
            logger.info("NebulaGraph连接已关闭")


class DocxPipelineWithKG:
    """DOCX处理管道 - 知识图谱增强版"""

    def __init__(self, enable_kg: bool = True):
        self.base_dir = Path("/Users/xujian/Athena工作平台")
        self.decision_dir = Path("/Volumes/AthenaData/语料/专利/专利无效复审决定原文")
        self.output_dir = self.base_dir / "production/data/patent_decisions"
        self.checkpoint_dir = self.output_dir / "checkpoints"

        # 服务
        self.bge_service = None
        self.qdrant_client = None
        self.nebula_manager = NebulaGraphManager() if enable_kg else None
        self.enable_kg = enable_kg
        self.executor = ThreadPoolExecutor(max_workers=8)

        # 智能决定要点提取器
        self.smart_extractor = SmartKeypointsExtractor()

        # 正则模式
        self.patterns = {
            'decision_number': re.compile(r'第(\d+)号'),
            'decision_date': re.compile(r'(\d{4})年(\d{1,2})月(\d{1,2})日'),
            'law_reference': re.compile(r'(专利法|实施细则)[\s\u3000]*第?([\d一二三四五六七八九十]+)[条条款款]'),
        }

        # 检查点
        self.checkpoint = self._load_checkpoint()

        # 性能统计
        self.stats = {
            'files_processed': 0,
            'chunks_created': 0,
            'vectors_generated': 0,
            'keypoints_extracted': 0,
            'kg_nodes_created': 0,
            'kg_edges_created': 0,
            'start_time': time.time()
        }

        logger.info(f"🚀 专利决定处理管道初始化完成 (KG: {'启用' if enable_kg else '禁用'})")

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
        logger.info("初始化服务...")

        # BGE服务
        try:
            model_path = self.base_dir / "models/converted/bge-large-zh-v1.5"
            if not model_path.exists():
                model_path = self.base_dir / "models/bge-large-zh-v1.5"

            config = {
                "model_path": str(model_path),
                "device": "cpu",
                "batch_size": 128,
                "max_length": 512,
                "normalize_embeddings": True,
                "cache_enabled": True,
                "preload": True
            }

            self.bge_service = BGEEmbeddingService(config)
            await self.bge_service.initialize()

            health = await self.bge_service.health_check()
            logger.info(f"✅ BGE服务就绪: {health['dimension']}维")

        except Exception as e:
            logger.error(f"❌ BGE初始化失败: {e}")
            raise

        # Qdrant客户端
        try:
            self.qdrant_client = QdrantClient(url="http://localhost:6333", timeout=60)
            collection_name = "patent_decisions"

            collections = self.qdrant_client.get_collections().collections
            collection_names = [c.name for c in collections]

            if collection_name not in collection_names:
                self.qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
                )
                logger.info("✅ 创建Qdrant集合")
            else:
                info = self.qdrant_client.get_collection(collection_name)
                logger.info(f"✅ Qdrant集合: {info.points_count}点")

        except Exception as e:
            logger.error(f"❌ Qdrant初始化失败: {e}")
            raise

        # NebulaGraph连接
        if self.enable_kg and self.nebula_manager:
            try:
                self.nebula_manager.connect()
            except Exception as e:
                logger.warning(f"⚠️ NebulaGraph初始化失败，将禁用知识图谱功能: {e}")
                self.nebula_manager = None
                self.enable_kg = False

    def extract_from_docx(self, file_path: Path) -> tuple[str, dict[str, Any]]:
        """从DOCX提取文本"""
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

            match = self.patterns['decision_number'].search(full_text)
            if match:
                metadata['decision_number'] = match.group(1)

            match = self.patterns['decision_date'].search(full_text)
            if match:
                metadata['decision_date'] = f"{match.group(1)}-{match.group(2).zfill(2)}-{match.group(3).zfill(2)}"

            return full_text, metadata

        except Exception as e:
            logger.debug(f"提取失败 {file_path.name}: {e}")
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

        # 章节识别规则
        section_patterns = {
            ('决定要点', 'keypoints'): [
                r'决定要点[：:：]\s*',
                r'本决定要点[：:：]\s*',
                r'要点[：:：]\s*',
                r'【要点】\s*',
                r'【决定要点】\s*',
            ],
            ('案由', 'background'): [
                r'案[ _]*由[：:：]\s*',
                r'一、[^\n]{0,10}案由',
                r'【案由】\s*',
            ],
            ('决定的理由', 'reasoning'): [
                r'决定的理由[：:：]\s*',
                r'理由[：:：]\s*',
                r'【理由】\s*',
                r'【决定的理由】\s*',
                r'二、[^\n]{0,10}理由',
            ],
            ('决定', 'decision'): [
                r'决定[：:：]\s*',
                r'决定如下[：:：]?\s*',
                r'【决定】\s*',
                r'三、[^\n]{0,10}决定',
                r'综上?，?决定',
            ],
        }

        # 编译正则表达式
        compiled_patterns = []
        for (section_name, block_type), patterns in section_patterns.items():
            for pattern in patterns:
                compiled_patterns.append((re.compile(pattern), section_name, block_type))

        for line in lines:
            line = line.strip()
            if not line:
                continue

            matched = False
            for pattern, section_name, block_type in compiled_patterns:
                if pattern.search(line):
                    if current_content:
                        chunks.append(self._create_chunk(doc_id, current_section, current_content, metadata))
                    current_section = section_name
                    current_content = []
                    matched = True
                    break

            if matched:
                continue

            current_content.append(line)

        # 保存最后一个section
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

        law_refs = self.patterns['law_reference'].findall(content_text)
        law_refs_cleaned = [f"{law} {art}" for law, art in law_refs]

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
                'related_laws': [ref for ref in law_refs_cleaned if '专利法' in ref or '实施细则' in ref]
            }
        }

    async def _extract_files_parallel(self, file_paths: list[Path]) -> list[tuple[str, dict[str, Any]]]:
        """并行提取文件"""
        loop = asyncio.get_event_loop()
        tasks = [loop.run_in_executor(self.executor, self.extract_from_docx, f) for f in file_paths]
        return await asyncio.gather(*tasks)

    async def process_batch(self, file_paths: list[Path], batch_index: int, total_batches: int):
        """处理一个批次"""
        batch_start = time.time()

        processed_set = set(self.checkpoint['processed_files'])
        files_to_process = [str(f) for f in file_paths if str(f) not in processed_set]

        if not files_to_process:
            logger.info(f"[{batch_index+1}/{total_batches}] 跳过 - 所有文件已处理")
            return

        logger.info(f"[{batch_index+1}/{total_batches}] 处理 {len(files_to_process)} DOCX文件...")

        all_chunks = []

        # 并行提取
        extract_results = await self._extract_files_parallel(file_paths)

        for file_path, (text, metadata) in zip(file_paths, extract_results, strict=False):
            if text:
                chunks = self.chunk_decision_text(text, metadata)

                # 检查是否有决定要点，如果没有则智能提取
                has_keypoints = any(c.get('block_type') == 'keypoints' for c in chunks)
                if not has_keypoints:
                    smart_keypoints = self.smart_extractor.extract_keypoints_from_text(text, metadata)
                    if smart_keypoints:
                        chunks.extend(smart_keypoints)
                        self.stats['keypoints_extracted'] += len(smart_keypoints)
                        logger.debug(f"  智能提取 {len(smart_keypoints)} 个决定要点: {file_path.name}")

                all_chunks.extend(chunks)

        extract_time = time.time() - batch_start

        if not all_chunks:
            logger.info("  批次无有效数据")
            return

        # 生成向量
        texts = [chunk['text'] for chunk in all_chunks]
        chunk_ids = [chunk['chunk_id'] for chunk in all_chunks]

        vector_batch_size = 128
        vectors = []

        for i in range(0, len(texts), vector_batch_size):
            batch_texts = texts[i:i + vector_batch_size]
            batch_ids = chunk_ids[i:i + vector_batch_size]

            response = await self.bge_service.encode(batch_texts, task_type="patent_decision")

            for chunk_id, embedding in zip(batch_ids, response.embeddings, strict=False):
                vectors.append({
                    'chunk_id': chunk_id,
                    'embedding': embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)
                })

        vector_time = time.time() - batch_start - extract_time

        # 上传Qdrant
        points = []
        for chunk, vec in zip(all_chunks, vectors, strict=False):
            hash_id = abs(hash(vec['chunk_id'])) % (10 ** 10)
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
                'source': 'patent_decision',
                'related_laws': chunk['metadata'].get('related_laws', [])
            }
            points.append(PointStruct(id=hash_id, vector=vec['embedding'], payload=payload))

        upsert_batch_size = 500
        for i in range(0, len(points), upsert_batch_size):
            batch_points = points[i:i + upsert_batch_size]
            self.qdrant_client.upsert(collection_name="patent_decisions", points=batch_points)

        upload_time = time.time() - batch_start - extract_time - vector_time

        # 生成知识图谱 (如果启用)
        kg_start = time.time()
        kg_nodes = 0
        kg_edges = 0

        if self.enable_kg and self.nebula_manager:
            logger.info("  生成知识图谱...")

            for chunk in all_chunks:
                # 插入决定书节点
                if self.nebula_manager.insert_decision_chunk(chunk):
                    kg_nodes += 1

                # 插入法律条款节点并创建关联
                law_refs = chunk.get('metadata', {}).get('law_references', [])
                for ref in law_refs:
                    if self.nebula_manager.insert_and_link_provision(chunk, ref):
                        kg_edges += 1

            self.stats['kg_nodes_created'] += kg_nodes
            self.stats['kg_edges_created'] += kg_edges

        kg_time = time.time() - kg_start

        # 更新检查点
        for file_path in files_to_process:
            self.checkpoint['processed_files'].append(file_path)

        self.checkpoint['total_chunks'] += len(all_chunks)
        self.checkpoint['total_vectors'] += len(vectors)
        self.checkpoint['qdrant_uploaded'] += len(points)
        self._save_checkpoint()

        # 更新统计
        self.stats['files_processed'] += len(files_to_process)
        self.stats['chunks_created'] += len(all_chunks)
        self.stats['vectors_generated'] += len(vectors)

        batch_time = time.time() - batch_start
        speed = len(files_to_process) / batch_time if batch_time > 0 else 0

        logger.info(f"  完成: {len(all_chunks)}块, {len(vectors)}向量, {kg_nodes}节点, {kg_edges}边 | 速度: {speed:.1f}文件/秒")

        return {
            'files_processed': len(files_to_process),
            'chunks_created': len(all_chunks),
            'vectors_generated': len(vectors),
            'kg_nodes': kg_nodes,
            'kg_edges': kg_edges,
            'batch_time': batch_time
        }

    async def run_full_pipeline(self, batch_size: int = 500):
        """运行完整管道"""
        logger.info("=" * 70)
        logger.info("🚀 专利决定处理管道启动（知识图谱增强版）")
        logger.info("=" * 70)

        await self.initialize_services()

        # 获取DOCX文件
        docx_files = list(self.decision_dir.glob("*.docx"))

        logger.info(f"📂 数据目录: {self.decision_dir.name}")
        logger.info(f"📊 DOCX文件数: {len(docx_files):,}")
        logger.info("📄 DOC文件数: 20,503 (暂不处理)")
        logger.info(f"🔗 知识图谱: {'启用' if self.enable_kg else '禁用'}")
        logger.info("")

        total_batches = (len(docx_files) + batch_size - 1) // batch_size
        logger.info(f"批次数: {total_batches} (批次大小: {batch_size})")
        logger.info("")

        results = []
        start_time = time.time()

        # 处理所有批次
        for batch_idx in range(total_batches):
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, len(docx_files))
            batch_files = docx_files[start_idx:end_idx]

            try:
                result = await self.process_batch(batch_files, batch_idx, total_batches)
                if result:
                    results.append(result)

                # 进度报告
                elapsed = time.time() - start_time
                progress = (batch_idx + 1) / total_batches * 100
                avg_speed = self.stats['files_processed'] / elapsed if elapsed > 0 else 0
                remaining_files = len(docx_files) - self.stats['files_processed']
                eta = remaining_files / avg_speed if avg_speed > 0 else 0

                logger.info(f"  进度: {progress:.1f}% | 已用: {elapsed/60:.1f}分钟 | "
                           f"预计剩余: {eta/60:.1f}分钟")
                logger.info("")

            except Exception as e:
                logger.error(f"❌ 批次 {batch_idx + 1} 失败: {e}")
                import traceback
                traceback.print_exc()
                continue

        # 最终报告
        total_time = time.time() - start_time
        logger.info("=" * 70)
        logger.info("🎉 全部批次处理完成！")
        logger.info("=" * 70)
        logger.info(f"📊 处理文件: {self.stats['files_processed']}")
        logger.info(f"📦 生成块: {self.stats['chunks_created']}")
        logger.info(f"🔢 生成向量: {self.stats['vectors_generated']}")
        logger.info(f"🎯 决定要点: {self.stats['keypoints_extracted']}")
        if self.enable_kg:
            logger.info(f"🔗 KG节点: {self.stats['kg_nodes_created']}")
            logger.info(f"🔗 KG边: {self.stats['kg_edges_created']}")
        logger.info(f"⏱️  耗时: {total_time/60:.1f}分钟")
        logger.info(f"⚡ 平均速度: {self.stats['files_processed']/total_time:.1f} 文件/秒")
        logger.info("")

        # 验证Qdrant
        try:
            info = self.qdrant_client.get_collection("patent_decisions")
            logger.info(f"✅ Qdrant集合: {info.points_count}点")
        except Exception as e:
            logger.warning(f"验证失败: {e}")

        # 验证知识图谱
        if self.enable_kg and self.nebula_manager:
            stats = self.nebula_manager.get_statistics()
            logger.info(f"✅ 知识图谱统计: {stats}")

    def close(self) -> Any:
        """关闭连接"""
        if self.nebula_manager:
            self.nebula_manager.close()
        if self.executor:
            self.executor.shutdown(wait=True)


def launch_doc_conversion() -> Any:
    """启动DOC转DOCX转换任务"""
    logger.info("")
    logger.info("=" * 70)
    logger.info("🔄 DOCX处理完成，自动启动DOC转DOCX转换任务")
    logger.info("=" * 70)
    logger.info("")

    import subprocess
    import sys

    converter_script = Path(__file__).parent / "doc_to_docx_converter.py"

    if not converter_script.exists():
        logger.error(f"❌ 转换脚本不存在: {converter_script}")
        return

    try:
        # 使用subprocess在新的进程中启动转换任务
        # 这会与当前进程分离，即使当前进程结束也会继续运行
        logger.info(f"🚀 启动转换任务: {converter_script}")
        logger.info("")

        # 在macOS上使用nohup确保进程在终端关闭后继续运行
        process = subprocess.Popen(
            [sys.executable, str(converter_script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True  # POSIX: 创建新会话，脱离父进程
        )

        logger.info(f"✅ 转换任务已启动 (进程ID: {process.pid})")
        logger.info("")
        logger.info("💡 转换日志将输出到:")
        logger.info(f"   {converter_script.parent / 'logs' / 'doc_conversion_*.log'}")
        logger.info("")

    except Exception as e:
        logger.error(f"❌ 启动转换任务失败: {e}")


async def main():
    """主函数"""
    # 启用知识图谱功能
    pipeline = DocxPipelineWithKG(enable_kg=True)

    try:
        # 处理所有批次
        await pipeline.run_full_pipeline(batch_size=500)

        # 处理完成后自动启动DOC转换
        launch_doc_conversion()

    finally:
        pipeline.close()


if __name__ == "__main__":
    asyncio.run(main())
