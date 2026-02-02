#!/usr/bin/env python3
"""
删除22维简化向量集合
Delete 22-dim Simple Vectors Collection

作者: 小诺·双鱼公主
创建时间: 2024年12月15日
"""

import logging
from qdrant_client import QdrantClient

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def delete_simple_vectors():
    """删除22维简化向量集合"""

    # 连接Qdrant
    client = QdrantClient(host="localhost", port=6333)

    collection_name = "patent_legal_vectors_simple"

    try:
        # 检查集合是否存在
        collections = client.get_collections().collections
        collection_names = [c.name for c in collections]

        if collection_name in collection_names:
            # 获取集合信息
            info = client.get_collection(collection_name)
            logger.info(f"找到集合: {collection_name}")
            logger.info(f"  向量数量: {info.points_count}")
            logger.info(f"  向量维度: {info.config.params.vectors.size}")

            # 确认删除
            print(f"\n确认要删除集合 '{collection_name}' 吗？")
            print(f"  - 向量数量: {info.points_count}")
            print(f"  - 向量维度: {info.config.params.vectors.size}")

            # 删除集合
            client.delete_collection(collection_name)
            logger.info(f"✅ 成功删除集合: {collection_name}")

            # 验证删除
            collections_after = client.get_collections().collections
            collection_names_after = [c.name for c in collections_after]

            if collection_name not in collection_names_after:
                print(f"\n✅ 验证成功: 集合 '{collection_name}' 已被删除")
            else:
                print(f"\n❌ 警告: 集合可能未完全删除")

        else:
            logger.info(f"集合 '{collection_name}' 不存在")

    except Exception as e:
        logger.error(f"删除集合失败: {e}")
        return False

    return True

def show_remaining_collections():
    """显示剩余的集合"""
    client = QdrantClient(host="localhost", port=6333)

    print("\n" + "="*60)
    print("📊 Qdrant中剩余的集合:")
    print("="*60)

    try:
        collections = client.get_collections().collections

        if not collections:
            print("  没有找到任何集合")
            return

        for collection in collections:
            info = client.get_collection(collection.name)
            print(f"\n📁 {collection.name}")
            print(f"   向量数量: {info.points_count}")
            print(f"   向量维度: {info.config.params.vectors.size}")
            print(f"   距离度量: {info.config.params.vectors.distance}")

    except Exception as e:
        logger.error(f"获取集合列表失败: {e}")

def main():
    """主函数"""
    print("🗑️ 删除22维简化向量集合")
    print("="*60)

    # 显示当前集合
    show_remaining_collections()

    # 删除简化向量集合
    if delete_simple_vectors():
        print("\n✅ 操作完成！")

        # 显示删除后的集合
        print("\n删除后的集合状态:")
        show_remaining_collections()
    else:
        print("\n❌ 删除失败！")

if __name__ == "__main__":
    main()