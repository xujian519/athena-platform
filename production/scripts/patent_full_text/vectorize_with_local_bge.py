#!/usr/bin/env python3
"""
专利向量化和知识图谱构建脚本 - 使用本地BGE模型
对成功提取的专利进行向量索引和知识图谱存储
"""

from __future__ import annotations
import json
import logging
import sys
from pathlib import Path
from typing import Any

# 设置路径
PROJECT_ROOT = Path("/Users/xujian/Athena工作平台")
PATENT_PROCESSED_DIR = PROJECT_ROOT / "apps/apps/patents" / "processed"
LOCAL_BGE_MODEL = PROJECT_ROOT / "models" / "BAAI/bge-m3"

sys.path.insert(0, str(PROJECT_ROOT / "production/dev/scripts/patent_full_text/phase3"))
sys.path.insert(0, str(PROJECT_ROOT))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LocalBGEEmbedding:
    """本地BGE模型加载器"""

    def __init__(self, model_path: str = None):
        """
        初始化本地BGE模型

        Args:
            model_path: 本地模型路径
        """
        if model_path is None:
            model_path = str(LOCAL_BGE_MODEL)

        self.model_path = Path(model_path)
        self.model = None

        if not self.model_path.exists():
            logger.warning(f"模型路径不存在: {self.model_path}")
            return

        logger.info(f"使用本地BGE模型: {self.model_path}")

    def load_model(self) -> Any | None:
        """加载本地模型"""
        if self.model is not None:
            return self.model

        try:
            from sentence_transformers import SentenceTransformer

            logger.info("正在加载本地BGE模型...")
            # 使用本地路径加载模型
            self.model = SentenceTransformer(str(self.model_path))
            logger.info("✅ BGE模型加载成功")
            logger.info(f"   向量维度: {self.model.get_sentence_embedding_dimension()}")

            return self.model

        except Exception as e:
            logger.error(f"❌ 加载BGE模型失败: {e}")
            logger.info("将使用简化向量作为后备方案")
            return None

    def encode(self, text: str) -> list:
        """
        对文本进行编码

        Args:
            text: 输入文本

        Returns:
            向量表示
        """
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

        # 创建1024维（BGE-M3）简化向量
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        vector = []
        for i in range(768):
            idx = i % len(text_hash)
            val = int(text_hash[idx], 16) / 15.0
            vector.append(val)

        return vector


def load_processed_patents() -> Any | None:
    """加载已处理的专利数据"""
    patent_files = list(PATENT_PROCESSED_DIR.glob("[A-Z]*.json"))
    patents = []

    for patent_file in patent_files:
        if "processing_report" in patent_file.name:
            continue

        try:
            with open(patent_file, encoding='utf-8') as f:
                patent_data = json.load(f)
                patents.append(patent_data)
                logger.info(f"加载: {patent_data['patent_number']} ({len(patent_data.get('full_text', ''))} 字符)")
        except Exception as e:
            logger.error(f"加载失败 {patent_file.name}: {e}")

    return patents


def vectorize_patent_with_local_model(embedder: LocalBGEEmbedding, text: str, patent_number: str) -> list:
    """
    使用本地BGE模型对专利文本进行向量化

    Args:
        embedder: 本地BGE嵌入模型
        text: 专利文本
        patent_number: 专利号

    Returns:
        向量表示
    """
    logger.info(f"  向量化: {patent_number}")

    # 使用摘要或前500字符进行向量化
    if len(text) > 500:
        text_to_encode = text[:500]
    else:
        text_to_encode = text

    vector = embedder.encode(text_to_encode)

    logger.info(f"  ✅ 向量维度: {len(vector)}")

    return vector


def save_to_qdrant_mock(patent_data: dict, vector: list) -> None:
    """模拟保存到Qdrant"""
    logger.info(f"  📊 Qdrant存储: {patent_data['patent_number']}")
    logger.info(f"    - 向量维度: {len(vector)}")
    logger.info(f"    - 文本长度: {len(patent_data.get('full_text', ''))}")


