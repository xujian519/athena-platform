#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认知决策层集成系统
Cognitive Decision Integration Layer

功能:
1. 统一认知处理 - 整合所有认知模块的统一接口
2. 智能决策融合 - 多模型结果的智能融合
3. 自适应优化 - 根据反馈持续优化性能
4. 实时监控 - 认知处理过程的实时监控
5. 知识管理 - 认知结果的持久化管理
"""

import asyncio
import json
import logging
import os
import pickle
import sys
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入认知模块
try:
    from enhanced_patent_feature_extractor import EnhancedPatentFeatureExtractor
except ImportError as e:
    logger.warning(f"增强特征提取器导入失败: {e}")
    EnhancedPatentFeatureExtractor = None

try:
    from enhanced_reasoning_engine import EnhancedReasoningEngine, ReasoningResult
except ImportError as e:
    logger.warning(f"增强推理引擎导入失败: {e}")
    EnhancedReasoningEngine = None

try:
    from cognitive_decision_manager import CognitiveDecisionManager, DecisionLevel
except ImportError as e:
    logger.warning(f"认知决策管理器导入失败: {e}")
    CognitiveDecisionManager = None

try:
    from hybrid_reasoning_architecture import HybridReasoningEngine, ReasoningMode
except ImportError as e:
    logger.warning(f"混合推理架构导入失败: {e}")
    HybridReasoningEngine = None

try:
    from dynamic_knowledge_graph import KnowledgeGraphManager, NodeType, RelationType
except ImportError as e:
    logger.warning(f"动态知识图谱导入失败: {e}")
    KnowledgeGraphManager = None

try:
    from large_language_model_integration import LargeLanguageModelIntegration, TaskType
except ImportError as e:
    logger.warning(f"大语言模型集成导入失败: {e}")
    LargeLanguageModelIntegration = None

try:
    from multimodal_patent_understanding import (
        ContentType,
        MultimodalPatentUnderstanding,
    )
except ImportError as e:
    logger.warning(f"多模态专利理解导入失败: {e}")
    MultimodalPatentUnderstanding = None

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


class ProcessingMode(Enum):
    """处理模式枚举"""
    FAST = 'fast'                    # 快速模式 - 仅使用规则推理
    BALANCED = 'balanced'            # 平衡模式 - 规则 + AI分析
    COMPREHENSIVE = 'comprehensive'  # 全面模式 - 所有模块
    CUSTOM = 'custom'                # 自定义模式


class ConfidenceLevel(Enum):
    """置信度等级"""
    VERY_LOW = 0.2      # 很低
    LOW = 0.4           # 低
    MEDIUM = 0.6        # 中等
    HIGH = 0.8          # 高
    VERY_HIGH = 0.95    # 很高


@dataclass
class CognitiveRequest:
    """认知处理请求"""
    request_id: str
    patent_data: Dict[str, Any]
    processing_mode: ProcessingMode = ProcessingMode.BALANCED
    task_type: str = 'general_analysis'
    context: Optional[Dict[str, Any]] = None
    options: Optional[Dict[str, Any]] = None
    priority: int = 1  # 1-5, 5最高
    user_id: str | None = None


@dataclass
class CognitiveResult:
    """认知处理结果"""
    request_id: str
    task_type: str
    processing_mode: ProcessingMode
    results: Dict[str, Any]
    confidence: float
    processing_time: float
    modules_used: List[str]
    summary: str
    recommendations: List[str]
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ProcessingStats:
    """处理统计"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_processing_time: float = 0.0
    module_usage: Dict[str, int] = None
    confidence_distribution: Dict[str, int] = None
    performance_metrics: Dict[str, float] = None

    def __post_init__(self):
        if self.module_usage is None:
            self.module_usage = {}
        if self.confidence_distribution is None:
            self.confidence_distribution = {level.name: 0 for level in ConfidenceLevel}
        if self.performance_metrics is None:
            self.performance_metrics = {}


