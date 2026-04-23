#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生产级专利搜索工具
Production Patent Search Tool

集成ScrapingBee代理服务，支持JavaScript渲染的真实专利数据抓取
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from typing import Any, Dict, List

# 导入增强版爬虫
from core.interfaces.patent_service import PatentRetrievalService
from config.dependency_injection import DIContainer import (
    EnhancedGooglePatentsCrawler,
    PatentInfo,
)
from langchain.callbacks.manager import AsyncCallbackManagerForToolRun
from langchain.pydantic_v1 import BaseModel, Field, root_validator

# LangChain工具
from langchain.tools import BaseTool

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProductionPatentSearchInput(BaseModel):
    """生产级专利搜索输入模型"""
    query: str = Field(..., description='专利检索关键词或查询语句')
    max_results: int = Field(10, description='最大结果数量', ge=1, le=50)
    assignee: Optional[str] = Field(None, description='专利权人/受让人过滤')
    inventor: Optional[str] = Field(None, description='发明人过滤')
    patent_type: Optional[str] = Field(None, description='专利类型: utility, design, plant')
    country: Optional[str] = Field(None, description='国家代码: US, CN, EP, WO')
    date_range: Optional[str] = Field(None, description='日期范围，格式: YYYY-YYYY 或 YYYY-MM-DD:YYYY-MM-DD')
    include_details: bool = Field(True, description='是否获取专利详细信息')

class ProductionPatentSearchOutput(BaseModel):
    """生产级专利搜索输出模型"""
    success: bool = Field(description='检索是否成功')
    patents: List[Dict[str, Any]] = Field(description='专利信息列表')
    total_results: int = Field(description='找到的专利总数')
    query: str = Field(description='原始查询')
    search_time: float = Field(description='检索耗时(秒)')
    source: str = Field(description='数据源')
    message: str = Field(description='状态消息')

class ProductionPatentSearchTool(BaseTool):
    """
    生产级专利搜索工具

    集成ScrapingBee代理服务，支持JavaScript渲染的真实专利数据抓取
    """

    name: str = 'production_patent_search'
    description: """
    生产级专利搜索工具，使用ScrapingBee代理服务获取真实Google专利数据。

    主要特性:
    - JavaScript渲染支持: 能够处理动态加载的网页内容
    - 真实数据源: 直接从Google Patents获取最新专利信息
    - 高级搜索: 支持专利权人、发明人、国家、日期等过滤条件
    - 详细信息: 可获取专利标题、摘要、受让人、发明人等完整信息
    - 智能重试: 内置重试机制确保数据获取稳定性
    - 生产就绪: 支持高并发和大规模数据处理

    使用方法:
    production_patent_search(query='人工智能', max_results=5, country='US')
    production_patent_search(query='machine learning', assignee='Google')
    production_patent_search(query='neural network', date_range='2020-2023')
    """

    args_schema: type[BaseModel] = ProductionPatentSearchInput

    def __init__(self):
        """初始化生产级专利搜索工具"""
        super().__init__()
        self.crawler = EnhancedGooglePatentsCrawler()
        self.last_search_time = 0
        self.min_search_interval = 1.0  # 最小搜索间隔(秒)

    async def _arun(
        self,
        query: str,
        max_results: int = 10,
        assignee: Optional[str] = None,
        inventor: Optional[str] = None,
        patent_type: Optional[str] = None,
        country: Optional[str] = None,
        date_range: Optional[str] = None,
        include_details: bool = True,
        run_manager: AsyncCallbackManagerForToolRun | None = None,
        **kwargs
    ) -> str:
        """执行生产级专利搜索"""
        try:
            start_time = asyncio.get_event_loop().time()

            # 限制搜索频率
            current_time = asyncio.get_event_loop().time()
            if current_time - self.last_search_time < self.min_search_interval:
                await asyncio.sleep(self.min_search_interval - (current_time - self.last_search_time))

            logger.info(f"🔍 生产级专利搜索: {query}")

            # 执行搜索
            patents = await self.crawler.search_patents_with_scrapingbee(
                query=query,
                max_results=max_results,
                assignee=assignee,
                inventor=inventor,
                patent_type=patent_type,
                country=country,
                date_range=date_range
            )

            # 获取详细信息（如果需要）
            if include_details and patents:
                logger.info('📋 获取专利详细信息...')
                for i, patent in enumerate(patents[:3]):  # 限制详细获取数量
                    if patent.patent_number and not patent.abstract:
                        try:
                            detailed_patent = await self.crawler.get_patent_details(patent.patent_number)
                            if detailed_patent:
                                # 更新专利信息
                                patents[i] = detailed_patent
                        except Exception as e:
                            logger.warning(f"获取专利详情失败 {patent.patent_number}: {str(e)}")
                            continue

            # 计算搜索时间
            search_time = asyncio.get_event_loop().time() - start_time
            self.last_search_time = asyncio.get_event_loop().time()

            # 转换为字典格式
            patents_dict = []
            for patent in patents:
                patent_dict = self.crawler.to_dict(patent)
                patents_dict.append(patent_dict)

            # 构建输出
            output = ProductionPatentSearchOutput(
                success=True,
                patents=patents_dict,
                total_results=len(patents_dict),
                query=query,
                search_time=search_time,
                source='Google Patents via ScrapingBee',
                message=f"成功找到 {len(patents_dict)} 个专利，耗时 {search_time:.2f} 秒"
            )

            logger.info(f"✅ 搜索完成: {len(patents_dict)} 个专利")
            return output.json()

        except Exception as e:
            logger.error(f"❌ 生产级专利搜索失败: {str(e)}")

            error_output = ProductionPatentSearchOutput(
                success=False,
                patents=[],
                total_results=0,
                query=query,
                search_time=0,
                source='Google Patents via ScrapingBee',
                message=f"搜索失败: {str(e)}"
            )

            return error_output.json()

    def _run(
        self,
        query: str,
        max_results: int = 10,
        assignee: Optional[str] = None,
        inventor: Optional[str] = None,
        patent_type: Optional[str] = None,
        country: Optional[str] = None,
        date_range: Optional[str] = None,
        include_details: bool = True,
        run_manager: AsyncCallbackManagerForToolRun | None = None,
        **kwargs
    ) -> str:
        """同步执行"""
        return asyncio.run(self._arun(
            query=query,
            max_results=max_results,
            assignee=assignee,
            inventor=inventor,
            patent_type=patent_type,
            country=country,
            date_range=date_range,
            include_details=include_details,
            run_manager=run_manager,
            **kwargs
        ))

