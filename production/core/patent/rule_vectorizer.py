#!/usr/bin/env python3
"""
专利规则向量化器
Patent Rule Vectorizer

为专利规则知识图谱提供专业的向量化、存储和检索能力
"""

from __future__ import annotations
import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from core.async_main import async_main
from core.logging_config import setup_logging

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    import numpy as np
    from qdrant_client import QdrantClient, models
    from qdrant_client.http import models as rest
    from sentence_transformers import SentenceTransformer
    QDRANT_AVAILABLE = True
except ImportError:
    print("⚠️ qdrant-client或sentence-transformers未安装")
    QDRANT_AVAILABLE = False

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

class PatentRuleVectorizer:
    """专利规则向量化器"""

    def __init__(self):
        self.qdrant_client = None
        self.embedding_model = None
        self.patent_rules = {}
        self.rule_categories = {}
        self.technical_terms = set()

        # 专利规则分类体系
        self.rule_categories = {
            "novelty": {
                "name": "新颖性规则",
                "description": "关于专利新颖性判断的规则",
                "keywords": ["新颖性", "现有技术", "公开", "抵触申请", "不丧失新颖性"]
            },
            "inventiveness": {
                "name": "创造性规则",
                "description": "关于专利创造性判断的规则",
                "keywords": ["创造性", "进步性", "实质性特点", "显著进步", "组合发明"]
            },
            "utility": {
                "name": "实用性规则",
                "description": "关于专利实用性判断的规则",
                "keywords": ["实用性", "产业应用", "技术方案", "可实施性", "积极效果"]
            },
            "sufficiency": {
                "name": "公开充分规则",
                "description": "关于专利说明书公开充分的规则",
                "keywords": ["公开充分", "清楚完整", "实现", "技术方案", "所属领域技术人员"]
            },
            "patentability": {
                "name": "可专利性规则",
                "description": "关于专利客体和授权条件的规则",
                "keywords": ["专利客体", "授权条件", "排除情形", "科学发现", "智力活动规则"]
            },
            "procedure": {
                "name": "程序规则",
                "description": "关于专利申请和审查程序的规则",
                "keywords": ["申请程序", "审查程序", "修改程序", "驳回程序", "复审程序"]
            }
        }

        # 初始化组件
        self._init_qdrant_client()
        self._init_embedding_model()
        self._load_patent_vocabulary()

    def _init_qdrant_client(self):
        """初始化Qdrant客户端"""
        if not QDRANT_AVAILABLE:
            logger.error("❌ Qdrant库不可用")
            return

        try:
            self.qdrant_client = QdrantClient(host='localhost', port=6333)
            logger.info("✅ Qdrant客户端连接成功")
        except Exception as e:
            logger.error(f"❌ Qdrant客户端连接失败: {e}")
            self.qdrant_client = None

    def _init_embedding_model(self):
        """初始化嵌入模型"""
        if not QDRANT_AVAILABLE:
            logger.warning("⚠️ 向量服务不可用,跳过模型初始化")
            return

        try:
            # 尝试加载本地BGE模型
            model_path = "/Users/xujian/Athena工作平台/models/BAAI/bge-m3"
            if Path(model_path).exists():
                self.embedding_model = SentenceTransformer(model_path)
                logger.info("✅ 本地BGE嵌入模型加载成功")
            else:
                # 使用在线模型
                self.embedding_model = SentenceTransformer('BAAI/BAAI/bge-m3')
                logger.info("✅ 在线BGE嵌入模型加载成功")
        except Exception as e:
            logger.error(f"❌ 嵌入模型初始化失败: {e}")
            self.embedding_model = None

    def _load_patent_vocabulary(self):
        """加载专利词汇表"""
        try:
            # 技术术语
            self.technical_terms = {
                # 专利类型
                "发明专利", "实用新型专利", "外观设计专利", "发明", "实用新型", "外观设计",

                # 专利要素
                "权利要求", "说明书", "摘要", "附图", "技术方案", "技术特征", "技术问题",
                "技术效果", "实施方式", "具体实施方式", "优选实施方式",

                # 申请和审查
                "专利申请", "申请日", "公开日", "授权日", "优先权", "优先权日", "国际申请",
                "PCT申请", "发明专利申请", "实用新型专利申请",

                # 审查程序
                "初步审查", "实质审查", "驳回", "授权", "公告", "复审", "无效", "终止",
                "放弃", "恢复", "撤回", "修改",

                # 法律概念
                "专利权", "专利侵权", "专利许可", "专利转让", "专利实施", "专利保护期",
                "专利保护范围", "临时保护",

                # 技术领域
                "技术领域", "背景技术", "现有技术", "对比文件", "引证文件",

                # 创新概念
                "创新点", "发明点", "技术进步", "技术突破", "技术创新", "技术改进",
                "优化方案", "替代方案"
            }

            # 扩展专业术语
            technical_terms_file = Path(__file__).parent.parent / "data" / "patent_technical_terms.json"
            if technical_terms_file.exists():
                with open(technical_terms_file, encoding='utf-8') as f:
                    additional_terms = json.load(f).get("terms", [])
                    self.technical_terms.update(additional_terms)
                logger.info(f"✅ 加载专利技术术语: {len(self.technical_terms)}个")

        except Exception as e:
            logger.error(f"❌ 加载专利词汇表失败: {e}")

    async def initialize_collections(self):
        """初始化向量集合"""
        if not self.qdrant_client:
            logger.error("❌ Qdrant客户端不可用")
            return False

        try:
            # 获取现有集合
            collections = self.qdrant_client.get_collections()
            logger.info(f"📊 当前Qdrant集合数量: {len(collections.collections)}")

            # 创建专利规则相关集合
            patent_collections = {
                "patent_rules_main": {
                    "description": "专利规则主向量库",
                    "vector_size": 1024,
                    "distance": "Cosine"
                },
                "patent_rules_novelty": {
                    "description": "新颖性规则向量库",
                    "vector_size": 1024,
                    "distance": "Cosine"
                },
                "patent_rules_inventiveness": {
                    "description": "创造性规则向量库",
                    "vector_size": 1024,
                    "distance": "Cosine"
                },
                "patent_rules_utility": {
                    "description": "实用性规则向量库",
                    "vector_size": 1024,
                    "distance": "Cosine"
                },
                "patent_rules_procedure": {
                    "description": "程序规则向量库",
                    "vector_size": 1024,
                    "distance": "Cosine"
                }
            }

            for collection_name, config in patent_collections.items():
                await self._ensure_collection(collection_name, config)

            logger.info("✅ 专利规则向量集合初始化完成")
            return True

        except Exception as e:
            logger.error(f"❌ 向量集合初始化失败: {e}")
            return False

    async def _ensure_collection(self, collection_name: str, config: dict):
        """确保向量集合存在"""
        try:
            # 检查集合是否存在
            try:
                self.qdrant_client.get_collection(collection_name)
                logger.info(f"📊 集合 {collection_name} 已存在")
                return
            except Exception as e:
                logger.warning(f'操作失败: {e}')

            # 创建新集合
            self.qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=config["vector_size"],
                    distance=models.Distance.COSINE
                )
            )

            # 创建索引
            self.qdrant_client.create_payload_index(
                collection_name=collection_name,
                field_name="category",
                field_schema=models.PayloadSchemaType.KEYWORD
            )

            self.qdrant_client.create_payload_index(
                collection_name=collection_name,
                field_name="rule_id",
                field_schema=models.PayloadSchemaType.KEYWORD
            )

            self.qdrant_client.create_payload_index(
                collection_name=collection_name,
                field_name="keywords",
                field_schema=models.PayloadSchemaType.KEYWORD_ARRAY
            )

            logger.info(f"✅ 创建集合 {collection_name} ({config['description']})")

        except Exception as e:
            logger.error(f"❌ 创建集合 {collection_name} 失败: {e}")

    async def vectorize_patent_rule(self, rule_data: dict[str, Any]) -> dict[str, Any] | None:
        """向量化专利规则"""
        if self.embedding_model is None:
            logger.warning("⚠️ 嵌入模型未初始化")
            return None

        try:
            # 提取规则内容
            rule_id = rule_data.get("rule_id", f"rule_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            rule_content = rule_data.get("content", "")
            rule_category = rule_data.get("category", "")
            rule_title = rule_data.get("title", "")

            # 多角度文本构建
            texts_to_embed = []

            # 1. 规则标题(如果有)
            if rule_title:
                texts_to_embed.append(f"规则标题: {rule_title}")

            # 2. 规则内容
            if rule_content:
                texts_to_embed.append(f"规则内容: {rule_content}")

            # 3. 技术术语增强
            technical_terms_in_rule = self._extract_technical_terms(rule_content)
            if technical_terms_in_rule:
                terms_text = "技术术语: " + " ".join(technical_terms_in_rule)
                texts_to_embed.append(terms_text)

            # 4. 分类标签
            if rule_category:
                category_text = f"规则分类: {rule_category}"
                texts_to_embed.append(category_text)

            # 5. 关键词增强
            keywords = rule_data.get("keywords", [])
            if keywords:
                keywords_text = "关键词: " + " ".join(keywords)
                texts_to_embed.append(keywords_text)

            if not texts_to_embed:
                logger.warning(f"⚠️ 规则 {rule_id} 没有可供向量化的内容")
                return None

            # 生成多角度向量
            vectors = []
            for text in texts_to_embed:
                vector = self.embedding_model.encode(text)
                vector = vector / np.linalg.norm(vector)  # 归一化
                vectors.append(vector.astype(np.float32))

            # 智能融合向量
            if len(vectors) == 1:
                final_vector = vectors[0]
            else:
                # 加权平均融合
                weights = [0.3, 0.4, 0.1, 0.1, 0.1]  # 标题、内容、术语、分类、关键词
                if len(vectors) < len(weights):
                    weights = weights[:len(vectors)]

                final_vector = np.average(vectors[:len(weights)], axis=0, weights=weights)
                final_vector = final_vector / np.linalg.norm(final_vector)  # 再次归一化

            # 构建向量化结果
            vectorization_result = {
                "rule_id": rule_id,
                "title": rule_title,
                "content": rule_content,
                "category": rule_category,
                "keywords": keywords,
                "technical_terms": technical_terms_in_rule,
                "vector": final_vector.tolist(),
                "vector_dimension": len(final_vector),
                "timestamp": datetime.now().isoformat(),
                "source": rule_data.get("source", "manual"),
                "confidence": self._calculate_vector_confidence(rule_data)
            }

            logger.info(f"✅ 专利规则 {rule_id} 向量化完成,维度: {len(final_vector)}")
            return vectorization_result

        except Exception as e:
            logger.error(f"❌ 专利规则向量化失败: {e}")
            return None

    def _extract_technical_terms(self, text: str) -> list[str]:
        """提取技术术语"""
        if not text:
            return []

        found_terms = []
        text_lower = text.lower()

        for term in self.technical_terms:
            if term in text or term.lower() in text_lower:
                found_terms.append(term)

        return found_terms

    def _calculate_vector_confidence(self, rule_data: dict[str, Any]) -> float:
        """计算向量化置信度"""
        confidence = 0.0

        # 内容完整性 (30%)
        if rule_data.get("content"):
            confidence += 0.3

        # 标题存在性 (20%)
        if rule_data.get("title"):
            confidence += 0.2

        # 分类明确性 (20%)
        if rule_data.get("category") in self.rule_categories:
            confidence += 0.2

        # 关键词丰富性 (15%)
        keywords = rule_data.get("keywords", [])
        if len(keywords) >= 3:
            confidence += 0.15
        elif len(keywords) >= 1:
            confidence += 0.1

        # 技术术语覆盖 (15%)
        content = rule_data.get("content", "")
        technical_terms_count = len(self._extract_technical_terms(content))
        if technical_terms_count >= 5:
            confidence += 0.15
        elif technical_terms_count >= 2:
            confidence += 0.1
        elif technical_terms_count >= 1:
            confidence += 0.05

        return min(confidence, 1.0)

    async def store_vectorized_rule(self, vector_data: dict[str, Any]) -> bool:
        """存储向量化规则到向量数据库"""
        if not self.qdrant_client or not vector_data:
            return False

        try:
            rule_id = vector_data["rule_id"]
            category = vector_data["category"]

            # 确定目标集合
            target_collection = self._get_target_collection(category)

            # 准备payload
            payload = {
                "rule_id": rule_id,
                "title": vector_data.get("title", ""),
                "content": vector_data.get("content", ""),
                "category": category,
                "keywords": vector_data.get("keywords", []),
                "technical_terms": vector_data.get("technical_terms", []),
                "confidence": vector_data.get("confidence", 0.0),
                "source": vector_data.get("source", ""),
                "timestamp": vector_data.get("timestamp", datetime.now().isoformat())
            }

            # 存储到向量数据库
            self.qdrant_client.upsert(
                collection_name=target_collection,
                points=[
                    models.PointStruct(
                        id=rule_id,
                        vector=vector_data["vector"],
                        payload=payload
                    )
                ]
            )

            logger.info(f"✅ 专利规则 {rule_id} 已存储到集合 {target_collection}")
            return True

        except Exception as e:
            logger.error(f"❌ 存储向量化规则失败: {e}")
            return False

    def _get_target_collection(self, category: str) -> str:
        """根据分类确定目标集合"""
        category_mapping = {
            "novelty": "patent_rules_novelty",
            "inventiveness": "patent_rules_inventiveness",
            "utility": "patent_rules_utility",
            "sufficiency": "patent_rules_main",
            "patentability": "patent_rules_main",
            "procedure": "patent_rules_procedure"
        }

        return category_mapping.get(category, "patent_rules_main")

    async def search_similar_rules(
        self,
        query: str,
        category: str | None = None,
        limit: int = 10,
        score_threshold: float = 0.7
    ) -> list[dict[str, Any]]:
        """搜索相似专利规则"""
        if self.embedding_model is None or self.qdrant_client is None:
            logger.error("❌ 向量搜索服务不可用")
            return []

        try:
            # 向量化查询
            query_vector = self.embedding_model.encode(query)
            query_vector = query_vector / np.linalg.norm(query_vector)
            query_vector = query_vector.astype(np.float32).tolist()

            # 确定搜索范围
            search_collections = []
            if category:
                search_collections = [self._get_target_collection(category)]
            else:
                # 搜索所有专利规则集合
                search_collections = [
                    "patent_rules_main",
                    "patent_rules_novelty",
                    "patent_rules_inventiveness",
                    "patent_rules_utility",
                    "patent_rules_procedure"
                ]

            # 并行搜索多个集合
            search_results = []
            for collection in search_collections:
                try:
                    result = self.qdrant_client.search(
                        collection_name=collection,
                        query_vector=query_vector,
                        query_filter=models.Filter(
                            must=[
                                models.FieldCondition(
                                    key="confidence",
                                    range=models.Range(gte=0.5)
                                )
                            ]
                        ),
                        limit=limit,
                        search_params=models.SearchParams(
                            hnsw=models.HNSW(ef=64, m=12),
                            exact=models.Exact(key=None)
                        )
                    )

                    for hit in result:
                        search_results.append({
                            "rule_id": hit.id,
                            "score": hit.score,
                            "payload": hit.payload,
                            "collection": collection
                        })

                except Exception as e:
                    logger.warning(f"⚠️ 搜索集合 {collection} 失败: {e}")

            # 按相似度排序并过滤
            search_results.sort(key=lambda x: x["score"], reverse=True)
            filtered_results = [
                result for result in search_results
                if result["score"] >= score_threshold
            ]

            # 去重(基于rule_id)
            seen_rules = set()
            unique_results = []
            for result in filtered_results:
                if result["rule_id"] not in seen_rules:
                    seen_rules.add(result["rule_id"])
                    unique_results.append(result)

            logger.info(f"🔍 专利规则搜索完成,找到 {len(unique_results)} 个相似规则")
            return unique_results[:limit]

        except Exception as e:
            logger.error(f"❌ 相似规则搜索失败: {e}")
            return []

    async def batch_vectorize_rules(self, rules_data: list[dict[str, Any]]) -> dict[str, Any]:
        """批量向量化专利规则"""
        results = {
            "success": [],
            "failed": [],
            "total": len(rules_data),
            "start_time": datetime.now().isoformat()
        }

        logger.info(f"🔄 开始批量向量化 {len(rules_data)} 个专利规则...")

        for i, rule_data in enumerate(rules_data):
            try:
                # 向量化规则
                vector_data = await self.vectorize_patent_rule(rule_data)
                if vector_data:
                    # 存储到向量数据库
                    success = await self.store_vectorized_rule(vector_data)
                    if success:
                        results["success"].append({
                            "rule_id": vector_data["rule_id"],
                            "category": vector_data["category"],
                            "confidence": vector_data["confidence"]
                        })
                        logger.info(f"✅ ({i+1}/{len(rules_data)}) 规则 {vector_data['rule_id']} 处理成功")
                    else:
                        results["failed"].append({
                            "rule_id": rule_data.get("rule_id", f"rule_{i}"),
                            "error": "存储失败"
                        })
                else:
                    results["failed"].append({
                        "rule_id": rule_data.get("rule_id", f"rule_{i}"),
                        "error": "向量化失败"
                    })

            except Exception as e:
                results["failed"].append({
                    "rule_id": rule_data.get("rule_id", f"rule_{i}"),
                    "error": str(e)
                })
                logger.error(f"❌ ({i+1}/{len(rules_data)}) 规则处理失败: {e}")

        results["end_time"] = datetime.now().isoformat()
        results["success_count"] = len(results["success"])
        results["failed_count"] = len(results["failed"])
        results["success_rate"] = results["success_count"] / len(rules_data) if rules_data else 0

        logger.info(f"🎉 批量向量化完成: 成功 {results['success_count']}/{results['total']} (成功率: {results['success_rate']:.1%})")
        return results

    async def get_collection_stats(self) -> dict[str, Any]:
        """获取集合统计信息"""
        if not self.qdrant_client:
            return {"error": "Qdrant客户端不可用"}

        try:
            collections_info = {
                "total_collections": 0,
                "total_vectors": 0,
                "collections": {}
            }

            patent_collections = [
                "patent_rules_main",
                "patent_rules_novelty",
                "patent_rules_inventiveness",
                "patent_rules_utility",
                "patent_rules_procedure"
            ]

            for collection_name in patent_collections:
                try:
                    collection_info = self.qdrant_client.get_collection(collection_name)
                    vector_count = collection_info.vectors_count

                    collections_info["collections"][collection_name] = {
                        "vectors_count": vector_count,
                        "status": "active",
                        "vector_size": collection_info.config.params.vectors.size
                    }

                    collections_info["total_vectors"] += vector_count
                    collections_info["total_collections"] += 1

                except Exception as e:
                    collections_info["collections"][collection_name] = {
                        "status": "error",
                        "error": str(e)
                    }

            collections_info["timestamp"] = datetime.now().isoformat()
            return collections_info

        except Exception as e:
            logger.error(f"❌ 获取集合统计失败: {e}")
            return {"error": str(e)}

    async def export_vectors(self, collection_name: str, output_file: str):
        """导出向量数据"""
        if not self.qdrant_client:
            logger.error("❌ Qdrant客户端不可用")
            return False

        try:
            # 获取所有向量
            all_points = []
            offset = 0
            limit = 1000

            while True:
                result = self.qdrant_client.scroll(
                    collection_name=collection_name,
                    scroll_filter=models.Filter(),
                    limit=limit,
                    offset=offset,
                    with_payload=True,
                    with_vectors=True
                )

                points = result[0]
                if not points:
                    break

                all_points.extend(points)
                offset += len(points)

                logger.info(f"📥 已获取 {len(all_points)} 个向量点...")

                # 防止内存溢出
                if len(all_points) >= 100000:
                    logger.warning("⚠️ 向量数量过大,停止获取")
                    break

            # 准备导出数据
            export_data = {
                "collection_name": collection_name,
                "export_time": datetime.now().isoformat(),
                "total_points": len(all_points),
                "points": []
            }

            for point in all_points:
                export_data["points"].append({
                    "id": point.id,
                    "vector": point.vector,
                    "payload": point.payload
                })

            # 保存到文件
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            logger.info(f"✅ 向量数据已导出到: {output_file}")
            return True

        except Exception as e:
            logger.error(f"❌ 导出向量数据失败: {e}")
            return False

@async_main
async def main():
    """测试专利规则向量化器"""
    print("📄 测试专利规则向量化器...")

    vectorizer = PatentRuleVectorizer()

    # 初始化集合
    if not await vectorizer.initialize_collections():
        print("❌ 向量集合初始化失败")
        return 1

    try:
        # 测试专利规则数据
        test_rules = [
            {
                "rule_id": "novelty_rule_001",
                "title": "新颖性判断标准",
                "content": "专利法第二十二条规定,授予专利权的发明,应当具备新颖性。新颖性,是指该发明或者实用新型不属于现有技术;也没有任何单位或者个人就同样的发明或者实用新型在申请日以前向国务院专利行政部门提出过申请,并记载在申请日以后公布的专利申请文件或者公告的专利文件中。",
                "category": "novelty",
                "keywords": ["新颖性", "现有技术", "申请日", "抵触申请"],
                "source": "专利法第二十二条"
            },
            {
                "rule_id": "inventiveness_rule_001",
                "title": "创造性判断标准",
                "content": "专利法第二十二条规定,授予专利权的发明,应当具备创造性。创造性,是指与现有技术相比,该发明具有突出的实质性特点和显著的进步,该实用新型具有实质性特点和进步。",
                "category": "inventiveness",
                "keywords": ["创造性", "现有技术", "实质性特点", "显著进步"],
                "source": "专利法第二十二条"
            },
            {
                "rule_id": "utility_rule_001",
                "title": "实用性判断标准",
                "content": "专利法第二十二条规定,授予专利权的发明,应当具备实用性。实用性,是指该发明或者实用新型能够制造或者使用,并且能够产生积极效果。",
                "category": "utility",
                "keywords": ["实用性", "制造", "使用", "积极效果"],
                "source": "专利法第二十二条"
            }
        ]

        # 批量向量化
        print("🔄 开始批量向量化测试规则...")
        batch_result = await vectorizer.batch_vectorize_rules(test_rules)

        print("📊 批量向量化结果:")
        print(f"   总数: {batch_result['total']}")
        print(f"   成功: {batch_result['success_count']}")
        print(f"   失败: {batch_result['failed_count']}")
        print(f"   成功率: {batch_result['success_rate']:.1%}")

        # 测试相似规则搜索
        print("\n🔍 测试相似规则搜索...")
        search_queries = [
            "如何判断专利的新颖性?",
            "专利创造性的标准是什么?",
            "实用性的要求有哪些?"
        ]

        for query in search_queries:
            similar_rules = await vectorizer.search_similar_rules(query, limit=3)
            print(f"   查询: {query}")
            print(f"   结果: 找到 {len(similar_rules)} 个相似规则")
            for i, rule in enumerate(similar_rules[:2], 1):
                print(f"     {i}. {rule['payload'].get('title', '')} (相似度: {rule['score']:.3f})")

        # 获取集合统计
        print("\n📊 获取集合统计信息...")
        stats = await vectorizer.get_collection_stats()
        if "error" not in stats:
            print(f"   总集合数: {stats['total_collections']}")
            print(f"   总向量数: {stats['total_vectors']}")
            for collection, info in stats["collections"].items():
                if info.get("status") == "active":
                    print(f"   - {collection}: {info.get('vectors_count', 0)} 个向量")

        print("\n🎉 专利规则向量化器测试完成!")
        return 0

    finally:
        # 清理资源
        if vectorizer.qdrant_client:
            vectorizer.qdrant_client.close()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
