# 专业法律写作能力设计方案

## 一、能力定位

### 核心价值
为律师、专利代理师、法官、法律学者等专业人士提供高质量的法律文档写作服务，包括但不限于：
- 法律研究报告
- 代理词/答辩状
- 法律意见书
- 合同审查报告
- 判例分析报告

### 目标用户
- 专利代理师撰写OA答复
- 律师起草法律文书
- 法官撰写裁判文书
- 学者撰写学术论文
- 企业法务出具法律意见

---

## 二、能力架构设计

### 2.1 三层架构

```
┌─────────────────────────────────────────────────────────┐
│                    用户请求层                            │
│   用户输入：写作任务、主题、要求、参考资料               │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│                  能力编排层 (Orchestrator)               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ 写作风格引擎 │  │  内容生成引擎 │  │  质量评估引擎 │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│                   能力执行层 (Capabilities)               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │
│  │ RAG检索能力 │ │  案例检索   │ │  法条检索   │       │
│  └─────────────┘ └─────────────┘ └─────────────┘       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │
│  │ 风格适配能力 │ │  结构规划   │ │  内容扩充   │       │
│  └─────────────┘ └─────────────┘ └─────────────┘       │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│                    数据存储层                            │
│  Qdrant向量库 │ Neo4j知识图谱 │ PostgreSQL关系数据      │
└─────────────────────────────────────────────────────────┘
```

### 2.2 核心模块

#### 模块1: 写作风格引擎 (Writing Style Engine)
**功能**: 根据不同角色和场景，适配写作风格

**输入**:
- 目标角色（律师/代理师/法官/学者）
- 文档类型（研究报告/法律文书/意见书）
- 风格要求（正式/简洁/详尽）

**输出**:
- 定制的写作风格提示词
- 术语使用规范
- 引用格式要求

**实现方式**:
```python
class WritingStyleEngine:
    STYLE_TEMPLATES = {
        "patent_attorney": {
            "tone": "technical_precise",
            "terminology": ["权利要求", "技术特征", "实施例"],
            "structure": "层次化"
        },
        "judge": {
            "tone": "objective_reasoning",
            "terminology": ["释法说理", "裁判要旨", "定分止争"],
            "structure": "三段论"
        },
        # ... 更多角色
    }

    def generate_style_prompt(self, role: str, doc_type: str) -> str:
        template = self.STYLE_TEMPLATES[role]
        # 生成角色特定的写作风格提示词
        pass
```

#### 模块2: 内容生成引擎 (Content Generation Engine)
**功能**: 协调各种能力，生成高质量内容

**工作流程**:
1. **需求分析** → 识别任务类型、字数要求、结构要求
2. **资料检索** → 调用RAG检索相关案例、法条、学术文献
3. **结构规划** → 生成文档大纲和章节安排
4. **内容生成** → 分章节生成内容
5. **质量优化** → 检查逻辑、补充引用、优化表达

#### 模块3: 质量评估引擎 (Quality Assessment Engine)
**功能**: 评估生成内容的质量，提供改进建议

**评估维度**:
- 结构完整性（是否包含所有必需章节）
- 引用准确性（法条、案例引用是否规范）
- 逻辑严密性（论证是否严密，前后是否一致）
- 语言规范性（是否使用法言法语）
- 批判性（是否有问题意识和创新观点）

---

## 三、能力配置 (Capability Registry)

### 3.1 能力定义

在 `core/capabilities/capability_registry.py` 中注册：

```python
from core.capabilities.capability_base import Capability, CapabilityInvocationType, CapabilityCategory

@capability_registry.register
class LegalWritingCapability(Capability):
    """专业法律写作能力"""

    capability_id = "legal_writing"
    name = "专业法律写作"
    description = "生成高质量的法律研究报告、法律文书等专业文档"
    version = "1.0.0"

    category = CapabilityCategory.KNOWLEDGE_GENERATION
    invocation_type = CapabilityInvocationType.COMPOSITE  # 复合能力

    # 配置参数
    parameters = {
        "task_type": {  # 任务类型
            "type": "string",
            "enum": ["research_report", "legal_brief", "opinion_letter", "judgment"],
            "required": True
        },
        "role": {  # 写作角色
            "type": "string",
            "enum": ["patent_attorney", "lawyer", "judge", "scholar"],
            "required": True
        },
        "topic": {  # 主题
            "type": "string",
            "required": True
        },
        "word_count": {  # 目标字数
            "type": "integer",
            "default": 5000
        },
        "structure": {  # 结构要求
            "type": "array",
            "items": {"type": "string"}
        },
        "style_requirements": {  # 风格要求
            "type": "object"
        }
    }

    # 子能力（能力编排）
    sub_capabilities = [
        "patent_vector_search",  # 检索相关案例
        "legal_kg_query",        # 知识图谱查询
        "style_adapter",         # 风格适配
        "content_expander",      # 内容扩充
        "quality_checker"        # 质量检查
    ]
```

