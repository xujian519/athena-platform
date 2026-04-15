#!/usr/bin/env python3
"""
统一法律向量库更新脚本
Unified Legal Vector Database Updater

功能:
1. 扫描法律语料目录,识别新增/更新的法律文件
2. 使用BGE模型生成高质量向量嵌入
3. 更新Qdrant统一法律向量集合
4. 保留元数据(法律分类、发布日期、关键词等)

作者: Athena AI Team
版本: v1.0.0
日期: 2026-01-11
"""

from __future__ import annotations
import hashlib
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# 添加项目路径
project_root = Path("/Users/xujian/Athena工作平台")
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.file_handler(project_root / 'logs' / 'legal_vector_update.log'),
        logging.stream_handler()
    ]
)
logger = logging.getLogger(__name__)

# 第三方库导入
try:
    import numpy as np
    import torch
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
    logger.error(f"缺少必要的依赖库: {e}")
    logger.error("请安装: pip3 install qdrant-client sentence-transformers numpy torch")
    sys.exit(1)

# 导入平台BGE-M3加载器
try:
    from core.nlp.bge_m3_loader import BGEM3ModelLoader
except ImportError:
    logger.warning("无法导入平台BGE-M3加载器,将使用默认加载方式")
    BGEM3ModelLoader = None


# ==================== 配置参数 ====================

LAWS_CORPUS_DIR = Path("/Volumes/AthenaData/07_Corpus_Data/语料/Laws-1.0.0")
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "unified_legal_laws"  # 统一法律向量集合
BGE_MODEL_PATH = "/Users/xujian/Athena工作平台/models/converted/BAAI/bge-m3"  # MPS优化的BGE-M3模型路径
BATCH_SIZE = 32
CHUNK_MAX_LENGTH = 512  # 分块最大长度
CHUNK_OVERLAP = 50  # 分块重叠
VECTOR_DIMENSION = 1024  # BGE-M3向量维度


# ==================== 工具类 ====================

class LegalFileParser:
    """法律文件解析器"""

    # 法律分类映射
    CATEGORY_MAP = {
        "宪法": "constitution",
        "宪法相关法": "constitution_related",
        "民法商法": "civil_commercial",
        "行政法": "administrative",
        "经济法": "economic",
        "社会法": "social",
        "刑法": "criminal",
        "诉讼与非诉讼程序法": "procedure",
        "行政法规": "administrative_regulation",
        "部门规章": "department_rule",
        "地方性法规": "local_regulation",
        "司法解释": "judicial_interpretation",
        "案例": "case",
        "其他": "other"
    }

    @staticmethod
    def parse_law_file(file_path: Path) -> dict[str, Any | None]:
        """
        解析法律文件

        Args:
            file_path: 法律文件路径

        Returns:
            包含法律元数据和内容的字典,如果解析失败则返回None
        """
        try:
            with open(file_path, encoding='utf-8') as f:
                content = f.read()

            # 提取标题和日期
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            title = title_match.group(1).strip() if title_match else file_path.stem

            # 提取日期
            date_pattern = r'(\d{4})[年\-](\d{1,2})[月\-](\d{1,2})[日\-]'
            dates = re.findall(date_pattern, content)
            date_str = f"{dates[0][0]}-{dates[0][1].zfill(2)}-{dates[0][2].zfill(2)}" if dates else None

            # 提取分类(从目录名)
            category_cn = file_path.parent.name
            category_en = LegalFileParser.CATEGORY_MAP.get(category_cn, "other")

            # 移除标题部分后的内容
            content_body = re.sub(r'^#.*?$<!-- INFO END -->', '', content, flags=re.DOTALL)

            # 提取关键词(从标题中)
            keywords = LegalFileParser._extract_keywords(title)

            return {
                "title": title,
                "date": date_str,
                "date_obj": datetime.strptime(date_str, "%Y-%m-%d") if date_str else None,
                "category_cn": category_cn,
                "category_en": category_en,
                "keywords": keywords,
                "content": content_body.strip(),
                "file_path": str(file_path),
                "file_name": file_path.name,
                "file_size": file_path.stat().st_size
            }
        except Exception as e:
            logger.warning(f"解析文件失败 {file_path}: {e}")
            return None

    @staticmethod
    def _extract_keywords(title: str) -> list[str]:
        """从标题中提取关键词"""
        # 常见法律关键词
        common_keywords = [
            "法", "条例", "规定", "办法", "细则", "解释",
            "决定", "规则", "章程", "纲要", "方案"
        ]
        keywords = []
        for kw in common_keywords:
            if kw in title:
                keywords.append(kw)
        return keywords


