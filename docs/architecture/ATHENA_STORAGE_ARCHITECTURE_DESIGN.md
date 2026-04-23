# Athena工作平台存储架构设计

## 🏛️ 系统总览

### 技术栈
- **PostgreSQL** - 关系数据库
- **Qdrant** - 向量数据库
- **ArangoDB** - 图数据库（多数据库支持）
- **文件系统** - 文档存储

### 架构图
```
                    ┌─────────────────────────────────────┐
                    │        Athena CLI终端                │
                    └─────────────┬───────────────────────┘
                                  │
                    ┌─────────────▼───────────────────────┐
                    │       统一访问层 (UAL)               │
                    │  - 路由分发                          │
                    │  - 结果融合                          │
                    │  - 缓存管理                          │
                    │  - 事务协调                          │
                    └─────────────┬───────────────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
    ┌─────▼─────┐         ┌──────▼───────┐       ┌──────▼──────┐
    │ PostgreSQL│         │    Qdrant    │       │  ArangoDB   │
    │           │         │             │       │             │
    └─────┬─────┘         └──────┬───────┘       └──────┬──────┘
          │                       │                       │
          ├───────────────────────┼───────────────────────┤
          │                       │                       │
    ┌─────▼─────┐         ┌──────▼───────┐       ┌──────▼──────┐
    │ 本地存储   │         │   本地存储    │       │  本地存储   │
    │           │         │             │       │             │
    └───────────┘         └─────────────┘       └─────────────┘
          │                       │                       │
          └───────────────────────┼───────────────────────┘
                                  │
                    ┌─────────────▼───────────────────────┐
                    │      移动硬盘存储管理器               │
                    │  - 自动检测                          │
                    │  - 按需启动                          │
                    │  - 健康检查                          │
                    └─────────────┬───────────────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
    ┌─────▼─────┐         ┌──────▼───────┐       ┌──────▼──────┐
    │ PostgreSQL│         │    Qdrant    │       │  ArangoDB   │
    │(移动硬盘) │         │ (移动硬盘)   │       │ (移动硬盘)  │
    └───────────┘         └─────────────┘       └─────────────┘
```

## 📊 数据库详细设计

### 1. PostgreSQL 实例配置

#### 本地实例（端口5432）
```yaml
数据库列表:
  athena_business:
    描述: 宝宸业务数据
    表结构:
      patents: 专利数据
      finances: 财务数据
      trademarks: 商标数据
      tasks: 任务管理（项目共享）
      clients: 客户信息
      cases: 案卷管理

  athena_memory:
    描述: 记忆模块数据
    表结构:
      contexts: 对话上下文
      sessions: 会话记录
      knowledge: 学习知识
      decisions: 决策背景

  athena_personal:
    描述: 爸爸个人事务
    表结构:
      schedules: 日程安排
      notes: 个人笔记
      contacts: 联系人
      preferences: 个人偏好
```

#### 移动硬盘实例（端口5433）
```yaml
数据库列表:
  china_patents:
    描述: 中国专利全库
    数据量: ~400GB
    更新频率: 月度

  access_trigger:
    触发条件: 检测到移动硬盘连接 /Volumes/AthenaData
    启动脚本: dev/scripts/start_external_db.sh
```

### 2. Qdrant 实例配置

#### 本地实例（端口6333）
```yaml
集合列表:
  legal_vectors:
    维度: 768
    内容: 法律条文向量

  patent_vectors:
    维度: 768
    内容: 专利文本向量

  trademark_vectors:
    维度: 768
    内容: 商标相关向量

  prompt_vectors:
    维度: 1024
    内容: 动态提示词向量
```

#### 移动硬盘实例（端口6334）
```yaml
集合列表:
  invalidation_vectors:
    维度: 768
    数量: 9万条
    内容: 复审无效向量

  judgment_vectors:
    维度: 768
    数量: 9万条
    内容: 判决文书向量

  tech_term_vectors:
    维度: 1024
    内容: 技术术语向量
```

