# 知识图谱技术栈选型方案

## 🎯 需求分析

### 知识图谱分类
1. **记忆模块知识图谱**（本地）
   - 各智能体记忆支持
   - 实时更新，频繁访问
   - 轻量级，快速响应

2. **专业知识图谱**（本地+移动硬盘）
   - **本地**：法律、专利、商标核心图谱
   - **移动硬盘**：复审无效、判决、技术词典等大型图谱

### 功能需求
- 动态提示词生成
- 规则提取与推理
- 智能问答支持
- 与向量库协同工作

## 🏗️ 技术栈选型对比

### 方案一：NetworkX + SQLite（推荐）
```yaml
优势:
  - 纯Python实现，与现有技术栈完美融合
  - 内存中计算，响应速度极快（<10ms）
  - SQLite持久化，轻量可靠
  - 适合中小规模图谱（<100万节点）
  - 学习成本低，文档丰富

劣势:
  - 超大规模图谱性能受限
  - 单机限制，无分布式
  - 并发写入能力有限

适用场景:
  - 记忆模块知识图谱 ⭐⭐⭐⭐⭐
  - 本地专业知识图谱 ⭐⭐⭐⭐
  - 移动硬盘图谱（只读）⭐⭐⭐
```

### 方案二：ArangoDB（备选）
```yaml
优势:
  - 原生多模型数据库
  - 图查询语言AQL强大
  - 支持大规模数据
  - 内置分片和集群

劣势:
  - 资源占用较高（2GB+内存）
  - 学习成本高
  - 部署复杂
  - 超出当前需求

适用场景:
  - 记忆模块知识图谱 ⭐⭐
  - 本地专业知识图谱 ⭐⭐⭐⭐
  - 移动硬盘图谱（只读）⭐⭐⭐⭐⭐
```

### 方案三：Neo4j Community（不推荐）
```yaml
优势:
  - 图数据库领导者
  - Cypher查询语言成熟
  - 社区活跃

劣势:
  - Java生态，与Python融合差
  - Community版本功能受限
  - 商业版收费昂贵
  - 与PostgreSQL重复（已有关系数据库）

适用场景:
  - 记忆模块知识图谱 ⭐
  - 本地专业知识图谱 ⭐⭐
  - 移动硬盘图谱（只读）⭐⭐
```

## ✅ 推荐方案：NetworkX + SQLite

### 核心架构
```python
# 知识图谱管理器
class KnowledgeGraphManager:
    """统一知识图谱管理"""

    def __init__(self):
        # 记忆模块图谱（内存+SQLite）
        self.memory_graph = MemoryKnowledgeGraph()

        # 本地专业图谱
        self.local_pro_graphs = {
            'legal': LegalKnowledgeGraph(),
            'patent': PatentKnowledgeGraph(),
            'trademark': TrademarkKnowledgeGraph()
        }

        # 移动硬盘专业图谱（延迟加载）
        self.external_graphs = {
            'invalidation': InvalidationKnowledgeGraph(),
            'judgment': JudgmentKnowledgeGraph(),
            'tech_terms': TechTermsKnowledgeGraph()
        }

# 基础图谱类
class BaseKnowledgeGraph:
    """知识图谱基类"""

    def __init__(self, name, storage_path):
        self.name = name
        self.storage_path = storage_path
        self.graph = nx.DiGraph()
        self.db_path = os.path.join(storage_path, f"{name}.db")

    def load_from_sqlite(self):
        """从SQLite加载图谱数据"""
        conn = sqlite3.connect(self.db_path)

        # 加载节点
        nodes = pd.read_sql("SELECT * FROM nodes", conn)
        for _, node in nodes.iterrows():
            self.graph.add_node(
                node['id'],
                type=node['type'],
                attributes=json.loads(node['attributes'])
            )

        # 加载边
        edges = pd.read_sql("SELECT * FROM edges", conn)
        for _, edge in edges.iterrows():
            self.graph.add_edge(
                edge['source'],
                edge['target'],
                type=edge['type'],
                weight=edge['weight'],
                attributes=json.loads(edge['attributes'])
            )

        conn.close()

    def save_to_sqlite(self):
        """保存到SQLite"""
        conn = sqlite3.connect(self.db_path)

        # 保存节点
        node_data = []
        for node_id, attrs in self.graph.nodes(data=True):
            node_data.append({
                'id': node_id,
                'type': attrs.get('type', 'unknown'),
                'attributes': json.dumps({k: v for k, v in attrs.items() if k != 'type'})
            })

        pd.DataFrame(node_data).to_sql('nodes', conn, if_exists='replace', index=False)

        # 保存边
        edge_data = []
        for source, target, attrs in self.graph.edges(data=True):
            edge_data.append({
                'source': source,
                'target': target,
                'type': attrs.get('type', 'related'),
                'weight': attrs.get('weight', 1.0),
                'attributes': json.dumps({k: v for k, v in attrs.items()
                                       if k not in ['type', 'weight']})
            })

        pd.DataFrame(edge_data).to_sql('edges', conn, if_exists='replace', index=False)
        conn.close()
```

