#!/bin/bash
# -*- coding: utf-8 -*-
# 记忆系统部署脚本
# Deploy Memory System

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 项目根目录
PROJECT_ROOT="/Users/xujian/Athena工作平台"

# 记忆系统配置
MEMORY_SYSTEM_DIR="${PROJECT_ROOT}/core/memory"
UNIFIED_MEMORY_FILE="${MEMORY_SYSTEM_DIR}/unified_agent_memory_system.py"
MEMORY_CONFIG_FILE="${PROJECT_ROOT}/config/memory_system_config.json"
MEMORY_SERVICE_PORT="8003"

# PostgreSQL配置
POSTGRES_HOST="localhost"
POSTGRES_PORT="5438"
POSTGRES_DB="memory_module"

# Qdrant配置
QDRANT_HOST="localhost"
QDRANT_PORT="6333"

# 知识图谱配置
KG_HOST="localhost"
KG_PORT="8002"

# 部署函数
deploy_memory_system() {
    log_info "开始部署统一记忆系统..."
    echo "=================================================="

    # 1. 检查必要的组件
    log_info "检查系统组件..."

    # 检查PostgreSQL
    if ! /opt/homebrew/Cellar/postgresql@17/17.7/bin/pg_isready -h ${POSTGRES_HOST} -p ${POSTGRES_PORT} >/dev/null 2>&1; then
        log_warning "PostgreSQL 未运行在 ${POSTGRES_HOST}:${POSTGRES_PORT}，尝试启动..."
        /opt/homebrew/Cellar/postgresql@17/17.7/bin/pg_ctl -D /Users/xujian/postgres_memory_data start -o "-c port=5438" 2>/dev/null
        sleep 2

        if ! /opt/homebrew/Cellar/postgresql@17/17.7/bin/pg_isready -h ${POSTGRES_HOST} -p ${POSTGRES_PORT} >/dev/null 2>&1; then
            log_error "PostgreSQL 启动失败"
            exit 1
        fi
    fi
    log_success "PostgreSQL 运行正常"

    # 检查Qdrant
    if ! curl -s http://${QDRANT_HOST}:${QDRANT_PORT}/health >/dev/null 2>&1; then
        log_warning "Qdrant 未运行在 ${QDRANT_HOST}:${QDRANT_PORT}"
        log_info "启动 Qdrant: scripts/start_qdrant.sh"
        bash "${PROJECT_ROOT}/scripts/start_qdrant.sh"
        sleep 3
    fi
    log_success "Qdrant 运行正常"

    # 检查知识图谱
    if ! curl -s http://${KG_HOST}:${KG_PORT}/api/health >/dev/null 2>&1; then
        log_warning "知识图谱未运行在 ${KG_HOST}:${KG_PORT}"
        log_info "启动知识图谱服务..."
        # 这里可以添加启动知识图谱的命令
    fi
    log_success "知识图谱服务正常"

    # 2. 创建记忆系统配置
    log_info "创建记忆系统配置..."
    cat > "${MEMORY_CONFIG_FILE}" << EOF
{
  "system": {
    "name": "Athena统一记忆系统",
    "version": "1.0.0",
    "deploy_date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  },
  "storage": {
    "postgresql": {
      "host": "${POSTGRES_HOST}",
      "port": "${POSTGRES_PORT}",
      "database": "${POSTGRES_DB}",
      "pool_size": 10,
      "max_overflow": 20
    },
    "qdrant": {
      "host": "${QDRANT_HOST}",
      "port": "${QDRANT_PORT}",
      "collection_name": "agent_memories",
      "vector_size": 768
    },
    "knowledge_graph": {
      "host": "${KG_HOST}",
      "port": "${KG_PORT}",
      "endpoint": "/api/v1"
    }
  },
  "memory": {
    "tiers": {
      "eternal": {"importance_threshold": 0.9, "retention_days": -1},
      "hot": {"importance_threshold": 0.7, "retention_days": 365},
      "warm": {"importance_threshold": 0.5, "retention_days": 90},
      "cold": {"importance_threshold": 0.0, "retention_days": 30}
    },
    "auto_save": {
      "enabled": true,
      "threshold": 5,
      "interval_seconds": 30
    },
    "compression": {
      "enabled": true,
      "threshold_days": 180
    }
  },
  "agents": {
    "athena": {
      "id": "athena_wisdom",
      "type": "wisdom_goddess",
      "memory_types": ["knowledge", "conversation", "reflection"]
    },
    "xiaona": {
      "id": "xiaona_libra",
      "type": "emotional_companion",
      "memory_types": ["family", "conversation", "preference"]
    },
    "xiaonuo": {
      "id": "xiaonuo_pisces",
      "type": "platform_coordinator",
      "memory_types": ["family", "schedule", "knowledge"]
    },
    "yunxi": {
      "id": "yunxi_vega",
      "type": "ip_manager",
      "memory_types": ["professional", "knowledge", "work"]
    },
    "xiaochen": {
      "id": "xiaochen_sagittarius",
      "type": "media_operator",
      "memory_types": ["work", "learning", "creative"]
    }
  }
}
EOF
    log_success "配置文件已创建: ${MEMORY_CONFIG_FILE}"

    # 3. 创建记忆系统服务启动脚本
    log_info "创建记忆系统服务脚本..."
    cat > "${PROJECT_ROOT}/scripts/start_memory_service.sh" << 'EOF'
#!/bin/bash
# 记忆系统服务启动脚本

PROJECT_ROOT="/Users/xujian/Athena工作平台"
PYTHONPATH="${PROJECT_ROOT}"

# 激活虚拟环境（如果有的话）
if [ -f "${PROJECT_ROOT}/venv/bin/activate" ]; then
    source "${PROJECT_ROOT}/venv/bin/activate"
fi

# 设置环境变量
export MEMORY_SYSTEM_CONFIG="${PROJECT_ROOT}/config/memory_system_config.json"
export POSTGRES_HOST="localhost"
export POSTGRES_PORT="5438"
export POSTGRES_DB="memory_module"

# 启动记忆系统API服务
cd "${PROJECT_ROOT}"
python3 -m core.memory.memory_api_server --port 8003
EOF
    chmod +x "${PROJECT_ROOT}/scripts/start_memory_service.sh"
    log_success "服务启动脚本已创建"

    # 4. 创建记忆系统API服务
    log_info "创建记忆系统API服务..."
    cat > "${MEMORY_SYSTEM_DIR}/memory_api_server.py" << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
记忆系统API服务器
Memory System API Server
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import argparse

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 导入记忆系统
from unified_agent_memory_system import UnifiedAgentMemorySystem, MemoryType, MemoryTier

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI应用
app = FastAPI(
    title="Athena记忆系统API",
    description="统一记忆系统的RESTful API接口",
    version="1.0.0"
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局记忆系统实例
memory_system: Optional[UnifiedAgentMemorySystem] = None

# 请求模型
class MemoryStoreRequest(BaseModel):
    agent_id: str
    content: str
    memory_type: str
    importance: float = 0.5
    emotional_weight: float = 0.0
    family_related: bool = False
    work_related: bool = True
    tags: List[str] = []
    metadata: Dict[str, Any] = {}

class MemoryRecallRequest(BaseModel):
    agent_id: str
    query: str
    limit: int = 10
    memory_type: Optional[str] = None

class MemorySearchRequest(BaseModel):
    query: str
    agent_id: Optional[str] = None
    memory_type: Optional[str] = None
    importance_threshold: float = 0.0
    limit: int = 20

# 启动事件
@app.on_event("startup")
async def startup_event():
    """启动时初始化记忆系统"""
    global memory_system

    # 加载配置
    config_path = os.environ.get('MEMORY_SYSTEM_CONFIG',
                                '/Users/xujian/Athena工作平台/config/memory_system_config.json')

    if Path(config_path).exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        logger.info(f"加载配置文件: {config_path}")
    else:
        logger.warning("配置文件不存在，使用默认配置")
        config = {}

    # 初始化记忆系统
    memory_system = UnifiedAgentMemorySystem(config=config)
    await memory_system.initialize()

    logger.info("记忆系统API服务已启动")

# 健康检查
@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "memory_system",
        "version": "1.0.0"
    }

# 存储记忆
@app.post("/api/memory/store")
async def store_memory(request: MemoryStoreRequest):
    """存储记忆"""
    try:
        success = await memory_system.store_memory(
            content=request.content,
            memory_type=MemoryType(request.memory_type),
            importance=request.importance,
            emotional_weight=request.emotional_weight,
            family_related=request.family_related,
            work_related=request.work_related,
            tags=request.tags,
            metadata=request.metadata,
            agent_id=request.agent_id
        )

        if success:
            return {"status": "success", "message": "记忆存储成功"}
        else:
            raise HTTPException(status_code=500, detail="记忆存储失败")

    except Exception as e:
        logger.error(f"存储记忆错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 检索记忆
@app.post("/api/memory/recall")
async def recall_memory(request: MemoryRecallRequest):
    """检索记忆"""
    try:
        memories = await memory_system.recall_memory(
            agent_id=request.agent_id,
            query=request.query,
            limit=request.limit,
            memory_type=MemoryType(request.memory_type) if request.memory_type else None
        )

        return {
            "status": "success",
            "count": len(memories),
            "memories": [
                {
                    "id": m.get("id"),
                    "content": m.get("content"),
                    "memory_type": m.get("memory_type"),
                    "importance": m.get("importance"),
                    "created_at": m.get("created_at"),
                    "tier": m.get("tier")
                }
                for m in memories
            ]
        }

    except Exception as e:
        logger.error(f"检索记忆错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 搜索记忆
@app.post("/api/memory/search")
async def search_memory(request: MemorySearchRequest):
    """搜索记忆"""
    try:
        results = await memory_system.search_memories(
            query=request.query,
            agent_id=request.agent_id,
            memory_type=MemoryType(request.memory_type) if request.memory_type else None,
            importance_threshold=request.importance_threshold,
            limit=request.limit
        )

        return {
            "status": "success",
            "query": request.query,
            "count": len(results),
            "results": results
        }

    except Exception as e:
        logger.error(f"搜索记忆错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 获取智能体记忆统计
@app.get("/api/memory/stats/{agent_id}")
async def get_memory_stats(agent_id: str):
    """获取智能体记忆统计"""
    try:
        stats = await memory_system.get_agent_memory_stats(agent_id)
        return {
            "status": "success",
            "agent_id": agent_id,
            "stats": stats
        }

    except Exception as e:
        logger.error(f"获取统计错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 跨智能体共享记忆
@app.post("/api/memory/share")
async def share_memory(memory_id: str, target_agents: List[str]):
    """共享记忆给其他智能体"""
    try:
        success = await memory_system.share_memory(memory_id, target_agents)

        if success:
            return {"status": "success", "message": f"记忆已共享给 {len(target_agents)} 个智能体"}
        else:
            raise HTTPException(status_code=500, detail="记忆共享失败")

    except Exception as e:
        logger.error(f"共享记忆错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 清理旧记忆
@app.post("/api/memory/cleanup")
async def cleanup_memories(background_tasks: BackgroundTasks):
    """清理旧记忆（后台任务）"""
    background_tasks.add_task(memory_system.cleanup_old_memories)
    return {"status": "accepted", "message": "记忆清理任务已启动"}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="记忆系统API服务器")
    parser.add_argument("--port", type=int, default=8003, help="服务端口")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="服务主机")

    args = parser.parse_args()

    uvicorn.run(
        "memory_api_server:app",
        host=args.host,
        port=args.port,
        reload=True,
        log_level="info"
    )
EOF
    log_success "记忆系统API服务已创建"

    # 5. 更新智能体基类以使用记忆系统
    log_info "更新智能体基类..."
    cat > "${PROJECT_ROOT}/core/agent/base_agent_with_unified_memory.py" << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
带统一记忆系统的智能体基类
Base Agent with Unified Memory System
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

from unified_agent_memory_system import UnifiedAgentMemorySystem, MemoryType, MemoryTier

class BaseAgentWithUnifiedMemory:
    """带统一记忆系统的智能体基类"""

    def __init__(self, agent_id: str, agent_type: str):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.memory_system: Optional[UnifiedAgentMemorySystem] = None
        self.conversation_context: List[Dict[str, Any]] = []
        self.memory_config = {
            'auto_save': True,
            'save_threshold': 5,
            'importance_threshold': 0.5
        }

    async def initialize(self):
        """初始化智能体和记忆系统"""
        # 加载记忆系统配置
        config_path = os.environ.get('MEMORY_SYSTEM_CONFIG',
                                    '/Users/xujian/Athena工作平台/config/memory_system_config.json')

        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # 获取当前智能体的配置
            agent_config = config.get('agents', {}).get(self.agent_type, {})
            if agent_config:
                config['current_agent'] = agent_config

        # 初始化记忆系统
        self.memory_system = UnifiedAgentMemorySystem(config=config.get('memory', {}))
        await self.memory_system.initialize()

        # 加载最近的重要记忆
        await self._load_recent_memories()

    async def _load_recent_memories(self):
        """加载最近的重要记忆"""
        try:
            # 获取最近的永恒记忆和热记忆
            recent_memories = await self.memory_system.recall_memory(
                agent_id=self.agent_id,
                query="recent important memories",
                limit=5,
                importance_threshold=0.7
            )

            for memory in recent_memories:
                self.conversation_context.append({
                    'type': 'memory',
                    'content': memory.get('content'),
                    'timestamp': memory.get('created_at'),
                    'importance': memory.get('importance')
                })

        except Exception as e:
            print(f"加载历史记忆失败: {e}")

    async def process_message(self, user_input: str, **kwargs) -> str:
        """处理用户消息"""
        # 保存用户输入到记忆
        if self.memory_config['auto_save']:
            await self._save_interaction_to_memory(user_input, is_user=True)

        # 添加到对话上下文
        self.conversation_context.append({
            'type': 'user',
            'content': user_input,
            'timestamp': datetime.now().isoformat()
        })

        # 生成响应
        response = await self._generate_response(user_input, **kwargs)

        # 保存响应到记忆
        if self.memory_config['auto_save']:
            await self._save_interaction_to_memory(response, is_user=False)

        # 添加到对话上下文
        self.conversation_context.append({
            'type': 'agent',
            'content': response,
            'timestamp': datetime.now().isoformat()
        })

        # 自动保存上下文
        await self._auto_save_context()

        return response

    async def _save_interaction_to_memory(self, content: str, is_user: bool):
        """保存交互到记忆系统"""
        try:
            # 根据内容判断重要性
            importance = self._calculate_importance(content)

            # 根据智能体类型确定记忆类型
            memory_type = self._determine_memory_type(content)

            # 保存到记忆系统
            await self.memory_system.store_memory(
                content=content,
                memory_type=memory_type,
                importance=importance,
                emotional_weight=self._calculate_emotional_weight(content),
                family_related=self._is_family_related(content),
                work_related=self._is_work_related(content),
                tags=self._extract_tags(content),
                metadata={
                    'is_user_input': is_user,
                    'agent_type': self.agent_type,
                    'session_id': getattr(self, 'session_id', None)
                },
                agent_id=self.agent_id
            )

        except Exception as e:
            print(f"保存记忆失败: {e}")

    async def _auto_save_context(self):
        """自动保存对话上下文"""
        if len(self.conversation_context) >= self.memory_config['save_threshold']:
            # 将对话上下文保存为一个整体记忆
            conversation_text = "\n".join([
                f"{'用户' if ctx['type'] == 'user' else '智能体'}: {ctx['content']}"
                for ctx in self.conversation_context[-self.memory_config['save_threshold']:]
            ])

            await self.memory_system.store_memory(
                content=conversation_text,
                memory_type=MemoryType.CONVERSATION,
                importance=0.6,
                metadata={
                    'conversation_context': True,
                    'agent_type': self.agent_type,
                    'turn_count': len(self.conversation_context)
                },
                agent_id=self.agent_id
            )

    async def search_memories(self, query: str, limit: int = 10):
        """搜索相关记忆"""
        if not self.memory_system:
            return []

        return await self.memory_system.recall_memory(
            agent_id=self.agent_id,
            query=query,
            limit=limit
        )

    # 以下方法需要子类实现
    async def _generate_response(self, user_input: str, **kwargs) -> str:
        raise NotImplementedError

    def _calculate_importance(self, content: str) -> float:
        """计算内容重要性"""
        # 默认实现，子类可以重写
        if len(content) > 100:
            return 0.7
        return 0.5

    def _determine_memory_type(self, content: str) -> MemoryType:
        """确定记忆类型"""
        # 默认实现，子类可以重写
        return MemoryType.CONVERSATION

    def _calculate_emotional_weight(self, content: str) -> float:
        """计算情感权重"""
        # 默认实现，子类可以重写
        return 0.5

    def _is_family_related(self, content: str) -> bool:
        """判断是否与家庭相关"""
        # 默认实现，子类可以重写
        family_keywords = ['爸爸', '妈妈', '女儿', '家庭', '家人']
        return any(keyword in content for keyword in family_keywords)

    def _is_work_related(self, content: str) -> bool:
        """判断是否与工作相关"""
        # 默认实现，子类可以重写
        work_keywords = ['工作', '项目', '专利', '业务', '任务']
        return any(keyword in content for keyword in work_keywords)

    def _extract_tags(self, content: str) -> List[str]:
        """提取标签"""
        # 默认实现，子类可以重写
        tags = []
        if '?' in content:
            tags.append('问题')
        if '！' in content or '!' in content:
            tags.append('感叹')
        if len(content) > 200:
            tags.append('长文本')
        return tags
EOF
    log_success "智能体基类已更新"

    # 6. 创建系统集成脚本
    log_info "创建系统集成脚本..."
    cat > "${PROJECT_ROOT}/scripts/integrate_memory_system.sh" << 'EOF'
#!/bin/bash
# 集成记忆系统到平台

PROJECT_ROOT="/Users/xujian/Athena工作平台"

echo "🔄 集成记忆系统到平台..."

# 1. 更新智能体启动脚本
for agent in athena xiaona xiaonuo yunxi xiaochen; do
    agent_script="${PROJECT_ROOT}/scripts/start_${agent}.sh"
    if [ -f "$agent_script" ]; then
        # 在启动脚本中添加记忆系统初始化
        if ! grep -q "unified_memory" "$agent_script"; then
            sed -i '' '/python3/i\
# 初始化统一记忆系统\
export MEMORY_SYSTEM_CONFIG="'$PROJECT_ROOT'/config/memory_system_config.json"\
' "$agent_script"
        fi
        echo "✅ 更新 $agent 启动脚本"
    fi
done

# 2. 创建环境变量配置
cat > "${PROJECT_ROOT}/.env.memory" << EOL
# 记忆系统环境变量
MEMORY_SYSTEM_CONFIG=${PROJECT_ROOT}/config/memory_system_config.json
POSTGRES_HOST=localhost
POSTGRES_PORT=5438
POSTGRES_DB=memory_module
QDRANT_HOST=localhost
QDRANT_PORT=6333
KG_HOST=localhost
KG_PORT=8002
MEMORY_SERVICE_PORT=8003
EOL

echo "✅ 创建环境变量配置"

# 3. 更新主启动脚本
main_script="${PROJECT_ROOT}/start.sh"
if [ -f "$main_script" ]; then
    if ! grep -q "memory_service" "$main_script"; then
        # 在启动脚本中添加记忆系统服务
        sed -i '' '/# Start core services/a\
# 启动记忆系统服务\
echo "启动记忆系统服务..."\
bash "${PROJECT_ROOT}"/scripts/start_memory_service.sh &\
MEMORY_PID=$!\
echo "记忆系统服务 PID: $MEMORY_PID"\
' "$main_script"
    fi
    echo "✅ 更新主启动脚本"
fi

echo "🎉 记忆系统集成完成！"
EOF
    chmod +x "${PROJECT_ROOT}/scripts/integrate_memory_system.sh"

    # 执行集成
    log_info "执行系统集成..."
    bash "${PROJECT_ROOT}/scripts/integrate_memory_system.sh"

    # 7. 创建验证脚本
    log_info "创建部署验证脚本..."
    cat > "${PROJECT_ROOT}/scripts/verify_memory_deployment.sh" << 'EOF'
#!/bin/bash
# 验证记忆系统部署

PROJECT_ROOT="/Users/xujian/Athena工作平台"
MEMORY_SERVICE_PORT="8003"

echo "🔍 验证记忆系统部署..."

# 1. 检查配置文件
if [ -f "${PROJECT_ROOT}/config/memory_system_config.json" ]; then
    echo "✅ 配置文件存在"
else
    echo "❌ 配置文件不存在"
    exit 1
fi

# 2. 检查记忆系统服务
if curl -s http://localhost:${MEMORY_SERVICE_PORT}/api/health > /dev/null; then
    echo "✅ 记忆系统API服务运行正常"
else
    echo "❌ 记忆系统API服务未运行"
    echo "请执行: bash ${PROJECT_ROOT}/scripts/start_memory_service.sh"
fi

# 3. 检查数据库连接
if psql -h localhost -p 5438 -d memory_module -c "SELECT 1;" > /dev/null 2>&1; then
    echo "✅ PostgreSQL连接正常"
    memory_count=$(psql -h localhost -p 5438 -d memory_module -t -c "SELECT COUNT(*) FROM memory_items;")
    echo "   当前记忆数: ${memory_count//[[:space:]]/}"
else
    echo "❌ PostgreSQL连接失败"
fi

# 4. 检查Qdrant
if curl -s http://localhost:6333/health > /dev/null; then
    echo "✅ Qdrant服务正常"
else
    echo "❌ Qdrant服务未运行"
fi

echo "🎉 验证完成！"
EOF
    chmod +x "${PROJECT_ROOT}/scripts/verify_memory_deployment.sh"

    log_success "部署脚本创建完成！"
    echo ""
    echo "=================================================="
    echo "📋 部署总结:"
    echo "  - 配置文件: ${MEMORY_CONFIG_FILE}"
    echo "  - API服务端口: ${MEMORY_SERVICE_PORT}"
    echo "  - 数据库: ${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"
    echo ""
    echo "🚀 下一步操作:"
    echo "  1. 启动记忆系统服务:"
    echo "     bash scripts/start_memory_service.sh"
    echo ""
    echo "  2. 验证部署:"
    echo "     bash scripts/verify_memory_deployment.sh"
    echo ""
    echo "  3. 重启平台服务:"
    echo "     bash start.sh"
    echo "=================================================="
}

# 主函数
main() {
    deploy_memory_system
}

# 执行
main "$@"