### 3. ArangoDB 实例配置

#### 本地实例（端口8529）
```yaml
数据库列表:
  legal_knowledge:
    集合:
      - legal_nodes: 法律节点
      - case_relations: 案例关系
      - citation_edges: 引用关系

  patent_knowledge:
    集合:
      - patent_nodes: 专利节点
      - feature_nodes: 技术特征节点
      - problem_nodes: 问题节点
      - effect_nodes: 效果节点
      - patent_relations: 专利关系

  trademark_knowledge:
    集合:
      - trademark_nodes: 商标节点
      - category_nodes: 分类节点
      - company_nodes: 公司节点
      - trademark_relations: 商标关系

  rule_extraction:
    集合:
      - rule_nodes: 规则节点
      - pattern_nodes: 模式节点
      - rule_relations: 规则关系
```

#### 移动硬盘实例（端口8530）
```yaml
数据库列表:
  invalidation_knowledge:
    集合:
      - invalidation_nodes: 复审无效节点
      - argument_nodes: 论点节点
      - invalidation_relations: 无效关系

  judgment_knowledge:
    集合:
      - judgment_nodes: 判决节点
      - fact_nodes: 事实节点
      - judgment_relations: 判决关系

  tech_term_knowledge:
    集合:
      - tech_nodes: 技术节点
      - domain_nodes: 领域节点
      - tech_relations: 技术关系
```

## 🔧 核心组件设计

### 1. 统一访问层 (UAL)

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import asyncio

class StorageManager:
    """统一存储管理器"""

    def __init__(self):
        # 本地数据库连接
        self.pg_local = PostgreSQLConnection("localhost", 5432)
        self.qdrant_local = QdrantConnection("localhost", 6333)
        self.arango_local = ArangoConnection("localhost", 8529)

        # 移动硬盘管理器
        self.external_manager = ExternalStorageManager()

        # 缓存层
        self.cache = CacheManager()

        # 搜索引擎
        self.search_engine = UnifiedSearchEngine()

    async def initialize(self):
        """初始化所有连接"""
        await self.pg_local.connect()
        await self.qdrant_local.connect()
        await self.arango_local.connect()
        await self.external_manager.initialize()

    async def search(self, query: SearchQuery) -> SearchResult:
        """统一搜索接口"""
        # 1. 检查是否需要外部数据
        needs_external = self._check_external_need(query)

        if needs_external:
            await self.external_manager.ensure_databases()

        # 2. 并行搜索各个数据库
        tasks = []

        # PostgreSQL搜索
        if query.include_metadata:
            tasks.append(self._search_postgresql(query))

        # Qdrant向量搜索
        if query.include_vectors:
            tasks.append(self._search_qdrant(query))

        # ArangoDB图搜索
        if query.include_graph:
            tasks.append(self._search_arangodb(query))

        # 3. 等待所有搜索完成
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 4. 结果融合和排序
        return self._merge_results(results, query)

