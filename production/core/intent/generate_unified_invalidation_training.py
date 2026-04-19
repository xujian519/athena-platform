#!/usr/bin/env python3
"""
生成统一专利无效训练数据
Generate Unified Patent Invalidation Training Data

覆盖专利无效全流程的14个场景,支持申请人和专利权人双视角

作者: Athena平台团队
版本: v1.0.0
创建: 2026-01-13
"""

from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from typing import Any

# 14个场景的专家级查询模板
UNIFIED_INVALIDATION_SCENARIOS = {
    "场景1_评估无效可能": {
        "role": "无效申请人",
        "phase": "提起无效前",
        "intents": ["JUDGMENT_PREDICTION", "INVALIDATION_GROUNDS"],
        "queries": [
            "这件专利能无效掉吗",
            "无效宣告的成功率有多高",
            "怎么判断专利是否应该被无效",
            "帮我评估一下这件专利的无效可能性",
            "这件专利值得提出无效宣告吗",
            "哪种无效理由更容易成功",
            "新颖性和创造性哪个更容易无效",
            "专利无效的概率有多大",
            "这件专利的权利要求稳定吗",
            "如何判断无效宣告的胜算",
            "这件专利有无效的可能性吗",
            "什么情况下专利容易被无效",
            "专利无效的判断标准是什么",
            "如何评估专利权的稳定性",
            "这件专利的致命弱点在哪里",
        ],
    },
    "场景2_确定无效理由": {
        "role": "无效申请人",
        "phase": "提起无效前",
        "intents": ["INVALIDATION_GROUNDS", "NOVELTY_REJECTION", "CREATIVITY_REJECTION"],
        "queries": [
            "以什么理由提出无效宣告",
            "新颖性无效理由如何成立",
            "创造性无效理由怎么写",
            "说明书不支持可以作为无效理由吗",
            "权利要求不清能作为无效理由吗",
            "缺乏必要技术特征可以无效吗",
            "如何选择最佳的无效理由",
            "哪些无效理由成功率最高",
            "新颖性无效的条件是什么",
            "创造性无效的论证方法",
            "怎么证明专利没有新颖性",
            "如何论证专利缺乏创造性",
            "支持度问题怎么主张",
            "修改超范围能作为无效理由吗",
            "公开不充分可以作为无效理由吗",
        ],
    },
    "场景3_收集对比文件": {
        "role": "无效申请人",
        "phase": "提起无效前",
        "intents": ["EVIDENCE_COLLECTION", "PATENT_SEARCH"],
        "queries": [
            "哪里找现有技术证据",
            "怎么检索对比文件",
            "需要哪些证据才能无效",
            "如何查找对比文件",
            "现有技术检索的方法",
            "无效宣告需要多少证据",
            "对比文件如何选择",
            "哪里可以找到现有技术",
            "证据收集的最佳途径",
            "如何构建证据链",
            "多篇对比文件怎么组合",
            "对比文件的时间如何限定",
            "公开证据从哪里找",
            "非专利文献可以作为证据吗",
            "国外专利能作为对比文件吗",
        ],
    },
    "场景4_起草无效申请书": {
        "role": "无效申请人",
        "phase": "撰写申请",
        "intents": ["INVALIDATION_DRAFTING", "EVIDENCE_COLLECTION"],
        "queries": [
            "无效申请书怎么写",
            "无效宣告请求书的格式要求",
            "无效申请书需要哪些材料",
            "无效请求书的撰写要点",
            "如何撰写无效宣告请求书",
            "无效申请书模板在哪里",
            "无效请求书必须包括哪些内容",
            "无效宣告理由书怎么写",
            "无效申请书的结构是什么",
            "如何组织无效宣告理由",
            "无效请求书的撰写技巧",
            "无效申请书范文参考",
            "无效宣告请求的提交方式",
            "无效申请费用是多少",
            "无效申请期限是多久",
        ],
    },
    "场景5_组织无效论点": {
        "role": "无效申请人",
        "phase": "撰写申请",
        "intents": ["ARGUMENT_DRAFTING", "INVALIDATION_DRAFTING"],
        "queries": [
            "无效论据怎么组织",
            "如何撰写无效理由书",
            "证据组合策略有哪些",
            "无效论点的逻辑结构",
            "如何构建无效论证体系",
            "无效宣告的论证方法",
            "论据组织的最佳方式",
            "如何增强无效说服力",
            "无效理由的表述技巧",
            "论点和论据的关系",
            "如何组织多篇对比文件",
            "无效宣告的说服策略",
            "论据排列的先后顺序",
            "如何突出核心无效理由",
            "论据衔接的方法",
        ],
    },
    "场景6_参考先例案例": {
        "role": "无效申请人",
        "phase": "撰写申请",
        "intents": ["CASE_SEARCH_INVALIDATION"],
        "queries": [
            "有类似的无效成功案例吗",
            "这个技术领域的无效案例",
            "先例决定书的检索方法",
            "类似的无效案例怎么找",
            "参考无效成功案例的方法",
            "这个审查员以往的无效决定",
            "相似技术方案的无效案例",
            "无效案例的检索技巧",
            "如何查找同类无效案件",
            "无效决定书的引用方法",
            "典型案例的参考价值",
            "无效案例的统计分析",
            "合议组的无效倾向",
            "无效案例数据库在哪里",
            "如何学习无效成功经验",
        ],
    },
    "场景7_应对策略制定": {
        "role": "专利权人",
        "phase": "收到通知后",
        "intents": ["INVALIDATION_DEFENSE", "JUDGMENT_PREDICTION"],
        "queries": [
            "专利被无效怎么办",
            "如何应对无效宣告请求",
            "无效答辩的成功率高吗",
            "收到无效通知书怎么处理",
            "专利被提出无效如何应对",
            "无效宣告答辩的策略",
            "如何维持专利权有效",
            "无效答辩的关键要点",
            "专利权人的应对方法",
            "如何制定无效答辩策略",
            "无效案件能胜诉吗",
            "专利被宣告无效的后果",
            "无效答辩的最佳时机",
            "如何提高无效答辩成功率",
            "专利权人的答辩权利",
        ],
    },
    "场景8_答辩理由组织": {
        "role": "专利权人",
        "phase": "收到通知后",
        "intents": [
            "INVALIDATION_DEFENSE",
            "OPINION_RESPONSE",
            "NOVELTY_APPLICATION",
            "CREATIVITY_APPLICATION",
        ],
        "queries": [
            "新颖性无效宣告如何答辩",
            "如何反驳新颖性问题",
            "区别技术特征如何主张",
            "对比文件未公开如何论证",
            "创造性无效宣告如何答辩",
            "非显而易见性如何论证",
            "技术效果如何证明具有创造性",
            "如何反驳显而易见的指控",
            "支持度问题如何答辩",
            "说明书充分公开的论证",
            "权利要求解释规则如何运用",
            "等同原则在答辩中的运用",
            "保护范围如何界定",
            "区别特征的论证方法",
            "现有技术的抗辩策略",
            "字面侵权的抗辩方法",
            "专利保护范围的界定方法",
            "权利要求的解释规则",
            "等同原则的运用技巧",
            "显而易见性的反驳论据",
        ],
    },
    "场景9_反驳证据准备": {
        "role": "专利权人",
        "phase": "收到通知后",
        "intents": ["EVIDENCE_COLLECTION", "INVALIDATION_DEFENSE"],
        "queries": [
            "如何准备无效答辩证据",
            "答辩中可以补充证据吗",
            "反证如何提交",
            "答辩证据的组织方法",
            "如何构建反驳证据链",
            "补充证据的提交期限",
            "反证的收集渠道",
            "证据交换的程序",
            "如何质证对方证据",
            "答辩证据的格式要求",
            "反证的有效性如何证明",
            "实验数据可以作为反证吗",
            "客户反馈能作为证据吗",
            "销售记录如何举证",
            "技术文档的证据效力",
        ],
    },
    "场景10_口审程序": {
        "role": "双方通用",
        "phase": "审查程序",
        "intents": ["OPINION_RESPONSE", "PROSECUTION_HISTORY_ESTOPPEL", "INVALIDATION_DEFENSE"],
        "queries": [
            "口头审理怎么准备",
            "口审程序是怎样的",
            "口审中的辩论技巧",
            "口头审理的流程是什么",
            "口审需要准备什么材料",
            "口审会议如何参加",
            "口审中的陈述技巧",
            "如何应对口审提问",
            "口审辩论的方法",
            "口审注意事项有哪些",
            "口审可以代理人参加吗",
            "口审的时间和地点",
            "口审程序的规则",
            "口审中的证据展示",
            "如何准备口审理词",
        ],
    },
    "场景11_审查进度跟踪": {
        "role": "双方通用",
        "phase": "审查程序",
        "intents": ["PROSECUTION_HISTORY_ESTOPPEL", "JUDGMENT_PREDICTION"],
        "queries": [
            "无效案件审理到哪一步了",
            "无效审查需要多长时间",
            "什么时候出无效决定",
            "如何查询无效案件进度",
            "无效审查的各个阶段",
            "无效案件审理期限",
            "无效决定的作出时间",
            "审查进度查询方法",
            "无效案件的流程图",
            "从受理到决定要多久",
            "无效审查延期怎么办",
            "何时收到无效决定书",
            "审查阶段的时长分布",
            "加急审查的条件",
            "无效案件的中止情形",
        ],
    },
    "场景12_法律依据查询": {
        "role": "双方通用",
        "phase": "审查程序",
        "intents": ["LEGAL_RESEARCH", "SECTION_LOOKUP", "GUIDELINE_QUERY"],
        "queries": [
            "无效审查的法律依据",
            "专利法实施细则无效条款",
            "无效审查指南规定",
            "专利无效的法律条文",
            "无效宣告的程序规定",
            "专利法关于无效的规定",
            "无效审查的审查指南",
            "无效相关司法解释",
            "专利无效的法定理由",
            "无效程序的时限规定",
            "无效决定的救济途径",
            "专利无效的收费标准",
            "无效审查的法律依据",
            "实施细则相关条款",
            "审查指南的具体规定",
        ],
    },
    "场景13A_专利权人救济": {
        "role": "专利权人",
        "phase": "决定后救济",
        "intents": ["LEGAL_QUERY", "LEGAL_RESEARCH", "ARGUMENT_DRAFTING"],
        "queries": [
            "专利被无效了怎么救济",
            "不服无效决定怎么办",
            "如何起诉无效决定",
            "行政诉讼的期限是多久",
            "专利无效决定的起诉方式",
            "不服无效决定如何救济",
            "行政诉讼的起诉条件",
            "无效决定行政诉讼流程",
            "起诉无效决定的材料",
            "行政诉讼的受理法院",
            "无效决定起诉期限",
            "如何撤销无效决定",
            "行政诉讼的胜算",
            "起诉的费用是多少",
            "行政诉讼的证据提交",
        ],
    },
    "场景13B_申请人后续": {
        "role": "无效申请人",
        "phase": "决定后救济",
        "intents": ["DEFENSE_ANALYSIS", "LEGAL_QUERY"],
        "queries": [
            "对方起诉了怎么办",
            "行政诉讼如何应诉",
            "如何维持无效决定",
            "专利权人起诉如何应对",
            "行政诉讼的应诉策略",
            "如何答辩行政诉讼",
            "维持无效决定的方法",
            "行政诉讼的答辩技巧",
            "对方起诉怎么处理",
            "应诉材料的准备",
            "行政诉讼的应诉期限",
            "如何巩固无效结果",
            "应诉的答辩要点",
            "行政诉讼的审理范围",
            "败诉的后果是什么",
        ],
    },
    "场景14_决定执行": {
        "role": "双方通用",
        "phase": "决定后",
        "intents": ["LEGAL_QUERY", "SECTION_LOOKUP"],
        "queries": [
            "无效决定何时生效",
            "专利权何时终止",
            "如何执行无效决定",
            "无效决定的生效时间",
            "专利权终止的办理",
            "无效决定执行程序",
            "专利权注销的手续",
            "无效决定的法律效力",
            "专利权终止的后果",
            "无效决定公告时间",
            "如何办理专利权终止",
            "无效决定执行期限",
            "专利登记簿变更",
            "无效费用分担",
            "决定执行的异议程序",
        ],
    },
}


