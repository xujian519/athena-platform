"""
Agent市场平台数据模型
Agent Marketplace Database Models

设计原则：
- 遵循Athena平台统一接口标准
- 支持Agent版本管理和生命周期
- 支持用户评价和评分
- 支持Agent分类和能力标签

作者: Athena平台团队
版本: 1.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional, List
from uuid import uuid4


# ==================== 枚举类型 ====================

class AgentStatus(str, Enum):
    """Agent状态"""
    DRAFT = "draft"              # 草稿
    PENDING_REVIEW = "pending"   # 待审核
    APPROVED = "approved"        # 已批准
    PUBLISHED = "published"      # 已发布
    DEPRECATED = "deprecated"    # 已弃用
    ARCHIVED = "archived"        # 已归档


class AgentCategory(str, Enum):
    """Agent类别"""
    GENERAL = "general"          # 通用
    PATENT = "patent"            # 专利
    LEGAL = "legal"              # 法律
    IP_MANAGEMENT = "ip"         # IP管理
    ANALYSIS = "analysis"        # 分析
    AUTOMATION = "automation"    # 自动化
    EXAMPLE = "example"          # 示例


class VisibilityLevel(str, Enum):
    """可见性级别"""
    PUBLIC = "public"            # 公开
    PRIVATE = "private"          # 私有
    ORGANIZATION = "organization"# 组织内


class ReviewStatus(str, Enum):
    """审核状态"""
    PENDING = "pending"          # 待审核
    APPROVED = "approved"        # 已批准
    REJECTED = "rejected"        # 已拒绝
    NEEDS_REVISION = "revision"  # 需要修订


# ==================== 核心实体 ====================

@dataclass
class Agent:
    """
    Agent实体

    表示市场中的一个Agent，包含基本信息、元数据和统计数据。
    """
    # 主键
    id: str = field(default_factory=lambda: str(uuid4()))

    # 基本信息
    name: str = ""                       # Agent名称 (PascalCase)
    display_name: str = ""               # 显示名称 (中文友好)
    slug: str = ""                       # URL友好标识符
    description: str = ""                # 描述
    long_description: str = ""           # 详细描述 (Markdown)

    # 分类和状态
    category: AgentCategory = AgentCategory.GENERAL
    status: AgentStatus = AgentStatus.DRAFT
    visibility: VisibilityLevel = VisibilityLevel.PRIVATE

    # 作者信息
    author_id: str = ""                  # 作者用户ID
    author_name: str = ""                # 作者显示名称
    organization: str = ""               # 所属组织

    # 版本信息
    current_version: str = "1.0.0"       # 当前版本号
    min_platform_version: str = "1.0.0"  # 最低平台版本要求

    # 技术信息
    python_version: str = "3.11+"        # Python版本要求
    dependencies: list[str] = field(default_factory=list)  # 依赖列表
    requires_llm: bool = False           # 是否需要LLM
    requires_tools: bool = False         # 是否需要工具系统

    # 统计信息
    download_count: int = 0              # 下载次数
    view_count: int = 0                  # 浏览次数
    fork_count: int = 0                  # 派生次数
    star_count: int = 0                  # 收藏次数

    # 评分信息
    rating_avg: float = 0.0              # 平均评分 (0-5)
    rating_count: int = 0                # 评分人数

    # 时间信息
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    published_at: Optional[datetime] = None

    # 元数据
    tags: list[str] = field(default_factory=list)
    featured: bool = False                # 是否精选
    verified: bool = False               # 是否官方认证


@dataclass
class AgentVersion:
    """
    Agent版本实体

    跟踪Agent的版本历史和变更记录。
    """
    # 主键
    id: str = field(default_factory=lambda: str(uuid4()))

    # 关联
    agent_id: str = ""                   # 关联Agent.id

    # 版本信息
    version: str = "1.0.0"               # 版本号 (语义化版本)
    changelog: str = ""                  # 变更日志

    # 代码信息
    module_path: str = ""                # 代码模块路径
    entry_point: str = ""                # 入口函数

    # 兼容性
    platform_version_min: str = ""       # 最低平台版本
    platform_version_max: str = ""       # 最高平台版本 (可选)

    # 状态
    status: AgentStatus = AgentStatus.DRAFT
    is_latest: bool = True               # 是否为最新版本

    # 统计
    download_count: int = 0

    # 时间
    created_at: datetime = field(default_factory=datetime.now)
    released_at: Optional[datetime] = None


@dataclass
class AgentCapability:
    """
    Agent能力实体

    定义Agent提供的具体能力。
    """
    # 主键
    id: str = field(default_factory=lambda: str(uuid4()))

    # 关联
    agent_id: str = ""                   # 关联Agent.id

    # 能力信息
    name: str = ""                       # 能力名称 (snake_case)
    display_name: str = ""               # 显示名称
    description: str = ""                # 描述

    # 输入输出
    input_types: list[str] = field(default_factory=list)
    output_types: list[str] = field(default_factory=list)

    # 性能
    estimated_time: float = 0.0          # 预估执行时间 (秒)
    max_concurrency: int = 1             # 最大并发数

    # 成本
    cost_per_call: float = 0.0           # 每次调用成本 (可选)
    requires_api_key: bool = False       # 是否需要API密钥


@dataclass
class AgentCategoryEntity:
    """
    Agent分类实体

    用于组织和浏览Agent。
    """
    # 主键
    id: str = field(default_factory=lambda: str(uuid4()))

    # 基本信息
    name: str = ""                       # 分类名称
    slug: str = ""                       # URL友好标识
    description: str = ""                # 描述
    icon: str = ""                       # 图标

    # 层级结构
    parent_id: Optional[str] = None      # 父分类ID
    level: int = 0                       # 层级深度
    order: int = 0                       # 排序

    # 统计
    agent_count: int = 0                 # 该分类下的Agent数量

    # 状态
    is_active: bool = True


@dataclass
class AgentReview:
    """
    Agent评价实体

    用户对Agent的评价和反馈。
    """
    # 主键
    id: str = field(default_factory=lambda: str(uuid4()))

    # 关联
    agent_id: str = ""                   # 关联Agent.id
    version_id: str = ""                 # 关联AgentVersion.id
    user_id: str = ""                    # 评价用户ID
    user_name: str = ""                  # 用户显示名称

    # 评价内容
    rating: int = 0                      # 评分 (1-5)
    title: str = ""                      # 评价标题
    content: str = ""                    # 评价内容

    # 标签
    tags: list[str] = field(default_factory=list)  # 评价标签 (如: "易于使用", "功能强大")

    # 审核
    status: ReviewStatus = ReviewStatus.PENDING
    admin_comment: str = ""              # 管理员评论

    # 时间
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class AgentRating:
    """
    Agent评分统计实体

    用于快速查询Agent的评分统计信息。
    """
    # 主键
    id: str = field(default_factory=lambda: str(uuid4()))

    # 关联
    agent_id: str = ""                   # 关联Agent.id

    # 评分统计
    total_reviews: int = 0               # 总评价数
    average_rating: float = 0.0          # 平均评分
    rating_distribution: dict = field(default_factory=dict)  # 评分分布 {1: count, 2: count, ...}

    # 细分统计
    ease_of_use: float = 0.0             # 易用性评分
    functionality: float = 0.0           # 功能性评分
    documentation: float = 0.0           # 文档质量评分
    performance: float = 0.0             # 性能评分

    # 趋势
    rating_trend: str = "stable"          # 评分趋势 (上升/下降/稳定)

    # 更新时间
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class AgentStatistics:
    """
    Agent使用统计实体

    记录Agent的使用情况和性能指标。
    """
    # 主键
    id: str = field(default_factory=lambda: str(uuid4()))

    # 关联
    agent_id: str = ""                   # 关联Agent.id
    version_id: str = ""                 # 关联AgentVersion.id (可选)

    # 使用统计
    total_calls: int = 0                 # 总调用次数
    successful_calls: int = 0            # 成功调用次数
    failed_calls: int = 0                # 失败调用次数
    success_rate: float = 0.0            # 成功率

    # 性能统计
    avg_execution_time: float = 0.0      # 平均执行时间 (秒)
    p95_execution_time: float = 0.0      # P95执行时间
    p99_execution_time: float = 0.0      # P99执行时间

    # 资源统计
    avg_memory_usage: float = 0.0        # 平均内存使用 (MB)
    peak_memory_usage: float = 0.0       # 峰值内存使用 (MB)

    # 时间范围
    date: str = ""                       # 统计日期 (YYYY-MM-DD)
    hour: Optional[int] = None           # 统计小时 (0-23)，可选

    # 更新时间
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class AgentDependency:
    """
    Agent依赖关系实体

    记录Agent之间的依赖关系。
    """
    # 主键
    id: str = field(default_factory=lambda: str(uuid4()))

    # 关联
    agent_id: str = ""                   # 依赖Agent
    depends_on_id: str = ""              # 被依赖的Agent

    # 关系类型
    dependency_type: str = "requires"    # requires, recommends, conflicts

    # 约束
    min_version: Optional[str] = None    # 最低版本要求
    max_version: Optional[str] = None    # 最高版本限制


@dataclass
class MarketplaceConfig:
    """
    市场配置实体

    市场平台的配置参数。
    """
    # 主键
    id: str = field(default_factory=lambda: str(uuid4()))

    # 配置项
    key: str = ""                        # 配置键
    value: str = ""                      # 配置值
    description: str = ""                # 描述

    # 类型
    value_type: str = "string"           # string, int, float, bool, json

    # 元数据
    category: str = ""                   # 配置分类
    is_public: bool = False              # 是否公开可见

    # 更新
    updated_at: datetime = field(default_factory=datetime.now)


# ==================== 辅助类 ====================

@dataclass
class AgentListItem:
    """
    Agent列表项

    用于列表API的轻量级返回对象。
    """
    id: str
    name: str
    display_name: str
    slug: str
    description: str
    category: str
    status: str
    author_name: str
    current_version: str

    # 统计
    download_count: int
    rating_avg: float
    rating_count: int

    # 标记
    featured: bool
    verified: bool

    # 时间
    updated_at: datetime


@dataclass
class AgentDetail:
    """
    Agent详细信息

    用于详情API的完整返回对象。
    """
    # 基本信息 (来自Agent)
    agent: Agent

    # 能力列表
    capabilities: list[AgentCapability]

    # 版本列表
    versions: list[AgentVersion]

    # 评分统计
    rating: AgentRating

    # 最新评价 (前5条)
    recent_reviews: list[AgentReview]

    # 统计信息
    statistics: AgentStatistics

    # 依赖关系
    dependencies: list[AgentDependency]
    dependents: list[AgentDependency]


@dataclass
class SearchFilters:
    """
    搜索过滤器

    用于Agent搜索的过滤条件。
    """
    # 关键词
    keyword: str = ""

    # 分类
    category: Optional[str] = None

    # 状态
    status: Optional[AgentStatus] = None

    # 作者
    author_id: Optional[str] = None

    # 标签
    tags: list[str] = field(default_factory=list)

    # 评分
    min_rating: Optional[float] = None

    # 技术要求
    requires_llm: Optional[bool] = None
    requires_tools: Optional[bool] = None

    # 排序
    sort_by: str = "updated_at"          # updated_at, download_count, rating_avg, name
    sort_order: str = "desc"             # asc, desc

    # 分页
    page: int = 1
    page_size: int = 20


# ==================== 工厂函数 ====================

def create_agent(
    name: str,
    display_name: str,
    description: str,
    category: AgentCategory = AgentCategory.GENERAL,
    author_id: str = "",
    author_name: str = "",
) -> Agent:
    """
    创建新Agent实例

    Args:
        name: Agent名称 (PascalCase)
        display_name: 显示名称
        description: 描述
        category: 类别
        author_id: 作者ID
        author_name: 作者名称

    Returns:
        Agent实例
    """
    from core.tools.unified_registry import to_snake_case

    agent = Agent(
        name=name,
        display_name=display_name,
        slug=to_snake_case(display_name),
        description=description,
        category=category,
        author_id=author_id,
        author_name=author_name,
    )
    return agent


def create_capability(
    agent_id: str,
    name: str,
    display_name: str,
    description: str,
    input_types: list[str],
    output_types: list[str],
    estimated_time: float = 5.0,
) -> AgentCapability:
    """
    创建Agent能力实例

    Args:
        agent_id: 关联的Agent ID
        name: 能力名称 (snake_case)
        display_name: 显示名称
        description: 描述
        input_types: 输入类型列表
        output_types: 输出类型列表
        estimated_time: 预估时间

    Returns:
        AgentCapability实例
    """
    return AgentCapability(
        agent_id=agent_id,
        name=name,
        display_name=display_name,
        description=description,
        input_types=input_types,
        output_types=output_types,
        estimated_time=estimated_time,
    )


# ==================== 数据库表创建SQL ====================

CREATE_TABLES_SQL = """
-- Agent市场平台数据库表创建脚本

