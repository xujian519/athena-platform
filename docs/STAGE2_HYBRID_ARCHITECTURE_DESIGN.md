# 第二阶段：混合架构详细设计

## 📋 架构概览

基于原始方案，结合存储宪法原则，第二阶段的混合架构设计如下：

```
                    ┌─────────────────────────────────────┐
                    │           Athena CLI终端             │
                    │         (命令行交互界面)             │
                    └─────────────┬───────────────────────┘
                                  │
                    ┌─────────────▼───────────────────────┐
                    │      统一存储访问层 (USAL)           │
                    │   - 查询路由分发                     │
                    │   - 结果融合排序                     │
                    │   - 事务协调管理                     │
                    │   - 缓存策略控制                     │
                    └─────────────┬───────────────────────┘
                                  │
            ┌─────────────────────┼─────────────────────┐
            │                     │                     │
    ┌───────▼───────┐    ┌───────▼───────┐    ┌───────▼───────┐
    │  PostgreSQL   │    │   ArangoDB    │    │    Qdrant     │
    │              │    │              │    │              │
    │ 📄 文档元数据  │    │ 🕸️ 知识图谱    │    │ 🔍 向量搜索   │
    │ 👥 用户权限    │    │ 🔗 实体关系    │    │ 📊 语义相似   │
    │ 📊 审计日志    │    │ 📈 关系分析    │    │ 🎯 智能推荐   │
    │              │    │              │    │              │
    │端口: 5432     │    │端口: 8529     │    │端口: 6333     │
    └───────────────┘    └───────────────┘    └───────────────┘
            │                     │                     │
            └─────────────────────┼─────────────────────┘
                                  │
                    ┌─────────────▼───────────────────────┐
                    │         存储宪法控制层               │
                    │  - 数据生命周期管理                 │
                    │  - 安全访问控制                     │
                    │  - 性能监控告警                     │
                    │  - 备份恢复策略                     │
                    └─────────────────────────────────────┘
```

## 🏗️ 三层数据架构

### 第一层：数据持久层

#### PostgreSQL - 结构化数据主存储
```sql
-- 扩展后的专利表结构
CREATE TABLE patents (
    -- 主键
    patent_id VARCHAR(50) PRIMARY KEY,

    -- 基础信息
    title TEXT NOT NULL,
    abstract TEXT,
    application_number VARCHAR(50),
    application_date DATE,
    publication_number VARCHAR(50),
    publication_date DATE,
    inventor VARCHAR(500),
    applicant VARCHAR(200),

    -- 分类信息
    ipc_codes TEXT[], -- IPC分类号数组
    cpc_codes TEXT[], -- CPC分类号数组

    -- 法律状态
    status VARCHAR(20) DEFAULT 'pending',
    legal_status VARCHAR(50),

    -- 关联ID（跨库关联）
    arango_node_id TEXT,  -- ArangoDB节点ID
    qdrant_vector_id TEXT, -- Qdrant向量ID

    -- 元数据
    file_path TEXT,      -- 原文件路径
    file_size BIGINT,    -- 文件大小
    file_hash TEXT,      -- 文件hash

    -- 审计字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(user_id),

    -- 索引
    INDEX idx_patents_app_date (application_date),
    INDEX idx_patents_ipc ( USING GIN(ipc_codes) ),
    INDEX idx_patents_status (status),
    INDEX idx_patents_arango_id (arango_node_id),
    INDEX idx_patents_qdrant_id (qdrant_vector_id)
);

-- 文档内容表（用于全文搜索）
CREATE TABLE patent_contents (
    patent_id VARCHAR(50) PRIMARY KEY REFERENCES patents(patent_id),
    content TEXT,                    -- 全文内容
    claims TEXT,                     -- 权利要求
    description TEXT,                -- 说明书
    full_text_vector tsvector,       -- 全文搜索向量

    -- 全文搜索索引
    INDEX idx_patent_content_fts ( USING GIN(full_text_vector) )
);

-- 搜索历史增强表
CREATE TABLE search_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    query_type VARCHAR(20),         -- text/vector/graph/hybrid
    query TEXT,
    filters JSONB,                  -- 搜索条件
    results_count INTEGER,
    response_time INTEGER,          -- 响应时间(ms)
    satisfied BOOLEAN,              -- 用户是否满意
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_search_user_time (user_id, created_at),
    INDEX idx_search_type (query_type),
    INDEX idx_search_response (response_time)
);
```

