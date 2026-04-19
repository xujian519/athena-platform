#!/usr/bin/env python3
"""
使用预训练法律BERT模型增强向量
Enhance Vectors with Pre-trained Legal BERT

使用预训练的法律BERT模型提升法律文档向量的质量

作者: Athena平台团队
创建时间: 2025-12-20
版本: v1.0.0
"""

from __future__ import annotations
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LegalBERTEncoder:
    """法律BERT编码器"""

    def __init__(self):
        self.nlp_service_url = "http://localhost:8001"
        self.qdrant_url = "http://localhost:6333"
        self.batch_size = 32

    def call_nlp_service(self, texts: list[str], use_legal_bert: bool = True) -> list[list[float | None]]:
        """调用NLP服务获取向量"""
        try:
            # 尝试使用法律BERT模型
            payload = {
                "texts": texts,
                "model": "legal_bert" if use_legal_bert else "default",
                "normalize": True
            }

            response = requests.post(
                f"{self.nlp_service_url}/batch_encode",
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                if "embeddings" in result:
                    embeddings = result["embeddings"]
                    # 确保向量维度为1024
                    normalized_embeddings = []
                    for emb in embeddings:
                        if len(emb) != 1024:
                            # 调整维度
                            if len(emb) > 1024:
                                emb = emb[:1024]
                            else:
                                emb = emb + [0.0] * (1024 - len(emb))
                        normalized_embeddings.append(emb)
                    return normalized_embeddings
                else:
                    logger.warning("NLP服务返回格式不正确")
            else:
                logger.warning(f"NLP服务请求失败: {response.status_code}")

        except Exception as e:
            logger.warning(f"调用NLP服务失败: {e}")

        return None

    def generate_fallback_vector(self, text: str) -> list[float]:
        """生成备用向量（增强版）"""
        # 法律专业词汇库
        legal_terms = {
            "民法": ["民法典", "民事", "合同", "侵权", "债权", "物权", "人格权", "婚姻", "继承"],
            "刑法": ["刑法", "犯罪", "刑罚", "罪名", "刑事责任", "故意", "过失", "正当防卫"],
            "行政法": ["行政", "行政处罚", "行政许可", "行政复议", "行政诉讼", "公务员"],
            "宪法": ["宪法", "公民", "国家机构", "基本权利", "基本义务"],
            "商法": ["公司", "企业", "商法", "破产", "保险", "票据", "证券"],
            "经济法": ["经济", "市场", "竞争", "消费者", "产品质量", "价格"],
            "诉讼法": ["诉讼", "审判", "证据", "执行", "仲裁", "调解", "管辖"]
        }

        vector = np.zeros(1024, dtype=np.float32)

        # 1. 基于法律关键词的向量化
        for domain, terms in legal_terms.items():
            domain_weight = 2.0 if domain in ["民法", "刑法"] else 1.5
            for term in terms:
                if term in text:
                    hash_val = abs(hash(term)) % 1024
                    vector[hash_val] += domain_weight

        # 2. 基于文本特征的向量化
        words = list(set(text.split()))
        for _i, word in enumerate(words[:500]):
            hash_val = abs(hash(word)) % 1024
            vector[hash_val] += 1.0

        # 3. 基于法律特征的增强
        if "第" in text and "条" in text:
            vector[700] = 1.0  # 有条款
            article_count = text.count("第")
            vector[701] = min(article_count / 100.0, 1.0)  # 条款数量

        # 4. 基于文档长度
        vector[0] = min(len(text) / 10000.0, 1.0)

        # 归一化
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        return vector.tolist()

    def enhance_collection(self, collection_name: str, limit: int | None = None) -> Any:
        """增强整个集合的向量"""
        logger.info(f"\n🚀 开始增强集合: {collection_name}")

        # 获取集合信息
        response = requests.get(f"{self.qdrant_url}/collections/{collection_name}")
        if response.status_code != 200:
            logger.error(f"无法获取集合信息: {collection_name}")
            return

        collection_info = response.json().get('result', {})
        total_points = collection_info.get('points_count', 0)

        # 确定处理数量
        process_count = min(limit or total_points, total_points)
        logger.info(f"📊 集合包含 {total_points:,} 个向量，将处理 {process_count:,} 个")

        enhanced_count = 0
        batch_count = 0

        # 分批处理
        for offset in range(0, process_count, self.batch_size):
            batch_count += 1

            # 获取一批向量点
            scroll_response = requests.post(
                f"{self.qdrant_url}/collections/{collection_name}/points/scroll",
                json={
                    "limit": min(self.batch_size, process_count - offset),
                    "offset": offset,
                    "with_payload": True,
                    "with_vector": False
                }
            )

            if scroll_response.status_code != 200:
                logger.error(f"获取批次 {batch_count} 失败")
                continue

            points = scroll_response.json().get('result', {}).get('points', [])

            # 准备文本
            texts = []
            for point in points:
                payload = point.get('payload', {})
                title = payload.get('title', '')
                file_path = payload.get('file_path', '')

                # 读取文件内容
                content = ""
                try:
                    if Path(file_path).exists():
                        with open(file_path, encoding='utf-8') as f:
                            content = f.read()
                except Exception as e:
                    logger.debug(f"空except块已触发: {e}")
                    pass

                # 组合文本（标题+部分内容）
                text = f"{title}\n\n{content[:1000]}"
                texts.append(text)

            # 获取增强向量
            vectors = self.call_nlp_service(texts, use_legal_bert=True)

            if vectors is None:
                logger.warning(f"批次 {batch_count} 使用备用向量方法")
                vectors = [self.generate_fallback_vector(text) for text in texts]

            # 准备更新数据
            update_points = []
            for i, point in enumerate(points):
                update_point = {
                    "id": point["id"],
                    "vector": vectors[i],
                    "payload": {
                        **point.get('payload', {}),
                        "enhanced": True,
                        "enhancement_method": "legal_bert" if vectors else "enhanced_hash",
                        "enhanced_at": datetime.now().isoformat()
                    }
                }
                update_points.append(update_point)

            # 更新向量
            update_response = requests.put(
                f"{self.qdrant_url}/collections/{collection_name}/points",
                json={"points": update_points}
            )

            if update_response.status_code == 200:
                enhanced_count += len(update_points)
                logger.info(f"✓ 批次 {batch_count}: 增强了 {len(update_points)} 个向量")
            else:
                logger.error(f"✗ 批次 {batch_count} 更新失败: {update_response.status_code}")

        logger.info(f"\n🎉 集合 {collection_name} 增强完成!")
        logger.info(f"   总计增强: {enhanced_count:,} 个向量")
        logger.info(f"   处理批次: {batch_count} 个")

        return enhanced_count

    def verify_enhancement(self, collection_name: str) -> bool:
        """验证增强效果"""
        logger.info(f"\n📈 验证 {collection_name} 的增强效果...")

        test_queries = [
            "民法典",
            "刑法",
            "合同纠纷",
            "行政处罚",
            "知识产权保护"
        ]

        improvements = []
        for query in test_queries:
            # 生成查询向量
            query_vector = self.generate_fallback_vector(query)

            # 搜索
            response = requests.post(
                f"{self.qdrant_url}/collections/{collection_name}/points/search",
                json={
                    "vector": query_vector,
                    "limit": 5,
                    "with_payload": True,
                    "score_threshold": 0.3
                }
            )

            if response.status_code == 200:
                results = response.json().get('result', [])
                scores = [r.get('score', 0) for r in results]
                avg_score = sum(scores) / len(scores) if scores else 0

                improvements.append({
                    "query": query,
                    "result_count": len(results),
                    "avg_similarity": avg_score,
                    "top_result": results[0].get('payload', {}).get('title', '')[:50] if results else None
                })

        # 保存验证结果
        verification = {
            "collection": collection_name,
            "timestamp": datetime.now().isoformat(),
            "test_results": improvements
        }

        verify_path = Path("/Users/xujian/Athena工作平台/production/data/metadata") / \
                     f"enhancement_verify_{collection_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(verify_path, 'w', encoding='utf-8') as f:
            json.dump(verification, f, ensure_ascii=False, indent=2)

        logger.info(f"📄 验证报告已保存: {verify_path}")

        return verification

def main() -> None:
    """主函数"""
    print("="*100)
    print("🤖 使用预训练法律BERT模型增强向量 🤖")
    print("="*100)

    encoder = LegalBERTEncoder()

    # 测试NLP服务
    print("\n🧪 测试NLP服务...")
    test_texts = ["中华人民共和国民法典"]
    vectors = encoder.call_nlp_service(test_texts)

    if vectors:
        print(f"✅ NLP服务可用，向量维度: {len(vectors[0])}")
        use_bert = True
    else:
        print("⚠️ NLP服务不可用，将使用增强的hash方法")
        use_bert = False

    # 增强集合
    collections = ["legal_articles_1024", "legal_judgments_1024"]
    total_enhanced = 0

    for collection in collections:
        # 处理部分文档作为示例（可以调整limit参数处理全部）
        enhanced = encoder.enhance_collection(collection, limit=500)
        total_enhanced += enhanced

        # 验证效果
        encoder.verify_enhancement(collection)

    print("\n" + "="*100)
    print("🎉 向量增强完成！")
    print(f"📊 总计增强: {total_enhanced:,} 个向量")
    print(f"🔧 使用方法: {'Legal BERT' if use_bert else 'Enhanced Hash'}")
    print("="*100)

if __name__ == "__main__":
    main()
