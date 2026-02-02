# 多知识图谱架构设计方案

## 🎯 核心需求分析

### 知识图谱的双重作用
1. **核心知识图谱** - 生成动态提示词和业务规则
2. **业务知识图谱** - 支撑专利创造性分析等具体业务

### 多图谱独立性需求
- 专利知识图谱：问题-特征-效果三元组
- 商标知识图谱：商标分类、使用场景、法律状态
- 法律知识图谱：法条引用、案例关联
- 技术图谱：技术方案、技术演进
- 各图谱之间保持相对独立，不强求完美连接

## 🏗️ 技术架构设计

### 架构选择：ArangoDB多数据库方案

```yaml
选择理由:
  ✅ 原生支持多数据库
  ✅ 每个数据库独立命名空间
  ✅ 查询隔离，互不影响
  ✅ 可以单独备份每个知识图谱
  ✅ Python集成良好

数据库规划:
  - athena_patent_db: 专利知识图谱
  - athena_trademark_db: 商标知识图谱
  - athena_legal_db: 法律知识图谱
  - athena_tech_db: 技术知识图谱
  - athena_memory_db: 记忆模块图谱
```

## 📊 具体图谱设计

### 1. 专利知识图谱（核心）

#### 数据模型
```yaml
专利问题-特征-效果图谱:
  nodes:
    - PatentNode: 专利节点
    - ProblemNode: 技术问题
    - FeatureNode: 技术特征
    - EffectNode: 技术效果
    - SolutionNode: 技术方案

  edges:
    - SOLVES: 专利解决问题
    - HAS_FEATURE: 方案包含特征
    - ACHIEVES: 特征达到效果
    - IMPROVES: 改进效果
    - SIMILAR_TO: 特征相似
    - REPLACES: 特征替代
```

#### ArangoDB实现
```javascript
// 专利知识图谱 - ArangoDB数据结构
{
  // 数据库: athena_patent_db

  // 集合: patents
  "apps/apps/patents": {
    "_key": "patent_202310000001",
    "type": "PatentNode",
    "title": "一种改进的图像处理方法",
    "patent_id": "CN202310000001",
    "apply_date": "2023-01-01",
    "ipc_codes": ["G06K9/00", "G06T7/00"],
    "metadata": {
      "inventor": ["张三", "李四"],
      "assignee": "某科技公司"
    }
  },

  // 集合: technical_problems
  "problems": {
    "_key": "problem_001",
    "type": "ProblemNode",
    "description": "图像处理速度慢",
    "domain": "图像处理",
    "severity": "high"
  },

  // 集合: technical_features
  "features": {
    "_key": "feature_001",
    "type": "FeatureNode",
    "name": "并行处理算法",
    "category": "算法优化",
    "parameters": {
      "thread_count": 8,
      "cache_size": "64MB"
    }
  },

  // 集合: effects
  "effects": {
    "_key": "effect_001",
    "type": "EffectNode",
    "name": "处理速度提升",
    "metric": "处理时间",
    "value": "50%提升",
    "unit": "percentage"
  }
}

// 关系边集合
"patent_relations": {
  "_from": "apps/patents/patent_202310000001",
  "_to": "problems/problem_001",
  "type": "SOLVES",
  "confidence": 0.95,
  "extracted_from": "说明书第[0023]段"
},

{
  "_from": "apps/patents/patent_202310000001",
  "_to": "features/feature_001",
  "type": "HAS_FEATURE",
  "importance": "main",
  "novelty_score": 0.8
},

{
  "_from": "features/feature_001",
  "_to": "effects/effect_001",
  "type": "ACHIEVES",
  "causality_strength": 0.9
}
```

