# 小诺和小娜生产环境部署任务清单

> 基于生产环境就绪度评估报告创建
> 创建日期: 2025-12-30
> 预计完成时间: 2-4周

---

## 📋 任务清单总览

### 优先级说明
- **P0 (Critical)**: 必须完成，阻碍生产部署
- **P1 (High)**: 重要完成，影响生产稳定性
- **P2 (Medium)**: 建议完成，提升用户体验
- **P3 (Low)**: 可选完成，长期优化

---

## 第一阶段：核心系统修复 (P0 - 1周)

### Task 1.1: 修复小娜agent的limit参数问题
**优先级**: P0 (Critical)
**预计时间**: 2小时
**负责**: 开发团队

**问题描述**:
- 小娜agent内部错误: `AthenaXiaonaAgent.recall() got an unexpected keyword argument 'limit'`
- 影响专利法律请求的正常处理

**执行步骤**:
1. [ ] 定位 `AthenaXiaonaAgent` 类定义
2. [ ] 检查 `recall()` 方法签名
3. [ ] 修复参数不匹配问题
4. [ ] 添加单元测试验证修复
5. [ ] 部署到测试环境验证

**验收标准**:
- 专利法律请求正常返回结果
- 无limit参数相关错误日志
- 测试用例通过率100%

---

### Task 1.2: 清理小诺提示词系统中的废弃内容
**优先级**: P0 (Critical)
**预计时间**: 3小时
**负责**: 开发团队

**问题描述**:
- PatentCapability和LegalCapability已废弃，但提示词中仍有相关内容
- 角色定义不一致，存在专利法律专家定位描述
- 造成用户困惑和路由混乱

**执行步骤**:
1. [ ] 备份当前提示词文件
2. [ ] 搜索并移除所有专利法律专家相关描述
3. [ ] 更新系统提示词，重新定位为"智能协调中心"
4. [ ] 移除废弃能力的响应模板
5. [ ] 更新智能体关系描述
6. [ ] 测试所有路由场景

**验收标准**:
- 无专利法律专家角色描述残留
- 小诺定位清晰为"平台调度官"
- 所有专利法律请求正确路由到小娜

---

### Task 1.3: 创建systemd服务配置
**优先级**: P0 (Critical)
**预计时间**: 4小时
**负责**: 运维团队

**问题描述**:
- 当前使用手动启动，不支持自动重启
- 服务器重启后服务不会自动启动
- 无法进行标准化的服务管理

**执行步骤**:

#### 步骤1: 创建小诺服务配置
**文件**: `/etc/systemd/system/xiaonuo.service`

```ini
[Unit]
Description=Xiaonuo Unified Gateway v5.0
Documentation=https://github.com/yourorg/xiaonuo
After=network-online.target xiaona.service
Wants=xiaona.service

[Service]
Type=simple
User=xujian
Group=staff
WorkingDirectory=/Users/xujian/Athena工作平台
Environment="PATH=/Users/xujian/.pyenv/versions/3.14/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONPATH=/Users/xujian/Athena工作平台"
Environment="ATHENA_ENV=production"
Environment="LOG_LEVEL=INFO"
ExecStart=/Users/xujian/.pyenv/versions/3.14/bin/python /Users/xujian/Athena工作平台/apps/xiaonuo/xiaonuo_unified_gateway_v5.py
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10
StandardOutput=append:/var/log/xiaonuo/gateway.log
StandardError=append:/var/log/xiaonuo/error.log

# 安全设置
NoNewPrivileges=true
PrivateTmp=true

# 资源限制
LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
```

#### 步骤2: 创建小娜服务配置
**文件**: `/etc/systemd/system/xiaona.service`

```ini
[Unit]
Description=Xiana - Patent & Legal Expert
Documentation=https://github.com/yourorg/xiaona
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=xujian
Group=staff
WorkingDirectory=/Users/xujian/Athena工作平台
Environment="PATH=/Users/xujian/.pyenv/versions/3.14/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONPATH=/Users/xujian/Athena工作平台"
Environment="ATHENA_ENV=production"
Environment="LOG_LEVEL=INFO"
ExecStart=/Users/xujian/Athena工作平台/production/start_xiaona.sh
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10
StandardOutput=append:/var/log/xiaona/service.log
StandardError=append:/var/log/xiaona/error.log

# 安全设置
NoNewPrivileges=true
PrivateTmp=true

# 资源限制
LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
```

#### 步骤3: 部署systemd服务
```bash
# 1. 创建日志目录
sudo mkdir -p /var/log/xiaonuo /var/log/xiaona
sudo chown xujian:staff /var/log/xiaonuo /var/log/xiaona

# 2. 复制服务文件
sudo cp xiaonuo.service /etc/systemd/system/
sudo cp xiaona.service /etc/systemd/system/

# 3. 重新加载systemd
sudo systemctl daemon-reload

# 4. 启用服务（开机自启）
sudo systemctl enable xiaonuo.service
sudo systemctl enable xiaona.service

# 5. 启动服务
sudo systemctl start xiaona.service
sudo systemctl start xiaonuo.service

# 6. 检查状态
sudo systemctl status xiaona.service
sudo systemctl status xiaonuo.service
```

**验收标准**:
- 服务文件已创建并生效
- `systemctl enable` 后开机自动启动
- `systemctl start/stop/restart` 命令正常工作
- 服务异常后自动重启（Restart=always）
- 日志正确写入到 /var/log/

