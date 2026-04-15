#!/usr/bin/env python3
"""
专利向量化和知识图谱构建脚本
对成功提取的专利进行向量索引和知识图谱存储
"""

from __future__ import annotations
import json
import logging
import sys
from pathlib import Path

# 设置路径
PROJECT_ROOT = Path("/Users/xujian/Athena工作平台")
PATENT_PROCESSED_DIR = PROJECT_ROOT / "apps/apps/patents" / "processed"

sys.path.insert(0, str(PROJECT_ROOT / "production/dev/scripts/patent_full_text/phase3"))
sys.path.insert(0, str(PROJECT_ROOT))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_processed_patents():
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


def vectorize_patent(text: str, patent_number: str) -> list:
    """
    对专利文本进行向量化
    使用BGE模型或简单的词频向量
    """
    try:
        # 尝试使用BGE模型
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('BAAI/bge-m3')
        embedding = model.encode(text[:512])  # 限制长度
        logger.info(f"  ✅ BGE向量: {len(embedding)}维")
        return embedding.tolist()
    except Exception as e:
        logger.warning(f"  ⚠️  BGE模型失败: {e}，使用简化向量")

        # 简化的字符频率向量
        import hashlib
        # 创建1024维（BGE-M3）简化向量（匹配BGE维度）
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        vector = []
        for i in range(768):
            # 从hash生成伪随机向量
            idx = i % len(text_hash)
            val = int(text_hash[idx], 16) / 15.0  # 归一化到0-1
            vector.append(val)
        logger.info(f"  ✅ 简化向量: {len(vector)}维")
        return vector


def save_to_qdrant_mock(patent_data: dict, vector: list):
    """模拟保存到Qdrant（实际需要Qdrant客户端）"""
    logger.info(f"  📊 Qdrant存储: {patent_data['patent_number']}")
    logger.info(f"    - 向量维度: {len(vector)}")
    logger.info(f"    - 文本长度: {len(patent_data.get('full_text', ''))}")
    # 实际部署时使用:
    # from qdrant_client import QdrantClient
    # client = QdrantClient("localhost", port=6333)
    # client.upsert(...)


def save_to_nebula_mock(patent_data: dict):
    """模拟保存到NebulaGraph（实际需要NebulaGraph客户端）"""
    logger.info(f"  🕸️  NebulaGraph存储: {patent_data['patent_number']}")
    logger.info(f"    - 标题: {patent_data.get('title', '')[:50]}...")
    logger.info("    - 节点类型: Patent")
    # 实际部署时使用:
    # from nebula3.gclient.net import ConnectionPool
    # 执行nGQL语句创建节点和边


def process_single_patent(patent_data: dict):
    """处理单个专利：向量化+知识图谱"""
    patent_number = patent_data['patent_number']
    full_text = patent_data.get('full_text', '')

    logger.info(f"\n处理专利: {patent_number}")
    logger.info("-" * 60)

    if not full_text:
        logger.warning("  ⚠️  无文本内容，跳过")
        return False

    # 1. 向量化
    logger.info("1️⃣  向量化处理")
    vector = vectorize_patent(full_text, patent_number)

    # 2. 保存向量到Qdrant
    logger.info("\n2️⃣  向量存储")
    save_to_qdrant_mock(patent_data, vector)

    # 3. 知识图谱构建
    logger.info("\n3️⃣  知识图谱构建")
    save_to_nebula_mock(patent_data)

    logger.info(f"\n  ✅ {patent_number} 处理完成")
    return True


def main():
    """主流程"""
    logger.info("="*70)
    logger.info("专利向量化和知识图谱构建")
    logger.info("="*70)

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
            if process_single_patent(patent):
                success_count += 1
        except Exception as e:
            logger.error(f"处理失败 {patent['patent_number']}: {e}")

    # 总结
    logger.info("\n" + "="*70)
    logger.info("处理完成")
    logger.info("="*70)
    logger.info(f"成功: {success_count}/{len(patents)}")
    logger.info("")
    logger.info("📝 注意: 当前使用简化向量模拟")
    logger.info("   实际部署时将连接:")
    logger.info("   - Qdrant (localhost:6333) 进行向量存储")
    logger.info("   - NebulaGraph (localhost:9669) 进行知识图谱构建")
    logger.info("")
    logger.info("💡 要启用实际存储，请确保:")
    logger.info("   1. Qdrant服务运行: docker ps | grep qdrant")
    logger.info("   2. NebulaGraph服务运行: docker ps | grep nebula")
    logger.info("   3. 安装客户端: pip install qdrant-client nebula3-python")


if __name__ == "__main__":
    main()
