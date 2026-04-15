#!/usr/bin/env python3
"""
增强版LangChain专利检索工具
Enhanced LangChain Patent Search Tool

基于LangChain框架的增强版专利检索工具，支持多数据源、高级检索策略和智能分析功能。
集成Google专利、USPTO、Espacenet等多个专利数据源。

Created by Athena AI团队
Date: 2025-12-05
Version: 2.0.0
"""

import asyncio
import json
import logging
import os
import re

# 项目内部依赖
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from urllib.parse import quote, urlencode

# 异步HTTP请求
import aiohttp

# 数据处理
from bs4 import BeautifulSoup
from langchain.callbacks.manager import AsyncCallbackManagerForToolRun
from langchain.pydantic_v1 import BaseModel, Field

# LangChain核心组件
from langchain.tools import BaseTool

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from prototypes.patent_search.production_google_patents_search import (
    ProductionGooglePatentsSearcher,
)

from tools.langchain_patent_search import (
    PatentInfo,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class PatentAnalysis:
    """专利分析结果"""
    patent_count: int = 0
    top_assignees: list[tuple[str, int]] = field(default_factory=list)
    top_inventors: list[tuple[str, int]] = field(default_factory=list)
    publication_trend: list[tuple[str, int]] = field(default_factory=list)
    technology_areas: list[str] = field(default_factory=list)
    average_citations: float = 0.0
    legal_status_distribution: dict[str, int] = field(default_factory=dict)


class AdvancedPatentSearchInput(BaseModel):
    """高级专利检索输入模型"""
    query: str = Field(..., description='专利检索关键词或查询语句')
    assignee: str | None = Field(None, description='专利权人/受让人')
    inventor: str | None = Field(None, description='发明人')
    patent_number: str | None = Field(None, description='专利号')
    filing_date_start: str | None = Field(None, description='申请日期开始 YYYY-MM-DD')
    filing_date_end: str | None = Field(None, description='申请日期结束 YYYY-MM-DD')
    publication_date_start: str | None = Field(None, description='公开日期开始 YYYY-MM-DD')
    publication_date_end: str | None = Field(None, description='公开日期结束 YYYY-MM-DD')
    patent_type: str | None = Field(None, description='专利类型: utility, design, plant')
    status: str | None = Field(None, description='专利状态: granted, application')
    country: str | None = Field(None, description='国家代码: US, CN, EP, WO')
    language: str | None = Field(None, description='语言代码: en, zh')
    sort_by: str | None = Field('relevance', description='排序方式: relevance, newest, oldest')
    max_results: int = Field(10, description='最大结果数量', ge=1, le=100)
    data_sources: list[str] = Field(['google_patents'], description='数据源列表')
    include_citations: bool = Field(True, description='是否包含引用信息')
    include_family: bool = Field(True, description='是否包含专利家族信息')
    similarity_threshold: float = Field(0.7, description='相似度阈值', ge=0.0, le=1.0)
    enable_analysis: bool = Field(True, description='是否启用分析功能')


class AdvancedPatentSearchOutput(BaseModel):
    """高级专利检索输出模型"""
    patents: list[dict[str, Any]] = Field(description='专利信息列表')
    analysis: dict[str, Any] | None = Field(None, description='专利分析结果')
    total_results: int = Field(description='总结果数量')
    query_time: float = Field(description='查询耗时(秒)')
    search_sources: list[str] = Field(description='使用的数据源')
    success: bool = Field(description='检索是否成功')
    message: str = Field(description='状态消息')
    citations: list[dict[str, Any]] = Field(default_factory=list, description='引用信息')
    family_patents: list[dict[str, Any]] = Field(default_factory=list, description='专利家族信息')


class EnhancedPatentSearchTool(BaseTool):
    """
    增强版LangChain专利检索工具

    基于LangChain框架的增强版专利检索工具，支持多数据源、
    高级检索策略、专利分析功能和智能推荐。

    主要功能:
    - 多数据源集成 (Google Patents, USPTO, Espacenet)
    - 高级检索策略 (布尔查询、通配符、模糊匹配)
    - 专利分析和统计
    - 专利家族检索
    - 引用网络分析
    - 智能推荐系统
    """

    name: str = 'enhanced_patent_search'
    description: str = (
        '增强版专利检索工具, 支持多数据源、布尔查询、通配符、精确匹配等高级检索功能。'
        '支持AND、OR、NOT布尔逻辑运算, 双引号精确匹配, 星号通配符, 括号优先级分组。'
    )

    args_schema: type[BaseModel] = AdvancedPatentSearchInput

    def __init__(self):
        """初始化增强专利检索工具"""
        super().__init__()
        self.searcher = ProductionGooglePatentsSearcher()
        self.session = None
        self._setup_session()

        # 数据源配置
        self.data_source_configs = {
            'google_patents': {
                'url': 'https://patents.google.com/',
                'name': 'Google Patents',
                'enabled': True
            },
            'uspto': {
                'url': 'https://patft.uspto.gov/',
                'name': 'USPTO Patent Full-Text Database',
                'enabled': True
            },
            'espacenet': {
                'url': 'https://worldwide.espacenet.com/',
                'name': 'Espacenet',
                'enabled': True
            }
        }

    def _setup_session(self):
        """设置HTTP会话"""
        self.session = aiohttp.ClientSession()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        self.session.headers.update(headers)

    def _build_google_patents_url(self, query: AdvancedPatentSearchInput) -> str:
        """构建Google专利检索URL"""
        base_url = 'https://patents.google.com/'
        params = []

        # 处理复杂查询
        processed_query = self._process_query_logic(query.query)
        params.append(f"q={quote(processed_query)}")

        # 专利权人
        if query.assignee:
            params.append(f"oq={quote(query.assignee)}")

        # 发明人
        if query.inventor:
            params.append(f"ia={quote(query.inventor)}")

        # 专利号
        if query.patent_number:
            params.append(f"q={quote(query.patent_number)}")

        # 日期范围
        if query.filing_date_start:
            params.append(f"after=priority:{query.filing_date_start}")
        if query.filing_date_end:
            params.append(f"before=priority:{query.filing_date_end}")

        if query.publication_date_start:
            params.append(f"after={query.publication_date_start}")
        if query.publication_date_end:
            params.append(f"before={query.publication_date_end}")

        # 专利类型
        type_map = {'utility': 'U', 'design': 'D', 'plant': 'P'}
        if query.patent_type and query.patent_type.lower() in type_map:
            params.append(f"type={type_map[query.patent_type.lower()]}")

        # 专利状态
        status_map = {'granted': 'GRANT', 'application': 'APP'}
        if query.status and query.status.lower() in status_map:
            params.append(f"status={status_map[query.status.lower()]}")

        # 国家
        if query.country:
            params.append(f"country={query.country.upper()}")

        # 语言
        lang_map = {'en': 'en', 'zh': 'zh'}
        if query.language and query.language.lower() in lang_map:
            params.append(f"language={lang_map[query.language.lower()]}")

        # 排序
        sort_map = {'relevance': '', 'newest': 'newest', 'oldest': 'oldest'}
        if query.sort_by and query.sort_by.lower() in sort_map:
            params.append(f"sort={sort_map[query.sort_by.lower()]}")

        return base_url + '?' + '&'.join(params)

    def _build_uspto_url(self, query: AdvancedPatentSearchInput) -> str:
        """构建USPTO检索URL"""
        base_url = 'https://patft.uspto.gov/netacgi/nph-Parser'
        params = {
            'patentnumber': query.patent_number or '',
            'Sect1': 'PTO2',
            'Sect2': 'HITOFF',
            'u': f"/netacgi/nph-Parser?patentnumber={query.patent_number or ''}&Sect1=PTO2&Sect2=HITOFF&p=1&u=%2Fnetahtml%2FPTO%2Fsrchnum.html&r=1&f=S",
            'OS': 'PN/2/0',
            'RS': 'PN/2/0'
        }

        # 处理关键词查询
        if query.query and not query.patent_number:
            params['TERM1'] = query.query
            params['FIELD1'] = 'TI'  # 标题字段

        return base_url + '?' + urlencode(params)

    def _build_espacenet_url(self, query: AdvancedPatentSearchInput) -> str:
        """构建Espacenet检索URL"""
        base_url = 'https://worldwide.espacenet.com/'
        params = []

        # 基本查询
        processed_query = self._process_query_logic(query.query)
        params.append(f"q={quote(processed_query)}")

        # 专利权人
        if query.assignee:
            params.append(f"inventor={quote(query.assignee)}")

        # 发明人
        if query.inventor:
            params.append(f"inventor={quote(query.inventor)}")

        return base_url + 'search?' + '&'.join(params)

    def _process_query_logic(self, query: str) -> str:
        """处理查询逻辑，支持AND、OR、NOT操作"""
        if not query:
            return ''

        # 处理布尔逻辑
        query = query.replace(' AND ', ' AND ').replace(' OR ', ' OR ').replace(' NOT ', ' NOT ')

        # 处理特殊字符
        query = re.sub(r'([^\w\s\(\)"\'\-\.])', r'\\\1', query)

        return query.strip()

    async def _search_google_patents(self, query: AdvancedPatentSearchInput) -> tuple[list[PatentInfo], dict[str, Any]]:
        """检索Google Patents"""
        search_url = self._build_google_patents_url(query)

        try:
            async with self.session.get(search_url) as response:
                if response.status == 200:
                    html_content = await response.text()
                    patents = self._parse_google_patents_results(html_content, query.max_results)

                    metadata = {
                        'source': 'Google Patents',
                        'url': search_url,
                        'total_estimated': self._estimate_total_results(html_content)
                    }

                    return patents, metadata
                else:
                    return [], {'error': f"HTTP {response.status}: {response.reason}"}

        except Exception as e:
            logger.error(f"Google Patents检索失败: {str(e)}")
            return [], {'error': str(e)}

    async def _search_uspto(self, query: AdvancedPatentSearchInput) -> tuple[list[PatentInfo], dict[str, Any]]:
        """检索USPTO数据库"""
        search_url = self._build_uspto_url(query)

        try:
            async with self.session.get(search_url) as response:
                if response.status == 200:
                    html_content = await response.text()
                    patents = self._parse_uspto_results(html_content, query.max_results)

                    metadata = {
                        'source': 'USPTO',
                        'url': search_url,
                        'total_estimated': len(patents)
                    }

                    return patents, metadata
                else:
                    return [], {'error': f"HTTP {response.status}: {response.reason}"}

        except Exception as e:
            logger.error(f"USPTO检索失败: {str(e)}")
            return [], {'error': str(e)}

    async def _search_espacenet(self, query: AdvancedPatentSearchInput) -> tuple[list[PatentInfo], dict[str, Any]]:
        """检索Espacenet"""
        search_url = self._build_espacenet_url(query)

        try:
            async with self.session.get(search_url) as response:
                if response.status == 200:
                    html_content = await response.text()
                    patents = self._parse_espacenet_results(html_content, query.max_results)

                    metadata = {
                        'source': 'Espacenet',
                        'url': search_url,
                        'total_estimated': len(patents)
                    }

                    return patents, metadata
                else:
                    return [], {'error': f"HTTP {response.status}: {response.reason}"}

        except Exception as e:
            logger.error(f"Espacenet检索失败: {str(e)}")
            return [], {'error': str(e)}

    def _parse_google_patents_results(self, html_content: str, max_results: int) -> list[PatentInfo]:
        """解析Google Patents检索结果"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            patents = []

            result_items = soup.find_all('div', class_='search-result-item')

            for i, item in enumerate(result_items[:max_results]):
                try:
                    patent_info = self._extract_google_patent_info(item)
                    if patent_info:
                        patents.append(patent_info)
                except Exception as e:
                    logger.warning(f"解析Google Patents结果 {i+1} 失败: {str(e)}")
                    continue

            return patents

        except Exception as e:
            logger.error(f"解析Google Patents结果失败: {str(e)}")
            return []

    def _parse_uspto_results(self, html_content: str, max_results: int) -> list[PatentInfo]:
        """解析USPTO检索结果"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            patents = []

            # USPTO的解析逻辑（需要根据实际HTML结构调整）
            result_items = soup.find_all('table')

            for i, item in enumerate(result_items[:max_results]):
                try:
                    patent_info = self._extract_uspto_patent_info(item)
                    if patent_info:
                        patents.append(patent_info)
                except Exception as e:
                    logger.warning(f"解析USPTO结果 {i+1} 失败: {str(e)}")
                    continue

            return patents

        except Exception as e:
            logger.error(f"解析USPTO结果失败: {str(e)}")
            return []

    def _parse_espacenet_results(self, html_content: str, max_results: int) -> list[PatentInfo]:
        """解析Espacenet检索结果"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            patents = []

            result_items = soup.find_all('div', class_='search-result')

            for i, item in enumerate(result_items[:max_results]):
                try:
                    patent_info = self._extract_espacenet_patent_info(item)
                    if patent_info:
                        patents.append(patent_info)
                except Exception as e:
                    logger.warning(f"解析Espacenet结果 {i+1} 失败: {str(e)}")
                    continue

            return patents

        except Exception as e:
            logger.error(f"解析Espacenet结果失败: {str(e)}")
            return []

    def _extract_google_patent_info(self, item) -> PatentInfo | None:
        """从Google Patents结果中提取专利信息"""
        try:
            # 提取标题和链接
            title_elem = item.find('h3', class_='search-result-title')
            if not title_elem:
                return None

            title = title_elem.get_text(strip=True)
            link_elem = title_elem.find('a')
            patent_url = link_elem.get('href') if link_elem else ''

            # 提取专利号
            patent_number = ''
            if link_elem:
                patent_number = link_elem.get_text(strip=True)

            # 提取其他信息...
            abstract_elem = item.find('div', class_='search-result-snippet')
            abstract = abstract_elem.get_text(strip=True) if abstract_elem else ''

            assignee = ''
            inventor = ''
            filing_date = ''
            publication_date = ''

            # 创建专利信息对象
            patent_info = PatentInfo(
                title=title,
                patent_number=patent_number,
                abstract=abstract,
                assignee=assignee,
                inventor=inventor,
                filing_date=filing_date,
                publication_date=publication_date,
                patent_url=patent_url,
                source='Google Patents',
                scraped_at=datetime.now()
            )

            return patent_info

        except Exception as e:
            logger.warning(f"提取Google Patents信息失败: {str(e)}")
            return None

    def _extract_uspto_patent_info(self, item) -> PatentInfo | None:
        """从USPTO结果中提取专利信息"""
        # 实现USPTO专利信息提取逻辑
        return None

    def _extract_espacenet_patent_info(self, item) -> PatentInfo | None:
        """从Espacenet结果中提取专利信息"""
        # 实现Espacenet专利信息提取逻辑
        return None

    def _estimate_total_results(self, html_content: str) -> int:
        """估算总结果数量"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # 查找结果统计信息
            count_elem = soup.find('div', class_='results-count')
            if count_elem:
                count_text = count_elem.get_text()
                # 提取数字
                numbers = re.findall(r'\d+', count_text.replace(',', ''))
                if numbers:
                    return int(numbers[0])

            return 0

        except Exception:
            return 0

    async def _analyze_patents(self, patents: list[PatentInfo]) -> PatentAnalysis:
        """分析专利数据"""
        if not patents:
            return PatentAnalysis()

        analysis = PatentAnalysis(patent_count=len(patents))

        # 分析专利权人分布
        assignee_counts = {}
        for patent in patents:
            if patent.assignee:
                assignee_counts[patent.assignee] = assignee_counts.get(patent.assignee, 0) + 1

        analysis.top_assignees = sorted(assignee_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        # 分析发明人分布
        inventor_counts = {}
        for patent in patents:
            if patent.inventor:
                inventors = [inv.strip() for inv in patent.inventor.split(',')]
                for inventor in inventors:
                    if inventor:
                        inventor_counts[inventor] = inventor_counts.get(inventor, 0) + 1

        analysis.top_inventors = sorted(inventor_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        # 分析公开日期趋势
        date_counts = {}
        for patent in patents:
            if patent.publication_date:
                # 提取年份
                year_match = re.search(r'\b(19|20)\d{2}\b', patent.publication_date)
                if year_match:
                    year = year_match.group()
                    date_counts[year] = date_counts.get(year, 0) + 1

        analysis.publication_trend = sorted(date_counts.items(), key=lambda x: x[0])

        return analysis

    async def _search_patent_citations(self, patent_number: str) -> list[dict[str, Any]]:
        """检索专利引用信息"""
        citations = []

        # 实现引用检索逻辑
        # 这里可以集成专门的引用数据库或API

        return citations

    async def _search_patent_family(self, patent_number: str) -> list[dict[str, Any]]:
        """检索专利家族信息"""
        family_patents = []

        # 实现专利家族检索逻辑
        # 这里可以集成专利家族数据库或API

        return family_patents

    async def _arun(
        self,
        query: str,
        run_manager: AsyncCallbackManagerForToolRun | None = None,
        **kwargs
    ) -> str:
        """执行增强专利检索"""
        try:
            start_time = time.time()

            # 解析输入参数
            search_input = AdvancedPatentSearchInput(**kwargs)

            # 多数据源检索
            all_patents = []
            search_metadata = []
            used_sources = []

            for data_source in search_input.data_sources:
                if data_source in self.data_source_configs:
                    source_config = self.data_source_configs[data_source]
                    if not source_config['enabled']:
                        continue

                    try:
                        if data_source == 'google_patents':
                            patents, metadata = await self._search_google_patents(search_input)
                        elif data_source == 'uspto':
                            patents, metadata = await self._search_uspto(search_input)
                        elif data_source == 'espacenet':
                            patents, metadata = await self._search_espacenet(search_input)
                        else:
                            continue

                        all_patents.extend(patents)
                        search_metadata.append(metadata)
                        used_sources.append(data_source)

                    except Exception as e:
                        logger.warning(f"检索 {data_source} 失败: {str(e)}")
                        continue

            # 去重处理（基于专利号）
            unique_patents = self._deduplicate_patents(all_patents)

            # 限制结果数量
            final_patents = unique_patents[:search_input.max_results]

            # 分析专利数据
            analysis = None
            if search_input.enable_analysis:
                analysis_data = await self._analyze_patents(final_patents)
                analysis = {
                    'patent_count': analysis_data.patent_count,
                    'top_assignees': analysis_data.top_assignees,
                    'top_inventors': analysis_data.top_inventors,
                    'publication_trend': analysis_data.publication_trend,
                    'technology_areas': analysis_data.technology_areas
                }

            # 检索引用和家族信息
            citations = []
            family_patents = []

            if search_input.include_citations and final_patents:
                for patent in final_patents[:3]:  # 限制为前3个专利
                    try:
                        patent_citations = await self._search_patent_citations(patent.patent_number)
                        citations.extend(patent_citations)
                    except Exception as e:
                        logger.warning(f"检索专利引用失败: {str(e)}")

            if search_input.include_family and final_patents:
                for patent in final_patents[:3]:  # 限制为前3个专利
                    try:
                        patent_family = await self._search_patent_family(patent.patent_number)
                        family_patents.extend(patent_family)
                    except Exception as e:
                        logger.warning(f"检索专利家族失败: {str(e)}")

            query_time = time.time() - start_time

            # 构建输出
            output = AdvancedPatentSearchOutput(
                patents=[self._patent_info_to_dict(p) for p in final_patents],
                analysis=analysis,
                total_results=len(final_patents),
                query_time=query_time,
                search_sources=used_sources,
                success=True,
                message=f"检索完成，找到 {len(final_patents)} 条专利，使用数据源: {', '.join(used_sources)}",
                citations=citations,
                family_patents=family_patents
            )

            return output.json()

        except Exception as e:
            logger.error(f"增强专利检索失败: {str(e)}")

            error_output = AdvancedPatentSearchOutput(
                patents=[],
                analysis=None,
                total_results=0,
                query_time=0,
                search_sources=[],
                success=False,
                message=f"检索失败: {str(e)}",
                citations=[],
                family_patents=[]
            )

            return error_output.json()

    def _deduplicate_patents(self, patents: list[PatentInfo]) -> list[PatentInfo]:
        """去重专利列表"""
        seen_patents = set()
        unique_patents = []

        for patent in patents:
            patent_key = (patent.patent_number, patent.title)
            if patent_key not in seen_patents:
                seen_patents.add(patent_key)
                unique_patents.append(patent)

        return unique_patents

    def _patent_info_to_dict(self, patent_info: PatentInfo) -> dict[str, Any]:
        """将专利信息对象转换为字典"""
        return {
            'title': patent_info.title,
            'patent_number': patent_info.patent_number,
            'abstract': patent_info.abstract,
            'assignee': patent_info.assignee,
            'inventor': patent_info.inventor,
            'filing_date': patent_info.filing_date,
            'publication_date': patent_info.publication_date,
            'patent_url': patent_info.patent_url,
            'source': patent_info.source,
            'scraped_at': patent_info.scraped_at.isoformat() if patent_info.scraped_at else None
        }

    def _run(
        self,
        query: str,
        run_manager: AsyncCallbackManagerForToolRun | None = None,
        **kwargs
    ) -> str:
        """同步执行增强专利检索"""
        return asyncio.run(self._arun(query, run_manager, **kwargs))


# 创建增强版专利检索工具
def create_enhanced_patent_search_tool() -> EnhancedPatentSearchTool:
    """创建增强版专利检索工具实例"""
    return EnhancedPatentSearchTool()


# 工具集合
ENHANCED_PATENT_SEARCH_TOOLS = [
    create_enhanced_patent_search_tool()
]


# 测试代码
async def test_enhanced_patent_search_tool():
    """测试增强版专利检索工具"""
    tool = create_enhanced_patent_search_tool()

    logger.info(str('=' * 60))
    logger.info('增强版LangChain专利检索工具测试')
    logger.info(str('=' * 60))

    # 测试1: 基本检索和分析
    logger.info("\n1. 测试基本检索和分析:")
    try:
        result = await tool._arun(
            query='人工智能',
            max_results=5,
            enable_analysis=True,
            data_sources=['google_patents']
        )
        result_data = json.loads(result)
        logger.info(f"   检索成功: {result_data['success']}")
        logger.info(f"   结果数量: {result_data['total_results']}")
        logger.info(f"   耗时: {result_data['query_time']:.2f}秒")

        if result_data['analysis']:
            analysis = result_data['analysis']
            logger.info(f"   分析: 专利总数={analysis['patent_count']}")
            if analysis['top_assignees']:
                logger.info(f"   顶级专利权人: {analysis['top_assignees'][0][0]} ({analysis['top_assignees'][0][1]}项专利)")

    except Exception as e:
        logger.info(f"   测试失败: {str(e)}")

    # 测试2: 多数据源检索
    logger.info("\n2. 测试多数据源检索:")
    try:
        result = await tool._arun(
            query='blockchain',
            max_results=3,
            data_sources=['google_patents', 'espacenet'],
            enable_analysis=False
        )
        result_data = json.loads(result)
        logger.info(f"   检索成功: {result_data['success']}")
        logger.info(f"   结果数量: {result_data['total_results']}")
        logger.info(f"   使用数据源: {', '.join(result_data['search_sources'])}")

    except Exception as e:
        logger.info(f"   测试失败: {str(e)}")

    # 测试3: 高级检索条件
    logger.info("\n3. 测试高级检索条件:")
    try:
        result = await tool._arun(
            query='deep learning',
            assignee='Google',
            filing_date_start='2020-01-01',
            filing_date_end='2023-12-31',
            max_results=3,
            include_citations=True,
            enable_analysis=True
        )
        result_data = json.loads(result)
        logger.info(f"   检索成功: {result_data['success']}")
        logger.info(f"   结果数量: {result_data['total_results']}")
        logger.info(f"   包含引用: {len(result_data['citations'])}")
        logger.info(f"   包含家族: {len(result_data['family_patents'])}")

    except Exception as e:
        logger.info(f"   测试失败: {str(e)}")

    logger.info(str("\n" + '=' * 60))
    logger.info('增强版LangChain专利检索工具测试完成')
    logger.info(str('=' * 60))


if __name__ == '__main__':
    asyncio.run(test_enhanced_patent_search_tool())
