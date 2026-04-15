#!/usr/bin/env python3
"""
专利业务知识库系统
基于专利知识图谱提取的规则和提示词，支持专利撰写、分析等全部专利业务

作者：小娜
日期：2025-12-07
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

class PatentBusinessKnowledgeBase:
    """专利业务知识库"""

    def __init__(self):
        # 专利业务规则库
        self.rules = self._load_business_rules()

        # 动态提示词模板库
        self.prompts = self._load_prompt_templates()

        # 专利撰写模板库
        self.templates = self._load_writing_templates()

        # 专利审查标准库
        self.examination_standards = self._load_examination_standards()

        # 专利案例库
        self.case_law = self._load_case_law()

    def _load_business_rules(self) -> dict:
        """加载专利业务规则"""
        return {
            '专利撰写': {
                '技术方案要求': {
                    '法条': '专利法第26条第3款',
                    '要求': '说明书应当对发明作出清楚、完整的说明，以所属技术领域的技术人员能够实现为准',
                    '要点': [
                        '技术问题：明确要解决的技术问题',
                        '技术方案：清楚、完整地描述技术方案',
                        '有益效果：说明技术方案带来的有益效果'
                    ]
                },
                '权利要求书要求': {
                    '法条': '专利法第26条第4款',
                    '要求': '权利要求书应当以说明书为依据，清楚、简要地限定要求专利保护的范围',
                    '要点': [
                        '独立权利要求包含必要技术特征',
                        '从属权利要求增加附加技术特征',
                        '用语应当清楚、简要'
                    ]
                },
                '修改规则': {
                    '法条': '专利法第33条',
                    '要求': '对发明和实用新型专利申请文件的修改不得超出原说明书和权利要求书记载的范围',
                    '禁止事项': [
                        '增加新的技术特征',
                        '扩大保护范围',
                        '补充技术效果'
                    ]
                }
            },

            '专利审查': {
                '新颖性': {
                    '定义': '不属于现有技术',
                    '现有技术': '申请日以前在国内外为公众所知的技术',
                    '判断标准': '技术方案是否被对比文件完全公开',
                    '例外情形': [
                        '申请日前6个月内首次展出',
                        '学术会议首次发表',
                        '他人未经同意泄露'
                    ]
                },
                '创造性': {
                    '定义': '与现有技术相比具有突出的实质性特点和显著的进步',
                    '三步法': [
                        '确定最接近的现有技术',
                        '确定发明的区别特征',
                        '判断是否显而易见'
                    ],
                    '考量因素': [
                        '技术方案是否解决了技术难题',
                        '是否产生了预料不到的技术效果',
                        '是否获得了商业成功'
                    ]
                },
                '实用性': {
                    '定义': '能够制造或使用，并且能够产生积极效果',
                    '要求': [
                        '技术方案必须能够在产业上应用',
                        '必须能够再现',
                        '必须产生积极效果'
                    ],
                    '排除情形': [
                        '科学发现',
                        '智力活动规则',
                        '疾病诊断治疗方法'
                    ]
                }
            },

            '专利无效': {
                '无效理由': {
                    '法条': '专利法第45条、第46条',
                    '主要理由': [
                        '缺乏新颖性',
                        '缺乏创造性',
                        '缺乏实用性',
                        '说明书公开不充分',
                        '权利要求得不到说明书支持',
                        '修改超范围'
                    ]
                },
                '证据规则': {
                    '证据形式': [
                        '专利文献',
                        '期刊论文',
                        '技术标准',
                        '产品说明书',
                        '使用公开证据'
                    ],
                    '优先顺序': [
                        '专利文献优先',
                        '印刷出版物其次',
                        '使用公开作为补充'
                    ]
                }
            },

            '专利侵权': {
                '侵权判定': {
                    '原则': '全面覆盖原则',
                    '判断方法': [
                        '技术特征逐一对比',
                        '相同侵权判断',
                        '等同侵权判断'
                    ],
                    '等同原则': '基本相同的手段、功能、效果，且无需创造性劳动'
                },
                '抗辩事由': [
                    '现有技术抗辩',
                    '先用权抗辩',
                    '合法来源抗辩',
                    '权利用尽抗辩'
                ]
            }
        }

    def _load_prompt_templates(self) -> dict:
        """加载提示词模板"""
        return {
            '专利撰写': {
                "技术方案描述": """
基于以下信息撰写技术方案部分：

技术领域：{tech_field}
背景技术：{background}
技术问题：{problem}
技术方案：{solution}
有益效果：{benefits}

