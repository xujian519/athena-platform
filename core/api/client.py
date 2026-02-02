"""
客户端注册和管理API

支持Athena客户端(opencode/iflow cli)的注册和能力管理
"""

from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

# =============================================================================
# 数据模型
# =============================================================================


class ClientCapability(BaseModel):
    """客户端能力"""

    enabled: bool
    formats: list[str]
    engine: str
    performance: dict | None = None


class ClientCapabilities(BaseModel):
    """客户端能力集合"""

    ocr: ClientCapability | None = None
    image_understanding: ClientCapability | None = None


class ClientRegistrationRequest(BaseModel):
    """客户端注册请求"""

    client_id: str
    client_type: str  # opencode, iflow-cli
    os: str | None = None
    timestamp: datetime = Field(default_factory=datetime.now)
    capabilities: dict[str, ClientCapability]


class ClientRegistrationResponse(BaseModel):
    """客户端注册响应"""

    success: bool
    client_id: str
    registered_at: datetime
    message: str = "注册成功"


class ClientInfo(BaseModel):
    """客户端信息"""

    client_id: str
    client_type: str
    os: str | None = None
    registered_at: datetime
    last_seen: datetime
    capabilities: dict[str, ClientCapability]


class ClientStatusResponse(BaseModel):
    """客户端状态响应"""

    client_id: str
    registered: bool
    capabilities: dict[str, ClientCapability]
    last_seen: datetime | None = None


# =============================================================================
# 客户端注册表(内存存储,生产环境应使用数据库)
# =============================================================================


class ClientRegistry:
    """客户端注册表"""

    def __init__(self):
        self.clients: dict[str, ClientInfo] = {}

    def register(self, request: ClientRegistrationRequest) -> ClientInfo:
        """注册客户端"""
        now = datetime.now()

        client_info = ClientInfo(
            client_id=request.client_id,
            client_type=request.client_type,
            os=request.os,
            registered_at=now,
            last_seen=now,
            capabilities=request.capabilities,
        )

        self.clients[request.client_id] = client_info
        return client_info

    def get_client(self, client_id: str) -> ClientInfo | None:
        """获取客户端信息"""
        return self.clients.get(client_id)

    def update_last_seen(self, client_id: str) -> None:
        """更新最后活跃时间"""
        if client_id in self.clients:
            self.clients[client_id].last_seen = datetime.now()

    def list_clients(self) -> list[ClientInfo]:
        """列出所有客户端"""
        return list(self.clients.values())


# 全局注册表实例
client_registry = ClientRegistry()

# =============================================================================
# API路由
# =============================================================================

router = APIRouter(prefix="/api/v1/client", tags=["client"])


@router.post("/register", response_model=ClientRegistrationResponse)
async def register_client(request: ClientRegistrationRequest):
    """
    注册客户端到Athena平台

    客户端启动时调用此接口,上报自身能力
    """
    try:
        # 注册客户端
        client_info = client_registry.register(request)

        return ClientRegistrationResponse(
            success=True,
            client_id=client_info.client_id,
            registered_at=client_info.registered_at,
            message="注册成功",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册失败: {e!s}",
        )


@router.get("/{client_id}", response_model=ClientInfo)
async def get_client_info(client_id: str):
    """
    获取客户端信息
    """
    client_info = client_registry.get_client(client_id)

    if not client_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"客户端不存在: {client_id}",
        )

    return client_info


@router.get("/{client_id}/status", response_model=ClientStatusResponse)
async def get_client_status(client_id: str):
    """
    获取客户端状态
    """
    client_info = client_registry.get_client(client_id)

    if not client_info:
        return ClientStatusResponse(
            client_id=client_id,
            registered=False,
            capabilities={},
            last_seen=None,
        )

    # 更新最后活跃时间
    client_registry.update_last_seen(client_id)

    return ClientStatusResponse(
        client_id=client_info.client_id,
        registered=True,
        capabilities=client_info.capabilities,
        last_seen=client_info.last_seen,
    )


@router.get("/list", response_model=list[ClientInfo])
async def list_clients():
    """
    列出所有已注册的客户端
    """
    return client_registry.list_clients()


# =============================================================================
# 路由导出
# =============================================================================
# Router will be included by main.py
