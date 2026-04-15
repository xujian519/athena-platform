# 专利全文处理系统 - 小诺调度部署指南

## 版本信息
- **版本**: v3.0.0
- **更新时间**: 2025-12-25
- **部署模式**: 小诺调度 + 按需启动

---

## 一、部署架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         小诺 (Xiaonuo)                          │
│                    (AI智能调度中心)                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    服务管理器 (按需启动)                          │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              根据任务类型自动启动必要服务                  │    │
│  │                                                         │    │
│  │  process_patent     → qdrant + nebula + redis + app     │    │
│  │  download_pdfs      → 无需额外服务                         │    │
│  │  search_patents     → qdrant + redis + app               │    │
│  │  get_patent_triples → nebula + app                        │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Docker服务集群                            │
│                                                                 │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐               │
│  │ Qdrant  │ │ Nebula  │ │  Redis  │ │   App   │               │
│  │ (向量DB)│ │ (图DB)  │ │ (缓存)  │ │(主应用) │               │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 二、小诺调度接口

### 2.1 服务管理工具 (新增4个)

| 工具名称 | 功能描述 | 使用场景 |
|---------|---------|---------|
| `start_patent_services` | 按需启动服务 | 执行任务前自动启动必要服务 |
| `stop_patent_services` | 停止服务 | 任务完成后释放资源 |
| `get_services_status` | 查询服务状态 | 检查服务运行情况 |
| `restart_patent_services` | 重启服务 | 服务异常时重启 |

### 2.2 完整工具清单 (18个)

**专利分析 (3个)**:
- `process_patent` - 处理专利全文
- `process_patent_batch` - 批量处理专利
- `get_patent_triples` - 获取专利三元组

**专利下载 (1个)**:
- `download_patent_pdfs` - 下载专利PDF

**专利检索 (2个)**:
- `search_cn_patents` - 检索中国专利
- `search_patents` - 向量搜索专利

**系统管理 (8个)**:
- `start_pdf_monitor` - 启动PDF监控
- `stop_pdf_monitor` - 停止PDF监控
- `get_pdf_monitor_status` - PDF监控状态
- `get_cache_stats` - 缓存统计
- `clear_cache` - 清除缓存
- `get_performance_stats` - 性能统计
- `get_database_status` - 数据库状态
- `get_patent_tool_status` - 工具状态

**服务管理 (4个)**:
- `start_patent_services` - 启动专利服务 ⭐
- `stop_patent_services` - 停止专利服务 ⭐
- `get_services_status` - 服务运行状态 ⭐
- `restart_patent_services` - 重启专利服务 ⭐

---

## 三、快速开始

### 3.1 验证部署

```bash
cd /Users/xujian/Athena工作平台/production/dev/scripts/patent_full_text

# 运行部署验证
python deploy_verify.py
```

### 3.2 初始化环境

```bash
# 初始化生产环境
python config_manager.py init --env production

# 查看配置
python config_manager.py show --env production
```

### 3.3 手动启动服务

```bash
# 启动所有服务
python service_manager.py start --service all

# 查看服务状态
python service_manager.py status

# 停止所有服务
python service_manager.py stop --service all
```

---

## 四、小诺调度使用

### 4.1 方式一：手动启动服务

```python
from tools.xiaonuo_patent_integration import get_xiaonuo_patent_registry

registry = get_xiaonuo_patent_registry()

# 1. 启动必要服务
registry.execute_tool(
    "start_patent_services",
    task_type="process_patent",
    auto_stop=False,
    idle_timeout=300
)

# 2. 执行专利处理
registry.execute_tool(
    "process_patent",
    patent_number="CN112233445A",
    title="专利标题",
    abstract="专利摘要",
    ipc_classification="G06F40/00"
)

# 3. 任务完成后停止服务
registry.execute_tool("stop_patent_services", service="all")
```

### 4.2 方式二：自动按需启动（推荐）

在小诺中集成自动启动逻辑：

```python
class XiaonuoPatentScheduler:
    """小诺专利调度器"""

    def __init__(self):
        self.registry = get_xiaonuo_patent_registry()

    def process_patent_auto(self, **kwargs):
        """自动处理专利（包含服务管理）"""

        # 1. 自动启动服务
        self.registry.execute_tool(
            "start_patent_services",
            task_type="process_patent",
            auto_stop=False  # 不自动停止，保持运行以便处理更多任务
        )

        # 2. 执行处理
        result = self.registry.execute_tool("process_patent", **kwargs)

        # 3. 返回结果
        return result

    def search_patents_auto(self, query: str, limit: int = 10):
        """自动搜索专利"""

        # 启动必要服务（qdrant + redis + app）
        self.registry.execute_tool(
            "start_patent_services",
            task_type="search_patents"
        )

        # 执行搜索
        result = self.registry.execute_tool(
            "search_patents",
            query=query,
            limit=limit
        )

        return result
```