-- 1. Agents表
CREATE TABLE IF NOT EXISTS agents (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    slug VARCHAR(200) UNIQUE NOT NULL,
    description TEXT,
    long_description TEXT,

    category VARCHAR(50) NOT NULL DEFAULT 'general',
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    visibility VARCHAR(20) NOT NULL DEFAULT 'private',

    author_id VARCHAR(100),
    author_name VARCHAR(200),
    organization VARCHAR(200),

    current_version VARCHAR(20) NOT NULL DEFAULT '1.0.0',
    min_platform_version VARCHAR(20) NOT NULL DEFAULT '1.0.0',

    python_version VARCHAR(20) NOT NULL DEFAULT '3.11+',
    dependencies JSONB DEFAULT '[]'::jsonb,
    requires_llm BOOLEAN DEFAULT FALSE,
    requires_tools BOOLEAN DEFAULT FALSE,

    download_count INTEGER DEFAULT 0,
    view_count INTEGER DEFAULT 0,
    fork_count INTEGER DEFAULT 0,
    star_count INTEGER DEFAULT 0,

    rating_avg DECIMAL(3,2) DEFAULT 0.00,
    rating_count INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    published_at TIMESTAMP,

    tags JSONB DEFAULT '[]'::jsonb,
    featured BOOLEAN DEFAULT FALSE,
    verified BOOLEAN DEFAULT FALSE,

    CHECK (rating_avg >= 0 AND rating_avg <= 5),
    CHECK (download_count >= 0),
    CHECK (view_count >= 0)
);