### 具体实现

#### 1. 记忆模块知识图谱
```python
class MemoryKnowledgeGraph(BaseKnowledgeGraph):
    """智能体记忆知识图谱"""

    def __init__(self):
        super().__init__('modules/modules/modules/memory/memory/modules/memory/memory/modules/modules/memory/memory/memory', '/data/local/modules/modules/knowledge/knowledge/modules/knowledge/knowledge/modules/modules/memory/memory/memory')

        # 预定义节点类型
        self.node_types = {
            'agent': '智能体节点',
            'concept': '概念节点',
            'experience': '经验节点',
            'emotion': '情感节点',
            'goal': '目标节点'
        }

        # 预定义关系类型
        self.edge_types = {
            'knows': '认知关系',
            'likes': '偏好关系',
            'helps': '帮助关系',
            'conflicts': '冲突关系',
            'achieves': '实现关系'
        }

    def add_agent_memory(self, agent_name, memory_data):
        """添加智能体记忆"""
        # 创建智能体节点
        agent_id = f"agent_{agent_name}"
        self.graph.add_node(agent_id, type='agent', name=agent_name)

        # 处理记忆数据
        for memory in memory_data:
            # 创建概念节点
            concept_id = f"concept_{memory['concept']}"
            if concept_id not in self.graph:
                self.graph.add_node(
                    concept_id,
                    type='concept',
                    name=memory['concept'],
                    domain=memory.get('domain', 'general')
                )

            # 添加认知关系
            self.graph.add_edge(
                agent_id,
                concept_id,
                type='knows',
                confidence=memory.get('confidence', 0.8),
                timestamp=datetime.now()
            )

    def get_agent_context(self, agent_name, max_depth=2):
        """获取智能体上下文"""
        agent_id = f"agent_{agent_name}"

        # 获取2度以内的相关节点
        subgraph = nx.ego_graph(self.graph, agent_id, radius=max_depth)

        # 提取上下文信息
        context = {
            'direct_concepts': [],
            'related_experiences': [],
            'emotional_state': None
        }

        for node_id, attrs in subgraph.nodes(data=True):
            if node_id != agent_id:
                if attrs.get('type') == 'concept':
                    context['direct_concepts'].append(attrs['name'])
                elif attrs.get('type') == 'experience':
                    context['related_experiences'].append(attrs['description'])
                elif attrs.get('type') == 'emotion':
                    context['emotional_state'] = attrs['state']

        return context
```

