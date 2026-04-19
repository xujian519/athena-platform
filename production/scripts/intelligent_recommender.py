#!/usr/bin/env python3
"""
智能推荐系统
Intelligent Recommender System

基于用户查询和历史行为的法律文档智能推荐

作者: Athena平台团队
创建时间: 2025-12-20
版本: v1.0.0
"""

from __future__ import annotations
import json
import logging
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Recommendation:
    """推荐结果"""
    id: str
    title: str
    score: float
    reason: str
    metadata: dict

class IntelligentRecommender:
    """智能推荐系统"""

    def __init__(self):
        self.qdrant_url = "http://localhost:6333"
        self.search_log_path = Path("/Users/xujian/Athena工作平台/production/data/metadata")
        self.recommendations_cache = {}

    def load_search_history(self, days: int = 7) -> list[dict]:
        """加载搜索历史"""
        history = []
        today = datetime.now()

        for i in range(days):
            date = today - timedelta(days=i)
            log_file = self.search_log_path / f"search_log_{date.strftime('%Y%m%d')}.json"

            if log_file.exists():
                with open(log_file, encoding='utf-8') as f:
                    day_history = json.load(f)
                    history.extend(day_history)

        return history

    def analyze_user_interests(self, history: list[dict]) -> dict:
        """分析用户兴趣"""
        # 提取关键词
        all_queries = [h['query'] for h in history]
        query_words = []
        for query in all_queries:
            query_words.extend(query.split())

        # 统计词频
        word_freq = Counter(query_words)

        # 法律领域分类
        legal_domains = {
            "民法": ["民法典", "民事", "合同", "侵权", "物权", "人格权", "婚姻", "继承"],
            "刑法": ["刑法", "犯罪", "刑罚", "罪名", "刑事责任"],
            "行政法": ["行政", "处罚", "许可", "复议", "诉讼"],
            "宪法": ["宪法", "公民", "权利", "义务"],
            "商法": ["公司", "企业", "破产", "保险", "证券"],
            "经济法": ["经济", "市场", "竞争", "消费者", "质量"],
            "诉讼法": ["诉讼", "审判", "证据", "执行", "仲裁"],
            "知识产权": ["专利", "商标", "著作权", "版权", "知识产权"]
        }

        # 计算领域兴趣度
        domain_scores = {}
        for domain, keywords in legal_domains.items():
            score = sum(word_freq.get(kw, 0) for kw in keywords)
            if score > 0:
                domain_scores[domain] = score

        # 归一化分数
        if domain_scores:
            max_score = max(domain_scores.values())
            domain_scores = {k: v/max_score for k, v in domain_scores.items()}

        return {
            "top_keywords": word_freq.most_common(10),
            "domain_interests": domain_scores,
            "total_searches": len(all_queries)
        }

    def find_similar_documents(self, doc_id: str, collection: str, limit: int = 5) -> list[dict]:
        """找到相似的文档"""
        # 获取文档向量
        response = requests.post(
            f"{self.qdrant_url}/collections/{collection}/points/search",
            json={
                "vector": {"vector": {"name": "image", "vector": [0.1] * 1024}},  # 需要实际向量
                "limit": limit + 1,  # 多获取一个排除自己
                "with_payload": True,
                "filter": {
                    "must_not": [
                        {"key": "id", "match": {"value": doc_id}}
                    ]
                }
            }
        )

        # 简化处理，返回模拟结果
        return []

    def generate_query_vector(self, query: str) -> list[float]:
        """生成查询向量（复用之前的方法）"""
        vector = np.zeros(1024, dtype=np.float32)
        words = query.split()

        for word in words:
            hash_val = abs(hash(word)) % 1024
            vector[hash_val] += 1.0

        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        return vector.tolist()

    def recommend_based_on_history(self, user_interests: dict) -> list[Recommendation]:
        """基于历史推荐的推荐"""
        recommendations = []
        collections = ["legal_articles_1024", "legal_judgments_1024"]

        # 为每个兴趣领域生成推荐
        for domain, score in user_interests.get('domain_interests', {}).items():
            if score > 0.3:  # 只推荐感兴趣的领域
                # 生成领域相关的查询
                domain_keywords = {
                    "民法": "民事权利义务关系",
                    "刑法": "犯罪构成要件",
                    "行政法": "行政行为程序",
                    "宪法": "公民基本权利",
                    "商法": "商事主体行为",
                    "经济法": "市场规则监管",
                    "诉讼法": "诉讼程序规则",
                    "知识产权": "知识产权保护"
                }

                query = domain_keywords.get(domain, domain)
                query_vector = self.generate_query_vector(query)

                # 搜索相关文档
                for collection in collections:
                    response = requests.post(
                        f"{self.qdrant_url}/collections/{collection}/points/search",
                        json={
                            "vector": query_vector,
                            "limit": 3,
                            "with_payload": True,
                            "score_threshold": 0.2
                        }
                    )

                    if response.status_code == 200:
                        results = response.json().get('result', [])
                        for item in results:
                            payload = item.get('payload', {})
                            recommendations.append(Recommendation(
                                id=item.get('id'),
                                title=payload.get('title', ''),
                                score=item.get('score', 0) * score,
                                reason=f"基于您对{domain}的兴趣",
                                metadata={
                                    "domain": domain,
                                    "source": collection,
                                    "confidence": score
                                }
                            ))

        # 排序并限制数量
        recommendations.sort(key=lambda x: x.score, reverse=True)
        return recommendations[:10]

    def recommend_trending_documents(self) -> list[Recommendation]:
        """推荐热门文档"""
        recommendations = []

        # 基于搜索频率推荐
        history = self.load_search_history(days=3)
        recent_queries = [h['query'] for h in history[-50:]]  # 最近50次搜索

        # 统计热门查询
        query_freq = Counter(recent_queries)
        hot_queries = query_freq.most_common(5)

        for query, freq in hot_queries:
            if freq >= 2:  # 至少被搜索2次
                query_vector = self.generate_query_vector(query)

                # 搜索相关文档
                response = requests.post(
                    f"{self.qdrant_url}/collections/legal_articles_1024/points/search",
                    json={
                        "vector": query_vector,
                        "limit": 2,
                        "with_payload": True,
                        "score_threshold": 0.3
                    }
                )

                if response.status_code == 200:
                    results = response.json().get('result', [])
                    for item in results:
                        payload = item.get('payload', {})
                        recommendations.append(Recommendation(
                            id=item.get('id'),
                            title=payload.get('title', ''),
                            score=item.get('score', 0) * (freq / 10),
                            reason=f"热门搜索：{query}（{freq}次）",
                            metadata={
                                "source": "trending",
                                "query": query,
                                "frequency": freq
                            }
                        ))

        # 排序
        recommendations.sort(key=lambda x: x.score, reverse=True)
        return recommendations[:5]

    def recommend_related_documents(self, doc_id: str, collection: str = None) -> list[Recommendation]:
        """推荐相关文档"""
        if not collection:
            collection = "legal_articles_1024"

        recommendations = []

        # 获取参考文档
        response = requests.post(
            f"{self.qdrant_url}/collections/{collection}/points/scroll",
            json={
                "filter": {"must": [{"key": "id", "match": {"value": doc_id}}]},
                "limit": 1,
                "with_payload": True
            }
        )

        if response.status_code == 200:
            points = response.json().get('result', {}).get('points', [])
            if points:
                doc = points[0]
                payload = doc.get('payload', {})
                title = payload.get('title', '')

                # 生成相关查询
                query_vector = self.generate_query_vector(title)

                # 搜索相似文档
                response = requests.post(
                    f"{self.qdrant_url}/collections/{collection}/points/search",
                    json={
                        "vector": query_vector,
                        "limit": 5,
                        "with_payload": True,
                        "score_threshold": 0.4,
                        "filter": {
                            "must_not": [
                                {"key": "id", "match": {"value": doc_id}}
                            ]
                        }
                    }
                )

                if response.status_code == 200:
                    results = response.json().get('result', [])
                    for item in results:
                        payload = item.get('payload', {})
                        recommendations.append(Recommendation(
                            id=item.get('id'),
                            title=payload.get('title', ''),
                            score=item.get('score', 0),
                            reason=f"与《{title[:30]}...》相关",
                            metadata={
                                "source": "similar",
                                "reference_doc": doc_id,
                                "similarity": item.get('score', 0)
                            }
                        ))

        return recommendations

    def generate_recommendations(self, user_id: str = "default", doc_id: str = None) -> dict:
        """生成综合推荐"""
        logger.info("\n🤖 生成智能推荐...")

        # 加载用户历史
        history = self.load_search_history(days=7)

        # 分析用户兴趣
        user_interests = self.analyze_user_interests(history)
        logger.info(f"  用户兴趣领域: {list(user_interests.get('domain_interests', {}).keys())}")

        all_recommendations = []

        # 1. 基于历史的推荐
        if history:
            history_recs = self.recommend_based_on_history(user_interests)
            all_recommendations.extend(history_recs)
            logger.info(f"  历史推荐: {len(history_recs)} 个")

        # 2. 热门推荐
        trending_recs = self.recommend_trending_documents()
        all_recommendations.extend(trending_recs)
        logger.info(f"  热门推荐: {len(trending_recs)} 个")

        # 3. 相关文档推荐（如果提供了文档ID）
        if doc_id:
            related_recs = self.recommend_related_documents(doc_id)
            all_recommendations.extend(related_recs)
            logger.info(f"  相关推荐: {len(related_recs)} 个")

        # 去重和排序
        seen_ids = set()
        unique_recs = []
        for rec in all_recommendations:
            if rec.id not in seen_ids:
                seen_ids.add(rec.id)
                unique_recs.append(rec)

        unique_recs.sort(key=lambda x: x.score, reverse=True)

        # 构建响应
        response = {
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "user_interests": user_interests,
            "total_recommendations": len(unique_recs),
            "recommendations": []
        }

        for rec in unique_recs[:20]:  # 最多返回20个
            response["recommendations"].append({
                "id": rec.id,
                "title": rec.title,
                "score": round(rec.score, 4),
                "reason": rec.reason,
                "metadata": rec.metadata
            })

        # 保存推荐记录
        self.save_recommendation_log(response)

        return response

    def save_recommendation_log(self, response: dict) -> None:
        """保存推荐日志"""
        log_path = self.search_log_path / f"recommendation_log_{datetime.now().strftime('%Y%m%d')}.json"

        logs = []
        if log_path.exists():
            with open(log_path, encoding='utf-8') as f:
                logs = json.load(f)

        # 添加新日志
        log_entry = {
            "user_id": response["user_id"],
            "timestamp": response["timestamp"],
            "interests": response["user_interests"].get('domain_interests', {}),
            "recommendation_count": response["total_recommendations"]
        }
        logs.append(log_entry)

        # 只保留最近50条
        logs = logs[-50:]

        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)

