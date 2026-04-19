"""
专利检索服务适配器
将外部专利搜索服务接口适配到统一的API网关
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import aiohttp

# 配置日志
logger = logging.getLogger(__name__)


@dataclass
class AdapterConfig:
    """适配器配置"""

    service_url: str
    health_threshold: int = 5000  # ms
    timeout: int = 30000  # ms
    retry_attempts: int = 3
    debug_mode: bool = False
    circuit_breaker: dict | None = None


@dataclass
class HealthStatus:
    """健康状态"""

    status: str  # 'healthy' | 'degraded' | 'unhealthy'
    timestamp: str
    details: dict | None = None


@dataclass
class ErrorResponse:
    """错误响应"""

    success: bool = False
    error: dict = None
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        if self.error is None:
            self.error = {}


class BaseAdapter:
    """适配器基类"""

    def __init__(self, config: AdapterConfig):
        self.config = config
        self.name = self.__class__.__name__
        self.version = "1.0.0"
        self.session = None
        self.logger = logging.getLogger(self.name)

    async def initialize(self):
        """初始化适配器"""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout / 1000)
            self.session = aiohttp.ClientSession(timeout=timeout)

    async def cleanup(self):
        """清理资源"""
        if self.session:
            await self.session.close()
            self.session = None

    @property
    def get_name(self) -> str:
        return self.name

    @property
    def get_version(self) -> str:
        return self.version

    async def health_check(self) -> HealthStatus:
        """健康检查"""
        try:
            if not self.session:
                await self.initialize()

            start_time = datetime.now()
            async with self.session.get(f"{self.config.service_url}/health") as response:
                if response.status == 200:
                    duration = (datetime.now() - start_time).total_seconds() * 1000
                    status = "healthy" if duration < self.config.health_threshold else "degraded"

                    return HealthStatus(
                        status=status,
                        timestamp=datetime.now().isoformat(),
                        details={"response_time": duration, "http_status": response.status},
                    )
                else:
                    return HealthStatus(
                        status="unhealthy",
                        timestamp=datetime.now().isoformat(),
                        details={"http_status": response.status, "error": "Health check failed"},
                    )
        except Exception as error:
            return HealthStatus(
                status="unhealthy",
                timestamp=datetime.now().isoformat(),
                details={"error": str(error)},
            )

    async def _handle_error(self, error: Exception) -> ErrorResponse:
        """统一错误处理"""
        self.logger.error(f"Adapter error: {error}", exc_info=True)

        return ErrorResponse(
            error={
                "code": "ADAPTER_ERROR",
                "message": str(error),
                "details": error.__dict__ if self.config.debug_mode else None,
            },
            timestamp=datetime.now().isoformat(),
        )

    async def ping_service(self):
        """ping服务检查"""
        response = await self.session.get(f"{self.config.service_url}/health")
        if not response.ok:
            raise Exception(f"Health check failed: {response.status}")
        return await response.json()


class PatentSearchAdapter(BaseAdapter):
    """专利检索服务适配器"""

    def __init__(self, config: AdapterConfig):
        super().__init__(config)
        self.service_name = "patent-search-adapter"
        self.api_prefix = "/api/v2/patent"

    async def transform_request(self, request: dict) -> dict:
        """
        将统一请求格式转换为外部专利搜索服务格式
        """
        try:
            # 基础字段映射
            transformed = {
                "title": request.get("query", ""),
                "abstract": request.get("description", ""),
                "technical_field": request.get("category", ""),
                "patent_id": request.get("patentId"),
                "type": request.get("type", "invention"),
            }

            # 搜索参数映射
            if "filters" in request:
                filters = request["filters"]
                if "publicationDate" in filters:
                    pub_date = filters["publicationDate"]
                    transformed["publication_date_from"] = pub_date.get("from")
                    transformed["publication_date_to"] = pub_date.get("to")

                if "applicants" in filters:
                    transformed["applicants"] = filters["applicants"]

                if "inventors" in filters:
                    transformed["inventors"] = filters["inventors"]

                if "classification" in filters:
                    transformed["classification"] = filters["classification"]

            # 分页参数
            transformed["limit"] = request.get("limit", 20)
            transformed["offset"] = request.get("offset", 0)

            # 排序参数
            sort_mapping = {
                "relevance": "relevance",
                "date": "publication_date",
                "applicant": "applicant_name",
            }
            transformed["sort_by"] = sort_mapping.get(
                request.get("sortBy", "relevance"), "relevance"
            )

            self.logger.debug(f"Transformed request: {transformed}")
            return transformed

        except Exception as error:
            self.logger.error(f"Request transformation failed: {error}")
            raise

    async def transform_response(self, response_data: Any) -> dict:
        """
        将外部专利搜索服务响应转换为统一格式
        """
        try:
            if isinstance(response_data, str):
                response_data = json.loads(response_data)

            # 如果是分析结果，直接返回
            if "analysis" in response_data or "report" in response_data:
                return {
                    "success": True,
                    "data": response_data,
                    "metadata": {
                        "adapter": self.service_name,
                        "timestamp": datetime.now().isoformat(),
                        "version": self.version,
                    },
                }

            # 处理搜索结果
            patents = []
            if "results" in response_data:
                patents = [
                    {
                        "id": patent.get("patent_id"),
                        "title": patent.get("title", ""),
                        "abstract": patent.get("abstract", ""),
                        "publicationDate": patent.get("publication_date"),
                        "applicants": patent.get("applicants", []),
                        "inventors": patent.get("inventors", []),
                        "classification": patent.get("classification", {}),
                        "similarityScore": patent.get("similarity_score"),
                        "relevanceScore": patent.get("relevance_score", 0.8),
                    }
                    for patent in response_data["results"]
                ]

            return {
                "success": True,
                "data": {
                    "patents": patents,
                    "total": response_data.get("total_count", 0),
                    "page": response_data.get("page", 1),
                    "pageSize": response_data.get("limit", 20),
                },
                "metadata": {
                    "query": response_data.get("query"),
                    "searchTime": response_data.get("search_time"),
                    "sources": response_data.get("sources", ["patent-search"]),
                    "adapter": self.service_name,
                    "timestamp": datetime.now().isoformat(),
                },
            }

        except Exception as error:
            self.logger.error(f"Response transformation failed: {error}")
            raise

    async def search_patents(self, request: dict) -> dict:
        """
        专利搜索接口
        """
        try:
            await self.initialize()

            # 转换请求
            patent_request = await self.transform_request(request)

            # 发送请求到外部专利搜索服务
            self.logger.info(f"Searching patents with query: {request.get('query')}")

            # 根据请求类型选择不同的端点
            if "analysis_type" in request:
                # 分析请求
                endpoint = f"{self.config.service_url}{self.api_prefix}/analyze"
                method = "POST"
                payload = patent_request
            else:
                # 搜索请求
                endpoint = f"{self.config.service_url}{self.api_prefix}/search"
                method = "GET"
                payload = None

            async with self.session.request(
                method=method,
                url=endpoint,
                json=payload,
                params=patent_request if method == "GET" else None,
            ) as response:
                response_data = await response.json()

                if response.status == 200:
                    return await self.transform_response(response_data)
                else:
                    return await self._handle_error(
                        Exception(f"API error: {response.status} - {response_data}")
                    )

        except Exception as error:
            return await self._handle_error(error)

    async def analyze_patent(self, request: dict) -> dict:
        """
        专利分析接口
        """
        try:
            await self.initialize()

            # 转换请求
            patent_request = await self.transform_request(request)
            patent_request["analysis_type"] = request.get("analysisType", "patentability")

            # 发送分析请求
            endpoint = f"{self.config.service_url}{self.api_prefix}/analyze"

            self.logger.info(f"Analyzing patent: {request.get('patentId')}")

            async with self.session.post(url=endpoint, json=patent_request) as response:
                response_data = await response.json()

                if response.status == 200:
                    return await self.transform_response(response_data)
                else:
                    return await self._handle_error(
                        Exception(f"API error: {response.status} - {response_data}")
                    )

        except Exception as error:
            return await self._handle_error(error)

    async def get_patent_rules(self, request: dict) -> dict:
        """
        获取专利规则
        """
        try:
            await self.initialize()

            params = {}
            if request.get("category"):
                params["category"] = request["category"]
            if request.get("keyword"):
                params["keyword"] = request["keyword"]

            endpoint = f"{self.config.service_url}{self.api_prefix}/rules"

            async with self.session.get(url=endpoint, params=params) as response:
                response_data = await response.json()

                if response.status == 200:
                    return {
                        "success": True,
                        "data": response_data,
                        "metadata": {
                            "adapter": self.service_name,
                            "timestamp": datetime.now().isoformat(),
                        },
                    }
                else:
                    return await self._handle_error(Exception(f"API error: {response.status}"))

        except Exception as error:
            return await self._handle_error(error)

    async def chat_with_agent(self, request: dict) -> dict:
        """
        与AI智能体对话
        """
        try:
            await self.initialize()

            chat_request = {
                "message": request.get("message"),
                "user_id": request.get("userId", "default"),
                "case_id": request.get("caseId"),
            }

            endpoint = f"{self.config.service_url}{self.api_prefix}/chat"

            async with self.session.post(url=endpoint, json=chat_request) as response:
                response_data = await response.json()

                if response.status == 200:
                    return {
                        "success": True,
                        "data": {
                            "response": response_data.get("response"),
                            "confidence": response_data.get("confidence", 0.0),
                            "actions": response_data.get("actions", []),
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

    async def optimize_claim(self, request: dict) -> dict:
        """
        优化权利要求
        """
        try:
            await self.initialize()

            optimize_request = {
                "original_claim": request.get("originalClaim"),
                "optimization_type": request.get("optimizationType", "broaden"),
            }

            endpoint = f"{self.config.service_url}{self.api_prefix}/optimize_claim"

            async with self.session.post(url=endpoint, json=optimize_request) as response:
                response_data = await response.json()

                if response.status == 200:
                    return {
                        "success": True,
                        "data": response_data.get("result"),
                        "metadata": {
                            "adapter": self.service_name,
                            "timestamp": datetime.now().isoformat(),
                        },
                    }
                else:
                    return await self._handle_error(Exception(f"API error: {response.status}"))

        except Exception as error:
            return await self._handle_error(error)


# 适配器工厂
class AdapterFactory:
    """适配器工厂"""

    _adapters = {}

    @classmethod
    def register(cls, name: str, adapter_class):
        """注册适配器"""
        cls._adapters[name] = adapter_class

    @classmethod
    def create(cls, name: str, config: AdapterConfig):
        """创建适配器实例"""
        if name not in cls._adapters:
            raise ValueError(f"Adapter not found: {name}")

        adapter_class = cls._adapters[name]
        return adapter_class(config)

    @classmethod
    def get_available_adapters(cls) -> list[str]:
        """获取可用适配器列表"""
        return list(cls._adapters.keys())


# 注册适配器
AdapterFactory.register("patent-search", PatentSearchAdapter)


# 适配器管理器
class AdapterManager:
    """适配器管理器"""

    def __init__(self, config: dict):
        self.config = config
        self.adapters = {}
        self.logger = logging.getLogger(self.__class__.__name__)

    async def initialize(self):
        """初始化所有适配器"""
        for name, adapter_config in self.config.items():
            config = AdapterConfig(**adapter_config)
            adapter = AdapterFactory.create(name, config)
            await adapter.initialize()
            self.adapters[name] = adapter

        self.logger.info(f"Initialized {len(self.adapters)} adapters")

    async def cleanup(self):
        """清理所有适配器"""
        for adapter in self.adapters.values():
            await adapter.cleanup()
        self.adapters.clear()

    async def get_adapter(self, name: str):
        """获取适配器"""
        if name not in self.adapters:
            raise ValueError(f"Adapter not found: {name}")
        return self.adapters[name]

    async def health_check_all(self) -> dict[str, HealthStatus]:
        """检查所有适配器健康状态"""
        results = {}
        for name, adapter in self.adapters.items():
            try:
                results[name] = await adapter.health_check()
            except Exception as error:
                results[name] = HealthStatus(
                    status="unhealthy",
                    timestamp=datetime.now().isoformat(),
                    details={"error": str(error)},
                )
        return results


# 使用示例
async def main():
    """测试适配器"""
    config = {
        "patent-search": {
            "service_url": "http://localhost:8050",
            "health_threshold": 5000,
            "timeout": 30000,
            "retry_attempts": 3,
            "debug_mode": True,
        }
    }

    manager = AdapterManager(config)
    await manager.initialize()

    try:
        # 获取适配器
        adapter = await manager.get_adapter("patent-search")

        # 健康检查
        health = await adapter.health_check()
        print(f"Health status: {health}")

        # 搜索专利
        search_request = {"query": "人工智能", "limit": 10, "offset": 0}

        result = await adapter.search_patents(search_request)
        print(f"Search result: {json.dumps(result, indent=2, ensure_ascii=False)}")

    finally:
        await manager.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
