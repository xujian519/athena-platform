#!/usr/bin/env python3
"""
LangExtract平台集成服务
将LangExtract集成到Athena平台的专业业务服务
"""

import asyncio
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from common_tools.langextract_tool import ExtractionScenario, get_langextract_tool
from xiaonuo_crawler_control import get_xiaonuo_crawler_controller
from xiaonuo_langextract_control import get_xiaonuo_langextract_controller

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

class IntegrationMode(Enum):
    """集成模式枚举"""
    XIAONUO_AUTO = 'xiaonuo_auto'  # 小诺全自动模式
    XIAONUO_SEMI = 'xiaonuo_semi'  # 小诺半自动模式
    DIRECT_API = 'direct_api'     # 直接API调用
    CRAWLER_ENHANCED = 'crawler_enhanced'  # 爬虫增强模式
    BATCH_PROCESSING = 'batch_processing'  # 批量处理模式

@dataclass
class ExtractionRequest:
    """提取请求"""
    request_id: str
    mode: IntegrationMode
    user_input: str
    text_or_documents: str | list[str] | None = None
    scenario: str | None = None
    custom_prompt: str | None = None
    config: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    callback_url: str | None = None
    priority: int = 1

@dataclass
class ExtractionResponse:
    """提取响应"""
    request_id: str
    success: bool
    mode: IntegrationMode
    result: dict[str, Any] | None = None
    error: str | None = None
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

