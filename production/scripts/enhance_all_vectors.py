#!/usr/bin/env python3
"""
扩展向量增强到全部文档
Enhance All Vectors

将所有法律文档的向量进行增强优化

作者: Athena平台团队
创建时间: 2025-12-20
版本: v1.0.0
"""

from __future__ import annotations
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AllVectorsEnhancer:
    """全向量增强器"""

    def __init__(self):
        self.qdrant_url = "http://localhost:6333"
        self.batch_size = 50
        self.enhanced_count = 0
        self.start_time = time.time()

    def generate_enhanced_vector(self, text: str, title: str) -> list[float]:
        """生成增强向量"""
        # 法律专业词汇库（扩展版）
        legal_domains = {
            "民法基础": {
                "keywords": ["民法典", "民事", "合同", "侵权", "债权", "物权", "人格权", "婚姻", "继承", "收养"],
                "weight": 2.5,
                "vector_range": (0, 100)
            },
            "商法经济": {
                "keywords": ["公司", "企业", "破产", "保险", "票据", "证券", "银行", "投资", "贸易", "竞争"],
                "weight": 2.0,
                "vector_range": (100, 200)
            },
            "刑法规定": {
                "keywords": ["刑法", "犯罪", "刑罚", "罪名", "刑事责任", "故意", "过失", "正当防卫", "紧急避险"],
                "weight": 2.5,
                "vector_range": (200, 300)
            },
            "行政程序": {
                "keywords": ["行政", "行政处罚", "行政许可", "行政复议", "行政诉讼", "公务员", "政府采购"],
                "weight": 2.0,
                "vector_range": (300, 400)
            },
            "宪法权利": {
                "keywords": ["宪法", "公民", "国家机构", "基本权利", "基本义务", "选举", "言论自由"],
                "weight": 3.0,
                "vector_range": (400, 500)
            },
            "诉讼程序": {
                "keywords": ["诉讼", "审判", "证据", "执行", "仲裁", "调解", "管辖", "起诉", "上诉"],
                "weight": 2.0,
                "vector_range": (500, 600)
            },
            "知识产权": {
                "keywords": ["专利", "商标", "著作权", "版权", "商业秘密", "知识产权", "侵权责任"],
                "weight": 2.0,
                "vector_range": (600, 700)
            },
            "劳动保障": {
                "keywords": ["劳动", "工资", "工伤", "社会保险", "劳动合同", "工会", "就业", "失业"],
                "weight": 1.8,
                "vector_range": (700, 800)
            },
            "环境资源": {
                "keywords": ["环境", "保护", "污染", "资源", "能源", "气候", "生态", "可持续发展"],
                "weight": 1.8,
                "vector_range": (800, 900)
            }
        }

        vector = np.zeros(1024, dtype=np.float32)

        # 1. 基于法律领域的向量化
        combined_text = f"{title} {text}"
        for _domain, config in legal_domains.items():
            domain_score = sum(1 for kw in config["keywords"] if kw in combined_text)
            if domain_score > 0:
                start, end = config["vector_range"]
                # 在指定范围内分布权重
                for i in range(start, min(end, 1024)):
                    vector[i] += domain_score * config["weight"] / (end - start)

        # 2. 基于文本特征的向量化
        words = list(set(combined_text.split()))
        for i, word in enumerate(words[:800]):
            hash_val = abs(hash(word)) % 1024
            vector[hash_val] += 1.0

        # 3. 标题强化（前50个位置）
        title_words = title.split()
        for word in title_words:
            hash_val = abs(hash(word)) % 50
            vector[hash_val] += 3.0

        # 4. 法律结构特征
        structure_features = {
            "has_articles": "第" in text and "条" in text,
            "has_chapters": any(marker in text for marker in ["章", "节", "编"]),
            "is_law": "法" in title and "中华人民共和国" in text,
            "is_regulation": "条例" in title or "规定" in title,
            "is_interpretation": "解释" in title or "司法解释" in title,
            "article_count": text.count("第")
        }

        # 结构特征编码（900-910位置）
        vector[900] = 1.0 if structure_features["has_articles"] else 0.0
        vector[901] = 1.0 if structure_features["has_chapters"] else 0.0
        vector[902] = 1.0 if structure_features["is_law"] else 0.0
        vector[903] = 1.0 if structure_features["is_regulation"] else 0.0
        vector[904] = 1.0 if structure_features["is_interpretation"] else 0.0
        vector[905] = min(structure_features["article_count"] / 100.0, 1.0)

        # 5. 文档长度特征
        vector[910] = min(len(text) / 50000.0, 1.0)

        # 6. 时间相关特征（如果有日期）
        if any(year in text for year in ["2020", "2021", "2022", "2023", "2024", "2025"]):
            vector[911] = 1.0

        # 归一化
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        return vector.tolist()

    def get_remaining_points(self, collection_name: str) -> Any | None:
        """获取未增强的向量点"""
        # 获取所有点，过滤出未增强的
        response = requests.post(
            f"{self.qdrant_url}/collections/{collection_name}/points/scroll",
            json={
                "limit": 10000,  # 大批量获取
                "with_payload": True,
                "with_vector": False,
                "filter": {
                    "must_not": [
                        {"key": "enhanced", "match": {"value": True}}
                    ]
                }
            }
        )

        if response.status_code == 200:
            result = response.json().get('result', {})
            return result.get('points', [])
        return []

    def enhance_collection(self, collection_name: str) -> Any:
        """增强整个集合"""
        logger.info(f"\n🚀 增强集合: {collection_name}")

        # 获取未增强的点
        points = self.get_remaining_points(collection_name)

        if not points:
            logger.info(f"✅ {collection_name} 所有向量都已增强")
            return 0

        logger.info(f"📊 找到 {len(points)} 个未增强的向量")

        batch_count = 0
        collection_enhanced = 0

        # 分批处理
        for i in range(0, len(points), self.batch_size):
            batch = points[i:i+self.batch_size]
            batch_count += 1

            # 准备数据
            update_points = []
            for point in batch:
                payload = point.get('payload', {})
                title = payload.get('title', '')
                file_path = payload.get('file_path', '')

                # 读取内容
                content = ""
                try:
                    if Path(file_path).exists():
                        with open(file_path, encoding='utf-8') as f:
                            content = f.read()
                except Exception as e:
                    logger.debug(f"空except块已触发: {e}")
                    content = title  # 如果读取失败，只使用标题

                # 生成增强向量
                enhanced_vector = self.generate_enhanced_vector(content, title)

                update_point = {
                    "id": point["id"],
                    "vector": enhanced_vector,
                    "payload": {
                        **payload,
                        "enhanced": True,
                        "enhancement_version": "v3.0",
                        "enhanced_at": datetime.now().isoformat(),
                        "enhancement_method": "comprehensive_legal_domain"
                    }
                }
                update_points.append(update_point)

            # 批量更新
            response = requests.put(
                f"{self.qdrant_url}/collections/{collection_name}/points",
                json={"points": update_points}
            )

            if response.status_code == 200:
                collection_enhanced += len(update_points)
                self.enhanced_count += len(update_points)

                # 显示进度
                progress = (i + len(batch)) / len(points) * 100
                elapsed = time.time() - self.start_time
                eta = elapsed / (i + len(batch)) * (len(points) - i - len(batch))

                logger.info(
                    f"✓ 批次 {batch_count}: {len(update_points)} 个向量 "
                    f"({progress:.1f}%, ETA: {eta:.0f}s)"
                )
            else:
                logger.error(f"✗ 批次 {batch_count} 更新失败")

        logger.info(f"\n🎉 {collection_name} 增强完成: {collection_enhanced} 个向量")
        return collection_enhanced

    def show_progress_summary(self) -> Any:
        """显示进度摘要"""
        elapsed = time.time() - self.start_time

        logger.info("\n" + "="*100)
        logger.info("📊 增强进度摘要 📊")
        logger.info("="*100)
        logger.info(f"⏱️ 总耗时: {elapsed:.2f} 秒")
        logger.info(f"📈 增强向量数: {self.enhanced_count:,}")
        logger.info(f"⚡ 平均速度: {self.enhanced_count/elapsed:.1f} 向量/秒")

def main() -> None:
    """主函数"""
    print("="*100)
    print("📈 扩展向量增强到全部文档 📈")
    print("="*100)

    enhancer = AllVectorsEnhancer()

    # 获取所有集合
    response = requests.get(f"{enhancer.qdrant_url}/collections")
    if response.status_code != 200:
        logger.error("无法获取集合列表")
        return

    collections = response.json().get('result', {}).get('collections', [])

    # 增强每个集合
    for col in collections:
        collection_name = col["name"]
        if "legal" in collection_name and "1024" in collection_name:
            enhancer.enhance_collection(collection_name)

    # 显示摘要
    enhancer.show_progress_summary()

    print("\n✅ 所有向量增强完成！")

if __name__ == "__main__":
    main()