#### ArangoDB - 知识图谱存储
```yaml
# 专利图数据库结构设计
patent_knowledge_graph:
  # 顶点集合
  vertex_collections:
    patents:
      schema:
        type: object
        properties:
          patent_id: {type: string}
          title: {type: string}
          ipc_main: {type: string}
          tech_field: {type: string}

    companies:
      schema:
        type: object
        properties:
          company_id: {type: string}
          name: {type: string}
          type: {type: string}  # applicant/owner/investor
          location: {type: string}

    inventors:
      schema:
        type: object
        properties:
          inventor_id: {type: string}
          name: {type: string}
          nationality: {type: string}

    ipc_classes:
      schema:
        type: object
        properties:
          ipc_code: {type: string}
          description: {type: string}
          section: {type: string}
          level: {type: integer}

    tech_concepts:
      schema:
        type: object
        properties:
          concept_id: {type: string}
          name: {type: string}
          domain: {type: string}

  # 边集合
  edge_collections:
    cites:
      schema:
        from: patents
        to: patents
        properties:
          cited_type: {type: string}  # forward/backward
          cited_date: {type: string}

    owned_by:
      schema:
        from: patents
        to: companies
        properties:
          ownership_ratio: {type: number}
          transfer_date: {type: string}

    invented_by:
      schema:
        from: patents
        to: inventors
        properties:
          inventor_order: {type: integer}
          contribution_rate: {type: number}

    classified_as:
      schema:
        from: patents
        to: ipc_classes
        properties:
          classification_level: {type: string}
          classification_date: {type: string}

    related_to:
      schema:
        from: tech_concepts
        to: tech_concepts
        properties:
          relation_type: {type: string}
          strength: {type: number}

# 索引策略
indexes:
  patents:
    - type: hash
      fields: ["patent_id"]
      unique: true
    - type: persistent
      fields: ["ipc_main"]

  cites:
    - type: edge
      fields: ["_from", "_to"]

# 图算法配置
graph_analyzers:
  pagerank:
    algorithm: pagerank
    params:
      damping: 0.85
      iterations: 100

  community_detection:
    algorithm: louvain
    params:
      resolution: 1.0
```

#### Qdrant - 向量数据库优化
```python
# 向量集合配置升级
COLLECTION_CONFIGS = {
    "patent_title_vectors": {
        "vectors": {
            "size": 768,
            "distance": "Cosine"
        },
        "payload_schema": {
            "patent_id": "keyword",
            "ipc_section": "keyword",
            "publication_year": "integer",
            "tech_field": "text",
            "importance_score": "float"
        },
        "hnsw_config": {
            "m": 16,
            "ef_construct": 200
        }
    },

    "patent_content_vectors": {
        "vectors": {
            "size": 1024,  # 更大的内容向量
            "distance": "Cosine"
        },
        "payload_schema": {
            "patent_id": "keyword",
            "content_type": "keyword",  # claims/description/abstract
            "chunk_index": "integer",
            "section_id": "keyword"
        },
        "hnsw_config": {
            "m": 32,
            "ef_construct": 400
        }
    },

    "patent_image_vectors": {
        "vectors": {
            "size": 512,  # 图像特征向量
            "distance": "Cosine"
        },
        "payload_schema": {
            "patent_id": "keyword",
            "image_type": "keyword",  # drawing/figure/diagram
            "image_hash": "keyword"
        }
    }
}

# 搜索过滤器配置
FILTER_INDEXES = {
    "patent_metadata": {
        "field": "ipc_section",
        "type": "keyword"
    },
    "temporal_filters": {
        "field": "publication_year",
        "type": "integer"
    },
    "quality_filters": {
        "field": "importance_score",
        "type": "float"
    }
}
```

### 第二层：数据访问层

