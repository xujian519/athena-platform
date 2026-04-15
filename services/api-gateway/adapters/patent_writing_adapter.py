"""
专利撰写服务适配器
将专利撰写服务适配到统一的API网关
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any

from patent_search_adapter import AdapterConfig, BaseAdapter

logger = logging.getLogger(__name__)


class PatentWritingAdapter(BaseAdapter):
    """专利撰写服务适配器"""

    def __init__(self, config: AdapterConfig):
        super().__init__(config)
        self.service_name = "patent-writing-service"
        self.api_prefix = "/api/v1/patent-writing"
        self.workflow_states = ["drafting", "review", "revision", "finalization", "completed"]

    async def transform_request(self, request: dict) -> dict:
        """
        将统一请求格式转换为专利撰写服务格式
        """
        try:
            # 基础映射
            transformed = {
                "title": request.get("title", ""),
                "invention_type": request.get("inventionType", "invention"),
                "technical_features": request.get("technicalFeatures", []),
                "technical_field": request.get("technicalField", ""),
                "technical_problem": request.get("technicalProblem", ""),
                "technical_solution": request.get("technicalSolution", ""),
                "claim_type": request.get("claimType", "apparatus"),
                "language": request.get("language", "zh-CN"),
                "jurisdiction": request.get("jurisdiction", "CN"),
            }

            # 选项映射
            options = {}
            if "includeDrawings" in request:
                options["include_drawings"] = request["includeDrawings"]
            if "includeExamples" in request:
                options["include_examples"] = request["includeExamples"]
            if "detailLevel" in request:
                options["detail_level"] = request["detailLevel"]

            if options:
                transformed["options"] = options

            # 如果有案卷ID，包含在工作流数据中
            if "caseId" in request:
                transformed["case_id"] = request["caseId"]

            self.logger.debug(f"Transformed writing request: {transformed}")
            return transformed

        except Exception as error:
            self.logger.error(f"Request transformation failed: {error}")
            raise

    async def transform_response(self, response_data: Any) -> dict:
        """
        将专利撰写服务响应转换为统一格式
        """
        try:
            if isinstance(response_data, str):
                response_data = json.loads(response_data)

            # 处理工作流响应
            if "workflow_id" in response_data:
                return {
                    "success": True,
                    "data": {
                        "patentId": response_data.get("patent_id", str(uuid.uuid4())),
                        "title": response_data.get("title", ""),
                        "status": response_data.get("status", "drafting"),
                        "workflowId": response_data.get("workflow_id"),
                        "nextSteps": response_data.get("next_steps", []),
                    },
                    "workflow": {
                        "workflowId": response_data.get("workflow_id"),
                        "status": response_data.get("status"),
                        "nextSteps": response_data.get("next_steps", []),
                        "createdAt": response_data.get("created_at"),
                        "updatedAt": response_data.get("updated_at"),
                    },
                    "metadata": {
                        "adapter": self.service_name,
                        "timestamp": datetime.now().isoformat(),
                        "version": self.version,
                    },
                }

            # 处理完整专利文档响应
            if "claims" in response_data and "description" in response_data:
                return {
                    "success": True,
                    "data": {
                        "patentId": response_data.get("patent_id", str(uuid.uuid4())),
                        "title": response_data.get("title", ""),
                        "abstract": response_data.get("abstract", ""),
                        "description": response_data.get("description", ""),
                        "claims": response_data.get("claims", []),
                        "drawings": response_data.get("drawings", []),
                        "examples": response_data.get("examples", []),
                        "metadata": {
                            "generatedAt": response_data.get(
                                "generated_at", datetime.now().isoformat()
                            ),
                            "version": response_data.get("version", "1.0"),
                            "language": response_data.get("language", "zh-CN"),
                            "jurisdiction": response_data.get("jurisdiction", "CN"),
                        },
                    },
                    "metadata": {
                        "adapter": self.service_name,
                        "timestamp": datetime.now().isoformat(),
                    },
                }

            # 处理部分生成响应
            return {
                "success": True,
                "data": response_data,
                "metadata": {"adapter": self.service_name, "timestamp": datetime.now().isoformat()},
            }

        except Exception as error:
            self.logger.error(f"Response transformation failed: {error}")
            raise

    async def create_draft(self, request: dict) -> dict:
        """
        创建专利草稿
        """
        try:
            await self.initialize()

            # 转换请求
            writing_request = await self.transform_request(request)
            writing_request["action"] = "create_draft"

            endpoint = f"{self.config.service_url}{self.api_prefix}/draft"

            self.logger.info(f"Creating patent draft: {request.get('title')}")

            async with self.session.post(url=endpoint, json=writing_request) as response:
                response_data = await response.json()

                if response.status == 200:
                    return await self.transform_response(response_data)
                else:
                    return await self._handle_error(
                        Exception(f"API error: {response.status} - {response_data}")
                    )

        except Exception as error:
            return await self._handle_error(error)

    async def generate_claims(self, request: dict) -> dict:
        """
        生成权利要求
        """
        try:
            await self.initialize()

            writing_request = await self.transform_request(request)
            writing_request["action"] = "generate_claims"

            endpoint = f"{self.config.service_url}{self.api_prefix}/claims/generate"

            self.logger.info(f"Generating claims for patent: {request.get('title')}")

            async with self.session.post(url=endpoint, json=writing_request) as response:
                response_data = await response.json()

                if response.status == 200:
                    return await self.transform_response(response_data)
                else:
                    return await self._handle_error(
                        Exception(f"API error: {response.status} - {response_data}")
                    )

        except Exception as error:
            return await self._handle_error(error)

    async def generate_description(self, request: dict) -> dict:
        """
        生成说明书
        """
        try:
            await self.initialize()

            writing_request = await self.transform_request(request)
            writing_request["action"] = "generate_description"

            endpoint = f"{self.config.service_url}{self.api_prefix}/description/generate"

            self.logger.info(f"Generating description for patent: {request.get('title')}")

            async with self.session.post(url=endpoint, json=writing_request) as response:
                response_data = await response.json()

                if response.status == 200:
                    return await self.transform_response(response_data)
                else:
                    return await self._handle_error(
                        Exception(f"API error: {response.status} - {response_data}")
                    )

        except Exception as error:
            return await self._handle_error(error)

    async def optimize_content(self, request: dict) -> dict:
        """
        优化专利内容
        """
        try:
            await self.initialize()

            optimize_request = {
                "patent_id": request.get("patentId"),
                "content_type": request.get(
                    "contentType", "claims"
                ),  # claims, description, abstract
                "optimization_type": request.get(
                    "optimizationType", "broaden"
                ),  # broaden, narrow, clarify
                "target_section": request.get("targetSection"),
                "suggestions": request.get("suggestions", []),
            }

            endpoint = f"{self.config.service_url}{self.api_prefix}/optimize"

            self.logger.info(f"Optimizing patent content: {request.get('patentId')}")

            async with self.session.post(url=endpoint, json=optimize_request) as response:
                response_data = await response.json()

                if response.status == 200:
                    return {
                        "success": True,
                        "data": {
                            "optimizedContent": response_data.get("optimized_content"),
                            "changes": response_data.get("changes", []),
                            "suggestions": response_data.get("suggestions", []),
                            "confidence": response_data.get("confidence", 0.8),
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

    async def check_compliance(self, request: dict) -> dict:
        """
        检查专利合规性
        """
        try:
            await self.initialize()

            compliance_request = {
                "patent_id": request.get("patentId"),
                "content": request.get("content"),
                "check_types": request.get("checkTypes", ["format", "claim_structure", "language"]),
                "jurisdiction": request.get("jurisdiction", "CN"),
            }

            endpoint = f"{self.config.service_url}{self.api_prefix}/compliance/check"

            self.logger.info(f"Checking compliance for patent: {request.get('patentId')}")

            async with self.session.post(url=endpoint, json=compliance_request) as response:
                response_data = await response.json()

                if response.status == 200:
                    return {
                        "success": True,
                        "data": {
                            "complianceScore": response_data.get("compliance_score", 0.0),
                            "issues": response_data.get("issues", []),
                            "suggestions": response_data.get("suggestions", []),
                            "passedChecks": response_data.get("passed_checks", []),
                            "failedChecks": response_data.get("failed_checks", []),
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

    async def get_workflow_status(self, request: dict) -> dict:
        """
        获取工作流状态
        """
        try:
            await self.initialize()

            workflow_id = request.get("workflowId")
            if not workflow_id:
                return await self._handle_error(Exception("Workflow ID is required"))

            endpoint = f"{self.config.service_url}{self.api_prefix}/workflow/{workflow_id}/status"

            async with self.session.get(url=endpoint) as response:
                response_data = await response.json()

                if response.status == 200:
                    return {
                        "success": True,
                        "data": {
                            "workflowId": response_data.get("workflow_id"),
                            "status": response_data.get("status"),
                            "currentStep": response_data.get("current_step"),
                            "progress": response_data.get("progress", 0),
                            "nextSteps": response_data.get("next_steps", []),
                            "completedSteps": response_data.get("completed_steps", []),
                            "errors": response_data.get("errors", []),
                            "createdAt": response_data.get("created_at"),
                            "updatedAt": response_data.get("updated_at"),
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

    async def update_workflow(self, request: dict) -> dict:
        """
        更新工作流
        """
        try:
            await self.initialize()

            workflow_id = request.get("workflowId")
            if not workflow_id:
                return await self._handle_error(Exception("Workflow ID is required"))

            update_request = {
                "action": request.get("action"),  # approve, reject, request_revision, complete
                "comments": request.get("comments", ""),
                "modifications": request.get("modifications", {}),
                "next_step": request.get("nextStep"),
            }

            endpoint = f"{self.config.service_url}{self.api_prefix}/workflow/{workflow_id}/update"

            self.logger.info(f"Updating workflow: {workflow_id}")

            async with self.session.post(url=endpoint, json=update_request) as response:
                response_data = await response.json()

                if response.status == 200:
                    return {
                        "success": True,
                        "data": {
                            "workflowId": response_data.get("workflow_id"),
                            "status": response_data.get("status"),
                            "nextSteps": response_data.get("next_steps", []),
                            "message": response_data.get(
                                "message", "Workflow updated successfully"
                            ),
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

    async def export_patent(self, request: dict) -> dict:
        """
        导出专利文档
        """
        try:
            await self.initialize()

            export_request = {
                "patent_id": request.get("patentId"),
                "format": request.get("format", "pdf"),  # pdf, docx, html
                "sections": request.get("sections", ["all"]),  # all, claims, description, abstract
                "language": request.get("language", "zh-CN"),
                "template": request.get("template", "standard"),
            }

            endpoint = f"{self.config.service_url}{self.api_prefix}/export"

            self.logger.info(f"Exporting patent: {request.get('patentId')}")

            async with self.session.post(url=endpoint, json=export_request) as response:
                if response.status == 200:
                    # 如果是文件下载
                    content_type = response.headers.get("Content-Type", "")
                    if (
                        "application/pdf" in content_type
                        or "application/vnd.openxmlformats" in content_type
                    ):
                        file_content = await response.read()
                        return {
                            "success": True,
                            "data": {
                                "fileContent": file_content.hex(),  # 转换为hex字符串传输
                                "fileName": f"patent_{request.get('patentId')}.{export_request['format']}",
                                "contentType": content_type,
                                "fileSize": len(file_content),
                            },
                            "metadata": {
                                "adapter": self.service_name,
                                "timestamp": datetime.now().isoformat(),
                            },
                        }
                    else:
                        response_data = await response.json()
                        return await self.transform_response(response_data)
                else:
                    return await self._handle_error(Exception(f"API error: {response.status}"))

        except Exception as error:
            return await self._handle_error(error)

    async def get_templates(self, request: dict) -> dict:
        """
        获取专利模板
        """
        try:
            await self.initialize()

            params = {
                "jurisdiction": request.get("jurisdiction", "CN"),
                "patent_type": request.get("patentType", "invention"),
                "language": request.get("language", "zh-CN"),
            }

            endpoint = f"{self.config.service_url}{self.api_prefix}/templates"

            async with self.session.get(url=endpoint, params=params) as response:
                response_data = await response.json()

                if response.status == 200:
                    return {
                        "success": True,
                        "data": {
                            "templates": response_data.get("templates", []),
                            "defaultTemplate": response_data.get("default_template"),
                            "categories": response_data.get("categories", []),
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

AdapterFactory.register("patent-writing", PatentWritingAdapter)


# 使用示例
async def test_patent_writing_adapter():
    """测试专利撰写适配器"""
    config = {
        "patent-writing": {
            "service_url": "http://localhost:8051",
            "health_threshold": 8000,
            "timeout": 60000,
            "retry_attempts": 2,
            "debug_mode": True,
        }
    }

    from patent_search_adapter import AdapterManager

    manager = AdapterManager(config)
    await manager.initialize()

    try:
        adapter = await manager.get_adapter("patent-writing")

        # 健康检查
        health = await adapter.health_check()
        print(f"Health status: {health}")

        # 创建专利草稿
        draft_request = {
            "title": "基于人工智能的专利撰写系统",
            "inventionType": "invention",
            "technicalFeatures": ["人工智能算法", "自然语言处理", "专利模板引擎"],
            "technicalField": "计算机软件",
            "technicalProblem": "传统专利撰写效率低下",
            "technicalSolution": "使用AI技术自动生成专利文档",
            "claimType": "method",
            "language": "zh-CN",
            "jurisdiction": "CN",
            "includeExamples": True,
            "detailLevel": "standard",
        }

        result = await adapter.create_draft(draft_request)
        print(f"Create draft result: {json.dumps(result, indent=2, ensure_ascii=False)}")

    finally:
        await manager.cleanup()


if __name__ == "__main__":
    asyncio.run(test_patent_writing_adapter())
