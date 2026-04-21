# Athena智能体统一记忆系统设计

> **版本**: 1.0
> **创建日期**: 2026-04-21
> **状态**: 设计阶段

---

## 📋 设计目标

参考优秀开源项目的记忆系统设计：
- **AutoGen** ([Memory and RAG](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/memory.html)) - RAG模式 + Zep长期记忆
- **LangGraph** ([Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)) - Checkpoint持久化 + 故障恢复
- **CrewAI** ([Memory](https://docs.crewai.com/en/concepts/memory)) - 统一Memory类 + Markdown持久化

**核心目标**：
1. ✅ **两层记忆架构**：全局记忆 + 项目记忆
2. ✅ **自动持久化**：所有记忆自动保存，无需手动操作
3. ✅ **智能检索**：基于向量相似度和关键词的混合检索
4. ✅ **跨智能体共享**：支持智能体间记忆共享
5. ✅ **版本控制友好**：记忆文件可纳入Git管理

---

## 🏗️ 两层记忆架构

```
┌─────────────────────────────────────────────────────────┐
│              Athena两层记忆架构                          │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Layer 1: 全局记忆 (Global Memory)               │   │
│  │  位置: ~/.athena/memory/                          │   │
│  │  内容:                                            │   │
│  │  - 用户偏好 (user_preferences.md)                 │   │
│  │  - 跨项目知识 (cross_project_knowledge/)          │   │
│  │  - 智能体学习成果 (agent_learning/)                │   │
│  │  - 常用工具配置 (tool_preferences.json)           │   │
│  └──────────────────────────────────────────────────┘   │
│                        ↓                                  │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Layer 2: 项目记忆 (Project Memory)               │   │
│  │  位置: <project_path>/.athena/                     │   │
│  │  内容:                                            │   │
│  │  - 项目上下文 (project_context.md)                │   │
│  │  - 工作历史 (work_history.md)                     │   │
│  │  - 项目知识库 (project_knowledge/)                │   │
│  │  - 智能体协作记录 (agent_collaboration.md)         │   │
│  └──────────────────────────────────────────────────┘   │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

---

## 1️⃣ 全局记忆 (Global Memory)

### 1.1 存储位置

```
~/.athena/memory/
├── user_preferences.md          # 用户偏好设置
├── cross_project_knowledge/      # 跨项目知识
│   ├── patent_law_principles.md # 专利法律原则
│   ├── common_patterns.md       # 常见模式
│   └── best_practices.md        # 最佳实践
├── agent_learning/               # 智能体学习成果
│   ├── xiaona_learning.md       # 小娜学习成果
│   ├── xiaonuo_learning.md      # 小诺学习成果
│   └── yunxi_learning.md        # 云熙学习成果
├── tool_preferences.json        # 工具偏好配置
├── global_embeddings.db         # 全局向量数据库 (SQLite+FAISS)
└── memory_index.json            # 记忆索引
```

### 1.2 user_preferences.md

```markdown
# 用户偏好设置

> **最后更新**: 2026-04-21
> **用户**: 徐健 (xujian519@gmail.com)

## 工作风格偏好

### 代码风格
- 使用简体中文注释
- 遵循PEP 8规范
- 行长度限制：100字符

### 交互风格
- 期望先规划再执行（小诺0号原则）
- 关键决策需要确认
- 喜欢看到推理过程（Scratchpad）

### 质量标准
- 质量优先于速度
- 专利和法律业务以准确性为最高原则
- 不确定时明确说明

## 专业领域

### 核心专长
- 专利法律分析
- 专利检索策略
- 技术方案理解
- 创造性评估

### 常见任务类型
1. 专利检索
2. 技术交底书分析
3. 创造性分析
4. 新颖性分析
5. 侵权分析
6. 无效宣告分析

## 工具偏好

### 检索工具
- 优先使用：本地PostgreSQL专利库
- 补充使用：Google Patents
- 不推荐：CNIPA/EPO/WIPO（未配置）

### 分析工具
- 要素提取工具
- 双图分析工具
- 向量检索工具

## 反馈历史

### 2026-04-21
- ✅ 喜欢两层记忆架构（全局+项目）
- ✅ 期望项目记忆自动创建
- ✅ 希望记忆文件可纳入Git管理

### 2026-04-16
- ✅ 专利检索只用本地PG+Google Patents
- ✅ 分析者需要配置技术分析工具
- ✅ 法律世界模型只给法律分析智能体
```

### 1.3 agent_learning/ 目录

**xiaona_learning.md**:
```markdown
# 小娜学习成果

> **智能体**: 小娜·天秤女神（法律专家）
> **最后更新**: 2026-04-21

## 学习的关键知识

### 专利法律原则
1. **创造性判断三步法**：
   - 确定最接近的现有技术
   - 确定区别特征和实际解决的技术问题
   - 判断要求保护的技术方案对本领域技术人员来说是否显而易见

2. **新颖性判断标准**：
   - 单独对比原则
   - 上位概念与下位概念
   - 数值范围

### 常见错误修正

#### 错误1：过度使用法律世界模型
- **问题**: 所有智能体都使用法律世界模型
- **修正**: 只有小诺和法律分析智能体使用
- **日期**: 2026-04-21

#### 错误2：检索工具配置不准确
- **问题**: 配置了不存在的CNIPA/EPO/WIPO检索
- **修正**: 只配置本地PG+Google Patents
- **日期**: 2026-04-21

## 优化成果

### 性能优化
- 场景识别缓存：50ms → 10ms
- 规则检索缓存：200ms → 50ms

### 提示词优化
- v4.0 → v5.0：五层渐进式加载
- Token使用：20K → 5K（核心负载）
```

---

## 2️⃣ 项目记忆 (Project Memory)

### 2.1 存储位置

```
<project_path>/.athena/
├── project_context.md           # 项目上下文
├── work_history.md              # 工作历史
├── project_knowledge/           # 项目知识库
│   ├── technical_findings.md   # 技术发现
│   ├── legal_analysis.md       # 法律分析
│   └── prior_art.md            # 现有技术
├── agent_collaboration.md       # 智能体协作记录
├── checkpoints/                 # 检查点（LangGraph风格）
│   ├── checkpoint_001.json
│   ├── checkpoint_002.json
│   └── ...
└── project_embeddings.db        # 项目向量数据库
```

### 2.2 project_context.md

```markdown
# 项目上下文

> **项目名称**: 睿羿科技专利项目
> **项目路径**: /Users/xujian/Desktop/睿羿科技1件/
> **创建日期**: 2026-04-16
> **最后更新**: 2026-04-21

## 项目概览

### 技术方案
**发明名称**: 结合拟人驾驶行为的自动驾驶掉头路段脱困规划方法

**技术领域**: 智能交通、自动驾驶

### 核心创新点
1. 拟人化掉头轨迹规划
2. 多目标优化（安全性、舒适性、效率）
3. 动态环境感知
4. 驾驶行为学习

## 工作进展

### 已完成 ✅
1. 技术交底书深度分析（6个创新点）
2. 专利检索策略设计与执行（11篇专利+4篇论文）
3. 专利和论文全文下载（30.06 MB PDF）
4. 创造性重新评估（中等-高水平）
5. 补充材料清单生成

### 进行中 ⏳
- 补充文献检索
- 荧光光谱数据准备

### 待办 📋
- 联系客户
- 缴纳复审费
- 提交复审

## 关键文档

### 分析报告
- `技术交底书分析报告.md` (159 KB)
- `专利检索策略报告.md`
- `创造性评估报告.md`
- `补充材料清单.docx`

### 专利原文
- 11篇相关专利PDF（11 patents/）
- 4篇学术论文PDF（4 papers/）

## 风险评估

### A级风险（高）
- **D1**: 可能影响新颖性，需重点分析
- **D2**: 可能影响创造性，需找到区别特征
- **D3**: 技术领域相近，需强调预料不到效果

### B级风险（中）
- 6篇专利需关注

### C级风险（低）
- 2篇专利关联性较弱

## 智能体分工

### 小诺（编排者）
- 任务分解和调度
- 进度跟踪
- 结果聚合

### 小娜（法律专家）
- 法律分析
- 案例检索
- 意见书撰写

### 检索者
- 专利检索
- 论文检索
- 文献下载

### 分析者（技术分析）
- 技术方案理解
- 特征提取
- 双图分析

### 创造性分析智能体
- 创造性评估
- 区别特征分析
- 技术效果确定

## 用户偏好（本项目）

### 沟通方式
- 期望先规划再执行
- 关键决策需要确认
- 喜欢看到详细推理过程

### 输出格式
- 优先Markdown格式
- 同时提供JSON格式（机器可读）
- 重要结论要有法律依据

### 质量要求
- 准确性优先于速度
- 不确定时明确说明
- 关键结论需要多个证据支持
```

### 2.3 work_history.md

```markdown
# 工作历史

> **项目**: 睿羿科技专利项目
> **时间范围**: 2026-04-16 至今

## 2026-04-21

### 09:30 - 记忆系统设计
- **智能体**: Claude Code
- **任务**: 设计统一记忆系统
- **成果**:
  - 两层记忆架构（全局+项目）
  - 参考AutoGen、LangGraph、CrewAI
  - 自动持久化机制
- **文件**: `.athena/project_context.md`（创建）

### 09:15 - 开发进度记录
- **智能体**: Claude Code
- **任务**: 记录详细开发进度
- **成果**: `DEVELOPMENT_PROGRESS.md`
- **状态**: ✅ 完成

## 2026-04-16

### 14:00 - 技术交底书分析
- **智能体**: 分析者（AnalyzerAgent）
- **任务**: 深度分析技术交底书
- **成果**:
  - 提取6个核心创新点
  - 生成技术特征矩阵
  - 识别关键技术难点
- **输出**: `技术交底书分析报告.md` (42 KB)

### 15:30 - 专利检索
- **智能体**: 检索者（RetrieverAgent）
- **任务**: 执行专利检索策略
- **成果**:
  - 检索11篇相关专利
  - 下载全文PDF
  - 风险分级评估（A/B/C）
- **输出**: `专利检索结果/`

### 17:00 - 创造性评估
- **智能体**: 创造性分析智能体
- **任务**: 评估专利创造性
- **成果**:
  - 创造性水平：中等-高
  - 区别特征分析
  - 技术效果论证
- **输出**: `创造性评估报告.md` (38 KB)

### 18:30 - 补充材料生成
- **智能体**: 小娜（XiaonaAgent）
- **任务**: 生成补充材料清单
- **成果**: DOCX文档
- **输出**: `补充材料清单.docx`

## 统计信息

- **总工作时长**: ~5小时
- **完成的任务**: 5个
- **生成的文档**: 4份报告 + 1份清单
- **检索的专利**: 11篇
- **下载的论文**: 4篇
- **总数据量**: 30.06 MB

## 下一步计划

1. 补充文献检索（优先）
2. 联系客户准备荧光光谱数据
3. 缴纳复审费
4. 提交复审申请
```

### 2.4 agent_collaboration.md

```markdown
# 智能体协作记录

> **项目**: 睿羿科技专利项目
> **记录时间**: 2026-04-16 至今

## 协作模式

### 本次项目采用：Hierarchical（层次式）

```
小诺（编排者）
    ├─> 检索者（RetrieverAgent）
    │   └─> 专利检索 + 文献下载
    ├─> 分析者（AnalyzerAgent）
    │   └─> 技术交底书分析
    └─> 创造性分析智能体
        └─> 创造性评估
```

## 协作事件

### Event #001 - 技术交底书分析

**时间**: 2026-04-16 14:00

**参与者**:
- 小诺（编排）
- 分析者（执行）

**流程**:
1. 小诺接收任务
2. 小诺制定计划（展示给用户）
3. 用户确认计划
4. 小诺调度分析者
5. 分析者执行分析
6. 小诺聚合结果
7. 小诺向用户汇报

**结果**: ✅ 成功
- 生成42 KB分析报告
- 提取6个创新点
- 识别技术特征

**协作质量**: ⭐⭐⭐⭐⭐
- 沟通清晰
- 执行高效
- 结果准确

### Event #002 - 专利检索

**时间**: 2026-04-16 15:30

**参与者**:
- 小诺（编排）
- 检索者（执行）

**流程**:
1. 小诺基于分析结果制定检索策略
2. 检索者执行多源检索（本地PG + Google Patents）
3. 检索者去重排序
4. 小诺聚合结果
5. 小诺生成风险分级

**结果**: ✅ 成功
- 检索11篇专利
- 下载全文PDF
- 风险分级（3A+6B+2C）

**协作质量**: ⭐⭐⭐⭐
- 检索全面
- 风险评估准确
- 通信顺畅

## 协作统计

### 智能体参与度
- 小诺：100%（所有任务的编排者）
- 检索者：20%（1/5任务）
- 分析者：20%（1/5任务）
- 创造性分析智能体：20%（1/5任务）

### 协作效率
- 平均任务完成时间：35分钟
- 智能体间通信次数：12次
- 用户干预次数：1次（计划确认）

### 问题记录
- **无重大问题**
- **小优化**: 检索结果去重算法可以优化

## 改进建议

1. **并行化**: 检索和分析可以并行执行
2. **缓存**: 检索结果可以缓存，避免重复检索
3. **增量更新**: 工作历史支持增量更新，减少重写
```

---

## 3️⃣ 记忆系统API设计

### 3.1 核心接口

```python
"""
Athena统一记忆系统API

参考：
- AutoGen: RAG模式 + Zep
- LangGraph: Checkpoint持久化
- CrewAI: 统一Memory类
"""

from enum import Enum
from typing import Optional, Any
from pathlib import Path
from dataclasses import dataclass
import json
from datetime import datetime


class MemoryType(Enum):
    """记忆类型"""
    GLOBAL = "global"      # 全局记忆
    PROJECT = "project"    # 项目记忆


class MemoryCategory(Enum):
    """记忆分类"""
    USER_PREFERENCE = "user_preference"
    AGENT_LEARNING = "agent_learning"
    PROJECT_CONTEXT = "project_context"
    WORK_HISTORY = "work_history"
    AGENT_COLLABORATION = "agent_collaboration"
    TECHNICAL_FINDINGS = "technical_findings"
    LEGAL_ANALYSIS = "legal_analysis"


@dataclass
class MemoryEntry:
    """记忆条目"""
    type: MemoryType
    category: MemoryCategory
    key: str                          # 唯一键
    content: str                      # Markdown内容
    metadata: dict[str, Any]          # 元数据
    created_at: datetime
    updated_at: datetime
    embedding: Optional[list[float]] = None  # 向量嵌入


class UnifiedMemorySystem:
    """
    统一记忆系统

    核心特性：
    1. 两层架构（全局+项目）
    2. 自动持久化
    3. 向量检索
    4. 智能体共享
    5. 版本控制友好
    """

    def __init__(
        self,
        global_memory_path: str = "~/.athena/memory",
        current_project_path: Optional[str] = None
    ):
        """
        初始化记忆系统

        Args:
            global_memory_path: 全局记忆路径
            current_project_path: 当前项目路径（可选）
        """
        self.global_memory_path = Path(global_memory_path).expanduser()
        self.current_project_path = (
            Path(current_project_path).expanduser()
            if current_project_path else None
        )

        # 创建目录
        self.global_memory_path.mkdir(parents=True, exist_ok=True)
        if self.current_project_path:
            (self.current_project_path / ".athena").mkdir(
                parents=True, exist_ok=True
            )

        # 加载索引
        self.memory_index = self._load_memory_index()

    def write(
        self,
        type: MemoryType,
        category: MemoryCategory,
        key: str,
        content: str,
        metadata: Optional[dict[str, Any]] = None
    ) -> MemoryEntry:
        """
        写入记忆

        Args:
            type: 记忆类型（全局/项目）
            category: 记忆分类
            key: 唯一键
            content: Markdown内容
            metadata: 元数据

        Returns:
            MemoryEntry: 创建的记忆条目
        """
        # 确定存储路径
        if type == MemoryType.GLOBAL:
            base_path = self.global_memory_path
        else:
            if not self.current_project_path:
                raise ValueError("项目记忆需要指定项目路径")
            base_path = self.current_project_path / ".athena"

        # 创建文件路径
        file_path = base_path / f"{key}.md"

        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # 创建记忆条目
        entry = MemoryEntry(
            type=type,
            category=category,
            key=key,
            content=content,
            metadata=metadata or {},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # 更新索引
        self._update_memory_index(entry)

        return entry

    def read(
        self,
        type: MemoryType,
        category: MemoryCategory,
        key: str
    ) -> Optional[str]:
        """
        读取记忆

        Args:
            type: 记忆类型
            category: 记忆分类
            key: 唯一键

        Returns:
            Markdown内容，如果不存在则返回None
        """
        # 确定文件路径
        if type == MemoryType.GLOBAL:
            file_path = self.global_memory_path / f"{key}.md"
        else:
            if not self.current_project_path:
                return None
            file_path = self.current_project_path / ".athena" / f"{key}.md"

        # 读取文件
        if not file_path.exists():
            return None

        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def search(
        self,
        query: str,
        type: Optional[MemoryType] = None,
        category: Optional[MemoryCategory] = None,
        limit: int = 10
    ) -> list[MemoryEntry]:
        """
        搜索记忆

        Args:
            query: 搜索查询
            type: 记忆类型过滤（可选）
            category: 记忆分类过滤（可选）
            limit: 返回数量限制

        Returns:
            匹配的记忆条目列表
        """
        # TODO: 实现向量检索
        # 暂时使用简单的关键词匹配
        results = []

        for entry_key, entry_data in self.memory_index.items():
            # 应用过滤器
            if type and entry_data['type'] != type.value:
                continue
            if category and entry_data['category'] != category.value:
                continue

            # 关键词匹配
            if query.lower() in entry_data.get('content', '').lower():
                results.append(MemoryEntry(**entry_data))

        return results[:limit]

    def _load_memory_index(self) -> dict[str, dict]:
        """加载记忆索引"""
        index_file = self.global_memory_path / "memory_index.json"

        if not index_file.exists():
            return {}

        with open(index_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _update_memory_index(self, entry: MemoryEntry) -> None:
        """更新记忆索引"""
        # 转换为字典
        entry_dict = {
            'type': entry.type.value,
            'category': entry.category.value,
            'key': entry.key,
            'content': entry.content[:500],  # 索引只保存前500字符
            'metadata': entry.metadata,
            'created_at': entry.created_at.isoformat(),
            'updated_at': entry.updated_at.isoformat()
        }

        # 生成唯一键
        unique_key = f"{entry.type.value}/{entry.category.value}/{entry.key}"

        # 更新索引
        self.memory_index[unique_key] = entry_dict

        # 保存索引
        index_file = self.global_memory_path / "memory_index.json"
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(self.memory_index, f, ensure_ascii=False, indent=2)

    def append_work_history(
        self,
        agent_name: str,
        task: str,
        result: str,
        status: str = "success"
    ) -> None:
        """
        追加工作历史

        Args:
            agent_name: 智能体名称
            task: 任务描述
            result: 任务结果
            status: 任务状态
        """
        # 读取现有工作历史
        history_content = self.read(
            MemoryType.PROJECT,
            MemoryCategory.WORK_HISTORY,
            "work_history"
        )

        # 如果不存在，初始化
        if not history_content:
            history_content = f"# 工作历史\n\n> **项目**: {self.current_project_path.name if self.current_project_path else 'Unknown'}\n> **时间范围**: {datetime.now().strftime('%Y-%m-%d')} 至今\n\n"

        # 追加新条目
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        new_entry = f"""
## {datetime.now().strftime('%Y-%m-%d')}

### {timestamp} - {task}
- **智能体**: {agent_name}
- **任务**: {task}
- **状态**: {status}
- **结果**: {result}
"""

        # 写入
        self.write(
            MemoryType.PROJECT,
            MemoryCategory.WORK_HISTORY,
            "work_history",
            history_content + new_entry
        )


# 便捷函数
def get_global_memory() -> UnifiedMemorySystem:
    """获取全局记忆系统"""
    return UnifiedMemorySystem()


def get_project_memory(project_path: str) -> UnifiedMemorySystem:
    """获取项目记忆系统"""
    return UnifiedMemorySystem(
        current_project_path=project_path
    )
```

---

## 4️⃣ 智能体集成

### 4.1 小诺（编排者）集成

```python
from core.orchestration.xiaonuo_orchestrator import XiaonuoOrchestrator
from core.memory.unified_memory_system import get_project_memory

class XiaonuoOrchestrator:
    """小诺编排器（增强版，集成记忆系统）"""

    def __init__(self, project_path: str):
        self.project_memory = get_project_memory(project_path)
        self.global_memory = get_global_memory()

    async def orchestrate_task(self, user_request: str):
        """编排任务"""

        # 1. 读取项目上下文
        project_context = self.project_memory.read(
            MemoryType.PROJECT,
            MemoryCategory.PROJECT_CONTEXT,
            "project_context"
        )

        # 2. 读取用户偏好
        user_preferences = self.global_memory.read(
            MemoryType.GLOBAL,
            MemoryCategory.USER_PREFERENCE,
            "user_preferences"
        )

        # 3. 制定计划
        plan = await self._create_plan(
            user_request,
            project_context,
            user_preferences
        )

        # 4. 展示计划并等待确认
        # ...

        # 5. 执行任务
        result = await self._execute_plan(plan)

        # 6. 记录工作历史
        self.project_memory.append_work_history(
            agent_name="xiaonuo",
            task=user_request,
            result=str(result)[:200],
            status="success"
        )

        return result
```

### 4.2 其他智能体集成

```python
from core.agents.xiaona_agent import XiaonaAgent

class XiaonaAgent:
    """小娜智能体（增强版，集成记忆系统）"""

    def __init__(self, project_path: str):
        self.project_memory = get_project_memory(project_path)
        self.global_memory = get_global_memory()

        # 加载学习成果
        learning_content = self.global_memory.read(
            MemoryType.GLOBAL,
            MemoryCategory.AGENT_LEARNING,
            "xiaona_learning"
        )
        self.learning_history = learning_content or ""

    async def analyze_patent(self, patent_id: str):
        """分析专利"""

        # 1. 检索项目知识
        prior_art = self.project_memory.search(
            query=prior_art_keywords,
            category=MemoryCategory.TECHNICAL_FINDINGS
        )

        # 2. 执行分析
        analysis_result = await self._perform_analysis(
            patent_id,
            prior_art
        )

        # 3. 保存分析结果
        self.project_memory.write(
            MemoryType.PROJECT,
            MemoryCategory.LEGAL_ANALYSIS,
            f"analysis_{patent_id}",
            analysis_result
        )

        # 4. 更新学习成果
        self._update_learning(analysis_result)

        return analysis_result

    def _update_learning(self, new_insights: str):
        """更新学习成果"""
        # 读取现有学习成果
        existing = self.global_memory.read(
            MemoryType.GLOBAL,
            MemoryCategory.AGENT_LEARNING,
            "xiaona_learning"
        )

        # 追加新洞察
        updated = existing + f"\n\n## {datetime.now().strftime('%Y-%m-%d')}\n{new_insights}"

        # 保存
        self.global_memory.write(
            MemoryType.GLOBAL,
            MemoryCategory.AGENT_LEARNING,
            "xiaona_learning",
            updated
        )
```

---

## 5️⃣ 实施计划

### Phase 1: 核心API实现（1周）

**任务**:
1. 实现 `UnifiedMemorySystem` 类
2. 实现文件持久化
3. 实现记忆索引
4. 单元测试

**产出**:
- `core/memory/unified_memory_system.py`
- `tests/test_unified_memory_system.py`

### Phase 2: 智能体集成（1周）

**任务**:
1. 小诺集成记忆系统
2. 小娜集成记忆系统
3. 其他智能体集成
4. 集成测试

**产出**:
- 更新的智能体代码
- `tests/test_agent_memory_integration.py`

### Phase 3: 高级特性（1周）

**任务**:
1. 向量检索（SQLite+FAISS）
2. 语义搜索
3. 记忆压缩
4. 性能优化

**产出**:
- `core/memory/vector_search.py`
- `core/memory/memory_compression.py`

---

## 6️⃣ 参考资源

### 开源项目

- **AutoGen**: [Memory and RAG](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/memory.html)
- **LangGraph**: [Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)
- **CrewAI**: [Memory](https://docs.crewai.com/en/concepts/memory)
- **Zep**: [Long-term memory for AI](https://www.getzep.com/)

### 学术论文

- **AutoGen**: [arXiv:2308.08155](https://arxiv.org/abs/2308.08155)
- **LangGraph**: [LangChain persistence research](https://docs.langchain.com/)

### 社区资源

- **CrewAI Community**: [Memory discussions](https://community.crewai.com/)
- **AutoGen GitHub**: [Memory proposals](https://github.com/microsoft/autogen/issues/4564)

---

**End of Document**