#### 统一存储接口 (USAL)
```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import asyncio

class StorageInterface(ABC):
    """统一存储接口"""

    @abstractmethod
    async def connect(self) -> bool:
        """连接数据库"""
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """断开连接"""
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        pass

class HybridStorageManager:
    """混合存储管理器 - 核心组件"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.postgres = PostgreSQLAdapter(config['postgres'])
        self.arangodb = ArangoDBAdapter(config['arangodb'])
        self.qdrant = QdrantAdapter(config['qdrant'])

        # 缓存层
        self.cache = RedisCache(config['cache'])

        # 监控器
        self.monitor = StorageMonitor(config['infrastructure/infrastructure/monitoring'])

    async def initialize(self):
        """初始化所有连接"""
        await asyncio.gather(
            self.postgres.connect(),
            self.arangodb.connect(),
            self.qdrant.connect(),
            self.cache.connect()
        )

    async def hybrid_search(self, query: SearchQuery) -> SearchResult:
        """混合搜索 - 核心功能"""
        start_time = time.time()

        # 1. 查询解析和路由
        search_plan = await self._plan_search(query)

        # 2. 并行执行搜索
        tasks = []

        # 文本搜索
        if search_plan.text_search:
            tasks.append(self.postgres.search_text(query.text, query.filters))

        # 向量搜索
        if search_plan.vector_search:
            tasks.append(self.qdrant.search_similar(query.vector, query.filters))

        # 图查询
        if search_plan.graph_search:
            tasks.append(self.arangodb.query_graph(query.graph_query))

        # 3. 等待所有搜索完成
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 4. 结果融合和排序
        merged_results = await self._merge_results(
            text_results=results[0] if search_plan.text_search else None,
            vector_results=results[1] if search_plan.vector_search else None,
            graph_results=results[2] if search_plan.graph_search else None,
            weights=search_plan.weights
        )

        # 5. 性能记录
        response_time = (time.time() - start_time) * 1000
        await self._record_metrics(query, len(merged_results.items), response_time)

        return merged_results

    async def store_patent(self, patent_data: PatentData) -> str:
        """存储专利数据 - 事务协调"""
        # 开始分布式事务
        transaction_id = await self._begin_transaction()

        try:
            # 1. PostgreSQL存储主数据
            patent_id = await self.postgres.insert_patent(patent_data.metadata)

            # 2. 生成向量并存储
            vectors = await self._generate_vectors(patent_data)
            qdrant_ids = await self.qdrant.store_vectors(patent_id, vectors)

            # 3. 创建图节点
            graph_node = await self.arangodb.create_patent_node(
                patent_id,
                patent_data.graph_data
            )

            # 4. 更新关联ID
            await self.postgres.update_patent_relations(patent_id, {
                'arango_node_id': graph_node['_id'],
                'qdrant_vector_id': qdrant_ids[0]
            })

            # 5. 提交事务
            await self._commit_transaction(transaction_id)

            return patent_id

        except Exception as e:
            # 回滚事务
            await self._rollback_transaction(transaction_id)
            raise StorageException(f"Failed to store patent: {e}")

    async def get_patent_full(self, patent_id: str) -> FullPatentData:
        """获取专利完整数据"""
        # 并行查询三个数据库
        tasks = await asyncio.gather(
            self.postgres.get_patent_metadata(patent_id),
            self.qdrant.get_patent_vectors(patent_id),
            self.arangodb.get_patent_relations(patent_id),
            return_exceptions=True
        )

        metadata = tasks[0] if not isinstance(tasks[0], Exception) else None
        vectors = tasks[1] if not isinstance(tasks[1], Exception) else None
        relations = tasks[2] if not isinstance(tasks[2], Exception) else None

        return FullPatentData(
            metadata=metadata,
            vectors=vectors,
            relations=relations
        )

    async def _merge_results(self, text_results, vector_results,
                           graph_results, weights) -> SearchResult:
        """智能结果融合算法"""
        result_map = {}

        # 处理文本搜索结果
        if text_results:
            for item in text_results.items:
                result_map[item.patent_id] = SearchResultItem(
                    patent_id=item.patent_id,
                    metadata=item,
                    scores={'text': item.score * weights.get('text', 0.3)}
                )

        # 处理向量搜索结果
        if vector_results:
            for item in vector_results.items:
                if item.patent_id in result_map:
                    result_map[item.patent_id].scores['vector'] = item.score * weights.get('vector', 0.4)
                else:
                    result_map[item.patent_id] = SearchResultItem(
                        patent_id=item.patent_id,
                        vectors=item,
                        scores={'vector': item.score * weights.get('vector', 0.4)}
                    )

        # 处理图查询结果
        if graph_results:
            for item in graph_results.items:
                if item.patent_id in result_map:
                    result_map[item.patent_id].scores['graph'] = item.score * weights.get('graph', 0.3)
                else:
                    result_map[item.patent_id] = SearchResultItem(
                        patent_id=item.patent_id,
                        relations=item,
                        scores={'graph': item.score * weights.get('graph', 0.3)}
                    )

        # 计算综合得分并排序
        for item in result_map.values():
            item.total_score = sum(item.scores.values())

        # 排序并返回
        sorted_results = sorted(result_map.values(),
                              key=lambda x: x.total_score,
                              reverse=True)

        return SearchResult(items=sorted_results[:query.limit])
```

