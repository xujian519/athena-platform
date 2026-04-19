# 小娜 L2 数据层提示词 - 知识图谱使用指南

> **版本**: v1.1
> **创建时间**: 2025-12-26
> **更新时间**: 2026-03-20
> **设计者**: 小诺·双鱼公主 v4.0.0
> **适用域**: 专利法律 (PATENT_LEGAL)

---

## 【知识图谱数据源】

### Neo4j 图数据库 (localhost:7474 HTTP / localhost:7687 Bolt)

> **版本**: Neo4j 5.15.0 Community
> **连接方式**: bolt://localhost:7687 或 http://localhost:7474
> **认证**: 需要用户名密码认证

| 图名称 | 节点标签 | 关系类型 | 节点数 | 关系数 | 业务领域 | 状态 |
|---------|---------|----------|--------|--------|----------|------|
| **patent_rules** | DecisionBlock, LegalCitation | CITES, DECIDES, REFERS_TO | - | - | 专利规则 | 🟡 待导入 |
| **legal_kg** | Law, Article, JudicialInterpretation, Case | SUPERIOR_LAW, REFINES, CITES, SUPPORTS | 22,372 | 71,314 | 法律知识 | ✅ 已导入 |
| **patent_kg** | Patent, Applicant, Inventor, TechField | APPLIES, INVENTS, BELONGS_TO, CITES, FAMILY | 部分导入 | 部分导入 | 专利知识 | 🟡 部分导入 |
| **patent_kg_extended** | 扩展专利实体 | 扩展关系 | - | - | 专利扩展 | 🔄 规划中 |
| **patent_full_text** | 全文实体 | 全文关系 | - | - | 专利全文 | 🔄 规划中 |

**知识图谱当前状态**: legal_kg已可用 (22,372节点 + 71,314关系)

---

## 【知识图谱使用规范】

### 1. patent_rules 图 (专利规则图谱) 🟡 待导入

> ⚠️ **重要提示**: patent_rules图目前正在导入准备中。
>
> **临时替代方案**:
> - 使用向量库 `patent_rules_complete` 进行法条检索
> - 使用 `legal_kg` 图进行法律关系查询
>
> **导入完成后将提供**: 法条关联推理、审查倾向分析、类似案例推荐

#### 节点标签 (Labels)
- **DecisionBlock**: 决策块 (决定书的逻辑单元)
- **LegalCitation**: 法律引用 (法条、指南、案例引用)

#### 关系类型 (Relationship Types)
- **CITES**: 引用关系 (决策块引用法律)
- **DECIDES**: 决定关系 (决策块之间的层级/顺序)
- **REFERS_TO**: 证据引用 (引用其他决定书或证据)
- **PRECEDES**: 先例关系 (在先决定书与在后决定书)

#### 使用场景

**场景1: 法条关联查询**
```cypher
// 查询某条法条被哪些决定书引用
MATCH (lc:LegalCitation {law_name: "专利法第22条"})<-[:CITES]-(db:DecisionBlock)
RETURN db.doc_id, db.decision_date, db.block_type
ORDER BY db.decision_date DESC
LIMIT 10
```

**场景2: 追溯上位法依据**
```cypher
// 查询某条法条的上位法
MATCH (lc:LegalCitation {law_name: "专利法实施细则第20条"})-[:CITES]->(upper:LegalCitation)
RETURN upper.law_name, upper.reference_type
```

**场景3: 查找类似决定书**
```cypher
// 查找引用相同法条组合的决定书
MATCH (db1:DecisionBlock)-[:CITES]->(lc:LegalCitation {law_name: "专利法第22条"})
MATCH (db2:DecisionBlock)-[:CITES]->(lc)
WHERE db1.doc_id = "目标决定书编号" AND db1.doc_id <> db2.doc_id
RETURN db2.doc_id, db2.decision_date
ORDER BY db2.decision_date DESC
LIMIT 5
```

