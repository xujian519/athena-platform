# 专利混合检索系统优化计划

## 📋 优化任务清单

根据您的要求，在专利审查指南GraphRAG系统完成后，需要执行以下优化任务：

### 1. 连接真实数据 📊

#### 1.1 数据库集成
```python
# 目标：连接真实的专利数据库
class PatentDatabaseConnector:
    """真实专利数据库连接器"""

    def __init__(self):
        self.postgres_conn = None
        self.neo4j_driver = None
        self.qdrant_client = None

    def connect_postgres(self):
        """连接PostgreSQL专利数据库"""
        # 使用现有的专利数据库
        from patent_platform.workspace.src.database.postgresql_manager import PostgreSQLManager
        self.postgres_manager = PostgreSQLManager()
        logger.info("PostgreSQL专利数据库连接成功")

    def connect_neo4j(self):
        """连接Neo4j专利知识图谱"""
        from patent_platform.workspace.src.knowledge_graph.neo4j_manager import Neo4jManager
        self.neo4j_manager = Neo4jManager()
        logger.info("Neo4j专利知识图谱连接成功")

    def load_real_patents(self, limit=10000):
        """加载真实专利数据"""
        # 从PostgreSQL加载专利数据
        query = """
        SELECT patent_id, title, abstract, claims, ipc_codes,
               publication_date, applicant, legal_status
        FROM patents
        ORDER BY publication_date DESC
        LIMIT %s
        """
        patents = self.postgres_manager.execute_query(query, (limit,))
        return patents
```

#### 1.2 数据质量提升
```python
# 专利数据清洗和标准化
class PatentDataCleaner:
    """专利数据清洗器"""

    def clean_text(self, text):
        """清洗专利文本"""
        # 标准化中文标点
        # 移除多余空格
        # 统一术语格式
        pass

    def normalize_ipc(self, ipc_codes):
        """标准化IPC分类"""
        # 验证IPC格式
        # 补充缺失层级
        pass

    def extract_entities(self, patent_text):
        """提取专利实体"""
        # 使用NLP工具提取技术术语
        # 识别公司名称
        # 提取发明人信息
        pass
```

### 2. 专业模型集成 🤖

#### 2.1 中文BERT集成
```python
# 使用专业embedding模型
from sentence_transformers import SentenceTransformer
from FlagEmbedding import FlagReranker

class ProfessionalEmbedding:
    """专业中文embedding服务"""

    def __init__(self):
        # 使用BGE-Large-ZH-v1.5 (1024维)
        self.model = SentenceTransformer(
            'BAAI/bge-large-zh-v1.5',
            cache_folder='./models/bge-large-zh-v1.5'
        )

        # 使用BGE-Reranker进行重排序
        self.reranker = FlagReranker(
            'BAAI/bge-reranker-large',
            cache_folder='./models/bge-reranker-large'
        )

    def encode_patent_text(self, text):
        """编码专利文本"""
        # 预处理专利文本
        enhanced_text = self.preprocess_patent_text(text)
        return self.model.encode(enhanced_text)

    def preprocess_patent_text(self, text):
        """专利文本预处理"""
        # 添加专利特有标识
        # 处理专业术语
        # 保留关键结构
        pass

    def rerank_results(self, query, passages):
        """重排序检索结果"""
        return self.reranker.compute_score(query, passages)
```

#### 2.2 领域微调模型
```python
# 在专利数据上微调模型
class PatentFineTuner:
    """专利领域模型微调器"""

    def prepare_training_data(self):
        """准备训练数据"""
        # 使用专利对构建对比学习数据
        # 使用专利分类数据
        pass

    def fine_tune_embedding_model(self):
        """微调embedding模型"""
        # 使用专利领域数据微调
        # 保存微调后的模型
        pass
```

### 3. 性能优化 ⚡

