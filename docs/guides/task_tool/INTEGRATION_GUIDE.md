# Task Tool系统集成指南

**版本**: v1.0.0
**创建日期**: 2026-04-05
**作者**: Agent-3 (domain-adapter-tester)

---

## 📋 目录

1. [概述](#概述)
2. [快速开始](#快速开始)
3. [安装指南](#安装指南)
4. [配置指南](#配置指南)
5. [API集成](#api集成)
6. [工作流集成](#工作流集成)
7. [部署指南](#部署指南)
8. [故障排除](#故障排除)
9. [最佳实践](#最佳实践)

---

## 概述

Task Tool系统是Athena平台的核心任务执行框架,提供统一的任务执行接口。本指南帮助你将Task Tool集成到你的应用中。

### 核心特性

- ✅ 多模型支持 (haiku/sonnet/opus)
- ✅ 同步/异步执行模式
- ✅ 后台任务管理
- ✅ 专利领域特定代理类型
- ✅ 四层记忆系统集成
- ✅ 完整的API和示例

### 适用场景

- 专利分析系统
- 专利检索平台
- 法律研究工具
- AI代理系统
- 任务执行框架

---

## 快速开始

### 5分钟快速集成

```python
from core.agents.task_tool import TaskTool

# 1. 创建TaskTool实例
task_tool = TaskTool()

# 2. 执行任务
result = task_tool.execute(
    prompt="分析专利CN202310123456.7的技术方案",
    tools=["patent-search", "patent-analysis"],
    agent_type="analysis",
)

# 3. 获取结果
print(f"任务ID: {result['task_id']}")
print(f"状态: {result['status']}")
```

### 验证安装

```bash
# 检查Task Tool是否可用
python3 -c "from core.agents.task_tool import TaskTool; print('✅ Task Tool可用')"

# 验证配置
python3 scripts/validate_patent_config.py config/patent/patent_agents.yaml
```

---

## 安装指南

### 环境要求

- Python 3.10+
- pip (Python包管理器)
- 依赖项: 见`requirements.txt`

### 安装步骤

#### 1. 克隆仓库

```bash
cd /path/to/your/workspace
git clone https://github.com/your-org/Athena工作平台.git
cd Athena工作平台
```

#### 2. 创建虚拟环境 (推荐)

```bash
# 使用venv
python3 -m venv venv
source venv/bin/activate

# 或使用conda
conda create -n athena python=3.10
conda activate athena
```

#### 3. 安装依赖

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. 验证安装

```bash
python3 -c "
from core.agents.task_tool import TaskTool, ModelMapper, BackgroundTaskManager
print('✅ 所有核心模块可用')
"
```

### Docker安装

如果你使用Docker,可以使用预构建的镜像:

```bash
# 拉取镜像
docker pull athena-platform/task-tool:latest

# 运行容器
docker run -it --rm athena-platform/task-tool:latest

# 或使用docker-compose
docker-compose up -d
```

---

## 配置指南

### 配置文件结构

```
Athena工作平台/
├── config/
│   └── patent/
│       └── patent_agents.yaml    # 专利代理类型配置
├── core/
│   └── agents/
│       └── task_tool/
│           ├── models.py        # 数据模型
│           ├── model_mapper.py  # 模型映射器
│           ├── task_tool.py     # TaskTool主体
│           └── background_task_manager.py  # 后台任务管理器
└── .env                           # 环境变量
```

### 环境变量配置

创建`.env`文件:

```bash
# LLM模型配置
ATHENA_SUBAGENT_MODEL=sonnet  # 默认模型: haiku/sonnet/opus

# API密钥
ANTHROPIC_API_KEY=your_api_key_here

# 后台任务配置
ATHENA_MAX_WORKERS=10  # 最大并发任务数

# 日志配置
LOG_LEVEL=INFO  # DEBUG/INFO/WARNING/ERROR
```

### 专利代理类型配置

编辑`config/patent/patent_agents.yaml`:

```yaml
patent_agent_types:
  patent-analyst:
    model:
      primary: "sonnet"  # 使用的模型
    tools:
      required:
        - name: "patent-search"
        - name: "patent-analysis"
        - name: "knowledge-graph-query"
    capabilities:
      - name: "patent-technical-analysis"
```

验证配置:

```bash
python3 scripts/validate_patent_config.py config/patent/patent_agents.yaml
```

### 模型映射配置

编辑`core/agents/task_tool/model_mapper.py`:

```python
MODEL_MAPPING: Dict[str, str] = {
    "haiku": "quick",    # 快速模型
    "sonnet": "task",    # 任务模型
    "opus": "main",      # 主模型
}

MODEL_CONFIGS: Dict[str, Dict[str, Any]] = {
    "quick": {
        "name": "quick",
        "temperature": 0.7,
        "max_tokens": 4096,
    },
    "task": {
        "name": "task",
        "temperature": 0.5,
        "max_tokens": 8192,
    },
    "main": {
        "name": "main",
        "temperature": 0.3,
        "max_tokens": 16384,
    },
}
```

---

## API集成

### 基础集成

创建简单的API服务:

```python
from flask import Flask, request, jsonify
from core.agents.task_tool import TaskTool

app = Flask(__name__)
task_tool = TaskTool()

@app.route('/api/execute', methods=['POST'])
def execute_task():
    """执行任务API"""
    data = request.json

    try:
        result = task_tool.execute(
            prompt=data['prompt'],
            tools=data.get('tools', []),
            model=data.get('model'),
            agent_type=data.get('agent_type'),
        )
        return jsonify({
            'success': True,
            'task_id': result['task_id'],
            'status': result['status'],
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### 异步任务集成

支持异步任务提交和状态查询:

```python
from flask import Flask, request, jsonify
from core.agents.task_tool import TaskTool, BackgroundTaskManager

app = Flask(__name__)
task_tool = TaskTool()
task_manager = BackgroundTaskManager(max_workers=10)

@app.route('/api/submit', methods=['POST'])
def submit_task():
    """提交后台任务"""
    data = request.json

    try:
        task = task_manager.submit(
            func=task_tool.execute,
            kwargs={
                'prompt': data['prompt'],
                'tools': data.get('tools', []),
                'agent_type': data.get('agent_type'),
                'background': False,
            },
            agent_id=data.get('agent_id'),
        )
        return jsonify({
            'success': True,
            'task_id': task.task_id,
            'status': 'submitted',
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
        }), 500

@app.route('/api/status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """查询任务状态"""
    task = task_manager.get_task(task_id)
    if task:
        return jsonify({
            'success': True,
            'task_id': task_id,
            'status': task.status.value,
            'created_at': task.created_at,
            'updated_at': task.updated_at,
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Task not found',
        }), 404
```

### FastAPI集成

使用FastAPI (推荐):

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from core.agents.task_tool import TaskTool

app = FastAPI()
task_tool = TaskTool()

class TaskRequest(BaseModel):
    prompt: str
    tools: list[str] = []
    model: str | None = None
    agent_type: str | None = None

@app.post("/api/execute")
async def execute_task(request: TaskRequest):
    """执行任务API"""
    try:
        result = task_tool.execute(
            prompt=request.prompt,
            tools=request.tools,
            model=request.model,
            agent_type=request.agent_type,
        )
        return {
            'success': True,
            'task_id': result['task_id'],
            'status': result['status'],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 运行
# uvicorn main:app --host 0.0.0.0 --port 5000
```

---

## 工作流集成

### 专利分析工作流集成

```python
from core.patent.workflows import AnalysisWorkflow

# 创建工作流实例
workflow = AnalysisWorkflow()

# 执行工作流
result = workflow.execute(
    patent_number="CN202310123456.7",
    analysis_type="comprehensive",
    include_comparison=True,
    generate_report=True,
    report_format="pdf",
    report_path="/path/to/report.pdf",
)

# 处理结果
if result['success']:
    print(f"分析完成: {result['report_path']}")
else:
    print(f"分析失败: {result['error']}")
```

### 专利检索工作流集成

```python
from core.patent.workflows import SearchWorkflow

# 创建工作流实例
workflow = SearchWorkflow()

# 执行工作流
result = workflow.execute(
    query="量子计算",
    data_sources=["local", "online"],
    max_results=50,
    export_format="csv",
    export_path="/path/to/results.csv",
)

# 处理结果
if result['success']:
    print(f"检索完成: 找到{result['total_count']}条专利")
    print(f"导出路径: {result['export_path']}")
else:
    print(f"检索失败: {result['error']}")
```

### 法律研究工作流集成

```python
from core.patent.workflows import LegalWorkflow

# 创建工作流实例
workflow = LegalWorkflow()

# 执行工作流
result = workflow.execute(
    legal_query="分析专利侵权判例",
    case_types=["infringement", "invalidation"],
    include_trend_analysis=True,
    generate_opinion=True,
)

# 处理结果
if result['success']:
    print(f"研究完成")
    print(f"法律意见: {result['legal_opinion']}")
else:
    print(f"研究失败: {result['error']}")
```

### 工作流链式调用

```python
from core.patent.workflows import AnalysisWorkflow, SearchWorkflow, LegalWorkflow

# 创建工作流实例
analysis_workflow = AnalysisWorkflow()
search_workflow = SearchWorkflow()
legal_workflow = LegalWorkflow()

# 链式调用
# 1. 检索专利
search_result = search_workflow.execute(query="量子计算")
if not search_result['success']:
    raise Exception("检索失败")

# 2. 分析专利
analysis_result = analysis_workflow.execute(
    patent_number=search_result['results'][0]['patent_number'],
)
if not analysis_result['success']:
    raise Exception("分析失败")

# 3. 法律研究
legal_result = legal_workflow.execute(
    legal_query=f"评估专利{search_result['results'][0]['patent_number']}的侵权风险",
)
if not legal_result['success']:
    raise Exception("法律研究失败")

print("所有工作流执行成功!")
```

---

## 部署指南

### 本地部署

```bash
# 1. 启动服务
python3 scripts/xiaonuo_unified_startup.py 启动平台

# 2. 验证服务
curl http://localhost:8005/health
```

### Docker部署

```bash
# 1. 构建镜像
docker build -t athena-task-tool:latest .

# 2. 运行容器
docker run -d \
  --name athena-task-tool \
  -p 8005:8005 \
  -v /path/to/config:/app/config \
  athena-task-tool:latest

# 3. 查看日志
docker logs -f athena-task-tool
```

### Docker Compose部署

创建`docker-compose.yml`:

```yaml
version: '3.8'

services:
  athena-task-tool:
    build: .
    container_name: athena-task-tool
    ports:
      - "8005:8005"
    volumes:
      - ./config:/app/config
      - ./data:/app/data
    environment:
      - ATHENA_SUBAGENT_MODEL=sonnet
      - ATHENA_MAX_WORKERS=10
      - LOG_LEVEL=INFO
    restart: unless-stopped
```

启动服务:

```bash
docker-compose up -d
```

### 生产环境部署

```bash
# 1. 使用生产配置
export ENVIRONMENT=production

# 2. 启动服务
python3 scripts/xiaonuo_unified_startup.py 启动平台

# 3. 使用systemd管理 (Linux)
sudo systemctl start athena-task-tool

# 4. 使用launchd管理 (macOS)
sudo launchctl load /Library/LaunchDaemons/com.athena.task-tool.plist
```

---

## 故障排除

### 常见问题

#### 问题1: 模块导入错误

**错误信息**:
```
ModuleNotFoundError: No module named 'core.agents.task_tool'
```

**解决方案**:
```bash
# 设置PYTHONPATH
export PYTHONPATH=/Users/xujian/Athena工作平台:$PYTHONPATH

# 或在代码中添加路径
import sys
sys.path.insert(0, '/Users/xujian/Athena工作平台')
```

#### 问题2: 配置文件验证失败

**错误信息**:
```
ValueError: config/patent/patent_agents.yaml 验证失败
```

**解决方案**:
```bash
# 运行配置验证脚本
python3 scripts/validate_patent_config.py config/patent/patent_agents.yaml

# 修复错误后重新验证
```

#### 问题3: 任务超时

**错误信息**:
```
TimeoutError: Task xxx timed out after 60 seconds
```

**解决方案**:
```python
# 增加超时时间
result = task_manager.wait_get_task(
    task_id=task_id,
    timeout=120,  # 增加到120秒
)
```

#### 问题4: 后台任务失败

**错误信息**:
```
RuntimeError: BackgroundTaskManager has been shut down
```

**解决方案**:
```python
# 确保在提交任务前管理器未关闭
if not task_manager._is_shutdown:
    task = task_manager.submit(func=my_task)
else:
    print("管理器已关闭,无法提交任务")
```

#### 问题5: 内存占用过高

**错误信息**:
```
MemoryError: unable to allocate memory
```

**解决方案**:
```python
# 降低并发数
task_manager = BackgroundTaskManager(max_workers=5)  # 从10降到5

# 或优化任务,减少内存使用
```

### 日志查看

```bash
# 查看应用日志
tail -f logs/athena-task-tool.log

# 查看错误日志
grep ERROR logs/athena-task-tool.log

# 查看特定任务的日志
grep "task_id" logs/athena-task-tool.log | grep "550e8400-e29b-41d4-a716-446655440000"
```

### 性能监控

```bash
# 查看系统资源
top

# 查看Python进程
ps aux | grep python

# 查看端口占用
lsof -i :8005
```

---

## 最佳实践

### 1. 错误处理

```python
try:
    result = task_tool.execute(
        prompt="执行任务",
        tools=["tool1", "tool2"],
    )
except ValueError as e:
    # 输入验证错误
    logger.error(f"输入验证错误: {e}")
except RuntimeError as e:
    # 运行时错误
    logger.error(f"运行时错误: {e}")
except Exception as e:
    # 未知错误
    logger.error(f"未知错误: {e}")
    raise
```

### 2. 资源管理

```python
# 使用上下文管理器
with BackgroundTaskManager(max_workers=10) as manager:
    task = manager.submit(func=my_task)
    # ... 其他操作
# 管理器自动关闭
```

### 3. 任务重试

```python
# 实现指数退避重试
import time

max_retries = 3
retry_delay = 2  # 初始延迟(秒)

for attempt in range(max_retries):
    try:
        result = task_tool.execute(
            prompt="执行任务",
            tools=["tool1", "tool2"],
        )
        break
    except Exception as e:
        if attempt < max_retries - 1:
            wait_time = retry_delay * (2 ** attempt)  # 指数退避
            time.sleep(wait_time)
        else:
            raise
```

### 4. 日志记录

```python
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

# 使用日志
logger = logging.getLogger(__name__)

logger.info("任务开始执行")
logger.warning("任务执行超时")
logger.error("任务执行失败", exc_info=True)
```

### 5. 配置管理

```python
# 使用环境变量
import os

model = os.getenv("ATHENA_SUBAGENT_MODEL", "sonnet")
max_workers = int(os.getenv("ATHENA_MAX_WORKERS", "10"))

# 使用配置文件
import yaml

with open("config/patent/patent_agents.yaml") as f:
    config = yaml.safe_load(f)
```

---

## 附录

### A. 环境变量参考

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `ATHENA_SUBAGENT_MODEL` | 默认LLM模型 | sonnet |
| `ATHENA_MAX_WORKERS` | 后台任务最大并发数 | 10 |
| `ANTHROPIC_API_KEY` | Anthropic API密钥 | - |
| `LOG_LEVEL` | 日志级别 | INFO |
| `PYTHONPATH` | Python模块搜索路径 | - |

### B. 端口参考

| 端口 | 服务 | 说明 |
|------|------|------|
| 8005 | Task Tool API | 主API端口 |
| 8006 | 后台任务API | 后台任务端口 |
| 5432 | PostgreSQL | 数据库端口 |
| 6379 | Redis | 缓存端口 |

### C. 目录结构

```
Athena工作平台/
├── config/                    # 配置文件
│   └── patent/
│       └── patent_agents.yaml
├── core/
│   └── agents/
│       └── task_tool/        # Task Tool核心模块
├── docs/
│   ├── api/task_tool/         # API文档
│   ├── examples/task_tool/    # 使用示例
│   └── guides/task_tool/     # 集成指南
├── logs/                      # 日志文件
├── data/                      # 运行时数据
└── tests/                     # 测试文件
```

### D. 相关文档

- API文档: `/docs/api/task_tool/API.md`
- 使用示例: `/docs/examples/task_tool/`
- 专利需求分析: `/docs/reports/task-tool-system-implementation/domain-analysis/T3-1-patent-domain-requirements-analysis.md`
- 代理类型配置: `/config/patent/patent_agents.yaml`

---

## 支持

如有问题或需要帮助,请联系:

- **GitHub Issues**: https://github.com/your-org/Athena工作平台/issues
- **Email**: support@example.com
- **文档**: https://docs.example.com

---

**集成指南版本**: v1.0.0
**最后更新**: 2026-04-05
**维护者**: Agent-3 (domain-adapter-tester)
