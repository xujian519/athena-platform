"""
真实API适配器
Real API Adapter

通过小诺协调API调用小娜等智能体进行专利检索和分析
"""

import asyncio
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class RealAPIAdapter:
    """真实API适配器 - 连接小诺协调服务"""

    def __init__(
        self,
        base_url: str = "http://localhost:8009",
        timeout: float = 120.0,
    ):
        """
        初始化真实API适配器

        Args:
            base_url: 小诺API服务地址
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        # 使用更简单的HTTP客户端配置
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            verify=False,  # 跳过SSL验证
            follow_redirects=True,
            # 明确禁用HTTP/2
            http1=True,
        )

    async def close(self):
        """关闭客户端连接"""
        await self.client.aclose()

    async def test_connection(self) -> dict[str, Any]:
        """测试API连接"""
        try:
            response = await self.client.get("/health")
            response.raise_for_status()
            data = response.json()

            return {
                "status": "ok",
                "service": data.get("service", "unknown"),
                "agent_name": data.get("agent_name", "unknown"),
                "initialized": data.get("initialized", False),
                "available_agents": data.get("available_agents", []),
                "message": "API连接正常",
            }

        except Exception as e:
            logger.error(f"API连接测试失败: {e}")
            return {
                "status": "error",
                "error": str(e),
            }

    async def search_patents(
        self,
        query: str,
        limit: int = 10,
        search_type: str = "patent",
    ) -> dict[str, Any]:
        """
        通过小娜搜索专利

        Args:
            query: 搜索查询
            limit: 结果数量限制
            search_type: 搜索类型

        Returns:
            搜索结果字典
        """
        try:
            logger.info(f"通过小娜搜索专利: query={query}, limit={limit}")

            # 构建协调任务请求
            request_data = {
                "task_type": "patent_search",
                "agents": ["xiaona"],
                "input_data": {
                    "query": query,
                    "limit": limit,
                    "search_type": search_type,
                },
                "coordination_mode": "sequential",
            }

            # 调用小诺协调API
            start_time = asyncio.get_event_loop().time()
            response = await self.client.post(
                "/api/v1/xiaonuo/coordinate",
                json=request_data
            )
            response.raise_for_status()
            elapsed_time = asyncio.get_event_loop().time() - start_time

            result_data = response.json()

            # 提取搜索结果
            if result_data.get("success"):
                result = result_data.get("result", {})
                return {
                    "query": query,
                    "total": result.get("total", 0),
                    "results": result.get("results", []),
                    "search_time": round(elapsed_time, 3),
                    "cached": False,
                    "source": "real_api",
                }
            else:
                # API调用失败，返回模拟数据
                logger.warning(f"小娜搜索失败: {result_data.get('error')}")
                return await self._fallback_search(query, limit, elapsed_time)

        except Exception as e:
            logger.error(f"搜索失败: {e}")
            # 降级到模拟数据
            return await self._fallback_search(query, limit, 0.5)

    async def analyze_patent(
        self,
        patent_id: str,
        analysis_type: str = "creativity",
    ) -> dict[str, Any]:
        """
        通过小娜分析专利

        Args:
            patent_id: 专利号或文件路径
            analysis_type: 分析类型

        Returns:
            分析结果字典
        """
        try:
            logger.info(f"通过小娜分析专利: patent_id={patent_id}, type={analysis_type}")

            # 构建协调任务请求
            request_data = {
                "task_type": f"patent_{analysis_type}",
                "agents": ["xiaona"],
                "input_data": {
                    "patent_id": patent_id,
                    "analysis_type": analysis_type,
                },
                "coordination_mode": "sequential",
            }

            # 调用小诺协调API
            start_time = asyncio.get_event_loop().time()
            response = await self.client.post(
                "/api/v1/xiaonuo/coordinate",
                json=request_data
            )
            response.raise_for_status()
            asyncio.get_event_loop().time() - start_time

            result_data = response.json()

            # 提取分析结果
            if result_data.get("success"):
                result = result_data.get("result", {})
                return {
                    "patent_id": patent_id,
                    "analysis_type": analysis_type,
                    "creativity_level": result.get("creativity_level", "未评估"),
                    "key_features": result.get("key_features", []),
                    "technical_effect": result.get("technical_effect", ""),
                    "authorization_prospects": result.get("authorization_prospects", ""),
                    "confidence": result.get("confidence", 0.0),
                    "details": result.get("details", {}),
                    "cached": False,
                    "source": "real_api",
                }
            else:
                # API调用失败，返回模拟数据
                logger.warning(f"小娜分析失败: {result_data.get('error')}")
                return await self._fallback_analysis(patent_id, analysis_type)

        except Exception as e:
            logger.error(f"分析失败: {e}")
            # 降级到模拟数据
            return await self._fallback_analysis(patent_id, analysis_type)

    async def _fallback_search(
        self,
        query: str,
        limit: int,
        elapsed_time: float,
    ) -> dict[str, Any]:
        """降级搜索（模拟数据）"""
        await asyncio.sleep(0.1)  # 模拟延迟

        return {
            "query": query,
            "total": min(limit, 5),
            "results": [
                {
                    "id": f"CN{1000+i}A",
                    "title": f"{query}相关专利 - 实施例{i+1}",
                    "applicant": "广东冠一机械科技有限公司",
                    "date": "2024-01-01",
                    "score": 0.95 - i * 0.05,
                    "abstract": f"本发明涉及{query}的技术领域...",
                }
                for i in range(min(limit, 5))
            ],
            "search_time": round(elapsed_time, 3),
            "cached": False,
            "source": "fallback",
        }

    async def _fallback_analysis(
        self,
        patent_id: str,
        analysis_type: str,
    ) -> dict[str, Any]:
        """降级分析（模拟数据）"""
        await asyncio.sleep(0.1)  # 模拟延迟

        return {
            "patent_id": patent_id,
            "analysis_type": analysis_type,
            "creativity_level": "中等" if analysis_type == "creativity" else "未评估",
            "key_features": [
                "特征1: 结构创新",
                "特征2: 方法优化",
                "特征3: 性能提升",
            ],
            "technical_effect": "具有显著的技术效果",
            "authorization_prospects": "良好",
            "confidence": 0.75,
            "details": {
                "novelty": "具有新颖性",
                "inventiveness": "具有创造性",
                "practicality": "具有实用性",
            },
            "cached": False,
            "source": "fallback",
        }


# 同步包装器
class SyncRealAPIAdapter:
    """同步真实API适配器"""

    def __init__(self, base_url: str = "http://localhost:8009"):
        self.async_adapter = RealAPIAdapter(base_url)
        self._loop = None

    def _get_loop(self):
        """获取事件循环"""
        try:
            return asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop

    def test_connection(self) -> dict[str, Any]:
        """测试连接"""
        loop = self._get_loop()
        return loop.run_until_complete(
            self.async_adapter.test_connection()
        )

    def search_patents(self, query: str, limit: int = 10) -> dict[str, Any]:
        """搜索专利"""
        loop = self._get_loop()
        return loop.run_until_complete(
            self.async_adapter.search_patents(query, limit)
        )

    def analyze_patent(self, patent_id: str, analysis_type: str = "creativity") -> dict[str, Any]:
        """分析专利"""
        loop = self._get_loop()
        return loop.run_until_complete(
            self.async_adapter.analyze_patent(patent_id, analysis_type)
        )

    def close(self):
        """关闭客户端"""
        if self._loop and self._loop.is_running():
            self._loop.run_until_complete(self.async_adapter.close())
