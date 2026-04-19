#!/usr/bin/env python3
"""
OpenAPI文档配置模块

为小诺统一网关提供完整的OpenAPI/Swagger文档配置
"""

from __future__ import annotations
import logging
from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi as _get_openapi

logger = logging.getLogger(__name__)


# =============================================================================
# OpenAPI配置常量
# =============================================================================

API_TITLE = "小诺统一网关 API"
API_VERSION = "5.0.0"
API_DESCRIPTION = """
# 小诺统一网关 v5.0

> Athena平台智能体协调中心 - 统一入口和智能路由

## 概述

小诺统一网关是Athena平台的核心调度中心,负责:

- **意图识别与路由**: 智能识别用户意图并路由到合适的智能体
- **能力编排与调度**: 协调17个专业能力模块的调用
- **多智能体协作**: 统一管理小娜、小宸等专业智能体
- **性能优化**: 集成v4.0 + Phase 1/2/3优化模块

## 能力列表

### 基础能力 (13个)
1. **小娜能力** - 专利法律专业服务
2. **通用助手** - 日常对话和信息查询
3. **Python编程** - Python代码编写和调试
4. **数据分析** - 数据处理和可视化
5. **AI写作** - 文档撰写和编辑
6. **翻译服务** - 多语言翻译
7. **数学计算** - 数学问题求解
8. **总结归纳** - 内容摘要生成
9. **知识检索** - 知识库查询
10. **创意生成** - 创意内容创作
11. **代码审查** - 代码质量检查
12. **技术咨询** - 技术问题解答
13. **工具调用** - 外部工具集成

### 优化模块 (4个)
- **v4.0**: 不确定性量化、命题响应、响应验证
- **Phase 1**: 意图评分、参数验证、执行引擎、智能拒绝
- **Phase 2**: BERT分类器、工具图谱、错误处理、参数提取、混沌工程
- **Phase 3**: 自主学习、多模态理解、智能体融合、预测维护、性能监控

### Phase 2扩展模块 (6个)
- **任务编排引擎** - DAG工作流管理
- **异步处理优化** - 优先级任务队列
- **知识图谱增强** - 实体关系检索
- **性能分析工具** - 终端友好监控
- **个性化响应** - 用户偏好自适应
- **多模态理解** - 文件系统集成

## 智能体架构

```
┌─────────────────────────────────────────────────────────┐
│  小诺统一网关 (8100) - 平台总调度官                      │
│  - 意图识别和路由                                         │
│  - 能力编排和调度                                         │
└─────────────────────────────────────────────────────────┘
          │         │         │         │
          ▼         ▼         ▼         ▼
       小娜      小宸    Athena核心
       (8001)    (8030)     (integrated)
       法律      媒体       通用AI
```

## 使用说明

### 基本请求

```bash
curl -X POST http://localhost:8100/chat \\
  -H "Content-Type: application/json" \\
  -d '{
    "message": "帮我检索专利",
    "session_id": "user_001"
  }'
```

### 指定能力

```bash
curl -X POST http://localhost:8100/chat \\
  -H "Content-Type: application/json" \\
  -d '{
    "message": "写一个Python函数",
    "capability_hint": "python_coding"
  }'
```

### 个性化响应

```bash
# 设置用户偏好
curl -X POST http://localhost:8100/phase2-extension/user-preference/user_001 \\
  -H "Content-Type: application/json" \\
  -d '{
    "response_detail": "detailed",
    "technical_depth": "advanced"
  }'
```

## 性能指标

- **并发处理**: 500 req/s
- **平均响应时间**: <300ms
- **可用性**: 99.9%

## 联系方式

- **作者**: 小诺·双鱼公主
- **邮箱**: xujian519@gmail.com
- **文档**: https://github.com/athena-platform
"""

