# API网关接口映射表和数据转换规则

## 1. 统一API接口规范

### 1.1 通用响应格式

```json
{
  "success": boolean,
  "data": object | null,
  "error": {
    "code": string,
    "message": string,
    "details": object | null
  } | null,
  "metadata": {
    "adapter": string,
    "timestamp": string,
    "version": string,
    "requestId": string | null
  }
}
```

### 1.2 通用请求头

```http
Content-Type: application/json
Authorization: Bearer <token> (可选)
X-Request-ID: <uuid> (可选)
X-Client-Version: <version> (可选)
```

## 2. 服务接口映射表

### 2.1 专利检索服务 (yunpat-agent)

| 统一API路径 | 原服务路径 | HTTP方法 | 适配器 | 描述 |
|------------|------------|----------|--------|------|
| `/api/v1/patents/search` | `/api/v2/patent/search` | POST | PatentSearchAdapter | 专利搜索 |
| `/api/v1/patents/analyze` | `/api/v2/patent/analyze` | POST | PatentSearchAdapter | 专利分析 |
| `/api/v1/patents/rules` | `/api/v2/patent/rules` | GET | PatentSearchAdapter | 获取专利规则 |
| `/api/v1/patents/chat` | `/api/v2/patent/chat` | POST | PatentSearchAdapter | AI智能体对话 |
| `/api/v1/patents/optimize-claim` | `/api/v2/patent/optimize_claim` | POST | PatentSearchAdapter | 优化权利要求 |

### 2.2 专利撰写服务

| 统一API路径 | 原服务路径 | HTTP方法 | 适配器 | 描述 |
|------------|------------|----------|--------|------|
| `/api/v1/patents/drafts` | `/api/v1/patent-writing/draft` | POST | PatentWritingAdapter | 创建专利草稿 |
| `/api/v1/patents/claims/generate` | `/api/v1/patent-writing/claims/generate` | POST | PatentWritingAdapter | 生成权利要求 |
| `/api/v1/patents/description/generate` | `/api/v1/patent-writing/description/generate` | POST | PatentWritingAdapter | 生成说明书 |
| `/api/v1/patents/optimize` | `/api/v1/patent-writing/optimize` | POST | PatentWritingAdapter | 优化专利内容 |
| `/api/v1/patents/compliance/check` | `/api/v1/patent-writing/compliance/check` | POST | PatentWritingAdapter | 检查专利合规性 |
| `/api/v1/patents/workflows/{workflowId}/status` | `/api/v1/patent-writing/workflow/{id}/status` | GET | PatentWritingAdapter | 获取工作流状态 |
| `/api/v1/patents/workflows/{workflowId}/update` | `/api/v1/patent-writing/workflow/{id}/update` | POST | PatentWritingAdapter | 更新工作流 |
| `/api/v1/patents/export` | `/api/v1/patent-writing/export` | POST | PatentWritingAdapter | 导出专利文档 |
| `/api/v1/patents/templates` | `/api/v1/patent-writing/templates` | GET | PatentWritingAdapter | 获取专利模板 |

### 2.3 认证服务

| 统一API路径 | 原服务路径 | HTTP方法 | 适配器 | 描述 |
|------------|------------|----------|--------|------|
| `/api/v1/auth/login` | 本地处理 | POST | AuthenticationAdapter | 用户登录 |
| `/api/v1/auth/register` | 本地处理 | POST | AuthenticationAdapter | 用户注册 |
| `/api/v1/auth/refresh` | 本地处理 | POST | AuthenticationAdapter | 刷新令牌 |
| `/api/v1/auth/verify` | 本地处理 | POST | AuthenticationAdapter | 验证令牌 |
| `/api/v1/auth/logout` | 本地处理 | POST | AuthenticationAdapter | 用户登出 |
| `/api/v1/auth/profile` | 本地处理 | GET | AuthenticationAdapter | 获取用户档案 |

### 2.4 技术分析服务