撰写要求：
1. 技术领域：写明发明所属技术领域
2. 背景技术：描述相关的现有技术及其不足
3. 技术问题：明确要解决的技术问题
4. 技术方案：详细描述技术方案，使本领域技术人员能够理解和实施
5. 有益效果：说明技术方案带来的有益效果

注意：必须满足专利法第26条第3款的要求！
                """.strip(),

                "权利要求书": """
基于技术方案撰写权利要求书：

独立权利要求：
- 包含解决技术问题的全部必要技术特征
- 采用两段式或一段式撰写
- 保护范围应当适当

从属权利要求：
- 引用部分引用在先权利要求
- 限定部分增加附加技术特征
- 进一步限定保护范围

撰写要点：
1. 用语应当清楚、简要
2. 以说明书为依据
3. 形成层次分明的保护体系
                """.strip(),

                "实施例": """
提供具体实施方式：

实施例1（优选）：
- 详细描述具体实施方式
- 给出具体的参数、材料、设备等
- 说明技术效果如何实现

实施例2（变形）：
- 描述等效或替代方案
- 说明参数的合理范围

要求：
- 实施例应当支持权利要求
- 提供足够的技术细节
- 使本领域技术人员能够实施
                """.strip()
            },

            '专利分析': {
                "新颖性分析": """
分析专利的新颖性：

专利号：{patent_no}
技术方案：{solution}
对比文件：{prior_art}

分析步骤：
1. 确定技术方案的技术特征
2. 提取对比文件的技术特征
3. 逐一对比技术特征
4. 判断是否被完全公开

结论：新颖/不具备新颖性
理由：说明判断依据
                """.strip(),

                "创造性分析": """
分析专利的创造性：

最接近的现有技术：{closest_prior_art}
区别特征：{differences}
技术效果：{effects}

三步法分析：
1. 确定最接近的现有技术
2. 确定区别特征
3. 判断是否显而易见

考量因素：
- 是否解决了技术难题
- 是否产生预料不到的效果
- 是否获得商业成功

结论：具备创造性/不具备创造性
                """.strip(),

                "侵权分析": """
分析是否构成侵权：

专利权利要求：{claims}
被诉侵权方案：{accused_solution}

分析步骤：
1. 解读权利要求保护范围
2. 提取被诉侵权技术特征
3. 逐一对比技术特征
4. 判断相同侵权或等同侵权

结论：构成侵权/不构成侵权
风险等级：高/中/低
建议：应对措施
                """.strip()
            },

            '专利检索': {
                "查新检索": """
执行专利查新检索：

技术要点：{tech_points}
关键词：{keywords}
分类号：{ipc}

检索策略：
1. 关键词组合检索
2. 分类号限定检索
3. 引用文献检索
4. 发明人/申请人检索

检索结果：
- 相关文献清单
- 对比分析
- 新颖性初步判断
                """.strip(),

                "无效检索": """
为无效宣告进行证据检索：

目标专利：{target_patent}
无效理由：{invalid_reason}

检索重点：
1. 申请日前的对比文件
2. 影响新颖性的文件
3. 影响创造性的组合证据
4. 公知常识证据

检索要求：
- 全面性：覆盖所有可能的技术领域
- 准确性：精确匹配技术特征
- 及时性：确保证据的公开时间
                """.strip()
            },

            '专利评估': {
                "技术价值评估": """
评估专利的技术价值：

技术创新点：{innovation}
技术先进性：{advancement}
技术成熟度：{maturity}

评估维度：
1. 技术突破性（10分）
2. 技术先进性（10分）
3. 技术实用性（10分）
4. 技术影响力（10分）

综合评分：__ / 40
价值等级：高/中/低
                """.strip(),

                "经济价值评估": """
评估专利的经济价值：

专利类型：{patent_type}
保护期限：{remaining_years}
技术领域：{tech_field}

评估方法：
1. 成本法：__万元
2. 市场法：__万元
3. 收益法：__万元

