# Agent市场平台设计文档

> **版本**: v1.0
> **日期**: 2026-04-21
> **状态**: Phase 3前期规划
> **作者**: Athena平台架构团队

---

## 📋 目录

1. [概述](#概述)
2. [核心功能设计](#核心功能设计)
3. [系统架构](#系统架构)
4. [数据模型](#数据模型)
5. [API设计](#api设计)
6. [前端界面设计](#前端界面设计)
7. [与现有系统集成](#与现有系统集成)
8. [实施计划](#实施计划)
9. [安全与合规](#安全与合规)
10. [监控与运维](#监控与运维)

---

## 概述

### 项目背景

Athena平台已拥有完善的Agent系统，包括：
- **统一Agent接口标准** (v1.0)
- **AgentRegistry** - Agent注册表
- **SubagentRegistry** - 子代理配置管理
- **Gateway服务发现** - 服务注册与路由

当前缺失一个统一的**Agent市场平台**，用于：
- 发现和浏览可用的Agent
- 共享和分发Agent
- 评价和反馈Agent质量
- 管理Agent的版本和生命周期

### 设计目标

1. **统一入口**: 提供统一的Agent发现和获取入口
2. **社区驱动**: 支持用户评价、反馈和贡献
3. **质量保证**: 通过评价、测试和认证机制保证Agent质量
4. **易于集成**: 与现有Gateway、AgentRegistry无缝集成
5. **可扩展性**: 支持未来Agent生态系统的扩展

### 核心价值

```
┌─────────────────────────────────────────────────────────┐
│              Agent市场平台核心价值                        │
├─────────────────────────────────────────────────────────┤
│  📦 Agent开发者          🎯 Agent使用者                  │
│  - 发布Agent            - 发现合适的Agent                │
│  - 管理版本             - 查看评价和评分                 │
│  - 获取反馈             - 一键安装                       │
│                        - 提交使用反馈                   │
└─────────────────────────────────────────────────────────┘
```

---

## 核心功能设计

### 1. Agent发现与浏览

#### 1.1 搜索功能
- **关键词搜索**: 按Agent名称、描述搜索
- **分类浏览**: 按领域分类（法律、IP管理、协调等）
- **标签筛选**: 按能力标签筛选
- **智能推荐**: 基于用户使用历史推荐

#### 1.2 Agent列表展示
```python
# Agent列表项结构
{
    "agent_id": "xiaona-professional-v5",
    "name": "小娜专业版V5",
    "description": "专利分析与法律专家",
    "category": "legal",
    "version": "5.0.0",
    "author": "Athena Team",
    "rating": 4.8,
    "downloads": 1520,
    "last_updated": "2026-04-15",
    "capabilities": ["patent_analysis", "legal_research"],
    "tags": ["patent", "legal", "analysis"]
}
```

#### 1.3 Agent详情页
- 基本信息（名称、描述、版本、作者）
- 能力列表
- 使用文档
- 评价和评分
- 下载统计
- 版本历史
- 依赖关系

### 2. Agent评价与评分系统

#### 2.1 评分维度
| 维度 | 权重 | 说明 |
|-----|-----|-----|
| 功能完整性 | 30% | Agent是否实现承诺的功能 |
| 代码质量 | 25% | 代码规范性、可维护性 |
| 文档质量 | 20% | 文档完整性、易理解性 |
| 稳定性 | 15% | 运行稳定性、错误处理 |
| 性能 | 10% | 响应速度、资源占用 |

#### 2.2 评价机制
```python
# 评价数据结构
{
    "review_id": "rev_001",
    "agent_id": "xiaona-professional-v5",
    "user_id": "user_123",
    "rating": {
        "overall": 4.5,
        "functionality": 5.0,
        "code_quality": 4.0,
        "documentation": 4.5,
        "stability": 5.0,
        "performance": 4.0
    },
    "comment": "功能强大，文档完善",
    "created_at": "2026-04-15T10:30:00Z",
    "helpful_count": 12
}
```

#### 2.3 质量认证徽章
- **官方认证** - 由Athena团队审核通过
- **社区推荐** - 高评分（>4.5）且高下载量
- **稳定性认证** - 通过稳定性测试
- **安全认证** - 通过安全审查

### 3. Agent分发与安装

#### 3.1 分发方式
1. **直接安装**: 从市场直接安装到本地
2. **Git仓库**: 从Git仓库克隆
3. **本地文件**: 从本地文件导入
4. **Docker镜像**: 通过Docker分发

#### 3.2 安装流程
```
用户选择Agent → 下载依赖 → 验证完整性 → 注册到AgentRegistry → 安装完成
```

#### 3.3 版本管理
- 语义化版本号 (SemVer)
- 版本切换和回滚
- 自动更新检查
- 变更日志 (CHANGELOG)

### 4. 用户反馈系统

#### 4.1 反馈类型
- Bug报告
- 功能请求
- 文档问题
- 性能问题

#### 4.2 反馈处理流程
```
提交反馈 → 自动分类 → 分配给维护者 → 处理反馈 → 通知用户 → 关闭
```

---

## 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        Agent市场平台                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Web前端     │  │  管理后台    │  │  CLI工具     │          │
│  │  (Vue.js)    │  │  (Vue.js)    │  │  (Python)    │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                   │
│         └─────────────────┼─────────────────┘                   │
│                           │                                     │
│         ┌─────────────────▼─────────────────┐                   │
│         │       RESTful API (FastAPI)       │                   │
│         └─────────────────┬─────────────────┘                   │
│                           │                                     │
│  ┌────────────────────────┼────────────────────────┐            │
│  │                        │                        │            │
│  ▼                        ▼                        ▼            │
│  ┌──────────┐      ┌──────────────┐      ┌──────────────┐      │
│  │ Agent    │      │  评价评分    │      │  用户账户    │      │
│  │ 目录服务 │      │  服务        │      │  服务        │      │
│  └──────────┘      └──────────────┘      └──────────────┘      │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    数据持久化层                          │   │
│  │  PostgreSQL  │  Redis  │  Qdrant  │  文件存储           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    集成层                                │   │
│  │  AgentRegistry  │  Gateway  │  认证服务                  │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 服务划分

#### 3.1 Agent目录服务 (Agent Catalog Service)
- Agent元数据管理
- 搜索和筛选
- 分类和标签管理

#### 3.2 评价评分服务 (Review & Rating Service)
- 评价提交和管理
- 评分计算
- 质量认证

#### 3.3 分发服务 (Distribution Service)
- Agent包管理
- 版本控制
- 下载统计

#### 3.4 用户账户服务 (User Account Service)
- 用户注册和认证
- 权限管理
- 用户画像

#### 3.5 反馈服务 (Feedback Service)
- 反馈收集
- 问题跟踪
- 通知系统

---

## 数据模型

### 核心实体

#### 4.1 Agent (代理)
```sql
CREATE TABLE agents (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    display_name VARCHAR(128) NOT NULL,
    description TEXT,
    category VARCHAR(32),
    author_id VARCHAR(64),
    repository_url VARCHAR(512),
    logo_url VARCHAR(512),
    current_version VARCHAR(16),
    status VARCHAR(16) DEFAULT 'active', -- active, deprecated, archived
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_category (category),
    INDEX idx_status (status),
    INDEX idx_author (author_id)
);
```

#### 4.2 AgentVersion (代理版本)
```sql
CREATE TABLE agent_versions (
    id VARCHAR(64) PRIMARY KEY,
    agent_id VARCHAR(64) NOT NULL,
    version VARCHAR(16) NOT NULL,
    changelog TEXT,
    package_url VARCHAR(512),
    checksum VARCHAR(64),
    min_platform_version VARCHAR(16),
    dependencies JSON,
    released_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
    UNIQUE KEY uk_agent_version (agent_id, version),
    INDEX idx_agent (agent_id)
);
```

#### 4.3 AgentCapability (代理能力)
```sql
CREATE TABLE agent_capabilities (
    id VARCHAR(64) PRIMARY KEY,
    agent_id VARCHAR(64) NOT NULL,
    name VARCHAR(64) NOT NULL,
    description TEXT,
    input_types JSON,
    output_types JSON,
    estimated_time FLOAT,
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
    INDEX idx_agent (agent_id),
    INDEX idx_name (name)
);
```

#### 4.4 AgentTag (代理标签)
```sql
CREATE TABLE agent_tags (
    agent_id VARCHAR(64) NOT NULL,
    tag VARCHAR(32) NOT NULL,
    PRIMARY KEY (agent_id, tag),
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
);
```

#### 4.5 Review (评价)
```sql
CREATE TABLE reviews (
    id VARCHAR(64) PRIMARY KEY,
    agent_id VARCHAR(64) NOT NULL,
    user_id VARCHAR(64) NOT NULL,
    rating_overall DECIMAL(2,1),
    rating_functionality DECIMAL(2,1),
    rating_code_quality DECIMAL(2,1),
    rating_documentation DECIMAL(2,1),
    rating_stability DECIMAL(2,1),
    rating_performance DECIMAL(2,1),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    helpful_count INT DEFAULT 0,
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
    INDEX idx_agent (agent_id),
    INDEX idx_user (user_id)
);
```

#### 4.6 Download (下载记录)
```sql
CREATE TABLE downloads (
    id VARCHAR(64) PRIMARY KEY,
    agent_id VARCHAR(64) NOT NULL,
    version VARCHAR(16),
    user_id VARCHAR(64),
    ip_address VARCHAR(45),
    user_agent VARCHAR(512),
    downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
    INDEX idx_agent (agent_id),
    INDEX idx_date (downloaded_at)
);
```

#### 4.7 Badge (徽章)
```sql
CREATE TABLE badges (
    agent_id VARCHAR(64) NOT NULL,
    badge_type VARCHAR(32) NOT NULL, -- official, community, stable, security
    awarded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    PRIMARY KEY (agent_id, badge_type),
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
);
```

### 数据模型关系图

```
┌─────────────┐     ┌─────────────────┐     ┌─────────────┐
│    User     │────<│     Review      │>────│   Agent     │
└─────────────┘     └─────────────────┘     └──────┬──────┘
                                                  │
                    ┌─────────────────────────────┼──────────────────┐
                    │                             │                  │
            ┌───────▼────────┐          ┌────────▼────────┐  ┌──────▼──────┐
            │ AgentVersion   │          │ AgentCapability │  │ AgentTag    │
            └────────────────┘          └─────────────────┘  └─────────────┘
                    │
            ┌───────▼────────┐
            │   Download     │
            └────────────────┘
```

---

## API设计

### RESTful API规范

#### 基础路径
- API基础URL: `/api/marketplace/v1/`
- 认证方式: Bearer Token (JWT)

#### 响应格式
```json
{
    "success": true,
    "data": {},
    "error": null,
    "meta": {
        "total": 100,
        "page": 1,
        "page_size": 20
    }
}
```

### 5.1 Agent相关API

#### GET /agents
获取Agent列表（支持搜索和筛选）

```python
# 请求参数
{
    "q": "patent",           # 搜索关键词
    "category": "legal",     # 分类筛选
    "tags": ["search"],      # 标签筛选
    "sort": "downloads",     # 排序方式
    "page": 1,               # 页码
    "page_size": 20          # 每页数量
}

# 响应
{
    "success": true,
    "data": [
        {
            "agent_id": "xiaona-professional-v5",
            "name": "小娜专业版V5",
            "description": "专利分析与法律专家",
            "category": "legal",
            "version": "5.0.0",
            "author": "Athena Team",
            "rating": 4.8,
            "downloads": 1520,
            "badges": ["official", "stable"]
        }
    ],
    "meta": {
        "total": 45,
        "page": 1,
        "page_size": 20
    }
}
```

#### GET /agents/{agent_id}
获取Agent详情

```python
# 响应
{
    "success": true,
    "data": {
        "agent_id": "xiaona-professional-v5",
        "name": "小娜专业版V5",
        "display_name": "小娜·天秤女神",
        "description": "专利法律专家，擅长专利分析、检索和撰写",
        "long_description": "详细描述...",
        "category": "legal",
        "version": "5.0.0",
        "author": {
            "id": "user_001",
            "name": "Athena Team",
            "avatar": "..."
        },
        "repository": "https://github.com/athena/xiaona",
        "license": "MIT",
        "homepage": "https://athena.ai/agents/xiaona",
        "rating": {
            "overall": 4.8,
            "functionality": 5.0,
            "code_quality": 4.5,
            "documentation": 5.0,
            "stability": 4.8,
            "performance": 4.5
        },
        "stats": {
            "downloads": 1520,
            "reviews": 45,
            "stars": 234
        },
        "badges": ["official", "stable", "community"],
        "capabilities": [
            {
                "name": "patent_search",
                "description": "专利检索",
                "input_types": ["query", "filters"],
                "output_types": ["patent_list"]
            }
        ],
        "tags": ["patent", "legal", "search", "analysis"],
        "versions": [
            {"version": "5.0.0", "released_at": "2026-04-15"},
            {"version": "4.2.0", "released_at": "2026-03-10"}
        ],
        "dependencies": {
            "min_platform_version": "2.0.0",
            "required_agents": [],
            "required_services": ["llm", "embedding"]
        },
        "install_command": "athena install xiaona-professional-v5",
        "created_at": "2026-01-15T00:00:00Z",
        "updated_at": "2026-04-15T00:00:00Z"
    }
}
```

#### POST /agents
发布新Agent（需要认证）

```python
# 请求
{
    "name": "my-custom-agent",
    "display_name": "我的自定义Agent",
    "description": "Agent描述",
    "category": "custom",
    "repository": "https://github.com/user/my-agent",
    "version": "1.0.0",
    "capabilities": [...],
    "tags": ["custom"]
}

# 响应
{
    "success": true,
    "data": {
        "agent_id": "my-custom-agent",
        "status": "pending_review"
    }
}
```

#### POST /agents/{agent_id}/install
安装Agent

```python
# 请求
{
    "version": "5.0.0"  # 可选，默认最新版
}

# 响应
{
    "success": true,
    "data": {
        "agent_id": "xiaona-professional-v5",
        "version": "5.0.0",
        "status": "installing",
        "install_id": "install_123"
    }
}
```

#### GET /agents/{agent_id}/versions
获取Agent版本列表

#### POST /agents/{agent_id}/reviews
提交评价（需要认证）

### 5.2 评价相关API

#### GET /agents/{agent_id}/reviews
获取Agent评价列表

```python
# 请求参数
{
    "sort": "helpful",  # helpful, recent, highest, lowest
    "page": 1,
    "page_size": 10
}

# 响应
{
    "success": true,
    "data": [
        {
            "review_id": "rev_001",
            "user": {
                "id": "user_123",
                "name": "张三",
                "avatar": "..."
            },
            "rating": {
                "overall": 5.0,
                "functionality": 5.0,
                "code_quality": 5.0
            },
            "comment": "非常实用的Agent！",
            "created_at": "2026-04-15T10:30:00Z",
            "helpful_count": 12,
            "is_helpful": false
        }
    ],
    "meta": {
        "total": 45,
        "average": 4.8
    }
}
```

#### POST /reviews/{review_id}/helpful
标记评价为有用

### 5.3 用户相关API

#### GET /users/me
获取当前用户信息

#### GET /users/me/installed-agents
获取已安装的Agent列表

#### GET /users/me/published-agents
获取发布的Agent列表

#### GET /users/me/reviews
获取我的评价列表

### 5.4 搜索API

#### GET /search
全文搜索

```python
# 请求参数
{
    "q": "专利检索 Agent",
    "type": "agent",  # agent, user, review
    "page": 1,
    "page_size": 20
}
```

#### GET /categories
获取所有分类

#### GET /tags
获取所有标签

---

## 前端界面设计

### 6.1 页面结构

#### 主要页面

| 页面 | 路径 | 功能 |
|-----|------|-----|
| 首页 | `/` | 展示热门Agent、推荐Agent |
| Agent列表 | `/agents` | 搜索、筛选、浏览Agent |
| Agent详情 | `/agents/:id` | Agent详细信息、评价 |
| 用户中心 | `/me` | 个人信息、已安装Agent |
| 发布Agent | `/publish` | 发布新Agent表单 |
| 管理后台 | `/admin` | Agent审核、用户管理 |

### 6.2 UI组件设计

#### Agent卡片组件
```vue
<AgentCard>
  <template #header>
    <AgentLogo :src="agent.logo" />
    <AgentBadges :badges="agent.badges" />
  </template>
  <template #body>
    <h3>{{ agent.display_name }}</h3>
    <p>{{ agent.description }}</p>
    <AgentTags :tags="agent.tags" />
  </template>
  <template #footer>
    <Rating :value="agent.rating" />
    <DownloadCount :count="agent.downloads" />
    <InstallButton :agent-id="agent.id" />
  </template>
</AgentCard>
```

#### 评价列表组件
```vue
<ReviewList>
  <ReviewFilter v-model="filter" />
  <Review v-for="review in reviews" :key="review.id">
    <ReviewerInfo :user="review.user" />
    <RatingBreakdown :rating="review.rating" />
    <ReviewComment>{{ review.comment }}</ReviewComment>
    <ReviewActions>
      <HelpfulButton :count="review.helpful_count" />
      <ReplyButton />
    </ReviewActions>
  </Review>
</ReviewList>
```

### 6.3 响应式设计

- **桌面端** (>1024px): 多列布局
- **平板端** (768-1024px): 两列布局
- **移动端** (<768px): 单列布局

---

## 与现有系统集成

### 7.1 与AgentRegistry集成

```python
# 安装Agent后自动注册到AgentRegistry
class MarketplaceInstaller:
    async def install_agent(self, agent_id: str, version: str) -> bool:
        # 1. 从市场下载Agent包
        package = await self._download_package(agent_id, version)

        # 2. 验证完整性
        if not self._verify_checksum(package):
            raise InstallationError("Checksum verification failed")

        # 3. 解压到本地
        install_path = await self._extract_package(package)

        # 4. 加载Agent类
        agent_class = self._load_agent_class(install_path)

        # 5. 注册到AgentRegistry
        from core.orchestration.agent_registry import get_agent_registry
        registry = get_agent_registry()
        registry.register(
            agent=agent_class(),
            phase=1,
            metadata={"source": "marketplace", "version": version}
        )

        return True
```

### 7.2 与Gateway集成

```go
// Gateway服务发现集成
// 已安装的Agent自动注册到Gateway服务注册表

func (s *MarketplaceService) RegisterAgentGateway(agentID string, config AgentConfig) error {
    instance := &ServiceInstance{
        ID:          agentID,
        ServiceName: "agent-" + agentID,
        Host:        config.Host,
        Port:        config.Port,
        Status:      "UP",
        Metadata: map[string]interface{}{
            "source":  "marketplace",
            "version": config.Version,
        },
    }

    s.gatewayRegistry.Register(instance)
    return nil
}
```

### 7.3 与认证系统集成

```python
# 复用现有认证系统
class MarketplaceAuth:
    def verify_token(self, token: str) -> User | None:
        # 调用Gateway认证服务
        response = requests.post(
            f"{GATEWAY_URL}/auth/verify",
            headers={"Authorization": f"Bearer {token}"}
        )
        return User.from_dict(response.json())
```

---

## 实施计划

### Phase 3.1: 基础设施 (Week 1-2)

**目标**: 搭建市场平台基础架构

| 任务 | 描述 | 交付物 |
|-----|------|--------|
| 数据库设计 | 设计并创建数据库表 | SQL脚本 |
| 后端框架 | 搭建FastAPI项目结构 | 项目框架 |
| 基础API | 实现Agent列表和详情API | API文档 |
| 前端框架 | 搭建Vue.js项目 | 项目框架 |

### Phase 3.2: 核心功能 (Week 3-5)

**目标**: 实现市场平台核心功能

| 任务 | 描述 | 交付物 |
|-----|------|--------|
| 搜索功能 | Agent搜索和筛选 | 搜索API |
| 评价系统 | 评价提交和展示 | 评价API + UI |
| 分发功能 | Agent包管理和下载 | 分发服务 |
| 安装集成 | 与AgentRegistry集成 | 安装器 |

### Phase 3.3: 高级功能 (Week 6-7)

**目标**: 实现高级功能和用户体验优化

| 任务 | 描述 | 交付物 |
|-----|------|--------|
| 版本管理 | Agent版本控制 | 版本API |
| 质量认证 | 徽章系统和审核流程 | 认证系统 |
| 用户中心 | 个人中心和仪表板 | 用户中心UI |
| CLI工具 | 命令行安装工具 | CLI包 |

### Phase 3.4: 集成测试 (Week 8)

**目标**: 全面测试和优化

| 任务 | 描述 | 交付物 |
|-----|------|--------|
| 集成测试 | 端到端测试 | 测试报告 |
| 性能优化 | API响应时间优化 | 性能报告 |
| 安全审计 | 安全漏洞扫描 | 审计报告 |
| 文档完善 | 用户文档和API文档 | 文档站点 |

### Phase 3.5: 上线发布 (Week 9)

**目标**: 正式上线

| 任务 | 描述 | 交付物 |
|-----|------|--------|
| 灰度发布 | 10% → 50% → 100% | 发布计划 |
| 监控配置 | 配置监控和告警 | 监控面板 |
| 用户培训 | 使用培训和FAQ | 培训材料 |

---

## 安全与合规

### 8.1 安全措施

#### Agent审核机制
- **静态代码分析**: 扫描潜在安全问题
- **沙箱执行**: 在隔离环境中测试
- **依赖检查**: 检查依赖的安全性

#### 访问控制
- **认证**: JWT Token认证
- **授权**: 基于角色的访问控制 (RBAC)
- **API限流**: 防止滥用

#### 数据保护
- **敏感数据加密**: 数据库加密存储
- **传输加密**: HTTPS/TLS
- **日志脱敏**: 日志中隐藏敏感信息

### 8.2 内容审核

#### Agent审核流程
```
提交Agent → 自动扫描 → 人工审核 → 发布/拒绝
```

#### 审核检查项
- [ ] 无恶意代码
- [ ] 无版权问题
- [ ] 符合接口标准
- [ ] 文档完整
- [ ] 通过基础测试

### 8.3 隐私保护

- 用户数据最小化收集
- 提供数据导出功能
- 支持账户注销
- 符合GDPR要求

---

## 监控与运维

### 9.1 监控指标

#### 业务指标
- Agent下载量
- 活跃用户数
- 评价提交量
- 安装成功率

#### 技术指标
- API响应时间
- 错误率
- 数据库连接数
- 缓存命中率

### 9.2 告警规则

| 告警项 | 阈值 | 级别 |
|-------|------|------|
| API错误率 | >5% | 高 |
| API响应时间 | >1s | 中 |
| 数据库连接数 | >80% | 中 |
| 磁盘使用率 | >90% | 高 |

### 9.3 日志管理

```python
# 结构化日志示例
logger.info(
    "agent_downloaded",
    extra={
        "agent_id": agent_id,
        "user_id": user_id,
        "version": version,
        "ip_address": request.client.host,
    }
)
```

---

## 附录

### A. Agent元数据规范

```yaml
# agent.yaml - Agent元数据文件
name: my-custom-agent
display_name: 我的自定义Agent
version: 1.0.0
description: Agent描述
long_description: |
  详细描述...
  可以是多行。

category: custom
tags:
  - custom
  - example

author:
  name: Your Name
  email: your@email.com

repository: https://github.com/user/my-agent
license: MIT
homepage: https://your-site.com

capabilities:
  - name: my_capability
    description: 我的能力
    input_types:
      - text
    output_types:
      - json
    estimated_time: 1.0

dependencies:
  min_platform_version: 2.0.0
  required_agents: []
  required_services:
    - llm

install:
  type: pip  # pip, git, docker
  location: .
  entry_point: core.agents.my_agent:MyAgent
```

### B. 技术栈选择

| 层级 | 技术 | 理由 |
|-----|------|-----|
| 后端 | FastAPI | 高性能、异步支持、自动文档 |
| 前端 | Vue.js 3 | 组件化、生态完善 |
| 数据库 | PostgreSQL | 关系型、JSON支持 |
| 缓存 | Redis | 高性能缓存 |
| 搜索 | Qdrant | 向量搜索 + 关键词搜索 |
| 容器 | Docker | 标准化部署 |

### C. 相关文档

- [统一Agent接口标准](./UNIFIED_AGENT_INTERFACE_STANDARD.md)
- [Agent通信协议规范](./AGENT_COMMUNICATION_PROTOCOL_SPEC.md)
- [Gateway架构文档](../../gateway-unified/README.md)

---

**文档版本**: v1.0
**最后更新**: 2026-04-21
**维护者**: Athena平台架构团队