def save_to_nebula_mock(patent_data: dict) -> None:
    """模拟保存到NebulaGraph"""
    logger.info(f"  🕸️  NebulaGraph存储: {patent_data['patent_number']}")
    logger.info(f"    - 标题: {patent_data.get('title', '')[:50]}...")
    logger.info("    - 节点类型: Patent")


def process_single_patent(embedder: LocalBGEEmbedding, patent_data: dict) -> Any | None:
    """处理单个专利：向量化+知识图谱"""
    patent_number = patent_data['patent_number']
    full_text = patent_data.get('full_text', '')

    logger.info(f"\n处理专利: {patent_number}")
    logger.info("-" * 60)

    if not full_text:
        logger.warning("  ⚠️  无文本内容，跳过")
        return False

    # 1. 向量化
    logger.info("1️⃣  向量化处理（使用本地BGE模型）")
    vector = vectorize_patent_with_local_model(embedder, full_text, patent_number)

    # 2. 保存向量到Qdrant
    logger.info("\n2️⃣  向量存储")
    save_to_qdrant_mock(patent_data, vector)

    # 3. 知识图谱构建
    logger.info("\n3️⃣  知识图谱构建")
    save_to_nebula_mock(patent_data)

    logger.info(f"\n  ✅ {patent_number} 处理完成")

    return True


def main() -> None:
    """主流程"""
    logger.info("="*70)
    logger.info("专利向量化和知识图谱构建 - 使用本地BGE模型")
    logger.info("="*70)

    # 检查本地模型
    logger.info("\n检查本地BGE模型:")
    logger.info(f"  路径: {LOCAL_BGE_MODEL}")
    if LOCAL_BGE_MODEL.exists():
        logger.info("  ✅ 模型文件存在")
        config_file = LOCAL_BGE_MODEL / "config.json"
        if config_file.exists():
            logger.info("  ✅ 配置文件存在")
        model_file = LOCAL_BGE_MODEL / "model.safetensors"
        if model_file.exists():
            size_mb = model_file.stat().st_size / (1024 * 1024)
            logger.info(f"  ✅ 模型文件存在 ({size_mb:.1f} MB)")
    else:
        logger.warning("  ⚠️  模型文件不存在")

    # 初始化本地BGE模型
    embedder = LocalBGEEmbedding(str(LOCAL_BGE_MODEL))

    # 尝试预加载模型
    logger.info("\n预加载本地BGE模型...")
    embedder.load_model()

    # 加载已处理的专利
    patents = load_processed_patents()

    if not patents:
        logger.warning("没有找到已处理的专利数据")
        return

    logger.info(f"\n共 {len(patents)} 个专利待处理")

    # 处理每个专利
    success_count = 0
    for patent in patents:
        try:
            if process_single_patent(embedder, patent):
                success_count += 1
        except Exception as e:
            logger.error(f"处理失败 {patent['patent_number']}: {e}")

    # 总结
    logger.info("\n" + "="*70)
    logger.info("处理完成")
    logger.info("="*70)
    logger.info(f"成功: {success_count}/{len(patents)}")
    logger.info("")

    if embedder.model is not None:
        logger.info("✅ 使用本地BGE模型进行向量化")
        logger.info(f"   模型路径: {LOCAL_BGE_MODEL}")
        logger.info("   向量维度: 768")
    else:
        logger.info("⚠️  BGE模型加载失败，使用简化向量")
        logger.info("   请检查模型路径或网络连接")

    logger.info("")
    logger.info("💡 提示:")
    logger.info("   - 当前使用模拟存储，未实际写入Qdrant和NebulaGraph")
    logger.info("   - 要启用真实存储，请安装: pip install qdrant-client nebula3-python")


if __name__ == "__main__":
    main()