估值区间：__ - __万元
风险提示：主要风险点
                """.strip()
            }
        }

    def _load_writing_templates(self) -> dict:
        """加载专利撰写模板"""
        return {
            '发明': {
                '名称': '发明名称',
                '摘要': '技术方案摘要（不超过300字）',
                '权利要求': '权利要求书',
                '说明书': {
                    '技术领域': '',
                    '背景技术': '',
                    '发明内容': '',
                    '附图说明': '',
                    '具体实施方式': ''
                }
            },

            '实用新型': {
                '名称': '实用新型名称',
                '摘要': '技术方案摘要（不超过300字）',
                '权利要求': '权利要求书',
                '说明书': {
                    '技术领域': '',
                    '背景技术': '',
                    '实用新型内容': '',
                    '附图说明': '',
                    '具体实施方式': ''
                },
                '附图': '必须提供附图'
            },

            '外观设计': {
                '名称': '使用该外观设计的产品名称',
                '图片': '产品设计图',
                '简要说明': '外观设计要点'
            }
        }

    def _load_examination_standards(self) -> dict:
        """加载审查标准"""
        return {
            '发明审查': {
                '实质审查周期': '3-5年',
                '审查重点': '新颖性、创造性、实用性',
                '审查意见': '通常1-2次审查意见通知书',
                '授权率': '约50%'
            },

            '实用新型审查': {
                '审查周期': '6-12个月',
                '审查重点': '初步审查形式要求',
                '审查方式': '形式审查，不进行实质审查',
                '授权率': '约80%'
            },

            '外观设计审查': {
                '审查周期': '6-9个月',
                '审查重点': '新颖性、明显冲突',
                '审查内容': '图片质量、保护范围清晰度',
                '授权率': '约85%'
            }
        }

    def _load_case_law(self) -> list[dict]:
        """加载案例法"""
        return [
            {
                '案件': '（2009）民提字第41号',
                '法院': '最高人民法院',
                '要旨': '明确等同侵权的认定标准',
                '适用': '等同侵权判定'
            },
            {
                '案件': '（2012）民提字第114号',
                '法院': '最高人民法院',
                '要旨': '禁止反悔原则的适用',
                '适用': '专利保护范围解释'
            },
            {
                '案件': '（2015）民申字第2750号',
                '法院': '最高人民法院',
                '要旨': '创造性判断中技术启示的认定',
                '适用': '创造性审查'
            }
        ]

    def get_writing_assistant(self, patent_type: str, tech_info: dict) -> dict:
        """获取撰写助手"""
        return {
            '模板': self.templates.get(patent_type, {}),
            '规则': self.rules['专利撰写'],
            '提示词': self.prompts['专利撰写'],
            '建议': self._generate_writing_suggestions(tech_info)
        }

    def get_analysis_assistant(self, analysis_type: str) -> dict:
        """获取分析助手"""
        return {
            '规则': self.rules.get(analysis_type, {}),
            '提示词': self.prompts['专利分析'].get(analysis_type, ''),
            '案例参考': self.case_law
        }

    def get_search_assistant(self, search_type: str) -> dict:
        """获取检索助手"""
        return {
            '提示词': self.prompts['专利检索'].get(search_type, ''),
            '检索策略': self._get_search_strategy(search_type),
            '注意事项': self._get_search_notes(search_type)
        }

    def get_evaluation_assistant(self, eval_type: str) -> dict:
        """获取评估助手"""
        return {
            '提示词': self.prompts['专利评估'].get(eval_type, ''),
            '评估标准': self._get_evaluation_standards(eval_type),
            '参考指标': self._get_evaluation_metrics(eval_type)
        }

    def _generate_writing_suggestions(self, tech_info: dict) -> list[str]:
        """生成撰写建议"""
        suggestions = []
        field = tech_info.get('tech_field', '').lower()

        if '机械' in field:
            suggestions.extend([
                '详细描述结构特征和连接关系',
                '说明运动部件的工作原理',
                '提供具体实施例和附图'
            ])
        elif '电子' in field or '通信' in field:
            suggestions.extend([
                '详细描述电路连接关系',
                '说明信号处理流程',
                '提供具体参数和实施方式'
            ])
        elif '化学' in field or '材料' in field:
            suggestions.extend([
                '清楚说明反应条件和制备方法',
                '提供具体实施例和测试数据',
                '说明产品性能和效果'
            ])
        elif '生物' in field or '医药' in field:
            suggestions.extend([
                '详细说明实验方法和结果',
                '提供具体的剂量和用法',
                '说明治疗效果和副作用'
            ])

        return suggestions

    def _get_search_strategy(self, search_type: str) -> list[str]:
        """获取检索策略"""
        strategies = {
            '查新检索': [
                '关键词+分类号组合检索',
                '引文检索（向前和向后）',
                '同族专利检索',
                '发明人/申请人检索'
            ],
            '无效检索': [
                '重点检索申请日前的技术',
                '查找最接近的对比文件',
                '构建组合证据',
                '收集公知常识证据'
            ],
            '侵权检索': [
                '限定目标产品/技术',
                '关键词精确匹配',
                '监控竞争对手专利',
                '定期更新检索'
            ]
        }
        return strategies.get(search_type, [])

    def _get_search_notes(self, search_type: str) -> list[str]:
        """获取检索注意事项"""
        notes = {
            '查新检索': [
                '检索范围要全面，覆盖主要技术领域',
                '注意关键词的同义词和近义词',
                '合理使用IPC/CPC分类号限定',
                '保留完整的检索过程记录'
            ],
            '无效检索': [
                '证据的公开时间必须早于申请日',
                '优先考虑专利文献作为证据',
                '注意对比文件的法律效力',
                '构建完整的证据链'
            ],
            '侵权检索': [
                '准确理解权利要求保护范围',
                '关注等同原则的适用',
                '注意检索的时效性',
                '保存检索证据'
            ]
        }
        return notes.get(search_type, [])

    def _get_evaluation_standards(self, eval_type: str) -> dict:
        """获取评估标准"""
        standards = {
            '技术价值': {
                '创新性': '1-10分，评估技术创新程度',
                '先进性': '1-10分，与国际领先水平对比',
                '实用性': '1-10分，评估产业化难度',
                '影响力': '1-10分，评估行业影响范围'
            },
            '经济价值': {
                '市场规模': '潜在市场规模评估',
                '竞争优势': '技术壁垒和差异化优势',
                '变现能力': '专利商业化难度',
                '风险因素': '技术、市场、法律风险'
            }
        }
        return standards.get(eval_type, {})

    def _get_evaluation_metrics(self, eval_type: str) -> list[str]:
        """获取评估指标"""
        metrics = {
            '技术价值': [
                '专利引用次数',
                '同族专利数量',
                '专利存活期',
                '技术领域分布'
            ],
            '经济价值': [
                '许可费率',
                '转让价格',
                '专利池参与度',
                '诉讼赔偿额'
            ]
        }
        return metrics.get(eval_type, [])

    def export_knowledge_base(self, output_path: str) -> Any:
        """导出知识库"""
        knowledge_base = {
            'version': '1.0.0',
            'created_at': datetime.now().isoformat(),
            'business_rules': self.rules,
            'prompt_templates': self.prompts,
            'writing_templates': self.templates,
            'examination_standards': self.examination_standards,
            'case_law': self.case_law,
            'application_scenarios': {
                '专利撰写': '支持发明人撰写高质量的专利申请',
                '专利分析': '提供专业的专利分析视角',
                '专利检索': '制定高效的检索策略',
                '专利评估': '多维度评估专利价值',
                '专利诉讼': '提供诉讼策略支持'
            }
        }

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(knowledge_base, f, ensure_ascii=False, indent=2)

        return str(output_file)


def main() -> None:
    """测试知识库系统"""
    logger.info(str('=' * 60))
    logger.info('专利业务知识库系统')
    logger.info(str('=' * 60))

    # 创建知识库实例
    kb = PatentBusinessKnowledgeBase()

    # 测试撰写助手
    logger.info("\n1. 专利撰写助手测试")
    logger.info(str('-' * 40))
    tech_info = {
        'tech_field': '电子通信',
        'problem': '如何提高信号传输效率'
    }
    writing_assistant = kb.get_writing_assistant('发明', tech_info)
    logger.info(f"撰写建议数量: {len(writing_assistant['建议'])}")
    print('撰写建议:', writing_assistant['建议'][:3])

    # 测试分析助手
    logger.info("\n2. 专利分析助手测试")
    logger.info(str('-' * 40))
    analysis_assistant = kb.get_analysis_assistant('新颖性分析')
    logger.info(f"相关案例数量: {len(analysis_assistant['案例参考'])}")

    # 测试检索助手
    logger.info("\n3. 专利检索助手测试")
    logger.info(str('-' * 40))
    search_assistant = kb.get_search_assistant('查新检索')
    logger.info(f"检索策略数量: {len(search_assistant['检索策略'])}")

    # 导出知识库
    logger.info("\n4. 导出知识库")
    logger.info(str('-' * 40))
    output_path = '/Users/xujian/Athena工作平台/data/support_data/reports/patent_business_knowledge_base.json'
    exported_file = kb.export_knowledge_base(output_path)
    logger.info(f"知识库已导出: {exported_file}")

    logger.info(str("\n" + '=' * 60))
    logger.info('知识库功能完备，可支持完整的专利业务流程！')
    logger.info(str('=' * 60))


if __name__ == '__main__':
    main()
