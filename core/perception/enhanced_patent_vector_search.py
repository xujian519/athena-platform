#!/usr/bin/env python3
"""
增强专利向量检索系统
Enhanced Patent Vector Search System

提供高质量的专利语义检索和相似度分析能力

作者: Athena AI系统
创建时间: 2025-12-07
版本: 1.0.0
"""
import numpy as np

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import requests
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class VectorSearchMode(Enum):
    """向量检索模式"""

    SEMANTIC = "semantic"  # 语义检索
    KEYWORD = "keyword"  # 关键词检索
    HYBRID = "hybrid"  # 混合检索
    TECHNICAL = "technical"  # 技术特征检索
    CLAIMS = "claims"  # 权利要求检索


@dataclass
class PatentSearchQuery:
    """专利检索查询"""

    query_text: str
    search_mode: VectorSearchMode = VectorSearchMode.HYBRID
    patent_id: str | None = None
    filters: dict[str, Any] = field(default_factory=dict)
    limit: int = 10
    threshold: float = 0.7
    technical_field: str | None = None
    ipc_classification: list[str] | None = None


@dataclass
class PatentSearchResult:
    """专利检索结果"""

    query_id: str
    patent_id: str
    title: str
    abstract: str
    similarity_score: float
    technical_field: str | None = None
    ipc_classification: list[str] | None = None
    key_features: list[str] = field(default_factory=list)
    snippet: str = ""
    ranking_position: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class PatentTextPreprocessor:
    """专利文本预处理器"""

    def __init__(self):
        # 停用词
        self.stop_words = {
            "的",
            "了",
            "在",
            "是",
            "我",
            "有",
            "和",
            "就",
            "不",
            "人",
            "都",
            "一",
            "一个",
            "上",
            "也",
            "很",
            "到",
            "说",
            "要",
            "去",
            "你",
            "会",
            "着",
            "没有",
            "看",
            "好",
            "自己",
            "这",
            "那",
            "他",
            "她",
            "它",
            "们",
            "这个",
            "那个",
            "什么",
            "怎么",
            "如何",
            "为什么",
            "因为",
            "所以",
            "但是",
            "然而",
            "因此",
            "而且",
            "或者",
            "包括",
            "包含",
            "具有",
            "设置",
            "安装",
            "固定",
            "连接",
            "支撑",
            "布置",
        }

        # 技术术语权重
        self.technical_terms_weights = {
            "装置": 2.0,
            "系统": 2.0,
            "方法": 2.0,
            "结构": 1.8,
            "组件": 1.5,
            "机构": 1.5,
            "单元": 1.5,
            "模块": 1.5,
            "部件": 1.3,
            "元件": 1.3,
            "零件": 1.2,
            "材料": 1.5,
            "合金": 2.0,
            "聚合物": 2.0,
            "复合": 1.8,
            "涂层": 1.5,
            "薄膜": 1.5,
            "纤维": 1.5,
            "陶瓷": 2.0,
            "塑料": 1.5,
            "芯片": 2.0,
            "电路": 1.8,
            "传感器": 2.0,
            "控制器": 2.0,
            "处理器": 2.0,
            "存储器": 1.8,
            "显示器": 1.5,
            "天线": 1.5,
            "基站": 2.0,
            "信号": 1.5,
            "协议": 1.5,
            "编码": 1.8,
            "调制": 1.8,
            "网络": 1.5,
            "传输": 1.5,
            "化合物": 2.0,
            "催化剂": 2.0,
            "反应器": 2.0,
            "合成": 2.0,
            "配方": 1.8,
        }

    def preprocess_text(self, text: str, mode: VectorSearchMode = VectorSearchMode.HYBRID) -> str:
        """预处理专利文本"""
        if not text:
            return ""

        # 清理文本
        text = self._clean_text(text)

        # 根据模式选择处理方式
        if mode == VectorSearchMode.KEYWORD:
            text = self._keyword_enhance(text)
        elif mode == VectorSearchMode.TECHNICAL:
            text = self._technical_enhance(text)
        elif mode == VectorSearchMode.CLAIMS:
            text = self._claims_enhance(text)

        return text

    def _clean_text(self, text: str) -> str:
        """清理文本"""
        # 移除特殊字符但保留中文标点和基本符号
        # 明确列出要保留的字符，包括中文逗号\uff0c
        text = re.sub(r"[^\u4e00-\u9fff\u3000-\u303f\w\s\uff0c,。;:!?、()\[\]\{\}\-\+\*/=<>\.`'""]", " ", text)

        # 合并多个空格
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def _keyword_enhance(self, text: str) -> str:
        """关键词增强"""
        # 先移除停用词
        for stop_word in self.stop_words:
            text = text.replace(stop_word, " ")

        # 提取关键词
        keywords = []
        words = text.split()

        for word in words:
            word = word.strip()
            if len(word) > 1 and word not in self.stop_words:
                keywords.append(word)

        # 加权重复技术术语
        enhanced_keywords = []
        for word in keywords:
            enhanced_keywords.append(word)
            if word in self.technical_terms_weights:
                weight = self.technical_terms_weights[word]
                # 重复技术术语以增加权重
                for _ in range(int(weight) - 1):
                    enhanced_keywords.append(word)

        return " ".join(enhanced_keywords)

    def _technical_enhance(self, text: str) -> str:
        """技术特征增强"""
        # 提取技术特征短语
        feature_patterns = [
            r"([^,。;;\n]{0,10}(?:装置|系统|方法|结构|组件|机构))",
            r"([^,。;;\n]{0,15}(?:包括|由|具有|设置|安装|配备))([^,。;;\n]{0,15})",
            r"([^,。;;\n]{0,15}(?:通过|利用|采用|基于|根据))([^,。;;\n]{0,15})",
        ]

        enhanced_features = []
        for pattern in feature_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                feature = "".join(match) if isinstance(match, tuple) else match
                enhanced_features.append(feature.strip())

        # 保持原文但重复技术特征
        enhanced_text = text + " " + " ".join(enhanced_features) * 2

        return enhanced_text

    def _claims_enhance(self, text: str) -> str:
        """权利要求增强"""
        # 提取权利要求关键元素
        claims_patterns = [
            r"([^,。;;\n]*(?:一种|所述)[^,。;;\n]*(?:装置|系统|方法|结构|组件))",
            r"([^,。;;\n]*(?:其中|其特征在于))([^,。;;\n]{0,20})",
            r"([^,。;;\n]*(?:根据权利要求\d+所述))([^,。;;\n]{0,15})",
        ]

        enhanced_claims = []
        for pattern in claims_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                claim = "".join(match) if isinstance(match, tuple) else match
                enhanced_claims.append(claim.strip())

        # 重点强调权利要求限制
        limitation_patterns = [
            r"([^,。;;\n]*范围[^,。;;\n]{0,10})",
            r"([^,。;;\n]*限定[^,。;;\n]{0,10})",
            r"([^,。;;\n]*由[^,。;;\n]*组成[^,。;;\n]*)",
        ]

        limitations = []
        for pattern in limitation_patterns:
            matches = re.findall(pattern, text)
            limitations.extend(matches)

        # 构建增强文本
        enhanced_text = text
        if enhanced_claims:
            enhanced_text += " 权利要求特征: " + " ".join(enhanced_claims)
        if limitations:
            enhanced_text += " 权利要求限制: " + " ".join(limitations)

        return enhanced_text