| 统一API路径 | 原服务路径 | HTTP方法 | 适配器 | 描述 |
|------------|------------|----------|--------|------|
| `/api/v1/analysis/novelty` | `/api/v1/technical-analysis/novelty` | POST | TechnicalAnalysisAdapter | 新颖性分析 |
| `/api/v1/analysis/inventive-step` | `/api/v1/technical-analysis/inventive-step` | POST | TechnicalAnalysisAdapter | 创造性分析 |
| `/api/v1/analysis/patentability` | `/api/v1/technical-analysis/patentability` | POST | TechnicalAnalysisAdapter | 可专利性分析 |
| `/api/v1/analysis/freedom-to-operate` | `/api/v1/technical-analysis/freedom-to-operate` | POST | TechnicalAnalysisAdapter | 自由实施分析 |
| `/api/v1/analysis/validity` | `/api/v1/technical-analysis/validity` | POST | TechnicalAnalysisAdapter | 专利有效性分析 |
| `/api/v1/analysis/infringement` | `/api/v1/technical-analysis/infringement` | POST | TechnicalAnalysisAdapter | 侵权风险分析 |
| `/api/v1/analysis/{analysisId}/status` | `/api/v1/technical-analysis/analysis/{id}/status` | GET | TechnicalAnalysisAdapter | 获取分析状态 |
| `/api/v1/analysis/{analysisId}/result` | `/api/v1/technical-analysis/analysis/{id}/result` | GET | TechnicalAnalysisAdapter | 获取分析结果 |
| `/api/v1/analysis/databases` | `/api/v1/technical-analysis/databases` | GET | TechnicalAnalysisAdapter | 获取支持的数据库 |
| `/api/v1/analysis/templates` | `/api/v1/technical-analysis/templates` | GET | TechnicalAnalysisAdapter | 获取分析模板 |

## 3. 数据转换规则

### 3.1 专利检索服务转换规则

#### 请求转换 (统一 → yunpat-agent)

```python
# 统一请求格式
{
  "query": "人工智能",
  "description": "AI相关专利",
  "category": "计算机软件",
  "limit": 20,
  "offset": 0,
  "sortBy": "relevance",
  "filters": {
    "publicationDate": {
      "from": "2020-01-01",
      "to": "2023-12-31"
    },
    "applicants": ["苹果公司", "微软公司"],
    "classification": ["G06N"]
  }
}

# 转换后的yunpat-agent格式
{
  "title": "人工智能",
  "abstract": "AI相关专利",
  "technical_field": "计算机软件",
  "limit": 20,
  "offset": 0,
  "sort_by": "relevance",
  "publication_date_from": "2020-01-01",
  "publication_date_to": "2023-12-31",
  "applicants": ["苹果公司", "微软公司"],
  "classification": ["G06N"]
}
```

#### 响应转换 (yunpat-agent → 统一)

```python
# yunpat-agent响应格式
{
  "results": [
    {
      "patent_id": "CN123456789A",
      "title": "人工智能专利",
      "abstract": "一种AI技术",
      "publication_date": "2023-01-01",
      "applicants": ["某公司"],
      "inventors": ["张三"],
      "classification": {"ipc": ["G06N"]},
      "similarity_score": 0.85,
      "relevance_score": 0.90
    }
  ],
  "total_count": 100,
  "query": "人工智能",
  "search_time": 1.5
}

# 转换后的统一格式
{
  "success": true,
  "data": {
    "patents": [
      {
        "id": "CN123456789A",
        "title": "人工智能专利",
        "abstract": "一种AI技术",
        "publicationDate": "2023-01-01",
        "applicants": ["某公司"],
        "inventors": ["张三"],
        "classification": {"ipc": ["G06N"]},
        "similarityScore": 0.85,
        "relevanceScore": 0.90
      }
    ],
    "total": 100,
    "page": 1,
    "pageSize": 20
  },
  "metadata": {
    "query": "人工智能",
    "searchTime": 1.5,
    "sources": ["yunpat"],
    "adapter": "patent-search",
    "timestamp": "2023-12-20T10:30:00Z"
  }
}
```

### 3.2 专利撰写服务转换规则

#### 请求转换 (统一 → 撰写服务)

```python
# 统一请求格式
{
  "title": "基于AI的专利撰写系统",
  "inventionType": "invention",
  "technicalFeatures": [
    "人工智能算法",
    "自然语言处理",
    "专利模板引擎"
  ],
  "technicalField": "计算机软件",
  "technicalProblem": "撰写效率低",
  "technicalSolution": "AI自动生成",
  "claimType": "method",
  "language": "zh-CN",
  "jurisdiction": "CN",
  "includeExamples": true,
  "detailLevel": "standard"
}

# 转换后的撰写服务格式
{
  "title": "基于AI的专利撰写系统",
  "invention_type": "invention",
  "technical_features": [
    "人工智能算法",
    "自然语言处理",
    "专利模板引擎"
  ],
  "technical_field": "计算机软件",
  "technical_problem": "撰写效率低",
  "technical_solution": "AI自动生成",
  "claim_type": "method",
  "language": "zh-CN",
  "jurisdiction": "CN",
  "options": {
    "include_examples": true,
    "detail_level": "standard"
  },
  "action": "create_draft"
}
```

