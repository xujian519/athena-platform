#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
条款级法律向量化系统
将法律文档按条款拆分并进行向量化，支持精确的条款检索
"""

import hashlib
import json
import logging
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    import numpy as np
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance,
        FieldCondition,
        Filter,
        MatchValue,
        PointStruct,
        VectorParams,
    )
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    logger.info(f"❌ 缺少依赖: {e}")
    logger.info('请安装: pip install sentence-transformers qdrant-client')
    exit(1)

@dataclass
class LegalClause:
    """法律条款数据结构"""
    clause_id: str                    # 条款唯一标识
    clause_number: str               # 条款编号 (如'第二十六条')
    clause_type: str                 # 条款类型 (条/款/项/目等)
    content: str                     # 条款内容
    law_name: str                    # 法律名称
    chapter: str | None = None    # 所属章节
    article: str | None = None    # 所属条文章节
    file_path: str = ''              # 原始文件路径
    line_number: int = 0             # 在文件中的行号
    vector: Optional[List[float] = None  # 向量表示


class ClauseLevelVectorizer:
    """条款级法律向量化器"""

    def __init__(self):
        # 配置路径
        self.laws_path = Path('/Users/xujian/Athena工作平台/domains/legal-knowledge')
        self.model_path = '/Users/xujian/Athena工作平台/models/bge-large-zh-v1.5'
        self.output_dir = Path('/Users/xujian/Athena工作平台/data/clause_level_vectors')
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 向量化配置
        self.collection_name = 'legal_clauses'
        self.vector_dim = 1024
        self.batch_size = 50  # 条款级处理可以用更大批次

        logger.info('📦 加载BGE模型...')
        self.model = SentenceTransformer(self.model_path, device='cpu')
        logger.info('✅ 模型加载成功')

        # 初始化Qdrant客户端
        try:
            self.qdrant = QdrantClient(host='localhost', port=6333)
            logger.info('✅ Qdrant连接成功')
        except Exception as e:
            logger.error(f"❌ Qdrant连接失败: {e}")
            self.qdrant = None

        # 条款识别模式
        self._init_clause_patterns()

        # 统计信息
        self.stats = {
            'total_files': 0,
            'total_clauses': 0,
            'clause_types': {},
            'law_documents': {},
            'processing_errors': 0,
            'vector_generation_time': 0.0
        }

    def _init_clause_patterns(self) -> Any:
        """初始化条款识别模式"""
        # 主要条款模式 - 匹配"第X条"
        self.article_pattern = re.compile(
            r'^第([一二三四五六七八九十百千万零0-9]+)条[：:\s]*(.*?)$',
            re.MULTILINE | re.IGNORECASE
        )

        # 款级模式 - 匹配"(一)"、"(1)"等
        self.sub_clause_patterns = [
            re.compile(r'^（([一二三四五六七八九十百千万零]+)）[：:\s]*(.*?)$', re.MULTILINE),  # 中文数字
            re.compile(r'^\(([一二三四五六七八九十百千万零]+)\)[：:\s]*(.*?)$', re.MULTILINE),  # 中文数字括号
            re.compile(r'^(\d+)[、.:,][：:\s]*(.*?)$', re.MULTILINE),  # 阿拉伯数字
            re.compile(r'^(\d+)\.[：:\s]*(.*?)$', re.MULTILINE),  # 带点的阿拉伯数字
        ]

        # 章节模式
        self.chapter_pattern = re.compile(r'^第[一二三四五六七八九十百千万零]+章[：:\s]*(.*?)$', re.MULTILINE)

        # 节模式
        self.section_pattern = re.compile(r'^第[一二三四五六七八九十百千万零]+节[：:\s]*(.*?)$', re.MULTILINE)

    def extract_clauses_from_file(self, file_path: Path) -> List[LegalClause]:
        """从文件中提取条款"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"❌ 读取文件失败 {file_path}: {e}")
            return []

        clauses = []
        lines = content.split('\n')
        law_name = self._extract_law_name(content, file_path.name)
        current_chapter = None
        current_section = None

        # 逐行解析
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or len(line) < 3:
                continue

            # 检查章节
            chapter_match = self.chapter_pattern.match(line)
            if chapter_match:
                current_chapter = chapter_match.group(1)
                continue

            # 检查节
            section_match = self.section_pattern.match(line)
            if section_match:
                current_section = section_match.group(1)
                continue

            # 检查主要条款 (第X条)
            article_match = self.article_pattern.match(line)
            if article_match:
                clause = self._create_article_clause(
                    article_match, law_name, file_path, line_num,
                    current_chapter, current_section
                )
                if clause:
                    clauses.append(clause)
                continue

            # 检查次级条款
            for pattern in self.sub_clause_patterns:
                sub_match = pattern.match(line)
                if sub_match:
                    clause = self._create_sub_clause(
                        sub_match, law_name, file_path, line_num,
                        current_chapter, current_section
                    )
                    if clause:
                        clauses.append(clause)
                    break

        return clauses

    def _extract_law_name(self, content: str, filename: str) -> str:
        """提取法律名称"""
        # 尝试从内容开头提取
        lines = content.split('\n')[:10]
        for line in lines:
            line = line.strip()
            if line and ('法' in line or '条例' in line or '规定' in line):
                if len(line) < 100 and not line.startswith('#'):
                    return line

        # 从文件名提取
        name = filename.replace('.md', '')
        # 移除日期和括号内容
        name = re.sub(r'\([^)]*\)', '', name)
        name = re.sub(r'\d{4}-\d{2}-\d{2}', '', name)
        return name.strip()

    def _create_article_clause(self, match, law_name: str, file_path: Path,
                             line_num: int, chapter: str = None, section: str = None) -> LegalClause | None:
        """创建主要条款"""
        try:
            article_num = f"第{match.group(1)}条"
            content = match.group(2).strip()

            if len(content) < 5:
                return None

            clause_id = self._generate_clause_id(law_name, article_num)

            clause = LegalClause(
                clause_id=clause_id,
                clause_number=article_num,
                clause_type='条',
                content=content,
                law_name=law_name,
                chapter=chapter,
                article=article_num,
                file_path=str(file_path),
                line_number=line_num
            )

            self.stats['clause_types']['条'] = self.stats['clause_types'].get('条', 0) + 1
            return clause

        except Exception as e:
            logger.warning(f"创建条款失败: {e}")
            return None

    def _create_sub_clause(self, match, law_name: str, file_path: Path,
                          line_num: int, chapter: str = None, section: str = None) -> LegalClause | None:
        """创建次级条款"""
        try:
            clause_num = match.group(1)
            content = match.group(2).strip()

            if len(content) < 5:
                return None

            # 确定条款类型
            if '（' in match.group(0) or '(' in match.group(0):
                clause_type = '项'
            elif '.' in match.group(0) or '、' in match.group(0):
                clause_type = '款' if '、' in match.group(0) else '目'
            else:
                clause_type = '其他'

            clause_id = self._generate_clause_id(law_name, clause_num, clause_type)

            clause = LegalClause(
                clause_id=clause_id,
                clause_number=clause_num,
                clause_type=clause_type,
                content=content,
                law_name=law_name,
                chapter=chapter,
                article=clause_num,
                file_path=str(file_path),
                line_number=line_num
            )

            self.stats['clause_types'][clause_type] = self.stats['clause_types'].get(clause_type, 0) + 1
            return clause

        except Exception as e:
            logger.warning(f"创建次级条款失败: {e}")
            return None

    def _generate_clause_id(self, law_name: str, clause_num: str, clause_type: str = '条') -> str:
        """生成条款唯一ID"""
        # 创建基于法律名称和条款编号的哈希ID
        id_string = f"{law_name}_{clause_num}_{clause_type}"
        hash_obj = hashlib.md5(id_string.encode('utf-8', usedforsecurity=False)
        return hash_obj.hexdigest()[:16]

    def process_all_legal_documents(self) -> List[LegalClause]:
        """处理所有法律文档"""
        logger.info(f"📁 开始扫描法律文档目录: {self.laws_path}")

        all_clauses = []
        doc_count = 0

        for legal_file in self.laws_path.rglob('*.md'):
            if legal_file.name.startswith('.'):
                continue

            doc_count += 1
            logger.info(f"📂 处理文档 ({doc_count}): {legal_file.name}")

            clauses = self.extract_clauses_from_file(legal_file)

            if clauses:
                all_clauses.extend(clauses)
                law_name = clauses[0].law_name
                self.stats['law_documents'][law_name] = len(clauses)
                logger.info(f"   ✅ 提取了 {len(clauses)} 个条款")
            else:
                logger.warning(f"   ⚠️ 未提取到条款")

        self.stats['total_files'] = doc_count
        self.stats['total_clauses'] = len(all_clauses)

        logger.info(f"✅ 总计处理 {doc_count} 个文档，提取 {len(all_clauses)} 个条款")
        return all_clauses

    def create_clause_collection(self) -> bool:
        """创建条款级向量集合"""
        if not self.qdrant:
            return False

        try:
            collections = self.qdrant.get_collections().collections
            collection_names = [c.name for c in collections]

            if self.collection_name not in collection_names:
                logger.info(f"🔧 创建条款集合 '{self.collection_name}'")
                self.qdrant.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_dim,
                        distance=Distance.COSINE
                    )
                )
                logger.info('✅ 条款集合创建成功')
            else:
                logger.info(f"📝 条款集合 '{self.collection_name}' 已存在")

            return True
        except Exception as e:
            logger.error(f"❌ 创建条款集合失败: {e}")
            return False

    def vectorize_and_upload_clauses(self, clauses: List[LegalClause]) -> Any:
        """向量化并上传条款"""
        if not self.qdrant:
            logger.warning('⚠️ Qdrant不可用，跳过上传播放')
            return

        if not clauses:
            logger.warning('⚠️ 没有条款需要向量化')
            return

        logger.info(f"🔄 开始向量化 {len(clauses)} 个条款...")
        start_time = time.time()

        # 批处理向量化
        for i in range(0, len(clauses), self.batch_size):
            batch = clauses[i:i + self.batch_size]
            batch_num = i // self.batch_size + 1
            total_batches = (len(clauses) + self.batch_size - 1) // self.batch_size

            logger.info(f"📦 处理批次 {batch_num}/{total_batches} (共 {len(batch)} 个条款)")

            try:
                # 提取文本内容
                texts = [clause.content for clause in batch]

                # 生成向量
                embeddings = self.model.encode(
                    texts,
                    batch_size=16,
                    normalize_embeddings=True,
                    show_progress_bar=False
                )

                # 创建Qdrant点
                points = []
                for clause, embedding in zip(batch, embeddings):
                    point = PointStruct(
                        id=hash(clause.clause_id) % (2**31),  # 转换为整数ID
                        vector=embedding.tolist(),
                        payload={
                            'clause_id': clause.clause_id,
                            'clause_number': clause.clause_number,
                            'clause_type': clause.clause_type,
                            'content': clause.content,
                            'law_name': clause.law_name,
                            'chapter': clause.chapter,
                            'article': clause.article,
                            'file_path': clause.file_path,
                            'line_number': clause.line_number,
                            'search_text': f"{clause.law_name} {clause.clause_number} {clause.content}"
                        }
                    )
                    points.append(point)

                # 上传到Qdrant
                self.qdrant.upsert(
                    collection_name=self.collection_name,
                    points=points
                )

                logger.info(f"✅ 批次 {batch_num} 上传成功")

            except Exception as e:
                logger.error(f"❌ 批次 {batch_num} 处理失败: {e}")
                continue

        self.stats['vector_generation_time'] = time.time() - start_time
        logger.info(f"🎉 条款向量化完成！总耗时: {self.stats['vector_generation_time']:.2f}秒")

    def save_clause_metadata(self, clauses: List[LegalClause]) -> None:
        """保存条款元数据"""
        metadata = {
            'created_time': datetime.now().isoformat(),
            'total_clauses': len(clauses),
            'collection_name': self.collection_name,
            'vector_dim': self.vector_dim,
            'model_path': self.model_path,
            'clause_types': self.stats['clause_types'],
            'law_documents': dict(sorted(self.stats['law_documents'].items(),
                                        key=lambda x: x[1], reverse=True)),
            'processing_stats': {
                'total_files': self.stats['total_files'],
                'processing_errors': self.stats['processing_errors'],
                'vector_generation_time': self.stats['vector_generation_time']
            }
        }

        # 保存元数据
        metadata_file = self.output_dir / 'clause_metadata.json'
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        # 保存条款数据
        clause_data = []
        for clause in clauses:
            clause_data.append({
                'clause_id': clause.clause_id,
                'clause_number': clause.clause_number,
                'clause_type': clause.clause_type,
                'content': clause.content,
                'law_name': clause.law_name,
                'chapter': clause.chapter,
                'article': clause.article,
                'file_path': clause.file_path,
                'line_number': clause.line_number
            })

        clause_file = self.output_dir / 'legal_clauses.json'
        with open(clause_file, 'w', encoding='utf-8') as f:
            json.dump(clause_data, f, ensure_ascii=False, indent=2)

        logger.info(f"💾 条款数据已保存:")
        logger.info(f"   - 元数据: {metadata_file}")
        logger.info(f"   - 条款数据: {clause_file}")

    def run(self) -> None:
        """主执行流程"""
        logger.info('🚀 启动条款级法律向量化系统')

        # 1. 处理文档并提取条款
        clauses = self.process_all_legal_documents()

        if not clauses:
            logger.error('❌ 没有提取到任何条款')
            return False

        # 2. 创建向量集合
        if self.create_clause_collection():
            # 3. 向量化并上传
            self.vectorize_and_upload_clauses(clauses)

        # 4. 保存元数据
        self.save_clause_metadata(clauses)

        # 5. 输出统计报告
        self._print_stats()

        logger.info('🎉 条款级向量化完成！')
        return True

    def _print_stats(self) -> Any:
        """打印统计信息"""
        logger.info(f"\n{'='*60}")
        logger.info('📊 条款级向量化统计报告:')
        logger.info(f"   - 处理文档: {self.stats['total_files']} 个")
        logger.info(f"   - 提取条款: {self.stats['total_clauses']} 个")
        logger.info(f"   - 条款类型分布:")

        for clause_type, count in sorted(self.stats['clause_types'].items(),
                                        key=lambda x: x[1], reverse=True):
            logger.info(f"     * {clause_type}: {count} 个")

        logger.info(f"   - 法律文档分布 (前10):")
        law_docs = sorted(self.stats['law_documents'].items(),
                         key=lambda x: x[1], reverse=True)[:10]
        for law_name, count in law_docs:
            logger.info(f"     * {law_name}: {count} 条")

        if self.stats['vector_generation_time'] > 0:
            speed = self.stats['total_clauses'] / self.stats['vector_generation_time']
            logger.info(f"   - 向量化速度: {speed:.2f} 条款/秒")
            logger.info(f"   - 总处理时间: {self.stats['vector_generation_time']:.2f}秒")


if __name__ == '__main__':
    vectorizer = ClauseLevelVectorizer()
    vectorizer.run()