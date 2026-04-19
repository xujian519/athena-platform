# Athena 统一API网关适配层架构设计

## 1. 架构概述

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                     统一API网关 (8080)                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   认证中间件     │  │   限流中间件     │  │   日志中间件     │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                    适配层 (Adapter Layer)                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │  专利检索适配器   │  │  专利撰写适配器   │  │  技术分析适配器   │  │
│  │   (yunpat)      │  │  (patent-writer)│  │ (tech-analysis) │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                      现有服务层                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │  专利检索服务     │  │  专利撰写服务     │  │  技术分析服务     │  │
│  │ (yunpat-agent)   │  │  (新建服务)      │  │  (新建服务)      │  │
│  │    :8050        │  │     :8051      │  │     :8052      │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 适配层设计原则

1. **统一接口**: 所有服务通过统一的REST API接口访问
2. **协议转换**: 将不同服务的内部协议转换为标准HTTP/JSON
3. **数据映射**: 处理不同服务间的数据格式差异
4. **错误处理**: 统一的错误处理和响应格式
5. **监控日志**: 统一的请求追踪和性能监控

## 2. 核心适配器基类

### 2.1 基础适配器接口

```typescript
interface IBaseAdapter {
  name: string;
  version: string;
  healthCheck(): Promise<HealthStatus>;
  transformRequest(request: any): Promise<any>;
  transformResponse(response: any): Promise<any>;
  handleError(error: any): Promise<ErrorResponse>;
}

interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  details?: any;
}

interface ErrorResponse {
  success: false;
  error: {
    code: string;
    message: string;
    details?: any;
  };
  timestamp: string;
}
```

### 2.2 抽象适配器基类

```typescript
abstract class BaseAdapter implements IBaseAdapter {
  protected config: AdapterConfig;
  protected logger: Logger;
  protected metrics: MetricsCollector;

  constructor(config: AdapterConfig) {
    this.config = config;
    this.logger = new Logger(this.name);
    this.metrics = new MetricsCollector(this.name);
  }

  abstract get name(): string;
  abstract get version(): string;

  async healthCheck(): Promise<HealthStatus> {
    try {
      const startTime = Date.now();
      await this.pingService();
      const duration = Date.now() - startTime;
      
      return {
        status: duration < this.config.healthThreshold ? 'healthy' : 'degraded',
        timestamp: new Date().toISOString(),
        details: { responseTime: duration }
      };
    } catch (error) {
      return {
        status: 'unhealthy',
        timestamp: new Date().toISOString(),
        details: { error: error.message }
      };
    }
  }

  abstract transformRequest(request: any): Promise<any>;
  abstract transformResponse(response: any): Promise<any>;

  async handleError(error: any): Promise<ErrorResponse> {
    this.logger.error('Adapter error', { error: error.message, stack: error.stack });
    
    return {
      success: false,
      error: {
        code: error.code || 'ADAPTER_ERROR',
        message: error.message || 'Internal adapter error',
        details: this.config.debugMode ? error.stack : undefined
      },
      timestamp: new Date().toISOString()
    };
  }

  protected abstract pingService(): Promise<void>;
}
```

## 3. 服务适配器实现

### 3.1 专利检索服务适配器