class LegalTextChunker:
    """法律文本分块器"""

    @staticmethod
    def chunk_legal_text(law_data: dict[str, Any]) -> list[dict[str, Any]]:
        """
        将法律文本分块

        Args:
            law_data: 法律数据字典

        Returns:
            分块列表,每个分块包含文本和元数据
        """
        content = law_data["content"]
        chunks = []

        # 按条/款/项分割
        sections = re.split(r'\n(?=第[一二三四五六七八九十百]+[章节条款])', content)

        current_chunk = ""
        chunk_index = 0

        for section in sections:
            section = section.strip()
            if not section:
                continue

            # 如果当前块加入这个section会超长,则保存当前块并开始新块
            if len(current_chunk) + len(section) > CHUNK_MAX_LENGTH and current_chunk:
                chunks.append({
                    "text": current_chunk.strip(),
                    "chunk_index": chunk_index,
                    "section": LegalTextChunker._extract_section_number(current_chunk)
                })
                chunk_index += 1
                current_chunk = section + "\n\n"
            else:
                current_chunk += section + "\n\n"

        # 添加最后一个块
        if current_chunk.strip():
            chunks.append({
                "text": current_chunk.strip(),
                "chunk_index": chunk_index,
                "section": LegalTextChunker._extract_section_number(current_chunk)
            })

        # 为每个chunk添加完整的元数据
        for chunk in chunks:
            chunk.update({
                "law_title": law_data["title"],
                "law_date": law_data["date"],
                "law_category_cn": law_data["category_cn"],
                "law_category_en": law_data["category_en"],
                "law_keywords": law_data["keywords"],
                "law_file_path": law_data["file_path"]
            })

        return chunks

    @staticmethod
    def _extract_section_number(text: str) -> str:
        """提取章节条编号"""
        match = re.search(r'第[一二三四五六七八九十百千]+[章节条款]', text)
        return match.group(0) if match else ""


class LegalVectorEmbedder:
    """法律向量嵌入生成器"""

    def __init__(self, model_path: str = BGE_MODEL_PATH):
        """初始化BGE-M3模型"""
        logger.info(f"加载BGE-M3模型: {model_path}")

        # 检测设备
        if torch.backends.mps.is_available():
            self.device = 'mps'
            logger.info("🔥 使用MPS设备 (Apple Silicon GPU加速)")
        elif torch.cuda.is_available():
            self.device = 'cuda'
            logger.info("🎮 使用CUDA设备 (NVIDIA GPU加速)")
        else:
            self.device = 'cpu'
            logger.info("💻 使用CPU设备")

        # 加载模型
        self.model = SentenceTransformer(model_path, device=self.device)
        self.vector_size = VECTOR_DIMENSION
        logger.info(f"✅ 模型加载完成,向量维度: {self.vector_size}")

    def encode_texts(self, texts: list[str], batch_size: int = BATCH_SIZE) -> np.ndarray:
        """
        批量生成文本向量

        Args:
            texts: 文本列表
            batch_size: 批次大小

        Returns:
            向量数组
        """
        logger.info(f"生成 {len(texts)} 个文本的向量嵌入...")
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            normalize_embeddings=True  # 归一化向量
        )
        logger.info(f"向量生成完成,形状: {embeddings.shape}")
        return embeddings


