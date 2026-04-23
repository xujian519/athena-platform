# Athena环境文件整合指南

## 📋 概述

当前项目有47个.env文件分散在各处，需要整合到统一的配置结构中。

## 🎯 整合策略

### 保留的核心配置文件（根目录）

```
Athena工作平台/
├── .env                      # 当前激活环境
├── .env.template             # 完整配置模板
├── .env.secrets.template     # 敏感信息模板
├── .env.development          # 开发环境
├── .env.testing              # 测试环境
├── .env.staging              # 预发布环境
├── .env.production           # 生产环境
└── .env.secrets              # 敏感信息（不提交）
```

### 需要整合的配置源

#### MCP服务配置
**位置**: `mcp-servers/.env`, `mcp-servers/*/.env`

**整合方案**: 将配置合并到根`.env.template`中，使用前缀区分：
```bash
# MCP服务配置
MCP_ENABLED=true
MCP_SERVERS_PATH=${ATHENA_HOME}/mcp-servers
MCP_LOG_LEVEL=INFO

# GitHub MCP
GITHUB_TOKEN=your_github_token_here

# 必应搜索MCP
BING_SEARCH_API_KEY=your_bing_search_api_key_here

# Jina AI MCP
JINA_API_KEY=your_jina_api_key_here

# 高德地图MCP
AMAP_API_KEY=your_amap_api_key_here
```

#### 服务配置
**位置**: `services/*/.env`, `services/*/.env.example`

**整合方案**: 使用服务名作为前缀：
```bash
# YunPat Agent服务
YUNPAT_AGENT_URL=http://localhost:8020
YUNPAT_DEFAULT_LLM=deepseek-chat

# 爬虫服务
CRAWLER_PORT=8022
CRAWLER_USER_AGENT=Athena-Crawler/1.0

# NLP服务
NLP_PORT=8030
NLP_MODEL=default
```

#### 项目配置
**位置**: `projects/phoenix/.env.*`

**整合方案**: Phoenix项目有自己的环境需求，保留其独立配置，但重命名以避免冲突：
```
projects/phoenix/.env.example -> 保留
projects/phoenix/.env.development -> 删除（使用开发环境）
projects/phoenix/.env.staging -> 删除（使用预发布环境）
projects/phoenix/.env.production -> 删除（使用生产环境）
```

## 🔧 整合步骤

### 步骤1: 更新根.env.template

将各服务的配置添加到根`.env.template`（已完成）

### 步骤2: 创建服务配置映射

为每个服务创建配置加载脚本：

```python
# core/config/service_config.py
import os
from pathlib import Path
from dotenv import load_dotenv

def load_service_config(service_name: str):
    """加载服务特定配置"""
    # 从统一.env加载服务配置
    load_dotenv('.env')

    # 服务配置前缀
    prefix = f"{service_name.upper()}_"

    # 提取服务相关配置
    service_config = {}
    for key, value in os.environ.items():
        if key.startswith(prefix):
            service_config[key[len(prefix):]] = value

    return service_config
```

### 步骤3: 更新服务代码

更新各服务使用统一配置：

```python
# 之前: services/yunpat-agent/main.py
# from dotenv import load_dotenv
# load_dotenv()  # 加载 .env

# 之后: services/yunpat-agent/main.py
from core.config.service_config import load_service_config
config = load_service_config('yunpat_agent')
```

### 步骤4: 清理重复文件

运行整合脚本：
```bash
bash dev/scripts/cleanup_env_files.sh
```

## ✅ 验证清单

- [ ] 根`.env.template`包含所有服务配置
- [ ] 各服务能从统一配置加载参数
- [ ] 所有服务正常运行
- [ ] 分散的.env文件已删除或备份
- [ ] `.gitignore`正确配置

## 🔄 回滚方案

如果整合后出现问题：
```bash
# 从备份恢复
cp -r .env_backup_YYYYMMDD_HHMMSS/* .
```

## 📊 目标状态

| 指标 | 当前 | 目标 |
|------|------|------|
| .env文件总数 | 47 | ≤10 |
| 根目录配置 | 9 | 9 |
| 服务目录配置 | 30+ | 0 |
| 备份位置 | - | .env_backup_* |

## 📝 注意事项

1. **不要删除** `.env.secrets` - 它包含真实密钥
2. **不要删除** `.env.docker.prod` - Docker生产环境需要
3. **备份优先** - 删除前先备份所有文件
4. **渐进迁移** - 可以先整合部分服务，验证后再全面推广