```typescript
class PatentSearchAdapter extends BaseAdapter {
  get name(): string { return 'PatentSearchAdapter'; }
  get version(): string { return '1.0.0'; }

  constructor(config: AdapterConfig) {
    super(config);
  }

  protected async pingService(): Promise<void> {
    const response = await fetch(`${this.config.serviceUrl}/health`);
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.status}`);
    }
  }

  async transformRequest(request: PatentSearchRequest): Promise<any> {
    // 将统一请求格式转换为yunpat-agent格式
    return {
      title: request.query,
      abstract: request.description,
      technical_field: request.category,
      patent_id: request.patentId,
      type: request.type || 'invention',
      // 映射搜索参数
      search_params: {
        limit: request.limit || 20,
        offset: request.offset || 0,
        sort_by: request.sortBy || 'relevance',
        filters: request.filters || {}
      }
    };
  }

  async transformResponse(response: any): Promise<PatentSearchResponse> {
    // 将yunpat-agent响应转换为统一格式
    const data = await response.json();
    
    return {
      success: true,
      data: {
        patents: data.results?.map((patent: any) => ({
          id: patent.patent_id,
          title: patent.title,
          abstract: patent.abstract,
          publicationDate: patent.publication_date,
          applicants: patent.applicants || [],
          inventors: patent.inventors || [],
          classification: patent.classification || {},
          similarityScore: patent.similarity_score,
          relevanceScore: patent.relevance_score || 0.8
        })) || [],
        total: data.total_count || 0,
        page: Math.floor((data.offset || 0) / (data.limit || 20)) + 1,
        pageSize: data.limit || 20
      },
      metadata: {
        query: data.query,
        searchTime: data.search_time,
        sources: data.sources || ['yunpat']
      }
    };
  }
}
```

### 3.2 专利撰写服务适配器

```typescript
class PatentWritingAdapter extends BaseAdapter {
  get name(): string { return 'PatentWritingAdapter'; }
  get version(): string { return '1.0.0'; }

  constructor(config: AdapterConfig) {
    super(config);
  }

  protected async pingService(): Promise<void> {
    // 检查专利撰写服务状态
    const response = await fetch(`${this.config.serviceUrl}/health`);
    if (!response.ok) {
      throw new Error(`Patent writing service unavailable: ${response.status}`);
    }
  }

  async transformRequest(request: PatentWritingRequest): Promise<any> {
    // 将统一请求转换为专利撰写服务格式
    return {
      workflow_type: 'patent_drafting',
      case_data: {
        title: request.title,
        invention_type: request.inventionType,
        technical_features: request.technicalFeatures,
        technical_field: request.technicalField,
        technical_problem: request.technicalProblem,
        technical_solution: request.technicalSolution,
        claim_type: request.claimType || 'apparatus',
        language: request.language || 'zh-CN',
        jurisdiction: request.jurisdiction || 'CN'
      },
      options: {
        include_drawings: request.includeDrawings || false,
        include_examples: request.includeExamples || true,
        detail_level: request.detailLevel || 'standard'
      }
    };
  }

  async transformResponse(response: any): Promise<PatentWritingResponse> {
    const data = await response.json();
    
    return {
      success: true,
      data: {
        patentId: data.patent_id || generateId(),
        title: data.title,
        abstract: data.abstract,
        description: data.description,
        claims: data.claims || [],
        drawings: data.drawings || [],
        examples: data.examples || [],
        metadata: {
          generatedAt: data.generated_at,
          version: data.version || '1.0',
          language: data.language || 'zh-CN',
          jurisdiction: data.jurisdiction || 'CN'
        }
      },
      workflow: {
        workflowId: data.workflow_id,
        status: data.status,
        nextSteps: data.next_steps || []
      }
    };
  }
}
```

### 3.3 认证服务适配器

```typescript
class AuthenticationAdapter extends BaseAdapter {
  private jwtService: JWTService;
  private authService: AuthService;

  get name(): string { return 'AuthenticationAdapter'; }
  get version(): string { return '1.0.0'; }

  constructor(config: AdapterConfig) {
    super(config);
    this.jwtService = new JWTService(config.jwt);
    this.authService = new AuthService(config.auth);
  }

  protected async pingService(): Promise<void> {
    await this.authService.checkConnection();
  }

  async transformRequest(request: AuthRequest): Promise<any> {
    switch (request.type) {
      case 'login':
        return {
          username: request.username,
          password: request.password,
          remember_me: request.rememberMe || false
        };

      case 'register':
        return {
          username: request.username,
          email: request.email,
          password: request.password,
          profile: request.profile
        };

      case 'refresh':
        return {
          refresh_token: request.refreshToken
        };

      default:
        throw new Error(`Unsupported auth request type: ${request.type}`);
    }
  }