### 3.3 认证服务转换规则

#### 请求转换 (统一 → 认证服务)

```python
# 统一登录请求格式
{
  "type": "login",
  "username": "user123",
  "password": "pass123",
  "rememberMe": true
}

# 转换后的认证处理格式
{
  "username": "user123",
  "password": "pass123",
  "remember_me": true
}

# 统一注册请求格式
{
  "type": "register",
  "username": "newuser",
  "email": "user@example.com",
  "password": "newpass123",
  "roles": ["user"],
  "profile": {
    "firstName": "张",
    "lastName": "三"
  }
}

# 转换后的认证处理格式
{
  "username": "newuser",
  "email": "user@example.com",
  "password": "newpass123",
  "roles": ["user"],
  "profile": {
    "firstName": "张",
    "lastName": "三"
  }
}
```

#### 响应转换 (认证服务 → 统一)

```python
# 认证服务内部用户数据
{
  "id": "user123",
  "username": "user123",
  "email": "user@example.com",
  "password_hash": "hashed_password",
  "roles": ["user"],
  "profile": {
    "firstName": "张",
    "lastName": "三"
  },
  "created_at": "2023-01-01T00:00:00Z",
  "last_login": "2023-12-20T10:30:00Z",
  "is_active": true
}

# 转换后的统一响应格式
{
  "success": true,
  "data": {
    "user": {
      "id": "user123",
      "username": "user123",
      "email": "user@example.com",
      "roles": ["user"],
      "profile": {
        "firstName": "张",
        "lastName": "三"
      }
    },
    "tokens": {
      "accessToken": "jwt_access_token",
      "refreshToken": "jwt_refresh_token",
      "expiresIn": 86400
    }
  },
  "metadata": {
    "adapter": "authentication",
    "timestamp": "2023-12-20T10:30:00Z"
  }
}
```

### 3.4 技术分析服务转换规则

#### 请求转换 (统一 → 分析服务)

```python
# 统一可专利性分析请求格式
{
  "analysisType": "patentability",
  "title": "AI专利分析系统",
  "abstract": "使用AI技术分析专利",
  "claims": ["一种分析方法", "包括机器学习"],
  "technicalField": "人工智能",
  "inventionType": "invention",
  "depth": "standard",
  "databases": ["CN", "US", "EP"],
  "includeNovelty": true,
  "includeInventiveStep": true,
  "includeIndustrialApplicability": true
}

# 转换后的分析服务格式
{
  "analysis_type": "patentability",
  "patent_data": {
    "title": "AI专利分析系统",
    "abstract": "使用AI技术分析专利",
    "claims": ["一种分析方法", "包括机器学习"],
    "technical_field": "人工智能",
    "invention_type": "invention"
  },
  "analysis_options": {
    "depth": "standard",
    "databases": ["CN", "US", "EP"],
    "include_novelty": true,
    "include_inventive_step": true,
    "include_industrial_applicability": true
  }
}
```

## 4. 错误码映射

### 4.1 通用错误码

| 错误码 | HTTP状态码 | 描述 |
|--------|----------|------|
| INVALID_REQUEST | 400 | 请求格式无效 |
| MISSING_PARAMETER | 400 | 缺少必需参数 |
| INVALID_PARAMETER | 400 | 参数值无效 |
| UNAUTHORIZED | 401 | 未授权访问 |
| FORBIDDEN | 403 | 禁止访问 |
| NOT_FOUND | 404 | 资源不存在 |
| METHOD_NOT_ALLOWED | 405 | 方法不允许 |
| RATE_LIMIT_EXCEEDED | 429 | 请求频率超限 |
| INTERNAL_ERROR | 500 | 内部服务器错误 |
| SERVICE_UNAVAILABLE | 503 | 服务不可用 |

### 4.2 业务错误码

| 服务 | 错误码 | HTTP状态码 | 描述 |
|------|--------|----------|------|
| 专利检索 | SEARCH_FAILED | 500 | 搜索失败 |
| 专利检索 | INVALID_QUERY | 400 | 查询条件无效 |
| 专利撰写 | DRAFT_CREATION_FAILED | 500 | 草稿创建失败 |
| 专利撰写 | WORKFLOW_NOT_FOUND | 404 | 工作流不存在 |
| 认证 | INVALID_CREDENTIALS | 401 | 用户名或密码错误 |
| 认证 | TOKEN_EXPIRED | 401 | 令牌已过期 |
| 认证 | USER_NOT_FOUND | 404 | 用户不存在 |
| 技术分析 | ANALYSIS_FAILED | 500 | 分析失败 |
| 技术分析 | UNSUPPORTED_ANALYSIS_TYPE | 400 | 不支持的分析类型 |