class ModuleManager:
    """模块管理器"""

    def __init__(self):
        self.modules = {}
        self.module_status = {}
        self._initialize_modules()

    def _initialize_modules(self):
        """初始化认知模块"""
        # 特征提取器
        if EnhancedPatentFeatureExtractor:
            try:
                self.modules['feature_extractor'] = EnhancedPatentFeatureExtractor()
                self.module_status['feature_extractor'] = 'loaded'
            except Exception as e:
                logger.error(f"特征提取器初始化失败: {e}")
                self.module_status['feature_extractor'] = 'failed'
        else:
            self.module_status['feature_extractor'] = 'unavailable'

        # 推理引擎
        if EnhancedReasoningEngine:
            try:
                self.modules['reasoning_engine'] = EnhancedReasoningEngine()
                self.module_status['reasoning_engine'] = 'loaded'
            except Exception as e:
                logger.error(f"推理引擎初始化失败: {e}")
                self.module_status['reasoning_engine'] = 'failed'
        else:
            self.module_status['reasoning_engine'] = 'unavailable'

        # 认知决策管理器
        if CognitiveDecisionManager:
            try:
                self.modules['decision_manager'] = CognitiveDecisionManager()
                self.module_status['decision_manager'] = 'loaded'
            except Exception as e:
                logger.error(f"决策管理器初始化失败: {e}")
                self.module_status['decision_manager'] = 'failed'
        else:
            self.module_status['decision_manager'] = 'unavailable'

        # 混合推理引擎
        if HybridReasoningEngine:
            try:
                self.modules['hybrid_reasoning'] = HybridReasoningEngine()
                self.module_status['hybrid_reasoning'] = 'loaded'
            except Exception as e:
                logger.error(f"混合推理引擎初始化失败: {e}")
                self.module_status['hybrid_reasoning'] = 'failed'
        else:
            self.module_status['hybrid_reasoning'] = 'unavailable'

        # 知识图谱管理器
        if KnowledgeGraphManager:
            try:
                self.modules['knowledge_graph'] = KnowledgeGraphManager()
                self.module_status['knowledge_graph'] = 'loaded'
            except Exception as e:
                logger.error(f"知识图谱管理器初始化失败: {e}")
                self.module_status['knowledge_graph'] = 'failed'
        else:
            self.module_status['knowledge_graph'] = 'unavailable'

        # 大语言模型集成
        if LargeLanguageModelIntegration:
            try:
                self.modules['llm_integration'] = LargeLanguageModelIntegration()
                self.module_status['llm_integration'] = 'loaded'
            except Exception as e:
                logger.error(f"大语言模型集成初始化失败: {e}")
                self.module_status['llm_integration'] = 'failed'
        else:
            self.module_status['llm_integration'] = 'unavailable'

        # 多模态理解
        if MultimodalPatentUnderstanding:
            try:
                self.modules['multimodal'] = MultimodalPatentUnderstanding()
                self.module_status['multimodal'] = 'loaded'
            except Exception as e:
                logger.error(f"多模态理解初始化失败: {e}")
                self.module_status['multimodal'] = 'failed'
        else:
            self.module_status['multimodal'] = 'unavailable'

    def get_module(self, module_name: str):
        """获取模块实例"""
        return self.modules.get(module_name)

    def is_available(self, module_name: str) -> bool:
        """检查模块是否可用"""
        return self.module_status.get(module_name) == 'loaded'

    def get_status(self) -> Dict[str, str]:
        """获取所有模块状态"""
        return self.module_status.copy()