class QdrantLegalManager:
    """Qdrant法律向量库管理器"""

    def __init__(self, host: str = QDRANT_HOST, port: int = QDRANT_PORT):
        """初始化Qdrant客户端"""
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = COLLECTION_NAME
        logger.info(f"Qdrant客户端初始化完成: {host}:{port}")

    def ensure_collection_exists(self, vector_size: int) -> Any:
        """确保集合存在"""
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]

        if self.collection_name not in collection_names:
            logger.info(f"创建集合: {self.collection_name}")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE  # 使用余弦相似度
                )
            )
            logger.info("集合创建成功")
        else:
            logger.info(f"集合已存在: {self.collection_name}")
            collection_info = self.client.get_collection(self.collection_name)
            logger.info(f"集合当前点数: {collection_info.points_count}")

    def upsert_chunks(self, chunks: list[dict[str, Any]], embeddings: np.ndarray) -> Any:
        """
        批量插入/更新向量点

        Args:
            chunks: 分块列表
            embeddings: 向量数组
        """
        logger.info(f"准备插入 {len(chunks)} 个向量点...")

        points = []
        skipped = 0

        for _i, (chunk, embedding) in enumerate(zip(chunks, embeddings, strict=False)):
            # 生成唯一ID
            unique_id = self._generate_point_id(chunk)

            # 确保向量是list类型并验证
            if isinstance(embedding, np.ndarray):
                # 检查是否有NaN或Inf
                if np.isnan(embedding).any() or np.isinf(embedding).any():
                    logger.warning(f"跳过包含NaN/Inf的向量: {chunk.get('law_title', 'Unknown')}")
                    skipped += 1
                    continue

                vector_list = embedding.astype(np.float32).tolist()
            else:
                # 检查list中是否有NaN或Inf
                if any(not isinstance(x, (int, float)) or np.isnan(x) or np.isinf(x) for x in embedding):
                    logger.warning(f"跳过包含无效值的向量: {chunk.get('law_title', 'Unknown')}")
                    skipped += 1
                    continue
                vector_list = list(embedding)

            # 构建payload,确保所有值都是JSON可序列化的
            payload = {
                "text": str(chunk.get("text", ""))[:10000],  # 限制文本长度
                "law_title": str(chunk.get("law_title", "")),
                "law_date": str(chunk.get("law_date", "")),
                "law_category_cn": str(chunk.get("law_category_cn", "")),
                "law_category_en": str(chunk.get("law_category_en", "")),
                "law_keywords": list(chunk.get("law_keywords", [])),
                "chunk_index": int(chunk.get("chunk_index", 0)),
                "section": str(chunk.get("section", "")),
                "file_path": str(chunk.get("law_file_path", "")),
                "updated_at": datetime.now().isoformat()
            }

            point = PointStruct(
                id=unique_id,
                vector=vector_list,
                payload=payload
            )
            points.append(point)

        if skipped > 0:
            logger.warning(f"跳过了 {skipped} 个无效向量")

        if not points:
            logger.error("没有有效的向量点可插入")
            return

        # 批量插入
        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
            wait=True
        )
        logger.info(f"成功插入 {len(points)} 个向量点")

    def _generate_point_id(self, chunk: dict[str, Any]) -> int:
        """生成唯一的点ID (必须是整数)"""
        # 使用文件路径+chunk_index生成hash作为ID
        content = f"{chunk['law_file_path']}_{chunk['chunk_index']}"
        # 使用MD5 hash的前16位作为整数ID
        hash_hex = hashlib.md5(content.encode('utf-8'), usedforsecurity=False).hexdigest()[:16]
        return int(hash_hex, 16)