TAGS_METADATA = [
    {
        "name": "core",
        "description": """
核心API端点 - 小诺网关的主要功能

**端点列表**:
- `POST /chat` - 统一对话接口(主要入口)
- `GET /` - 服务信息
- `GET /health` - 健康检查
        """,
    },
    {
        "name": "capabilities",
        "description": """
能力管理API - 管理和查询可用能力

**功能**:
- 查询所有可用能力
- 获取能力详细信息
- 能力使用统计
        """,
    },
    {
        "name": "optimization",
        "description": """
优化模块API - 查询优化模块状态

**模块**:
- v4.0 不确定性量化
- Phase 1: 意图评分、参数验证、执行引擎、智能拒绝
- Phase 2: BERT分类器、工具图谱、错误处理
- Phase 3: 自主学习、多模态理解、智能体融合
        """,
    },
    {
        "name": "phase2-extension",
        "description": """
Phase 2扩展模块API - 高级功能接口

**模块**:
- 任务编排引擎 - DAG工作流执行
- 异步处理器 - 优先级任务队列
- 知识图谱增强 - 实体关系检索
- 性能监控器 - 终端友好监控
- 响应适配器 - 用户个性化
- 多模态集成器 - 文件处理
        """,
    },
    {
        "name": "monitoring",
        "description": """
监控API - Prometheus指标和系统监控

**端点**:
- `GET /metrics` - Prometheus指标
- `GET /stats` - 使用统计
- `GET /phase2-extension/metrics` - 性能指标
        """,
    },
    {
        "name": "alerts",
        "description": """
告警API - 系统告警管理

**功能**:
- 发送测试告警
- 查询告警配置
- 告警历史记录
        """,
    },
    {
        "name": "health",
        "description": """
健康检查API - 服务健康状态

**端点**:
- `GET /health` - 服务健康状态
- `GET /phase2-extension/status` - 扩展模块状态
        """,
    },
]

CONTACT_INFO = {
    "name": "徐健",
    "email": "xujian519@gmail.com",
    "url": "https://github.com/athena-platform/xiaonuo",
}

LICENSE_INFO = {
    "name": "MIT License",
    "url": "https://opensource.org/licenses/MIT",
}

SERVERS = [
    {
        "url": "http://localhost:8100",
        "description": "本地开发环境",
    },
    {
        "url": "https://api.athena-platform.com",
        "description": "生产环境",
    },
]


# =============================================================================
# 自定义OpenAPI配置函数
# =============================================================================


def get_openapi_config(
    app: FastAPI,
    title: str = API_TITLE,
    version: str = API_VERSION,
    description: str = API_DESCRIPTION,
) -> dict[str, Any]:
    """
    生成自定义OpenAPI配置

    Args:
        app: FastAPI应用实例
        title: API标题
        version: API版本
        description: API描述

    Returns:
        OpenAPI配置字典
    """
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = _get_openapi(
        title=title,
        version=version,
        description=description,
        routes=app.routes,
        tags=TAGS_METADATA,
    )

    # 添加额外信息
    openapi_schema["info"]["contact"] = CONTACT_INFO
    openapi_schema["info"]["license"] = LICENSE_INFO
    openapi_schema["info"]["x-logo"] = {
        "url": "https://raw.githubusercontent.com/athena-platform/main/docs/logo.png",
        "alt_text": "小诺统一网关",
    }

    # 添加服务器配置
    openapi_schema["servers"] = SERVERS

    # 添加全局安全定义
    openapi_schema["components"]["security_schemes"] = {
        "ApiKeyAuth": {
            "type": "api_key",
            "in": "header",
            "name": "X-API-Key",
            "description": "API密钥认证(可选)",
        },
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearer_format": "JWT",
            "description": "JWT令牌认证(可选)",
        },
    }

    # 添加常用响应
    openapi_schema["components"]["responses"] = {
        "Unauthorized": {
            "description": "未授权",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "message": "未授权访问",
                        "error_code": "UNAUTHORIZED",
                    }
                }
            },
        },
        "NotFound": {
            "description": "资源未找到",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "message": "资源未找到",
                        "error_code": "NOT_FOUND",
                    }
                }
            },
        },
        "ValidationError": {
            "description": "请求验证失败",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "message": "请求验证失败",
                        "error_code": "VALIDATION_ERROR",
                        "errors": [
                            {
                                "field": "message",
                                "message": "字段不能为空",
                                "type": "value_error.missing",
                            }
                        ],
                    }
                }
            },
        },
        "InternalServerError": {
            "description": "服务器内部错误",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "message": "服务器内部错误",
                        "error_code": "INTERNAL_ERROR",
                    }
                }
            },
        },
        "ServiceUnavailable": {
            "description": "服务不可用",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "message": "服务暂时不可用",
                        "error_code": "SERVICE_UNAVAILABLE",
                        "details": {"reason": "依赖服务不可用", "retry_after": 60},
                    }
                }
            },
        },
    }

    # 添加通用参数
    openapi_schema["components"]["parameters"] = {
        "SessionId": {
            "name": "session_id",
            "in": "query",
            "description": "会话ID,用于维持上下文",
            "required": False,
            "schema": {"type": "string", "example": "user_001"},
        },
        "IncludeDetails": {
            "name": "include_details",
            "in": "query",
            "description": "是否包含详细信息",
            "required": False,
            "schema": {"type": "boolean", "default": False},
        },
    }

    app.openapi_schema = openapi_schema
    return openapi_schema