---

## 五、服务管理详解

### 5.1 按需启动逻辑

| 任务类型 | 启动的服务 | 说明 |
|---------|-----------|------|
| `process_patent` | qdrant + nebula + redis + app | 需要所有服务 |
| `download_pdfs` | 无 | PDF下载独立运行 |
| `search_patents` | qdrant + redis + app | 不需要图数据库 |
| `get_patent_triples` | nebula + app | 只需要图数据库 |
| `cache_stats` | redis | 只需要缓存 |

### 5.2 服务状态查询

```python
# 查询所有服务状态
status = registry.execute_tool("get_services_status")

print(status)
# {
#     "success": true,
#     "services": {
#         "qdrant": {"status": "running", "uptime": 3600, ...},
#         "nebula": {"status": "running", "uptime": 3600, ...},
#         "redis": {"status": "running", "uptime": 3600, ...},
#         "app": {"status": "running", "uptime": 3600, ...}
#     }
# }
```

### 5.3 自动停止策略

```python
# 启动服务时设置自动停止
registry.execute_tool(
    "start_patent_services",
    task_type="process_patent",
    auto_stop=True,        # 任务完成后自动停止
    idle_timeout=300       # 空闲5分钟后停止
)
```

---

## 六、生产部署流程

### 6.1 初始化部署

```bash
# 1. 验证部署
python deploy_verify.py

# 2. 初始化配置
python config_manager.py init --env production

# 3. 启动服务
python service_manager.py start --service all

# 4. 健康检查
python health_check.py
```

### 6.2 小诺集成验证

```bash
# 测试小诺工具注册
python dev/tools/test_patent_tool_registration.py

# 预期输出:
# ✅ 小诺工具数量: 18个
# ✅ 服务管理工具: 4个
```

### 6.3 完整工作流

```
┌─────────────────────────────────────────────────────────────────┐
│                     用户请求处理专利                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    小诺接收请求                                 │
│                                                                 │
│  1. 解析任务类型                                                │
│  2. 确定需要的服务                                              │
│  3. 调用 start_patent_services                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 服务管理器自动启动服务                           │
│                                                                 │
│  • 根据task_type确定必要服务                                    │
│  • docker-compose up -d [services]                             │
│  • 健康检查确认服务就绪                                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    执行专利处理任务                              │
│                                                                 │
│  • 调用 process_patent                                         │
│  • 向量化、三元组提取、知识图谱构建                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    返回处理结果                                 │
│                                                                 │
│  • vectors: 生成的向量数量                                      │
│  • triples: 提取的三元组数量                                    │
│  • vertices: 创建的顶点数量                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              (可选) 自动停止服务释放资源                         │
│                                                                 │
│  • 如果设置了 auto_stop=True                                   │
│  • 或空闲时间超过 idle_timeout                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 七、故障排查

### 7.1 服务启动失败

```bash
# 查看Docker日志
docker-compose logs qdrant
docker-compose logs nebula-graphd
docker-compose logs app

# 重启单个服务
python service_manager.py restart --service qdrant
```

### 7.2 小诺工具调用失败

```bash
# 验证工具注册
python dev/tools/test_patent_tool_registration.py

# 检查服务状态
python service_manager.py status

# 查看服务日志
docker-compose logs -f app
```

---

## 八、最佳实践

1. **按需启动** - 只在需要时启动服务，节省资源
2. **批量处理** - 保持服务运行，批量处理多个专利
3. **监控状态** - 定期检查服务状态，及时发现问题
4. **自动停止** - 任务完成后自动停止，避免资源浪费
5. **日志记录** - 记录服务启动/停止时间，便于审计

---

## 九、文件清单

| 文件 | 说明 |
|------|------|
| `service_manager.py` | 服务管理器 |
| `config_manager.py` | 配置管理器 |
| `health_check.py` | 健康检查脚本 |
| `deploy_verify.py` | 部署验证脚本 |
| `dev/tools/patent_full_text_tool.py` | 小诺工具接口 |
| `dev/tools/xiaonuo_patent_integration.py` | 小诺集成注册 |

---

**部署完成时间**: 2025-12-25
**版本**: v3.0.0
**状态**: ✅ 已集成小诺调度 + 按需启动
