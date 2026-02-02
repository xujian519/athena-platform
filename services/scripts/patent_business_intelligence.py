#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专利业务智能系统
基于知识图谱提取动态提示词和规则，支持专利撰写、分析等全部专利业务

作者：小娜
日期：2025-12-07
"""

import json
from core.async_main import async_main
import logging
from core.logging_config import setup_logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import jieba
import jieba.analyse
from neo4j import GraphDatabase

# 导入安全配置
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "core"))
from security.env_config import get_env_var, get_database_url, get_jwt_secret

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

class PatentBusinessIntelligence:
    """专利业务智能系统"""

    def __init__(self):
        self.neo4j_uri = 'bolt://localhost:7687'
        self.neo4j_user = 'neo4j'
        self.neo4j_password=os.getenv("DB_PASSWORD", "password")
        self.driver = None

        # 知识图谱数据路径
        self.kg_data_path = Path('/Users/xujian/Athena工作平台/data/knowledge_graph_neo4j/raw_data')

        # 专利业务规则库
        self.rules = {
            '专利撰写规则': self._extract_patent_writing_rules(),
            '专利分析规则': self._extract_patent_analysis_rules(),
            '专利审查规则': self._extract_patent_examination_rules(),
            '专利无效规则': self._extract_patent_invalid_rules(),
            '专利诉讼规则': self._extract_patent_litigation_rules()
        }

        # 动态提示词模板
        self.prompt_templates = {
            '专利撰写': self._generate_writing_prompts(),
            '专利分析': self._generate_analysis_prompts(),
            '专利检索': self._generate_search_prompts(),
            '专利评估': self._generate_evaluation_prompts(),
            '专利预警': self._generate_warning_prompts()
        }

    def connect_neo4j(self) -> Any:
        """连接Neo4j数据库"""
        try:
            self.driver = GraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_password)
            )
            return True
        except Exception as e:
            logger.error(f"连接Neo4j失败: {e}")
            return False

    def _extract_patent_writing_rules(self) -> Dict:
        """从知识图谱提取专利撰写规则"""
        rules = {
            '技术方案描述': {
                '规则': '必须清晰、完整地描述技术方案，使所属技术领域的技术人员能够理解和实施',
                '要点': [
                    '要解决的技术问题',
                    '采用的技术方案',
                    '有益效果'
                ],
                '来源': '专利法第26条第3款'
            },
            '权利要求撰写': {
                '规则': '应当以说明书为依据，清楚、简要地限定要求专利保护的范围',
                '要点': [
                    '独立权利要求应包含解决技术问题的必要技术特征',
                    '从属权利要求应包含附加技术特征',
                    '避免使用模糊或含义不清的用语'
                ],
                '来源': '专利法第26条第4款'
            },
            '说明书支持': {
                '规则': '说明书应当对权利要求书作清楚、完整的说明',
                '要点': [
                    '技术领域背景',
                    '发明内容',
                    '具体实施方式',
                    '附图说明（如有）'
                ],
                '来源': '专利法实施细则第18条'
            }
        }

        # 从判决案例中提取实际应用规则
        if self.connect_neo4j():
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (case:案件)-[:CONTAINS]->(patent:专利)
                    WHERE case.case_type = '专利行政案件'
                    RETURN case.case_number, court.case_level
                    LIMIT 10
                """)

                for record in result:
                    rules['案例参考'] = rules.get('案例参考', [])
                    rules['案例参考'].append({
                        '案件号': record['case.case_number'],
                        '法院': record['court.case_level'],
                        '启示': '参考法院在专利撰写要求方面的判决要点'
                    })

        return rules

    def _extract_patent_analysis_rules(self) -> Dict:
        """提取专利分析规则"""
        return {
            '技术分析': {
                '规则': '从技术角度分析专利的创新性和实用性',
                '维度': [
                    '技术方案的新颖性',
                    '技术效果的显著性',
                    '技术实现的可行性'
                ]
            },
            '法律分析': {
                '规则': '从法律角度评估专利的保护范围和稳定性',
                '维度': [
                    '权利要求的清晰度',
                    '保护范围的合理性',
                    '法律风险的识别'
                ]
            },
            '市场分析': {
                '规则': '从市场角度评估专利的商业价值',
                '维度': [
                    '技术市场的应用前景',
                    '竞争对手的技术布局',
                    '专利的货币化潜力'
                ]
            }
        }

    def _extract_patent_examination_rules(self) -> Dict:
        """提取专利审查规则"""
        return {
            '新颖性审查': {
                '标准': '不属于现有技术',
                '现有技术定义': '申请日以前在国内外为公众所知的技术',
                '审查要点': '进行全面检索，对比最接近的现有技术'
            },
            '创造性审查': {
                '标准': '与现有技术相比具有突出的实质性特点和显著的进步',
                '三步法': [
                    '确定最接近的现有技术',
                    '确定发明的区别特征',
                    '判断是否具备创造性'
                ]
            },
            '实用性审查': {
                '标准': '能够制造或使用，并产生积极效果',
                '排除情形': '科学发现、智力活动规则、疾病诊断治疗方法等'
            }
        }

    def _extract_patent_invalid_rules(self) -> Dict:
        """提取专利无效宣告规则"""
        return {
            '无效理由': {
                '法条依据': '专利法第45条、第46条',
                '主要理由': [
                    '缺乏新颖性',
                    '缺乏创造性',
                    '缺乏实用性',
                    '说明书公开不充分',
                    '权利要求书得不到说明书支持'
                ]
            },
            '证据规则': {
                '证据形式': '对比文件、公知常识、使用公开等',
                '证据效力': '优先考虑专利文献，其次是期刊论文、技术标准等'
            }
        }

    def _extract_patent_litigation_rules(self) -> Dict:
        """提取专利诉讼规则"""
        return {
            '侵权判定': {
                '原则': '全面覆盖原则',
                '等同原则': '以基本相同的手段、实现基本相同的功能、达到基本相同的效果',
                '禁止反悔原则': '专利权人曾经在审查过程中放弃的技术方案不能在侵权诉讼中主张'
            },
            '诉讼策略': {
                '证据收集': '技术对比报告、专家意见、销售记录等',
                '抗辩理由': '现有技术抗辩、先用权抗辩、合法来源抗辩等'
            }
        }

    def _generate_writing_prompts(self) -> Dict:
        """生成专利撰写动态提示词"""
        prompts = {
            "技术方案": """
请基于以下技术要点撰写专利申请的技术方案部分：

技术背景：{background}
技术问题：{problem}
解决方案：{solution}

要求：
1. 清晰描述技术领域和背景技术
2. 明确要解决的技术问题
3. 详细描述技术方案，包括技术特征的组合关系
4. 说明技术方案带来的有益效果

请确保描述满足专利法第26条第3款的要求，使本领域技术人员能够理解和实施。
            """.strip(),

            "权利要求": """
基于上述技术方案，撰写权利要求书：

独立权利要求（1项）：
- 包含解决技术问题的全部必要技术特征
- 使用'包括...'、'其特征在于...'等标准表述

从属权利要求（3-5项）：
- 在引用权利要求的基础上增加附加技术特征
- 进一步限定保护范围
- 形成层次分明的保护体系

注意：权利要求应当以说明书为依据，清楚、简要地限定保护范围。
            """.strip(),

            "实施例": """
提供1-3个具体实施例，详细描述技术方案的实现方式：

实施例1：
- 详细描述具体的技术参数、结构组成
- 说明各部件的连接关系和工作原理
- 提供具体的操作步骤或制作方法

实施例2（可选）：
- 变形实施方式
- 不同的参数范围或材料选择

要求：实施例应当支持权利要求书限定的保护范围。
            """.strip()
        }

        return prompts

    def _generate_analysis_prompts(self) -> Dict:
        """生成专利分析动态提示词"""
        return {
            "专利性分析": """
分析以下专利的专利性：

专利号：{patent_number}
技术领域：{tech_field}
技术方案：{solution}

分析维度：
1. 新颖性：检索对比文件，评估是否为现有技术
2. 创造性：与最接近现有技术对比，判断是否有实质性特点和显著进步
3. 实用性：评估是否能够制造或使用并产生积极效果

请提供详细的对比分析和结论。
            """.strip(),

            "稳定性评估": """
评估专利的权利稳定性：

权利要求：{claims}
说明书：{description}
审查档案：{prosecution_history}

评估要点：
1. 权利要求是否得到说明书支持
2. 是否存在无效宣告风险
3. 保护范围是否合理
4. 是否存在撰写缺陷

请提供风险等级（高/中/低）和改进建议。
            """.strip(),

            "侵权风险评估": """
评估产品/技术的侵权风险：

对比专利：{patent}
涉嫌侵权产品/技术：{product}

分析步骤：
1. 解读专利权利要求的保护范围
2. 分析被诉侵权技术方案的技术特征
3. 逐一比对技术特征，判断是否构成相同或等同
4. 评估抗辩可能性

请提供侵权风险结论和应对建议。
            """.strip()
        }

    def _generate_search_prompts(self) -> Dict:
        """生成专利检索动态提示词"""
        return {
            "查新检索": """
为以下技术方案进行专利查新检索：

技术要点：{tech_points}
关键词：{keywords}
技术领域：{field}

检索策略：
1. 构建检索式：
   - 关键词组合
   - IPC/CPC分类号限定
   - 时间范围限定
2. 检索数据库：
   - 中文专利库
   - 外文专利库
   - 非专利文献
3. 检索结果分析：
   - 相关度排序
   - 对比文件筛选
   - 新颖性判断

请输出检索报告和对比分析。
            """.strip(),

            "无效检索": """
为专利无效宣告进行证据检索：

目标专利：{target_patent}
无效理由：{invalid_reason}
需要检索的对比文件类型：{doc_types}

检索重点：
1. 最早公开日之前的相关技术
2. 与技术方案最接近的对比文件
3. 影响创造性的组合证据
4. 公知常识证据

请提供检索式、相关文献清单和法律效力分析。
            """.strip(),

            "FTO检索": """
为产品上市进行自由实施(FTO)检索：

产品技术方案：{product_tech}
目标市场：{market}
检索时间范围：{time_range}

检索目标：
1. 确定可能侵权的高风险专利
2. 评估侵权风险等级
3. 提供设计绕过建议
4. 制定风险应对策略

请输出高风险专利清单和风险分析报告。
            """.strip()
        }

    def _generate_evaluation_prompts(self) -> Dict:
        """生成专利评估动态提示词"""
        return {
            "技术价值评估": """
评估专利的技术创新价值：

专利技术：{patent_tech}
所属技术领域：{tech_field}
技术发展阶段：{tech_stage}

评估维度：
1. 技术先进性：与国际/国内领先水平对比
2. 技术成熟度：技术发展阶段和产业化程度
3. 技术壁垒：技术难度和替代难度
4. 应用前景：潜在应用领域和市场空间

请提供评分（1-10分）和详细评估说明。
            """.strip(),

            "经济价值评估": """
评估专利的经济价值：

专利号：{patent_number}
专利类型：{patent_type}
剩余保护期：{remaining_years}
技术领域：{tech_field}

评估方法：
1. 成本法：研发投入和维护成本
2. 市场法：可比专利交易价格
3. 收益法：未来收益折现
4. 综合评估：考虑战略价值

请输出评估结果和估值范围。
            """.strip(),

            "投资价值评估": """
评估专利/专利包的投资价值：

专利组合：{patent_portfolio}
技术领域：{tech_field}
市场前景：{market_outlook}

投资分析：
1. 技术壁垒和市场独占性
2. 商业化路径和盈利模式
3. 风险因素（法律风险、技术风险、市场风险）
4. 投资回报预测
5. 退出机制

请提供投资建议和风险提示。
            """.strip()
        }

    def _generate_warning_prompts(self) -> Dict:
        """生成专利预警动态提示词"""
        return {
            "侵权监控": """
监控以下领域的潜在侵权风险：

监控范围：{monitor_scope}
关键词/技术特征：{keywords}
监控对象：{target_companies}

预警机制：
1. 定期检索新发布的专利申请
2. 监控竞争对手的技术动态
3. 跟踪相关技术领域的发展趋势
4. 识别潜在的侵权风险

请设置预警阈值和响应流程。
            """.strip(),

            "技术预警": """
关注以下技术领域的发展预警：

技术领域：{tech_field}
关键技术点：{key_tech}
跟踪指标：{metrics}

预警内容：
1. 突破性技术进展
2. 标准必要专利布局
3. 专利诉讼动态
4. 监管政策变化
5. 市场竞争态势

请提供预警等级和应对建议。
            """.strip(),

            "法律状态监控": """
监控目标专利的法律状态变化：

专利清单：{patent_list}
监控内容：{monitor_items}
频率：{frequency}

监控要点：
1. 年费缴纳情况
2. 专利权转移
3. 许可备案情况
4. 无效宣告请求
5. 诉讼动态

请及时更新专利资产清单并提示风险。
            """.strip()
        }

    def get_patent_writing_assistant(self, tech_info: Dict) -> Dict:
        """获取专利撰写助手"""
        return {
            '规则指引': self.rules['专利撰写规则'],
            '撰写模板': self.prompt_templates['专利撰写'],
            '建议': self._generate_writing_suggestions(tech_info)
        }

    def get_patent_analysis_assistant(self, patent_info: Dict) -> Dict:
        """获取专利分析助手"""
        return {
            '分析规则': self.rules['专利分析规则'],
            '分析模板': self.prompt_templates['专利分析'],
            '知识支持': self._get_relevant_case_law(patent_info)
        }

    def get_patent_strategy_assistant(self, business_goal: str) -> Dict:
        """获取专利策略助手"""
        strategy_map = {
            '防御型布局': {
                '要点': '构建专利护城河，防止竞争对手进入',
                '策略': '围绕核心产品申请基础专利和改进专利',
                '提示词': self._generate_defensive_strategy_prompt()
            },
            '进攻型布局': {
                '要点': '通过专利申请抢占技术制高点，制约对手',
                '策略': '在关键技术节点提前布局，形成专利网',
                '提示词': self._generate_offensive_strategy_prompt()
            },
            '货币化布局': {
                '要点': '通过专利许可、转让实现商业价值',
                '策略': '选择市场价值高的技术进行专利布局',
                '提示词': self._generate_monetization_strategy_prompt()
            }
        }

        return strategy_map.get(business_goal, {})

    def _generate_writing_suggestions(self, tech_info: Dict) -> List[str]:
        """生成撰写建议"""
        suggestions = []

        # 基于技术领域提供建议
        if '机械' in tech_info.get('field', ''):
            suggestions.append('重点描述结构特征、连接关系和工作原理')
        elif '电子' in tech_info.get('field', ''):
            suggestions.append('详细描述电路连接、信号流程和控制逻辑')
        elif '化学' in tech_info.get('field', ''):
            suggestions.append('清楚说明反应条件、制备方法和产品性能')

        # 基于创新点提供建议
        if tech_info.get('innovation_type') == '改进型':
            suggestions.append('突出改进点相对于现有技术的优势')
        elif tech_info.get('innovation_type') == '组合型':
            suggestions.append('说明技术特征组合带来的协同效应')

        return suggestions

    def _get_relevant_case_law(self, patent_info: Dict) -> List[Dict]:
        """获取相关判例"""
        relevant_cases = []

        if self.connect_neo4j():
            with self.driver.session() as session:
                # 查询相关判例
                result = session.run("""
                    MATCH (case:案件)-[:CONTAINS]->(patent:专利)
                    WHERE case.case_type = '专利行政案件' OR case.case_type = '专利民事案件'
                    RETURN case.case_number, case.court, case.procedure
                    LIMIT 5
                """)

                for record in result:
                    relevant_cases.append({
                        '案件号': record['case.case_number'],
                        '审理法院': record['case.court'],
                        '审理程序': record['case.procedure']
                    })

        return relevant_cases

    def _generate_defensive_strategy_prompt(self) -> str:
        """生成防御型策略提示词"""
        return """
作为专利防御策略顾问，请为以下业务场景制定专利防御布局方案：

核心产品：{core_product}
主要竞争对手：{competitors}
技术保护需求：{protection_needs}

防御策略要点：
1. 核心专利：围绕产品关键技术创新点申请基础专利
2. 外围专利：在改进技术、应用场景等方面形成保护圈
3. 防御性公开：对无法或不值得专利的技术进行防御性公开
4. 专利组合：构建多层次、立体化的专利保护体系

请输出详细的防御策略方案。
        """.strip()

    def _generate_offensive_strategy_prompt(self) -> str:
        """生成进攻型策略提示词"""
        return """
作为专利进攻策略顾问，请制定专利进攻布局策略：

目标市场：{target_market}
技术制高点：{tech_dominance}
竞争对手弱点：{competitor_weakness}

进攻策略要点：
1. 基础专利：在关键技术源头进行专利布局
2. 标准专利：推动技术标准化，获取标准必要专利
3. 专利网：在技术演进路径上提前布局
4. 诉讼威慑：通过专利组合形成威慑力

请制定进攻策略实施方案。
        """.strip()

    def _generate_monetization_strategy_prompt(self) -> str:
        """生成货币化策略提示词"""
        return """
作为专利货币化策略顾问，请制定专利商业化方案：

专利资产：{patent_assets}
目标市场：{target_market}
商业模式：{business_model}

货币化路径：
1. 专利许可：制定许可策略和定价方案
2. 专利转让：筛选高价值专利进行转让
3. 专利运营：通过专利池、交叉许可等方式
4. 专利金融：专利质押融资、证券化等

请输出专利货币化具体方案。
        """.strip()

    def export_knowledge_base(self, output_path: str) -> Any:
        """导出知识库"""
        knowledge_base = {
            '更新时间': datetime.now().isoformat(),
            '专利业务规则': self.rules,
            '动态提示词模板': self.prompt_templates,
            '应用场景': {
                '专利撰写': '支持发明人撰写高质量的专利申请文件',
                '专利分析': '提供全方位的专利分析视角和工具',
                '专利检索': '制定高效的检索策略和方案',
                '专利评估': '多维度评估专利价值',
                '专利预警': '主动识别和应对专利风险'
            }
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(knowledge_base, f, ensure_ascii=False, indent=2)

        logger.info(f"知识库已导出到: {output_path}")


def main() -> None:
    """主函数 - 测试系统功能"""
    pbi = PatentBusinessIntelligence()

    # 测试专利撰写助手
    tech_info = {
        'field': '电子通信',
        'innovation_type': '改进型',
        'problem': '如何提高信号传输效率',
        'solution': '采用新型调制技术'
    }

    logger.info(str('='*60))
    logger.info('专利撰写助手测试')
    logger.info(str('='*60))
    writing_assistant = pbi.get_patent_writing_assistant(tech_info)
    print(json.dumps(writing_assistant, ensure_ascii=False, indent=2)[:500] + '...')

    # 测试专利分析助手
    patent_info = {
        'patent_number': 'CN123456789',
        'tech_field': '人工智能',
        'claims': '一种机器学习算法...'
    }

    logger.info(str("\n" + '='*60))
    logger.info('专利分析助手测试')
    logger.info(str('='*60))
    analysis_assistant = pbi.get_patent_analysis_assistant(patent_info)
    print(json.dumps(analysis_assistant, ensure_ascii=False, indent=2)[:500] + '...')

    # 测试专利策略助手
    logger.info(str("\n" + '='*60))
    logger.info('专利策略助手测试')
    logger.info(str('='*60))
    strategy_assistant = pbi.get_patent_strategy_assistant('防御型布局')
    print(json.dumps(strategy_assistant, ensure_ascii=False, indent=2)[:500] + '...')

    # 导出知识库
    output_path = '/Users/xujian/Athena工作平台/data/support_data/reports/patent_business_knowledge_base.json'
    pbi.export_knowledge_base(output_path)
    logger.info(f"\n知识库已导出到: {output_path}")


if __name__ == '__main__':
    main()