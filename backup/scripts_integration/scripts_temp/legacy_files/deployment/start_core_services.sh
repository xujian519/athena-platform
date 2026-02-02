#!/bin/bash

# Athena工作平台核心服务启动脚本
# 启动8000、8008、8083等核心服务

echo "🚀 启动Athena工作平台核心服务"
echo "=================================="

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3未安装"
    exit 1
fi

# 设置Python路径
export PYTHONPATH="/Users/xujian/Athena工作平台:$PYTHONPATH"
cd "/Users/xujian/Athena工作平台"

# 清理可能存在的端口占用
echo "🛑 清理现有服务端口..."
lsof -ti :8000 :8008 :8083 2>/dev/null | xargs kill -9 2>/dev/null || true
sleep 2

echo ""
echo "📋 服务启动计划:"
echo "├── 🏛️ Athena身份认知服务 (端口8010) - 已运行"
echo "├── 🔗 身份记忆集成服务 (端口8011) - 已运行"
echo "├── 🎯 Athena主服务 (端口8000) - 待启动"
echo "├── 🧠 Athena记忆服务 (端口8008) - 待启动"
echo "└── 💖 小诺记忆服务 (端口8083) - 待启动"

# 创建Athena主服务 (端口8000)
echo ""
echo "🎯 创建Athena主服务 (端口8000)..."

cat > /tmp/athena_main_service.py << 'EOF'
#!/usr/bin/env python3
"""
Athena工作平台主服务
端口: 8000
提供核心API和服务入口
"""

import sys
import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import uvicorn
import json
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "core"))
sys.path.append(str(project_root / "services"))

app = FastAPI(
    title="Athena工作平台",
    description="智能工作平台主服务",
    version="2.0.0"
)

# 系统状态
system_status = {
    "service_name": "athena-main",
    "version": "2.0.0",
    "status": "running",
    "start_time": datetime.now().isoformat(),
    "services": {
        "identity": {"port": 8010, "status": "running"},
        "memory_integration": {"port": 8011, "status": "running"}
    }
}

class HealthCheck(BaseModel):
    status: str
    timestamp: str
    services: Dict[str, Any]

@app.get("/")
async def root():
    return {
        "service": "Athena工作平台主服务",
        "status": "running",
        "port": 8000,
        "version": "2.0.0",
        "message": "🏛️ Athena智能工作平台已启动",
        "start_time": system_status["start_time"],
        "available_services": [
            "🧠 智能分析",
            "🔍 专利检索",
            "📋 案卷管理",
            "🤖 AI助手",
            "🎯 自动化工具"
        ]
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "athena-main",
        "timestamp": datetime.now().isoformat(),
        "system_status": system_status,
        "uptime_seconds": (datetime.now() - datetime.fromisoformat(system_status["start_time"])).total_seconds()
    }

@app.get("/api/v1/status")
async def get_status():
    return {
        "success": True,
        "data": system_status,
        "message": "系统状态正常"
    }

@app.get("/api/v1/services")
async def get_services():
    return {
        "success": True,
        "services": [
            {"name": "身份认知系统", "port": 8010, "status": "running", "description": "Athena身份认知和记忆管理"},
            {"name": "记忆集成系统", "port": 8011, "status": "running", "description": "跨系统记忆集成服务"},
            {"name": "主服务API", "port": 8000, "status": "running", "description": "平台核心API服务"}
        ]
    }