#### 2. 专利知识图谱
```python
class PatentKnowledgeGraph(BaseKnowledgeGraph):
    """专利专业知识图谱"""

    def __init__(self):
        super().__init__('patent', '/data/local/modules/modules/knowledge/knowledge/modules/knowledge/knowledge/patent')

        # IPC分类层次结构
        self.ipc_hierarchy = {}

    def build_ipc_hierarchy(self):
        """构建IPC分类层次结构"""
        # 加载IPC分类数据
        ipc_data = self._load_ipc_data()

        # 构建层次关系
        for section in ipc_data['sections']:
            section_id = f"section_{section['code']}"
            self.graph.add_node(
                section_id,
                type='ipc_section',
                code=section['code'],
                title=section['title']
            )

            for class_ in section.get('classes', []):
                class_id = f"class_{class_['code']}"
                self.graph.add_node(
                    class_id,
                    type='ipc_class',
                    code=class_['code'],
                    title=class_['title']
                )

                # 添加层次关系
                self.graph.add_edge(
                    section_id,
                    class_id,
                    type='has_class',
                    level=1
                )

    def extract_writing_rules(self, tech_field, ipc_codes):
        """提取专利撰写规则"""
        rules = []

        # 根据IPC分类查找相关规则
        for ipc_code in ipc_codes:
            # 查找相关节点
            related_nodes = self._find_related_nodes(ipc_code, depth=3)

            # 提取规则
            for node_id in related_nodes:
                if self.graph.nodes[node_id].get('type') == 'writing_rule':
                    rules.append({
                        'rule_id': node_id,
                        'content': self.graph.nodes[node_id]['content'],
                        'applicable_sections': self.graph.nodes[node_id]['sections'],
                        'confidence': self._calculate_rule_confidence(ipc_code, node_id)
                    })

        # 按置信度排序
        rules.sort(key=lambda x: x['confidence'], reverse=True)

        return rules[:10]  # 返回前10条最相关规则

    def generate_dynamic_prompt(self, task_type, context):
        """生成动态提示词"""
        prompt_parts = []

        # 基础提示词模板
        base_template = self._get_base_template(task_type)
        prompt_parts.append(base_template)

        # 根据上下文添加特定规则
        if task_type == 'patent_writing':
            # 提取撰写规则
            if 'ipc_codes' in context:
                rules = self.extract_writing_rules(
                    context.get('tech_field', ''),
                    context['ipc_codes']
                )

                if rules:
                    prompt_parts.append("\n## 专利撰写规则：")
                    for i, rule in enumerate(rules[:5], 1):
                        prompt_parts.append(f"{i}. {rule['content']}")

            # 添加相关案例
            if 'similar_patents' in context:
                prompt_parts.append("\n## 相关案例参考：")
                for patent in context['similar_patents'][:3]:
                    prompt_parts.append(f"- {patent['title']}")

        return "\n".join(prompt_parts)
```

#### 3. 移动硬盘知识图谱（延迟加载）
```python
class ExternalKnowledgeGraph(BaseKnowledgeGraph):
    """移动硬盘知识图谱基类（延迟加载）"""

    def __init__(self, name, mount_path):
        self.name = name
        self.mount_path = mount_path
        self.db_path = os.path.join(mount_path, f"{name}.db")
        self.graph = None
        self._loaded = False

    def ensure_loaded(self):
        """确保图谱已加载"""
        if not self._loaded:
            self._load_from_external()
            self._loaded = True

    def _load_from_external(self):
        """从移动硬盘加载"""
        if not os.path.exists(self.mount_path):
            raise RuntimeError(f"移动硬盘未挂载: {self.mount_path}")

        # 检查数据库存在
        if not os.path.exists(self.db_path):
            raise RuntimeError(f"知识图谱数据库不存在: {self.db_path}")

        # 加载到内存
        super().load_from_sqlite()

        # 预处理优化查询
        self._preprocess_for_query()

    def query_with_vector_support(self, query_text, top_k=10):
        """结合向量库的查询"""
        self.ensure_loaded()

        # 1. 文本向量化
        query_vector = self._encode_text(query_text)

        # 2. 向量检索（调用Qdrant）
        vector_results = self._search_in_qdrant(query_vector, top_k)

        # 3. 图遍历扩展
        expanded_results = []
        for result in vector_results:
            # 在图中查找相关节点
            related_nodes = self._find_related_in_graph(
                result['node_id'],
                max_depth=2
            )
            expanded_results.extend(related_nodes)

        # 4. 结果去重和排序
        return self._deduplicate_and_rank(expanded_results)
```