def main() -> None:
    """主函数 - 演示智能推荐"""
    print("="*100)
    print("🤖 智能推荐系统演示 🤖")
    print("="*100)

    recommender = IntelligentRecommender()

    # 生成推荐
    recommendations = recommender.generate_recommendations()

    print("\n📊 推荐统计:")
    print(f"  总推荐数: {recommendations['total_recommendations']}")
    print(f"  用户兴趣: {recommendations['user_interests']['domain_interests']}")

    print("\n📋 推荐文档:")
    for i, rec in enumerate(recommendations["recommendations"][:10]):
        print(f"\n{i+1}. {rec['title'][:60]}...")
        print(f"   推荐分数: {rec['score']}")
        print(f"   推荐理由: {rec['reason']}")

    # 相关文档推荐演示
    print("\n" + "="*80)
    print("相关文档推荐演示")
    print("="*80)

    # 假设用户正在查看某个文档
    related_recs = recommender.recommend_related_documents("sample_doc_001")
    if related_recs:
        print(f"\n相关文档推荐 ({len(related_recs)}个):")
        for i, rec in enumerate(related_recs):
            print(f"\n{i+1}. {rec['title'][:60]}...")
            print(f"   相似度: {rec['metadata']['similarity']:.3f}")

    print("\n✅ 智能推荐演示完成！")

if __name__ == "__main__":
    main()