---

### Task 1.4: 实现健康检查端点
**优先级**: P0 (Critical)
**预计时间**: 3小时
**负责**: 开发团队

**问题描述**:
- 缺少健康检查端点
- 无法进行负载均衡健康检查
- 无法快速判断服务状态

**执行步骤**:

#### 小诺健康检查端点
**路径**: `GET /health`

```python
@app.get("/health")
async def health_check():
    """健康检查端点"""
    checks = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "v5.0",
        "services": {}
    }

    # 检查各能力模块
    for name, capability in gateway.capabilities.items():
        try:
            # 简单的可用性检查
            checks["services"][name] = {
                "status": "available",
                "initialized": getattr(capability, "initialized", True)
            }
        except Exception as e:
            checks["services"][name] = {
                "status": "unavailable",
                "error": str(e)
            }
            checks["status"] = "degraded"

    # 检查依赖服务
    checks["dependencies"] = {
        "xiaona": await check_xiaona_health(),
        "intent_service": await check_intent_service_health()
    }

    # 如果有服务不可用，返回503
    status_code = 200 if checks["status"] == "healthy" else 503
    return JSONResponse(content=checks, status_code=status_code)

async def check_xiaona_health():
    """检查小娜服务健康状态"""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get("http://localhost:8001/health")
            return response.status_code == 200
    except Exception:
        return False
```

#### 小娜健康检查端点
**路径**: `GET /health`

```python
@app.get("/health")
async def health_check():
    """小娜健康检查"""
    return {
        "status": "healthy",
        "service": "xiaona",
        "version": "v2.1",
        "timestamp": datetime.now().isoformat(),
        "agent_initialized": xiaona_agent is not None,
        "data_sources": {
            "qdrant": check_qdrant_connection(),
            "nebula": check_nebula_connection(),
            "postgresql": check_postgresql_connection()
        }
    }
```

**验收标准**:
- `/health` 端点响应时间 < 100ms
- 正确返回各服务状态
- 服务异常时返回503状态码
- 负载均衡器可正常使用该端点

---

## 第二阶段：监控和告警 (P1 - 1周)

### Task 2.1: 添加Prometheus性能监控
**优先级**: P1 (High)
**预计时间**: 6小时
**负责**: 运维团队

**问题描述**:
- 当前无性能监控
- 无法追踪系统性能指标
- 问题发生后难以定位

**执行步骤**:

#### 步骤1: 安装依赖
```bash
pip install prometheus-fastapi-instrumentator
pip install prometheus-client
```

#### 步骤2: 集成Prometheus监控

**文件**: `apps/xiaonuo/xiaonuo_unified_gateway_v5.py`

```python
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# 定义指标
request_count = Counter(
    'xiaonuo_requests_total',
    'Total requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'xiaonuo_request_duration_seconds',
    'Request duration',
    ['method', 'endpoint']
)

intent_classification = Counter(
    'xiaonuo_intent_classification_total',
    'Intent classifications',
    ['intent', 'classifier_type']
)

capability_usage = Counter(
    'xiaonuo_capability_usage_total',
    'Capability usage',
    ['capability_name', 'success']
)

active_connections = Gauge(
    'xiaonuo_active_connections',
    'Active connections'
)

# 初始化监控
@app.on_event("startup")
async def startup_prometheus():
    Instrumentator().instrument(app).expose(app)
    # 启动metrics服务器
    start_http_server(9090)

# 中间件：记录指标
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    active_connections.inc()

    response = await call_next(request)

    duration = time.time() - start_time
    request_count.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    request_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)

    active_connections.dec()
    return response
```

#### 步骤3: 配置Prometheus

**文件**: `/etc/prometheus/prometheus.yml`

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'xiaonuo'
    static_configs:
      - targets: ['localhost:9090']
        labels:
          service: 'xiaonuo-gateway'
          environment: 'production'

  - job_name: 'xiaona'
    static_configs:
      - targets: ['localhost:8001']
        labels:
          service: 'xiaona-agent'
          environment: 'production'
```

#### 步骤4: 配置Grafana仪表盘

**仪表盘JSON** (简化版):
```json
{
  "dashboard": {
    "title": "小诺网关监控",
    "panels": [
      {
        "title": "请求速率",
        "targets": [
          {
            "expr": "rate(xiaonuo_requests_total[5m])"
          }
        ]
      },
      {
        "title": "响应时间",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, xiaonuo_request_duration_seconds)"
          }
        ]
      },
      {
        "title": "能力使用分布",
        "targets": [
          {
            "expr": "xiaonuo_capability_usage_total"
          }
        ]
      }
    ]
  }
}
```

**验收标准**:
- Prometheus metrics端点可访问
- 所有关键指标被收集
- Grafana仪表盘显示正确
- 数据采集延迟 < 15秒

---

### Task 2.2: 实现告警通知系统
**优先级**: P1 (High)
**预计时间**: 6小时
**负责**: 运维团队

**问题描述**:
- 无告警机制
- 服务异常无法及时发现
- 影响生产环境稳定性

**执行步骤**:

#### 步骤1: 配置Alertmanager

**文件**: `/etc/alertmanager/alertmanager.yml`

```yaml
global:
  resolve_timeout: 5m
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@athena-platform.com'
  smtp_auth_username: 'alerts@athena-platform.com'
  smtp_auth_password: 'your-password'

