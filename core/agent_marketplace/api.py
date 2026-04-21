"""
Agent市场平台FastAPI后端
Agent Marketplace FastAPI Backend

提供Agent的CRUD操作、搜索、评价和统计功能。

作者: Athena平台团队
版本: 1.0.0
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# 导入模型
from core.agent_marketplace.models import (
    Agent,
    AgentCapability,
    AgentCategory,
    AgentListItem,
    AgentDetail,
    AgentStatus,
    AgentVersion,
    ReviewStatus,
    SearchFilters,
    create_agent,
    create_capability,
)

logger = logging.getLogger(__name__)


# ==================== Pydantic模型 ====================

class AgentBase(BaseModel):
    """Agent基础模型"""
    name: str = Field(..., description="Agent名称 (PascalCase)")
    display_name: str = Field(..., description="显示名称")
    slug: str = Field(..., description="URL友好标识符")
    description: str = Field(..., description="描述")
    category: str = Field(default="general", description="类别")


class AgentCreate(AgentBase):
    """Agent创建模型"""
    long_description: str = Field(default="", description="详细描述")
    author_id: str = Field(..., description="作者ID")
    author_name: str = Field(..., description="作者名称")
    organization: str = Field(default="", description="所属组织")
    requires_llm: bool = Field(default=False, description="是否需要LLM")
    requires_tools: bool = Field(default=False, description="是否需要工具")
    tags: List[str] = Field(default_factory=list, description="标签列表")


class AgentUpdate(BaseModel):
    """Agent更新模型"""
    display_name: Optional[str] = None
    description: Optional[str] = None
    long_description: Optional[str] = None
    category: Optional[str] = None
    requires_llm: Optional[bool] = None
    requires_tools: Optional[bool] = None
    tags: Optional[List[str]] = None


class AgentResponse(AgentBase):
    """Agent响应模型"""
    id: str
    status: str
    author_name: str
    current_version: str
    download_count: int
    rating_avg: float
    rating_count: int
    featured: bool
    verified: bool
    created_at: datetime
    updated_at: datetime


class AgentListResponse(BaseModel):
    """Agent列表响应"""
    items: List[AgentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class CapabilityCreate(BaseModel):
    """能力创建模型"""
    name: str = Field(..., description="能力名称 (snake_case)")
    display_name: str = Field(..., description="显示名称")
    description: str = Field(..., description="描述")
    input_types: List[str] = Field(..., description="输入类型")
    output_types: List[str] = Field(..., description="输出类型")
    estimated_time: float = Field(default=5.0, description="预估时间 (秒)")


class ReviewCreate(BaseModel):
    """评价创建模型"""
    rating: int = Field(..., ge=1, le=5, description="评分 (1-5)")
    title: str = Field(..., description="评价标题")
    content: str = Field(..., description="评价内容")
    tags: List[str] = Field(default_factory=list, description="标签")


class ReviewResponse(BaseModel):
    """评价响应模型"""
    id: str
    agent_id: str
    user_name: str
    rating: int
    title: str
    content: str
    tags: List[str]
    created_at: datetime


class StatisticsResponse(BaseModel):
    """统计响应模型"""
    agent_id: str
    total_calls: int
    successful_calls: int
    failed_calls: int
    success_rate: float
    avg_execution_time: float


# ==================== 依赖项 ====================

async def get_db():
    """
    获取数据库会话

    TODO: 实现实际的数据库连接
    """
    # 模拟数据库
    return {}


class MarketplaceService:
    """市场服务类"""

    def __init__(self):
        # 模拟数据存储
        self.agents: Dict[str, Agent] = {}
        self.capabilities: Dict[str, List[AgentCapability]] = {}
        self.reviews: Dict[str, List[Any]] = {}

    async def create_agent(self, data: AgentCreate) -> Agent:
        """创建Agent"""
        agent = create_agent(
            name=data.name,
            display_name=data.display_name,
            description=data.description,
            category=AgentCategory(data.category),
            author_id=data.author_id,
            author_name=data.author_name,
        )
        agent.long_description = data.long_description
        agent.organization = data.organization
        agent.requires_llm = data.requires_llm
        agent.requires_tools = data.requires_tools
        agent.tags = data.tags

        self.agents[agent.id] = agent
        self.capabilities[agent.id] = []
        self.reviews[agent.id] = []

        logger.info(f"创建Agent: {agent.id} - {agent.display_name}")
        return agent

    async def get_agent(self, agent_id: str) -> Optional[Agent]:
        """获取Agent"""
        return self.agents.get(agent_id)

    async def list_agents(
        self,
        filters: SearchFilters,
    ) -> tuple[List[Agent], int]:
        """列出Agent"""
        agents = list(self.agents.values())

        # 应用过滤
        if filters.keyword:
            keyword = filters.keyword.lower()
            agents = [
                a for a in agents
                if keyword in a.name.lower()
                or keyword in a.display_name.lower()
                or keyword in a.description.lower()
            ]

        if filters.category:
            agents = [a for a in agents if a.category.value == filters.category]

        if filters.status:
            agents = [a for a in agents if a.status == filters.status]

        if filters.min_rating is not None:
            agents = [a for a in agents if a.rating_avg >= filters.min_rating]

        # 排序
        if filters.sort_by == "updated_at":
            reverse = filters.sort_order == "desc"
            agents.sort(key=lambda x: x.updated_at, reverse=reverse)
        elif filters.sort_by == "download_count":
            reverse = filters.sort_order == "desc"
            agents.sort(key=lambda x: x.download_count, reverse=reverse)
        elif filters.sort_by == "rating_avg":
            reverse = filters.sort_order == "desc"
            agents.sort(key=lambda x: x.rating_avg, reverse=reverse)
        elif filters.sort_by == "name":
            reverse = filters.sort_order == "desc"
            agents.sort(key=lambda x: x.display_name.lower(), reverse=reverse)

        total = len(agents)

        # 分页
        start = (filters.page - 1) * filters.page_size
        end = start + filters.page_size
        agents = agents[start:end]

        return agents, total

    async def update_agent(self, agent_id: str, data: AgentUpdate) -> Optional[Agent]:
        """更新Agent"""
        agent = self.agents.get(agent_id)
        if not agent:
            return None

        if data.display_name is not None:
            agent.display_name = data.display_name
        if data.description is not None:
            agent.description = data.description
        if data.long_description is not None:
            agent.long_description = data.long_description
        if data.category is not None:
            agent.category = AgentCategory(data.category)
        if data.requires_llm is not None:
            agent.requires_llm = data.requires_llm
        if data.requires_tools is not None:
            agent.requires_tools = data.requires_tools
        if data.tags is not None:
            agent.tags = data.tags

        agent.updated_at = datetime.now()
        return agent

    async def delete_agent(self, agent_id: str) -> bool:
        """删除Agent"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            if agent_id in self.capabilities:
                del self.capabilities[agent_id]
            if agent_id in self.reviews:
                del self.reviews[agent_id]
            return True
        return False

    async def add_capability(
        self, agent_id: str, data: CapabilityCreate
    ) -> Optional[AgentCapability]:
        """添加能力"""
        if agent_id not in self.agents:
            return None

        capability = create_capability(
            agent_id=agent_id,
            name=data.name,
            display_name=data.display_name,
            description=data.description,
            input_types=data.input_types,
            output_types=data.output_types,
            estimated_time=data.estimated_time,
        )

        self.capabilities[agent_id].append(capability)
        return capability

    async def get_capabilities(self, agent_id: str) -> List[AgentCapability]:
        """获取能力列表"""
        return self.capabilities.get(agent_id, [])

    async def get_categories(self) -> List[Dict[str, Any]]:
        """获取分类列表"""
        return [
            {"value": cat.value, "label": cat.value.title()}
            for cat in AgentCategory
        ]