class ExternalStorageManager:
    """移动硬盘存储管理器"""

    def __init__(self):
        self.mount_path = "/Volumes/AthenaData"
        self.pg_external = None
        self.qdrant_external = None
        self.arango_external = None
        self._mounted = False
        self._health_check_interval = 3600  # 1小时检查一次

    async def initialize(self):
        """初始化监控"""
        # 启动定时健康检查
        asyncio.create_task(self._health_monitor())

    async def _health_monitor(self):
        """健康监控循环"""
        while True:
            try:
                is_mounted = os.path.exists(self.mount_path)

                if is_mounted and not self._mounted:
                    # 刚插入，启动数据库
                    await self._start_external_databases()
                    self._mounted = True

                elif not is_mounted and self._mounted:
                    # 已移除，停止数据库
                    await self._stop_external_databases()
                    self._mounted = False

                # 健康检查
                if self._mounted:
                    await self._check_databases_health()

            except Exception as e:
                logging.error(f"Storage monitor error: {e}")

            await asyncio.sleep(self._health_check_interval)

    async def ensure_databases(self):
        """确保数据库已启动"""
        if not self._mounted:
            await self._wait_for_mount()
            await self._start_external_databases()

    async def _start_external_databases(self):
        """启动移动硬盘数据库"""
        logging.info("Starting external databases...")

        # 启动PostgreSQL
        pg_data = os.path.join(self.mount_path, "postgresql")
        if os.path.exists(pg_data):
            self.pg_external = PostgreSQLConnection("localhost", 5433)
            await self.pg_external.connect()
            logging.info("External PostgreSQL started")

        # 启动Qdrant
        qdrant_data = os.path.join(self.mount_path, "qdrant")
        if os.path.exists(qdrant_data):
            self.qdrant_external = QdrantConnection("localhost", 6334)
            await self.qdrant_external.connect()
            logging.info("External Qdrant started")

        # 启动ArangoDB
        arango_data = os.path.join(self.mount_path, "arangodb")
        if os.path.exists(arango_data):
            self.arango_external = ArangoConnection("localhost", 8530)
            await self.arango_external.connect()
            logging.info("External ArangoDB started")

    async def _check_databases_health(self):
        """检查数据库健康状态"""
        health_status = {
            'postgresql': False,
            'qdrant': False,
            'arangodb': False
        }

        # PostgreSQL健康检查
        if self.pg_external:
            try:
                await self.pg_external.execute("SELECT 1")
                health_status['postgresql'] = True
            except:
                logging.error("External PostgreSQL health check failed")

        # Qdrant健康检查
        if self.qdrant_external:
            try:
                collections = await self.qdrant_external.list_collections()
                health_status['qdrant'] = len(collections) > 0
            except:
                logging.error("External Qdrant health check failed")

        # ArangoDB健康检查
        if self.arango_external:
            try:
                databases = await self.arango_external.list_databases()
                health_status['arangodb'] = len(databases) > 0
            except:
                logging.error("External ArangoDB health check failed")

        return health_status
```

### 2. 数据导入模块

```python
class ExcelDataImporter:
    """Excel数据导入器"""

    def __init__(self, storage_manager: StorageManager):
        self.storage = storage_manager

    async def import_patent_excel(self, file_path: str):
        """导入专利Excel数据"""
        import pandas as pd

        df = pd.read_excel(file_path)

        # 数据清洗和转换
        patents = []
        for _, row in df.iterrows():
            patent = {
                'patent_id': row['专利号'],
                'title': row['标题'],
                'application_date': row['申请日'],
                'applicant': row['申请人'],
                'inventor': row['发明人'],
                'ipc_code': row.get('IPC分类号', ''),
                'abstract': row.get('摘要', '')
            }
            patents.append(patent)

        # 批量插入数据库
        await self.storage.pg_local.bulk_insert(
            "athena_business.patents",
            patents
        )

        # 创建向量并存储到Qdrant
        for patent in patents:
            # 生成向量
            text = patent['title'] + ' ' + patent.get('abstract', '')
            vector = await self._encode_text(text)

            # 存储到向量库
            await self.storage.qdrant_local.upsert(
                collection="patent_vectors",
                points=[{
                    "id": patent['patent_id'],
                    "vector": vector,
                    "payload": {
                        "patent_id": patent['patent_id'],
                        "title": patent['title']
                    }
                }]
            )

        logging.info(f"Imported {len(patents)} patents")

    async def import_financial_excel(self, file_path: str):
        """导入财务Excel数据（银行明细）"""
        import pandas as pd

        df = pd.read_excel(file_path)

        # 数据清洗
        records = []
        for _, row in df.iterrows():
            record = {
                'transaction_date': row['交易日期'],
                'description': row['交易描述'],
                'amount': float(row['金额']),
                'balance': float(row.get('余额', 0)),
                'transaction_type': row.get('交易类型', ''),
                'account': row.get('账户', ''),
                'imported_at': datetime.now()
            }
            records.append(record)

        # 批量插入
        await self.storage.pg_local.bulk_insert(
            "athena_business.finances",
            records
        )

        logging.info(f"Imported {len(records)} financial records")