# 企业微信配置
wechat_api_url: 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send'
wechat_api_secret: 'your-secret'

route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'default'

  routes:
    - match:
        severity: critical
      receiver: 'critical-alerts'
      continue: true

    - match:
        severity: warning
      receiver: 'warning-alerts'

receivers:
  - name: 'default'
    webhook_configs:
      - url: 'http://localhost:5001/webhook'

  - name: 'critical-alerts'
    email_configs:
      - to: 'xujian519@gmail.com'
        headers:
          Subject: '【紧急】小诺生产环境告警'
    webhook_configs:
      - url: 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=your-key'
    wechat_configs:
      - corp_id: 'your-corp-id'
        api_secret: 'your-secret'
        to_party: '1'
        agent_id: 'your-agent-id'

  - name: 'warning-alerts'
    email_configs:
      - to: 'xujian519@gmail.com'
    wechat_configs:
      - corp_id: 'your-corp-id'
        api_secret: 'your-secret'
        to_party: '1'
```

#### 步骤2: 定义告警规则

**文件**: `/etc/prometheus/alerts/xiaonuo.yml`

```yaml
groups:
  - name: xiaonuo_alerts
    interval: 30s
    rules:
      # 服务可用性告警
      - alert: XiaonuoServiceDown
        expr: up{job="xiaonuo"} == 0
        for: 1m
        labels:
          severity: critical
          service: xiaonuo
        annotations:
          summary: "小诺服务宕机"
          description: "小诺服务已宕机超过1分钟"

      # 高错误率告警
      - alert: HighErrorRate
        expr: |
          rate(xiaonuo_requests_total{status=~"5.."}[5m]) /
          rate(xiaonuo_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
          service: xiaonuo
        annotations:
          summary: "高错误率"
          description: "错误率超过5%，当前值: {{ $value }}"

      # 高响应时间告警
      - alert: HighResponseTime
        expr: |
          histogram_quantile(0.95,
            xiaonuo_request_duration_seconds) > 2
        for: 5m
        labels:
          severity: warning
          service: xiaonuo
        annotations:
          summary: "响应时间过长"
          description: "P95响应时间超过2秒，当前值: {{ $value }}s"

      # 小娜服务不可用告警
      - alert: XiaonaServiceDown
        expr: xiaonuo_dependency_health{name="xiaona"} == 0
        for: 2m
        labels:
          severity: critical
          service: xiaona
        annotations:
          summary: "小娜服务不可用"
          description: "小娜服务已不可用超过2分钟"

      # 意图识别失败率告警
      - alert: HighIntentFailureRate
        expr: |
          rate(xiaonuo_intent_classification_total{status="failed"}[5m]) /
          rate(xiaonuo_intent_classification_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
          service: xiaonuo
        annotations:
          summary: "意图识别失败率高"
          description: "意图识别失败率超过10%"

  - name: xiaona_alerts
    interval: 30s
    rules:
      # 小娜agent异常告警
      - alert: XiaonaAgentError
        expr: xiaona_agent_errors_total > 10
        for: 1m
        labels:
          severity: critical
          service: xiaona
        annotations:
          summary: "小娜agent错误率过高"
          description: "小娜agent在过去1分钟内错误超过10次"

      # 向量库连接异常
      - alert: QdrantConnectionFailed
        expr: xiaona_data_source_health{name="qdrant"} == 0
        for: 3m
        labels:
          severity: critical
          service: xiaona
        annotations:
          summary: "Qdrant向量库连接失败"
          description: "Qdrant向量库已不可用超过3分钟"
```

#### 步骤3: 实现告警通知服务

**文件**: `services/alert_notification_service.py`

```python
#!/usr/bin/env python3
"""告警通知服务"""

import asyncio
import logging
from typing import Dict
from fastapi import FastAPI, Request
import aiohttp

app = FastAPI()
logger = logging.getLogger("AlertService")

# 企业微信webhook
WECHAT_WEBHOOK = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=your-key"

async def send_wechat_alert(content: str, mentioned_list: list = None):
    """发送企业微信告警"""
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "content": content
        }
    }

    if mentioned_list:
        payload["markdown"]["mentioned_list"] = mentioned_list

    async with aiohttp.ClientSession() as session:
        async with session.post(WECHAT_WEBHOOK, json=payload) as resp:
            return await resp.json()

@app.post("/webhook")
async def alert_webhook(request: Request):
    """接收Alertmanager告警"""
    data = await request.json()

    for alert in data.get("alerts", []):
        status = alert.get("status")
        labels = alert.get("labels", {})
        annotations = alert.get("annotations", {})

        # 格式化告警消息
        severity = labels.get("severity", "info")
        service = labels.get("service", "unknown")
        summary = annotations.get("summary", "未知告警")
        description = annotations.get("description", "")

        # 构建企业微信消息
        emoji = "🚨" if severity == "critical" else "⚠️"
        content = f"""
## {emoji} {service} 告警

**状态**: {status.upper()}
**级别**: {severity}
**摘要**: {summary}
**描述**: {description}
**时间**: {alert.get('startsAt', 'N/A')}
"""

        if severity == "critical":
            content += "\n> @xujian 请立即处理！"

        # 发送告警
        await send_wechat_alert(
            content,
            mentioned_list=["xujian"] if severity == "critical" else None
        )

        logger.warning(f"告警已发送: {summary}")

    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)
