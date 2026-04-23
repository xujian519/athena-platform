#!/usr/bin/env python3
"""
增强推理引擎
Enhanced Reasoning Engine

专利认知决策系统的核心推理引擎，集成法律规则库和冲突解决机制

作者: Athena + 小诺
创建时间: 2025-12-05
版本: 2.0.0
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RuleType(Enum):
    """规则类型枚举"""
    NOVELTY = 'novelty'          # 新颖性规则
    INVENTIVE = 'inventive'      # 创造性规则
    PRACTICAL = 'practical'      # 实用性规则
    LEGAL = 'legal'              # 法律规则
    PROCEDURAL = 'procedural'    # 程序性规则
    DOMAIN = 'domain'            # 领域特定规则
    CONFLICT = 'conflict'        # 冲突解决规则

class RulePriority(Enum):
    """规则优先级"""
    CRITICAL = 5     # 关键规则（法律强制）
    HIGH = 4         # 高优先级（重要指导）
    MEDIUM = 3       # 中等优先级（一般建议）
    LOW = 2          # 低优先级（补充说明）
    OPTIONAL = 1     # 可选规则（参考意见）

@dataclass
class LegalRule:
    """法律规则数据类"""
    rule_id: str
    rule_type: RuleType
    priority: RulePriority
    title: str
    description: str
    conditions: list[str]          # 触发条件
    actions: list[str]             # 执行动作
    exceptions: list[str]          # 例外情况
    confidence: float = 1.0        # 规则置信度
    source: str = 'CN_PATENT_LAW'  # 规则来源
    last_updated: datetime = field(default_factory=datetime.now)
    conflict_resolution: dict[str, Any] = field(default_factory=dict)

@dataclass
class ReasoningResult:
    """推理结果数据类"""
    conclusion: str
    confidence: float
    applied_rules: list[str]
    reasoning_path: list[str]
    conflicts_detected: list[str]
    resolution_strategy: str
    evidence: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)

class ConflictResolver:
    """冲突解决器"""

    def __init__(self):
        self.resolution_strategies = {
            'priority_based': self._resolve_by_priority,
            'confidence_based': self._resolve_by_confidence,
            'source_authority': self._resolve_by_authority,
            'temporal': self._resolve_by_temporal,
            'domain_specific': self._resolve_by_domain
        }

    def resolve_conflicts(self, conflicting_rules: list[LegalRule], context: dict[str, Any]) -> list[LegalRule]:
        """解决规则冲突"""
        logger.info(f"🔧 解决 {len(conflicting_rules)} 个规则冲突...")

        # 按优先级分组
        priority_groups = {}
        for rule in conflicting_rules:
            if rule.priority not in priority_groups:
                priority_groups[rule.priority] = []
            priority_groups[rule.priority].append(rule)

        # 优先级最高的规则优先
        max_priority = max(priority_groups.keys())
        highest_priority_rules = priority_groups[max_priority]

        if len(highest_priority_rules) == 1:
            return highest_priority_rules

        # 同优先级规则进一步解决冲突
        resolved_rules = self._resolve_same_priority(highest_priority_rules, context)

        return resolved_rules

    def _resolve_same_priority(self, rules: list[LegalRule], context: dict[str, Any]) -> list[LegalRule]:
        """解决同优先级规则冲突"""
        # 1. 按置信度排序
        sorted(rules, key=lambda x: x.confidence, reverse=True)

        # 2. 检查领域特异性
        domain_specific_rules = [r for r in rules if r.rule_type == RuleType.DOMAIN]
        if domain_specific_rules:
            return [max(domain_specific_rules, key=lambda x: x.confidence)]

        # 3. 按时间优先（最新规则优先）
        latest_rules = max(rules, key=lambda x: x.last_updated)
        return [latest_rules]

    def _resolve_by_priority(self, rules: list[LegalRule]) -> list[LegalRule]:
        """基于优先级解决冲突"""
        max_priority = max(r.priority for r in rules)
        return [r for r in rules if r.priority == max_priority]

    def _resolve_by_confidence(self, rules: list[LegalRule]) -> list[LegalRule]:
        """基于置信度解决冲突"""
        max_confidence = max(r.confidence for r in rules)
        return [r for r in rules if r.confidence == max_confidence]

    def _resolve_by_authority(self, rules: list[LegalRule]) -> list[LegalRule]:
        """基于权威性解决冲突"""
        authority_rank = {
            'CN_PATENT_LAW': 5,      # 中国专利法
            'CN_PATENT_RULE': 4,     # 专利法实施细则
            'CN_EXAM_GUIDE': 3,      # 审查指南
            'COURT_CASE': 2,         # 法院判例
            'EXPERT_OPINION': 1      # 专家意见
        }

        max_authority = max(authority_rank.get(r.source, 0) for r in rules)
        return [r for r in rules if authority_rank.get(r.source, 0) == max_authority]

    def _resolve_by_temporal(self, rules: list[LegalRule]) -> list[LegalRule]:
        """基于时间顺序解决冲突"""
        latest_rule = max(rules, key=lambda x: x.last_updated)
        return [latest_rule]

    def _resolve_by_domain(self, rules: list[LegalRule]) -> list[LegalRule]:
        """基于领域特异性解决冲突"""
        domain_rules = [r for r in rules if r.rule_type == RuleType.DOMAIN]
        if domain_rules:
            return domain_rules
        return [max(rules, key=lambda x: x.confidence)]

class LegalRuleBase:
    """法律规则库"""

    def __init__(self):
        self.rules = {}
        self.rule_index = {
            'novelty': [],
            'inventive': [],
            'practical': [],
            'legal': [],
            'procedural': [],
            'domain': []
        }
        self._load_default_rules()

    def _load_default_rules(self):
        """加载默认规则"""
        logger.info('📚 加载法律规则库...')

        # 新颖性规则
        novelty_rules = [
            LegalRule(
                rule_id='NOV_001',
                rule_type=RuleType.NOVELTY,
                priority=RulePriority.CRITICAL,
                title='现有技术检索原则',
                description='判断新颖性时，必须进行全面检索，包括国内外专利、非专利文献',
                conditions=[
                    '评估专利新颖性',
                    '进行现有技术检索'
                ],
                actions=[
                    '检索中国专利数据库',
                    '检索外国专利数据库',
                    '检索非专利文献',
                    '对比技术方案'
                ],
                exceptions=[
                    '保密状态的技术',
                    '未公开的技术'
                ],
                confidence=0.95
            ),
            LegalRule(
                rule_id='NOV_002',
                rule_type=RuleType.NOVELTY,
                priority=RulePriority.HIGH,
                title='对比文件选择原则',
                description='选择最接近的现有技术作为对比文件',
                conditions=[
                    '存在多个现有技术文件',
                    '需要选择对比文件'
                ],
                actions=[
                    '分析技术领域相似性',
                    '分析技术问题相似性',
                    '分析技术方案相似性',
                    '选择最接近文件'
                ],
                exceptions=[],
                confidence=0.90
            )
        ]

        # 创造性规则
        inventive_rules = [
            LegalRule(
                rule_id='INV_001',
                rule_type=RuleType.INVENTIVE,
                priority=RulePriority.CRITICAL,
                title='三步法原则',
                description='确定最接近现有技术、确定发明区别、判断是否显而易见',
                conditions=[
                    '评估专利创造性',
                    '已知最接近现有技术'
                ],
                actions=[
                    '确定最接近现有技术',
                    '确定发明区别特征',
                    '判断现有技术启示',
                    '评估技术效果'
                ],
                exceptions=[],
                confidence=0.95
            ),
            LegalRule(
                rule_id='INV_002',
                rule_type=RuleType.INVENTIVE,
                priority=RulePriority.HIGH,
                title='技术效果考量',
                description='考虑发明的技术效果和商业成功',
                conditions=[
                    '技术方案具有商业价值',
                    '产生预料不到的技术效果'
                ],
                actions=[
                    '评估技术效果',
                    '分析商业成功原因',
                    '考虑非显而易见性'
                ],
                exceptions=[
                    '仅是市场推广成功',
                    '非技术因素导致成功'
                ],
                confidence=0.85
            )
        ]

        # 实用性规则
        practical_rules = [
            LegalRule(
                rule_id='PRA_001',
                rule_type=RuleType.PRACTICAL,
                priority=RulePriority.MEDIUM,
                title='可实施性原则',
                description='发明必须能够在产业上制造或使用',
                conditions=[
                    '评估专利实用性',
                    '技术方案完整'
                ],
                actions=[
                    '评估技术方案完整性',
                    '判断产业可行性',
                    '考虑实施成本'
                ],
                exceptions=[
                    '纯理论发现',
                    '违反自然规律'
                ],
                confidence=0.90
            )
        ]

        # 法律程序规则
        procedural_rules = [
            LegalRule(
                rule_id='PRO_001',
                rule_type=RuleType.PROCEDURAL,
                priority=RulePriority.CRITICAL,
                title='优先权原则',
                description='在12个月内要求优先权',
                conditions=[
                    '有首次申请',
                    '在12个月内'
                ],
                actions=[
                    '提交优先权声明',
                    '提供首次申请副本',
                    '核实申请日期'
                ],
                exceptions=[
                    '超过12个月期限',
                    '首次申请被撤回'
                ],
                confidence=0.98
            )
        ]

        # 加载所有规则
        for rule in novelty_rules + inventive_rules + practical_rules + procedural_rules:
            self.add_rule(rule)

    def add_rule(self, rule: LegalRule):
        """添加规则到规则库"""
        self.rules[rule.rule_id] = rule
        if rule.rule_type.value in self.rule_index:
            self.rule_index[rule.rule_type.value].append(rule.rule_id)

    def get_rule(self, rule_id: str) -> LegalRule | None:
        """获取规则"""
        return self.rules.get(rule_id)

    def get_rules_by_type(self, rule_type: RuleType) -> list[LegalRule]:
        """按类型获取规则"""
        rule_ids = self.rule_index.get(rule_type.value, [])
        return [self.rules[rid] for rid in rule_ids if rid in self.rules]

    def search_rules(self, keywords: list[str]) -> list[LegalRule]:
        """搜索规则"""
        matching_rules = []
        for rule in self.rules.values():
            rule_text = f"{rule.title} {rule.description} {' '.join(rule.conditions)}"
            if any(keyword.lower() in rule_text.lower() for keyword in keywords):
                matching_rules.append(rule)
        return matching_rules

class EnhancedReasoningEngine:
    """增强推理引擎"""

    def __init__(self):
        self.rule_base = LegalRuleBase()
        self.conflict_resolver = ConflictResolver()
        self.reasoning_history = []
        self.performance_metrics = {
            'total_reasonings': 0,
            'conflicts_detected': 0,
            'conflicts_resolved': 0,
            'average_confidence': 0.0
        }

    async def reason(self,
                     patent_data: dict[str, Any],
                     context: dict[str, Any] | None = None) -> ReasoningResult:
        """执行专利推理"""
        logger.info("🧠 开始专利推理分析...")

        start_time = datetime.now()
        context = context or {}

        # 1. 识别适用的规则
        applicable_rules = self._identify_applicable_rules(patent_data, context)

        # 2. 检测规则冲突
        conflicts = self._detect_conflicts(applicable_rules)

        # 3. 解决冲突
        if conflicts:
            logger.info(f"⚠️ 检测到 {len(conflicts)} 个规则冲突")
            resolved_rules = self.conflict_resolver.resolve_conflicts(conflicts, context)
            applicable_rules = [r for r in applicable_rules if r not in conflicts] + resolved_rules
            self.performance_metrics['conflicts_detected'] += len(conflicts)
            self.performance_metrics['conflicts_resolved'] += len(conflicts)

        # 4. 执行推理
        conclusion, confidence = await self._execute_reasoning(patent_data, applicable_rules, context)

        # 5. 构建推理路径
        reasoning_path = self._build_reasoning_path(applicable_rules, patent_data)

        # 6. 收集证据
        evidence = self._collect_evidence(patent_data, applicable_rules)

        # 7. 创建推理结果
        result = ReasoningResult(
            conclusion=conclusion,
            confidence=confidence,
            applied_rules=[r.rule_id for r in applicable_rules],
            reasoning_path=reasoning_path,
            conflicts_detected=[r.rule_id for r in conflicts] if conflicts else [],
            resolution_strategy='priority_based' if conflicts else 'none',
            evidence=evidence
        )

        # 8. 更新性能指标
        self._update_performance_metrics(result)

        # 9. 记录推理历史
        self.reasoning_history.append({
            'timestamp': start_time,
            'patent_id': patent_data.get('patent_id', 'unknown'),
            'result': result
        })

        logger.info(f"✅ 推理完成，置信度: {confidence:.2f}")
        return result

    def _identify_applicable_rules(self, patent_data: dict[str, Any], context: dict[str, Any]) -> list[LegalRule]:
        """识别适用的规则"""
        applicable_rules = []

        # 基于专利类型识别规则
        patent_type = patent_data.get('patent_type', 'invention')

        if patent_type == 'invention':
            applicable_rules.extend(self.rule_base.get_rules_by_type(RuleType.NOVELTY))
            applicable_rules.extend(self.rule_base.get_rules_by_type(RuleType.INVENTIVE))
            applicable_rules.extend(self.rule_base.get_rules_by_type(RuleType.PRACTICAL))

        # 基于技术领域识别规则
        tech_field = patent_data.get('technical_field', '')
        domain_rules = self.rule_base.search_rules([tech_field])
        applicable_rules.extend(domain_rules)

        # 基于申请阶段识别规则
        application_stage = context.get('application_stage', '')
        if 'priority' in application_stage.lower():
            procedural_rules = self.rule_base.get_rules_by_type(RuleType.PROCEDURAL)
            applicable_rules.extend(procedural_rules)

        # 去重并按优先级排序
        unique_rules = list({rule.rule_id: rule for rule in applicable_rules}.values())
        unique_rules.sort(key=lambda x: x.priority.value, reverse=True)

        return unique_rules

    def _detect_conflicts(self, rules: list[LegalRule]) -> list[LegalRule]:
        """检测规则冲突"""
        conflicts = []

        # 检查动作冲突
        action_groups = {}
        for rule in rules:
            for action in rule.actions:
                if action not in action_groups:
                    action_groups[action] = []
                action_groups[action].append(rule)

        for action, rule_list in action_groups.items():
            if len(rule_list) > 1:
                # 检查是否有相互矛盾的规则
                for i, rule1 in enumerate(rule_list):
                    for rule2 in rule_list[i+1:]:
                        if self._rules_conflict(rule1, rule2):
                            conflicts.extend([rule1, rule2])

        return list(set(conflicts))

    def _rules_conflict(self, rule1: LegalRule, rule2: LegalRule) -> bool:
        """判断两个规则是否冲突"""
        # 简单的冲突检测逻辑
        if rule1.rule_type != rule2.rule_type:
            return False

        # 检查是否有相互排除的条件
        if rule1.exceptions and any(exc in rule2.conditions for exc in rule1.exceptions):
            return True
        if rule2.exceptions and any(exc in rule1.conditions for exc in rule2.exceptions):
            return True

        return False

    async def _execute_reasoning(self,
                                patent_data: dict[str, Any],
                                rules: list[LegalRule],
                                context: dict[str, Any]) -> tuple[str, float]:
        """执行推理过程"""
        conclusions = []
        confidences = []

        for rule in rules:
            # 检查规则条件
            if self._check_conditions(rule.conditions, patent_data, context):
                # 执行规则动作
                rule_conclusion, rule_confidence = await self._apply_rule(rule, patent_data, context)
                conclusions.append(rule_conclusion)
                confidences.append(rule_confidence * rule.confidence)

        if not conclusions:
            return '无法确定结论', 0.0

        # 综合多个结论
        final_conclusion = self._combine_conclusions(conclusions)
        final_confidence = np.mean(confidences) if confidences else 0.0

        return final_conclusion, final_confidence

    def _check_conditions(self, conditions: list[str], patent_data: dict[str, Any], context: dict[str, Any]) -> bool:
        """检查规则条件是否满足"""
        for condition in conditions:
            if not self._evaluate_condition(condition, patent_data, context):
                return False
        return True

    def _evaluate_condition(self, condition: str, patent_data: dict[str, Any], context: dict[str, Any]) -> bool:
        """评估单个条件"""
        # 简化的条件评估逻辑
        condition_lower = condition.lower()

        # 检查专利数据中的关键词
        patent_text = str(patent_data).lower()
        if condition_lower in patent_text:
            return True

        # 检查上下文
        context_text = str(context).lower()
        if condition_lower in context_text:
            return True

        # 默认返回True（实际应用中需要更复杂的逻辑）
        return True

    async def _apply_rule(self, rule: LegalRule, patent_data: dict[str, Any], context: dict[str, Any]) -> tuple[str, float]:
        """应用单个规则"""
        # 基于规则类型生成结论
        if rule.rule_type == RuleType.NOVELTY:
            return self._apply_novelty_rule(rule, patent_data)
        elif rule.rule_type == RuleType.INVENTIVE:
            return self._apply_inventive_rule(rule, patent_data)
        elif rule.rule_type == RuleType.PRACTICAL:
            return self._apply_practical_rule(rule, patent_data)
        else:
            return f"应用规则 {rule.title}", rule.confidence

    def _apply_novelty_rule(self, rule: LegalRule, patent_data: dict[str, Any]) -> tuple[str, float]:
        """应用新颖性规则"""
        # 简化的新颖性判断逻辑
        has_prior_art = 'prior_art' in patent_data
        novelty_score = patent_data.get('novelty_score', 0.5)

        if has_prior_art and novelty_score > 0.7:
            conclusion = f"基于{rule.title}，该专利具备新颖性"
            confidence = min(novelty_score * rule.confidence, 1.0)
        else:
            conclusion = f"基于{rule.title}，该专利新颖性存疑"
            confidence = (1 - novelty_score) * rule.confidence

        return conclusion, confidence

    def _apply_inventive_rule(self, rule: LegalRule, patent_data: dict[str, Any]) -> tuple[str, float]:
        """应用创造性规则"""
        inventive_score = patent_data.get('inventive_score', 0.5)
        technical_effect = patent_data.get('technical_effect', '')

        if inventive_score > 0.6 and technical_effect:
            conclusion = f"基于{rule.title}，该专利具备创造性"
            confidence = min(inventive_score * rule.confidence, 1.0)
        else:
            conclusion = f"基于{rule.title}，该专利创造性不足"
            confidence = (1 - inventive_score) * rule.confidence

        return conclusion, confidence

    def _apply_practical_rule(self, rule: LegalRule, patent_data: dict[str, Any]) -> tuple[str, float]:
        """应用实用性规则"""
        implementable = patent_data.get('implementable', True)

        if implementable:
            conclusion = f"基于{rule.title}，该专利具备实用性"
            confidence = 0.9 * rule.confidence
        else:
            conclusion = f"基于{rule.title}，该专利不具实用性"
            confidence = 0.8 * rule.confidence

        return conclusion, confidence

    def _build_reasoning_path(self, rules: list[LegalRule], patent_data: dict[str, Any]) -> list[str]:
        """构建推理路径"""
        path = []
        path.append('开始专利认知推理')

        for i, rule in enumerate(rules):
            path.append(f"步骤{i+1}: 应用{rule.title}")
            path.append(f"  - 规则类型: {rule.rule_type.value}")
            path.append(f"  - 优先级: {rule.priority.name}")
            path.append(f"  - 置信度: {rule.confidence:.2f}")

        path.append('生成最终结论')
        return path

    def _collect_evidence(self, patent_data: dict[str, Any], rules: list[LegalRule]) -> dict[str, Any]:
        """收集证据"""
        evidence = {
            'patent_data': {
                'patent_id': patent_data.get('patent_id'),
                'title': patent_data.get('title'),
                'technical_field': patent_data.get('technical_field')
            },
            'applied_rules': [
                {
                    'rule_id': rule.rule_id,
                    'title': rule.title,
                    'source': rule.source,
                    'priority': rule.priority.name
                }
                for rule in rules
            ],
            'metrics': {
                'novelty_score': patent_data.get('novelty_score'),
                'inventive_score': patent_data.get('inventive_score'),
                'practical_score': patent_data.get('practical_score', 1.0)
            }
        }

        return evidence

    def _combine_conclusions(self, conclusions: list[str]) -> str:
        """综合多个结论"""
        if len(conclusions) == 1:
            return conclusions[0]

        # 基于结论的相似性进行分组
        similar_conclusions = self._group_similar_conclusions(conclusions)

        # 生成综合结论
        combined = "综合分析结果：\n"
        for group in similar_conclusions:
            combined += f"- {group[0]}\n"

        return combined

    def _group_similar_conclusions(self, conclusions: list[str]) -> list[list[str]:
        """将相似的结论分组"""
        # 简化的分组逻辑，实际应用中可以使用更复杂的文本相似度算法
        groups = []
        for conclusion in conclusions:
            added = False
            for group in groups:
                if any(word in group[0] for word in conclusion.split() if len(word) > 3):
                    group.append(conclusion)
                    added = True
                    break
            if not added:
                groups.append([conclusion])

        return groups

    def _update_performance_metrics(self, result: ReasoningResult):
        """更新性能指标"""
        self.performance_metrics['total_reasonings'] += 1

        # 更新平均置信度
        current_avg = self.performance_metrics['average_confidence']
        total = self.performance_metrics['total_reasonings']
        self.performance_metrics['average_confidence'] = (
            (current_avg * (total - 1) + result.confidence) / total
        )

    def get_performance_report(self) -> dict[str, Any]:
        """获取性能报告"""
        return {
            **self.performance_metrics,
            'rule_base_size': len(self.rule_base.rules),
            'reasoning_history_size': len(self.reasoning_history),
            'last_updated': datetime.now().isoformat()
        }

    def export_rules(self, file_path: str):
        """导出规则库"""
        rules_data = {}
        for rule_id, rule in self.rule_base.rules.items():
            rules_data[rule_id] = {
                'rule_type': rule.rule_type.value,
                'priority': rule.priority.value,
                'title': rule.title,
                'description': rule.description,
                'conditions': rule.conditions,
                'actions': rule.actions,
                'exceptions': rule.exceptions,
                'confidence': rule.confidence,
                'source': rule.source,
                'last_updated': rule.last_updated.isoformat()
            }

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(rules_data, f, ensure_ascii=False, indent=2)

        logger.info(f"📄 规则库已导出到: {file_path}")

async def main():
    """主函数"""
    logger.info('🧠 增强推理引擎测试')
    logger.info('Athena + 小诺 为您服务~ 💖')
    logger.info(str('='*50))

    engine = EnhancedReasoningEngine()

    # 测试用例
    test_patent = {
        'patent_id': 'CN202512050001',
        'title': '一种智能专利分析方法',
        'technical_field': '人工智能',
        'patent_type': 'invention',
        'novelty_score': 0.8,
        'inventive_score': 0.7,
        'practical_score': 0.9,
        'implementable': True,
        'technical_effect': '显著提升分析效率'
    }

    test_context = {
        'application_stage': 'priority_filing',
        'prior_art_found': True
    }

    # 执行推理
    result = await engine.reason(test_patent, test_context)

    # 显示结果
    logger.info("\n📋 推理结果:")
    logger.info(f"结论: {result.conclusion}")
    logger.info(f"置信度: {result.confidence:.2f}")
    logger.info(f"应用的规则: {', '.join(result.applied_rules)}")

    if result.conflicts_detected:
        logger.info(f"检测到的冲突: {', '.join(result.conflicts_detected)}")
        logger.info(f"解决策略: {result.resolution_strategy}")

    logger.info("\n🔍 推理路径:")
    for i, step in enumerate(result.reasoning_path, 1):
        logger.info(f"{i}. {step}")

    # 性能报告
    performance = engine.get_performance_report()
    logger.info("\n📊 性能报告:")
    logger.info(f"总推理次数: {performance['total_reasonings']}")
    logger.info(f"平均置信度: {performance['average_confidence']:.2f}")
    logger.info(f"冲突检测次数: {performance['conflicts_detected']}")
    logger.info(f"规则库大小: {performance['rule_base_size']}")

    # 导出规则库
    engine.export_rules('patent_reasoning_rules.json')
    logger.info("\n✅ 测试完成！")

if __name__ == '__main__':
    asyncio.run(main())