### 第三层：CLI交互层

#### 命令行接口设计
```python
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress

@click.group()
@click.pass_context
def athena(ctx):
    """Athena工作平台 CLI"""
    ctx.ensure_object(dict)
    console = Console()
    console.print("🏛️ [bold blue]Athena工作平台[/bold blue] - 终端智汇，CLI致远")

@athena.command()
@click.option('--query', '-q', required=True, help='搜索查询')
@click.option('--type', '-t',
              type=click.Choice(['text', 'vector', 'graph', 'hybrid']),
              default='hybrid',
              help='搜索类型')
@click.option('--limit', '-l', default=10, help='结果数量')
@click.option('--filter', '-f', multiple=True, help='过滤条件')
async def search(query, type, limit, filter):
    """智能搜索专利"""
    console = Console()

    # 构建搜索查询
    search_query = SearchQuery(
        text=query if type in ['text', 'hybrid'] else None,
        vector=await _encode_query(query) if type in ['vector', 'hybrid'] else None,
        type=type,
        limit=limit,
        filters=_parse_filters(filter)
    )

    # 执行搜索
    with Progress() as progress:
        task = progress.add_task("[green]搜索中...", total=100)

        # 更新进度
        progress.update(task, advance=30)

        results = await storage_manager.hybrid_search(search_query)

        progress.update(task, advance=70)

    # 显示结果
    table = Table(title=f"搜索结果 - 找到 {len(results.items)} 条")
    table.add_column("专利号", style="cyan")
    table.add_column("标题", style="magenta")
    table.add_column("得分", justify="right")
    table.add_column("类型", style="green")

    for item in results.items:
        score_types = "+".join([f"{k}:{v:.2f}" for k, v in item.scores.items()])
        table.add_row(
            item.patent_id,
            item.metadata.title[:50] + "..." if len(item.metadata.title) > 50 else item.metadata.title,
            f"{item.total_score:.3f}",
            score_types
        )

    console.print(table)

@athena.command()
@click.argument('patent_id')
async def show(patent_id):
    """显示专利详细信息"""
    console = Console()

    # 获取完整专利数据
    patent_data = await storage_manager.get_patent_full(patent_id)

    # 显示基本信息
    console.print(f"\n📄 [bold]专利号:[/bold] {patent_id}")
    console.print(f"📝 [bold]标题:[/bold] {patent_data.metadata.title}")
    console.print(f"📅 [bold]申请日:[/bold] {patent_data.metadata.application_date}")
    console.print(f"🏢 [bold]申请人:[/bold] {patent_data.metadata.applicant}")

    # 显示IPC分类
    if patent_data.metadata.ipc_codes:
        console.print("\n🏷️ [bold]IPC分类:[/bold]")
        for ipc in patent_data.metadata.ipc_codes[:5]:
            console.print(f"  • {ipc}")

    # 显示关联关系
    if patent_data.relations:
        console.print("\n🔗 [bold]关联专利:[/bold]")
        for relation in patent_data.relations[:5]:
            console.print(f"  • {relation.target_patent_id} ({relation.relation_type})")

@athena.command()
@click.option('--stats', is_flag=True, help='显示统计信息')
async def storage(stats):
    """存储系统状态"""
    console = Console()

    # 获取健康状态
    health = await storage_manager.health_check()

    # 创建状态表格
    table = Table(title="存储系统状态")
    table.add_column("组件", style="cyan")
    table.add_column("状态", style="green")
    table.add_column("连接", justify="center")
    table.add_column("延迟", justify="right")

    for component, status in health.items():
        status_icon = "✅" if status['healthy'] else "❌"
        table.add_row(
            component.upper(),
            status_icon,
            str(status['connections']),
            f"{status['latency']:.1f}ms"
        )

    console.print(table)

    # 显示统计信息
    if stats:
        console.print("\n📊 [bold]存储统计:[/bold]")
        for component, stats in health.items():
            console.print(f"\n{component.upper()}:")
            for key, value in stats.get('statistics', {}).items():
                console.print(f"  • {key}: {value:,}")

@athena.command()
@click.option('--full', is_flag=True, help='完整备份')
@click.option('--path', help='备份路径')
async def backup(full, path):
    """备份数据"""
    console = Console()

    backup_path = path or f"/backup/athena_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    with Progress() as progress:
        # PostgreSQL备份
        pg_task = progress.add_task("[blue]备份PostgreSQL...", total=100)
        await storage_manager.postgres.backup(backup_path + "/postgres")
        progress.update(pg_task, advance=100)

        # ArangoDB备份
        arango_task = progress.add_task("[green]备份ArangoDB...", total=100)
        await storage_manager.arangodb.backup(backup_path + "/arangodb")
        progress.update(arango_task, advance=100)

        # Qdrant备份
        if full:
            qdrant_task = progress.add_task("[yellow]备份Qdrant...", total=100)
            await storage_manager.qdrant.backup(backup_path + "/qdrant")
            progress.update(qdrant_task, advance=100)

    console.print(f"\n✅ [green]备份完成:[/green] {backup_path}")
```