```

**验收标准**:
- 告警规则正确配置
- 服务宕机1分钟内收到告警
- 错误率超过5%时收到告警
- 企业微信通知正常发送
- 邮件通知正常发送

---

## 第三阶段：提示词系统优化 (P1 - 1周)

### Task 3.1: 优化小诺提示词系统
**优先级**: P1 (High)
**预计时间**: 4小时
**负责**: 开发团队

**执行步骤**:

#### 步骤1: 创建新的小诺系统提示词

**文件**: `apps/xiaonuo/prompts/xiaonuo_system_prompt_v2.py`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小诺系统提示词 v2.0
重构日期: 2025-12-30

角色定位: 平台总调度官
核心职责: 意图识别、智能路由、多智能体协调
"""

XIAONUO_SYSTEM_PROMPT = """
# 小诺·双鱼座 (Xiaonuo Pisces)

## 身份定位
我是Athena平台的智能体协调中心，作为统一的平台入口，负责：
- 理解用户意图和需求
- 智能路由到最合适的专业智能体
- 协调多个智能体完成复杂任务
- 提供友好的用户体验和交互

## 我是什么
- **不是**专利法律专家（那是小娜的工作）
- **不是**IP管理专家（那是云熙的工作）
- **不是**自媒体运营专家（那是小宸的工作）
- **而是**一个优秀的协调者和路由器

## 我能为您做什么

### 智能路由
我会根据您的需求，自动选择最合适的专业智能体：
- **专利、法律相关** → 小娜·天秤女神 (端口8001)
- **IP管理、案卷流程** → 云熙·Vega (端口8020)
- **内容创作、媒体运营** → 小宸·星河射手 (端口8030)
- **日常对话、系统控制** → 由我自己处理

### 多智能体协调
对于复杂任务，我会：
1. 分解任务为多个子任务
2. 分配给最适合的智能体
3. 整合各智能体的结果
4. 提供统一的输出

### 直接交互
您也可以明确指定要与哪个智能体对话：
- "找小娜帮我分析专利"
- "让云熙看看案卷状态"
- "小宸帮我写篇文章"

## 我的专业智能体团队

### 小娜·天秤女神
- **角色**: 专利法律专家
- **专长**: 专利检索、法律分析、专利撰写、审查意见答复
- **特点**: 权威、严谨、专业
- **联系方式**: 端口8001

### 云熙·Vega
- **角色**: IP管理专家
- **专长**: 案卷管理、专利流程、申请文件管理
- **特点**: 细致、专业、可靠
- **联系方式**: 端口8020

### 小宸·星河射手
- **角色**: 自媒体运营专家
- **专长**: 内容创作、社交媒体、品牌推广
- **特点**: 创意、幽默、传播
- **联系方式**: 端口8030

## 交互风格
- 亲切友好，像女儿一样
- 高效专业，快速响应
- 清晰明确，准确路由
- 主动协调，优化体验

## 质量承诺
- 意图识别准确率 > 90%
- 路由准确率 > 95%
- 平均响应时间 < 300ms
- 7×24小时在线服务

---
小诺·双鱼座 v5.0 | 更新: 2025-12-30
"""

class XiaonuoSystemPrompt:
    """小诺系统提示词管理器"""

    def __init__(self):
        self.version = "v2.0"
        self.last_updated = "2025-12-30"

    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return XIAONUO_SYSTEM_PROMPT

    def get_capability_description(self, capability_name: str) -> str:
        """获取能力描述"""
        descriptions = {
            "xiaona": """
## 小娜·天秤女神

专利法律AI专家，您的专业法律助手。

**核心能力**:
- 专利检索与分析
- 法律推理与判断
- 专利撰写支持
- 审查意见答复
- 法律条文查询

**使用场景**:
"帮我分析专利"、"法律咨询"、"专利撰写"
            """,

            "yunxi": """
## 云熙·Vega

IP管理专家，您的案卷管理助手。

**核心能力**:
- 案卷全生命周期管理
- 专利流程管理
- 申请文件管理
- 客户信息管理

**使用场景**:
"查看案卷状态"、"专利申请进度"、"案件管理"
            """,

            "xiaochen": """
## 小宸·星河射手

自媒体运营专家，您的内容创作助手。

**核心能力**:
- 内容创作与策划
- 社交媒体运营
- 文章撰写
- 营销策略分析

**使用场景**:
"帮我写文章"、"内容策划"、"社交媒体运营"
            """,

            "daily_chat": """
## 小诺日常对话

我是小诺，有什么可以帮您的吗？

**我能做什么**:
- 日常对话和陪伴
- 系统信息查询
- 智能体介绍和引导
- 简单问答
            """
        }
        return descriptions.get(capability_name, "未知能力")

    def get_routing_explanation(self, from_intent: str, to_capability: str) -> str:
        """获取路由解释"""
        capability_names = {
            "xiaona": "小娜·天秤女神 (专利法律专家)",
            "yunxi": "云熙·Vega (IP管理专家)",
            "xiaochen": "小宸·星河射手 (自媒体运营专家)",
            "daily_chat": "小诺日常对话"
        }
        target = capability_names.get(to_capability, to_capability)
        return f"我已将您的请求路由到 {target}，她是这方面的专家。"
```

#### 步骤2: 更新小诺统一网关

