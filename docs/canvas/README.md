# Canvas/Host UI系统 - 快速开始

## 📖 什么是Canvas/Host UI系统？

Canvas/Host UI系统是Athena平台的实时用户界面渲染引擎，能够：
- 🎨 动态创建和管理UI组件（文本、进度条、图表、表格、指标、日志）
- 🔄 通过WebSocket实时推送更新
- 🤖 可视化Agent状态和任务进度
- 📊 构建监控仪表板和分析界面

---

## 🚀 5分钟快速开始

### 方法1: 运行演示程序（推荐）

```bash
# 进入项目目录
cd /Users/xujian/Athena工作平台

# 运行演示脚本
python examples/canvas_demo.py
```

演示程序包含4个示例：
1. **基础使用** - 创建Canvas和添加各种UI组件
2. **实时更新** - 模拟任务执行和进度更新
3. **专利分析仪表板** - 完整的专利分析界面
4. **WebSocket订阅** - 多客户端实时通信

### 方法2: 查看单元测试

```bash
# 运行Canvas Host测试
pytest tests/canvas/test_canvas_host.py -v

# 查看测试覆盖率
pytest tests/canvas/test_canvas_host.py --cov=core.canvas --cov-report=html
```

### 方法3: 启动Gateway（Go版本）

```bash
# 进入Gateway目录
cd gateway-unified

# 快速部署（macOS）
sudo bash quick-deploy-macos.sh

# 检查服务状态
sudo /usr/local/athena-gateway/status.sh

# 查看日志
sudo journalctl -u athena-gateway -f
```

Gateway启动后，访问：
- WebSocket: `ws://localhost:8005/ws`
- HTTP API: `http://localhost:8005/api`
- 健康检查: `http://localhost:8005/health`

---

## 📚 文档导航

| 文档 | 说明 |
|------|------|
| [使用指南](../guides/CANVAS_HOST_USAGE_GUIDE.md) | 完整的API文档和使用示例 |
| [Python实现](../../core/canvas/canvas_host.py) | Python版Canvas Host源码 |
| [Go实现](../../gateway-unified/internal/websocket/canvas/) | Go版Canvas Host源码 |
| [测试代码](../../tests/canvas/test_canvas_host.py) | 单元测试和集成测试 |
| [演示程序](../../examples/canvas_demo.py) | 可运行的示例代码 |

---

## 💡 常见使用场景

### 场景1: 专利分析仪表板

```python
from core.canvas.canvas_host import CanvasHost, UIComponentFactory

async def create_patent_dashboard():
    host = CanvasHost("patent_dashboard")
    await host.start()

    # 创建Canvas
    await host.create_canvas("patent_001", "专利分析: CN123456789A")

    # 添加相似度指标
    metric = UIComponentFactory.create_metric_component(
        component_id="similarity",
        title="相似度评分",
        metric_name="总体相似度",
        value=85.6,
        unit="%"
    )
    await host.add_component("patent_001", metric)

    # 添加进度条
    progress = UIComponentFactory.create_progress_component(
        component_id="progress",
        title="分析进度",
        current=3,
        total=5
    )
    await host.add_component("patent_001", progress)

    return host
```

### 场景2: Agent状态监控

```python
async def monitor_agents():
    host = CanvasHost("agent_monitor")
    await host.start()

    await host.create_canvas("agent_status", "Agent状态监控")

    # 实时更新Agent状态
    while True:
        for agent_id in ["xiaona", "xiaonuo", "yunxi"]:
            status = await get_agent_status(agent_id)

            # 更新指标
            await host.update_component(
                "agent_status",
                f"{agent_id}_cpu",
                {"value": status["cpu_usage"]}
            )

        await asyncio.sleep(5)  # 每5秒更新
```

### 场景3: 任务队列可视化

```python
async def visualize_tasks():
    host = CanvasHost("task_viz")
    await host.start()

    await host.create_canvas("task_queue", "任务队列")

    # 添加表格组件
    table = UIComponent(
        component_id="queue_table",
        component_type=UIComponentType.TABLE,
        title="等待处理的任务",
        data={
            "headers": ["任务ID", "类型", "优先级"],
            "rows": []
        }
    )
    await host.add_component("task_queue", table)

    # 定期更新
    while True:
        tasks = await get_pending_tasks()
        await host.update_component(
            "task_queue",
            "queue_table",
            {"rows": [[t["id"], t["type"], t["priority"]] for t in tasks]}
        )
        await asyncio.sleep(2)
```

---

## 🎨 支持的UI组件

| 组件类型 | 说明 | 工厂方法 |
|---------|------|---------|
| TEXT | 文本显示 | `create_text_component()` |
| PROGRESS | 进度条 | `create_progress_component()` |
| CHART | 图表（折线图、柱状图等） | `create_chart_component()` |
| TABLE | 表格 | `UIComponent(component_type=TABLE)` |
| METRIC | 指标卡片 | `create_metric_component()` |
| LOG | 日志列表 | `UIComponent(component_type=LOG)` |

---

## 🔌 API快速参考

### Canvas生命周期

```python
# 启动/停止
await host.start()
await host.stop()

# 创建/删除Canvas
await host.create_canvas(canvas_id, title)
await host.delete_canvas(canvas_id)

# 获取统计
stats = host.get_statistics()
```

### 组件管理

```python
# 添加组件
await host.add_component(canvas_id, component)

# 更新组件
await host.update_component(canvas_id, component_id, new_data)

# 移除组件
await host.remove_component(canvas_id, component_id)

# 获取所有组件
components = await host.get_canvas_components(canvas_id)
```

### WebSocket订阅

```python
# 订阅更新
await host.subscribe(client_id, websocket_connection)

# 取消订阅
await host.unsubscribe(client_id)
```

---

## 🧪 测试

```bash
# 运行所有测试
pytest tests/canvas/ -v

# 运行特定测试
pytest tests/canvas/test_canvas_host.py::TestCanvasHost -v

# 查看覆盖率
pytest tests/canvas/ --cov=core.canvas --cov-report=html
open htmlcov/index.html
```

---

## 🐛 故障排查

### 问题1: 导入错误

```bash
# 确保PYTHONPATH正确
export PYTHONPATH=/Users/xujian/Athena工作平台:$PYTHONPATH

# 或在代码中添加
import sys
sys.path.insert(0, '/Users/xujian/Athena工作平台')
```

### 问题2: 测试失败

```bash
# 检查Python版本
python3.11 --version  # 需要Python 3.11+

# 安装依赖
poetry install
# 或
pip install -r requirements.txt
```

### 问题3: Gateway无法启动

```bash
# 检查端口占用
lsof -i :8005

# 查看日志
sudo journalctl -u athena-gateway -n 50

# 重启服务
sudo systemctl restart athena-gateway
```

---

## 📞 获取帮助

- 📖 查看完整文档: `docs/guides/CANVAS_HOST_USAGE_GUIDE.md`
- 💻 查看示例代码: `examples/canvas_demo.py`
- 🧪 查看测试用例: `tests/canvas/test_canvas_host.py`
- 🐛 报告问题: 在GitHub上创建Issue

---

**最后更新**: 2026-04-20
**维护者**: Athena平台团队