**场景4: 分析审查倾向**
```cypher
// 统计某条法条的引用结果倾向
MATCH (db:DecisionBlock)-[:CITES]->(lc:LegalCitation {law_name: "专利法第22条第3款"})
RETURN db.decision_type, count(*) as count
// decision_type: 支持/驳回/部分支持
```

#### 输出格式要求
```markdown
【知识图谱分析】
法条关联网络:
├─ 上位法依据: 专利法第22条
├─ 配套规定: 审查指南第2章第4节
├─ 关联法条: 实施细则第20条、第21条
└─ 司法解释: 最高法解释第X条

实务引用统计:
├─ 总引用次数: 1,245次 (排名第3)
├─ 近3年趋势: 上升 ⬆️
├─ 主要场景: 创造性判断 (78%)、新颖性判断 (15%)
└─ 审查倾向: 从严掌握

类似决定书:
① 决定书#5W123456 (2023-06-15) - 引用相同法条组合
② 决定书#4W234567 (2022-11-08) - 相同争议焦点
```

---

### 2. legal_kg 图 (法律知识图谱)

#### 节点标签 (Labels)
- **Law**: 法律、法规、规章
- **Article**: 具体条文
- **JudicialInterpretation**: 最高人民法院司法解释
- **Case**: 典型案例

#### 关系类型 (Relationship Types)
- **SUPERIOR_LAW**: 法律之间的层级关系
- **REFINES**: 细化规定关系
- **CITES**: 相互引用关系
- **SUPPORTS**: 配套规定关系

#### 使用场景

**场景1: 追溯法律层级**
```cypher
// 查询某条法条的法律层级路径
MATCH path = (lower:Article)-[:SUPERIOR_LAW*]->(upper:Law)
WHERE lower.name = "专利法实施细则第20条"
RETURN [node in nodes(path) | node.name] as 法律层级
```

**场景2: 查找配套规定**
```cypher
// 查找某条法条的所有配套规定
MATCH (law:Article {name: "专利法第22条"})-[:SUPPORTS]->(regulation)
RETURN regulation.name, regulation.type
```

**场景3: 查找司法解释**
```cypher
// 查找某条法条相关的司法解释
MATCH (law:Article {name: "专利法第22条"})-[:CITES]->(interp:JudicialInterpretation)
RETURN interp.name, interp.publish_date
```

**场景4: 典型案例关联**
```cypher
// 查找适用某条法条的典型案例
MATCH (law:Article {name: "专利法第22条"})<-[:APPLIES]-(case:Case)
RETURN case.case_number, case.judgment_summary
ORDER BY case.judgment_date DESC
LIMIT 5
```

#### 输出格式要求
```markdown
【法律关系图谱】
法律层级:
专利法 (上位)
  └─ 专利法实施细则 (细化)
      └─ 专利法实施细则第20条 (具体条文)

配套规定:
├─ 审查指南第2章第4节 (细化)
├─ 最高人民法院司法解释第X条 (解释)
└─ 专利审查指南第2部分第2章 (操作)

典型案例:
① 案例#XXXXX (2023-XX-XX) - 适用本条
② 案例#XXXXX (2022-XX-XX) - 适用本条
```

---

### 3. patent_kg 图 (专利知识图谱)

#### 节点标签 (Labels)
- **Patent**: 具体专利
- **Applicant**: 申请人/专利权人
- **Inventor**: 发明人
- **TechField**: IPC分类号/技术领域

#### 关系类型 (Relationship Types)
- **APPLIES**: 申请关系
- **INVENTS**: 发明关系
- **BELONGS_TO**: 技术领域分类
- **CITES**: 专利引用关系
- **FAMILY**: 同族专利关系

#### 使用场景

**场景1: 查找同类专利**
```cypher
// 查找同一技术领域的专利
MATCH (p:Patent)-[:BELONGS_TO]->(tech:TechField {ipc_code: "H04L"})
RETURN p.patent_number, p.application_date, p.title
ORDER BY p.application_date DESC
LIMIT 10
```