-- 2. Agent Versions表
CREATE TABLE IF NOT EXISTS agent_versions (
    id VARCHAR(36) PRIMARY KEY,
    agent_id VARCHAR(36) NOT NULL,
    version VARCHAR(20) NOT NULL,
    changelog TEXT,

    module_path VARCHAR(500),
    entry_point VARCHAR(200),

    platform_version_min VARCHAR(20),
    platform_version_max VARCHAR(20),

    status VARCHAR(20) DEFAULT 'draft',
    is_latest BOOLEAN DEFAULT TRUE,

    download_count INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    released_at TIMESTAMP,

    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
    UNIQUE (agent_id, version)
);

-- 3. Agent Capabilities表
CREATE TABLE IF NOT EXISTS agent_capabilities (
    id VARCHAR(36) PRIMARY KEY,
    agent_id VARCHAR(36) NOT NULL,
    name VARCHAR(100) NOT NULL,
    display_name VARCHAR(200),
    description TEXT,

    input_types JSONB DEFAULT '[]'::jsonb,
    output_types JSONB DEFAULT '[]'::jsonb,

    estimated_time DECIMAL(10,2) DEFAULT 0.00,
    max_concurrency INTEGER DEFAULT 1,

    cost_per_call DECIMAL(10,4) DEFAULT 0.0000,
    requires_api_key BOOLEAN DEFAULT FALSE,

    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
);

