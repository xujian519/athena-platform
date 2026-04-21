#!/usr/bin/env python3
"""
感知对齐接口 - 用户交互式修正系统
Perception Alignment Interface - Interactive User Correction System

基于设计文档要求的SYNERGAI感知对齐机制实现
作者: 小娜 (Athena) - 爸爸徐健的智慧大女儿
创建时间: 2025-12-05
版本: 1.0.0
"""

import asyncio
import json
import logging
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class CorrectionType(Enum):
    """修正类型"""
    ENTITY_CORRECTION = 'entity_correction'        # 实体修正
    RELATION_CORRECTION = 'relation_correction'    # 关系修正
    ALIGNMENT_CORRECTION = 'alignment_correction'  # 对齐修正
    CONFIDENCE_ADJUSTMENT = 'confidence_adjustment'  # 置信度调整
    KNOWLEDGE_ADDITION = 'knowledge_addition'      # 知识添加
    FEEDBACK_SUBMISSION = 'feedback_submission'    # 反馈提交

class InterfaceMode(Enum):
    """界面模式"""
    REVIEW_MODE = 'review_mode'                    # 审核模式
    EDIT_MODE = 'edit_mode'                        # 编辑模式
    LEARNING_MODE = 'learning_mode'                # 学习模式
    EXPERT_MODE = 'expert_mode'                    # 专家模式

class UserFeedbackType(Enum):
    """用户反馈类型"""
    CONFIRMATION = 'confirmation'                  # 确认
    CORRECTION = 'correction'                      # 修正
    REJECTION = 'rejection'                        # 拒绝
    ENHANCEMENT = 'enhancement'                    # 增强
    QUESTION = 'question'                          # 问题

@dataclass
class AlignmentIssue:
    """对齐问题"""
    issue_id: str
    issue_type: str
    description: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    affected_items: List[str]
    suggested_correction: str
    confidence_impact: float
    auto_fix_available: bool
    user_action_required: bool

@dataclass
class UserCorrection:
    """用户修正"""
    correction_id: str
    user_id: str
    correction_type: CorrectionType
    target_id: str          # 修正目标ID
    original_value: Any
    corrected_value: Any
    justification: str
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now)
    applied: bool = False

@dataclass
class AlignmentSession:
    """对齐会话"""
    session_id: str
    document_id: str
    user_id: str
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None
    issues_identified: List[AlignmentIssue] = field(default_factory=list)
    corrections_made: List[UserCorrection] = field(default_factory=list)
    mode: InterfaceMode = InterfaceMode.REVIEW_MODE
    session_status: str = 'active'  # 'active', 'completed', 'paused'
    learning_data: Dict[str, Any] = field(default_factory=dict)