#### Python访问接口
```python
from arango import ArangoClient

class PatentKnowledgeGraph:
    """专利知识图谱管理器"""

    def __init__(self, arango_url: str, username: str, password: str):
        self.client = ArangoClient(arango_url)
        self.db = self.client.db('athena_patent_db', username=username, password=password)

    def extract_patent_triples(self, patent_id: str) -> Dict:
        """提取专利的问题-特征-效果三元组"""

        # 查询专利节点
        patent = self.db.collection('apps/apps/patents').get(patent_id)

        # 查询相关的问题
        problems = self.db.aql.execute("""
            FOR problem IN 1..1 OUTBOUND @patent_id GRAPH 'patent_graph'
            FILTER edge.type == 'SOLVES'
            RETURN {
                problem: problem,
                confidence: edge.confidence
            }
        """, bind_vars={'patent_id': f'apps/patents/{patent_id}'})

        # 查询技术特征
        features = self.db.aql.execute("""
            FOR feature IN 1..1 OUTBOUND @patent_id GRAPH 'patent_graph'
            FILTER edge.type == 'HAS_FEATURE'
            RETURN {
                feature: feature,
                importance: edge.importance,
                novelty_score: edge.novelty_score
            }
        """, bind_vars={'patent_id': f'apps/patents/{patent_id}'})

        # 查询技术效果
        effects = self.db.aql.execute("""
            FOR v, e IN 2..2 OUTBOUND @patent_id GRAPH 'patent_graph'
            FILTER e.type == 'ACHIEVES'
            RETURN {
                feature: v[0],
                effect: v[1],
                causality_strength: e.causality_strength
            }
        """, bind_vars={'patent_id': f'apps/patents/{patent_id}'})

        return {
            'patent': patent,
            'problems': list(problems),
            'features': list(features),
            'effects': list(effects)
        }

    def compare_two_patents(self, patent1_id: str, patent2_id: str) -> Dict:
        """对比两个专利的技术方案"""

        # 获取两个专利的三元组
        triple1 = self.extract_patent_triples(patent1_id)
        triple2 = self.extract_patent_triples(patent2_id)

        # 特征相似度计算
        feature_similarity = self._calculate_feature_similarity(
            triple1['features'],
            triple2['features']
        )

        # 效果相似度计算
        effect_similarity = self._calculate_effect_similarity(
            triple1['effects'],
            triple2['effects']
        )

        # 问题相似度计算
        problem_similarity = self._calculate_problem_similarity(
            triple1['problems'],
            triple2['problems']
        )

        # 综合相似度
        overall_similarity = (
            feature_similarity * 0.5 +
            effect_similarity * 0.3 +
            problem_similarity * 0.2
        )

        return {
            'similarity_score': overall_similarity,
            'feature_similarity': feature_similarity,
            'effect_similarity': effect_similarity,
            'problem_similarity': problem_similarity,
            'shared_features': self._find_shared_features(triple1, triple2),
            'unique_features_patent1': self._find_unique_features(triple1, triple2),
            'unique_features_patent2': self._find_unique_features(triple2, triple1)
        }

    def generate_dynamic_prompt(self, task_type: str, context: Dict) -> str:
        """基于知识图谱生成动态提示词"""

        if task_type == 'patent_writing':
            # 提取相关技术特征
            tech_domain = context.get('tech_domain', '')
            relevant_features = self.db.aql.execute("""
                FOR feature IN features
                FILTER feature.domain == @domain OR feature.category == @domain
                SORT feature.usage_count DESC
                LIMIT 10
                RETURN feature
            """, bind_vars={'domain': tech_domain})

            # 构建提示词
            prompt_parts = [
                "基于专利知识图谱分析，建议关注以下技术特征：",
                ""
            ]

            for feature in relevant_features:
                prompt_parts.append(f"• {feature['name']}: {feature.get('description', '')}")

            prompt_parts.append("")
            prompt_parts.append("相关的技术效果：")

            # 查询相关效果
            effects = self.db.aql.execute("""
                FOR v, e IN 1..1 OUTBOUND @features GRAPH 'patent_graph'
                FILTER e.type == 'ACHIEVES'
                RETURN DISTINCT v
            """, bind_vars={'features': [f['id'] for f in relevant_features]})

            for effect in effects:
                prompt_parts.append(f"• {effect['name']}")

            return "\n".join(prompt_parts)
```

### 2. 商标知识图谱（独立）

#### 数据模型
```yaml
商标知识图谱:
  nodes:
    - TrademarkNode: 商标本身
    - CategoryNode: 商品/服务类别
    - CompanyNode: 申请主体
    - ClassNode: Nice分类
    - UsageNode: 使用场景
    - LegalStatusNode: 法律状态

  edges:
    - BELONGS_TO: 商标属于某类
    - APPLIED_BY: 公司申请
    - USED_IN: 使用场景
    - TRANSITION_TO: 状态变更
    - OPPOSES: 异议关系
    - LICENSED_TO: 许可关系
```