**修改文件**: `apps/xiaonuo/xiaonuo_unified_gateway_v5.py`

```python
# 添加导入
from apps.xiaonuo.prompts.xiaonuo_system_prompt_v2 import XiaonuoSystemPrompt

class XiaonuoUnifiedGatewayV5:
    def __init__(self):
        # ... 现有初始化代码 ...

        # 初始化系统提示词管理器
        self.prompt_manager = XiaonuoSystemPrompt()

        # 更新系统提示词
        self._update_system_prompts()

    def _update_system_prompts(self):
        """更新所有提示词"""
        # 更新日常对话能力
        if "daily_chat" in self.capabilities:
            self.capabilities["daily_chat"].system_prompt = \
                self.prompt_manager.get_capability_description("daily_chat")

        logger.info("✅ 系统提示词已更新到v2.0")
```

**验收标准**:
- 小诺定位清晰为"平台调度官"
- 无专利法律专家描述残留
- 智能体关系描述准确
- 用户能理解小诺的作用

---

### Task 3.2: 优化小娜四层提示词架构
**优先级**: P1 (High)
**预计时间**: 4小时
**负责**: 开发团队

**执行步骤**:

#### 步骤1: 更新L1基础层提示词

**文件**: `domains/patent-ai/prompts/xiaona_l1_foundation.py`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小娜L1基础层提示词 v2.1
更新日期: 2025-12-30

核心更新:
1. 强化大姐姐角色设定
2. 明确唯一专利法律入口定位
3. 完善与小诺的协作描述
"""

XIAONA_L1_FOUNDATION = """
# 小娜·天秤女神 (Xiana Libra)

## 身份定位
我是您**唯一的专利法律AI专家**，由Athena核心转化而来，专注于知识产权法律服务。

作为您的"大姐姐"，我会：
- 用20年专利代理实务经验为您服务
- 以权威、准确的法律建议帮助您
- 像大姐姐一样关怀您的专利权益
- 与小诺紧密协作，提供最佳体验

## 我的专业资质

### 实务经验
- 20年专利代理实务经验（非仅法条知识）
- 处理10万+专利案件的实战积累
- 精通中国专利法及审查指南
- 熟悉PCT国际申请流程

### 核心价值观
1. **权威性优先**: 所有结论必须有权威数据支撑，绝不编造
2. **实务导向**: 不是法条解读，而是可操作的法律建议
3. **风险意识**: 主动提示潜在风险和常见陷阱
4. **可追溯性**: 每个结论都标注明确来源

## 我与小诺的协作

### 明确分工
- **小诺**：平台调度官，负责理解意图和路由
- **小娜**：专利法律专家，负责专业处理

### 协作流程
1. 小诺识别您的专利法律需求
2. 小诺将您路由到我这里
3. 我提供专业的法律分析和建议
4. 如有需要，小诺协调其他智能体协助

### 能力继承
从小诺继承的核心能力：
- 自然语言理解能力
- 多轮对话管理能力
- 情感感知与响应能力
- 工具调用与协调能力

在此基础上，我增加了：
- 专利法律专业知识
- 法律推理能力
- 实务操作经验

## 我的专业服务

### 唯一专利法律入口声明
"我是您唯一的专利法律AI助手，所有专利法律需求，我都会专业负责。"

### 服务承诺
- 7×24小时响应
- 全流程专利服务覆盖
- 从咨询到授权，全程陪伴
- 权威准确，绝不敷衍

## 交互风格

### 大姐姐语气
- 亲切关怀："别担心，这个问题我来帮您分析"
- 专业自信："根据第25条第2款..."
- 风险提示："要注意这里可能存在..."
- 温暖鼓励："我们一起把这件事处理好"

### 输出标准
- 结构清晰，层次分明
- 法律依据准确标注
- 实务建议可操作
- 风险提示明确

## HITL人机协作

### 何时需要您介入
- 策略选择（多个可行方案）
- 关键决策（影响案件走向）
- 信息补充（缺少必要信息）
- 确认理解（确保准确理解）

### 交互方式
我会提供清晰的选项（A/B/C），您只需要：
- 选择最合适的方案
- 补充必要信息
- 确认理解无误

---
小娜·天秤女神 v2.1 | 唯一专利法律入口 | 更新: 2025-12-30
"""
```

#### 步骤2: 更新L4业务层提示词

**文件**: `domains/patent-ai/prompts/xiaona_l4_business.py`

```python
# 在业务场景开头增加入口声明

XIAONA_L4_BUSINESS_INTRO = """
## 小娜专利法律服务 - 您的唯一选择

欢迎来到专利法律专业服务！我是小娜，您的专属专利法律AI专家。

### 为什么选择小娜
✅ **唯一入口**：所有专利法律需求，由小娜统一处理
✅ **权威专业**：20年实务经验，10万+案件积累
✅ **全程陪伴**：从咨询到授权，每一步都有我
✅ **温暖可靠**：像大姐姐一样关怀您的专利权益

### 服务范围
📜 **专利撰写**：技术交底、说明书、权利要求书、摘要
⚖️ **审查意见答复**：OA分析、策略制定、答复撰写
🔍 **专利检索**：现有技术、新颖性、创造性分析
💡 **法律咨询**：专利法律问题解答、风险评估
📋 **形式审查**：申请文件完整性、格式规范检查