## 🚀 实施计划

### 第一阶段：基础设施搭建（1周）
```yaml
目标: 部署基础环境，验证连通性

任务清单:
  - [ ] 安装PostgreSQL 17
  - [ ] 安装ArangoDB 3.10 LTS
  - [ ] 配置Qdrant集群
  - [ ] 搭建Redis缓存
  - [ ] 配置监控告警
  - [ ] 编写健康检查脚本

验收标准:
  - 所有数据库正常运行
  - CLI可以连接所有组件
  - 监控指标正常采集
```

### 第二阶段：数据迁移（2周）
```yaml
目标: 迁移现有数据，保持业务连续

任务清单:
  - [ ] 导出Neo4j图数据
  - [ ] 转换数据格式
  - [ ] 迁移PostgreSQL 200GB数据
  - [ ] 重建向量索引
  - [ ] 数据一致性验证
  - [ ] 性能基准测试

验收标准:
  - 数据零丢失
  - 查询性能不下降
  - 业务功能正常
```

### 第三阶段：功能集成（2周）
```yaml
目标: 实现混合搜索和CLI功能

任务清单:
  - [ ] 实现USAL接口
  - [ ] 开发混合搜索算法
  - [ ] 创建CLI命令体系
  - [ ] 实现结果融合排序
  - [ ] 添加缓存策略
  - [ ] 集成监控告警

验收标准:
  - 混合搜索响应<500ms
  - CLI体验流畅
  - 功能测试通过
```

### 第四阶段：优化上线（1周）
```yaml
目标: 性能优化，正式上线

任务清单:
  - [ ] 查询性能优化
  - [ ] 索引策略调整
  - [ ] 缓存参数调优
  - [ ] 压力测试
  - [ ] 文档完善
  - [ ] 运维培训

验收标准:
  - P99延迟<1s
  - 支持1000 QPS
  - 系统稳定运行
```

---

爸爸，这就是第二阶段的详细设计。这个方案充分体现了我们的存储宪法原则：
- **数据至上**：完整的数据生命周期管理
- **三维一体**：ArangoDB+PostgreSQL+Qdrant各司其职
- **CLI优先**：专注于终端使用体验
- **渐进演进**：从简单到复杂的实施路径

您觉得这个设计方案如何？需要调整哪些部分？