def setup_openapi_docs(app: FastAPI | None = None, custom_openapi: dict[str, Any] | None = None) -> None:
    """
    设置OpenAPI文档

    Args:
        app: FastAPI应用实例
        custom_openapi: 自定义OpenAPI配置(可选)
    """

    # 设置自定义OpenAPI函数
    def custom_openapi_func() -> Any:
        if custom_openapi:
            return custom_openapi
        return get_openapi_config(app)

    app.openapi = custom_openapi_func

    # 配置Swagger UI
    app.swagger_ui_init_oauth = {
        "use_pkce_with_authorization_code_grant": True,
        "client_id": "xiaonuo-swagger-client",
        "scopes": ["read:api", "write:api"],
    }

    logger.info("OpenAPI文档配置完成")


# =============================================================================
# 额外的示例数据
# =============================================================================

EXAMPLE_REQUESTS = {
    "patent_search": {
        "summary": "专利检索示例",
        "description": "检索专利信息的示例请求",
        "value": {
            "message": "帮我检索关于人工智能的专利",
            "session_id": "user_001",
            "include_details": True,
        },
    },
    "python_coding": {
        "summary": "Python编程示例",
        "description": "Python代码编写示例请求",
        "value": {
            "message": "写一个快速排序函数",
            "capability_hint": "python_coding",
            "session_id": "user_002",
        },
    },
    "data_analysis": {
        "summary": "数据分析示例",
        "description": "数据分析示例请求",
        "value": {
            "message": "分析这个销售数据的趋势",
            "session_id": "user_003",
            "context": {"data_file": "/path/to/sales.csv"},
        },
    },
}

EXAMPLE_RESPONSES = {
    "success": {
        "summary": "成功响应示例",
        "description": "请求处理成功的响应示例",
        "value": {
            "success": True,
            "response": "我找到了以下相关专利...",
            "capability_used": "xiaona",
            "intent_detected": {"intent": "patent_search", "confidence": 0.95},
            "confidence": 0.95,
            "processing_time": 0.234,
            "suggestions": ["查看专利详情", "分析专利技术方案", "检索相似专利"],
            "session_id": "user_001",
            "timestamp": "2025-12-30T12:00:00",
        },
    },
    "error": {
        "summary": "错误响应示例",
        "description": "请求处理失败的响应示例",
        "value": {
            "success": False,
            "error": "服务暂时不可用",
            "error_code": "SERVICE_UNAVAILABLE",
            "details": {"reason": "小娜服务连接失败", "retry_after": 60},
        },
    },
}


# =============================================================================
# 导出函数
# =============================================================================

__all__ = [
    "API_DESCRIPTION",
    "API_TITLE",
    "API_VERSION",
    "CONTACT_INFO",
    "EXAMPLE_REQUESTS",
    "EXAMPLE_RESPONSES",
    "LICENSE_INFO",
    "SERVERS",
    "TAGS_METADATA",
    "get_openapi_config",
    "setup_openapi_docs",
]