-- 4. Categories表
CREATE TABLE IF NOT EXISTS agent_categories (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    icon VARCHAR(100),

    parent_id VARCHAR(36),
    level INTEGER DEFAULT 0,
    order_index INTEGER DEFAULT 0,

    agent_count INTEGER DEFAULT 0,

    is_active BOOLEAN DEFAULT TRUE,

    FOREIGN KEY (parent_id) REFERENCES agent_categories(id) ON DELETE SET NULL
);

-- 5. Reviews表
CREATE TABLE IF NOT EXISTS agent_reviews (
    id VARCHAR(36) PRIMARY KEY,
    agent_id VARCHAR(36) NOT NULL,
    version_id VARCHAR(36),
    user_id VARCHAR(100) NOT NULL,
    user_name VARCHAR(200),

    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    title VARCHAR(200),
    content TEXT,

    tags JSONB DEFAULT '[]'::jsonb,

    status VARCHAR(20) DEFAULT 'pending',
    admin_comment TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
    UNIQUE (agent_id, user_id)
);

-- 6. Ratings表
CREATE TABLE IF NOT EXISTS agent_ratings (
    id VARCHAR(36) PRIMARY KEY,
    agent_id VARCHAR(36) NOT NULL UNIQUE,

    total_reviews INTEGER DEFAULT 0,
    average_rating DECIMAL(3,2) DEFAULT 0.00,
    rating_distribution JSONB DEFAULT '{}'::jsonb,

    ease_of_use DECIMAL(3,2) DEFAULT 0.00,
    functionality DECIMAL(3,2) DEFAULT 0.00,
    documentation DECIMAL(3,2) DEFAULT 0.00,
    performance DECIMAL(3,2) DEFAULT 0.00,

    rating_trend VARCHAR(20) DEFAULT 'stable',

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
);