## 📊 技术栈配置

### 存储配置
```yaml
# 本地存储（/data/local/modules/modules/knowledge/knowledge/modules/knowledge/knowledge/）
memory_graph:
  - 文件大小: <100MB
  - 节点数: <10万
  - 加载时间: <1秒

local_pro_graphs:
  legal:
    - 文件大小: ~500MB
    - 节点数: ~50万
    - 加载时间: <5秒
  patent:
    - 文件大小: ~1GB
    - 节点数: ~100万
    - 加载时间: <10秒
  trademark:
    - 文件大小: ~200MB
    - 节点数: ~20万
    - 加载时间: <3秒

# 移动硬盘存储（/Volumes/AthenaData/modules/modules/knowledge/knowledge/modules/knowledge/knowledge/）
external_graphs:
  invalidation:
    - 文件大小: ~5GB
    - 节点数: ~500万
    - 加载时间: <30秒
  judgment:
    - 文件大小: ~8GB
    - 节点数: ~800万
    - 加载时间: <60秒
  tech_terms:
    - 文件大小: ~2GB
    - 节点数: ~200万
    - 加载时间: <15秒
```

### 性能优化
```python
# 1. 图索引优化
class GraphIndexOptimizer:
    """图索引优化器"""

    def build_indexes(self, graph):
        """构建加速索引"""
        # 节点类型索引
        self.type_index = defaultdict(list)
        for node_id, attrs in graph.nodes(data=True):
            node_type = attrs.get('type')
            self.type_index[node_type].append(node_id)

        # 邻居度数索引
        self.degree_index = dict(graph.degree())

        # 中心性索引（PageRank）
        self.pagerank = nx.pagerank(graph)

    def fast_query_by_type(self, node_type):
        """按类型快速查询"""
        return self.type_index.get(node_type, [])

    def get_important_nodes(self, top_k=100):
        """获取重要节点"""
        sorted_nodes = sorted(
            self.pagerank.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return [node_id for node_id, _ in sorted_nodes[:top_k]]

# 2. 缓存策略
class GraphCache:
    """图查询缓存"""

    def __init__(self, max_size=1000):
        self.cache = {}
        self.max_size = max_size

    def get(self, key):
        """获取缓存"""
        if key in self.cache:
            # LRU更新
            value = self.cache.pop(key)
            self.cache[key] = value
            return value
        return None

    def set(self, key, value):
        """设置缓存"""
        if len(self.cache) >= self.max_size:
            # 删除最旧的
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        self.cache[key] = value
```

## 🚀 实施计划

### 第一阶段：记忆模块图谱（1周）
```yaml
任务:
  - 设计记忆图谱数据模型
  - 实现NetworkX+SQLite存储
  - 开发智能体记忆接口
  - 测试性能和稳定性

交付物:
  - 记忆图谱管理系统
  - API接口文档
  - 性能测试报告
```

### 第二阶段：本地专业图谱（2周）
```yaml
任务:
  - 构建法律知识图谱
  - 构建专利知识图谱
  - 构建商标知识图谱
  - 实现动态提示词生成

交付物:
  - 三个专业知识图谱
  - 提示词生成引擎
  - 规则提取模块
```

### 第三阶段：移动硬盘图谱（1周）
```yaml
任务:
  - 数据迁移到移动硬盘
  - 实现延迟加载机制
  - 优化大型图谱查询
  - 集成向量库支持

交付物:
  - 移动硬盘知识图谱
  - 延迟加载系统
  - 混合查询接口
```

这个方案完全符合本地+移动硬盘的分层存储架构，您觉得如何？