  async transformResponse(response: any): Promise<AuthResponse> {
    const data = await response.json();
    
    if (data.success) {
      return {
        success: true,
        data: {
          user: {
            id: data.user.id,
            username: data.user.username,
            email: data.user.email,
            roles: data.user.roles || [],
            profile: data.user.profile || {}
          },
          tokens: data.tokens ? {
            accessToken: data.tokens.access_token,
            refreshToken: data.tokens.refresh_token,
            expiresIn: data.tokens.expires_in
          } : undefined
        }
      };
    } else {
      return {
        success: false,
        error: {
          code: data.error_code || 'AUTH_ERROR',
          message: data.message || 'Authentication failed'
        }
      };
    }
  }

  async generateToken(user: User): Promise<string> {
    return this.jwtService.sign(user);
  }

  async verifyToken(token: string): Promise<User | null> {
    return this.jwtService.verify(token);
  }
}
```

### 3.4 技术分析服务适配器

```typescript
class TechnicalAnalysisAdapter extends BaseAdapter {
  get name(): string { return 'TechnicalAnalysisAdapter'; }
  get version(): string { return '1.0.0'; }

  constructor(config: AdapterConfig) {
    super(config);
  }

  protected async pingService(): Promise<void> {
    const response = await fetch(`${this.config.serviceUrl}/health`);
    if (!response.ok) {
      throw new Error(`Technical analysis service unavailable: ${response.status}`);
    }
  }

  async transformRequest(request: TechnicalAnalysisRequest): Promise<any> {
    switch (request.analysisType) {
      case 'novelty':
        return {
          patent_data: {
            title: request.title,
            abstract: request.abstract,
            claims: request.claims,
            technical_field: request.technicalField
          },
          analysis_options: {
            depth: request.depth || 'standard',
            databases: request.databases || ['CN', 'US', 'EP', 'WO'],
            date_range: request.dateRange
          }
        };

      case 'inventive_step':
        return {
          patent_data: {
            title: request.title,
            abstract: request.abstract,
            technical_problem: request.technicalProblem,
            technical_solution: request.technicalSolution,
            technical_features: request.technicalFeatures
          },
          analysis_options: {
            comparison_basis: request.comparisonBasis || 'closest_prior_art',
            technical_level: request.technicalLevel || 'ordinary_skilled_person'
          }
        };

      case 'patentability':
        return {
          patent_data: {
            title: request.title,
            abstract: request.abstract,
            claims: request.claims,
            technical_field: request.technicalField,
            invention_type: request.inventionType
          },
          analysis_options: {
            include_novelty: request.includeNovelty !== false,
            include_inventive_step: request.includeInventiveStep !== false,
            include_industrial_applicability: request.includeIndustrialApplicability !== false
          }
        };

      default:
        throw new Error(`Unsupported analysis type: ${request.analysisType}`);
    }
  }

  async transformResponse(response: any): Promise<TechnicalAnalysisResponse> {
    const data = await response.json();
    
    return {
      success: true,
      data: {
        analysisType: data.analysis_type,
        results: {
          novelty: data.novelty_analysis,
          inventiveStep: data.inventive_step_analysis,
          patentability: data.patentability_assessment,
          confidence: data.confidence_score || 0.8
        },
        priorArt: data.prior_art_references || [],
        recommendations: data.recommendations || [],
        report: data.detailed_report
      },
      metadata: {
        analysisTime: data.analysis_time,
        databasesSearched: data.databases_searched,
        analystVersion: data.analyst_version
      }
    };
  }
}
```

## 4. 统一数据模型

### 4.1 请求模型

```typescript
// 通用请求基类
interface BaseRequest {
  requestId?: string;
  timestamp?: string;
  userId?: string;
  context?: Record<string, any>;
}

// 专利搜索请求
interface PatentSearchRequest extends BaseRequest {
  query: string;
  description?: string;
  category?: string;
  patentId?: string;
  type?: 'invention' | 'utility' | 'design';
  limit?: number;
  offset?: number;
  sortBy?: 'relevance' | 'date' | 'applicant';
  filters?: {
    publicationDate?: {
      from?: string;
      to?: string;
    };
    applicants?: string[];
    inventors?: string[];
    classification?: string[];
  };
}