# 全局服务实例
marketplace_service = MarketplaceService()


# ==================== 路由 ====================

router = APIRouter(
    prefix="/api/v1/agent-marketplace",
    tags=["Agent Marketplace"],
)


@router.get("/agents", response_model=AgentListResponse)
async def list_agents(
    keyword: str = Query("", description="搜索关键词"),
    category: Optional[str] = Query(None, description="类别筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    min_rating: Optional[float] = Query(None, ge=0, le=5, description="最低评分"),
    sort_by: str = Query("updated_at", description="排序字段"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="排序方向"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
):
    """
    获取Agent列表

    支持关键词搜索、分类筛选、评分筛选和排序。
    """
    filters = SearchFilters(
        keyword=keyword,
        category=category,
        status=AgentStatus(status) if status else None,
        min_rating=min_rating,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )

    agents, total = await marketplace_service.list_agents(filters)

    total_pages = (total + page_size - 1) // page_size

    return AgentListResponse(
        items=[AgentResponse(**a.__dict__) for a in agents],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str):
    """
    获取Agent详情

    返回指定Agent的详细信息。
    """
    agent = await marketplace_service.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent not found: {agent_id}",
        )

    return AgentResponse(**agent.__dict__)


@router.post("/agents", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(data: AgentCreate):
    """
    创建新Agent

    创建一个新的Agent并返回其详细信息。
    """
    agent = await marketplace_service.create_agent(data)
    return AgentResponse(**agent.__dict__)


@router.put("/agents/{agent_id}", response_model=AgentResponse)
async def update_agent(agent_id: str, data: AgentUpdate):
    """
    更新Agent

    更新指定Agent的信息。
    """
    agent = await marketplace_service.update_agent(agent_id, data)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent not found: {agent_id}",
        )

    return AgentResponse(**agent.__dict__)


@router.delete("/agents/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(agent_id: str):
    """
    删除Agent

    删除指定的Agent。
    """
    success = await marketplace_service.delete_agent(agent_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent not found: {agent_id}",
        )


@router.get("/agents/{agent_id}/capabilities")
async def get_agent_capabilities(agent_id: str):
    """
    获取Agent能力列表

    返回指定Agent的所有能力。
    """
    agent = await marketplace_service.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent not found: {agent_id}",
        )

    capabilities = await marketplace_service.get_capabilities(agent_id)
    return {"agent_id": agent_id, "capabilities": capabilities}


@router.post("/agents/{agent_id}/capabilities", status_code=status.HTTP_201_CREATED)
async def add_agent_capability(agent_id: str, data: CapabilityCreate):
    """
    添加Agent能力

    为指定Agent添加新能力。
    """
    capability = await marketplace_service.add_capability(agent_id, data)
    if not capability:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent not found: {agent_id}",
        )

    return capability


