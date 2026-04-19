"""
技术分析服务适配器
将技术分析服务适配到统一的API网关，提供专利技术分析功能
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any

from patent_search_adapter import AdapterConfig, BaseAdapter

logger = logging.getLogger(__name__)


class TechnicalAnalysisAdapter(BaseAdapter):
    """技术分析服务适配器"""

    def __init__(self, config: AdapterConfig):
        super().__init__(config)
        self.service_name = "technical-analysis-service"
        self.api_prefix = "/api/v1/technical-analysis"

        # 支持的分析类型
        self.analysis_types = {
            "novelty": "新颖性分析",
            "inventive_step": "创造性分析",
            "patentability": "可专利性分析",
            "freedom_to_operate": "自由实施分析",
            "validity": "专利有效性分析",
            "infringement": "侵权风险分析",
        }

        # 支持的数据库
        self.supported_databases = ["CN", "US", "EP", "WO", "JP", "KR", "DE", "FR", "GB", "CA"]

    async def transform_request(self, request: dict) -> dict:
        """
        将统一请求格式转换为技术分析服务格式
        """
        try:
            analysis_type = request.get("analysisType", "patentability")

            if analysis_type not in self.analysis_types:
                raise ValueError(f"Unsupported analysis type: {analysis_type}")

            # 基础专利数据映射
            patent_data = {
                "title": request.get("title", ""),
                "abstract": request.get("abstract", ""),
                "claims": request.get("claims", []),
                "technical_field": request.get("technicalField", ""),
                "technical_problem": request.get("technicalProblem", ""),
                "technical_solution": request.get("technicalSolution", ""),
                "technical_features": request.get("technicalFeatures", []),
                "invention_type": request.get("inventionType", "invention"),
            }

            # 分析选项映射
            analysis_options = {
                "depth": request.get("depth", "standard"),
                "databases": request.get("databases", self.supported_databases),
                "date_range": request.get("dateRange", {}),
                "comparison_basis": request.get("comparisonBasis", "closest_prior_art"),
                "technical_level": request.get("technicalLevel", "ordinary_skilled_person"),
                "include_novelty": request.get("includeNovelty", True),
                "include_inventive_step": request.get("includeInventiveStep", True),
                "include_industrial_applicability": request.get(
                    "includeIndustrialApplicability", True
                ),
            }

            # 根据分析类型调整请求格式
            transformed = {
                "analysis_type": analysis_type,
                "patent_data": patent_data,
                "analysis_options": analysis_options,
            }

            # 特定分析类型的额外参数
            if analysis_type == "freedom_to_operate":
                transformed["target_territories"] = request.get("targetTerritories", ["CN", "US"])
                transformed["product_features"] = request.get("productFeatures", [])

            elif analysis_type == "validity":
                transformed["challenged_claims"] = request.get("challengedClaims", [])
                transformed["invalidity_grounds"] = request.get("invalidityGrounds", [])

            elif analysis_type == "infringement":
                transformed["target_product"] = request.get("targetProduct", {})
                transformed["comparison_elements"] = request.get("comparisonElements", [])

            self.logger.debug(f"Transformed analysis request: {transformed}")
            return transformed

        except Exception as error:
            self.logger.error(f"Request transformation failed: {error}")
            raise

    async def transform_response(self, response_data: Any) -> dict:
        """
        将技术分析服务响应转换为统一格式
        """
        try:
            if isinstance(response_data, str):
                response_data = json.loads(response_data)

            if not response_data.get("success", True):
                return {
                    "success": False,
                    "error": {
                        "code": response_data.get("error_code", "ANALYSIS_ERROR"),
                        "message": response_data.get("message", "Analysis failed"),
                    },
                    "timestamp": datetime.now().isoformat(),
                }

            # 提取分析结果
            analysis_type = response_data.get("analysis_type", "unknown")
            results = response_data.get("results", {})

            # 基础响应结构
            transformed_response = {
                "success": True,
                "data": {
                    "analysisType": analysis_type,
                    "results": {
                        "confidence": results.get("confidence", 0.8),
                        "summary": results.get("summary", ""),
                        "detailed_analysis": results.get("detailed_analysis", {}),
                    },
                    "priorArt": response_data.get("prior_art_references", []),
                    "recommendations": response_data.get("recommendations", []),
                    "report": response_data.get("detailed_report", ""),
                },
                "metadata": {"adapter": self.service_name, "timestamp": datetime.now().isoformat()},
            }

            # 根据分析类型添加特定结果
            if analysis_type == "novelty":
                transformed_response["data"]["results"]["novelty"] = {
                    "is_novel": results.get("is_novel", False),
                    "novelty_score": results.get("novelty_score", 0.0),
                    "novel_features": results.get("novel_features", []),
                    "disclosing_references": results.get("disclosing_references", []),
                }

            elif analysis_type == "inventive_step":
                transformed_response["data"]["results"]["inventiveStep"] = {
                    "has_inventive_step": results.get("has_inventive_step", False),
                    "inventive_step_score": results.get("inventive_step_score", 0.0),
                    "technical_contribution": results.get("technical_contribution", ""),
                    "obviousness_reasoning": results.get("obviousness_reasoning", ""),
                    "closest_prior_art": results.get("closest_prior_art", {}),
                }

            elif analysis_type == "patentability":
                transformed_response["data"]["results"]["patentability"] = {
                    "overall_patentable": results.get("overall_patentable", False),
                    "patentability_score": results.get("patentability_score", 0.0),
                    "requirements_analysis": {
                        "novelty": results.get("novelty_analysis", {}),
                        "inventive_step": results.get("inventive_step_analysis", {}),
                        "industrial_applicability": results.get(
                            "industrial_applicability_analysis", {}
                        ),
                        "subject_matter_eligibility": results.get("subject_matter_eligibility", {}),
                    },
                }

            elif analysis_type == "freedom_to_operate":
                transformed_response["data"]["results"]["freedomToOperate"] = {
                    "can_operate_freely": results.get("can_operate_freely", False),
                    "risk_level": results.get("risk_level", "high"),
                    "blocking_patents": results.get("blocking_patents", []),
                    "risk_mitigation": results.get("risk_mitigation", []),
                }

            elif analysis_type == "validity":
                transformed_response["data"]["results"]["validity"] = {
                    "is_valid": results.get("is_valid", True),
                    "validity_score": results.get("validity_score", 0.8),
                    "invalidity_risks": results.get("invalidity_risks", []),
                    "strongest_claims": results.get("strongest_claims", []),
                    "weakest_claims": results.get("weakest_claims", []),
                }

            elif analysis_type == "infringement":
                transformed_response["data"]["results"]["infringement"] = {
                    "infringement_risk": results.get("infringement_risk", "low"),
                    "infringement_score": results.get("infringement_score", 0.0),
                    "infringing_claims": results.get("infringing_claims", []),
                    "non_infringing_claims": results.get("non_infringing_claims", []),
                    "design_around_suggestions": results.get("design_around_suggestions", []),
                }

            # 添加分析元数据
            if "analysis_metadata" in response_data:
                metadata = response_data["analysis_metadata"]
                transformed_response["metadata"].update(
                    {
                        "analysisTime": metadata.get("analysis_time", 0),
                        "databasesSearched": metadata.get("databases_searched", []),
                        "analystVersion": metadata.get("analyst_version", "1.0"),
                        "searchStrategy": metadata.get("search_strategy", ""),
                        "confidenceLevel": metadata.get("confidence_level", "medium"),
                    }
                )

            return transformed_response

        except Exception as error:
            self.logger.error(f"Response transformation failed: {error}")
            raise

    async def analyze_novelty(self, request: dict) -> dict:
        """
        新颖性分析
        """
        try:
            await self.initialize()

            # 转换请求
            analysis_request = await self.transform_request(request)
            analysis_request["analysis_type"] = "novelty"

            endpoint = f"{self.config.service_url}{self.api_prefix}/novelty"

            self.logger.info(f"Starting novelty analysis for: {request.get('title')}")

            async with self.session.post(url=endpoint, json=analysis_request) as response:
                response_data = await response.json()

                if response.status == 200:
                    return await self.transform_response(response_data)
                else:
                    return await self._handle_error(
                        Exception(f"API error: {response.status} - {response_data}")
                    )

        except Exception as error:
            return await self._handle_error(error)

    async def analyze_inventive_step(self, request: dict) -> dict:
        """
        创造性分析
        """
        try:
            await self.initialize()

            # 转换请求
            analysis_request = await self.transform_request(request)
            analysis_request["analysis_type"] = "inventive_step"

            endpoint = f"{self.config.service_url}{self.api_prefix}/inventive-step"

            self.logger.info(f"Starting inventive step analysis for: {request.get('title')}")

            async with self.session.post(url=endpoint, json=analysis_request) as response:
                response_data = await response.json()

                if response.status == 200:
                    return await self.transform_response(response_data)
                else:
                    return await self._handle_error(
                        Exception(f"API error: {response.status} - {response_data}")
                    )

        except Exception as error:
            return await self._handle_error(error)

    async def analyze_patentability(self, request: dict) -> dict:
        """
        可专利性分析
        """
        try:
            await self.initialize()

            # 转换请求
            analysis_request = await self.transform_request(request)
            analysis_request["analysis_type"] = "patentability"

            endpoint = f"{self.config.service_url}{self.api_prefix}/patentability"

            self.logger.info(f"Starting patentability analysis for: {request.get('title')}")

            async with self.session.post(url=endpoint, json=analysis_request) as response:
                response_data = await response.json()

                if response.status == 200:
                    return await self.transform_response(response_data)
                else:
                    return await self._handle_error(
                        Exception(f"API error: {response.status} - {response_data}")
                    )

        except Exception as error:
            return await self._handle_error(error)

    async def analyze_freedom_to_operate(self, request: dict) -> dict:
        """
        自由实施分析
        """
        try:
            await self.initialize()

            # 转换请求
            analysis_request = await self.transform_request(request)
            analysis_request["analysis_type"] = "freedom_to_operate"

            endpoint = f"{self.config.service_url}{self.api_prefix}/freedom-to-operate"

            self.logger.info(f"Starting FTO analysis for: {request.get('title')}")

            async with self.session.post(url=endpoint, json=analysis_request) as response:
                response_data = await response.json()

                if response.status == 200:
                    return await self.transform_response(response_data)
                else:
                    return await self._handle_error(
                        Exception(f"API error: {response.status} - {response_data}")
                    )

        except Exception as error:
            return await self._handle_error(error)

    async def analyze_validity(self, request: dict) -> dict:
        """
        专利有效性分析
        """
        try:
            await self.initialize()

            # 转换请求
            analysis_request = await self.transform_request(request)
            analysis_request["analysis_type"] = "validity"

            endpoint = f"{self.config.service_url}{self.api_prefix}/validity"

            self.logger.info(f"Starting validity analysis for: {request.get('title')}")

            async with self.session.post(url=endpoint, json=analysis_request) as response:
                response_data = await response.json()

                if response.status == 200:
                    return await self.transform_response(response_data)
                else:
                    return await self._handle_error(
                        Exception(f"API error: {response.status} - {response_data}")
                    )

        except Exception as error:
            return await self._handle_error(error)

    async def analyze_infringement(self, request: dict) -> dict:
        """
        侵权风险分析
        """
        try:
            await self.initialize()

            # 转换请求
            analysis_request = await self.transform_request(request)
            analysis_request["analysis_type"] = "infringement"

            endpoint = f"{self.config.service_url}{self.api_prefix}/infringement"

            self.logger.info(f"Starting infringement analysis for: {request.get('title')}")

            async with self.session.post(url=endpoint, json=analysis_request) as response:
                response_data = await response.json()

                if response.status == 200:
                    return await self.transform_response(response_data)
                else:
                    return await self._handle_error(
                        Exception(f"API error: {response.status} - {response_data}")
                    )

        except Exception as error:
            return await self._handle_error(error)

    async def get_analysis_status(self, request: dict) -> dict:
        """
        获取分析状态
        """
        try:
            await self.initialize()

            analysis_id = request.get("analysisId")
            if not analysis_id:
                return await self._handle_error(Exception("Analysis ID is required"))

            endpoint = f"{self.config.service_url}{self.api_prefix}/analysis/{analysis_id}/status"

            async with self.session.get(url=endpoint) as response:
                response_data = await response.json()

                if response.status == 200:
                    return {
                        "success": True,
                        "data": {
                            "analysisId": response_data.get("analysis_id"),
                            "status": response_data.get(
                                "status"
                            ),  # pending, running, completed, failed
                            "progress": response_data.get("progress", 0),
                            "startedAt": response_data.get("started_at"),
                            "estimatedCompletion": response_data.get("estimated_completion"),
                            "error": response_data.get("error"),
                        },
                        "metadata": {
                            "adapter": self.service_name,
                            "timestamp": datetime.now().isoformat(),
                        },
                    }
                else:
                    return await self._handle_error(
                        Exception(f"API error: {response.status} - {response_data}")
                    )

        except Exception as error:
            return await self._handle_error(error)

    async def get_analysis_result(self, request: dict) -> dict:
        """
        获取分析结果
        """
        try:
            await self.initialize()

            analysis_id = request.get("analysisId")
            if not analysis_id:
                return await self._handle_error(Exception("Analysis ID is required"))

            endpoint = f"{self.config.service_url}{self.api_prefix}/analysis/{analysis_id}/result"

            async with self.session.get(url=endpoint) as response:
                response_data = await response.json()

                if response.status == 200:
                    return await self.transform_response(response_data)
                else:
                    return await self._handle_error(
                        Exception(f"API error: {response.status} - {response_data}")
                    )

        except Exception as error:
            return await self._handle_error(error)

    async def get_supported_databases(self, request: dict) -> dict:
        """
        获取支持的数据库列表
        """
        try:
            await self.initialize()

            endpoint = f"{self.config.service_url}{self.api_prefix}/databases"

            async with self.session.get(url=endpoint) as response:
                response_data = await response.json()

                if response.status == 200:
                    return {
                        "success": True,
                        "data": {
                            "databases": response_data.get("databases", self.supported_databases),
                            "default_databases": response_data.get(
                                "default_databases", ["CN", "US", "EP", "WO"]
                            ),
                            "database_info": response_data.get("database_info", {}),
                        },
                        "metadata": {
                            "adapter": self.service_name,
                            "timestamp": datetime.now().isoformat(),
                        },
                    }
                else:
                    return await self._handle_error(Exception(f"API error: {response.status}"))

        except Exception as error:
            return await self._handle_error(error)

    async def get_analysis_templates(self, request: dict) -> dict:
        """
        获取分析模板
        """
        try:
            await self.initialize()

            params = {
                "analysis_type": request.get("analysisType"),
                "jurisdiction": request.get("jurisdiction", "CN"),
            }

            endpoint = f"{self.config.service_url}{self.api_prefix}/templates"

            async with self.session.get(url=endpoint, params=params) as response:
                response_data = await response.json()

                if response.status == 200:
                    return {
                        "success": True,
                        "data": {
                            "templates": response_data.get("templates", []),
                            "default_template": response_data.get("default_template"),
                            "template_categories": response_data.get("template_categories", []),
                        },
                        "metadata": {
                            "adapter": self.service_name,
                            "timestamp": datetime.now().isoformat(),
                        },
                    }
                else:
                    return await self._handle_error(Exception(f"API error: {response.status}"))

        except Exception as error:
            return await self._handle_error(error)


# 注册适配器
from patent_search_adapter import AdapterFactory

AdapterFactory.register("technical-analysis", TechnicalAnalysisAdapter)


# 使用示例
async def test_technical_analysis_adapter():
    """测试技术分析适配器"""
    config = {
        "technical-analysis": {
            "service_url": "http://localhost:8053",
            "health_threshold": 10000,
            "timeout": 120000,
            "retry_attempts": 2,
            "debug_mode": True,
        }
    }

    from patent_search_adapter import AdapterManager

    manager = AdapterManager(config)
    await manager.initialize()

    try:
        adapter = await manager.get_adapter("technical-analysis")

        # 健康检查
        health = await adapter.health_check()
        print(f"Health status: {health}")

        # 测试可专利性分析
        patentability_request = {
            "title": "基于机器学习的专利分析系统",
            "abstract": "一种使用机器学习技术分析专利文档的系统和方法",
            "claims": [
                "一种专利分析方法，包括：获取专利文档；使用机器学习模型分析所述专利文档的特征；生成分析报告。",
                "根据权利要求1所述的方法，其中所述机器学习模型包括深度神经网络。",
            ],
            "technicalField": "人工智能",
            "technicalProblem": "传统专利分析方法效率低下",
            "technicalSolution": "使用机器学习技术提高分析效率",
            "technicalFeatures": ["机器学习模型", "专利特征提取", "自动化分析"],
            "inventionType": "invention",
            "depth": "standard",
            "databases": ["CN", "US", "EP"],
            "includeNovelty": True,
            "includeInventiveStep": True,
            "includeIndustrialApplicability": True,
        }

        result = await adapter.analyze_patentability(patentability_request)
        print(f"Patentability analysis result: {json.dumps(result, indent=2, ensure_ascii=False)}")

    finally:
        await manager.cleanup()


if __name__ == "__main__":
    asyncio.run(test_technical_analysis_adapter())
