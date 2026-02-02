#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用REST API将专利审查指南向量导入Qdrant
"""

import json
import requests
import logging
import time
from typing import List, Dict

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class QdrantImporter:
    """Qdrant向量导入器"""

    def __init__(self, host="localhost", port=6333):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.collection_name = "patent_guideline"

    def check_qdrant_status(self) -> bool:
        """检查Qdrant服务状态"""
        try:
            response = requests.get(f"{self.base_url}/collections", timeout=5)
            if response.status_code == 200:
                logger.info("✅ Qdrant服务运行正常")
                return True
            else:
                logger.error(f"❌ Qdrant服务异常: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            logger.error("❌ 无法连接到Qdrant服务")
            logger.info(f"请确保Qdrant在 {self.base_url} 运行")
            return False
        except Exception as e:
            logger.error(f"❌ 检查失败: {e}")
            return False

    def create_collection(self) -> bool:
        """创建集合"""
        try:
            # 检查集合是否存在
            response = requests.get(f"{self.base_url}/collections/{self.collection_name}")
            if response.status_code == 200:
                logger.info(f"✅ 集合 {self.collection_name} 已存在")
                return True

            # 创建新集合
            collection_config = {
                "vectors": {
                    "size": 768,
                    "distance": "Cosine"
                }
            }

            response = requests.put(
                f"{self.base_url}/collections/{self.collection_name}",
                json=collection_config
            )

            if response.status_code == 200:
                logger.info(f"✅ 成功创建集合: {self.collection_name}")
                return True
            else:
                logger.error(f"❌ 创建集合失败: {response.text}")
                return False

        except Exception as e:
            logger.error(f"❌ 创建集合异常: {e}")
            return False

    def load_vectors(self, file_path: str) -> List[Dict]:
        """加载向量数据"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            vectors = data.get("vectors", [])
            logger.info(f"✅ 加载向量数据: {len(vectors)} 个")
            return vectors

        except Exception as e:
            logger.error(f"❌ 加载向量失败: {e}")
            return []

    def upload_vectors(self, vectors: List[Dict], batch_size: int = 100) -> bool:
        """批量上传向量"""
        if not vectors:
            logger.error("❌ 没有向量数据可上传")
            return False

        total = len(vectors)
        logger.info(f"📤 开始上传 {total} 个向量...")

        # 分批上传
        for i in range(0, total, batch_size):
            batch = vectors[i:i+batch_size]

            # 转换为Qdrant格式
            points = []
            for i, item in enumerate(batch):
                # 将字符串ID转换为数字ID
                id_value = hash(item["id"]) & 0xFFFFFFFF  # 转换为32位正整数
                point = {
                    "id": id_value,
                    "vector": item["vector"],
                    "payload": {
                        "original_id": item["id"],  # 保留原始ID
                        **item.get("payload", {})
                    }
                }
                points.append(point)

            # 上传批次
            try:
                response = requests.put(
                    f"{self.base_url}/collections/{self.collection_name}/points",
                    json={"points": points}
                )

                if response.status_code == 200:
                    batch_num = i // batch_size + 1
                    total_batches = (total - 1) // batch_size + 1
                    logger.info(f"✅ 批次 {batch_num}/{total_batches} 上传成功")
                else:
                    logger.error(f"❌ 批次上传失败: {response.text}")
                    return False

                # 避免过快请求
                time.sleep(0.1)

            except Exception as e:
                logger.error(f"❌ 上传批次异常: {e}")
                return False

        logger.info(f"✅ 所有向量上传完成！")
        return True

    def verify_upload(self) -> bool:
        """验证上传结果"""
        try:
            response = requests.get(f"{self.base_url}/collections/{self.collection_name}")
            if response.status_code == 200:
                collection_info = response.json()
                points_count = collection_info["result"]["points_count"]
                logger.info(f"✅ 集合中向量总数: {points_count}")
                return True
            else:
                logger.error(f"❌ 获取集合信息失败: {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ 验证失败: {e}")
            return False

    def run(self, vectors_file: str):
        """执行导入流程"""
        logger.info("🚀 开始导入专利审查指南向量到Qdrant...")
        print("\n" + "="*60)
        print("Qdrant 向量导入工具")
        print("="*60)

        # 1. 检查服务状态
        if not self.check_qdrant_status():
            logger.error("\n❌ Qdrant服务未运行，请先启动Qdrant")
            logger.info("启动命令: docker run -p 6333:6333 qdrant/qdrant")
            return False

        # 2. 创建集合
        if not self.create_collection():
            logger.error("\n❌ 创建集合失败")
            return False

        # 3. 加载向量
        vectors = self.load_vectors(vectors_file)
        if not vectors:
            logger.error("\n❌ 无法加载向量数据")
            return False

        # 4. 上传向量
        if not self.upload_vectors(vectors):
            logger.error("\n❌ 向量上传失败")
            return False

        # 5. 验证结果
        if not self.verify_upload():
            logger.error("\n❌ 验证失败")
            return False

        # 6. 完成
        print("\n" + "="*60)
        print("✅ 导入完成！")
        print("="*60)
        print(f"\n📊 导入统计:")
        print(f"  集合名称: {self.collection_name}")
        print(f"  向量维度: 768")
        print(f"  距离度量: Cosine")
        print(f"  导入数量: {len(vectors)}")
        print(f"\n🔗 访问方式:")
        print(f"  REST API: http://localhost:6333")
        print(f"  Web UI: http://localhost:6333/dashboard")
        print("\n💡 使用示例:")
        print(f"  - 查询相似内容: POST /collections/{self.collection_name}/search")
        print("="*60)

        return True

def main():
    """主函数"""
    importer = QdrantImporter()

    # 向量文件路径
    vectors_file = "/Users/xujian/Athena工作平台/data/guideline_vectors/patent_guideline_vectors.json"

    # 执行导入
    success = importer.run(vectors_file)

    if not success:
        logger.error("\n❌ 导入失败，请检查错误信息")
        exit(1)

if __name__ == "__main__":
    main()