class PatentEmbeddingGenerator:
    """专利嵌入生成器"""

    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        self.model_name = model_name
        self.model = None
        self.initialized = False

    async def initialize(self):
        """初始化嵌入模型"""
        if self.initialized:
            return

        logger.info(f"🧠 加载专利嵌入模型: {self.model_name}")

        try:
            # 加载sentence-transformers模型
            self.model = SentenceTransformer(self.model_name)

            # 测试模型
            test_embedding = self.model.encode("测试", convert_to_numpy=True)

            self.initialized = True
            logger.info(f"✅ 专利嵌入模型加载完成: 向量维度{len(test_embedding)}")

        except Exception as e:
            logger.error(f"❌ 专利嵌入模型加载失败: {e}")
            raise

    def generate_embedding(self, text: str) -> np.ndarray:
        """生成文本嵌入向量"""
        if not self.initialized:
            raise RuntimeError("嵌入模型未初始化")

        try:
            embedding = self.model.encode(
                text, convert_to_numpy=True, show_progress_bar=False, normalize_embeddings=True
            )

            return embedding

        except Exception as e:
            logger.error(f"嵌入生成失败: {e}")
            raise

    def batch_generate_embeddings(self, texts: list[str]) -> np.ndarray:
        """批量生成嵌入向量"""
        if not self.initialized:
            raise RuntimeError("嵌入模型未初始化")

        try:
            embeddings = self.model.encode(
                texts,
                convert_to_numpy=True,
                show_progress_bar=False,
                normalize_embeddings=True,
                batch_size=32,
            )

            return embeddings

        except Exception as e:
            logger.error(f"批量嵌入生成失败: {e}")
            raise


