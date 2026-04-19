#!/usr/bin/env python3
"""
专利向量化脚本 - 保存向量数据
Patent Vectorization with Vector Storage

将处理好的专利文本转换为BGE向量并保存
"""

from __future__ import annotations
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

# 设置路径
PROJECT_ROOT = Path("/Users/xujian/Athena工作平台")
PATENT_PROCESSED_DIR = PROJECT_ROOT / "apps/apps/patents" / "processed"
LOCAL_BGE_MODEL = PROJECT_ROOT / "models" / "BAAI/bge-m3"
VECTOR_OUTPUT_DIR = PATENT_PROCESSED_DIR / "vectors"

sys.path.insert(0, str(PROJECT_ROOT / "production/dev/scripts/patent_full_text"))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LocalBGEEmbedding:
    """本地BGE模型加载器"""

    def __init__(self, model_path: str = None):
        if model_path is None:
            model_path = str(LOCAL_BGE_MODEL)
        self.model_path = Path(model_path)
        self.model = None

    def load_model(self) -> Any | None:
        """加载本地模型"""
        if self.model is not None:
            return self.model

        try:
            from sentence_transformers import SentenceTransformer

            logger.info("正在加载本地BGE模型...")
            self.model = SentenceTransformer(str(self.model_path))
            logger.info("✅ BGE模型加载成功")
            logger.info(f"   向量维度: {self.model.get_sentence_embedding_dimension()}")
            return self.model

        except Exception as e:
            logger.error(f"❌ 加载BGE模型失败: {e}")
            logger.info("将使用简化向量作为后备方案")
            return None

    def encode(self, text: str) -> list:
        """对文本进行编码"""
        if self.model is None:
            self.load_model()

        if self.model is not None:
            # 截断过长的文本
            if len(text) > 512:
                text = text[:512]

            embedding = self.model.encode(text)
            return embedding.tolist()

        # 如果模型加载失败，使用简化向量
        return self._get_fallback_vector(text)

    def _get_fallback_vector(self, text: str) -> list:
        """获取后备向量（基于hash）"""
        import hashlib
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        vector = []
        for i in range(768):
            idx = i % len(text_hash)
            val = int(text_hash[idx], 16) / 15.0
            vector.append(val)
        return vector


def load_processed_patents() -> list[dict]:
    """加载已处理的专利数据"""
    patent_files = list(PATENT_PROCESSED_DIR.glob("[A-Z]*.json"))
    patents = []

    for patent_file in patent_files:
        if "processing_report" in patent_file.name:
            continue

        try:
            with open(patent_file, encoding='utf-8') as f:
                patent_data = json.load(f)

                # 只处理有足够文本的专利
                if patent_data.get('text_length', 0) > 100:
                    patents.append(patent_data)
                    logger.info(f"加载: {patent_data['patent_number']} ({patent_data['text_length']} 字符)")
        except Exception as e:
            logger.error(f"加载失败 {patent_file.name}: {e}")

    return patents


def vectorize_patent(
    embedder: LocalBGEEmbedding,
    text: str,
    patent_number: str
) -> dict:
    """
    使用本地BGE模型对专利文本进行向量化

    Returns:
        包含向量和元数据的字典
    """
    logger.info(f"  向量化: {patent_number}")

    # 使用摘要或前500字符进行向量化
    if len(text) > 500:
        text_to_encode = text[:500]
    else:
        text_to_encode = text

    vector = embedder.encode(text_to_encode)

    return {
        'patent_number': patent_number,
        'vector': vector,
        'vector_dim': len(vector),
        'text_length': len(text),
        'encoded_length': len(text_to_encode)
    }