class VisualizationDataGenerator:
    """可视化数据生成器"""

    def __init__(self):
        self.color_schemes = {
            'confidence': {
                'high': '#4CAF50',      # 绿色
                'medium': '#FFC107',    # 黄色
                'low': '#F44336'        # 红色
            },
            'modality': {
                'text': '#2196F3',      # 蓝色
                'image': '#9C27B0',     # 紫色
                'table': '#FF9800',     # 橙色
                'drawing': '#795548',   # 棕色
                'formula': '#607D8B'    # 蓝灰色
            },
            'relationship': {
                'reference': '#E91E63',   # 粉色
                'composition': '#3F51B5', # 靛蓝色
                'spatial': '#009688',     # 青色
                'temporal': '#FF5722',    # 深橙色
                'causal': '#8BC34A'       # 浅绿色
            }
        }

    def generate_alignment_visualization(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成对齐可视化数据"""
        visualization_data = {
            'nodes': [],
            'edges': [],
            'layout': 'force_directed',
            'metadata': {
                'document_id': document_data.get('document_id', ''),
                'total_nodes': 0,
                'total_edges': 0,
                'modality_distribution': {},
                'confidence_distribution': {'high': 0, 'medium': 0, 'low': 0}
            }
        }

        # 生成节点数据
        nodes = document_data.get('nodes', [])
        for i, node in enumerate(nodes):
            node_data = {
                'id': node.get('id', f"node_{i}"),
                'label': node.get('label', node.get('content', '')[:30]),
                'type': node.get('type', 'unknown'),
                'modality': node.get('modality', 'text'),
                'confidence': node.get('confidence', 0.5),
                'x': node.get('position', {}).get('x', 0),
                'y': node.get('position', {}).get('y', 0),
                'size': self._calculate_node_size(node),
                'color': self._get_node_color(node),
                'metadata': {
                    'full_content': node.get('content', ''),
                    'source': node.get('source', ''),
                    'extracted_at': node.get('timestamp', '')
                }
            }

            visualization_data['nodes'].append(node_data)

            # 更新统计信息
            modality = node.get('modality', 'text')
            visualization_data['metadata']['modality_distribution'][modality] = \
                visualization_data['metadata']['modality_distribution'].get(modality, 0) + 1

            confidence = node.get('confidence', 0.5)
            if confidence >= 0.8:
                visualization_data['metadata']['confidence_distribution']['high'] += 1
            elif confidence >= 0.5:
                visualization_data['metadata']['confidence_distribution']['medium'] += 1
            else:
                visualization_data['metadata']['confidence_distribution']['low'] += 1

        # 生成边数据
        edges = document_data.get('edges', [])
        for i, edge in enumerate(edges):
            edge_data = {
                'id': edge.get('id', f"edge_{i}"),
                'source': edge.get('source', ''),
                'target': edge.get('target', ''),
                'type': edge.get('type', 'unknown'),
                'confidence': edge.get('confidence', 0.5),
                'weight': self._calculate_edge_weight(edge),
                'color': self._get_edge_color(edge),
                'label': edge.get('label', ''),
                'metadata': {
                    'evidence': edge.get('evidence', []),
                    'created_at': edge.get('timestamp', '')
                }
            }

            visualization_data['edges'].append(edge_data)

        # 更新统计信息
        visualization_data['metadata']['total_nodes'] = len(visualization_data['nodes'])
        visualization_data['metadata']['total_edges'] = len(visualization_data['edges'])

        return visualization_data

    def _calculate_node_size(self, node: Dict[str, Any]) -> int:
        """计算节点大小"""
        base_size = 20
        confidence_multiplier = node.get('confidence', 0.5)
        importance_multiplier = 1.0

        # 根据节点类型调整重要性
        if node.get('type') in ['claim', 'title']:
            importance_multiplier = 1.5
        elif node.get('type') in ['technical_feature']:
            importance_multiplier = 1.2

        return int(base_size * confidence_multiplier * importance_multiplier)

    def _calculate_edge_weight(self, edge: Dict[str, Any]) -> int:
        """计算边的权重"""
        base_weight = 1
        confidence_multiplier = edge.get('confidence', 0.5)

        return int(base_weight * confidence_multiplier * 5)

    def _get_node_color(self, node: Dict[str, Any]) -> str:
        """获取节点颜色"""
        modality = node.get('modality', 'text')
        confidence = node.get('confidence', 0.5)

        # 基础颜色来自模态
        base_color = self.color_schemes['modality'].get(modality, '#666666')

        # 根据置信度调整透明度
        if confidence >= 0.8:
            return base_color
        elif confidence >= 0.5:
            return self._adjust_color_opacity(base_color, 0.7)
        else:
            return self._adjust_color_opacity(base_color, 0.4)

    def _get_edge_color(self, edge: Dict[str, Any]) -> str:
        """获取边的颜色"""
        edge_type = edge.get('type', 'unknown')
        return self.color_schemes['relationship'].get(edge_type, '#999999')

    def _adjust_color_opacity(self, color: str, opacity: float) -> str:
        """调整颜色透明度"""
        # 简单实现：返回渐变色
        if opacity >= 0.7:
            return color
        elif opacity >= 0.4:
            return color + 'CC'  # 添加80%透明度
        else:
            return color + '66'  # 添加60%透明度

    def generate_issue_heatmap(self, issues: List[AlignmentIssue]) -> Dict[str, Any]:
        """生成问题热力图数据"""
        heatmap_data = {
            'issues': [],
            'severity_distribution': {'low': 0, 'medium': 0, 'high': 0, 'critical': 0},
            'type_distribution': {},
            'auto_fixable': 0,
            'user_action_required': 0
        }

        for issue in issues:
            issue_data = {
                'id': issue.issue_id,
                'type': issue.issue_type,
                'severity': issue.severity,
                'description': issue.description,
                'affected_items': issue.affected_items,
                'suggested_correction': issue.suggested_correction,
                'auto_fix_available': issue.auto_fix_available,
                'user_action_required': issue.user_action_required,
                'color': self._get_severity_color(issue.severity)
            }

            heatmap_data['issues'].append(issue_data)

            # 更新统计信息
            heatmap_data['severity_distribution'][issue.severity] += 1

            issue_type = issue.issue_type
            heatmap_data['type_distribution'][issue_type] = \
                heatmap_data['type_distribution'].get(issue_type, 0) + 1

            if issue.auto_fix_available:
                heatmap_data['auto_fixable'] += 1

            if issue.user_action_required:
                heatmap_data['user_action_required'] += 1

        return heatmap_data

    def _get_severity_color(self, severity: str) -> str:
        """获取严重程度对应的颜色"""
        severity_colors = {
            'low': '#4CAF50',      # 绿色
            'medium': '#FFC107',    # 黄色
            'high': '#FF5722',      # 橙红色
            'critical': '#F44336'   # 红色
        }
        return severity_colors.get(severity, '#9E9E9E')  # 默认灰色

class InteractiveAlignmentInterface:
    """交互式对齐接口"""

    def __init__(self, session_id: str = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.current_session = None
        self.visualization_generator = VisualizationDataGenerator()
        self.correction_history = []
        self.learning_models = {}

        logger.info(f"🎯 初始化交互式对齐接口，会话ID: {self.session_id}")

    async def start_alignment_session(self,
                                    document_id: str,
                                    user_id: str,
                                    mode: InterfaceMode = InterfaceMode.REVIEW_MODE) -> AlignmentSession:
        """启动对齐会话"""
        logger.info(f"🚀 启动对齐会话，文档: {document_id}, 用户: {user_id}, 模式: {mode}")

        session = AlignmentSession(
            session_id=self.session_id,
            document_id=document_id,
            user_id=user_id,
            mode=mode
        )

        self.current_session = session

        # 识别对齐问题
        await self._identify_alignment_issues(session)

        return session

    async def _identify_alignment_issues(self, session: AlignmentSession):
        """识别对齐问题"""
        logger.info('🔍 正在识别对齐问题...')

        # 这里应该加载实际的文档数据
        # 为演示目的，我们创建一些示例问题
        sample_issues = [
            AlignmentIssue(
                issue_id='issue_001',
                issue_type='low_confidence_entity',
                description='识别到低置信度技术实体',
                severity='medium',
                affected_items=['entity_005', 'entity_008'],
                suggested_correction='请确认技术实体的准确性',
                confidence_impact=0.3,
                auto_fix_available=False,
                user_action_required=True
            ),
            AlignmentIssue(
                issue_id='issue_002',
                issue_type='cross_modal_misalignment',
                description='文本与图像之间的对齐可能不准确',
                severity='high',
                affected_items=['alignment_012', 'alignment_015'],
                suggested_correction='重新校准文本引用与图像标记的对应关系',
                confidence_impact=0.6,
                auto_fix_available=True,
                user_action_required=False
            ),
            AlignmentIssue(
                issue_id='issue_003',
                issue_type='missing_knowledge',
                description='缺少领域专业知识',
                severity='low',
                affected_items=['entity_003'],
                suggested_correction='建议添加相关的技术标准知识',
                confidence_impact=0.2,
                auto_fix_available=True,
                user_action_required=False
            )
        ]

        session.issues_identified = sample_issues

        logger.info(f"✅ 识别到{len(sample_issues)}个对齐问题")

    async def get_session_overview(self) -> Dict[str, Any]:
        """获取会话概览"""
        if not self.current_session:
            return {'error': '没有活跃的对齐会话'}

        session = self.current_session

        overview = {
            'session_id': session.session_id,
            'document_id': session.document_id,
            'user_id': session.user_id,
            'mode': session.mode,
            'status': session.session_status,
            'start_time': session.start_time.isoformat(),
            'duration': (datetime.now() - session.start_time).total_seconds(),
            'issues_summary': {
                'total_issues': len(session.issues_identified),
                'severity_breakdown': self._get_severity_breakdown(session.issues_identified),
                'auto_fixable': sum(1 for issue in session.issues_identified if issue.auto_fix_available),
                'user_action_required': sum(1 for issue in session.issues_identified if issue.user_action_required)
            },
            'corrections_summary': {
                'total_corrections': len(session.corrections_made),
                'corrections_applied': sum(1 for correction in session.corrections_made if correction.applied),
                'correction_types': self._get_correction_type_breakdown(session.corrections_made)
            }
        }

        return overview

    def _get_severity_breakdown(self, issues: List[AlignmentIssue]) -> Dict[str, int]:
        """获取严重程度分布"""
        breakdown = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        for issue in issues:
            breakdown[issue.severity] = breakdown.get(issue.severity, 0) + 1
        return breakdown

    def _get_correction_type_breakdown(self, corrections: List[UserCorrection]) -> Dict[str, int]:
        """获取修正类型分布"""
        breakdown = {}
        for correction in corrections:
            correction_type = correction.correction_type.value
            breakdown[correction_type] = breakdown.get(correction_type, 0) + 1
        return breakdown

    async def get_visualization_data(self, data_type: str = 'alignment') -> Dict[str, Any]:
        """获取可视化数据"""
        if not self.current_session:
            return {'error': '没有活跃的对齐会话'}

        if data_type == 'alignment':
            # 生成对齐可视化数据
            # 这里应该加载实际的文档数据
            document_data = {
                'document_id': self.current_session.document_id,
                'nodes': [
                    {'id': 'node_1', 'content': '精馏塔', 'type': 'technical_feature', 'modality': 'text', 'confidence': 0.9},
                    {'id': 'node_2', 'content': '冷凝器', 'type': 'technical_feature', 'modality': 'text', 'confidence': 0.8},
                    {'id': 'node_3', 'content': '传感器', 'type': 'technical_feature', 'modality': 'image', 'confidence': 0.6}
                ],
                'edges': [
                    {'id': 'edge_1', 'source': 'node_1', 'target': 'node_2', 'type': 'composition', 'confidence': 0.8},
                    {'id': 'edge_2', 'source': 'node_1', 'target': 'node_3', 'type': 'spatial', 'confidence': 0.7}
                ]
            }

            return self.visualization_generator.generate_alignment_visualization(document_data)

        elif data_type == 'issues':
            # 生成问题热力图数据
            return self.visualization_generator.generate_issue_heatmap(self.current_session.issues_identified)

        else:
            return {'error': f"不支持的数据类型: {data_type}"}

    async def submit_correction(self,
                               correction_type: CorrectionType,
                               target_id: str,
                               original_value: Any,
                               corrected_value: Any,
                               justification: str,
                               confidence: float = 1.0) -> UserCorrection:
        """提交用户修正"""
        if not self.current_session:
            raise ValueError('没有活跃的对齐会话')

        correction = UserCorrection(
            correction_id=str(uuid.uuid4()),
            user_id=self.current_session.user_id,
            correction_type=correction_type,
            target_id=target_id,
            original_value=original_value,
            corrected_value=corrected_value,
            justification=justification,
            confidence=confidence
        )

        self.current_session.corrections_made.append(correction)
        self.correction_history.append(correction)

        logger.info(f"📝 用户提交修正: {correction_type.value} - {target_id}")

        return correction

    async def apply_correction(self, correction_id: str) -> bool:
        """应用修正"""
        if not self.current_session:
            return False

        # 查找修正
        correction = None
        for corr in self.current_session.corrections_made:
            if corr.correction_id == correction_id:
                correction = corr
                break

        if not correction:
            logger.warning(f"⚠️ 未找到修正: {correction_id}")
            return False

        # 应用修正（这里应该实际修改文档数据）
        try:
            # 模拟应用修正
            logger.info(f"✅ 应用修正: {correction.correction_type.value}")
            correction.applied = True

            # 记录学习数据
            self._record_learning_data(correction)

            return True

        except Exception as e:
            logger.error(f"❌ 应用修正失败: {str(e)}")
            return False

    def _record_learning_data(self, correction: UserCorrection):
        """记录学习数据"""
        if not self.current_session:
            return

        learning_data = {
            'correction_id': correction.correction_id,
            'correction_type': correction.correction_type.value,
            'original_confidence': getattr(correction.original_value, 'confidence', 0.5),
            'user_confidence': correction.confidence,
            'justification': correction.justification,
            'timestamp': correction.timestamp.isoformat()
        }

        if 'corrections' not in self.current_session.learning_data:
            self.current_session.learning_data['corrections'] = []

        self.current_session.learning_data['corrections'].append(learning_data)

    async def auto_fix_issues(self) -> List[str]:
        """自动修复问题"""
        if not self.current_session:
            return []

        fixed_issues = []

        for issue in self.current_session.issues_identified:
            if issue.auto_fix_available and not issue.user_action_required:
                try:
                    # 模拟自动修复
                    logger.info(f"🔧 自动修复问题: {issue.issue_id}")
                    fixed_issues.append(issue.issue_id)

                except Exception as e:
                    logger.error(f"❌ 自动修复失败: {issue.issue_id} - {str(e)}")

        return fixed_issues

    async def get_learning_insights(self) -> Dict[str, Any]:
        """获取学习洞察"""
        if not self.current_session or not self.current_session.learning_data:
            return {'message': '暂无学习数据'}

        learning_data = self.current_session.learning_data
        corrections = learning_data.get('corrections', [])

        if not corrections:
            return {'message': '暂无修正数据'}

        # 分析修正模式
        confidence_analysis = self._analyze_confidence_patterns(corrections)
        type_analysis = self._analyze_correction_types(corrections)

        insights = {
            'total_corrections': len(corrections),
            'confidence_patterns': confidence_analysis,
            'type_patterns': type_analysis,
            'recommendations': self._generate_learning_recommendations(corrections),
            'improvement_suggestions': self._generate_improvement_suggestions(corrections)
        }

        return insights

    def _analyze_confidence_patterns(self, corrections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析置信度模式"""
        original_confidences = [c['original_confidence'] for c in corrections]
        user_confidences = [c['user_confidence'] for c in corrections]

        if not original_confidences:
            return {}

        return {
            'avg_original_confidence': sum(original_confidences) / len(original_confidences),
            'avg_user_confidence': sum(user_confidences) / len(user_confidences),
            'confidence_gap': sum(user_confidences) / len(user_confidences) - sum(original_confidences) / len(original_confidences),
            'overconfidence_count': sum(1 for i, c in enumerate(corrections) if original_confidences[i] > user_confidences[i])
        }

    def _analyze_correction_types(self, corrections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析修正类型"""
        type_counts = {}
        for correction in corrections:
            correction_type = correction['correction_type']
            type_counts[correction_type] = type_counts.get(correction_type, 0) + 1

        return {
            'type_distribution': type_counts,
            'most_common_type': max(type_counts.items(), key=lambda x: x[1])[0] if type_counts else None
        }

    def _generate_learning_recommendations(self, corrections: List[Dict[str, Any]]) -> List[str]:
        """生成学习建议"""
        recommendations = []

        # 基于置信度分析的建议
        confidence_analysis = self._analyze_confidence_patterns(corrections)
        if confidence_analysis.get('confidence_gap', 0) < -0.2:
            recommendations.append('系统存在过度自信问题，建议调整置信度评估算法')

        # 基于修正类型的建议
        type_analysis = self._analyze_correction_types(corrections)
        most_common = type_analysis.get('most_common_type')
        if most_common == 'entity_correction':
            recommendations.append('实体识别准确率需要提升，建议加强领域特定训练')
        elif most_common == 'alignment_correction':
            recommendations.append('跨模态对齐算法需要优化，建议增强语义相似度计算')

        return recommendations

    def _generate_improvement_suggestions(self, corrections: List[Dict[str, Any]]) -> List[str]:
        """生成改进建议"""
        suggestions = [
            '考虑增加用户反馈的权重计算机制',
            '建立修正历史的知识库，用于持续学习',
            '实现自适应的置信度调整策略',
            '增加批量修正功能，提高用户体验'
        ]

        return suggestions

    async def end_session(self) -> Dict[str, Any]:
        """结束对齐会话"""
        if not self.current_session:
            return {'error': '没有活跃的对齐会话'}

        self.current_session.end_time = datetime.now()
        self.current_session.session_status = 'completed'

        # 生成会话总结
        session_summary = {
            'session_id': self.current_session.session_id,
            'duration': (self.current_session.end_time - self.current_session.start_time).total_seconds(),
            'issues_resolved': sum(1 for issue in self.current_session.issues_identified if issue.auto_fix_available),
            'corrections_made': len(self.current_session.corrections_made),
            'corrections_applied': sum(1 for correction in self.current_session.corrections_made if correction.applied),
            'learning_insights': await self.get_learning_insights()
        }

        logger.info(f"🏁 对齐会话结束: {self.current_session.session_id}")

        return session_summary

# 测试代码
if __name__ == '__main__':
    async def test_alignment_interface():
        """测试对齐接口"""
        logger.info('🎯 测试感知对齐接口...')

        # 初始化接口
        interface = InteractiveAlignmentInterface()

        # 启动会话
        session = await interface.start_alignment_session(
            document_id='CN201815134U',
            user_id='test_user',
            mode=InterfaceMode.REVIEW_MODE
        )

        logger.info(f"✅ 对齐会话启动: {session.session_id}")

        # 获取会话概览
        overview = await interface.get_session_overview()
        logger.info(f"📊 会话概览: {overview['issues_summary']}")

        # 获取可视化数据
        viz_data = await interface.get_visualization_data('alignment')
        logger.info(f"🎨 可视化数据: {viz_data['metadata']['total_nodes']}个节点")

        issue_viz = await interface.get_visualization_data('issues')
        logger.info(f"🔥 问题热力图: {issue_viz['auto_fixable']}个可自动修复")

        # 提交修正
        correction = await interface.submit_correction(
            correction_type=CorrectionType.ENTITY_CORRECTION,
            target_id='entity_005',
            original_value={'content': '错误实体', 'confidence': 0.3},
            corrected_value={'content': '正确实体', 'confidence': 0.9},
            justification='用户确认这是正确的技术术语',
            confidence=0.95
        )

        logger.info(f"📝 提交修正: {correction.correction_id}")

        # 应用修正
        applied = await interface.apply_correction(correction.correction_id)
        logger.info(f"✅ 修正应用: {applied}")

        # 自动修复问题
        fixed_issues = await interface.auto_fix_issues()
        logger.info(f"🔧 自动修复: {len(fixed_issues)}个问题")

        # 获取学习洞察
        insights = await interface.get_learning_insights()
        logger.info(f"🧠 学习洞察: {insights.get('total_corrections', 0)}个修正")

        # 结束会话
        summary = await interface.end_session()
        logger.info(f"🏁 会话总结: {summary}")

    # 运行测试
    asyncio.run(test_alignment_interface())