class UnifiedLegalVectorUpdater:
    """统一法律向量库更新器"""

    def __init__(self):
        """初始化更新器"""
        self.parser = LegalFileParser()
        self.chunker = LegalTextChunker()
        self.embedder = None  # 延迟初始化
        self.qdrant = None    # 延迟初始化

        # 统计信息
        self.stats = {
            "total_files": 0,
            "parsed_files": 0,
            "total_chunks": 0,
            "uploaded_chunks": 0,
            "errors": 0
        }

    def scan_law_files(self, newer_than: datetime | None = None) -> list[Path]:
        """
        扫描法律文件

        Args:
            newer_than: 只处理此日期之后修改的文件

        Returns:
            法律文件路径列表
        """
        logger.info(f"扫描法律语料目录: {LAWS_CORPUS_DIR}")

        law_files = []
        for pattern in ["*.md", "*.txt"]:
            law_files.extend(LAWS_CORPUS_DIR.rglob(pattern))

        # 过滤日期
        if newer_than:
            law_files = [f for f in law_files if datetime.fromtimestamp(f.stat().st_mtime) > newer_than]
            logger.info(f"找到 {len(law_files)} 个新文件(修改时间 > {newer_than})")
        else:
            logger.info(f"找到 {len(law_files)} 个法律文件")

        self.stats["total_files"] = len(law_files)
        return law_files

    def process_files(self, law_files: list[Path]) -> Any | None:
        """
        处理法律文件并更新向量库

        Args:
            law_files: 法律文件路径列表
        """
        # 初始化模型和Qdrant
        logger.info("初始化BGE模型...")
        self.embedder = LegalVectorEmbedder()

        logger.info("初始化Qdrant管理器...")
        self.qdrant = QdrantLegalManager()
        self.qdrant.ensure_collection_exists(self.embedder.vector_size)

        # 处理文件
        all_chunks = []
        for i, law_file in enumerate(law_files, 1):
            logger.info(f"[{i}/{len(law_files)}] 处理: {law_file.name}")

            # 解析文件
            law_data = self.parser.parse_law_file(law_file)
            if not law_data:
                self.stats["errors"] += 1
                continue

            self.stats["parsed_files"] += 1

            # 分块
            chunks = self.chunker.chunk_legal_text(law_data)
            logger.info(f"  分块: {len(chunks)} 个")
            self.stats["total_chunks"] += len(chunks)

            all_chunks.extend(chunks)

            # 批量处理
            if len(all_chunks) >= BATCH_SIZE:
                self._upload_chunks(all_chunks)
                all_chunks = []

        # 处理剩余的chunks
        if all_chunks:
            self._upload_chunks(all_chunks)

    def _upload_chunks(self, chunks: list[dict[str, Any]]) -> Any:
        """上传一批chunks到Qdrant"""
        if not chunks:
            return

        # 生成向量
        texts = [chunk["text"] for chunk in chunks]
        embeddings = self.embedder.encode_texts(texts)

        # 上传到Qdrant
        self.qdrant.upsert_chunks(chunks, embeddings)
        self.stats["uploaded_chunks"] += len(chunks)

        logger.info(f"已上传: {self.stats['uploaded_chunks']}/{self.stats['total_chunks']} 个向量点")

    def print_summary(self) -> Any:
        """打印统计摘要"""
        logger.info("=" * 60)
        logger.info("📊 法律向量库更新统计")
        logger.info("=" * 60)
        logger.info(f"扫描文件总数: {self.stats['total_files']}")
        logger.info(f"成功解析: {self.stats['parsed_files']}")
        logger.info(f"解析失败: {self.stats['errors']}")
        logger.info(f"总分块数: {self.stats['total_chunks']}")
        logger.info(f"已上传: {self.stats['uploaded_chunks']}")
        logger.info(f"成功率: {self.stats['parsed_files']/self.stats['total_files']*100:.1f}%")
        logger.info("=" * 60)


# ==================== 主函数 ====================

def main() -> None:
    """主函数"""
    logger.info("╔══════════════════════════════════════════════════════════════╗")
    logger.info("║        统一法律向量库更新脚本 v1.0.0                        ║")
    logger.info("║        Unified Legal Vector Database Updater                 ║")
    logger.info("╚══════════════════════════════════════════════════════════════╝")
    logger.info("")

    # 创建更新器
    updater = UnifiedLegalVectorUpdater()

    # 扫描文件(只处理2024-12-01之后修改的文件)
    law_files = updater.scan_law_files(newer_than=datetime(2024, 12, 1))

    if not law_files:
        logger.info("未找到新的法律文件,退出")
        return

    # 处理文件
    logger.info(f"开始处理 {len(law_files)} 个法律文件...")
    updater.process_files(law_files)

    # 打印摘要
    updater.print_summary()

    logger.info("")
    logger.info("✅ 法律向量库更新完成!")


if __name__ == "__main__":
    main()