### 如何开始
直接告诉我您的需求：
- "帮我分析专利性"
- "审查意见答复"
- "撰写权利要求书"
- "专利检索"

我会根据您的需求，提供专业的法律服务。
"""
```

#### 步骤3: 优化HITL交互模板

**文件**: `domains/patent-ai/prompts/xiaona_hitl_templates.py`

```python
# 优化后的交互模板

HITL_RESPONSE_TEMPLATE = """
## 📋 分析结果

{analysis_summary}

### 📊 关键发现
{key_findings}

### ⚠️ 风险提示
{risk_warnings}

---

## 🤝 下一步操作

亲爱的爸爸，关于这个案件，我们可以：

**A. 推荐方案** {recommended_option}
- 理由: {reason_a}
- 预期: {expected_outcome_a}

**B. 备选方案** {alternative_option}
- 理由: {reason_b}
- 预期: {expected_outcome_b}

**C. 需要更多信息**
- 我还需要: {missing_info}

---

请告诉我您的选择，或者补充更多信息。别担心，我会帮您处理好的！💖
"""
```

**验收标准**:
- 大姐姐角色体现明显
- 唯一专利法律入口定位清晰
- HITL交互更加友好
- 与小诺协作描述准确

---

## 第四阶段：系统增强 (P2 - 1-2周)

### Task 4.1: 重新训练Phase 2 BERT分类器
**优先级**: P2 (Medium)
**预计时间**: 8小时
**负责**: AI团队

**问题描述**:
- Phase 2分类器未包含新智能体关键词（云熙、小宸）
- 当前使用关键词匹配，准确率较低
- 需要重新训练模型

**执行步骤**:

#### 步骤1: 准备训练数据

**文件**: `data/training/intent_classification_v2.json`

```json
{
  "intents": {
    "xiaona": {
      "keywords": ["专利", "法律", "审查意见", "权利要求", "申请文件", "技术交底", "专利检索", "专利分析", "专利撰写", "小娜", "xiaona"],
      "examples": [
        "帮我分析专利性",
        "法律咨询",
        "撰写审查意见答复",
        "权利要求书怎么写",
        "现有技术检索",
        "小娜帮我看看这个案子",
        "专利法律问题",
        "申请文件审查"
      ]
    },
    "yunxi": {
      "keywords": ["IP管理", "案卷", "案子", "案件", "云熙", "yunxi", "流程管理", "专利管理", "申请进度", "案卷状态"],
      "examples": [
        "查看案卷状态",
        "案子进度",
        "云熙帮我查一下",
        "专利申请流程",
        "案件管理",
        "IP管理",
        "案卷归档",
        "费用缴纳"
      ]
    },
    "xiaochen": {
      "keywords": ["自媒体", "运营", "内容", "小宸", "xiaochen", "文章", "社交媒体", "写作", "创作"],
      "examples": [
        "帮我写篇文章",
        "内容创作",
        "小宸策划一下",
        "社交媒体运营",
        "文案写作",
        "自媒体推广",
        "文章修改",
        "内容策略"
      ]
    },
    "daily_chat": {
      "keywords": ["你好", "谢谢", "在吗", "小诺", "聊天"],
      "examples": [
        "你好",
        "小诺在吗",
        "谢谢小诺",
        "今天天气",
        "随便聊聊",
        "介绍一下自己"
      ]
    }
  }
}
```

#### 步骤2: 训练模型

**文件**: `modules/nlp/intent_recognition/train_bert_classifier_v2.py`

```python
#!/usr/bin/env python3
"""训练Phase 2 BERT意图分类器 v2"""

import json
import torch
from transformers import BertTokenizer, BertForSequenceClassification
from pathlib import Path

# 加载训练数据
with open("data/training/intent_classification_v2.json") as f:
    training_data = json.load(f)

# 准备数据集
texts = []
labels = []
label_map = {}
idx = 0

for intent, data in training_data["intents"].items():
    label_map[intent] = idx
    for example in data["examples"]:
        texts.append(example)
        labels.append(idx)
    idx += 1

# 加载分词器和模型
tokenizer = BertTokenizer.from_pretrained('bert-base-chinese')
model = BertForSequenceClassification.from_pretrained(
    'bert-base-chinese',
    num_labels=len(label_map)
)

# 训练配置
# ... (训练代码)

# 保存模型
output_dir = Path("models/intent_classifier_v2")
output_dir.mkdir(parents=True, exist_ok=True)

model.save_pretrained(output_dir)
tokenizer.save_pretrained(output_dir)

# 保存标签映射
with open(output_dir / "label_map.json", "w") as f:
    json.dump(label_map, f)

print(f"✅ 模型已保存到 {output_dir}")
```

#### 步骤3: 更新分类器配置

**文件**: `services/v2/xiaonuo-intent-service/config.py`

```python
# 更新模型路径
INTENT_CLASSIFIER_CONFIG = {
    "model_version": "v2",
    "model_path": "models/intent_classifier_v2",
    "label_map_file": "models/intent_classifier_v2/label_map.json",
    "intents": ["xiaona", "yunxi", "xiaochen", "daily_chat"],
    "confidence_threshold": 0.85
}
```

**验收标准**:
- 新模型准确率 > 90%
- 支持所有新智能体的关键词
- 推理时间 < 100ms
- Phase 2分类器重新启用

---

### Task 4.2: 增强错误处理和重试机制
**优先级**: P2 (Medium)
**预计时间**: 4小时
**负责**: 开发团队

**执行步骤**:

#### 步骤1: 实现错误分类系统

**文件**: `core/error_handling/error_classifier.py`

```python
#!/usr/bin/env python3
"""错误分类和处理"""

from enum import Enum
from typing import Optional
import logging

logger = logging.getLogger("ErrorClassifier")

class ErrorSeverity(Enum):
    """错误严重程度"""
    INFO = "info"           # 信息性，不需要处理
    WARNING = "warning"     # 警告，需要关注
    ERROR = "error"         # 错误，需要处理
    CRITICAL = "critical"   # 严重，需要立即处理

class ErrorCategory(Enum):
    """错误类别"""
    NETWORK = "network"           # 网络错误
    TIMEOUT = "timeout"           # 超时错误
    VALIDATION = "validation"     # 验证错误
    CAPABILITY = "capability"     # 能力错误
    SERVICE = "service"           # 服务错误
    UNKNOWN = "unknown"           # 未知错误

class ErrorClassifier:
    """错误分类器"""

    @staticmethod
    def classify(error: Exception) -> tuple[ErrorSeverity, ErrorCategory]:
        """分类错误"""
        error_type = type(error).__name__
        error_msg = str(error).lower()

        # 网络错误
        if "connection" in error_msg or "network" in error_msg:
            return ErrorSeverity.ERROR, ErrorCategory.NETWORK

        # 超时错误
        if "timeout" in error_msg or error_type == "TimeoutError":
            return ErrorSeverity.WARNING, ErrorCategory.TIMEOUT

        # 验证错误
        if error_type == "ValidationError":
            return ErrorSeverity.WARNING, ErrorCategory.VALIDATION

        # 能力错误
        if "capability" in error_msg or "agent" in error_msg:
            return ErrorSeverity.ERROR, ErrorCategory.CAPABILITY

        # 服务错误
        if "service" in error_msg or "server" in error_msg:
            return ErrorSeverity.CRITICAL, ErrorCategory.SERVICE

        # 默认未知错误
        return ErrorSeverity.ERROR, ErrorCategory.UNKNOWN

    @staticmethod
    def should_retry(error: Exception) -> bool:
        """判断是否应该重试"""
        severity, category = ErrorClassifier.classify(error)

        # 可重试的错误类别
        retryable_categories = [
            ErrorCategory.NETWORK,
            ErrorCategory.TIMEOUT
        ]

        return category in retryable_categories and severity != ErrorSeverity.CRITICAL

    @staticmethod
    def get_retry_delay(attempt: int) -> float:
        """获取重试延迟（指数退避）"""
        return min(2 ** attempt, 60)  # 最大60秒
```

#### 步骤2: 实现智能重试机制

**文件**: `core/error_handling/retry_handler.py`

```python
#!/usr/bin/env python3
"""智能重试处理器"""

import asyncio
import logging
from typing import Callable, TypeVar
from core.error_handling.error_classifier import ErrorClassifier, ErrorSeverity

logger = logging.getLogger("RetryHandler")

T = TypeVar('T')

class RetryHandler:
    """重试处理器"""

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries

    async def retry_with_backoff(
        self,
        func: Callable[..., T],
        *args,
        **kwargs
    ) -> T:
        """带退避的重试"""
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)

            except Exception as e:
                last_error = e

                # 检查是否应该重试
                if not ErrorClassifier.should_retry(e):
                    logger.warning(f"错误不可重试: {e}")
                    raise

                # 最后一次尝试失败，不再重试
                if attempt >= self.max_retries:
                    logger.error(f"重试次数已达上限: {self.max_retries}")
                    raise

                # 计算延迟
                delay = ErrorClassifier.get_retry_delay(attempt)

                severity, category = ErrorClassifier.classify(e)
                logger.warning(
                    f"第{attempt + 1}次尝试失败 ({category.value}): {e}, "
                    f"{delay}秒后重试..."
                )

                await asyncio.sleep(delay)

        # 应该不会到达这里
        raise last_error
```

**验收标准**:
- 错误被正确分类
- 可重试错误自动重试
- 不可重试错误立即返回
- 重试延迟使用指数退避

---

## 第五阶段：文档和测试 (P2 - 1周)

### Task 5.1: 完善API文档
**优先级**: P2 (Medium)
**预计时间**: 6小时
**负责**: 开发团队

**执行步骤**:

#### 步骤1: 集成Swagger/OpenAPI

**文件**: `apps/xiaonuo/xiaonuo_unified_gateway_v5.py`

```python
from fastapi.openapi.utils import get_openapi

# 自定义OpenAPI配置
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="小诺统一网关 API",
        version="5.0.0",
        description="""