class EnhancedPatentVectorSearch:
    """增强专利向量检索系统"""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.initialized = False

        # 初始化组件
        self.preprocessor = PatentTextPreprocessor()
        self.embedding_generator = PatentEmbeddingGenerator(
            self.config.get("model_name", "paraphrase-multilingual-MiniLM-L12-v2")
        )

        # 向量数据库配置
        self.vector_db_url = self.config.get("vector_db_url", "http://localhost:6333")
        self.collection_name = self.config.get("collection_name", "patent_vectors")

        # 缓存
        self.embedding_cache = {}
        self.search_cache = {}

        logger.info("🔍 创建增强专利向量检索系统")

    async def initialize(self):
        """初始化检索系统"""
        if self.initialized:
            return

        logger.info("🚀 启动增强专利向量检索系统")

        try:
            # 初始化嵌入生成器
            await self.embedding_generator.initialize()

            # 检查向量数据库连接
            await self._check_vector_db_connection()

            # 初始化向量数据库集合
            await self._initialize_collection()

            self.initialized = True
            logger.info("✅ 增强专利向量检索系统启动完成")

        except Exception as e:
            logger.error(f"❌ 增强专利向量检索系统启动失败: {e}")
            raise

    async def _check_vector_db_connection(self):
        """检查向量数据库连接"""
        try:
            health_url = f"{self.vector_db_url}/health"
            response = requests.get(health_url, timeout=5)

            if response.status_code == 200:
                logger.info("✅ 向量数据库连接正常")
            else:
                logger.warning(f"⚠️ 向量数据库响应异常: {response.status_code}")

        except Exception as e:
            logger.error(f"❌ 向量数据库连接失败: {e}")

    async def _initialize_collection(self):
        """初始化向量数据库集合"""
        try:
            # 检查集合是否存在
            collections_url = f"{self.vector_db_url}/collections"
            response = requests.get(collections_url)

            if response.status_code == 200:
                collections = response.json().get("result", {})
                collection_names = [col.get("name") for col in collections]

                if self.collection_name not in collection_names:
                    # 创建新集合
                    create_url = f"{self.vector_db_url}/collections"
                    create_data = {
                        "name": self.collection_name,
                        "vectors": {"size": 384, "distance": "Cosine"},  # MiniLM的向量维度
                        "payload_schema": {
                            "patent_id": "keyword",
                            "title": "text",
                            "abstract": "text",
                            "technical_field": "keyword",
                            "ipc_classification": "keyword",
                            "key_features": "array",
                            "metadata": "json",
                        },
                    }

                    create_response = requests.post(create_url, json=create_data)
                    if create_response.status_code == 200:
                        logger.info(f"✅ 创建向量数据库集合: {self.collection_name}")
                    else:
                        logger.error(f"❌ 创建集合失败: {create_response.text}")
                else:
                    logger.info(f"✅ 向量数据库集合已存在: {self.collection_name}")

        except Exception as e:
            logger.error(f"初始化向量数据库集合失败: {e}")

    async def index_patent(
        self,
        patent_id: str,
        title: str,
        abstract: str,
        technical_field: str | None = None,
        ipc_classification: list[str] | None = None,
        key_features: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """索引专利"""
        if not self.initialized:
            raise RuntimeError("检索系统未初始化")

        try:
            logger.info(f"📝 索引专利: {patent_id}")

            # 预处理文本
            combined_text = f"{title} {abstract}"
            preprocessed_text = self.preprocessor.preprocess_text(
                combined_text, VectorSearchMode.HYBRID
            )

            # 生成缓存键
            cache_key = f"{patent_id}_{hash(combined_text)}"
            if cache_key in self.embedding_cache:
                embedding = self.embedding_cache[cache_key]
            else:
                # 生成嵌入向量
                embedding = self.embedding_generator.generate_embedding(preprocessed_text)
                self.embedding_cache[cache_key] = embedding

            # 构建点数据
            point_data = {
                "id": patent_id,
                "vector": embedding.tolist(),
                "payload": {
                    "patent_id": patent_id,
                    "title": title,
                    "abstract": abstract,
                    "technical_field": technical_field or "",
                    "ipc_classification": ipc_classification or [],
                    "key_features": key_features or [],
                    "metadata": metadata or {},
                },
            }

            # 上传到向量数据库
            upsert_url = f"{self.vector_db_url}/collections/{self.collection_name}/points"
            response = requests.put(upsert_url, json={"points": [point_data]})

            if response.status_code == 200:
                logger.info(f"✅ 专利索引完成: {patent_id}")
                return True
            else:
                logger.error(f"❌ 专利索引失败: {response.text}")
                return False

        except Exception as e:
            logger.error(f"专利索引异常: {e}")
            return False

    async def search_patents(self, query: PatentSearchQuery) -> list[PatentSearchResult]:
        """检索专利"""
        if not self.initialized:
            raise RuntimeError("检索系统未初始化")

        try:
            logger.info(f"🔍 检索专利: {query.search_mode.value} - 限制{query.limit}")

            # 检查缓存
            cache_key = f"{query.query_text}_{query.search_mode.value}_{query.limit}"
            if cache_key in self.search_cache:
                logger.info("📋 使用缓存检索结果")
                return self.search_cache[cache_key]

            # 预处理查询文本
            preprocessed_query = self.preprocessor.preprocess_text(
                query.query_text, query.search_mode
            )

            # 生成查询向量
            query_embedding = self.embedding_generator.generate_embedding(preprocessed_query)

            # 构建搜索请求
            search_data = {
                "vector": query_embedding.tolist(),
                "limit": query.limit,
                "with_payload": True,
                "with_vector": False,
                "score_threshold": query.threshold,
            }

            # 添加过滤条件
            if query.technical_field:
                search_data["filter"] = {
                    "must": [{"key": "technical_field", "match": {"value": query.technical_field}}]
                }

            # 执行搜索
            search_url = f"{self.vector_db_url}/collections/{self.collection_name}/points/search"
            response = requests.post(search_url, json=search_data)

            if response.status_code == 200:
                search_results = response.json()
                points = search_results.get("result", [])

                # 转换为专利检索结果
                results = []
                for i, point in enumerate(points):
                    payload = point.get("payload", {})
                    result = PatentSearchResult(
                        query_id=str(cache_key),
                        patent_id=payload.get("patent_id", ""),
                        title=payload.get("title", ""),
                        abstract=payload.get("abstract", ""),
                        similarity_score=point.get("score", 0.0),
                        technical_field=payload.get("technical_field"),
                        ipc_classification=payload.get("ipc_classification"),
                        key_features=payload.get("key_features", []),
                        snippet=self._generate_snippet(
                            payload.get("abstract", ""), query.query_text
                        ),
                        ranking_position=i + 1,
                        metadata=payload.get("metadata", {}),
                    )
                    results.append(result)

                # 缓存结果
                self.search_cache[cache_key] = results

                logger.info(f"✅ 专利检索完成: 找到{len(results)}个结果")
                return results
            else:
                logger.error(f"❌ 专利检索失败: {response.text}")
                return []

        except Exception as e:
            logger.error(f"专利检索异常: {e}")
            return []

    def _generate_snippet(self, text: str, query: str, max_length: int = 200) -> str:
        """生成检索摘要"""
        if not text or not query:
            return ""

        try:
            # 简单的关键词高亮和摘要生成
            _query_words = set(query.split())
            text_words = text.split()

            snippet_words = []
            current_length = 0

            for word in text_words:
                if current_length + len(word) + 1 <= max_length:
                    snippet_words.append(word)
                    current_length += len(word) + 1
                else:
                    break

            return " ".join(snippet_words) + ("..." if len(snippet_words) < len(text_words) else "")

        except Exception as e:
            logger.debug(f"文本截断失败，使用简单截取: {e}")
            return text[:max_length] + ("..." if len(text) > max_length else "")

    async def find_similar_patents(
        self, patent_id: str, limit: int = 10
    ) -> list[PatentSearchResult]:
        """查找相似专利"""
        try:
            # 首先获取目标专利信息
            point_url = f"{self.vector_db_url}/collections/{self.collection_name}/points/ids"
            response = requests.post(point_url, json={"ids": [patent_id]})

            if response.status_code == 200:
                points = response.json().get("result", [])
                if points:
                    target_payload = points[0].get("payload", {})
                    target_text = (
                        f"{target_payload.get('title', '')} {target_payload.get('abstract', '')}"
                    )

                    # 使用目标专利文本检索相似专利
                    similarity_query = PatentSearchQuery(
                        query_text=target_text,
                        search_mode=VectorSearchMode.SEMANTIC,
                        limit=limit,
                        threshold=0.6,
                    )

                    # 排除自身
                    similar_results = await self.search_patents(similarity_query)
                    similar_results = [r for r in similar_results if r.patent_id != patent_id]

                    logger.info(
                        f"✅ 相似专利检索完成: {patent_id} - 找到{len(similar_results)}个相似专利"
                    )
                    return similar_results
                else:
                    logger.warning(f"⚠️ 未找到目标专利: {patent_id}")
                    return []
            else:
                logger.error(f"❌ 获取目标专利失败: {response.text}")
                return []

        except Exception as e:
            logger.error(f"相似专利检索异常: {e}")
            return []

    async def get_statistics(self) -> dict[str, Any]:
        """获取检索统计信息"""
        try:
            # 获取集合信息
            collection_url = f"{self.vector_db_url}/collections/{self.collection_name}"
            response = requests.get(collection_url)

            if response.status_code == 200:
                collection_info = response.json()["result"]
                points_count = collection_info.get("points_count", 0)
                vectors_size = collection_info.get("vectors_config", {}).get("size", 0)

                return {
                    "total_patents": points_count,
                    "vector_dimension": vectors_size,
                    "embedding_cache_size": len(self.embedding_cache),
                    "search_cache_size": len(self.search_cache),
                    "collection_name": self.collection_name,
                    "initialized": self.initialized,
                }
            else:
                return {"error": "无法获取统计信息"}

        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {"error": str(e)}

    async def clear_cache(self):
        """清理缓存"""
        self.embedding_cache.clear()
        self.search_cache.clear()
        logger.info("🗑️ 检索缓存已清理")

    async def shutdown(self):
        """关闭检索系统"""
        logger.info("🔄 关闭增强专利向量检索系统")

        try:
            await self.clear_cache()
            self.initialized = False
            logger.info("✅ 增强专利向量检索系统已关闭")

        except Exception as e:
            logger.error(f"❌ 增强专利向量检索系统关闭失败: {e}")


# 导出类
__all__ = [
    "EnhancedPatentVectorSearch",
    "PatentEmbeddingGenerator",
    "PatentSearchQuery",
    "PatentSearchResult",
    "PatentTextPreprocessor",
    "VectorSearchMode",
]
