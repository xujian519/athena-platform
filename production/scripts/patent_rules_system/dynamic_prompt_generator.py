#!/usr/bin/env python3
"""
动态提示词生成器 - 增强版
Dynamic Prompt Generator - Enhanced Version

基于专利规则向量库和知识图谱生成精准的行业提示词

作者: Athena平台团队
创建时间: 2025-12-20
版本: v2.0.0
"""

from __future__ import annotations
import asyncio
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from qdrant_vector_store_simple import QdrantVectorStoreSimple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DynamicPromptGenerator:
    """动态提示词生成器"""

    def __init__(self):
        self.vector_store = QdrantVectorStoreSimple()

        # 提示词模板
        self.templates = {
            'patent_drafting': {
                'title': '专利撰写助手',
                'keywords': ['撰写', '起草', '权利要求', '说明书'],
                'template': """
【专利撰写助手】
任务：{task}
技术领域：{tech_field}
发明点：{invention}

【相关法规依据】:
{relevant_rules}

【撰写要点】:
1. 权利要求书应当：
   - 清楚、简要地限定要求专利保护的范围
   - 以说明书为依据
   - 独立权利要求应当整体反映发明的技术方案

2. 说明书应当：
   - 对发明作出清楚、完整的说明
   - 达到所属技术领域的技术人员能够实现的程度
   - 包含技术问题、技术方案、有益效果

【专业提示】:
- 根据技术特征构建合适的权利要求层次
- 使用规范的专利术语和法律用语
- 注意满足专利法第26条的要求
"""
            },
            'patent_examination': {
                'title': '专利审查助手',
                'keywords': ['审查', '授权', '驳回', '三性'],
                'template': """
【专利审查助手】
审查类型：{exam_type}
技术方案：{tech_solution}

【审查标准依据】:
{relevant_rules}

【审查要点】:
1. 新颖性审查：
   - 是否属于现有技术
   - 是否存在同样的发明在先申请

2. 创造性审查：
   - 是否具有突出的实质性特点
   - 是否具有显著的进步

3. 实用性审查：
   - 是否能够在产业上制造或使用
   - 是否能产生积极效果

【审查结论】:
{conclusion}
"""
            },
            'patent_infringement': {
                'title': '专利侵权分析助手',
                'keywords': ['侵权', '保护范围', '等同', '全面覆盖'],
                'template': """
【专利侵权分析助手】
涉案专利：{patent_number}
被控侵权产品/方法：{accused_product}

【法律依据】:
{relevant_rules}

【侵权判定分析】:
1. 字面侵权：
   - 被控侵权技术方案是否包含权利要求全部技术特征

2. 等同侵权：
   - 是否以基本相同的手段
   - 实现基本相同的功能
   - 达到基本相同的效果
   - 所属领域技术人员无需创造性劳动

【分析结论】:
{conclusion}
"""
            },
            'patent_strategy': {
                'title': '专利布局策略助手',
                'keywords': ['布局', '战略', '组合', '壁垒'],
                'template': """
【专利布局策略助手】
企业类型：{company_type}
技术领域：{tech_field}
业务目标：{business_goal}

【策略依据】:
{relevant_rules}

【布局建议】:
1. 核心技术专利：
   - 围绕关键技术创新点构建专利组合
   - 形成基础专利和改进专利的层次结构

2. 外围专利布局：
   - 延伸技术应用的周边领域
   - 构建专利池和专利联盟

3. 国际专利申请：
   - 根据目标市场选择PCT或直接申请
   - 考虑不同国家的保护期限和费用

【风险提示】:
- 注意避免专利悬崖
- 关注竞争对手的专利布局
- 定期进行专利有效性评估
"""
            },
            'patent_filing': {
                'title': '专利申请流程助手',
                'keywords': ['申请', '提交', '流程', '期限'],
                'template': """
【专利申请流程助手】
申请类型：{application_type}
目标国家/地区：{target_region}

【申请流程指南】:
{relevant_rules}

【关键时间节点】:
1. 申请准备阶段：
   - 进行专利检索
   - 准备申请文件
   - 确定申请策略

2. 提交申请：
   - 提交专利申请文件
   - 缴纳申请费用
   - 获得申请号

3. 审查阶段：
   - 初步审查（实用新型/外观设计）
   - 实质审查（发明专利）
   - 答复审查意见

【费用提示】:
- 申请费：{application_fee}
- 审查费：{examination_fee}
- 年费：{annual_fee}
"""
            }
        }

    async def generate_prompt(self, task: str, context: dict[str, Any] = None, mode: str = 'auto') -> dict[str, Any]:
        """生成动态提示词"""

        # 1. 识别任务类型
        prompt_type = self._identify_task_type(task, context)

        # 2. 检索相关法规
        relevant_rules = await self._retrieve_relevant_rules(task, prompt_type)

        # 3. 提取关键信息
        key_info = self._extract_key_info(task, context)

        # 4. 选择并填充模板
        template = self.templates.get(prompt_type, self._get_fallback_template())
        prompt = self._fill_template(template, key_info, relevant_rules)

        # 5. 生成建议和补充
        suggestions = await self._generate_suggestions(task, relevant_rules)

        return {
            'task': task,
            'type': prompt_type,
            'prompt': prompt,
            'relevant_rules': relevant_rules,
            'suggestions': suggestions,
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'template_used': template.get('title', '通用模板'),
                'rules_count': len(relevant_rules)
            }
        }

    def _identify_task_type(self, task: str, context: dict[str, Any] = None) -> str:
        """识别任务类型"""
        task_lower = task.lower()

        # 基于关键词识别
        for ptype, template in self.templates.items():
            for keyword in template['keywords']:
                if keyword in task_lower:
                    return ptype

        # 基于上下文识别
        if context:
            if '撰写' in task_lower or '起草' in task_lower:
                return 'patent_drafting'
            elif '审查' in task_lower or '三性' in task_lower:
                return 'patent_examination'
            elif '侵权' in task_lower or '保护范围' in task_lower:
                return 'patent_infringement'
            elif '布局' in task_lower or '战略' in task_lower:
                return 'patent_strategy'
            elif '申请' in task_lower or '流程' in task_lower:
                return 'patent_filing'

        # 默认返回撰写助手
        return 'patent_drafting'

    async def _retrieve_relevant_rules(self, task: str, prompt_type: str) -> list[dict[str, Any]]:
        """检索相关法规"""
        rules = []

        # 构建查询
        keywords = self.templates.get(prompt_type, {}).get('keywords', [])
        queries = [task] + keywords

        # 合并查询结果
        for query in queries[:3]:  # 限制查询次数
            try:
                results = await self.vector_store.search(
                    query=query,
                    top_k=3,
                    search_mode="hybrid"
                )
                rules.extend(results)
            except Exception as e:
                logger.warning(f"查询失败: {query} - {str(e)}")

        # 去重并排序
        unique_rules = []
        seen_content = set()

        for rule in rules:
            content_hash = hash(rule.content[:100])
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_rules.append({
                    'content': rule.content,
                    'source': rule.metadata.get('document_title', 'unknown'),
                    'type': rule.doc_type.value,
                    'score': rule.score
                })

        # 按相关性排序
        unique_rules.sort(key=lambda x: x['score'], reverse=True)

        return unique_rules[:5]  # 返回前5个最相关的

    def _extract_key_info(self, task: str, context: dict[str, Any] = None) -> dict[str, Any]:
        """提取关键信息"""
        key_info = {'task': task}

        # 从上下文提取
        if context:
            for key, value in context.items():
                if value:
                    key_info[key] = value

        # 从任务描述提取
        # 提取技术领域
        tech_fields = ['人工智能', 'AI', '机器学习', '深度学习', '生物医药', '新能源',
                      '通信', '互联网', '物联网', '区块链', '自动驾驶', '新能源']
        for field in tech_fields:
            if field in task:
                key_info['tech_field'] = field
                break

        # 提取专利号
        patent_pattern = r'(?:CN|US|WO|EP)\s*\d+[A-Z]?'
        patent_match = re.search(patent_pattern, task)
        if patent_match:
            key_info['patent_number'] = patent_match.group()

        return key_info

    def _fill_template(self, template: dict[str, Any], key_info: dict[str, Any],
                      relevant_rules: list[dict[str, Any]]) -> str:
        """填充模板"""
        prompt_template = template['template']

        # 格式化相关法规
        rules_text = ""
        for i, rule in enumerate(relevant_rules[:3], 1):
            rules_text += f"{i}. [{rule['type']}] {rule['content'][:150]}...\n"

        # 填充变量
        filled_prompt = prompt_template.format(
            task=key_info.get('task', ''),
            tech_field=key_info.get('tech_field', '未指定'),
            invention=key_info.get('invention', '待描述'),
            relevant_rules=rules_text or "暂无相关法规",
            exam_type=key_info.get('exam_type', '专利申请'),
            tech_solution=key_info.get('tech_solution', '技术方案待分析'),
            conclusion=key_info.get('conclusion', '需要进一步分析'),
            patent_number=key_info.get('patent_number', '专利号待定'),
            accused_product=key_info.get('accused_product', '被控侵权产品/方法'),
            company_type=key_info.get('company_type', '科技企业'),
            business_goal=key_info.get('business_goal', '技术创新保护'),
            application_type=key_info.get('application_type', '发明专利'),
            target_region=key_info.get('target_region', '中国'),
            application_fee=key_info.get('application_fee', '根据专利类型确定'),
            examination_fee=key_info.get('examination_fee', '发明专利需实质审查费'),
            annual_fee=key_info.get('annual_fee', '逐年递增')
        )

        return filled_prompt

    def _get_fallback_template(self) -> dict[str, Any]:
        """获取备用模板"""
        return {
            'title': '通用专利助手',
            'template': """
【专利事务助手】
任务：{task}

【相关法规依据】:
{relevant_rules}

【处理建议】:
1. 根据具体需求选择合适的专利策略
2. 确保符合专利法及相关法规要求
3. 建议咨询专业专利代理人

【重要提示】:
- 专利事务具有较强的专业性
- 不同国家/地区的规定存在差异
- 注意 deadlines 和时效性要求
"""
        }

    async def _generate_suggestions(self, task: str, relevant_rules: list[dict[str, Any]]) -> list[str]:
        """生成建议"""
        suggestions = []

        # 基于任务类型生成建议
        if '撰写' in task or '起草' in task:
            suggestions = [
                "建议先进行专利检索，避免重复申请",
                "权利要求书应该层次分明，独立权利要求限定必要技术特征",
                "说明书应该充分公开，达到能够实现的程度"
            ]
        elif '审查' in task:
            suggestions = [
                "审查时需重点关注新颖性、创造性、实用性",
                "注意审查意见的答复期限",
                "必要时可以修改申请文件或申请复审"
            ]
        elif '侵权' in task:
            suggestions = [
                "侵权判定需要全面覆盖原则",
                "注意等同原则的适用条件",
                "建议进行专业的侵权风险评估"
            ]
        else:
            suggestions = [
                "建议明确具体需求，以便提供更精准的帮助",
                "可以提供更多背景信息，如技术领域、专利号等",
                "复杂问题建议咨询专业专利律师或代理人"
            ]

        # 基于相关法规补充建议
        if relevant_rules:
            top_rule = relevant_rules[0]
            if '实施细则' in top_rule['source']:
                suggestions.append("参考专利法实施细则的具体要求")
            elif '审查指南' in top_rule['source']:
                suggestions.append("请参考专利审查指南的具体规定")

        return suggestions

    async def multi_turn_dialogue(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        """支持多轮对话"""
        # 提取最新的用户消息
        user_message = None
        for msg in reversed(messages):
            if msg['role'] == 'user':
                user_message = msg['content']
                break

        if not user_message:
            return {'error': '没有找到用户消息'}

        # 从历史消息中提取上下文
        context = {'history': messages[:-1]}

        # 生成提示词
        return await self.generate_prompt(user_message, context)


async def test_generator():
    """测试提示词生成器"""
    generator = DynamicPromptGenerator()

    test_cases = [
        {
            'task': '帮我撰写一个关于人工智能图像识别的发明专利权利要求',
            'context': {'tech_field': '人工智能', 'invention': '基于深度学习的图像识别方法'}
        },
        {
            'task': '判断一项技术方案是否具有创造性',
            'context': {'exam_type': '实质审查', 'tech_solution': '使用AI优化算法'}
        },
        {
            'task': '分析CN123456789A是否侵犯CN987654321B的专利权',
            'context': {'patent_number': 'CN123456789A', 'accused_product': '智能设备'}
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"测试用例 {i}: {test_case['task']}")
        print(f"{'='*60}")

        result = await generator.generate_prompt(
            task=test_case['task'],
            context=test_case['context']
        )

        print(f"\n任务类型: {result['type']}")
        print(f"使用模板: {result['metadata']['template_used']}")
        print(f"相关法规数: {result['metadata']['rules_count']}")

        print("\n生成的提示词:")
        print("-"*60)
        print(result['prompt'])
        print("-"*60)

        print("\n建议:")
        for j, suggestion in enumerate(result['suggestions'], 1):
            print(f"  {j}. {suggestion}")


if __name__ == "__main__":
    asyncio.run(test_generator())