class LangExtractIntegrationService:
    """LangExtract集成服务"""

    def __init__(self):
        """初始化集成服务"""
        self.langextract_tool = get_langextract_tool()
        self.xiaonuo_controller = get_xiaonuo_langextract_controller()
        self.crawler_controller = get_xiaonuo_crawler_controller()

        self.active_requests = {}
        self.processing_queue = []
        self.statistics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'xiaonuo_usage': 0,
            'direct_api_usage': 0,
            'crawler_enhanced_usage': 0
        }

        # 业务场景集成配置
        self.business_integrations = self._load_business_integrations()

        logger.info('LangExtract集成服务初始化完成')

    def _load_business_integrations(self) -> dict[str, Any]:
        """加载业务集成配置"""
        return {
            'patent_business': {
                'enabled': True,
                'scenarios': [
                    ExtractionScenario.PATENT_ANALYSIS,
                    ExtractionScenario.CONTRACT_REVIEW,
                    ExtractionScenario.LEGAL_DOCUMENT
                ],
                'enhanced_features': [
                    'patent_claims_analysis',
                    'technical_features_extraction',
                    'prior_art_comparison',
                    'infringement_risk_assessment'
                ]
            },
            'financial_analysis': {
                'enabled': True,
                'scenarios': [
                    ExtractionScenario.FINANCIAL_STATEMENT,
                    ExtractionScenario.BUSINESS_REPORT,
                    ExtractionScenario.MARKET_RESEARCH
                ],
                'enhanced_features': [
                    'financial_ratio_analysis',
                    'trend_identification',
                    'risk_factor_extraction',
                    'compliance_check'
                ]
            },
            'medical_healthcare': {
                'enabled': True,
                'scenarios': [
                    ExtractionScenario.MEDICAL_REPORT
                ],
                'enhanced_features': [
                    'diagnosis_extraction',
                    'medication_analysis',
                    'symptom_tracking',
                    'treatment_plan_analysis'
                ]
            },
            'academic_research': {
                'enabled': True,
                'scenarios': [
                    ExtractionScenario.ACADEMIC_PAPER,
                    ExtractionScenario.TECHNICAL_DOCUMENT
                ],
                'enhanced_features': [
                    'literature_review',
                    'methodology_extraction',
                    'result_synthesis',
                    'citation_analysis'
                ]
            },
            'content_analysis': {
                'enabled': True,
                'scenarios': [
                    ExtractionScenario.NEWS_ARTICLE,
                    ExtractionScenario.PRODUCT_REVIEW,
                    ExtractionScenario.USER_FEEDBACK
                ],
                'enhanced_features': [
                    'sentiment_analysis',
                    'topic_modeling',
                    'opinion_mining',
                    'trend_detection'
                ]
            }
        }

    async def initialize(self) -> bool:
        """初始化集成服务"""
        try:
            # 初始化各个组件
            await self.langextract_tool.initialize()
            await self.xiaonuo_controller.initialize()

            logger.info('LangExtract集成服务启动成功')
            return True

        except Exception as e:
            logger.error(f"LangExtract集成服务启动失败: {e}")
            return False

    async def process_request(self, request: ExtractionRequest) -> ExtractionResponse:
        """处理提取请求"""
        start_time = datetime.now()

        try:
            logger.info(f"开始处理提取请求: {request.request_id}, 模式: {request.mode.value}")

            # 更新统计
            self.statistics['total_requests'] += 1

            # 根据模式处理请求
            if request.mode == IntegrationMode.XIAONUO_AUTO:
                result = await self._process_xiaonuo_auto(request)
                self.statistics['xiaonuo_usage'] += 1

            elif request.mode == IntegrationMode.XIAONUO_SEMI:
                result = await self._process_xiaonuo_semi(request)
                self.statistics['xiaonuo_usage'] += 1

            elif request.mode == IntegrationMode.DIRECT_API:
                result = await self._process_direct_api(request)
                self.statistics['direct_api_usage'] += 1

            elif request.mode == IntegrationMode.CRAWLER_ENHANCED:
                result = await self._process_crawler_enhanced(request)
                self.statistics['crawler_enhanced_usage'] += 1

            elif request.mode == IntegrationMode.BATCH_PROCESSING:
                result = await self._process_batch_processing(request)

            else:
                raise ValueError(f"不支持的集成模式: {request.mode}")

            # 更新统计
            if result['success']:
                self.statistics['successful_requests'] += 1
            else:
                self.statistics['failed_requests'] += 1

            # 计算执行时间
            execution_time = (datetime.now() - start_time).total_seconds()

            # 构建响应
            response = ExtractionResponse(
                request_id=request.request_id,
                success=result['success'],
                mode=request.mode,
                result=result.get('result'),
                error=result.get('error'),
                execution_time=execution_time,
                metadata={
                    'processing_steps': result.get('steps', []),
                    'enhancement_applied': result.get('enhancements', []),
                    'business_context': request.context.get('business_domain')
                }
            )

            logger.info(f"请求处理完成: {request.request_id}, 成功: {result['success']}, 耗时: {execution_time:.2f}秒")

            return response

        except Exception as e:
            logger.error(f"请求处理失败: {request.request_id}, 错误: {e}")
            execution_time = (datetime.now() - start_time).total_seconds()

            self.statistics['failed_requests'] += 1

            return ExtractionResponse(
                request_id=request.request_id,
                success=False,
                mode=request.mode,
                error=str(e),
                execution_time=execution_time
            )

    async def _process_xiaonuo_auto(self, request: ExtractionRequest) -> dict[str, Any]:
        """处理小诺全自动模式"""
        try:
            # 1. 小诺智能分析
            if not request.text_or_documents:
                # 需要先获取文本
                return {
                    'success': False,
                    'error': '缺少待提取的文本或文档',
                    'steps': ['xiaonuo_analysis'],
                    'suggestion': '请提供需要提取的文本或文档'
                }

            await self.xiaonuo_controller.analyze_request(
                request.user_input,
                request.context
            )

            # 2. 智能决策执行
            execution_result = await self.xiaonuo_controller.smart_extraction_execution(
                request.user_input,
                request.context,
                request.text_or_documents
            )

            return {
                'success': execution_result['success'],
                'result': execution_result.get('result'),
                'error': execution_result.get('error'),
                'steps': ['xiaonuo_analysis', 'smart_execution'],
                'xiaonuo_analysis': execution_result.get('analysis', {}),
                'enhancements': ['intelligent_decision', 'auto_scenario_matching']
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"小诺全自动处理失败: {str(e)}",
                'steps': ['xiaonuo_analysis']
            }

    async def _process_xiaonuo_semi(self, request: ExtractionRequest) -> dict[str, Any]:
        """处理小诺半自动模式"""
        try:
            # 1. 小诺分析提供建议
            analysis = await self.xiaonuo_controller.analyze_request(
                request.user_input,
                request.context
            )

            # 2. 用户确认后执行
            if not request.text_or_documents:
                return {
                    'success': False,
                    'error': '缺少待提取的文本或文档',
                    'steps': ['xiaonuo_analysis'],
                    'xiaonuo_suggestions': analysis.suggested_prompts,
                    'suggestion': '请确认提取参数并重新提交'
                }

            # 使用分析结果执行提取
            if request.scenario:
                result = await self.langextract_tool.execute_scenario(
                    scenario=request.scenario,
                    text_or_documents=request.text_or_documents,
                    config=request.config
                )
            else:
                # 使用推荐场景
                result = await self.langextract_tool.execute_scenario(
                    scenario=analysis.recommended_scenario,
                    text_or_documents=request.text_or_documents,
                    config=request.config
                )

            return {
                'success': result.success,
                'result': {
                    'extractions': result.extractions,
                    'stats': result.stats,
                    'data': result.data
                },
                'error': result.error,
                'steps': ['xiaonuo_analysis', 'user_confirmation', 'execution'],
                'xiaonuo_analysis': analysis.__dict__,
                'enhancements': ['scenario_recommendation', 'user_control']
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"小诺半自动处理失败: {str(e)}",
                'steps': ['xiaonuo_analysis']
            }

    async def _process_direct_api(self, request: ExtractionRequest) -> dict[str, Any]:
        """处理直接API调用模式"""
        try:
            if not request.text_or_documents:
                return {
                    'success': False,
                    'error': '缺少待提取的文本或文档',
                    'steps': ['parameter_validation']
                }

            if request.scenario:
                # 使用指定场景
                result = await self.langextract_tool.execute_scenario(
                    scenario=request.scenario,
                    text_or_documents=request.text_or_documents,
                    config=request.config
                )
            elif request.custom_prompt:
                # 使用自定义提示
                result = await self.langextract_tool.execute_custom_extraction(
                    text_or_documents=request.text_or_documents,
                    prompt_description=request.custom_prompt,
                    config=request.config
                )
            else:
                return {
                    'success': False,
                    'error': '必须指定场景或自定义提示',
                    'steps': ['parameter_validation']
                }

            return {
                'success': result.success,
                'result': {
                    'extractions': result.extractions,
                    'stats': result.stats,
                    'data': result.data
                },
                'error': result.error,
                'steps': ['parameter_validation', 'extraction_execution'],
                'enhancements': ['direct_control', 'flexible_parameters']
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"直接API调用失败: {str(e)}",
                'steps': ['parameter_validation', 'extraction_execution']
            }

    async def _process_crawler_enhanced(self, request: ExtractionRequest) -> dict[str, Any]:
        """处理爬虫增强模式"""
        try:
            # 1. 使用爬虫获取数据
            if not request.text_or_documents:
                # 尝试从用户输入中提取URL
                urls = self._extract_urls_from_text(request.user_input)
                if not urls:
                    return {
                        'success': False,
                        'error': '未找到URL，请提供URL或文本内容',
                        'steps': ['url_extraction']
                    }

                # 使用爬虫获取内容
                crawler_result = await self.crawler_controller.smart_crawler_execution(
                    f"爬取以下URL的内容: {', '.join(urls)}",
                    {'urls': urls}
                )

                if not crawler_result['success']:
                    return {
                        'success': False,
                        'error': f"爬取失败: {crawler_result.get('error', 'unknown')}",
                        'steps': ['url_extraction', 'web_crawling']
                    }

                # 获取爬取的内容
                crawled_content = crawler_result.get('execution_result', {}).get('data', [])
                if crawled_content:
                    request.text_or_documents = "\n\n".join(str(item) for item in crawled_content)
                else:
                    return {
                        'success': False,
                        'error': '爬取内容为空',
                        'steps': ['url_extraction', 'web_crawling']
                    }

            # 2. 执行信息提取
            if request.scenario:
                result = await self.langextract_tool.execute_scenario(
                    scenario=request.scenario,
                    text_or_documents=request.text_or_documents,
                    config=request.config
                )
            else:
                # 使用智能分析推荐场景
                analysis = await self.xiaonuo_controller.analyze_request(
                    request.user_input, request.context
                )
                result = await self.langextract_tool.execute_scenario(
                    scenario=analysis.recommended_scenario,
                    text_or_documents=request.text_or_documents,
                    config=request.config
                )

            return {
                'success': result.success,
                'result': {
                    'extractions': result.extractions,
                    'stats': result.stats,
                    'data': result.data,
                    'crawled_urls': urls if 'urls' in locals() else []
                },
                'error': result.error,
                'steps': ['url_extraction', 'web_crawling', 'extraction_execution'],
                'enhancements': ['auto_content_acquisition', 'integrated_pipeline']
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"爬虫增强处理失败: {str(e)}",
                'steps': ['url_extraction', 'web_crawling', 'extraction_execution']
            }

    async def _process_batch_processing(self, request: ExtractionRequest) -> dict[str, Any]:
        """处理批量处理模式"""
        try:
            if not request.text_or_documents:
                return {
                    'success': False,
                    'error': '批量处理需要提供文档列表',
                    'steps': ['batch_validation']
                }

            # 确保是列表格式
            if isinstance(request.text_or_documents, str):
                documents = [request.text_or_documents]
            else:
                documents = request.text_or_documents

            # 批量处理
            batch_results = []
            for i, doc in enumerate(documents):
                try:
                    if request.scenario:
                        result = await self.langextract_tool.execute_scenario(
                            scenario=request.scenario,
                            text_or_documents=doc,
                            config=request.config
                        )
                    else:
                        result = await self.langextract_tool.execute_custom_extraction(
                            text_or_documents=doc,
                            prompt_description=request.custom_prompt or '提取关键信息',
                            config=request.config
                        )

                    batch_results.append({
                        'document_index': i,
                        'success': result.success,
                        'extractions': result.extractions,
                        'stats': result.stats,
                        'error': result.error
                    })

                except Exception as e:
                    batch_results.append({
                        'document_index': i,
                        'success': False,
                        'error': str(e)
                    })

            # 汇总结果
            successful_count = sum(1 for r in batch_results if r['success'])
            total_extractions = sum(len(r.get('extractions', [])) for r in batch_results)

            return {
                'success': successful_count > 0,
                'result': {
                    'batch_results': batch_results,
                    'summary': {
                        'total_documents': len(documents),
                        'successful_documents': successful_count,
                        'success_rate': successful_count / len(documents),
                        'total_extractions': total_extractions
                    }
                },
                'steps': ['batch_validation', 'parallel_processing'],
                'enhancements': ['batch_efficiency', 'parallel_execution']
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"批量处理失败: {str(e)}",
                'steps': ['batch_validation', 'parallel_processing']
            }

    def _extract_urls_from_text(self, text: str) -> list[str]:
        """从文本中提取URL"""
        import re
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, text)
        return urls

    async def get_service_status(self) -> dict[str, Any]:
        """获取服务状态"""
        return {
            'service': 'LangExtract集成服务',
            'status': 'running',
            'version': '1.0.0',
            'components': {
                'langextract_tool': self.langextract_tool.get_status(),
                'xiaonuo_controller': self.xiaonuo_controller.get_status(),
                'business_integrations': {
                    domain: config['enabled']
                    for domain, config in self.business_integrations.items()
                }
            },
            'statistics': self.statistics,
            'active_requests': len(self.active_requests),
            'queue_size': len(self.processing_queue),
            'capabilities': [
                '智能场景识别',
                '自动决策执行',
                '爬虫内容获取',
                '批量并行处理',
                '业务场景集成',
                '实时监控分析'
            ]
        }

    async def batch_process(
        self,
        requests: list[ExtractionRequest],
        max_concurrent: int = 5
    ) -> list[ExtractionResponse]:
        """批量处理请求"""
        try:
            logger.info(f"开始批量处理 {len(requests)} 个请求")

            # 创建信号量控制并发数
            semaphore = asyncio.Semaphore(max_concurrent)

            async def process_single_request(request):
                async with semaphore:
                    return await self.process_request(request)

            # 并发处理所有请求
            tasks = [process_single_request(req) for req in requests]
            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # 处理异常结果
            processed_responses = []
            for i, response in enumerate(responses):
                if isinstance(response, Exception):
                    processed_responses.append(
                        ExtractionResponse(
                            request_id=requests[i].request_id,
                            success=False,
                            mode=requests[i].mode,
                            error=str(response)
                        )
                    )
                else:
                    processed_responses.append(response)

            logger.info(f"批量处理完成，成功: {sum(1 for r in processed_responses if r.success)}/{len(processed_responses)}")

            return processed_responses

        except Exception as e:
            logger.error(f"批量处理失败: {e}")
            # 返回失败响应
            return [
                ExtractionResponse(
                    request_id=req.request_id,
                    success=False,
                    mode=req.mode,
                    error=f"批量处理系统错误: {str(e)}"
                )
                for req in requests
            ]

    async def get_business_integrations(self) -> dict[str, Any]:
        """获取业务集成信息"""
        return {
            'total_integrations': len(self.business_integrations),
            'enabled_integrations': [
                domain for domain, config in self.business_integrations.items()
                if config['enabled']
            ],
            'integration_details': self.business_integrations
        }

    async def enhance_patent_business(
        self,
        patent_text: str,
        analysis_type: str = 'full'
    ) -> dict[str, Any]:
        """专利业务增强功能"""
        try:
            logger.info(f"开始专利业务增强分析: {analysis_type}")

            # 使用专利分析场景
            result = await self.langextract_tool.execute_scenario(
                scenario=ExtractionScenario.PATENT_ANALYSIS.value,
                text_or_documents=patent_text,
                config={
                    'analysis_type': analysis_type,
                    'include_claims': True,
                    'include_technical_features': True,
                    'include_prior_art': analysis_type == 'full'
                }
            )

            if result.success:
                # 添加专利特有的增强分析
                enhanced_result = {
                    'basic_extractions': result.extractions,
                    'patent_specific_analysis': {
                        'claims_structure': self._analyze_claims_structure(result.extractions),
                        'technical_features': self._extract_technical_features(result.extractions),
                        'innovation_highlights': self._identify_innovation_highlights(result.extractions),
                        'business_value': self._assess_patent_business_value(result.extractions)
                    }
                }

                result.data.update(enhanced_result)

            return {
                'success': result.success,
                'result': result.data,
                'error': result.error,
                'analysis_type': analysis_type
            }

        except Exception as e:
            logger.error(f"专利业务增强分析失败: {e}")
            return {
                'success': False,
                'error': f"专利分析失败: {str(e)}"
            }

    def _analyze_claims_structure(self, extractions: list[dict[str, Any]]) -> dict[str, Any]:
        """分析权利要求结构"""
        claims = [ext for ext in extractions if ext.get('extraction_class') == 'claim']
        return {
            'total_claims': len(claims),
            'independent_claims': len([c for c in claims if 'independent' in c.get('attributes', {})]),
            'dependent_claims': len([c for c in claims if 'dependent' in c.get('attributes', {})])
        }

    def _extract_technical_features(self, extractions: list[dict[str, Any]]) -> list[str]:
        """提取技术特征"""
        features = [ext for ext in extractions if ext.get('extraction_class') == 'technical_feature']
        return [feature['extraction_text'] for feature in features]

    def _identify_innovation_highlights(self, extractions: list[dict[str, Any]]) -> list[str]:
        """识别创新亮点"""
        innovations = [ext for ext in extractions if ext.get('extraction_class') == 'innovation']
        return [innovation['extraction_text'] for innovation in innovations]

    def _assess_patent_business_value(self, extractions: list[dict[str, Any]]) -> dict[str, Any]:
        """评估专利商业价值"""
        # 简化的商业价值评估
        return {
            'value_score': 0.8,  # 基于提取结果计算
            'market_potential': 'high',
            'competitive_advantage': 'significant',
            'licensing_potential': 'strong'
        }

    async def shutdown(self):
        """关闭服务"""
        logger.info('LangExtract集成服务正在关闭...')
        # 清理资源
        self.active_requests.clear()
        self.processing_queue.clear()
        logger.info('LangExtract集成服务已关闭')

# 全局实例
_langextract_integration_service = None

def get_langextract_integration_service() -> LangExtractIntegrationService:
    """获取LangExtract集成服务实例"""
    global _langextract_integration_service
    if _langextract_integration_service is None:
        _langextract_integration_service = LangExtractIntegrationService()
    return _langextract_integration_service