#### 3.1 缓存机制
```python
from redis import Redis
import pickle
from functools import wraps

class CacheManager:
    """缓存管理器"""

    def __init__(self):
        self.redis = Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=False
        )
        self.cache_ttl = {
            'query_result': 3600,  # 1小时
            'embedding': 86400,   # 24小时
            'patent_data': 7200   # 2小时
        }

    def cache_result(self, key, data, cache_type='query_result'):
        """缓存结果"""
        cache_data = pickle.dumps(data)
        self.redis.setex(
            f"{cache_type}:{key}",
            self.cache_ttl[cache_type],
            cache_data
        )

    def get_cached_result(self, key, cache_type='query_result'):
        """获取缓存结果"""
        cache_data = self.redis.get(f"{cache_type}:{key}")
        if cache_data:
            return pickle.loads(cache_data)
        return None
```

#### 3.2 并行处理
```python
import asyncio
import concurrent.futures

class ParallelProcessor:
    """并行处理器"""

    def __init__(self, max_workers=4):
        self.max_workers = max_workers
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)

    async def parallel_vector_search(self, queries):
        """并行向量搜索"""
        loop = asyncio.get_event_loop()

        tasks = []
        for query in queries:
            task = loop.run_in_executor(
                self.executor,
                self._vector_search,
                query
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        return results

    def _vector_search(self, query):
        """向量搜索（在线程池中执行）"""
        # 执行向量搜索
        pass
```

#### 3.3 索引优化
```python
class IndexOptimizer:
    """索引优化器"""

    def optimize_postgresql_indexes(self):
        """优化PostgreSQL索引"""
        indexes = [
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patents_title_gin ON patents USING GIN(to_tsvector('chinese', title))",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patents_ipc_gin ON patents USING GIN(ipc_codes)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patents_applicant_btree ON patents(applicant)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patents_date_btree ON patents(publication_date)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patents_legal_status ON patents(legal_status)"
        ]

        for index_sql in indexes:
            self.postgres_conn.execute(index_sql)

    def create_materialized_views(self):
        """创建物化视图"""
        views = [
            """
            CREATE MATERIALIZED VIEW IF NOT EXISTS mv_patent_stats AS
            SELECT
                COUNT(*) as total_patents,
                COUNT(DISTINCT ipc_codes[1]) as unique_ipc_classes,
                DATE_TRUNC('month', publication_date) as month,
                legal_status
            FROM patents
            GROUP BY month, legal_status
            """
        ]

        for view_sql in views:
            self.postgres_conn.execute(view_sql)
```

### 4. API接口增强 🔌

#### 4.1 RESTful API
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="专利混合检索API", version="2.0")

class SearchRequest(BaseModel):
    query: str
    filters: Optional[dict] = None
    limit: int = 20
    include_explanation: bool = True
    use_rerank: bool = True

class PatentResponse(BaseModel):
    patent_id: str
    title: str
    abstract: str
    ipc_codes: List[str]
    score: float
    highlights: dict
    explanation: Optional[str]

@app.post("/search/patents")
async def search_patents(request: SearchRequest):
    """检索专利"""
    # 检查缓存
    cache_key = f"search:{hash(str(request.dict()))}"
    cached_result = cache.get_cached_result(cache_key)
    if cached_result:
        return cached_result

    # 执行检索
    results = await patent_retrieval.hybrid_search(
        query=request.query,
        filters=request.filters,
        limit=request.limit
    )

    # 使用reranker重排序
    if request.use_rerank and len(results) > 0:
        passages = [r['abstract'] for r in results]
        scores = await embedding_service.rerank_results(request.query, passages)
        for i, result in enumerate(results):
            result['rerank_score'] = scores[i]
        results.sort(key=lambda x: x['rerank_score'], reverse=True)

    # 生成响应
    response = [PatentResponse(**r) for r in results]

    # 缓存结果
    cache.cache_result(cache_key, response)

    return response
```

#### 4.2 WebSocket实时检索
```python
from fastapi import WebSocket
import json