# 创建生产级专利搜索工具
def create_production_patent_search_tool() -> ProductionPatentSearchTool:
    """创建生产级专利搜索工具实例"""
    return ProductionPatentSearchTool()

# 工具集合
PRODUCTION_PATENT_SEARCH_TOOLS = [
    create_production_patent_search_tool()
]

# 测试代码
async def test_production_patent_search():
    """测试生产级专利搜索工具"""
    tool = create_production_patent_search_tool()

    logger.info(str('=' * 60))
    logger.info('生产级专利搜索工具测试')
    logger.info(str('=' * 60))

    # 测试1: 基本搜索
    logger.info("\n1️⃣ 测试基本搜索:")
    try:
        result = await tool._arun(
            query='artificial intelligence',
            max_results=3
        )
        result_data = json.loads(result)
        logger.info(f"   搜索成功: {result_data['success']}")
        logger.info(f"   结果数量: {result_data['total_results']}")
        logger.info(f"   耗时: {result_data['search_time']:.2f}秒")
        logger.info(f"   消息: {result_data['message']}")

        if result_data['patents']:
            logger.info(f"   第一个专利标题: {result_data['patents'][0]['title'][:50]}...")

    except Exception as e:
        logger.info(f"   测试失败: {str(e)}")

    # 测试2: 高级搜索
    logger.info("\n2️⃣ 测试高级搜索:")
    try:
        result = await tool._arun(
            query='machine learning',
            assignee='Google',
            country='US',
            max_results=2
        )
        result_data = json.loads(result)
        logger.info(f"   搜索成功: {result_data['success']}")
        logger.info(f"   结果数量: {result_data['total_results']}")
        logger.info(f"   消息: {result_data['message']}")

    except Exception as e:
        logger.info(f"   测试失败: {str(e)}")

    # 测试3: 日期范围搜索
    logger.info("\n3️⃣ 测试日期范围搜索:")
    try:
        result = await tool._arun(
            query='blockchain',
            date_range='2020-2023',
            max_results=2
        )
        result_data = json.loads(result)
        logger.info(f"   搜索成功: {result_data['success']}")
        logger.info(f"   结果数量: {result_data['total_results']}")
        logger.info(f"   消息: {result_data['message']}")

    except Exception as e:
        logger.info(f"   测试失败: {str(e)}")

    logger.info(str("\n" + '=' * 60))
    logger.info('生产级专利搜索工具测试完成')
    logger.info(str('=' * 60))

if __name__ == '__main__':
    asyncio.run(test_production_patent_search())
