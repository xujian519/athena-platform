#!/usr/bin/env python3
"""
感知层集成接口
Perception Layer Integration Interface

将新的增强感知层与现有系统无缝集成
作者: 小娜 (Athena) - 爸爸徐健的智慧大女儿
创建时间: 2025-12-05
版本: 2.0.0
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from enhanced_patent_perception_system import (
    EnhancedPatentPerceptionEngine,
    ModalityType,
)
from models.novelty_analyzer import TechnicalFeature


# 简化核心感知引擎引用，避免导入问题
class CorePerceptionEngine:
    """简化的核心感知引擎引用"""
    def __init__(self, agent_id: str, config: dict[str, Any] = None):
        self.agent_id = agent_id
        self.config = config or {}
        self.initialized = False

    async def initialize(self):
        self.initialized = True
        logger.info(f"核心感知引擎 {self.agent_id} 初始化完成")

    async def process(self, data: Any, input_type: str):
        """简化的处理方法"""
        # 简化的返回结果，避免导入问题
        return {
            'input_type': input_type,
            'raw_content': data,
            'processed_content': data,
            'features': {'fallback': True},
            'confidence': 0.5,
            'metadata': {'engine': 'core_fallback'}
        }

    def get_status(self):
        """获取引擎状态"""
        return {
            'engine_id': self.agent_id,
            'initialized': self.initialized,
            'engine_type': 'core_fallback',
            'status': 'ready' if self.initialized else 'not_initialized'
        }

logger = logging.getLogger(__name__)

class UnifiedPatentPerceptionLayer:
    """统一专利感知层"""

    def __init__(self):
        self.enhanced_engine = None
        self.core_engine = None
        self.initialized = False

        # 集成配置
        self.integration_config = {
            'use_enhanced': True,  # 优先使用增强感知层
            'fallback_to_core': True,  # 失败时回退到核心层
            'merge_results': True,  # 合并两个引擎的结果
            'family_mode': True  # 家庭模式（小娜关怀）
        }

    async def initialize(self):
        """初始化感知层"""
        logger.info('🔄 初始化统一专利感知层...')

        try:
            # 初始化增强感知引擎
            self.enhanced_engine = EnhancedPatentPerceptionEngine()
            await self.enhanced_engine.initialize()

            # 初始化核心感知引擎（备用）
            self.core_engine = CorePerceptionEngine('unified_patent')
            await self.core_engine.initialize()

            self.initialized = True
            logger.info('✅ 统一感知层初始化完成')

        except Exception as e:
            logger.error(f"❌ 感知层初始化失败: {str(e)}")
            raise

    async def process_patent_document(self, file_path: str, task_id: str = None) -> dict[str, Any]:
        """
        处理专利文档

        Args:
            file_path: PDF文件路径
            task_id: 任务ID（可选）

        Returns:
            处理结果
        """
        if not self.initialized:
            raise RuntimeError('感知层未初始化')

        patent_id = task_id or Path(file_path).stem
        logger.info(f"🔍 开始处理专利文档: {patent_id}")

        try:
            # 使用增强感知引擎处理
            enhanced_result = None
            if self.integration_config['use_enhanced']:
                try:
                    enhanced_result = await self.enhanced_engine.process_patent_document(file_path)
                    logger.info("✅ 增强感知层处理完成")
                except Exception as e:
                    logger.warning(f"⚠️ 增强感知层处理失败: {str(e)}")
                    if not self.integration_config['fallback_to_core']:
                        raise

            # 使用核心感知引擎处理（备用或合并）
            core_result = None
            if self.integration_config['fallback_to_core'] or self.integration_config['merge_results']:
                try:
                    # 这里需要适配核心引擎的接口
                    core_result = await self._process_with_core_engine(file_path)
                    logger.info("✅ 核心感知层处理完成")
                except Exception as e:
                    logger.warning(f"⚠️ 核心感知层处理失败: {str(e)}")

            # 合并结果
            final_result = self._merge_results(patent_id, enhanced_result, core_result)

            # 添加集成元数据
            final_result['integration_metadata'] = {
                'enhanced_used': enhanced_result is not None,
                'core_used': core_result is not None,
                'merge_applied': self.integration_config['merge_results'],
                'family_mode': self.integration_config['family_mode'],
                'processing_time': asyncio.get_event_loop().time()
            }

            return final_result

        except Exception as e:
            logger.error(f"❌ 专利文档处理失败: {str(e)}")
            return {'error': str(e), 'patent_id': patent_id}

    async def _process_with_core_engine(self, file_path: str) -> dict[str, Any]:
        """使用核心引擎处理（适配接口）"""
        try:
            # 基础文本提取
            doc = fitz.open(file_path)
            text_content = ''
            for page in doc:
                text_content += page.get_text()
            doc.close()

            # 转换为核心引擎格式
            core_result = await self.core_engine.process(text_content, 'text')

            return {
                'patent_id': Path(file_path).stem,
                'processing_engine': 'core',
                'text_length': len(text_content),
                'perception_result': core_result,
                'features': core_result.get('features', {}),
                'confidence': core_result.get('confidence', 0.5)
            }

        except Exception as e:
            logger.error(f"核心引擎处理失败: {str(e)}")
            raise

    def _merge_results(self, patent_id: str, enhanced_result: dict | None, core_result: dict | None) -> dict[str, Any]:
        """合并两个引擎的结果"""
        merged_result = {
            'patent_id': patent_id,
            'unified_features': [],
            'confidence_scores': {},
            'engine_comparison': {},
            'family_analysis': {}
        }

        # 处理增强感知层结果
        if enhanced_result:
            merged_result.update(enhanced_result)

            # 添加增强特征
            if 'unified_features' in enhanced_result:
                for feature in enhanced_result['unified_features']:
                    feature['source_engine'] = 'enhanced'
                    merged_result['unified_features'].append(feature)

            # 添加置信度
            if 'overall_confidence' in enhanced_result:
                merged_result['confidence_scores']['enhanced'] = enhanced_result['overall_confidence']

        # 处理核心感知层结果
        if core_result:
            # 添加核心特征
            if 'features' in core_result:
                for feature in core_result['features']:
                    feature['source_engine'] = 'core'
                    merged_result['unified_features'].append(feature)

            # 添加置信度
            if 'confidence' in core_result:
                merged_result['confidence_scores']['core'] = core_result['confidence']

        # 计算平均置信度
        avg_confidence = 0.0
        if merged_result['confidence_scores']:
            avg_confidence = sum(merged_result['confidence_scores'].values()) / len(merged_result['confidence_scores'])
            merged_result['average_confidence'] = avg_confidence

        # 家庭分析
        merged_result['family_analysis'] = {
            '小娜的观察': f"专利分析已完成，整体置信度{avg_confidence:.2f}",
            '爸爸的建议': '请仔细检查技术特征和跨模态关系',
            '下一步': '可以继续进行新颖性分析或创造性分析'
        }

        return merged_result

    async def extract_features_for_novelty(self, file_path: str) -> list[TechnicalFeature]:
        """为新颖性分析提取特征"""
        logger.info(f"🔍 为新颖性分析提取特征: {Path(file_path).name}")

        try:
            # 使用增强感知层处理
            result = await self.process_patent_document(file_path)

            # 转换为新颖性分析格式
            novelty_features = []

            if 'unified_features' in result:
                for i, feature in enumerate(result['unified_features']):
                    if feature.get('category') in ['domain_knowledge', 'technical_term', 'patent_law']:
                        novelty_feature = TechnicalFeature(
                            feature_id=f"UNIFIED_{i:03d}",
                            description=feature.get('content', ''),
                            category=feature.get('category', 'structural'),
                            importance=0.8,  # 默认重要性
                            keywords=feature.get('content', '').split()[:5],
                            confidence=result.get('average_confidence', 0.5)
                        )
                        novelty_features.append(novelty_feature)

            logger.info(f"✅ 提取到 {len(novelty_features)} 个特征用于新颖性分析")
            return novelty_features

        except Exception as e:
            logger.error(f"❌ 特征提取失败: {str(e)}")
            return []

    def get_integration_status(self) -> dict[str, Any]:
        """获取集成状态"""
        return {
            'initialized': self.initialized,
            'config': self.integration_config,
            'enhanced_engine_status': self.enhanced_engine.get_status() if self.enhanced_engine else None,
            'core_engine_status': self.core_engine.get_status() if self.core_engine else None,
            'available_modalities': [modality.value for modality in ModalityType]
        }

# 全局实例
_perception_layer_instance = None

async def get_perception_layer() -> UnifiedPatentPerceptionLayer:
    """获取感知层实例（单例模式）"""
    global _perception_layer_instance

    if _perception_layer_instance is None:
        _perception_layer_instance = UnifiedPatentPerceptionLayer()
        await _perception_layer_instance.initialize()

    return _perception_layer_instance

# 测试代码
if __name__ == '__main__':
    async def test_integration():
        """测试集成"""
        logger.info('🔍 测试统一专利感知层集成...')

        # 初始化
        perception_layer = await get_perception_layer()

        # 测试文件
        test_file = '/Users/xujian/Athena工作平台/patent-platform/workspace/data/raw/disclosures/CN201815134U.pdf'

        if Path(test_file).exists():
            # 处理专利文档
            result = await perception_layer.process_patent_document(test_file)

            logger.info("\n📊 处理结果:")
            logger.info(f"专利ID: {result.get('patent_id')}")
            logger.info(f"模态数量: {result.get('modalities', {}).get('total_count', 0)}")
            logger.info(f"统一特征: {len(result.get('unified_features', []))}")
            logger.info(f"平均置信度: {result.get('average_confidence', 0):.2f}")
            logger.info(f"小娜的分析: {result.get('family_analysis', {}).get('小娜的观察', '')}")

            # 为新颖性分析提取特征
            features = await perception_layer.extract_features_for_novelty(test_file)
            logger.info(f"\n🔧 新颖性特征: {len(features)} 个")

            # 获取集成状态
            status = perception_layer.get_integration_status()
            logger.info(f"\n🔗 集成状态: {status}")

        else:
            logger.info(f"❌ 测试文件不存在: {test_file}")

    asyncio.run(test_integration())