def save_vectors(vectors: list[dict], output_dir: Path) -> None:
    """保存向量数据"""
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. 保存为JSON格式
    json_file = output_dir / "patent_vectors.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(vectors, f, ensure_ascii=False, indent=2)
    logger.info(f"  💾 JSON格式: {json_file}")

    # 2. 保存为NumPy格式（更高效）
    npy_file = output_dir / "patent_vectors.npy"
    vector_matrix = np.array([v['vector'] for v in vectors])
    np.save(npy_file, vector_matrix)
    logger.info(f"  💾 NumPy格式: {npy_file}")

    # 3. 保存元数据
    metadata = {
        'timestamp': datetime.now().isoformat(),
        'total_patents': len(vectors),
        'vector_dim': vectors[0]['vector_dim'] if vectors else 0,
        'patent_numbers': [v['patent_number'] for v in vectors],
        'text_lengths': [v['text_length'] for v in vectors]
    }

    meta_file = output_dir / "metadata.json"
    with open(meta_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    logger.info(f"  💾 元数据: {meta_file}")

    # 4. 保存统计信息
    stats = {
        'total_patents': len(vectors),
        'vector_dim': vectors[0]['vector_dim'] if vectors else 0,
        'total_text_length': sum(v['text_length'] for v in vectors),
        'avg_text_length': sum(v['text_length'] for v in vectors) / len(vectors) if vectors else 0,
        'avg_encoded_length': sum(v['encoded_length'] for v in vectors) / len(vectors) if vectors else 0
    }

    stats_file = output_dir / "statistics.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    logger.info(f"  💾 统计信息: {stats_file}")


def main() -> None:
    """主流程"""
    logger.info("="*70)
    logger.info("专利向量化 - 保存向量数据")
    logger.info("="*70)

    # 检查本地模型
    logger.info("\n检查本地BGE模型:")
    logger.info(f"  路径: {LOCAL_BGE_MODEL}")
    if LOCAL_BGE_MODEL.exists():
        logger.info("  ✅ 模型文件存在")
    else:
        logger.warning("  ⚠️  模型文件不存在")

    # 初始化本地BGE模型
    embedder = LocalBGEEmbedding(str(LOCAL_BGE_MODEL))
    logger.info("\n预加载本地BGE模型...")
    embedder.load_model()

    # 加载已处理的专利
    patents = load_processed_patents()

    if not patents:
        logger.warning("没有找到已处理的专利数据")
        return

    logger.info(f"\n共 {len(patents)} 个专利待向量化")

    # 向量化每个专利
    vectors = []
    for patent in patents:
        patent_number = patent['patent_number']
        full_text = patent.get('full_text', '')

        if not full_text:
            logger.warning(f"  ⚠️ {patent_number} 无文本内容，跳过")
            continue

        try:
            vector_data = vectorize_patent(embedder, full_text, patent_number)
            vectors.append(vector_data)
            logger.info(f"  ✅ 向量维度: {vector_data['vector_dim']}")
        except Exception as e:
            logger.error(f"  ❌ {patent_number} 向量化失败: {e}")

    # 保存向量
    if vectors:
        logger.info("\n保存向量数据...")
        save_vectors(vectors, VECTOR_OUTPUT_DIR)

        # 打印总结
        logger.info("\n" + "="*70)
        logger.info("向量化完成")
        logger.info("="*70)
        logger.info(f"成功: {len(vectors)}/{len(patents)}")
        logger.info("向量维度: 768")
        logger.info(f"输出目录: {VECTOR_OUTPUT_DIR}")
        logger.info("")

        if embedder.model is not None:
            logger.info("✅ 使用本地BGE模型进行向量化")
            logger.info(f"   模型路径: {LOCAL_BGE_MODEL}")
        else:
            logger.info("⚠️  使用简化向量")

        # 打印统计信息
        total_text = sum(v['text_length'] for v in vectors)
        avg_text = total_text / len(vectors) if vectors else 0

        logger.info("")
        logger.info("📊 统计信息:")
        logger.info(f"   总文本量: {total_text:,} 字符")
        logger.info(f"   平均文本: {avg_text:,.0f} 字符/专利")
        logger.info(f"   向量总数: {len(vectors)}")
        logger.info(f"   数据大小: {len(vectors) * 768 * 4 / 1024:.1f} KB (原始)")
    else:
        logger.warning("没有成功的向量化结果")


if __name__ == "__main__":
    main()
