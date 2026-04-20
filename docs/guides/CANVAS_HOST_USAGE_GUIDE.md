# Canvas/Host UI系统使用指南

## 📖 系统概述

Canvas/Host UI系统是Athena平台的实时用户界面渲染引擎，支持：
- 🎨 动态UI组件渲染（文本、进度条、图表、表格、指标、日志）
- 🔄 WebSocket实时更新
- 🤖 Agent状态可视化
- 📊 任务监控仪表板
- 🌐 响应式布局

---

## 🏗️ 架构设计

```
┌─────────────────────────────────────────────────────┐
│              Gateway (Go, Port 8005)                │
│  ┌──────────────────────────────────────────────┐  │
│  │   CanvasHost Service                         │  │
│  │   - Canvas管理 (host.go)                     │  │
│  │   - Agent可视化 (agent_visualizer.go)        │  │
│  │   - WebSocket控制器 (websocket.go)           │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
         │ WebSocket              │ HTTP REST
         │                        │
    ┌────▼────┐              ┌────▼────┐
    │ 前端UI   │              │ Python  │
    │ (浏览器) │              │ 后端    │
    └─────────┘              └─────────┘
```

---

## 🐍 Python版本使用

### 1. 基础使用

```python
import asyncio
from core.canvas.canvas_host import (
    CanvasHost,
    UIComponentFactory,
    UIComponentType,
)

async def main():
    # 1. 创建Canvas Host
    host = CanvasHost("xiaona_dashboard")
    await host.start()
    
    # 2. 创建Canvas
    await host.create_canvas(
        canvas_id="patent_analysis",
        title="专利分析仪表板"
    )
    
    # 3. 添加UI组件
    
    # 文本组件
    text_component = UIComponentFactory.create_text_component(
        component_id="status_text",
        title="分析状态",
        text="正在分析专利CN123456789A..."
    )
    await host.add_component("patent_analysis", text_component)
    
    # 进度条组件
    progress_component = UIComponentFactory.create_progress_component(
        component_id="analysis_progress",
        title="分析进度",
        current=3,
        total=5
    )
    await host.add_component("patent_analysis", progress_component)
    
    # 指标组件
    metric_component = UIComponentFactory.create_metric_component(
        component_id="similarity_score",
        title="相似度指标",
        metric_name="相似度得分",
        value=85.6,
        unit="%"
    )
    await host.add_component("patent_analysis", metric_component)
    
    # 图表组件
    chart_data = [
        {"x": "权利要求1", "y": 0.85},
        {"x": "权利要求2", "y": 0.72},
        {"x": "权利要求3", "y": 0.91},
    ]
    chart_component = UIComponentFactory.create_chart_component(
        component_id="similarity_chart",
        title="相似度对比图",
        chart_type="bar",
        data=chart_data
    )
    await host.add_component("patent_analysis", chart_component)
    
    # 4. 更新组件
    await host.update_component(
        "patent_analysis",
        "analysis_progress",
        {"current": 4, "total": 5}
    )
    
    # 5. 获取统计信息
    stats = host.get_statistics()
    print(f"Canvas数量: {stats['total_canvases']}")
    
    # 6. 停止服务
    await host.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. 实时更新示例

```python
async def monitor_patent_analysis(host: CanvasHost, patent_id: str):
    """监控专利分析进度"""
    
    # 创建监控Canvas
    canvas_id = f"analysis_{patent_id}"
    await host.create_canvas(canvas_id, f"专利分析: {patent_id}")
    
    # 添加进度条
    progress = UIComponentFactory.create_progress_component(
        component_id="progress",
        title="分析进度",
        current=0,
        total=100
    )
    await host.add_component(canvas_id, progress)
    
    # 添加日志组件
    log_component = UIComponent(
        component_id="logs",
        component_type=UIComponentType.LOG,
        title="分析日志",
        data={"entries": []}
    )
    await host.add_component(canvas_id, log_component)
    
    # 模拟分析过程
    stages = [
        "检索现有技术",
        "分析权利要求",
        "评估创造性",
        "生成报告"
    ]
    
    for i, stage in enumerate(stages):
        # 更新进度
        progress_value = int((i + 1) / len(stages) * 100)
        await host.update_component(
            canvas_id,
            "progress",
            {"current": progress_value, "total": 100}
        )
        
        # 添加日志
        logs = log_component.data["entries"]
        logs.append({
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "level": "INFO",
            "message": f"完成: {stage}"
        })
        await host.update_component(
            canvas_id,
            "logs",
            {"entries": logs}
        )
        
        await asyncio.sleep(1)  # 模拟处理时间
    
    # 添加完成指标
    final_metric = UIComponentFactory.create_metric_component(
        component_id="final_score",
        title="分析结果",
        metric_name="创造性评分",
        value=8.5,
        unit="/10"
    )
    await host.add_component(canvas_id, final_metric)