// 专利撰写请求
interface PatentWritingRequest extends BaseRequest {
  title: string;
  inventionType: string;
  technicalFeatures: string[];
  technicalField?: string;
  technicalProblem?: string;
  technicalSolution?: string;
  claimType?: 'apparatus' | 'method' | 'use';
  language?: string;
  jurisdiction?: string;
  includeDrawings?: boolean;
  includeExamples?: boolean;
  detailLevel?: 'basic' | 'standard' | 'detailed';
}

// 认证请求
interface AuthRequest extends BaseRequest {
  type: 'login' | 'register' | 'refresh' | 'logout';
  username?: string;
  email?: string;
  password?: string;
  refreshToken?: string;
  rememberMe?: boolean;
  profile?: Record<string, any>;
}

// 技术分析请求
interface TechnicalAnalysisRequest extends BaseRequest {
  analysisType: 'novelty' | 'inventive_step' | 'patentability';
  title: string;
  abstract?: string;
  claims?: string[];
  technicalField?: string;
  technicalProblem?: string;
  technicalSolution?: string;
  technicalFeatures?: string[];
  inventionType?: string;
  depth?: 'basic' | 'standard' | 'detailed';
  databases?: string[];
  dateRange?: {
    from?: string;
    to?: string;
  };
  comparisonBasis?: string;
  technicalLevel?: string;
  includeNovelty?: boolean;
  includeInventiveStep?: boolean;
  includeIndustrialApplicability?: boolean;
}
```

### 4.2 响应模型

```typescript
// 通用响应基类
interface BaseResponse {
  success: boolean;
  timestamp: string;
  requestId?: string;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
}

// 专利搜索响应
interface PatentSearchResponse extends BaseResponse {
  data?: {
    patents: Patent[];
    total: number;
    page: number;
    pageSize: number;
  };
  metadata?: {
    query: string;
    searchTime: number;
    sources: string[];
  };
}

// 专利撰写响应
interface PatentWritingResponse extends BaseResponse {
  data?: {
    patentId: string;
    title: string;
    abstract: string;
    description: string;
    claims: string[];
    drawings: any[];
    examples: any[];
    metadata: {
      generatedAt: string;
      version: string;
      language: string;
      jurisdiction: string;
    };
  };
  workflow?: {
    workflowId: string;
    status: string;
    nextSteps: string[];
  };
}

// 认证响应
interface AuthResponse extends BaseResponse {
  data?: {
    user: {
      id: string;
      username: string;
      email: string;
      roles: string[];
      profile: Record<string, any>;
    };
    tokens?: {
      accessToken: string;
      refreshToken: string;
      expiresIn: number;
    };
  };
}

// 技术分析响应
interface TechnicalAnalysisResponse extends BaseResponse {
  data?: {
    analysisType: string;
    results: {
      novelty?: any;
      inventiveStep?: any;
      patentability?: any;
      confidence: number;
    };
    priorArt: any[];
    recommendations: any[];
    report?: string;
  };
  metadata?: {
    analysisTime: number;
    databasesSearched: string[];
    analystVersion: string;
  };
}
```

## 5. 适配器工厂和注册表

### 5.1 适配器工厂

```typescript
class AdapterFactory {
  private static adapters = new Map<string, typeof BaseAdapter>();

  static register(name: string, adapterClass: typeof BaseAdapter): void {
    this.adapters.set(name, adapterClass);
  }

  static create(name: string, config: AdapterConfig): BaseAdapter {
    const AdapterClass = this.adapters.get(name);
    if (!AdapterClass) {
      throw new Error(`Adapter not found: ${name}`);
    }
    return new AdapterClass(config);
  }

  static getAvailableAdapters(): string[] {
    return Array.from(this.adapters.keys());
  }
}

// 注册所有适配器
AdapterFactory.register('patent-search', PatentSearchAdapter);
AdapterFactory.register('patent-writing', PatentWritingAdapter);
AdapterFactory.register('authentication', AuthenticationAdapter);
AdapterFactory.register('technical-analysis', TechnicalAnalysisAdapter);
```

### 5.2 适配器管理器

```typescript
class AdapterManager {
  private adapters = new Map<string, BaseAdapter>();
  private circuitBreakers = new Map<string, CircuitBreaker>();