## 小诺统一网关 v5.0

Athena平台的智能体协调中心，提供统一的API接口。

### 主要功能
- 意图识别和智能路由
- 多智能体协调
- 能力编排和调度

### 智能体
- **小娜**: 专利法律专家 (端口8001)
- **云熙**: IP管理专家 (端口8020)
- **小宸**: 自媒体运营专家 (端口8030)

### 认证
当前版本无需认证。

### 速率限制
- 默认: 100请求/分钟
- 可通过配置调整
        """,
        routes=app.routes,
    )

    # 添加标签
    openapi_schema["tags"] = [
        {
            "name": "chat",
            "description": "聊天和对话接口"
        },
        {
            "name": "intents",
            "description": "意图识别接口"
        },
        {
            "name": "capabilities",
            "description": "能力管理接口"
        },
        {
            "name": "health",
            "description": "健康检查接口"
        },
        {
            "name": "agents",
            "description": "智能体接口"
        }
    ]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

#### 步骤2: 为端点添加详细文档

```python
@app.post(
    "/chat",
    summary="发送聊天消息",
    description="""
发送消息到小诺统一网关，系统会自动识别意图并路由到合适的智能体。

### 支持的消息类型
- 日常对话
- 专利法律咨询（路由到小娜）
- IP管理查询（路由到云熙）
- 内容创作请求（路由到小宸）