```

### 3. WebSocket订阅示例

```python
# 模拟WebSocket连接类
class MockWebSocket:
    def __init__(self):
        self.messages = []
    
    async def send(self, message: str):
        """接收Canvas更新"""
        data = json.loads(message)
        print(f"[WebSocket] 收到更新: {data['type']}")
        self.messages.append(data)

async def setup_realtime_updates(host: CanvasHost):
    """设置实时更新"""
    
    # 创建WebSocket连接
    ws = MockWebSocket()
    
    # 订阅Canvas更新
    await host.subscribe("client_001", ws)
    
    # 创建Canvas
    await host.create_canvas("realtime_canvas", "实时更新测试")
    
    # 添加组件（会自动广播到订阅者）
    component = UIComponentFactory.create_text_component(
        component_id="test_text",
        title="实时文本",
        text="这是一个实时更新的文本"
    )
    await host.add_component("realtime_canvas", component)
    
    # 更新组件（会自动广播）
    await host.update_component(
        "realtime_canvas",
        "test_text",
        {"text": "文本已更新！"}
    )
    
    # 取消订阅
    await host.unsubscribe("client_001")
```

---

## 🌐 Go版本使用（Gateway集成）

### 1. 通过WebSocket连接

```javascript
// 前端代码 - 连接到Gateway
const ws = new WebSocket('ws://localhost:8005/ws');

// 发送握手消息
ws.send(JSON.stringify({
    id: "handshake_001",
    type: "handshake",
    data: {
        client_id: "web_client_001",
        capabilities: ["canvas", "task"]
    }
}));

// 监听消息
ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    
    if (message.type === "canvas_update") {
        renderCanvasUpdate(message.data);
    }
};

// 渲染Canvas更新
function renderCanvasUpdate(data) {
    const { canvas_id, component } = data;
    
    // 创建或更新Canvas容器
    let container = document.getElementById(canvas_id);
    if (!container) {
        container = document.createElement('div');
        container.id = canvas_id;
        container.className = 'canvas-container';
        document.body.appendChild(container);
    }
    
    // 渲染组件
    const componentDiv = document.createElement('div');
    componentDiv.className = `component component-${component.component_type}`;
    componentDiv.innerHTML = `
        <div class="component-title">${component.title}</div>
        <div class="component-content">${renderComponentContent(component)}</div>
    `;
    container.appendChild(componentDiv);
}

function renderComponentContent(component) {
    switch (component.component_type) {
        case 'text':
            return component.data.text;
        case 'progress':
            return `
                <progress value="${component.data.current}" 
                         max="${component.data.total}">
                </progress>
                <span>${component.data.percentage.toFixed(1)}%</span>
            `;
        case 'metric':
            return `
                <div class="metric-value">${component.data.value}</div>
                <div class="metric-unit">${component.data.unit}</div>
            `;
        // ... 其他组件类型
        default:
            return '';
    }
}
```

### 2. HTTP API调用

```bash
# 创建Canvas
curl -X POST http://localhost:8005/api/canvas \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session_001",
    "title": "专利分析仪表板"
  }'

# 添加组件
curl -X POST http://localhost:8005/api/canvas/{canvas_id}/components \
  -H "Content-Type: application/json" \
  -d '{
    "component_id": "metric_001",
    "component_type": "metric",
    "title": "相似度得分",
    "data": {
      "metric_name": "相似度",
      "value": 85.6,
      "unit": "%"
    }
  }'

# 更新组件
curl -X PUT http://localhost:8005/api/canvas/{canvas_id}/components/{component_id} \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "value": 90.2
    }
  }'