@router.get("/categories")
async def get_categories():
    """
    获取分类列表

    返回所有可用的Agent分类。
    """
    categories = await marketplace_service.get_categories()
    return {"categories": categories}


@router.get("/agents/{agent_id}/statistics", response_model=StatisticsResponse)
async def get_agent_statistics(agent_id: str):
    """
    获取Agent统计信息

    返回指定Agent的使用统计。
    """
    agent = await marketplace_service.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent not found: {agent_id}",
        )

    # TODO: 实现实际的统计查询
    return StatisticsResponse(
        agent_id=agent_id,
        total_calls=0,
        successful_calls=0,
        failed_calls=0,
        success_rate=0.0,
        avg_execution_time=0.0,
    )


# ==================== 应用工厂 ====================

def create_app() -> FastAPI:
    """
    创建FastAPI应用

    Returns:
        FastAPI应用实例
    """
    app = FastAPI(
        title="Athena Agent Marketplace API",
        description="Athena平台Agent市场API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生产环境应限制具体域名
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    app.include_router(router)

    # 健康检查
    @app.get("/health")
    async def health_check():
        """健康检查端点"""
        return {
            "status": "healthy",
            "service": "agent-marketplace",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
        }

    return app


# ==================== 主入口 ====================

app = create_app()


if __name__ == "__main__":
    import uvicorn

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # 运行服务器
    uvicorn.run(
        "core.agent_marketplace.api:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info",
    )
