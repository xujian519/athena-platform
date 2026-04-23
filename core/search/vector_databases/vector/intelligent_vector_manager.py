#!/usr/bin/env python3

"""
智能向量管理器
Intelligent Vector Manager

统一管理法律和专利知识图谱的向量存储、检索和优化
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import numpy as np

from core.async_main import async_main
from core.logging_config import setup_logging

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

try:
    from qdrant_client import QdrantClient, models
    from qdrant_client.http import models as 
    from sentence_transformers import SentenceTransformer
    QDRANT_AVAILABLE = True
except ImportError:
    print("⚠️ qdrant-client或sentence-transformers未安装")
    QDRANT_AVAILABLE = False

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

class IntelligentVectorManager:
    """智能向量管理器"""

    def __init__(self):
        self.qdrant_client = QdrantClient(host='localhost', port=6333)
        self.embedding_model = None
        self.collections_config = {}
        self.performance_stats = {
            'total_queries': 0,
            'cache_hits': 0,
            'average_response_time': 0,
            'last_optimization': None
        }

        # 加载配置
        self._load_configuration()

        # 初始化嵌入模型
        self._init_embedding_model()

        # 初始化缓存
        self.query_cache = {}
        self.cache_size_limit = 1000

    def _load_configuration(self):
        """加载向量配置"""
        config_path = Path(__file__).parent / 'config' / 'vector_collections_config.json'

        default_config = {
            "legal_collections": {
                "legal_main": {
                    "size": 1536,
                    "description": "法律主向量库",
                    "priority": "high",
                    "update_strategy": "incremental"
                },
                "legal_contracts": {
                    "size": 1024,
                    "description": "法律合同条款向量库",
                    "priority": "high",
                    "update_strategy": "batch"
                },
                "legal_ip": {
                    "size": 1024,
                    "description": "知识产权法向量库",
                    "priority": "high",
                    "update_strategy": "incremental"
                }
            },
            "patent_collections": {
                "patent_rules": {
                    "size": 1024,
                    "description": "专利规则向量库",
                    "priority": "high",
                    "update_strategy": "real_time"
                },
                "patent_applications": {
                    "size": 1536,
                    "description": "专利申请向量库",
                    "priority": "medium",
                    "update_strategy": "batch"
                },
                "patent_legal": {
                    "size": 1024,
                    "description": "专利法律向量库",
                    "priority": "high",
                    "update_strategy": "real_time"
                }
            }
        }

        if config_path.exists():
            with open(config_path, encoding='utf-8') as f:
                self.collections_config = json.load(f)
            logger.info("✅ 向量集合配置加载成功")
        else:
            self.collections_config = default_config
            # 保存默认配置
            config_path.parent.mkdir(exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            logger.info("📝 创建默认向量集合配置")

    def _init_embedding_model(self):
        """初始化嵌入模型"""
        if not QDRANT_AVAILABLE:
            logger.warning("⚠️ 向量服务不可用,跳过模型初始化")
            return

        try:
            # 尝试加载BGE模型
            model_path = "/Users/xujian/Athena工作平台/models/BAAI/bge-m3"
            if Path(model_path).exists():
                self.embedding_model = SentenceTransformer(model_path)
                logger.info("✅ BGE嵌入模型加载成功")
            else:
                # 使用在线模型
                self.embedding_model = SentenceTransformer('BAAI/BAAI/bge-m3')
                logger.info("✅ 在线BGE嵌入模型加载成功")
        except Exception as e:
            logger.error(f"❌ 嵌入模型初始化失败: {e}")
            self.embedding_model = None

    async def initialize_collections(self):
        """初始化向量集合"""
        if not QDRANT_AVAILABLE:
            logger.error("❌ Qdrant服务不可用")
            return False

        try:
            # 确保Qdrant服务可用
            collections = self.qdrant_client.get_collections()
            logger.info(f"📊 当前Qdrant集合数量: {len(collections)}")

            # 创建法律相关集合
            for collection_name, config in self.collections_config['legal_collections'].items():
                await self._ensure_collection(f"legal_{collection_name}", config)

            # 创建专利相关集合
            for collection_name, config in self.collections_config['patent_collections'].items():
                await self._ensure_collection(f"patent_{collection_name}", config)

            logger.info("✅ 向量集合初始化完成")
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
            except Exception:
                pass  # 集合不存在，继续创建

            # 创建新集合
            vector_size = config.get('size', 1024)

            self.qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=vector_size,
                    distance=models.Distance.COSINE
                )
            )

            # 创建向量索引
            self.qdrant_client.create_index(
                collection_name=collection_name,
                field_name="vector",
                field_schema=models.PayloadSchemaParams(
                    datatype=models.PayloadSchemaType.FLOAT,
                    dims=vector_size
                )
            )

            logger.info(f"✅ 创建集合 {collection_name} (维度: {vector_size})")

        except Exception as e:
            logger.error(f"❌ 创建集合 {collection_name} 失败: {e}")

    async def vectorize_text(self, text: str, collection_type: str = "legal") -> np.Optional[ndarray]:
        """向量化文本"""
        if self.embedding_model is None:
            logger.warning("⚠️ 嵌入模型未初始化")
            return None

        try:
            # 预处理文本
            processed_text = self._preprocess_text(text, collection_type)

            # 生成向量
            embedding = self.embedding_model.encode(processed_text)

            # 归一化向量
            embedding = embedding / np.linalg.norm(embedding)

            return embedding.astype(np.float32)

        except Exception as e:
            logger.error(f"❌ 文本向量化失败: {e}")
            return None

    def _preprocess_text(self, text: str, collection_type: str) -> str:
        """预处理文本"""
        # 基础清理
        text = text.strip()

        # 领域特定预处理
        if collection_type == "legal":
            # 法律文本预处理
            text = self._preprocess_legal_text(text)
        elif collection_type == "patent":
            # 专利文本预处理
            text = self._preprocess_patent_text(text)

        return text

    def _preprocess_legal_text(self, text: str) -> str:
        """法律文本预处理"""
        # 法律术语标准化
        legal_terms = {
            "民法典": "中华人民共和国民法典",
            "专利法": "中华人民共和国专利法",
            "商标法": "中华人民共和国商标法",
            "著作权法": "中华人民共和国著作权法",
            "民事诉讼法": "中华人民共和国民事诉讼法",
            "刑事诉讼法": "中华人民共和国刑事诉讼法"
        }

        for term, standard in legal_terms.items():
            text = text.replace(term, standard)

        return text

    def _preprocess_patent_text(self, text: str) -> str:
        """专利文本预处理"""
        # 专利术语标准化
        patent_terms = {
            "发明": "发明专利",
            "实用新型": "实用新型专利",
            "外观设计": "外观设计专利",
            "创造": "创造性",
            "新颖": "新颖性",
            "实用性": "实用性"
        }

        for term, standard in patent_terms.items():
            text = text.replace(term, standard)

        return text

    async def hybrid_search(self, query: str, domain: str, limit: int = 10) -> dict[str, Any]:
        """混合搜索:向量+关键词"""
        start_time = datetime.now()

        try:
            # 生成查询向量
            query_vector = await self.vectorize_text(query, domain)
            if query_vector is None:
                return {"error": "向量化失败"}

            # 确定目标集合
            target_collections = []

            # 收集相关集合
            if domain == "legal":
                target_collections.extend([
                    "legal_main", "legal_contracts", "legal_ip"
                ])
            elif domain == "patent":
                target_collections.extend([
                    "patent_rules", "patent_applications", "patent_legal"
                ])

            # 并行搜索多个集合
            search_tasks = []
            for collection in target_collections:
                task = self._search_collection(collection, query_vector, limit)
                search_tasks.append(task)

            # 等待所有搜索完成
            results = await asyncio.gather(*search_tasks)

            # 合并结果
            merged_results = self._merge_search_results(results, query_vector)

            # 记录性能统计
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            self._update_performance_stats(response_time)

            return {
                "query": query,
                "domain": domain,
                "reports/reports/results": merged_results,
                "response_time": response_time,
                "collections_searched": target_collections,
                "cache_hit": False
            }

        except Exception as e:
            logger.error(f"❌ 混合搜索失败: {e}")
            return {"error": str(e)}

    async def _search_collection(self, collection_name: str, query_vector: np.ndarray, limit: int) -> dict[str, Any]:
        """搜索单个集合"""
        try:
            # 向量相似度搜索
            search_result = self.qdrant_client.search(
                collection_name=collection_name,
                query_vector=query_vector.tolist(),
                limit=limit,
                search_params=models.SearchParams(
                    hnsw=models.HNSW(
                        ef=64,  # 高效搜索参数
                        m=12   # 搜索候选数量
                    ),
                    exact=models.Exact(
                        key=None  # 禁用精确匹配
                    )
                )
            )

            # 转换结果格式
            results = []
            for point in search_result:
                if hasattr(point, 'payload') and point.payload:
                    results.append({
                        "id": point.id,
                        "score": point.score,
                        "payload": dict(point.payload),
                        "collection": collection_name
                    })

            return {
                "collection": collection_name,
                "reports/reports/results": results,
                "total": len(results)
            }

        except Exception as e:
            logger.error(f"❌ 搜索集合 {collection_name} 失败: {e}")
            return {"collection": collection_name, "reports/reports/results": [0]}

    def _merge_search_results(self, results: list[dict], query_vector: np.ndarray) -> list[dict]:
        """合并搜索结果"""
        all_results = []

        # 收集所有结果
        for result in results:
            if "reports/reports/results" in result:
                all_results.extend(result["reports/reports/results"])

        # 按相似度排序
        all_results.sort(key=lambda x: x.get("score", 0), reverse=True)

        # 去重(基于内容)
        seen_content = set()
        unique_results = []
        for result in all_results[:50]:  # 限制结果数量
            content_key = str(result.get("payload", {}))
            if content_key not in seen_content:
                seen_content.add(content_key)
                unique_results.append(result)

        return unique_results

    def _update_performance_stats(self, response_time: float):
        """更新性能统计"""
        self.performance_stats['total_queries'] += 1

        # 更新平均响应时间
        current_avg = self.performance_stats['average_response_time']
        total_queries = self.performance_stats['total_queries']
        new_avg = ((current_avg * (total_queries - 1)) + response_time) / total_queries
        self.performance_stats['average_response_time'] = new_avg

    async def get_performance_stats(self) -> dict[str, Any]:
        """获取性能统计"""
        return {
            **self.performance_stats,
            "cache_size": len(self.query_cache),
            "cache_hit_rate": (
                self.performance_stats['cache_hits'] / max(1, self.performance_stats['total_queries'])
            ),
            "last_updated": datetime.now().isoformat()
        }

    def save_configuration(self):
        """保存配置"""
        config_path = Path(__file__).parent / 'config' / 'vector_collections_config.json'
        config_path.parent.mkdir(exist_ok=True)

        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.collections_config, f, indent=2, ensure_ascii=False)

        logger.info("✅ 向量配置已保存")

    async def close(self):
        """关闭连接"""
        try:
            if QDRANT_AVAILABLE and self.qdrant_client:
                self.qdrant_client.close()
                logger.info("✅ Qdrant连接已关闭")
        except Exception as e:
            logger.error(f"❌ 关闭连接失败: {e}")

@async_main
async def main():
    """测试智能向量管理器"""
    print("🚀 初始化智能向量管理器...")

    manager = IntelligentVectorManager()

    try:
        # 初始化集合
        success = await manager.initialize_collections()
        if success:
            print("✅ 向量集合初始化成功")

            # 测试向量化
            test_text = "这是一份关于专利保护的法律条文"
            vector = await manager.vectorize_text(test_text, "legal")
            if vector is not None:
                print(f"✅ 文本向量化成功,向量维度: {len(vector)}")

            # 测试混合搜索
            result = await manager.hybrid_search("专利侵权责任", "legal", limit=5)
            print(f"📊 混合搜索结果: 找到 {len(result.get('reports/reports/results', []))} 条记录")

            # 显示性能统计
            stats = await manager.get_performance_stats()
            print("📈 性能统计:")
            print(f"  总查询数: {stats['total_queries']}")
            print(f"  平均响应时间: {stats['average_response_time']:.3f}s")
            print(f"  缓存命中率: {stats['cache_hit_rate']:.2%}")

            # 保存配置
            manager.save_configuration()
            print("✅ 配置已保存")

        else:
            print("❌ 向量集合初始化失败")
            return 1

        return 0

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return 1
    finally:
        await manager.close()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