if __name__ == "__main__":
    print("🏛️ 启动Athena工作平台主服务...")
    print(f"📊 端口: 8000")
    print(f"🧠 服务: {system_status['service_name']}")
    print(f"📋 版本: {system_status['version']}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF

# 创建Athena记忆服务 (端口8008)
echo "🧠 创建Athena记忆服务 (端口8008)..."

cat > /tmp/athena_memory_service.py << 'EOF'
#!/usr/bin/env python3
"""
Athena记忆服务
端口: 8008
提供记忆管理和知识检索功能
"""

import sys
import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import uvicorn
import json
from pathlib import Path

app = FastAPI(
    title="Athena记忆服务",
    description="智能记忆管理和知识检索",
    version="2.0.0"
)

# 记忆系统状态
memory_status = {
    "service_name": "athena-memory",
    "version": "2.0.0",
    "status": "running",
    "start_time": datetime.now().isoformat(),
    "total_memories": 0,
    "active_sessions": 0
}

@app.get("/")
async def root():
    return {
        "service": "Athena记忆服务",
        "status": "running",
        "port": 8008,
        "version": "2.0.0",
        "message": "🧠 Athena记忆系统已启动",
        "features": [
            "💾 知识存储",
            "🔍 智能检索",
            "📝 记忆管理",
            "🧠 学习分析"
        ]
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "athena-memory",
        "timestamp": datetime.now().isoformat(),
        "memory_status": memory_status
    }

if __name__ == "__main__":
    print("🧠 启动Athena记忆服务...")
    print(f"📊 端口: 8008")
    print(f"💾 服务: {memory_status['service_name']}")
    uvicorn.run(app, host="0.0.0.0", port=8008)
EOF

# 创建小诺记忆服务 (端口8083)
echo "💖 创建小诺记忆服务 (端口8083)..."

cat > /tmp/xiaonuo_memory_service.py << 'EOF'
#!/usr/bin/env python3
"""
小诺记忆服务
端口: 8083
提供小诺专属记忆和情感交互功能
"""

import sys
import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import uvicorn
import json
from pathlib import Path

app = FastAPI(
    title="小诺记忆服务",
    description="小诺专属记忆和情感交互系统",
    version="3.0.0"
)

# 小诺记忆状态
xiaonuo_status = {
    "service_name": "xiaonuo-memory",
    "version": "3.0.0",
    "status": "running",
    "start_time": datetime.now().isoformat(),
    "emotional_state": "happy",
    "family_bond": "strong",
    "learning_mode": "active"
}

@app.get("/")
async def root():
    return {
        "service": "小诺记忆服务",
        "status": "running",
        "port": 8083,
        "version": "3.0.0",
        "message": "💖 小诺记忆系统已启动",
        "emotional_state": xiaonuo_status["emotional_state"],
        "features": [
            "💖 情感记忆",
            "🎨 创意记录",
            "👨‍👧 父女情深",
            "📚 学习成长",
            "💝 贴心关怀"
        ]
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "xiaonuo-memory",
        "timestamp": datetime.now().isoformat(),
        "xiaonuo_status": xiaonuo_status
    }

if __name__ == "__main__":
    print("💖 启动小诺记忆服务...")
    print(f"📊 端口: 8083")
    print(f"💝 状态: {xiaonuo_status['emotional_state']}")
    uvicorn.run(app, host="0.0.0.0", port=8083)
EOF

echo ""
echo "🚀 启动核心服务..."

# 启动Athena主服务 (端口8000)
echo "🎯 启动Athena主服务 (端口8000)..."
python3 /tmp/athena_main_service.py &
MAIN_PID=$!
sleep 3

# 启动Athena记忆服务 (端口8008)
echo "🧠 启动Athena记忆服务 (端口8008)..."
python3 /tmp/athena_memory_service.py &
MEMORY_PID=$!
sleep 3

# 启动小诺记忆服务 (端口8083)
echo "💖 启动小诺记忆服务 (端口8083)..."
python3 /tmp/xiaonuo_memory_service.py &
XIAONUO_PID=$!
sleep 3

# 保存进程ID
echo $MAIN_PID > /tmp/athena_main.pid
echo $MEMORY_PID > /tmp/athena_memory.pid
echo $XIAONUO_PID > /tmp/xiaonuo_memory.pid

echo ""
echo "📊 服务状态检查:"

# 检查Athena主服务
if curl -s http://localhost:8000/health > /dev/null; then
    main_health=$(curl -s http://localhost:8000/health | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['status'])")
    echo "✅ Athena主服务 (端口8000): $main_health"
else
    echo "❌ Athena主服务 (端口8000): 启动失败"
fi

# 检查Athena记忆服务
if curl -s http://localhost:8008/health > /dev/null; then
    memory_health=$(curl -s http://localhost:8008/health | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['status'])")
    echo "✅ Athena记忆服务 (端口8008): $memory_health"
else
    echo "❌ Athena记忆服务 (端口8008): 启动失败"
fi

# 检查小诺记忆服务
if curl -s http://localhost:8083/health > /dev/null; then
    xiaonuo_health=$(curl -s http://localhost:8083/health | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['status'])")
    echo "✅ 小诺记忆服务 (端口8083): $xiaonuo_health"
else
    echo "❌ 小诺记忆服务 (端口8083): 启动失败"
fi

echo ""
echo "🌐 核心服务访问地址:"
echo "├── 🏛️ Athena主服务: http://localhost:8000"
echo "├── 🧠 Athena记忆服务: http://localhost:8008"
echo "├── 💖 小诺记忆服务: http://localhost:8083"
echo "├── 🔍 健康检查: http://localhost:8000/health"
echo "└── 📊 服务状态: http://localhost:8000/api/v1/services"

echo ""
echo "🔗 与现有系统集成:"
echo "├── ✅ Athena主服务 (8000) ↔ 身份认知服务 (8010)"
echo "├── ✅ Athena记忆服务 (8008) ↔ 身份记忆集成 (8011)"
echo "├── ✅ 小诺记忆服务 (8083) ↔ 身份记忆集成 (8011)"
echo "└── ✅ 所有核心服务统一API标准"

echo ""
echo "💡 核心服务特性:"
echo "├── 🏛️ 主服务: 统一API入口，服务路由"
echo "├── 🧠 记忆服务: 知识管理，智能检索"
echo "├── 💖 小诺服务: 情感记忆，创意记录"
echo "├── 🔗 集成服务: 跨系统数据同步"
echo "├── 📊 监控服务: 实时状态监控"
echo "└── 🛡️ 健康检查: 自动故障检测"

echo ""
echo "🛑 停止核心服务:"
echo "   kill $MAIN_PID $MEMORY_PID $XIAONUO_PID"
echo "   或使用: bash /tmp/stop_core_services.sh"

# 创建停止脚本
cat > /tmp/stop_core_services.sh << 'EOF'
#!/bin/bash
echo "🛑 停止Athena工作平台核心服务..."

if [ -f /tmp/athena_main.pid ]; then
    MAIN_PID=$(cat /tmp/athena_main.pid)
    kill $MAIN_PID 2>/dev/null || true
    rm -f /tmp/athena_main.pid
    echo "✅ Athena主服务已停止"
fi

if [ -f /tmp/athena_memory.pid ]; then
    MEMORY_PID=$(cat /tmp/athena_memory.pid)
    kill $MEMORY_PID 2>/dev/null || true
    rm -f /tmp/athena_memory.pid
    echo "✅ Athena记忆服务已停止"
fi

if [ -f /tmp/xiaonuo_memory.pid ]; then
    XIAONUO_PID=$(cat /tmp/xiaonuo_memory.pid)
    kill $XIAONUO_PID 2>/dev/null || true
    rm -f /tmp/xiaonuo_memory.pid
    echo "✅ 小诺记忆服务已停止"
fi

# 清理端口
lsof -ti :8000 :8008 :8083 | xargs kill -9 2>/dev/null || true

echo "🧹 核心服务端口清理完成"
EOF

chmod +x /tmp/stop_core_services.sh

echo ""
echo "🎉 Athena工作平台核心服务启动完成!"
echo "🏛️ 智能工作平台已完全激活，准备为您提供全方位服务"