#### ArangoDB实现
```javascript
// 商标知识图谱 - 数据库: athena_trademark_db

{
  "_key": "trademark_tm001",
  "type": "TrademarkNode",
  "name": "ABC",
  "registration_number": "TM001",
  "class": "第9类",
  "application_date": "2020-01-01",
  "status": "registered"
}

{
  "_key": "company_a",
  "type": "CompanyNode",
  "name": "ABC科技有限公司",
  "jurisdiction": "中国大陆"
}

{
  "_key": "class_9",
  "type": "ClassNode",
  "nice_class": 9,
  "description": "科学仪器",
  "goods": ["计算机", "手机", "耳机"]
}
```

### 3. 图谱管理器（统一入口）

```python
class MultiKnowledgeGraphManager:
    """多知识图谱统一管理器"""

    def __init__(self, arango_url: str, username: str, password: str):
        self.client = ArangoClient(arango_url)

        # 各知识图谱实例
        self.patent_graph = PatentKnowledgeGraph(arango_url, username, password)
        self.trademark_graph = TrademarkKnowledgeGraph(arango_url, username, password)
        self.legal_graph = LegalKnowledgeGraph(arango_url, username, password)
        self.memory_graph = MemoryKnowledgeGraph(arango_url, username, password)

    def get_knowledge_graph(self, graph_type: str):
        """获取指定类型的知识图谱"""
        graphs = {
            'patent': self.patent_graph,
            'trademark': self.trademark_graph,
            'legal': self.legal_graph,
            'modules/modules/modules/memory/memory/modules/memory/memory/modules/modules/memory/memory/memory': self.memory_graph
        }
        return graphs.get(graph_type)

    def cross_graph_query(self, query_info: Dict) -> Dict:
        """跨图谱查询（可选功能）"""
        results = {}

        # 如果需要跨图谱查询，分别查询再合并
        if 'patent' in query_info['graph_types']:
            results['patent'] = self.patent_graph.query(query_info['patent_query'])

        if 'trademark' in query_info['graph_types']:
            results['trademark'] = self.trademark_graph.query(query_info['trademark_query'])

        return results

    def backup_knowledge_graph(self, graph_type: str, backup_path: str):
        """备份指定知识图谱"""
        graph = self.get_knowledge_graph(graph_type)
        if graph:
            return graph.backup(backup_path)

    def restore_knowledge_graph(self, graph_type: str, backup_path: str):
        """恢复指定知识图谱"""
        graph = self.get_knowledge_graph(graph_type)
        if graph:
            return graph.restore(backup_path)
```

## 📋 实施计划

### 第一阶段：ArangoDB环境搭建（3天）
```yaml
任务:
  1. 安装ArangoDB 3.10 LTS
  2. 创建多个知识图谱数据库
  3. 配置访问权限
  4. 测试Python连接

验收标准:
  - ArangoDB正常运行
  - 多数据库访问正常
  - Python接口测试通过
```

### 第二阶段：专利知识图谱迁移（1周）
```yaml
任务:
  1. 从Neo4j导出专利图数据
  2. 转换为ArangoDB格式
  3. 导入到athena_patent_db
  4. 实现Python访问接口
  5. 验证功能完整性

验收标准:
  - 数据迁移完整
  - 查询功能正常
  - 性能达到要求
```

### 第三阶段：其他知识图谱构建（2周）
```yaml
任务:
  1. 构建商标知识图谱
  2. 构建法律知识图谱
  3. 实现动态提示词生成
  4. 测试跨图谱功能

验收标准:
  - 各图谱功能正常
  - 提示词生成有效
  - 业务流程支持
```

### 第四阶段：系统集成和优化（1周）
```yaml
任务:
  1. 与PostgreSQL和Qdrant集成
  2. 实现缓存机制
  3. 性能优化
  4. 监控和备份配置

验收标准:
  - 系统稳定运行
  - 响应时间<500ms
  - 自动备份正常
```

## ✅ 方案优势

1. **真正的多数据库支持** - 每个知识图谱独立数据库
2. **独立性保证** - 各图谱之间不强求完美连接
3. **专业功能支持** - 专利创造性分析等复杂业务
4. **动态提示词** - 实时生成业务相关的提示词
5. **可扩展性** - 可以轻松添加新的知识图谱类型

这个方案完全满足您的需求！