# 获取Canvas
curl http://localhost:8005/api/canvas/{canvas_id}
```

### 3. Go代码集成

```go
package main

import (
    "context"
    "log"
    "time"
    
    "github.com/athena-workspace/gateway-unified/internal/websocket/canvas"
)

func main() {
    // 创建Canvas Host
    host := canvas.NewCanvasHost()
    defer host.Close()
    
    // 创建Canvas
    c := host.CreateCanvas("session_001", "专利分析")
    
    // 添加指标组件
    host.AddComponent(c.ID, &canvas.Component{
        ID:   "similarity_metric",
        Type: "metric",
        Data: map[string]interface{}{
            "metric_name": "相似度",
            "value":       85.6,
            "unit":        "%",
        },
    })
    
    // 更新组件
    host.UpdateComponent(c.ID, "similarity_metric", map[string]interface{}{
        "value": 90.2,
    })
    
    // 渲染Canvas
    html := host.Render(c.ID)
    log.Println("渲染的HTML:", html)
    
    // 保持运行
    time.Sleep(5 * time.Second)
}
```

---

## 🎯 实际应用场景

### 场景1: 专利分析仪表板

```python
async def create_patent_analysis_dashboard(patent_id: str):
    """创建专利分析仪表板"""
    
    host = CanvasHost(f"patent_{patent_id}")
    await host.start()
    
    # 创建仪表板Canvas
    canvas_id = f"patent_dashboard_{patent_id}"
    await host.create_canvas(canvas_id, f"专利分析: {patent_id}")
    
    # 布局：顶部指标卡片
    metrics = [
        {"title": "相似度", "value": "85.6%", "type": "primary"},
        {"title": "权利要求数", "value": "10", "type": "info"},
        {"title": "引用文献", "value": "23", "type": "warning"},
        {"title": "法律状态", "value": "有效", "type": "success"},
    ]
    
    for i, metric in enumerate(metrics):
        component = UIComponent(
            component_id=f"metric_{i}",
            component_type=UIComponentType.METRIC,
            title=metric["title"],
            data={
                "metric_name": metric["title"],
                "value": metric["value"],
                "type": metric["type"]
            },
            position={"row": 0, "col": i}
        )
        await host.add_component(canvas_id, component)
    
    # 中部：相似度对比图表
    chart_data = {
        "labels": ["权利要求1", "权利要求2", "权利要求3"],
        "datasets": [{
            "label": "相似度得分",
            "data": [0.85, 0.72, 0.91],
            "color": "#4CAF50"
        }]
    }
    
    chart = UIComponentFactory.create_chart_component(
        component_id="similarity_chart",
        title="权利要求相似度分析",
        chart_type="bar",
        data=chart_data
    )
    chart.position = {"row": 1, "col": 0, "colspan": 2}
    await host.add_component(canvas_id, chart)
    
    # 底部：分析日志
    log_component = UIComponent(
        component_id="analysis_logs",
        component_type=UIComponentType.LOG,
        title="分析日志",
        data={"entries": []},
        position={"row": 2, "col": 0, "colspan": 4}
    )
    await host.add_component(canvas_id, log_component)
    
    return host
```

### 场景2: Agent状态监控

```python
async def monitor_agent_status():
    """监控Agent状态"""
    
    host = CanvasHost("agent_monitor")
    await host.start()
    
    await host.create_canvas("agent_status", "Agent状态监控")
    
    # 实时更新Agent状态
    while True:
        for agent_id in ["xiaona", "xiaonuo", "yunxi"]:
            # 获取Agent状态（示例）
            status = await get_agent_status(agent_id)
            
            # 更新指标
            await host.update_component(
                "agent_status",
                f"{agent_id}_tasks",
                {"current": status["completed_tasks"], "total": status["total_tasks"]}
            )
            
            # 更新日志
            if status["recent_logs"]:
                await host.update_component(
                    "agent_status",
                    f"{agent_id}_logs",
                    {"entries": status["recent_logs"]}
                )
        
        await asyncio.sleep(5)  # 每5秒更新一次
