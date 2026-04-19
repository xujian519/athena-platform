#!/usr/bin/env python3
"""
法律向量库更新 - 稳定版本
使用更小的批次和更频繁的提交来避免错误
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
        logging.file_handler(project_root / 'logs' / 'legal_vector_update_stable.log'),
        logging.stream_handler()
    ]
)
logger = logging.getLogger(__name__)

# 第三方库导入
try:
    import numpy as np
    import torch
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, PointStruct, VectorParams
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    logger.error(f"缺少必要的依赖库: {e}")
    sys.exit(1)

# 配置参数
LAWS_CORPUS_DIR = Path("/Volumes/AthenaData/07_Corpus_Data/语料/Laws-1.0.0")
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "unified_legal_laws"
BGE_MODEL_PATH = "/Users/xujian/Athena工作平台/models/converted/BAAI/bge-m3"
BATCH_SIZE = 16  # 减小批次大小
CHUNK_MAX_LENGTH = 512
VECTOR_DIMENSION = 1024

# 确保日志目录存在
(project_root / 'logs').mkdir(parents=True, exist_ok=True)

def parse_law_file(file_path: Path) -> dict[str, Any | None]:
    """解析法律文件"""
    try:
        with open(file_path, encoding='utf-8') as f:
            content = f.read()

        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else file_path.stem

        date_pattern = r'(\d{4})[年\-](\d{1,2})[月\-](\d{1,2})[日\-]'
        dates = re.findall(date_pattern, content)
        date_str = f"{dates[0][0]}-{dates[0][1].zfill(2)}-{dates[0][2].zfill(2)}" if dates else None

        category_cn = file_path.parent.name

        content_body = re.sub(r'^#.*?$<!-- INFO END -->', '', content, flags=re.DOTALL)

        return {
            "title": title,
            "date": date_str,
            "category_cn": category_cn,
            "content": content_body.strip(),
            "file_path": str(file_path),
            "file_name": file_path.name
        }
    except Exception as e:
        logger.warning(f"解析文件失败 {file_path}: {e}")
        return None

def chunk_text(text: str, max_length: int = CHUNK_MAX_LENGTH) -> list[str]:
    """简单分块"""
    chunks = []
    current_chunk = ""

    sentences = re.split(r'([。！？；\n])', text)
    for sentence in sentences:
        if len(current_chunk) + len(sentence) > max_length and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = sentence
        else:
            current_chunk += sentence

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks

def main() -> None:
    logger.info("╔══════════════════════════════════════════════════════════════╗")
    logger.info("║        法律向量库更新 - 稳定版 (小批次)                  ║")
    logger.info("╚══════════════════════════════════════════════════════════════╝")

    # 扫描文件
    law_files = []
    for pattern in ["*.md", "*.txt"]:
        law_files.extend(LAWS_CORPUS_DIR.rglob(pattern))

    # 只处理2024-12-01之后的文件
    law_files = [f for f in law_files if datetime.fromtimestamp(f.stat().st_mtime) > datetime(2024, 12, 1)]
    logger.info(f"找到 {len(law_files)} 个新文件")

    # 初始化模型
    logger.info(f"加载BGE-M3模型: {BGE_MODEL_PATH}")
    device = 'mps' if torch.backends.mps.is_available() else 'cpu'
    logger.info(f"使用设备: {device}")

    model = SentenceTransformer(BGE_MODEL_PATH, device=device)
    logger.info(f"✅ 模型加载完成,向量维度: {VECTOR_DIMENSION}")

    # 初始化Qdrant
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    logger.info("✅ Qdrant连接成功")

    # 检查集合
    collections = client.get_collections().collections
    collection_names = [c.name for c in collections]

    if COLLECTION_NAME not in collection_names:
        logger.info(f"创建集合: {COLLECTION_NAME}")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=VECTOR_DIMENSION,
                distance=Distance.COSINE
            )
        )
    else:
        info = client.get_collection(COLLECTION_NAME)
        logger.info(f"集合已存在,当前点数: {info.points_count}")

    # 处理文件
    total_chunks = 0
    uploaded_chunks = 0
    errors = 0

    for file_idx, law_file in enumerate(law_files, 1):
        logger.info(f"[{file_idx}/{len(law_files)}] 处理: {law_file.name}")

        law_data = parse_law_file(law_file)
        if not law_data:
            errors += 1
            continue

        # 分块
        text_chunks = chunk_text(law_data["content"])
        logger.info(f"  分块: {len(text_chunks)} 个")

        # 逐个处理chunk
        for chunk_idx, text_chunk in enumerate(text_chunks):
            # 生成向量
            embedding = model.encode(text_chunk, normalize_embeddings=True)

            # 验证向量
            if np.isnan(embedding).any() or np.isinf(embedding).any():
                logger.warning(f"  跳过无效向量 (chunk {chunk_idx})")
                continue

            # 生成ID
            content_id = f"{law_file.name}_{chunk_idx}"
            point_id = int(hashlib.md5(content_id.encode('utf-8'), usedforsecurity=False).hexdigest()[:16], 16)

            # 创建payload
            payload = {
                "text": text_chunk[:10000],
                "law_title": law_data["title"],
                "law_date": law_data["date"] or "",
                "law_category_cn": law_data["category_cn"],
                "chunk_index": chunk_idx,
                "file_path": law_data["file_path"],
                "updated_at": datetime.now().isoformat()
            }

            # 插入向量点 (逐个插入,避免批量错误)
            try:
                point = PointStruct(
                    id=point_id,
                    vector=embedding.astype(np.float32).tolist(),
                    payload=payload
                )

                client.upsert(
                    collection_name=COLLECTION_NAME,
                    points=[point],
                    wait=True
                )

                uploaded_chunks += 1
                total_chunks += 1

                if uploaded_chunks % 10 == 0:
                    logger.info(f"  已上传: {uploaded_chunks} 个向量点")

            except Exception as e:
                logger.error(f"  插入失败 (chunk {chunk_idx}): {e}")
                errors += 1

    # 最终统计
    logger.info("=" * 60)
    logger.info("📊 处理完成统计")
    logger.info("=" * 60)
    logger.info(f"总文件数: {len(law_files)}")
    logger.info(f"成功解析: {len(law_files) - errors}")
    logger.info(f"解析失败: {errors}")
    logger.info(f"已上传向量点: {uploaded_chunks}")
    logger.info("=" * 60)

    # 检查最终集合状态
    final_info = client.get_collection(COLLECTION_NAME)
    logger.info(f"✅ 集合最终点数: {final_info.points_count}")
    logger.info("✅ 法律向量库更新完成!")

if __name__ == "__main__":
    main()