-- 7. Statistics表
CREATE TABLE IF NOT EXISTS agent_statistics (
    id VARCHAR(36) PRIMARY KEY,
    agent_id VARCHAR(36) NOT NULL,
    version_id VARCHAR(36),

    total_calls INTEGER DEFAULT 0,
    successful_calls INTEGER DEFAULT 0,
    failed_calls INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2) DEFAULT 0.00,

    avg_execution_time DECIMAL(10,2) DEFAULT 0.00,
    p95_execution_time DECIMAL(10,2) DEFAULT 0.00,
    p99_execution_time DECIMAL(10,2) DEFAULT 0.00,

    avg_memory_usage DECIMAL(10,2) DEFAULT 0.00,
    peak_memory_usage DECIMAL(10,2) DEFAULT 0.00,

    date VARCHAR(10) NOT NULL,
    hour INTEGER,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
);

-- 8. Dependencies表
CREATE TABLE IF NOT EXISTS agent_dependencies (
    id VARCHAR(36) PRIMARY KEY,
    agent_id VARCHAR(36) NOT NULL,
    depends_on_id VARCHAR(36) NOT NULL,

    dependency_type VARCHAR(20) DEFAULT 'requires',
    min_version VARCHAR(20),
    max_version VARCHAR(20),

    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
    FOREIGN KEY (depends_on_id) REFERENCES agents(id) ON DELETE CASCADE,
    UNIQUE (agent_id, depends_on_id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_agents_category ON agents(category);
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
CREATE INDEX IF NOT EXISTS idx_agents_author ON agents(author_id);
CREATE INDEX IF NOT EXISTS idx_agents_slug ON agents(slug);
CREATE INDEX IF NOT EXISTS idx_agents_rating ON agents(rating_avg DESC);
CREATE INDEX IF NOT EXISTS idx_agents_updated ON agents(updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_reviews_agent ON agent_reviews(agent_id);
CREATE INDEX IF NOT EXISTS idx_reviews_user ON agent_reviews(user_id);
CREATE INDEX IF NOT EXISTS idx_reviews_rating ON agent_reviews(rating);

CREATE INDEX IF NOT EXISTS idx_stats_agent_date ON agent_statistics(agent_id, date);

-- 全文搜索索引
CREATE INDEX IF NOT EXISTS idx_agents_search ON agents USING gin(
    to_tsvector('simple',
        COALESCE(name, '') || ' ' ||
        COALESCE(display_name, '') || ' ' ||
        COALESCE(description, '') || ' ' ||
        COALESCE(long_description, '')
    )
);
"""


# ==================== 导出 ====================

__all__ = [
    # 枚举
    "AgentStatus",
    "AgentCategory",
    "VisibilityLevel",
    "ReviewStatus",

    # 实体
    "Agent",
    "AgentVersion",
    "AgentCapability",
    "AgentCategoryEntity",
    "AgentReview",
    "AgentRating",
    "AgentStatistics",
    "AgentDependency",
    "MarketplaceConfig",

    # 辅助类
    "AgentListItem",
    "AgentDetail",
    "SearchFilters",

    # 工厂函数
    "create_agent",
    "create_capability",

    # SQL
    "CREATE_TABLES_SQL",
]
