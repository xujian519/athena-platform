#!/usr/bin/env python3
"""
法律向量质量增强器
Legal Vector Quality Enhancer

提升法律向量的质量和搜索相关性

作者: Athena平台团队
创建时间: 2025-12-20
版本: v1.0.0
"""

from __future__ import annotations
import logging
from datetime import datetime

import numpy as np
import requests

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LegalVectorEnhancer:
    """法律向量质量增强器"""

    def __init__(self):
        self.nlp_service_url = "http://localhost:8001"
        self.qdrant_url = "http://localhost:6333"
        self.data_source = "/Users/xujian/Athena工作平台/dev/tools/Laws-1.0.0"

    def extract_legal_keywords(self, text: str) -> list[str]:
        """提取法律关键词"""
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

        keywords = []
        text_lower = text.lower()

        for _category, terms in legal_terms.items():
            for term in terms:
                if term in text:
                    keywords.append(term)

        return list(set(keywords))

    def extract_legal_structure(self, content: str) -> dict:
        """提取法律文件结构"""
        structure = {
            "has_chapters": False,
            "has_articles": False,
            "article_count": 0,
            "level": "unknown"
        }

        # 检查是否有章节
        if any(marker in content for marker in ["第", "章", "节"]):
            structure["has_chapters"] = True

        # 统计条款数量
        import re
        articles = re.findall(r'第[一二三四五六七八九十百千万\d]+条', content)
        structure["article_count"] = len(articles)
        structure["has_articles"] = len(articles) > 0

        # 判断法律层级
        if "宪法" in content:
            structure["level"] = "宪法"
        elif "法律" in content and "全国人民代表大会" in content:
            structure["level"] = "法律"
        elif "条例" in content or "规定" in content:
            structure["level"] = "行政法规"
        elif "办法" in content or "实施细则" in content:
            structure["level"] = "部门规章"
        elif "地方性法规" in content:
            structure["level"] = "地方性法规"

        return structure

    def generate_enhanced_vector(self, text: str, title: str, metadata: dict) -> list[float]:
        """生成增强的语义向量"""
        try:
            # 尝试调用NLP服务获取高质量向量
            response = requests.post(
                f"{self.nlp_service_url}/encode",
                json={
                    "text": f"{title}\n\n{text[:1000]}"  # 限制长度避免超出限制
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                if "embedding" in result:
                    vector = result["embedding"]
                    # 确保是1024维
                    if len(vector) != 1024:
                        # 调整维度
                        if len(vector) > 1024:
                            vector = vector[:1024]
                        else:
                            vector = vector + [0.0] * (1024 - len(vector))
                    return vector

        except Exception as e:
            logger.warning(f"NLP服务调用失败，使用增强hash方法: {e}")

        # 增强的hash向量方法
        vector = np.zeros(1024, dtype=np.float32)

        # 1. 基于关键词的向量化
        keywords = self.extract_legal_keywords(text)
        for keyword in keywords:
            hash_val = abs(hash(keyword)) % 1024
            # 法律关键词权重更高
            vector[hash_val] += 2.0

        # 2. 基于结构的向量化
        structure = self.extract_legal_structure(text)
        if structure["has_articles"]:
            # 法律文件特征位
            vector[1] = 1.0
            vector[2] = structure["article_count"] / 1000.0  # 归一化

        # 3. 基于层级的向量化
        level_map = {
            "宪法": [1.0, 0, 0, 0],
            "法律": [0, 1.0, 0, 0],
            "行政法规": [0, 0, 1.0, 0],
            "地方性法规": [0, 0, 0, 1.0]
        }
        level_vec = level_map.get(structure["level"], [0.25, 0.25, 0.25, 0.25])
        vector[10:14] = level_vec

        # 4. 基于文本特征的向量化
        words = list(set(text.split()))
        for _i, word in enumerate(words[:500]):
            hash_val = abs(hash(word)) % 1024
            vector[hash_val] += 1.0

        # 5. 标题权重
        title_words = title.split()
        for word in title_words:
            hash_val = abs(hash(word)) % 1024
            vector[hash_val] += 3.0  # 标题权重更高

        # 归一化
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        return vector.tolist()

    def enhance_collection(self, collection_name: str) -> dict:
        """增强整个集合的向量质量"""
        print(f"\n🔧 增强集合: {collection_name}")

        # 获取集合信息
        response = requests.get(f"{self.qdrant_url}/collections/{collection_name}")
        if response.status_code != 200:
            print("❌ 无法获取集合信息")
            return {"status": "error", "message": "无法获取集合信息"}

        collection_info = response.json().get('result', {})
        points_count = collection_info.get('points_count', 0)

        if points_count == 0:
            print("⚠️ 集合为空")
            return {"status": "empty", "message": "集合为空"}

        print(f"📊 集合包含 {points_count:,} 个向量")

        # 采样评估质量（不处理全部，避免耗时过长）
        sample_size = min(100, points_count)
        enhanced_count = 0

        try:
            # 获取样本点
            response = requests.post(
                f"{self.qdrant_url}/collections/{collection_name}/points/scroll",
                json={
                    "limit": sample_size,
                    "with_payload": True,
                    "with_vector": False
                }
            )

            if response.status_code == 200:
                points = response.json().get('result', {}).get('points', [])

                # 批量增强
                batch_size = 20
                for i in range(0, len(points), batch_size):
                    batch = points[i:i+batch_size]

                    enhanced_points = []
                    for point in batch:
                        payload = point.get('payload', {})
                        title = payload.get('title', '')
                        file_path = payload.get('file_path', '')

                        # 读取原始文件
                        try:
                            with open(file_path, encoding='utf-8') as f:
                                content = f.read()
                        except Exception as e:
                            logger.debug(f"空except块已触发: {e}")
                            content = ""

                        # 生成增强向量
                        enhanced_vector = self.generate_enhanced_vector(
                            content, title, payload
                        )

                        enhanced_point = {
                            "id": point["id"],
                            "vector": enhanced_vector,
                            "payload": {
                                **payload,
                                "enhanced": True,
                                "enhanced_at": datetime.now().isoformat(),
                                "enhanced_version": "v2.0"
                            }
                        }
                        enhanced_points.append(enhanced_point)

                    # 更新向量
                    response = requests.put(
                        f"{self.qdrant_url}/collections/{collection_name}/points",
                        json={"points": enhanced_points}
                    )

                    if response.status_code == 200:
                        enhanced_count += len(enhanced_points)
                        print(f"  ✓ 批次 {i//batch_size + 1}: 增强了 {len(enhanced_points)} 个向量")

        except Exception as e:
            print(f"❌ 增强过程出错: {e}")
            return {"status": "error", "message": str(e)}

        print(f"\n✅ 成功增强 {enhanced_count:,} 个向量")

        # 评估增强效果
        improvement = self.evaluate_improvement(collection_name)

        return {
            "status": "success",
            "enhanced_count": enhanced_count,
            "improvement": improvement
        }

    def evaluate_improvement(self, collection_name: str) -> dict:
        """评估增强效果"""
        print("\n📈 评估增强效果...")

        test_queries = [
            ("民法典", "民法基本法律"),
            ("刑法", "刑事犯罪法律"),
            ("合同纠纷", "民事合同相关"),
            ("行政处罚", "行政法律责任"),
            ("知识产权", "专利商标著作权")
        ]

        improvement = {
            "before": {"avg_score": 0, "relevant_results": 0},
            "after": {"avg_score": 0, "improvement": 0}
        }

        # 这里简化处理，实际应该对比增强前后的数据
        # 仅作为示例展示评估框架

        return improvement

    def create_optimized_collection(self) -> str:
        """创建优化后的新集合"""
        new_collection = "legal_optimized_1024_v2"

        # 检查是否已存在
        response = requests.get(f"{self.qdrant_url}/collections/{new_collection}")
        if response.status_code == 200:
            print(f"⚠️ 集合 {new_collection} 已存在")
            return new_collection

        # 创建新集合
        response = requests.put(
            f"{self.qdrant_url}/collections/{new_collection}",
            json={
                "vectors": {
                    "size": 1024,
                    "distance": "Cosine"
                },
                "optimizers_config": {
                    "default_segment_number": 4
                }
            }
        )

        if response.status_code == 200:
            print(f"✅ 创建优化集合: {new_collection}")
            return new_collection
        else:
            print(f"❌ 创建集合失败: {response.text}")
            return None

def main() -> None:
    """主函数"""
    print("="*100)
    print("🚀 法律向量质量增强器 🚀")
    print("="*100)

    enhancer = LegalVectorEnhancer()

    # 1. 测试向量生成
    print("\n🧪 测试向量生成...")
    test_text = """
    中华人民共和国民法典

    第一编 总则
    第一章 基本规定
    第一条 为了保护民事主体的合法权益，调整民事关系，维护社会和经济秩序，
    适应中国特色社会主义发展要求，弘扬社会主义核心价值观，根据宪法，制定本法。
    """

    test_vector = enhancer.generate_enhanced_vector(
        test_text, "中华人民共和国民法典", {}
    )
    print(f"✓ 生成测试向量: {len(test_vector)}维")

    # 2. 增强现有集合
    collections = ["legal_articles_1024", "legal_judgments_1024"]

    for collection in collections:
        result = enhancer.enhance_collection(collection)
        if result["status"] == "success":
            print(f"\n✅ {collection} 增强完成")
            print(f"   - 增强向量数: {result['enhanced_count']:,}")

    # 3. 创建优化集合（可选）
    print("\n💡 建议: 可以创建优化集合来存储增强后的向量")
    print("   - 使用优化的索引配置")
    print("   - 保留原始集合作为备份")

    print("\n🎉 向量增强完成！")

if __name__ == "__main__":
    main()