### 3.2 能力实现

创建 `core/capabilities/legal_writing_capability.py`：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专业法律写作能力
Professional Legal Writing Capability
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class LegalWritingCapability:
    """专业法律写作能力"""

    def __init__(self, rag_manager=None, kg_manager=None):
        self.rag_manager = rag_manager
        self.kg_manager = kg_manager

        # 加载写作风格模板
        self.style_templates = self._load_style_templates()

    async def generate(
        self,
        task_type: str,
        role: str,
        topic: str,
        word_count: int = 5000,
        structure: List[str] = None,
        style_requirements: Dict[str, Any] = None,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        生成法律文档

        Args:
            task_type: 任务类型（research_report, legal_brief等）
            role: 写作角色（patent_attorney, lawyer, judge等）
            topic: 主题
            word_count: 目标字数
            structure: 结构要求
            style_requirements: 风格要求
            context: 额外上下文

        Returns:
            生成结果
        """
        start_time = datetime.now()
        logger.info(f"📝 开始生成法律文档: {topic}")
        logger.info(f"   任务类型: {task_type}")
        logger.info(f"   写作角色: {role}")
        logger.info(f"   目标字数: {word_count}")

        # 1. 生成写作风格提示词
        style_prompt = self._generate_style_prompt(role, task_type)

        # 2. 检索相关资料
        materials = await self._retrieve_materials(topic, task_type)

        # 3. 生成文档结构
        document_structure = self._generate_structure(
            task_type, structure
        )

        # 4. 分章节生成内容
        content_sections = {}
        for section in document_structure:
            section_content = await self._generate_section(
                section, topic, materials, style_prompt
            )
            content_sections[section] = section_content

        # 5. 组装完整文档
        full_document = self._assemble_document(
            content_sections, document_structure
        )

        # 6. 质量检查
        quality_report = self._assess_quality(
            full_document, task_type, role
        )

        processing_time = (datetime.now() - start_time).total_seconds()

        return {
            "success": True,
            "document": full_document,
            "metadata": {
                "task_type": task_type,
                "role": role,
                "word_count": len(full_document),
                "processing_time": processing_time
            },
            "materials_used": materials,
            "quality_report": quality_report
        }

    def _generate_style_prompt(self, role: str, task_type: str) -> str:
        """生成写作风格提示词"""
        template = self.style_templates.get(role, {})
        style_requirements = template.get("style_requirements", {})

        # 读取我们之前创建的写作风格指南
        with open(
            '/Users/xujian/Athena工作平台/config/prompts/legal_writing_style_prompt.md',
            'r', encoding='utf-8'
        ) as f:
            base_style_guide = f.read()

        # 结合角色特定要求
        role_specific = style_requirements.get(task_type, "")

        return f"{base_style_guide}\n\n## 角色特定要求\n{role_specific}"

    async def _retrieve_materials(
        self,
        topic: str,
        task_type: str
    ) -> Dict[str, Any]:
        """检索相关资料"""
        materials = {
            "cases": [],
            "laws": [],
            "academic_papers": []
        }

        # 使用RAG检索相关案例
        if self.rag_manager:
            try:
                rag_context = await self.rag_manager.retrieve(
                    query=topic,
                    task_type=task_type,
                    top_k=10
                )
                materials["rag_results"] = rag_context.retrieval_results
            except Exception as e:
                logger.warning(f"RAG检索失败: {e}")

        # 从知识图谱查询相关案例
        if self.kg_manager:
            try:
                # 查询相关案例
                kg_cases = await self.kg_manager.query_related_cases(topic)
                materials["cases"] = kg_cases
            except Exception as e:
                logger.warning(f"知识图谱查询失败: {e}")

        return materials

    def _generate_structure(
        self,
        task_type: str,
        custom_structure: List[str] = None
    ) -> List[str]:
        """生成文档结构"""
        if custom_structure:
            return custom_structure

        # 默认结构模板
        default_structures = {
            "research_report": [
                "摘要",
                "一、原则法理",
                "二、法律依据",
                "三、案例演进",
                "四、争议分析",
                "五、比较法视角",
                "六、完善建议",
                "结论"
            ],
            "legal_brief": [
                "基本情况",
                "案件事实",
                "法律依据",
                "代理意见",
                "结论"
            ],
            "opinion_letter": [
                "背景说明",
                "法律分析",
                "风险评估",
                "专业建议"
            ]
        }

        return default_structures.get(
            task_type,
            ["摘要", "正文", "结论"]
        )

    async def _generate_section(
        self,
        section: str,
        topic: str,
        materials: Dict[str, Any],
        style_prompt: str
    ) -> str:
        """生成单个章节的内容"""
        # 这里调用LLM生成具体章节内容
        # 可以根据章节类型使用不同的提示词

        section_prompt = f'''
        请为法律研究报告撰写"{section}"章节。

        主题：{topic}

        写作风格要求：
        {style_prompt}

        参考资料：
        {materials}

        请确保：
        1. 使用专业的法言法语
        2. 逻辑严密，论证充分
        3. 如有引用，请标注来源
        4. 字数800-1200字
        '''

        # 调用LLM生成内容
        # 这里需要集成LLM客户端
        # ...

        return f"## {section}\n\n(章节内容占位符)"

    def _assemble_document(
        self,
        content_sections: Dict[str, str],
        structure: List[str]
    ) -> str:
        """组装完整文档"""
        document_parts = []

        # 添加标题
        document_parts.append("# 法律研究报告\n")

        # 添加各章节
        for section in structure:
            if section in content_sections:
                document_parts.append(content_sections[section])

        return "\n\n".join(document_parts)

    def _assess_quality(
        self,
        document: str,
        task_type: str,
        role: str
    ) -> Dict[str, Any]:
        """评估文档质量"""
        quality_report = {
            "structure_completeness": 0.0,
            "citation_accuracy": 0.0,
            "logical_consistency": 0.0,
            "language_standard": 0.0,
            "critical_thinking": 0.0,
            "overall_score": 0.0,
            "suggestions": []
        }

        # 检查结构完整性
        required_sections = self._generate_structure(task_type)
        missing_sections = [
            s for s in required_sections
            if s not in document
        ]
        quality_report["structure_completeness"] = (
            1.0 - len(missing_sections) / len(required_sections)
        )

        # 检查引用格式
        if "《" in document and "》" in document:
            quality_report["citation_accuracy"] = 0.8

        # 检查法言法语
        legal_terms = ["权利要求", "技术特征", "侵权", "保护范围"]
        term_count = sum(1 for term in legal_terms if term in document)
        quality_report["language_standard"] = min(term_count / 3, 1.0)

        # 计算总分
        quality_report["overall_score"] = sum([
            quality_report["structure_completeness"],
            quality_report["citation_accuracy"],
            quality_report["logical_consistency"],
            quality_report["language_standard"],
            quality_report["critical_thinking"]
        ]) / 5

        # 生成改进建议
        if quality_report["overall_score"] < 0.8:
            quality_report["suggestions"].append(
                "建议补充更多具体案例和法条引用"
            )

        return quality_report

    def _load_style_templates(self) -> Dict[str, Any]:
        """加载写作风格模板"""
        return {
            "patent_attorney": {
                "tone": "技术精准",
                "focus": ["技术特征分析", "权利要求解释"],
                "style_requirements": {
                    "research_report": "注重技术细节和逻辑层次"
                }
            },
            "lawyer": {
                "tone": "论证有力",
                "focus": ["法律适用", "争议焦点"],
                "style_requirements": {
                    "research_report": "注重法理分析和实务论证"
                }
            },
            "judge": {
                "tone": "客观公正",
                "focus": ["释法说理", "定分止争"],
                "style_requirements": {
                    "research_report": "注重法理阐释和规则发展"
                }
            },
            "scholar": {
                "tone": "批判创新",
                "focus": ["问题意识", "理论建构"],
                "style_requirements": {
                    "research_report": "注重批判性分析和前瞻性思考"
                }
            }
        }
```

---

## 四、使用示例

### 4.1 API调用示例

```python
# 通过动态提示词系统API调用
import httpx

async def generate_legal_report():
    response = await httpx.AsyncClient().post(
        'http://localhost:8000/api/v1/capabilities/legal_writing/invoke',
        json={
            "capability_id": "legal_writing",
            "parameters": {
                "task_type": "research_report",
                "role": "scholar",
                "topic": "专利全面覆盖原则深度研究",
                "word_count": 6000,
                "structure": [
                    "摘要",
                    "一、原则法理",
                    "二、法律依据",
                    "三、案例演进",
                    "四、争议分析",
                    "五、比较法视角",
                    "六、完善建议"
                ]
            },
            "timeout": 300
        }
    )

    result = response.json()
    return result["document"]
```

### 4.2 场景规则配置

在Neo4j中配置场景规则，使其自动调用写作能力：

```cypher
// 创建场景规则
CREATE (sr:ScenarioRule {
    rule_id: "legal_writing_report_v1",
    domain: "legal",
    task_type: "research_report",
    phase: "drafting",

    system_prompt_template: "$load_template('legal_writing_style')",
    user_prompt_template: "请撰写关于{topic}的法律研究报告。角色：{role}，字数：{word_count}字。",

    // 能力调用配置
    capability_invocations: [
        {
            capability_id: "patent_vector_search",
            order: 1,
            parameters: {
                query_text: "{topic}",
                top_k: 10,
                task_type: "legal_research"
            },
            result_variable: "search_results",
            enabled: true
        },
        {
            capability_id: "legal_writing",
            order: 2,
            parameters: {
                task_type: "research_report",
                role: "{role}",
                topic: "{topic}",
                word_count: {word_count}
            },
            result_variable: "legal_document",
            enabled: true
        }
    ],

    version: "1.0.0",
    is_active: true
})
```

---

## 五、技术实现要点

### 5.1 分段生成策略

由于LLM有输出长度限制，采用分段生成策略：

```python
async def generate_long_document(topic: str, target_words: int):
    """生成长文档"""
    sections = ["摘要", "一、原则法理", "二、法律依据", ...]

    document_parts = []
    context = {
        "previous_sections": [],
        "materials": await retrieve_materials(topic)
    }

    for i, section in enumerate(sections):
        # 生成当前章节
        section_content = await generate_section(
            section=section,
            topic=topic,
            context=context,
            previous_summary=summarize_previous(context["previous_sections"])
        )

        document_parts.append(section_content)
        context["previous_sections"].append(section_content)

        # 如果字数不足，扩充当前章节
        if len(section_content) < target_words / len(sections):
            section_content = await expand_section(
                section, section_content, context
            )

    return assemble_document(document_parts)
```

### 5.2 质量保证机制

1. **生成前检查**
   - 验证输入参数完整性
   - 检查参考资料可用性
   - 确认风格模板加载成功

2. **生成中监控**
   - 监控每章节生成质量
   - 实时调整生成策略
   - 记录生成过程日志

3. **生成后评估**
   - 质量评分（结构、引用、逻辑、语言）
   - 改进建议生成
   - 用户反馈收集

### 5.3 迭代优化机制

```python
async def iteratively_optimize(document: str, quality_report: Dict):
    """迭代优化文档"""
    max_iterations = 3

    for i in range(max_iterations):
        if quality_report["overall_score"] >= 0.85:
            break

        # 根据质量报告生成改进建议
        improvements = generate_improvement_suggestions(quality_report)

        # 应用改进
        document = apply_improvements(document, improvements)

        # 重新评估
        quality_report = assess_quality(document)

    return document, quality_report
```

---

## 六、实施路径

### 阶段1: 核心能力实现 (1-2周)
- [ ] 创建 `LegalWritingCapability` 类
- [ ] 实现基本的内容生成流程
- [ ] 集成RAG检索能力
- [ ] 实现质量评估机制

### 阶段2: 风格适配增强 (1周)
- [ ] 完善写作风格模板
- [ ] 实现多角色风格切换
- [ ] 添加自定义风格配置

### 阶段3: 质量优化 (1-2周)
- [ ] 实现分段生成策略
- [ ] 添加迭代优化机制
- [ ] 集成用户反馈

### 阶段4: 集成测试 (1周)
- [ ] 端到端测试
- [ ] 性能优化
- [ ] 用户验收测试

---

## 七、预期效果

| 指标 | 当前（无专门能力） | 目标（实施后） |
|------|-------------------|---------------|
| 文档结构完整性 | 60% | 95% |
| 法言法语规范性 | 70% | 90% |
| 案例引用准确性 | 50% | 85% |
| 逻辑严密性 | 65% | 85% |
| 生成速度 | N/A | <60秒（2000字） |
| 质量稳定性 | 低 | 高（方差<10%） |

---

## 八、使用场景示例

### 场景1: OA答复撰写
```python
# 专利代理师需要撰写审查意见答复
result = await legal_writing.generate(
    task_type="oa_response",
    role="patent_attorney",
    topic="CN202311060998.X创造性审查意见答复",
    context={
        "application_number": "CN202311060998.X",
        "oa_summary": "根据专利法第22条第3款...",
        "rejection_reasons": "区别特征仅为常规手段"
    }
)
```

### 场景2: 法律研究报告
```python
# 学者需要撰写研究报告
result = await legal_writing.generate(
    task_type="research_report",
    role="scholar",
    topic="专利全面覆盖原则深度研究",
    word_count=6000,
    structure=["摘要", "法理", "案例", "争议", "建议"]
)
```

### 场景3: 代理词撰写
```python
# 律师需要撰写代理词
result = await legal_writing.generate(
    task_type="legal_brief",
    role="lawyer",
    topic="某专利侵权纠纷案代理词",
    context={
        "case_number": "(2024)京民初123号",
        "plaintiff": "某科技公司",
        "defendant": "某制造公司",
        "core_dispute": "是否构成等同侵权"
    }
)
```

---

**版本**: v1.0
**创建日期**: 2026-01-23
**作者**: Athena工作平台团队