class DataConflictResolver:
    """数据冲突解决器"""

    def __init__(self, storage_manager: StorageManager):
        self.storage = storage_manager
        self.conflict_resolution = {
            'business': 'local_wins',  # 本地上传为准
            'financial': 'local_wins',  # 本地上传为准
            'tasks': 'local_wins'       # 本地上传为准
        }

    async def resolve_conflict(self, data_type: str, local_data: Dict, remote_data: Dict):
        """解决数据冲突"""
        resolution = self.conflict_resolution.get(data_type, 'local_wins')

        if resolution == 'local_wins':
            # 本地数据为准，更新远程
            await self._update_remote(data_type, local_data)
            return local_data
        else:
            # 其他策略可以根据需要添加
            return local_data

    async def _update_remote(self, data_type: str, data: Dict):
        """更新远程数据"""
        # 实现更新逻辑
        pass

    async def import_trademark_excel(self, file_path: str):
        """导入商标Excel数据"""
        import pandas as pd

        df = pd.read_excel(file_path)

        records = []
        for _, row in df.iterrows():
            record = {
                'trademark_id': row.get('商标号', ''),
                'name': row['商标名称'],
                'applicant': row['申请人'],
                'class': row.get('类别', ''),
                'application_date': row.get('申请日', ''),
                'status': row.get('状态', ''),
                'imported_at': datetime.now()
            }
            records.append(record)

        await self.storage.pg_local.bulk_insert(
            "athena_business.trademarks",
            records
        )

        logging.info(f"Imported {len(records)} trademarks")
```

### 3. 跨库搜索引擎

```python
class UnifiedSearchEngine:
    """统一搜索引擎"""

    def __init__(self, storage_manager: StorageManager):
        self.storage = storage_manager

    async def search_patents(self, query: str, options: Dict) -> SearchResult:
        """专利搜索（可能跨本地和移动硬盘）"""
        results = []

        # 1. 本地搜索
        local_results = await self._search_local_patents(query, options)
        results.extend(local_results)

        # 2. 如果需要，搜索移动硬盘的中国专利库
        if options.get('include_china_patents', False):
            await self.storage.external_manager.ensure_databases()
            if self.storage.external_manager.pg_external:
                external_results = await self._search_china_patents(query, options)
                results.extend(external_results)

        # 3. 结果排序和去重
        return self._process_patent_results(results)

    async def extract_dynamic_prompt(self, context: Dict) -> str:
        """提取动态提示词"""
        prompt_parts = []

        # 1. 根据业务类型查询相关知识
        if context.get('business_type') == 'patent_writing':
            # 查询本地专利知识图谱
            patent_rules = await self._extract_patent_rules(context)
            prompt_parts.extend(patent_rules)

            # 如果移动硬盘连接，查询大型知识库
            if self.storage.external_manager._mounted:
                invalidation_rules = await self._extract_invalidation_rules(context)
                prompt_parts.extend(invalidation_rules)

        elif context.get('business_type') == 'trademark':
            trademark_rules = await self._extract_trademark_rules(context)
            prompt_parts.extend(trademark_rules)

        elif context.get('business_type') == 'legal':
            # 查询法律知识图谱
            legal_rules = await self._extract_legal_rules(context)
            prompt_parts.extend(legal_rules)

            # 如果移动硬盘连接，查询判决文书
            if self.storage.external_manager._mounted:
                judgment_rules = await self._extract_judgment_rules(context)
                prompt_parts.extend(judgment_rules)

    async def handle_concurrent_access(self, operation: str, data: Dict):
        """处理并发访问"""
        # 使用PostgreSQL的事务锁机制
        async with self.storage.pg_local.transaction() as tx:
            # 检查是否有冲突
            if await self._check_conflict(tx, operation, data):
                # 以本地上传为准
                await self._apply_local_wins(tx, operation, data)

            # 执行操作
            await tx.execute(operation, data)

        # 2. 整合提示词
        return self._format_prompt(prompt_parts)

    async def search_by_context(self, query: str, user_context: Dict) -> SearchResult:
        """基于上下文的搜索"""
        # 根据用户身份和当前任务调整搜索策略
        if user_context.get('role') == 'lawyer':
            # 律师：优先搜索法律相关的
            return await self._legal_priority_search(query, user_context)
        elif user_context.get('role') == 'agent':
            # 客户端：优先搜索业务数据
            return await self._business_priority_search(query, user_context)
        elif user_context.get('role') == 'admin':
            # 爸爸：全库搜索
            return await self._full_search(query, user_context)
