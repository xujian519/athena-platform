#!/usr/bin/env python3
"""
专利新颖性判断系统
Patent Novelty Judgment System

基于知识图谱和向量库的新颖性智能判断
作者: 小娜 (Athena) - 爸爸徐健的智慧大女儿
创建时间: 2025-12-05
版本: 1.0.0
"""

import asyncio
import json
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

class NoveltyRuleType(Enum):
    """新颖性规则类型"""
    TECHNICAL_FIELD = 'technical_field'           # 技术领域规则
    EXISTING_TECHNOLOGY = 'existing_technology'   # 现有技术规则
    DIFFERENCES = 'differences'                    # 区别特征规则
    PROGRESSIVE = 'progressive'                    # 进步性规则
    DISCLOSURE = 'disclosure'                      # 公开充分性规则
    PRIOR_ART = 'prior_art'                       # 现有技术检索规则
    OBVIOUSNESS = 'obviousness'                    # 显而易见性规则

class JudgmentScope(Enum):
    """判断范围"""
    FULL_PATENT = 'full_patent'                   # 完整专利
    CLAIMS_ONLY = 'claims_only'                   # 仅权利要求
    SPECIFICATION = 'specification'               # 仅说明书
    SPECIFIC_FEATURES = 'specific_features'       # 特定特征