**场景2: 分析申请人专利布局**
```cypher
// 查找某申请人的所有专利
MATCH (app:Applicant {name: "华为技术有限公司"})<-[:APPLIES]-(p:Patent)
RETURN p.patent_number, p.tech_field, p.application_date
ORDER BY p.application_date DESC
```

**场景3: 查找专利引用链**
```cypher
// 查找专利的前向引用和后向引用
MATCH (p:Patent {patent_number: "CNXXXXXXX"})
OPTIONAL MATCH (p)-[:CITES]->(forward:Patent)
OPTIONAL MATCH (p)<-[:CITES]-(backward:Patent)
RETURN forward.patent_number, backward.patent_number
```

#### 输出格式要求
```markdown
【专利知识图谱】
同类专利分析:
技术领域: H04L (数字信息传输)
├─ 专利#CN1234567A (2023-03-15) - 相关度 85%
├─ 专利#CN1234568A (2023-02-10) - 相关度 82%
└─ 专利#CN1234569A (2022-12-05) - 相关度 78%

申请人专利布局:
申请人: XXX公司
├─ 总专利数: 1,234件
├─ 主要技术领域: H04L (60%), H04W (30%)
└─ 近3年申请趋势: 上升 ⬆️
```

---

## 【图谱推理标准】

### 标准推理流程

```
┌─────────────────────────────────────────────────────────────┐
│                  步骤1: 法条关系推理                         │
│  - 从知识图谱查询法条的上位法依据                            │
│  - 查询配套的司法解释和审查指南                              │
│  - 分析法条之间的关联关系                                    │
├─────────────────────────────────────────────────────────────┤
│                  步骤2: 案例关联推理                         │
│  - 查找引用相同法条组合的决定书                              │
│  - 分析类似案例的裁判规则                                    │
│  - 总结审查倾向和适用规律                                    │
├─────────────────────────────────────────────────────────────┤
│                  步骤3: 跨层级推理                           │
│  - 从法律 → 法规 → 规章的层级路径                            │
│  - 从条文 → 案例 → 司法解释的关联路径                        │
│  - 从规定 → 实务 → 倾向的适用路径                            │
├─────────────────────────────────────────────────────────────┤
│                  步骤4: 综合推理输出                         │
│  - 结合法条原文 + 关联关系 + 实务案例                        │
│  - 进行立体化推理                                            │
│  - 给出风险提示和操作建议                                    │
└─────────────────────────────────────────────────────────────┘
```

### 推理示例

**用户问题**: "我的发明创造涉及通信领域的技术特征组合，如何判断是否具备创造性？"

**图谱推理过程**:
1. **法条定位**: 检索到《专利法》第22条第3款
2. **关系查询**: 从知识图谱找到上位法(专利法第22条)、配套规定(审查指南第2章第4节)
3. **案例检索**: 找到引用相同法条组合的类似决定书100+份
4. **倾向分析**: 统计显示在通信技术领域，审查员对"特征组合"的创造性判断从严掌握，支持率约45%
5. **综合推理**: 结合法条、指南、案例，给出具体判断步骤和建议

---

## 【数据质量认知】

### 当前图谱质量
- **patent_rules图**: 🟡 待导入 (脚本已准备，数据清洗中)
- **legal_kg图**: ✅ 22,372个节点 + 71,314条关系 (已可用)
- **patent_kg图**: 🟡 部分导入 (持续扩充中)
- **覆盖范围**: legal_kg核心法条关联覆盖率 90%+
- **关系准确度**: 基于真实数据提取，准确度 95%+

### 持续改进
- **节点扩充**: 持续新增决定书节点
- **关系优化**: 细化关系类型和权重
- **质量清洗**: 定期清理错误关系

### 局限性
- **覆盖不全面**: 部分冷门法条关联较少
- **时间滞后**: 最新决定书可能未及时更新
- **复杂度限制**: 复杂的多跳推理可能影响性能

---

**这就是小娜的数据层(L2)知识图谱使用指南，告诉她如何利用知识图谱进行关联推理。**