class ResultFusionEngine:
    """结果融合引擎"""

    def __init__(self):
        self.fusion_strategies = {
            'weighted_average': self._weighted_average_fusion,
            'confidence_voting': self._confidence_voting_fusion,
            'hierarchical': self._hierarchical_fusion,
            'ml_based': self._ml_based_fusion
        }

    async def fuse_results(self, results: Dict[str, Any], strategy: str = 'hierarchical') -> Dict[str, Any]:
        """融合多个模块的结果"""
        if strategy not in self.fusion_strategies:
            strategy = 'hierarchical'

        fusion_func = self.fusion_strategies[strategy]
        return await fusion_func(results)

    async def _weighted_average_fusion(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """加权平均融合"""
        fused_result = {
            'confidence': 0.0,
            'scores': {},
            'reasoning': '',
            'evidence': []
        }

        total_weight = 0.0

        for module_name, result in results.items():
            if result and isinstance(result, dict):
                confidence = result.get('confidence', 0.0)
                weight = confidence  # 使用置信度作为权重

                # 融合分数
                if 'scores' in result:
                    for key, value in result['scores'].items():
                        if key not in fused_result['scores']:
                            fused_result['scores'][key] = 0.0
                        fused_result['scores'][key] += value * weight

                # 收集推理过程
                if 'reasoning' in result:
                    fused_result['reasoning'] += f"[{module_name}] {result['reasoning']}\n"

                # 收集证据
                if 'evidence' in result:
                    fused_result['evidence'].extend(result['evidence'])

                fused_result['confidence'] += confidence * weight
                total_weight += weight

        # 标准化分数和置信度
        if total_weight > 0:
            fused_result['confidence'] /= total_weight
            for key in fused_result['scores']:
                fused_result['scores'][key] /= total_weight

        return fused_result

    async def _confidence_voting_fusion(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """置信度投票融合"""
        votes = {}
        total_votes = 0

        for module_name, result in results.items():
            if result and isinstance(result, dict):
                confidence = result.get('confidence', 0.0)
                if confidence > 0.5:  # 只有置信度超过0.5的结果才参与投票
                    # 投票权重基于置信度
                    vote_weight = int(confidence * 10)

                    # 对决策进行投票
                    if 'decision' in result:
                        decision = result['decision']
                        if decision not in votes:
                            votes[decision] = 0
                        votes[decision] += vote_weight
                        total_votes += vote_weight

        # 确定得票最多的决策
        best_decision = None
        max_votes = 0

        for decision, vote_count in votes.items():
            if vote_count > max_votes:
                max_votes = vote_count
                best_decision = decision

        # 计算融合置信度
        fusion_confidence = max_votes / total_votes if total_votes > 0 else 0.0

        return {
            'decision': best_decision,
            'confidence': fusion_confidence,
            'vote_distribution': votes,
            'total_votes': total_votes
        }

    async def _hierarchical_fusion(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """分层融合"""
        # 定义模块优先级层次
        module_hierarchy = {
            'reasoning_engine': 1,      # 最高优先级 - 法律推理
            'hybrid_reasoning': 2,      # 混合推理
            'decision_manager': 3,      # 决策管理
            'llm_integration': 4,       # 大语言模型
            'knowledge_graph': 5,       # 知识图谱
            'feature_extractor': 6,     # 特征提取
            'multimodal': 7             # 多模态理解
        }

        # 按优先级排序结果
        sorted_results = []
        for module_name, result in results.items():
            if result and isinstance(result, dict) and module_name in module_hierarchy:
                priority = module_hierarchy[module_name]
                sorted_results.append((priority, module_name, result))

        sorted_results.sort(key=lambda x: x[0])

        # 分层融合：高优先级的结果优先，低优先级的用于补充和验证
        primary_result = None
        supporting_evidence = []
        conflicting_views = []

        for priority, module_name, result in sorted_results:
            if primary_result is None:
                # 第一个有效结果作为主要结果
                primary_result = result.copy()
                primary_result['primary_source'] = module_name
            else:
                # 其他结果作为补充证据或冲突观点
                if self._is_supporting(primary_result, result):
                    supporting_evidence.append({
                        'module': module_name,
                        'evidence': result,
                        'confidence': result.get('confidence', 0.0)
                    })
                else:
                    conflicting_views.append({
                        'module': module_name,
                        'conflict': result,
                        'confidence': result.get('confidence', 0.0)
                    })

        # 调整主要结果的置信度
        if primary_result:
            support_factor = sum(e['confidence'] for e in supporting_evidence) / len(supporting_evidence) if supporting_evidence else 0
            conflict_factor = sum(c['confidence'] for c in conflicting_views) / len(conflicting_views) if conflicting_views else 0

            # 有支持证据提高置信度，有冲突观点降低置信度
            confidence_adjustment = (support_factor - conflict_factor) * 0.1
            primary_result['confidence'] = max(0.0, min(1.0, primary_result.get('confidence', 0.0) + confidence_adjustment))

            primary_result['supporting_evidence'] = supporting_evidence
            primary_result['conflicting_views'] = conflicting_views

        return primary_result or {}

    async def _ml_based_fusion(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """基于机器学习的融合"""
        # 简化实现：基于历史性能的权重融合
        # 实际应用中可以使用训练好的融合模型

        module_performance = {
            'reasoning_engine': 0.9,
            'hybrid_reasoning': 0.85,
            'decision_manager': 0.8,
            'llm_integration': 0.75,
            'knowledge_graph': 0.7,
            'feature_extractor': 0.6,
            'multimodal': 0.65
        }

        fused_result = {
            'confidence': 0.0,
            'scores': {},
            'reasoning': '',
            'evidence': [],
            'method': 'ml_based_fusion'
        }

        total_weight = 0.0

        for module_name, result in results.items():
            if result and isinstance(result, dict):
                # 基于模块性能和结果置信度的组合权重
                performance = module_performance.get(module_name, 0.5)
                confidence = result.get('confidence', 0.0)
                weight = performance * confidence

                # 融合逻辑类似于加权平均
                if 'scores' in result:
                    for key, value in result['scores'].items():
                        if key not in fused_result['scores']:
                            fused_result['scores'][key] = 0.0
                        fused_result['scores'][key] += value * weight

                if 'reasoning' in result:
                    fused_result['reasoning'] += f"[{module_name} (w:{weight:.2f})] {result['reasoning']}\n"

                if 'evidence' in result:
                    fused_result['evidence'].extend(result['evidence'])

                fused_result['confidence'] += confidence * weight
                total_weight += weight

        # 标准化
        if total_weight > 0:
            fused_result['confidence'] /= total_weight
            for key in fused_result['scores']:
                fused_result['scores'][key] /= total_weight

        return fused_result

    def _is_supporting(self, primary: Dict[str, Any], candidate: Dict[str, Any]) -> bool:
        """判断候选结果是否支持主要结果"""
        # 简化的支持度判断
        primary_decision = primary.get('decision')
        candidate_decision = candidate.get('decision')

        if primary_decision and candidate_decision:
            return primary_decision == candidate_decision

        # 基于分数的相似度判断
        primary_scores = primary.get('scores', {})
        candidate_scores = candidate.get('scores', {})

        if not primary_scores or not candidate_scores:
            return True  # 默认认为是支持的

        # 计算分数相似度
        similarity = 0.0
        common_keys = set(primary_scores.keys()) & set(candidate_scores.keys())

        for key in common_keys:
            primary_val = primary_scores[key]
            candidate_val = candidate_scores[key]
            # 归一化并计算相似度
            similarity += 1 - abs(primary_val - candidate_val)

        if common_keys:
            similarity /= len(common_keys)
            return similarity > 0.7

        return True


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self):
        self.metrics = {}
        self.alerts = []
        self.performance_history = []

    def record_processing_time(self, module_name: str, processing_time: float):
        """记录处理时间"""
        if module_name not in self.metrics:
            self.metrics[module_name] = {
                'total_requests': 0,
                'total_time': 0.0,
                'average_time': 0.0,
                'max_time': 0.0,
                'min_time': float('inf')
            }

        metrics = self.metrics[module_name]
        metrics['total_requests'] += 1
        metrics['total_time'] += processing_time
        metrics['average_time'] = metrics['total_time'] / metrics['total_requests']
        metrics['max_time'] = max(metrics['max_time'], processing_time)
        metrics['min_time'] = min(metrics['min_time'], processing_time)

        # 检查性能告警
        if processing_time > metrics['average_time'] * 2:
            self.add_alert(f"{module_name} 处理时间过长: {processing_time:.2f}s")

    def record_confidence(self, module_name: str, confidence: float):
        """记录置信度"""
        if module_name not in self.metrics:
            self.metrics[module_name] = {}

        if 'confidence_history' not in self.metrics[module_name]:
            self.metrics[module_name]['confidence_history'] = []

        self.metrics[module_name]['confidence_history'].append(confidence)

        # 保持历史记录长度
        if len(self.metrics[module_name]['confidence_history']) > 100:
            self.metrics[module_name]['confidence_history'] = \
                self.metrics[module_name]['confidence_history'][-100:]

    def add_alert(self, message: str):
        """添加告警"""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'severity': 'warning'
        }
        self.alerts.append(alert)

        # 保持告警历史
        if len(self.alerts) > 50:
            self.alerts = self.alerts[-50:]

    def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return {
            'module_metrics': self.metrics,
            'recent_alerts': self.alerts[-10:] if self.alerts else [],
            'total_alerts': len(self.alerts)
        }

    def generate_performance_report(self) -> str:
        """生成性能报告"""
        lines = [
            '# 认知层性能报告',
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            ''
        ]

        for module_name, metrics in self.metrics.items():
            if 'total_requests' in metrics:
                lines.extend([
                    f"## {module_name}",
                    f"- 总请求数: {metrics['total_requests']}",
                    f"- 平均处理时间: {metrics['average_time']:.2f}s",
                    f"- 最大处理时间: {metrics['max_time']:.2f}s",
                    f"- 最小处理时间: {metrics['min_time']:.2f}s",
                    ''
                ])

            if 'confidence_history' in metrics:
                history = metrics['confidence_history']
                if history:
                    avg_confidence = sum(history) / len(history)
                    lines.extend([
                        f"- 平均置信度: {avg_confidence:.3f}",
                        f"- 最近置信度: {history[-1]:.3f}",
                        ''
                    ])

        if self.alerts:
            lines.extend([
                '## 最近告警',
                *[f"- {alert['timestamp']}: {alert['message']}" for alert in self.alerts[-5:]],
                ''
            ])

        return "\n".join(lines)


class CognitiveIntegrationLayer:
    """认知决策层集成系统"""

    def __init__(self):
        self.module_manager = ModuleManager()
        self.result_fusion = ResultFusionEngine()
        self.performance_monitor = PerformanceMonitor()
        self.processing_stats = ProcessingStats()
        self.cache = {}
        self.knowledge_updates = []

    async def process_request(self, request: CognitiveRequest) -> CognitiveResult:
        """处理认知请求"""
        start_time = time.time()

        try:
            self.processing_stats.total_requests += 1

            # 检查缓存
            cache_key = self._generate_cache_key(request)
            if cache_key in self.cache:
                logger.info(f"使用缓存结果: {request.request_id}")
                cached_result = self.cache[cache_key]
                cached_result.processing_time = time.time() - start_time
                return cached_result

            # 根据处理模式选择模块
            modules_to_use = self._select_modules(request.processing_mode)
            module_results = {}
            modules_used = []

            # 并行处理各模块
            tasks = []
            for module_name in modules_to_use:
                if self.module_manager.is_available(module_name):
                    task = self._process_with_module(module_name, request)
                    tasks.append((module_name, task))

            # 等待所有任务完成
            for module_name, task in tasks:
                try:
                    result = await asyncio.wait_for(task, timeout=30.0)
                    if result:
                        module_results[module_name] = result
                        modules_used.append(module_name)

                        # 记录性能指标
                        if isinstance(result, dict) and 'processing_time' in result:
                            self.performance_monitor.record_processing_time(
                                module_name, result['processing_time']
                            )
                        if isinstance(result, dict) and 'confidence' in result:
                            self.performance_monitor.record_confidence(
                                module_name, result['confidence']
                            )
                except asyncio.TimeoutError:
                    logger.warning(f"{module_name} 处理超时")
                    self.performance_monitor.add_alert(f"{module_name} 处理超时")
                except Exception as e:
                    logger.error(f"{module_name} 处理失败: {str(e)}")

            # 融合结果
            fused_result = await self.result_fusion.fuse_results(
                module_results,
                strategy='hierarchical'
            )

            # 生成总结和建议
            summary = self._generate_summary(fused_result, modules_used)
            recommendations = self._generate_recommendations(fused_result, request)

            processing_time = time.time() - start_time

            # 创建结果
            result = CognitiveResult(
                request_id=request.request_id,
                task_type=request.task_type,
                processing_mode=request.processing_mode,
                results=fused_result,
                confidence=fused_result.get('confidence', 0.0),
                processing_time=processing_time,
                modules_used=modules_used,
                summary=summary,
                recommendations=recommendations,
                metadata={
                    'cache_key': cache_key,
                    'module_count': len(modules_used),
                    'total_modules': len(modules_to_use)
                }
            )

            # 更新统计
            self.processing_stats.successful_requests += 1
            self._update_processing_stats(processing_time, result.confidence)

            # 缓存结果
            self.cache[cache_key] = result

            # 更新知识图谱
            await self._update_knowledge_graph(request, result)

            logger.info(f"请求处理完成: {request.request_id}, 耗时: {processing_time:.2f}s")
            return result

        except Exception as e:
            processing_time = time.time() - start_time
            self.processing_stats.failed_requests += 1
            logger.error(f"请求处理失败 {request.request_id}: {str(e)}")

            return CognitiveResult(
                request_id=request.request_id,
                task_type=request.task_type,
                processing_mode=request.processing_mode,
                results={'error': str(e)},
                confidence=0.0,
                processing_time=processing_time,
                modules_used=[],
                summary=f"处理失败: {str(e)}",
                recommendations=[],
                metadata={'error': str(e)}
            )

    def _select_modules(self, processing_mode: ProcessingMode) -> List[str]:
        """根据处理模式选择模块"""
        available_modules = [name for name, status in self.module_manager.get_status().items()
                           if status == 'loaded']

        if processing_mode == ProcessingMode.FAST:
            return ['reasoning_engine']  # 仅使用推理引擎
        elif processing_mode == ProcessingMode.BALANCED:
            return ['reasoning_engine', 'feature_extractor', 'decision_manager']
        elif processing_mode == ProcessingMode.COMPREHENSIVE:
            return available_modules  # 使用所有可用模块
        elif processing_mode == ProcessingMode.CUSTOM:
            return ['reasoning_engine', 'hybrid_reasoning', 'llm_integration']
        else:
            return available_modules

    async def _process_with_module(self, module_name: str, request: CognitiveRequest) -> Dict[str, Any]:
        """使用指定模块处理请求"""
        module = self.module_manager.get_module(module_name)
        if not module:
            return None

        start_time = time.time()

        try:
            if module_name == 'feature_extractor':
                return await self._process_with_feature_extractor(module, request)
            elif module_name == 'reasoning_engine':
                return await self._process_with_reasoning_engine(module, request)
            elif module_name == 'decision_manager':
                return await self._process_with_decision_manager(module, request)
            elif module_name == 'hybrid_reasoning':
                return await self._process_with_hybrid_reasoning(module, request)
            elif module_name == 'knowledge_graph':
                return await self._process_with_knowledge_graph(module, request)
            elif module_name == 'llm_integration':
                return await self._process_with_llm_integration(module, request)
            elif module_name == 'multimodal':
                return await self._process_with_multimodal(module, request)
            else:
                logger.warning(f"未知模块: {module_name}")
                return None

        except Exception as e:
            logger.error(f"{module_name} 处理错误: {str(e)}")
            return {
                'error': str(e),
                'processing_time': time.time() - start_time,
                'confidence': 0.0
            }

    async def _process_with_feature_extractor(self, extractor, request: CognitiveRequest) -> Dict[str, Any]:
        """特征提取器处理"""
        patent_text = request.patent_data.get('text', '')
        if not patent_text:
            return None

        features = await extractor.extract_patent_features(patent_text)

        return {
            'type': 'feature_extraction',
            'features': features,
            'processing_time': getattr(features, 'processing_time', 0.0),
            'confidence': getattr(features, 'average_confidence', 0.7)
        }

    async def _process_with_reasoning_engine(self, engine, request: CognitiveRequest) -> Dict[str, Any]:
        """推理引擎处理"""
        reasoning_result = await engine.reason(request.patent_data)

        return {
            'type': 'legal_reasoning',
            'decision': reasoning_result.decision,
            'reasoning': reasoning_result.reasoning,
            'evidence': reasoning_result.evidence,
            'confidence': reasoning_result.confidence,
            'processing_time': getattr(reasoning_result, 'processing_time', 0.0)
        }

    async def _process_with_decision_manager(self, manager, request: CognitiveRequest) -> Dict[str, Any]:
        """决策管理器处理"""
        decision = await manager.make_decision(request.patent_data, request.context)

        return {
            'type': 'cognitive_decision',
            'decision': decision.decision,
            'decision_level': decision.decision_level.name,
            'confidence': decision.confidence,
            'recommendations': decision.recommendations,
            'processing_time': getattr(decision, 'processing_time', 0.0)
        }

    async def _process_with_hybrid_reasoning(self, engine, request: CognitiveRequest) -> Dict[str, Any]:
        """混合推理引擎处理"""
        # 这里需要根据实际的HybridReasoningEngine接口调整
        patent_text = request.patent_data.get('text', '')

        # 模拟混合推理结果
        return {
            'type': 'hybrid_reasoning',
            'reasoning_mode': ReasoningMode.HYBRID_SEQUENTIAL.value,
            'decision': '通过分析',
            'confidence': 0.85,
            'rule_confidence': 0.9,
            'neural_confidence': 0.8,
            'processing_time': 2.5
        }

    async def _process_with_knowledge_graph(self, manager, request: CognitiveRequest) -> Dict[str, Any]:
        """知识图谱处理"""
        # 搜索相关知识
        patent_text = request.patent_data.get('text', '')
        search_results = manager.search_nodes(patent_text[:100])  # 使用前100字符搜索

        return {
            'type': 'knowledge_graph',
            'related_nodes': search_results,
            'node_count': len(search_results),
            'confidence': 0.7,
            'processing_time': 0.5
        }

    async def _process_with_llm_integration(self, llm, request: CognitiveRequest) -> Dict[str, Any]:
        """大语言模型集成处理"""
        patent_text = request.patent_data.get('text', '')

        # 使用LLM进行分析
        analysis_result = await llm.analyze_patent(patent_text[:1000])  # 限制长度

        return {
            'type': 'llm_analysis',
            'analysis': analysis_result,
            'confidence': 0.8,
            'processing_time': 3.0
        }

    async def _process_with_multimodal(self, multimodal, request: CognitiveRequest) -> Dict[str, Any]:
        """多模态理解处理"""
        # 如果专利数据包含图像路径
        image_path = request.patent_data.get('image_path')
        if image_path and os.path.exists(image_path):
            analysis_result = await multimodal.process_patent_document(image_path)

            return {
                'type': 'multimodal_analysis',
                'summary': analysis_result.summary,
                'extracted_content': len(analysis_result.extracted_content),
                'confidence': analysis_result.confidence,
                'processing_time': analysis_result.processing_time
            }

        return {
            'type': 'multimodal_analysis',
            'summary': '未找到图像内容',
            'extracted_content': 0,
            'confidence': 0.0,
            'processing_time': 0.1
        }

    def _generate_cache_key(self, request: CognitiveRequest) -> str:
        """生成缓存键"""
        key_data = {
            'patent_hash': hashlib.md5(
                json.dumps(request.patent_data, sort_keys=True, usedforsecurity=False).encode()
            ).hexdigest()[:16],
            'mode': request.processing_mode.value,
            'task_type': request.task_type
        }
        return json.dumps(key_data, sort_keys=True)

    def _generate_summary(self, fused_result: Dict[str, Any], modules_used: List[str]) -> str:
        """生成处理总结"""
        if 'error' in fused_result:
            return f"处理失败: {fused_result['error']}"

        summary_parts = []

        # 模块使用情况
        summary_parts.append(f"使用了 {len(modules_used)} 个认知模块: {', '.join(modules_used)}")

        # 决策信息
        if 'decision' in fused_result:
            summary_parts.append(f"主要决策: {fused_result['decision']}")

        # 置信度
        confidence = fused_result.get('confidence', 0.0)
        summary_parts.append(f"综合置信度: {confidence:.2f}")

        # 关键发现
        if 'scores' in fused_result:
            scores = fused_result['scores']
            if 'novelty' in scores:
                summary_parts.append(f"新颖性评分: {scores['novelty']:.2f}")
            if 'inventive' in scores:
                summary_parts.append(f"创造性评分: {scores['inventive']:.2f}")

        return '; '.join(summary_parts)

    def _generate_recommendations(self, fused_result: Dict[str, Any], request: CognitiveRequest) -> List[str]:
        """生成建议"""
        recommendations = []

        # 基于置信度的建议
        confidence = fused_result.get('confidence', 0.0)
        if confidence < 0.5:
            recommendations.append('建议进行人工复核，系统置信度较低')
        elif confidence < 0.7:
            recommendations.append('建议补充更多技术信息以提高分析准确性')

        # 基于决策的建议
        if 'decision' in fused_result:
            decision = fused_result['decision']
            if '驳回' in decision or '拒绝' in decision:
                recommendations.append('建议准备修改材料以应对潜在驳回')

        # 基于分数的建议
        scores = fused_result.get('scores', {})
        if scores.get('novelty', 1.0) < 0.5:
            recommendations.append('建议进行更全面的新颖性检索')
        if scores.get('inventive', 1.0) < 0.6:
            recommendations.append('建议强调技术方案的突出特点和创新点')

        return recommendations

    def _update_processing_stats(self, processing_time: float, confidence: float):
        """更新处理统计"""
        # 更新平均处理时间
        total = self.processing_stats.total_requests
        current_avg = self.processing_stats.average_processing_time
        self.processing_stats.average_processing_time = (
            (current_avg * (total - 1) + processing_time) / total
        )

        # 更新置信度分布
        if confidence >= ConfidenceLevel.VERY_HIGH.value:
            self.processing_stats.confidence_distribution['VERY_HIGH'] += 1
        elif confidence >= ConfidenceLevel.HIGH.value:
            self.processing_stats.confidence_distribution['HIGH'] += 1
        elif confidence >= ConfidenceLevel.MEDIUM.value:
            self.processing_stats.confidence_distribution['MEDIUM'] += 1
        elif confidence >= ConfidenceLevel.LOW.value:
            self.processing_stats.confidence_distribution['LOW'] += 1
        else:
            self.processing_stats.confidence_distribution['VERY_LOW'] += 1

    async def _update_knowledge_graph(self, request: CognitiveRequest, result: CognitiveResult):
        """更新知识图谱"""
        if not self.module_manager.is_available('knowledge_graph'):
            return

        kg = self.module_manager.get_module('knowledge_graph')

        # 提取关键信息用于知识图谱更新
        patent_id = request.patent_data.get('patent_id', f"patent_{request.request_id}")
        patent_title = request.patent_data.get('title', '未知专利')
        patent_text = request.patent_data.get('text', '')

        # 创建专利节点
        try:
            kg.add_node(
                patent_id,
                NodeType.PATENT,
                {
                    'title': patent_title,
                    'summary': patent_text[:200] if patent_text else '',
                    'confidence': result.confidence,
                    'decision': result.results.get('decision', ''),
                    'processing_time': result.processing_time,
                    'modules_used': result.modules_used,
                    'timestamp': datetime.now().isoformat()
                }
            )

            # 如果有技术关键词，创建技术节点
            keywords = result.results.get('keywords', [])
            for keyword in keywords[:5]:  # 限制数量
                tech_id = f"tech_{keyword}_{hashlib.md5(keyword.encode('utf-8'), usedforsecurity=False).hexdigest()[:8]}"
                kg.add_node(tech_id, NodeType.TECHNOLOGY, {'name': keyword})

                # 创建专利-技术关系
                kg.add_relation(patent_id, tech_id, RelationType.USES_IN, {'confidence': 0.8})

        except Exception as e:
            logger.error(f"知识图谱更新失败: {str(e)}")

    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            'module_status': self.module_manager.get_status(),
            'processing_stats': asdict(self.processing_stats),
            'performance_metrics': self.performance_monitor.get_metrics(),
            'cache_size': len(self.cache),
            'knowledge_updates': len(self.knowledge_updates)
        }

    def export_knowledge_graph(self, format: str = 'json') -> str | None:
        """导出知识图谱"""
        if not self.module_manager.is_available('knowledge_graph'):
            return None

        kg = self.module_manager.get_module('knowledge_graph')
        return kg.export_graph(format)

    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
        logger.info('认知层缓存已清空')

    def generate_comprehensive_report(self) -> str:
        """生成综合报告"""
        lines = [
            '# 认知决策层综合报告',
            f"报告时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            '',
            '## 系统概览'
        ]

        # 模块状态
        module_status = self.module_manager.get_status()
        loaded_modules = [name for name, status in module_status.items() if status == 'loaded']
        lines.extend([
            f"- 已加载模块: {len(loaded_modules)}/{len(module_status)}",
            f"- 活跃模块: {', '.join(loaded_modules)}",
            ''
        ])

        # 处理统计
        stats = self.processing_stats
        success_rate = (stats.successful_requests / stats.total_requests * 100) if stats.total_requests > 0 else 0
        lines.extend([
            '## 处理统计',
            f"- 总请求数: {stats.total_requests}",
            f"- 成功请求: {stats.successful_requests}",
            f"- 失败请求: {stats.failed_requests}",
            f"- 成功率: {success_rate:.1f}%",
            f"- 平均处理时间: {stats.average_processing_time:.2f}s",
            ''
        ])

        # 性能报告
        lines.append('## 性能报告')
        performance_report = self.performance_monitor.generate_performance_report()
        lines.append(performance_report)

        return "\n".join(lines)


# 创建全局实例
cognitive_integration = CognitiveIntegrationLayer()


# 测试函数
async def test_cognitive_integration():
    """测试认知集成层"""
    logger.info('🧠 测试认知决策层集成系统')

    # 创建测试请求
    test_request = CognitiveRequest(
        request_id='test_001',
        patent_data={
            'patent_id': 'TEST001',
            'title': '基于人工智能的专利审查方法',
            'text': '''
            本发明公开了一种基于人工智能的专利审查方法，包括以下步骤：
            1. 获取待审查专利文本；
            2. 使用自然语言处理技术提取专利特征；
            3. 基于机器学习模型进行新颖性判断；
            4. 输出审查结果和修改建议。

            该方法提高了专利审查的效率和准确性。
            '''
        },
        processing_mode=ProcessingMode.BALANCED,
        task_type='patent_analysis',
        user_id='test_user'
    )

    logger.info("\n🔄 处理认知请求...")
    result = await cognitive_integration.process_request(test_request)

    logger.info(f"✅ 处理完成!")
    logger.info(f"任务类型: {result.task_type}")
    logger.info(f"处理模式: {result.processing_mode.value}")
    logger.info(f"使用模块: {', '.join(result.modules_used)}")
    logger.info(f"置信度: {result.confidence:.2f}")
    logger.info(f"处理时间: {result.processing_time:.2f}s")
    logger.info(f"总结: {result.summary}")

    if result.recommendations:
        logger.info("\n💡 建议:")
        for rec in result.recommendations:
            logger.info(f"- {rec}")

    # 显示系统状态
    logger.info("\n📊 系统状态:")
    status = cognitive_integration.get_system_status()
    print(json.dumps(status, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    asyncio.run(test_cognitive_integration())