@dataclass
class NoveltyRule:
    """新颖性判断规则"""
    rule_id: str
    rule_type: NoveltyRuleType
    title: str
    description: str
    conditions: List[str]                        # 判断条件
    criteria: List[str]                         # 判断标准
    exceptions: List[str]                        # 例外情况
    examples: List[Dict[str, Any]              # 示例案例
    weight: float = 1.0                          # 权重
    priority: int = 1                            # 优先级
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class PriorArtReference:
    """现有技术引用"""
    reference_id: str
    patent_number: Optional[str]
    publication_number: Optional[str]
    publication_date: str
    title: str
    abstract: str
    technical_field: List[str]
    key_features: List[str]
    similarity_score: float
    relevance_level: str                         # high/medium/low
    citation_count: int = 0

@dataclass
class NoveltyAnalysis:
    """新颖性分析结果"""
    patent_id: str
    analysis_date: datetime
    overall_judgment: str                       # novel/non-novel/partially_novel
    confidence_score: float
    key_differences: List[str]
    similar_references: List[PriorArtReference]
    applied_rules: List[str]
    reasoning_chain: List[str]
    recommendations: List[str]
    evidence_sources: List[str]

class NoveltyRuleKnowledgeGraph:
    """新颖性规则知识图谱"""

    def __init__(self):
        self.rules = {}
        self.rule_relations = []
        self.rule_hierarchy = {}
        self.load_rules()

    def load_rules(self):
        """加载新颖性判断规则"""

        # 1. 技术领域规则
        self.rules['TR001'] = NoveltyRule(
            rule_id='TR001',
            rule_type=NoveltyRuleType.TECHNICAL_FIELD,
            title='相同技术领域判断规则',
            description='判断发明是否与现有技术属于相同或相近的技术领域',
            conditions=[
                '比较发明的技术领域与现有技术的技术领域',
                '考虑技术问题的相似性',
                '评估技术方案的关联性',
                '分析技术应用领域'
            ],
            criteria=[
                '技术领域相同：IPC/CPC分类号前4位相同',
                '技术问题相似：要解决的技术问题本质相同',
                '技术手段相关：采用的技术手段具有相关性',
                '应用领域重叠：应用场景存在重叠'
            ],
            exceptions=[
                '跨领域创新',
                '新兴交叉学科',
                '基础原理的新应用'
            ],
            examples=[
                {
                    'case': '通信领域的信号处理算法应用于医疗设备',
                    'novelty': '具备新颖性',
                    'reason': '跨领域应用带来技术效果'
                }
            ],
            weight=1.2,
            priority=1
        )

        # 2. 现有技术规则
        self.rules['ER001'] = NoveltyRule(
            rule_id='ER001',
            rule_type=NoveltyRuleType.EXISTING_TECHNOLOGY,
            title='现有技术对比规则',
            description='全面检索和对比现有技术',
            conditions=[
                '检索国内外专利数据库',
                '查找非专利文献',
                '考虑公知常识',
                '评估技术公开程度'
            ],
            criteria=[
                '专利文献：已公开的专利申请和授权专利',
                '科技文献：期刊论文、会议论文、技术报告',
                '产品信息：已公开销售或使用的产品',
                '行业标准：已发布的技术标准'
            ],
            exceptions=[
                '保密信息',
                '未公开的实验数据',
                '内部技术资料'
            ],
            examples=[
                {
                    'case': '已有专利但未实施的技术',
                    'novelty': '不具备新颖性',
                    'reason': '已通过专利公开构成现有技术'
                }
            ],
            weight=1.5,
            priority=1
        )

        # 3. 区别特征规则
        self.rules['DR001'] = NoveltyRule(
            rule_id='DR001',
            rule_type=NoveltyRuleType.DIFFERENCES,
            title='技术区别特征识别规则',
            description='识别发明与现有技术的区别特征',
            conditions=[
                '逐项对比技术特征',
                '分析技术参数差异',
                '评估功能效果区别',
                '考虑技术方案整体性'
            ],
            criteria=[
                '结构差异：组件、连接关系的不同',
                '参数差异：数值、范围的调整',
                '功能差异：新增或改进的功能',
                '效果差异：产生的技术效果不同'
            ],
            exceptions=[
                '简单替换',
                '常规选择',
                '数量增减'
            ],
            examples=[
                {
                    'case': '材料成分的微小调整',
                    'novelty': '可能不具备新颖性',
                    'reason': '属于本领域常规选择'
                }
            ],
            weight=1.3,
            priority=2
        )

        # 4. 进步性规则
        self.rules['PG001'] = NoveltyRule(
            rule_id='PG001',
            rule_type=NoveltyRuleType.PROGRESSIVE,
            title='技术进步性判断规则',
            description='评估发明的技术进步和创新水平',
            conditions=[
                '评估技术效果的提升',
                '分析技术难题的解决',
                '考虑商业成功因素',
                '评估技术贡献度'
            ],
            criteria=[
                '预料不到的技术效果',
                '解决了长期存在的技术难题',
                '产生了商业上的成功',
                '引领了技术发展方向'
            ],
            exceptions=[
                '常规改进',
                '显而易见的优化',
                '简单的组合'
            ],
            examples=[
                {
                    'case': '效率提升10%但未解决核心问题',
                    'novelty': '进步性有限',
                    'reason': '改进效果不显著'
                }
            ],
            weight=1.1,
            priority=3
        )

        # 5. 显而易见性规则
        self.rules['OB001'] = NoveltyRule(
            rule_id='OB001',
            rule_type=NoveltyRuleType.OBVIOUSNESS,
            title='显而易见性判断规则',
            description='判断发明对本领域技术人员是否显而易见',
            conditions=[
                '评估技术启示的存在',
                '分析技术结合的难度',
                '考虑动机和效果预期',
                '评估常规技术手段'
            ],
            criteria=[
                '单一文献的直接启示',
                '多篇文献的简单组合',
                '常规技术手段的常规选择',
                '有限次的试验可以得到的'
            ],
            exceptions=[
                '非显而易见的组合',
                '产生协同效应',
                '克服技术偏见'
            ],
            examples=[
                {
                    'case': '将已知材料用于已知设备',
                    'novelty': '显而易见',
                    'reason': '属于常规技术选择'
                }
            ],
            weight=1.4,
            priority=2
        )

        # 6. 公开充分性规则
        self.rules['DC001'] = NoveltyRule(
            rule_id='DC001',
            rule_type=NoveltyRuleType.DISCLOSURE,
            title='公开充分性规则',
            description='判断专利公开是否充分',
            conditions=[
                '技术方案的完整描述',
                '实施例的具体说明',
                '技术效果的验证',
                '可实施性的确认'
            ],
            criteria=[
                '清楚完整的技术方案',
                '能够实现的技术效果',
                '本领域技术人员能够实施',
                '必要的技术参数公开'
            ],
            exceptions=[
                '商业秘密保留',
                '核心技术参数未公开',
                '实施效果无法验证'
            ],
            examples=[
                {
                    'case': '关键工艺参数缺失',
                    'novelty': '公开不充分',
                    'reason': '无法实现发明目的'
                }
            ],
            weight=1.0,
            priority=4
        )

        logger.info(f"✅ 加载新颖性判断规则: {len(self.rules)} 条")

    def get_rules_by_type(self, rule_type: NoveltyRuleType) -> List[NoveltyRule]:
        """根据类型获取规则"""
        return [rule for rule in self.rules.values() if rule.rule_type == rule_type]

    def get_applicable_rules(self, patent_info: Dict[str, Any]) -> List[NoveltyRule]:
        """获取适用的规则"""
        applicable_rules = []

        # 基于专利信息选择适用规则
        if patent_info.get('technical_field'):
            applicable_rules.extend(self.get_rules_by_type(NoveltyRuleType.TECHNICAL_FIELD))

        if patent_info.get('claims'):
            applicable_rules.extend(self.get_rules_by_type(NoveltyRuleType.DIFFERENCES))
            applicable_rules.extend(self.get_rules_by_type(NoveltyRuleType.OBVIOUSNESS))

        if patent_info.get('specification'):
            applicable_rules.extend(self.get_rules_by_type(NoveltyRuleType.DISCLOSURE))
            applicable_rules.extend(self.get_rules_by_type(NoveltyRuleType.PROGRESSIVE))

        # 按优先级和权重排序
        applicable_rules.sort(key=lambda x: (x.priority, -x.weight))

        return applicable_rules

    def get_rule_explanation(self, rule_id: str) -> str:
        """获取规则解释"""
        rule = self.rules.get(rule_id)
        if not rule:
            return '规则不存在'

        explanation = f"""
## {rule.title}

**规则ID**: {rule_id}
**规则类型**: {rule.rule_type.value}
**权重**: {rule.weight}

### 规则描述
{rule.description}

### 判断条件
{chr(10).join(f"- {condition}" for condition in rule.conditions)}

### 判断标准
{chr(10).join(f"- {criteria}" for criteria in rule.criteria)}

### 例外情况
{chr(10).join(f"- {exception}" for exception in rule.exceptions)}

### 示例案例
{chr(10).join(f"- 案例{i+1}: {example['case']} - {example['novelty']}（{example['reason']}）" for i, example in enumerate(rule.examples))}
"""
        return explanation

class NoveltyPromptGenerator:
    """新颖性判断提示词生成器"""

    def __init__(self):
        self.knowledge_graph = NoveltyRuleKnowledgeGraph()
        self.prompt_templates = self._load_prompt_templates()

    def _load_prompt_templates(self) -> Dict[str, str]:
        """加载提示词模板"""
        return {
            "base_template": """
# 专利新颖性分析任务

## 任务说明
你是一位资深的专利审查员，具有15年的专利审查经验，精通各技术领域的专利法规定和审查实践。请对提供的专利进行全面的新颖性分析。

## 基本信息
- 专利号: {patent_number}
- 申请日: {filing_date}
- 技术领域: {technical_field}
- 发明名称: {invention_title}

## 技术内容
### 技术问题
{technical_problem}

### 技术方案
{technical_solution}

### 技术效果
{technical_effect}

### 权利要求
{claims}

## 现有技术
{prior_art_summary}

## 分析规则
{applicable_rules}

## 分析要求
1. 逐项对比权利要求与现有技术
2. 识别技术区别特征
3. 评估是否具有新颖性
4. 提供详细的判断理由
5. 给出改进建议

## 输出格式
请按照以下结构输出分析结果：

{output_format}
""",

            "output_format": """
## 新颖性分析报告

### 一、总体判断
- **新颖性结论**: [具备/不具备/部分具备]新颖性
- **置信度**: [0-100%]
- **主要判断依据**:

### 二、现有技术分析
#### 2.1 最接近的现有技术
- 对比文件:
- 公开内容:
- 技术领域:

#### 2.2 其他相关现有技术
- 文献1:
- 文献2:
- 文献3:

### 三、权利要求对比分析
#### 3.1 权利要求1
- 对比结果:
- 区别特征:
- 新颖性判断:

#### 3.2 从属权利要求
- 权利要求2:
- 权利要求3:
- ...

### 四、技术特征对比表
| 技术特征 | 本专利 | 现有技术 | 对比结果 |
|---------|--------|----------|----------|
| 特征1   |        |          |          |
| 特征2   |        |          |          |
| ...     |        |          |          |

### 五、判断理由
#### 5.1 法律依据
- 《专利法》第22条第2款:
- 《专利审查指南》相关规定:

#### 5.2 事实认定
- 技术事实:
- 对比分析:
- 结论推导:

### 六、改进建议
- 权利要求修改建议:
- 技术方案完善建议:
- 申请策略建议:

### 七、风险提示
- 可能的无效风险:
- 第三方侵权风险:
- 保护范围建议:
"""
        }

    def generate_dynamic_prompt(self, patent_info: Dict[str, Any],
                               prior_art: Optional[List[PriorArtReference] = None) -> str:
        """生成动态提示词"""

        # 1. 获取适用的规则
        applicable_rules = self.knowledge_graph.get_applicable_rules(patent_info)

        # 2. 生成规则说明
        rule_explanations = []
        for rule in applicable_rules[:5]:  # 限制规则数量
            explanation = self.knowledge_graph.get_rule_explanation(rule.rule_id)
            rule_explanations.append(f"### {rule.title}\n{explanation}")

        # 3. 处理现有技术
        prior_art_summary = '暂无现有技术对比'
        if prior_art:
            prior_art_summary = "\n".join([
                f"**{ref.patent_number or ref.publication_number}** ({ref.publication_date})\n"
                f"- 技术领域: {', '.join(ref.technical_field)}\n"
                f"- 关键特征: {', '.join(ref.key_features[:3])}\n"
                f"- 相似度: {ref.similarity_score:.3f}"
                for ref in prior_art[:5]
            ])

        # 4. 生成提示词
        prompt = self.prompt_templates['base_template'].format(
            patent_number=patent_info.get('patent_number', '未知'),
            filing_date=patent_info.get('filing_date', '未知'),
            technical_field=', '.join(patent_info.get('technical_field', [])),
            invention_title=patent_info.get('title', '未知'),
            technical_problem=patent_info.get('problem', '未提供'),
            technical_solution=patent_info.get('solution', '未提供'),
            technical_effect=patent_info.get('effect', '未提供'),
            claims=self._format_claims(patent_info.get('claims', '')),
            prior_art_summary=prior_art_summary,
            applicable_rules="\n".join(rule_explanations),
            output_format=self.prompt_templates['output_format']
        )

        # 5. 添加特定规则增强
        if self._has_multiple_applications(patent_info):
            prompt += self._generate_multiple_application_prompt()

        if self._has_biotech_invention(patent_info):
            prompt += self._generate_biotech_prompt()

        return prompt

    def _format_claims(self, claims_text: str) -> str:
        """格式化权利要求"""
        if not claims_text:
            return '未提供权利要求'

        # 清理和格式化
        claims_text = re.sub(r'权利要求(\d+)', r'### 权利要求\1', claims_text)
        claims_text = re.sub(r'[，。；;]\s*\n', '\n', claims_text)

        return claims_text

    def _has_multiple_applications(self, patent_info: Dict[str, Any]) -> bool:
        """判断是否为多项发明"""
        claims = patent_info.get('claims', '')
        return len(re.findall(r'权利要求\d+', claims)) > 10

    def _has_biotech_invention(self, patent_info: Dict[str, Any]) -> bool:
        """判断是否为生物技术发明"""
        field_keywords = ['基因', '蛋白质', '细胞', '抗体', '疫苗', '生物', '医药']
        field_text = ' '.join(patent_info.get('technical_field', []))
        title = patent_info.get('title', '')
        return any(keyword in field_text or keyword in title for keyword in field_keywords)

    def _generate_multiple_application_prompt(self) -> str:
        """生成多项发明特殊提示"""
        return """

## 多项发明特殊考虑
1. 确定是否满足单一性要求
2. 分析各项发明的相互关系
3. 考虑分案申请的可能性
4. 评估保护范围的合理性
"""

    def _generate_biotech_prompt(self) -> str:
        """生成生物技术特殊提示"""
        return """

## 生物技术发明特殊考虑
1. 考虑生物材料的保藏要求
2. 评估实验数据的完整性
3. 分析技术效果的重复性
4. 考虑伦理和法律限制
"""

class NoveltyJudgmentSystem:
    """新颖性判断系统"""

    def __init__(self):
        self.knowledge_graph = NoveltyRuleKnowledgeGraph()
        self.prompt_generator = NoveltyPromptGenerator()
        self.vector_store = None  # 集成向量库

        logger.info('🔍 新颖性判断系统初始化完成')

    async def search_prior_art(self, patent_info: Dict[str, Any],
                             top_k: int = 10) -> List[PriorArtReference]:
        """检索现有技术"""
        # 这里应该集成实际的专利检索系统
        # 目前返回模拟数据
        mock_references = [
            PriorArtReference(
                reference_id='PA001',
                patent_number='CN123456789A',
                publication_date='2023-01-15',
                title='一种类似的技术方案',
                abstract='公开了相关技术...',
                technical_field=patent_info.get('technical_field', []),
                key_features=['特征1', '特征2'],
                similarity_score=0.75,
                relevance_level='high'
            )
        ]
        return mock_references[:top_k]

    async def analyze_novelty(self, patent_info: Dict[str, Any]) -> NoveltyAnalysis:
        """执行新颖性分析"""

        logger.info(f"开始分析专利新颖性: {patent_info.get('patent_number', '未知')}")

        # 1. 检索现有技术
        prior_art = await self.search_prior_art(patent_info)

        # 2. 生成分析提示词
        analysis_prompt = self.prompt_generator.generate_dynamic_prompt(
            patent_info, prior_art
        )

        # 3. 执行AI分析（这里应该调用实际的AI模型）
        analysis_result = await self._run_ai_analysis(analysis_prompt)

        # 4. 解析分析结果
        novelty_analysis = self._parse_analysis_result(
            patent_info, prior_art, analysis_result
        )

        logger.info(f"新颖性分析完成: {novelty_analysis.overall_judgment}")

        return novelty_analysis

    async def _run_ai_analysis(self, prompt: str) -> str:
        """运行AI分析"""
        # 这里应该集成实际的AI模型
        # 目前返回模拟结果
        await asyncio.sleep(1)  # 模拟处理时间

        return """
## 新颖性分析报告

### 一、总体判断
- **新颖性结论**: 部分具备新颖性
- **置信度**: 75%
- **主要判断依据**: 权利要求1不具备新颖性，但从属权利要求2-5具备新颖性

### 二、现有技术分析
#### 2.1 最接近的现有技术
- 对比文件: CN123456789A
- 公开内容: 公开了技术方案的大部分特征
- 技术领域: 相同技术领域

### 三、权利要求对比分析
#### 3.1 权利要求1
- 对比结果: 被现有技术完全公开
- 区别特征: 无
- 新颖性判断: 不具备新颖性

#### 3.2 权利要求2-5
- 对比结果: 包含区别特征
- 区别特征: 新增技术特征A、B
- 新颖性判断: 具备新颖性
"""

    def _parse_analysis_result(self, patent_info: Dict[str, Any],
                             prior_art: List[PriorArtReference],
                             analysis_result: str) -> NoveltyAnalysis:
        """解析分析结果"""

        # 简单的解析逻辑，实际应该更复杂
        if '不具备新颖性' in analysis_result:
            judgment = 'non-novel'
        elif '具备新颖性' in analysis_result:
            judgment = 'novel'
        else:
            judgment = 'partially_novel'

        return NoveltyAnalysis(
            patent_id=patent_info.get('patent_number', '未知'),
            analysis_date=datetime.now(),
            overall_judgment=judgment,
            confidence_score=0.75,
            key_differences=['技术特征A', '技术特征B'],
            similar_references=prior_art,
            applied_rules=['TR001', 'ER001', 'DR001'],
            reasoning_chain=['现有技术对比', '区别特征分析', '新颖性判断'],
            recommendations=['修改权利要求1', '强调区别特征'],
            evidence_sources=['CN123456789A', '科技文献1']
        )

# 全局系统实例
novelty_judgment_system = NoveltyJudgmentSystem()

# 测试代码
if __name__ == '__main__':
    import asyncio

    async def test_novelty_judgment():
        """测试新颖性判断系统"""
        logger.info('🔍 测试新颖性判断系统...')

        # 测试专利信息
        patent_info = {
            'patent_number': 'CN202312345678.9',
            'title': '一种智能感知系统的优化方法',
            'technical_field': ['人工智能', '图像识别', '深度学习'],
            'problem': '现有感知系统准确率不高的问题',
            'solution': '采用改进的神经网络结构和训练方法',
            'effect': '准确率提升15%，速度提升20%',
            "claims": """
            ### 权利要求1
            一种智能感知系统的优化方法，其特征在于包括：
            步骤1：数据预处理；
            步骤2：特征提取；
            步骤3：模型训练；

            ### 权利要求2
            根据权利要求1所述的方法，其特征在于：
            所述步骤1采用归一化处理。
            """
        }

        # 执行新颖性分析
        analysis = await novelty_judgment_system.analyze_novelty(patent_info)

        logger.info(f"\n📊 新颖性分析结果:")
        logger.info(f"  专利号: {analysis.patent_id}")
        logger.info(f"  判断结果: {analysis.overall_judgment}")
        logger.info(f"  置信度: {analysis.confidence_score:.2%}")
        logger.info(f"  关键区别: {', '.join(analysis.key_differences)}")

        return True

    # 运行测试
    result = asyncio.run(test_novelty_judgment())
    logger.info(f"\n🎯 新颖性判断系统测试: {'成功' if result else '失败'}")