## 5. 配置映射

### 5.1 服务端口配置

```yaml
# 统一配置
services:
  patent-search:
    port: 8050
    health_path: /health
  patent-writing:
    port: 8051
    health_path: /health
  authentication:
    port: 8052
    health_path: /health
  technical-analysis:
    port: 8053
    health_path: /health

# 网关配置
gateway:
  port: 8080
  routes:
    - path: /api/v1/patents/*
      service: patent-search
      timeout: 30000
    - path: /api/v1/auth/*
      service: authentication
      timeout: 10000
    - path: /api/v1/analysis/*
      service: technical-analysis
      timeout: 120000
```

### 5.2 适配器配置映射

```json
{
  "patent-search": {
    "service_url": "http://localhost:8050",
    "health_threshold": 5000,
    "timeout": 30000,
    "retry_attempts": 3,
    "circuit_breaker": {
      "threshold": 5,
      "timeout": 60000,
      "reset_timeout": 30000
    }
  },
  "patent-writing": {
    "service_url": "http://localhost:8051",
    "health_threshold": 8000,
    "timeout": 60000,
    "retry_attempts": 2,
    "circuit_breaker": {
      "threshold": 3,
      "timeout": 90000,
      "reset_timeout": 45000
    }
  },
  "authentication": {
    "service_url": "http://localhost:8052",
    "health_threshold": 3000,
    "timeout": 10000,
    "retry_attempts": 1,
    "circuit_breaker": {
      "threshold": 5,
      "timeout": 30000,
      "reset_timeout": 15000,
      "secret": "jwt-secret-key",
      "algorithm": "HS256",
      "expires_in": 86400,
      "bcrypt_rounds": 12
    }
  },
  "technical-analysis": {
    "service_url": "http://localhost:8053",
    "health_threshold": 10000,
    "timeout": 120000,
    "retry_attempts": 2,
    "circuit_breaker": {
      "threshold": 4,
      "timeout": 120000,
      "reset_timeout": 60000
    }
  }
}
```

## 6. 数据验证规则

### 6.1 通用验证规则

```python
# 字符串验证
string_validation = {
    "min_length": 1,
    "max_length": 1000,
    "required": False,
    "pattern": "^[\\s\\S]*$"
}

# 数值验证
number_validation = {
    "type": "integer",
    "min_value": 0,
    "max_value": 1000000,
    "required": False
}

# 日期验证
date_validation = {
    "format": "YYYY-MM-DD",
    "required": False,
    "min_date": "1900-01-01",
    "max_date": "2100-12-31"
}

# 分页验证
pagination_validation = {
    "limit": {"min": 1, "max": 100, "default": 20},
    "offset": {"min": 0, "max": 10000, "default": 0}
}
```

### 6.2 业务特定验证

```python
# 专利搜索验证
patent_search_validation = {
    "query": {
        "required": True,
        "min_length": 2,
        "max_length": 500
    },
    "limit": {"min": 1, "max": 100},
    "sortBy": {
        "enum": ["relevance", "date", "applicant"],
        "default": "relevance"
    }
}

# 用户认证验证
auth_validation = {
    "username": {
        "required": True,
        "min_length": 3,
        "max_length": 50,
        "pattern": "^[a-zA-Z0-9_]+$"
    },
    "email": {
        "required": True,
        "pattern": "^[\\w\\.-]+@[\\w\\.-]+\\.[a-zA-Z]{2,}$"
    },
    "password": {
        "required": True,
        "min_length": 8,
        "max_length": 128,
        "pattern": "^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d)[a-zA-Z\\d@$!%*?&]{8,}$"
    }
}

# 专利分析验证
analysis_validation = {
    "title": {
        "required": True,
        "min_length": 5,
        "max_length": 200
    },
    "analysisType": {
        "required": True,
        "enum": ["novelty", "inventive_step", "patentability", "freedom_to_operate", "validity", "infringement"]
    },
    "depth": {
        "enum": ["basic", "standard", "detailed"],
        "default": "standard"
    }
}
```

这个接口映射表和数据转换规则文档提供了完整的API网关集成指南，确保所有服务能够统一接入并正常工作。