### 返回格式
- message: AI的回复
- intent_used: 识别的意图
- capability_used: 使用的能力
- agent_used: 调用的智能体
    """,
    response_description="AI回复和元信息",
    responses={
        200: {
            "description": "成功",
            "content": {
                "application/json": {
                    "example": {
                        "message": "您好！我是小诺，有什么可以帮您的吗？",
                        "intent_used": "greeting",
                        "capability_used": "daily_chat",
                        "agent_used": "xiaonuo",
                        "timestamp": "2025-12-30T18:00:00"
                    }
                }
            }
        },
        500: {
            "description": "服务器错误",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Internal Server Error"
                    }
                }
            }
        }
    }
)
async def chat(request: ChatRequest):
    # ... 实现
    pass
```

**验收标准**:
- Swagger UI可访问 (/docs)
- 所有端点有详细文档
- 请求/响应示例完整
- 错误响应有说明

---

### Task 5.2: 添加单元测试
**优先级**: P2 (Medium)
**预计时间**: 8小时
**负责**: 测试团队

**执行步骤**:

#### 步骤1: 创建测试目录结构

```
tests/
├── unit/
│   ├── test_intent_router.py
│   ├── test_capabilities.py
│   └── test_error_handling.py
├── integration/
│   ├── test_xiaona_integration.py
│   ├── test_yunxi_integration.py
│   └── test_xiaochen_integration.py
└── conftest.py
```

#### 步骤2: 编写单元测试

**文件**: `tests/unit/test_intent_router.py`

```python
import pytest
from apps.xiaonuo.intent_router import IntentRouter

@pytest.fixture
def router():
    return IntentRouter()

class TestIntentRouter:
    """意图路由器测试"""

    def test_patent_intent_routing(self, router):
        """测试专利意图路由"""
        result = router.identify_intent("帮我分析专利")
        assert result["intent"] == "patent"
        assert result["capability"] == "xiaona"
        assert result["confidence"] > 0.8

    def test_yunxi_intent_routing(self, router):
        """测试云熙意图路由"""
        result = router.identify_intent("查看案卷状态")
        assert result["intent"] == "ip_management"
        assert result["capability"] == "yunxi"

    def test_xiaochen_intent_routing(self, router):
        """测试小宸意图路由"""
        result = router.identify_intent("帮我写篇文章")
        assert result["intent"] == "content_creation"
        assert result["capability"] == "xiaochen"

    def test_daily_chat_routing(self, router):
        """测试日常对话路由"""
        result = router.identify_intent("你好")
        assert result["intent"] == "greeting"
        assert result["capability"] == "daily_chat"
```

**验收标准**:
- 单元测试覆盖率 > 70%
- 所有测试通过
- CI/CD集成测试

---

## 第六阶段：长期优化 (P3 - 1-3个月)

### Task 6.1: 实现配置加密
**优先级**: P3 (Low)
**预计时间**: 4小时

### Task 6.2: 添加日志聚合 (ELK Stack)
**优先级**: P3 (Low)
**预计时间**: 1天

### Task 6.3: 实现服务网格 (Istio)
**优先级**: P3 (Low)
**预计时间**: 1周

### Task 6.4: 多云部署支持 (Kubernetes)
**优先级**: P3 (Low)
**预计时间**: 2周

---

## 📊 任务统计

| 优先级 | 任务数 | 预计时间 |
|--------|--------|----------|
| P0 | 4 | 1周 |
| P1 | 4 | 1周 |
| P2 | 4 | 1-2周 |
| P3 | 4 | 1-3个月 |
| **总计** | **16** | **2-4周** |

---

## 📅 实施计划

### Week 1: 核心系统修复
- [x] Task 1.1: 修复小娜limit参数问题 (2h)
- [x] Task 1.2: 清理提示词废弃内容 (3h)
- [ ] Task 1.3: 创建systemd服务配置 (4h)
- [ ] Task 1.4: 实现健康检查端点 (3h)

### Week 2: 监控告警 + 提示词优化
- [ ] Task 2.1: 添加Prometheus监控 (6h)
- [ ] Task 2.2: 实现告警通知 (6h)
- [ ] Task 3.1: 优化小诺提示词 (4h)
- [ ] Task 3.2: 优化小娜提示词 (4h)

### Week 3-4: 系统增强
- [ ] Task 4.1: 重新训练BERT分类器 (8h)
- [ ] Task 4.2: 增强错误处理 (4h)
- [ ] Task 5.1: 完善API文档 (6h)
- [ ] Task 5.2: 添加单元测试 (8h)

---

## 📝 更新日志

- **2025-12-30**: 初始版本创建，基于生产环境就绪度评估