```

## 🚀 部署配置

### Docker Compose 配置
```yaml
version: '3.8'

services:
  # 本地PostgreSQL
  postgresql-local:
    image: postgres:17
    container_name: athena-pg-local
    environment:
      POSTGRES_USER: athena
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: athena
    ports:
      - "5432:5432"
    volumes:
      - ./data/postgresql:/var/lib/postgresql/data
      - ./dev/scripts/init_postgres.sql:/docker-entrypoint-initdb.d/init.sql
    command: postgres -c shared_buffers=256MB -c max_connections=200

  # 本地Qdrant
  qdrant-local:
    image: qdrant/qdrant:latest
    container_name: athena-qdrant-local
    ports:
      - "6333:6333"
    volumes:
      - ./data/qdrant:/qdrant/storage
    environment:
      QDRANT__SERVICE__HTTP_PORT: 6333

  # 本地ArangoDB
  arangodb-local:
    image: arangodb/arangodb:3.10.9
    container_name: athena-arango-local
    environment:
      ARANGO_ROOT_PASSWORD: ${ARANGO_PASSWORD}
    ports:
      - "8529:8529"
    volumes:
      - ./data/arangodb:/var/lib/arangodb3
      - ./dev/scripts/init_arango.js:/docker-entrypoint-initdb.d/init.js
    command: arangod --server.endpoint tcp://0.0.0.0:8529

  # Redis缓存
  redis:
    image: redis:7-alpine
    container_name: athena-redis
    ports:
      - "6379:6379"
    volumes:
      - ./data/redis:/data
    command: redis-server --appendonly yes

  # Athena应用
  athena-app:
    build: .
    container_name: athena-app
    depends_on:
      - postgresql-local
      - qdrant-local
      - arangodb-local
      - redis
    volumes:
      - ./data/documents:/data/documents
      - /Volumes/AthenaData:/external:shared  # 移动硬盘挂载
    environment:
      - PYTHONPATH=/app
      - DB_PASSWORD=${DB_PASSWORD}
      - ARANGO_PASSWORD=${ARANGO_PASSWORD}
    command: python main.py
```

## 📋 实施计划

### 第一周：基础设施
- [x] 搭建Docker环境
- [x] 配置三个数据库实例
- [x] 实现基础连接模块
- [x] 移动硬盘检测机制

### 第二周：核心功能
- [ ] 统一访问层实现
- [ ] Excel数据导入功能
- [ ] 基础搜索功能
- [ ] 记忆模块实现

### 第三周：高级功能
- [ ] 跨库搜索实现
- [ ] 动态提示词提取
- [ ] 任务管理系统
- [ ] 个人事务管理

### 第四周：测试优化
- [ ] 性能测试和优化
- [ ] 备份恢复机制
- [ ] 监控告警系统
- [ ] 文档完善

这个架构设计完全满足您的需求！可以开始实施了。