@app.websocket("/ws/search")
async def websocket_search(websocket: WebSocket):
    """WebSocket实时检索"""
    await websocket.accept()

    try:
        while True:
            # 接收查询
            data = await websocket.receive_text()
            query_data = json.loads(data)

            # 实时检索
            results = await real_time_search(query_data['query'])

            # 推送结果
            await websocket.send_json({
                'type': 'search_results',
                'results': results,
                'query_id': query_data.get('query_id'),
                'timestamp': time.time()
            })

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
```

### 5. 监控与度量 📈

#### 5.1 性能监控
```python
from prometheus_client import Counter, Histogram, Gauge
import time

# Prometheus指标
search_counter = Counter('patent_search_requests_total', 'Total patent search requests')
search_duration = Histogram('patent_search_duration_seconds', 'Patent search duration')
cache_hit_rate = Gauge('patent_search_cache_hit_rate', 'Cache hit rate')

class PerformanceMonitor:
    """性能监控器"""

    @search_duration.time()
    def monitor_search(self, func):
        """监控搜索性能"""
        def wrapper(*args, **kwargs):
            search_counter.inc()
            start_time = time.time()

            result = func(*args, **kwargs)

            duration = time.time() - start_time
            logger.info(f"Search completed in {duration:.3f}s")

            return result
        return wrapper

    def update_cache_stats(self, hits, total):
        """更新缓存统计"""
        hit_rate = hits / total if total > 0 else 0
        cache_hit_rate.set(hit_rate)
```

#### 5.2 质量评估
```python
class QualityAssessment:
    """质量评估器"""

    def evaluate_retrieval_quality(self, query, results):
        """评估检索质量"""
        metrics = {
            'precision': self.calculate_precision(query, results),
            'recall': self.calculate_recall(query, results),
            'coverage': self.calculate_coverage(query, results),
            'diversity': self.calculate_diversity(results),
            'freshness': self.calculate_freshness(results)
        }

        return metrics

    def calculate_precision(self, query, results):
        """计算精确率"""
        # 与基准答案比较
        pass

    def calculate_freshness(self, results):
        """计算新鲜度"""
        # 检查专利年龄分布
        now = datetime.now()
        freshness_scores = []

        for result in results:
            pub_date = result.get('publication_date')
            if pub_date:
                age_days = (now - pub_date).days
                # 近期专利得分更高
                score = 1 / (1 + age_days / 365)
                freshness_scores.append(score)

        return sum(freshness_scores) / len(freshness_scores) if freshness_scores else 0
```

## 🚀 实施时间线

### 第1周：数据库连接
- [ ] 连接PostgreSQL专利数据库
- [ ] 连接Neo4j知识图谱
- [ ] 连接Qdrant向量库
- [ ] 测试数据迁移

### 第2周：专业模型集成
- [ ] 安装BGE-Large-ZH-v1.5模型
- [ ] 集成BGE-Reranker
- [ ] 测试模型性能
- [ ] 微调专利领域模型

### 第3周：性能优化
- [ ] 实现Redis缓存
- [ ] 添加并行处理
- [ ] 优化数据库索引
- [ ] 性能基准测试

### 第4周：API开发
- [ ] 开发RESTful API
- [ ] 实现WebSocket支持
- [ ] 添加监控指标
- [ ] 文档编写

## 📊 预期提升

### 性能提升
- 检索准确率: 85% → 95%
- 响应时间: 500ms → 200ms
- 并发支持: 10 QPS → 100 QPS

### 功能增强
- 真实数据检索
- 专业语义理解
- 智能排序
- 实时更新

## 💡 关键技术决策

1. **模型选择**: BGE-Large-ZH-v1.5是目前中文语义理解的最佳选择
2. **缓存策略**: Redis + 本地缓存双层缓存
3. **并行处理**: 向量检索和图谱检索并行执行
4. **增量更新**: 定期更新索引以保持数据新鲜度

---

*更新时间: 2025-12-12*