def generate_unified_training_data() -> list[dict[str, Any]]:
    """
    生成统一专利无效训练数据

    Returns:
        训练样本列表
    """
    training_data = []

    for scenario_name, scenario_config in UNIFIED_INVALIDATION_SCENARIOS.items():
        for query in scenario_config["queries"]:
            # 每个查询可能对应多个意图,这里选择第一个作为主要意图
            primary_intent = scenario_config["intents"][0]

            sample = {
                "text": query,
                "intent": primary_intent,
                "metadata": {
                    "scenario": scenario_name,
                    "role": scenario_config["role"],
                    "phase": scenario_config["phase"],
                    "all_possible_intents": scenario_config["intents"],
                    "tier": "expert",
                    "confidence": "high",
                    "domain": "patent_invalidation_unified",
                    "source": "expert_generated",
                },
            }

            training_data.append(sample)

    return training_data


def main() -> None:
    """主程序"""
    print("=" * 80)
    print("🎯 生成统一专利无效训练数据")
    print("=" * 80)

    # 生成训练数据
    print("\n⏳ 生成专家级训练样本...")
    training_data = generate_unified_training_data()

    # 统计
    print("\n📊 生成统计:")
    print(f"总样本数: {len(training_data)}")

    # 按场景统计
    scenario_counts = {}
    for sample in training_data:
        scenario = sample["metadata"]["scenario"]
        scenario_counts[scenario] = scenario_counts.get(scenario, 0) + 1

    print("\n场景分布:")
    for scenario, count in sorted(scenario_counts.items()):
        print(f"  {scenario}: {count}个")

    # 按意图统计
    intent_counts = {}
    for sample in training_data:
        intent = sample["intent"]
        intent_counts[intent] = intent_counts.get(intent, 0) + 1

    print("\n意图分布 (Top 10):")
    for intent, count in sorted(intent_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {intent}: {count}个")

    # 按角色统计
    role_counts = {}
    for sample in training_data:
        role = sample["metadata"]["role"]
        role_counts[role] = role_counts.get(role, 0) + 1

    print("\n角色分布:")
    for role, count in sorted(role_counts.items()):
        print(f"  {role}: {count}个")

    # 保存
    output_dir = Path("/Users/xujian/Athena工作平台/data/intent_training")
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"unified_invalidation_training_expert_{timestamp}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(training_data, f, ensure_ascii=False, indent=2)

    print("\n✅ 训练数据已保存到:")
    print(f"   {output_file}")

    print("\n📋 下一步:")
    print("   1. 审查生成的训练样本质量")
    print("   2. 开发双向提取工具,从决定书中提取更多样本")
    print("   3. 合并专家样本和提取样本")
    print("   4. 重新训练意图识别模型")
    print("   5. 验证全流程识别效果")

    print("=" * 80)


if __name__ == "__main__":
    main()