```

### 场景3: 任务队列可视化

```python
async def visualize_task_queue():
    """可视化任务队列"""
    
    host = CanvasHost("task_queue_viz")
    await host.start()
    
    await host.create_canvas("task_queue", "任务队列")
    
    # 添加队列统计表格
    table_component = UIComponent(
        component_id="queue_table",
        component_type=UIComponentType.TABLE,
        title="等待处理的任务",
        data={
            "headers": ["任务ID", "类型", "优先级", "等待时间"],
            "rows": []
        }
    )
    await host.add_component("task_queue", table_component)
    
    # 定期更新
    while True:
        tasks = await get_pending_tasks()
        
        rows = []
        for task in tasks[:10]:  # 只显示前10个
            rows.append([
                task["id"],
                task["type"],
                task["priority"],
                f"{task["wait_time"]}秒"
            ])
        
        await host.update_component(
            "task_queue",
            "queue_table",
            {"rows": rows}
        )
        
        await asyncio.sleep(2)
```

---

## 🔌 集成到Athena平台

### 1. 在小娜Agent中使用

```python
from core.agents.xiaona_agent import XiaonaAgent
from core.canvas.canvas_host import CanvasHost

class XiaonaAgentWithUI(XiaonaAgent):
    def __init__(self):
        super().__init__()
        self.canvas_host = CanvasHost("xiaona_ui")
    
    async def analyze_patent(self, patent_id: str):
        """分析专利并显示UI"""
        
        # 启动Canvas服务
        await self.canvas_host.start()
        
        # 创建分析Canvas
        canvas_id = f"analysis_{patent_id}"
        await self.canvas_host.create_canvas(
            canvas_id,
            f"专利分析: {patent_id}"
        )
        
        # 添加进度条
        progress = UIComponentFactory.create_progress_component(
            component_id="progress",
            title="分析进度",
            current=0,
            total=100
        )
        await self.canvas_host.add_component(canvas_id, progress)
        
        # 执行分析步骤
        steps = ["检索", "分析", "评估", "报告"]
        for i, step in enumerate(steps):
            # 执行实际分析
            result = await getattr(self, f"_step_{step}")(patent_id)
            
            # 更新进度
            await self.canvas_host.update_component(
                canvas_id,
                "progress",
                {"current": (i + 1) * 25, "total": 100}
            )
            
            # 显示结果
            await self._show_result(canvas_id, step, result)
        
        await self.canvas_host.stop()
```

### 2. 通过Gateway访问

```bash
# 1. 启动Gateway
cd /Users/xujian/Athena工作平台/gateway-unified
sudo bash quick-deploy-macos.sh

# 2. 检查服务状态
sudo /usr/local/athena-gateway/status.sh

# 3. 查看日志
sudo journalctl -u athena-gateway -f

# 4. 测试WebSocket连接
wscat -c ws://localhost:8005/ws

# 5. 测试HTTP API
curl http://localhost:8005/health
```

---

## 📱 前端模板示例

### 默认HTML模板

```html
<!DOCTYPE html>
<html>
<head>
    <title>Athena Canvas</title>
    <style>
        .canvas-container {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            padding: 20px;
        }
        .component {
            background: white;
            border-radius: 8px;
            padding: 16px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .component-title {
            font-weight: bold;
            margin-bottom: 12px;
        }
        .component-metric .metric-value {
            font-size: 32px;
            color: #4CAF50;
        }
    </style>
</head>
<body>
    <div id="agent-grid" class="canvas-container"></div>
    <script src="/static/canvas.js"></script>
</body>
</html>
```

---

## 🚀 快速开始

### Python快速开始

```python
# 1. 安装依赖
pip install -r requirements.txt

# 2. 运行示例
python examples/canvas_demo.py

# 3. 测试
pytest tests/canvas/test_canvas_host.py -v
```

### Go快速开始

```bash
# 1. 启动Gateway
cd gateway-unified
make run-dev

# 2. 运行测试
go test ./internal/websocket/... -v

# 3. 访问UI
open http://localhost:8005
```

---

## 📚 相关文档

- **API文档**: `docs/api/CANVAS_HOST_API.md`
- **测试报告**: `tests/canvas/test_canvas_host.py`
- **Go实现**: `gateway-unified/internal/websocket/canvas/`
- **Python实现**: `core/canvas/canvas_host.py`

---

**最后更新**: 2026-04-20
**维护者**: Athena平台团队