  constructor(private config: ManagerConfig) {
    this.initializeAdapters();
  }

  private async initializeAdapters(): Promise<void> {
    for (const [name, adapterConfig] of Object.entries(this.config.adapters)) {
      const adapter = AdapterFactory.create(name, adapterConfig);
      this.adapters.set(name, adapter);
      
      // 初始化熔断器
      this.circuitBreakers.set(name, new CircuitBreaker({
        threshold: adapterConfig.circuitBreaker?.threshold || 5,
        timeout: adapterConfig.circuitBreaker?.timeout || 60000,
        resetTimeout: adapterConfig.circuitBreaker?.resetTimeout || 30000
      }));
    }
  }

  async getAdapter(name: string): Promise<BaseAdapter> {
    const adapter = this.adapters.get(name);
    if (!adapter) {
      throw new Error(`Adapter not found: ${name}`);
    }

    const circuitBreaker = this.circuitBreakers.get(name);
    if (!circuitBreaker?.allowRequest()) {
      throw new Error(`Circuit breaker open for adapter: ${name}`);
    }

    // 健康检查
    const health = await adapter.healthCheck();
    if (health.status === 'unhealthy') {
      circuitBreaker?.recordFailure();
      throw new Error(`Adapter unhealthy: ${name}`);
    }

    circuitBreaker?.recordSuccess();
    return adapter;
  }

  async healthCheckAll(): Promise<Record<string, HealthStatus>> {
    const results: Record<string, HealthStatus> = {};
    
    for (const [name, adapter] of this.adapters) {
      try {
        results[name] = await adapter.healthCheck();
      } catch (error) {
        results[name] = {
          status: 'unhealthy',
          timestamp: new Date().toISOString(),
          details: { error: error.message }
        };
      }
    }
    
    return results;
  }

  getAvailableAdapters(): string[] {
    return Array.from(this.adapters.keys());
  }
}
```

## 6. 配置文件

### 6.1 适配器配置

```json
{
  "adapters": {
    "patent-search": {
      "serviceUrl": "http://localhost:8050",
      "healthThreshold": 5000,
      "timeout": 30000,
      "retryAttempts": 3,
      "circuitBreaker": {
        "threshold": 5,
        "timeout": 60000,
        "resetTimeout": 30000
      },
      "debugMode": false
    },
    "patent-writing": {
      "serviceUrl": "http://localhost:8051",
      "healthThreshold": 8000,
      "timeout": 60000,
      "retryAttempts": 2,
      "circuitBreaker": {
        "threshold": 3,
        "timeout": 90000,
        "resetTimeout": 45000
      },
      "debugMode": false
    },
    "authentication": {
      "serviceUrl": "http://localhost:8052",
      "jwt": {
        "secret": "${JWT_SECRET}",
        "expiresIn": "24h",
        "issuer": "athena-platform"
      },
      "auth": {
        "provider": "local",
        "bcryptRounds": 12,
        "sessionTimeout": 3600
      },
      "healthThreshold": 3000,
      "timeout": 10000,
      "retryAttempts": 1,
      "debugMode": false
    },
    "technical-analysis": {
      "serviceUrl": "http://localhost:8053",
      "healthThreshold": 10000,
      "timeout": 120000,
      "retryAttempts": 2,
      "circuitBreaker": {
        "threshold": 4,
        "timeout": 120000,
        "resetTimeout": 60000
      },
      "debugMode": false
    }
  },
  "global": {
    "metricsEnabled": true,
    "tracingEnabled": true,
    "logLevel": "info"
  }
}
```

这个适配层架构设计提供了：

1. **统一接口**: 所有服务通过适配器提供一致的API接口
2. **可扩展性**: 易于添加新的服务适配器
3. **可靠性**: 包含熔断器、重试机制和健康检查
4. **监控**: 内置指标收集和日志记录
5. **配置管理**: 灵活的配置系统支持不同环境

现在我们可以基于这个设计创建具体的服务适配器实现。