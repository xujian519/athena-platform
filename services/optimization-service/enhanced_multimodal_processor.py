#!/usr/bin/env python3
"""
增强多模态处理器 - 集成Dolphin文档解析能力
Enhanced Multimodal Processor with Dolphin Document Parsing Integration
"""

import os
import tempfile
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

# AI和HTTP客户端
import aiohttp
import requests

# 导入原有的多模态处理器
from multimodal_processor import (
    MediaItem,
    ModalityType,
    ProcessingResult,
    ProcessingTask,
    get_multimodal_processor,
)

from core.logging_config import setup_logging

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

# 新增处理任务类型
class EnhancedProcessingTask(ProcessingTask):
    """增强处理任务类型"""
    DOCUMENT_LAYOUT_ANALYSIS = 'document_layout_analysis'
    PROFESSIONAL_OCR = 'professional_ocr'
    STRUCTURED_EXTRACTION = 'structured_extraction'
    DOLPHIN_PARSE = 'dolphin_parse'

@dataclass
class DolphinProcessingOptions:
    """Dolphin处理选项"""
    include_layout: bool = True
    include_ocr: bool = True
    max_pages: int = 10
    structured_output: bool = True
    confidence_threshold: float = 0.8
    language: str = 'ch'

class EnhancedMultimodalProcessor:
    """增强的多模态处理器，集成Dolphin文档解析能力"""

    def __init__(self):
        # 使用原有的多模态处理器
        self.base_processor = get_multimodal_processor()

        # Dolphin服务配置
        self.dolphin_endpoint = 'http://localhost:8013'
        self.dolphin_available = self._check_dolphin_service()

        # GLM视觉服务配置
        self.glm_vision_endpoint = 'http://localhost:8091'
        self.glm_vision_available = self._check_glm_vision_service()

        logger.info("Enhanced Multimodal Processor initialized:")
        logger.info(f"  - Base Processor: {'✓' if self.base_processor else '✗'}")
        logger.info(f"  - Dolphin Service: {'✓' if self.dolphin_available else '✗'}")
        logger.info(f"  - GLM Vision Service: {'✓' if self.glm_vision_available else '✗'}")

    def _check_dolphin_service(self) -> bool:
        """检查Dolphin服务是否可用"""
        try:
            response = requests.get(f"{self.dolphin_endpoint}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Dolphin服务不可用: {e}")
            return False

    def _check_glm_vision_service(self) -> bool:
        """检查GLM视觉服务是否可用"""
        try:
            response = requests.get(f"{self.glm_vision_endpoint}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"GLM视觉服务不可用: {e}")
            return False

    async def process_media(self, media_item: MediaItem, tasks: list[ProcessingTask],
                          options: dict[str, Any] | None = None) -> list[ProcessingResult]:
        """
        处理媒体文件，集成Dolphin文档解析能力

        Args:
            media_item: 媒体项目
            tasks: 处理任务列表
            options: 处理选项

        Returns:
            处理结果列表
        """
        results = []

        # 处理基础任务
        base_tasks = [task for task in tasks if not isinstance(task, EnhancedProcessingTask)]
        if base_tasks and self.base_processor:
            base_results = await self.base_processor.process_media(media_item, base_tasks, options)
            results.extend(base_results)

        # 处理增强任务
        enhanced_tasks = [task for task in tasks if isinstance(task, EnhancedProcessingTask)]

        for task in enhanced_tasks:
            try:
                if task == EnhancedProcessingTask.DOLPHIN_PARSE:
                    result = await self._process_with_dolphin(media_item, options)
                    results.append(result)
                elif task == EnhancedProcessingTask.DOCUMENT_LAYOUT_ANALYSIS:
                    result = await self._analyze_document_layout(media_item, options)
                    results.append(result)
                elif task == EnhancedProcessingTask.PROFESSIONAL_OCR:
                    result = await self._professional_ocr(media_item, options)
                    results.append(result)
                elif task == EnhancedProcessingTask.STRUCTURED_EXTRACTION:
                    result = await self._structured_extraction(media_item, options)
                    results.append(result)

            except Exception as e:
                logger.error(f"增强任务处理失败 {task}: {e}")
                error_result = ProcessingResult(
                    result_id=str(uuid.uuid4()),
                    task_type=task,
                    input_item=media_item,
                    output_data={'error': str(e), 'task': task.value},
                    confidence=0.0,
                    model_used='enhanced_processor_error'
                )
                results.append(error_result)

        # 如果没有使用增强任务，使用Dolphin增强文档处理
        if not enhanced_tasks and media_item.modality_type == ModalityType.DOCUMENT and self.dolphin_available:
            try:
                dolphin_result = await self._process_with_dolphin(media_item, options)
                results.append(dolphin_result)
            except Exception as e:
                logger.error(f"Dolphin增强处理失败: {e}")

        return results

    async def _process_with_dolphin(self, media_item: MediaItem,
                                  options: dict[str, Any] | None = None) -> ProcessingResult:
        """使用Dolphin处理文档"""
        if not self.dolphin_available:
            raise Exception('Dolphin服务不可用')

        start_time = time.time()

        try:
            # 准备文件
            file_path = await self._prepare_file_for_dolphin(media_item)

            # 准备处理选项
            dolphin_options = DolphinProcessingOptions(**(options or {}))

            # 调用Dolphin服务
            async with aiohttp.ClientSession() as session:
                data = aiohttp.FormData()
                data.add_field('file', open(file_path, 'rb'),
                             filename=Path(file_path).name,
                             content_type='application/octet-stream')
                data.add_field('include_layout', str(dolphin_options.include_layout))
                data.add_field('include_ocr', str(dolphin_options.include_ocr))
                data.add_field('max_pages', str(dolphin_options.max_pages))

                async with session.post(f"{self.dolphin_endpoint}/parse", data=data) as response:
                    if response.status == 200:
                        result_data = await response.json()

                        # 增强结果数据
                        enhanced_result = self._enhance_dolphin_result(result_data, media_item)

                        return ProcessingResult(
                            result_id=str(uuid.uuid4()),
                            task_type=EnhancedProcessingTask.DOLPHIN_PARSE,
                            input_item=media_item,
                            output_data=enhanced_result,
                            confidence=0.9,
                            processing_time=time.time() - start_time,
                            model_used='Dolphin-Enhanced'
                        )
                    else:
                        raise Exception(f"Dolphin解析失败: HTTP {response.status}")

        except Exception as e:
            logger.error(f"Dolphin处理失败: {e}")
            return ProcessingResult(
                result_id=str(uuid.uuid4()),
                task_type=EnhancedProcessingTask.DOLPHIN_PARSE,
                input_item=media_item,
                output_data={'error': str(e)},
                confidence=0.0,
                processing_time=time.time() - start_time,
                model_used='Dolphin-Error'
            )
        finally:
            # 清理临时文件
            if 'file_path' in locals() and os.path.exists(file_path):
                os.unlink(file_path)

    async def _analyze_document_layout(self, media_item: MediaItem,
                                     options: dict[str, Any] | None = None) -> ProcessingResult:
        """分析文档版面"""
        if not self.dolphin_available:
            # 使用基础版面分析
            return await self._fallback_layout_analysis(media_item, options)

        try:
            # 调用Dolphin进行版面分析
            dolphin_options = {
                'include_layout': True,
                'include_ocr': False,
                **(options or {})
            }

            result = await self._process_with_dolphin(media_item, dolphin_options)

            # 提取版面分析结果
            layout_data = result.output_data.get('result', {}).get('layout_analysis', {})

            return ProcessingResult(
                result_id=str(uuid.uuid4()),
                task_type=EnhancedProcessingTask.DOCUMENT_LAYOUT_ANALYSIS,
                input_item=media_item,
                output_data={
                    'layout_blocks': layout_data.get('blocks', []),
                    'block_types': layout_data.get('block_types', []),
                    'total_blocks': layout_data.get('total_blocks', 0),
                    'layout_summary': self._generate_layout_summary(layout_data)
                },
                confidence=0.85,
                processing_time=result.processing_time,
                model_used='Dolphin-Layout'
            )

        except Exception as e:
            logger.error(f"版面分析失败: {e}")
            return await self._fallback_layout_analysis(media_item, options)

    async def _professional_ocr(self, media_item: MediaItem,
                               options: dict[str, Any] | None = None) -> ProcessingResult:
        """专业OCR文字识别"""
        if not self.dolphin_available:
            # 使用GLM视觉作为备选
            return await self._fallback_ocr(media_item, options)

        try:
            # 调用Dolphin进行OCR
            dolphin_options = {
                'include_layout': False,
                'include_ocr': True,
                **(options or {})
            }

            result = await self._process_with_dolphin(media_item, dolphin_options)

            # 提取OCR结果
            ocr_data = result.output_data.get('result', {}).get('ocr_result', {})

            return ProcessingResult(
                result_id=str(uuid.uuid4()),
                task_type=EnhancedProcessingTask.PROFESSIONAL_OCR,
                input_item=media_item,
                output_data={
                    'extracted_text': ocr_data.get('full_text', ''),
                    'text_blocks': ocr_data.get('text_blocks', []),
                    'total_blocks': ocr_data.get('total_blocks', 0),
                    'language_detection': 'zh-CN',  # Dolphin默认支持中英文
                    'confidence_scores': [block.get('confidence', 0.0)
                                        for block in ocr_data.get('text_blocks', [])]
                },
                confidence=0.9,
                processing_time=result.processing_time,
                model_used='Dolphin-OCR'
            )

        except Exception as e:
            logger.error(f"专业OCR失败: {e}")
            return await self._fallback_ocr(media_item, options)

    async def _structured_extraction(self, media_item: MediaItem,
                                    options: dict[str, Any] | None = None) -> ProcessingResult:
        """结构化内容提取"""
        try:
            # 组合使用Dolphin和GLM视觉
            dolphin_result = None
            glm_result = None

            # 使用Dolphin进行版面和OCR分析
            if self.dolphin_available:
                dolphin_options = {
                    'include_layout': True,
                    'include_ocr': True,
                    'structured_output': True,
                    **(options or {})
                }
                dolphin_result = await self._process_with_dolphin(media_item, dolphin_options)

            # 使用GLM视觉进行内容理解
            if self.glm_vision_available:
                glm_result = await self._analyze_with_glm_vision(media_item, options)

            # 融合结果
            structured_content = self._merge_structured_results(dolphin_result, glm_result)

            return ProcessingResult(
                result_id=str(uuid.uuid4()),
                task_type=EnhancedProcessingTask.STRUCTURED_EXTRACTION,
                input_item=media_item,
                output_data=structured_content,
                confidence=0.88,
                processing_time=time.time(),
                model_used='Dolphin-GLM-Fusion'
            )

        except Exception as e:
            logger.error(f"结构化提取失败: {e}")
            return ProcessingResult(
                result_id=str(uuid.uuid4()),
                task_type=EnhancedProcessingTask.STRUCTURED_EXTRACTION,
                input_item=media_item,
                output_data={'error': str(e)},
                confidence=0.0,
                processing_time=0.0,
                model_used='Error'
            )

    async def _prepare_file_for_dolphin(self, media_item: MediaItem) -> str:
        """为Dolphin准备文件"""
        if media_item.file_path and os.path.exists(media_item.file_path):
            return media_item.file_path

        elif media_item.binary_data:
            # 保存二进制数据到临时文件
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.bin')
            temp_file.write(media_item.binary_data)
            temp_file.close()
            return temp_file.name

        else:
            raise ValueError('媒体项目没有有效的文件数据')

    def _enhance_dolphin_result(self, dolphin_result: dict, media_item: MediaItem) -> dict:
        """增强Dolphin结果"""
        enhanced = dolphin_result.copy()

        # 添加元数据
        enhanced['metadata'] = {
            'processor': 'EnhancedMultimodalProcessor',
            'modality_type': media_item.modality_type.value,
            'item_id': media_item.item_id,
            'processing_time': datetime.now().isoformat(),
            'enhancement_level': 'full'
        }

        # 如果Dolphin成功解析，添加分析摘要
        if dolphin_result.get('success') and 'result' in dolphin_result:
            result = dolphin_result['result']
            enhanced['analysis_summary'] = self._generate_analysis_summary(result)

            # 添加质量评估
            enhanced['quality_assessment'] = self._assess_extraction_quality(result)

        return enhanced

    def _generate_analysis_summary(self, result: dict) -> dict:
        """生成分析摘要"""
        summary = {
            'content_types': [],
            'extraction_quality': 'unknown',
            'structure_detected': False
        }

        # 分析内容类型
        if 'merged_content' in result:
            categorized = result['merged_content'].get('categorized_content', {})
            if categorized:
                summary['content_types'] = [content_type for content_type in categorized.keys()
                                          if categorized[content_type]]
                summary['structure_detected'] = True

        # 评估提取质量
        if 'ocr_result' in result:
            ocr_data = result['ocr_result']
            total_blocks = ocr_data.get('total_blocks', 0)
            if total_blocks > 0:
                avg_confidence = sum(block.get('confidence', 0)
                                   for block in ocr_data.get('text_blocks', [])) / total_blocks
                if avg_confidence > 0.9:
                    summary['extraction_quality'] = 'excellent'
                elif avg_confidence > 0.8:
                    summary['extraction_quality'] = 'good'
                elif avg_confidence > 0.7:
                    summary['extraction_quality'] = 'fair'
                else:
                    summary['extraction_quality'] = 'poor'

        return summary

    def _assess_extraction_quality(self, result: dict) -> dict:
        """评估提取质量"""
        assessment = {
            'overall_score': 0.0,
            'text_quality': 0.0,
            'structure_quality': 0.0,
            'completeness': 0.0
        }

        # 文本质量评估
        if 'ocr_result' in result:
            ocr_blocks = result['ocr_result'].get('text_blocks', [])
            if ocr_blocks:
                confidences = [block.get('confidence', 0) for block in ocr_blocks]
                assessment['text_quality'] = sum(confidences) / len(confidences)

        # 结构质量评估
        if 'layout_analysis' in result:
            layout_blocks = result['layout_analysis'].get('blocks', [])
            if layout_blocks:
                block_scores = [block.get('score', 0) for block in layout_blocks]
                assessment['structure_quality'] = sum(block_scores) / len(block_scores) if block_scores else 0

        # 完整性评估
        content_areas = 0
        if 'merged_content' in result:
            categorized = result['merged_content'].get('categorized_content', {})
            content_areas = sum(1 for items in categorized.values() if items)

        assessment['completeness'] = min(content_areas / 5.0, 1.0)  # 最多5种内容类型

        # 总体评分
        assessment['overall_score'] = (
            assessment['text_quality'] * 0.4 +
            assessment['structure_quality'] * 0.3 +
            assessment['completeness'] * 0.3
        )

        return assessment

    def _generate_layout_summary(self, layout_data: dict) -> str:
        """生成版面摘要"""
        if not layout_data or 'blocks' not in layout_data:
            return '未检测到版面结构'

        blocks = layout_data['blocks']
        block_types = [block.get('type', 'unknown') for block in blocks]

        type_counts = {}
        for block_type in block_types:
            type_counts[block_type] = type_counts.get(block_type, 0) + 1

        summary_parts = []
        for block_type, count in type_counts.items():
            type_name = {
                'title': '标题',
                'text': '正文',
                'figure': '图片',
                'table': '表格',
                'list': '列表'
            }.get(block_type, block_type)

            summary_parts.append(f"{count}个{type_name}")

        if summary_parts:
            return f"检测到{len(blocks)}个版面元素：' + '、".join(summary_parts)
        else:
            return '检测到版面元素但无法分类'

    async def _fallback_layout_analysis(self, media_item: MediaItem,
                                      options: dict[str, Any] | None = None) -> ProcessingResult:
        """备用版面分析"""
        # 使用基础处理器进行分析
        if self.base_processor:
            return await self.base_processor.process_media(
                media_item, [ProcessingTask.ANALYZE_CONTENT], options
            )
        else:
            return ProcessingResult(
                result_id=str(uuid.uuid4()),
                task_type=EnhancedProcessingTask.DOCUMENT_LAYOUT_ANALYSIS,
                input_item=media_item,
                output_data={'error': '无可用的版面分析服务'},
                confidence=0.0,
                model_used='Fallback'
            )

    async def _fallback_ocr(self, media_item: MediaItem,
                           options: dict[str, Any] | None = None) -> ProcessingResult:
        """备用OCR识别"""
        # 使用GLM视觉进行OCR
        if self.glm_vision_available:
            return await self._analyze_with_glm_vision(media_item, options)
        else:
            return ProcessingResult(
                result_id=str(uuid.uuid4()),
                task_type=EnhancedProcessingTask.PROFESSIONAL_OCR,
                input_item=media_item,
                output_data={'error': '无可用的OCR服务'},
                confidence=0.0,
                model_used='Fallback'
            )

    async def _analyze_with_glm_vision(self, media_item: MediaItem,
                                     options: dict[str, Any] | None = None) -> ProcessingResult:
        """使用GLM视觉进行分析"""
        try:
            # 准备文件
            file_path = await self._prepare_file_for_dolphin(media_item)

            # 调用GLM视觉API
            with open(file_path, 'rb') as f:
                files = {'file': f}
                data = {
                    'text': options.get('prompt', '请详细分析这个文档的内容和结构'),
                    'model': 'glm-4v-plus'
                }

                response = requests.post(
                    f"{self.glm_vision_endpoint}/analyze-image",
                    files=files,
                    data=data,
                    timeout=30
                )

                if response.status_code == 200:
                    glm_result = response.json()

                    return ProcessingResult(
                        result_id=str(uuid.uuid4()),
                        task_type=EnhancedProcessingTask.PROFESSIONAL_OCR,
                        input_item=media_item,
                        output_data={
                            'glm_analysis': glm_result,
                            'extracted_content': glm_result.get('analysis', ''),
                            'confidence': 0.8
                        },
                        confidence=0.8,
                        processing_time=0.0,
                        model_used='GLM-4V-Plus'
                    )
                else:
                    raise Exception(f"GLM视觉API调用失败: {response.status_code}")

        except Exception as e:
            logger.error(f"GLM视觉分析失败: {e}")
            raise e
        finally:
            if 'file_path' in locals() and os.path.exists(file_path):
                os.unlink(file_path)

    def _merge_structured_results(self, dolphin_result: ProcessingResult,
                                glm_result: ProcessingResult) -> dict[str, Any]:
        """融合结构化结果"""
        merged = {
            'dolphin_analysis': None,
            'glm_analysis': None,
            'structured_content': {},
            'confidence_fusion': 0.0
        }

        # 提取Dolphin结果
        if dolphin_result and dolphin_result.output_data.get('success'):
            merged['dolphin_analysis'] = dolphin_result.output_data.get('result', {})

            # 提取结构化内容
            if 'merged_content' in merged['dolphin_analysis']:
                merged['structured_content'] = merged['dolphin_analysis']['merged_content']

        # 提取GLM结果
        if glm_result:
            merged['glm_analysis'] = glm_result.output_data

        # 计算融合置信度
        dolphin_conf = dolphin_result.confidence if dolphin_result else 0.0
        glm_conf = glm_result.confidence if glm_result else 0.0
        merged['confidence_fusion'] = (dolphin_conf * 0.7 + glm_conf * 0.3)

        return merged

    async def cross_modal_search(self, query: str, modality_filter: ModalityType | None = None,
                               limit: int = 10) -> list[dict[str, Any]]:
        """跨模态搜索（继承原有功能）"""
        if self.base_processor:
            return await self.base_processor.cross_modal_search(query, modality_filter, limit)
        else:
            logger.warning('基础多模态处理器不可用，跨模态搜索功能受限')
            return []

# 全局实例
_enhanced_processor = None

def get_enhanced_multimodal_processor() -> EnhancedMultimodalProcessor:
    """获取增强多模态处理器实例"""
    global _enhanced_processor
    if _enhanced_processor is None:
        _enhanced_processor = EnhancedMultimodalProcessor()
    return _enhanced_processor

# 兼容性函数
def get_multimodal_processor() -> Any | None:
    """获取多模态处理器（向后兼容）"""
    return get_enhanced_multimodal_processor()
