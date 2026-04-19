#!/usr/bin/env python3
"""
条款级向量化系统
Article-Level Vectorization System

对法律法规的每个条款进行精确向量化

作者: Athena平台团队
创建时间: 2025-12-20
版本: v1.0.0
"""

from __future__ import annotations
import json
import logging
import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import requests

# 使用安全哈希函数替代不安全的MD5/SHA1
from production.utils.security_helpers import short_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ArticleVector:
    """条款向量"""
    article_id: str
    vector: list[float]
    metadata: dict

class ArticleLevelVectorizer:
    """条款级向量化器"""

    def __init__(self):
        self.qdrant_url = "http://localhost:6333"
        self.batch_size = 100

        # 法律领域特征权重
        self.domain_weights = {
            "民法": 2.5,
            "刑法": 2.5,
            "行政法": 2.0,
            "宪法": 3.0,
            "商法": 2.0,
            "经济法": 1.8,
            "诉讼法": 2.0,
            "劳动法": 1.8,
            "知识产权": 2.0
        }

        # 条款类型关键词
        self.article_types = {
            "定义条款": ["定义", "是指", "包括", "本法所称"],
            "义务条款": ["应当", "必须", "有义务", "应负"],
            "权利条款": ["有权", "可以", "享有", "权利"],
            "禁止条款": ["不得", "禁止", "不准", "严禁"],
            "处罚条款": ["处罚", "罚款", "没收", "责令"],
            "程序条款": ["申请", "审批", "备案", "登记"],
            "责任条款": ["责任", "赔偿", "补偿", "承担"],
            "期限条款": ["期限", "时限", "日内", "个月内"]
        }

    def load_analyzed_data(self) -> dict:
        """加载已分析的法律数据"""
        analysis_file = Path("/Users/xujian/Athena工作平台/production/output/analysis") / \
                       "legal_structure_analysis_20251220_212658.json"

        if not analysis_file.exists():
            logger.error("找不到分析结果文件")
            return {}

        with open(analysis_file, encoding='utf-8') as f:
            return json.load(f)

    def generate_article_vector(self, article: dict) -> list[float]:
        """为单个条款生成向量"""
        vector = np.zeros(1024, dtype=np.float32)

        # 1. 条款编号特征（0-99）
        article_num = self.chinese_to_number(article.get('article_number', ''))
        if article_num:
            # 将条款编号映射到向量空间
            vector[article_num % 100] = 1.0

        # 2. 条款类型特征（100-199）
        content = f"{article.get('title', '')} {article.get('content', '')}"
        for article_type, keywords in self.article_types.items():
            if any(kw in content for kw in keywords):
                idx = 100 + hash(article_type) % 100
                vector[idx] = 1.0

        # 3. 法律领域特征（200-399）
        domain = self.identify_legal_domain(content)
        if domain:
            start = 200
            for d in self.domain_weights.keys():
                if d == domain:
                    vector[start:start+25] = self.domain_weights[d] / 10
                start += 25

        # 4. 关键词特征（400-799）
        keywords = self.extract_legal_keywords(content)
        for keyword in keywords:
            hash_val = abs(hash(keyword)) % 400
            vector[400 + hash_val] += 1.0

        # 5. 条款长度特征（800）
        vector[800] = min(len(content) / 1000.0, 1.0)

        # 6. 章节特征（801-899）
        chapter = article.get('chapter', '')
        section = article.get('section', '')
        if chapter:
            vector[801] = 1.0
        if section:
            vector[802] = 1.0

        # 7. 义务权利平衡特征（900-909）
        obligations = sum(1 for kw in ["应当", "必须", "有义务"] if kw in content)
        rights = sum(1 for kw in ["有权", "可以", "享有"] if kw in content)
        if obligations > 0:
            vector[900] = obligations / (obligations + rights) if (obligations + rights) > 0 else 0
        if rights > 0:
            vector[901] = rights / (obligations + rights) if (obligations + rights) > 0 else 0

        # 8. 条款关系特征（910-919）
        if any(word in content for word in ["根据", "依据", "按照"]):
            vector[910] = 1.0  # 引用其他条款
        if any(word in content for word in ["修改", "修订", "调整"]):
            vector[911] = 1.0  # 修改性条款
        if any(word in content for word in ["废止", "取消", "失效"]):
            vector[912] = 1.0  # 废止性条款

        # 归一化
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        return vector.tolist()

    def chinese_to_number(self, chinese_str: str) -> int:
        """将中文数字转换为阿拉伯数字"""
        chinese_map = {
            '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
            '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
            '百': 100, '千': 1000, '万': 10000
        }

        result = 0
        temp = 0
        for char in chinese_str:
            if char in chinese_map:
                if char in ['十', '百', '千', '万']:
                    if temp == 0:
                        temp = 1
                    result += temp * chinese_map[char]
                    temp = 0
                else:
                    temp = chinese_map[char]

        return result + temp

    def identify_legal_domain(self, text: str) -> str | None:
        """识别法律领域"""
        domain_keywords = {
            "民法": ["民事", "合同", "侵权", "物权", "债权", "人格权", "婚姻", "继承"],
            "刑法": ["犯罪", "刑罚", "刑事责任", "故意", "过失", "正当防卫"],
            "行政法": ["行政", "行政处罚", "行政许可", "行政复议", "行政诉讼"],
            "宪法": ["宪法", "公民", "基本权利", "基本义务", "国家机构"],
            "商法": ["公司", "企业", "破产", "保险", "票据", "证券"],
            "经济法": ["市场", "竞争", "消费者", "产品质量", "价格"],
            "诉讼法": ["诉讼", "审判", "证据", "执行", "仲裁", "管辖"],
            "劳动法": ["劳动", "工资", "工伤", "劳动合同", "社会保险"],
            "知识产权": ["专利", "商标", "著作权", "版权", "知识产权"]
        }

        scores = {}
        for domain, keywords in domain_keywords.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scores[domain] = score

        return max(scores, key=scores.get) if scores else None

    def extract_legal_keywords(self, text: str) -> list[str]:
        """提取法律关键词"""
        legal_terms = [
            # 基础概念
            "权利", "义务", "责任", "赔偿", "补偿", "承担", "履行", "违反",
            # 行为规范
            "应当", "必须", "可以", "有权", "不得", "禁止", "严禁", "不准",
            # 程序
            "申请", "审批", "备案", "登记", "公告", "通知", "送达", "执行",
            # 法律后果
            "处罚", "罚款", "没收", "责令", "撤销", "吊销", "注销", "无效",
            # 时间相关
            "期限", "时效", "之日起", "日内", "个月内", "年内", "立即",
            # 主体
            "公民", "法人", "组织", "机构", "部门", "单位", "个人", "当事人"
        ]

        found_keywords = []
        for term in legal_terms:
            if term in text:
                found_keywords.append(term)

        # 提取特定模式
        patterns = [
            r'(\d+元)',
            r'(\d+%)',
            r'([一二三四五六七八九十]+年以上)',
            r'(依法追究.+责任)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            found_keywords.extend(matches)

        return found_keywords[:20]  # 最多返回20个

    def create_article_collection(self) -> bool:
        """创建条款级向量集合"""
        collection_name = "legal_articles_v3_1024"

        # 检查是否已存在
        response = requests.get(f"{self.qdrant_url}/collections/{collection_name}")
        if response.status_code == 200:
            logger.info(f"集合 {collection_name} 已存在")
            return True

        # 创建新集合
        create_payload = {
            "vectors": {
                "size": 1024,
                "distance": "Cosine"
            },
            "optimizers_config": {
                "default_segment_number": 4,
                "max_segment_size": 200000,
                "memmap_threshold": 50000
            },
            "quantization_config": {
                "scalar": {
                    "type": "int8",
                    "quantile": 0.99
                }
            }
        }

        response = requests.put(
            f"{self.qdrant_url}/collections/{collection_name}",
            json=create_payload
        )

        if response.status_code == 200:
            logger.info(f"✅ 成功创建集合: {collection_name}")
            return True
        else:
            logger.error(f"❌ 创建集合失败: {response.text}")
            return False

    def process_all_articles(self) -> Any | None:
        """处理所有条款的向量化"""
        logger.info("\n🚀 开始条款级向量化...")

        # 加载分析数据
        data = self.load_analyzed_data()
        if not data:
            return

        # 创建集合
        if not self.create_article_collection():
            return

        collection_name = "legal_articles_v3_1024"
        total_articles = 0
        processed = 0

        # 收集所有条款
        all_articles = []
        for result in data.get("reports/reports/results", []):
            if "articles" in result:
                for article in result["articles"]:
                    # 添加元数据
                    article["file_title"] = result.get("title", "")
                    article["file_path"] = result.get("file_path", "")
                    all_articles.append(article)

        total_articles = len(all_articles)
        logger.info(f"📊 找到 {total_articles} 个条款")

        # 批量处理
        for i in range(0, total_articles, self.batch_size):
            batch = all_articles[i:i+self.batch_size]
            batch_num = i // self.batch_size + 1

            logger.info(f"\n处理批次 {batch_num}/{(total_articles-1)//self.batch_size + 1}")

            # 生成向量
            points = []
            for article in batch:
                vector = self.generate_article_vector(article)

                # 总是生成新的UUID格式的ID
                content_str = f"{article.get('file_title', '')}_{article.get('article_number', '')}_{article['title'][:100]}"
                content_hash = short_hash(content_str.encode())
                article_id = str(uuid.UUID(content_hash))

                point = {
                    "id": article_id,
                    "vector": vector,
                    "payload": {
                        "article_number": article.get("article_number", ""),
                        "title": article.get("title", ""),
                        "content": article.get("content", ""),
                        "chapter": article.get("chapter", ""),
                        "section": article.get("section", ""),
                        "keywords": article.get("keywords", []),
                        "file_title": article.get("file_title", ""),
                        "file_path": article.get("file_path", ""),
                        "vectorization_version": "v3.0",
                        "vectorization_timestamp": datetime.now().isoformat()
                    }
                }
                points.append(point)

            # 上传到Qdrant
            try:
                response = requests.put(
                    f"{self.qdrant_url}/collections/{collection_name}/points",
                    json={"points": points}
                )

                if response.status_code == 200:
                    processed += len(points)
                    logger.info(f"✅ 批次 {batch_num}: 成功处理 {len(points)} 个条款")
                    logger.info(f"   进度: {processed}/{total_articles} ({processed/total_articles*100:.1f}%)")
                else:
                    logger.error(f"❌ 批次 {batch_num} 失败: {response.text}")

            except Exception as e:
                logger.error(f"❌ 批次 {batch_num} 异常: {e}")

        # 验证结果
        self.verify_vectorization(collection_name, total_articles)

        logger.info("\n✅ 条款级向量化完成！")
        logger.info(f"   总条款数: {total_articles}")
        logger.info(f"   处理成功: {processed}")

    def verify_vectorization(self, collection_name: str, expected_count: int) -> bool:
        """验证向量化结果"""
        logger.info("\n🔍 验证向量化结果...")

        response = requests.get(f"{self.qdrant_url}/collections/{collection_name}")
        if response.status_code == 200:
            collection_info = response.json().get("result", {})
            points_count = collection_info.get("points_count", 0)
            vectors_count = collection_info.get("vectors_count", 0)

            logger.info(f"  集合名称: {collection_name}")
            logger.info(f"  向量点数: {points_count:,}")
            logger.info(f"  向量数量: {vectors_count:,}")
            logger.info(f"  预期数量: {expected_count:,}")

            if points_count == expected_count:
                logger.info("  ✅ 数量匹配")
            else:
                logger.warning("  ⚠️ 数量不匹配")

        # 测试搜索
        logger.info("\n🧪 测试搜索功能...")
        test_vector = np.random.rand(1024).tolist()

        search_response = requests.post(
            f"{self.qdrant_url}/collections/{collection_name}/points/search",
            json={
                "vector": test_vector,
                "limit": 3,
                "with_payload": True
            }
        )

        if search_response.status_code == 200:
            results = search_response.json().get("result", [])
            logger.info(f"  搜索返回: {len(results)} 个结果")
            if results:
                for i, result in enumerate(results):
                    payload = result.get("payload", {})
                    logger.info(f"    {i+1}. {payload.get('article_number', '')}条 "
                               f"- {payload.get('title', '')[:50]}...")

def main() -> None:
    """主函数"""
    print("="*100)
    print("📚 条款级向量化系统 📚")
    print("="*100)

    vectorizer = ArticleLevelVectorizer()
    vectorizer.process_all_articles()

if __name__ == "__main__":
    main()
